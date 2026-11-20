# Codex brief: HD reference views for the MM7 Robot v2 (m386: Seeker / Sentinel / Assassin Droid), ALL-METAL

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m386_v2_claude/references_hd/`.
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

## Why this is a v2

The first reconstruction followed the sprite's bone-coloured parts literally and came out as a dinosaur SKELETON with
robot parts (skull, vertebrae, ribs, teeth). The owner rejected that: this monster is a **droid** and must read as a
**fully metallic machine**. Keep the native silhouette, proportions, pose and colour scheme, but build every part
from machined metal. Where the sprite looks like bone, read it as aged brass/bronze armour plating.

## Inputs (attached, in order; RUN 2 adds the selected primary in front of these)
1. `native_views.png` — ORIGINAL native MM7 sprite views of the standing frame, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (machine's right side, head to image right), rear
   three-quarter, back. Magenta is background, not the machine. Silhouette, pose, proportions and palette authority.
2. `native_identity.png` — ORIGINAL native frames (3x nearest): front, side, side, rear. Magenta is background.
   Layout authority for the chassis, head, neck, tail, legs and the gun under the body. NOT a material authority for
   the head, neck and tail (see "Why this is a v2").

## Deliverables
Five images, genuine transparent background, **1536 x 1024 LANDSCAPE**, unresized returns, one machine each:
`00_three_quarter.png` (front three-quarter from the machine's RIGHT, camera slightly above chassis height; the head
points diagonally toward screen-right), `01_front.png`, `02_back.png`, `03_left.png` (machine's LEFT side: head
points to image LEFT), `04_right.png` (machine's RIGHT side: head points to image RIGHT). Same machine, same pose
and proportions in all five. Near-orthographic camera, even soft neutral studio light (no dramatic light, no cast
shadows), whole machine inside the frame with at least 60 px margin on every side (scale the machine down if needed;
the curled tail top and the spike tips must not touch the edge), no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: high-definition reconstruction of the EXISTING Might and Magic VII
walking combat droid from the supplied original sprites, as a 3D modelling and texturing reference. Same silhouette,
pose and colours as the sprite, rebuilt as a credible, fully three-dimensional, FULLY METALLIC ROBOT with
semi-realistic game materials (worn gunmetal steel, aged brass/bronze, rusty orange-red painted plates), sharp fine
mechanical detail (panel seams, rivets, bolts, hinges, pistons, cable runs), like a high-quality model of a
steampunk-industrial war machine.

Identity: a four-legged mechanical walker with a predatory, raptor-like silhouette — but a MACHINE through and
through, no part looks organic or skeletal.
- CHASSIS: a compact, boxy dark GUNMETAL steel body with panel lines and bolts; a round glossy black ORB lens in the
  front centre that glows WHITE.
- HEAD: an armoured mechanical SENSOR HEAD with a long wedge-shaped snout silhouette like a raptor's, built from
  riveted overlapping metal plates (brass/bronze with steel parts), a hinged metal lower jaw (slightly open; a straight
  steel blade edge or a row of small square steel vent teeth, not bone teeth), one bright glowing GREEN optic lens in
  a round metal bezel on each side of the head. No skull, no eye sockets, no bone.
- NECK: long and thin, rising from the front-top of the chassis, going forward and slightly up; built as a chain of
  ARTICULATED METAL SEGMENTS — short brass/bronze armoured collars over a black flexible cable / hydraulic spine,
  with small pistons along it. Not vertebrae.
- TAIL: long, rising from the back of the chassis and curling up and over in a big arc, tapering to a pointed steel
  tip; built as a chain of interlocking brass/bronze RING SEGMENTS (each a short tapered metal cylinder or overlapping
  armour band), with small flat metal cooling fins / vanes along the underside instead of ribs. Not vertebrae,
  not a skeleton.
- LEGS: exactly FOUR legs, two at the front corners and two at the back corners; each leg is a long straight
  polished steel SPIKE (a smooth metal rod ending in a sharp point on the ground) held in a thick rusty bronze
  CYLINDER SLEEVE (like a gun barrel housing, with black cable windings) near its top; each sleeve is joined to the
  chassis side by a short rusty orange-red painted armour arm and black hydraulic hoses. The four spikes stand
  splayed: they slant down and outward to the ground like a spider's legs, so the chassis is held about two thirds of
  the spikes' length above the ground. No knees: each spike is one straight rod.
- GUN: under the chassis, hanging on a short pivot mount, a dark steel BALL housing with a short forward-pointing
  BARREL wrapped in coils that glow pale BLUE-VIOLET, the muzzle pointing forward. Clearly visible and clearly a
  weapon.

POSE (the native standing frame in input 1): standing on the four spike tips, chassis level, neck and head forward,
tail curled up behind. Legs splayed evenly, clearly separated, none crossing. Gun under the body pointing forward.

Do NOT: draw a skeleton, skull, bones, vertebrae, ribs, spinal processes, fossil, teeth like an animal's, flesh, skin
or any organic material; do not add wheels, feet, arms, hands, wings, extra legs or heads, or scenery; do not change
the colour scheme (dark gunmetal body, brass/bronze head-neck-tail and sleeves, rusty orange-red arm plates, steel
spikes, green eyes, white orb, blue gun coils); do not crop the tail or the spike tips; no magenta spill, coloured
fringe or checkerboard.

## Per-image checks (re-run before selecting)
Reads instantly as a METAL ROBOT, with nothing that reads as bone or skeleton; exactly four straight spike legs in
bronze sleeves standing on their tips; armoured mechanical raptor-like head with green optics on a segmented metal
neck; curled segmented metal tail; dark chassis with the white front orb; the ball-and-barrel gun under the body with
blue coils, pointing forward; correct side for 03/04; same proportions as the primary; transparent background,
1536x1024, at least 60 px margin, nothing cropped.
