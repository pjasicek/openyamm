# Shared System Unification Plan

## Goal

Finish the architectural split between:

- shared gameplay systems
- shared presentation and UI systems
- runtime-specific indoor and outdoor world adapters

The target is straightforward:

- if a system answers "what should happen?" or "how should it look to the
  player?", it should be shared
- if a system answers "how does this map representation expose geometry,
  visibility, collision, or traversal?", it should stay runtime-specific

This plan exists to prevent the indoor runtime work from drifting into a second
copy of outdoor gameplay/UI/rendering logic.

## Non-goals

- Do not merge ODM and BLV geometry/collision into one giant scene class.
- Do not introduce broad `isIndoor` / `isOutdoor` branching into shared code.
- Do not keep parallel indoor-only and outdoor-only copies of HUD, dialogue,
  spell, projectile, or actor rendering paths.
- Do not copy OE code. OE remains a behavior reference only.

## Architectural Rule

The correct split is:

### Shared

- gameplay rules
- UI logic
- UI rendering
- overlay/input semantics
- spell/projectile/effect semantics
- common billboard and particle presentation
- save/session semantics

### Runtime-specific

- map loading/parsing
- geometry representation
- collision queries
- line-of-sight queries
- visibility/culling queries
- sector/portal traversal indoors
- terrain/bmodel traversal outdoors
- scene-local render data extraction

## Target End State

When this plan is complete:

- indoor and outdoor call the same gameplay HUD stack
- indoor and outdoor call the same stacked-screen/UI stack
- indoor and outdoor call the same dialogue/chest/shop/spellbook/inventory
  stack
- indoor and outdoor call the same spell/projectile/effect stack
- indoor and outdoor call the same actor/deco/sprite billboard rendering stack
  wherever geometry representation is not the reason for divergence
- `IndoorGameView` and `OutdoorGameView` become thin adapters instead of large
  owners of behavior
- world-specific code stays behind explicit interfaces

The ownership model to keep driving toward is:

- `GameSession`
- `Party`
- shared UI / shared input / shared gameplay controllers
- `IGameplayWorldRuntime *activeWorld`

That means shared overlay/UI/controller state belongs to `GameSession`, while
`IndoorGameView` and `OutdoorGameView` expose only world/runtime services plus
render/layout capabilities that genuinely differ by runtime.

## System Inventory

This section is the authoritative ownership map.

### A. Shared UI and Screen Systems

These should be identical between indoor and outdoor.

- gameplay HUD
- status bar text / event text
- main gameplay menu
- save screen
- load screen
- controls screen
- keyboard screen
- video options screen
- rest screen
- journal/history/quests/notes views
- map/minimap UI rendering and overlays
- character screen
- inventory screen
- spellbook screen
- chest UI
- corpse loot UI
- house/shop/bank/trainer/guild overlays
- dialogue rendering and dialogue interaction flow
- Arcomage UI flow
- town portal UI
- Lloyd's beacon UI
- item inspect / tooltip UI
- screen-space targeting overlays and crosshairs
- screen overlays such as fullscreen fades/flash/drain effects

### B. Shared UI Infrastructure

These are support systems that should not live in outdoor-only code.

- HUD layout loading and layout resolution
- HUD texture loading
- HUD bitmap font loading
- HUD texture tint caches
- HUD font tint caches
- HUD quad submission abstraction
- HUD/world-space textured quad helper APIs used by overlays
- UI pointer hit testing
- UI click/hover/pressed asset resolution
- YML-driven screen presentation layer

### C. Shared Gameplay Systems

These should be shared because they define behavior, not world representation.

- spell definitions and spell semantics
- spell targeting semantics
- spell damage rolls
- buff/debuff application rules
- quick-cast and attack-cast semantics
- enchant-item spell flow
- dialogue state machine
- event dialog action handling
- house service logic
- merchant/bank/temple/trainer/guild logic
- item move/hold/transfer logic
- chest/corpse loot rules
- treasure generation
- random enchant generation
- qbit semantics
- quest/note/journal state semantics
- party spell logic
- combat resolution rules
- UI input debounce/repeat rules for shared overlays

### D. Shared Presentation Systems

These should be shared when their job is "how to present game state", not "how
 to query world geometry".

- projectile simulation model
- projectile trail/impact effect logic
- particle system
- particle renderer
- status-effect/debuff FX
- impact FX
- decal logic such as blood splats where world placement is abstracted
- weather presentation logic
- fog color/density policy
- actor outline/highlight presentation
- actor billboard draw submission
- decoration billboard draw submission
- sprite-object billboard draw submission
- billboard tint/fog/filtering treatment
- shared actor/deco/object sprite frame selection rules

