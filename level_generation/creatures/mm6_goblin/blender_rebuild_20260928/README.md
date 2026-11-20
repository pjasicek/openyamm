# MM6 goblin: authored Blender rebuild

**Execution result, 2026-09-28: 12,916 exported triangles including the sword, 72 joints and seven clips.**
The user’s hard limit is 15,000 triangles. The editable Blender project, rigged GLB and original unrigged
texturing handoff are in [delivery](delivery/README.md).
**Latest: [attack elbow correction, frames 8/9/10/17](review/attack_arm_correction/index.html?frame=7).**
Both elbows now flex in their anatomical bend plane. The sword hand takes a forward arc through the cut, with
a lower elbow during downstroke and recovery. The review has direct shortcuts to the four reported frames;
[findings and checks](review/attack_elbow_correction/README.md). Only attack changed.

**Screenshot 2128: [attack arm correction](review/attack_arm_correction/index.html).** Both arms now follow
the six native front-facing attack poses: compact guard, raised sword arm across the chest, cupped free hand,
then an opening sweep across the abdomen. The comparison synchronizes original / before / revised, with eight
model directions. Only `attack` changed; geometry, textures and the other six actions are identical.
Open the **[complete animation gallery](review/complete_gallery/index.html)**: all seven actions from eight
directions, **56 videos rendered from the latest textured GLB**, with slow playback, exact frame stepping and
synchronized eight-view comparison. The main [review entry point](review.html) opens this gallery; the
[original modeling review](review_modeling.html) remains available.
The user-supplied Meshy PBR maps are integrated, with the duplicate eye paint locally repaired in color,
normal and roughness. **Screenshot 2120 correction:** brighter eye materials and larger fitted gold irises/dark pupils
make the eyes clearer at full-body scale. Open the [eye visibility review](review/eye_readability/index.html).
Only the two iris/pupil surfaces and three eye materials changed in this pass; topology, UVs, weights, maps and
all seven clips are retained. The preceding [whole-body walk correction](review/body_motion_correction/index.html)
adds the original's pronounced chest/back turn, opposing hips, forward lean and longer stride.
The original modeling handoff and raw Meshy return remain available.
See the [execution log](WORK_LOG.md) for changes and validation.

**Hand correction:** feedback in `test_img/2095.png`–`2098.png` exposed reversed finger flexion and an outward
sword grip. Both palms now face inward in standing, the thumbs face forward, and the fingers close around the
palm-side hilt. All seven actions and both GLBs have been updated, still at 12,916 triangles.
See the [before/after hand review](review/hand_correction/index.html).

**Screenshot 2100 follow-up:** the free left thumb now rests toward the palm, and the neutral chest/head tilt
has been removed to center the neck. See the [thumb and neck comparison](review/thumb_neck_correction/index.html).

**Motion correction, screenshots 2101–2103:** the attack now prepares upward with a lifted, slightly turned head,
then slices down and to the side with the cutting edge leading. The walk swings both upper arms in opposition;
the shoulder caps use continuous attachment instead of stepped clearance offsets. Walking now takes 1 second
per cycle for the requested slower arm swing. See the [motion comparison](review/motion_correction/index.html).

The original planning study follows. Its approximate 10K budget was superseded by the user’s 15K ceiling.

Open the [visual reference board](references.html) alongside the [attempt audit](ATTEMPT_AUDIT.md).
[Measured source inventory](source_audit.json) records the files and GLB counts checked for this study.

The proposed result is a newly authored, coherent goblin with the presence of the selected references and dense
Meshy sculpt, approximately **10,000 exported triangles including the sword**, deliberate joint topology, and
UVs ready for later material work. The difficult work is likeness and deformation: adding geometry indiscriminately
did not solve either in the previous attempts. Blender MCP provides the required editing access, but the result
must earn acceptance through visible comparisons and motion, not a claim about model capability.

## What the history actually establishes

- The brown ghost is the useful successful Blender precedent: connected anatomical surfaces, reference-led body
  revisions, a rig, seven clips and a documented accepted visual improvement. Its GLB is **46,771 triangles**;
  it does not demonstrate a 10K humanoid workflow by itself.
