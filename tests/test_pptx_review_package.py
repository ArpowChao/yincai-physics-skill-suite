import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MANIFEST_PATH = SCRIPTS / "build_pptx_review_manifest.py"


def load_manifest_module():
    if not MANIFEST_PATH.exists():
        raise AssertionError("scripts/build_pptx_review_manifest.py is missing")
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "build_pptx_review_manifest_test",
            MANIFEST_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class PptxReviewPackageTests(unittest.TestCase):
    def test_manifest_maps_embedded_media_to_slide(self):
        module = load_manifest_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sample.pptx"
            output = root / "review"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "ppt/slides/slide1.xml",
                    '<p:sld xmlns:p="p" xmlns:a="a"><a:t>動能</a:t></p:sld>',
                )
                archive.writestr(
                    "ppt/slides/_rels/slide1.xml.rels",
                    '<Relationships xmlns="http://schemas.openxmlformats.org/'
                    'package/2006/relationships"><Relationship Id="rId1" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/'
                    '2006/relationships/video" '
                    'Target="../media/media1.mp4"/></Relationships>',
                )
                archive.writestr("ppt/media/media1.mp4", b"video-fixture")

            manifest = module.build_manifest(source, output)

            self.assertEqual(1, manifest["slide_count"])
            self.assertEqual(1, manifest["media_count"])
            self.assertEqual("動能", manifest["slides"][0]["text"])
            relation = manifest["slides"][0]["relationships"][0]
            self.assertEqual("video", relation["kind"])
            self.assertEqual("ppt/media/media1.mp4", relation["archive_path"])
            self.assertEqual(
                b"video-fixture",
                (output / "media" / "media1.mp4").read_bytes(),
            )

    def test_manifest_keeps_notes_and_source_hash(self):
        module = load_manifest_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sample.pptx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "ppt/slides/slide1.xml",
                    '<p:sld xmlns:p="p" xmlns:a="a"><a:t>觀察速率</a:t></p:sld>',
                )
                archive.writestr(
                    "ppt/notesSlides/notesSlide1.xml",
                    '<p:notes xmlns:p="p" xmlns:a="a"><a:t>先比較兩車</a:t>'
                    "</p:notes>",
                )

            manifest = module.build_manifest(source, root / "review")

            self.assertEqual(64, len(manifest["source_sha256"]))
            self.assertEqual(1, manifest["slides_with_notes"])
            self.assertIn("先比較兩車", manifest["slides"][0]["notes"])


if __name__ == "__main__":
    unittest.main()
