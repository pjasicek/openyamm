# OpenYAMM Editor Production Specification

## Purpose

This document defines the target production-grade specification for the
OpenYAMM editor.

It is intended to be specific enough that implementation can begin without
having to rediscover:

- editor architecture
- application layout
- scene/document model
- tool modes
- panels and popups
- asset pipelines
- build/compile flow
- validation rules
- playtest flow

This document is based on:

- [level_editor_authoring_inventory.md](/home/pjasicek/github/OpenYAMM/docs/level_editor_authoring_inventory.md)
- [game-engine-architecture.md](/home/pjasicek/github/OpenYAMM/docs/game-engine-architecture.md)
- [runtime_refactor_plan.md](/home/pjasicek/github/OpenYAMM/docs/runtime_refactor_plan.md)
- the current `engine/`, `game/`, `editor/`, `tools/` structure

It assumes the following content direction:

- base geometry remains `BLV`-like for indoor and `ODM`-like for outdoor
- authored scene supplements are stored in `.scene.yml`
- compiled runtime scene caches exist alongside YAML
- Lua replaces legacy `EVT` as the authored script format
- the editor is a separate executable in the same repository and reuses runtime
  systems from `engine/` and `game/`

## Goals

The editor must allow a team to author an entire Might-and-Magic-style map
package, not only a mesh.

This includes:

- level geometry assembly
- terrain authoring
- rooms and portals
- facets and interactions
- mechanisms and doors
- sprites and decorations
- lights
- spawns and encounters
- monsters
- runtime objects
- chests and loot definitions
- environment and map-header settings
- transitions and mapstats metadata
- script bindings and Lua editing
- validation and playtest

## Non-Goals

The editor is not intended to be:

- a generic node-graph sandbox
- a cinematic sequencer-first tool
- a physically based material authoring suite
- a general-purpose 3D DCC replacement
- a multiplayer/network gameplay editor

External DCC tools remain responsible for heavy geometry authoring.

## Primary Product Decisions

These decisions are fixed for the first production editor.

### App Shape

- one repository
- shared runtime code
- separate executable target:
  - `openyamm`
  - `openyamm-editor`

### Language And Runtime

- C++20
- SDL3 window/input integration through existing engine app shell patterns
- bgfx for viewport rendering
- Dear ImGui docking UI for editor chrome and tools

### Platform Direction

- the editor must remain a cross-platform product target
- Linux-first implementation is acceptable
- no implementation choice may block later Windows or macOS support
- platform-specific behavior must be isolated behind small services or adapters
- file paths, file dialogs, clipboard access, process launch, windowing details,
  drag-and-drop, and modifier-key behavior must not be hard-coded as Linux-only
- editor document formats, build/cache outputs, and project metadata must remain
  platform-neutral

Rationale:

- C++ matches the runtime
- bgfx and SDL3 are already used
- Dear ImGui is the fastest path to a production-grade docking tool UI
- custom retained-mode editor UI should not be built first
- SDL3 and bgfx keep the shell portable if platform edges are kept contained

### Data Ownership

- geometry source:
  - `BLV` / `ODM` runtime geometry containers
- authored semantics:
  - `.scene.yml`
- scripts:
  - `.lua`
- compiled cache:
  - `.scene.bin` or equivalent scene cache asset

### Authoritative Model

The editor authoritative source model is:

- geometry container
- scene YAML
- Lua scripts
- sidecar tables or project metadata

Compiled runtime/cache data is derived.

### Runtime Reuse

The editor must reuse:

- map loaders where possible
- scene runtime structures where possible
- renderers and debug draw subsystems where possible
- gameplay-side data tables and resolvers
- collision and hit-testing logic where practical

The editor must not fork gameplay logic into a second incompatible
implementation.

## Success Criteria

The editor is considered production-ready when all of these are true:

- a new indoor level can be created, saved, compiled, loaded, and played
- a new outdoor level can be created, saved, compiled, loaded, and played
- all original-style authored systems from the inventory can be represented
- the editor can rebuild derived data deterministically
- playtest uses the same scene/runtime systems as the game
- YAML and Lua are first-class authoring formats
- validation catches broken references, missing assets, invalid geometry links,
  bad script bindings, and impossible content definitions

