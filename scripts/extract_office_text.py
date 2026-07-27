from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


NUMBER_RE = re.compile(r"(\d+)")


def natural_key(name: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in NUMBER_RE.split(name)]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_text(xml_bytes: bytes, text_tag: str = "t") -> str:
    root = ElementTree.fromstring(xml_bytes)
    values = [
        node.text or ""
        for node in root.iter()
        if local_name(node.tag) == text_tag and (node.text or "").strip()
    ]
    return " ".join(values).strip()


def xml_paragraphs(xml_bytes: bytes) -> list[str]:
    root = ElementTree.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for node in root.iter():
        if local_name(node.tag) != "p":
            continue
        values = [
            child.text or ""
            for child in node.iter()
            if local_name(child.tag) == "t" and (child.text or "").strip()
        ]
        text = "".join(values).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def notes_body_text(xml_bytes: bytes) -> str:
    root = ElementTree.fromstring(xml_bytes)
    found_body_placeholder = False
    paragraphs: list[str] = []
    for shape in root.iter():
        if local_name(shape.tag) != "sp":
            continue
        placeholders = [
            node
            for node in shape.iter()
            if local_name(node.tag) == "ph"
        ]
        if not any(node.attrib.get("type") == "body" for node in placeholders):
            continue
        found_body_placeholder = True
        for paragraph in shape.iter():
            if local_name(paragraph.tag) != "p":
                continue
            values = [
                node.text or ""
                for node in paragraph.iter()
                if local_name(node.tag) == "t" and (node.text or "").strip()
            ]
            text = "".join(values).strip()
            if text:
                paragraphs.append(text)
    if found_body_placeholder:
        return "\n".join(paragraphs).strip()
    # Minimal fixtures and some non-standard producers omit placeholders.
    return xml_text(xml_bytes)


def _notes_target(archive: zipfile.ZipFile, slide_name: str) -> str | None:
    slide_path = Path(slide_name)
    rels = (
        slide_path.parent
        / "_rels"
        / f"{slide_path.name}.rels"
    ).as_posix()
    if rels not in archive.namelist():
        return None
    root = ElementTree.fromstring(archive.read(rels))
    for node in root.iter():
        if node.attrib.get("Type", "").endswith("/notesSlide"):
            target = node.attrib.get("Target", "")
            number = NUMBER_RE.search(Path(target).name)
            if number:
                return f"ppt/notesSlides/notesSlide{number.group(1)}.xml"
    return None


def extract_pptx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        slide_names = sorted(
            (
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=natural_key,
        )
        slides = []
        for position, slide_name in enumerate(slide_names, start=1):
            note_name = _notes_target(archive, slide_name)
            if not note_name:
                fallback = f"ppt/notesSlides/notesSlide{position}.xml"
                note_name = fallback if fallback in names else None
            slides.append(
                {
                    "slide": position,
                    "text": xml_text(archive.read(slide_name)),
                    "notes": notes_body_text(archive.read(note_name)) if note_name else "",
                }
            )
    return {"type": "pptx", "path": str(path), "slides": slides}


def extract_docx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("DOCX is missing word/document.xml")
        paragraphs = xml_paragraphs(archive.read("word/document.xml"))
    return {"type": "docx", "path": str(path), "paragraphs": paragraphs}


def extract_office(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".pptx":
        return extract_pptx(source)
    if suffix == ".docx":
        return extract_docx(source)
    raise ValueError(f"Unsupported Office format: {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PPTX/DOCX text as JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = extract_office(args.input)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
