# MM9 DAT Trigger Runtime Goal

## Status

Planned from an audit of all 45 extracted MM9 DAT maps, the local MM9 object-DLL decompilation, the local
LithTech-family source, assigned SCR files, generated MM9 discovery data, and the current OpenYAMM importer and
runtime.

OpenYAMM currently has two incomplete and conflicting trigger paths:

- generated scene data imports only ordinary `Trigger` objects whose outputs can already be reduced to one of five
  destructible actions; and
- the positioned-transition runtime treats imported `ExitTrigger` objects as independent, always-enabled party-entry
  volumes.

That is insufficient for MM9. Ordinary DAT triggers form a map-local command graph connecting touch volumes, logic
nodes, exits, doors, traps, sounds, actors, spawners, destructibles, script objects, and other named objects. Trigger
state, sender identity, output order, delays, counters, and enable/disable commands affect gameplay and must survive
save/load where the source does.

This goal is complete only when every supported shipped MM9 `Trigger` and `ExitTrigger`:

- is imported without discarding unrecognized target/message pairs;
- receives native-equivalent touch and object-command activation;
- routes its ordered outputs to typed native receivers or an explicitly compiled source-specific hook;
- preserves enabled state, activation count, cooldown, delayed activation, and required sender identity;
- cooperates with the shared transition, mechanism, actor, audio, destructible, map-state, and save systems;
- reports unresolved targets or unsupported required receivers through generated audits instead of silently dropping
  them; and
- adds no meaningful runtime cost when MM9 is not mounted or the active map has no MM9 trigger definitions.

The first required vertical slice is Bootcamp source trigger 216. Completion of only that case is not completion of
the goal; Yanmirsfort sender-dependent behavior and the Thronheim City prison breakout are also mandatory acceptance
cases.

## Objective

Import MM9 DAT trigger objects as typed map-local command nodes with optional touch-sensitive axis-aligned volumes,
then route their messages through existing shared OpenYAMM gameplay systems and narrowly compiled MM9 hooks.

The implementation must reproduce the source distinction between:

- a movement-generated touch notification;
- an object command such as `ON`, `OFF`, or `TRIGGER`;
- delayed activation and ordered target/message fanout;
- an `ExitTrigger` that can be touched or activated by another object;
- a message string such as `Leave`, which is an arbitrary receiver command rather than a volume-exit event; and
- source-specific SCR behavior that requires a compiled hook but does not justify a general SCR runtime.

## Relationship To Existing Goals

This document owns DAT `Trigger` import, touch activation, trigger state, command fanout, and the connection between
ordinary triggers and typed receivers.

Related documents retain their existing ownership:

- `MM9_TRANSITIONS_TRANSPORT_SKILLS_GOAL.md` owns destination/start-point resolution, confirmation, travel days, and
  shared map-transition behavior. This goal adds `ExitTrigger` enable state and command activation to that path.
- `MM9_DESTRUCTIBLE_GEOMETRY_GOAL.md` owns destructible geometry state and the Thronheim prison wall. This goal owns
  delivery of `Breakout`, `Destroy`, `DamageOn`, `DamageOff`, and related source messages.
- `MM9_SCRIPTED_ACTOR_IMPORT_GOAL.md` owns imported actor behavior and explicit encounter profiles. This goal supplies
  the source trigger command and touching-object context.
- `MM9_RUDE_SCR_INTEGRATION.md` owns strict build-time compilation of dialogue-linked SCR routines. This goal may
  request additional narrow compiled callbacks, such as Bootcamp NPC436 `Leave`, but must not introduce a general SCR
  interpreter.

Do not duplicate receiver-owned gameplay state in the trigger runtime. The trigger runtime delivers commands; the
transition, door, actor, destructible, sound, or other target subsystem remains authoritative for the resulting state.

## Non-Negotiable Architecture

- Keep generated MM9 trigger definitions, audits, and explicit overlays under `assets_dev/worlds/mm9/`.
- Keep ordinary trigger behavior map-local and world-scoped. MM6/MM7/MM8 and classic ODM/BLV maps must not pay for
  MM9 trigger scans, name indexes, command routing, or trigger save state.
- Use one MM9 trigger/command runtime for enclosed and exterior MM9 maps. Do not tie the semantic layer to
  `OutdoorWorldRuntime`, even if converted MM9 geometry currently uses ODM-style world representation.
