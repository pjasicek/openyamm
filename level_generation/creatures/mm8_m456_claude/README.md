# MM8 Dragon Hunter — m456

Created 2026-10-16 using the shared Claude humanoid and texture playbooks. Dragon Hunter, Crusader and
Dragonslayer (descriptors 43–45, palettes 457–459) share one body, eight clips and a separate left-hand serrated sword.
Installed in the game. User artistic acceptance is not recorded. The raw anatomy audit is **not a clean pass**;
read [review notes](review/ASSESSMENT.md) alongside the finished model.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m456_claude/review/viewer/)
· [outdoor](review/ingame/out_3d/t0.png) · [indoor](review/ingame/in_3d/t0.png)
· [native outdoor](review/ingame/out_sprite/t0.png)
· [placed native Crusader](review/ingame/camp_sprite.png) / [3D](review/ingame/camp_3d.png).

## Arm and pauldron repair — current revision, 2026-10-16

The user reported the free attack arm flailing and the pads sitting below the shoulders. The clavicle motion now
fits the rigid armour sockets, the free hand uses a controlled counterbalance, and the pads hinge from the upper
cuirass seam. Upper-arm straps now follow the upper arm instead of the forearm. Final twist/pad helpers are derived
from the corrected motion at 120 Hz; Hit/Fidget/Death transitions are smoothed without changing their guard endpoints.
The left sword path, blade orientation, impact timing, palette textures and knee repair are retained.

[Attack frame 22](review/arm_pad_repair/browser/Attack_22_rear.png) ·
[Running shoulders](review/arm_pad_repair/browser/Running_9_front.png) ·
[Four LODs](review/arm_pad_repair/lod_contact.png) ·
[Validation and limits](review/arm_pad_repair/validation.json).

Eight clips and four LODs pass the sleeve-root attachment check. The new pad-hinge, free-arm continuity, guard-return
and sword-path checks pass, as does the installed actor regression. The strict raw anatomy audit retains warnings;
read the current [assessment](review/ASSESSMENT.md). User artistic acceptance is not recorded.

The earlier sleeve-root repair and matching-weight LOD seam fix are retained. Its historical evidence is in
`review/shoulder_repair/`; the immediately preceding model and user screenshots are preserved in
`review/arm_pad_repair/before/`. The current revision changes animation, superseding the earlier unchanged-animation claim.

## MM6 inspiration

- `mm6_natm_claude`: source-frame rig, measured joints, source ankle paths and upright run, measured equipment.
- `mm6_bar1_claude`: sword fitting and source motion selection before modelling; upright Standard Run pelvis.
- `mm6_kni_reduce_claude`: restrained steel, native colour tiers and rigid armour pieces.

The hunter retains its own open-face crested helmet, dark steel/chain, gold edging, abdominal panel and serrated
left-hand sword. No shield, cape or spell was added. The MM8 sprite source remains unchanged.

## Selected assets

- Editable packed scene: `work/dragon_hunter_final.blend`; authoring mesh/rig: `work/master_reduced.blend`.
- Runtime sources: `export/mm8_m456.glb`, `export/mm8_m456_sword.glb`.
- Portable combined scenes with baked tier colours: `review/viewer/mm8_dragon_hunter_{a,b,c}.glb`.
- Installed source/runtime paths and exact hashes: [runtime_install.json](runtime_install.json).
- References/provenance: `references_hd/`, `references_head/`, `references_props/`; local clip hashes:
  [motion selection](references/motion_selection.json). Raw library animations were not installed or committed.
- Shared 1K body/head maps, palette masks/ramps and prop maps: `textures/`. Runtime body/head atlas is 2080×1024.
  ORM stores specular mask in R, roughness in G and zero metallic in B; tangent normal green was corrected for glTF.

59 joints, at most four weights per vertex. Body LODs: **13,275 / 7,115 / 3,304 / 1,222** triangles;
sword: **820 / 376 / 172 / 60**. Colour and shadow meshes share their fitted skeleton. Knee rows are restored after
reduction so the reduced meshes bend instead of spanning the knee with one large flat triangle.
Standing height 1.688513 m × scale 116.6104938 = native 196.898389 units (179 sprite pixels × 1.099991).
Both attack slots bind Attack; Running is a presentation clip. Gameplay stats and action timing are unchanged.

| Clip | Seconds | Source / adaptation |
|---|---:|---|
| Standing | 3 | Standard Idle; fitted sword carry |
| Walking | 1 | Walk; measured stride 1.72523 m |
| Running | 0.733333 | Standard Run; source foot paths, upright pelvis, stride 1.66942 m |
| Attack | 0.8 | SwordAttackL2; planted stance, smoothed transition, edge aligned with cut |
| Hit | 0.5 | UnarmedGetHitF1; within native 0.625 s |
| Death | 3.633333 | Standing React Death Backward; restrained translation, floor correction |
| Dead | 1 | Held final Death pose |
| Fidget | 2.833333 | Standing Taunt Battlecry; fitted carry |

