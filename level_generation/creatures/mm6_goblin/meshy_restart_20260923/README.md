# MM6 Goblin Meshy restart — 2026-09-23

Following `codex/meshy/OPENYAMM_MONSTER_3D_WORKFLOW.md` and `OPENYAMM_MONSTER_REFERENCE_PROMPTS.md`.
The current target is **animated runtime 3D**. The current stage is **lighter geometry evaluation**,
with rig deformation still untested. See [the current runtime plan](RUNTIME_3D_PLAN.md).
[Candidate comparison and repaired source](candidate_review.html).
See [master 01 findings](master_01/README.md) and [rendered review](master_01/review.html).
Previous attempts are preserved; this run starts from the native baseline Goblin, BGoblin A / merged ID 550.

- [Current runtime 3D plan](RUNTIME_3D_PLAN.md)
- [Superseded remesh operation](MESHY_STEP_02.md)
- [Previous retry operation](MESHY_STEP_01B.md)
- [Master 01 findings](master_01/README.md)
- [Previous generation operation card](MESHY_STEP_01.md)
- [Four-view upload ZIP](mm6_goblin_step01_upload.zip)
- [Visual review](review.html)
- [Identity, parts and action mapping](IDENTITY.md)
- [Run record](run.json)

## Reference review

Built-in imagegen produced the pixels. Exact prompts are in `prompts/`; input paths, hashes and generation records
are in `run.json`. Four selected images are in `references/` as front.png, left.png, back.png and right.png.
Do not upload files ending in candidate_01 or the contact sheet.

Selected after agent visual inspection for a first geometry attempt:

- Full body, consistent rest pose and approximate scale; open hands, neutral wrists, head looking forward.
- Right-hip pouch and right-ear jewelry remain on the same anatomical side; sides were generated separately.
- Lean exposed torso, two separate upper-back plates, no added full cuirass or spine strap.
- Native rear skull form clarified consistently in the two profiles.
- Front/profile/back checked together at native-size review scales (128/256/512 px of figure height).
- Same 1024×1536 canvases. Approximate colored-subject height differs by about 1.3% across views, and baseline by
  up to 22 pixels (1.4% of canvas). No independent per-view enlargement or aspect distortion was applied.

These are AI interpretations, not mathematically calibrated renders of an existing model. Tiny rivets, straps,
digit anatomy and jewelry remain interpreted; fine armor detail varies slightly between cameras. The original
BMPs govern identity and actions. The returned 3D master must resolve coherent depth and pass inspection before
paid remesh/texturing/rigging proceeds. The first source model is archived under `master_01/`; it has not passed geometry acceptance.

## Candidate changes

- front_candidate_01: rejected as the upload front because the fingers were too curled and the arms too closed.
  front.png is the targeted pose correction.
- left_candidate_01: rear skull too rounded compared with right.png and native profile.
  left.png is the targeted skull correction, retaining left-side equipment asymmetry.

## Scope

The user clarified that the active deliverable is an animated 3D character for eventual in-game use.
Billboard generation is not the current target. The dense master is retained for shape and detail baking;
the 199K reduction is an intermediate, not an accepted runtime model. A local 30K-triangle geometry trial
is being evaluated; final budget and topology depend on appearance, deformation and runtime measurements.
No runtime bindings, engine code, AGENTS.md rules or original assets were changed.
No Meshy credits were spent by the agent.

## Current Quad Remesher trial: 200K input

The dense-input attempt was cancelled near 79.78% after slow single-thread processing, without a result.
The replacement is prepared in Blender scene **MM6 Goblin - Quad Remesh 200K** with selected body
**Goblin_QR_200K_DensityGuided**: 198,000 input triangles, 9,000 target quads, adaptive size 50,
adaptive count off, density colors on, symmetry off. The two simple back plates are separate; rivets are hidden.
The dense source and first trial are preserved for reference and later detail baking.

[Prepared checkpoint](quad_remesh_trial_02_200k/prepared_trial.blend),
[settings](quad_remesh_trial_02_200k/prepared_settings.json), and
[density guide](quad_remesh_trial_02_200k/density_guide.png).
The user must click **Remesh It** in the host application under Quad Remesher's human-interaction requirement.
No replacement solver job has been started by the agent. Output still requires geometry and deformation review.

## Completed trial 02 and next comparison

Trial 02 completed, but its painted density allocation damaged torso/armor/skirt shapes.
[Measured review and comparison](quad_remesh_trial_02_200k/README.md).
The reimported GLB contains 27,320 triangles. It is archived, not accepted for texturing or rigging.
The current Blender scene is **MM6 Goblin - Quad Remesh Neutral**, prepared with the same 198K source,
9,000 target quads and **Use Vertex Color off**. This controlled trial isolates the excessive density guide.
[Prepared settings](quad_remesh_trial_03_neutral/prepared_settings.json).

## Current status: neutral remesh reviewed, targeted cleanup next

Trial 03 exported/reimported at **21,128 triangles**. It improves the skirt relative to the painted trial,
but face and armor shape loss remains unacceptable. Roughly 41% of the body triangles fall in the
belt/skirt/hip spatial region. [Review and comparison](quad_remesh_trial_03_neutral/README.md).
No further whole-body remesh is prepared. Next work is targeted clothing simplification and joint topology,
using the preserved source and the earlier local 30K trial, whose static shape remains better.
Neither is yet accepted as a rigged runtime asset. Earlier "click Remesh It" instructions are superseded.

## Current evaluation correction: maps must be included

The user's 7,834-triangle Dark Knight reference demonstrates detailed appearance with inexpensive geometry,
2K color and 1K normal maps. [Measured audit and texture-on/off comparison](reference_asset_audit/README.md).
Our clay-only reviews did not justify a 20–30K minimum. [Goblin bake proof](bake_probe_30k/README.md)
restores surface relief with unchanged geometry, with projection artifacts still to fix.
Next is a deliberately budgeted 8–12K-total experiment evaluated with provisional bake/materials and joint tests.
This supersedes selecting the 30K candidate as the default production base solely on clay appearance.

## Current result: rebuilt skirt and belt comparison

The requested local test is complete: **1,392-triangle** skirt/belt with a 2K dense-source normal bake.
[Comparison, files and limitations](skirt_rebuild_01/README.md). The 153,049-triangle whole-character file
retains source-density surroundings for review; it is not the runtime target. Covered waist/upper-thigh geometry
was reconstructed to replace the original fused shell. Original assets remain preserved. Rigging is still pending.

## Current result: complete 10,577-triangle review candidate

[Detail simplification and verified export](detail_rebuild_01/README.md) extends the rebuilt garment to a complete
low mesh with baked normal maps. Separate back rivets are baked, the pouch is 318 triangles, and the head receives
more of the geometry budget. Local bake/jewelry defects, color materials and joint deformation remain unfinished.
This is a static candidate excluding the sword; it is not accepted as a production or rigged runtime asset.

## Next operation: test the rig on the reviewed geometry

[Prepared Meshy upload and exact operation card](meshy_rig_test_01/README.md). The user accepted the static
10K appearance. The upload copy has one material and one UV set, with unchanged triangles and preserved normal
pixels. Run a Humanoid rig with a few test clips before final color texturing; do not automatically remesh again.

## Current result: local rig repair

Meshy returned a warped rig with misplaced spine/neck joints and inappropriate weights.
[Diagnosis, local repair and animated comparisons](rig_review_01/README.md). The repaired candidate restores
the accepted 10,577 triangles and includes all five returned clips on a centered 28-joint skeleton.
It still needs final motion/contact/grip and material work; no further Meshy rig/remesh retry is pending.

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
