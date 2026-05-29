# MM9 Runtime Events Scripted Slice Goal

Goal: extend the implemented MM9 outdoor bmodel door slice into a broader playable runtime event slice, driven by
`<map>.events.yml` plus generated per-map Lua, while preserving normal MM6-MM8 behavior.

This goal is not complete MM9 `*.scr` parity. It should implement enough generated Lua dispatch, trigger volumes, model
instance bindings, and indoor face-group bindings to make more authored MM9 map behavior playable without guessing or
hardcoding map-specific behavior.

## Current Baseline

Already implemented or expected before this goal starts:

- MM9 maps can load generated `<map>.events.yml` sidecars when `kind: mm9_events`.
- MM6-MM8 maps without MM9 sidecars keep the legacy event path.
- MM9 outdoor `odm_bmodel` mechanisms can be bound from sidecar data.
- Outdoor `Door`, `RotatingDoor`, and `WeightedLift` bmodel mechanisms can be triggered and animated.
- `mm9.trigger <object-name> [message]` can manually dispatch to a named MM9 mechanism for debug testing.
- Generated sidecars preserve raw object references and unresolved binding diagnostics.

## Scope

Implement the next playable subset:

- load generated per-map MM9 Lua only for maps with `kind: mm9_events`;
- dispatch named MM9 object/message events through a runtime MM9 event registry;
- execute generated Lua trigger callbacks for supported commands;
- support runtime trigger volumes from `Trigger` objects;
- support model-instance bindings for simple scripted movement and interaction;
- support BLV/indoor face-group bindings for indoor MM9 mechanisms;
- keep unsupported commands and unresolved targets as explicit diagnostics;
- add unit and headless coverage proving MM9 support is sidecar-gated and MM6-MM8 behavior is unchanged.

## Non-Goals

This goal must not be treated as full `*.scr` implementation.

Out of scope:

- full LithTech/Monolith script VM parity;
- exhaustive SCR command/function catalog;
- exact source-engine expression, scoping, reentrancy, and timing quirks;
- complete AI, perception, shooter, trap, water, ladder, sound, dialogue, cutscene, and object-lifecycle command support;
- save/load completeness for every possible script state;
- hand-editing generated Lua to make a map work.

Unsupported behavior should be logged with source script and line information when available, then used to drive later
incremental goals.

## Runtime Registry

- [ ] Add an MM9 runtime event state object owned by the active map/session, not global engine state.
- [ ] Build exact `object_id -> object` lookup from `events.yml`.
- [ ] Build exact `source_name -> object_id` lookup.
- [ ] Build `source_object_index -> object_id` lookup.
- [ ] Build `mechanism_id -> mechanism state` lookup for built-in mechanisms.
- [ ] Build `source_name/message -> generated Lua handler` lookup.
- [ ] Preserve exact source object names by default.
- [ ] Add diagnostics for unresolved names, case mismatches, duplicate source names, and unsupported messages.
- [ ] Clear all MM9 runtime event state on map unload.

## Generated Lua Runtime

- [ ] Load `generated.lua` from `<map>.events.yml` only when `kind == mm9_events`.
- [ ] Register generated Lua trigger handlers from generated metadata or generated Lua callbacks.
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
- [ ] Dispatch generated Lua from `triggerMm9Object(targetName, messageName)`.
- [ ] Let generated Lua call back into built-in mechanism execution.
- [ ] Preserve unsupported generated commands as diagnostics, not silent success.
- [ ] Never hand-edit generated Lua; fix the generator, event sidecar, or runtime API instead.

## Trigger Volumes

- [ ] Parse and load `trigger_volume` bindings from `events.yml`.
- [ ] Convert MM9 `Pos` and `Dims` into runtime AABB/OBB volumes using the verified coordinate mapping.
- [ ] Support player touch/overlap enter dispatch.
- [ ] Support explicit use/click dispatch for trigger volumes when authored.
- [ ] Respect `StartOn` enough to disable inactive triggers.
- [ ] Preserve `TriggerTouch`, `PlayerTriggerable`, `SendDelay`, `TriggerDelay`, and timed fields in runtime state.
- [ ] Add basic cooldown/retrigger handling only when source timing is clear enough; otherwise log the limitation.
- [ ] Add diagnostics for triggers whose target/message cannot be resolved.

## Model Instance Bindings

- [ ] Consume `model_instance` bindings from `events.yml`.
- [ ] Route use/click on bound model instances to MM9 named dispatch.
- [ ] Move bound model instances by dynamic transform from rest state.
- [ ] Support `MoveToPos` and `MoveDir` for model instances.
- [ ] Support simple model/skin swaps from `SetModelFilenames`.
- [ ] Update render transform and picking after movement or model changes.
- [ ] Keep unsupported animation commands explicit until `PlayAnim` has a real runtime target.

