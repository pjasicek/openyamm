# OpenYAMM Indoor Sector/Portal Rendering, Collision, and Simulation Architecture

## Purpose

This document defines a production-grade architecture for indoor MM6–MM8-style maps using sectors, portals, actor/billboard ownership, collision queries, and simulation tiers.

Primary goals:

- High performance on large indoor dungeons.
- No obvious rendering artifacts.
- Deterministic and debuggable behavior.
- Robust handling of closed doors, moving doors, portals, sector loops, and actors near boundaries.
- Clean separation between rendering visibility, collision reachability, sound propagation, AI reachability, and actor simulation.
- Avoid fragile assumptions such as “visible sector means all objects in that sector are visible.”

The system should be designed as a reusable spatial layer used by rendering, collision, physics/movement, AI, sound, triggers, and debug tooling.

This document is implementation guidance for OpenYAMM, not only a greenfield architecture. The first implementation
must preserve current content behavior while replacing fragile sector bitmask shortcuts with validated data and
observable migration steps.

Current OpenYAMM-specific failure modes that this architecture must eliminate:

- Non-portal faces with default `roomBehindNumber == 0` being interpreted as sector adjacency.
- Standalone/orphan sector visibility making distant no-portal sectors visible through walls.
- Decorations/actors/sprite objects accepted by sector id and then culled only by the global camera frustum.
- Diagnostics counting sector-eligible objects as rendered even when later frustum/texture/hidden-state tests skip them.
- Actor, decoration, and sprite ownership existing only as a single sector id, causing portal-edge popping or leakage.
- Rendering, picking, collision, and AI using subtly different sector interpretations without a shared validated graph.

---

# 1. Core Concepts

## 1.1 Sector

A **sector** is a spatial cell, typically a room, corridor segment, or convex-ish part of an indoor dungeon.

A sector contains or references:

- Static render faces/meshes.
- Static collision faces/triangles.
- Portals to neighboring sectors.
- Lights affecting the sector.
- Actors currently in the sector.
- Billboards/decorations/items currently in the sector.
- Trigger volumes or face-event metadata.
- Optional per-sector BVHs for render/collision queries.

```cpp
struct Sector
{
    SectorId id;
    AABB bounds;

    std::vector<FaceId> renderFaces;
    std::vector<CollisionFaceId> collisionFaces;
    std::vector<PortalId> portals;

    std::vector<ActorId> actors;
    std::vector<BillboardId> billboards;
    std::vector<LightId> lights;
    std::vector<TriggerId> triggers;

    Bvh renderFaceBvh;
    Bvh collisionFaceBvh;
};
```

Important: a sector should not be assumed to be perfectly convex unless the imported map data guarantees that. The engine should work with imperfect/non-convex sectors, but performance and correctness improve when sectors are reasonably small and room-like.

## 1.2 Portal

A **portal** connects two sectors. It usually represents a doorway, corridor opening, window, gate, secret passage, or any opening through which visibility/movement/sound can pass.

In imported BLV data, a portal edge must be derived from a validated portal face, not from arbitrary `roomNumber` /
`roomBehindNumber` fields. A face contributes a portal edge only when all of the following are true:

- The face is marked as a portal by source data or a trusted import rule.
- Both connected sector ids are valid and distinct.
- The face has at least three valid vertices and a usable polygon area.
- The portal polygon overlaps or is near both connected sector bounds.
- Door/mechanism linkage, if present, resolves to a valid runtime door or is explicitly marked as unlinked.

Faces that fail validation remain render/collision faces where appropriate, but must not create graph adjacency. In
particular, default sector id `0` must never be treated as "behind" unless the face is a validated portal to sector `0`.

OpenYAMM already imports BLV sector portal lists as `IndoorSector::portalFaceIds`. The editor's "Connected Rooms"
display is derived from those portal faces by reading each portal face's `roomNumber` and `roomBehindNumber`. The
runtime graph must use that same source of truth, with stricter validation, instead of deriving adjacency from arbitrary
sector face lists.

A validated portal face belongs logically to both connected sectors:

```text
face.roomNumber       = sector A
face.roomBehindNumber = sector B

portal is listed in sector A's portal list
portal is listed in sector B's portal list
sector A connected sectors includes sector B
sector B connected sectors includes sector A
```

The raw BLV data may list the portal face on only one side, or duplicate it through general face lists. The runtime
level-load cache must canonicalize this into one bidirectional portal link and attach that link to both sectors.

Recommended OpenYAMM level-load graph cache:

```cpp
struct IndoorPortalLink
{
    PortalId id;
    FaceId faceId;
    SectorId sectorA;
    SectorId sectorB;
    std::vector<DoorId> blockingDoorIds;
    AABB bounds;
    std::vector<Vec3> polygonWorld;
    PortalValidationFlags validationFlags;
};

struct IndoorSectorPortalCache
{
    SectorId sectorId;
    std::vector<PortalId> portalIds;
    std::vector<SectorId> connectedSectorIds;
};

struct IndoorPortalGraph
{
    std::vector<IndoorSectorPortalCache> sectors;
    std::vector<IndoorPortalLink> portals;
    std::vector<PortalDiagnostic> diagnostics;
};
```

Build this once when the indoor map and scene delta are loaded. Rebuild only when authoritative geometry/portal/door
metadata changes. Per-frame rendering, collision, AI, sound, picking, and diagnostics should read this cache rather than
rescanning all faces or all sectors.

```cpp
struct Portal
{
    PortalId id;

    SectorId a;
    SectorId b;

    std::vector<Vec3> polygonWorld;
    Plane plane;
    AABB bounds;

    std::vector<DoorId> blockingDoorIds;
    PortalFlags flags;
};
```

Recommended portal flags:

```cpp
enum class PortalFlag : uint32_t
{
    BlocksVisibilityWhenClosed = 1 << 0,
    BlocksMovementWhenClosed   = 1 << 1,
    BlocksSoundWhenClosed      = 1 << 2,
    IsWindow                   = 1 << 3,
    IsSecret                   = 1 << 4,
    OneWayVisibility           = 1 << 5,
    OneWayMovement             = 1 << 6,
};
```

