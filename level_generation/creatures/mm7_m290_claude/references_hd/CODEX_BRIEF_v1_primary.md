# Codex brief (run 1): HD primary three-quarter view for the MM7 Monk (m290)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m290_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. Record format: as in
`level_generation/creatures/mm7_m170_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm7_m290/native/m290sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority.
2. `mm7_m290/native/m290sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m290/native/m290sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m290/native/m290sa4.png` — ORIGINAL native BACK frame (the hood and the robe back).
5. `mm7_m290/aligned_2x/m290sa1.png` — restored 2x three-quarter view, SURFACE MATERIAL ONLY (cloth, rope, skin).

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return; raw returns
under `raw/`; `generation_runs.json`. Accept the first image that passes the checks; at most ONE targeted corrective
regeneration for a failed image, then select the better and note residual faults. Stop after that.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Monk" from the supplied original sprites, as a 3D modelling reference. Not a new design. Output: exactly ONE
1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the top of the hood down to
the feet, centred, about 80% of the canvas height with about 140 px of transparent space above and below, generous side
margins. Near-orthographic camera, no floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic
or rim light). Credible fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites):
- A lean, fit adult man with a calm, serious face, clean-shaven, light skin; his head covered by a HOOD.
- A loose, heavy floor-length FOREST-GREEN monk's robe of coarse wool with deep vertical folds: a deep HOOD worn up,
  framing the face closely; a short cowl draping over the shoulders; very WIDE long sleeves reaching past the wrists;
  the robe falls straight to the ground, the hem just above the feet, slightly ragged.
- A WHITE ROPE CORD (twisted, with small knots) tied at the waist, its two ends hanging down the front to about the
  knees.
- Simple dark sandals; bare hands, light skin.

Pose (the pose for every later view as well): standing upright, relaxed, weight even, feet slightly apart. Arms in an
A-POSE: hanging down and out from the body at about 35 degrees from vertical, elbows very slightly bent, with a clear
gap of air between each arm/sleeve and the body; the hands out of the sleeves, OPEN and relaxed, fingers gently
separated, thumb clearly apart from the index finger. Both hands EMPTY. Head level, looking forward from the hood.

Do NOT: draw any held object, weapon or staff; take the hood down; add armour, jewellery, a belt buckle or pattern;
change the colours (forest-green robe and hood, white rope, light skin); let the sleeves cover the hands; crop the
hood or the feet; add a floor, shadow, glow, spell effect or text.

INPUT ROLES (put these in the prompt): inputs 1–4 are the ORIGINAL native frames (anatomy, costume and silhouette
authority; transparent background is not part of the character; their fists and glowing spell effects are not to be drawn); input 5 is SURFACE
MATERIAL ONLY.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic. It must show real depth (the front and one flank of the robe). Head
aligned with the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (hood, feet), true transparent alpha, 1024 x 1536;
- hood up, forest-green floor-length robe with wide sleeves, white knotted rope belt with hanging ends;
- A-pose arms clear of the body, both hands open and empty, out of the sleeves.