### E. Runtime-specific World Adapters

These should stay different because the world representation is different.

#### Outdoor-specific

- ODM/DDM loading
- terrain extraction
- bmodel extraction
- terrain height/cell/slope queries
- outdoor collision queries
- outdoor world LOS queries
- sky/terrain-atmosphere source extraction
- terrain/bmodel visibility and culling
- outdoor map transition geometry queries

#### Indoor-specific

- BLV/DLV loading
- sector/BSP/portal data extraction
- indoor floor/ceiling/face queries
- indoor collision queries
- indoor LOS queries
- sector/portal visibility and culling
- mechanism/door geometry movement data
- indoor event-face geometry lookup

## Shared-vs-Adapter Matrix

Use this matrix when deciding ownership:

### Shared + adapter-backed

These should be shared, but call runtime-specific query interfaces:

- world interaction selection
- spell target validation
- projectile collision
- projectile impact placement
- actor visibility checks
- actor/world hover picking
- blood/decal placement
- water-impact detection
- minimap/world marker sampling
- AoE ground marker placement

### Fully shared

These should need no indoor/outdoor branching in their core:

- menus and YML screens
- dialogue logic and rendering
- chest and corpse UI logic
- spellbook and character UI
- item transfer logic
- quick-cast semantics
- status text handling
- qbit semantics
- house service logic
- spell and projectile semantics

### Fully runtime-specific

These should not be forced into one implementation:

- world geometry loading
- raw collision kernels
- raw LOS kernels
- raw culling kernels
- terrain sampling
- sector/portal traversal

## Concrete Interface Targets

The codebase should converge on these seams.

### 1. Shared Gameplay Overlay View

Current direction already exists in part:

- `game/ui/IGameplayOverlayView.h`
- `game/ui/GameplayOverlayContext.*`

Target:

- all shared overlay/screen renderers talk only to a runtime-neutral overlay
  interface
- indoor and outdoor provide only the minimal adapter methods

This interface should fully cover:

- layout lookup and resolution
- HUD texture/font access
- UI quad submission
- active shared overlay state
- status text
- party/runtime access needed by shared overlay controllers

### 2. Shared World Query Interface

Need a runtime-neutral interface used by gameplay systems that touch the world.

Target responsibilities:

- raycast from screen/cursor or from a world ray
- LOS test
- projectile collision query
- water query
- floor/ground placement query
- actor enumeration in radius / in frustum / in LOS
- decoration/object/face interaction query

This is not a renderer interface. It is a gameplay spatial-query interface.

### 3. Shared Billboard Presentation Layer

Target responsibilities:

- submit actor/deco/sprite-object billboards
- resolve tint/fog/outline/filtering behavior
- resolve sprite frame / orientation rules

Runtime-specific code should only provide:

- the list of visible billboard instances
- per-instance state
- visibility/culling results

### 4. Shared Projectile and Effect Service

Target responsibilities:

- projectile spawn/update semantics
- trail spawning
- impact spawning
- spell FX routing
- debuff FX
- screen overlays tied to spells

Runtime-specific code should only provide:

- collision query adapter
- impact surface classification
- world placement helpers

### 5. Shared Screen/UI Controller Layer

Target responsibilities:

- menu/overlay state transitions
- shared hotkeys
- input debouncing/latching
- dialogue/chest/shop/spellbook/character/inventory flow

Runtime-specific code should only provide:

- requests that touch the world/runtime
- active world state backing the UI

## Current Redundancy Inventory

These are the main duplication risks today:

### High risk

- HUD texture/font/layout ownership still historically tied to
  `OutdoorGameView`
- dialogue orchestration partly duplicated between indoor and outdoor
- actor/deco/sprite billboard draw paths still too runtime-local
- world interaction logic still too entangled with concrete outdoor/indoor view
  types

### Medium risk

- gameplay overlay input flow may drift into scene-specific branches
- spell/projectile integration may fork if indoor adapters are not introduced
  cleanly
- stacked screens may retain scene-owned glue instead of one shared owner

### Low risk

- save/session state is already moving in the right direction
- `GameplayUiController` and scene runtimes already provide a reasonable base

## Migration Plan

This work should happen in waves, not ad hoc.

### Wave 1. Finish Shared HUD Ownership

Goal:
- remove outdoor ownership of generic HUD infrastructure

Do:
- move HUD texture/font/layout resolution and caches behind a shared service
- make indoor and outdoor call that service
- keep only low-level texture submission runtime-adapter-specific if necessary

