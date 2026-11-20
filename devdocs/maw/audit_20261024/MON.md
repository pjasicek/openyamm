# MON audit: monsters, difficulty, progression, experience

Auditor scope: zzMaw-Monsters.lua, zzzMaw_Experience.lua, BountyHunt.lua, pseudoSpawnpoint.lua, zzMaw-Maps.lua (levels,
refill, reset), zzMaw_Arena.lua, MenuExtraSettings.lua, zzMaw-Survival.lua, MonsterHP.lua, Estimates.lua (monster
numbers) against MawMonsterRules, MawMonsterLevels, MawExperienceRules, MawExperienceCurve, MawGameState, MawRules,
MawMonsterInspect, the indoor/outdoor world call sites and BountyHuntRuntime. MAW paths are relative to
`Maw-Mod-MMMerge/Scripts/`. Nothing was built or run; the balance model was not re-derived (it is golden-tested
against MAW's own Lua, `tests/MawBalanceModelTests.cpp` + `devdocs/maw/data/balance_golden.csv`).

One engine fact several findings rest on (checked in `re_mm8/mm8_orig/mm8.exe` with objdump): in MM8's
damageMonsterFromParty the kill call `call 0x402e78` (MMExt's `MonsterKilled` hook) is at 0x4375f7, and the
experience is read from the monster structure afterwards (`mov ecx,[esi+0x7c]` at 0x43760c) and given at 0x437613
(MMExt's `MonsterKillExp` hook). So MAW's `events.MonsterKilled` (zzMaw-Monsters.lua:4044-4080), which rewrites
`mon.Experience` to the template formula of `totalLevel[mon.Id]` (lines 4071-4080), runs before the kill experience
is read: in MAW **every** party kill is worth the formula for the monster id's level on the current map, whatever
its map structure said (risen, boss or unique).

### MON-1: Risen monsters always give full experience; Road to Insanity and Beyond Madness should give none
Severity: P2
Confidence: confirmed (read both sides; engine order checked in mm8.exe)
MAW: zzMaw-Monsters.lua:2247-2249 sets a risen monster's Exp to a quarter and NameId to Id+300, but
zzMaw-Monsters.lua:4071-4080 resets Experience to the full template value at death (see the engine note above), so
Nightmare/Doom risen give full experience; zzzMaw_Experience.lua:172-176 gives 0 for NameId>300 in Insanity/Madness.
OpenYAMM: IndoorWorldRuntime.cpp:15684 multiplies `rulesetFacts.experience` by the share (0.25, or 0 in
Insanity/Madness, MawMonsterRules.cpp:1031-1032), but revival happens in `leaveMap`, and every later load of the map
goes through `restoreSnapshot` (GameApplication.cpp:8243 -> IndoorWorldRuntime.cpp:18886 `refreshRulesetMonsters`
-> `refreshRulesetMonster` 15529 -> `resolveMonster`), which recomputes `facts.experience` from scratch
(MawMonsterRules.cpp:515-526, no `risen` check). `MawExperienceRules::grantKillExperience` (79-118) never looks at
`risen`. Net: the share is gone before the party can meet the risen monsters; in Road to Insanity and Beyond Madness
they give full experience and bank it (MAW: nothing), so leaving a dungeon early becomes an experience farm.
Not covered by: DEVIATIONS 51 (positions only), PHASE9 P9.I2 ("revival without experience", marked built), GAPS A3.x.
Suggested fix: in `MawMonsterRules::resolveMonster`, when `facts.risen` set experience to 0 in Insanity/Madness (or
make `grantKillExperience` return 0 for risen there). For Nightmare/Doom decide: MAW's effective rule is full
experience (its quarter is dead code); if the quarter is wanted, keep the reduced value across re-resolves and add a
deviation row.

### MON-2: Map completion counts risen monsters as alive; MAW counts them as slain
Severity: P2
Confidence: confirmed
MAW: zzMaw-Monsters.lua:2600 counts `monster.NameId>300` (risen, alive or not) with the dead in `m`. After a
Nightmare/Doom revival the cleared share does not drop: the party finishes the map by killing the not-yet-killed
ones, and the 65 % "weakened" check (2785-2793) uses the same ratio.
OpenYAMM: IndoorWorldRuntime.cpp:15621-15657 (`mapKillProgress`) counts a living risen actor as a living hostile, so
after a revival the share falls back (often to near 0) and completion and the 65 % weakening
(MawMonsterRules.cpp:1643-1663) need every risen monster killed again.
Not covered by: GAPS A3.13 (lists d42, mdt15, hidden, non-hostile; not risen), DEVIATIONS 51.
Suggested fix: in both `mapKillProgress` implementations count an actor with `rulesetFacts.risen` as slain (alive or
dead), as MAW does.

### MON-3: "Completed" is permanent; MAW's per-visit completion resets on refill and on a dungeon reset
Severity: P2
Confidence: confirmed
MAW: completion state has two parts: `vars.dungeonCompletedList[file]` (permanent, rewards and dimension pool) and
`mapvars.completed` (map variables, wiped by a refill or reset). Save cost (zzMaw-Monsters.lua:2145-2147), the HUD
colour/100 % (2276, 2627-2638) and the bounty gate (BountyHunt.lua:188) read `mapvars.completed`. A reset needs
`dungeonCompletedList == true` (zzMaw-Maps.lua:183-188); resetting marks it "resetting" -> "resetted" (166-176) and
only a re-clear sets it back to true (zzMaw-Monsters.lua:2646-2662 "Reset is possible again").
OpenYAMM: one set, `MawGameState::completedMaps`, never cleared. After a reset or a natural refill (MAW refills
dungeons outside Insanity/Madness) the map shows green "100%" at once (MawMonsterRules.cpp:1081-1101), Nightmare/Doom
saves there are free (1812), and `mapResetOffer` (1264-1278) offers another +20-level reset on every entry without a
re-clear, so resets can be chained (each a full refill of loot and experience).
Not covered by: GAPS A3.13, PHASE9 P9.I1 ("repeat text not applicable"), DEVIATIONS (none).
Suggested fix: keep a per-visit "cleared since last refill" flag (a named map variable, which a refill already
wipes) for the HUD, save cost and reset offer; keep `completedMaps` for the one-time reward and the dimension pool;
allow a reset only when the per-visit flag is set.

### MON-4: Endless Arena monsters drop nothing at all; MAW only empties the non-boss corpses
Severity: P2
Confidence: confirmed
MAW: Global/zzMaw_Arena.lua:293-299 zeroes gold and item chance only for `NameId==0` corpses; the wave boss keeps
`generateBoss` loot (100 % item, sqrt(100L)d sqrt(100L) gold). Crafting drops (zzAlchemy.lua:1119-1126) and dimension
map drops (zzMaw-Maps.lua:826-860) come from `MonsterKilled`, not the corpse, and run in d42 except in Beyond Madness.
OpenYAMM: assets_dev/rulesets/maw/events/maps/d42_maw.lua:47 summons every arena monster, the boss included, with
`loot = false`, which sets `proceduralDeathLoot = false` (IndoorWorldRuntime.cpp:14211); that blocks `corpseLoot`
(17270) and `lootWithoutCorpse` (14426), so no boss loot, gems, crafting specials or dimension maps.
MAPS_CONTENT.md §4.7 ("Corpses drop nothing") is the misread.
Not covered by: DEVIATIONS 50 (wave cycling only), GAPS (none).
Suggested fix: keep loot on the boss (`loot = step == 6`), and give the non-boss corpses no gold/item but their
crafting and dimension rolls (e.g. a "no carried loot" flag distinct from `dropsLoot`).

### MON-5: Kills in the Arena (d42) bank levels; MAW banks nothing there
Severity: P2
Confidence: confirmed
MAW: zzzMaw_Experience.lua:213-216 returns before `addBolsterExp` on d42 ("no bolster from arena"); members still
get their kill experience.
OpenYAMM: MawExperienceRules.cpp:116 always calls `addBankedExperience(bankedExperience / 5, ...)`; no d42 check
anywhere in the kill path (IndoorWorldRuntime.cpp:13187). Endless Arena farming raises every other map's monster
levels (the bank drives `levelOutside`), and the arena waves themselves are not bank-scaled.
Not covered by: DEVIATIONS 50, GAPS (none).
Suggested fix: skip the bank deposit when `m_rules.currentMap() == "d42.blv"` (only d42, not 7d05/zarena).

### MON-6: Dimension affix 12 "Monster resistances +X" has no effect
Severity: P2
Confidence: confirmed
MAW: zzMaw-Monsters.lua:600-605 sets every template resistance to min(base + X, 200 + X, 999) with X =
`getMapAffixPower(12)`; `recalculateMawMonster` copies them to the map's monsters (215-219).
OpenYAMM: `MawMapAffix::MonsterResistance` (MawDimensionMaps.h:39) is never read; every other affix except 25 and 33
has a `mapAffix(...)` site (grep). The affix still shows on the map item.
Not covered by: DEVIATIONS 60 / GAPS L8.2 (only 25 and 33).
Suggested fix: add X to the monster's resistances (before `mawCappedMonsterResistance`, keeping MAW's 200 + X and 999
caps) wherever the hit reads the target's resistance, and the inspect panel's resistance text.

### MON-7: Boss and unique kill experience use the wrong level
Severity: P3
Confidence: confirmed
MAW: at death the experience is the template's for `totalLevel[mon.Id]` (zzMaw-Monsters.lua:4071-4080, engine note
above): a boss is worth its C row's map level, a unique its own id's map level; their own boss/unique level never
enters it (the health ratio, which includes the boss HealthMult, does).
OpenYAMM: MawMonsterRules.cpp:516-519 uses `(bossLevel + familyLevel) / 2` for bosses, which equals the C level only
when the boss level was not re-rolled (`bossLevel` 308-323 re-rolls into [1.1L, 1.3L] or [L+10, L+30] often, then the
value is lower), and the unique's own level for uniques (424-447: bank-bolstered without -4, 2.5x, or the Madness
level) instead of the id's map level.
Not covered by: GAPS A3.4/A3.5, DEVIATIONS (none).
Suggested fix: compute experience from `baseLevel` (the id's resolved level, `levelOf(levels, stats.id, ...)`) for
every monster; the health ratio already carries the boss multiplier.

### MON-8: Bosses made from A or B rows get the wrong level
Severity: P3
Confidence: confirmed
MAW: `MawBossLevel` (zzMaw-Monsters.lua:31-40): a C row gets C + (C - B), a B row the C level, an A row the B level
(affix 19 "BecomeBoss" makes A/B bosses, 2911-2917). BALANCE_MODEL.md §7.6 states this correctly.
OpenYAMM: `bossLevel` (MawMonsterRules.cpp:308-323, used in `makeBoss` 739 and `resolveMonster` 416-417) applies
2L - familyLevel to every tier: a B boss stays at B, an A boss drops to 2A - B (then usually re-rolled around A).
Not covered by: GAPS A3.5.
Suggested fix: pass the row's next-tier level (B for A, C for B) as the boss's base for A/B rows; keep 2C - B for C.

### MON-9: Map drop level reads all tiers of the native families (GAPS A2.9 marked done)
Severity: P3
Confidence: confirmed
MAW: `MawMapDropLevel` (zzMaw-Monsters.lua:1926-1935) takes `totalLevel` of the B rows in `currentMapMonsters`
(B rows whose picture is a map encounter picture, a picture listed twice counted twice, first three sorted by base
level), at index ceil(n/2).
OpenYAMM: MawRules.cpp:639-654 collects the levels of every row whose picture is "<encounter> X" (A, B and C), once
each, sorted by resolved level, and `mapDropLevel` (305-313) takes the lower middle of that list: with two families
it picks the low family's C level instead of its B level.
Not covered by: GAPS A2.9 (done, but the list is wrong).
Suggested fix: push only rows whose picture equals `<encounter> + " B"`, once per encounter slot (duplicates kept).

### MON-10: The dimension +HP affix also inflates kill experience
Severity: P3
Confidence: confirmed
MAW: kill experience scales by `getMonsterHealth(mon)` (zzzMaw_Experience.lua:191, Estimates.lua:678-722), which does
not include affix 15 (it only ever touched the dead HPtable, DEVIATIONS 59).
OpenYAMM: `mawMemberKillExperience` (MawExperienceRules.cpp:120-136) divides the actor's real `maxHp`, which includes
the affix (MawMonsterRules.cpp:456-457), so under DEVIATIONS 59 the affix also gives +X % experience and bank.
Not covered by: DEVIATIONS 59 (says only that live HP rises).
Suggested fix: either divide the affix back out for the experience ratio, or note the extra experience in DEVIATIONS 59.

### MON-11: Nightmare revival also raises monsters that were not there on the first load
Severity: P3
Confidence: confirmed
MAW: only the roster recorded at the map's first load (`mapvars.monsterMap`, zzMaw-Monsters.lua:2213-2225, looped
at 2236) can rise; summoner adds, death summons and event spawns never do.
OpenYAMM: `reviveSlainMonsters` (IndoorWorldRuntime.cpp:15659-15716) revives every dead actor with stats that is not
a boss, unique or NPC, including Summoner adds (`summonBossFamilyMember`), affix 9 death summons and map-script
summons.
Not covered by: DEVIATIONS 51.
Suggested fix: mark actors placed by the map's first fill (or skip actors spawned at runtime) and revive only those.

