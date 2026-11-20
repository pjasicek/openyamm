# Codex brief: HD reference views for the MM6 Cockatrice (mm6_ckt_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ckt_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_spi1_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM6 standing sprite views, enlarged 2x with nearest neighbour,
   left to right: front, front three-quarter (facing image right, its right flank toward the camera), profile (facing image
   right), rear three-quarter, back. Magenta is background, not part of the creature. Design, anatomy, pose and
   proportion authority.
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes (left to right: tan,
   turquoise, red wings). Only the wing membranes change between palettes. Use the MIDDLE (turquoise) wings.
3. `references_hd/native_walk_side.png` — native walk frames in profile: shows the bird legs, the scaly orange
   feet with three forward toes and a rear toe, and the long spiked tail clearly.
4. `level_generation/creatures/mm6_ckt/aligned_2x/cktstda1.png` — restored 2x three-quarter frame, for surface
   material only (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter (like native view 2 of 5: creature facing image right, about 40 degrees
  toward the camera), camera at chest height slightly above (primary; generate first; this image alone becomes the
  3D mesh, so both wings, both legs, the tail, the neck and the beak must be clearly separate and readable)
- `01_front.png`, `02_back.png`, `03_left.png` (pure profile, the creature's LEFT flank toward the camera, so it faces
  image LEFT), `04_right.png` (pure profile, the creature's RIGHT flank toward the camera, facing image RIGHT)
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI "Cockatrice" (Agar's Pet) from the supplied original sprites, as a 3D modelling reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine
detail (individual body feathers, scaly legs, leathery wing membrane), even soft neutral studio light,
near-orthographic camera, whole creature inside the frame with generous margins, transparent background, no floor,
no cast shadow, no text.

Identity (from the native sprites): a bipedal monster bird the size of a large dog, standing upright on two legs.
- HEAD and NECK: a vulture/eagle head on a long, bare, curved neck with pink wrinkled skin (bare-headed like a
  vulture), a large hooked ORANGE-YELLOW BEAK, a RED bare patch around each eye (red brow), small dark eyes, and a
  ruff of pale ivory spiky feathers where the neck meets the body.
- BODY: a stocky, deep-chested torso covered in dark BROWN feathers with lighter brown mottling; a short single ivory
  spike on top of the head/crown in front view.
- WINGS: two large BAT-LIKE leathery wings (not feathered) growing from the shoulders, raised and spread up and out
  as in the native standing views: ivory-white bony wing arm and 4 long ivory finger bones fanning out, with
  TURQUOISE-GREEN scaly membranes stretched between them, scalloped trailing edge. The membrane is the only colour
  that changes between tiers, so keep it a clean turquoise.
- LEGS: two thick bird legs; feathered brown thighs, then bare scaly ORANGE-YELLOW lower legs and feet; each foot has
  three long forward toes and one rear toe, all ending in ivory talons.
- TAIL: a long, thick, tapering lizard-like brown tail reaching back and down to the ground behind, with a row of
  ivory SPIKES along its top and a dark arrow-tipped end.
- A row of ivory spikes also runs down the back from the shoulders.

Pose (identical in all five views): standing on both legs, feet flat and apart (a clear gap between the legs), body
upright and slightly leaning forward as in the native views, neck curved up with the head looking forward, beak
closed, both wings raised and fully spread with the membranes not overlapping the body, tail extended straight back
behind (tip near the ground) and clear of the legs.

Do NOT: add feathers to the wings, a crest, horns, arms or hands, extra legs or toes, a saddle or armour; do not
close or fold the wings; do not change the colours (brown body, pink bare neck, orange beak and feet, red eye
patches, ivory spikes/wing bones/talons, turquoise wing membrane); do not crop the wingtips or the tail.

Checks per image: bat wings with 4 ivory finger bones and turquoise membranes, vulture head with orange hooked beak
and pink bare neck, two bird legs with orange scaly feet (3 forward toes + 1 rear), long spiked tail behind, back
spikes, transparent background, nothing cropped, same pose in all views, side views correct (03 faces image left, 04 faces
image right).
