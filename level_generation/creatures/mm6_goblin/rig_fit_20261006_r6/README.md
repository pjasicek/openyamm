# MM6 Goblin — shoulder and skirt fit R6

R6 repairs the rear shoulder weight discontinuity and brings the twelve leather skirt strips closer to the
actual hips and thighs. It retains the R5 head/neck, complete rig and all nine animation curves. This is a
review candidate; the full creature remains in revision because anatomy and motion findings are still open.

Open [the existing review page](http://127.0.0.1:8901/level_generation/creatures/mm6_goblin/review_20261006/).
R6 is selected by default. Choose **Standing**, **Back**, and **Shoulders / upper back** or **Hands / skirt**,
then switch between **Brow / jaw · R5** and **Shoulders / skirt · R6**. Camera and exact time stay fixed.
Expand **Shoulder / skirt repair** for the two supplied screenshots and identical-camera before/after renders.
Previous notes remain bound to their original model hashes.

## Cause and correction

- Shoulder skin: the earlier manual rig repair forced torso weights below abs(X)=0.22 m and arm weights
  above 0.285 m, leaving a sharp inherited boundary between them. Neighboring vertices switched from spine
  to approximately 81% upper-arm influence. A 12 mm edge became 135 mm in Standing and 242 mm in Attack.
  The rest surface was sound. R6 replaces the cutoff with a gradual torso/clavicle/arm blend across 404
  processed vertices, preserving the joint centers and topology. Worst regional edge stretch drops from
  11.26× to 2.46× in Standing and from 20.13× to 3.80× in the sampled Attack range. These numerical screens
  complement the rear skin/armor close-up review; they do not clear every possible pose.
- Skirt shape: the former circular shell was too deep front to back, and every strip received a constant
  six-degree flare. R6 fits an elliptical shell around the actual pelvis/thigh surface with a 12 mm nominal
  rest clearance and retained 3.5 mm thickness. All 288 garment vertices move; the strips remain separate.
- Skirt motion: six rigid-hinge fitting trials exposed clipping and, when lifted farther to clear it,
  unacceptable outward flips. The seventh fit transfers the nearby hips/thigh skin blend to the leather.
  This keeps the skirt near the body without corrective panel rotation curves. Skin-matched deformation
  still needs further contact refinement in extreme poses; it is not cloth collision simulation.

The first radial fit incorrectly included the lowered A-pose hands in the target surface query; the target
was corrected to the actual pelvis/thigh faces. Rejected rigid trials are diagnostic history, not the selected
model. A library-append packaging attempt dropped inactive actions from its saved master; the selected recipe
instead works directly from R5 and retains all nine actions. No paid generation or new texture job was used.

## Files and checks

- [Editable master](goblin_r6.blend), [textured GLB](goblin_r6.glb), [revision and hashes](revision.json)
- [Supplied feedback](feedback/user_feedback.json), [initial diagnosis](inspection.json)
- [Preservation](review/preservation_checks.json), [actual GLB reimport](review/export_reimport_checks.json)
- [Surface screens](review/surface_checks.json), [browser checks](browser/browser_validation.json)
- [Selected recipe](scripts/revise.py), [rejected hinge trial source](review/rejected_rigid_trial.py.txt)

Topology, UVs, R5 head/neck and every other non-cloth rest vertex, all 64 bone rest/inverse-bind matrices,
all nine action curves and exported animation samples, sword and embedded PNG/material assignments are unchanged.
652 body vertex weight sets differ in total, within shoulders and leather only.
The asset remains 14,313 triangles with at most four skin influences. 261 poses reimported from the actual GLB
match the master within 0.034 mm. 45 browser checks pass, including four model versions,
same-pose R5/R6 comparison, all clips and endpoints, saved-frame links, annotations and narrow-screen layout.

## Remaining work

Standing, Fidget and Corpse have no flagged skirt/body penetration in the sampled local surface screen.
Other clips still have flagged vertices, edge midpoints or triangle centroids; walking/running, Attack, Hit
and especially the death collapse require further cloth/contact review. Nearest signed distance is a local
diagnostic, not complete collision certification. The source Meshy Walk/Run floor penetration remains about
31/39 mm. Wrist/sword-path choreography, free-hand/skirt contact, heel/ankle shape and final likeness review
also remain open. No stage is cleared by the export or browser checks alone.

Stage 2 remains model/rig revision; stage 3 remains motion revision. User action: compare the closer skirt and
repaired shoulders and send marked exact-frame feedback as needed. Codex action: refine remaining anatomy and
cloth contacts, then gait contacts and coherent attack/hand motion. Meshy spending remains **20 / 100 credits**.
