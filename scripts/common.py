from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRICULUM = REPO_ROOT / "data" / "curriculum" / "stage5-physics.json"
CODE_PATTERN = re.compile(r"^(P[A-Za-z]{2})-(?:V|Ⅴ)([acAC])((?:-\d+)+)$")


class UnknownCurriculumCode(ValueError):
    """Raised when a project code has no official Stage 5 parent."""


def normalize_content_code(code: str) -> str:
    raw = code.strip().replace("Ⅴ", "V").replace("－", "-")
    match = CODE_PATTERN.match(raw)
    if not match:
        raise UnknownCurriculumCode(f"Invalid Stage 5 physics code: {code}")
    family, track, suffix = match.groups()
    family = family[0].upper() + family[1].upper() + family[2].lower()
    return f"{family}-V{track.lower()}{suffix}"


def load_curriculum(path: Path | str = DEFAULT_CURRICULUM) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("Curriculum catalog must contain an entries object")
    return data


def resolve_official_code(
    project_code: str, catalog: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = catalog or load_curriculum()
    normalized = normalize_content_code(project_code)
    lookup = {key.lower(): value for key, value in data["entries"].items()}
    segments = normalized.split("-")
    for end in range(len(segments), 2, -1):
        candidate = "-".join(segments[:end])
        entry = lookup.get(candidate.lower())
        if entry:
            return entry
    raise UnknownCurriculumCode(
        f"No official Stage 5 physics parent for project code: {project_code}"
    )


def relative_to_repo(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)
