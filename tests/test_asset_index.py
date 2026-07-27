import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEXER_PATH = ROOT / "scripts" / "index_materials.py"
EXTRACTOR_PATH = ROOT / "scripts" / "extract_office_text.py"


def load_module(name: str, path: Path):
    if not path.exists():
        raise AssertionError(f"{path.relative_to(ROOT)} is missing")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class AssetIndexTests(unittest.TestCase):
    def test_filename_parser_keeps_project_code_and_status(self):
        indexer = load_module("index_materials", INDEXER_PATH)
        parsed = indexer.parse_material_filename(
            "PEb-Vc-4-1_牛頓第1定律_王老師_G3_0124_美工(已).pptx"
        )
        self.assertEqual("PEb-Vc-4-1", parsed["project_code"])
        self.assertEqual("牛頓第1定律", parsed["topic"])
        self.assertEqual("已", parsed["status_hint"])
        self.assertEqual("pptx", parsed["extension"])

    def test_artifact_type_comes_from_parent_directory(self):
        indexer = load_module("index_materials_type", INDEXER_PATH)
        self.assertEqual(
            "slides",
            indexer.classify_artifact(Path("普高一/投影片/demo.pptx")),
        )
        self.assertEqual(
            "worksheet",
            indexer.classify_artifact(Path("普高一/學習單/demo.docx")),
        )
        self.assertEqual(
            "diagnostic-question",
            indexer.classify_artifact(Path("普高一/診斷題/demo.docx")),
        )

    def test_indexer_is_read_only_and_returns_records(self):
        indexer = load_module("index_materials_build", INDEXER_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slides = root / "普高一" / "投影片"
            slides.mkdir(parents=True)
            sample = slides / "PKa-Vc-1-1_波速_吳老師_G3_0206_美工(已).pptx"
            sample.write_bytes(b"fixture")
            records = indexer.build_index(root)
            self.assertEqual(1, len(records))
            self.assertEqual("slides", records[0]["artifact_type"])
            self.assertEqual(sample.stat().st_size, records[0]["size_bytes"])
            self.assertEqual([sample], list(root.rglob("*.pptx")))

    def test_extracts_pptx_slides_and_notes(self):
        extractor = load_module("extract_office_text", EXTRACTOR_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pptx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "ppt/slides/slide1.xml",
                    '<p:sld xmlns:p="p" xmlns:a="a"><a:t>牛頓第一定律</a:t>'
                    "<a:t>物體維持運動狀態</a:t></p:sld>",
                )
                archive.writestr(
                    "ppt/notesSlides/notesSlide1.xml",
                    '<p:notes xmlns:p="p" xmlns:a="a"><a:t>請先觀察公車煞車</a:t></p:notes>',
                )
            result = extractor.extract_office(path)
            self.assertEqual("pptx", result["type"])
            self.assertIn("牛頓第一定律", result["slides"][0]["text"])
            self.assertIn("公車煞車", result["slides"][0]["notes"])

    def test_pptx_notes_ignore_slide_number_placeholders(self):
        extractor = load_module("extract_office_text_placeholders", EXTRACTOR_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pptx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "ppt/slides/slide1.xml",
                    '<p:sld xmlns:p="p" xmlns:a="a"><a:t>內容</a:t></p:sld>',
                )
                archive.writestr(
                    "ppt/notesSlides/notesSlide1.xml",
                    '<p:notes xmlns:p="p" xmlns:a="a"><p:sp><p:nvPr>'
                    '<p:ph type="body"/></p:nvPr><p:txBody/></p:sp>'
                    '<p:sp><p:nvPr><p:ph type="sldNum"/></p:nvPr>'
                    "<p:txBody><a:t>1</a:t></p:txBody></p:sp></p:notes>",
                )
            result = extractor.extract_office(path)
            self.assertEqual("", result["slides"][0]["notes"])

    def test_extracts_docx_paragraphs(self):
        extractor = load_module("extract_office_text_docx", EXTRACTOR_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "word/document.xml",
                    '<w:document xmlns:w="w"><w:body><w:p><w:r>'
                    "<w:t>觀察並記錄</w:t></w:r></w:p></w:body></w:document>",
                )
            result = extractor.extract_office(path)
            self.assertEqual("docx", result["type"])
            self.assertEqual(["觀察並記錄"], result["paragraphs"])


if __name__ == "__main__":
    unittest.main()
