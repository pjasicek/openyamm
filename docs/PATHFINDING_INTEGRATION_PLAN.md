# Native Actor Pathfinding Integration Plan

This plan covers a native OpenYAMM integration inspired by `reference/pathfinder` and the MMerge
`PathfinderDll.lua` / `MonsterPathfinding.lua` usage. The reference code is a behavioral model only. Do not copy it
into OpenYAMM.

## Goal

Add `game/pathfinding/*` as a native medium-range actor route planner for static BLV/ODM geometry. The planner should
feed waypoints into the existing shared actor AI and world movement controllers. It should replace the current
static-obstacle role of the crowding heuristic, while keeping local actor-contact steering for dynamic bodies.

The final ownership split should be:

- `game/pathfinding/*`: shared path geometry, trace/floor queries, A* planning, path state, and bounded job scheduling.
- `game/indoor/*`: BLV path map construction from indoor runtime geometry, sectors, doors, portals, and face masks.
- `game/outdoor/*`: ODM path map construction from terrain, water mask, bmodels, blocking decorations/sprites.
- `GameplayActorAiSystem`: combat/idle/flee decisions and pursuit intent. It should not own map geometry.
- `IndoorMovementController` / `OutdoorMovementController`: authoritative per-frame collision, floor, slope, water,
  gravity, sliding, and actor contact resolution.

## Current OpenYAMM Shape

Shared actor AI currently computes direct pursuit:

- `GameplayActorAiSystem::AI_Pursue` builds a direction toward `actor.target.currentPosition`.
- `resolvePursueAction` chooses direct, short offset, wide offset, or ranged orbit movement.
- `ActorMovementIntent` carries `desiredMoveX/Y/Z`, `targetPosition`, `targetEdgeDistance`, `meleePursuitActive`, and
  `applyMovement`.

Indoor integration:

- `IndoorWorldRuntime::collectIndoorActorAiFacts` provides target facts, LOS, movement speed, radius/height, sector, and
  runtime crowd state.
- `IndoorWorldRuntime::applyIndoorActorMovementIntegration` converts `ActorMovementIntent` to velocities and calls
  `IndoorMovementController::resolveMove`.
- Post-move it builds coarse movement facts and calls
  `GameplayActorAiSystem::updateActorAfterWorldMovement`.
- Indoor currently sets `crowdSteeringTriggersOnMovementBlocked = true`, so static wall blocking can trigger the same
  sidestep/retreat/stand behavior used for actor crowding.

Outdoor integration:

- `OutdoorWorldRuntime::collectOutdoorActorAiFacts` builds target facts from outdoor LOS and engagement logic.
- `OutdoorWorldRuntime::applyOutdoorActorMovementIntegration` applies water restriction, slope response, then calls
  `OutdoorMovementController::resolveOutdoorActorMove`.
- Outdoor post-move crowd steering is mainly actor-contact based; `crowdSteeringTriggersOnMovementBlocked = false`.

The important existing seam is the world runtime, after shared AI has selected pursuit but before movement integration.
That is where pathfinding should replace the direct `desiredMoveX/Y` with a direction toward the current waypoint.

## Reference Findings

`reference/pathfinder` provides these useful behaviors:

- It models maps as blocking/non-blocking facets plus a coarse 3D spatial grid.
- A facet is non-blocking when it is portal, or invisible plus untouchable.
- `trace_line` checks segment/facet intersections.
- `get_floor_level` finds nearest floor below or, if needed, nearest floor above and marks void.
- `trace_way` validates a walking segment by sampling floor along the segment, rejecting void and height deltas above
  `step_height`, then tracing side body lines at object radius.
- `AStarWay` uses 8-neighbor ground movement and 26-neighbor flying movement.
- Step size is `max(step_length, 24)`.
- Walking nodes snap to floor; flying nodes stay volumetric but still reject void.
- The target is accepted when close enough and there is a clear line from the current node to the target.
- The DLL wrapper also offers async jobs, but the core algorithm is synchronous.

MMerge usage adds these runtime policies:

- Map path data is rebuilt on map load and stopped on leave/save/load boundaries.
- Indoor path data is built directly from `Map.Facets` and `Map.Vertexes`.
- Outdoor path data includes bmodels, terrain triangles excluding water tiles, cubes at water boundaries, and cubes for
  blocking sprites/decorations.
- Monster path requests use `step_height = 40`.
- Step length is monster body radius indoors and twice body radius outdoors.
- Processing is limited to active, hostile/pursuing, alive monsters within distance thresholds.
- Direct sight/reach keeps normal movement; pathfinding is used when target is not directly reachable.
- Failed path builds are delayed before retry.
- Existing paths rebuild when the target moves more than about `1024` map units, the monster gets stuck, or the path is
  exhausted.
