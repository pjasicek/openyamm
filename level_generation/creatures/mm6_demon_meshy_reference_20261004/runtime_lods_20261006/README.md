# Runtime creature LODs — 2026-10-06

Selected and installed runtime export: `mm6_demon_lods.glb`. The full-detail editable Blender project and portable GLB in
`../texturing_fixed_20261005/` remain the authoring masters. This derived game export retains their level-zero
geometry/UVs, rig, nine clips and textures; `Demon_Death_Plume` is replaced by the shared runtime particles.

| Level | Body triangles | Body colour draws | Body shadow draws per cascade |
| --- | ---: | ---: | ---: |
| 0 | 16,474 | 4 | 1 |
| 1 | 8,237 | 4 | 1 |
| 2 | 2,980 | 4 | 1 |
| 3 | 1,019 | 4 | 1 |

The offline Blender tool decimates material regions separately and retains the original palette/material ownership.
Joint names remap exporter joint indices to the original rig. Inverse-bind and object-transform checks reject a
changed coordinate space. Colour mesh extras reference three lower meshes and four combined opaque shadow meshes;
these are renderer choices, not extra scene nodes. Exact picking and native AI still use level zero.

Generation tool: `tools/build_actor_lods.py`. Start from the prepared level-zero runtime export; already optimized
exports are rejected to prevent repeated simplification. Installed-data check: `python3 tools/test_build_actor_lods.py`.
The selected stage's canonical `../texturing_fixed_20261005/validation.json` records technical/native review.
`lods.json` records generated mesh indices and counts. `mm6_demon_lods.geometry.glb` is intermediate Blender geometry,
not a replacement rig/material deliverable.

GPU records and native captures: `output/performance/demon_lod_shadow_20261006/`.
