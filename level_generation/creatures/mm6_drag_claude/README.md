# MM6 Fire / Lightning / Thunder Lizard (`drag`)

Production revision v3 follows the shared Claude 3D playbooks. The user accepted v3, including the whole-body Attack/Cast motion and corrected eye recoloring (2026-10-13).

| Tier | Descriptor | Monster ID | Palette |
| --- | --- | --- | --- |
| Fire Lizard | DragonCave A | 505 | 689 |
| Lightning Lizard | DragonCave B | 506 | 690 |
| Thunder Lizard | DragonCave C | 507 | 691 |

[Review viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_drag_claude/review/viewer/).
Nine clips: Standing, Walking, Running, Fidget, Attack, Cast, Hit, Death, Dead.
Standing is upright; gait leans forward. Attack/Cast release at 0.75 s from Socket_Mouth.
The native death is a fall to a corpse, with no dragon/drake burning effect.

## Selected delivery

- Editable: `export/mm6_drag.blend`.
- Portable full-detail animated GLB: `export/mm6_drag_runtime_lod0.glb`.
- Engine source with region palettes, colour/shadow LODs and merged head/body atlas: `export/mm6_drag.glb`.
- Installed via `tools/install_model.py` in both `assets_source/worlds/mm6/models/` and `assets_dev/worlds/mm6/models/`.
- Body and head each retain 2K albedo, normal and material maps, downsampled from separate 4K Meshy returns.
  Runtime packing uses 4128×2048 atlases with a gutter and preserves both 2K sets' density.
- 28 deform bones plus mouth socket; four influences per vertex.
- Scale 328: native standing silhouette 252 px × 1.299988, divided by approximately 1 m standing height.
  B/C use native tier scaling relative to A. Gait stride is 0.23 model units.
- Meshy: **25 / 100 credits** (5 geometry, 10 body texture, 10 head texture). Local rig/animations cost no credits.
  Rejected `meshy-7.1` requests created no paid tasks; retained requests use the live API's `meshy-7` model.

## Geometry reduction

15,323 corrected source triangles → 13,789 at the first 10% step. The second step, 12,411 triangles,
changed the posed hip surface by up to 18.16 mm on the 1 m model and was rejected. Head, thin fins,
claws and spines are protected. This is the last passing tested level, not a claim of a mathematical minimum.
Colour LOD counts are 13,789 / 6,894 / 2,471 / 794 before runtime backface copies.
The installed full-detail mesh has **13,879 triangles**, including 90 required reverse faces.
See `review/reduction/selection.json` and both measured/rendered trials.

## Production and reproduction

Original native references/motion: `../mm6_drag/native/`, `work/native_motion.json`, `review/native_motion.png`.
Selected high-detail body/head views and prompts: `references_hd/`. Original API outputs and receipts: `meshy/`.
Claim this project through `tools/creature_workspace.py` before changing it; use the Blender wrapper with that token.

Source sequence: inspect_model → clean_model → build_rig → uv_uploads → animate_lizard.
Retexture returns retain the verified UVs (`work/texture_uv_parity.json`); do not replace the animated master with a static return.
Then: texture_pipeline → compose_lizard → repair_spines → export_lizard → reduce_review.
Selected reduction is step 01. `ground_death.py` records the final corpse contact correction in `work/death_grounded.blend`;
`final_materials.py` consumes it, corrects horn classes and maps spine UVs to the interior of an ivory island.
`work/ivory_uv_centers.json` stores those verified pixel centres. Do not rerun early-stage scripts over final selections.

Final export sequence: final_materials → tools/prepare_actor_glb.py → build_lods → finish_runtime → viewer_tiers.
`finish_runtime.py` uses the existing shared region-variant and head-material merge tools. Install through `tools/install_model.py`.
Hashes, API jobs, selection and check status are in `creature_3d_progress.json`.

## Validation

Normal game build and the focused `mm6_cave_lizard_actor_model_tiers_and_clips` regression pass.
Earlier in the run the MM6-filtered actor suite produced 56 passes and five failures in other families: Mage/Guard material contracts,
Ooze gloss contract, missing Wyrm model and its burn binding. This task does not change those families. Concurrent Wyrm work subsequently fixed a transient unsupported-material loading failure; the final focused regression passes against the normal shared manifest. The entire MM6 suite was not repeated after those external changes.
The three tiers × nine clips pass `claude_shared/check_viewer.mjs`; actual playback was inspected at normal and quarter speed.
The merged installed GLB is reimported by `scripts/audit_delivered.py` and sampled for every clip.
Original/3D native comparisons are under `review/ingame/`, captured on NVIDIA OpenGL 3.3 through the desktop launcher.
The temple is dim and its right wall occludes the third spawn; all three tiers are visible in the outdoor comparison.
Native source and 3D poses can differ because live actors choose facing independently.

