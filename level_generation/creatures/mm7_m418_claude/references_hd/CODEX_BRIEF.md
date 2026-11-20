# Codex brief (run 2): four HD front/back/side views for the MM7 Troglodyte (m418)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m418_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m418_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m418_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m418_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same troglodyte, hood-head, maw and teeth, spines, blue pattern, arms with three claws, legs, tail, colours,
   pose, proportions, light and render style.
2. `mm7_m418/native/m418sa0.png` — ORIGINAL native front.
3. `mm7_m418/native/m418sa2.png` — ORIGINAL native right profile (hunch, spines, tail).
4. `mm7_m418/native/m418sa4.png` — ORIGINAL native back (spine row, tail).

## Deliverables (1536 x 1024 LANDSCAPE like input 1, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | the maw and hood rim; its RIGHT arm on IMAGE LEFT; the tail hidden behind |
| `02_back.png` | straight behind it | the spine row down the back, the tail toward the camera; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same troglodyte as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Troglodyte monster), as a 3D modelling reference. Not
a new design. ONE complete creature, spine tips to toe claws and tail tip, centred, generous margins, near-orthographic
camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio
light, same render style and materials as input 1.

Identity (as in input 1): a squat hunched reptilian biped; a very large rounded armoured hood-like head merged into a
high arched back (no neck), a wide maw of ivory pointed teeth under the forward hood rim with a narrow cyan-blue rim,
no eyes; a row of pointed dorsal spines from the hood top down the back and tail; olive-green fine scales; vivid
cyan-blue stripes on the hood and patches on the flanks with purple mottling; dark segmented throat and belly; long
thin arms with three long pale claws per hand; bent scaly legs with pale toe claws; a long thin tapering tail.

Pose (identical in all views, as in input 1): crouched on the two bent legs with the feet apart; the body leaning
forward; the arms hanging down and forward with a gap from the body and legs; claws slightly spread; the tail
extended back. Hood-head facing forward.

Do NOT: add eyes, horns, wings, armour, weapons or effects; change the colours or the blue pattern; change the pose;
crop the tail, spines or claws; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same creature, proportions, pose and colours as input 1;
- whole creature including the tail tip inside the frame with margins, true transparent background, 1536 x 1024;
- three claws per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the body and legs, the whole tail is visible behind.
