# MM7 Script And Mechanics Missing Inventory

This inventory answers: after the MM7 MMMerge map/global overlay work, what MM7-visible script or mechanics behavior
might still be missing?

Sources scanned:

- `reference/mmmerge/Scripts/Maps/*.lua`
- `reference/mmmerge/Scripts/Global/*.lua`
- `reference/mmmerge/Scripts/General/*.lua`
- `reference/mmext-scripts/Decompiled_Scripts/mm7orig/`
- current OpenYAMM overlays under `assets_dev/worlds/mm7/events/`
- current shared runtime/tests under `game/` and `tests/`

Do not copy MMMerge Lua into OpenYAMM. Use these scripts only as behavior references and implement through generated
event overlays, typed table consumers, or shared gameplay systems.

Status values:

- `Done`: implemented and covered well enough for this inventory.
- `Mostly done`: core runtime/data behavior exists, but some presentation or call-site wiring is still pending.
- `Verify`: believed implemented, but exact text/UX/gameplay should still be spot-checked.
- `Pending`: worthwhile runtime/data work that is not fully implemented.
- `Deferred`: valid MMMerge/custom-content work, but outside core original-MM7 parity.
- `Not MM7-core`: global MMerge convenience/editor/mod infrastructure that can wait unless a user-facing need appears.

## Short Answer

Core original-MM7 map script parity is effectively closed. All 26 MM7 MMMerge map overlays have OpenYAMM coverage or a
scene/data equivalent.

The remaining meaningful MM7-visible gaps are not map overlays. Most high-value shared mechanics now have core runtime
support; the remaining work is either follow-up call-site wiring, lower-priority audits, or custom MMerge systems:

- extra artifact/item effects and artifact uniqueness,
- exact jail/throne transition presentation,
- remaining spell-tweak audit for Mass Distortion, GM Town Portal, Shield, monster Power Cure, and disabled monster spells,
- remaining NPC follower/hireling call-site wiring for skill/stat/resistance bonuses,
- monster death-spawn/special-action behavior and indoor activation/stuck cleanup,
- full zombie player portrait/temple/healing behavior,
- generated mercenary eligibility metadata,
- exact NPC text spot-checks,
- full Dragon Hatchling roster-member lifecycle,
- detailed CrossContinents/Breach/Saving Goobers final quest mechanics.

## Original MM7 Map Overlay Coverage

| Source | Map / behavior family | Status | Notes |
| --- | --- | --- | --- |
| `7d05.lua` | Arena NPC 639 routing, silent doors, save/Lloyd block | Done | Covered through arena restrictions, scene data, and dialogue regression. |
| `7d06.lua` | Temple of the Moon door initial states | Done | Baked into scene/exporter path and regression-covered. |
| `7d08.lua` | Tularean Caves Loren Steel follower | Done | `7d08_mmmerge.lua`; scripted regression covered. |
| `7d23.lua` | Lincoln local monster state and wetsuit exit gate | Done | `7d23_mmmerge.lua`; scripted regression covered. |
| `7d24.lua` | Stone City throne gate and Dwarf King follower cleanup | Done | `7d24_mmmerge.lua`; scripted regression covered. |
| `7d25.lua` | Celeste light-path hostile groups | Done | `7d25_mmmerge.lua`; scripted regression covered. |
| `7d27.lua` | Colony Zod item/NPC pickup repair | Done | `7d27_mmmerge.lua`; scripted regression covered. |
| `7d29.lua` | Castle Harmondale rest, invasion, Golem cleanup, CrossContinents marker | Done | `7d29_mmmerge.lua`; original-MM7 behavior covered. |
| `7d30.lua` | Castle Lambent faction gate and CrossContinents marker | Done | `7d30_mmmerge.lua`; scripted regression covered. |
| `7d34.lua` | Red Dwarf Mines rescued dwarf followers | Done | `7d34_mmmerge.lua`; scripted regression covered. |
| `7d36.lua` | Eeofol corrected travel coordinates | Done | `7d36_mmmerge.lua`; scripted regression covered. |
| `7d37.lua` | Haunted Mansion portrait pickup/mapvar/texture state | Done | `7d37_mmmerge.lua`; scripted regression covered. |
| `7nwc.lua` | Strange Temple / Temple in a Bottle return | Done | `7nwc_mmmerge.lua`; return state is persisted. |
| `7out01.lua` | Emerald Island tavern Arcomage topic removal | Done | `7out01_mmmerge.lua`; scripted regression covered. |
| `7out02.lua` | Harmondale rebuild, Judge, invasion, scavenger advert | Done | `7out02_mmmerge.lua`; major branches covered. |
| `7out03.lua` | Erathia route override and scavenger advert | Done | `7out03_mmmerge.lua`; persistent route override covered. |
| `7out04.lua` | Tularean Forest Dimension Door, Clanker's Lab, artifact battle | Done | `7out04_mmmerge.lua`; scene face binding and event coverage are in regression. |
| `7out05.lua` | Deyja local relation and post-NPC hostile summon | Done | `7out05_mmmerge.lua`; scripted regression covered. |
| `7out13.lua` | Tatalia Adventurer's Inn house addition | Done | `7out13_mmmerge.lua`; scripted regression covered. |
| `7out15.lua` | Shoals underwater face/action restrictions and auto-travel | Done | `7out15_mmmerge.lua`; hooks registered and covered. |
| `d03.lua` | Castle Gloaming faction gate and CrossContinents marker | Done | `d03_mmmerge.lua`; scripted regression covered. |
| `out09.lua` | Evenmorn obelisk and Dimension Door proximity | Done | `out09_mmmerge.lua`; scripted regression covered. |
| `out11.lua` | Barrow Downs corrected Stone City entrance | Done | `out11_mmmerge.lua`; scripted regression covered. |
| `out12.lua` | Land of the Giants Xenofex/control-cube behavior | Done | `out12_mmmerge.lua`; scripted regression covered. |
| `out14.lua` | Avlee to Shoals wetsuit edge-travel gate | Done | `out14_mmmerge.lua`; per-member wetsuit check covered. |
| `mdt15.lua` | Small House map-refill item reset | Done | `mdt15_mmmerge.lua`; refill regression covered. |

