# Codex brief (run 2): four HD views for the MM7 Peasant Human2 Female (m372)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m372_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m372_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m372_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, face, veil, gown, sleeves, colours, pose, proportions, light and render style.
2. `mm7_m372_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; the grey background is not part of the character). Use it for what each
   view shows (the veil hanging down the back to the shoulder blades, the back of the gown, the bell sleeves from
   behind, the gold cord belt all round the waist with its blue clasp and hanging cord ends at her RIGHT hip).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("her right" means her own anatomical right):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face and chest square to camera; her RIGHT arm and the blue belt clasp on IMAGE LEFT |
| `02_back.png` | straight behind her | the veil down the back, back of the gown and sleeves; her RIGHT arm and the hanging cord ends on IMAGE RIGHT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm and sleeve nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm, sleeve and the belt clasp nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII female human peasant), as a 3D modelling reference.
Not a new design. ONE complete figure, head to shoe soles, centred, generous margins, near-orthographic camera at
chest height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same
render style and materials as input 1.

Identity (as in input 1): adult woman, light skin, red lips, short auburn fringe, thin gold circlet; a pale
sage-green veil over the head, draped round the neck and shoulders, its face edge trimmed with dark-green beads; a
floor-length forest-green gown with a beaded round neckline; very wide bell sleeves hanging to knee height, lined pale
sage-green; a thin twisted gold cord belt with a dark-blue gem clasp and hanging cord ends at her RIGHT hip; brown
shoe toes under the hem.

Pose (identical in all views, as in input 1): neutral A-pose, upright, feet slightly apart under the gown. Arms out at
about 30-35 degrees from vertical, a clear gap between each arm, its sleeve and the gown, and between each hand and
the gown. Hands empty and open, five spread fingers, palms toward the body. Head level.

Do NOT: put anything in the hands, add an apron, cape, cloak or crown; change any colour; change the pose; crop the
head or shoes; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the belt clasp on her RIGHT hip
on the image side the table implies; same character, proportions, pose and colours as input 1; whole figure inside
the frame, 1024 x 1536, true alpha; open empty hands.
