# Codex brief: HD reference views for the MM6 caged skeleton (hngncge2, bonecage)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm6_dungeons_3d/bones/skeleton/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `.../skeleton/references_hd/native_hngncge2_x3.png` — ORIGINAL native MM6 sprite `hngncge2` (hanging cage with a
   skeleton hung by its wrists), enlarged 3x with nearest neighbour. The skeleton's anatomy, proportions and warm
   bone colour authority. The black cage bars in front of it are NOT part of the skeleton.
2. `.../skeleton/references_hd/native_bonecage_x3.png` — ORIGINAL native MM6 sprite `bonecage` (a skeleton seated
   huddled in a cage), enlarged 3x with nearest neighbour; second anatomy reference. Bars are not part of it.
   Magenta in both is background.
3. `.../skeleton/references_hd/x2_hngncge2_surface_only.png` — restored 2x hngncge2, for bone surface material only.

## Deliverables (5 images, transparent background, 1024 x 1536 PORTRAIT, unresized returns)
- `00_three_quarter.png` — front-right three-quarter, camera at chest height, slightly above (primary; generate
  first)
- `01_front.png`, `02_back.png`, `03_left.png` (the skeleton's own left side), `04_right.png` (its right side)
Generate 01–04 with 00 as an additional input so all five show the SAME skeleton, SAME pose, SAME proportions. Also
write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and a `selected_views_review.png` contact sheet. Regenerate a view if it fails the checks.

The skeleton will be modelled in 3D, rigged and re-posed (hanging by the wrists, and seated huddled) for the two
cages, so it must stand in a clean neutral A-pose here, not in either sprite's pose.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the skeleton painted in
the EXISTING Might and Magic VI cage decoration sprites, as a 3D modelling and texturing reference. Not a new design.
ONE complete adult human skeleton, whole body head to toes, centred, generous margins, near-orthographic camera,
transparent background, no stand, no floor, no shadow, no text, no cage. Even soft neutral studio light (no dramatic
light) that still shows form. Credible anatomical sculpt, semi-realistic game material, sharp fine detail.

Identity: anatomically correct adult human skeleton, lean, average proportions (head about one eighth of the height):
skull with the lower jaw attached, mouth closed; cervical spine; collarbones and shoulder blades; a full rib cage of
twelve rib pairs with clear gaps between the ribs and a sternum; lumbar spine; a bowl-shaped pelvis; humerus, radius
and ulna as separate bones; hands with five separate finger bones each; femur, kneecap, tibia and fibula; feet with
separate toe bones. Colour from inputs 1 and 3: aged dry bone, warm honey-tan to pale cream on the highlights,
darker ochre-brown in the joints, between the ribs and in the sockets; eye sockets near black. Matte, no flesh, no
sinew, no blood.

Pose (identical in all five views): standing upright in an A-pose: arms straight, about 35 degrees away from the
sides, palms facing forward, fingers slightly spread and clearly separated; legs straight with a clear gap between
them, feet flat, toes forward; head level, looking straight ahead. No bone touches another limb.

Do NOT: add armour, cloth, rope, chains, a weapon, a stand, a cage, horns, glowing eyes, extra ribs or limbs; do not
stylise it (no cartoon, no oversized skull); do not colour it white or grey; do not crop the feet or the hands.

Checks per image: complete skeleton head to toes inside the frame; open rib cage with visible gaps; separate forearm
bones; five fingers per hand; arms clear of the body; legs apart; warm tan bone; true transparent background; same
pose and proportions as the primary.
