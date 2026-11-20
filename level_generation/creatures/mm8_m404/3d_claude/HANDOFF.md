> Superseded by the completed 2026-10-18 production delivery; see README.md and creature_3d_progress.json.

# MM8 Lizardman Warrior: stopped-session handoff

> 2026-10-18 scoped update: the selected Mixamo attack candidate is recorded in README.md and
> creature_3d_progress.json. The later leg revision adds the source steps and pelvis weight transfer, grounded support, apron follow and tail clearance while retaining the approved upper-body fit. This document preserves the October 15 baseline and its failures.

User explicitly requested on 2026-10-15: “wrap it up, write down your findings for other session to pick up and stop.”
Production is stopped, not complete. Resume production only on a subsequent user request. This handoff and
`creature_3d_progress.json` describe the latest candidate, not an accepted asset. No new production was started
while writing this handoff. The final pipeline had already finished with a gate failure; the temporary preview
server on port 9064 was stopped. The workspace lease is released after saving these records.

## Start here

- Project root: `level_generation/creatures/mm8_m404`; production directory: `3d_claude/`.
- Identity `mm8:m404`; full authorized scope was references, model, equipment, rig, all animations, textures,
  three native tiers, LODs, runtime installation, regression and indoor/outdoor comparison.
- Earliest unresolved prerequisite: exported motion/contact gates (G4/G6).
- Furthest artifact: untextured rigged pilot `export/pilot_combined.glb`, eight clips, separate sword attachment.
- Latest result: **845 PASS / 19 FAIL / 18 INFO / 2 N/A**, in `review/pilot_gates/gates.json` and `gates.md`.
  The old README result 833/31 and older correction-ledger result 825/39 are superseded.
- Meshy: **35 credits consumed of 100**. No body/head retexture job submitted. Do not buy replacement geometry
  or rerig merely because a new session started. Immutable service returns and receipts already exist.
- There is no runtime installation, final viewer acceptance, game check or user artistic acceptance.
- Main time sink: repeatedly optimizing two arms independently while trying to preserve a rigid two-hand grip.
  This traded contacts for wrist/shoulder twists. Avoid repeating broad parameter searches or adding more path
  Gaussians; inspect the actual failing poses and change a small number of authored keys.

Read the current creature-to-3D skill and the full applicable Claude humanoid/texture playbooks on resume.
Reuse selected HD references and existing tools. No commits or staging were requested. The repository already
contained thousands of unrelated dirty paths; do not reset, stage or clean them.

## Latest confirmed failures

Numbers and times below come from the final exported pilot, not from pre-export IK estimates. Penetration is mm,
rotation is degrees, timing is seconds, and other quantities are fractions. Attack2 duplicates Attack.

| Clip | Gate / region | Worst | Time (s) | Required |
| --- | --- | ---: | ---: | --- |
| Attack | blow_speed_fraction  | 0.416916 | 1.09375 | >= 0.8 |
| Attack | blow_time_error_s  | 0.604167 | 1.09375 | <= 0.0208333 |
| Attack | blade_edge_share  | 0.471464 | 1.09375 | >= 0.7 |
| Attack | blade_signed_lead  | -0.45082 | 1.09375 | >= 0 |
| Attack | arm_body_penetration_mm L | 95.1499 | 0.708333 | <= 2 |
| Attack | arm_body_penetration_mm R | 59.0066 | 0.583333 | <= 2 |
| Attack | prop_body_penetration_mm sword | 47.9471 | 0.583333 | <= 2 |
| Attack2 | blow_speed_fraction  | 0.416916 | 1.09375 | >= 0.8 |
| Attack2 | blow_time_error_s  | 0.604167 | 1.09375 | <= 0.0208333 |
| Attack2 | blade_edge_share  | 0.471464 | 1.09375 | >= 0.7 |
| Attack2 | blade_signed_lead  | -0.45082 | 1.09375 | >= 0 |
| Attack2 | arm_body_penetration_mm L | 95.1499 | 0.708333 | <= 2 |
| Attack2 | arm_body_penetration_mm R | 59.0066 | 0.583333 | <= 2 |
| Attack2 | prop_body_penetration_mm sword | 47.9471 | 0.583333 | <= 2 |
| Death | arm_body_penetration_mm L | 7.79012 | 0.208333 | <= 2 |
| Death | cloth_penetration_mm loincloth | 2.03825 | 1.375 | <= 2 |
| Death | prop_body_penetration_mm sword | 31.861 | 0.6875 | <= 2 |
| Death | wrist_flexion_deg R | 60.2359 | 0.375 | <= 60 |
| Death | upper_arm_roll_deg R | 65.1683 | 0.354167 | <= 60 |

