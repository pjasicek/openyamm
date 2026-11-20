# Authored MM6 goblin

New Blender geometry, a local rig and seven native-inspired clips. **12,916 triangles including the sword**,
under the user’s 15,000-triangle ceiling.

**[Complete animation gallery](../review/complete_gallery/index.html): 56 videos, seven actions × eight directions.**
Every video uses the latest textured GLB. Includes slow playback, exact frame stepping, synchronized views and
individual MP4 downloads. [Gallery notes and checks](../review/complete_gallery/README.md).

**Latest: [attack elbow correction](../review/attack_arm_correction/index.html?frame=7), frames 8/9/10/17.**
Corrected sideways/backward elbow bending in both arms, removed the right elbow's upward kick, and revised the
cut/recovery path. The review includes direct frame shortcuts and the previous attack as its default baseline.
Only attack changed; [findings and checks](../review/attack_elbow_correction/README.md).

**[Attack arm correction](../review/attack_arm_correction/index.html), screenshot 2128.**
The sword elbow stays closer in the opening guard and rises across the chest. The free hand cups beneath the
grip during preparation, then opens across the abdomen. Both elbow paths and wrist transitions were revised.
Only the attack animation changed; geometry, textures, rigging and the other six clips match the previous export.
The eight attack videos in the complete gallery are refreshed. The native attack has six front-facing images;
the side/back views are authored reconstruction, checked against the standing directions for anatomy.

**[Eye visibility correction](../review/eye_readability/index.html), screenshot 2120.**
The eyes are brighter, with larger gold irises and dark pupils fitted to the existing eyeballs. The iris/pupil
positions and three eye materials change; triangle count, UVs, atlas maps, rigging and all seven actions are retained.

The [whole-body walk correction](../review/body_motion_correction/index.html), screenshots 2117–2118, is included.
The textured Blender project and rigged GLB now include a pronounced torso turn, opposing hips, forward lean,
longer stride and corrected body rise/fall. The eye repair, materials and other six actions are retained.
The original modeling handoff and raw Meshy return remain available.

The [original modeling review](../review_modeling.html) includes fixed views, grip close-ups, the target references,
and motion previews rendered from the exported/reimported modeling GLB. This is an authored modeling handoff;
visual acceptance and an in-engine installation are not implied by the technical checks.

## Files

| File | Use |
| --- | --- |
| [mm6_goblin_textured.blend](mm6_goblin_textured.blend) | Latest editable project; corrected attack elbows, clearer eyes, whole-body walk and packed repaired PBR maps. Opens at reported attack frame 8. |
| [mm6_goblin_textured_rigged.glb](mm6_goblin_textured_rigged.glb) | Latest textured portable model; seven clips including the corrected attack. |
| [mm6_goblin_authored.blend](mm6_goblin_authored.blend) | Editable skin topology, separate costume/weapon parts, local skeleton, UVs and actions. |
| [mm6_goblin_rigged.glb](mm6_goblin_rigged.glb) | Portable skinned asset with all seven clips and fixed triangulation. |
| [mm6_goblin_texturing.glb](mm6_goblin_texturing.glb) | Unrigged A-pose with matching triangles and UVs; sword parked separately beside the body. |
| [Optional source normal proof](../textures/goblin_optional_source_normal.png) | One 2048×2048 tangent normal map embedded in the original modeling GLBs. The new textured candidate uses Meshy's normal map. |
| [Blender audit](blender_audit.json), [binary GLB checks](glb_validation.json), [UV checks](uv_validation.json), [reimport comparison](roundtrip_validation.json) | Measured delivery receipts. |
| [Textured export checks](textured_validation.json), [textured reimport](textured_roundtrip_validation.json) | Only attack changed; geometry, UVs, weights, rig, packed images/materials and the other six clips are identical; 21-pose reimport. |
| [Attack arm checks](attack_arm_validation.json), [hand checks](hand_validation.json) | 145 attack samples for wrist bend, bone scale, loop closure and cutting direction; grip/attachment checked across 35 action poses. |
| [Elbow checks](attack_elbow_validation.json) | Anatomical bend plane and positive flexion in both arms, measured at 145 source and exported poses, including interpolation. |
| [Source foot checks](foot_validation.json), [exported foot checks](foot_export_validation.json) | Foot pitch, absence of sideways twist, sole clearance and loop closure at 96 samples/second. |
| [Source body checks](body_validation.json), [exported body checks](body_export_validation.json) | Chest/hip turn, lean, stride, support phase, shoulder attachment and loop closure. |

The dense historical Meshy model is a hidden reference inside the Blender project. It does not appear in either
GLB. New vertex connectivity was authored through Blender MCP; the dense model supplied local shape guidance
and the optional normal-bake source. No global remesh or decimation generated this topology.

## Geometry and rig

| Group | Triangles |
| --- | ---: |
| Connected body, head and ears | 7,596 |
| Mouth lining, eyes, irises, pupils and teeth | 688 |
| Gorget, shoulders, upper-back plates, bracers, shin guards and straps | 2,072 |
| Belt and buckle | 480 |
| Seventeen leather strips and pouch | 1,036 |
| Three right-ear hoops and hand/foot claws | 720 |
| Curved sword | 324 |
| **Total** | **12,916** |

There are **72 joints**, **26 mesh parts**, **11 material regions**, and at most **three weights per
vertex**. The GLB has 10,589 vertices after normal/UV splits; this is separate from its triangle count. The mesh
parts and material regions are retained for editing and texturing. Draw-call consolidation after final materials
and engine integration remain separate work.

The skeleton includes articulated fingers/thumbs, two distal forearm twist helpers, two shoulder-plate controls,
17 skirt controls and a rigid `weapon.R` attachment. Finger curls were fitted around the handle; the opposed
thumb was solved separately. Skirt flare was fitted against posed skin before sampling the animation channels.
There are no exported runtime IK or cloth dependencies.

