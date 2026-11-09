# Codex brief (run 2): four HD views and the longsword for the MM7 Plate Fighter (m230)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m230_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m230_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m230_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same knight, helm, plume, armour, tabard, colours, pose, proportions, light and render style.
2. `mm7_m230_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; grey background is not part of the character). Use it for what each view
   shows (the plume down the back of the helm, the back of the tabard, the back plates).
3. `mm7_m230_claude/source/native_attack.png` — ORIGINAL native attack frames; for the longsword only.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("his right" means his own anatomical right; the tabard is GREEN on his right half):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | T visor of the helm square to camera; the GREEN half of the tabard on IMAGE LEFT |
| `02_back.png` | straight behind him | the plume down the back of the helm, the back of the tabard, back plates; the GREEN half on IMAGE RIGHT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm nearest the camera |
| `longsword.png` | prop only, no person | see "Longsword" below |

Generate each body view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any
residual fault.

## Prompt content for the body views (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Plate Fighter knight), as a 3D modelling reference.
Not a new design. ONE complete figure, plume to sabatons, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1.

Identity (as in input 1): full plate armour of polished steel with gold edge trim; flat-topped great helm with a T
visor, gold rim, gold eagle crest and a green-and-white plume; chain mail at the elbows; long tabard split green (his
right) / white (his left) with a green leaf motif; dark belt; gold knee cops.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 35 degrees from vertical, a clear gap between each arm and the body and between
each hand and the thigh. Gauntlets empty and open, five spread fingers. Helm facing forward.

Do NOT: draw a weapon, shield, cape or cloak; reveal a face; change any colour; change the pose; crop the plume or
feet; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the green tabard half on the
image side the table implies; same knight, proportions, pose and colours as input 1; whole figure inside the frame,
1024 x 1536, true alpha; open empty gauntlets.

## Longsword

Production prop design for the faithful reconstruction; no person in the image. Two large views of the SAME sword
side by side, both uncropped: the broad flat side and a three-quarter view. Transparent background, flat diffuse
studio light, no ground, shadow or text. From the native frames: a one-handed knightly longsword about 1.05 m overall;
a straight double-edged polished steel blade about 5 cm wide with a slightly WAVY (flame-like) edge outline and a
central fuller, tapering to a point; a GOLD crossguard with downturned ends; a dark grip about 14 cm with gold wire;
a round gold pommel. Restrained highlights, not chrome-white. No engravings or gems. Portrait 1024 x 1536 with the
sword vertical, tip up, in each view.
