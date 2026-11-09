# Codex brief: HD reference views for the MM7 Bat (m158: Giant Bat / Vampire Bat / Inferno Bat)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m158_claude/references_hd/`.
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
1. `native_views.png` — ORIGINAL native MM7 sprite views of the spread-wing flight frame, enlarged 3x with nearest
   neighbour, left to right: front, front three-quarter, profile (creature's right side, head to image right),
   rear three-quarter, back. Magenta is background, not creature. Design, anatomy, pose and palette authority.
2. `native_identity.png` — ORIGINAL native close frames (2x nearest): chest/belly, profile with ears and red eye,
   belly from below, side with raised head, rear. Magenta is background. Detail authority for fur, ears, membrane.

## Deliverables
Five images, genuine transparent background, **1536 x 1024 LANDSCAPE**, unresized returns, one creature each:
`00_three_quarter.png` (front three-quarter from the creature's RIGHT, camera slightly above; muzzle points
diagonally toward screen-right), `01_front.png`, `02_back.png`, `03_left.png` (creature's LEFT side: head points
to image LEFT), `04_right.png` (creature's RIGHT side: head points to image RIGHT). Same creature, same pose and
proportions in all five. Near-orthographic camera, even soft neutral studio light (no dramatic light, no cast
shadows on the body), whole wingspan inside the frame with at least 70 px margin, no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII giant bat from the supplied original sprites, as a 3D modelling and texturing reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp fine
detail (shaggy fur strands, skin, membrane veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a giant bat with a small compact body covered in SHAGGY, slightly tufted
grey-brown (warm taupe-grey) fur. Head with a short pointed fox-like muzzle, mouth slightly open showing small
white fangs, small GLOWING RED eyes, very large upright pointed ears with PINK inner skin. Huge leathery wings:
membrane MID-GREEN (leafy green, lighter where lit) with a fine skin texture and thin PINK veins; the arm and the
long finger bones are PINK/flesh coloured and clearly visible along the leading edge and through the membrane;
scalloped trailing edge ending in a point at each finger tip; small pink thumb claw at each wrist. Short hind legs
with small PINK feet and claws, held back under the tail end of the body. No tail.

POSE (the native flight frame in input 1): the body is horizontal, as if flying forward, belly down; head raised
slightly and looking forward. Both wings spread WIDE to the sides, membranes fully open, nearly horizontal with the
outer halves and wing tips lifted slightly upward (a shallow V), finger bones fanned apart so each membrane panel is
visible; the membranes must not overlap the body. Hind legs trail back and down.

Do NOT: add extra limbs, a tail, horns, armour or scenery; do not fold the wings; do not change the colours (no
blue, no black membrane); do not crop the wing tips; no magenta spill, coloured fringe or checkerboard.

## Per-image checks (re-run before selecting)
Full wingspan inside the frame; red eyes, white fangs, large pink inner ears; green membrane with pink veins and
pink finger bones; shaggy grey-brown fur; pink feet; horizontal body with the native spread pose; correct side for
03/04; same proportions as the primary; transparent background, 1536x1024.
