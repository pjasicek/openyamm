# Lua-Only Event Runtime Plan

## Goal

Remove `.ir.yml` from shipped gameplay runtime and make Lua the only event
runtime format, while preserving the same functional parity that the previous
`EVT + STR` pipeline provided.

Target end state:

- gameplay loads only Lua event assets
- no `.evt`, `.str`, or `.ir.yml` are needed at runtime
- all event strings and runtime metadata needed by gameplay are carried in Lua
- legacy `EVT/STR` remains available only through tooling for import and dumps

This is the finalization step after:

- removing runtime `EVT/STR` execution
- moving legacy parsing into tools
- proving broad Lua handler coverage

## Direction Assessment

This is the correct direction.

Reasons:

- one authored/runtime scripting format
- no duplicated `IR + Lua` asset pair that can drift
- simpler load path
- simpler modding and debugging
- clearer ownership of event text and event metadata

The important constraint is that `IR` must not be removed until every runtime
responsibility it currently carries is explicitly represented in Lua.

## Current Runtime Responsibilities Still Carried By IR

Today `EventIrProgram` still provides runtime structure beyond executable Lua:

- event inventory
- local/global handler ids
- `CanShowTopic` handler ids
- on-load trigger discovery
- helper queries:
  - event hints
  - event summaries
  - opened chest ids
- structural validation coverage

To remove `IR`, each of these must move to Lua or to derived runtime structures
built from Lua.

## Required Lua Runtime Shape

The runtime should load a single Lua chunk per scope:

- `Data/scripts/Global.lua`
- `Data/scripts/maps/<map>.lua`

Each script must expose both handlers and explicit metadata.

Required Lua tables:

```lua
evt.global = evt.global or {}
evt.map = evt.map or {}
evt.CanShowTopic = evt.CanShowTopic or {}

evt.meta = evt.meta or {}
evt.meta.global = evt.meta.global or {}
evt.meta.map = evt.meta.map or {}
```

Per-scope metadata shape:

```lua
evt.meta.map.onLoad = { 7, 25, 40 }
evt.meta.map.hint = {
    [171] = "True Mettle",
}
evt.meta.map.summary = {
    [171] = '171: "True Mettle" SpeakInHouse,...',
}
evt.meta.map.openChestIds = {
    [312] = { 5, 9 },
}
```

Global scope equivalent:

```lua
evt.meta.global.onLoad = { ... }
evt.meta.global.hint = { ... }
evt.meta.global.summary = { ... }
evt.meta.global.openChestIds = { ... }
```

Notes:

- `evt.hint`, `evt.house`, and `evt.str` can still exist as compatibility
  tables if useful for generated scripts.
- runtime helper lookups should use `evt.meta.*`, not reconstruct from function
  bodies.
- summaries may be pre-generated strings rather than recomputed dynamically.

## Functional Parity Requirements

The Lua-only runtime must preserve parity with previous `EVT + STR` behavior for:

- local map events
- global events
- `CanShowTopic`
- on-load events
- event strings previously originating from `.str`
- helper surfaces previously backed by `EvtProgram + StrTable`

Specifically:

- `ShowMessage` and `StatusText` strings must be available directly from Lua
- `SpeakInHouse` labels/hints must remain available
- inspect/debug/event-summary helpers must continue working
- opened chest linkage must still be derivable for runtime helper use
- event inventory must remain deterministic and complete

## Architecture Change

### 1. Replace `EventIrProgram` in runtime with a Lua-native asset model

Introduce a new lightweight runtime asset model, for example:

- `EventLuaProgram`
- or `ScriptedEventProgram`

Suggested structure:

```cpp
struct ScriptedEventMetadata
{
    std::vector<uint16_t> onLoadEventIds;
    std::unordered_map<uint16_t, std::string> hints;
    std::unordered_map<uint16_t, std::string> summaries;
    std::unordered_map<uint16_t, std::vector<uint32_t>> openedChestIds;
};

struct ScriptedEventProgram
{
    std::string sourceText;
    std::string sourceName;
    ScriptedEventMetadata metadata;
};
```

