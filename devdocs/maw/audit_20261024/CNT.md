# CNT — map content, events, quests, NPCs, misc tweaks

Auditor scope: MAW `Scripts/Maps/*`, `Scripts/Global/*` (content side), `General/zzMaw-Maps.lua` (map rules),
`MiscTweaks.lua`, `ExtraEvents.lua`, `Core/events.lua`, `zMaw-hooks.lua`, `zzMaw-TownPortalClickFix.lua`,
`zzMaw-Survival.lua`, `zzzzzMaw_Core.lua`, `MawCore/Fixes.lua`, `Engine.lua`, `BountyHunt.lua` (content side) against
`assets_dev/rulesets/maw/{events,maps,content}` and the loaders. MAW paths are relative to
`/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/`, OpenYAMM paths to the repository root. MMMerge base for "what MAW
changed" is `reference/mmmerge/Scripts`. Nothing was built or run.

---

### CNT-1: MAW global hooks reuse event ids 65310/65311, which are the base Amethyst and Diamond crystal events
Severity: P2
Confidence: confirmed (read both sides)
MAW: no such ids (MAW's hatchling release is an MMExt `NPCTopic`, the Doom circus move a script-load statement,
Global/Quest_DragonHatchling.lua:191-210, Global/GLOBAL.lua:799-803).
OpenYAMM: `assets_dev/rulesets/maw/events/Global_maw.lua:451` registers `RegisterGlobalNpcEnterHook(65310, …)` and
`:503` `RegisterGlobalOnLoadEvent(65311, …)`. Both go through `support.replaceGlobalEvent`
(`event_support.lua:1118-1123`, `:1082-1085`), so in a MAW game they overwrite global events 65310 (Amethyst) and 65311
(Diamond) of `assets_dev/engine/events/Global_mmmerge_crystals.lua:4-5`, which `InteractiveDecorationRules.cpp:20-21,
234-239` binds to the crystal decorations. Clicking an Amethyst crystal now runs the hatchling hook (no context, does
nothing) and a Diamond crystal runs the Doom circus move; neither can be harvested. 65311 also becomes a global onLoad
event. `ruleset.yml idRanges` only guards qbits/topics 10001-10099, not global event ids, so the load-time collision
check does not catch it.
Not covered by: no related row (DEVIATIONS, GAPS N8.5, P9.D7 checked).
Suggested fix: give the two MAW hooks ids from the MAW range (e.g. 10050/10051); consider declaring a global-event id
range in `ruleset.yml` and checking it like the others.

### CNT-2: d22's replaced load event never runs — GAPS N8.3 "done" is broken (and base d22 load behaviour is lost in MAW)
Severity: P2
Confidence: confirmed (read both sides)
MAW: Maps/d22.lua:12-36 replaces load event 5 (`events.LoadMap = evt.map[5].last`): clerics hostile with QBit 19, a
dimension run, or angered clerics; secret button (facet 5) shown with QBit 28 or a run.
OpenYAMM: `assets_dev/rulesets/maw/events/maps/d22_maw.lua:6` calls `ReplaceMapEvent(5, …)`. `support.replaceMapEvent`
→ `removeScopeEvent` removes 5 from `meta.onLoad` (`event_support.lua:831`, `:862-871`) and nothing re-adds it
(compare `worlds/mm8/events/maps/d07_mmmerge.lua:26`, which calls `AppendMapOnLoadEvent(1)` after its replace).
`ScriptedEventProgram.cpp:587` reads the final `onLoad`, so in every MAW game d22 runs no event 5 on load: during a
dimension run the clerics stay friendly and the button hidden; outside a run the base behaviour (clerics hostile after
the Necromancer alliance or angering them, the hostility cool-down that clears QBit 230, the Dyson button) is gone too.
`tests/scenarios/rulesets/maw_content_map_fixes.yml` only exercises event 452. A scan of every world/ruleset overlay
found no other replaced onLoad or timer event without a re-append.
Not covered by: GAPS N8.3 (marked done; implementation incomplete).
Suggested fix: add `AppendMapOnLoadEvent(5)` after the replacement (or make `ReplaceMapEvent` keep onLoad/onLeave
membership); add a load assertion (group 39 hostile, facet 5 secret) on a dimension run to the scenario.

