# Review-round-2 lessons for the orchestrator

Shared tools and playbooks were read-only. These are local notes for review.

- Correct palms in the source rest frame before retargeting. Use the anatomical hinge axis and a real palm normal;
  hand-bone Y or a guessed forearm roll is insufficient for beast hands.
- Preserve a fixed off-hand frame on two-handed shafts. Validate palm and every finger against the actual surface,
  then validate release too: a coarse triangle can cut the shaft after the grip interval ends.
- Source library motion supplies momentum; planted discrete steps and retiming preserve contacts. Inspect actual
  tip and edge motion rather than selecting by clip name alone. Keep Cast distinct for table spellcasters.
- Test looping clip seams separately. A non-cyclic IK pole path passed every within-clip frame but jerked on wrap;
  circular pole filtering fixed it while retaining the library hand path.
- Flat soles need a selected underside patch on the final reduced meshes. Restore a measurable sole plane at distant
  LODs and report both mesh-patch and bone-axis yaw instead of assuming the estimates are identical.
- Split, overlapping wraps cannot be classified by one artificial capped volume. Require a signed crossing through
  an actual outer panel; an inward ray must meet fabric, and a farther overlapping panel can still cover the skin.
  Assert nonempty covered sample regions: a short rest-distance cutoff can accidentally make the test vacuous.
- Keep native skin statistics and lighting gain separate. Texture-space quantiles are useful but do not certify
  native lit appearance; mottling and high muscle contrast remain artistic decisions.
- Reduce LOD0 in measured steps and rebake all maps, including tangent normals. Preserve 16 px bake dilation.
  Do not run Meshy's normal-channel conversion on an OpenGL rebake.
- Report LOD comparison baselines explicitly. This run meets 0.97 at LOD1/2 against LOD0; LOD3 meets it only against
  its incoming LOD, and that does not establish the stricter full-detail criterion. The full-detail failure stays open.
- Run the current loader and binding validators on every final GLB. Non-recolouring props omit both region keys;
  empty ramps are rejected. Shadow materials must be OPAQUE and every weight set normalized.
