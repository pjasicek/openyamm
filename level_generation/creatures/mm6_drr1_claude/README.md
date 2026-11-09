# MM6 Wyrm / Giant Wyrm / Great Wyrm

Claude quadruped playbook production, 2026-10-13. Revision 02 is runtime-installed; user artistic approval of the revision is not recorded.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm6_drr1_claude/review/viewer/)
includes all three colours, eight clips, exact-frame feedback, camera views and native references.
The viewer shows skeletal death motion and the held charred remains; surface fire is rendered by the game.

| Native descriptor | Monster ID | Skin |
|---|---:|---|
| DragonLand A / Wyrm | 511 | wyrm_a |
| DragonLand B / Giant Wyrm | 512 | wyrm_b |
| DragonLand C / Great Wyrm | 513 | wyrm_c |

## Delivered assets

- `export/mm6_wyrm.blend`: editable, packed animated master.
- `export/mm6_wyrm.glb`: four colour LODs and shadow LODs, two texture sets and shared region ramps.
- `export/mm6_wyrm_remains.glb`: grounded, black spiny remnant; its attachment is hidden during living clips.
- Sources installed through `tools/install_model.py` under `assets_source/worlds/mm6/models/`, with processed
  runtime copies under `assets_dev/worlds/mm6/models/`. Binding: `assets_dev/worlds/mm6/models/actors.yml`.
- Authoring LOD triangles: **14,413 / 7,206 / 2,592 / 862**. Runtime back-face copies make these
  **14,624 / 7,330 / 2,657 / 886**. Separate remnant: **1,048** authored triangles.
- 31 joints, maximum eight allowed skin influences. Body albedo 2K, dedicated head albedo 1K;
  normal, specular/roughness, region and burn maps 1K. No duplicate runtime textures per colour tier.

The 16,073-triangle Meshy model lost two disconnected tail scraps (58 triangles), then passed one protected
10% reduction. The next 12,972-triangle candidate visibly faceted the chest/limbs and exceeded the deformation
limits. See `review/reduction/`: matched clay views and numerical surface comparisons across all eight clips.

## Appearance and motion

The native wingless quadruped, slender neck, narrow horned head, gold underside/spines and long tail drove the
five body masters and the dedicated head close reference. Tiny digits and hidden-side anatomy are inferred;
these are appearance references, not calibrated orthographic anatomy. Source evidence remains in `../mm6_drr1/`.
Native palettes 697/696/695 supply green/blue/red ramps. The head has separate texel density and local horn,
cheek and eye masks. The native scale is 210 visible pixels × 2 / 0.432092 m = 972.0146 model scale;
B/C use the engine's native descriptor scale ratios. The viewer holds one common size for colour comparison.

Motion uses the playbook's local quadruped IK workflow, informed by the native Wyrm action strips, with rigid
jaw/teeth ownership and planted action feet. These are authored 3D adaptations, not literal bitmap pose fits.

| Clip | Seconds | Behavior |
|---|---:|---|
| Standing | 3 | Loop, restrained breathing/head/tail motion |
| Walking | 0.75 | Four-beat gait, 0.12 m stride |
| Running | 0.625 | Faster diagonal gait, 0.19 m stride |
| Attack | 1 | Head/jaw windup, impact at 0.625 s, recovery |
| Hit | 0.625 | Native duration; neck recoil and recovery |
| Fidget | 1.5 | Head turn and tail movement |
| Death | 0.875 | Native duration; rear/roll/collapse plus runtime burn |
| Dead | 1/24 | Held final state; black remnant attachment |

No separate Cast is needed by this non-caster. The Water projectile launches from `Socket_Mouth`; attack impact
is fitted to the native action clock. Burn ignition follows head/jaw and tail tip, then consumes the body.
`gameplay.corpses=keep` retains the black remnant; the ordinary default satchel policy still applies otherwise.
Zero-scale attachment visibility resets in every living clip. Export sockets are taken from a nonsingular
bind pose. Editable curves use linear interpolation matching the actual reviewed GLB samples.

## Validation and review

- Ordinary OpenGL build passed. No Vulkan rebuild.
- Focused model animation / bounds / loot unit tests: **20 passed**, 266,504 assertions.
- `checks/export_parity.json`: every clip plus dense attack samples matches the reimported export within
  **0.0075 mm**; sockets within **0.00050 mm**. All eight clips checked at 120 Hz stay above **-1.369 mm**.
  Initial death support: zero hip rise, at most 1.001 mm floor gap through 0.2 s.
  Attack hip travel range: 45 mm, with the head crossing both sides of the centreline.