## Original MM7 Global Overlay Coverage

| Source | MM7 behavior | Status | Missing / next action |
| --- | --- | --- | --- |
| `StdQuestsFunctions.lua` | Malwick wand/ambush, Cast Off, Arcomage deck restriction, Arcomage win tracking, MM7 endgame QBits | Done | No open original-MM7 gap known. |
| `StdQuestsFollowers.lua` | Dwarves, Loren/fake Loren, Judge follower lifecycle | Done | No open original-MM7 gap known. |
| `PromotionTopics.lua` | Antagarich promotion topics, Lich ritual, blaster topic | Done | No open original-MM7 gap known after the Lich follow-up. |
| `TownPortalSwitches.lua` | MM7 continent switch, arena save/Lloyd restrictions, portal labels | Done | Current table/UI tests cover MM7 unlocks and labels. |
| `Quest_DragonHatchling.lua` | Cross-path Warlock/Arch Druid entry plus hatchling feed/grow/follower flow | Deferred | Full named dragon party-member/roster lifecycle, dismissal/rejoin, and skill/SP aura are not implemented. |
| `Quest_CrossContinents.lua` | Verdant intro/topics, Dimension Door gate, connector stone, completion reward, final quest start | Deferred | First playable slice is done. Detailed Breach/BrAlvar/BrBase final quest mechanics remain. |
| `Quest_SavingGoobers.lua` | Later CrossContinents custom quest chain | Deferred | Not core original-MM7 parity. Implement only after final quest mechanics are in scope. |
| `Quest_EnrothGrandmasters.lua` | Enroth custom grandmaster topics | Deferred | Not MM7-core; relevant only for merged/custom cross-continent progression. |
| `Quest_EnrothDarkArts.lua` | Enroth light/dark switching topics | Deferred | Not MM7-core; relevant only for merged/custom cross-continent progression. |
| `ExtraArtifacts.lua` | Artifact uniqueness and custom artifact/special-item effects, including MM7 artifacts | Pending | Runtime item generation/equipment effects should be audited against this script. |
| `ExtraPotions.lua` | Extra black/white potion drink effects | Done | Extra potion ids `51-70` and missing standard cure/buff potion effects are handled in item-use runtime and unit-covered. |
| `NPCFollowersSkills.lua` | Hireling skill/stat/buff/repair/identify/gold/travel/food/fee effects | Mostly done | Shared follower bonus helpers are implemented. Rest-food, transport-day, gold pickup, shop identify/repair, and character-sheet luck/elemental-resistance consumers are wired. Remaining work is exact skill bonus consumption in combat/service calculations. |
| `Reputation.lua` | Beg/threat/bribe topics, global/continent fame, guard/shop/NPC reputation reactions | Mostly done | EVT reputation routing, effective reputation labels, BTB text/gates, merchant pricing, temple donation, peasant-kill penalties, stealing reputation/fines, guard hostility toggles, shop refusal/theft ban timers, bounty reward effects, town-hall fine payment, and throne sentence mechanics are wired. Dark Sacrifice is not an active runtime action in the merged spell table because spell id 96 is Dark Grasp. Remaining audit: exact jail/throne movie presentation if visual parity becomes important. |
| `MonsterPathfinding.lua` | MMerge pathfinder DLL behavior | Not MM7-core | OpenYAMM has its own actor movement/LOS systems; do not port DLL-shaped behavior directly. |
| `OutdoorAnimObjects.lua` | MMerge custom outdoor animated model helpers | Not MM7-core | Only port if a specific map overlay needs equivalent model animation. |
| `Editor *.lua`, `Convert Blv.lua` | MMerge editor/tooling scripts | Not MM7-core | Not runtime parity work. |

