# MM8 Pirate Warrior — m412

Created and installed on 2026-10-15 using the shared Claude humanoid and texture playbooks. This is the male sword
Pirate, including the three ordinary and three Wimpy descriptors (IDs 10–12 and 181–183). Original sprites are
unchanged. The user-reported Running knee collapse was repaired on 2026-10-15. Agent verification is complete; user review of this revision remains pending.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m412_claude/review/viewer/) ·
[Viewer entry](review/viewer/index.html) · [Canonical progress](creature_3d_progress.json).
The viewer uses the existing repository-root server and shared three.js assets. Its tier textures are review-only
bakes of the runtime ramp rule; the installed models share one texture set and use native palette ramps.

## Selected assets

- Editable, packed rig: [work/pirate_final.blend](work/pirate_final.blend), 42 bones, eight clips.
- Final body: [export/mm8_m412.glb](export/mm8_m412.glb).
- Separate cutlass: [export/mm8_m412_cutlass.glb](export/mm8_m412_cutlass.glb), attached to `Sword`.
- Source installs: `assets_source/worlds/mm8/models/mm8_m412*.glb`.
- Cooked runtime installs: `assets_dev/worlds/mm8/models/mm8_m412*.glb`, using `tools/install_model.py` and desktop
  texture cooking. Never edit the runtime files or copy them back over a source.
- [Bindings](integration/actors.yml), merged into `assets_dev/worlds/mm8/models/actors.yml` without replacing other
  creatures; [install hashes](integration/install_receipt.json).

The anatomical right hand holds the cutlass. The left arm ends in a rigid hook and socket; it deliberately has no
finger rig. The eyepatch covers the right eye. Native palettes 413/414/415 recolour the bandanna, sash and sword grip
in green/blue/red. Face, shirt, trousers, boots, leather and metal retain their own materials. Head and body use a
merged 2080×1024 atlas, UV0, green-corrected tangent normals and ORM with specular mask in R, roughness in G and zero
metalness in B. The prop retains its own material and matching variants.

| Detail level | Body triangles | Cutlass triangles |
| --- | ---: | ---: |
| 0 | 11,877 | 900 |
| 1 | 6,323 | 414 |
| 2 | 2,573 | 162 |
| 3 | 842 | 54 |

Body colour and shadow chains have four levels. Level zero exceeds the usual 5–8k humanoid aim to retain the fitted
fingers and close-up face; it stays below the 15k source target. Distant LODs intentionally simplify individual
fingers. The standing scale is 139.882698, derived from the native 197-pixel silhouette × SFT scale 1.199997 versus
the measured posed model height 1.6899832 m. World height is 236.4 units. See [scale/stride](integration/scale_stride.json).

## Motion and provenance

| Role | Duration | Source |
| --- | ---: | --- |
| Standing | 3.000 s | Local Mixamo Standard Idle |
| Walking | 1.000 s | Local Mixamo Walk |
| Running | 0.733333 s | Local Mixamo Standard Run |
| Attack | 1.766667 s | Local Mixamo Sword And Shield Slash, with ready lead |
| Hit | 0.500 s | Local humanoid set UnarmedGetHitF 1 |
| Death | 3.633333 s | Local Mixamo Standing React Death Backward |
| Dead | 1.000 s | Held final Death pose |
| Fidget | 2.833333 s | Local Mixamo Standing Taunt Battlecry, fitted entry |

No animation purchases. Native timing remains gameplay-authoritative. Melee and ranged presentation use the same
sword action, with the measured impact at 0.989583 s against the native 1.0 s action. The signed cutting-edge
alignment is 0.988; impact tip speed is 30.26 m/s, 98.2% of the peak. The right fist stays on the grip throughout.
Walking stride is 1.588725 m and running stride 3.879521 m per full cycle, measured from planted-foot speed.
Ordinary Pirates use Walking at their table speed; Running is available for sufficiently fast movement.

The rig copies source frames with fitted joint positions. Meshy provides the body and joint proposal, with local
wrist/ankle/finger fitting and weight repairs. Retargeted world rotations retain authored motion. Standing, attack
and fidget feet were levelled; the Fidget entry was changed to prevent crossed sleeves. Running retains the source
leg paths, with vertical clearance fitted from source heel/toe contacts. It does not use the earlier synthetic run
experiment. The cutlass was built locally from the generated prop reference; its knucklebow was fitted toward the
fingers to clear the right cuff.

[Native inputs](references/sources.json) record all 160 unchanged BMP hashes and native palettes/timing.
[HD masters](references_hd/) and [motion selection](references/motion_selection.json) record the selected identity,
references and local clip hashes. Meshy used **30 / 100 credits**: topology 5, joint proposal 5, body texture 10,
head texture 10. Four completed jobs and their downloads are retained in `meshy/` and canonical progress.
No paid regeneration or unused animation job was started.

## Verification and limits

- Development `openyamm` build passed. Added focused regression `mm8_pirate_actor_models_keep_native_roles` in
  `game/outdoor/HeadlessOutdoorDiagnostics.cpp`: all six heights, eight clip durations, attachment bone, LODs and
  presentation state isolation. [Pirate pass](review/regression/pirate.log).
- Existing [MM6 peasant](review/regression/mm6_peasants.log), [MM8 Dark Elf](review/regression/mm8_dark_elf.log), and
  [MM7 indoor/outdoor lifecycle](review/regression/mm7_map_lifecycle.log) checks passed.
