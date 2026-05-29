# MM7 MMMerge Remaining Work Tracker

This document tracks the remaining MM7/MMMerge integration work after the map overlays, global quest fixes, custom
Antagarich promotions, Temple in a Bottle, Dimension Door item, and first CrossContinents/Dragon Hatchling slices.

Use this as the active checklist for what is not yet fully closed. Keep implementation details in the relevant code or
inventory documents; keep this file focused on current status, references, and done criteria.

Status values:

- `Pending`: implementation or data integration is still needed.
- `Verify`: believed implemented, but needs focused game/editor/headless verification.
- `Deferred`: valid MMMerge/custom-content parity work, but intentionally outside the current core-MM7 slice.
- `Done`: complete and verified; keep a short note when moving an item here.

## High Priority

| Item | Status | Scope | References | Done criteria |
| --- | --- | --- | --- | --- |
| Antagarich continent/start/death routing | Done | `Continent settings.txt` now drives defeat respawn maps in addition to the existing death movie lookup. Emerald Island resolves to `7out01.odm`; Harmondale and other Antagarich maps resolve to `7out02.odm`. | `reference/mmmerge/Scripts/General/MenuChooseContinent.lua`, `reference/mmmerge/Scripts/General/10_Continents.lua`, `reference/mmmerge/Data/Tables/Continent settings.txt`; `game/app/GameApplication.cpp`, `game/outdoor/HeadlessOutdoorDiagnostics.cpp`, `tests/MergedBaseTablesTests.cpp` | Table-backed death maps and `7losegame` are covered by merged-table assertions and the app headless party-defeat case. |
| Antagarich weather/custom sky audit | Done | Weather/custom sky table consumption already happens during outdoor map load; the MM7 custom sky rows and continent sky list are now covered by asset-resolution tests. | `reference/mmmerge/Scripts/General/Weather.lua`, `reference/mmmerge/Data/Tables/Bolster - maps.txt`, `reference/mmmerge/Data/Tables/Continent settings.txt`; `game/data/GameDataLoader.cpp`, `tests/MergedBaseTablesTests.cpp`, `tests/MapStatsRegressionTests.cpp` | Antagarich sky references resolve through `AssetFileSystem`; Tularean Forest bolster/weather metadata is covered by regression tests. |
| Runtime bolster consumer | Done | Shared bolster runtime now consumes merged map and monster rows for effective HP/AC/move speed/spell skill scaling, map spell/summon gates, and immobile/static monster handling in both indoor and outdoor actor AI setup. | `reference/mmmerge/Scripts/General/AdaptiveMonstersStats.lua`, `reference/mmmerge/Data/Tables/Bolster - maps.txt`, `reference/mmmerge/Data/Tables/Bolster - monsters.txt`; `game/gameplay/GameplayBolsterRuntime.cpp`, `game/outdoor/OutdoorWorldRuntime.cpp`, `game/indoor/IndoorWorldRuntime.cpp`, `tests/GameplayBolsterRuntimeTests.cpp` | Covered with focused unit tests for the MM7 Tularean Forest row and immobile tree summon gating; applies to MM6/MM7/MM8 because the merged tables are global. |
| Town Portal MM7 unlock verification | Done | Antagarich Town Portal labels/unlocks are loaded from merged `TownPortalSwitch.txt` rows and QBits `718-723`. | `reference/mmmerge/Scripts/General/1_TownPortalSwitch.lua`, `reference/mmmerge/Scripts/Global/TownPortalSwitches.lua`, `reference/mmmerge/Data/Tables/TownPortalSwitch.txt`; `game/ui/GameplayUiRuntime.cpp`, `tests/MergedBaseTablesTests.cpp` | Regression covers Castle Harmondale, Tularean Forest, Steadwick, Nighon, Celeste, and The Pit destination labels and qbit gates. |
| MM7 indoor transition video/text audit | Done | Known MM7 dungeon transitions use world/map transition metadata instead of MM8 fallback. | `reference/mmmerge/Scripts/General/MiscTweaks.lua`, `reference/mmmerge/Data/Tables/House Movies.txt`, `reference/mmmerge/Data/Tables/House exits.txt`, `assets_dev/engine/data_tables/map_stats.txt`; `tests/GameplayRuleRegressionTests.cpp` | Regression covers Temple of the Moon enter/exit text and transition video source. |