### MON-12: Leecher bosses do not stack and drop fractional drain
Severity: P3
Confidence: confirmed
MAW: `leecher` (zzMaw-Monsters.lua:3390-3428, every 0.5 s) drains for each Leecher/Omnipotent boss in range, carries
fractions per member (`amountHP`, `amountSP`), skips hidden bosses (AIState 19), drains SP even from members below
1 HP.
OpenYAMM: MawMonsterRules.cpp:1745-1770 takes the strongest boss only and truncates `maxHealth * leech` and
`spellPoints * leech` each tick, so small drains vanish; two leechers drain like one.
Not covered by: GAPS (none).
Suggested fix: sum the per-boss strengths and keep a per-member fractional carry.

### MON-13: Unique monster level capped at 255
Severity: P3
Confidence: confirmed
MAW: the engine field is capped (zzMaw-Monsters.lua:305) but `getMonsterLevel` (1884-1895) returns the uncapped
`uniqueMonsterLevel`, which hit chance (zzMaw_MonsterHit.lua:16), drop level (zzMaw-Items.lua:285-305), crafting
(zzAlchemy.lua:1151) and dimension drops (zzMaw-Maps.lua:906-931) read.
OpenYAMM: MawMonsterRules.cpp:446 caps `facts.level` of uniques at 255 (regular monsters and bosses stay uncapped).
Late game (bank above ~250) uniques hit and drop like level-255 monsters.
Not covered by: GAPS A3.4.
Suggested fix: drop the cap from `facts.level` (cap only where the engine field is meant).

