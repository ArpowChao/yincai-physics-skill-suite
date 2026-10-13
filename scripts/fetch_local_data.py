"""下載公開官方來源到 local-data/sources/（只用標準函式庫）。

repo 不收課綱與學測原檔；清單在 data/sources/official-downloads.json。
換電腦或給別人使用時，執行一次即可取得 yincai-physics-node-items 需要的檔案。

用法：
  python scripts/fetch_local_data.py                 # 下載全部（已存在的檔案略過）
  python scripts/fetch_local_data.py --group gsat    # 只下載學測自然試題與答案
  python scripts/fetch_local_data.py --dry-run       # 只列出會下載什麼
  python scripts/fetch_local_data.py --force         # 已存在也重新下載

下載後：
  python scripts/gsat_sources.py extract local-data/sources/gsat local-data/gsat-text

課本章節與 Bloom 論文不在下載清單內，需自行放入（見 local-data/README.md）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "sources" / "official-downloads.json"
DEFAULT_DEST = ROOT / "local-data" / "sources"
USER_AGENT = "Mozilla/5.0 (yincai-physics-skill-suite fetch_local_data)"


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def select(files: list[dict], group: str) -> list[dict]:
    return [f for f in files if group == "all" or f["group"] == group]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_pdf(data: bytes) -> bool:
    """官方網站出錯時常回傳 HTML 頁面；只接受真正的 PDF。"""
    return data[:5] == b"%PDF-"


def download(url: str, timeout: int = 60, retries: int = 2) -> bytes:
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # 網路錯誤：稍候重試
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"下載失敗：{last}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--group", choices=["all", "gsat", "curriculum"], default="all")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    files = select(load_manifest()["files"], args.group)
    ok = skipped = differ = failed = planned = 0
    for entry in files:
        target = args.dest / entry["target"]
        if target.exists() and not args.force:
            print(f"略過（已存在）：{target.relative_to(args.dest)}")
            skipped += 1
            continue
        if args.dry_run:
            print(f"將下載：{entry['title']} → {target.relative_to(args.dest)}")
            planned += 1
            continue
        try:
            data = download(entry["url"])
        except RuntimeError as exc:
            print(f"✗ {entry['id']}：{exc}")
            failed += 1
            continue
        if not check_pdf(data):
            print(f"✗ {entry['id']}：回傳內容不是 PDF，官方網址可能已更換（{entry['url']}）")
            failed += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        ok += 1
        mark = "✓"
        if entry.get("reference_sha256") and sha256(data) != entry["reference_sha256"]:
            mark = "⚠"
            differ += 1
        print(f"{mark} {target.relative_to(args.dest)}（{len(data) // 1024} KB）")

    if args.dry_run:
        print(f"\n試算：將下載 {planned}、略過 {skipped}。")
        return 0
    print(f"\n完成：下載 {ok}、略過 {skipped}、失敗 {failed}。")
    if differ:
        print(f"⚠ 有 {differ} 個檔案與建立清單時的副本不同：官方可能換過檔案，可使用，但引用題號與答案前請人工確認。")
    if failed:
        print("失敗的檔案可到官方索引頁手動下載，存成清單中的 target 檔名：")
        for name, url in load_manifest()["index_pages"].items():
            print(f"  {name}: {url}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
