# MM6 demon — keyed native attack

The supplied demon now has an **Attack** clip reconstructed from the six original MM6 attack observations.
It contains **37 keyed poses at 48 fps**, lasts exactly **750 ms**, and includes repaired jaw, claw and forearm
controls. The package also retains **Walking** and **Running**. Original imported and previously corrected
packages remain in place. This is a staged, untextured animation asset; it has not been installed into gameplay.

[Front/profile playback](attack_preview.gif) · [Animated GLB](mm6_demon_attack.glb) ·
[Editable Blender project](mm6_demon_attack.blend) · [Native/model comparison](native_comparison.jpg) ·
[Acceptance record](acceptance.json).

## Playback

Open `mm6_demon_attack.blend` and play frames **0–36** at **48 fps**. The project opens directly in the isolated
`MM6_Demon_Attack` scene with **Attack** active. The Action Editor contains `Attack`, `Walking` and `Running`;
the corresponding NLA tracks are muted to allow action editing without combining clips.

In a GLB viewer, select **Attack** and play it once. Looping is a viewer setting: glTF does not encode a standard
loop flag. [animation_manifest.json](animation_manifest.json) records Attack as nonlooping, Walking/Running
as looping and `attack2` as the same native attack. A later blend to standing belongs outside the 750 ms action.
No gameplay impact event has been added or moved. The GIF repeats with an extra 350 ms endpoint pause for
inspection; its animation portion lasts 750 ms with GIF's 10 ms timestamp rounding.

| Native pose | Clip frame | Time | Keyed movement |
| --- | ---: | ---: | --- |
| A | 0 | 0 ms | Low outward guard, hooked hands, frontal head and small snarl. |
| B | 6 | 125 ms | Right upper arm lifts; bent elbow and opening palm; left hand rises; jaw opens. |
| C | 12 | 250 ms | Right forearm rotates upward with the elbow bent; left claw guards the abdomen; maximum jaw opening. |
| D | 18 | 375 ms | Right wrist lowers outward; left guard drops; small chest/head dip. |
| E | 24 | 500 ms | Right forearm sweeps across the chest; left arm counterbalances; restrained head/body turn and tail reversal. |
| F | 30 | 625 ms | Arms lower and proximal fingers recurl; head/body recover and jaw closes. |
| F hold | 36 | 750 ms | Holds the observed recovery pose through the original endpoint. |

Both feet stay planted. Arm segments use the actual shoulder, elbow and `Hand.head` wrist centers; the original
approximately 0.098-unit forearm-to-hand offset is preserved. Bone scale remains one. Depth and intermediate
movement are inferred from the frontal attack and the genuine native standing views. The original bitmaps hold
each observation for 125 ms; this 3D action smoothly extrapolates between those observations.

## Repairs made while posing

- Moved `Bone_025` to a rear jaw hinge and partitioned lower jaw, lower teeth and mouth floor from upper face,
  upper teeth and skull. An isolated 18-degree opening now moves the tested upper-face/skull/upper-teeth
  vertices by **0.0 units** while the lower jaw opens.
- Established physical tip masks for **all ten claws**, including the previously omitted Ring branch and thumb
  terminal geometry. Connected finger geometry now belongs to its own branch instead of neighboring fingers.
  Terminal claw shape stays rigid while proximal joints open and fan the hand.
- Added **three forearm twist helpers per arm**. Pronation spreads along the forearm; the elbow and wrist centers
  retain their positions. Palm orientation follows continuous anchor quaternions, and signed twist angles are
  unwrapped across the sweep. This resolves the intermediate palm flip and forearm collapse found during review.
- Removed stray upper-face weighting from shoulder horn tips and made the hard upper horn tips follow their
  shoulder controls. The earlier shoulder-parent and foot repairs are retained.
- Solved the small hip/chest dip against constant foot targets, with no attack step or sideways foot roll.

