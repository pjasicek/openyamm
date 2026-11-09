# MM8 Dragon Turtle (`m580`, Dragon Turtle A/B/C) reduction (2026-10-18)

User: "OK do those 5" (MM8 triangle-reduction batch). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md),
no-retexture variant: no part needed rebuilding, so the installed textures, the three palette variants and the shell
region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m580.glb` (identical to `mm8_m580_claude/export/`, user
approved `m580_v1`), copied to `work/mm8_m580_source_pre_reduce.glb` (rollback source). One `Turtle` node, one
material (`TurtleBody_A`, variants B/C), 18 bones, 4 influences. Scripts copied from `../mm8_m492_reduce_claude/`.

## Mesh

Weld 9,261 -> 29 open edges (the intended internal tongue sheet); no coincident vertices with other weights, no
reversed doubles (12,971 triangles before and after the weld), no small separate pieces (smallest piece 131 faces).
Faces by dominant bone (`scripts/bone_faces.py`): Head 4,760 + Jaw 1,461 (48 %), paddles 4,214, Shell 1,341,
neck/tail the rest. Limits scaled to the 1.44 m length: p99 4.32 mm, max 21.6 mm.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 12,971 | | | | |
| uniform | 70 % | 9,079 | 0.82 / 5.28 | 0.999 | 0.999 | pass |
| uniform | 55 % | 7,133 | 1.20 / 4.26 | 0.998 | 0.998 | pass |
| uniform | 45 % | 5,835 | 1.57 / 5.19 | 0.995 | 0.998 | pass; small notch on the rear paddle rim |
| uniform | 35 % | 4,539 | 2.15 / 5.19 | 0.993 | 0.996 | auto pick; teeth blunter, paddle rims notched |
| paddles 60 % | **45 %** | **5,835** | 1.68 / 5.19 | 0.996 | 0.997 | **visual pick** |
| paddles 60 % | 40 % | 5,187 | 2.04 / 4.96 | 0.995 | 0.996 | pass; teeth coarser |
| paddles 60 % | 35 % | 4,539 | 2.89 / 8.85 | 0.992 | 0.994 | pass |

Every step passes the numeric gate, so the pick is visual. The thin paddle sheets are the first to show the cut
(notched rims), so the paddle-weighted faces get their own 60 % group (`work/groups_paddle.npy`,
`REA_GROUPS`/`REA_GROUP_RATIOS=1:0.6`) and the head and shell take the rest. At 45 % the open-mouth teeth, horns,
ear fins, eyes, shell spikes and painted scute lines match the source; at 40 % and below the teeth merge.
Texture drift (`texture_drift.py`): 10 faces over 40 (2.6 cm²), no drift lock.

Shading: judge only `review/glbclose/` (straight from the GLBs, `glb_close.py`). The source column of
`review/close/` comes from the welded `source.blend`, whose custom normals the weld scrambles (fake wrinkles).
The source's genuine Meshy lumps on the head are softened a little at 45 % (`review/glbclose/sheet.png`).

## Build

`export_cand.py` (Cand_45 of `work/ladder_pad.blend`) -> `swap_lod0.py` -> `build_lods.py` (the creature's own
profile: shared 0.5 / 0.18 / 0.06, 4 influences) -> `shrink_shadow_lods.py` (copied from `mm8_m580_claude`: shadow
LOD1-3 tucked inside the surface, paddles/tail/jaw excluded) -> `carry_variants.py` (variants on all 7 LOD/shadow
primitives): `export/mm8_m580.glb`, 7.4 MB (installed 8.8 MB). Winding check: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,971 | 6,485 | 2,334 | 777 |
| reduced | 5,835 | 2,917 | 1,049 | 350 |

`work/lod_check_{src,r45}.json`: every LOD keeps the source bounds (LOD3 tail tip 1.2 cm shorter) and the same
minimum height in every clip (lowest 2.6 mm in Death/Dead, source LOD3 3.9 mm); no face stretches over 20x in any
clip at any LOD. `review/lods/sheet.png`: LOD3 at 350 triangles keeps the horns, spikes and paddles but the shell
outline is visibly faceted up close (it is the far LOD).

Viewer: `review/viewer/` (installed vs 45 %, tiers A/B/C, preview tier maps from `viewer_tiers.py`);
`tools/run_creature_review.py ... check`: 42 clip switches, no console errors.

## Status

Installed 2026-10-18 after user review ("OK") with `tools/install_model.py --world mm8 export/mm8_m580.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_dragon_turtle_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_dragon_turtle_actor_models_keep_swim_and_native_combat` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m580_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Turtle, REA_GLB=the rollback source) -> `dump_mesh.py` -> `bone_faces.py`
-> paddle groups -> `REA_GROUPS=work/groups_paddle.npy REA_GROUP_RATIOS=1:0.6 run_ladder.sh pad 0.45,0.40,0.35` ->
`close_ladder.py`, `close_sheet.py`, `texture_drift.py r45`, `glb_close.py` -> build as above -> `lod_check.py`,
`lod_views.py`, `viewer_tiers.py`.

## Floor fix — 2026-10-21

`--hover -0.017098 Death Dead`: the lowest point of the swim (0.017 m above the floor) now meets it; the idle still floats as the native sprite does. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m580.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
