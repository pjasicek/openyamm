# Codex brief: paint the MM9 Colloidal Warrior's head (mm9_colloidalwarrior_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_colloidalwarrior_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool. A fantasy video-game monster made of living slime, restored from a 2002 game for a game mod. The result
is PROJECTED onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel:
brow, brow nubs, eye slits, nose, mouth, cheek folds, throat rolls. Only surface paint is added. Do not change the shape, do not turn or tilt the
head, do not add volume beyond the clay's outline, do not move any feature.

## Inputs (attached, in order)
1-5. `clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`: the clay head, geometry authority.
6. `references_hd/mm9_head_views_b.png`: the original head with its skin (Colloidal Warrior, green): identity, colour, eye and mouth paint.
7. `references_hd/mm9_skin_x4_b.png`: the original skin: surface material and colour (the face is top left).
8. `references_head/in_body_head.png`: the high-definition master's head: face identity and slime material.

## Deliverables (true transparent background, same size and framing as the clay, unresized returns, no floor, no shadow, no text)
`b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`, `b_05_top.png`.
Generate the front first, then use it as an extra input for the other views. One corrective regeneration per view at most. Keep raw returns in
`raw/`. Write `generation_runs_b.json` (id, prompt, inputs with sha256, output path).
Even soft studio light, no cast shadows, no rim light, no specular highlights baked in: the paint is a colour map (the game adds the gloss).
Semi-realistic game-art materials with sharp detail.

## Paint
- SLIME: olive and yellow-green gelatinous slime, darker olive in the folds and creases, a few darker mossy-green blotches and speckles on the
  dome and the throat rolls, as inputs 6-7. Smooth wet surface texture (fine drips, small bubbles), NOT scales, NOT fur, NOT rock.
- BROW and NUBS: the same slime, a little lighter on the ridges, darker green in the grooves between the nubs.
- EYES: inside each almond eye slit of the clay, a glowing ORANGE-AMBER slit eye: a bright orange band filling the slit, brightest yellow-orange
  along its middle, a thin black rim line along the upper and lower lids, as input 6. No pupils, no white, no round iris. The eye exactly fills
  the clay's slit; nothing painted outside it.
- NOSE: the beak nose a little paler yellow-green with darker nostrils.
- MOUTH: on the clay's mouth line and lips: a near-black gap between the lips with ONE row of small pointed yellowish-ivory teeth along the
  upper lip and one along the lower lip, exactly along the clay's own lip line and only as wide as the clay's mouth, as input 6. The lips dark
  olive-brown. Paint only where the clay has the mouth; no second mouth, no teeth anywhere else.
- THROAT ROLLS and BACK: slime as above, darker olive in the creases between rolls; the back of the dome plain slime with soft folds.
