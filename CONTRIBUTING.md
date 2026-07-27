# 貢獻指南

## 修改原則

1. 先描述教師負擔、失敗案例或想保留的優點，不以「讓提示詞更長」當作目標。
2. 課綱結論必須指向 A 級證據；LLM-wiki 與舊教材只提供候選概念。
3. 可跨 Skill 共用的規則放在 `data/`、`references/` 或 `scripts/`，不要複製到 10 份 `SKILL.md`。
4. `SKILL.md` 必須包含 Inputs、Workflow、Output contract、Stop conditions、Common mistakes。
5. 不提交原始教師教材、學生資料、本機絕對路徑或含姓名的索引。

## 開發流程

1. 在 issue 或品質紀錄附上最小重現案例。
2. 先新增會重現問題的測試。
3. 修改最小範圍的規則、資料或 Skill。
4. 執行：

   ```powershell
   python scripts/validate_suite.py
   python -m unittest discover -s tests -v
   ```

5. 以一組真實但不提交原始檔的教材乾跑，記錄「保留優點」與「待修缺失」。
6. Pull request 說明影響哪些 Skills、資料版本、相容性與人工覆核結果。

## Skill 版本

- `PATCH`：措辭、範例或不改輸出契約的小修正。
- `MINOR`：增加規則、欄位或向後相容能力。
- `MAJOR`：改變輸入、輸出契約或判定語意。

品質紀錄中的 `skill_version` 必須對應執行時版本。正式發布時以 Git tag 標記整套版本。

## 新增課綱或知識資料

- 保留來源名稱、頁碼、擷取日期與適用範圍。
- 區分官方課綱代碼與專案拆分代碼。
- 無法映射至官方母節點時必須 `HOLD`。
- 任何高於課綱的補充內容都應標為延伸，且不得成為必要作答前提。

## Pull request 檢查表

- [ ] 沒有本機絕對路徑、個資或未授權教材。
- [ ] 15 項以上自動測試通過。
- [ ] 所有 Skill metadata 可解析且預設提示含 `$skill-name`。
- [ ] 課綱與事實結論有證據等級及來源。
- [ ] 紀錄了表現良好之處，不只列缺失。
- [ ] 有 `PASS / REVISE / HOLD` 與停止條件。
