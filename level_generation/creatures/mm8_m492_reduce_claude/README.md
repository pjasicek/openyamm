# MM8 Dragon (`m492`, Dragon A/B/C, Wimpy Dragon A/B/C) reduction (2026-10-18)

User: "Do the tris reduction according to our playbook on mm8 dragon". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the
installed textures, palette variant and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m492.glb` (identical to `mm8_m492_claude/export/`,
motion v3), copied to `work/mm8_m492_source_pre_reduce.glb` (rollback source). One material, one `Body` node.

## Mouth seam fix (new for this creature)

The m492 build split the fused lips along a seam (`mm8_m492_claude/scripts/rig_dragon.py`): upper lip on Head, lower
lip on Jaw, with coincident vertices (52 pairs, also the two oral-cap fan centres). The first ladder drew a dark box
between the open jaws in Attack at every step (36 faces stretched over 20x their rest area):
- the MeshLab weld-back and the weight transfer both picked either vertex of a coincident pair;
- MeshLab collapses near the mouth corners also built faces across the seam.

Fixes: `decimate_tex.py` moves coincident vertices 2e-5 m apart towards their own faces for MeshLab and the
weld-back and records each output vertex's source index; `reduce_ladder.py` gives source vertices their exact
source weights (`exact_weights`); `mouth_keep.py` keeps 945 faces exactly (within 1.2 cm of the lip seam, plus the
upper teeth cones). After that, no face stretches in any clip at any LOD (`scripts/lod_check.py`).

## Ladder

Weld 21,502 -> 321 open edges (unchanged by every step); 3 zero-area lip slivers drop on import (18,278 -> 18,275).
Limits scaled to the 0.79 m bound (p99 2.37 mm, max 11.85 mm), 4 influences like the installed model.

| step | triangles | p99 / max mm | IoU (front) | SSIM | |
|---|---:|---|---|---|---|
| source | 18,278 | | | | |
| 70 % | 12,791 | 1.19 / 5.04 | 0.986 | 0.997 | pass |
| **55 %** | **10,051** | 1.85 / 6.63 | 0.976 | 0.996 | **visual pick** (IoU) |
| 45 % | 8,223 | 2.45 / 9.33 | 0.964 | 0.994 | fail (p99, IoU) |

The 55 % IoU failure is the front and back views only (side views 0.984-0.987): one-pixel flips along the edge-on
wing membranes and a small patch at each wing elbow (`review/iou_front_crops.png`). Close-ups show no change at
open mouth, head, horns, fore and hind claws, dorsal and tail spines, belly and wing membranes:
`review/close/sheet_mouth_a.png`, `sheet_mouth_b.png`, `sheet_wings_r55.png` (source / 70 / 55 / 45).
Texture drift (`texture_drift.py`): 290 faces over 40, almost all area on large wing-membrane faces; the membrane
veins and scale pattern render unchanged face-on, so no drift lock was run.

## Build

`export_cand.py` (Cand_55) -> `swap_lod0.py` -> `build_lods.py` (same ratios as the m492 project: 0.5 / 0.25 /
0.125, 4 influences) -> `carry_variants.py`: `export/mm8_m492.glb`, 31.9 MB (installed 34.0 MB), 9 clips, palette
variant on all 8 colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 18,278 | 9,122 | 4,550 | 2,254 |
| reduced | 10,051 | 5,006 | 2,480 | 1,204 |

`work/lod_check_{src,r55}.json`: every LOD keeps the source bounds (height 0.426 m, wing span 0.95 m; the LOD1-3
tail tip is 1 cm shorter, like installed LOD2/3) and stays above the floor in every frame of every clip (lowest
0.3 mm in Hit, as the source). LOD2 has one face stretching over 20x in Death. `review/lods/sheet.png` compares all
LODs at rest and at the attack release.

Viewer: `review/viewer/` (installed vs 55 %), `tools/run_creature_review.py ... check`: 18 clip switches, no console
errors.

## Normals check (2026-10-18)

The source mesh carries custom normals. In the welded `work/source.blend` they differ from smooth normals by 20°
median, but that is the weld's doing: Blender stores custom normals relative to the default normals, and merging
seam vertices rotates them, so `source.blend` renders show fake wrinkles. Rendered straight from the GLBs
(`scripts/glb_close.py`, `review/glbclose/sheet.png`), the installed source shades smooth, like this reduction; a
normal transfer from `source.blend` (`REA_NORMALS=transfer`) added that noise and was discarded. The installed export
is unchanged. The close-up sheets in `review/close/` show `source.blend` normals for the source column.

## Status

Installed 2026-10-18 (user: "OK fine") with `tools/install_model.py --world mm8`; runtime copy 6.1 -> 4.0 MB.
`OPENYAMM_REGRESSION_FILTER=mm8_dragon_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_dragon_actor_models_keep_native_sizes_and_simulation` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m492_source_pre_reduce.glb` with
`tools/install_model.py --world mm8`. No in-game captures were taken for this geometry-only change.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `dump_mesh.py` -> `small_pieces.py`
-> `mouth_keep.py - work/keep_mouth.npy` -> `REA_KEEP_FACES=work/keep_mouth.npy run_ladder.sh mouth 0.70,0.55,0.45`
-> `close_ladder.py`, `close_sheet.py`, `texture_drift.py` -> build as above -> `lod_check.py`, `lod_views.py`.
