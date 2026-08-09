from __future__ import annotations

import argparse
import json
import lzma
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = ROOT / "data" / "tts-pronunciation" / "moe-heteronyms.json"
DEFAULT_JS_OUTPUT = ROOT / "showcase" / "tts-pronunciation" / "moe-heteronyms.js"
SOURCE_URL = "https://github.com/g0v/moedict-data"

# 同音字只用在配音稿草稿。未列出的讀音仍會標示，但不會自動改字。
HOMOPHONE_BY_READING: dict[str, dict[str, str]] = {
    "角": {"ㄐㄧㄠˇ": "腳", "ㄐㄩㄝˊ": "決"},
    "行": {"ㄒㄧㄥˊ": "型", "ㄏㄤˊ": "航"},
    "長": {"ㄔㄤˊ": "常", "ㄓㄤˇ": "掌"},
    "重": {"ㄓㄨㄥˋ": "仲", "ㄔㄨㄥˊ": "崇"},
    "樂": {"ㄌㄜˋ": "勒", "ㄩㄝˋ": "月"},
    "數": {"ㄕㄨˋ": "樹", "ㄕㄨˇ": "鼠"},
    "量": {"ㄌㄧㄤˋ": "亮", "ㄌㄧㄤˊ": "良"},
    "率": {"ㄌㄩˋ": "綠", "ㄕㄨㄞˋ": "帥"},
    "校": {"ㄒㄧㄠˋ": "笑", "ㄐㄧㄠˋ": "叫"},
    "調": {"ㄊㄧㄠˊ": "條", "ㄉㄧㄠˋ": "吊"},
    "為": {"ㄨㄟˊ": "維", "ㄨㄟˋ": "位"},
    "應": {"ㄧㄥ": "英", "ㄧㄥˋ": "硬"},
    "還": {"ㄏㄞˊ": "孩", "ㄏㄨㄢˊ": "環"},
    "乾": {"ㄍㄢ": "甘", "ㄑㄧㄢˊ": "前"},
    "藏": {"ㄘㄤˊ": "蒼", "ㄗㄤˋ": "葬"},
    "朝": {"ㄔㄠˊ": "潮", "ㄓㄠ": "招"},
    "強": {"ㄑㄧㄤˊ": "牆", "ㄑㄧㄤˇ": "搶", "ㄐㄧㄤˋ": "匠"},
    "教": {"ㄐㄧㄠ": "交", "ㄐㄧㄠˋ": "叫"},
    "相": {"ㄒㄧㄤ": "香", "ㄒㄧㄤˋ": "像"},
    "降": {"ㄐㄧㄤˋ": "匠", "ㄒㄧㄤˊ": "詳"},
    "當": {"ㄉㄤ": "噹", "ㄉㄤˋ": "盪"},
    "覺": {"ㄐㄩㄝˊ": "決", "ㄐㄧㄠˋ": "叫"},
    "正": {"ㄓㄥˋ": "政", "ㄓㄥ": "征"},
    "中": {"ㄓㄨㄥ": "忠", "ㄓㄨㄥˋ": "眾"},
    "將": {"ㄐㄧㄤ": "江", "ㄐㄧㄤˋ": "匠"},
    "供": {"ㄍㄨㄥ": "工", "ㄍㄨㄥˋ": "共"},
    "曲": {"ㄑㄩ": "軀", "ㄑㄩˇ": "取"},
    "分": {"ㄈㄣ": "芬", "ㄈㄣˋ": "份"},
    "處": {"ㄔㄨˇ": "楚", "ㄔㄨˋ": "觸"},
    "種": {"ㄓㄨㄥˇ": "腫", "ㄓㄨㄥˋ": "眾"},
    "累": {"ㄌㄟˋ": "類", "ㄌㄟˇ": "壘", "ㄌㄟˊ": "雷"},
    "空": {"ㄎㄨㄥˋ": "控"},
    "露": {"ㄌㄨˋ": "路", "ㄌㄡˋ": "漏"},
    "參": {"ㄘㄢ": "餐", "ㄕㄣ": "深"},
    "解": {"ㄐㄧㄝˇ": "姐", "ㄐㄧㄝˋ": "借", "ㄒㄧㄝˋ": "謝"},
    "差": {"ㄔㄚ": "叉", "ㄔㄚˋ": "岔", "ㄔㄞ": "拆", "ㄘ": "疵"},
    "背": {"ㄅㄟ": "杯", "ㄅㄟˋ": "被"},
    "假": {"ㄐㄧㄚˇ": "甲", "ㄐㄧㄚˋ": "價"},
    "了": {"ㄌㄧㄠˇ": "瞭"},
    "切": {"ㄑㄧㄝ": "且", "ㄑㄧㄝˋ": "竊"},
    "省": {"ㄒㄧㄥˇ": "醒"},
    "少": {"ㄕㄠˋ": "紹"},
    "好": {"ㄏㄠˋ": "號"},
    "轉": {"ㄓㄨㄢˋ": "賺"},
    "給": {"ㄐㄧˇ": "己"},
    "得": {"ㄉㄜˊ": "德", "ㄉㄜ": "的"},
    "著": {"ㄓㄨㄛˊ": "卓", "ㄓㄠ": "招"},
    "和": {"ㄏㄜˊ": "河", "ㄏㄜˋ": "賀", "ㄏㄨㄛˋ": "或"},
    "只": {"ㄓˇ": "紙"},
    "便": {"ㄅㄧㄢˋ": "變"},
    "難": {"ㄋㄢˊ": "南"},
}


