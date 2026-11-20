# Codex brief: HD reference views for the MM6 Bloodsucker (winged serpent) (mm6_bld_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bld_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `level_generation/creatures/mm6_bld_claude/references_hd/native_views.png` — ORIGINAL native MM6 sprite views, enlarged 2x
   with nearest neighbour, left to right: front, front three-quarter, profile (creature's right side shown), rear
   three-quarter, back. Magenta is background, not creature. This is the design, anatomy, pose and palette authority.
2. `level_generation/creatures/mm6_bld/aligned_2x/bldflya1.png` — restored 2x frame, for surface material only (never the design).

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
Magic VI Bloodsucker (winged serpent) from the supplied original sprites, as a 3D modelling/texturing reference. Not a new design.
Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials, sharp fine
detail (fur strands, skin pores, scales, membrane veins), as if a high-quality sculpt of the sprite.

Identity (from the native sprites): a flying serpent-dragon. Long thick body tapering into a very long tail; dark
TEAL-GREEN scaly hide with darker transverse stripes; salmon/pink-red underside on the belly. A row of ivory SPIKES
along the spine and the whole tail. Head: blunt, with a huge round open MAW at the front ringed by small ivory teeth,
the maw interior salmon/red; small glowing CYAN eyes on the sides of the head. Two large bat-like wings rising from
the shoulders: tan/beige leathery membrane, ivory BONE struts and finger bones with knobbed ends. Four short legs
with dark clawed feet hanging under the body.

Pose (as the native fly sprites): body roughly horizontal and slightly curved, head forward with the maw open, tail
trailing behind and gently curving, wings raised high in a V above the back (spread, not folded), legs hanging.

Do NOT: add a second head, horns, rider or armour; do not close the maw; do not change colours; do not crop wings or tail.
Checks per image: maw with teeth ring, cyan eyes, spine/tail spikes, striped teal body with salmon belly, tan wings
with ivory struts, four legs, same pose in all views, transparent background.
