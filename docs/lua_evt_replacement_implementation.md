# Lua Replacement For MM8 EVT

## Purpose

This document defines a complete implementation plan for replacing the original
MM8 `EVT` runtime with Lua scripting in OpenYAMM.

The target is not "add Lua next to EVT". The target is:

- Lua becomes the runtime-authored scripting format
- original `EVT` content is converted into Lua
- game/runtime behavior remains 1:1 compatible with original MM8 behavior for
  the supported surface
- the old `EVT` runtime path is removed from shipped runtime code after parity
  is proven

This document is meant to be executable as an end-to-end implementation plan,
not a loose design sketch.

Current update:
- the shipped gameplay runtime now uses `.ir.yml` + Lua script assets
- legacy EVT/STR parsing and dump/export live under
  [tools/legacy_events](/home/pjasicek/github/OpenYAMM/tools/legacy_events)
  and the `openyamm_event_asset_export` tool

## Executive Decision

The proposed direction is correct with two important refinements.

### What Is Correct

These are the right first-phase goals:

- keep the original MM8 event behavior 1:1
- keep the current split of:
  - one global script
  - one map-local script
- keep the event-id-driven model initially
- provide Lua with the same gameplay-facing capability surface that EVT has
- convert original content into Lua instead of hand-rewriting maps one by one

### What Should Be Adjusted

Two details should change from the initial intuition.

