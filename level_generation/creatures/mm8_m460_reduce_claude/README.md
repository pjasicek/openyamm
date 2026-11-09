# MM8 Cleric (`m460`, Acolyte / Cleric / Priest) reduction (2026-10-19)

User: "OK do those 5" (Lizardman Warrior, Vampire, Smuggler, Gog, Cleric). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons. No retexture, no Meshy credits.
Not installed; awaiting user review.

Sources: the installed `assets_source/worlds/mm8/models/mm8_m460.glb` and `mm8_m460_staff.glb`, byte-identical to
`mm8_m460_claude/export/`, copied to `work/mm8_m460_source_pre_reduce.glb` and `work/mm8_m460_staff_source_pre_reduce.glb`
(rollback sources). Body: one node `Cleric`, three material variants (`Cleric_A/B/C`), merged head/body 2080x1024 atlas
with a hair region mask, 124 joints, 8 influences, eight clips. The staff is a static attachment on the `Staff` joint
(right hand). Scripts start from `mm8_m464_reduce_claude/` (parent fix, exact source weights, coincident-vertex
handling, trims, error and spot locks); the prop chain from `mm8_m604_reduce_claude/`.

## Regions (`make_groups.py`)

Weld 6,428 -> 811 open edges (robe edges), no coincident vertices with other weights. Height 1.697 m: limits p99
5.09 mm, max 25.5 mm. After the weld the body is a few large pieces; `review/labels_groups_keep.png` shows them.

| label | region | faces | picked ratio |
|---|---|---:|---|
| 1 | face (head-atlas part of the skin piece) | 1,543 | 60 % |
| 2 | hair (region mask R, the hair ramp) | 1,951 | 50 % |
| 3 | left hand | 943 | 50 % |
| 4 | right hand (staff grip) | 923 | kept |
| 5 | robe skirt | 1,200 | 90 % |
| 6 | robe top and collar | 1,183 | 85 % |
| 7 | skin: chest, arms, legs | 588 | 90 % |

Every region is its own group (`groups_all.npy`), so the ladder ratio is only a label; `decimate_tex.py` now skips the
free part when it is empty. Kept exactly (`work/keep_o.npy`, 3,672 faces):
- pieces of up to 250 faces: eyes, sash, belt, beads, wrist cuffs;
- the right hand (fitted staff grip and fingers);
- the feet (skin below 15 cm): at 72 % the right foot collapsed under the hem, 80 mm at rest;
- the skirt hem band (below 12 cm): a hem fold showed a light sliver in Walking (`review/close/sheet_o_low.png`, feet);
- the collar and robe-top gold trims (`trim_faces.py` with `TRIM_GROUPS=6,5`, no ring; 373 faces): the collar's
  gold edge went jagged at 70 % (`review/close/sheet_e4_head.png`);
- one error lock (`err_lock.py`, 16 mm, Cand_74 of ladder d): mostly hidden inner surfaces of the skirt and torso
  that moved in Death;
- spot locks (`spot_lock.py`) for the flecks the averaged checks found on visible faces (`visible_only.py`, below) and
  for collar-gold texels on two hair faces beside the right cheek (`hair_gold.py`); the lips (2 cm around the mouth),
  where a dark fleck appeared with the face at 60 %.

## Ladder

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: face 75, hair/L hand 60, rest free (75-55 %) | 7,357 ... 5,815 | 6.23 / 39.2 ... 375 / 652 | 0.989-0.419 | | fail: the free skin/robe region collapsed (right foot gone) |
| b: + skirt 85 % (80-72 %) | 7,719 ... 7,061 | 2.91 / 32.8 ... 6.29 / 45.8 | 0.997-0.986 | | fail: max at hidden skirt and torso points |
| e4: all regions grouped, skin 90, robe top 80, skirt 90 | 7,513 | 3.19 / 22.5 | 0.996 | 0.995 | pass; collar gold edge jagged, flecks |
| f1: + gold trims | 7,485 | 3.70 / 22.5 | 0.997 | 0.996 | pass; hair fleck, collar inside streaked |
| l: + fleck spots, robe top 85 % | 7,683 | 3.29 / 22.5 | 0.996 | 0.996 | pass |
| m: face 60 % | 7,533 | 3.31 / 22.5 | 0.996 | 0.996 | pass; dark fleck at the lips |
| **o: + lips, hem band** | **7,645** | **3.21 / 24.8** | **0.997** | **0.996** | **picked** |

