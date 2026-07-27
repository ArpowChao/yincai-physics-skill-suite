# 外部審查者請從這裡開始

謝謝協助審查因材網高中物理教材產線。你不需要先理解全部程式，也不需要取得
教師原始教材庫；請依自己的專長檢查一小段，留下可重現、可行動的證據即可。

## 最快的審查方式

如果收到一個 `review-package` 資料夾：

1. 開啟 `review-workbench.html`。
2. 先看頂端的 `PASS / REVISE / HOLD` 與原因。
3. 用左側篩選「需處理」、「教學斷點」、「有影片」或「缺講稿」。
4. 中央切換投影片／本頁影片；右側先看「教學鏈」中的問題、學生輸出與回饋，
   再確認九步驟、十項內容品質及 critical gates。
5. 在「老師覆核」選擇通過、修改或暫緩，並寫一句理由。
6. 按「匯出審查紀錄」，把 JSON 交回維護者。

Windows 與 Mac 都可以使用這個方式；不需要安裝 Git、Python 或 PowerPoint。
瀏覽器中的覆核內容只存在你的電腦，不會自動上傳。

審查包名稱應採 `單元代碼_單元名稱_YYYYMMDD-HHmmss`。若同單元有多輪結果，
先依資料夾尾端時間辨識版本，不要把新結果存回舊資料夾。

維護者若要建立精簡分享包，需先確認投影片與影片的分享權：

```powershell
python scripts/build_review_share_bundle.py `
  "outputs\review-packages\單元" `
  "outputs\share-bundles\單元" `
  --confirm-authorized `
  --zip
```

產生的分享包會排除原始 PPTX、教師姓名檔名、完整媒體庫與轉錄原始資料。
審查者只要解壓縮 ZIP 並雙擊 `index.html`。

## 一個好問題要包含什麼

請使用 repository 的「教材／Skill 審查問題」issue 表單，至少提供：

- 版本：例如 `v0.4.0`。
- 單元代碼與頁碼／影片編號。
- 問題類型：課綱、物理、影片關聯、自學講稿、題目、介面或隱私授權。
- 實際看到什麼，以及合理預期應該是什麼。
- 依據：官方條目、物理推導、畫面證據或可重現步驟。
- 嚴重度：`blocker / major / minor / suggestion`。
- 本來做得好的地方；避免修正時把優點一起破壞。

只有「感覺不太好」很難迭代；「第 3 頁影片同時改變車種與速率，不能支持同速率下
質量越大動能越大的結論，而且看完沒有學生輸出、後面也未使用影片證據」就是
可測試、可修正的回報。

## 判定用語

- `PASS`：必要證據齊全，沒有 blocker 或 major。
- `REVISE`：方向正確，但有明確可修正的問題。
- `HOLD`：缺官方映射、關鍵原檔、授權、圖文證據或人工決策，不能猜。

## 不要上傳

- 教師或學生姓名、班級、成績與作答紀錄。
- 未取得分享權的完整 PPTX、DOCX、PDF、圖片或影片。
- `local-data/`、`outputs/`、`archive/` 的完整內容。
- 本機帳號、絕對路徑、API 金鑰或登入資訊。

外部可分享內容只應包含 repo 追蹤的程式、規則、去識別案例，以及經授權的審查包。

## 想修改專案

請接著閱讀 [貢獻指南](CONTRIBUTING.md) 與
[維護與迭代手冊](docs/maintenance.md)。Mac 使用者可先看
[macOS 使用指南](docs/macos-guide.md)。提交前執行：

```powershell
python scripts/audit_repository.py
python scripts/validate_suite.py
python -m unittest discover -s tests -v
```
