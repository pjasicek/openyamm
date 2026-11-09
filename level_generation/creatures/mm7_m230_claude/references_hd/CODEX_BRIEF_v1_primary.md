# Codex brief (run 1): HD primary for the MM7 Plate Fighter (m230)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m230_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m230_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m230_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII "Plate Fighter" knight (Initiate of the Sword) shown in the attached original sprite views, as a 3D
modelling reference. Not a new design. Exactly ONE whole figure from the plume tip to the sabaton soles, front
three-quarter view (the body turned about 35 degrees toward image right, so his right side is nearer the camera, as in
the native second view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral
studio light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): a stocky, broad armoured knight of human proportions in full plate armour of
polished steel with GOLD edge trim on every plate. A cylindrical flat-topped great helm with a narrow eye slit and a
vertical breathing slot (a T-shaped visor opening), a gold rim, a small gold eagle crest on top and a long GREEN and
WHITE feather plume flowing from the crest down the back of the helm. Rounded pauldrons, plate arms with steel chain
mail visible at the elbows and armpits, plate gauntlets. Over the cuirass a long tabard reaching mid-thigh, split
vertically: GREEN on his right half and WHITE on his left half, with a darker green leaf/vine heraldic motif on the
white half and a few faded red stains. A dark leather belt at the waist. Plate legs with large rounded GOLD knee
cops, plate greaves and steel sabatons.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap between the legs, feet
flat. Arms hanging down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap between each
arm and the body and between each hand and the thigh. BOTH HANDS EMPTY and OPEN, plate-gauntleted fingers straight
and visibly spread apart, thumb separated, palms toward the thighs. Head level, facing forward.

Do NOT: draw the sword or any weapon (modelled separately), a shield, cape or cloak; reveal a face; change any colour
(steel, gold trim, green/white tabard and plume); turn the head; crop the plume or feet; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Great helm with T visor, gold eagle crest, green/white plume; gold-trimmed plate; split green/white tabard (green on
  HIS right); gold knee cops.
- Empty open gauntlets with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
