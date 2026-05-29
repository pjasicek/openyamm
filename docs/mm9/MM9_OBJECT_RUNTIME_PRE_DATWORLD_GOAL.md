# MM9 Object Runtime Pre-DatWorld Goal

Status: implementation goal for the MM9 object/script runtime slice that can be completed before a real in-game
`DatLevelWorld` backend owns DAT geometry, visibility, collision, and moving world models.

## Objective

Implement the MM9 runtime object layer needed by generated Lua scripts and native MM9 actor/object integration without
waiting for full DAT world rendering/collision.

This goal should preserve LithTech-style MM9 object semantics:

- script object handles are generic opaque handles;
- direct generic operations mutate/query runtime object state;
- capability operations route through services;
- `Trigger` and callback events route through a target object message/event bus;
- source object identity and raw properties remain preserved for later DAT backend integration.

This goal must not introduce a universal OpenYAMM `LTObject` base class or move MM6-MM8 actor/runtime behavior into an
MM9-specific object bus.

## Read First

- `docs/mm9/MM9_SCRIPT_OBJECT_HANDLE_DIRECT_VS_ROUTED.md`: direct generic versus routed object operation contract.
- `docs/mm9/MM9_LITHTECH_OBJECT_RUNTIME_CONCEPT.md`: LithTech object concept and OpenYAMM mapping.
- `docs/mm9/MM9_READABLE_LUA_RUNTIME_API_PLAN.md`: desired generated Lua shape and object proxy direction.
- `docs/mm9/MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md`: current command coverage, counts, and runtime status.
- `docs/mm9/MM9_NATIVE_3D_ACTOR_IMPLEMENTATION_GOAL.md`: native MM9 actor visual ownership split.
- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`: DAT parser/source-preservation authority.
- `game/mm9/Mm9ObjectLayer.*`: current source-object projection.
- `game/mm9/Mm9SpawnLayer.*`: current source spawn projection.
- `game/mm9/Mm9ScriptRuntime.*`: current generated Lua runtime and object-state maps.
- `game/mm9/Mm9DialogueRuntime.*` and `game/mm9/Mm9DialoguePackage.*`: generated package/object binding context.

## Scope

Build the runtime contract and testable object/script layer now:

- stable MM9 object handles;
- object registry for loaded/generated MM9 object bindings;
- runtime mutable object state;
- direct generic object operations;
- object proxy API for Lua;
- message bus for `AddTrigger`, `RemoveTrigger`, and `Trigger`;
- callback registration and dispatch storage;
- request queues for movement, animation, audio, FX, and presentation;
- capability classification and cache-membership metadata;
- save/load for mutable state needed across callbacks and map reloads;
- focused tests proving handle routing and state persistence.

This should extend the current `game/mm9` runtime pieces instead of replacing them. In particular,
`Mm9ScriptRuntimeState`, `Mm9ObjectLayer`, `Mm9ScriptedObjectRuntime`, `Mm9InteractionRouting`, and
`Mm9AnimatedActorBinding` already own useful slices of the object/runtime story.

Do not implement real DAT geometry services in this goal.

## Architecture

Keep implementation in `game/mm9/*` unless a narrow shared runtime hook already exists.

Logical components:

These names describe ownership boundaries, not mandatory classes. Do not add forwarding/adaptor layers whose only
purpose is to rename existing `Mm9ScriptRuntime` state. Extract helpers only when that makes tests or ownership clearer.

- `Mm9ObjectHandle`
  - stable handle parser/formatter;
  - `mm9:<mapId>:object:<sourceIndex>`;
  - `mm9:player`;
  - synthetic handles such as spawned objects and sound handles where already used.
- `Mm9ObjectRegistry`
  - handle to source binding;
  - lookup by map id/source object index;
  - lookup by authored name and class/name aliases;
  - lookup by RUDE id where generated bindings provide it;
  - case-insensitive lookup where MM9 scripts rely on it.
  - Initial implementation can be indexed views over `Mm9DialoguePackage::objectBindings` and `Mm9ObjectLayer`.
- `Mm9RuntimeObjectState`
  - current transform/facing/velocity;
  - object flags and active/removed/hidden/alive state;
  - numeric and string property bags;
  - stats;
  - target handle;
  - relation tokens;
  - object links;
  - script override;
  - cache/capability membership bits.
  - Prefer consolidating `Mm9ScriptRuntimeState` maps over creating a parallel state store. Member vectors such as
    `m_audioRequests`, `m_animationRequests`, and `m_movementRequests` must either become read views over saved state or
    be kept in strict sync on load, restore, and request mutation.
- `Mm9ObjectMessageBus`
  - per-object message registrations from `AddTrigger`;
  - `RemoveTrigger`;
  - `Trigger` dispatch by target handle/name;
  - owner-context switch to the target object;
  - recursion/depth guard;
  - dispatch records for diagnostics and unresolved backend work.
  - This can initially remain inside `Mm9ScriptRuntime`; the important behavior is target-object routing, not a new
    bus class.
- `Mm9ObjectCallbackRegistry`
  - `OnDamage`, `OnDeath`, `OnTouchNotify`, `OnFoundTarget`, `OnLostTarget`, `OnAlert`, model-key, movement, audio, and
    numbered callback registration;
  - dispatch helpers that later DAT/actor/model/audio systems can call.
- `Mm9ObjectProxy` Lua surface
  - `ctx:object`;
  - `ctx:self`;
  - `ctx:player`;
  - `ctx:paramObject`;
  - object methods that call the runtime instead of owning state in Lua.

If the existing `Mm9ScriptRuntime` already owns part of this state, this goal may refactor only as much as needed to
make ownership explicit and testable. Avoid a large rewrite for naming purity.

LithTech uses `BaseClass` plus aggregates for shared behavior. The OpenYAMM analogue should be small capability/state
registries in `game/mm9`, not inheritance from a generic `LTObject` clone.

## Direct Generic Operations

Implement or consolidate these through the registry/runtime state:

- `GetObjectHandle`
- `GetObjectHandleByRUDEID`
- `GetMyHandle`
- `GetPlayerHandle`
- `GetObjectName`
- `GetClassName`
- `IsClass`
- `IsPlayer`
- `GetPOS`
- `SetPos`
- `GetFaceDir`
- `FaceDir`
- `SetFlag`
- `ClearFlag`
- `IsVisible`
- `IsObjectActive`
- `RemoveObject`
- `GetStat`
- `SetStat`
- `GetStatStr`
- `SetPropNumber`
- `SetPropString`
- `GetDims`
- `GetObjectMinMax`
- `Target`
- `GetTarget`
- `CreateObjectLink`
- `BreakObjectLink`

These commands should not require knowing a C++ subclass. They resolve handles and mutate/query runtime object state.

Handle variables must be resolved before hardcoded aliases except for true reserved handles. For example, after
`GetObjectHandle Terrain3 g_hObject`, later `g_hObject` must resolve to `Terrain3`, not to the active owner object.
`hMe` remains the current owner alias and `hPlayer` remains `mm9:player`.

State changes must update cache-membership metadata where relevant:

- visible/renderable;
- solid/collidable;
- ray-hit/pickable;
- trigger volume;
- interactive;
- scheduled;
- removed.

The first cache implementation can be vectors or flags. The important part is that callers do not need to rescan and
reclassify raw source properties every frame.

Unknown object properties, stats, and flags should be preserved exactly. Known flags can additionally update cache
membership when their behavior is understood, such as visibility, solid/collision, ray-hit/pickable, touch/trigger, and
active/removed state.

## Capability Operations

Implement these as request records or service calls behind generic object handles:

- model/animation:
  - `PlayAnim`;
  - `LoopAnim`;
  - `SetAnimPlaying`;
  - `GetCurrAnim`;
  - `GetAnimName`;
  - `AddModelKey`;
  - `RemoveModelKey`;
  - `HidePiece`;
- model/socket:
  - `AttachProp`;
  - `DetachProp`;
  - `GetSocketPos`;
  - `SetModelFilenames`;
- movement/action requests:
  - `MoveToPos`;
  - `WalkTo`;
  - `RunTo`;
  - `WalkToPos`;
  - `RunToPos`;
  - `MoveDir`;
  - `Stop`;
  - `FaceObject`;
  - `FacePos`;
  - `Rotate`;
- audio/FX/presentation:
  - `PlaySound`;
  - `PlaySoundHandle`;
  - `KillSound`;
  - `GetSoundDuration`;
  - `CacheClientFX`;
  - `DoClientFX`;
  - `CreateFX`;
  - screen fade, letterbox, rollover, texture/model presentation requests.

If no backend exists yet, record a typed request with source file/line, owner handle, target handle, arguments, and
callback labels. Do not drop the command or guess behavior.

## Routed Operations

Implement or consolidate routed behavior:

- `AddTrigger <message>, <label>` registers on the active owner object.
- `RemoveTrigger <message>` removes from the active owner object.
- `Trigger <target>, <message>` resolves the target and dispatches to the target object.
- `Trigger` must not call the caller's local label unless the caller and target are the same object.
- If the target has a script message registration, run that label in the target owner context.
- If the target later gains a native capability handler, route there before or after script handling according to the
  proven MM9 behavior for that object class.
- If unresolved, record the dispatch for diagnostics.

LithTech/NOLF has two routing details that matter for compatibility:

- A trigger message string can be a command-manager command. Representative code in
  `mm9/lithtech/NOLF/ObjectDLL/ServerUtilities.cpp` checks `g_pCmdMgr->IsValidCmd(...)` and processes the command
  before sending `MID_TRIGGER` to an object. MM9 commands such as `MSG`, `DELAY`, `REPEAT`, `LOOP`, and `ABORT` should
  stay in our central script scheduler/command layer, not be blindly delivered as object-local trigger labels.
- Name-based trigger dispatch can fan out to all objects returned by `FindNamedObjects`. Handle-based dispatch should
  stay single-target. If generated MM9 scripts pass raw object names to `Trigger`, preserve a stable one-to-many lookup
  path or at least record ambiguity diagnostics before choosing a single object. `GetObjectHandle` may still return one
  stable first match for LithTech-style handle variables.

Callback registrations should be object-scoped:

- `OnDamage`;
- `OnDamageDone`;
- `OnDeath`;
- `OnDeathDone`;
- `OnTouchNotify`;
- `OnFoundPlayer`;
- `OnFoundTarget`;
- `OnLostTarget`;
- `OnTargetDead`;
- `OnTargetBeyondDist`;
- `OnTargetWithinDist`;
- `OnAlert`;
- `OnStuck`;
- `OnObstacle`;
- `OnObstacleAvoided`;
- `OnPostStartWorld`;
- `OnPostMiniSaveLoad`;
- `OnPostSaveLoad`;
- model-key callbacks;
- numbered callbacks from `SetCallBack`.

The runtime should expose dispatch helpers that future actor/world/model/audio systems can call with an owner handle,
event kind, selector, sender/target handle, and parameters.

Do not design callbacks as a per-frame poll. LithTech `OnUpdate` is driven by `SetNextUpdate`: if the object does not
set a next update, it stops receiving update calls. Our equivalent should be one-shot scheduled invocations and typed
backend result dispatches that reschedule explicitly when needed.

## Lua Proxy API

Add or complete this Lua surface without requiring the exporter to immediately use all of it:

```lua
ctx:self()
ctx:player()
ctx:object(nameOrHandle)
ctx:objectOrNil(nameOrHandle)
ctx:objectByRudeId(rudeId)
ctx:paramObject(index)
```

Baseline object methods:

```lua
object:handle()
object:name()
object:className()
object:trigger(message)
object:pos()
object:setPos(x, y, z)
object:faceDir()
object:setFaceDir(x, y, z)
object:setFlag(flag, enabled)
object:flag(flag)
object:getStat(stat)
object:setStat(stat, value)
object:target(target, force)
object:getTarget()
object:walkTo(target, range, callback)
object:runTo(target, range, callback)
object:faceObject(target, rate, callback)
object:playAnimation(name, loop, callback)
object:loopAnimation(name, callback)
object:remove()
```

Proxy instances must be runtime facades over stable handles. If a proxy is stored in script state, save/load must
persist the stable handle and rehydrate the proxy through the registry.

## Save/Load

Persist all state that affects callbacks, later labels, or map behavior:

- object handle variables;
- runtime positions/facing/velocity;
- flags and removed/hidden/alive state;
- numeric/string property bags;
- stats;
- target handles;
- friend/enemy relation tokens;
- object links;
- trigger registrations;
- callback registrations;
- pending scheduled invocations;
- pending request queues;
- script overrides;
- synthetic spawned object handles.

If request queues are mirrored outside `Mm9ScriptRuntimeState` for convenience, restore paths and save/load tests must
prove that the mirrored lists are identical to the serialized state after load and after result dispatch.

Use an explicit save version bump if the serialized schema changes.

## Performance Constraints

Follow the LithTech performance shape without copying its implementation:

- classify objects once at load/projection time;
- maintain active/scheduled/renderable/collidable/ray-hit/trigger/interactable views;
- update views on state change, not every frame;
- avoid per-frame string classification of object classes/properties;
- avoid full object scans for `Trigger`, handle lookup, or object-name lookup;
- use maps from handle/name/class/RUDE id to object indices;
- keep raw source order separate from hot runtime views.

Specific LithTech patterns to mirror in OpenYAMM terms:

- Active objects are packed before inactive objects. `CServerMgr::PreUpdateObjects` stops at the first inactive object
  because `sm_SetObjectStateFlags` moves inactive objects to the tail and active objects to the head. We do not need
  intrusive lists, but our hot update paths should use active/scheduled vectors or swap-remove views rather than
  scanning all imported objects.
- Scheduled updates are sparse. `m_NextUpdate <= 0` means no update; positive values count down by frame time and call
  `OnUpdate` once. There is no useful "update every object 60 times per second" model to copy. Use due-time queues or
  compact scheduled vectors, and jitter/stagger repeated AI-style work when many objects become active at once.
- Spatial queries skip empty branches and de-duplicate callbacks with a frame code in LithTech's world tree. Before
  `DatLevelWorld`, only build cheap non-spatial indices. After DAT bounds exist, object queries should go through a
  spatial structure with per-query de-duplication, not through all-object scans.
- LithTech optimizes objects out of world-tree membership when they have no relevant visible, solid, touch, ray-hit,
  container, force-update, or special-effect flags. Our equivalent is capability/cache membership bits: source-only or
  dormant script objects should not appear in render/collision/raycast/trigger hot views.
- LithTech uses fixed-size temporary query arrays and 16-bit object ids. Do not copy those limits blindly, but do keep
  bounded scratch buffers, reserve sizes from source counts, and emit diagnostics if a query exceeds expected capacity.
- String maps are acceptable on script-command paths. They should not be introduced into per-frame actor movement,
  LOS, collision, render submission, or trigger-volume overlap paths.

The first data structures can be simple. The important constraint is API shape: do not design call sites that require
linear scans forever.

## Current OpenYAMM Oddities To Address

The current engine is close enough to implement this slice now, but these gaps should be fixed or explicitly decided
while doing it:

- `Mm9ScriptRuntime::objectHandleForName` currently treats `g_hObject` like the active owner before checking
  `objectHandleVars`. That is incoherent with scripts that assign `g_hObject` via `GetObjectHandle`.
- `objectBindingForObject` and `dispatchTrigger` currently search package bindings and trigger vectors linearly. This is
  acceptable for present tests, but the goal should introduce indexed lookup or an indexed view before any per-frame or
  high-frequency use depends on it.
- `dispatchTrigger` only routes package-backed object handles today. Synthetic spawned handles, player handles, raw-name
  fan-out, and unresolved native-capability dispatch need a recorded path so the behavior does not silently disappear.
- `removeRuntimeObject` already removes links, trigger registrations, callbacks, and scheduled invocations for package
  objects. It does not cancel active pending movement, animation, audio, FX, or AI requests for that handle. Decide
  which request records are immutable diagnostics and which are live pending work, then cancel live work on removal.
- `Mm9ObjectLayer`, `Mm9ScriptedObjectRuntime`, and `Mm9AnimatedActorBinding` already project source object visibility,
  solidity, bounds, collision radius, interaction, and visuals. Extend those projections; do not create a second,
  disconnected MM9 object database.
- Existing MM6-MM8 actor systems use their own actor vectors and gameplay services. MM9 actor-like objects should bridge
  into shared gameplay services only when they represent gameplay actors, while MM9 script-object routing stays in
  `game/mm9`.

## Tests

Add focused unit coverage around `Mm9ScriptRuntime` and new `game/mm9` helpers.

Required tests:

- handle formatting/parsing accepts valid MM9 handles and rejects malformed ones;
- `GetObjectHandle Terrain3 g_hObject` makes later `g_hObject` resolve to `Terrain3`, not active object;
- `GetMyHandle hMe` resolves to the active owner object;
- `GetPlayerHandle hPlayer` resolves to `mm9:player`;
- `AddTrigger Use OnUse` registers on the active object only;
- `Trigger hDoor Use` dispatches to the target door/object registration, not the caller's local label;
- trigger dispatch switches owner context to the target object while running the label;
- trigger message strings that are central scheduler commands are handled by the scheduler path, not treated as
  object-local trigger labels;
- raw-name trigger dispatch either fans out to all matching objects or records an ambiguity diagnostic before applying
  the chosen compatibility rule;
- recursive trigger dispatch respects the depth guard;
- `RemoveTrigger Use` removes only the active object's registration;
- `SetFlag`/`ClearFlag` update runtime state and cache-membership metadata;
- `RemoveObject` marks removed, clears/removes relevant trigger/callback/request state, and persists;
- `GetStat`/`SetStat` and `SetPropNumber`/`SetPropString` persist unknown names without dropping them;
- object links detach when a linked object is removed;
- live pending requests for a removed object are canceled or marked inactive while historical diagnostic records remain
  available if needed;
- object proxies call through stable handles and do not own duplicated state;
- proxies stored in runtime state save as handles and rehydrate through the registry;
- saved state and any mirrored request vectors are identical after restore;
- movement/animation/audio/FX commands record typed requests with owner handle, target handle, callback, and source
  line;
- callback registration dispatch helper runs the correct label for the correct owner.

Add at least one integration-style generated-script fixture covering:

```scr
GetObjectHandle Terrain3 g_hObject
AddTrigger Use OnUse
Trigger g_hObject open
```

Expected behavior: the trigger goes to `Terrain3`; it does not call `OnUse` on the caller unless `Terrain3` is the
caller.

## Build And Verification

Use focused unit tests first:

```bash
cmake --build build --target openyamm_unit_tests/fast -j25
./build/tests/openyamm_unit_tests --test-case="MM9 script runtime*" --success=false
```

If new tests use a more specific suite name, run that suite directly as well.

Run package/runtime validation touched by script changes:

```bash
./build/tests/openyamm_unit_tests --test-case="MM9 dialogue package*" --success=false
```

Run the full target only if shared headers, CMake, or broad runtime code changed:

```bash
cmake --build build --target openyamm -j25
```

## Deferred Until DatLevelWorld

- DAT BSP/portal visibility.
- Real DAT collision and floor resolution.
- Real raycasts, LOS, and reachability.
- Real object spatial indices tied to DAT bounds and moving world models.
- Door/platform/world-model movement against DAT geometry.
- Trigger volume overlap from actual movement.
- Object picking against final DAT render/collision geometry.
- Static-light spatial queries consumed by the DAT renderer.
- Final actor pathing over DAT navigation/collision structures.

The runtime should record requests and expose service boundaries now so these can plug in later.

## Non-Goals

- Do not introduce `engine/LTObject` or an engine-wide LithTech object manager.
- Do not make generated Lua own object storage.
- Do not bypass the message bus by calling another object's generated label directly.
- Do not hardcode MM9 object class behavior into the shared MM6-MM8 actor systems.
- Do not require full `DatLevelWorld` before object handles, callbacks, and request queues work.
- Do not discard unknown object commands, properties, classes, or flags.

## Done Criteria

- MM9 object handles resolve through a stable registry.
- Direct generic operations work against runtime object state.
- Object proxies exist and preserve handle routing semantics.
- `AddTrigger`, `RemoveTrigger`, and `Trigger` route through target object context.
- Callback registrations are object-scoped and dispatchable by later engine/world services.
- Request queues preserve movement, animation, audio, FX, and presentation intent.
- Save/load persists runtime object state needed across callbacks and reloads.
- Tests prove the active-object alias bug is fixed and target-object trigger dispatch is correct.
- No broad LithTech object manager or generic engine bloat is introduced.
