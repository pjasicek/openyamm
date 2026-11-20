# FMON — second pass, function inventory of MAW's monster files

Files: `Scripts/General/zzMaw-Monsters.lua` (4475 lines), `zzBossSync.lua` (solo paths), `zzMaw_MonsterHit.lua`,
`pseudoSpawnpoint.lua`, `zSERIOUSMAW.lua` (MAW `ef23ee17`). Every function, event handler, timer and side-effecting
table-level statement was listed (inventory at the end) and traced to `game/rules/maw/*` / `assets_dev/rulesets/maw/*`
or to a DEVIATIONS / GAPS / pass-1 row. Read-only; nothing built. One engine fact was checked in the binary with
objdump on `re_mm8/mm8_orig/mm8.exe` (the MMExt-hooked executable MAW runs on; the first pass used the same file).

MAW paths below are relative to `Maw-Mod-MMMerge/Scripts/General/` unless prefixed (DM = `Modules/MawCore/Damage.lua`).

---

### FMON-2-1: Monster missile attacks take two Speed rolls in MAW, one in OpenYAMM (engine fact now verified)
Severity: P2 (question: MAW's real behaviour vs. its own model)
Confidence: confirmed (both Lua sides read; engine call sites checked in mm8.exe)
MAW: `zzMaw_MonsterHit.lua:12-31` replaces the engine routine 0x425893 (monster-hits-player roll) with the Speed roll
`chanceToBeHit(Speed, L) >= U()`. In mm8.exe that routine has exactly two callers, both in the monster-damages-player
function at 0x437b06: 0x437b59 (melee path) and 0x437ffd (projectile path, reached for monster attack objects
0x1f4-0x221 = 500-545, arrows via the GM-Unarmed evade check at 0x43809e). After the engine lets the hit through, the
`DamageToPlayer` pipeline rolls the Speed dodge again for any hit carrying an object
(DM:1684-1686, `dodgeableHere = action 2/3 or data.Object ~= nil`). So: melee one roll, monster spells one roll
(pipeline only), monster attack missiles two rolls: chance to be hit p² instead of p (Hell at par: 0.81 -> 0.66, about
19 % fewer missile hits). COMBAT_SPEC §14 lists this as "not verified"; it is now.
OpenYAMM: `MawCombatRules::monsterAttackLands` (MawCombatRules.cpp:3395) always lands, `characterEvades` (3401) rolls
Dodging and Speed once for every attack, missiles included.
Not covered by: DEVIATIONS 20-22 (cover only), CMB checked list ("monster hit = Speed roll"), COMBAT_SPEC §14 (open).
Suggested fix: decide with the user. MAW's balance model (`MawBalanceModel::chanceToBeHit`, one roll) assumes p, so
keeping one roll is defensible: add a DEVIATIONS row ("MAW rolls missiles twice through the engine hook and the
pipeline; one roll here, as its model assumes"). Matching MAW: roll Speed a second time in `characterEvades` when the
attack is a physical monster missile (not a spell).

### FMON-2-2: Kills by the party's allied monsters give experience in MAW, none in OpenYAMM
Severity: P3
Confidence: confirmed (read both sides; the exact amount reads `mon.Exp`, see below)
MAW: zzMaw-Monsters.lua:4082-4095 — when the last hitter (`WhoHitMonster`) is a monster with `Ally == 9999` (Summon
Wisp, zzMaw-Spells.lua:3434-3452; Reanimate / GM Control Undead, MMMerge SpellsTweaks.lua:107), every conscious member
gets `mon.Exp / consciousCount` (the template formula just reset at 4072-4080): no health ratio, no (level+1)x1000 cap,
no bank deposit. Conversely, a monster that itself has `Ally == 9999` gives 0 when killed (4062-4065), so killing your
own wisp or reanimated undead (friendly fire on) gives nothing.
OpenYAMM: experience is only granted from the party-damage paths (`grantMonsterKillExperience` at
IndoorWorldRuntime.cpp:13187/15891, OutdoorWorldRuntime.cpp:16216/17441); the monster-vs-monster path
(IndoorWorldRuntime.cpp ~14709-14745) grants nothing, and a party kill of an allied actor grants the normal reward.
Not covered by: GAPS A3.x, DEVIATIONS (none), MON-1..18.
Suggested fix: in the MAW rules, when a party-allied actor kills a monster with ruleset facts, give each conscious member
`facts.experience / conscious` (no ratio, no cap, no bank); give 0 for killing an actor allied to the party.

### FMON-2-3: GAPS A3.14 (fast-melee speed bonus) is incomplete: party allies and neutrals in a fight stay calm
Severity: P3
Confidence: confirmed
MAW: zzMaw-Monsters.lua:94-100 gives the bonus (v/2 + 300) to every hostile monster **and every party ally
(`Ally == 9999`)** on load; :142-152 (`AfterMonsterAttacked`) gives it to any non-ally monster that attacks or is
attacked by another monster, so neutral guards or peasants fighting monsters speed up too.
OpenYAMM: OutdoorWorldRuntime.cpp:9707-9708 and IndoorWorldRuntime.cpp:9816-9817 use `calmMoveSpeed` whenever the actor
is not `hostileToParty`; party summons/reanimated allies and neutrals fighting monsters keep the calm speed.
Not covered by: GAPS A3.14 ("neutral ones once they fight", marked done).
Suggested fix: use the fast speed for actors allied to the party and for actors currently engaged with another actor
(e.g. a non-null hostile actor target), not only for `hostileToParty`.

### FMON-2-4: A boss's spell skill is not multiplied by its damage multiplier
Severity: P3
Confidence: plausible (MAW side confirmed; effect depends on which monster spells read skill in our engine)
MAW: zzMaw-Monsters.lua:3074-3075 sets `SpellSkill = JoinSkill(s x dmgMult, m)` for every boss (dmgMult 1.2-1.4,
Broodlord 1.5-1.8, Omnipotent 2-2.5, x affix 18). Damage spells are recomputed by the pipeline anyway, so this matters
for skill-driven monster spells (heals, self-buffs such as Haste, Stoneskin, Bless, Hour of Power, Pain Reflection).
OpenYAMM: `makeBoss` (MawMonsterRules.cpp:726-818) never touches spell skill; `resolveMonster` only sets
`spell1SkillLevel` for the dimension Fireball/Dragon Breath affixes (553-556).
Not covered by: GAPS A3.5/L3.2, bosses.yml notes.
Suggested fix: in `resolveMonster`, when `facts.bossAffix != 0`, scale `spell1SkillLevel` by `bossDamageMultiplier`
(spell 1 only, as MAW).

### FMON-2-5: extends MON-6 — MAW's affix 12 (monster resistances +X) reaches only unnamed monsters
Severity: P3 (detail for the MON-6 fix)
Confidence: confirmed
MAW: the template resistances get `min(base + X, 200 + X, 999)` (zzMaw-Monsters.lua:600-605), but the first
`AfterLoadMap` handler (107-126) resets **every** map monster to `min(base, 200)` (no X), and only `NameId == 0`
monsters copy the template back (`recalculateMawMonster`, 213-219). Bosses (220-299), uniques (1-219) and risen
monsters (>300) never get X.
OpenYAMM: MON-6 (affix 12 unread) still open; `mawCappedMonsterResistance` caps at 200 (MawCombatRules.cpp:710-713).
Not covered by: MON-6 (suggests applying X to every hit target).
Suggested fix: when MON-6 is fixed, apply X (and the 200 + X / 999 caps) only to actors with no boss affix, no unique
flag and not risen — or add a deviation row if it should cover bosses too.

### FMON-2-6: Risen monsters' loot differs from MAW and has no deviation row
Severity: P3
Confidence: confirmed (engine loot-at-search behaviour from OpenEnroth `Actor::LootActor`, Actor.cpp:3491-3584)
MAW: revival (zzMaw-Monsters.lua:2242-2258) sets `AIState = 0` *before* testing `AIState == Removed`, so the zeroing of
`TreasureItemPercent`/`TreasureDiceSides` and the reseed of `mapvars.MonsterSeed[i]` are dead code. The engine rolls
corpse loot when the corpse is searched, from those untouched fields, and MAW's PickCorpse (zzMaw-Items.lua:161-205)
reseeds from the unchanged `MonsterSeed[index]`: in Nightmare/Doom a risen monster drops its full loot again (most
likely the same roll). Only Insanity/Madness empty it (4139-4145). MAW's own prompt (2820) and the commented
`round(old.item/4)` say risen monsters should give *less* loot.
OpenYAMM: `IndoorWorldRuntime::reviveSlainMonsters` (IndoorWorldRuntime.cpp ~15690-15696) clears the carried item and
sets `proceduralDeathLoot = false` when the corpse had been searched, so a risen monster whose corpse was looted drops
nothing at all; an unsearched one keeps its loot. (Related quirk not ported, correctly: MAW records bosses as
`respawn = true` because they are still NameId 0 at LoadMap, and PickCorpse resets a looted boss to NameId 0, so a
looted boss rises as a plain "Resurrected" monster with boss HP; we never revive bosses.)
Not covered by: DEVIATIONS 51 (positions only), MON-1 (experience only), GAPS A4.4 (crafting drops only).
Suggested fix: record the choice in DEVIATIONS (MAW duplicates loot through dead code; we give none after a search),
or give a quarter as MAW's text intends.

### FMON-2-7: extends MON-12 — Leecher drains four times as hard in turn-based mode
Severity: P3
Confidence: confirmed
MAW: zzMaw-Monsters.lua:3402 `timeMultiplier = Game.TurnBased and 4 or 1` multiplies both the HP and SP drain.
OpenYAMM: MawMonsterRules.cpp:1743-1770 has no turn-based factor (and takes the strongest Leecher only, MON-12).
Not covered by: MON-12 (stacking, fractions, hidden bosses).
Suggested fix: fold the x4 into the MON-12 rework if turn-based time runs the 0.5 s aura tick at the same pace as MAW's
timer; otherwise note it in DEVIATIONS.

### FMON-2-8: extends MON-17 — the clobbered global `bolsterLevel` also prices chest gold on horizontal maps
Severity: P3 (question)
Confidence: confirmed
MAW: on horizontal non-starter maps the monster loop overwrites the global `bolsterLevel` with
`basetable[i].Level x 2.5` for every row (zzMaw-Monsters.lua:551), ending at row 651 (Cactus C). zzMaw-Items.lua:904-924
(chest gold piles, after `Sleep(1)`, so after the recalculation) uses that global: chest gold is
`10 x (band mean + level(651) x 2.5) x 1/2/4 x U(0.66, 1.32)` there, whatever the party's bank.
OpenYAMM: `MawItemRules::chestGoldAmount` (MawItemRules.cpp:2066) uses `mapBolster` (bank − 4, resets, Madness,
dimension power), i.e. MAW's intended value.
Not covered by: MON-17 (names only the 7d24/7d37 scripts), GAPS L4.4.
Suggested fix: decide together with MON-17; if the intended value stays, one DEVIATIONS row covering both readers of
the clobbered global.

### FMON-2-9: extends MON-3 — Beyond Madness dimension runs on a completed map lose the pity specials
Severity: P3
Confidence: confirmed
MAW: `checkPityProtectedBoss` runs unless `Map.Name == "d42.blv"` or `mapvars.completed` (zzMaw-Monsters.lua:3036);
`mapvars` are fresh in a dimension run, so a run on an already completed dungeon can roll Broodlords/Omnipotents with
pity.
OpenYAMM: `makeBoss` (MawMonsterRules.cpp:763) tests the permanent `state.completedMaps`, so in Beyond Madness every
dimension run on a completed map (all of them, as runs need a completed target) gets no Broodlord or Omnipotent at all,
and the pity counters do not move.
Not covered by: MON-3 (save cost, HUD, reset offer), GAPS L3.2.
Suggested fix: use the per-visit completion flag MON-3 proposes (or `!dimensionRun || !run.completed`).

### FMON-2-10: Boss HP multiplier takes the re-rolled level; MAW the C + (C − B) level
Severity: P3 (small: a few % boss HP when C − B is outside 10-30 % of C)
Confidence: confirmed
MAW: `generateBoss` computes `fromLevel = 1 + min(MawBossLevel, 255)/255` (3000-3008) once; the re-roll into
[1.1C, 1.3C] / [C+10, C+30] happens later in `recalculateMawMonster` (321-331) and changes only the level, not the
stored `HealthMult`. Boss gold dice `sqrt(100 L)` also use the pre-re-roll level (3013-3014).
OpenYAMM: `makeBoss` (MawMonsterRules.cpp:739-748) uses `bossLevel(...)`, i.e. the re-rolled level, for the HP
multiplier; `corpseLoot` (903) uses `facts.level` (re-rolled) for the gold dice.
Not covered by: GAPS A3.5, MON-8 (A/B rows).
Suggested fix: compute the multiplier and gold dice from `2L − familyLevel` capped at 255 before the re-roll, or
accept and note.

### FMON-2-11: Goblin King (NameId 300) and Goblin's Lieutenant (301) — MAW quirks not ported, no row
Severity: P3 (question)
Confidence: confirmed by reading (MAW in-game effect plausible)
MAW: NameIds 300/301 sit on MAW's boss/risen boundaries. 301 is `> 300`, so the Lieutenant counts as slain while alive
for map completion (2600), gives 0 experience and an empty corpse in Insanity/Madness (zzzMaw_Experience.lua:172,
4141), and no crafting or dimension drops (zzAlchemy.lua:1119, zzMaw-Maps.lua:827). 300 is in `[220, 300]` for
`getMonsterHealth` (Estimates.lua:716-720), which calls `generateBoss(index)` on it the first time the inspect panel
(2089) or the kill-experience hook reads its HP: the King becomes a random-affix boss with a new name; and the solo
`zzBossSync` purge (`client_purge_except_set`, zzBossSync.lua:70-82, run from `on_map_ready` 310-331) resets any
NameId 221-300 not in `bossSet` to 0 on every load, so after a reload he is a plain monster (name and x3 HP gone).
OpenYAMM: `7out02_maw.lua:31` and `7d29_maw.lua:11` spawn them as named monsters (`name = 300/301`, `hpScale = 3`); no
risen or boss treatment.
Not covered by: CNT rows on 7d29/7out02, DEVIATIONS.
Suggested fix: keep ours (MAW's behaviour is accidental) and add one DEVIATIONS line, or ask the MAW author.

### FMON-2-12: Two monster-position safety nets are not ported and have no row
Severity: P3 (question)
Confidence: confirmed (MAW side); whether OpenYAMM needs them is a runtime question
MAW: `checkOutOfBound` (3536-3576, every 2 s) clamps outdoor monsters to ±22528 (back to ±22400) and returns indoor
monsters that are in no room to their last in-room position; `nudgeMonsterAroundCorner` + `MonstersProcessed`
(4205-4325, indoors, real time) steers a standing hostile monster within 350 units whose line to the party crosses a
wall sideways for 10 frames.
OpenYAMM: no counterpart (only the bounty spawn uses the ±22528 range, OutdoorWorldRuntime.cpp:20321). MAW-only
displacements exist here too (`pushActor` up to 2048, Swapper `swapActorPlaces`, Puller, dashes).
Not covered by: DEVIATIONS, GAPS.
Suggested fix: confirm in play that pushed/swapped actors cannot leave the map or end in a wall; if they can, clamp in
`pushActor`/`swapActorPlaces`; record the nudge as "engine AI handles corners" in DEVIATIONS.

---

## Checked and matching (summary)

- Level resolution, HP, damage, AC, experience formula and density were verified in pass 1 (MON checked list); this
  pass re-traced them entry by entry and found only the extensions above.
- Density: every Hard/Hell, Nightmare, Doom, Insanity, Madness branch of `AdjustMonsterDensity` matches
  `adjustMapEncounters`; the one shape difference (MAW raises a slot's Low to 1 at Hard/Hell even when Hi > 3) never
  bites: no map has Low 0 with Hi > 3 (checked `map_stats.txt`).
- Bosses: count `ceil((n − 30)/150)` (/60 Doom), affixes 16/17/19, C-tier non-wimp unnamed candidates, HP
  2.5 x (1 + L/255/f) x (1 + 0.5U/f), damage 1.2-1.4, random Broodlord/Omnipotent order (Omnipotent overrides and
  multiplies over a Broodlord), Broodlings never roll specials (MAW passes `skillType`; `generatedByBroodlord` is never
  set), Madness pity numbers (x2/x1.5, x4/x2), affix 18 on HP and damage, draw scale, hatch cascade C -> 3 B -> 3 A,
  Omnipotent's 14 single-affix bosses (MAW radius 512, ours 256: cosmetic).
- Hell/bounty ranged attack 2 (starting maps, walkers, no missile/attack 2/spell, tier x10 %, dice /1.4, bonus /2);
  disease -> poison below 20; Doom special-attack roll (pool, uniques excluded, bosses included, after bosses).
- Nightmare/Doom: save food 0/2 (outdoor/indoor) and 3/10 with enemies near; Lloyd/TP block; revival only indoors at
  bolster 300/600 or Mode 2, uniques and bosses excluded, 65 % weakening; "Resurrected" names; Insanity food cap
  15 + floor(High/25).
- Map completion: dead AI states, hidden 19, non-hostile excluded, mdt15, d42, 0/0 handling, 0.99^floor(n/100),
  Insanity outdoor 100 %, reward formulas incl. Madness and dimension runs, completion message wording.
- Leecher range 1500, ((1500 − d)/1500)² x 5 %, HP floor 1; Regenerating 1 % x 0.99^hits / (1 + L/50) per 0.1 s; Swift x2;
  affix 11 speed; Shadow vs Wizard Eye; turn-based walk limit 370 (Doom family, Austerity).
- Death drops (80 % cancel, 217/632/633/640/654 and reagents thinned); Madness rewardless maps; Insanity risen corpses
  empty.
- Madness death ledger (pending on hit, 4.5-minute shortcut when clear, leave clears, death/load counts), apart from
  CHM-2.
- BossSync solo: boss identity survives save/load (ours: facts in the save, SaveGame.cpp:765/794).
- pseudoSpawnpoint: tier pick by powerChances, family from `(id + 2) div 3`, radius, treasure on; the vars.seed reseed is
  RANDOMS territory.
- zSERIOUSMAW: names 200-204 are unused by MAW's maps (MAPS_CONTENT actor survey), 304 is overwritten by the
  "Resurrected" names, 205 is ported (`content/place_mon_names.txt`).
- MAW bug deliberately not reproduced (no finding): the load-time speed bonus re-applies to an already boosted
  `Velocity` on every `AfterLoadMap` (94-96 has no `Velocity == MoveSpeed` guard); ours derives speed from the table each
  resolve.

---

## Inventory: MAW entry → OpenYAMM counterpart → status

Status: ✓ matches; row = covered by an existing DEVIATIONS/GAPS/pass-1 id; FMON-2-n = this file; n/a = multiplayer,
debug, randomizer, UI-only, helper or dead code.

### zzMaw-Monsters.lua

| Line | MAW entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 5 | `bolsteredLevel` | `mawBolsteredLevel` | ✓ |
| 18 | `MawTierB` | `mawFamilyBId` | ✓ |
| 27-29 | `BOSS_HP_*`, `AUSTERITY_BOSS_FLATTEN` | `makeBoss` constants | ✓ |
| 31 | `MawBossLevel` | `bossLevel()` | MON-8 |
| 42 | GameInitialized2: `BLevel`; Bonus 20 -> 17 | table B levels; `content/monster_data_patch.txt` | ✓ (A3.7) |
| 67 | `getPlayerControlledMonsters` | — | n/a (multiplayer) |
| 81 | `speedBonus` | `resolveMonster` moveSpeed | ✓ |
| 85 | AfterLoadMap: speed for hostile/ally | `calmMoveSpeed` | FMON-2-3 |
| 85 | AfterLoadMap: SpellSkill % 64 | actors take table skills | ✓ (A3.7 moot) |
| 85 | AfterLoadMap: resistances min(base,200,999) | `mawCappedMonsterResistance` | ✓; FMON-2-5 |
| 85 | AfterLoadMap: one-time recalc guard | resolve on every load | ✓ |
| 142/149 | `speedBonusInCombat`, AfterMonsterAttacked | — | FMON-2-3 |
| 159 | GameInitialized2: `basetable` | monster table rows | ✓ |
| 203 | `recalculateMawMonster`: d42 skip | arena spawns via `d42_maw.lua` | ✓ (MON-4/5) |
| 203 | ... NameId 0: template stats, keep HP % | `refreshRulesetMonsters` | ✓ (A3.2) |
| 203 | ... AIType != 1 -> 0 | `monster_data_patch.txt` | ✓ (A3.7) |
| 203 | ... uniques (store, level, HP) | `resolveMonster` unique branch | ✓ (A3.4); MON-7, MON-13 |
| 203 | ... bosses 220-299 re-roll | `bossLevel()` draw | ✓ (A3.5); FMON-2-10 |
| 203 | ... affix 3/4 Fireball / Dragon Breath | `generatedSpell1Id` | ✓ |
| 203 | ... affix 12 only for NameId 0 | — | FMON-2-5 (MON-6) |
| 355 | Action: 113 difficulty change; monster count change | option change re-resolve; spawn-time resolve | ✓ |
| 383 | AfterLoadMap: Madness/Nightmare/Doom bolster force + recalc | `mawModelConfig`, resolve | ✓ |
| 404 | BeforeLoadMap: recalc table | `monsterLevels` cache | ✓ |
| 410 | LoadMap: recalc | resolve on load | ✓ |
| 416 | `recalculateMonsterTable` levels | `resolveMawMonsterLevels` | ✓ (pass 1) |
| 416 | ... HPtable, ×10 rounding | `resolveMonster` health | ✓ |
| 416 | ... affix 12 | — | MON-6 |
| 416 | ... experience, Antagarich, density mult | `resolveMonster` | ✓ (dev 75) |
| 416 | ... AC (L+10)/(LB+10) | `resolveMonster` | ✓ (A3.10) |
| 416 | ... ranged attack 2 | `gainsHellRangedAttack` | ✓ (A3.3) |
| 416 | ... affix 15 on HPtable | live HP | dev 59; MON-10 |
| 416 | ... global `bolsterLevel` clobber | `scriptInfo`, `chestGoldAmount` | MON-17; FMON-2-8 |
| 669 | (commented) dragon-breath LoadMap | — | n/a (dead) |
| 733 | `deepcopy` | — | n/a (helper) |
| 750 | GameInitialized2: `BackupMapStats` | table counts each map | ✓ |
| 765 | BeforeLoadMap: `AdjustMonsterDensity` | `adjustMapEncounters` | ✓ (randomizer skip n/a) |
| 771-795 | `monsterDensity`, `GetDensitySpread/Mean`, `GetMonsterExpMult` | model / `monsterExperienceMultiplier` | ✓ |
| 797 | `AdjustMonsterDensity` | `adjustMapEncounters` | ✓; MON-18 (map 96) |
| 929 | GameInitialized2: `monsterPicTable` | — | n/a (randomizer) |
| 929 | ... HostileTxt 152/143 | `content/hostile_patch.txt` | ✓ (A3.7) |
| 946-1592 | `horizontalMaps`, `madnessStartingMaps`, `mapLevels` | `data/map_levels.yml` | ✓ (dev 7) |
| 1594-1811 | map progressions, `madnessLevel`, `madnessMapLevels` | `MawMapLevels::madnessLevel` | ✓ (phase 9 modes) |
| 1858/1864 | KeyDown/KeyUp Alt raw numbers | inspect ALT | ✓ (H.2) |
| 1871 | `spellToDamageKind` | `mawMonsterInspectNumbers` | ✓ (dev 130) |
| 1884 | `getMonsterLevel` | `facts.level` | ✓; MON-13 |
| 1897/1926 | `staticMapDropLevel`, `MawMapDropLevel` | `MawRules::mapDropLevel` | MON-9 |
| 1937 | GameInitialized2: monster spell multipliers | balance model table | ✓ |
| 1965 | BuildMonsterInformationBox | `mawMonsterInspectNumbers` | dev 130, H.2; side effect FMON-2-11 |
| 2134 | LoadMap: MMMerge bolster off | `bolsterMonstersEnabled = false` | ✓ |
| 2140 | CanSaveGame (food) | `saveFoodCost` | ✓; MON-3 |
| 2172 | AfterLoadMap: Insanity food cap/refund | `capInsanityFood` | ✓ (CHM, deliberate) |
| 2190/2198 | CanCastLloyd / CanCastTownPortal | `teleportBlockedNearEnemies` | ✓ (SPL question on TP) |
| 2208 | GameInitialized2: "Resurrected" names | `actorDisplayName` | ✓ |
| 2213 | LoadMap: first-load roster | — | MON-11 |
| 2228 | LeaveMap: revival | `leaveMap`, `reviveSlainMonsters` | dev 51, MON-1, MON-11; FMON-2-6 |
| 2265/2273 | completion text + LoadMap colour | `mapProgressText` | ✓; MON-16 |
| 2290-2440 | `SeedDeaths.*`, `_A/_B/_C/_D/_H`, `ensure_dir_once`, GameInitialized2 | `MawMadnessLedger` | ✓ (P9.M8) |
| 2442/2448/2462/2470 | BeforeNewGameAutosave, BeforeLoadMap, DeathMap, LeaveMap (ledger) | ledger start/load/partyDied/leaveMap | ✓ |
| 2475 | `mawTick_DeathSeedTimeout` | `MawMadnessLedger::update` | ✓ |
| 2500 | `mawTick_DeathCounterUI` | ledger UI | ✓ (P9 C) |
| 2519 | Action: quit applies pending, load warning | `loadRun`; warning text (MawExperienceRules.cpp:351) | ✓ |
| 2536 | ExitMapAction (clear HUD text) | — | n/a (UI) |
| 2543 | MonsterKilled: completion check | 1 s completion check | ✓ |
| 2550-2566 | `shareMapCompletion`, MultiplayerInitialized, MawMapCompleted | — | n/a (multiplayer) |
| 2568 | `checkMapCompletition` | `mawMapCompletion`, `rewardMapProgress`, `completeDimensionRun` | ✓; MON-2, MON-3 |
| 2799 | `nightmare()`: prompt, Doom bolster, intro texts | Rules panel | dev 2; Madness intro phase 9 |
| 2866/2960/2965 | `mawBossesOnMapReady`, AfterLoadMap, MultiplayerMapDataProcessed | `placeMapBosses` | ✓ (A3.11); affix 17 via `spawnTier` ✓ |
| 2972 | `generateBoss` | `makeBoss` | ✓; MON-8, FMON-2-4, FMON-2-10 |
| 3110 | `SkillList` | `RolledBossAffixes` | ✓ |
| 3115-3183 | `getMapSeedForBossAffixes`, `getSeededSkillForBoss`, `getSeededSpecialBossChance` | `RandomStream` BossAffix | ✓ (RANDOMS) |
| 3186-3235 | `initializePityProtection`, `getPityAdjustedChance`, `checkPityProtectedBoss` | `makeBoss` Madness branch | ✓; FMON-2-9 |
| 3236 | GameInitialized2 (empty) | — | n/a |
| 3239-3318 | `x1/y1/z1/aa1/r1`, `debug.setupvalue` (console logging) | — | n/a (anti-cheat) |
| 3320 | BeforeLoadMap: `vars.ChallengeMode` transport/time | — | n/a (multiplayer, PHASE9 note) |
| 3355-3382 | `inRangeMonIdx`, `inRangeTxt`, `SafeSkillFromPlaceMon`, `Clamp01` | — | n/a (helpers) |
| 3387-3390 | `amountHP/SP`, `leecher` (timer 0.5 s) | `updateMonsters` leech | MON-12; FMON-2-7 |
| 3435 | LoadMap: swift reset | `m_bossTracks` reset | ✓ |
| 3442 | `mawTick_SwiftBosses` (Swift, affix 11) | moveSpeed x2, affix 11 | ✓ |
| 3494 | `calcDices` (commented) | — | n/a (dead) |
| 3536/3577 | `checkOutOfBound` (timer 2 s), LeaveMap | — | FMON-2-12 |
| 3585 | `eliteRegen` (timer 0.1 s) | Regenerating in `updateMonsters` | ✓ |
| 3604 | `mappingRegen` (timer 1 s) | map regeneration | dev 59 |
| 3612 | MonsterKilled: Z − 1 | — | n/a (engine animation fix) |
| 3617/3624 | `resizeList`, GameInitialized2 | — | DAT-4 |
| 3633 | GameInitialized2: Baa names 211-214 | `content/place_mon_names.txt` | ✓ (DAT-8) |
| 3641 | MonsterSpriteScale | `actorDrawScale` | ✓ (A3.12) |
| 3655 | BeforeLoadMap: template AIType | `monster_data_patch.txt` | ✓ (A3.7) |
| 3664 | `mawTick_TurnbasedMoveLimit` | `turnBasedWalkLimit` | ✓ |
| 3682 | `effectNames` | inspect special attack | ✓ |
| 3691 | AfterLoadMap: Doom conditions; disease -> poison | `rollDoomSpecialAttacks`; `resolveMonster` | ✓ (D.20, A3.8) |
| 3750 | AfterLoadMap: anti-cheat, OutdoorLastRefillDay | — | n/a (multiplayer) |
| 3766 | `calculateDirection` | — | n/a (helper for DM) |
| 3774 | AfterLoadMap: MAWBOLSTER labels | — | n/a (phase 9 UI) |
| 3785 | MonsterDropItem 80 % | `keepsDeathDrop` | ✓ (A3.9) |
| 3810-3880 | `transform`, `explosionRemap`, `MawEnableProjectileImpact`, GameInitialized2, `mawTick_RestoreProjectiles` | 3D projectiles; fire arrow 545 -> 550 | n/a (visuals); A1.9 |
| 3884 | PlayerAttacked: MM6 projectile target/cover/Fixator | `coverMonsterAttack`, `applyMonsterHitEffects` | dev 20, dev 10 |
| 4019/4034 | GameInitialized2 `baseTransportTable`; LeaveMap `storeTime` | — | n/a (multiplayer) |
| 4044 | MonsterKilled: death-drop thinning | `keepsDeathDrop` | ✓ (A3.9) |
| 4044 | ... ally-killed / ally-killer experience | — | FMON-2-2 |
| 4044 | ... experience reset to template | `facts.experience` | MON-1, MON-7 |
| 4044 | ... Omnipotent 14 bosses, Broodlord/Broodling hatch | `hatchBoss` | ✓ (L3.2; radius cosmetic) |
| 4126 | `mawForgetBoss` | facts live on the actor | ✓ |
| 4139 | PickCorpse: Insanity risen empty; NameId reset | `corpseLoot` | ✓ |
| 4161 | `getMonsterDamage` (commented) | — | n/a (dead) |
| 4205/4311 | `nudgeMonsterAroundCorner`, MonstersProcessed | — | FMON-2-12 |
| 4334-4368 | GameInitialized2 `engLocalizedMap`, `englishMapName`, `aliasLocalizedNames` | bands keyed by map file | ✓ (dev 7) |
| 4370 | `getDistances` | — | n/a (helper) |
| 4376/4390 | `isRedone` fixes | — | n/a (MM Redone only) |
| 4404 | safe wrapper of `recalculateMawMonster` | — | n/a |
| 4420 | PickCorpse: Madness rewardless maps | `madnessRewardlessMap` | ✓ |
| 4433 | KeyDown K: pull corpses and crafting items | `gatherLoot` | dev 139 |
| 4468 | GameInitialized2: scheduler registrations | `updateMonsters` | ✓ |

### zzBossSync.lua (solo paths)

| Line | MAW entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 10-30 | `mawmapvarsend` shim | — | n/a (multiplayer) |
| 32-56 | `inMulti`, `isHost`, `NOW`, `schedule_refresh`, `HostBurst_Start` | — | n/a |
| 60-82 | `client_purge_all_boss_marks`, `client_purge_except_set` (runs solo) | — | FMON-2-11 (NameId 300 purge) |
| 85-153 | `apply_boss_names`, `apply_boss_set`, `refresh_all_boss_labels` | boss facts restored from the save | ✓ |
| 156-296 | MAWMapvarArrived, snapshot request/broadcast, ClientJoined | — | n/a (multiplayer) |
| 298 | BeforeLoadMap (client only) | — | n/a |
| 310/327/332 | `on_map_ready`, AfterLoadMap, MultiplayerMapDataProcessed | save/load of facts | ✓ |
| 338 | Tick (refresh window, host bursts) | — | n/a |
| 366-564 | boss debug (`whoAmI` ... `onAfterLoadMap`, F9 disabled) | — | n/a (debug) |

### zzMaw_MonsterHit.lua

| Line | MAW entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1 | `safeGet` | — | n/a (helper) |
| 12 | `MawRollDodge` | `characterEvades` Speed roll | ✓ (one roll) |
| 18 | `rollHit` | — | n/a |
| 25 | hook 0x425893 (melee and monster missiles) | `monsterAttackLands` = true | FMON-2-1 |

### pseudoSpawnpoint.lua

| Line | MAW entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 2 | `getRange` | `GameplayMonsterSpawnRequest.count` | ✓ |
| 14 | `pseudoSpawnpoint` (tier by powerChances, radius, wall retry, limit − 20, treasure on, group) | `IGameplayWorldRuntime::spawnMonsters` | ✓ (`vars.seed` reseed: RANDOMS) |
| 152 | `psp` | — | n/a (debug) |
| 157/166 | `table.join`, `joinTables` | — | n/a (helpers) |

### zSERIOUSMAW.lua

| Line | MAW entry | OpenYAMM counterpart | Status |
|---|---|---|---|
| 1 | GameInitialized2: PlaceMonTxt 200-205, 304 | 205 in `content/place_mon_names.txt`; 200-204 unused by maps; 304 overwritten by MAW | ✓ (DAT-8 for the id range) |
