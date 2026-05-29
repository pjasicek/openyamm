# Lua EVT Legacy Dependency Inventory

## Scope

This document records the repository state after the first Lua-EVT legacy-helper removal pass.

Current update:
- legacy EVT/STR parser code now lives under
  [tools/legacy_events](/home/pjasicek/github/OpenYAMM/tools/legacy_events)
- gameplay/runtime no longer carries those parser sources under `game/`

The goal of this pass was narrow:

- stop using raw `EvtProgram` / `StrTable` in active gameplay views just to:
  - resolve event hints
  - summarize linked events in inspect/debug overlays
  - derive linked chest ids
- move those helper queries onto `EventIrProgram`
- keep raw EVT loading only where it is still needed for:
  - import/conversion
  - dumps
  - diagnostics
  - selected-map transitional storage

## Completed In This Pass

### Active runtime/helper seam moved to `EventIrProgram`

These helper queries now live on `EventIrProgram`:

- `hasEvent(...)`
- `getHint(...)`
- `summarizeEvent(...)`
- `getOpenedChestIds(...)`

Files changed to use `EventIrProgram` directly:

- [EventIr.h](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h)
- [EventIr.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)
- [OutdoorInteractionController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorInteractionController.cpp)
- [OutdoorGameView.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.h)
- [OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)
- [IndoorDebugRenderer.h](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorDebugRenderer.h)
- [IndoorDebugRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorDebugRenderer.cpp)
- [GameApplication.cpp](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)

Result:

- active outdoor gameplay no longer needs raw `EvtProgram` / `StrTable` for event hinting or inspect summaries
- active indoor debug view no longer needs raw `EvtProgram` / `StrTable` for inspect summaries or mechanism binding summaries
- app view initialization no longer threads raw EVT/STR through those views

### Loader helper scans moved to `EventIrProgram`

These loader-side helper scans now use IR instead of raw EVT:

- linked chest detection for logging
- event-driven indoor texture preload discovery
- event-driven decoration sprite preload discovery

Main file:

- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)

Result:

- runtime warmup/helper extraction is now driven by IR operations where possible

## Remaining Legacy Dependencies

These are still present after pass 1 and are intentional for now.

### 1. Raw EVT/STR import and conversion

Files:

- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [EvtProgram.h](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h)
- [EvtProgram.cpp](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.cpp)
- [StrTable.h](/home/pjasicek/github/OpenYAMM/game/tables/StrTable.h)
- [StrTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/StrTable.cpp)
- [EventIr.h](/home/pjasicek/github/OpenYAMM/game/events/EventIr.h)
- [EventIr.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)

Why it remains:

- `EventIrProgram` is still built from parsed `EvtProgram + StrTable`
- this is still the import seam
- removing it requires either:
  - Lua/native-authored source as the primary loader input
  - or a standalone offline conversion pipeline that no longer depends on runtime parsing

### 2. Selected-map transitional storage

Files:

- [MapAssetLoader.h](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.h)

Fields still present:

- `localStrTable`
- `localEvtProgram`
- `globalEvtProgram`

Why it remains:

- `SelectedMap` still carries raw parsed source data alongside IR
- this is now transitional storage, not an active gameplay-view requirement
- removing it cleanly requires tightening the loader contract so only:
  - `localEventIrProgram`
  - `globalEventIrProgram`
  - optional dev/debug dump inputs
  survive past load

### 3. Dumps and diagnostics

Files:

- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)

Why it remains:

- raw EVT and STR are still used to emit legacy dumps and conversion diagnostics
- these are useful during parity work and are not part of the active runtime execution path

### 4. Build inclusion of legacy parser/runtime source

Files:

- [game/CMakeLists.txt](/home/pjasicek/github/OpenYAMM/game/CMakeLists.txt)

Why it remains:

- the repository still builds:
  - `events/EvtProgram.cpp`
  - `tables/StrTable.cpp`
- this is still required because the runtime loader/import path still depends on them

## What Was Explicitly Not Attempted In Pass 1

- deleting `EvtProgram`
- deleting `StrTable`
- removing raw EVT/STR from `SelectedMap`
- removing dump/export support
- replacing the IR import seam with Lua-native authored loading

Those are later steps. Doing them in this pass would have mixed structural migration with runtime behavior risk.

## Remaining Runtime Risk After Pass 1

The major runtime-helper risk that existed before this pass is now reduced:

- active views no longer rely on raw EVT/STR helper queries

The main remaining legacy risk is structural, not gameplay-facing:

- the loader still parses legacy source data to build IR and dump artifacts

## Recommended Next Steps

1. Remove raw `EvtProgram` / `StrTable` from `SelectedMap`.
   Keep them only in the local loader/import scope.

2. Move dump/export needs behind an explicit dev-only path.
   Do not keep raw legacy data live in the selected-map runtime object graph just for diagnostics.

3. Expand Lua/IR coverage so runtime no longer depends on legacy helper fallbacks anywhere.

4. Only after that, decide whether raw EVT/STR stays as:
   - offline import only
   - or is fully removed from the shipped runtime build

## Definition Of Done For Pass 1

Pass 1 is considered complete when:

- active gameplay views do not require raw `EvtProgram` / `StrTable`
- event hinting and inspect summaries use `EventIrProgram`
- loader helper scans use `EventIrProgram` where practical
- remaining raw legacy use is documented and constrained to loader/import/debug paths
