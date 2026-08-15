# 專有名詞與兩岸詞彙證據規則

## 來源角色

專有名詞不存在一個可包辦所有領域的 GitHub 萬用資料庫。校正時依下列優先順序取證，不能把一般辭典的「查無此詞」當成專名錯誤：

1. 使用者提供、且已確認的專案詞表或品牌詞表。
2. 主管機關、品牌官網、原始論文、標準文件等一手來源。
3. 學門專業名詞庫，例如國家教育研究院術語資料。
4. `g0v/moedict-data`：一般國語詞義、字形與用法參考。
5. `g0v/moedict-data-csld`：兩岸差異候選參考；不可脫離語境批次替換。

第 4、5 類來源不能單獨證明品牌名稱、菌種、基因、蛋白質、論文縮寫或產品文案。外部來源互相衝突，或找不到一手來源時，保留原文並標記 `HOLD`。

## 專案詞表與掃描器

- 已覆核研究專名表：`data/terminology/research-proper-terms.json`
- 唯讀掃描器：`scripts/check_research_terms.py`
- 詞表只保存短詞目、錯聽形式、處理動作、信心與來源識別碼，不重製第三方資料庫或文章全文。

在 repository 根目錄執行：

```powershell
python scripts/check_research_terms.py transcript.txt --format text
python scripts/check_research_terms.py transcript.txt --format json --include-known
```

動作定義：

- `replace`：已有一手來源或正式術語來源，且錯聽形式沒有合理多義；仍只作人工修訂建議。
- `review`：有高度可能的建議，但產品全名、斷句或語境仍需人工確認；不得自動套用。
- `preserve`：偏好形式或已接受別名；即使和專案偏好不同也不得自動改寫。

掃描器永遠不改寫檔案。`replace`、`review`、`preserve` 都是報告中的人工決策狀態，
不是自動套用授權。

## 新增專有名詞

1. 先保留原文，取得使用者詞表或一手來源。
2. 在 `sources` 新增來源識別碼、網址、版本／日期、擷取日期、角色與授權註記。
3. 在 `terms` 新增偏好詞、類型、領域、來源與 variants。
4. 錯聽詞若有歧義用 `review`；接受別名用 `preserve`，不要為了統一字面而設為 `replace`。
5. 在 `tests/test_research_terms.py` 增加真實但去識別的最小案例。
6. 執行單元測試、suite validator 與 repository audit。

## 報告中的證據標記

修訂對照表的「說明與依據」欄需寫入：

- 詞表 `source_ids`；
- `confirmed` 或 `candidate`；
- `replace`、`review` 或 `preserve`；
- 若不在詞表，列出實際查閱的一手來源，而不是籠統寫「MOE」。

未取得證據時使用「專名待確認／HOLD」，不得自行補造大小寫、英文字母、數字或學名。
