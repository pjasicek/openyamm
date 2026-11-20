# MMerge features in OpenYAMM

Status: investigation (2026-10-22). Part of the [vanilla mode investigation](README.md). Line numbers are from the
audit date and will drift.

MMerge's own feature scripts are in `reference/mmmerge/Scripts/General/` (with `Global/` and `Structs/`). This table
maps each one to our implementation and rates how easy it is to switch off or replace with vanilla behaviour.

Ease: **D** data-driven (swap or empty a table), **H** hard-coded (needs a code gate), **N** not implemented.

## Feature table

| MMerge feature | OpenYAMM location | Driven by | Ease |
|---|---|---|---|
| Continents (tracking, change events) | `MapStats.cpp:679` sets `mergedContinentId`; fallback map-id ranges 0-61 / 62-136 / 137-203 in `GameplayDialogController.cpp:769-781` | `bolster_maps.txt` + hard-coded ranges | D/H |
| Continent settings (reputation, followers, news, death map and movie, skies, loading screens) | `ReputationRuntime.cpp:57`, `EventDialogContent.cpp:263-295`, `GameApplication.cpp:1747, 11922`, `GameplayDialogController.cpp:1990` | `continent_settings.txt` (row 4 "Between time" is MMerge-only) | D |
| Town Portal switch | `GameplayUiRuntime.cpp:133-146` picks the group by **map-id range**; loader `:680-715` | `town_portal_switch.txt` (`townport`, `Antagrich`, `TPEnroth`, `TPGlobal`) | D table, H selection |
| Dimensional travel (Verdant, the connector stones, the Dimension Door scroll and MMerge's travel spots were removed on 2026-11-09) | `GameplayUiRuntime.cpp` (`TPGlobal`), opened by the towns' pedestals (`evt.OpenDimensionDoor`, event 1777 in New Sorpigal, Ravenshore and Harmondale; Sturmford City's 250) and MMerge's town fountains (oute3 140, out02 104, 7d29 65031), with no quest; the Town Portal continent buttons | world scene overlays `<map>_dimensional_travel.scene.yml`, `7d29_dimension_travel.scene.yml` | D, easy to gate |
| Outdoor travels (map-edge links) | `MapStats::applyMergedOutdoorTravels` (`MapStats.cpp:813`) | `outdoor_travels.txt`, including cross-world edges (`7out02` to `out11`, `out14`, `7out15`) | D |
| Boats and stables | `HouseTable.cpp:1340-1390` | `house_rules.txt`, `transport_locations.txt` (QBit-gated cross-world rows, e.g. QBits 1192, 223, 610) | D |
| Adaptive monster stats (bolster) | `game/gameplay/GameplayBolsterRuntime.cpp` (new spells, summons, replication at `:755-790`); setting `[features] bolster_monsters` | `bolster_maps.txt`, `bolster_monsters.txt`; `bolster_formulas.txt` is loaded but unused | D toggle, H formulas |
| Additional UI (MM6/MM7 UI art) | table loaded, no consumer | `additional_ui.txt` | N |
| Bounty hunt (MM8 made like MM6/MM7) | `BountyHuntRuntime.cpp:113-150` picks from **every** world's monsters | `monster_data.txt`, `bolster_monsters.txt` "No bounty hunt" | H, needs a world filter |
| Council appearance (Free Haven pictures) | `HouseInteraction.cpp:31, 166, 1409`; `GameplayDialogueRenderer.cpp:57, 330-392` | hard-coded house 209 and NPC ids | H |
| Extra events (engine hooks) | spread out, e.g. hireling travel and food reductions in `NpcFollowerRuntime.h:50-53` | code | H |
| Extra quick spells | only the vanilla single quick spell (`GameplaySpellActionController.cpp:10`) | — | N |
| History per continent | `Party.h:446-448`, `setActiveHistoryContinent` | `english/history.txt`, `mm7_history.txt` | D |
| Choose character / choose continent menus | `NewGameScreen.cpp:829, 2003, 2037`; start via `resolveContinentStartDestination` | `character_selection.yml` | D |
| Racial skills | `ClassSkillTable::applyRaceSkillOverrides` | `race_skills.yml` | D (empty for vanilla) |
| Misc tweaks (lich, regeneration, turn-based speed, arena travel, fixes) | scattered, e.g. lich portraits `Party.cpp:908-911` | code | H, partly ported |
| Monster items (drops, summon on death) | `monster_death_drops.txt` (`GameDataLoader.cpp:2549`); summons via bolster | data | D |
| NPC followers (hireling panel, professions) | `NpcFollowerRuntime.*`, gated by the continent's `npcFollowers` | `npc_professions.txt`, `npc_btb.txt` | D/H |
| NPC mercenaries (hire generated characters) | `MercenaryRecruitmentRuntime.cpp` (`:1052`) | roster, `character_selection.yml` | H |
| NPC news topics | `GenericActorDialog.cpp:427`, `OutdoorInteractionController.cpp:1909, 5013`, `IndoorGameView.cpp:933` | `news_topics_*.txt`, `npc_names.txt`, continent flag | D |
| Teacher autonotes | `GameplayDialogController.cpp:787+` | `teacher_autonotes.txt`, `teacher_topics.txt` | D |
| Spell tweaks | **mostly not ported.** Town Portal uses the vanilla rule (`PartySpellSystem.cpp:1771-1806`); monster spell limits in `MonsterSpellSupport.cpp:42-52` | MMerge's MM8-layout `spells.txt` | H |
| Stealing from shops **and monsters** | `StealingRuntime.h:8-12` | code | H (vanilla MM7 steals from shops only) |
| Switch gold (per-continent gold art) | not found; `Global_mm6_gold_bags.lua` handles MM6 bag events only | — | N |
| Usable items (horseshoe, genie lamp, Deck of Fate, Temple in a Bottle, Dimension Door scroll) | `InventoryItemUseRuntime.cpp:19-25, 185-205, 780, 937`; `GameplayItemService.cpp` | hard-coded item ids | H |
| Extra potions (permanent stat potions, once each) | `InventoryItemUseRuntime.cpp:25, 185-205` | `potion_settings.txt`, `reagent_settings.txt` | H/D |
| Weather | `game/outdoor/WeatherModel.*` | `bolster_maps.txt` weather columns + `engine/rendering/weather/weather.yml` | D (OpenYAMM's weather is presentation; keep) |
| Zombie players | Zombie condition only (`Party.cpp:3590, 6748`; temple tier `HouseInteraction.cpp:703`) | code | H, partial |
| Reputation | `ReputationRuntime.cpp:33, 57` (`continentUsesMergedReputation`) | `continent_settings.txt` | D |

## MMerge content to hide in vanilla mode

- **Lua overlays.** 69 `*_mmmerge.lua` files: 26 in mm6, 25 in mm7 and 14 in mm8 under `worlds/*/events/maps/`,
  plus `Global_mm6_mmmerge.lua`, `Global_mm7_mmmerge.lua` and `engine/events/Global_mmmerge_crystals.lua`.
  - They are hand ports of MMerge's `Scripts/Maps/*.lua` and are picked up by `isLuaMapOverlayFileName`
    (`GameDataLoader.cpp:322`). Skipping the `_mmmerge` suffix is a small switch.
  - `events/common/cross_continents_common.lua` is always prepended (`:461`).
  - Each overlay still needs a check: some may carry fixes rather than additions.
- **Global events.** `engine/events/Global.lua` is generated from MMerge's merged `Global.EVT` (113,780 bytes, about
  2.5 times vanilla MM8's 45,579). It covers all three games in one file.
- **Classes.** `class_extra.txt` and `english/class.txt` hold MMerge's 50-class tree, including Peasant, Dark
  Archmage, High Priest and Master Wizard. `character_selection.yml` lets races pick classes their own game didn't
  allow.
- **Items.** `items.txt` has 2,203 merged rows (MM8, MM7 and MM6 blocks plus MMerge extras: crystals 2056-2065, Deck
  of Fate 2067, Arcomage deck 1453, connector stones 624/625, message scrolls 770-772). About 315 rows carry a
  `World:mmX` flag, honoured by `ItemDefinition::availableInWorld` (`ItemTable.cpp:535`) in random generation
  (`ItemGenerator.cpp:168`) and shops (`HouseServiceRuntime.cpp:487`). Flagging every row would make loot and shops
  per world.
- **Artifacts** are unique across all three games in MMerge (`reference/mmmerge/Scripts/Global/ExtraArtifacts.lua:22-30`)
  and the artifacts-found limit is removed.
- **QBits.** MMerge's cross-continent and extra quests sit around 1537-1792, plus 783/784 and 1104/1105.
- **NPCs and houses.** Verdant (NPC 803) and the meeting-spot houses 185, 641 and 1195 are MMerge-only; Verdant's
  scripts are removed (2026-11-09), her table rows stay unused.
- **Metaquests and quest additions.** Enroth Grandmaster teachers
  (`Global_mm6_mmmerge.lua:18-64`); MMerge's Enroth Dark Arts, Saving Goobers and Dragon Hatchling quests (no match
  found in our event scripts). The repository root has `MMERGE_QUEST_COMPLETION_INVENTORY.pdf`.
- **Cross-world travel rows.** `transport_locations.txt` rows 79-81 and 96-100, the cross-world edges in
  `outdoor_travels.txt`, the `TPGlobal` Town Portal group, and continent row 4.
- **Monsters.** Bolster adds spells, summons and replication not in the original games. Bounty hunts draw from all
  worlds. Whether map random encounters (`map_stats` Mon1-3) contain other-world monsters was not checked.

## Effort by category

1. **Data swap** (a ruleset table override): continent settings, character selection, race skills, outdoor travels,
   house rules and transport, news topics, teacher autonotes, bolster off.
2. **Small code gates:** skip `_mmmerge` overlays and the dimensional travel pedestals and fountains; hide the Town Portal
   continent buttons; choose Town Portal groups and continent ids by `worldId` instead of map-id ranges
   (`GameplayUiRuntime.cpp:133`, `GameplayDialogController.cpp:769`); filter bounty hunts by world; make monster
   stealing a ruleset rule.
3. **Deep:** the class and promotion tree, party size, spell rules and spell table (see [RULES.md](RULES.md) and
   [SPELLS.md](SPELLS.md)), and the global event file.
