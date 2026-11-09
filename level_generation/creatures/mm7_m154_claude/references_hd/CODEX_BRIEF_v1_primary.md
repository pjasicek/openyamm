# Codex brief (run 1): HD primary for the MM7 Archer (m154)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m154_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m154_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m154_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Archer" shown in the attached original sprite views, as a 3D modelling reference. Not a new design. Exactly
ONE whole figure from the helmet horns to the boot soles, front three-quarter view (the body turned about 35 degrees
toward image right, so his right side is nearer the camera, as in the native second view), camera near orthographic
at chest height, slightly above. Generous margins. Even soft neutral studio light. Transparent background, no floor,
no shadow, no scenery, no text.

Identity (all from the native views): a strong adult man of normal human proportions with dark brown skin and a calm,
serious face. A rounded steel helmet with a short central spike and two small curved pale horns, worn over a steel
chain-mail coif that covers the neck and shoulders. A short-sleeved GREEN tunic reaching mid-thigh with a large WHITE
tree emblem on the chest; a polished GOLD gorget/collar plate on the upper chest; rounded dark steel pauldrons; grey
chain-mail sleeves on the arms; tan-yellow leather gloves; a brown leather belt with a round gold buckle; a brown
leather strap diagonally across the chest. Olive-brown leather trousers and tall olive-brown leather boots. On his back
a brown fur-covered quiver worn diagonally with a few white-fletched arrows sticking up behind his LEFT shoulder.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs, feet flat.
Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap between each arm and
the body and between each hand and the thigh. BOTH HANDS EMPTY and OPEN, gloved fingers straight and visibly spread
apart, thumb separated, palms toward the thighs. Head level, looking forward.

Do NOT: draw the bow or an arrow in the hands (modelled separately), a shield, cape or cloak; change any colour (green
tunic, white tree, gold gorget, steel, olive leather); turn the head; crop the horns or feet; add a floor, shadow or
text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Horned spiked helmet over a mail coif; green tunic with the white tree; gold gorget; dark pauldrons; mail sleeves;
  tan gloves; olive trousers and boots; fur quiver with arrows behind his LEFT shoulder.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
