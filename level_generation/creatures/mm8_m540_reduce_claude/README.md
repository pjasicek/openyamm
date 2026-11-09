# MM8 Ogre Mage (`m540`, Ogre Mage A/B/C) reduction (2026-10-18)

User: "OK do those 5" (MM8 reduction batch: ratman, m436, m584, wolf, m540). This is the default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant. UVs are kept, so the merged body/head
atlas, the three palette variants and the region ramps stay valid. No Meshy credits were used. The scripts were copied
from [mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md), which also carries the m492 coincident-vertex
handling. Production project: [mm8_m540_claude](../mm8_m540_claude/README.md).

Source: the installed `assets_source/worlds/mm8/models/mm8_m540.glb`, identical to `mm8_m540_claude/export/`.
Its `assets_dev` copy differs only by cooking. It was copied to `work/mm8_m540_source_pre_reduce.glb` as the
rollback source, and the wand to `work/mm8_m540_wand_source_pre_reduce.glb`.
- One merged material, `OgreMage_A`; B and C are variants of it.
- Mesh node `OgreMage`, 8 influences.
- The 2080x1024 atlas holds the body set at u < 0.5 and the head set at u > 0.5.
- The production build already reduced the body parts (about 73 %) and the head (12,198 -> 4,599), so the slack is
  small. This is the playbook's "already-reduced body" case.

The wand (1,499 triangles: skull, orb, grip) is left unchanged. It is a rigid prop whose grip band and skull/orb detail
the playbook keeps, so a cut would save only a few hundred triangles.

## What breaks under a cut

| try | result |
|---|---|
| head set decimated on its own at 70 % | eye and lip texture slid: one eye looks closed (`review/close/sheet_h70.png`) |
| face kept, rest of head at 55 % | the topknot strands vanished (82 mm error) |
| face kept, skull 60 %, hair 75 % | the pointed ears were cut flat (`review/close/sheet_hair.png`) |
| **head kept except hair; hair 80 %, cape 85 %** | face, ears and topknot unchanged (`review/glbclose/sheet_r77.png`) |

## Final configuration

Masks are built by `small_pieces.py`, `finger_faces.py`, `sample_lum.py` and `head_groups.py`.

Kept exactly (4,457 faces):
- the head set except the hair: face, skull, ears, neck (2,426 faces);
- finger-weighted faces (1,376);
- 15 small pieces of up to 80 faces (arm bands and straps, 580 faces);
- the faces locked by one drift-lock round.

Decimated on their own:
- the dark topknot hair: base-colour luminance under 0.18, 2,167 faces, cut to 80 %;
- the cape: faces on the Cape0-2 bones, 350 faces, cut to 85 %. At 76 % its hem moved 27 mm.

The rest of the body is cut uniformly.

Weld: 12,292 -> 784 open edges, unchanged by every step. There are no coincident vertices with other weights. Limits
are scaled to the 1.735 m bound: p99 5.2 mm, max 26.0 mm.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 13,068 | | | | |
| 80 % | 10,452 | 6.08 / 26.39 | 0.991 | 0.992 | fail (p99) |
| **77 % + drift lock** | **10,060** | 6.83 / 26.39 | 0.987 | 0.990 | **visual pick** |
| 74 % | 9,668 | 7.81 / 33.91 | 0.986 | 0.988 | fail |

### Why no step passes p99

No step passes the p99 limit. The body was already decimated, so even a 72 % cut of the free part gives about 5 mm p99.
Most of that is the ragged tunic hem, the loin and the forearm wraps. The max error comes from two sources:
- 26.4 mm at one point in `Dead` that is the same at every ratio, even with the whole head kept;
- 26.1 mm at single topknot strand tips.

The close-ups show no visible change at the 77 % step:
- `review/close/sheet_hc.png`: renders of the welded blend, source / 80 / 77 / 74. They cover topknot, collar from
  behind, cape in Running, tunic hem and belt skull, foot, cast hand, Death and corpse.
- `review/glbclose/sheet_r77.png`: the ground truth, rendered from the GLBs with their own normals. It shows face front
  and three-quarter, topknot, ear, cast hand, body front and back, cape in Running, and the hem.

The welded `source.blend` scrambles custom normals, so judge shading only from `glbclose`.

### Texture drift and stretch

Texture drift after the one lock round: 1 face over 40, 10.8 cm2.

`stretch_check.py`: the three faces that stretch over 20x in Running are the same tunic-front faces in the source and in
the candidate.

## Build

