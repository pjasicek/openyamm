# MM8 Thunder Lizard (`m516`, Young Basilisk / Basilisk / Elder Basilisk) reduction (2026-10-18)

User: "OK do those 5" (MM8 triangle-reduction batch). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md),
no-retexture variant: no part needed rebuilding, so the installed textures, region-palette variants and ramps stay
valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m516.glb` (byte-identical to `../mm8_m516_claude/export/`,
attack revision 02; the `assets_dev` runtime copy was cooked from it at the same time), copied to
`work/mm8_m516_source_pre_reduce.glb` (rollback source). One material per tier (body + head atlas), one `Body` node,
30 bones, 4 influences, 8 clips. The project build had already cut 15 % with face and toe detail protected.

## Keep sets

- Weld 12,474 -> 81 open edges; no coincident vertices with other weights (no split-seam fix needed).
- Small pieces kept exactly (`small_pieces.py`, `REA_SMALL=200`): both eyes (122/123 faces) and the 194-face piece in
  the front of the head; 439 faces.
- Thigh crease patch (`patch_keep.py`, 4 cm, mirrored): every uniform step had its maximum error (28-31 mm,
  `Running:15`) at one inner-thigh/hip vertex, plus a shoulder point (35 mm, `Attack:24`) from 60 %. Rest positions
  were found with `rest_points.py`; the patches add 21 faces.
- Head (Head/Jaw weights, 2,853 faces) decimated on its own at 80 % (`REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8`):
  the uniform cut softened the lower teeth row and the gum line in the open-mouth Fidget frame.

## Ladder

Limits for the 2.0 m standing height (p99 6 mm, max 30 mm; the 3.5 m tail length would allow 10.5 / 52 mm).

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 12,644 | | | |
| uniform, eyes kept | 80 % | 10,114 | 2.93 / 28.69 | 0.996 | pass (thigh point) |
| uniform, eyes kept | 70 % | 8,850 | 4.30 / 31.20 | 0.993 | fail (thigh point) |
| + crease/shoulder patches | 60 % | 7,586 | 5.41 / 26.33 | 0.989 | pass; lower teeth soften |
| + crease/shoulder patches | 55 % | 6,954 | 6.22 / 28.47 | 0.987 | fail (p99) |
| + patches, head 80 % | 65 % | 8,216 | 4.98 / 26.33 | 0.990 | pass |
| **+ patches, head 80 %** | **60 %** | **7,584** | 5.86 / 28.47 | 0.987 | **pick** |
| + patches, head 80 % | 55 % | 6,952 | 6.67 / 30.94 | 0.984 | fail (p99, max) |

Texture drift at the pick: 6 faces over 40 (20.6 cm²), no drift lock. Close-ups (`review/close/sheet_head.png`,
`sheet_body.png`; source / u70 / u60 / h60 / u55 / h55) and GLB renders with each file's own normals
(`review/glbclose/sheet_src_r60.png`: installed / 60 % textured, then clay) show no change in the frills, crest and
dorsal spines, eyes, open mouth, hand and foot claws, tail or belly. The clay renders in `review/close/` come from the
welded `source.blend`, whose custom normals are scrambled by the weld; judge shading only from `review/glbclose/`.

## Build

`export_cand.py` (Cand_60) -> `swap_lod0.py` -> `build_lods.py` (the m516 ratios: 0.5 / 0.25 / 0.125, 4 influences)
-> `../mm8_m516_claude/scripts/shrink_shadow_lods.py` (shadow LOD1-3 tucked inside the surface, as installed) ->
`carry_variants.py` (variants on all 7 LOD/shadow primitives) -> `check_winding.py` (0 inverted closed parts):
`export/mm8_m516.glb`, 7.4 MB (installed 8.5 MB), 8 clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,644 | 6,321 | 3,158 | 1,579 |
| reduced | 7,584 | 3,791 | 1,895 | 948 |

`work/lod_check_{src,r60}.json`: every LOD keeps the 2.0 m height; no face stretches over 20x in any frame of any clip;
all LODs stay above the floor in every clip (lowest 4.3 mm, LOD1 Death). LOD3 ends 3.6 cm short at the tail tip
(installed LOD3: 0.7 cm) and its feet sit up to 2.1 cm above the floor (installed LOD3: 1.0 cm).
`review/lods/sheet.png`: installed / reduced, LOD0-3, standing three-quarter and bite.

Viewer: `review/viewer/` (installed vs 60 %); `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m516_reduce_claude check`: 16 clip switches, no console errors.

## Status

Installed 2026-10-18 after user review ("OK") with `tools/install_model.py --world mm8 export/mm8_m516.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_thunder_lizard_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_thunder_lizard_actor_models_keep_native_tiers_and_biped` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m516_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `dump_mesh.py` -> `REA_SMALL=200
small_pieces.py` -> `patch_keep.py work/keep_small200.npy work/keep_p2.npy 0.2114,-0.0753,0.8351 0.2035,-0.2295,1.3617`
-> `REA_KEEP_FACES=work/keep_p2.npy REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8 run_ladder.sh hpp 0.65,0.60,0.55` ->
`close_ladder.py`, `glb_close.py`, `texture_drift.py r60` -> build as above -> `lod_check.py`, `lod_views.py`.

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/q3`](../gait_rollout_20261031/q3/README.md) added three clips for the two-legged body.
Each keeps `animate_lizard.py`'s machinery.

| clip | gait | length | stride |
|---|---|---|---|
| Walk2 | grounded run, no flight, Standard's wandering | 0.70 s | 1.988 |
| Run2 | run with short flights | 0.60 s | 3.414 |
| Sprint | bounding strides, MAW's chase | 0.4833 s | 4.8285 |

The installed Running had served both wandering (×1.15-1.37) and chasing (×2.3-2.7; MAW ×4.3-4.5). Every tier now
plays ×0.91-1.15.

Binding:
- `walking: Walk2`, `stride_length: 1.988`
- `run: Run2`, `run_stride_length: 3.414`
- `sprint: Sprint`, `sprint_stride_length: 4.8285`

The clips were grafted onto the installed GLB; the original clips are byte for byte.

Rebuild: `blender -b --factory-startup -P scripts/gait_m516.py -- work/m516_clips.glb`, then `graft_clips.py` (see the
q3 README). A far-LOD repair rerun or any re-export must re-graft these clips. The viewer is
`../mm8_m516_claude/review/viewer`, revision `lizard-gait-1`.