### CNT-3: A reset dungeon can be reset again at once — MAW requires it to be cleared again first
Severity: P2
Confidence: confirmed (read both sides)
MAW: General/zzMaw-Maps.lua:168-177, 183-212: accepting a reset marks the map "resetting", then "resetted" on arrival;
`canResetDungeon` offers the prompt only while the entry is exactly `true`, which the completion check sets again only
when the reset dungeon is cleared once more ("Dungeon Completed! Reset is possible again.",
General/zzMaw-Monsters.lua:2640-2660). Also never in Insanity/Madness.
OpenYAMM: `game/rules/maw/MawMonsterRules.cpp:1264-1285` offers the reset whenever `completedMaps` contains the map;
`resetMap` only increments `mapResetCounts` and forces a refill, and `completedMaps` is never cleared
(`MawExperienceRules.cpp:145-200` returns early for completed maps, so no "reset possible again" either). The party can
enter, loot the chests, leave and reset again at the entrance dialog (`EventDialogContent.cpp:1197-1208`) as often as
it likes: every reset refills chests and corpses-to-be and stacks +20 levels, a loot-farming loop MAW's state machine
prevents.
Not covered by: no related row (GAPS §3 and §8 checked; A3.13 is the completion percentage only).
Suggested fix: keep a per-map "reset, not yet re-cleared" flag in `MawGameState` (save it), refuse the offer while it
is set, clear it in `rewardMapProgress` when the map is completed again and show MAW's "Reset is possible again".

### CNT-4: Endless Arena bosses drop nothing
Severity: P3
Confidence: confirmed (read both sides)
MAW: Global/zzMaw_Arena.lua:320-327 strips treasure only from monsters with `NameId == 0`; the wave-6 boss gets a
boss name from `generateBoss` (General/zzMaw-Monsters.lua:2996), so it keeps its boss loot (outside Madness, where
General/zzMaw-Monsters.lua:4420-4428 strips everything in d42).
OpenYAMM: `assets_dev/rulesets/maw/events/maps/d42_maw.lua:331-332` spawns every wave, the boss included, with
`loot = false`; `IndoorWorldRuntime::mapActorCorpseLoot` (`IndoorWorldRuntime.cpp:17266-17273`) returns empty loot
when `proceduralDeathLoot` is false, so the boss's MAW boss loot (A2.7) is never rolled.
Not covered by: no related row (DEVIATIONS 50, GAPS A2.7, P9.M5 checked).
Suggested fix: pass `loot = step ~= 6` outside Beyond Madness (Madness keeps the all-empty rule).

### CNT-5: An Endless Arena run is not aborted when the party leaves d42; the topic stays hidden
Severity: P3
Confidence: plausible (needs a runtime check)
MAW: Global/zzMaw_Arena.lua:60-76, 336-340: loading any other map or a save resets the run (`isArenaStarted=false`,
`ProcessGameData` → abort) and the Arena Master offers "Endless Arena" again on the next arena visit; while a level runs
both slots A and B of NPC 313 are hidden (`:115-129`).
OpenYAMM: `Global_maw.lua:482-493` sets `MawArenaLevel` and clears slot B; only the d42 timer's completion branch
(`d42_maw.lua:311-318`) restores slot B. Dying, casting Town Portal or otherwise leaving d42 mid-level leaves
`MawArenaLevel > 0` and slot B empty, so the Endless Arena cannot be started again unless the party re-enters d42 by the
base arena topic (slot A, still shown) and kills that fight's monsters plus the remaining waves.
Not covered by: no related row (DEVIATIONS 50 is the family list only).
Suggested fix: on-leave event in d42 (or an onLoad check elsewhere) that clears `MawArenaLevel` and restores
`SetNPCTopic(313, 1, 10030)`; optionally hide slot A while a level runs.

