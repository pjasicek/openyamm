# Skirt / thigh clearance correction — v3

The user correctly identified visible thigh penetration in `test_img/2034.png`, walking frame 15.
The earlier hips-dominant garment weights did not make the hanging strips lift sufficiently with the legs.
This is a deformation defect; v2 upright alignment did not resolve garment clearance.

## Current files

- [Animated GLB](mm6_goblin_10577_skirt_v3.glb)
- [Standalone editable Blender project](mm6_goblin_skirt_v3.blend)
- [Matching walking-pose comparison](skirt_comparison.jpg)
- [Exported front](export_front.png), [quarter view](export_quarter.png), [opposite step/view](export_opposite.png)

The current Blender scene is `Goblin - Skirt Clearance v3`, walking frame 15.

## Changes

The 17 separate hanging strips now each have one hinge bone parented to Hips, rooted near the belt.
Their inner and outer surfaces share the same rigid influence. The belt remains attached to Hips.
Strip motion is fitted to the evaluated thigh surfaces with a 3 mm target clearance, then eased with a
conservative temporal envelope and a small angular margin. Motion is baked into ordinary skeletal actions;
there is no runtime cloth simulation or Blender driver dependency. The original geometry, UVs and normal atlas
are preserved: 10,577 triangles, now 45 joints (28 original plus 17 skirt controls), five clips.
Maximum strip angle in walking is 21.5 degrees. Upright v2 torso corrections remain.

## Verification and limits

- [Clearance report](motion_clearance_report.json): 645 poses across five clips, sampled at whole and half frames.
  Garment vertices, edge midpoints and face centers below the belt attachment were checked against thigh surfaces.
  No sampled penetration was detected. Minimum sampled clearance was 3.67 mm walking and 1.57 mm running.
- The thigh surfaces have open upper boundaries; an outward ray distinguishes actual interior samples from
  points outside an open boundary. A nearest-normal sign alone gave false positives and was rejected.
- This is a sampled surface check, not a proof of all possible continuous-time collisions or a full garment
  self-collision/body/hand/pouch simulation. New or blended animations need their own deformation review.
- Export was reimported: 10,577 triangles, 45 joints and five `Goblin_Skirt_` clips. Sampled joint positions
  matched within 0.010 mm. See [export report](export_report.json). Reimported front and oblique views reviewed.
- Original v2 and earlier files remain unchanged. Preliminary solver outputs are diagnostic experiments;
  `clearance_solution.json` and `motion_clearance_report.json` describe the accepted local correction.

Grip, authentic MM6 combat motions, final materials and runtime integration remain unfinished.
The deformation change fixes the reported skirt issue; it does not establish overall production acceptance.
