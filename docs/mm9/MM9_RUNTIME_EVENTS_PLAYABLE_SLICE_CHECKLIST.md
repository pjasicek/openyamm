# MM9 Runtime Events Playable Slice Checklist

Goal: make an MM9 map such as `thjorgard` load its generated event data in-game and allow basic authored mechanisms,
especially doors and trigger-driven movers, to be used by the player.

This is the next slice after generating `<map>.events.yml` and generated Lua. Existing MM6-MM8 behavior must remain
unchanged unless a map explicitly declares `kind: mm9_events`.

## Scope

Target playable behavior:

- enter a generated MM9 map;
- load `<map>.events.yml`;
- build a source object registry by MM9 object name and id;
- bind supported mechanism objects to runtime geometry/model/volume targets;
- click/use a supported MM9 door or interaction target;
- dispatch the authored message, usually `Use`, `Open`, `Close`, `Toggle`, or map-script-specific messages;
- move/rotate the bound geometry or model instance;
- update picking and collision enough that the player can pass through an opened door.

Initial mechanism support should focus on:

- `Door`;
- `RotatingDoor`;
- `WeightedLift`;
- `Trigger` use/touch dispatch where needed by doors/lifts;
- scripted `MoveToPos`/`MoveDir` only when needed for a chosen sample map.

Out of scope for the first playable slice:

- full MM9 script VM parity;
- all traps, shooters, water, ladders, destructibles, AI barriers, and perception volumes;
- perfect sound/animation parity;
- save/load completeness beyond temporary runtime state;
- broad editor authoring UI.

## Candidate Test Maps

Use one or two representative maps first:

- `thjorgard`
  - outdoor-like MM9 city map with many authored objects and interactions.
- `thjorgardcity`
  - city variant if the generated playable package currently targets this name.
- `darkpassageway`
  - useful for bridge/switch behavior after basic doors work.
- `1000terrors`
  - useful for door/rotating-door/weighted-lift regression once basics work.

Before implementation, inspect the chosen map's generated event sidecar:

```bash
rg -n "source_class: (Door|RotatingDoor|WeightedLift|Trigger)|source_name:|mechanism:" \
  assets_dev/worlds/mm9/maps/thjorgard.events.yml
```

## Runtime Loading

- [ ] Add an optional MM9 event asset reference to map/scene loading.
- [ ] Resolve `<map>.events.yml` beside the loaded MM9 map/scene.
- [ ] Load MM9 event data only if the sidecar exists and `kind == mm9_events`.
- [ ] Do nothing for MM6-MM8 maps with no MM9 sidecar.
- [ ] Report malformed MM9 sidecars as MM9 map-load diagnostics, not global fatal errors for other worlds.
- [ ] Load generated per-map Lua path from `generated.lua` when present.
- [ ] Keep generated Lua optional for built-in door/lift mechanisms.
- [ ] Add map-load logging/debug output showing MM9 event object/mechanism/trigger counts.

## Runtime Registry

- [ ] Add a runtime MM9 event state object owned by the current map/session.
- [ ] Build `object_id -> object`.
- [ ] Build `source_name -> object_id`.
- [ ] Build `source_object_index -> object_id`.
- [ ] Build `mechanism_id -> mechanism state`.
- [ ] Build `source_name/message -> handler` for built-in mechanisms.
- [ ] Build script handler registry from generated Lua metadata or generated Lua runtime callbacks.
- [ ] Preserve unresolved target diagnostics in runtime debug output.
- [ ] Ensure this registry is cleared on map unload.

## Binding To Runtime Targets

- [ ] Consume `bindings` from `<map>.events.yml`.
- [ ] Support `model_instance` bindings first, because they already have stable `source_object_index` from scene data.
- [ ] Support `odm_bmodel` bindings for outdoor-style movable world geometry.
- [ ] Support `blv_face_group` bindings for indoor-style movable face groups.
- [ ] Support `trigger_volume` bindings as AABB/OBB interaction volumes.
- [ ] Keep `unresolved` bindings non-fatal but visible in diagnostics.
- [ ] Add debug assertion/log when a mechanism receives a message but has no executable binding.
- [ ] Avoid guessing a geometry target at runtime if the sidecar did not bind it.
- [ ] If the generated sidecar lacks enough bindings for the target map, add generator binding improvements before
      adding runtime hacks.

## Picking And Use Dispatch

- [ ] Route player use/click on bound model instances to the corresponding MM9 interaction.
- [ ] Route player use/click on bound ODM bmodel/face group to the corresponding MM9 interaction.
- [ ] Route player use/click on bound BLV face group to the corresponding MM9 interaction.
- [ ] For `Door`/`RotatingDoor`, default use message should trigger the door if the sidecar does not specify another
      use edge.
- [ ] Dispatch authored `interaction.sends` target/message edges where present.
- [ ] Support direct self-use for door-like objects.
- [ ] Add temporary debug command or overlay line for selected object name/message dispatch.
- [ ] Ensure MM6-MM8 face event dispatch is not changed.

## Message Dispatch

- [ ] Implement `triggerMm9Object(targetName, messageName)`.
- [ ] Resolve target names case-insensitively only if MM9 source behavior requires it; otherwise preserve exact names and
      log unresolved case mismatches.
