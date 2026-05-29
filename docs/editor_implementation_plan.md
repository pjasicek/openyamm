# OpenYAMM Editor Implementation Plan

## Purpose

This document turns the production editor specification into an execution plan.

It defines:

- target and CMake changes
- concrete module/folder additions
- initial class list
- ownership boundaries
- MVP scope
- phased milestones
- acceptance criteria per milestone

This document is intended to be actionable by a builder session or engineering
team without another architectural planning round.

Primary input:

- [editor_production_spec.md](/home/pjasicek/github/OpenYAMM/docs/editor_production_spec.md)

Supporting inputs:

- [level_editor_authoring_inventory.md](/home/pjasicek/github/OpenYAMM/docs/level_editor_authoring_inventory.md)
- [game-engine-architecture.md](/home/pjasicek/github/OpenYAMM/docs/game-engine-architecture.md)
- [runtime_refactor_plan.md](/home/pjasicek/github/OpenYAMM/docs/runtime_refactor_plan.md)

## Executive Implementation Strategy

The editor should be built in three architectural layers:

1. editor shell
2. editor document/model layer
3. domain tools and panels

The correct MVP is not “everything at once”.
The correct MVP is:

- one real editor executable
- one real docked UI shell
- one real viewport
- one real editable outdoor scene path
- one real save/build cycle

Then expand into:

- indoor structure tools
- rich object inspectors
- Lua binding
- validation and playtest

## Fixed Technical Decisions

These are locked for implementation unless a severe blocker appears.

- executable:
  - `openyamm-editor`
- language:
  - C++20
- UI:
  - Dear ImGui docking
- window/input:
  - SDL3
- rendering:
  - bgfx
- runtime reuse:
  - `engine/` and `game/` stay the shared foundation
- authored scene format:
  - `.scene.yml`
- scripts:
  - `.lua`
- compiled cache:
  - `.scene.bin`

## Platform Constraint

The editor may be implemented and validated on Linux first, but it must be
engineered as a cross-platform application from the start.

Required rules:

- keep all platform-specific behavior behind explicit services
- do not bake Linux-only shell commands into core editor workflows
- keep path handling, file watching, file dialogs, process launch, clipboard,
  drag-and-drop, and modifier-key mapping abstracted
- avoid assuming case-sensitive paths in editor logic
- do not depend on X11/Wayland-specific APIs directly in editor modules
- prefer SDL3, bgfx, and existing engine abstraction layers for portability

Phase 1 may use simple in-editor file pickers or temporary Linux-friendly
fallbacks, but the call sites must remain replaceable with portable services.

## Current Build Context

Relevant current state:

- `openyamm_engine` already exists in [engine/CMakeLists.txt](/home/pjasicek/github/OpenYAMM/engine/CMakeLists.txt)
- `openyamm` already exists in [game/CMakeLists.txt](/home/pjasicek/github/OpenYAMM/game/CMakeLists.txt)
- `editor/CMakeLists.txt` is still only a placeholder in
  [editor/CMakeLists.txt](/home/pjasicek/github/OpenYAMM/editor/CMakeLists.txt)
- top-level build already has `OPENYAMM_BUILD_EDITOR` and `add_subdirectory(editor)`
  in [CMakeLists.txt](/home/pjasicek/github/OpenYAMM/CMakeLists.txt)

This means the correct next step is to replace the placeholder target, not to
invent a new build toggle or repo structure.

## Target And Library Plan

## 1. Build Targets

### 1.1 New Target

Create:

- `openyamm-editor`

in `editor/CMakeLists.txt`.

### 1.2 Initial Link Dependencies

`openyamm-editor` links to:

- `openyamm_engine`
- `yaml-cpp::yaml-cpp`
- SDL3 transitively through engine
- bgfx transitively through engine

Phase 1 should avoid linking the entire `openyamm` executable target.

### 1.3 Shared Game Code Reuse

The editor will need code from `game/`.
Do not solve this by linking against the `openyamm` executable target.

Instead, introduce reusable game-side libraries as needed.

Recommended split:

- keep `openyamm_engine` unchanged as the low-level base
- introduce one or more new reusable game-side libraries:
  - `openyamm_game_data`
  - `openyamm_game_maps`
  - `openyamm_game_scene`
  - `openyamm_game_editor_support`