- **Pick 78 %:** outside the head, hands and small pieces the mesh was already lean (robe top 1,183 faces, skirt
  1,200, skin 588); cutting those harder broke the collar, hem and hidden layers first. The savings come from the face
  (60 %), hair (50 %) and left hand (50 %).
- **Close-ups** (`review/close/sheet_o_{head,mid,low,pose}.png`, source / r74, textured and clay): face, hair, collar
  front and back, torso, shoulders, both hands and the Cast hands, cuffs, sash, hem, feet, Death and Attack match.
  The collar's inside reads slightly smoother; the face is a little softer around the eye sockets in clay.
- **Flecks:** `dark_slivers.py` (dark and light, `REA_DARK_L=80 REA_DARK_N=4`) flags 9 + 7 faces at the pick, all on
  hidden skin and lining. `visible_only.py` (new) keeps a flagged face only if a ray from it escapes the mesh:
  0 visible. `texture_drift.py`: 1 face over 40 (0.1 cm2). `hair_gold.py`: 0 (source 0).

## Normals

Plain smooth. The installed GLB's normals are within 2.7 deg (median) of smooth normals and have no split seams;
rendered straight from the GLBs (`scripts/glb_close.py`, `review/glbclose/sheet.png`) the installed model and the
reduction shade the same.

## Build

