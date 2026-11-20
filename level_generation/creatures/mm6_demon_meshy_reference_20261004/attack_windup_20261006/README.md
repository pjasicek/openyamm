# Demon attack windup reach

The attack now raises its active right arm farther before the downward/across-body strike. A smooth additional
upper-arm rotation reaches 24 degrees at the native high-claw anchor, 250 ms into the 750 ms clip. The wrist rises
from 1.55343 to 1.76167 model units: about 21.8 world units at the normal demon scale. The claws reach above the head.
The additional lift returns to zero by 375 ms, preserving the original strike and recovery.

[Before and after, front/profile](windup_comparison.png) · [Attack sequence](attack_contact.png) ·
[48 fps playback](attack_preview.mp4) · [Export checks](export_checks.json)

## Selected files

- [Editable master](mm6_demon_animation_master.blend), retaining the other selected clips, materials and sockets.
- [Portable animated GLB](mm6_demon_animated.glb).
- [Runtime GLB](mm6_demon_runtime.glb), installed as `assets_dev/worlds/mm6/models/mm6_demon.glb`.

Only the Attack clip's `mixamorig:RightArm` rotation output changes in the GLBs. Both exports retain the original
binary prefix, node hierarchy, bind data, weights, geometry, color/shadow LODs, materials, images, all other clips
and every key time. There are no additional bones, draws, runtime layers or gameplay timing changes.
The ordinary ranged fire attack shares this gesture; the two-handed spell cast remains its accepted separate clip.

## Checks

The delivered runtime export was reimported for seven front-view poses, the peak profile and a complete 36-frame
sequence at 48 fps. Front/profile comparisons and sequence contacts were inspected for reach, attachments and
clearance. Encoded playback has 36 frames and a 0.750-second duration. This is export/pose review; artistic
acceptance of the new windup remains for the user.

The focused runtime suite passed all three cases: simulation/death rules, the New Sorpigal crowd (219 models in
this run), and indoor binding. Geometry and renderer code were unchanged; no build or new FPS comparison was needed.

```sh
env OPENYAMM_REGRESSION_FILTER=mm6_demon_actor_models \
  ./build/game/openyamm --headless-run-regression-suite actors
./tools/run_demon_3d_test.sh
```

`author.py` derives the modified action from the previous selected master and transfers only the rotation accessor
into the recorded exports. `runtime_before.glb` preserves its original runtime input for reproduction. `review.py`
checks actual exports in an isolated Blender process. Run either with `tools/run_creature_blender.sh` and its
project-relative script path. The original [animation/socket revision](../animation_controller_20261006/README.md)
remains the source of accepted casting, locomotion and effects.
