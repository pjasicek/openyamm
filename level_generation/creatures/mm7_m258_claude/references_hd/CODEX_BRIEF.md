# Codex brief: HD reference views for the MM7 Griffin (mm7_m258_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m258_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_rat_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite flight views (the creature never lands), enlarged
   3x with nearest neighbour, left to right: front, front three-quarter, profile (facing image right), rear
   three-quarter, back. Magenta is background. Design, anatomy and colour authority (tier A colouring).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes. Use the LEFT (teal)
   colouring.
3. `references_hd/native_flight.png` — native wing-beat frames (front row, then side row): wing shape, how the
   primaries fan, leg positions in flight. Anatomy evidence only.
4. `level_generation/creatures/mm7_m258/trimmed_2x/m258sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the griffin's right (it faces toward image left-front), camera
  slightly above (primary; generate first; this image alone becomes the 3D mesh, so both wings, all four legs and
  the tail must be readable)
- `01_front.png`, `02_back.png`, `03_left.png` (the griffin's LEFT side: it faces image LEFT), `04_right.png` (its
  RIGHT side: it faces image RIGHT)
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
show the same griffin, pose and proportions. At most one corrective regeneration per view. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII griffin from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine detail (feather
barbs, fur, scaly talons), even soft neutral studio light, near-orthographic camera, the WHOLE griffin inside the frame
with margins (wingtips, tail tuft and claws included), transparent background, no floor, no cast shadow, no scenery,
no text.

Identity (from the native sprites): an eagle-headed lion. Front half eagle: head, neck, chest and shoulders covered
in dense TEAL-GREEN feathers (dark teal with lighter blue-green edges), a hooked YELLOW-GOLD beak, small pointed
feather tufts (ear tufts) on top of the head, fierce eye. Two front legs are EAGLE legs with yellow-gold scaly skin and
four long curved dark talons each. Rear half lion: muscular hindquarters and two lion hind legs in warm BROWN fur
with pale pink-grey paw pads. A long thin brown lion tail ending in a TEAL feather tuft. Two large feathered eagle
WINGS from the shoulders: teal coverts near the shoulder, long OLIVE-BROWN/khaki flight feathers (primaries and
secondaries) with darker tips, clearly separated primaries.

Pose (identical in all five views, a neutral rigging pose based on the native flight frames): flying level, body
horizontal; BOTH WINGS FULLY SPREAD straight out to the sides and raised about 25 degrees above horizontal, primaries
fanned with small gaps, the wings not overlapping the body or each other; head up and looking forward; the eagle
front legs reaching forward and down with talons open; the lion hind legs hanging down and slightly back, paws
relaxed and clearly apart from the front legs; the tail extended straight back and slightly down with the tuft clear
of the legs.

Do NOT: add a rider, saddle, armour, horns, extra limbs or extra wings (exactly two wings, two eagle legs, two lion
legs, one tail); do not fold the wings; do not change colours (teal plumage, gold beak and eagle legs, brown lion
body, olive-brown flight feathers, teal tail tuft); do not crop wingtips, talons or the tail.

Checks per image (re-run before selecting): whole griffin with both wingtips inside the frame; two spread wings with
separated primaries; two eagle front legs with four talons each; two brown lion hind legs; tail with teal tuft; ear
tufts; gold hooked beak; tier-A colours; transparent background; same pose and proportions as the primary; side views
facing the stated direction.
