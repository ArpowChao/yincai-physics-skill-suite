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

    def test_nine_step_declares_chain_anchors(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        anchors = rubric["chain_anchors"]
        self.assertEqual("S6", anchors["概念鏈"]["anchor"])
        self.assertEqual("S8", anchors["探究鏈"]["anchor"])
        self.assertEqual("S9", anchors["應用鏈"]["anchor"])
        self.assertEqual("S7", anchors["概念鏈"]["supported_by"])
        self.assertEqual("S2", anchors["探究鏈"]["supported_by"])

    def test_nine_step_separates_generation_and_teaching_order(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        sequence = rubric["teaching_order"]["sequence"]
        self.assertEqual(["S6", "S5", "S4", "S8", "S3", "S9"], sequence)
        # S1 外殼、S2 設計套路、S7 素材：都不是獨立教學時刻。
        for step in ("S1", "S2", "S7"):
            self.assertNotIn(step, sequence)
        self.assertLess(sequence.index("S8"), sequence.index("S3"))
        edges = rubric["generation_order"]["edges"]
        for edge in (
            {"from": "S2", "to": "S8", "relation": "套路"},
            {"from": "S8", "to": "S3", "relation": "形成"},
            {"from": "S3", "to": "S1", "relation": "內涵"},
            {"from": "S6", "to": "S5", "relation": "引出"},
            {"from": "S5", "to": "S4", "relation": "轉換", "via": "S7"},
        ):
            self.assertIn(edge, edges)

    def test_step_names_match_source_framework(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        names = {item["id"]: item["name"] for item in rubric["steps"]}
        self.assertEqual(
            {
                "S1": "教學知識",
                "S2": "大概念",
                "S3": "原理原則",
                "S4": "概念",
                "S5": "事實",
                "S6": "學生體驗情境連結問題討論",
                "S7": "事實—逐步到—概念",
                "S8": "探究活動",
                "S9": "有感應用",
            },
            names,
        )
        groups = rubric["structure_groups"]
        self.assertEqual(["S1", "S2", "S3", "S4", "S5"], groups["知識結構"]["steps"])
        self.assertEqual(["S6", "S7", "S8", "S9"], groups["教學活動"]["steps"])

    def test_big_ideas_use_seven_exclusive_confirmed_names(self):
        data = json.loads(
            (ROOT / "data" / "big-ideas.json").read_text(encoding="utf-8")
        )
        ideas = {item["id"]: item["zh_tw"] for item in data["ideas"]}
        self.assertEqual(7, len(ideas))
        self.assertEqual("改變與穩定", ideas["change-and-stability"])
        self.assertEqual("系統", ideas["system"])
        self.assertEqual("結構與功能", ideas["structure-and-function"])
        self.assertNotIn("change", ideas)
        self.assertNotIn("balance", ideas)
        self.assertNotIn("structure", ideas)
        self.assertIn("只能", data["selection_rule"])
        self.assertIn("不得使用主／副大概念", data["selection_rule"])

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("只選一個", architect)
        self.assertIn("不使用主／副大概念", architect)
        self.assertIn("改變與穩定", architect)
        self.assertIn("結構與功能", architect)

    def test_rubric_readers_declare_direction(self):
        directions = {
            "physics-one-page-architect": "正向生成",
            "physics-worksheet-generator": "正向生成",
            "physics-framework-checker": "逆向審查",
            "physics-ppt-upgrader": "逆向審查",
            "physics-unit-package-qc": "逆向審查",
        }
        for name, direction in directions.items():
            with self.subTest(skill=name):
                text = (SKILLS_ROOT / name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn("nine-step.json", text)
                self.assertIn(direction, text)

    def test_architect_anchors_chains_instead_of_flat_coverage(self):
        text = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        # 「合計覆蓋」把九步驟讀成打勾清單，是三鏈錯置的來源。
        self.assertNotIn("三鏈合計覆蓋", text)
        self.assertIn("錨定 S6", text)
        self.assertIn("錨定 S8", text)
        self.assertIn("錨定 S9", text)
        self.assertIn("教學順序", text)

    def test_student_language_requires_stage_calibration(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        s5 = {item["id"]: item for item in rubric["steps"]}["S5"]
        self.assertIn("學習階段與程度基準", s5["required_evidence"])
        calibration = s5["calibration"]
        self.assertTrue(calibration["rule"])
        self.assertIn("國中會考 B 基礎", calibration["baselines"])
        self.assertTrue(calibration["checks"])
        # 沒有基準就寫學生說法，是 S5 飄移的來源。
        for failure in (
            "未標明學習階段與程度基準就寫學生說法",
            "用低於實際學習階段的語言假造學生說法",
            "把學生在前一學習階段已取得的用詞列為本單元要教的 S4",
        ):
            self.assertIn(failure, s5["common_failures"])

    def test_experience_context_is_familiar_or_directly_observable(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        s6 = {item["id"]: item for item in rubric["steps"]}["S6"]
        self.assertIn("已有經驗", s6["purpose"])
        self.assertIn("容易直接觀察", s6["purpose"])
        self.assertIn("離學生生活太遠", s6["purpose"])
        self.assertTrue(
            any("直接可觀察性" in item for item in s6["required_evidence"])
        )

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("已有經驗", architect)
        self.assertIn("容易直接觀察", architect)
        self.assertIn("離學生生活太遠", architect)

    def test_ai_experience_video_is_short_and_single_focus(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        s6 = {item["id"]: item for item in rubric["steps"]}["S6"]
        video = s6["ai_video"]
        self.assertEqual(2, video["duration_seconds"]["minimum"])
        self.assertEqual(10, video["duration_seconds"]["maximum"])
        self.assertIn("一個", video["role"])
        self.assertIn("不承擔完整背景", video["role"])
        self.assertTrue(video["required_support"])

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("2–10 秒", architect)
        self.assertIn("一個可重播觀察", architect)
        self.assertIn("不讓短片承擔完整背景", architect)

    def test_architect_requires_ai_video_storyboard_cards_for_three_activities(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        contract = rubric["ai_video_storyboard_contract"]
        self.assertEqual(
            ["S6 體驗活動", "S8 探究活動", "S9 應用活動"],
            contract["applies_to"],
        )
        self.assertEqual({"min": 2, "max": 10}, contract["default_duration_seconds"])
        for field in [
            "開場畫面",
            "關鍵動作或變化",
            "收尾畫面",
            "鏡位與構圖",
            "畫面中可見的物理證據",
            "學生觀看任務",
            "不可直接揭露的答案",
        ]:
            self.assertIn(field, contract["required_fields"])

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("AI 影片畫面規格卡", architect)
        self.assertIn("S6 體驗活動、S8 探究活動、S9 應用活動各輸出一張", architect)
        self.assertIn("不使用理由、替代表徵", architect)

    def test_architect_states_stage_baseline(self):
        text = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("學習階段與程度基準", text)


    def test_cross_agent_runtime_requires_user_iteration_decision(self):
        runtime = (ROOT / "references" / "cross-agent-runtime.md").read_text(
            encoding="utf-8"
        )
        for choice in ["只套用本次", "記為候選需求", "納入共通規則"]:
            self.assertIn(choice, runtime)
        self.assertIn("未取得選擇前", runtime)
        self.assertIn("不得自行把候選需求升級成共通規則", runtime)


if __name__ == "__main__":
    unittest.main()
