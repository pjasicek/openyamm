# Codex brief: HD reference views of the MM7 decoration statue `7dec54` (horned dwarf warrior with a double axe)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm7_3d/dressing/statues_hd/7dec54/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs, in order:
1. `native_views_x4.png` — the ORIGINAL native MM7 sprites (five directional views) of this statue, enlarged with nearest neighbour.
   This is the DESIGN AUTHORITY (shape, pose, proportions, parts). Left to right: a0 front, a1 front three-quarter, a2 side (the dwarf faces the image left, so his RIGHT side faces the camera), a3 back three-quarter, a4 back. The flat cyan (and any black border)
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
object is a carved STONE SCULPTURE (one solid piece of weathered stone: dark green-grey granite with gilded inlays), matte, slightly weathered, fine
chisel and grain detail, no paint except where stated. Whole statue visible and centred, filling about 80 % of the
frame height, near-orthographic camera, transparent background, no floor, no cast shadow, no text. Even soft
neutral studio light (no dramatic light; Meshy bakes light into the albedo).

Identity: a stocky, broad-shouldered dwarf warrior standing square, feet apart, knees slightly bent, as in a0
and a4. Horned helmet: a smooth dark iron dome, a broad GOLD rim band with rivets, a short gold central spike on top
and two thick, round, tapering GOLD horns curving out and up from the dome's sides (each with a gold collar at its
root). Stern face, heavy brows, big nose; a long full beard of carved strands reaching the belt. A studded leather
jerkin with short shoulder flaps over a chainmail shirt; a chainmail skirt to above the knees; a wide belt with a
square buckle. Bare muscular forearms with wide GOLD bracers and GOLD arm rings; heavy boots with GOLD rings at the
boot tops. His RIGHT hand holds a double-bladed battle axe low beside his thigh, the dark haft angled back and up
behind him, the two crescent axe blades behind his right hip (see a2); his LEFT fist is clenched at his side. The
statue is stone; the gold parts are gilded brass. No plinth: he stands directly on the ground.

Do NOT: do not add a cape, a shield, a second weapon, a plinth or wings; do not change the horn count (two horns plus one central spike); do not make it cartoonish; do not crop any part; do not add a floor, a backdrop, a second figure or text.

Checks per image: two thick round gold horns plus a central spike; gold rim, bracers, arm rings and boot rings; long beard to the belt; mail shirt and skirt; axe in the RIGHT hand with its blades behind the right hip; true transparent background; portrait 1024 x 1536; same statue as the primary.
