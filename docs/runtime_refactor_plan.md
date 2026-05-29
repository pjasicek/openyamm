# Runtime Refactor Plan

## Goal

Finish the runtime refactor so gameplay logic is shared by default and only the
parts that truly depend on map representation stay tied to outdoor or indoor.

Companion plan:
- `docs/shared_system_unification_plan.md` is the concrete ownership and
  migration plan for shared indoor/outdoor HUD, UI, spell/projectile, and
  presentation systems.

Target rule:
- shared if it answers "what gameplay should happen?"
- scene-specific if it answers "how does this map type represent space,
  visibility, or geometry?"

The end state should avoid both bad extremes:
- not everything hanging under `OutdoorGameView` or `OutdoorWorldRuntime`
- not one giant monolith full of `isOutdoor` and `isIndoor` branches

## Refactor Completion Criteria

The refactor is done when all of these are true:
- app flow is screen-driven and independent from outdoor rendering
- save/load is session-driven and scene-neutral
- gameplay state lives in `GameSession` and scene runtimes, not in renderers
- `GameApplication` drives gameplay through shared interfaces, not outdoor-only
  concrete types
- indoor and outdoor each provide a scene backend behind the same seam
- shared gameplay systems are reused by both scenes where the rules are the same
- renderers only render and bridge input, without owning campaign/runtime state

## Current State

### Landed

These architecture steps are already in-tree:
- app shell:
  - `game/app/AppMode.h`
  - `game/ui/IScreen.h`
  - `game/app/ScreenManager.h`
  - `game/app/ScreenManager.cpp`
- menu screens:
  - `game/ui/MenuScreenBase.h`
  - `game/ui/MenuScreenBase.cpp`
  - `game/ui/screens/MainMenuScreen.*`
  - `game/ui/screens/LoadMenuScreen.*`
  - `game/ui/screens/NewGameScreen.*`
- session layer:
  - `game/app/GameSession.h`
  - `game/app/GameSession.cpp`
- gameplay glue:
  - `game/gameplay/GameplayController.h`
  - `game/gameplay/GameplayController.cpp`
- shared gameplay UI ownership:
  - `game/ui/GameplayUiController.h`
  - `game/ui/GameplayUiController.cpp`
  - `game/ui/UiLayoutManager.h`
  - `game/ui/UiLayoutManager.cpp`
- scene seam:
  - `game/scene/IMapSceneRuntime.h`
  - `game/scene/SceneKind.h`
  - `game/scene/OutdoorSceneRuntime.*`
  - `game/scene/IndoorSceneRuntime.*`
- event seam:
  - `EventRuntime` no longer depends directly on `OutdoorWorldRuntime`
- scene-neutral session persistence:
  - `SaveGame` now persists active scene kind plus indoor/outdoor scene state
  - save loading keeps compatibility with older version 8 saves

### Partially Landed

These are only partially complete:
- `GameApplication` still contains too much scene bootstrapping and renderer
  orchestration
- `OutdoorGameView` still mixes renderer, input bridge, and a large amount of
  gameplay-facing UI logic
- `IndoorDebugRenderer` is cleaner than before, but it is still not a pure
  renderer
- save payloads are scene-neutral, but still shaped too much like runtime
  snapshots rather than a final session model
- menu startup is restored, but the textured menu renderer still needs a proper
  fix and fallback cleanup

## What Must Be Shared

These systems should end up scene-neutral unless a concrete blocker appears:
- party state and progression
- house stock and service state
- awards, qbits, NPC availability, topic gating
- save/load session model
- gameplay time progression
- dialogue state and event messages
- inventory, item movement, held-item logic
- readable scrolls, books, character sheets, spellbook, status bar
- spell backend rules
- reward and grant logic
- event interpreter logic
- combat resolution rules
- monster decision logic where map representation is not involved
- world-item ownership and loot rules
- quicksave and quickload flow
- app screen flow

## What Must Stay Scene-Specific

These should stay behind interfaces, not be merged into one concrete runtime:
- ODM/DDM loading and terrain preparation
- BLV loading and portal/sector preparation
- outdoor terrain collision
- indoor sector, portal, and door collision
- outdoor atmosphere, sky, fog, and terrain extraction
- indoor portal visibility, mechanism geometry, and sector visibility
- outdoor camera behavior where it depends on terrain/world presentation
- indoor camera/debug visualization where it depends on indoor geometry
- scene-local render data production

## What Still Leaks Scene-Specific Logic Too High

These are the main remaining problem areas:
- `game/outdoor/OutdoorGameView.cpp`
  - still too large
  - still owns too much UI and input-routing detail
  - still acts as more than a renderer/view bridge
- `game/indoor/IndoorDebugRenderer.cpp`
  - still contains responsibilities that should move to a cleaner indoor
    renderer or view layer
- `game/app/GameApplication.cpp`
  - still knows too much about how each scene boots and binds its renderer
- `game/maps/SaveGame.cpp`
  - persists large runtime snapshots directly instead of a more deliberate
    long-term session model
- `game/events/EventRuntime.cpp`
  - interface seam is improved, but the shared-vs-scene split still needs a
    cleanup pass

## Remaining Work

### 1. Stabilize The Menu Renderer

Goal:
- make menu-first startup robust again without debug-text fallbacks

Why it matters:
- the app shell is now the real entry point
- if menu rendering is flaky, the whole refactor is harder to validate

Do:
- fix the actual texture/shader render path in `game/ui/MenuScreenBase.cpp`
- keep a visible failure mode for missing assets or shaders
- verify `MainMenu`, `LoadMenu`, and `NewGame` all render without depending on
  gameplay views