### MON-14: Monster damage follows the party size at resolve time, not at the hit
Severity: P3
Confidence: plausible (needs a runtime check of a hire/dismiss mid-map)
MAW: `getMonsterDamage` is evaluated per hit (Damage.lua:1703-1705) with the current `Party.Count` in the cover term
(Estimates.lua:428-440).
OpenYAMM: `facts.attack1Damage` is fixed in `resolveMonster` from `model(partyCount)` (MawMonsterRules.cpp:449-490)
and used by the "damage-recompute" stage (MawCombatRules.cpp:917); a party that goes solo (or grows) keeps the old
damage until the next map load.
Not covered by: GAPS (none).
Suggested fix: refresh ruleset monsters when the party size changes, or scale by model(now)/model(then) at the hit.

### MON-15: Bounty details: Omnipotent escort, kill credit across maps
Severity: P3
Confidence: confirmed
MAW: BountyHunt.lua:220-224: an Omnipotent bounty target brings 100-200 more monsters (radius 2048); 241-261: only the
current map's entry counts, only the monster with the boss's exact name, and a kill not by the party drops the entry.
OpenYAMM: `spawnBountyTarget` (MawMonsterRules.cpp:1164-1220) never adds the Omnipotent horde;
`markRuntimeBountyHuntMonsterKilled` (BountyHuntRuntime.cpp:193-247) marks every town's entry with that monster id
for any boss of the id on any map (`bountyKillCounts` only checks `bossAffix != 0`).
Not covered by: GAPS A3.3, PHASE9 P9.I8.
Suggested fix: spawn 100-200 kin when the rolled target is Omnipotent; under MAW match only the current map's entry.

