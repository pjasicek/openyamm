# Codex brief (run 2): corrected HD primary three-quarter view for the MM7 Vampire (m422)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m422_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

The orchestrator reviewed run 1 (`m422_three_quarter_v1`, `m422_three_quarter_v2` in `generation_runs.json`). The
identity of v2 is ACCEPTED (face, hair, collar, coat, gold strip and clasps, belt, cuffs, cape, boots). Two faults
remain for 3D modelling: the arms hang too close to the coat (the hands nearly touch it and Meshy would fuse them), and
the camera is only about 25 degrees off the front. Produce ONE corrected primary. Append the new run(s) to
`generation_runs.json` (same record format, ids `m422_three_quarter_v3`, and `_v4` if a correction is needed), keep raw
returns under `raw/`, and replace `00_three_quarter.png` with the selected image only if it is better than v2 on the
two faults while keeping the identity; otherwise keep v2 and say so. At most ONE corrective regeneration.
If the image tool declines a request, record the refusal text in `generation_runs.json` and in your last message and
stop (do not reword).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m422_claude/references_hd/raw/m422_three_quarter_v2.png` — IDENTITY AUTHORITY: the same man, costume,
   colours, materials, light and render style.
2. `mm7_m422/native/m422sa1.png` — ORIGINAL native three-quarter frame (design authority; transparent background is not
   part of the character).
3. `mm7_m422/native/m422sa0.png` — ORIGINAL native front frame.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: the EXACT same character as input 1 (a faithful HD reconstruction of
the existing Might and Magic VII Vampire nobleman), redrawn as a 3D modelling reference with a corrected pose and
camera. Not a new design. Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background, ONE complete
figure from the collar tips to the boot soles, centred, about 78% of the canvas height, at least 120 px of transparent
space above and below and generous side margins. Near-orthographic camera, even soft neutral studio light, no floor,
no shadow, no text.

Identity: exactly as input 1 — pale ivory-grey skin, narrow stern face, dark eyes, mouth closed or only slightly open
with two small subtle fangs, swept-back charcoal hair with a widow's peak; tall flared burgundy collar with thin gold
edge; royal-blue coat to mid-shin with the white shirt V, small gold neck ornament, vertical gold front strip with gold
clasps, gold hem band, white cuffs; broad ornate gold belt with oval buckle and winglike side scrolls; burgundy cape
behind the arms to the coat hem with a scalloped gold-trimmed edge; black trousers, black calf-high boots.

Pose: standing upright, feet about shoulder width apart. ARMS IN A WIDE A-POSE: each arm straight down and OUT at
about 45 degrees from vertical, so that each hand is clearly away from the coat skirt with a wide gap of air (at least
a hand's width) between the hand and the coat and between the inner arm/sleeve and the torso below the armpit. The
arms are in FRONT of the cape: the cape stays behind the body and does not fill the gaps under the arms. Both hands
OPEN, relaxed, palms toward the body, five long slender fingers slightly separated, empty. Head level, looking forward.

Camera: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to the character's left of straight front (the same side as
input 1, showing his left flank of the coat and part of the cape on his back), at chest height, near-orthographic.

Do NOT: change the costume, colours or face; add a weapon, armour, jewellery, bats, blood, glow or effects; let the
cape cover the arms or hands; crop the collar or boots; add a floor, shadow or text; leave a coloured halo around
the figure (clean alpha edges).

## Checks (re-run before selecting)

- the camera is a real 40–45 degree three-quarter (one coat flank clearly visible), not near-frontal;
- clear gaps: hand-to-coat and inner sleeve-to-torso below the armpits, both sides; cape behind;
- identity identical to input 1; five fingers per hand; whole figure inside 1024 x 1536 with true alpha and margins.