Animations are authored from native motion, not exact sprite-frame reconstructions. Android/Vulkan were not tested.
No gameplay timing, damage, projectile effects or renderer implementation was changed.

Final death validation: `review/ingame/death-models/fall.png` and `loot_satchel.png` use the normal mounted assets and live input tour. The current engine keeps the corpse briefly, then sinks it and shows its shared loot satchel; this creature leaves that shared behavior intact. Static screenshot tours freeze animation, so their `03-death_start_frozen.png` is only the start pose, not corpse evidence. The final held Dead pose and contacts are reviewed in `review/viewer_final/dead.png` and `review/death_grounding.json`.

A temporary manifest excluding the concurrently broken Wyrm was used for the final outdoor comparison (`outdoor-models/run.json`); only that unrelated binding differed. The later live death run and final focused regression use the normal full manifest. The temporary test asset mount was removed after review.

## v2 Attack/Cast momentum (2026-10-13)

The hips gather backward then drive forward, with knee compression over fixed feet, chest/neck follow-through,
arm motion and tail counterbalance. The head counter-rotates at release to retain forward aim. The windup
flows into release without the previous hold. Both clips remain 27 frames / 1.125 s; release remains at 0.75 s.

`scripts/motion_v2.py` loads `work/accepted_v1.blend`, replaces only Attack/Cast, asserts planted feet and
unchanged curve hashes for the other seven clips, then saves/exports the selected master. Continue with
prepare_actor_glb → build_lods → finish_runtime → viewer_tiers → install_model. Do not rerun final_materials
over this revision; that script restores the older animation checkpoint. Geometry and texture sets are unchanged.

All 27 viewer tier/clip loads pass; Attack/Cast playback was sampled at normal and quarter speed with
front/right/quarter extreme poses (`review/viewer_motion_v2/`). All nine installed clips pass reimport sampling,
and the focused game regression passes 1/1. `review/motion_v2.json` records the bake and preservation checks.
No new engine build, native GPU capture, Android or Vulkan run was needed for this scoped animation revision;
the earlier validation section describes v1 native checks. No additional Meshy credits were spent.

## v3 eye variant mask (2026-10-13)

The eye mask had been excluded from both recolorable regions, leaving orange source pixels beside the
recolored portion. `compose_lizard.py` now includes the full eye in the existing belly/fin region, preserving
the native tier colors and soft edge. Eye interiors have full coverage. Albedo, normal and material maps,
the body mask, geometry and all clips are unchanged. See `review/eye_mask_v3.json` for texture hashes.

Rebuilt runtime mask/atlas/variants and all viewer tiers, then installed. Three tier front closeups inspected
(`review/eye_v3/`); 27 viewer tier/clip loads and focused game regression 1/1 pass. No new native GPU capture.

## Further selective reduction trials (2026-10-13, rejected)

The accepted v3 remains installed at 13,789 base / 13,879 runtime triangles. Its selected/installed file hashes
were verified unchanged. `scripts/reduce_selective.py` starts from `work/accepted_v3.blend`, with protected
hips/legs, neck/face, UV seams, small limbs, spikes, tail crest and ear-fin roots. Several region/target trials
(12,986–13,243 triangles) fail the existing 7 mm posed-surface limit. A gentler 13,375-triangle trial passes
that numeric gate (6.29 mm maximum) but visibly changes membrane folds and shading in front head closeups,
so it is rejected too. Measurements alone are insufficient. See `review/reduction_v4/selection.json`,
`viewer_baseline/` and `viewer_trial/` for reports and same-camera comparisons; Attack/Running playback was
sampled at normal and quarter speed. No trial was installed or substituted into the main viewer.

A substantial further saving would need deliberate retopology and rebaking of selected regions; the existing
lower LODs already reduce distant rendering cost. This is a tested stopping point, not a mathematical minimum.

## v4 reduction and retexture (2026-10-13, installed)

The user accepted the reduction pilot `../mm6_drag_reduce_claude/` (README rounds 2-3): texture-aware reduction to
35 %, teeth rebuilt as clean cones, fresh UVs, new Meshy body/head retexture (20 credits). **4,882 triangles**
(LODs 2,428 / 844 / 254); the runtime copy adds 165 back copies. Installed from that project's `export/mm6_drag.glb`.
The v3 source is kept in `review/pre_reduce/mm6_drag_source_v3.glb` for rollback. Focused regression
`mm6_cave_lizard_actor_model_tiers_and_clips` passes. Rig and clips are unchanged.
