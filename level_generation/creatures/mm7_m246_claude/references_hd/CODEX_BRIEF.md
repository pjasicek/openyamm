# Codex brief (run 2): four HD views and the broadsword for the MM7 Goblin (m246)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m246_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (see `generation_runs.json`). Do not regenerate or re-judge it.
Append the new runs to `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m246_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side,
on a mid-grey background).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m246_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same goblin, face, ears, chin tuft, helmet and crest, hair, armour, vest, colours, pose, proportions, light and
   render style.
2. `mm7_m246_claude/source/native_standing_views.png` — ORIGINAL native five-view sprite (front, front three-quarter,
   right profile, back three-quarter, back; grey background is not part of the character). Use it for what each view
   shows (the back of the helmet with the reddish-brown hair below it, the back of the vest, the pauldron from behind).
3. `mm7_m246_claude/source/native_attack_front.png` — ORIGINAL native attack frames; for the broadsword only.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions ("his left" means his own anatomical left; the spiked brass PAULDRON and the armoured navy sleeve
are on HIS LEFT arm, the bare green upper arm with the navy bracer is HIS RIGHT arm):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | face square to camera; the PAULDRON arm on IMAGE RIGHT, the bare arm on IMAGE LEFT |
| `02_back.png` | straight behind him | back of the helmet, hair and vest; the PAULDRON arm on IMAGE LEFT, the bare arm on IMAGE RIGHT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his pauldron arm nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his bare right arm nearest the camera |
| `broadsword.png` | prop only, no person | see "Broadsword" below |

Generate each body view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any
residual fault.

## Prompt content for the body views (adapt per view)

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Goblin warrior), as a 3D modelling reference.
Not a new design. ONE complete figure, crest to soles, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1.

Identity (as in input 1): lean muscular green-skinned goblin with pointed ears, yellow eyes, small lower tusks and a
purple chin tuft; tall ornate gold helmet with a spiked crown band and a tall swept-back gold crest; reddish-brown hair
from under the back of the helmet; sleeveless blue-teal scaled vest with gold trim and a diagonal leather strap; studded
brass belt with gold hanging hip panels; spiked brass pauldron and navy scaled sleeve with gold plates on his LEFT arm;
bare green right upper arm with a navy scaled bracer with gold bands on the right forearm; navy scaled trousers with
brown knee bands; brown boots with spiked brass shin guards.

Pose (identical in all views, as in input 1): neutral A-pose, upright, legs straight and slightly apart with a clear
gap, feet flat. Arms out at about 35 degrees from vertical, a clear gap between each arm and the body and between each
hand and the thigh. Hands empty and open, fingers straight and spread. Head facing forward.

Do NOT: draw a weapon, shield, cape or cloak; move the pauldron to the other arm; change any colour; change the pose;
crop the crest or feet; add a floor, shadow or text.

Checks per view: correct camera (side and facing direction, pure front/back/profile); the pauldron on the image side
the table implies; same goblin, proportions, pose and colours as input 1; whole figure inside the frame, 1024 x 1536,
true alpha; open empty hands.

## Broadsword

Production prop design for the faithful reconstruction; no person in the image. Two large views of the SAME sword
side by side, both uncropped: the broad flat side and a three-quarter view. Transparent background, flat diffuse
studio light, no ground, shadow or text. From the native attack frames (input 3): a LARGE one-handed broadsword about
1.1 m overall; a long, broad, almost straight single-piece steel blade about 7 cm wide, very slightly curved along its
back, widening a little toward an angled clipped point; bright polished silver edges with a darker rusty red-brown
band down the middle of the blade; a GOLD crossguard whose two quillons curve forward toward the blade like a
crescent; a short dark leather grip about 14 cm wrapped in gold wire; a small round gold pommel. Restrained highlights,
not chrome-white. No gems, engravings or text. Portrait 1024 x 1536 with the sword vertical, tip up, in each view.
