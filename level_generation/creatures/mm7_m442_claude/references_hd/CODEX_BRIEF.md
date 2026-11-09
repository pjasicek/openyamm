# Codex brief (run 2): four HD views for the MM7 Peasant Goblin Female (m442)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m442_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m442_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m442_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, face, hair, clothing, colours, pose, proportions, light and render style.
2. `mm7_m442_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; the grey background is not part of the character). Use it for what each
   view shows (the ponytail and red ribbon from behind, the purple-and-white striped back of the vest, the sash all round
   the waist, the white lacing down the OUTER side of each trouser leg, the boots' front lacing). Her sickle is NOT
   drawn: hands stay empty.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face and chest square to camera; her RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind her | ponytail and ribbon, back of the vest, sash, trousers and boots; her RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII female goblin villager), as a 3D modelling reference.
Not a new design. ONE complete figure, head to shoe soles, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): adult goblin woman, sturdy, olive-green skin, pointed ears, long narrow nose; near-black
high ponytail tied with a red ribbon with stiff pointed ends; sleeveless purple vest with broad white stripes, white
trim and brass toggles over a cream blouse with very wide hanging sleeves; cream waist sash; purple knee trousers with
white criss-cross lacing down the outer sides and white knee cuffs; tall brown boots laced up the front with brass
eyelets.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 30-35 degrees from vertical, a clear gap between each arm and the body and between
each hand and the thigh. Hands empty and open, five spread fingers, palms toward the body. Head level.

Do NOT: put anything in the hands (no sickle), add a hat, cape or armour; change any colour; change the pose;
crop the head or shoes; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); same character, proportions, pose and colours as input 1; whole
figure inside the frame, 1024 x 1536, true alpha; open empty hands.

## Prop reference (one more image, after the four views)

`sickle.png`: 1024 x 1536 portrait, true transparent background, the prop ALONE (no hand, no person): her small farm
sickle from the native frames (input 2 shows it in her right hand in the standing views; the native sprite draws one
slim curved crescent SILVER steel blade on a short dark wooden handle). Exact flat side view, orthographic: the
straight handle VERTICAL at the bottom of the image, centred, about 12 cm long with a small brass ferrule where the
blade tang enters it; the crescent blade rising from the top of the handle and curving round to the RIGHT and back
over, its sharp edge on the INNER (concave) side, the tip pointing back toward the handle's axis, the whole crescent
about 30 cm across. Fill the frame height with the prop (generous margins). Even flat light, no shadow, no text.
Checks: one sickle only, handle vertical at the bottom, crescent opening to the right, true alpha, nothing cropped.
