# MM8 Minotaur — two-handed revision

> **Installed model reduced and attack replaced (2026-10-19):** the installed body and axe are now the reduction from [`../mm8_m484_reduce_claude/`](../mm8_m484_reduce_claude/README.md) (LOD0 9,253 + 1,772 -> 6,751 + 1,130). On user review the two-handed Attack was deleted; the original one-handed attack, reworked to cut through the front centre with the head facing forward (1.1 s, impact 0.6667 s), is now Attack and Cast. The two-handed notes below describe the superseded version; `motion_selection.json` is historical. Rollback sources are in `../mm8_m484_reduce_claude/work/`.

Family `m484`, descriptors 64–66: Minotaur Guard, Warrior and Battleleader. Created using the shared Claude humanoid,
HD-reference and texture playbooks. MM6 Minotaur supplied rig/motion workflow references; MM8 sprites supplied anatomy,
outfit, palette and scale. The two-handed attack is the gameplay default; the original one-handed attack is retained as an alternate at the user's request.

## Deliverables

- [Review viewer](http://127.0.0.1:8767/level_generation/creatures/mm8_m484_claude/review/viewer/): three tiers, ten clips,
  normal/slow playback and feedback capture.
- `delivery/mm8_minotaur.blend`: packed, editable 69-bone rig and textures.
- `export/mm8_m484_lod0.glb`: portable assembled model, ten animations baked at 60 fps.
- `export/mm8_m484.glb` and `export/mm8_m484_axe.glb`: game body and separate Axe attachment, three reduced LODs each.
- `delivery/manifest.json`: selected file hashes and technical evidence. `creature_3d_progress.json` is the continuation record.

| LOD | Body triangles | Axe triangles | Total |
| --- | ---: | ---: | ---: |
| 0 | 9,253 | 1,772 | 11,025 |
| 1 | 4,616 | 886 | 5,502 |
| 2 | 1,647 | 318 | 1,965 |
| 3 | 533 | 100 | 633 |

The engine's established actor ratios (50%, 18%, 6%) replace successive 50% reductions for the distant/shadow levels.
Torso/head/arms and pelvis/legs remain closed underneath the separate mail kilt. Axe blade openings are real geometry.
The source-frame rig has fitted joints, connected finger weights, four influences per vertex, forearm/upper-arm twist helpers,
12 kilt bones and an Axe socket. Accepted geometry and UVs were preserved during the two-handed revision.

## Motion and appearance

Attack uses the reviewed local `2Hand Axe.glb:2HandAxeAttack1` overhead action as its motion reference. Its chamber and handle
path are fitted around the broad bull head and short arms; both hands grip through the chop and recovery. The upper hand
slides 12 cm along the handle during the downswing. Attack and the native self-buff Cast alias each last 1.667 seconds.
The other roles are Standing (2 s), Walking (0.8 s), Running (0.733 s), Hit (0.5 s), Death (2.467 s), held Dead (1 s) and
Fidget (1.2 s). `AttackOneHand` (0.867 s) preserves the original fitted one-handed attack from
`work/gated_master_onehand_v1.blend`; it is selectable in the viewer and included in the editable Blender file and
installed GLB, without a gameplay binding. Death retains the axe in the right hand. Detailed source selection is in `motion_selection.json`.

Rust-brown bull, red-tipped ivory horns, long mane, silver nose ring and bracers, black crossed harness/belt, mail kilt and
cloven hooves. Only the mail changes tier: native palettes 485 brass, 486 silver and 487 yellow gold. Body and head use
shared base colour/normal/specular-roughness maps, packed into a 2080×1024 runtime atlas; the axe uses 512×1024 maps.
Body/head UV overlap and degenerate UV triangles are zero. Normal green polarity was measured against the source maps;
MR red carries the runtime specular mask and metallic is zero under the current engine contract.

## Checks and installation

Half-frame contact, wrist, floor and deformation checks cover the nine gameplay clips. Quarter-frame samples additionally check both
hands against the axe handle. `review/upperarm_contacts.json`, `final_stretch.json`, `final_motion_gates.json`,
`twohand_grip.json` and `export_parity.json` record actual measurements. Sub-millimetre closed-finger compression against the
shaft is retained. Arm stretch p99 peaks at 2.024 and hand maximum at 3.237. Grip centres match within 0.002 mm at baked keys; left-grip interpolation drift peaks at 5.18 mm between keys, visually reviewed at that frame with the shaft still inside the closed hand. No visible body/weapon intersection was accepted. The run contains a deliberate flight phase. Death and
its held corpse meet the ground, and the weapon remains attached.

The alternate revision preserves all nine gameplay clips, mesh attributes, indices and weights bit-for-bit in both
portable and runtime exports (`review/alternate_preservation.json`). Fresh export/reimport checks cover all ten clips;
`AttackOneHand` has 53 samples with a maximum surface difference of 0.049 mm. Normal/quarter-speed alternate playback,
all 30 tier/clip switches and the focused Minotaur runtime regression passed. Native captures were not repeated for
this unbound alternate; the existing gameplay clips are unchanged. See `review/playback_alternate/`,
`alternate_viewer_check.log` and `alternate_regression.log`.

Installation uses `tools/install_model.py --world mm8`: accepted sources live in `assets_source/worlds/mm8/models/` and
cooked runtime models in `assets_dev/worlds/mm8/models/`. `actors.yml` binds all three tiers, native action roles, measured
impact timing, head look and Axe attachment. Standing scale is 173.2569363302: native 206 pixels × sprite scale 1.5 / fitted
1.783478379 m head height. Walking/running strides are 1.365/2.239 m.

The desktop build, MM8 actor regressions, browser playback and native GPU captures are recorded under `review/`.
Native captures use the ordinary OpenGL/NVIDIA desktop launcher and isolated settings/saves. See `review/ingame/README.md`
for camera records and comparison limits. Steep outdoor slopes can leave parts of the flat corpse pose above or inside terrain; terrain-following corpse deformation is an existing engine limitation and was not added here. Android and Vulkan were not tested. User artistic acceptance is not yet recorded.

Meshy spending: **30/100 credits** (Smart Topology 5, rig 5, body/head retextures 10 each). One rejected texture request cost
zero. No paid animation jobs were needed; raw local-library clips remain outside committed assets.
