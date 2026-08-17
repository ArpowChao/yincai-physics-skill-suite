# 英文術語與 ECDICT 來源政策

## 證據優先序

英文術語、縮寫與識別字依下列順序判定：

1. 論文原文、官方產品文件、標準組織資料庫等第一手來源。
2. 臺灣官方或學術術語來源，例如教育部辭典、國家教育研究院雙語詞彙。
3. 使用者確認的專案詞表或既有正式教材。
4. ECDICT 的英文詞目、詞形與中譯候選。

低順位來源不得推翻高順位來源。只有 ECDICT 命中時，不得自動取代逐字稿。

## ECDICT 快照

- Repository: <https://github.com/skywind3000/ECDICT>
- 使用時核對的 revision: `bc015ed2e24a7abef49fc6dbbb7fe32c1dadaf8b`
- License: MIT
- 主要資料檔：UTF-8 CSV，常用欄位包含 `word`、`phonetic`、`definition`、
  `translation`、`pos`、`exchange`。

本專案不內嵌或重新散布完整 ECDICT。使用者可自行下載上游 CSV，透過
`scripts/check_ecdict_terms.py` 在本機做唯讀查核；工具報告會保留來源網址、revision
與授權資訊，方便日後追溯。

## 可用與不可用範圍

ECDICT 可用來：

- 找英文一般詞的正字、常見大小寫差異與去標點後的近似詞目。
- 提供詞性、音標、詞形與中譯候選，協助發現 ASR 可能誤辨的片段。
- 將未命中的英數混合詞列為待確認項目。

ECDICT 不可單獨用來：

- 決定基因、蛋白質、化合物、菌株、儀器型號、品牌、人名或縮寫的正式寫法。
- 把英文中譯直接當成臺灣標準術語；ECDICT 中譯可能使用簡體中文或中國慣用詞。
- 將 `normalized` 模糊命中視為同一專有名詞，或在未取得證據時改變大小寫、連字號、
  數字、希臘字母及上下標。

例如 `algorithm` 可用 ECDICT 確認英文一般詞的拼法，但其中文仍應依臺灣語境選用
「演算法」。`PepTSh`、`3M3SH`、`S-Cys-Gly-3M3SH` 則應回查論文或官方資料；
`not-found` 只表示字典沒有詞目，不等於原稿錯誤。

## 查核程序

1. 先保留原始逐字稿，不直接覆寫。
2. 若有 ECDICT CSV，執行：

   ```powershell
   python scripts/check_ecdict_terms.py transcript.txt C:\path\to\ecdict.csv `
     --output outputs\ecdict-candidates.json
   ```

3. 優先處理 `not-found`、`case-variant` 與 `normalized`；逐項查找第一手來源。
4. 確認後才修改逐字稿，並在修訂對照表寫明實際來源。未確認項目保留原詞並標註
   「待確認」。
5. SRT/VTT 的序號與時間軸不得因術語查核而更動。