- Waypoints are applied by turning the monster toward the next point; the DLL does not replace engine movement physics.

## Native Design

### Core Types

Create these files:

- `game/pathfinding/PathfindingTypes.h`
- `game/pathfinding/PathMap.h`
- `game/pathfinding/PathMap.cpp`
- `game/pathfinding/PathPlanner.h`
- `game/pathfinding/PathPlanner.cpp`
- `game/pathfinding/ActorPathRuntime.h`
- `game/pathfinding/ActorPathRuntime.cpp`

Core model:

- `PathPoint`: float `x/y/z`.
- `PathBounds`: float AABB.
- `PathFacet`: vertices, polygon kind, attributes, blocking flag, walkable-floor flag, dynamic flag, optional source id.
- `PathFloorSample`: `hasFloor`, `inVoid`, `z`, `normalZ`, `facetIndex`.
- `PathObject`: `canFly`, `radius`, `stepLength`, `stepHeight`.
- `PathPlanRequest`: actor id/index, source, target, object, node limit, map revision.
- `PathPlanResult`: status, waypoints, analyzed-node count, revision.
- `ActorPathState`: target snapshot, source snapshot, active waypoint vector, waypoint index, request id, in-progress
  flag, failed-until time, target-moved threshold, last source position, map revision.

Use float geometry internally and quantize only A* node keys. The reference uses `short` because it is shaped around MM
memory; OpenYAMM already stores runtime movement in floats.

### Path Map

`PathMap` owns static path geometry and queries:

- `buildSpatialGrid(float cellSize)`.
- `floorAt(PathPoint position)`.
- `traceLine(PathPoint from, PathPoint to, float radius, bool checkBody)`.
- `traceWalkSegment(PathPoint from, PathPoint to, const PathObject &object)`.
- `canReachDirectly(PathPoint from, PathPoint to, const PathObject &object)`.

Implementation details:

- Use a coarse 3D grid similar in purpose to the reference `facet_groups`, but implement it natively with OpenYAMM data
  structures.
- Do not reuse movement-controller swept collision for A* validation. Planning needs cheap segment feasibility; movement
  remains authoritative and can still reject a waypoint step.
- Reuse existing geometry helper concepts where they already exist, but avoid adding forwarding wrappers that only hide
  duplicated ownership.
- Keep non-blocking logic aligned with current face attributes: portal is non-blocking; invisible plus untouchable is
  non-blocking; normal untouchable/invisible behavior must match indoor/outdoor collision rules.
- Walking segment validation should sample along the segment at `min(stepLength, 24)`-like increments, snap to floor,
  reject void, and reject floor deltas above `stepHeight`.
- Body clearance should trace center plus left/right side lines at actor radius. Later enhancement can add high/low body
  traces, but the first integration should keep parity with the reference behavior.

### A* Planner

`PathPlanner` should implement a bounded route search:

- 8-neighbor ground search.
- 26-neighbor flying search.
- Step size: `max(object.stepLength, 24.0f)`.
- Walking nodes are floor-snapped before enqueue.
- Ground heuristic: squared distance plus an uphill penalty.
- Flying heuristic: squared 3D distance.
- Stop when the node is within `stepSize * 4` of the target and direct trace to target succeeds.
- Return waypoints in actor-travel order.
- Enforce a hard node limit. Start with `8000` for MMerge parity, but expose it as a constant/config on the runtime.

Avoid per-frame allocations where practical:

- Use a binary heap for the open set.
- Use quantized node keys in an unordered map/set.
- Reuse scratch buffers inside a planner instance owned by the world path runtime.

### Job Scheduling

Start with a synchronous planner behind a strict node limit for unit tests and the first indoor prototype. Add
`ActorPathRuntime` before enabling broad runtime use:

- Max jobs per map: 50.
- Max worker threads: 1 or 2.
- Max completed-result applications per actor tick: bounded.
- Cancel all jobs on map unload, save/load boundary, or map path revision change.
- Do not block the actor update loop waiting for a path. If a path is pending, either continue direct movement when
  direct movement is still useful, or hold briefly when direct movement is known blocked.

This mirrors the MMerge behavior without importing the DLL-shaped API.

## World Builders

### Indoor

Add `game/indoor/IndoorPathfindingBuilder.h/.cpp`.

Required work:

- Build `PathMap` from `IndoorMapData` faces and runtime vertices.
- Respect runtime door/mechanism movement. Do not duplicate the private cache logic inside
  `IndoorMovementController`; extract a shared indoor runtime collision/path geometry cache if needed.
