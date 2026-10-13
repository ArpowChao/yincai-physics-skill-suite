import json
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "yincai-physics-node-items" / "SKILL.md"
PERFORMANCE = ROOT / "data" / "curriculum" / "stage5-learning-performance.json"
GSAT = ROOT / "data" / "gsat" / "verified-physics-sources.json"
CURRICULUM = ROOT / "data" / "curriculum" / "stage5-physics.json"
DOWNLOADS = ROOT / "data" / "sources" / "official-downloads.json"
SCRIPTS = [
    ROOT / "scripts" / "gsat_sources.py",
    ROOT / "scripts" / "build_node_item_sheet.py",
    ROOT / "scripts" / "audit_node_item_sheet.py",
    ROOT / "scripts" / "fetch_local_data.py",
]


class NodeItemSkillTests(unittest.TestCase):
    def test_skill_keeps_item_writing_contract(self):
        text = SKILL.read_text(encoding="utf-8")
        for marker in [
            "1. 理解題",
            "2. 應用題",
            "診斷題1（經典題修改）",
            "改編自 ○○○ 學測自然第 N 題",
            "scripts/resolve_curriculum.py",
            "scripts/gsat_sources.py",
            "scripts/build_node_item_sheet.py",
            "scripts/audit_node_item_sheet.py",
            "stage5-learning-performance.json",
            "不停下來詢問",
            "正解不可明顯最長",
            "不得憑記憶寫題號",
            "105 學測第 1 題",
            "不用破折號",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_learning_performance_catalog_covers_all_mandatory_codes(self):
        data = json.loads(PERFORMANCE.read_text(encoding="utf-8"))
        codes = [entry["code"] for entry in data["entries"]]
        expected = {
            "ti-Vc-1", "tr-Vc-1", "tc-Vc-1", "tm-Vc-1",
            "po-Vc-1", "po-Vc-2", "pe-Vc-1", "pe-Vc-2",
            "pa-Vc-1", "pa-Vc-2", "pc-Vc-1", "pc-Vc-2",
            "ai-Vc-1", "ai-Vc-2", "ai-Vc-3",
            "ah-Vc-1", "ah-Vc-2",
            "an-Vc-1", "an-Vc-2", "an-Vc-3",
        }
        self.assertEqual(expected, set(codes))
        self.assertEqual(len(codes), len(set(codes)))
        allowed = {"high", "medium", "low", "not_suitable"}
        for entry in data["entries"]:
            with self.subTest(code=entry["code"]):
                self.assertTrue(entry["statement"])
                self.assertIn(entry["mcq_suitability"], allowed)
                self.assertIn(entry["source"]["pdf_page"], {35, 36, 37})
                if entry["code"].startswith("ai-"):
                    self.assertEqual("not_suitable", entry["mcq_suitability"])
                else:
                    self.assertTrue(entry["mcq_pattern"])

    def test_verified_gsat_sources_are_traceable(self):
        data = json.loads(GSAT.read_text(encoding="utf-8"))
        curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
        known_codes = json.dumps(curriculum, ensure_ascii=False)
        seen = set()
        for entry in data["entries"]:
            key = (entry["year"], entry["question"])
            with self.subTest(source=key):
                self.assertNotIn(key, seen)
                seen.add(key)
                self.assertTrue(101 <= entry["year"] <= 115)
                self.assertRegex(entry["official_answer"], r"^[A-J]+$")
                self.assertIn(entry["type"], {"single", "multiple"})
                self.assertTrue(entry["core_concept"])
                for code in entry["related_codes"]:
                    self.assertIn(f'"{code}"', known_codes)
        wrong = {(m["year"], m["question"]) for m in data["misattributions"]}
        self.assertIn((105, 1), wrong)
        self.assertNotIn((105, 1), seen)

    def test_official_downloads_cover_every_gsat_year(self):
        data = json.loads(DOWNLOADS.read_text(encoding="utf-8"))
        files = data["files"]
        targets = [f["target"] for f in files]
        self.assertEqual(len(targets), len(set(targets)))
        gsat = {(f["year"], f["kind"]) for f in files if f["group"] == "gsat"}
        expected = {(y, k) for y in range(101, 116) for k in ("試題", "答案")}
        self.assertEqual(expected, gsat)
        self.assertTrue(any(f["group"] == "curriculum" for f in files))
        for f in files:
            with self.subTest(file=f["id"]):
                self.assertRegex(f["url"], r"^https://www\.(ceec|naer)\.edu\.tw/")
                self.assertTrue(f["target"].endswith(".pdf"))
                self.assertNotIn("..", f["target"])
                self.assertRegex(f["reference_sha256"], r"^[0-9a-f]{64}$")
                if f["group"] == "gsat":
                    # gsat_sources.py 以「{年}*試題*」「{年}*答案*」找檔
                    self.assertTrue(f["target"].startswith(f"gsat/{f['year']}學測自然_{f['kind']}"))
        verified = json.loads(GSAT.read_text(encoding="utf-8"))
        for entry in verified["entries"]:
            self.assertIn((entry["year"], "試題"), gsat)

    def test_fetch_dry_run_needs_no_network(self):
        import contextlib
        import io
        import sys
        import tempfile

        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import fetch_local_data
        finally:
            sys.path.pop(0)
        self.assertTrue(fetch_local_data.check_pdf(b"%PDF-1.7 ..."))
        self.assertFalse(fetch_local_data.check_pdf(b"<!DOCTYPE html>"))
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            code = fetch_local_data.main(["--dry-run", "--dest", tmp])
        self.assertEqual(0, code)
        self.assertIn("將下載 31", out.getvalue())

    def test_tool_scripts_compile(self):
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                py_compile.compile(str(path), doraise=True)


if __name__ == "__main__":
    unittest.main()
