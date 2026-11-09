# MM8 Efreeti (`m536`, Efreeti A/B/C) reduction (2026-10-19)

User: "OK go ahead" (MM8 triangle-reduction batch of openyamm-f6: m536, m616, m568, m628, m412). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the
installed textures, palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m536.glb`, byte-identical to
`../mm8_m536_claude/export/mm8_m536.glb` (the `assets_dev` runtime copy is the cooked form of the same install,
2026-10-18 10:05), copied to `work/mm8_m536_source_pre_reduce.glb` (rollback source). Nodes: `Body` (12,310, one
material per tier, merged body + head atlas, 55 bones, 4 influences), `FlameTail` (fire shell 2,584 with its own
LOD1-2) and `FlaskRemains` (1,120, hidden while alive); 9 clips. Only `Body` is reduced; the fire shell, its LODs
and the flask remain byte-identical. Scripts are copied from `../mm8_m624_reduce_claude/scripts/` (fixed
`reduce_ladder.py`); `swap_lod0.py` and `carry_variants.py` from `../mm8_m572_reduce_claude/` (keep another node's
own LOD meshes: the fire shell).

The creature build had already cut the body once (`../mm8_m536_claude/review/reduction/`, Blender Decimate at 81 %
with face and fingers kept), so the torso and arms are thin: half the faces (5,946) are the rigid `B_Head` set
(face, horns, cheek horns), and that is where the slack is.

The glTF importer names an empty `Body` and the mesh object `Body.002`; `import_source.py`, `build_lods.py` and
`lod_check.py` rename after import.

## Keep sets

- Weld 11,008 -> 48 open edges; no coincident vertices with other weights (no split-seam fix), no two-sided pairs.
- Small pieces (`REA_SMALL=200 small_pieces.py`, 794 faces in 11 pieces): eyes (139 / 135), teeth (34-54 each) and
  the 144-face mouth piece. The two cheek horns (434 / 432) stay with the head.
- Head (`REA_PROTECT_HEAD=1`, B_Head-dominated faces) decimated on its own; the rest of the budget goes to torso,
  arms, hands and fingers in one cut. Per-region budgets the other way round (body 85-90 % fixed, head taking the
  rest) did worse: `region_err.py` puts the error in the arms, hands and torso, not the head.
- One drift-lock round (`texture_drift.py r65` -> `drift_lock.py`, 794 -> 883 faces): six faces near the forearm
  spikes drifted over 40 (41 cm²); after the lock 5.4 cm².

## Ladder

Limits for 1.3 m (largest posed dimension; rest height 1.6 m): p99 3.9 mm, max 19.5 mm.

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 12,310 | | | |
| uniform | 70 % | 8,616 | 3.70 / 12.89 | 0.996 | pass |
| uniform | 60 % | 7,386 | 4.74 / 14.05 | 0.994 | fail (p99) |
| small kept, body 85 %, head rest | 70 % | 8,614 | 3.70 / 11.25 | 0.994 | pass |
| small kept, head 55 % | 70 % | 8,614 | 3.29 / 11.03 | 0.995 | pass |
| small kept, head 50 % | 67 % | 8,246 | 3.62 / 11.25 | 0.994 | pass |
| small kept, head 45 % | 65 % | 8,000 | 3.80 / 11.25 | 0.994 | pass |
| small kept, head 40 % / 35 % | 65 % | 8,000 | 3.94 / 4.04 | 0.991 | fail (p99) |
| **small + drift lock, head 45 %** | **65 %** | **8,000** | 3.86 / 11.25 | 0.994 | **pick** |
| small + drift lock, head 45 % | 67 % | 8,246 | 3.54 / 11.03 | 0.994 | pass |

Close-ups (`review/close/sheet_head.png`, `sheet_body.png`: source / uniform 70 / h55 r70 / h50 r67 / h45 r65)
show no visible change in the face, teeth, eyes, horns, cheek horns, hands, cuffs, chest or back spikes. The clay
column of the source there comes from the welded `source.blend` (scrambled custom normals: fake wrinkles); judge
shading from `review/glbclose/sheet_src_r65.png` (installed / reduced from the GLBs, textured and clay), where
both look the same.

## Build

`export_cand.py` (Cand_65, node `Body`) -> `swap_lod0.py` -> `build_lods.py` (the m536 ratios 0.5 / 0.25 / 0.125,
4 influences; the horn tips, rest z > 2.975, are protected points: without them LOD3 ended 1 cm short) ->
`../mm6_djn_claude/scripts/shrink_shadow_lods.py` (as the creature's `finish_runtime.py`) -> `carry_variants.py`
(variants on all 7 LOD/shadow primitives) -> `check_winding.py` (0 inverted closed parts): `export/mm8_m536.glb`,
9.9 MB (installed 11.0 MB). Node, material, image, variant and animation lists are identical to the installed file,
including the 27 scale keys of `model_hide_collapsed_meshes.py` (node indices unchanged).

| | LOD0 | LOD1 | LOD2 | LOD3 | fire shell | flask |
|---|---:|---:|---:|---:|---:|---:|
| installed | 12,310 | 6,152 | 3,073 | 1,529 | 2,584 / 1,196 / 480 | 1,120 |
| reduced | 8,000 | 3,997 | 1,992 | 992 | unchanged | unchanged |

`work/lod_check_{src,r65}.json`: every LOD keeps the rest bounds (top 3.0003 at every LOD) and the lowest point of
every clip (Death/Dead 0.314 m, as installed); no face stretches over 20x in any frame. `review/lods/sheet.png`:
installed / reduced, LOD0-3, three-quarter, cast and head; the LOD3 head is visibly coarser up close (992 vs 1,529
triangles), as expected at that distance. The creature build's own hand/digit contact gate needs its editable
master; the reduced surface stays within 11.25 mm of the source in every frame of every clip, under that gate's
12 mm tolerance.

Viewer: <http://127.0.0.1:8765/level_generation/creatures/mm8_m536_reduce_claude/review/viewer/> (installed vs
65 %, three tiers; serve the repository root). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m536_reduce_claude check`: 54 clip switches, no console errors.

## Status

Installed 2026-10-19 after user review ("ok") with `tools/install_model.py --world mm8`; actor regression `mm8_efreeti_actor_models_keep_fire_tail_and_native_tiers` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install after review:

```
python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m536_reduce_claude/export/mm8_m536.glb
OPENYAMM_REGRESSION_FILTER=mm8_efreeti_actor_models ./build/game/openyamm --headless-run-regression-suite actors
```

Rollback: `python3 tools/install_model.py --world mm8
level_generation/creatures/mm8_m536_reduce_claude/work/mm8_m536_source_pre_reduce.glb`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=Body.002 import_source.py` -> `dump_mesh.py` -> `dump_groups.py` ->
`REA_SMALL=200 small_pieces.py` (copied to `work/keep_small200.npy`) -> `REA_KEEP_FACES=work/keep_small200.npy
REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.45 run_ladder.sh h45 0.70,0.67,0.65` -> `texture_drift.py r65` ->
`drift_lock.py work/keep_small200.npy work/keep_lock.npy r65` -> the same ladder with `work/keep_lock.npy` (`h45L`)
-> `close_ladder.py`, `glb_close.py` -> build as above -> `lod_check.py`, `lod_views.py`, `viewer_variants.py`,
`viewer_manifest.py`. `m536_sets.py` holds the region labels of the rejected per-region configurations.
