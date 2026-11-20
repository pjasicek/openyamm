# Codex brief: HD reference views of the MM7 decoration statue `7dec55` (walking dwarf with a club)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm7_3d/dressing/statues_hd/7dec55/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs, in order:
1. `native_views_x4.png` — the ORIGINAL native MM7 sprites (five directional views) of this statue, enlarged with nearest neighbour.
   This is the DESIGN AUTHORITY (shape, pose, proportions, parts). Left to right: a0 front, a1 front three-quarter, a2 side (the dwarf faces the image left, so his RIGHT side faces the camera), a3 back three-quarter, a4 back. The colours painted on a4 are an original art error: the statue is stone all round. The flat cyan (and any black border)
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
object is a carved STONE SCULPTURE (one solid piece of weathered stone: grey-green weathered granite), matte, slightly weathered, fine
chisel and grain detail, no paint except where stated. Whole statue visible and centred, filling about 80 % of the
frame height, near-orthographic camera, transparent background, no floor, no cast shadow, no text. Even soft
neutral studio light (no dramatic light; Meshy bakes light into the albedo).

Identity: a stocky dwarf caught mid-stride, as in a0 and a2: his RIGHT leg forward, LEFT leg back on its toes,
leaning forward. A pointed soft cap whose tip flops forward over the brow; a long full beard to the belly; a
fur-trimmed vest (thick fur collar and hem) over a tunic, a wide belt, heavy boots. His RIGHT arm hangs a little back,
the hand holding a short, heavy knobbed club that points down and forward; his LEFT fist swings forward at belly
height. All one stone colour. No plinth: he stands directly on the ground.

Do NOT: do not add a helmet, horns, an axe, a shield, a cape or a plinth; do not colour any part; do not make it cartoonish; do not crop any part; do not add a floor, a backdrop, a second figure or text.

Checks per image: mid-stride with the right leg forward; pointed cap with the tip falling forward; long beard; fur collar; club in the RIGHT hand pointing down and forward; true transparent background; portrait 1024 x 1536; same statue as the primary.
