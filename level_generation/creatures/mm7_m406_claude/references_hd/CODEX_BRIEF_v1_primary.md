# Codex brief (run 1): HD primary for the MM7 Swordsman (m406)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m406_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m406_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m406_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Swordsman" (town guard / adventurer) shown in the attached original sprite views, as a 3D modelling
reference. Not a new design. Exactly ONE whole figure from the helmet spike to the soles, front three-quarter view (the
body turned about 35 degrees toward image right, so his right side is nearer the camera, as in the native second
view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral studio light.
Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): a broad, heavily muscled adult man of normal human proportions with a short
dark beard and a stern face. A rounded steel spangenhelm with a tall pointed spike on top, worn over a steel chain-mail
coif that covers the neck, cheeks and chin sides (the face open). Bare, muscular, tanned upper arms and shoulders
(no sleeves) with a few small red scratches. Dark steel-and-leather vambraces on the forearms and dark gauntlets. A
sleeveless tabard over the torso reaching mid-thigh, split vertically: BLUE on his right half and WHITE on his left half,
with three white chevrons across the blue half on the chest and back, a few faded red stains. A dark leather belt.
Steel plate leg armour with large rounded GOLD knee cops, plate greaves and steel sabatons.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs, feet flat.
Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap between each arm and
the body and between each hand and the thigh. BOTH HANDS EMPTY and OPEN, gauntleted fingers straight and visibly spread
apart, thumb separated, palms toward the thighs. Head level, looking forward.

Do NOT: draw the sword or any weapon (modelled separately), a shield, cape or cloak; add sleeves or arm plates above the
vambraces; change any colour (steel, blue/white tabard, gold knee cops, tanned skin); turn the head; crop the spike or
feet; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Spiked spangenhelm over a mail coif, bearded face; bare muscular upper arms; split blue/white tabard (blue on HIS
  right) with white chevrons; plate legs with gold knee cops.
- Empty open gauntlets with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
