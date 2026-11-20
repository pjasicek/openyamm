# MM6 demon bat ears — revision 5

[Open the review](index.html), starting at Standing frame 0.
[Compare native / previous / revised ears](Head_comparison.jpg) in front and profile views,
or [compare animated heads](Head_animated_poses.jpg) through Walk, Attack, Hit and Fidget.
Both model versions use identical cameras and framing; native crops use nearest-neighbour enlargement.

The native demon has large bat-like ears. Revision 4 still read as crown spikes above separate
lower ear folds, especially in profile. This revision removes those forms and replaces them with
one continuous, closed ear shell on each side: a broad side profile, rounded lower lobe,
raised outer rim and recessed bowl. Both ears follow the existing head bone.
The revised forehead, muzzle, jaw and eyes are retained.

All nine animation curves and the 85-joint bind are identical to
[revision 4](../animations_native_v4_20261005/README.md). Every retained vertex keeps its
position and skin weights; its world motion is identical. Ear topology changes locally:
324 previous vertices and 707 triangles are removed, 772 ear vertices and 1595 ear/attachment
triangles are added. The resulting body has 8397 vertices and 16622 triangles.
Both new ear shells are closed, and the two cut attachment regions are capped.
The body remains untextured clay with simple eye colours.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Animated GLB with all nine clips](mm6_demon_native_animations.glb)
- [Validation](validation.json): unchanged retained geometry/weights/rig/actions, closed shells and GLB reimport
- [Browser validation](browser_validation.json): every review frame/view, native anchor and ear comparison
- [Ear geometry changes](ear_geometry_changes.json)

GLB reimport is checked at 1249 quarter-frame samples. Blender's exporter drops influences
of 0.0001 or less and normalizes the remaining weights; original weights are preserved in Blender.
User visual acceptance is pending; these assets are not installed into the game.

## Reproduction

The sculpt in author_ears.py starts from revision 4's body mesh each time, removes only the
head-supported ear region, closes the attachment cuts and creates the two cupped ears.
It records previous vertex/face indices so preservation can be checked after topology changes,
and remaps the existing claw-tip index lists. Import this module through MCP, call apply()
and save the isolated scene as authored_checkpoint.blend before exporting.

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v5_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v5_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v5_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v5_20261005/build_review.py
```

The exported Blender project includes SELECT_ANIMATION.py for selecting any clip.
Previous revision packages are preserved.