def normalize_bopomofo(value: str) -> list[str]:
    return re.sub(r"[\s˙]+", " ", value.strip()).split()


def load_moe_entries(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".xz":
        with lzma.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    return json.loads(path.read_text(encoding="utf-8"))


def build_rules(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tracked = set(HOMOPHONE_BY_READING)
    rules_by_phrase: dict[str, dict[str, Any]] = {}
    for entry in entries:
        phrase = str(entry.get("title", ""))
        if not 2 <= len(phrase) <= 8 or not tracked.intersection(phrase):
            continue
        for heteronym in entry.get("heteronyms", []):
            syllables = normalize_bopomofo(str(heteronym.get("bopomofo", "")))
            if len(syllables) != len(phrase):
                continue
            spoken = list(phrase)
            reviewed: list[dict[str, Any]] = []
            for index, character in enumerate(phrase):
                if character not in tracked:
                    continue
                reading = syllables[index]
                replacement = HOMOPHONE_BY_READING[character].get(reading, character)
                spoken[index] = replacement
                reviewed.append(
                    {
                        "index": index,
                        "character": character,
                        "reading": reading,
                        "replacement": replacement,
                    }
                )
            rules_by_phrase.setdefault(
                phrase,
                {
                    "original": phrase,
                    "spoken": "".join(spoken),
                    "pronunciation": " ".join(syllables),
                    "reviewed": reviewed,
                    "verified": False,
                    "source": "moe-revised-dictionary",
                    "note": "教育部辭典讀音參考；同音字是配音草稿，套用前請人工確認。",
                },
            )
            break
    return sorted(rules_by_phrase.values(), key=lambda rule: (-len(rule["original"]), rule["original"]))


def write_outputs(rules: list[dict[str, Any]], json_output: Path, js_output: Path) -> None:
    payload = {
        "schema_version": 1,
        "locale": "zh-TW",
        "source": {
            "name": "教育部重編國語辭典修訂本（g0v JSON 格式轉換）",
            "url": SOURCE_URL,
            "license": "CC BY-ND 3.0 TW；格式轉換與應用依教育部公眾授權說明",
        },
        "rules": rules,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    js_output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    compact_browser_payload = {
        "source": payload["source"],
        "rules": [
            [rule["original"], rule["spoken"], rule["pronunciation"]]
            for rule in rules
        ],
    }
    browser_serialized = json.dumps(
        compact_browser_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    json_output.write_text(serialized + "\n", encoding="utf-8")
    js_output.write_text(
        f"globalThis.MOE_HETERONYM_LEXICON={browser_serialized};\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="匯入教育部辭典的常見多音詞讀音參考。")
    parser.add_argument("source", type=Path, help="dict-revised.json 或 dict-revised.json.xz")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--js-output", type=Path, default=DEFAULT_JS_OUTPUT)
    args = parser.parse_args()
    rules = build_rules(load_moe_entries(args.source))
    write_outputs(rules, args.json_output, args.js_output)
    print(f"已匯入 {len(rules)} 條多音詞讀音參考。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
