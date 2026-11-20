# MM9 Training Hall props as 3D decorations (2026-10-30)

The props, wall torches, braziers, hanging fire bowls, barrels and chests of MM9's Training Hall, converted from their
LithTech ABC models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_traininghall/README.md)).
The route is the Klusos House / Ruined Temple props projects' (the Anskram Keep scripts run on this project's table
through `scripts/anskram.py`; `build.py` runs the Anskram build with this project's specs). No paid services, no Meshy,
no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the user's rule since 2026-10-30).

## Outputs

- **6 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  all through `check_winding.py` in `finish.py`: `lumberdebris02` (48 triangles), `lumberdebris03` (48),
  `lumberdebris05` (72), `trainingmount` (the joust's wooden training horse, 280), `spindummy` (the spinning dummy with
  its mace and lance, 331), `strawdummy` (the straw dummy on its gallows, 462 / 271 / 114).
- **7 reused** (same ABC and skin; their GLBs and rows stay with their owners): Anskram's `walltorch` (flame cards on the
  head, `card` billboard), `barrel03` (row `mm9_barrel03_x100`), `chest1` (`mm9_chest1_x100`); the Temple of Honk's
  `brazier` (flame cards in its bowl); Beethoven's `hangingbowl1` (flame cards on its rim; Beethoven places it at x1.5, the
  hall at x1: a new row); the Lich Lab's `blackchest`; Drangheim Prison's `lumberstone02`.
- Rows **2295-2301** (7: the 6 models and `mm9_hangingbowl1_x100`) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`,
  sprites 26096-26102, bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under
  `mm9r_common/locks/mm9_decorations.lock`. No row carries a light: every torch, brazier and bowl has its MM9 `Light`
  beside it, kept as a BLV light (or bake-only where a floor point was already under four).
- `../../projects/mm9r_traininghall/props.json`: **45 placements** (16 props, 11 wall torches, 6 hanging bowls, 5
  braziers, 2 barrels, 5 chests), each checked against the old map's baked BModel: median of medians **0.56** units, worst
  `Blackbox` 0.73.
- The 8 MM9 `Fire` objects (no model in MM9) are placed by the map project as the Anskram gate fire's flame cards at a
  third (`mm9_gatefire_x33`, unlit, an existing row).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_traininghall_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py            # needs the map's work/lights.json: build the map once first
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py -- <props>; bash scripts/contact_sheet.sh
```

## Notes

- **LODs.** `trainingmount` and `spindummy` have no LODs (`lods: False` in `build.py`): their last native ABC LOD is a
  few loose shards (contact sheet `review/props_sheet.png`, first build). `strawdummy` keeps its three.
- **Collision**: the dummies and the training mounts get a cylinder (radius half the smaller footprint side, model
  height); wall torches, hanging bowls and the low lumber heaps none.
- Contact sheet: `review/props_sheet.png` (every built prop: LOD0 front, three-quarter, side, behind-above, below,
  then the LODs). Flames in game: the map project's `review/flames01/`.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `strawdummy` 462 / 271 / 113  -> 382 / 191 / 94 triangles (LOD0 / LOD1 / LOD2). Fixed in
the Anskram build this project runs (`blib.SKIP_BONE_SHAPES`); LOD0 and LOD1 lost exactly the ball, LOD2 (a decimation)
was remade. Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed parts) and reinstalled with
`install_model.py --world mm9`; the replaced GLBs and scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends
on decoration models (stale_bakes.py lists none).
