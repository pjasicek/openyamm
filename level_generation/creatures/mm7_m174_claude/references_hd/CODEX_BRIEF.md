# Codex brief (run 2): four HD views for the MM7 Cleric of the Sun (m174)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m174_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m174_three_quarter_v3` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record
format), keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five selected views side
by side on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m174_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same gold sun mask and wavy rays, grey steel skull cap, tall flared scarlet collar, wavy gold mantle,
   striped scarlet robe, teal jewelled stole with cream/gold edge, bare tan forearms with gold wrist bands, pose,
   proportions, light and render style.
2. `mm7_m174/native/m174sa0.png` — ORIGINAL native front frame (256 x 256).
3. `mm7_m174/native/m174sa2.png` — ORIGINAL native profile frame.
4. `mm7_m174/native/m174sa4.png` — ORIGINAL native back frame: the grey cap, the collar and the two rounded lobes of
   the mantle over the striped robe back.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the cleric faces the viewer in `01_front`; "his left" means the cleric's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | symmetric front: mask centred, mantle open at the centre front, stole centred, both forearms out from the robe |
| `02_back.png` | straight behind him | the grey skull cap with the back of the rays, the collar, the two rounded mantle lobes, the striped robe back to the hem; his LEFT arm on IMAGE LEFT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his left arm nearest the camera; mask and rays in profile |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his right arm nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Cleric of the Sun), as a 3D modelling reference.
Not a new design. ONE complete figure from the ray tips to the robe hem, centred, about 80% of the canvas height,
generous margins, near-orthographic camera at chest height, transparent background, no floor, no shadow, no
scenery, no text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): the face covered by a polished gold sun mask with about twelve wavy golden rays radiating
around the head; a smooth grey steel skull cap behind it; a tall stiff flared scarlet collar; a large rounded gold
mantle with rippling wavy ridges over the shoulders and upper arms down to the waist, open at the centre front; a
floor-length scarlet robe with fine vertical darker red and orange-red stripes; a teal-green stole with a cream/gold
edge, gold buckle and a column of small yellow and orange-red jewels hanging down the front to the knees, pointed;
bare tan forearms with broad gold wrist bands; bare open hands.

Pose (identical to input 1): standing upright, legs slightly apart under the robe; the forearms angled out from the
body with clear air between each forearm/hand and the robe; hands open and empty, fingers gently separated. Head level.

Do NOT: show the real face; add a staff, weapon or held object; add a hood, cape, armour or extra jewellery; change
colours; let the mantle cover the forearms or hands; crop the rays or hem; add a floor, shadow, glow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame, true transparent background, 1024 x 1536;
- same mask, rays, cap, collar, mantle, robe stripes, stole, wrist bands wherever the view can see them;
- hands open, empty and clear of the robe; no added object.
