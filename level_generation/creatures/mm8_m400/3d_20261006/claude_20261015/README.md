# MM8 Lizardman Peasant A — Claude playbook continuation, 2026-10-15

The selected delivery is **Peasant A**, native descriptor 1, bitmap family `m400`, palette 401.
It is installed in the MM8 model manifest. Farmer B and Villager C retain their sprites.
The 2026-10-06 body, fitted 40-bone rig and native-action interpretation were reused under the playbook's resume
rule, then corrected and finished. This is not a new source-frame rig or a new body generation.
User artistic acceptance remains pending.

## Review and files

- [Interactive animation viewer](review/viewer/index.html): serve the repository and open this path;
  the current local server is `http://127.0.0.1:8765/level_generation/creatures/mm8_m400/3d_20261006/claude_20261015/review/viewer/`.
  Six clips, normal/slow playback, native frames in five directions and per-frame feedback use the shared viewer.
- [Portable GLB](delivery/mm8_lizardman_peasant.glb), [editable Blender master](delivery/mm8_lizardman_peasant.blend),
  [separate-material LOD0](delivery/mm8_lizardman_peasant_lod0.glb), [texture maps](textures/).
- [Delivery receipt and installed hashes](delivery/delivery.json), [components](delivery/components.json),
  [clip roles](delivery/clips.json), [calibration](calibration.json).
- [Native GPU front](review/ingame/material_front/front.png), [studio front](review/final_Standing_front.png), [head](review/final_detail_head.png),
  [hands](review/final_detail_hands.png), [feet](review/final_detail_feet.png),
  [fidget](review/final_Fidget_side.png), [corpse](review/final_Corpse_quarter.png).
- [Normal playback sheet](review/playback_front_1x.jpg), [slow side playback](review/playback_right_0.25x.jpg).

## Changes and source intent

The native creature is unarmed: teal scales, paired webbed head fins, a green gold-edged tunic, checkered apron,
arm bands, ivory neck/calf ornaments and three forward toes. The retained four-digit hands are an inference
from the source views. No tail, weapon, cast or disappearance effect was invented.

New four-view transparent head references and one Meshy head-only retexture preserve the selected identity.
All 1,594 uploaded head triangles retained exact triangle UV correspondence. Only maps were transferred back
to the animated master. The new reference prompts and input/output hashes are in
[head provenance](references_head/generation_runs.json); the paid job and immutable downloads remain in the
canonical progress record and the creature's `meshy/head_retexture_claude_20261015/` directory.
This revision cost 10 credits; the whole retained project has consumed 70 of its 100-credit limit.

Weight smoothing removes sharp ownership changes at the garment, neck, knees and ankles. The original worst
edge stretch was 38.7x on a 4.3 mm edge; the final export's maximum is below 4x. Head, hands, feet and the
checkered apron are protected during body reduction. The fidget now reaches toward the snout with a 59.54-degree
wrist swing and continuous forearm rotation; it no longer reverses the wrist. One-shots ease from/to Standing,
and Death ends at the exact Corpse pose. A sampled root correction keeps the mesh on the floor.

Standing/Corpse are 0.125 s, Hit/Fidget 0.5 s, Death 0.75 s. Walk retains the source gait's sampled 31/30-second
cycle. Both native attack slots alias Walk; gameplay timing remains authoritative. Animation is baked at 192 Hz
to preserve the source's curved motion between frames; NLA's fractional walk endpoint is corrected explicitly.

**Standing v2 (2026-10-18, user review of the triangle reduction).** The 0.125 s static Standing became a 4.0 s
idle: arms re-posed like the native `m400sa` frames, two breaths, a weight shift with both feet held exactly in
place, head drift and a slight arm swing (`scripts/standing_idle.py`, run by `rebuild.py` after `polish_motion.py`;
Hit/Fidget/Death arm bones ease to the new pose). Previous clips stay in the master as `Standing_v1`, `Hit_v1`,
`Fidget_v1`, `Death_v1`; the v1 master is `work/standing_v1/master_motion_v1.blend`. The clips ship on the reduced
model (`../../../mm8_lizardman_peasant_reduce_claude/`, transplanted with `scripts/export_clips.py`); `delivery/` here
was not rebuilt and still holds v1.

## Runtime

