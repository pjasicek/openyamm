# MM8 Air Elemental — m508

Created, revised for larger muscles and installed 2026-10-18. Technical and agent visual review complete; user approved this muscular revision on 2026-10-18.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m508_claude/review/viewer/) ·
[Portable GLB](export/mm8_m508.glb) · [Packed editable Blender master](export/mm8_m508.blend) ·
[Canonical progress and hashes](creature_3d_progress.json)

![Restored reference, previous model and muscular revision](review/muscle_revision/comparison.jpg)

The latest revision follows the request for a more muscular build. Restored ×2 `m508sa0`, `m508sa2` and
`m508ac0` supplied the chest, shoulder, arm and abdominal references. The previous model and its state are
preserved in `archive/pre_muscle_revision/`; current screenshots use the `muscle_` prefix.

![Revised three native tiers outdoors](review/muscle_revision/outdoor_models/front.png)

## Source and selected route

The requested combination is the explicitly accepted [MM6 Air wind treatment](../mm6_aie1_claude/README.md)
and [Djinn upper-body motion](../mm6_djn_claude/README.md), fitted to MM8's visible humanoid torso.
The shared non-humanoid playbook's effect-body exception uses procedural wind and a simple MPFB torso,
as in [MM6 Fire](../mm6_fie1_claude/README.md). No Meshy jobs or HD image generations were required: **0 credits**.

[Native inventory](native/inventory.json) verifies 160 BMP sources and records 20 orphan death-view images.
The eight native action contact sheets are in `review/native_*.png`. Descriptor groups m509/m510/m511 all use
palette 508; tiers differ by scale, so this model shares one appearance. Monster ids 82–84 bind Air Elemental
A/B/C at 1, 1.25 and 1.5 times the base scale. The base standing frame is 204 pixels tall; model height is
2.04 m before runtime scale 100. Original sprites and gameplay tables remain authoritative.

Wind streaks and palm discharge come from the restored m508 front/back standing and attack frames under
`../mm8_packed_outline_collection_20261002/families/mm8_m508/aligned_2x/`.
[Texture provenance](textures/provenance.json) records source hashes. Djinn rotations are sampled from its
selected GLB and retained with source hash in [djinn_motion.json](work/djinn_motion.json).
No Djinn costume, geometry or palette enters this creature.

## Geometry, material and motion contracts

The torso has a broader chest and back, larger deltoids, upper arms and forearms, abdominal relief,
complete open hands, a bald face and a waist cut inside the wind. MPFB muscle targets and increased body mass
provide the bulk. Reduction now follows trimming so the 6400-triangle torso budget preserves the anatomy.
Reduced cloud mottling, stronger AO and azimuth-neutral baked top lighting make the muscle shapes readable
from every side. Smaller UV charts are checked for pixel overlap before baking.
The model uses four separate mesh roles across three materials: opaque Body, blended Wind, palm Lightning and DeathCloud.
Body colour, broad shading and AO are baked into a 1024² map. Wind is 1024×2048 RGBA and lightning 512² RGBA.
All three maps are embedded in the portable GLB and packed in the Blender master.

The elemental materials are deliberately unlit, with zero specular and edge darkening, following the accepted
Air/Fire treatment. They remain pale in dark interiors; the original lit sprite becomes much darker there.
Single-sided wind shells are ordered inside outer-to-inner and outside inner-to-outer, with soft alpha edges.
The shared engine scrolls wind U at 0.75 per second; layer UV repeats create different rotation speeds.
Leaf width bones avoid scale/rotation shear. Only the opaque torso casts a solid shadow.

| Colour LOD | Body | Wind | Dispersal | Lightning | Total triangles |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 6400 | 3264 | 720 | 12 | 10396 |
| 1 | 3200 | 1536 | 360 | 12 | 5108 |
| 2 | 1598 | 680 | 192 | 8 | 2478 |
| 3 | 510 | 232 | 168 | 8 | 918 |

The shadow chain uses the three coarse torso meshes. LOD3 is intended for distance and visibly faceted when
forced near the camera. The totals include the normally hidden dispersal and lightning meshes.

| Clip | Seconds | Behaviour |
| --- | ---: | --- |
| Standing | 3.0 | Floating torso and continuous wind |
| Walking / Running | 1.2 / 0.8 | Fitted Djinn upper-body travel with wind lean |
| Attack / Cast | 1.5 | Gather in both palms, push forward, release at 0.78 s |
| Hit | 0.733333 | Short recoil within the native 0.75 s hit window |
| Fidget | 2.4 | Djinn torso/head motion |
| Death | 0.8 | Arms spread, torso contracts, wind expands and disperses |
| Dead | 1.0 | All four mesh nodes hidden; no corpse |

