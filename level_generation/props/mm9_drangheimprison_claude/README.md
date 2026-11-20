# MM9 Drangheim Prison props as 3D decorations (2026-10-30)

The props, braziers, barrels, bone piles and chests of MM9's Drangheim Prison, converted from their LithTech ABC models
into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_drangheimprison/README.md)). The route
is the Lich Lab props project's ([`../mm9_lichlab_claude/`](../mm9_lichlab_claude/README.md)): its scripts, pointed at this
project. No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4.

## Outputs

- **36 models** installed with `tools/install_model.py --world mm9` (`mm9_deco_*.glb`), all through `check_winding.py`.
- **Reused** (same ABC and skin): `barrel`, `barrel03`, `bed`, `blackchest`, `chair`, `chairdesk01`, `chest1`, `cot`,
  `desk01ns`, `hangingbowl2`, `table01`, `tableround`, `trashpile`, `walltorch`, `weaponrack`.
- Rows **2174-2214** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`. The MM9 sprite
  block 24801-24999 filled up during this project: the rows continue at sprite 26001
  (`devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`, `SPRITE_RANGE2` in `scripts/tables.py`).
- `../../projects/mm9r_drangheimprison/props.json`: 261 placements, each checked against the old map's baked BModel:
  median 0.5 units, worst 0.81 except `Prop18` (the rusty axe, 9.5: below); 64 objects the old map did not bake stand on the floor under them.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_drangheimprison_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply
python3 scripts/placements.py
python3 ../../projects/mm9r_common/review_root.py
```

## Notes

- **Tipped placements** have the pitch or roll baked in, as decorations turn about z only: `barrellying` (Barrel15/16),
  `bedmedium2r90`, `bedmedium2r270` (Cot4/5).
- **`bonepile`** has no LODs (its LOD chain failed the winding check). Beethoven's project uses the same row and GLB.
- **`Prop18`** (`axerusty`): the ABC lies flat, MM9 stands it against the wall: quarter tilt baked in (best orientation 9.5 units from the bake; every other prop is under 1).
- `cabinet04ns`, `cabinet05ns`, `weaponrackns` carry the quarter turn of MM9's `ns` models (`scripts/specs.json`).
- Skins: Real-ESRGAN for the first 33 (then the shared `upscale`), Lanczos x4 for the three tipped variants, the user's
  rule since 2026-10-30; the Codex x4 pass replaces both. No normal or roughness maps. These are not Meshy-textured.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `weaponrackns` 1355 / 676 / 336  -> 1275 / 635 / 317 triangles (LOD0 / LOD1 / LOD2).
`scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to its own per-face skin
import; LOD0 lost exactly the ball (inside the rack), LOD1/LOD2 were remade. Rebuilt, checked (`finish.py`,
check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and
scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
