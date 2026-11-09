# Engine support for a ruleset

Status: investigation (2026-10-22). Part of the [vanilla mode investigation](README.md). Line numbers are from the
audit date and will drift.

## Today: one merged game

There is no ruleset, profile, game mode or campaign concept in the code. Everything below assumes the MMerge base.

### Content mounting

- **Development mode** (`engine/AssetFileSystem.cpp:683-747`).
  - Mounts the asset root, `engine/` and the active world at `/`, active world first.
  - For maps, events, textures, `_legacy`, sprites, icons, audio, music and video, mounts the active world, then
    `engine/`, then **every other world folder found on disk** (`:1098-1140`, `:1170-1183`, scan at `:245-270`).
  - There is no allow-list. `KnownWorldPackageIds` (`:104`) is declared but unused.
- **Packaged mode** reads `index.json` and mounts every listed pack the same way (`:922-951`).
- **Qualified paths** (`engine/...`, `worlds/<id>/...`) resolve only to that package (`:1695-1790`). Unqualified
  paths fall through the mount order.
- **The active world** changes with the map. `GameApplication::activateWorldForMap` (`game/app/GameApplication.cpp:7288-7338`)
  uses `MapStatsEntry::worldId`. That id is the `world_id` column of `map_stats.txt`, or a guess from the file name:
  `6*` or `oute*` is mm6, `7*` is mm7, anything else mm8 (`game/maps/MapIdentity.cpp:64-86`).
- **`world.yml`** (`game/content/ContentManifest.cpp:105-363`) supports id, name, sourceGame, start map, qbits,
  party movement, actor awareness, schema version, dependencies, id ranges and table contributions. The mm6/7/8
  manifests set only id, name and start map; only mm9 uses the rest.
- **Campaigns:** `assets_dev/campaigns/default/campaign.yml` exists; no code reads it. `AGENTS.md` says not to add
  a campaign layer for now.

### Gameplay tables

- `GameDataLoader::loadInternal` (`game/data/GameDataLoader.cpp:1570-1808`) loads 30+ tables;
  `loadMergedBaseTables` (`:3535-3804`) about 30 more; `applyMergedRuntimeTables` (`:3806-3852`) applies them.
- **Every path is fixed to `engine/data_tables/`** (`:503`, `:690`, `:695`). A world cannot shadow a table.
- **Table contributions** from `world.yml` support only `append` (merge by id within declared `idRanges`) and
  `distribution`. `TableContributionMode::Override` is parsed (`ContentManifest.cpp:80`) but every consumer rejects
  it (`GameDataLoader.cpp:2475, 2654, 3433, 3595, 4050, 4179, 4264`). Classes, skills, spells, race skills,
  character selection and continent settings have no contribution path at all.
- **Lua is additive:** every `events/Global_*.lua` and `events/maps/<map>_*.lua` is appended
  (`GameDataLoader.cpp:322-444`); `events/common/{world_common,cross_continents_common,common,<world>_common}.lua`
  are prepended (`:458-472`).
- **`worlds/mm6/_legacy/tables/`** is archived source, not read at runtime (only `_legacy/map_delta` is,
  `MapAssetLoader.cpp:4977`). `tools/export_mm6_world_tables.py` converts it into `engine/data_tables`.
- **Common data loads once**, before any world is chosen (`ensureCommonGameDataLoaded`,
  `GameApplication.cpp:7171-7197`, cached in `m_commonGameDataLoaded`).

### New game

1. `openNewGameScreen` (`GameApplication.cpp:9747`) loads common data.
2. **Continent selection** (`game/ui/screens/NewGameScreen.cpp:2025-2061`): hard-coded cards
   `{"enroth", "antagarich", "jadame"}` (`:2032`), enabled by `new_game_continents` in
   `engine/data_tables/character_selection.yml`.
3. **Character candidates** (`:825-900`): doll entries marked `availableAtStart` crossed with
   `race_class_availability`. The continent's `available_class_ids` only feeds `startingCasterClassId` (`:305-321`,
   hard-coded class ids 4/5 and 42/44); `available_race_ids` is parsed but unused.
4. **Party size 1-5** (`:742-800`), `Party::MaxMembers = 5` (`game/party/Party.h:693`).
5. **Start** (`startNewSessionFromCharacterCreation`, `GameApplication.cpp:10024-10129`).
   - Map and position come from the continent's `Death map 1` in `continent_settings.txt` (`:9809-9829`), falling
     back to `world.yml` `start.map`.
   - Gold 200 and food 5 are hard-coded (`:10063-10064`).
   - Start time is 9:00 (`GameSession.h:311`).
   - **The base year 1168 is a constant in at least seven places:** `GameMechanics.cpp:24`, `EventRuntime.cpp:40`,
     `StoryTextFormatter.cpp:15`, `GameplayPartyOverlayRenderer.cpp:66`, `LoadGameScreen.cpp:30,57`,
     `GameplaySaveLoadUiSupport.cpp:20`, `GameApplication.cpp:1752,1769`. Vanilla calendars start in 1165 (MM6),
     1168 (MM7) and 1172 (MM8).
