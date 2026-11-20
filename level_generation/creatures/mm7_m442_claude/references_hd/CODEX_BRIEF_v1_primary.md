# Codex brief (run 1): HD primary for the MM7 Peasant Goblin Female (m442)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m442_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Attached input (path relative to `level_generation/creatures/`)

1. `mm7_m442_claude/source/native_standing_views.png` — the ORIGINAL native MM7 standing sprite in five views, left to
   right: front, front three-quarter, right-side profile, back three-quarter, back. Enlarged 3x with nearest-neighbour
   pixels on a flat grey background (the grey is not part of the character). IDENTITY EVIDENCE, not an image to upscale.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, true transparent background, unresized image-generation return.
Keep each raw return under `raw/` (`m442_three_quarter_v1.png`, ...). Record every run in `generation_runs.json`
(id, prompt, input sha256, output path, selected flag, reason, superseded runs).

## Prompt content

TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the existing Might and
Magic VII female goblin villager (a peasant woman of the goblin race) shown in the attached original sprite views, as
a 3D modelling reference. Not a new design. Exactly ONE whole figure from the top of the hair to the boot soles, front
three-quarter view (the body turned about 35 degrees toward image right, so her right side is nearer the camera, as in
the native second view), camera near orthographic at chest height, slightly above. Generous margins. Even soft neutral
studio light. Transparent background, no floor, no shadow, no scenery, no text.

Identity (all from the native views): an adult goblin woman, upright, sturdy build with broad shoulders and thick
arms, olive-green skin on the face, neck and hands, pointed ears, a long narrow nose, stern face. Near-black hair
pulled up into a short high ponytail at the crown, tied with a vivid red ribbon whose two stiff pointed ends stick up
and out. A fitted sleeveless PURPLE vest with broad white vertical stripes and white trim, closed with small brass
toggles; under it a cream-white blouse with very wide, long sleeves that hang open at the wrists in loose cuffs; a
cream-white sash wrapped round the waist. PURPLE close-fitting trousers to just below the knee with white
criss-cross lacing down the outer side of each leg and white cuffs at the knee. Tall brown leather boots laced up the
front with brass eyelets.

Pose: neutral A-pose, standing upright, legs straight and slightly apart with a clear gap, feet flat. Arms hanging
down and out at about 35 degrees from vertical, elbows nearly straight, a clear gap of air between each arm and the
body and between each hand and the thigh, the wide sleeves hanging free of the body. BOTH HANDS EMPTY, fully OPEN and
relaxed, palms toward the thighs, five straight fingers visibly spread apart, thumb clearly separated. Head level,
looking forward.

Do NOT: put anything in the hands (her sickle is modelled separately), add a weapon, bag, hat, cape, armour or
jewellery; change any colour (green skin, black hair, red ribbon, purple-and-white vest, cream blouse and sash, purple
trousers, brown boots); turn the head; crop the hair ribbon or the boots; add a floor, shadow or text.

## Checks before selecting (re-run each)

- One figure, front three-quarter, whole figure inside the frame with margins, 1024 x 1536, true transparent alpha.
- Green goblin face with pointed ears, black high ponytail with the red ribbon; purple-and-white striped vest; very
  wide cream sleeves; cream sash; purple knee trousers with white side lacing; tall laced brown boots.
- Empty open hands with five spread fingers each, clear gaps arm/body and hand/thigh, legs apart.
- Do at most ONE targeted corrective regeneration; then select the better return and note any residual fault.
- If the image tool refuses a request, record the refusal text in generation_runs.json and stop; do not rephrase.
