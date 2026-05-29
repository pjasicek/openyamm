# MMerge Lua Overlay Implementation Plan

OpenYAMM should expose the gameplay capabilities needed for MMerge parity through a clean engine-owned Lua API. The
goal is functional parity with MMerge behavior, not MMExt API compatibility or raw memory/table access.

## Principles

- Prefer authoritative data import for static table changes.
- Use map/global event overlays for event replacements and load/leave supplements.
- Expose typed hooks only for behavior that is genuinely runtime-conditional.
- Do not expose raw `Game.*`, `Map.*`, `Party.*`, `Mouse.*`, or memory-backed table mutation.
- Keep hook execution in shared gameplay systems, with indoor/outdoor code only providing world state and event
  execution.

## Runtime Shape

Lua scripts register hooks with normal event ids. Registration stores event ids in `evt.meta.map` or
`evt.meta.global`; C++ freezes that metadata with the rest of the event program. When shared gameplay reaches a hook
point, it executes all matching global hooks first, then map hooks, with a typed transient hook context.

Hook handlers receive a Lua context table built from the transient C++ context. Handlers can call typed `evt.*`
functions to set hook results such as blocked action, rest-food override, or house-topic replacement.

## First Slice

Implement the generic hook dispatcher and the high-value map-fixup hooks:

- `RegisterNpcEnterHook` / `RegisterNpcExitHook`
- `RegisterHouseTopicFilter` / `RegisterHouseTopicClickHook`
- `RegisterRestFoodCostHook`
- `RegisterGameplayActionHook`
- typed hook context/result accessors

Expose Lua facts/helpers used by those hooks and near-term MM7 overlays:

- `evt.GetPartyPosition`
- `evt.GetEnemyDetectorState`
- `evt.GetCurrentScreen`
- `evt.GetCurrentMapName`
- scalar `evt.GetMapVar` / `evt.SetMapVar`
- scalar `evt.GetGlobalVar` / `evt.SetGlobalVar`
- `evt.GetHeldItemId` / `evt.SetHeldItem` / `evt.ClearHeldItem`
- `evt.GetPartyMemberCount`
- `evt.PartyMemberHasItem`
- `evt.PartyMemberHasEquippedItem`
- `evt.SetLocalMonsterRelation`

## Deferred

Implement these when porting overlays that require them:

- outdoor edge travel override/blocking
- map-refill hook and monster item reset helpers
- transport-route override application
- party face override lifecycle
- promotion helpers
- roster/party-member lifecycle
- item generation hooks
- CrossContinents and Dragon Hatchling custom quest surfaces

## Verification

- Build `openyamm`.
- Add or reuse focused scripted/headless tests when concrete MM7 overlays are ported onto the API.
- Keep compatibility aliases in Lua helper names only; C++ should remain typed and engine-owned.