## General MMerge Mechanics Visible In MM7

| Source | Behavior | Status | Missing / next action |
| --- | --- | --- | --- |
| `10_Continents.lua` | Current/previous continent events and continent-scoped state | Done | Current runtime has active map/continent context. Revisit only if a script needs explicit previous-continent events. |
| `MenuChooseContinent.lua` | New-game continent chooser, intro movie, start/death maps | Pending | Antagarich death routing is done. New-game continent selection is still the broader merged-start UI task. |
| `MenuChooseCharacter.lua`, `CharacterOutfits.lua` | Merged race/class/portrait/outfit rules | Pending | Character selection data is partly consumed; active new-game flow still assumes the current fixed continent path. |
| `1_TownPortalSwitch.lua` | Continent-aware Town Portal table | Done | MM7 labels/unlocks are regression-covered. |
| `2_OutdoorTravels.lua` | Outdoor edge travel, death maps, Dimension Door helper, loading pics | Done | Active routes/death maps/Dimension Door are covered; specific loading-picture behavior is intentionally not a current target. |
| `Weather.lua` | Continent and map custom sky/weather | Done | MM7 sky/custom rows are covered by table/asset tests. |
| `AdaptiveMonstersStats.lua` | Runtime bolster, generated attacks/spells, PlayerAC formula | Mostly done | New ranged attacks/spells, stats, and bounty exclusions are wired. Active summon/replicate execution remains pending. |
| `BountyHunt.lua` | Monthly town-hall bounty hunt generation/reward/monster tracking | Mostly done | Shared runtime covers monthly target generation, level reward, kill marking, reward/fame/reputation output, bolster monster `No bounty hunt` exclusions, town-hall fine/bounty actions, and one-time hostile bounty spawn by monster id near the party. Remaining work: exact MMerge random map-wide spawn placement/presentation if needed. |
| `Stealing.lua` | Ctrl-click shop/monster stealing, fines, ban timers, reputation changes | Mostly done | Shared stealing resolver covers skill scaling, recovery, shop/monster success, caught/fine/reputation outputs, level gates, and monster distance gates. Ctrl-click shop/guild stock stealing, live indoor/outdoor actor stealing, caught-theft ban timers, and terrible-reputation shop refusal are wired. Remaining work: exact recovery-animation/presentation details. |
| `SpellsTweaks.lua` | Slow/Mass Distortion/Stun/Control Undead chances, GM Town Portal rule, Shield fix, monster Power Cure, disabled monster spells | Mostly done | Slow/Stun resistance gates and Control Undead dark-resistance cap are implemented. Remaining audit: Mass Distortion, GM Town Portal, Shield, monster Power Cure, and disabled monster spells. |
| `MonsterItems.lua` | Monster trophy drops, no drops from reanimated monsters, indoor activation, stuck cleanup, death-spawn special action | Mostly done | Reanimated/party-controlled monsters no longer create normal death drops. Remaining audit: death-spawn/special actions plus active-on-sight/stuck cleanup. |
| `ZombiePlayers.lua` | Zombie condition order, immunities, portraits/voices, direct-heal harm, dark temple reanimate behavior | Deferred | Reanimate can apply Zombie condition, but full MMerge zombie lifecycle was explicitly excluded from the current implementation pass. |
| `ExtraQuickSpells.lua` | Multiple quick-spell slots/keybinds | Deferred | UI convenience, not original-MM7 parity. |
| `NPCFollowers.lua` | Merged NPC follower framework | Mostly done | Follower state/hire flow exists; verify against `NPCFollowersSkills.lua` for bonuses/fees. |
| `NPCMercenaries.lua` | Generated mercenary pool and portrait exceptions | Deferred | We have classic hireables/Adventurer's Inn; generated mercenaries are not worth prioritizing unless needed for custom content. |
| `NPCNewsTopics.lua` | Profession/news topic generation | Done | Profession news/follower gating is table-backed and tested. |
| `NPCTeacherAutonotes.lua` | Teacher autonote creation | Done | Merged teacher autonote mappings and note creation are tested. |
| `History.lua` | Merged history/autonote support | Done | Runtime consumes merged quest/history/autonote tables where relevant. |
| `UsableItems.lua` | Temple in a Bottle and Dimension Door scroll | Done | Implemented through item runtime and map overlay. |
| `MiscTweaks.lua` | Transition text fixes and miscellaneous labels | Done | Known MM7 transition video/text regression is covered. Reopen only for a concrete wrong prompt/video. |
| `Additional UI.lua` | Hostile indicator/selection ring presentation | Deferred | Table is loaded; runtime presentation consumer was explicitly excluded from the current implementation pass. |
| `SwitchGold.lua` | Gold pile icon/sprite changes by MM7/MM8 continent | Deferred | Cosmetic presentation work was explicitly excluded from the current implementation pass. |
| `CouncilAppearance.lua` | Enroth council screen portrait overlay | Deferred | Not MM7-core. |
| `ExtraEvents.lua`, `ExtEvt.lua` | MMExt compatibility event hooks and extended variables | Mostly done | Do not port wholesale; add typed OpenYAMM hooks only when a pending feature needs them. |
| `DataTables.lua`, `LocalizeTables.lua`, `PaletteMul.lua`, `MenuControls.lua`, `MenuExtraSettings.lua`, `DebugConsoleKey.lua` | MMerge infrastructure/settings/localization conveniences | Not MM7-core | Not original-MM7 parity work. |

