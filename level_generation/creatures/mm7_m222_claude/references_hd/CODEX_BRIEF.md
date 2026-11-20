# Codex brief (run 2): four HD views and the scimitar for the MM7 Chain Fighter (m222)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m222_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m222_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m222_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, face, helmet, hair, armour, colours, pose, proportions, light and render style.
2. `mm7_m222_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; grey background is not part of the character). Use it for what each view
   shows (the back of the hair, the scabbard across the back, the back of the mail briefs and leggings).
3. `mm7_m222_claude/source/native_attack.png` — ORIGINAL native attack frames; for the scimitar only.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face and chest square to camera; her RIGHT arm (gold shoulder guard) on IMAGE LEFT |
| `02_back.png` | straight behind her | back of the long hair, the empty scabbard diagonally across the back from her right shoulder to her left hip, back of the mail shirt and mail briefs, back of the leggings and boots; her RIGHT arm (gold shoulder guard) on IMAGE RIGHT |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm (green arm band) nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm (gold shoulder guard) nearest the camera |
| `scimitar.png` | prop only, no person | see "Scimitar" below |

Generate each body view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any
residual fault.

## Prompt content for the body views (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Chain Fighter soldier), as a 3D modelling
reference. Not a new design. ONE complete figure, helmet crest to boot soles, centred, generous margins,
near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no text. Even
soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a practical fantasy foot soldier, an athletic adult woman, fair skin, long straight
light-brown hair down her back; steel kettle helmet with a gold crest and gold rim; cropped steel chain-mail shirt
with short sleeves, green cloth trim at the neck V and at its lower edge, a green band on her LEFT upper arm, a
brown leather strap diagonally across the chest, one embossed gold shoulder guard on her RIGHT shoulder; brown
leather gauntlets with gold rivets; steel chain-mail briefs with a gold chain belt and two long embossed gold
panels hanging in front to the knees; dark navy-blue leather leggings; tall steel boots with dark bands; an EMPTY
dark scabbard on her back (capped top, no hilt). Neutral, modest documentation-style turnaround view.

If the image tool refuses a view, retry that view ONCE adding a thin dark brown fitted leather underlayer beneath
the mail briefs, and note the deviation in the run's reason.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap between the legs and boots, feet flat. Arms out at about 35 degrees from vertical, a clear gap between each arm
and the body and between each hand and the thigh. Hands open, five spread gloved fingers, palms toward the thighs.
Head level, looking forward.

Do NOT: draw a sword in the hands or a hilt in the scabbard, a shield, cape, cloak or skirt; change any colour;
change the pose; crop the helmet or boots; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- gold shoulder guard on her RIGHT shoulder, green arm band on her LEFT arm, in the image side the table implies;
- same character, proportions, pose and colours as input 1; whole figure inside the frame, 1024 x 1536, true alpha;
- empty open hands with five fingers wherever visible.

## Scimitar

Production prop design for the faithful reconstruction; no person in the image. Two large views of the SAME sword
side by side, both uncropped: the broad flat side (blade edge-on is NOT wanted), and a three-quarter view. Transparent
background, flat diffuse studio light, no ground, shadow or text. From the native attack frames: a one-handed
scimitar, about 0.95 m overall; a strongly curved single-edged polished steel blade that widens toward the tip
(about 4 cm wide at the guard, 6 cm near the tip), the cutting edge on the convex side; a gold crossguard with small
rounded ends curving toward the blade; a short dark brown leather-wrapped grip about 11 cm; a round gold pommel.
Worn practical steel, restrained highlights, not chrome-white. No engravings, gems or extra decorations. Portrait
1024 x 1536 with the sword vertical, tip up, in each view.
