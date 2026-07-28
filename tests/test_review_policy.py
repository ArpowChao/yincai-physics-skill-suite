import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "scripts" / "review_policy.py"
WORKBENCH_PATH = ROOT / "scripts" / "build_review_workbench.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ReviewPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_module("review_policy_test", POLICY_PATH)

    def test_accepts_inferred_big_idea_without_explicit_slide(self):
        review = {
            "inferred_big_idea": {
                "statement": "動能由質量與速率共同決定。",
                "evidence_slides": [3, 4, 6],
                "confidence": "high",
                "alignment_judgment": "跨頁內容一致，不需要另列大概念專頁。",
            },
            "content_scores": [
                {
                    "judgment": "可從活動穩定反推大概念。",
                    "minimal_fix": "不需補目標或大概念專頁。",
                }
            ],
            "priority_actions": [],
        }
        self.assertEqual([], self.policy.validate_review_policy(review))

    def test_rejects_gemini_style_explicit_label_requirement(self):
        review = {
            "content_scores": [
                {
                    "judgment": "缺乏 S2 大概念顯性標記。",
                    "minimal_fix": "在 Slide 3 標明大概念：交互作用。",
                }
            ],
            "priority_actions": ["新增一頁大概念專頁。"],
        }
        errors = self.policy.validate_review_policy(review)
        self.assertEqual(3, len(errors))
        self.assertTrue(all("不得" in error for error in errors))

    def test_workbench_refuses_policy_violating_review(self):
        workbench = load_module("build_review_workbench_test", WORKBENCH_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            (package / "manifest.json").write_text(
                json.dumps({"slides": [], "source_filename": "lesson.pptx"}),
                encoding="utf-8",
            )
            (package / "review-result.json").write_text(
                json.dumps(
                    {
                        "unit_code": "PBa-V.1-2-2",
                        "unit_title": "動能",
                        "content_scores": [
                            {
                                "judgment": "缺乏 S2 大概念顯性標記。",
                                "minimal_fix": "在 Slide 3 標明大概念。",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "違反專案審查政策"):
                workbench.build_workbench_data(package)


if __name__ == "__main__":
    unittest.main()