1. The Lua boundary should match the normalized OpenYAMM event runtime seam,
   not the raw binary EVT record format.

   The right compatibility boundary is the current combination of:

   - [`EventRuntimeState`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
   - [`ISceneEventContext`](/home/pjasicek/github/OpenYAMM/game/events/ISceneEventContext.h)
   - the public `EventRuntime` entrypoints:
     - `buildOnLoadState(...)`
     - `executeEventById(...)`
     - `canShowTopic(...)`
     - `advanceMechanisms(...)`

   That is a stable gameplay/runtime boundary. Raw EVT payload layout is not.

2. The canonical conversion input should be OpenYAMM's normalized event IR,
   not decompiled text files.

   Use:

   - `.evt`
   - `.str`
   - current `EvtProgram`
   - current `EventIrProgram`

   as the converter input path.

   Decompiled TXT can still be useful for:

   - human review
   - diagnostics
   - import fallback

   But it should not be the primary translation source if we want deterministic,
   low-risk bulk conversion.

## Current OpenYAMM Event Architecture

OpenYAMM already has a useful replacement seam.

### Current Loading Pipeline

Today the map load path is:

1. `GameDataLoader` loads local `.evt` and `Global.evt`
2. corresponding `.str` tables are loaded
3. [`EvtProgram`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h) parses raw binary instructions
4. [`EventIrProgram`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h) normalizes them into an IR
5. [`EventRuntime`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h) executes that IR into gameplay/runtime state

Relevant code:

- [`game/data/GameDataLoader.cpp`](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [`game/events/EvtProgram.h`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h)
- [`game/events/EvtProgram.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.cpp)
- [`game/events/EventIr.h`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h)
- [`game/events/EventIr.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)
- [`game/events/EventRuntime.h`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [`game/events/EventRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)

### Current Runtime Boundary

`EventRuntimeState` already captures the engine-visible effects of events:

- variables and history
- map vars and decor vars
- texture/sprite/facet/actor/chest overrides
- dialogue context
- pending map moves
- pending movie playback
- pending input prompts
- pending sounds
- portrait/spell FX requests
- mechanism state
- NPC topic/news/greeting/item overrides

`ISceneEventContext` already covers the scene-dependent actions:

- cast event spell
- summon monsters
- summon event item
- check monsters killed

This is exactly the shape we want the first Lua backend to target.

### Important Current Coverage Fact

Mechanically, OpenYAMM already covers the full raw opcode inventory it defines:

- `EvtOpcode` contains 66 enum entries including `Invalid`
- `EventIrProgram::mapOperation(...)` maps all real opcodes
- `EventRuntime::executeEvent(...)` covers all `EventIrOperation` values

That is useful, but it is not the same as saying every behavior is already
fully applied in every scene path.

### Important Current Gaps

There are runtime application gaps that should be closed before or during the
Lua migration because they would otherwise become Lua parity failures.

The main ones visible in current code are:

- `SetTexture` is consumed by indoor rendering, but not by outdoor rendering
- `SetFacetBit` is consumed by indoor rendering, but not by outdoor geometry
- `SetSprite` writes `spriteOverrides`, but that state is not currently applied
- `SetSnow` writes `snowEnabled`, but that state is not currently applied

Evidence:

- indoor uses `textureOverrides` and `facetSetMasks` in
  [`game/indoor/IndoorDebugRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorDebugRenderer.cpp)
- there is no equivalent outdoor consumer for `textureOverrides`,
  `facetSetMasks`, `spriteOverrides`, or `snowEnabled`

This matters because the migration target is behavior parity, not just parser
parity.

## Legacy Compatibility Surface

For complete replacement planning, we need to distinguish three layers:

1. original MM8 binary EVT opcode surface
2. MMExtension's decompiled Lua compatibility surface
3. MMExtension's broader event/hook ecosystem that goes beyond EVT

The first two are relevant to phase 1. The third is not.

## Original MM8 / OpenEnroth Raw Opcode Surface

OpenEnroth's local reference enum matches OpenYAMM's raw opcode inventory.

Reference:

- [`reference/OpenEnroth-git/src/Engine/Evt/EvtEnums.h`](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Evt/EvtEnums.h)
- [`game/events/EvtProgram.h`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h)

The real raw opcode surface is:

| Raw Opcode | OpenYAMM Support Today |
|---|---|
| `SpeakInHouse` | yes |
| `PlaySound` | yes |
| `MouseOver` | yes |
| `LocationName` | yes |
| `MoveToMap` | yes |
| `OpenChest` | yes |
| `ShowFace` | yes |
| `ReceiveDamage` | yes |
| `SetSnow` | partial scene application |
| `SetTexture` | partial scene application |
| `ShowMovie` | yes |
| `SetSprite` | partial scene application |
| `Compare` | yes |
| `ChangeDoorState` | yes |
| `Add` | yes |
| `Subtract` | yes |
| `Set` | yes |
| `SummonMonsters` | yes |
| `CastSpell` | yes |
| `SpeakNpc` | yes |
| `SetFacesBit` | partial scene application |
| `ToggleActorFlag` | yes |
| `RandomGoTo` | yes |
| `InputString` | yes |
| `StatusText` | yes |
| `ShowMessage` | yes |
| `OnTimer` | yes |
| `ToggleIndoorLight` | indoor only, as expected |
| `PressAnyKey` | yes |
| `SummonItem` | yes |
| `ForPartyMember` | yes |
| `Jmp` | yes |
| `OnMapReload` | yes |
| `OnLongTimer` | yes |
| `SetNpcTopic` | yes |
| `MoveNpc` | yes |
| `GiveItem` | yes |
| `ChangeEvent` | yes |
| `CheckSkill` | yes |
| `OnCanShowDialogItemCmp` | yes |
| `EndCanShowDialogItem` | yes |
| `SetCanShowDialogItem` | yes |
| `SetNpcGroupNews` | yes |
| `SetActorGroup` | yes |
| `NpcSetItem` | yes |
| `SetNpcGreeting` | yes |
| `IsActorKilled` | yes |
| `CanShowTopic_IsActorKilled` | yes |
| `OnMapLeave` | yes |
| `ChangeGroup` | yes |
| `ChangeGroupAlly` | yes |
| `CheckSeason` | yes |
| `ToggleActorGroupFlag` | yes |
| `ToggleChestFlag` | yes |
| `CharacterAnimation` | yes |
| `SetActorItem` | yes |
| `OnDateTimer` | yes |
| `EnableDateTimer` | yes |
| `StopAnimation` | yes |
| `CheckItemsCount` | yes |
| `RemoveItems` | yes |
| `SpecialJump` | yes |
| `IsTotalBountyHuntingAwardInRange` | yes |
| `IsNpcInParty` | yes |

This means the raw opcode inventory is already known and finite.

## MMExtension Decompilation Compatibility Surface

MMExtension exposes a decompiled Lua API that is larger than the raw EVT opcode
set. This is the important compatibility reference if generated Lua scripts are
meant to look like decompiled MM scripts.

Reference:

- [`reference/MMExtension/MMExtension.htm`](/home/pjasicek/github/OpenYAMM/reference/MMExtension/MMExtension.htm)

### Core Command-Level Compatibility Surface

MMExtension documents these relevant `evt.*` commands or compatibility helpers:

- `evt.EnterHouse`
- `evt.PlaySound`
- `evt.MoveToMap`
- `evt.OpenChest`
- `evt.FaceExpression`
- `evt.DamagePlayer`
- `evt.SetSnow`
- `evt.SetTexture`
- `evt.SetTextureOutdoors`
- `evt.ShowMovie`
- `evt.SetSprite`
- `evt.Cmp`
- `evt.SetDoorState`
- `evt.Add`
- `evt.Subtract`
- `evt.Set`
- `evt.SummonMonsters`
- `evt.CastSpell`
- `evt.SpeakNPC`
- `evt.SetFacetBit`
- `evt.SetFacetBitOutdoors`
- `evt.SetMonsterBit`
- `evt.Question`
- `evt.StatusText`
- `evt.SetMessage`
- `evt.SetLight`
- `evt.SimpleMessage`
- `evt.SummonObject`
- `evt.ForPlayer`
- `evt.SetNPCTopic`
- `evt.MoveNPC`
- `evt.GiveItem`
- `evt.ChangeEvent`
- `evt.CheckSkill`
- `evt.SetNPCGroupNews`
- `evt.SetMonsterGroup`
- `evt.SetNPCItem`
- `evt.SetNPCGreeting`
- `evt.CheckMonstersKilled`
- `evt.ChangeGroupToGroup`
- `evt.ChangeGroupAlly`
- `evt.CheckSeason`
- `evt.SetMonGroupBit`
- `evt.SetChestBit`
- `evt.FaceAnimation`
- `evt.SetMonsterItem`
- `evt.StopDoor`
- `evt.CheckItemsCount`
- `evt.RemoveItems`
- `evt.Jump`
- `evt.IsTotalBountyInRange`
- `evt.CanPlayerAct`
- `evt.RefundChestArtifacts`

### Script Registration Surface

MMExtension also exposes the compatibility data/handler tables:

- `evt.map`
- `evt.hint`
- `evt.str`
- `evt.house`
- `evt.CanShowTopic`
- `evt.Player`
- `evt.CurrentPlayer`
- `evt.Players.*`
- `evt.VarNum.*`

This is not the same thing as the raw binary opcode set. It is a Lua-shaped
compatibility API layered on top of it.

### What Must Be In Scope

For OpenYAMM phase 1, the must-have target is:

- full original raw opcode semantics
- enough MMExtension-style compatibility surface to execute generated
  decompiled-style Lua without semantic loss

### What Is Out Of Scope For Phase 1

Do not confuse this with all of MMExtension.

The following are explicitly out of phase 1:

- the full `events.*` hook ecosystem
- full `structs.*` memory binding
- LuaJIT FFI behavior
- editor-specific MMExtension helpers
- arbitrary modding hooks that were never part of raw EVT compatibility

The phase 1 job is "replace MM8 EVT with Lua", not "reimplement MMExtension".

## Recommended Runtime Technology

## Recommendation

Use:

- upstream Lua 5.4.x
- embedded directly as a project dependency
- with a thin handwritten C API wrapper

Do not use:

- LuaJIT
- sol2 as the primary runtime binding layer
- LuaBridge as the primary runtime binding layer

## Why This Is The Best Fit

### 1. The actual scripting need is narrow and compatibility-driven

We do not need a large object-exposure framework.

The first-phase scripting boundary is mostly:

- register functions
- push/pull integers, strings, booleans, and small tables
- keep handler references
- run chunks safely
- expose a deterministic compatibility namespace

That maps naturally to the official Lua C API.

### 2. Lua itself is designed exactly for this host/embedded shape

The official manual describes Lua as:

- "lightweight"
- "embeddable"
- a host-driven scripting library

Relevant source:

- [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/manual.html)

The manual explicitly states:

- the host program can execute chunks, read/write variables, and register C
  functions
- different chunk environments are supported
- protected calls are supported through `lua_pcall` / `lua_pcallk`
- a registry exists specifically for C-side storage

These are exactly the capabilities we need for a deterministic event runtime.

### 3. LuaJIT is the wrong compatibility target for OpenYAMM

MMExtension historically used LuaJIT, but that does not make LuaJIT the right
choice here.

Reasons:

- MMExtension is tied to Lua 5.1-era semantics and LuaJIT-specific behavior
- LuaJIT itself documents that it is API/ABI compatible with Lua 5.1 and only
  partially compatible with later Lua versions
- phase 1 does not need FFI or JIT
- OpenYAMM wants portability, predictable embedding, and a narrow host boundary

Relevant source:

- [LuaJIT extensions](https://luajit.org/extensions.html)

The LuaJIT docs explicitly note:

- it is compatible with Lua 5.1
- it only has partial compatibility with Lua 5.2+

That is a poor fit for a new engine-facing scripting boundary that we want to
keep stable for years.

### 4. sol2 is useful, but not the best fit for the core compatibility layer

sol2 is ergonomic, but it introduces a larger C++ template surface and more
policy/config complexity than this task needs.

Its own docs show:

- important safety modes are off unless manually enabled
- exception/safety behavior has a substantial configuration matrix
- Lua/LuaJIT integration behavior changes based on compile-time defines

Relevant source:

- [sol2 safety docs](https://sol2.readthedocs.io/en/latest/safety.html)

For a compatibility-critical system with a small, known API, handwritten
bindings are simpler to audit, easier to debug, and less likely to hide edge
behavior behind template machinery.

### Final Library Choice

For this project, "best Lua library" means:

- `Lua 5.4.x` as the embedded language runtime
- no general-purpose C++ binding library in phase 1
- a small OpenYAMM-owned wrapper layer over the official C API

If a higher-level binding helper is desired later for editor tools, test tools,
or non-compatibility gameplay scripting, it can be evaluated separately.

It should not own the first replacement of the EVT runtime.

## Recommended Architecture

## High-Level Shape

Introduce two layers.

### 1. Generic Lua Host Layer

Place this under a neutral layer, for example:

- `engine/scripting/`

Responsibilities:

- create/destroy `lua_State`
- load chunks from strings/files
- run protected calls
- store registry references
- error formatting and tracebacks
- sandbox library opening policy

This layer should know nothing about MM8 EVT.

### 2. EVT Compatibility Layer

Place this in game code, for example:

- `game/events/lua/`

Responsibilities:

- expose `evt.*` compatibility namespace
- expose variables/selectors/constants
- translate Lua API calls into `EventRuntimeState` and `ISceneEventContext`
- collect registered handlers
- execute on-load / per-event / can-show-topic / timer hooks

This layer is MM8-specific.

## Runtime Object Model

Introduce a Lua backend that mirrors the current runtime interface:

```cpp
class LuaEventRuntime
{
public:
    bool buildOnLoadState(...);
    bool executeEventById(...);
    bool canShowTopic(...);
    void advanceMechanisms(...);
};
```

Then add a small backend selection seam:

```cpp
enum class EventBackendKind
{
    LegacyEvt,
    Lua,
};
```

Recommended transition structure:

- keep current `EventRuntime` as the legacy backend
- add `LuaEventRuntime`
- add parity tests that execute both
- switch the game to Lua after parity is proven
- then remove runtime use of `EventRuntime`

This lets implementation happen safely.

## Critical State Rule

Do not store gameplay-persistent script state inside arbitrary Lua globals.

The canonical persistent state must remain in C++:

- `EventRuntimeState`
- party state
- map runtime state
- savegame state

Lua should be treated as:

- code
- handler registration
- static data tables

not as the authoritative storage for gameplay persistence.

This avoids impossible save/load problems with arbitrary closures and hidden
upvalues.

## Lua Script Model

## Script Files

For phase 1, use:

- one global compatibility script
- one map-local compatibility script

Suggested runtime paths:

- `assets_dev/Data/scripts/Global.lua`
- `assets_dev/Data/scripts/maps/out01.lua`
- `assets_dev/Data/scripts/maps/d05.lua`

The exact path can be adjusted, but the two-level structure is correct.

## Load Order

For each loaded map:

1. create fresh Lua state
2. open only approved libraries
3. register OpenYAMM compatibility API
4. load bootstrap compatibility helpers
5. execute `Global.lua`
6. execute map-local script
7. freeze registration tables into C++ lookup structures

Recommended library policy for phase 1:

- open:
  - base
  - table
  - string
  - math
  - coroutine
- do not open by default:
  - `io`
  - `os`
  - `debug`
  - unrestricted `package`

This keeps the environment tight and deterministic.

## Script Registration Surface

The compatibility namespace should expose:

```lua
evt.global = {}
evt.map = {}
evt.hint = {}
evt.house = {}
evt.str = {}
evt.CanShowTopic = {}
evt.VarNum = {}
evt.Players = {}
evt.const = {}
```

Notes:

- `evt.global[eventId]` is the global event handler table
- `evt.map[eventId]` is the map-local event handler table
- `evt.CanShowTopic[topicId]` contains topic visibility handlers
- `evt.hint[eventId]`, `evt.house[eventId]`, `evt.str[textId]` preserve the
  decompiled authoring shape

This gives us compatibility with generated Lua while keeping the runtime lookup
simple.

## Event Strings Strategy

The proposal to move strings into Lua is good, but they should stay structured.

Recommended format:

```lua
local STR = {
    [1] = "Some text",
    [2] = "Another text",
}

evt.str = STR
```

Why this is better than scattering literals everywhere:

- preserves original text-id references
- keeps conversion deterministic
- makes diffs and review easier
- leaves room for future localization tooling
- avoids one giant mixed code/text soup

So:

- yes, remove runtime dependence on `.str`
- no, do not inline every message directly into every function body unless the
  converter has a strong reason

## Compatibility API Design

## Guiding Rule

Expose a Lua surface that feels like MMExtension/decompiled EVT, but implement
it against OpenYAMM's normalized C++ boundary.

That means:

- Lua authoring side looks compatibility-oriented
- C++ execution side remains clean and normalized

## Mandatory Lua Command Surface

Phase 1 must expose Lua-callable equivalents for:

- all raw EVT commands
- the decompiled compatibility aliases/wrappers needed for generated scripts

### Direct Command Functions

Implement these as Lua-callable functions:

- `evt.EnterHouse`
- `evt.PlaySound`
- `evt.MoveToMap`
- `evt.OpenChest`
- `evt.FaceExpression`
- `evt.DamagePlayer`
- `evt.SetSnow`
- `evt.SetTexture`
- `evt.SetTextureOutdoors`
- `evt.ShowMovie`
- `evt.SetSprite`
- `evt.Cmp`
- `evt.SetDoorState`
- `evt.Add`
- `evt.Subtract`
- `evt.Set`
- `evt.SummonMonsters`
- `evt.CastSpell`
- `evt.SpeakNPC`
- `evt.SetFacetBit`
- `evt.SetFacetBitOutdoors`
- `evt.SetMonsterBit`
- `evt.Question`
- `evt.StatusText`
- `evt.SetMessage`
- `evt.SetLight`
- `evt.SimpleMessage`
- `evt.SummonObject`
- `evt.ForPlayer`
- `evt.SetNPCTopic`
- `evt.MoveNPC`
- `evt.GiveItem`
- `evt.ChangeEvent`
- `evt.CheckSkill`
- `evt.SetNPCGroupNews`
- `evt.SetMonsterGroup`
- `evt.SetNPCItem`
- `evt.SetNPCGreeting`
- `evt.CheckMonstersKilled`
- `evt.ChangeGroupToGroup`
- `evt.ChangeGroupAlly`
- `evt.CheckSeason`
- `evt.SetMonGroupBit`
- `evt.SetChestBit`
- `evt.FaceAnimation`
- `evt.SetMonsterItem`
- `evt.StopDoor`
- `evt.CheckItemsCount`
- `evt.RemoveItems`
- `evt.Jump`
- `evt.IsTotalBountyInRange`
- `evt.CanPlayerAct`
- `evt.RefundChestArtifacts`

### Important Classification

These commands fall into three categories.

#### A. Direct original EVT equivalents

These should map almost 1:1 to current `EventRuntime` behavior:

- `Add`
- `Subtract`
- `Set`
- `MoveToMap`
- `OpenChest`
- `PlaySound`
- `SetTexture`
- `SetSprite`
- `CastSpell`
- `SummonMonsters`
- `SummonObject`
- and so on

#### B. Compatibility aliases

These are just Lua naming/shape wrappers over existing behavior:

- `EnterHouse` -> current `SpeakInHouse` semantics
- `FaceExpression` -> `ShowFace`
- `DamagePlayer` -> `ReceiveDamage`
- `SetDoorState` -> `ChangeDoorState`
- `SetMonsterBit` -> `ToggleActorFlag`
- `SetMonsterGroup` -> `SetActorGroup`
- `SetMonsterItem` -> `SetActorItem`
- `SetMonGroupBit` -> `ToggleActorGroupFlag`
- `Jump` -> `SpecialJump` or `Jmp` depending on emitted shape

#### C. Decompiler/runtime convenience helpers

These need explicit Lua-side support even though they are not raw binary EVT
instructions:

- `SetMessage`
- `SimpleMessage`
- `Question`
- `CanPlayerAct`
- `RefundChestArtifacts`
- `SetTextureOutdoors`
- `SetFacetBitOutdoors`

These should be designed consciously and not left as undocumented oddities.

## Variable And Selector Compatibility

Phase 1 must also expose:

- `evt.VarNum.*`
- `evt.Players.*`
- `evt.Player`
- `evt.CurrentPlayer`

OpenYAMM already has the base inventories in:

- [`EvtEnums.h`](/home/pjasicek/github/OpenYAMM/game/events/EvtEnums.h)

Implementation recommendation:

- generate the compatibility constants from `EvtVariable` and
  `EvtPartySelector`, not by hand
- keep them in one central registrar file
- make Lua scripts use numeric constants identical to the event system when
  applicable

## API Boundary Mapping

Each Lua API function should do one of:

- mutate `EventRuntimeState`
- query `EventRuntimeState`
- call `ISceneEventContext`
- query `Party`
- queue pending actions in `EventRuntimeState`

This mapping should be explicit and documented in code.

Example categories:

- state-only:
  - `evt.Set`
  - `evt.Add`
  - `evt.SetNPCGreeting`
  - `evt.SetNPCItem`
- scene-context:
  - `evt.CastSpell`
  - `evt.SummonMonsters`
  - `evt.SummonObject`
  - `evt.CheckMonstersKilled`
- pending-action:
  - `evt.ShowMovie`
  - `evt.MoveToMap`
  - `evt.Question`
  - `evt.SimpleMessage`

## Recommended Internal Representation

Do not evaluate arbitrary global tables at runtime every time an event runs.

After loading the scripts, extract and freeze handler references into C++.

Recommended C++ metadata structure:

```cpp
struct LuaEventProgram
{
    std::unordered_map<uint16_t, int> globalHandlers;
    std::unordered_map<uint16_t, int> mapHandlers;
    std::unordered_map<uint16_t, int> canShowTopicHandlers;
    std::unordered_map<uint16_t, std::string> hints;
    std::unordered_map<uint16_t, uint32_t> houses;
    std::unordered_map<uint32_t, std::string> strings;
    std::vector<uint16_t> onLoadEventIds;
    std::vector<uint16_t> onLeaveEventIds;
    std::vector<LuaTimerTrigger> timerTriggers;
};
```

Where `int` is a Lua registry reference.

This gives:

- deterministic lookup
- no repeated table traversal
- easy parity tests
- clean save/load story

## Translation Strategy

## Canonical Converter Input

Use this as the primary converter pipeline:

1. load `.evt`
2. load `.str`
3. build `EvtProgram`
4. build `EventIrProgram`
5. emit generated Lua

This is the correct pipeline because:

- the raw parser already exists
- the IR already removes many binary quirks
- strings are already resolved there
- house/NPC table-aware conversion already exists in the IR layer

## Why Not Convert From Decompiled TXT First

Decompiled text is useful, but weaker as the canonical source:

- it is one more lossy textual layer
- it is harder to make deterministic when formatting changes
- it mixes presentation concerns with semantics

So the recommendation is:

- use `EventIrProgram` as canonical converter source
- keep decompiled EVT/TXT dumps only as diagnostics and review aids

## Generated Lua Style

Generated scripts should be deterministic and boring.

Requirements:

- stable formatting
- stable ordering
- no smart rewrites
- preserve event ids exactly
- preserve topic ids exactly
- preserve string ids exactly

Generated script shape should look like:

```lua
local STR = {
    [1] = "Hello.",
    [2] = "You found something.",
}

evt.str = STR

evt.hint[151] = STR[1]
evt.house[151] = 37

evt.map[151] = function()
    evt.SetMessage(2)
    evt.SimpleMessage()
end

evt.CanShowTopic[412] = function()
    if evt.Cmp("QBits", 712) then
        return true
    end
    return false
end
```

The emitter should prefer compatibility readability over cleverness.

## Generated Trigger Metadata

Do not infer on-load/timer behavior by scanning arbitrary user Lua bodies later.

The generator should emit explicit trigger metadata, for example:

```lua
evt.triggers = {
    on_load = { 100, 101 },
    on_leave = { 200 },
    on_timer = {
        { event = 300, interval_minutes = 5 },
    },
    on_long_timer = {
        { event = 301, interval_minutes = 1440 },
    },
    on_date_timer = {
        { event = 302, month = 5, day = 17, hour = 0 },
    },
}
```

This makes runtime execution deterministic and avoids phase-1 dependency on a
full MMExtension-style helper DSL.

## Runtime Execution Model

## One State Per Loaded Map Session

Use one Lua state per active loaded map session.

That state contains:

- the compatibility namespace
- the global script
- the map-local script
- frozen handler refs

Do not keep one process-global mutable Lua state for the whole game. That makes
state isolation, map reloads, and save/load much harder.

## Save/Load Model

Do not serialize the Lua VM.

On save:

- save only gameplay/runtime state in C++

On load:

1. rebuild the Lua state
2. load global and map-local scripts
3. rebuild handler refs
4. restore C++ runtime state

This works because gameplay-persistent event state remains in:

- `EventRuntimeState`
- party state
- scene/runtime state

## Error Handling Model

Every script load and handler call must use protected execution.

Use:

- `lua_pcall` or `lua_pcallk`
- a standard traceback-producing message handler

On script error:

- log map name
- log event id
- log call kind:
  - load
  - on-load
  - event execution
  - can-show-topic
  - timer
- fail safely without corrupting engine state

For generated original-content Lua, script errors are engine bugs and should be
treated as hard failures in tests.

## Compatibility Mode And Replacement Mode

The implementation should deliberately have two runtime modes during migration.

### Mode A: Dual-Run Parity Mode

Run both:

- legacy `EventRuntime`
- new `LuaEventRuntime`

Then compare their resulting `EventRuntimeState` and scene-side effects for test
inputs.

This mode exists only for migration/testing.

### Mode B: Lua-Only Runtime Mode

The shipping target mode:

- no runtime `.evt` execution
- Lua only

After parity is proven, this becomes the default and the old runtime path is
removed from the game.

## Detailed Implementation Plan

## Phase 0: Close Legacy Runtime Application Gaps

Before replacing the interpreter, fix known current application gaps so Lua does
not inherit false negatives.

Required:

1. Apply `spriteOverrides`
2. Apply `snowEnabled`
3. Apply outdoor `SetTexture` equivalents
4. Apply outdoor `SetFacetBit` equivalents where meaningful

Without this, parity tests will fail even if Lua calls are correct.

## Phase 1: Add Generic Lua Host

Implement a generic Lua host layer under `engine/` or a similarly neutral
location.

Deliverables:

- `LuaStateOwner`
- chunk loading helpers
- protected call helpers
- registry-ref helpers
- traceback/error formatting
- minimal library-opening policy

Tests:

- create/destroy state
- load chunk from string
- registry ref roundtrip
- protected call error capture

## Phase 2: Add EVT Compatibility Runtime Skeleton

Implement a new game-side runtime layer, for example:

- `LuaEventRuntime.h/.cpp`
- `LuaEventBindings.h/.cpp`
- `LuaEventProgram.h/.cpp`

Initial responsibilities:

- build Lua state
- register `evt` namespace
- freeze handler refs from `evt.map`, `evt.global`, `evt.CanShowTopic`
- expose no-op or stub bindings first

Tests:

- handler registration from synthetic script
- lookup by event id
- topic visibility handler registration
- trigger metadata extraction

## Phase 3: Expose Compatibility Constants

Expose:

- `evt.VarNum.*`
- `evt.Players.*`
- season constants
- facet/actor/chest bit constants

Implement these from existing enums, not hardcoded string piles.

Tests:

- constants present
- constants equal expected numeric values

## Phase 4: Implement Lua Binding Surface

Implement the actual command functions.

Order the work in this sequence:

1. pure variable/state mutators
2. message/dialog functions
3. pending actions
4. scene-context actions
5. topic visibility helpers
6. compatibility aliases/wrappers

### 4A. Pure State Mutators

Implement first:

- `evt.Set`
- `evt.Add`
- `evt.Subtract`
- `evt.SetNPCTopic`
- `evt.SetNPCGroupNews`
- `evt.SetNPCGreeting`
- `evt.SetNPCItem`
- `evt.SetMonsterItem`
- `evt.SetMonsterBit`
- `evt.SetMonGroupBit`
- `evt.SetMonsterGroup`
- `evt.SetChestBit`
- `evt.SetFacetBit`
- `evt.SetFacetBitOutdoors`
- `evt.SetTexture`
- `evt.SetTextureOutdoors`
- `evt.SetSprite`
- `evt.SetSnow`
- `evt.SetLight`

### 4B. Message/Dialog/Prompt Functions

Implement:

- `evt.SetMessage`
- `evt.SimpleMessage`
- `evt.Question`
- `evt.StatusText`
- `evt.SpeakNPC`
- `evt.EnterHouse`
- `evt.CanShowTopic`

### 4C. Pending Action Functions

Implement:

- `evt.MoveToMap`
- `evt.ShowMovie`
- `evt.Jump`

### 4D. Scene-Context Functions

Implement:

- `evt.CastSpell`
- `evt.SummonMonsters`
- `evt.SummonObject`
- `evt.CheckMonstersKilled`

### 4E. Party/Inventory/Skill Functions

Implement:

- `evt.GiveItem`
- `evt.RemoveItems`
- `evt.CheckItemsCount`
- `evt.CheckSkill`
- `evt.CanPlayerAct`
- `evt.DamagePlayer`
- `evt.FaceExpression`
- `evt.FaceAnimation`
- `evt.IsTotalBountyInRange`
- `evt.CheckSeason`
- `evt.ChangeGroupToGroup`
- `evt.ChangeGroupAlly`
- `evt.MoveNPC`
- `evt.ChangeEvent`
- `evt.OpenChest`
- `evt.RefundChestArtifacts`

Each function should be backed by small, auditable C++ helpers. Do not bury
gameplay mutations directly in the raw C API glue.

## Phase 5: Implement Lua Trigger Execution

Implement the Lua backend methods:

- `buildOnLoadState(...)`
- `executeEventById(...)`
- `canShowTopic(...)`
- `advanceMechanisms(...)`

Required behavior:

- map-local event handlers override global ones where appropriate
- on-load executes in same order as legacy runtime
- can-show-topic matches legacy short-circuit behavior
- timer/date-timer behavior matches legacy runtime scheduling

This phase should still coexist with the legacy runtime.

## Phase 6: Add EventIr -> Lua Generator

Implement a deterministic generator under `tools/`, for example:

- `tools/export_evt_lua.py`
- or C++ if better aligned with existing code

Preferred implementation path:

- feed `EventIrProgram`
- emit compatibility Lua

Inputs:

- local `.evt`
- local `.str`
- global `.evt`
- global `.str`
- house table
- NPC dialog table

Outputs:

- `Global.lua`
- per-map Lua files

Generator requirements:

- deterministic formatting
- stable ordering
- escaped strings
- stable numeric ids
- generated comments only if they help auditing

## Phase 7: Add Dual-Run Parity Harness

This is the most important validation tool.

Build a parity harness that:

1. loads original EVT
2. loads generated Lua
3. executes the same event/topic/trigger in both backends
4. compares resulting:
   - `EventRuntimeState`
   - scene-context calls
   - pending actions
   - granted/removed items
   - dialogue context

This harness should be integrated into headless regression tests.

It is the safest way to prove replacement correctness.

## Phase 8: Bulk Convert All MM8 Scripts

Once the generator and parity harness are stable:

1. convert all global/local scripts
2. check generated Lua into the repo
3. run parity on the converted set
4. fix gaps until parity passes

Runtime should still be able to run legacy EVT behind a dev/test switch during
this phase.

## Phase 9: Switch Runtime To Lua

After parity is complete:

1. make Lua the default runtime backend
2. stop loading `.evt/.str` at runtime
3. keep legacy EVT parsing only in tools/tests
4. remove runtime code paths that only existed for legacy EVT execution

At this point the game is truly running on Lua.

## Phase 10: Remove Legacy Runtime Dependency

Final cleanup:

- runtime no longer depends on `EvtProgram` or `EventIrProgram`
- converter tools may still use them offline
- docs/editor/runtime all point to Lua as the authored script format

This is the point where the replacement is complete rather than hybrid.

## Testing Strategy

The migration must be test-driven. Manual spot checks are not enough.

## 1. Binding-Level Unit Tests

For every Lua-exposed command:

- set up synthetic runtime state
- call the Lua function
- assert exact state/result changes

Examples:

- `evt.Add("Gold", 100)` mutates gold
- `evt.SetNPCTopic{NPC=1, Index=2, Event=500}` updates topic override
- `evt.MoveToMap{X=1, Y=2, Z=3, Name="Out01.odm"}` queues pending move
- `evt.ShowMovie("LoseGame")` queues pending movie

## 2. Legacy-Vs-Lua Parity Tests

For every opcode family:

- build tiny one-event legacy scripts
- generate Lua
- execute both
- compare state

This should cover:

- variable math
- compare/jump flow
- party selectors
- messages
- NPC/house actions
- map moves
- movies
- timers
- topic visibility
- monster-kill checks
- chest/item mutations
- actor/group/facet/texture changes

## 3. Golden Generator Tests

For a set of fixture EVT/STR inputs:

- generate Lua
- compare against checked-in golden files

This catches accidental generator drift.

## 4. Full-Map Parity Tests

For representative maps:

- local + global on-load execution
- common interactable decorations
- house/NPC topics
- map boundary transitions
- timers
- spell-triggered events where relevant

Suggested map set:

- one outdoor early game map
- one indoor dungeon map
- one map with dense NPC topic scripting
- one map with more mechanism/chest behavior

## 5. Topic Visibility Tests

These need dedicated coverage because `CanShowTopic` is a separate execution
mode.

Cases:

- compare-only visibility
- monster-killed visibility
- nested jumps
- explicit `SetCanShowTopic`
- fallback when no handler exists

## 6. Save/Load Tests

Because script state is not serialized directly:

1. load map
2. execute Lua events that mutate runtime state
3. save
4. reload
5. rebuild Lua VM
6. assert gameplay state is preserved exactly

This is critical.

## 7. Complete Compatibility Inventory Test

Add a structural test that asserts:

- every `EvtOpcode` has a Lua compatibility implementation or alias mapping
- every required MMExtension compatibility command in the chosen phase-1 set is
  registered
- every `EvtVariable` compatibility constant is exposed

This prevents accidental holes.

## Required Phase-1 Compatibility Decisions

These decisions should be fixed before implementation starts.

### Decision 1: Compatibility Target

Phase 1 target is:

- all original MM8 EVT semantics
- plus the MMExtension-style decompiled `evt.*` compatibility surface required by
  generated scripts

Phase 1 does not target:

- the full MMExtension `events.*` hook system
- `structs.*`
- FFI
- debugger integration

### Decision 2: Runtime State Ownership

Persistent gameplay state remains in C++.

Lua is not allowed to become the authoritative owner of arbitrary persistent
map-local mutable state in phase 1.

### Decision 3: Translation Source

Canonical translation source is `EventIrProgram`, not decompiled TXT.

### Decision 4: Authoring Format

Generated Lua should preserve:

- global script
- map-local script
- event ids
- topic ids
- string ids in structured tables

### Decision 5: Shipping Runtime

Shipping runtime after replacement should not execute `.evt/.str`.

Those formats remain tooling inputs only.

## Risks And Mitigations

## Risk: Hidden behavior drift in obscure opcodes

Mitigation:

- parity harness
- opcode-by-opcode tests
- representative full-map tests

## Risk: Lua scripts accidentally rely on hidden mutable globals

Mitigation:

- keep persistent state in C++
- rebuild Lua VM on load
- lint/generated-script checks

## Risk: Runtime becomes harder to debug than legacy EVT

Mitigation:

- stable generated Lua format
- event id in every error
- map name in every error
- generator emits comments with original opcode shape where useful

## Risk: Overbuilding a general scripting platform instead of replacing EVT

Mitigation:

- phase-1 scope lock
- no full MMExtension hook ecosystem
- no general modding API first
- no object/userdata system beyond what compatibility requires

## Risk: Binding library complexity obscures bugs

Mitigation:

- use official Lua C API directly
- keep glue layer small and explicit

## Definition Of Done

The EVT replacement is complete only when all of the following are true:

- all shipped maps run on Lua scripts, not runtime `.evt/.str`
- raw original MM8 event semantics are covered
- generated Lua executes with parity against legacy runtime on regression set
- save/load works without serializing Lua VM internals
- global + map-local script split is in place
- strings are authored in Lua, not runtime `.str`
- runtime no longer needs legacy EVT execution code

## Recommended File And Subsystem Plan

Suggested additions:

- `engine/scripting/LuaStateOwner.h`
- `engine/scripting/LuaStateOwner.cpp`
- `engine/scripting/LuaRegistryRef.h`
- `engine/scripting/LuaCall.h`
- `game/events/lua/LuaEventRuntime.h`
- `game/events/lua/LuaEventRuntime.cpp`
- `game/events/lua/LuaEventBindings.h`
- `game/events/lua/LuaEventBindings.cpp`
- `game/events/lua/LuaEventProgram.h`
- `game/events/lua/LuaEventProgram.cpp`
- `tools/export_evt_lua.py`
- `tests` or headless diagnostics coverage additions in
  [`game/outdoor/HeadlessOutdoorDiagnostics.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp)
  and equivalent indoor/event-focused suites

Suggested eventual runtime removals or downgrades to tool-only use:

- runtime use of [`EvtProgram`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h)
- runtime use of [`EventIrProgram`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h)

## Final Recommendation

The correct implementation strategy is:

1. keep the current C++ event runtime boundary
2. add a Lua backend that targets that boundary
3. convert original content from `EventIr` into compatibility Lua
4. prove parity with dual-run tests
5. switch runtime to Lua
6. remove runtime EVT execution

This is the lowest-risk path to a real replacement.

It preserves original behavior, uses the codebase's current architecture
properly, and avoids turning the migration into an unbounded scripting-engine
project.

## Sources

Local reference sources used:

- [`game/events/EventRuntime.h`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [`game/events/EventRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- [`game/events/EventIr.h`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h)
- [`game/events/EventIr.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)
- [`game/events/EvtProgram.h`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h)
- [`game/events/EvtProgram.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.cpp)
- [`game/events/ISceneEventContext.h`](/home/pjasicek/github/OpenYAMM/game/events/ISceneEventContext.h)
- [`game/data/GameDataLoader.cpp`](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [`reference/OpenEnroth-git/src/Engine/Evt/EvtEnums.h`](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Evt/EvtEnums.h)
- [`reference/OpenEnroth-git/src/Engine/Evt/EvtProgram.h`](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Evt/EvtProgram.h)
- [`reference/MMExtension/MMExtension.htm`](/home/pjasicek/github/OpenYAMM/reference/MMExtension/MMExtension.htm)
- [`docs/level_editor_authoring_inventory.md`](/home/pjasicek/github/OpenYAMM/docs/level_editor_authoring_inventory.md)
- [`docs/editor_production_spec.md`](/home/pjasicek/github/OpenYAMM/docs/editor_production_spec.md)

Primary web sources used:

- [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/manual.html)
- [Lua version history](https://www.lua.org/versions.html)
- [sol2 safety documentation](https://sol2.readthedocs.io/en/latest/safety.html)
- [LuaJIT extensions documentation](https://luajit.org/extensions.html)
