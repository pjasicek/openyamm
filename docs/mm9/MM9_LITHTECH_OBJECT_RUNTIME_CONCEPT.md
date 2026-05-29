# MM9 LithTech Object Runtime Concept

Status: design note for mapping MM9/LithTech object concepts into OpenYAMM without importing LithTech's engine
architecture.

## Objective

Document what a LithTech `LTObject` means, what parts of the LithTech object/update model are useful for MM9, and how
OpenYAMM should implement the same practical behavior using existing MM6-MM8 runtime boundaries.

The goal is to make MM9 object handling performant and future-proof while avoiding a broad, duplicated entity engine.

## Read First

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`: DAT parser authority and source-preservation constraints.
- `docs/mm9/MM9_MAP_RUNTIME_CLASSIFICATION.md`: which MM9 maps need DAT BSP/portal treatment.
- `docs/mm9/MM9_NATIVE_3D_ACTOR_IMPLEMENTATION_GOAL.md`: current native animated actor ownership split.
- `docs/mm9/MM9_LIGHT_LAYER_PRE_DATWORLD_GOAL.md`: example of source-preserving MM9 projection before full
  `DatWorld` rendering.
- `docs/mm9/MM9_SCRIPT_OBJECT_HANDLE_DIRECT_VS_ROUTED.md`: SCR/Lua object-handle direct-operation versus routed-message
  contract.
- `game/mm9/Mm9ObjectLayer.*`: current MM9 source-object projection.
- `game/mm9/Mm9SpawnLayer.*`: current MM9 spawn projection.
- `game/mm9/Mm9ScriptRuntime.*`: current MM9 script-facing object handles and object-local state.
- `game/gameplay/GameplayActorAiSystem.*` and `game/gameplay/GameplayActorService.*`: existing shared actor gameplay
  systems.

Local LithTech reference points:

- `mm9/lithtech/sdk/inc/ltbasedefs.h:2061`: object type enum.
- `mm9/lithtech/runtime/world/src/de_objects.h:124`: `LTObject` is the engine object base for objects in the BSP.
- `mm9/lithtech/runtime/server/src/serverobj.h:58`: `m_NextUpdate` scheduled update counter.
- `mm9/lithtech/runtime/server/src/s_object.cpp:295`: per-frame full object update.
- `mm9/lithtech/runtime/server/src/s_object.cpp:640`: active/inactive list movement.
- `mm9/lithtech/runtime/server/src/servermgr.cpp:880`: active-prefix object update scan.
- `mm9/lithtech/runtime/world/src/world_tree.cpp:138`: spatial box query with early empty-subtree rejection and
  duplicate callback suppression.

## LithTech Meaning Of Object

In LithTech, "object" is a broad engine runtime concept. It is not the same thing as an RPG actor, monster, NPC, or
decoration. An `LTObject` is the engine-side shell for a thing with transform, flags, type, world-tree participation,
server/client state, and an optional game class.

The gameplay meaning usually comes from the server-side game object/class, not from `LTObject` alone:

- `SObjData::m_pObject` links the engine object to the game class instance.
- `SObjData::m_pClass` identifies the authored class.
- `HOBJECT` is effectively an object handle to an `LTObject`.

LithTech object types relevant to MM9 mapping:

- `OT_MODEL`: model object. Map to actor, monster, NPC, animated prop, projectile, item, or model-backed interactive
  object depending on class and script data.
- `OT_WORLDMODEL`: world-model or brush-like object. Map to door, lift, platform, moving mechanism, breakable world
  chunk, or DAT world model instance.
- `OT_CONTAINER`: volume derived from world model. Map to water, damage volume, trigger volume, or environment region.
- `OT_LIGHT`: dynamic/authored light. Map to an MM9 light-layer record, with static/dynamic classification handled
  separately.
- `OT_SPRITE`: sprite/billboard. Map to FX, billboard, marker-like visual, or legacy fallback visual.
- `OT_NORMAL`: invisible logic object. Map to script controller, trigger helper, marker, or stateful nonvisual object.
- `OT_CAMERA`: camera object. Map to cutscene, debug, or runtime camera source if MM9 data requires it.
- `OT_PARTICLESYSTEM`, `OT_POLYGRID`, `OT_LINESYSTEM`, `OT_CANVAS`, `OT_VOLUMEEFFECT`: specialized
  client/render/effect objects. Treat as MM9-specific source classes until a runtime feature needs them.

Examples:

- A monster is normally an `OT_MODEL` plus AI/game-class data.
- An NPC is normally an `OT_MODEL` plus dialogue/script/game-class data.
- A stool or tree can be an `OT_MODEL` prop, but if it is baked into source world geometry it is not a separate actor.
- A door is usually closer to `OT_WORLDMODEL` or a mechanism/world model than to an actor.
- A trigger can be a container/world-model volume, an invisible normal object, or a script-facing authored object.

## OpenYAMM Design Position

Do not port the LithTech object manager. It is a whole-engine entity registry with server/client networking assumptions,
intrusive object banks, broad object-type ownership, and LithTech-specific render/physics hooks.

OpenYAMM should keep:

- Shared MM6-MM8 gameplay systems for actor AI, combat, party interaction, services, projectiles, items, dialogue, and
  save/load semantics.
- MM9-specific source projection in `game/mm9/*`.
- DAT world geometry, BSP/portal, collision, picking, and visibility as world-runtime concerns, not as general gameplay
  replacements.
- Native MM9 animated actor visuals as the MM9 visual adapter over the generic animated-model renderer.

The right mapping is:

- MM9 authored objects become source-preserving `game/mm9` projections first.
- Projection classifies objects into runtime capabilities.
- Existing OpenYAMM systems consume those capabilities through narrow hooks.
- Full DAT world integration later replaces only the geometry/query backend, not the gameplay model.

## Runtime Capability Buckets

Classify MM9 objects by behavior instead of forcing every object into one base runtime class:

- `sourceOnly`: preserved for editor, diagnostics, regeneration, and future support.
- `renderableModel`: visible model-backed object using native MM9 animated/static model rendering.
- `actorLike`: object needs actor state, AI, combat, health, target, faction, or animation state.
- `interactive`: object can be selected, clicked, used, talked to, opened, or scripted.
- `collidable`: object participates in actor/player/projectile collision.
- `rayHit`: object participates in picking, line-of-sight, spell targeting, or use tracing.
- `triggerVolume`: object fires enter/exit/use/overlap behavior through script or event routing.
- `worldMechanism`: door, platform, lift, mover, breakable world model, portal mechanism, or other world-geometry
  behavior.
- `scheduledScript`: object needs time-based script callbacks but not per-frame actor AI.
- `lightSource`: object contributes to MM9 lighting data.
- `soundSource`: object contributes positional or ambient audio behavior.

These buckets should be represented as explicit flags or cached derived metadata in MM9 projection/runtime state. A
single object may have several capabilities.

## What To Use From LithTech

Use these patterns, implemented in OpenYAMM style:

### Active And Inactive Partition

LithTech moves inactive objects to the tail of its object list and stops scanning at the first inactive object during
normal updates. OpenYAMM should use the same idea without intrusive lists:

- Maintain `activeActorIndices` or `activeObjectIndices` per loaded map.
- Remove or swap dormant objects out of hot update lists when their state changes.
- Keep source order and stable source ids separately from hot runtime order.
- Do not scan all MM9 objects every frame to find the small subset that can update.

### Scheduled Updates

LithTech only calls `OnUpdate` after `m_NextUpdate` counts down. The OpenYAMM equivalent should be a scheduling policy,
not a new global object callback model:

- Add per-object next-update time only for MM9 objects that need periodic behavior.
- Use a heap, bucketed time wheel, or active scheduled list if object counts justify it.
- Let shared systems such as `GameplayActorAiSystem` own behavior decisions.
- Use scheduling to decide when an actor/script object is eligible to run, not to hide gameplay logic inside an engine
  object base class.

### Spatial Query Caches

LithTech uses a world tree for object queries and avoids visiting empty subtrees. OpenYAMM should build map-local query
structures for MM9 runtime objects:

- `collidableObjectSpatialIndex`
- `rayHitObjectSpatialIndex`
- `triggerVolumeSpatialIndex`
- `interactiveObjectSpatialIndex`
- later, `staticLightSpatialIndex`

These should be updated on spawn/despawn/move/state changes, not rebuilt every frame.

### Optimized-Out Objects

LithTech can remove objects from world-tree participation when flags prove they are not visible, solid, touchable,
ray-hittable, container-like, force-updated, or carrying special effects.

OpenYAMM should express the same idea through capability flags:

- Source-only objects stay out of render, collision, picking, trigger, and AI caches.
- Hidden noninteractive objects leave render and ray-hit caches.
- Nonsolid objects leave collision caches.
- Dormant scripted objects leave scheduled update lists until a trigger, script, save restore, or world event activates
  them.

### Staggered Expensive Work

LithTech-era game code often schedules AI updates instead of recomputing everything every server frame. OpenYAMM should
do the same for MM9-heavy behavior:

- Bucket perception checks.
- Bucket pathfinding requests.
- Avoid recomputing nearest hostile, line of sight, or path every frame for every actor.
- Use deterministic staggering so save/load and tests remain stable.

## What Not To Use From LithTech

Do not import these as OpenYAMM architecture:

- `LTObject` as a universal base class.
- `SObjData` and `BaseClass`/`ClassDef` ownership as runtime object identity.
- Intrusive linked lists and object banks as the default container strategy.
- Server/client replication, change flags, net flags, and client-visible object filtering.
- LithTech `HOBJECT` pointer-handle semantics.
- LithTech's 16-bit object-id limit.
- A global `OnUpdate` callback on every runtime object.
- A global 30 Hz or 60 Hz actor tick. LithTech defaults `ServerFPS` to 30 when lock-step server FPS is used, but the
  object update logic is not a hard 60 Hz rule.
- Direct LithTech flag names such as `FLAG_OPTIMIZEMASK` in shared OpenYAMM APIs.

Those details solve LithTech's engine shape. They would bloat OpenYAMM and create a second runtime model beside the
existing MM6-MM8 systems.

## OpenYAMM Implementation Shape

### MM9 Source Projection

Extend the existing `Mm9ObjectLayer` and related MM9 layers as source-preserving projections:

- Preserve source object index, class, name, transform, bounds, raw properties, and provenance.
- Add derived capability flags.
- Add stable semantic ids such as `mm9:<mapId>:object:<sourceIndex>`.
- Preserve LithTech/source class names for script and diagnostics.
- Keep missing/unknown properties visible through diagnostics or raw property preservation.

This projection can be built before full `DatWorld` rendering exists.

### MM9 Runtime Instance Layer

For loaded maps, create a thin MM9 runtime instance layer that owns mutable state not appropriate for source projection:

- alive/removed/hidden state;
- current transform and velocity where MM9 scripts can mutate them;
- current AI/script state;
- current target/friend/enemy links;
- object-local numeric/string properties;
- scheduled update metadata;
- cache membership flags;
- stable handle to source projection and save/load state.

This should live in `game/mm9/*` and be consumed by existing world runtimes through narrow interfaces.

### Shared Gameplay Integration

Use existing shared gameplay code where behavior is genuinely gameplay:

- Actor AI and combat decisions should flow through `GameplayActorAiSystem` or deliberately shared extensions.
- Dialogue, services, qbits, inventory, rewards, and party-visible state should use existing shared systems.
- Turn-based/realtime update cadence should respect existing MM6-MM8 semantics.
- MM9-specific script commands can adapt to shared systems through `Mm9ScriptRuntime`, but should not create duplicate
  gameplay backends.

### World Runtime Integration

Use world-specific code where the behavior depends on DAT geometry:

- DAT BSP/portal visibility.
- Collision against DAT world models.
- Door/platform/world-model movement.
- Floor resolution and movement integration.
- Ray casts, line of sight, and picking against DAT geometry.
- Trigger volume overlap.
- Spatial indices for MM9 object query acceleration.

This keeps MM9's world representation from leaking into general engine gameplay.

## Performance Contract

The MM9 object runtime should avoid these hot-path costs:

- no full object scan for every frame update;
- no full object scan for every click/raycast;
- no full actor scan for every AI perception query once a spatial index exists;
- no per-frame rebuild of render/collision/interaction lists;
- no per-frame parsing or string classification of source properties;
- no per-frame model/skin/sidecar resolution;
- no per-frame recalculation of static bounds unless the object moved or changed state.

Expected cached views for a loaded MM9 map:

- `activeActorIndices`
- `scheduledObjectQueue` or equivalent bucketed scheduler
- `renderableObjectIndices`
- `collidableObjectIndex`
- `rayHitObjectIndex`
- `interactiveObjectIndex`
- `triggerVolumeIndex`
- `worldMechanismIndices`
- `staticLightIndex` once DAT rendering consumes static object lights

Cache updates should be event-driven:

- source map load;
- spawn/despawn/remove;
- transform change;
- visibility/solid/ray-hit/trigger flag change;
- script activation/deactivation;
- save/load restore;
- world mechanism state change.

## Avoiding Future Dead Ends

Keep these constraints in the first implementation:

- Preserve raw source fields even when a derived capability is understood.
- Keep source identity stable even if hot runtime arrays reorder for performance.
- Separate immutable source projection from mutable runtime state.
- Separate object capabilities from gameplay class inheritance.
- Store broad categories as flags/enums, not as string checks in frame code.
- Make spatial/cache membership explicit and testable.
- Keep MM9 DAT geometry hooks behind world-runtime interfaces so portal/BSP support can replace the temporary ODM-like
  path later.
- Do not force all MM9 objects into actor state. Most objects are not actors.
- Do not force all MM9 objects into render state. Some objects are invisible logic or trigger volumes.
- Do not make the generic engine know LithTech class names.

## Incremental Plan Before Full DatWorld

These pieces can be done now without a complete in-game `DatWorld` renderer:

- Expand `Mm9ObjectLayer` source projection with raw property preservation and derived capability flags.
- Add stable MM9 object handles and source ids consistently across object, spawn, dialogue, script, and visual paths.
- Add classification tests for representative MM9 classes:
  - actor/NPC/monster model object;
  - visible prop;
  - invisible script controller;
  - trigger volume;
  - light;
  - sound source;
  - door/mechanism/world-model-like object.
- Add a renderer-neutral MM9 runtime object state container.
- Add cache-membership bookkeeping with tests, even if the first cache implementation is a vector.
- Add scheduled-update metadata and deterministic bucket assignment for script/AI candidates.
- Route script-facing object position, visibility, target, stat, and remove/spawn operations through the runtime state
  container instead of ad hoc maps where practical.

Defer until real DAT world integration:

- DAT BSP/portal visibility object insertion.
- DAT world-model movement and collision.
- true spatial index against DAT geometry and object bounds.
- object vs world collision.
- trigger overlap against player/party/actors using DAT movement.
- static-light spatial index consumed by the MM9 DAT renderer.

## Done Criteria

This design is satisfied when:

- MM9 object source data is preserved and classified without needing full `DatWorld`.
- Runtime mutable object state is separated from immutable source projection.
- Actor-like MM9 objects can use shared gameplay systems without forcing every object to be an actor.
- Non-actor objects can be interactive, collidable, scriptable, or source-only without creating separate engine-wide
  inheritance.
- Hot update, render, collision, pick, trigger, and script paths consume preclassified/cached views.
- No broad LithTech object manager, networking model, or generic engine bloat is introduced.
