# MM6 demon head refinement — revision 4

[Open the review](index.html), starting at Standing frame 0.
[Compare native / previous / refined heads](Head_comparison.jpg) in front and profile views,
or [compare animated heads](Head_animated_poses.jpg) at Walk, Attack, Hit and Fidget poses.
Both model versions use identical cameras and framing; the native crops use nearest-neighbour enlargement.

The head now has a rounder rear skull, wider muzzle and lower jaw, softer inner brow,
larger pink eyes with dark pupils, thinner upright ear blades and raised lower ear folds.
The existing jaw hinge and teeth are retained. The eyes follow the existing head bone.
This is a local reshaping of the Meshy head, rather than a complete reconstruction of the native anatomy.

All nine animation curves, the 85-joint bind and original vertex weights are identical to
[revision 3](../animations_native_v3_20261005/README.md). Geometry outside the edited head
is identical, including the previously corrected hands, feet and tail. Original connectivity
is preserved; two small pupil caps add 50 vertices and 48 triangles. The delivered body has
7949 vertices and 15734 triangles. The body remains untextured clay with simple eye colours.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Animated GLB with all nine clips](mm6_demon_native_animations.glb)
- [Validation](validation.json): preserved geometry/rig/actions, deformation and actual GLB reimport
- [Browser validation](browser_validation.json): every review frame/view, native anchor and head comparison
- [Head geometry changes](head_geometry_changes.json)

GLB reimport is checked at 1249 quarter-frame samples. Blender's exporter drops influences
of 0.0001 or less and normalizes the remaining weights; the original Blender weights are kept
and the exported poses differ by at most 0.0000021 metres.
User visual acceptance is pending; these assets are not installed into the game.

## Reproduction

The sculpt in author_head.py starts from original rest coordinates, edits head-supported vertices
and rebuilds the pupil caps without accumulating the reshape. Append revision 3's scene into
Blender, copy the body mesh datablock to preserve the source, then import this module and call
apply() through MCP. Save the isolated scene as authored_checkpoint.blend before exporting.

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v4_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v4_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v4_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v4_20261005/build_review.py
```

The exported Blender project includes SELECT_ANIMATION.py for selecting any clip.
Previous revision packages are preserved.
