# Codex brief: HD reference views for the MM6 Bat (giant bat) (mm6_bat_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bat_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `level_generation/creatures/mm6_bat_claude/references_hd/native_views.png` — ORIGINAL native MM6 sprite views, enlarged 2x
   with nearest neighbour, left to right: front, front three-quarter, profile (creature's right side shown), rear
   three-quarter, back. Magenta is background, not creature. This is the design, anatomy, pose and palette authority.
2. `level_generation/creatures/mm6_bat/aligned_2x/batwae0.png` — restored 2x frame, for surface material only (never the design).

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — front three-quarter from the creature's right, camera slightly above (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png` (creature's right side)
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

IMPORTANT — pose: these images will texture an EXISTING 3D mesh that was modelled from these very sprites, so the
pose must match the native sprites (described below), not a new neutral pose. Keep proportions faithful to the
sprites. Even soft neutral studio light (no dramatic light, no strong cast shadows on the body), near-orthographic
camera, whole creature inside the frame with margins, transparent background, no floor, no shadow, no text.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Bat (giant bat) from the supplied original sprites, as a 3D modelling/texturing reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials, sharp fine
detail (fur strands, skin pores, scales, membrane veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a giant bat. Small compact body with short dark mauve-grey fur, slightly
lighter chest. Head with a short pointed muzzle, large upright pointed ears with pink inner skin, small GLOWING RED
eyes, two long ivory fangs. Huge leathery wings: membrane deep BLUE with fine darker vein/crack texture, wing
fingers and arm bones dark charcoal, scalloped trailing edge ending in points at each finger; small hook claw at
the wrist. Short hind legs hanging below the body with small pale claws.

Pose (as the native front fly sprite): wings spread wide and flat to both sides, nearly horizontal with the tips
slightly raised, membranes fully open; body upright in the middle, head facing forward, legs hanging down.

Do NOT: add extra limbs, tail, horns; do not fold the wings; do not change colours; do not crop the wingtips.
Checks per image: full wingspan inside the frame, red eyes, fangs, pink inner ears, blue veined membrane with dark
finger bones, legs and claws visible, same pose in all views, transparent background.
