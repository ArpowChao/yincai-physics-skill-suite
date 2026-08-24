import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
EXPECTED_SKILLS = {
    "chatcut-teaching-rough-cut",
    "video-narration-postproduction",
    "prepare-tts-transcript",
    "zh-tw-proofread",
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
    def test_chatcut_rough_cut_keeps_v1541_protection_contract(self):
        skill_dir = SKILLS_ROOT / "chatcut-teaching-rough-cut"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        rules = (
            skill_dir / "references" / "rough-cut-rules-v1.5.4.1.md"
        ).read_text(encoding="utf-8")
        template = (
            skill_dir / "references" / "teacher-input-template-v1.5.4.1.md"
        ).read_text(encoding="utf-8")
        for marker in [
            "V1.5.4.1 開場硬保護、檢核點精準保護與可追溯穩定版",
            "Atomic Block",
            "只保護最長 7 秒",
            "可編輯時間線",
            "SRT",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        for marker in [
            "先暫時保護原始素材前 15 秒",
            "前 7 秒",
            "不得只以音訊交叉淡化取代",
            "不得重新剪輯整支影片",
            "有效刪除清單",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, rules)
        self.assertIn("其他不可修改區段", template)

    def test_proofreader_accepts_pinned_github_terminology_evidence(self):
        skill = (
            SKILLS_ROOT / "zh-tw-proofread" / "SKILL.md"
        ).read_text(encoding="utf-8")
        evidence = (
            SKILLS_ROOT
            / "zh-tw-proofread"
            / "references"
            / "github-terminology-evidence.md"
        ).read_text(encoding="utf-8")
        for marker in [
            "GitHub 術語依據",
            "tag 或 commit",
            "GitHub 內容只作為名詞證據",
            "不執行",
            "只套用於本次校對",
            "共通規則",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        for marker in [
            "owner/repo:path@tag-or-sha",
            "未合併 PR",
            "access token",
            "去識別最小案例與測試",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, evidence)

    def test_video_narration_skill_keeps_production_gates(self):
        text = (
            SKILLS_ROOT / "video-narration-postproduction" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for marker in [
            "先選路徑",
            "220–280",
            "預設 0.5 秒",
            "0.15 秒",
            "2.9 秒",
            "3.1 秒",
            "低振幅零交叉",
            "這不是強制項目",
            "機器音",
        ]:
            self.assertIn(marker, text)

    def test_tts_pronunciation_tool_has_review_assets(self):
        required = [
            ROOT / "scripts" / "tts_pronunciation.py",
            ROOT / "data" / "tts-pronunciation" / "verified.json",
            ROOT / "data" / "tts-pronunciation" / "formulas.json",
            ROOT / "showcase" / "tts-pronunciation" / "index.html",
            ROOT / "showcase" / "tts-pronunciation" / "styles.css",
            ROOT / "showcase" / "tts-pronunciation" / "app.js",
            ROOT / "showcase" / "tts-pronunciation" / "cross-strait-candidates.js",
            ROOT / "data" / "tts-pronunciation" / "cross-strait-candidates.json",
            SKILLS_ROOT
            / "prepare-tts-transcript"
            / "references"
            / "pronunciation-sources.md",
        ]
        self.assertEqual([], [str(path.relative_to(ROOT)) for path in required if not path.exists()])

    def test_tts_skill_documents_sources_and_evidence_boundaries(self):
        source_doc = (
            SKILLS_ROOT
            / "prepare-tts-transcript"
            / "references"
            / "pronunciation-sources.md"
        ).read_text(encoding="utf-8")
        for marker in [
            "15,660",
            "51 個",
            "g0v/moedict-data",
            "g0v/moedict-data-csld",
            "a1e91196f84cd2f3456570906191615f477278c8",
            "g2pW",
            "不是 TTS 錯誤率",
            "已驗證替代",
        ]:
            self.assertIn(marker, source_doc)

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

    def test_proofread_skill_has_physics_source_policy(self):
        skill = (SKILLS_ROOT / "zh-tw-proofread" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        source_path = (
            SKILLS_ROOT
            / "zh-tw-proofread"
            / "references"
            / "physics-terminology-sources.md"
        )
        self.assertTrue(source_path.exists())
        source = source_path.read_text(encoding="utf-8")
        for marker in ["QUDT", "UCUM", "CLDR", "moedict-data", "待確認"]:
            self.assertIn(marker, skill + source)

        terminology = json.loads(
            (ROOT / "data" / "terminology" / "physics-terms.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("1.1.0", terminology["terminology_version"])
        policy = terminology["source_policy"]
        self.assertIn(
            "repo-curriculum-and-project-confirmed",
            policy["preferred_term_order"],
        )
        self.assertIn(
            "qudt-for-quantity-unit-dimension",
            policy["preferred_term_order"],
        )
        self.assertIn("不得自動覆寫", policy["conflict_rule"])

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


    def test_architect_confirms_scope_before_generating(self):
        # 交付形式與深度上限沒問就自己假設，是整份架構作廢的來源。
        text = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("開始前必須確認", text)
        for item in (
            "交付形式",
            "先備單元",
            "最少要帶走的一句話",
        ):
            with self.subTest(item=item):
                self.assertIn(item, text)
        self.assertIn("未取得答案前不生成架構", text)
        self.assertIn("不以假設代替提問", text)

    def test_architect_offers_candidates_before_committing(self):
        # 直接生成單一情境，使用者只能一輪一輪退回重做。
        text = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("10 個候選", text)
        self.assertIn("學生會說出的話", text)
        self.assertIn("迷思風險", text)
        self.assertIn("不得由物理概念反推類比", text)
        self.assertIn("未選定前不進入後續步驟", text)

    def test_inquiry_task_pattern_library(self):
        # 春修版證據：探究不是只有控變因一式，共歸納出七種題型。
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        library = rubric["s8_inquiry_task_patterns"]
        self.assertIn("審查時不得因教材未使用某型而扣分", library["scope"])
        names = [item["name"] for item in library["patterns"]]
        self.assertEqual(7, len(names))
        for expected in (
            "輪流固定一個變數，最後讓數字打架",
            "公式是選出來的，不是背出來的",
            "故意出一組比不出來的",
            "把數據畫線延伸出去",
            "做不出的實驗，就用想的＋AI 影片演出來",
            "反著問——怎麼做到、怎麼弄壞",
            "查真實數據，還要教怎麼查",
        ):
            self.assertIn(expected, names)

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("探究活動題型庫", architect)
        self.assertIn("s8_inquiry_task_patterns", architect)
        self.assertIn("探究活動有七種出題方法", architect)
        self.assertIn("不是只有控變因一式", architect)

    def test_application_task_pattern_library(self):
        # 春修版證據：應用另有四種題型，且不得只列裝置名稱。
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        library = rubric["s9_application_task_patterns"]
        self.assertIn("審查時不得因教材未使用某型而扣分", library["scope"])
        names = [item["name"] for item in library["patterns"]]
        self.assertEqual(5, len(names))
        for expected in (
            "拋真實購買問題，讓學生用規格做決定",
            "同一件事列三種做法，讓學生評比高下",
            "應用寫成回家做得到的驗證步驟",
            "四個問題一路追問，直接拿去問 AI",
            "兩個看起來一樣的現象，問異同",
        ):
            self.assertIn(expected, names)

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("應用活動題型庫", architect)
        self.assertIn("s9_application_task_patterns", architect)
        self.assertIn("應用活動有五種出題方法", architect)

    def test_inquiry_evidence_source_rule_blocks_generated_video_for_measurement(self):
        # 要從畫面讀數值、比例或間距時，證據不得來自生成式 AI 影片。
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        rule = rubric["s8_inquiry_task_patterns"]["evidence_source_rule"]
        self.assertIn("不看是哪一個 S 步驟", rule["rule"])
        self.assertIn("不得使用生成式 AI 影片", rule["rule"])
        for field in ("rationale", "fallback"):
            self.assertTrue(rule[field].strip())
        self.assertIn("伽利略", rule["examples"]["allowed"])
        self.assertIn("雙狹縫", rule["examples"]["disallowed"])

        # 思考實驗題型必須自己指回這條判準，否則會被讀成「AI 影片一律可用」。
        patterns = {
            item["id"]: item["rule"]
            for item in rubric["s8_inquiry_task_patterns"]["patterns"]
        }
        self.assertIn(
            "evidence_source_rule", patterns["thought-experiment-ai-video"]
        )

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("evidence_source_rule", architect)
        self.assertIn("不得使用生成式 AI 影片", architect)

    def test_application_transfer_distance_rule(self):
        # S9 的載體必須離開 S6／S8 的器材，只換光源或數字不算遷移。
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "nine-step.json").read_text(
                encoding="utf-8"
            )
        )
        rule = rubric["s9_application_task_patterns"]["transfer_distance_rule"]
        self.assertIn("必須離開", rule["rule"])
        self.assertIn("不算遷移", rule["rule"])
        self.assertTrue(rule["check"].strip())
        self.assertTrue(rule["example"].strip())

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("transfer_distance_rule", architect)
        self.assertIn("遷移距離", architect)
        self.assertIn("都用這課的新名詞講一遍", architect)
        self.assertIn("限一句、配白話翻譯", architect)

    def test_activity_frame_shared_rules(self):
        # 春修版共同慣例：比大小一個量大一個量小、最易搞混的例子直接寫進活動框。
        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("活動框共同守則", architect)
        self.assertIn("一個量大、另一個量小，才要動腦", architect)
        self.assertIn("直接寫進活動框備註", architect)

    def test_observation_sentence_upgrades(self):
        # S5 觀察句成對寫並預告活動現象；學生背過但不懂的公式也可以當起點。
        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("觀察句成對寫", architect)
        self.assertIn("有變化的、沒變化的都寫", architect)
        self.assertIn("觀察區就是活動的預告清單", architect)
        self.assertIn("也可以當起點", architect)
        self.assertIn("把背誦變成理解", architect)

    def test_single_big_idea_per_topic_selected_by_user(self):
        # 每個單元只能選一個大概念；生成端給選項，由使用者選定。
        data = json.loads(
            (ROOT / "data" / "big-ideas.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("大概念可以多個", data["selection_rule"])
        self.assertIn("由使用者選定", data["selection_rule"])
        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("大概念可以多個", architect)
        self.assertIn("只選一個", architect)
        self.assertIn("由使用者選定", architect)

    def test_change_and_stability_is_one_big_idea_not_two(self):
        # 「改變與穩定」是七項中的一項；拆成兩項會把七項誤算成八項。
        data = json.loads(
            (ROOT / "data" / "big-ideas.json").read_text(encoding="utf-8")
        )
        self.assertEqual(7, len(data["ideas"]))
        self.assertIn("「改變與穩定」是一項", data["selection_rule"])
        for text, label in (
            (data["source"]["note"], "big-ideas.json note"),
            (
                (SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md").read_text(
                    encoding="utf-8"
                ),
                "SKILL.md",
            ),
        ):
            with self.subTest(source=label):
                # 「改變」和「穩定」並列即為拆項寫法。
                self.assertNotIn("「改變」和「穩定」", text)
                self.assertIn("改變與穩定", text)

    def test_cross_agent_runtime_requires_user_iteration_decision(self):
        runtime = (ROOT / "references" / "cross-agent-runtime.md").read_text(
            encoding="utf-8"
        )
        for choice in ["只套用本次", "記為候選需求", "納入共通規則"]:
            self.assertIn(choice, runtime)
        self.assertIn("未取得選擇前", runtime)
        self.assertIn("不得自行把候選需求升級成共通規則", runtime)


    def test_transfer_question_rubric_is_optional_and_low_load(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "transfer-question.json").read_text(
                encoding="utf-8"
            )
        )
        # 未選用不構成缺失，審查不得因未使用而扣分——選配定位是向後相容的前提。
        self.assertEqual("optional-extension", rubric["status"])
        self.assertEqual("S9", rubric["applies_after"])
        self.assertIn("不得因未使用", rubric["source"]["note"])
        # 課末不再燒腦，是 C2 與 S8 探究的根本分工。
        limits = rubric["load_limits"]
        self.assertEqual(2, limits["integrated_concepts_max"])
        self.assertEqual(2, limits["reasoning_steps_max"])
        self.assertEqual("Aha", limits["affect"])
        rules = " ".join(rubric["iron_rules"])
        for marker in ["類比性借用", "保結構", "〔待查證〕", "不引入新概念"]:
            self.assertIn(marker, rules)
        for field in [
            "他領域情境",
            "同構說明",
            "保持的關係形狀",
            "最少他領域背景",
            "預期 Aha 點",
        ]:
            self.assertTrue(
                any(field in item for item in rubric["required_fields"]),
                field,
            )

    def test_transfer_question_keeps_entry_ban_and_closes_the_course(self):
        rubric = json.loads(
            (ROOT / "data" / "rubrics" / "transfer-question.json").read_text(
                encoding="utf-8"
            )
        )
        # S6 入口禁令與 C2 出口遷移是不同槽位，混用會讓體驗情境脫離學生經驗。
        slot = rubric["slot_rule"]
        self.assertIn("S6", slot["entry"])
        self.assertIn("不得由物理概念反推類比", slot["entry"])
        self.assertIn("出口", slot["exit"])
        self.assertIn("最後", rubric["placement"]["rule"])
        self.assertIn("S9", rubric["placement"]["rule"])

        architect = (
            SKILLS_ROOT / "physics-one-page-architect" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("跨域遷移題", architect)
        self.assertIn("transfer-question.json", architect)
        self.assertIn("類比性借用", architect)
        self.assertIn("同構", architect)
        self.assertIn("選配", architect)
        # 入口禁令原文必須保留，不得因新增出口遷移而被稀釋。
        self.assertIn("不得由物理概念反推類比", architect)

if __name__ == "__main__":
    unittest.main()
