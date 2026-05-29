# World And Mod Architecture

This document defines the target architecture for running multiple Might and Magic-like worlds on OpenYAMM without
rewriting the engine. OpenYAMM remains the runtime. MMerge-style global content is treated as the flat engine/base
content layer, and worlds/mods extend that layer.

The first concrete use case is an MM Merge-style setup with MM8, MM7, and MM6 worlds.

## Core Vision

OpenYAMM is the engine. A world is content.

The engine should not contain hardcoded branches for MM6, MM7, MM8, or future custom worlds. It should understand:

- one world is currently active;
- some engine/base content is global and shared by all worlds;
- some content is owned by one world;
- mods can add worlds, append global data, or connect worlds.

The existing game engine, renderer, UI systems, event runtime, combat, inventory, party state, map runtime, save/load,
and editor systems remain the base. World support is an incremental content/package layer around those systems, not a
new engine.

## Terms

- Engine/base: OpenYAMM code plus flat MMerge global data shared by all worlds.
- Global content: data shared across all mounted worlds.
- World: a playable geography/story package such as MM8/Jadame, MM7/Antagarich, MM6/Enroth, or a new custom world.
- Mod: an optional package that appends global content and/or adds worlds.
- Active world: the world currently used for map loading, map-local events, local quests, and local travel.

## Package Shape

The desired development asset layout is:

```text
assets_dev/
  engine/
    ui/
    scripts/common/
    data_tables/
    audio/
    icons/
    sprites/
    rendering/
    textures/
    fonts/

  worlds/
    mm8/
      world.yml
      data_tables/
      maps/
      events/
      quests/
      npcs/
      houses/
      travel/
      monsters/
      assets/

    mm7/
      world.yml
      data_tables/
      maps/
      events/
      quests/
      npcs/
      houses/
      travel/
      monsters/
      assets/

    mm6/
      world.yml
      data_tables/
      maps/
      events/
      quests/
      npcs/
      houses/
      travel/
      monsters/
      assets/

  mods/
    some_mod/
      mod.yml
      worlds/
      overrides/
```

This layout is intentionally flat. `assets_dev/engine/` is the MMerge-compatible base layer. Worlds own map-local
content and local art/audio, while mods append to the base or add worlds.

## Current MMerge Flat Import Status

The following MMerge reference tables are treated as base-global and should be loaded from `assets_dev/engine/` rather
than through active-world `Data/...` shadowing:

- item, random item, standard enchant, special enchant, hostile, spell text, skill/class/stat text, potion, merchant,
  global text, credits, launcher, intro, scroll, quests, autonotes, awards, history, and transitions;
- NPC dialogue registries: `npc.txt`, `npc_greet.txt`, `npc_news.txt`, `npc_topic.txt`, `npc_topic_text.txt`, and
  `english/npc_group.txt`;
- engine-authored shared support tables such as class skills, class multipliers, character/paperdoll data, spell
  mechanics, object list, icon/portrait frames, portrait FX, face animations, Arcomage rules, and spell FX.

The remaining MMerge tables fall into three categories:

- Direct import after schema check: tables whose MMerge layout already matches an existing loader or only needs a
  mechanical column rename.
- Export/import from binary registries: `SFT`, `IFT`, `TFT`, `PFT`, overlays, decoration lists, tile data, object
  lists, and monster lists should use the fully generated MMerge `DataFiles/*.bin` sources when available, not the
  older baseline BINs embedded in `mmmerge.T.lod`.
- New runtime support needed: continent settings, character selection/voices, bolster settings, transport indexes and
  locations, house rules/exits/movies, teacher topics/autonotes, news topic filters, race/class extras, potion/reagent
  settings, town portal switching, and other MMerge-specific control tables need explicit loaders and gameplay logic
  before they become authoritative.

## Mounting Model

Runtime loading should be based on deterministic package layers:

```text
engine content
mounted world packages
mod overlays
active world alias
```

Existing gameplay code should keep using the normal asset and data lookup systems where possible. The mounting layer
decides which package answers the lookup.

The active world can expose a compatibility alias for legacy-style lookups:

```text
world/mm6/data_tables/MapStats.txt  -> namespaced MM6 map stats
world/mm8/data_tables/MapStats.txt  -> namespaced MM8 map stats
active/data_tables/MapStats.txt     -> current active world's map stats
```