## Verification And Data Audits

| Item | Status | Scope | References | Done criteria |
| --- | --- | --- | --- | --- |
| Arena restrictions and NPC 639 routing | Done | Arena save/Lloyd restrictions and NPC `639` topic routing are regression-covered. | `reference/mmmerge/Scripts/Maps/7d05.lua`, `reference/mmmerge/Scripts/Global/TownPortalSwitches.lua`; `tests/GameplayRuleRegressionTests.cpp` | Regression covers NPC `639` routing and save/Lloyd blocking in `7d05.blv`. |
| Temple of the Moon initial door state | Done | Doors `5-8` start closed and `9-10` start open in the authoritative scene data. | `reference/mmmerge/Scripts/Maps/7d06.lua`; `tests/GameplayRuleRegressionTests.cpp` | Regression parses `7d06.scene.yml` and confirms the initial door states. |
| Tularean Forest Dimension Door authored trigger | Done | Scene overlays can now target bmodels by name; `7out04_1.scene.yml` binds all `ClL1_W` faces to event `504`. | `reference/mmmerge/Scripts/Maps/7out04.lua`; `assets_dev/worlds/mm7/maps/7out04_1.scene.yml`, `game/maps/OutdoorSceneYml.cpp`, `tests/ScriptedMapRegressionTests.cpp` | Regression loads `7out04.odm` with companions and verifies all `ClL1_W` faces trigger event `504`; event `504` opens Dimension Door. |
| MM7 house video table audit | Done | House videos and known MM7 dungeon transition clips resolve from merged metadata. | `reference/mmmerge/Data/Tables/House Movies.txt`, `reference/mmmerge/Data/Tables/House exits.txt`; `tests/GameplayRuleRegressionTests.cpp` | Regression covers the previous MM7 Temple of the Moon/MM8 fallback class of transition bug. |
| NPC text exactness audit | Verify | Functional NPC topics/greetings are integrated, but exact legacy text selection can be tightened if a topic shows wrong copy. | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCText.txt`, `NPCGreet.txt`, `NPCTopic.txt`; `reference/mmmerge/Scripts/Global/*.lua` | Spot-check promotion, Verdant, CrossContinents, and Dragon Hatchling topics. Any wrong text is fixed through table/topic ids, not script string fallbacks. |
| Teacher/autonote fullscreen/minimap markers | Done | Teacher autonote mapping and generated marker text are data-driven through the merged teacher/autonote tables. | `reference/mmmerge/Data/Tables/Teacher autonotes.txt`, merged autonote/news/profession tables; `tests/MergedBaseTablesTests.cpp`, `tests/HouseDialogueRegressionTests.cpp` | Regression covers merged teacher autonote mappings and teacher topic note creation. |
| Transport/Town Portal table audit | Done | Merged Town Portal, Dimension Door, outdoor edge travel, stable/boat route, transport override, and save-state paths are audited. `Transport Index.txt` stays parsed as reference-only; runtime routes stay owned by `House rules.txt` plus `Transport Locations.txt`. | `MMERGE_TRANSPORT_TOWN_PORTAL_AUDIT.md`, `reference/mmmerge/Data/Tables/TownPortalSwitch.txt`, `reference/mmmerge/Data/Tables/Outdoor travels.txt`, `reference/mmmerge/Data/Tables/Transport Locations.txt`, `reference/mmmerge/Scripts/Structs/After/RemoveTravelLocationsLimits.lua` | Audit confirms byte-identical active tables, identifies runtime consumers/tests, and records the intentional Dimension Door landing-policy delta. |

## Deferred Custom-Content Or Broader Systems

| Item | Status | Scope | References | Done criteria |
| --- | --- | --- | --- | --- |
| Dragon Hatchling full party-member lifecycle | Deferred | Current slice supports cross-path promotion entry and feed/grow/join-as-follower. Remaining work is real named party/roster member behavior, dismissal lifecycle, and skill/SP aura. | `reference/mmmerge/Scripts/Global/Quest_DragonHatchling.lua`, merged NPC/quest/class/race tables | Hatchling can become a custom party/roster member with stable name/state across save/load, dismissal/rejoin works, and aura effects apply only while appropriate. |
| CrossContinents shared Breach map package | Done | `Breach.odm`, `BrAlvar.odm`, and `BrBase.blv` are mounted under `assets_dev/worlds/mmmerge` with legacy companions and minimal travel/local-state scripts. | `reference/mmerge_data_forus/Data/breach.games.lod`, `reference/mmmerge/Scripts/Maps/Breach.lua`, `reference/mmmerge/Scripts/Maps/BrAlvar.lua`, `reference/mmmerge/Scripts/Maps/BrBase.lua`; `assets_dev/worlds/mmmerge/maps`, `assets_dev/worlds/mmmerge/events/maps`, `tests/ScriptedMapRegressionTests.cpp` | Headless regression loads all three maps from the shared package and compiles the local scripts. |
| CrossContinents shared final quest gameplay | Deferred | First playable slice is in: Verdant intro/topics, Dimension Door gate, connector stone, completion rewards, final quest start, and Breach map mounting. Remaining work is the detailed Breach/BrAlvar/BrBase final quest mechanics and later Saving Goobers extension. | `reference/mmmerge/Scripts/Global/Quest_CrossContinents.lua`, `reference/mmmerge/Scripts/Maps/Breach.lua`, `reference/mmmerge/Scripts/Maps/BrAlvar.lua`, `reference/mmmerge/Scripts/Maps/BrBase.lua`, `reference/mmmerge/Scripts/Global/Quest_SavingGoobers.lua` | Final quest mechanics are ported as OpenYAMM scripts/systems without copying MMMerge Lua, with headless coverage for key exits, quest state, and completion. |
| Runtime generated mercenary portrait metadata | Deferred | MMMerge hardcodes Antagarich portrait exceptions. OpenYAMM should solve this through character selection/portrait metadata instead. | `reference/mmmerge/Scripts/General/NPCMercenaries.lua`, `assets_dev/engine/data_tables/character_data.txt`, character selection metadata | Generated mercenaries avoid special MM6/MM7 faces through data-driven portrait eligibility. No hardcoded Antagarich exception list in runtime code. |
| Broader roster lifecycle hooks | Deferred | Some MMMerge custom content wants party-member creation, naming, dismissal, aura, and custom roster behavior. This is broader than MM7 parity overlays. | `reference/mmmerge/Scripts/Global/Quest_DragonHatchling.lua`, future mod scripting API plans | Engine exposes a clean, mod-friendly roster/party-member API with save-stable state and tests. |

## Already Closed Core MM7 Work

These are kept here so the remaining list has context. Do not re-open unless a regression is found.

| Item | Status | Notes |
| --- | --- | --- |
| MM7 map overlay scripts | Done | Implemented for the known MM7 MMMerge map overlays. See `MM7_MMERGE_FIXUP_INVENTORY.md` for per-map details. |
| Original MM7 quest repairs | Done | Malwick wand/ambush, Cast Off, MM7 endgame QBits, Arcomage deck restriction, tavern win tracking, and rescued follower lifecycle are implemented/tested. |
| Antagarich custom promotions | Done | Events `795-853` plus blaster topic `950` are overlaid. Class changes use table-backed Lua class metadata. |
| Lich ritual focused follow-up | Done | Member-owned jar consumption, race/sex-aware Lich identity, resistance/immunity state, and incompatible skill cleanup are implemented/tested. |
| Temple in a Bottle and Dimension Door scroll | Done | Return location persists in runtime/save state; `7nwc` fallback works; scroll opens the same Dimension Door UI. |
| Erathia transport route override | Done | Runtime transport override is persistent save state; route data comes from house rules/transport location tables. |

## Update Rules

- When implementing an item, update `Status`, `Done criteria`, and add the concrete OpenYAMM file/test path in the
  item row.
- If an item proves already complete, move it to `Done` with the verification command or test name.
- If an item grows into multiple implementation tasks, split the row rather than adding a long note.
- Do not copy MMMerge Lua. Use the references to implement behavior through OpenYAMM data, overlays, or shared systems.
