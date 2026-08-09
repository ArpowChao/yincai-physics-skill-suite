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

    def test_git_worktree_metadata_file_is_allowed(self):
        module = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root, module)
            (root / ".git").write_text("gitdir: ../repo/.git/worktrees/demo", encoding="utf-8")
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

    def test_collaboration_entrypoints_and_ci_are_present(self):
        required = [
            ROOT / "AGENTS.md",
            ROOT / "GEMINI.md",
            ROOT / "docs" / "getting-started.md",
            ROOT / "docs" / "collaboration-workflow.md",
            ROOT / "docs" / "macos-guide.md",
            ROOT / "docs" / "maintenance.md",
            ROOT / ".github" / "workflows" / "ci.yml",
        ]
        for path in required:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/getting-started.md", readme)
        self.assertIn("docs/collaboration-workflow.md", readme)
        self.assertIn("docs/macos-guide.md", readme)

        gemini = (ROOT / "GEMINI.md").read_text(encoding="utf-8")
        runtime = (
            ROOT / "references" / "cross-agent-runtime.md"
        ).read_text(encoding="utf-8")
        self.assertIn("physics-framework-checker", gemini)
        self.assertIn("/skills list", runtime)
        self.assertIn("不得因此扣分", runtime)

        workflow = (
            ROOT / ".github" / "workflows" / "ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python scripts/audit_repository.py", workflow)
        self.assertIn("python scripts/validate_suite.py", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)

        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/outputs/", gitignore)


if __name__ == "__main__":
    unittest.main()