The new attack eliminates its previous wrist/upper-arm rotation, head and mantle failures, but **still has severe
arm/body and sword/body intersections**. All grip/palm/finger contact, stretch, feet/floor and gait checks pass in
this export. All attack joint checks pass. Death's right arm/body and mantle contacts now pass, but the changed
right-hand path regressed the left release to 7.79 mm contact and left small right-wrist/shoulder violations.
The 2.038 mm apron contact is a real recorded failure, not permission to relax the 2 mm threshold.

The attack's strongest selected forward tip event is now at 1.09375 s, near the return to guard, with poor speed
fraction/edge lead. The exporter still configures the old 0.4895833333 s impact. **Do not merely set impact to
1.09375 s to clear timing:** fix the intended downstroke and edge alignment, then measure and bind its impact.
The current attack is an experiment, not a selected successful motion.

Latest normal/slow browser playback was on an **older** pilot: 16 clip/speed combinations completed, but the known
motion defects remained. That historical run does not validate this revision. New final playback is required.
The latest clay render batch was not reviewed before the user's stop request; existing images are evidence to
inspect, not an approval. `review/handoff_20261015/last_pipeline.log` preserves the final run and failure exit.

## Selected assets and identity

Native family `m404`, 160 BMP frames with recorded hashes in `../sources.json`. Global descriptors 4/5/6 are
Lizardmen Warrior A/B/C (Soldier, Sergeant, Captain), sprite aliases m405/m406/m407, palettes 405/406/407.
Native standing is `assets_dev/engine/sprites/m404Sa0.bmp` (case matters); standing image bbox [93,58,214,256],
198 pixels including sword; descriptor scale 1.299988. Native standing is upright and narrow, two hands at upper
abdomen, blade diagonally up at about 45–50 degrees. Death keeps the sword in the right hand and releases the left.
Attack2 uses the same sword sprite frames despite Arrow gameplay; preserve that gameplay, do not invent a bow.

Selected body HD views: `references_hd/00_three_quarter.png`, `01_front.png`, `02_back.png`, `03_left.png`,
`04_right.png`; head details under `references_head/`; sword master `references_props/sword.png`.
Native variant study: `../references/native_variants.png`; death study `../references/native_d_v2.png`.
`native_n_v0.png` is Fidget, not Standing. Palette files are `assets_dev/worlds/mm8/textures/Pal405.act` etc.
Only the mantle's semantic colour region changes green/blue/red; preserve red piping, gold throat and skin.

Selected body is front_geometry_v3 (three long digits + thumb), with the better head grafted from dense
multiview_geometry_v2. Assembly is 14,966 triangles, about 1.9 m high, Blender forward -Y. Piece attribute:
0 skin (9250 tris), 1 mantle (1090), 2 belt (332), 3 right bracer (375), 4 left bracer (373),
5 loincloth (230), 6 buckle (116), 7 head (3200). Head seam is near z=1.555 m.
`work/assembled_parts.blend`, `work/assembly.json`, `export/body_for_rig.glb` retain the selected assembly.

Sword: locally authored closed mesh, 932 triangles, about 1.65 m long, local +Y, origin at mid-grip.
Tip 1.405 m, pommel -0.242 m, guard +0.17 m, octagonal handle radius 0.016 m, usable grip +/-0.135 m.
`work/sword.blend`, `export/sword_static.glb`, `textures/props/sword_base.png`, `sword_orm.png`,
`sword_material_classes.png` are retained. Sword is rigidly weighted to `Socket_Sword`.

Meshy jobs (all under `../meshy/`, authoritative receipts in progress JSON):

| Job | Credits | Outcome |
| --- | ---: | --- |
| smart_topology_v1 | 5 | Rejected: thin head, two long digits, overly long tail |
| multiview_geometry_v2 | 20 | Rejected body: duplicate fingers; dense head reused |
| front_geometry_v3 | 5 | Selected body; original weak head replaced |
| body_rig_v1 | 0 | HTTP 422 on neutral upload; no charge |
| body_rig_v2 | 5 | Successful rig after provisional HD projection |

## Motion implementation and findings worth preserving

