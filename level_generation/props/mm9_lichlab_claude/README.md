# MM9 Lich Lab props as 3D decorations (2026-10-30)

The props, chests and pickups of MM9's Lich Lab, converted from their LithTech ABC models into OpenYAMM 3D decorations
for the native BLV ([map project](../../projects/mm9r_lichlab/README.md)). The route is the Anskram Keep props
project's ([`../mm9_anskramkeep_claude/`](../mm9_anskramkeep_claude/README.md)), itself the isle's: the isle's
`blib.py`, `textures.upscale`, `finish.finish`, `review.py`, `sheet.py` and `glbio.py` run with their path globals
pointed at this project; the prop table, build, tables and placements are this project's. No paid services, no Codex
images: every model is MM9's own mesh with its skin x4 (Real-ESRGAN).

## Outputs

- **37 models** installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`); all pass `check_winding.py` (0 inverted closed parts).
- **Reused, not rebuilt** (same ABC and skin): Anskram's `chair`, `crate`, `barrel`, `chest1`, `scroll`; the isle's
  `cookpot` (its flames and light 160 are MM9's `Fire0` under the kitchen pot); the Temple of Honk's `bookflat`,
  `chairdesk03`, `desk03`, `table02`.
- The MM9 world's decoration contribution (`devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`): rows **2075-2119** in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 24875-24919, bindings in
  `worlds/mm9/models/indoor_decorations.yml` (including the indoor binding of the isle's `mm9_cookpot`, which only had
  an outdoor one, and `mm9_gatefire_unlit`: Anskram's gate fire flames without its light, for the cage fires).
  Appended under `level_generation/projects/mm9r_common/locks/mm9_decorations.lock`.
- `../../projects/mm9r_lichlab/props.json`: the 181 placements (167 props, 8 chests, 3 barrels, 3 bone piles), each
  checked against the old map's baked BModel: median vertex distance 0.55 units, worst 1.16 (the tilted books);
  BonePile1 16.5 (another model, below). The 13 objects the old import did not bake (the herb bags and jars it took for
  pickups, the flaying benches whose ABC has NaN UVs) stand on the floor or shelf under them (MoveToFloor).
- `review/props_sheet.png`: contact sheet (LOD0 front, three-quarter, side, behind-above, below; LOD1/LOD2).

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `pew3ns` | PEW3NS (PEW3) | 12 | 118 | quarter turn baked in |
| `throne` | THRONE | 11 | 220 | |
| `skeletonstatue` | SKELETONSTATUE (+SKELSTATUEBASE) | 4 + 2 + 2 | 1155 / 577 / 287 | two skins, two materials; x1, x1.5, x3 |
| `bagherbs` | BAGHERBS2 (BAGHERBS1 + HERBS) | 7 | 367 / 183 / 90 | Elixir Ingredients pickups; herbs cut-out |
| `jar` / `jarbroken` | JAR_EMPTY / JAR_BROKEN | 4 / 1 | 214 / 146 | glass (BLEND); the jars are pickups |
| `torturecage01`, `torturerack01`, `torturewheel01/02`, `torturecrusher01/02`, `pillory`, `flayingbench`, `headsmansblock`, `skeletoncage` | the torture room's | 1-4 each | 72-818 | cut-out skins; `flayingbench` converted with NaN UVs zeroed (`scripts/convert_sanitized.py`), no LODs (a decimated LOD2 broke), `torturecrusher02` no LODs, `headsmansblock` quarter turn |
| `table01` / `table01ns` / `table02` (reused) | TABLE01 / TABLE01NS (TABLE01) | 2 / 3 | 204 | `ns` quarter turn |
| `shelfitem01/02/03/05` | SHELFITEM* | 2 / 3 / 1 / 5 | 133-792 | bottles (05 glass BLEND), x1, x1.5, x2 |
| `chair03`, `bookstack01`, `podium01`, `cauldron01`, `beaker01`, `burner`, `logs`, `blackchest`, `switch02`, `skeletonsitting`, `scroll2/3`, `scrolldouble`, `lichengine` | | 1-3 each | 35-451 | `burner`: deforming piece, bind pose baked; `logs`: LOGSBURNING without the isle's flames (no Fire burns on it here); `lichengine` x4 (1135 units): MM9's `static_model` pose |
| `booktilt` | BOOK | 3 | 252 | the shooting range's books: placement pitch 27 degrees baked |

Decoration names are `mm9_<prop>` (a second scale `mm9_<prop>_x<scale %>`); bindings use `yaw: facing` and the
height model height x MM9 Scale. Collision: MM9 Solid props get radius = half the smaller footprint side and the model
height; table-top things (jars, bags, bottles, books, scrolls, the switch) none.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_lichlab_claude
python3 scripts/props_table.py                       # raw objects -> work/raw_objects_compact.json, binding origins
python3 scripts/convert_all.py                       # ABC -> work/raw/<prop>/ (rigid; full for deforming models)
python3 scripts/textures.py                          # skins x4 -> textures/<id>_basecolor.png
blender --background --python scripts/build.py       # work/<prop>_export.glb, work/<prop>_meta.json (specs.json: turns, LODs)
python3 scripts/finish.py --install                  # checks, then tools/install_model.py --world mm9
blender --background --python scripts/review.py -- <props> && scripts/contact_sheet.sh
python3 scripts/tables.py                            # dry run; --apply appends rows, sprites, bindings (takes the lock)
python3 scripts/placements.py                        # ../../projects/mm9r_lichlab/props.json, bake fit
python3 ../../projects/mm9r_common/review_root.py    # link the new models and rows into the review root
```

`tables.py` reuses a world row whose binding has the same model and height (within 0.6), names new variants
`mm9_<prop>` or `mm9_<prop>_x<scale %>`, takes the decorations lock and re-reads every file inside it, refuses engine
names, only appends, and writes by temporary file + `os.replace`.

## Deviations and notes

- BonePile1 is MM9's lever model (`Switch02.ABC`) with a skeleton skin path that does not exist: a data slip among
  three bone piles; it becomes a sitting skeleton like the other two.
- The Lich engine is static in MM9's `static_model` pose: its `StartUp`/`SpinCycle` ring spin (LichEngineProp.scr)
  needs node animation, which decorations do not have; the map shows a lightning strike instead (map README).
- Skins are the native 128-256 px skins x4; no normal or roughness maps (roughness 0.85).
- **Name clash (2026-10-30).** The Temple of Honk props project built `bookflat`, `chairdesk03`, `desk03` and
  `table02` from the same ABCs minutes before this project installed its own copies over theirs; their GLBs were
  reinstalled from their project (identical meshes) and `props_table.REUSED` now takes them from there. Before naming
  a prop, check `assets_source/worlds/mm9/models/mm9_deco_<name>.glb`.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `booktilt` 252        -> 172 triangles; `burner` 151        -> 71 triangles (LOD0 / LOD1
/ LOD2). `scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to its own per-face
skin import. `booktilt` keeps its first install's frame (`frame_x`, `blib.BOOK_BALL_FRAME_X_M`: the ball past the spine
had moved its base centre 1.585 units), so its placements stay valid. `bookflat` is Temple of Honk's (fixed there).
Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py
--engine`; the replaced GLBs and scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration
models (stale_bakes.py lists none).
