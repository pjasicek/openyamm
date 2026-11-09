# Codex brief (run 1): HD three-quarter primary for the MM7 Zombie (m438)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m438_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm7_m470_claude/references_hd/
generation_runs.json` (id, family `m438`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m438/native/m438sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m438/native/m438sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m438/native/m438sa2.png` — ORIGINAL native right profile.
4. `mm7_m438/native/m438sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m438/native/m438sa4.png` — ORIGINAL native back.
6. `mm7_m438/aligned_2x/m438sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (skin, cloth, rope).
   It never sets the design, pose or proportions.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`m438_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences. If the image service refuses or blocks a request,
do NOT reword it to get around the refusal: stop, record the refusal text in `generation_runs.json` and in your last
message, and end the run.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Zombie monster from the supplied original sprites, as a 3D modelling reference. Not a new design. Output:
exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, from the top of the
head to the soles, centred, generous margins, near-orthographic camera, no floor, no shadow, no scenery, no text.
Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible, fully
three-dimensional sculpt, semi-realistic game materials, restrained game illustration, sharp fine detail.

Identity (from the native sprites): an adult male undead humanoid with a slim, upright, lean-muscled build.
- HEAD: gray-green skin, a narrow gaunt face, sunken dark eye sockets with small pale eyes, a thin grim mouth, short
  dark cropped hair, a narrow olive cloth headband around the forehead.
- BODY: bare gray-green torso, shoulders and arms, defined but lean muscles; the original small flat dark red and
  ivory accents on the chest and on the figure's RIGHT flank (a few exposed rib lines there), kept small and flat as
  in the sprite.
- ARMS: the figure's LEFT arm is whole, with a normal five-fingered hand. The figure's RIGHT arm ends just below the
  elbow: a short forearm stump with a dark red end and two small pale bone tips, exactly as pictured in the sprites.
- CLOTHES: worn dark olive-brown cloth trousers, loose, with torn cuffs at mid-shin and a few small native holes; a
  thin pale gray rope belt tied at the front with two short hanging ends. No shirt, no shoes.
- LEGS AND FEET: bare gray-green feet. The figure's RIGHT lower leg below the trouser cuff shows the original dark
  red and ivory accents (as in the sprite, not enlarged or intensified).
- COLOUR AND MATERIAL: gray-green skin with soft gray shading, olive-brown cloth trousers and headband, pale gray
  rope, small dark red and ivory accents only where the sprite has them.

The sprites show a separate forearm held in the figure's LEFT hand. The 3D model gets that object as a separate prop
later, so in this reference the LEFT hand is EMPTY.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and apart with a clear gap of air
between the legs and between the feet, feet flat with toes forward. Both arms hang down and out to the sides at about
35 degrees from vertical, elbows very slightly bent, with a clear gap of air between each arm and the body. The LEFT
hand is open and relaxed, five fingers slightly apart and slightly curled, palm facing the thigh. The RIGHT arm's
stump points down and out at the same angle. Head level, looking forward.

Do NOT: draw the held forearm or any weapon or object in the hands; add armour, a shirt, shoes, a cape, jewellery or
any accessory not listed; add new wounds, extra blood, gore detail, glow, smoke or effects; enlarge or intensify the
red accents; give the right arm a hand; change the colours; make it bulky or cartoonish; crop the head or feet; add a
floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; the uniform background pixels are not part of the
creature. In input 1 the figure's RIGHT arm (the stump) is on IMAGE LEFT. Input 6 is the restored front: SURFACE
MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. Show FRONT and RIGHT flank: the face points
diagonally toward SCREEN-LEFT, and the right-arm stump is nearer the camera. FRAMING / ALPHA: the whole figure
occupies about 80 % of the height with generous transparent margins, genuine RGBA alpha outside the silhouette and in
the air gaps. No painted checkerboard. Return exactly 1024 x 1536 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background (not a checkerboard drawn into the pixels);
- gaunt gray-green face, dark cropped hair, olive headband;
- right arm ends below the elbow as a stump; left hand empty with five fingers;
- olive-brown torn trousers, rope belt, bare torso and bare feet; red accents small, only where the sprite has them;
- A-pose with the stated gaps.
