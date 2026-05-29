# Level Editor Authoring Inventory

## Purpose

This document answers a specific planning question:

What must an OpenYAMM editor support in order to create a complete MM-style
level package, and what additional authoring systems should a successor need on
top of the original game while still feeling like Might and Magic rather than a
different game?

This is based on a cross-check of:

- current OpenYAMM runtime structs and loaders
- MMExtension editor scripts and readme
- `mm_mapview2` map structure references
- OpenEnroth snapshot/reference structs
- the current OpenYAMM event and map table systems

The goal is not to reproduce every low-level legacy blob as manual editor UI.
The goal is to distinguish:

- authored source data
- derived/compiled data
- runtime/save state
- successor-only additions worth supporting

## Evidence Sources

Primary sources used:

- [MMEditor Readme.txt](</home/pjasicek/github/OpenYAMM/reference/MMExtension/MMEditor Readme.txt>)
- [Editor Props.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Props.lua>)
- [Editor Read Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Read Data.lua>)
- [Editor Odm Read.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Read.lua>)
- [Editor Odm Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Data.lua>)
- [Editor Ground.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Ground.lua>)
- [Editor Import.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Import.lua>)
- [Editor Export.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Export.lua>)
- [Editor Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Data.lua>)
- [Editor GUI.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor GUI.lua>)
- [Editor BSP.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor BSP.lua>)
- [ConstAndBits.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Core/ConstAndBits.lua>)
- [01 common structs.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Structs/01%20common%20structs.lua>)
- [odmmap.h](</home/pjasicek/github/OpenYAMM/reference/mm_mapview2-master/include/odmmap.h>)
- [blvmap.h](</home/pjasicek/github/OpenYAMM/reference/mm_mapview2-master/include/blvmap.h>)
- [CompositeSnapshots.h](</home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Snapshots/CompositeSnapshots.h>)
- [OutdoorMapData.h](</home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorMapData.h>)
- [IndoorMapData.h](</home/pjasicek/github/OpenYAMM/game/indoor/IndoorMapData.h>)
- [MapDeltaData.h](</home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h>)
- [MapStats.h](</home/pjasicek/github/OpenYAMM/game/tables/MapStats.h>)
- [EvtProgram.h](</home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h>)

## Executive Summary

The original content model was already broader than just:

- geometry
- monsters
- chests

To create a full original-style level package, the editor or editor-adjacent
toolchain must cover at least these authoring domains:

- indoor or outdoor base geometry
- terrain, tilesets, and model placement for outdoors
- rooms, portals, BSP-ish visibility, lights, and doors for indoors
- facet metadata and trigger flags
- decoration/sprite placement and sprite trigger metadata
- monster and item spawn anchors
- initial dynamic map state:
  - monsters
  - items / sprite objects
  - chests
  - doors/mechanisms
  - local variables
- map-wide environment/header settings
- map-local scripts and script links
- mapstats-style sidecar metadata:
  - travel
  - encounters
  - treasure level
  - music / environment

The original authoring workflow was not purely in-engine:

- indoor geometry was expected to come from external 3D modelling software and
  be imported
- outdoor models also came from external models
- the editor then layered MM-specific meaning on top

That same split is still the right direction for OpenYAMM.

The most important design conclusion is:

- the editor must author meaning, not just shape

That means:

- geometry import alone is insufficient
- runtime binary formats alone are insufficient
- a complete editor must cover semantic map authoring, scripting links,
  mechanism wiring, and environment/presentation controls

## Original Authoring Inventory

## 1. Shared Across Indoor And Outdoor

These concepts exist in both indoor and outdoor content in one form or another:

- placed decoration/sprite entities with:
  - decoration type
  - transform / facing
  - event ids
  - variable ids
  - special trigger ids
- spawn anchors
- facet interaction metadata:
  - event ids
  - trigger modes
  - special flags
- local event variables
- initial dynamic content:
  - monsters
  - objects / sprite objects
  - chests
