# Codex brief: seal emblems and one book cover for 3D ground items

Scope: image generation only. Write ONLY into `level_generation/props/items_letters_redo_20261018/codex/`. Do not edit
any other file and do not run builds. Use your built-in image generation tool. These are flat texture sources for
existing Might and Magic VII items (fantasy game asset restoration), not new designs.

## A. `emblems_raw.png` — eight seal emblems, one image
Input `emblem_reference_sheet.png` (2048 x 1024, four columns by two rows of 512 cells, magenta background) shows
each emblem as it sits on its letter in the game icon. Paint ONLY the emblems, in the same 4 x 2 layout and order,
each centred in its own cell and filling about 80% of the cell, seen exactly straight from above (no perspective),
on a fully TRANSPARENT background (no envelope, no paper, no shadow, no glow):

1. gold crescent ring brooch (open crescent/ring shape) with two small purple gems near its lower ends
2. green fern / leaf sprig emblem, three pairs of curled fronds from one stem
3. orange-red butterfly with spread wings and small antennae
4. green serpent in an S-wave, head at the upper left
5. polished silver-blue caduceus-like double serpent ornament with a central drop
6. red bat with spread pointed wings
7. ivory skull with dark eye sockets and nose, teeth
8. round red wax seal with a raised rosette/flower impression

Keep each emblem's exact shape, proportions and colours from its reference cell, but crisp and clean at high
resolution. Base colour only: even flat light, no strong highlights, no cast or drop shadows, no ambient occlusion
outside the shape. Output 2048 x 1024 PNG with alpha. If the tool cannot return transparency, use a flat pure
magenta (#ff00ff) background instead and say so.

## B. `item320_cover.png` and `item320_spine.png` — Prophecies of the Snake
Input `item320_icon_x8.png` shows the closed book at an angle (magenta background). Deliver:
- `item320_cover.png`: the FRONT COVER only, straight-on and square to the frame (no perspective), filling the WHOLE
  image edge to edge (no background, no page edges, no spine, no thickness). Landscape 1536 x 1024. Deep red leather
  with gold corner ornaments and border, and the large golden scaled cobra/snake head motif centred with red eyes,
  as in the icon. Even flat light, no strong highlights, no shadows, no lettering.
- `item320_spine.png`: the spine straight-on, 1536 x 256 landscape strip, same red leather with gold raised bands and
  small gold ornaments, no lettering.

Save each generated file (copy the tool's output) to the names above inside `codex/`, and write
`codex/generation_runs.json` listing for each output: prompt, inputs, the original generated file path, and size.
At most one corrective regeneration per image.
