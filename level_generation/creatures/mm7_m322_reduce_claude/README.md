# MM7 Peasant Elf Female (`m322`, descriptors 331-339) reduction (2026-10-20)

User: "OK reduce tris count now" (the five MM7 batch-J peasants; this project is m322 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine palette looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy
credits. **Not installed** (batch J: the user installs later).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m322_reduce_claude/review/viewer/) (source vs
reduced, all nine looks, six clips, the staff on its joint)

## Source

`../mm7_m322_claude/export/mm7_m322.glb` and `mm7_m322_staff.glb` (after the 2026-10-20 walk fix: Mixamo Standard
Walk), copied byte for byte to `work/mm7_m322_source_pre_reduce.glb` and `work/mm7_m322_staff_source_pre_reduce.glb`
(rollback sources). One merged body + head atlas material per look (`Elf_A1`…`Elf_C3`, 2080x1024), node `Elf`, clips
Standing, Walking, Hit, Death, Dead, Fidget. Bind height 1.75 m (ladder limits p99 5.25 mm, max 26.25 mm; IoU >= 0.98,
SSIM >= 0.93). Weld (identical weights only): 6,602 -> 232 open edges, no coincident vertices with other weights,
11,188 triangles in and out. Scripts start from `../mm7_m410_reduce_claude/scripts/` (paths, node `Elf`, height).

## Where the triangles are (`scripts/dump_prod_pieces.py` + `scripts/m322_pieces.py`, `review/labels_pieces.png`)

The production master's Smart Topology shells (`../mm7_m322_claude/work/rig_v6.blend` 'piece', mapped by rest
position, max 0.0008 mm); its one skin shell (body, head, vest, trousers, bracers, boots) split by bone weights, the
region mask (R trousers) and the base colour:

