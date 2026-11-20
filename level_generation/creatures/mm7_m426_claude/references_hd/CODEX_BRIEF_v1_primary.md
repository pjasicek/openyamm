# Codex brief (run 1): HD primary three-quarter view for the MM7 Warlock (m426)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m426_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. Record format: as in
`level_generation/creatures/mm7_m170_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm7_m426/native/m426sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority. The wand in it is NOT to be drawn.
2. `mm7_m426/native/m426sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m426/native/m426sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m426/native/m426sa4.png` — ORIGINAL native BACK frame (the long hair over the dark blue cape).
5. `mm7_m426/aligned_2x/m426sa1.png` — restored 2x three-quarter view, SURFACE MATERIAL ONLY (cloth, gold, hair, skin).

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return; raw returns
under `raw/`; `generation_runs.json`. Accept the first image that passes the checks; at most ONE targeted corrective
regeneration for a failed image, then select the better and note residual faults. Stop after that.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Warlock" (a sorceress) from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the
top of the hair down to the bare feet, centred, about 80% of the canvas height with about 140 px of transparent space
above and below, generous side margins. Near-orthographic camera, no floor, no shadow, no scenery, no text. Even soft
neutral studio light (no dramatic or rim light). Credible fully three-dimensional sculpt, semi-realistic game
materials, sharp fine detail.

Identity (from the native sprites):
- An adult woman of athletic build, a calm, stern face with green-blue eyes, red lips, a small gold earring; very
  long, thick, wavy COPPER-RED hair falling over the shoulders and down the back to the waist.
- GOWN: a sleeveless floor-length crimson-RED gown: a fitted red bodice with a modest neckline edged by a thin GOLD
  CORD that ties at the centre of the chest, two thin gold cords wrapping diagonally round the bodice, a narrow gold
  band at the waist, and a long softly draped red skirt to the ankles with a gold band at the hem.
- CAPE: a long DARK NAVY-BLUE cape hanging from the shoulders behind the arms down to the ankles, closed across the back,
  with a narrow pale lavender edge band; seen from the front only its edges show behind the arms.
- JEWELLERY: a broad gold armband on each upper arm and a broad gold bracelet on each wrist.
- Bare arms and bare feet, warm light skin.

Pose (the pose for every later view as well): standing upright, relaxed, weight even, feet slightly apart. Arms in an
A-POSE: hanging down and out from the body at about 35 degrees from vertical, elbows very slightly bent, with a clear
gap of air between each arm and the body and gown; the arms in FRONT of the cape. Her RIGHT hand OPEN and relaxed,
fingers gently separated. Her LEFT hand CLOSED in a firm FIST as if gripping an invisible short wand held upright: a
clear round grip opening running STRAIGHT UP AND DOWN through the fist. Both hands EMPTY. Head level, looking forward.

Do NOT: draw the wand or any held object; add armour, a hood, shoes or extra jewellery; change the colours (copper-red
hair, crimson gown with gold cords, navy cape with lavender edge, gold arm and wrist bands); let the cape or the hair
cover the arms or hands; crop the hair or the feet; add a floor, shadow, glow, sparkles, spell effect or text.

INPUT ROLES (put these in the prompt): inputs 1–4 are the ORIGINAL native frames (anatomy, costume and silhouette
authority; transparent background is not part of the character; their wand is not to be drawn); input 5 is SURFACE
MATERIAL ONLY.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic. It must show real depth (the front and one flank of the robe). Head
aligned with the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (hair, bare feet), true transparent alpha, 1024 x 1536;
- long wavy copper-red hair, crimson sleeveless gown with gold cords and hem band, navy cape with lavender edge behind;
- gold armbands and bracelets; A-pose arms clear of the body; right hand open, LEFT hand a fist with a vertical grip
  opening; both empty; bare feet.
