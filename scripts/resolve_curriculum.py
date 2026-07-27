from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    DEFAULT_CURRICULUM,
    DEFAULT_PROJECT_NODES,
    load_curriculum,
    load_project_nodes,
    resolve_curriculum_scope,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a project learning-node code to its official Stage 5 parent."
    )
    parser.add_argument("code")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CURRICULUM)
    parser.add_argument(
        "--project-catalog",
        type=Path,
        default=DEFAULT_PROJECT_NODES,
    )
    args = parser.parse_args()
    entry = resolve_curriculum_scope(
        args.code,
        load_curriculum(args.catalog),
        load_project_nodes(args.project_catalog),
    )
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