A portal can be:

- Open for visibility.
- Open for movement.
- Open for sound.
- Open for AI/pathfinding.

These should be separate queries, not one boolean.

```cpp
bool isPortalOpenForVisibility(const Portal& portal, const WorldState& state);
bool isPortalOpenForMovement(const Portal& portal, const WorldState& state);
bool isPortalOpenForSound(const Portal& portal, const WorldState& state);
bool isPortalOpenForAI(const Portal& portal, const WorldState& state);
```

## 1.3 Door / Moving Occluder

A door is a game object that may affect portals and collision.

```cpp
struct Door
{
    DoorId id;
    float openFraction; // 0 closed, 1 open; not used for first-pass visibility blocking
    DoorState state;
    Transform transform;
    CollisionShapeId collisionShape;
};
```

For production stability, start with binary portal state:

```text
Closed  -> portal blocked
Open    -> portal open
Opening -> portal open
Closing -> portal open
```

Do not implement partial portal clipping for door animation in the first production pass. Moving doors are transitional
and usually last around a second, so treating `Opening` and `Closing` as open preserves fidelity well enough while
keeping traversal deterministic and cheap.

The visibility rule for a door-linked portal is:

```cpp
bool mechanismBlocksPortalVisibility(EvtMechanismState state)
{
    return state == EvtMechanismState::Closed;
}
```

If several mechanisms block the same portal, the portal is blocked when any linked mechanism is `Closed`. Unlinked doors
must not block portals by broad whole-map heuristics. Geometry-overlap door/portal matching may be used as a validation
diagnostic, but the production visibility path should prefer explicit `portal -> blockingDoorIds` links.

---

# 2. Do Not Use One Visibility Set For Everything

Different systems need different sector sets.

Rendering asks:

```text
What can the camera see through open visible portals?
```

Collision asks:

```text
What can the swept capsule/projectile/shape touch during this movement?
```

AI asks:

```text
What sectors can an actor path or reason through?
```

Sound asks:

```text
What sectors can sound propagate through, and with what attenuation?
```

Actor simulation asks:

```text
Which actors need full, reduced, or sleeping updates this frame?
```

Recommended per-frame structure:

```cpp
struct FrameSpatialSets
{
    std::vector<VisibleSectorInstance> visibleForCamera;
    std::unordered_map<SectorId, std::vector<Frustum>> visibleFrustumsBySector;

    std::unordered_set<SectorId> cameraVisibleSectorIds;
    std::unordered_set<SectorId> nearPlayerSectorIds;
    std::unordered_set<SectorId> fullActorTickSectorIds;
    std::unordered_set<SectorId> reducedActorTickSectorIds;
    std::unordered_set<SectorId> soundReachableSectorIds;
};
```

Key rule:

> The sector/portal graph is shared. The traversal policy is system-specific.

---

# 3. Rendering Visibility

## 3.1 Portal Traversal Overview

Indoor visibility should be computed by recursive or stack-based sector/portal traversal.

Algorithm:

```text
1. Find camera sector.
2. Start with full camera frustum.
3. Add current sector as visible with this frustum.
4. For each portal in current sector:
   - skip if any explicitly linked blocking mechanism is Closed
   - skip if portal faces away where applicable
   - skip if portal polygon/bounds outside current frustum
   - compute portal-clipped child frustum
   - recurse into neighboring sector with child frustum
5. Continue until no visible portals remain, recursion depth is reached, or frustum becomes too small.
```

Important:

> A visible sector is only a candidate container. Objects inside still require per-object culling.

## 3.2 Visible Sector Instance

Do not store visibility only as:

```cpp
bool sectorVisible;
```

A sector can be visible through multiple portals with different clipped frustums.

Use:

```cpp
struct VisibleSectorInstance
{
    SectorId sector;
    Frustum clippedFrustum;
    PortalPathHash pathHash;
    int depth;
    float screenAreaEstimate;
};
```

The same sector may appear multiple times if reached through different portal paths.

## 3.3 Portal Traversal Pseudocode

```cpp
void buildVisibleSectors(
    const Camera& camera,
    SectorId cameraSector,
    const WorldState& state,
    VisibleSet& out)
{
    PortalTraversalStack stack;

    stack.push({
        .sector = cameraSector,
        .frustum = camera.frustum,
        .depth = 0,
        .pathHash = {}
    });

    while (!stack.empty())
    {
        TraversalNode node = stack.pop();

        if (node.depth > MaxPortalDepth)
            continue;

        if (isFrustumTooSmall(node.frustum))
            continue;

        out.addVisibleInstance(node.sector, node.frustum, node.pathHash, node.depth);

        const Sector& sector = sectors[node.sector];

        for (PortalId portalId : sector.portals)
        {
            const Portal& portal = portals[portalId];

            if (!isPortalOpenForVisibility(portal, state))
                continue;

            SectorId nextSector = portal.getOtherSector(node.sector);
            if (nextSector == InvalidSectorId)
                continue;

            if (wouldCreateForbiddenPortalCycle(node.pathHash, portalId, nextSector))
                continue;

            if (!node.frustum.intersects(portal.bounds))
                continue;

            if (!portalPolygonFacesCameraEnough(portal, camera.position, node.sector))
                continue;

            Frustum childFrustum;
            if (!clipFrustumThroughPortal(
                    node.frustum,
                    camera.position,
                    portal.polygonWorld,
                    childFrustum))
            {
                continue;
            }

            if (isFrustumTooSmall(childFrustum))
                continue;

            stack.push({
                .sector = nextSector,
                .frustum = childFrustum,
                .depth = node.depth + 1,
                .pathHash = extendPathHash(node.pathHash, portalId, nextSector)
            });
        }
    }
}
```

## 3.4 Portal Clipping

Portal clipping should create a new frustum whose side planes are generated from the camera position and portal polygon edges.

For each portal edge:

```text
plane = plane through camera position and portal edge
orientation = keep inside the portal polygon cone
```

Then intersect these planes with the parent frustum.

Robustness requirements:

- Reject degenerate portal polygons.
- Reject portals almost behind camera.
- Reject portals whose projected screen area is below threshold.
- Use epsilon tolerances consistently.
- Debug-draw portal frustums.

## 3.5 Handling Cycles

Indoor sector graphs may contain cycles:

```text
sector A -> sector B -> sector C -> sector A
```

Avoid infinite recursion using:

- Maximum portal depth.
- Portal-path hash.
- Minimum projected portal area.
- Optional sector/frustum merge.

Do not simply mark a sector as globally visited and skip forever. That can incorrectly cull a sector visible through another portal.

Recommended rule:

```text
Allow revisiting a sector if the new clipped frustum meaningfully expands visibility.
Prevent exact or near-exact repeated portal paths.
Clamp recursion depth.
```

## 3.6 Per-Object Culling

After visible sector instances are collected, cull objects inside them.

An object in a visible sector is renderable only if:

- Its sector is visible through at least one visible sector instance.
- Its bounds intersect the relevant clipped frustum.
- It is not hidden by game state.
- It passes object-specific distance/LOD rules.

```cpp
bool isObjectVisibleInSectorInstances(
    const RenderObject& object,
    const std::vector<Frustum>& sectorFrustums)
{
    for (const Frustum& f : sectorFrustums)
    {
        if (f.intersects(object.worldBounds))
            return true;
    }

    return false;
}
```

Do not submit all actors or billboards in a visible sector blindly.

Implementation requirement for OpenYAMM:

- Sector-mask eligibility is only the first coarse filter.
- Actual submitted counts must be recorded after hidden-state, texture/frame resolution, billboard bounds, and
  sector-instance frustum tests.
- A decoration, actor, item, projectile, or spell billboard in a visible sector must still be rejected if its conservative
  bounds do not intersect any clipped frustum for one of its render memberships.
- Global camera frustum checks are acceptable only for the root sector. Portal-reached sectors must use the clipped
  frustum(s) for that sector instance.
- If visible sector instances are not yet implemented, do not enable aggressive object culling as a correctness fix.
  Use diagnostics to prove the missing clipped-frustum data first.

## 3.7 Static Geometry Rendering

For static sector geometry:

- First include sector based on portal traversal.
- Then test face/meshlet/submesh bounds against the clipped frustum.
- Use a per-sector render BVH if sectors can contain many faces.

```text
visible sector -> render BVH query with clipped frustum -> draw visible face batches
```

For small sectors, a simple face loop is acceptable initially.

## 3.8 Actors, Billboards, Decorations, Items

Actors and billboards should be submitted only if their bounds intersect at least one clipped frustum instance for their sector.

```cpp
for (BillboardId id : sector.billboards)
{
    const Billboard& b = billboards[id];

    if (!isBillboardEnabledByGameState(b))
        continue;

    if (!isObjectVisibleInSectorInstances(b, frustumsForSector[b.sector]))
        continue;

    visibleBillboards.push_back(makeDrawItem(b));
}
```

Billboards near portals or crossing sector boundaries should be either:

- Registered in multiple sectors based on AABB overlap.
- Or assigned to current sector but tested against neighboring portal-visible sectors.

Preferred production solution:

```text
Renderable objects can have multiple sector memberships.
Primary sector is used for simulation ownership.
Visibility sectors are used for rendering culling.
```

OpenYAMM migration rule:

- Runtime actors and sprite objects keep a primary simulation sector.
- Rendering builds or caches a separate `SpatialMembership` from the object's conservative bounds.
- Static decorations get render memberships at map load.
- Dynamic actors/items/projectiles update render memberships after movement or sector transfer.
- A missing or invalid primary sector must not silently become sector `0`; it must be logged and either recovered by
  spatial query or treated as unknown/uncullable in debug builds.

Static decoration import rule:

- Decoration sector id from source data is an initial hint.
- If a decoration's bounds overlap a portal plane or neighboring sector bounds, it may need multiple render memberships.
- Decorations in sectors that are never reachable through validated portals must not become visible through an orphan
  root-frustum fallback unless explicitly tagged as moving/standalone mechanism geometry.

Map-load render membership cache:

```text
sector id -> static decoration ids
sector id -> static sprite/object ids
sector id -> static light ids
sector id -> mechanism render object ids
```

The cache must be built from validated sector ownership and conservative bounds. It must not use "all objects in all
sectors" scans during normal rendering. Dynamic actors, dropped items, projectiles, and spell effects update their render
memberships when they move, change sector, or grow/shrink bounds.

## 3.9 Transparent Sorting

After culling, transparent billboards should be sorted back-to-front or handled by the renderer’s selected transparency method.

Simple MM-style approach:

```cpp
std::sort(visibleBillboards.begin(), visibleBillboards.end(),
    [&](const BillboardDrawItem& a, const BillboardDrawItem& b)
    {
        return distanceSquared(camera.position, a.position) >
               distanceSquared(camera.position, b.position);
    });
```

Caveats:

- Sorting by center distance can fail for large sprites.
- Intersecting transparent geometry can still artifact.
- For MM-style sprites, center-distance sorting is usually acceptable.

## 3.10 Large Objects Spanning Sectors

Large render/collision objects should not rely on a single sector.

Use one of:

```text
A. Multi-sector registration based on object bounds.
B. Global object list with sector-filtered broadphase.
C. Parent sector + neighbor-sector checks.
```

Recommended:

```cpp
struct SpatialMembership
{
    SectorId primarySector;
    SmallVector<SectorId, 4> overlappingSectors;
};
```

---

# 4. Collision and Movement

## 4.1 Collision Is Not Camera Visibility

Do not use the camera-visible sector set as the collision sector set.

Rendering visibility:

```text
camera frustum through visible portals
```

Collision reachability:

```text
swept shape through movement-open portals
```

A player can collide with something around a corner that is not visible. A projectile can pass through a portal not currently visible to the camera. AI can path through sectors not visible to the camera.

## 4.2 Collision Candidate Gathering

For a moving capsule:

