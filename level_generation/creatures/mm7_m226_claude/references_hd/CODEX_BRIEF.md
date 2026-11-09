# Codex brief (run 2): four HD views and the falchion for the MM7 Leather Fighter (m226)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m226_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m226_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m226_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, hair, clothing, colours, pose, proportions, light and render style.
2. `mm7_m226_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; grey background is not part of the character). Use it for what each view
   shows (ponytail, the back of the jerkin and shoulder yoke, the sheathed sword behind the right shoulder, the gold
   dagger sheath on the right hip, the laced green panel on the left thigh).
3. `mm7_m226_claude/source/native_attack.png` — ORIGINAL native attack frames; for the falchion only.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("his left" means his own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | face and chest square to camera; his RIGHT arm on IMAGE LEFT; laced green thigh panel on IMAGE RIGHT |
| `02_back.png` | straight behind him | ponytail, back of the jerkin and the shoulder yoke, back of the belt, trousers and boots; his RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his LEFT arm and the laced thigh panel nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his RIGHT arm and the gold dagger sheath nearest the camera |
| `falchion.png` | prop only, no person | see "Falchion" below |

Generate each body view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any
residual fault.

## Prompt content for the body views (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Leather Fighter), as a 3D modelling reference. Not a
new design. ONE complete figure, head to boot soles, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1.

Identity (as in input 1): muscular adult man, pale skin, dark hair in a ponytail; green padded jerkin with a high
green collar; dark brown riveted leather shoulder yoke with short spikes; studded spiked bracers; dark belt with a
large silver buckle plate; brown pebbled leather trousers with a laced green panel on his LEFT thigh; gold dagger
sheath on his RIGHT hip; black buckled boots; a sheathed sword's grip behind his RIGHT shoulder.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 35 degrees from vertical, a clear gap between each arm and the body and between
each hand and the thigh. Hands empty and open, five spread fingers, palms toward the thighs. Head level.

Do NOT: draw a weapon in the hands, a shield, cape or helmet; change any colour; change the pose; crop the head or
boots; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the laced panel on his LEFT
thigh and the dagger sheath on his RIGHT hip on the image side the table implies; same character, proportions, pose
and colours as input 1; whole figure inside the frame, 1024 x 1536, true alpha; open empty hands.

## Falchion

Production prop design for the faithful reconstruction; no person in the image. Two large views of the SAME sword
side by side, both uncropped: the broad flat side and a three-quarter view. Transparent background, flat diffuse
studio light, no ground, shadow or text. From the native frames: a one-handed falchion about 1.0 m overall; a broad
single-edged steel blade (about 7 cm wide, widening toward a clipped point), gently curved with the cutting edge on
the CONVEX side, and two or three sharp hooked notches/spikes along the back (spine) near the tip; a short steel
crossguard; a dark leather-wrapped grip about 12 cm with gold bands; a small round pommel. Worn practical dark steel,
restrained highlights. No engravings or gems. Portrait 1024 x 1536 with the sword vertical, tip up, in each view.
