# MM8 Skeleton Archer (`m628`, Skeletons Archer A/B/C) reduction (2026-10-19)

User: "OK go ahead" (MM8 triangle-reduction batch of openyamm-f6: m536, m616, m568, m628, m412). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the installed
textures, palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m628.glb`, byte-identical to `../mm8_m628/export/mm8_m628.glb`
(attack-opening revision, 2026-10-18 14:55); the `assets_dev` runtime copy was cooked from it at the same time (same
seven clips, not stale). Copied to `work/mm8_m628_source_pre_reduce.glb` (rollback source). One `SkeletonArcher` node
with two primitives: body+head atlas (`SkeletonArcherBody_A`, three variants, 10,368 tris) and the skinned flexing bow
(`SkeletonArcherBow_A`, 1,699 tris: limbs, grip, nocked and spare arrows). 60 bones, at most 3 influences at LOD0.
Scripts are copied from `../mm8_m624_reduce_claude/scripts/` (parent-before-transform `reduce_ladder.py`).

## Keep sets

Weld 11,143 -> 910 open edges (unchanged by every step); no merged two-sided faces (12,067 before and after).
30 coincident vertices with other weights: 24 are the two string tubes, which rest as unit tubes at the origin and are
placed by the `StringTop`/`StringBottom` bones; the other two pairs are single body points (neck, right thigh).

`m628_sets.py` (per-face dominant bone, material, flat-shaded faces) -> `m628_keep.py` -> `work/keep_a.npy`, 5,877 faces
kept exactly:

| set | faces | why |
|---|---:|---|
| bow material | 1,699 | limbs flex, nocked arrow, spare arrows, fitted grip |
| string tubes | 24 | |
| finger-weighted | 1,124 | 19 capped rigid segments of the bare hand, glove digits, bow grip |
| hand-weighted | 494 | |
| small pieces (up to 80 faces) | +2,528 | teeth, vertebrae, foot and hand bones, studs; ends taper at any cut |
| coincident body points (1.2 cm) | +8 | |

One drift-lock round (`drift_lock.py` on the first pick) added 100 faces -> `work/keep_b.npy` (5,977).

The source's flat-shaded faces (243: bow tips, arrows, string tubes) are all kept; `decimate_tex.py` now records the
kept faces' source indices and `reduce_ladder.py` (`REA_SHARP=work/sharp.npy`) keeps them flat.

## Ladder

Limits for the 1.77 m model: p99 5.3 mm, max 26.6 mm. Rest-pose deviation per region (`region_sweep.py`): the skull
(one 2,057-face piece) and jaw (351) take a cut easily (skull at 50 %: p95 1.8 mm), but the bones, ribs, pelvis and
thighs are already lean (p95 4.5 mm at 80 %). The pass/fail is set by the body; the skull is set by close-ups.

| config | triangles | p99 / max mm | IoU | |
|---|---:|---|---|---|
| source | 12,067 | | | |
| uniform (keep_a), 80 % | 9,653 | 5.12 / 24.55 | 0.991 | pass |
| uniform, 75 % | 9,049 | 6.62 / 25.77 | 0.985 | fail |
| head protected at 80 %, 85 % | 10,255 | 7.07 / 25.77 | 0.984 | fail (cut pushed onto bones) |
| skull 30 %, jaw 50 %, rest adaptive, 78 % | 9,411 | 5.24 / 24.55 | 0.990 | pass; skull brow and sockets change |
| + drift lock, 79 % | 9,531 | 4.94 / 24.55 | 0.991 | pass; skull still changed |
| + drift lock, skull 50 %, jaw 50 % | 9,979 | 4.82 / 24.55 | 0.992 | pass; notch at the left chin |
| **+ drift lock, skull 60 %, jaw 60 %** | **10,243** | 4.79 / 24.55 | 0.993 | **pick** (SSIM 0.995) |

The max (24.55 mm, `Death:6`) is one left-clavicle point in every step, including the gentle ones; it stays under the
limit. Texture drift at the pick: 2 faces over 40 (2.8 cm²).

**Skull normals.** The installed skull's normals are softened authored normals, not plain smooth normals: a reduced
skull with plain smooth normals (and even an exactly kept one) showed a heavier brow and narrower sockets in the GLB
renders. `glb_normals.py` transfers custom normals onto the decimated cranium only (`REA_NORMAL_PIECES`) from an
**unwelded** import of the installed GLB, in the rest pose (never from the welded `source.blend`). On the jaw the
transfer dented the chin, so the jaw keeps plain smooth normals, which match the installed jaw. Elsewhere the
installed normals are plain smooth (body p90 1.4° from the reduced file's normals at shared vertices).

Close-ups: `review/glbclose/sheet_skull.png` (installed / skull 30 / 50 / 60 %, plain normals),
`sheet_normals.png` (installed / plain / full transfer, body), `sheet_src_r79_{tex,clay}.png` (body spots, renders
straight from GLBs). `review/close/` comes from the welded `source.blend`, whose clay normals are scrambled; use it
only for textured comparisons.

## Build

`export_cand.py` (Cand_84 from `work/ladder_pick.blend`) -> `swap_lod0.py` -> `build_lods.py` (the installed build's
ratios 0.5 / 0.25 / 0.125, 4 influences, its protected finger tips, soles and bow nocks from
`../mm8_m628/export/lods.json`) -> `carry_variants.py` (variants on all 7 LOD/shadow body primitives; the bow has none,
as installed) -> `check_winding.py` (0 inverted closed parts): `export/mm8_m628.glb`, 10.6 MB (installed 10.9 MB),
7 clips. Same structure as installed: two draws per LOD, one shadow primitive per level.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,067 | 5,992 | 2,885 | 1,346 |
| reduced | 10,243 | 5,066 | 2,432 | 1,112 |

`work/lod_check_{src,r84}.json`: every LOD keeps the 1.81 m height (LOD0 identical); no face stretches over 20x in any
frame of any clip; floor clearance matches installed (lowest LOD0 +0.2 mm, LOD3 -16.9 mm in Death, installed LOD3 the
same). `review/lods/sheet.png`: installed / reduced, LOD0-3, standing, attack and hands; LOD3 loses the thin bare
shin in both files.

The production motion gates (`../mm8_m628/scripts/motion_gates.py`) check the rig and clips on the master blend; this
reduction leaves the rig, clips, hands, fingers, glove, string and bow geometry and their weights unchanged (source
vertices keep exact source weights), so they were not re-run. There is no shared gate config for this creature.

Viewer: `review/viewer/` (installed vs reduced, three palettes), served from the repository root:
<http://127.0.0.1:8912/level_generation/creatures/mm8_m628_reduce_claude/review/viewer/>.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m628_reduce_claude check`: 42 switches,
no console errors.