- Use the same authoritative face attributes and mechanism state sources as indoor movement:
  `MapDeltaData`, `EventRuntimeState`, door distance, and face attribute overrides.
- Include portals as non-blocking.
- Include walkable floors and ceilings for `floorAt`, but only blocking facets for line/body traces.
- Rebuild or update when the indoor geometry revision changes. The current movement runtime already tracks door
  signatures and surface revision; pathfinding should consume the same revision source.

Integration point:

- `IndoorWorldRuntime` owns one `ActorPathRuntime` and one indoor `PathMap` cache.
- Before `applyIndoorActorMovementIntegration` calls `movementController.resolveMove`, ask the path runtime to resolve
  the pursuit waypoint for `ActorMovementIntent`.
- If a waypoint is active, replace `desiredMoveX/Y/Z` with direction to that waypoint and leave the rest of movement
  integration unchanged.
- If direct trace to target is clear, clear path state and use the existing direct pursuit.

### Outdoor

Add `game/outdoor/OutdoorPathfindingBuilder.h/.cpp`.

Required work:

- Build terrain facets from the ODM height map.
- Exclude water from ground walkability for non-water-walking monsters.
- Add blocking proxy volumes for water boundaries, matching the behavior of the reference but implemented from
  OpenYAMM terrain/land-mask helpers.
- Add bmodel facets with current face attributes.
- Add blocking decorations and sprite objects as proxy cylinders or coarse cubes. Use existing collision sets as the
  authoritative source.
- Rebuild on map load and when bmodel face attributes or collision sets change.

Outdoor policy:

- Initially pathfind ground monsters only. Outdoor flying monsters usually do not need this and MMerge skips them.
- Keep existing outdoor water restriction as authoritative. Pathfinding should reduce bad water routes, but movement
  must still prevent invalid entry.
- Use outdoor step length `radius * 2.0f` for MMerge parity.

## Runtime Policy

Pathfinding should be considered only when all of these are true:

- Actor is active, alive, movement allowed, and currently pursuing a party/actor target.
- Actor is not already in melee range.
- Target is sensed but direct walking/flying reach is blocked, or the last movement step was blocked by static geometry.
- The actor is within practical planning range.
- The actor is not under a failed-path retry cooldown.

Suggested initial thresholds:

- Indoor ground actors: target distance <= `12000`.
- Indoor flying actors: target distance <= `6000`.
- Outdoor ground actors: target distance <= `12000`.
- Rebuild if target moved more than `1024`.
- Retry failed path after 2 to 4 in-game minutes or a short real-time equivalent if in-game time is not advanced during
  combat ticks.
- Advance waypoint when XY distance to waypoint is less than actor radius.

Direct reach test:

- For melee actors, require `PathMap::canReachDirectly` with body radius and walking/flying rules.
- For ranged actors, existing LOS can still allow attacking. Pathfinding should only move ranged actors when combat
  engagement decided they should pursue.

Pending path behavior:

- If no path exists and direct movement is not known blocked, continue current direct pursuit.
- If direct movement is blocked and a path job is pending, hold/stand briefly instead of invoking static crowd sidestep.
- If planning fails, fall back to current behavior only after cooldown. Do not retry every frame.

## Crowding Heuristic Replacement

Current crowd steering has two jobs mixed together:

- Dynamic local avoidance for actor/party contacts.
- Recovery when direct pursuit hits static geometry.

After pathfinding:

- Keep `AI_CrowdSteer`, `AI_CrowdStand`, `AI_CrowdRetreat`, and `AI_CrowdSidestep` for actor/party contact and close
  dynamic blockage.
- Stop using crowd sidestep/retreat as the primary response to static walls. Indoor should no longer set
  `crowdSteeringTriggersOnMovementBlocked = true` for ordinary static blocking once pathfinding is active.
- Add enough movement-block detail to distinguish static geometry from actor contact. Indoor already has
  `IndoorMoveDebugInfo::primaryBlockKind`; outdoor should expose similar coarse debug info if needed.
- If a path exists but the next waypoint is temporarily blocked by another actor, local crowd steering may still run.
- If a path exists but static geometry rejects the next waypoint repeatedly, invalidate the path and request a rebuild.

## Data Flow

Per actor tick:

1. World runtime collects normal `ActorAiFacts`.
2. `GameplayActorAiSystem::updateActors` decides combat, attack, and pursuit intent.
3. World runtime receives `ActorMovementIntent`.
4. If the intent is pursuit movement, world runtime asks `ActorPathRuntime` for a waypoint decision.
5. `ActorPathRuntime` checks direct reach and path state:
   - direct reachable: clear path, keep direct movement;
   - path available: return current waypoint;
   - path stale/missing and eligible: enqueue request;
   - path failed/pending: return hold/direct fallback policy.
