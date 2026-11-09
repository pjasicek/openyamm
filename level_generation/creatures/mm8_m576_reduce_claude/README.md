# MM8 Triton (`m576`, Triton A/B/C) reduction (2026-10-18)

User: "pick 5 more to do" (MM8 triangle-reduction batch 2, coordinated with sessions openyamm-f9, openyamm-b4 and
openyamm-f6). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part
needed rebuilding, so the installed textures (padded 4096x2048 body + head atlas, `mm8_m576.cook.yml`), palette
variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m576.glb`, byte-identical to `../mm8_m576_claude/export/`
(texture correction of 2026-10-18 on the accepted spear-lunge attack); the runtime copy has the same eight clips
(not stale). Copied to `work/mm8_m576_source_pre_reduce.glb` (rollback source; the cook sidecar beside it). One
`Triton` node, one material `Triton_A` (+ B/C variants), 59 joints, 4 influences. The trident
(`mm8_m576_trident.glb`, 632 / 316 / 176 / 98) is a separate attachment and is not changed; `export/` holds an
unchanged copy for the gate runner. Scripts are copied from `../mm8_m624_reduce_claude/scripts/` (fixed parenting
order in `reduce_ladder.py`); shading was judged only from renders of the GLBs themselves (`glb_close.py`).

## Keep sets and groups

Import: weld 6,992 -> 32 open edges, no coincident vertices with other weights, no two-sided sheets (10,656 tris).
`triton_classes.py` labels pieces and regions: body 7,000 (head skin 2,017, hands 1,126 + 1,129, feet 485), crest
1,000, collar 650, pauldrons 448 + 450, shoulder guards 2 x 250, four harness straps 4 x 100, buckle 8, eyes 2 x 100.

- **Kept exactly** (`work/keep_d.npy`, 2,716 faces): the left gripping hand and fingers (trident grip), eyes, the
  four thin harness straps and the buckle, the sole band (foot faces in the lowest 6 cm), the mouth (365 face-skin
  faces around lips and corner fangs: a uniform cut smoothed the fangs away), one drift-lock round
  (`drift_lock.py`, 1.5 cm radius) and a 3 cm patch at the back of each calf (`patch_keep.py`; a reduced calf vertex
  sank 6 mm below the floor in the Death fall).
- **Collar** decimated on its own at 85 % (`groups_collar.npy`): in the shared cut its back rim folded into a dark
  crease.
- Protecting the head skin at 80 % or giving crest / right hand their own ratios moved the error onto the limbs (the
  body below the head is already light: ~2,700 tris), so everything else shares one cut.

## Ladder

Limits for the 1.723 m height: p99 5.17 mm, max 25.85 mm.

| config | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| k: hand, eyes, straps, soles kept | 60 % | 6,392 | 4.74 / 22.56 | 0.985 | 0.989 | pass; fangs lost, collar back crease |
| p: + head skin at 80 % | 65 % | 6,924 | 5.30 / 22.56 | 0.983 | 0.987 | fail |
| kb: k + mouth | 60 % | 6,392 | 5.16 / 22.56 | 0.983 | 0.988 | pass; collar back crease |
| kc: kb + collar 85 % | 63 % | 6,712 | 5.13 / 22.56 | 0.984 | 0.988 | pass; drift 14 faces / 73 cm2 |
| kd: kc + drift lock | 65 % | 6,926 | 5.10 / 22.56 | 0.984 | 0.989 | pass; LOD0 6 mm below floor in Death |
| **ke: kd + calf patches** | **64 %** | **6,818** | 5.05 / 22.56 | 0.984 | 0.989 | **pick**: drift 2 faces / 5.5 cm2 |

Close-ups from the GLBs (`review/glbclose/sheet_tex.png`, `sheet_clay.png`, installed / 64 %): face, mouth fangs,
crest, ears, collar, pauldrons, straps, both hands, legs, back and the attack pose match the installed model; a few
small dark specks remain on the collar top at the back of the neck.

## LODs

`build_lods.py` (`tools/build_actor_lods.py` with protected points, like `../mm8_m576_claude/scripts/build_lods.py`):
the whole left gripping hand, the sole band (lowest 12 mm per foot; 6 mm let the LOD3 left foot fail the running
foot-yaw gate), the Dead-pose floor contact (34 vertices; LOD3 floated 2.1 cm without them) and the top 3 cm of the
crest spike (LOD3 lost 5.4 cm of height without it). Ratios 0.5 / 0.375 / 0.275 of the new LOD0, inside the gate
caps of `gates.json` (0.51 / 0.38 / 0.28); the installed LOD1-3 (`REA_KEEP_LODS=1`) would break those caps against
the smaller LOD0, so they are rebuilt. Protecting the right hand as well starved LOD2/3 (LOD3 head collapsed to one
spike) and was not needed: the gates pass without it. Then the creature's `shrink_shadow_lods.py` (shadow LOD1-3
inside the surface) and `carry_variants.py` (variants on all 8 colour/shadow meshes). Winding check: 0 inverted.
`export/mm8_m576.glb` 12.9 MB (installed 13.6 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,656 | 5,327 | 3,889 | 2,811 |
| reduced | 6,818 | 3,407 | 2,554 | 1,873 |

- `review/full_gates/gates.md` (shared gate runner, `gates.json` copied from the creature project): **PASS**,
  {'PASS': 6474, 'INFO': 140, 'N/A': 68}, the same counts as the installed model: trident grip contacts, hands,
  soles, foot yaw, posture and LOD ratios on every clip and every colour/shadow LOD.
- `work/lod_check_r64.json` vs `work/lod_check_src.json`: every LOD keeps the 1.703 m height and the bounds; the
  corpse lies on the floor at every LOD (1 mm); lowest point in any clip -7.1 mm at LOD3 (installed LOD3 -6.4 mm);
  the one stretched face in Attack/Death/Hit at LOD1-2 is also in the installed LOD1-3.
- `review/lods/sheet.png` (installed / reduced per LOD: three-quarter, attack, head). LOD3's crest spike is a broad
  wedge instead of the installed thin horn (protected tip, collapsed base); it reads correctly at that distance.

## Attack vs native

The native attack (`../mm8_m576_claude/references_native/attack_side.png`) lifts the trident overhead and stabs down
into the ground in front. The installed Attack is an underhand forward lunge with a forward grip: a deliberate
deviation the user requested and accepted (`../mm8_m576_claude/README.md`, Motion). Not changed here.

## Viewer

`review/viewer/` (installed vs 64 % for Triton A/B/C, region ramps baked; the trident is not shown):
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m576_reduce_claude check`:
48 switches, no console errors.

