# Current target: animated runtime 3D goblin

User clarification, 2026-09-23: the current deliverable is a 3D character intended for eventual use
in the game. Billboard rendering is not the active deliverable. This supersedes the billboard-first
scope in earlier run notes.

## Source and candidate roles

- Preserve `repaired_master/mm6_goblin_repaired_master.glb` as the detailed shape/baking source.
- Keep `reduction_200k/` as an intermediate comparison; its count has not been justified for runtime.
- Reject `remesh_01/`: severe eye, mouth and spike loss. A raw mesh can omit map-level surface detail,
  but this candidate also loses important forms and silhouette. Smoothing alone did not repair it.
- Evaluate `runtime_candidate_30k/` as a local geometry trial. Its target is 30,000 triangles including
  the existing back plates/rivets and excluding the separate sword. This is a test budget, not a
  measured engine limit or an animation-ready topology claim. It starts from the dense repaired source,
  not the damaged Meshy remesh or the 200K intermediate.

## Next steps

1. Replace excessive clothing/detail geometry with purpose-built low geometry before another global reduction.
   For the belt/skirt, retain the hanging-strip outline, gaps, visible overlaps and just enough sections to
   follow the hips/thighs without clipping. Move small rivets, stitching, shallow folds and trim relief into
   baked normal maps and color/roughness textures. No cloth simulation is planned. Finish left-ear cleanup.
2. Inspect and repair topology around shoulders, elbows, wrists and fingers. Use a provisional rig to
   test a firm sword grip, wrist twist, elbow bend and raised/free-arm poses before finalizing topology.
   Automatic triangle reduction and automatic quad remeshing both need this deformation review.
3. Finalize UVs/triangulation; bake shallow detail from the dense source into normal maps. Build/reference
   textures for skin, leather and armor, then inspect the exported material appearance. Preserve actual
   geometry for ears, spikes, fingers and the important face forms. UVs and texture baking are not yet done.
4. Finalize weights and native-matched idle/walk/attack/hit/death clips with a separate attached sword.
5. Derive lower LODs after the main mesh passes motion review. Validate exports, then inspect the engine's
   actual model/skinning/material support and profile a representative group of goblins before runtime
   acceptance. A valid GLB does not establish that the character is integrated or performant in OpenYAMM.

No new paid Meshy operation is requested at this stage. First settle geometry and the deformation route.

## Triangle allocation correction after user review

The 30K trial is a uniform collapse experiment, not a sensible final allocation by part. A centroid-based
spatial audit counts 7,532 triangles (25.1%) in the belt/skirt/hip region, including the pouch and underlying
body surfaces. The narrower skirt-height band contains 4,825 triangles (16.1%), also including underlying
body surfaces. These are not exact semantic skirt-only counts. The separate twelve back-plate rivets alone
consume 1,200 triangles (4%). See `runtime_candidate_30k/triangle_allocation_audit.json`.

Prioritize simplified clothing and baked decorative detail; reserve geometry for face, silhouette and
working joints. The 30K total is not an acceptance goal: a lower total with deliberate allocation can
be better. Skinning is the bone/vertex attachment and deformation system; it is still needed to follow
body motion even without cloth physics. Normal maps supply lighting detail, not actual strip outlines,
open gaps, thickness, collision avoidance or deformation. Exact simplified part budgets remain unmeasured.

## Quad Remesher evaluation — 2026-09-24

The 200K input completed with both painted and neutral density. Both whole-body outputs lost important
face/armor forms. Neutral density gave 21,128 exported triangles but roughly 41% of body geometry in the
belt/skirt/hip region. See [trial 03 review](quad_remesh_trial_03_neutral/README.md).
The plugin has not demonstrated a better asset than the local 30K reduction. No more whole-body retries
are queued; proceed with the targeted clothing and joint work above, preserving source detail for baking.

## Evaluation correction after inspecting a shipped-style reference — 2026-09-24

