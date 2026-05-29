# BLV/DLV Indoor Parity Plan

## Goal

Bring indoor gameplay to roughly the same runtime maturity as outdoor gameplay, while keeping the original
`BLV + DLV` data path for now.

The immediate target is OE-parity-oriented indoor runtime behavior, not a new authoring format. Converting BLV/DLV
into `.scene.yml` comes later, after the runtime is functionally correct and architecturally stable.

## Non-goals

- Do not replace BLV/DLV in this phase.
- Do not fork a separate indoor-only gameplay stack if an existing gameplay/UI/event system can be reused.
- Do not chase renderer sophistication before indoor runtime correctness.
- Do not copy OE code. OE is only the behavior and structure reference.

## Executive Summary

OpenYAMM outdoor gameplay is already a real runtime stack:

- `OutdoorPartyRuntime`
- `OutdoorWorldRuntime`
- `OutdoorSceneRuntime`
- `OutdoorGameView`
- outdoor movement/collision/interaction/combat/projectiles/HUD/event integration

OpenYAMM indoor support is currently not a gameplay stack. It is mostly:

- parsed BLV geometry
- parsed DLV delta state
- indoor textures / billboard asset preparation
- `IndoorSceneRuntime` for event/mechanism stepping
- `IndoorDebugRenderer` for textured inspection/debug viewing

That means the core indoor gap is not asset loading. The gap is runtime ownership and integration:

- movement
- collision
- sector / floor / portal logic
- actor and sprite-object runtime
- door runtime
- visibility / render traversal
- interaction
- combat/projectiles/spells
- gameplay UI integration
- save/restore parity

The right direction is not to “duplicate outdoors for indoors”. The right direction is:

1. extract the genuinely shared gameplay contracts now hidden behind `Outdoor*` types
2. build indoor-specific world/movement/rendering implementations behind those contracts
3. keep geometry/collision/render traversal indoor-specific where OE is indoor-specific

## Current OpenYAMM State

### What already exists for BLV/DLV

#### BLV parsing

`game/indoor/IndoorMapData.h`

Already loads:

- vertices
- faces
- sectors
- lights
- BSP nodes
- decorations/entities
- spawns
- outlines
- face texture coordinates and trigger-related fields

Important current structs:

- `IndoorFace`
- `IndoorSector`
- `IndoorLight`
- `IndoorBspNode`
- `IndoorEntity`
- `IndoorSpawn`
- `IndoorOutline`

#### DLV parsing

`game/maps/MapDeltaData.h`

Indoor delta parsing already includes:

- `visibleOutlines`
- `faceAttributes`
- `decorationFlags`
- actors
- sprite objects
- chests
- doors
- persistent variables
- location time / reputation / alert state

`MapDeltaDoor` is already rich enough to drive real indoor door runtime, not just inspection.

#### Indoor assets

`game/maps/MapAssetLoader.cpp`

Already builds:

- `IndoorTextureSet`
- indoor decoration billboard set
- indoor actor preview billboard set
- indoor sprite object billboard set

This is a strong base. Asset-side coverage is ahead of runtime-side coverage.

#### Indoor scene shell

`game/scene/IndoorSceneRuntime.*`

Current responsibilities:

- holds party reference
- holds optional `MapDeltaData`
- holds optional `EventRuntimeState`
- executes local/global scripted events
- advances mechanisms
- snapshots/restores event + delta state

Current non-responsibilities:

- party movement runtime
- indoor actor/sprite/chest/world runtime
- indoor collision
- indoor projectile/combat runtime
- indoor interaction/runtime picking
- indoor rendering/runtime visibility
- indoor time/gameplay state application beyond event/mechanism shell

#### Indoor renderer

`game/indoor/IndoorDebugRenderer.*`

Current coverage:

- textured face rendering
- animated face texture selection
- decoration billboards
- actor preview billboards
- sprite-object preview billboards
- free-camera inspect/raycast
- mechanism-adjusted visual door geometry

Current limitation:

