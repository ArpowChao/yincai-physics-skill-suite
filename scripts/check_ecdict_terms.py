#!/usr/bin/env python3
"""Create a read-only ECDICT candidate report for Latin-script transcript terms."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ECDICT_URL = "https://github.com/skywind3000/ECDICT"
ECDICT_REVISION = "bc015ed2e24a7abef49fc6dbbb7fe32c1dadaf8b"
ECDICT_LICENSE = "MIT"

TERM_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?=[A-Za-z0-9_.+/\-]*[A-Za-z])"
    r"[A-Za-z0-9]+(?:[-_.+/][A-Za-z0-9]+)*"
    r"(?![A-Za-z0-9])"
)

MATCH_RANK = {
    "not-found": 0,
    "normalized": 1,
    "case-variant": 2,
    "exact": 3,
}


@dataclass(frozen=True)
class Occurrence:
    token: str
    start: int
    end: int


def normalize_term(value: str) -> str:
    """Mirror ECDICT-style stripword matching: lowercase ASCII letters and digits."""

    return "".join(char.lower() for char in value if char.isascii() and char.isalnum())


def extract_occurrences(text: str) -> list[Occurrence]:
    """Extract Latin/number identifiers without changing the source text."""

    return [
        Occurrence(match.group(0), match.start(), match.end())
        for match in TERM_RE.finditer(text)
    ]


def _candidate_status(token: str, headword: str) -> str:
    if token == headword:
        return "exact"
    if token.casefold() == headword.casefold():
        return "case-variant"
    if normalize_term(token) == normalize_term(headword):
        return "normalized"
    return "not-found"


def lookup_candidates(
    tokens: Iterable[str], ecdict_csv: Path
) -> dict[str, dict[str, str]]:
    """Stream ECDICT once and retain the strongest candidate for each unique token."""

    unique_tokens = list(dict.fromkeys(tokens))
    by_folded: dict[str, set[str]] = {}
    by_normalized: dict[str, set[str]] = {}
    for token in unique_tokens:
        by_folded.setdefault(token.casefold(), set()).add(token)
        normalized = normalize_term(token)
        if normalized:
            by_normalized.setdefault(normalized, set()).add(token)

    matches: dict[str, dict[str, str]] = {}
    csv.field_size_limit(max(csv.field_size_limit(), 10_000_000))
    with ecdict_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "word" not in reader.fieldnames:
            raise ValueError("ECDICT CSV must contain a 'word' column")

        for row in reader:
            headword = (row.get("word") or "").strip()
            if not headword:
                continue
            possible = set(by_folded.get(headword.casefold(), set()))
            possible.update(by_normalized.get(normalize_term(headword), set()))
            for token in possible:
                status = _candidate_status(token, headword)
                current = matches.get(token)
                if current and MATCH_RANK[current["match"]] >= MATCH_RANK[status]:
                    continue
                matches[token] = {
                    "match": status,
                    "headword": headword,
                    "phonetic": row.get("phonetic") or "",
                    "translation": row.get("translation") or "",
                    "pos": row.get("pos") or "",
                    "exchange": row.get("exchange") or "",
                }

    return matches


def build_report(transcript: Path, ecdict_csv: Path) -> dict[str, object]:
    text = transcript.read_text(encoding="utf-8-sig")
    occurrences = extract_occurrences(text)
    matches = lookup_candidates((item.token for item in occurrences), ecdict_csv)

    grouped: dict[str, list[Occurrence]] = {}
    for item in occurrences:
        grouped.setdefault(item.token, []).append(item)

    candidates: list[dict[str, object]] = []
    for token, items in grouped.items():
        candidate: dict[str, object] = {
            "token": token,
            "match": "not-found",
            "headword": "",
            "phonetic": "",
            "translation": "",
            "pos": "",
            "exchange": "",
            "occurrences": [
                {"start": item.start, "end": item.end} for item in items
            ],
            "auto_replace": False,
            "review": "保留原詞；ECDICT 僅提供候選，專有名詞須查第一手來源。",
        }
        candidate.update(matches.get(token, {}))
        candidates.append(candidate)

    return {
        "source_file": str(transcript),
        "source_unchanged": True,
        "ecdict": {
            "url": ECDICT_URL,
            "revision": ECDICT_REVISION,
            "license": ECDICT_LICENSE,
            "csv_file": str(ecdict_csv),
        },
        "candidate_only": True,
        "candidates": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Latin-script terms and compare them with a local ECDICT CSV. "
            "The report never edits the transcript."
        )
    )
    parser.add_argument("transcript", type=Path, help="UTF-8 TXT, SRT, or VTT file")
    parser.add_argument("ecdict_csv", type=Path, help="Local ECDICT CSV file")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.transcript, args.ecdict_csv)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {len(report['candidates'])} candidates to {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
