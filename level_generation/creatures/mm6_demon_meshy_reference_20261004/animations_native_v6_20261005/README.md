# MM6 demon tail and feet — revision 6

[Open the review](index.html), starting at Standing frame 0 in Profile.
[Compare the full profile](Profile_comparison.jpg), [compare planted feet](Foot_comparison.jpg),
or [inspect animated tails and feet](Profile_animated_poses.jpg).
Before/after models use identical cameras; native frames use nearest-neighbour enlargement.

The previous tail was fitted to front-view tips, leaving too much rearward reach in profile.
The revised curve arches from the hip, returns toward the thigh, then hangs to the tip.
Its root-to-tip depth is reduced by 28%, while the original front-view tip position and
physical bone lengths are retained. This applies to the six native states and Attack.
The additional Meshy Walking/Running clips retain their original tail motion.

Both feet have longer forefeet, wider toes and shorter, lower rear spurs. A smooth deformation
changes 1347 vertices supported by the existing foot groups. Airborne ankle paths are retained;
leg rotations are adjusted only where needed to keep the revised feet above the support plane.
The original foot orientations, lifts and pivots remain. Running uses quarter-frame leg keys
to prevent penetration between integer frames, and those keys are retained in the GLB.

The 8397 vertices, 16622 triangles, skin weights, 85-joint bind, face, bat ears, upper-body curves,
effect animations and all nine clip timings are retained from
[revision 5](../animations_native_v5_20261005/README.md). No body/root lowering was needed.
The body remains untextured clay with simple eye colours.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Animated GLB](mm6_demon_native_animations.glb)
- [Geometry and curve checks, ground contact, deformation and GLB reimport](validation.json)
- [Browser review checks](browser_validation.json)
- [Profile changes and affected vertices](profile_changes.json)

GLB reimport is checked at 1249 quarter-frame samples across all nine clips. The review contains
480 exported full-body poses and 40 before/after feature crops. Meshy Walking/Running retain their
existing wrist/knee skin creases; their revised foot region and ground contact are checked separately.
User visual acceptance is pending; these assets are not installed into the game.

## Reproduction

Import author_profile.py through Blender MCP and call apply() in the isolated
MM6_Demon_Native_Animations scene. It starts from revision 5's original geometry and actions,
so repeated authoring does not accumulate the changes. It saves authored_checkpoint.blend.
Only foot-supported vertex positions and leg/tail rotation curves change.

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v6_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v6_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v6_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v6_20261005/build_review.py
```

The Blender project includes SELECT_ANIMATION.py for selecting any clip.
Previous revision packages are preserved.