### MON-16: Indoor completion colour below Nightmare (cosmetic)
Severity: P3
Confidence: confirmed
MAW: an indoor map is red until `monsterMap.cleared` (65 % at bolster >= 300, or completion), so below Nightmare it is
red until completed (zzMaw-Monsters.lua:2276-2282, 2627-2638).
OpenYAMM: MawMonsterRules.cpp:1079-1097 shows yellow unless revival rules apply.
Not covered by: GAPS A3.13. Possibly an intended improvement; if so, a deviation row.
Suggested fix: decide; either match MAW or record it.

### MON-17: Question: `evt.RulesetInfo().bolsterLevel` vs MAW's global `bolsterLevel`
Severity: P3
Confidence: plausible
MAW: Maps/7d37.lua:31 and Maps/7d24.lua:31 read the global `bolsterLevel`, which includes the +20 per reset, the Madness
fixed level and the dimension power (zzMaw-Monsters.lua:431-441) and, on horizontal non-starter maps, is clobbered to
`basetable[651].Level x 2.5` by the monster loop (551; BALANCE_MODEL.md §7.5 "side effect").
OpenYAMM: `scriptInfo` (MawMonsterRules.cpp:1227-1236) returns bank - 4 only, used by 7d24_maw.lua:25 and
7d37_maw.lua:8; in horizontal progression MAW's scripts effectively always pick the better item.
Not covered by: DEVIATIONS (none).
Suggested fix: decide whether to follow MAW's effective value (at least the reset/Madness/dimension terms) or record
the difference.