This is still a debug viewer, not the gameplay renderer/runtime path.

### What outdoor already solved

Outdoor is the reference for runtime completeness, not for geometry behavior.

Key runtime pieces:

- `game/outdoor/OutdoorPartyRuntime.*`
- `game/outdoor/OutdoorWorldRuntime.*`
- `game/scene/OutdoorSceneRuntime.*`
- `game/outdoor/OutdoorGameView.*`
- `game/outdoor/OutdoorInteractionController.*`
- `game/outdoor/OutdoorRenderer.*`

Outdoor currently owns or wires:

- party movement state
- world actors
- projectiles
- spell casting backend
- combat events
- world items
- chests / corpse loot
- atmosphere / fog / rain
- map transitions
- interaction and hover logic
- gameplay HUD and stacked overlays
- save/restore of full runtime state

### Where the current duplication risk sits

Right now many gameplay subsystems are named and typed as outdoor-only even when their logic is mostly generic.

Examples:

- `PartySpellSystem::castSpell(Party&, OutdoorPartyRuntime&, OutdoorWorldRuntime&, ...)`
- `HouseInteraction` depends on `OutdoorWorldRuntime`
- `GameplayDialogController::Context` carries `OutdoorWorldRuntime *`
- `GameplayOverlayContext` exposes `OutdoorPartyRuntime *` and `OutdoorWorldRuntime *`
- `OutdoorInteractionController` owns event activation, NPC talk, world-item pickup, hover resolution,
  chest/corpse entry

If indoor is added by copying these systems, the codebase will split badly.

## OpenEnroth Reference Mapping

### OE top-level indoor model

OE keeps one engine, but indoor and outdoor location runtimes are distinct.

Relevant OE files:

- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.h`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp`
- `reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.h`
- `reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp`
- `reference/OpenEnroth-git/src/Engine/Graphics/BspRenderer.*`
- `reference/OpenEnroth-git/src/Engine/Graphics/PortalFunctions.*`

Important OE conclusion:

- top-level engine flow is shared
- indoor and outdoor geometry/collision/render traversal are not the same path
- some gameplay concepts are shared
- sector/BSP/portal/floor handling is fundamentally indoor-specific

### OE BLV structures

OE indoor runtime owns much more than OpenYAMM currently does.

`IndoorLocation` in OE owns:

- geometry vertices
- faces
- face extras
- sectors
- lights
- doors
- BSP nodes
- outlines
- packed face/sector/door arrays
- spawn points
- `LocationInfo` (`dlv`)
- `LocationTime`
- visible outlines
- particle / decal / spell-fx integration

Important structure deltas:

### Face split

OE separates:

- `BLVFace`
- `BLVFaceExtra`

OpenYAMM currently folds much of the face-extra/event/texture-delta data into `IndoorFace`.

This is not automatically wrong, but the runtime consequences matter:

- door UV adjustments
- event/hint resolution
- texture movement by door
- face event metadata

### Sector richness

OE `BLVSector` stores explicit categorized spans:

- floor faces
- wall faces
- ceiling faces
- portal faces
- non-BSP face span
- full BSP face span
- decoration ids
- light ids
- ambient light level
- first BSP node
- bounding box

OpenYAMM `IndoorSector` stores counts and some vectors, but it is not yet a real runtime query structure.

### Door runtime

OE `BLVDoor` is active runtime geometry state.

OpenYAMM currently stores door delta data in `MapDeltaDoor`, but only the debug renderer consumes it directly.

### Location delta/time

OE splits:

- `LocationInfo`
- `LocationTime`

OpenYAMM already has similar data in `MapDeltaLocationInfo` and `MapDeltaLocationTime`.

This is good alignment.

### OE indoor render/visibility behavior

OE indoor rendering is sector/BSP/portal-driven.

Key OE flow:

- `BLVRenderParams::Reset()`
- determine party sector and eye sector
- `PrepareDrawLists_BLV()`
- `pBspRenderer->Render()`
- gather visible sectors
- draw visible indoor faces
- draw visible decorations/sprite objects/actors
- apply indoor billboard lighting
- render particles

