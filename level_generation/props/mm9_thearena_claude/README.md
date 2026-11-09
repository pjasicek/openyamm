# MM9 The Arena props as 3D decorations (2026-10-31)

The props and wall torches of MM9's arena in Thjorgard City, converted from their LithTech ABC models into OpenYAMM 3D
decorations for the native BLV ([map project](../../projects/mm9r_thearena/README.md)). The route is the Ruined Temple
props project's (the Anskram Keep scripts run on this project's table through `scripts/anskram.py`). No paid services, no
Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos).

## Outputs

- **2 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  through `check_winding.py` in `finish.py`:
  - `torchrust` (TORCH2.abc with `refinerysolidrusta`, 178 triangles): the wall torch, orange flame cards on the head
    (the Anskram flame flipbook; the Ruined Temple's `torchmetal` is the same mesh with blue flames), hung, no collision;
  - `tapestry_banner6` (TAPESTRY-OLD01.abc with `Banner6`, 48 triangles): the banners of Sven's box, hung, opaque (the
    skin has no alpha), at MM9's scales 1.0 and 1.5 (two rows).
- **2 reused** (same ABC and skin): the Lich Lab's `throne`, the Anskram Keep's `chair02`.
- Rows **2438-2440** (`mm9_tapestry_banner6`, `mm9_tapestry_banner6_x150`, `mm9_torchrust`) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26239-26241, bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`. No row carries a
  light: every torch has its MM9 `Light` beside it (40 units off), kept as a BLV light.
- `../../projects/mm9r_thearena/props.json`: **31 placements**: the 11 spectators (below) and 20 (14 torches, 4 banners,
  the throne, the chair), each
  checked against the old map's baked BModel: banners 0.34-0.41, chair 0.45, throne 0.54 units median; the torches
  5.76-5.87 (the torch2 model's known offset, as in the Ruined Temple, Beethoven and the Chasm).
- **The 11 `RUDEProp` spectators** (added 2026-11-05, user decision): static decorations of MM9's own seated peasant
  meshes in their PropAnim.scr pose, Sturmford City's route for its seated townsfolk (below).

## Spectators (2026-11-05)

`scripts/spectators.py` is a props table in the Sturmford City scripts' shape; `scripts/sturmford.py` runs Sturmford's
convert, textures, finish and placement helpers on it (as `anskram.py` does for the Anskram scripts), and
`scripts/build_spectators.py` runs Sturmford's Blender build. PeasantMS2.abc / PeasantMS1.abc carry only T-pose
animations: `listen` comes from PeasantSeated.abc (same 43 nodes in the same order), the woman's `conv1` from
PeasantFSeated.abc (the women's seated library; same 54 nodes as PeasantFS2.abc), added by
`scripts/convert_library_pose.py` (Sturmford's), posed at the first key. The shadow n-gon (`ngon_s`, PeasantFS2's
`NGon01`) is stripped. Static: no idle animation.

| Model | Body, skin, pose | Triangles | Spectators |
|---|---|---|---|
| `peasantms2alisten` | PeasantMS2, PeasantM2a, listen | 678 / 339 / 168 | Spectator4 |
| `peasantms2blisten` | PeasantMS2, PeasantM2b, listen | 678 / 339 / 168 | Spectator0, 2, 10 |
| `peasantms2clisten` | PeasantMS2, PeasantM2c, listen | 678 / 339 / 168 | Spectator1, 7 |
| `peasantms1alisten` | PeasantMS1, PeasantM1a, listen | 632 / 316 / 158 | Spectator3 |
| `peasantms1blisten` | PeasantMS1, PeasantM1b, listen | 632 / 316 / 158 | Spectator6 |
| `peasantfs2bconv1` | PeasantFS2, PeasantF2b, conv1 | 495 / 241 / 120 | Spectator5, 9 |
| `peasantms2dlisten` (**reused**, Sturmford City's Halfdan) | PeasantMS2, PeasantM2d, listen | | Spectator8 |

- **6 models built**, installed with `tools/install_model.py --world mm9`, each through `check_winding.py` (0 inverted
  closed parts, rerun on the installed sources). PeasantMS1's native ABC LODs collapse its feet and head to spikes in
  the seated pose, so its LOD1/LOD2 are collapse decimations (`build_spectators.DECIMATED_LODS`).
- **Skins**: the Codex x4 redraws of `level_generation/props/mm9_skins_x4/` (`skins.py`): new redraws
  `peasantms1alisten` (PeasantM1a), `peasantms1blisten` (PeasantM1b), `peasantfs2bconv1` (PeasantF2b), with notes in
  its `work/notes.json`; PeasantM2a/b/c reuse the accepted redraws of the same skins (`erccsitting`,
  `peasantms2bconv`, `peasantm2innkeeper`). Installed with `skins.cmd_install` limited to these six models
  (`work/skins_install_spectators.log`); no other project's model was touched.
- Rows **2798-2803** (`mm9_peasantfs2bconv1`, `mm9_peasantms1alisten`, `mm9_peasantms1blisten`, `mm9_peasantms2alisten`,
  `mm9_peasantms2blisten`, `mm9_peasantms2clisten`; hint townsman / townswoman, collision radius 32-39, height
  146-153), sprites 26599-26604, bindings in `worlds/mm9/models/indoor_decorations.yml` (heights 146.2-153.4), under the
  decorations lock (`work/tables_apply_spectators.log`). Spectator8 uses the existing `mm9_peasantms2dlisten` (row 2489).
- **Placements**: the old import baked none of them, so each is checked against MM9's own pose instead (Sturmford's
  posed branch): the ABC skinned at its library animation's first key at the DAT position, base on the floor under it
  (all MoveToFloor 1; the posed feet are 10-12 units under that floor at the DAT height): `fit_pose_units` 0.00-0.23.
  `kind: prop` (PropAnim.scr only loops the pose; no dialogue or click event); `source_name` is the DAT name
  (Spectator0-10), with `script`, `script_params`, `pose`, `floor_z` and `rude_npc_id` (428 for all) kept for
  reference. Not looked at in game: whether they read as seated on the stands' steps (the tiers are 62-82 units high
  with a 20-unit lip; MM9 places them the same way).
- Contact sheet: `review/spectators_sheet.png` (`scripts/spectators_sheet.sh`; the installed models, LOD0 front,
  three-quarter, side, behind-above, below, then LOD1/LOD2 three-quarter).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_thearena_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py            # needs the map's work/lights.json: build the map once first
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py -- torchrust tapestry_banner6; bash scripts/contact_sheet.sh
# the spectators (before tables.py and placements.py)
python3 scripts/spectators.py convert && python3 scripts/spectators.py textures
blender --background --factory-startup --python scripts/build_spectators.py
python3 scripts/spectators.py finish --install      # then the mm9_skins_x4 redraws (above)
blender --background --factory-startup --python scripts/review.py -- <spectator props>; bash scripts/spectators_sheet.sh
```

Contact sheet: `review/props_sheet.png` (LOD0 front, three-quarter, side, behind-above, below).