- Normal-speed and quarter-speed browser playback completed for all eight clips (`review/revision02/playback/`).
  Close face/jaw, side profile and corpse views are in `review/revision02/viewer/`.
- `checks/viewer.json`: all 24 tier/clip combinations load without browser errors.
- Dedicated Wyrm binding/tiers/clips and shared burn-death regressions pass.
- Burned Wyrm remains retain loot picking with `gameplay.corpses=keep`; picking drops the vanished body
  and follows visible attachment bounds through both indoor/outdoor broad phases.
- Initial-delivery full MM6 actor suite: **58 pass, 3 fail**. Failures concern mage shared materials, guard merged materials and
  ooze specular/material expectations; these other creature assets were not changed in this project.
- Native NVIDIA/OpenGL screenshots in New Sorpigal and Agar's Laboratory use identical model/sprite cameras.
  Hostile close views exercise movement/attack/death; friendly overview runs provide clearer scale comparisons.
  Live AI chooses different poses between runs. See `review/revision02/` for current model captures and comparisons; native sprite captures remain under
  `review/ingame/`.
- Delivery hashes and installed copies are recorded in `checks/delivery.json`.

Revision 02 reran the dedicated Wyrm binding and shared burn/remains-picking regressions.
No engine code changed in this revision; the recorded 20 unit tests belong to the earlier corpse-picking fix.
Android was not tested. User artistic acceptance remains a separate review.

## Revision 02 — user feedback, 2026-10-13

Compared native front/quarter/side silhouettes with the restored `../mm6_drr1/redo_2x/sheets/` animation sheets.
The generated references widened the front stance and the Meshy geometry widened it further. Corrected the
existing 14,413-triangle master locally instead of introducing a new mesh, UV layout and skin transfer.
`review/revision02/anatomy.json` records the edit: front ankle centres went from 168 mm apart to 86 mm (49% closer),
forearm volume increased by a 1.25 radial factor, upper arms by 1.12; hind legs were tucked inward and strengthened.
UVs and topology remain exact. Existing weights were retained except a smooth lower-leg-to-paw transfer at 627
sole/ankle vertices, fixing heels that otherwise dipped through the floor during the stronger action.

Attack now shifts the hips back, tilts the body/chest and draws the head farther back to the left; release drives
forward and crosses to the right. Impact remains at 0.625 s. Death keeps planted support during the initial recoil,
then folds and falls; body grounding excludes the tail, whose chain is solved independently against the floor.
This removes the old whole-body lift caused by a low tail. Burn maps, remains and all LODs were rebuilt.

The existing mesh, textures and rig were reused; no new imagegen or Meshy jobs were needed. The preserved initial
master is `review/revision02/previous/mm6_wyrm.blend`. Revision reproduction begins with `revise_anatomy.py`,
then `anim_wyrm.py` → `finalize.py` → prepare_actor_glb → build_lods.py → bake_burn_maps.py → finish_runtime.py.
`viewer_tiers.py` refreshes previews. Restored ×2 sheets are linked directly in the viewer.

## Revision 04 — retopology and retexture, 2026-10-13 (Claude)

User request: far fewer triangles without changing features, then a crisp retexture. Pilot and method:
`../mm6_drr1_retopo_claude/` and [guidelines section 8](../../GAME_ASSET_MODELLING_GUIDELINES.md).
- Body: one continuous curvature-adaptive isotropic remesh (MeshLab, `a14`), small holes closed (the chest
  opening this mesh already had), chest junction relaxed, shrinkwrapped onto the revision-02 surface, weights by
  data transfer (max 8). Kept source pieces: tongue, eyes, cheek spikes. Teeth: 30 generated ivory cones on the
  original rows (upper on Head, lower on Jaw). Remodelling the back spines as clean cones was tried and dropped: no
  triangle saving and stumps beside the new cones.
- Triangles: LOD chain **8,801 / 4,400 / 1,581 / 524** (was 14,413 / 7,206 / 2,592 / 861); remains 1,067.
- New UVs (body 94 % + head corner for the upload; separate head set) and Meshy retextures `body_texture_v2`,
  `head_texture_v2` (20 credits) from the existing HD masters and head close reference. Compose:
  `../mm6_drr1_retopo_claude/scripts/compose_final.py` (eyes repainted, teeth ivory, horns/crest/cheeks recoloured,
  native ramps refit: mean error 0.03-0.12 8-bit levels). Master and remains: `scripts/finalize_v4.py`; then
  prepare_actor_glb → build_lods.py → bake_burn_maps.py (`--material Wyrm=body --material WyrmHead=head --ignite Head
  Jaw Tail9 Tail10`) → finish_runtime.py → install_model.py.
