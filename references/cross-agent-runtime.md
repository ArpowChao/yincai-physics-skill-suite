# 跨 Agent 執行契約

本檔是 Codex、Gemini CLI 與其他可讀取 repository 的 Agent 共用入口。

## 開始前

1. 從 repository 根目錄工作。
2. 找到 `.agents/skills/`，依任務讀取並啟用對應 `SKILL.md`。
3. PPT 內容總審查使用 `physics-framework-checker`。
   `physics-framework-9step` 是已知的舊一頁式架構 Skill，不得用於內容型 PPT
   審查；即使它存在於使用者全域目錄或舊對話快取，也要停用。
4. 先用 `python scripts/resolve_curriculum.py <單元代碼>` 取得 repo 內課綱與
   專案節點；不得只靠模型記憶判定超綱。
5. 產生 `review-result.json` 後，必須執行：

   ```text
   python scripts/check_skill_conflicts.py --task content-deck-review
   python scripts/validate_review_policy.py <review-result.json>
   ```

6. 只有政策檢查通過，才可建立 `review-workbench.html`。

## S1／S2 不可違反的判讀

- 單元名稱是學習目標錨點。未另列行為動詞式目標句，本身不是缺失。
- 從跨頁活動、問題、證據、公式、學生任務、回饋及應用推定大概念，並列出
  證據頁碼。
- 未顯示「大概念」標題、專頁或字樣，本身不是缺失，不得因此扣分、降級 S2，
  或要求新增／標明大概念。
- 應檢查的是推定大概念與單元名稱及跨頁內容是否一致。若無法反推或跨頁矛盾，
  應以證據指出「主線不清」或「內容不一致」，不能改寫成「缺大概念標籤」。

## Gemini CLI 自我檢查

開始審查前執行 `/skills list`，確認 `physics-framework-checker` 在清單中；
用 `/memory show` 確認本專案 `GEMINI.md` 已載入。剛更新 repository 時執行
`/skills reload` 與 `/memory reload`。若 workspace 尚未信任，先完成 `/trust`
後重新啟動 Gemini CLI。

Skill 未出現在清單、專案記憶未載入、課綱代碼無法解析，或 PPT 影音無法觀察時，
停止並回報 `HOLD`；不要用通用提示詞猜測結果。

若 `/skills list` 仍顯示 `physics-framework-9step`，不要在內容審查中批准它；
重新載入後仍被自動觸發時，開新對話並明確指定只使用 workspace 的
`physics-framework-checker`。
