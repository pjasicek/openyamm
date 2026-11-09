# MM8 Phoenix — m572

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m572_reduce_claude/`](../mm8_m572_reduce_claude/README.md) (LOD0 14,872 -> 8,919). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m572_reduce_claude/work/mm8_m572_source_pre_reduce.glb`.


Selected production revision: **attack-v3**, built and installed on 2026-10-18.
Technical checks and agent image review are complete. User artistic acceptance is not recorded.

- [Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m572_claude/review/viewer/): three tiers, nine clips, native frames and frame-specific feedback.
- [Editable packed Blender master](phoenix_master.blend).
- [Portable GLB with native variants and runtime LODs](export/mm8_m572.glb).
- [Production state and provenance](creature_3d_progress.json), [delivery hashes and review evidence](review/delivery.json).
- [Outdoor comparison](review/runtime/outdoor-comparison.jpg), [indoor comparison](review/runtime/indoor-comparison.jpg), [native death sequence](review/runtime/combat-death.jpg).

## Attack/Cast timing refinement — 2026-10-18

Viewer frames **17–32 at 48 fps now occupy frames 17–23**, making that held portion **2.5× faster**.
All following keys move 0.1875 seconds earlier: each clip is now 1.0625 seconds long and its authored impact is
0.6875 seconds (viewer frame 33). All nine Phoenix binding markers follow the new impact. The engine still
applies damage at the native gameplay time, fitting the animation wind-up to that event.

The deeper body/claw lean-back and stronger strike from attack-v2 are preserved: the existing pose values,
including flame channels, are byte-identical. Geometry, textures and the other seven clips are also unchanged.
[Timing and checks](review/attack_v3/revision.json), [preservation proof](review/attack_v3/preservation.json),
[native attack](review/attack_v3/native-attack.jpg) and normal/half-speed recordings in `review/playback/` cover this revision.
Review used timed images; continuous video viewing is not claimed. The export parity check, all 27 tier/clip
switches and the focused regression pass. No further Meshy credits were used.

The earlier [attack-v2 pose comparison](review/attack_v2/before-after.jpg) remains the reference for the unchanged
body and claw poses; its timing is superseded here.

## Identity and motion

The compact feathered bird, hooked beak, separate lower bill, two articulated taloned feet and short fanned tail
follow the native Phoenix. Harpy supplied feather and articulated-wing lessons; Bat supplied the flight benchmark.
The bird rig and animation were authored locally. No humanoid retarget or paid animation service was used.

The native study contains 125 stored poses, of which 103 are referenced, with five stored views and mirrored directions.
Phoenix A/B/C are local monster IDs 130/131/132, displayed as Fire Bird/Phoenix/Grand Phoenix, using palettes 573/574/575.
The native death order is **Na, Nb, Da, Db, then Xa**; orphan animation frames were not substituted.
See [native inventory](references/native_inventory.json), [pre-retiming motion measurements](work/clips.json) and [selected timing map](work/attack_retime.json) and the source images in `references/native/`.

| Clip | Duration | Behavior |
| --- | ---: | --- |
| Standing / Walking | 1.0 s | Flight with delayed elbow/wrist recovery, feather folding and body counter-motion |
| Running | 0.75 s | Faster forward flight |
| Fidget | 2.0 s | Flight with a head look |
| Attack / Cast | 1.0625 s | Deeper lean-back and claw tuck, shortened anticipation, sharp talon drive; authored impact at 0.6875 s |
| Hit | 0.625 s | Backward and lateral bank, followed by recovery |
| Death | 1.125 s | Backward fall with feet raised, grounded torso and settling wings |
| Dead | 1.0 s held | Exact landed endpoint, flames extinguished |

Attack retains the native 0.875-second damage timing; the native attack is fire melee with no projectile or spell.
Cast supplies the common presentation role without adding gameplay abilities. Death extends the native half-second
poses into a physical landing; gameplay timing and simulation tables remain unchanged. The engine owns flight altitude:
there is no extra hover pedestal in the mesh. Wing strokes may extend below the live actor origin; corpse surfaces stay above the floor.

## Geometry and materials

Meshy Smart Topology produced an untextured 31,789-triangle bird. A measured 26-bone avian rig assigns detached feathers
and claws to their anatomical controls, with soft blends across connected joints. Nine flame controls bring the total
to **35 bones**, with no more than four influences per vertex.

The selected step of the approximately 10% reduction ladder preserved the silhouette; the next step lost a protected
contour. The final export removes 68 zero-area faces. Frozen UVs have no overlap, with increased head texel density.
Meshy's texture return was transferred onto the preserved original geometry/UVs rather than replacing the rigged mesh.
The maximum measured surface correspondence error was 0.0495 mm.

| Geometry | LOD0 | LOD1 | LOD2 | LOD3 |
| --- | ---: | ---: | ---: | ---: |
| Bird triangles | 14,872 | 7,430 | 3,712 | 1,836 |
| Flame triangles | 288 | 216 | 144 | 72 |