Local source `anim_library/humanoid_set/2Hand Sword.glb`, SHA256
`aefb79a582a9287afca77227f3d613d09f44ac26cc63f4656f6f4cbb8331f2b5`.
G1 source review is under `review/g1/`. Fitted source-frame rig is `work/rig_v2.blend` (baseline checkpoint).
Roles: Standing=Idle (2 s), Walking=Walk (0.8 s), Attack=Attack1 (1.2 s), Hit=GetHitF1 trimmed to 0.5 s,
Death=Death1 (1.4 s), Fidget=IdleAlert1 (2.333 s); Attack2 copies Attack, Dead holds final Death for four frames.
Do not commit raw animation-library clips. Source world rotations are retargeted onto the fitted rig.

`scripts/motion_fit.py` now bypasses independent arm IK for Attack. It captures the fitted Standing upper-arm,
forearm and hand matrices, then rotates BOTH arms as one assembly about the line through both shoulders, carried
by the current chest transform. Smoothstep angle keys at authoring 30 fps:
`(0,0), (8,-70), (10,-70), (16,+15), (23,+10), (36,0)` degrees. Clavicles keep the Standing local frames.
This preserves elbow/wrist relationships and two-hand grip (pre-export max relative grip error about 7 microns).
The old Attack IK/path code below that branch is dead code; remove it after a successful replacement is selected.
The follow-through still intersects the torso. Inspect actual 0.58–0.71 s poses before editing that arc.

`posture_timing.py` reduces Attack pelvis/spine/neck/head source displacement to 25% to match native facing.
Previous full/70% torso turns put shoulders almost front-to-back, making the grip solver fight the body.
Attack/Death source clavicle amplitudes are 25%; new Attack overrides clavicles with Standing frames.
Standing/Fidget lower body is 12% source with tiny pelvis breathing; Walking torso/head 35%, pelvis/clavicles 30%.

Death still uses the independent arm fitter. In chest-relative coordinates, the right-hand centre interpolates
from guard towards `(-.62,-.25,1.35)` over frames 3–15 with a `-.16*sin(pi*t)` forward bow. Blade passes through
forward `(0,-1,.1)` orientation before pointing down `(-.1,0,-1)`; direct guard-to-down rotation pierced the body.
Left release is frames 3–9, free wrist target chest-local `(.58,.08,1.13)`, with an outward bow of .24 m and
gradual local hand/finger relaxation to identity. Its held-contact gate interval is only 0–0.1 s. Moving the
right path farther out fixed its arm contact but changed the early left release and did not clear the blade.

Other clips use constant fitted controls with nine cost samples (the final export/check still samples densely).
Dynamic fitting uses a grid over elbow phase and hand roll with actual relative joint-quaternion continuity
penalties. Independent IK arithmetic was checked against the analytic pose: 0-degree rotation discrepancy and
about 2-micron position discrepancy. Blender/export parity was also verified near floating-point precision.
The continuing failures are motion/anatomy constraints, not an established exporter coordinate bug.
Do not keep adding Gaussian offsets or blindly densifying the search. The left/right clearance cost currently
uses a uniform .215 m radius, which may be excessive near wrists; actual posed meshes remain authoritative.

Preserve these successful corrections:

- Four normalized influences, matching runtime. Excess distal Clavicle weight moves to UpperArm across the
  0.02–0.12 m shoulder-to-elbow region; this fixed arm stretch p99 failures.
- Hand ownership becomes complete by about 5 mm after the wrist. Finger contact uses the actual weighted
  barycentric samples, not neighbouring palm skin. Left grip centre moved 1.5 mm along negative palm normal
  to compensate octagonal flat variation; do not apply that shift twice.
- Finger roots are 0/1/2/4. `grip_surface.py` skips reoptimization when already below 2 mm gap / 1 mm penetration,
  but always measures and only publishes under the 3 mm acceptance limits.
- Forearm twist share .6, ramp 0–.12; upper-arm countertwist -.5, ramp 0–.60, continuous angle unwrap.
- Feet are corrected at quarter frames. Fixed Standing soles, Walking toe lift .102 m, source foot XY *.5,
  root support .002 m, tail floor .001 m. Preserve dense export/interpolation. Measure final gait stride;
  source foot shortening might look too small at runtime speed. Running has not been authored.
- `finish_cloth.py` owns `B_Loincloth`, parent Pelvis, entire piece 5. It follows the leading thigh angle,
  plus 8 degrees, clamped to 80 degrees; it still barely clips late Death. Do not thin the cloth to hide it.
- Left contact interval for Death is authored in `export_pilot.py`, which regenerates `pilot.gates.json`.
  Edit the exporter source for persistent config changes, not just its generated config.

