"""把 WSQ 學生版 Markdown 轉成一頁 DOCX（physics-worksheet-generator 使用）。

用法：
  python scripts/build_wsq_docx.py outputs/節點_WSQ.md outputs/節點_單元_WSQ.docx

只轉第一個標題含「WSQ」的一級標題到下一個一級標題之間（學生版），格式見 audit_wsq.py。
需要 python-docx。中文微軟正黑體、英文與數字 Arial。

版型：
- 標頭：左側米色標題區（節點碼＋單元名稱），右側深藍「WSQ」標籤；下接班級／座號／姓名欄。
- W／S／Q 各有色塊徽章（藍／橘紅／綠）與一行作答說明。
- W 每格只有題號與題目（不標投影片頁碼）；S、Q 放進淡色作答框，各給兩條手寫作答線。
- 句中的＿＿轉成加長的底線空格；□ 換成較大的 ☐。色塊與作答線在黑白列印下仍分得出來。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from audit_wsq import BLANK_LINE, ITEM, sections, student_block

EAST_ASIA = "微軟正黑體"
LATIN = "Arial"
BLANK = re.compile(r"＿+")
ANSWER_LINES = 2
CONTENT_W = 17.4  # 版心寬（cm），A4 左右各留 1.8 cm

NAVY, INK, MUTED, RULE, PAPER = "12233F", "33415C", "6B7280", "C9CED6", "F4F1EA"
COLOR = {"W": "1F4E8C", "S": "D2542F", "Q": "2F7A5F"}
TINT = {"W": "E9EFF7", "S": "FBEEE9", "Q": "E8F2ED"}
LINE = {"W": "7F97BD", "S": "C98E7A", "Q": "84AE98"}
ENGLISH = {"W": "Watch", "S": "Summarize", "Q": "Question"}
HINT = {"W": "依影片順序，邊看邊填","S": "從提示接著寫，用自己的話", "Q": "勾選一個句首，接著寫下去"}

# Word 對順序不合 schema 的屬性會忽略（網底、框線不見）或判定檔案損毀
TC_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
            "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]
TBL_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
             "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook"]
AFTER_PBDR = ["w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct",
              "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
              "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
              "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
              "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange"]


def parse(text: str) -> dict:
    """回傳 {"title", "code", "name", "header", "labels", "sections": [(標題, [行...])]}；不依賴 python-docx，可單獨測試。"""
    block = student_block(text)
    if not block:
        raise ValueError("找不到標題含「WSQ」的學生版")
    title = block[0][2:].strip()
    code, _, name = title.removesuffix("｜WSQ").partition(" ")
    header = next((line.strip() for line in block[1:] if line.strip() and not line.startswith("## ")), "")
    labels = [part.strip("：:　 ") for part in BLANK.split(header) if part.strip("：:　 ")]
    parts = sections(block)
    return {"title": title, "code": code, "name": name.strip(), "header": header, "labels": labels,
            "sections": list(parts.items())}


def build(spec: dict, out: Path) -> None:
    from docx import Document
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT as VALIGN
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor, Twips

    def el(tag: str, **attrs):
        node = OxmlElement(tag)
        for key, value in attrs.items():
            node.set(qn(f"w:{key}"), str(value))
        return node

    def put(parent, child, order: list[str]) -> None:
        tag = child.tag.rsplit("}", 1)[-1]
        for old in parent.findall(qn(f"w:{tag}")):
            parent.remove(old)
        rank = order.index(tag)
        for existing in parent:
            name = existing.tag.rsplit("}", 1)[-1]
            if name in order and order.index(name) > rank:
                existing.addprevious(child)
                return
        parent.append(child)

    def shade(cell, fill: str) -> None:
        put(cell._tc.get_or_add_tcPr(), el("w:shd", val="clear", color="auto", fill=fill), TC_ORDER)

    def borders(cell, **edges) -> None:
        """edges：top/left/bottom/right=(粗細, 顏色, 線型)；未列的邊不畫。"""
        box = OxmlElement("w:tcBorders")
        for edge in ("top", "left", "bottom", "right"):
            sz, color, val = edges.get(edge, (0, "auto", "nil"))
            box.append(el(f"w:{edge}", val=val, sz=sz, space=0, color=color))
        put(cell._tc.get_or_add_tcPr(), box, TC_ORDER)

    def margins(cell, top: float, bottom: float, left: float, right: float) -> None:
        mar = OxmlElement("w:tcMar")
        for edge, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
            mar.append(el(f"w:{edge}", w=int(value * 567), type="dxa"))
        put(cell._tc.get_or_add_tcPr(), mar, TC_ORDER)

    def table(widths: list[float], rows: int = 1):
        t = doc.add_table(rows=rows, cols=len(widths))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        put(t._tbl.tblPr, el("w:tblW", w=int(sum(widths) * 567), type="dxa"), TBL_ORDER)
        put(t._tbl.tblPr, el("w:tblLayout", type="fixed"), TBL_ORDER)
        for row in t.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Cm(width)
        return t

    def fmt(p, before: float = 0, after: float = 0, spacing: float = 1.15, align=None):
        pf = p.paragraph_format
        pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), spacing
        if align is not None:
            p.alignment = align
        return p

    def run(p, text: str, size: float, color: str = INK, bold: bool = False,
            underline: bool = False, fill: str | None = None):
        r = p.add_run(text)
        r.font.size, r.font.bold, r.font.name, r.font.underline = Pt(size), bold, LATIN, underline
        r.font.color.rgb = RGBColor.from_string(color)
        r_pr = r._element.get_or_add_rPr()
        r_pr.get_or_add_rFonts().set(qn("w:eastAsia"), EAST_ASIA)
        if fill:
            r_pr.append(el("w:shd", val="clear", color="auto", fill=fill))

    def rich(p, text: str, size: float) -> None:
        pos = 0
        for m in list(BLANK.finditer(text)) + [None]:
            end = m.start() if m else len(text)
            if text[pos:end]:
                run(p, text[pos:end].replace("□", "☐"), size)
            if m:
                # 用不換行空格：Word 不畫段尾一般空格的底線
                run(p, " " * max(18, len(m.group()) * 6), size, NAVY, underline=True)
                pos = m.end()

    def answer_lines(cell, color: str) -> None:
        for _ in range(ANSWER_LINES):
            p = cell.add_paragraph()
            pf = p.paragraph_format
            pf.space_before, pf.space_after = Pt(0), Pt(0)
            pf.line_spacing_rule, pf.line_spacing = WD_LINE_SPACING.EXACTLY, Pt(38)
            # 連續兩段框線相同時 Word 會合併成一組，只畫 bottom；加 between 才會每行都有線
            border = OxmlElement("w:pBdr")
            for edge in ("bottom", "between"):
                border.append(el(f"w:{edge}", val="single", sz=6, space=1, color=color))
            p._p.get_or_add_pPr().insert_element_before(border, *AFTER_PBDR)

    def spacer(pt: float) -> None:
        # 也用來隔開表格：相鄰表格會被 Word 併成一張
        p = fmt(doc.add_paragraph(), spacing=1.0)
        p.paragraph_format.line_spacing_rule, p.paragraph_format.line_spacing = WD_LINE_SPACING.EXACTLY, Pt(pt)

    def section_head(key: str, heading: str) -> None:
        badge, title = table([1.5, CONTENT_W - 1.5]).rows[0].cells
        shade(badge, COLOR[key])
        margins(badge, 0.08, 0.08, 0.05, 0.05)
        badge.vertical_alignment = VALIGN.CENTER
        run(fmt(badge.paragraphs[0], spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER), key, 20, "FFFFFF", bold=True)
        run(fmt(badge.add_paragraph(), spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER), ENGLISH[key], 7, "FFFFFF")
        borders(title, bottom=(12, COLOR[key], "single"))
        margins(title, 0.05, 0.08, 0.3, 0.1)
        title.vertical_alignment = VALIGN.BOTTOM
        p = fmt(title.paragraphs[0], spacing=1.0)
        run(p, heading[1:].strip(), 14.5, COLOR[key], bold=True)
        run(p, "　" + HINT[key], 9, MUTED)

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin = section.right_margin = Cm((21 - CONTENT_W) / 2)
    section.top_margin, section.bottom_margin, section.footer_distance = Cm(1.5), Cm(1.6), Cm(0.8)
    # 空段落（表格間隔、儲存格段落記號）用小字，避免撐高版面
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = LATIN, Pt(4)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), EAST_ASIA)

    left, right = table([CONTENT_W - 3.2, 3.2]).rows[0].cells
    shade(left, PAPER)
    borders(left, left=(36, NAVY, "single"))
    margins(left, 0.25, 0.25, 0.45, 0.3)
    left.vertical_alignment = VALIGN.CENTER
    p = fmt(left.paragraphs[0], after=2, spacing=1.0)
    run(p, spec["code"], 10.5, NAVY, bold=True)
    run(p, "　因材網高中物理．看影片紀錄單", 9.5, MUTED)
    # 長單元名稱（如「原子核融合是質量轉換為能量的應用實例」）縮字級，維持一行
    run(fmt(left.add_paragraph(), spacing=1.05), spec["name"], 19 if len(spec["name"]) <= 14 else 17, NAVY, bold=True)
    shade(right, NAVY)
    margins(right, 0.2, 0.2, 0.1, 0.1)
    right.vertical_alignment = VALIGN.CENTER
    run(fmt(right.paragraphs[0], spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER), "WSQ", 22, "FFFFFF", bold=True)
    run(fmt(right.add_paragraph(), before=2, spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER), "作答約 10 分鐘", 8.5, "D6DCE6")

    if spec["labels"]:
        spacer(8)
        widths = [4.6] * (len(spec["labels"]) - 1)
        for cell, label in zip(table(widths + [CONTENT_W - sum(widths)]).rows[0].cells, spec["labels"]):
            borders(cell, bottom=(6, RULE, "single"))
            margins(cell, 0.05, 0.05, 0.1, 0.3)
            run(fmt(cell.paragraphs[0], spacing=1.0), label + "：", 11, MUTED)

    for heading, lines in spec["sections"]:
        key = heading[:1]
        spacer(16)
        section_head(key, heading)
        spacer(4)
        if key == "W":
            items = [ITEM.match(line).group(1) for line in lines if ITEM.match(line)]
            for n, (row, item) in enumerate(zip(table([1.0, CONTENT_W - 1.0], rows=len(items)).rows, items), 1):
                no, body = row.cells
                for cell in row.cells:
                    cell.vertical_alignment = VALIGN.CENTER
                    if n < len(items):
                        borders(cell, bottom=(4, RULE, "dotted"))
                shade(no, TINT["W"])
                margins(no, 0.24, 0.24, 0.05, 0.05)
                margins(body, 0.24, 0.24, 0.3, 0.05)
                run(fmt(no.paragraphs[0], spacing=1.0, align=WD_ALIGN_PARAGRAPH.CENTER), str(n), 14, COLOR["W"], bold=True)
                rich(fmt(body.paragraphs[0], spacing=1.25), item.strip(), 12)
            continue

        box = table([CONTENT_W]).rows[0].cells[0]
        shade(box, TINT[key])
        borders(box, left=(30, COLOR[key], "single"))
        margins(box, 0.25, 0.3, 0.45, 0.45)
        first = True
        for line in lines:
            if BLANK_LINE.match(line):
                answer_lines(box, LINE[key])
                continue
            p = fmt(box.paragraphs[0] if first else box.add_paragraph(), after=2, spacing=1.2)
            first = False
            if line.startswith("提示："):
                run(p, "提示　", 11, COLOR[key], bold=True)
                rich(p, line.removeprefix("提示："), 12)
            else:
                for i, option in enumerate(o.strip() for o in line.split("□") if o.strip()):
                    run(p, ("　　" if i else "") + "☐ ", 12, COLOR[key], bold=True)
                    run(p, option, 11.5)

    p = fmt(section.footer.paragraphs[0], spacing=1.0)
    tabs = p.paragraph_format.tab_stops
    # 頁尾樣式內建置中／靠右定位點（4680、9360 twips），不清掉會搶走 \t
    for pos in (4680, 9360):
        tabs.add_tab_stop(Twips(pos), WD_TAB_ALIGNMENT.CLEAR)
    tabs.add_tab_stop(Cm(CONTENT_W), WD_TAB_ALIGNMENT.RIGHT)
    run(p, f"{spec['code']}　{spec['name']}", 8, MUTED)
    run(p, "\tW 看影片記重點 → S 寫出重點觀念 → Q 留下一個想法", 8, MUTED)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 2
    source, out = Path(args[0]), Path(args[1])
    build(parse(source.read_text(encoding="utf-8")), out)
    print("saved", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
