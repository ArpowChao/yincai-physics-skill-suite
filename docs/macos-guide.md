# macOS 使用指南

Mac 使用者可以審查教材、複製 private repository、修改 Skill、執行 Python
工具、建立離線工作台與分享 ZIP。只有依賴 Windows PowerPoint 自動化的兩個步驟，
需要交給指定的 Windows 匯出者處理。

## 先選擇你的工作方式

| 要做的事 | Mac 能否完成 | 最簡單的方法 |
|---|---:|---|
| 審查別人提供的 ZIP | 可以 | 解壓縮後開啟 `index.html` |
| 共同維護 GitHub 專案 | 可以 | GitHub Desktop，不必先學終端機 |
| 執行 Skill、驗證與 PPTX manifest | 可以 | Codex／其他 Agent 搭配 Python 3.11+ |
| 建立離線審查工作台與分享 ZIP | 可以 | 執行跨平台 Python 工具 |
| 以 PowerPoint 引擎匯出逐頁 PNG／播放 MP4 | 專案目前不支援 | 交給 Windows 匯出者 |
| 自動把 speaker notes 寫回 PPTX | 專案目前不支援 | Mac 產生 notes JSON，Windows 匯出者寫回 |

「專案目前不支援」是指現有自動化腳本依賴 Windows PowerShell 與 PowerPoint
COM，不代表 Mac 不能開啟或人工編輯 PowerPoint。

## 只要審查教材，不需要 GitHub

1. 下載對方提供的審查 ZIP。
2. 完整解壓縮，不要直接在 ZIP 預覽。
3. 雙擊 `index.html`。
4. 逐頁覆核後按「匯出審查紀錄」。
5. 把下載的 JSON 交回維護者。

這個流程不需要 Python、PowerPoint、GitHub 帳號或網路連線。若瀏覽器阻擋影片
自動播放，請在頁面中手動按播放；不要因此判定影片不存在。

## 第一次加入 GitHub：不使用終端機

### 1. 接受邀請

管理者會把 GitHub 邀請寄到你的帳號或信箱。請先登入正確的 GitHub 帳號並按
`Accept invitation`。只有收到 Gmail 通知，不等於已經接受 repository 邀請。

### 2. 用 GitHub Desktop 複製專案

1. 安裝並開啟 GitHub Desktop。
2. 使用剛才接受邀請的 GitHub 帳號登入。
3. 選 `File → Clone Repository`。
4. 在 GitHub.com 頁籤選
   `ArpowChao/yincai-physics-skill-suite`。
5. 選擇 Mac 上的本機資料夾，再按 `Clone`。

如果清單沒有顯示 repository，先確認邀請已接受、登入帳號正確，再按
`File → Clone Repository → URL`，貼上：

```text
https://github.com/ArpowChao/yincai-physics-skill-suite.git
```

### 3. 交給 AI Agent 協助

在 Codex 或其他能讀取本機專案的 Agent 中開啟剛複製的資料夾，然後可以直接說：

> 請先閱讀 AGENTS.md、README.md 與 docs/macos-guide.md。不要上傳 outputs、
> local-data 或教材原檔。先建立分支，再依 issue 修改、執行完整測試並建立 PR。

Agent 不需要額外「串接 GitHub」才能讀寫本機檔案；但要 push 或建立 PR，Mac
上的 GitHub Desktop／Git 必須已用有權限的帳號登入。接受邀請與登入仍由本人完成。

## 使用 Terminal 的跨平台流程

已熟悉終端機的人可使用：

```bash
git clone https://github.com/ArpowChao/yincai-physics-skill-suite.git
cd yincai-physics-skill-suite
cp config/project.example.toml config/project.toml
python3 scripts/audit_repository.py
python3 scripts/validate_suite.py
python3 -m unittest discover -s tests -v
```

如果 `python3 --version` 低於 3.11，先更新 Python。`config/project.toml` 只放
本機路徑，不要加入 Git。

## 在 Mac 建立 PPTX 審查資料

先抽取逐頁文字、speaker notes、圖片、內嵌媒體關係與頁面對應：

```bash
python3 scripts/build_pptx_review_manifest.py \
  "/Users/你的帳號/Documents/單元.pptx" \
  "outputs/review-packages/單元代碼_單元名稱" \
  --timestamp
```

完成 AI 審查並產生 `review-result.json` 後，可建立離線工作台：

