# MM9 Script Object Handles: Direct Versus Routed Operations

Status: contract note for MM9 `.SCR` to Lua conversion and the MM9 script/object runtime.

## Objective

Inventory what a LithTech-style script object handle can access directly, what must be routed through the target object,
and how OpenYAMM should preserve those semantics without copying LithTech's object manager.

This document is intentionally narrower than
`MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md`: it focuses only on `hobject` semantics and command routing.

## Reference Points

- `mm9/lithtech/sdk/inc/ltbasetypes.h:53`: `HOBJECT` is `LTObject *`.
- `mm9/lithtech/runtime/server/src/serverobj.h:24`: handle, `LTObject`, and `BaseClass` conversion macros.
- `mm9/lithtech/sdk/inc/iltserver.h:213`: `FindNamedObjects`.
- `mm9/lithtech/sdk/inc/iltserver.h:292`: `SendToObject`.
- `mm9/lithtech/runtime/server/src/serverde_impl.cpp:1244`: `SendToObject` calls the target `ObjectMessageFn`.
- `mm9/lithtech/sdk/inc/iltbaseclass.h:89`: `ObjectMessageFn`.
- `mm9/lithtech/sdk/inc/iltbaseclass.cpp:159`: default `ObjectMessageFn` forwards to aggregates.
- `mm9/lithtech/sdk/inc/iltbaseclass.h:182`: `OnUpdate`.
- `mm9/lithtech/runtime/server/src/smoveabstract.cpp:50`: touch notification calls the object's `OnTouch`.
- `mm9/lithtech/NOLF/ObjectDLL/ServerUtilities.cpp:165`: representative name-to-object trigger dispatch.
- `mm9/lithtech/NOLF/ObjectDLL/Character.cpp:417`: character-specific `MID_TRIGGER`.
- `mm9/lithtech/NOLF/ObjectDLL/Door.cpp:1974`: door-specific `MID_TRIGGER`.
- `mm9/lithtech/NOLF/ObjectDLL/Prop.cpp:215`: prop-specific `MID_TRIGGER`.

## Core Rule

An `hobject` variable in MM9 scripts is an opaque handle to a runtime object. It is not a Lua table, not a C++ actor
pointer, and not proof that the object is a monster, NPC, prop, door, light, or trigger.

Operations fall into three buckets:

- Direct generic operations: runtime can apply them to the object shell by handle.
- Direct capability operations: runtime can apply them by handle only if the object has the needed capability.
- Routed operations: runtime must deliver a message/event/request to the target object's script, class behavior, actor
  controller, world mechanism, model service, or other capability handler.

For SCR-to-Lua conversion, preserve that distinction. Do not turn `Trigger hDoor, Use` into a direct call to a local Lua
label named `Use`; it must route to the target object's registered handler or capability implementation.

## Handle Values

Script handle variables include:

- explicit `#hobject` variables;
- common globals such as `g_hObject`, `g_hMyObject`, `g_hTarget`, `hMe`, and `hPlayer`;
- `NULL`, `0`, and empty handle values;
- handles returned by `GetObjectHandle`, `GetMyHandle`, `GetPlayerHandle`, `GetTarget`, `GetObjects`, `Spawn`, and
  `GetObjectHandleByRUDEID`;
- handles passed through script params and object properties.

OpenYAMM should keep handles stable strings such as `mm9:<mapId>:object:<sourceIndex>` internally. The converter should
treat them as opaque values and compare them by handle equality only.

## Direct Generic Fields And Operations

These are safe to model as generic runtime-object state because LithTech exposes equivalent `HOBJECT` APIs directly.
They may still update cached views such as render, collision, ray-hit, trigger, and interaction lists.

- Identity:
  LithTech `FindNamedObjects`, `GetObjectName`, and `GetObjectClass`; MM9 `GetObjectHandle`, `GetObjectName`,
  `GetClassName`, and `IsClass`; owned by the MM9 object registry.
- Current object/player handles:
  active object handle and client/player object; MM9 `GetMyHandle`, `GetPlayerHandle`, and `IsPlayer`; owned by the
  script runtime context.