- Reuse shared movement, actor, transition, mechanism, audio, destructible, event, party, map-delta, and save systems.
- Do not add a general MM9 SCR VM or compile general MM9 actor AI as part of this goal.
- Do not reduce arbitrary source messages to a fixed trigger-action enum. Native target classes and compiled hooks
  decide what a message means.
- Do not model MM9 DAT `Trigger` as an `on_enter`/`on_leave` scripting abstraction. The source is touch-notification
  driven and has no general leave callback.
- Do not use the party center as the collision test. Use the moving party or actor collider and a swept overlap test
  against the trigger AABB so thin volumes cannot be skipped.
- Do not rotate the trigger AABB. LithTech object dimensions update the world-tree bounds as `position - dims` and
  `position + dims`; source rotation is provenance/debug data, not collision orientation.
- Do not directly edit generated scene YAML, raw-object YAML, event YAML, or generated Lua. Fix the importer/compiler
  or add an explicit reviewed authored overlay.
- Do not select the first similarly named object, nearest object, or nearest start point when source resolution fails.
  Retain the authored name, emit an audit record, and require a reviewed correction when gameplay needs one.
- Preserve original map id, source object index, source class, source name, target slot, target name, message spelling,
  assigned script, raw source property, and source-file provenance in generated data and diagnostics.
- Preserve target output order. A queued transition must not commit in the middle of a trigger fanout batch.
- Keep runtime state under a stable map id plus source object index. Generated scene indexes and BModel indexes are
  resolved definition details, not persistent identities.

## Source Authority

Use local evidence in this order:

1. The original extracted MM9 DAT object, including class, source object index, name, transform, dimensions,
   properties, target slots, messages, and assigned script.
2. MM9 native behavior recovered from `/home/pjasicek/github/OpenMM9/reference/game/data/object.lto.c` and the reviewed
   findings in `/home/pjasicek/github/OpenMM9/docs/object_native_re_method_findings.md`.
3. The assigned SCR and only the callback paths reachable from the relevant trigger message or touch event.
4. Local LithTech-family source as a structural cross-check for collision notification and inherited trigger
   behavior, not as code to copy and not as proof when MM9 decompilation differs.
5. Generated OpenYAMM raw-object, script-IR, event, and scene data as reproducible importer output.
6. A reviewed MM9 map overlay when a required source-specific behavior cannot be represented by the generic typed
   runtime or strict callback compiler.

Use the local OpenMM9 checkout and checked-in references. Do not replace available local evidence with web research.

## Audited Shipped Baseline

The checked-in audit generator must reproduce or explicitly explain changes from this baseline.

### Object census

Across 45 extracted maps:

| Class | Count | Maps containing class | Meaning |
| --- | ---: | ---: | --- |
| `Trigger` | 482 | 33 | Touch-capable or command-only message router |
| `ExitTrigger` | 105 | 44 | Positioned and command-activated map transition |
| `PortalTrigger` | 1 | 1 | Named portal controller; not an ordinary trigger volume |

The 482 ordinary triggers contain 1,394 authored target/message output slots:

- 1,344 resolve case-insensitively to exactly one statically named object in the same DAT;
- 50 have no static same-map target and must remain name-addressable for runtime-spawned objects or explicit source
  review;
- no shipped resolved target name currently maps to multiple static objects, but the native operation addresses named
  objects and the representation must not assume that uniqueness for future content; and
- no output has a message without a target name.

### Ordinary trigger properties

| Property or behavior | Shipped distribution |
| --- | --- |
| `StartOn` | 466 enabled, 16 disabled |
| `PlayerTriggerable` | 418 enabled, 64 disabled |
| `AITriggerable` | 71 enabled, 411 disabled |
| Neither player nor AI triggerable | 63 command/logic nodes |
| `ActivationCount` | 323 one-shot, 157 unlimited, one five-use, one ten-use |
| Non-zero `TriggerDelay` | 9 |
| Non-zero `SendDelay` | 53 |
| Either delay non-zero | 57 |
| Non-empty `ActivationSound` | 7 |
| Non-zero source rotation | 14 |
| Zero `Dims` component | 4 |
| Assigned `ScriptName` | 1, Yanmirsfort `Yanmir_EndOfWorld.scr` |

