# Ground detail and grass options for OpenYAMM

> Superseded for the runtime renderer: the implemented grass and its level of detail are described in
> [Grass level of detail](GRASS_LOD.md). This page is the original exploration.

Exploration requested after accepting the new New Sorpigal dirt/transition work. This is a recommendation,
not an active generation goal or an implemented renderer change. Performance estimates below are qualitative;
no prototype was benchmarked for this exploration.

## Recommendation

Combine subtle world-space colour variation with short, sparse grass clumps near the camera.
Keep the accepted x2 terrain as the continuous ground beneath them. Use its palette and existing grass coverage
masks, retaining clear paths, doorways, items and the readable sprite silhouettes of MM6.

| Approach | Visual contribution | Expected cost and fit |
| --- | --- | --- |
| Broad colour variation | Uneven meadow colour across several tiles, reduced repeat visibility | Very low CPU; low GPU. First choice. A world-space texture field can add a sample; material masking can require another. Static vertex variation is cheaper but coarser. |
| Detail colour/normal mapping | Small surface variation and light response; no new silhouette | Low CPU; low/moderate GPU. Colour detail is straightforward. Normals require additional lighting/basis work in this renderer and should be subtle. |
| Instanced painted tufts | Actual ground-level silhouette, depth, gentle wind | Low CPU with persistent batches; GPU depends strongly on visible coverage and overdraw. Best companion to the existing sprite art. |
| Small opaque blade clumps | Actual depth without alpha-cutout holes | Potentially useful on mobile if cards are fill-rate bound, but thin triangles can be inefficient. More geometric appearance; profile against cards. |
| Shell grass | Short fur-like depth from stacked cutout surfaces | Small CPU possible, but repeated covered pixels increase GPU cost. Can look like a carpet and expose layers at shallow angles. Not the baseline recommendation. |
| Parallax occlusion mapping | Apparent depth within the ground texture | Additional dependent height samples; awkward at shallow angles and material boundaries. Better reserved for a later surface experiment than grass volume. |
| Dense GPU-generated blades/mesh shaders | Full meadow with detailed blade motion | Modern, scalable on suitable hardware; substantially more integration and platform requirements than this task needs. Not a baseline dependency. |

Modern implementations still use simple instancing and vertex animation. Mesh shaders are an alternative way to
generate/manage geometry, not a requirement for convincing grass or a guarantee of lower frame cost.

## Findings in this repository

- `game/shaders/fs_outdoor_terrain_fog.sc` uses `outdoor_textured_fog.sh`: terrain-array colour sampling,
  alpha cutoff, fog and local FX light attenuation. It already receives world position. It has no normal-map
  sampling or normal-dependent diffuse lighting.
- `game/outdoor/OutdoorGameView.h`: `TexturedTerrainVertex` has position/UV/control fields, no normal/tangent basis.
  Adding a normal map alone will not create the intended lighting effect.
- `game/outdoor/OutdoorRenderer.cpp`: terrain comes from the height grid's two triangles per cell. It also builds
  4096-world-unit chunks with bounds for local lighting. These are useful structural references, but the reviewed
  render loop is not a ready-made grass distance/frustum-culling implementation.
- No `setInstanceDataBuffer` use was found in the searched `engine/` and `game/` sources. bgfx itself supports
  instancing; this would be new renderer work here. A persistent static batched mesh per small patch is also viable
  for an initial experiment and does not require one gameplay object per tuft.
- The accepted grass/dirt masks are in
  `mm6_new_sorpigal_dirt_fidelity/transitions/masks/connected_v4`. They are generation assets, not currently a
  runtime grass-placement system. A compact per-tile coverage resource or baked placement data must be exported.

## Proposed first experiment

1. Add world-space, low-contrast colour variation on grass, starting around ±5% brightness with restrained
   olive/yellow tint changes. This range is an art starting point, not a measured optimum. Apply a common world-space
   field through coverage on both pure grass and transition tiles. Do not reset the field at tile boundaries.
2. Add a few painted tuft variants as two crossed cards per clump, tightly cropped to reduce empty alpha area.
   Keep them short relative to the characters' ankles, with a few taller accents away from heavily used paths.
   Match root colours to the ground and use the same fog/ambient response. Avoid strong glossy highlights.