- map-local script binding via event ids

### 1.1 Dynamic Monster Authoring

To recreate the original game fully, the editor/toolchain must support much
more than just monster placement.

The original authored monster surface includes:

- monster id / type
- display/name binding:
  - `NameId`
  - optional `NPC_ID`
- transform:
  - position
  - direction
  - guard position
  - guard radius
- relationship / behavior setup:
  - group
  - hostile
  - ally
  - `AIType`
  - `HostileType`
  - `MoveType`
  - move speed
  - fly
  - no-flee
- visibility / map-state flags:
  - invisible
  - show-on-map
  - on-alert-map
- combat setup:
  - hit points
  - level
  - armor class
  - experience
  - melee/ranged attack payload
  - missiles
  - attack recovery
  - spell loadout and spell chances
- resistances:
  - physical
  - elemental
  - mind/body/spirit style resistances
  - light/dark in MM7/MM8
- treasure payload:
  - gold dice
  - item chance
  - item level
  - item type
  - carried item
- special monster behaviors:
  - shot count
  - summon-monster variants
  - explode-on-death variants

This is a real authoring surface, not just runtime implementation detail.

### 1.2 Dynamic Sprite-Object / Item-Object Authoring

The original content model also includes map sprite-objects that are more than
static decorations and more than chest entries.

These objects carry an authored or script-driven surface including:

- visual/object type
- transform:
  - position
  - direction
  - look angle
- movement payload:
  - velocity
- lifetime payload:
  - age
  - max age
  - temporary flag
- rendering/interaction flags:
  - visible
  - dropped-by-player
  - ignore-range
  - no-z-buffer
  - skip-a-frame
  - attach-to-head
  - missile
  - removed
- room binding
- light multiplier
- item payload
- spell / trap payload

This matters because a complete level package includes not only static map
objects, but also authored initial object state and script-driven object
behavior.

### 1.3 Chest Authoring Is Richer Than A Single “Chest” Checkbox

Chest authoring includes at least:

- chest picture/id
- trapped flag
- identified flag
- full item contents
- item grid/inventory layout
- per-item item state:
  - identified
  - broken
  - hardened
  - stolen

So an editor needs real chest content tooling, not only a chest placement marker
or a single “loot list” text box.

### 1.4 Randomized And Template-Based Content Authoring

Original-style content authoring is not only literal placement of final objects.
It also includes authored rules that resolve into runtime content.

That means the editor/toolchain must support authored expressions like:

- chest content templates:
  - exact items
  - random items by treasure level
  - random items constrained by item class
  - mixed exact and random contents
  - gold ranges
  - gold split across multiple stacks
- spawn templates:
  - mapstats encounter slot references
  - monster group aliases like `m1`, `m2`, `m3`, `m1a`
  - item spawn aliases like `i1` through `i7`
  - group and alert-map coupling
- monster payload templates:
  - carried item
  - random treasure payload
  - hostility / group presets
- lock / trap / refill-style map tuning:
  - lock difficulty
  - trap strength
  - refill cadence

For a production-grade editor proposal, this is a major point:

- authors need to express content-generation intent, not only final literal
  instances

If the proposal only describes direct object property editing and not these
template/distribution mechanics, it will still be incomplete.

In OpenYAMM terms this currently spans:

- [OutdoorMapData.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorMapData.h)
- [IndoorMapData.h](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorMapData.h)
- [MapDeltaData.h](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h)

## 2. Outdoor Authored Content

What original outdoor authoring actually covered:

### 2.1 Base Outdoor Map Header

Authored outdoor header/environment data includes:

- sky / minimap naming
- tileset groups
- flight ceiling
- fog enable and fog distances
- precipitation state:
  - rain
  - snow
- MM8 map-extra flags:
  - `Foggy`
  - `Underwater`
  - `RedFog`
  - `NoTerrain`
  - `AlwaysDark`
  - `AlwaysLight`
  - `AlwaysFoggy`

