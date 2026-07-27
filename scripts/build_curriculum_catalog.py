from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CODE_RE = re.compile(r"(P[A-Za-z]{2})-[ⅤV]([ac])-(\d+)")
OFFICIAL_DOCUMENT = "十二年國民基本教育課程綱要國民中小學暨普通型高級中等學校─自然科學領域"
CATALOG_PAGES = {
    "mandatory": range(38, 41),
    "advanced-elective": range(49, 53),
}
NOTE_PAGES = {
    "mandatory": range(186, 192),
    "advanced-elective": range(194, 203),
}


def compact(text: str) -> str:
    normalized = " ".join(
        (text or "")
        .replace("力", "力")
        .replace("度", "度")
        .replace("行", "行")
        .replace("類", "類")
        .replace("論", "論")
        .split()
    )
    return re.sub(
        r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])",
        "",
        normalized,
    )


def canonical(match: re.Match[str]) -> str:
    family, track, number = match.groups()
    family = family[0].upper() + family[1].upper() + family[2].lower()
    return f"{family}-V{track}-{number}"


def extract_segments(text: str) -> list[tuple[str, str]]:
    normalized = compact(text)
    matches = list(CODE_RE.finditer(normalized))
    segments = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        statement = normalized[match.end() : end].strip(" ：:;；")
        segments.append((canonical(match), statement))
    return segments


def build_catalog(pdf_path: Path) -> dict[str, Any]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError(
            "pdfplumber is required only when rebuilding the committed curriculum catalog"
        ) from exc

    entries: dict[str, dict[str, Any]] = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        for track, pages in CATALOG_PAGES.items():
            for page_number in pages:
                for table in pdf.pages[page_number - 1].extract_tables():
                    for row in table[1:]:
                        for cell in row:
                            for code, statement in extract_segments(cell or ""):
                                if not code.startswith("P"):
                                    continue
                                current = entries.get(code)
                                if current is None or len(statement) > len(current["statement"]):
                                    entries[code] = {
                                        "code": code,
                                        "track": track,
                                        "statement": statement,
                                        "teaching_note": "詳見官方課綱學習內容說明。",
                                        "source": {
                                            "document": OFFICIAL_DOCUMENT,
                                            "pdf_page": page_number,
                                        },
                                    }

        for track, pages in NOTE_PAGES.items():
            previous_codes: list[str] = []
            for page_number in pages:
                for table in pdf.pages[page_number - 1].extract_tables():
                    for row in table[1:]:
                        if len(row) < 4:
                            continue
                        content_cell = row[2] or ""
                        note = compact(row[3] or "")
                        if not note:
                            continue
                        codes = [code for code, _ in extract_segments(content_cell)]
                        if codes:
                            previous_codes = codes
                        elif previous_codes:
                            # A learning-content explanation can continue on the next
                            # PDF page with an empty learning-content cell.
                            codes = previous_codes
                        for code in codes:
                            if code in entries and entries[code]["track"] == track:
                                current = entries[code]["teaching_note"]
                                if current == "詳見官方課綱學習內容說明。":
                                    entries[code]["teaching_note"] = note
                                    entries[code]["teaching_note_source_page"] = page_number
                                    entries[code]["teaching_note_source_pages"] = [page_number]
                                elif note not in current:
                                    entries[code]["teaching_note"] = f"{current} {note}"
                                    source_pages = entries[code].setdefault(
                                        "teaching_note_source_pages",
                                        [entries[code]["teaching_note_source_page"]],
                                    )
                                    if page_number not in source_pages:
                                        source_pages.append(page_number)

    return {
        "catalog_version": "1.0.0",
        "generated_from": OFFICIAL_DOCUMENT,
        "scope": "Taiwan Stage 5 physics mandatory and advanced-elective learning content",
        "code_note": (
            "Official codes end at the first numeric segment. Additional numeric segments "
            "in project filenames are local learning-node codes."
        ),
        "entries": dict(sorted(entries.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 5 physics curriculum JSON.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    catalog = build_catalog(args.pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"entries": len(catalog["entries"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
