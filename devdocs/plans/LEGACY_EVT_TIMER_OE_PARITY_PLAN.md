# Legacy EVT Timer OpenEnroth Parity Plan

This document defines the implementation plan for exporting and running legacy `OnTimer` and `OnLongTimer` EVT
triggers with OpenEnroth-compatible behavior. OpenEnroth and GrayFace's decompiled scripts are behavioral references
only; do not copy their code.

The motivating regression is the central fountain in New Sorpigal (`oute3`, event 131). Its generated Lua body is
correct, but its refill trigger is missing from exported timer metadata. On the first visit, the fountain therefore
reports `Refreshing!` instead of consuming one of 30 charges and restoring 5 hit points.

Do not repair this by editing generated Lua or by adding a New Sorpigal-specific overlay. The defect affects the
general legacy timer pipeline and must be fixed in the EVT parser, Lua exporter, shared event timer runtime, and timer
persistence.

## Status Checklist

- [x] Decode `OnTimer` and `OnLongTimer` payloads into a typed legacy timer descriptor.
- [x] Export every legacy timer trigger, including calendar schedules and 16-bit alternative intervals.
- [x] Identify timer continuations by source event and trigger step.
- [x] Preserve timer owner, handler, trigger kind, and local/global scope in Lua metadata.
- [x] Add a shared scripted-event timer scheduler used by indoor and outdoor maps.
- [x] Match OpenEnroth first-visit, last-visit, alarm advancement, and polling behavior.
- [x] Preserve native `RegisterMapTimerEvent` and `RegisterGlobalTimerEvent` behavior explicitly.
- [x] Persist stable timer state and map last-visit time across save/load.
- [x] Add explicit migration from the current timer save representation.
- [x] Regenerate all generated legacy Lua event files.
- [x] Add exporter, scheduler, runtime, save, and New Sorpigal regression coverage.
- [x] Build `openyamm` and run focused headless verification.

## Verification Results

- `tools/regenerate_lua_events.sh` regenerated the shared global script and 67 MM6, 76 MM7, and 61 MM8 map scripts.
- Focused exporter, metadata, scheduler, scope, overlay, save, and migration unit tests pass.
- `cmake --build build --target openyamm -j25` passes.
- The focused headless New Sorpigal regression passes the timer guard, first refill, first healing drink, charge
  exhaustion, and `Refreshing!` path.
- The full unit run completed with 929 of 933 cases passing. Its four failures are outside this timer change: projectile
  particle sizing, monster missile parsing, and the Mount Nighon actor-relation regression.

## Behavioral Sources

Primary local references:

- `reference/OpenEnroth-git/src/Engine/Evt/EvtInstruction.cpp`
  - Typed decoding of both timer opcodes.
- `reference/OpenEnroth-git/src/Engine/Evt/Processor.cpp`
  - Trigger enumeration, timer initialization, polling, execution, and alarm advancement.
- `reference/OpenEnroth-git/src/Engine/Evt/EvtProgram.cpp`
  - Enumeration of every trigger instruction, including repeated trigger opcodes in one event.
- `reference/OpenEnroth-git/src/Engine/Graphics/LocationTime.h`
  - Per-map last-visit state.
- `reference/OpenEnroth-git/src/Engine/SaveLoad.cpp`
  - Last-visit timestamp updates during map departure/save.
- `reference/mmext-scripts/Decompiled_Scripts/mm6/txt/OUTE3.txt`
  - Readable New Sorpigal event 130/131 control flow.
- `script_dumps/7d14.evt.txt`
  - Event 196, which contains three independent `OnLongTimer` triggers.
- `reference/mmmerge/Scripts/Core/timers.lua`
  - GrayFace/MMExtension distinction between ordinary and refill timer APIs.

## New Sorpigal Acceptance Behavior

The relevant legacy control flow is:

```text
event 130
  step 0: OnLongTimer / OnRefillTimer { Second = 1 }
  step 1: set first fountain counter to 30
  step 2: set second fountain counter to 30

event 131
  if first fountain counter < 1:
      show "Refreshing!"
  else:
      subtract one charge
      add 5 HP to the current character
      show "+5 Hit points restored."
  set the fountain autonote
```

Required runtime sequence:

1. Register event 130's long-timer trigger while loading `oute3`.
2. Run map-load events before polling timers.
3. Because a first visit has no prior map visit timestamp, treat the calendar timer as immediately due.
4. On the first eligible legacy timer poll, execute event 130 starting at step 1.
5. Set both exported counters, currently `MapVar(51)` and `MapVar(52)`, to 30.
6. The first normal use of event 131 consumes one charge and restores 5 HP.
7. After the timer fires, schedule its next alarm for the next future daily occurrence at `00:00:01`.
8. After 30 uses and before the next refill, event 131 reports `Refreshing!`.

GrayFace displays the first counter as `MapVar49`, while the generated Lua uses `MapVar(51)`. This numbering difference
is not the reported defect: the generated setter and consumer use the same exported selector. Timer registration is the
missing operation.

## Legacy Timer Descriptor

Both `OnTimer` and `OnLongTimer` use the same 10-byte descriptor payload:

| Offset | Width | Meaning |
| --- | --- | --- |
| 0 | `uint8_t` | Yearly flag; any nonzero value is true |
| 1 | `uint8_t` | Monthly flag; any nonzero value is true |
| 2 | `uint8_t` | Weekly flag; any nonzero value is true |
| 3 | `uint8_t` | Daily start hour/offset |
| 4 | `uint8_t` | Daily start minute |
| 5 | `uint8_t` | Daily start second |
| 6 | `uint16_t` little-endian | Alternative interval in half-minutes |
| 8 | `uint16_t` | Unused/reserved legacy value |

Add a typed representation to `EvtInstruction`, for example:

```cpp
struct LegacyTimerDescriptor
{
    uint8_t yearly = 0;
    uint8_t monthly = 0;
    uint8_t weekly = 0;
    uint8_t startHour = 0;
    uint8_t startMinute = 0;
    uint8_t startSecond = 0;
    uint16_t intervalHalfMinutes = 0;
    uint16_t reserved = 0;
};
```

Parse this descriptor explicitly for both timer opcodes. Exporter logic must not inspect `listValues` byte positions.

Preserve raw byte values during decoding. In particular:

- Combine both bytes of `intervalHalfMinutes`.
- Treat nonzero calendar flags as true rather than requiring exactly `1`.
- Preserve start hours greater than 23. Existing legacy data contains such values, and OpenEnroth treats them as a
  duration offset rather than clamping them to a clock hour.
- Support a completely zero calendar descriptor as a daily timer at midnight.

## Schedule Selection

Use OpenEnroth's precedence exactly:

1. A nonzero alternative half-minute interval overrides all calendar fields.
2. Otherwise, yearly takes precedence.
3. Otherwise, monthly takes precedence.
4. Otherwise, weekly takes precedence.
5. Otherwise, the timer is daily and uses hour, minute, and second.

Calendar periods are:

- day: 1 game day
- week: 7 game days
- month: 28 game days
- year: 12 28-day months, or 336 game days

All timers generated from legacy `OnTimer` and `OnLongTimer` opcodes repeat. Do not export legacy calendar timers as
one-shot timers.

## Exported Lua Metadata

Generated metadata should describe the source schedule, not a countdown calculated at export time. A daily long timer
for New Sorpigal should have this conceptual form:

```lua
timers = {
    {
        eventId = 130,
        sourceEventId = 130,
        triggerStep = 0,
        origin = "legacy",
        triggerKind = "long",
        scheduleKind = "daily",
        startHour = 0,
        startMinute = 0,
        startSecond = 1,
    },
}
```

