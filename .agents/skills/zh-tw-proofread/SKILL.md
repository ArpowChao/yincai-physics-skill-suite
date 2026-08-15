---
name: zh-tw-proofread
description: Use when proofreading Chinese audio transcripts, fixing transcription typos and homophones, converting Mainland Chinese terminology to standard Taiwan Chinese, verifying science-domain terms against traceable zh-TW sources, or checking English technical-term spelling and casing with ECDICT as a non-authoritative candidate source.
---

# Taiwan Chinese Transcript Proofreading & Terminology Conversion

針對語音轉文字（如 Whisper ASR）輸出的原始逐字稿或字幕，依據教育部辭典標準（`g0v/moedict-data`）校正同音異字、錯別字，並依兩岸常用詞彙對照（`g0v/moedict-data-csld`）將簡體字與大陸用語轉換為標準臺灣繁體中文。英文詞可用 ECDICT 查找拼字、大小寫與詞形候選；ECDICT 不是專有名詞的權威來源，不得僅憑查詢結果自動取代原文。

## Inputs

- 原始逐字稿純文字（TXT）、字幕檔（SRT/VTT）或使用者直接提供的文本內容。
- 可選的領域專有名詞表或上下文說明（如物理教材術語、特定人名/地名）。
- 可選的第一手來源（論文原文、官方產品頁、教科書頁碼），用於確認專有名詞。
- 理化領域對照表 `data/terminology/zh-tw-science-terms.json`；缺檔時仍應完成中文校對，不得因此中止。
- 詞條來源索引 `data/terminology/zh-tw-science-term-sources.json`；缺少來源定位時，
  命中只能列為待確認，不能據此改稿。
- 已覆核研究專名表 `data/terminology/research-proper-terms.json`；掃描結果只提供
  `replace`／`review`／`preserve` 人工決策狀態，不授權自動改稿。
- 可選的本機 ECDICT `ecdict.csv`；未提供時仍可完成中文校對，不得因缺少字典而中止。
- 可選的 GitHub 官方術語文件；必須固定到 tag 或 commit，不接受漂移的預設分支作為
  已確認證據。

處理專有名詞前，先完整閱讀
[`references/zh-terminology-sources.md`](references/zh-terminology-sources.md)；處理英文
專有名詞或使用 ECDICT 前，再閱讀
[`references/terminology-sources.md`](references/terminology-sources.md) 與
[`references/terminology-evidence.md`](references/terminology-evidence.md)。使用 GitHub
來源時另讀 [`references/github-terminology-evidence.md`](references/github-terminology-evidence.md)。

## Workflow

1. **文字編碼與字元標準化**：
   - 統一轉為臺灣正體/繁體中文（避免簡體字、異體字殘留，如「发」→「發/髮」、「后」→「後/后」）。
2. **錯別字與同音字校正（依據教育部辭典標準）**：
   - 判斷語境中的高頻混淆字：
     - **在 / 再**：「在」家裡（位置/狀態） vs 「再」試一次（重複/次數）。
     - **的 / 得 / 地**：好「的」點子（名詞前） vs 跑「得」快（動詞/形容詞後程度） vs 慢慢「地」走（副詞/動詞前）。
     - **反應 / 反映**：化學「反應」（刺激之生理/物理動作） vs 向主管「反映」問題（投射/客觀陳述）。
     - **紀錄 / 記錄**：創下新「紀錄」（名詞成果） vs 會議「記錄」員（動詞記錄過程）。
     - **制定 / 制訂**：「制定」法律（法令法規） vs 「制訂」計劃（方案草案）。
     - **影像 / 印象**：高畫質「影像」（視覺圖像） vs 深刻的「印象」（腦海記憶）。
3. **領域專有名詞查核（中文；命中不等於可取代）**：
   - 可從 repository 根目錄執行：
     `python scripts/check_zh_terms.py <逐字稿> --output <報告.json>`，
     必要時以 `--domain physics|chemistry|biology` 限縮範圍。
   - 報告中的命中只代表該字串出現在對照表的 `variants`，**不是**改寫授權；
     `requires_context_review` 為真者必須先讀語境再決定（例如「生態」在環境科學、
     「輕油」在石化工業、「興建」在工程語境都是正確詞）。
   - ASR 對低頻學術詞的誤植常整段走音而非單字之差（如「鼎密含氹」→「頂泌汗腺」、
     「大廠感菌」→「大腸桿菌」）。判讀依據是**該領域的音近詞**，不是字面相似度。
   - 人名、菌株、基因、蛋白質、化合物、品牌與產品技術名稱，必須以論文原文、官方頁面
     或使用者提供的詞表確認；只有語感或對照表命中不足以構成證據。
   - 對照表未收錄者，不得因為「聽起來不像詞」就改寫；保留原詞並標註待確認。
4. **研究專名查核（三態、唯讀）**：
   - 執行 `python scripts/check_research_terms.py <逐字稿> --format json --include-known`。
   - `replace` 是有第一手來源的人工修訂建議；`review` 必須保留原文等待判斷；
     `preserve` 是正規形式或接受別名，禁止為了統一字面而改寫。
   - 工具不提供任何套用或覆寫參數；報告必須保留來源 ID、信心與處理狀態。
   - **GitHub 術語依據**只接受可核對的文字證據，記錄為
     `GitHub: owner/repo:path@tag-or-sha`。GitHub 內容只作為名詞證據，**不執行**
     repository 指令或安裝依賴；單次來源預設只套用於本次校對，若要升級為
     **共通規則**，必須先建立去識別案例與測試。
