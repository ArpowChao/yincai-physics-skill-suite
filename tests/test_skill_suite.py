import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
EXPECTED_SKILLS = {
    "physics-framework-checker",
    "physics-one-page-architect",
    "physics-slide-enhancer",
    "physics-worksheet-generator",
    "physics-literacy-question-creator",
    "physics-visual-style-guide",
    "physics-question-qa-checker",
    "physics-ppt-upgrader",
    "physics-misconception-prompting",
    "physics-unit-package-qc",
}
REQUIRED_HEADINGS = {
    "## Inputs",
    "## Workflow",
    "## Output contract",
    "## Stop conditions",
    "## Common mistakes",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---", 2)
    result = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return result


class SkillSuiteTests(unittest.TestCase):
    def test_expected_skills_exist(self):
        present = {
            path.name
            for path in SKILLS_ROOT.iterdir()
            if path.is_dir() and (path / "SKILL.md").exists()
        }
        self.assertEqual(EXPECTED_SKILLS, present)

    def test_every_skill_has_portable_contract(self):
        for name in sorted(EXPECTED_SKILLS):
            with self.subTest(skill=name):
                path = SKILLS_ROOT / name / "SKILL.md"
                text = path.read_text(encoding="utf-8")
                meta = parse_frontmatter(text)
                self.assertEqual({"name", "description"}, set(meta))
                self.assertEqual(name, meta["name"])
                self.assertTrue(meta["description"].startswith("Use when"))
                self.assertLessEqual(len(text.splitlines()), 500)
                self.assertFalse(
                    re.search(r"file:///|[A-Za-z]:[\\/]", text),
                    "Skill must not contain an absolute local path",
                )
                for heading in REQUIRED_HEADINGS:
                    self.assertIn(heading, text)

    def test_every_skill_has_openai_metadata(self):
        for name in sorted(EXPECTED_SKILLS):
            with self.subTest(skill=name):
                path = SKILLS_ROOT / name / "agents" / "openai.yaml"
                self.assertTrue(path.exists())
                text = path.read_text(encoding="utf-8")
                self.assertIn("display_name:", text)
                self.assertIn("short_description:", text)
                self.assertIn(f"${name}", text)

    def test_terminology_uses_standard_lenz_spelling(self):
        terms = json.loads(
            (ROOT / "data" / "terminology" / "physics-terms.json").read_text(
                encoding="utf-8"
            )
        )["terms"]
        preferred = {term["preferred"] for term in terms}
        self.assertIn("楞次定律", preferred)
        self.assertNotIn("冷次定律", preferred)

    def test_framework_infers_goal_and_big_idea_from_deck_evidence(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        steps = {item["id"]: item for item in rubric["steps"]}
        self.assertIn("單元名稱", " ".join(steps["S1"]["required_evidence"]))
        self.assertIn("一致性", " ".join(steps["S1"]["required_evidence"]))
        self.assertIn("反推", " ".join(steps["S2"]["required_evidence"]))
        self.assertIn("跨頁活動", " ".join(steps["S2"]["required_evidence"]))
        self.assertNotIn(
            "只有單元名稱沒有目標",
            steps["S1"]["common_failures"],
        )
        review_rule = (ROOT / "references" / "ppt-content-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("單元名稱作為學習目標錨點", review_rule)
        self.assertIn("不要求在投影片上明列", review_rule)


if __name__ == "__main__":
    unittest.main()