Acceptance:
- no shared overlay renderer depends on `OutdoorGameView`
- indoor and outdoor use one HUD asset/font/layout implementation

### Wave 2. Finish Shared Overlay/Screen Rendering

Goal:
- all YML-driven screens and stacked overlays render through one shared stack

Do:
- unify menu/rest/dialogue/chest/corpse/character/spellbook/inventory rendering
- move scene-specific orchestration down into small adapters only

Acceptance:
- same rendering path is used indoors and outdoors for all shared screens
- no debug-only indoor fallback remains for screens that already exist outdoors

### Wave 3. Finish Shared Overlay/Input Control Flow

Goal:
- shared overlays behave the same regardless of scene kind

Do:
- centralize input debounce/latch and state transition logic
- keep only world-touching actions behind runtime adapters

Acceptance:
- chest/dialogue/menus/rest/spellbook/character input semantics are identical
  indoors and outdoors

### Wave 4. Introduce Shared World Query Interfaces

Goal:
- allow gameplay systems to stop depending on concrete outdoor/indoor types

Do:
- define runtime-neutral interfaces for:
  - raycast/picking
  - LOS
  - projectile collision
  - actor enumeration
  - surface classification
- wire indoor and outdoor implementations

Acceptance:
- shared gameplay systems do not need `OutdoorWorldRuntime` or
  `IndoorWorldRuntime` concrete ownership

### Wave 5. Unify Spell, Projectile, and Effect Runtime

Goal:
- one spell/projectile/effect stack

Do:
- move projectile/effect ownership into shared services
- keep only geometry collision and placement adapters runtime-specific

Acceptance:
- the same spell and projectile code path runs in both scenes
- no indoor/outdoor duplicate spell logic exists except geometry queries

### Wave 6. Unify Billboard Presentation

Goal:
- stop maintaining separate actor/deco/sprite draw logic where not required

Do:
- create a shared billboard renderer/presenter
- separate:
  - instance collection and culling
  - actual draw submission and presentation rules

Acceptance:
- actor/deco/sprite rendering style is identical by default indoors and outdoors
- only instance collection/culling differs by scene kind

### Wave 7. Cleanup Scene Views

Goal:
- make views thin

Do:
- shrink `OutdoorGameView`
- shrink `IndoorGameView`
- keep renderer resources, per-scene view glue, and input forwarding there
- move shared logic out

Acceptance:
- views are adapters, not owners of large gameplay/UI subsystems

## File/Module Direction

These are the expected ownership directions, not mandatory exact filenames.

### Shared targets

- `game/ui/`
  - HUD service
  - overlay renderers
  - overlay controllers
  - shared screen renderers
- `game/gameplay/`
  - dialogue/service/item-transfer/shared interaction semantics
  - spell/effect orchestration
- `game/render/`
  - shared billboard presentation
  - shared particle presentation
  - shared decal helpers where possible
- `game/scene/`
  - runtime-neutral interfaces for world query and scene services

### Outdoor adapters

- `game/outdoor/`
  - terrain/bmodel queries
  - outdoor runtime state extraction
  - outdoor instance visibility collection

### Indoor adapters

- `game/indoor/`
  - sector/portal/floor/face queries
  - indoor runtime state extraction
  - indoor instance visibility collection

## Regression Strategy

This refactor only works if regressions stay visible.

Required regression coverage:

- indoor and outdoor chest UI semantics
- indoor and outdoor dialogue UI semantics
- shared screen transitions
- shared hotkey behavior
- spellbook and inventory interactions
- quick-cast semantics
- projectile behavior parity where scene geometry is not the reason for
  difference
- save/load round-trip across indoor and outdoor

Diagnostics should be scene-neutral where possible. A test should assert shared
behavior once, then run it against both indoor and outdoor adapters.

## Acceptance Criteria

This plan is complete when all of these are true:

- there is one shared HUD infrastructure path
- there is one shared stacked-screen/UI path
- there is one shared dialogue/chest/shop/inventory/spellbook path
- there is one shared spell/projectile/effect path
- actor/deco/sprite billboard presentation is shared by default
- indoor and outdoor only differ at the world query / geometry / visibility
  seams
- views and renderers no longer own broad gameplay or UI behavior

## Immediate Next Refactor Order

The recommended order from this point:

1. shared HUD infrastructure extraction
2. shared menu/rest/dialogue/chest/corpse/character/spellbook rendering
3. shared overlay input/control flow cleanup
4. shared world query interface introduction
5. shared projectile/effect service extraction
6. shared billboard presentation extraction
7. shrink indoor/outdoor view ownership

If the work starts diverging from this order, the reason should be explicit in
the commit or handoff note.
