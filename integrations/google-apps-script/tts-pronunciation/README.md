# Google Sheet 讀音候選收件匣

這個 Apps Script 只接收單一候選詞條，不接收完整逐字稿。試算表欄位為提交時間、
原稿詞語、配音寫法、使用語境、來源頁面、狀態與維護備註。

## 設定

1. 開啟已指定的 [Google Sheet](https://docs.google.com/spreadsheets/d/12UqQgG3GNxepKRNLeKjW5T1NvQEHqg2gMObu6IR1ZjU/edit)，從「擴充功能 → Apps Script」開啟綁定腳本。
2. 將 `Code.gs` 的內容複製到腳本專案。試算表 ID 已經填妥，不必再設定。
3. 在 Apps Script 編輯器執行一次 `setupCandidateSheet` 並授權；腳本會建立
   `讀音候選` 工作表與標題列。
4. 選擇「部署 → 新部署 → 網頁應用程式」，設定以部署者身分執行，並依團隊需求
   選擇可存取對象。
5. 複製結尾為 `/exec` 的網址，填入
   `data/tts-pronunciation/submission.json` 的 `apps_script_url`。
6. 重新部署 GitHub Pages。按鈕會自動改成「送到 Google 共用候選表」。

請不要把 OAuth token 或 Google 密碼放進 repository。若部署允許
任何人存取，請定期查看異常提交；正式共用規則仍需人工確認後才同步回 GitHub。
