# MM6 demon native animations — revision 3

[Open the review](index.html), which starts at **Attack C / frame 12**, the raised-hand pose.
[Compare native / previous / corrected Attack](Attack_right_hand_comparison.jpg).
The native panel uses one scale derived from Standing and a common ground; the two model panels
use identical orthographic cameras. No pose is independently resized to fit its hand.

The native C fingers extend up and left. The previous model's fingers curl and point toward the camera,
making its raised hand look compact. This revision reduces that foreshortening, straightens both finger
knuckles and lifts the right arm modestly while retaining physical bone lengths and rigid terminal claws.
The correction is strongest at C, blends through B/D and the E sweep, and leaves A/F's curled shape.

Only Attack's right arm, forearm, palm and four long-finger joint rotations change. All other Attack
channels, including the foot pivot, left arm, head and torso, remain identical. All eight other actions
are identical to [revision 2](../animations_native_v2_20261005/README.md), including the stronger Hit tilt
and hand reach, Fidget/Hit foot adjustments and tighter tail curve.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Animated GLB with all nine clips](mm6_demon_native_animations.glb)
- [Validation](validation.json): corrected reach, scope preservation, quarter-frame deformation and GLB comparison
- [Browser validation](browser_validation.json): every review frame/view and native anchor
- [All Attack anchors, including profile and oblique views](Attack_anchors.jpg)

Body topology, bind matrices and weights are unchanged: 7899 vertices, 15686 triangles, 85 joints.
The body remains untextured clay. The model retains four long fingers plus thumb; the native has three
plus thumb. Posing cannot remove that anatomical difference. Joint angles and hidden depth remain
authored interpretations. User visual acceptance is pending; these assets are not installed into the game.

## Reproduction

The correction in revise_attack.py starts from the previous Attack action and reuses motion.bake_action.
It copies only the changed rotation channels into the baseline action. To reauthor, append revision 2's
scene into Blender, import this module and call build() through MCP. The isolated
authored_checkpoint.blend already contains all corrected actions and synchronized effects.

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v3_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v3_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v3_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v3_20261005/build_review.py
```

The exported Blender project retains the embedded SELECT_ANIMATION.py for selecting any clip.
Previous revision packages are preserved.
