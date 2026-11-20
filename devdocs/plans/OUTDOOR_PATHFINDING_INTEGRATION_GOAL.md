# Outdoor Pathfinding Integration Goal

Goal: enable actor pathfinding in outdoor maps by reusing the existing `game/pathfinding` system and adding ODM-specific
path map construction and runtime hooks.

Do not copy code from `reference/pathfinder` or OpenEnroth. Use local references only for behavior and data-shape
validation.

## Status

Implemented in this branch:

- `OutdoorPathfindingBuilder` materializes ODM terrain and BModel geometry into `PathMap`.
- Outdoor runtime caches full and land-only path maps, invalidates them on geometry/map-delta changes, and routes
  pursuing actors through `ActorPathRuntime` before final `OutdoorMovementController` collision.
- Settings are wired as `[features] outdoor_pathfinding` and `[logging] outdoor_pathfinding`, defaulting to disabled.
- Focused doctests cover terrain, water exclusion, BModel conversion, and planning around outdoor blockers.
- Headless movement coverage verifies a ground actor routes around an outdoor BModel obstacle.

Follow-up coverage still worth adding:

- water-avoidance runtime scenario for non-water-capable actors;
- broader outdoor-map smoke runs before enabling `outdoor_pathfinding` by default.

## References

- Current reusable pathfinding core:
  - `game/pathfinding/PathMap.*`
  - `game/pathfinding/PathPlanner.*`
  - `game/pathfinding/ActorPathRuntime.*`
- Current BLV integration:
  - `game/indoor/IndoorPathfindingBuilder.*`
  - `IndoorWorldRuntime::indoorPathMap()`
  - indoor actor pursuit path resolution in `IndoorWorldRuntime::applyIndoorActorMovementIntegration()`
- Current ODM geometry and movement:
  - `game/outdoor/OutdoorGeometryUtils.*`
  - `game/outdoor/OutdoorMovementController.*`
  - `OutdoorWorldRuntime::rebuildOutdoorFaceGeometryCache()`
  - `OutdoorWorldRuntime::refreshOutdoorModelMechanismGeometry()`
  - `OutdoorWorldRuntime::applyOutdoorActorMovementIntegration()`
- Reference pathfinder outdoor setup:
  - `reference/pathfinder/integration/library.cpp`
  - `reference/pathfinder/integration/MapData.cpp`
  - `reference/pathfinder/src/MapData_AStarWay.cpp`
  - `reference/pathfinder/src/Tracing.cpp`

## Current State

- `PathMap`, `PathPlanner`, and `ActorPathRuntime` are world-agnostic enough to serve both BLV and ODM.
- Indoor pathfinding is wired through an indoor-only builder and an indoor-only cached path map snapshot.
- Outdoor actor movement already has authoritative final collision through `OutdoorMovementController`.
- Outdoor runtime has no `PathMap`, no `ActorPathRuntime`, and no waypoint resolution before applying actor velocity.
- ODM terrain is implicit height-map geometry, while BModels already have explicit cached face geometry in
  `m_outdoorFaces`.

## Reference Model

`reference/pathfinder` handles outdoor maps as a normal facet world:

- clear outdoor map state;
- add outdoor BModel facets;
- add outdoor ground triangles as irregular floor facets;
- optionally add cube blockers;
- build spatial facet areas;
- run the same A* / trace / floor sampling logic used for indoor maps.

OpenYAMM should follow that data-shape, not the reference implementation.

## Target Architecture

### 1. Add OutdoorPathfindingBuilder

Add `game/outdoor/OutdoorPathfindingBuilder.h/.cpp`.

The builder should create a `PathMap` from:

- terrain triangles generated from `OutdoorMapData::heightMap`;
- current outdoor BModel face geometry from `std::vector<OutdoorFaceGeometryData>`;
- map-delta face attributes already reflected into `m_outdoorFaces`;
- optional mode flags for full terrain vs land-only terrain.