```text
1. Compute swept AABB of capsule from start to end.
2. Start from actor's current sector.
3. Add collision faces from sectors whose bounds intersect the swept AABB.
4. Traverse through portals open for movement if portal bounds intersect swept AABB.
5. Query per-sector collision BVHs for candidate triangles/faces.
```

```cpp
CollisionCandidates gatherCapsuleSweepCandidates(
    const CollisionWorldSnapshot& snapshot,
    SectorId startSector,
    const Capsule& capsule,
    Vec3 delta)
{
    AABB sweptBounds = capsule.computeSweptAabb(delta).expanded(CollisionEpsilon);

    Queue<SectorId> queue;
    SmallSet<SectorId> visited;

    queue.push(startSector);
    visited.insert(startSector);

    CollisionCandidates out;

    while (!queue.empty())
    {
        SectorId sectorId = queue.pop();
        const SectorCollision& sector = snapshot.sectors[sectorId];

        if (!sweptBounds.intersects(sector.bounds))
            continue;

        sector.collisionBvh.query(sweptBounds, out.triangles);

        for (PortalId portalId : sector.portals)
        {
            const Portal& portal = snapshot.portals[portalId];

            if (!isPortalOpenForMovement(portal, snapshot.state))
                continue;

            if (!sweptBounds.intersects(portal.bounds))
                continue;

            SectorId next = portal.getOtherSector(sectorId);
            if (visited.insert(next))
                queue.push(next);
        }
    }

    return out;
}
```

## 4.3 Player/Actor Shape

For MM-style movement, prefer a vertical capsule or vertical cylinder-like controller.

Recommended initial model:

```cpp
struct CharacterCollider
{
    Vec3 basePosition;
    float radius;
    float height;
    float stepHeight;
    float skinWidth;
};
```

Avoid full rigid-body simulation for actors. Use game-controlled movement:

```text
AI/input decides desired movement.
Collision system resolves allowed movement.
Game stores final position.
```

## 4.4 Move-and-Slide

Core algorithm:

```text
1. desiredMove = velocity * dt or input movement.
2. Sweep capsule along desiredMove.
3. If no hit, move fully.
4. If hit, move to safe distance before impact.
5. Project remaining movement onto collision plane.
6. Repeat for limited iterations.
7. Resolve ground/ceiling.
```

```cpp
MoveResult moveAndSlide(
    const CollisionWorldSnapshot& snapshot,
    const CharacterCollider& collider,
    SectorId startSector,
    Vec3 desiredMove,
    CollisionScratch& scratch)
{
    Vec3 position = collider.basePosition;
    Vec3 remaining = desiredMove;

    MoveResult result;

    for (int i = 0; i < MaxSlideIterations; ++i)
    {
        if (lengthSquared(remaining) < MinMoveDistanceSq)
            break;

        Capsule capsule = makeCapsuleAt(collider, position);
        SweepHit hit = sweepCapsule(snapshot, startSector, capsule, remaining, scratch);

        if (!hit.hit)
        {
            position += remaining;
            break;
        }

        float safeFraction = std::max(0.0f, hit.fraction - collider.skinWidth);
        position += remaining * safeFraction;

        Vec3 normal = hit.normal;
        remaining = remaining - normal * dot(remaining, normal);

        result.hitSomething = true;
        result.lastHit = hit;
    }

    result.position = position;
    return result;
}
```

Production requirements:

- Use skin width to avoid resting exactly on surfaces.
- Clamp tiny remaining movement to zero.
- Limit slide iterations.
- Use stable normal selection when multiple faces are hit at nearly same time.
- Add stuck recovery for actors starting slightly inside geometry.

## 4.5 Grounding, Slopes, and Stairs

Recommended approach:

```text
Horizontal movement and vertical grounding should be handled separately where possible.
```

For old-school RPG movement, a 2.5D controller is often more robust than full arbitrary rigid-body physics.

Grounding step:

```text
1. After horizontal move, probe downward.
2. Find best walkable floor within snap distance.
3. If floor normal is walkable, snap to floor.
4. If too steep, treat as wall/slide.
5. Check ceiling clearance.
```

Slope rules:

```cpp
bool isWalkableFloor(const Vec3& normal)
{
    return dot(normal, WorldUp) >= cos(MaxWalkableSlopeRadians);
}
```

Stairs/steps:

```text
1. Try normal move.
2. If blocked by low obstacle, try raising by stepHeight.
3. Move horizontally.
4. Probe down to valid floor.
5. Accept if final position is stable and not penetrating ceiling.
```

## 4.6 Actor-vs-Actor Collision

Do not solve actors as physical rigid bodies.

Recommended stages:

```text
1. Move actors in parallel against static world.
2. Build dynamic actor spatial hash.
3. Find overlaps.
4. Resolve overlaps in deterministic actor-id order.
```

Actor overlap resolution should be simple:

```text
- separate capsules/circles horizontally
- do not create complex pushing chains
- allow soft overlap for far/reduced actors if acceptable
```

Deterministic pair sorting:

```cpp
std::sort(pairs.begin(), pairs.end(), [](const ActorPair& a, const ActorPair& b)
{
    return std::tie(a.minActorId, a.maxActorId) <
           std::tie(b.minActorId, b.maxActorId);
});
```

## 4.7 Projectiles

Projectiles should usually use raycasts or swept spheres, not rigid bodies.

```text
fast projectile -> raycast/swept sphere from old position to new position
slow projectile -> swept sphere/capsule if needed
area spell      -> sector-aware overlap query
```

Projectile traversal should use collision reachability, not render visibility.

## 4.8 Collision Metadata

Static collision faces should preserve game metadata.

```cpp
struct CollisionFace
{
    Triangle triangle;
    Vec3 normal;

    SectorId sectorId;
    FaceId sourceFaceId;
    MaterialId materialId;
    EventId eventId;

    CollisionFlags flags;
};
```

This allows raycasts and sweeps to answer:

```text
What did I hit?
Which sector?
Which face?
Which material?
Which event/script?
Does it block movement/projectiles/sight?
```

---

# 5. Physics Model

## 5.1 Keep Physics Simple