## Top-Level Architecture

## 1. Targets And Modules

### 1.1 Editor Target

Add a real editor executable in `editor/`:

- target name:
  - `openyamm-editor`

### 1.2 Proposed Module Split

Under `editor/`:

- `editor/app/`
  - editor application bootstrap
  - dock layout state
  - global command dispatch
- `editor/document/`
  - editor document
  - dirty tracking
  - save/build orchestration
  - stable ids/reference resolution
- `editor/scene/`
  - editor scene graph wrappers
  - selection and outliner nodes
  - editor-only metadata
- `editor/viewport/`
  - viewport rendering orchestration
  - camera controller
  - gizmos
  - overlays
  - picking bridge
- `editor/tools/`
  - terrain tool
  - facet tool
  - room/portal tool
  - door/mechanism tool
  - sprite tool
  - light tool
  - spawn tool
  - monster tool
  - chest tool
  - environment tool
- `editor/panels/`
  - outliner
  - inspector
  - asset browser
  - validation
  - console/log
  - Lua browser/editor
  - mapstats panel
- `editor/build/`
  - compile scene
  - rebuild derived structures
  - emit caches
- `editor/import/`
  - geometry import
  - asset import
  - missing asset resolution
- `editor/undo/`
  - command stack
  - transaction grouping

### 1.3 Dependency Rules

- `editor/` depends on `engine/` and `game/`
- `game/` must not depend on `editor/`
- reusable compile/build logic may later move from `editor/` to `tools/` or
  `game/` if it becomes runtime-independent

## 2. Core Runtime Objects

The editor must have these core objects.

### 2.1 `EditorApplication`

Owns:

- window
- bgfx context
- UI main loop
- global services
- project/session open state

### 2.2 `EditorSession`

Owns:

- open project
- recent files
- loaded data tables
- loaded assets
- current document
- playtest state

### 2.3 `EditorDocument`

Owns one open level package.

Contains:

- map identity
- indoor/outdoor kind
- geometry source bindings
- scene YAML model
- script references
- mapstats linkage
- dirty flags by subsystem
- derived-cache status

### 2.4 `EditorScene`

Normalized authoring graph used by panels/tools.

Contains typed nodes for:

- terrain
- models
- rooms
- facets
- portals
- mechanisms
- decorations
- lights
- spawns
- monsters
- runtime objects
- chests
- transitions
- zones
- script bindings

### 2.5 `EditorSelection`

Owns:

- active selection set
- primary selection
- hover target
- selection filter
- pivot mode
- transform mode

### 2.6 `EditorCommandStack`

Owns:

- undo/redo history
- grouped transactions
- mergeable drags
- save checkpoints

### 2.7 `EditorBuildService`

Owns:

- scene validation
- derived-data rebuild
- runtime cache emission
- package sync
- playtest handoff

## Project And File Model

## 3. Project Structure

The editor works on a project rooted in the OpenYAMM repo or a content project
folder.

Minimum project structure:

- `assets_dev/`
- `data/` or extracted source assets
- `docs/`
- `tools/`

For authored maps:

- indoor:
  - `D05.blv`
  - `D05.scene.yml`
  - `D05.lua`
  - `D05.scene.bin`
- outdoor:
  - `Out02.odm`
  - `Out02.scene.yml`
  - `Out02.lua`
  - `Out02.scene.bin`

### 3.1 Optional Sidecars

Depending on maturity, the editor may split scene data into multiple sidecars:

- `Out02.materials.yml`
- `Out02.environment.yml`
- `Out02.encounters.yml`
- `D05.mechanisms.yml`

But version 1 should support one primary `.scene.yml` per map package and be
able to expand later.

## 4. Stable IDs And References

Every editor-authored object that can be referenced externally must have a
stable id.

Objects requiring stable ids:

- mechanisms
- transitions
- chests
- monsters
- decorations with script bindings
- named facets
- rooms
- portals
- spawns
- zones
- lights if referenced

Reference forms:

- stable uuid-like internal id
- human-readable optional name
- optional legacy numeric id where required by compatibility

Scripts must bind to stable ids or named aliases, not transient array indexes.

## 5. Document Dirty Tracking

Dirty state must be tracked at subsystem granularity:

