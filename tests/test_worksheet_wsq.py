import contextlib
import importlib.util
import io
import re
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "physics-worksheet-generator" / "SKILL.md"
TEMPLATES = ROOT / "references" / "worksheets_templates_and_examples.md"

# 改版前的 WSQ 樣板：時間碼、數據表、公式摘要、三種提問都要寫
OLD_WSQ = """# PXx-Vc-1-1 電流 WSQ 自學學習單

## W - 觀看與紀錄
| 觀看時間點 | 影片觀察重點 | 學生紀錄 |
|:---:|---|---|
| 01:15 | 觀察燈泡發亮之閉合迴路 | [ ] 閉合 [ ] 斷開 |

## S - 總結與歸納
### 1. 數據記錄表格
| 試驗次數 | 電流 $I$ |
|:---:|:---:|
* **數學關係式**：$$I = \\frac{\\Delta Q}{\\Delta t}$$

## Q - 提問與困惑
| 澄清型 | 影片中是否有不理解的概念？ | |
| 深化型 | 如果改變條件，會怎樣？ | |
| 應用型 | 這個原理在生活中有什麼應用？ | |
"""


def load_audit():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import audit_wsq
    finally:
        sys.path.pop(0)
    return audit_wsq


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def load_builder():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import build_wsq_docx
    finally:
        sys.path.pop(0)
    return build_wsq_docx


def template_example() -> str:
    text = TEMPLATES.read_text(encoding="utf-8")
    blocks = re.findall(r"```markdown\n(.*?)```", text, re.S)
    return next(b for b in blocks if b.startswith("# PEb-Vc-4-1"))