3. Bake deterministic placements and terrain heights into a world/map presentation resource. Use the actual rendered
   terrain triangles for height interpolation, coverage masks for grass, and exclusions for roads, shore, buildings
   and steep slopes. No per-frame map-wide scattering, raycasts, physics bodies or gameplay entities.
4. Store small spatial batches and cull outside the camera/frustum and nearby detail radius. Use persistent instance
   data or static patch buffers. Animate only tips in the vertex shader with a small shared wind field; roots stay put.
   Bounds must include tip movement. Batching must still permit useful culling.
5. Thin instances by distance in a stable order and reduce their height near the end of the detail radius, leaving
   the existing terrain texture in the distance. Check transitions while walking and flying. Avoid a crawling dither
   pattern or rebuilding random placements when the camera moves.

A reasonable *starting experiment*, not a performance guarantee, is 1,000–4,000 visible two-card clumps:
4,000–16,000 triangles before any additional subdivision. GPU cost is not determined by that triangle count alone;
alpha coverage, overlap, screen resolution and small projected triangles can dominate. Restrict draw distance and
density before adding elaborate GPU culling machinery. Start with no grass shadow pass or per-blade interaction.

Use alpha cutoff and depth writes rather than sorted translucent grass. Cutout rendering still costs fragments and
can shimmer; evaluate mip/alpha coverage and available antialiasing. Do not assume discard eliminates overdraw cost.
If cutout cards are expensive on the target mobile GPU, compare a few broader opaque blade triangles instead.

Keep material variation and placements world-content driven and the rendering reusable. Start enabled only for the
New Sorpigal experiment; disabled worlds should not allocate the extra assets or perform grass updates.
Do not randomly rotate/offset completed directional terrain tiles to fight repetition: that breaks NE/SW coverage
and reviewed joins. Preserve the current land/water pack and its water-repeat/land-clamp sampling distinction.

## Compare and measure

Compare the accepted terrain, variation only, and variation plus tufts using the same map, camera, executable,
resolution, filtering and ordinary gameplay state. Include the supplied town camera, open grass at ankle height,
a hill, roads/doorways, night or fog, and an elevated flying view. Record motion to catch cutoff popping and shimmer.

Measure CPU frame cost, GPU frame cost and high-percentile frame times with GPU profiling on representative real
hardware. Add batches, submitted instances/triangles and memory/load-time deltas to the record. Existing Xvfb
software captures are suitable for static visual checks but cannot establish hardware GPU cost.
If Android is included, use a release build on a real device and check sustained performance, not just a short cold run.
Reduce density/range or use variation-only on lower tiers. Set a device-specific frame-time budget before acceptance.

## Primary sources consulted

- [bgfx examples](https://bkaradzic.github.io/bgfx/examples.html): built-in instancing and bump-mapping examples
  demonstrate the underlying API capabilities; not proof of an existing OpenYAMM integration.
- [Godot MultiMesh optimization](https://docs.godotengine.org/en/stable/tutorials/performance/using_multimesh.html):
  batching, per-instance shader data and the need for spatially separated batches when visibility is all-or-none.
- [Arm: Game, Set and Batch](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/game-set-and-batch):
  batching vegetation and reducing API overhead.
- [Arm: finding hidden mobile performance problems](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/finding-and-fixing-hidden-performance-problems-in-mobile-games-with-arm-performance-studio):
  overdraw, inefficient geometry and profiling. These risks inform the mobile recommendations above.
- [AMD GPUOpen: procedural grass rendering, 2024](https://gpuopen.com/learn/mesh_shaders/mesh_shaders-procedural_grass_rendering/):
  modern mesh-shader grass generation, blade detail reduction with distance and wind.
- [NVIDIA GPU Gems: waving grass](https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-7-rendering-countless-blades-waving-grass):
  historical crossed-card and tip-animation principles. Its period-specific hardware limits and sorting approach
  are not modern baseline requirements.
- [Epic: detail textures](https://dev.epicgames.com/documentation/en-us/unreal-engine/adding-detail-textures-to-unreal-engine-materials):
  layering colour/normal detail onto an existing surface.
- [Catlike Coding: parallax](https://catlikecoding.com/unity/tutorials/rendering/part-20/):
  author-demonstrated normal versus parallax behaviour and height-field sampling. Used for the technique, not current Unity API advice.

Style choices, proposed counts and OpenYAMM integration steps are our recommendations inferred from these techniques
and the local code, not external benchmark results.
