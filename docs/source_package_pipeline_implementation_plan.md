# Source Package Pipeline Implementation Plan

## Purpose

This document defines a concrete, phased implementation plan for moving
OpenYAMM from direct baked-map editing toward a source-first level pipeline.

Target outcome:

- external DCC tools own mesh creation
- OpenYAMM owns map assembly and gameplay semantics
- editor saves source packages
- build step compiles source packages to runtime maps
- current runtime remains usable during migration
- headless tests verify each phase end-to-end

This plan is intentionally executable by follow-up Codex sessions without
having to rediscover:

- package structure
- source ownership
- migration order
- compiler boundaries
- validation rules
- acceptance criteria

## References

Primary local references:

- [editor_production_spec.md](/home/pjasicek/github/OpenYAMM/docs/editor_production_spec.md)
- [level_editor_authoring_inventory.md](/home/pjasicek/github/OpenYAMM/docs/level_editor_authoring_inventory.md)
- [runtime_refactor_plan.md](/home/pjasicek/github/OpenYAMM/docs/runtime_refactor_plan.md)
- [OutdoorMapData.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorMapData.h)
- [OutdoorSceneYml.h](/home/pjasicek/github/OpenYAMM/game/maps/OutdoorSceneYml.h)
- [EditorDocument.h](/home/pjasicek/github/OpenYAMM/editor/document/EditorDocument.h)
- [EditorSession.h](/home/pjasicek/github/OpenYAMM/editor/document/EditorSession.h)

## Product Direction

The desired long-term content model is:

1. external source assets
2. OpenYAMM source package
3. compiled runtime output

Where:

- external source assets:
  - Blender files
  - `OBJ` initially
  - `glTF/GLB` later
  - source textures/materials
- OpenYAMM source package:
  - gameplay-meaningful
  - reimport-safe
  - diffable
  - editor-owned
- compiled runtime output:
  - phase 1:
    - `ODM`
    - `BLV`
    - current companions
  - phase 2:
    - successor chunked runtime format if needed

## Core Principles

1. `ODM` and `BLV` are compiled runtime geometry, not ideal long-term source.
2. `.scene.yml` remains semantic gameplay authoring, not geometry import state.
3. External DCC tools remain responsible for heavy mesh authoring.
4. The editor must preserve authored meaning across reimport.
5. Source package save and runtime build must be separate operations.
6. Every phase must remain headless-testable.

## Source Package Layout

Initial outdoor package target:

- `assets_dev/Data/maps/out01/map.yml`
- `assets_dev/Data/maps/out01/geometry.yml`
- `assets_dev/Data/maps/out01/terrain.yml`
- `assets_dev/Data/maps/out01/scene.yml`
- `assets_dev/Data/maps/out01/mapstats.yml`
- `assets_dev/Data/maps/out01/events/`
- `assets_dev/Data/maps/out01/imports/`

Meaning:

- `map.yml`
  - map identity
  - package version
  - environment metadata
- `geometry.yml`
  - bmodel instances
  - source mesh links
  - import settings
  - material remaps
  - editor grouping/defaults
- `terrain.yml`
  - height edits
  - tile painting
  - terrain semantic flags
- `scene.yml`
  - entities
  - spawns
  - actors
  - sprite objects
  - chests
  - face interaction overrides
- `mapstats.yml`
  - encounter families
  - travel/treasure/environment sidecar data
- `events/`
  - local event source files
- `imports/`
  - import fingerprints
  - optional derived diagnostics

## Ownership Split

### External DCC Owns

- mesh topology
- UV unwrap
- material slots
- source-local transforms

### `geometry.yml` Owns

- source asset path
- source mesh/node name
- import scale
- import orientation policy
- per-instance transform before bake
- material-to-runtime-texture remaps
- editor tags and groups
- bulk face defaults
- reimport fingerprint

### `terrain.yml` Owns

- authored heightfield edits
- terrain tile painting
- terrain semantic flags

### `scene.yml` Owns

- gameplay semantics
- scene objects
- encounter anchors
- actor and chest state
- interactive faces

### Compiled Runtime Owns

- baked geometry
- baked terrain
- runtime-ready texture and UV data
- runtime-ready collision and indices

## Stable ID Strategy

Stable ids must arrive before wide source-package adoption.

Required ids:

- `geometry_id` for each bmodel instance
- `face_id` where possible for source-side face references
- stable scene object ids later if needed

Rules:

- raw `bmodelIndex` and `faceIndex` remain compile-time/runtime indices
- source package references should migrate toward stable ids
- compiler resolves stable ids into baked runtime indices
- when topology changes on reimport:
  - preserve ids by source submesh and face group if possible
  - otherwise use best-effort geometric matching
  - emit validation warnings when ids cannot be preserved

## Save / Build / Playtest Model

Use these operations explicitly:

- `Save`
  - writes source package only
- `Build`
  - compiles source package into runtime output
- `Playtest`
  - ensures build is fresh
  - launches game using compiled output

Do not blur source save and runtime build into one implicit step.

## Module Plan

### Editor

- `editor/document/`
  - source package load/save
  - dirty tracking by source file
  - build orchestration
- `editor/import/`
  - source asset linkage
  - reimport pipeline
- `editor/build/`
  - source package compiler entry points
- `editor/panels/`
  - package validation panel
  - import status panel
- `editor/app/`
  - Save / Build / Playtest commands

### Game / Tools

- `game/maps/`
  - package compiler and package loader helpers
- `game/outdoor/`
  - compile outdoor source to `OutdoorMapData`
- `game/indoor/`
  - later compile indoor source to `IndoorMapData`
- `tools/`
  - headless package build / validation commands as needed

## Phase Plan

## Phase 0. Preconditions

### Goal

Prepare the editor/runtime for source-package introduction without changing
content ownership yet.

### Tasks

- audit current save paths:
  - what mutates `ODM`
  - what mutates `.scene.yml`
- isolate editor commands into:
  - save semantics
  - save geometry
  - future build command hooks
- centralize source-vs-runtime dirty tracking in `EditorDocument`
- document current runtime inputs:
  - `ODM`
  - `.scene.yml`
  - `map_stats.txt`
  - events

### Code Areas

- `editor/document/EditorDocument.*`
- `editor/document/EditorSession.*`
- `editor/app/EditorMainWindow.*`

### Headless Checks

- existing:
  - `--headless-run-regression-suite outdoor-scene-yml-roundtrip`
- add:
  - explicit check that save only writes intended outputs for current model

### Exit Criteria

- save/build responsibilities are easy to separate in later phases
- no implicit runtime writes happen outside explicit save/build entry points

## Phase 1. Minimal `geometry.yml`

### Goal

Introduce persistent geometry-side source metadata without replacing `ODM`.

### Deliverable

A minimal `geometry.yml` that stores:

- package version
- source map file identity
- per-bmodel `geometry_id`
- source asset path
- source mesh/node name
- import scale
- default texture/material remaps
- remembered import settings

### Tasks

1. Define schema.
2. Add load/save in editor.
3. Persist current session-only reimport metadata into `geometry.yml`.
4. Keep `ODM` as the runtime geometry source for actual play.
5. Surface source metadata in bmodel inspector.

### Schema Sketch

```yaml
version: 1
map_file: out01.odm
bmodels:
  - geometry_id: bmodel_out01_0001
    runtime_bmodel_index: 0
    source:
      asset_path: imports/houses/house_a.obj
      mesh_name: House_A
      scale: 1.0
    materials:
      default_texture: grastyl
      remaps:
        roof_mat: roof01
        wall_mat: stone02
```

### Code Areas

- `editor/document/EditorDocument.*`
- `editor/document/EditorSession.*`
- `editor/app/EditorMainWindow.*`
- new:
  - `game/maps/OutdoorGeometryYml.*` or equivalent

### Headless Checks

Add:

- load `ODM` + generated `geometry.yml`
- verify bmodel count and geometry ids
- verify remembered reimport path survives save/reload
- verify no runtime behavior changes when `geometry.yml` is present but unused

Suggested command:

- `openyamm-editor --headless-run-regression-suite outdoor-geometry-yml-roundtrip`

### Exit Criteria

- editor can save and reopen `geometry.yml`
- reimport source survives restart
- runtime still works from `ODM` exactly as before

## Phase 2. Source Package Root

### Goal

Move from ad-hoc sidecars to a map package root.

### Deliverable

Editor can open:

- legacy:
  - `out01.odm`
- package:
  - `Data/maps/out01/`

With package-aware routing for:

- `map.yml`
- `geometry.yml`
- `scene.yml`

### Tasks

1. Define `map.yml`.
2. Add package discovery and resolution.
3. Add package-aware document open/save.
4. Support legacy fallback when package is absent.
5. Add migration command:
  - legacy map -> package scaffold

### Code Areas

- `editor/document/EditorDocument.*`
- `editor/document/EditorSession.*`
- `game/maps/`
- `tools/` migration script or command

