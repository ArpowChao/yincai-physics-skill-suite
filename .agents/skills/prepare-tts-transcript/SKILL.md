---
name: prepare-tts-transcript
description: Use when preparing Traditional Chinese transcripts, subtitles, formulas, or narration text for TTS, especially when polyphonic characters, Taiwan/Mainland pronunciation differences, or homophone substitutions must be reviewed without changing the original transcript.
---

# Prepare TTS Transcript

把正確文字的「原始逐字稿」與實際送入語音系統的「配音稿」分開管理。只修改配音稿，並保留每一項讀音替代與公式口語化建議供人確認。

## Inputs

- 一個 UTF-8 純文字、SRT 或 VTT 檔案，或使用者直接提供的文字。
- 可選的個人規則 JSON；只在本次或使用者自己的瀏覽器內優先套用。
- 若使用者指定詞語的正確讀音，記錄語境、原詞、配音替代字與備註。

## Workflow

1. 從 repository 根目錄執行分析，絕不覆寫輸入檔：

   ```powershell
   python scripts/tts_pronunciation.py analyze "path/to/transcript.txt" --output-dir outputs/tts-pronunciation
   ```

2. 回報產生的兩個檔案：
   - `*.tts.txt`：只供 TTS 使用的配音稿。
   - `*.changes.json`：原文、建議替代、讀音、理由、來源和位置。
3. 需要逐項確認、修改或新增個人規則時，啟動本機頁面：

   ```powershell
   python scripts/tts_pronunciation.py serve --host 127.0.0.1 --port 8765
   ```

   開啟終端機顯示的本機網址，匯入 TXT、SRT 或 VTT，逐筆接受、略過或編輯建議，再下載配音稿與修改紀錄。
4. 公式先轉成可朗讀建議，例如 `x² + y² = z²` 轉成「x 的平方 加 y 的平方 等於 z 的平方」。根號、分數與巢狀公式若仍有歧義，要求人工作最後確認。
5. 時間軸、字幕序號與原始文字必須保留；只在配音輸出替換詞語和公式。

## Confirmed and personal rules

- `data/tts-pronunciation/verified.json` 是全團隊共用、已確認的安全規則。
- `data/tts-pronunciation/moe-heteronyms.json` 是教育部辭典的多音詞參考層；只能
  標示為待確認，不得視為目標 TTS 一定會唸錯，也不得未確認就改稿。
- `data/tts-pronunciation/cross-strait-candidates.json` 仍是兩岸讀音候選層，不得
  標示為逐條試聽確認。依 2026-08-11 的團隊批次確認，網頁對
  `has_full_suggestion=true` 的 4,882 條完整草稿預設套用到配音稿；179 條不完整
  草稿仍維持待確認。每筆都必須保留「保留原稿」選項，且不得改動正式逐字稿。
- 個人規則優先於共用規則，但預設只存在瀏覽器或另外匯出的 JSON，不直接寫回共用資料。
- 最長詞組優先，避免短詞規則拆錯語境。
- 不要把個人規則升級為共用規則，除非人已確認語境、替代字可被目標 TTS 唸對，並補上測試。
- 無法確定的多音字只標示為待確認，不猜測或自動取代。
- g2pW 可在 Agent 環境中作為整句上下文判音的第二意見；它是模型而不是同音字
  替換庫，輸出仍須轉成目標 TTS 能穩定讀對的同音字，並經人試聽確認。不要把
  g2pW 模型塞進靜態 GitHub Pages。

## Evidence and sources

- 新增或修改共用讀音規則、比較臺灣與中國讀音、使用 g2pW 或匯入辭典前，先讀
  [讀音來源與證據層級](references/pronunciation-sources.md)。
- 嚴格區分四層證據：「官方臺灣讀音」、「兩岸讀音差異或模型候選」、「目標
  TTS 實際誤讀」、「已試聽成功的同音字替代」。批次套用的兩岸候選仍停留在
  第二層，不得因此升級為已試聽成功或寫入 `verified.json`。
- 只有同時確認正確讀音、實際聽到目標 TTS 誤讀，並試聽替代字有效後，才把規則
  升級到 `verified.json`。記錄使用的語音服務、聲音版本、日期與測試句。
- 不把第三方資料集的規模寫成「已發現錯音數」；數量、篩選方式、版本與授權必須
  一起標示。

## Output contract

- 原始逐字稿內容與檔案保持不變。
- 每個變更至少包含 `kind`、`original`、`replacement`、`pronunciation`、`reason`、`source`、`start`、`end`。
- 清楚區分「正確顯示文字」和「TTS 配音文字」。
- SRT/VTT 的時間碼與提示結構不變。
- 若公式無法可靠口語化，保留原式並在修改紀錄標成待人工確認。

## Stop conditions

- 找不到輸入檔，或檔案不是可解碼的文字、SRT、VTT。
- 使用者要求直接覆寫唯一的原始逐字稿。
- 讀音依賴專有名詞、方言或上下文，但沒有足夠證據判斷。
- 複雜公式含有未支援的矩陣、分段函數或高度巢狀結構；輸出建議後停下來請人確認。

## Common mistakes

- 把配音用同音字回填到正式字幕或教材。
- 只記替代結果，沒有保留原詞、位置和理由。
- 對所有單字做全域取代，忽略詞組和語境。
- 將公式的視覺寫法直接交給 TTS，期待引擎自行推斷念法。
- 未經確認就把一次性的個人修正加入共用字典。
