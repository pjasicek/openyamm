# Codex brief (run 1): HD primary for the MM7 Peasant Human2 Male (m362)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m362_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m362_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m362_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII male human townsman (a well-dressed peasant) shown in the attached original sprite views, as a 3D modelling
reference. Not a new design. Exactly ONE whole figure from the top of the head to the boot soles, front three-quarter
view (the body turned about 35 degrees toward image right, so his right side is nearer the camera, as in the native
second view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral studio
light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): a clean-shaven young adult man of normal human proportions, light skin, thick
straight BLOND hair of medium length (covering the ears, to the nape), no beard. A loose pale grey-white linen shirt
with full puffed long sleeves gathered at the wrists into narrow cuffs, the shirt's laced V-neck visible at the
chest. Over it a sleeveless VIOLET-PURPLE doublet (vest) reaching to the upper thigh, with two broad WHITE bands from
the shoulders down the front forming a V to the waist and a white strip continuing down the middle of the skirt
below the belt, and puffed purple-and-white padded shoulder rolls (epaulettes) on both shoulders. A wide black
leather belt with rows of small round brass studs. Loose dark grey-brown breeches gathered below the knee, tucked
into tall black leather riding boots to just below the knee with a turned-down cuff. On his LEFT hip a rapier in a
black scabbard with a silver swept hilt, the scabbard hanging diagonally backward behind his left leg.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs and
boots, feet flat. Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap of
air between each arm and the body and between each hand and the thigh. BOTH HANDS EMPTY, fully OPEN and relaxed,
palms toward the thighs, five straight fingers visibly spread apart, thumb clearly separated. Head level, looking
forward.

Do NOT: put anything in the hands, draw the rapier drawn or held, add a hat, cape, cloak, armour or jewellery, add a
beard or moustache; change any colour (violet doublet with white bands, grey-white shirt, black studded belt, dark
grey breeches, black boots, blond hair); turn the head; crop the head, boots or scabbard; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Blond clean-shaven man; puffed grey-white shirt sleeves; violet doublet with the white V bands and the white centre
  strip below the belt; shoulder rolls; studded black belt; grey breeches; tall black boots; the sheathed rapier on
  his LEFT hip angled backward.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
