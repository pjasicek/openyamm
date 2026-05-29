# Outdoor Pathfinding MMerge Parity Plan

This document describes how MMerge uses the external `pathfinder` library outdoors, what that library actually
computes, and how to implement the same behavior in OpenYAMM without copying MMerge, OpenEnroth, or the pathfinder
integration code.

The intended implementation should reuse OpenYAMM's existing `PathMap`, `PathPlanner`, and `ActorPathRuntime`
infrastructure. The new work is an outdoor path-map builder plus outdoor runtime integration.

## Goals

- Add outdoor pathfinding for grounded monsters, matching MMerge's outdoor policy.
- Keep flying outdoor monsters out of pathfinding initially, because MMerge excludes them outdoors.
- Keep the path search asynchronous by using the existing `ActorPathRuntime` worker queue.
- Use the same world collision surfaces that outdoor movement and LOS already use.
- Preserve current outdoor AI when pathfinding is disabled.
- Avoid partial-route behavior outdoors for the first parity implementation.

## Non-Goals

- Do not integrate the external DLL directly.
- Do not add actor collision blockers into A*. MMerge does not pathfind around other actors.
- Do not solve local crowding in the path map. Crowd steering and movement collision remain runtime movement concerns.
- Do not implement outdoor flying pathfinding in the first pass.
- Do not create a new pathfinding abstraction parallel to `PathMap` and `ActorPathRuntime`.

## Reference Behavior

The relevant MMerge files are:

- `reference/mmmerge/Scripts/Modules/PathfinderDll.lua`
- `reference/mmmerge/Scripts/Global/MonsterPathfinding.lua`
- `reference/pathfinder/src/MapData_AStarWay.cpp`
- `reference/pathfinder/src/MapData.cpp`
- `reference/pathfinder/src/Tracing.cpp`
- `reference/pathfinder/integration/MapData.cpp`
- `reference/pathfinder/integration/library.cpp`

Use these files as behavioral references only. The implementation should be native OpenYAMM code.

## MMerge Outdoor Map Build

MMerge builds one pathfinder map per loaded map. Outdoors, `PathfinderDll.init_map()` calls `init_outdoor()`.

The outdoor build does this:

1. Initializes an outdoor map instance.
2. Adds all outdoor BModel faces.
3. Adds generated terrain ground triangles.
4. Adds blocking decoration cubes.
5. Adds water-edge blockers.
6. Builds the pathfinder spatial area grid.

The external library spatial grid uses a default cell size of `400`.

### BModels

MMerge passes `Map.Models` directly into the DLL. The DLL reads each BModel face, its vertices, polygon type, and
face attributes. It does not pre-filter faces aggressively. Walkability and blocking behavior are decided later from
polygon type and attributes.

Pathfinder facet rules:

- Polygon types `3` and `4` are floors.
- Polygon types `5` and `6` are ceilings.
- Other polygon types are generic blocking faces.
- A face is non-blocking if it is a portal, or if it is both invisible and untouchable.
- Untouchable faces should not block body tracing.

OpenYAMM mapping:

- Use `OutdoorMapData::bmodels` and `buildOutdoorFaceGeometry`.
- Convert `OutdoorFaceGeometryData` into `PathFacet`.
- Use `isOutdoorWalkablePolygonType` for `walkableFloor`.
- Use `FaceAttribute::Portal`, `FaceAttribute::Invisible`, and `FaceAttribute::Untouchable`.
- Set `PathFacet::blocking` consistently with outdoor movement/LOS semantics:
  - portals do not block;
  - untouchable faces do not block;
  - ordinary BModel walls block;
  - walkable BModel floors are walkable floors and also participate in body tracing where appropriate.

### Terrain Ground

MMerge generates terrain vertices for the full 128x128 height map. The raw MM DLL integration writes X as
`(64 - x) * 512`, but OpenYAMM has already normalized outdoor coordinates differently:

- `outdoorGridCornerWorldX(gridX) == (gridX - 64) * 512`
- `outdoorGridCornerWorldY(gridY) == (64 - gridY) * 512`

The OpenYAMM builder must use the existing helpers from `OutdoorGeometryUtils.h`, not MMerge's raw-memory transform.

MMerge adds two terrain triangles per non-water tile:

- top-left, top-right, bottom-right
- top-left, bottom-left, bottom-right

OpenYAMM rendered terrain uses the same diagonal orientation in `OutdoorRenderer::buildTexturedTerrainVertices`:

- top-left, bottom-left, top-right
- top-right, bottom-left, bottom-right

Those are equivalent triangle halves for the same square. The builder should match OpenYAMM's rendered terrain
ordering so path floor height matches the visual and movement terrain.

Terrain path facets:

- `PathFacetKind::Floor`
- `walkableFloor = true`
- `blocking = true`
- no portal/invisible/untouchable attributes
- source id may encode the tile or terrain triangle index

### Water

MMerge does not add ground triangles for water tiles. It also adds small vertical blockers around exposed water edges,
using cube side faces with radius `48`.

OpenYAMM should classify water using the same runtime water logic used for monsters:

- `isOutdoorTerrainWater(outdoorMapData, x, y)`
- the land-mask lookup currently implemented inside `OutdoorWorldRuntime.cpp`
- the same combined semantics as the runtime's `isOutdoorMonsterWaterTile(...)` helper

For initial parity, all grounded pathfinding monsters should treat water as not walkable, except monsters that can
walk/swim on water if we explicitly add that as a second phase. MMerge's generic path build has no per-monster water
ground generation; it simply omits water terrain from the map.

Implementation options:

- Prefer generating no terrain floor facets for water tiles.
- Add water-edge side blockers matching MMerge's exposed-edge rule.
- Keep water handling independent of movement's runtime pushback so A* does not choose water crossings that movement
  later rejects.

### Blocking Decorations

MMerge adds four vertical side faces around qualifying outdoor sprites:

- decoration is not `NoBlockMovement`;
- decoration is not `NoDraw`;
- radius is greater than `30`;
- height is greater than `30`;
- cube radius is the decoration radius;
- cube center is `(sprite.x, sprite.y, sprite.z + radius)`.

OpenYAMM should use the already-built outdoor decoration collision data instead of re-reading raw sprite memory.

Builder input should include either:

- `OutdoorDecorationCollisionSet`, or
- a compact vector of `OutdoorDecorationCollision`.

Each qualifying decoration should add four wall facets around the square:

- `(x - r, y - r) -> (x + r, y - r)`
- `(x + r, y - r) -> (x + r, y + r)`
- `(x + r, y + r) -> (x - r, y + r)`
- `(x - r, y + r) -> (x - r, y - r)`

Each wall facet should extend vertically from `z - radius` to `z + radius` if using the MMerge cube-center convention.
If using OpenYAMM's decoration collision `worldZ` as the authored base, preserve the collision controller's convention
and verify with a unit test against a known blocking decoration.

## Pathfinder Library Algorithm

The external pathfinder library is not using a navmesh. It searches a regular step grid over collision geometry.

### Floor Queries

For grounded objects:

- The start point is snapped to a floor.
- Candidate points are raised by `stepHeight` for floor lookup.
- A candidate is rejected if no floor is found.
- A candidate is rejected if it is in void.
- A candidate is rejected if the floor Z delta exceeds `stepHeight`.

`getFloorLevel` considers floor and ceiling facets, skips non-blocking facets, and uses a vertical ray down at the
candidate XY. The closest acceptable floor becomes the grounded position.

OpenYAMM's `PathMap::floorAt` and `PathPlanner` already follow the same structure.

### Segment Tracing

For grounded movement, the library checks a segment by:

1. Sampling floor support along the segment.
2. Rejecting excessive step height.
3. Tracing body side lines against blocking facets.

For a body radius greater than one, it traces the center line and side lines offset by the radius. Grounded traces are
lifted by `stepHeight`.

OpenYAMM's `PathMap::traceWalkSegment` and `PathMap::traceLine` already provide this role.

### A* Search

The library:

- uses 8 horizontal directions for grounded objects;
- uses 26 directions for flying objects;
- uses `stepLength` as the XY grid step, clamped to at least `24`;
- stops when a node is within `stepLength * 4` of the target and has a direct trace to the target;
- has a node limit supplied by MMerge as `8000`.

MMerge object parameters outdoors:

- `canFly = Monster.Fly`
- `radius = Monster.BodyRadius`
- `stepLength = Monster.BodyRadius * 2`
- `stepHeight = 40`
- `nodeLimit = 8000`

However, MMerge never submits outdoor flying monsters because its outdoor eligibility rejects `Mon.Fly != 0`.

OpenYAMM should use:

- `PathObject::canFly = false`
- `PathObject::radius = actorCollisionRadius`
- `PathObject::stepLength = actorCollisionRadius * 2.0f`
- `PathObject::stepHeight = 40.0f`
- `ActorPathResolveRequest::nodeLimit = 8000`
- `ActorPathResolveRequest::planningRange = 12000.0f`

The current `ActorPathRuntime` queues `PathPlanRequest` with `allowPartialPath = false` by default. Keep that for
outdoor parity.

## MMerge Runtime Policy

MMerge only pathfinds selected monsters. Its outdoor eligibility is stricter than indoor eligibility.

Outdoor `MonsterNeedsProcessing` requires:

- improved pathfinding enabled;
- monster active and alive;
- AI state is pursue, or hostile idle;
- monster is not flying;
- monster is within `12000` units of the party.

MMerge also skips all pathfinding for the tick if the party is outdoors and flying more than `200` units above floor.

OpenYAMM should implement the same policy before it asks `ActorPathRuntime` for a waypoint:

- `settings.outdoorPathfinding` is true;
- path map exists and has the current revision;
- actor is active, alive, hostile/pursuing through the normal AI result;
- `pStats->canFly == false`;
- actor movement is allowed;
- movement intent action is `Pursue`;
- `movementIntent.meleePursuitActive == true`;
- `movementIntent.applyMovement == true`;
- `movementIntent.inMeleeRange == false`;
- actor is within `12000` units of the party;
- party is not more than `200` units above the path/support floor.

For target actors, MMerge still gates processing using distance to the party. OpenYAMM can keep that for parity. The
path target itself should remain `movementIntent.targetPosition`, because the shared AI already resolved the current
combat target.

## MMerge Runtime State

MMerge keeps per-monster path state:

- generated waypoint list;
- current waypoint step;
- target snapshot;
- generation time;
- in-process flag;
- need-rebuild flag;
- fail count;
- stale target threshold of about `1024` units.

MMerge consumes the path in its `MonstersProcessed` hook, not inside the pathfinder:

- if the monster still needs pathfinding and the target is not considered directly reachable, it reads the current
  waypoint from the stored path;
- it sets the monster direction toward that waypoint;
- if the monster is within `Monster.BodyRadius` in XY distance, it advances to the next waypoint;
- if it reaches the end, it clears the path and marks the monster for a later rebuild.

The pathfinder returns a full waypoint list. It does not move the monster, resolve actor collision, or perform local
crowd avoidance.

OpenYAMM already has equivalent state in `ActorPathRuntime`:

- active waypoints;
- waypoint index;
- source and target snapshots;
- pending async job id;
- failed cooldown;
- direct-check cache;
- target moved threshold of `1024`;
- stale source and stale target discard checks;
- worker thread queue.

Therefore the outdoor implementation should not add another state machine. Add a second `ActorPathRuntime` member to
`OutdoorWorldRuntime`, or name it explicitly as outdoor actor path runtime.

## MMerge Scheduling

MMerge uses two layers of scheduling:

- the Lua side rotates through monsters and submits only a small amount of work per tick;
- the DLL side runs queued path tasks on up to two worker threads, with a maximum task queue size of `50`.

Its Lua coroutine loop also has a small wall-clock budget, roughly `3` milliseconds. Failed plans increase fail count
and delay retries. Queue priority is based mostly on distance to target, with penalties for flyers and repeated fails.
Outdoors, flyers are already excluded before queue submission.

OpenYAMM does not need to copy this scheduler. `ActorPathRuntime` already supplies background workers and per-actor
pending/completed state. The outdoor runtime only needs a small per-step plan budget and a minimum plan interval so it
does not enqueue every actor every fixed tick.

## OpenYAMM Code Changes

### 1. Add Outdoor Path Map Builder

Add:

- `game/outdoor/OutdoorPathfindingBuilder.h`
- `game/outdoor/OutdoorPathfindingBuilder.cpp`
- tests in `tests/OutdoorPathfindingBuilderTests.cpp`
- CMake entries in `game/CMakeLists.txt` and `tests/CMakeLists.txt`

Suggested API:

```cpp
struct OutdoorPathMapBuildResult
{
    size_t terrainTileCount = 0;
    size_t terrainFacetCount = 0;
    size_t bModelFaceCount = 0;
    size_t bModelFacetCount = 0;
    size_t decorationBlockerCount = 0;
    size_t waterBlockerCount = 0;
    size_t skippedFaceCount = 0;
    PathMap pathMap;
};

class OutdoorPathfindingBuilder
{
public:
    static OutdoorPathMapBuildResult buildPathMap(
        const OutdoorMapData &outdoorMapData,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask,
        const OutdoorDecorationCollisionSet &decorationCollisionSet,
        float spatialGridCellSize = 400.0f);
};
```

If `OutdoorDecorationCollisionSet` is awkward to include, pass a vector of already-flattened decoration collisions.
Keep the builder free of `OutdoorWorldRuntime` ownership.

Builder responsibilities:

- convert BModel faces to `PathFacet`;
- generate terrain floor triangles for non-water tiles;
- add decoration wall blockers;
- add exposed water-edge wall blockers;
- call `PathMap::setFacets`;
- call `PathMap::buildSpatialGrid(400.0f)`.

The builder should use these existing helpers:

- `outdoorGridCornerWorldX`
- `outdoorGridCornerWorldY`
- `buildOutdoorFaceGeometry`
- `isOutdoorWalkablePolygonType`
- `isOutdoorTerrainWater`

The builder should not call movement integration code.

### 2. Add Settings

Extend `GameSettings`:

- `bool outdoorPathfinding = false` or `true`, depending on desired rollout safety;
- `bool logOutdoorPathfinding = false`.

Add settings.ini serialization:

- `[gameplay] outdoor_pathfinding=true`
- `[logging] outdoor_pathfinding=false`

The existing indoor implementation already has:

- `[gameplay] indoor_pathfinding`
- `[logging] indoor_pathfinding`

Keep naming parallel.

When disabled, the outdoor runtime must:

- set the outdoor `ActorPathRuntime` worker count to `0`;
- not build or use path requests during actor movement;
- keep the old movement intent and collision path unchanged.

### 3. Add OutdoorWorldRuntime Members

Add includes:

- `game/pathfinding/ActorPathRuntime.h`
- `game/pathfinding/PathMap.h`
- `game/outdoor/OutdoorPathfindingBuilder.h`

Add members:

```cpp
PathMap m_outdoorPathMap;
bool m_outdoorPathMapValid = false;
size_t m_outdoorPathMapRevision = 0;
ActorPathRuntime m_outdoorActorPathRuntime;
double m_outdoorActorPathRuntimeSeconds = 0.0;
double m_nextOutdoorActorPathPlanSeconds = 0.0;
size_t m_outdoorActorPathPlansThisStep = 0;
```

The `PathMap` owns its own revision, so `m_outdoorPathMapRevision` is optional if callers use
`m_outdoorPathMap.revision()`.

Suggested constants near the existing outdoor actor constants:

```cpp
constexpr bool OutdoorActorPathfindingEnabled = true;
constexpr size_t OutdoorActorPathNodeLimit = 8000;
constexpr size_t OutdoorActorPathPlanBudgetPerStep = 2;
constexpr size_t OutdoorActorPathWorkerCount = 2;
constexpr double OutdoorActorPathPlanIntervalSeconds = 0.1;
constexpr float OutdoorGroundPathPlanningRange = 12000.0f;
constexpr float OutdoorPartyFlyingPathDisableHeight = 200.0f;
constexpr double OutdoorPathFailedRetrySeconds = 3.0;
constexpr double OutdoorPathDirectCheckIntervalSeconds = 0.25;
constexpr double OutdoorPathMinReplanIntervalSeconds = 1.0;
constexpr double OutdoorPathShortcutCheckIntervalSeconds = 0.5;
constexpr float OutdoorPathSpatialGridCellSize = 400.0f;
```