Important OE-specific concepts that OpenYAMM does not yet have indoors:

- party foot sector
- party eye sector
- visible sector list
- portal-clipped traversal
- indoor face visibility list
- indoor billboard light evaluation by sector/lights

### OE indoor collision/physics behavior

OE collision is shared at concept level, not at resolver-path level.

Shared concepts:

- sliding motion
- actor collisions
- decoration collisions
- portal traversal
- floor finding
- movement clipping

Indoor-specific OE functions:

- `CollideIndoorWithGeometry`
- `CollideIndoorWithDecorations`
- `CollideIndoorWithPortals`
- `ProcessPartyCollisionsBLV`
- `ProcessActorCollisionsBLV`
- `BLV_GetFloorLevel`
- `GetSector`

Outdoor-specific OE functions:

- outdoor terrain / bmodel collision
- outdoor support sampling
- outdoor map bounds / edge travel
- flight / water-walk outdoor semantics

Important conclusion:

Indoor should not try to reuse outdoor movement/controller logic directly. It should reuse only
shared motion/combat API shape.

### OE indoor doors

OE updates doors as active runtime geometry:

- door state machine
- sounds
- moved vertex positions
- recomputed face planes
- updated face texture coordinates and alignment offsets

OpenYAMM currently only does mechanism-adjusted visual geometry inside the debug renderer.

That is not enough for:

- gameplay collision
- projectile collision
- visibility correctness
- interaction correctness

### OE indoor lighting

OE indoor lighting differs materially from outdoor:

- sector ambient minima
- stationary lights
- mobile lights stack
- decoration-attached light contribution
- billboard light level resolution indoors

OpenYAMM outdoor lighting already has:

- daylight/fog/weather/fx light path

OpenYAMM indoor currently lacks a real equivalent runtime lighting model.

## Delta Matrix: OpenYAMM vs OE

| Area | OpenYAMM current | OE reference | Gap |
| --- | --- | --- | --- |
| BLV geometry parse | Mostly present | Present | Moderate |
| DLV parse | Mostly present | Present | Low |
| Indoor runtime shell | Minimal | Full runtime | High |
| Party movement indoors | Missing | Present | High |
| Actor runtime indoors | Missing | Present | High |
| Indoor sprite objects | Preview/state only | Present | High |
| Indoor door runtime | Visual debug-only | Full runtime | High |
| Sector queries | Missing runtime API | Present | High |
| Floor lookup | Missing | Present | High |
| Portal traversal | Missing | Present | High |
| BSP visibility | Missing | Present | High |
| Indoor lighting | Minimal | Present | High |
| Indoor interaction | Debug inspect only | Present | High |
| Indoor combat/projectiles | Missing | Present | High |
| Shared gameplay UI reuse | Mostly outdoor-bound | Shared at engine level | High |
| Save/restore indoor gameplay state | Minimal | Full | High |

## Shared vs Specific: What Must Be Reused

### Must become shared contracts

These are currently outdoor-bound but should become map-runtime-level services.

#### 1. Party-facing gameplay world interface

Needed consumers:

- spell casting
- interaction
- combat text
- NPC talk
- chest/corpse/world-item access
- event execution support
- line-of-sight queries

Proposed direction:

- add a shared gameplay-facing world interface
- indoor and outdoor both implement it
- keep geometry/collision internals private to each implementation

The interface should cover only gameplay needs, not renderer internals.

Likely responsibilities:

- map kind/name/time
- `party()`
- `eventRuntimeState()`
- actor iteration/query
- projectile spawn/cast entry points
- spell application to actors/party
- line-of-sight query
- chest/corpse/world-item open/take operations
- pending audio/combat/message queues
- map move requests

#### 2. Party spell backend

`PartySpellSystem` should not depend directly on outdoor types.

Current problem:

- spell backend takes `OutdoorPartyRuntime` and `OutdoorWorldRuntime`

Required change:

- retarget spell backend to shared party/world gameplay contracts

Important note:

- spell descriptors, mana/recovery logic, utility spell targeting, and many spell-side rules are shared
- spell execution details can dispatch to indoor/outdoor world implementations when geometry differs

#### 3. Gameplay dialog / house / transport context

`GameplayDialogController` and `HouseInteraction` are mostly gameplay systems, not outdoor systems.

Current issue:

- hard dependency on `OutdoorWorldRuntime`

Required change:

- depend on shared gameplay world/context

#### 4. Overlay/HUD access layer

`GameplayOverlayContext` currently exposes outdoor runtime pointers.

Required change:

- expose shared party/world interfaces
- keep outdoor-specific HUD widgets conditional where genuinely outdoor-only

Examples of outdoor-only HUD data:

- terrain minimap interpretation
- outdoor wizard-eye actor/item/projectile overlay semantics
- weather/rain display if not desired indoors

#### 5. Scene runtime contract

`IMapSceneRuntime` is currently too thin.

It only exposes:

- map kind/name
- party
- event runtime state
- pending map move
- `advanceGameMinutes`

This is enough for script shelling, not enough for gameplay view/control unification.

It should grow carefully into the common scene/gameplay contract, or a sibling interface should
be introduced for that role.

### Must remain indoor-specific

These should not be forced through outdoor geometry assumptions.

#### 1. Movement/collision resolver

Indoor needs:

- sector-aware floor finding
- portal-aware transitions
- face-plane sliding
- ceiling constraints
- door geometry participation
- indoor decoration collision semantics

#### 2. Visibility/render traversal

Indoor needs:

- BSP traversal
- portal clipping
- visible sector tracking
- eye-sector logic

#### 3. Door geometry runtime

Indoor doors are geometry mutation, not just state flags.

#### 4. Indoor lighting evaluation

Indoor is not outdoor fog/daylight logic with a different mesh.

#### 5. Indoor interaction picking

The shared high-level interaction rules can be shared, but face/portal/sector picking will need indoor implementation.

## Target Architecture

### New runtime split

Introduce indoor runtime peers to outdoor runtime rather than stretching the debug renderer:

- `IndoorPartyRuntime`
- `IndoorWorldRuntime`
- `IndoorGameView`
- `IndoorRenderer`
- `IndoorInteractionController`
- `IndoorMovementDriver` or `IndoorMovementController`

Also introduce shared interfaces used by gameplay systems:

- `IGameplayWorldRuntime`
- `IGameplayPartyRuntime`
- optionally `IGameplaySceneRuntime` or an expanded `IMapSceneRuntime`

### Proposed ownership

#### `IndoorSceneRuntime`

Should remain the scripted-map scene shell, but stop being the whole indoor runtime.

It should coordinate:

- map file identity
- party reference
- event runtime state
- local/global event programs
- map delta ownership
- world runtime and party runtime access

#### `IndoorWorldRuntime`

Should own:

- runtime actors
- runtime sprite objects
- indoor chests/corpses/world interactions
- door runtime state and geometry state
- visible outlines state application
- event state application into runtime
- audio/combat/pending message queues
- indoor lighting state needed by renderer
- projectile runtime and spell impact/runtime logic

#### `IndoorPartyRuntime`

Should own:

- indoor movement state
- indoor movement input update
- party spell movement-side consequences indoors
- indoor support state
- sector/foot/eye-sector runtime values

#### `IndoorRenderer`

Should own:

- BLV gameplay rendering path
- BSP/portal traversal
- visible face submission
- indoor billboards
- indoor particles/fx
- indoor lights uniform/setup

The existing `IndoorDebugRenderer` should either:

- become a thin debug mode layered over `IndoorRenderer`, or
- remain a separate tooling renderer but stop being the gameplay path

## Implementation Phases

### Phase 0: Freeze the target and document invariants

Deliverables:

- this plan
- explicit indoor parity checklist
- agreement that BLV/DLV remain the source format for now

Rules:

- no large gameplay duplication
- no indoor work inside `Outdoor*` runtime classes except extraction work

### Phase 1: Extract shared gameplay interfaces

Goal:

Make gameplay systems stop depending on `Outdoor*` types where not required.

Work:

- introduce shared gameplay world interface
- introduce shared gameplay party interface where needed
- retarget:
  - `PartySpellSystem`
  - `GameplayDialogController`
  - `HouseInteraction`
  - `GameplayOverlayContext`
  - any other gameplay service that only needs world/party services, not outdoor geometry

Success criteria:

- outdoor still works unchanged functionally
- gameplay service code compiles against shared interfaces
- indoor runtime can be wired later without editing these systems again

### Phase 2: Build indoor runtime ownership model

Goal:

Turn indoor from “scene shell + debug renderer” into a real runtime stack.

Work:

- add `IndoorPartyRuntime`
- add `IndoorWorldRuntime`
- extend `GameApplication` indoor branch to create them
- keep `IndoorSceneRuntime` for scripted state, but let it compose/coordinate the new runtimes
- define indoor snapshots for:
  - party runtime
  - world runtime
  - scene/runtime event state

Success criteria:

- indoor load path resembles outdoor load path structurally
- `GameSession` can persist indoor runtime beyond raw scene shell state

### Phase 3: Sector and floor query layer

Goal:

Implement the indoor geometry query API that all later systems depend on.

Required APIs:

- `getSector(position)`
- `getEyeSector(position, eyeHeight)`
- `getFloorZ(position, sectorId)`
- approximate / fallback floor query where needed
- sector portal transition query
- face visibility/query helpers
- indoor line segment vs face / door / portal tests

Notes:

- this is the indoor equivalent of outdoor support sampling and LOS support
- build this as a reusable geometry/query module, not buried inside rendering

Success criteria:

- party and actor movement code can ask for floor/sector cleanly
- projectiles and LOS can reuse the same geometry query layer

### Phase 4: Indoor door runtime

Goal:

Promote doors from debug visualization to real runtime geometry.

Work:

- create door runtime state from `MapDeltaDoor`
- update moving door state every frame/tick
- mutate active runtime geometry or maintain transformed door geometry state
- recompute affected face plane / z-calc / texture deltas
- make collision and rendering use the same door geometry state
- hook sounds and event-driven door transitions

Important requirement:

There must be one authoritative door geometry state used by:

- render visibility
- collision
- projectile collision
- interaction

Success criteria:

- opening/closing doors affect both what is drawn and what can be passed through

### Phase 5: Indoor movement and collision

Goal:

Implement party indoor locomotion with OE-like semantics.

Work:

- `IndoorMovementDriver` / `IndoorMovementController`
- face-plane sliding
- sector-aware movement
- portal transition handling
- floor snapping
- ceiling blocking
- decoration collision
- actor collision
- door collision

Keep outdoor-only rules out:

- no outdoor map-edge travel logic
- no terrain support logic
- no outdoor water-walk/flight semantics copied blindly

Explicit OE-parity checks:

- indoor floor finding
- indoor portal crossings
- wall sliding
- movement against moving/opening doors
- actor sector updates

Success criteria:

- party can traverse an indoor level with correct blocking/sliding/floor placement

### Phase 6: Indoor actor and sprite-object runtime

Goal:

Promote indoor actors/sprite objects from preview data to runtime entities.

Work:

- load runtime actors from indoor delta/spawns
- track AI state, hostility, health, spell effects, animations
- track indoor sprite objects/projectiles
- connect sector updates and floor updates
- integrate chests/corpse loot/runtime interactions

Reuse:

- shared combat/spell/dialog systems where possible

Do not reuse blindly:

- outdoor actor locomotion/collision assumptions

Success criteria:

- hostile/friendly indoor actors exist as real runtime entities
- indoor sprite objects are not just preview billboards