### MON-18: Hall under the Hill slot 3 count (minor)
Severity: P3
Confidence: confirmed
MAW: zzMaw-Monsters.lua:905-908 sets map 96's slot 3 to 1-3 after the density rules, so Hard..Madness do not raise it.
OpenYAMM: the picture change is in content/map_stats_patch.txt, but the 1-3 count is the table's and
`adjustMapEncounters` (MawMonsterRules.cpp:1387-1446) raises it like any slot (e.g. 2-4 at Nightmare).
Not covered by: (none).
Suggested fix: skip density for map 96 slot 3, or accept and note.

## Checked and matching

- Level resolution (`resolveMawMonsterLevels`) against recalculateMonsterTable (MON:416-617): native family detection
  and three-way sort, band extra bolster, adjust x1.5 (x1 Madness), partyBolster / bolsteredLevel, horizontal cap
  with the doubled reset bonus, non-starter 2.5x with flattener, fixed Madness level with offsets (non-native
  offset quirk ported), d42 formula, bounty override, arena-by-name zeroing, final round(max(L,1)); Austerity ^1.015;
  dimension power x10+20; reset +20.
- `mawBolsteredLevel`, the experience curve (`mawExperienceForLevel`/`mawLevelForExperience`, table to 2000 and
  extrapolation), bank (`addBankedExperience` with LVLBEFORE starting at 0), `levelOutside`/`totalLevel`,
  getPartyLevel(4) for bounties.
- Monster HP from family B level x tier ratio (0.6-1.8) x boss HealthMult, rounding to tens above 1000; damage x0.66 /
  x1.5 by tier x boss DamageMult; attack-2 damage by dice ratio; spell damage x the 22-entry multiplier table for
  spells < 100 (Ice Blast's duplicate key resolved to 0.75); 2-roll 75-125 % spread; AC base x (L+10)/(LB+10).
- Monster experience formula (lvlBase clamp, Antagarich bonus per DEVIATIONS 75, density multiplier
  sqrt(mean3/meanD)); kill split by living (not dead/eradicated) members, per-member health ratio with
  min(calcLevel(exp), total bank), (level+1)x1000 cap, bank = uncapped sum / 5; Madness rewardless maps.
- Event experience (x(1+L/100)+500L, x5/party, bank per call; total level in Madness), Doom/Madness new-party setup.
- Map completion rewards: 0.99^floor(n/100), Insanity outdoor 100 %, slain multipliers (0.67 Nightmare, 0.5 Doom, x0.8
  Insanity), experience/gold formulas incl. Madness, gem tier, per-member share, Austerity text; mdt15 and d42.
- Density by difficulty and mode (Hard/Hell gating, Nightmare/Doom/Insanity/Madness spreads, Dif+1), dimension scaling;
  never-refill outdoor list and Insanity no-refill; reset unavailable in Insanity/Madness; +20 per reset.
- Bosses: from MAW difficulty, ceil((n-30)/150) (/60 Doom), affix 16/17/19, C-tier non-wimp unnamed candidates
  (hostility not required), HP 2.5 x (1+L/255/f) x (1+0.5U/f), damage 1.2-1.4, Broodlord/Omnipotent chances and
  multipliers x2/x3 by mode, Madness pity, affix 18; draw scale x1.4/x2 (+50 % Omnipotent); hatching cascade.
- Boss affix runtime: Regenerating (1 % x 0.99^hits / (1+L/50) per 0.1 s), Swift x2 speed, Shadow vs Wizard Eye,
  Summoner (physical or 40 %, 75/25 A/B, halfway point, speed 350).
- Doom special-attack roll (sqrt(L)x2 %, pool by level, uniques excluded), disease->poison below 20; Hell/bounty
  ranged attack-2 rule and its dice; fast-melee speed bonus; Nightmare/Doom food cost to save, Lloyd/Town Portal
  block, revival rules incl. Austerity at Nightmare, 65 % weakening threshold, Insanity food cap.
- Unique monster levels (no -4, 2.5x horizontal elsewhere, Madness level + 2 x (High-Mid) or 3x).
- Bounty: reward round(L + getPartyLevel(4)) x 100, target from monTbl (C-tier non-wimp minus 462/579, by level),
  bounty level max(bank(4) - LB/1.5, 0) kept on the map, 5-15 escorts 55/30/15, "clear the area" gate, Insanity one
  open bounty. Arena wave family index and wave table, L x 20000 reward.
- Difficulty mapping to model index (DEVIATIONS 1), option change clears model and level caches and re-resolves live
  monsters keeping the HP share; Standard `MonsterRules`/`ExperienceRules` defaults reproduce HEAD behaviour
  (bounty reward level x 100, respawn days, no bosses).
