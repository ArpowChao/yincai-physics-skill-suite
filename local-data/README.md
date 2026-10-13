# local-data：需要使用但不可直接分享

這個資料夾存放本機教材、官方來源複本、研究資料、姓名索引與尚未審定的候選知識。
除本說明外，內容全部由 `.gitignore` 排除。

## 分類

| 資料夾 | 用途 | 可公開？ |
|---|---|---|
| `materials/` | PPTX、DOCX、題庫等完整教材庫 | 否，需逐件確認授權 |
| `sources/` | 官方課綱 PDF 等可重建資料來源 | repo 不直接收大型原檔 |
| `samples/` | 本機真實測試簡報 | 否，先去識別與確認授權 |
| `research/` | 論文、評分與研究工作資料 | 否，依原授權使用 |
| `private/` | 姓名、團隊規劃等個資 | 否 |
| `indexes/` | 含姓名或本機路徑的教材索引 | 否 |
| `physics-kb/` | LLM-wiki 等候選知識 | 否；一律視為 D 級證據 |
| `reference-candidates/` | 尚未審定的規則與範例 | 否；通過審查後才能移入 `references/` |
| `review-candidates/` | 一次性或含姓名的審查報告 | 否；去識別後可移入 `quality/examples/` |
| `skill-candidates/` | 舊 Skill 的局部範例／參考 | 否；驗證後整合進共用資料層 |

## 下載公開官方來源

課綱與學測原檔不放進 repo；換電腦或給別人使用時，在 repo 根目錄執行：

```
python scripts/fetch_local_data.py
```

清單在 `data/sources/official-downloads.json`，下載到：

| 位置 | 內容 | 來源 |
|---|---|---|
| `sources/curriculum/108課綱_自然科學領域.pdf` | 十二年國教自然科學領域課綱 | 國家教育研究院 |
| `sources/gsat/{年}學測自然_試題.pdf`、`_答案.pdf` | 101～115 學測自然試題與選擇題答案 | 大學入學考試中心 |

只用 Python 標準函式庫；已存在的檔案會略過，`--force` 重新下載，`--dry-run` 只列清單。
下載失敗時，到清單中的 `index_pages` 手動下載並存成同樣檔名。

以下需自行放入，不在下載清單：

| 位置 | 內容 | 原因 |
|---|---|---|
| `materials/textbook/` | 同章課本 PDF（Ch01～Ch06） | 出版社著作，不公開散布 |
| `research/bloom.pdf` | Krathwohl (2002) Bloom 修訂版概述，DOI 10.1207/s15430421tip4104_2 | 期刊著作；Skill 只用其結論 |

可公開、可攜式的規則應放在 `data/` 或 `references/`；可重現的去識別案例放在
`quality/examples/`。不要讓正式 Skill 依賴這個資料夾才能啟動。