### Phase 7: Indoor visibility and gameplay renderer

Goal:

Replace debug-view rendering with gameplay-ready indoor rendering.

Work:

- implement indoor renderer distinct from debug renderer
- implement BSP traversal / portal clipping
- track visible sectors
- build visible face list
- submit only visible faces/billboards
- render door-mutated geometry
- integrate sprite objects / actors / particles

This is the biggest indoor-specific renderer task.

Important note:

Do not overgeneralize outdoor and indoor renderer internals. Share shader/material helpers and
billboard code where useful, but not the visibility model.

Success criteria:

- indoor view is driven by party camera
- only visible sectors/faces are drawn
- render behavior is stable enough for gameplay, not just debugging

### Phase 8: Indoor lighting model

Goal:

Make indoor readability and parity acceptable.

Work:

- sector ambient contribution
- stationary light evaluation
- dynamic/mobile light contribution as needed
- decoration-attached lights
- billboard light level evaluation
- indoor fog/sky cases if required by BLV flags/data

Pragmatic first target:

- readable OE-like indoor lighting, not full renderer perfection

Success criteria:

- actors/decorations/faces do not look like unlit debug geometry
- indoor lights differ meaningfully from outdoor daylight path

### Phase 9: Indoor interaction parity

Goal:

Make indoor clicking/space interaction feel like gameplay, not debug inspection.

Work:

- indoor inspect ray / hit resolution
- event-face interaction
- decoration interaction
- NPC interaction
- chest and corpse entry
- hover text / status bar logic
- keyboard vs mouse interaction parity

Architecture note:

- high-level interaction result handling can be shared
- hit testing itself should be indoor-specific

Success criteria:

- indoor doors/faces/decorations/NPCs/chests can be interacted with using the same gameplay flow as outdoors

### Phase 10: Indoor combat, projectiles, and spell integration

Goal:

Make indoor combat use the same gameplay systems, with indoor geometry semantics.

Work:

- indoor line-of-sight
- indoor projectile collision against faces/doors/actors
- indoor spell targeting
- immediate spell impacts
- actor spell effect application
- combat events/audio/text
- chest/corpse/world-item consequences

Important:

- `PartySpellSystem` should already be shared by this phase
- indoor runtime supplies the world-specific execution hooks

Success criteria:

- party spells and monster attacks work indoors with geometry-aware collision

### Phase 11: Indoor save/restore parity

Goal:

Persist indoor runtime state fully enough that level reload/save/load is stable.

Need snapshots for:

- party indoor movement state
- actor runtime state
- sprite-object/projectile state
- chest/corpse/world-item state
- door runtime state
- event/mechanism state
- map delta and location time

Success criteria:

- entering/leaving indoors and save/load preserve runtime state correctly

### Phase 12: Debug tools and acceptance tests

Goal:

Retain observability while moving away from the debug renderer gameplay path.

Work:

- keep indoor debug overlays as optional tooling
- add targeted diagnostics:
  - sector at camera
  - eye sector
  - current floor face
  - visible sector count
  - active door states
  - indoor actor sector ids
  - ray hit target
- add headless/runtime tests for geometry query invariants where feasible

## Concrete Refactor Targets in OpenYAMM

### Immediate extraction candidates

These are good first refactor targets because they currently create indoor blockers:

#### `PartySpellSystem`

Current file:

- `game/party/PartySpellSystem.*`

Needed change:

- remove direct `OutdoorPartyRuntime` / `OutdoorWorldRuntime` dependency

#### `GameplayDialogController`

Current file:

- `game/gameplay/GameplayDialogController.*`

Needed change:

- replace `OutdoorWorldRuntime *` in context with shared gameplay world contract

#### `HouseInteraction`

Current file:

- `game/gameplay/HouseInteraction.*`

Needed change:

- same as above

#### `GameplayOverlayContext`

Current file:

- `game/ui/GameplayOverlayContext.*`

Needed change:

- stop exposing only outdoor runtime types

#### `GameApplication`