Shared gate changes this session are in `../../claude_shared/gates/run_gates.py`, `test_gates.py`, `README.md`
(paths from this production directory). They cover configurable finger roots/palm normals, wrist neutral after
twist, float64 closed-ray parity with signed coincident-hit handling, and proximal-knuckle-transported curl sign.
The shared checker suite had 15 passing tests. No thresholds were relaxed to accept known intersections.

## Reproduction and checkpoint chain

On a later authorized resume, claim a NEW token; the old session's token is released:

```sh
python3 tools/creature_workspace.py claim --project level_generation/creatures/mm8_m404 --identity mm8:m404 --owner codex-lizardman-resume --state 3d_claude/creature_3d_progress.json
```

Use the returned token with the existing wrappers. Never nest the guarded Blender wrapper in another guard.
All project edits use `creature_workspace.py run --project ... --token ... -- <command>`.
Blender wrapper accepts `tools/run_creature_blender.sh --token <NEW_TOKEN> <project-script.py>`.

`contact_pilot_pipeline.py` runs motion_fit, tail_fit, twist_bones, weights_body, floor_finish, finish_cloth,
audit_motion, grip_surface, apply_surface_fingers, export_pilot and independent gates. It takes several minutes
and writes the latest checkpoints/reviews. `chest_path_pipeline.py` first rebuilds posture_timing, then runs it.
Use that only when posture changed; otherwise run contact_pilot_pipeline. `weighted_contact_pipeline.py`
rebuilds the surface-cost data before that chain when relevant weights change.

Checkpoints:
`rig_v2 -> rig_weighted -> rig_fingers -> rig_stance -> rig_grip -> rig_tail -> rig_twist ->
rig_weighted_final -> rig_motion` under `work/`. The current pipeline starts from rig_stance.
Pilot export is 120 fps with LINEAR sign-continuous quaternions (authoring frame keys multiplied by four).
It exports body and sword, then splits `Socket_Sword`. The exporter defines all gate selectors and config.
No need to rerun the whole several-minute pipeline just to inspect a failed pose.

Temporary `/tmp/lizard-*.py` files are old one-off mutations and diagnostics, not a supported build chain.
Do not rerun mutation installers: several are non-idempotent, obsolete or would overwrite current fixes.
Some diagnostics execute a prefix of motion_fit and no longer work after its Standing-dependent attack branch.
All essential authoring code is already under `scripts/`; `/tmp` is not needed to resume production.

## Prepared but unexecuted finishing work

These scripts exist but have NOT produced accepted results; inspect their assumptions before running:

- `reduce_rigged.py`: rig_motion -> rig_reduced, targets skin 6200, mantle 800, belt 220, each bracer 260,
  apron 230, buckle 80, head unchanged 3200 (~11k). Protects head/neck/hands/fingers/feet; decimates before
  Armature, limits to four influences. Recheck contacts and appearance after reduction.
- `export_uploads.py`: freezes neutral body upload plus separate head upload; saves rig_uv_master;
  head Smart UV 66 degrees, margin .01. Uploads intentionally omit rig/sword/animations.
- `requests/body_retexture_v1.json` and `head_retexture_v1.json`: Meshy7, PBR 2K, four selected HD views.
  Body uses new UVs, head preserves original UVs. Correct API key is `multiview_image_urls`.
  Planned 10 credits each, neither submitted. Use run_creature_meshy.sh and recorded budget/receipts.
- `transfer_uv.py`: AABB scale/translation and nearest face/corner correspondence with unique-face/count
  and <0.0001 m error assertions. `uv_raster.py` and `bake_ao.py` prepared for body UVMap and head HeadUV.
- `export_runtime.py`: expects rig_textured and 1K body/head basecolor, normal, metal_rough maps;
  copies HeadUV to its exported UVMap, joins body/head/sword materials, exports eight 120 Hz clips.
  Inspect this prepared script before use; it has not run. Sword maps already exist.

After motion succeeds: reduce/verify, body+head textures/UV transfer, colour/seam/material review, native mantle
mask and palette ramps, final GLBs/LODs/attachment split, viewer review, install, binding and runtime checks.
Material contract is **ORM red = specular mask, green = roughness, blue = metalness** with
`openyamm_specular_mask: true`; AO is baked into base colour. Use shared textures and one padded region mask,
not separate runtime per-tier textures. Keep head detail and neck seam coherent. Sword is separate equipment.

Use existing helpers: prepare_actor_glb, build_actor_lods, shadow fix, region variants, attachment split and
head-material merge as required by the current playbooks. The LOD helper's Python generate function supports
ratios (.5,.25,.125) and four influences; its CLI defaults are more aggressive. Generic decimation does not
protect hands: verify coarse grip contacts and preserve those areas if necessary, rather than relaxing gates.
Final merged-material gate regions can use component_seeds, vertex selections/lod_regions or cloth bone weights.

