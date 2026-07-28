from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ALLOWED_ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "GEMINI.md",
    "LICENSES.md",
    "README.md",
    "REVIEWER_START_HERE.md",
    "VERSION",
}
REQUIRED_SHAREABLE_DIRS = {
    ".agents",
    ".github",
    "config",
    "data",
    "docs",
    "quality",
    "references",
    "scripts",
    "showcase",
    "tests",
}
FORBIDDEN_TRACKED_SUFFIXES = {
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".pdf",
    ".xlsx",
    ".xlsm",
    ".7z",
    ".zip",
    ".omv",
}
LOCAL_TRACKED_ALLOWLIST = {
    "archive/README.md",
    "local-data/README.md",
}
PRIVATE_TRACKED_PREFIXES = (
    "archive/",
    "local-data/",
    "outputs/",
    "quality/records/",
)
NONPORTABLE_RE = re.compile(r"file:///|[A-Za-z]:[\\/]Program[\\/]", re.IGNORECASE)
REPO_LINK_RE = re.compile(r"`((?:\.\./){2,}[^`\n]+\.md)`")
NONPORTABLE_SCAN_EXEMPT = {
    "docs/plans/2026-07-27-adaptive-physics-skill-suite.md",
    "quality/baseline-2026-07-27.md",
    "scripts/audit_repository.py",
    "scripts/validate_suite.py",
    "tests/test_repository_layout.py",
    "tests/test_skill_suite.py",
}


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8").replace("\\", "/")
        for item in result.stdout.split(b"\0")
        if item
    ]


def audit_tree(root: Path, tracked: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    for item in root.iterdir():
        if item.is_file() and item.name not in ALLOWED_ROOT_FILES:
            errors.append(f"Unexpected root file: {item.name}")
    for directory in sorted(REQUIRED_SHAREABLE_DIRS):
        if not (root / directory).is_dir():
            errors.append(f"Missing required directory: {directory}")

    tracked = tracked if tracked is not None else tracked_files(root)
    for relative in tracked:
        normalized = relative.replace("\\", "/")
        suffix = Path(normalized).suffix.lower()
        if suffix in FORBIDDEN_TRACKED_SUFFIXES:
            errors.append(f"Large/source binary is tracked: {normalized}")
        if normalized in LOCAL_TRACKED_ALLOWLIST:
            continue
        if normalized.startswith(PRIVATE_TRACKED_PREFIXES):
            errors.append(f"Local/private path is tracked: {normalized}")
        path = root / normalized
        if path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".toml", ".py"}:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if (
                normalized not in NONPORTABLE_SCAN_EXEMPT
                and NONPORTABLE_RE.search(text)
            ):
                errors.append(f"Non-portable local path in tracked file: {normalized}")

    for skill_file in (root / ".agents" / "skills").glob("*/SKILL.md"):
        text = skill_file.read_text(encoding="utf-8")
        for match in REPO_LINK_RE.finditer(text):
            target = (skill_file.parent / match.group(1)).resolve()
            if not target.is_file():
                errors.append(
                    f"Broken Skill reference: {skill_file.relative_to(root)} -> "
                    f"{match.group(1)}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that the repository stays shareable and maintainable."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = audit_tree(root)
    if errors:
        print("Repository audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository audit passed: root, tracked files, privacy boundaries, and Skill links are clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