### CNT-6: Releasing the dragon while he is a hatchling does not remove him
Severity: P3
Confidence: confirmed (read both sides)
MAW: Global/Quest_DragonHatchling.lua:191-210: "Release the dragon" shows only while NPC 396 is hired and always calls
`NPCFollowers.Remove`; `:28-30` removes him again on load if released.
OpenYAMM: the hatchling is a follower from the Warlock promotion (`worlds/mm7/events/Global_mm7_mmmerge.lua:987`).
`Global_maw.lua:451-469` shows the release topic on every visit and removes the follower only
`if DragonJoined ~= 0`, so a hatchling "flies away" (message, `MoveNPC(396, 0)`) but stays in the followers and can be
fed on; `DragonReleased` is written but never read, so nothing keeps a released dragon out (789 re-adds him when
`DragonJoined` is set).
Not covered by: DEVIATIONS 53 (two topics instead of Y/N), GAPS N8.5 (rejoin).
Suggested fix: remove the follower whenever `HasFollowerNpc(396)`; have 789 and the enter hook check `DragonReleased`;
show the release topic only while he travels with the party.

### CNT-7: Scripted MAW spawns lose their actor tweaks
Severity: P3
Confidence: confirmed (read both sides)
MAW: Maps/7d24.lua:20-36 Manticore: HP ×2.5, no Attack1 missile, spell 6 at 100 % skill 3, speed 400, MoveType 0,
treasure 100 %; it comes *instead of* the 20th troglodyte (`return`). Maps/7d37.lua:20-36 Necromancer: HP ×2.5, no
missile, hostile, SpellChance 30, SpellSkill 1, wand 174/171 with 66 charges. Maps/7out02.lua (fort): Lieutenant
`SpellChance=100`.
OpenYAMM: `evt.SummonMonstersById` (`EventRuntime.cpp:7786-7863`) has no spell, spell chance/skill, missile or
item-charge fields, so `7d24_maw.lua:108-114`, `7d37_maw.lua:142-143` and `7out02_maw.lua:183-184` spawn table casters
with table spells and chances (the Manticore comment says "spellcaster" but sets none), and `7d24_maw.lua:107-114`
spawns a troglodyte in the same tick as the Manticore (20 troglodytes plus the boss; MAW 19 plus the boss).
Not covered by: no related row.
Suggested fix: add `spell`, `spellChance`, `spellSkill`, `noMissile`, `itemCharges` to the summon request (or a MAW
actor-override table), and `return` after the Manticore.

### CNT-8: An Omnipotent bounty target comes without its 100-200 escorts
Severity: P3
Confidence: confirmed (read both sides)
MAW: General/BountyHunt.lua:214-224: after `generateBoss`, when the boss name starts with "Omnipotent" it adds
100-200 more monsters of the family (55/30/15) within 2048, then the usual 5-15 within 1024.
OpenYAMM: `MawMonsterRules::spawnBountyTarget` (`MawMonsterRules.cpp:1164-1219`) spawns the boss and the 5-15 escorts
only.
Not covered by: GAPS A3.3, L3.2 (Omnipotent itself), P9.I8 checked.
Suggested fix: after the boss spawn, if its rolled affix is Omnipotent, spawn the extra 100-200 at radius 2048.

### CNT-9: Deyja nights warn twice and carry unfinished waves into the next night
Severity: P3
Confidence: confirmed (read both sides)
MAW: Maps/7out05.lua:17-40 keys the night by `round(Game.Time / Day)` (changes at noon), so one warning per night;
1001 spawns only while `mapvars.ambush[today]`, so leftover waves die with the night.
OpenYAMM: `7out05_maw.lua:216-232` keys by `floor((minutes + 120) / 1440)`, which changes at 22:00: a check between
21:30 and 22:00 warns (day N), the next check at 22:00 is day N+1 and warns again. `MawRiseWaves` (`:234-258`) is not
tied to the day: a rising after about 03:15 leaves waves that resume at 22:00 the next night, before (and on top of)
that night's own rising.
Not covered by: DEVIATIONS 52 (persistence across saves only).
Suggested fix: key the day at noon (e.g. `floor((minutes + 12*60) / 1440)`), and store the rising's day with the
waves so 60002 spawns only for the current night.

