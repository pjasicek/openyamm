# Codex brief (run 2): four HD views, the bow and the arrow for the MM7 Archer (m154)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m154_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m154_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m154_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, helmet, coif, tunic, emblem, armour, quiver, colours, pose, proportions, light and style.
2. `mm7_m154_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; grey background is not part of the character). Use it for what each view
   shows (the fur quiver diagonally across the back with arrows behind his left shoulder, the back of the tunic).
3. `mm7_m154_claude/source/native_attack.png` — ORIGINAL native attack frames; for the bow and the arrow only.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("his left" means his own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | face and chest square to camera; the arrows behind his LEFT shoulder on IMAGE RIGHT |
| `02_back.png` | straight behind him | the fur quiver diagonally across the back, arrows over his LEFT shoulder on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm nearest the camera |
| `bow.png` | prop only, no person | see "Bow and arrow" below |

Generate each body view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any
residual fault.

## Prompt content for the body views (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Archer), as a 3D modelling reference. Not a new
design. ONE complete figure, helmet horns to boot soles, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1.

Identity (as in input 1): dark-skinned man; horned spiked steel helmet over a mail coif; green tunic with a white tree
emblem; gold gorget; dark steel pauldrons; mail sleeves; tan leather gloves; brown belt with a gold buckle and a
diagonal strap; olive-brown trousers and tall boots; brown fur quiver on the back with white-fletched arrows over his
LEFT shoulder.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 35 degrees from vertical, a clear gap between each arm and the body and between each
hand and the thigh. Hands empty and open, five spread fingers. Head facing forward.

Do NOT: draw the bow or an arrow in the hands, a shield, cape or cloak; change any colour; change the pose; crop the
horns or feet; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the arrows over his LEFT shoulder
on the image side the table implies; same character, proportions, pose and colours as input 1; whole figure inside the
frame, 1024 x 1536, true alpha; open empty hands.

## Bow and arrow (`bow.png`)

Production prop design for the faithful reconstruction; no person in the image. Transparent background, flat diffuse
studio light, no ground, shadow or text. Portrait 1024 x 1536. LEFT two thirds: the unstrung-looking SIDE view of the
bow, vertical, its full length uncropped: a reddish-brown wooden RECURVE bow about 1.3 m long (native frames), limbs
about 4 cm wide at the grip tapering to the tips which curve away from the string, a dark leather grip wrap in the
middle, and a thin pale string running straight from tip to tip on the LEFT side of the bow (the string side). RIGHT
third: ONE arrow, vertical, point up: a straight light wooden shaft about 0.8 m, a dark steel broadhead, white
feather fletching. No decorations, gems or engravings.