## Status

Installed 2026-10-19 after user review ("ok") with `tools/install_model.py --world mm8`; actor regression `mm8_skeleton_archer_actor_models_keep_tiers_and_arrow_release` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install after review (from the repository root):
`python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m628_reduce_claude/export/mm8_m628.glb`,
then `OPENYAMM_REGRESSION_FILTER=mm8_skeleton_archer_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_skeleton_archer_actor_models_keep_tiers_and_arrow_release`) and add the ledger row.
Rollback: `python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m628_reduce_claude/work/mm8_m628_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=SkeletonArcher, REA_GLB=the rollback source) -> `dump_mesh.py` ->
`small_pieces.py` -> `m628_sets.py` -> `m628_keep.py work/keep_a.npy` -> (first pick, `texture_drift.py`,
`drift_lock.py work/keep_a.npy work/keep_b.npy r78`) -> regions (`work/regions_h.npy`: 1 skull, 2 jaw) ->
`REA_GROUPS=work/regions_h.npy REA_GROUP_RATIOS=1:0.6,2:0.6 REA_KEEP_FACES=work/keep_b.npy run_ladder.sh s60 0.849` ->
`REA_NORMAL_PIECES=-0.035,-0.005,1.671 REA_CAND=Cand_84 glb_normals.py -- ladder_s60c.blend <rollback glb> SkeletonArcher`
-> build as above -> `lod_check.py` (REA_NODE=SkeletonArcher), `lod_views.py`, `glb_close.py`, viewer
(`viewer_variants.py`, `viewer_manifest.py`).


## Gait rollout (2026-10-31)

Package [h21](../gait_rollout_20261031/h21/README.md) appended new in-place locomotion clips to the installed source
`assets_source/worlds/mm8/models/mm8_m628.glb` (existing clips, meshes, skins and materials byte-identical): `Walk2` (2Hand-Bow-Walk-Slow, 1.15 s, stride 1.2501) bound as walking and `WalkFast` (2Hand-Bow-Walk, 0.84 s, 1.8966) bound as run (walk-as-run kept); the installed `Walking` stays in the GLB.
Bindings are in `../gait_rollout_20261031/h21/bindings.yml` (applied by the rollout coordinator). Rebuild:
`level_generation/creatures/gait_rollout_20261031/h21/scripts/rebuild.sh m628` (from `h21/work/mm8_m628_pre_gait.glb`,
the pre-gait source), then `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_m628.glb --world mm8 --name mm8_m628.glb`. A far-LOD repair,
head-bob or reduction rerun on this model must re-graft these clips: copy its new source over the pre-gait copy and
rerun the rebuild (or graft them with `claude_shared/graft_clips.py`).
