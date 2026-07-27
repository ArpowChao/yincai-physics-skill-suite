from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import DEFAULT_CURRICULUM, load_curriculum, resolve_official_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a project learning-node code to its official Stage 5 parent."
    )
    parser.add_argument("code")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args()
    entry = resolve_official_code(args.code, load_curriculum(args.catalog))
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