`eventId` is the actual Lua handler that must execute. It can be a hidden synthetic event ID when the trigger's
continuation is not the source event's normal entry point. `sourceEventId` remains the owning legacy event used for
overlay removal, replacement, diagnostics, and stable save identity.

Alternative interval metadata should preserve the source unit:

```lua
{
    eventId = 230,
    sourceEventId = 230,
    triggerStep = 0,
    origin = "legacy",
    triggerKind = "timer",
    scheduleKind = "interval",
    intervalHalfMinutes = 10,
}
```

Weekly, monthly, and yearly schedules need only `scheduleKind`; daily schedules also carry their complete start offset.

Do not retain the generated legacy fields `targetHour`, `remainingGameMinutes`, or a countdown derived from an assumed
9:00 starting time. Those values lose source precision and cannot implement first-visit/last-visit behavior.

### Native Lua Timers

`RegisterMapTimerEvent` and `RegisterGlobalTimerEvent` are hand-authored runtime APIs, not legacy EVT opcodes. Keep their
relative-delay semantics through an explicit native metadata variant, for example:

```lua
{
    eventId = 12000,
    sourceEventId = 12000,
    origin = "native",
    scheduleKind = "relative",
    repeating = true,
    intervalGameMinutes = 5,
    initialDelayGameMinutes = 5,
}
```

The Lua loader may temporarily read the old native fields during the save/schema migration, but new registrations must
emit the explicit native form. Do not use a broad fallback that silently guesses whether a definition is legacy or
native.

## Trigger Enumeration And Continuations

Export every timer trigger instruction rather than one timer per event.

Timer identity for generated legacy events must include:

- source event ID
- exact trigger step
- trigger opcode/kind

The existing helper shape that searches for the first `(eventId, opcode)` occurrence is insufficient. MM7 `7d14`
event 196 has three `OnLongTimer` instructions: one weekly trigger and two yearly triggers. The two yearly triggers are
separate source instructions and must both remain registered even when they reach the same continuation.

Refactor synthetic trigger generation so that:

1. The exporter visits each trigger instruction.
2. Its continuation begins at the first executable instruction at or after `triggerStep + 1`.
3. A synthetic handler is generated when that continuation differs from the source event's normal entry point.
4. Synthetic lookup uses the exact trigger step, not merely the opcode.
5. Timer execution invokes the handler corresponding to that trigger's continuation.
6. Export does not `break` after the first timer found in an event.

Include `OnLongTimer` wherever trigger splitting currently recognizes `OnTimer`.

## Shared Runtime Model

Replace the separate indoor and outdoor timer countdown implementations with a small shared gameplay component under
`game/events/`, such as `ScriptedEventTimer.h/.cpp`.

The normalized timer definition should retain at least:

```cpp
enum class ScriptedTimerOrigin
{
    Legacy,
    Native,
};

enum class ScriptedTimerScheduleKind
{
    Relative,
    Interval,
    Daily,
    Weekly,
    Monthly,
    Yearly,
};

struct ScriptedTimerDefinition
{
    ScriptedEventScope scope = ScriptedEventScope::Map;
    ScriptedTimerOrigin origin = ScriptedTimerOrigin::Native;
    ScriptedTimerScheduleKind scheduleKind = ScriptedTimerScheduleKind::Relative;
    uint16_t eventId = 0;
    uint16_t sourceEventId = 0;
    uint8_t triggerStep = 0;
    bool longTimer = false;
    bool repeating = false;
    uint16_t intervalHalfMinutes = 0;
    int startHour = 0;
    int startMinute = 0;
    int startSecond = 0;
    float intervalGameMinutes = 0.0f;
    float initialDelayGameMinutes = 0.0f;
};
```

The final types may separate legacy and native schedule payloads with a variant if that is simpler and prevents invalid
field combinations. Do not add adapter layers that preserve duplicate indoor/outdoor ownership.

