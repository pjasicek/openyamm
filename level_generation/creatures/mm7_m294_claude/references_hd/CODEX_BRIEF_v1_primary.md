# Codex brief (run 1): HD primary three-quarter view for the MM7 Necromancer (m294)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m294_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. Record format: as in
`level_generation/creatures/mm7_m426_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm7_m294/native/m294sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority.
2. `mm7_m294/native/m294sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m294/native/m294sa2.png` — ORIGINAL native PROFILE frame.
4. `mm7_m294/native/m294sa4.png` — ORIGINAL native BACK frame (the long white hair over the black cape).
5. `mm7_m294/aligned_2x/m294sa1.png` — restored 2x three-quarter view, SURFACE MATERIAL ONLY (cloth, boots, gold,
   hair, skin).

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return; raw returns
under `raw/`; `generation_runs.json`. Accept the first image that passes the checks; at most ONE targeted corrective
regeneration for a failed image, then select the better and note residual faults. Stop after that.
If the image tool declines a request, do NOT rephrase or retry it: stop, record the exact refusal text in
`generation_runs.json` and in your last message.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Necromancer" (an undead sorceress monster) from the supplied original sprites, as a 3D modelling reference.
Not a new design. Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure,
full body from the top of the head down to the boot soles, centred, about 80% of the canvas height with about 140 px
of transparent space above and below, generous side margins. Near-orthographic camera, no floor, no shadow, no
scenery, no text. Even soft neutral studio light (no dramatic or rim light). Credible fully three-dimensional sculpt,
semi-realistic game materials, sharp fine detail.

Identity (from the native sprites; keep the native coverage and slim proportions, no added exposure or exaggeration):
- An adult woman of slim build with very pale grey-white skin, a narrow stern face, pale glowing eyes and dark lips.
- HAIR: long, straight, silky WHITE hair, parted in the middle, falling over the shoulders and straight down the back
  to the waist.
- HEADPIECE: a thin black band across the forehead with a small round GOLD ornament set with a pale jewel at the
  centre of the brow.
- NECK: a black choker.
- GARMENT: the native dark PURPLE fitted one-piece garment: one long purple sleeve on her LEFT arm (her right arm
  bare), asymmetric diagonal straps across the torso and the native geometric cut-out openings, high-cut at the hips
  as in the native frames. Faint thin red scratch marks on the pale skin as in the native.
- LEGS: semi-sheer dark grey stockings to high on the thigh with a broad black band at the top, and glossy black
  knee-high heeled boots with a pointed GOLD chevron ornament at each knee.
- CAPE: a long RAGGED BLACK cape hanging from the shoulders behind the arms down to the floor, opening at the front
  into two long panels on either side of the legs (a split skirt), the hem torn into long irregular tattered strips.
  Render the cape OPAQUE matte charcoal-black cloth. Seen from the front it shows behind the arms and beside the legs.
- HANDS: pale, slender, with long dark pointed fingernails, EMPTY.

Pose (the pose for every later view as well): standing upright, relaxed, weight even, feet about shoulder width apart
with a clear gap between the legs. Arms in an A-POSE: hanging down and out from the body at about 40 degrees from
vertical, elbows very slightly bent, with a clear gap of air between each arm and the body and cape; the arms in FRONT
of the cape. Both hands OPEN and relaxed, fingers separated, palms facing the thighs. Head level, looking forward,
the hair falling behind the shoulders so the arms stay clear.

Do NOT: draw a weapon, staff or any held object; add armour, a hood, a crown, extra jewellery or extra limbs; change
the colours (white hair, pale grey skin, purple garment, black cape, grey stockings, black boots, gold details); let
the cape or the hair cover the arms or hands; crop the head or the boots; add a floor, shadow, glow, sparkles, spell
effect or text.

INPUT ROLES (put these in the prompt): inputs 1–4 are the ORIGINAL native frames (anatomy, costume and silhouette
authority; the magenta/transparent background is not part of the character); input 5 is SURFACE MATERIAL ONLY.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic. It must show real depth (the front and one flank of the body and cape).
Head aligned with the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (head, hair, cape hem, boots), true transparent alpha, 1024 x 1536;
- long straight white hair, forehead band with gold ornament, black choker, purple one-piece with ONE long sleeve on
  her left arm, grey thigh stockings, black boots with gold knee chevrons, ragged black split cape to the floor;
- A-pose arms clear of the body and cape; both hands open and empty, separated fingers; gap between the legs.