MMerge delays failed retries for much longer, roughly four in-game minutes. OpenYAMM can start with the existing indoor
`3.0` second cooldown for responsiveness, but if the goal is strict MMerge parity then use a longer outdoor-specific
cooldown. Keep it as a constant so it can be tuned without touching logic.

### 4. Build And Reset On Map Load

In `OutdoorWorldRuntime::initialize` or the current load path after:

- `rebuildOutdoorFaceGeometryCache();`
- `m_outdoorMovementController.emplace(...)`
- `syncOutdoorFaceGeometryAttributesFromMapDelta();`

build the outdoor path map:

```cpp
m_outdoorActorPathRuntime.clear();
m_outdoorActorPathRuntime.setWorkerCount(0);
m_outdoorActorPathRuntimeSeconds = 0.0;
m_nextOutdoorActorPathPlanSeconds = 0.0;
m_outdoorActorPathPlansThisStep = 0;
m_outdoorPathMapValid = false;

if (outdoorPathfindingEnabled() && outdoorMapData)
{
    OutdoorPathMapBuildResult buildResult =
        OutdoorPathfindingBuilder::buildPathMap(
            *outdoorMapData,
            outdoorLandMask,
            outdoorDecorationCollisionSet,
            OutdoorPathSpatialGridCellSize);
    m_outdoorPathMap = std::move(buildResult.pathMap);
    m_outdoorPathMapValid = true;
}
```

If pathfinding is disabled at load time, skipping the build gives the intended zero runtime cost beyond the settings
branch.

If settings can change during a loaded outdoor map, `setSettingsSnapshot` or the runtime settings binding should:

- clear and stop workers when disabled;
- lazily rebuild on the next outdoor map load, or explicitly rebuild if enabling during an active map is required.

### 5. Rebuild On Outdoor Geometry Changes

Outdoor BModel geometry and attributes can change via mechanisms. Current hooks include:

- `rebuildOutdoorFaceGeometryCache`
- `syncOutdoorFaceGeometryAttributesFromMapDelta`
- `setOutdoorFaceGeometryAttributes`
- movement controller `updateFaceGeometries`
- party runtime `updateFaceGeometries`

The simplest structurally correct implementation is:

- mark the outdoor path map dirty when outdoor face geometry or face attributes change;
- rebuild at a safe point before the next actor path request;
- increment the path map revision by rebuilding `PathMap`.

Do not leave stale path geometry after moving/hidden faces change, because `ActorPathRuntime` already discards plans
when the map revision changes.

### 6. Advance Outdoor Path Runtime Time

In the actor fixed-step loop, mirror the indoor runtime:

- increment `m_outdoorActorPathRuntimeSeconds` by `ActorUpdateStepSeconds`;
- reset `m_outdoorActorPathPlansThisStep` at the start of each fixed actor step;
- use `m_nextOutdoorActorPathPlanSeconds` to throttle plan submissions.

This should happen in `updateMapActors` around the same place that active actor facts are collected and movement is
applied.

### 7. Integrate With Outdoor Movement

The best hook is `OutdoorWorldRuntime::applyOutdoorActorMovementIntegration`, before velocity is written from
`desiredMoveX/Y`.

Create a local `ActorMovementIntent`-like path gate from the existing parameters:

- `meleePursuitActive`
- `inMeleeRange`
- `targetPosition`
- `targetEdgeDistance`
- `desiredMoveX/Y`
- `pStats`
- active actor mask

Outdoor path can be used when:

```cpp
const bool outdoorPathCanUseIntent =
    outdoorPathfindingEnabled()
    && m_outdoorPathMapValid
    && !pStats->canFly
    && meleePursuitActive
    && !inMeleeRange
    && movementAllowedForThisActor
    && !partyTooHighAboveOutdoorFloor();
```

`movementAllowedForThisActor` is already known in AI facts but not directly passed into the integration function.
Either pass it through from `ActorMovementIntent`, or recompute it from `pStats->movementType` and `actor.immobile`.

Then:

```cpp
PathObject pathObject = {};
pathObject.canFly = false;
pathObject.radius = actorCollisionRadius(actor, pStats);
pathObject.stepLength = std::max(pathObject.radius * 2.0f, 24.0f);
pathObject.stepHeight = 40.0f;

ActorPathResolveRequest pathRequest = {};
pathRequest.actorIndex = actorIndex;
pathRequest.source = {actor.preciseX, actor.preciseY, actor.preciseZ};
pathRequest.target = {targetPosition.x, targetPosition.y, targetPosition.z};
pathRequest.object = pathObject;
pathRequest.nodeLimit = OutdoorActorPathNodeLimit;
pathRequest.mapRevision = m_outdoorPathMap.revision();
pathRequest.planningRange = OutdoorGroundPathPlanningRange;
pathRequest.waypointReachDistance = pathObject.radius;
pathRequest.nowSeconds = m_outdoorActorPathRuntimeSeconds;
pathRequest.failedRetrySeconds = OutdoorPathFailedRetrySeconds;
pathRequest.directCheckIntervalSeconds = OutdoorPathDirectCheckIntervalSeconds;
pathRequest.minReplanIntervalSeconds = OutdoorPathMinReplanIntervalSeconds;
pathRequest.shortcutCheckIntervalSeconds = OutdoorPathShortcutCheckIntervalSeconds;
pathRequest.allowPlan =
    m_outdoorActorPathPlansThisStep < OutdoorActorPathPlanBudgetPerStep
    && m_outdoorActorPathRuntimeSeconds >= m_nextOutdoorActorPathPlanSeconds;

ActorPathResolveResult pathResult =
    m_outdoorActorPathRuntime.resolveWaypoint(m_outdoorPathMap, pathRequest);
```

If `pathResult.pathActive`:

- replace `desiredMoveX/Y` with the normalized vector from actor position to `pathResult.waypoint`;
- set actor move direction to the same vector;
- update yaw using the same facing-dead-zone logic used to fix indoor billboard flipping;
- keep normal movement collision resolution.

If `pathResult.queued` or an existing plan is pending:

- hold movement at zero for the actor, matching MMerge's short `HoldMonster` period.

If `pathResult.failed`, `cooldown`, or `discarded`:

- prefer falling back to normal direct movement outdoors, not zero movement, unless testing shows direct movement causes
  the old "run into wall forever" behavior too often.

This is intentionally different from the current indoor failure hold, because MMerge failure does not install a
waypoint and the base engine can still continue its normal behavior.

### 8. Direct Reachability And LOS

MMerge stops path steering when `MonsterTargetInSight` is true. For melee monsters, that check includes both LOS and a
path trace. For ranged monsters, LOS is enough.

OpenYAMM already has shared AI decisions for attack LOS and melee range. Outdoor pathfinding should not override
attack decisions. It should only replace pursuit movement when the AI has already chosen pursuit.

`ActorPathRuntime::resolveWaypoint` also performs direct reachability checks through `PathMap`. If the actor can walk
directly to the target, it returns no active path and the normal AI movement remains in control.

This gives the desired behavior:

- clear direct approach: normal outdoor pursuit;
- blocked approach: path waypoint pursuit;
- in melee range: no path override;
- attacking/casting/recovering: no path override.

### 9. Actor Collisions And Crowding

Do not add actors to `PathMap`.

MMerge's A* does not solve actor crowding. It routes through static geometry only. Actor collisions are handled by the
game's movement collision and by AI/crowd steering.

For OpenYAMM:

- keep `OutdoorMovementController::resolveOutdoorActorMove` responsible for actor-vs-actor collision;
- keep `GameplayActorAiSystem` crowd steering responsible for local sidestep/stand/retreat behavior;
- do not let actor collision contacts invalidate path plans;
- if actors are pathing from far away, it is reasonable to ignore actor-vs-actor collision until near the party, but
  that belongs in outdoor movement collision policy, not A*.

Indoor already has an "ignore actor collision when not in party sector" rule. Outdoor can add a simpler distance-based
variant later if crowding remains bad:

- while pathfinding is active;
- while target edge distance is above a threshold, for example `768`;
- ignore map actor colliders except self;
- restore actor collisions near the target.

That should be a separate, logged movement-collision change.

### 10. Logging

Add logging parallel to indoor:

```text
[OutdoorPathfinding] map_build map="..." terrain_tiles=... terrain_facets=...
    bmodel_faces=... bmodel_facets=... decoration_blockers=... water_blockers=...
    skipped_faces=... revision=...

[OutdoorPathfinding] plan actor=... actor_id=... status=... discarded=...
    discard_reason=... nodes=... waypoints=... waypoint_index=...
    source=(...) target=(...) revision=... active=...
    plan_source=(...) snapped_source=(...) snapped_target=(...)
    source_valid=... target_valid=... direct=...
    source_facet=... target_facet=... best=(...) best_facet=...
    candidates=... accepted=... reject_no_floor=... reject_step=...
    reject_walk=... reject_dup=...
```

Use `settings.logOutdoorPathfinding`. Keep this off by default.

Do not add per-frame movement spam as permanent logging. If movement diagnostics are needed while implementing, guard
them behind a separate temporary compile-time block or remove them before commit.

## Tests

Add focused unit tests before broad runtime testing.

### Builder Tests

`OutdoorPathfindingBuilderTests.cpp` should cover:

- a flat non-water terrain tile produces two walkable floor facets;
- water terrain tiles produce no walkable floor facets;
- exposed water edges produce wall blockers;
- BModel walkable faces become `PathFacetKind::Floor`;
- BModel wall faces become blocking non-walkable facets;
- untouchable BModel faces do not block;
- blocking decorations add four wall facets;
- too-small decorations do not add blockers.

### Planner Tests

Use the built outdoor path map with `PathPlanner`:

- plan across flat terrain succeeds;
- plan across water fails or routes around if land exists;
- plan around a decoration blocker succeeds;
- plan from terrain onto a BModel ramp/floor succeeds if step height allows it;
- plan over a too-large height jump fails.

### Runtime Tests

Add headless or runtime tests where possible:

- outdoor grounded monster pursues around a static obstacle;
- outdoor flying monster does not request pathfinding;
- pathfinding disabled leaves no active worker threads and no path requests;
- party more than `200` units above outdoor floor disables outdoor path requests;
- moving/hidden outdoor face invalidates path map and causes stale plans to be discarded.

## Performance Expectations

Worst-case terrain facets are roughly:

- `(128 - 1) * (128 - 1) * 2 = 32258` triangles before water filtering.

This is much larger than typical indoor path maps, so the spatial grid size matters. Start with `400.0f` to match the
pathfinder library. If profiling shows expensive floor queries, optimize the outdoor map representation in a second
step:

- keep terrain in a terrain-specific floor sampler inside `PathMap`, or
- add a compact terrain floor source that avoids inserting every terrain triangle as a general polygon.

Do not start with that optimization unless profiling requires it. The first implementation should prioritize parity
and correctness.

Runtime planning should use:

- two worker threads;
- per-step plan budget of two;
- minimum plan interval of `0.1` seconds;
- node limit `8000`;
- no partial paths.

This matches the current indoor async structure and is close to MMerge's `max_threads = 2`, `max_tasks = 50`, and
`limit = 8000`.

## Implementation Order

1. Add settings fields and serialization for outdoor pathfinding and logging.
2. Add `OutdoorPathfindingBuilder` and builder tests.
3. Build the outdoor path map on outdoor map load when enabled.
4. Add outdoor path runtime members and stop workers when disabled.
5. Hook `ActorPathRuntime` into `applyOutdoorActorMovementIntegration`.
6. Add map-build and plan logging behind `logOutdoorPathfinding`.
7. Add dirty/rebuild hooks for outdoor geometry changes.
8. Run unit tests and targeted outdoor manual tests.
9. Profile before adding any terrain-specific optimization.

## Manual Test Scenarios

Use these cases after the unit tests pass:

- MM6 New Sorpigal goblins around houses or fences.
- MM6 Abandoned Temple exterior approach if available.
- MM7 or MM8 outdoor maps with BModel ramps and bridges.
- Water-adjacent ground monsters to verify they do not path through water.
- Party flying above terrain to verify outdoor pathfinding pauses.
- A mixed pack with flying and grounded monsters to verify only grounded actors path.

Expected behavior:

- grounded monsters path around static outdoor geometry;
- grounded monsters do not enter water because of pathing;
- flying monsters behave exactly as before;
- when disabled in settings, outdoor actor movement matches the current code path;
- logs appear only when explicitly enabled.
