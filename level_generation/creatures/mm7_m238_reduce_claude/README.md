# MM7 Genie (`m238`, Djinni / Genie / Efreet) triangle reduction (2026-10-20)

User request after batch G: "reduce tris count for all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: nothing needed rebuilding, so the textures,
region mask, tier ramps, clips, the lamp mesh and the collapsed-mesh node keys stay as exported. No Meshy credits.
Scripts copied from `mm7_m162_reduce_claude/` (ladder, UV weights, LODs, LOD check, gates, viewer), adapted for the
genie (`make_groups.py`, `close_m238.py`, `arm_contacts.py`, `strip_node_keys.py`, `viewer_tiers.py`). Batch G rules
apply: nothing installed, nothing in `assets_dev/` or `assets_source/`, `mm7_m238_claude/` untouched. Every Blender and
Python step runs memory-capped (`scripts/cap.sh`, `scripts/b.sh`).

Source: `../mm7_m238_claude/export/mm7_m238.glb` (not installed), copied to `work/mm7_m238_source_pre_reduce.glb`
(rollback source, sha256 d85fa95b...). One body material `M238_A` (body and head in one 2080x1024 atlas) with the tier
variants `M238_B/C` (one region: the green cloth), body node `M238`, lamp node `M238Lamp` (899 triangles, drawn only
on the corpse), 1.79 m.

## Ladder

Weld 6,260 -> 208 open edges (unchanged by the picked step). Limits scaled to the 1.79 m height: p99 5.37 mm, max
26.9 mm, silhouette IoU >= 0.98, textured SSIM >= 0.93.