- geometry source dirty
- scene YAML dirty
- Lua dirty
- mapstats dirty
- derived cache stale
- validation stale

The UI must show:

- unsaved changes
- unbuilt changes
- validation state

## Main Window And Layout

## 6. Window Layout

The default editor layout is fixed and should ship with a sensible docking
preset.

### 6.1 Default Layout

- top:
  - main menu bar
  - main toolbar
- left column:
  - scene outliner
  - asset browser tab
- center:
  - main 3D viewport
- right column:
  - inspector
  - context-specific tool panel
- bottom:
  - validation/errors
  - log/console
  - Lua/script browser
  - build output

### 6.2 Layout Presets

Ship with these presets:

- `Default`
- `Terrain`
- `Indoor Structure`
- `Scripting`
- `Validation`

Users may save custom layouts.

### 6.3 Top Menu Bar

Required menus:

- `File`
- `Edit`
- `View`
- `Select`
- `Create`
- `Tools`
- `Build`
- `Playtest`
- `Window`
- `Help`

### 6.4 Main Toolbar

Toolbar sections:

- file:
  - new map
  - open
  - save
  - save all
- history:
  - undo
  - redo
- build:
  - validate
  - rebuild derived
  - compile scene
- playtest:
  - play from start
  - play from camera
  - stop playtest
- transform:
  - select
  - move
  - rotate
  - scale
- space:
  - local/world
  - pivot center/individual
- snapping:
  - toggle snap
  - position step
  - rotation step
  - scale step
- overlays:
  - grid
  - ids
  - bounds
  - collision
  - scripts
  - lighting
  - spawn/encounter

## 7. Scene Outliner

The outliner is the primary hierarchical navigation tool.

### 7.1 Outliner Root

Top-level sections:

- `Map`
- `Geometry`
- `Environment`
- `Terrain` or `Rooms`
- `Facets`
- `Mechanisms`
- `Decorations`
- `Lights`
- `Spawns`
- `Monsters`
- `Objects`
- `Chests`
- `Transitions`
- `Zones`
- `Scripts`
- `Validation`

Indoor-specific sections:

- `Rooms`
- `Portals`
- `Doors`

Outdoor-specific sections:

- `Terrain`
- `Models`

### 7.2 Outliner Behavior

Must support:

- search by name/id/type
- filter by category
- visibility toggle
- lock toggle
- isolate selection
- multi-select
- drag-drop reparent where semantically valid
- context menu on every node type

### 7.3 Outliner Badges

Each row may show badges for:

- hidden
- locked
- script-bound
- invalid
- missing asset
- stale build

## 8. Inspector

The inspector is always context-sensitive and shows the primary selection.

### 8.1 Inspector Sections

Each object inspector starts with:

- object type
- stable id
- display name
- enabled/disabled
- visibility/lock
- comments/notes

Then object-specific groups follow.

### 8.2 Multi-Edit

When multiple compatible objects are selected:

- show shared fields only
- mixed values display as mixed state
- edits apply to all selected

### 8.3 Defaults And Overrides

Where objects inherit from tables or templates, inspector must distinguish:

- default value
- override value
- reset-to-default action

This is especially important for:

- monsters
- items
- loot templates
- material semantics

## Viewport And Interaction

## 9. Viewport Camera

### 9.1 Camera Modes

Required modes:

- free-fly
- orbit around selection
- top-down orthographic
- side orthographic
- front orthographic

### 9.2 Camera Controls

Default controls:

- `RMB drag`
  - look around
- `WASD`
  - move
- `Q/E`
  - move down/up
- `Shift`
  - speed boost
- mouse wheel
  - speed scale in free-fly
  - zoom in orthographic
- `F`
  - frame selection
- `Shift+F`
  - frame entire map

### 9.3 Camera Persistence

The editor stores:

- last camera per map
- per-layout camera settings
- orthographic zoom

## 10. Viewport Rendering

The viewport renders with runtime-compatible map renderers plus editor overlays.

### 10.1 Required View Modes

- lit
- unlit
- wireframe
- collision
- material semantics
- lighting only
- portal/room
- spawn/encounter
- script binding

### 10.2 Render Toggles

User toggles:

- terrain
- models
- indoor geometry
- billboards
- monsters
- lights
- gizmos
- helper icons
- bounds
- collision hulls
- normals
- ids/names
- fog
- shadows
- post
- sky
- water animation

### 10.3 Editor Overlays

Overlays are drawn on top of the normal scene.

Required overlay categories:

- selection outline
- hover outline
- transform gizmo
- room colors
- portal highlight
- terrain brush circle
- facet normal lines
- light radius spheres
- spawn radius rings
- monster guard radius rings
- chest markers
- transition arrows
- mechanism links
- script binding indicators
- invalid-reference markers

## 11. Picking And Hit Testing

Picking must support:

- facets
- terrain cells
- rooms
- portals
- decorations
- lights
- spawns
- monsters
- objects
- chests
- mechanism handles
- transition markers
- zones

Priority rules:

- active tool target type first
- then visible selectable objects
- hidden/locked objects ignored unless override mode enabled

## 12. Gizmos

### 12.1 Transform Gizmo

Standard gizmo with:

- move arrows
- plane handles
- rotate rings
- scale axes

Supports:

- local/world
- snap
- drag transaction grouping

### 12.2 Domain-Specific Gizmos

Required special gizmos:

- terrain brush disc
- terrain falloff preview
- spawn radius ring
- light radius sphere
- monster guard radius ring
- door direction arrow
- door move-length line
- transition direction arrow
- zone box/sphere handles
- portal face tint/outline
- facet UV offset preview arrows

## Tool Modes

## 13. Tool Mode Set

The editor uses explicit modes, shown in toolbar and tool panel.

Required modes:

- `Select`
- `Terrain`
- `Model`
- `Facet`
- `Room/Portal`
- `Door/Mechanism`
- `Decoration`
- `Light`
- `Spawn`
- `Monster`
- `Object`
- `Chest`
- `Transition`
- `Environment`
- `Script Binding`
- `Validation`

Mode changes alter:

- selectable object classes
- active overlays
- inspector subpanels
- viewport click behavior
- gizmos

## 14. Select Mode

Primary general mode.

Supports:

- click select
- ctrl multi-select
- marquee select
- select same texture
- select same model
- select same room
- select same script binding

Context actions:

- focus
- duplicate
- delete
- isolate
- move to camera
- land on floor/terrain

## 15. Terrain Mode

Outdoor only.

### 15.1 Brushes

Brush operations:

- raise/lower
- flatten
- smooth
- set absolute height
- noise
- ramp/spline shaping

### 15.2 Paint Operations

- terrain tile paint
- autotile paint
- semantic paint:
  - water
  - burn
  - future semantic flags

### 15.3 Terrain Panel

Controls:

- brush radius
- strength
- falloff
- brush shape
- target height
- active tileset
- active tile
- semantic flag palette

## 16. Model Mode

Outdoor:

- place imported models
- move/rotate/scale models
- save selected model chunk
- replace model asset

Indoor:

- mostly geometry import driven
- individual grouped geometry blocks may still be manipulable if supported

## 17. Facet Mode

Supports direct facet editing for both indoor and outdoor.

### 17.1 Facet Inspector Groups

- identity:
  - facet index
  - model index if outdoor
  - id/name
- appearance:
  - texture
  - UV offset
  - alignment flags
  - animated texture flags
- geometry:
  - polygon type
  - room
  - room behind
- semantics:
  - water
  - lava
  - sky
  - invisible
  - untouchable
  - secret
  - show on map / hide on map
- triggers:
  - event binding
  - trigger by click
  - trigger by step
  - trigger by monster
  - trigger by object
- door coupling:
  - moved by door
  - static bitmap
  - multi-door

### 17.2 Facet Actions

- assign texture
- align texture
- nudge UV
- select same texture
- bulk-set flags
- bind to mechanism/script
- convert to portal candidate

## 18. Room / Portal Mode

Indoor only.

### 18.1 Room Editing

Supports:

- assign selected facets to room
- split room
- merge rooms
- rename room
- set darkness
- set EAX environment

### 18.2 Portal Editing

Supports:

- mark facet as portal
- connect room and room-behind
- validate one-way/two-room relationship
- auto-build portals from room adjacency

### 18.3 Room Visuals

