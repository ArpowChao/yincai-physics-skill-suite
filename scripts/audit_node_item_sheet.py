"""檢查任務單 docx 的題目長度、標點、單位空格、答案分布與正解長度（yincai-physics-node-items 使用）。

用法：
  python scripts/audit_node_item_sheet.py outputs/節點_P4_MMDD_練習題.docx outputs/節點_P4_MMDD_診斷題.docx

需要 python-docx。出現 ⚠ 的項目須處理；「極端字眼」只出現在題幹或詳解時可保留。
同一份任務單的 _練習題、_診斷題 一起給時，答案分布以兩份合計的 4 題判斷。
"""
import re, sys
from docx import Document
pairs = {}
for path in sys.argv[1:]:
    d = Document(path); print("##", path.split("/")[-1])
    qt = [t for t in d.tables if any(r.cells[0].text.strip() == "題目：" for r in t.rows)][1:]
    answers = []
    for i, t in enumerate(qt, 1):
        f = {r.cells[0].text.strip(): r.cells[-1].text.strip() for r in t.rows}
        opts = {k: f.get(f"（{k}）", "") for k in "ABCD"}
        ans = re.sub(r"[（）\s]", "", f.get("答案：", "")); answers.append(ans)
        n = lambda s: len(re.sub(r"\s", "", s))
        warn = []
        if n(f["題目："]) > 90 and "（甲）" not in f["題目："]: warn.append(f"題幹{n(f['題目：'])}字")
        if not f["題目："].endswith(("？", "。")): warn.append("題幹結尾不是？或。")
        L = {k: n(v) for k, v in opts.items()}
        if ans in L and L[ans] == max(L.values()) and max(L.values()) - sorted(L.values())[-2] >= 3: warn.append("正解明顯最長")
        if max(L.values()) - min(L.values()) > 12: warn.append(f"選項長度差{max(L.values())-min(L.values())}")
        for k, v in opts.items():
            if re.search(r"[，；]", v) and not v.endswith("。"): warn.append(f"({k})句子未以。結尾")
        if n(f["詳解："]) > 170: warn.append(f"詳解{n(f['詳解：'])}字")
        allt = "\n".join(f.values())
        for pat, msg in [(r"[一-鿿][,?!;:()]|[,?!;:()][一-鿿]|—", "半形標點或破折號"),
                         (r"(?:℃|m/s|m/s²|\bkg|\bW|\bN|\bJ|\bV|\bA|\bm) [一-鿿，。]|[A-Za-z²³℃Ω] [，。、；：？！）]", "單位後有空格"),
                         (r"完全|絕對|必定|永遠|任何", "極端字眼(檢查是否在誘答)")]:
            hits = re.findall(pat, allt)
            if hits: warn.append(f"{msg}{hits[:3]}")
        print(f"  Q{i} 題幹{n(f['題目：'])} 選項{list(L.values())} 詳解{n(f['詳解：'])} 答{ans}", "⚠ " + "；".join(warn) if warn else "OK")
    stem = re.sub(r"_(練習題|診斷題)\.docx$", "", path)
    if stem != path:
        pairs.setdefault(stem, []).extend(answers); print("  答案", answers); continue
    if len(set(answers)) < len(answers) - 1: print("  ⚠ 答案分布過度集中", answers)
    else: print("  答案", answers)
for stem, answers in pairs.items():
    print("##", stem.split("/")[-1], "（練習題＋診斷題）")
    if len(set(answers)) < len(answers) - 1: print("  ⚠ 答案分布過度集中", answers)
    else: print("  答案", answers)