This avoids rewriting the engine around new data APIs all at once.

## Identity And Namespacing

Raw MM6/MM7/MM8 ids must not become global truth. They are import aliases.

Canonical ids should be namespaced:

```text
item.longsword
spell.firebolt
skill.sword
class.knight
portrait.mm8.01

world.mm6.map.oute3
world.mm7.map.7out01
world.mm8.map.out01

world.mm6.monster.goblin
world.mm7.monster.goblin
world.mm8.monster.goblin

base.merge.quest.verdant
```

Imported legacy ids should map to canonical ids:

```text
mm6 monster id 123 -> world.mm6.monster.goblin
mm8 item id 45     -> item.longsword
```

This allows existing table formats to remain useful while preventing collisions between worlds.

## Data Scope Inventory

### Base Global

These are shared by all worlds:

- party roster and active party;
- character inventory contents;
- item definitions;
- item enchantments, materials, bonuses, and artifact/relic metadata;
- skills;
- spells and spell effects;
- classes and races, with world-specific availability filters;
- character portraits and paperdolls;
- shared UI, menus, HUD layouts, fonts, and common icons;
- common audio and video assets that are not tied to a world;
- core formulas for combat, recovery, inventory, character progression, and spell behavior;
- base-level quest/metaquest state;
- the merged QBit journal registry (`quests.txt`);
- merged journal/autonote/history/transition/NPC dialogue registries when running the MMerge-style base;
- declared QBit ownership ranges for mounted worlds and mods;
- cross-world travel unlocks;
- base difficulty and bolster profile;
- save metadata, base id, active world id, and mounted worlds.

Items should be global. A party can carry items between worlds, and shops, monsters, quests, and treasure tables should
reference one canonical item repository. Imported MM6/MM7/MM8 item ids should be remapped into that repository.

Spells, skills, classes, races, portraits, menus, and UI should also be global unless a mod explicitly overrides
them. Availability can still be world-specific.

### World Specific

These belong inside a world package:

- maps;
- map geometry and scene data;
- map-local event scripts;
- world-local quest/story metadata that has not been promoted into the shared base registry;
- map-local event variables;
- world-local autonotes, awards, history text, NPC rows, and NPC dialogue only when a world/mod intentionally keeps
  them out of the flat MMerge base tables;
- houses, shops, guilds, temples, taverns, trainers, and hirelings;
- local shop inventories and treasure placement;
- outdoor edge travel;
- local town portal destinations;
- local Lloyd/Dimension Door destination rules;
- death and respawn maps;
- loading screens;
- sky, water, weather, lighting, and map presentation defaults;
- local music;
- local reputation behavior;
- monsters and monster placement;
- monster sprites, billboards, sounds, and animation metadata.

Monsters should be world-specific by default. For example, an MM6 goblin and an MM8 goblin may share a display name but
should not need to share stats, ids, art, placement assumptions, or progression rules.

Sound ids follow the same ownership model. Shared UI, player, spell, movement, and common combat sounds live in the
engine sound scope. Monster and other world-owned sounds live in the active world's sound scope. The same numeric sound
id can therefore exist in `engine`, `mm6`, `mm7`, and `mm8`; duplicates are errors only within one scope.

### Base Specific

These belong to the engine/base layer that connects worlds:

- the list of mounted worlds;
- the list of worlds available at new game start;
- cross-world travel routes and unlock rules;
- base-level dimension door rules;
- world completion predicates;
- metaquests that observe multiple worlds;
- base difficulty profiles, including "normal" or "increased" destination difficulty;
- global table overrides needed to make mounted worlds coexist;
- explicit import and id remap manifests.

An MM Merge-like Verdant quest belongs to the shared base, not to MM6, MM7, or MM8 individually.

QBits are global party/save state. World and mod packages may introduce new QBits, but they must reserve explicit
ranges and merge their visible quest-note rows into the shared QBit journal registry. For example, a custom world can
reserve `10000..10999` and provide quest-note rows in that range. Duplicate QBit quest rows across mounted packages
should be treated as data errors unless a mod override explicitly replaces the row.

### Mod Overlay

A mod overlay can:

- add a new world;
- patch global tables;
- patch one world's local data;
- replace or add assets;
- add quests, NPCs, houses, monsters, or maps;
- add cross-world travel routes;
- add localization;
- rebalance items, monsters, spells, or difficulty.

Mod overlays should be explicit and deterministic. They should not silently mask broken authoritative data.

## Runtime Architecture

World support should be implemented as small systems around the existing engine:

```text
BaseWorldManager
  mountedWorlds
  activeWorldId
  crossWorldTravel
  metaQuestState

WorldRegistry
  world definitions
  start maps
  death maps
  loading screens
  presentation settings
  local travel definitions

GameDataRepository
  global tables
  active world tables
  mod overrides
  legacy id alias maps

AssetFileSystem
  mounted package layers
  namespaced asset lookup
  active world alias

TravelService
  map transitions
  world transitions
  outdoor edge travel
  boats and stables
  town portal
  dimension door
  death respawn
```

The existing gameplay systems should generally keep depending on `GameDataRepository`, `AssetFileSystem`, the current
map runtime, and shared gameplay services. The new layer supplies the active world context.

## World Definition

A world manifest should describe how a world is loaded:

```yaml
id: mm6
name: Enroth
sourceGame: mm6

start:
  map: world.mm6.map.oute3
  x: 0
  y: 0
  z: 0
  direction: 0
  introMovie: 6intro

tables:
  mapStats: data_tables/MapStats.txt
  monsters: data_tables/Monsters.txt
  quests: data_tables/Quests.txt
  autonotes: data_tables/Autonotes.txt
  houses: data_tables/2DEvents.txt

travel:
  outdoor: travel/OutdoorTravels.txt
  townPortal: travel/TownPortal.txt
  deathMap: world.mm6.map.outc2

assets:
  maps: maps/
  sprites: assets/sprites/
  bitmaps: assets/bitmaps/
  icons: assets/icons/
```

MM8 should use the same mechanism as MM6 and MM7. It is the first supported world, not a permanent hardcoded special
case.

## Base Definition

A MMerge-style flat base should describe mounted worlds and shared rules. For now this should live in the engine/base
content layer or a small base manifest, not in a separate `assets_dev/campaigns/*` package:

```yaml
id: merge
name: World of Enroth

global:
  items: global/items.txt
  spells: global/spells.txt
  skills: global/skills.txt
  classes: global/classes.txt
  races: global/races.txt

worlds:
  - mm8
  - mm7
  - mm6

startWorlds:
  - mm8
  - mm7
  - mm6

crossWorldTravel:
  rules: cross_world_travel/routes.txt

metaquests:
  - metaquests/verdant.yml

difficulty:
  profiles:
    - normal
    - increased
```

The shared engine/base layer owns the logic that lets the player start in one world and later travel to another.

## Save Model

Save data must be base-aware and world-aware:

```yaml
baseId: mmerge
activeWorldId: mm6
activeMapId: world.mm6.map.oute3

party:
  characters: ...
  inventory: ...
  spells: ...
  skills: ...

globalState:
  baseVars: ...
  metaQuests: ...
  unlockedWorldTravel: ...
  difficulty: normal

worldState:
  mm6:
    questBits: ...
    eventVars: ...
    mapSnapshots: ...
    completed: false

  mm7:
    questBits: ...
    eventVars: ...
    mapSnapshots: ...

  mm8:
    questBits: ...
    eventVars: ...
    mapSnapshots: ...
```

The party is global. Map runtime snapshots, quest bits, and event variables are world-scoped unless explicitly declared
engine-global.

Map runtime state should be keyed by canonical map id, not raw filename.

## New Game Flow

New game startup should be:

```text
select base
select starting world from available worlds
load engine/base global content
mount selected world
show shared character creation UI
filter races, classes, portraits, and party options by world/mod rules
create global party
enter selected world's start map
```

The UI remains the OpenYAMM/MM8-style UI unless a mod explicitly overrides it.

## World Travel

Cross-world travel should be a normal game service:

```cpp
travelTo(WorldId worldId, MapId mapId, EntryPoint entryPoint)
```

The service should:

- snapshot the current map runtime;
- save current world-local variables;
- switch `activeWorldId`;
- activate the target world's package alias;
- load the target map;
- restore or create the target map runtime;
- apply base difficulty and bolster rules.

