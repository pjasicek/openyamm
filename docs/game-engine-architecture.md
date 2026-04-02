# Game And Engine Architecture

This is a living architecture document.

It describes the current intended structure of OpenYAMM after the recent runtime
and `game/` source reorganization. It is not a claim that every subsystem is
finished. Some areas, especially indoor runtime and renderer cleanup, are still
expected to change.

Use this document to answer:

- where new code should go
- which subsystem should own a responsibility
- which dependencies are acceptable
- which parts of the architecture are stable vs still in motion

## Top-Level Layers

OpenYAMM is organized into four top-level code layers:

- `engine/`
  - reusable runtime infrastructure
  - rendering backend integration
  - asset filesystem and low-level support systems
- `game/`
  - game-specific runtime, content loading, UI, scenes, and gameplay logic
- `editor/`
  - authoring and inspection tools
  - should reuse runtime systems instead of reimplementing game rules
- `tools/`
  - conversion, extraction, diagnostics, and standalone helper tools

The practical rule is:

- `engine/` should not depend on `game/`
- `game/` may depend on `engine/`
- `editor/` may depend on both `engine/` and `game/`
- `tools/` may depend on whatever they need, but should not distort runtime
  architecture

## Current `game/` Subsystems

The `game/` layer now uses one level of subsystem folders.

### `game/app`

Owns application-level flow:

- app mode selection
- startup and shutdown orchestration
- session bootstrapping
- screen routing

Main files:

- [`game/app/GameApplication.cpp`](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)
- [`game/app/GameSession.cpp`](/home/pjasicek/github/OpenYAMM/game/app/GameSession.cpp)
- [`game/app/ScreenManager.cpp`](/home/pjasicek/github/OpenYAMM/game/app/ScreenManager.cpp)

### `game/audio`

Owns game-facing audio and video playback integration:

- gameplay audio system
- sound catalog / sound ids
- house video playback support

Main files:

- [`game/audio/GameAudioSystem.cpp`](/home/pjasicek/github/OpenYAMM/game/audio/GameAudioSystem.cpp)
- [`game/audio/SoundCatalog.cpp`](/home/pjasicek/github/OpenYAMM/game/audio/SoundCatalog.cpp)
- [`game/audio/HouseVideoPlayer.cpp`](/home/pjasicek/github/OpenYAMM/game/audio/HouseVideoPlayer.cpp)

### `game/data`

Owns broad data-loading and content-resolution glue that does not fit a single
table or map loader:

- actor naming helpers
- gameplay data loading bootstrap

Main files:

- [`game/data/GameDataLoader.cpp`](/home/pjasicek/github/OpenYAMM/game/data/GameDataLoader.cpp)
- [`game/data/ActorNameResolver.cpp`](/home/pjasicek/github/OpenYAMM/game/data/ActorNameResolver.cpp)

### `game/events`

Owns event parsing, IR, and execution runtime:

- EVT program parsing
- intermediate representation
- event execution state
- scene event context seam
- event dialog content production

Main files:

- [`game/events/EvtProgram.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.cpp)
- [`game/events/EventIr.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)
- [`game/events/EventRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- [`game/events/EventDialogContent.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventDialogContent.cpp)

### `game/gameplay`

Owns shared gameplay rules and controllers that are not inherently outdoor or
indoor:

- gameplay orchestration
- dialogue controllers
- shared overlay input controllers
- house interaction and house services
- shared mechanics

Main files:

- [`game/gameplay/GameplayController.cpp`](/home/pjasicek/github/OpenYAMM/game/gameplay/GameplayController.cpp)
- [`game/gameplay/GameplayDialogController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/gameplay/GameplayDialogController.cpp)
- [`game/gameplay/GameMechanics.cpp`](/home/pjasicek/github/OpenYAMM/game/gameplay/GameMechanics.cpp)
- [`game/gameplay/HouseInteraction.cpp`](/home/pjasicek/github/OpenYAMM/game/gameplay/HouseInteraction.cpp)

### `game/indoor`

Owns indoor scene-specific code.

Current state:

- this area is not yet as clean as outdoor
- the main file is still the debug-oriented indoor renderer
- expect this folder to change during the indoor refactor

Main files:

- [`game/indoor/IndoorDebugRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorDebugRenderer.cpp)
- [`game/indoor/IndoorMapData.cpp`](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorMapData.cpp)

### `game/items`

Owns item runtime behavior:

- item use
- enchantment runtime
- item generation
- item runtime helpers
- equip position logic
- price calculation

Main files:

- [`game/items/InventoryItemUseRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/items/InventoryItemUseRuntime.cpp)
- [`game/items/ItemRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/items/ItemRuntime.cpp)
- [`game/items/ItemGenerator.cpp`](/home/pjasicek/github/OpenYAMM/game/items/ItemGenerator.cpp)

### `game/maps`

Owns map and save/session data transport:

- map asset loading
- map delta data
- map registry
- savegame persistence

Main files:

- [`game/maps/MapAssetLoader.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.cpp)
- [`game/maps/MapDeltaData.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.cpp)
- [`game/maps/MapRegistry.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/MapRegistry.cpp)
- [`game/maps/SaveGame.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/SaveGame.cpp)

### `game/outdoor`

Owns outdoor scene-specific code.

This is currently the cleanest scene area in the codebase after the refactor.

Responsibilities:

- outdoor view orchestration
- outdoor renderer and billboard renderer
- outdoor-specific interaction and input
- outdoor movement
- outdoor party/world runtime
- outdoor geometry helpers and map data

Main files:

- [`game/outdoor/OutdoorGameView.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)
- [`game/outdoor/OutdoorRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorRenderer.cpp)
- [`game/outdoor/OutdoorInteractionController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorInteractionController.cpp)
- [`game/outdoor/OutdoorGameplayInputController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)
- [`game/outdoor/OutdoorWorldRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorWorldRuntime.cpp)

### `game/party`

Owns party- and character-facing shared rules and data:

- party runtime state
- party spell system
- spell school and spell ids
- skill data
- speech ids

Main files:

- [`game/party/Party.cpp`](/home/pjasicek/github/OpenYAMM/game/party/Party.cpp)
- [`game/party/PartySpellSystem.cpp`](/home/pjasicek/github/OpenYAMM/game/party/PartySpellSystem.cpp)
- [`game/party/SpellSchool.cpp`](/home/pjasicek/github/OpenYAMM/game/party/SpellSchool.cpp)

### `game/scene`

Owns scene runtime seams and scene backend implementations:

- indoor scene runtime
- outdoor scene runtime
- common scene interfaces

Main files:

- [`game/scene/OutdoorSceneRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/scene/OutdoorSceneRuntime.cpp)
- [`game/scene/IndoorSceneRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/scene/IndoorSceneRuntime.cpp)

### `game/tables`

Owns pure loaded-data tables.

These files should remain mostly data-oriented and not grow scene/runtime logic.

Examples:

- item, monster, object, map, and NPC tables
- portrait, face animation, doll, icon, and speech tables
- spell and scroll tables

### `game/ui`

Owns shared UI rendering, UI state, and screens:

- gameplay HUD and overlay renderers
- shared HUD services
- gameplay UI controller
- menu screens
- screen interfaces

Main files:

- [`game/ui/GameplayUiController.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/GameplayUiController.cpp)
- [`game/ui/GameplayHudRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/GameplayHudRenderer.cpp)
- [`game/ui/GameplayDialogueRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/GameplayDialogueRenderer.cpp)
- [`game/ui/GameplayPartyOverlayRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/GameplayPartyOverlayRenderer.cpp)
- [`game/ui/screens/MainMenuScreen.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/screens/MainMenuScreen.cpp)

## Current Runtime Ownership Model

The intended ownership model is:

- `app` owns application flow
- `maps` and `data` load content
- `scene` owns scene runtime backends
- `gameplay` owns shared gameplay rules/controllers
- `ui` owns shared UI state and rendering helpers
- `outdoor` and later `indoor` own scene-specific rendering, geometry, and
  interaction

The practical test is:

- if a system answers "what gameplay should happen?" it should lean toward
  `gameplay`, `party`, `items`, `events`, or `ui`
- if a system answers "how does this scene represent space, visibility,
  rendering, or scene-local interaction?" it should lean toward `outdoor` or
  `indoor`

## Main Runtime Flows

### Startup And Session Flow

Current flow:

1. `GameApplication` boots the engine shell.
2. `GameDataLoader` loads gameplay content.
3. `GameApplication` builds the current session/runtime.
4. The active screen or active scene renderer is initialized.

Main entry point:

- [`game/app/GameApplication.cpp`](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)

### Map Load Flow

Current outdoor-oriented flow:

1. `MapAssetLoader` loads map assets and parsed data.
2. `GameApplication` builds outdoor party/world runtime.
3. `OutdoorSceneRuntime` is created.
4. `OutdoorGameView` initializes renderer-side resources.

Main files:

- [`game/maps/MapAssetLoader.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.cpp)
- [`game/app/GameApplication.cpp`](/home/pjasicek/github/OpenYAMM/game/app/GameApplication.cpp)
- [`game/scene/OutdoorSceneRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/scene/OutdoorSceneRuntime.cpp)
- [`game/outdoor/OutdoorGameView.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)

### Event Execution Flow

Current flow:

1. scene-specific interaction resolves an activation target
2. interaction/controller code produces an event id
3. scene runtime executes local or global event IR
4. `EventRuntime` updates state and produces messages/dialogue context
5. gameplay/dialogue/UI layers present results

Main files:

- [`game/outdoor/OutdoorInteractionController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorInteractionController.cpp)
- [`game/scene/OutdoorSceneRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/scene/OutdoorSceneRuntime.cpp)
- [`game/events/EventRuntime.cpp`](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- [`game/gameplay/GameplayDialogController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/gameplay/GameplayDialogController.cpp)

### Input / UI / Render Flow

Current outdoor flow:

1. `OutdoorGameplayInputController` handles outdoor gameplay input orchestration
2. shared overlay input is delegated to shared gameplay/UI controllers
3. `OutdoorGameView` orchestrates render passes
4. renderer/UI helpers render world and gameplay overlays

Main files:

- [`game/outdoor/OutdoorGameplayInputController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameplayInputController.cpp)
- [`game/gameplay/GameplayOverlayInputController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/gameplay/GameplayOverlayInputController.cpp)
- [`game/gameplay/GameplayPartyOverlayInputController.cpp`](
  /home/pjasicek/github/OpenYAMM/game/gameplay/GameplayPartyOverlayInputController.cpp)
- [`game/outdoor/OutdoorRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorRenderer.cpp)
- [`game/ui/GameplayHudRenderer.cpp`](/home/pjasicek/github/OpenYAMM/game/ui/GameplayHudRenderer.cpp)

## Dependency Rules

These are the intended dependency rules for new code.

### Allowed By Default

- `app -> maps, data, scene, ui, gameplay, audio`
- `scene -> events, gameplay, party, items, tables`
- `ui -> gameplay, party, items, tables`
- `outdoor -> scene, gameplay, ui, party, items, events, tables`
- `indoor -> scene, gameplay, ui, party, items, events, tables`
- `gameplay -> party, items, events, tables`
- `maps -> tables, party, events`

### Avoid By Default

- `tables` depending on scene runtime or render code
- `events` depending directly on outdoor or indoor concrete runtime types
- `ui` owning campaign or save/session state
- `outdoor` or `indoor` becoming god-objects that absorb shared gameplay rules
- `GameApplication` directly owning scene-specific gameplay behavior

## Stable Areas vs Moving Areas

### Stable Enough To Treat As Real Structure

- the `game/` subsystem folder split
- outdoor renderer/view/controller separation
- shared gameplay overlay controllers and renderers
- `scene` as the seam between app flow and scene-specific runtime
- `tables` as data-only subsystem

### Still Expected To Change

- indoor renderer and indoor gameplay input shape
- some remaining save/session semantics
- exact shared-vs-scene split around event/runtime details
- utility placement for a few remaining root-level files such as:
  - `BinaryReader.h`
  - `StringUtils.h`
  - `SpriteObjectDefs.h`
  - `SpawnPreview.*`

## How To Place New Code

Use these rules when adding new files:

- pure data table loader or lookup:
  - `game/tables`
- scene-neutral gameplay rules or controllers:
  - `game/gameplay`
- party or spell-specific shared logic:
  - `game/party`
- item runtime behavior:
  - `game/items`
- map/save/loading logic:
  - `game/maps`
- event parser / IR / execution:
  - `game/events`
- outdoor-only renderer, movement, hit testing, or interaction:
  - `game/outdoor`
- indoor-only renderer, movement, hit testing, or interaction:
  - `game/indoor`
- shared gameplay UI or menu screens:
  - `game/ui`
- app flow / boot / mode switching:
  - `game/app`

If a new file seems to belong equally in two places, the better question is:

- is it deciding gameplay semantics
- or is it representing a specific scene/runtime/view

That answer should usually pick the folder.

## Recommended Next Documentation Updates

This document should be updated when any of these happen:

- indoor gets the same cleanup outdoor already received
- save/session model changes materially
- a new shared runtime seam is introduced
- remaining root-level utility files are given proper subsystem homes

Related documents:

- [runtime_refactor_plan.md](/home/pjasicek/github/OpenYAMM/docs/runtime_refactor_plan.md)
- [implementation-assumptions.md](/home/pjasicek/github/OpenYAMM/docs/implementation-assumptions.md)