All shipped ordinary triggers currently have:

- `WeightedTrigger = 0`;
- `TimedTrigger = 0`;
- `Locked = 0`;
- `OccurencePct = 1.0`;
- empty `AITriggerName`;
- empty `AttachToObject`; and
- `AdditionalTargets = 0`.

`TriggerTouch` is enabled on 180 objects, but every shipped `MessageTouch` is empty, so this touch-back path has no
shipped effect. Preserve it in the source schema, but do not confuse it with ordinary target/message fanout.

### Exit triggers

The existing transition audit resolves 104 of 105 exits and intentionally leaves the invalid Arslegard City
`SkyStart0` arrival unsupported. Of the 105 exits:

- 99 start enabled and six start disabled;
- 101 request confirmation and four are automatic;
- 103 have no assigned script;
- one uses `PropTrigger.scr`; and
- one uses `TrainingHallExit.scr`.

The six disabled exits are:

| Map | Source object | Name | Script |
| --- | ---: | --- | --- |
| Afterworld | 105 | `ExitTrigger1` | `PropTrigger.scr` |
| Dark Passageway | 274 | `ExitPoint` | none |
| Thjorgard | 114 | `ExitTrigger6` | none |
| Thjorgard | 486 | `ExitTrigger3` | none |
| Training Hall | 221 | `ExitTrigger0` | `TrainingHallExit.scr` |
| Yanmirsfort | 612 | `PlayerExit` | none |

These must not activate from spatial overlap until source behavior enables them. The existing positioned-transition
record does not currently retain `StartOn`, so this is a known correctness gap.

### Current import coverage

Only eight of the 482 ordinary triggers are currently emitted as active scene `trigger_volumes`:

- three in Training Hall;
- two in Ruined Temple;
- one in Anskram Keep;
- one in Inventa Storca; and
- one in Thjorad Mine.

They are selected only because at least one output resolves to a recognized destructible action. All other door,
trigger, sound, trap, actor, spawner, script-object, exit, and custom-message outputs are dropped from runtime data.

### DAT decoding defect

MM9 stores shipped `ActivationCount` values as integral IEEE-754 float payloads even though the property code is `6`.
The current generic property decoder reads code `6` as `uint32_t` and only normalizes `TravelDays` specially.
Consequently:

- source `1.0` appears as `1065353216`;
- source `5.0` appears as `1084227584`; and
- source `10.0` appears as `1092616192`.

Add a property-specific `ActivationCount` normalization with unit coverage. Do not reinterpret every code-6 property
as float; other code-6 properties are genuine integer fields.

## Recovered Native Semantics

### Touch lifecycle

MM9 does not expose a generic trigger-volume `enter`, `stay`, or `leave` event.

The source behavior is:

1. A player or actor moves.
2. LithTech collision processing detects overlap with a nonsolid trigger object's axis-aligned bounds.
3. The trigger receives a touch notification for the moving object.
4. The trigger applies enabled, active, occurrence, player/AI, optional AI-name, and cooldown gates.
5. An accepted touch stores the touching object as sender and requests activation.
6. Remaining motion while overlapping may produce later touch notifications. `TriggerDelay`, pending activation state,
   and `ActivationCount` determine whether those later notifications have an effect.
7. Leaving the box emits no callback. It only ends future overlap notifications.

OpenYAMM may retain ephemeral overlap/contact data to deduplicate the same collision within one simulation step, but
that implementation detail must not become a source-visible `OnLeave` event or replace native cooldown and activation
rules.

The inherited DAT property named `TouchNotify` is not the switch that makes ordinary `Trigger` objects work. Most
shipped triggers have it disabled, including functional trigger volumes. Trigger class behavior supplies its native
touch path.

### Activation and fanout

Required semantics are:

- `StartOn` initializes the enabled state.
- `OFF` disables the trigger.
- `ON` enables the trigger and resets its successful activation count.
- `TRIGGER` resets its successful activation count and requests routed/manual activation using the command sender.
- A touch activation does not reset the count.
- `ActivationCount = 0` means unlimited successful activations.
- A positive `ActivationCount` is the maximum number of successful fanouts before further touch activation is
  rejected.
- `TriggerDelay` throttles accepted touch notifications.
- `SendDelay` delays fanout after accepted activation and retains the sender needed by touch-back or compiled target
  behavior.
