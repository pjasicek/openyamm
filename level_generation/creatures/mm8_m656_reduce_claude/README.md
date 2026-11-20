# MM8 Human Mercenary (`m656`, Soldier of Fortune / Mercenary / Captain) reduction (2026-10-18)

User: "pick 5 more to do" (MM8 triangle-reduction batch 2, coordinated with sessions openyamm-f9, openyamm-f6 and
openyamm-b4). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the installed
textures, three palette variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m656.glb`, byte-identical to `../mm8_m656_claude/export/`
(revision `m656_equipped_v3`), copied to `work/mm8_m656_source_pre_reduce.glb` (rollback source). One merged body +
head atlas material, one `Mercenary` node, 58 joints, 4 influences, 1.69 m. The sword and scabbard
(`mm8_m656_sword.glb`, `mm8_m656_scabbard.glb`) are separate installed attachments and are not touched. Scripts are
copied from `../mm8_m624_reduce_claude/scripts/` (fixed parenting order in `reduce_ladder.py`). The weld leaves 811
open edges and no coincident vertices with other weights; no faces are lost on import.

## Where the triangles are

The m656 build already reduced the body once (`../mm8_m656_claude/scripts/reduce_rigged.py`, the `ReduceProtect`
group). Of 10,623 triangles: head atlas 3,181 (face and neck skin 1,387, helmet, horns, cheek guards and hair 1,390,
plus eyes and the painted face features), finger faces 1,301, small separate pieces 1,422 (28 skirt strips, studs,
buckles, knee bands, forearm spikes, eyes), gloves 573 and the remaining body about 4,200.

## Keep sets and groups

`scripts/face_info.py` labels faces (head atlas side, finger/hand weights, connected pieces, sampled base colour);
`scripts/merc_sets.py` builds the sets; `review/labels/` shows them.

- **Kept exactly** (`work/keep_p3.npy`, 3,726 faces): the fingers of both hands, the whole right (sword) hand,
  small pieces up to 80 faces, the painted face features (moustache, brows), a 3 cm patch around the mouth (at 60 % the
  lips took notches at the corners), and 4 cm patches (both sides) at the crotch, the lower breastplate edge and the
  back of the knees, where the first ladders failed in Death and Hit.
- **Groups**: face and neck skin 60 %, rest of the head set (helmet, horns, cheek guards, hair) 60 %, left glove 50 %;
  the body takes the rest of the ladder budget (`scripts/ladder_ratios.py` converts a body ratio into the overall one).

Limits for the 1.691 m height: p99 5.07 mm, max 25.37 mm.

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,623 | | | | |
| g1: head 75/55 %, gloves 60 %, body takes the rest | r70 | 7,435 | 6.09 / 34.1 | 0.983 | 0.982 | fail: body at 33 % |
| g2: body 83 % / 75 % | r81 / r78 | 8,677 / 8,313 | 4.07 / 23.8, 4.54 / 27.1 | | | pass / fail (crotch, chest edge in Death) |
| p2: + spot patches, skin 60 %, gloves 50 %, body 70 % | r74 | 7,949 | 4.71 / 17.3 | 0.990 | 0.989 | pass, but cut the right glove |
| p3: body 65 % | r72 | 7,737 | 5.10 / 17.4 | 0.988 | 0.987 | fail (p99) |
| p4: + right hand kept, body 67.5 % | r75 | 7,979 | 4.84 / 17.3 | 0.990 | 0.988 | pass; mouth corners notched |
| **p5: + mouth patch, body 67.5 %** | **r76** | **8,149** | 4.83 / 17.3 | 0.990 | 0.988 | **pick** |

`scripts/region_error.py` (p1 r74): the body caused 73 % of the over-limit error and the helmet group 26 %; face skin at
75 % had p99 1.1 mm, so the skin went to 60 % and the gloves to 50 %. Texture drift (`texture_drift.py r76`): 6
faces over 40 (4.2 cm2), p99 17.4.

## Normals of kept pieces (new for this creature)

The import weld merges glTF's normal-split vertices, and the ladder rebuilds every candidate smooth-shaded. The kept
skirt strips (flat boards) turned rounded and hid the green tunic between them. `scripts/kept_normals.py` sets the
candidate's custom normals from the unwelded installed GLB (never from `source.blend`): the source face's corner
normals for every unchanged source face (15,795 corners), the source vertex normal where its corners agree (3,434),
the computed smooth normal for new vertices (5,218). Close-ups: `review/glbclose/` (strips flat again, green visible).

## Build

`export_cand.py` (Cand_76 after `kept_normals.py`) -> `swap_lod0.py` -> `build_lods.py` (as the m656 project: 0.5 /
0.25 / 0.125, 4 influences) -> `../mm8_m656_claude/scripts/shrink_shadow_lods.py` (inset shadow LODs, as installed) ->
`carry_variants.py`: `export/mm8_m656.glb`, 8.3 MB (installed 8.6 MB), 8 clips; materials, skins, animations,
images, variants and node list match the installed file. Winding check: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,623 | 5,309 | 2,653 | 1,285 |
| reduced | 8,149 | 4,072 | 2,035 | 976 |

- `scripts/grip_check.py`: all 701 right-hand vertices and 473 left-finger vertices keep their bind positions (max
  0.0005 mm) and weights, so the fitted sword grip is unchanged at LOD0.
- `work/lod_check_{src,r76}.json`: bounds within 2 mm of the installed LODs; lowest point in any clip -0.1 / 0.1 /
  -3.5 / -4.4 mm at LOD0-3 (installed 2.0 / 0.2 / -3.8 / 1.1 mm); one face stretches over 20x in Death and in Running at
  LOD2 only. `review/lods/sheet.png`: all LODs standing, attack wind-up and corpse; the horns survive at LOD3.
- Viewer: `review/viewer/` (installed vs reduced, tiers A/B/C, sword and scabbard not shown);
  `tools/run_creature_review.py ... check`: 48 switches, no console errors.

## Attack vs the native sprite (not changed)

`review/attack_native/sheet.png` (native views 0 and 2 against the clip at 8 even times, rendered from
`../mm8_m656_claude/export/mm8_m656_prepared.glb`, which has the sword merged): the native attack is a high overhead
wind-up (sword behind the head, `m656ab`-`ac`), then a forward lunge with a diagonal downward cut across the body
(`ad`-`ae`), and the sword is raised again (`af`-`ah`). The 3D Attack winds up low and out to the side, then sweeps
horizontally at about head height, upright and without the lunge. Same kind of mismatch as the Couatl; the clip is
unchanged here.

## Open issues

- The saving is 23 % at LOD0: about a third of the mesh is kept exactly (fingers, the sword hand, strips, studs,
  face features) and the body was already reduced once; at body 65 % p99 fails by 0.03 mm.
- The helmet dome shows slightly more faceting in clay renders; textured it reads unchanged.

## No cheek guards and body retexture v2 (2026-10-19)

User review: "i would remove these from the helmet" (the cheek guards) "+ I would retexture the body". The previous
candidate (r76, 8,149 triangles) is kept in `work/candidate_r76/`.

- `scripts/remove_cheek_guards.py export/... work/cheekless.glb`: the guards are separate 28-face pieces (source pieces
  74/75), kept as separate pieces in every LOD. They are removed from all four colour and all four shadow meshes,
  with unused vertices dropped. The face and helmet underneath are closed surfaces: no hole, no exposed edge.
- `scripts/swap_body_textures.py work/cheekless.glb ../mm8_m656_claude/textures_v2 export/mm8_m656.glb --head`
  replaces both halves of the four atlases and the variant ramps. Geometry, skins, clips and variants are untouched.
  With the v1 texture folder it reproduces the previous atlases pixel for pixel. Texture provenance (Meshy job
  `body_retexture_v2`, 10 credits) and the cheek and rim repaint: `../mm8_m656_claude/README.md`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,623 | 5,309 | 2,653 | 1,285 |
| r76 | 8,149 | 4,072 | 2,035 | 976 |
| **v2** | **8,093** | **4,040** | **2,007** | **964** |

Checks:
- Winding: 0 inverted closed parts.
- Grip: the same 701 and 473 hand vertices as before, max 0.0005 mm.
- `work/lod_check_v2.json`: bounds, lowest points and stretched faces equal r76's.
- Viewer: 72 switches, no console errors.

Sheets: `review/retex_v2/head_cheeks.png` (installed vs new, five head views, clay) and `review/retex_v2/body_tiers.png`
(installed vs new, A/B/C). Viewer: installed, r76 and v2 for each tier.

The body texture barely changed: same flat studs, same cloth. A real improvement would need new references (clearer
studs, sharper cloth) before another retexture. The sides of the head have no modelled ears; the guards hid that.

## Raised studs, textures v3 (2026-10-19)

User choice after v2: "Add stud relief, then show me". The candidate v2 is kept in `work/candidate_v2/`.
`scripts/swap_body_textures.py work/cheekless.glb ../mm8_m656_claude/textures_v3 export/mm8_m656.glb --head` puts the
stud textures into the same no-cheek-guard mesh (texture provenance: `../mm8_m656_claude/README.md`, "Raised studs").
Only the four atlas images differ from v2: accessors, meshes, nodes, skins, clips, materials and variants are
identical. Triangles are v2's: 8,093 / 4,040 / 2,007 / 964.

- Winding: 0 inverted closed parts.
- Viewer: 96 switches, no console errors. It opens on v3; for each tier, v2, r76 and installed follow.
- `scripts/glb_close.py` gained pauldron, bracer and `chest_graze` spots (a low sun from screen left: raised studs are lit
  on the left).
- `scripts/stud_sheets.py` writes `review/studs_v3/closeups_a.png` (installed, v2, v3 in tier A: torso, back,
  pauldron, bracer, glove, boots, grazing light, head) and `review/studs_v3/tiers.png` (installed vs v3, A/B/C).

The Blender renders do not use the engine's specular mask, so the in-game highlights on the studs will be stronger
than in the sheets. Studs on UV seams and the bracer's ragged studs were not recognised and stay flat.

## Status

Installed 2026-10-19 after user review ("good approved": v3, cheek guards removed, body retexture v2 and raised studs) with
`tools/install_model.py --world mm8 level_generation/creatures/mm8_m656_reduce_claude/export/mm8_m656.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_mercenary_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_mercenary_actor_models_keep_tiers_equipment_and_simulation` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m656_source_pre_reduce.glb` with
`tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Mercenary, REA_GLB=the rollback source) -> `dump_mesh.py`, `dump_groups.py`
-> `face_info.py` -> `merc_sets.py` -> `patch_keep.py work/keep_merc.npy work/keep_p1.npy 0.017,0.0,0.638
0.136,-0.032,1.168 0.121,-0.049,1.106 0.16,0.10,0.46` -> right hand (`rhand > 0.5`) into `keep_p2.npy` ->
`REA_PATCH_R=0.03 patch_keep.py work/keep_p2.npy work/keep_p3.npy -0.007,-0.055,1.487` ->
`REA_KEEP_FACES=work/keep_p3.npy REA_GROUPS=work/groups_merc.npy REA_GROUP_RATIOS=1:0.6,2:0.6,3:0.5 run_ladder.sh p5
$(ladder_ratios.py work/keep_p3.npy work/groups_merc.npy 1:0.6,2:0.6,3:0.5 0.675)` -> `kept_normals.py -- Cand_76
work/mesh_r76.npz work/mm8_m656_source_pre_reduce.glb Mercenary` -> build as above -> `grip_check.py`,
`lod_check.py` (REA_NODE=Mercenary), `split_lods.py` + `lod_views.py`, `glb_close.py`, `viewer_variants.py`,
`viewer_manifest.py`, `attack_frames.py`.

## Head bob (2026-10-22)

The installed source of `mm8_m656` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m656` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.

## Gait rollout (2026-10-31)

The installed source `assets_source/worlds/mm8/models/mm8_m656.glb` now also carries `Sprint` (humanoid set Unarmed-Sprint, 0.58 s, stride 4.3848) for MAW's chase (7.70-8.02); walk and run unchanged.
Appended by [package h17](../gait_rollout_20261031/h17/README.md) on the installed source (existing clips, meshes, LODs
and variants byte-identical); pre-gait copy and rollback: `../gait_rollout_20261031/h17/work/mm8_m656_pre_gait.glb`.
Bindings are in `../gait_rollout_20261031/h17/bindings.yml` (applied by the rollout coordinator). Rebuild:
`../gait_rollout_20261031/h17/scripts/rebuild.sh m656`. A far-LOD repair, head-bob or reduction rerun that rewrites
this source must re-graft these clips (copy the new source over the pre-gait copy and rebuild, or
`claude_shared/graft_clips.py`).
