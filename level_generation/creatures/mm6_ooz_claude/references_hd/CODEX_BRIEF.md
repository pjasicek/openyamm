# Codex brief: HD reference views for the MM6 Ooze (mm6_ooz_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ooz_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation. Record format as in
`level_generation/creatures/new_sorpigal_3d_stage1_20261006/gua/generation_runs.json`. Attached inputs, in order:
1. `references_hd/native_views.png` — the ORIGINAL native low-res standing sprites, five views side by side
   (front, front three-quarter, side, rear three-quarter, back), enlarged with nearest neighbour. Magenta is
   background, not creature. Design, shape and colour authority.
2. `level_generation/creatures/mm6_ooz/native/oozata.png` — native attack frame (a pseudopod rises from the puddle):
   only to understand the material; do NOT draw a pseudopod in the deliverables.

## Deliverables (5 images, transparent background, 1536 x 1024 landscape, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera above at about 30 degrees elevation (primary; generate first) |
| `01_front.png` | front, camera at about 20 degrees elevation |
| `02_back.png` | back, camera at about 20 degrees elevation |
| `03_left.png` | the creature's left side, camera at about 20 degrees elevation |
| `04_right.png` | the creature's right side, camera at about 20 degrees elevation |

Generate 01–04 with 00 as an additional input so all five show the SAME blob with the same lobes and lumps.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Ooze from the supplied original sprites, as a 3D modelling and texturing reference. Not a new design.

Identity (from the native sprites): a low, flat puddle of thick green slime, roughly oval, only slightly longer than
it is wide (about 1.2 : 1; the native side view is 295 px long, the front view 252 px wide), and its height only about
one fifth of its length. The rim is irregular and lobed, made of many rounded
bulging lumps of different sizes that hang slightly over the floor line; a few small droplet lumps sit just outside
the rim. The top surface is gently domed and covered with soft rounded bumps and shallow dimples, like thick bubbling
jelly. Material: wet, glossy, semi-opaque vivid green slime (saturated mid green, darker green in the creases and
under the lumps, lighter yellow-green on top of the bumps), with small soft specular glints. No eyes, no mouth, no
face, no bones, no objects inside.

Camera and light: one complete blob centred with generous margins, near-orthographic camera, even soft neutral
studio light from above (no dramatic shadows, no coloured light, no rim light), transparent background, no floor,
no cast shadow, no text.

Do NOT: add eyes, teeth, a face, bubbles floating in the air, skulls or bones inside, a pseudopod or tentacles, a
floor, puddle reflections, drips in the air; change the colour; crop the rim.

## Checks per image

Whole blob in frame with margins; flat proportions (height about one fifth of the length, length about 1.2 x the
width); lobed rim with rounded
lumps; vivid green; no face or added features; transparent background; 1536 x 1024; the same blob as `00`.
