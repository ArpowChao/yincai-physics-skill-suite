from __future__ import annotations

import argparse
import json
from pathlib import Path

from quality_records import read_records, summarize_records, validate_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize review-record JSON/JSONL.")
    parser.add_argument("input", nargs="+", help="Files, directories, or glob patterns")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = read_records(args.input)
    errors = []
    for index, record in enumerate(records, start=1):
        for error in validate_record(record):
            errors.append(f"record {index}: {error}")
    if errors:
        raise ValueError("\n".join(errors))
    payload = json.dumps(summarize_records(records), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
