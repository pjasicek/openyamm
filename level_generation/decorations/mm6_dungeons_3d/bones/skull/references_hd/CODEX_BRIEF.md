# Codex brief: HD reference views for one MM6 human skull (torskul0 skull torch, skull pile)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm6_dungeons_3d/bones/skull/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool (prompt style and record format as in
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `.../skull/references_hd/native_torskul0_x4.png` — ORIGINAL native MM6 sprite `torskul0` (skull torch: three
   skulls round a fire cup on a post), enlarged 4x with nearest neighbour. The skulls' SHAPE authority: high rounded
   domed cranium, long face, deep sockets, lower jaw present, mouth closed. Their orange colour is firelight; ignore it.
2. `.../skull/references_hd/native_pile_skulls_x5.png` — ORIGINAL native MM6 sprite `sklplrev` (skull pile), the
   upper part enlarged 5x with nearest neighbour: front and three-quarter skull faces. The BONE COLOUR authority.
   Magenta in both is background.
3. `.../skull/references_hd/x2_pile_surface_only.png` — restored 2x skull pile, for bone surface material only.

## Deliverables (5 images, transparent background, 1024 x 1024 SQUARE, unresized returns)
- `00_three_quarter.png` — the skull from its front-right three-quarter, camera slightly above the eyes (primary;
  generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (the skull's own left side), `04_right.png` (its own right side), all
  with the camera level with the eye sockets.
Generate 01–04 with 00 as an additional input so all five show the SAME skull. Also write `generation_runs.json`
(id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet. Regenerate a view if it fails the checks.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the skull painted in
the EXISTING Might and Magic VI decoration sprites, as a 3D modelling and texturing reference. Not a new design. ONE
complete adult human skull with its lower jaw (mandible) attached and the mouth closed, upright and looking straight
ahead (Frankfort plane level), centred, filling about 70 % of the frame, near-orthographic camera, transparent
background, no stand, no floor, no shadow, no text. Even soft neutral studio light (no dramatic light), sharp fine
detail: sutures, pores, small chips, worn teeth.

Identity: anatomically correct human skull, a little heavy-browed as in the sprites: high smooth rounded cranium,
deep round eye sockets (near black inside), triangular nasal opening, prominent cheekbones, full upper and lower rows
of worn teeth meeting, strong lower jaw. Colour from input 2: aged bone, warm cream to pale yellowish ivory on the
dome, brow and cheekbones, darkening to dusky olive-grey and brown-grey in the sutures, temples, under the cheekbones
and round the teeth. Matte, slightly waxy, old and dry; no flesh, no blood.

Do NOT: add horns, cracks that split the skull, gold teeth, glowing eyes, candles, a stand or a spine; do not make it
cartoonish, elongated or alien; do not colour it orange, white or brown; do not crop it.

Checks per image: one human skull with its lower jaw, mouth closed; correct anatomy (sockets, nasal opening,
cheekbones, teeth rows, mastoids, foramen magnum visible only from below); cream bone with grey-olive hollows; the
side views agree with the front; true transparent background; same skull as the primary.