- While one delayed activation is pending, the native active gate prevents a second overlapping activation request.
- Output slots are processed in source order from 1 through 10.
- Target and message matching is case-insensitive for command selection, while source spelling remains in provenance.
- Native name dispatch can address all currently live objects with the target name.
- If `WeightedTrigger` is enabled, slot 1 versus slot 2 is selected by `Message1Weight`; slots 3 through 10 remain
  ordinary outputs.
- `TriggerTouch` sends `MessageTouch` back to the touching sender after normal output fanout when both fields are
  effective.
- `ActivationSound` plays at the trigger position with `SoundRadius` when successful fanout occurs.
- Timed triggers schedule repeated activations between `MinTriggerTime` and `MaxTriggerTime`.

The shipped maps do not enable weighted, timed, locked, occurrence-percentage, named-AI, attachment, or non-empty
touch-back behavior. The importer must preserve those fields. The runtime must either implement their recovered
high-confidence semantics or reject future enabled use through validation; it must not silently ignore a newly
enabled authored property.

Access-key, access-message, and access-sound fields must remain represented with provenance. If their complete native
consumer cannot be proven, classify them as source-unused in the shipped audit and leave them outside shipped
completion rather than inventing UI behavior.

### ExitTrigger

`ExitTrigger` is a separate typed object, not merely an ordinary `Trigger` with a destination payload.

Required behavior is:

- preserve the existing resolved destination, arrival, facing, confirmation, travel-day, and loading-presentation
  data;
- initialize enabled state from `StartOn`;
- accept player touch activation when enabled;
- accept `OPEN` or `TRIGGER` command activation when enabled;
- accept `ON` and `OFF` commands to change enabled state;
- retain the activation sender long enough for prompt/transition policy that needs it;
- queue a transition request through the shared transition runtime; and
- defer committing an automatic transition until the current trigger output batch has completed.

An `ExitTrigger` may therefore participate in both spatial collision and the named command graph. Do not create two
independent state records for those roles.

### PortalTrigger

The single shipped `PortalTrigger` has `PortalName` and `StartOn` but no `Dims`. It is a named portal-control object,
not a touch volume. Preserve and audit it separately. Do not insert it into the ordinary trigger collision list until
its exact command/portal-side-effect contract is recovered and required.

## Generated Definition Contract

Add one authoritative generated map-local representation for ordinary DAT `Trigger` objects. A suitable scene shape
is provisionally:

```yaml
mm9_triggers:
  - source_object_index: 216
    source_class: "Trigger"
    source_name: "Trigger0"
    source_script: ""
    position: {x: 34775, y: 12411, z: 1289}
    half_extents: {x: 128, y: 384, z: 128}
    source_rotation_lt: [0, 0, 0, 0]
    touch:
      player: true
      ai: false
      ai_only: false
      ai_name: ""
      occurrence: 1.0
      trigger_delay_ms: 0
    activation:
      initially_enabled: true
      initially_locked: false
      activation_limit: 1
      send_delay_ms: 0
      activation_sound: ""
      sound_radius: 200
    outputs:
      - slot: 1
        target_name: "ExitTrigger0"
        resolved_source_object_indices: [217]
        message: "trigger"
      - slot: 2
        target_name: "CommonerHuman2MaleA0"
        resolved_source_object_indices: [207]
        message: "Leave"
```

The exact field layout may be refined during implementation, but it must preserve equivalent information and these
ownership rules:

- `target_name` is the authoritative native routing key.
- Resolved source indexes are deterministic generation evidence and a fast path for static objects, not permission to
  discard the target name or ignore dynamically created named objects.
- A zero-size or non-touchable trigger remains a valid command/logic node if it has inputs or outputs.
- Position and dimensions use the existing LT-to-OpenYAMM axis mapping and coordinate scale.
- `Dims` are half-extents after axis mapping and absolute-value normalization.
- Source rotation is retained but does not rotate collision bounds.
- Output slots remain ordered and sparse source slot numbers are retained.
- Empty target/message pairs are not synthesized.
- Source class, assigned script, and all dormant native fields remain available to validation and diagnostics.

Do not maintain both the current destructible-only `trigger_volumes` representation and a second general trigger
representation. Replace the specialized ownership and route destructible commands through the general command path.

### Exit definition contribution

