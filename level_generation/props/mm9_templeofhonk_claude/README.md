# MM9 Temple of Honk props as 3D decorations (2026-10-30)

The props, braziers, wall torches, chests, the accountant's key and the Golden Honk of MM9's Temple of Honk, converted
from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_templeofhonk/)).
The route is the Anskram Keep props project's ([`../mm9_anskramkeep_claude/`](../mm9_anskramkeep_claude/README.md)),
itself the isle's; their scripts are reused, not copied: `scripts/anskram.py` puts this project's `props_table` in
`sys.modules['props_table']` and loads an Anskram script by path (`convert_all.convert`, `textures`, the `tables` and
`placements` helpers); `build.py` runs the Anskram `build.py` source with its paths and `PROPS` pointed here;
`finish.py` is the isle's `finish` with this project's `HERE` and cut-outs; `review.py` and `contact_sheet.sh` run the
Anskram ones from here. No paid services, no Meshy, no Codex; the flames are the shared CC0 Unity Labs flipbook.

## Outputs

- 32 models installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`, cooked
  copies in `assets_dev/engine/models/`); all pass `check_winding.py` (0 inverted closed parts).
- The MM9 world's decoration contribution: rows **2043-2074** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`
  (decoration_list_id 2042-2073), sprites 24843-24874 in `worlds/mm9/rendering/sprite_frame_data_world_decorations.yml`,
  bindings in `worlds/mm9/models/indoor_decorations.yml` (block "MM9 Temple of Honk props").
- `../../projects/mm9r_templeofhonk/props.json`: the 154 placements (88 props, 49 braziers, 11 torches, 5 chests, the
  Golden Honk; the 6 `Fish` are not placed) in the map's frame, each checked against the old map's baked BModel:
  median vertex distance 0.50, worst 0.92 units (the 1.3-unit key against an integer-vertex bake).
- `review/props_sheet.png`: contact sheet (LOD0 front, three-quarter, side, behind-above, below; LOD1/LOD2).

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `brazier` | BRAZIER | 46 | 220 | flame cards in the bowl (the torch's cards); no light (below) |
| `hangingbowl` / `hangingbowl2` | HANGINGBRAZIERBOWL / 2 (HANGINGBRAZIERBOWL3) | 2 / 1 | 175 / 227 | x0.75; flames seated on the rim; cut-out chains |
| `benchstone02` / `benchstone01` | BENCH_STONE02 / 01 (BENCH_STONE) | 14 / 1 | 156 / 192 | |
| `bench04` | BENCH04 | 6 | 52 | |
| `bookcase01ew` / `ns` | BOOKCASE01EW / NS (BOOKCASE01) | 6 / 6 | 116 | `ns` quarter turn baked in |
| `tapestry_*` (12) | TAPESTRY-OLD01 (TAPESTRY_FLOWER, _OLIVE, _PURPLE, _REDBLACK; BAYEUX_START, _LINK, _2, BAYUEX_END; BAYEUX2_START, _LINK, _2, _END) | 22 | 48 | x2; one mesh, twelve level-texture skins (opaque) |
| `chairdesk01` / `chairdesk03` | CHAIR_FORDESK01 / 03 | 3 / 2 | 214 / 110 | |
| `cabinet04` / `cabinet01ns` | CABINET04 / CABINET01NS (CABINET01) | 2 / 1 | 20 / 58 | `ns` quarter turn |
| `desk03` | DESK03 | 2 | 146 | |
| `table02` | TABLE02 (TABLE01) | 2 | 132 | |
| `bookflat` / `booktilt15` | BOOK | 1 / 1 | 252 | bind pose; `booktilt15` has Book1's 14.6 degree pitch baked in |
| `harp` | HARP | 1 | 225 | cut-out strings |
| `key2` | KEY2 | 1 | 276 / 137 / 68 | `key0`, the accountant's key (kind quest) |
| `chest3` | CHEST3 | 1 | 122 | the `CollectionChest` |
| `goldenhonk` | PICKUPITEMS/QUEST/GOLDENHONK | 1 | 248 | the Golden Honk on the altar (kind quest) |

Decoration names are `mm9_<prop>`; each binding uses `yaw: facing` and the height model height x MM9 Scale.

Reused (same ABC model, skin and placement scale; rows, bindings and GLBs unchanged, checked by `tables.py`):
Anskram's `mm9_barrel` (5, x1.5), `mm9_chair` (6), `mm9_crate` (2), `mm9_crate_x200` (1), `mm9_desk01ns` (2),
`mm9_tableround` (1), `mm9_walltorch` (11) and `mm9_chest` (chest1 + chest2, 4). The isle's `mm9_book` is not reused:
its lectern tilt (pitch 2.506, roll pi) is baked in. `desk03`, `chairdesk03`, `table02` and `bookflat` use the same
names as the Lich Lab props project's builds of the same model, skin and scale (identical meta: triangles, height,
extent, origin); whichever project appends first owns the row and the other reuses it.

