# MM6 Goblin — brow / jaw refinement R5

The user reported excessive brow projection in R4 and compared its rounded jaw outline and side silhouette
with detailed front/profile references. R5 is a focused head correction on the retained R4 master.

Open [the existing viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_goblin/review_20261006/), choose
**Head / neck**, and switch **Face / neck · R4** to **Brow / jaw · R5**. Time and camera remain fixed.
The original model and existing hash-bound notes still load their original revisions. Expand **Latest brow /
jaw comparison** below the viewport for the supplied reference and identical-camera before/after renders.

## Diagnosis and repair

- Brow: R4 overemphasized a continuous projecting supraorbital shelf. R5 retracts its leading surface by up to
  approximately 24 mm, keeps the eyelid rim and recessed eyes, and retains compact paired brow pads.
- Front outline: the cheek-to-chin transition still formed a broad, soft U. R5 tapers the sides toward a more
  distinct chin and mandibular contour while preserving mouth width, the ears and the improved neck connection.
- Profile/hand comparison: the reference uses straight lowered arms and open fingers; the native ready pose
  has bent elbows and curled/weapon-gripping fingers. The [neutral hand check](review/after5_neutral_hand.png)
  confirms long separate fingers. Projected wrist height alone does not establish shortened arm anatomy.
- Heel/ankle: [neutral foot geometry](review/after5_neutral_feet.png) remains bulkier and less defined than the
  detailed reference. This remains an anatomy finding; it is independent of the already known stock gait floor
  penetration. Skirt panels also still flare away from the body. These regions were inspected, not corrected in R5.
- The red alignment lines are useful silhouette comparisons, not a requirement to force skull, hip, wrist and
  heel onto one rigid vertical plane. Distinguish pose and camera from real geometry before altering bone lengths.

All five supplied images are preserved in [feedback/](feedback/), with hashes in
[user_feedback.json](feedback/user_feedback.json). The detailed references guide the intended sculpt; native
sprites still establish digit count, outfit identity and actual ready/action poses. The sharper individual teeth
and darker olive appearance in the detailed reference remain differences in the retained mesh/maps.

## Selected files and verification

- [Editable master](goblin_anatomy_r5.blend) and [textured portable GLB](goblin_anatomy_r5.glb)
- [Revision / hashes](revision.json)
- [Front](review/after5_front.png), [profile](review/after5_right.png), [three-quarter](review/after5_quarter.png),
  [full-body ready profile](review/after5_body_right.png)
- [Preservation checks](review/preservation_checks.json), [actual GLB reimport checks](review/export_reimport_checks.json),
  [browser validation](browser/browser_validation.json)

580 face vertices change; no local face reversals were detected. Topology, UVs, all weights, bone hierarchy/rest,
all nine animation curves and exported samples, sword, neck/body/limb geometry and embedded PNG/material factors
are preserved. 261 reimported poses match the master within 0.019 mm. Existing Meshy Walk/Run contact penetration
remains approximately 31/39 mm; export fidelity does not clear that choreography/contact defect.

43 browser checks pass, including all three model versions, R4 comparison at the same pose, old-model frame
links, every clip/endpoint, marked notes, slow playback and narrow-screen layout. Neutral textured/clay front,
profile, three-quarter, gait, Attack, Hit and Corpse head views were inspected.

Stage 2 remains anatomy revision; stage 3 remains needs_revision. User action: review the R5 brow/jaw and clarify
the intended emphasis of the marked side comparison. Codex action: refine remaining likeness, fit skirt and
heel/ankle, then resolve gait contacts, attack path and hand/cloth issues. No new Meshy job: **20 / 100 credits**.
