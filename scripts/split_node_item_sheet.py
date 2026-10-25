"""把含 4 題的任務單 docx 拆成「_練習題」與「_診斷題」兩份（yincai-physics-node-items 使用）。

用法：
  python scripts/split_node_item_sheet.py 任務單.docx [...] [--out-dir 目錄] [--force]

輸出：任務單_練習題.docx（理解題、應用題）與 任務單_診斷題.docx（診斷題1、2）。
兩份都保留填寫說明、編號表與範例；題號各自從 1 重編，區段標題分別為「練習題」「診斷題」。
只用標準函式庫，直接改 word/document.xml，其他零件原樣複製。原檔不動。
"""
from __future__ import annotations

import argparse
import html
import io
import re
import sys
import zipfile
from pathlib import Path

KINDS = ("練習題", "診斷題")
TAG = re.compile(r"<(/?)([\w:.\-]+)[^>]*?(/?)>")
TEXT = re.compile(r"(<w:t(?:\s[^>]*)?>)([^<]*)(</w:t>)")
ITEM = re.compile(r"^\s*\d+\s*[.．、]\s*(?:理解題|應用題|診斷題)")
CONTENT = re.compile(r"<w:drawing|<w:pict|<m:oMath|<w:object")


def top_level(xml: str, start: int, end: int) -> list[tuple[str, str]]:
    """回傳 body 底下每個直接子元素的 (標籤名, 原始字串)。"""
    spans, depth, begin, name = [], 0, 0, ""
    for m in TAG.finditer(xml, start, end):
        closing, tag, self_closing = m.groups()
        if closing:
            depth -= 1
            if depth == 0:
                spans.append((name, xml[begin:m.end()]))
        elif self_closing:
            if depth == 0:
                spans.append((tag, m.group(0)))
        else:
            if depth == 0:
                begin, name = m.start(), tag
            depth += 1
    return spans


def text_of(fragment: str) -> str:
    return html.unescape("".join(m.group(2) for m in TEXT.finditer(fragment)))


def is_blank(name: str, fragment: str) -> bool:
    return name == "w:p" and not text_of(fragment).strip() and not CONTENT.search(fragment)


def set_text(fragment: str, new: str) -> str:
    """整段文字改成 new：寫進第一個 w:t，其餘 w:t 清空。"""
    first = True

    def repl(m: re.Match) -> str:
        nonlocal first
        value = html.escape(new, quote=False) if first else ""
        first = False
        return m.group(1) + value + m.group(3)

    return TEXT.sub(repl, fragment)


def renumber(fragment: str, number: int) -> str:
    """把標題開頭的題號換成 number，題號跨多個 w:t 也能處理。"""
    nodes = list(TEXT.finditer(fragment))
    joined = "".join(m.group(2) for m in nodes)
    m = re.match(r"\s*(\d+)", joined)
    if not m:
        return fragment
    lo, hi = m.span(1)
    out, pos, offset, placed = [], 0, 0, False
    for node in nodes:
        value = node.group(2)
        a, b = max(lo - offset, 0), min(hi - offset, len(value))
        if a < b:
            value = value[:a] + ("" if placed else str(number)) + value[b:]
            placed = True
        offset += len(node.group(2))
        out.append(fragment[pos:node.start(2)] + value)
        pos = node.end(2)
    out.append(fragment[pos:])
    return "".join(out)


def split_document_xml(xml: str) -> dict[str, str]:
    open_tag = re.search(r"<w:body(?:\s[^>]*)?>", xml)
    close = xml.rindex("</w:body>")
    children = top_level(xml, open_tag.end(), close)
    sect = [frag for name, frag in children if name == "w:sectPr"]
    children = [(n, f) for n, f in children if n != "w:sectPr"]

    starts = [i for i, (n, f) in enumerate(children) if n == "w:p" and ITEM.match(text_of(f))]
    if not starts:
        raise ValueError("找不到「N. 理解題／應用題／診斷題」題號標題")
    head = children[:starts[0]]
    section = next((f for n, f in head if n == "w:p" and text_of(f).strip() in KINDS), None)
    head = [f for n, f in head if f is not section]
    if section is None:
        section = re.sub(r' w14:(?:paraId|textId)="[^"]*"', "", children[starts[0]][1])

    groups: dict[str, list[list[tuple[str, str]]]] = {kind: [] for kind in KINDS}
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(children)
        kind = "診斷題" if "診斷" in text_of(children[s][1]) else "練習題"
        groups[kind].append(children[s:e])
    for kind, items in groups.items():
        if not items:
            raise ValueError(f"找不到{kind}的題目")

    result = {}
    for kind, items in groups.items():
        items = [list(seg) for seg in items]
        while items[-1] and is_blank(*items[-1][-1]):
            items[-1].pop()
        parts = head + [set_text(section, kind)]
        for number, seg in enumerate(items, 1):
            parts.append(renumber(seg[0][1], number))
            parts.extend(f for _, f in seg[1:])
        parts.append("<w:p/>")
        parts.extend(sect)
        result[kind] = xml[:open_tag.end()] + "".join(parts) + xml[close:]
    return result


def split_docx_bytes(data: bytes) -> dict[str, bytes]:
    source = zipfile.ZipFile(io.BytesIO(data))
    xml = source.read("word/document.xml").decode("utf-8")
    result = {}
    for kind, new_xml in split_document_xml(xml).items():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as target:
            for info in source.infolist():
                payload = new_xml.encode("utf-8") if info.filename == "word/document.xml" else source.read(info)
                # writestr 會改寫 ZipInfo 的位移，來源的 info 第二輪還要讀，所以另建一份
                entry = zipfile.ZipInfo(info.filename, info.date_time)
                entry.external_attr = info.external_attr
                target.writestr(entry, payload, compress_type=zipfile.ZIP_DEFLATED)
        result[kind] = buffer.getvalue()
    return result


def output_paths(path: Path, out_dir: Path | None = None) -> dict[str, Path]:
    folder = out_dir or path.parent
    return {kind: folder / f"{path.stem}_{kind}{path.suffix}" for kind in KINDS}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把任務單拆成練習題與診斷題兩份 docx")
    parser.add_argument("docx", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--force", action="store_true", help="覆寫已存在的輸出檔")
    args = parser.parse_args(argv)
    status = 0
    for path in args.docx:
        if path.stem.endswith(KINDS):
            print(f"略過 {path.name}：已是拆分檔")
            continue
        targets = output_paths(path, args.out_dir)
        existing = [p.name for p in targets.values() if p.exists()]
        if existing and not args.force:
            print(f"略過 {path.name}：{'、'.join(existing)} 已存在（要覆寫加 --force）")
            status = 1
            continue
        try:
            parts = split_docx_bytes(path.read_bytes())
        except (ValueError, KeyError, zipfile.BadZipFile) as error:
            print(f"失敗 {path.name}：{error}")
            status = 1
            continue
        for kind, target in targets.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(parts[kind])
            print("saved", target)
    return status


if __name__ == "__main__":
    sys.exit(main())
