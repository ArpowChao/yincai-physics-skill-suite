from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

try:
    from scripts.import_moe_tts_lexicon import HOMOPHONE_BY_READING
except ModuleNotFoundError:  # Direct script execution adds scripts/ to sys.path.
    from import_moe_tts_lexicon import HOMOPHONE_BY_READING


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = (
    ROOT / "data" / "tts-pronunciation" / "cross-strait-candidates.json"
)
DEFAULT_JS_OUTPUT = (
    ROOT / "showcase" / "tts-pronunciation" / "cross-strait-candidates.js"
)
SOURCE_REPOSITORY = "https://github.com/g0v/moedict-data-csld"
SOURCE_COMMIT = "a1e91196f84cd2f3456570906191615f477278c8"
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+\Z")
TONE_SANDHI_ONLY = {"一", "不"}


def normalize_syllables(value: str) -> list[str]:
    normalized = value.replace("丨", "ㄧ").replace("　", " ").strip()
    return re.sub(r"\s+", " ", normalized).split() if normalized else []


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def aligned_readings(
    row: dict[str, str], minimum: int = 1, maximum: int = 8
) -> tuple[str, list[str], list[str]] | None:
    phrase = row.get("正體字形", "").strip()
    if not minimum <= len(phrase) <= maximum or not HAN_RE.fullmatch(phrase):
        return None
    taiwan = normalize_syllables(row.get("臺灣音讀", ""))
    mainland = normalize_syllables(row.get("大陸音讀", ""))
    if len(taiwan) != len(phrase) or len(mainland) != len(phrase):
        return None
    return phrase, taiwan, mainland


def preferred_homophones() -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for reading_map in HOMOPHONE_BY_READING.values():
        for reading, replacement in reading_map.items():
            normalized = " ".join(normalize_syllables(reading))
            if replacement not in result[normalized]:
                result[normalized].append(replacement)
    return dict(result)


def build_corpus_homophones(
    rows: Iterable[dict[str, str]],
) -> dict[str, list[str]]:
    taiwan_counts: dict[str, Counter[str]] = defaultdict(Counter)
    mainland_counts: dict[str, Counter[str]] = defaultdict(Counter)
    corpus_counts: Counter[str] = Counter()
    reading_totals: Counter[str] = Counter()
    for row in rows:
        phrase = row.get("正體字形", "").strip()
        if not 1 <= len(phrase) <= 8 or not HAN_RE.fullmatch(phrase):
            continue
        taiwan = normalize_syllables(row.get("臺灣音讀", ""))
        mainland = normalize_syllables(row.get("大陸音讀", ""))
        corpus_counts.update(phrase)
        if len(taiwan) == len(phrase):
            for character, taiwan_reading in zip(phrase, taiwan):
                taiwan_counts[taiwan_reading][character] += 1
                reading_totals[character] += 1
        if len(mainland) == len(phrase):
            for character, mainland_reading in zip(phrase, mainland):
                mainland_counts[mainland_reading][character] += 1
    return {
        reading: sorted(
            (
                character
                for character in set(candidates) | set(mainland_counts[reading])
                if mainland_counts[reading][character]
                or candidates[character] / reading_totals[character] >= 0.8
            ),
            key=lambda character: (
                -int(bool(mainland_counts[reading][character])),
                -(mainland_counts[reading][character] + candidates[character]),
                -corpus_counts[character],
                character,
            ),
        )
        for reading, candidates in {
            key: taiwan_counts[key]
            for key in set(taiwan_counts) | set(mainland_counts)
        }.items()
    }


def choose_homophone(
    reading: str,
    original: str,
    preferred: dict[str, list[str]],
    corpus_candidates: dict[str, list[str]],
) -> str | None:
    for candidate in [
        *preferred.get(reading, []),
        *corpus_candidates.get(reading, []),
    ]:
        if candidate != original:
            return candidate
    return None


