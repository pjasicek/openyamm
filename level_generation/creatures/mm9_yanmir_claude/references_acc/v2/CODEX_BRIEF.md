# Codex brief: staff pole texture for MM9 Yanmir (mm9_yanmir_claude, follow-up)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yanmir_claude/references_acc/v2/`. No builds, no Meshy. Use your built-in
image generation tool. This is a flat seamless TEXTURE TILE for a video-game staff's pole, not a picture of a staff.

## Inputs (attached, in order)
1. `mm9_staff_views.png`: the ORIGINAL 2002 game staff (head front, head side, a piece of its pole close up, the whole staff): the pole's material
   and colour authority (third panel).
2. `mm9_shaft_crop.png`: the original pole close up.

## Deliverable
`pole_tile.png`: 1024 x 512 (landscape), opaque, no text, flat even lighting (a colour map: no cast shadows, no perspective, no highlights from a
light). SEAMLESS left-right AND top-bottom (the left edge continues the right edge, the top the bottom). Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path). At most one corrective regeneration.

Content: the surface of the original staff's pole, as inputs 1 and 2: a hard, old, knotted pale wood or speckled stone, mottled grey-brown, beige
and off-white with irregular dark brown-black speckles and short dark streaks, a few small knots, fine grain running LEFT TO RIGHT. Mid-tone overall
(not white, not dark), the same palette as input 2, sharp fine detail. Evenly spread, no large single feature, no seams, no borders.