class WsqFormatTests(unittest.TestCase):
    def test_skill_fixes_short_wsq_format(self):
        text = SKILL.read_text(encoding="utf-8")
        for marker in [
            "### WSQ 固定格式",
            "3～5 格",
            "30 字內",
            "10 分鐘內",
            "不標投影片頁碼",
            "選一個寫",
            "scripts/audit_wsq.py",
            "scripts/build_wsq_docx.py",
            "不產教師版",
            "不放數據表、公式推導、計算題、影片時間碼",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("提供澄清、深化、應用提問句型", text)
        self.assertNotIn("每格標投影片頁碼", text)

    def test_template_wsq_drops_timestamps_and_data_tables(self):
        text = TEMPLATES.read_text(encoding="utf-8")
        wsq = text.split("## 📑 模式二")[0]
        for banned in ["觀看時間點", "數據記錄表格", "核心原理與公式摘要", "澄清型", "（第"]:
            with self.subTest(banned=banned):
                self.assertNotIn(banned, wsq)

    def test_template_example_passes_audit(self):
        warn, stats = load_audit().audit(template_example())
        self.assertEqual([], warn)
        self.assertEqual(4, stats["W"])
        self.assertLessEqual(stats["minutes"], 10)

    def test_old_long_wsq_is_flagged(self):
        warn, _ = load_audit().audit(OLD_WSQ)
        joined = "\n".join(warn)
        for expected in ["W 有 0 格", "表格", "時間碼", "LaTeX", "提示："]:
            with self.subTest(expected=expected):
                self.assertIn(expected, joined)

    def test_slide_page_tag_is_flagged(self):
        # 標了頁碼，學生會只盯那幾張投影片、忽略其他頁面
        tagged = template_example().replace("1. 公車", "1. （第 2 張）公車")
        warn, _ = load_audit().audit(tagged)
        self.assertEqual(["W1 標了投影片頁碼（第 N 張），請拿掉"], warn)

    def test_too_many_w_items_and_long_prompt_are_flagged(self):
        example = template_example()
        extra = "\n".join(f"{n}. 多一格＿＿。" for n in range(5, 7))
        longer = example.replace("4. 物體", "4. " + "很長的敘述" * 8 + "物體")
        warn, _ = load_audit().audit(longer.replace("## S", extra + "\n\n## S"))
        joined = "\n".join(warn)
        self.assertIn("W 有 6 格", joined)
        self.assertIn("W4 題目", joined)

    def test_docx_builder_parses_student_version_only(self):
        import py_compile

        py_compile.compile(str(ROOT / "scripts" / "build_wsq_docx.py"), doraise=True)
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_wsq_docx
        finally:
            sys.path.pop(0)
        spec = build_wsq_docx.parse(template_example() + "\n# 教師版\n- W：前傾\n")
        self.assertEqual("PEb-Vc-4-1 牛頓第一定律｜WSQ", spec["title"])
        self.assertTrue(spec["header"].startswith("班級："))
        self.assertEqual(["W", "S", "Q"], [heading[:1] for heading, _ in spec["sections"]])
        self.assertNotIn("前傾", str(spec))

    def test_docx_builder_splits_code_name_and_header_labels(self):
        build_wsq_docx = load_builder()
        spec = build_wsq_docx.parse(template_example())
        self.assertEqual("PEb-Vc-4-1", spec["code"])
        self.assertEqual("牛頓第一定律", spec["name"])
        self.assertEqual(["班級", "座號", "姓名"], spec["labels"])

    def test_skill_describes_styled_layout(self):
        text = SKILL.read_text(encoding="utf-8")
        for marker in ["W／S／Q 色塊徽章", "W 每格只有題號與題目", "作答框", "黑白列印"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    @unittest.skipUnless(importlib.util.find_spec("docx"), "需要 python-docx")
    def test_docx_uses_styled_layout(self):
        import tempfile
        import zipfile

        build_wsq_docx = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "wsq.docx"
            with contextlib.redirect_stdout(io.StringIO()):
                build_wsq_docx.build(build_wsq_docx.parse(template_example()), out)
            with zipfile.ZipFile(out) as z:
                body = z.read("word/document.xml").decode("utf-8")
                footer = "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("word/footer"))

        # 標頭與三區徽章；不出現投影片頁碼
        for text in ["牛頓第一定律", "WSQ", "Watch", "Summarize", "Question", "班級", "滑行距離"]:
            with self.subTest(text=text):
                self.assertIn(text, body)
        self.assertNotRegex(body, r"第\s*\d+\s*張")
        for color in build_wsq_docx.COLOR.values():
            with self.subTest(color=color):
                self.assertIn(f'w:fill="{color}"', body)
        self.assertIn("PEb-Vc-4-1", footer)
        self.assertIn('w:eastAsia="微軟正黑體"', body)
        self.assertIn('w:ascii="Arial"', body)
        self.assertIn('w:w="11906"', body)  # A4 寬

        root = ElementTree.fromstring(body)
        local = lambda node: node.tag.rsplit("}", 1)[-1]  # noqa: E731

        # Word 會把相鄰表格併成一張，各區塊之間要有段落隔開
        top = [local(node) for node in root.find(f"{W}body")]
        self.assertGreaterEqual(top.count("tbl"), 5)
        self.assertNotIn(("tbl", "tbl"), list(zip(top, top[1:])))

        # 儲存格屬性要照 OOXML 順序，否則 Word 會忽略網底或框線
        order = build_wsq_docx.TC_ORDER
        for tc_pr in root.iter(f"{W}tcPr"):
            names = [local(child) for child in tc_pr]
            ranks = [order.index(name) for name in names]
            self.assertEqual(sorted(ranks), ranks, names)

    def test_cli_exit_code(self):
        import tempfile

        audit = load_audit()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            good = Path(tmp) / "good.md"
            bad = Path(tmp) / "bad.md"
            good.write_text(template_example(), encoding="utf-8")
            bad.write_text(OLD_WSQ, encoding="utf-8")
            self.assertEqual(0, audit.main([str(good)]))
            self.assertEqual(1, audit.main([str(good), str(bad)]))


if __name__ == "__main__":
    unittest.main()
