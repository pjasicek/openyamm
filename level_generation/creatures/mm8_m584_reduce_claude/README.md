# MM8 Raven Man (`m584`, Raven Man A/B/C: Rook, Corbie, Raven) reduction (2026-10-18)

User: "OK do those 5" (MM8 reduction batch: ratman, m436, m584, wolf, m540). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (UVs kept, so the shared 2080 x 1024
body+head atlas, three palette variants and region ramps stay valid). No Meshy credits. Scripts copied from
[mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md) (coincident-vertex separation, exact source weights).

Source: installed `assets_source/worlds/mm8/models/mm8_m584.glb` (identical to `mm8_m584_claude/export/`), copied to
`work/mm8_m584_source_pre_reduce.glb` (rollback source). One material `Raven_A` (B/C are variants), mesh node
`Body`, 8 influences (the production rig needs them through the shoulders), double-sided material. The polearm
(1,536 triangles, separate attachment) is unchanged.

## What was protected

`import_source.py` weld: 9,302 -> 467 open edges, all 14,290 triangles kept (no reversed copies merged), no
coincident vertices with other weights. `region_masks.py` labels faces by skin weights:

- **Wings kept exactly** (4,024 faces: two closed wing cores, 36 flight feathers, 144 coverts on `Wing_`/`Feather_`
  bones). Every piece is 16-140 faces; the production LODs already keep them whole because feather shells open gaps
  under any collapse.
- **Hands and fingers kept exactly** (1,434 faces): the grip is fitted to the polearm shaft.
- **Small pieces kept** (`small_pieces.py`, up to 80 faces: eyes, studs, bra cups, buckles; 891 faces outside the
  wings).
- **Head decimated on its own at 75 %** (2,261 `B_Head` faces, `REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.75`).
- **Feet and talons at 70 %** as their own group (1,349 faces).

What is left for the main cut (torso, arms, harness, loincloth, legs) is about 5,500 faces, so the whole model
cannot go far below 80 %.

## Ladder

Limits scaled to the 1.8 m figure (p99 5.4 mm, max 27 mm; wingspan 3.7 m).

| ladder | step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---|---:|---|---|---|---|
| a | **80 %** | **11,430** | 4.71 / 16.58 | 0.997 | 0.991 | **picked** |
| a | 78 % | 11,144 | 5.44 / 16.58 | 0.997 | 0.990 | fail (p99) |
| a | 75 % | 10,714 | 7.32 / 21.02 | 0.995 | 0.989 | fail |
| a | 70 % | 10,000 | 13.68 / 61.80 | 0.988 | 0.985 | fail |
| b (+3 mm contact faces kept) | 78 / 75 / 72 % | 11,144 / 10,714 / 10,286 | 7.7-35 / 25-99 | | | fail |

At 75 % and below the skin under the bra cups and the shorts under the loincloth poke through, and the thigh and knee
guards get shards (`review/close/sheet_a.png`, `sheet_a2.png`: source / 80 / 75 / 70). Keeping the faces where two
pieces touch (`contact_keep.py`, ladder b) broke the main cut into islands and made the error much worse; dropped.
The 80 % step has no visible change at the head and beak, torso, back, arms, grip hand, loincloth, legs, talons,
wings or corpse (`review/close/sheet_r80_tex.png`; clay from the GLBs with their own normals:
`review/glbclose/sheet_clay.png`). Most of its error is a 5-10 mm smoothing of the upper arms and calves in every
frame, not a pose problem (`region_error.py`).
Texture drift: 6 faces over 40, 41 cm2 in total, on broad loincloth/thigh faces that render unchanged; no lock.
No face stretches over 20x its rest area in any frame of any clip (`stretch_check.py`).

## Build

`export_cand.py` (Cand_80, 8 influences) -> `swap_lod0.py` -> `build_lods.py` (the production settings: 0.5 / 0.25 /
0.125, 8 influences) -> `preserve_wing_lods.py` (the production step with this project's paths: the 4,024 wing
triangles go back whole into every LOD) -> `carry_variants.py` -> `prune_vertices.py` (the wing step merged the
whole LOD0 vertex set into each LOD; the unused vertices are dropped and the buffer compacted):
`export/mm8_m584.glb`, 13.9 MB (installed 14.4 MB), 6 clips, 3 variants on all 8 colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,290 | 9,394 | 6,909 | 5,384 |
| reduced | 11,430 | 8,238 | 6,276 | 5,034 |

The LODs fall less than LOD0 because the wings (4,024) stay whole in every one, as in the installed model.
`work/lod_check_{src,r80}.json`: every LOD keeps the source bounds (3.74 x 0.57 x 2.12 m), and the floor matches the
source in every clip (hover 0.55 m alive; corpse lowest -2.4 mm at LOD2 in Death, same as the installed LOD2). One
face stretches over 20x in Death/Dead at LOD1-3 and in Attack at LOD3 (the installed LOD2 has one too).
`review/lods/sheet.png` compares all LODs at rest and in Attack.

Viewer `review/viewer/` (installed vs reduced for Rook, Corbie and Raven; ramps baked for the browser from the GLB's
own region mask by `viewer_tiers.py`; the production viewer's eight-weight skinning):
`tools/run_creature_review.py --project level_generation/creatures/mm8_m584_reduce_claude check`: 36 clip switches,
no console errors.
http://127.0.0.1:8912/level_generation/creatures/mm8_m584_reduce_claude/review/viewer/

## Status

Installed 2026-10-18 (user: "ok") with `tools/install_model.py --world mm8`; `mm8_raven_man_actor_models_keep_flight_and_polearms` passes. Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Commands used:
`python3 tools/install_model.py level_generation/creatures/mm8_m584_reduce_claude/export/mm8_m584.glb --world mm8`,
then `OPENYAMM_REGRESSION_FILTER=mm8_raven_man_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_raven_man_actor_models_keep_flight_and_polearms`) and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m584_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `dump_mesh.py` (REA_PROTECT=B_Head) ->
`region_masks.py`, `small_pieces.py` -> keep = small | wings | hands (`work/keep_wh.npy`), feet group
(`work/groups_feet.npy`) -> `REA_KEEP_FACES=work/keep_wh.npy REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.75
REA_GROUPS=work/groups_feet.npy REA_GROUP_RATIOS=1:0.7 run_ladder.sh a 0.80,0.75,0.70` -> `stretch_check.py`,
`close_ladder.py`, `close_sheet.py`, `texture_drift.py` -> build as above -> `lod_check.py`, `lod_views.py`,
`glb_close.py`, `viewer_tiers.py`.

## Floor fix — 2026-10-21

`--hover -0.397589 Death Dead`: the living clips' 0.56 m hover kept the lowest living point 0.398 m (29.8 world units) above the floor; every living clip is lowered by that, and Death eases it out without taking any key under the floor (66 keys held at it). The body stands about 0.16 m up instead of 0.56 m. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m584.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
