# Codex brief (run 2): four HD views for the MM7 Peasant Human1 Female (m342)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m342_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m342_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m342_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, face, hair, clothing, colours, pose, proportions, light and render style.
2. `mm7_m342_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; the grey background is not part of the character). Use it for what each
   view shows (the long chestnut hair down the back, the back of the bodice and its lacing, the belt all round the waist,
   the sheathed dagger hanging at her LEFT hip, the white petticoat hem all round).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face and chest square to camera; her RIGHT arm on IMAGE LEFT; the sheathed dagger on IMAGE RIGHT |
| `02_back.png` | straight behind her | long hair down the back, back of the bodice, belt, skirt and petticoat; her RIGHT arm on IMAGE RIGHT; the dagger on IMAGE LEFT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm and the sheathed dagger nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII female human peasant), as a 3D modelling reference.
Not a new design. ONE complete figure, head to shoe soles, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): adult woman, light skin, long wavy chestnut-brown hair, gold hoop earrings; white
off-the-shoulder blouse with full puffed sleeves gathered below the elbow into ruffled cuffs, bare forearms; fitted
forest-green bodice with shoulder straps, laced up the front through gold eyelets; long forest-green skirt to the
ankles with a narrow front split showing a white underskirt and a white ruffled petticoat hem below; black belt with
a square gold buckle; a dagger in a black scabbard with gold fittings hanging from the belt at her LEFT hip; black
flat shoes.

Pose (identical in all views, as in input 1): neutral A-pose, upright, feet slightly apart under the skirt, flat. Arms out at about 30-35 degrees from vertical, a clear gap between each arm and the body and between
each hand and the skirt. Hands empty and open, five spread fingers, palms toward the body. Head level.

Do NOT: put anything in the hands, add an apron, shawl, hat, headscarf or cape; change any colour; change the pose;
crop the head or shoes; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the sheathed dagger on her LEFT hip on the image side the table implies; same character, proportions, pose and colours as input 1; whole
figure inside the frame, 1024 x 1536, true alpha; open empty hands.
