# Codex brief (v2 run 1): HD three-quarter primary and prop images for the MM7 Angel (m150)

User review of v1 (2026-10-20): the helmet must be its own model, the cuirass texturing is wrong (it must be polished
steel, not black), the shoulders read unnatural, and the shield is wrong (the native shield is a HEATER shield with a
gold emblem, not round). This v2 run replaces the body primary and adds two prop images.

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m150_claude/references_hd/v2/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation. Records:
`references_hd/v2/generation_runs.json` (id, family `m150`, role, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs); raw returns under `references_hd/v2/raw/`.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m150/native/m150sa0.png` — ORIGINAL native front. Design, proportions and palette authority.
2. `mm7_m150/native/m150sa1.png` — ORIGINAL native front three-quarter.
3. `mm7_m150/native/m150sa2.png` — ORIGINAL native side.
4. `mm7_m150/native/m150sa4.png` — ORIGINAL native back.
5. `mm7_m150/native/m150ah0.png` — ORIGINAL native attack frame with the SHIELD facing the camera (heater shape, gold
   emblem).
6. `mm7_m150/aligned_2x/m150sa0.png` — restored 2x front: SURFACE MATERIAL ONLY (polished steel, brass, skin, feathers).
7. `mm7_m150/aligned_2x/m150ah0.png` — restored 2x attack frame: SURFACE MATERIAL ONLY for the shield face and emblem.
8. `mm7_m150_claude/references_hd/00_three_quarter.png` — the v1 primary: keep its FACE, WINGS, skirt, leather tabs,
   greaves and sandals; do NOT copy its dark armour colour or its helmet.

## Deliverable 1: `v2/00_three_quarter.png` (body primary, NO helmet)

Landscape 1536 x 1024, true transparent background, unresized. Front-right three-quarter (camera 40-45 deg toward the
figure's own RIGHT; the face and toes point diagonally toward SCREEN-LEFT), chest height, near-orthographic.

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Angel from the original sprites, as a 3D modelling reference. Not a new design. ONE complete figure, head
to soles and both complete wings, centred with generous margins, no floor, shadow, scenery or text. Even soft neutral
studio light (no rim light, no glow). Credible fully three-dimensional sculpt, semi-realistic game materials.

Identity:
- HEAD: BARE HEAD, NO HELMET (the helmet is a separate model). Stern clean-shaven face with tan skin, strong jaw,
  straight nose, dark eyes, as input 8. Dark brown wavy hair, combed back close to the skull on top and falling to the
  nape at the back (hair close to the head so a helmet can sit over it).
- TORSO: a POLISHED BRIGHT STEEL muscled cuirass (silver-grey steel with soft reflections, NOT black, NOT dark), front
  and back plates, modelled pectorals and abdominals, with polished BRASS-GOLD rims along the neck opening, the
  armholes and the lower edge, as in inputs 1, 2 and 6. The cuirass covers the chest and the back up to the base of
  the neck and to the shoulder joints; its armholes are cut at the shoulder joint where the arm leaves the torso. A
  narrow brass-rimmed steel SHOULDER STRAP lies over the top of each shoulder, joining the front and back plates. No
  separate pauldrons; the deltoids are bare skin outside the armholes. A brown leather belt with a round brass buckle.
- ARMS: bare muscular tan arms with natural, rounded shoulders (deltoids continuous with the trapezius, not bulging
  boxes); a steel bracer with brass rims on each forearm; bare hands, five fingers.
- WAIST AND LEGS: as input 8 — green knee-length skirt with dark brown leather tabs and small brass rings, steel and
  brass greaves, brown sandals.
- WINGS: as input 8 — two large feathered wings on the shoulder blades, white to pale lavender upper feathers,
  blue-violet undersides, raised in a high open V; the trailing edges above the elbows, not touching the arms.

Pose: neutral A-pose for rigging: upright, legs apart with a clear gap, feet flat, toes forward; arms hanging down and
OUT at a clear 35-40 degrees from vertical (wider than input 8), elbows very slightly bent, a clear gap of air between
each arm and the torso all the way up into the armpit; hands empty, open, five fingers slightly apart, palms toward
the thighs; head level.

Do NOT: draw a helmet, cap, crown or headband; a sword, a shield or any weapon; a cape, halo or glow; dark or black
armour; pauldrons; extra arms or wings; cartoon proportions; crop the wing tips or the feet; floor, shadow or text.

Checks: bare head with close dark hair; polished SILVER steel cuirass with brass rims and shoulder straps; arms at
35-40 deg with open armpits; wings as input 8; camera and alpha as stated; 1536 x 1024. One targeted correction at most.

## Deliverable 2: `v2/helmet.png` (helmet prop, alone)

Square 1254 x 1254, transparent background, flat diffuse studio light, no head, no person, no text. ONE helmet seen
from the front three-quarter (its front turned toward screen-left, slightly from above), complete and uncropped,
physical thickness visible at the opening. Design from inputs 1, 2, 3 and the v1 head turnaround
(`mm7_m150_claude/references_head/00_front.png` style): a rounded polished STEEL bowl helmet with a brass-gold band
around the brow, open face with brass-rimmed steel cheek guards, a tall brass-gold CREST rising from the crown that
curls forward at its top into a SCROLL (a solid curled crest, not a loop or ring), small swept-back brass-gold
feathered wing ornaments on both temples, and a round teal jewel set at each side. Hollow inside, sized for a human
head. No hair, no plume of loose feathers.

## Deliverable 3: `v2/shield.png` (shield prop, alone)

Portrait 1024 x 1536, transparent background, flat diffuse studio light, no arm, no hand, no text. ONE shield seen
straight from the FRONT (exterior face to the camera), complete. Design from inputs 1, 5 and 7: a HEATER shield (flat
top edge with slightly rounded corners, straight sides curving to a POINT at the bottom), about 75 cm tall and 55 cm
wide, gently convex, dark brown-bronze face with a polished BRASS-GOLD rim and a row of small brass studs along the
rim, and a large raised brass-gold EMBLEM in the centre: a stylised upright winged motif / fleur shape as in inputs 5
and 7 (vertical spine with symmetrical upswept wings or leaves). Physical rim thickness visible.

Checks for 2 and 3: prop alone, complete, transparent background, the stated canvas, design faithful to the native
(heater shape, gold emblem; steel helmet with a curled scroll crest).