- The first Blender goblin reached **206,722 triangles**, 88 joints and seven clips. It was packaged and checked,
  but the saved comparisons still show simple shoulder shells, small feet, an artificial mouth and weak anatomical
  transitions relative to the intended art. Delivery completion is not a reason to adopt its appearance.
- The Meshy restart supplied an appealing detailed body, then lost important forms during automatic remeshing.
  Master 01 is **1,142,748 triangles**; the locally repaired source is **1,144,016**. Its hidden construction and
  fused parts were poor starting conditions for clean clothing, joints and weights.
- The later local work did reach **10,577 triangles without a sword**, using rebuilt clothing and normal baking.
  Subsequent local rig/hand/sword work reached **12,073 triangles including sword**, 61 joints and five clips.
  This was a useful review candidate, still missing final body materials, some native actions and overall runtime
  acceptance. It is inaccurate to say no low-poly or animated result was ever achieved.

The new request changes the construction approach: author the low mesh and its parts deliberately from the outset.
The old low models remain evidence about cost, baking and failure cases; they are not the starting topology.

## Reference authority and intended appearance

| Role | Exact references | How to use them |
| --- | --- | --- |
| Native identity and motion | [Standing views](../source_audit/standing_strip.png), [attack](../source_audit/attack_native.png), [walk](../source_audit/walk_native.png), [source manifest](../source_manifest.json) | Set silhouette, costume coverage, handedness, action order and timing. |
| Main neutral modeling design | Restart [front](../meshy_restart_20260923/references/front.png), [left](../meshy_restart_20260923/references/left.png), [back](../meshy_restart_20260923/references/back.png), [right](../meshy_restart_20260923/references/right.png) | Selected historical reference set; coherent look to aim at. AI interpretations, not calibrated orthographic measurements or new user approval. |
| Face and material character | [Restored head](../reference_restoration/head_v1.png), [earlier turnaround](../reference_restoration/turnaround_v1.png) | Heavy brow, recessed eyes, cheek/jaw planes, worn olive skin/iron/leather. Newer neutral design wins where they conflict. |
| Useful dense 3D form | [Repaired Meshy master](../meshy_restart_20260923/repaired_master/mm6_goblin_repaired_master.glb), [front/side/back comparison](../meshy_restart_20260923/master_01/review/reference_vs_master.jpg) | Inspect depth and masses; optionally use local surfaces as projection guides or bake sources after correcting disagreements. |
| Budget/material proof | [Dense / low / normal-mapped comparison](../meshy_restart_20260923/detail_rebuild_01/comparison.jpg), [face close-up](../meshy_restart_20260923/detail_rebuild_01/face_comparison.jpg) | Preserve the demonstrated economy while fixing mouth, ear, shin and topology problems. |
| Motion lessons | [Earlier rejected grip/rig](../meshy_sword_attack/rig_revision/README.md), [latest attack](../meshy_restart_20260923/sword_attack_01/attack_comparison.jpg) | Use diagnoses and native action references; previous clips are not automatically approved motion. |

Keep the lean muscular build, narrow waist, long forearms, compact angular head, heavy low brow, small eyes,
short broad nose, projecting jaw, tall ears, rear skull taper, long clawed feet and a right-handed curved sword.
Clothing is a modest V-shaped gorget, separate spiked shoulder caps/bracers/shin guards, two small upper-back
plates, leather strip skirt, belt and right-hip pouch. Abdomen, thighs and most of the back stay exposed.

Correct the dense master's rounded skull, excessive tooth projection, invented chest embellishment and extra
left-ear jewelry wherever those survive in a reference. Its attractive surface richness is useful; its errors
do not become design requirements. The original frontal sword looks short through foreshortening.

Four fingers and an opposed thumb, four prominent toes, and three right-ear hoops are historical reconstruction
choices, not exact counts established by the native pixels. Retain those choices for continuity unless visual
inspection warrants a recorded change. Avoid the invented central spine strap from the older turnaround.

## Geometry budget

Count the **evaluated, triangulated export**, including back faces, thickness, teeth, eyes, nails, costume and
weapon. Authoring quads, Blender vertex counts and UV-split GLB vertices are separate measurements.
Target about 10K; an 8–12K result is a review range, not an engine performance guarantee or a reason to spend 12K.

