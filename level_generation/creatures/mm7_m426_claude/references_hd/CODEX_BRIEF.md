# Codex brief (run 2): four HD views for the MM7 Warlock (m426)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m426_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m426_three_quarter_v2` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record
format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five selected views side
by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m426_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, long wavy copper-red hair, crimson sleeveless gown with gold neck cord, crossing bodice cords,
   waist band and hem band, navy cape with lavender edge, gold armbands and bracelets, bare feet, pose (right hand
   open, LEFT hand a fist with a vertical grip opening), proportions, light and render style.
2. `mm7_m426/native/m426sa0.png` — ORIGINAL native front frame (256 x 256). Its wand is NOT to be drawn.
3. `mm7_m426/native/m426sa2.png` — ORIGINAL native profile frame.
4. `mm7_m426/native/m426sa4.png` — ORIGINAL native back frame: the long hair down the back over the navy cape.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | symmetric front: face and neck cord centred, her RIGHT hand open on IMAGE LEFT, her LEFT fist on IMAGE RIGHT, cape edges behind the arms |
| `02_back.png` | straight behind her | the long copper hair down the back over the navy cape to the ankles; her LEFT fist on IMAGE LEFT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her left arm and fist nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her right arm and open hand nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Warlock), as a 3D modelling reference.
Not a new design. ONE complete figure from the ray tips to the robe hem, centred, about 80% of the canvas height,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no
scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): an athletic adult woman with very long thick wavy copper-red hair to the waist; a crimson
sleeveless floor-length gown with a fitted bodice, a thin gold cord at the neckline, two gold cords crossing the bodice,
a gold waist band and gold hem band; a long navy-blue cape with a pale lavender edge hanging behind the arms; broad
gold armbands and bracelets; bare arms and bare feet.

Pose (identical to input 1): standing upright, feet slightly apart; arms out from the body in an A-pose with air
between each arm and the body; right hand open, LEFT hand a firm fist with a vertical grip opening; both empty. Head
level.

Do NOT: draw a wand or held object; add armour, a hood, shoes or extra jewellery; change colours; let the cape or the
hair cover the arms or hands; crop the hair or the feet; add a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (hair, bare feet), true transparent background, 1024 x 1536;
- same hair, gown, gold cords and bands, cape with lavender edge and jewellery wherever the view can see them;
- right hand open, left hand a fist, both empty; no added object.