Regions (`make_groups.py`, pieces + dominant bone + gold by base colour):
- **Kept exactly:** circlet, eyes, forehead jewel and gem settings (780).
- **Face** (B_Head faces below 1.63 m in front of the head's centre plane, ears included; 1,819): decimated on its own at 85 %.
- **Hair cap and ponytail** (1,306), **gold trims** (ponytail bands, collar, cuffs, top trims; 586), **vortex shell**
  (2,399), **palms** (657), **earrings** (594), **fingers** (1,368): their own ratios.
- **Torso, arms, neck and inner core:** the rest of the budget.

| run | hair / gold / vortex / palms / earrings / fingers | step | triangles | p99 / max mm | IoU | |
|---|---|---|---:|---|---|---|
| a | 0.45 / 0.8 / 0.55 / 0.6 / 0.5 / kept | 72 % | 7,894 | 5.98 / 14.4 | 0.984 | fail (vortex and hair) |
| b | 0.6 / 0.85 / 0.68 / 0.6 / 0.5 / kept | 74 % | 8,114 | 5.57 / 17.6 | 0.986 | fail (the torso squeezed) |
| c | 0.6 / 0.85 / 0.68 / 0.6 / 0.5 / 0.75 | 72 % | 7,894 | 5.07 / 15.4 | 0.987 | pass |
| **d** | **0.55 / 0.85 / 0.64 / 0.6 / 0.5 / 0.72** | **71 %** | **7,786** | **5.11 / 15.4** | **0.987** | **picked** |
| d | | 70 % | 7,676 | 5.61 / 15.4 | 0.986 | fail |

- Keeping the fingers exactly (1,368 triangles, 12 % of the model) left the torso to absorb the whole cut and it broke
  (b); the fingers at 72-75 % keep their shape in the close-ups.
- Close-ups source vs r71 (`review/close/sheet_d71_tex.png`, `sheet_d71_clay.png`, `sheet_d71_hair.png`): face front,
  three-quarter and side, earrings, ponytail from behind and the side, the hair from above, folded arms, both hands,
  the raised hands of the cast, collar, chest, top from behind, the vortex, Attack, Walking, Death, Hit. No feature
  changed.
- Texture checks: `texture_drift.py r71` 18 faces over 40 (p99 28.7), all on the vortex's streaked mist (z 0.4-0.8 m);
  `dark_slivers.py r71` (L 80, N 4) mostly hairline faces where dark hair meets blue skin. Neither shows in the
  close-ups.

## Build

`scripts/build_export.sh Cand_71 ladder_d.blend`: `export_cand.py` (2 vortex-tip vertices lifted onto z = 0) ->
`swap_lod0.py` (into the rollback source) -> `strip_node_keys.py` (the collapsed-mesh scale keys make the importer
read the body node as an empty, so the LOD builder needs them off) -> `build_lods.py` (ratios 0.5 / 0.22 / 0.08, bounds
and Death/Dead floor contact protected) -> `shrink_shadow_lods.py` -> `carry_variants.py` (7 primitives) ->
`tools/model_hide_collapsed_meshes.py` (the keys again).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch G export | 10,972 | 5,486 | 1,973 | 656 |
| reduced | **7,786** | 3,893 | 1,712 | 619 |

The lamp keeps its 899 triangles: it is drawn only on the corpse (hidden while she is alive), so reducing it saves
nothing in play. Export `export/mm7_m238.glb` 7.3 MB (source 8.1 MB).

## Gates

- **Collapsed-mesh keys** (`model_hide_collapsed_meshes.py`): body hidden from 1.367 s of Death and in Dead, the lamp in
  every clip before 0.533 s of Death, exactly as the batch G export.
- **`lod_check.py`** (every LOD, every frame, on key-stripped copies `work/gate_*.glb`): bounds kept (1.05 x 0.47 x
  1.80 m) at every LOD, no stretched face; lowest points as the source (Standing 2.4 cm, Walking 6.3, Attack 1.6, Hit
  4.4 cm hover; LOD3 0.9-1.4 cm lower like the source's LOD3).
- **Edge stretch** (`outliers.py`, K 3, gate copies): the same maxima as the source in every clip (Standing 2.89,
  Walking 2.84, Attack 4.62, Hit 3.11, Fidget 3.40, Death 4.59) at the same kept vertices (right clavicle, waist).
- **Arm contacts** (`arm_contacts.py`, forearms and hands vs the trunk, cone test): 0 cm in Standing, Walking, Fidget,
  Attack and Hit, as the source.
- **Winding** (`check_winding.py`): 0 inverted closed parts.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m238_reduce_claude/review/viewer/`: batch G export (r100) and
reduced (r71, default) for tiers A, B and C (`viewer_tiers.py` bakes the tier ramps for three.js; the lamp and the
hiding keys are kept). `run_creature_review.py check`: 42 switches, no console errors. Shots: `review/shots/`.

## For the user to review

- The face is cut to 85 % on its own (a uniform cut halves faces); the fingers to 72 %.
- LOD3 (619) is as coarse as before.

## Install (installed 2026-10-21)

Replaces the batch G export of `mm7_m238_claude/` (same binding `../mm7_m238_claude/actors_m238_binding.yml`, same
clips, nodes and materials):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m238_reduce_claude/export/mm7_m238.glb --world mm7
```

Rollback: `work/mm7_m238_source_pre_reduce.glb`.

## Reproduce

1. `REA_NODE=M238.001 REA_GLB=level_generation/creatures/mm7_m238_reduce_claude/work/mm7_m238_source_pre_reduce.glb scripts/b.sh import_source.py`
   (the body mesh imports as `M238.001` under an empty carrying the node keys);
2. `b.sh dump_mesh.py`, `dump_faces.py`, `dump_weights.py`; `python3 scripts/make_groups.py` (KEEP_FINGERS=0);
3. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep.npy REA_PROTECT_FACES=work/protect_face.npy REA_PROTECT_RATIO=0.85
   REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,2:0.85,3:0.64,4:0.6,5:0.5,6:0.72 scripts/run_ladder.sh d 0.71,0.70,0.69`;
4. `b.sh close_m238.py ladder_d.blend Cand_71`, `pair_sheet.py`, `texture_drift.py r71`, `dark_slivers.py r71`;
5. `scripts/build_export.sh Cand_71 ladder_d.blend`;
6. gates on key-stripped copies (`strip_node_keys.py`, `gate_import.py`, `lod_check.py`, `outliers.py`,
   `arm_contacts.py`, `check_winding.py`);
7. `viewer_tiers.py <glb> r100|r71`, `viewer_manifest.py`.