6. World runtime converts selected target point to `desiredMoveX/Y/Z`.
7. Existing movement controller resolves actual movement.
8. Post-movement facts update local contact/crowd/path invalidation state.

No generated path state should be saved at first. Clear and rebuild on load.

## Diagnostics

Add optional debug-only visibility:

- Current path waypoints for selected/nearby actor.
- Path request status: direct, queued, active, success, failed, cooldown, stale revision.
- Node count and planning time.
- Static block reason that caused a path request.
- Map path revision.

Keep diagnostics out of normal logs.

## Implementation Phases

### Phase 1 - Core Path Map And Tests

- Add `game/pathfinding/*` core types and `PathMap`.
- Add unit tests for:
  - line trace through/around a wall;
  - floor selection below and above;
  - void rejection;
  - walk segment step-height rejection;
  - body-radius side trace rejection.
- No world runtime integration yet.

### Phase 2 - A* Planner

- Implement bounded A*.
- Add unit tests for:
  - route around a wall;
  - no route through void;
  - stairs/ramp with allowed step height;
  - too-high step rejected;
  - flying path over a ground-only obstacle;
  - node limit failure.

### Phase 3 - Indoor Builder Prototype

- Add indoor path map build from BLV runtime geometry.
- Factor shared indoor geometry cache if needed so movement and pathfinding do not diverge.
- Add a headless or unit fixture test using a simple indoor map or synthetic `IndoorMapData`.
- Integrate path waypoint override in `IndoorWorldRuntime`.
- Enable only for active pursuing actors behind a runtime feature flag or internal constant during validation.

### Phase 4 - Indoor Behavior Replacement

- Use pathfinding before static crowd steering.
- Change indoor post-move crowd steering so static wall blocks invalidate/request paths rather than immediately
  sidestepping.
- Keep actor-contact crowd behavior unchanged.
- Add regression coverage for a blocked indoor pursuer reaching the party through a doorway/corridor.

### Phase 5 - Outdoor Builder And Ground Actors

- Add outdoor path map build from terrain, water mask, bmodels, decorations, and sprite blockers.
- Integrate path waypoint override in `OutdoorWorldRuntime` for ground actors.
- Keep outdoor water restriction authoritative.
- Add regression coverage for ground monsters routing around water/blocking bmodels.

### Phase 6 - Runtime Job Queue

- Add bounded async planning to `ActorPathRuntime`.
- Cancel jobs on map unload/save/load/path revision change.
- Apply completed paths in actor update without blocking.
- Add stress coverage for many active actors and stale target/revision cancellation.

### Phase 7 - Tuning And Cleanup

- Tune step length, step height, node limit, planning range, and retry cooldown.
- Remove or narrow static-obstacle fallback behavior from crowd steering.
- Add debug overlay rendering for current paths and path states.
- Run focused manual tests in indoor corridors, doorways, outdoor water edges, bmodel-heavy maps, and actor crowds.

## Validation

Required automated validation before enabling broadly:

- `cmake --build build --target openyamm_unit_tests -j25`
- `./build/tests/openyamm_unit_tests`
- `cmake --build build --target openyamm -j25`

Focused behavior validation:

- Indoor static obstacle: hostile ground actor routes around a wall/doorway to reach party.
- Indoor door/mechanism: path invalidates or updates after a door changes position.
- Indoor dynamic crowd: two actors do not continuously replan around each other; local contact steering handles it.
- Outdoor water: non-water monster avoids water path and still respects movement water restriction.
- Outdoor bmodel: monster routes around a blocking model facet.
- Failed route: actor does not enqueue a path every frame.
- Target movement: path rebuilds only after meaningful target displacement.
- Save/load/map transition: queued paths are cleared and no stale waypoint is applied.

## Non-Goals

- Do not replace `IndoorMovementController` or `OutdoorMovementController`.
- Do not pathfind through moving actors as A* blockers in the first implementation.
- Do not save generated paths.
- Do not expose pathfinding to Lua until the native runtime has stable ownership and diagnostics.
- Do not import the MMerge DLL API shape.

## Open Questions

- Whether `step_height = 40` should remain a fixed MMerge-parity constant or be derived from movement-controller
  `MaximumRise` per world.
- Whether pathfinding direct-reach should use actor eye/target height for flying monsters, or foot-level points plus
  vertical clearance.
- Whether outdoor blocking decorations should be cubes for MMerge parity or cylinders for closer OpenYAMM collision
  parity. Cylinders are likely more correct; cubes may match the reference path data more closely.
- Whether the first runtime integration should be guarded by a user/debug setting until manual map coverage is broad.