For MM-style gameplay, physics should be simple and game-driven.

Use:

```text
velocity integration
simple gravity
move-and-slide collision
floor/ceiling resolution
scripted doors/lifts/platforms
ray/sweep projectiles
```

Avoid initially:

```text
rigid-body impulse solvers
stacking boxes
constraints/joints
ragdolls
mass/inertia gameplay
```

## 5.2 Character Update

```cpp
void updateCharacter(Character& c, float dt)
{
    if (!c.grounded)
        c.velocity.z -= Gravity * dt;

    Vec3 desiredMove = c.velocity * dt;

    MoveResult move = collisionWorld.moveAndSlide(
        c.collider,
        c.sector,
        desiredMove);

    c.position = move.position;
    c.sector = findBestSectorForPosition(c.position, c.sector);
    c.grounded = move.grounded;

    if (move.hitFloor && c.velocity.z < 0.0f)
        c.velocity.z = 0.0f;

    if (move.hitCeiling && c.velocity.z > 0.0f)
        c.velocity.z = 0.0f;
}
```

## 5.3 Doors, Lifts, Moving Geometry

Treat doors/lifts as scripted kinematic objects.

```text
Game animation decides transform.
Collision snapshot includes current transform.
Portal visibility state is derived from mechanism state:
Closed blocks traversal; Open, Opening, and Closing allow traversal.
Collision may still use the current moving geometry snapshot.
```

For stable multithreaded queries, snapshot moving collider transforms once per frame.

```cpp
struct MovingColliderSnapshot
{
    ColliderId id;
    Transform transform;
    ShapeRef shape;
    CollisionMask mask;
    SectorMembership sectors;
};
```

---

# 6. Actor Simulation and Performance

## 6.1 Actor Simulation Tiers

Do not fully update every actor in the dungeon every frame.

```cpp
enum class ActorTickTier
{
    Full,
    Reduced,
    Sleeping,
    Frozen
};
```

Suggested semantics:

```text
Full:
    near player, visible, in combat, attacking, being attacked, scripted important

Reduced:
    nearby through portals, audible, recently active, not directly visible

Sleeping:
    far sector, behind closed door, not relevant this frame

Frozen:
    unloaded or inactive map region
```

## 6.2 Tier Assignment

Use sector graph, distance, visibility, combat state, and scripts.

```text
Full update sectors:
    player sector
    visible sectors near the player
    adjacent open sectors
    sectors containing aggro actors

Reduced update sectors:
    sectors within N portal hops
    sectors sound-reachable with active actors

Sleeping:
    sectors behind closed doors or too far away
```

Important:

> Do not make actor ticking depend only on camera visibility. Monsters should not freeze just because the player looks away.

## 6.3 Reduced Tick Example

```cpp
void updateActorByTier(Actor& actor, float dt)
{
    switch (actor.tickTier)
    {
        case ActorTickTier::Full:
            updateAI(actor, dt);
            updateMovement(actor, dt);
            updateAnimation(actor, dt);
            break;

        case ActorTickTier::Reduced:
            actor.reducedAccumulator += dt;
            if (actor.reducedAccumulator >= ReducedTickInterval)
            {
                updateAI(actor, actor.reducedAccumulator);
                updateCoarseMovement(actor, actor.reducedAccumulator);
                actor.reducedAccumulator = 0.0f;
            }
            break;

        case ActorTickTier::Sleeping:
            updateLongTermTimers(actor, dt);
            break;

        case ActorTickTier::Frozen:
            break;
    }
}
```

## 6.4 Actor Sector Membership

Actors should maintain current sector and possibly overlapping sectors.

```cpp
struct ActorSpatialState
{
    SectorId primarySector;
    SmallVector<SectorId, 4> overlappingSectors;
    AABB worldBounds;
};
```

After movement:

```text
1. Try to keep actor in current sector if position still valid.
2. If crossing open portal, transfer to neighbor sector.
3. If ambiguous, use nearest floor/containing sector.
4. If lost, use fallback spatial query and log warning.
```

---

# 7. Multithreading

## 7.1 Recommended Frame Pattern

Use snapshot -> parallel queries -> deterministic apply.

```text
1. Build immutable frame snapshot.
2. Build actor/projectile/query jobs.
3. Run queries in parallel.
4. Store results into per-job result buffers.
5. Apply results on main thread or in deterministic ordered phases.
```

```cpp
void PhysicsSystem::update(float dt)
{
    CollisionWorldSnapshot snapshot = buildCollisionSnapshot();

    buildActorMoveJobs(snapshot, dt, moveJobs);

    jobSystem.parallelFor(moveJobs.size(), [&](size_t i)
    {
        CollisionScratch& scratch = workerScratch.local();
        moveResults[i] = processActorMoveJob(snapshot, moveJobs[i], scratch);
    });

    applyMoveResultsDeterministically(moveResults);
    resolveActorOverlapsDeterministically();
    processTriggersDeterministically();
}
```

## 7.2 Thread Safety Rules

Worker threads may:

- Read immutable sector/portal/collision snapshots.
- Use thread-local scratch buffers.
- Write to their own result slot.

Worker threads must not:

- Mutate actor state directly.
- Emit game events directly.
- Modify sector membership directly.
- Spawn/despawn entities directly.
- Lock a global collision mutex for every query.

## 7.3 Thread-Local Scratch

Avoid allocations inside tight query loops.

```cpp
struct CollisionScratch
{
    std::vector<SectorId> sectorQueue;
    std::vector<TriangleCandidate> triangleCandidates;
    std::vector<PortalId> portalCandidates;
};
```

Use worker-local scratch:

```cpp
CollisionScratch& scratch = workerScratch.local();
scratch.clearButKeepCapacity();
```

## 7.4 Determinism

To avoid hard-to-reproduce bugs:

- Apply actor results in stable actor-id order.
- Sort trigger events before processing.
- Sort actor overlap pairs before resolving.
- Do not let thread scheduling affect gameplay state.
- Avoid unordered container iteration for gameplay-visible results.

---

# 8. Line of Sight, Picking, Sound, and AI

