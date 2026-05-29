# Runtime Rendering And Physics Optimization Plan

This document captures the read-only optimization audit for indoor and outdoor runtime paths. It is intentionally
actionable: each item names the likely payoff, touched files, proposed implementation shape, and validation work.

No profiling results are attached yet. Treat the priorities below as code-inspection priorities and verify them with
timing counters or profiler captures before doing larger rewrites.

## Priority Summary

| Priority | Area | Expected payoff | Risk | First implementation target |
| --- | --- | --- | --- | --- |
| P0 | Outdoor actor movement colliders | High CPU reduction on actor-heavy maps | Low/medium | Build active actor collider list once per actor step |
| P0 | Outdoor actor/background AI cadence | High CPU reduction on actor-heavy maps | Medium | Keep nearby active actors at 128 Hz, throttle background actors |
| P0 | Outdoor actor/decor/projectile broadphase | High CPU reduction on actor/projectile-heavy maps | Medium | Reuse one actor grid for movement and projectiles |
| P1 | Indoor render sector culling | High GPU/CPU submit reduction indoors | Medium | Filter textured geometry by visible sector mask |
| P1 | Indoor actor update sector cadence | High CPU reduction in large dungeons | Medium | Current/adjacent sectors full rate, distant sectors lower rate |
| P1 | Outdoor billboard batching/culling | Medium/high render submit reduction | Medium | Batch non-hovered same-texture billboard runs |
| P1 | Outdoor runtime BModel mechanism path | Medium CPU/render reduction | Medium | Cache override texture lookup and transient vertex data |
| P2 | HUD/dialogue batching | Medium submit reduction in UI-heavy frames | Low/medium | Batch same-texture HUD quads |
| P2 | Outdoor terrain/BModel chunk culling | Unknown until profiling | High | Only after GPU profiling shows terrain/BModel bottleneck |
| P2 | Physics multithreading | Unknown until data is made immutable | High | Defer until broadphase and cadence fixes land |

## Baseline Instrumentation

- [ ] Add or reuse timing counters for actor update phases:
  - active actor selection
  - AI fact collection
  - gameplay AI update
  - movement integration
  - projectile update
  - world item update
- [ ] Add render counters per frame:
  - terrain submits
  - BModel submits
  - runtime mechanism BModel submits
  - billboard draw items and submits by category
  - HUD textured quad submits
- [ ] Capture representative scenes:
  - outdoor actor-heavy map
  - outdoor projectile-heavy combat
  - outdoor decoration/sprite-heavy town
  - indoor multi-sector dungeon with closed and open portals
  - HUD/dialogue-heavy interaction
- [ ] Compare before/after by frame time, submit count, actor update time, and worst-frame spikes.

## Threading Status

The collision/physics simulation path does not appear to use multiple CPU cores today. The only clear runtime threading
found in the audited paths is outdoor sprite preload decoding:

- `game/outdoor/OutdoorBillboardRenderer.cpp:89` chooses worker count from `std::thread::hardware_concurrency()`.
- `game/outdoor/OutdoorBillboardRenderer.cpp:1621` uses `std::async` to decode pending sprite preload requests.

Do not start by threading physics. Several current structures mutate internal visit marks during broadphase collection,
and actor/world state is updated in-place during fixed steps. Threading this safely would require snapshot inputs,
per-worker scratch buffers, deterministic merge order, and careful save/replay behavior.

Action:

- [ ] First reduce unnecessary work with broadphase, culling, batching, and lower cadence for distant actors.
- [ ] If physics remains a bottleneck, isolate immutable per-step input snapshots and per-thread scratch storage.
- [ ] Make broadphase candidate queries thread-safe before parallelizing them.
- [ ] Keep deterministic application of movement, damage, projectiles, and event side effects on one merge path.

## Existing Broadphase And Culling Inventory

Already present:

- Outdoor movement has a BModel face grid in `game/outdoor/OutdoorMovementController.cpp:2600`.
- Outdoor movement has a sprite-object collider grid in `game/outdoor/OutdoorMovementController.cpp:2841`.
- Outdoor world runtime has a separate BModel face grid for projectile/floor queries in
  `game/outdoor/OutdoorWorldRuntime.cpp:8901`.
- Outdoor decoration billboards have a render/interaction spatial index in
  `game/outdoor/OutdoorInteractionController.cpp:3266`.
- Indoor rendering can build a portal-visible sector mask in `game/indoor/IndoorRenderer.cpp:1958`.
- Indoor actor rendering already filters actors through visible sector mask in
  `game/indoor/IndoorRenderer.cpp:2761`.
- Indoor picking/inspection paths use visible sector masks in `game/indoor/IndoorRenderer.cpp:3134` and
  `game/indoor/IndoorRenderer.cpp:3430`.

