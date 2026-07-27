from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from common import load_curriculum, resolve_official_code
from quality_records import validate_record


def build_record(
    project_code: str,
    skill: str,
    artifact_refs: list[str],
    skill_version: str = "1.0.0",
) -> dict:
    official = resolve_official_code(project_code, load_curriculum())
    timestamp = datetime.now(ZoneInfo("Asia/Taipei"))
    slug = project_code.lower().replace("-", "_")
    return {
        "record_version": "1.0",
        "record_id": f"{timestamp:%Y%m%d-%H%M%S}-{slug}",
        "created_at": timestamp.isoformat(timespec="seconds"),
        "skill": skill,
        "skill_version": skill_version,
        "project_code": project_code.replace("Ⅴ", "V"),
        "official_code": official["code"],
        "artifact_refs": artifact_refs,
        "evidence": [{"level": "A", "ref": f"curriculum:{official['code']}"}],
        "decision": "HOLD",
        "strengths": [],
        "findings": [],
        "human_decision": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a review-record JSON template.")
    parser.add_argument("project_code")
    parser.add_argument("skill")
    parser.add_argument("--artifact-ref", action="append", default=[])
    parser.add_argument("--skill-version", default="1.0.0")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    record = build_record(
        args.project_code,
        args.skill,
        args.artifact_ref,
        args.skill_version,
    )
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    payload = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