## 8.1 Raycasts and Picking

Mouse picking and projectiles should use sector-aware raycasts.

```text
1. Start in camera/source sector.
2. Raycast against sector collision/render faces.
3. If ray hits blocking face, stop.
4. If ray crosses an open portal, continue into neighbor sector.
5. Return closest valid hit.
```

Picking should preserve face/object metadata:

```cpp
struct PickHit
{
    bool hit;
    float distance;
    Vec3 position;
    Vec3 normal;

    SectorId sector;
    FaceId face;
    ActorId actor;
    BillboardId billboard;
    EventId event;
};
```

## 8.2 Line of Sight

LOS is similar to raycast, but uses visibility blockers rather than movement blockers.

```cpp
bool hasLineOfSight(SectorId fromSector, Vec3 from, SectorId toSector, Vec3 to)
{
    // Traverse through visibility-open portals and blocking sight geometry.
}
```

Closed doors should usually block LOS.

## 8.3 Sound Propagation

Sound should traverse sound-open portals with attenuation.

```text
sound cost = geometric distance + portal penalty + door penalty
```

Use this for:

- Monster aggro.
- Ambient sound occlusion.
- Event sounds behind doors.

## 8.4 AI Reachability

AI/pathfinding should use movement-open portals.

Do not let AI path through closed doors unless the actor can open them or the script allows it.

---

# 9. Rendering Artifact Prevention

## 9.1 Common Artifacts

Potential issues:

- Distant no-portal/orphan sectors marked visible by root camera frustum through walls.
- Decorations or torches from a visible sector rendered over black because only global frustum culling was applied.
- Invalid `roomBehindNumber == 0` links making enclosed rooms appear adjacent to sector `0`.
- Sector visible through one portal but object incorrectly skipped through another portal.
- Sector marked globally visited too early.
- Sprites submitted even though outside portal-clipped frustum.
- Actor near portal disappears due to single-sector ownership.
- Closed door visually blocks portal but traversal still renders sector behind it.
- Portal polygon mismatch leaves cracks or over-culls geometry.
- Transparent billboards sorted incorrectly.
- Large object crosses sector boundary and is culled.
- Camera exactly on portal plane creates flickering.
- Degenerate portal creates invalid frustum.

## 9.2 Rules to Avoid Artifacts

- Store visible sector instances, not only sector ids.
- Cull objects against the clipped frustum for that sector instance.
- Allow sector revisits through meaningfully different frustums.
- Give actors/billboards multi-sector membership near portals.
- Use conservative bounds for billboards and animated actors.
- Add epsilon to portal/frustum tests.
- Use debug visualization for portals, clipped frustums, sector ids, and culling decisions.
- Keep door visual state and portal blocking state synchronized.
- Do not have a generic orphan-sector render fallback. Standalone/moving geometry must be represented as validated
  mechanism render objects with explicit bounds and sector membership.
- Log and quarantine invalid sector links instead of treating them as valid adjacency.

## 9.3 Conservative Culling Bias

When uncertain, prefer slight overdraw over visible popping.

Recommended:

```text
expand object bounds slightly
expand portal bounds slightly
use conservative frustum intersection
avoid tiny epsilon over-culling
```

Production rendering should prioritize:

```text
no disappearing objects > minimal draw count
```

---

# 10. Data Import and Validation

## 10.1 Import-Time Validation

During map import/build, validate:

- Every graph adjacency comes from a validated portal face.
- Every portal connects exactly two valid sectors.
- Every validated portal is canonicalized into one bidirectional portal link.
- Every bidirectional portal link is attached to both connected sectors' portal lists.
- Every sector's connected-sector list is derived only from its validated bidirectional portal links.
- No non-portal face with default or stale `roomBehindNumber` creates adjacency.
- Sector `0` links are accepted only when the face is a validated portal to sector `0`.
- Portal polygon is non-degenerate.
- Portal plane normal is valid.
- Portal polygon lies close to both connected sector boundaries.
- Sector bounds contain or overlap portal bounds.
- Door-linked portals reference valid doors.
- Portal blocking uses explicit `portal -> blockingDoorIds` links. Door/portal bounds overlap is diagnostic unless the
  data is explicitly migrated into a validated link.
- For visibility traversal, only `Closed` mechanism state blocks a linked portal. `Open`, `Opening`, and `Closing` are
  visibility-open.
- Closed portal collision/visibility flags are consistent.
- Render faces and collision faces have valid sector ids.
- Actor/billboard initial positions resolve to valid sectors.
- Standalone/moving sectors are explicitly classified as mechanism geometry, sky/special geometry, or invalid. They are
  not automatically visible because they intersect the root camera frustum.
- Per-sector actor/decoration/sprite counts are recorded for diagnostics and compared against runtime memberships.

The validation output must include:

```text
sector id
portal face id
front/back sector ids
validation status
door/mechanism id if any
reason for rejection
```

## 10.2 Runtime Validation

Debug builds should assert/log:

- Actor lost sector membership.
- Portal traversal depth exceeded often.
- Invalid clipped frustum generated.
- Object culled despite debug force-visible mode.
- Closed door portal rendered unexpectedly.
- Collision query traversed suspiciously many sectors.
- Object has primary sector `0` or unknown sector without a recovery reason.
- Sector is render-visible without a visible sector instance path, except explicit root sector and explicit standalone
  mechanism geometry.
- Rendered decoration/actor/sprite count is nonzero for a sector that has no clipped-frustum intersection.
- Submitted object is outside every clipped frustum for its render memberships.

Runtime visibility logs must distinguish:

```text
objects loaded in a sector
objects eligible by sector mask
objects passing clipped-frustum/bounds culling
objects actually submitted
objects rejected by hidden state, missing frame, missing texture, sector, or frustum
```

## 10.3 Debug Views

Required debug tools:

```text
show current sector
show eye sector and foot sector separately
show visible sectors
show visible sector instances and portal paths
show portal polygons
show rejected portal faces with reasons
show open/closed portal state
show portal-clipped frustums
show actor sector membership
show actor render memberships
show decoration and sprite render memberships
show collision candidates
show sweep hits and normals
show per-object culling reason
show actor simulation tier
show raycast/LOS paths through sectors
```

