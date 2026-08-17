from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "terminology" / "research-proper-terms.json"
VALID_ACTIONS = {"replace", "review", "preserve"}
VALID_CONFIDENCE = {"confirmed", "candidate"}


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(registry)
    return registry


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise ValueError("Unsupported terminology registry schema_version")

    sources = registry.get("sources")
    terms = registry.get("terms")
    if not isinstance(sources, list) or not isinstance(terms, list):
        raise ValueError("Registry must contain sources and terms lists")

    source_ids: set[str] = set()
    for source in sources:
        required = {"id", "name", "url", "version", "retrieved_on", "role"}
        if not required.issubset(source):
            raise ValueError(f"Incomplete source record: {source}")
        if source["id"] in source_ids:
            raise ValueError(f"Duplicate source id: {source['id']}")
        source_ids.add(source["id"])

    term_ids: set[str] = set()
    variant_texts: set[str] = set()
    for term in terms:
        required = {"id", "preferred", "term_type", "source_ids", "variants"}
        if not required.issubset(term):
            raise ValueError(f"Incomplete term record: {term}")
        if term["id"] in term_ids:
            raise ValueError(f"Duplicate term id: {term['id']}")
        term_ids.add(term["id"])
        if not term["source_ids"] or not set(term["source_ids"]).issubset(source_ids):
            raise ValueError(f"Unknown or missing source for term: {term['id']}")
        for variant in term["variants"]:
            required_variant = {"text", "kind", "action", "confidence"}
            if not required_variant.issubset(variant):
                raise ValueError(f"Incomplete variant for term: {term['id']}")
            if not variant["text"]:
                raise ValueError(f"Empty variant for term: {term['id']}")
            if variant["text"] in variant_texts:
                raise ValueError(f"Duplicate variant text: {variant['text']}")
            variant_texts.add(variant["text"])
            if variant["action"] not in VALID_ACTIONS:
                raise ValueError(f"Invalid action for {variant['text']}")
            if variant["confidence"] not in VALID_CONFIDENCE:
                raise ValueError(f"Invalid confidence for {variant['text']}")


def scan_text(
    text: str,
    registry: dict[str, Any],
    *,
    include_known: bool = False,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for term in registry["terms"]:
        for variant in term["variants"]:
            if variant["action"] == "preserve" and not include_known:
                continue
            start = text.find(variant["text"])
            while start >= 0:
                end = start + len(variant["text"])
                candidates.append(
                    {
                        "start": start,
                        "end": end,
                        "original": variant["text"],
                        "preferred": term["preferred"],
                        "term_id": term["id"],
                        "term_type": term["term_type"],
                        "variant_kind": variant["kind"],
                        "action": variant["action"],
                        "confidence": variant["confidence"],
                        "source_ids": list(term["source_ids"]),
                    }
                )
                start = text.find(variant["text"], start + 1)

    candidates.sort(key=lambda item: (item["start"], -len(item["original"])))
    selected: list[dict[str, Any]] = []
    occupied_until = -1
    for candidate in candidates:
        if candidate["start"] < occupied_until:
            continue
        selected.append(candidate)
        occupied_until = candidate["end"]
    return selected


def _read_input(path_text: str) -> str:
    if path_text == "-":
        return sys.stdin.read()
    return Path(path_text).read_text(encoding="utf-8-sig")


def _format_text_report(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "No registered terminology matches."
    lines = []
    for match in matches:
        sources = ", ".join(match["source_ids"])
        lines.append(
            f"{match['start']}:{match['end']} {match['original']} -> "
            f"{match['preferred']} [{match['action']}/{match['confidence']}; {sources}]"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only scan against the reviewed research proper-name registry; "
            "actions are review metadata and never authorize rewriting."
        )
    )
    parser.add_argument("input", help="UTF-8 text file, or - for stdin")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument(
        "--include-known",
        action="store_true",
        help="Also report preferred forms and accepted aliases that must be preserved.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    registry = load_registry(args.registry)
    text = _read_input(args.input)
    matches = scan_text(text, registry, include_known=args.include_known)

    if args.format == "json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        print(_format_text_report(matches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