"Travel to MM6 on increased difficulty" should be represented as a base travel transition with a destination
difficulty profile, not as a one-off script hack.

## MM6 Import Reference From MMerge

The local MMerge references are:

- `reference/mmerge_data_forus/`: exported LOD contents and generated/merged table data.
- `reference/mmmerge/`: MMerge scripts and repo history.
- `reference/mmext-scripts/Decompiled_Scripts/`: GrayFace decompiled MM6/MM7/MM8 event scripts. Treat these as
  semi-authoritative behavior references for original game event flow. The per-world `txt/` folders are usually the
  easiest source for reading event control flow; the Lua files are useful when checking MMExt names and decoded
  argument intent.

Use these as behavioral and data-structure references only. Do not copy MMerge or MMExt decompiled script code into
OpenYAMM. MMerge runs by flattening MM6, MM7, and MM8 into one MM8-shaped runtime and patching the executable through
Lua and memory hooks. OpenYAMM should not reproduce that runtime shape. Import the useful data, then split it into
engine/base and world ownership.

### MM6 Source Inputs

The MM6 raw source set in `reference/mmerge_data_forus` is sufficient for a vertical slice:

- `Data/mm6.games.lod/`: MM6 map binaries, currently 15 `*.odm`/`*.ddm` outdoor pairs and
  51 `*.blv`/`*.dlv` indoor pairs.
- `Data/mm6.T.lod/`: MM6 `*.evt` event programs.
- `Data/mmmerge.T.lod/`: merged text tables and MM6 `*.str` files needed for map/event strings.
- `Data/mm6.D.lod/`: MM6 world audio.
- `Data/mm6.bitmaps.lod/`: MM6 terrain, dungeon, sky, bitmap, and palette assets.
- `Data/mm6.icons.lod/`: MM6 UI, item, paperdoll, and icon assets.
- `Data/mm6.sprites.lod/`: MM6 object, decoration, item, and world sprite assets.
- `Data/mmmerge.sprites.lod/`: merged/custom monster sprite art used by MMerge for MM6 monsters.
- `Data/Tables/`: MMerge generated tables such as `SFT.txt`, `TFT.txt`, `Tile*.txt`, `Sounds.txt`,
  `Continent settings.txt`, `TownPortalSwitch.txt`, `Outdoor travels.txt`, and character/base tables.
- `DataFiles/`: generated binary tables, including `dsft.bin`, `dtft.bin`, `dtile*.bin`, `dmonlist.bin`,
  `ddeclist.bin`, `dobjlist.bin`, `dchest.bin`, `dift.bin`, `dpft.bin`, `doverlay.bin`, and `dsounds.bin`.

### Target MM6 World Shape

MM6 should be imported as a normal world package:

```text
assets_dev/worlds/mm6/
  world.yml
  audio/
  events/maps/
  maps/
  rendering/sprite_frames/monsters/
  sprites/
  textures/
  icons/
  _legacy/
```

The `_legacy/` tree is source-only import material. Runtime systems should consume canonical TXT/YML/BMP/PNG/WAV
assets from the normal world folders. Active TXT/BIN gameplay registries are flat MMerge/base data under
`engine/data_tables`, not world-local files.

Flat MM6/MMerge table imports feed these engine table targets:

```text
data_tables/chest_data.txt
data_tables/decoration_data.txt
data_tables/house_animations.txt
data_tables/house_data.txt
data_tables/map_navigation.txt
data_tables/map_stats.txt
data_tables/mon_list.txt
data_tables/monster_data.txt
data_tables/monster_death_drops.txt
data_tables/monster_descriptors.txt
data_tables/monster_projectiles.txt
data_tables/monster_relation_data.txt
data_tables/npc.txt
data_tables/npc_greet.txt
data_tables/npc_news.txt
data_tables/npc_topic.txt
data_tables/npc_topic_text.txt
data_tables/roster.txt
data_tables/sounds.txt
data_tables/terrain_tile_data.txt
data_tables/terrain_tile_data_2.txt
data_tables/terrain_tile_data_3.txt
data_tables/texture_frame_data.txt
data_tables/town_portal_switch.txt
data_tables/house_rules.txt
data_tables/transport_locations.txt
```

Flat MM6/MMerge story/localization imports feed these engine table targets:

```text
data_tables/english/autonote.txt
data_tables/english/awards.txt
data_tables/english/history.txt
data_tables/english/npc_group.txt
data_tables/english/place_mon.txt
data_tables/english/quest.txt
data_tables/english/trans.txt
```

MMerge's `MapStats.txt` currently gives MM6 maps global ids around `137..203`; for example `oute3.odm` is New
Sorpigal and `6d01.blv` is Goblinwatch. Treat those ids as import aliases in the flat engine table.

### Exporter Work Needed

Existing exporters should be parameterized before a full MM6 import. They should accept explicit source and target
paths instead of assuming old `assets_dev/Data` locations.

- `tools/export_outdoor_scene_yml.py` already detects MM6 ODM files. Use it for each `*.odm` with its `*.ddm`.
- `tools/export_indoor_scene_yml.py` should be used for each `*.blv` with its `*.dlv`.
- `event_asset_export_main` should use an MM6-specific config pointing at flat `engine/data_tables/*` registries and
  `worlds/mm6/_legacy/events`.
- Binary/table exporters for `SFT`, `TFT`, `Tile*`, `DecList`, `ObjList`, `MonList`, `Sounds`, `IFT`, `PFT`, and
  `Chest` need source/target arguments and world-aware output paths.

The desired output is our canonical TXT/YML shape, not runtime `*.bin` files. Keep `*.bin` only in `_legacy/` when
useful as import evidence.

### MMerge Systems To Rebuild Cleanly

The following MMerge systems are useful references, but in OpenYAMM they should become normal engine/base systems:

- world selection before new game, based on MMerge `MenuChooseContinent.lua`;
- active world tracking, based on MMerge `10_Continents.lua`;
- per-world saved state, replacing MMerge continent-local counter and day-counter storage;
- cross-world travel, based on MMerge `TownPortalSwitch.txt`, `Outdoor travels.txt`,
  `Transport Index.txt`, and `Transport Locations.txt`;
- world start/death/loading settings, based on MMerge `Continent settings.txt`;
- character creation availability filters, based on MMerge `Character selection.txt`.

Do not include MMerge's bolster/adaptive monster system in the first MM6 slice. It is a base balance feature, not
required for proving that MM6 can run as a world.

### First MM6 Slice

The first experiment should be New Sorpigal:

1. Create the `worlds/mm6` skeleton.
2. Export only `oute3.odm` and `oute3.ddm` to map/scene YML.
3. Extract or generate only the MM6 rows needed by `oute3.odm`.
4. Import the terrain, texture, decoration, monster, sprite-frame, monster audio, and event/string data that map needs.
5. Boot directly with `activeWorldId = "mm6"`.
6. Fix hardcoded MM8 assumptions exposed by that one map.

Avoid mass-importing all MM6 assets first. A single outdoor map exposes the remaining runtime assumptions with a much
smaller data and debugging surface.

## Migration Plan

Migration should keep the engine working at every step:

1. Add world and mod manifests while MM8 remains in its current content location.
2. Introduce `WorldId` and canonical `MapId` with MM8 as the only world.
3. Add active-world asset and data aliases.
4. Convert save/runtime map keys from raw filenames to canonical map ids.
5. Move MM8 world-specific data under `assets_dev/worlds/mm8/`.
6. Move shared data under `assets_dev/engine/`.
7. Add world discovery with MM8 mounted: MM8.
8. Add world selection to new game, initially offering only MM8.
9. Import one MM6 map as `worlds/mm6`.
10. Add MM6 as an optional starting world.
11. Add cross-world travel through `TravelService`.
12. Expand MM6 and MM7 import coverage.
13. Add base-level metaquests and difficulty profiles.

This keeps the current engine as the base and avoids a high-risk rewrite.

## Design Rules

- Preserve existing data table formats where practical.
- Prefer package scope and canonical ids over hardcoded source-game branches.
- Keep shared mechanics in shared gameplay code.
- Keep world-specific content in world packages.
- Keep cross-world rules in shared engine/base systems or explicit mod/world manifests.
- Treat mods as explicit overlays, not as hidden runtime mutation.
- Do not duplicate global tables per world when a single canonical repository is correct.
- Do not use broad compatibility fallbacks to hide stale converted data.
- Make migrations explicit when old saves or assets need reshaping.
