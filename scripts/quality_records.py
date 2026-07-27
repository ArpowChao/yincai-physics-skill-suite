from __future__ import annotations

import json
import glob
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REQUIRED_FIELDS = {
    "record_version",
    "record_id",
    "created_at",
    "skill",
    "skill_version",
    "project_code",
    "official_code",
    "artifact_refs",
    "evidence",
    "decision",
    "strengths",
    "findings",
    "human_decision",
}
DECISIONS = {"PASS", "REVISE", "HOLD"}
SEVERITIES = {"blocker", "major", "minor", "suggestion"}
EVIDENCE_LEVELS = {"A", "B", "C", "D"}


def validate_record(record: dict[str, Any]) -> list[str]:
    errors = []
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if record.get("decision") not in DECISIONS:
        errors.append(f"decision must be one of {sorted(DECISIONS)}")
    for index, evidence in enumerate(record.get("evidence", [])):
        if evidence.get("level") not in EVIDENCE_LEVELS:
            errors.append(f"evidence[{index}].level is invalid")
        if not evidence.get("ref"):
            errors.append(f"evidence[{index}].ref is required")
    for index, finding in enumerate(record.get("findings", [])):
        if finding.get("severity") not in SEVERITIES:
            errors.append(f"findings[{index}].severity is invalid")
        for field in ("criterion", "note", "action"):
            if not finding.get(field):
                errors.append(f"findings[{index}].{field} is required")
    for index, strength in enumerate(record.get("strengths", [])):
        for field in ("criterion", "note"):
            if not strength.get(field):
                errors.append(f"strengths[{index}].{field} is required")
    return errors


def summarize_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    decision_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    strength_counts: Counter[str] = Counter()
    criterion_counts: Counter[str] = Counter()
    total = 0
    for record in records:
        total += 1
        decision_counts[record.get("decision", "UNKNOWN")] += 1
        for strength in record.get("strengths", []):
            strength_counts[strength.get("criterion", "unknown")] += 1
        for finding in record.get("findings", []):
            severity_counts[finding.get("severity", "unknown")] += 1
            criterion_counts[finding.get("criterion", "unknown")] += 1
    return {
        "records": total,
        "decisions": dict(sorted(decision_counts.items())),
        "findings_by_severity": dict(sorted(severity_counts.items())),
        "findings_by_criterion": dict(sorted(criterion_counts.items())),
        "strengths_by_criterion": dict(sorted(strength_counts.items())),
    }


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
    return records


def read_records(inputs: Iterable[Path | str]) -> list[dict[str, Any]]:
    paths: list[Path] = []
    for raw in inputs:
        candidate = Path(raw)
        if candidate.is_dir():
            paths.extend(sorted(candidate.glob("*.json")))
            paths.extend(sorted(candidate.glob("*.jsonl")))
            continue
        matches = [Path(match) for match in glob.glob(str(raw))]
        paths.extend(matches or [candidate])

    records: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix.lower() == ".jsonl":
            records.extend(read_jsonl(path))
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            records.extend(payload)
        elif isinstance(payload, dict):
            records.append(payload)
        else:
            raise ValueError(f"Expected object or array in {path}")
    return records
