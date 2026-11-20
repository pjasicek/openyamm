# MAW phase 9: challenge modes and the randomizer (scope proposal)

Status: done (2026-10-24); agreed with the §5 recommendations except Q6, which follows MAW. Source: MAW
`ef23ee17`; file abbreviations as in the inventory below (MON `General/zzMaw-Monsters.lua`, IT `zzMaw-Items.lua`, SK
`zzMAW-Skills.lua`, SP `zzMaw-Spells.lua`, AL `zzAlchemy.lua`, MP `zzMaw-Maps.lua`, DMG `Modules/MawCore/Damage.lua`,
EST `Modules/MawCore/Estimates.lua`, XP `zzzMaw_Experience.lua`, RND `zzzzMalekith-Randomizer.lua`, MES
`MenuExtraSettings.lua`).

## 1. The modes in MAW

One spinner on party creation picks Normal, Doom, Road to Insanity, Beyond Madness or Austerity; it is fixed for the
life of the save (MES:237-305). The first three nest: Insanity is Doom plus more, Madness is Insanity plus more. Doom,
Insanity and Madness force difficulty index 7/8/9 (bolster 600, so every True Nightmare system applies too); Madness
also forces horizontal progression. Austerity combines with any difficulty 1-6. The randomizer is a separate tumbler
that combines with everything. "Survival" (`Mode 1`) is dead code.

## 2. What already exists

`RulesetChallengeMode` and `RulesetOptions.randomizer` are saved; the Rules panel has the controls (disabled because
`ruleset.yml` offers `challengeModes: [none]`, `randomizer: false`). The formula layer already branches on the mode:

- `mawModelConfig`: difficulty index 7/8/9, the doom/insanity/madness flags, Austerity's hit tables and level curve.
- Masteries 6/12/20, 8/16/25, 10/24/40 and teacher prices by mode; Cover/Mana Shield ladders; Supreme at 30/50/70.
- Crit and artifact caps (Madness 3000/900), dragon level cap, enchant power ×1.1/×1.2, rarity weights.
- Density per mode (`adjustMapEncounters`), bosses per map, Broodlord/Omnipotent chances, item drop ×0.5.
- Map completion experience and gold per mode, Madness hall caps, Austerity's enchant curve, no Legendary, reagent /8,
  no crafting items, the "and" reward text.
- The Nightmare systems (food cost to save, Lloyd/Town Portal block near enemies, revival on exit) already treat
  Doom/Insanity/Madness as Nightmare (`nightmareRules`).

So phase 9 is mostly the mechanics below, plus turning the modes on and testing them.

## 3. What is left, by mode

Ids are proposals for the tracker. "Doom" rows also apply in Insanity and Madness; "Insanity" rows also in Madness.

### Doom

| Id | Rule (MAW) | Where | Owner |
|---|---|---|---|
| P9.D1 | New game: gold set to 5000, 10000/party size experience each; starting enchantable items get 2 bonus charges (4 from Insanity) | MES:272-301, IT:4537-4552 | A |
| P9.D2 | Monsters gain on-hit conditions once per map visit: chance √L·2 %, pool by level (poison/weak/fear <15 ... eradication 100) | MON:3691-3747 | B |
| P9.D3 | Unidentified items cannot be worn; wear level requirement −3 | IT:4132-4134, 4362-4371 | C |
| P9.D4 | Identify costs IdRepSt², repair 5 at houses | IT:4188-4201 | C |
| P9.D5 | Chests need Disarm skill × mastery ≥ the map's Lock (×2 when Lock ≥ 4) or GM to open (see Q1) | IT:4145-4167 | C |
| P9.D6 | Hiring refused except houses 1466 and 1486; hire topic renamed | NPCFollowers.lua:248-253, 490-497 | C |
| P9.D7 | Content: circus traders 1109/1165/1166 leave, outb3 event 92 closed, oute3 event 104 goes to outb3 | GLOBAL.lua:799-803, Maps/outb3.lua, Maps/oute3.lua | C |
| P9.D8 | Struck monsters reveal the ones within 256 units indoors; Mass Distortion divisors; real-time poison ×6 | DMG:221-230, 371-394; IT:1514-1521 | B |
| P9.D9 | Turn-based movement capped at 370 units a phase (also Austerity) | MON:3663-3679 | B |
| P9.D10 | Kill experience × the density factor (√(2/3.5), Insanity ≈0.707, Madness ≈0.667) | MON:793-795 | A |
| P9.D11 | Death below −full HP, eradication below −2·full HP | DMG:1907-1922 | B |

