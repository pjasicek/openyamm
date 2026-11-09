# MM6 goblin — Corsair-inspired sword, articulated grip and native attack

## Current review files

- [Standalone Blender project](mm6_goblin_corsair_attack.blend)
- [Animated character GLB](mm6_goblin_corsair_attack.glb)
- [Separate reusable sword GLB](corsair_goblin_sword.glb)
- [Front / oblique attack playback](attack_preview.gif)
- [Native six-pose comparison](attack_comparison.jpg), [all whole-frame poses](attack_frames.jpg)
- [Grip palm](grip_palm.png), [grip side](grip_side.png), [grip back](grip_back.png)
- [Reimported windup](export_windup.png), [reimported follow-through](export_followthrough.png)

Open the Blender project and press Space: scene **Goblin - Sword and Native Attack**, action
`MM6_Goblin_Attack`, frames **1–37 at 48 fps (0.75 seconds)**. The saved pose is frame 7.
The Action Editor contains the five delivery clips; muted NLA tracks retain each action in the project.
Viewport overlays are disabled for an unobstructed character review; enable them to inspect/edit bones.

## What changed

1. Built an original 540-triangle curved sword using Corsair's shape, gold guard, dark grip and red pommel inset.
   Merged item **1305** resolves to `7item220.bmp`; this is the MM7 icon in the merged registry.
   This is a Corsair-inspired interpretation fitted to the MM6 goblin, not proof of the original sprite weapon's item id.
2. Rebuilt the small right-hand region: retained the original cut wrist boundary, lofted a palm and added four
   articulated fingers plus an opposed thumb. Fifteen new finger bones control the grasp. No alternate fist mesh swap.
   Newly built hand faces use a flat-normal region of the existing UV atlas; original body detail/UVs are retained.
3. Added `Weapon.R`, parented to `mixamorig:RightHand`. All sword parts are rigidly weighted to this attachment.
   The fingers shape the grip independently. Contact fitting is baked into the editable neutral geometry; no driver,
   runtime IK or cloth solver is required. The standalone sword has its handle center at the origin, +Y toward its
   tip, +Z toward the blade's curvature, +X through blade thickness.
4. Authored a new attack from native `gobata0`–`gobatf0`: across-body start, raised windup, strike, follow-through
   and recovery. Native timing is 0.75 s. Missing 3D depth, limb paths and recovery interpolation are authored
   interpretations. The generic Meshy slash is not the delivery attack.
5. Adapted idle/walk/run to hold the sword with the same closed grip. Torso/leg motion from the corrected source
   is retained in those clips. Authored attack includes torso/shoulder motion, planted support and free-hand response.
6. Refit and baked the 17 skirt hinges for the new attack; existing v3 clearance is retained in locomotion.

## Counts and clips

**12,073 total triangles** = 11,533 body including rebuilt hand + 540 sword. The hand adds 956 triangles to the
10,577-triangle v3 body. **61 bones** = 45 v3 bones + 15 finger bones + one weapon attachment. Maximum four skin
influences per vertex. Original sources and all earlier repair candidates remain unchanged.

| Clip | Seconds | Purpose |
| --- | ---: | --- |
| MM6_Goblin_Idle | 10.0 | Existing idle with armed right hand |
| MM6_Goblin_Walk | 1.041667 | Existing walk with armed right hand |
| MM6_Goblin_Run | 0.666667 | Existing run with armed right hand |
| MM6_Goblin_Attack | 0.75 | Authored native-style melee attack |
| MM6_Goblin_GripRest | 0.083333 | Static grip inspection pose |

Delivery uses 48 fps to preserve the authored attack's half-frame keys from the 24-fps working timeline.
The motion duration is unchanged. [Manifest and file hashes](delivery_manifest.json).

## Checks performed

- Front and oblique continuous playback / intermediate poses, grip from three close views, and exported stills.
- [Attack audit](combat_audit.json): no sampled blade-edge/body intersections in 37 attack samples; planted foot
  minimum remains within floating-point tolerance of z=0. Attack returns to its initial pose.
- [Wrist bend](wrist_bend_report.json): at most 25 degrees in the authored attack.
  [Twist audit](twist_audit.json): hand axial roll about 5–9 degrees; no full-turn wrist reversal.
  These are rig measurements, not a claim of exhaustive anatomical/continuous-time collision validation.
- [Skirt clearance](motion_clearance_report.json): 607 whole/half-frame poses across five clips; no sampled
  thigh penetration. Minimum clearance in attack is 4.57 mm; all clips remain above 1.57 mm.
  Checks include strip vertices, edge midpoints and face centers below belt attachments; they do not establish
  complete garment self-collision or arbitrary animation-blend clearance.
- [Grip contact](grip_contact.json): each digit fitted around the handle. Vertex clearance includes a small margin
  for the flat polygon faces between samples. Visual review also checks opposing thumb and palm placement.
- [Export verification](export_verification.json): 12,073 triangles, 61 bones, five clips and correct durations.
  Reimported body surface positions match within **0.008 mm** at sampled exported frames; weighted joint positions
  match within 0.006 mm. Arbitrary-between-key skin error was below 0.049 mm.
  A ~0.54 mm position difference affected only the unused `RightHandMiddle4` helper; see
  [joint detail](export_joint_detail.json). It has no vertex influence. No visible deformation was waived.
- New hand polygons were triangulated before export so the preserved normal atlas has exported tangent data.
  [Standalone sword verification](sword_export_verification.json): 540 triangles, one mesh, five materials, no skin/clips.

Diagnostic pose reports use the original 24-fps working coordinates. Multiply attack offset from frame 1 by two
for the delivery timeline: native comparison poses are delivery frames 1, 7, 13, 19, 25, 31; recovery is 37.
The preview GIF adds a pause after the attack for viewing; the actual GLB attack is exactly 0.75 seconds.

## Remaining scope

This is the completed sword/grip/attack review version. It is not final runtime asset acceptance.
Authentic body color/material textures, old bake/jewelry blemishes, native hit/death actions, animation-transition
review and OpenYAMM skeletal/material integration remain. Walk/run timings are still the returned clips' timings,
not a claim that the full locomotion reproduces native MM6 timing. The low-resolution hand has deliberately simple
surfaces and needs its final skin/material treatment along with the body.

Scripts under `scripts/` record the working-session operations and depend on named scenes/checkpoints. The
standalone `.blend` is the authoritative editable handoff; no temporary file or running helper is needed to open it.