Timer state should store an absolute next alarm rather than a decrementing remaining duration. Prefer an integer game
time unit capable of representing legacy seconds exactly. A state also needs a stable definition key and any explicit
one-shot/fired state required by native timers.

For generated legacy timers, the stable key is `(scope, sourceEventId, triggerStep, triggerKind)`. For native timer
definitions, assign a deterministic registration identity in addition to scope and event ID so that two registrations
for the same event do not collapse during save reconciliation.

### Scope-Safe Execution

Preserve whether a definition came from the local or global event program. Timer dispatch must invoke the selected
program explicitly:

- map timer: execute only its local handler
- global timer: execute only its global handler

Do not use local-first/global-fallback lookup for a known timer scope. A local and global event with the same numerical
ID must not dispatch to the wrong program.

## Legacy Alarm Initialization

Given current party time `now` and per-map `lastVisit`, initialize legacy alarms as follows.

### Alternative Interval

```text
period = intervalHalfMinutes * 30 game seconds
nextAlarm = now + period
```

Alternative intervals do not fire immediately on first visit and do not use `lastVisit`.

### Daily Calendar Timer

If `lastVisit` is absent or zero:

```text
nextAlarm = immediately due
```

Otherwise:

```text
candidate = start of lastVisit's game day + startHour/startMinute/startSecond
if candidate < lastVisit:
    candidate += one game day
nextAlarm = candidate
```

Use the strict `<` comparison from OpenEnroth. A candidate exactly equal to `lastVisit` remains due.

### Weekly, Monthly, And Yearly Calendar Timers

```text
if lastVisit exists:
    nextAlarm = lastVisit + period
else:
    nextAlarm = now
```

The zero/no-last-visit paths are what initialize New Sorpigal's fountain counters on a new game.

## Polling And Alarm Advancement

Match these invariants:

- Register timers before map-load events execute.
- Do not execute a timer continuation before map-load events.
- Poll legacy timers no earlier than 30 game seconds after map registration, matching OpenEnroth's timer guard.
- A due timer executes at most once in one scheduler update, even after a large rest or time jump.
- Execute a generated legacy continuation corresponding to `triggerStep + 1`.
- After an alternative interval fires, set `nextAlarm = now + period`.
- After a calendar timer fires, repeatedly add its period without executing again until `nextAlarm > now`.
- For an initially due daily timer, first establish its epoch-relative time-of-day alarm, then advance it by whole days
  until it is strictly in the future.
- Do not create a catch-up storm over subsequent frames after a large time jump.

Indoor currently checks timers before advancing its world clock, while outdoor advances time before checking. The shared
scheduler must receive one consistent post-advance `now` value. Reorder the indoor call or calculate the target time
before dispatch so both worlds evaluate the same interval against the same timestamp.

## Map Reentry And Persistence

Legacy calendar timers use per-map last-visit time as their authoritative reentry input. `MapDeltaData` already contains
`MapDeltaLocationTime::lastVisitTime`; wire it into the runtime rather than adding a parallel timestamp.

The legacy DDM/DLV field uses legacy time ticks. With 128 ticks per real second and 30 game seconds per real second,
one game minute is 256 legacy ticks. Add named conversion helpers and keep the serialized field's original unit:

```text
legacyTicks = round(gameMinutes * 256)
gameMinutes = legacyTicks / 256
```

Required lifecycle behavior:

1. On normal map departure, stamp the current map's `lastVisitTime` with current party game time.
2. Preserve source/imported nonzero last-visit values.
3. Add location time to outdoor runtime snapshots; indoor snapshots already carry the containing map delta.
4. On normal map reentry, rebuild legacy timer alarms from definitions, current time, and `lastVisitTime`.
5. Do not treat existing map-respawn/refill hooks as replacements for legacy `OnLongTimer` events.
6. On quicksave/load of the active map, restore exact timer alarms by stable definition key so an immediately due timer
   is not executed twice.
7. If a newly generated definition has no state in an older save, initialize it explicitly from current time and
   `lastVisitTime`.
