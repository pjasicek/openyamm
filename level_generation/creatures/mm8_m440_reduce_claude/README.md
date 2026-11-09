# MM8 Ogre Warrior (`m440`, Ogre Brawler / Warrior / Warleader) reduction (2026-10-19)

User: "OK do both" (m440 Ogre Warrior and m456 Dragon Hunter, the two heaviest unreduced MM8 models). Default route
of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: the UVs are kept, so the merged
body + head atlas, the three palette variants and the region ramps stay valid. No Meshy credits. Scripts are copied
from [mm8_m436_reduce_claude](../mm8_m436_reduce_claude/README.md) (Ogre Peasant: per-region budgets, hidden skin,
GLB close-ups), with the parenting-order fix of `mm8_m624_reduce_claude/scripts/reduce_ladder.py` (parent before the
local matrix; the m440 rig has an identity transform, so it changes nothing here).

The source is the installed `assets_source/worlds/mm8/models/mm8_m440.glb`, identical to
`mm8_m440_claude/export/mm8_m440.glb`; it is copied to `work/mm8_m440_source_pre_reduce.glb` (rollback source). One
material `M440_A` (B/C are variants), mesh node `M440`, 57 joints, 4 influences. The club
(`mm8_m440_club.glb`, 1,387 / 1,059 / 899 / 793 triangles) is a separate rigid attachment and is unchanged. The bind
height is 1.70 m: limits p99 5.1 mm, max 25.5 mm.

A Codex trial (`../mm8_m440_reduce_codex/`, 94 %, 17,626 triangles, never reviewed or installed) kept the whole head
(9,449 triangles), both hands and the existing lower LODs; it is left untouched. Its gate config matches
`mm8_m440_claude/final.gates.json`, which is used here.

## Where the triangles are

Weld 10,130 -> 1,430 open edges, 4 coincident vertices with other weights; no face stretches in any clip
(`stretch_check.py`: source 0, candidate 0). `make_groups.py` labels every face:

| part | faces | treatment |
|---|---:|---|
| face, scalp and neck skin (head texture set of the main piece) | 5,042 | 35 % |
| helmet dome and crest | 1,261 | 75 % (55 % and 40 % smeared the dome's texture and softened the brim) |
| horns | 600 | 45 % |
| the crest's ten rivets (70-faced 1.4 cm domes) | 720 | 35 % |
| mouth pieces (teeth rows, lips) | 704 | 70 % |
| eyes (2 x 150), brim rivets, tusks, studs, apron flaps (pieces up to 80 faces) | 1,837 | kept exactly |
| left hand / right hand (club grip), without the fingertips | 709 / 722 | 60 % / 75 % |
| fingertips (distal finger bones), toes, soles (below 1 cm) | 1,434 | kept exactly |
| feet above the soles | 332 | 75 % |
| armour and cloth pieces (straps, belt, shoulder plate, wrist and shin wraps) | 2,078 | 80 % |
| body skin (torso, arms, legs) | 3,313 | rest of the ladder (80 %) |

2,442 skin vertices no ray reaches in the Standing pose (under the straps, plate and wraps; `vis_mask.py`) are left
out of the ladder error. Two drift-lock rounds (`drift_lock.py`, 3 cm around faces drifting over 40 on faces over
3 cm2) keep 464 more source faces exactly, mostly on the belt, the wrist wraps and the chainmail at the back.

## Ladder

| config | triangles | p99 / max mm | IoU | SSIM | finding |
|---|---:|---|---|---|---|
| a: head 50 %, helmet 50 %, hands 55 %, gear 70 %, body 60 % | 12,910 | 6.26 / 31.9 | 0.993 | 0.990 | fails: body skin p99 13.6 mm (sparse already) |
| b: head 35 %, helmet 40 %, body 90 % | 13,430 | 3.29 / 20.6 | 0.997 | 0.995 | passes; helmet dome smear, brim softened |
| g: body 75 %, gear 70 %, feet 60 % | 11,730 | 5.79 / 24.6 | 0.993 | 0.992 | fails: body and feet |
| h: head 25 %, helmet 55 % | 11,938 | 4.19 / 20.8 | 0.996 | 0.994 | passes; brow facets in clay, helmet smear |
| **i: head 35 %, helmet 75 %, horns 45 %** | **12,678** | **4.12 / 20.8** | 0.996 | 0.994 | **picked** |

The face, helmet and rivets carried the cut; the body skin is already sparse (3,313 faces for torso, arms and legs)
and fails below 80 %. The 20.8 mm max is the upper back (`Hit` frame 3), from skinning against the swinging arm;
it is under 1 mm at rest. Texture drift of the pick: 2 faces over 40, 0.7 cm2. Close-ups of the welded candidates
(`review/close/sheet_b_*`, `sheet_h_*`) and straight from the GLBs with their own normals
(`review/glbclose/sheet_tex.png`, `sheet_clay.png`: installed / reduced, head front/side/back, both hands with the
grip, feet, torso, back, apron, the attack and the corpse) match; the brows are a little flatter in clay, the
textured face is the same.

## Build

`scripts/build_export.sh`: `export_cand.py` (Cand_67 of `work/ladder.blend` = ladder i) -> `swap_lod0.py`
(`work/r67_lod0.glb`) -> `build_lods.py` (4 influences, wrist and sole vertices protected) -> `preserve_contacts.py`
(the LOD0 right hand and both feet put back into every LOD, as in the production LOD chain, then the shadow LODs
rebuilt from the colour LODs) -> `shrink_shadow_lods.py` (the m440 project's shadow tuck, contacts excluded) ->
`carry_variants.py`: `export/mm8_m440.glb`, 7.8 MB (installed 8.6 MB), 8 clips, 3 variants on all 8 colour/shadow
meshes; materials, extras, images, nodes and clips as installed.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 18,752 | 10,649 | 6,400 | 4,238 |
| reduced | 12,678 | 7,219 | 5,032 | 3,609 |

LOD ratios 0.5 / 0.3 / 0.17 instead of the production 0.5 / 0.25 / 0.125: from the lighter LOD0 those left brown
smears on the helmet dome at LOD2 and LOD3. Without the wrist protection the 0.3 LOD2 failed the gate's right-arm
stretch (5.3-6.5 against 5) in every clip. `review/lods/sheet.png` compares all LODs standing and in the attack; the
reduced LOD3 helmet keeps a small smear, as the installed LOD3 has on the shoulder plate.

Checks:
- **Shared gate runner** (`claude_shared/gates/run_gates.sh`, config `mm8_m440_claude/final.gates.json` with the
  installed club): **PASS**, 6,618 checks, the same as the installed model (`review/gates/gates.md`,
  `review/gates_src/`).
- **LOD check** (`work/lod_check_{src,r67}.json`): every LOD keeps the installed bounds within 6 mm and the same
  lowest point per clip; no face of any LOD stretches over 20x in any clip. Death dips 6.7 mm below the floor at
  LOD0, as installed.
- **Winding:** 0 inverted closed parts.

Pre-existing, not changed: the installed Death clip dips 6.7 mm below the floor at full detail.

Viewer: `review/viewer/` shows installed (r100) and reduced (r67) for each tier, body only (the club is unchanged),
ramps baked from the GLB's own material by `viewer_tiers.py`, clips and native anchors from the m440 project
(`http://127.0.0.1:8912/level_generation/creatures/mm8_m440_reduce_claude/review/viewer/`).
`node level_generation/creatures/claude_shared/check_viewer.mjs <url>`: 48 switches, no console errors.

## Status

Installed 2026-10-19 (user: "ogre ok"); winding 0, both unit tests pass (2 cases, 70 assertions) and the row is in the
ledger. Install (from the repository root): run
`level_generation/decorations/mm8_3d/animated/scripts/check_winding.py` on the export, then
`python3 tools/install_model.py level_generation/creatures/mm8_m440_reduce_claude/export/mm8_m440.glb --world mm8`.
There is no actors-suite case for m440; build `openyamm_unit_tests` and run
`./build/tests/openyamm_unit_tests --test-case='*Ogre keeps club*,*Ogre actor bindings*'`
(`ModelAnimation mm8 Ogre keeps club motion and recovery in the cooked asset`, `mm8 Ogre actor bindings resolve
merged monster ids and the fitted club`), then add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Bindings, scale and the club are unchanged. Rollback: install `work/mm8_m440_source_pre_reduce.glb` the same way.

Reproduce:
1. `REA_NODE=M440 REA_GLB=<rollback source> blender -b -P scripts/import_source.py`
2. `REA_PROTECT=B_Head dump_mesh.py`, `dump_weights.py`, `vis_mask.py`, `make_groups.py`
3. `cp work/keep.npy work/keep_base.npy`; drift-lock rounds with `drift_lock.py` after `texture_drift.py` (base
   colour extracted to `work/basecolor.png`), then
   `REA_HIDDEN=work/hidden.npy REA_HEIGHT_M=1.70 REA_GROUP_RATIOS=1:0.35,2:0.6,3:0.75,4:0.75,5:0.75,6:0.8,7:0.45,8:0.7,9:0.35 run_groups.sh i 0.85,0.8`
4. `stretch_check.py`, `region_error.py`, `close_ladder.py`, `close_sheet.py`, `texture_drift.py`
5. `cp work/ladder_i.blend work/ladder.blend`, then `build_export.sh`
6. `REA_NODE=M440 lod_check.py`, `lod_views.py`, `glb_close.py`, the gate runner, `viewer_tiers.py` (installed r100,
   reduced r67), `viewer_manifest.py`

## Head bob (2026-10-22)

The installed source of `mm8_m440` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m440` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.

## Gait rollout (2026-10-31)

Package h19 of the [gait rollout](../gait_rollout_20261031/h19/README.md) appended new clips to the installed source
for Ogre Warrior A/B/C: `Jog` (library Unarmed-Run-Forward legs and trunk on this model's `Running` arms and club, 0.74 s) and `Sprint` (Unarmed-Sprint, 0.63 s). Existing clips, meshes and skins are unchanged (binary prefix identical). Installed 2026-10-31
with `tools/install_model.py --world mm8`; bindings for the coordinator (`../gait_rollout_20261031/h19/bindings.yml`):
run: Jog, run_stride_length: 2.7509, sprint: Sprint, sprint_stride_length: 3.5983. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h19/review/m440_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h19/scripts/rebuild.sh
m440` (from the pre-gait copy `../gait_rollout_20261031/h19/work/mm8_m440_pre_gait.glb`). A far-LOD repair, head-bob or
reduction rerun replaces the source without these clips: copy the new source over that pre-gait copy and rerun the
rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.