## Indoor BLV Face-Group Bindings

- [ ] Generate or consume `blv_face_group` bindings without changing the BLV file format.
- [ ] Load MM9 event sidecars for indoor/BLV-style MM9 maps.
- [ ] Route use/click on bound BLV faces to MM9 named dispatch.
- [ ] Move bound BLV face groups by dynamic transform from rest state.
- [ ] Rotate bound BLV face groups around authored pivots where present.
- [ ] Update indoor render, picking, collision, floor resolution, and LOS after movement.
- [ ] Preserve existing MM6-MM8 indoor mechanisms and EVT face dispatch.

## Message Dispatch

- [ ] Keep built-in door/lift handling for common messages: `Use`, `Open`, `Close`, `Toggle`, `Move`.
- [ ] Dispatch authored `interaction.sends` and trigger output edges before falling back to self-use.
- [ ] Support generated Lua handlers for map-script-specific messages.
- [ ] Log unsupported messages with source object name, class, and message.
- [ ] Avoid routing MM9 named messages through legacy EVT ids except for the existing sidecar-gated click bridge.

## Diagnostics And Debugging

- [ ] Add an MM9 events debug log category or consistent log prefix.
- [ ] Log loaded event sidecar path and generated Lua path.
- [ ] Log object, mechanism, trigger, interaction, script, binding, and unresolved counts.
- [ ] Extend `mm9.trigger` to show whether dispatch hit built-in runtime, generated Lua, or both.
- [ ] Add debug output for current hovered MM9 source object when a binding is available.
- [ ] Add diagnostics for unsupported Lua API calls with source script and line when known.
- [ ] Add diagnostics for executable messages with no bound runtime target.

## Tests

- [ ] Unit test MM9 runtime registry construction from `Mm9EventsData`.
- [ ] Unit test exact `source_name -> object_id` lookup and duplicate-name diagnostics.
- [ ] Unit test generated Lua handler registration from metadata.
- [ ] Unit test `Trigger(targetName, messageName)` dispatch from generated Lua into built-in mechanism runtime.
- [ ] Unit test unsupported Lua command diagnostics include script and line metadata.
- [ ] Unit test trigger-volume overlap dispatches target/message once.
- [ ] Unit test inactive `StartOn=false` trigger does not fire.
- [ ] Unit test model-instance `MoveDir` reaches expected dynamic transform.
- [ ] Unit test BLV face-group movement reaches expected dynamic transform.
- [ ] Unit test maps without MM9 sidecars keep legacy MM6-MM8 event behavior.
- [ ] Headless test loading a representative outdoor MM9 map and triggering a generated Lua callback.
- [ ] Headless test loading a representative indoor MM9 map and opening/moving one bound face group.
- [ ] Headless test that unsupported MM9 script behavior logs diagnostics and does not crash.

## Candidate Maps

Use small, representative maps before broadening:

- `thjorgard` or `thjorgardcity`
  - Outdoor bmodel mechanisms plus generated Lua dispatch smoke tests.
- `darkpassageway`
  - Bridge/switch and trigger-driven movement behavior.
- `1000terrors`
  - Door, rotating-door, and weighted-lift regression map.
- A known indoor MM9 map with exported BLV face groups
  - Use the smallest map with clear authored doors or lifts once bindings are generated.

## Acceptance Criteria

- [ ] An MM9 map can load `events.yml` and generated Lua together.
- [ ] `mm9.trigger <object> <message>` can dispatch to built-in runtime or generated Lua and report which path ran.
- [ ] At least one trigger volume in a sample MM9 map dispatches an authored target/message.
- [ ] At least one model-instance target can be moved or updated from generated Lua.
- [ ] At least one indoor BLV face group can be triggered and moved/rotated from MM9 event data.
- [ ] Unsupported script commands are visible diagnostics with source context, not silent no-ops.
- [ ] MM6-MM8 maps without `kind: mm9_events` behave as before.
- [ ] No generated Lua, raw object YAML, ODM, or BLV file is hand-edited to make the samples work.

## Future Goal: Complete SCR Parity

After this playable subset is stable, create a separate complete SCR parity goal:

- inventory every parsed MM9 SCR command and service;
- classify each command as implemented, data-only preserved, intentionally unsupported, or unknown;
- implement command behavior incrementally from real map failures;
- add map-level regression tests for each newly supported behavior class;
- preserve all unsupported behavior as explicit diagnostics until implemented.
