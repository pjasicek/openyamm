# MM9 Lossless Mechanism Integration Investigation

This note records the current investigation into preserving and implementing Might and Magic IX map mechanisms in
OpenYAMM. The target is lossless import first, then faithful runtime behavior. "Lossless" is the key requirement:
mechanism-related source data from MM9 DAT objects, generated geometry, and scripts must survive import even when the
engine cannot yet execute every behavior.

The recommendation is to avoid forcing MM9 mechanisms into legacy ODM/BLV door records as the authoritative model.
MM9 mechanism authorship is object and script based. ODM/BLV geometry can be a runtime target, but the source truth
should be a per-map MM9 event sidecar with stable references back to raw DAT objects and source scripts.

## Source Material Checked

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`
- `docs/mm9/MM9_IMPORT_TOOLCHAIN.md`
- `mm9/mm9_openyamm_integration_handoff.md`
- `tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py`
- `tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py`
- `assets_dev/worlds/mm9/maps/*.raw_objects.yml`
- `assets_dev/worlds/mm9/maps/*.scene.yml`
- `assets_dev/worlds/mm9/maps/*.mm9.yml`
- `assets_dev/worlds/mm9/maps/*.bsp.yml`
- `assets_dev/worlds/mm9/maps/*.geometry.yml`
- `assets_dev/worlds/mm9/maps/*.material_aliases.yml`
- `assets_dev/worlds/mm9/maps/*.model_assets.yml`
- `mm9/extracted/SCRIPTS/SCRIPTS/*.scr`
- `mm9/extracted/SCRIPTS/SCRIPTS/*.inc`
- `mm9/mm9_tools/script.txt`
- `game/maps/OutdoorSceneYml.*`
- `game/events/EventRuntime.*`
- `game/outdoor/OutdoorWorldRuntime.cpp`
- `game/scene/IndoorSceneRuntime.cpp`
- `game/maps/MapDeltaData.h`

The existing importer has already parsed all currently available MM9 DAT files as a local DAT v66 variant. The format
notes report:

- 45 DAT files parsed.
- 12,671 world models decoded.
- 32,288 object instances decoded.
- 460 user portals decoded.
- 672,656 leaf references decoded.
- 0 invalid decoded references in the current corpus.

The importer also preserves raw object payloads in `*.raw_objects.yml`. This is essential. For mechanisms, the raw
object payload and decoded properties are more authoritative than any lossy conversion into ODM/BLV concepts.

## Main Finding

MM9 mechanisms are not just "doors" in the MM6-MM8 BLV sense. They are authored as LithTech-style server objects,
script objects, props, trigger volumes, movers, rotating brushes, water volumes, ladders, destructible blockers,
animated model swaps, and named message targets. A map mechanism is often the combination of:

- a source DAT object with class-specific properties;
- optional geometry, model, volume, or collision representation;
- optional script name and script parameters;
- named trigger messages sent to other objects;
- state flags such as visible, solid, locked, start open, or start on;
- sounds and animation names;
- movement commands such as `MoveToPos`, `MoveDir`, and `Rotate`.

Because MM9 uses this object and message graph, a lossless OpenYAMM import should preserve the graph directly. Legacy
ODM/BLV mechanisms can be generated as compatibility/runtime targets only when they are an exact fit.

## DAT Object Mechanism Classes

The MM9 raw object sidecars contain 282 object classes across 32,288 objects. The following classes are the main
mechanism carriers or mechanism-adjacent objects observed in the generated `*.raw_objects.yml` data:

| Class | Count | Mechanism relevance |
| --- | ---: | --- |
| `Door` | 757 | Linear/sliding door object with move direction, distance, speeds, lock state, trigger outputs, sounds, and touch/use behavior. |
| `RotatingDoor` | 1,017 | Pivoting door object with rotation point, rotation angles, open-away behavior, lock state, trigger outputs, and sounds. |
| `WeightedLift` | 14 | Lift/pressure platform variant using door-like movement, touch/weight behavior, delays, and wait times. |
| `RotatingBrush` | 15 | Continuous or triggerable rotating brush/machinery with axis flags, start-on state, sounds, damage, and collision. |
| `Trigger` | 482 | Volume/message dispatcher with dimensions, target/message slots, touch/use gating, timed behavior, unlock key, and sounds. |
| `ScriptObject` | 110 | Invisible script brain used to sequence map events and route messages. |
| `Prop` | 5,840 | Model instance carrier; many props have scripts, can move, hide, animate, change model, or forward triggers. |
| `WorldObject` | 1,120 | World object carrier; can have scripts and authored transform/visibility/physics properties. |
| `InvisibleBrush` | 297 | Invisible collision or trigger blocker, often manipulated by scripts. |
| `DestructableBrush` | 261 | Destroyable or stateful blocker/geometry object. |
| `DestructableProp` | 174 | Destroyable model object. |
| `BlueWater` | 70 | Water volume/surface object with hidden/show-surface/fog/physics/damage state. |
| `Ladder` | 68 | Climb volume object with dimensions, visibility/hidden state, and scripts in some maps. |
| `Shooter` | 169 | Trap/projectile source object, generally activated by trigger/message state. |
| `AIBarrier` | 294 | AI navigation blocker that can participate in mechanism state. |
| `PerceptionBrush` | 289 | Visibility/perception volume that may be toggled or script controlled. |
| `Marker` | 735 | Named point used by scripts as destinations, pivots, or references. |

Other classes can still matter. Losslessness requires preserving every source object and all decoded/raw properties,
not only the classes listed above.

## Common Door-Like Properties

The raw object corpus shows a consistent property set across `Door`, `RotatingDoor`, and `WeightedLift`. These should
map to a normalized mechanism IR without dropping original values:

- Identity and transform:
  - `Name`
  - `Pos`
  - `Rotation`
  - `Scale`
  - `Filename`
  - `Skin`
- Script:
  - `ScriptName`
  - `ScriptParams`
  - `Parameters`
  - `StartOn`
- Basic physical state:
  - `Visible`
  - `Solid`
  - `Rayhit` or `RayHit`
  - `MoveToFloor`
  - `BoxPhysics`
- Door motion:
  - `Speed`
  - `ClosingSpeed`
  - `MoveDelay`
  - `OpenWaitTime`
  - `MoveDir`
  - `MoveDist`
- Rotating-door motion:
  - `RotationPoint`
  - `RotationAngles`
  - `OpenAway`
- Activation:
  - `StartOpen`
  - `PushOpen`
  - `TouchToOpen`
  - `AutoTrigger`
  - `Locked`
  - `ReopenOnContact`
  - `DoubleDoorName`
  - `TriggerDims`
  - `LockJiggleSpeed`
- Sounds:
  - `Sounds`
  - `SoundPos`
  - `OpenStartSound`
  - `OpenBusySound`
  - `OpenStopSound`
  - `CloseStartSound`
  - `CloseBusySound`
  - `CloseStopSound`
  - `JiggleSound`
- Trigger outputs:
  - `OpenTriggerTarget0` through `OpenTriggerTarget3`
  - `OpenTrigger0` through `OpenTrigger3`
  - `CloseTriggerTarget0` through `CloseTriggerTarget3`
  - `CloseTrigger0` through `CloseTrigger3`

These fields should not be flattened to a single "door tag". The raw property names and values need to remain
recoverable, because some behavior may depend on exact class semantics or on fields that are only partially understood.

## Trigger Object Properties

`Trigger` objects are first-class mechanism routers. They should not be reduced to a single legacy face event.
Observed important properties include:

- `Name`
- `Pos`
- `Rotation`
- `Dims`
- `StartOn`
- `Visible`
- `Rayhit` or `RayHit`
- `TriggerTouch`
- `MessageTouch`
- `PlayerTriggerable`
- `AITriggerName`
- `WeightedTrigger`
- `TimedTrigger`
- `MinTriggerTime`
- `MaxTriggerTime`
- `SendDelay`
- `TriggerDelay`
- `UnlockKey`
- `AccessDeniedMsg`
- `LockedSound`
- `UnlockedSound`
- `ActivationSound`
- `TargetName1` through `TargetName10`
- `MessageName1` through `MessageName10`

This means the importer needs to preserve ordered trigger outputs. A target/message pair is part of the authored
mechanism graph even if the target cannot be resolved during import.

## Script Command Surface

The script corpus confirms that mechanisms are also script-driven. The following mechanism-relevant command counts
were found by scanning the extracted `.scr` and `.inc` files:

| Command/pattern | Lines | Files | Meaning for mechanisms |
| --- | ---: | ---: | --- |
| `MoveToPos` | 68 | 54 | Move current object to an absolute position, often a marker position. |
| `MoveDir` | 25 | 12 | Move current object along a direction for a distance/rate, or continuously if distance is zero. |
| `Rotate` | 2 | 1 | Rotate current object around an arbitrary axis by degrees and rate. |
| `SetPos` | 67 | 47 | Teleport or reset object position. |
| `SetFlag` / `ClearFlag` | 513 | 92 | Toggle visibility, solidity, gravity, go-through-world, and other object flags. |
| `SetStat` / `GetStat` | 291 | 85 | Query or set object state, especially door state and locking. |
| `Trigger` | 1,573 | 320 | Send named messages to objects. |
| `AddTrigger` | 1,289 | 577 | Register script callbacks for named messages. |
| `PlayAnim` | 382 | 134 | Play named model animations as part of a mechanism. |
| `SetModelFilenames` | 27 | 19 | Swap model and skin. |
| `OnTouchNotify` | 35 | 17 | Register touch/collision callbacks. |

The `mm9/mm9_tools/script.txt` reference describes the core movement commands:

- `MoveToPos x,y,z,{rate=0},{callback}` moves the current object to a position. `rate=0` means instant.
- `MoveDir x,y,z,{dist=0},{rate=0},{callback}` moves along a direction. `dist=0` means continuous movement.
- `Rotate xAxis,yAxis,zAxis,degrees,{rate=0},{callback}` rotates the current object around an axis.
- `Trigger hObject,string` sends a trigger message to another object.
- `AddTrigger name,callback` registers a callback for a trigger message.
- `GetPos` and `SetPos` read/write object positions.
- `GetDims` and `SetDims` read/write object dimensions.
- `PlayAnim` and `LoopAnim` drive model animations.
- `SetModelFilenames` swaps model/skin names.
- `OnTouchNotify` creates touch-driven callbacks.

The exact runtime units for script rates should not be guessed into the final schema. They appear to be LithTech-world
rate units, but until calibrated they should be preserved as source units and annotated as such.

## Script Examples That Matter

These scripts show the variety of mechanism behavior that must survive import:

- `DOORLOCK.scr`
  - Registers `AddTrigger use OnUse`.
  - Checks key/item requirements.
  - Calls `SetStat g_hmyobject,Locked,FALSE`.
  - Optionally consumes the key and can relock.
  - Implication: locking is a script-visible state, not just an import-time flag.

- `TALADDERMOVE.scr`
  - Captures the original ladder position.
  - Trigger `Lower` calls `MoveToPos nOrigPosX, nOrigPosY-Distance, nOrigPosZ, Rate`.
  - Parameters define distance and rate.
  - Implication: ladders can be moving mechanisms and need dynamic volume/collision support.

- `MOVEHOTWATER.scr`
  - Uses a marker object name from parameters.
  - Resolves marker position through `GetObjectHandle` and `GetPos`.
  - Moves the current object to that marker with `MoveToPos`.
  - Implication: script motion often depends on named object references, not inline coordinates.

- `WATERTRAP.scr`
  - Supports `SinkWater`, `FillWater`, and `ToggleWater`.
  - Moves water between original position and original position plus configured distance.
  - Tracks a fill speed accumulator and lower speed.
  - Implication: water mechanisms need stateful motion and volume/surface updates.

- `WATER.inc`
  - Generic water sink/fill/toggle include.
  - Uses `GetDims` to derive sink distance from water volume dimensions.
  - Implication: dimensions are authored behavior inputs.

- `BASEDOOR.inc`
  - Lets AI detect a door, stop, face it, trigger `Use`, wait `DoorOpenTime`, then resume path.
  - Implication: door mechanisms affect AI pathing and cannot be visual-only.

- `BLADETRAP.scr`
  - Uses `MoveDir` sequences.
  - Implication: traps may be kinematic objects with damage/collision, not just animations.

- `CAGE.scr`
  - Uses the script `Rotate` command.
  - Implication: arbitrary script rotation exists even if it is rare in the corpus.

- `DARKP_RAISINGBRIDGE.scr`
  - Uses top/down marker names and `MoveToPos` with rate `180`.
  - Trigger `Move` toggles bridge state.
  - Implication: bridge state and destination markers must be represented.

- `DARKP_RAISINGSWITCH.scr`
  - Uses `PlayAnim`, then triggers a puzzle manager.
  - Implication: animated switches can be part of the same mechanism graph as movers.

- `YF_FALLINGFLOOR.scr`
  - Clears/sets flags, moves to a marker with high speed, destroys blocker/beam objects, and removes itself.
  - Implication: mechanisms can combine visibility, collision, movement, destruction, and object lifecycle.

- `HIDEMODEL.scr`
  - Toggles visible/solid/gravity-like flags based on key ownership.
  - Implication: model visibility and collision flags are mechanism state.

- `CHANGEMODEL.scr`
  - Calls `SetModelFilenames`.
  - Implication: model-swap state is part of mechanism behavior.

- `PROPTRIGGER.scr`
  - Lets props forward touch/use messages to configured target objects.
  - Implication: message forwarding must be modeled, not only direct trigger volumes.

## Existing OpenYAMM Mechanism Support

OpenYAMM already has partial mechanism support, but it is not rich enough to be the MM9 source model.

### Indoor BLV Path

`MapDeltaDoor` in `game/maps/MapDeltaData.h` represents a legacy BLV-style moving door:

- face offsets;
- vertex offsets;
- sector offsets;
- direction;
- move length;
- open/close speed;
- state;
- event id.

`IndoorSceneRuntime.cpp` advances these mechanisms and updates indoor geometry/pathing state. This works for
MM6-MM8-style BLV doors, but it cannot losslessly represent:

- arbitrary source object identity;
- named trigger/message graph;
- rotations around arbitrary pivots;
- continuous rotating brushes;
- script-driven marker destinations;
- visibility/solid/rayhit/model-swap changes;
- water/ladders/volumes;
- multiple target object types;
- original MM9 raw property values.

### Outdoor Path

`EventRuntime` has `OutdoorModelMechanismDefinition`, and `OutdoorWorldRuntime.cpp` can currently translate an outdoor
bmodel by a configured vector. This is useful as a runtime target, but it is limited:

- movement is translation-only;
- no rotation or arbitrary pivot;
- no source object graph;
- no Trigger object volume semantics;
- no model instance mover support;
- no source script command IR;
- no audio/animation/model-swap integration;
- no complete collision/AI/pathing integration for MM9 semantics.

This should be extended, but it should not become the only MM9 mechanism representation.

## Why ODM/BLV Alone Is Not Enough

MM9 does not cleanly match the older split where outdoor mechanisms are a small extension to ODM bmodels and indoor
mechanisms are BLV doors. The generated ODM/BLV geometry is an OpenYAMM compatibility representation of MM9 world data,
not the original authorship model.

Forcing MM9 mechanisms into ODM/BLV alone would lose information:

- source object class names;
- raw object property payloads;
- script names and parameters;
- Trigger target slots beyond a single event id;
- marker-based destinations;
- touch/use/AI/timed trigger details;
- lock/jiggle/reopen/double-door semantics;
- arbitrary rotations and continuous rotating brushes;
- model swaps and animations;
- visibility/solid/rayhit/dimensions changes;
- unresolved or currently unknown source fields.

The right split is:

- ODM/BLV geometry remains render/collision representation.
- A source-first MM9 event sidecar remains the authored behavior representation.
- Runtime binders connect source mechanisms to BLV faces, ODM bmodels, model instances, volumes, or script objects.

## Recommended Import Artifact

Add a generated per-map sidecar:

```text
assets_dev/worlds/mm9/maps/<map>.events.yml
```

This file should be generated from `*.raw_objects.yml`, source scripts, and generated geometry metadata. It should not
replace the raw object sidecar. It should be a normalized index that keeps source references and makes runtime binding
practical.

Embedding event data into `<map>.scene.yml` is possible, but a sidecar is cleaner because:

- it keeps static scene geometry stable;
- it can be regenerated and diffed independently;
- it can preserve unresolved bindings without polluting render-only scene data;
- it can grow script IR and validation reports without changing the core scene schema.

The scene or map metadata can reference the event sidecar explicitly:

```yaml
events: <map>.events.yml
scripts:
  level: events/<map>.lua
  mechanisms: events/<map>.mechanisms.lua
```

The expected runtime artifact set for an MM9 map is:

- `<map>.scene.yml` or generated ODM/BLV/static scene data;
- `<map>.raw_objects.yml` as source/debug/import truth;
- `<map>.events.yml` as the normalized lossless behavior index;
- generated per-map Lua, split as desired between general map behavior and mechanism-specific behavior.

The raw object sidecar does not need to be loaded in normal gameplay once validation is trusted, but the generated
runtime data must always retain stable references back to it.

## General Interactions

General MM9 interactions should be part of the same behavior graph as mechanisms. Do not make BLV/ODM face events the
authoritative source for MM9 quest/dialogue/use/touch behavior.

MM6-MM8-style interactable faces are naturally represented by face event ids. MM9 interactions are more commonly named
objects, props, trigger volumes, script objects, and messages. A converted face can be a picking target, but the
behavior should resolve through the MM9 source object/message registry.

Recommended starting point:

```yaml
interactions:
  - interaction_id: mm9:map:interaction:well01
    source_object_index: 456
    source_class: Prop
    source_name: Well01
    activation:
      use: true
      touch: false
    binding:
      target_kind: model_instance
      instance_id: mm9:map:model_instance:22
    sends:
      target_name: Well01Script
      message_name: Use
```

For converted static geometry, the binding may point at faces:

```yaml
binding:
  target_kind: blv_face_group
  face_indices: [88]
```

The important rule is that faces, bmodels, model instances, and volumes identify where interaction occurs. The
interaction entry identifies what MM9 object/message/script behavior occurs.

The sidecar is named `events.yml` because it owns the broader MM9 map behavior graph. Moving mechanisms are a section
inside this file, alongside trigger volumes, general interactions, script bindings, and unresolved diagnostics.

## Proposed Sidecar Schema

The schema below is intentionally source-first. It distinguishes normalized fields from preserved raw fields.

```yaml
format_version: 1
kind: mm9_events
source_dat: 1000Terrors.dat
source_raw_objects: 1000Terrors.raw_objects.yml
coordinate_system:
  source: lithtech_mm9
  openyamm_mapping: [x, z, y]
  scale: 2.56

objects:
  - object_id: mm9:1000terrors:object:123
    source_object_index: 123
    source_class: RotatingDoor
    source_name: TrapTrigger0
    source_payload:
      declared_data_length: 456
      raw_object_ref: 1000Terrors.raw_objects.yml#objects[123]

    transform:
      source_pos_lt: [0.0, 0.0, 0.0]
      openyamm_pos: [0.0, 0.0, 0.0]
      source_rotation_raw: [0.0, 0.0, 0.0, 1.0]
      source_scale: [1.0, 1.0, 1.0]

    script:
      script_name: scripts/example.scr
      script_params_raw: "TargetName,Message,100"
      params:
        - index: 1
          raw: TargetName
        - index: 2
          raw: Message
        - index: 3
          raw: "100"

    binding:
      status: unresolved
      candidates:
        - target_kind: bmodel
          target_id: 42
          confidence: exact_name
          notes: source name matched generated bmodel name
        - target_kind: model_instance
          target_id: mm9:1000terrors:model_instance:12
          confidence: position_overlap

    mechanism:
      kind: rotating_door
      source_units: lithtech
      linear:
        move_dir_lt: [0.0, 0.0, 0.0]
        move_dist_lt: 0.0
        open_speed_lt_per_sec: 35.0
        close_speed_lt_per_sec: 10.0
      rotation:
        rotation_point_lt: [0.0, 0.0, 0.0]
        rotation_angles_deg: [0.0, 90.0, 0.0]
        open_away: false
      timing:
        move_delay_seconds: 0.0
        open_wait_seconds: 0.0

    activation:
      start_open: false
      start_on: true
      locked: false
      push_open: false
      touch_to_open: false
      auto_trigger: false
      reopen_on_contact: false
      double_door_name: ""

    trigger_outputs:
      - phase: open
        slot: 0
        target_name: SorceressStatue
        message_name: Go
      - phase: close
        slot: 0
        target_name: ""
        message_name: ""

    audio:
      sound_pos_lt: [0.0, 0.0, 0.0]
      open_start_sound: ""
      open_busy_sound: ""
      open_stop_sound: ""
      close_start_sound: ""
      close_busy_sound: ""
      close_stop_sound: ""
      jiggle_sound: ""

    collision:
      visible: true
      solid: true
      rayhit: true
      box_physics: false

    raw_properties:
      preserve_all_decoded_properties: true
      raw_object_ref: 1000Terrors.raw_objects.yml#objects[123]

triggers:
  - trigger_id: mm9:1000terrors:object:200
    source_object_index: 200
    source_name: SpawnTrigger0
    dims_lt: [128.0, 64.0, 128.0]
    start_on: true
    touch:
      trigger_touch: true
      message_touch: false
      player_triggerable: true
      ai_trigger_name: ""
    timing:
      timed_trigger: false
      min_trigger_time_seconds: 0.0
      max_trigger_time_seconds: 0.0
      send_delay_seconds: 0.0
      trigger_delay_seconds: 0.0
    outputs:
      - slot: 1
        target_name: TrapTrigger0
        message_name: Use

scripts:
  - script_id: scripts/darkp_raisingbridge.scr
    source_path: mm9/extracted/SCRIPTS/SCRIPTS/DARKP_RAISINGBRIDGE.scr
    parse_status: parsed_with_unknowns
    registered_triggers:
      - message: Move
        callback: OnMove
    commands:
      - command: MoveToPos
        source_line: 42
        arguments_raw: ["nTopX", "nTopY", "nTopZ", "180"]
        normalized:
          kind: move_to_marker_position
          rate_source_units: 180

unresolved:
  - kind: target_name
    source_object_index: 200
    target_name: MissingTarget
    message_name: Open
    severity: warning
```

The exact field names can change during implementation, but the requirements should not:

- preserve source object index and class;
- preserve source object name;
- preserve raw properties;
- preserve scripts and raw script params;
- represent trigger outputs as ordered slots;
- keep unresolved references as explicit diagnostics;
- keep movement values in source units until verified;
- allow binding to more than one target type.

## Script IR Requirement

An event sidecar is incomplete without a script IR. The first parser does not need full execution, but it must avoid
throwing behavior away. Suggested script IR levels:

1. Tokenized command stream with source path, line number, command, raw arguments, and labels/functions.
2. `AddTrigger` registry: message name to callback label/function.
3. `Trigger` graph edges: source script/object to target object/message expression.
4. Movement extraction for `MoveToPos`, `MoveDir`, `Rotate`, and `SetPos`.
5. State extraction for `SetFlag`, `ClearFlag`, `SetStat`, `GetStat`, `PlayAnim`, `SetModelFilenames`, `DestroyObject`,
   and object visibility/solidity changes.
6. Unknown command preservation with raw source line.

This lets runtime support arrive incrementally without needing to re-investigate scripts later. A command that is not
implemented should still be present in the IR and visible in validation reports.

## Binding Strategy

Event import should run in three phases.

### Phase 1: Preserve

Generate `<map>.events.yml` from raw objects and scripts without requiring geometry binding. Every mechanism-like
object is represented with source class, object index, name, decoded properties, raw object reference, script name, and
script params.

Output validation:

- all mechanism classes are counted;
- all script references are listed;
- missing scripts are reported;
- all trigger target names are indexed;
- unresolved targets are reported;
- unknown script commands are reported.

### Phase 2: Bind

Bind source objects to generated OpenYAMM runtime targets. Candidate target kinds:

- BLV face group;
- ODM bmodel;
- scene model instance;
- trigger volume;
- collision volume;
- water volume;
- ladder volume;
- script-only object.

Binding should use multiple signals:

- exact source name match;
- source object class;
- generated `source_ref` and `source_object_index`;
- generated bmodel source face metadata;
- model filename/skin;
- position and bounds overlap;
- marker references;
- trigger target graph;
- manual override table for maps where automatic binding is ambiguous.

Bindings should have confidence labels such as:

- `exact_source_object_index`;
- `exact_name`;
- `source_model_match`;
- `bounds_overlap`;
- `nearest_position`;
- `manual_override`;
- `unresolved`.

Unresolved bindings are acceptable in the import output. Silent incorrect bindings are not acceptable.

### Phase 3: Execute

Runtime execution should consume normalized mechanisms and target bindings. The implementation order should prioritize
the highest value and lowest ambiguity mechanisms first:

1. Trigger object volumes and object-name/message dispatch.
2. Linear `Door` and `WeightedLift` movement using `MoveDir`, `MoveDist`, speeds, start state, locks, and wait times.
3. `RotatingDoor` movement using `RotationPoint`, `RotationAngles`, speeds, and open-away behavior.
4. Script `MoveToPos`, `MoveDir`, `SetPos`, and marker resolution.
5. Visibility/solid/rayhit flag changes.
6. Continuous `RotatingBrush` mechanisms.
7. `PlayAnim`, `LoopAnim`, and `SetModelFilenames`.
8. Water/ladders/dynamic volumes.
9. Destructible blockers, shooters, traps, and AI/perception barriers.

## Runtime Representation

Introduce a shared source-mechanism runtime layer rather than growing MM9 behavior directly inside the legacy BLV door
code. Conceptually:

```text
SourceMechanism
  source object id
  source class
  current state
  trigger handlers
  authored motion/state/audio/script data
  bound runtime targets

Runtime target
  BLV face group
  ODM bmodel
  scene model instance
  trigger volume
  collision volume
  water/ladder volume
  script-only object
```

Supported transform kinds should include:

- linear translation;
- rotation around arbitrary pivot;
- continuous rotation;
- absolute move to position;
- visibility toggle;
- solidity/rayhit toggle;
- model/skin swap;
- animation playback;
- destroy/remove;
- dimensions update.

`MapDeltaDoor` can remain the MM6-MM8-compatible indoor representation. It can also be used as an execution target for
MM9 only when a mechanism is exactly equivalent to a linear BLV face offset. It should not be the MM9 source schema.

## ODM Mapping

For outdoor-style generated maps, the current bmodel translation path is a useful starting point. It should be extended
to support:

- source object ids and sidecar loading;
- bmodel rotation around source pivots;
- model instance movement;
- model instance rotation;
- trigger volumes;
- dynamic broadphase bounds for moving mechanisms;
- batched spatial index updates;
- collision and picking updates from current transforms;
- optional attached party movement for lifts/platforms;
- object sounds and trigger outputs.

The importer should not bake the open/closed geometry state into ODM as the only state. ODM should hold rest geometry.
This event sidecar should hold the authored mechanism and initial state.

## BLV Mapping

For indoor-style generated maps, use BLV as static sector/face representation and bind MM9 mechanisms to BLV face groups
only when the binding is known. Some MM9 mechanisms may be better represented as model instances or volumes even inside
an indoor-looking map.

When binding to BLV faces, preserve:

- source object id;
- source object class;
- source object name;
- source movement type;
- source trigger graph;
- source raw properties;
- exact rest transform and dynamic transform.

Do not create a fake legacy BLV door if doing so would lose rotation, trigger, script, or object state data.

## Performance Approach

Mechanisms are sparse compared with static world geometry. Runtime should avoid rebuilding an entire map each frame.

Recommended approach:

- keep static geometry in the existing static spatial structures;
- represent each moving mechanism as a dynamic proxy with current transform and broadphase AABB;
- recompute only the affected proxy AABB when a mechanism moves;
- update render transforms directly for model instances where possible;
- for bmodel/face-group geometry, evaluate current positions from rest geometry plus transform;
- avoid accumulating vertex edits over time;
- batch spatial index updates for mechanisms moved in the same tick;
- update collision/pathing hooks only for mechanisms that changed since the previous tick;
- keep trigger volumes as cheap AABB/OBB checks unless a script requires finer geometry.

The current outdoor mechanism refresh path already proves the idea of updating moved bmodels. It should evolve toward
transform-based dynamic proxies and rotation support instead of whole-map rebuilds.

## Validation Requirements

Lossless integration should include a validation command that runs across all 45 DAT-derived maps. It should fail on
data loss and report incomplete runtime support separately.

Minimum validation checks:

- every raw object with a mechanism-relevant class appears in `<map>.events.yml`;
- every event sidecar entry references a valid raw object index;
- every decoded property remains recoverable through `raw_properties` or raw object reference;
- class totals match the raw object corpus;
- all `ScriptName` references either resolve to an extracted script or are reported;
- all `ScriptParams` values are preserved exactly;
- all `TargetName*`/`MessageName*` trigger slots are preserved in order;
- all `OpenTrigger*` and `CloseTrigger*` slots are preserved in order;
- all script commands are either parsed into known IR commands or preserved as unknown raw commands;
- all movement commands preserve raw arguments and source line;
- every binding has a confidence value;
- unresolved bindings are listed explicitly;
- no generated mechanism silently drops source units, sounds, lock state, wait times, or trigger delays.

Recommended count checks from current corpus:

- `Door`: 757
- `RotatingDoor`: 1,017
- `WeightedLift`: 14
- `RotatingBrush`: 15
- `Trigger`: 482
- `ScriptObject`: 110
- `BlueWater`: 70
- `Ladder`: 68
- `InvisibleBrush`: 297
- `DestructableBrush`: 261
- `DestructableProp`: 174
- `Shooter`: 169

These counts should be regenerated by tooling rather than hardcoded, but they are useful regression targets for the
current data set.

## Suggested Test Maps

Use focused tests and visual/runtime checks on representative mechanisms:

- `1000Terrors`
  - Door, rotating door, weighted lift, triggers, and statue trigger chains.
- Dark Passageway scripts
  - Raising bridge and switch behavior from `DARKP_RAISINGBRIDGE.scr` and `DARKP_RAISINGSWITCH.scr`.
- Training Hall ladder scripts
  - Moving ladder behavior from `TALADDERMOVE.scr`.
- Water trap maps
  - `WATERTRAP.scr` and `WATER.inc` sink/fill/toggle behavior.
- Cage script map
  - Rare script-driven `Rotate` command.
- Falling floor script map
  - Combined flag changes, object movement, destruction, and removal.

For each implemented mechanism type, tests should compare:

- initial state;
- activated state;
- final transform;
- movement duration from source speed/rate;
- trigger outputs;
- lock/use/touch behavior;
- collision and picking state;
- relevant AI/pathing behavior where applicable.

## Open Questions

These should be answered by targeted reverse engineering or runtime observation, not guessed into the final import:

- Exact units for `MoveToPos`, `MoveDir`, and door `Speed`/`ClosingSpeed`.
- Exact semantics of `OpenAway` for `RotatingDoor`.
- Whether `RotationAngles` are always Euler degrees in source coordinate order.
- Exact continuous-rotation behavior of `RotatingBrush` and `RotatingStuff`.
- Whether `MoveDelay`, `OpenWaitTime`, `TriggerDelay`, and `SendDelay` are always seconds.
- Exact handling of `ReopenOnContact` and collision blocking during closing.
- Exact behavior of `PushOpen`, `TouchToOpen`, and `AutoTrigger` interaction precedence.
- Full meaning of `SoundPos` and whether sounds follow moving objects or stay at authored positions.
- How dynamic water/ladders should affect current gameplay systems once moved.
- Whether any object properties use map-local enum values that need decoding beyond current scalar/vector parsing.

This event sidecar should preserve raw values even while these questions remain open.

## Complete Implementation Checklist

This checklist is intentionally end-to-end. A task is not complete if it only produces runtime behavior while losing
source data, or if it only preserves data with no way for the game/editor to load, inspect, and validate it.

### Import And Generation

- [ ] Define the `mm9_events` YAML schema with explicit `format_version`, map id, source DAT path, source raw object
      sidecar path, coordinate conversion metadata, and generated-tool version.
- [ ] Add a generator that reads every `assets_dev/worlds/mm9/maps/<map>.raw_objects.yml`.
- [ ] Emit `assets_dev/worlds/mm9/maps/<map>.events.yml` for every MM9 map.
- [ ] Preserve every raw object index in the event sidecar, even if the object is currently classified as non-mechanism.
- [ ] Classify known mechanism and interaction carriers: `Door`, `RotatingDoor`, `WeightedLift`, `RotatingBrush`,
      `Trigger`, `ScriptObject`, `Prop`, `WorldObject`, `InvisibleBrush`, `DestructableBrush`, `DestructableProp`,
      `BlueWater`, `Ladder`, `Shooter`, `AIBarrier`, `PerceptionBrush`, `Marker`, and any class with `ScriptName`.
- [ ] Emit an explicit `unclassified_objects` or `objects` section for source objects not yet understood.
- [ ] Preserve all decoded object properties by reference to `raw_objects.yml` and by normalized fields where known.
- [ ] Preserve raw `ScriptName`, `ScriptParams`, `Parameters`, `Name`, `Pos`, `Rotation`, `Scale`, `Filename`, `Skin`,
      `Visible`, `Solid`, `Rayhit`/`RayHit`, `Hidden`, `Dims`, and object class values.
- [ ] Normalize door-like movement fields without deleting source fields: `Speed`, `ClosingSpeed`, `MoveDelay`,
      `OpenWaitTime`, `MoveDir`, `MoveDist`, `RotationPoint`, `RotationAngles`, and `OpenAway`.
- [ ] Normalize activation fields: `StartOpen`, `StartOn`, `PushOpen`, `TouchToOpen`, `AutoTrigger`, `Locked`,
      `ReopenOnContact`, `DoubleDoorName`, `TriggerDims`, and `LockJiggleSpeed`.
- [ ] Normalize sound fields while preserving empty strings and unknown values.
- [ ] Normalize ordered trigger slots: `TargetName1..10`, `MessageName1..10`, `OpenTriggerTarget0..3`,
      `OpenTrigger0..3`, `CloseTriggerTarget0..3`, and `CloseTrigger0..3`.
- [ ] Emit `interactions` for general use/touch/click behavior, not only moving mechanisms.
- [ ] Keep generated sidecars deterministic: stable ordering, stable ids, stable formatting.
- [ ] Add a generation command that can regenerate all MM9 event sidecars in one pass.
- [ ] Add the generation command to the MM9 import documentation.

### Script IR And Lua Generation

- [ ] Add a parser for `mm9/extracted/SCRIPTS/SCRIPTS/*.scr` and `*.inc`.
- [ ] Preserve raw source file path, line number, original line text, command name, raw argument strings, labels, and
      function/callback boundaries.
- [ ] Parse `AddTrigger` into message-to-callback registrations.
- [ ] Parse `Trigger` into source-to-target message edges where statically knowable.
- [ ] Parse movement commands: `MoveToPos`, `MoveDir`, `Rotate`, and `SetPos`.
- [ ] Parse object lookup and marker patterns: `GetObjectHandle`, `GetPos`, `GetDims`, and script params used as names.
- [ ] Parse state commands: `SetFlag`, `ClearFlag`, `SetStat`, `GetStat`, `DestroyObject`, and object removal commands.
- [ ] Parse presentation commands: `PlayAnim`, `LoopAnim`, and `SetModelFilenames`.
- [ ] Preserve all unknown commands as `unknown_command` entries with raw source and arguments.
- [ ] Preserve script include relationships.
- [ ] Preserve known script bugs/quirks as source behavior instead of silently correcting them during import.
- [ ] Emit script IR referenced from `<map>.events.yml`, either embedded or as generated `script_ir` sidecars.
- [ ] Generate per-map Lua from script IR for executable behavior.
- [ ] Support either one generated Lua file per map or split files such as:
      `assets_dev/worlds/mm9/events/<map>.lua` and
      `assets_dev/worlds/mm9/events/<map>.mechanisms.lua`.
- [ ] Mark generated Lua files clearly as generated so fixes happen in the exporter/parser, not by hand editing.
- [ ] Ensure generated Lua can resolve source object names through the runtime mechanism registry.
- [ ] Ensure generated Lua has APIs for message dispatch, movement, state flags, stats, animation, model swap, item/key
      checks, and quest/dialogue hooks needed by map scripts.

### Binding To Runtime Targets

- [ ] Add binding records in `<map>.events.yml` for target kinds:
      `odm_bmodel`, `blv_face_group`, `model_instance`, `trigger_volume`, `collision_volume`, `water_volume`,
      `ladder_volume`, `script_object`, and `unresolved`.
- [ ] Preserve source object identity on every binding: source object index, source class, source name, source position,
      and raw object reference.
- [ ] Bind generated model instances using `source_object_index`, `source_ref`, source model filename, source name, and
      position/bounds overlap.
- [ ] Bind ODM bmodels using generated source metadata, bmodel names, source model references, face source data, and
      bounds overlap.
- [ ] Bind BLV face groups using generated source face metadata where available, plus object names, source model refs,
      bounds overlap, and manual overrides where needed.
- [ ] Store face indices and vertex indices for BLV face-group bindings when faces are the runtime target.
- [ ] Store bmodel index and optional local face indices for ODM bmodel bindings.
- [ ] Store model instance id for prop/model bindings.
- [ ] Store dimensions and transform for trigger, water, ladder, and collision volume bindings.
- [ ] Assign every binding a confidence value such as `exact_source_object_index`, `exact_name`, `source_model_match`,
      `bounds_overlap`, `nearest_position`, `manual_override`, or `unresolved`.
- [ ] Report every unresolved binding; never silently bind to a low-confidence target.
- [ ] Add manual binding override support as data, not code special cases.
- [ ] Validate that bindings do not reference missing faces, vertices, bmodels, model instances, or volumes.

### Runtime Loading

- [ ] Extend map/scene loading to discover optional MM9 event sidecars.
- [ ] Load `<map>.events.yml` only for MM9 maps or maps that declare this sidecar.
- [ ] Preserve existing MM6-MM8 loading behavior when no MM9 event sidecar exists.
- [ ] Build a runtime registry keyed by stable mechanism id and source object name.
- [ ] Build a message dispatch registry for source object names and script objects.
- [ ] Load generated per-map Lua and register its message handlers.
- [ ] Support built-in mechanisms that require no Lua, such as simple doors/lifts/triggers.
- [ ] Support Lua-driven mechanisms that call into runtime movement/state APIs.
- [ ] Separate source mechanism state from runtime target transform state.
- [ ] Save/load mechanism state: open/closed/on/off, current progress, locked, visible/solid/rayhit flags, destroyed
      state, current animation/model, timers, and script-local state required by generated Lua.
- [ ] Ensure old saves for MM6-MM8 remain compatible.

### Game Runtime Behavior

- [ ] Implement named message dispatch: `Trigger(targetName, messageName)`.
- [ ] Implement use/click dispatch from bound faces, bmodels, model instances, and volumes to interaction entries.
- [ ] Implement touch dispatch from trigger/collision volumes.
- [ ] Implement linear movement from rest transform using source direction, distance, speed, close speed, delay, and wait.
- [ ] Implement rotating door movement around arbitrary source pivot and angle.
- [ ] Implement continuous rotating brush movement with correct start/stop state once semantics are verified.
- [ ] Implement `MoveToPos`, `MoveDir`, `Rotate`, and `SetPos` runtime APIs for generated Lua.
- [ ] Implement marker lookup and marker-position movement.
- [ ] Implement `SetFlag`/`ClearFlag` effects for visibility, solidity, rayhit/picking, gravity-like flags, and
      go-through-world where relevant.
- [ ] Implement `SetStat`/`GetStat` for door state, locked state, open/closed/opening/closing, and `DoorOpenTime`.
- [ ] Implement trigger delays, send delays, timed triggers, start-on/start-off, and touch gating.
- [ ] Implement lock/key/item checks needed by generated Lua scripts.
- [ ] Implement door sounds and moving-object sound positions.
- [ ] Implement animation playback hooks for `PlayAnim` and `LoopAnim`.
- [ ] Implement model/skin swapping for `SetModelFilenames`.
- [ ] Implement dynamic water movement, visibility, fog/surface flags, and damage volume behavior.
- [ ] Implement dynamic ladder volumes and moving ladder support.
- [ ] Implement destructible blockers/props and object removal.
- [ ] Implement shooter/trap activation once projectile semantics are mapped.
- [ ] Implement AI door interaction equivalent to `BASEDOOR.inc` behavior: stop, face, trigger use, wait, resume.
- [ ] Update picking/collision/pathing when a dynamic target moves or changes flags.
- [ ] Keep dynamic updates incremental; do not rebuild entire maps every frame.

### Editor Support

- [ ] Load `<map>.events.yml` in the editor alongside scene geometry.
- [ ] Display source object names, classes, ids, and binding confidence.
- [ ] Display mechanism target bindings: face group, bmodel, model instance, volume, or unresolved.
- [ ] Highlight bound faces/vertices/bmodels/model instances/volumes for selected mechanisms.
- [ ] Show trigger/message graph edges between source objects.
- [ ] Show general interactions separately from moving mechanisms while preserving the shared source object graph.
- [ ] Show generated script references and registered message handlers.
- [ ] Surface unresolved bindings, missing target names, missing scripts, and unknown script commands as editor diagnostics.
- [ ] Allow manual binding overrides to be authored as explicit data.
- [ ] Prevent editor saves from editing generated raw object data directly.
- [ ] If the editor edits an event sidecar, preserve raw source references and unknown fields.
- [ ] Add editor preview controls for open/close/toggle/use/touch messages.
- [ ] Add editor preview for movement progress and final transforms.
- [ ] Add editor validation action for the current map.
- [ ] Keep MM6-MM8 editor behavior unchanged when no MM9 sidecar is loaded.

### Lossless Validation

- [ ] Add a command that validates one MM9 map.
- [ ] Add a command that validates all MM9 maps.
- [ ] Verify every raw object index appears in the mechanism/import index or in an explicit preserved object section.
- [ ] Verify every sidecar object references an existing raw object index.
- [ ] Verify every decoded raw property is reachable from the event sidecar by raw reference or normalized field.
- [ ] Verify no known mechanism/interactable/source-script object is omitted.
- [ ] Verify class totals match raw object totals for known mechanism classes.
- [ ] Verify all trigger slots are preserved in original order.
- [ ] Verify all script names and params are preserved byte-for-byte or string-for-string as exported.
- [ ] Verify missing scripts are diagnostics, not silent drops.
- [ ] Verify all script commands are represented as known commands or unknown raw commands.
- [ ] Verify all movement commands preserve raw arguments and source line.
- [ ] Verify all target names either resolve to source objects or appear in unresolved diagnostics.
- [ ] Verify every binding target exists or is marked unresolved.
- [ ] Verify generated Lua references only objects/messages known to the registry or listed unresolved.
- [ ] Verify regenerated sidecars are deterministic and produce clean diffs.
- [ ] Verify validation separates "data loss" failures from "runtime not implemented yet" warnings.

### Unit And Integration Tests

- [ ] Add importer unit tests for raw object to normalized sidecar conversion.
- [ ] Add importer unit tests for ordered trigger slot preservation.
- [ ] Add importer unit tests for preserving unknown properties.
- [ ] Add script parser unit tests for `AddTrigger`, `Trigger`, `MoveToPos`, `MoveDir`, `Rotate`, `SetPos`,
      `SetFlag`, `ClearFlag`, `SetStat`, `GetStat`, `PlayAnim`, and `SetModelFilenames`.
- [ ] Add script parser unit tests for unknown command preservation.
- [ ] Add sidecar schema validation tests.
- [ ] Add binding tests with synthetic face groups, bmodels, model instances, and volumes.
- [ ] Add runtime unit tests for named message dispatch.
- [ ] Add runtime unit tests for linear door/lift movement over time.
- [ ] Add runtime unit tests for reversing/closing behavior and lock state.
- [ ] Add runtime unit tests for rotating doors around arbitrary pivots.
- [ ] Add runtime unit tests for trigger delay/send delay/timed trigger behavior.
- [ ] Add runtime unit tests for visibility/solid/rayhit toggles.
- [ ] Add runtime unit tests for model swap and animation command dispatch.
- [ ] Add save/load tests for mechanism state.
- [ ] Add editor model tests that load an event sidecar and expose object names, bindings, graph edges, diagnostics,
      and preview state.
- [ ] Add editor tests for manual binding override persistence.
- [ ] Add regression tests proving MM6-MM8 maps without MM9 sidecars still use the existing mechanism/event path.
- [ ] Add focused headless map tests for representative MM9 maps and scripts listed in the suggested test maps section.

### Acceptance Criteria

- [ ] Every MM9 map has generated `<map>.events.yml`.
- [ ] Every MM9 map has generated executable Lua or an equivalent generated script artifact referenced by the map.
- [ ] Validation across all 45 maps reports no data-loss failures.
- [ ] Unknown and unimplemented behavior is explicitly reported, not dropped.
- [ ] General interactions, mechanisms, triggers, and scripts resolve through the same MM9 source object/message registry.
- [ ] The game can load an MM9 map, load its sidecar/Lua, dispatch use/touch/messages, and execute implemented
      mechanisms.
- [ ] The editor can inspect MM9 mechanisms/interactions, show bindings and diagnostics, and preview implemented
      movements.
- [ ] Existing MM6-MM8 gameplay, map loading, event execution, and editor behavior remain unchanged unless a map
      explicitly opts into the MM9 sidecar mechanism path.
- [ ] Runtime mechanisms use transform/state evaluation from rest data rather than accumulating destructive geometry
      edits.
- [ ] ODM/BLV remain geometry/runtime targets; `<map>.events.yml` and generated Lua remain the authoritative MM9
      behavior artifacts.

## Bottom Line

MM9 mechanisms should be integrated as source-authored object/script mechanisms with generated runtime bindings. ODM and
BLV are useful render/collision targets, but they should not be the lossless storage model for MM9 behavior. The
event sidecar approach keeps all DAT and script intent available, supports both outdoor-like and indoor-like maps through the
same mechanism layer, and lets OpenYAMM implement behavior incrementally without losing original author intent.