## Highest-Value Missing Work

| Priority | Item | Why it matters | Suggested verification |
| --- | --- | --- | --- |
| High | Bounty hunt runtime | Core runtime, town-hall actions, and hostile bounty spawning are implemented; exact random map-wide placement remains optional. | Unit tests cover target generation, runtime kill tracking, reward claim, fine payment, and exclusion tags. Add headless spawn placement tests if exact placement becomes important. |
| High | Extra potion drink effects | Implemented in item-use runtime. | Unit tests cover representative extra potion ids and standard cure/buff behavior. |
| High | Stealing runtime | Core resolver, Ctrl-click shop stock entry point, live actor entry point, and caught-theft bans are implemented. | Unit tests cover success/caught/fine/reputation/recovery, monster range/level gates, sensitive-target reputation rules, shop stock integration, and house bans. Add headless monster interaction tests for inventory transfer presentation if needed. |
| Medium | Spell tweak parity audit | Slow/Stun/Control Undead deltas are implemented; the rest needs focused audit. | Focused spell/combat tests after comparing remaining behavior to intended deltas. |
| Medium | NPC follower skill/fee bonuses | Core helpers, food, travel, gold pickup, shop identify/repair, and character-sheet stat/resistance consumers are implemented; exact skill consumers remain. | Unit tests cover helper deltas, shop service consumers, and character-summary bonuses. Add combat/service tests when skill consumers are wired. |
| Medium | Monster item/death special behavior | No-drop behavior for reanimated/party-controlled actors is implemented; death-spawn/special action behavior remains. | Actor death tests for no reanimated drops, configured drops, and delayed summon/replicate. |
| Deferred | Zombie player lifecycle | Reanimate currently sets Zombie, but MMerge changes portraits, healing, immunities, and temple behavior. | Explicitly excluded from this pass. |
| Deferred | Additional UI and SwitchGold presentation | Cosmetic but visible in MM7/MMerge. | Explicitly excluded from this pass. |
| Deferred | Dragon Hatchling party-member lifecycle | Custom content, not original-MM7 parity. | Save/load roster lifecycle tests once party-member scripting API exists. |
| Deferred | CrossContinents final quest and Saving Goobers | Custom shared content beyond original MM7. | Headless Breach/BrAlvar/BrBase quest-flow tests. |

## Existing Trackers This Supersedes Or Complements

- `MM7_MMERGE_FIXUP_INVENTORY.md`: per-map and first-pass global overlay implementation record.
- `MM7_MMERGE_REMAINING_WORK_TRACKER.md`: active short remaining-work checklist.
- `MM7_MMERGE_LUA_EXPOSURE_INVENTORY.md`: Lua/runtime API surface required by MM7 overlays.
- `MMERGE_TXT_TABLE_INTEGRATION_INVENTORY.md`: table import/runtime status.

Use this document as the broad MM7-visible missing-mechanics inventory. When a row is implemented, update this file and
the more specific tracker if one exists.