Not yet covered enough:

- Outdoor actor movement collisions scan actor colliders linearly.
- Outdoor decoration collisions scan decoration colliders linearly.
- Outdoor projectile actor collision scans all actors.
- Indoor textured geometry render still iterates all textured batches in the main path.
- Indoor decoration, actor, and sprite-object billboard render is currently called with an empty sector mask in the main
  world render path.
- Outdoor static sprite-object billboard rendering iterates all sprite-object billboards without the same distance/grid
  candidate filtering used by decoration billboard rendering.

## P0: Outdoor Actor Movement Collider Rebuild

Problem:

- `buildNearbyActorMovementColliders()` builds a vector of active actor colliders from all map actors.
- It is called inside per-actor movement paths, so the same active-collider list can be rebuilt many times during one
  fixed actor update.

Key files:

- `game/outdoor/OutdoorWorldRuntime.cpp:2085`
- `game/outdoor/OutdoorWorldRuntime.cpp:7694`
- `game/outdoor/OutdoorWorldRuntime.cpp:7906`
- `game/outdoor/OutdoorMovementController.cpp:1005`

Action:

- [ ] Build the active actor collider list once per `updateMapActors()` fixed step after active actor selection.
- [ ] Pass the list into `applyOutdoorActorPhysicsStep()` and `applyOutdoorActorMovementIntegration()`, or store it in
  a scoped per-step cache on `OutdoorWorldRuntime`.
- [ ] Avoid rebuilding the vector unless active mask, actor positions, or actor dimensions change.
- [ ] Preserve the ignored-actor behavior for the actor currently being resolved.

Validation:

- [ ] Add a regression test or debug counter proving collider list builds once per fixed step, not once per actor.
- [ ] Run outdoor combat/headless scenario with multiple active actors.
- [ ] Confirm actor/actor collision and crowding behavior remains unchanged.

## P0: Outdoor Actor And Background AI Cadence

Problem:

- `updateMapActors()` runs actor logic at `1 / 128` seconds.
- Each fixed step scans all map actors to select active actors.
- `collectOutdoorActorAiFrameFacts()` allocates an `N * N` LOS cache and collects facts for active and background actors
  every fixed step.

Key files:

- `game/outdoor/OutdoorWorldRuntime.cpp:6653`
- `game/outdoor/OutdoorWorldRuntime.cpp:6689`
- `game/outdoor/OutdoorWorldRuntime.cpp:6705`
- `game/outdoor/OutdoorWorldRuntime.cpp:8171`

Action:

- [ ] Keep current nearby active actor behavior at 128 Hz.
- [ ] Update background/out-of-range actors at a lower cadence, for example 8 Hz or 16 Hz.
- [ ] Reuse active actor selection for several fixed substeps when the party has not moved far enough to change the
  result materially.
- [ ] Replace the per-step `N * N` LOS cache allocation with a reused cache or sparse pair cache.
- [ ] Only compute actor-vs-actor LOS pairs that AI actually asks for.

Validation:

- [ ] Confirm distant actors still resume correctly when the party approaches.
- [ ] Confirm timed AI states, recovery, animation time, hostility, and death cleanup do not stall incorrectly.
- [ ] Test maps with many hostile actors and maps with mostly distant passive actors.

## P0: Outdoor Actor, Decoration, And Projectile Broadphase

Problem:

- Outdoor BModel face and sprite-object collision have grids, but actor and decoration cylinder checks are linear.
- Projectile actor collision loops every map actor per projectile step.

Key files:

- `game/outdoor/OutdoorMovementController.cpp:897`
- `game/outdoor/OutdoorMovementController.cpp:1005`
- `game/outdoor/OutdoorWorldRuntime.cpp:9435`
- `game/outdoor/OutdoorWorldRuntime.cpp:9496`
- `game/outdoor/OutdoorWorldRuntime.cpp:10079`

Action:

- [ ] Add a static decoration collision grid for outdoor decoration cylinders.
- [ ] Add a dynamic actor collision grid built once per actor/projectile step.
- [ ] Query actor grid for movement collision candidates.
- [ ] Query actor grid for projectile actor collision candidates.
- [ ] Keep BModel face collision on the existing face grid.
- [ ] Consider sharing grid cell size with existing face/sprite grids unless profiling shows too many candidates.

Validation:

- [ ] Verify collision with large decorations, small decorations, and actors at cell boundaries.
- [ ] Verify projectiles still hit actors when crossing multiple cells in one step.
- [ ] Verify ignored actor collider behavior remains correct.

## P1: Indoor Render Sector Culling

Problem:

- Indoor renderer builds and caches a portal-visible sector mask.
- Main textured geometry submission still iterates `m_texturedBatches`.
- Lighting supports a visible sector mask, but the render path passes `nullptr`.
- Main billboard rendering currently passes an empty sector mask because of moving/elevator concerns.

