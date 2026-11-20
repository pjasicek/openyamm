# MM8 Dragon — m492

Production uses the shared Claude quadruped/dragon workflow. Four clawed legs, two membrane wings, a long spined tail and
articulated jaws are retained. The death flame was removed at the user's request in motion v2. User artistic acceptance is not recorded.

- Editable master: `dragon_master.blend`.
- Runtime source: `export/mm8_m492.glb`; one native palette, nine clips, four colour LODs and four shadow LODs.
- Interactive review: [local viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m492_claude/review/viewer/).
- Resumable receipts and stage gates: `creature_3d_progress.json`.

## Triangle reduction — 2026-10-18

The installed model is now the 55 % reduction from [`../mm8_m492_reduce_claude/`](../mm8_m492_reduce_claude/README.md):
LOD0 10,051 triangles (was 18,278), LODs 5,006 / 2,480 / 1,204, same textures, variant, rig and clips. `export/` and
`dragon_master.blend` here remain the unreduced motion-v3 production; the rollback source is
`../mm8_m492_reduce_claude/work/mm8_m492_source_pre_reduce.glb`. The triangle counts in the sections below describe
that unreduced production.

## Motion revision v3 — single attack arc

The user identified an extra head turn around viewer frame 53, followed by another reversal around frame 62.
The v2 yaw keys returned toward zero at release and then swung back to the strike side. Attack/Cast now make one
upper-left to lower-right sweep, hold that side through the start of the rise, then settle directly to centre.
The release remains at **1.25 s (viewer frame 60 at 48 fps)**. The evaluated mouth path has no sideways reversal
from frames 48–66; frames 66–80 return monotonically to centre. See `review/motion_v3/head_path.json` and
`head_contact.jpg`, including the reported frames 53 and 62.

Only Attack/Cast neck/head yaw and its small tail counter-motion changed. Hit, Death, the other clips and all
geometry/material/skin data are preserved byte-for-byte (`review/motion_v3/preservation.json`). The revised master
and all six production/viewer GLBs are updated; installed hashes are in `work/install_receipt.json`.

Checks: 96 Hz floor/socket sampling, keyed wing/body contacts, 48 Hz lower-LOD Attack/Cast checks, all-nine-clip
export reimport (maximum **8.77e-6 m** error), nine viewer clip switches, 12 timed normal/half-speed Attack playback
samples, exact-frame head close-ups and native NVIDIA OpenGL attack captures. The focused Dragon regression passes
with the normal production manifest. Evidence is under `review/motion_v3/`; the current delivery receipt is
`work/delivery_checks.json`. Hit/Death retain motion-v2 evidence. No additional Meshy credits were spent.

Reproduce with `scripts/motion_v3.py`, `scripts/check_motion_v3.py`, then `scripts/publish_motion_v3.py` under the
creature lease; run the existing export audit/reimport and `scripts/check_motion_lods_v3.py` before installation.
The previous selected master, exports, viewer, scripts and playback are retained under `work/before_motion_v3/`.

## Motion revision v2 — 2026-10-18

User requested the MM6 `cdr1` attack/head-movement study, stronger backward and sideways hit recoil, and no death flame.
Motion v2 introduced the changes below; v3 above replaces its attack yaw recovery.

- **Attack/Cast:** sideways head preparation, a deeper chest/neck dip, then a short forward thrust with open jaws at
  **1.25 s**. Recovery sweeps the head back up. The front-only MM8 `m492aa0`–`m492aj0` source frames establish the dip,
  wing lowering and recovery; the accepted MM6 `cdr1` v6 motion supplies the head-sweep reference. Hidden attack views
  cannot be reconstructed from those MM8 bitmaps. The visible sequence is retimed so its release pose coincides with
  the existing gameplay event, rather than firing after the head has already recovered. Native reference labels in
  the viewer retain their original frame times; anchor positions follow the retimed motion.
- **Hit:** the original front/side `m492n*` sequence informed the backward neck arch, lateral bank, tucked limbs,
  tail counter-motion and opposing head sweep. Head travel spans **0.153 m sideways and 0.173 m fore/aft**. The native
  **1.25 s** duration remains unchanged; incoming blending still leaves the larger recoil visible.
- **Death:** the body collapse and held corpse are unchanged. The flame mesh is omitted from production/viewer GLBs,
  and its controls are disabled in the editable master. No replacement effect was added.

The body, every colour/shadow LOD, UVs, materials, textures and skin data are verified unchanged. Standing, Walking,
Running, Fidget, Death and Dead body skeletal samples are preserved byte-for-byte in the GLBs. Historical v1 is retained
under `work/before_motion_v2/`; this includes the previous exports, master, scripts, viewer and playback.

