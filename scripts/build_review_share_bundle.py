from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_review_workbench import build_html, build_workbench_data


REQUIRED_FILES = {
    "manifest.json",
    "review-result.json",
    "review-report.md",
}
OPTIONAL_PUBLIC_FILES = {
    "playback.mp4",
    "slides-contact-sheet.png",
    "video-contact-sheet.png",
}
FORBIDDEN_BUNDLE_SUFFIXES = {
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".pdf",
    ".7z",
    ".zip",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_share_bundle(
    package_dir: Path,
    output_dir: Path,
    *,
    include_playback: bool = True,
) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    output_dir = output_dir.resolve()
    missing = sorted(
        name for name in REQUIRED_FILES if not (package_dir / name).is_file()
    )
    if missing:
        raise FileNotFoundError(f"Review package is missing: {', '.join(missing)}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    data = build_workbench_data(package_dir)
    data["source_filename"] = ""
    (output_dir / "review-workbench.html").write_text(
        build_html(data),
        encoding="utf-8",
    )
    copy_file(package_dir / "review-report.md", output_dir / "review-report.md")
    copy_file(
        package_dir / "review-result.json",
        output_dir / "review-result.json",
    )

    for slide in data["slides"]:
        relative = Path(slide["image"])
        copy_file(package_dir / relative, output_dir / relative)
    for slide in data["slides"]:
        for media in slide["media"]:
            relative = Path(media["path"])
            copy_file(package_dir / relative, output_dir / relative)

    for name in OPTIONAL_PUBLIC_FILES:
        if name == "playback.mp4" and not include_playback:
            continue
        source = package_dir / name
        if source.is_file():
            copy_file(source, output_dir / name)

    readme = f"""# {data['unit_code']} {data['unit_title']} 外部審查包

1. 開啟 `review-workbench.html`。
2. 逐頁檢查投影片、影片關聯、九步驟與 AI 建議。
3. 在「老師覆核」記錄 `PASS / REVISE / HOLD` 與理由。
4. 按「匯出審查紀錄」，將 JSON 交回維護者。

本分享包不含原始 PPTX、教師姓名檔名、完整教材庫或自動轉錄原始資料。
內容仍可能包含受授權限制的頁面與影片，只能依提供者核定範圍使用。
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    forbidden = [
        path.relative_to(output_dir).as_posix()
        for path in files
        if path.suffix.lower() in FORBIDDEN_BUNDLE_SUFFIXES
    ]
    if forbidden:
        raise ValueError(f"Forbidden files entered share bundle: {forbidden}")
    manifest = {
        "bundle_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit_code": data["unit_code"],
        "unit_title": data["unit_title"],
        "decision": data["decision"],
        "includes_playback": (output_dir / "playback.mp4").is_file(),
        "files": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }
    (output_dir / "bundle-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a privacy-minimized directory for external review."
    )
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--confirm-authorized",
        action="store_true",
        help="Confirm that sharing the rendered slides and referenced videos is authorized.",
    )
    parser.add_argument(
        "--without-playback",
        action="store_true",
        help="Exclude the full playback MP4.",
    )
    args = parser.parse_args()
    if not args.confirm_authorized:
        print(
            "Stopped: confirm permission to share rendered slides and referenced "
            "videos with --confirm-authorized.",
            file=sys.stderr,
        )
        return 2
    manifest = build_share_bundle(
        args.package_dir,
        args.output_dir,
        include_playback=not args.without_playback,
    )
    print(
        json.dumps(
            {
                "bundle": str(args.output_dir.resolve()),
                "unit_code": manifest["unit_code"],
                "files": len(manifest["files"]) + 1,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
