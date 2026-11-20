# Codex brief (run 1): HD primary three-quarter view for the MM7 Mage (m274)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m274_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. Record format: as in
`level_generation/creatures/mm7_m170_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm7_m274/native/m274sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority. The staff in it is NOT to be drawn.
2. `mm7_m274/native/m274sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m274/native/m274sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m274/native/m274sa4.png` — ORIGINAL native BACK frame (the magenta cape with stars and crescent moons).
5. `mm7_m274/aligned_2x/m274sa1.png` — restored 2x three-quarter view, SURFACE MATERIAL ONLY (cloth, gold, beard).

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return; raw returns
under `raw/`; `generation_runs.json`. Accept the first image that passes the checks; at most ONE targeted corrective
regeneration for a failed image, then select the better and note residual faults. Stop after that.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Mage" (Sorcerer) from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the
tips of the collar horns down to the shoes, centred, about 80% of the canvas height with about 140 px of transparent
space above and below, generous side margins. Near-orthographic camera, no floor, no shadow, no scenery, no text.
Even soft neutral studio light (no dramatic or rim light). Credible fully three-dimensional sculpt, semi-realistic game
materials, sharp fine detail.

Identity (from the native sprites):
- A broad, powerfully built middle-aged man; a stern face with a long straight nose, heavy brows, receding ginger
  hair swept back, and a very LONG thick GINGER-ORANGE BEARD reaching the belt, with two thin braided strands hanging
  from the moustache; ginger eyebrows.
- COLLAR: a tall stiff MAGENTA (purple-pink) stand-up collar behind the head that rises into TWO POINTED HORN-LIKE
  TIPS to the left and right of the head (higher than the top of the head), lined in gold; below it a broad GOLD
  shoulder yoke with pointed shoulder tips lying over both shoulders.
- ROBE: a long dark FOREST-GREEN robe to the ankles, fitted over a muscular chest, open down the front from the waist
  over a slightly darker green underrobe, with broad GOLD trim bands along both front edges and the hem; long WIDE
  bell sleeves with gold cuff trim, ending at the wrists.
- BELT: a broad GOLD belt with a round gold medallion set with a large RED gem at the centre front.
- CAPE: a MAGENTA cape hangs from the gold yoke behind the arms down to the ankles, closed across the back, with
  darker magenta STARS and CRESCENT MOONS printed on it and a gold hem band; seen from the front only its edges show
  behind the arms.
- Brown leather shoes; bare hands with a light warm skin tone.

Pose (the pose for every later view as well): standing upright, relaxed, legs slightly apart with the feet showing
under the hem. Arms in an A-POSE: hanging down and out from the body at about 35 degrees from vertical, elbows very
slightly bent, with a clear gap of air between each arm/sleeve and the body; the arms in FRONT of the cape. His RIGHT
hand OPEN and relaxed, fingers gently separated. His LEFT hand CLOSED in a firm FIST as if gripping an invisible
upright staff held vertically at his side: fingers wrapped round, thumb over the index finger, a clear round grip
opening running STRAIGHT UP AND DOWN through the fist. Both hands EMPTY. Head level, looking forward.

Do NOT: draw the staff or any held object; add a hat, hood, armour or extra jewellery; change the colours (forest
green robe, magenta collar and cape, gold yoke/trim/belt, red gem, ginger beard and hair); let the cape cover the arms
or hands; let the beard merge with the arms; crop the collar horns or the feet; add a floor, shadow, glow, sparkles,
spell effect or text.

INPUT ROLES (put these in the prompt): inputs 1–4 are the ORIGINAL native frames (anatomy, costume and silhouette
authority; transparent background is not part of the character; their staff is not to be drawn); input 5 is SURFACE
MATERIAL ONLY.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic. It must show real depth (the front and one flank of the robe). Head
aligned with the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (collar horns, feet), true transparent alpha, 1024 x 1536;
- long ginger beard with two braids, magenta horned collar, gold pointed yoke, green robe with gold front/hem trim,
  wide sleeves, gold belt with red gem, magenta star-and-moon cape behind;
- A-pose arms clear of the body; right hand open, LEFT hand a firm fist with a vertical grip opening; both empty.