Checks: revised Attack/Hit sampled at **96 Hz** with positive floor clearance; keyed wing/body collision tests pass;
all attack mouth samples fit adult and small-family release limits. All lower LODs retain positive clearance.
Reimport of all nine exported clips matches the editable master within **8.77e-6 m**. Viewer switches all nine clips
without errors. See `review/motion_v2/dense_checks.json`, `lod_motion_checks.json`, `preservation.json` and the new
playback/native-game evidence. The focused Dragon regression passes against the normal production manifest.
Current native captures are in `review/motion_v2/combat/` (attack) and `review/motion_v2/clean_hit_death/`
(idle damage reaction, flame-free collapse and satchel transition). Indoor captures, Android and Vulkan were not
repeated for this scoped motion edit.

Reproduce this revision under the creature lease with `scripts/motion_v2.py`, `scripts/check_motion_v2.py`, then
`scripts/publish_motion_v2.py`; verify/export/install through the existing helpers. The publication step starts from
`work/before_motion_v2/` and preserves the existing body data. Earlier full-production scripts are historical inputs,
not a replacement for this final scoped revision.

## Native identity and size

All six descriptors use palette 492. There are no invented red/green/black colour tiers.

| Descriptor | Monster id | Scale |
| --- | ---: | ---: |
| Dragon A | 70 | 1504.288787354 |
| Dragon B | 71 | 1504.288787354 |
| Dragon C | 72 | 1504.288787354 |
| Wimpy Dragon A | 190 | 1203.431029883 |
| Wimpy Dragon B | 191 | 1203.431029883 |
| Wimpy Dragon C | 192 | 1203.431029883 |

The small family preserves the native 4:5 sprite-size ratio. Scale comes from average front silhouette area over a full
11-frame flight cycle; wing span alone is unsuitable for flyers. No hover pedestal or simulation-size change is added.
`review/scale/measurement.json` retains the calculation. Native references cover all 172 source frames and exact descriptor
aliases, including spaces (`Dragon A`, `Wimpy Dragon A`).

## Geometry, animation and materials

Smart Topology supplied the immutable 30k source. Local repairs remove three loose single-triangle artefacts, open the
fused mouth, add its dark interior and upper teeth, and fit a six-limb rig. Soft limb roots, rigid digits, wing feathering,
crown clearance and folded corpse wings are checked after weighting. Reduction proceeds in approximately 10% steps;
step 5 passes, while step 6 exceeds the 1 mm 99th-percentile surface-error gate in the corpse poses. Textured and clay
comparisons retain all checkpoints. LOD0 contains **18,278 body triangles**. Lower body LODs
contain **9,122 / 4,550 / 2,254 triangles**; shadow meshes use the same four counts.

| Clip | Duration | Use |
| --- | ---: | --- |
| Standing / Walking | 1.375 s | Native flight period |
| Running | 1.083333 s | Faster flight option |
| Fidget | 2.75 s | Two-cycle native-informed look |
| Attack / Cast | 1.666667 s | Native impact at 1.25 s, then recovery; Cast is a non-caster alias |
| Hit | 1.25 s | Native recoil duration |
| Death | 1.375 s | Flame-free side fall, body/limb grounding before folded wings |
| Dead | 1 s | Exact held Death endpoint |

The release socket sits inside the jaws: all authored attack samples fit the native launch envelope. Moving attacks use
the whole Root subtree so the checked neck, wing and mouth pose stays together. Native movement, damage, HP, collision,
ranged elements, sounds and action clocks remain engine-owned. No whole-body burnaway is enabled.

Body, head and wings have independent UV domains; their 2k runtime maps occupy one padded **6208×2048** atlas without
resampling. The head has roughly twice the body's linear texel density. Raw Meshy returns are 4k body, 2k head and 4k wings.
The fitted mesh and frozen UVs are retained: five small paint transfers cover coincident faces omitted by the service;
two retained lip slivers total 3.72e-8 m². These closed-mouth seam slivers are the recorded modelling-guideline exception.
153 oral-cap triangles receive separately defined dark oral paint. All three UV domains have zero interior overlap at 2k.
Original sculpt normals and AO are baked locally. Normal maps use glTF +Y-up; the MR red channel contains the specular mask,
green roughness and blue metallic (zero). Physical classes distinguish hide, membranes, ivory horns, teeth, eyes and mouth.
Native region ramps preserve generated luminance. The former mouth-fire mesh is omitted from all current runtime and viewer exports. Its historical atlas remains as
source provenance; no flame or substitute effect is enabled for Death.

## Provenance and checks

The selected five body and four head HD references retain original generation outputs, prompts and SHA-256 receipts.
Meshy used **35 credits**: 5 for geometry and 10 each for body, head and wing textures. No animation-library purchase.
`meshy/` retains original returns. The historical fire atlas is the repository's own procedural bonfire atlas; see `work/mouth_fire.json`.

- Original production gate (before motion v2): dense reduced-mesh sampling at 48 Hz, normalized four-weight skin, closed loop endpoints, no floor penetration;
  Death/Dead endpoints match exactly. `review/animation_gate_reduced.json`.
