# MM7 Roc (m390) triangle reduction — 2026-10-21

User: "all 3 are good, reduce tris" (Batch H Roc, accepted). [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
default route, no-retexture branch, with the scripts of [mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md)
(texture-aware MeshLab ladder, floor-contact LOD lock, stretch/drift/sliver checks). No Meshy credits. Nothing is
installed; MM8 files were only read.

**Result: 6,867 → 6,237 triangles (−9 %)**, `export/mm7_m390.glb`, 8.0 MB (was 8.3 MB),
sha256 `25f54029de84ca912cb4b705ad1b7a8d745bc70ce6deae60b00fb8b8f818ecfd`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| current (`mm7_m390_claude/export/mm7_m390.glb`) | 6,867 | 3,432 | 1,704 | 822 |
| reduced (`export/mm7_m390.glb`) | 6,237 | 3,118 | 1,542 | 742 |

## Source and regions

Ladder source: the unreduced Thunderbird (`work/source_pre_reduce.glb`, copy of
`mm8_m552_reduce_claude/work/mm8_m552_source_pre_reduce.glb`, 11,447 triangles after the weld), so the result is one
reduction from the original, not a second one on top of the installed 60 % step. Same images, UVs, weights, clips and
sockets. Limits for the 0.69 m model: p99 2.07 mm, max 10.35 mm.

Per-region budgets (`scripts/face_regions.py` → `work/groups.npy`, dominant bone per face; `decimate_tex.py`
`REA_GROUPS`): group 1 legs and talons (Thigh/Shin/Toe, 1,344 faces), 2 head and neck (1,060), 3 belly and back
(Root/Chest, 1,291), 0 wings, flight feathers and tail (7,752), which takes the rest of each step's budget.

| run | group ratios (legs, head, belly) | step | tris | p99 mm | max mm | worst | IoU min | SSIM |
|---|---|---|---:|---:|---:|---|---:|---:|
| m552 uniform (installed) | — | r60 | 6,867 | 1.70 | 9.33 | Attack:21 | 0.981 | 0.993 |
| m552 uniform | — | r50 | 5,723 | 2.14 | 15.66 | Attack:21 | 0.976 | 0.991 |
| g1 | 0.8, 0.75, 0.7 | r55 / r50 / r45 / r40 | 6,293 / 5,721 / 5,149 / 4,575 | 2.39 / 3.02 / 3.93 / 5.55 | ≤ 10.3 | wings | 0.971 / 0.960 / 0.950 / 0.923 | |
| g2 | 0.75, 0.55, 0.55 | r56 / r54 / r51 | 6,521 / 6,179 / 5,835 | 1.95 / 2.17 / 2.43 | 6.6 | Hit:3 | 0.976 / 0.973 / 0.971 | 0.991 |
| g3 | 0.7, 0.5, 0.5 | r56 / r54 / r53 | 6,409 / 6,237 / 6,065 | 1.94 / 2.02 / 2.14 | 10.68 | Attack:21 | 0.978 / 0.975 / 0.973 | 0.991 |
| **g4** | **0.7, 0.5, 0.6** | r55 / **r54** / r53 | 6,351 / **6,237** / 6,123 | 1.99 / **2.07** / 2.15 | **6.55** | Hit:3 | 0.975 / **0.974** / 0.973 | 0.991 |

Protecting the legs and belly fixed the installed step's worst spot (thighs/belly in the talon strike: 9.33 → 6.55 mm;
uniform 50 % misses by 15.7 mm there). What remains is the wings: p99 rises as soon as they take a larger cut, so the
gain over the installed 60 % is small. **Picked g4 r54**: p99 at the limit, max well under it.

The automatic IoU gate (0.98 in every view) fails for every step below the installed one, on the **front view**: the
edge-on wings make a 6,911-pixel silhouette, and the r56 difference is 164 pixels of 1-pixel aliasing along the wing
rims (`review/front_iou_diff_r56.png`: red source-only, blue reduced-only), not lost shape. The step was therefore picked visually, as the playbook allows for the
goblin, hydra and flying eye.

## Checks (g4 r54)

- No stretched faces in any clip (`stretch_check.py`); texture drift: 3 faces over 40, 0.6 cm² (`texture_drift.py`);
  dark slivers: 56 faces, the same noise floor as the installed step (53), stacked feathers (`dark_slivers.py`).
- Close-ups source / r55 / r54, textured and clay (`review/close/sheet_g4.png`): beak side and three-quarter in the
  strike, head front, both feet (flight and strike), belly, tail fan, both wing surfaces, wing front, back and corpse
  match. The source column's clay noise is the weld's rotated custom normals (playbook: judge shading from GLBs).
- LODs (`lod_check.py` → `work/lod_check_r54.json`): every LOD keeps the source bounds; Death/Dead rest 1.1 mm above
  the floor (45 contact points locked from `floor_contacts.py`); no stretched faces.
- `check_winding.py`: 0 inverted closed parts. Images byte-identical to the Roc export (same base colour, normal,
  metal/rough and region mask), so the MM7 ramps (`../mm7_m390_claude/textures/m390_ramps.json`) are unchanged.
- Viewer: current vs reduced for each MM7 tier, `run_creature_review.py check` 36 switches, no console errors;
  `review/tiers_cur_vs_r54.png` (flight and talon strike, three tiers) matches.

Viewer: http://127.0.0.1:8912/level_generation/creatures/mm7_m390_reduce_claude/review/viewer/

## Build

```sh
REA_GLB=<this>/work/source_pre_reduce.glb REA_NODE=Thunderbird blender -b -P scripts/import_source.py
blender -b -P scripts/dump_mesh.py; blender -b -P scripts/face_regions.py   # then work/groups.npy (see README table)
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.6 scripts/run_ladder.sh g4 0.555,0.545,0.535
cp work/ladder_g4.blend work/ladder.blend; REA_CAND=Cand_54 REA_NODE=Thunderbird blender -b -P scripts/export_cand.py
python3 scripts/swap_lod0.py work/source_pre_reduce.glb work/cand_export.glb work/r54_lod0.glb Thunderbird
REA_NODE=Thunderbird blender -b -P scripts/floor_contacts.py; blender -b -P scripts/build_lods.py
python3 scripts/shrink_shadow_lods.py work/r54_lods.glb work/r54_shadow.glb; python3 scripts/carry_variants.py work/r54_shadow.glb
python3 scripts/mm7_variants.py    # MM7 variants m390_a/b/c, materials Roc_A/B/C, MM7 ramps -> export/mm7_m390.glb
```

`run_ladder.sh` uses the pymeshlab venv in this session's scratchpad; recreate one (`pip install pymeshlab numpy
scipy pillow`) and point `VENV` at it.

## Install later (not done)

Same command and binding as [mm7_m390_claude](../mm7_m390_claude/README.md), with this file:
`python3 tools/install_model.py level_generation/creatures/mm7_m390_reduce_claude/export/mm7_m390.glb --world mm7`.
Rollback / unreduced: `mm7_m390_claude/export/mm7_m390.glb`. Record it in `REDUCTION_LEDGER.md` when installed.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: living lowest at -151.5 (suggested hover 0.266206); living lowest at -179.0 (suggested hover 0.266206); living lowest at -206.6 (suggested hover 0.266206).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m390.glb export/mm7_m390.glb --hover 0.266206 Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m390.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
