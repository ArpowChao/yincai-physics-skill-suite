# Standalone bilingual Google Flow segment prompts

Read only for Stage 3 and apply independently to every adjacent accepted image pair.

## Inspect before writing

Inspect both images for body position, gaze, expression, left/right hands, prop identity and contact, background geometry, practical lights, shadows, color temperature, camera height, 35mm perspective, subject scale, depth of field, crop, edge anchors and complete source-to-destination paths.

For live-action sequences, also compare both endpoints with the fixed photographic master for painterly drift as specified in `image-generation-qa.md`. An endpoint rejected for appearance is not an accepted reference; repair it before writing the segment prompt instead of expecting video generation to restore photography.

Infer the shortest plausible bridge containing exactly one primary visual change. Do not invent dialogue, detours, props, characters, camera moves or actions assigned to other segments.

## Output order per segment

1. `片段 K｜圖 K → 圖 K+1｜D 秒`
2. `本段唯一主要變化`
3. `分鏡動作腳本`
4. `刪除動作：無` or the removed minor beat
5. `完整英文 Prompt`
6. `完整中文 Prompt`

Both prompts must be complete standalone production prompts and contain these eight sections in this exact order.

## 1. ABSOLUTE PRIORITY RULE / 絕對優先規則

The literal first rendered frame must exactly match reference one and the literal last frame must exactly match reference two. Any mismatch fails the clip. Freeze a settled start for the first 0.5 seconds; if the start is already mid-action, continue immediately from 0.0 seconds without pause, anticipation, reset or replay.

## 2. FRAME ZERO / 第零幀

Lock body, left hand, right hand, gaze, expression, prop/contact state, every functional connection and path anchor, lighting, shadows and things that must not yet appear. End with `FRAMING LOCK` / `構圖鎖定`, naming exact left/right edge anchors, camera height and subject scale. Forbid widening, pulling back, reframing or lens changes.

## 3. FINAL FRAME / 最終幀

Lock the same categories from reference two. If unfinished, write `in progress, NOT finished` / `仍在進行中，尚未完成`. If ending during an action, write the concrete `The video ends MID-[action]` and equivalent Chinese. Never overshoot and return.

## 4. CHARACTER / 人物

Describe only visually supported identity, face, hair, build, clothing and accessories. End with `identical to references, no deviation` / `與參考圖完全相同，不得偏離`.

## 5. TIMED ACTION / 分秒動作

Use contiguous timestamp ranges that exactly fill 4, 6, 8 or 10 seconds. Bind one observable beat to each range and reach the final state only at the end. Put risky hands, reflections, sparks, smoke, liquid or particles in the middle and constrain effects with `small`, `fine`, `subtle` and `brief`. Remove an unfit minor beat instead of speeding it up. No early completion, hold, loop, redo or reverse.

## 6. CAMERA / 攝影機

Lock framing and shot size with only extremely subtle handheld micro-movement. Forbid push, pull, pan, tilt, orbit, zoom, cut, angle or lens change. Permit a tiny slow drift and ease back only when necessary to land on reference two.

## 7. LOOK / 視覺風格

Describe actual key/fill/practical directions, warm/cool tendency, environmental and shadow colors, shallow depth of field, 35mm documentary realism, natural film grain and `slightly soft focus matching the reference image sharpness`. Use explicit NOT statements against the opposite temperature or mood. Forbid flat lighting and color-grade shifts.

Keep the chosen visual medium stable through every intermediate frame. For live action, explicitly preserve photographic skin, hair, cloth, material surfaces and optical blur, with no watercolor/paint treatment, etched contours, artificial microtexture or sharpening halos. Grain must not build up over time. If a graphic overlay is requested, confine its flat style to the overlay; the underlying scene remains photographic. Include these constraints equivalently in both languages.

## 8. ABSOLUTELY FORBIDDEN / 絕對禁止

Enumerate skipping or approximating the opening; pre-roll, establishing shot, reset or completed interaction before frame zero; early ending, hold, overshoot, loop, reverse or replay; widened field of view; cuts or transitions; text, subtitles, logos or watermarks; distorted or extra/missing fingers; face, age, body, hair or clothing drift; a different key prop or location; color-grade changes; flat lighting; teleporting objects; missing supply paths; changed connector counts; swapped sockets; disappearing cables/pipes; hidden paths without stable anchors; and every story action assigned to another segment. Add only relevant excessive-effect bans such as large sparks, flames, heavy splashes or thick smoke.

## Equivalence and final checks

The Chinese version is not a summary. It must preserve every timestamp, negation, boundary, qualifier, prop, physical path and lighting constraint from English. Verify the eight headings, exact duration coverage, correct freeze rule, edge anchors, one primary change, first/last-frame match and no reliance on another segment.