Keep destination and arrival data in `assets_dev/worlds/mm9/data_tables/map_transitions.txt`. Extend that contribution
and its loader with data equivalent to:

- `StartOn`/initially enabled;
- source script identity;
- stable receiver identity by source map and source object index; and
- any required native activation metadata not already present.

The trigger runtime references the transition definition by stable source identity. Do not duplicate destination,
arrival, travel, or prompt data into ordinary scene trigger records.

## Runtime Ownership

### Map object command registry

Create one active-map MM9 command registry populated only while an MM9 map is loaded. Every participating typed map
object registers:

- stable source object index;
- source class;
- source name;
- live runtime identity or typed receiver handle; and
- supported native or compiled commands.

Name lookup is case-insensitive and returns every live object with the authored target name. Static generation audits
may report unique bindings, but runtime routing must not hardcode single-object semantics.

The registry must not own target state. It invokes typed receivers such as:

- ordinary trigger state;
- positioned transition state;
- door, rotating-door, lift, switch, and mechanism state;
- destructible state;
- actor/native command state;
- sound, fire, shooter, spawner, earthquake, damage-brush, perception, or other imported object-family state; and
- explicit compiled script hooks.

An unsupported command returns a structured result containing map, source trigger, slot, target name, resolved target
identity, target class, and message. Required progression commands must fail the relevant content validation or test;
they must not silently report success.

### Command context

Each dispatch carries context equivalent to:

- source map canonical id;
- source trigger object index;
- target slot;
- target name and message;
- activation kind: touch, routed/manual, or timed;
- sender/touching runtime object identity when present;
- activation position and simulation time; and
- optional source script provenance.

Sender identity is mandatory for Yanmirsfort and any compiled callback using `GetParam 0`. Do not substitute the party
for a missing sender.

### Trigger state

Store mutable state separately from generated definitions. At minimum:

```text
enabled
locked
successful activation count
touch cooldown remaining or last accepted touch time
pending delayed activation flag
pending activation due time
pending activation kind
pending sender stable identity
next timed activation when applicable
```

An ephemeral per-step contact set may prevent duplicate collision reports in the same movement integration. It is not
source state and should not be serialized as an `inside`/`left` gameplay flag.

### Dispatch transaction

A successful fanout is one ordered command batch:

1. Validate enabled, lock, occurrence, filter, cooldown, pending state, and activation limit.
2. Record sender and schedule `SendDelay`, or begin immediately when the delay is zero.
3. Revalidate the activation limit at fanout time where required by native behavior.
4. Select weighted slots when enabled.
5. Dispatch source slots 1 through 10 synchronously and in order.
6. Dispatch optional touch-back message.
7. Play activation sound.
8. Increment successful activation count.
9. Publish queued map transition or other deferred world operation only after the batch completes.

Do not partially persist a batch halfway through output dispatch. A save request or map transition arising during the
batch observes the completed logical activation.

## Collision Integration

Use shared movement-produced contacts rather than a party-only full-map scan.

For each moving eligible object:

- use its current collision bounds and previous/current movement segment;
- test against candidate trigger AABBs through a spatial index or active-map broad phase;
- expand the trigger bounds by the mover's half-extents, or use an equivalent swept AABB/capsule test;
- report at most one touch per mover/trigger pair per movement integration;
- retain contacts for player and AI filtering after broad-phase detection; and
- avoid tunneling through thin source volumes.

Do not require the mover's center to enter the unexpanded trigger box. Several exits and ordinary triggers have thin
dimensions for which center-point sampling is observably incorrect.

Loading or spawning with the party already intersecting a trigger must not synthesize an activation before the first
qualifying movement contact. This matches the movement-driven source model and prevents immediate transitions at map
load.

## Script Compilation Boundary

Trigger routing does not authorize a general SCR runtime.

The generator must classify each target message as one of:

1. a supported native typed receiver command;
2. an existing strict compiled callback;
3. an explicit reviewed map/encounter overlay;
4. a dynamically named target that can be validated only at runtime; or
5. unresolved/unsupported with source provenance.

For required script callbacks:

- compile only the callback registered for the incoming message and routines transitively reached from it;
- bind state by map source object identity, not only script filename;
- preserve sender parameters required by the routine;
- call shared OpenYAMM operations for keys, items, transitions, actor removal, mechanisms, sounds, and other effects;
- reject unsupported reachable commands at generation time for required bindings; and
- keep generated Lua generated.

