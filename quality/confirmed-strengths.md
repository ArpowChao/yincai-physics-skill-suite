# 已確認可保留的設計

更新日期：2026-07-27

以下是目前由規格檢查與測試確認的套件層級優點；真實教學成效仍需累積教師覆核紀錄。

| ID | 設計 | 證據 |
|---|---|---|
| CS-001 | 10 個 Skills 共用同一份課綱與評分規準，避免版本漂移 | suite validator 與 `test_skill_suite.py` |
| CS-002 | 自訂教材代碼能解析到最長的官方母節點，未知代碼不猜測 | `test_curriculum.py` |
| CS-003 | 每次審查同時記錄優點與缺失，可保留有效教學設計 | `test_quality_records.py` |
| CS-004 | 原始教材索引採唯讀，且輸出使用相對路徑 | `test_asset_index.py` |
| CS-005 | 每個 Skill 都明訂輸入、工作流、輸出、停止條件與常見錯誤 | `scripts/validate_suite.py` |
| CS-006 | 真實 `PEb-Vc-4-1` 單元已具歷史概念衝突、生活應用與迷思誘答，可作升級時的保留基底 | `quality/examples/peb-vc-4-1-dry-run.json` |
| CS-007 | 五個首波分享 Skills 已以同一真實單元完成 29 項輸出契約檢核，能串成架構—審查—講稿—學習單—題目的連續示範 | `showcase/review.html`、`scripts/validate_showcase.py` |