Evidence:

- [Editor Props.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Props.lua>)
- [Editor Odm Read.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Read.lua>)
- [Editor Odm Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Data.lua>)
- [MapExtra](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Structs/01%20common%20structs.lua>)

### 2.2 Outdoor Terrain

Authored outdoor terrain includes:

- heightmap sculpting
- terrain tile painting
- terrain tile smoothing / transition logic
- terrain semantic flags in `AMAP`
  - confirmed:
    - burn
    - water
  - likely more legacy semantics beyond the currently confirmed bits

The original editor had explicit ground tools for:

- raise/lower
- flatten
- smooth
- spline-like brush shaping
- tile painting / autotiling

Evidence:

- [Editor Ground.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Ground.lua>)

### 2.3 Outdoor Models

Authored outdoor static structures include:

- model placement
- imported geometry
- per-model facet sets
- model naming / object naming
- save/load of model chunks

The original editor supported:

- importing outdoor map geometry from `.obj`
- importing individual outdoor models
- saving models in `MDT` so setup is preserved

The readme explicitly says `MDT` preserves setup such as:

- facet bits
- event numbers
- water-flow-type setup

Evidence:

- [MMEditor Readme.txt](</home/pjasicek/github/OpenYAMM/reference/MMExtension/MMEditor Readme.txt>)
- [Editor Odm Read.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Read.lua>)
- [Editor Odm Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Odm Data.lua>)

### 2.4 Outdoor Facets

Outdoor facets are not just geometry.
They carry authored gameplay and presentation metadata.

Original outdoor facet authoring includes:

- texture assignment
- texture UV offset / alignment data
- event / cog ids
- trigger mode
- facet bits:
  - `IsWater`
  - `Invisible`
  - `AnimatedTFT`
  - `AlternativeSound`
  - `IsSky`
  - `TriggerByClick`
  - `TriggerByStep`
  - `Untouchable`
  - `IsLava`
  - MM7+:
    - `IsSecret`
    - `ScrollUp`
    - `ScrollDown`
    - `ScrollLeft`
    - `ScrollRight`
    - `AlignTop`
    - `AlignBottom`
    - `AlignLeft`
    - `AlignRight`

OpenYAMM currently stores the equivalent outdoor face data in
[OutdoorMapData.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorMapData.h).

### 2.5 Outdoor Sprites / Decorations / Event Triggers

The original outdoor editor treated placed sprites/decorations as authored map
content with their own properties.

Authorable sprite properties include:

- decoration name / type
- transform
- direction
- index/id
- event id
- trigger radius
- trigger by touch
- trigger by monster
- trigger by object
- show on map
- chest marker
- visibility
- ship / obelisk-chest special bit depending on game

These are important because a lot of map interactivity is sprite-based rather
than face-based.

Original content also already had authored sprite-light behavior.
In MM7/MM8 this is partly driven through sprite/decoration definitions rather
than a separate freeform light actor.

Evidence:

- [Editor Props.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Props.lua>)
- [Editor Read Data.lua](</home/pjasicek/github/OpenYAMM/reference/MMExtension/Scripts/Global/Editor Read Data.lua>)

### 2.6 Outdoor Lights

Outdoor authoring includes explicit placed lights.

Authorable light properties include:

- position
- radius
- index / id
- off bit
- RGB
- halo/type

This matters because original content already had authored local light sources,
even if the runtime lighting model was simple.

### 2.7 Outdoor Spawns

Outdoor spawns are authored anchors, not pure runtime generation.

Authorable spawn properties include:

- position
- radius
- kind
  - monster groups / single monsters by mapstats slot
  - item treasure-level drops
- group
- alert-map bit

The readme also documents the original spawn shorthand:

- `m1`, `m2`, `m3`
- `m1a`, `m1b`, `m1c`
- `i1` through `i7`

This means an editor needs first-class spawn authoring, not just monster
placement.

### 2.8 Outdoor Dynamic Initial State

