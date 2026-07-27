from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from extract_office_text import extract_pptx


NUMBER_RE = re.compile(r"(\d+)")


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in NUMBER_RE.split(value)]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def timestamped_output_dir(
    output_dir: Path,
    now: datetime | None = None,
) -> Path:
    timestamp = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
    return output_dir.with_name(f"{output_dir.name}_{timestamp}")


def relationship_kind(type_uri: str) -> str:
    return type_uri.rstrip("/").rsplit("/", 1)[-1]


def relationship_records(
    archive: zipfile.ZipFile,
    slide_name: str,
) -> list[dict[str, Any]]:
    slide_path = Path(slide_name)
    rels_name = (
        slide_path.parent / "_rels" / f"{slide_path.name}.rels"
    ).as_posix()
    if rels_name not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read(rels_name))
    records: list[dict[str, Any]] = []
    for node in root.iter():
        if not node.tag.endswith("Relationship"):
            continue
        target = node.attrib.get("Target", "")
        target_mode = node.attrib.get("TargetMode", "Internal")
        type_uri = node.attrib.get("Type", "")
        record: dict[str, Any] = {
            "relationship_id": node.attrib.get("Id"),
            "kind": relationship_kind(type_uri),
            "target_mode": target_mode,
            "target": target,
        }
        if target_mode != "External":
            archive_path = posixpath.normpath(
                posixpath.join(posixpath.dirname(slide_name), target)
            )
            record["archive_path"] = archive_path
            if archive_path in archive.namelist():
                payload = archive.read(archive_path)
                record["size_bytes"] = len(payload)
                record["sha256"] = sha256_bytes(payload)
        records.append(record)
    return records


def build_manifest(source: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    extracted = extract_pptx(source)

    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        slide_names = sorted(
            (
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=natural_key,
        )
        media_names = sorted(
            (
                name
                for name in names
                if name.startswith("ppt/media/") and not name.endswith("/")
            ),
            key=natural_key,
        )
        media: list[dict[str, Any]] = []
        for archive_path in media_names:
            payload = archive.read(archive_path)
            target = media_dir / Path(archive_path).name
            target.write_bytes(payload)
            media.append(
                {
                    "archive_path": archive_path,
                    "extracted_path": target.relative_to(output_dir).as_posix(),
                    "extension": target.suffix.lower(),
                    "size_bytes": len(payload),
                    "sha256": sha256_bytes(payload),
                }
            )

        slides: list[dict[str, Any]] = []
        for index, slide_name in enumerate(slide_names, start=1):
            content = extracted["slides"][index - 1]
            slides.append(
                {
                    "slide": index,
                    "text": content["text"],
                    "notes": content["notes"],
                    "relationships": relationship_records(archive, slide_name),
                }
            )

    return {
        "manifest_version": "1.0",
        "source_filename": source.name,
        "source_size_bytes": source.stat().st_size,
        "source_sha256": sha256_file(source),
        "slide_count": len(slides),
        "slides_with_notes": sum(bool(slide["notes"].strip()) for slide in slides),
        "media_count": len(media),
        "media": media,
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract a PPTX review manifest and embedded media."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Append local time as YYYYMMDD-HHmmss and refuse an existing target.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    if args.timestamp:
        output_dir = timestamped_output_dir(output_dir)
        if output_dir.exists():
            parser.error(f"timestamped output already exists: {output_dir}")
    manifest = build_manifest(args.input.resolve(), output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "manifest": str(manifest_path.resolve()),
                "output_dir": str(output_dir.resolve()),
                "slides": manifest["slide_count"],
                "media": manifest["media_count"],
                "slides_with_notes": manifest["slides_with_notes"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
