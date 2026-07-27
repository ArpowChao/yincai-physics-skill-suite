from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRICULUM = REPO_ROOT / "data" / "curriculum" / "stage5-physics.json"
DEFAULT_PROJECT_NODES = (
    REPO_ROOT / "data" / "curriculum" / "project-node-catalog.json"
)
CODE_PATTERN = re.compile(r"^(P[A-Za-z]{2})-(?:V|Ⅴ)([acAC])((?:-\d+)+)$")
TECHNICAL_NODE_PATTERN = re.compile(
    r"^(P[A-Za-z]{2})-(?:V|Ⅴ)\.(\d+(?:-\d+)+)$"
)
EXTENDED_OFFICIAL_NODE_PATTERN = re.compile(
    r"^(P[A-Za-z]{2})-(?:V|Ⅴ)([acAC])-(\d+)((?:[.-]\d+)*)$"
)


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


def load_project_nodes(path: Path | str = DEFAULT_PROJECT_NODES) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("Project node catalog must contain an entries object")
    return data


def normalize_project_node_code(code: str) -> str:
    raw = (
        code.strip()
        .replace("Ⅴ", "V")
        .replace("－", "-")
        .replace("–", "-")
        .rstrip("。．.")
    )
    technical = TECHNICAL_NODE_PATTERN.match(raw)
    if technical:
        family, suffix = technical.groups()
        family = family[0].upper() + family[1].upper() + family[2].lower()
        return f"{family}-V.{suffix}"
    extended = EXTENDED_OFFICIAL_NODE_PATTERN.match(raw)
    if extended:
        family, track, number, suffix = extended.groups()
        family = family[0].upper() + family[1].upper() + family[2].lower()
        return f"{family}-V{track.lower()}-{number}{suffix}"
    return raw


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


def resolve_curriculum_scope(
    project_code: str,
    catalog: dict[str, Any] | None = None,
    project_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    curriculum = catalog or load_curriculum()
    nodes = project_catalog or load_project_nodes()
    normalized = normalize_project_node_code(project_code)
    node_lookup = {key.lower(): value for key, value in nodes["entries"].items()}
    node = node_lookup.get(normalized.lower())
    if node:
        official_parent = node.get("official_parent")
        official_entry = None
        if official_parent:
            official_entry = curriculum["entries"].get(official_parent)
        source = node.get("official_source")
        if not source and node.get("sources"):
            first = node["sources"][0]
            source = {
                "document": first.get("workbook"),
                "sheet": first.get("sheet"),
                "row": first.get("row"),
            }
        course = node.get("course", "")
        if official_entry:
            track = official_entry["track"]
        elif course == "技高物理A":
            track = "technical-physics-a"
        elif course == "技高物理B":
            track = "technical-physics-b"
        else:
            track = "project-node"
        return {
            "code": official_parent or node["code"],
            "project_code": node["code"],
            "project_title": node.get("title"),
            "track": track,
            "statement": (
                official_entry.get("statement")
                if official_entry
                else node.get("official_statement")
                or node.get("learning_content")
                or node.get("node_scope")
            ),
            "teaching_note": (
                official_entry.get("teaching_note")
                if official_entry
                else node.get("learning_content_explanation")
                or node.get("node_scope")
            ),
            "source": official_entry.get("source") if official_entry else source,
            "scope_constraints": node.get("scope_constraints", []),
            "mapping_status": node.get("mapping_status", "mapped"),
            "evidence_level": node.get("evidence_level", "B"),
            "conflicts": node.get("conflicts", []),
            "project_node": node,
        }
    try:
        return resolve_official_code(project_code, curriculum)
    except UnknownCurriculumCode as exc:
        raise UnknownCurriculumCode(
            f"No official or project-approved Stage 5 physics scope for: "
            f"{project_code}"
        ) from exc


def relative_to_repo(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)
