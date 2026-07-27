# Skill Suite 共用執行規則

## 每次任務的共同前置

1. 從 repo 根目錄工作；不要假設固定磁碟代號。
2. 讀取 `config/project.toml`；不存在時參考 `config/project.example.toml`，並使用使用者提供的輸入路徑。
3. 執行 `python scripts/resolve_curriculum.py <專案碼>`，取得官方父碼、必修／選修層級、課綱陳述與教學說明。
4. 依 `references/evidence-policy.md` 使用 A → B → C → D 證據順序。
5. 需要舊教材時，先用 `scripts/index_materials.py` 建立或更新本機索引；檔名狀態只作提示。
6. 需要讀取 PPTX/DOCX 時，先用 `scripts/extract_office_text.py` 取得結構化文字；涉及圖文或版面判斷時仍須渲染檢視。
7. 將結論分為 `PASS`、`REVISE`、`HOLD`，同時記錄 strengths 與 findings。

## 不可省略的人工門檻

- 看不到圖時，不判定圖文一致。
- 沒有重算時，不判定數值與正解正確。
- 找不到官方父碼時，不判定未超綱。
- 來源互相衝突時，不自行選一個答案；列為 `HOLD`。
- 不在公開品質紀錄中寫入學生個資或未授權教材全文。

## 共用資料

- 官方課綱：`data/curriculum/stage5-physics.json`
- 九步驟：`data/rubrics/nine-step.json`
- 三面向八準則：`data/rubrics/literacy-eight-criteria.json`
- 術語：`data/terminology/physics-terms.json`
- 初始迷思庫：`data/misconceptions/starter.json`
- 品質紀錄 schema：`data/schemas/review-record.schema.json`
