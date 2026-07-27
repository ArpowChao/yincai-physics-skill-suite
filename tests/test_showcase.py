import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_showcase.py"


class ShowcaseTests(unittest.TestCase):
    def test_showcase_outputs_match_all_assertions(self):
        spec = importlib.util.spec_from_file_location("validate_showcase", VALIDATOR)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        self.assertEqual([], module.validate())


if __name__ == "__main__":
    unittest.main()
