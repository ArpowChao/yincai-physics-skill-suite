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

## 新需求與迭代決策閘門

當使用者提出可能影響其他單元、其他使用者或未來輸出契約的新要求時，不得默認把
單次對話直接寫成永久規則。完成不具破壞性的當次工作後，主動追問使用者要採哪一種處理：

1. **只套用本次**：不修改共用 Skill、資料或測試。
2. **記為候選需求**：寫入本機品質紀錄，保留案例與理由；累積更多證據後再決定是否升級。
3. **納入共通規則**：建立去識別的最小重現案例或品質紀錄，先補測試，再更新共用資料、
   對應 Skill、版本與 Changelog。

以下情況不必重複追問：

- 使用者已明確說「只改這次」、「記錄候選」或「更新 Skill／納入迭代」。
- 只是拼字、格式或單一教材內容修正，不會改變共用判定。
- 新要求涉及個資、未授權內容或與正式證據衝突；此時停止永久化並說明限制。

追問時要摘要準備永久化的規則與可能影響哪些 Skill／輸出。未取得選擇前，可以完成
當次產出，但不得自行把候選需求升級成共通規則。

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