Pragmatic first implementation:

- create `openyamm_game_editor_support`
- move only the code the editor immediately needs into that linkable unit
- defer wider library refactoring until needed

### 1.4 Phase 1 Minimal Link Scope

For the first editor milestone, the editor needs direct reuse of:

- map loading
- outdoor map data
- indoor map data
- scene runtime seams
- relevant tables
- spawn preview
- Lua/script binding helpers once scripting arrives

## Folder And Module Plan

## 2. New Folder Structure

Create the following under `editor/`:

- `editor/app/`
- `editor/document/`
- `editor/scene/`
- `editor/viewport/`
- `editor/tools/`
- `editor/panels/`
- `editor/build/`
- `editor/import/`
- `editor/undo/`
- `editor/widgets/`
- `editor/assets/`

`editor/assets/` is for editor-only shaders/icons if needed.

## 3. Initial File List

The first implementation wave should add these files.

### 3.1 App

- `editor/app/EditorApplication.h`
- `editor/app/EditorApplication.cpp`
- `editor/app/EditorMainWindow.h`
- `editor/app/EditorMainWindow.cpp`
- `editor/app/main.cpp`

### 3.2 Document

- `editor/document/EditorDocument.h`
- `editor/document/EditorDocument.cpp`
- `editor/document/EditorProject.h`
- `editor/document/EditorProject.cpp`
- `editor/document/DirtyState.h`

### 3.3 Scene

- `editor/scene/EditorScene.h`
- `editor/scene/EditorScene.cpp`
- `editor/scene/EditorNodeId.h`
- `editor/scene/EditorSelection.h`
- `editor/scene/EditorSelection.cpp`
- `editor/scene/EditorReferenceResolver.h`
- `editor/scene/EditorReferenceResolver.cpp`

### 3.4 Viewport

- `editor/viewport/EditorViewport.h`
- `editor/viewport/EditorViewport.cpp`
- `editor/viewport/EditorCameraController.h`
- `editor/viewport/EditorCameraController.cpp`
- `editor/viewport/EditorOverlayRenderer.h`
- `editor/viewport/EditorOverlayRenderer.cpp`
- `editor/viewport/EditorPicking.h`
- `editor/viewport/EditorPicking.cpp`
- `editor/viewport/GizmoRenderer.h`
- `editor/viewport/GizmoRenderer.cpp`

### 3.5 Panels

- `editor/panels/SceneOutlinerPanel.h`
- `editor/panels/SceneOutlinerPanel.cpp`
- `editor/panels/InspectorPanel.h`
- `editor/panels/InspectorPanel.cpp`
- `editor/panels/ToolPanel.h`
- `editor/panels/ToolPanel.cpp`
- `editor/panels/ValidationPanel.h`
- `editor/panels/ValidationPanel.cpp`
- `editor/panels/LogPanel.h`
- `editor/panels/LogPanel.cpp`
- `editor/panels/AssetBrowserPanel.h`
- `editor/panels/AssetBrowserPanel.cpp`

### 3.6 Tools

- `editor/tools/IEditorTool.h`
- `editor/tools/SelectionTool.h`
- `editor/tools/SelectionTool.cpp`
- `editor/tools/TerrainTool.h`
- `editor/tools/TerrainTool.cpp`
- `editor/tools/FacetTool.h`
- `editor/tools/FacetTool.cpp`
- `editor/tools/ModelTool.h`
- `editor/tools/ModelTool.cpp`

### 3.7 Build

- `editor/build/EditorBuildService.h`
- `editor/build/EditorBuildService.cpp`
- `editor/build/SceneCompiler.h`
- `editor/build/SceneCompiler.cpp`
- `editor/build/SceneValidation.h`
- `editor/build/SceneValidation.cpp`

### 3.8 Import

- `editor/import/GeometryImportService.h`
- `editor/import/GeometryImportService.cpp`
- `editor/import/AssetImportService.h`
- `editor/import/AssetImportService.cpp`

### 3.9 Undo

- `editor/undo/EditorCommand.h`
- `editor/undo/EditorCommandStack.h`
- `editor/undo/EditorCommandStack.cpp`

## Ownership Plan

## 4. Core Class Responsibilities

