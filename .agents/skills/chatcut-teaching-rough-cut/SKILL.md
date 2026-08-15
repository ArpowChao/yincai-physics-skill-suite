---
name: chatcut-teaching-rough-cut
description: Use when performing a one-pass rough cut of a PowerPoint or EverCam teaching video in ChatCut, including editable-timeline safety, retake and pause removal, PowerPoint animation preservation, protected AI or inserted clips, a precise silent window on the single slide titled 檢核點, captions, and traceable duration accounting.
---

# ChatCut 教學影片一次到位粗剪

## 版本

- 規則版本：**V1.5.4.1 開場硬保護、檢核點精準保護與可追溯穩定版**。
- 正式規則：`references/rough-cut-rules-v1.5.4.1.md`。
- 教師設定範本：`references/teacher-input-template-v1.5.4.1.md`。

## Inputs

- 可編輯的 ChatCut 專案與原始 PowerPoint／EverCam 教學素材。
- 可選的教師設定：開場、插入影片、檢核點與其他不可修改區段的時間碼。
- 未填設定時，依正式規則從原始素材辨識；不要把「不確定」當成可刪除。

## Workflow

1. 開始任何剪輯前，完整讀取 `references/rough-cut-rules-v1.5.4.1.md`；它是本 Skill 的正式執行契約。
2. 以原始素材辨識並鎖定開場 AI 影片、插入短片 Atomic Block、PPT 動畫、主標題為「檢核點」的無聲思考窗、答案揭示、必要轉場與片尾。
3. 只在未鎖定區段執行轉錄、錯錄與重錄處理、停頓壓縮、贅詞處理及可選的局部加速。
4. 逐一驗證新增剪接點，將剪後時間線與原始素材比對，並核對有效刪除清單與片長差異。
5. 儲存可編輯時間線後，建立、同步並匯出臺灣繁體字幕與 SRT；只在已確認的字幕技術錯誤時安全降級。

## Output contract

1. 已儲存、保持可編輯的 ChatCut 粗剪時間線。
2. 正常情況下可編輯的臺灣繁體中文字幕軌、完整 SRT 與剪後逐字稿（系統支援時）。
3. 精簡成果摘要：規則版本、片長與縮短量、實際處理數、保護區驗證、對帳結果、最多 5 個人工抽查點，以及未完成的字幕／轉場／渲染問題。

## Stop conditions

- 無法取得原始素材或可寫入的 ChatCut 專案，因此不能實際建立或儲存時間線。
- 無法確認疑似開場、插入影片或檢核點位置時，保留該段、列為人工抽查，並繼續處理其餘安全區段；不得擴大硬保護或先刪後驗。
- 字幕、局部加速或單一轉場失敗時，只依正式規則降級該子任務；不得重置、重建或破壞已完成時間線。

## Common mistakes

- 先自動去頭或只看剪後時間線，才辨識開場 AI 影片。
- 將所有題目頁或整張「檢核點」頁面設為硬保護，而非只保護最長 7 秒的確認無聲思考窗。
- 以音訊交叉淡化取代必要視覺轉場，或剪掉 PowerPoint 動畫、插入影片的首尾。
- 為產出字幕或報告重建已完成時間線，或未完成原始素材比對就宣告驗證通過。
