# Codex brief (run 2): four HD views for the MM7 Monk (m290)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m290_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m290_three_quarter_v2` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record
format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five selected views side
by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m290_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, hood up, forest-green wool robe with the draped cowl, wide sleeves, white knotted rope belt with
   tasselled ends, sandals, pose (A-pose, both hands open), proportions, light and render style.
2. `mm7_m290/native/m290sa0.png` — ORIGINAL native front frame (256 x 256).
3. `mm7_m290/native/m290sa2.png` — ORIGINAL native profile frame.
4. `mm7_m290/native/m290sa4.png` — ORIGINAL native back frame: the hood and the robe back.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | symmetric front: face in the hood, rope knot and ends centred, both arms out with open hands |
| `02_back.png` | straight behind him | the hood from behind, the cowl and the robe back to the hem; his LEFT hand on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Monk), as a 3D modelling reference.
Not a new design. ONE complete figure from the ray tips to the robe hem, centred, about 80% of the canvas height,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no
scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a lean adult man, clean-shaven, light skin; a deep forest-green hood worn up with a pale
inner edge; a draped green cowl over the shoulders; a loose floor-length forest-green wool robe with very wide long
sleeves; a white twisted rope belt knotted at the waist with two tasselled ends hanging to the knees; dark sandals.

Pose (identical to input 1): standing upright, feet slightly apart; arms out from the body in an A-pose with air between
each arm/sleeve and the body; both hands open and empty, out of the sleeves. Head level.

Do NOT: draw any held object; take the hood down; add armour or jewellery; change colours; let the sleeves cover the
hands; crop the hood or the feet; add a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (hood, feet), true transparent background, 1024 x 1536;
- same hood, cowl, robe, sleeves, rope belt and sandals wherever the view can see them;
- both hands open and empty; no added object.