### 4.1 `EditorApplication`

Owns:

- editor process lifetime
- engine-style main loop
- SDL window event dispatch
- bgfx frame flow
- global dock layout bootstrap

Must not own:

- map authoring data itself
- selection state details
- tool logic

### 4.2 `EditorMainWindow`

Owns:

- Dear ImGui dockspace
- menu bar and toolbar
- panel creation and layout
- high-level command routing

Must not own:

- file parsing
- scene compilation
- domain editing logic

### 4.3 `EditorDocument`

Owns:

- one open map package
- source file paths
- scene data
- dirty flags
- last build result

Must be the source of truth for authoring state in the editor.

### 4.4 `EditorScene`

Owns:

- normalized authoring graph
- stable node ids
- typed access to authoring objects

Must present a scene-neutral editing model even though indoor and outdoor
geometry differ.

### 4.5 `EditorBuildService`

Owns:

- validation orchestration
- derived data rebuild
- compile to runtime cache
- temporary build for playtest

Must not own:

- panel UI
- map editing state

### 4.6 `EditorViewport`

Owns:

- rendering integration for the main viewport
- camera
- picking orchestration
- overlay composition

Must not own:

- panel layout
- authoring data persistence

### 4.7 `IEditorTool`

Each tool owns:

- click behavior
- drag behavior
- active overlay needs
- active inspector extension
- hotkeys specific to that tool

Tool implementations must not bypass the command stack for user-visible edits.

## Data Model Plan

## 5. Editor Document Composition

`EditorDocument` should contain at least:

- `SceneKind`
- map base name
- source geometry path
- YAML source path
- Lua path list
- loaded `EditorScene`
- optional compiled cache metadata
- dirty flags
- validation issues

### 5.1 Preferred Sub-Objects

Recommended members:

- `EditorScene m_scene`
- `EditorSelection m_selection`
- `DirtyState m_dirtyState`
- `ValidationResult m_validation`
- `BuildState m_buildState`

## 6. Normalized Authoring Types

Add typed editor-facing structs for:

- `EditorTerrain`
- `EditorModelInstance`
- `EditorRoom`
- `EditorFacet`
- `EditorPortal`
- `EditorDoor`
- `EditorMechanism`
- `EditorDecoration`
- `EditorLight`
- `EditorSpawn`
- `EditorMonster`
- `EditorRuntimeObject`
- `EditorChest`
- `EditorTransition`
- `EditorZone`
- `EditorScriptBinding`

These should be editor-side normalization structs, not direct aliases of
runtime structs.

### 6.1 Runtime Bridging Rule

Do not directly mutate runtime scene structs from the UI.

Instead:

1. mutate editor document/model
2. rebuild runtime preview state from document

This avoids editor state becoming an accidental shadow runtime.

## 7. Stable ID Strategy

Implement stable ids immediately.

Required:

- deterministic serialization
- preserved across reorderings
- used in scene YAML and script bindings

Add:

- `EditorNodeId`
- `StableIdGenerator`
- `NameRegistry`

## UI Framework Plan

## 8. Dear ImGui Adoption

The editor should use Dear ImGui docking immediately.

Implementation tasks:

- vendor or integrate Dear ImGui
- add SDL3 backend glue
- add bgfx renderer backend glue
- create one editor UI service that owns ImGui frame begin/end

### 8.1 Why This Is Required

Without this, the team will waste time on windowing/UI infrastructure instead of
authoring tools.

## 9. Docking Layout State

Create:

- `EditorDockLayoutService`

Responsibilities:

- default dock layout
- layout reset
- save/load user layouts

## Tooling Order

## 10. MVP Cut

The MVP is not “all tool types”.
The MVP is a usable outdoor map editor.

### 10.1 MVP Features

- editor executable boots
- docked UI works
- viewport renders outdoor scene
- outliner works
- inspector works for selected object
- selection/move/rotate/scale works
- terrain sculpt works
- terrain paint works
- outdoor model placement works
- decoration placement works
- light placement works
- spawn placement works
- environment editing works
- save `.scene.yml`
- validate basic references
- compile derived cache

### 10.2 MVP Explicitly Deferred

- indoor room/portal/door workflow
- chest loot rule editor
- monster full inspector
- Lua editor integration
- playtest
- generic mechanism graph

