# Quad Remesher trial 02: reviewed 200K source with painted density

Completed and archived; **rejected as final geometry**. Target was 9,000 quads with adaptive count off,
confirmed in `submitted_settings.txt`. Actual result: 13,532 quads and 210 other polygons,
27,274 body triangles before export, 27,342 including two back plates. Reimported GLB has
**27,320 triangles**; export reduced the count by 22. Raw FBX and Blender checkpoint are preserved.

[Comparison](comparison.jpg): reviewed 199K source, previous local 30K reduction, this remesh.
The result softens facial forms, loses armor/spike shape and severely collapses belt/skirt strips.
Some shallow detail could be baked, but silhouette and strip-shape loss cannot be repaired by normal maps.

The spatial audit places 33.1% of body triangles in the head region and 32.4% in the hand regions,
leaving only 2.9% in the belt/skirt/hip region. These are approximate spatial counts, not semantic selections.
The agent's painted density contrast was too aggressive. Raw topology also contains boundary/nonmanifold
edges; this result has not passed deformation review and should not be sent for paid textures or rigging.

Next: separate trial 03 uses the same 198K body, 9,000 target and other settings with vertex-color density
**disabled**, isolating this setting. It is prepared for the user's manual Remesh It click.
No automated solver call was made. If acceptable shape cannot be retained, proceed with targeted topology
work rather than accepting damaged geometry. Dense source is retained for baking.
