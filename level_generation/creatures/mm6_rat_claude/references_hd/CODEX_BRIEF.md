# Codex brief: HD reference views for the MM6 Giant Rat (mm6_rat_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_rat_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `level_generation/creatures/mm6_rat_claude/references_hd/native_views.png` — ORIGINAL native MM6 sprite views, enlarged 2x
   with nearest neighbour, left to right: front, front three-quarter, profile (creature's right side shown), rear
   three-quarter, back. Magenta is background, not creature. This is the design, anatomy, pose and palette authority.
2. `level_generation/creatures/mm6_rat/trimmed_2x/ratsta1.png` — restored 2x frame, for surface material only (never the design).

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
Magic VI Giant Rat from the supplied original sprites, as a 3D modelling/texturing reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials, sharp fine
detail (fur strands, skin pores, scales, membrane veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a large hunched sewer rat. Dense dark charcoal fur with a subtle green-grey cast
over the high arched back and body; bare wrinkled grey-green skin on the head, muzzle, ears, the long thin legs and
the long naked tail. Large round amber-orange eyes with dark pupils, small rounded ears, long muzzle with whiskers,
two prominent yellowed ivory incisors, mouth slightly open. A dark leather COLLAR with short ivory/silver SPIKES
around the neck. Long thin legs with large clawed feet, long pale claws.

Pose (as the native standing sprites): crouched on all four feet, back strongly arched high, head held forward and
slightly low, muzzle pointing forward, tail lying out behind on the ground and curving slightly. All four feet
visible, tail fully visible.

Do NOT: add armour, saddle, extra limbs, red glowing eyes; do not change colours; do not crop the tail.
Checks per image: arched back, amber eyes, spiked collar, incisors, naked tail, long clawed feet, same pose in all
views, transparent background.
