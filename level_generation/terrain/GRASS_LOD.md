# Grass level of detail

How outdoor grass (terrain decorations) reaches the horizon at a bounded cost. It replaces the old fixed radius,
whose last half thinned tuft by tuft: running showed grass popping in across a deep band ahead, and flying above
the radius removed every tuft and exposed bare terrain colour.

## How shipped games do it

Large-scale foliage systems (Horizon Zero Dawn's GPU placement, Ghost of Tsushima's grass, Far Cry 5, Unreal's
landscape grass and Unity's terrain details) differ in where the instances come from, but they share the same
three ideas:

1. **Constant density on screen, not on the ground.** The area of a ring around the camera grows with the square
   of its distance, so a region keeps a fraction `k(d) = (near / d)^2` of its instances beyond a full-density
   radius. The total instance count then grows only with the logarithm of the range.
2. **Thinned instances grow to keep the coverage.** The survivors scale up by `s = 1 / sqrt(k)` in footprint
   (wider blades or clumps), so the field reads as equally dense while its count falls. The thinning order is
   fixed per instance, so no tuft flickers as the camera moves.
3. **The terrain carries the far field.** The ground shader blends towards the grass colour where the geometry has
   thinned out, using the same coverage. Where the last tufts fade, the ground already has their colour, so the
   edge is invisible, including from the air.

Open-world titles also generate their instances in a ring around the camera, often on the GPU, because their worlds
are streamed. MM maps are fixed 128 x 128 cells with at most about 115,000 placed tufts (7 MB), so OpenYAMM keeps
the deterministic whole-map placement and adds the LOD on top of it. Streaming placement would only become necessary
for a dense near layer beyond that budget; the node layout below would then fill its ranges on demand.

## OpenYAMM design

### Placement (load time, `scatterTerrainDecorations`)

- Unchanged placement rules: per-cell candidates, masks, exclusions, variants and tall clumps. Tufts stand on the
  materials terrain's smoothed surface.
- Every instance gets a **rank** in [0, 1) from its own random stream (`sizeWindRank.w`). The rank is its place in
  the thinning order: a tuft is drawn while `rank < k(distance)`.
- Instances are stored in a **rank quadtree** per mesh kind (grass, stones). Leaves are 2048-unit squares; each
  level up doubles the size. A node at depth `j` above the leaves holds the ranks in `[4^-(j+1), 4^-j)` of its area,
  the root everything below that. A node is therefore needed only within `near * 2^(j+1)`, and every level costs a
  similar handful of draws: coarse nodes cover large distant areas with their few low-rank tufts.
- Nodes are stored depth first and each node's instances sorted by rank, so a node draws a prefix of its range and a
  fully drawn node continues into its first child's range (draws merge).
- Node bounds include the largest LOD scale and the wind sway.

### Per frame (CPU, `TerrainDecorationRenderer::collectDraws`)

From each root: skip a subtree whose region bounds are outside the frustum or the far distance, or whose best case
`k(nearest region distance)` cannot reach the next band. Otherwise a node draws the prefix of its instances with
`rank < k(nearest own distance)` (binary search), then visits its children. The resulting ranges go through the
existing light selection and contiguous-range merging. Visibility is cached as before (camera change or 20 Hz).

### Per instance (vertex shader, `vs_terrain_decoration.sc`)

- `keep = min(1, (near / d)^2) * (1 - smoothstep(0.85 far, far, d))` with `d` the 3D camera distance.
- A tuft fades out (alpha cutoff, as before) while its rank crosses the last 20 % of `keep`; past it, the vertex
  shader collapses the card and skips its lighting, so culled tufts cost no fragments. Inside the full density
  distance every tuft stays whole (the fade compares the rank with the unclamped `(near / d)^2`).
- Scale `s = min(max_scale, 1 / sqrt(k))`: width `s^1.5`, height `s^0.5`. The card's screen area grows by `s^2`, so
  coverage stays constant to `near * max_scale`. Height grows less than width so distant tufts read as a denser mat
  rather than taller plants.
- Stones keep their full count and size to their own short distance and then fade by rank.

### Terrain (fragment shader, `outdoor_terrain_materials.sh`)

A foliage map (RGBA16F, 256 x 256 over the map, built from the placed tufts) stores the average tuft colour,
premultiplied, and the tufts' optical depth: projected card area per ground area. The terrain blends its albedo
towards that colour by

`coverage(view angle) * (1 - drawn(d)) * foliage_tint`

where `drawn(d) = k * s^2 * end fade` is the share of the coverage the geometry still supplies and
`coverage = 1 - exp(-depth * cot(elevation))` (grazing views see mostly grass, views from above see the ground
between the tufts). Close to the camera `drawn = 1` and the terrain is unchanged.

## Configuration (`worlds/<world>/terrain_decorations/<map>.yml`)

| Key | Default | Meaning |
| --- | --- | --- |
| `near_distance` | 2048 | Full density radius. |
| `far_distance` | 16384 | The last tufts fade out over its final 15 %. |
| `stone_distance` | 2048 | Stones' range (no thinning before their fade). |
| `lod_max_scale` | 2.0 | Largest compensation `s`; past `near * s` the coverage falls and the terrain takes over. |
| `foliage_tint` | 1.0 | Strength of the terrain's far grass colour (0 disables it). |

Placement, plant layers and the ground moisture tint are in [Meadow](MEADOW.md).

The previous `distance` key is gone; the map files were migrated (`near_distance` = old `distance / 2`).

## Checks

- Unit tests (`TerrainDecorationTests.cpp`): keep/scale curves, the rank bands and depth-first contiguity of the
  quadtree, bounds at the largest scale, prefix draws, the logarithmic growth with the range and the foliage map.
  On a 127 x 127 cell grass field (16 candidates per cell, camera at 180 looking along +X), the submitted instances
  were 4,400 with a 4096 range, 5,309 with 8192 and 6,152 with 16384 (22 separate ranges); flying at 4000 still
  submitted 3,846 instead of none.
- oute3 (65,554 instances in 304 nodes, full density to 3072): captures at the ground pose, at ground level and
  flying at 1500 and 4000 units against the previous renderer. The near field is unchanged; from 4000 units the old
  renderer showed no grass at all, the new one keeps sparse, wider tufts over a slightly olive ground. A temporary
  768 full-density distance confirmed the terrain tint takes over where the tufts thin.
- Cost (release, RTX 3060 Ti, OpenGL, 1600 x 900, VSync off, bgfx per-view GPU timers): at the oute3 field pose the
  main view took 454 us with grass and 391 us without (about 0.06 ms; 9,539 instances submitted in 40 ranges, close
  to the old renderer's 8,714). The terrain tint, the size compensation and the range beyond 6144 were each within
  run-to-run noise. Grass code does not appear in a CPU profile of the default New Sorpigal pose. FPS comparisons
  on a machine running other jobs (load average 28-40 during these checks) are dominated by that load; toggle
  `render grass on|off` in the console within one run instead of comparing separate launches.
- Not yet checked: the Vulkan and Android (GLES) builds, and long walking/flying sequences in motion.
