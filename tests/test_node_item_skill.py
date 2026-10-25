import json
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "yincai-physics-node-items" / "SKILL.md"
PERFORMANCE = ROOT / "data" / "curriculum" / "stage5-learning-performance.json"
GSAT = ROOT / "data" / "gsat" / "verified-physics-sources.json"
CURRICULUM = ROOT / "data" / "curriculum" / "stage5-physics.json"
DOWNLOADS = ROOT / "data" / "sources" / "official-downloads.json"
SCRIPTS = [
    ROOT / "scripts" / "gsat_sources.py",
    ROOT / "scripts" / "build_node_item_sheet.py",
    ROOT / "scripts" / "audit_node_item_sheet.py",
    ROOT / "scripts" / "fetch_local_data.py",
    ROOT / "scripts" / "split_node_item_sheet.py",
]
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def para(text: str = "", page_break: bool = False) -> str:
    run = '<w:r><w:br w:type="page"/></w:r>' if page_break else ""
    if text:
        run += f'<w:r><w:rPr><w:color w:val="FF0000"/></w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'
    return f'<w:p w14:paraId="1A2B3C4D">{run}</w:p>'


def table(label: str) -> str:
    return f"<w:tbl><w:tr><w:tc><w:p><w:r><w:t>題目：</w:t></w:r></w:p></w:tc><w:tc>{para(label)}</w:tc></w:tr></w:tbl>"


def make_sheet(section: bool = True) -> bytes:
    """合成一份 4 題任務單：填寫說明、範例、（練習題）、理解、應用、診斷1、診斷2，題號照舊檔的錯置寫法。"""
    import io
    import zipfile

    body = [para("填寫說明："), table("範例題"), para(page_break=True)]
    if section:
        body.append(para("練習題"))
    body += [
        para("1. 理解題"), table("理解題目"),
        para("2. 應用題"), table("應用題目"), para(page_break=True),
        para("3. 診斷題1（經典題修改）"), table("診斷一題目"), para(page_break=True),
        para("2. 診斷題2（經典題修改）"), table("診斷二題目"), para(),
    ]
    xml = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
        f'<w:body>{"".join(body)}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", xml)
        z.writestr("word/media/image1.png", b"\x89PNG fixture")
    return buffer.getvalue()


def outline(docx: bytes) -> list[str]:
    """body 直接子元素的摘要：段落文字、[分頁]、[表:內容]、[空]、[sectPr]。"""
    import io
    import zipfile
    from xml.etree import ElementTree

    root = ElementTree.fromstring(zipfile.ZipFile(io.BytesIO(docx)).read("word/document.xml"))
    result = []
    for child in root.find(f"{{{W_NS}}}body"):
        tag = child.tag.split("}")[1]
        text = "".join(t.text or "" for t in child.iter(f"{{{W_NS}}}t"))
        if tag == "tbl":
            result.append(f"[表:{text}]")
        elif tag == "sectPr":
            result.append("[sectPr]")
        elif any(b.get(f"{{{W_NS}}}type") == "page" for b in child.iter(f"{{{W_NS}}}br")):
            result.append("[分頁]")
        else:
            result.append(text or "[空]")
    return result