The supplied Dark Knight GLB is genuinely 7,834 triangles including sword/shield, with a 2K color map,
1K normal map and 27 skin joints. [Measured reference and texture-on/off comparison](reference_asset_audit/README.md).
This demonstrates why clay-only detail comparisons cannot establish the necessary runtime triangle budget.
The earlier local 30K mesh is a diagnostic candidate, not the assumed production starting topology or minimum budget.

A [local normal-bake proof](bake_probe_30k/README.md) restores goblin surface relief without changing geometry,
although projection artifacts remain. Revise the sequence: establish essential silhouette and joint geometry,
then perform a provisional UV/bake/material comparison before deciding more geometry or extensive reconstruction
is required. Repair only demonstrated silhouette, bake or deformation failures. Final UVs/bakes follow topology acceptance.
Target roughly 8–12K total triangles including sword for the next deliberate low-mesh experiment; validate it
rather than promising this budget. Neither a good texture nor a high triangle count substitutes for deformation tests.
Earlier remesh rejections remain not-accepted candidates, but their missing-surface-detail rationale is provisional
until a baked comparison; genuine strip/silhouette distortion remains a separate issue.

## Completed clothing proof — 2026-09-24

[Skirt/belt reconstruction](skirt_rebuild_01/README.md) now provides 17 simple strips and a belt at
1,392 triangles with baked surface relief. The fused source required local covered-body reconstruction.
This is a component proof; projected border/belt fit refinement and deformation checks remain. The surrounding
source-density body is intentionally retained in the comparison, not selected as the final runtime mesh.
Use this separation of geometry and map detail for subsequent low-mesh assembly; no new Meshy references are needed
on the evidence of this test alone.

## 2026-09-24 — complete detail-reduction candidate

The local test now includes the whole character at **10,577 triangles excluding sword**, with the 1,392-triangle
rebuilt garment, 318-triangle pouch and baked back rivets. [Files, comparison and limitations](detail_rebuild_01/README.md).
Export/reimport and embedded normal pixels were checked. Geometry budgeting is now concrete; production acceptance
still requires local projection/jewelry cleanup, deformation testing, authentic color materials and weapon/animation work.
No new whole-body remesh or paid Meshy operation is pending. Routine Blender work is authorized; reuse the approved
helper and Blender launcher separately from script-writing commands to avoid unnecessary approval prompts.

## 2026-09-24 — warped Meshy rig repaired locally

[Current repair files and evidence](rig_review_01/README.md). The rig test exposed misplaced spine/neck joints
and head/neck weights tied to the shoulder. A centered local skeleton, corrected influences and retarget alignment
improve the motion without remeshing. The accepted 10,577-triangle geometry has been restored and all five clips
exported/reimported. Full-cycle walk/slash comparisons are available; final contact, grip, native actions and materials
remain separate acceptance work. Keep the corrected local rig when bringing back any future Meshy texture result.

## 2026-09-24 — upright animation correction v2

The remaining ~5-degree lateral torso bias was measured and corrected locally.
[Current files, front-view comparison and measurements](rig_review_01/README.md).
Idle/walk average within 0.02 degrees of vertical; normal sway remains.
Use the `rig_upright_v2` GLB / `rig_upright_v2` Blender scene for further motion work.

## 2026-09-24 — skirt clearance v3

The thigh-through-strip defect reported in `2034.png` is corrected with 17 baked skirt hinge controls.
[Current files and deformation review](rig_review_01/skirt_clearance/README.md).
Geometry remains 10,577 triangles; 45 joints and five clips. No sampled thigh penetration in the focused
whole/half-frame check. Grip, authentic motions, materials and runtime acceptance remain.

## 2026-09-24 — sword, finger grip and native attack

[Current combat asset, playback and verification](sword_attack_01/README.md).
Corsair-inspired separate sword, rebuilt right hand with 15 finger controls, stable weapon attachment,
armed idle/walk/run and authored 0.75-second native-style attack. 12,073 triangles including sword, 61 bones,
five clips. Original v3 is preserved. Body materials, hit/death and runtime integration remain.