Suggested result struct:

```cpp
struct OutdoorPathMapBuildResult
{
    PathMap pathMap;
    size_t terrainTriangleCount = 0;
    size_t bModelFaceCount = 0;
    size_t pathFacetCount = 0;
    size_t skippedFaceCount = 0;
    size_t skippedWaterTerrainCount = 0;
};
```

### 2. Terrain Facets

Generate terrain facets using the same rendered split as `sampleOutdoorRenderedTerrainHeight()`:

- grid cells: `0..126` by `0..126`;
- two triangles per cell;
- world corners from `outdoorGridCornerWorldX/Y`;
- height from `heightMap[index] * OutdoorMapData::TerrainHeightScale`;
- `PathFacetKind::Floor`;
- `walkableFloor = true`;
- `blocking = false`.

For normal ground actors, support a land-only path map that skips water terrain using existing terrain/land-mask rules.
Flyers and water-capable monsters should use the full path map.

Do not use a procedural floor callback first. Materialized terrain triangles match the current `PathMap` design and
match the reference pathfinder model.

### 3. BModel Facets

Convert each `OutdoorFaceGeometryData` to a `PathFacet`.

- `geometry.isWalkable` maps to `PathFacetKind::Floor` and `walkableFloor = true`.
- Non-walkable faces map to `PathFacetKind::Wall` when mostly vertical, otherwise `PathFacetKind::Generic`.
- `FaceAttribute::Untouchable` makes the facet non-blocking.
- Preserve current face attributes from map delta and mechanism updates.
- Use a deterministic source id for BModel faces, for example a packed `bModelIndex/faceIndex` helper. This enables
  preferred source snapping when an actor is standing on a BModel face.

Keep the builder dependent on `OutdoorGeometryUtils` data, not raw ODM binary structures.

### 4. Outdoor Runtime Cache

Add outdoor equivalents of the indoor path map cache:

- `std::shared_ptr<const PathMap> m_outdoorPathMapSnapshot`;
- `std::shared_ptr<const PathMap> m_outdoorLandPathMapSnapshot`;
- validity flags or a small cache struct;
- `ActorPathRuntime m_actorPathRuntime`;
- outdoor path plan counters/timers matching the indoor budget pattern.

Invalidate outdoor path maps when:

- loading/restoring a map;
- rebuilding outdoor face geometry;
- refreshing outdoor model mechanisms;
- changing BModel face attributes through events/map delta.

Do not invalidate path maps for dynamic actor movement; actor collision remains in `OutdoorMovementController`.

### 5. Actor Pursuit Integration

Wire path resolution into `OutdoorWorldRuntime::applyOutdoorActorMovementIntegration()` before assigning
`actor.velocityX/Y/Z`.

Use pathfinding only when:

- actor pathfinding feature flag is enabled;
- movement action is `Pursue`;
- movement is being applied;
- actor is not already in melee range;
- actor movement state is initialized;
- an appropriate path map is available.

If pathfinding returns an active waypoint:

- replace `desiredMoveX/Y` with a normalized direction to the waypoint;
- for flyers, also derive `effectiveDesiredMoveZ` from the waypoint/target height;
- keep final collision and sliding in `OutdoorMovementController::resolveOutdoorActorMove()`;
- keep crowd steering as a local fallback after movement resolution.

If direct path reports reachable, keep current direct pursuit behavior. If planning fails or is cooling down, fall back
to current outdoor movement logic.

### 6. Feature Flags And Logging

Add settings analogous to indoor pathfinding:

- `[features] outdoor_pathfinding=true/false`
- `[logging] outdoor_pathfinding=true/false`

Default can start disabled until the first outdoor tests are stable, then switch to enabled when behavior is acceptable.

Log with an `[OutdoorPathfinding]` prefix and keep logs focused:

- map build summary;
- plan result summary;
- movement fallback/debug summary only when logging is enabled.

