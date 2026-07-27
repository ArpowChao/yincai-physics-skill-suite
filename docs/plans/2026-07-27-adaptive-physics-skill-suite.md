# Adaptive Physics Skill Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立可移植、可驗證、能以官方課綱與既有教材持續迭代的因材網高中物理教材產線 Skill Suite。

**Architecture:** 採十個薄 Skill 搭配共用機器可讀資料層、證據摘要、索引與品質紀錄。所有本機教材與 LLM-wiki 以設定檔定位，不寫死磁碟路徑，也不預設納入公開 repo。

**Tech Stack:** Markdown、YAML、JSON/JSONL、Python 3 標準函式庫、unittest、OOXML（PPTX/DOCX）、Git。

### Task 1: 建立 RED 驗收基線

**Files:**
- Create: `tests/test_skill_suite.py`
- Create: `tests/test_curriculum.py`
- Create: `tests/test_asset_index.py`
- Create: `tests/test_quality_records.py`
- Create: `tests/fixtures/`

**Steps:**
1. 寫入會檢查十個 Skill、frontmatter、相對路徑、必要章節與 metadata 的測試。
2. 執行 `python -m unittest discover -s tests -v`，確認因缺少資料、腳本、metadata 或硬編碼路徑而失敗。
3. 保存失敗摘要到 `quality/baseline-2026-07-27.md`。

### Task 2: 建立官方課綱與共用規準

**Files:**
- Create: `data/curriculum/stage5-physics.json`
- Create: `data/rubrics/nine-step.json`
- Create: `data/rubrics/literacy-eight-criteria.json`
- Create: `data/schemas/review-record.schema.json`
- Create: `data/terminology/physics-terms.json`
- Rewrite: `references/stage5_curriculum_and_scope.md`
- Create: `references/evidence-policy.md`

**Steps:**
1. 以官方 PDF 第 38–40、186–191 頁建立必修物理父碼、內容與教學說明。
2. 明確區分官方碼與專案延伸碼。
3. 為每筆範圍規則加入來源、頁碼與信心層級。
4. 執行 curriculum 測試直到通過。

### Task 3: 建立可重跑工具

**Files:**
- Create: `scripts/common.py`
- Create: `scripts/resolve_curriculum.py`
- Create: `scripts/index_materials.py`
- Create: `scripts/extract_office_text.py`
- Create: `scripts/new_review_record.py`
- Create: `scripts/summarize_quality.py`
- Create: `scripts/validate_suite.py`
- Create: `config/project.example.toml`

**Steps:**
1. 先用 fixture 測試課綱碼正規化、檔名解析、組件分類與品質紀錄驗證。
2. 實作最小功能使單元測試逐一通過。
3. 對 `資料/` 執行索引 dry run，禁止修改原始教材。
4. 對一份 PPTX 與 DOCX 執行文字抽取，確認頁／投影片邊界與 speaker notes 狀態可辨識。

### Task 4: 逐一升級十個 Skill

**Files:**
- Rewrite: `.agents/skills/*/SKILL.md`
- Create: `.agents/skills/*/references/repo-map.md`
- Create: `.agents/skills/*/agents/openai.yaml`

**Steps（每個 Skill 均重複）：**
1. 執行該 Skill 的結構測試，確認 RED。
2. 將 description 改為明確觸發條件，不摘要整個流程。
3. 加入輸入檢查、證據順序、工作流程、輸出契約、停止條件、常見錯誤與最小範例。
4. 移除 `file:///f:/...` 等絕對路徑。
5. 產生 `agents/openai.yaml`。
6. 執行 `quick_validate.py` 與專案測試，確認 GREEN 後才處理下一個 Skill。

處理順序：`physics-framework-checker`、`physics-one-page-architect`、`physics-slide-enhancer`、`physics-worksheet-generator`、`physics-visual-style-guide`、`physics-literacy-question-creator`、`physics-question-qa-checker`、`physics-misconception-prompting`、`physics-ppt-upgrader`、`physics-unit-package-qc`。

### Task 5: 建立品質回饋與 repo 文件

**Files:**
- Create: `quality/README.md`
- Create: `quality/records/.gitkeep`
- Create: `quality/known-issues.md`
- Create: `quality/confirmed-strengths.md`
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `.gitignore`

**Steps:**
1. 說明如何記錄缺失、通過項目、人工裁決與回歸案例。
2. README 加入五分鐘快速開始、三條產線、十個 Skill 對照、設定、資料權限、驗證與跨電腦安裝。
3. CONTRIBUTING 加入一問題一案例、規準版本化、來源標註、個資與版權要求。
4. 初始化 Git，僅追蹤可分享內容；原始教材、PDF、PPTX、DOCX、個人設定與生成輸出保持忽略。

### Task 6: 端到端驗證

**Files:**
- Create: `quality/examples/peb-vc-4-1-dry-run.md`
- Update: `quality/known-issues.md`
- Update: `quality/confirmed-strengths.md`

**Steps:**
1. 解析 `PEb-Vc-4-1` 為官方父碼 `PEb-Vc-4`。
2. 索引同單元 PPTX、學習單與題目。
3. 抽取三類文本，執行 dry-run 總檢並記錄證據、缺失與通過項目。
4. 執行 `python -m unittest discover -s tests -v`、`python scripts/validate_suite.py`、十個 `quick_validate.py`（若環境缺少其 PyYAML 依賴，記錄限制並以本專案驗證器交叉檢查）。
5. 重新閱讀本計畫逐項核對，僅在所有必需項目有新鮮驗證證據時宣告完成。
