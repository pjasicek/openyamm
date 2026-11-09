# Quad Remesher trial 03: neutral density

Completed and inspected on 2026-09-24. **Rejected as final geometry.**

## Result

- Same 198,000-triangle input body as trial 02; vertex-color density disabled.
- Submitted target 9,000 quads, adaptive size 50, adaptive quad count off.
- Raw result: 10,461 quads plus 168 other faces; 21,090 body triangles by polygon count.
- Raw scene including the two back plates: 21,158 triangles.
- Exported and reimported GLB: **21,128 triangles**, three meshes, no UVs, textures or rig.
- Export count differs from raw polygon triangulation count by 30; raw FBX and full Blender checkpoint retained.

## Visual findings

[Matched views](comparison.jpg) compare the 199K source, local 30K reduction, painted remesh, and neutral remesh.
The neutral result retains skirt-strip outlines better than trial 02, but severely softens eyes, mouth,
armor edges/spikes and torso forms. The earlier local 30K reduction remains the better static shape candidate.
Loss of fine engraving/rivets can be addressed with baking; the facial and silhouette losses here cannot
be accepted as merely missing textures.

The spatial audit counts 8,594 body triangles (40.75%) in the belt/skirt/hip region, including nearby
anatomy/pouch. Head region: 1,570 (7.44%); hand regions: 1,944 (9.22%). These are spatial estimates,
not exact semantic component budgets. Thus disabling painted density changes allocation but does not
solve the overly complex source clothing. Raw mesh has 59 boundary edges and 64 nonmanifold edges
(including boundaries); their presence alone is not a deformation test. Rigging remains unvalidated.

## Decision and next step

No further whole-body remesh is queued. Preserve the source and both remesh experiments.
Proceed with targeted mesh work: simplify skirt/belt strips while retaining outlines/gaps/overlaps,
retain better-preserved face/armor forms from the source/local reduction, then repair joints and test
a provisional rig and firm sword grip. The local 30K trial is a starting comparison, not an accepted rig-ready asset.
Do not send this rejected neutral remesh for paid textures or rigging.