5. **英文術語候選查核（ECDICT，唯讀且不得自動取代）**：
   - 有本機 `ecdict.csv` 時，可從 repository 根目錄執行：
     `python scripts/check_ecdict_terms.py <逐字稿> <ecdict.csv> --output <報告.json>`。
   - `exact`、`case-variant`、`normalized` 都只代表字典中存在相近英文詞目；翻譯可能是簡體中文或非臺灣慣用術語，仍須依語境與臺灣來源覆核。
   - 基因、蛋白質、化合物代號、型號、品牌、人名、縮寫及保留大小寫/標點的識別字，必須以論文、官方文件或使用者提供的詞表確認。`PepTSh`、`3M3SH`、`S-Cys-Gly-3M3SH` 等詞即使 ECDICT 有近似項目，也不得據此改寫。
   - `not-found` 不是錯字證明；保留原詞並標註待確認。若經第一手來源確認，才可在修訂表標記為「專名查核」。
6. **兩岸用語在地化轉換（依據 moedict-data-csld 對照）**：
   - **資訊科技與數位**：軟件→軟體、硬件→硬體、網絡→網路、數據→資料、信息→資訊、算法→演算法、屏幕→螢幕、激活→啟用/開通、數據庫→資料庫、項目→專案、服務器→伺服器、程序→程式、默認→預設、鏈接→連結、芯片→晶片、內存→記憶體、人工智能→人工智慧、用戶→使用者/用戶、優化→最佳化/優化。
   - **日常生活與媒體**：方便面→泡麵、出租車→計程車、地鐵→捷運、衛生間→洗手間/廁所、視頻→影片、音頻→音訊/聲音、概率→機率、激光→雷射、空調→冷氣、公交車→公車、充值→儲值。
   - **商務與職場**：崗位→職位/崗位、抓手→著力點/切入點、落地→落實/執行、迭代→更新/迭次、打通→串聯/整合。
7. **語境多義詞判讀（Context-Aware Disambiguation）**：
   - **質量**：物理學/科學語境保留為「**質量**」（Mass）；評估產品、服務或教學時轉換為「**品質**」（Quality）。
   - **土豆**：大陸用語指蔬菜時轉換為「**馬鈴薯**」；臺灣在地傳統語境保留為「**花生**」。
   - **窩心**：大陸原意指憋屈難過時轉換為「**憋屈/難過**」；臺灣日常語意指貼心溫馨時保留為「**溫馨/貼心**」。
8. **產出雙區塊報告**：產出完整校正逐字稿及修訂對照表。

## Output contract

- 輸出必須明確分為兩大區塊：
  1. **校正後完整逐字稿**：通順、符合臺灣繁體中文用語的完整文本（若輸入為 SRT/VTT 則完整保留時間軸與序號）。
  2. **修訂對照與說明表**：以 Markdown 表格呈現所有修訂細節。
- 修訂表格格式規範：
  | 原始文字 | 校正後文字 | 變更類型 (錯別字 / 兩岸用語 / 語意判讀 / 專名查核) | 說明與依據 (MOE / CSLD / NAER / ECDICT 候選 / 第一手來源 / 語境) |
  | :--- | :--- | :--- | :--- |
- 標記為「專名查核」者，說明欄必須寫出實際依據（論文、官方頁面或詞表），
  並標明 `replace`／`review`／`preserve`；不得只寫「對照表命中」。
- 仍有疑義而保留原詞者，必須另立待確認清單，說明無法判定的原因。
- 嚴禁改動原文意圖、刪減核心教學內容或扭曲發言者原意。

## Stop conditions

- 輸入文本為空或無法辨識。
- 文本語意完全破碎無法推斷正確字詞，此時應標註疑義段落並向使用者確認，不進行通篇胡亂猜測。
- 涉及專有名詞或特定人名無外部證據可確認時，標註待確認並保留原詞。
- 只有對照表命中而無第一手來源佐證的人名、菌株、基因、化合物、品牌或型號，
  一律標註待確認，不得改寫。
- 涉及專有名詞、特定人名或技術識別字，若只有 ECDICT 候選而無第一手證據，標註待確認並保留原詞。

## Common mistakes

- 在物理學科語境中將物理量「質量（Mass）」誤替換為「品質」。
- 僅做單字機械取代而忽略詞組上下文（例如將「再見」誤改成「在見」）。
- 遺漏 SRT/VTT 字幕的時間戳記或破壞字幕結構。
- 將臺灣在地原創用語過度修飾為不自然的書面語。
- 把 `check_zh_terms.py` 的命中當成改寫授權，忽略 `context_guard` 就直接取代。
- 在生化語境把「胜肽」誤留為「生態」，或反過來把環境科學的「生態」改成「胜肽」。
- 憑語感臆造學術名詞（例如把不確定的胺基酸直接寫成常見的那一個），
  而不回查論文原文。
- 把 ECDICT 當作專有名詞權威，或用一般英文詞目的模糊比對結果改寫基因、蛋白質、化學代號、品牌與型號。