1. `export_cand.py` exports Cand_77 of `work/ladder_lock.blend` with `REA_NODE=OgreMage` and `REA_INFLUENCES=8`.
2. `swap_lod0.py` swaps it into LOD0.
3. `build_lods.py` (blender) builds the LODs:
   - It splits the head set into a temporary material and runs `build_actor_lods` at 0.5 / 0.25 / 0.125 with
     8 influences.
   - It reduces the head by bounded spatial cells of 4 / 8 / 16 mm, like `mm8_m540_claude/scripts/reduce_head_lods.py`.
     The production README says the fine face surfaces collapse under edge decimation.
   - It merges every level back into one primitive with the installed variants.
4. `compact_glb.py` and `carry_variants.py` finish the file.

Result: `export/mm8_m540.glb`, 9.3 MB (installed 10.1 MB), with 9 clips and 3 variants on all 8 colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 13,068 | 8,679 | 5,833 | 3,420 |
| reduced | 10,060 | 6,970 | 4,776 | 2,920 |

The head set takes 4,020 / 3,303 / 2,186 triangles at LOD1-3 (production: 4,442 / 3,717 / 2,364). Its maximum vertex
displacement is 2.9 / 7.3 / 16.7 mm.

`work/lod_check_{src,r77}.json`:
- Every LOD keeps the source bounds: 1.44 x 0.57 x 1.70 m, top 1.6993 / 1.6985 m as installed.
- The lowest point over all clips is -55 mm at LOD0. That is the same as the source: the folded cape below the floor in
  Death, recorded in the production README.
- LOD1 has 1-2 faces stretching over 20x in Attack/Cast/Walking/Running. The installed LOD1 has 3 in Running.
- LOD2 and LOD3 have none.

`review/lods/sheet.png` compares all LODs at rest and at the cast release.

Viewer: `review/viewer/` shows installed and reduced side by side for every tier, with the ramps baked for the browser
by `viewer_tiers.py`. The installed wand is attached to the Wand bone. `tools/run_creature_review.py ... check` made
54 tier/clip switches with no console errors. Shots of the cast release are in `review/shots/`.

## Status

Installed 2026-10-18 (user: "ok") with `tools/install_model.py --world mm8`; `mm8_ogre_mage_actor_models_keep_tiers_roles_and_wand_cast` passes. Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install:

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m540_reduce_claude/export/mm8_m540.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_ogre_mage_actor_models ./build/game/openyamm --headless-run-regression-suite actors
```

The regression is `mm8_ogre_mage_actor_models_keep_tiers_roles_and_wand_cast`. After installing, add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Rollback: install `work/mm8_m540_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

## Reproduce

1. `REA_NODE=OgreMage REA_GLB=<rollback source> import_source.py`
2. `REA_PROTECT=B_Head,B_Neck dump_mesh.py`
3. `small_pieces.py`, `finger_faces.py` (blender), `sample_lum.py`; head set `u > 0.5` -> `work/protect_head.npy`;
   then `head_groups.py`
4. `REA_KEEP_FACES=work/keep_head.npy REA_GROUPS=work/groups_hair.npy REA_GROUP_RATIOS=1:0.8,2:0.85 run_ladder.sh hc 0.80,0.77,0.74`
5. `texture_drift.py r77`, then `drift_lock.py work/keep_head.npy work/keep_lock.npy r77`, then rerun with
   `REA_KEEP_FACES=work/keep_lock.npy` and label `lock` at `0.77`
6. `stretch_check.py`, `region_error.py`, `probe_max.py`, `close_ladder.py` / `close_sheet.py`, `glb_close.py`
7. Build as above
8. `REA_NODE=OgreMage lod_check.py`, `lod_views.py`, `viewer_tiers.py <glb> <tag>`

## Head bob (2026-10-22)

The installed source of `mm8_m540` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m540` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.

## Gait rollout (2026-10-31)

Package h19 of the [gait rollout](../gait_rollout_20261031/h19/README.md) appended new clips to the installed source
for Ogre Mage A/B/C: `Walk2` (a shorter walk: humanoid-set Armed-Walk legs on this model's `Walking` arms, 0.98 s), `Jog` (Unarmed-Run-Forward on `Running`'s arms, wand and cape, 0.78 s) and `Sprint` (Unarmed-Sprint, 0.62 s); `LoinFront` follows the leading thigh by this project's rule (x1.20 + 12 deg). Existing clips, meshes and skins are unchanged (binary prefix identical). Installed 2026-10-31
with `tools/install_model.py --world mm8`; bindings for the coordinator (`../gait_rollout_20261031/h19/bindings.yml`):
walking: Walk2, stride_length: 1.3252, run: Jog, run_stride_length: 2.2798, sprint: Sprint, sprint_stride_length: 3.3136. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h19/review/m540_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h19/scripts/rebuild.sh
m540` (from the pre-gait copy `../gait_rollout_20261031/h19/work/mm8_m540_pre_gait.glb`). A far-LOD repair, head-bob or
reduction rerun replaces the source without these clips: copy the new source over that pre-gait copy and rerun the
rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.