Outdoor initial dynamic state comes from the `DDM`-style companion layer and
includes:

- location state:
  - respawn count
  - last respawn day
  - reputation
  - alert status
- face attribute overrides
- decoration flags
- actors / monsters with the full monster-authored property surface described
  above
- sprite objects / item-like runtime objects with movement/lifetime/item/spell
  payload
- chests
- local map variables
- local decor variables
- map extra / environment-time fields

This is what the `.scene.yml` migration is replacing for outdoor authored
initial state.

## 3. Indoor Authored Content

Indoor maps are materially richer in structural authoring than outdoor maps.

### 3.1 Indoor Geometry

Indoor authored base geometry includes:

- vertices
- facets
- facet UVs
- facet texture names
- facet type
- room assignment
- room-behind assignment
- portal classification

Current OpenYAMM storage:

- [IndoorMapData.h](/home/pjasicek/github/OpenYAMM/game/indoor/IndoorMapData.h)

### 3.2 Rooms

Indoor rooms are explicit authored content, not just derived render buckets.

Room authoring includes:

- room/facet membership
- darkness
- MM8 EAX environment
- portal relations
- BSP / draw ordering data
- room-local light and sprite associations

The original editor treated rooms as a first-class concept and even supported:

- import-as-rooms workflow from `.obj`
- manual portals using `_Portal_`
- automatic portal creation when rooms share boundaries

That means an indoor editor must have a real room model, not only a loose mesh
scene.

### 3.3 Portals And Visibility Structure

Indoor authoring includes:

- portal facets
- room-behind links
- BSP or BSP-like visibility structure
- outlines for automap / edge visualization

Important point:

- BSP and outline data should be compiler-managed where possible
- but the editor must still expose the inputs and be able to visualize and
  regenerate them

### 3.4 Indoor Doors / Mechanisms

Indoor doors are a major authored system.

The original editor exposed:

- door id
- move length
- open speed / close speed
- direction vector
- no sound
- start state
- close-portal behavior
- vertex filter
- vertex filter parameters

It also had door-aware facet metadata:

- `MovedByDoor`
- `DoorStaticBmp`
- `MultiDoor`
- facet/door reconstruction and bounds updates

This is not cosmetic.
It is a real authored mechanism system coupled to geometry movement.

### 3.5 Indoor Lights

Indoor lights are richer because they also interact with rooms and room light
lists.

Authorable indoor light properties include:

- position
- radius
- RGB
- type / halo
- off state
- index / id

The editor also had explicit room-light association logic and sprite-light
updates.

### 3.6 Indoor Sprites / Decorations

Indoor sprites/decorations share the same high-level property surface as
outdoor sprite entities:

- decoration type / name
- transform
- direction
- event id
- trigger radius and modes
- visibility / map flags
- chest marker / special bits

### 3.7 Indoor Spawns

Indoor spawns are the same general authoring concept as outdoor:

- position
- radius
- kind
- group
- alert-map bit

### 3.8 Indoor Dynamic Initial State

Indoor companion data additionally includes door state and geometry-offset data.

Indoor initial dynamic state includes:

- location state
- visible outlines
- face attribute overrides
- decoration flags
- actors / monsters with the full monster-authored property surface described
  above
- sprite objects / item-like runtime objects with movement/lifetime/item/spell
  payload
- chests
- doors:
  - state
  - time since triggered
  - movement info
  - moved vertex/face/sector lists
  - texture delta offsets
  - x/y/z offset arrays
- local variables
- location time / map extra

This is why indoor `.scene.yml` will need shared sections with outdoor, but also
indoor-specific door / mechanism sections.

## 4. Script And Sidecar Authoring

A complete level package is not only map binary data.

### 4.1 Lua Map Scripts

For the successor, Lua should be the authoritative scripting layer for level and
map logic.

However, because the plan is to rewrite legacy `EVT` content 1:1 into Lua, the
editor and runtime still need to cover the same behavioral surface that `EVT`
historically covered.