Do not add noisy per-frame logs in normal builds.

## Water And Terrain Rules

Outdoor pathfinding must respect actor water capability.

Initial implementation should use two cached maps:

- full outdoor path map: terrain, water terrain, BModels;
- land-only outdoor path map: terrain excluding water/land-mask water, plus BModels.

Selection:

- flyers use full map;
- monsters that can walk on water use full map;
- ordinary ground actors use land-only map.

Keep `applyOutdoorWaterRestriction()` for safety while integration is proven. It should become a fallback guard, not the
primary navigation mechanism.

## Source Id Strategy

`PathMap::snapToWalkableSourceFacet()` uses `PathFacet::sourceId`. Outdoor should define helpers instead of ad hoc ids:

- terrain source ids may be negative or omitted because terrain support does not currently expose a triangle id;
- BModel source ids should be positive and stable for the active map;
- the runtime should pass a preferred source id only when `actor.movementState.supportKind == BModelFace`.

If BModel/face indices can exceed a safe packed range, add a small mapping table in the build result instead of relying
on bit packing.

## Implementation Plan

1. Add `OutdoorPathfindingBuilder` with terrain-only map construction.
2. Add unit tests for terrain triangle generation, floor queries, and direct walking over normal terrain.
3. Add land-only terrain mode and tests for water exclusion.
4. Add BModel face conversion and tests for walkable platforms, walls, and untouchable faces.
5. Add outdoor path map cache and invalidation in `OutdoorWorldRuntime`.
6. Add feature flags and logging settings.
7. Wire `ActorPathRuntime` into outdoor pursuit with current movement fallback intact.
8. Add unit coverage for waypoint direction selection around a BModel wall or water gap.
9. Add a focused headless outdoor scenario where a pursuing ground actor routes around an obstacle.
10. Tune step length, step height, planning range, worker count, and per-step plan budget.

## Suggested Tuning Defaults

Start conservative and adjust with diagnostics:

- terrain path spatial grid: `512.0f` or `1024.0f`;
- ground actor path step length: `64.0f` or `96.0f`;
- outdoor ground step height: `128.0f`;
- ground planning range: `12000.0f`;
- flying planning range: `6000.0f`;
- node limit: `8000` initially, raise only if diagnostics prove it is needed;
- worker count: match indoor initially.

## Tests

Add focused doctests before broad runtime work:

- terrain-only builder creates expected facet count for a small synthetic height map;
- floor query returns rendered triangle height for both terrain triangle orientations;
- land-only mode excludes water terrain;
- BModel floor becomes walkable;
- BModel wall blocks `PathMap::canReachDirectly()`;
- untouchable BModel face is non-blocking;
- planner routes around a blocker on an outdoor-style terrain map.

Add runtime/headless coverage after the builder is stable:

- ground actor pursues around an outdoor BModel obstacle;
- ground actor avoids water when not water-capable;
- flyer can still route over terrain/water;
- mechanism movement invalidates and rebuilds the outdoor path map.

## Non-Goals

- Do not replace `OutdoorMovementController`; it remains authoritative for final collision, sliding, ground settling,
  and dynamic actor contacts.
- Do not add ODM-specific logic to `PathPlanner` unless a test proves the generic planner cannot express the behavior.
- Do not include live actor positions in the static path map.
- Do not copy or vendor `reference/pathfinder`.
- Do not change generated Lua events for this work.

## Open Questions

- Should outdoor pathfinding default on immediately, or stay behind a feature flag until headless coverage is stable?
- Should water-capable monster detection live near `applyOutdoorWaterRestriction()` helpers or in a shared actor
  movement capability helper?
- Do we need a public helper for outdoor terrain triangle ids, or is nearest-floor snapping sufficient for terrain
  starts?
- Are decoration and sprite-object blockers important enough for the first milestone, or should collision fallback
  handle them until actor pursuit around terrain/BModels is stable?
