# Demon expression correction — 2026-10-06

The selected shared head now has a heavier, lower inner brow, a less raised forehead, a taller mouth opening,
a squarer lower jaw and less raised mouth corners. The native/restored large eyes are retained. The result
is intended to read as a tooth-baring snarl rather than a cheerful grin.

Matching-camera exported renders: [before](review/before_a_front.png), [after A](review/after_a_front.png),
[after B](review/after_b_front.png), [after C](review/after_c_front.png).
Clay, profile, oblique and Attack/Hit/Cast samples are in [review](review/).

Source: the [A/B/C variants revision](../variants_20261006/README.md), with its skins, black pupils,
white claws and all ten clips retained. No Meshy request, replacement texture, rerigging or engine change was needed.
The edit moves existing vertices in rest space; it retains connectivity, UVs, joint weights and bind data.
Vertex normals follow the deformation. Existing normal maps remain unchanged.

The runtime applies the same local sculpt to all four color LODs and copies their revised positions/normals
into the corresponding merged shadow meshes. Triangle counts remain **16,474 / 8,237 / 2,980 / 1,019**;
no extra vertices, material sections or draw calls are added. The portable animated GLB retains its original
full-detail mesh and sparse death-plume morphs. Its bytes outside the edited geometry are preserved.

- Editable [expression master](mm6_demon_expression_master.blend).
- Portable [animated GLB](mm6_demon_animated.glb).
- Installed [runtime GLB](../../../../assets_dev/worlds/mm6/models/mm6_demon.glb).
- [Reproducible sculpt and preservation assertions](sculpt.py), [verification](verification.json).

[Checks](checks.json): four focused headless regressions passed, covering native stats, tier scales,
shared assets, FX/animation/death behavior and indoor binding. NVIDIA/OpenGL native captures:
[seven A/B/C actors](review/seven_demons_native.png) and [forced LOD1](review/forced_lod1_native.png).
Blender's forced-LOD imports show artifacts on the previous source too; use native GPU evidence for LOD appearance.

Technical/agent review and user artistic acceptance are separate; this revision is ready for user review.
Run `./tools/run_demon_3d_test.sh` after restarting the game to review all seven A/B/C actors.