8. Stop using event/schedule similarity as the permanent timer reconciliation mechanism.

Bump the save format version when the common timer state replaces the current indoor/outdoor representations. Add an
explicit migration from version 66 rather than preserving an indefinite compatibility heuristic.

Native timers should retain their documented relative-delay and save behavior independently from legacy last-visit
scheduling.

## Overlay Ownership And Removal

`RemoveMapEvent(sourceEventId)` must remove:

- the visible source event handler
- all timer definitions whose `sourceEventId` matches
- any hidden synthetic handlers owned only by those timer definitions

Event replacement should likewise replace timer definitions owned by the source event without leaving stale synthetic
registrations. This is why generated metadata needs both the actual handler `eventId` and owning `sourceEventId`.

Map metadata merging must retain timer scope and stable identity. It must not silently deduplicate two distinct legacy
trigger steps.

## Implementation Order

### Phase 1: Typed Decode And Exporter Coverage

- Add `LegacyTimerDescriptor` to the legacy EVT instruction representation.
- Decode both timer opcodes explicitly.
- Refactor continuation helpers to accept an exact trigger instruction/step.
- Export every timer trigger and all schedule kinds.
- Add exporter unit tests before regenerating assets.

This phase should make generated `oute3.lua` contain event 130 timer metadata without hand-editing the generated file.

### Phase 2: Metadata Loader And Pure Scheduler

- Extend `ScriptedEventProgram` to parse the normalized legacy/native timer schema.
- Implement a shared timer definition, stable key, state, initialization, and advancement component.
- Cover the scheduler with pure unit tests for each schedule and boundary condition.

### Phase 3: Indoor/Outdoor Runtime Integration

- Replace both duplicated timer-state loops with the shared scheduler.
- Make both runtimes pass consistent current/post-advance time.
- Dispatch local and global handlers using explicit scope.
- Preserve load ordering and the legacy 30-game-second polling guard.
- Update headless diagnostics that inspect or advance timers.

### Phase 4: Reentry, Save Migration, And Overlay Semantics

- Stamp and restore `lastVisitTime`.
- Add location time to outdoor snapshots.
- Serialize the common absolute timer state and stable key.
- Add the version 66 migration.
- Update `RemoveMapEvent`, replacement, and metadata merging behavior.
- Keep native Lua registrations on their explicit native path.

### Phase 5: Regeneration And Runtime Verification

- Run `tools/regenerate_lua_events.sh`.
- Review the complete generated timer metadata diff for MM6/MM7/MM8.
- Run focused exporter, metadata, scheduler, save, and scripted-map tests.
- Build with `cmake --build build --target openyamm -j25`.
- Run focused headless New Sorpigal coverage.

## Test Plan

### Exporter Tests

Add focused cases to `tests/LegacyLuaExportTests.cpp`:

- MM6 `oute3` event 130 exports a daily long timer at `00:00:01`.
- MM6 `oute3` event 230 remains a repeating alternative interval timer.
- MM7 `7d14` event 196 exports all three long timers with distinct trigger-step identities.
- A daily timer with only `Second = 1` is not omitted.
- A daily timer with minute and second fields preserves both.
- Weekly, monthly, and yearly flags select the correct schedule by precedence.
- Noncanonical nonzero flag values are treated as true.
- An hour greater than 23 is preserved.
- An alternative interval greater than 255 proves both bytes of the `uint16_t` are decoded.
- Multiple `OnTimer` instructions in one event all export.
- Mixed `OnTimer` and `OnLongTimer` instructions all export with correct continuations.

### Metadata And Native API Tests

- Legacy and native metadata variants parse into unambiguous normalized definitions.
- Existing native map/global registration calls emit the new native representation.
- Two native definitions for the same event keep distinct stable identities.
- Removing a source event removes all owned timers and synthetic handlers.
- A local/global numerical event-ID collision dispatches the timer to its declared scope.