Key files:

- `game/indoor/IndoorRenderer.cpp:1958`
- `game/indoor/IndoorRenderer.cpp:2392`
- `game/indoor/IndoorRenderer.cpp:2516`
- `game/indoor/IndoorRenderer.cpp:2571`
- `game/indoor/IndoorRenderer.cpp:4872`
- `game/indoor/IndoorRenderer.cpp:5163`
- `game/indoor/IndoorRenderer.cpp:5641`

Action:

- [ ] Apply visible sector mask to textured geometry batches.
- [ ] Keep a conservative fallback for batches whose sector ownership is ambiguous.
- [ ] Pass the visible sector mask into indoor lighting where supported.
- [ ] For billboards, filter by current sector mask for static decorations and sprite objects first.
- [ ] Handle moving/elevator billboards by checking both current sector and last/next known sector, or by marking only
  those objects as uncullable.
- [ ] Add debug toggle/counter to compare total indoor batches vs visible batches.

Validation:

- [ ] Test doors, windows, elevators, and portals where sectors become visible/invisible.
- [ ] Test decorations or actors crossing sector boundaries.
- [ ] Confirm no interaction/picking regression for hidden sectors.

## P1: Indoor Actor Update Sector Cadence

Problem:

- Indoor actor update also uses a 128 Hz fixed step.
- Active actor selection uses sectors and portal adjacency, but background actor facts are still collected in the same
  frame facts path.

Key files:

- `game/indoor/IndoorWorldRuntime.cpp:62`
- `game/indoor/IndoorWorldRuntime.cpp:3572`
- `game/indoor/IndoorWorldRuntime.cpp:3654`
- `game/indoor/IndoorWorldRuntime.cpp:3689`
- `game/indoor/IndoorWorldRuntime.cpp:6654`

Action:

- [ ] Keep current sector and adjacent/portal-visible actors at full rate.
- [ ] Move non-current/non-adjacent actors to lower cadence.
- [ ] Use sector graph distance or portal-visible set as the first pass, then distance as a tie-breaker.
- [ ] Ensure actors that can affect the party through projectiles, sounds, scripted triggers, or open portals remain
  eligible for full-rate updates.

Validation:

- [ ] Test dungeons with enemies behind doors and around portal-connected rooms.
- [ ] Test actors pathing through portals.
- [ ] Test combat state transitions when party retreats across sectors.

## P1: Outdoor Billboard Batching And Culling

Problem:

- Decoration billboard rendering has candidate collection and groups by texture.
- Runtime projectile billboard rendering groups by texture.
- Actor billboards, runtime world items, and static sprite-object billboards still submit one quad at a time.
- Static sprite-object billboard rendering appears to iterate all sprite-object billboards without distance/near-plane
  rejection.

Key files:

- `game/outdoor/OutdoorBillboardRenderer.cpp:1955`
- `game/outdoor/OutdoorBillboardRenderer.cpp:2054`
- `game/outdoor/OutdoorBillboardRenderer.cpp:2194`
- `game/outdoor/OutdoorBillboardRenderer.cpp:2655`
- `game/outdoor/OutdoorBillboardRenderer.cpp:2886`
- `game/outdoor/OutdoorBillboardRenderer.cpp:2974`
- `game/outdoor/OutdoorBillboardRenderer.cpp:3186`
- `game/outdoor/OutdoorBillboardRenderer.cpp:3423`
- `game/outdoor/OutdoorBillboardRenderer.cpp:3672`
- `game/outdoor/OutdoorBillboardRenderer.cpp:3718`

Action:

- [ ] Add distance and near-plane filtering to static sprite-object billboards.
- [ ] Batch non-hovered actor billboards by texture in sorted runs.
- [ ] Batch non-hovered world item billboards by texture in sorted runs.
- [ ] Batch static sprite-object billboards by texture.
- [ ] Keep hovered outline draws separate unless outline state can be batched safely.
- [ ] Preserve alpha ordering enough to avoid visible sprite sorting regressions. If strict ordering prevents global
  texture sorting, batch only consecutive same-texture runs after depth sort.

Validation:

- [ ] Compare submit counts in actor-heavy and item-heavy outdoor scenes.
- [ ] Verify hover outlines still render above the selected actor/item.
- [ ] Check transparent sprite ordering in dense scenes.

## P1: Outdoor Runtime BModel Mechanism Rendering

Problem:

- Static/resolved BModel groups are cached by revision, but runtime mechanism BModels are processed per batch each
  frame.
- The runtime path does texture override lookup, linear search through animation handles, copies batch vertices, mutates
  copied vertices, uploads transient vertices, and submits per batch.

