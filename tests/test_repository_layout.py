import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_repository.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_repository_test", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RepositoryLayoutTests(unittest.TestCase):
    def make_tree(self, root: Path, module):
        for directory in module.REQUIRED_SHAREABLE_DIRS:
            (root / directory).mkdir(parents=True, exist_ok=True)
        for name in module.ALLOWED_ROOT_FILES:
            (root / name).write_text("", encoding="utf-8")

    def test_clean_shareable_tree_passes(self):
        module = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root, module)
            errors = module.audit_tree(root, tracked=["README.md"])
            self.assertEqual([], errors)

    def test_flags_loose_root_file_and_tracked_binary(self):
        module = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root, module)
            (root / "teacher-list.md").write_text("name", encoding="utf-8")
            (root / "lesson.pptx").write_bytes(b"fixture")
            errors = module.audit_tree(
                root,
                tracked=["README.md", "lesson.pptx"],
            )
            self.assertTrue(any("Unexpected root file" in error for error in errors))
            self.assertTrue(any("binary is tracked" in error for error in errors))

    def test_flags_broken_skill_reference(self):
        module = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root, module)
            skill = root / ".agents" / "skills" / "demo" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                "- `../../../references/missing.md`\n",
                encoding="utf-8",
            )
            errors = module.audit_tree(root, tracked=["README.md"])
            self.assertTrue(any("Broken Skill reference" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