`export_cand.py` (Cand_74 of `work/ladder_o.blend`, REA_NODE=Cleric, 8 influences) -> `swap_lod0.py ... Cleric` ->
`build_lods.py` (the creature's own settings, `mm8_m460_claude/scripts/build_lods.py`: 0.5 / 0.25 / 0.125, 8
influences; protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame and the top 5 mm of the
crown, 61 points) -> `carry_variants.py`: `export/mm8_m460.glb`, 6.5 MB (installed 7.0 MB). Textures, variants,
clips and node structure are the installed ones. `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,811 | 4,905 | 2,452 | 1,224 |
| reduced | 7,645 | 3,821 | 1,910 | 955 |

Shadow meshes match the colour LODs, as installed. `lod_check.py` (REA_NODE=Cleric, `work/lod_check_{src,r74}.json`):
every LOD keeps the 1.70 m height and 1.12 m width; the lowest point is -1.0 mm in Death at every LOD, as LOD0; Standing
stays at LOD0's 4.7 mm on every LOD (the installed LOD3 rose to 9.0 mm). Faces stretching over 20x in Death/Hit are the source's own robe cloth
(1-3 per clip at LOD0, as installed). `review/lods/sheet.png` compares all LODs (Standing and Hit).

## Staff: unchanged

600 triangles (shaft, gold bands, guard disc, knob, spear tip; 12-sided rings, the shaft between bands already single
segments). With the grip kept (`staff_comp.npy`), `prop_parts.py` at 80 / 70 / 60 / 50 % gave 502 / 452 / 404 / 356
triangles (max 0.11-0.37 % of the length), but even 70 % turned the guard disc into a star and faceted the knob
(`review/staff/sheet_clay.png`). Cutting only the 96 shaft faces between the ends saves 30-50 triangles. The staff
and its LODs (600 / 300 / 149 / 75) stay as installed; `check_winding.py`: 0.

## Retexture check

- **Texture set:** unchanged; the reduction keeps UVs.
- **Skin:** face texels are darker than the chest and hands (linear luminance median 0.20 vs 0.33-0.37), but the face
  set includes stubble, brows and baked shading; rendered, the face reads only slightly warmer than the chest, as in the
  accepted installed model (its README: neck seam mismatch 0.45/255). No unify step.
- **Existing faults:** none that the reduction exposed. A small dark triangle at the back of the left shoulder (an
  open vest edge showing its back face, `hair_side` clay) is in the source too.
- **Verdict:** no retexture and no local texture fix.

## Review

Viewer `review/viewer/` (installed vs reduced per tier, staff included; tier ramps baked by `viewer_variants.py`, the
unchanged staff primitive copied from the installed viewer files by `viewer_staff.py`):
http://127.0.0.1:8912/level_generation/creatures/mm8_m460_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 48 clip switches, no console errors. `review/shots/std_b_pair.png`: tier B
installed / reduced.

## Status

Installed 2026-10-19 (user: "cleric ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_cleric ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_cleric_actor_models_keep_tiers_roles_and_staff_cast` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m460_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Cleric, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py` ->
`make_groups.py` (groups.npy, keep_base.npy; `groups_all.npy` = groups with label 0 -> 7) -> ladder d
(`REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.5,5:0.8,6:0.7
REA_HEIGHT_M=1.697 run_ladder.sh d 0.74,0.72,0.70`) -> `REA_CAND=Cand_74 REA_ERR_MM=16 REA_LOCK_R=0.02 err_lock.py --
work/keep_base.npy work/keep_e.npy` -> `TRIM_GROUPS=6,5 TRIM_GROUPS_FILE=work/groups_all.npy trim_faces.py
work/keep_e.npy work/keep_f0.npy 0` -> spot locks: `spot_lock.py keep_f0 keep_h 0.015 0.016,-0.088,1.643
0.022,-0.083,1.641 0.066,-0.004,1.585 -0.089,-0.005,1.499`, `keep_h keep_i 0.015 0.063,-0.046,1.481
-0.067,-0.08,1.432`, `keep_i keep_j 0.012 -0.085,-0.008,1.552 -0.028,0.071,1.573 -0.048,0.063,1.55`, `keep_j keep_k
0.02 -0.079,-0.039,1.541 -0.085,-0.008,1.552`, `keep_k keep_n 0.02 0,-0.105,1.575` -> keep_o = keep_n + skirt faces
below 12 cm -> `REA_KEEP_FACES=work/keep_o.npy REA_GROUPS=work/groups_all.npy
REA_GROUP_RATIOS=1:0.6,2:0.5,3:0.5,7:0.9,6:0.85,5:0.9 REA_HEIGHT_M=1.697 run_ladder.sh o 0.74` -> checks
(`dark_slivers.py`, `visible_only.py`, `texture_drift.py`, `hair_gold.py`, `group_error.py`, `close_human.py`,
`close_sheet.py`) -> build as above -> `lod_check.py`, `lod_views.py`, `glb_close.py` -> `viewer_variants.py
export/mm8_m460.glb r74` -> `viewer_staff.py`. Staff trials: `prop_dump.py -- staff`, `prop_parts.py`,
`prop_build.py`, `staff_views.py`.

## Gait rollout (2026-10-31, package h18)

New in-place locomotion clips appended to the installed source (every existing clip, mesh, skin and material
byte-identical): `Jog` (Unarmed-Run-Forward legs, 0.72 s, stride 2.2160; robe simulated with a numpy port of `robe_sim.py`, staff lifted off the floor): his chase (2.89-3.62 u/s, a run pace) played `Walking` at x1.52-1.90. Arms, hands and props come from this model's own fitted clips. Built, gated and installed in
[../gait_rollout_20261031/h18/](../gait_rollout_20261031/h18/README.md); bindings for the coordinator in its
`bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h18/scripts/rebuild.sh m460`; rollback:
install `../gait_rollout_20261031/h18/work/mm8_m460_pre_gait.glb`. A far-LOD repair, head-bob, floor-fix or reduction
rerun on this model must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
