# MM6 demon native animations — revision 2

[Open the review](index.html) to compare native frames with the actual exported GLB at 48 fps.
The page includes Attack alongside Standing, Walk Native, Hit, Fidget, Death and Ash Remains.
The [editable Blender project](mm6_demon_native_animations.blend) and
[animated GLB](mm6_demon_native_animations.glb) contain all nine clips.

## Corrections from native review

- **Fidget:** slight inward right-foot shift/pivot, with a smaller left-foot adjustment. Both feet remain supported.
- **Hit:** stronger backward head tilt with sideways roll, higher left-hand reach and straighter fingers at D.
  The supporting right foot pivots/shifts slightly inward; the existing left-foot lift is retained.
- **Walk/tail:** tighter hanging curve, a raised proximal segment and a return toward the body before the blade.
  The new tail pose also applies to Standing, Hit, Fidget and the visible Death poses.
- **Attack:** checked against native feet. Its revision 3 grounded right-foot/knee pivot is already present;
  the action remains unchanged and is now available in this review.

At Hit D, the wrist reaches 0.128 m higher and the highest finger joint reaches 0.140 m higher than revision 1.
The authored head pitch increases from approximately 12° to 40° backward. These angles are interpretations
of the native silhouette, not recovered 3D measurements. At the Walk endpoint the tail's maximum rearward
bone extent decreases from 0.505 m to 0.387 m. The source model's large blade and anatomy remain intact.
See [pose comparison checks](feedback_pose_checks.json) and [native close-up measurements](native_feedback_measurements.json).

Native timing, one-shot endpoints, the disintegration effect and separate Ash Remains are retained from
[revision 1](../animations_native_20261005/README.md). Attack, Walking and Running retain their revision 3
curves and world-space mesh motion exactly. Body topology, bind matrices and weights are unchanged:
7899 vertices, 15686 triangles, 85 joints. The body remains untextured clay.

## Checks and reproduction

[Validation](validation.json) passed 1249 quarter-frame source/GLB comparisons across all nine clips,
with maximum body-coordinate error 0.00000203 m. Feet clear the floor, hard claw tips stay rigid,
bone scales stay unit, and Walk closes exactly. Effect/visibility resets pass.
[Browser validation](browser_validation.json) passed 470 frame/view states and 34 native anchor clicks.
The review contains 480 actual GLB renders, seven GIFs and seven front/profile/oblique anchor plates.
Visual acceptance remains pending user review; this package is not installed into the game.

The isolated `authored_checkpoint.blend` contains the corrected NLA actions and synchronized effects.
`motion.py` contains the pose controls and bake helper. Export, validate and rebuild the review with the
existing approved creature runner:

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v2_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v2_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v2_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_v2_20261005/build_review.py
```

In the exported Blender project, edit the embedded `SELECT_ANIMATION.py` to select a clip.
The original revision 1 and Attack revision 3 packages are preserved.