## Status

Installed 2026-10-18 after user review ("triton ok") with `tools/install_model.py --world mm8 export/mm8_m576.glb` (the `mm8_m576.cook.yml` sidecar is unchanged).
`OPENYAMM_REGRESSION_FILTER=mm8_triton_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_triton_actor_models_keep_tiers_trident_and_simulation` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m576_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Triton, REA_GLB=the rollback source) -> `dump_groups.py` ->
`REA_PROTECT=B_Head,B_Jaw dump_mesh.py` -> `triton_classes.py` -> `triton_sets.py a` -> `mouth_keep.py`
-> `kc` ladder -> `texture_drift.py r63` -> `REA_LOCK_R=0.015 drift_lock.py work/keep_b.npy work/keep_c.npy r63` ->
`REA_PATCH_R=0.03 patch_keep.py work/keep_c.npy work/keep_d.npy -0.1518,0.1196,0.3694` ->
`REA_KEEP_FACES=work/keep_d.npy REA_GROUPS=work/groups_collar.npy REA_GROUP_RATIOS=3:0.85 run_ladder.sh ke 0.66,0.65,0.64`
-> `cand_glb.sh ke 64` -> `build_lods.py` -> `shrink_shadow_lods.py work/ke_r64_lods_raw.glb export/mm8_m576.glb` ->
`carry_variants.py` -> `../claude_shared/gates/run_gates.sh export/mm8_m576.glb --config gates.json --out review/full_gates`
-> `REA_NODE=Triton lod_check.py`, `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_manifest.py`.
