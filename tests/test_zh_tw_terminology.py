import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERMS_PATH = ROOT / "data" / "terminology" / "zh-tw-science-terms.json"
SOURCES_PATH = ROOT / "data" / "terminology" / "zh-tw-science-term-sources.json"
SKILL_PATH = ROOT / ".agents" / "skills" / "zh-tw-proofread" / "SKILL.md"
REFERENCE_PATH = (
    ROOT / ".agents" / "skills" / "zh-tw-proofread" / "references" / "zh-terminology-sources.md"
)
ALLOWED_CATEGORIES = {"asr-homophone", "cross-strait", "orthography"}
ALLOWED_DOMAINS = {"physics", "chemistry", "biology", "general-science"}


def load_terms() -> dict:
    return json.loads(TERMS_PATH.read_text(encoding="utf-8"))


def load_sources() -> dict:
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


class TerminologyDataTests(unittest.TestCase):
    def test_data_file_has_required_top_level_fields(self):
        data = load_terms()
        for field in [
            "terminology_version",
            "locale",
            "evidence_policy",
            "categories",
            "evidence_codes",
            "entries",
        ]:
            self.assertIn(field, data, f"缺少頂層欄位 {field}")
        self.assertEqual("zh-TW", data["locale"])
        self.assertTrue(data["entries"], "entries 不得為空")

    def test_every_source_is_versioned_and_addressable(self):
        data = load_sources()
        source_ids = set()
        for source in data["sources"]:
            source_id = source.get("id", "")
            self.assertTrue(source_id, "來源必須有 id")
            self.assertNotIn(source_id, source_ids, f"來源 id 重複：{source_id}")
            source_ids.add(source_id)
            self.assertTrue(source.get("url"), f"{source_id} 缺少 URL")
            self.assertTrue(source.get("version"), f"{source_id} 缺少版本或擷取日期")

    def test_every_entry_resolves_to_traceable_source_records(self):
        terms = load_terms()
        source_data = load_sources()
        source_ids = {source["id"] for source in source_data["sources"]}
        mappings = {
            mapping["preferred"]: mapping["source_refs"]
            for mapping in source_data["term_sources"]
        }
        self.assertEqual(
            {entry["preferred"] for entry in terms["entries"]},
            set(mappings),
            "詞條與來源索引必須一一對應",
        )
        for entry in terms["entries"]:
            refs = mappings[entry["preferred"]]
            self.assertTrue(refs, f"{entry['preferred']} 缺少來源引用")
            for ref in refs:
                self.assertIn(
                    ref.get("source_id"),
                    source_ids,
                    f"{entry['preferred']} 引用不存在的來源 {ref.get('source_id')}",
                )
                self.assertTrue(
                    ref.get("locator"),
                    f"{entry['preferred']} 的來源引用缺少查詢鍵或記錄定位",
                )

    def test_every_entry_declares_category_domain_and_evidence(self):
        data = load_terms()
        codes = set(data["evidence_codes"])
        for entry in data["entries"]:
            preferred = entry.get("preferred", "")
            self.assertTrue(preferred, "每條都必須有 preferred")
            self.assertIn(entry.get("category"), ALLOWED_CATEGORIES, preferred)
            self.assertIn(entry.get("domain"), ALLOWED_DOMAINS, preferred)
            evidence = entry.get("evidence", [])
            self.assertTrue(evidence, f"{preferred} 缺少 evidence")
            for code in evidence:
                self.assertIn(code, codes, f"{preferred} 使用未定義的 evidence 代碼 {code}")

    def test_preferred_terms_are_unique(self):
        preferred = [entry["preferred"] for entry in load_terms()["entries"]]
        duplicates = {term for term in preferred if preferred.count(term) > 1}
        self.assertFalse(duplicates, f"preferred 重複：{sorted(duplicates)}")

    def test_variant_never_equals_its_own_preferred(self):
        for entry in load_terms()["entries"]:
            self.assertNotIn(
                entry["preferred"],
                entry.get("variants", []),
                f"{entry['preferred']} 的 variants 含有自己，會造成無限取代",
            )

    def test_variants_do_not_collide_across_entries(self):
        seen: dict[str, str] = {}
        for entry in load_terms()["entries"]:
            for variant in entry.get("variants", []):
                self.assertNotIn(
                    variant,
                    seen,
                    f"variant「{variant}」同時指向 {seen.get(variant)} 與 {entry['preferred']}",
                )
                seen[variant] = entry["preferred"]

    def test_mass_quality_entry_carries_context_guard(self):
        """物理「質量」被誤改成「品質」是本 suite 已知的最高風險錯誤。"""
        entries = {entry["preferred"]: entry for entry in load_terms()["entries"]}
        self.assertIn("品質", entries)
        guard = entries["品質"].get("context_guard", "")
        self.assertIn("質量", guard)
        self.assertIn("物理", guard)