### Headless Checks

- scaffold package from `out01.odm + out01.scene.yml`
- reopen package
- normalize output and compare against legacy-loaded authored state

### Exit Criteria

- package load/save works
- legacy path still works
- migration command is deterministic

## Phase 3. Terrain Source Model

### Goal

Make terrain source-authored instead of only direct `ODM` mutation.

### Deliverable

`terrain.yml` stores:

- height edits
- tile paint
- terrain semantic overrides

Editor terrain tools read/write `terrain.yml` state.

### Tasks

1. Define `terrain.yml`.
2. Add source terrain model to `EditorDocument`.
3. Retarget paint/sculpt tools to source terrain state.
4. Add compiler path from terrain source to in-memory `OutdoorMapData`.
5. Keep build output identical to current runtime where possible.

### Schema Sketch

```yaml
version: 1
height_map:
  encoding: rle_hex
  data: ...
tile_map:
  encoding: rle_hex
  data: ...
terrain_overrides:
  - cell: [12, 42]
    water: true
    burn: false
    legacy_attributes: 2
```

### Code Areas

- `editor/document/EditorDocument.*`
- `editor/document/EditorSession.*`
- `editor/viewport/EditorOutdoorViewport.*`
- `game/maps/`
- `game/outdoor/OutdoorMapData.*`

### Headless Checks

- terrain paint round-trip through package
- terrain sculpt round-trip through package
- compile package to `ODM`
- compare compiled terrain against editor source state

### Exit Criteria

- terrain edits survive package reload
- build emits correct `ODM.heightMap` and `tileMap`
- direct terrain editing no longer depends on immediate `ODM` mutation as the
  authoritative source

## Phase 4. Source-Aware Geometry Compiler

### Goal

Compile `geometry.yml` + imported source assets into baked `OutdoorMapData`.

### Deliverable

Editor/source pipeline can:

- load source-linked bmodels
- reimport external mesh
- compile to baked runtime bmodel geometry
- preserve scene semantics when geometry is rebuilt

### Tasks

1. Introduce source geometry document objects.
2. Add compile step:
   - source mesh + remaps + instance transform -> `OutdoorBModel`
3. Preserve or remap stable ids on reimport.
4. Rebuild compiled `ODM` from source package during build.
5. Add validation for missing source assets and remap failures.

### Code Areas

- `editor/import/`
- `editor/build/`
- `editor/document/`
- `game/maps/`
- `game/outdoor/OutdoorMapData.*`

### Headless Checks

- build package with imported `OBJ`
- reimport changed `OBJ`
- verify compiled `ODM` changes while source semantics remain
- verify interactive face overrides survive geometry rebuild when topology is
  unchanged
- verify warnings when stable ids cannot be preserved

### Exit Criteria

- geometry source is authoritative for imported bmodels
- `ODM` becomes a build artifact for those bmodels
- editor can reopen package and deterministically rebuild runtime geometry

## Phase 5. Stable IDs For Geometry Semantics

### Goal

Stop treating source semantics as fundamentally tied to raw runtime indices.

### Deliverable

Scene-side references can use stable ids for:

- bmodels
- faces

Compiler resolves them to baked indices.

### Tasks

1. Add stable id fields to geometry source model.
2. Add stable-id references to scene semantic model.
3. Keep backward compatibility with raw indices during transition.
4. Add remapping report when compile changes baked indices.

### Code Areas

- `editor/document/`
- `game/maps/OutdoorSceneYml.*`
- new stable-id resolver helpers in `game/maps/`

### Headless Checks

- compile package with stable face refs
- rebuild after bmodel reorder
- verify semantic refs still target the same logical faces

### Exit Criteria

- authored face semantics survive index churn
- package is no longer structurally fragile against compile reorder

## Phase 6. Package Build Command

### Goal

Make runtime output an explicit build step.

### Deliverable

Editor UI and headless tools support:

- `Save Source`
- `Build Map`
- `Playtest`

### Tasks

1. Add build orchestration to editor.
2. Add headless package build command.
3. Separate build artifacts from source package.
4. Add stale-build detection.

### Code Areas

- `editor/app/`
- `editor/build/`
- `tools/`

### Headless Checks

- source-only save leaves runtime unchanged
- build updates runtime outputs
- repeated build is deterministic

### Exit Criteria

- source and compiled outputs are clearly separated
- editor workflows are explicit and predictable

## Phase 7. Validation System

### Goal

Catch source-package, import, and compile issues before play.

### Validation Rules

