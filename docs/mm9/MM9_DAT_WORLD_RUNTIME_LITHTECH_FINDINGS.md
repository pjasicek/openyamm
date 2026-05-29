# MM9 DAT World Runtime LithTech Findings

Status: implementation findings for the OpenYAMM MM9 DAT world runtime. This document translates the local
`mm9/lithtech/*` engine reference into practical runtime architecture, performance constraints, and glitch-prevention
rules for OpenYAMM.

## Objective

Implement a performant MM9 DAT world runtime in `game/mm9/*` that can render, collide, pick, move mechanisms, and feed
MM9 script/object systems without overfitting OpenYAMM's shared engine to LithTech internals.

The goal is not to clone LithTech. The goal is to preserve the proven runtime split:

- parsed source DAT data stays authoritative;
- static visual geometry is preprocessed into render-friendly batches;
- collision uses a separate query structure from visual render batches;
- moving doors/platforms/mechanisms are world-model instances with stable transforms;
- dynamic objects live in a broadphase/index, not in the static mesh;
- script objects communicate by stable object handles and routed events.

## Read First

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`: local MM9 DAT v66 parser contract and verified deviations.
- `docs/mm9/MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md`: script commands waiting on DAT world services.
- `game/mm9/Mm9DatWorld.*`: current parser/runtime source structures.
- `game/mm9/Mm9DatPhysicsQuery.*`: current DAT physics/query surface.
- `game/mm9/Mm9ObjectLayer.*`: current source-object projection.
- `game/mm9/Mm9LightLayer.*`: current light/source projection.
- `game/mm9/Mm9SkyLayer.*`: current sky object/source-world projection.
- `game/mm9/Mm9ScriptedObjectRuntime.*`: current scripted object movement/property projection, including
  `MoveToFloor`.
- `editor/document/EditorDocument.cpp`: current editor DAT level load path using the shared `game/mm9` primitives.
- `editor/viewport/EditorOutdoorViewport.cpp`: current editor proof of DAT render batching, DTX texture use, overlays,
  and mechanism preview transforms.
- `tests/Mm9DatWorldTests.cpp`: render filtering coverage, including helper, sky, rail, terrain, and visible-water
  splits.
- `tests/Mm9DatPhysicsQueryTests.cpp`: physics/visible channel query coverage against real DAT helper geometry.
- `mm9/lithtech/runtime/world/src/*`: shared/client/server BSP reference.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/*`: render-block and visibility reference.
- `mm9/lithtech/runtime/shared/src/*`: movement and collision reference.
- `mm9/lithtech/tools/PreProcessor/*`: preprocessed world/render/collision data reference.

## Version Caveat

The local LithTech runtime and preprocessor tree is a strong architectural reference, but it is not an exact binary
reference for MM9 DAT files.

- OpenYAMM has locally verified MM9 world DAT files as version `66`.
- The inspected LithTech PC runtime/preprocessor path uses `CURRENT_WORLD_VERSION` / `CURRENT_DAT_VERSION` `85`.
- MM9 v66 has verified layout differences from public v66 references, such as the `UserPortal` record shape.
- Therefore, use `docs/mm9/MM9_DAT_FORMAT_NOTES.md` and all-world parse validation as the binary authority.
- Use `mm9/lithtech/*` for runtime responsibilities, data separation, culling shape, mechanism behavior, collision
  shape, and performance constraints.

## Core Finding

The local LithTech tree contains a complete processed-world runtime architecture:

- shared world/BSP load;
- client render-data load;
- D3D render-block rendering;
- dynamic-object visibility sets;
- moving world-model rendering;
- server/client collision and ray queries;
- tool/preprocessor code that creates world tree, physics BSP, render blocks, lightmaps, light groups, blockers, and
  object data.

It does not give us a ready-to-use MM9 v66 DAT runtime because MM9's shipped DAT format is older and locally different.
OpenYAMM should implement a native MM9 DAT runtime using the same split, not try to load v66 data through v85 structs.

## LithTech Runtime Split

LithTech separates the processed world into several cooperating layers:

- `WorldBsp`
  - BSP planes, nodes, surfaces, polygons, points, texture names, world-model flags, and world-model name.
  - Loaded by `WorldBsp::Load` in `mm9/lithtech/runtime/world/src/de_mainworld.cpp`.
- `WorldData`
  - Owns an original BSP and, for moveable world models, an optional transformed BSP.
  - The transformed BSP is used for world-model collision.
- `WorldTree`
  - Broadphase tree for dynamic objects, lights, and always-visible objects.
  - Used for object visibility and object/object collision candidates.
- `IWorldSharedBSP`
  - Shared client/server world data: world extents, world tree layout, world models, static lights, light grid,
    blocker data, particle blocker data, render-data position.
- `IWorldClientBSP`
  - Client load path that reads render data through the renderer.
- `IWorldServerBSP`
  - Server load path that exposes world intersections and movement collision.
- `CD3D_RenderWorld` / `CD3D_RenderBlock`
  - Renderer-owned optimized static geometry tree with sections, shaders, textures, lightmaps, sky portals, occluders,
    light groups, and child render blocks.

OpenYAMM should mirror this conceptually:

- parsed `Mm9DatWorld` is source data;
- a runtime world instance owns render partitions, collision structures, mechanism instances, and object indices;
- renderer-facing data is not the same structure as collision-facing data;
- dynamic/script objects are indexed separately from static world triangles;
- save/load persists dynamic state, not the static parsed DAT.

## World Loading Findings

LithTech v85 load sequence:

1. Read header offsets and world info.
2. Read world extents and source-world offset.
3. Load `WorldTree` layout.
4. Load each `WorldData` / `WorldBsp`.
5. If a world model is moveable, load or create an additional transformed BSP.
6. Calculate bounding spheres for world models and polygons.
7. Parse static light objects and insert lights into `WorldTree`.
8. Load light grid.
9. Load blocker data and particle blocker data.
10. Load renderer-specific render data.

OpenYAMM implication:

- Keep DAT parse as a source pass.
- Build a separate runtime-load pass that derives:
  - visual render groups;
  - collision BSP/BVH/query structures;
  - raycast/picking structures;
  - mechanism/world-model instances;
  - dynamic object registry;
  - light runtime data.
- Do not use YAML/sidecar map output as the hot runtime format once DAT runtime exists. Sidecars are validation and
  source-preservation aids, not final per-frame structures.

## Leafs, Portals, And Visibility

Do not assume the inspected LithTech v85 path is a classic leaf-PVS renderer.

The v85 preprocessor writes zero for user portals, leaf count, vis list size, and leaf lists in its `WriteWorldBspData`
path, and comments that the engine no longer uses those structures. Runtime `WorldBsp::Load` still has compatibility
code to skip leaf lists, but the active render path is render blocks plus frustum/occluder culling.

MM9 v66 is different:

- local MM9 DATs do contain leaf data and user portals;
- the parser decodes BSP leaf polygon references for all local worlds;
- user portals are real source data and should be preserved.

OpenYAMM rules:

- Parse and preserve MM9 leaf/user-portal data exactly.
- Do not block first runtime rendering on reconstructing exact LithTech leaf PVS.
- Use DAT leaves/portals as hints for sectors, visibility, and diagnostics.
- Start with robust frustum culling over render partitions.
- Add portal/sector visibility only when the decoded MM9 portal semantics are validated by screenshots and traversal
  tests.
- Never discard geometry because a leaf/portal interpretation is uncertain. Prefer drawing too much over missing walls.

## Static Rendering Findings

LithTech v85 does not draw directly from `WorldBsp` polygon arrays. It draws renderer-specific render blocks:

- render blocks have bounds;
- each block contains sections grouped by shader/texture/lightmap;
- each section points into packed vertices and indices;
- render blocks form a child tree;
- the renderer collects visible render blocks, then draws section shaders;
- sky portals and occluders are part of render-block data;
- lightmap and light-group data are bound into the render-block shader path.

OpenYAMM implementation shape:

- Convert DAT visual polygons into bgfx-friendly immutable vertex/index buffers.
- Partition triangles by:
  - world model;
  - material/texture/effect state;
  - opacity/blend mode;
  - lightmap/light mode when implemented;
  - spatial block.
- Build one or more spatial trees over render partitions.
- Keep helper BSPs and invisible/helper surfaces out of visual buffers unless explicitly drawing diagnostics.
- Preserve source polygon ids for picking, debugging, collision diagnostics, and script linkage.
- Keep generated material aliases map-local because MM9 maps reuse short texture aliases for different source DTX files.

Minimum first renderer:

- static opaque DAT geometry;
- static translucent/additive geometry in a separate pass;
- per-map texture/material alias resolution;
- frustum culling by render partition bounds;
- optional debug draw for raw BSP/helper surfaces.

Do not start by submitting one draw per polygon. That will be too slow and will make later lightmap/material work
harder.

## Existing Editor DAT Rendering Findings

The editor already proves a large part of the native MM9 DAT data path:

- `EditorDocument` loads `.level.yml`, resolves the source DAT, parses `Mm9DatWorld`, builds `Mm9DatRenderMesh`,
  computes DAT render bounds, loads sidecars, assigns material aliases, and builds object, light, sound, and spawn
  layers from the same `game/mm9` primitives.
- `EditorOutdoorViewport` classifies DAT triangles with sidecar world-model roles, then groups vertices by source model
  and resolved DTX texture instead of submitting one polygon at a time.
- DTX textures are decoded and cached by source path before bgfx texture creation.
- Normal editor rendering skips helper/invisible/trigger/visibility/water-volume triangles unless a diagnostic subset
  is selected.
- The editor keeps fallback procedural batches for missing material/debug views and overlay buffers for portals,
  world-model bounds, object bounds, mechanisms, and asset issues.
- Mechanism preview rendering already groups transforms by source model and applies linear/rotating motion to batches
  without rebuilding the static vertex buffers.

Runtime implication:

- Reuse the proven `game/mm9` parser, render-mesh, filter, material, DTX, object, light, sound, spawn, and event data
  products.
- Port the small mechanism-transform math and policies into `game/mm9/*`; do not make runtime depend on editor
  viewport classes.
- Use the editor's grouping as the minimum performance floor: group by source model, material/texture, blend state, and
  later spatial chunk. Do not regress to per-triangle draw submission.
- Preserve editor diagnostics as runtime counters where useful: resolved/missing material batches, active/inert
  mechanisms, helper geometry counts, source-model draw counts, and texture cache misses.
- Treat the current editor ocean/sky path as proof of source classification, not final gameplay semantics. Visible
  ocean can be rendered as visual water first; water volumes, sky camera mapping, and exact ocean height still need
  runtime validation.

## Render-Block Culling And Performance

LithTech render performance comes from avoiding per-polygon work:

- `CD3D_RenderWorld::Draw` collects visible render blocks, not visible polygons.
- transformed world models bypass some occlusion/frustum work and render all blocks with the world-model transform.
- render blocks are pre-bound to shaders and buffers.
- frame stats track world block culling, object culling, texture memory, and render-block draw counts.

OpenYAMM rules:

- Per-frame render traversal should operate on blocks/chunks, not triangles.
- Draw call count should be proportional to visible material sections, not source polygon count.
- Bounds should be stable and precomputed.
- Updating a moving mechanism should update instance transform and broadphase bounds, not rebuild static geometry.
- Keep instrumentation from the start:
  - visible render blocks;
  - triangles submitted;
  - draw calls;
  - culled blocks;
  - material switches;
  - mechanism instances drawn;
  - collision/raycast query counts.

## World Models And Mechanisms

LithTech represents doors, platforms, and moving brush/mechanism geometry as world models:

- a world model has a named original BSP;
- moveable world models can have a transformed BSP for collision;
- rendering finds the named renderer world model and draws it with the instance transform;
- rotation and movement update object transforms, bounds, and collision state;
- objects standing on a moving/rotating world model are moved or detached depending on flags;
- collision can push objects away, crush them, or send touch notifications.

OpenYAMM implementation shape:

- Treat each DAT world model as a stable source world-model definition.
- Treat each placed mechanism as a runtime instance:
  - stable object handle;
  - source world-model id/name;
  - transform;
  - bounds;
  - visibility/solid/ray-hit/touch flags;
  - script binding/object binding.
- Static main world and helper BSPs are definitions, not interactive object instances unless DAT objects bind to them.
- Render mechanisms by instancing prebuilt world-model render buffers with a transform.
- Collision mechanisms need a transformed collision representation or a query transform back into local BSP space.

Important performance decision:

- Prefer transforming queries into the mechanism's local space over rewriting all mechanism collision vertices every
  frame.
- Cache transformed bounds for broadphase.
- Only rebuild transformed collision data if query-local-space collision proves too complex or too slow.

## Partial Geometry Rebuilds

LithTech's `w_TransformWorldModel` can transform points, planes, and polygon centers into a second BSP. Its partial path
returns early for box-physics world models. Rendering does not rebuild geometry; it uses the world transform.

OpenYAMM rules:

- Static render buffers are immutable after load.
- Moving world-model render buffers are also immutable; draw with instance transform.
- Collision should avoid full vertex rebuilds per frame.
- Mechanism movement should update:
  - transform;
  - inverse transform;
  - world-space AABB;
  - broadphase membership;
  - dirty flags for dependent standing/carrying objects.
- Only rebuild derived collision caches when transform changes and a cached representation is actually needed.

## Collision Findings

LithTech collision is split into several paths:

- dynamic object broadphase via `WorldTree::FindObjectsInBox`;
- world collision against `WorldBsp`;
- world-model collision through a world model's valid BSP;
- player-specific blocker polys;
- stair-step handling;
- standing-on tracking;
- touch/crush notifications;
- swept sphere and segment intersection helpers.

OpenYAMM implementation shape:

- Provide one MM9 DAT world query service, used by movement, projectiles, scripts, picking, and AI:
  - segment/raycast;
  - swept sphere/capsule or actor hull sweep;
  - AABB overlap;
  - floor/support query;
  - line-of-sight query;
  - material/surface query.
- Keep collision geometry separate from visual render geometry.
- Treat `PhysicsBSP` and invisible/helper surfaces as collision candidates, not visual art.
- Treat `VisBSP` as visibility/source metadata until semantics are proven.
- Surface flags and DTX surface metadata should be preserved for footstep/material behavior.
- Collision results must return source world-model id, polygon id, surface/material, normal, hit position, and object
  handle when applicable.

Glitch-prevention rules:

- Use the same coordinate conversion everywhere: LithTech `(x, y, z)` maps to OpenYAMM `(x, z, y)`.
- Keep winding and normals validated after conversion.
- Do not mix visual helper surfaces into collision blindly.
- Do not let rendering use one transform while collision uses another.
- For moving mechanisms, update broadphase bounds immediately when transform changes.
- Standing/floor resolution must account for moving world models, not only static terrain.

## Dynamic Object Broadphase

LithTech stores dynamic objects in a `WorldTree` and uses frame codes to avoid duplicate callbacks when objects overlap
multiple nodes. Box queries skip empty branches and test object bounds before invoking callbacks.

OpenYAMM rules:

- Build a dynamic object broadphase for MM9 runtime objects:
  - actors;
  - pickups/props;
  - trigger volumes;
  - moving world models;
  - lights/effects where spatial queries need them.
- Use stable object indices plus handles, not string lookup in hot queries.
- Use per-query generation ids or small visited sets to avoid duplicate hits.
- Keep active/renderable/collidable/ray-hit/trigger/interactable views separate.
- Update membership on state/flag changes, not by scanning every object every frame.

First implementation can use a simple grid or BVH. The API must not require future linear scans.

## Object Visibility And Draw Lists

LithTech builds a visible set per frame:

- renderable objects are filtered by visibility flags, object group, sky-object flags, and optional world occlusion;
- object sets have fixed/default capacities and diagnostics on overflow;
- object rendering is ordered by type and blend mode.

OpenYAMM rules:

- Keep MM9 object rendering separate from static DAT rendering.
- Build per-frame lists for:
  - opaque static world sections;
  - translucent static world sections;
  - opaque mechanisms;
  - translucent mechanisms;
  - actors/models;
  - billboards/sprites/FX;
  - lights if renderer needs visible light lists.
- Overflow should not silently drop objects. Use growing vectors with reserve and diagnostics when thresholds are
  exceeded.
- Use flags from MM9 object state to update render/pick/collision membership.

## Object Placement And MoveToFloor

LithTech does not globally clamp every object to the floor when a world loads. Floor placement is class/property-driven:

- `MoveObjectToFloor` in `mm9/lithtech/NOLF/ObjectDLL/ServerUtilities.cpp` casts downward from the object's current
  position, intersects solid world/object geometry, and moves the object down only when the hit point is farther below
  the object than its vertical half-dims. The final height is effectively floor hit height plus object half-height plus
  a small bias.
- `Prop` exposes `MoveToFloor` with a true default and performs the snap on its first update only when enabled.
- `PickupItem` exposes the same property, but dynamically created pickup items default it off and only schedule the
  one-shot first update when needed.
- `Character` performs the snap during initial update when `m_bMoveToFloor` is true.
- Several specialized interactables and special actors opt out with hidden or false defaults, while teleport/startpoint
  style objects preserve an explicit `MoveToFloor` property for spawn placement.

OpenYAMM rules:

- Do not apply a universal "snap all MM9 objects to terrain/floor" pass.
- Preserve authored positions by default. If an object starts slightly above floor, assume that may be intentional until
  its class/property policy says otherwise.
- Use the parsed `MoveToFloor` property from raw/scripted objects. `Mm9ScriptedObjectRuntime` already projects this
  into movement state with a true default, so the runtime slice should consume that value instead of reparsing strings
  in hot code.
- Apply floor placement only during object spawn/initialization or explicit teleport/startpoint logic, not every frame.
- Implement floor placement as a bounded downward support query through `Mm9DatCollisionWorld`/`Mm9DatPhysicsQuery`.
  The result should preserve X/Z, set Y from floor hit plus actor/object half-height plus a small bias, and record a
  diagnostic when no support is found.
- Flying/swimming/special actors, sky/water helpers, mechanisms/world models, triggers, rails, and authored helper
  objects must not be floor-snapped unless their own object policy explicitly says so.
- If Guberland/Guberland City objects appear above terrain, first inspect `MoveToFloor` and class policy. Do not hide a
  coordinate-conversion or support-query bug by clamping everything.

Runtime diagnostics should expose:

- objects with `MoveToFloor=true` and a successful support snap;
- objects with `MoveToFloor=true` but no support hit;
- objects with `MoveToFloor=false` that remain above/below nearby support;
- skipped classes such as mechanisms, helper objects, sky, water, and trigger-only objects.

## Picking And Raycasts

LithTech has both renderer-side triangle ray support and world/server intersection support. OpenYAMM should avoid
divergence:

- gameplay raycasts should use the DAT collision/query service;
- editor/diagnostic picking may use render triangles if it returns source polygon ids;
- user interaction picking should agree with gameplay raycasts when possible.

Rules:

- Every visual triangle should retain source world-model/polygon/material ids.
- Every collision triangle should retain source world-model/polygon/material ids.
- If visual and collision geometry differ, the hit result must say which domain was queried.
- Scripts such as clear-shot and target checks should use gameplay collision, not render picking.

## Lighting And Lightgroups

LithTech's v85 path has:

- static light objects parsed from object data;
- light grid loaded into shared world data;
- renderer lightmaps in render-block sections;
- light groups that can update light table/render-block data;
- dynamic object lighting through nearby/static light queries.

OpenYAMM rules:

- Do not make lighting block first correct geometry/collision.
- Preserve light source objects and light group metadata now.
- Static geometry should initially support a simple material/light model, then add MM9-specific lightmaps or baked light
  data once render-data semantics are verified.
- Runtime light groups should be represented as named/id-controlled state so scripts can later change them.
- Dynamic object lighting should query nearby/source lights through a spatial light index, not scan all lights.

## Helper BSPs And Invisible Geometry

MM9 DATs include special world models such as `PhysicsBSP` and `VisBSP`.

Rules:

- Preserve these models as source data.
- Do not render `PhysicsBSP` as normal art.
- Use `PhysicsBSP` for collision when it is present and validated.
- Treat `VisBSP` as visibility helper metadata until proven otherwise.
- Invisible/helper surfaces should be draw-disabled by default but available in debug overlays.
- Collision inclusion must be based on surface/model role, not only texture name.

## OpenYAMM Runtime Components

Recommended `game/mm9/*` ownership split:

- `Mm9DatWorld`
  - parsed immutable source DAT data.
- `Mm9DatWorldRuntime`
  - loaded map instance, runtime state, object/mechanism registries, and service entry points.
- `Mm9DatRenderWorld`
  - render partitions, bgfx buffers, material sections, and render stats.
- `Mm9DatCollisionWorld`
  - collision/query structures for static world, helper BSPs, and mechanisms.
- `Mm9DatMechanismRuntime`
  - moving world-model instances, transforms, broadphase membership, standing/carrying interactions.
- `Mm9DatObjectBroadphase`
  - dynamic objects, triggers, interactables, and query acceleration.
- `Mm9DatWorldQueries`
  - common query API used by scripts, AI, movement, projectiles, and picking.

These names are ownership guidance, not mandatory class names. Avoid adapter layers that only forward to another owner.

## Integration With Existing Engine

Use shared engine systems where they already make sense:

- bgfx renderer backend;
- shared actor/gameplay services for actor behavior;
- shared audio, dialogue, inventory, save/load, and UI systems;
- shared package/content mounting.

Keep MM9-specific world concerns in `game/mm9/*`:

- DAT world-model definitions;
- MM9 object handles and DAT source object mapping;
- LithTech-style flags and world-model movement;
- MM9 collision/raycast quirks;
- MM9 helper BSP roles;
- MM9 script callback dispatch from DAT movement/collision events.

Do not move MM6-MM8 indoor/outdoor world representation toward LithTech just because MM9 needs these services.

## Implementation Order

Recommended slices:

1. Source-to-runtime registry
   - stable world-model ids;
   - stable polygon ids;
   - object handles;
   - helper-model roles;
   - source metadata preservation.
2. Static visual renderer
   - render partitions;
   - material grouping;
   - opaque/translucent pass split;
   - frustum culling;
   - source-id debug picking.
3. Static collision/query service
   - raycast;
   - floor/support query;
   - swept actor hull;
   - helper BSP inclusion;
   - material/surface result metadata.
4. Dynamic object broadphase
   - actors;
   - trigger volumes;
   - interactables;
   - ray-hit/pickable views.
5. Mechanism/world-model runtime
   - transform;
   - render instancing;
   - transformed collision queries;
   - standing/carrying update;
   - touch/crush/callback events.
6. Script/AI integration
   - movement requests consume DAT collision;
   - `IsClearShot`, `FindTargets`, `GetObjects`, `OnTouchNotify`, `OnObstacle`, and related callbacks use the runtime
     query service.
7. Lighting/lightgroups
   - preserve and expose light sources first;
   - add static/baked lighting only after visual/collision correctness is stable.

## Performance Constraints

Hard constraints for the OpenYAMM implementation:

- No per-frame all-polygon scans.
- No per-frame all-object string lookup.
- No draw-per-polygon static rendering.
- No full collision mesh rebuild for every moving mechanism tick.
- No duplicate visual/collision transform authority.
- No silent overflow/drop of visible objects or collision candidates.
- No blocking render path on exact leaf-PVS reconstruction.
- No hand-authored special cases for individual MM9 maps unless captured as explicit source metadata or migrations.

Target runtime behavior:

- static geometry submit cost scales with visible render sections;
- dynamic object query cost scales with broadphase candidates;
- mechanism update cost scales with moved mechanisms, not all mechanisms;
- script ray/movement checks use shared DAT query APIs;
- save/load persists dynamic object/mechanism state without serializing static geometry.

## Glitch Prevention Checklist

Before treating a DAT map runtime slice as usable:

- visual geometry lines up with source coordinates and expected map bounds;
- helper `PhysicsBSP`/`VisBSP` surfaces are not visible in normal rendering;
- collision floor height agrees with rendered floor on representative maps;
- wall collision normals face the expected way;
- actor/camera cannot fall through helper-only floors;
- ray picking returns stable source ids;
- moving world model render and collision transforms match;
- objects standing on moving mechanisms follow or detach consistently;
- invisible/removed objects leave render, collision, ray-hit, and trigger views;
- material aliases do not bleed across maps;
- translucent/additive surfaces do not break opaque depth;
- world-model names and source indices remain stable across reload;
- save/load restores mechanism transforms, object removal, trigger registrations, and pending movement/callback state.

## Tests And Diagnostics

Add focused coverage as runtime slices land:

- all-world DAT parse remains green;
- representative maps build render partitions without invalid source ids;
- no helper BSP triangles appear in normal visual partitions;
- static raycast hits known floors/walls in at least one outdoor and one indoor map;
- floor query matches expected converted coordinates;
- moving world-model transform changes both render bounds and collision query results;
- broadphase duplicate prevention returns each object once per query;
- object flag changes update render/collision/raycast/trigger views;
- `MoveToFloor` placement uses the collision service once at initialization and does not alter objects whose policy
  disables it;
- source polygon/material ids survive visual and collision queries;
- debug stats expose render blocks, draw calls, triangles, collision queries, and broadphase candidate counts.

Useful debug overlays:

- visual render partition bounds;
- collision BSP/helper geometry;
- dynamic object broadphase cells/nodes;
- source polygon id under cursor;
- mechanism local axes and world AABB;
- raycast path and hit normal;
- portal/leaf decoded source data.

## Local LithTech Reference Index

World loading and source structures:

- `mm9/lithtech/runtime/world/src/world_shared_bsp.h`
  - `CURRENT_WORLD_VERSION 85`;
  - shared world data and header offsets.
- `mm9/lithtech/runtime/world/src/world_shared_bsp.cpp`
  - shared load sequence, world-model load, static lights, light grid, blocker data, render data.
- `mm9/lithtech/runtime/world/src/de_world.h`
  - `WorldBsp`, `WorldData`, `WorldPoly`, `Surface`, `Node`, surface flags, world-info flags.
- `mm9/lithtech/runtime/world/src/de_mainworld.cpp`
  - `WorldBsp::Load`, world-model transformation, bounding sphere calculation.
- `mm9/lithtech/runtime/client/src/world_client_bsp.cpp`
  - client world load and render-data handoff.
- `mm9/lithtech/runtime/server/src/world_server_bsp.cpp`
  - server world load, segment/swept-sphere intersection, world-model init.

Rendering:

- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_device.cpp`
  - renderer world-data load entry.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderworld.*`
  - render-block world, culling, occlusion, sky extents, lightgroups, ray support.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/d3d_renderblock.*`
  - block load, sections, textures, lightmaps, vertices, indices, sky portals, occluders.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/tagnodes.*`
  - visible object sets and dynamic object culling.
- `mm9/lithtech/runtime/render_a/src/sys/d3d/drawworldmodel.cpp`
  - moving world-model render path through instance transforms.

Collision and movement:

- `mm9/lithtech/runtime/shared/src/collision.cpp`
  - BSP collision, stair stepping, player blocker data, collision response.
- `mm9/lithtech/runtime/shared/src/moveobject.cpp`
  - dynamic movement, world-model collision, moving/rotating mechanisms, standing-on handling.
- `mm9/lithtech/runtime/world/src/world_tree.*`
  - dynamic broadphase, object insertion, box queries, duplicate prevention.
- `mm9/lithtech/runtime/world/src/fullintersectline.cpp`
  - segment/ray intersection against world and objects.
- `mm9/lithtech/runtime/world/src/world_blocker_data.cpp`
  - extra player blocker polygon data.
- `mm9/lithtech/NOLF/ObjectDLL/ServerUtilities.cpp`
  - `MoveObjectToFloor` downward support query and placement bias.
- `mm9/lithtech/NOLF/ObjectDLL/Prop.cpp`
  - first-update `MoveToFloor` policy for props.
- `mm9/lithtech/NOLF/ObjectDLL/PickupItem.cpp`
  - `MoveToFloor` property with dynamic pickup default disabled.
- `mm9/lithtech/NOLF/ObjectDLL/Character.cpp`
  - initial-update character floor placement when enabled.

Preprocessor/tool pipeline:

- `mm9/lithtech/tools/PreProcessor/Packer_PC/PCWorldPacker.cpp`
  - v85 file packing, world BSP write, object data, light grid, blocker data, render data.
- `mm9/lithtech/tools/PreProcessor/Packer_PC/PCRenderWorld.cpp`
  - render-world generation and world-model render data.
- `mm9/lithtech/tools/PreProcessor/Packer_PC/PCRenderTree*.cpp`
  - render-block tree, lightmap packing, sky portals, occluders, lightgroups.
- `mm9/lithtech/tools/PreProcessor/create_world_tree.cpp`
  - world tree generation from editor polygons.
- `mm9/lithtech/tools/PreProcessor/createphysicsbsp.cpp`
  - physics BSP generation from brushes.

## Open Questions

These should be resolved with local MM9 data and screenshots, not by assuming v85 behavior:

- How much of MM9 v66 leaf/portal data should drive runtime visibility versus diagnostics/sector hints?
- Which MM9 world models are visual mechanisms, pure helper BSPs, or both?
- Which surface flags besides known invisible/helper bits affect collision, render blending, steps, and material
  behavior?
- Does MM9 require exact LithTech stair-step behavior for comfortable actor/player movement, or can OpenYAMM use its
  shared movement model with MM9 query results?
- How are MM9 lightmaps/render sections represented in v66 compared to the v85 render-block path?
- Which script commands mutate light groups, portals, or world-model state in shipped MM9 scripts?
- What is the exact MM9 class-default matrix for `MoveToFloor` across raw object classes, spawned classes, and script
  spawn strings?

## Done Criteria For The Runtime Architecture

- MM9 DAT maps render from native runtime partitions, not per-polygon immediate submission.
- Static and moving world-model collision queries use the same coordinate/transform model as rendering.
- Helper BSPs and invisible surfaces do not leak into normal visuals.
- Dynamic objects and triggers are broadphase-indexed and handle-routable.
- Scripts, AI, picking, projectiles, and movement consume one DAT query API.
- Mechanisms render and collide through stable instance state.
- Runtime stats show culling/query behavior clearly enough to catch performance regressions.
- The architecture remains scoped to `game/mm9/*` except for narrow shared renderer/gameplay hooks.