Those come after the shell and outdoor path are proven.

## 11. Milestone Plan

### Milestone 0: Build And Shell

Goal:

- create a real `openyamm-editor` app target and docked editor shell

Tasks:

- replace `editor/CMakeLists.txt` placeholder
- add Dear ImGui integration
- add `EditorApplication`
- add `EditorMainWindow`
- add empty dock panels
- boot bgfx viewport panel

Acceptance:

- `openyamm-editor` launches
- dock layout appears
- empty viewport renders
- menu/toolbar are interactive

### Milestone 1: Document And Scene Core

Goal:

- real level document with load/save and selection

Tasks:

- implement `EditorDocument`
- implement `EditorScene`
- implement stable ids
- implement outliner
- implement inspector shell
- implement selection state
- implement command stack

Acceptance:

- open a map package
- selection is visible in outliner and inspector
- save/load round-trips document

### Milestone 2: Outdoor MVP

Goal:

- outdoor map editing loop works end to end

Tasks:

- outdoor runtime preview bridge
- terrain tool
- model placement tool
- facet inspector basics
- decoration tool
- light tool
- spawn tool
- environment panel
- build service basics

Acceptance:

- edit outdoor map
- save YAML
- rebuild derived data
- reopen and see same results

### Milestone 3: Validation And Asset Flow

Goal:

- content-authoring quality bar becomes usable for a team

Tasks:

- validation framework
- asset browser
- geometry import service
- missing asset resolver
- build log/validation panel

Acceptance:

- invalid content produces focused actionable issues
- asset placement via browser works
- geometry import can create/update content

### Milestone 4: Indoor Structure

Goal:

- indoor authoring becomes viable

Tasks:

- room/portal tool
- room inspector
- portal editing
- indoor viewport overlays
- indoor facet tool
- derived rebuild for BSP/outlines

Acceptance:

- indoor map can be imported and structurally edited
- rooms and portals validate and render correctly

### Milestone 5: Doors, Chests, Monsters

Goal:

- original-style authored interactive content is covered

Tasks:

- door/mechanism tool
- monster tool
- chest editor
- runtime-object tool
- richer inspectors

Acceptance:

- door authoring works
- monster full property editing works
- chest rule-based content authoring works

### Milestone 6: Lua And References

Goal:

- authored scripts are properly integrated

Tasks:

- Lua browser/editor
- scene-to-Lua reference browsing
- script binding panel
- reverse-reference search

Acceptance:

- select object and jump to script
- select script binding and focus object
- missing references are validated

### Milestone 7: Playtest And Successor Extensions

Goal:

- editor becomes a full workflow hub

Tasks:

- play from start/camera
- temporary build for unsaved changes
- mechanism link overlays
- zones
- successor environment/material tools

Acceptance:

- edit, build, playtest in one loop

## Class-Level Deliverables By Milestone

## 12. Milestone 0 Class List

Required:

- `EditorApplication`
- `EditorMainWindow`
- `EditorDockLayoutService`
- `EditorImGuiService`

## 13. Milestone 1 Class List

Required:

- `EditorDocument`
- `EditorScene`
- `EditorSelection`
- `EditorCommandStack`
- `SceneOutlinerPanel`
- `InspectorPanel`

## 14. Milestone 2 Class List

Required:

- `EditorViewport`
- `EditorCameraController`
- `EditorOverlayRenderer`
- `EditorPicking`
- `SelectionTool`
- `TerrainTool`
- `ModelTool`
- `FacetTool`
- `DecorationTool`
- `LightTool`
- `SpawnTool`
- `EnvironmentTool`
- `EditorBuildService`

## 15. Milestone 3 Class List

Required:

- `SceneValidation`
- `ValidationPanel`
- `AssetBrowserPanel`
- `GeometryImportService`
- `AssetImportService`
- `MissingAssetResolverDialog`

## 16. Milestone 4 Class List

Required:

- `RoomPortalTool`
- `IndoorStructurePanel`
- `IndoorSceneBridge`

## 17. Milestone 5 Class List

Required:

- `DoorMechanismTool`
- `MonsterTool`
- `ChestTool`
- `RuntimeObjectTool`
- `ChestContentEditorDialog`
- `MonsterPresetDialog`