### CNT-10: Road to Insanity trade-good rule ports MAW's 1946 typo (Tularean Wood keeps selling) — MAW bug ported as-is?
Severity: P3
Confidence: confirmed (read both sides)
MAW: Global/GLOBAL.lua:38-50 lists `1946` (Deadly Swarm) where `1496` (Crate of Tularean Wood) is meant, so the
Tularean Wood seller is never cleared (noted in MAPS_CONTENT §4.1).
OpenYAMM: `Global_maw.lua:514-529` lists every seller but event 1260 / NPC 723 (item 1496), reproducing the typo. No
deviation row says whether that is intended.
Not covered by: PHASE9 P9.I8 (describes the rule, not the typo); DEVIATIONS checked.
Suggested fix: add `{event = 1260, npc = 723, item = 1496}` (and a DEVIATIONS row), or record the ported bug.

### CNT-11: MAW's NPC greetings are not ported
Severity: P3
Confidence: confirmed (read both sides)
MAW: Global/zzMAWRespec.lua:5-9 replaces the greeting of the Oracle (314), Judge Grey (413) and the Seer (794) with
"If you seek to pursuit a new path and reset your skills…"; Global/zzMaw_Arena.lua:2-5 the Arena Master's (313) with
"Welcome to the arena, warriors! This might be different…". The respec topic is one slot that turns from "Skill reset
info" into "I want to reset" after the explanation.
OpenYAMM: `content/npc_respec_patch.txt` adds topics only; greetings stay base, and both respec topics are always
listed (`Global_maw.lua:4-15`).
Not covered by: DEVIATIONS 53, 61 (topic slots), GAPS D.6 checked.
Suggested fix: patch the four NPCs' greeting cells (or a `SetNPCGreeting` in an enter hook), or record a deviation.

### CNT-12: MAW-dropped base content kept without DEVIATIONS rows
Severity: P3
Confidence: confirmed (read both sides)
MAW: drops or changes base events beyond those DEVIATIONS 54 lists: Maps/d19.lua:4-41 (door 15 and the transformer need
Dyson or NPC 11 topic D 634; the QBit 19 and invisibility paths go), Maps/7out02.lua (old base copy: no Judge Grey
death, no Arbiter messenger), Maps/7d24.lua (throne-room QBit 647 check, Dwarf King QBit 658 unstick),
Maps/7d29.lua (Cross-Continents Antagarich completion), Maps/7out01.lua (non-Redone: no-Arcomage tavern filter),
General/zzMaw-Maps.lua:610-613 (outa1 90 Hive post-ending lock), out11 505 (Barrow VII to `mdr01.blv`), Maps/d22.lua
(Dyson requirement for button and door outside runs).
OpenYAMM: all kept (`*_mmmerge.lua`, generated events) — consistent with MAPS_CONTENT §3.5 — but DEVIATIONS 54 names
only 6d05, 7d32, 7d34, out03, d07, pyramid and znwc, so these differences are undocumented as deviations.
Not covered by: DEVIATIONS 54 (partial).
Suggested fix: extend DEVIATIONS 54 with the list from MAPS_CONTENT §3.5.

