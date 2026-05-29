# Indoor Unimplemented Event Inventory

This document lists indoor event gaps found by comparing generated indoor Lua scripts under
`assets_dev/Data/scripts/maps/` with the current event runtime and indoor scene/world application code.

## Summary

All `evt.*` functions used by generated indoor map scripts are currently registered in `EventRuntime`.
The remaining gaps are not missing Lua bindings, but missing or incomplete consumers:

- `RefundChestArtifacts` is registered but no-op.
- Input prompt events are stored but do not appear to have an active gameplay/UI consumer.
- Several generated indoor events are metadata-only `RegisterEvent(..., nil, ...)` entries.

Implemented after the initial audit:

- Indoor timed events are advanced by `IndoorSceneRuntime`.
- Indoor NPC topic events execute through the shared event runtime hook.
- Explicit metadata-only events are treated as handled no-ops by `EventRuntime`.
- Indoor pressure plate face events fire from party floor-face transitions.
- Indoor `TriggerByObject` face events fire from moving world item and projectile face collisions.
- Indoor `TriggerByMonster` face events fire from actor wall-collision movement results.
- `_SpecialJump` dispatches through the scene event context and currently applies an indoor party launch impulse.
- Indoor `CastSpell` applies shared event buffs or spawns real indoor projectiles through the shared projectile service.

## Runtime Gaps

### Indoor Timed Events

Status: implemented.

Outdoor advances Lua timer triggers through `OutdoorWorldRuntime::updateTimers(...)` from
`OutdoorSceneRuntime::advanceFrame(...)`. Indoor now advances `ScriptedEventProgram::timerTriggers()` from
`IndoorSceneRuntime::advanceSimulation(...)`, applies event runtime state, and applies party event state without
auto-granting pending items.

Affected generated indoor timers:

- `d05.lua`: event `110`, repeating every `2.5` game minutes.
- `d22.lua`: event `451`, repeating every `5` game minutes.
- `d42.lua`: events `451`, `452`, `453`, `454`, `455`, `456`, repeating every `1.5` to `2.5` game minutes.

Implementation notes:

- Timer state is snapshot/restored with `IndoorSceneRuntime::Snapshot`.
- Timers only advance while indoor world simulation is allowed, matching modal gameplay pause behavior.
- Timer execution lives in the scene runtime, not renderer code.

### Indoor NPC Topic Events

Status: implemented.

`IndoorWorldRuntime::executeNpcTopicEvent(...)` now executes global NPC topic events through the shared
`EventRuntime` binding used by the dialogue controller.

Previous impact:

- Indoor dialogue topics that should execute a Lua event could not execute through the shared dialogue controller.
- This was especially risky for indoor NPC/house dialogues because the UI path was shared, but the indoor world hook
  was not.

Implementation notes:

- `previousMessageCount` is recorded before execution.
- Indoor world event state is applied after successful execution.
- Party event state is applied with `grantItemsToInventory = false`, matching outdoor topic-event behavior.
- The hook stays in the world runtime seam used by shared dialogue code; it does not duplicate dialogue UI behavior.

### `_SpecialJump` / `Jump`

Status: implemented for indoor movement as a scene-context launch impulse.

Known indoor usage:

- `elemf.lua`: events `452`, `453`, `454`.

Implementation direction:

- `EventRuntime` delegates `_SpecialJump` / `Jump` to `ISceneEventContext::specialJump(...)`.
- Indoor decodes the legacy packed horizontal speed/angle and vertical speed into a pending movement impulse on
  `IndoorPartyRuntime`.

### `CastSpell`

Status: implemented for shared party buffs and indoor event projectiles.

Implementation notes:

- Buff-style event spells use `tryApplyEventSpellBuffs(...)`, matching outdoor.
- Non-buff event spells resolve their display object from `spells.txt` / `objlist.txt` and spawn through
  `GameplayProjectileService` with `SourceKind::Event`.
- Event projectile damage and party impact handling use the shared projectile service event-source path.
- Outdoor scripts also contain `_SpecialJump`, but OE marks the opcode as unused. Outdoor can opt into the same scene
  hook later if those launch-pad events need parity.

### Indoor Face Trigger Sources

Status: implemented for party pressure plates, object/projectile triggers, and monster wall-collision triggers.

OE has separate face attributes for event activation by stepping, monster collision, and object collision:

- `FACE_PRESSURE_PLATE`
- `FACE_TriggerByMonster`
- `FACE_TriggerByObject`

Current implementation:

- Party pressure plates are detected in `IndoorSceneRuntime` by comparing the last processed party grounded support
  face with the current grounded support face.
- The event is executed by `IndoorWorldRuntime::executeFaceTriggeredEvent(...)`, which uses the effective runtime face
  attributes and `IndoorFace::cogTriggered`.
- Moving indoor world items and indoor projectiles trigger `TriggerByObject` when their collision path hits a matching
  face.
- Indoor actors trigger `TriggerByMonster` from the wall face reported by `IndoorMovementController` debug/movement
  result data.

### `RefundChestArtifacts`

`RefundChestArtifacts` is registered but currently no-op.

Known generated indoor usage:

- No direct generated indoor usage found in the current scripts.

Implementation direction:

- Low priority unless a map/event begins using it.
- If implemented, keep it shared in item/artifact event logic.

