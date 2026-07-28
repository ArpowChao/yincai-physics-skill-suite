from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    DEFAULT_PROJECT_NODE_OVERRIDES,
    DEFAULT_PROJECT_NODES,
    apply_project_node_overrides,
    load_project_nodes,
    normalize_project_node_code,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Add or replace one team-reviewed project-node override without "
            "requiring the source XLSX files."
        )
    )
    parser.add_argument("patch", type=Path, help="JSON patch containing code/reason/evidence/set")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_PROJECT_NODES)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_PROJECT_NODE_OVERRIDES)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the patch without changing the overrides file.",
    )
    args = parser.parse_args()

    patch = json.loads(args.patch.read_text(encoding="utf-8"))
    code = normalize_project_node_code(str(patch.pop("code")))
    override_file = args.overrides.resolve()
    overrides = (
        json.loads(override_file.read_text(encoding="utf-8"))
        if override_file.exists()
        else {
            "catalog_version": "1.0.0",
            "purpose": (
                "Team-reviewed project node corrections that survive raw Excel re-imports."
            ),
            "entries": {},
        }
    )
    overrides.setdefault("entries", {})[code] = patch

    base = load_project_nodes(args.catalog.resolve(), overrides_path=None)
    applied = apply_project_node_overrides(base, overrides)
    if not args.check:
        override_file.write_text(
            json.dumps(overrides, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "code": code,
                "valid": True,
                "written": not args.check,
                "overrides_file": str(override_file),
                "resolved_title": applied["entries"][code].get("title"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