## Lights and fires

Every `Brazier` and `WallTorch` has its own MM9 `Light` 10-104 units away (60 distinct lights for 60 fires), which the
map keeps as a BLV point light; their rows carry no light (LightRadius 0) and `props.json` names each one's light.
MM9 gives all of them the same fire (Fire 1, FireScale 1, colours 220/180/0 - 255/215/0), so the floor brazier gets
the Anskram torch's two flame cards in its small bowl; the hanging bowls, placed at 0.75, get three cards 1/0.75 larger
seated on their rim (their top is the hook). MM9's FireOffset (0, 6, 0) would put the floor brazier's fire on its stem,
under the bowl; the flame sits in the bowl instead.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_templeofhonk_claude
python3 scripts/props_table.py                       # raw objects -> work/raw_objects_compact.json, binding origins
python3 scripts/convert_all.py                       # ABC -> work/raw/<prop>/ (Anskram's convert, isle venv)
python3 scripts/textures.py                          # skins x4 -> textures/ (Real-ESRGAN); flame02 from Anskram
blender --background --python scripts/build.py       # work/<prop>_export.glb, work/<prop>_meta.json
python3 scripts/finish.py --install                  # checks, then tools/install_model.py --world mm9
blender --background --python scripts/review.py && scripts/contact_sheet.sh
python3 scripts/tables.py                            # dry run; apply under the shared lock:
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py [--verbose]            # ../../projects/mm9r_templeofhonk/props.json, bake fit
```

## Frames and the placement check

As Anskram's: the asset is the raw import mirrored in X; `placements.py` places each finished LOD0 as the engine does
and compares it with the old map's BModel of the same object (`MM9_static_prop_<object>_<name>`, `MM9_chest_...`,
`MM9_pickup_453_Honk`; BModel names stop at 32 characters, so they are matched by prefix). The frame is the old map's
(no offset). `bookcase01ns` and `cabinet01ns` import a quarter turn from the transcoder's bake and are turned back
(fit 0.54, 0.57). The tilted book is compared with its pitch applied. The Golden Honk (MoveToFloor 1) stands on the
altar top under its DAT position (floor 573.0; the old bake's base 573.4), fit 0.74.

## Deviations

- Textures are the native 128 px skins x4 (512); no normal or roughness maps (roughness 0.85).
- The tapestries and hanging bowls get their vertex occlusion without blib's floor plane (it darkened the lower half
  of every tapestry by up to 45 %).
- The 22 tapestries are twelve GLBs of one 48-triangle mesh (one per skin), as Anskram's two weapons cabinets.
- Collision: MM9 Solid props get radius = half the smaller footprint side and the model height (the brazier's without
  its flame: 149); torches, tapestries, hanging bowls, books and the key none; chairs, `chest3` and the Golden Honk are
  not Solid in MM9.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `bookflat` 252        -> 172 triangles; `booktilt15` 252        -> 172 triangles (LOD0 /
LOD1 / LOD2). Fixed in the Anskram build this project runs (`blib.SKIP_BONE_SHAPES`). The ball sat just past the spine
and had moved the books' base centre 1.585 units along x: `build.py` keeps that frame (`PROPS[..]['frame_x']`,
`blib.BOOK_BALL_FRAME_X_M`) so the book placements of every map (Lich Lab, Lindisfarne Monastery and Tasar Academy reuse
`bookflat`) stay valid; geometry otherwise identical. Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed
parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and scripts are in
`work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
