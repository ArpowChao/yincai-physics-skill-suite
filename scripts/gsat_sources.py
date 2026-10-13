"""學測母題查詢工具（yincai-physics-node-items 使用）。

用法：
  python scripts/fetch_local_data.py --group gsat   # 先下載官方 PDF（沒有 .7z 時）
  python scripts/gsat_sources.py extract <學測.7z 或 PDF 資料夾> local-data/gsat-text
  例如：python scripts/gsat_sources.py extract local-data/sources/gsat local-data/gsat-text
  python scripts/gsat_sources.py search  local-data/gsat-text 關鍵字1 [關鍵字2 ...]
  python scripts/gsat_sources.py show    local-data/gsat-text <年> <題號>

extract 需要 pymupdf；來源為 .7z 時另需 py7zr。原題 PDF 與抽出的文字只放在
local-data/，不得提交到 repo。題目含分式、上標或圖時，文字會失真，須另看 PDF 頁面。
"""
import glob, os, re, sys
cmd = sys.argv[1]
if cmd == "extract":
    src, out = sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    if src.endswith(".7z"):
        import py7zr
        raw = out + "_raw"; os.makedirs(raw, exist_ok=True)
        with py7zr.SevenZipFile(src) as a:
            a.extractall(path=raw)
        src = raw
    import pymupdf
    for p in sorted(glob.glob(os.path.join(src, "**", "*.pdf"), recursive=True)):
        if os.path.islink(p): continue
        t = "\n".join(pg.get_text() for pg in pymupdf.open(p))
        open(os.path.join(out, os.path.basename(p)[:-4] + ".txt"), "w", encoding="utf-8").write(t)
    print("extracted to", out, len(os.listdir(out)), "files")
    sys.exit()

D = sys.argv[2]
def questions(year):
    f = glob.glob(os.path.join(D, f"{year}*試題*.txt"))
    if not f: return {}
    t = open(f[0], encoding="utf-8").read()
    starts = [(int(m.group(1)), m.start()) for m in re.finditer(r"(?m)^\s*(\d{1,2})\s*[\.．]\s", t)]
    qs, last = {}, 0
    for i, (n, s) in enumerate(starts):
        if n < last - 5:  # 跳過頁碼等雜訊
            continue
        e = starts[i + 1][1] if i + 1 < len(starts) else s + 2500
        qs.setdefault(n, re.sub(r"\s*\n\s*", "", t[s:e]))
        last = n
    return qs
def answer(year, n):
    f = glob.glob(os.path.join(D, f"{year}*答案*.txt"))
    if not f: return "?"
    a = re.sub(r"\s+", " ", open(f[0], encoding="utf-8").read())
    m = re.search(rf"(?<!\d){n} ([A-J]+(?: 或[A-J]+)?)", a)
    return m.group(1) if m else "?(非選擇題或格式不符)"
years = sorted({re.match(r"(\d+)", os.path.basename(f)).group(1) for f in glob.glob(os.path.join(D, "*試題*.txt"))})
if cmd == "search":
    kws = sys.argv[3:]
    for y in years:
        for n, q in questions(y).items():
            if any(k in q for k in kws):
                print(f"{y}-{n} [{answer(y, n)}] {q[:90]}")
elif cmd == "show":
    y, n = sys.argv[3], int(sys.argv[4])
    q = questions(y).get(n)
    print(q[:3000] if q else "找不到此題（可能在題組說明內，請改用 search 找題組前言）")
    print("官方答案：", answer(y, n))