- Transform read/write:
  LithTech `GetObjectPos`, `SetObjectPos`, `TeleportObject`, and `GetObjectRotation`; MM9 `GetPOS`, `SetPos`,
  `GetFaceDir`, and `FaceDir`; owned by runtime object state, then world services.
- Basic movement request to point:
  LithTech low-level `MoveObject`; MM9 `MoveToPos`, `MoveDir`, and `Rotate`; owned by the movement service request
  queue.
- Bounds/dims:
  LithTech `GetObjectDims` and `SetObjectDims`; MM9 `GetDims` and `GetObjectMinMax`; owned by object state plus the
  world/collision service.
- Flags/state:
  LithTech object flags, user flags, and `SetObjectState`; MM9 `SetFlag`, `ClearFlag`, `IsVisible`, and
  `IsObjectActive`; owned by object state and cache membership.
- Lifetime:
  LithTech `RemoveObject`; MM9 `RemoveObject` and `Die`; owned by object runtime, save/load, and cache removal.
- Links:
  LithTech `CreateInterObjectLink` and `BreakInterObjectLink`; MM9 `CreateObjectLink` and `BreakObjectLink`; owned by
  the object link registry.
- Generic properties:
  LithTech world-file props and object-local state; MM9 `SetPropNumber`, `SetPropString`, `GetStat`, `SetStat`, and
  `GetStatStr`; owned by the MM9 object property bag.
- Target handle slot:
  game object state, not an engine field; MM9 `Target` and `GetTarget`; owned by actor/object runtime state.
- Scheduling:
  LithTech `SetNextUpdate`; MM9 `Wait`, delayed callbacks, and scheduled command records; owned by the script
  scheduler.

Implementation rule: generic direct operations should not require knowing the C++ subclass. They should resolve the
handle, mutate or query the object runtime record, and notify the relevant cache/service if the change affects
visibility, collision, picking, trigger membership, renderability, or save state.

## Direct Capability Operations

These accept generic handles in LithTech APIs, but they are only meaningful for objects with a specific engine type or
runtime capability. OpenYAMM should keep the handle generic and dispatch to a capability service after validation.

- Model animation:
  LithTech `SetModelAnimation`, `SetModelPlaying`, and model string keys; MM9 `PlayAnim`, `LoopAnim`,
  `SetAnimPlaying`, `GetCurrAnim`, and `GetAnimName`; route to model/actor visual service and record callback labels.
- Model sockets/nodes:
  LithTech attachment APIs and model node hide status; MM9 `AttachProp`, `DetachProp`, `GetSocketPos`, and
  `HidePiece`; route to model/socket service and fail visibly if there is no model capability.
- Model files/skin:
  LithTech `GetModelFilenames` and object create filename/skin; MM9 `SetModelFilenames`; route to the MM9 model
  resolver/visual binding.
- Light data:
  LithTech `GetLightColor`, `SetLightColor`, and `GetLightRadius`; route script-visible light-class behavior to the
  MM9 light runtime if needed.
- Sound handles:
  LithTech sound object/manager APIs; MM9 `PlaySound`, `PlaySoundHandle`, `KillSound`, and `GetSoundDuration`; route
  to the audio service and keep synthetic script sound handles.
- Client FX:
  LithTech client FX message system; MM9 `CacheClientFX`, `DoClientFX`, and `CreateFX`; route to the effect service
  request queue.
- Camera/cutscene:
  LithTech camera object plus game code; MM9 `SetCamera`, fades, letterbox, and scene commands; route to the
  presentation/camera service.
- World mechanism:
  LithTech world model movement/state; door/platform/trigger messages such as `Use`, `Open`, `Close`, and `Lock` via
  `Trigger`; route to world mechanism service or script handler.

Implementation rule: if the handle lacks the capability, do not invent behavior in the converter. Record a diagnostic
or a no-op result matching known script expectations, and keep enough provenance to fix the object binding later.

## Routed Operations

Routed operations must enter target behavior, not just mutate generic fields.

### Object Messages

