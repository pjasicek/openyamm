# MM7 MMMerge Fixup And Script Inventory

This inventory tracks MMMerge behavior layered on top of original MM7/Antagarich content. Sources scanned:

- `reference/mmmerge/Scripts/Maps/*.lua`
- `reference/mmmerge/Scripts/Global/*.lua`
- `reference/mmmerge/Scripts/General/*.lua`
- `reference/mmmerge/Data/Tables/*.txt`
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/*.txt`
- `reference/mmext-scripts/Decompiled_Scripts/mm7orig/`

Do not copy MMMerge Lua into OpenYAMM. Treat it as reference behavior and implement through generated event overlays,
scene overlays, typed table consumers, or shared gameplay systems.

## Summary

- MMMerge has 26 MM7 map overlay scripts:
  - 20 prefixed MM7 maps: `7d*.lua`, `7out*.lua`, `7nwc.lua`
  - 6 MM7 maps with non-prefixed merged names: `d03.lua`, `out09.lua`, `out11.lua`, `out12.lua`, `out14.lua`,
    `mdt15.lua`
- Static scene/data fixups already identified in the broad map inventory:
  - `7d05`: arena restrictions and silent doors
  - `7d06`: Temple of the Moon door initial states
  - `7d23`: Lincoln containment actor group state
- The remaining MM7 overlays are mostly runtime behavior:
  - Harmondale castle/rebuild/invasion/judge state
  - MM7 good/evil faction progression gates
  - NPC follower migration for rescue quests
  - Dimension Door/Town Portal hooks
  - MM7 endgame/cross-continent state
  - special item behavior and map-specific quest repairs

## Map Overlay Inventory

| Map script | MM7 map | MMMerge behavior | OpenYAMM work item |
| --- | --- | --- | --- |
| `7d05.lua` | The Arena | Reroutes NPC 639 topics, silences all arena doors, blocks saving and Lloyd's Beacon. | Keep as arena runtime restriction plus NPC/event metadata. Already tracked as done in `MMERGE_MAP_FIXUP_INVENTORY.md`; verify NPC 639 topic routing remains correct after dialogue changes. |
| `7d06.lua` | The Temple of the Moon | On load, forces doors 5-8 closed and doors 9-10 open. | Static scene mechanism initial-state fix. Already baked into MM7 scene/exporter path. |
| `7d08.lua` | The Tularean Caves | Event 376 adds Loren Steel follower 410 if QBit 1695 is set. Other Loren cleanup lives in `StdQuestsFollowers.lua`. | Implemented in `7d08_mmmerge.lua`; covered by scripted map regression. |
| `7d23.lua` | The Lincoln | Makes monster group 56 non-hostile and invisible; replaces exit event 501 with a wetsuit check before travel to Shoals. | Implemented in `assets_dev/worlds/mm7/events/maps/7d23_mmmerge.lua`; covered by scripted map regression. |
| `7d24.lua` | Stone City | Replaces throne room event 416 to gate on QBit 647 instead of Award 3; clears QBit 658 when exiting Dwarf King NPC 398. | Implemented in `7d24_mmmerge.lua`; covered by scripted map regression. |
| `7d25.lua` | Celeste | After load, if QBit 612 is set, sets groups 55-57 hostile. | Implemented in `7d25_mmmerge.lua`; covered by scripted map regression. |
| `7d27.lua` | Colony Zod | Replaces event 376 to award item 1463, hide sprite/facet, set QBit 752, then speak NPC 626. | Implemented in `7d27_mmmerge.lua`; covered by scripted map regression. |
| `7d29.lua` | Castle Harmondale | Removes Golem follower on quest completion; makes rest free after QBit 610; resolves Mercenary Guild invasion monster state/bank gold; marks CrossContinents Antagarich complete when QBit 633 is set. | Implemented local follower cleanup, free rest, Mercenary Guild invasion load/leave state, and CrossContinents Antagarich completion marker in `7d29_mmmerge.lua`. |
| `7d30.lua` | Castle Lambent | Replaces throne room event 416 with faction/enemy detector gate; marks CrossContinents Antagarich complete when QBit 633 is set. | Implemented throne-room faction/enemy detector gate and CrossContinents Antagarich completion marker in `7d30_mmmerge.lua`. |
| `7d34.lua` | The Red Dwarf Mines | Events 376-382 add rescued dwarf followers 399-405 when item 1431 is present. | Implemented in `7d34_mmmerge.lua`; basic add/gate path is covered by scripted map regression. Global follower lifecycle remains tracked separately. |
| `7d36.lua` | Tunnels to Eeofol | Replaces event 501 with corrected Land of the Giants coordinates. | Implemented in `7d36_mmmerge.lua`; covered by scripted map regression. |
| `7d37.lua` | The Haunted Mansion | Replaces event 376 to pick up portrait item 1423 once, change texture `t2bs`, set QBit 778, hide hint using `mapvars.PortraitTaken`. | Implemented in `7d37_mmmerge.lua`; covered by scripted map regression. |
| `7nwc.lua` | The Strange Temple | Replaces exit event 501 to return to `vars.TempleInABottleEnteredFrom`, else default to Harmondale. | Implemented in `7nwc_mmmerge.lua`; Temple in a Bottle persists the return destination in runtime/save state and the fallback Harmondale exit remains covered. |
| `7out01.lua` | Emerald Island | Removes Arcomage from Emerald Island taverns; tavern topics become rent room, buy food, learn. | Implemented by `7out01_mmmerge.lua` house-topic filter; verified by scripted regression. |
| `7out02.lua` | Harmondale | Removes Judge followers at event 37; replaces Castle Harmondale entrance 301; runs Mercenary Guild invasion timing; gives scavenger-hunt advertisement near coordinates; rewrites Judge Grey death timing to be unconditional within six months after rebuild. | Implemented in `7out02_mmmerge.lua`; event replacements, invasion/judge load state, and major branches covered. Proximity timer is registered. |
| `7out03.lua` | Erathia | Changes boat/transport index depending on whether party visited Emerald Island; gives scavenger-hunt advertisement near coordinates. | Implemented in `7out03_mmmerge.lua`; scavenger timer and persistent transport route override are covered. |
| `7out04.lua` | The Tularean Forest | Adds Dimension Door trigger on tile/model/facet; replaces Clanker's Lab event 503; replaces artifact messenger/battle event 401 and summons faction battle monsters. | Implemented in `7out04_mmmerge.lua`; event `504`, Clanker's Lab, messenger item/QBits, and corrected summon groups covered. Facet/tile trigger is registered by event id; exported face binding still needs visual/editor audit if missing in map data. |
| `7out05.lua` | Deyja | Local hostile table override: `HostileTxt[91][0] = 0`; sets monster groups 55/56 hostile based on QBit 611; on leaving NPC 461, summons hostile group 59 if QBit 761 not set. | Implemented in `7out05_mmmerge.lua`; local monster relation, group hostility, and NPC-exit summon covered. |
| `7out13.lua` | Tatalia | Adds Adventurer's Inn house 1607 at event/house 82. | Implemented in `7out13_mmmerge.lua`; event `82` house entry covered. |
| `7out15.lua` | Shoals | On load sets party faces to 30; restores faces on leave; blocks actions/item use while underwater; auto-travels to Avlee when Z > 3900. | Implemented in `7out15_mmmerge.lua`; portrait override/restore and action hook covered, surfacing timer registered. |
| `d03.lua` | Castle Gloaming | Replaces throne room event 5 with faction/enemy detector gate; marks CrossContinents Antagarich complete when QBit 633 is set. | Implemented throne-room faction/enemy detector gate and CrossContinents Antagarich completion marker in `d03_mmmerge.lua`. |
| `out09.lua` | Evenmorn Island | Shows obelisk treasure only at midnight after QBits 676-689; adds Dimension Door event 6 and proximity timer around coordinates. | Implemented in `out09_mmmerge.lua`; Dimension Door event and daytime treasure hide covered. Runtime proximity timer registered. |
| `out11.lua` | The Barrow Downs | Replaces event 501 with corrected Stone City entrance coordinates/house id. | Implemented in `out11_mmmerge.lua`; covered by scripted map regression. |
| `out12.lua` | The Land of the Giants | Replaces load event 1 with delayed Xenofex/control-cube behavior: if QBit 616 or 635 and not 775, set greeting, put item 866 in mouse, speak NPC 462. | Implemented in `out12_mmmerge.lua`; covered by scripted map regression. |
| `out14.lua` | Avlee | Walk-to-map left side checks every party member has wetsuit item 1406 equipped or in inventory before sending to Shoals. | Implemented in `out14_mmmerge.lua` through the shared map-transition hook; blocked/allowed branches covered. |
| `mdt15.lua` | The Small House | On map refill, resets the first two monsters so control cube item 1477 and blaster item 866 can be acquired again. | Implemented in `mdt15_mmmerge.lua`; map-refill hook and dual guaranteed monster drops are covered by scripted map regression. |

## Global MM7 Script Inventory

| Source | MM7 behavior | OpenYAMM work item |
| --- | --- | --- |
| `Scripts/General/10_Continents.lua` | Tracks current/previous continent and map using `TownPortalControls.MapOfContinent`; emits continent change events. | Keep active-world/continent context authoritative. Existing continent settings consumer covers part of this; ensure map load events expose previous/current continent transitions. |
| `Scripts/General/MenuChooseContinent.lua` | Parses `Continent settings.txt`; defines Antagarich death/start maps: Emerald Island start and Harmondale fallback; plays `7intro` for MM7 start. | New game continent chooser and death-map routing are separate tasks. Death movie support is partially implemented; start-map routing should use the table, not hardcoded values. |
| `Scripts/General/Weather.lua` | Uses `Bolster - maps.txt` and `Continent settings.txt` to choose Antagarich sky/weather and per-map custom sky such as Bracada `7plansky3`. | Weather/sky consumer is partially implemented. Verify all Antagarich map rows with weather/custom sky are consumed and that weather effects match current particle system. |
| `Scripts/Global/TownPortalSwitches.lua` | Defines MM7 map range 62-136 as Antagarich; treats `7d05.blv` as arena; blocks save/Lloyd in arena; supports special global Dimension Door screen. | Map range/continent resolution and arena restriction must be shared runtime behavior. Dimension Door is implemented separately; verify MM7 hooks invoke it. |
| `Scripts/Global/StdQuestsFunctions.lua` | Replaces Malwick wand grant with a charged identified wand in mouse item; summons Malwick ambush monsters; rewrites Cast Off global 783 to move to Harmondale; extends Arcomage win tracking; blocks Antagarich Arcomage without deck; adds Antagarich guild join globals 1150-1160; fixes MM7 endgame QBits 642/783. | Implemented for original-MM7 parity: Malwick events `513/514/769`, Cast Off `783`, endgame events `920/922`, Arcomage deck restriction, and all-tavern win QBit `750` are covered. Guild join topics are handled by native dialogue/house logic from merged tables. |
| `Scripts/Global/StdQuestsFollowers.lua` | Handles Red Dwarf Mines rescued dwarf followers 399-405; Loren/fake Loren followers 410-411; Judge followers 416-417. | Implemented in `assets_dev/worlds/mm7/events/Global_mmmerge.lua`; covered by scripted map regression for dwarf, Loren/fake Loren, and Judge follower state. |
| `Scripts/Global/PromotionTopics.lua` | Replaces Antagarich class promotion topic flows for Archer, Cleric, Druid, Paladin, Monk, Knight, Ranger, Thief, Wizard, including light/dark branch handling and merged-class compatibility. | Implemented first-pass MMerge promotion overlay for Antagarich events `795-853` plus blaster topic `950`. Uses the shared Lua class/promotion API and merged `class_extra.txt` metadata, so promoted classes can be table/mod driven. Lich ritual now consumes member-owned jars and applies race/sex-aware Lich identity plus Lich resistance/immunity state. |
| `Scripts/Global/Quest_DragonHatchling.lua` | Makes warlock and arch druid promotion quests accessible from either light/dark path after MM6/MM7 cross-continent state; turns the dragon hatchling into follower/party-member flow with feeding, naming, dismissal, skill/SP bonuses. | Implemented cross-path Arch Druid/Warlock entry and functional hatchling feed/grow/join-as-follower flow. Full custom party-member naming/dismissal/skill-aura behavior remains future roster/party lifecycle work. |
| `Scripts/Global/Quest_CrossContinents.lua` | Uses Antagarich completion QBit 783; places Verdant at Harmondale; grants connector stone on `7out02.odm`; changes Verdant hint topic based on MM7 light/dark QBits 611/612. | Implemented Verdant intro/topics, Dimension Door cross-continent gate after `GotMainQuest`, continent completion/reward tracking, connector stone grant/use/recharge state, and final quest QBit start. Shared Breach maps are mounted under `worlds/mmmerge`; detailed final quest mechanics and later Saving Goobers extension remain future custom-content work. |
| `Scripts/General/UsableItems.lua` | Item 1452 sends party to `7nwc.blv` and stores return position; Dimension Door scroll invokes global Dimension Door. | Implemented: Temple in a Bottle stores a saved return location and sends the party to `7nwc.blv`; `7nwc` returns to that location or falls back to Harmondale; Dimension Door scroll opens the same portal UI as the HUD button. |
| `Scripts/General/MiscTweaks.lua` | Provides corrected transition text ids for MM7 dungeons: `7d14`, `7d15`, `7d16`, `7d18`, `7d35`, `7d36`, `7d37`, `mdt09`, `mdt10`, `mdt14`, all `mdk*`/`mdr*`/`mdt*` barrows. | Prefer data-driven transition text mapping from MMerge table/export. Avoid ad hoc fallback labels. |
| `Scripts/General/NPCMercenaries.lua` | Antagarich portrait exceptions exclude MM7/MM6 special faces from random mercenary generation. | Runtime generated mercenary support should consume `Character selection.txt`/portrait metadata rather than hardcoded exceptions. |
| `Scripts/General/AdaptiveMonstersStats.lua` | Bolster behavior includes special handling relevant to MM7 static monsters, e.g. Tularean Forest trees. | Bolster runtime consumer remains a separate shared system. Ensure MM7 map rows in `bolster_maps.txt` and monster-kind flags are consumed before tuning. |

## MMerge Data Table Inputs For MM7

These tables are part of the MM7 fixup surface because the scripts above read them or because they replace original
MM7 table state in the merged base.

| Table | MM7/Antagarich scope | OpenYAMM state / next step |
| --- | --- | --- |
| `Data/Tables/Continent settings.txt` | Row `2 Antagarich`: death movie `7losegame`, water `7wtrtyl`, start map `7out01.odm`, post-Emerald fallback `7out02.odm`, sky set. | Integrated and partially consumed. Verify death spawn routing and new-game start routing separately. |
| `Data/Tables/TownPortalSwitch.txt` | `@ Antagrich` block: Castle Harmondale, Tularean Forest, Steadwick, Nighon, Celeste, The Pit; QBits 718-723. | Data is integrated. Verify Town Portal UI unlocks and labels use this block for continent 2. |
| `Data/Tables/Outdoor travels.txt` | Antagarich outdoor edge travel for `7out02`, `7out03`, `7out04`, `7out05`, `7out06`, `out11`, `7out13`, `out14`, `7out15`. | Integrated and consumed. Map-specific Shoals/wetsuit travel gates are implemented through map-transition hooks. |
| `Data/Tables/Transport Locations.txt` | Rows 25-59 are MM7 boat/stable/arena routes; rows 79 and 97 are long cross-continent routes using MM7 maps/QBits. | Integrated and consumed by house rules/routes. Erathia's Emerald-Island-dependent Royal Steeds route override is implemented in `7out03_mmmerge.lua` and persisted in save state. |
| `Data/Tables/Bolster - maps.txt` | Rows 62-136 are Antagarich map settings: continent id, bolster kind, spells/summons/weather flags, custom sky. | Integrated with typed loader. Runtime bolster consumer pending; weather/custom sky consumer partially active. |
| `Data/mmmerge.T.lod/MapStats.txt` | Rows 62-136 define merged MM7 map ids and filenames. | Integrated as `assets_dev/engine/data_tables/map_stats.txt`. Used as flat base map registry. |
| `Data/Tables/House Movies.txt` | MM7 house/dungeon video stems and house sound groups. | Integrated and consumed for houses. Verify MM7 indoor transition videos still use map/transition data rather than MM8 fallback. |
| `Data/Tables/House exits.txt` | Merged house exit picture and coordinate overrides, including MM7 exits. | Integrated and consumed. Keep as authoritative for direct house exits. |
| `Data/Tables/House rules.txt` | MM7 tavern/boat/stable/shop/training/Arcomage rules. | Integrated and consumed in house interaction; map-level Arcomage restrictions still need script parity. |
| `Data/mmmerge.T.lod/Quests.txt` | Global QBit registry, including MM7 and MMerge-added high bits. | Integrated. Use named comments/registry when porting overlays; do not invent local QBit aliases. |
| `Data/mmmerge.T.lod/NPCData.txt`, `NPCGreet.txt`, `NPCText.txt`, `NPCTopic.txt` | Merged MM7 NPC ids, greetings, text, topics used by global scripts. | Integrated. Original MM7 follower/guild/promotion parity and first-pass merged-class promotion topics are covered; exact legacy text selection can be tightened later if a topic still shows incorrect copy. |
| `Data/Tables/Teacher autonotes.txt` and news/profession tables | MM7 teacher/autonote/news behavior on maps and fullscreen map. | Integrated per base table inventory. Keep fullscreen/minimap marker implementation data-driven. |

## Parity Execution Tracker

Use this section as the active implementation tracker. Each item should be implemented as an OpenYAMM overlay,
table-driven consumer, scene/exporter fix, or shared gameplay behavior. The MMMerge files are references only; do not
copy their Lua into OpenYAMM.

| Phase | Item | Status | MMMerge reference | OpenYAMM target / verification |
| --- | --- | --- | --- | --- |
| 0 | Generic overlay primitives: replacement, load/leave/timer, NPC enter/exit, house topic, rest-cost, held item, named vars, local relations. | Partially implemented. Map-refill, map-transition, party portrait mutation hooks, and table-backed class/promotion Lua helpers are available; broader roster lifecycle remains deferred. | `reference/mmmerge/Scripts/Maps/*.lua`, `reference/mmmerge/Scripts/Global/*.lua` | Shared `EventRuntime`/gameplay hooks. Add focused tests when each deferred hook is first needed. |
| 0 | Arena restrictions, NPC 639 routing, silent arena doors. | Mostly implemented/tracked elsewhere; verify after dialogue changes. | `reference/mmmerge/Scripts/Maps/7d05.lua`, `reference/mmmerge/Scripts/Global/TownPortalSwitches.lua` | Existing arena restriction path plus map/dialogue metadata; add regression for NPC `639` and save/Lloyd restrictions. |
| 0 | Temple of the Moon initial door states. | Baked into scene/exporter path; verify in editor/game. | `reference/mmmerge/Scripts/Maps/7d06.lua` | Scene mechanism initial states; headless/editor check doors `5-10`. |
| 0 | Continent, weather, town portal, start/death routing data. | Partially implemented through table consumers. | `reference/mmmerge/Scripts/General/10_Continents.lua`, `MenuChooseContinent.lua`, `Weather.lua`, `Scripts/General/1_TownPortalSwitch.lua`, `Scripts/Global/TownPortalSwitches.lua` | `Continent settings.txt`, `TownPortalSwitch.txt`, `Bolster - maps.txt`; verify Antagarich sky/weather/death/start/Town Portal unlocks. |
| 1 | Lincoln exit wetsuit gate and status text. | Implemented and tested. Group-state supplement remains in the same overlay. | `reference/mmmerge/Scripts/Maps/7d23.lua` | `assets_dev/worlds/mm7/events/maps/7d23_mmmerge.lua`; event `501`; blocked/allowed travel to Shoals covered. |
| 1 | Stone City throne room and Dwarf King exit cleanup. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d24.lua` | `7d24` overlay; event `416`; NPC exit hook for NPC `398`; QBit `658` clear covered. |
| 1 | Celeste hostile groups after Light path state. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d25.lua` | `7d25` load overlay; QBit `612`; groups `55-57`; load-state hostility covered. |
| 1 | Colony Zod quest item pickup. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d27.lua` | `7d27` overlay event `376`; item `1463`, QBit `752`, sprite/facet hide, NPC `626`; activation covered. |
| 1 | Red Dwarf Mines rescued dwarf pickups. | Implemented and tested, including global follower cleanup. | `reference/mmmerge/Scripts/Maps/7d34.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | `7d34` events `376-382`; followers `399-405`; item `1431` gate and Dwarf King cleanup covered. |
| 1 | Tunnels to Eeofol corrected travel. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d36.lua` | `7d36` event `501`; destination map/coordinates covered. |
| 1 | Haunted Mansion portrait pickup. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d37.lua` | `7d37` event `376`; item `1423`, QBit `778`, named mapvar, texture/facet state covered. |
| 1 | Barrow Downs Stone City entrance correction. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/out11.lua` | `out11` event `501`; destination and house id covered. |
| 1 | Land of the Giants Xenofex/control-cube delayed behavior. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/out12.lua` | `out12` after-load overlay; NPC `462`, item `866`, QBits `616/635/775`; held item and greeting covered. |
| 1 | Small House map-refill monster item reset. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/mdt15.lua` | `mdt15` refill overlay; reset first two monsters for items `1477` and `866`; refill regression covered. |
| 2 | Tularean Caves Loren Steel follower. | Implemented and tested. | `reference/mmmerge/Scripts/Maps/7d08.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | `7d08` event `376`; follower `410`, QBit `1695`; pickup and already-active branch covered. |
| 2 | Global rescued follower lifecycle. | Implemented and tested for dwarf, Loren/fake Loren, and Judge follower transitions. | `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | Global MM7 overlay; dwarf/Loren/Judge followers `399-417`; add/remove and NPC-enter cleanup covered. |
| 3 | Emerald Island tavern topics without Arcomage. | Done. | `reference/mmmerge/Scripts/Maps/7out01.lua` | `7out01_mmmerge.lua`; verified rent/buy food/learn topics only. |
| 3 | Castle Harmondale free rest and castle-local state. | Done for original MM7-local behavior. CrossContinents marker deferred. | `reference/mmmerge/Scripts/Maps/7d29.lua` | `7d29_mmmerge.lua`; QBit `610` rest cost, Golem follower `395`, invasion group `60`, bank gold, and leave completion covered. |
| 3 | Antagarich Arcomage deck restriction and win tracking. | Done. | `reference/mmmerge/Scripts/Global/StdQuestsFunctions.lua` | `Global_mmmerge.lua`; item `1453`; tested top-level and play-topic blocking without deck. `Party::recordArcomageWin` sets QBit `750` after wins at houses `240`-`252`. |
| 4 | Harmondale outdoor rebuild, judge, invasion, scavenger advertisement. | Done for original MM7-local behavior. CrossContinents custom Verdant/stone content remains deferred. | `reference/mmmerge/Scripts/Maps/7out02.lua`, `reference/mmmerge/Scripts/Global/Quest_CrossContinents.lua` | `7out02_mmmerge.lua`; event `37`, event `301`, invasion/judge load state, NPC movement/greetings, and proximity timer registration covered. |
| 4 | Castle Lambent faction gate. | Done for original MM7-local behavior. CrossContinents marker deferred. | `reference/mmmerge/Scripts/Maps/7d30.lua` | `7d30_mmmerge.lua`; event `416`; QBits `611/612`; blocked/allowed throne-room flow covered. |
| 4 | Castle Gloaming faction gate. | Done for original MM7-local behavior. CrossContinents marker deferred. | `reference/mmmerge/Scripts/Maps/d03.lua` | `d03_mmmerge.lua`; event `5`; QBits `611/612/710`; blocked/allowed throne-room flow covered. |
| 4 | Tularean Forest Dimension Door, Clanker's Lab, artifact messenger/battle. | Done for event behavior; facet/tile authored trigger still needs map-data audit if event `504` is not bound in exported data. | `reference/mmmerge/Scripts/Maps/7out04.lua` | `7out04_mmmerge.lua`; events `401`, `503`, `504`; QBits, NPC movement, item grant, and summon groups covered. |
| 4 | Deyja local relation and post-NPC hostile summon. | Done. | `reference/mmmerge/Scripts/Maps/7out05.lua` | `7out05_mmmerge.lua`; HostileTxt row `91`, groups `55/56/59`, NPC `461`, QBit `761` covered. |
| 4 | Tatalia Adventurer's Inn house/event addition. | Done. | `reference/mmmerge/Scripts/Maps/7out13.lua` | `7out13_mmmerge.lua`; event/house `82` resolves to house `1607`. |
| 5 | Erathia transport rewrite and scavenger advertisement. | Done. | `reference/mmmerge/Scripts/Maps/7out03.lua` | `7out03_mmmerge.lua`; proximity grant and persistent Royal Steeds route override covered. |
| 5 | Evenmorn obelisk treasure and Dimension Door proximity. | Done. | `reference/mmmerge/Scripts/Maps/out09.lua` | `out09_mmmerge.lua`; event `6`, QBits `676-689`, daytime treasure hide, and proximity timer registration covered. |
| 5 | Avlee to Shoals wetsuit edge-travel gate. | Done. | `reference/mmmerge/Scripts/Maps/out14.lua` | `out14_mmmerge.lua`; item `1406` per active member; blocked/allowed edge travel covered. |
| 5 | Shoals underwater face/action restrictions and auto-travel. | Done for scripted behavior. | `reference/mmmerge/Scripts/Maps/7out15.lua` | `7out15_mmmerge.lua`; portrait `30` load/restore and action block covered; Z-height auto-travel timer registered. |
| 6 | Malwick wand, ambush, Cast Off, MM7 endgame, guild joins. | Done for original MM7 parity. | `reference/mmmerge/Scripts/Global/StdQuestsFunctions.lua` | `Global_mmmerge.lua`; events `513/514/769/783/920/922` covered. Native guild join support consumes merged dialogue/house data. |
| 6 | Antagarich promotion topics. | Implemented first-pass MMerge overlay. | `reference/mmmerge/Scripts/Global/PromotionTopics.lua` | `Global_mmmerge.lua` replaces events `795-853` and `950`; class changes use the shared Lua promotion API and merged class metadata. Knight/Champion, cross-path Arch Druid, and race-aware Lich jar transformation coverage is in scripted regression tests. |
| 7 | Temple in a Bottle return and Dimension Door item use. | Done. | `reference/mmmerge/Scripts/General/UsableItems.lua`, `reference/mmmerge/Scripts/Maps/7nwc.lua` | Item runtime plus `7nwc` event `501`; return-position persistence, fallback exit, and Dimension Door scroll behavior covered. |
| 7 | Corrected MM7 transition text ids. | Deferred data audit. | `reference/mmmerge/Scripts/General/MiscTweaks.lua` | Current transition UI resolves MM6/MM7 titles/videos through map stats and house/movie tables. If a specific dungeon still shows a wrong prompt/video, add a data-driven map-to-transition-text table instead of hardcoding event fallbacks. |
| 8 | CrossContinents shared bridge content. | Implemented first playable slice plus shared Breach map mounting. | `reference/mmmerge/Scripts/Global/Quest_CrossContinents.lua`, `reference/mmmerge/Scripts/Maps/Breach.lua`, `reference/mmmerge/Scripts/Maps/BrAlvar.lua`, `reference/mmmerge/Scripts/Maps/BrBase.lua` | `Global_mmmerge.lua` plus shared item use: Verdant intro/topics, `GotMainQuest` Dimension Door gate, connector stone, completion rewards, final quest start, and `worlds/mmmerge` Breach map loading are covered. Detailed Breach final quest mechanics and later Saving Goobers content remain separate custom-content work. |
| 8 | Dragon Hatchling custom quest/party-member flow. | Implemented first playable slice. | `reference/mmmerge/Scripts/Global/Quest_DragonHatchling.lua` | `Global_mmmerge.lua`: cross-path promotion entry plus feed/grow/join-as-follower behavior is covered. Full named roster/party-member dragon and skill/SP aura remain future party lifecycle work. |

## MMMerge Source Reference Map

Use these references when implementing each parity family. Prefer the map/global script named here, then cross-check
original event intent with `reference/mmext-scripts/Decompiled_Scripts/mm7orig/` when an event replacement changes an
original MM7 event.

| Work family | Primary MMMerge references | Secondary data references |
| --- | --- | --- |
| Arena restrictions and silent doors | `reference/mmmerge/Scripts/Maps/7d05.lua`, `reference/mmmerge/Scripts/Global/TownPortalSwitches.lua` | `reference/mmmerge/Data/Tables/TownPortalSwitch.txt` |
| Temple of the Moon door initial state | `reference/mmmerge/Scripts/Maps/7d06.lua` | MM7 scene/exported mechanism data |
| Tularean Caves Loren follower | `reference/mmmerge/Scripts/Maps/7d08.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCData.txt` |
| Lincoln/Shoals wetsuit flow | `reference/mmmerge/Scripts/Maps/7d23.lua`, `reference/mmmerge/Scripts/Maps/out14.lua`, `reference/mmmerge/Scripts/Maps/7out15.lua` | `reference/mmmerge/Data/Tables/Outdoor travels.txt`, `reference/mmerge_data_forus/Data/mmmerge.T.lod/Quests.txt` |
| Stone City and Dwarf King state | `reference/mmmerge/Scripts/Maps/7d24.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCText.txt`, `NPCTopic.txt` |
| Celeste/Lambent/Gloaming faction gates | `reference/mmmerge/Scripts/Maps/7d25.lua`, `reference/mmmerge/Scripts/Maps/7d30.lua`, `reference/mmmerge/Scripts/Maps/d03.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/Quests.txt` |
| Colony Zod and Land of the Giants item/NPC repairs | `reference/mmmerge/Scripts/Maps/7d27.lua`, `reference/mmmerge/Scripts/Maps/out12.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCData.txt`, `Quests.txt` |
| Harmondale castle/rebuild/invasion/judge | `reference/mmmerge/Scripts/Maps/7d29.lua`, `reference/mmmerge/Scripts/Maps/7out02.lua`, `reference/mmmerge/Scripts/Global/Quest_CrossContinents.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/Quests.txt`, `NPCGreet.txt`, `NPCData.txt` |
| Red Dwarf Mines rescued dwarves | `reference/mmmerge/Scripts/Maps/7d34.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFollowers.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCData.txt` |
| Eeofol and Barrow Downs corrected map moves | `reference/mmmerge/Scripts/Maps/7d36.lua`, `reference/mmmerge/Scripts/Maps/out11.lua` | `reference/mmmerge/Data/Tables/House exits.txt`, MM7 decompiled map events |
| Haunted Mansion portrait | `reference/mmmerge/Scripts/Maps/7d37.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/Quests.txt` |
| Emerald Island tavern and Malwick | `reference/mmmerge/Scripts/Maps/7out01.lua`, `reference/mmmerge/Scripts/Global/StdQuestsFunctions.lua` | `reference/mmmerge/Data/Tables/House rules.txt`, `NPCText.txt`, `NPCTopic.txt` |
| Erathia route/scavenger and Tularean Forest battle | `reference/mmmerge/Scripts/Maps/7out03.lua`, `reference/mmmerge/Scripts/Maps/7out04.lua` | `reference/mmmerge/Data/Tables/Transport Locations.txt`, `Outdoor travels.txt` |
| Deyja hostile relation override | `reference/mmmerge/Scripts/Maps/7out05.lua` | Merged monster hostility/monster tables under `reference/mmmerge/Data/Tables/` |
| Tatalia Adventurer's Inn | `reference/mmmerge/Scripts/Maps/7out13.lua` | `reference/mmmerge/Data/Tables/House exits.txt`, `House rules.txt` |
| Evenmorn obelisk and Dimension Door | `reference/mmmerge/Scripts/Maps/out09.lua`, `reference/mmmerge/Scripts/Global/TownPortalSwitches.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/Quests.txt` |
| Small House refill reset | `reference/mmmerge/Scripts/Maps/mdt15.lua` | Monster/item tables under `reference/mmerge_data_forus/Data/mmmerge.T.lod/` |
| Temple in a Bottle | `reference/mmmerge/Scripts/General/UsableItems.lua`, `reference/mmmerge/Scripts/Maps/7nwc.lua` | Item table rows for item `1452` |
| Promotion topics | `reference/mmmerge/Scripts/Global/PromotionTopics.lua` | `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCText.txt`, `NPCTopic.txt`, `Quests.txt` |
| Dragon Hatchling custom quest | `reference/mmmerge/Scripts/Global/Quest_DragonHatchling.lua` | Merged NPC/quest/class/race tables |
| Continent, town portal, weather, and start/death routing | `reference/mmmerge/Scripts/General/10_Continents.lua`, `MenuChooseContinent.lua`, `Weather.lua`, `Scripts/General/1_TownPortalSwitch.lua`, `Scripts/Global/TownPortalSwitches.lua` | `reference/mmmerge/Data/Tables/Continent settings.txt`, `TownPortalSwitch.txt`, `Bolster - maps.txt`, `MapStats.txt` |

## General Verification Rules

- For event overlays, add a regression that confirms the replacement event id exists and changes the expected
  QBits/items/NPC topics/map move.
- For load/leave/timer overlays, add focused headless coverage for the runtime state change when practical.
- For table consumers, assert the merged MM7 rows are loaded by id/name rather than hardcoded by map filename.
- For travel fixes, assert target map, coordinates, house id/icon, and whether a transition prompt should appear.
- For follower and held-item behavior, assert save/load persistence where the state can survive a map transition.

## Explicit Non-Scope

The following MMMerge script families affect MM7 indirectly but are not MM7-specific fixups:

- MMExtension memory limit removals under `Scripts/Structs/After/Remove*`
- base UI/input patches that only compensate for MM8 executable limits
- general merged item/spell/class/race support already tracked in `MMERGE_TXT_TABLE_INTEGRATION_INVENTORY.md`
- custom CrossContinents maps mounted under shared `worlds/mmmerge` content, with detailed final quest mechanics still pending