- missing source asset path
- changed source fingerprint
- missing texture remap
- invalid stable face id
- duplicate geometry ids
- degenerate faces
- unresolved event references
- impossible terrain edits
- stale compiled output

### Tasks

1. Add package validation service.
2. Add validation panel in editor.
3. Add headless validation command.
4. Gate build/playtest on hard validation failures.

### Headless Checks

- package validation suite with intentionally broken fixtures

### Exit Criteria

- validation catches common authoring failures before runtime

## Phase 8. `mapstats.yml`

### Goal

Move map-specific encounter and sidecar metadata into the package.

### Deliverable

`mapstats.yml` stores:

- encounter 1/2/3
- difficulty
- min/max counts
- travel/environment values
- treasure level
- redbook/environment metadata

### Tasks

1. Define schema.
2. Add editor UI for mapstats package editing.
3. Add compile/load bridge back to current runtime expectations.
4. Add import from `map_stats.txt` row.

### Headless Checks

- import row -> `mapstats.yml`
- reload package
- runtime encounter previews match source data

### Exit Criteria

- map encounter semantics are source-authored inside the package

## Phase 9. Event Package

### Goal

Move map-local event sources into package structure.

### Deliverable

Map-local event files under:

- `events/*.evt.yml`
- later `events/*.lua`

### Tasks

1. Define package event file layout.
2. Add source/load/save support.
3. Add jump-to-reference from scene objects/faces.
4. Add validation for broken event links.

### Headless Checks

- load package with event files
- resolve scene links
- validate missing/broken links

### Exit Criteria

- scene semantics and local scripts are co-owned in the package

## Phase 10. Indoor Parity

### Goal

Repeat the outdoor source-package pattern for indoor maps.

### Tasks

- add indoor `geometry.yml`
- add indoor source terrain equivalent where relevant
- add `BLV` compiler path
- reuse package root conventions

### Exit Criteria

- one source-package model supports both outdoor and indoor maps

## Phase 11. Successor Runtime Format

### Goal

Support larger worlds and streaming without changing source authoring model.

### Deliverable

A chunked compiled runtime format that is built from the same package source.

### Required Features

- chunked terrain
- chunked geometry instances
- streaming cells
- stable ids across cells
- async loading support

### Rule

Do not block earlier phases on this step.

The source package must be designed so this phase is additive.

## Migration Strategy

### Legacy Input

- `ODM`
- `BLV`
- `.scene.yml`
- `map_stats.txt`
- legacy event sources

### Migration Commands

Need commands for:

- legacy outdoor map -> package scaffold
- legacy indoor map -> package scaffold
- package -> compiled runtime

### Rule

Migration must not require the whole project to switch at once.

## Headless Test Plan

Need a dedicated package suite in addition to current outdoor round-trip tests.

### Suite Names

Recommended new suites:

- `outdoor-geometry-yml-roundtrip`
- `outdoor-package-roundtrip`
- `outdoor-package-build`
- `outdoor-package-validation`
- `outdoor-reimport-preserves-semantics`
- later:
  - `indoor-package-roundtrip`

### Minimum Assertions By Phase

Phase 1:

- `geometry.yml` save/load round-trip
- reimport metadata persists

Phase 2:

- package scaffold from legacy map
- package reopen equals legacy authored state

Phase 3:

- terrain paint/sculpt survive source save/build/reload

Phase 4:

- imported geometry rebuilds deterministically
- material remaps survive save/reload

Phase 5:

- stable face references survive recompilation and reorder

Phase 6:

- source save does not alter runtime outputs
- build alters runtime outputs deterministically

Phase 7:

- validation fixtures produce expected diagnostics

Phase 8:

- encounter previews/runtime resolution match `mapstats.yml`

Phase 9:

- event file links resolve from scene objects and faces

## Risks

Primary risks:

- raw runtime indices leaking into source package
- reimport destroying authored semantics
- trying to replace DCC responsibilities with custom editor mesh editing
- binding save and build together too tightly
- introducing chunked runtime concerns too early

Mitigation:

- stable id strategy early
- compiler boundary explicit
- source package minimal at first
- runtime compatibility retained during migration

## Recommended Execution Order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7
9. Phase 8
10. Phase 9
11. Phase 10
12. Phase 11

## Definition Of Success

This plan is successful when:

- OpenYAMM can author a map package without using `ODM` as the only source of
  truth
- reimport is persistent and semantic-safe
- source save and runtime build are separate
- current runtime can still play compiled output
- the same source package model can later target a larger successor runtime
  without rewriting authoring workflows
