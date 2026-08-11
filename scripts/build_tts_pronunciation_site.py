from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_SOURCE = ROOT / "showcase" / "tts-pronunciation"
DATA_SOURCE = ROOT / "data" / "tts-pronunciation"


def build(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name in (
        "index.html",
        "sources.html",
        "styles.css",
        "moe-heteronyms.js",
        "cross-strait-candidates.js",
        "app.js",
    ):
        shutil.copy2(SITE_SOURCE / name, output / name)
    data_output = output / "data"
    data_output.mkdir(parents=True, exist_ok=True)
    for name in ("verified.json", "formulas.json", "submission.json"):
        shutil.copy2(DATA_SOURCE / name, data_output / name)
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the static TTS review site.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve())
    print(f"Static TTS review site built at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