Do not compile unrelated includes, generic combat AI, navigation, wandering, or conversation behavior merely because
the same SCR file contains it.

## Required Acceptance Cases

### Bootcamp completion trigger

Source objects:

- ordinary trigger 216, `Trigger0`;
- exit trigger 217, `ExitTrigger0`;
- actor 207, `CommonerHuman2MaleA0`, assigned `NPC436.scr`.

Required result:

1. A qualifying party movement contact activates trigger 216 exactly once from its source `ActivationCount = 1`.
2. Slot 1 sends `trigger` to exit 217.
3. Exit 217 queues an automatic transition to Isle of Ashes using `StartPoint0`, six travel days, and no confirmation.
4. Slot 2 sends `Leave` to actor 207 before the transition commits.
5. The strict compiled `NPC436.scr` `OnLeave` callback grants raw key 473 through the existing MM9 key/QBit mapping.
6. Remaining inside the trigger does not repeat the one-shot fanout.
7. Save/load after activation does not grant key 473 or queue the transition again from the exhausted touch trigger.

The `Leave` label in this case is receiver script policy, not a volume-leave event.

### Yanmirsfort end-of-world trigger

Source objects:

- ordinary trigger 611, `EndOfWorldTrigger`, assigned `Yanmir_EndOfWorld.scr`;
- disabled exit trigger 612, `PlayerExit`.

Required result:

1. Touching trigger 611 sends `OutOfWorld` to its own named receiver.
2. The compiled callback receives the actual touching object as parameter zero.
3. A player toucher sends `ON` and then `TRIGGER` to exit 612 and reaches the resolved Frosgard City transition.
4. Yanmir touching the same trigger follows the source Yanmir branch rather than transitioning the party.
5. Another actor toucher follows the source actor-removal branch.
6. Direct spatial overlap with exit 612 while it is disabled does not transition the party.

This case proves sender propagation, AI touch support, self-targeted trigger messages, and disabled-exit command
activation.

### Thronheim City prison breakout

Source objects:

- trigger 78, `BadAssTrigger`;
- trigger 79, `BadAssTrigger0`;
- actor 66, `BadAss`, assigned `ThronHeimCity_BadAss.scr`;
- destructible prison wall 65.

Required result:

1. Either trigger delivers `Breakout` to actor 66.
2. The encounter profile starts only once even though both source triggers are unlimited.
3. The actor reaches the source-defined wall-breaking sequence.
4. The wall receives `Destroy` through the same command runtime.
5. Rendering, collision, navigation, picking, LOS, and persistence update through the destructible subsystem.

This goal owns the trigger delivery. The destructible and scripted-actor goals own their respective downstream state.

### Disabled exits

Add focused coverage proving that all imported `StartOn = 0` exits ignore touch and `TRIGGER` until enabled, accept
`ON`, transition when subsequently activated, accept `OFF`, and retain enabled state across save/load where the map
state is persistent.

### Repeat, delay, and counter behavior

Add pure/unit coverage for:

- unlimited touch activation;
- one-, five-, and ten-use activation limits;
- `ON` and routed `TRIGGER` counter reset semantics;
- touch cooldown independent from send delay;
- one pending delayed activation at a time;
- sender survival through delayed fanout;
- ordered slot dispatch;
- weighted slot 1/2 selection with later slots unaffected;
- occurrence rejection not incrementing successful activation count; and
- activation sound occurring only on successful fanout.

### Collision behavior

Add focused headless coverage for:

- swept party contact with a thin trigger;
- party collider overlap when the center remains outside the raw trigger bounds;
- AI-only and player-disabled filters;
- movement while overlapping and cooldown handling;
- no synthetic `leave` callback;
- no immediate activation merely because a map loads with the party already overlapping; and
- no duplicate contact from one movement integration.

## Persistence Contract

Persist trigger state through the shared save/map-delta system, keyed by canonical map id and source object index.

Required saved data includes:

- enabled and locked state;
- successful activation count;
- cooldown remaining;
- pending delayed activation and remaining delay;
- pending activation kind and stable sender identity when still valid;
- next timed activation remaining when timed behavior is supported; and
- source-specific compiled callback state owned by the target object.

