# Codex brief: HD reference views for the MM7 Dragonfly (m186: Dragonfly / Fire Dragonfly / Queen Dragonfly)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m186_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool
(`image_gen`), no CLI/API fallback. Record format as in
`level_generation/creatures/mm6_bat_claude/references_hd/generation_runs.json`.

This brief has two runs. The run you are asked to do is named in the command that invoked you:
- **RUN 1 (primary):** produce only `00_three_quarter.png`. At most one corrective regeneration. Then stop.
- **RUN 2 (views):** input 1 is the selected `00_three_quarter.png`; produce `01_front.png`, `02_back.png`,
  `03_left.png`, `04_right.png`, each with at most one corrective regeneration, plus `selected_views_review.png`
  (contact sheet of all five selected views on grey).
In both runs append to `generation_runs.json` (id, prompt, inputs with sha256, raw output path copied to `raw/`,
selected flag, reason, superseded runs).

## Inputs (attached, in order; RUN 2 adds the selected primary in front of these)
1. `native_views.png` — ORIGINAL native MM7 sprite views of the spread-wing flight frame, enlarged 2x with nearest
   neighbour, left to right: front, front three-quarter, profile (creature's right side, head to image right),
   rear three-quarter (the engine mirrors it, so the head also points right), back. Magenta is background, not creature. Design, anatomy, pose and palette authority.
2. `native_identity.png` — ORIGINAL native frames (2x nearest): side views of the head, crest, body rings and
   tail claw, wings, and a front view. Magenta is background. Detail authority for head, crest, wings and claw.

## Deliverables
Five images, genuine transparent background, **1536 x 1024 LANDSCAPE**, unresized returns, one creature each:
`00_three_quarter.png` (front three-quarter from the creature's RIGHT, camera slightly above; head points
diagonally toward screen-right), `01_front.png`, `02_back.png`, `03_left.png` (creature's LEFT side: head points
to image LEFT), `04_right.png` (creature's RIGHT side: head points to image RIGHT). Same creature, same pose and
proportions in all five. Near-orthographic camera, even soft neutral studio light (no dramatic light, no cast
shadows on the body), whole wingspan inside the frame with at least 70 px margin, no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII giant dragonfly monster from the supplied original sprites, as a 3D modelling and texturing reference. Not a
new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials and
sharp fine detail (chitin plates, segment rings, wing veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a monstrous giant dragonfly. HEAD: large, with two big glossy ORANGE-RED compound
eyes, a short snout ending in pale IVORY hooked mandibles (slightly open), and a tuft of thin GOLD-YELLOW bristly
legs/feelers hanging under the jaw. Behind the head a short thorax carries a CREST of curved bright GREEN spines
running down the back of the neck and upper body like a mane. BODY: a very long, thin, SEGMENTED abdomen of
brown-grey chitin rings with a slight bronze sheen and paler ring edges, hanging BELOW the head in an S-curve: it
first bends back behind the head, then curves forward and down. Small green spines continue sparsely along the back
of the upper abdomen. TAIL END: a grasping claw of three to four long curved olive-gold prongs with pale silver tips,
like a forked pincer. WINGS: exactly FOUR long narrow translucent wings (two pairs, forewings slightly longer) attached
at the thorax just behind the head, pale silver-grey and glassy with a dense network of thin RED-BROWN veins.

POSE (the native flight frame in input 1): hovering upright. The head is at the top looking forward; the body hangs
down under it in the S-curve from input 1 (front view: a straight vertical column under the head; side view: S
curve); the tail claw at the bottom, prongs spread. All four wings spread straight out to the sides, nearly
horizontal, fore and hind wing on each side slightly apart so both are visible, none overlapping the body.

Do NOT: add legs other than the small gold bristles under the head, add a stinger, extra wings, armour or scenery;
do not fold the wings; do not change the colours; do not crop the wing tips or the tail claw; no magenta spill,
coloured fringe or checkerboard.

## Per-image checks (re-run before selecting)
Exactly four wings, fully inside the frame; orange-red eyes, ivory mandibles, gold bristles under the head; green
spine crest; long segmented brown body in the native S-curve hanging below the head; forked claw tail with three or
four prongs; correct side for 03/04; same proportions as the primary; transparent background, 1536x1024.
