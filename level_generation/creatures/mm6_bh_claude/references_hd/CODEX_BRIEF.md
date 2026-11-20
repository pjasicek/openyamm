# Codex brief: HD reference views for the MM6 Flying Eye (mm6_bh_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bh_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_spi1_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM6 sprite views, enlarged 2x with nearest neighbour, left to
   right: front, front three-quarter, profile, rear three-quarter, back. Magenta is background. Design, anatomy and
   pose authority (this sheet is drawn in the blue tier-B palette).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes, left to right: tier A,
   tier B, tier C. Use the LEFT (tier A) colouring.
3. `level_generation/creatures/mm6_bh/aligned_2x/bhwlka1.png` — restored 2x three-quarter frame, for surface material
   only (never the design).

## Deliverables (5 images, transparent background, 1024 x 1024 SQUARE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the creature's right, camera at eye height (primary; generate
  first; this image alone becomes the 3D mesh, so horns, mouth and tendrils must be clearly readable)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png` (creature's right side)
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI "Flying Eye" from the supplied original sprites, as a 3D modelling reference. Not a new design.
Beautifully detailed, credible fully three-dimensional sculpt with semi-realistic game materials and sharp fine detail
(pitted stone-like skin, horn ridges, wet eye), even soft neutral studio light, near-orthographic camera, whole
creature inside the frame with margins, transparent background, no floor, no cast shadow, no text.

Identity (from the native sprites): a disembodied floating demonic HEAD with no body and no limbs. The FRONT is a
grey, pitted, stone-like face mask: heavy furrowed angry brow, ONE single large round EYE in the centre of the face
(tier A: glowing green iris with a yellow ring, dark pupil, bright highlight, wet), and below it a wide open MOUTH
showing rows of long sharp ivory fangs and a dark interior. The BACK and top of the skull are a different material:
lumpy, wrinkled, fleshy skin, reddish-brown in tier A. Two large curling RAM HORNS, grey with ridged rings, grow from
the upper sides of the head and curl outward and down into open spirals. The bottom of the head ends in a short
fringe of dripping, stalactite-like fleshy TENDRILS hanging down (several thin points of different lengths).

Pose (identical in all five views): head level, facing forward, mouth open as in the sprites, horns symmetric,
tendrils hanging straight down. Proportions: head roughly as wide as tall, horns spanning wider than the head.

Do NOT: add a body, neck, arms, eyestalks, extra eyes, wings or a halo; do not close the mouth; do not change the
colours (grey face and horns, reddish-brown back skin, green-yellow eye, ivory fangs); do not crop the horns.
Checks per image: one central eye, open fanged mouth, two spiral ram horns, grey stone face vs reddish-brown back
skin, hanging tendrils, transparent background, same pose in all views.
