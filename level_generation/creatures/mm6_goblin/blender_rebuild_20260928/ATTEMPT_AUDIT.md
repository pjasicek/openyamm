# Creature 3D attempts: evidence and lessons

Audited 2026-09-28 for the [new Blender rebuild plan](README.md).
[Visual board](references.html) · [measured file inventory](source_audit.json).

## Scope and confidence

A recursive scan of `level_generation/creatures/` found model files in **brown_ghost** (8 files) and
**mm6_goblin** (91 files), counting `.blend`, `.glb`, `.gltf`, `.fbx`, `.obj` and `.usdz`. These counts include
checkpoints and duplicates, not 99 distinct attempts. Documentation searches found no additional implemented
creature 3D project in that subtree. The MM5 troll is 2D image/motion authoring; the Meshy pilot discusses an ogre
as another possible subject but does not supply an ogre model.

This audit inspected source/reference images, comparison renders, project notes, relevant authoring scripts and
the JSON/accessor structure of selected **actual GLB files**. Counts below were remeasured where marked in the
inventory. It did not reopen every Blender checkpoint, replay every clip or perform new deformation tests.
Historical motion/contact measurements are attributed to their saved reports rather than presented as rerun tests.
The earlier Meshy source in `output/meshy_goblin_v2_review/` was followed because the creature project imports it.

## The attempts and their results

| Attempt | Construction and result | What remains useful / what failed |
| --- | --- | --- |
| [Brown ghost](../../brown_ghost/README.md), September 7 | Original Blender/MCP construction from native `m242` sprites and selected AI restoration sheets. 46,771 exported triangles, 32 joints, seven clips; directional sprite delivery followed. | Documented user-accepted visual improvement. Replacing a toy-like head with continuous skull surfaces, then improving the whole robe/body, mattered more than valid bones or materials. Not a 10K biped benchmark. |
| [Original Blender goblin](../README.md), September 8 | Native audit → restored turnaround/head/action sheets → scripted anatomical surfaces and voxel-unified body → separate costume → 88-bone rig → seven clips → bake/GLB/sprites. 206,722 triangles. | Extensive functional delivery. Saved [comparison](../review/native_restored_model.png) still shows simplified armor, face/teeth, feet and body transitions. My current visual assessment: unsuitable as the new appearance target despite the detailed delivery record. |
| [First textured Meshy goblin and head correction](../../../../output/meshy_goblin_v2_review/README.md), September 23 | Earlier generated body, corrected animated head pitch in selected idle/walk clips. Saved report: 97,517 triangles, 28 joints, ten clips. | Useful detailed appearance; posture needed per-action correction. This is a separate branch from the later untextured million-triangle restart. Its generation settings are not reconstructed here. |
| [First Meshy sword/attack](../meshy_sword_attack/README.md) and [arm revision](../meshy_sword_attack/rig_revision/README.md) | Local 5,932-triangle sword plus grip morph and native-style attack on the earlier body: 103,449 total triangles, 12 clips. Revision adds four twist joints, raising 28 joints to 32. | Explicitly challenged by user review: loose grip, wrist reversal, bent bracers, flared free arm. Revision improved technical faults but remained a review checkpoint with unfinished hand/gesture work. |
| [Restart master 01](../meshy_restart_20260923/master_01/README.md) | Four selected front/left/back/right AI references submitted by the user. Saved UI evidence: Meshy 7.1 Flagship, Multiview, Ultra 2K, A-pose, enhancement/texture/split off. 1,142,748 triangles; no UVs, maps or rig. | Attractive coherent body and surface detail; missing back plates/rear skull taper, excessive teeth and extra ear jewelry. Correct input views were present; "forgot the back image" was not supported. |
| [Restart master 02](../meshy_restart_20260923/master_02/README.md) | Retry: 1,183,918 triangles, no UVs/maps/rig. Actual retry controls not recorded. | Better tooth projection, but a round skull, invented single back plate and lumpier surfaces. No demonstrated improvement from more geometry. Master 01 selected for local repair. |
| [Locally repaired master](../meshy_restart_20260923/repaired_master/README.md) | Skull taper and teeth corrected; two back plates added. 1,144,016 triangles, 15 mesh objects. | Best retained dense shape/bake source. Body/armor/clothing still largely fused. Failed left-ear surgery was reverted; the extra jewelry survives in this source. |
| [Meshy remesh](../meshy_restart_20260923/remesh_01/README.md) | 24,180 exported triangles. Actual submitted controls unconfirmed. | Rejected: lost eye/mouth/spike/finger and armor forms. A smoothing diagnostic improved shading but could not restore missing structure. |
| [Local reductions](../meshy_restart_20260923/runtime_candidate_30k/README.md) | 200K intermediate, then a 30K local reduction with better static shape retention. | Neither proved joint topology. Excessive spend in skirt/hips; 1,200 triangles in twelve separate back rivets. Clay appearance was mistakenly used to support too high a minimum budget. |
| [Quad Remesher trials](../meshy_restart_20260923/quad_remesh_trial_03_neutral/README.md) | Dense run cancelled without output near 79.78%. Two completed 198K-input trials: painted density 27,320 exported triangles; neutral density 21,128. | Painted allocation damaged skirt/torso/armor; neutral spent about 41% of body triangles in the belt/skirt/hip region while losing face/armor shape. Neither accepted. These are not proof that all hand-authored low topology would fail. |
| [Skirt reconstruction](../meshy_restart_20260923/skirt_rebuild_01/README.md) | Seventeen new strips and belt: 1,392 triangles with a 2K normal bake. Fused waist required reconstruction of covered anatomy. | Concrete proof that planned clothing geometry works. Surrounding 153,049-triangle context model was a component review, not a runtime candidate. |
| [Whole low candidate](../meshy_restart_20260923/detail_rebuild_01/README.md) | Weighted body decimation plus new clothing, simpler pouch and baked back rivets. 10,577 triangles, two normal atlases, no sword or rig at this stage. | Static appearance accepted according to later restart notes. Normal maps restore considerable detail; local shin/ear/mouth defects remain. Body is still mostly decimated/fused source topology. |
| [Returned Meshy rig and local repairs](../meshy_restart_20260923/rig_review_01/README.md) | Return altered 10,577 triangles to 10,372; 28-joint skeleton displaced through torso/neck. Local repair restored accepted mesh, recentered joints and corrected weights/posture; v3 added 17 skirt controls. | Rig errors had specific causes unrelated to insufficient triangles. Clearance improved in saved sampled checks. No universal motion/transition acceptance followed. |
| [Latest sword/hand/attack](../meshy_restart_20260923/sword_attack_01/README.md), September 24 | Rebuilt right hand, 15 finger controls, 540-triangle sword, native-style 0.75 s attack. **12,073 triangles, 61 joints, five clips**. | Strongest low-cost motion checkpoint found. Final body material, native hit/death, old bake/jewelry defects and transition/runtime review remained. It is not a completed production character. |