- Original production gate: 268 authored keyed wing/body collision samples: no intersections. `review/wing_contacts.json`.
- GLB reimport: all nine clips, maximum sampled surface error **8.77e-6 m**. `work/export_parity.json`.
- Embedded images, LOD counts, absence of the flame mesh, palette variant and specular-mask contract: `work/final_export_audit.json`.
- Browser: all nine clip switches succeed without console errors. Playback retains normal/half-speed WebM recordings
  and timed PNG samples; agent inspection uses the sampled images.

## Installed runtime verification

`tools/install_model.py` installed the source under `assets_source/worlds/mm8/models/mm8_m492.glb` and cooked the
runtime model plus five textures under `assets_dev`. Motion v2 updated the model with zero textures recooked. `work/install_receipt.json` records matching source/export hashes
and the cooked runtime hash; the installed bytes were checked again after runtime review. All six descriptor bindings
are in `assets_dev/worlds/mm8/models/actors.yml`; `work/runtime_bindings.yml` retains this family's exact entries.

- The original production OpenGL build passed; no rebuild was needed for motion v2. Native desktop captures used the NVIDIA GPU (`vendor=0x10de`) on Wayland.
- Motion v2: `mm8_dragon_actor_models_keep_native_sizes_and_simulation` passes with the normal production
  manifest. It covers all six descriptors, shared geometry, eight presentation states, nine clips and the mouth release
  envelope. See `review/motion_v2/dragon-motion-v2-production-regression.log`. No simulation or renderer behavior
  changed in this revision.
- Historical v1: Dragon, Gorgon and Serpentman focused cases passed with a temporary manifest containing their twelve
  production bindings verbatim. The Cyclops/Skeleton Archer loader blockers recorded then no longer block the current
  focused Dragon run. The broad actor suite and the other two focused cases were not rerun for motion v2.
- Original production: matching native/model cameras were inspected on MM8 `out05.odm` and `d17.blv`; see `review/ingame/out_sprites`,
  `out_models`, `in_sprites` and `in_models`. The model intentionally starts at the actor origin: native flying
  billboards lean toward the camera and appear raised, but the playbook forbids a 3D hover pedestal that clips ceilings.
- The controlled MM6 `oute3.odm` fixture holds one hostile Dragon stationary for attack framing; current captures are
  in `review/motion_v2/combat/`. That pass retains projectile effects from preceding attacks, so the separate idle fixture
  in `review/motion_v2/clean_hit_death/` verifies the stronger damage reaction and flame-free death without nearby
  projectile remnants. Its 15 frames show recoil, side fall, grounded folded wings and the existing sink/satchel transition.
  The exported `Dead` clip is held and has no burnaway. Both native runs completed on NVIDIA OpenGL.
- Original production: all four colour LODs render in the native game; all lower LODs passed 48 Hz floor checks over
  every clip. Motion v2 repeats the lower-LOD checks for Attack/Cast/Hit: `review/motion_v2/lod_motion_checks.json`.
  Blender LOD comparisons cover raised/lowered wings, attack, corpse and rear view: `review/lods/`.
- The adult and small family share one palette and model. Their native 5:4 scale relationship is retained in the six
  bindings; the smaller family is also captured at the adult's camera. See `review/ingame/lods` and `small_lods`.
- Browser playback retains all nine clips at 1× and 0.5× with 108 timed PNG samples and 18 WebM recordings.
  Historical motion-v2 inspection covers 36 timed Attack/Hit/Death frames at both speeds in
  `review/motion_v2/playback_contact.jpg`, plus authored poses, LOD comparisons and head close-ups. Unchanged clips were
  recorded but not visually reinspected. Original v1 playback is retained under `work/before_motion_v2/playback/`; v2 playback is in
  `work/before_motion_v3/playback/`. Current playback inspection is described in motion v3 above.
  Continuous video was not independently watched.

The isolated review fixtures preserve production maps and tables; their sole scene changes are the review actor and
its stationary/aggressor attributes. No native sprites, collision dimensions, combat values or gameplay clocks were
changed in the production assets. `work/combat_fixture.json` and `work/small_fixture.json` record those fixture changes.

## Reproduce or review

Open the local viewer linked above while its server is running, or run
`python3 -m http.server 8912 --bind 127.0.0.1` from the repository root. Use
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m492_claude check`
for the clip-switch check. Editing or writing review captures requires claiming this creature workspace first;
`tools/creature_workspace.py` and the existing Blender/Meshy wrappers retain that ownership guard.

The project retains the authored rig, animation, reduction, UV, texture assembly, export and validation scripts.
Final body topology and actions are in `dragon_master.blend`; `export/mm8_m492.glb` is the selected deliverable.

Indoor captures, Android, Vulkan, the broad actor suite and hardware performance benchmarking were not repeated for
this scoped motion revision. No engine renderer changes. User artistic acceptance remains unrecorded.
