# Meshy rig diagnosis and local repair — 2026-09-24

Input: `/home/pjasicek/Downloads/Meshy_AI_mm6_goblin_10577_mesh_All_Animations.glb`.
The original is preserved here as `meshy_returned.glb`.

## Skirt clearance v3 — current candidate

The thigh penetration reported in `test_img/2034.png` is corrected with baked hinge motion for the 17 strips.
[Updated files, comparison and checks](skirt_clearance/README.md). The mesh remains 10,577 triangles; the rig now
has 45 joints and five clips. This supersedes v2 as the current local review candidate.

## Upright correction v2 — previous candidate

The screenshot `test_img/2033.png` correctly exposed a remaining lateral animation bias.
The previous repair centered the bind skeleton but did not fully correct torso motion alignment.
Forty-eight samples per clip measured approximately -5.03 degrees in idle, -5.07 in walk,
and -5.63 in run (head-to-hips lateral line, relative to root heading).

A constant 5.05-degree torso correction about the pelvis removes the persistent offset while preserving
cyclic sway. Shoulder neutral rotation offsets were calibrated from idle/walk; this is an authored posture
adjustment. Restpose now explicitly keys location, rotation and scale so earlier clips cannot leave offsets.

Current files:

- [Upright animated GLB](mm6_goblin_10577_rig_upright_v2.glb)
- [Editable Blender scene](mm6_goblin_rig_upright_v2.blend), `Goblin - Upright Rig Review`
- [Front-view comparison](upright_audit/posture_comparison.jpg)
- [Neutral rest mesh](upright_audit/neutral_rest.png)
- [Before measurements](upright_audit/posture_report.json), [after measurements](upright_audit/posture_v2_report.json)
- [Final export verification](upright_audit/export_verification.json)

Mean lateral lean is now +0.016 degrees idle, -0.016 degrees walk, and -0.583 degrees run.
Walking retains approximately -2.22 to +2.54 degrees of sway. Mean shoulder height difference is
2.3 mm idle / 2.9 mm walking. These measurements describe skeleton alignment, not exact mirrored surface symmetry.
The original sculpt has small side-to-side differences; the pouch/equipment and moving limbs are also asymmetric.
No mesh mirroring was performed.

Final GLB reimport: 10,577 triangles, 28 joints, five `Goblin_Upright_` actions. Twelve pose samples per
clip match the authored joint positions within 0.008 mm. Reimported idle/walk/slash stills were visually checked.
This supersedes the v1 posture assessment; originals and v1 deliverables remain preserved.
Existing grip, authentic motion, material and runtime acceptance work remains outstanding.

## Previous repair v1 files

- [Repaired animated GLB](mm6_goblin_10577_rig_repaired.glb)
- [Editable Blender file, five actions stored on muted NLA tracks](mm6_goblin_rig_repaired.blend)
- [Idle / slash comparison](repair_comparison.jpg)
- [Walk comparison animation](walk_comparison.gif)
- [Slash comparison animation](slash_comparison.gif)
- [Walk sampled frames](walk_comparison_frames.jpg), [slash sampled frames](slash_comparison_frames.jpg)

**This is a local rig repair candidate, not final game-asset acceptance.** The same accepted geometry is retained.
No further automatic remesh is justified by the demonstrated rig faults.

## Findings

The imported mesh looks intact with the armature in REST position. Warping appears with the animation skinning.
The upload had 10,577 triangles; Meshy's returned model has 10,372, 28 joints and five animation entries.
The removed 205 triangles were not accepted as an intentional topology change.

The bind skeleton is visibly misplaced through the torso: the lower spine is offset by about 5.8 cm to one side,
the upper spine by about 8.0 cm, and the neck base by about 8.7 cm, at Meshy's normalized 1.7 m model height.
This is an offset relative to the body centerline, not evidence of a triangle-budget shortage.
The supplied restpose action matches the supplied bind matrices, so a simple import/restpose reset does not fix it.

Regional weight audit found:

- Head vertices above z=1.48: mean Head 71.2%, Neck 21.1%, **RightShoulder 5.2%**, plus terminal/head helpers.
- Central neck: mean **RightShoulder 24.1%**, plus unrelated arm influence.
- Belt sample: mean Hips 58.1%, thighs together 28.9%, Spine 13.0%.
- Hand vertices assigned to terminal `HandMiddle4` helper bones despite no articulated finger chain.

See [bone inventory](blender_inventory.json), [weights audit](weights_audit.json), and
[rest-pose identity check](restpose_deformation.json).

## Repairs made

1. Rebuilt a centered torso/neck bind chain. Kept the useful arm/leg joint locations and existing 28-bone naming.
2. Retargeted the supplied motion rotations onto this skeleton. A constant alignment correction was derived from
   five idle samples for head orientation relative to the chest (~37.9 degrees) and foot orientation (~30.8/36.5 degrees).
   This is an authored neutral-posture choice; it does not establish that Meshy's source motion intended that pose.
3. Gave the head coherent head-bone weights and restricted the neck to chest/neck/head influences.
4. Removed terminal hand/toe helper influence; made feet rigid below the ankle transition.
5. Anchored belt and pouch to the hips; limited thigh influence on hanging strips. Both inner and outer garment
   surfaces are included, with matching weights on coincident UV-split vertices to avoid seams pulling apart.
6. Adjusted covered waist, shoulder caps, bracers and wrist transitions so rigid equipment bends less.
7. Restored the accepted **10,577-triangle geometry and original normal atlas**. Corrected weights were transferred
   from the returned surface; nearest-source distance was under 0.887 mm for every vertex (mean ~0.0113 mm).
8. Baked the five motion clips at the imported scene's 24 fps, with linear key interpolation and quaternion
   sign-continuity checks. No triangle reduction or subdivision was used.

[Retarget details](retarget_report.json), [geometry/weight-transfer measurements](geometry_restore_report.json).

## Verification

The repaired GLB was exported and imported into a fresh Blender scene. It contains **10,577 triangles,
28 joints, and five animation clips**: Idle_3, Walking, Running, Right_Hand_Sword_Slash, and restpose,
with `Goblin_Fixed_` prefixes. Idle and slash stills and twelve samples each across walk/slash were rendered
from the reimported GLB and visually compared against the unchanged Meshy return.
[Reimport report and hash](reimport_report.json).

Running is included and structurally exported, but did not receive the same full-cycle visual review in this pass.
The local fixes visibly improve the head/neck alignment and equipment deformation. The first weights-only
experiment did not fix the bad head alignment and is superseded by this centered-rig version.

## Remaining production work

- Review foot contact, shoulder/underarm transitions and skirt/leg intersections through the intended game motions.
- Add actual finger/grip controls and the separate sword; the returned rig contains terminal hand helpers, not finger chains.
- Recreate or adapt the authentic MM6 slash, hit, death and fidget. This generic sword slash is still a rig test.
- Clean the pre-existing normal-map marks/jewelry and generate authentic color/material maps.
- Runtime skeletal skinning/material integration remains separate engine work.

Do not run another paid Meshy rig/remesh retry for this repair. Keep the accepted low mesh and corrected local rig
as the current candidates. A later Meshy texture pass should use the preserved unrigged UV-compatible upload;
its material result can be applied to the local rig without replacing the repaired skeleton.

Scripts under `scripts/` record the diagnosis and repairs and depend on named working Blender scenes.