Serialize remaining durations rather than process-local absolute clocks. On load:

- rebuild definition and receiver indexes from mounted content;
- validate saved source identities against the active map package;
- restore pending state only when its definition still matches;
- resolve a saved sender through stable runtime identity;
- clear only a sender reference that can no longer exist, while retaining source-equivalent output behavior that does
  not require it; and
- never resurrect a removed target or infer a replacement by name proximity.

Ephemeral collision-contact sets are rebuilt after load and are not persistent gameplay state.

## Import And Audit Work

### Property normalization

- Add property-specific normalization for `ActivationCount` code-6 float payloads.
- Retain raw bytes and decoded semantic values in diagnostics.
- Add tests for 0, 1, 5, and 10 and prove unrelated code-6 integer properties remain integers.

### Trigger graph generation

- Generate all 482 ordinary trigger records, including command-only and zero-size nodes.
- Emit all non-empty source target/message slots in authored order.
- Retain target names even when static resolution succeeds.
- Record every statically resolved source object index and class.
- Record unresolved targets without dropping them.
- Classify each target command by expected receiver family when source class is known.
- Record source script attachment and callback binding evidence.
- Replace the destructible-only trigger emission path rather than layering a second owner over it.

### Generated audit

Emit a deterministic world-owned audit, provisionally
`assets_dev/worlds/mm9/import/trigger_graph_audit.yml`, containing at least:

- source-map and class census;
- property distributions;
- trigger definitions emitted/skipped;
- output-slot count;
- static target resolution cardinality;
- unresolved target names;
- target class/message inventory;
- native receiver coverage;
- compiled callback coverage;
- explicit overlay coverage;
- dormant native property use;
- zero-size and command-only classification;
- disabled exit inventory;
- duplicate source identity or name findings; and
- errors that block required progression behavior.

The audit is generated evidence, not a hand-maintained allowlist. Reviewed exceptions belong in a narrow source
override with an id, reason, evidence, and review state.

### Validation policy

Generation/content composition must fail for:

- duplicate trigger source ownership;
- malformed position or dimensions on a required touch trigger;
- invalid activation count or delay values;
- a required source output lost during conversion;
- a required statically resolvable target resolving to the wrong class or identity;
- a required custom script message with no compiled hook or reviewed overlay;
- an enabled unsupported dormant property; or
- a required exit lacking valid transition data.

Static unresolved names that are proven to be runtime-created may remain as name-routed outputs with explicit audit
classification. Unknown unresolved names must not be silently reclassified as dynamic.

## Implementation Milestones

### Milestone 1: Reproducible source audit

- Add `ActivationCount` normalization and parser tests.
- Add deterministic trigger and exit census generation.
- Produce the target class/message and unresolved-name inventories.
- Establish checked-in Bootcamp, Yanmirsfort, and Thronheim source fixtures.

### Milestone 2: Generated definition and loaders

- Emit every ordinary trigger into the authoritative map-local definition.
- Extend transition definitions with initial enabled state and script provenance.
- Parse definitions into semantic MM9 map data not owned by outdoor rendering.
- Remove the destructible-only trigger action representation after receiver routing replaces it.

### Milestone 3: Command registry and trigger state machine

- Add active-map object registration and case-insensitive plural name lookup.
- Implement `ON`, `OFF`, `TRIGGER`, activation limits, cooldown, send delay, ordered fanout, and diagnostics.
- Route destructibles and existing mechanisms through their authoritative services.
- Queue transition publication until command-batch completion.

### Milestone 4: Shared movement contact integration

- Produce swept contacts for party and AI colliders.
- Add active-map broad-phase lookup so contact work scales with nearby trigger volumes.
- Remove party-center fresh-entry ownership from the old ordinary-trigger and exit paths.
- Preserve safe map-load initialization without synthetic activation.

### Milestone 5: ExitTrigger integration

- Make spatial touch and object commands share one exit enabled state.
- Connect `OPEN`, `TRIGGER`, `ON`, and `OFF` to the existing transition service.
- Preserve confirmation, cancellation, travel, arrival, and loading presentation.
- Validate all six disabled shipped exits.

### Milestone 6: Required compiled callbacks and overlays