This becomes the runtime load product instead of:

- `EventIrProgram + luaSource`

### 2. Update `EventRuntime` to bind directly from Lua programs

`EventRuntime` should stop depending on IR event enumeration.

Instead:

- load Lua chunk
- freeze handler tables directly:
  - `evt.global`
  - `evt.map`
  - `evt.CanShowTopic`
- freeze metadata tables directly:
  - `evt.meta.global`
  - `evt.meta.map`

On-load events should come from:

- `evt.meta.<scope>.onLoad`

Helper queries should come from frozen metadata:

- `hint[eventId]`
- `summary[eventId]`
- `openChestIds[eventId]`

### 3. Remove runtime YAML parsing

`GameDataLoader` should stop reading:

- `Global.ir.yml`
- `maps/<map>.ir.yml`

It should only read:

- `Global.lua`
- `maps/<map>.lua`

and build `ScriptedEventProgram` from Lua only.

## Loader Plan

### Current

Gameplay loader currently:

- reads `.ir.yml`
- parses it into `EventIrProgram`
- attaches file-backed Lua source

### Target

Gameplay loader should:

1. read `Global.lua`
2. read `maps/<map>.lua`
3. create runtime script assets from Lua only
4. store those assets in `SelectedMap`

`SelectedMap` should end up with something like:

- `std::optional<ScriptedEventProgram> localEventProgram;`
- `std::optional<ScriptedEventProgram> globalEventProgram;`

and no IR fields.

## Exporter Plan

The legacy export tool remains the authoritative importer from:

- legacy `.evt`
- legacy `.str`

But its output changes.

### Current exporter output

- `Global.lua`
- `Global.ir.yml`
- `maps/<map>.lua`
- `maps/<map>.ir.yml`
- dumps

### Target exporter output

- `Global.lua`
- `maps/<map>.lua`
- dumps only

Generated Lua must now include metadata tables directly.

For generated scripts, emitter responsibilities expand to:

- emit handler functions
- emit `CanShowTopic` functions
- emit metadata tables

Specifically:

- `evt.meta.<scope>.onLoad`
- `evt.meta.<scope>.hint`
- `evt.meta.<scope>.summary`
- `evt.meta.<scope>.openChestIds`

### Exporter source of truth

The exporter may still internally build temporary IR-like structures while
importing legacy content, but those structures must stay tool-only.

Gameplay must not know about them.

## Detailed Implementation Phases

### Phase 1. Introduce Lua-native runtime metadata model

Add:

- `ScriptedEventProgram` type under `game/events/`
- metadata containers for:
  - on-load ids
  - hints
  - summaries
  - chest links

Keep existing runtime working during this phase.

### Phase 2. Teach `EventRuntime` to freeze metadata from Lua

Add Lua-side metadata readers:

- read `evt.meta.global`
- read `evt.meta.map`

Freeze:

- handler tables
- metadata tables

Do not remove IR path yet. Support both temporarily.

### Phase 3. Update Lua exporter to emit metadata

Move generation responsibility into [EventLuaExport.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventLuaExport.cpp):

- emit normal handlers
- emit `CanShowTopic` handlers
- emit metadata tables

The metadata emitter should be deterministic and stable so generated Lua diffs
stay readable.

### Phase 4. Switch gameplay loader to Lua-only

Change [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp):

- stop reading `.ir.yml`
- read only Lua files
- construct `ScriptedEventProgram`

Change [MapAssetLoader.h](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.h):

- replace IR program fields with Lua-native program fields

### Phase 5. Remove IR from active gameplay/runtime

After loader and runtime are Lua-only:

- remove `EventIrProgram` from active gameplay code paths
- keep it only if still needed by tools, or move it to tools as well

Possible final split:

- `game/events/`
  - Lua runtime only