- [ ] Support common door messages: `Use`, `use`, `Open`, `open`, `Close`, `close`, `Toggle`, `Move`.
- [ ] For built-in mechanisms, map messages to open/close/toggle actions.
- [ ] For generated Lua, expose an API for receiving a target object and message.
- [ ] Preserve unsupported messages as diagnostics, not silent success.
- [ ] Avoid routing MM9 messages through legacy EVT ids.

## Door And Lift Execution

- [ ] Implement linear movement from rest transform using `MoveDir`, `MoveDist`, `Speed`, and `ClosingSpeed`.
- [ ] Respect `StartOpen`.
- [ ] Respect `Locked` enough to block opening and emit a debug/log diagnostic.
- [ ] Respect `OpenWaitTime` for auto-close where present, if the first target map needs it.
- [ ] Respect `MoveDelay` if the first target map needs it.
- [ ] Support reversing direction while moving.
- [ ] Move bound model instances by transform, not by destructively editing rest data.
- [ ] Move bound ODM bmodels by dynamic transform.
- [ ] Move bound BLV face groups by dynamic transform.
- [ ] Update collision/picking after movement.
- [ ] Move the party with platforms/lifts only after basic static door passage works.

## Rotating Door Execution

- [ ] Implement rotation around `RotationPoint`.
- [ ] Apply `RotationAngles` in the verified MM9 coordinate mapping.
- [ ] Use source speed fields for timing, preserving current uncertainty in units with a documented conversion.
- [ ] Respect `StartOpen`.
- [ ] Respect `Locked`.
- [ ] Update collision/picking after rotation.
- [ ] Add visual/debug test for a known `RotatingDoor` map before enabling broadly.

## Trigger Volumes

- [ ] Create runtime volumes from `Trigger` objects with `Dims` and `Pos`.
- [ ] Support player touch enter or overlap dispatch.
- [ ] Support `StartOn`.
- [ ] Support `TriggerTouch` and `PlayerTriggerable`.
- [ ] Preserve `SendDelay`, `TriggerDelay`, and timed trigger fields even if not fully implemented.
- [ ] Prevent repeated trigger spam with a basic cooldown if needed, but document any deviation from source behavior.

## Generated Lua Runtime

- [ ] Load generated MM9 Lua only for maps with `mm9_events`.
- [ ] Add a small MM9 Lua API surface:
  - `Trigger(targetName, messageName)`;
  - `MoveToPos(objectName, x, y, z, rate, callbackName)`;
  - `MoveDir(objectName, x, y, z, dist, rate, callbackName)`;
  - `SetStat(objectName, statName, value)`;
  - `GetStat(objectName, statName)`;
  - `SetFlag(objectName, flagName)`;
  - `ClearFlag(objectName, flagName)`;
  - `PlayAnim(objectName, animName)`;
  - `SetModelFilenames(objectName, modelName, skinName)`.
- [ ] Start by using generated Lua metadata to register `AddTrigger` handlers.
- [ ] Do not hand-edit generated Lua for fixes; fix generator/parser/runtime APIs.
- [ ] Unsupported commands should log explicit diagnostics with source script and line.

## Collision And Spatial Updates

- [ ] Represent moving mechanism targets as dynamic transforms from rest state.
- [ ] Update render transform for model instances.
- [ ] Update world collision for moved bmodels or face groups.
- [ ] Update picking/raycast data for moved targets.
- [ ] Avoid whole-map rebuilds every frame.
- [ ] Recompute dynamic target AABBs when a mechanism moves.
- [ ] Verify that opened doors stop blocking player movement in the sample map.

## Diagnostics

- [ ] Add debug log category for MM9 events.
- [ ] Log loaded event sidecar path and generated Lua path.
- [ ] Log mechanism count, interaction count, trigger count, and unresolved count.
- [ ] Log use/click target object name and message in debug builds.
- [ ] Log unresolved target names.
- [ ] Log unsupported messages/commands.
- [ ] Log missing bindings.
- [ ] Add a console/debug command to trigger a named MM9 object manually:

```text
mm9.trigger DoorName Use
```

## Tests

- [ ] Unit test loading an MM9 event sidecar into runtime registry.
- [ ] Unit test `source_name -> object_id` lookup.
- [ ] Unit test direct message dispatch to a built-in linear door.
- [ ] Unit test locked door blocks open.
- [ ] Unit test linear door reaches expected open transform.
- [ ] Unit test linear door closes/reverses.
- [ ] Unit test rotating door reaches expected rotation.
- [ ] Unit test trigger volume dispatches target/message.
- [ ] Unit test unresolved target produces diagnostic but does not crash.
- [ ] Unit test maps without MM9 sidecars keep legacy event path.
- [ ] Headless runtime test loading the chosen MM9 map and triggering one known door/object by name.
- [ ] Headless runtime test that player collision is unblocked after opening the chosen door.
- [ ] Optional editor smoke test that event sidecar loads and selected bindings can be inspected.

## Acceptance Criteria

- [ ] Starting an MM9 map with `<map>.events.yml` loads the event sidecar.
- [ ] Starting MM6-MM8 maps behaves exactly as before.
- [ ] Runtime debug output shows the MM9 event registry for the loaded MM9 map.
- [ ] At least one known door or door-like mechanism in `thjorgard` or the selected target map can be triggered in-game.
- [ ] The mechanism visibly moves to its open state.
- [ ] Player collision/picking updates enough to pass through or interact with the changed state.
- [ ] Unsupported MM9 behavior is reported as explicit diagnostics, not silent no-op success.
- [ ] No generated Lua or event sidecar is hand-edited to make the sample work.