| Part, both sides where applicable | Initial triangle allowance | Priority |
| --- | ---: | --- |
| Head, ears, eyeballs, mouth lining and visible teeth | 2,000 | Face planes, recesses, lip/jaw silhouette and ear depth |
| Neck, torso and pelvis | 1,000 | Continuous anatomy and shoulder/hip connections |
| Arms, elbow and wrist transitions | 800 | Bending and distributed twist |
| Hands, fingers and nails | 1,300 | Palm volume, thumb opposition and a convincing grasp |
| Legs, feet and toe claws | 1,400 | Knee/ankle motion and long native foot silhouette |
| Armor, major spikes and visible straps | 1,100 | Separate rigid shells and readable edges |
| Belt and hanging skirt strips | 850 | Outline, overlap, gaps and bending sections |
| Pouch | 150 | Silhouette and flap volume |
| Ear hoops and buckle silhouette | 100 | Restrained asymmetric detail |
| Separate sword | 400 | Blade curve, thickness, guard and handle |
| Unassigned correction allowance | 900 | Spend only on visible or deformation failures |
| **Total** | **10,000** | **9,100 allocated + 900 reserved** |

These are proposed allocations, not measured new geometry. Rebalance between parts before raising the total.
The previous 540-triangle sword and 1,392-triangle skirt are useful cost references, not mandatory replacements
for these allocations. Character detail and required hand articulation may consume some of the reserve.

## Which detail is geometry, and which can wait

| Keep in the mesh | Put in later maps/materials |
| --- | --- |
| Brow/cheek/nose/jaw masses; actual eye recess and mouth opening | Fine wrinkles, pores, scars, lip creases and skin mottling |
| Ear outline, thickness, main cup; rear skull projection | Shallow ear ridges and fine surface variation |
| Distinct fingers, thumb web, palm arch, major claws | Knuckle creases, nail striations and subtle tendons |
| Long foot/heel/arch and visible toe separations | Minor skin relief and claw wear |
| Shoulder/bracer/shin outlines, large spikes and visible plate thickness | Rivets away from silhouettes, engraving, hammered pits and shallow rolled trim |
| Skirt strips, real gaps/overlaps, pointed ends and visible edge thickness | Stitching, leather grain, shallow folds and most fasteners |
| Sword curve, guard, handle diameter and visible pommel profile | Grip wrapping relief, blade scratches and tiny inset decoration |

Judge this at roughly 128, 256 and 512 pixels of standing figure height, plus hand/face close-ups. A feature that
changes an outline or must separate during movement needs geometry even if small. A feature visible mainly as a
lighting change is a candidate for a normal map. Normal maps cannot fix anatomy, open a fused finger gap, preserve
a missing spike silhouette, create contact or stop a skirt intersection. PBR describes surface response; normal,
base-color, roughness and metalness maps each solve different parts of the appearance.

Final texturing remains the user's Meshy step. During modeling, use simple olive/brown/iron material regions for
readability and clay/wireframe for shape. A small provisional normal-bake proof is appropriate if a geometry
decision depends on shallow relief; it is not a new full texturing project. Do not reject an intentionally plain
plate merely because rivets have not been baked yet, or excuse a bad jaw because textures are pending.

## Construction in Blender MCP

### 1. Establish one controlled working scene

Follow [Blender MCP startup](../../../BLENDER_MCP_STARTUP.md): inspect version, current scene and unsaved ownership,
reuse a working GUI, and verify execution plus viewport capture. No live connection was tested for this plan.
Use a new owned scene such as `MM6 Goblin - Authored Low Mesh`; preserve existing projects.

Load the four selected images and a locked copy of the repaired high mesh in separate reference collections.
Keep both out of exports. Use a ground-centered origin, meters, Z up and -Y forward in Blender, recording the
glTF conversion. Start from a documented working height, provisionally 1.7 m to make old rig comparisons convenient;
this is not a claim that the game descriptor's height 145 means 1.45 m or that the goblin is canonically 1.7 m tall.

