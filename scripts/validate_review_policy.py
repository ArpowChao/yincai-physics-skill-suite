from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.review_policy import validate_review_policy
except ModuleNotFoundError:
    from review_policy import validate_review_policy


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate model-generated PPT review results against project policies."
    )
    parser.add_argument("review_result", type=Path)
    args = parser.parse_args()
    path = args.review_result.resolve()
    review = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_review_policy(review)
    if errors:
        print("Review policy validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Review policy validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
