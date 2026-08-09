import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TtsStaticSiteTests(unittest.TestCase):
    def test_browser_analyzes_locally_with_relative_assets(self):
        site = ROOT / "showcase" / "tts-pronunciation"
        html = (site / "index.html").read_text(encoding="utf-8")
        app = (site / "app.js").read_text(encoding="utf-8")

        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js"', html)
        self.assertIn('src="cross-strait-candidates.js"', html)
        self.assertIn("analyzeLocally", app)
        self.assertIn("FALLBACK_CONFIRMED_RULES", app)
        self.assertIn('original: "主角"', app)
        self.assertIn('spoken: "主腳"', app)
        self.assertIn('fetch("data/verified.json")', app)
        self.assertIn("CROSS_STRAIT_PRONUNCIATION_CANDIDATES", app)
        self.assertNotIn("/api/analyze", app)

    def test_static_site_builder_copies_only_required_public_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "site"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_tts_pronunciation_site.py"),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "app.js").is_file())
            self.assertTrue((output / "moe-heteronyms.js").is_file())
            self.assertTrue((output / "cross-strait-candidates.js").is_file())
            self.assertTrue((output / "styles.css").is_file())
            self.assertTrue((output / "data" / "verified.json").is_file())
            self.assertTrue((output / "data" / "formulas.json").is_file())
            self.assertTrue((output / "data" / "submission.json").is_file())
            self.assertTrue((output / ".nojekyll").is_file())
            self.assertFalse((output / "scripts").exists())

    def test_pages_workflow_builds_and_deploys_static_artifact(self):
        workflow = (ROOT / ".github" / "workflows" / "tts-pages.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("build_tts_pronunciation_site.py", workflow)
        self.assertIn("actions/configure-pages@", workflow)
        self.assertIn("actions/upload-pages-artifact@", workflow)
        self.assertIn("actions/deploy-pages@", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)

    def test_shared_rule_submission_uses_a_structured_github_issue(self):
        app = (ROOT / "showcase" / "tts-pronunciation" / "app.js").read_text(
            encoding="utf-8"
        )
        template = ROOT / ".github" / "ISSUE_TEMPLATE" / "tts-pronunciation.yml"

        self.assertIn("/issues/new", app)
        self.assertIn("tts-pronunciation.yml", app)
        self.assertTrue(template.is_file())
        template_text = template.read_text(encoding="utf-8")
        self.assertIn("id: original", template_text)
        self.assertIn("id: spoken", template_text)
        self.assertIn("人工確認", template_text)

    def test_google_apps_script_candidate_inbox_is_ready_for_sheet_deployment(self):
        integration = ROOT / "integrations" / "google-apps-script" / "tts-pronunciation"
        code = (integration / "Code.gs").read_text(encoding="utf-8")
        app = (ROOT / "showcase" / "tts-pronunciation" / "app.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function doPost", code)
        self.assertIn("appendRow", code)
        self.assertIn("LockService.getScriptLock", code)
        self.assertIn("safeCell_", code)
        self.assertIn('fetch("data/submission.json")', app)
        self.assertIn("submitToAppsScript", app)
        self.assertTrue((integration / "appsscript.json").is_file())

    def test_moe_reference_lexicon_is_large_and_attributed(self):
        path = ROOT / "data" / "tts-pronunciation" / "moe-heteronyms.json"
        payload = __import__("json").loads(path.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(payload["rules"]), 15000)
        self.assertEqual("zh-TW", payload["locale"])
        self.assertIn("教育部", payload["source"]["name"])
        self.assertIn("CC BY-ND", payload["source"]["license"])

    def test_cross_strait_candidates_are_large_attributed_and_actionable(self):
        path = ROOT / "data" / "tts-pronunciation" / "cross-strait-candidates.json"
        payload = __import__("json").loads(path.read_text(encoding="utf-8"))
        rules = {rule["original"]: rule for rule in payload["rules"]}

        self.assertGreaterEqual(len(rules), 5000)
        self.assertGreaterEqual(
            payload["generation"]["full_homophone_suggestions"], 4800
        )
        self.assertEqual(
            "a1e91196f84cd2f3456570906191615f477278c8",
            payload["source"]["commit"],
        )
        self.assertEqual("維小", rules["微小"]["spoken"])
        self.assertEqual("除存", rules["儲存"]["spoken"])
        self.assertEqual("頭法", rules["頭髮"]["spoken"])
        self.assertFalse(rules["微小"]["verified"])


if __name__ == "__main__":
    unittest.main()
