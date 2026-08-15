# 授權與來源邊界

此 repository 已公開供檢視、clone、fork 與提出 Pull Request，但目前尚未選定
開源授權。**公開可見不代表放棄著作權，也不代表自動允許重製、改作或再散布。**

專案負責人後續仍需決定：

1. 程式碼與 Skills 的授權（例如 Apache-2.0 或 MIT）。
2. 原創教學架構、規準整理與範例的內容授權（例如適當的 Creative Commons 授權）。
3. 第三方教材、圖片、論文與課綱摘錄是否可再散布。

在正式授權檔發布前，請先以 Issue 或 Pull Request 聯絡維護者取得使用許可。
外部使用者可以 fork 進行技術評估或提出修改，但 Pull Request 被接受不代表取得
repository 其他內容的授權。

教育部課綱、既有教師教材、論文附件、出版社或 LLM-wiki 來源不會因放入本機資料庫
而自動取得再授權權利。公開範圍只包含本專案原創程式、結構、去識別紀錄與必要的
短引用／來源指引；原始 PPTX、DOCX、PDF 與全文資料不納入版控。

## 配音讀音參考資料

`data/tts-pronunciation/moe-heteronyms.json` 的詞目與注音取自教育部
《重編國語辭典修訂本》，透過 [g0v/moedict-data](https://github.com/g0v/moedict-data)
提供的 JSON 格式轉換資料整理。辭典資料採「創用 CC 姓名標示－禁止改作 3.0
臺灣」授權；教育部允許格式轉換與後續應用，但辭典文字本身的權利仍屬教育部。
本專案另外產生的同音字草稿與介面判斷不宣稱為教育部內容，且一律標示為待人工
確認。資料來源與正式授權說明見
[教育部國語辭典公眾授權網](https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/index.html)。

匯入工具固定保留來源名稱、網址與授權欄位；若更新上游資料，應重新執行
`scripts/import_moe_tts_lexicon.py` 並覆核筆數、來源版本與抽樣讀音。

### 兩岸讀音參考

兩岸讀音調查參考 [中華語文知識庫](https://www.chinese-linguipedia.org/about.html)
與 [g0v/moedict-data-csld](https://github.com/g0v/moedict-data-csld)。上游說明中，原始
《中華語文大辭典／兩岸詞典》內容採 CC BY-NC-ND 4.0；g0v 所做的格式轉換與編排
部分採 CC0。兩者的授權範圍不可混為一談。

本 repository 不重製整份 `moedict-data-csld`，但
`data/tts-pronunciation/cross-strait-candidates.json` 與網頁用的精簡 JS 會保存經篩選
的詞目、兩岸讀音及專案產生的同音字草稿。這個候選子集必須保留來源、版本、
姓名標示、非商業與禁止改作限制，不能被視為本專案程式碼授權的一部分。若要在
其他產品重新散布，仍須自行確認原始權利人的授權範圍。官方審音資料另見
[臺灣《國語一字多音審訂表》](https://language.moe.gov.tw/001/Upload/Files/wxiao89/a.pdf)
及 [中國《普通話異讀詞審音表》](https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75598.html)。

### g2pW

[g2pW](https://github.com/GitYCC/g2pW) 程式碼採 Apache-2.0，用於 Agent 或本機端的
上下文多音字判讀；研究方法見 [論文](https://arxiv.org/abs/2203.10430)。本專案不把
g2pW 模型或其訓練資料打包進靜態網頁。若未來散布模型權重或相依資料，必須另行
查核上游 repository 所列的個別授權。

更完整的資料角色、版本快照與升級條件見
`.agents/skills/prepare-tts-transcript/references/pronunciation-sources.md`。

## 英文術語候選資料

[ECDICT](https://github.com/skywind3000/ECDICT) 是採 MIT License 發布的英漢字典
專案。`zh-tw-proofread` 以 revision
`bc015ed2e24a7abef49fc6dbbb7fe32c1dadaf8b` 的資料格式與欄位作為工具契約基準，
只讀取使用者自行下載的本機 CSV，並在候選報告保留來源網址、revision 與授權。

本 repository 不內嵌或重新散布完整 ECDICT 資料庫。ECDICT 的一般英文詞目與中譯
只作拼字、大小寫與詞形候選，不能取代論文、官方產品文件或領域術語表；其中譯也
可能不是臺灣慣用詞。完整的證據順位與使用邊界見
`.agents/skills/zh-tw-proofread/references/terminology-sources.md`。

## 研究專名來源

`data/terminology/research-proper-terms.json` 只保存八個短專名、常見錯聽形式、
三態人工決策與來源識別碼，不重製論文全文。研究專名目前引用
[eLife 7:e34995](https://elifesciences.org/articles/34995) 的公開論文頁；原始來源的
著作權不因短詞目索引而改變。完整證據邊界見
`.agents/skills/zh-tw-proofread/references/terminology-evidence.md`。