class ScanBehaviourTests(unittest.TestCase):
    def scan(self, text: str, domain: str | None = None) -> dict:
        from scripts.check_zh_terms import scan_text

        return scan_text(text, load_terms()["entries"], domain)

    def test_scanner_reports_real_transcript_errors(self):
        text = "我們鼎密含氹分泌出來的前驅物，科學家先拿大廠感菌當測試平台，再把弱氨酸換掉。"
        found = {hit["found"]: hit["preferred"] for hit in self.scan(text)["hits"]}

        self.assertEqual("頂泌汗腺", found.get("鼎密含氹"))
        self.assertEqual("大腸桿菌", found.get("大廠感菌"))
        self.assertEqual("酪胺酸", found.get("弱氨酸"))

    def test_longest_variant_wins_over_substring(self):
        """「雙生態」不可同時被報成「生態」。"""
        hits = self.scan("這是一個雙生態的分子。")["hits"]

        self.assertEqual(1, len(hits))
        self.assertEqual("雙生態", hits[0]["found"])
        self.assertEqual("雙胜肽", hits[0]["preferred"])

    def test_guarded_entry_is_flagged_for_human_review(self):
        hits = self.scan("這個產品的質量很好。")["hits"]

        self.assertEqual(1, len(hits))
        self.assertTrue(hits[0]["requires_context_review"])
        self.assertIn("物理", hits[0]["context_guard"])

    def test_report_never_authorises_automatic_replacement(self):
        report = self.scan("流醇基團卡住了通道。")

        self.assertFalse(report["auto_replace"])
        self.assertIn("人工覆核", report["reminder"])

    def test_domain_filter_limits_results(self):
        text = "力距是物理量，硫醇是化學物質。"

        physics_only = self.scan(text, domain="physics")["hits"]
        self.assertEqual(["力距"], [hit["found"] for hit in physics_only])

    def test_clean_text_produces_no_false_positive(self):
        report = self.scan("向量與純量的差別在於方向。")

        self.assertEqual(0, report["total_hits"])


class CliTests(unittest.TestCase):
    def test_cli_survives_a_cp950_console(self):
        """ASR 誤植常帶罕用字（如「氹」），cp950 主控台不得讓工具崩潰。"""
        import io
        import sys
        import tempfile

        from scripts import check_zh_terms

        with tempfile.TemporaryDirectory() as folder:
            transcript = Path(folder) / "transcript.txt"
            transcript.write_text("我們鼎密含氹分泌出來的。", encoding="utf-8")

            console = io.TextIOWrapper(io.BytesIO(), encoding="cp950", errors="strict")
            original = sys.stdout
            sys.stdout = console
            try:
                exit_code = check_zh_terms.main([str(transcript)])
            finally:
                sys.stdout = original

        self.assertEqual(0, exit_code)

    def test_cli_reports_missing_transcript_without_traceback(self):
        import contextlib
        import io

        from scripts import check_zh_terms

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = check_zh_terms.main(["does-not-exist.txt"])

        self.assertEqual(2, exit_code)
        self.assertIn("找不到逐字稿", stderr.getvalue())

    def test_cli_rejects_blank_transcript(self):
        import contextlib
        import io
        import tempfile

        from scripts import check_zh_terms

        with tempfile.TemporaryDirectory() as folder:
            transcript = Path(folder) / "blank.txt"
            transcript.write_text(" \n\t", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = check_zh_terms.main([str(transcript)])

        self.assertEqual(2, exit_code)
        self.assertIn("空白", stderr.getvalue())


class SkillWiringTests(unittest.TestCase):
    def test_skill_references_the_terminology_data_and_policy(self):
        text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("data/terminology/zh-tw-science-terms.json", text)
        self.assertIn("data/terminology/zh-tw-science-term-sources.json", text)
        self.assertIn("references/zh-terminology-sources.md", text)
        self.assertIn("check_zh_terms.py", text)

    def test_reference_document_states_evidence_priority(self):
        text = REFERENCE_PATH.read_text(encoding="utf-8")

        self.assertIn("證據優先序", text)
        self.assertIn("terms.naer.edu.tw", text)

    def test_skill_still_forbids_unverified_proper_noun_rewrite(self):
        text = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("待確認", text)
        self.assertIn("## Stop conditions", text)


if __name__ == "__main__":
    unittest.main()
