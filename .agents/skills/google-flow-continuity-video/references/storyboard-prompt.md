# Stage 2 storyboard prompt contract

Read only for Stage 2. Deliver one copy-ready Traditional Chinese prompt with every value filled. It must contain these sections.

## Required prompt structure

1. State that the user is making a connected Google Flow Omni short film and request the derived number of separate 16:9 images, never a grid, collage or storyboard sheet.
2. `【我的故事】` — the confirmed observable story.
3. `【固定連戲設定】` — character, clothing, scene/time, key props, physical connections, lighting and fixed camera/edge anchors.
4. `【自動切段計畫】` — total segments and frames, then each `圖片 K → 圖片 K+1`, its single primary change, exact start/end states and duration.
5. Detailed generation rules and a post-generation audit.

## Required rules inside the prompt

- Every image is an exact handoff state; use a mid-action boundary or stable causal checkpoint as planned.
- All frames depict the same identities, clothing, room, props, camera, crop and unaffected lighting.
- Between adjacent images only the assigned delta may change.
- Default to natural live-action camera photographs, 35mm perspective, shallow depth of field and 16:9; honor another medium only when explicitly requested. Keep grain and sharpness at the accepted master level rather than adding texture with each edit.
- For live action, name the fixed photographic master separately from the preceding frame's pose/prop reference and require both on each edit where supported. Keep natural skin, hair, cloth and optical blur; reject watercolor/paint patches, etched microtexture and cumulative stylization even when objects and poses match. Apply the detailed acceptance and recovery checks in `image-generation-qa.md`.
- A requested thought cloud or other graphic may be flat; its style must not spread to the underlying person or environment.
- No text, subtitles, brands, logos or watermarks inside images.
- Before generation, list each frame's pose, left/right hands, prop state, functional connections, lighting, shot distance, left-edge anchor and right-edge anchor.
- After generation, audit identity, hands, props, camera, color, dimensions, every physical path and photographic appearance against both the preceding accepted frame and the fixed master. Stop propagation and repair failing frames before delivery; prompt wording alone is not evidence that the style stayed photographic.

## Physical-path contract

For every functional system, explicitly record:

- source
- intermediate connection points
- load or destination
- exact number and type of cables, plugs, sockets, pipes or hoses
- visible entry/exit anchor for any hidden portion

For electrical scenes, distinguish each appliance lead from the extension strip's own mains lead. Define which plug occupies which top-facing socket and which sockets remain empty. Forbid side/end sockets unless the real prop explicitly has them. Wires may not disappear, fuse, cross-swap, pierce furniture or change exit points.

For smoke or fluid, define the one physical source and slow path. Do not let the effect originate from a frame edge, detector, ceiling or unrelated object.

## Execution note

When this agent has an image-generation/editing tool, the text prompt may request the full set, but the agent should execute strict-continuity images sequentially according to `image-generation-qa.md`. Do not claim images were generated when only a prompt was produced.
