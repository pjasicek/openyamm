# P5 shrine and Rest Stop props (D-56), 2026-11-21

Lane S sub-agent `xeen-s7-p5`. The Cube and the Scepter in the stone hands (D-56 change 4), the wedding cake on its
table and the Rest Stop bench (shipped first). No Meshy, no Codex. The stone hands themselves are
[xeen_p5hands_claude](../xeen_p5hands_claude/README.md); all six rows were appended by `scripts/append_rows.py
rows.json --apply` (append only; refuses a taken row, sprite or name).

| Decoration | Row / sprite | Model | Binding | Radius / height (row) |
|---|---|---|---|---|
| `xeen_cube` "Cube of Power" | 4019 / 27019 | `worlds/xeen/world_items/models/item_xeen_12365.glb` (installed ground item, 39.6 cube) | height 84 (2.12x), `z_offset` 394, yaw offset 0 | 0 / 84 |
| `xeen_scepter` "Xeen's Scepter" | 4020 / 27020 | `worlds/xeen/world_items/models/item_xeen_12366.glb` (installed ground item, 48.6 long, 6.04 high) | height 21.7 (3.6x: 175 long), `z_offset` 398, `yaw_offset` -90 deg (east-west at facing 0) | 0 / 22 |
| `xeen_cake` "wedding cake" | 4021 / 27021 | `worlds/xeen/models/xeen_deco_cake.glb` (new: MM9 round table + built cake) | height 161.6, `yaw_offset` -90 deg | 82 / 162 |
| `xeen_bench` "bench" | 4022 / 27022 | `worlds/xeen/models/xeen_deco_bench.glb` (MM9 `mm9_deco_bench01.glb`, installed as a copy) | height 56, `yaw_offset` -90 deg | 40 / 56 |

All bindings in `assets_dev/worlds/xeen/models/indoor_decorations.yml` (P5 is a BLV), `yaw: facing`; sprites use the
engine's `pending` texture. Nothing references `worlds/mm9/`.

## Placement (for A5)

- **Cube and Scepter**: place each at its hand's own xy and floor (the dais top), **facing 0**, hidden until
  `state:wedding`: the binding's `z_offset` lifts it onto the palm (palm centre 390 over the hand's origin). This is
  what A5's generator does already (`decor:cube` (-384, -320) and `decor:scepter` (384, -320) are the hands' spots).
  The Cube (84) sits in the west palm; the Scepter lies across the east palm, its clock-face head to one side. No
  collision (radius 0).
- **Cake** (`landmark:cake`, (576, 832) in the pavilion): MM9's round table (165 across, 92 high) with a three-tier
  white-and-gold cake (gold stand plate, piping rings, a small double-ring topper; 69 high) on it; 162 overall. Origin
  at the table's foot centre; facing is free (round). Collision radius 82.
- **Bench**: MM9's backless plank bench, 92 x 50, seat 56 high; origin at its centre; its long side is its front, so
  A5's facing (the hut's facing, `yaw_offset` -90 deg) puts it along the hut's front, the sitter facing the road.
  Collision radius 40 (covers the depth, not the full length).

## Models

- `scripts/build_cake.py`: a copy of `assets_source/worlds/mm9/models/mm9_deco_roundtable.glb` (90 triangles, two
  materials) with the built cake appended as a third primitive and material (1,968 triangles, a 512 x 256 atlas: icing
  with faint swags, gold). One mesh, no LOD chain (2,058 triangles in all; the MM9 table has none either). Winding: 0
  inverted closed parts (after the piping tori were turned outward).
- The bench is `mm9_deco_bench01.glb` unchanged (68 triangles), installed with `--name xeen_deco_bench.glb`; candidates
  rendered in `review/cand_sheet.png` (bench03, the marble benchstone01 with a back) were not used.
- The Cube and the Scepter are the ground-item models bound again (`review/items_sheet.png`); no new model.

## Checks

In game on X6 (`build-xeen`; scratch overlay `scripts/ingame_overlay.py` -> `work/ingame/mount`: the six decorations as
entities on open ground at (4096, -9216), outdoor copies of these bindings in an overlay `decorations.yml`, the
Pharaoh's binding in an overlay `actors.yml`; nothing written to `assets_dev` by it): `review/ingame/sheet.jpg` (front,
close, both three-quarters, the cake, the bench, from far, with the Pharaoh spawned behind) and `sheet4.jpg` (the palms
from above and the side, the pair at eye height; free camera through `debug.screenshot_tour_path`, `work/ingame/shots.yml`).
No model or binding errors in the run logs.

## Known limits

- The Scepter lies flat (a decoration binding cannot stand it up, and D-56 asks for no new model): from the dais's
  foot it shows as a dark bar over the east palm; the cinematic's close shot from above shows its head.
- The cube's flat base meets a palm that slopes 14 deg to the front: about 5 units sunk at the heel side, 12 clear at
  the front edge.
- The table keeps MM9's dark wood (no cloth) under the white pavilion.
- None of these is seen on P5 itself yet (A5 places them).