### Input Prompts

`Question`, `_InputString`, and `_PressAnyKey` store `EventRuntimeState::pendingInputPrompt`, but no active
gameplay/UI consumer was found in the current audit.

Known generated indoor usage:

- No direct generated indoor usage found in the current scripts.

Implementation direction:

- Low priority for indoor parity unless scripts begin using these commands.
- Implement through shared event-dialog/UI flow, not indoor-specific code.

## Generated Metadata-Only Indoor Events

The generated support layer only installs a callable Lua handler when `handler ~= nil`.
Therefore `RegisterEvent(..., nil, ...)` produces metadata/hint text but no executable body.
`EventRuntime` now treats such explicit hint-only events as handled no-ops instead of unresolved events.

Current count: `87` metadata-only indoor events.

### `d05.lua`

- `402`: `Legacy event 402`

### `d06.lua`

- `401`: `Submarine`

### `d09.lua`

- `459`: `Bookshelf`
- `460`: `Bookshelf`
- `461`: `Bookshelf`
- `462`: `Bookshelf`
- `463`: `Bookshelf`
- `464`: `Bookshelf`
- `465`: `Bookshelf`
- `466`: `Bookshelf`
- `467`: `Bookshelf`
- `468`: `Bookshelf`
- `469`: `Bookshelf`
- `470`: `Bookshelf`
- `471`: `Bookshelf`

### `d20.lua`

- `101`: `Legacy event 101`
- `104`: `Legacy event 104`
- `105`: `Legacy event 105`
- `106`: `Legacy event 106`

### `d24.lua`

- `204`: `Thanys' House`
- `206`: `Ferris' House`
- `208`: `Flooded House`
- `210`: `Flooded House`
- `212`: `Weapon shop placeholder`
- `214`: `Suretail House`
- `216`: `Rionel's House`
- `218`: `Armor shop placeholder`
- `220`: `Magic shop placeholder`
- `222`: `Spell shop placeholder`
- `224`: `Ulbrecht's House`
- `226`: `Senjac's House`
- `228`: `Alchemist placeholder`
- `230`: `Temple placeholder`
- `401`: `Fountain`
- `453`: `Lotts' House`
- `455`: `Hollyfield House`
- `457`: `Tessalar's House`
- `459`: `Stormeye's House`
- `461`: `Bank placeholder`
- `463`: `Training hall placeholder`
- `465`: `Ayzar's Axes`
- `467`: `Linked Mail`
- `469`: `Amulets of Power`
- `471`: `Perius' Powders`
- `473`: `The Shaman`
- `475`: `Balthazar Academy`
- `477`: `Bank of Balthazar`
- `479`: `Guild of Mind`

### `elema.lua`

- `12`: `Wingsail's House`
- `14`: `Vapor's House`
- `16`: `Zephyr's House`
- `18`: `Empty House`
- `20`: `Empty House`
- `22`: `Empty House`
- `24`: `Empty House`
- `26`: `Nedlon's House`
- `401`: `Castle of Air`
- `402`: `Raven Man Nest`
- `403`: `Gate out of the Plane of Air`

### `eleme.lua`

- `202`: `Loamwalker's House`
- `204`: `Soil's House`
- `206`: `Empty House`
- `208`: `Empty House`
- `210`: `Empty House`
- `212`: `Empty House`
- `214`: `Empty House`
- `216`: `Empty House`
- `218`: `Empty House`
- `220`: `Empty House`
- `224`: `Griven's House`
- `401`: `Gate out of the Plane of Earth`

### `elemf.lua`

- `12`: `Ember's House`
- `14`: `Evenblaze's House`
- `16`: `Empty House`
- `18`: `Empty House`
- `20`: `Empty House`
- `22`: `Burn's House`
- `401`: `Castle of Fire`
- `402`: `War Camp`
- `403`: `Gate out of the Plane of Fire`

### `elemw.lua`

- `12`: `Riverglass' House`
- `14`: `Clearcreek's House`
- `16`: `Empty House`
- `18`: `Empty House`
- `20`: `Empty House`
- `22`: `Black Current's House`
- `401`: `Gate out of the Plane of Water`

## Currently Registered Indoor Script Commands

Generated indoor scripts currently use this `evt.*` set:

- `CastSpell`
- `CheckMonstersKilled`
- `EnterHouse`
- `FaceAnimation`
- `ForPlayer`
- `GiveItem`
- `MoveNPC`
- `MoveToMap`
- `OpenChest`
- `SetDoorState`
- `SetFacetBit`
- `SetLight`
- `SetMonGroupBit`
- `SetNPCTopic`
- `SetTexture`
- `ShowMovie`
- `SpeakNPC`
- `StatusText`
- `StopDoor`
- `SummonMonsters`
- `_IsNpcInParty`
- `_SpecialJump`

All of these are registered. `_SpecialJump` now dispatches through `ISceneEventContext::specialJump(...)` and indoor
maps apply it as a party movement impulse.

## Recommended Fix Order

1. Triage metadata-only `RegisterEvent(..., nil, ...)` entries against OE behavior only if one of them should perform
   a real action instead of being metadata-only.
2. Leave `RefundChestArtifacts` and input prompts until there is concrete indoor script usage or a known gameplay bug.