The body, head and neck share a welded skin surface. Eye/mouth openings, the separate mouth liner, iris/pupil
discs and strap rims have intentional open boundaries. No non-manifold junctions or unused construction vertices
remain. Normal-map detail does not replace the ear silhouette, claws, fingers, skirt gaps, plate shells or sword.

## Clips

| Action | Duration | Behavior |
| --- | ---: | --- |
| `standing` | 2 s | Restrained breathing in the armed stance. |
| `walk` | 1 s | Chest/back alternation, opposing hips, forward lean and longer stride; 26°/38° foot roll with sole contact. |
| `attack` | 0.75 s | Compact guard, sword arm raised across chest, cupped free hand, descending slash with free-hand sweep and recovery. |
| `hit` | 0.75 s | Left forearm across the face. |
| `death` | 0.625 s | Forward collapse ending prone. |
| `corpse` | 1 s | Held final death pose. |
| `fidget` | 0.75 s | Small head, torso and armed-hand adjustment. |

Blender uses 48 fps. The editable actions have sampled FK channels; the GLB exporter samples every Blender frame.
The walk is in place, and is not a root-motion locomotion asset. The death clip moves the root into the fall.
These are new interpretations of the sparse native frames, not extracted native 3D motion.

The screenshots 2101–2103 follow-up replaced the walk's mostly forearm motion with upper-arm swings, and slowed
the cycle from 0.75 to 1 second. The screenshot 2128 correction reconstructs both attack arms from native A–F,
retaining the chin lift and slight head turn in B/C. The frames 8/9/10/17 follow-up makes both elbows bend
about a shared anatomical hinge and gives the sword hand a forward arc. The right elbow follows a lower,
outward path; wrist bend is limited to 35° instead of driving the elbow from hand orientation. The sword
remains attached to the palm-side grip. The attack has its own guard pose at both ends of its loop.

Shoulder caps follow a continuous partial rotation of the upper-arm direction, without inheriting axial roll.
Their clearance uses a bounded continuous elevation offset. The old per-frame nearest-surface search produced
discrete offsets and visible pops. See the [before/after motion comparison](../review/motion_correction/index.html)
and [historical motion checks](motion_validation.json). That review preserves the earlier attack;
[attack arm checks](attack_arm_validation.json) and the [latest comparison](../review/attack_arm_correction/index.html)
supersede its attack measurements and previews.

## Texturing handoff

The hand correction from screenshots 2095–2098 is included in these files. Standing palms face inward and thumbs
forward; negative finger flexion closes around the palm-side hilt. Forearm twist helpers distribute the rotation
through the distal forearms. All seven actions were rebaked. See the
[before/after review](../review/hand_correction/index.html) and [hand checks](hand_validation.json).
The screenshot 2100 follow-up also corrects the relaxed left thumb and centers the idle neck/head;
[compare the refinement](../review/thumb_neck_correction/index.html). The bind mesh and texturing GLB are unchanged
by this pose-only refinement.

Use the unrigged GLB for the Meshy texturing pass. Preserve original UVs when that option is available. Keep the
local Blender skeleton/actions authoritative when bringing materials back. Compare returned geometry and UVs
before transferring maps; do not substitute an automatic rig for this one.

Both GLBs use one shared 0–1 UV atlas with nominal 8-pixel padding at 2K, extra face/hand allocation, and no stacked
islands. The final binary check found **zero positive-area overlaps and zero collapsed UV triangles**. Small folded
areas were split into additional charts; this changed neither the evaluated triangle count nor the skin weights.
The face, bare torso and other surfaces occupy approximately 46% of the atlas after padding and packing.

The optional normal proof adds selected facial and abdominal relief from the old sculpt. Its influence fades to
zero on the rebuilt ears, hands, costume and other mismatched areas. It is a modeling aid, not a final PBR texture
set. In Blender, disconnect the Normal Map node in `GB15 Skin blockout` to inspect plain geometry. If replacing or
combining it with new normals, preserve the final triangulation/tangent basis and combine tangent normals correctly.

The parked sword changes only its object transform in the unrigged handoff. Its local triangles/UVs match the
rigged sword; [texturing_transforms.json](texturing_transforms.json) records the parking transform. Transfer its
materials back to `GB15 Curved sword`, retaining the locally fitted attachment.

## Opening and editing

- Open the Blender project and use the `MM6 Goblin - Authored 15K` scene. `GB15 Character` contains the asset;
  `GB15 Reference` contains the hidden guide and reference images; `GB15 Studio` contains presentation objects.
- Select `GB15 Goblin rig`. In the Action Editor choose one of the seven named actions. Set the range to 1–97 for
  standing, 1–37 for attack/hit/fidget, 1–31 for death, or 1–49 for walk/corpse.
- For bind geometry and UV editing, switch the armature to **Rest Position**. Keep the fixed triangulation modifier
  after the armature modifier; removing or changing it invalidates the optional tangent-normal bake.
- Bone names identify the editable regions. Right is the character’s right: `.R`, shown on the viewer’s left in
  a front view. The weapon exits the index/thumb side of that hand.

Working coordinates are meters, Blender Z up and −Y forward, at a provisional 1.7 m body height. This is a modeling
scale, not a claim about the canonical goblin’s height or the game descriptor’s units. Standard glTF export is Y up.

Checks cover the delivered binary, normalized weights/normals, UVs, clip durations and bind-surface parity.
The rigged and texturing surfaces agree within 0.002 mm. The reimport comparison checked every joint plus the skin
and sword in 21 poses; maximum surface error was approximately 0.004 mm. These checks establish portability, not
art approval, complete collision freedom in arbitrary poses, or engine performance.
