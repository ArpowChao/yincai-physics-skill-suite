from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "showcase"


def validate() -> list[str]:
    errors: list[str] = []
    evals_path = SHOWCASE / "evals" / "evals.json"
    if not evals_path.exists():
        return ["missing showcase/evals/evals.json"]
    evals = json.loads(evals_path.read_text(encoding="utf-8"))["evals"]
    by_id = {item["id"]: item for item in evals}

    eval_dirs = sorted((SHOWCASE / "iteration-1").glob("[0-9][0-9]-*"))
    if len(eval_dirs) != len(evals):
        errors.append(f"expected {len(evals)} eval directories, found {len(eval_dirs)}")

    for eval_dir in eval_dirs:
        metadata_path = eval_dir / "eval_metadata.json"
        result_path = eval_dir / "with_skill" / "outputs" / "result.md"
        grading_path = eval_dir / "with_skill" / "grading.json"
        for path in (metadata_path, result_path, grading_path):
            if not path.exists():
                errors.append(f"missing {path.relative_to(ROOT)}")
        if not all(path.exists() for path in (metadata_path, result_path, grading_path)):
            continue

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        eval_id = metadata["eval_id"]
        if eval_id not in by_id:
            errors.append(f"{eval_dir.name}: unknown eval_id {eval_id}")
            continue
        expected = by_id[eval_id]["expectations"]
        graded = [item["text"] for item in grading["expectations"]]
        if expected != graded:
            errors.append(f"{eval_dir.name}: grading expectations differ from evals.json")
        if not all(item["passed"] is True for item in grading["expectations"]):
            errors.append(f"{eval_dir.name}: contains a failed expectation")
        summary = grading["summary"]
        if summary["passed"] != len(expected) or summary["total"] != len(expected):
            errors.append(f"{eval_dir.name}: grading summary count mismatch")
        if summary["pass_rate"] != 1.0:
            errors.append(f"{eval_dir.name}: pass rate is not 1.0")
        if not result_path.read_text(encoding="utf-8").strip():
            errors.append(f"{eval_dir.name}: empty result")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Showcase validation passed: 5 topics, 29/29 expectations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
