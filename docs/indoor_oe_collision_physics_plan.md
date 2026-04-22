# Indoor OE-Like Collision / Physics Plan

## Goal

Replace the current simplified indoor movement resolver with a structurally OE-like BLV collision/physics resolver.

The target is not a visual workaround and not a portal-specific heuristic. Indoor party and actor movement should use
the same logical collision model as OE:

- swept low/high body spheres;
- nearest collision along the movement segment;
- bounded iterative movement;
- face, portal, party, actor, decoration, and sprite-object collision categories;
- collision response based on hit type;
- sector transition through portals during movement;
- floor/ceiling/step-up handling integrated with the collision loop.

OpenEnroth may be inspected only as reference. Do not copy OE code.

## Current Problem

The current `IndoorMovementController::resolveMove` is a simplified destination test:

- it tries the final position;
- if blocked, it tries wall projection and axis fallback;
- it does not sweep to the nearest collision point;
- it does not preserve OE's low/high sphere model;
- it currently compensates for this by using a reduced non-flying indoor actor navigation radius.

That makes large indoor monsters feel too wide in portals and makes actor-vs-actor blocking too frequent. The reduced
navigation radius is a temporary gameplay unblocker, not the desired structural solution.

## OE Behavior To Model

Use the local reference only:

- `reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp`
- `CollideBodyWithFace`
- `CollideIndoorWithGeometry`
- `CollideIndoorWithPortals`
- `CollideWithActor`
- `ProcessActorCollisionsBLV`
- `ProcessPartyCollisionsBLV`

Reference-level behavior to preserve conceptually:

- Movement has a collision state with low sphere, high sphere, velocity, direction, move distance, adjusted move
  distance, hit PID/type, collision position, and sector id.
- Actor BLV movement uses authored actor radius for face/body collision.
- Actor-vs-actor crowd probing uses an override radius of `40`.
- The loop advances only to the nearest collision distance, then adjusts velocity and retries.
- Face hits project remaining movement along a slide plane.
- Actor hits can produce crowd/flee/stand behavior facts, but gameplay AI response remains shared.
- Party hits block hostile actors instead of letting them pass through.
- Portal-adjacent sectors are considered only when the swept body touches the portal plane/box closely enough.
- The actor/party sector id updates as portal crossing succeeds.
- Floor stepping allows small upward movement but prevents bad out-of-bounds moves and unsupported large drops.

## Ownership Boundary

Indoor collision/physics is world-specific and belongs in indoor world code:

- `game/indoor/IndoorMovementController.*`
- `game/indoor/IndoorWorldRuntime.*`
- `game/indoor/IndoorPartyRuntime.*`
- indoor collision helpers if new files are needed

Shared gameplay should not own BLV face geometry, sector portals, moving mechanism vertices, or floor/ceiling
queries.

Shared actor AI should continue to own behavior decisions. Indoor movement should only report movement/contact facts
needed by shared AI.

## Desired Public Shape

Prefer a contained indoor movement API like:

```cpp
IndoorMoveResult IndoorMovementController::resolveMove(const IndoorMoveRequest &request) const;
```

Where the request/result are coarse and world-specific:

- request: current move state, body dimensions, velocity, jump/fly flags if needed, ignored actor, colliders;
- result: final move state, collided actors, primary block/hit info, sector transition info, landed/floor info.

Avoid callback bags. Avoid large inline lambdas inside render/update loops.

## Implementation Strategy

Do not rewrite everything blindly. Build the OE-like solver in stages, while keeping the game buildable.

### Stage 1 - Audit And Shape

1. Audit current indoor movement entry points:
   - party movement;
   - actor movement;
   - projectile world collision if it shares helpers;
   - current debug/instrumentation.
2. Audit OE BLV movement behavior and record the exact conceptual deltas in `PROGRESS.md`.
3. Define internal collision structs:
   - collision body;
   - collision state;
   - collision hit;
   - collision request/result;
   - collision category enum.
4. Keep these structs private to indoor movement unless there is a clear reason to expose them.

### Stage 2 - Swept Face Collision

1. Implement swept sphere-vs-face tests for indoor faces using existing generated BLV geometry.
2. Sweep low sphere, high sphere, midpoint, and face-center-height sphere similarly to OE.
3. Track nearest hit by adjusted movement distance.
4. Ignore untouchable/ethereal/non-blocking moving mechanism faces correctly.
5. Use mechanism-adjusted vertices.
6. Use sector-limited face candidates plus portal-adjacent sectors.
7. Add unit/doctest coverage for pure geometry pieces where possible.

### Stage 3 - Portal Sector Handling