### Pure Scheduler Tests

- First-visit New Sorpigal daily timer is immediately due.
- After firing at a 9:00 start, its next alarm is the next `00:00:01` occurrence.
- An alternative half-minute interval first fires only after its interval.
- Daily reentry before the due time does not fire.
- Daily reentry after the due time fires once.
- Weekly, 28-day monthly, and 336-day yearly periods match OpenEnroth.
- A large time jump executes once and advances the next alarm strictly into the future.
- Two timers with the same event/opcode but different trigger steps remain independent.
- A timer exactly equal to its alarm is due.

### Runtime Regression Tests

- On first `oute3` visit, event 130 sets `MapVar(51)` and `MapVar(52)` to 30.
- The first event 131 use changes `MapVar(51)` from 30 to 29 and invokes the 5-HP/status path.
- The exhausted fountain reports `Refreshing!` and still sets the autonote.
- The refill resets the counter to 30 rather than incrementing it.
- Indoor and outdoor runtimes produce the same timer result.
- Map-load events execute before an immediately due timer continuation.
- Large rest/time-advance operations do not produce a catch-up storm.
- Existing map respawn hooks remain independent from long timers.

### Save And Reentry Tests

- Leaving and reentering before the daily alarm does not refill the fountain.
- Leaving and reentering after the alarm refills it once.
- Quicksave/load does not refire an already handled first-visit timer.
- Active legacy and native timer states round-trip with stable identity.
- Outdoor location time round-trips in the runtime snapshot.
- A version 66 save migrates deterministically.
- A newly added timer definition initializes from `lastVisitTime` when absent from old saved state.

## Expected Files

Primary implementation files:

- `tools/legacy_events/EvtProgram.h`
- `tools/legacy_events/EvtProgram.cpp`
- `tools/LegacyLuaExport.cpp`
- `game/events/ScriptedEventProgram.h`
- `game/events/ScriptedEventProgram.cpp`
- new shared `game/events/ScriptedEventTimer.h/.cpp`
- `game/scene/IndoorSceneRuntime.h`
- `game/scene/IndoorSceneRuntime.cpp`
- `game/outdoor/OutdoorWorldRuntime.h`
- `game/outdoor/OutdoorWorldRuntime.cpp`
- `game/maps/MapDeltaData.h`
- `game/maps/MapDeltaData.cpp`
- `game/maps/SaveGame.h`
- `game/maps/SaveGame.cpp`
- `game/app/GameSession.cpp` and/or `game/app/GameApplication.cpp` for map lifecycle integration
- `assets_dev/engine/scripts/common/event_support.lua`
- relevant `game/CMakeLists.txt`, `tools/CMakeLists.txt`, and `tests/CMakeLists.txt`

Primary tests:

- `tests/LegacyLuaExportTests.cpp`
- `tests/ScriptedMapRegressionTests.cpp`
- `tests/MapDeltaDataTests.cpp`
- focused shared timer scheduler tests
- outdoor headless timer diagnostics where currently applicable

Generated outputs under `assets_dev/worlds/mm6/events`, `assets_dev/worlds/mm7/events`, and
`assets_dev/worlds/mm8/events` must change only through `tools/regenerate_lua_events.sh`.

## Completion Criteria

The work is complete when:

- All legacy timer descriptor forms present in MM6/MM7/MM8 export without omission or truncation.
- Every timer trigger retains its exact continuation and stable identity.
- Indoor and outdoor maps use one shared scheduler with OpenEnroth-compatible alarm rules.
- Native Lua timers remain behaviorally intact through an explicit schema.
- Timer scope, overlay ownership, map reentry, and save/load behavior are deterministic.
- A new game in New Sorpigal initializes the fountain counters automatically and the first normal drink restores 5 HP.
- No generated legacy Lua file contains a hand-authored repair.
- Regeneration, focused tests, the `openyamm` build, and headless New Sorpigal verification pass.