Per-object culling reason example:

```text
Billboard 183 skipped:
    sector visible: yes
    visible sector instances: 2
    hidden by game state: no
    tested clipped frustums: 2
    bounds intersects frustum: no
    submitted: no
```

Once-per-second text diagnostics are useful during migration, but they must not be the only tool. They should include
actual submitted counts and enough identifiers to reproduce a bad object:

```text
[IndoorVisibility] map=... foot_sector=159 eye_sector=159 visible_instances=...
[IndoorSector] sector=194 visible_instances=1 path=159->192->194 geometry_submit=12/80
[IndoorObject] kind=decoration id=414 sector=194 memberships=[194] eligible=1 frustum=0 submitted=0 reason=outside_clipped_frustum
```

---

# 11. Acceptance Tests

## 11.1 Portal Visibility Tests

Test cases:

1. Camera in sector A, open portal to sector B: B visible.
2. Camera in sector A, closed door portal to B: B not visible.
3. Camera in sector A, opening door portal to B: B visible.
4. Camera in sector A, closing door portal to B: B visible.
5. Portal outside frustum: B not visible.
6. Portal partially in frustum: B visible with clipped frustum.
7. Sector visible through two portals: both visibility paths considered.
8. Portal cycle A -> B -> C -> A does not infinite loop.
9. Tiny portal below threshold does not cause unstable traversal.
10. Camera exactly near portal plane does not flicker badly.
11. Enclosed room with no open portal sees only its own sector.
12. Non-portal face with `roomBehindNumber == 0` does not create adjacency.
13. No-portal orphan sector in front of the camera but behind a wall is not visible.
14. Moving/elevator/standalone geometry renders only through explicit mechanism membership, not generic orphan fallback.
15. Runtime connected-sector cache matches editor connected-room output for the test room.

## 11.2 Object Culling Tests

1. Actor in visible sector and inside clipped frustum: submitted.
2. Actor in visible sector but outside clipped frustum: not submitted.
3. Actor behind closed door: not submitted.
4. Actor straddling portal: remains visible from both relevant sectors.
5. Large object crossing sector boundary: not incorrectly culled.
6. Billboard near edge of portal: conservative bounds prevent popping.
7. Torch/decor in visible sector but outside portal-clipped frustum is not submitted.
8. Decoration in a distant no-portal sector is not submitted even if inside the global camera frustum.
9. Submitted object counts match diagnostics after hidden-state, frame, texture, sector, and frustum filters.
10. Unknown-sector object logs a recovery/uncullable reason and does not silently become sector `0`.

## 11.3 Collision Tests

1. Player collides with wall in current sector.
2. Player moves through open portal into neighbor sector.
3. Player cannot move through closed door portal.
4. Player collision considers neighbor sector even if not camera-visible.
5. Capsule slides along wall without jitter.
6. Capsule does not pass through thin door/wall at high movement speed.
7. Floor snap works on slopes and stairs.
8. Ceiling collision prevents clipping upward.
9. Actor starting slightly inside wall recovers or logs deterministic failure.

## 11.4 Actor Simulation Tests

1. Actor in player sector gets full tick.
2. Actor visible through portal gets full or reduced tick according to policy.
3. Aggro actor behind player still updates even if not camera-visible.
4. Actor behind closed door sleeps/reduces unless scripted active.
5. Reduced-tick actor preserves timers and does not break combat logic.
6. Actor transitions sector through open portal correctly.

## 11.5 Multithreading Tests

1. Same frame produces same result across repeated runs.
2. Actor update results do not depend on worker scheduling.
3. Trigger events processed in stable order.
4. Actor overlap resolution deterministic.
5. No allocations in hot collision query loops after warm-up.
6. No global collision mutex in per-query path.

---

# 12. Performance Strategy

## 12.1 Indoor Rendering

Primary performance wins:

```text
sector/portal visibility
portal-clipped frustums
per-object culling
per-sector render BVH if needed
state/material batching after visibility collection
```

Rendering should avoid:

```text
submitting all sectors
submitting all objects in visible sectors
global frustum only for deep sectors
whole-map object scans in hot render paths
generic orphan-sector visibility fallbacks
```

Target performance shape:

```text
visibility traversal cost ~= visible portal count
static geometry submission ~= visible face/meshlet count after clipped-frustum culling
billboard/actor/decor submission ~= visible object memberships after clipped-frustum culling
hidden dungeon population should not materially affect render frame time
```

## 12.2 Indoor Collision

Primary performance wins:

```text
sector-filtered collision candidate gathering
swept AABB portal traversal
per-sector collision BVH
thread-local scratch
parallel actor/projectile queries
```

Collision should avoid:

```text
testing actor against entire dungeon mesh
allocating per query
global locks
using camera visibility for collision
```

## 12.3 Actor Simulation

Primary performance wins:

```text
simulation tiers
sector/distance/aggro-based full tick selection
reduced tick rates
sleeping/frozen far actors
parallel movement queries
```

Actor simulation should avoid:

```text
full AI and collision update for every monster every frame
making simulation depend only on camera visibility
physics-solver-driven monster movement
```

---

# 13. Suggested Implementation Plan

## Phase 0: OpenYAMM BLV Ground Truth and Migration

This phase is mandatory before replacing rendering or collision behavior. Its goal is to make current BLV-derived data
trustworthy enough for the architecture below.

