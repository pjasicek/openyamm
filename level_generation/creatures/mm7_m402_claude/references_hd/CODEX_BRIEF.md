# Codex brief: HD reference views for the MM7 Spider (mm7_m402_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m402_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_spi1_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (facing image right), rear three-quarter, back. Magenta is
   background. Design, anatomy and colour authority (tier A colouring).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes (only the abdomen colour
   changes). Use the LEFT (dark green abdomen) colouring.
3. `references_hd/native_actions.png` — native walk (side) and attack (front) frames: leg joints in motion. Anatomy
   evidence only.
4. `level_generation/creatures/mm7_m402/trimmed_2x/m402sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the spider's right (it faces toward image left-front), camera
  slightly above (primary; generate first; this image alone becomes the 3D mesh, so every leg must be readable)
- `01_front.png`, `02_back.png`, `03_left.png` (its LEFT side: it faces image LEFT), `04_right.png` (its RIGHT side:
  it faces image RIGHT)
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
show the same spider, pose and proportions. At most one corrective regeneration per view. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII giant spider from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail (glossy
chitin, coarse hair fringes, leg joints), even soft neutral studio light, near-orthographic camera, whole spider inside
the frame with margins, transparent background, no floor, no cast shadow, no web, no text.

Identity (from the native sprites): a giant spider with a large, round, very GLOSSY DARK GREEN ABDOMEN behind (like a
polished gem, with a bright specular sheen), a smaller BLACK cephalothorax in front marked with a pale WHITE-GREY
SKULL-LIKE face pattern, a cluster of small bright YELLOW eyes, short black chelicerae with small pale fangs, and EIGHT
long thin BLACK segmented legs. Each leg is clearly jointed (coxa, femur, patella, tibia, metatarsus, tarsus); the
femurs rise high above the body before bending down to the ground (high knees); the lower leg segments carry ragged
fringes of DARK RED hair on their underside, and each leg ends in a small curved pale silver claw. Legs are glossy
black with subtle dark grey highlights.

Pose (neutral rest pose for rigging, based on the native standing sprites): standing on all eight feet, body level and
low, abdomen slightly raised; legs spread wide and EVENLY spaced around the body like a star, the four on each side
clearly separated with visible air gaps — no leg crosses or overlaps another leg or the body; front legs reach
forward, rear legs back; all eight feet on one ground plane; fangs closed under the face.

Do NOT: add extra legs (exactly eight), a tail, wings, a web, armour or markings not in the sprites; do not make the
abdomen matte or hairy; do not change the colours (glossy dark green abdomen, black legs and thorax, red leg fringes,
white skull pattern, yellow eyes); do not let legs touch or cross; do not crop any foot.

Checks per image (re-run before selecting): exactly eight legs with all feet in frame; legs separated; glossy green
abdomen; white skull pattern on the thorax; yellow eyes; red fringes on the lower legs; same pose in all views;
transparent background; side views facing the stated direction.