## Intended look versus the observed artifacts

The original [goblin brief](../GOAL.md) asked for a polished fantasy character that survives profile, rear,
close-up and motion inspection. It explicitly rejected a procedural-placeholder standard. The later restart
changed the active goal from sprite production to eventual runtime 3D; its old appended status sections need
to be read chronologically. Statements such as "rigging untested" near the top are superseded by the later
September 24 rig and sword results, not proof that those artifacts are missing.

My visual inspection of the [selected four-view design](../meshy_restart_20260923/reference_review.jpg) shows the
desired compact, forceful face, believable hands/feet, fitted modest armor and worn materials. The
[dense source comparison](../meshy_restart_20260923/master_01/review/reference_vs_master.jpg) captures much of
the richness, but visibly changes skull/back/teeth and armor design. The
[first Blender result](../review/native_restored_model.png) is recognizable while noticeably smoother, simpler
and less convincing in those regions. This is a shape/construction problem as well as a surface problem.

The [10K normal comparison](../meshy_restart_20260923/detail_rebuild_01/comparison.jpg) is positive evidence:
much of the source's surface richness returns on unchanged low geometry. The
[face close-up](../meshy_restart_20260923/detail_rebuild_01/face_comparison.jpg) also exposes angular/fused mouth
forms and jewelry/bake blemishes. It demonstrates feasibility of detail transfer, not a finished face.

The latest [attack comparison](../meshy_restart_20260923/sword_attack_01/attack_comparison.jpg) follows the broad
blade phases, but the source's torso turn and body gesture remain stronger. The saved
[grip close-up](../meshy_restart_20260923/sword_attack_01/grip_palm.png) has articulated digits around a handle,
yet the palm/knuckle surface remains visibly coarse. These are current visual assessments of saved stills;
they do not contradict successful export parity or claim a newly measured animation fault.

## Why the work did not converge to the requested finish

1. **The cost target arrived after construction.** Dense procedural or generated geometry was treated as the
   asset to rescue. Whole-body simplification then had to infer identity, component boundaries and deformation
   needs simultaneously. More triangles hid neither a weak silhouette nor the wrong joint layout.
2. **Surface detail and essential form were mixed together.** Tiny rivets consumed geometry while the mouth,
   hands and joints needed directed attention. The user-supplied [7,834-triangle Dark Knight audit](
   ../meshy_restart_20260923/reference_asset_audit/README.md) corrected the clay-only evaluation. It is a
   cost/material reference; no character mesh or texture from it should become goblin content.
3. **Fused construction made local repairs expensive.** The skirt was part of the body, jewelry part of the ear,
   and armor part of deforming limbs. Removing clothing meant rebuilding hidden anatomy; removing jewelry could
   destroy the ear. The new mesh should have intentional part boundaries from the beginning.
4. **Some failures were rig placement/weights, others were our animation.** Saved restart diagnostics found
   spine/neck offsets around 5.8–8.7 cm at a normalized 1.7 m height and shoulder contamination in neck/head
   weights. Earlier wrist reversal came from the authored camera-facing blade basis. These call for different fixes.
5. **Validation outran visual judgment.** Export parity, collision samples and normalized weights correctly
   described packaging/measurements. They could not certify a believable fist, anatomy, gesture or final look.
6. **Whole-body reruns obscured the next problem.** More references, automatic remesh retries and expanded
   animation sets did not replace targeted face, hand, clothing and joint construction. The useful progress
   came from replacing specific parts and inspecting their behavior.

## What to carry forward

Carry forward the native source audit, selected neutral images, head/material references, repaired dense master
as a read-only guide, existing bake comparisons and precise failure diagnoses. Keep the 10K and 12K results as
benchmarks. Use new geometry and a locally placed rig for the new attempt. Retain the successful ghost lesson:
model complete connected forms, then judge the complete creature, rather than assembling an inventory of parts.

Do not carry forward the earlier 206K/103K budgets, a blanket minimum of 30K, fused parts, automatic skeleton
placement, the older fixed grip morph, or historical "final" labels as visual approval. There is no need for a
new paid geometry generation or whole-body remesh to start the proposed Blender rebuild.
