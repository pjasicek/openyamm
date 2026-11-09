# Codex brief (run 2): four HD views for the MM7 Peasant Human1 Male (m352)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m352_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m352_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m352_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, hair, beard, clothing, colours, pose, proportions, light and render style.
2. `mm7_m352_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; the grey background is not part of the character). Use it for what each
   view shows (the long black hair falling down the back, the back of the tunic, the belt all round the waist, the
   strap end hanging at his LEFT hip, the ragged tabbed hem all round).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("his left" means his own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | face and chest square to camera; his RIGHT arm on IMAGE LEFT; the hanging belt strap end on IMAGE RIGHT |
| `02_back.png` | straight behind him | long black hair down the back, back of the tunic, belt and hem, trousers and shoes; his RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his LEFT arm and the hanging strap end nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII male human peasant), as a 3D modelling reference.
Not a new design. ONE complete figure, head to shoe soles, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): an ordinary lean adult man, light tan skin, long straight black hair past the shoulders,
black moustache and short full beard; a loose forest-green woven wool tunic to mid-thigh with a row of brass studs
round the neckline, wide three-quarter sleeves ending at mid-forearm in a studded cuff band, a ragged tabbed hem; a
studded tan-brown leather belt with a small silver buckle and a strap end hanging at his LEFT hip; close-fitting
pale grey-beige linen trousers; short brown leather ankle shoes.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 30-35 degrees from vertical, a clear gap between each arm and the body and between
each hand and the thigh. Hands empty and open, five spread fingers, palms toward the thighs. Head level.

Do NOT: put anything in the hands, add a weapon, bag, hat, hood, cape or armour; change any colour; change the
pose; crop the head or shoes; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the hanging belt strap end on
his LEFT hip on the image side the table implies; same character, proportions, pose and colours as input 1; whole
figure inside the frame, 1024 x 1536, true alpha; open empty hands.
