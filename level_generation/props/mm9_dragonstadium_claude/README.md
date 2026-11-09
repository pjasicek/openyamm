# MM9 Dragon Stadium props as 3D decorations (2026-10-31)

The three lying skeletons and the two chests of MM9's Dragon Stadium (`DRAGONSTADIUM.dat`) as OpenYAMM 3D decorations
for the native BLV ([map project](../../projects/mm9r_dragonstadium/)). Route: Connecting Tunnels' props project
([`../mm9_connectingtunnels_claude/`](../mm9_connectingtunnels_claude/README.md)), its `props_table.py`, `tables.py`
and `placements.py` copied and adapted. Both props are MM9 models already installed by other projects, so nothing is
built here: no GLB, no texture, no Meshy, no Codex.

## Outputs

- **Reused models** (same ABC and skin; GLBs, rows and bindings stay with their owners):
  - `blackchest` (`models/props/BlackChest.ABC`, `skins/props/BlackChest.dtx`): the Lich Lab's
    `mm9_deco_blackchest.glb`, row `mm9_blackchest` (2078) at Scale 1: TreasureChest0, TreasureChest1.
  - `skeletonlayingprop` (`models/props/SkeletonLaying.ABC`, `skins/props/Skeleton.dtx`): Connecting Tunnels'
    `mm9_deco_skeletonlayingprop.glb` (the Ruined Temple's `skeletonlaying` is another skin), placed at MM9's Scale 1.5:
    Prop0-2 (BonePile).
- **One new row** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`: **2452** `mm9_skeletonlayingprop_x150`
  (skeleton, radius 104, height 46: MM9's Solid 1, the base row's collision x 1.5), sprite **26253** (pending), indoor
  binding (height 45.9) in `worlds/mm9/models/indoor_decorations.yml`; appended by `tables.py --apply`, which takes
  `mm9r_common/locks/mm9_decorations.lock` and re-reads the next free numbers inside it.
- `../../projects/mm9r_dragonstadium/props.json`: **5 placements** (3 bone piles, 2 chests), the old map's frame (the
  BLV keeps it).

## Fit to the old map's bake

Each placement against the old map's baked BModel (`MM9_static_prop_<object>_<name>`, `MM9_chest_...`), the Dook's
Castle / Thjorad way: **5 baked placements, median of medians 0.65 units, worst 0.78** (TreasureChest0).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_dragonstadium_claude
python3 scripts/props_table.py          # work/raw_objects_compact.json, binding origins
python3 scripts/tables.py --apply       # the one new row (takes the decorations lock itself)
python3 scripts/placements.py           # props.json
python3 ../../projects/mm9r_common/review_root.py
```

Review: the props in the map's tour sheets (`../../projects/mm9r_dragonstadium/review/v02_compare.jpg`, views d01-d03):
the chests and skeletons stand where MM9's do, upright, at MM9's size.
