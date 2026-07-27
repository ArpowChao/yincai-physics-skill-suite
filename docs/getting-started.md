# 操作手冊

本手冊分成「只參與審查」、「從 PPTX 建立審查包」與「修改專案」三種使用方式。
原始教材與每次輸出都留在本機，不上傳 GitHub。

## 1. 只參與教材審查

如果收到審查 ZIP：

1. 解壓縮到本機資料夾。
2. 雙擊 `index.html`；不需要安裝 Python、PowerPoint 或啟動伺服器。
3. 左側用「需處理」、「教學斷點」、「有影片」及「缺講稿」篩選頁面。
4. 中央切換投影片與本頁影片。
5. 右側依序查看：
   - 本頁判讀；
   - 教學鏈：問題、學生行動、預期輸出、回饋與前後銜接；
   - 九步驟、推定大概念、十項內容品質及 critical gates；
   - 老師覆核。
6. 每頁選擇 `PASS`、`REVISE` 或 `HOLD`，並記錄理由。
7. 按「匯出審查紀錄」，把產生的 JSON 交回維護者。

覆核內容只保存在瀏覽器本機儲存空間，不會自動上傳。完整審查準則見
[`REVIEWER_START_HERE.md`](../REVIEWER_START_HERE.md)。

## 2. 第一次安裝

共同需求：

- Git；
- Python 3.11 以上；

平台差異：

- Windows PowerShell 與 Microsoft PowerPoint：只有實際匯出動畫、內嵌影片、
  播放 MP4，或自動把 speaker notes 寫回 PPTX 時需要；
- Mac 可完成 GitHub 協作、Python 驗證、manifest、工作台與分享 ZIP；上述兩個
  PowerPoint 自動化步驟交給 Windows 匯出者。第一次使用請看
  [`macOS 使用指南`](macos-guide.md)。

取得 private repository 需要先由管理者加入 GitHub collaborator：

```powershell
git clone https://github.com/ArpowChao/yincai-physics-skill-suite.git
Set-Location yincai-physics-skill-suite
```

建立本機設定：

```powershell
Copy-Item config/project.example.toml config/project.toml
```

修改 `config/project.toml` 中的教材、課綱及輸出位置。這個檔案包含本機路徑，
已被 Git 忽略，不要強制加入版本控制。

確認環境正常：

```powershell
python scripts/audit_repository.py
python scripts/validate_suite.py
python -m unittest discover -s tests -v
```

三個指令都成功後才開始處理真實教材。

Mac Terminal 請把 `Copy-Item` 改成 `cp`、`Set-Location` 改成 `cd`，並優先使用
`python3`。完整可複製指令見 [`macOS 使用指南`](macos-guide.md)。

## 3. 從 PPTX 建立審查包

### 3.1 建立唯讀 manifest

```powershell
python scripts/build_pptx_review_manifest.py `
  "C:\教材\單元.pptx" `
  "outputs\review-packages\單元代碼_單元名稱" `
  --timestamp
```

實際資料夾使用本機時間命名：

```text
單元代碼_單元名稱_YYYYMMDD-HHmmss
```

例如：

```text
PBa-V.1-2-2_動能_20260727-230815
```

`--timestamp` 可以避免同一單元的新審查覆蓋舊結果。來源 PPTX 採唯讀方式處理。

### 3.2 匯出逐頁畫面與實際播放

這一步目前需要 Windows 與 Microsoft PowerPoint。Mac 使用者先完成 manifest，
再把來源 PPTX 透過已授權的安全管道交給 Windows 匯出者：

```powershell
powershell -ExecutionPolicy Bypass `
  -File scripts/export_pptx_review_assets.ps1 `
  -InputPptx "C:\教材\單元.pptx" `
  -OutputDir "outputs\review-packages\單元代碼_單元名稱_YYYYMMDD-HHmmss"
```

這一步會產生：

- `slides/`：逐頁 PNG；
- `playback.mp4`：PowerPoint 實際播放預覽；
- `export-status.json`：匯出狀態。

