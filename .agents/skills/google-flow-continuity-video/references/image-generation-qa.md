# Sequential image generation and visual QA

Read only when the user asks the agent to create or repair storyboard images.

## Generate from one accepted lineage

1. Choose or create the opening frame and establish the intended visual medium.
2. Inspect it at original detail before accepting it. For live action, register a fixed photographic master using the appearance checks below.
3. Save it as a new version in the project output folder.
4. Generate the next frame by editing the last accepted boundary frame, not by starting a fresh unrelated image. For live action, also supply the fixed photographic master as a separate appearance reference on every edit; deduplicate when they are the same file.
5. In the edit prompt, list the exact permitted delta first, label each reference's role, then lock unaffected regions and states. Include the concise photographic lock below rather than repeatedly expanding a long list of adjectives.
6. Inspect the result before producing any later frame.
7. If it fails, repair that frame from the last accepted source. Never propagate a failed frame.

Before each live-action generation call, record the exact reference paths. Frame 2 may use the master alone because the master is also its preceding boundary. Frame 3 and every later generated frame must attach both (a) the unchanged photographic master and (b) the immediately preceding accepted boundary. If the tool tends to privilege the first reference, place the fixed master first and explicitly assign the later reference to pose and story state. If the call contains only the newest generated frame, stop before generation: recursive full-frame re-rendering accumulates color and material drift even when the text prompt requests preservation.

When the final frame requires a large pose change that makes direct editing unstable, use the nearest accepted frame plus explicit identity/camera/prop references. Preserve the same lineage and re-audit all invariants.

## Prevent cumulative photographic drift

These checks apply to live-action sequences; preserve an explicitly requested illustrated medium instead of imposing photography on it.

### Fixed master and reference roles

- Select the earliest inspected frame with natural camera rendering and compatible identity, lighting and framing. Keep its file fixed across edits; do not silently replace it with the newest generated frame.
- The last accepted boundary frame controls current pose, prop design, labels, geometry and story state. The photographic master controls only the rendering of skin, hair, cloth, surfaces, light and optical blur. If later user changes supersede old props or lettering in the master, explicitly forbid copying those old details.
- A frame rejected for appearance cannot serve as an appearance master. A technically obsolete image may support photographic texture only if that aspect was separately inspected and accepted; record this limited role and never use its rejected content as a boundary state.
- Where multiple references are supported, attach both images, not just a textual claim to match the original. If unavailable, use the cleanest accepted source within the lineage and explain the limitation when it affects delivery. Do not switch tools or use local compositing outside existing authorization/tool rules.