1. Implement OE-like portal-adjacent sector inclusion from swept body bounds and portal plane distance.
2. Implement sector id update when movement crosses a portal.
3. Ensure actors can pass through open portals without requiring the final position to be centered perfectly.
4. Ensure closed/moving door faces still block when they should.
5. Add targeted diagnostics for sector transitions and portal face hits.

### Stage 4 - Iterative Actor Movement

1. Replace actor movement final-position testing with the swept iterative resolver.
2. Use authored actor radius for BLV face/body collision.
3. Use OE-like actor-vs-actor override radius `40` for crowd/contact probing.
4. Preserve party collider interaction.
5. Report contacted actor count and movement-block state to shared actor AI.
6. Remove the temporary reduced indoor wall-navigation radius workaround once authored radius works correctly.
7. Validate Naga Vault portal cases manually.

### Stage 5 - Iterative Party Movement

1. Move party indoor movement to the same swept resolver.
2. Preserve current controls, jump, gravity, and floor snapping behavior where it intentionally differs from OE.
3. Match OE collision feel for walls, doors, actors, floors, and portals.
4. Ensure hostile actors block party forward movement without excessive sideways sliding.
5. Ensure the party no longer jitters over moving-door pockets.

### Stage 6 - Collision Categories And Responses

1. Implement hit response by category:
   - face;
   - actor;
   - party;
   - decoration;
   - sprite object;
   - portal/sector transition.
2. Face response should project velocity along the slide plane and damp where OE does.
3. Actor/party responses should produce movement/contact facts, not direct gameplay behavior outside shared AI.
4. Floors should stop downward velocity and allow small step-up.
5. Steep faces should prevent uphill pushing where relevant.

### Stage 7 - Cleanup

1. Remove obsolete destination-test wall-slide and axis-fallback code.
2. Remove temporary debug logging or gate it behind an explicit diagnostic flag.
3. Remove temporary radius workaround constants if no longer needed.
4. Keep helper names domain-specific and readable.
5. Keep headers minimal.

## Required Diagnostics

Temporary diagnostics are allowed during the slice, but must be bounded and removable:

- `IndoorCollisionHit` with actor id/name, hit kind, face id, sector id, adjusted distance, move distance;
- `IndoorPortalTransition` with old/new sector and portal face id;
- `IndoorActorMoveBlocked` only while debugging, with log budget;
- optional debug draw for body low/high spheres and blocking face wireframe if needed.

Diagnostics must not become permanent noisy stdout spam.

## Tests

Prefer doctest/unit tests for pure movement geometry where possible:

- swept sphere misses face;
- swept sphere hits nearest face;
- low/high/mid sphere selection picks nearest hit;
- portal-adjacent sector inclusion;
- actor-vs-actor override radius contact calculation;
- velocity projection along a wall normal.

Headless or manual tests are still needed for full BLV integration:

- `blv18` Naga Vault portal actors can pass through portals;
- large nagas no longer need perfect center alignment to pass through a portal;
- actors do not pass through closed doors/walls;
- actors can slide along walls instead of getting pinned;
- actor-vs-actor crowding still blocks enough to prevent overlap but does not jam every portal;
- party collides with hostile actors indoors;
- party movement through opened door pockets does not jitter;
- indoor mechanisms/doors remain passable/blocked according to state.

## Acceptance Criteria

- Indoor actor collision uses swept iterative movement, not destination-only collision.
- Indoor party collision uses the same collision engine or an intentionally shared variant.
- BLV face collision uses authored actor body dimensions once the swept resolver is active.
- Actor-vs-actor contact uses OE-like override radius for crowd/contact probing.
- Portal sector transitions are handled by the movement solver, not by portal-specific hacks.
- The Naga Vault portal case works without shrinking all actor visual/combat radii.
- Existing indoor doors/mechanisms still open, close, block, and become passable correctly.
- Shared actor AI remains shared and only receives movement/contact facts.
- No OpenEnroth code is copied.
- Build and CTest pass.
- `PROGRESS.md` records manual smoke results or explicitly states what remains to test.

## Non-Goals

- Do not rewrite outdoor movement unless an indoor helper can be safely shared without regressions.
- Do not move BLV collision into shared gameplay.
- Do not change spell/projectile gameplay semantics as part of this slice.
- Do not rework actor AI unless a collision result fact is missing.
- Do not keep the reduced indoor actor navigation radius as the final solution.

## Done Definition

This slice is done when:

- all acceptance criteria above are satisfied;
- temporary heuristics and noisy diagnostics are removed or explicitly gated;
- `cmake --build build --target openyamm -j25` passes;
- `ctest --test-dir build --output-on-failure` passes;
- `PROGRESS.md` contains `## Done definition satisfied: YES`.