### Road to Insanity

| Id | Rule | Where | Owner |
|---|---|---|---|
| P9.I1 | No map ever refills; no dungeon reset; outdoor maps need 100 % to complete; the repeat text drops "Reset is possible again" | MP:80-187, MON:2623-2649 | A |
| P9.I2 | Resurrected monsters give no experience and no loot | XP:172-176, MON:4139-4145 | A |
| P9.I3 | Disintegration: overkill below −10·full HP dismisses the member (party of 2+); a preference, on by default (Q6) | DMG:1923-1932 | B |
| P9.I4 | Poison ×2 more; Invisibility stripped when the detector is red; Elementalists: no √party factor, Invisibility only at GM; own healing-spell cost table | IT:1516, SP:3849-3857, DMG:171-186, SP:2335-2343 | B |
| P9.I5 | Spell books in shops ×5/×10/×20 by tier; training price `estimateSkill(level)+4` | IT:2306-2324, SK:1643-1657 | C |
| P9.I6 | Food capped indoors at 15 + monsters/25, the excess refunded outdoors | MON:2172-2187 | A |
| P9.I7 | Gem drops ×1.5; a dropped dimension map gets ≥30 charges (Insanity only) | AL:1180-1183, MP:928-930 | A |
| P9.I8 | Content: out01 pirate waves stop after 25; one open bounty at a time; trade items' EventA cleared once moved | Maps/out01.lua:22, BountyHunt.lua:150-156, GLOBAL.lua:38-50 | C |

### Beyond Madness

| Id | Rule | Where | Owner |
|---|---|---|---|
| P9.M1 | New game: every character level 1, no experience or skill points, every skill at 1 (before the Doom bonus) | MES:278-300 | A |
| P9.M2 | Horizontal progression locked | MON:357-388 | A |
| P9.M3 | Fixed map levels (`madnessMapLevels`, five starting maps exempt) with the slot offsets; unique monsters | MON:290-305, 431-574 | A |
| P9.M4 | Seeded boss affixes with Broodlord/Omnipotent pity, seeded Broodlord HP ×2 dmg ×1.5, Omnipotent ×4/×2 | MON:3028-3235 | A |
| P9.M5 | No experience, corpse loot or crafting drops on bounty maps, the arena, d42 and 7d05; event experience by total level | XP:114, 162-166; MON:4421-4428; AL:1122-1126 | A |
| P9.M6 | Dimension maps: monster drops only at level ≥70 and map level ≥950; map items cannot be dropped | MP:824-858, 1166-1197 | A |
| P9.M7 | No mercenaries; the dragon hatchling does not rejoin; Town Portal refused near enemies | NPCMercenaries.lua, Quest_DragonHatchling.lua:74, SP:3728-3735 | B |
| P9.M8 | Death ledger: any hit that lands (monsters, traps, falls, burning, events; audit CHM-2) marks the run pending for 5 game minutes (about 30 s once clear); loading or quitting while pending counts as a death; deaths shown on the character screen (see Q4) | DMG:1567-1573, MON:2289-2534 | A + C (UI) |

### Austerity

| Id | Rule | Where | Owner |
|---|---|---|---|
| P9.A1 | Bosses flattened (level term and HP spread ÷4); Fly cancelled by attacking at any difficulty; Mass Distortion ×4 | MON:29, 3005-3007; DMG:318, 389-391 | B |
| P9.A2 | Body armour and shield give at least round(skill × mastery) × 2 AC and resistance | IT:2980-2996 | B |
| P9.A3 | Identify Monster 10 GM for every member on each map load (0 after a respec until the next load) | AL:40-46, zzMAWRespec.lua:51-55 | B |
| P9.A4 | "Potion Deleted in Austerity" names (232-237, 252-256, 261-263; renamed, not blocked) | AL:22-36 | C |