Attack impact is measured at **0.385416667 s**. The blade follows its cutting edge (0.9995 edge share).
The compact pommel clears the body throughout the fall. Native gold/skin stay fixed across all three palettes.

## Production and reproduction

Meshy used **30 / 100 credits**: Smart Topology 5, rig 5, body retexture 10, head retexture 10.
Receipts and selected inputs are in `creature_3d_progress.json`. The sword is locally modelled from the generated
native-guided reference. Body/head UV transfer has zero face-centroid mismatch and zero mismatched corners.

The fitted/UV source is `work/master_uv.blend`. With the project ownership token:

1. `scripts/compose_textures.py` writes maps and native ramps.
2. Blender `scripts/finish_export.py` fits lining/crest, polishes motion and grip, reduces, and exports all clips.
3. `tools/prepare_actor_glb.py export/mm8_m456_lod0.glb export/mm8_m456_prepared.glb` fixes texture conventions.
4. Blender `scripts/build_lods.py`, then `scripts/finalize_exports.py` restore knee rows, apply variants,
   split the sword and merge head materials. `viewer_tiers.py` and `viewer_manifest.py` refresh the viewer.
5. `tools/install_model.py <export> --world mm8` for both body and sword. Never edit cooked runtime copies.
6. Run `scripts/check_arm_pads.py`, `scripts/check_shoulders.py`, `scripts/check_knees.py`, Blender `scripts/run_numeric_gates.py`, shared viewer check and affected native captures.

`refine_sword.py` and `fit_crest.py` are recorded one-time repairs to the earlier reduced checkpoint;
the normal pipeline already includes them. Do not apply those repair scripts again to the corrected master.

**Sword guard (user review 2026-10-19).** The blade started at the height of the recurved guard's tips (0.149 m) while
the guard's centre lies at 0.100-0.115 m, leaving a 4 cm hole on the centreline (and 7 mm between grip and guard).
`scripts/close_sword_guard.py work/mm8_m456_sword_pre_guard.glb export/mm8_m456_sword.glb` moves the blade's root row
to 0.108 m (inside the guard) and the grip's top row to 0.0995 m (against its underside; the `gates.json` grip region
ends at 0.1 m) in every LOD, then the sword is reinstalled. Winding 0; shared gates on the reduced body: no new or worse
row. `make_sword.py` still builds the old gap; rerun this script after it. Rollback: install
`work/mm8_m456_sword_pre_guard.glb` with `--name mm8_m456_sword.glb`.

## Validation

The ordinary development build and focused Dragon Hunter binding regression are recorded under `review/regression/`.
The test covers three skins, sword instances, native height, all eight clip durations, three reduced LODs and
simulation-state isolation. A broader actor-model run passed 63 cases and failed two MM6 cases (Demon variants and
Ooze glossy skin); each also fails when run separately with `--world mm6`. The MM7 indoor/outdoor lifecycle passed.

All 24 viewer tier/clip combinations load without console errors. Actual playback at normal and half speed,
face/hands/armour closeups and posed knee LODs are retained in `review/`. Final clearance playback covers the shortened
crest and compact pommel. Native captures used NVIDIA OpenGL 3.3 on Wayland. The MM6 indoor console-spawned sprites
were invisible, so the indoor sprite comparison uses authored Crusaders in MM8 `d16.blv` at a matching camera.

No renderer changes, Vulkan build, Android build or commit were made for this creature.

## Gait rollout (2026-10-31)

Package h16 of the [gait rollout](../gait_rollout_20261031/h16/README.md) appended two clips to the installed source
for Dragon Hunter A/B/C: `Jog` (library Unarmed-Run-Forward legs and trunk on this model's `Running` arms and sword,
0.72 s) and `Sprint` (Unarmed-Sprint, 0.60 s). Existing clips, meshes and skins are unchanged (binary prefix
identical). Installed 2026-10-31 with `tools/install_model.py --world mm8`; bindings for the coordinator
(../gait_rollout_20261031/h16/bindings.yml): run: Jog, run_stride_length: 3.2029, sprint: Sprint,
sprint_stride_length: 4.2567. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h16/review/m456_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h16/scripts/rebuild.sh
m456` (from the pre-gait copy `../gait_rollout_20261031/h16/work/mm8_m456_pre_gait.glb`). Its walk/run carry the
`head_bob_claude` fix; a far-LOD repair or head-bob rerun replaces the source without these clips: copy the new source
over that pre-gait copy and rerun the rebuild before installing. Rollback: install the pre-gait copy and drop the
bindings.