### CNT-13: MAW monster names 205 and 211-214 lie outside the declared id range
Severity: P3
Confidence: confirmed (read both sides)
MAW: PlaceMon 205 (Naga Empress), 211-214 (Temple of Baa clergy) used by d18/d04 actors.
OpenYAMM: `content/place_mon_names.txt` appends 205, 211-214, 300, 301, but `ruleset.yml` declares
`monster_names: {begin: 220, end: 301}`, so a world that adds names 163-219 (base `place_mon.txt` ends at 162) would
collide with these five silently (the E.3 check only compares declared ranges). Also `patches/english/place_mon.txt`
rewrites row 162 "Placeholder" to the text "162" (taken from MAW's table).
Not covered by: GAPS E.3 (range check built for the declared range).
Suggested fix: declare 205-219 (or 205-301) as MAW's name range.

---

## Checked and matching

- Overlay loading: `GameDataLoader.cpp:337-394, 427-470` appends `rulesets/<id>/events/maps/<map>_*.lua` and
  `events/Global_*.lua` after the worlds' overlays, only when a ruleset is active; scene overlays
  (`MapAssetLoader.cpp:3856-3889`) likewise. Every MAW overlay name maps to exactly one world map. Ruleset switch
  reloads all common data (`GameApplication::activateRuleset`), so no MAW overlay leaks into Standard.
- MM6 stat shrines (outb1 261/262, outb2, outc1, outc2, outc3, outd1, outd2, outd3, oute1, oute2, oute3 261): any
  month, QBit 1230 guard, stats and QBits 1231-1242 as MAW (ours keeps the "+3" texts MAW drops).
- outb1 101 well: unscaled 5000 XP, monthly refill (map never refills in MAW). outb3 92: Doom+ closed, refused above MAW
  difficulty unless member 0 is level 255 (`difficulty > 2` = MAW `BolsterAmount > 100`). oute3 104 Doom route.
- Teleporter events 1777/1888/2666 targets and QBit 527/93 branches (Survival branch is dead code, README §6).
- 7d06, 7d21, 7d29 (once per game, global var), 7out02 ambush/lieutenant/10 reinforcement waves, 7d11 pillar doors,
  7d20 wine rack odds and MAW potions 225/229/230/224/240, out01 463 with the Insanity cap of 25 pirate returns.
- Scene overlays d04 (35 actors to 211-214), d08, d12, d18 (spawns and four Naga Empresses), 7d33 (actors 0-5, item 806
  removed), elemf, out05, d42 gate faces, 7d12 face 1817 → 3, 7d37 face 896 → 10: actor indices verified against the
  base scene files.
- GLOBAL.lua: quest gold bonus `gold × L/100 + 250 L` when gold and member 0's experience rise
  (`GameplayDialogController.cpp:1466-1486`, `MawExperienceRules::questGoldBonus`, L = `getPartyLevel()`); black-potion
  quests 181/203/212/234/246 (reagent colours of all worlds, rewards 254/254/254/253/252, XP); Galvinus 132/133 and
  CanShow; Rust 207 and 571-576 with item 249 (CanShow of 207 survives the replace); circus trades capped at 10 per kind
  per map; Doom circus traders moved.
- Druid Circlet (QBit 10001, 3000 gold, 10000 XP, strength-5 amulet), Dimensional Maps topic slots (DEVIATIONS 61),
  respec topic slots (no clash with base topics; base scripts set no slots of 314/413/794/41/313 that MAW uses).
- Trade-good topic events 250-266, 515, 1258, 1262-1266: NPCs and items match the base tables.
- Nightmare/Doom save food (indoor 2/10, outdoor 0/3, free on cleared maps, autosaves exempt), Lloyd/Town Portal block
  near enemies, Madness Town Portal text, Insanity food cap (P9.I6), outdoor no-refill map list (MAW `outSideMaps`),
  houses opening at 5 (A5.11), moved trainers (`npc_extra_houses.yml`: MAW's moves minus each NPC's home house).
- MiscTweaks (non-potion): unarmed GM dodge, MM7 regeneration and Meditation SP are switched off in MAW and overridden
  by `MawCombatRules::characterEvades` / `MawSkillRules`; the catalyst change is A4.8; the random MM6 music MAW disables
  has no Standard counterpart. ExtraEvents/Core/events.lua, zMaw-hooks.lua, zzMaw-TownPortalClickFix.lua,
  MawCore/Fixes.lua, Engine.lua and zzzzzMaw_Core.lua are binary/UI patches with no content to port (movement speeds
  are DEVIATIONS 134; the arena-pool fallback does not apply because OpenYAMM's arena reads unscaled table levels and
  refuses an empty draw).
