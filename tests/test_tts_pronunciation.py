import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TtsPronunciationTests(unittest.TestCase):
    def load_rules(self):
        from scripts.tts_pronunciation import load_rules

        return load_rules(ROOT / "data" / "tts-pronunciation" / "verified.json")

    def test_confirmed_phrase_is_replaced_without_changing_source(self):
        from scripts.tts_pronunciation import analyze_text

        source = "他是這部電影的主角，也是一個重要角色。"
        result = analyze_text(source, self.load_rules())

        self.assertEqual(source, result["source_text"])
        self.assertEqual(
            "他是這部電影的主腳，也是一個重要腳色。",
            result["speech_text"],
        )
        self.assertEqual(["主角", "角色"], [item["original"] for item in result["changes"]])
        self.assertTrue(all(item["verified"] for item in result["changes"]))

    def test_longest_phrase_wins_without_replacing_unrelated_character(self):
        from scripts.tts_pronunciation import analyze_text

        rules = [
            {"original": "角", "spoken": "腳", "verified": True},
            {"original": "主角", "spoken": "主腳", "verified": True},
        ]
        result = analyze_text("主角研究三角形。", rules)

        self.assertEqual("主腳研究三腳形。", result["speech_text"])
        self.assertEqual(
            [(0, 2, "主角"), (5, 6, "角")],
            [(item["start"], item["end"], item["original"]) for item in result["changes"]],
        )

    def test_personal_override_has_priority_over_confirmed_rule(self):
        from scripts.tts_pronunciation import analyze_text

        result = analyze_text(
            "主角登場。",
            self.load_rules(),
            overrides=[{"original": "主角", "spoken": "主腳色"}],
        )

        self.assertEqual("主腳色登場。", result["speech_text"])
        self.assertEqual("personal", result["changes"][0]["source"])
        self.assertFalse(result["changes"][0]["verified"])

    def test_rule_file_is_valid_json_and_contains_required_fields(self):
        path = ROOT / "data" / "tts-pronunciation" / "verified.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(138, len(data["rules"]))
        for rule in data["rules"]:
            self.assertTrue(rule["original"])
            self.assertTrue(rule["spoken"])
            self.assertTrue(rule["verified"])

        imported = [
            rule
            for rule in data["rules"]
            if rule.get("source") == "user-confirmed-csv"
        ]
        self.assertEqual(136, len(imported))
        self.assertTrue(
            all(rule["pronunciation"] and rule["note"] for rule in imported)
        )
        self.assertEqual(
            {"和（連詞）", "聘請", "舞蹈"},
            {
                rule["original"]
                for rule in imported
                if rule.get("auto_apply") is False
            },
        )
        imported_by_original = {rule["original"]: rule for rule in imported}
        self.assertEqual("勒色", imported_by_original["垃圾"]["spoken"])
        self.assertEqual("熟．悉", imported_by_original["熟悉"]["spoken"])
        self.assertEqual("簸放", imported_by_original["播放"]["spoken"])

    def test_rule_marked_not_for_auto_apply_is_not_replaced(self):
        from scripts.tts_pronunciation import analyze_text

        result = analyze_text(
            "這是一條危險規則。",
            [
                {
                    "original": "危險",
                    "spoken": "為險",
                    "verified": True,
                    "auto_apply": False,
                }
            ],
        )

        self.assertEqual("這是一條危險規則。", result["speech_text"])
        self.assertEqual([], result["changes"])

    def test_equation_is_expanded_to_teacher_friendly_speech(self):
        from scripts.tts_pronunciation import analyze_text

        result = analyze_text("x² + y² = z²", self.load_rules())

        self.assertEqual(
            "x 的平方，加上 y 的平方，等於 z 的平方",
            result["speech_text"],
        )
        self.assertEqual("formula", result["changes"][0]["type"])
        self.assertTrue(result["changes"][0]["verified"])

    def test_square_root_and_fraction_are_expanded(self):
        from scripts.tts_pronunciation import analyze_text

        result = analyze_text("√x = a/b", self.load_rules())

        self.assertEqual("根號 x，等於 b 分之 a", result["speech_text"])

    def test_srt_timestamp_is_preserved_while_equation_is_expanded(self):
        from scripts.tts_pronunciation import analyze_text

        source = "1\n00:00:01,000 --> 00:00:03,000\nx² + y² = z²\n"
        result = analyze_text(source, self.load_rules())

        self.assertIn("00:00:01,000 --> 00:00:03,000", result["speech_text"])
        self.assertIn("x 的平方，加上 y 的平方，等於 z 的平方", result["speech_text"])

    def test_formula_configuration_is_versioned_data(self):
        path = ROOT / "data" / "tts-pronunciation" / "formulas.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual("zh-TW", payload["locale"])
        self.assertEqual("加上", payload["operators"]["+"])

    def test_cli_exports_speech_and_change_files_without_touching_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "lesson.srt"
            source = "主角說：x² + y² = z²"
            input_path.write_text(source, encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "tts_pronunciation.py"),
                    "analyze",
                    str(input_path),
                    "--output-dir",
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(source, input_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "主腳說：x 的平方，加上 y 的平方，等於 z 的平方",
                (root / "lesson.tts.txt").read_text(encoding="utf-8"),
            )
            change_payload = json.loads(
                (root / "lesson.changes.json").read_text(encoding="utf-8")
            )
            self.assertEqual(2, len(change_payload["changes"]))

    def test_local_api_returns_analysis_json(self):
        from scripts.tts_pronunciation import create_server

        server = create_server(ROOT, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload = json.dumps({"text": "角色的 x²"}).encode("utf-8")
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/api/analyze",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))

            self.assertEqual("腳色的 x 的平方", result["speech_text"])
            self.assertEqual(["pronunciation", "formula"], [c["type"] for c in result["changes"]])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
