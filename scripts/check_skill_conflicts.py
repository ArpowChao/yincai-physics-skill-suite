from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NAME_RE = re.compile(r"^name:\s*[\"']?([^\"'\r\n]+)", re.MULTILINE)


def discover_skill_names(roots: list[Path]) -> dict[str, list[str]]:
    discovered: dict[str, list[str]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for skill_file in root.glob("*/SKILL.md"):
            try:
                text = skill_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            match = NAME_RE.search(text)
            if match:
                name = match.group(1).strip()
                discovered.setdefault(name, []).append(str(skill_file))
    return discovered


def default_skill_roots(repository: Path) -> list[Path]:
    user_home = Path.home()
    return [
        repository / ".agents" / "skills",
        user_home / ".gemini" / "config" / "skills",
        user_home / ".gemini" / "skills",
        user_home / ".agents" / "skills",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect installed Skills that conflict with this repository's task routing."
    )
    parser.add_argument(
        "--task",
        default="content-deck-review",
        help="Task key from data/skill-routing.json.",
    )
    parser.add_argument(
        "--skill-root",
        action="append",
        type=Path,
        help="Additional Skill root to scan; may be supplied more than once.",
    )
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    routing = json.loads(
        (repository / "data" / "skill-routing.json").read_text(encoding="utf-8")
    )
    route = routing["routes"].get(args.task)
    if route is None:
        print(f"Unknown task route: {args.task}")
        return 2

    roots = default_skill_roots(repository)
    roots.extend(path.expanduser().resolve() for path in args.skill_root or [])
    discovered = discover_skill_names(roots)
    preferred = route["preferred_skill"]
    incompatible = [
        name for name in route.get("incompatible_skills", []) if name in discovered
    ]

    print(f"Task: {args.task}")
    print(f"Required project Skill: {preferred}")
    if preferred not in discovered:
        print(f"ERROR: required Skill not found: {preferred}")
        return 1
    if incompatible:
        print("ERROR: incompatible Skill(s) found:")
        for name in incompatible:
            for path in discovered[name]:
                print(f"- {name}: {path}")
        print("Do not activate these Skills for this task; reload the Agent session.")
        return 1
    print("Skill routing check passed: no known content-review conflict found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
