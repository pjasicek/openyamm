# Codex brief (run 2): four HD front/back/side views for the MM7 Gargoyle (m234)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m234_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m234_three_quarter_v2` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/` (`m234_front_v1.png`,
...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m234_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same gargoyle, head, horns, ears, eyes, stone skin, claws, digitigrade legs, tail, wings, colours, pose,
   proportions, light and render style.
2. `mm7_m234/native/m234sa0.png` — ORIGINAL native front.
3. `mm7_m234/native/m234sa2.png` — ORIGINAL native side profile.
4. `mm7_m234/native/m234sa4.png` — ORIGINAL native back (wing membranes from behind, tail root).

## Deliverables (1536 x 1024 landscape, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, chest, both wings spread symmetrically behind; its RIGHT arm on IMAGE LEFT; the tail behind the legs |
| `02_back.png` | straight behind it | back of the head and horns, the back with the wing roots on the shoulder blades and the backs of both membranes, the tail root at the base of the spine; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera; the digitigrade leg shape (raised heel); the wings rise behind its back; the tail hangs behind |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera; the wings rise behind its back; the tail hangs behind |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in vein patterns or stone speckle.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same stone gargoyle as input
1 (a faithful HD reconstruction of the existing Might and Magic VII Gargoyle monster), as a 3D modelling reference. Not
a new design. ONE complete figure, horn tips to toe claws, both wings to their tips and the whole tail, centred,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery,
no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a lean muscular demonic humanoid of slate-grey weathered stone with fine cracks; a bestial
muzzle with small fangs, small red eyes, pointed ears, two large ram horns curling back; no clothing, smooth groin;
clawed hands with five digits and long dark talons; digitigrade legs with raised heels and three long clawed toes; a
long thin whip tail ending in a small arrowhead tip; two large bat wings on the upper back with dark bony struts, a
hooked wrist claw and green veined membranes with a scalloped trailing edge.

Pose (identical in all views, as in input 1): standing upright on the toes with the heels raised, legs nearly straight
and apart with a clear gap between the legs and feet. Arms hanging down and out to the sides, elbows very slightly
bent, a clear gap of air between each arm and the body; hands open, claws spread, palms facing the thighs. Head level,
looking forward. Wings spread and raised in a high open V exactly as in input 1. Tail hanging behind the legs, its tip
on the ground plane.

Do NOT: add armour, clothing, weapons or jewellery; add extra horns, limbs or wings; give it human feet; change the
colours; change the pose (no turned head, no raised arm, no folded wings); crop the wing tips, horns, tail or feet; add
a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same figure, proportions, pose, wings, tail and colours as input 1;
- whole figure, wing tips and tail tip inside the frame with margins, true transparent background, 1536 x 1024;
- five clawed digits per hand wherever visible; digitigrade legs;
- in profile, the arm nearest the camera hangs clear of the torso; the wings sit behind the back;
- in the front and back views the wings are symmetric and attached at the shoulder blades.
