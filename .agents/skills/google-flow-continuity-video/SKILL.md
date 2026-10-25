---
name: google-flow-continuity-video
description: Use when completing AI-video stories, automatically segmenting visible actions, creating continuity-locked storyboard prompts or images, or writing standalone bilingual Google Flow Gemini Omni/Omni Flash prompts for adjacent start/end reference frames; do not use for unrelated video editors.
---

# Google Flow Continuity Video

Build a reliable connected short film through gated stages. Communicate in the user's language; default to Traditional Chinese. Every confirmed detail becomes canonical until the user changes it.

## Inputs

- A story idea or confirmed observable story, plus any supplied character, scene and ending constraints.
- Existing continuity state and accepted reference images, when continuing a sequence.
- Available image-generation/editing tools if images are requested; actual video generation also requires the user's Google Flow access. This Skill supplies production rules, not credentials or a Flow automation client.
- At least two inspected chronological boundary images before Stage 3.

Save generated assets under `outputs/google-flow/` in a new story folder. Preserve earlier versions and record accepted reference filenames; generated images and videos stay local.

## Workflow

### Maintain workflow state

Infer the furthest completed stage from the conversation. Do not restart confirmed work or regenerate accepted assets unless the user requests it.

Maintain a compact continuity bible:

- character identity, age, face, hair, build, clothing and accessories
- location, time, fixed camera, crop and edge anchors
- key props and their exact geometry
- lighting sources, direction, color temperature and powered/unpowered states
- ordered visible event chain and intended ending
- segment plan, frame count and each segment duration
- physical source-to-destination paths, connector counts and visible hidden-path anchors
- accepted reference file for every frame
- intended visual medium and a fixed, inspected photographic master for live-action sequences; record its role separately from each frame's pose/prop reference

When the protagonist is unspecified, prefer one high-school student when plausible. Preserve any protagonist the user explicitly supplies.

Default to natural live-action photography unless the user explicitly chooses another medium. Keep that medium consistent across the entire sequence. A requested graphic overlay such as a question-mark cloud does not authorize turning the underlying photograph into an illustration.

### Stage 1 — Complete and confirm the observable story

Express who, where, what visibly happens and how it ends in one to three sentences. Keep one continuous location unless the user explicitly requests a scene or time change.

Resolve narrative semantics before planning images:

- If the educational point is a past accident, normally show the past accident itself rather than only a present-day worried expression.
- If the user explicitly wants recollection conveyed by narration or acting, keep the present scene and do not invent a flashback.
- Never silently replace a requested visible incident with narration, or invent a flashback when it was forbidden.

Output `步驟 1｜故事確認`, the polished story, and a short continuity setting. Stop for confirmation unless the user has already clearly approved the story.

### Stage 2 — Analyze complexity and plan storyboard images

After confirmation, read [references/segmentation.md](references/segmentation.md). Derive the smallest reliable number of segments; for `S` segments require `S+1` chronological boundary images. Each segment owns exactly one primary visual state change and independently uses 4, 6, 8 or 10 seconds.

Then read [references/storyboard-prompt.md](references/storyboard-prompt.md) and produce one complete Traditional Chinese storyboard prompt with no placeholders. Before the copy-ready prompt, show the complexity plan: start state, one primary change, end state, risk and duration for every segment.

If the user asks this agent to generate images, also read [references/image-generation-qa.md](references/image-generation-qa.md). Generate and inspect frames sequentially within one accepted lineage. For every live-action edit after the master, the actual image-generation call must include the fixed photographic master as an image reference; after frame 2 it must also include the preceding accepted boundary as a separate image reference. A prompt that merely says "match the master" does not satisfy this requirement. Do not generate a strict-continuity batch as unrelated images or rely on successive edits alone to preserve realism.

### Stage 3 — Create segment scripts and Flow prompts

Proceed only when at least two chronological images are available and actually inspected. For `N` accepted images, create `N-1` independent prompts from adjacent pairs only.

Read [references/video-prompt-spec.md](references/video-prompt-spec.md). For every pair:

1. state the one primary visual change
2. write a short physical motion bridge
3. report removed actions or `刪除動作：無`
4. output a complete standalone English prompt
5. output a semantically identical standalone Traditional Chinese prompt

Never rely on a previous segment's wording. Explicitly forbid actions assigned to earlier or later segments.

### Quality gate

Do not deliver or propagate a frame until all relevant checks pass:

- same identity, clothing, location, fixed camera, crop, prop design and unaffected lighting
- only the planned delta changed between adjacent frames
- functional systems trace from source through every connector to destination/load
- cable/socket counts, routes and anchors remain consistent
- no distorted hands, duplicate cords, side sockets, floating plugs or self-powered devices
- no unintended transition, dissolve, morph, global exposure shift or color-grade drift
- same visual medium and photographic material quality as the fixed master; no watercolor/paint-like patches, etched microtexture or cumulative loss of real skin, hair, cloth and background detail
- frame dimensions and aspect ratio match the accepted sequence
- first and last states are visually unambiguous

If a frame fails, repair only that frame from the last reference that passes both continuity and appearance checks, plus the fixed photographic master where applicable. Never use a failed frame as the source for later generation. Preserve prior files and save repaired variants with incremented versions. A user's report of painterly drift reopens appearance QA for that frame and its descendants; do not keep treating them as accepted.


## Output contract

- Stage 1: polished story, continuity settings and explicit confirmation checkpoint.
- Stage 2: complexity plan, per-segment duration, `S+1` boundary frames for `S` segments and one complete Traditional Chinese storyboard prompt. If generating images, also save the delta matrix and per-frame continuity/appearance QA, including the accepted lineage and fixed master.
- Stage 3: `N-1` prompts for `N` accepted chronological images; each segment includes its one change, motion bridge, removed actions and complete equivalent English/Traditional Chinese prompts in the eight-section format.
- Record strengths worth preserving and concrete findings. Use `PASS` only for the completed stage's inspected deliverables, `REVISE` for repairable continuity/appearance or prompt defects, and `HOLD` when required inputs, confirmation or inspection are unavailable. Story approval and final publication remain human decisions.

## Stop conditions

- Stop at story confirmation unless approval is already explicit; do not restart accepted stages.
- Hold Stage 3 until both adjacent endpoints have been inspected and accepted.
- Stop dependent generation when a frame fails continuity or appearance QA. Follow the bounded repair limit in [references/image-generation-qa.md](references/image-generation-qa.md); never propagate a failed frame.
- If requested image generation or inspection is unavailable, report that limitation and hold the dependent stage. Do not claim generated or accepted media from prompt text alone.

## Common mistakes

- Generating unrelated images as a batch, or using successive edits without the fixed photographic master.
- Treating matching poses as sufficient while photographic materials drift into illustration.
- Combining activation, a protective trip and a person's reaction into one primary state change.
- Inventing a flashback, scene change, camera move or extra action that the user did not approve.
- Writing a Chinese summary instead of an equivalent standalone prompt, or relying on a previous segment's wording.