Key files:

- `game/outdoor/OutdoorRenderer.cpp:2735`
- `game/outdoor/OutdoorRenderer.cpp:2740`
- `game/outdoor/OutdoorRenderer.cpp:2791`
- `game/outdoor/OutdoorRenderer.cpp:2816`
- `game/outdoor/OutdoorRenderer.cpp:2913`
- `game/outdoor/OutdoorRenderer.cpp:2929`

Action:

- [ ] Add a texture-name-to-animation-index map for BModel texture override lookup.
- [ ] Cache per-mechanism resolved vertex data by visual revision and mechanism offset revision.
- [ ] Avoid copying `batch.vertices` every frame when offset/flow/secret pulse did not change.
- [ ] Add coarse BModel or face bounds culling before doing override lookup and transient upload.
- [ ] Consider grouping mechanism batches by texture/animation when offsets and state allow it.

Validation:

- [ ] Test moving platforms, doors, elevators, texture overrides, secret faces, water/lava flow, and hidden facets.
- [ ] Verify event-driven visual changes invalidate the cache correctly.

## P2: Outdoor Terrain And Static BModel Chunk Culling

Problem:

- Outdoor textured terrain submits the full terrain vertex buffer every frame.
- Resolved BModel draw groups are grouped globally by texture/animation, so individual BModels cannot be culled at
  submit time without changing grouping.

Key files:

- `game/outdoor/OutdoorRenderer.cpp:2666`
- `game/outdoor/OutdoorRenderer.cpp:2740`

Action:

- [ ] Profile GPU vertex/fill cost before starting this.
- [ ] If terrain is a bottleneck, split terrain into chunks and frustum/distance cull chunks.
- [ ] If BModels are a bottleneck, build draw groups by texture plus spatial chunk/BModel rather than global texture
  only.
- [ ] Keep chunk size large enough to avoid replacing one big submit with too many small submits.

Validation:

- [ ] Compare draw calls, vertex counts, and GPU frame time.
- [ ] Test high viewpoints where most terrain is visible.
- [ ] Test fog/view-distance transitions.

## P2: HUD And Dialogue Quad Batching

Problem:

- Some UI paths already batch specialized data, but many HUD/dialogue paths submit textured quads one at a time.
- The crosshair alone submits multiple small quads.
- Dialogue and party overlay paths contain many direct `submitHudTexturedQuad()` calls.

Key files:

- `game/ui/GameplayHudOverlaySupport.cpp:1236`
- `game/ui/GameplayDialogueRenderer.cpp:1164`
- `game/ui/GameplayDialogueRenderer.cpp:1263`
- `game/ui/GameplayDialogueRenderer.cpp:2140`
- `game/ui/GameplayPartyOverlayRenderer.cpp:534`
- `game/ui/GameplayPartyOverlayRenderer.cpp:2132`

Action:

- [ ] Add or reuse a small HUD quad batcher keyed by texture handle and render state.
- [ ] Batch same-texture static HUD pieces, crosshair strokes, and repeated overlay elements.
- [ ] Keep text rendering separate unless the font path already supports batching by atlas.
- [ ] Avoid batching across ordering boundaries where UI layering matters.

Validation:

- [ ] Compare HUD submit counts with normal gameplay HUD, dialogue, inventory, and party overlay screens.
- [ ] Verify layering, hover states, and inspect overlays.

## Deferred: Physics Multithreading

Do not implement this until the P0/P1 single-threaded work is measured. Threading is still viable later, but it should be
done after the data flow is made easier to reason about.

Action:

- [ ] Convert broadphase queries to thread-safe read-only queries with per-thread scratch buffers.
- [ ] Snapshot actor/projectile/world collision state at the start of a fixed step.
- [ ] Run independent candidate/fact collection in parallel.
- [ ] Merge results deterministically on the main simulation path.
- [ ] Keep event side effects, inventory/loot, damage application, and save-state mutation on deterministic ownership.

Validation:

- [ ] Add deterministic replay/headless scenario coverage before enabling threaded simulation.
- [ ] Run the same scenario with 1, 2, 4, and many worker threads and compare final state hashes.

## Suggested Implementation Order

1. Add timing counters and submit counters.
2. Build outdoor active actor colliders once per fixed actor step.
3. Add outdoor actor grid and reuse it for movement and projectile actor collision.
4. Lower cadence for outdoor background actors.
5. Apply indoor sector mask to textured geometry and static billboards.
6. Lower cadence for indoor distant/non-adjacent actors.
7. Batch outdoor actor/world-item/static-sprite billboards.
8. Cache outdoor runtime BModel mechanism rendering work.
9. Batch HUD/dialogue quads.
10. Re-profile before considering terrain chunking or physics multithreading.

