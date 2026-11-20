# Codex brief: HD reference views for the MM7 Robot (m386: Seeker Droid / Sentinel Droid / Assassin Droid)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m386_claude/references_hd/`.
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
1. `native_views.png` — ORIGINAL native MM7 sprite views of the standing frame, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (creature's right side, head to image right), rear
   three-quarter (mirrored by the engine), back. Magenta is background, not creature. Design, anatomy, pose and
   palette authority.
2. `native_identity.png` — ORIGINAL native frames (3x nearest): front, side, side, rear. Magenta is background.
   Detail authority for the chassis, head, neck, tail, legs and the gun under the body.

## Deliverables
Five images, genuine transparent background, **1536 x 1024 LANDSCAPE**, unresized returns, one creature each:
`00_three_quarter.png` (front three-quarter from the creature's RIGHT, camera slightly above chest height; the head
points diagonally toward screen-right), `01_front.png`, `02_back.png`, `03_left.png` (creature's LEFT side: head
points to image LEFT), `04_right.png` (creature's RIGHT side: head points to image RIGHT). Same machine, same pose
and proportions in all five. Near-orthographic camera, even soft neutral studio light (no dramatic light, no cast
shadows), whole machine inside the frame with at least 60 px margin, no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII robot ("droid") from the supplied original sprites, as a 3D modelling and texturing reference. Not a new
design. Beautifully detailed, credible fully three-dimensional machine with semi-realistic game materials (worn
gunmetal, rusty bronze, aged bone-coloured brass), sharp fine detail, as if a high-quality model of the sprite.

Identity (from the native sprites): a four-legged mechanical walker built like a robotic dinosaur skeleton.
CHASSIS: a compact, boxy dark GUNMETAL body with panel lines and bolts, with a round glossy black ORB in the
front centre that glows WHITE. HEAD: a mechanical dinosaur / raptor SKULL of aged bronze-brown metal plates and
bone-like struts, long snout, open jaw with small teeth, two bright glowing GREEN eyes; it sits on a long thin
segmented VERTEBRA NECK of bronze bone-like segments that rises from the front-top of the chassis, goes forward and
slightly up. TAIL: a long segmented vertebra tail of the same bronze bone segments with small side ribs, rising from
the back of the chassis and curling up and over in a big arc. LEGS: exactly FOUR legs, two at the front corners and
two at the back corners; each leg is a long straight steel SPIKE (a smooth metal rod ending in a sharp point on the
ground) held in a thick rusty bronze CYLINDER SLEEVE (like a gun barrel housing, with black cable windings) near its
top; each sleeve is joined to the chassis side by a short rusty reddish-brown armour arm and black cables. The four
spikes stand splayed: they slant down and outward to the ground like a spider's legs, so the chassis is held about
two thirds of the spikes' length above the ground. GUN: under the chassis, a small dark metal ball with a short
forward-pointing coil emitter that glows pale BLUE-VIOLET.

POSE (the native standing frame in input 1): standing on the four spike tips, chassis level, neck and head forward,
tail curled up behind. Legs splayed evenly, clearly separated, none crossing.

Do NOT: add wheels, feet, arms, hands, wings, extra legs or heads, armour plates or scenery; do not make it organic
flesh; do not change the colours; do not crop the tail or the spike tips; no magenta spill, coloured fringe or
checkerboard.

## Per-image checks (re-run before selecting)
Exactly four spike legs with bronze sleeves, standing on their tips; robot raptor skull with green eyes on a
segmented neck; segmented curled tail; dark chassis with the white front orb; small blue emitter under the body;
correct side for 03/04; same proportions as the primary; transparent background, 1536x1024, nothing cropped.
