"""檢查 WSQ 學生版是否符合固定格式與長度上限（physics-worksheet-generator 使用）。

用法：
  python scripts/audit_wsq.py outputs/節點_WSQ.md [...]

只檢查第一個標題含「WSQ」的一級標題到下一個一級標題之間（學生版）。
出現 ⚠ 的項目須處理；有 ⚠ 時結束碼為 1。只用標準函式庫。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

W_MIN, W_MAX = 3, 5
W_PROMPT_MAX = 35
PAGE = re.compile(r"（第\s*\d+(?:～\d+)?\s*張）")
ITEM = re.compile(r"^\d+\.\s*(.*)$")
BLANK_LINE = re.compile(r"^[＿_\s]{6,}$")
TIMESTAMP = re.compile(r"(?<![\d.])\d{1,2}:\d{2}(?![\d])")


def student_block(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("# ") and "WSQ" in line), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("# ")), len(lines))
    return lines[start:end]


def sections(block: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = None
    for line in block[1:]:
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif current is not None and line.strip():
            result[current].append(line.strip())
    return result


def prompt_length(item: str) -> int:
    body = PAGE.sub("", item)
    body = re.sub(r"[＿_□\s]", "", body)
    return len(body)


def audit(text: str) -> tuple[list[str], dict[str, int]]:
    block = student_block(text)
    if not block:
        return ["找不到標題含「WSQ」的學生版"], {}
    warn: list[str] = []
    parts = sections(block)
    keys = {k[0]: k for k in parts if k[:1] in "WSQ"}
    order = [k[:1] for k in parts]
    if order != ["W", "S", "Q"]:
        warn.append(f"區塊須依序只有 W、S、Q，實際為 {order}")

    w_items = [ITEM.match(line).group(1) for line in parts.get(keys.get("W", ""), []) if ITEM.match(line)]
    if not W_MIN <= len(w_items) <= W_MAX:
        warn.append(f"W 有 {len(w_items)} 格（應 {W_MIN}～{W_MAX} 格）")
    for n, item in enumerate(w_items, 1):
        # 標了頁碼，學生會只盯那幾張投影片、忽略其他頁面
        if PAGE.search(item):
            warn.append(f"W{n} 標了投影片頁碼（第 N 張），請拿掉")
        if "＿" not in item and "□" not in item:
            warn.append(f"W{n} 沒有作答空格或勾選")
        if prompt_length(item) > W_PROMPT_MAX:
            warn.append(f"W{n} 題目 {prompt_length(item)} 字（上限 {W_PROMPT_MAX}）")

    s_key = keys.get("S", "")
    s_lines = parts.get(s_key, [])
    if s_key and "30" not in s_key:
        warn.append("S 標題沒寫 30 字內")
    if sum(line.startswith("提示：") for line in s_lines) != 1:
        warn.append("S 要有一行「提示：」句首")
    if sum(bool(BLANK_LINE.match(line)) for line in s_lines) != 1:
        warn.append("S 只留一行作答")

    q_lines = parts.get(keys.get("Q", ""), [])
    if sum(line.count("□") == 3 for line in q_lines) != 1:
        warn.append("Q 要有一行三個句首勾選")
    if sum(bool(BLANK_LINE.match(line)) for line in q_lines) != 1:
        warn.append("Q 只留一行作答")

    body = "\n".join(block)
    if any(line.lstrip().startswith("|") for line in block):
        warn.append("學生版不放表格")
    if TIMESTAMP.search(body):
        warn.append(f"學生版不用影片時間碼{TIMESTAMP.findall(body)[:3]}")
    if "$" in body:
        warn.append("學生版不放公式推導（LaTeX）")

    stats = {"W": len(w_items), "minutes": len(w_items) + 3 + 2}
    return warn, stats


def main(argv: list[str] | None = None) -> int:
    status = 0
    for path in argv if argv is not None else sys.argv[1:]:
        warn, stats = audit(Path(path).read_text(encoding="utf-8"))
        print("##", Path(path).name)
        if stats:
            print(f"  W {stats['W']} 格＋S 1 題＋Q 1 題，估計作答 {stats['minutes']} 分鐘")
        for item in warn:
            print("  ⚠", item)
        if not warn:
            print("  OK")
        status = status or (1 if warn else 0)
    return status


if __name__ == "__main__":
    sys.exit(main())
