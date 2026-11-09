# MM9 Anskram Keep props as 3D decorations (2026-10-30)

The props, wall torches and chests of MM9's Anskram Keep, converted from their LithTech ABC models into OpenYAMM 3D
decorations for the native BLV ([map project](../../projects/mm9r_anskramkeep/README.md)). The route is the isle
props project's ([`../mm9_isleofashes_claude/`](../mm9_isleofashes_claude/README.md)); its scripts are reused, not
copied: `blib.py` (import in the asset frame, clean, smooth, occlusion, export, renders), `textures.upscale`
(Real-ESRGAN x4), `finish.finish` (materials, LOD linking, checks, install), `review.py`, `sheet.py` and `glbio.py` run
with their path globals pointed at this project. The isle's prop table, transform and ODM bake are isle-specific, so
this project has its own table, build, tables and placements. None of the isle's 16 props is used here (the keep's
furniture is other ABC files). No paid services; the flames are the shared CC0 Unity Labs flipbook.

## Outputs

- 23 models installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`, cooked
  copies in `assets_dev/engine/models/`); all pass `check_winding.py` (0 inverted closed parts).
- The MM9 world's decoration contribution (`devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`): rows **2018-2042** in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt` (decoration_list_id 2017-2041), sprites 24818-24842 in
  `worlds/mm9/rendering/sprite_frame_data_world_decorations.yml`, bindings in `worlds/mm9/models/indoor_decorations.yml`
  (BLV maps read the indoor manifest; the outdoor `decorations.yml` is a dependency of baked outdoor maps).
- `../../projects/mm9r_anskramkeep/props.json`: the 248 placements (241 props, 7 chests) in the map's frame, each
  checked against the old map's baked BModel: median vertex distance 0.55, worst 0.78 units.
- `review/props_sheet.png`: contact sheet (LOD0 front, three-quarter, side, behind-above, below; LOD1/LOD2).
- `review/torch_flames_sheet.png`: in-game close-ups of the torch flames, front and both sides (below, Flames).

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `walltorch` | WALLTORCH | 101 | 152 | flame cards (flipbook) on the head, card billboard (Flames, below); no light of its own (below) |
| `bedmedium` | BEDMEDIUM | 16 + 12 | 92 | two decorations: x1.15, x1.2 |
| `crate` | CRATE | 14 + 6 | 12 | x1, x2 |
| `dresserns` | DRESSERNS (DRESSERPLAIN) | 20 | 20 | quarter turn baked in (below) |
| `chair` | CHAIR (CHAIRPLAIN) | 16 | 104 | cut-out skin (MASK) |
| `weaponscabinet01` / `04` | WEAPONSCABINET01 (01, 04) | 12 / 5 | 52 | one mesh, two skins |
| `barrel` / `barrel03` | BARREL / BARREL03 | 6 / 4 | 192 / 144 | x1.5; `barrel03` are MM9's drinkable `Barrel` objects |
| `chest` / `chest1` | CHEST1 (CHEST2 / CHEST1) | 6 / 1 | 158 | the treasure chests (x1, x0.8) |
| `scroll` | SCROLL-OPEN | 5 | 80 | |
| `tableround` | TABLEROUND | 4 | 120 | |
| `trashpile` | TRASHPILE | 4 | 400 / 200 / 97 | MM9's `BonePile` objects |
| `tablebench` | TABLE_BENCH_BROKEN (TABLE_BENCH) | 3 | 166 | |
| `weaponrack` | WEAPONRACK (WEAPONRACK_USED) | 3 | 1355 / 676 / 336 | deforming pieces: full export, bind pose baked |
| `bed` | BED | 2 | 70 | x1.2 |
| `chair02` | CHAIR02 | 2 | 256 | no LODs (a decimated LOD2 inverted a leg) |
| `bookcase02ew` / `ns` | BOOKCASE02EW / NS (BOOKCASE02) | 2 / 2 | 40 | x1.5; `ns` quarter turn |
| `desk01` / `desk01ns` | DESK01 / DESK01NS (DESK01) | 1 / 1 | 122 | `ns` quarter turn |
| `gatefire` | (none: MM9 `Fire` objects) | 8 | 6 | flame cards only: the Imp gates' fires; carries its light |

Decoration names are `mm9_<prop>` (a second scale `mm9_<prop>_x<scale %>`); each binding uses `yaw: facing` and the
height model height x MM9 Scale.

## Lights