The mesh retains **7,899 vertices and 15,686 triangles** with unchanged rest coordinates and connectivity.
The rig has **85 bones**: the original 79 plus the six twist helpers. Walking and Running retain their original
bone motion and timing; their surfaces use the repaired weights. No original texture or UV layer existed in the
supplied animated mesh, and none was generated in this pass.

## Review and verification

All **37 output poses** were inspected from front and profile. Hand/wrist and head/jaw crops retain the original
1300 × 1100 render pixels for detail inspection. Rear, opposite profile and both three-quarter directions were
checked at the six native anchors and the endpoint. Seven representative Walking and Running poses were also
reviewed. The actual exported GLB was independently imported and visually inspected from both three-quarter
directions and at selected frontal/profile poses.

[Review plates](review_plates/) and [full renders](review_frames/) preserve the visual evidence.
[Actual GLB renders](export_review_frames/) use 48 fps **before import**, so their frame labels match the clip.
The wider common three-quarter crop includes the complete claw sweep; the earlier narrow three-quarter D render
clips a fingertip at the image boundary and is superseded for framing by the exported-file review.

Numerical screening covered **145 attack times**, every quarter output frame:

| Check | Final result |
| --- | ---: |
| Maximum relative arm-segment length error | 0.000000427 |
| Maximum relative rigid claw-tip edge error | 0.0000965 (0.00965%) |
| Maximum rigid foot-region drift | 0.000134 model units |
| Lowest rigid sole point | +0.001869 model units above floor |
| Minimum sampled distal-digit surface gap | 0.003438 model units |
| Hand-versus-torso triangle intersections | 0 |
| Smallest triangle area / rest area | 0.13665 |
| Triangle area-collapse flags below 0.1 | 0 |
| Largest quarter-sample bone rotation | 9.81 degrees |

These checks screen fixed lengths, rigid tips, planted soles, discontinuities and selected surface collisions;
they do not prove complete body self-intersection freedom. The visible hands, arm joints, horn attachment,
harness, jaw, feet and tail were reviewed alongside the numerical results.

[Actual GLB reimport](export_roundtrip_audit.json) checked 145 Attack, 101 Walking and 65 Running times against
the delivered Blender project. The maximum mesh-coordinate error was **0.000002593 model units**. The imported
GLB retains one mesh, 85 joints, matching triangle indices and all three named clips. The standalone Blender
startup was also validated. Detailed diagnostics are in [deformation_review.json](deformation_review.json),
[control_repairs.json](control_repairs.json), [surface_flags.json](surface_flags.json) and
[blend_startup_validation.json](blend_startup_validation.json).

## Remaining model differences

This is the native action adapted to the supplied Meshy geometry, not an exact geometric reconstruction of MM6.
That mesh has **four long claws plus a thumb per hand**, whereas the native attack exposes three long claws plus
a thumb. Its terminal claws are more curved, the blade-shaped tail is larger, and body/head proportions differ.
These inherited shapes were retained. Consequently the open-hand reach and silhouette, especially at C, do not
match the original sprite exactly. The comparison shows this explicitly; no independent pose resizing or claw
stretching hides the difference. Hidden joint depth and intermediate muscle deformation remain interpretations.

## Reproduction

Task-local scripts preserve the authoring and checks. `repair_controls.py` rebuilds weights from the saved
source geometry, `add_forearm_twists.py` adds/distributes the helper controls, and `author_attack.py` keys the
motion in `motion.py`. `review_attack.py` performs the subframe checks and renders; `inspect_surface_flags.py`
screens triangle collapse. `make_review.py` composes diagnostic plates and the GIF. `export_attack.py` exports
the staged assets; `normalize_attack.py` makes the Blender file a normal standalone project.
`check_export.py` verifies the actual GLB; `render_export.py` renders that reimport for visual review.

The earlier [source study](../attack_study/ATTACK_MOTION_SPEC.md) retains the native observations and original
failed control probes. Its initial four-branch hand probe was incomplete; the corrected mapping and final
results in this package supersede it. Source-file SHA-256 checks and deliverable hashes are recorded in the
local acceptance record. Shared workflows, runtime assets and global ledgers were not edited.