LithTech `SendToObject` delivers a message to the target object's `ObjectMessageFn`. Representative game classes then
handle `MID_TRIGGER` differently:

- `Character` reads the message and calls `ProcessTriggerMsg`.
- `Door` reads the message and calls `TriggerMsg`.
- `Prop` reads the message and calls `TriggerMsg`.
- `Trigger` objects apply trigger-specific delay, count, filter, and target-message behavior.

MM9 script equivalents:

- `AddTrigger <message>, <label>`
- `RemoveTrigger <message>`
- `Trigger <targetHandleOrName>, <message>`
- `SetCallBack`
- object-scoped `On*` registrations that produce future label invocations

OpenYAMM contract:

- `AddTrigger` registers a message handler on the active object, not globally.
- `Trigger` resolves the target handle/name and sends the message to that target.
- If the target has a registered script handler for that message, run the label in the target object's owner context.
- If the target has a native capability handler, route to that handler.
- If neither exists, record the dispatch for diagnostics and future backend work.
- Do not execute the caller's local label unless the caller is also the resolved target.

### Engine And World Events

These are routed by the engine/world/actor system into object behavior:

- update tick after `SetNextUpdate`;
- touch/collision notifications;
- crush/link-broken notifications;
- activation/deactivation;
- model string keys;
- damage/death events;
- found/lost target and alert events;
- movement arrival/stuck/obstacle events;
- post-world-start and post-save-load callbacks.

MM9 script equivalents:

- `OnTouchNotify`
- `OnDamage`, `OnDamageDone`
- `OnDeath`, `OnDeathDone`
- `OnFoundPlayer`, `OnFoundTarget`, `OnLostTarget`
- `OnTargetDead`, `OnTargetBeyondDist`, `OnTargetWithinDist`, `OnTargetOutOfRange`
- `OnAlert`, `OnHelp`
- `OnStuck`, `OnObstacle`, `OnObstacleAvoided`, `OnAvoidingObstacle`
- `AddModelKey`, `RemoveModelKey`
- `OnPostStartWorld`, `OnPostMiniSaveLoad`, `OnPostSaveLoad`

OpenYAMM contract:

- Store these as callback registrations on the active object.
- Event producers later route into the registered labels with the correct owner, sender/target handles, params, and
  source context.
- The converter must not inline these as immediate calls unless the original command immediately invokes a local label.

### AI And Combat Requests

These accept handles, but they are actor-controller operations rather than generic object fields:

- `WalkTo`, `RunTo`, `WalkToPos`, `RunToPos`, `Stop`
- `FaceObject`, `FacePos`, `IsFacing`
- `Attack`, `RangeAttack`, `CanAttack`, `CanRangeAttack`, `HasRangeAttack`, `IsAttacking`
- `FindTargets`, `IsClearShot`, `CanReachObject`, `CanReachTarget`, `FindHidingPlace`
- `AddFriend`, `RemoveFriend`, `AddEnemy`, `RemoveEnemy`, `IsFriend`
- `Aware`, `Taunt`, `Launch`, `Converse`, `ResumeWait`, `PauseWait`, `SetIdle`
- `Damage`, `Heal`-like script/service effects if encountered

OpenYAMM contract:

- Keep target handles generic.
- Route to an MM9 actor/object controller service.
- Use shared gameplay damage/projectile systems where those semantics are gameplay, not DAT geometry.
- Use DAT world movement, collision, floor, raycast, and visibility services where those semantics are world-specific.

## Converter Guidance

The SCR-to-Lua converter should follow these rules:

- Preserve `#hobject` declarations as handle-typed variables or opaque script values.
- Preserve `NULL` and `0` handle semantics; do not conflate missing variable, empty string, and null object.
- Preserve case-insensitive command matching, but keep original names in comments/provenance.
- Convert direct generic operations to runtime API calls only if those calls still resolve through the MM9 object
  registry.
- Convert direct capability operations to runtime capability calls or `ctx:command(...)`; do not directly mutate model,
  audio, FX, or actor internals from generated Lua.
