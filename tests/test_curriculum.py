import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "curriculum" / "stage5-physics.json"
PROJECT_DATA_PATH = (
    ROOT / "data" / "curriculum" / "project-node-catalog.json"
)
PROJECT_OVERRIDES_PATH = (
    ROOT / "data" / "curriculum" / "project-node-overrides.json"
)
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

    def test_cross_page_work_energy_note_is_not_truncated(self):
        entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))["entries"]
        for code in ["PBa-Va-1", "PBa-Va-2"]:
            with self.subTest(code=code):
                self.assertIn(
                    "外力作功之總和等於質點動能之變化量",
                    entries[code]["teaching_note"],
                )
                self.assertEqual(
                    [196, 197],
                    entries[code]["teaching_note_source_pages"],
                )

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

    def test_project_catalog_contains_sanitized_excel_nodes(self):
        self.assertTrue(PROJECT_DATA_PATH.exists())
        data = json.loads(PROJECT_DATA_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(data["entry_count"], 1000)
        node = data["entries"]["PBa-V.1-2-2"]
        self.assertEqual("技高物理A", node["course"])
        self.assertEqual("動能", node["title"])
        self.assertEqual("PBa-V.1-2", node["official_parent"])
        self.assertIn("物體會因此產生能量的變化", node["learning_content_explanation"])
        self.assertEqual(108, node["official_source"]["pdf_page"])
        self.assertEqual("A+B", node["evidence_level"])
        self.assertIn("source-conflict", node["mapping_status"])
        self.assertTrue(
            any("位能的定義" in item for item in node["conflicts"])
        )

        raw = PROJECT_DATA_PATH.read_text(encoding="utf-8")
        for forbidden_field in [
            '"author"',
            '"teacher"',
            '"group"',
            '"progress"',
            '"作者老師"',
            '"負責人"',
        ]:
            with self.subTest(forbidden_field=forbidden_field):
                self.assertNotIn(forbidden_field, raw)

    def test_technical_and_elective_nodes_resolve_to_scope_cards(self):
        common = load_common()
        curriculum = common.load_curriculum(DATA_PATH)
        projects = common.load_project_nodes(PROJECT_DATA_PATH)

        technical = common.resolve_curriculum_scope(
            "PBa-V.1-2-2",
            curriculum,
            projects,
        )
        self.assertEqual("PBa-V.1-2", technical["code"])
        self.assertEqual("technical-physics-a", technical["track"])
        self.assertEqual("動能", technical["project_title"])
        self.assertEqual("A+B", technical["evidence_level"])
        self.assertTrue(technical["conflicts"])

        elective = common.resolve_curriculum_scope(
            "PBa-Va-2.1",
            curriculum,
            projects,
        )
        self.assertEqual("PBa-Va-2", elective["code"])
        self.assertEqual("advanced-elective", elective["track"])
        self.assertEqual("動能", elective["project_title"])
        self.assertEqual("功能定理。", elective["statement"])

    def test_team_override_requires_no_raw_workbooks(self):
        common = load_common()
        catalog = common.load_project_nodes(
            PROJECT_DATA_PATH,
            overrides_path=None,
        )
        overrides = {
            "entries": {
                "PBa-V.1-2-2": {
                    "reason": "教師覆核後補強範圍提醒",
                    "evidence_refs": ["issue:#example", "curriculum:p.108"],
                    "expected": {"title": "動能"},
                    "set": {
                        "scope_constraints": [
                            "本測試證明協作者可不依賴原始 Excel 修正節點。"
                        ]
                    },
                }
            }
        }
        updated = common.apply_project_node_overrides(catalog, overrides)
        self.assertEqual(
            ["本測試證明協作者可不依賴原始 Excel 修正節點。"],
            updated["entries"]["PBa-V.1-2-2"]["scope_constraints"],
        )
        self.assertEqual(["PBa-V.1-2-2"], updated["overrides_applied"])

    def test_team_override_rejects_stale_or_private_changes(self):
        common = load_common()
        catalog = common.load_project_nodes(
            PROJECT_DATA_PATH,
            overrides_path=None,
        )
        stale = {
            "entries": {
                "PBa-V.1-2-2": {
                    "reason": "測試",
                    "evidence_refs": ["test"],
                    "expected": {"title": "位能"},
                    "set": {"title": "測試"},
                }
            }
        }
        with self.assertRaises(ValueError):
            common.apply_project_node_overrides(catalog, stale)
        private = {
            "entries": {
                "PBa-V.1-2-2": {
                    "reason": "測試",
                    "evidence_refs": ["test"],
                    "expected": {"title": "動能"},
                    "set": {"teacher": "不應寫入"},
                }
            }
        }
        with self.assertRaises(ValueError):
            common.apply_project_node_overrides(catalog, private)

    def test_tracked_override_file_is_shareable(self):
        self.assertTrue(PROJECT_OVERRIDES_PATH.exists())
        overrides = json.loads(
            PROJECT_OVERRIDES_PATH.read_text(encoding="utf-8")
        )
        self.assertIsInstance(overrides["entries"], dict)

    def test_unknown_code_is_not_guessed(self):
        common = load_common()
        catalog = common.load_curriculum(DATA_PATH)
        with self.assertRaises(common.UnknownCurriculumCode):
            common.resolve_official_code("PZZ-Vc-99-1", catalog)
        with self.assertRaises(common.UnknownCurriculumCode):
            common.resolve_curriculum_scope(
                "PZZ-V.1-99-1",
                catalog,
                common.load_project_nodes(PROJECT_DATA_PATH),
            )


if __name__ == "__main__":
    unittest.main()
