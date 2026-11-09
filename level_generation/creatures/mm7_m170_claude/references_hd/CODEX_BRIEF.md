# Codex brief (run 2): four HD views for the MM7 Cleric of the Moon (m170)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m170_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m170_three_quarter_v1` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to the existing `generation_runs.json`
(same record format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five
selected views side by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m170_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, hair, helmet, crescent, collar, pendant, back frame, banners, tassels, robe, trim, rope belt,
   hands, colours, pose, proportions, light and render style. (It is a front-LEFT three-quarter view.)
2. `mm7_m170/native/m170sa0.png` — ORIGINAL native front frame (256 x 256).
3. `mm7_m170/native/m170sa2.png` — ORIGINAL native profile frame: how the back frame and banners sit behind the body.
4. `mm7_m170/native/m170sa4.png` — ORIGINAL native back frame: the square gold back plate, the V of two gold rods
   from it, the two banners covering the upper back to the sides, the black hair under the helmet.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | symmetric front: face, collar and pendant centred, rope knot centred, both arms out in the A-pose, banners visible behind to both sides |
| `02_back.png` | straight behind him | the back: helmet back and long black hair, the square gold back plate between the shoulder blades, the V of rods and both banners hanging behind the back to hip height, the robe back to the hem; his LEFT arm on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm nearest the camera; the back frame, crescent and banners seen edge-on behind him |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm nearest the camera; frame and banners edge-on behind him |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in fold detail.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Cleric of the Moon), as a 3D modelling reference.
Not a new design. ONE complete figure from the rod tips above the head to the robe hem, centred, about 82% of the
canvas height, generous margins, near-orthographic camera at chest height, transparent background, no floor, no
shadow, no scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a tall gaunt man with ashen grey skin, a long narrow severe face, long straight black hair;
a polished gold domed helmet with cheek plates; a large gold engraved crescent rising behind the shoulders, its points
beside the head; a black-and-gold ribbed round collar with a gold Y-chain and round gold pendant on the chest; on the
back a small square gold plate from which two thin gold rods rise in a wide V above the head with small hooks at the
tips, a row of turquoise tassels hanging from each rod and a long dark olive-brown banner with a ragged lower edge
hanging from each rod behind the body to about hip height; a floor-length grass-green robe with wide sleeves, a thin
gold trim line down the front and a gold band round the hem; a gold-ochre rope belt knotted at the front with two
hanging ends with tassels; bare grey long-fingered hands with dark claw-like nails.

Pose (identical to input 1): standing upright, legs slightly apart under the robe; arms hanging down and out from
the body in an A-pose with a clear gap of air between each arm and the torso; both hands open and empty with the
fingers slightly spread and gently curled. Head level, looking forward. The banners hang BEHIND the arms.

Do NOT: add a staff, weapon or held object; add a beard, hood, cape, armour or extra jewellery; change colours; let
the banners cover the arms, hands or the robe front; crop the rod tips, crescent, banners or hem; add a floor,
shadow, glow, spell effect or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (rod tips, crescent, banners, hem), true transparent background, 1024 x 1536;
- same helmet, crescent, collar, back plate, rods, tassels, banners, robe, trim and rope belt wherever the view can see
  them; long black hair visible in the back view;
- arms clear of the body, both hands open and empty; no added object.
