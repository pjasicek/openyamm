# Codex brief (run 2): four HD views for the MM7 Mage (m274)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m274_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m274_three_quarter_v2` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record
format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five selected views side
by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m274_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, ginger beard with two braids, receding ginger hair, magenta horned collar, gold pointed yoke, green
   robe with gold trim and darker green underrobe, wide sleeves, gold belt with red gem, magenta star-and-moon cape,
   brown shoes, pose (right hand open, LEFT hand a fist with a vertical grip opening), proportions, light and style.
2. `mm7_m274/native/m274sa0.png` — ORIGINAL native front frame (256 x 256). Its staff is NOT to be drawn.
3. `mm7_m274/native/m274sa2.png` — ORIGINAL native profile frame.
4. `mm7_m274/native/m274sa4.png` — ORIGINAL native back frame: the magenta cape with darker stars and crescent moons,
   the collar horns and the gold yoke from behind.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | symmetric front: beard centred, belt gem centred, the RIGHT hand open on IMAGE LEFT, the LEFT fist on IMAGE RIGHT, cape edges behind the arms |
| `02_back.png` | straight behind him | the magenta cape with stars and crescent moons from the yoke to the hem, the collar horns, the back of the head; his LEFT fist on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm and fist nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm and open hand nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Mage), as a 3D modelling reference.
Not a new design. ONE complete figure from the ray tips to the robe hem, centred, about 80% of the canvas height,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no
scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a broad middle-aged man with a very long thick ginger-orange beard to the belt with two thin
braids, receding swept-back ginger hair; a tall magenta stand-up collar rising into two pointed horn tips beside the
head, a broad gold pointed shoulder yoke; a forest-green robe to the ankles with broad gold trim on the front edges and
hem, open over a darker green underrobe, wide bell sleeves with gold cuff trim; a broad gold belt with a round gold
medallion and a large red gem; a magenta cape with darker stars and crescent moons and a gold hem band hanging behind
the arms; brown shoes; bare hands.

Pose (identical to input 1): standing upright, legs slightly apart; arms out from the body in an A-pose with air between
each arm and the body; right hand open, LEFT hand a firm fist with a vertical grip opening; both hands empty. Head level.

Do NOT: draw a staff or held object; add a hat, hood or armour; change colours; let the cape cover the arms or hands;
crop the collar horns or the feet; add a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (collar horns, feet), true transparent background, 1024 x 1536;
- same beard, collar, yoke, robe, trim, belt gem, cape pattern and shoes wherever the view can see them;
- right hand open, left hand a fist, both empty; no added object.
