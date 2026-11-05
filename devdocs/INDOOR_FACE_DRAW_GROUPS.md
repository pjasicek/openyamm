# Indoor face draw groups

How the BLV renderer (`game/indoor/IndoorRenderer.cpp`) draws the world faces of every indoor map (MM6–MM8 dungeons,
MM9 dungeons and cities): one draw call per texture and draw state for all visible sectors together, instead of one per
texture per sector. Added 2026-11-01 as proposal 2 of [Thjorgard City's street cost](mm9_rework/CITY_STREET_COST.md),
where draw-call submission was most of a still street frame's extra time.

## Batches and groups

- **Batch** (`TexturedBatch`): one sector's faces of one texture, keyed as before by texture, sector, back sector,
  lightmap page, liquid colour (and one per translucent face). It stays the unit of visibility, of the static-light
  refresh, of mover updates, of water reflections, of the water surfaces and of the portal view's counts.
- **Draw group** (`TexturedDrawGroup`, key `IndoorFaceDrawGroupKey` in `IndoorFaceDrawGroups.h`): the batches with
  one draw state: texture (with its animation frames, size and surface material maps), lightmap page, liquid colour
  and, for a translucent face, its face index. The group owns
  the GPU resources: one dynamic vertex buffer holding its batches one after another (`groupVertexOffset`), one
  32-bit index buffer of their indices in the same order, and the lightmap UV stream of a lightmapped group.
- **Plan** (`IndoorFaceDrawPlan`): the groups' index lists and each batch's range of its list. Each frame the main
  view marks the batches it draws (visible, opaque, not a liquid that the enhanced water draws); the plan orders them
  (**Order** below) and gives about one draw per group with a drawn batch. When a draw's batches are one run of its
  group's list the draw uses the group's own index buffer; otherwise their indices are copied into one merged list (a dynamic index buffer,
  `m_mergedFaceIndexBufferHandle`). The plan and the merged upload are redone only when the drawn batches change (a
  still camera and most walking frames reuse them); a rebuild of the batches clears it.

## What forced a draw per sector, and what replaced it

| Per-draw state of the old per-sector batch | Now |
| --- | --- |
| `u_indoorFaceGrid.yz`: the sector and back sector whose portal reach gates the light grid's dynamic lights | Per vertex (`TexturedVertex::sectors`, `a_texcoord6.xy` → `v_faceInfo.xy`); the uniform keeps only `x`, grid on/off |
| `u_indoorDaylight`: the scene daylight for a sector open to the sky, zero elsewhere and on lightmapped faces | Per vertex: `TexturedVertex::daylight` (1 for `TexturedBatch::daylit`, `a_texcoord6.z` → `v_faceInfo.z`) scales the daylight, which every face draw of a map with daylight sets |
| Lightmap page and its UV stream | Group key; the group's UV stream |
| Texture, animation frame, size (sky and secret-pulse uniforms), surface material maps | Group key (texture) |
| Liquid colour (opaque water without the enhanced water renderer) | Group key |
| Translucent tint and opacity, back-to-front order | One group per translucent face; still drawn one by one, sorted (`renderTranslucentFaces`) |
| Water reflections' per-batch light lists, clip plane, bounds cull | Unchanged: reflections draw per batch, a range of its group's index buffer |
| Clip plane, fog, sky projection, secret pulse time, light grid binding, lights `{}` | Per view, the same for every draw |
| Static vertex light refresh, door/mover vertex updates | Write the batch's range of the group's vertex buffer |

Event-face highlights, blood splats, picking and decals do not use the face batches. A face hidden or retextured by an
event changes the geometry revision and rebuilds the batches and groups, as before.

**Order.** Opaque faces draw with depth test and write (`LEQUAL`), so where two faces cover a pixel at one depth the
later draw wins; the batches used to draw one by one in batch order. Merging moves a group's later batches ahead of
other groups' batches, so the plan keeps batch order for every two batches with faces that **cover the same pixels at
one depth** (`indoorFacesMeetAtOneDepth`): planes within 30 degrees of each other (coincident or back-to-back faces,
a panel up to a unit off a wall: the 24-bit depth buffer is about half a unit coarse at 3 000 units) and one reaching
the other's interior by more than 0.01. Those pairs (`addFaceDrawConflicts`: a 512-unit plan grid of the faces at
their current pose, after each rebuild and for the moved faces of a mover) are edges of an order; each re-plan draws
the drawn batches in a topological order of them, a group at a time (the group with the most batches ready, then the
ones it frees), one draw per turn. Faces that only share an edge, or meet at a larger angle (a wall on a floor, an eave
under a wall, faces crossing), tie at most along that line, about a pixel wide, and may change order.

What that costs and buys (2026-11-01, Thjorgard City): keeping every touching pair, the angled contacts included
(1 930 of its 2 280 pairs), split each street texture into 2-8 draws (Thjorgard streets 146-300 world draws); with
only the near-parallel pairs they are 100-185, and in MM6-MM8 the world draws equal the distinct textures. The price
is single pixels along contact lines: some contact lines show the other face's pixel than before (one pixel high
along an eave, a seam in Lich Lab that showed before and no longer does). Finding the pairs takes about 40 ms of
Thjorgard's 220-250 ms batch rebuild at load (3-5 ms in MM6-MM8).

## Result (2026-11-01)

See the measurement and the pixel comparison in
[CITY_STREET_COST.md, "Proposal 2: result"](mm9_rework/CITY_STREET_COST.md#proposal-2-result).

## Code and tests

| What | Where |
| --- | --- |
| Group key, plan, merged list | `game/indoor/IndoorFaceDrawGroups.h/.cpp` |
| Groups built with the batches | `IndoorRenderer::rebuildAllTexturedBatches`, `createTexturedDrawGroup` |
| Main view, per-batch draws, one draw | `submitMainViewFaces`, `submitTexturedBatch`, `submitTexturedFaces` |
| Draw order between touching faces | `indoorFacesMeetAtOneDepth`, `IndoorFaceDrawPlan::addConflict`/`update`; `IndoorRenderer::addFaceDrawConflicts` |
| Shaders | `vs_indoor_textured_lit.sc`, `vs_indoor_textured_baked.sc`, `fs_indoor_textured_lit.sc` (`v_faceInfo`) |
| Portal view count | `face_draws=` in the `[PortalView]` line, "N draws of M batches" in the readout |

Tests: `./build/tests/openyamm_unit_tests --test-case='*indoor face*'` (layout, one draw per group, the
single-run and merged cases, re-planning only on change, keys, the order of touching batches, which faces touch).
