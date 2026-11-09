# MM6 demon skull clasp — revision 7

[Open the review](index.html), starting at Standing frame 0 in Front.
[Compare the chest band and skull](Clasp_comparison.jpg),
[inspect clasp close-ups](Clasp_closeups.jpg), or
[check its animated attachment](Clasp_animated_poses.jpg).
Before/after models use identical cameras; native frames use nearest-neighbour enlargement.

The native chest band carries a skull alone. Revision 7 removes the invented hanging ring
(74 vertices, 148 triangles) and enlarges the existing skull by 60% in width and 55% in height.
Its depth is reduced by 60% and it sits directly on the band. The skull's 249 vertices and
494 triangles are retained; it is weighted rigidly to the existing Bone_024 chest attachment.

The delivered body contains 8323 vertices and 16474 triangles. All remaining body/harness
geometry and weights, the 85-joint bind, and all nine animation curves match
[revision 6](../animations_native_v6_20261005/README.md) exactly. The previous head, bat ears,
tail, feet, hand corrections and disintegration are retained. The body remains untextured
clay with simple eye colours; skull surface colour and detail remain part of texturing.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Animated GLB](mm6_demon_native_animations.glb)
- [Geometry, curve, deformation and GLB reimport checks](validation.json)
- [Browser review checks](browser_validation.json)
- [Clasp dimensions and affected vertices](clasp_changes.json)

GLB reimport is checked at 1249 quarter-frame samples across all nine clips. The review contains
480 exported full-body poses and 60 before/after clasp crops. The browser check covers
470 frame/view states, 34 native anchors, exact native pixels, playback and Death/Ash transitions.
User visual acceptance is pending; these assets are not installed into the game.

## Reproduction

Import author_clasp.py through Blender MCP and call apply() in the existing
MM6_Demon_Native_Animations scene with revision 6's actions. It starts from revision 6's
original mesh, so repeated authoring does not accumulate changes, and saves authored_checkpoint.blend.
Only the ring geometry and skull coordinates/weights change.

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v7_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v7_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v7_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v7_20261005/build_review.py
```

The Blender project includes SELECT_ANIMATION.py for selecting any clip.
Previous revision exports are preserved. Earlier head/ear/profile authoring files and reports
are historical context; their vertex indices refer to their own revisions, not this mesh.