Measure crown/chin/shoulder/elbow/wrist/hip/knee/ankle landmarks and widths on the references. Save the observed
image coordinates and confidence before choosing model ratios. Align ground and height without distorting aspect.
Because the images are not exact projections, reconcile contradictions in 3D instead of forcing every contour.
Build front, both profiles, rear and three-quarter cameras with fixed comparison framing.

### 2. Build the whole silhouette, then resolve the face and hands

Create new low-resolution skin surfaces with explicit vertex/edge control. Torso and limb cross-section guides
can seed the mesh, but shoulder, armpit, crotch, neck and hand junctions need intentionally connected patches.
Mirror early skin work where useful, then retain the required costume asymmetry. Primitive volumes are blockout
tools; visible anatomy must develop into continuous shaped surfaces.

Keep the complete body visible while refining head and hands. In the face, establish cheek/temple/jaw planes,
inset eye openings, a short nose and lip boundary; then connect the loops into the skull and neck. Build ears as
thin cupped surfaces. Make a small real mouth cavity and a restrained irregular tooth row. Do not recreate the
earlier separate eyelid tubes, bead-like teeth or pasted-on ellipsoid muscles.

Create palms with real thumb webs and knuckle arcs; fingers are tapered articulated surfaces, not detached
cylinders laid on a flat palm. Test a rough handle inside the hand now. Form feet with heel, arch, forefoot and
toes before adding guards. Long feet must read in profile as well as front.

Use the high mesh as a local surface guide when helpful. Restrict shrinkwrap/projection by component so vertices
cannot snap from a forearm to a bracer, across the mouth, or between skirt strips. Define the new edge flow first;
global remesh or collapse of the 1.14M source is not the planned topology generator. Avoid global subdivision or
voxel union as a finishing step that silently discards the budget and joint layout.

First shape milestone: a complete untextured silhouette with a credible head, hands and feet, shown against the
native and selected restoration from the fixed views. Correct the largest visible mismatch before adding detail.

### 3. Make clothing and armor actual separate parts

Build thin plate shells and the few large spikes independently from the skin. Their underlying limb topology
stays usable. Bracers/shin guards follow the corresponding rigid limb segment; shoulder shells get an intentional
attachment/control and clearance during arm lift. Separate objects during authoring need not mean separate
runtime materials or draw calls; compatible parts can be combined at export after their behavior is settled.

Fit a simple belt and around 17 individually shaped strips, preserving reference lengths, overlaps and negative
spaces. Give strips enough longitudinal sections to bend without faceted kinks, with efficient inner/edge faces.
Keep the covered hip/thigh surface simple but usable when the skirt lifts. Omit hidden skin only where it remains
hidden throughout the reviewed poses. Build a small pouch and separate right-ear hoops rather than inheriting
the source's fused jewelry. Add the native curved sword as an independent rigid mesh, fitted to the actual palm.

### 4. Test deformation before committing the mesh

Place a small local skeleton using the authored anatomy. Center pelvis/spine/neck/head in the body; verify front
and profile placement and bone roll before binding. Shoulder, elbow, hip and knee loops should run around the
joint with supporting rows on both sides. Keep long triangles and high-valence poles out of the principal bend
creases; quads alone do not establish good deformation. Smooth and inspect volume through the entire bend.

Start weights by anatomical region, then refine visually. The hanging hand's proximity to the pelvis must not
give the hip arm weights. Head/neck weights cannot include an unrelated shoulder. Keep rigid armor rigid,
distribute forearm twist through appropriate helper joints if the motion needs it, and use normalized weights
with at most four influences in the proposed GLB export.

Provide editable finger chains and a right-hand weapon attachment, plus skirt controls that follow motion without
cloth simulation. Start with roughly 60–80 deform joints depending on finger/strip controls, and prune only unused
controls at export; this is an authoring estimate, not a validated renderer limit. Do not optimize the rig by
removing necessary grip or skirt behavior before measuring any engine constraint.

