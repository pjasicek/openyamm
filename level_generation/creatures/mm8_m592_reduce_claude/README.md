# MM8 Plane Guardian (`m592`, Plane / Chaos Guardian, Protector, Overlord) reduction (2026-10-19)

This follows the default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons,
without a retexture. The scripts come from
[mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md): the ladder, floor-contact LOD lock, tier viewer and
retexture check. Further pieces:
- from [mm8_m476_reduce_claude](../mm8_m476_reduce_claude/README.md): `reduce_ladder.py` with exact source weights, the
  parent fix and UV-based weights (`uv_weights.py`, `REA_WEIGHTS=component`);
- from [mm8_m604_reduce_claude](../mm8_m604_reduce_claude/README.md): `face_bones.py`, the per-region groups, bounding
  extremes locked in the LODs, and `region_error.py`;
- from [mm8_m592_claude](../mm8_m592_claude/README.md): `shrink_shadow_lods.py` and `fix_lod_winding.py`.

No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m592.glb`, identical to `mm8_m592_claude/export/`. It is
copied to `work/mm8_m592_source_pre_reduce.glb` as the rollback source. It has:
- one material (`PlaneGuardian_A`, variants B/C), with its 1K body and head maps merged into a 2080x1024 atlas;
- a region mask with the mane in R;
- a specular mask in the metal-rough map's red channel (eyes, teeth, gums, claws);
- the mesh node `PlaneGuardian`, 4 influences, 9 clips, and no attachments or effect meshes.

## Ladder

The weld goes from 7,346 to 182 open edges. There are no coincident vertices with other weights and no triangles are
lost on import. The mesh is one 10,654-face body plus 54 small pieces (mane tufts on the crown, loose fangs; 342 faces).
The body is already economical: the whole torso is 1,576 faces. Most of the faces sit in the head and jaw (3,258)
and in the six claws (about 240 faces each). Limits are scaled to the 1.70 m height: p99 5.1 mm, max 25.5 mm.

`scripts/make_groups.py` sets the budgets:
- **kept exactly (1,630):** small pieces; head and jaw faces the specular mask marks as shiny (eyes, teeth, gums), plus
  one ring of neighbours; soles (below 4 cm);
- **groups:** head and jaw skin (1,964), claws (shiny finger faces, 1,375), hands (palms and claw bases, 1,185), feet
  (572), and the body taking the rest of the ladder budget.

| ladder | groups (head / claws / hands / feet) | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,996 | | | | |
| g1, nearest-face weights | 75 / 60 (claws in hands) / – / – | 8,244 | 8.65 / 49.4 | 0.992 | 0.982 | fail |
| k1, kept faces only | – | 8,796 (80 %) | 4.67 / 29.7 | 0.995 | 0.994 | fail (max) |
| g3, UV weights | 60 / 50 / 55 / 60 | 8,758 (80 %) | 5.66 / 16.5 | 0.995 | 0.994 | fail (p99) |
| g4 | 70 / 60 / 75 / 80 | 9,014 (82 %) | 4.22 / 21.1 | 0.996 | 0.994 | pass |
| g6 | 60 / 50 / 75 / 80 | 8,794 (80 %) | 4.50 / 18.6 | 0.995 | 0.995 | pass |
| **g6** | **60 / 50 / 75 / 80** | **8,574 (78 %)** | **4.98 / 21.1** | **0.995** | **0.994** | **pick** (lowest passing) |
| g7 | 50 / 45 / 75 / 80 | 8,462 (77 %) | 5.37 / 21.1 | 0.994 | 0.994 | fail (p99) |

- **What sets the limit:** the body and the feet. `region_error.py` puts most of the points over 5 mm on the feet,
  hands and head when those go to 55-60 %, and on the back and calves when the body goes below about 80 %. The
  hunched back and running legs reach 30-60 mm misses in Running below 78 %.
- **Lighter head and claws (g7)** frees body budget, but the p99 still rises.
- **UV-based weights** replace the nearest-face transfer. They cut the max error at the same step, because the mane
  tufts and dental arches sit close to other surfaces.
- **Close-ups** (`review/close/sheet_g6_a.png`: attack head, open mouth, hand claws, toe claws;
  `sheet_g6_b.png`: whole body front, side and back, mane, corpse; columns source / 80 / 78):
  - teeth, gums and eyes are unchanged (kept);
  - claws and toes keep their shape;
  - mane strands and body read the same textured.

  The source column's clay shading comes from the welded `source.blend`, so it is not used for judging normals.
- **Texture drift at 78 %:** 1 face over 40 (4.9 cm2, back of the mane). No drift lock.

## Build

The chain is:
1. `export_cand.py` (REA_NODE=PlaneGuardian, Cand_78);
2. `swap_lod0.py`;
3. `floor_contacts.py` (Death/Dead, 59 points);
4. `build_lods.py` (0.5 / 0.25 / 0.125 and 4 influences, as the m592 project; floor contacts and 190 vertices within
   2 cm of each bounding extreme protected);
5. `shrink_shadow_lods.py` (2 / 4 / 7 mm inset, as installed);
6. `fix_lod_winding.py` (no repairs needed);
7. `carry_variants.py`.

The result is `export/mm8_m592.glb` at 7.3 MB (installed: 7.8 MB). It has 9 clips and 3 variants on all 8 colour and
shadow meshes. The materials, nodes, skins, animations and image bytes are unchanged.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,996 | 5,476 | 2,724 | 1,350 |
| reduced | **8,574** | 4,263 | 2,117 | 1,043 |

`lod_check.py` (`work/lod_check_{src,r78}.json`):
- **Bounds:** every LOD keeps the LOD0 bounds (height 1.700 m, arm span 2.12 m). The installed LOD1-3 lost up to
  3 cm of height.
- **Floor:** Death, Dead, Standing and Attack keep the source's lowest points (-0.6 / +0.4 / +0.4 / -0.2 mm) at
  every LOD. Walking and Running sink 0.6-0.7 mm deeper than the source at LOD0 (-9.5 / -11.3 mm against -8.9 /
  -10.6 mm; the source's own heel-down contact) and are shallower than installed at LOD1-3.
- **Stretched faces:** LOD0 has the same 4 stretched faces as the source, LOD1 has 1, and LOD2/3 have none.
- **Winding:** `check_winding.py` finds 0 inverted closed parts.

`review/lods/sheet.png` compares installed and reduced at every LOD (standing, attack, corpse).

## Retexture check

**Verdict: no retexture needed.** No local fix was applied and no credits were spent.

- **Normals:** clay renders straight from the GLBs (`review/retexture/sheet_head.png`, `sheet_body.png`, clay
  columns) show that the installed model shades smooth, and so does the reduction.
- **Head and body, per tier:** face, eyes, teeth, gums, open mouth, mane, flanks, chest, hands, claws, feet and back
  match the installed model in gold, green and red.
- **A pre-existing mane-mask fleck, left as is:** 14 chest faces under the beard tips carry a partial mane mask, so 3-4
  small mane-coloured flecks show in the chest crease from below (`review/retexture/*_belly_tex.png`), as in the
  installed model. Clearing the mask there exposed the gold hair strokes in the base colour. Filling the base colour
  instead turned the small spiky beard-tip faces into flat grey patches, which looked worse. Both attempts are in
  `work/maskfix_rejected/` (`scripts/mask_fix.py`); the export keeps the installed textures byte for byte.

## Viewer

`review/viewer/` has three tiers, installed and 78 % for each. The region ramps are baked per tier by
`viewer_variants.py`, and the native reference frames come from the m592 project.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m592_reduce_claude check`: 54 clip
switches, no console errors.

## Status

Installed 2026-10-19 (user: "plane guardian ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_plane_guardian ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_plane_guardian_actor_models_keep_tiers_scale_and_claw_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m592_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `import_source.py` (REA_NODE=PlaneGuardian, REA_GLB=the rollback source);
2. `dump_mesh.py`, `face_bones.py`, `dump_weights.py`;
3. `make_groups.py` (needs `work/img1.png`, the metal-rough map extracted from the GLB);
4. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.6,2:0.5,3:0.75,4:0.8 run_ladder.sh g6 0.80,0.78`;
5. `region_error.py`, `probe_max.py`, `close_ladder.py -- ladder_g6.blend Cand_80,Cand_78`, `close_sheet.py`,
   `texture_drift.py r78`;
6. build as above;
7. `lod_check.py` (REA_NODE=PlaneGuardian) and `lod_views.py`;
8. `viewer_variants.py`, then `retex_views.py` (RETEX_HEAD=B_Head RETEX_SPOTS=biped) and `retex_sheet.py`.

## Floor fix — 2026-10-21

`--ground-loop Walking`: the walk lifted every foot up to 0.019 m off the floor at 21 of 49 keys. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m592.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.

## Gait rollout (2026-10-31): Walk2, Jog, Sprint

Package [h22](../gait_rollout_20261031/h22/README.md) appended three locomotion clips to the installed source; every
other clip, mesh and skin is unchanged. `Walk2` (0.70 s, stride 1.0813) and `Jog` (0.62 s, 1.9098) take the legs from
this model's own `Walking` and `Running`; `Sprint` (0.52 s, 3.2502) from the humanoid set's Unarmed-Sprint, fitted to
the Guardian's back-set ankles and bow legs. Arms, claws and jaw come from `Walking` / `Running`. Bindings for all six
descriptors (`walking: Walk2`, `run: Jog`, `sprint: Sprint` and their strides) are in the package's `bindings.yml`;
`Walking` and `Running` are no longer bound for locomotion. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h22/scripts/rebuild.sh m592`. A far-LOD repair, floor fix or any
re-export of this model must re-graft these clips (copy the new source over the package's
`work/mm8_m592_pre_gait.glb` and rebuild).
