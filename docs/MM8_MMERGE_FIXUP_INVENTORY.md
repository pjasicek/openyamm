# MM8 MMMerge Fixup And Script Inventory

This inventory tracks MMMerge behavior layered on top of original MM8/Jadame content. Sources scanned:

- `reference/mmmerge/Scripts/Maps/*.lua`
- `reference/mmmerge/Scripts/Global/*.lua`
- `reference/mmmerge/Scripts/General/*.lua`
- `reference/mmmerge/Scripts/Structs/After/*.lua`
- `reference/mmmerge/Data/Tables/*.txt`
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/*.txt`
- `reference/mmext-scripts/Decompiled_Scripts/mm8orig/`
- `reference/mmext-scripts/Decompiled_Scripts/mm8/`

Do not copy MMMerge Lua into OpenYAMM. Treat it as reference behavior and implement through generated event overlays,
scene overlays, typed table consumers, or shared gameplay systems.

## Summary

- MMMerge has 16 map overlay scripts whose filenames match original MM8 maps:
  `d06`, `d07`, `d19`, `d24`, `d34`, `d38`, `d39`, `d42`, `out01`, `out02`, `out04`, `out05`,
  `out06`, `out07`, `out13`, and `pbp`.
- Most MM8 overlays are small bug/continuity repairs around reusable keys, map-local monster state, Town Portal or
  Dimension Door hooks, and late-game quest state.
- `out04` and `out06` are static/data fixes: Ironsand and Shadowspire terrain footstep overrides live in scene data,
  and Shadowspire dirt terrain is remapped to `gdtyl` as tracked in `MMERGE_MAP_FIXUP_INVENTORY.md`.
- The generated `assets_dev/worlds/mm8/events/maps/*.lua` files are original MM8 event exports. They may already
  include GrayFace/MM8Patch-style decompiled event corrections, but they are not equivalent to MMMerge's extra map Lua
  overlays unless explicitly noted below.
- Non-prefixed MMMerge scripts such as `d03`, `out09`, `out11`, `out12`, `out14`, `mdt15`, `hive`, `pyramid`,
  `sewer`, `sci-fi`, and `oracle` are not original MM8/Jadame maps in the merged table. Track them under the MM7,
  MM6, or custom-content inventories instead.

## Map Overlay Inventory

| Map script | MM8 map | MMMerge behavior | Status / OpenYAMM work item |
| --- | --- | --- | --- |
| `d06.lua` | Pirate Outpost | Replaces submarine event 451 so the party can enter with Pirate Leader's Key item `619` or persisted lost-item QBit `214`; sets QBit `214` once accepted. | Implemented in `assets_dev/worlds/mm8/events/maps/d06_mmmerge.lua`; covered by reusable-key branch regressions. |
| `d07.lua` | Smuggler's Cove | Replaces original wererat load/leave hostility bookkeeping with `mapvars.WereratsMad`, clears it after one day, and marks it on monster kill. | Implemented in `d07_mmmerge.lua` with named map vars and a timer-based defeated-group tracker; covered by kill-tracker/cooldown regressions. |
| `d19.lua` | Necromancers' Guild | Replaces inner chamber door event 15 so invisibility blocks the NPC warning path without requiring Dyson Leland; replaces event 131 so the Skeleton Transformer can be destroyed without Dyson Leland if map state is ready. | Implemented in `d19_mmmerge.lua`; covered by door and transformer branch regressions. |
| `d24.lua` | Balthazar Lair | On map load, if QBit `23` is set, all group-0 tritons are hidden by setting actor AI state to invisible. | Implemented in `d24_mmmerge.lua` through group invisible state; covered by on-load runtime-state regressions. |
| `d34.lua` | Small Sub Pen | Replaces submarine event 451 so return travel to Pirate Outpost no longer requires Pirate Leader's Key. | Implemented in `d34_mmmerge.lua`; covered by reusable travel regression. |
| `d38.lua` | Prison of the Lord of Water | After load, if QBit `53` is not set, moves NPC `24` back to house `662` to repair consequences of the Regna cannon sequence. | Implemented in `d38_mmmerge.lua`; covered by on-load NPC placement regression. |
| `d39.lua` | Prison of the Lord of Earth | After load, if QBit `51` is not set, moves NPC `25` back to house `663` to repair consequences of the Regna cannon sequence. | Implemented in `d39_mmmerge.lua`; covered by on-load NPC placement regression. |
| `d42.lua` | Arena | Replaces arena exit event 501 to route to the active continent: Antagarich `7out02.odm`, Enroth `outd3.odm`, otherwise Jadame `out02.odm`. | Implemented in `d42_mmmerge.lua` using `CurrentContinent()`; runtime restrictions live in `d42_1.scene.yml`. |
| `out01.lua` | Dagger Wound Island | Adds Dimension Door trigger on tile `(63, 59)` and sets Jadame Town Portal unlock QBit `185` on load. | Implemented in `out01_mmmerge.lua` with a 1-second tile latch timer and QBit `185` on load; covered by on-load and tile-latch regressions. |
| `out02.lua` | Ravenshore | Adds CrossContinents final-quest proximity hook near `(15103, -9759)`; blocks Town Portal there and moves to `BrAlvar.odm` or `Breach.odm`; marks Jadame continent finished when QBit `56` is set; replaces crystal event 504 so Conflux Key item `610` is only needed the first time. | Crystal reuse implemented in `out02_mmmerge.lua`. Breach/CrossContinents hook remains deferred custom-content work. |
| `out04.lua` | Ironsand Desert | Overrides tile sounds by tile set: default, desert, and volcanic terrain use explicit walk/run sound ids. | Implemented as `assets_dev/worlds/mm8/maps/out04_1.scene.yml` terrain footstep overrides; covered by descriptor/footstep regression. |
| `out05.lua` | Garrote Gorge | Replaces/overrides clear-land quest event 131 for dragon and dragon-hunter kill completion, guarded by alliance QBits `22/21` and completion QBits `155/158`. | Implemented as an appended safety completion pass in `out05_mmmerge.lua` to preserve generated Riki/lost-item logic; covered by clear-land completion regression. |
| `out06.lua` | Shadowspire | Locally swaps dirt tile texture to `gdtyl` and gives tile set 5 explicit walk/run sounds. | Done as static/data fix: `out06_1.scene.yml` carries terrain footstep overrides and the terrain descriptor remap is tracked in `MMERGE_MAP_FIXUP_INVENTORY.md`; covered by descriptor/footstep regression. |
| `out07.lua` | Murmurwoods | Adds Dimension Door event 500 and tile `(43, 98)` trigger; lets Cauri/statue events 132-136 use Stone to Flesh spell knowledge as an alternative to scroll item `339`; extends the gem exchange tree to accept merged duplicate gem item ids. | Implemented in `out07_mmmerge.lua`; covered by statue, gem, Dimension Door, and tile-latch regressions. |
| `out13.lua` | Regna | Replaces cannon events 451/452 so the Cannonball of Dominion can fire the cannon again whenever item `662` is present, even after the fleet is already sunk; drives a timed fire/effects/finalization sequence through `mapvars`. | Implemented in `out13_mmmerge.lua`; covered by reusable cannon sequence regression. |
| `pbp.lua` | Plane Between Planes | Replaces prison entrances 502-505 so Ring of Keys item `629` is only needed the first time each prison is opened; persists per-prison `mapvars.*PrisonOpen` state. | Implemented in `pbp_mmmerge.lua`; covered by per-prison branch regressions. |

## Original MM8 Maps With No MMMerge Map Overlay

No MMMerge per-map Lua overlay was found for these original MM8 map scripts. Keep generated original events authoritative
unless a global/table-driven MMMerge system below affects them:

`d05`, `d08`, `d09`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `d16`, `d17`, `d18`, `d20`, `d21`, `d22`, `d23`,
`d25`, `d26`, `d27`, `d28`, `d29`, `d30`, `d31`, `d32`, `d33`, `d35`, `d36`, `d37`, `d40`, `d41`, `d43`, `d44`,
`d45`, `d46`, `d47`, `d48`, `d49`, `d50`, `elema`, `eleme`, `elemf`, `elemw`, `out03`, `out08`, and `out15`.

## Global MM8 Script Inventory

| Source | MM8/Jadame behavior | Status / OpenYAMM work item |
| --- | --- | --- |
| `Scripts/General/10_Continents.lua` | Tracks current/previous continent and map; treats original MM8 map ids `0..61` as Jadame unless `Bolster - maps.txt` overrides them. | Partially covered by active world/continent context. Verify previous/current continent events if any MM8 overlay depends on them. |
| `Scripts/General/1_TownPortalSwitch.lua` | Reads `TownPortalSwitch.txt` and swaps Town Portal destinations, icons, labels, and unlock QBits. Jadame uses QBits `180..185`. | Integrated and runtime consumed through `assets_dev/engine/data_tables/town_portal_switch.txt`. Dagger Wound QBit `185` discovery and Jadame Town Portal rows are covered by regression tests. |
| `Scripts/Global/TownPortalSwitches.lua` | Resolves map-to-continent, treats `d42.blv` as arena, blocks Lloyd's Beacon and saving in arena, and provides the shared Dimension Door event. | Implemented through scene runtime restrictions, Town Portal/Dimension Door UI data, and MM8 map overlays. `d42` save/Lloyd restrictions and MM8 Dimension Door hooks are covered by regressions. |
| `Scripts/General/2_OutdoorTravels.lua` | Uses merged `Outdoor travels.txt` for edge travel across all continents. Current merged rows affect MM6/MM7/custom bridge maps and do not replace original MM8 outdoor edge travel. | Integrated as table data; MM8 original outdoor transitions are guarded by regression coverage. |
| `Scripts/General/MenuChooseContinent.lua` | Reads `Continent settings.txt`; Jadame row defines MM8 new-game start, death movie, water texture, sky set, and fallback map. | Start/death map, coordinates, facing, death movie, water/sky/weather rows are consumed. New-game continent chooser UI remains future work. |
| `Scripts/General/Weather.lua` | Uses `Continent settings.txt` and `Bolster - maps.txt` for sky/weather selection. | Consumed for outdoor maps through merged continent settings and bolster-map weather flags; Jadame custom sky/weather rows are covered by regression coverage. |
| `Scripts/Global/Quest_CrossContinents.lua` | Adds custom Verdant/CrossContinents quest state; for Jadame, uses QBit `228` as MM8 story completion, fixed meet spot in Regna, connector stone map `out03.odm`, and final Breach hook through `out02.lua`. | First playable global slice exists for CrossContinents, but custom Breach maps and MM8 map-local `out02` hook remain separate custom-content work. |
| `Scripts/Global/Quest_DragonHatchling.lua` | Adds custom dragon hatchling/party-member flow and cross-world promotion paths. This is not original MM8, but can affect a Jadame-starting party. | First playable feed/grow/join-as-follower slice exists in shared global overlay work; full party-member lifecycle remains future work. |
| `Scripts/Global/StdQuestsFunctions.lua` | Provides shared fixes and helpers used by MMerge quest overlays, including lost quest items, guild joins, Arcomage handling, and cross-continent quest helpers. | Partially implemented for MM6/MM7 slices. Audit for MM8-specific behavior before using it as authority; many functions are shared and table-driven rather than map-local. |
| `Scripts/General/NPCMercenaries.lua` and `NPCFollowers.lua` | Makes mercenary/follower state continent-aware and supports merged roster behavior. | Partially implemented through shared follower/roster systems. Verify Jadame special NPCs are not broken by MM6/MM7 follower imports. |
| `Scripts/General/AdaptiveMonstersStats.lua` | MMerge bolster system can change Jadame monster stats through `Bolster - maps.txt` and monster kind flags. | Runtime bolster applies shared HP, AC, movement speed, attack damage, spell skill/mastery, and summon/new-spell eligibility facts through indoor/outdoor actor AI paths. |
| `Scripts/General/Additional UI.lua`, `MenuChooseCharacter.lua`, `MenuChooseContinent.lua`, `MenuExtraSettings.lua` | Changes MM8 UI flow for merged continent/character selection and MMerge settings. | Not MM8 map fixup scope. Track in UI/new-game/merge-settings work, not map parity. |
| `Scripts/Structs/After/Remove*`, `GlobalEventsNewHandler.lua`, `Text Tables.lua`, `DataTablesSupport.lua` | Removes MM8 executable limits and expands tables/QBits/classes/items/NPCs for merged content. | Do not port as memory patches. Equivalent OpenYAMM work belongs in typed loaders, table limits, save/schema support, and shared systems. Most table integration is tracked in `MMERGE_TXT_TABLE_INTEGRATION_INVENTORY.md`. |

## MMerge Data Table Inputs For MM8

| Table | MM8/Jadame scope | OpenYAMM state / next step |
| --- | --- | --- |
| `Data/Tables/Continent settings.txt` | Jadame start/death/water/sky settings. | Integrated and consumed for active-world start destinations, party-defeat respawn destinations, death movies, water, skies, and weather. |
| `Data/Tables/TownPortalSwitch.txt` | Jadame Town Portal block and QBits `180..185`. | Integrated and consumed. Verify map unlock QBits from map events/overlays, especially Dagger Wound `185`. |
| `Data/Tables/Outdoor travels.txt` | Shared merged outdoor edge travel. | Integrated and consumed; current rows do not override original MM8 outdoor edge travel. |
| `Data/Tables/Bolster - maps.txt` | Jadame map bolster/weather/sky flags. | Integrated with typed loader and consumed by outdoor map loading/weather runtime and shared indoor/outdoor actor bolster runtime. |
| `Data/mmmerge.T.lod/MapStats.txt` | Rows `0..61` are original Jadame/MM8 map ids in the merged flat map table. | Integrated as `assets_dev/engine/data_tables/map_stats.txt`. Treat raw ids as import aliases, not canonical world ids. |
| `Data/Tables/Tile*.txt` and generated `DataFiles/dtile*.bin` | Merged terrain tile ids and tile sounds. | Integrated/remapped for MM8 outdoor lookups. Keep `out04`/`out06` local tile-sound overlays in sync with this table. |
| `Data/Tables/House Movies.txt`, `House exits.txt`, `House rules.txt` | Merged house animation, sound, exit, service, and Arcomage rules for Jadame houses. | Integrated and consumed. Verify any MM8 house behavior changed only when the merged table intentionally differs. |
| `Data/mmmerge.T.lod/Quests.txt` | Global QBit/autonote/quest registry, including original MM8 bits and MMerge-added bits. | Integrated. Use registry comments when porting map overlays. |
| `Data/mmmerge.T.lod/NPCData.txt`, `NPCGreet.txt`, `NPCText.txt`, `NPCTopic.txt` | Merged NPC dialogue tables including original MM8 NPCs plus custom MMerge NPCs. | Integrated. CrossContinents/Verdant and Dragon Hatchling behavior should reference these through global overlay work. |
| `Data/Tables/Character selection.txt`, `Class Skills.txt`, race/class tables | MMerge character creation and roster rules for Jadame and other continents. | Integrated and partially consumed. New-game continent selection remains future work. |
| `Tables/Potion settings.txt`, `Reagent settings.txt`, `POTION.TXT`, `POTNOTES.TXT` | Merged item/potion behavior that changes base MM8 mechanics. | Integrated and runtime consumed for potion classification/mixing. Track in table inventory, not map fixups. |

## Decompiled MM8 Original-Vs-Patched Delta Audit

`reference/mmext-scripts/Decompiled_Scripts/mm8/` differs from `mm8orig/` for these files:

`D07`, `D22`, `D27`, `D29`, `Global`, `OUT04`, `OUT06`, `Out01`, `Out02`, `Out03`, `Out07`, `d16`, `d17`, and
`d19`.

Treat these as GrayFace/MM8Patch-style decompiled script deltas, not automatically as MMMerge map overlays. They are
still useful when validating generated MM8 event exports. Before porting an MMMerge overlay on one of these maps, check:

1. whether OpenYAMM's generated event script already matches `mm8/` rather than `mm8orig/`;
2. whether MMMerge's separate `Scripts/Maps/<map>.lua` intentionally replaces that behavior;
3. whether the desired OpenYAMM target should be a generated event correction, a supplemental overlay, or static scene
   data.

## Parity Execution Tracker

| Phase | Item | Status | Reference | Verification target |
| --- | --- | --- | --- | --- |
| 0 | Confirm original-MM8 map overlay loading model supports replacing generated events without duplicate handlers. | Done. Added MM8 overlay compile/exposure coverage in `tests/ScriptedMapRegressionTests.cpp`. | `MMERGE_MAP_FIXUP_INVENTORY.md`; MM6/MM7 overlay implementations. | Keep compile test green as new MM8 overlays are added. |
| 1 | Reusable key/once-open fixes: `d06`, `d34`, `out02` crystal, `pbp` prisons. | Done. | `reference/mmmerge/Scripts/Maps/d06.lua`, `d34.lua`, `out02.lua`, `pbp.lua`. | Scripted regressions cover each replacement event and persisted QBit/mapvar branch. |
| 1 | Small monster/NPC state repairs: `d07`, `d24`, `d38`, `d39`. | Done. | `reference/mmmerge/Scripts/Maps/d07.lua`, `d24.lua`, `d38.lua`, `d39.lua`. | Load/after-load tests cover hostility/invisibility/NPC house state. |
| 2 | Dimension Door and arena/Town Portal hooks: `out01`, `out02`, `out07`, `d42`. | Done except Breach/CrossContinents custom hook. | Map scripts plus `TownPortalSwitches.lua`. | Runtime tests cover portal UI request, tile latches, Town Portal unlocks, arena restrictions, and continent-aware arena exit. |
| 2 | Terrain and tile-sound parity: `out04`, `out06`. | Done. | `reference/mmmerge/Scripts/Maps/out04.lua`, `out06.lua`. | Terrain descriptor and footstep override assertions cover tile-set sound ids. |
| 3 | Quest quality-of-life fixes: `d19`, `out05`, `out07`, `out13`. | Done. | `reference/mmmerge/Scripts/Maps/d19.lua`, `out05.lua`, `out07.lua`, `out13.lua`. | Branch regressions cover invisible door, transformer, clear-land completion, statue spell use, gem table, and reusable cannon. |
| 4 | Custom CrossContinents/Breach content touching Jadame. | Deferred custom-content work after base MM8 fixes. | `Quest_CrossContinents.lua`, `out02.lua`, `BrAlvar.lua`, `BrBase.lua`, `Breach.lua`. | Mount custom maps as content packages, then cover Verdant/Breach entry and completion paths. |

## Explicit Non-Scope

The following MMMerge script families can affect a Jadame/MM8 playthrough but are not MM8 map fixups:

- MMExtension memory limit removals under `Scripts/Structs/After/Remove*`
- general merged item/spell/class/race/table support already tracked in `MMERGE_TXT_TABLE_INTEGRATION_INVENTORY.md`
- MM6/MM7 imported map overlays that happen to use non-prefixed filenames in the merged table
- custom CrossContinents maps `BrAlvar`, `BrBase`, and `Breach` until custom content mounting is in scope
- UI/new-game continent selector behavior unless the task is explicitly about character creation or start routing