Review open hand → grasp, elbow bends, forearm pronation/supination, raised and cross-body sword arm, left arm
shielding the face, a deep step/crouch, and the beginning of a prone collapse. Watch intermediate frames from
front, side and oblique angles. Make a short walk and one 0.75-second attack before expanding the action set.
Confirm thumb opposition, palm/handle contact, wrist continuity, armor clearance and skirt/leg clearance by sight;
focused contact/weight checks support that review. Export/reimport a motion probe at this stage.

### 5. Freeze geometry and prepare the user's texturing handoff

After shape and deformation pass, unwrap a deliberate non-overlapping UV set, favoring the face and hands.
Start with one shared 2K body/costume atlas and a modest sword allocation; select final texture size from review.
Do not silently repeat the old three-4K-texture budget. Record material/part IDs and retain source UVs. Save the
editable quad mesh, then freeze the export triangulation and shading basis before any final tangent-normal bake.

Deliver an unrigged A-pose texturing copy with exactly the same final surface and UVs as the local rigged mesh,
plus the local rigged project. Preserve the rig and clips locally when incorporating the user's returned maps.
Meshy's documented Retexture API accepts uploaded GLB and provides `enable_original_uv`; request UV preservation
when available in the user's chosen interface. UI options and returned geometry still need checking.
[Meshy Retexture documentation](https://docs.meshy.ai/en/api/retexture), checked 2026-09-28.

On return, compare geometry, UVs, transforms and image assignments before transferring materials. Vertex splitting
can change exported counts without changing the surface; compare the actual correspondence, not just a total.
If UVs changed, explicitly rebake/transfer into the authoritative UV layout. Do not replace the local skeleton
with an automatic rig. If using both dense-source and Meshy normals, combine tangent normals correctly and inspect
the result; ordinary RGB blending is not a normal-combination method. Baking the old sculpt is useful only where
the new form agrees with it, using isolated part sources/cages to avoid projecting neighboring geometry.

### 6. Finish native motion, then package the asset

The required motion reference remains native: standing, walk (0.75 s), attack (0.75 s), hit (0.75 s),
death (0.625 s), held corpse and fidget (0.75 s). Standing can gain restrained breathing. Author real changes
between the sparse source keys; increase sampling only to preserve motion, not to invent animation quality.
Running is optional: the previous Meshy run/walk durations do not define native timing.

Make the attack a torso-led cross-body slash with anticipation and recovery; inspect body weight shift and the
free arm, not only blade angles. Hit raises the left forearm across the face. Death must end prone. Review
transitions and planted feet as well as isolated clips. Bake any authoring IK/constraints into portable motion.

Finish with the normal `.blend`, rigged GLB, matching unrigged texture handoff, simple posing instructions,
triangle/part/weight/clip/UV inventory, fixed-camera comparisons and short motion previews. Reimport the actual
GLB and compare its appearance and motion. Keep revision checkpoints after accepted shape and deformation so a
material change cannot force another reconstruction of the character.

## Evidence required to call the rebuild successful

| Milestone | Visible evidence and decision |
| --- | --- |
| Proportions and face | Native / selected art / new mesh at equal figure height; front, both profiles, rear, oblique and face close-up. The heavy brow, jaw, feet and costume coverage survive plain lighting. |
| Topology and budget | Mesh/wireframe review and evaluated per-part triangle counts; no unintentional fused parts or visible holes; reserve spent on specific observed needs. |
| Grip and motion | Continuous bend/grip/attack/walk previews and risky intermediate poses; convincing palm/thumb, stable wrist, rigid plates and clear skirt. |
| Texture handoff | UV-ready matching rigged/unrigged surfaces; no further topology repair expected merely to make the first useful poses. Final artistic materials remain the user's step. |
| Final portable model | Reimported geometry, maps, weights, actions and timings agree with the reviewed asset; face/hand close-ups still hold up. |

These are work checkpoints, not requests for repeated permission. Report each largest remaining mismatch and
fix its cause. If a scripted construction yields the same toy-like shape twice, change the surface construction
or hand-edit its control vertices; do not substitute more rivets, noise, lights or a larger mesh.

Runtime installation, renderer/skinning/material support, LODs and performance testing are subsequent engine work.
Their present status was not re-audited for this planning task. A 10K GLB is not a promise about frame rate.
Preserve all historical sources and existing game assets throughout the new authoring run.