Cast arm motion is fitted to a positive elbow hinge with bounded arm/wrist twist and a smoothed axial turn.
No feet, equipment, clothing or solid remains are required. The runtime binding retains native gameplay timing,
uses palm/eye sockets, head look, travel stride 1.65 and the original Sparks/Lightning Bolt/Implosion spells.
Visual release markers use the selected clip clock; they do not change combat data.

## Delivery and verification

Selected GLB SHA-256: `9d3281a595e011fcf849b9f3fd07c339f5dd01d6e4b9a22c9df3d175d5398132`.
Installed with `tools/install_model.py` to `assets_source/worlds/mm8/models/mm8_m508.glb` and the cooked
`assets_dev/worlds/mm8/models/mm8_m508.glb`. The three descriptor bindings are in the world's `models/actors.yml`.
Installed hashes, component coverage and corrections are in the canonical progress record.

- [Deformation report](work/gates.json): **615 PASS, 0 FAIL**, sampling 48 Hz skin/rotation and 24 Hz body contacts.
  Reuses the shared GLB decoder, skinning and surface BVH. Covers all four colour LODs, shadow weights,
  finite skinning, shear, stretch, elbow/wrist constraints, loop seams and ground clearance.
  The generic grounded-humanoid runner is not claimed as passing: feet/soles/knees, cloth and props are N/A;
  translucent shell intersections are intentional and excluded from solid-body collision checks.
- [Independent Blender reimport](work/reimport_parity.json): all nine clips, 27 keyed/fractional samples;
  maximum surface difference 8.65e-07 m.
- [Viewer check](review/viewer_check.json): 27 tier/clip switches, zero failures or console errors.
- [Normal and half-speed playback](review/playback/playback.json): 18 refreshed WebMs, sampled PNGs and nine contact sheets.
  Reviewed all clips plus [torso](review/shots/muscle_torso.png), [cast/palms](review/shots/muscle_cast.png),
  [front](review/shots/muscle_front.png), [side](review/shots/muscle_side.png) and [back](review/shots/muscle_back.png).
- [Family regression with the current production manifest](review/muscle_revision/regression.log): **1 PASS, 0 FAIL**.
  Checks tier ratios, shared model, required clips/sockets, cast discharge visibility and empty Dead.
  An isolated-family run also passes. An earlier full-manifest attempt encountered a concurrent unrelated Ogre
  socket update; the final full-manifest retry passes. No engine code changed in this revision, so no rebuild was needed.
- Revised NVIDIA OpenGL 3.3/Wayland captures: matched camera [outdoor](review/muscle_revision/outdoor_comparison.jpg)
  and [indoor](review/muscle_revision/indoor_comparison.jpg) model/native tiers, forced [LOD0–3](review/muscle_revision/lods.jpg),
  live [casting](review/muscle_revision/combat.jpg), [hit and death](review/muscle_revision/death.jpg).
  All three new runs exited successfully with no model-loading errors. Native game readback generated the PNGs.
  The native comparison panels reuse the unchanged sprite captures at the same cameras.

The ordinary build, [MM6 Air](review/mm6_air_regression.log) and [Djinn](review/mm6_djinn_regression.log)
regressions passed during initial delivery. The six original game runs under `review/ingame/`, including outdoor
combat, are historical evidence for the previous torso; the three `review/muscle_revision/` runs show this revision.

Captures use New Sorpigal `oute3.odm` and Agar's laboratory `6d19.blv`. Isolated hard-link fixtures preload
ids 82–84 before debug spawning; only the fixture scene files were replaced, never production maps.
The per-run `tour.yml`, `run.json` and focused `capture.log` preserve cameras, commands and GPU evidence.
These minimized-window visual runs are not performance measurements. Android and Vulkan were not tested.

## Reproduction

Claim this project through `tools/creature_workspace.py` before writing. Run ordinary Python scripts under
its `run --project … --token … --` guard and Blender scripts with `tools/run_creature_blender.sh --token …`.
Use the existing selected master for small edits; a full rebuild follows this order:

1. `scripts/build_figure.py` — installed MPFB base, muscular morphs, abdominal relief, waist trim, reduction and fitted weights.
2. `scripts/retarget.py` — sample local selected Djinn and create upper-body actions.
3. `scripts/make_textures.py` — restored-source wind, lightning and body palette.
4. `scripts/build_model.py` — bake body colour, assemble effects/LODs, animate and pack master/raw GLB.
5. `scripts/finish_runtime.py` — prepare GLB, link LODs, set materials/scroll and hidden Dead mesh nodes.
6. `scripts/audit_export.py`, `scripts/reimport_check.py`, `scripts/make_viewer.py` — validate export and refresh review.
7. `tools/run_creature_review.py --project … check`, then `playback`/`shots` with the lease token.
8. `python3 tools/install_model.py …/export/mm8_m508.glb --world mm8`, followed by the focused regression and captures.

`prepare_native.py` is the initial inventory/bootstrap step and resets initial progress; do not run it on resume.
Blender intermediates and early diagnostic stills in `work/` and `review/figure_*` are not selected deliverables.
