# 品質學習迴圈

`quality/` 讓專案能從真實教材的成功與失敗持續改善，而不把未驗證的單次經驗直接寫成規則。

## 一次審查的生命週期

1. 用 `scripts/new_review_record.py` 建立紀錄，初始判定為 `HOLD`。
2. Skill 讀取教材並附上 A–D 級證據。
3. 在 `strengths` 記錄應保留的做法，在 `findings` 記錄缺失與具體修正動作。
4. 教師覆核後填寫 `human_decision`。
5. 若同一準則重複出現問題，先建立測試，再修改共用資料或 Skill。
6. 用 `scripts/summarize_quality.py` 看趨勢；改善後保留原紀錄，不覆寫歷史。

## 判定

- `PASS`：無 blocker/major，必要證據齊全，可進下一站。
- `REVISE`：方向明確，但有可修正的 major/minor。
- `HOLD`：缺官方映射、關鍵原始檔、授權、圖文證據或人工決策。

## 儲存規則

- 本機完整紀錄可放在 `quality/records/`，預設不進 Git。
- 要提交的案例先去識別，放在 `quality/examples/`。
- `known-issues.md` 記錄套件層級限制；`confirmed-strengths.md` 記錄多次被驗證有效的設計。
- 不得把教師或學生姓名、作答紀錄、未授權全文放進公開案例。

外部審查者可從 [`REVIEWER_START_HERE.md`](../REVIEWER_START_HERE.md) 開始，
用審查工作台匯出逐頁 JSON，或使用 GitHub 的「教材／Skill 審查問題」表單。
維護者確認去識別後，再把可重現案例轉成 `quality/examples/` 與自動測試。