def build_candidates(rows: list[dict[str, str]]) -> tuple[list[dict], dict[str, int]]:
    preferred = preferred_homophones()
    corpus_candidates = build_corpus_homophones(rows)
    rules_by_phrase: dict[str, dict] = {}
    both_readings = 0
    raw_differences = 0
    filtered_phrases = 0
    full_suggestions = 0

    for row in rows:
        if row.get("臺灣音讀", "").strip() and row.get("大陸音讀", "").strip():
            both_readings += 1
            if normalize_syllables(row["臺灣音讀"]) != normalize_syllables(
                row["大陸音讀"]
            ):
                raw_differences += 1

        aligned = aligned_readings(row, minimum=2, maximum=6)
        if not aligned:
            continue
        phrase, taiwan, mainland = aligned
        differing = [
            index
            for index, pair in enumerate(zip(taiwan, mainland))
            if pair[0] != pair[1]
        ]
        if not differing or all(phrase[index] in TONE_SANDHI_ONLY for index in differing):
            continue
        filtered_phrases += 1
        if phrase in rules_by_phrase:
            continue

        spoken = list(phrase)
        substitutions = []
        for index in differing:
            replacement = choose_homophone(
                taiwan[index], phrase[index], preferred, corpus_candidates
            )
            substitutions.append(
                {
                    "index": index,
                    "character": phrase[index],
                    "taiwan_reading": taiwan[index],
                    "mainland_reading": mainland[index],
                    "replacement": replacement or "",
                }
            )
            if replacement:
                spoken[index] = replacement

        has_full_suggestion = all(item["replacement"] for item in substitutions)
        if has_full_suggestion:
            full_suggestions += 1
        rules_by_phrase[phrase] = {
            "original": phrase,
            "spoken": "".join(spoken),
            "taiwan_pronunciation": " ".join(taiwan),
            "mainland_pronunciation": " ".join(mainland),
            "substitutions": substitutions,
            "has_full_suggestion": has_full_suggestion,
            "verified": False,
            "source": "cross-strait-reference",
            "note": (
                "兩岸詞典讀音差異；同音字是依臺灣讀音產生的草稿，"
                "請用目標 TTS 試聽後再套用。"
            ),
        }

    rules = sorted(
        rules_by_phrase.values(),
        key=lambda rule: (-len(rule["original"]), rule["original"]),
    )
    stats = {
        "source_rows": len(rows),
        "rows_with_both_readings": both_readings,
        "raw_pronunciation_differences": raw_differences,
        "filtered_phrase_rows": filtered_phrases,
        "unique_candidate_phrases": len(rules),
        "full_homophone_suggestions": full_suggestions,
    }
    return rules, stats


def apply_manual_overrides(rules: list[dict], json_output: Path) -> None:
    """Preserve human auto_apply:false review decisions across re-imports.

    Re-running this script rebuilds every rule from the raw dictionary CSV, which
    would otherwise silently drop a maintainer's "keep original, do not auto-apply"
    decision made through the showcase review page. Match by (original, spoken) so a
    decision only carries forward while it still targets the same suggested text.
    """
    if not json_output.exists():
        return
    try:
        previous = json.loads(json_output.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    rejected = {
        (rule.get("original"), rule.get("spoken"))
        for rule in previous.get("rules", [])
        if rule.get("auto_apply") is False
    }
    if not rejected:
        return
    for rule in rules:
        if (rule["original"], rule["spoken"]) in rejected:
            rule["auto_apply"] = False


def write_outputs(
    rules: list[dict], stats: dict[str, int], json_output: Path, js_output: Path
) -> None:
    apply_manual_overrides(rules, json_output)
    payload = {
        "schema_version": 1,
        "locale": "zh-TW",
        "source": {
            "name": "中華語文知識庫《兩岸詞典》（g0v 格式整理）",
            "url": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "license": "原始詞典 CC BY-NC-ND 4.0；g0v 格式轉換與編排 CC0",
        },
        "generation": stats,
        "rules": rules,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    compact = {
        "source": payload["source"],
        "generation": stats,
        "rules": [
            [
                rule["original"],
                rule["spoken"],
                rule["taiwan_pronunciation"],
                rule["mainland_pronunciation"],
                rule["has_full_suggestion"],
                rule.get("auto_apply", True),
            ]
            for rule in rules
        ],
    }
    js_output.parent.mkdir(parents=True, exist_ok=True)
    js_output.write_text(
        "globalThis.CROSS_STRAIT_PRONUNCIATION_CANDIDATES = "
        + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build pending Taiwan/Mainland pronunciation candidates for TTS review."
    )
    parser.add_argument("source", type=Path, help="兩岸詞典.csv")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--js-output", type=Path, default=DEFAULT_JS_OUTPUT)
    args = parser.parse_args()

    rows = read_rows(args.source)
    rules, stats = build_candidates(rows)
    write_outputs(rules, stats, args.json_output, args.js_output)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