```bash
python3 scripts/build_review_workbench.py \
  "outputs/review-packages/單元代碼_單元名稱_YYYYMMDD-HHmmss"
```

確認素材授權後，可建立分享 ZIP：

```bash
python3 scripts/build_review_share_bundle.py \
  "outputs/review-packages/單元代碼_單元名稱_YYYYMMDD-HHmmss" \
  "outputs/share-bundles/單元代碼_單元名稱_YYYYMMDD-HHmmss" \
  --confirm-authorized \
  --zip
```

這些 Python 工具不會修改來源 PPTX。`outputs/` 預設不進 Git。

## 何時交給 Windows 匯出者

遇到以下任一情況，就需要 Windows 電腦實際開啟 PowerPoint：

- 要確認動畫、觸發順序或內嵌影片是否真的在簡報播放時出現；
- 要取得 PowerPoint 實際播放的 `playback.mp4`；
- 要把 `speaker-notes.json` 自動寫回新的 PPTX；
- 要驗證寫回 notes 後沒有破壞版面、動畫或影片。

建議分工：

1. Mac 使用者完成 manifest、AI 審查、人工意見或 `speaker-notes.json`。
2. 透過已授權的安全管道把來源 PPTX 與指定輸出資料夾交給 Windows 匯出者。
3. Windows 匯出者執行
   `scripts/export_pptx_review_assets.ps1` 或
   `scripts/apply_pptx_notes.ps1`。
4. 匯出者回傳審查 ZIP 或新 PPTX，不把教材放進 GitHub。
5. Mac 使用者在工作台完成內容覆核。

沒有 PowerPoint 實際匯出證據時，影片／動畫欄位應標記 `not_observable` 或
`HOLD`，不可只根據檔名或縮圖判定通過。

## 用 GitHub Desktop 提交修改

0. **先按左上角 `Fetch origin`，再按 `Pull origin`（若有）。** 從過期的 `main`
   開分支是衝突的主要來源，這一步不能跳過。
1. 在 GitHub Desktop 選 `Branch → New Branch`，名稱使用
   `docs/`、`fix/`、`feat/`、`data/` 或 `test/` 前綴。確認 based on 是 `main`。
2. 在 Agent 或編輯器完成修改。
3. 執行驗證，確認沒有把 `outputs/`、`local-data/` 或教材原檔加入。
4. 回到 GitHub Desktop，檢查 Changes 清單。
5. 填寫 Summary，按 `Commit to ...`。
6. 按 `Publish branch`。
7. 按 `Create Pull Request`，在 GitHub 網頁填寫問題、證據與測試結果。
8. 等 GitHub Actions 通過及人工 review 後再合併。

不要直接修改或 push `main`。完整規則見
[`collaboration-workflow.md`](collaboration-workflow.md)。

## 常見問題

### PR 出現「This branch has conflicts」

代表你和別人改到同一行。GitHub Desktop 的處理方式：

1. 選 `Branch → Update from main`（會先自動 Fetch）。
2. 出現衝突清單時，按 `Open in editor`。
3. 刪掉 `<<<<<<<`、`=======`、`>>>>>>>` 三行標記，留下最終要的內容；
   兩邊都該保留時就兩段都留。
4. 存檔回到 GitHub Desktop，按 `Continue merge`。
5. **重跑一次驗證指令**，因為你的修改剛被套到別人的新程式上。
6. 按 `Push origin`。

`.pptx`、`.docx`、圖片與影片無法逐行合併，只能整份二選一——這也是它們不進
版控的原因之一。完整說明與 Terminal 指令見
[`collaboration-workflow.md §4.7`](collaboration-workflow.md#47-與別人的修改整併)。

### 收到邀請但還是看不到 repository

確認三件事：邀請已按接受、GitHub Desktop 登入同一個帳號、repository 仍為
private 且你的 collaborator 權限未被移除。

### `python` 指令找不到

Mac 通常使用 `python3`。先執行：

```bash
python3 --version
```

### Agent 會不會自動把教材上傳 GitHub

不應該。提交前一定要看 GitHub Desktop 的 Changes 清單；`outputs/`、
`local-data/`、原始 PPTX、PDF、DOCX 與影片都不應出現。若出現，先停止提交並
通知維護者。

### Mac 能不能直接補寫講稿

可以先由 `physics-slide-enhancer` 產生 `speaker-notes.json`。目前自動寫回 PPTX
仍交給 Windows 匯出者，而且輸出必須另存新檔，不覆寫來源。