Acceptance:
- startup opens a usable textured main menu
- menu screens do not require any outdoor runtime/view to exist

### 2. Split `OutdoorGameView` Into View And Renderer Responsibilities

Goal:
- finish the outdoor side of the same cleanup we started with scene runtimes

Keep in the outdoor renderer/view:
- bgfx resources
- terrain, sky, fog, billboards, screen-space drawing
- outdoor camera control
- render-time caches
- input hit-testing that is purely view-related

Move out where possible:
- gameplay interaction routing
- shared overlay orchestration
- non-render save/runtime concerns
- any remaining state that belongs in `GameplayUiController`,
  `GameplayController`, or `OutdoorSceneRuntime`

Suggested target:
- `game/render/OutdoorRenderer.*`
- optional thin `OutdoorGameplayView` or keep `OutdoorGameView` as the thin
  bridge after shrinking it heavily

Acceptance:
- outdoor rendering still looks the same
- `OutdoorSceneRuntime` remains the runtime owner
- `OutdoorGameView` shrinks materially and stops acting like a gameplay god
  object

### 3. Finish Indoor Renderer Cleanup

Goal:
- make indoor match the same ownership model as outdoor

Do:
- keep runtime ownership in `IndoorSceneRuntime`
- strip remaining gameplay/runtime concerns from `IndoorDebugRenderer`
- either rename it to a real indoor renderer or introduce a separate indoor
  renderer file pair

Acceptance:
- indoor renderer does not own scene runtime state
- indoor and outdoor renderer layers follow the same architectural pattern

### 4. Tighten Session And Save Semantics

Goal:
- move from "runtime snapshot that works" to "session model that is deliberate"

Do:
- audit what should be persisted long-term vs what is just transient runtime
  cache
- reduce unnecessary renderer-derived or temporary state in saves
- make indoor and outdoor persistence symmetric where possible
- keep compatibility policy explicit

Likely end state:
- `GameSession` becomes the canonical persistence model
- scene runtime snapshots become narrower implementation details

Acceptance:
- quicksave and quickload remain stable
- save data clearly represents session state, not renderer state
- indoor and outdoor both round-trip through the same save/load flow

### 5. Move Shared Gameplay Input And Overlay Flow Higher

Goal:
- stop scene renderers from owning shared gameplay interaction behavior

Do:
- push more common input routing into `GameplayController`
- push more overlay lifecycle into `GameplayUiController`
- let scene runtimes answer scene-specific interaction queries
- let renderers only present and forward

Candidates:
- event dialog open/close flow
- non-scene-specific hotkeys
- inventory/book/sheet overlays
- shared status/report text

Acceptance:
- opening shared gameplay overlays does not require scene-specific branching in
  renderers unless layout/rendering truly differs

### 6. Unify Shared Gameplay Services

Goal:
- make indoor and outdoor use the same gameplay services where map
  representation is not the reason for divergence

Audit and unify:
- combat resolver
- projectile backend
- monster AI decision logic
- world item and loot logic
- shared interaction tracing rules where feasible
- event-triggered rewards and gating
- portrait reaction and speech dispatch

Do not force unification for:
- collision queries
- visibility/line-of-sight implementations that depend on scene structure
- geometry extraction

Acceptance:
- the majority of gameplay rules are shared code paths
- scene-specific code is mostly geometry/collision/render data code

### 7. Clean `GameApplication` Down To App Orchestration

Goal:
- leave `GameApplication` as the top-level app coordinator, not a second
  gameplay runtime

Keep:
- screen flow
- bootstrapping
- scene selection and high-level transitions
- renderer/runtime binding
- global audio integration

Move out or keep minimal:
- scene-specific restore logic
- ad hoc transition logic that belongs in controllers or runtimes
- knowledge of renderer internals

Acceptance:
- `GameApplication` talks in terms of session, current scene runtime, current
  screen, and renderer bindings
- most gameplay detail is elsewhere

## Recommended Execution Order

This is the cleanest remaining order:

1. menu renderer stabilization
2. `OutdoorGameView` split and shrink
3. indoor renderer cleanup to match the outdoor pattern
4. save/session tightening
5. shared gameplay input and overlay cleanup
6. shared gameplay services audit and unification
7. final `GameApplication` cleanup pass

## Definition Of "Only Needed Stuff Is Tied To Outdoor/Indoor"

Use this test during every remaining change:

If the code needs to know:
- terrain heightmap vs portal sectors
- outdoor sky/fog vs indoor mechanism geometry
- how to raycast or collide in that map type
- how to extract renderables from that map type

then scene-specific code is correct.

If the code only needs to know:
- which event fired
- what reward or dialogue should happen
- how party state changes
- whether an item, buff, spell, or service should apply
- how a save/load or overlay should behave

then the code should be shared.

## Final Expected Shape

At the end of the refactor, the rough layering should be:

- app:
  - `GameApplication`
  - `ScreenManager`
  - menu screens
- shared gameplay/session:
  - `GameSession`
  - `GameplayController`
  - `GameplayUiController`
  - shared gameplay services
- scene seam:
  - `IMapSceneRuntime`
- scene backends:
  - `OutdoorSceneRuntime`
  - `IndoorSceneRuntime`
- render/view:
  - outdoor renderer/view bridge
  - indoor renderer/view bridge

That keeps gameplay shared by default and keeps outdoor/indoor coupling only
where the map model genuinely requires it.