Relevant legacy behavior categories from
[EvtProgram.h](/home/pjasicek/github/OpenYAMM/game/events/EvtProgram.h):

- house interaction
- map travel
- chest open
- play sound
- show movie
- texture swap
- sprite change
- damage
- snow/weather toggles
- summon monsters
- summon items
- cast spells
- set facet bit
- toggle actor flags
- toggle chest flags
- mechanism / door state changes
- timer events
- map reload / map leave hooks
- NPC topic and greeting changes
- NPC group news changes

So the scripting requirement becomes:

- Lua files are the authored source of map logic
- the engine exposes a stable Lua API that covers the full original `EVT`
  behavior surface
- scene objects, facets, sprites, doors, chests, transitions, houses, and local
  vars must be referenceable from Lua
- original event-id-driven logic can be preserved initially, but the long-term
  direction should allow named references and clearer bindings

A complete level editor ecosystem therefore needs either:

- an integrated Lua script editor

or:

- a tightly linked sidecar Lua editor with good jump-to-reference tooling

It is not enough to expose trigger ids on facets and sprites if the actual Lua
map script is painful to author or hard to connect back to the scene.

### 4.2 MapStats-Like Sidecars

`MapStats` authoring is part of a complete level package.

Current OpenYAMM [MapStats.h](/home/pjasicek/github/OpenYAMM/game/tables/MapStats.h)
already covers part of this surface, but the original authoring model was
broader.

Original `MapStats`-like authoring includes:

- map id
- display name
- file name
- reset / refill cadence:
  - reset count
  - first visit day
  - refill days
  - alert days
- treasure level
- encounter chance
- encounter 1/2/3 definitions:
  - picture
  - monster
  - difficulty
  - min/max count
- lock
- trap
- steal / perception related fields
- redbook track
- environment name
- MM7+/MM8 EAX environment
- top-level-area flag
- map-start / arrival usage
- outdoor bounds
- north/south/east/west transitions:
  - target map
  - travel days
  - direction
  - arrival coordinates

Original authoring also depended on:

- `MapStats.txt`
- `npcgroup.txt`
- object / item / monster / chest generation tables

A complete “make a level” workflow must provide editing or at least guided
integration for these sidecars.

This also means the toolchain must cover the authored entry surface for the map:

- default map start position
- transition arrival coordinates
- transition-facing / direction expectations where used

### 4.3 Dialog / House / NPC Sidecars

Level-linked content also depends on:

- house ids
- NPC ids
- greeting/topic bindings
- local strings / STR references
- map-local NPC / dialog logic

This is not all viewport authoring, but it is still part of “create the level”.

## What The Editor Must Support

This section is the practical answer.

## 1. Required 3D Authoring Surface

To build complete original-style content, the editor must support:

- 3D viewport with fly navigation
- object selection and outliner
- transform gizmos
- facet selection
- multi-select
- undo/redo
- property inspector
- import/export with external DCC tools

For indoor:

- import geometry from external mesh authoring
- room assignment
- portal authoring / portal detection
- indoor facet editing
- room properties
- door/mechanism authoring
- light placement and room-light assignment
- outline / automap preview

For outdoor:

- terrain sculpting
- terrain tile painting with transition support
- tileset assignment
- outdoor model import / placement
- outdoor facet editing
- sprite/decor placement
- light placement
- spawn placement
- outdoor map header/environment editing

## 2. Required Semantic Authoring

The editor must expose at least:

- facet bits
- sprite bits
- chest bits
- event ids
- trigger modes
- local vars links
- chest item definitions and layout
- spawn kind definitions
- monster placement plus the real monster property surface:
  - AI
  - hostility
  - attacks
  - spells
  - resistances
  - treasure
  - patrol/guard data
- item / sprite-object placement plus runtime-object payload:
  - velocity
  - lifetime
  - flags
  - spell/item/trap payload
