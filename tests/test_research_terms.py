import json
import unittest
from pathlib import Path

from scripts.check_research_terms import (
    load_registry,
    scan_text,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "terminology" / "research-proper-terms.json"


class ZhTwProofreadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry(REGISTRY_PATH)

    def test_registry_has_traceable_sources_and_valid_references(self):
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        source_ids = [source["id"] for source in raw["sources"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertIn("elife-34995", source_ids)

        known_sources = set(source_ids)
        for term in raw["terms"]:
            self.assertTrue(term["source_ids"])
            self.assertLessEqual(set(term["source_ids"]), known_sources)
            for variant in term["variants"]:
                self.assertIn(variant["action"], {"replace", "review", "preserve"})

    def test_scan_finds_research_proper_names(self):
        text = "PPT SH 與 3M3 SH 出現在 E-Live 的研究中。"
        matches = scan_text(text, self.registry)
        corrections = {match["original"]: match["preferred"] for match in matches}
        self.assertEqual("PepTSh", corrections["PPT SH"])
        self.assertEqual("3M3SH", corrections["3M3 SH"])
        self.assertEqual("eLife", corrections["E-Live"])

    def test_scanner_reports_actions_but_never_rewrites_source(self):
        text = "PPT SH 與 3M3 SH"
        matches = scan_text(text, self.registry)
        self.assertEqual(text, "PPT SH 與 3M3 SH")
        self.assertTrue(all(item["action"] in {"replace", "review", "preserve"} for item in matches))

    def test_accepted_alias_is_preserved_and_unknown_name_is_not_invented(self):
        default_matches = scan_text("SH1446與不存在的專名XYZ", self.registry)
        self.assertEqual([], default_matches)

        known_matches = scan_text(
            "SH1446與不存在的專名XYZ", self.registry, include_known=True
        )
        self.assertEqual(1, len(known_matches))
        self.assertEqual("preserve", known_matches[0]["action"])
        self.assertEqual("SH1446", known_matches[0]["preferred"])

    def test_registry_contains_exact_requested_research_terms(self):
        self.assertEqual(
            {
                "PepTSh", "3M3SH", "S-Cys-Gly-3M3SH", "SH1446", "POT",
                "Staphylococcus hominis", "eLife", "X 射線晶體學",
            },
            {term["preferred"] for term in self.registry["terms"]},
        )

    def test_registry_exercises_all_three_manual_decision_states(self):
        self.assertEqual(
            {"replace", "review", "preserve"},
            {
                variant["action"]
                for term in self.registry["terms"]
                for variant in term["variants"]
            },
        )


if __name__ == "__main__":
    unittest.main()
