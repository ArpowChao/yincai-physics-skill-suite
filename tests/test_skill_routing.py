import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_skill_conflicts.py"


def load_module():
    spec = importlib.util.spec_from_file_location("skill_routing_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class SkillRoutingTests(unittest.TestCase):
    def test_discovers_named_skills(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "physics-framework-9step" / "SKILL.md"
            skill.parent.mkdir()
            skill.write_text(
                "---\nname: physics-framework-9step\ndescription: legacy\n---\n",
                encoding="utf-8",
            )
            discovered = module.discover_skill_names([root])
            self.assertIn("physics-framework-9step", discovered)

    def test_routing_declares_legacy_content_review_conflict(self):
        routing = json.loads(
            (ROOT / "data" / "skill-routing.json").read_text(encoding="utf-8")
        )
        content_route = routing["routes"]["content-deck-review"]
        self.assertEqual(
            "physics-framework-checker", content_route["preferred_skill"]
        )
        self.assertIn(
            "physics-framework-9step", content_route["incompatible_skills"]
        )


if __name__ == "__main__":
    unittest.main()