- Build a validated sector/portal graph from current `IndoorMapData`.
- Use `IndoorSector::portalFaceIds` as the source of truth, matching the editor's "Connected Rooms" model.
- Accept graph edges only from validated portal faces.
- Remove any adjacency derived from arbitrary `sector.faceIds`.
- Canonicalize every valid `roomNumber` / `roomBehindNumber` portal into one bidirectional link.
- Cache each portal link into both connected sectors' portal lists.
- Cache each sector's connected-sector list from those bidirectional portal links.
- Cache explicit `portal -> blockingDoorIds` links from `MapDeltaDoor::faceIds` membership.
- Treat bounds-overlap door/portal matches as diagnostics unless migrated into explicit validated links.
- Use the simplified visibility blocker rule: `Closed` blocks; `Open`, `Opening`, and `Closing` traverse.
- Reject default/stale `roomBehindNumber == 0` links unless the face is a validated portal to sector `0`.
- Remove the generic orphan-sector visibility fallback from render visibility.
- Reclassify required standalone sectors as explicit mechanism/special render objects with bounds and memberships.
- Preserve current `IndoorMapData` fields as source/import data, but introduce runtime graph data with validation status.
- Add map-load diagnostics for rejected portal faces, invalid sector links, degenerate portal polygons, and suspicious
  high-population sectors.
- Add once-per-second migration diagnostics that distinguish loaded, sector-eligible, clipped-frustum-visible, and
  actually submitted geometry/decorations/actors/sprites.
- Add debug rendering for current sector, eye sector, validated portals, rejected portal candidates, and visible sector
  paths.
- Compare the validated graph and visible sector list against OpenEnroth behavior on representative indoor maps.
- Add regression tests for enclosed rooms, sector `0` pollution, orphan sectors, open portals, closed doors, and portal
  loops.

Phase 0 completion criteria:

- No enclosed room reports bogus adjacency to sector `0`.
- No no-portal sector becomes render-visible solely because it intersects the root camera frustum.
- Actor, decoration, and sprite diagnostics report actual submitted counts.
- Current render output is no worse than the pre-migration path on known test screenshots.
- The validated graph is the only source used by render visibility traversal.
- Runtime connected-sector diagnostics match the editor's connected-room output for validated portals.

## Phase 1: Data and Debug

- Define Sector, Portal, Door, CollisionFace, VisibleSectorInstance.
- Import/build sector graph.
- Validate portal connections.
- Debug draw sectors, portals, current camera sector.

## Phase 2: Runtime Portal Visibility

- Implement camera sector lookup.
- Implement portal traversal with clipped frustums.
- Render sector debug colors.
- Add closed/open portal state.
- Add cycle/depth protection.

## Phase 3: Per-Object Culling

- Add visible frustums by sector.
- Cull static faces/batches against clipped frustums.
- Cull actors/billboards against clipped frustums.
- Implement multi-sector render membership for large/portal-near objects.

## Phase 4: Collision Candidate Gathering

- Build per-sector collision BVH.
- Implement collision sector traversal using swept AABB and movement-open portals.
- Implement raycasts and capsule/cylinder sweeps.
- Preserve face/material/event metadata in hits.

## Phase 5: Character Movement

- Implement move-and-slide.
- Add ground snap, slope limits, step handling, ceiling checks.
- Add stuck recovery diagnostics.
- Add debug sweep drawing.

## Phase 6: Actor Simulation Tiers

- Compute full/reduced/sleeping sector sets.
- Assign actor tick tiers.
- Implement reduced tick accumulation.
- Ensure aggro/scripted actors remain active.

## Phase 7: Multithreading

- Build immutable collision snapshot.
- Parallelize actor movement jobs.
- Parallelize projectile and LOS batches.
- Deterministic apply phase.
- Add determinism tests.

## Phase 8: Hardening

- Test maps with loops, doors, secret passages, large halls, narrow corridors.
- Add debug culling reason view.
- Add stress tests with many actors and projectiles.
- Profile render/collision/AI separately.
- Tune thresholds conservatively to avoid artifacts.

---

# 14. Production Defaults

Recommended starting constants:

```cpp
constexpr int MaxPortalDepth = 16;
constexpr int MaxSlideIterations = 5;
constexpr float CollisionSkinWidth = 0.02f;
constexpr float MinMoveDistance = 0.0001f;
constexpr float PortalBoundsExpansion = 0.02f;
constexpr float ObjectBoundsExpansion = 0.03f;
constexpr float MaxWalkableSlopeDegrees = 45.0f;
constexpr float StepHeight = 0.35f;
constexpr float GroundSnapDistance = 0.25f;
constexpr float ReducedActorTickInterval = 0.25f;
```

These values must be tuned to the engine’s world units.

---

# 15. Key Design Rules

1. **Sector visibility is candidate visibility, not final object visibility.**
2. **Store visible sector instances with clipped frustums, not just visible sector ids.**
3. **Do not globally skip a sector just because it was already visited once.**
4. **Closed doors must consistently affect rendering, collision, AI, and sound according to separate policies.**
5. **Collision uses swept-volume reachability, not camera visibility.**
6. **Actors use game-controlled movement, not rigid-body physics.**
7. **Far actors should be tiered/reduced/slept by gameplay policy, not by physics engine magic.**
8. **Worker threads compute results; deterministic phases apply results.**
9. **Prefer conservative culling over visible popping.**
10. **Debug visualization and culling reasons are mandatory for production stability.**
11. **Only validated portal faces create sector graph edges.**
12. **Default or stale sector id `0` values are invalid until proven by validation.**
13. **Standalone/moving sectors require explicit special handling; no generic root-frustum orphan fallback.**
14. **Diagnostics must distinguish eligible, visible, and actually submitted objects.**

---

# 16. Final Architecture Summary

The indoor engine should be built around a shared sector/portal graph.

Rendering uses it as:

```text
camera frustum -> open visible portals -> clipped sector frustums -> per-object culling
```

Collision uses it as:

```text
swept shape -> movement-open portals -> sector collision BVHs -> narrowphase hits
```

Physics/movement uses it as:

```text
game velocity -> move-and-slide -> ground/ceiling/step resolution -> sector transfer
```

Actor simulation uses it as:

```text
player sector + visible/near/aggro sectors -> full/reduced/sleeping tick tiers
```

Sound uses it as:

```text
sound source sector -> sound-open portals -> attenuation and reachability
```

AI uses it as:

```text
movement-open portal graph -> path/reachability/awareness
```

This gives MM6–MM8-style indoor dungeons strong performance while keeping the system deterministic, debuggable, and resistant to hard-to-catch culling and collision edge cases.
