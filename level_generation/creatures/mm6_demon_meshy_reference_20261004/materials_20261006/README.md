# Demon material touch-up — 2026-10-06

Installed local edits to the existing Meshy textures: richer jade leather on charcoal A, green skin and
ochre leather on B, and warm dark red skin with a distinct crimson harness on C. The previous muted
green/mauve maps are preserved in [the expression revision](../expression_20261006/README.md).
This is an artistic adjustment guided by the restored variant views, not an exact recovery of the original artwork.

[Native before](review/before_daylight.png) and [native after](review/after_daylight.png) use the same camera,
three paused Standing poses, native tier sizes and 1600×900 NVIDIA/OpenGL rendering.
[Seven live actors](review/seven_demons_native.png) use the normal test's three A, two B and two C actors.
[Exported front/profile/back views](review/) were inspected for all three skins in neutral Blender lighting.

The roughness maps now distinguish rough skin, matte leather and smoother bone/claws. Normal-map strength
is 0.75 to reduce the dominance of fine scale detail over the larger forms. Existing normal images,
variant iris colors, black pupils, white claw colors and the different variants' bone pigments are retained.
The already implemented scene sunlight, local lights, shadows and sky reflections remain authoritative;
this pass changes no renderer code or global lighting settings. New AO baking is outside this adjustment.

- Editable [material master](mm6_demon_materials_master.blend), with updated maps packed.
- Portable [animated GLB](mm6_demon_animated.glb).
- [Runtime GLB](mm6_demon_runtime.glb), installed at `assets_dev/worlds/mm6/models/mm6_demon.glb`.
- [Offline texture edits and preservation checks](tune.py), [master update](master.py), [export review](review.py).
- [Verification](verification.json) and [consumer checks](checks.json).

Every non-image buffer view is preserved byte-for-byte, including sparse plume data. Geometry, UVs,
weights, rig, sockets, all ten clips, material-variant mappings and four color/shadow LODs are unchanged.
Color triangle counts remain 16,474 / 8,237 / 2,980 / 1,019. Image count and dimensions are unchanged:
the edits add no texture samples, draw calls, GPU texture storage or per-frame processing.
The fixed-pose diagnostic used temporary per-variant copies, so its memory/FPS counters are not a production benchmark.
No new controlled performance measurement was claimed.

Four focused actor regressions passed: simulation/death rules, shared variants/native stats/tier scaling,
New Sorpigal crowd and indoor binding. Technical and agent visual review are complete; artistic acceptance
is pending. Restart with `./tools/run_demon_3d_test.sh` to review the installed seven actors.

Reproduction: claim the creature project, run `python3 materials_20261006/tune.py <lease-token>`
from the project directory, then use `tools/run_creature_blender.sh --token <lease-token>` on
`materials_20261006/master.py` and `materials_20261006/review.py` from the repository root.
These scripts use the preserved expression revision as their input and write only this material revision;
installation is a separate copy of the verified runtime GLB.