- Compile Bootcamp NPC436 `Leave -> OnLeave` and grant raw key 473.
- Compile the required Yanmirsfort `OutOfWorld` callback with sender identity.
- Connect Thronheim `Breakout` to the reviewed encounter profile.
- Classify remaining required script-target messages and fail rather than silently omit unsupported progression paths.

### Milestone 7: Save/load and completion validation

- Persist trigger and exit mutable state.
- Cover delayed activation and sender restoration.
- Run focused headless map cases.
- Validate affected MM6/MM7/MM8 transition, door, destructible, event, movement, and save/load paths.
- Record performance and memory behavior with MM9 mounted and unmounted.

## Testing And Verification

### Unit coverage

Prefer doctest coverage for:

- property normalization;
- trigger definition parsing and validation;
- case-insensitive plural target lookup;
- activation limits and counter reset;
- cooldown versus send delay;
- weighted selection;
- ordered dispatch;
- save-state round trips; and
- exit enabled-state commands.

### Focused headless coverage

Use headless runtime tests for:

- Bootcamp source objects 216, 217, and 207;
- Yanmirsfort source objects 611 and 612 with player and actor touchers;
- Thronheim City source objects 78, 79, 66, and 65;
- a thin positioned exit;
- one AI-triggerable map case;
- one delayed trap chain;
- one trigger-to-trigger `ON`/`OFF` chain; and
- save/load before touch, during delay, after fanout, and after map re-entry.

### Regression coverage

At minimum validate:

- MM6/MM7/MM8 ordinary map transitions and boundary exits;
- classic ODM and BLV movement/collision;
- shared door and mechanism commands;
- destructible rendering/collision/navigation state;
- event execution and transition confirmation/cancellation;
- party and actor movement performance; and
- save/load with an MM9 world mounted and with MM9 absent.

Development build command:

```bash
cmake --build build --target openyamm -j25
```

Run focused unit and headless test targets in proportion to the implemented milestone before broader suites.

## Diagnostics

Provide concise opt-in diagnostics for:

- accepted and rejected touch activation with rejection reason;
- `ON`, `OFF`, and `TRIGGER` state changes;
- delayed activation scheduling and completion;
- ordered output slot dispatch;
- target name resolution and receiver class;
- unsupported message handling;
- compiled callback or overlay selection;
- transition queueing after batch completion; and
- save/load trigger-state restoration.

Keep verbose per-frame overlap logs out of normal builds and final changes. Diagnostics must use stable map and source
object identities so regenerated scene indexes do not invalidate traces.

## Completion Gates

This goal is complete only when all of the following are true:

- [ ] The parser decodes shipped `ActivationCount` values semantically and preserves raw provenance.
- [ ] A checked-in deterministic audit accounts for all 482 ordinary triggers, 105 exits, one portal trigger, and all
      1,394 ordinary trigger outputs.
- [ ] Ordinary trigger generation no longer filters behavior down to destructible-only actions.
- [ ] Command-only, zero-size, player, and AI trigger nodes are represented correctly.
- [ ] Trigger collision uses moving colliders and swept AABB-equivalent contact rather than party-center entry tests.
- [ ] No generic MM9 trigger `OnLeave` callback is invented.
- [ ] Ordered, case-insensitive, plural named-object command routing works.
- [ ] `ON`, `OFF`, `TRIGGER`, activation limits, cooldown, send delay, sender propagation, and activation sound follow
      recovered semantics.
- [ ] Exit spatial touch and command activation share one persisted enabled state.
- [ ] All six disabled shipped exits remain inactive until enabled.
- [ ] Bootcamp trigger 216 transitions the party and grants raw key 473 through its second output before map commit.
- [ ] Yanmirsfort trigger 611 distinguishes player, Yanmir, and other actor senders and activates disabled exit 612 only
      on the player path.
- [ ] Either Thronheim City breakout trigger reaches the existing actor/destructible encounter outcome.
- [ ] Required custom messages have typed receivers, strict compiled hooks, or reviewed overlays; required progression
      messages never disappear as no-ops.
- [ ] Trigger and exit mutable state survive save/load and map re-entry without duplication.
- [ ] Generated files remain generated and regenerate deterministically.
- [ ] MM6/MM7/MM8 gameplay, rendering, collision, transitions, events, save/load, startup, and runtime performance show
      no regression.
- [ ] With MM9 unmounted, the trigger subsystem adds no meaningful startup, map-load, update, or memory cost.

