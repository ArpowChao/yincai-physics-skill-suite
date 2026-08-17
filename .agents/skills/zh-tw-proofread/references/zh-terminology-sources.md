# 中文專有名詞來源政策

本文件規範 `zh-tw-proofread` 在處理**中文**專有名詞時的依據與界線。
英文術語與 ECDICT 的使用另見英文術語來源政策。

## 為什麼需要這一層

一般同音字校正（在／再、的／得／地）靠語感即可判斷，但 ASR 對低頻學術詞的誤植
是**整段走音**，字面上看不出破綻，語感反而會把錯的讀順：

| ASR 輸出 | 正確詞 | 若只靠語感 |
|---|---|---|
| 鼎密含氹 | 頂泌汗腺 | 看不出是什麼，容易整段跳過 |
| 大廠感菌 | 大腸桿菌 | 像某種菌名，讀起來不突兀 |
| 弱氨酸 | 酪胺酸 | 像某種胺基酸，最容易被臆改成常見的那一個 |
| 直子一代型寡態 | 質子偶合寡胜肽 | 完全走音，需要領域知識才還原 |

最後一類最危險：模型會**挑一個常見的同類詞填進去**（例如把不確定的胺基酸寫成
「丙胺酸」），產出讀起來完全通順但事實錯誤的稿件。因此本 skill 要求專名一律回到
第一手來源，不接受語感推定。

## 證據優先序

1. **第一手來源**：論文原文、官方產品文件、標準組織資料庫、教科書頁碼。
2. **國家教育研究院樂詞網**（<https://terms.naer.edu.tw/>）：臺灣學術名詞的權威對照，
   收錄各學科英中名詞與審定譯名。
3. **教育部重編國語辭典修訂本**（`g0v/moedict-data`）：一般字詞正寫與詞義。
4. **兩岸常用詞彙對照**（`g0v/moedict-data-csld`）：兩岸用語差異。
5. **本 repository 的 `data/terminology/zh-tw-science-terms.json`**：候選清單。

低順位不得推翻高順位。對照表命中只是「值得查」，不是「可以改」。

## 對照表的定位

`data/terminology/zh-tw-science-terms.json` 收錄三類：

- `asr-homophone`：語音辨識同音／近音誤植，例如「流醇」→「硫醇」。
- `cross-strait`：兩岸譯名差異，例如「中微子」→「微中子」、「勢能」→「位能」。
- `orthography`：臺灣中文內部的別字，例如「力距」→「力矩」、「震幅」→「振幅」。

每條都必須有 `evidence` 欄位標示依據類型，並在
`data/terminology/zh-tw-science-term-sources.json` 以 `source_refs` 指向可追溯的
來源記錄。NAER 引用至少保存中英文查詢鍵；只有來源名稱而沒有 URL、
版本／擷取日期及查詢定位，不算完成查核。帶 `context_guard` 的條目代表該詞在別的
領域是正確詞，**必須先讀語境**：

- 「生態」在環境科學正確，只有生化語境指 peptide 時才是「胜肽」之誤。
- 「輕油」在石化工業正確（naphtha），只有描述親和性時才是「親油」之誤。
- 「興建」在工程語境正確，只有化學鍵結語境才是「氫鍵」之誤。
- 「質量」在物理語境是 mass，**絕不可**改成「品質」。這是本 suite 已知的最高風險錯誤。

## 查核程序

1. 保留原始逐字稿，不直接覆寫。
2. 從 repository 根目錄執行：

   ```powershell
   python scripts/check_zh_terms.py transcript.txt --output outputs\zh-term-candidates.json
   ```

   需要限縮領域時加 `--domain physics`（或 `chemistry`、`biology`）。
3. 先處理 `requires_context_review` 為真的命中，逐條判斷語境。
4. 對照表沒抓到、但屬於下列類型的詞，一律主動查第一手來源：
   人名、菌株、基因、蛋白質、化合物、儀器型號、品牌、產品技術名稱、期刊名。
5. 查到才改，並在修訂對照表寫明實際來源；查不到就保留原詞並列入待確認清單。
6. SRT/VTT 的序號與時間軸不得因術語查核而更動。

## 維護規則

發現新的誤植型態時，回頭補進 `data/terminology/zh-tw-science-terms.json`，並遵守：

- `preferred` 不得重複，`variants` 不得與自己的 `preferred` 相同。
- 同一個 `variant` 不得同時指向兩個 `preferred`（會造成取代衝突）。
- 新增條目必須填 `category`、`domain`、`evidence`，並在來源索引新增同名
  `term_sources` 記錄；每個引用都要解析到 `sources` 中的來源，並提供可重現的
  `locator`。
- 若該詞在其他領域是正確詞，必須補 `context_guard`。
- 資料改動要同步更新 `tests/test_zh_tw_terminology.py` 的回歸案例。

對照表刻意保持精選而非窮舉：它處理的是「已經踩過的坑」，未收錄的專名走查證流程，
不靠擴充清單來取代查證。