- mechanism ids and actions
- authored randomization/template mechanics:
  - chest content templates
  - spawn aliases/templates
  - treasure-level-driven item generation
  - lock/trap/gold distribution setup

Without this, the tool would only be a geometry editor, not a level editor.

## 2.1 Required Authoring Expressions

The future proposal should treat these as first-class authoring tasks, not as
freeform text hacks:

- “4 random level-4-to-5 items”
- “1 random level-6 weapon”
- “3000-5000 gold split into 4 stacks”
- “spawn from encounter slot `m2b`”
- “monster carries one guaranteed item plus normal treasure”
- “chest is trapped and requires lock threshold X”

Some of these can compile down to legacy-compatible data or to successor-native
Lua/YAML definitions, but the authoring surface must represent them clearly.

## 3. Required Sidecar Editing Or Integration

The editor ecosystem must cover:

- local Lua map scripts
- shared/global Lua references and bindings
- mapstats / travel / encounter data
- minimap name / icon linkage
- house and NPC references

This does not all need to live in the main 3D viewport, but it must be part of
the overall authoring toolchain.

## 4. Required Compile / Rebuild Systems

Some legacy structures should not be manually authored.
The editor or build step should regenerate them.

Examples:

- outdoor `IDList` / `OMAP`
- terrain normals / normal refs
- indoor BSP
- indoor outlines
- room light/sprite membership lists
- door compiled vertex/face/offset data

This is a major architectural point:

- authors should edit intent
- tools should compile helper structures

## 5. Required Workflow / Ergonomic Tools

The original editor surface was not only data fields.
It also provided a set of practical editing operations that made map building
workable.

At minimum, a successor editor should support equivalents for:

- create / clone / delete selected objects
- move selected object to player/camera position
- land selected object on floor or terrain
- nudge objects and UVs with small and large step sizes
- select same texture
- select same object / model
- toggle between outdoor facet editing and model editing
- import full map geometry
- import a single model
- save a model chunk with its setup preserved
- test chest contents / interactables quickly
- automated door creation from selected indoor facets
- manual override of generated results
- visibility of selections, ids, and room/model membership in viewport
- import/export controls that existed in the original workflow:
  - import scale
  - ignore imported UVs
  - export rotation toggle
  - show-all-indexes editing mode
  - test-with-living-monsters mode

Without these workflow affordances, an editor can technically expose the right
data and still be much slower than the original toolchain in practice.

## 6. Required Editor Surface Decomposition

Because this document will be used as input for a production-grade editor
proposal, the proposal should not stop at “support these systems”.
It should map those systems onto concrete editor surfaces.

At minimum, the proposal should define dedicated or clearly grouped surfaces for:

- main 3D viewport
- scene outliner / selection tree
- property inspector
- terrain sculpt/paint panel
- indoor room/portal panel
- facet editor
- door/mechanism editor
- sprite/decor editor
- light editor
- spawn/encounter editor
- monster editor
- chest/loot editor
- environment/map-header editor
- mapstats / travel / transition editor
- Lua script/editor binding browser
- validation/error panel
- asset browser/import panel
- playtest/simulate controls

For the more detail-oriented authoring tasks, the proposal should also define
specialized editing views or dialogs where needed:

- chest content editor:
  - exact items
  - random item generators
  - gold distribution
  - trap/lock settings
- monster editor:
  - combat stats
  - spells
  - resistances
  - AI/hostility/group data
  - treasure payload
- spawn editor:
  - alias-driven spawn definitions
  - encounter-slot references
  - radius/group/alert settings
- environment editor:
  - weather
  - fog
  - sky
  - ceiling
  - ambient/environment profile

If the proposal does not define which tasks live in which surfaces, it will be
too abstract to implement cleanly.

## Original-Era Things Easy To Miss

These are the easiest systems to forget when planning a replacement editor.

### 1. Facet Trigger Surface Is Larger Than It Looks

Facet authoring is not only:

- texture
- event id

It also includes:

- step / click / monster / object triggers
- secret flags
- untouchable flags
- water / lava / sky flags
- animated texture flags
- texture scroll flags
- D3D alignment flags
- door-related flags

### 2. Sprite/Event-Trigger Authoring Matters

A large amount of authored interactivity is sprite-based, not only face-based.

If the editor cannot place and configure trigger sprites well, it cannot
comfortably recreate original content.

### 3. Room / Portal / Door Workflow Is Core Indoors

Indoors are not just imported meshes.
The room and door structure is central to:

- visibility
- minimap
- interaction
- movement
- authoring sanity

### 4. Outdoor Header Flags Matter More Than They Look

Outdoor maps use authored environment flags beyond simple sky selection:

- fog
- red fog
- underwater
- rain / snow
- no terrain
- always dark
- always light
- always foggy
- ceiling

These need a first-class home in the editor.

### 5. Treasure And Spawn Authoring Are Table-Coupled

Original content often authored:

- a spawn type
- a treasure level
- a mapstats encounter slot

rather than hand-placing every exact final monster/item.

An editor needs to support those abstractions rather than forcing everything to
be literal.

The same applies to monsters and chests:

- monster hostility / AI setup
- monster treasure payload
- chest lock/trap/content tuning

are all part of the original authored level package, not separate “system
designer only” concerns.

### 6. Sprite Lights And Animated Presentation Already Existed

The original authoring model already used:

- local lights
- sprite lights
- animated textures
- weather flags
- sound triggers
- movies

So successor-era visual improvements are not alien to the content model.
They are an extension of existing authored presentation, not a departure from
the game’s feel.

### 7. There Is No Strong Evidence Of A Rich Standalone Particle Authoring Model

This is important.

The original toolchain appears to rely on:

- animated textures
- sprites
- sprite lights
- weather flags
- spell/projectile systems
- sound

more than on a modern explicit particle-system editor.

There is evidence for particle trail/color data on spell or sprite-object style
runtime objects, but that is not the same thing as map-authored particle
emitters.

So if OpenYAMM wants particles/VFX authoring, that is a real successor addition,
not something the original pipeline already solved cleanly.

## Derived Versus Authored

This separation should guide the future editor.

Authored:

- geometry inputs
- terrain shape and paint
- room membership
- portal intent
- facet semantics
- lights
- sprites / entities
- spawns
- chests
- monsters
- sprite objects / runtime item objects as initial scene content
- map header / environment settings
- scripts and sidecars

Derived / compiled:

- outdoor `IDList` / `OMAP`
- terrain normals
- BSP / outline structures
- compiled door geometry-offset payloads
- room light/sprite membership tables
- runtime collision caches

Runtime / save state:

- dead monsters
- looted chests
- current door progress
- revealed automap
- temporary objects
- visit time

This is exactly why `scene.yml` plus compiled runtime data is the right
long-term model.

## Successor Requirements

The following is a deliberate three-pass successor analysis.

The rule is:

- stay in the Might and Magic family
- improve fidelity, clarity, and authoring power
- do not turn the game into a different genre or aesthetic

## Pass 1: Rendering And Presentation Additions

These are the clearest successor-era additions that still fit MM.

### Must Have

- semantic materials instead of texture-name conventions
- proper per-surface UV transform tools:
  - offset
  - rotation
  - scale
- richer local lighting:
  - color
  - intensity
  - attenuation
  - flicker / pulse presets
- better fog controls:
  - density / distance
  - color
  - zone or profile support
- shadow support for key scene elements
- improved sky and weather profiles
- explicit water/lava/flow material behavior
- decals / stain / scorch / puddle overlays
- sprite-light and emissive control as first-class authored data

### Good Fit For MM Feel

- restrained postprocessing:
  - color grading
  - bloom
  - light vignette
  - underwater tint
- better animated materials:
  - fountains
  - lava
  - slime
  - magical panels
