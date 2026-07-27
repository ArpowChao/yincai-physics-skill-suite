import importlib.util
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MANIFEST_PATH = SCRIPTS / "build_pptx_review_manifest.py"
WORKBENCH_PATH = SCRIPTS / "build_review_workbench.py"
SHARE_BUNDLE_PATH = SCRIPTS / "build_review_share_bundle.py"


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


def load_workbench_module():
    if not WORKBENCH_PATH.exists():
        raise AssertionError("scripts/build_review_workbench.py is missing")
    spec = importlib.util.spec_from_file_location(
        "build_review_workbench_test",
        WORKBENCH_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_share_bundle_module():
    if not SHARE_BUNDLE_PATH.exists():
        raise AssertionError("scripts/build_review_share_bundle.py is missing")
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location(
            "build_review_share_bundle_test",
            SHARE_BUNDLE_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class PptxReviewPackageTests(unittest.TestCase):
    def test_timestamped_output_dir_is_sortable_and_file_safe(self):
        module = load_manifest_module()
        output = module.timestamped_output_dir(
            Path("outputs/review-packages/PBa-V.1-2-2_動能"),
            datetime(2026, 7, 27, 23, 8, 15),
        )
        self.assertEqual(
            "PBa-V.1-2-2_動能_20260727-230815",
            output.name,
        )
        self.assertNotIn(":", output.name)

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

    def test_workbench_embeds_slides_media_and_framework(self):
        module = load_workbench_module()
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            (package / "manifest.json").write_text(
                """{
                  "source_filename": "sample.pptx",
                  "source_sha256": "abc123",
                  "slides": [
                    {"slide": 1, "text": "動能", "notes": "", "relationships": []}
                  ]
                }""",
                encoding="utf-8",
            )
            (package / "review-result.json").write_text(
                """{
                  "unit_code": "PBa-V.1-2-2",
                  "unit_title": "動能",
                  "decision": "HOLD",
                  "nine_step_summary": {
                    "complete": ["S4"],
                    "partial": ["S1"],
                    "insufficient": ["S2"]
                  },
                  "lesson_path": "情境 S1 → 公式 S1",
                  "suggested_path": "情境 S1 → 補證據 → 形成概念",
                  "inferred_big_idea": {
                    "statement": "動能由質量與速率共同決定",
                    "evidence_slides": [1],
                    "confidence": "high",
                    "alignment_judgment": "活動與單元名稱一致"
                  },
                  "content_scores": [{
                    "criterion": "學生任務與輸出",
                    "score": 1,
                    "evidence": "S1 只有觀看",
                    "judgment": "缺少可判定輸出",
                    "minimal_fix": "加入比較表"
                  }],
                  "critical_gates": [{
                    "gate": "關鍵任務沒有輸出或回饋",
                    "triggered": true,
                    "evidence": "S1"
                  }],
                  "slide_ledger": [{
                    "slide": 1,
                    "teaching_role": "engage",
                    "primary_question": "哪一個物體動能較大？",
                    "learner_action": "比較質量與速率",
                    "expected_output": "選擇並說明理由",
                    "feedback": "下一頁用數據驗證",
                    "prerequisite": "速率與質量",
                    "next_link": "下一頁建立關係",
                    "architecture_elements": ["S5", "S6"],
                    "continuity_tags": ["MISSING-BRIDGE"]
                  }],
                  "media_alignment": [{
                    "slide": 1,
                    "media": "media1.mp4",
                    "role": "context",
                    "rating": "partial",
                    "reason": "只能作為情境",
                    "observation_focus": "比較兩車",
                    "comparison": "質量與速率",
                    "learner_output": "寫出還缺的資料",
                    "used_later": "下一頁資料表"
                  }],
                  "slide_findings": [{
                    "slide": 1,
                    "severity": "major",
                    "continuity_tag": "MISSING-BRIDGE",
                    "title": "缺少控制變因",
                    "detail": "影片沒有量測資料",
                    "action": "補資料表"
                  }]
                }""",
                encoding="utf-8",
            )

            data = module.build_workbench_data(package)
            html = module.build_html(data)

            self.assertEqual("slides/slide-01.png", data["slides"][0]["image"])
            self.assertEqual("media/media1.mp4", data["slides"][0]["media"][0]["path"])
            self.assertEqual(
                "選擇並說明理由",
                data["slides"][0]["ledger"]["expected_output"],
            )
            self.assertEqual("情境 S1 → 公式 S1", data["lesson_path"])
            self.assertEqual(
                "動能由質量與速率共同決定",
                data["inferred_big_idea"]["statement"],
            )
            self.assertTrue(data["critical_gates"][0]["triggered"])
            self.assertIn("教材審查工作台", html)
            self.assertIn("缺少控制變因", html)
            self.assertIn("教學鏈", html)
            self.assertIn("MISSING-BRIDGE", html)
            self.assertIn("學生任務與輸出", html)
            self.assertIn("推定大概念", html)
            self.assertIn("匯出審查紀錄", html)
            self.assertNotIn("fonts.googleapis.com", html)

    def test_workbench_escapes_script_terminator_in_embedded_data(self):
        module = load_workbench_module()
        data = {
            "unit_code": "TEST",
            "unit_title": "</script><script>alert(1)</script>",
            "source_sha256": "abc",
            "slides": [],
        }
        html = module.build_html(data)
        embedded = html.split("const DATA = ", 1)[1].split(";\n", 1)[0]
        self.assertNotIn("</script", embedded.lower())

    def test_share_bundle_excludes_original_and_sanitizes_filename(self):
        module = load_share_bundle_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            output = root / "share"
            (package / "slides").mkdir(parents=True)
            (package / "media").mkdir()
            (package / "slides" / "slide-01.png").write_bytes(b"slide")
            (package / "media" / "media1.mp4").write_bytes(b"video")
            (package / "original.pptx").write_bytes(b"private-original")
            (package / "transcripts").mkdir()
            (package / "transcripts" / "media1.json").write_text(
                '{"text": "unreliable"}',
                encoding="utf-8",
            )
            (package / "review-report.md").write_text("# Review", encoding="utf-8")
            (package / "manifest.json").write_text(
                """{
                  "source_filename": "PBa-V.1-2-2_動能_王老師.pptx",
                  "source_sha256": "abc123",
                  "slides": [
                    {"slide": 1, "text": "動能", "notes": "", "relationships": []}
                  ]
                }""",
                encoding="utf-8",
            )
            (package / "review-result.json").write_text(
                """{
                  "unit_code": "PBa-V.1-2-2",
                  "unit_title": "動能",
                  "decision": "HOLD",
                  "nine_step_summary": {},
                  "media_alignment": [{
                    "slide": 1,
                    "media": "media1.mp4",
                    "role": "context",
                    "rating": "partial",
                    "reason": "只作為情境"
                  }]
                }""",
                encoding="utf-8",
            )

            manifest = module.build_share_bundle(
                package,
                output,
                include_playback=False,
            )

            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "review-workbench.html").is_file())
            self.assertTrue((output / "README-請先看.txt").is_file())
            self.assertTrue((output / "slides" / "slide-01.png").is_file())
            self.assertTrue((output / "media" / "media1.mp4").is_file())
            self.assertFalse((output / "original.pptx").exists())
            self.assertFalse((output / "transcripts").exists())
            self.assertFalse((output / "playback.mp4").exists())
            workbench = (output / "review-workbench.html").read_text(encoding="utf-8")
            self.assertNotIn("王老師", workbench)
            self.assertEqual("PBa-V.1-2-2", manifest["unit_code"])

            zip_path = module.create_zip(output)
            self.assertTrue(zip_path.is_file())
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("index.html", names)
            self.assertIn("slides/slide-01.png", names)
            self.assertIn("media/media1.mp4", names)
            self.assertNotIn("original.pptx", names)


if __name__ == "__main__":
    unittest.main()