Opaque body shadow LODs accompany all four levels. The body uses a 2048-pixel base colour and 1024-pixel normal,
AO, packed material and region maps. A zero-miss normal bake recovers source feather relief; the service normal's
green channel was corrected before combining detail. Feathers, feet, keratin, eyes and mouth have separate material
ranges in one atlas. Metallic is zero; packed R stores the engine specular mask, G roughness, B metallic.

All three variants use native palette ramps and anatomical region masks, including their gold, pink-white and red
flames. The installed portable export SHA-256 is:
`0302649403a8b4674ce61a9228eee7ead9a4a28cae485968d749e71e060582f7`.

## Flames and the native renderer

The selected flame is an original imagegen plume retained unchanged as [RGBA texture](textures/phoenix_plume.png),
with its exact prompt and hash in [generation provenance](textures/flame_generation.json). Crossed transparent planes
follow the chest, head, tail and each wing segment. Independent leaf controls animate plume size, strengthen the strike
and extinguish all fire between 0.18 and 0.60 seconds of Death. Dead uses collapsed flame controls.

The flame material uses alpha blending, two-sided rendering, unlit shading and 0.80 opacity. It emits no world light.
UVs are static and clamped: the runtime's skinned shader does not use mesh vertex alpha, so the early scrolling version
clipped plume tips despite looking acceptable in the browser. Static UVs retain the painted soft outline; bone-scale
flicker supplies movement. No renderer change was needed. Earlier lattice-like shells and scrolling plumes are superseded.

## Installation and verification

`assets_source/worlds/mm8/models/mm8_m572.glb` matches the portable export. The cooked model and textures are installed
under `assets_dev/worlds/mm8/models/`. `actors.yml` binds all three IDs to the shared model and their native skins.
Scale A/B is 560.1548593705693; C is 653.5140025989975, preserving the native 7:6 ratio. Calibration averages occupied
front area over all eight native flight frames; [measurement](review/scale/measurement.json) records the calculation.

- Export audit: finite data, normalized weights, four influences, nine clips, closed loops, extinguished corpse,
  three variants, four body/flame/shadow levels.
- Blender reimport: all nine clips sampled against the master; maximum surface error 0.00783 mm.
- Lower LODs: previously sampled at 1/64-second intervals, with positive corpse floor clearance; this revision preserves every pose value and changes only two clips’ timestamps.
- Browser: 27 tier/clip switches passed with no console errors. Eighteen normal/half-speed videos are in
  `review/playback/`, with 108 timed PNG samples and their times. The agent inspected image sequences, not continuous video playback.
- Native OpenGL on NVIDIA RTX 3060 Ti: matching sprite/model cameras outdoors on out05 and indoors on d17;
  all four forced LODs; damage, melee combat, extinguishing death, landing and the normal loot-satchel transition.
  These used isolated one-actor fixtures; production maps were not changed. The outdoor map event labels its first
  actor “Dragon Hunter Pet”, including in the native baseline; the fixture still uses Phoenix ID 130.
- Development build passed. Focused `mm8_phoenix_actor_models_keep_native_tiers_and_simulation` regression passed,
  as did the existing Dragon regression. Logs, exact launch records and representative images are in `review/runtime/`.

Android, Vulkan, continuous human playback review and performance benchmarking were not performed. Source/body motion
and the timing revisions are separately identified in the saved evidence. No user artistic approval is inferred.

## Reproduction and later edits

Claim the existing `mm8:m572` project through `tools/creature_workspace.py` before modifying it, and use the returned
token with the shared Meshy, Blender and review wrappers. Start from the packed master for a local revision; do not
regenerate paid geometry or paint merely to reopen the project.

The retained stage scripts and `work/` checkpoints cover rigging, local motion, silhouette reduction, UV freezing,
texture transfer, AO/normal composition, flame construction and export. `flame_revision_pipeline.py` rebuilds the flame
assembly and portable LOD0 from `work/anim_uv.blend`, then runs `retime_attack.py`; `finish_runtime.py` prepares runtime materials; `build_lods.py`
runs in Blender, then `apply_runtime_ramps.py` writes the final GLB. `reuse_body_lods.py` reuses LODs for revisions with unchanged geometry
and asserts identical body attributes, indices and bind matrices against the saved checkpoint before reusing its LODs.
`animate_phoenix.py --attack-only` updates only Attack/Cast in the frozen `work/anim_uv.blend`, using the original
1.25-second source choreography. `retime_attack.py` applies the selected timing map after export, updates the packed
master and rejects already-retimed input. Do not retime the delivered master twice.
Run `audit_export.py`, `verify_export.py`, and the affected visual checks before reinstalling with `tools/install_model.py`.

Paid Meshy use was **15 credits**: five for Smart Topology and ten for multiview PBR retexturing. Job requests,
task IDs, inputs, hashes and receipts remain in the canonical progress record. The HD references and flame texture
have separate image-generation provenance; that cost is not included in the Meshy total.
