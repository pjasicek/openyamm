# Codex brief: HD reference views for the MM6 skull pile decoration (sklplrev)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm6_dungeons_3d/bones/skullpile/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `.../skullpile/references_hd/native_front_x3.png` — the ORIGINAL native MM6 sprite `sklplrev` (214 x 153 px),
   enlarged 3x with nearest neighbour. It is the only native view (the game shows the same front view from every
   side). Magenta is background, not part of the pile. This is the design, shape, proportion and palette authority.
2. `.../skullpile/references_hd/x2_surface_only.png` — restored 2x frame, for surface material only (bone surface
   detail). It never sets the design.

## Deliverables (5 images, transparent background, 1536 x 1024 LANDSCAPE, unresized returns)
- `00_three_quarter.png` — the pile seen from the front, camera raised about 25 degrees above the pile's mid-height
  so the top of the heap and its depth are visible (primary; generate first)
- `01_front.png` — the front, camera level with about a third of the pile height (as the native sprite)
- `02_back.png` — the same pile from behind (camera turned 180 degrees round it, same height as 01)
- `03_left.png` — the same pile from its left side (camera turned 90 degrees), same height as 01
- `04_right.png` — from its right side, same height as 01
Generate 01–04 with 00 as an additional input so all five show the SAME pile, the SAME outline and proportions,
seen from four sides. Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it fails the checks.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI dungeon decoration "skull pile" from the supplied original sprite, as a 3D modelling and texturing
reference. Not a new design. ONE free-standing heap of human skulls, centred, generous margins, near-orthographic
camera, transparent background, no floor, no ground shadow, no scenery, no text. Even soft neutral studio light
(no dramatic light, no strong cast shadows) that still shows the round forms. Credible, fully three-dimensional,
semi-realistic game materials, sharp fine detail (bone pores, sutures, chips, teeth).

Identity (from the native sprite): a broad rounded conical mound of about sixty to eighty human skulls heaped
loosely on one another, about 1.4 times as wide as it is tall, with a rounded top and gently sloping sides that
spread out at the base; the outline is lumpy, made of the skulls' round crowns. All skulls are the same adult human
size (about one seventh of the pile width), crania with the upper teeth; most have no lower jaw, a few keep one.
They face every way: many face outward with dark eye sockets and nasal holes, others show the back or top of the
smooth domed cranium, some lie on their sides, a few tilt upside down. Deep dark gaps between the skulls.
Colour: aged bone, pale cream to warm yellowish ivory on the crowns and cheekbones, greying to dusky olive-grey and
cool blue-grey in the hollows, eye sockets near black. Matte to slightly waxy bone, no blood, no flesh.

Do NOT: add bones other than skulls (no ribs, no long bones, no full skeletons), candles, rocks, a base, a floor,
moss, blood, glowing eyes, horns, animal or monster skulls; do not change the colour to white or brown; do not make
it a tall tower or a flat spread; do not crop the pile.

Checks per image: one mound, about 1.4 : 1 width to height; only human skulls of one size; varied orientations; cream
bone with grey-olive hollows; nothing cropped; true transparent background; same pile as the primary.
