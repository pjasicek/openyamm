# Codex brief: HD reference views for the MM6 Spider (mm6_spi1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_spi1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM6 sprite standing views, enlarged 2x with nearest neighbour,
   left to right: front, front three-quarter, profile, rear three-quarter, back. Magenta is background. Design,
   anatomy and pose authority (this sheet is drawn in the blue palette).
2. `references_hd/native_palettes.png` — the same three-quarter view in the three native palettes, left to right:
   tier A brown, tier B dark blue, tier C dark red. Use the LEFT (tier A, brown) colouring.
3. `level_generation/creatures/mm6_spi1/aligned_2x/spi1sta1.png` — restored 2x three-quarter frame, for surface
   material only (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the spider's right, camera slightly above (primary; generate first;
  this image alone will be turned into the 3D mesh, so every leg must be readable)
- `01_front.png`, `02_back.png`, `03_left.png` (spider's left side), `04_right.png` (spider's right side)
Generate 01–04 with 00 as an additional input so all five are the SAME spider, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI giant spider from the supplied original sprites, as a 3D modelling reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials, sharp fine detail
(bristly hairs, chitin plates, leg joints), even soft neutral studio light, near-orthographic camera, whole spider
inside the frame with margins, transparent background, no floor, no cast shadow, no web, no text.

Identity (from the native sprites): a giant hunting spider (tarantula/wolf-spider build). Large rounded oval ABDOMEN
behind, higher than the head, with dark transverse stripes/ridges; smaller CEPHALOTHORAX in front, low; EIGHT long
thick hairy legs, each clearly jointed (coxa, femur, patella, tibia, metatarsus, small tarsus tip), the femurs rising
high above the body before bending down to the ground (strongly arched "knee up" legs); a pair of short PEDIPALPS in
front; two heavy CHELICERAE under the face ending in pale ivory-green FANGS; a cluster of small glowing ORANGE-RED eyes
on the front of the head. Colouring (tier A): warm brown with dark brown/black banding and stripes on legs and
abdomen, coarse hair texture, slightly paler joints, darker undersides.

Pose (neutral rest pose for rigging, based on the native standing sprites): standing on all eight feet, body level
and low, abdomen slightly raised; legs spread wide and EVENLY spaced around the body like a star, the four on each
side clearly separated with visible air gaps — no leg crosses or overlaps another leg or the body; front legs reach
forward, rear legs back; all eight feet on one ground plane; head facing forward, fangs closed under the face.

Do NOT: add extra legs (exactly eight), a tail, wings, web, armour or markings not in the sprites; do not change the
colouring to black widow or tarantula pink; do not let legs touch or cross; do not crop any foot.
Checks per image: exactly eight legs with all feet in frame; legs separated; abdomen stripes; orange eye cluster;
pale fangs; brown tier-A colouring; same pose in all views; transparent background.
