# MM8 Gorgon (`m564`, Brass / Bronze / Iron Gorgon) reduction (2026-10-18)

The user asked for the five MM8 triangle-reduction picks (m580, m408, m564, m624, m516). This is the default route
of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch. No part needed rebuilding, so the
installed textures, the three palette variants and the region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m564.glb`. It is identical (hash) to
`mm8_m564_claude/export/mm8_m564.glb`, and the `assets_dev` runtime copy was cooked from it at the same time, so it is
not a stale source. It is copied to `work/mm8_m564_source_pre_reduce.glb` as the rollback source. The mesh is one
continuous surface: horns, ears, hooves and the tail tuft are not separate pieces, and the only small pieces are two
degenerate scraps (8 faces) at the left hock. It has one material and one `Gorgon` node.

## Import and keep set

- The weld takes the open edges from 13,272 to 48, and the weld and later steps leave all 48 unchanged. No faces
  drop (12,804), so there are no reversed two-sided copies.
- 27 vertices coincide with other vertices that carry different weights: at the chest (UpperArm_L/Neck1) and at the
  left hock (Shin_L beside HindPastern_L). `scripts/seam_keep.py` keeps the 155 faces within 1 cm of them, plus the
  scraps, exactly (`work/keep_seam.npy`). This is the m492 split-seam rule, and m492's `decimate_tex.py` and
  `reduce_ladder.py` (`exact_weights`) are used unchanged.
- Limits are scaled to the 0.95 m bound (nose to tail tuft): p99 2.85 mm, max 14.25 mm. The model uses 4 influences.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 12,804 | | | | |
| uniform + seam keep | 70 % | 8,962 | 1.82 / 8.35 | 0.994 | 0.988 | pass |
| | 60 % | 7,682 | 2.45 / 9.58 | 0.992 | 0.986 | pass |
| | **55 %** | **7,042** | 2.77 / 9.68 | 0.990 | 0.985 | **auto pick, visually confirmed** |
| | 50 % | 6,402 | 3.05 / 10.61 | 0.988 | 0.983 | fail (p99) |
| head (3,300 faces) at 80 % | 60 / 55 % | 7,682 / 7,042 | 2.92 / 10.61, 3.44 / 13.97 | | | fail |
| lower legs (z < 7 cm) at 75 % | 60 / 55 % | 7,680 / 7,040 | 2.89 / 10.61, 3.34 / 13.97 | | | fail |

Protecting the head or the dense hooves fixes the borders of each part, and that costs the body more than it saves
(both runs failed at the same counts). A uniform cut is best here.

Texture drift (`texture_drift.py`) at 55 %: 15 faces over 40, 7.6 cm² in total, all of them small faces. The close-ups
show no change to the painted plate grooves, so no drift lock was run.

- Close-ups: `review/close/sheet_r55.png` (source / 60 / 55 %) and `sheet_uni.png` (70 / 60 / 50 %). Their source
  column renders the welded `source.blend`. The weld scrambles the stored custom normals, so the source clay looks
  crumpled; those columns are for geometry only.
- Shading ground truth, rendered from the GLBs with their own normals (`scripts/glb_close.py`):
  `review/glbclose/sheet_tex.png` and `sheet_clay.png`. Head, horns, eyes, muzzle, ears, the Attack strike, cloven
  hooves, flank, rear and tail are unchanged.
- Known small change: the round stud above the right hind hoof flattens slightly. Every step from 70 % down does this.

## Build

`export_cand.py` (Cand_55) -> `swap_lod0.py` -> `build_lods.py` (the m564 ratios 0.5 / 0.25 / 0.125, 4 influences)
-> `shrink_shadow_lods.py` (copied from the m564 build: shadow LODs tucked inside the colour surface) ->
`carry_variants.py`. Output: `export/mm8_m564.glb`, 6.8 MB (installed 8.1 MB), 8 clips, 3 variants on all 8
colour/shadow meshes, winding check 0 inverted.

`build_lods.py` protects the 9 vertices within 2 cm of each horn tip (`protected_points`). Without them, LOD3 lost
4 cm of both horns (front bound -0.478 -> -0.439 m).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,804 | 6,402 | 3,201 | 1,600 |
| reduced | 7,042 | 3,520 | 1,760 | 880 |

The LOD check (`work/lod_check_{src,r55}.json`) found the following:
- Every LOD keeps the horn-to-tail length (0.954 m at LOD0, 0.952 m at LOD3). The height is 0.436 m at LOD0 and LOD1, 0.433 m at LOD2 and
  0.430 m at LOD3 (installed LOD3: 0.432 m).
- The lowest point in any frame of any clip is -2.4 mm at LOD3 (installed LOD3: -2.0 mm) and -0.4 mm at LOD0
  (installed LOD0: -1.0 mm).
- No face stretches over 20× its rest area in any clip at any LOD.

`review/lods/sheet.png` compares all LODs at rest and at the strike.

Viewer: `review/viewer/` holds the installed Brass Gorgon and the reduced Brass, Bronze and Iron Gorgons. They are
LOD0-only copies with that project's baked tier textures (`scripts/viewer_tiers.py`).
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m564_reduce_claude check` gave 32 clip
switches and no console errors.

## Status

Installed 2026-10-18 after user review ("OK") with `tools/install_model.py --world mm8 export/mm8_m564.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_gorgon_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_gorgon_actor_models_keep_native_tiers_and_simulation` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m564_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

To reproduce, run these in order:
1. `import_source.py` (REA_NODE=Gorgon, REA_GLB=the rollback source)
2. `REA_PROTECT=Head dump_mesh.py`
3. `small_pieces.py`
4. `seam_keep.py work/keep_small.npy work/keep_seam.npy`
5. `REA_KEEP_FACES=work/keep_seam.npy run_ladder.sh uni2 0.65,0.60,0.55`
6. `close_ladder.py`, `close_sheet.py`, `texture_drift.py`
7. Build as above.
8. `lod_check.py` (REA_NODE=Gorgon), `lod_views.py`, `glb_close.py`, `viewer_tiers.py`

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/q3`](../gait_rollout_20261031/q3/README.md) added three clips. Each keeps
`animate_gorgon.py`'s leg machinery.

| clip | gait | length | stride |
|---|---|---|---|
| Walk2 | lateral walk | 0.80 s | 0.512 |
| Run2 | flying trot | 0.60 s | 0.774 |
| Sprint | transverse gallop, MAW's chase | 0.4667 s | 1.1247 |

The chase had played Running ×1.56-1.87, and MAW ×3.1-3.3. Every tier now plays ×0.97-1.17.

Binding:
- `walking: Walk2`, `stride_length: 0.512`
- `run: Run2`, `run_stride_length: 0.774`
- `sprint: Sprint`, `sprint_stride_length: 1.1247`

The clips were grafted onto the installed GLB; the original eight clips are byte for byte (the
`mm8_gorgon_actor_models_keep_native_tiers_and_simulation` regression checks them).

Rebuild: `blender -b --factory-startup -P scripts/gait_m564.py -- work/m564_clips.glb`, then `graft_clips.py` (see the
q3 README). A far-LOD repair rerun or any re-export must re-graft these clips. Viewer revision `gorgon-gait-1`.