- Rig and all clips are the unchanged revision-02/03 actions. Previous textures and exports: `review/pre_retopo/`.
- Checks: MM6 actor suite 59 pass / 3 unrelated fails (mage, guard, ooze); Wyrm tiers/clips and burn death pass;
  viewer 24 tier/clip combinations load. Renders: `../mm6_drr1_retopo_claude/review/v4/`.
- Open for review: small gold flecks Meshy painted on the left shoulder and inner right thigh, a flat gold patch
  behind the horn roots.

## Revision 05 — holes, eyes, colour flecks, 2026-10-13 (Claude)

User review of revision 04: chest holes, smudged eyes, gold triangles on the thighs. No regeneration; whole chain:
`../mm6_drr1_retopo_claude/scripts/rebuild_wyrm.sh` (patch -> dump/AO -> compose -> finalize -> runtime -> install).
- Holes: chest junction, tail base and a small head hole closed (`patch_v5.py`; `holes_fill` had silently left them
  open). Each patch has its own texture cell painted with the revision-02 colour at that point.
- Eyes: clean ellipsoid eyeballs replace the lumpy pieces; painted iris, rim and slit pupil.
- Texture repairs in `compose_final.py`: reference repair against revision 02, per-texel 3D colour vote, and gold
  removal on the lower lateral legs (revision 02 had gold there too). 9,214 triangles.
- Still visible: a dark green diamond low on the chest plates, a small gold fleck on the left shoulder and a ragged
  gold edge at the right hip. Options: explicit 3D repaint zones, or a fresh body retexture (10 credits).

## Reproduction notes

The canonical lease/progress and paid-job receipts are in `creature_3d_progress.json`.
Meshy used 25 credits total: Smart Topology 5, body retexture 10, head retexture 10. Original returns are preserved.
Main scripts cover source inspection, rig, UVs, local clips, head UVs, AO/material composition, reduction,
final export, LODs and runtime finish. Use `tools/run_creature_blender.sh` with a current project lease for Blender
scripts and the workspace guard for other project writes. `finalize.py` reads the selected reduction, restores
body-side UV seams, refreshes packed maps, builds the charred remnant and exports the master and LOD0.
Then run prepare_actor_glb → build_lods.py → finish_runtime.py → install_model.py. Burn maps are baked from the
final LOD0 with the shared bake_burn_maps.py; region ramps combine the body/head compose outputs. Do not rerun
paid Meshy jobs to resume an export or review.

## Gait rollout: Walk2 and Run2 (2026-10-31)

[Gait rollout package q1](../gait_rollout_20261031/q1/README.md) added `Walk2` and `Run2`, shorter strides for the
slow speeds. Before:
- Great Wyrm C wandered on Walking at ×0.69.
- Its chase fell back on Walking at ×1.38, because Running would play ×0.73.

The script `../gait_rollout_20261031/q1/scripts/gait_wyrm.py` copies `scripts/anim_wyrm.py`'s gait, IK and tail
functions, with the same phases and the Remains bone at scale 0. It reads `export/mm6_wyrm.blend`.

| clip | length (24 fps) | stride | authored speed |
|---|---|---|---|
| Walk2 | 0.7917 s | 0.111 | 0.14 |
| Run2 | 0.6667 s | 0.18 | 0.27 |

The clips were grafted onto the installed source; the existing clips are byte-identical. Binding: `walking: Walk2`,
`stride_length: 0.111`, `run: Run2`, `run_stride_length: 0.18`. The gate passed: ×0.79-1.37 on every tier. The Wyrm
regressions pass.

```sh
cd ../gait_rollout_20261031/q1
blender -b --factory-startup -P scripts/gait_wyrm.py -- work/wyrm_clips.glb
python3 ../../claude_shared/graft_clips.py work/rollback/mm6_wyrm.glb work/wyrm_clips.glb export/mm6_wyrm.glb \
  --clip Walk2 --clip Run2
```

A far-LOD repair rerun (`lod_repair_claude`) must re-graft these clips.
