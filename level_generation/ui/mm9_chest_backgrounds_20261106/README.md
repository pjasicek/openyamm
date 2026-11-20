# MM9 chest-screen backgrounds (2026-11-06)

The MM9 chest and treasure-bag inventory backgrounds (`assets_dev/worlds/mm9/icons_x2/mm9_chest.png`,
`mm9_treasure_bag.png`, 920x688, x2 of the 460x344 `ChestBackground`) were regenerated because their item grid
(`engine/data_tables/chest_data.txt`: offset 42,34 and 18,30, 9x9 cells of 32) did not sit on the chest floor: the
chest's grid overlapped its left iron band and front rim while the floor ran past the grid on the right, and the bag's
rope and coins cut into the grid. MM6-MM8's chests (`engine/icons_x2/chest01-08.png`) put the floor just around the
grid, the rim outside it and the open lid on the right; the new backgrounds follow that.

- `refs/*_layout.png`: the layout guide from the grid (floor = grid + 6 units, rim, lid or bag side);
  `refs/*_style.png`: the previous art (`originals/`) as the style reference.
- `gen.py NAME VERSION`: one `codex exec` image worker with both references (prompts in `prompts/`, results in `raw/`).
- `fit.py RAW NAME LEFT TOP RIGHT BOTTOM [--install]`: scales the result per axis so its measured floor edges land on
  the grid's floor box, writes `final/` and `review/*_fit.png` (grid drawn), and installs with `--install`.

Accepted: `mm9_chest_v1` (floor 122,98-1055,975, scale 0.643 x 0.684) and `mm9_treasure_bag_v2` (floor 78,93-1007,977,
scale 0.646 x 0.679; its right 9 pixels are padded). `review/raw_sheet.png` shows all four variants.
