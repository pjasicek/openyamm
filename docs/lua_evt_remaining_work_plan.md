# Lua EVT Remaining Work Plan

## Purpose

This document defines the remaining implementation plan to finish the Lua
replacement for the original MM8 EVT runtime in OpenYAMM.

Current update:
- gameplay now loads `.ir.yml` + Lua only
- legacy EVT/STR import and dump generation are tool-only paths under
  [tools/legacy_events](/home/pjasicek/github/OpenYAMM/tools/legacy_events)

The goal is no longer to prove the direction. The Lua runtime path already
exists and is functioning. The remaining work is:

- remove legacy runtime-helper dependence
- close remaining behavior parity seams
- add broad automated coverage
- delete obsolete legacy runtime paths only after parity is proven

This is a completion plan, not a design exploration.

## Current State

What is already true:

- runtime event execution is Lua-backed
- file-backed Lua scripts are loaded and preferred when present
- the `evt.*` compatibility surface is broadly implemented
- generated Lua scripts compile and execute for real maps
- targeted regressions already cover several important event behaviors

What is still not finished:

- runtime still has some legacy `.evt` / `.str` helper dependence
- parity is still being proven incrementally through discovered seams
- broad automated coverage is not yet exhaustive enough to justify deleting
  the remaining legacy runtime path

## Execution Order

The remaining work should be done in this order:

1. remove legacy runtime-helper dependence
2. close remaining parity seams
3. add broad automated coverage
4. remove obsolete legacy runtime/helper code

This order matters.

If legacy runtime/helper paths are removed too early, the migration loses the
 fallback/reference layer before parity is proven.

## 1. Remove Legacy Runtime-Helper Dependence

### Goal

Make Lua plus native derived runtime data the only event source required for
 gameplay.

Legacy `.evt` and `.str` files should remain useful for:

- offline conversion
- diagnostics
- verification
- editor/import tooling

They should no longer be required by shipped gameplay/runtime code.

### Work Items

#### 1.1 Inventory all remaining legacy dependencies

Audit the runtime for direct or indirect dependence on:

- `localEvtProgram`
- `globalEvtProgram`
- `localStrEntries`
- `globalStrEntries`
- raw event metadata extracted only from legacy EVT/STR

Start with these files:

- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [EventDialogContent.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventDialogContent.cpp)
- [HouseInteraction.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/HouseInteraction.cpp)
- [OutdoorInteractionController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorInteractionController.cpp)

For every dependency found, classify it as one of:

- execution dependency
- runtime metadata dependency
- debug/diagnostic dependency
- editor/import dependency

#### 1.2 Replace runtime metadata uses

Replace any remaining runtime dependence on legacy event text/metadata with
 Lua-derived or native stored data.

The key metadata surfaces are:

- event hints
- house mappings
- event strings
- topic visibility helpers
- event labels used by runtime UI flows

The runtime should be able to derive these from:

- `evt.str`
- `evt.hint`
- `evt.house`
- `evt.CanShowTopic`
- `evt.map`
- `evt.global`

#### 1.3 Keep legacy only for offline and diagnostic use

After replacement:

- map loading may still import legacy sources
- converter/exporter tooling may still consume them
- diagnostics may still dump them

But gameplay/runtime execution must not require them.

### Deliverable

Gameplay runtime no longer requires legacy `.evt` or `.str` files for maps
that already have Lua scripts.

## 2. Close Remaining Parity Seams

### Goal

Eliminate remaining scene-side behavior mismatches between:

- original MM8 behavior
- the current Lua runtime path

The cannonball gravity fix is the model for this phase:

- find one concrete mismatch
- locate the runtime seam
- patch the seam
- add a focused regression

### Parity Audit Buckets

#### 2.1 Outdoor world/application

Audit and verify:

- `SetTexture`
- `SetFacetBit`
- `SetSprite`
- `SetSnow`
- `CastSpell`
- `SummonMonsters`
- `SummonObject`
- chest state changes
- monster bit toggles
- monster group changes
- door/mechanism changes

#### 2.2 Indoor world/application

