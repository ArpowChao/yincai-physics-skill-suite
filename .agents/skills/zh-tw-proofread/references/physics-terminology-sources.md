# 物理術語來源與證據邊界

## 查核順序

1. 先用 repo 內課綱、專案節點映射與 `data/terminology/physics-terms.json`。這些來源決定臺灣高中教材的首選詞。
2. 用教育部辭典資料確認臺灣正體字形與一般詞義。
3. 用 QUDT 核對物理量、單位、量綱與概念關係。
4. 用 UCUM 核對無歧義的機器可讀單位代碼。
5. 用 Unicode CLDR `zh_Hant` 核對繁體中文單位的顯示形式。
6. 用 `moedict-data-csld` 辨識兩岸同實異名與同名異實，不用它單獨決定首選詞。
7. QUDT 無該概念時才查 OM；將 OM 當補充本體，不當臺灣中文譯名權威。

## 固定來源

| 來源 | 用途 | 本次固定 revision |
| :--- | :--- | :--- |
| [g0v/moedict-data](https://github.com/g0v/moedict-data) | 教育部《重編國語辭典修訂本》機器可讀格式 | `a6dc997417507eb510fc29822bc514de2c92728c` |
| [QUDT](https://github.com/qudt/qudt-public-repo) | 物理量、單位、量綱、轉換與概念關係 | `6b8df6f429c45bc6fb0b25659d34f51954a148f9` |
| [UCUM](https://github.com/ucum-org/ucum) | 機器可讀單位代碼與常數 | `ef4c31cd7d3bc81de1a1bf2cc8414bf502b6304f` |
| [Unicode CLDR](https://github.com/unicode-org/cldr) | `zh_Hant` 單位顯示與本地化 | `d6061e98231c3c99c1a8b9679f67b916cf5a5128` |
| [g0v/moedict-data-csld](https://github.com/g0v/moedict-data-csld) | 兩岸詞彙差異候選證據 | `a1e91196f84cd2f3456570906191615f477278c8` |
| [OM](https://github.com/HajoRijgersberg/OM) | QUDT 以外的應用物理量與單位補充 | `0ae80866e9bc3e1d430cdeec82af8d7b019b8793` |

## 證據邊界

- 不把 GitHub 資料庫的英文 label 當成臺灣教材的正式譯名。
- 不把一般國語辭典當成物理概念定義或課綱範圍證據。
- 不把兩岸差異詞庫中的所有臺灣詞都當成本專案首選詞。
- 外部來源與 repo 正式資料衝突時，保留 repo 詞並在修訂表列出衝突；若 repo 本身也有衝突，標記 `待確認`。
- 離線時可用 repo 內資料繼續，但不得宣稱已核對未快取的外部詞條。

## 授權與再利用

- 本 reference 只保存來源資訊、用途與 revision，不重製整份外部詞庫。
- `moedict-data` 的辭典本文權利仍屬教育部；`moedict-data-csld` 的原始內容與 g0v 格式編排不是同一授權層。
- QUDT、UCUM、CLDR 與 OM 各有自身授權；若未來要把上游詞條或定義實際納入 repo，必須在匯入前逐一查核並保留歸屬。
