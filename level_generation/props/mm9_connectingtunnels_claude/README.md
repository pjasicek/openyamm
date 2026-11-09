# MM9 Connecting Tunnels props as 3D decorations (2026-10-31)

The mine lanterns, candles, lying skeletons, barrels, crates, sacks, rubble and the two chests of MM9's Connecting
Tunnels (`CONNECTINGTUNNELS.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for the native
BLV ([map project](../../projects/mm9r_connectingtunnels/)). The route is Thjorad Mine's props project
([`../mm9_thjoradmine_claude/`](../mm9_thjoradmine_claude/README.md)), scripts copied and adapted: one material per MM9
skin, the isle's `blib` build and `finish` checks, plus Dook's Castle's `TILTS` (pitch and roll baked into a variant).
No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the isle's
`textures.upscale`).

## Outputs

- **17 models built here**, installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` in `finish.py` (0 inverted closed
  parts each):

| Prop | ABC / skin | Triangles | Placements | Notes |
| --- | --- | --- | --- | --- |
| `minelantern02plain` | MineLantern02 / MineLantern | 87 | 45 | Thjorad's `minelantern02` is the `minelantern-bright` skin (another file) |
| `skeletonlayingprop` | SkeletonLaying / Props/Skeleton | 519 / 258 / 129 | 9 (BonePile0-8) | the Ruined Temple's `skeletonlaying` is `skins/skeleton2.dtx` (md5 differs) |
| `sack02` | Sack02 / Sack01 | 128 | 2 | |
| `sack01` | Sack01 / Sack01 | 128 | 0 | upright; built first, its one placement is tilted (below); kept for other maps |
| `stonedebris01ls`, `04ls`, `05ls` | StoneDebris01/04/05 / LumberStoneDebris | 48, 112, 96 | 0 | upright; likewise kept (the Ruined Temple's `stonedebris04`/`05` use other skins) |
| `stonedebris01lsp350` | StoneDebris01 / LumberStoneDebris, pitch -10.3 | 48 | Prop5 | tilted variant |
| `stonedebris04lsp350` | StoneDebris04, pitch -10.3 | 112 | Prop6 | tilted variant |
| `stonedebris04lsp7` | StoneDebris04, pitch +6.9 | 112 | Prop3 | tilted variant |
| `stonedebris05lsp350` | StoneDebris05, pitch -10.3 | 96 | Prop7 | tilted variant |
| `stonedebris02p350` | StoneDebris02 (the isle's model and skin), pitch -10.3 | 32 | Prop8 | tilted variant |
| `lumberstone03p10` | LumberStoneDebris03 (Drangheim's), pitch +10 | 112 | Prop4 | tilted variant |
| `cratep356` | Crate (Anskram's), pitch -4.4 | 12 | Prop9, 10, 12 | tilted variant |
| `crater355` | Crate, roll -4.8 | 12 | Prop14 | tilted variant |
| `barrelp356` | Barrel (Anskram's), pitch -4.0 | 192 | Prop13 | tilted variant |
| `sack01p350r356` | Sack01, pitch -10.5, roll -4.0 | 128 | Prop17 | tilted variant |

- **Reused** (same ABC and skin; GLBs, rows and bindings stay with their owners; each owner's work GLB is byte-identical
  to the installed one): Anskram Keep's `barrel` (`mm9_barrel_x100`, row 2076, 8), `barrel03` (`mm9_barrel03_x100`,
  2176, 3), `crate` (`mm9_crate`, 2029, 8); the Temple of Honk's `chest3` (`mm9_chest3`, 2055, TreasureChest0); Lich
  Lab's `blackchest` (new scale row, below; TreasureChest1); Tasar Academy's `candle` (`mm9_candle`, 2306, 28: `card`
  flame billboards seated on the wick, checked in the GLB: `Fire` material `openyamm_billboard: card`, flipbook 16x4);
  Drangheim Prison's `sack03` (`mm9_sack03`, 2193, 2). Drangheim's `lumberstone03` and the isle's `stonedebris02` are
  the sources of tilted variants here, not placed upright.
- Rows **2417-2434** (18 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26218-26235**,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in two `tables.py --apply` runs (it takes
  `mm9r_common/locks/mm9_decorations.lock` itself and re-reads the next free numbers inside it): `mm9_blackchest_x95`
  (2417, the coffin chest at Scale 0.95, height 67.2), `mm9_minelantern02plain` (2418), `mm9_sack01` (2419),
  `mm9_sack02` (2420), `mm9_skeletonlayingprop` (2421), `mm9_stonedebris01ls`/`04ls`/`05ls` (2422-2424), then the ten
  tilted variants 2425-2434 (`mm9_barrelp356` ... `mm9_stonedebris05lsp350`). The isle's outdoor-only
  `mm9_stonedebris02` row also got an indoor binding (written by the first run; not placed after the tilts). No row
  carries a light: the lanterns' and candles' light is the map's BLV or bake lights.
- `../../projects/mm9r_connectingtunnels/props.json`: **119 placements** (77 props, 28 candles as `torch`, 9 bone
  piles, 3 barrels, 2 chests: TreasureChest0 `mm9_chest3`, TreasureChest1 `mm9_blackchest_x95` inside the coffin),
  each with `source_name`, `decoration`, `x/y/z`, `yaw_degrees`, `script`/`script_params` (all null: the map has no
  `.scr` scripts on its props) as Thjorad's `placements.py` writes them.
- `review/props_sheet.png`: contact sheet of the 17 built models (looked at); `review/<prop>/`: the review renders.

## Fit to the old map's bake

Each placement is checked against the old map's baked BModel (`MM9_static_prop_<object>_<name>`, `MM9_chest_...`) the
Dook's Castle / Thjorad way (finished LOD0 placed as the engine places it, median vertex distance): **85 baked
placements, median of medians 0.56 units, worst 1.15** (Prop11, an upright crate). Before the tilted variants the worst
was 8.4 (Prop8, rubble at -10.3 degrees on the ramp; the crates and sack on the sloping floor 6-7).

**34 not baked by the old import**: mine lantern18-52 (the old import baked only lanterns 7-17). They are placed by the
transcoder's rule (binding origin, MoveToFloor 0, no drop); that rule puts the 11 baked lanterns within 0.7 units of
their bakes (bounding-box centres), so the unbaked ones are as reliable.

Bake lookups replace spaces in DAT names with `_` (`mine lantern10` -> `MM9_static_prop_2_mine_lantern10`).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_connectingtunnels_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply                 # takes the decorations lock itself
python3 scripts/placements.py
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py -- && bash scripts/contact_sheet.sh
```

## Notes

- **Tilts**: decorations turn by yaw only, and MM9 pitches or rolls twelve props by 4-10 degrees (the ramp's rubble,
  crates, a barrel and a sack on a sloping floor). `props_table.TILTED` gives each distinct (pitch, roll) its own model
  with the tilt baked in (`build.py` `tilt_matrix`, no LODs), read from the DAT (the objects of one variant must share
  their rotation exactly, checked). Named `<prop>p<pitch deg>r<roll deg>` as Verhoffin's and Yanmir's variants.
- **Collision**: MM9's `Solid` flag (`tables.py`), except the hanging lanterns (MoveToFloor 0), candles and debris
  (`NO_COLLISION`; all Solid 0 in this DAT anyway). So the lying skeletons (Solid 1) collide: radius 70, height 31
  (half the smaller footprint side of the sprawled skeleton). The Ruined Temple's `mm9_skeletonlaying` row has none. If a
  skeleton blocks a tunnel in game, the map agent can lower the row's radius (2421); not checked in game here. The
  black chest inside the coffin is Solid 0 in MM9: no collision on its row.
- `minelantern02plain`'s skin has alpha 225-255 (no cut-out; built opaque). The hook on top is part of the mesh.
- `sack01` stands upright (a full sack, 81 units); `sack02` lies flat.

## Not checked

- Nothing was looked at in game: no lantern, candle flame or skeleton in the BLV, no lighting of the props. The candle
  flames were checked in Tasar Academy's close-up renders of the same installed GLB (front and side: the cards stand on
  the wick) and in the GLB's material, not in this map.
- The skeletons' collision radius against the tunnel widths.
- The unused upright models (`sack01`, `stonedebris01ls`, `04ls`, `05ls`) and their rows are installed but not placed.