### Randomizer

MAW shuffles 101 artifact ids (MM8 32, MM7 40, MM6 29) with `os.time()` and swaps them in chests, on the ground and in
the packs as they are seen, recording found ids two inconsistent ways; it also shuffles the maps' monster slots
(picture, difficulty, counts) once and deals them out on every load (RND:1-170). Nothing checks reachability.

Scrapped (2026-10-24): MAW's author called it working but not polished and the user dropped it (DEVIATIONS 138).
The ruleset offers no randomizer; `RulesetOptions::randomizer` stays in the save format, always off.

## 4. Not ported (proposed)

- Multiplayer: `vars.ChallengeMode` (always-open houses, instant training, frozen time) is the online session's, not a
  challenge mode (GAPS A5.11's note is wrong); the mode sync.
- The debug-console anti-cheat logging (MAW's console; ours is a developer tool).
- Insanity's per-monster-type loot LCG: our seeded streams replace it (RANDOMS.md §7).
- Dead code: Survival, the corpse-removal loot branch, the old monster damage, the commented item rules.

## 5. Decisions (agreed 2026-10-24)

| Q | Question | Decision |
|---|---|---|
| Q1 | Doom's chest gate tests `Trapped` the opposite way (untrapped chests need the skill), likely a MAW slip | Every closed chest on a map with a Lock value needs the skill, trapped or not, as its message says |
| Q2 | Austerity with Nightmare is allowed in MAW | Allow it, as MAW |
| Q3 | Doom and Insanity may switch progression mid-game in MAW; Madness is locked | As MAW |
| Q4 | Madness's death ledger lives outside the save in MAW, so reloading cannot erase a death | A ledger file per run in the user data folder (plain, not obfuscated), shown on the character screen; deleting it is the player's business |
| Q5 | Omnipotent bosses still drop Celestial items in Austerity | Keep, as MAW |
| Q6 | Disintegration (Insanity) dismisses a member for good; MAW has a setting for it | As MAW: a Rules-panel preference beside homing and friendly fire, on by default (`enableDisintegrate`, zz_Maw-initialize.lua:13) |
| Q7 | The randomizer as proposed in §3 | Moot: the randomizer is scrapped (DEVIATIONS 138) |
| Q8 | Mode content (Doom's circus, outb3/oute3, pirates) needs overlays that run only in that mode | A `RulesetChallengeMode()` query for event Lua, used by the MAW overlays |

## 6. Order, saves and tests

Progress: step 1 done 2026-10-24. `ruleset.yml` offers the four modes (no randomizer: scrapped); the Doom modes force
Nightmare (`rulesetChallengeModeDifficulty`: new game, `--ruleset`, scenarios), Austerity keeps a changeable difficulty
and gets Nightmare revival only at Nightmare; P9.D1 and P9.M1 (`ExperienceRules::prepareNewParty`); Q8 is
`evt.RulesetInfo().challengeMode`. Tests: `MawChallengeModeTests.cpp`, scenario `maw_challenge_modes`.

A's rows (2026-10-24). Already built in phase 3, found by the audit: P9.D10 (`monsterExperienceMultiplier`), P9.M2
(Madness forces horizontal), P9.M3 (`madnessLevel`, slot offsets), Insanity's no reset, 100 % outdoor completion,
revival without experience, gem drops ×1.5 and the event experience by total level. Built now: no refills from
Insanity (`mapRespawnDays`), revived monsters' empty corpses, the dungeon food cap (`MawGameState::heldFood`), a
dropped map's power ≥30 in Insanity, Madness's map drops (level 70, maps of level 950), Madness's Broodlord and
Omnipotent pity and multipliers (`broodlordPity`, `omnipotentPity`, none in d42 or on completed maps), no
experience, loot or crafting on Madness's arenas, 7d05 and bounty maps (`MawRules::madnessRewardlessMap`), dimension
maps kept out of the world in Madness (`ItemRules::canDropToWorld`). Save version 113. Not applicable: the repeat-clear
text ("Reset is possible again"), since a completed map shows no repeat message here. P9.M8: `MawMadnessLedger`
(the run is the save's root seed; `saves/maw_madness_deaths.txt`, scenarios keep it in their save folder;
`GameSession::setMadnessLedgerFile`); hits mark it in `applyMonsterHitEffects`, the wait runs in `updateMonsters`, a
load of a pending run counts a death; scenario `maw_madness_ledger`. Its UI (count, timer, load warning) is C's.

B's rows (2026-10-24): D2 (as MAW plays, GAPS D.20), D8 (`revealActorsAround`), D9 (`turnBasedWalkLimit`), D11,
I3 (`RulesetPreferences::disintegration`, DEVIATIONS 103), I4, A1-A3, and M7 (moved from C: `offersMercenaries`, the
hatchling's rejoin, `teleportBlockedText`).
C's rows (2026-10-24). D3: the wear level's −3 (and Insanity's) was built; unidentified items are refused in Doom
(`ItemRules::wearRefusal`, checked in `Party::tryEquipItemOnMember`). D4: `ItemRules::shopServiceMultiplier` (identify
difficulty², repairs 5). D5: `ItemRules::chestOpenRefusal`, checked before any trap in `resolveChestTrapOpen` (Q1:
every closed chest). D6: `ClassRules::followerHireRefusal` (the topic renamed, houses 1466 and 1486 still hire). D7:
`outb3_maw.lua` 92, `oute3_maw.lua` 104, a global on-load moving NPCs 1109, 1165 and 1166 away. I5: spellbook prices
in `MawItemRules::shopBuyValue`, `SkillRules::trainingPriceMultiplier` (expected skill + 4). I8: `out01_maw.lua` 463
(25 returns, map variable MawPiratesSpawned), `MonsterRules::bountyElsewhere` (one open bounty, read in
`BountyHuntRuntime`), the trade goods' first topic cleared after a purchase (`Global_maw.lua`). M8's UI:
`ExperienceRules::runDeaths` ("Death Count" on the character screen), `deathPendingSeconds` (red seconds under the
clearing share), `loadWarning` (the load confirmation from play). Q6: `ruleset_disintegrate`, last in the Rules tab's
Preferences and the new-game panel, Insanity and Madness only, saved with version 113. Tests: `MawContentUiTests.cpp`,
scenarios `maw_doom_items`, `maw_doom_content`, `maw_insanity_content`. M7 and A4 went to B.
Other rows are often partly built too: check the code before writing.

1. Turn the modes on (`ruleset.yml`, the Rules panel's descriptions and locks: Madness locks horizontal, the mode can
   never change after creation), the new-game setup (P9.D1, P9.M1) and a scenario per mode that starts, fights, saves
   and loads.
2. The rows by owner in parallel: A (monsters, maps, progression, ledger), B (combat, spells, skills,
   classes), C (items, houses, content, UI). Claims as in the gap pass.
3. A balance smoke per mode: monster HP and damage at levels 20/50/100 against `devdocs/maw/data/difficulty.yml`.

Save state: the Madness pending-death flag and run id, the Insanity food
refund, the once-per-visit monster condition rolls. One save version for all of it.

## 7. Doc corrections to apply

COMBAT §3.8 (removed corpses keep their loot; resurrected ones lose it only in Insanity), GAPS A5.11 (always-open houses
are multiplayer), TRAINERS_SKILLS §414 (Austerity's Identify Monster rule), UI_CONTENT:112 (no keys are shuffled),
RANDOMS §6 (actions 404/14 are object interaction and dropping), CLASSES_SPELLS_SPEC:762 (Invisibility at GM is
Elementalists only), and the missing chest gate and density experience factor.
