import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "curriculum" / "stage5-physics.json"
COMMON_PATH = ROOT / "scripts" / "common.py"


def load_common():
    if not COMMON_PATH.exists():
        raise AssertionError("scripts/common.py is missing")
    spec = importlib.util.spec_from_file_location("suite_common", COMMON_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class CurriculumTests(unittest.TestCase):
    def test_curriculum_catalog_has_both_stage5_tracks(self):
        self.assertTrue(DATA_PATH.exists())
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        entries = data["entries"]
        self.assertGreaterEqual(len(entries), 110)
        self.assertIn("PEb-Vc-4", entries)
        self.assertIn("PKa-Vc-1", entries)
        self.assertIn("PEb-Va-15", entries)
        self.assertIn("PKc-Va-10", entries)
        self.assertEqual("mandatory", entries["PEb-Vc-4"]["track"])
        self.assertEqual("advanced-elective", entries["PEb-Va-15"]["track"])

    def test_every_entry_has_source_and_scope_note(self):
        self.assertTrue(DATA_PATH.exists())
        entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))["entries"]
        for code, entry in entries.items():
            with self.subTest(code=code):
                self.assertEqual(code, entry["code"])
                self.assertTrue(entry["statement"])
                self.assertTrue(entry["source"]["document"])
                self.assertIsInstance(entry["source"]["pdf_page"], int)
                self.assertTrue(entry["teaching_note"])

    def test_cross_page_teaching_note_keeps_mandatory_scope_boundary(self):
        entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))["entries"]
        note = entries["PEb-Vc-4"]["teaching_note"]
        self.assertIn("不涉及公式之推導與計算", note)
        self.assertIn(188, entries["PEb-Vc-4"]["teaching_note_source_pages"])

    def test_project_node_resolves_to_official_parent(self):
        common = load_common()
        catalog = common.load_curriculum(DATA_PATH)
        self.assertEqual(
            "PEb-Vc-4",
            common.resolve_official_code("PEb-Vc-4-1", catalog)["code"],
        )
        self.assertEqual(
            "PKa-Vc-1",
            common.resolve_official_code("PKa-Ⅴc-1-1-1", catalog)["code"],
        )
        self.assertEqual(
            "PKc-Va-10",
            common.resolve_official_code("PKc-Va-10-13", catalog)["code"],
        )

    def test_unknown_code_is_not_guessed(self):
        common = load_common()
        catalog = common.load_curriculum(DATA_PATH)
        with self.assertRaises(common.UnknownCurriculumCode):
            common.resolve_official_code("PZZ-Vc-99-1", catalog)


if __name__ == "__main__":
    unittest.main()