Suggested concise edit clause (translate into the prompt's language):

> Reference A controls the current scene and the specified pose change. Reference B controls original camera rendering only. Preserve natural skin variation, individual hair strands, cotton folds, subdued wood grain and smooth optical background blur. No painted patches, brushwork, etched or worm-like contours, plastic skin or sharpening halos. Do not copy obsolete props or text from B. Keep exposure, color and camera framing fixed.

Do not use repeated sharpening, added grain or claims such as "8K/ultra detailed" as a repair for painterly texture. More apparent detail is not evidence of photographic realism.

### Compare before accepting each frame

Inspect at original resolution, using matching regions in the candidate, preceding accepted frame AND fixed master. Also inspect at normal viewing size for the overall photographic impression. Check at least:

| Region | Acceptable camera appearance | Reject |
|---|---|---|
| Face and hands | Natural, irregular skin variation and continuous tonal shading | Watercolor patches, waxy smoothing, repeated pores, contour scribbles |
| Hair and shirt | Plausible strands, cotton and folds at the original sharpness | Brush-like clumps, carved outlines, invented fibrous networks |
| Desk and wall | Subdued material detail and smooth optical blur | Crawling/etched wood patterns, canvas texture, mosaic-like wall patches |
| Book and product label | Current user-approved detail/readability and physical orientation | Fake microtexture or sharpening substituted for printed detail |

Judge material texture separately from face identity, pose, text and framing. A frame that passes continuity but looks painted still fails. Check cumulative change against the master even if the difference from the immediately preceding frame seems small. Matching file dimensions does not prove visual quality or pixel equality.

For each candidate, record source boundary, fixed master, permitted delta, appearance pass/fail and the visible defect if any. Do not claim "restored realism" or "unchanged pixels" merely because the prompt requested them or the small preview looks good.

Treat a visible trend across frames as a failure even when each adjacent change looks modest. Compare frames 1, 2 and the candidate side by side at the same display scale. If skin becomes flatter or blotchier, hair clumps become brush-like, white fabric loses natural folds, or desk/wall color progressively shifts, reject the earliest frame where the trend becomes visible and invalidate all descendants.

### Recovery and bounded retries

On drift, stop the dependent chain immediately. Recheck the earlier boundary; use the most recent one that still passes appearance QA together with the fixed master. Retry only the failing frame, with the specific observed defect addressed. Never sharpen the failed output and feed it forward.

If two targeted repair attempts still fail the appearance check, stop that repair chain, retain clearly marked candidates and report the concrete limitation. Do not generate dependent frames or call the sequence finished. An already-authorized viable alternative may continue; elapsed retries do not authorize a tool switch or a change of visual medium.

If the user reports watercolor or illustration drift in previously delivered frames, treat the affected frames and downstream descendants as needing reinspection, acknowledge the failed quality check, and correct from the clean lineage. Preserve earlier frames that still pass.

### Graphic overlays

A thought cloud, arrow or other requested flat graphic is a separate visual layer. Its allowed stylization is confined to that region; the person and environment must remain photographic. Prefer a localized edit and recheck the underlying photo afterward. Use deterministic compositing only when explicitly allowed by the active tool rules and user authorization.

## Delta matrix

Before generation create a compact matrix with one row per frame and columns for:

- character pose, left hand, right hand, gaze and expression
- each prop's state
- every indicator or practical light
- plug/socket assignment and cable path
- room lighting and exposure
- camera/crop/edge anchors
- intended medium, fixed photographic master and appearance-QA status

Mark each transition's permitted delta. Anything not marked must remain unchanged.

## Electrical topology audit

Trace every device separately:

`appliance body → its one appliance cord → its one plug → assigned socket → extension strip → strip's one mains lead → wall receptacle`

Verify:

- every appliance has exactly one cord unless the real design requires otherwise
- every visible plug belongs to one traceable cord
- socket positions and occupancy match the plan
- the strip's supply cable is not mistaken for an appliance cord
- there are no side sockets, duplicate plugs, adapters or unexplained branches
- cords do not disappear behind an object without the same visible entry/exit anchor
- ON/OFF indicators agree with the wiring and protective-switch state

Reject visually attractive frames that fail topology.

## Lighting and prop-design locks

Electrical state changes do not authorize a new light source or global exposure change. If a local device glow changes, preserve the device grille, internal structure, dimensions and orientation. Change only the existing small glow region; do not invent tubes, coils, vertical light bars or a redesigned prop.

After a trip or outage, specify which practical lights lose power and which independent ambient sources remain. Lock face illumination to those real sources; do not allow unexplained fill from the dark side.

## Effects and transitions

Default to no sparks, smoke, fire, explosion or full-room blackout unless the story requires them. A protective trip is normally shown by a switch/button state and indicator lights turning off. Forbid dissolve, crossfade, morphing, object redesign and global brightness interpolation between reference states.

## Economy and stopping condition

Generate one candidate, inspect it, and state the exact defect before retrying. Repair only the failed frame. Do not regenerate accepted earlier frames because a later frame failed. Preserve all prior versions so the user can compare and revert.

Do not declare success from the generation preview alone. Confirm image dimensions, visual continuity and physical topology first.