Every `WallTorch` has its own MM9 `Light` 41-93 units away, which the map keeps as a BLV point light (768, warm
231/157/90). The torch rows therefore carry no light (LightRadius 0): the BLV light is the torch's light and nothing
doubles; `props.json` names each torch's light. The gate fire row carries MM9's `Fire` light (205, 255/190/130).

## Flames

The flame cards are a billboard about their own centre: `openyamm_billboard: "card"`, set once for every MM9 flame in
the isle's `finish.py`. Plain `true` is the far-impostor mode: the shader keeps a card's offset across the model and
its height but drops its depth, so the card stands on the model's vertical axis. A torch that leans out of the wall
has its head off that axis (`walltorch` 0.25 m, `sconcetorch` and `bluetorch` 0.17, the braziers 0.085), so until
2026-10-30 the flame hung over the bracket, on the wall side of the head. It only looked right from straight in
front, because the lost depth runs along that view. Only flames on the model's axis may use plain `true`.

`build.py` was right: the cards' head (0.0, 0.858, 0.252 in the GLB) is under 1 cm from the ABC's `FireNode`
(0.003, 0.851, 0.245). The fix needs no rebuild of a torch: `finish.py <prop> --install` re-applies the material
extras. `bluesconce` is the exception, see the [Chasm README](../mm9_chasmofthedead_claude/README.md). Picking turns a
card about the same pivot (`facingCardCorner`), so a flame picks where it is drawn. Flame cards are not in the bake;
`tools/lighting/stale_bakes.py` lists no new map.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_anskramkeep_claude
python3 scripts/props_table.py                       # raw objects -> work/raw_objects_compact.json, binding origins
python3 scripts/convert_all.py                       # ABC -> work/raw/<prop>/ (rigid; full for deforming models)
python3 scripts/textures.py                          # skins x4 -> textures/ (Real-ESRGAN, via the isle's textures.py)
blender --background --python scripts/build.py       # work/<prop>_export.glb, work/<prop>_meta.json
python3 scripts/finish.py --install                  # checks, then tools/install_model.py --world mm9
blender --background --python scripts/review.py && scripts/contact_sheet.sh
python3 scripts/tables.py                            # dry run; --apply appends the world rows, sprites, bindings
python3 scripts/placements.py                        # ../../projects/mm9r_anskramkeep/props.json, bake fit
python3 ../../projects/mm9r_common/review_root.py    # link the new models and rows into the review root
```

`tables.py --apply` re-reads the world files right before writing, refuses a name the engine already has, only
appends, and writes each file as a new file renamed over the old one (the review mirror hard-links them). Rows that
exist keep their numbers.

## Frames and the placement check

As the isle's: the raw GLB holds the ABC model space x 2.56 in LithTech axes; the old transcoder baked a prop at
`Rz(-yaw) * Scale * swap(model + binding origin) * 2.56 + swap(Pos) * 2.56` (+ a floor drop for MoveToFloor props);
the asset is the raw import mirrored in X. `placements.py` places each finished LOD0 as the engine does and compares
it with the old map's BModel of the same object (`MM9_static_prop_<object>_<name>`, `MM9_chest_<object>_<name>`). The
keep's frame is the old map's (no offset), so positions are the bake's. The three `*ns` models (bookcase, desk,
dresser) import a quarter turn away from the transcoder's bake (their raw extents equal their `*ew` twins'); the
build turns them back (`build.py` `turn: 90`), after which they fit at 0.5-0.9 units.

## Deviations

- Textures are the native 128 px skins x4 (512); no normal or roughness maps (roughness 0.85).
- The weapon rack is 1 355 triangles (its weapons; 3 placements, LODs 676 / 336).
- `SpikePit` (the PropDamagers): the three in the trap pits are the model `spikepit` (the map project places them on
  the pit floors and wires their damage); the three under the moving crushers are not placed (decorations are static).
- Collision: MM9 Solid props get radius = half the smaller footprint side and the model height; the torches and
  scrolls none (wall-hung, small).


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `weaponrack` 1355 / 676 / 336  -> 1275 / 635 / 317 triangles (LOD0 / LOD1 / LOD2).
`scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES`, so every project that runs this build (Verhoffin Ruins,
Temple of Honk, Training Hall, Tasar Academy and the others) imports without the ball. The build also takes a `frame_x`
spec (metres added to the base centre's x; Temple of Honk's books use it). LOD0 lost exactly the ball; LOD1/LOD2 are
decimations and were remade from the clean LOD0. Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed
parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and scripts are in
`work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