未錄製正式計時的簡報只能用播放 MP4 確認動畫與影片是否出現，不能把預覽長度
當成真正教學時間。

### 3.3 執行 PPT 總審查

在 Codex 中提供 PPTX、單元代碼與名稱，使用
`physics-framework-checker`。審查至少應產生：

- `review-result.json`；
- `review-report.md`；
- 九步驟覆蓋；
- 從活動反推的「推定大概念」及證據頁碼；
- 逐頁教學清冊；
- 影片角色、觀看焦點、學生輸出與後續用途；
- `PASS / REVISE / HOLD`。

單元名稱是學習目標錨點；大概念不要求在投影片明列。審查者應從活動、問題、
證據、公式與應用反推大概念，再判斷內容是否與單元名稱一致。

### 3.4 建立離線工作台

```powershell
python scripts/build_review_workbench.py `
  "outputs\review-packages\單元代碼_單元名稱_YYYYMMDD-HHmmss"
```

開啟生成的 `review-workbench.html`，進行人工覆核。

### 3.5 補寫 speaker notes

只有使用者要求修改時才建立新 PPTX；不覆寫來源。以下自動寫回工具目前需要
Windows 與 Microsoft PowerPoint；Mac 可先產生 `speaker-notes.json` 再交付：

```powershell
powershell -ExecutionPolicy Bypass `
  -File scripts/apply_pptx_notes.ps1 `
  -InputPptx "C:\教材\單元.pptx" `
  -NotesJson "outputs\review-packages\單元\speaker-notes.json" `
  -OutputPptx "outputs\review-packages\單元\單元_自學講稿版.pptx"
```

完成後重新建立 manifest、逐頁 PNG 與播放 MP4，確認 notes、動畫及影片未被破壞。

## 4. 建立給別人的分享 ZIP

先確認投影片、圖片及影片有權提供給指定審查者，再執行：

```powershell
python scripts/build_review_share_bundle.py `
  "outputs\review-packages\單元代碼_單元名稱_YYYYMMDD-HHmmss" `
  "outputs\share-bundles\單元代碼_單元名稱_YYYYMMDD-HHmmss" `
  --confirm-authorized `
  --zip
```

分享工具會排除原始 PPTX、教師姓名檔名、轉錄資料與未引用媒體，但授權確認仍由
分享者負責。ZIP 是交付物，不加入 Git。

## 5. 哪些內容不會上傳 GitHub

以下內容預設由 `.gitignore` 排除：

- `outputs/`；
- `local-data/`；
- `archive/` 的本機內容；
- `config/project.toml`；
- PPTX、DOCX、PDF、XLSX、影片壓縮包；
- `quality/records/` 的真實審查紀錄。

提交前確認：

```powershell
git status --short
git ls-files outputs
```

第二個指令應沒有輸出。

## 6. 更新到最新版

沒有本機修改時：

```powershell
git switch main
git pull --ff-only
python scripts/validate_suite.py
python -m unittest discover -s tests -v
```

要修改規則或 Skill 時，不直接在 `main` 工作；依
[`collaboration-workflow.md`](collaboration-workflow.md) 建立 issue、分支及 PR。

## 7. 常見問題

### 課綱碼無法解析

維持 `HOLD`，不要用相似代碼猜測。把缺少的官方對照建立 issue，附正式來源。

### 投影片只有圖片或影片無法播放

不要判定圖文或影片正確。先由 PowerPoint 匯出逐頁畫面與播放 MP4；仍看不到時
記為 `not_observable` 或 `HOLD`。

### 工作台顯示舊結果

確認開啟的是資料夾尾端時間最新的 `review-workbench.html`。修改
`review-result.json` 後必須重新執行 `build_review_workbench.py`。

### Git 顯示 outputs

一般情況 `outputs/` 只會出現在 `git status --ignored`，不會出現在一般
`git status`。若曾被誤加入索引，不要提交，請先通知維護者處理。
