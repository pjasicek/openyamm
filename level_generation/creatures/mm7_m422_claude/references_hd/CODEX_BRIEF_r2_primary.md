# Codex brief (reworded variant 2 after refusals): corrected HD primary for the MM7 m422 character

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m422_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Background: runs `m422_three_quarter_v3` and `m422_three_quarter_r1` (both with the HD v2 image as an input) were declined by the image tool at the output stage. Run 1 (native frames as inputs) was not. Per a recorded user decision this is a
reworded, clearly neutral request (see the note `note_refusal_override_20261020` in `generation_runs.json`).
Append the new run(s) to `generation_runs.json` with ids `m422_three_quarter_r2` (and `_r2b` if one corrective
regeneration is needed), keep raw returns under `raw/`. Replace `00_three_quarter.png` with the selected image only if
it fixes the two faults below while keeping the costume identity; otherwise keep v2 and say so (judge it against the game frames). If the image tool
declines this request, record the refusal text (with error code and moderation fields if shown) in
`generation_runs.json` and in your last message, and stop: do not reword it yourself.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m422/native/m422sa0.png` — original low-resolution game frame, front view (design authority; the transparent
   background is not part of the figure).
2. `mm7_m422/native/m422sa1.png` — original game frame, three-quarter view.
3. `mm7_m422/native/m422sa2.png` — original game frame, profile.
4. `mm7_m422/native/m422sa4.png` — original game frame, back view (cape and collar).
5. `mm7_m422/aligned_2x/m422sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL ONLY.

## Prompt content

TASK CONTEXT — 3D MODELLING REFERENCE for a fantasy video game: a neutral, dignified full-body character turnaround
image of the costumed nobleman in inputs 1–4, in a modelling A-pose. Stylised semi-realistic
game-art render (hand-painted look, not a photograph). Not a new design. Output: exactly
ONE 1024 x 1536 portrait PNG, genuine transparent background, ONE complete figure from the top of the collar to the
boot soles, centred, about 78% of the canvas height, at least 120 px of transparent space above and below, generous
side margins. Near-orthographic camera, even soft neutral studio light, no floor, no shadow, no text.

Character (as in the game frames): a tall, lean, calm aristocratic man with very pale ivory skin, a narrow composed face with a
neutral, serene expression and the mouth gently closed (two tiny pointed eye-teeth may just show at the lip, very
subtle), dark eyes, short swept-back charcoal-grey hair with a widow's peak. Costume: a tall flared dark-red stand-up
cape collar with a thin gold edge; a royal-blue long coat to mid-shin with a white shirt V at the neck, a small gold
neck ornament, a vertical gold embroidered front strip with gold clasps, a gold hem band and white shirt cuffs; a broad
ornate gold belt with an oval buckle and winglike side scrolls; a dark-red cape behind the arms down to the coat hem
with a gently scalloped gold-trimmed edge; black trousers and black calf-high riding boots.

Pose: standing upright and relaxed, feet about shoulder width apart. ARMS IN A WIDE A-POSE: each arm straight down
and OUT at about 45 degrees from vertical, each hand clearly away from the coat with a wide gap of air (at least a
hand's width) between hand and coat and between the inner sleeve and the torso below the armpit. The arms are in FRONT
of the cape; the cape stays behind the body. Both hands open and relaxed, palms toward the body, five slender fingers
slightly separated, empty. Head level, looking forward.

Camera: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to the man's left of straight front (the same side as input 2,
showing the left flank of the coat and part of the cape), at chest height, near-orthographic.

Do NOT: make it photographic; change the costume or colours; add a weapon, armour, jewellery, animals, blood, glow, smoke or effects; draw a
menacing or aggressive expression; let the cape cover the arms or hands; crop the collar or boots; add a floor,
shadow or text; leave a coloured halo around the figure.

## Checks (re-run before selecting)

- a real 40–45 degree three-quarter camera (one coat flank clearly visible), not near-frontal;
- wide gaps hand-to-coat and inner sleeve-to-torso below the armpits on both sides; cape behind;
- costume matching inputs 1–4 (collar, coat, strip and clasps, belt, cuffs, cape, boots); pale face, dark hair;
  five fingers per hand; whole figure inside 1024 x 1536 with true alpha and margins.
