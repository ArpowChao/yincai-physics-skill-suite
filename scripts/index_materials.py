from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EXTENSIONS = {".pptx", ".docx", ".pdf", ".md"}
CODE_RE = re.compile(r"^(P[A-Za-z]{2}-(?:V|Ⅴ)[acAC](?:-\d+)+)")
STATUS_RE = re.compile(r"\((已|不)\)")
ARTIFACT_DIRECTORIES = {
    "投影片": "slides",
    "學習單": "worksheet",
    "診斷題": "diagnostic-question",
    "練習題": "practice-question",
}


def parse_material_filename(filename: str) -> dict[str, Any]:
    path = Path(filename)
    stem = path.stem
    parts = stem.split("_")
    code_match = CODE_RE.match(stem)
    status_match = STATUS_RE.search(stem)
    return {
        "project_code": (
            code_match.group(1).replace("Ⅴ", "V") if code_match else None
        ),
        "topic": parts[1].strip() if len(parts) > 1 else None,
        "author_hint": parts[2].strip() if len(parts) > 2 else None,
        "status_hint": status_match.group(1) if status_match else None,
        "extension": path.suffix.lower().lstrip("."),
    }


def classify_artifact(path: Path) -> str:
    for part in path.parts:
        if part in ARTIFACT_DIRECTORIES:
            return ARTIFACT_DIRECTORIES[part]
    if path.suffix.lower() == ".pptx":
        return "slides"
    return "unclassified"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def build_index(root: Path | str, include_hash: bool = False) -> list[dict[str, Any]]:
    base = Path(root).resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        parsed = parse_material_filename(path.name)
        stat = path.stat()
        record = {
            "relative_path": path.relative_to(base).as_posix(),
            "filename": path.name,
            "artifact_type": classify_artifact(path.relative_to(base)),
            "size_bytes": stat.st_size,
            "modified_ns": stat.st_mtime_ns,
            **parsed,
        }
        if include_hash:
            record["sha256"] = sha256_file(path)
        records.append(record)
    return records


def write_jsonl(records: Iterable[dict[str, Any]], output: Path | str) -> None:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Index local physics teaching assets.")
    parser.add_argument("root", type=Path, help="Material library root")
    parser.add_argument("--output", type=Path, help="Optional JSONL output")
    parser.add_argument("--hash", action="store_true", help="Calculate SHA-256")
    args = parser.parse_args()
    records = build_index(args.root, include_hash=args.hash)
    if args.output:
        write_jsonl(records, args.output)
    print(
        json.dumps(
            {
                "root": str(args.root.resolve()),
                "records": len(records),
                "output": str(args.output.resolve()) if args.output else None,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
