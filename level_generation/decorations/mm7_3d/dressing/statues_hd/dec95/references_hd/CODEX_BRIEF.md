# Codex brief: HD reference views of the MM7 decoration statue `dec95` (knight leaning on a sword, on a plinth)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm7_3d/dressing/statues_hd/dec95/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs, in order:
1. `native_views_x12.png` — the ORIGINAL native MM7 sprite of this statue, enlarged with nearest neighbour.
   This is the DESIGN AUTHORITY (shape, pose, proportions, parts). The sprite is one view, straight front. The flat cyan (and any black border)
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
object is a carved STONE SCULPTURE (one solid piece of weathered stone: speckled warm grey granite), matte, slightly weathered, fine
chisel and grain detail, no paint except where stated. Whole statue visible and centred, filling about 80 % of the
frame height, near-orthographic camera, transparent background, no floor, no cast shadow, no text. Even soft
neutral studio light (no dramatic light; Meshy bakes light into the albedo).

Identity: a stone statue of a knight in full plate armour standing upright: a ROUNDED great helm (a barrel or
bucket helm with a domed top, a slight brow ridge and one narrow horizontal eye slit cut into the front), smooth
rounded pauldrons, a plain breastplate, a short fauld over the hips, plate arms with gauntlets, plate legs and
sabatons. His RIGHT hand rests on the pommel of a straight cross-hilted longsword standing upright beside his right
foot, its point on the plinth. His LEFT arm hangs at his side. He stands on a sloped stone plinth: a low truncated
pyramid (wider at the bottom) about one fifth of the total statue height.

Do NOT: do not add spikes, a crest, a plume, a shield, a cape or a visor that is open; do not make the helm flat-topped or cubic; do not crop any part; do not add a floor, a backdrop, a second figure or text.

Checks per image: rounded great helm with a narrow eye slit; smooth plain plate armour without spikes; right hand on the pommel of an upright straight sword whose point stands on the plinth; sloped truncated-pyramid plinth; true transparent background; portrait 1024 x 1536; same statue as the primary.