| piece | faces | |
|---|---:|---|
| head skin | 2,702 | 849 visible face front |
| hands | 2,112 | kept exactly (the left fist's solved staff grip) |
| hair | 1,300 | |
| skin rest (arms, shoulders, back, belly, the trousers' open side lacing) | 1,229 | |
| vest lacing, studs, trouser grommets (40 small pieces) | 1,142 | kept exactly |
| trousers | 1,085 | |
| boots | 713 | |
| vest | 471 | |
| eyes and mouth bits | 434 | kept exactly |

## Keep set and groups (`scripts/m322_sets.py` + patches, pick = set `m`)

Kept exactly (`work/keep_m.npy`, 6,215 faces): both hands (every face touching a vertex with hand + finger weight >
0.3), eyes and mouth, every small piece (vest lacing, studs, grommets), the visible face front, the trousers' open side
lacing strips (skin-shell faces on the legs outside the trousers mask: painted laces) and the trouser faces on the mask
border, grown by one face ring (`RING=1`: at set c a trouser collapse beside the strip dragged a pale lacing texel onto
the right shin), the wrist and bracer edges (`patch_keep.py`, 5.5 cm at both wrists and both bracer tops: a notch at
the right bracer's wrist edge and a jag at its top otherwise), one drift lock (`drift_lock.py`, 2 cm) and the boots
whole (the second boot cuff drifted 5.8 cm2 after the lock).

| group | faces | ratio |
|---|---:|---|
| 1 visible head sides (ears, temples, hairline) | 900 | 60 % |
| 2 hidden head skin (under the hair) | 953 | 50 % (35 %: p99 15 mm) |
| 3 hair | 1,300 | 60 % |
| 4 trousers | 699 | 60 % |
| 6 vest | 391 | 75 % |
| 0 free (arms, shoulders, back, belly) | 730 | 66 % (50 %: p99 10.6 mm) |

## Ladder (`scripts/run_ladder.sh`; `review/ladder_sheet_<set>.png`)

| set | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 11,188 | | | | |
| a: base, free 70-50 % | r80-r78 | 9,030-8,804 | 4.05-4.80 / 12.6-23.4 | 0.994-0.991 | 0.998-0.997 | pass |
| b: hidden head 35 %, boots 50 %, free 50-30 % | r74-r72 | 8,310-8,088 | 8.7-13.0 / 23-59 | 0.989-0.961 | | fail |
| c: hidden head 50 %, boots 65 % | r78 / r77 | 8,742 / 8,630 | 4.30 / 4.76 | 0.992 / 0.990 | 0.997 | pass; pale fleck on the right shin, faceted upper arms |
| d: + lacing ring | r79 | 8,942 | 3.99 / 14.8 | 0.992 | 0.997 | pass; notch at the right wrist edge |
| e: harder hair/trousers/vest | r78 | 8,726 | 4.67 / 33.4 | | | fail (max, Death) |
| g: + wrist patches | r80 | 8,960 | 4.24 / 14.8 | 0.992 | 0.997 | pass; jag at the right bracer top |
| h2: + bracer-top patches, free 75 % | r81 | 9,092 | 4.04 / 14.8 | 0.994 | 0.997 | pass; 28 dark-sliver faces (two 3-7 cm2 on the boot cuffs) |
| k: + drift lock | r81 | 9,136 | 4.15 / 18.4 | 0.994 | 0.998 | pass; one boot-cuff face drifted 5.8 cm2 |
| **m: + boots kept** | **r82** | **9,202** | **3.88 / 22.8** | **0.993** | **0.998** | **pick** |

The pick is the lowest configuration that passes the ladder and shows no visible change in the close-ups. The 22.8 mm
maximum is at Hit frame 6 (limit 26.25). Texture drift (`texture_drift.py`, `drift_visible.py m_r82`): 2 faces over 40
(1.3 cm2), none over 3 cm2. Dark slivers (`dark_slivers.py`, from `../mm7_m174_reduce_claude/`): 17 faces, each under
1 cm2. Slivers (`sliver_vis.sh m_r82`): 28 new thin faces (2.5-6 cm long, 2.6-4 mm high) against the source's 55;
the textured and clay close-ups show none of them.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh m Cand_82 kn` (source normals on unchanged faces and kept vertices) -> `work/m82_lod0.glb`
-> `REA_CAP_Z=1.70 cap_points.py` (13 hair-top points) and `REA_NODE=Elf floor_points.py` (24 Dead/Death floor contacts)
-> `REA_LOD_RATIOS=0.5,0.21,0.068 build_lods.py` (`tools/build_actor_lods.py`, 37 protected points) ->
`shrink_shadow_lods.py` (shadow LODs inset up to 15 mm) -> `carry_variants.py` (7 primitives) ->
`../mm7_m322_claude/scripts/clamp_lod_uv.py` (nothing to clamp) -> `check_winding.py` (0 inverted closed parts):
`export/mm7_m322.glb`, 6.43 MB (source 6.66 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 11,188 | 5,593 | 1,978 | 634 |
| reduced body | **9,202** | **4,600** | **1,897** | **588** |
| staff (`export/mm7_m322_staff.glb`, byte-identical copy) | 1,160 | 580 | 208 | 68 |

Checks:
- `scripts/compare_glb.py`: nodes, skin, materials and extras, images, all six clips and the variants extension
  identical to the source; `KHR_materials_variants` (nine looks) on all 8 colour/shadow primitives. `DIFFERENCES none`.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,578 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0008 mm) and weights exactly, so the staff grip is unchanged.
- `scripts/lod_check.py`: every LOD keeps the 1.75 m top (1.7508 / 1.7508 / 1.7515 / 1.7508) and the source's bounds;
  the lowest point per clip is within 1-4 mm of the source's at every LOD (Dead -0.4 cm at LOD3 vs -0.15); no face
  stretches over 20x in any clip at any LOD.
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_m82_upper.png` (face, hair, torso, vest back, hands, forearms) and `sheet_m82_lower.png`
  (left forearm, side lacing, shins, boots, Walking, Hit, Dead); earlier steps in `sheet_c77_*`, `sheet_d79_*`,
  `sheet_f79.png`, `sheet_g80_wrists.png`, `sheet_g80_h81.png`.
- Viewer: `review/viewer/` (source vs 82 % pick, nine looks with the ramps baked by `viewer_variants.py`, the staff added
  under the `Sword` joint for review only by `viewer_staff.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m322_reduce_claude check`: 108 switches, no console errors; shots in other looks
  `review/viewer_tiers_sheet.png`.

## Open points for review

- The cut is modest (-17.8 %): more than half of the mesh is kept exactly (hands 2,112 for the fitted staff grip, the
  face front, 40 small pieces, the painted side lacing, boots). The source was already reduced once in its build
  (15.9k -> 11.2k with head and hands protected).
- The staff is unchanged (1,160 triangles; a 10-sided lathe, little to gain).
- Inherited from the source (unchanged): the shoulder skin's texture patches; the staff's small contacts listed in
  `../mm7_m322_claude/README.md`.

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m322_reduce_claude/export/mm7_m322.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m322_reduce_claude/export/mm7_m322_staff.glb --world mm7
```

then the binding from `../mm7_m322_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m322_source_pre_reduce.glb` (+
`work/mm7_m322_staff_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=level_generation/creatures/mm7_m322_reduce_claude/work/mm7_m322_source_pre_reduce.glb REA_NODE=Elf
import_source.py` -> `dump_mesh.py`, `dump_groups.py`, `extract_basecolor.py work/mm7_m322_source_pre_reduce.glb` ->
`dump_prod_pieces.py ../mm7_m322_claude/work/rig_v6.blend` -> `m322_pieces.py` -> `REA_MIN_PIX=6 visibility.py 1.40 1.76`
(copy to `work/visible_head.npy`) -> `REA_PATCH_R=0.055 patch_keep.py - work/patch_wrist.npy 0.355,0.003,0.956
-0.359,0.001,0.951` -> `REA_PATCH_R=0.055 patch_keep.py work/patch_wrist.npy work/patch_bracer.npy 0.287,0.036,1.123
-0.29,0.032,1.124` -> `RING=1 M322_EXTRA_KEEP=work/patch_bracer.npy m322_sets.py h` -> `run_ladder.sh h2 h
"1:0.6,2:0.5,3:0.6,4:0.6,5:0.65,6:0.75" 0.75,0.68` -> `dark_slivers.py h2_r81` -> `REA_LOCK_R=0.02 drift_lock.py
work/keep_h.npy work/keep_k.npy h2_r81` -> keep_m = keep_k | boots (piece 5), groups_m = groups_h with kept faces 0 ->
`run_ladder.sh m m "1:0.6,2:0.5,3:0.6,4:0.6,6:0.75" 0.72,0.66` -> build as above (`REA_HEIGHT_M=1.75` for the ladder).
Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`).

## Installed (2026-10-20)

User: "OK accept all, to assets_source, assets_dev". `check_winding.py` 0 inverted closed parts; installed with
`tools/install_model.py ... --world mm7` (sources in `assets_source/worlds/mm7/models/` equal the exports; cooked
runtime copies in `assets_dev/worlds/mm7/models/`). Nine `actors.yml` bindings added to
`assets_dev/worlds/mm7/models/actors.yml` from the production README's template (descriptor -> palette -> skin from
`../mm7_m322/variants.json` and the ramps file); every skin, clip, look node and attachment checked against both GLBs.
Boot check: `7out02.odm` (Harmondale) with spawned peasants of all five batch J models, 185 outdoor actors textured,
no missing models and no errors in the log (`output/batchJ_boot/`). Ledger row added to `../REDUCTION_LEDGER.md`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Standing sinks to -2.8; dying sinks to -2.5.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m322.glb export/mm7_m322.glb --lift-joints Dead Death Standing --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Standing --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m322.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h13](../gait_rollout_20261031/h13/README.md) appended one clip to the installed source
`assets_source/worlds/mm7/models/mm7_m322.glb` (every existing clip, mesh, skin and material byte-identical): `Jog`
(humanoid set Unarmed-Run-Forward legs; arms from Walking; 0.76 s), bound for the peasants' flight (Wimps flee at 2x Spd in both rulesets) as `run: Jog`,
`run_stride_length: 2.4487` (the package's `bindings.yml`, applied by the coordinator). The staff keeps its world-upright carry (the package composer's `upright_props`).
Rebuild: `level_generation/creatures/gait_rollout_20261031/h13/scripts/rebuild.sh m322`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h13/export/mm7_m322.glb --world mm7
--name mm7_m322.glb`. A far-LOD repair, head-bob or reduction rerun that re-exports this model must re-graft the Jog: copy
the new source over `h13/work/mm7_m322_pre_gait.glb` and rerun the rebuild.