- Convert `AddTrigger` and callback registrations into explicit runtime registrations scoped to the current owner
  object.
- Convert `Trigger` into runtime message dispatch, never into direct local label execution.
- Preserve message strings exactly enough for case-insensitive matching and diagnostics.
- Keep labels as labels; do not assume a label belongs to another script just because another object uses the same
  label name.
- For unknown object commands, emit a runtime command call with source file/line metadata rather than lowering it into
  guessed behavior.

Preferred Lua shape:

```lua
ctx:command("getobjecthandle", "Door0, hDoor")
ctx:command("trigger", "hDoor, Use")
ctx:command("setflag", "hMe, FLAG_SOLID")
ctx:command("walkto", "hTarget, 128, OnArrive")
```

Typed helper syntax is acceptable only if the helper preserves the same runtime routing:

```lua
local hDoor = ctx:getObjectHandle("Door0")
ctx:trigger(hDoor, "Use")
ctx:setObjectFlag(hMe, "FLAG_SOLID", true)
ctx:walkTo(hTarget, 128, "OnArrive")
```

The helper form must still call the MM9 runtime. It must not call another generated Lua function directly.

## OpenYAMM Runtime Shape

OpenYAMM should model this with four layers:

- Object registry: stable handle, source index, map id, object name, class, RUDE binding, source properties.
- Generic state: transform, flags, object state, property/stat bags, links, removed/hidden/alive state, target handle.
- Capability services: actor controller, model/animation, world mechanism, trigger volume, light, sound, FX, camera.
- Message/event bus: `Trigger`, `AddTrigger`, callback registration, scheduler, engine/world event delivery.

This avoids both failure modes:

- too generic: treating every command as a property write and losing door/actor/trigger behavior;
- too specific: generating direct subclass calls or Lua label calls that bypass handle/message semantics.

## Classification Cheat Sheet

- `GetObjectHandle`, `GetMyHandle`, `GetPlayerHandle`:
  direct generic handle lookup/context only.
- `GetObjectName`, `GetClassName`, `IsClass`, `IsPlayer`:
  direct generic registry/class metadata queries.
- `GetPOS`, `SetPos`, `GetFaceDir`, `FaceDir`:
  direct generic state plus world cache update; real DAT transforms later become authoritative.
- `SetFlag`, `ClearFlag`, `IsVisible`, `RemoveObject`:
  direct generic state plus cache update; affects render/collision/ray-hit/trigger membership.
- `GetStat`, `SetStat`, `SetPropNumber`, `SetPropString`, `GetStatStr`:
  direct generic property bag; promote known names to typed fields where useful.
- `CreateObjectLink`, `BreakObjectLink`:
  direct generic link state with routed link-broken notifications.
- `AddTrigger`, `RemoveTrigger`, `Trigger`:
  routed object messages; the target object decides behavior.
- `On*`, `AddModelKey`, `SetCallBack`:
  routed event callback registration; an event producer invokes these later.
- `WalkTo`, `RunTo`, `MoveToPos`, `Stop`, `FaceObject`:
  routed movement/actor requests; these need the movement/world service.
- `Target`, `GetTarget`:
  direct actor/object state that is later consumed by the actor controller.
- `Attack`, `RangeAttack`, `Damage`, `Die`:
  routed gameplay/actor requests using shared combat where applicable.
- `PlayAnim`, `LoopAnim`, `SetAnimPlaying`, `HidePiece`:
  direct capability operation requiring a model capability.
- `AttachProp`, `DetachProp`, `GetSocketPos`:
  direct capability operation requiring a model/socket capability.
- `PlaySound`, `KillSound`, `DoClientFX`, camera/fade commands:
  direct capability or presentation requests; service-owned, not generic object behavior.

## Non-Goals

- Do not introduce a universal OpenYAMM `LTObject` base class.
- Do not make generated Lua own object storage.
- Do not route MM6-MM8 actor behavior through MM9's script object bus.
- Do not require the complete in-game `DatWorld` renderer before preserving handle/message semantics.
- Do not discard unknown object properties or unknown object commands.
