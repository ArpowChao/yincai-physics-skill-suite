# TTS end-to-end workflow

只在作者選擇 TTS 或兩種都做後進入此分支。

## 1. Inventory and timing map

1. 保留原始影片、AI 影片、逐字稿、SRT/VTT 與未切 TTS。
2. 用 `ffprobe` 記錄所有串流、時長、幀率、sample rate 與聲道。
3. 在全片影音錨點表列出每頁、句子、動畫、AI、題目、答案、固定停留與最後一句。
4. 告知作者頁尾預設 0.5 秒，詢問是否改為 0.15 秒或其他值並記錄。

## 2. Prepare TTS assets

1. 逐頁或按最小視覺單位管理音檔，不用一條長 TTS 當最終對齊單位。
2. 需要逐字稿校正時使用 `$zh-tw-proofread`；需要多音字、公式或配音替代字時使用 `$prepare-tts-transcript`。
3. 保留自然生成速度；字級時間戳只作搜尋錨點。
4. 解碼 48 kHz PCM，保留未切來源供逐頁與結尾比對。

## 3. Safe page boundaries

上一頁保留最後音素、release、breath 與完整衰減後，找 stable silence 內的低振幅零交叉；不使用機械 fade-out。下一頁移除多餘開頭空白，但保留完整第一音素，在其前找零交叉並加入預設 12 ms 淡入。

manifest 記錄候選時間、snapped sample／時間、調整量、上一頁 stable-silence onset 與下一頁 stable-silence end。

## 4. Rebuild pages

1. 移除安全邊界間的來源空白。
2. 完整尾音後只加入一次固定停留；預設 0.5 秒，作者可明確改為 0.15 秒或其他值。
3. 依完整 TTS 加固定停留重建畫面，不拉伸自然 TTS。
4. 畫面硬切；下一頁畫面出現後 TTS 才淡入。
5. 動畫在對應概念開始發音時出現。

## 5. AI and checkpoints

- AI 影片保持 1.0x，只播放指定原聲；TTS bus 在 AI 區間必須 sample-level 靜音。
- 題目尾音後移除相鄰來源空白，未作答 frame 3 秒，答案 frame 3 秒。
- 成品在相對 2.9 秒與 3.1 秒抽 frame，並量測約六秒靜音。

## 6. Review and master

先輸出 alignment review，逐頁確認尾字、第一音素、動畫、AI 與檢核點；作者批准後才調音。TTS 與每個 AI clip 分別平衡，最後目標為 48 kHz AAC、`I=-14 LUFS`、`TP<=-1.5 dBTP`、`LRA=3–5 LU`。

## 7. Release audit

- 逐頁比對未切 TTS，確認完整尾音、單次停留、12 ms 淡入與畫面硬切。
- 確認 AI 區間完全沒有 TTS，且 AI 原聲保持原速。
- 最後一句一路聽到 EOF；「bye bye」兩字與最後衰減都要通過 AAC。
- 比較版以 `_0.5秒`、`_0.15秒` 等名稱分開，不覆蓋作者保留版本。