## 18. Milestone 6 Class List

Required:

- `LuaScriptPanel`
- `ScriptBindingPanel`
- `LuaReferenceResolver`

## 19. Milestone 7 Class List

Required:

- `PlaytestService`
- `ZoneTool`
- `MechanismGraphPanel`

## Serialization And Build Plan

## 20. YAML Serialization Ownership

Create editor-side serializers:

- `EditorSceneYamlSerializer`
- `EditorSceneYamlDeserializer`

Do not make UI code write YAML directly.

### 20.1 Determinism Rules

- stable key ordering
- stable array ordering where semantically possible
- no transient/editor-cache fields in source YAML
- explicit format version

## 21. Compiled Cache Ownership

Create:

- `SceneCompiler`
- `SceneCacheWriter`

Responsibilities:

- convert normalized document into runtime-oriented scene cache
- rebuild derived structures

## 22. Validation Ownership

Validation should be layered:

- source validation
- reference validation
- geometry validation
- build validation
- script binding validation

Implementation split:

- `SceneValidation`
- validators by domain:
  - `GeometryValidator`
  - `ReferenceValidator`
  - `SpawnValidator`
  - `ChestValidator`
  - `ScriptValidator`

## Playtest Plan

## 23. Playtest Service

Create:

- `PlaytestService`

Responsibilities:

- temporary build if needed
- spawn runtime session
- hand off current map and start mode
- stop and restore editor state

### 23.1 Start Modes

- from map start
- from current camera
- from selected transition marker if applicable

## UI Implementation Plan

## 24. Panel Implementation Order

Implement panels in this order:

1. viewport
2. outliner
3. inspector
4. tool panel
5. validation
6. asset browser
7. Lua browser

Reason:

- viewport/outliner/inspector are the minimum usable authoring triangle

## 25. Inspector Implementation Order

Add inspectors in this order:

1. environment
2. terrain
3. decorations
4. lights
5. spawns
6. facets
7. rooms
8. monsters
9. chests
10. doors/mechanisms
11. transitions
12. script bindings

## 26. Tool Implementation Order

Add tools in this order:

1. selection
2. transform
3. terrain
4. model placement
5. decoration
6. light
7. spawn
8. facet
9. room/portal
10. door/mechanism
11. monster
12. chest
13. transition
14. script binding

## Risk Plan

## 27. Major Risks

### 27.1 Over-Coupling To Runtime Internals

Risk:

- editor becomes fragile because it mutates runtime structs directly

Mitigation:

- normalized editor document layer
- one-way rebuild to runtime preview

### 27.2 Trying To Solve Indoor And Outdoor Simultaneously

Risk:

- MVP stalls

Mitigation:

- outdoor-first MVP
- indoor structure as a later milestone

### 27.3 UI Scope Explosion

Risk:

- generic editor chrome grows faster than useful authoring tools

Mitigation:

- implement domain tools first
- delay secondary polish panels

### 27.4 Script Integration Too Late

Risk:

- scene IDs and binding model become incompatible with Lua needs

Mitigation:

- stable ids implemented in milestone 1
- script binding placeholder model present before Lua panel

## Acceptance Criteria

## 28. Milestone Acceptance Summary

The project can move to the next milestone only if the previous one meets its
acceptance criteria with no manual file editing required for the tested flow.

### Required quality bar for every milestone

- builds cleanly
- does not corrupt authored files
- undo/redo works for introduced edits
- errors are surfaced in UI/log, not silently swallowed

## Immediate Next Tasks

## 29. First Builder Task List

The first builder session should do exactly this:

1. replace `editor/CMakeLists.txt` placeholder with a real target
2. integrate Dear ImGui docking for editor UI
3. add `EditorApplication`, `EditorMainWindow`, and `main.cpp`
4. create empty docked panels:
   - viewport
   - outliner
   - inspector
   - log
5. get one bgfx-backed viewport rendering inside the editor window
6. load one outdoor map in read-only mode through reused runtime code

That is the correct first proof point.

## One-Sentence Summary

Build the OpenYAMM editor as an outdoor-first, docked C++ authoring
application with a normalized document layer, runtime-backed viewport, explicit
domain tools, and milestone-gated expansion into indoor structure, rich content
authoring, Lua, and playtest.
