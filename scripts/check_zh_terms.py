"""掃描中文逐字稿，列出理化專有名詞的候選誤植。

本工具唯讀：只輸出候選清單與依據，不改寫輸入檔，也不代替人工判定。
命中僅代表「該字串出現在對照表的 variants 中」，仍須依語境與第一手來源覆核。

用法：
    python scripts/check_zh_terms.py <逐字稿.txt> [--terms <對照表.json>]
        [--output <報告.json>] [--domain physics] [--include-guarded]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMS = ROOT / "data" / "terminology" / "zh-tw-science-terms.json"


def load_terms(path: Path) -> dict:
    """讀取對照表並做最小結構檢查。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "entries" not in data or not isinstance(data["entries"], list):
        raise ValueError(f"{path} 缺少 entries 陣列")
    return data


def build_lookup(entries: list[dict], domain: str | None = None) -> list[tuple[str, dict]]:
    """展開成 (variant, entry) 清單，長詞在前以便最長匹配。"""
    pairs: list[tuple[str, dict]] = []
    for entry in entries:
        if domain and entry.get("domain") != domain:
            continue
        for variant in entry.get("variants", []):
            if variant:
                pairs.append((variant, entry))
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    return pairs


def scan_text(text: str, entries: list[dict], domain: str | None = None) -> dict:
    """回報每個命中的位置。重疊命中只保留最長的那一個。"""
    pairs = build_lookup(entries, domain)
    claimed: set[int] = set()
    hits: list[dict] = []

    for variant, entry in pairs:
        start = text.find(variant)
        while start != -1:
            span = range(start, start + len(variant))
            if not any(index in claimed for index in span):
                claimed.update(span)
                line = text.count("\n", 0, start) + 1
                hits.append(
                    {
                        "found": variant,
                        "preferred": entry["preferred"],
                        "category": entry.get("category", ""),
                        "domain": entry.get("domain", ""),
                        "english": entry.get("english", ""),
                        "evidence": entry.get("evidence", []),
                        "line": line,
                        "offset": start,
                        "context": text[max(0, start - 12) : start + len(variant) + 12].replace(
                            "\n", " "
                        ),
                        "context_guard": entry.get("context_guard", ""),
                        "requires_context_review": bool(entry.get("context_guard")),
                        "note": entry.get("note", ""),
                    }
                )
            start = text.find(variant, start + 1)

    hits.sort(key=lambda hit: hit["offset"])
    guarded = [hit for hit in hits if hit["requires_context_review"]]
    return {
        "source_characters": len(text),
        "total_hits": len(hits),
        "guarded_hits": len(guarded),
        "auto_replace": False,
        "reminder": (
            "候選僅供人工覆核；context_guard 條目必須先讀語境，"
            "未經第一手來源確認不得改寫專有名詞。"
        ),
        "hits": hits,
    }


def format_report(report: dict) -> str:
    if not report["hits"]:
        return "沒有命中對照表中的候選誤植。仍請人工覆核未收錄的專有名詞。"

    lines = [
        f"共 {report['total_hits']} 個候選"
        f"（其中 {report['guarded_hits']} 個需先判斷語境）：",
        "",
    ]
    for hit in report["hits"]:
        flag = " [需判斷語境]" if hit["requires_context_review"] else ""
        lines.append(
            f"行 {hit['line']}：{hit['found']} → {hit['preferred']}"
            f"（{hit['category']}／{hit['domain']}）{flag}"
        )
        lines.append(f"    上下文：…{hit['context']}…")
        if hit["context_guard"]:
            lines.append(f"    語境警告：{hit['context_guard']}")
    lines.append("")
    lines.append(report["reminder"])
    return "\n".join(lines)


def configure_stdout() -> None:
    """Windows 主控台預設 cp950，無法輸出「氹」這類罕用字。

    ASR 誤植本來就常出現罕用字，輸出編碼必須改成 UTF-8 並容錯，
    否則查核工具會在最需要它的案例上直接崩潰。
    """
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="中文理化專有名詞候選誤植查核（唯讀）")
    parser.add_argument("transcript", type=Path, help="逐字稿純文字檔")
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS, help="對照表 JSON")
    parser.add_argument("--output", type=Path, help="輸出 JSON 報告路徑")
    parser.add_argument("--domain", help="只查特定領域，如 physics／chemistry／biology")
    args = parser.parse_args(argv)

    if not args.transcript.exists():
        print(f"找不到逐字稿：{args.transcript}", file=sys.stderr)
        return 2
    if not args.terms.exists():
        print(f"找不到對照表：{args.terms}", file=sys.stderr)
        return 2

    data = load_terms(args.terms)
    text = args.transcript.read_text(encoding="utf-8")
    report = scan_text(text, data["entries"], args.domain)
    report["terminology_version"] = data.get("terminology_version", "")
    report["evidence_policy"] = data.get("evidence_policy", [])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"報告已寫入 {args.output}")

    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