- colored room tint
- portal outline
- room id label
- optional isolate room

## 19. Door / Mechanism Mode

Indoor first-class.
Outdoor supported through generic mechanisms.

### 19.1 Door Editing

Door inspector fields:

- id
- speed open
- speed close
- move length
- direction X/Y/Z
- no sound
- start state
- close portal
- vertex filter
- vertex filter param 1
- vertex filter param 2

Door actions:

- create from selected facets
- auto-detect move direction
- assign adjacent facets
- preview open/close
- rebuild derived door data

### 19.2 Mechanism Editing

Shared mechanism model for indoor and outdoor.

Mechanism fields:

- id
- name
- type
- activators
- targets
- state model
- delays
- repeat rules
- conditions
- script callbacks

Mechanism visuals:

- link lines from activators to targets
- target badges
- activation area overlay if applicable

## 20. Decoration Mode

Used for map sprites/decorations.

Decoration inspector fields:

- decoration asset/name
- transform
- direction
- event id or script binding
- trigger radius
- trigger by touch/monster/object
- show on map
- chest flag
- invisible
- ship/obelisk-chest special bit
- sprite-light properties if applicable

Actions:

- place from asset browser
- duplicate
- move to floor
- rotate to camera direction
- replace decoration type

## 21. Light Mode

Supports placed map lights.

Light inspector fields:

- id
- position
- radius
- off
- RGB
- halo/type
- future successor extras:
  - intensity
  - flicker preset
  - pulse preset

Visuals:

- billboard icon
- radius sphere
- color preview

## 22. Spawn / Encounter Mode

Supports original-style spawn anchors and successor encounter authoring.

### 22.1 Spawn Inspector

- kind
- alias display:
  - `m1`
  - `m2b`
  - `i4`
- position
- radius
- group
- on-alert-map

### 22.2 Encounter Preview

The panel must resolve spawn aliases against current mapstats and show:

- resulting monster group or item class
- treasure level effect
- encounter picture/name
- warnings for missing references

### 22.3 Successor Extensions

- named encounter zones
- conditional encounter sets
- density preview

## 23. Monster Mode

Supports full monster-authored surface.

### 23.1 Monster Inspector Groups

- identity:
  - monster id
  - name id
  - NPC id
  - group
- transform:
  - position
  - direction
  - guard position
  - guard radius
- behavior:
  - hostile
  - ally
  - AI type
  - hostile type
  - move type
  - speed
  - fly
  - no flee
- visibility:
  - invisible
  - show on map
  - on alert map
- combat:
  - HP
  - level
  - armor class
  - experience
  - attack 1
  - attack 2
  - range attack
  - attack recovery
  - spells and spell chances
- resistances:
  - all supported schools/types
- loot:
  - treasure gold dice
  - item chance
  - item level
  - item type
  - carried item
- special:
  - shot count
  - summon settings
  - explode-on-death settings

### 23.2 Monster Actions

- place monster
- duplicate monster
- reset overrides to monster-table default
- convert current monster to preset
- preview effective stats

### 23.3 Visuals

- monster facing arrow
- guard radius ring
- label with name/id

## 24. Object Mode

For dynamic sprite-objects/runtime objects.

Inspector fields:

- type
- position
- direction
- look angle
- velocity
- room
- age
- max age
- visible
- temporary
- dropped by player
- ignore range
- no z-buffer
- attach to head
- missile
- removed
- light multiplier
- item payload
- spell/trap payload

This mode is necessary because these objects are authored initial scene content,
not only transient gameplay effects.

## 25. Chest Mode

Supports chest placement and full loot authoring.

### 25.1 Chest Inspector

- chest id/picture
- trapped
- identified
- linked script/mechanism if any

### 25.2 Chest Content Editor

This opens a dedicated popup/panel, not only inline inspector fields.

Required tabs:

- `Grid`
  - chest inventory cell layout
  - drag/drop exact items
- `Exact Items`
  - explicit item entries
- `Random Rules`
  - treasure-level item generation rules
  - item-class constraints
  - count ranges
- `Gold`
  - total gold range
  - split mode
  - stack count
- `Trap/Lock`
  - trap enabled
  - trap strength
  - lock threshold if applicable through sidecar/system linkage