class NodeItemSkillTests(unittest.TestCase):
    def test_skill_keeps_item_writing_contract(self):
        text = SKILL.read_text(encoding="utf-8")
        for marker in [
            "1. 理解題",
            "2. 應用題",
            "診斷題1（經典題修改）",
            "改編自 ○○○ 學測自然第 N 題",
            "scripts/resolve_curriculum.py",
            "scripts/gsat_sources.py",
            "scripts/build_node_item_sheet.py",
            "scripts/audit_node_item_sheet.py",
            "stage5-learning-performance.json",
            "不停下來詢問",
            "正解不可明顯最長",
            "不得憑記憶寫題號",
            "105 學測第 1 題",
            "不用破折號",
            "_練習題",
            "_診斷題",
            "1. 診斷題1（經典題修改）",
            "題號在各自檔案內從 1 起算",
            "scripts/split_node_item_sheet.py",
            "理解（2.5）",
            "應用（3.5）",
            "1 記憶、2 理解、3 應用、4 分析",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_learning_performance_catalog_covers_all_mandatory_codes(self):
        data = json.loads(PERFORMANCE.read_text(encoding="utf-8"))
        codes = [entry["code"] for entry in data["entries"]]
        expected = {
            "ti-Vc-1", "tr-Vc-1", "tc-Vc-1", "tm-Vc-1",
            "po-Vc-1", "po-Vc-2", "pe-Vc-1", "pe-Vc-2",
            "pa-Vc-1", "pa-Vc-2", "pc-Vc-1", "pc-Vc-2",
            "ai-Vc-1", "ai-Vc-2", "ai-Vc-3",
            "ah-Vc-1", "ah-Vc-2",
            "an-Vc-1", "an-Vc-2", "an-Vc-3",
        }
        self.assertEqual(expected, set(codes))
        self.assertEqual(len(codes), len(set(codes)))
        allowed = {"high", "medium", "low", "not_suitable"}
        for entry in data["entries"]:
            with self.subTest(code=entry["code"]):
                self.assertTrue(entry["statement"])
                self.assertIn(entry["mcq_suitability"], allowed)
                self.assertIn(entry["source"]["pdf_page"], {35, 36, 37})
                if entry["code"].startswith("ai-"):
                    self.assertEqual("not_suitable", entry["mcq_suitability"])
                else:
                    self.assertTrue(entry["mcq_pattern"])

    def test_verified_gsat_sources_are_traceable(self):
        data = json.loads(GSAT.read_text(encoding="utf-8"))
        curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
        known_codes = json.dumps(curriculum, ensure_ascii=False)
        seen = set()
        for entry in data["entries"]:
            key = (entry["year"], entry["question"])
            with self.subTest(source=key):
                self.assertNotIn(key, seen)
                seen.add(key)
                self.assertTrue(101 <= entry["year"] <= 115)
                self.assertRegex(entry["official_answer"], r"^[A-J]+$")
                self.assertIn(entry["type"], {"single", "multiple"})
                self.assertTrue(entry["core_concept"])
                for code in entry["related_codes"]:
                    self.assertIn(f'"{code}"', known_codes)
        wrong = {(m["year"], m["question"]) for m in data["misattributions"]}
        self.assertIn((105, 1), wrong)
        self.assertNotIn((105, 1), seen)

    def test_official_downloads_cover_every_gsat_year(self):
        data = json.loads(DOWNLOADS.read_text(encoding="utf-8"))
        files = data["files"]
        targets = [f["target"] for f in files]
        self.assertEqual(len(targets), len(set(targets)))
        gsat = {(f["year"], f["kind"]) for f in files if f["group"] == "gsat"}
        expected = {(y, k) for y in range(101, 116) for k in ("試題", "答案")}
        self.assertEqual(expected, gsat)
        self.assertTrue(any(f["group"] == "curriculum" for f in files))
        for f in files:
            with self.subTest(file=f["id"]):
                self.assertRegex(f["url"], r"^https://www\.(ceec|naer)\.edu\.tw/")
                self.assertTrue(f["target"].endswith(".pdf"))
                self.assertNotIn("..", f["target"])
                self.assertRegex(f["reference_sha256"], r"^[0-9a-f]{64}$")
                if f["group"] == "gsat":
                    # gsat_sources.py 以「{年}*試題*」「{年}*答案*」找檔
                    self.assertTrue(f["target"].startswith(f"gsat/{f['year']}學測自然_{f['kind']}"))
        verified = json.loads(GSAT.read_text(encoding="utf-8"))
        for entry in verified["entries"]:
            self.assertIn((entry["year"], "試題"), gsat)

    def test_fetch_dry_run_needs_no_network(self):
        import contextlib
        import io
        import sys
        import tempfile

        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import fetch_local_data
        finally:
            sys.path.pop(0)
        self.assertTrue(fetch_local_data.check_pdf(b"%PDF-1.7 ..."))
        self.assertFalse(fetch_local_data.check_pdf(b"<!DOCTYPE html>"))
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            code = fetch_local_data.main(["--dry-run", "--dest", tmp])
        self.assertEqual(0, code)
        self.assertIn("將下載 31", out.getvalue())

    def load_splitter(self):
        import sys

        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import split_node_item_sheet
        finally:
            sys.path.pop(0)
        return split_node_item_sheet

    def test_split_puts_practice_and_diagnostic_items_in_separate_files(self):
        import io
        import zipfile

        splitter = self.load_splitter()
        parts = splitter.split_docx_bytes(make_sheet())
        head = ["填寫說明：", "[表:題目：範例題]", "[分頁]"]
        self.assertEqual(
            head + ["練習題", "1. 理解題", "[表:題目：理解題目]", "2. 應用題", "[表:題目：應用題目]", "[空]", "[sectPr]"],
            outline(parts["練習題"]),
        )
        self.assertEqual(
            head + ["診斷題", "1. 診斷題1（經典題修改）", "[表:題目：診斷一題目]", "[分頁]",
                    "2. 診斷題2（經典題修改）", "[表:題目：診斷二題目]", "[空]", "[sectPr]"],
            outline(parts["診斷題"]),
        )
        for kind, data in parts.items():
            with self.subTest(kind=kind):
                names = zipfile.ZipFile(io.BytesIO(data)).namelist()
                self.assertEqual(["[Content_Types].xml", "word/document.xml", "word/media/image1.png"], names)

    def test_split_adds_missing_section_heading(self):
        splitter = self.load_splitter()
        parts = splitter.split_docx_bytes(make_sheet(section=False))
        self.assertEqual("練習題", outline(parts["練習題"])[3])
        self.assertEqual("診斷題", outline(parts["診斷題"])[3])

    def test_split_renumbers_heading_split_across_runs(self):
        splitter = self.load_splitter()
        fragment = "<w:p><w:r><w:t>1</w:t></w:r><w:r><w:t>2. 診斷</w:t></w:r><w:r><w:t>題1</w:t></w:r></w:p>"
        self.assertEqual(
            "<w:p><w:r><w:t>3</w:t></w:r><w:r><w:t>. 診斷</w:t></w:r><w:r><w:t>題1</w:t></w:r></w:p>",
            splitter.renumber(fragment, 3),
        )

    def test_split_cli_names_files_and_refuses_overwrite(self):
        import contextlib
        import io
        import tempfile

        splitter = self.load_splitter()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            source = Path(tmp) / "PXx-Vc-1-1_測試_P4_1025.docx"
            source.write_bytes(make_sheet())
            self.assertEqual(0, splitter.main([str(source)]))
            names = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(
                ["PXx-Vc-1-1_測試_P4_1025.docx", "PXx-Vc-1-1_測試_P4_1025_練習題.docx", "PXx-Vc-1-1_測試_P4_1025_診斷題.docx"],
                names,
            )
            self.assertEqual(1, splitter.main([str(source)]))
            self.assertEqual(0, splitter.main([str(Path(tmp) / "PXx-Vc-1-1_測試_P4_1025_練習題.docx")]))

    def test_tool_scripts_compile(self):
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                py_compile.compile(str(path), doraise=True)


if __name__ == "__main__":
    unittest.main()