- [Viewer check](review/viewer_check.json): all 24 tier/clip combinations, zero browser errors. Real playback was
  reviewed at normal and half speed; final Running and final detail captures are retained separately. Earlier
  all-clip playback precedes only the final run vertical adjustment and UV channel cleanup, not the contact repairs.
- [Full-detail checks](review/gate_assessment.json) pass on every clip: arm p99 stretch ≤1.9942×, hand stretch ≤1.744×,
  wrist flexion ≤59.48°, forearm roll ≤70.01°, grip gap ≤2.935 mm, grip penetration ≤0.961 mm, no measured arm/body,
  prop/body, head or floor penetration. Imported final export and source-relative motion are measured at subframes.
- **The unmodified shared batch checker still reports FAIL**, with 4,966 PASS, 140 INFO, 136 UNVERIFIED and 488 FAIL
  rows (including repeated colour/shadow skeleton checks). Its raw [report](review/gates_contacts/gates.md) is retained.
  [Assessment](review/gate_assessment.json) explains each category: absent left palm/fingers, fixed local-axis palm/
  hinge proxies, authored knee/lift/yaw ranges, fast source actions, stricter 10 mm resting/40 mm flight preferences,
  and distant LOD fingers. These results are not relabelled as a full batch pass. The resting sole maximum 13.44 mm
  is within the playbook’s ±20 mm. Running has genuine flight: 68.67 mm worst lower-foot clearance in the exported
  samples; 47.16% contact at the checker’s 10 mm band. Source-relative rotation data is in
  [source_motion_comparison.json](review/source_motion_comparison.json).
- Native game captures use the NVIDIA GPU (`vendor=0x10de`), OpenGL 3.3, SDL Wayland and engine PNG readback.
  [Outdoor 3D](review/ingame/out_3d/t0.png) and [native sprites](review/ingame/out_sprite/t0.png) compare the three
  palettes in New Sorpigal. [Indoor three tiers](review/ingame/in_3d/t0.png) verifies the common model renderer.
  The final [Stronghold native](review/ingame/stronghold_native.png) and
  [Stronghold 3D](review/ingame/stronghold_3d.png) comparison uses the same saved MM8 map state and camera.
  Animation phase is live and can differ between captures. Logs and run records are retained under `review/ingame/runs/`.

Console-spawned Pirates were invisible in the MM6 indoor sprite-only check, including after quickload; the 3D actors
were visible. Native placed Pirates in MM8’s Stronghold render correctly and supplied the indoor comparison.
This existing spawn/sprite-path issue was not patched as part of asset production. Existing stale outdoor lighting
bake and unrelated Lich-atlas warnings were observed in MM6 logs; no release or lighting rebake was performed.
Android and Vulkan were not built or run. No commit or staging action was performed.

## Re-export

Acquire this creature’s lease first. The selected authoring checkpoint is `work/master_knees.blend`;
`work/pirate_final.blend` is the packed delivery scene. Using the existing guarded workspace/Blender wrappers, run:

1. `scripts/repair_knees.py` from the preserved `master_grounded_delivery.blend`, then `scripts/export_runtime.py` — sole runtime UV channel, eight actions and 120 Hz retained contact keys.
2. `tools/prepare_actor_glb.py export/mm8_m412_lod0.glb export/mm8_m412_prepared.glb` — PNG maps and normal convention.
3. `scripts/build_lods.py`, then `scripts/finalize_exports.py` — shared LOD tool plus `refine_knee_lods.py`, native ramps, split prop, merged head.
4. `scripts/viewer_tiers.py`, then `scripts/viewer_manifest.py` — review-only tiers and hashes.
5. Recheck gates/viewer; install both exports with `tools/install_model.py <export> --world mm8`; rerun the focused
   regression and affected game captures. Existing bindings need no change unless scale, stride, clips or impacts change.

Paths in the Python scripts resolve from this project. The command in step 2 is illustrative relative to the project;
invoke the repository tool with the full project export paths. Geometry repairs are preserved in the earlier scripts
and checkpoints; do not rerun old `motion_v1/v2` or synthetic running experiments over this selected result.

## Running knee correction — 2026-10-15

The user identified a dislocated-looking anatomical right knee at viewer frames 14–19 (48 fps), clearest at frame 16.
The fitted right knee was 77 mm from the trouser ring centre, and planar reduction had removed the edge rows needed
for a deep bend. Dual-quaternion skinning alone did not fix the long triangles. The repair fits both knee centres,
restores local bend rows and smooth thigh/calf weights, then rebakes the existing world rotations at 120 Hz. It adds
no bones, animation purchases, textures or engine changes. Sole/floor clearance is maintained while fitting the
new segment lengths; standing scale and measured walking/running strides were recalibrated.

The LOD reducer also removed bend rows, so the local export now restores UV- and weight-interpolated knee cuts after
reduction. LOD1 reserves its budget with a 0.46 base ratio. Final body counts are 11877/6323/2573/842 (53.2%,21.7%,7.1%
of full detail); the body remains below 15k. Submillimetre cut fragments are welded in the authoring mesh.

[Correction evidence](review/knee_fix/README.md) contains the final frames 13–19, all-clip playback, both knee swing
extremes at every LOD, a 120 Hz curvature regression, final asset hashes and native game captures. The full-detail
worst edge-to-skinned-midpoint deviation fell from 64.51 to 5.49 mm. This test measures lost bend curvature; the earlier
edge-stretch checks alone did not catch this defect. The shared batch report remains FAIL with the documented
source-motion/prosthesis/distant-LOD exceptions; this repair does not relabel it as a full pass.
