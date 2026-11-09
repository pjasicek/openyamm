# Codex brief: HD reference views of the MM7 decoration statue `dec94` (winged woman on a plinth)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm7_3d/dressing/statues_hd/dec94/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs, in order:
1. `native_views_x7.png` — the ORIGINAL native MM7 sprite of this statue, enlarged with nearest neighbour.
   This is the DESIGN AUTHORITY (shape, pose, proportions, parts). The sprite is one view: the figure seen from her front-right, turned toward the image right, wings spread to the image left. The flat cyan (and any black border)
   is background, not part of the statue.
2. `x2_surface_only.png` — a restored 2x frame, for stone surface material only. It never sets the design.

## Deliverables (transparent background, 1024 x 1536 PORTRAIT, unresized returns, one statue per image)
- `00_three_quarter.png` — the statue from its front-left three-quarter (the statue's own front turned about 35
  degrees toward the image's right), camera a little above chest height (primary; generate first).
- `01_front.png` — straight front.
- `03_side.png` — the statue's own right side, so its front faces the image LEFT.
- `02_back.png` — straight back.
Generate 00 first and check it. Then generate 01, 03, 02 with 00 as an additional input so all four show the SAME
statue, pose and proportions. At most one corrective regeneration per view. Also write `generation_runs.json` (id,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and a `selected_views_review.png`
contact sheet of the selected views.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the statue painted in the
EXISTING Might and Magic VII decoration sprite, as a 3D modelling and texturing reference. Not a new design. The
object is a carved STONE SCULPTURE (one solid piece of weathered stone: warm brown-grey weathered sandstone), matte, slightly weathered, fine
chisel and grain detail, no paint except where stated. Whole statue visible and centred, filling about 80 % of the
frame height, near-orthographic camera, transparent background, no floor, no cast shadow, no text. Even soft
neutral studio light (no dramatic light; Meshy bakes light into the albedo).

Identity: a classical stone statue of a winged woman in the style of an ancient Greek victory figure: a nude
female figure with smooth, idealised, non-explicit sculpted anatomy (like a marble Nike or Venus), standing with her
weight on her left leg, the right foot slightly forward, both hands resting on her hips with the elbows out, chest
lifted, head turned up and to her left. Hair pulled back tight into a small bun. Two large feathered wings spring from
her shoulder blades and spread up and back (long splayed primary feathers, rows of coverts). She stands on a thick
rectangular stone plinth: a plain block with a thin top slab, the plinth about one quarter of the total statue
height.

Do NOT: do not add clothing, jewellery, a sword, a wreath or a halo; do not make the plinth stepped or ornate; do not add explicit detail; do not crop any part; do not add a floor, a backdrop, a second figure or text.

Checks per image: hands on the hips; head turned up; two feathered wings spread up and back; a thick block plinth with a thin top slab, about a quarter of the height; true transparent background; portrait 1024 x 1536; same statue as the primary.
