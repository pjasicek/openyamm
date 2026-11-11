# MM9 Beethoven props as 3D decorations (2026-10-30)

The props, chests, torches and quest objects of MM9's Beethoven (the Sturmford sewers), converted from their LithTech ABC
models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_beethoven/README.md)). The
route is the Temple of Honk and Chasm of the Dead props projects': these scripts wrap the Anskram Keep's (`anskram.py`)
and the isle's helpers. No paid services, no Codex images: every model is MM9's own mesh with its skin x4 (made with Real-ESRGAN before the user retired it for props; the Codex x4 pass replaces them).

## Outputs

- **16 models** installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all
  passing `check_winding.py` (0 inverted closed parts); the coffins' lid pins and a bone of the bone pile had inward
  normals in the ABC and are reversed in `scripts/build.py` (`fix_closed_parts`).
- **Reused** (same ABC and skin): Anskram's `mm9_walltorch`, `mm9_trashpile`, `mm9_chest1` at the Lich Lab's row
  `mm9_chest1_x100`; the isle's well at a new row `mm9_well_x100`.
- **Rows 2121-2136** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 24921-24936, bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `locks/mm9_decorations.lock`.
- `../../projects/mm9r_beethoven/props.json`: 103 placements, each checked against the old map's baked BModel (median
  vertex distance under a unit; worst `sconcetorch` 5.9, its flame cards).
- **`mm9_bottlefloat.glb`** (`scripts/bottle.py`): the floating wine bottle of BottleFollow.scr as one looping scripted
  model, in `assets_source/engine/models/`.

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `urngargoyle` | URNGARGOYLE | 13 | 176 | one is a DestructableProp (`Urn0`), drawn the same |
| `jar01`-`jar06` | JAR01-06 (PANTRY-ITEMS, 02) | 33 | 42-88 | shelf jars; no collision (MM9's solid ones stand on shelves) |
| `jar01side`, `jar04side` | JAR01, JAR04 | 2 | 42 | lying on their side: pitch 90 baked in |
| `coffinfancy` | COFFINFANCY (COFFINSTONE) | 8 | 616 / 307 / 153 | the closed coffins the mummies wake in, x1.2 |
| `coffinraised` | COFFINRAISED (COFFINSTONE) | 6 | 634 / 317 / 157 | the coffin chests, x1.2 |
| `sconcetorch` | TORCH2 (SCONCE1) | 7 | 178 | CandleProp; flame cards, no light (each has its own MM9 Light) |
| `hangingbowl1` | HANGINGBRAZIERBOWL | 1 | 175 | x1.5, cut-out chains, flame cards on its rim |
| `bonepile` | BONEPILE | 3 | 559 / 278 / 135 | |
| `manuscript` | LUDWIG-MANUSCRIPT | 1 | 82 | pitch 90 baked in; Ludwig's quest item |
| `winebottle` | WINEBOTTLE01 | (4) | 64 | only as the mesh of `mm9_bottlefloat` |

Skins in `textures/`; `flame02_basecolor.png` is the shared CC0 flipbook.

## Route

```sh
cd level_generation/props/mm9_beethoven_claude
python3 scripts/props_table.py                       # work/raw_objects_compact.json, binding origins
python3 scripts/convert_all.py                       # ABC -> work/raw/<prop>/
python3 scripts/textures.py                          # skins x4
blender --background --python scripts/build.py -- <props>
python3 scripts/finish.py --install
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py                        # ../../projects/mm9r_beethoven/props.json
python3 scripts/bottle.py --install                  # the floating bottle
python3 ../../projects/mm9r_common/review_root.py    # link the new models and rows into the review root
```

## The coffin lids

`scripts/coffin_parts.py --install` splits the finished `coffinfancy` into the coffin (`mm9_deco_coffinfancy.glb`:
without its lid, and without the ABC's Skeleton piece, which every placement hides with `HidePiece0 Skeleton`) and its
lid (`mm9_deco_coffinfancy_lid.glb`, the binding's `part`): one node at the lid's bone (the ABC's Bone01) with the
ABC's `Open` and `Close` clips as `open` and `close` (1 s each), carried from the raw import into asset space. The
binding's height is the coffin's own, 97.1 (the whole coffin's 124.3 scale). Beethoven's map Lua opens it with
`evt.PlayDecorationClip(cog, "open")` (CoffinRaise.scr). Run it again after rebuilding `coffinfancy`; `tables.py`
keeps the existing binding.

## The bottle

`evt.SpawnWorldModel` takes a GLB and a clip name and plays the clip in a loop, and models carry node animation, so one
GLB holds the whole journey in native units: clips `sw`, `nw`, `ne`, `se`, each six seconds' bobbing at its start, the
drift along the start's markers at MM9's 40 LT/s, a jump to `MarkerLower0`, the drift to Ludwig's manuscript, a jump
back (170-390 s a loop). The node translation is the native point as (-x, z, y) (`gltfModelPlacement`), spawned at
the origin at scale 1. Keys every 0.25 s, strictly increasing (the loader refuses equal times). The bottle rides 8 LT
above its markers, which lie on MM9's translucent water; the water here is opaque.

## Notes

- `Treasurechest<k>` and `TreasureChest<k>` differ only in case; the compiler's node names ignore case, so the map
  project anchors the first five as `Chest<k>`.
- Skins are the native skins x4; no normal or roughness maps (roughness 0.85).