Reuse the existing shared viewer (for example mm8_natm), not a new custom viewer. The previous temporary viewer
needed import URLs beginning `./vendor/` and manifest `feedback: "feedback.json"` to start correctly.
Its `/tmp/pilot.glb` snapshot and playback evidence are stale. Check the eventual final project viewer at normal
and 0.25x speed, all eight roles, three tiers and useful views, after all exports/material changes.

Install final accepted source GLBs with `tools/install_model.py ... --world mm8`; never copy into assets_dev or
copy cooked runtime files back into authoring. Current installer already has COOKED_MODELS=("*",), newer than
older repository instructions describing uncooked creatures. Source is under assets_source, runtime under assets_dev.
No existing m404 binding was found. Append only descriptors 4/5/6 in `assets_dev/worlds/mm8/models/actors.yml`.
Proposed names: mm8_m404.glb, mm8_m404_sword.glb, M404, Socket_Sword, skins m404_a/b/c; yaw -1.570796327.
Derive scale from 198 native pixels * 1.299988 / final Standing visible height; verify body and sword together.
Set upper-body root B_Spine and look bones B_Neck/B_Head; measure stride and actual strike timing before binding.

Focused actor regression examples are in game/outdoor/HeadlessOutdoorDiagnostics.cpp near the MM8 Dark Elf and
Lizardman Peasant cases (~7870/7981 at this session). No C++ or actor-table change has yet been made for this work.
Use normal build (`cmake --build build --target openyamm -j25`), focused headless regression and approved native
GPU launcher. No Vulkan build. Example native comparison cameras: MM6 6d19 indoor (1672.832,-2938.578,-46.896),
yaw 3.132, pitch -14.868 degrees; oute3 outdoor (-3718.493,3245.946,1), yaw 3.359, pitch -13.751 degrees.
Mount MM8 art/global actor data and spawn IDs 4/5/6 for tier comparisons. Review existing mm8_m432_claude in-game
capture notes and tools/RUN_GAME.md for the actual test setup. Native sprites versus 3D, indoor/outdoor, attacks,
hit/death/corpse and all tiers remain unchecked. Renderer changes are outside this asset task.

## Snapshot identities at stop

Canonical progress is in `creature_3d_progress.json`; these hashes make this handoff's evidence revision explicit.
Do not infer acceptance from filenames such as `rig_weighted_final` or from successful process completion.

| Role | Path (relative to 3d_claude) | SHA256 |
| --- | --- | --- |
| animation_master | `work/rig_motion.blend` | `cee33b1c341854380357b543f2c172992bdfc29702cb9d6acf6cbf545e6bd7f1` |
| fitted_source_rig | `work/rig_v2.blend` | `d5df9cce99b4f5795077b86a85ab3913474d230316d5f223e47f8abd5e8b9f4f` |
| assembled_geometry | `work/assembled_parts.blend` | `80ef8efbf26601472be7649cffabae59cace7b34287dc0461aa52510fcae76c2` |
| portable_pilot | `export/pilot_combined.glb` | `854bade78b90a22e4c1b4313a1c78c189874dc400f50787e7a0fad556ce526b5` |
| pilot_body | `export/pilot_body.glb` | `90861bc8ecbb5726870a52e04d743f98040401ea97fe0eb605875e40fae9475e` |
| pilot_sword | `export/pilot_sword.glb` | `d1cbe8fe1f39434aa61bee78f3c6726ffb365c4f50525bce31aac8a2608ca9d8` |
| gate_report | `review/pilot_gates/gates.json` | `4997d77aa980e87c8d80fe34e5a2381fa8ec1746029b481eaa0c1b4804615edb` |
| motion_authoring | `scripts/motion_fit.py` | `788501754026bfe53c861700fd4aa2ebc03940f018f74b5e8848663931d2a67d` |
| posture_authoring | `scripts/posture_timing.py` | `3656524ae9a20f88f7b813596ec3df1c232b1b6124a6a0b709c829ce62f249c5` |
| cloth_authoring | `scripts/finish_cloth.py` | `f920d62af49bc11b32c0c17f729f596b868c55ee6a48a6d4913086bcb3a0ae55` |
| pilot_exporter | `scripts/export_pilot.py` | `271986b87db89ce82de20363755ecabd2c1c4ab87e50c2f2aac5cd8e264fb7ee` |
