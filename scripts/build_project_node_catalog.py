from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "local-data" / "sources" / "node-maps"
DEFAULT_OUTPUT = ROOT / "data" / "curriculum" / "project-node-catalog.json"
OFFICIAL_CATALOG = ROOT / "data" / "curriculum" / "stage5-physics.json"

WORKBOOKS = [
    ("物A-B知識節點 07.18.xlsx", "technical", ["物理A", "物理B"]),
    (
        "選修物理123_知識節點V7.xlsx",
        "elective",
        ["選物1", "選物2", "選物3", "補選物1", "補選物2"],
    ),
    (
        "選修物理4_知識節點V3.xlsx",
        "elective",
        [
            "選物1(11年級)",
            "選物2(11年級)",
            "選物3(12年級)",
            "選物4(12年級)",
            "選物5(12年級)",
            "補選物1",
            "補選物2",
        ],
    ),
    (
        "SDGS教材.xlsx",
        "sdgs",
        ["113年度節點", "114年度節點", "SDGs編碼", "工作表17", "工作表9", "工作表10"],
    ),
]

TECHNICAL_OFFICIAL_PARENTS = {
    "PBa-V.1-2": {
        "statement": "能與力的關係。",
        "teaching_note": (
            "說明對物體施力，使物體沿施力的方向產生位移，"
            "物體會因此產生能量的變化。"
        ),
        "course_constraints": [
            "物理A規劃1學分及2學分版本。",
            "標有*的學習內容可由教師依學生學習狀況彈性刪減。",
            "本條官方說明支持力、位移與能量變化的關係；"
            "未直接指定動能公式計算或功能定理推導深度。",
        ],
        "source": {
            "document": "十二年國民基本教育課程綱要技術型高級中等學校─自然科學領域",
            "publisher": "教育部／國家教育研究院",
            "url": (
                "https://stv.naer.edu.tw/data/course_outline/"
                "pta_18539_2327449_60503.pdf"
            ),
            "pdf_page": 108,
        },
    }
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def normalized(value: Any) -> str:
    return (
        clean(value)
        .replace("Ⅴ", "V")
        .replace("－", "-")
        .replace("–", "-")
    )


def official_code(value: Any) -> str | None:
    match = re.search(
        r"P([A-Za-z])([A-Za-z])-V([aAcC])-(\d+)",
        normalized(value).replace(" ", ""),
    )
    if not match:
        return None
    first, second, track, number = match.groups()
    return f"P{first.upper()}{second.lower()}-V{track.lower()}-{number}"


def extended_code(value: Any) -> str | None:
    match = re.search(
        r"P([A-Za-z])([A-Za-z])-V([aAcC])-(\d+)((?:[.-]\d+)*)",
        normalized(value).replace(" ", "").rstrip("。．."),
    )
    if not match:
        return None
    first, second, track, number, suffix = match.groups()
    return f"P{first.upper()}{second.lower()}-V{track.lower()}-{number}{suffix}"


def technical_code(value: Any) -> str | None:
    match = re.search(
        r"P([A-Za-z])([A-Za-z])-V\.(\d+(?:-\d+)+)", normalized(value)
    )
    if not match:
        return None
    first, second, suffix = match.groups()
    return f"P{first.upper()}{second.lower()}-V.{suffix}"


def technical_parent(value: Any) -> str | None:
    match = re.search(
        r"P([A-Za-z])([A-Za-z])-V\.(\d+-\d+)", normalized(value)
    )
    if not match:
        return None
    first, second, suffix = match.groups()
    return f"P{first.upper()}{second.lower()}-V.{suffix}"


def sdgs_code(value: Any) -> str | None:
    match = re.search(r"PNa-SDG\.1-[A-Za-z0-9-]+", clean(value), re.I)
    return re.sub(r"^pna", "PNa", match.group(0), flags=re.I) if match else None


def title_after_code(value: Any, code: str) -> str:
    raw = clean(value)
    index = raw.lower().find(code.lower())
    if index < 0:
        return ""
    return re.sub(r"^[_\s.。．-]+", "", raw[index + len(code) :]).split("\n")[0].strip()


def add(entries: dict[str, dict[str, Any]], entry: dict[str, Any]) -> None:
    existing = entries.get(entry["code"])
    if not existing:
        entries[entry["code"]] = entry
        return
    for source in entry["sources"]:
        if source not in existing["sources"]:
            existing["sources"].append(source)
    for field in [
        "title",
        "course",
        "learning_content",
        "learning_content_explanation",
        "official_parent",
        "official_statement",
        "node_scope",
    ]:
        if not existing.get(field) and entry.get(field):
            existing[field] = entry[field]
    if entry.get("related_physics_nodes"):
        existing["related_physics_nodes"] = sorted(
            set(existing.get("related_physics_nodes", []))
            | set(entry["related_physics_nodes"])
        )
    conflicts = set(existing.get("conflicts", []))
    if existing.get("title") and entry.get("title") and existing["title"] != entry["title"]:
        conflicts.add(f"title mismatch: {existing['title']} <> {entry['title']}")
    if (
        existing.get("official_parent")
        and entry.get("official_parent")
        and existing["official_parent"] != entry["official_parent"]
    ):
        conflicts.add(
            "official parent mismatch: "
            f"{existing['official_parent']} <> {entry['official_parent']}"
        )
    existing["conflicts"] = sorted(conflicts)


def technical_rows(
    entries: dict[str, dict[str, Any]],
    filename: str,
    sheet: str,
    rows: list[tuple[Any, ...]],
) -> None:
    is_a = sheet == "物理A"
    explanation = subtheme = learning_content = ""
    for row_number, row in enumerate(rows[1:], start=2):
        explanation = clean(row[0]) or explanation
        subtheme = clean(row[2 if is_a else 1]) or subtheme
        learning_content = clean(row[3 if is_a else 2]) or learning_content
        code = technical_code(row[4])
        if not code:
            continue
        title = clean(row[5]) or title_after_code(row[4], code)
        parent = technical_parent(learning_content)
        official = TECHNICAL_OFFICIAL_PARENTS.get(parent or "")
        legacy = extended_code(row[10]) if is_a and len(row) > 10 else None
        legacy_title = clean(row[11]) if is_a and len(row) > 11 else ""
        conflicts = []
        if legacy and (
            ("動能" in title and "位能" in legacy_title)
            or ("位能" in title and "動能" in legacy_title)
        ):
            conflicts.append(
                f"legacy reference label does not match node title: {legacy} {legacy_title}"
            )
        add(
            entries,
            {
                "code": code,
                "node_type": "technical-learning-node",
                "course": "技高物理A" if is_a else "技高物理B",
                "title": title,
                "subtheme": subtheme or None,
                "learning_content": parent or learning_content or None,
                "learning_content_explanation": (
                    official["teaching_note"] if official else explanation or None
                ),
                "official_parent": parent,
                "official_statement": (
                    official["statement"] if official else learning_content or None
                ),
                "official_source": official["source"] if official else None,
                "scope_constraints": (
                    official["course_constraints"] if official else []
                ),
                "node_scope": title or None,
                "evidence_level": "A+B" if official else "B",
                "mapping_status": (
                    "mapped-with-source-conflict"
                    if conflicts
                    else "mapped-a+b"
                    if official
                    else "mapped"
                ),
                "legacy_reference": (
                    {
                        "code": legacy,
                        "official_parent": official_code(legacy),
                        "title": legacy_title or None,
                    }
                    if legacy
                    else None
                ),
                "conflicts": conflicts,
                "sources": [{"workbook": filename, "sheet": sheet, "row": row_number}],
            },
        )


def elective_rows(
    entries: dict[str, dict[str, Any]],
    official: dict[str, Any],
    filename: str,
    sheet: str,
    rows: list[tuple[Any, ...]],
) -> None:
    for row_number, row in enumerate(rows, start=1):
        found = [(index, extended_code(value)) for index, value in enumerate(row)]
        found = [(index, code) for index, code in found if code]
        if not found:
            continue
        index, code = found[0]
        parent = official_code(code)
        parent_entry = official["entries"].get(parent or "")
        before = clean(row[index - 1]) if index > 0 else ""
        after = clean(row[index + 1]) if index + 1 < len(row) else ""
        title = before or after or title_after_code(row[index], code)
        add(
            entries,
            {
                "code": code,
                "node_type": "elective-learning-node",
                "course": sheet,
                "title": title or after or None,
                "subtheme": None,
                "learning_content": parent,
                "learning_content_explanation": (
                    parent_entry.get("teaching_note") if parent_entry else None
                ),
                "official_parent": parent,
                "official_statement": (
                    parent_entry.get("statement") if parent_entry else None
                ),
                "official_source": parent_entry.get("source") if parent_entry else None,
                "node_scope": after or title or None,
                "evidence_level": "A" if parent_entry else "B",
                "mapping_status": "mapped" if parent_entry else "mapped-parent-missing",
                "legacy_reference": None,
                "conflicts": [],
                "sources": [{"workbook": filename, "sheet": sheet, "row": row_number}],
            },
        )


def sdgs_rows(
    entries: dict[str, dict[str, Any]],
    filename: str,
    sheet: str,
    rows: list[tuple[Any, ...]],
) -> None:
    for row_number, row in enumerate(rows, start=1):
        values = [clean(value) for value in row]
        matched = [(value, sdgs_code(value)) for value in values]
        matched = [(value, code) for value, code in matched if code]
        if not matched:
            continue
        code_cell, code = matched[0]
        related: set[str] = set()
        for value in values:
            for raw in re.findall(
                r"(?:\d+-)?P[A-Za-z]{2}-V[acAC](?:-\d+)+(?:[.-]\d+)*",
                normalized(value),
            ):
                candidate = extended_code(re.sub(r"^\d+-", "", raw))
                if candidate:
                    related.add(candidate)
        title = title_after_code(code_cell, code)
        add(
            entries,
            {
                "code": code,
                "node_type": "sdgs-learning-node",
                "course": "SDGs教材",
                "title": title or None,
                "subtheme": None,
                "learning_content": None,
                "learning_content_explanation": None,
                "official_parent": None,
                "official_statement": None,
                "node_scope": title or None,
                "related_physics_nodes": sorted(related),
                "evidence_level": "B",
                "mapping_status": (
                    "mapped" if related else "mapped-without-physics-link"
                ),
                "legacy_reference": None,
                "conflicts": [],
                "sources": [{"workbook": filename, "sheet": sheet, "row": row_number}],
            },
        )


def build(source_dir: Path) -> dict[str, Any]:
    try:
        import openpyxl
    except ImportError as exc:
        raise SystemExit(
            "Rebuilding the project node catalog requires openpyxl: "
            "python -m pip install openpyxl"
        ) from exc
    official = json.loads(OFFICIAL_CATALOG.read_text(encoding="utf-8"))
    entries: dict[str, dict[str, Any]] = {}
    sources = []
    for filename, kind, sheets in WORKBOOKS:
        path = source_dir / filename
        payload = path.read_bytes()
        sources.append(
            {
                "filename": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
        )
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for sheet in sheets:
            rows = list(workbook[sheet].iter_rows(values_only=True))
            if kind == "technical":
                technical_rows(entries, filename, sheet, rows)
            elif kind == "elective":
                elective_rows(entries, official, filename, sheet, rows)
            else:
                sdgs_rows(entries, filename, sheet, rows)
        workbook.close()
    sorted_entries = dict(sorted(entries.items()))
    return {
        "catalog_version": "1.0.0",
        "title": "因材網高中物理專案知識節點對照",
        "generated_from": sources,
        "privacy_note": (
            "Only curriculum/node fields and workbook cell provenance are retained. "
            "Teacher names, groups, progress, and raw workbooks are excluded."
        ),
        "authority_note": (
            "Official Va/Vc parents use A-level curriculum data. Technical Physics "
            "A/B and SDGs node maps are B-level project-approved mappings until an "
            "official technical curriculum source is attached."
        ),
        "entry_count": len(sorted_entries),
        "conflict_count": sum(
            bool(entry.get("conflicts")) for entry in sorted_entries.values()
        ),
        "entries": sorted_entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the sanitized project node catalog from four local XLSX files."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    catalog = build(args.source_dir.resolve())
    args.output.resolve().write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "entry_count": catalog["entry_count"],
                "conflict_count": catalog["conflict_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
