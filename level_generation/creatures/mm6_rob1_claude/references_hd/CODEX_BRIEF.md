# Codex brief: HD reference views for the MM6 Patrol Unit (mm6_rob1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_rob1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_spi1_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM6 sprite views, enlarged 2x with nearest neighbour, left to
   right: front, front three-quarter (seen from the robot's right), profile (robot's right side, facing image right),
   rear three-quarter, back. Magenta is background, not part of the robot. Design and proportion authority
   (tier A palette).
2. `references_hd/native_palettes.png` — the three-quarter view in the three native palettes, left to right: tier A
   (steel), tier B (blue), tier C (copper). Use the LEFT (tier A) colouring.
3. `references_hd/native_attack.png` — native front attack frames: the lens at the front of the top sensor head
   flashes red. Shows the sensor head end-on; for the sensor head shape only. Draw the lens unlit in the masters.
4. `level_generation/creatures/mm6_rob1/aligned_2x/rob1fla1.png` — restored 2x three-quarter frame, for surface
   material only (never the design).

## Deliverables (5 images, transparent background, 1024 x 1024 SQUARE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the robot's right (like native view 2 of 5), camera slightly
  above the equator so the top cap and the sensor head read in depth (primary; generate first; this image alone
  becomes the 3D mesh, so the stacked rings, their lips and the sensor head must be clearly readable)
- `01_front.png`, `02_back.png`, `03_left.png` (robot's left side, facing image left), `04_right.png` (robot's right
  side, facing image right)
Generate 01–04 with 00 as an additional input so all five are the SAME robot, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI "Patrol Unit" hovering sentry robot from the supplied original sprites, as a 3D modelling reference. Not a
new design. Credible, fully three-dimensional hard-surface model with semi-realistic game materials and sharp fine
detail, even soft neutral studio light (no dramatic highlights, no coloured reflections, no environment reflections
of a room), near-orthographic camera, whole robot inside the frame with margins, transparent background, no floor,
no cast shadow, no thruster flame, no text.

Identity (from the native sprites): a SPHERE about as wide as tall, built from five horizontal stacked bands, top to
bottom:
1. Top CAP: a dome of dull blue-grey steel with an etched, swirling, acid-etched/engraved surface pattern (tier A:
   cool steel grey with a slight blue tint).
2. Upper RING: a thick polished shell band of warm dark bronze-chrome metal (smooth, satin-reflective, tier A:
   warm grey-brown chrome), slightly proud of the cap with a rounded lip at its top and bottom edge. At the FRONT
   its top edge dips into a downward-pointing V notch that exposes the etched cap down to a point.
3. Red BELT: a narrower recessed equatorial band of glossy crimson-red, inset between the two rings (dark gap/lip
   above and below it). At the FRONT centre sits one EYE: a horizontal almond/lens-shaped light set into the belt,
   glowing yellow-orange at the centre fading to orange-red at the tips. Nothing else on the belt.
4. Lower RING: the same polished bronze-chrome band, mirroring the upper ring. At the FRONT its lower edge rises into
   an upward-pointing inverted V notch that exposes the etched lower cap up to a point (mirror of the upper notch).
5. Bottom CAP: the same etched blue-grey steel dome as the top.
From the sides and back the rings are plain and continuous (no notches, no eye); the notches and the eye are front
only.

SENSOR HEAD on top of the sphere, centred: a short thin pale-tan metal post that leans and bends slightly forward,
carrying a small rectangular box-shaped sensor head lying horizontally and pointing FORWARD (along the eye
direction). The sensor box is about one fifth of the sphere's width long: its rear half is a pale blue-grey steel
block, its front half is a slightly tapered, flatter grey steel nozzle ending in a flat front face holding a small
round lens (unlit). Its rear end face has small ridged vents along the edges. In the front view the sensor head is
seen end-on as a small rectangle above the sphere; in the side views it is a horizontal box pointing toward the
robot's front.

Pose (identical in all five views): sphere upright and level, belt horizontal, sensor head pointing straight
forward. Proportions as in the sprites: sphere overall height to width about 1:1, the sensor head plus post adds
about 25 % of the sphere height above the top.

Do NOT: add legs, arms, wheels, thrusters, antennas, guns, extra eyes, lights or panels; do not put the eye or the
notches on the back or sides; do not change the colours (etched blue-grey caps, warm bronze-chrome rings, crimson
belt, yellow-orange eye); do not make the sphere flattened or egg-shaped; do not crop the sensor head.

Checks per image: five stacked bands (cap / ring / red belt / ring / cap) with lips between them, front-only V notches
(upper pointing down, lower pointing up) and a single front eye, sensor head on a bent post pointing forward,
etched caps vs smooth polished rings, transparent background, same proportions in all views, side views correct
(03 faces image left, 04 faces image right, sensor head points toward the facing direction).
