# MM8 Wyvern — m560

> **Installed model reduced and rebuilt (2026-10-18):** the installed runtime is now the reduction from [`../mm8_m560_reduce_claude/`](../mm8_m560_reduce_claude/README.md) (LOD0 14,652 -> 9,071, teeth and dorsal spikes rebuilt, Meshy retexture, 10 credits). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m560_reduce_claude/work/mm8_m560_source_pre_reduce.glb`.


Created and installed on 2026-10-18 using the shared Claude non-humanoid playbook. The asset is ready for
review; the native indoor sprite comparison and the broad actor suite have the limitations listed below.
User artistic acceptance has not been requested or assumed.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m560_claude/review/viewer/)
· [Three native tiers](review/tiers.png)
· [Outdoor 3D / native comparison](review/outdoor_comparison.png)
· [Indoor corpses](review/runtime/indoor/model/indoor_model_corpses.png)

## Flight correction — m560_v2 (2026-10-18)

Fixed the user-reported lift at viewer frames **17–31 (48 fps)**. `ground()` previously raised the whole body
whenever a wing tip crossed the floor. Fly, Attack and Hit now use a fixed **0.405 model-unit flight clearance**,
chosen to clear their complete motion, plus the original small authored bob. Flight is higher throughout its cycle,
instead of being pushed up during each downstroke. Death descends from the same initial height and retains the
existing grounded corpse pose. The wing, neck, tail and leg motion in the airborne clips is unchanged.

The full-cycle root excursion dropped from **0.190579 to 0.017980 model units** (81.19 to 7.66 game units).
Root-curve and clip-transition assertions now catch this regression. All 461 dense samples, GLB reimport parity,
15 viewer tier/clip combinations, ten normal/quarter-speed playback combinations and the focused game regression
pass. Fixed-camera native checks cover frames 0, 17, 24, 31 and the corpse in New Sorpigal and Agar's Laboratory.
All colour/shadow LOD geometry, UVs, weights, indices, texture payloads and materials remain identical to v1.
The editable master, three viewer tiers, source GLB and cooked runtime have all been updated.

Evidence: [validation](review/flight_fix_v2/validation.json),
[before frame 24](review/flight_fix_v2/before/f24.png), [after frame 24](review/flight_fix_v2/after/f24.png),
[playback](review/flight_fix_v2/playback/playback.json), [outdoor frame 24](review/flight_fix_v2/runtime/outdoor/outdoor_f24.png),
[indoor frame 24](review/flight_fix_v2/runtime/indoor/indoor_f24.png).
Earlier comparison galleries below document v1; the correction directory contains current evidence.
No additional Meshy jobs or engine changes were needed. Android/Vulkan and the broad actor suite were not rerun.

For animation-only revisions, run `animate.py`, then `refresh_animations.py` to copy actions into the retained
UV master, followed by the export/preparation/LOD/postprocess/verification/installation sequence below.
Do not regenerate UVs or textures. The playback check retained with this revision waits for the first advancing
animation frame before sampling, avoiding a false failure during browser startup.

## Delivered asset

- `wyvern.blend`: editable 44-bone master, five actions and packed PBR maps.
- `export/mm8_m560.glb`: portable source GLB, 7.96 MB, four shared images and three palette variants.
- Installed through `tools/install_model.py`: authoritative source under
  `assets_source/worlds/mm8/models/mm8_m560.glb`, cooked runtime under
  `assets_dev/worlds/mm8/models/mm8_m560.glb` with its adjacent cooked textures.
- `assets_dev/worlds/mm8/models/actors.yml`: Wyvern A/B/C, global monster ids 121/122/123;
  skins `m560_a`, `m560_b`, `m560_c`. Other bindings are preserved.
- LOD triangles: **14,652 / 7,325 / 2,620 / 812**; four influences per vertex, one body primitive per colour LOD.
  The standard shadow LOD chain is included. Medium-quality sun shadows were visually checked without needing
  the older bat's shadow shrink correction.
- Two hind legs, two membrane wings, five neck joints, articulated jaw, nine tail joints, teeth, eyes and dorsal
  spines. No separate equipment or projectile sockets are required by the native wyvern.

## Motion and scale

| Clip | Seconds | Use |
|---|---:|---|
| Fly | 1.000 | Standing, walking, run and fidget; seamless loop |
| Attack | 1.125 | Melee/ranged/cast alias; impact at 0.833333 s, then follow-through |
| Hit | 0.875 | Native-length recoil and recovery |
| Death | 0.750 | Rear, roll and land on the side/back |
| Dead | 1.000 | Held corpse, identical to the Death endpoint |

These are locally authored interpretations of native motion, not exact sprite-frame reconstructions or Meshy
animation presets. The native attack lasts 0.875 s; its gameplay timing is retained by the impact binding.
Hit and Death retain the native durations. The native standing/walking/fidget roles share the same flight cycle.
The corpse wings lie flat; the neck and tail settle onto the floor. Default satchel gameplay still replaces the
body normally; `gameplay.corpses=keep` was used to inspect held corpses.

Scale **426** comes from mean opaque silhouette area over eight flight samples and five native viewing angles,
including the native frame scale 1.5 (`review/scale_measurement.json`). All three tiers have the same native size.
Their explicit scale avoids a dependency on unloaded cross-world sprite frames. Stride is 200/426 model units,
matching the native movement speed and one-second flight cycle. The camera-facing sprites carry a different
vertical silhouette and anchor treatment; the 3D flight phase is not synchronized to the bitmap holds.

## Texture and source provenance

The original 135 indexed BMPs and native palette ids 561/562/563 are inventoried and hashed in
`references/native_inventory.json`. The five selected Codex HD masters, exact generation prompts and receipts
are in `references_hd/`; corrected front and left views were selected before modelling.

Meshy Smart Topology produced the body. Two duplicate intersecting membrane sheets were removed; one
sheet per wing remains double-sided. Local heat weights were repaired, and wing sheets/struts were assigned to
wing chains to prevent torso/leg stretching during the death roll. Those corrections are reproducible in
`scripts/rig_wyvern.py` and recorded in `creature_3d_progress.json`.

The body uses one 2K base colour and 1K normal, material and region maps. Head/jaw UV islands receive 2.5x density;
the close face remains sharp on this small non-humanoid head without a separate material. The four-view Meshy
retexture preserved UVs: returned geometry was only uniformly scaled/recentred and reordered, with bidirectional
per-corner position/UV error below 2e-7. Maps were applied to the retained animated master.

Membrane and body ramps use corresponding pixels from the native palettes. Horns, teeth, eyes and mouth retain
separate material classes. Runtime ORM uses the shared material-class tool: red specular mask with baked AO,
green roughness and blue metallic (zero on this creature). The normal green channel is converted to glTF +Y up.
Browser GLBs bake the ramps for preview only; the installed model shares its textures across tiers.

Meshy consumption: **25 / 100 credits**: Smart Topology 5, first retexture 10, corrected four-view retexture 10.
The first texture request accidentally used an ignored image-list parameter, so only its text prompt took effect;
its output is archived, not selected. The corrected request uses documented `multiview_image_urls`.

## Verification and limits

- Ordinary `openyamm` build passed; no Vulkan build was run.
- Focused `mm8_wyvern_actor_models_keep_native_tiers_and_motion` regression passed after final binding changes.
  It checks all three ordinary monster spawns, shared model ownership, equal tier size, required chains/clips,
  and unchanged simulation state.
- All 15 viewer tier/clip combinations loaded without errors. All five clips were played at 1x and 0.25x;
  front/profile/rear/quarter, face, wing-fold and corpse views were inspected.
- 461 dense deformation samples passed finite geometry, unit bone scale, loop continuity and ground tolerance.
  Subframe penetration is below one world unit. Export/reimport surface error is below 0.000006 model units.
- Source and cooked winding checks passed; all colour/shadow LODs have valid indices, finite normals, normalized
  four-bone weights and nondegenerate triangles. Normal convention is verified. See `review/delivery_checks.json`.
- NVIDIA OpenGL 3.3 / Wayland checks in New Sorpigal and Agar's Laboratory covered all three tiers, flight,
  attacks, hit, death, held corpses and indoor forced LODs. Outdoor native sprites were captured at the same camera.
  Tight indoor views crop the broad wing span; no model collision or ceiling-conforming rig was added.
- **Native indoor comparison unavailable:** console-spawned native wyvern sprites are invisible in Agar's
  Laboratory, including after `reload map`; the three 3D actors render there correctly. Failed comparison evidence
  is retained rather than presented as a successful comparison.
- **Full actor suite not green:** 70 passes, six failures (demon variant-instance count, old ooze gloss expectation,
  and DWI/terrain scenario state), followed by `std::bad_alloc`. No general renderer/gameplay changes were made
  for these other cases. Complete log: `review/runtime/m560-actors-regression.log`.
- Android and Vulkan were not tested. User artistic review is separate from these checks.

## Reproduction

Claim this creature workspace before writing; use `tools/run_creature_blender.sh --token TOKEN` for Blender scripts
and `tools/creature_workspace.py run --project ... --token TOKEN --` for other writes.

The local sequence is `inspect_model.py`, `rig_wyvern.py`, `stress.py`, `animate.py`, `uv_export.py`, `bake_ao.py`,
`compose_textures.py`, `export_glb.py`, `tools/prepare_actor_glb.py` (LOD0 → prepared), `build_lods.py`,
`postprocess.py`, `verify_export.py`, `verify_delivery.py`, then the standard installer. Reuse the recorded Meshy
jobs and selected images; do not submit new paid jobs to reproduce the existing asset. `measure_motion.py` supplies
the dense samples. Native game tours, immutable launch settings, logs and screenshots are in `review/runtime/`.
Serve the repository root to use `review/viewer/`; its Three.js dependencies reuse the existing goblin viewer.