- `tools/legacy_events/`
  - legacy parser
  - IR-like conversion utilities if still useful for dump generation

### Phase 6. Decide whether `EventIr` stays as tool-only format

Two valid options:

1. Keep `EventIr` as a tool-only intermediate for dump generation
2. Remove `EventIr` entirely and generate dumps directly from legacy parse

Recommendation:

- keep `EventIr` as tool-only for now
- it remains useful for:
  - readable dumps
  - legacy import diagnostics
  - debugging exporter output

But it should not live in gameplay runtime paths.

## Runtime API Parity Surface

The Lua runtime must continue to support the full legacy-compatible event API
surface already established:

- `evt.global`
- `evt.map`
- `evt.CanShowTopic`
- compatibility functions such as:
  - `evt.EnterHouse`
  - `evt.PlaySound`
  - `evt.MoveToMap`
  - `evt.OpenChest`
  - `evt.SetTexture`
  - `evt.SetFacetBit`
  - `evt.SetSprite`
  - `evt.SetSnow`
  - `evt.CastSpell`
  - `evt.SummonMonsters`
  - `evt.SummonObject`
  - etc.

This plan does not reduce API surface. It only removes IR/YAML from runtime.

## Testing Plan

This migration needs both structural and behavioral coverage.

### A. Load/Binding Coverage

Add or update tests to assert:

- every scripted map loads using Lua only
- no runtime `.ir.yml` reads occur
- handler inventory is complete for:
  - local handlers
  - global handlers
  - `CanShowTopic`
- on-load metadata is read from Lua metadata tables

### B. Helper Metadata Coverage

Add focused regressions for:

- hint lookup from Lua metadata
- summary lookup from Lua metadata
- opened chest linkage from Lua metadata
- house-label/helper behavior from Lua metadata

These should replace any previous IR-backed helper assumptions.

### C. Whole-Script Execution Coverage

Keep the broad scripted-map execution sweep:

- load every scripted map
- build runtime state
- execute every local handler
- execute global handlers once
- verify no runtime errors

### D. Side-Effect Parity Coverage

Retain and extend real map regressions for:

- house entry
- cutscene/movie requests
- map transitions
- facet/texture/sprite changes
- weather/snow changes
- chest state
- spell/projectile events
- summon events

These protect the runtime boundary while IR is removed.

### E. Exporter Coverage

Add tool-side tests or headless checks for generated Lua:

- generated Lua contains metadata tables
- metadata counts match expected event inventory
- generated Lua compiles
- generated Lua-only runtime behaves the same as previous `IR + Lua` runtime

## Definition Of Done

This work is complete only when all of the following are true:

- gameplay runtime does not load `.ir.yml`
- gameplay runtime does not depend on `EventIrProgram`
- gameplay runtime uses only Lua event assets
- all runtime helper queries come from Lua metadata
- broad scripted-map load/binding/execution coverage passes
- preserved legacy dump/export tool still works
- legacy EVT/STR parsing remains tool-only

## Recommended Execution Order

1. add Lua metadata model in runtime
2. emit metadata tables from Lua exporter
3. teach `EventRuntime` to freeze metadata from Lua
4. switch gameplay loader to Lua-only
5. add/update structural helper tests
6. remove IR from active gameplay paths
7. optionally move `EventIr` to tools if it remains dump-only

## Expected Final Repository Shape

Gameplay side:

- `game/events/`
  - Lua runtime only
  - no legacy parser
  - no runtime IR

Tools side:

- `tools/legacy_events/`
  - legacy EVT parser
  - legacy STR parser
  - optional IR conversion/dump support
- `openyamm_event_asset_export`
  - legacy import
  - Lua generation
  - dump generation

Runtime assets:

- `assets_dev/Data/scripts/Global.lua`
- `assets_dev/Data/scripts/maps/*.lua`

No runtime:

- `.evt`
- `.str`
- `.ir.yml`
