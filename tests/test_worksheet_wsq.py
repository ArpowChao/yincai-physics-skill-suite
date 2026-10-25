import contextlib
import io
import re
import sys
import unittest
from pathlib import Path


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
            "投影片頁碼",
            "選一個寫",
            "scripts/audit_wsq.py",
            "scripts/build_wsq_docx.py",
            "不產教師版",
            "不放數據表、公式推導、計算題、影片時間碼",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("提供澄清、深化、應用提問句型", text)

    def test_template_wsq_drops_timestamps_and_data_tables(self):
        text = TEMPLATES.read_text(encoding="utf-8")
        wsq = text.split("## 📑 模式二")[0]
        for banned in ["觀看時間點", "數據記錄表格", "核心原理與公式摘要", "澄清型"]:
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

    def test_too_many_w_items_and_long_prompt_are_flagged(self):
        example = template_example()
        extra = "\n".join(f"{n}. （第 {n} 張）多一格＿＿。" for n in range(5, 7))
        longer = example.replace("4. （第 8 張）", "4. （第 8 張）" + "很長的敘述" * 8)
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
