# Codex brief: HD reference views for the MM7 Beholder (m166: Floating Eye / Gazer / Evil Eye)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m166_claude/references_hd/`.
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
1. `native_views.png` — ORIGINAL native MM7 sprite views of the hovering frame, enlarged 2x with nearest neighbour,
   left to right: front, front three-quarter, profile (creature's right side, face to image right), rear
   three-quarter (mirrored by the engine), back. Magenta is background, not creature. Design, anatomy, pose and
   palette authority.
2. `native_identity.png` — ORIGINAL native frames (3x nearest): front hover, side tilt, front with the big eye lit.
   Magenta is background. Detail authority for the head, eyes, stalks, mouth and tentacles.

## Deliverables
Five images, genuine transparent background, **1024 x 1536 PORTRAIT**, unresized returns, one creature each:
`00_three_quarter.png` (front three-quarter from the creature's RIGHT, camera at head height, slightly above; the
face points diagonally toward screen-right), `01_front.png`, `02_back.png`, `03_left.png` (creature's LEFT side:
face points to image LEFT), `04_right.png` (creature's RIGHT side: face points to image RIGHT). Same creature, same
pose and proportions in all five. Near-orthographic camera, even soft neutral studio light (no dramatic light, no
cast shadows), whole creature inside the frame with at least 60 px margin, no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "beholder" (floating eye monster) from the supplied original sprites, as a 3D modelling and texturing
reference. Not a new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic
game materials and sharp fine detail (wet glossy flesh, folds, veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a floating head with no body. HEAD: a roughly round, slightly heart-shaped mass
of glossy reddish-BROWN flesh covered in deep BRAIN-LIKE FOLDS and ridges, wider at the top. FACE (front, lower
half): ONE large round central EYE with a yellow-green iris and dark pupil set in a fleshy socket; below it a wide
MOUTH with small IVORY teeth and a little orange tongue, with a few thin GOLDEN drool strands hanging down from it.
EYE STALKS: exactly FOUR thin pale grey-pink stalks growing from the upper head (two on each side, angled up and
out), each ending in a small round eyeball with a green iris. TENTACLES: exactly EIGHT long thin smooth dark
grey-brown tentacles growing from the underside of the head, hanging down and gently curving outward like a
jellyfish, about twice the head's height long; each ends in a flat, leaf-shaped bright GREEN tip (like a narrow
blade). The tentacles are separate from each other with clear air gaps, none crossing.

POSE (the native hover frame in input 1): floating upright, face forward; eye stalks up and out; the eight tentacles
hang down, spread evenly around the head, the outer ones curving out to the sides, tips pointing down and out.

Do NOT: add a body, arms, legs, horns, a second big eye, extra stalks or tentacles, armour or scenery; do not
change the colours; do not crop the tentacle tips; no magenta spill, coloured fringe or checkerboard.

## Per-image checks (re-run before selecting)
One big central green eye, four eye stalks with eyeballs, eight separated tentacles with green leaf tips, brain-like
brown head, ivory teeth and gold drool; correct side for 03/04; same proportions as the primary; transparent
background, 1024x1536, nothing cropped.