### 25.3 Required Authoring Expressions

The chest editor must represent examples like:

- 4 random level-4-to-5 items
- 1 random level-6 weapon
- 3000-5000 gold split into 4 stacks
- 2 exact quest items plus normal random treasure

Freeform text may exist as an advanced mode, but these expressions must be
constructible via explicit controls.

## 26. Transition Mode

Supports map edges, doors-to-map, and map start/arrival markers.

Inspector fields:

- target map
- travel days
- direction
- arrival position
- use map start position
- transition conditions

Viewport visuals:

- edge arrows
- target labels
- arrival marker

## 27. Environment Mode

Supports map-wide environment/header settings.

### 27.1 Outdoor Environment Fields

- sky
- tilesets
- ceiling
- fog flag
- fog ranges
- rain
- snow
- underwater
- red fog
- no terrain
- always dark
- always light
- always foggy

### 27.2 Indoor Environment Fields

- default darkness
- per-room darkness
- EAX environment

### 27.3 Successor Additions

- ambient color
- fog color
- weather profile
- postprocess profile
- semantic water/lava/flow material settings

## 28. Script Binding Mode

Supports linking scene objects to Lua.

### 28.1 Script Browser

Required features:

- list map scripts
- open referenced Lua file
- jump from scene object to script reference
- jump from script reference to scene object
- show unresolved references

### 28.2 Binding Inspector

For selected object, show:

- legacy trigger id if any
- current Lua binding target
- callback/hook name
- referenced stable ids
- reverse-reference list

### 28.3 Lua Editing

Version 1 may embed a simple text editor or open an external editor.

Minimum requirements:

- open file
- save file
- syntax highlight
- line diagnostics
- jump-to-reference integration

## Secondary Panels And Popups

## 29. Asset Browser

Tabs:

- textures
- materials
- models
- decorations
- monsters
- items
- sounds
- videos
- scripts

Must support:

- search
- preview
- drag-drop into viewport
- replace selected object asset
- show missing asset state

## 30. Validation Panel

Validation categories:

- missing asset
- bad scene reference
- missing script target
- invalid room/portal relation
- unassigned transition target
- broken spawn alias
- impossible loot rule
- invalid door geometry
- stale compiled cache
- overlapping ids/names
- unsupported imported geometry condition

Each issue row shows:

- severity
- summary
- object reference
- click-to-focus
- optional fix action

## 31. Log / Console Panel

Tabs:

- editor log
- build log
- script runtime log
- import log

Supports filter/search and copy.

## 32. Required Popups And Wizards

Required dialogs:

- new map
- open map package
- import geometry
- import model
- missing texture resolver
- save model chunk
- create room from selection
- create portal
- create door/mechanism
- chest content editor
- spawn template picker
- monster preset picker
- transition target picker
- mapstats row editor
- rebuild derived data confirmation
- validation summary
- playtest options
- bulk rename / bulk replace

## Asset Pipelines

## 33. Geometry Import

### 33.1 Indoor

Primary path:

- import from `glTF`

Compatibility path:

- import from `OBJ`

Import options:

- import as rooms
- import as loose geometry
- import scale
- ignore imported UVs
- no export rotation
- missing texture mapping policy

Rules:

- `_Portal_` support for compatibility import
- `_Invisible_` support for compatibility import
- no blind triangulation assumptions for room/portal authoring

### 33.2 Outdoor

Primary path:

- import static models from `glTF`

Compatibility path:

- import static models and full map geometry from `OBJ`

Outdoor terrain itself is authored in editor, not imported as final authored
truth.

## 34. Texture And Material Import

Supports:

- diffuse/base color textures
- animated texture frame bindings
- semantic material tags
- future emissive/normal inputs where adopted

The editor must never force humans to encode semantics only in texture names.

## 35. Scene Build Pipeline

Build stages:

1. validate authored data
2. normalize ids/references
3. rebuild derived structures
4. emit `.scene.bin`
5. refresh runtime preview

Derived build products include:

- outdoor decoration lookup structures
- terrain normals
- indoor BSP
- indoor outlines
- room membership lists
- compiled door offsets/geometry lists

## 36. Save Behavior

`Save` writes:

- `.scene.yml`
- related Lua references if embedded edits changed
- editor-only metadata if used

`Build` writes:

- `.scene.bin`
- other derived caches

Geometry source files are only rewritten by explicit geometry export/compile
actions.

## Playtest And Simulation

## 37. Playtest Modes

Required:

- play from map start
- play from current camera position
- play with current unsaved scene state after temporary build

### 37.1 Playtest Rules

- uses runtime systems, not editor-only simulation
- launches through the same scene runtime interfaces as the game
- can stop and return to authoring without losing unsaved edits

### 37.2 Headless Validation Hooks

The editor build pipeline must integrate with headless tests for:

- map load
- scene.yml equivalence where relevant
- script compile/load
- spawn resolution
- chest content generation sanity
- missing asset detection

## UI Behavior Details

## 38. Selection Rules

- hidden objects are not selectable by default
- locked objects are not editable
- current tool filters target classes
- double-click frames object
- alt-click samples texture/material where applicable

## 39. Snapping

Supports:

- world grid snap
- local snap
- angle snap
- scale snap
- terrain surface snap
- floor/ground snap

## 40. Bulk Edit

Bulk edit is required for:

- facet flags
- texture assignment
- room assignment
- decoration replacement
- light intensity/radius
- spawn group changes
- monster group/hostility changes

## 41. Search And Reference Navigation

Global search must find:

- object by id
- object by name
- mapstats target map
- Lua script reference
- mechanism target
- texture/material usage
- decoration/monster/item usage

## 42. Missing Asset Behavior

On missing assets:

- object remains in scene
- inspector shows missing state
- validation emits issue
- missing asset resolver can remap

The editor must not silently discard authored references.

## Implementation Notes

## 43. Recommended Runtime Reuse

Use current systems where possible:

- `engine/EngineApplication.*` patterns for app loop
- `engine/BgfxContext.*`
- `game/scene/*SceneRuntime.*`
- `game/maps/MapAssetLoader.*`
- `game/outdoor/*` render/runtime helpers
- `game/indoor/IndoorDebugRenderer.*` as a source for indoor viewport overlays
  and picking behavior, but not as the final editor UI architecture
- `game/SpawnPreview.*`
- `game/tables/*`

## 44. Proposed Editor-Only Systems

New systems required:

- editor document model
- command stack
- stable id allocator
- panel registry
- gizmo/overlay renderer
- editor build service
- Lua reference browser
- content template editors

## 45. Performance Targets

Editor targets:

- idle viewport at 60 fps on normal dev machines for common maps
- large edits should remain interactive
- selection/picking under 16 ms for typical scenes
- build/compile incremental where possible

## 46. Versioning

Version all editor-authored formats:

- `.scene.yml`
- `.scene.bin`
- editor metadata

Migration tooling must exist for format revisions.

## 47. Implementation Phases

### Phase 1

- editor executable
- default docking UI
- viewport
- outliner
- inspector
- select/move/rotate/scale
- outdoor terrain + model + sprite + light + spawn editing
- save/load `.scene.yml`

### Phase 2

- indoor room/portal/door workflow
- chest editor
- monster editor
- transition/mapstats editor
- validation panel
- build cache emission

### Phase 3

- Lua browser/editor integration
- mechanism graph tooling
- bulk edit
- reference viewer
- playtest integration

### Phase 4

- successor semantic materials
- VFX emitters
- zones
- richer environment profiles

## 48. Final Acceptance Checklist

Before declaring the editor production-ready, verify all of the following.

- can create a new outdoor map from blank terrain
- can create a new indoor map from imported geometry
- can place and edit decorations, lights, spawns, monsters, objects, chests
- can define exact and random loot content
- can define original-style spawn aliases and see resolved previews
- can author door/mechanism data indoors
- can bind scene objects to Lua and navigate references both ways
- can edit map header and mapstats-linked data
- can validate and rebuild derived data
- can compile and playtest without manual file surgery
- can save, reopen, and get deterministic results

## One-Sentence Summary

The OpenYAMM editor must be a shared-runtime, docked C++ authoring application
that edits geometry-backed map packages, `.scene.yml`, Lua, and sidecar metadata
through dedicated domain tools rather than through one generic property list.