Audit the same categories where applicable indoors:

- texture/facet/light changes
- chest state
- indoor mechanisms/doors
- local event geometry/application side effects

#### 2.3 Dialogue and presentation

Audit:

- `Question`
- `SimpleMessage`
- `SetMessage`
- `SpeakNPC`
- `EnterHouse`
- `CanShowTopic`
- house/NPC topic visibility
- house/NPC fallback behavior

#### 2.4 Transitions and cutscenes

Audit:

- `MoveToMap`
- `ShowMovie`
- `Jump`
- special jump
- on-load / on-leave / timer interactions around transitions

#### 2.5 Combat, event spells, and spawned projectiles

Audit:

- event spell targeting
- projectile orientation
- object flag inheritance
- gravity / no-gravity behavior
- impact semantics
- sound/effect triggering

### Method

For each event category:

1. identify the current runtime seam
2. identify one or more real map events using it
3. add a focused regression
4. fix the runtime if the regression fails

Do not try to prove parity abstractly. Use real map events wherever possible.

### Deliverable

Every known scene-application seam has at least one concrete regression that
 proves the intended runtime behavior.

## 3. Add Broad Automated Lua Coverage

### Goal

Make parity failures detectable automatically instead of discovering them only
 during gameplay.

### Coverage Layers

#### 3.1 Script-load coverage

For all scripted content:

- compile `Global.lua`
- compile every map-local Lua script
- verify handler tables are present and frozen correctly:
  - `evt.global`
  - `evt.map`
  - `evt.CanShowTopic`

#### 3.2 Static handler inventory coverage

For every scripted map:

- enumerate referenced handler ids
- verify local/global handlers are loadable
- verify file-backed and generated Lua expose the same handler presence where
  applicable

#### 3.3 Executed event coverage

Add a headless harness that executes representative event ids across all maps.

Classify events before execution into:

- safe deterministic
- scene-mutating but testable
- dialog/input dependent
- intentionally excluded destructive/random cases

For executed events, verify critical outputs such as:

- variable mutations
- pending map moves
- pending movies
- pending dialogue context
- sprite/facet/texture overrides
- monster/object spawn side effects
- projectile/effect creation
- status/message output

#### 3.4 Map sweep regression

Add a permanent regression that iterates all maps with Lua scripts and does at
 minimum:

- compile scripts
- initialize runtime
- run on-load
- execute a sampled set of local/global handlers
- assert no unresolved handler or Lua runtime failure

### Comparison Strategy

Where useful during the transition:

- compare Lua runtime result against the current IR execution path

After confidence is high:

- keep Lua-only assertions
- remove unnecessary dual-run scaffolding

### Deliverable

Automated coverage catches:

- missing handler bindings
- unresolved events
- scene-application regressions
- runtime script errors

before they are found manually in gameplay.

## 4. Final Legacy Removal Pass

### Goal

Delete obsolete runtime/helper paths only after the preceding phases are green.

### Remove

- legacy runtime execution dependence on EVT/STR
- dead helper code that only existed for runtime fallback
- temporary dual-path compatibility scaffolding that is no longer needed

### Keep

- offline import/conversion tools
- debug dump/export tools
- editor-oriented import paths, if still needed

### Final Audit

Do one final audit of:

- [GameDataLoader.cpp](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [EventRuntime.h](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.h)
- [EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- Lua script asset loading
- headless regressions
- docs

### Deliverable

Lua is the runtime event system.

Legacy EVT remains only as source/import material and diagnostic input, not as
 a live gameplay runtime dependency.

## Definition Of Done

This effort is complete only when all of the following are true:

- gameplay runtime does not require legacy `.evt` / `.str` for scripted maps
- all known remaining parity seams have dedicated regressions
- broad automated Lua coverage runs across all scripted maps
- no unresolved event/runtime Lua failures remain in the coverage harness
- obsolete legacy runtime/helper paths have been removed

## Recommended Immediate Next Step

Start with the legacy dependency inventory.

That is the correct first move because it defines exactly what still prevents
 the runtime from being fully Lua-native without deleting the safety net too
 early.
