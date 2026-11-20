# MM6 Genie / Djinn / Efreet — Claude production v1

Native family `mm6:djn`; descriptors **544 / 545 / 546**, `BGenie A/B/C`, palettes **739 / 740 / 741**.
Created with the shared Claude source-frame workflow. User accepted the current 12,063-triangle version on 2026-10-12.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm6_djn_claude/review/viewer/)
includes all three tiers, nine clips, frame stepping, slow playback and native reference anchors.

## Selected delivery

- Editable, packed native-A master: [export/mm6_djn.blend](export/mm6_djn.blend).
- Runtime with palette variants and LODs: [export/mm6_djn.glb](export/mm6_djn.glb), installed identically at
  `assets_dev/worlds/mm6/models/mm6_djn.glb`; bindings appended in that directory’s `actors.yml`.
- Portable tier previews: `review/viewer/mm6_djn_a.glb`, `_b.glb`, `_c.glb`.
- Original separate 1K body/head texture sets and native palette ramps: `textures/`.
  Runtime merges these losslessly into 2080×1024 atlases with a 32px gutter.
- 60 bones, four influences per vertex. LOD triangles **12,063 / 6,029 / 2,169 / 718**, plus shadow LODs.
- Meshy: **35 / 100 credits**. Geometry 5, body texture 10, initial head 10, corrected head 10.
  Original returns and task/download hashes remain in `meshy/` and `creature_3d_progress.json`.

## Design and motion

Blue muscular male upper body, black topknot and goatee, pointed ears and earrings, gold belt,
right upper-arm band and small wrist bracelet, large left forearm bracer, no legs.
The ridged charcoal vortex curls backward and sways with floating movement.
All three gold arm ornaments detach during death; the body shrinks away and the ornaments remain.
Death is implemented with existing skeletal transforms; there is no new renderer feature.

Standing 3.0s; Walking 1.2s; Running 0.8s; Attack/Cast 1.5s; Hit 0.7333s; Fidget 2.4s;
Death 1.8s; Dead 1.0s. Attack and Cast use the same dual-palm release, adapted from the locally
stored `UnarmedCastDualAttack2` after source-rig motion review. Vortex and death are locally authored.
Release marker is 0.78s, fitted to the native 0.75s action by the existing engine.
Palm sockets launch projectiles and carry the existing white-blue star effect matching the native hand flashes.

Scale is 72.1: the native upright image spans 199 visible pixels at 0.799988 scale, against the
approximately 2.208m standing pose. All tiers share size. Head look uses the neck and head.

## Review and corrections

Five full-body HD masters and four head references are retained with exact prompts and imagegen provenance.
The left reference was corrected to preserve the native asymmetric jewelry.
Geometry was fitted before texture upload; hands have measured finger chains and source-frame retargeting.
Shoulder weights were smoothed after measured attack stretch failures. Final full-resolution skin stretch
p99 remains below 2×, and all authored poses remain above the floor.

The body retexture omitted seven small vortex faces. They were retained and given separate UV patches,
with texture sampling from adjacent returned faces. All other body faces transfer by verified correspondence.
The initial head unwrap overlapped; the replacement is repacked and separately retextured.
Final body/head UV overlap: **zero pixels** at 1K. Runtime normals are verified +Y-up.
Blue contamination at UV edges and the lower goatee was corrected; neck normal detail fades across the material seam.

Reduction ladder: 14,893 → 13,403 → **12,063** → 10,855 triangles.
Step 3 visibly faceted the casting shoulders/bracer rim and raised maximum posed surface error to 19.49mm;
step 2 was selected. Head, hands and UV seams were protected. See `review/reduction/selection.json`.

Agent review covers all nine clips at normal and quarter speed, front/side/back/three-quarter views,
face and palm closeups, tier colors and death/remains. Evidence: `review/playback/`, `review/closeups/`,
`review/tier_b/`, `review/tier_c/`, and indoor/outdoor model-versus-sprite captures in `review/ingame/`.

## Validation and limits

- Ordinary `openyamm` build passed; no Vulkan build.
- Genie actor-binding regression passed: all descriptors, palette variants, calibrated heights,
  clips, both palms and vortex chain.
- Final export reimport parity passed all clips; maximum measured surface difference 0.074mm,
  maximum socket difference 0.018mm, including half-frame attack samples.
- Viewer checked all **27 tier/clip combinations**, with no errors.
- Installed GLB verified identical, all animation samples retained through postprocessing, shared variants,
  one merged color primitive per LOD, 1K-equivalent texture density and valid influences.
- Native OpenGL desktop captures verified on NVIDIA hardware indoors and outdoors, including casting and remains.
- MM6 actor subset: **49 passed, 4 failed** in other families (Free Haven mage materials, guard materials,
  ooze material assumptions, male-cannibal binding). The unfiltered MM6-world actor suite additionally
  encountered DWI/world actor failures and crashed. These wider failures were not changed by this asset task.
- The documented `tools/model_backface_split.py` is absent from this checkout. That optimization was skipped;
  supported double-sided materials remain. No renderer changes were made.

## Reproduction / resume

Claim `mm6:djn` at this project root before writes. Use `tools/creature_workspace.py run` for ordinary
Python and `tools/run_creature_blender.sh` for isolated Blender scripts, retaining the returned lease token.
Do not resubmit successful Meshy jobs: their original returns are local.

The retained selected mesh is `work/textured_master.blend`; full-resolution source is
`work/textured_master_full.blend`. Earlier stages are `fitted_body.blend`, `rig_v1.blend`, `anim_v1.blend`.
`animate_genie.py` records the selected motion, and `align_cast.py` applied its final shared Attack/Cast timing.
`compose_genie.py` uses verified UV rasters and current body-v1/head-v2 texture returns.

Final rebuild order: system Python `compose_genie.py`; Blender `export_genie.py`; system Python
`tools/prepare_actor_glb.py export/mm6_djn_lod0.glb export/mm6_djn_runtime_lod0.glb`;
Blender `build_lods.py`; system Python `finish_runtime.py`, `viewer_tiers.py`, `update_viewer_manifest.py`.
Refresh the packed editable base-color maps from the tier-A preview, then Blender `pack_editable.py`.
Copy the runtime GLB to its installed path (bindings already exist), then `validate_delivery.py`.
Run the viewer checker and affected native checks after relevant changes. Reproduction does not imply user acceptance.