Current file:

- `game/app/GameApplication.cpp`

Needed change:

- indoor branch should construct a real indoor runtime and gameplay view, not only
  `IndoorSceneRuntime + IndoorDebugRenderer`

### Systems that should stay separate

#### Outdoor movement vs indoor movement

Do not merge these into one class with branches. Share math/helpers if useful, not the whole controller.

#### Outdoor visibility vs indoor visibility

Outdoor frustum over terrain/BModels is not indoor BSP+portal traversal.

#### Outdoor support sampling vs indoor floor/sector logic

These should expose similar services to gameplay code, but not share implementation.

## Data Mapping Decisions

### Keep BLV/DLV as the authoritative source format in this phase

Reason:

- runtime parity work is already large
- changing authoring/runtime format simultaneously will hide behavioral regressions

### Likely internal runtime representations to add

Even while keeping BLV/DLV input, internal runtime structures should become stronger than the raw parsed structs.

Examples:

- indoor runtime face geometry cache
- sector query cache
- door runtime geometry state
- visible face/sector lists
- indoor actor runtime structs
- indoor projectile structs

This is acceptable and desirable. The key is that BLV/DLV stay the load/save boundary for now.

## Validation Checklist

Indoor runtime is ready for parity iteration when all of the following are true:

- party can move through BLV spaces with correct floor snapping
- walls/doors/portals block or pass correctly
- sector id and eye sector are stable during traversal
- indoor actors spawn and update correctly
- indoor sprite objects/projectiles collide correctly
- clicking/space interaction hits the right face/entity/NPC/chest
- door movement changes both visuals and collision
- visible sector rendering works without obvious overdraw-through-portals bugs
- indoor billboards/decorations respect lighting and visibility
- spells and monster attacks work indoors
- save/load preserves indoor runtime state

## Risks

## 1. Accidental outdoor leakage

Risk:

Indoor code keeps pulling in `OutdoorWorldRuntime` because it is the only place where gameplay services exist.

Mitigation:

- do Phase 1 first
- introduce shared interfaces before major indoor implementation

## 2. Rendering-first trap

Risk:

Trying to perfect indoor rendering before sector/floor/door runtime exists.

Mitigation:

- build sector/floor/door runtime before final gameplay renderer pass

## 3. Debug-renderer accretion

Risk:

Turning `IndoorDebugRenderer` into the gameplay renderer by adding more hacks.

Mitigation:

- either demote it to tooling or explicitly refactor common pieces out of it early

## 4. Data-model mismatch around doors/faces

Risk:

Current `IndoorFace` representation may be too flattened for door UV/face-extra parity.

Mitigation:

- allow runtime-side split/cache structures even if loader output stays as-is

## Recommended Build Order

1. Extract shared gameplay interfaces from outdoor-bound systems.
2. Add `IndoorPartyRuntime` and `IndoorWorldRuntime` ownership skeletons.
3. Implement sector/floor/portal query layer.
4. Implement real indoor door runtime.
5. Implement indoor party collision/movement.
6. Implement indoor actor/sprite-object runtime.
7. Wire indoor interaction against the runtime.
8. Build indoor gameplay renderer with BSP/portal visibility.
9. Add indoor lighting.
10. Wire combat/projectiles/spells.
11. Complete save/restore parity.
12. Keep debug tooling on top.

## Bottom Line

The main architectural problem is not that indoor data is missing. The data coverage is already fairly good.

The real problem is that outdoor became the de facto owner of nearly all gameplay runtime services, while indoor
stopped at parsing plus debugging.

So the correct next move is:

- extract shared gameplay contracts from outdoor
- create proper indoor runtime peers
- keep collision, sector logic, doors, and visibility indoor-specific
- reuse gameplay/event/UI/combat logic through those shared contracts

That path gives OE-style parity without duplicating the whole game stack twice, and it also sets up the later
BLV/DLV-to-`.scene.yml` conversion on top of a stable runtime rather than during runtime churn.
