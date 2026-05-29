# MM9 Script Lua Runtime Command Inventory

Status: implementation contract for the generated MM9 Lua runtime.

This document inventories the command surface produced from the MM9 `.scr` files and maps it to the engine services
OpenYAMM needs to provide. It uses generated OpenYAMM data as the source inventory and local `mm9/lithtech/*`
references only as behavioral/structural references. Do not copy LithTech or original MM9 code into OpenYAMM.

## Inventory Sources

Primary generated inventory:

- [assets_dev/worlds/mm9/scripts/script_index.yml](../../assets_dev/worlds/mm9/scripts/script_index.yml): canonical
  per-script, per-line command inventory. Every command entry includes source file, source line, normalized command,
  original command spelling, and raw arguments.
- [assets_dev/worlds/mm9/scripts](../../assets_dev/worlds/mm9/scripts): generated Lua files.
- [tools/Mm9RudeTranscode.cpp](../../tools/Mm9RudeTranscode.cpp#L650): exporter emits a direct `ctx:<method>(...)`
  call where one exists, otherwise falls back to `ctx:command(command, args, meta)`.

Current OpenYAMM runtime surface:

- [game/mm9/Mm9ScriptRuntime.h](../../game/mm9/Mm9ScriptRuntime.h#L20): records unimplemented commands, callbacks,
  key/party accesses, trigger registrations, dispatches, variables, and object properties.
- [game/mm9/Mm9ScriptRuntime.cpp](../../game/mm9/Mm9ScriptRuntime.cpp#L269): current direct Lua methods.
- [game/mm9/Mm9ScriptRuntime.cpp](../../game/mm9/Mm9ScriptRuntime.cpp#L687): generic `ctx:command(...)` recorder.
- [game/mm9/Mm9ScriptRuntime.cpp](../../game/mm9/Mm9ScriptRuntime.cpp#L712): registered `ctx` method table.

LithTech/MM9-local reference anchors:

- [mm9/lithtech/sdk/inc/iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L165): world queries, collision/raycast,
  object transform, movement, standing/collision info, point shade, named object lookup, and object messaging.
- [mm9/lithtech/sdk/inc/iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L705): world-file object property getters.
- [mm9/lithtech/sdk/inc/iltbaseclass.h](../../mm9/lithtech/sdk/inc/iltbaseclass.h#L520): update, touch/collision, model
  key, crush, and physics-affect callbacks.
- [mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp](../../mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp#L17): representative
  trigger object properties: targets, messages, delays, activation counts, locks, touch rules, and sounds.
- [mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp](../../mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp#L466): representative touch
  filtering and trigger activation.
- [mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp](../../mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp#L771): representative
  activation, weighted messages, dispatch, touch reply, and activation sound.
- [mm9/lithtech/NOLF/ObjectDLL/CommandMgr.cpp](../../mm9/lithtech/NOLF/ObjectDLL/CommandMgr.cpp#L130):
  representative object command scheduler (`MSG`, `RAND`, `DELAY`, `REPEAT`, `LOOP`, `ABORT`).
- [mm9/lithtech/runtime/shared/src/shared_iltphysics.cpp](../../mm9/lithtech/runtime/shared/src/shared_iltphysics.cpp#L76):
  object dimensions and standing/collision info semantics.
- [mm9/lithtech/runtime/shared/src/moveobject.cpp](../../mm9/lithtech/runtime/shared/src/moveobject.cpp#L1526):
  movement resolves physical objects through collision processing or player mover paths.
- [mm9/lithtech/sdk/inc/ltengineobjects.cpp](../../mm9/lithtech/sdk/inc/ltengineobjects.cpp#L302): representative
  world `Sound` object property load and playback.
- [mm9/lithtech/sdk/inc/ltbasedefs.h](../../mm9/lithtech/sdk/inc/ltbasedefs.h#L1946): `FLAG_MODELKEYS`.
- [mm9/lithtech/runtime/server/src/s_object.cpp](../../mm9/lithtech/runtime/server/src/s_object.cpp#L180):
  model string-key messages are sent only when model keys are enabled.

Important caveat: the provided `mm9/lithtech/*` tree contains LithTech SDK/runtime and sample game object DLLs, not the
exact MM9 proprietary script-command implementation. The references above are the closest local implementation meaning:
object handles, messages, callbacks, movement, collision, flags, sound, and command scheduling.

## Source Coverage Snapshot

Generated inventory count on 2026-05-27:

| Metric | Count |
| --- | ---: |
| Script modules (`.scr`) | 715 |
| Include modules (`.inc`) | 87 |
| Generated inventory modules | 802 |
| Source command invocations | 42,610 |
| Unique normalized command tokens | 759 |
| Label definitions | 6,125 |
| Include directives | 1,077 |
| Assignment-form command tokens | 2,435 |
| Unique assignment targets | 471 |
| `if`/`if(`/malformed-if variants | 3,891 |

Every source invocation is represented in `script_index.yml`; the markdown tables below summarize the runtime service
surface. For lossless work, future agents should query `script_index.yml` for exact file/line/argument examples.

Implementation checkpoint on 2026-05-27:

- The high-frequency `ctx:command(...)` surface is covered through runtime commands or the generic assignment-form
  handler. A scan of generated Lua after the current implementation batch leaves only assignment-form tokens in the
  high-frequency list.
- The next lower-frequency batch added `PauseWait`, `OnCongestion`, `OnDeathDone`, `RemoveEnemy`, `IsOnGround`,
  `TraceOn`, `IsClearShot`, `FindTargets`, `RemoveFriend`, `GetGameTime`, `GetPCLevel`, and related vector/object
  helpers.
- The next one-off batch added runtime normalization for malformed legacy command tokens (`Command(`,
  `if(condition)`, `while(condition)`, and `(if`) and implemented the remaining non-assignment generated fallback
  command shapes. A scan of generated Lua after applying the same runtime normalization reports zero remaining
  non-assignment fallback command tokens outside the implemented/direct command surface.
- The recursive generated-Lua guard in
  [tests/Mm9ScriptRuntimeCommandTests.cpp](../../tests/Mm9ScriptRuntimeCommandTests.cpp) now scans both
  `assets_dev/worlds/mm9/scripts/*.lua` and `assets_dev/worlds/mm9/scripts/includes/*.lua`. It asserts that every
  non-assignment `ctx:command(...)` fallback token is either implemented by the generic runtime dispatcher or covered
  by a direct generated `ctx:<method>(...)` runtime method.
- Include-only AI/navigation helpers are now recognized so included source labels do not silently fall through as
  unknown commands. These include `CanReachObject`, `CanReachTarget`, `CastRay`, `FindHidingPlace`, `FacePos`,
  `SetRotation`, `CalcRotationRate`, `GetAnimNbr`, `GetObjectTarget`, `VecMag`, `VecAngle`, `Sin`, `Cos`, and the
  include-only callback aliases.
- This checkpoint means generated Lua command information is no longer dropped by the MM9 script runtime recorder. It
  does not mean the final gameplay backends are complete: real script fibers, timed callback dispatch, DAT world
  collision/raycasting, actor movement, animation playback, audio playback, and party stat/promotion application still
  need the engine services described below.

## Generated Lua `ctx` Surface

Static `ctx:<method>(...)` occurrences in generated Lua:

| Method | Static calls | Meaning |
| --- | ---: | --- |
| `command` | 42,610 | Generic fallback for every source command shape. |
| `trigger` | 1,573 | Dispatch object/script message. |
| `addTrigger` | 1,289 | Register source trigger name to label callback. |
| `getParam` | 1,042 | Read script/object activation parameter into a script variable. |
| `hasKey` | 727 | Test MM9 key/qbit, usually writing a result variable in source semantics. |
| `giveKey` | 343 | Set MM9 key/qbit. |
| `takeKey` | 169 | Clear MM9 key/qbit. |
| `giveExp` | 122 | Grant party experience. |
| `onRudeExit` | 120 | Register label to run when dialogue closes/exits. |
| `giveItem` | 101 | Grant party item. |
| `setPropNumber` | 74 | Set numeric property on active object. |
| `giveGold` | 68 | Grant party gold. |
| `takeItem` | 54 | Remove party item. |
| `hasItem` | 52 | Test party item, usually writing a result variable in source semantics. |
| `setConsoleNumVar` | 44 | Write global numeric console variable. |
| `doRude` | 41 | Open RUDE dialogue by raw MM9 id. |
| `getConsoleNumVar` | 26 | Read global numeric console variable into script variable. |
| `setConsoleStrVar` | 14 | Write global string console variable. |
| `getConsoleStrVar` | 13 | Read global string console variable into script variable. |
| `getObjectHandleByRudeId` | 12 | Resolve object handle from RUDE id binding. |

Current generated Lua uses `ctx:command(...)` as a fallback branch, not as a second execution path when a direct method
exists. Runtime code must not double-apply direct commands.

## Current Direct Command Matrix

These commands already have direct C++ method stubs, but several are still only partial because source scripts often
expect output variables and object-scoped state, not only a Lua return value.

| Source command | Count | Source parameter shape | Required runtime effect | Current status |
| --- | ---: | --- | --- | --- |
| `DoRude` | 41 | `<rudeId>` | Open generated RUDE dialogue for current owner/object. | Implemented for dialogue entry. |
| `OnRudeExit` | 120 | `<label>` | Register callback label for dialogue exit. | Implemented as an object-scoped callback registration; close-event routing still belongs to UI/world callers. |
| `GiveKey` | 343 | `[ignored/empty], <rawKeyId>` or `<rawKeyId>` | Set qbit-backed MM9 key (`9000 + raw id`) and preserve raw id access. | Implemented for raw-id aliases, empty first slots, key state, and access records. |
| `TakeKey` | 169 | `<rawKeyId>` | Clear qbit-backed MM9 key. | Implemented for raw-id aliases, key state, and access records. |
| `HasKey` | 727 | `<rawKeyId>, <destVar>` | Write boolean/number result to destination variable and return truth for direct use. | Implemented for return value and source destination-variable semantics. |
| `GiveItem` | 101 | `<itemId>` | Grant one party item using MM9-to-base item id mapping. | Implemented for numeric/script-expression ids; source audit found no authored quantity/quality operands. |
| `TakeItem` | 54 | `<itemId>` | Remove one item from party inventory. | Implemented for numeric/script-expression ids; source audit found no authored quantity/quality operands. |
| `HasItem` | 52 | `<itemId>, <destVar>` or `<itemId> <destVar>` | Write result variable and return truth. | Implemented for party lookup, return value, destination variable, and access records. |
| `GiveGold` | 68 | `<amountExpr>` | Add evaluated amount to party gold. | Implemented with the shared party gold state. |
| `GiveExp` | 122 | `<amountExpr>` | Grant shared party experience. | Implemented with shared party experience grant; MM9-specific reward scaling remains data work. |
| `SetConsoleNumVar` | 44 | `<name>, <valueExpr>` | Write global persistent numeric variable. | Implemented for simple expressions and persistent runtime state. |
| `GetConsoleNumVar` | 26 | `<name>, <destVar>` | Read global numeric var into script var. | Implemented for simple vars. |
| `SetConsoleStrVar` | 14 | `<name>, <valueExpr/string>` | Write global persistent string variable. | Implemented for literal/string-token values and persistent runtime state. |
| `GetConsoleStrVar` | 13 | `<name>, <destVar>` | Read global string var into script var. | Implemented for simple vars. |
| `GetParam` | 1,042 | `<index>, <destVar>` | Read active object/script parameter into numeric/string script variable. | Implemented for active owner parameter vectors. |
| `SetPropNumber` | 74 | `<property>, <valueExpr>` | Set numeric property on active script object, e.g. `DoRude False`. | Implemented as persisted object property state; behavior wiring remains object-service work. |
| `GetObjectHandleByRUDEID` | 12 | `<rudeIdExpr>, <destHandleVar>` | Resolve world object bound to RUDE id into script handle variable. | Implemented as binding-backed stable string handles. |
| `AddTrigger` | 1,289 | `<messageName>, <label>` | Register object message callback. | Implemented for package-backed runtime objects; DAT world trigger-object semantics remain backend work. |
| `Trigger` | 1,573 | `<targetHandle/name>, <message>` | Send message to target object/script. | Implemented for package-backed runtime objects; real LithTech object messaging remains backend work. |

Direct methods should eventually parse the full raw `meta.args`, not only the first Lua argument. The source format has
comma-separated, whitespace-separated, quoted, and occasionally empty placeholder parameters.

## Runtime Services To Implement

### 1. Script VM, Control Flow, And Scheduler

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `Exit` | 7,734 | Stop current label/script. Some calls include truth values. |
| `endif` | 3,893 | End conditional block. |
| `Gosub` | 3,425 | Call label/subroutine and return. |
| `if`, `if(` | 3,879 | Conditional execution using expression evaluator. |
| `else` | 602 | Conditional alternate branch. |
| `Wait` | 1,250 | Delay and resume label/callback. |
| `goto` | 158 | Jump to label. |
| `while(` / `endwhile` | 135 | Loop with expression condition. |
| `SetCallBack` | 49 | Register numbered callback slot for `DoCallback`. |

Implementation requirements:

- Runtime cannot rely on generated Lua control flow alone; the exporter currently records legacy commands, so the
  engine-side script service must provide the legacy behavior behind `ctx:command(...)` or the exporter must be upgraded
  to emit real Lua control flow.
- Provide a per-object script fiber/job state: active script source, label, program counter or generated Lua label,
  local variables, wait deadline, pending callback, current sender/target, and active parameters.
- `Wait min, max, label` schedules resume after a random time in the range. LithTech `CommandMgr` has equivalent
  delayed/repeated command scheduling in `DELAY`, `REPEAT`, and `LOOP`
  ([CommandMgr.cpp](../../mm9/lithtech/NOLF/ObjectDLL/CommandMgr.cpp#L130),
  [ProcessRepeat/Loop](../../mm9/lithtech/NOLF/ObjectDLL/CommandMgr.cpp#L414)).
- `Exit` must terminate only the current script invocation/fiber, not unload the object.
- Conditions must support booleans, numbers, object handles, string variables, `NULL`, `TRUE`, `FALSE`, `==`, `!=`,
  comparisons, arithmetic, parentheses, and implicit truthiness matching the source scripts.

Current status:

- `Exit`, `Gosub`, `Goto`, `Wait`, `if`, `if(`, `while`, `while(`, `else`, `endif`, and `endwhile` are recognized by
  [Mm9ScriptRuntime](../../game/mm9/Mm9ScriptRuntime.cpp) and recorded as control/scheduler requests instead of being
  reported as unknown commands.
- `Wait` preserves minimum delay, maximum delay, label, source script, and source line, and enqueues a runtime scheduled
  invocation with the current owner context. `advanceScriptTime(...)` advances deterministic runtime script time and
  runs due labels through the generated Lua runtime.
- `GetTime` reads the same deterministic runtime script clock, and `GetGameTime` derives a 24-hour clock plus nearest
  15-minute interval from that clock until a full world calendar is wired in.
- `SetCallBack` registers numbered callback metadata for `DoCallback`. `DoCallback` dispatches the selected callback
  immediately in the current owner context, and `KillCallback` removes the selected numbered callback. It is not a
  timer; timed script continuation remains `Wait`.
- Pending scheduled invocation state and runtime script time are saved in OpenYAMM save version 76.
- Callback registrations are now object-scoped, part of `Mm9ScriptRuntimeState`, and restored through save/load in
  OpenYAMM save versions 77-78. `dispatchRegisteredCallbacks(...)` runs matching labels with the registered owner
  context; wiring real engine events into that helper still belongs to the MM9 actor/world scheduler.
- `@M` minute/hour schedule entries are recorded as control/scheduler requests with hour, minute, primary label, and
  fallback label. They do not yet enqueue real daily schedule callbacks.
- `if`/`while` records preserve the source condition text and a best-effort evaluation result from the runtime
  expression evaluator. They do not yet skip/execute blocks because the current generated Lua still emits legacy
  control-flow lines sequentially.
- `Gosub` and `Goto` preserve their target label. They do not yet invoke labels or alter the current script instruction
  pointer.
- Control/scheduler request state is saved in OpenYAMM save version 72.

### 2. Variables, Expressions, Arrays, And Assignment Commands

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `set` | 1,497 | Assign variable to token/expression. |
| assignment-form tokens | 2,435 | Lines parsed as `<target> = <expr>`. |
| `ArrayPut` | 600 | Write indexed script array. |
| `ArrayGet` | 126 | Read indexed script array. |
| `GetRandomInt` | 243 | Inclusive/integer random into destination variable. |
| `GetRandomFloat` | 63 | Float random into destination variable. |
| `Add`, `Sub`, `Mul` | 248 | Mutating arithmetic helpers. |
| `VecScale`, `MoveDir`, vector helpers | 48+ | Vector math and movement support. |
| `GetTime` | 80 | Read current world/script time. |

Implementation requirements:

- Add one authoritative MM9 script expression evaluator. Do not spread ad hoc parsing into each command.
- Maintain typed-but-loose variables: numeric, string, handle, boolean. Source scripts mix strings and numeric suffixes
  (`sMonsterA + Script`, `sWaypoint + nIndex`, etc.).
- Support script locals, object fields, map globals, global console vars, arrays, and built-in constants.
- Assignment-form commands are not function calls. They are variable writes and arithmetic/string expression evaluation.
- Preserve case-insensitive lookup for command names, but preserve original variable/property spelling where it affects
  object/property lookup.

Top assignment targets by count:

| Target | Count | Example |
| --- | ---: | --- |
| `current_group` | 288 | `MM_ARSLEGAARD.scr:141 current_group = Group1` |
| `goto_location` | 288 | `MM_ARSLEGAARD.scr:142 goto_location = Work` |
| `g_ntemp` | 65 | `ANIMTEST.scr:241 g_nTemp = 1` |
| `ntemp` | 61 | `BELLWEIGHT.scr:25 nTemp = 1` |
| `g_btemp` | 58 | `AICOMMON.inc:123 g_bTemp = TRUE` |
| `g_htarget` | 52 | `AICOMMON.inc:478 g_hTarget = NULL` |
| `ncounter` | 51 | `BATTLEJUKEBOX.scr:77 nCounter = 0` |
| `nmarker` | 50 | `DP_GUARD1.scr:82 nMarker = nCount * 3 + 4` |
| `index` | 48 | `MM_ARSLEGAARD.scr:100 index = 0` |
| `goto_marker` | 36 | `MM_ARSLEGAARD.scr:65 goto_marker = marker_work + npc_id` |
| `smarker` | 35 | `DC_SARGENT.scr:64 sMarker = sMarkerName + 1` |
| `LISTINDEX` | 31 | `CHASM_GHOSTSPAWNER.scr:34 LISTINDEX = LISTLAST` |

### 3. World Object Registry And Handles

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `GetObjectHandle` | 1,903 | Resolve object by name/string into handle variable. |
| `GetMyHandle` | 406 | Store active object handle. |
| `GetPlayerHandle` | 77 | Store party/player object handle. |
| `GetClassName` | 48 | Read class name for object handle. |
| `IsPlayer` | 38 | Test player object handle. |
| `IsClass` | 30 | Test class inheritance/type. |
| `GetTarget` | 25 | Read AI/object target handle. |
| `CreateObjectLink` | 39 | Link active object lifetime to another object. |

LithTech meaning:

- `ILTServer::FindNamedObjects` resolves names to object handles
  ([iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L203)).
- Object messages are sent to `ObjectMessageFn` via `SendToObject`
  ([iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L276)).
- Link break callbacks exist as `MID_LINKBROKEN`
  ([iltbaseclass.h](../../mm9/lithtech/sdk/inc/iltbaseclass.h#L547)).

Implementation requirements:

- Add a DAT-world object registry keyed by stable runtime handle, source object index, map id, object name, class,
  RUDE binding, and original DAT/LithTech ids where available.
- Handles must remain valid across save/load or be remapped through stable ids.
- Object name lookup should support exact source names and case-insensitive aliases where MM9 scripts rely on them.
- `NULL` is a first-class handle value, not an empty string accident.

### 4. Object Transform, Movement, Collision, And Physics Queries

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `GetPOS` | 248 | Read object/world position into vars. |
| `SetPos` | 67 | Teleport/set object position. |
| `MoveToPos` | 67 | Move object toward position, then callback. |
| `WalkTo` | 198 | AI/object walk to target handle/marker, then callback. |
| `RunTo` | 90 | AI/object run to target handle/marker, then callback. |
| `MoveDir` | 24 | Move along vector/direction at speed, then callback. |
| `FaceObject` | 126 | Rotate object toward target object. |
| `FaceDir` | 67 | Set facing direction. |
| `GetFaceDir` | 47 | Read orientation vector. |
| `RotateDir` | 28 | Rotate direction vector by angle. |
| `OnStuck` | 45 | Register movement blocked callback. |
| `OnObstacle` | 44 | Register obstacle callback. |

LithTech meaning:

- Object transform/movement services live on `ILTServer`: `GetObjectPos`, `SetObjectPos`, `MoveObject`,
  `GetStandingOn`, `GetLastCollision`
  ([iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L175)).
- Movement of physical objects performs collision processing; player-like movement can use a specialized mover
  ([moveobject.cpp](../../mm9/lithtech/runtime/shared/src/moveobject.cpp#L1526)).
- Object dims and standing-on plane/object data are runtime physics concepts
  ([shared_iltphysics.cpp](../../mm9/lithtech/runtime/shared/src/shared_iltphysics.cpp#L76)).
- `MID_TOUCHNOTIFY` is emitted for collisions with objects or static world geometry
  ([iltbaseclass.h](../../mm9/lithtech/sdk/inc/iltbaseclass.h#L540)).

Implementation requirements:

- DAT world view should expose the same gameplay-facing movement/collision services as BLV/ODM views, but implemented
  with MM9/LithTech semantics for world objects.
- Movement commands must be asynchronous: start movement now, update over time, call success/stuck/obstacle labels.
- Collision resolution should use world BSP/physics hull data from DAT where available, not texture UVs or render-only
  triangles as the authoritative movement source.
- Support object dimensions, flags (`FLAG_SOLID`, `FLAG_GOTHRUWORLD`, `FLAG_TOUCH_NOTIFY`, `FLAG_RAYHIT`), touch
  notifications, ground plane/standing object, wall sliding, and blocked movement reporting.
- `WalkTo`/`RunTo` speeds should be data/stat driven where scripts set `WalkVel`, `RunVel`, `FlyVel`, etc.

Current status:

- `GetPOS` and `SetPos` are implemented against an MM9 runtime object-position state map. This preserves script-visible
  transform variables before DAT object transforms are wired into the world view.
- `FaceDir`, `GetFaceDir`, and `RotateDir` are implemented against runtime facing/vector variables. `RotateDir`
  performs the simple script-visible XY plane rotation needed by existing scripts; real object orientation application
  still belongs to DAT actor/world services.
- `VecScale` mutates the three named vector component variables in place using the evaluated scale expression.
- `VecNorm` normalizes three named vector component variables in place while preserving the script string form of
  fractional results for later expression reads.
- `MoveToPos`, `WalkTo`, `RunTo`, `MoveDir`, `FaceObject`, and `Stop` are implemented as pending movement/action
  request records with source, owner handle, target handle/position/direction, speed/distance, and callback labels.
  The script runtime now exposes `dispatchMovementResult(...)` so the future DAT physics step can report arrival,
  stuck, obstacle, obstacle-avoided, and touch outcomes back into the authored success and `On*` labels with the
  correct owner context. Collision detection, wall sliding, step height, and choosing those outcomes remain DAT physics
  work.
- `Rotate` is implemented as a movement/action request with direction, angle, speed, and optional callback. Real object
  angular integration remains DAT actor/world work.
- `Spawn` allocates a stable synthetic spawned-object handle, stores the requested spawn position, writes the destination
  handle variable, and records the spawn request. Real DAT object creation and actor/model instantiation remain deferred.
- `GetDistance` computes distance from the runtime object-position state.
- `GetDims` reads `DimsX`, `DimsY`, and `DimsZ` object stats into destination variables.
- `SetVelocity` records `VelocityX`, `VelocityY`, and `VelocityZ` object stats.
- `CreateObjectLink` records active-object links, `RunScript` records the active object's script override,
  `SetModelFilenames` records model/texture filenames for the active object, and `AttachProp` records an attachment
  request with model, texture, socket, and attached-object handle.
- `GetObjects` queries package-backed object bindings by class/name into a script handle array and count. Real DAT world
  object registry lookup and radius filtering remain deferred.
- `GetStatStr` and `SetPropString` use an MM9 object string-property bag. `ScriptName` falls back to the runtime script
  override or active script source when no explicit string property exists.
- Movement request, spawn request, transform, facing, object-link, script-override, and synthetic spawn-handle state is
  saved in OpenYAMM save version 69. Model filename, attachment, and promotion request state is saved in version 71.
  Object string-property state is saved in version 74.

### 5. Object Properties, Stats, Flags, And Visibility

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `SetStat` | 177 | Set object stat/property such as velocity/range. |
| `GetStat` | 114 | Read object stat/property. |
| `SetPropNumber` | 74 | Set active object property. |
| `SetFlag` | 255 | Enable object flag. |
| `ClearFlag` | 258 | Disable object flag. |
| `RemoveObject` | 227 | Delete/deactivate object. |
| `SetModelFilenames` | 27 | Change model/skin. |
| `AttachProp` | 29 | Attach prop model to socket/object. |

LithTech meaning:

- World-file properties are read by typed getters like `GetPropString`, `GetPropReal`, `GetPropLongInt`
  ([iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L705)).
- Object flags are a core runtime concept, including `FLAG_MODELKEYS`
  ([ltbasedefs.h](../../mm9/lithtech/sdk/inc/ltbasedefs.h#L1946)).
- Common flag mutation exists through `ILTCommon::SetObjectFlags`
  ([iltcommon.h](../../mm9/lithtech/sdk/inc/iltcommon.h#L226)).

Implementation requirements:

- Define an MM9 object property bag seeded from DAT object properties and script defaults.
- Known property/stat names should map to typed runtime fields (`DoRude`, `WalkVel`, `RunVel`, `FlyVel`,
  `HitPoints`, `AttackRange`, visibility/solid/rayhit/model keys).
- Unknown properties should remain in the property bag and be saved, not discarded.
- `RemoveObject` should mark runtime object removed, detach links, cancel scheduled callbacks, and persist removal.

Current status:

- `SetStat`, `GetStat`, `SetPropNumber`, `SetPropString`, and `GetStatStr` are backed by runtime object property/stat
  bags so script-visible object state is not discarded before DAT objects provide authoritative typed fields.
- `SetFlag`, `ClearFlag`, and `RemoveObject` record runtime object flag/removal state. Real visibility, solidity,
  ray-hit, and world-scene removal remain object/world work. `RemoveObject` also detaches runtime object links, removes
  that object's trigger registrations, cancels pending scheduled invocations, and clears registered callbacks for the
  removed object.
- `GetObjectMinMax` writes deterministic min/max variables from stored object stat fields (`MinX` through `MaxZ`) and
  defaults missing bounds to zero until DAT object extents are authoritative.
- `SetModelFilenames`, `AttachProp`, and `DetachProp` record model/attachment requests. Attachment request operation
  state is saved in OpenYAMM save version 75.

### 6. Triggers, Messages, And Event Callbacks

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `AddTrigger` | 1,289 | Map incoming message name to label. |
| `Trigger` | 1,573 | Send message to object/handle. |
| `RemoveTrigger` | 93 | Unregister trigger message. |
| `AddModelKey` | 118 | Register animation string-key callback. |
| `OnDamage` | 118 | Register damage callback. |
| `OnPostStartWorld` | 147 | Register after-world-start callback. |
| `OnPostMiniSaveLoad` | 116 | Register after mini-save load callback. |
| `OnPostSaveLoad` | 76 | Register after save/load callback. |
| `OnTouchNotify` | 30 | Register touch/collision callback. |
| `OnDeath` | 33 | Register death callback. |
| `OnFoundPlayer`, `OnFoundTarget`, `OnLostTarget` | 141 | AI perception callbacks. |
| `OnTargetDead`, `OnTargetBeyondDist`, `OnAlert` | 100 | AI/target state callbacks. |

LithTech meaning:

- Representative trigger object receives touch or trigger messages, waits for delays/activation counts, then sends
  target messages ([Trigger.cpp](../../mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp#L466),
  [Trigger.cpp](../../mm9/lithtech/NOLF/ObjectDLL/Trigger.cpp#L771)).
- Object messages are dispatched to `ObjectMessageFn` through the server API
  ([iltserver.h](../../mm9/lithtech/sdk/inc/iltserver.h#L276)).
- Model string keys require `FLAG_MODELKEYS` and arrive as `MID_MODELSTRINGKEY`
  ([iltbaseclass.h](../../mm9/lithtech/sdk/inc/iltbaseclass.h#L553),
  [s_object.cpp](../../mm9/lithtech/runtime/server/src/s_object.cpp#L180)).

Implementation requirements:

- Add a message bus scoped to the active MM9 world/map. It must route by handle, name, class, and special handles
  (`hMe`, player, target, object arrays).
- `AddTrigger` should register message-name to label on the current object. `Trigger hObj, On` should resolve
  `hObj` and invoke the registered `On` label on that target object.
- Callback registration persists across save/load where MM9 expects object scripts to keep their handlers.
- Engine events (`touch`, `damage`, `death`, `target lost`, `model key`) should enqueue script invocations with the
  same active owner/sender/params model as object activation.

Current status:

- `AddTrigger` registers one label per current object/message and replaces existing registrations for the same
  map/object/message. `RemoveTrigger` removes them, and `Trigger` records resolved dispatches.
- `Trigger` now resolves package-backed target object handles, looks up the target object's registered message label,
  temporarily switches to the target owner context, and runs the registered label through the generated Lua runtime.
  This covers package/runtime message routing before the DAT object registry exists; real world object messaging,
  delayed trigger objects, activation counts, and touch-driven trigger dispatch remain actor/world scheduler work.
- Callback commands are recorded with owner map/object, source, kind, selector, label, and line metadata. This includes
  the later
  aliases `OnDamageDone`, `OnStuckDone`, `OnObstacleAvoided`, `OnCongestion`, `OnDeathDone`, `OnDoor`, `OnPathClear`,
  `OnTargetOutOfRange`, `OnProjectile`, `OnAvoidingObstacle`, `OnHelp`, `OnWorldSwitch`, `OnEnrage`,
  `OnEnrageDone`, `OnFear`, `OnFearDone`, `OnPlayerInterrupt`, and `OnTargetHit`.
- The script runtime can dispatch registered object callbacks by kind/selector and owner map/object. Real engine event
  producers for touch, damage, death, target changes, model keys, and lifecycle events are still pending the MM9
  actor/world scheduler.

### 7. AI, Combat, Awareness, And Targeting

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `Target` | 321 | Set current target handle. |
| `Stop` | 310 | Stop motion/action/animation. |
| `SetIdle` | 74 | Enter idle AI state. |
| `AIGetDistance` | 52 | Distance to target/object into variable. |
| `AddFriend`, `AddEnemy` | 103 | Faction/perception lists. |
| `Attack` | 31 | Start melee/active attack, then callback. |
| `CanAttack` | 28 | Test melee attack possibility into variable. |
| `IsAttacking` | 25 | Test active attack state. |
| `RunScript` | 25 | Switch/load script behavior. |
| `CanRangeAttack`, `RangeAttack`, range helpers | lower frequency | Ranged combat checks and actions. |

Implementation requirements:

- Separate script command dispatch from AI policy. Commands should call an MM9 actor controller service.
- Actor controller needs target handle, faction relations, perception state, movement state, attack state, cooldowns,
  and callbacks.
- Combat commands should use shared gameplay damage/projectile systems where possible, but movement and collision should
  follow DAT/LithTech world services.
- Distance/clear-shot checks should use the same DAT collision/raycast service as movement and projectiles.

Current status:

- `Target` and `GetTarget` store/read the active object's current target handle in runtime state.
- `SetIdle` records an idle AI state and clears the active attack state for the current object.
- `Walk` and `Run` record simple movement requests and update the active object's AI state.
- `AddFriend` and `AddEnemy` preserve authored class/name relation tokens in per-object relation lists. These are
  intentionally not resolved to object handles because scripts use them as class/faction filters.
- `IsFriend` tests a resolved target handle against the active object's preserved friend tokens by handle, object name,
  and object class.
- `RemoveFriend` and `RemoveEnemy` remove authored class/name relation tokens from the active object's relation lists.
- `SendAlert` records an AI alert request with the resolved target handle.
- `IsAI`, `IsActor`, and `IsVisible` write deterministic result variables from current object bindings/removal state.
- `IsOnGround`, `IsClearShot`, `FindTargets`, `HasRangeAttack`, and `IsTargetInRange` write deterministic variables
  from runtime state. Standing info, raycast checks, target acquisition, and attack-range policy remain
  actor-controller/DAT collision work.
- `AIGetDistance` writes a deterministic distance from the runtime object-position state. This is enough for scripts and
  tests before DAT object transforms are authoritative; collision/raycast-aware distance remains actor-controller work.
- `CanAttack`, `CanRangeAttack`, and `IsAttacking` write destination variables from runtime target/attack state.
  Clear-shot, cooldown, range, and melee reach checks remain actor-controller and DAT collision work.
- `Attack` and `RangeAttack` record AI attack requests, mark the active object attacking, and register completion
  callback labels. Real combat, animation coupling, projectiles, and damage dispatch remain shared gameplay/backend work.
- `Damage` records target, amount, damage type, and reaction flag as a damage request. When the target is a
  package-backed MM9 object with a runtime `HitPoints` stat, it subtracts health, clamps at zero, dispatches
  `OnDamage`/`OnDamageDone`, and marks/removes dead objects while dispatching `OnDeath`/`OnDeathDone`. Shared combat
  damage resolution, armor/resistance math, loot, and animation coupling remain backend work.
- `Die` marks the active object dead, non-attacking, and removed in runtime state. Real death animation, loot, linked
  object cleanup, and callback dispatch remain actor/world work.
- `ExitScript` is accepted as a control request, matching the generated legacy command stream.
- `Subtract` is accepted as an alias for `Sub`.
- `OnAttackReady` and `OnTargetWithinDist` are accepted as callback registrations; empty labels clear/disable in source
  scripts and are treated as implemented no-ops until callback storage grows explicit clear semantics.
- `Taunt`, `Aware`, `Launch`, `Converse`, and `ResumeWait` are accepted as animation/AI-state request records with
  callback labels where the source command supplies them. Real state-machine behavior remains actor-controller work.
- `PauseWait`, `Jump`, and `BlendAnim` are accepted as animation/AI request records.
- `SetPushBack`, `RunToPos`, `WalkToPos`, `Strafe`, and `TurnLeft` are accepted as movement request records. Real
  collision-aware movement and pushback integration remain DAT/LithTech world service work.
- Vector helpers `VecAdd`, `VecSub`, `VecCross`/`GetCrossProduct`, `CalcDist`, `VecDist`, and `NormalizeVector` now
  share the pure script-variable path used by the higher-frequency vector helpers.
- `GetGameTime`, `GetPCLevel`, `GetPCVoice`, `GetVelocity`, `GetLiquidContainer`, `GetContainer`, and
  `BreakObjectLink` are accepted with deterministic runtime-state behavior or recorded control intent.
- `GetParam` and `SetParam` read and mutate the active owner script parameter vector, so later parameter reads in the
  same object/script context see authored parameter changes.
- `GetCurrAnim`, `GetAnimName`, `SetAnimPlaying`, `GetSocketPos`, `GetRightDir`, `GetForwardDir`, `GetReverseDir`,
  `GetRotation`, `GetAngleToPos`, `GetPlayersWithinDist`, `CheckWorldCollision`, `Spawn2`, `SetInt`, `IsMoving`,
  `IsFacing`, `SetTargetLostTime`, `Help`, `EstimateRangeAttackHit`, `Land`, `GetPlayerId`, and `GetPlayerNbr` are
  accepted with deterministic runtime-state behavior or request records. Real animation indices, socket transforms,
  collision traces, range-hit estimates, and player id mapping remain actor/world integration work.
- AI relation, state, attack-state, and request records are saved in OpenYAMM save version 70.
  Damage request state is saved in version 73.

### 8. Audio, Animation, Client FX, And Presentation

High-volume commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `PlaySound` | 710 | Play sound, often with callback/radius/loop flags. |
| `CacheSound` | 139 | Preload sound. |
| `PlaySoundHandle` | 69 | Play sound and store handle. |
| `GetSoundDuration` | 65 | Query sound duration into var. |
| `KillSound` | 99 | Stop sound by handle. |
| `PlayAnim` | 375 | Play model animation and callback. |
| `LoopAnim` | 224 | Loop model animation and callback/check label. |
| `CacheClientFX` | 70 | Preload named client effect. |
| `DoClientFX` | 69 | Spawn/start named client effect. |
| `RolloverText` | 58 | UI/world rollover text. |
| `Debugout`, `cprint` | 131 | Debug/console output. |
| `ScreenFadeOut`, `ScreenFadeIn`, `LetterBox` | 113 | Cutscene UI state. |

LithTech meaning:

- World `Sound` object loads sound filename/radius/volume/ambient properties and plays through `SoundMgr`
  ([ltengineobjects.cpp](../../mm9/lithtech/sdk/inc/ltengineobjects.cpp#L302)).
- Sound duration is a sound manager service (`GetSoundDuration`) in the runtime.
- Client FX are message-driven in sample game code (`MID_CLIENTFX_CREATE` is defined in
  [MsgIDs.h](../../mm9/lithtech/NOLF/Shared/MsgIDs.h#L85) and sent by
  [ClientFX.cpp](../../mm9/lithtech/NOLF/ObjectDLL/ClientFX.cpp#L128)).

Implementation requirements:

- Add script-facing audio handles with stop/query semantics. They should map to OpenYAMM mixer handles, not raw
  LithTech handles.
- Animation commands must support callbacks when an animation completes and model string-key events when enabled.
- Client FX names can initially map to OpenYAMM particle/effect descriptors, but missing FX should be logged with
  source file/line and not crash.
- Cutscene presentation commands need a shared service for screen fade, letterbox, camera mode, and UI text.

Current status:

- `CacheSound`, `PlaySound`, `Speak`, `PlaySoundHandle`, `KillSound`, and `GetSoundDuration` are implemented as
  script-visible request records in [Mm9ScriptRuntime](../../game/mm9/Mm9ScriptRuntime.cpp). `PlaySoundHandle`
  allocates stable synthetic `mm9:sound:<n>` handles, stores them in runtime state, and `KillSound` removes the active
  synthetic handle. Audio request records are saved in OpenYAMM save version 80, and `dispatchAudioResult(...)` lets
  the mixer layer report completion/stopped results so authored sound callbacks run and synthetic handles become done.
  Real OpenYAMM mixer handle binding and non-zero duration lookup remain backend work.
- `PlayAnim` and `LoopAnim` are implemented as animation request records, register completion/check callbacks, and are
  saved in OpenYAMM save version 79. `dispatchAnimationResult(...)` lets the actor/model layer report completion or
  model string-key events back into authored callback labels. Actual model playback and model-key production still
  depend on actor/model services.
- `Taunt`, `Aware`, `Launch`, `Converse`, `ResumeWait`, `PauseWait`, `Jump`, and `BlendAnim` share the same
  request/callback recording path as animation commands so their script labels are preserved before the actor
  controller exists.
- `CacheClientFX`, `DoClientFX`, and `CreateFX` are implemented as client-FX request records with resolved object
  handles. Client-FX request records are part of MM9 script runtime state and are saved/restored in OpenYAMM save
  version 82. Real particle/effect descriptors remain renderer/effects work.
- `ScreenFadeOut`, `ScreenFadeIn`, `LetterBox`, `RolloverText`, `CacheTexture`, `HidePiece`, and `DoLetter` are
  implemented as presentation request records. Presentation request records are part of MM9 script runtime state and are
  saved/restored in OpenYAMM save version 82. Real UI/camera application, model-piece visibility, item text, and texture
  preloading remain presentation-layer work.
- `OnDamage`, `OnPostStartWorld`, `OnPostMiniSaveLoad`, `OnPostSaveLoad`, `OnFoundPlayer`, `OnFoundTarget`,
  `OnTargetDead`, `OnTouchNotify`, `OnLostTarget`, `OnObjectLinkBroken`, `OnObstacle`, `OnAlert`, `OnStuck`,
  `OnDeath`, `OnCacheFiles`, `OnTargetBeyondDist`, `AddModelKey`, and `SetCallBack` are implemented as callback
  registrations with kind/selector metadata. `RemoveModelKey` removes matching model-key registrations for the active
  object. The runtime has dispatch helpers for movement outcomes, animation completion/model-key events, damage/death
  lifecycle, numbered callbacks, and generic object-scoped callbacks; producing those real events still belongs to the
  later actor, movement, model, and lifecycle services.

### 9. Gameplay/Dialogue/Party Commands

High-volume direct commands:

| Command | Count | Meaning |
| --- | ---: | --- |
| `DoRude` | 41 | Open dialogue. |
| `OnRudeExit` | 120 | Dialogue exit callback. |
| `GiveKey`, `TakeKey`, `HasKey` | 1,239 | MM9 qbit-backed key state. |
| `GiveItem`, `TakeItem`, `HasItem` | 207 | Party inventory state. |
| `GiveGold`, `GiveExp` | 190 | Party reward state. |
| `GivePromo` | 48 | Promotion/class reward. |
| console var commands | 97 | Global script state. |

Implementation requirements:

- Keep raw MM9 key ids semantically visible as `mm9.keys.<raw_id>` while storing qbit ids through the reserved range.
- Runtime command implementations should be idempotent only when the original command is idempotent. Reward commands
  must rely on script conditions/key checks, not hidden anti-duplication.
- `GivePromo` needs a promotion/class/race mapping into shared gameplay state.
- Console vars are global persistent script state; map vars and object vars are different scopes.

Current status:

- `GiveKey`, `TakeKey`, `HasKey`, item commands, gold, experience, console vars, params, and RUDE object-handle queries
  have direct runtime methods and destination-variable behavior. `GiveItem`, `TakeItem`, and `HasItem` parse generated
  metadata arguments when present and fall back to the direct Lua argument, so script-expression item ids are preserved
  even when a helper call lacks `meta.args`.
- Generic `HasGold` and `TakeGold` use the shared party gold state and record party access entries.
- Generic `GivePromo` records the requested promotion name and character token and records a party access entry so the
  command is not lost. Applying the actual MM9 promotion/class/race mapping to shared party members remains gameplay
  integration work.
- Generic `GiveAttribute` records the full argument vector in a party-command request and applies MM9 primary stat ids
  (`0..5`, plus generated names like `STAT_MIGHT`) to the active party member or whole party according to the `bAll`
  argument. Effects without a positive duration become permanent shared character stat bonuses; effects with a positive
  duration become timed magical bonuses, are tracked in MM9 script runtime state, survive state restore/save-load, and
  expire when script time advances.
- Generic `Heal` and `GetAttribute` record party-command requests. `GetAttribute` reads the current active party
  member's MM9 primary stat ids (`0..5`, plus generated names like `STAT_MIGHT`) from shared character stats including
  permanent and magical bonuses. `Heal` applies immediately to the active party member when the target resolves to the
  player handle, and to runtime object `HitPoints`/`MaxHitPoints` for package-backed object handles. Duration-based
  attribute buffs and non-player heal reactions remain gameplay/actor integration work.
- Generic `AddNPC` and `RemoveNPC` record party-command requests. `AddNPC` also writes a stable synthetic
  `mm9:npc:<id>` handle into the requested destination variable.
- Party-command request state is saved in OpenYAMM save version 75.

## Complete High-Frequency Generic Command Table

Commands below are the high-frequency generic commands not covered by direct `ctx` methods. Lower-frequency tokens and
all exact argument strings remain in `script_index.yml`.

| Command | Count | Example |
| --- | ---: | --- |
| `exit` | 7,734 | `1000T_BIGICKY.scr:27 Exit True` |
| `endif` | 3,893 | `1000T_BIGICKY.scr:48 endif` |
| `gosub` | 3,425 | `1000T_BIGICKY.scr:32 Gosub CheckTrigger` |
| `if` | 2,979 | `1000T_BIGICKY.scr:56 if (b_Direction==0)` |
| `getobjecthandle` | 1,903 | `1000T_CIRCLESHOOTER.scr:98 GetObjectHandle sStopName, hTrigger` |
| `set` | 1,497 | `ABRIEL.scr:115 set bACTIII FALSE` |
| `wait` | 1,250 | `1000T_BIGICKY.scr:101 Wait 0, 0.5, Main2` |
| `if(` | 900 | `1000T_BIGICKY.scr:62 if( LISTINDEX==LISTLAST )` |
| `playsound` | 710 | `1000T_BIGICKY.scr:71 playsound Sounds\\AnimSounds\\evileyeflap.wav DoNothing 1000 400 FALSE 90` |
| `else` | 602 | `1000T_BIGICKY.scr:46 else` |
| `arrayput` | 600 | `BATTLEJUKEBOX.scr:89 ArrayPut spSounds, 0, sounds\\Weapons\\nmetalhollow.wav` |
| `getmyhandle` | 406 | `1000T_BIGICKY.scr:83 GetMyHandle hMe` |
| `playanim` | 375 | `1000T_SORCSTATUES.scr:49 PlayAnim Taunt, StartSequence` |
| `target` | 321 | `1000T_CIRCLESHOOTER.scr:65 Target hPlayer, TRUE` |
| `stop` | 310 | `1000T_FLYINGCREATURE_.scr:47 Stop` |
| `clearflag` | 258 | `1000T_BIGICKY.scr:84 ClearFlag hMe, FLAG_SOLID` |
| `setflag` | 255 | `1000T_BIGICKY.scr:85 SetFlag hMe, FLAG_GOTHRUWORLD` |
| `getpos` | 248 | `1000T_CIRCLESHOOTER.scr:89 GetPOS LISTOBJECT, xMe,yMe,zMe` |
| `getrandomint` | 243 | `1000T_BIGICKY.scr:79 GetRandomInt 0, 100, TRAVERSERADIUS` |
| `@m` | 235 | `ATLIPROMO.scr:86 @m 2 : 45 givekey givekey` |
| `removeobject` | 227 | `1000T_FLYINGCREATURE_.scr:48 RemoveObject hMe` |
| `loopanim` | 224 | `1000T_BIGICKY.scr:38 LoopAnim Hang, 0, CheckTrigger` |
| `walkto` | 198 | `ABRIEL.scr:35 walkto g_hobject 1 DoNothing` |
| `add` | 182 | `ABUWATER.scr:42 Add nDestPosY, nDimsY` |
| `setstat` | 177 | `1000T_BIGICKY.scr:88 SetStat hMe, FlyVel, nSpeed` |
| `goto` | 158 | `AKE.scr:30 goto Onexit` |
| `onpoststartworld` | 147 | `AKERETAINER.scr:53 OnPostStartWorld Init` |
| `cachesound` | 139 | `AK_GIANTIMP.scr:32 CacheSound "sounds\\animsounds\\gezzampt\\aware.wav"` |
| `arrayget` | 126 | `AICOMMON.inc:121 ArrayGet g_hObjectArray, g_nTemp, g_hObject` |
| `faceobject` | 126 | `AICOMMON.inc:253 FaceObject g_hResurrect, 450` |
| `addmodelkey` | 118 | `AICOMMON.inc:529 AddModelKey DoResurrection, DoResurrectionTrigger` |
| `ondamage` | 118 | `AITEST.scr:54 OnDamage OnDamage` |
| `onpostminisaveload` | 116 | `AKE.scr:226 OnPostMiniSaveLoad PostMiniSaveLoad` |
| `getstat` | 114 | `1000T_BIGICKY.scr:86 GetStat hMe, FlyVel, nSpeed` |
| `spawn` | 109 | `AK_IMPGATE.scr:205 Spawn hCreature, xMe, yMe, zMe, SPAWN_PARAM` |
| `killsound` | 99 | `ABUWATER.scr:60 KillSound hWaterSound` |
| `removetrigger` | 93 | `AK_IMPGATE.scr:241 RemoveTrigger spawn` |
| `runto` | 90 | `ARENACREATURE.scr:71 runto g_hobject 128 OnArrive` |
| `gettime` | 80 | `ATTACK.inc:63 GetTime g_nLastAttackTime` |
| `endwhile` | 79 | `AICOMMON.inc:159 endwhile` |
| `getplayerhandle` | 77 | `1000T_CIRCLESHOOTER.scr:56 GetPlayerHandle hPlayer` |
| `onpostsaveload` | 76 | `AKERETAINER.scr:55 OnPostSaveLoad Init` |
| `debugout` | 76 | `ANIMTEST.scr:259 Debugout sTemp` |
| `setidle` | 74 | `ATTACK.inc:103 SetIdle` |
| `cacheclientfx` | 70 | `AK_GIANTIMP.scr:31 CacheClientFX SPELL_BLACKSMOKE` |
| `playsoundhandle` | 69 | `AKE.scr:51 Playsoundhandle voices\\cinema\\socialism\\ake01.wav, soundhandle, 768, FALSE, 100` |
| `doclientfx` | 69 | `AK_GIANTIMP.scr:46 DoClientFX g_hMyObject, SPELL_BLACKSMOKE, TRUE, TRUE` |
| `movetopos` | 67 | `1000T_CIRCLESHOOTER.scr:90 MoveToPos xMe,yMe,zMe, 500, UpdatePOS` |
| `setpos` | 67 | `AKE.scr:134 SetPos g_hMyObject,3328.0,1344.0,-480.0` |
| `facedir` | 67 | `AKE.scr:135 FaceDir 0,0,0,0` |
| `getsoundduration` | 65 | `AKE.scr:52 GetSoundDuration , soundhandle, sounddur` |
| `getrandomfloat` | 63 | `AICOMMON.inc:172 GetRandomFloat 2,10,g_nRandom` |
| `onfoundplayer` | 63 | `ATLIPROMO.scr:42 OnfoundPlayer OnLeave` |
| `rollovertext` | 58 | `AK_GUARDESCAPE.scr:45 RolloverText 150, 1, 5000, 4000` |
| `while(` | 56 | `BATTLEJUKEBOX.scr:78 while( nCounter<NUMSOUNDS )` |
| `cprint` | 55 | `ANIMTEST.scr:132 cprint backpedal` |
| `addfriend` | 54 | `AICOMMON.inc:455 AddFriend g_sTemp` |
| `aigetdistance` | 52 | `ATTACK.inc:229 AIGetDistance g_hTarget, g_nDist1` |
| `addenemy` | 49 | `AICOMMON.inc:438 AddEnemy AIBase` |
| `onfoundtarget` | 49 | `ANIMTEST.scr:226 OnFoundTarget OnFoundTarget` |
| `setcallback` | 49 | `C0TEST.scr:11 SetCallBack 0, OnZoomWait` |
| `getclassname` | 48 | `AICOMMON.inc:454 GetClassName g_hMyObject, g_sTemp` |
| `givepromo` | 48 | `ILSHEALERROOM.scr:127 GivePromo Lich Char1` |
| `getfacedir` | 47 | `ALTCINEMAMGR.scr:193 GetFaceDir hLocation, dx,dy,dz` |
| `onstuck` | 45 | `1000T_BIGICKY.scr:90 OnStuck TraverseResume` |
| `onobstacle` | 44 | `BASE.inc:86 OnObstacle BaseObstacle` |
| `sub` | 41 | `ABUWATER.scr:46 Sub nDestPosY, nWaterToLeave` |
| `createobjectlink` | 39 | `AICOMMON.inc:383 CreateObjectLink g_hDeathTarget` |
| `screenfadeout` | 39 | `ARGUMENT.scr:157 ScreenFadeOut 1` |
| `screenfadein` | 38 | `ARGUMENT.scr:178 screenfadein 1` |
| `isplayer` | 38 | `BASECRAWL.inc:697 IsPlayer g_hTarget,g_bTemp` |
| `letterbox` | 36 | `ALTCINEMAMGR.scr:224 LetterBox True` |
| `ontargetbeyonddist` | 36 | `BASE.inc:450 OnTargetBeyondDist g_nMaxEvadeDist, BeAggressive` |
| `onalert` | 34 | `BASE.inc:1281 OnAlert BaseAlert` |
| `ondeath` | 33 | `AICOMMON.inc:513 OnDeath OnDeath` |
| `oncachefiles` | 32 | `AK_GIANTIMP.scr:14 OnCacheFiles CacheFiles` |
| `attack` | 31 | `ABRIEL.scr:136 attack OnStop` |
| `ontargetdead` | 30 | `AK_IMPGATE.scr:180 OnTargetDead Respawn` |
| `isclass` | 30 | `BASECRAWL.inc:265 IsClass g_hObject,Actor,g_btemp` |
| `ontouchnotify` | 30 | `CHESSSQUARE.scr:36 OnTouchNotify OnTouch` |
| `onlosttarget` | 29 | `ANIMTEST.scr:231 OnLostTarget OnLostTarget` |
| `attachprop` | 29 | `ARG_KIRA.scr:201 AttachProp kirasword.ABC KiraSword.dtx Sheath g_hobject2` |
| `rotatedir` | 28 | `ANIMTEST.scr:28 RotateDir g_dirX,g_dirY,g_dirZ,180` |
| `canattack` | 28 | `ANIMTEST.scr:142 CanAttack g_bTemp` |
| `setmodelfilenames` | 27 | `1000T_BIGICKY.scr:81 SetModelFilenames models\\flyingicky.abc TEXTURES\\LevelTextures\\Misc\\black.dtx` |
| `onobjectlinkbroken` | 27 | `AICOMMON.inc:515 OnObjectLinkBroken OnLinkBroken` |
| `gettarget` | 25 | `AICOMMON.inc:378 GetTarget g_hDeathTarget` |
| `runscript` | 25 | `AITEST.scr:47 RunScript g_sDefaultScript` |
| `isattacking` | 25 | `ATTACK.inc:27 IsAttacking g_bAttacking` |
| `mul` | 25 | `BASE.inc:190 Mul g_nTemp, 0.4` |
| `vecscale` | 24 | `ALTCINEMAMGR.scr:147 VecScale dx,dy,dz, dirScale` |
| `movedir` | 24 | `ALTCINEMAMGR.scr:149 MoveDir dx,dy,dz, ds, nSpeed, CameraOff` |

## Implementation Order

1. Keep generated data authoritative. Do not hand-edit generated Lua. Extend exporter/runtime and regenerate.
2. Implement an MM9 script expression/argument evaluator and variable store first. Most commands depend on this.
3. Implement DAT world object registry/handle lookup, object property bag, and stable save/load ids.
4. Implement trigger/message bus and callback scheduler. This unlocks `AddTrigger`, `Trigger`, `Wait`, `On*`, and
   activation flow.
5. Implement DAT world movement/collision/raycast services with LithTech-style object flags, touch notify, standing
   info, and async movement callbacks.
6. Wire AI actor controller commands to those world services.
7. Add presentation services for audio, animation, client FX, and cutscene UI.
8. Add focused tests that run representative labels from `AICOMMON.inc`, `BASE*.inc`, object-use scripts, trigger
   scripts, cutscene scripts, and reward/dialogue scripts. Assert state changes, callbacks, and unimplemented-command
   counts by source file/line.

## Immediate Independent Work Plan

This section is a concrete implementation plan that can be done now in `game/mm9/*` without waiting for DAT world
objects, actor animation, or movement/collision runtime integration.

Keep this work MM9-specific for now. MM6/MM7/MM8 EVT Lua uses a different command model and already talks to a
different game-facing API. MM9 scripts are LithTech-style object scripts with handles, message callbacks, loose
variables, command strings, object stats, and triggers. If a small expression/token helper later proves reusable, extract
it after the MM9 behavior is implemented and tested; do not introduce a shared abstraction up front.

### Scope Boundary

Status on 2026-05-27: the "Implement now" list below is implemented in `Mm9ScriptRuntime` and covered by
`Mm9ScriptRuntimeCommandTests`. The deferred list remains intentionally outside this batch because it needs the DAT
world/object/actor services that are being integrated separately.

Implement now:

- MM9 script argument parsing and value coercion.
- MM9 script variables, assignment, arithmetic, arrays, and pure commands.
- Destination-variable semantics for existing direct query commands.
- Trigger registration/removal/dispatch bookkeeping without real cross-object routing.
- Focused unit tests for the above.

Defer until DAT world/object/actor services exist:

- Real `GetObjectHandle` lookup from DAT world objects.
- Real `GetPOS`, `SetPos`, `MoveToPos`, `WalkTo`, `RunTo`, `MoveDir`, collision, touch, obstacle, and stuck behavior.
- Actor AI and combat execution.
- Animation completion callbacks, model string keys, real OpenYAMM mixer handles, and client FX execution.
- Real cross-object `Trigger` dispatch through the DAT object registry.

### Step 1: Add MM9 Script Value And Argument Helpers

Add private helpers in [Mm9ScriptRuntime.cpp](../../game/mm9/Mm9ScriptRuntime.cpp) first. Split to
`Mm9ScriptExpression.*` only if the implementation becomes too large for the runtime file.

Required behavior:

- Parse comma-separated and whitespace-separated arguments.
- Preserve quoted strings and allow paths with backslashes.
- Preserve empty placeholder slots, especially shapes like `givekey , 47`.
- Recognize `TRUE`, `FALSE`, `NULL` case-insensitively.
- Represent values as loose MM9 script values: number, string, boolean, handle/null.
- Resolve variables from script vars, console vars, map vars, object handle vars, and property bag where appropriate.
- Preserve original text for diagnostics and unimplemented-command reporting.

Unit tests:

- `givekey , 47` keeps an empty first slot and parses `47`.
- `PlaySound "sounds\\x y.wav", Done, 1000` keeps the quoted sound path as one argument.
- `TRUE`, `False`, `NULL`, numeric literals, unknown names, and quoted strings coerce predictably.

### Step 2: Implement Expression And Assignment Basics

Implement enough expression evaluation for current generated scripts before adding world services.

Commands to handle:

- `set <var> <expr>`
- Assignment-form commands parsed as `<target> = <expr>`.
- `Add <var>, <expr>`
- `Sub <var>, <expr>`
- `Mul <var>, <expr>`
- `Div <var>, <expr>`

Expression support:

- Numeric arithmetic: `+`, `-`, `*`, `/`.
- Parentheses.
- Comparisons for later condition support: `==`, `!=`, `<`, `<=`, `>`, `>=`.
- Boolean truthiness matching source scripts.
- String concatenation-like source patterns where `+` combines string tokens and numeric suffixes, e.g.
  `sMonsterA + Script` or `sWaypoint + nIndex`.

State behavior:

- Numeric results update `scriptNumVars`.
- String/handle results update `scriptStrVars` or `objectHandleVars` when appropriate.
- If a value can be both numeric and string, preserve both the numeric and string representation, matching current
  `setScriptVariableFromString` behavior.

Unit tests:

- `set bACTIII FALSE` writes numeric false.
- `g_nTemp = 1 + 2 * 3` writes `7`.
- `sMonsterA = sMonsterA + Script` writes the expected string result.
- `Add/Sub/Mul/Div` mutate existing variables.
- Implemented pure commands do not add entries to `unimplementedCommands()`.

### Step 3: Fix Destination-Variable Semantics

Existing direct commands should keep their Lua return values, but source scripts primarily depend on destination
variables.

Update these commands:

- `HasKey <key>, <destVar>`
- `HasItem <item>, <destVar>`
- `GetParam <index>, <destVar>`
- `GetConsoleNumVar <name>, <destVar>`
- `GetConsoleStrVar <name>, <destVar>`
- `GetObjectHandleByRUDEID <rudeId>, <destHandleVar>`

Required behavior:

- Destination variables are written even when the Lua caller ignores the return value.
- Boolean query results are written as MM9 numeric booleans (`1`/`0`) and string booleans only if the existing runtime
  pattern needs it.
- Failed handle resolution writes `NULL`/empty handle consistently and still records a useful diagnostic when needed.

Unit tests:

- `HasKey TEST_KEY, g_ntemp` writes `1` or `0`.
- `HasItem 197 g_bTemp` writes destination variable despite whitespace-only separation.
- `GetParam 0, npc_id` writes numeric/string vars.
- `GetObjectHandleByRUDEID npc_id, npc_object` writes a stable synthetic handle when the package binding exists.

### Step 4: Add Script Arrays

Extend [Mm9ScriptRuntimeState](../../game/mm9/Mm9ScriptRuntime.h#L94) with array storage. Keep the shape explicit and
MM9-specific.

Commands to handle:

- `ArrayPut <arrayName>, <indexExpr>, <valueExpr>`
- `ArrayGet <arrayName>, <indexExpr>, <destVar>`

Required behavior:

- Array names are case-preserving but lookup should tolerate source command casing where practical.
- Index expressions are evaluated numerically.
- Values preserve number/string/handle shape.
- Arrays survive `state()` / `restoreState()`.

Unit tests:

- `ArrayPut spSounds, 0, sounds\\Weapons\\nmetalhollow.wav` then `ArrayGet spSounds, 0, sTemp`.
- Numeric array values round-trip.
- Missing array/index returns `NULL`, empty string, or `0` consistently and is documented by tests.
- Save/restore preserves arrays.

### Step 5: Implement Pure Generic Commands Behind `ctx:command(...)`

Extend the generic command path so it dispatches implemented pure commands before calling
`recordUnimplementedCommand(...)`.

Handle now:

- `set`
- assignment-form tokens
- `Add`, `Sub`, `Mul`, `Div`
- `ArrayPut`, `ArrayGet`
- `GetRandomInt`, `GetRandomFloat`
- `GetTime`
- `Debugout`, `cprint`

Suggested behavior:

- `GetRandomInt min, max, dest`: write an integer in range. Make tests deterministic by allowing an injectable or
  fixed-seed RNG if needed.
- `GetRandomFloat min, max, dest`: write a float/double-compatible script number.
- `GetTime dest`: write script/world runtime time. Until a world clock is available, use a runtime-owned monotonic value
  that tests can set or observe deterministically.
- `Debugout` and `cprint`: no gameplay effect. Either record to a debug-output vector or treat as implemented no-op
  with source diagnostics available in tests.

Unit tests:

- Each implemented generic command avoids `unimplementedCommands()`.
- Unknown commands still record source, normalized command, raw args, line, and raw line exactly.
- Random commands respect bounds.
- `GetTime` writes a deterministic value in tests.

### Step 6: Improve Trigger Bookkeeping

Do not implement real DAT object dispatch yet. Make the local state model correct and stable.

Commands to handle:

- Existing direct `AddTrigger <message>, <label>`.
- Existing direct `Trigger <target>, <message>`.
- New generic `RemoveTrigger <message>`.

Required behavior:

- `AddTrigger` records the active script source, map id, object index, message name, label, and source line.
- Re-registering the same message on the same object should replace the previous label unless source behavior proves it
  should stack.
- `RemoveTrigger` removes the matching registration for the active object.
- `Trigger` records a dispatch with resolved target/message text and source context.
- State survives `restoreState()`.

Unit tests:

- Add, replace, and remove trigger registration.
- Dispatch resolves script variables in target/message arguments.
- Save/restore preserves registrations and dispatch history where intended.

### Step 7: Unit Test Organization

Prefer focused doctest/unit coverage. Use a new `tests/Mm9ScriptRuntimeCommandTests.cpp` if adding to
`Mm9DialogueRuntimeTests.cpp` would make that file harder to navigate.

Test groups:

- Argument parser and coercion.
- Expression evaluator and assignment.
- Destination-variable query commands.
- Arrays and state restore.
- Pure generic command dispatch.
- Trigger bookkeeping.
- Audio, animation, client-FX, presentation, and callback request recording.
- Unknown-command diagnostics.

Regression target:

- Small generated-script fixtures should be enough. Use `script_index.yml` examples for representative command shapes,
  but do not require a DAT world or actor runtime.
- Existing MM9 dialogue/runtime tests should continue to pass.

## Done Criteria

Immediate `game/mm9/*` batch:

- Running representative object activations no longer records high-frequency generic commands as unimplemented.
- `HasKey`, `HasItem`, query commands, and expression commands write destination variables exactly as source scripts
  expect.
- Trigger/message flow can execute `AddTrigger` plus `Trigger hObj, Message` across objects.
- Save/load preserves object variables, console vars, map vars, trigger registrations, object removal, and pending waits.
- Missing long-tail commands are visible with source file/line and exact raw args, not silently ignored.

Deferred DAT/world integration:

- Movement commands report arrival, obstacle, stuck, and touch callbacks from DAT collision data.
- DAT actor, model, audio, client-FX, and presentation services consume the request records and dispatch the registered
  callbacks.

Verification commands used for this batch:

- `cmake --build build --target openyamm_unit_tests/fast -j25`
- `./build/tests/openyamm_unit_tests --test-case="MM9 script runtime*" --success=false`
- `./build/tests/openyamm_unit_tests --test-case="MM9 generated Lua script runtime*" --success=false`
- `./build/tests/openyamm_unit_tests --test-case="MM9 qbit-backed key state survives save load and restores dialogue visibility" --success=false`
- `./build/tests/openyamm_unit_tests --test-case="MM9 save load rejects stale dialogue state schema versions" --success=false`