- authored VFX emitters:
  - torch smoke
  - magic mist
  - waterfall spray
  - embers

### Should Be Optional

- 3D actors instead of billboards

This can fit the successor, but it should remain optional because:

- the overall game feel can survive with sprites
- authoring burden goes up sharply
- mixed sprite/3D support may be the most practical path

### Should Be Avoided As A Design Center

- physically based realism as the primary look
- heavy filmic grading
- dense post stack
- modern cinematic camera language

That would drift away from MM rather than improve it.

## Pass 2: Authoring Workflow Additions

These are the biggest quality-of-life wins for a successor editor.

### Must Have

- YAML-authored scene supplements plus compiled runtime cache
- asset import pipeline from external DCC tools
  - preferably `glTF`
- live property editing in viewport
- play-from-here / quick simulate
- validation passes with actionable errors
- object and reference search
- stable ids and named references
- prefab / reusable object groups
- robust undo/redo

### Strongly Recommended

- event / mechanism graph view
- terrain brush presets
- light / VFX preview in editor
- material preview and assignment tools
- side-by-side authored vs compiled diagnostics
- automatic rebuild of derived data
- scene-to-Lua reference browsing
- map diff friendliness:
  - stable ordering
  - stable ids
  - readable source files

### Very Useful

- hot reload of `scene.yml`
- asset browser
- reference viewer:
  - what Lua handlers reference this face
  - what mechanisms target this object
  - what mapstats row points to this map

## Pass 3: Successor Gameplay-Semantic Additions

These are not just graphical.
They are the semantic systems a successor should gain while still feeling like
MM.

### Must Have

- generic mechanism system for both indoor and outdoor
- named triggers and targets
- mechanism groups and links
- explicit trigger volumes / regions
- explicit environment zones:
  - underwater
  - poisonous
  - hot
  - dark
  - sacred / magical
- better encounter/spawn authoring:
  - zones
  - conditions
  - population sets

### Strong MM-Compatible Improvements

- secret / perception markers as named authored semantics
- better house / transition markers
- explicit map start / arrival marker authoring in the viewport
- audio emitters / ambient loops
- rest danger and encounter tuning by area
- authored patrol / guard positions for NPCs and monsters
- richer chest / loot template authoring
- quest marker / world-state variations controlled by qbits or map vars

### Good But Optional

- cutscene / camera marker support
- scripted scene sequences
- authored cinematic spell/VFX cues

These can help, but they should not dominate the tool or the game.

## What The Successor Editor Should Not Overbuild

To stay true to MM’s feel, avoid making the editor revolve around:

- giant generic node graphs for everything
- physically based material complexity as the default
- extremely granular cinematic sequencing
- multiplayer/network assumptions
- systemic destruction
- large-scale procedural world generation

That would spend complexity on the wrong axis.

## Recommended Final Split

For OpenYAMM, the clean future target is:

- `BLV` / `ODM` or their equivalents remain low-level geometry/runtime scene
  containers
- shared `.scene.yml` authoring concept exists for both indoor and outdoor
- derived runtime/helper data is compiled, not hand-authored
- editor focuses on:
  - shape import and assembly
  - semantic authoring
  - event/mechanism wiring
  - environment/presentation tuning
  - validation and preview

In one sentence:

the editor should author the full map package, not just the mesh.

## Practical Minimum For “Can Build The Whole Original Game”

If the question is “what is the minimum feature set required to recreate all
original-style levels?”, the answer is:

- indoor mesh import and room/portal workflow
- outdoor terrain sculpt and tile paint
- model import and placement
- facet property editing
- sprite/decor editing
- light editing
- spawn editing
- monster editing
- item/sprite-object editing
- chest editing
- door/mechanism editing indoors
- map header/environment editing
- mapstats/travel/encounter editing
- Lua script editing or tight sidecar integration
- compile/regenerate helper structures
- playtest/validation loop

Anything less than that will only recreate part of the original authoring
surface.