6. **World to continent** is fixed: mm8 = 1, mm7 = 2, mm6 = 3 (`GameApplication.cpp:9787-9807`).
7. **Recruitment** (`MercenaryRecruitmentRuntime.cpp:93-120`) uses the continent's class list with hard-coded
   fallbacks for continents 1 and 2.

### Saves

- `GameSaveData` (`game/maps/SaveGame.h:21-49`, version 93 at `SaveGame.cpp:24`) stores the map, party, named
  global variables, per-map snapshots and time.
- `requiredContentPackages` lists non-engine packages that own items or vendors in the save (`SaveGame.cpp:4301-4405`).
- **No world id, continent, ruleset or table fingerprint is saved.** The world is re-derived from the map name.

### Rule toggles that already exist

- `[features]` settings such as `bolster_monsters`, pathfinding and blaster tweaks (`GameSettings.cpp:1468`). These
  are global user settings, not per save.
- `continent_settings.txt` (MMerge's per-continent rules: reputation, followers, news, death maps, skies, loading
  screens) is the closest thing to a profile today.
- `namedGlobalVars` already carries flags such as `MMerge.CrossContinents.DragonJoined` (the MM7 hatchling).

## Hard-coded merged-base assumptions

| Area | Where |
|---|---|
| All worlds always mounted | `engine/AssetFileSystem.cpp:1120-1129` |
| Map ownership over a fixed `{"mm6","mm7","mm8"}` | `GameDataLoader.cpp:2386` |
| World guessed from map name | `MapIdentity.cpp:64-86` |
| `mm8` as default world | `MapIdentity.h:9`, `ContentManifest.h:68`, `GameDataLoader.h:238`, `SoundCatalog.h:51`, `ContentManifest.cpp:95-102` |
| Continent ids and cards | `GameApplication.cpp:9787-9807`, `NewGameScreen.cpp:2032`, `MercenaryRecruitmentRuntime.cpp:108-117` |
| Death/respawn keyed on QBits 93 and 519 | `GameApplication.cpp:1268-1269, 11851-11856` |
| Cross-continent travel | `GameplayScreenRuntime.cpp:4084-4103`, `GameplayUiRuntime.cpp:717-760`, `GameplayItemService.cpp:33-34`, `events/common/cross_continents_common.lua` |
| 53 MMerge class names and promotion families | `game/party/SkillData.cpp:47-100, 370-420, 500-580` |
| Race constants (e.g. Dragon = 5) | `game/party/Party.cpp:902` |
| Spell ids in MM8/MMerge layout, about 520 uses in 24 files | `game/party/SpellIds.h:7-142` |
| Spell rules (112 rules) | `game/gameplay/PartySpellSystem.cpp:419-642` |
| Base year 1168 | see New game above |

## What a ruleset needs

1. **Identity.** A ruleset id chosen at new game, stored in the save (new field, version bump, following the
   existing `reader.version() < X` pattern), shown on the Load screen and checked on load. The hardcore
   investigation (`devdocs/plans/HARDCORE_MODE_INVESTIGATION.md`) has the same shape: a mode fixed at new game and
   carried by the save. The multiplayer plan's `CampaignState` (ruleset plus content fingerprint) should use the
   same id.
2. **A mounted-worlds allow-list** in `AssetFileSystem`, so a vanilla MM7 game cannot resolve MM6 or MM8 files.
3. **Table resolution per ruleset.** `engineDataTablePath` resolves through the ruleset first. The parsed but
   unused `Override` contribution mode is the natural hook, but it currently lives on worlds; a ruleset package is
   cleaner.
4. **Reloading common data** when the ruleset changes (new game, loading a save of a different ruleset).
5. **Per-ruleset constants** replacing the hard-coded ones: base year, start gold/food, party size limits, mastery
   ranks, resistance set, condition set, world/continent ids.
6. **Spell and class behaviour by ruleset.** `SpellIds.h` and `SkillData.cpp` are the deepest assumptions; see
   [SPELLS.md](SPELLS.md) and [RULES.md](RULES.md). MM7 and MM8 share almost everything; MM6 needs either a remap
   of its spell ids onto the MM7/MM8 slots plus new spell effects, or per-ruleset spell definitions.