Source: `assets_source/worlds/mm8/models/mm8_lizardman_peasant.glb`.
The installer cooks the runtime GLB and four `.oytex` textures under `assets_dev/worlds/mm8/models/`.
The binding uses scale 115.3635802632 (196 native pixels / 1.698976 m), stride about 1.408454 m,
yaw offset -pi/2, and neck/Head look nodes. There is one merged material with the `m400_a` variant, four
2080x1024 atlases, metallic zero, per-class specular in MR red, and a padded garment region mask/ramp.
The A ramp preserves the retained A appearance; this revision does not author B/C palette ramps.

Colour LOD triangle counts: **10,995 / 5,495 / 2,744 / 2,417**; corresponding shadow LODs are present.
The final level is deliberately 22% of LOD0: further collapse damaged separate fingers and small outfit parts.
This is the recorded silhouette-budget deviation. There are at most eight normalized influences per vertex.

## Verification

- [Export comparison](review/export_validation.json): 97 poses per clip, maximum source/export surface error
  2.28 mm, maximum floor penetration 0.45 mm, exact one-shot/loop/corpse endpoints.
- [Final rig measurements](review/rig_probe_final_export.json): hand edge stretch <=2.405x, arm p99 <1.49x,
  wrist swing <=59.55 degrees, forearm roll within 90 degrees. These are checks of the retained rig, not a claim
  that every source-frame-rig-specific gate was applicable.
- [Asset validation](review/asset_validation.json): all eight meshes, indices, finite attributes, normalized
  influences, no degenerate triangles and six supported zero-origin animation timelines.
- [Viewer check](review/viewer_check.json) and [actual playback receipt](review/playback/playback.json): six clips,
  24 front/right normal/quarter-speed runs, no console errors; the exported poses and captures were inspected.
- `cmake --build build --target openyamm -j25` passed. The focused case is
  `mm8_lizardman_peasant_actor_model_keeps_native_roles`; the MM8 actor suite (`OPENYAMM_REGRESSION_FILTER=mm8_`)
  passed 1/1. It covers the installed model, clips, LODs, native role aliases and unchanged simulation state.
- Native GPU: OpenGL 3.3 on NVIDIA through SDL Wayland. [Outdoor model](review/ingame/outdoor_model/approach.png)
  and [sprite](review/ingame/outdoor_sprite/approach.png) use the playbook's identical New Sorpigal camera.
  [Indoor model](review/ingame/indoor_model/approach.png) was checked in Agar's Laboratory.
  [MM8 world](review/ingame/mm8_native_world/front.png) verifies automatic manifest selection in Dagger Wound Islands.

**Runtime review limitation:** the native indoor sprite was invisible at the test pose with models disabled,
also after isolated quicksave/reload. The model renders correctly there, but an indoor sprite/model size
comparison could not be completed. The records and failed baseline captures are preserved under `review/ingame/`.
This task does not change the sprite renderer. Android and Vulkan were not tested. Very deep scene shadows can
hide colour detail; the cart-side MM8 capture records that lighting condition separately.

## Reproduce

Claim the existing `mm8:m400` workspace using `tools/creature_workspace.py` and its canonical
`3d_20261006/creature_3d_progress.json`; use the returned token with the existing Blender wrapper.
The retained `master_weights.blend` and authored `textures/` are the rebuild inputs:

```sh
tools/run_creature_blender.sh --token <token> level_generation/creatures/mm8_m400/3d_20261006/claude_20261015/scripts/rebuild.py
python3 tools/creature_workspace.py run --project level_generation/creatures/mm8_m400 --token <token> -- python3 level_generation/creatures/mm8_m400/3d_20261006/claude_20261015/scripts/validate_asset.py
python3 tools/install_model.py level_generation/creatures/mm8_m400/3d_20261006/claude_20261015/delivery/mm8_lizardman_peasant.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_ ./build/game/openyamm --world mm8 --headless-run-regression-suite actors
```

`rebuild.py` runs motion correction, export, prepare, colour/shadow LODs, variants, head-material merge,
reimport comparison, render and deformation probes. The head UV preparation and material composition scripts
are retained for source-level changes. Refresh viewer/receipt hashes and repeat affected visual checks after
any new export. Install from the project GLB, never from a cooked runtime copy. Nothing was staged or committed.
