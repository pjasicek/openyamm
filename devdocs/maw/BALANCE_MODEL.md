# MAW balance model and monster resolution

> Formulas updated to MAW `8fbb48d1` (2026-11-05) and `8967ae88` (2026-11-12) where [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) and [UPSTREAM_SYNC_8967ae88.md](UPSTREAM_SYNC_8967ae88.md) list a change.

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`. Paths below are relative
to its `Scripts/` folder; `E:n` means `Modules/MawCore/Estimates.lua` line n, `M:n` means `General/zzMaw-Monsters.lua`
line n.

This document covers the monster side of MAW completely: the balance model in `Estimates.lua` (every function, curve,
table and constant, plus every external table it reads), how monster level, HP, damage, AC, resistances and
experience are resolved in every mode, and golden output produced by running the model. Machine-readable drafts:

| File | Contents |
|---|---|
| [data/balance_golden.csv](data/balance_golden.csv) | Model output, levels 1-2000, all difficulties, solo/party |
| [data/map_levels.yml](data/map_levels.yml) | `mapLevels` bands by map file, starter maps, Madness levels |
| [data/difficulty.yml](data/difficulty.yml) | Every per-difficulty number and flag |
| [data/monster_scaling.yml](data/monster_scaling.yml) | Level, HP, damage, AC, resistance, EXP, treasure rules |
| [data/bosses.yml](data/bosses.yml) | Boss spawning, stats, 14 affixes, Broodlord, Broodling, Omnipotent |
| [data/dimension_affixes.yml](data/dimension_affixes.yml) | The 33 dimension-map affixes with their real effects |
| [data/exp_curve.yml](data/exp_curve.yml) | Experience curve, banks, kill/quest/completion experience |
| [MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md) | `MONSTERS.txt` and `mapstats.txt` diff against base MMMerge |

Read [COMBAT.md](COMBAT.md) §3-6 for the surrounding mechanics; section 12 lists what in it is wrong.

---

## 1. The model in one page

MAW does not tune monsters directly. It builds an **expected character** for any level L: the skill level, stats,
gear and buffs an average character of that level is assumed to have, using the same curves the real game code uses.
From that character it derives two numbers:

- **Power**: expected damage output, normalised so that 1 "hit" is one attack at the weapon's base recovery
  (`getPlayerEstimatedPower`, E:545-600). It includes attack speed, crits, weapon enchants, legendary bonuses and
  hit chance, so it is closer to damage per unit time than damage per swing.
- **Vitality**: expected effective HP, i.e. HP divided by the expected share of damage that gets through armour,
  resistances, dodge and legendary reductions, times a Cover bonus (`getPlayerEstimatedVitality`, E:440-452).

Every monster family is then sized against the expected character **at the family's B-tier level**:

```
monster HP     = Power(L_B)    x hitToKillMonster[difficulty] x tier HP ratio x boss HP mult
monster damage = Vitality(L_B) / hitToKill[difficulty]        x tier damage mult x boss damage mult
```

`hitToKillMonster` runs from 1 (Easy) to 5 (Beyond Madness): how many "hits" of the expected character a B monster
takes. `hitToKill` runs from 14 down to 4: how many monster hits kill the expected character. Monster levels come
from a separate resolver (section 7) that depends on progression mode, the map's level band and the party's banked
levels. Monster damage from the MONSTERS.txt dice is ignored, except as a ratio between Attack1 and Attack2.

Because the expected character itself depends on the difficulty (more monsters means more loot seen, which means
better gear in the model), the ratio between difficulties is not simply the ratio of the hit tables (section 9.2).

---

## 2. How the golden output was produced

### 2.1 Harness

The model was run, not re-implemented: a scratch harness loads MAW's own source lines into a Lua 5.4 interpreter and
calls MAW's functions. The harness (`harness.lua` plus a driver script) lived in the session scratchpad and is not
kept in either repository; this section is enough to rebuild it.

Source lines loaded verbatim (as chunks; `General/` unless noted):

- `zzMaw-Stats.lua:263-267, 296-298`: `STAT_DAMAGE_DIVISOR`, `GetMightDamageMultiplier`,
  `getIntellectDamageMultiplier`
- `zzMaw-Stats.lua:947-951`: `events.GetStatisticEffect` (the "1 effect per 5 points from 25" hook)
- `zzMaw-Stats.lua:1462-1530`: `masteryForSkill`, `masteryPerLevel`, `GetGradualMasteryValue`, `masteryThresholds`,
  `GetDifficulty`
- `zzMAW-Skills.lua:23-182, 408-418`: weapon/armour skill tables, `armsmasterSkill`, `skillCap`, `skillEffectCap`,
  `SPELL_HASTE_DIVISOR`, `GetSpeedBonusFromStat`
- `zzMaw-Items.lua:444-893`: enchant strength curves, loot tier, rarity tables, `GetExpectedEnchantFraction`,
  `GetPrimordialCharges`, `GetDifficultyExtraPower`, `TIER_LEVELS`
- `zzMaw-Items.lua:2047-2064, 2097, 4283`: `enchantbonusdamage`, `ENCHANT_DAMAGE_MULT`, `LEGENDARY19_ENCHANT_MULT`,
  `fireAuraDamage`
- `zzMaw-Spells.lua:80-82, 2063-2067, 2334-2353, 2655-2691`: heal helpers, `GetBuffMultiplier`, `GetBuffStatPct`,
  `buffPower`
- `Global/zzMaw_Mapping.lua:36-56`: the `buffPower` table that is live in game (section 5.1)
- `Modules/MawCore/Formulas.lua`, `ItemLevel.lua`: whole files
- `zzzMaw_Experience.lua:7-45`: `calcLevel`, `calcExp`
- `zzMaw-Monsters.lua:5-25, 770-796`: `bolsteredLevel`, `MawTierB`, density tables, `GetMonsterExpMult`
- `Modules/MawCore/Estimates.lua:1-753`: whole file, with its locals exported at the end for the extra CSV columns

Shims (everything else the code touches):

- `round` = MAW's own half-up `round` (`zz_Maw-initialize.lua:315-322`); `table.find`; `unpack`.
- `const.Skills` and the used `const.Spells` ids with **MM8 values** (MMExtension `Core/ConstAndBits.lua`): Sword 1,
  Chain 10, Alchemy 37; Haste 5, Fire Resistance 3, Shield 17, Stone Skin 38, Bless 46, Fate 47, Heroism 51,
  Heal 68, Cure Disease 74.
- `Game.GetStatisticEffect(v)`: the engine table at 0x48E18E (thresholds 500 400 350 300 275 250 225 200 175 150 125
  100 75 50 40 35 30 25 21 19 17 15 13 11 9 7 5 3 0 → 30 25 20 19 18 17 16 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 0
  −1 ... −6, same as OpenEnroth `Character.cpp:235-240`), then MAW's hook (`floor(v/5)` from 25). The model passes
  fractional stats; MMExtension's `mem.call` hands the engine an int32. **Assumption: truncation.** With rounding
  instead, results differ by at most 6.5 % (power) and 0.4 % (vitality), and only at levels below about 10.
- `vars`, `Game.BolsterAmount`, `Party.Count` per configuration (2.2). `MawCore`, `mapvars`, `events` as empty tables.
- `encStrUp` set to `encStrUpAusterity` when Austerity is on, as `zzMaw-Items.lua:895-901` does on BeforeLoadMap.
- Lua 5.4 instead of LuaJIT: the loaded code uses no integer-only or 5.1-only behaviour; all values stay far below
  2^53.

### 2.2 Configurations

Each configuration runs in a fresh interpreter, because the model caches per difficulty.

| config | `BolsterAmount` | `vars` | Index |
|---|---|---|---|
| `easy_normal` | 50 | - | 1 (bolster 0 gives identical numbers) |
| `unreachable70` | 70 | - | 2 |
| `maw` | 100 | - | 3 |
| `hard` | 150 | - | 4 |
| `hell` | 200 | - | 5 |
| `nightmare` | 300 | `trueNightmare` | 6 |
| `doom` | 600 | `Mode = 2` | 7 |
| `insanity` | 600 | `Mode = 2`, `insanityMode` | 8 |
| `madness` | 600 | `Mode = 2`, `insanityMode`, `madnessMode` | 9 |
| `aust_*` | 50-300 | `Mode = 8`, `AusterityMode` (+ `trueNightmare` at 300) | 1-6 |

Each is run with `Party.Count` 5 and 1. Levels: 1-100 every level, 110-600 every 10, 700-2000 every 100.

### 2.3 CSV columns

`config, austerity, party_count, level, difficulty` then: `skill` (`estimateSkill`), `mastery` (`masteryPerLevel`),
`stat` (`estimateStat`), `geared` (`gearedFraction`), `max_enchant` (`GetMaxEnchantStrength`), `health`, `mana`,
`armor_class`, `resistance`, `enchant_resistance`, `phys_taken`, `magic_taken`, `chance_hit`, `legendary_taken`,
`cover_mult`, `vitality`, `attack`, `power`, `spell_power`, `monster_hp_b` (`getMonsterHealth(nil, L)`),
`monster_dmg_b` (`getMonsterDamage(nil, L)`), `exp_mult` (`GetMonsterExpMult`). 4,920 rows, 6 significant digits.

`monster_hp_b` and `monster_dmg_b` are the B-tier, non-boss values for a family whose B row resolves to level L. For
A and C rows multiply HP by the clamped table ratio (section 6.1) and damage by 0.66 or 1.5.

### 2.4 Variants checked

- **`buffPower` source.** In game the table from `Global/zzMaw_Mapping.lua` replaces the one in `zzMaw-Spells.lua`
  after the first map load (5.1). The golden file uses the live table. With the `zzMaw-Spells.lua` table instead,
  vitality and monster damage drop by up to 1.25 % (largest at levels 20-60); power, attack and HP do not change.
- **Stat conversion**, see 2.1.
- Healing (`getPlayerEstimatedHealing`) was not run: it needs `oldTable`, the spell delays copied from the live
  `Game.Spells` at startup (`zzMaw-Stats.lua:147-155`). It does not feed monsters.

---

## 3. `Estimates.lua`, function by function

Notation: `s` = estimated skill level, `m` = its mastery (1-4), `th` = `masteryThresholds()`, `ramp(x)` = clamp to
[0, 1], `GGMV(tbl, s, m)` = `GetGradualMasteryValue` (3.2). Tables written `{a, b, c, d}` are indexed 1-4 by mastery
with index 0 = 0 unless stated.

### 3.1 Small helpers (E:18-77)

- `buffRamp(s) = ramp((s - th[2]) / (th[3] - th[2]))` (E:19-22): a buff is worth nothing below the Expert threshold and
  full value at the Master threshold (4 → 7, insanity 8 → 16, madness 10 → 24).
- `gradualRow(tbl, s, m)` (E:24-29): `tbl[1]` (or 0) at mastery ≤ 1, else `GGMV(tbl, s, m)`.
- `casterSkill(spell, s) = min(s, 75 for spells 83/85/86 (Day of the Gods, Day of Protection, Hour of Power), else
  50)` (E:32-35), the `skillEffectCap` numbers.
- `buffFlat(spell, s, m, L, div = 4)` (E:37-46):
  `(gradualRow(Base) + L/div) x (1 + gradualRow(Scaling)/100 x casterSkill) x buffRamp(s)`, using `buffPower[spell]`.
  `CASTER_LEVEL_DIVISOR = STONESKIN_LEVEL_DIVISOR = 4`.
- `buffMult(spell, s, m)` (E:48-55): `gradualRow(Base)/100 x buffRamp(s) x (1 + 0.02 x casterSkill)`
  (`BUFF_MULT_PER_SKILL = 0.02`).
- `masterLearned()` (E:59-66): 12, 20 (insanity), 30 (madness). **Never called.**
- `estimateWeaponDamageMultiplier(L) = 1 + 0.02 x estimateSkill(L)` (E:68-70).
- `legendaryRamp(L) = ramp((L - 100) / (420 - 100))` (E:72-77): legendary items phase in from level 100 to 420.

### 3.2 Skill and mastery

- `skillPointsAtLevel(L)` (E:79-86): 0 below level 2, else with `q = floor(L/10)`, `r = L - 10q`:
  `5 (L - 1) + 5 q (q - 1) + q (r + 1)`. This is MAW's skill-point income (5 per level plus a growing bonus per ten
  levels).
- `skillLevelFromPoints(p) = (sqrt(1 + 8 (p + 1)) - 1) / 2` (E:88-90): the skill level whose cumulative cost
  `s (s + 1) / 2 - 1` equals p.
- `estimateSkill(L) = skillLevelFromPoints(skillPointsAtLevel(L) / 5)` (E:92-95, `SKILLS_TRAINED = 5`): the points are
  spread over five skills.
- `masteryForSkill(S)` (`zzMaw-Stats.lua:1462-1469`): the highest i in 4..1 with `S >= th[i]`;
  `masteryPerLevel(L) = masteryForSkill(estimateSkill(L))` (:1471-1473).
- `masteryThresholds()` (:1497-1505): `{0, 4, 7, 10}`, insanity `{0, 8, 16, 25}`, madness `{0, 10, 24, 40}`.
- `GetGradualMasteryValue(tbl, s, m)` (:1480-1495): mastery 0 → `tbl[0]`; otherwise ramps linearly from
  `tbl[m-1]` (or 0) at `th[m]` to `tbl[m]` (or `tbl[m-1]` if missing) at `th[m+1]` (GM: at `1.4 x th[4]`).

Resulting skill: 1.0 at level 1, 4.0 at 10, 11.4 at 50, 19.1 at 100, 33.7 at 200, 76.4 at 500, 147 at 1000, 289 at
2000. Mastery: Expert from level 10, Master from 24, GM from 42 (normal thresholds); 30/80/150 in Road to Insanity,
42/140/250 in Beyond Madness.

### 3.3 Weapon (E:98-158)

Constants: `WEAPON_BASE_DICE_DAMAGE = 8`, `WEAPON_TIER_FLAT_DAMAGE = 16`, `WEAPON_FLAT_PER_LEVEL = 0.5`,
`WEAPON_FLAT_PER_POWER = 2`, `WEAPON_DICE_PER_POWER = 2`.

- `weaponTierFlat(tier) = 16 x (clamp(tier, 1, 6) - 1) / 5` (E:101-105), default tier `ItemLevel.ExpectedTier = 3.5`.
  **Not used by the model.**
- `estimateWeaponFlat(L) = min(0.5 L, 16)` (E:109-111): the expected base type's flat damage.
- `getWeaponDamageForLevel(IL, twoHanded, flat)` (E:120-139), with `power = min(ItemLevel.PowerFor(IL), 255)` and
  `PowerFor(IL) = min(floor(IL/5), 100)`:
  - `flatPower = floor(power/2)`; `powerFlat = 2 x flatPower`; `powerDice = 4 x (power - flatPower)`
  - `diceOnly = 16 + powerDice`; `flatOnly = flat + powerFlat`; `levelDamage = powerFlat + powerDice/2`
  - one-handed: all three halved
  - returns `(diceOnly + flatOnly, diceOnly, flatOnly, levelDamage)`. The first value is always the sum of the other
    two, so every `wDmg - wDice - wFlat` term downstream is **identically 0** (a leftover of an older half/half split).
- `estimateStatFlatDamage(IL) = GetStatisticEffect(estimateStat(IL))` (E:141-143).
- `getWeaponLevelDamage(IL, twoHanded, wFlat)` (E:145-158): the "item-level weapon damage" enchants scale from:
  `armsSkill = 1.5 estimateSkill(IL)`; `arms = GGMV(armsmasterSkill.Damage, armsSkill, masteryForSkill(armsSkill)) x
  armsSkill`; one-handed halves `arms` and the stat bonus; result
  `((levelDamage + arms) x (1 + 0.02 estimateSkill(IL)) + statEffect) x (1 + estimateStat(IL)/1000)`.

### 3.4 Gear: how much enchant power the character wears (E:160-226)

- `STAT_SHARE = 0.2`, `TOTAL_SLOTS = 13.75` (2h weapon 2, cloak 1, helm 1.25, armour 1.5, gloves 1.25, boots 1.25,
  rings 0.75 x 6, amulet 1, bow 1.25, belt 1, minus 2.25 for ring resistance enchants), `ENCHANTS_PER_ITEM = 3`.
- `getTotalEnchantPower(L) = 3 x 13.75 x GetMaxEnchantStrength(L)` (E:168-170).
- `GetMaxEnchantStrength(L) = encStrUp(GetLootTier(L)) x GetDifficultyExtraPower() x 1.1` (`zzMaw-Items.lua:492-496`;
  `1.1 = (PRIMORDIAL_ENCHANT_MULT 1.25 - 1) x 0.4 + 1`, "items are Primordial or Legendary").
  - `GetLootTier(L) = L/15 + GetLootStrength(L)`, `GetLootStrength(L) = min(1 + L/15, 6)` (:482-490,
    `TIER_LEVELS = 15` at :889).
  - `encStrUpNormal(t) = 1 + 2t` up to t = 12, then `25 + min(3 (t - 12), 75)` (cap 100) (:444-449).
  - `encStrUpAusterity(t) = t + 2` up to 30, then `32 + 2 (t - 30)` (uncapped) (:451-456).
  - `GetDifficultyExtraPower()`: 1.2 insanity, 1.1 Doom, 1.05 true Nightmare, else 1 (:552-561).
  - Result: 3.6 at level 1, 18.0 at 50, 29.7 at 100, 51.7 at 200, capped at 110 from level 465 (Normal/MAW).
- `gearedAnchor(L) = (L + 20) / (L + 100)` (E:172-174), fitted against Beyond Madness ("GEARED_ANCHOR_DIFFICULTY = 9",
  "GEARED_ANCHOR_DENSITY = 1").
- `dropsSeenPerSlot(L, d) = (L / (3.6 + L/140) + 1) x d` (E:204-206): `DROPS_PER_SLOT_RATE = 3.6`,
  `DROPS_PER_SLOT_CAP = 140`.
- `DROPS_DENSITY_BY_DIFFICULTY` (E:192-202): 0.40, 0.40, 0.40, 0.43, 0.43, 0.47, 0.59, 0.66, 0.70 for indices 1-9.
- `gearedFraction(L) = gearedAnchor(L) x EEF(tier, drops(L, density[d]), d) / EEF(tier, drops(L, 1), 9)` (E:210-226),
  cached per difficulty. EEF is `GetExpectedEnchantFraction` (`zzMaw-Items.lua:867-877`): the expected enchant
  fraction of the **best of n drops**:
  - `rarityItemFraction(r) = enchantCount[r] / 3 x mean(r) / mean(Primordial)`, `mean = (Min + Max) / 2 / 20` from
    `enchantStrengthRange` (Celestial/Primordial 25-25, Ancient 20-25, Legendary 16-20, others 8-20) and
    `enchantCountByRarity` (Common 0, Uncommon 1, Rare 2, Epic and up 3): Common 0, Uncommon 0.187, Rare 0.373,
    Epic 0.56, Legendary 0.72, Ancient 0.9, Primordial and Celestial 1.0 (:822-833).
  - `GetRarityDistribution(tier, d)` (:835-852): Common..Epic from `GetEnchantBands` (thresholds
    `min(Base + PerTier x tier, Cap)`: Epic 5/0.75/20, Rare 20/2/60, Uncommon 60/1/80, Common 100/0/100; band widths
    scaled by `rarityBandMult[d]` and normalised, :624-653); then the Epic share is split by the upgrade cascade
    Celestial 0.002, Legendary 0.03, Primordial 0.04, Ancient 0.12 (:585-590), each times
    `rarityDifficultyMult[d] x GetEnchantChance(Uncommon, tier) / 80` (:757-763).
  - `EEF = sum over rarities sorted by fraction of fraction(r) x (cum_r^n - cum_{r-1}^n)`.
  - Result at MAW: 0.115 at level 1, 0.284 at 50, 0.394 at 100, 0.613 at 300, 0.776 at 1000, 0.827 at 2000; higher
    on harder difficulties (Beyond Madness 0.569 at level 100).

### 3.5 Stats (E:228-237)

```
estimateStat(L) = (17 + min(L, 500) x 0.2 + getTotalEnchantPower(L) x 0.25 x gearedFraction(L))
                  x (1 + GetBuffStatPct(s, true) x buffRamp(s))
```

`17` is the creation stat, `0.2 per level` (to level 500) the alchemy black potions, `GetBuffStatPct(s, light=true)
= min(10 + s/7, 20) / 100` the Day of the Gods aura (`zzMaw-Spells.lua:2665-2668`). One number stands for every
stat (Might, Endurance, Speed, Luck, Accuracy, Intellect). 21.5 at level 1, 88.9 at 50, 178 at 100, 395 at 200,
1085 at 500, then nearly flat (1266 at 2000) because enchant strength caps at 465 and alchemy at 500.

### 3.6 Health and mana (E:240-345)

- `hpPerLevel(L) = min(6 L / P, 6) + 3`, P = 330 in madness else 210 (E:247-251): 3 to 9 HP per level, reaching 9
  at the promotion level. `spPerLevel` is identical (E:302-306).
- `computeHealth(L)` (E:253-272), cached per mode and bolster:
  - `hp = stat/10`; `flatBonus = hp x min(1 + hp/50, 5) x 4` (HP enchants);
  - `enduranceEffect = stat/5`;
  - `bbMastery = min(m, 3)` (`BODYBUILDING_MASTERY`, the average character stops at Master);
  - `bodybuildingFlat = s x gradualRow({1, 2, 3}, s, bbMastery)`;
  - `bodybuildingPct = GGMV(bodybuildingHP = {0.5, 1, 1.5, 2}, s, bbMastery)` (`zzMAW-Skills.lua:105`);
  - `health = (25 + perLevel x L + (enduranceEffect + bodybuildingFlat) x perLevel + flatBonus)
    x (1 + bodybuildingPct x s / 100) x (1 + stat / 1000)`.
- `computeMana(L)` (E:308-319): `pool = 15 + perLevel x (L + 2 x statEffect + s x gradualRow({1, 2, 3, 5}, s, m))`
  (`MED_PER_RANK`, GM counts 5), `x (1 + gradualRow(enlightenmentManaPerSkill = {0.5, 1, 1.5, 2}, s, m) / 100 x s)`.

### 3.7 Defence (E:347-437)

- `EXPECTED_NEARBY_MONSTERS = 5`, `ARMOR_REFERENCE_AC = 116`.
- `estimateWornArmor(L) = (116 + 116 x c / 40) x gearedFraction(L)` (E:350-354), `c = GetPrimordialCharges(L) =
  min(max(round(1.2 PowerFor(L)), PowerFor(L) + 4), 255)` (`zzMaw-Items.lua:512-529`), `Formulas.chargesArmorAC`.
- `estimateArmorClass(L) = worn x (1 + 0.5 legendaryRamp + gradualRow(skillItemAC[Chain] = {3, 4, 5, 6}, s, m) x s
  / 100) + buffFlat(Stone Skin 38, s, m, L, 4)` (E:356-366; `LEGENDARY_28_ARMOR = 0.5`).
- `estimateResistance(L) = worn x gradualRow(skillItemRes[Chain] = {1, 2, 3, 4}, s, m) x s / 100 + buffFlat(Fire
  Resistance 3, s, m, L) + statEffect(stat)` (E:368-376): one element stands for all six; Luck adds the stat effect.
- `estimateEnchantResistance(L) = (GetMaxEnchantStrength(L) x 100 / 200) x (1 + 0.5 legendaryRamp)` (E:378-383): a
  ring resistance roll (`Formulas.resistanceEnchantPower`, `ringReductionDivisor = 200`), `LEGENDARY_16_RESISTANCE`.
- `estimateChanceToGetHit(L) = 1 / (1 + stat / (100 + stat) x 0.5)` (E:385-387, `Formulas.chanceToBeHit` with the
  monster at the same level, `speedDodgeShare = 0.5`).
- `estimatePhysicalDamageTaken(L) = max(1 / (AC / (200 + L) + 1), 0.1)` (E:389-392).
- `estimateMagicDamageTaken(L) = max(1 / (res / (100 + L) + 1) x max(1 - buffMult(Shield 17), 0.7)
  x 1 / (enchantRes / 100 + 1), 0.1)` (E:394-403).
- `estimateLegendaryDamageTaken(L) = (1 - 0.10 r) x (1 - (1 - 0.97^5) r)`, r = legendaryRamp (E:405-412;
  `LEGENDARY_18_REDUCTION = 0.10`, `LEGENDARY_22_PER_MONSTER = 0.03`).
- Cover (E:414-437): `COVER_BASE = 0.10`, `COVER_PER_SKILL = 0.01`, `COVER_GATE = {0, 1}`;
  `gate = gradualRow(COVER_GATE, s, m)`; `p = min(0.1 + 0.01 s, 0.1 + 0.01 x skillCap[50] = 0.4) x gate`;
  `ratio = TANK_VITALITY_RATIO = 2`, or `1 / 0.5 = 2` solo;
  `coverMultiplier = 1 / ((1 - p) + p / ratio)`. **At GM the gate reads `tbl[3]` (nil) and drops to 0**, so Cover
  only counts while the estimated skill is in the Expert-Master band (levels 10-41 normally, 30-140 in Road to
  Insanity, 42-240 in Beyond Madness).

### 3.8 Vitality (E:440-452)

```
taken    = (physical x 0.5 + magic x 0.5) x chanceToGetHit x legendaryTaken      (physicalVitalityShare = 0.5)
vitality = health / taken x coverMultiplier
```

Returns `vitality, physical, magic, taken, health`. 62.8 at level 1, 1094 at 50, 3569 at 100, 18,860 at 200,
186,940 at 500, 1.51 million at 2000 (MAW difficulty, party of 5).

### 3.9 Attack (E:522-543)

`SKILL_ENCHANT_MULT = 1.5`, `LEGENDARY_33_SKILL = 10`; `getMeleeSkill(L) = 1.5 s + 10 legendaryRamp` (E:524-526).

```
attack = wFlat                                   (the (wDmg - wDice - wFlat)/2 term is 0)
       + GGMV(skillAttack[Sword] = {1, 2, 3, 4}, melee, masteryForSkill(melee)) x melee
       + GGMV(armsmasterSkill.Attack = {1, 1, 1, 1}, s, m) x s
       + statEffect(stat)
       + buffFlat(Bless 46, s, m, L)
```

Used by `Formulas.mawHitChance` as the par attack for a monster of level L.

### 3.10 Power (E:497-600)

Constants: `expectedEnchantCoeff = enchantbonusdamage[46].Coeff (0.5) x ENCHANT_DAMAGE_MULT (1)`,
`EXPECTED_ENCHANT_LEVEL = 100`, `EXPECTED_WEAPON_DICE = 3`, `LEGENDARY_21_PER_MONSTER = 0.05`,
`LEGENDARY_11_DAMAGE = 0.15`, `LEGENDARY19_ENCHANT_MULT = 1.5` (`zzMaw-Items.lua:2097`).

```
(wDmg, wDice, wFlat) = getWeaponDamageForLevel(L, two-handed, estimateWeaponFlat(L))
melee   = getMeleeSkill(L);              wsm = 1 + skillDamage[Sword] (2) x melee / 100
arms    = 1.5 s;                         armsBase = GGMV(armsmasterSkill.Damage = {0, 1, 1, 1.5}, arms, m(arms)) x arms
scal    = 0 + wFlat + 0.5 wDice + armsBase
damage  = 1.5 + scal x wsm + max(melee - scal x (wsm - 1), 0)          (a weapon skill point is worth >= 1 damage)
damage  = (damage + statEffect) x (1 + buffMult(Heroism 51)) x (1 + stat / 1000)
speed   = GetSpeedBonusFromStat(stat) / 100                     ((stat - 13)/4 up to 21, else floor(stat/10))
        + GGMV(skillRecovery[Sword] = {0, 1, 1, 2}, melee, m(melee)) x melee / 100
        + GGMV(armsmasterSkill.Speed = {0, 0, 1, 1}, arms, m(arms)) x arms / 100
damage *= (1 + speed) x (1 + buffMult(Haste 5))
cc      = stat / min(500 + 5L, 3000) + 0.05 + 0.1 r + buffMult(Fate 47)      (luck = accuracy = stat)
cd      = stat / min(250 + 2.5L, 2000 or 3000 in madness) + 1.5 - 1
critM   = 1 + min(cc, 1) x cd;       damage *= critM
encL    = (1 + 0.5 r) x (1 + (critM - 1) r)                                    (legendary 19, crits on enchants)
encBase = getWeaponLevelDamage(L, two-handed, wFlat) x encL
damage += encBase x 0.5 x min(L / 100, 1) + encBase x GGMV(fireAuraDamage = {0.1, 0.15, 0.2, 0.25}, s, m)
damage *= min(1 + 0.05 x 5 x r, 2) x (1 + 0.15 r)                             (legendaries 21 and 11)
damage *= max(cc, 1)                                                           (crit chance overflow)
power   = damage x min(0.75 + blessHit(s), 1),  blessHit(s) = 0.05 + 0.05 x min(s, 50) / 50
```

r is `legendaryRamp(L)`. Legendary 29 (resistance shred) and 12 (hybrid builds) are not modelled (E:515-519).
13.7 at level 1, 276 at 50, 799 at 100, 4,141 at 200, 69,395 at 500, 1.08 million at 2000 (MAW).

### 3.11 Spell power and delay (E:602-653)

- References: novice Fire Bolt `{add 8, dice 2, delay 110}`, GM Incinerate `{add 19, dice 21, delay 90}`,
  interpolated by `t = min(s / th[4], 1)` (E:602-612).
- `estimateSpellDelay(L, base) = base / (1 + floor(stat / 20) / 100) x 1.015^s / (1 + buffMult(Haste))` (E:614-620,
  `SPELL_HASTE_DIVISOR = 20`).
- `getPlayerEstimatedSpellPower(L)` (E:622-653): `empower = 1 + buffMult(Haste 5)` (see 5.3);
  `dice x= empower x spellDiceScale(s)`, `add x= empower x spellAddScale(s)` (`(1 + 0.02 s) 1.02^s` and
  `(1 + 0.01 s^2) 1.02^s`); `power = add + 1.5 s (1 + dice) / 2`; `x (1 + stat / 1000)`; crit with
  `Formulas.critDamageMult(stat, L, madness, isSpell)` = `stat / (4 dim) + 1.5`; plus weapon enchant damage
  `encBase x (0.5 min(L/100, 1) + GGMV(fireAuraDamage)) x 1.015^s`; divided by `delay / 100`; `x max(cc, 1)`.
  Not used for monsters; in the CSV for completeness.

### 3.12 Healing (E:655-676)

`estimateHealingFor(spell, L, s, m) = (base + scaling x s) x (1 + stat / min(1000 + 3L, 4000)) / (delay / 100)` with
`ascendHealingValues` (`scaling x (1 + 0.02 s) 1.015^s`, `base x (1 + 0.01 s^2) 1.015^s`, both rounded) over
`getBaseHealingSpells()` rows (Heal `{4, 8, 12, 16}` + `{2, 3, 4, 6}`/skill; Cure Disease `{-, -, 25, 40}` +
`{-, -, 7, 10}`; insanity has its own rows) and the spell delay from `oldTable`. `getPlayerEstimatedHealing` takes the
better of Heal and Cure Disease. Used by skill tooltips and regeneration; not by monsters; not run (2.4).

### 3.13 `getMonsterDamage` and `getMonsterHealth` (E:458-495, 678-726)

```
getMonsterDamage(mon, L):
  hits = {14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4}[difficulty], Austerity {15, 10, 5, 4, 3, 2.5, 2, 1.5, 1}
  if mon: L = totalLevel[MawTierB(mon.Id)] or L
  damage = vitality(L) / hits
  if mon: x0.66 for A (Id % 3 == 1), x1.5 for C (Id % 3 == 0);
          NameId 220..300: generateBoss(index) if it has no record yet (host only), x bossData.DamageMult

getMonsterHealth(mon, L):
  hits = {1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5}[difficulty], Austerity {1, 2, 4, 5, 6, 7, 8, 9, 9.5}
  if mon: L = totalLevel[MawTierB(mon.Id)] or L
  health = power(L) x hits
  if mon: x clamp(FullHP(row) / FullHP(B row), 0.6, 1.8) from the unmodified MONSTERS.txt (basetable)
          (a mock {Id, Level} without GetIndex stops here)
          NameId 220..300: generateBoss if needed, x bossData.HealthMult
```

Called with `nil` the functions return the B-tier, non-boss value; that is what the CSV holds.

### 3.14 Commented-out blocks (E:671-676, 728-753)

Two `--[[ ]]` test loops: a healing readout (HPS as a share of max HP for levels 10-500) and the **old HP curve**
`HP = i (i/10 + 3) x 2 x (1 + i/360)`, x `(2 + i/300)` at bolster 600, x `(1.5 + i/300)` in insanity, divided by
`clamp(0.3 + L/200, 1, 50/15)`, x `2^(res/100)` with `res = i/2`, printed as a ratio to `GetPlayerEstimatedPower`
(note the capital G: that function no longer exists). Dead code, documented for archaeology only.

---

## 4. Every external table and constant the model reads

- `masteryThresholds()`: `{0,4,7,10}`, insanity `{0,8,16,25}`, madness `{0,10,24,40}` (`zzMaw-Stats.lua:1497-1505`)
- `GetGradualMasteryValue`, `masteryForSkill`, `masteryPerLevel`: section 3.2 (`zzMaw-Stats.lua:1462-1495`)
- `GetDifficulty()`: section 2.2, [data/difficulty.yml](data/difficulty.yml) (`zzMaw-Stats.lua:1507-1530`)
- `Game.GetStatisticEffect`: engine table + MAW hook `floor(v/5)` from 25 (`zzMaw-Stats.lua:947-951`)
- `STAT_DAMAGE_DIVISOR`, `GetMightDamageMultiplier`, `getIntellectDamageMultiplier`: 1000; `stat/1000`
  (`zzMaw-Stats.lua:263-267, 296-298`)
- `skillEffectCap`: buff 50, dayBuff 75 (`zzMAW-Skills.lua:169-172`)
- `skillCap[50]` (Cover): 30 (`zzMAW-Skills.lua:162-167`)
- `armsmasterSkill`: Damage `{0,1,1,1.5,2}`, Speed `{0,0,1,1,1}`, Attack `{1,1,1,1,1}` (1-based, 5th unused)
  (`zzMAW-Skills.lua:149-153`)
- `skillAttack[Sword]`, `skillRecovery[Sword]`, `skillDamage[Sword]`: `{1,2,3,4}`, `{0,1,1,2}`, 2
  (`zzMAW-Skills.lua:45-83`)
- `skillItemAC[Chain]`, `skillItemRes[Chain]`: `{3,4,5,6}`, `{1,2,3,4}` (`zzMAW-Skills.lua:125-138`)
- `bodybuildingHP`: `{0.5,1,1.5,2}` (`zzMAW-Skills.lua:105`)
- `SPELL_HASTE_DIVISOR`, `GetSpeedBonusFromStat`: 20; `(s-13)/4` to 21, then `floor(s/10)`
  (`zzMAW-Skills.lua:408-417`)
- `buffPower`: live table: resistance buffs 20+2/skill, Haste 10+2, Shield 15+3, Stone Skin 20+2, Bless 20+2, Fate
  5+1, Heroism 15+3 (`Global/zzMaw_Mapping.lua:36-56`, see 5.1)
- `GetBuffStatPct(s, light)`: `min(10 + s/7, 20)/100` (light) (`zzMaw-Spells.lua:2665-2668`)
- `encStrUpNormal`, `encStrUpAusterity`: section 3.4 (`zzMaw-Items.lua:444-456`)
- `PRIMORDIAL_ENCHANT_MULT`, `LOOT_STRENGTH_MAX`, `TIER_LEVELS`: 1.25, 6, 15 (`zzMaw-Items.lua:465, 482, 889`)
- `GetLootStrength`, `GetLootTier`, `GetMaxEnchantStrength`: section 3.4 (`zzMaw-Items.lua:484-496`)
- `GetDifficultyExtraPower`: 1.2 insanity, 1.1 Doom, 1.05 true Nightmare, 1 (`zzMaw-Items.lua:552-561`)
- `GetPrimordialCharges`, `PRIMORDIAL_CHARGES_MULT`, `PRIMORDIAL_MIN_CHARGES`: `min(max(round(1.2 p), p + 4), 255)`
  (`zzMaw-Items.lua:498-529`)
- `rarityUpgradeChance`: Celestial 0.002, Legendary 0.03, Primordial 0.04, Ancient 0.12 (`zzMaw-Items.lua:585-590`)
- `rarityDifficultyMult`: 1, 1, 1, 1.1, 1.2, 1.4, 1.6, 1.8, 2 (`zzMaw-Items.lua:604-614`)
- `enchantChances`: Epic 5+0.75t (20), Rare 20+2t (60), Uncommon 60+t (80), Common 100 (`zzMaw-Items.lua:624-629`)
- `rarityBandMult`: [data/difficulty.yml](data/difficulty.yml) (`zzMaw-Items.lua:655-665`)
- `enchantStrengthRange`, `ENCHANT_STRENGTH_DEFAULT`, `ENCHANT_STRENGTH_DIV`: Celestial/Primordial 25-25, Ancient
  20-25, Legendary 16-20, others 8-20; /20 (`zzMaw-Items.lua:667-674`)
- `enchantCountByRarity`: 0, 1, 2, 3, 3, 3, 3, 3 (`zzMaw-Items.lua:676-685`)
- `GetRarityBaseMultiplier`, `GetRarityDistribution`, `GetExpectedEnchantFraction`: section 3.4
  (`zzMaw-Items.lua:757-877`)
- `enchantbonusdamage[46].Coeff`, `ENCHANT_DAMAGE_MULT`: 0.5, 1 (`zzMaw-Items.lua:2061-2063`)
- `LEGENDARY19_ENCHANT_MULT`: 1.5 (`zzMaw-Items.lua:2097`)
- `fireAuraDamage`: `{0.1,0.15,0.2,0.25}` (`zzMaw-Items.lua:4283`)
- `MawCore.ItemLevel`: `PerPower 5`, `POWER_CAP 100`, `POWER_HARD_CAP 255`, `Tiers 6`, `ExpectedTier 3.5`
  (`Modules/MawCore/ItemLevel.lua:5-24`)
- `Formulas`: `damageFloor 0.1`, `soloCoverDamageTaken 0.5`, armour `200 + L`, resistance `100 + L`,
  `speedDodgeShare 0.5`, `physicalVitalityShare 0.5`, `hitAtPar 0.75`, `hitMax 1`, Bless hit 0.05-0.10, spell scales,
  crit (`luck/min(500+5L,3000) + 0.05`, `stat/min(250+2.5L, 2000/3000) + 1.5`, spell `/4`), `enlightenmentManaPerSkill
  {0.5,1,1.5,2}`, `ringReductionDivisor 200`, `chargesArmorAC = ref x c/40` (`Modules/MawCore/Formulas.lua`)
- `getHealPersonalityBonus`, `ascendHealingValues`, `getBaseHealingSpells`, `oldTable`: healing only
  (`zzMaw-Spells.lua:80-82, 2063-2067, 2334-2353`; `zzMaw-Stats.lua:147-155`)
- `Party.Count`: Cover ratio 2 when solo (engine)
- `totalLevel`, `MawTierB`, `basetable`, `generateBoss`, `mapvars.bossData`: monster side (sections 6-7)
  (`zzMaw-Monsters.lua`)

---

## 5. Quirks and bugs found while running the model

### 5.1 Two `buffPower` tables

`zzMaw-Spells.lua:2670-2691` defines resistance buffs (Fire/Air/Water/Earth/Mind/Body Resistance) and Day of
Protection with **Base 10** ("halved base"), but `Global/zzMaw_Mapping.lua:25-57` replaces the whole table on every
AfterLoadMap with **Base 20** for those (other rows equal). Global scripts register after General ones, so the first
recalculation of a session runs on the halved table and every later one on the Mapping table. On a dimension map with
affix 33 the Mapping handler scales the current table instead, and that compounds on each reload inside the map. The
golden file uses the Mapping table (2.4: up to 1.25 % on vitality).

### 5.2 Cover worthless at GM

`COVER_GATE = {0, 1}` has no third or fourth entry, so `GetGradualMasteryValue` at GM ramps from `tbl[3] = nil → 0` to
`tbl[4] = nil → 0` (E:416, 426). Cover adds nothing to vitality once the estimated skill reaches GM (level 42 at
normal thresholds). The intent ("phases in across the expert band") was presumably `{0, 1, 1, 1}`.

### 5.3 Spell power reads Haste as "empower"

`getPlayerEstimatedSpellPower` (E:629) scales spell dice and flat damage by `buffMult(const.Spells.Haste)`; the Empower
Magic buff (spell 28, 15 % + 3/skill) is presumably meant. The same Haste factor is applied again to the delay.

### 5.4 Dead or constant terms

- `wDmg - wDice - wFlat` is always 0 (3.3): the `0.75 x` term in power and the `/2` term in attack contribute nothing.
- `masterLearned()` and `weaponTierFlat()` are not called by the model.
- The caches (`gearedCache`, `healthCache`, `manaCache`) key on difficulty and mode flags only, so a mid-session
  `buffPower` change (5.1) never invalidates them; health and mana do not read `buffPower`, so this is harmless today.

### 5.5 Shape of the curves

- Enchant strength caps at level 465 and the alchemy stat at 500, so `estimateStat` is almost flat from level 500
  (1085 → 1266 at 2000). From there power grows with skill (Ascension-like `1.5 s` weapon skill) and vitality with HP
  per level and Bodybuilding: power x15.5 and vitality x8.1 from level 500 to 2000.
- Below level 10 the model is dominated by the base stat 17 and the engine's stat table, which is why the int
  conversion assumption (2.1) only matters there.
- Higher mastery thresholds lower the expected character in Road to Insanity and Beyond Madness (power at level 10:
  33.2 MAW, 30.0 insanity), which partly offsets their larger hit tables at low levels.

---

## 6. Monster HP and damage

### 6.1 HP

- Template and live HP come from `getMonsterHealth` (3.13). Recalculated on BeforeLoadMap (when banks exist), LoadMap,
  AfterLoadMap, when the settings screen closes (action 113) and when `Map.Monsters.High` changes
  (`M:353-414`); live monsters keep their HP percentage (`MawSetMonsterHP(mon, hp, fraction)`).
- **Tier ratio** from the unmodified MONSTERS.txt (`basetable`, `M:157-197`): `FullHP(A)/FullHP(B)` and
  `FullHP(C)/FullHP(B)`, clamped to [0.6, 1.8] (E:700-708). This is why MAW's HP column changes still matter
  ([MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md) §2).
- **Templates** (`Game.MonstersTxt[i].HP`) are `min(round(HP), 32000)`, rounded to tens above 1000 (`M:619-628`).
  Rows are processed 1..651 in order, so an A row (i % 3 == 1) asks for `totalLevel[i + 1]` before this pass has
  set it and gets the previous map's B level; live monsters are corrected by `recalculateMawMonster` (`M:206-227`).
- **Real HP above 32000** lives in `mapvars.MawMonsterHP[index] = {max, hp, proxy}` (`Modules/MawCore/MonsterHP.lua`):
  the engine keeps a proxy pool for the health bar, AI and death check; the damage pipeline subtracts real damage from
  the ledger and converts it into proxy damage that keeps the bar percentage; death sends 32500.
- **Bosses**: `getMonsterHealth(mon) x bossData.HealthMult` (2.5-7.5, x1.5 Broodlord, x4 Omnipotent;
  [data/bosses.yml](data/bosses.yml)). The boss's own higher level is not used for HP.
- **Unique monsters** (NameId 1-219) also take HP and damage from their family's B level; their stored unique level
  (section 7.6) only affects the displayed level, AC/resistance maths, crit and hit chances.
- Dimension affix 15 ("+X % HP") multiplies the `HPtable` cache after the templates were written (`M:659-663`); live
  HP never reads that cache, so monster HP does not change. Only the leech reference does
  ([data/dimension_affixes.yml](data/dimension_affixes.yml)).

### 6.2 Damage

The pipeline stage `damage-recompute` (`Modules/MawCore/Damage.lua:1583-1800`) replaces the engine's damage:

1. dodge: GM Dodging `1 - 1/(1 + (skill + 10)/200)`, never for dragons; plus `MawRollDodge` for melee and missiles;
2. base = `getMonsterDamage(mon)` (3.13): Attack1 uses it as is; Attack2 uses it x `avg(Attack2 dice) / avg(Attack1
   dice)` with the Attack2 damage kind; spells (id < 100) use it x `monsterSpellMultiplierList[spell]` (`M:1937-1963`,
   [data/monster_scaling.yml](data/monster_scaling.yml));
3. dimension affix 14 changes the kind to Energy (on every hit, a MAW bug; see the affix file);
4. round, then x `(U{75..125} + U{75..125}) / 200` (triangular, mean 1);
5. x the lowest active debuff (Dark Grasp `DamageHalved` 0.7, Shrinking Ray 0.7, `Damage.lua:1575-1578`);
6. player mitigation `calcMawDamage(..., attacker level)` (COMBAT.md §1.3-1.4), solo Cover x0.5, disease x1.25/1.5/2
   (bonus halved solo), boss Exploding split, then the map affixes 1, 2 and 10 (`Damage.lua:1938-1956`).

Traps and environment damage use `getMonsterDamage(nil, getTotalLevel())` (/3 for spell type 15) x
`min((11 - 2 x Perception mastery) / 10, 1)`. Monster-vs-monster hits use `getMonsterDamage(attacker) / 3 /
2^(physical res / 100)` (`Damage.lua:233-241`).

---

## 7. Monster level resolution

All of this is `recalculateMonsterTable()` (`M:416-665`), run for all 651 rows on every map load. Notation as in
[data/monster_scaling.yml](data/monster_scaling.yml): `base` = the row's MONSTERS.txt level, `LB` = its family's B
level, `X` = the map band value assigned to a native family, `mean` = mean of the map's low/mid/high.

### 7.1 Shared inputs

- **Party bolster** = `getPartyLevel() - 4` (levels banked on the other continents,
  [data/exp_curve.yml](data/exp_curve.yml)), `^1.015` in Austerity, at least 0 (`M:418-422`).
- **Reset bonus** = `20 x vars.mapResetCount[map file]` (`M:425-427`), added to the party bolster.
- **Natives** (`M:448-475`): each MONSTERS row whose picture equals a MapStats `MonsterNPic` + `" B"`, gathered in
  monster-id order and sorted by base level (stable). With 3 families they take low/mid/high, with 2 low/high, with
  1 low. Every row of a native family uses its family's slot (`|i - native| <= 1`).
- **Extra bolster** (`M:480-519`): natives `X - LB`; other families halfway into the band, `(low - LB)/2` below it or
  `(high - LB)/2` above it, else 0.
- **Adjust**: natives `(mean - X) x 1.5` (x1 in Beyond Madness); 0 otherwise. Only the horizontal, arena and (via its
  own formula) madness rules use it.
- Maps named `"The Arena"` or `"Arena"` force extra bolster and party bolster to 0 (`M:521-524`).

### 7.2 Free progression (the bolster toggle on)

```
L = bolsteredLevel(partyBolster + resetBonus, base + extraBolster)            (M:529-531)
```

`bolsteredLevel(f, n)` (`M:5-13`) adds n **vanilla** levels' worth of experience (`500 t (t - 1)`) on top of MAW's
curve at f, so above level 100 a family gains fewer than n levels: 30 on top of 100 gives 126.8, 100 on top of 200 gives
249.4. With no banked levels, natives sit exactly at their band plus their tier offset (`X + base - LB`).

### 7.3 Horizontal progression (the toggle off)

Starter maps (`horizontalMaps`, `M:946-955`: out01, d05, 6d02, 7out01, 7d06, 7d28, 7d29, oute3, 6d01):

```
L = max(min((base + extra) x 2.5, bolsteredLevel(partyBolster + 2 x resetBonus, base + extra)), 1)
```

The party-bolster cap means a starter map never exceeds what free progression would give; the reset bonus is counted
twice in the cap (`M:542`, `bolsterLevel` already contains it).

All other maps (`M:546-555`):

```
L = max(2.5 base + 2.5 extra - 1.5 (base - LB) + adjust - 9 + resetBonus, 5)
natives:      L = X + 1.5 mean - 9 + (base - LB) + resetBonus
non-natives:  L = 2.5 LB + (base - LB) + 2.5 extra - 9 + resetBonus
```

So a map's monsters sit at about 2.5x the map's mean band minus 9, the low/mid/high spread is kept at 1x, and the A/C
offsets at 1x (the "flattener" `0.6 x 2.5`). The party's banks have no effect.

### 7.4 Beyond Madness

`freeProgression` is forced off. A map with an entry in `madnessMapLevels` that is not a madness starting map uses a
fixed level M ([data/map_levels.yml](data/map_levels.yml) `madness`; `500 (position / length)^1.2`, Breach 1100):

```
offset = 2 (Xslot - mean) + 2 (base - LB)           (Xslot = 0 for non-natives)          (M:560-573)
L      = max(offset >= 0 ? bolsteredLevel(M, offset) : 2M - bolsteredLevel(M, -offset), 5)
```

Non-natives therefore get `offset = -2 mean + ...` and land well below M. Other maps (no madness level, or the
starting maps out01, 7out01, 7d06, 7d28, oute3) use the horizontal rules of 7.3 with adjust x1 and the party bolster
from the banks.

### 7.5 Special maps and states

- **Dimension maps** (`mapvars.mapAffixes`): `L = base + extra + Power x 10 + 20`; no party bolster, no horizontal or
  madness rule (`M:439-443`). Shown level: `Power x 10 + 20 + round(mean)`.
- **Arena d42**: `L = max(6 base - 4.8 (base - LB) + 2 adjust, 5)`, plus `600 + 3.5 x ((highestArenaWave + 1) x 3 -
  #monTbl)` once the wave counter passes the end of the C-tier family list (`M:577-589`). Arena waves pick family
  `monTbl[(level x 3 - 2 + k) % #monTbl]` ([COMBAT.md](COMBAT.md) §6.7).
- **Bounty maps**: `L = base + mawBounty` for every monster on the map, `mawBounty = max(getPartyLevel(4) - LB(target)
  / 1.5, 0)` (`M:591-593`, `BountyHunt.lua:214`). The map variable is never cleared, so the whole town keeps that level.
- **Resets**: +20 per reset of that dungeon (7.1); not available in Road to Insanity and Beyond Madness.
- **Final**: `round(max(L, 1))`; the engine field is capped at 255, the real value stays in `totalLevel[id]`
  (`getMonsterLevel`, `M:1884-1895`).
- **Side effect**: the global `bolsterLevel` is overwritten inside the loop on horizontal non-starter maps and in the
  arena (`M:550, 579`); chest gold (`zzMaw-Items.lua:907-922`) later reads that clobbered value. Monster loot reads
  the saved copy `bolsterLevel2`.

### 7.6 Bosses and unique monsters

- **Bosses**: `MawBossLevel` (`M:31-40`): a C row gets `C + (C - B)`, a B row (affix 19) the C level, an A row the
  B level. HP and damage still come from the family B level (6.1).
- **Unique monsters** (`M:229-311`, stored once per map in `mapvars.oldUniqueMonsterTable`):
  - free progression and horizontal starter maps: `bolsteredLevel(getPartyLevel(), old)` (no -4);
  - horizontal other maps: `2.5 x old`;
  - Beyond Madness on a fixed-level map: `M + 2 (high - mid)`; elsewhere `3 x old`.
  - The level is recomputed from the stored original on every recalculation (`mapvars.boosted` is never set).

### 7.7 Worked example: Ravenshore (`out02.odm`, band 14/14/17)

Natives (MapStats pictures): Dire Wolf (B level 14), Centaur (14), Human Mercenary (17), mean 15. Levels from the
formulas above (Python port of `bolsteredLevel`, checked against the Lua values):

| Row | base | Free, no banks | Free, 100 banked (bolster 96) | Horizontal | Horizontal, 1 reset |
|---|---|---|---|---|---|
| 85 Dire Wolf Yearling (A) | 9 | 9 | 105 | 23 | 43 |
| 86 Dire Wolf (B) | 14 | 14 | 110 | 28 | 48 |
| 87 Pack Leader (C) | 19 | 19 | 114 | 33 | 53 |
| 100 Centaur (A) | 11 | 11 | 107 | 25 | 45 |
| 101 Centaur Warrior (B) | 14 | 14 | 110 | 28 | 48 |
| 102 Centaur Warlord (C) | 18 | 18 | 113 | 32 | 52 |
| 193 Soldier of Fortune (A) | 10 | 10 | 106 | 24 | 44 |
| 194 Mercenary (B) | 17 | 17 | 112 | 31 | 51 |
| 195 Mercenary Captain (C) | 24 | 24 | 118 | 38 | 58 |

Beyond Madness, Shadow Guild Hideout (`6d03.blv`, position 7 of 54, M = 43, band 11/15/15): Thief 31, Burglar 39,
Rogue 51, Thug 35, Ruffian 47, Brigand 59.

The B rows' levels are the levels to look up in the golden tables (section 9): a Ravenshore Dire Wolf on MAW
difficulty in horizontal progression has the HP and damage of row 28.

---

## 8. Other monster numbers

Full rules with line numbers: [data/monster_scaling.yml](data/monster_scaling.yml). In short:

- **AC** = `base AC x (L + 10) / (LB + 10)` (`M:616`).
- **Resistances** = `min(base + affix12, 200 + affix12, 999)`; `Imm` (200) is the cap, nothing is immune; player
  damage is divided by `2^(res/100)`.
- **Experience** = `round((lb x 20 + lb^1.8) x L / lb) x GetMonsterExpMult()`, `lb = min(max(base, L/3), 100)`; the
  award per member scales with monster HP over the expected HP at the member's level
  ([data/exp_curve.yml](data/exp_curve.yml)).
- **Speed**: fast melee monsters `v/2 + 300`; summoned adds 350.
- **Extra ranged attack** outdoors at bolster ≥ 200 or on bounty maps (A/B/C 10/20/30 %).
- **AI** forced aggressive, steal bonus 20 → 17, diseases below level 20 → poisons, Doom on-hit conditions
  ([data/difficulty.yml](data/difficulty.yml)).
- **Treasure**: gold `(bolster + LB) x 7.5` (x0.5 A, x2 C), item % `ceil(sqrt(L) x (1 + tier) x 0.5 + min(%, 50) x
  0.3)`, item level from `(max(LB, map low) + 10 tier) / 20`.
- **Bosses**: [data/bosses.yml](data/bosses.yml). **Density**: [data/difficulty.yml](data/difficulty.yml).

---

## 9. Golden output

Source: [data/balance_golden.csv](data/balance_golden.csv) (2.2-2.3). All tables below: party of 5, no Austerity,
`d1`..`d9` = difficulty index (d1 Easy/Normal, d2 unreachable, d3 MAW, d4 Hard, d5 Hell, d6 Nightmare, d7 Doom,
d8 Road to Insanity, d9 Beyond Madness).

### 9.1 The expected character at MAW difficulty (d3)

Columns: estimated skill, mastery, stat, `gearedFraction`, max enchant strength, health, AC, resistance, physical
and magic damage share taken, chance to be hit, vitality, power, attack.

```
level, skill,  m,   stat,  gear, maxEn,  health,     AC,    res,  phys, magic,   hit, vitality,    power,attack
    1,     1,  1,   21.5, 0.115,  3.59,    54.2,   15.1,   4.15, 0.932, 0.947, 0.919,     62.8,     13.7,  5.31
    2,  1.56,  1,   21.7, 0.108,  3.89,    59.7,   14.5,   4.22, 0.936, 0.949, 0.918,     69.0,     15.0,  6.98
    5,   2.7,  1,   22.9,   0.1,  4.77,    75.6,   14.1,   4.35, 0.942, 0.951, 0.915,     87.3,     20.0,  12.4
   10,  4.04,  2,   27.2, 0.127,  6.23,     106,   19.4,   6.05, 0.931, 0.942, 0.903,      125,     33.2,  26.6
   15,  5.21,  2,   33.6, 0.154,   7.7,     149,   35.3,   18.1, 0.892, 0.844, 0.888,      196,     54.0,  49.1
   20,  6.21,  2,   40.8, 0.177,  9.17,     199,   51.2,   31.4, 0.862, 0.767, 0.873,      291,     78.9,  74.8
   30,  8.07,  3,   55.9, 0.219,  12.1,     326,   74.8,   49.0, 0.836, 0.704, 0.848,      539,      140,   115
   40,  9.79,  3,   71.6, 0.254,  15.0,     492,   92.6,   60.8, 0.826, 0.691, 0.827,      863,      211,   142
   50,  11.4,  4,   88.9, 0.284,  18.0,     662,    112,   74.0, 0.818, 0.677,  0.81,     1094,      276,   163
   60,  13.0,  4,    107, 0.311,  20.9,     854,    132,   89.8, 0.809, 0.662, 0.794,     1462,      357,   184
   70,  14.6,  4,    127, 0.335,  23.8,    1077,    154,    106, 0.801, 0.647, 0.781,     1903,      452,   205
   80,  16.1,  4,    145, 0.357,  26.0,    1322,    175,    121, 0.795, 0.637, 0.772,     2392,      554,   226
   90,  17.6,  4,    159, 0.376,  27.5,    1586,    197,    136,  0.79, 0.628, 0.765,     2924,      664,   246
  100,  19.1,  4,    178, 0.394,  29.7,    1896,    219,    153, 0.785, 0.617, 0.758,     3569,      799,   267
  150,  26.4,  4,    279, 0.473,  40.7,    4070,    366,    253,  0.75, 0.558, 0.731,     8844,     1930,   380
  200,  33.7,  4,    395, 0.538,  51.7,    7598,    553,    380, 0.717, 0.501, 0.715,    18860,     4141,   499
  250,  40.9,  4,    513, 0.581,  62.7,   11511,    771,    527, 0.688, 0.448, 0.705,    32294,     8035,   623
  300,  48.0,  4,    635, 0.613,  73.7,   16136,   1021,    695, 0.662, 0.401, 0.698,    50878,    14500,   749
  400,  62.2,  4,    890,  0.66,  95.7,   28865,   1595,   1066,  0.62, 0.338,  0.69,   111169,    38333,   987
  500,  76.4,  4,   1085, 0.694,   110,   44376,   2249,   1490, 0.587, 0.308, 0.686,   186940,    69395,  1197
  600,  90.6,  4,   1118, 0.718,   110,   56646,   2653,   1772, 0.589, 0.309, 0.685,   238278,    90610,  1353
  800,   119,  4,   1165, 0.753,   110,   84939,   3458,   2336, 0.591, 0.309, 0.685,   356575,   148010,  1662
 1000,   147,  4,   1196, 0.776,   110,  118276,   4261,   2900, 0.593, 0.309, 0.684,   495857,   229389,  1966
 1500,   218,  4,   1242, 0.809,   110,  223821,   6265,   4312, 0.595,  0.31, 0.684,   936509,   549178,  2720
 2000,   289,  4,   1266, 0.827,   110,  361190,   8266,   5726, 0.596,  0.31, 0.683,  1509680,  1076550,  3470
```

### 9.2 Difficulty relative to MAW

Monster HP / damage of each index divided by the MAW value at the same level (from the CSV). The hit tables alone
would give 0.5/0.5, 0.75/0.7, 1.25/1.08, 1.5/1.17, 1.75/1.27, 2/1.4, 2.25/1.56, 2.5/1.75.

| Level | d1 | d2 | d4 | d5 | d6 | d7 | d8 | d9 |
|---|---|---|---|---|---|---|---|---|
| 20 | 0.50/0.50 | 0.75/0.70 | 1.26/1.10 | 1.51/1.21 | 1.81/1.37 | 2.15/1.58 | 1.45/1.35 | 1.57/1.50 |
| 50 | 0.50/0.50 | 0.75/0.70 | 1.28/1.11 | 1.56/1.22 | 1.88/1.39 | 2.25/1.62 | 1.62/1.40 | 1.35/1.26 |
| 100 | 0.50/0.50 | 0.75/0.70 | 1.29/1.11 | 1.58/1.23 | 1.93/1.41 | 2.39/1.68 | 2.54/2.22 | 2.10/1.65 |
| 300 | 0.50/0.50 | 0.75/0.70 | 1.32/1.13 | 1.63/1.26 | 2.12/1.50 | 2.74/1.83 | 3.62/2.32 | 4.14/2.50 |
| 1000 | 0.50/0.50 | 0.75/0.70 | 1.31/1.13 | 1.62/1.26 | 2.09/1.50 | 2.64/1.80 | 3.43/2.25 | 3.54/2.57 |

Indices 1-3 share the same expected character, so their ratios equal the hit ratios. From index 4 the character is
better geared (more loot seen, `DROPS_DENSITY_BY_DIFFICULTY`, rarity multipliers, `GetDifficultyExtraPower`), which
raises both monster HP and damage. Road to Insanity and Beyond Madness have higher mastery thresholds, which lowers the
expected character at low and middle levels.

### 9.3 Austerity

Monster HP and damage (B tier) for indices 1-6 with `AusterityMode` (austerity hit tables and enchant curve):

Austerity monster HP, indices 1-6:

```
level,       a1,       a2,       a3,       a4,       a5,       a6
    1,     13.7,     27.5,     54.9,     68.7,     82.6,     96.5
   10,     33.1,     66.1,      132,      166,      199,      233
   20,     75.7,      151,      303,      380,      457,      535
   50,      247,      494,      988,     1254,     1510,     1806
  100,      653,     1306,     2612,     3324,     4009,     4828
  200,     2730,     5459,    10918,    13930,    16889,    20571
  300,     8119,    16238,    32476,    41477,    50548,    61927
  500,    37950,    75899,   151798,   196341,   240129,   299631
 1000,   275706,   551413,  1102830,  1459930,  1807830,  2362120
 2000,  4532150,  9064300, 18128600, 24812400, 31224600, 43478300
```

Austerity monster damage, indices 1-6:

```
level,       a1,       a2,       a3,       a4,       a5,       a6
    1,      4.2,      6.3,     12.5,     15.9,     21.5,     26.2
   10,      8.1,     12.1,     24.2,     30.8,     41.6,     51.0
   20,     18.2,     27.3,     54.6,     69.5,     93.8,      115
   50,     63.4,     95.1,      190,      242,      327,      404
  100,      191,      287,      573,      732,      989,     1232
  200,      857,     1286,     2571,     3293,     4459,     5604
  300,     2013,     3019,     6039,     7769,    10546,    13341
  500,     7160,    10740,    21480,    27941,    38145,    49155
 1000,    38590,    57885,   115771,   152580,   209517,   276934
 2000,   257630,   386445,   772889,  1021080,  1401800,  1859450
```

### 9.4 Solo

Monster damage solo divided by monster damage with a party of 5 (HP is unchanged). The only difference is the Cover
term: a solo character counts `1/0.5 = 2` as the tank ratio, a party `1 + 6 L / (L + 240)`, and only while Cover's
gate is open (5.2).

```
level,     d1,     d2,     d3,     d4,     d5,     d6,     d7,     d8,     d9
   10,  1.001,  1.001,  1.001,  1.001,  1.001,  1.001,  1.001,  1.000,  1.000
   20,  1.023,  1.023,  1.023,  1.023,  1.023,  1.023,  1.023,  1.000,  1.000
   30,  1.020,  1.020,  1.020,  1.020,  1.020,  1.020,  1.020,  1.000,  1.000
   40,  1.008,  1.008,  1.008,  1.008,  1.008,  1.008,  1.008,  1.002,  1.000
   50,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  0.999,  1.000
  100,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  0.953,  0.971
  150,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  0.912
  200,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  0.884
  300,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000,  1.000
```

### 9.5 Per-difficulty tables, levels 1-2000

Values below 100 with one decimal, the rest rounded. `power` and `vitality` are the expected character at that level;
`monster_hp_b` = `power x hitToKillMonster`, `monster_dmg_b` = `vitality / hitToKill` (B tier, no boss).

#### Expected player power (damage per swing-equivalent), getPlayerEstimatedPower

```
level,       d1,       d2,       d3,       d4,       d5,       d6,       d7,       d8,       d9
    1,     13.7,     13.7,     13.7,     13.8,     13.8,     13.8,     13.8,     13.8,     14.7
    2,     15.0,     15.0,     15.0,     15.0,     15.0,     15.1,     15.1,     16.0,     16.0
    3,     16.1,     16.1,     16.1,     16.1,     16.1,     16.1,     16.2,     17.1,     17.1
    4,     17.1,     17.1,     17.1,     17.1,     17.1,     17.2,     18.2,     18.1,     18.2
    5,     20.0,     20.0,     20.0,     20.1,     20.1,     21.1,     21.2,     21.0,     22.2
    6,     21.8,     21.8,     21.8,     21.8,     22.8,     22.9,     23.0,     23.2,     23.2
    7,     23.6,     23.6,     23.6,     24.7,     24.7,     24.8,     24.9,     24.1,     24.1
    8,     26.5,     26.5,     26.5,     26.6,     26.6,     26.7,     28.1,     25.1,     25.1
    9,     28.5,     28.5,     28.5,     28.6,     28.7,     28.8,     30.2,     26.0,     27.0
   10,     33.2,     33.2,     33.2,     33.3,     33.4,     34.9,     35.1,     30.0,     30.0
   11,     36.7,     36.7,     36.7,     36.8,     38.3,     38.4,     38.6,     31.0,     31.0
   12,     40.3,     40.3,     40.3,     41.9,     42.0,     42.2,     43.6,     32.0,     33.4
   13,     45.2,     45.2,     45.2,     45.4,     45.5,     46.9,     47.2,     34.3,     34.4
   14,     48.3,     48.3,     48.3,     48.4,     48.5,     50.0,     50.4,     35.3,     35.4
   15,     54.0,     54.0,     54.0,     55.5,     55.6,     55.9,     58.1,     38.5,     39.5
   16,     57.3,     57.3,     57.3,     58.9,     59.0,     61.2,     61.7,     40.7,     40.6
   17,     62.1,     62.1,     62.1,     62.4,     62.5,     64.8,     66.8,     42.2,     41.6
   18,     65.7,     65.7,     65.7,     66.0,     68.1,     68.5,     70.6,     43.7,     44.1
   19,     69.3,     69.3,     69.3,     71.7,     71.9,     73.9,     74.6,     46.8,     45.1
   20,     78.9,     78.9,     78.9,     79.2,     79.5,     81.6,     84.6,     50.9,     49.6
   21,     83.5,     83.5,     83.5,     83.9,     85.8,     86.4,     89.6,     52.7,     50.7
   22,     88.2,     88.2,     88.2,     90.3,     90.6,     93.7,     96.4,     55.7,     51.9
   23,     95.2,     95.2,     95.2,     95.7,     96.0,     99.3,      102,     57.6,     54.9
   24,      101,      101,      101,      101,      104,      105,      108,     59.6,     56.4
   25,      109,      109,      109,      112,      112,      115,      119,     65.8,     61.6
   26,      115,      115,      115,      116,      117,      119,      124,     67.9,     63.2
   27,      120,      120,      120,      121,      123,      124,      130,     71.3,     64.8
   28,      124,      124,      124,      127,      127,      132,      135,     73.5,     68.2
   29,      129,      129,      129,      132,      132,      136,      140,     75.8,     70.0
   30,      140,      140,      140,      141,      144,      146,      153,     83.1,     75.6
   31,      146,      146,      146,      150,      151,      154,      160,     86.3,     77.6
   32,      152,      152,      152,      156,      157,      160,      166,     90.9,     79.5
   33,      160,      160,      160,      161,      164,      169,      174,     93.7,     82.9
   34,      165,      165,      165,      169,      169,      175,      180,     98.8,     84.4
   35,      176,      176,      176,      180,      180,      186,      195,      105,     90.0
   36,      184,      184,      184,      185,      189,      194,      201,      109,     91.6
   37,      190,      190,      190,      194,      195,      200,      210,      113,     95.3
   38,      194,      194,      194,      199,      200,      205,      214,      118,     97.0
   39,      197,      197,      197,      202,      206,      212,      218,      122,      100
   40,      211,      211,      211,      215,      216,      223,      233,      131,      105
   41,      215,      215,      215,      219,      220,      229,      238,      136,      109
   42,      219,      219,      219,      223,      228,      234,      245,      143,      111
   43,      226,      226,      226,      231,      232,      238,      250,      148,      115
   44,      230,      230,      230,      236,      237,      247,      258,      154,      118
   45,      244,      244,      244,      246,      250,      258,      270,      164,      126
   46,      249,      249,      249,      253,      255,      265,      275,      171,      129
   47,      253,      253,      253,      258,      263,      270,      283,      175,      133
   48,      260,      260,      260,      262,      268,      275,      288,      181,      136
   49,      264,      264,      264,      271,      272,      284,      297,      185,      141
   50,      276,      276,      276,      283,      287,      296,      310,      198,      149
   51,      285,      285,      285,      288,      292,      304,      319,      203,      154
   52,      290,      290,      290,      295,      297,      309,      324,      210,      160
   53,      295,      295,      295,      300,      307,      315,      335,      219,      164
   54,      303,      303,      303,      310,      312,      325,      341,      224,      170
   55,      315,      315,      315,      323,      327,      338,      358,      238,      178
   56,      320,      320,      320,      328,      333,      347,      364,      244,      185
   57,      330,      330,      330,      336,      338,      352,      375,      253,      190
   58,      335,      335,      335,      341,      348,      363,      381,      262,      196
   59,      343,      343,      343,      352,      354,      369,      390,      268,      203
   60,      357,      357,      357,      365,      371,      386,      406,      285,      213
   61,      363,      363,      363,      371,      377,      393,      418,      292,      220
   62,      373,      373,      373,      381,      383,      399,      425,      302,      225
   63,      379,      379,      379,      387,      394,      411,      435,      313,      234
   64,      388,      388,      388,      398,      401,      418,      443,      321,      242
   65,      403,      403,      403,      413,      419,      437,      465,      339,      253
   66,      409,      409,      409,      419,      425,      444,      472,      352,      263
   67,      420,      420,      420,      428,      437,      456,      483,      360,      268
   68,      427,      427,      427,      435,      444,      463,      490,      371,      277
   69,      436,      436,      436,      447,      450,      473,      504,      385,      287
   70,      452,      452,      452,      463,      469,      490,      522,      403,      300
   71,      458,      458,      458,      473,      477,      503,      534,      416,      309
   72,      471,      471,      471,      480,      489,      511,      542,      431,      321
   73,      478,      478,      478,      487,      497,      522,      557,      442,      328
   74,      488,      488,      488,      500,      507,      530,      569,      455,      338
   75,      505,      505,      505,      517,      525,      554,      588,      482,      357
   76,      511,      511,      511,      527,      531,      561,      596,      492,      365
   77,      523,      523,      523,      534,      544,      568,      610,      506,      372
   78,      530,      530,      530,      540,      551,      579,      618,      516,      382
   79,      537,      537,      537,      547,      558,      587,      630,      534,      390
   80,      554,      554,      554,      571,      579,      605,      649,      554,      410
   81,      565,      565,      565,      578,      587,      620,      658,      566,      417
   82,      572,      572,      572,      586,      594,      628,      674,      574,      427
   83,      579,      579,      579,      597,      608,      636,      682,      590,      434
   84,      593,      593,      593,      604,      616,      648,      695,      599,      446
   85,      611,      611,      611,      623,      635,      667,      716,      624,      462
   86,      618,      618,      618,      637,      646,      675,      725,      635,      472
   87,      626,      626,      626,      644,      654,      691,      741,      646,      480
   88,      637,      637,      637,      652,      662,      699,      750,      664,      493
   89,      644,      644,      644,      664,      670,      707,      759,      675,      501
   90,      664,      664,      664,      684,      697,      732,      786,      703,      522
   91,      679,      679,      679,      692,      706,      742,      796,      716,      531
   92,      688,      688,      688,      708,      719,      759,      814,      736,      546
   93,      696,      696,      696,      717,      728,      769,      825,      750,      556
   94,      709,      709,      709,      726,      737,      783,      840,      768,      568
   95,      730,      730,      730,      752,      766,      806,      865,      794,      595
   96,      746,      746,      746,      761,      776,      816,      884,      817,      605
   97,      755,      755,      755,      777,      789,      834,      895,      835,      618
   98,      764,      764,      764,      787,      799,      844,      911,      850,      636
   99,      777,      777,      777,      796,      808,      859,      922,      873,      646
  100,      799,      799,      799,      823,      839,      883,      957,      903,      672
  110,      967,      967,      967,      996,     1016,     1080,     1166,     1177,      869
  120,     1161,     1161,     1161,     1196,     1220,     1299,     1416,     1521,     1128
  130,     1383,     1383,     1383,     1426,     1461,     1557,     1699,     1913,     1449
  140,     1638,     1638,     1638,     1690,     1731,     1860,     2039,     2301,     1793
  150,     1930,     1930,     1930,     2005,     2054,     2202,     2425,     2750,     2204
  160,     2276,     2276,     2276,     2357,     2408,     2602,     2875,     3266,     2735
  170,     2654,     2654,     2654,     2750,     2818,     3067,     3391,     3868,     3351
  180,     3090,     3090,     3090,     3214,     3294,     3576,     3979,     4544,     4095
  190,     3594,     3594,     3594,     3728,     3821,     4165,     4647,     5341,     4969
  200,     4141,     4141,     4141,     4320,     4429,     4843,     5403,     6216,     6035
  210,     4766,     4766,     4766,     4974,     5126,     5608,     6256,     7217,     7251
  220,     5467,     5467,     5467,     5708,     5855,     6424,     7203,     8351,     8490
  230,     6233,     6233,     6233,     6510,     6680,     7368,     8263,     9582,     9864
  240,     7071,     7071,     7071,     7422,     7631,     8407,     9447,    10977,    11280
  250,     8035,     8035,     8035,     8414,     8676,     9580,    10767,    12564,    12879
  260,     9080,     9080,     9080,     9536,     9810,    10839,    12233,    14276,    14693
  270,    10261,    10261,    10261,    10753,    11092,    12280,    13860,    16200,    16673
  280,    11537,    11537,    11537,    12124,    12478,    13876,    15661,    18374,    18841
  290,    12924,    12924,    12924,    13606,    14038,    15617,    17651,    20735,    21313
  300,    14500,    14500,    14500,    15269,    15778,    17559,    19846,    23312,    23993
  310,    16196,    16196,    16196,    17060,    17631,    19697,    22289,    26237,    27004
  320,    18010,    18010,    18010,    18999,    19613,    21944,    24830,    29259,    30116
  330,    19881,    19881,    19881,    21024,    21731,    24319,    27515,    32523,    33478
  340,    21954,    21954,    21954,    23171,    23953,    26814,    30432,    36003,    37063
  350,    24224,    24224,    24224,    25573,    26438,    29603,    33694,    39854,    41032
  360,    26600,    26600,    26600,    28144,    29099,    32624,    37125,    43948,    45245
  370,    29220,    29220,    29220,    30861,    32005,    35890,    40872,    48467,    49879
  380,    31984,    31984,    31984,    33887,    35043,    39417,    44880,    53259,    54791
  390,    35025,    35025,    35025,    37115,    38420,    43222,    49334,    58533,    60249
  400,    38333,    38333,    38333,    40627,    42057,    47321,    53999,    64278,    66084
  410,    41779,    41779,    41779,    44287,    45931,    51732,    59067,    70295,    72249
  420,    45558,    45558,    45558,    48340,    50135,    56618,    64465,    76893,    79008
  430,    48676,    48676,    48676,    51746,    53710,    60658,    69221,    82409,    84854
  440,    52083,    52083,    52083,    55372,    57331,    64912,    74058,    88359,    90806
  450,    55624,    55624,    55624,    59044,    61283,    69388,    79202,    94695,    97222
  460,    59191,    59191,    59191,    62985,    65372,    74014,    84650,   101015,   103684
  470,    62261,    62261,    62261,    66184,    68673,    77744,    88617,   105854,   108610
  480,    64615,    64615,    64615,    68530,    71076,    80349,    91632,   109148,   112005
  490,    66922,    66922,    66922,    71094,    73702,    83145,    94657,   112588,   115405
  500,    69395,    69395,    69395,    73674,    76344,    86062,    97602,   115860,   118705
  510,    71335,    71335,    71335,    75708,    78431,    88292,   100245,   118854,   121733
  520,    73424,    73424,    73424,    77897,    80504,    90614,   102778,   121647,   124628
  530,    75434,    75434,    75434,    79954,    82790,    93114,   105290,   124556,   127493
  540,    77432,    77432,    77432,    82096,    84986,    95514,   108062,   127692,   130665
  550,    79632,    79632,    79632,    84400,    87350,    97896,   110719,   130620,   133698
  560,    81749,    81749,    81749,    86566,    89571,   100522,   113581,   133666,   136702
  570,    83854,    83854,    83854,    88818,    91880,   103041,   116260,   136950,   140022
  580,    86169,    86169,    86169,    91241,    94364,   105543,   119045,   140016,   143197
  590,    88396,    88396,    88396,    93518,    96698,   108296,   121808,   143204,   146343
  600,    90610,    90610,    90610,    95885,    99123,   110939,   124852,   146639,   149817
  700,   115524,   115524,   115524,   121903,   125766,   139911,   156094,   181785,   185342
  800,   148010,   148010,   148010,   155927,   160701,   178303,   198239,   230059,   226047
  900,   185864,   185864,   185864,   195664,   201177,   222711,   247171,   286017,   272215
 1000,   229389,   229389,   229389,   241243,   248131,   274151,   303190,   349894,   324806
 1100,   279118,   279118,   279118,   293279,   301451,   332499,   366965,   422755,   383504
 1200,   335544,   335544,   335544,   352283,   361885,   398568,   439106,   504863,   457567
 1300,   399093,   399093,   399093,   418700,   429886,   472846,   520033,   597145,   540087
 1400,   470194,   470194,   470194,   492877,   505904,   555263,   609876,   699394,   632552
 1500,   549178,   549178,   549178,   575443,   589827,   647369,   710221,   813519,   735215
 1600,   636082,   636082,   636082,   666148,   683072,   749028,   820908,   939337,   847742
 1700,   732238,   732238,   732238,   766474,   785118,   860227,   941923,  1076830,   971952
 1800,   837071,   837071,   837071,   875820,   897479,   982609,  1074190,  1227030,  1106940
 1900,   952098,   952098,   952098,   995765,  1019430,  1115250,  1219280,  1391740,  1254120
 2000,  1076550,  1076550,  1076550,  1125380,  1151850,  1259510,  1376080,  1569670,  1414740
```

#### Expected player vitality (effective HP), getPlayerEstimatedVitality

```
level,       d1,       d2,       d3,       d4,       d5,       d6,       d7,       d8,       d9
    1,     62.8,     62.8,     62.8,     64.0,     64.8,     66.0,     67.1,     68.9,     70.3
    2,     69.0,     69.0,     69.0,     70.2,     71.1,     72.4,     73.5,     75.9,     77.4
    3,     75.1,     75.1,     75.1,     76.4,     77.3,     78.6,     80.4,     83.8,     85.3
    4,     81.1,     81.1,     81.1,     82.5,     83.5,     84.9,     88.4,     91.7,     93.2
    5,     87.3,     87.3,     87.3,     88.9,     90.0,     92.5,     96.2,     99.9,      102
    6,     93.9,     93.9,     93.9,     96.1,     97.6,      100,      104,      108,      110
    7,      101,      101,      101,      104,      105,      108,      112,      117,      118
    8,      109,      109,      109,      111,      113,      116,      121,      125,      126
    9,      116,      116,      116,      119,      121,      124,      129,      134,      135
   10,      125,      125,      125,      128,      130,      134,      139,      144,      144
   11,      138,      138,      138,      141,      143,      147,      153,      153,      154
   12,      151,      151,      151,      155,      157,      162,      169,      163,      163
   13,      165,      165,      165,      169,      172,      177,      185,      173,      173
   14,      180,      180,      180,      185,      187,      193,      202,      184,      183
   15,      196,      196,      196,      201,      204,      211,      220,      194,      194
   16,      213,      213,      213,      218,      222,      229,      239,      206,      204
   17,      231,      231,      231,      236,      240,      248,      259,      217,      215
   18,      249,      249,      249,      255,      259,      268,      280,      228,      226
   19,      269,      269,      269,      276,      280,      289,      302,      240,      237
   20,      291,      291,      291,      299,      303,      313,      328,      253,      249
   21,      315,      315,      315,      322,      328,      339,      355,      266,      261
   22,      339,      339,      339,      348,      353,      366,      383,      279,      273
   23,      366,      366,      366,      375,      380,      394,      413,      292,      286
   24,      393,      393,      393,      403,      409,      424,      444,      306,      298
   25,      415,      415,      415,      426,      433,      448,      471,      320,      312
   26,      438,      438,      438,      449,      456,      473,      497,      335,      325
   27,      462,      462,      462,      473,      481,      498,      524,      350,      339
   28,      486,      486,      486,      498,      506,      525,      551,      364,      353
   29,      511,      511,      511,      524,      532,      552,      580,      380,      367
   30,      539,      539,      539,      552,      561,      582,      612,      398,      383
   31,      566,      566,      566,      581,      590,      612,      644,      418,      398
   32,      595,      595,      595,      610,      620,      644,      677,      440,      413
   33,      625,      625,      625,      641,      651,      676,      712,      462,      429
   34,      656,      656,      656,      672,      683,      709,      747,      485,      444
   35,      688,      688,      688,      705,      717,      745,      785,      509,      462
   36,      721,      721,      721,      739,      751,      780,      822,      533,      478
   37,      754,      754,      754,      773,      786,      817,      861,      558,      495
   38,      788,      788,      788,      808,      821,      854,      900,      584,      513
   39,      823,      823,      823,      845,      859,      893,      941,      611,      530
   40,      863,      863,      863,      885,      900,      936,      987,      640,      549
   41,      902,      902,      902,      925,      940,      979,     1033,      670,      568
   42,      847,      847,      847,      869,      884,      920,      971,      701,      589
   43,      876,      876,      876,      899,      914,      951,     1005,      732,      612
   44,      905,      905,      905,      929,      944,      983,     1039,      765,      635
   45,      936,      936,      936,      960,      976,     1017,     1076,      799,      660
   46,      966,      966,      966,      991,     1008,     1051,     1111,      834,      684
   47,      997,      997,      997,     1023,     1040,     1084,     1148,      870,      709
   48,     1028,     1028,     1028,     1054,     1072,     1118,     1184,      907,      734
   49,     1060,     1060,     1060,     1087,     1105,     1154,     1222,      945,      760
   50,     1094,     1094,     1094,     1123,     1142,     1192,     1263,      987,      788
   51,     1128,     1128,     1128,     1157,     1177,     1229,     1304,     1029,      817
   52,     1162,     1162,     1162,     1193,     1213,     1267,     1344,     1072,      845
   53,     1197,     1197,     1197,     1228,     1250,     1305,     1386,     1118,      875
   54,     1232,     1232,     1232,     1265,     1286,     1345,     1428,     1164,      905
   55,     1270,     1270,     1270,     1304,     1327,     1387,     1474,     1213,      937
   56,     1306,     1306,     1306,     1341,     1365,     1428,     1518,     1262,      969
   57,     1344,     1344,     1344,     1380,     1403,     1469,     1563,     1313,     1001
   58,     1382,     1382,     1382,     1419,     1444,     1511,     1608,     1366,     1034
   59,     1420,     1420,     1420,     1459,     1484,     1554,     1655,     1420,     1068
   60,     1462,     1462,     1462,     1502,     1528,     1602,     1705,     1480,     1105
   61,     1503,     1503,     1503,     1544,     1571,     1646,     1755,     1539,     1142
   62,     1544,     1544,     1544,     1587,     1614,     1692,     1804,     1601,     1179
   63,     1586,     1586,     1586,     1630,     1659,     1740,     1856,     1665,     1217
   64,     1629,     1629,     1629,     1674,     1703,     1787,     1907,     1730,     1256
   65,     1675,     1675,     1675,     1721,     1752,     1839,     1964,     1801,     1298
   66,     1719,     1719,     1719,     1766,     1798,     1888,     2017,     1871,     1339
   67,     1763,     1763,     1763,     1812,     1845,     1938,     2071,     1943,     1380
   68,     1808,     1808,     1808,     1858,     1892,     1988,     2125,     2017,     1424
   69,     1854,     1854,     1854,     1905,     1939,     2039,     2181,     2094,     1468
   70,     1903,     1903,     1903,     1957,     1993,     2095,     2242,     2179,     1515
   71,     1951,     1951,     1951,     2007,     2043,     2149,     2300,     2264,     1563
   72,     2000,     2000,     2000,     2056,     2094,     2203,     2359,     2351,     1611
   73,     2049,     2049,     2049,     2107,     2146,     2259,     2420,     2441,     1660
   74,     2100,     2100,     2100,     2159,     2199,     2315,     2481,     2534,     1711
   75,     2153,     2153,     2153,     2215,     2256,     2377,     2548,     2635,     1766
   76,     2199,     2199,     2199,     2262,     2304,     2427,     2602,     2724,     1811
   77,     2246,     2246,     2246,     2310,     2353,     2478,     2658,     2816,     1858
   78,     2293,     2293,     2293,     2358,     2402,     2531,     2714,     2910,     1906
   79,     2340,     2340,     2340,     2406,     2451,     2584,     2772,     3007,     1954
   80,     2392,     2392,     2392,     2462,     2507,     2643,     2836,     3099,     2009
   81,     2442,     2442,     2442,     2512,     2559,     2698,     2895,     3178,     2061
   82,     2492,     2492,     2492,     2564,     2612,     2754,     2956,     3258,     2114
   83,     2543,     2543,     2543,     2616,     2665,     2810,     3016,     3340,     2168
   84,     2595,     2595,     2595,     2669,     2719,     2868,     3078,     3422,     2224
   85,     2650,     2650,     2650,     2727,     2778,     2930,     3146,     3513,     2283
   86,     2703,     2703,     2703,     2781,     2834,     2989,     3209,     3598,     2341
   87,     2755,     2755,     2755,     2836,     2889,     3048,     3274,     3684,     2399
   88,     2810,     2810,     2810,     2891,     2945,     3108,     3338,     3773,     2459
   89,     2864,     2864,     2864,     2947,     3002,     3168,     3403,     3863,     2520
   90,     2924,     2924,     2924,     3009,     3066,     3237,     3478,     3964,     2588
   91,     2984,     2984,     2984,     3071,     3129,     3304,     3550,     4065,     2658
   92,     3045,     3045,     3045,     3134,     3194,     3373,     3625,     4170,     2730
   93,     3106,     3106,     3106,     3197,     3258,     3442,     3700,     4275,     2802
   94,     3169,     3169,     3169,     3261,     3323,     3512,     3776,     4384,     2877
   95,     3236,     3236,     3236,     3332,     3396,     3589,     3860,     4501,     2959
   96,     3301,     3301,     3301,     3398,     3463,     3660,     3939,     4613,     3036
   97,     3365,     3365,     3365,     3465,     3532,     3734,     4018,     4728,     3116
   98,     3429,     3429,     3429,     3532,     3600,     3807,     4098,     4843,     3198
   99,     3496,     3496,     3496,     3600,     3669,     3882,     4179,     4962,     3280
  100,     3569,     3569,     3569,     3677,     3748,     3966,     4271,     5092,     3373
  110,     4349,     4349,     4349,     4483,     4573,     4850,     5236,     6537,     4416
  120,     5257,     5257,     5257,     5424,     5536,     5885,     6368,     8331,     5774
  130,     6293,     6293,     6293,     6498,     6636,     7069,     7665,    10517,     7528
  140,     7491,     7491,     7491,     7742,     7910,     8446,     9178,    13212,     9408
  150,     8844,     8844,     8844,     9149,     9353,    10006,    10890,    11947,    11445
  160,    10384,    10384,    10384,    10750,    10992,    11782,    12846,    14144,    13855
  170,    12146,    12146,    12146,    12584,    12875,    13830,    15099,    16688,    16723
  180,    14118,    14118,    14118,    14637,    14982,    16118,    17620,    19548,    19906
  190,    16366,    16366,    16366,    16982,    17388,    18737,    20507,    22842,    23483
  200,    18860,    18860,    18860,    19587,    20060,    21650,    23712,    26516,    27546
  210,    21658,    21658,    21658,    22506,    23058,    24917,    27305,    30652,    32190
  220,    24039,    24039,    24039,    25006,    25631,    27750,    30459,    34255,    37547
  230,    26568,    26568,    26568,    27662,    28370,    30768,    33817,    38091,    43576
  240,    29348,    29348,    29348,    30589,    31392,    34100,    37534,    42349,    50526
  250,    32294,    32294,    32294,    33690,    34592,    37637,    41477,    46872,    40321
  260,    35466,    35466,    35466,    37030,    38041,    41451,    45739,    51761,    45535
  270,    38948,    38948,    38948,    40704,    41836,    45660,    50444,    57175,    51403
  280,    42620,    42620,    42620,    44579,    45840,    50104,    55413,    62897,    57770
  290,    46643,    46643,    46643,    48834,    50241,    54992,    60893,    69217,    64926
  300,    50878,    50878,    50878,    53311,    54875,    60144,    66663,    75872,    72667
  310,    55417,    55417,    55417,    58112,    59842,    65676,    72870,    83040,    81172
  320,    60277,    60277,    60277,    63266,    65174,    71628,    79555,    90783,    90536
  330,    65279,    65279,    65279,    68568,    70668,    77762,    86446,    98774,   100472
  340,    70739,    70739,    70739,    74363,    76673,    84476,    94006,   107557,   109727
  350,    76432,    76432,    76432,    80405,    82934,    91480,   101894,   116719,   119439
  360,    82485,    82485,    82485,    86835,    89599,    98950,   110304,   126507,   129697
  370,    89086,    89086,    89086,    93856,    96887,   107123,   119528,   137248,   140692
  380,    95943,    95943,    95943,   101154,   104450,   115616,   129104,   148418,   152122
  390,   103415,   103415,   103415,   109112,   112715,   124904,   139599,   160667,   164668
  400,   111169,   111169,   111169,   117369,   121284,   134536,   150474,   173389,   177675
  410,   119390,   119390,   119390,   126130,   130378,   144775,   162051,   186925,   191523
  420,   128342,   128342,   128342,   135688,   140306,   155969,   174704,   201751,   206696
  430,   136121,   136121,   136121,   143995,   148946,   165722,   185753,   214717,   219967
  440,   144516,   144516,   144516,   152974,   158273,   176274,   197715,   228783,   234358
  450,   153021,   153021,   153021,   162067,   167734,   186970,   209847,   243061,   248947
  460,   161754,   161754,   161754,   171415,   177452,   197957,   222307,   257711,   263926
  470,   169295,   169295,   169295,   179438,   185769,   207274,   232728,   269796,   276246
  480,   174965,   174965,   174965,   185418,   191929,   214027,   240117,   278093,   284656
  490,   181056,   181056,   181056,   191862,   198574,   221319,   248107,   287116,   293789
  500,   186940,   186940,   186940,   198066,   204963,   228326,   255745,   295696,   302476
  510,   191843,   191843,   191843,   203212,   210246,   234062,   261959,   302619,   309456
  520,   196798,   196798,   196798,   208412,   215573,   239864,   268229,   309588,   316498
  530,   201805,   201805,   201805,   213654,   220961,   245719,   274544,   316631,   323588
  540,   206854,   206854,   206854,   218959,   226403,   251630,   280927,   323733,   330752
  550,   211965,   211965,   211965,   224316,   231898,   257585,   287367,   330884,   337978
  560,   217127,   217127,   217127,   229717,   237437,   263606,   293863,   338109,   345253
  570,   222332,   222332,   222332,   235181,   243038,   269682,   300406,   345394,   352603
  580,   227598,   227598,   227598,   240697,   248694,   275803,   307017,   352729,   360015
  590,   232917,   232917,   232917,   246257,   254392,   281989,   313674,   360138,   367477
  600,   238278,   238278,   238278,   251880,   260154,   288232,   320400,   367608,   375014
  700,   294807,   294807,   294807,   310993,   320682,   353677,   390805,   445695,   453809
  800,   356575,   356575,   356575,   375453,   386607,   424759,   467100,   530124,   538998
  900,   423580,   423580,   423580,   445299,   457966,   501533,   549364,   620989,   630694
 1000,   495857,   495857,   495857,   520541,   534796,   584052,   637661,   718347,   728952
 1100,   573404,   573404,   573404,   601191,   617101,   672330,   732015,   822269,   833792
 1200,   656238,   656238,   656238,   687272,   704909,   766400,   832463,   932736,   945256
 1300,   744367,   744367,   744367,   778793,   798230,   866278,   939008,  1049810,  1063340
 1400,   837794,   837794,   837794,   875746,   897071,   971958,  1051680,  1173480,  1188090
 1500,   936509,   936509,   936509,   978164,  1001420,  1083480,  1170500,  1303790,  1319510
 1600,  1040530,  1040530,  1040530,  1086020,  1111310,  1200820,  1295450,  1440710,  1457590
 1700,  1149850,  1149850,  1149850,  1199340,  1226730,  1324000,  1426540,  1584270,  1602340
 1800,  1264480,  1264480,  1264480,  1318110,  1347680,  1453020,  1563780,  1734440,  1753760
 1900,  1384420,  1384420,  1384420,  1442350,  1474180,  1587870,  1707180,  1891280,  1911890
 2000,  1509680,  1509680,  1509680,  1572040,  1606200,  1728590,  1856750,  2054760,  2076700
```

#### Expected player attack rating, getPlayerEstimatedAttack

```
level,       d1,       d2,       d3,       d4,       d5,       d6,       d7,       d8,       d9
    1,      5.3,      5.3,      5.3,      5.3,      5.3,      5.3,      5.3,      4.9,      5.8
    2,      7.0,      7.0,      7.0,      7.0,      7.0,      7.0,      7.0,      7.0,      6.8
    3,      8.8,      8.8,      8.8,      8.8,      8.8,      8.8,      8.8,      8.1,      7.8
    4,     10.6,     10.6,     10.6,     10.6,     10.6,     10.6,     11.6,      9.3,      8.8
    5,     12.4,     12.4,     12.4,     12.4,     12.4,     13.4,     13.4,     10.5,     10.9
    6,     14.5,     14.5,     14.5,     14.5,     15.5,     15.5,     15.5,     12.7,     11.9
    7,     16.6,     16.6,     16.6,     17.6,     17.6,     17.6,     17.6,     13.9,     13.0
    8,     19.7,     19.7,     19.7,     19.7,     19.7,     19.7,     20.7,     15.1,     14.1
    9,     21.8,     21.8,     21.8,     21.8,     21.8,     21.8,     22.8,     16.3,     16.1
   10,     26.6,     26.6,     26.6,     26.6,     26.6,     27.6,     27.6,     20.6,     19.3
   11,     31.0,     31.0,     31.0,     31.0,     32.0,     32.0,     32.0,     22.0,     20.5
   12,     35.3,     35.3,     35.3,     36.3,     36.3,     36.3,     37.3,     23.4,     22.7
   13,     40.6,     40.6,     40.6,     40.6,     40.6,     41.6,     41.6,     25.8,     23.9
   14,     44.9,     44.9,     44.9,     44.9,     44.9,     45.9,     45.9,     27.2,     25.1
   15,     49.1,     49.1,     49.1,     50.1,     50.1,     50.1,     51.1,     28.5,     27.3
   16,     53.3,     53.3,     53.3,     54.3,     54.3,     55.3,     55.3,     30.9,     28.5
   17,     58.6,     58.6,     58.6,     58.6,     58.6,     59.6,     60.6,     32.3,     29.8
   18,     62.8,     62.8,     62.8,     62.8,     63.8,     63.8,     64.8,     33.7,     32.0
   19,     67.0,     67.0,     67.0,     68.0,     68.0,     69.0,     69.0,     36.1,     33.2
   20,     74.8,     74.8,     74.8,     74.8,     74.8,     75.8,     76.8,     39.7,     37.5
   21,     79.6,     79.6,     79.6,     79.6,     80.6,     80.6,     81.6,     41.2,     38.9
   22,     84.3,     84.3,     84.3,     85.3,     85.3,     86.3,     87.3,     43.8,     40.2
   23,     89.9,     89.9,     89.9,     89.9,     89.9,     90.9,     91.9,     45.3,     42.5
   24,     94.5,     94.5,     94.5,     94.5,     95.5,     95.5,     96.5,     46.9,     43.8
   25,     97.1,     97.1,     97.1,     98.1,     98.1,     99.1,      100,     49.5,     46.0
   26,      101,      101,      101,      101,      101,      102,      103,     51.0,     47.3
   27,      103,      103,      103,      103,      104,      104,      106,     53.6,     48.6
   28,      106,      106,      106,      107,      107,      108,      109,     55.2,     50.8
   29,      109,      109,      109,      110,      110,      111,      112,     56.7,     52.1
   30,      115,      115,      115,      115,      116,      116,      118,     61.7,     56.4
   31,      118,      118,      118,      119,      119,      120,      121,     64.0,     57.8
   32,      121,      121,      121,      122,      122,      123,      124,     67.2,     59.2
   33,      124,      124,      124,      124,      125,      126,      127,     69.0,     61.0
   34,      126,      126,      126,      127,      127,      128,      129,     71.8,     61.9
   35,      129,      129,      129,      130,      130,      131,      133,     73.6,     63.8
   36,      132,      132,      132,      132,      133,      134,      135,     76.4,     64.6
   37,      134,      134,      134,      135,      135,      136,      138,     78.2,     66.5
   38,      136,      136,      136,      137,      137,      138,      140,     80.9,     67.3
   39,      138,      138,      138,      139,      140,      141,      142,     82.7,     69.2
   40,      142,      142,      142,      143,      143,      144,      146,     87.8,     72.2
   41,      144,      144,      144,      145,      145,      147,      148,     89.8,     74.1
   42,      146,      146,      146,      147,      148,      149,      151,     92.8,     75.3
   43,      148,      148,      148,      149,      149,      150,      152,     94.8,     77.6
   44,      150,      150,      150,      151,      151,      153,      155,     97.8,     78.8
   45,      152,      152,      152,      152,      153,      154,      156,     99.9,     81.0
   46,      154,      154,      154,      155,      155,      157,      158,      103,     82.3
   47,      155,      155,      155,      156,      157,      158,      160,      105,     84.5
   48,      158,      158,      158,      158,      159,      160,      162,      108,     85.8
   49,      159,      159,      159,      160,      160,      162,      164,      110,     88.0
   50,      163,      163,      163,      164,      165,      166,      168,      115,     91.4
   51,      165,      165,      165,      165,      166,      168,      170,      117,     93.8
   52,      167,      167,      167,      168,      168,      170,      172,      120,     96.1
   53,      169,      169,      169,      170,      171,      172,      175,      124,     97.5
   54,      171,      171,      171,      172,      172,      174,      176,      126,     99.9
   55,      173,      173,      173,      174,      175,      176,      179,      129,      101
   56,      174,      174,      174,      175,      176,      178,      180,      131,      104
   57,      177,      177,      177,      178,      178,      180,      183,      134,      105
   58,      178,      178,      178,      179,      180,      182,      184,      138,      107
   59,      181,      181,      181,      182,      182,      184,      187,      140,      110
   60,      184,      184,      184,      185,      186,      188,      190,      145,      113
   61,      186,      186,      186,      187,      188,      190,      193,      148,      116
   62,      188,      188,      188,      189,      189,      191,      194,      151,      117
   63,      190,      190,      190,      191,      192,      194,      197,      155,      120
   64,      192,      192,      192,      193,      193,      195,      198,      157,      122
   65,      194,      194,      194,      195,      196,      198,      201,      161,      124
   66,      195,      195,      195,      196,      197,      199,      202,      164,      126
   67,      198,      198,      198,      199,      200,      202,      205,      167,      128
   68,      199,      199,      199,      200,      201,      203,      206,      170,      131
   69,      202,      202,      202,      203,      203,      206,      209,      174,      133
   70,      205,      205,      205,      206,      207,      209,      212,      178,      137
   71,      207,      207,      207,      209,      209,      212,      215,      182,      139
   72,      209,      209,      209,      210,      211,      213,      216,      186,      142
   73,      211,      211,      211,      212,      213,      216,      219,      188,      144
   74,      214,      214,      214,      215,      216,      218,      222,      192,      146
   75,      215,      215,      215,      216,      217,      220,      223,      196,      149
   76,      217,      217,      217,      219,      219,      222,      225,      199,      151
   77,      219,      219,      219,      220,      221,      223,      227,      202,      152
   78,      221,      221,      221,      222,      223,      226,      229,      205,      155
   79,      222,      222,      222,      223,      224,      227,      231,      209,      157
   80,      226,      226,      226,      228,      229,      231,      235,      213,      162
   81,      228,      228,      228,      229,      230,      233,      236,      216,      163
   82,      230,      230,      230,      231,      232,      235,      239,      218,      166
   83,      231,      231,      231,      233,      234,      236,      240,      221,      168
   84,      234,      234,      234,      235,      236,      239,      243,      223,      171
   85,      235,      235,      235,      236,      237,      240,      244,      226,      173
   86,      237,      237,      237,      239,      240,      242,      246,      228,      175
   87,      238,      238,      238,      240,      241,      244,      248,      229,      177
   88,      241,      241,      241,      242,      243,      246,      250,      232,      180
   89,      242,      242,      242,      244,      244,      247,      251,      234,      182
   90,      246,      246,      246,      248,      249,      252,      256,      239,      187
   91,      248,      248,      248,      249,      250,      253,      257,      241,      189
   92,      250,      250,      250,      252,      253,      256,      260,      244,      191
   93,      251,      251,      251,      253,      254,      257,      261,      246,      193
   94,      254,      254,      254,      255,      256,      260,      264,      249,      196
   95,      255,      255,      255,      257,      258,      261,      265,      251,      199
   96,      258,      258,      258,      259,      260,      263,      268,      254,      201
   97,      259,      259,      259,      261,      262,      265,      269,      257,      204
   98,      261,      261,      261,      263,      264,      267,      272,      259,      207
   99,      263,      263,      263,      264,      265,      269,      273,      262,      209
  100,      267,      267,      267,      269,      270,      273,      278,      266,      214
  110,      289,      289,      289,      291,      292,      296,      301,      297,      245
  120,      312,      312,      312,      314,      315,      319,      325,      329,      278
  130,      335,      335,      335,      337,      339,      343,      349,      358,      313
  140,      357,      357,      357,      359,      361,      366,      373,      382,      344
  150,      380,      380,      380,      383,      385,      390,      397,      407,      372
  160,      404,      404,      404,      407,      408,      414,      422,      432,      403
  170,      427,      427,      427,      430,      432,      439,      447,      458,      433
  180,      452,      452,      452,      455,      457,      464,      473,      484,      465
  190,      476,      476,      476,      479,      481,      488,      498,      510,      498
  200,      499,      499,      499,      503,      505,      513,      523,      535,      532
  210,      524,      524,      524,      528,      531,      539,      549,      562,      565
  220,      549,      549,      549,      553,      555,      564,      575,      589,      592
  230,      574,      574,      574,      578,      580,      590,      601,      615,      619
  240,      598,      598,      598,      603,      606,      615,      627,      642,      645
  250,      623,      623,      623,      628,      631,      641,      653,      669,      672
  260,      648,      648,      648,      653,      656,      666,      679,      695,      699
  270,      673,      673,      673,      678,      681,      692,      705,      722,      726
  280,      699,      699,      699,      704,      707,      719,      732,      750,      753
  290,      723,      723,      723,      729,      732,      744,      758,      777,      780
  300,      749,      749,      749,      755,      759,      771,      785,      804,      808
  310,      775,      775,      775,      781,      785,      798,      813,      832,      836
  320,      799,      799,      799,      806,      809,      823,      838,      858,      862
  330,      823,      823,      823,      830,      834,      848,      863,      884,      888
  340,      846,      846,      846,      853,      857,      871,      887,      909,      913
  350,      870,      870,      870,      877,      881,      895,      912,      934,      938
  360,      893,      893,      893,      900,      904,      919,      936,      959,      963
  370,      917,      917,      917,      924,      929,      944,      962,      985,      989
  380,      940,      940,      940,      948,      952,      968,      986,     1010,     1014
  390,      963,      963,      963,      971,      976,      992,     1011,     1035,     1040
  400,      987,      987,      987,      995,     1000,     1016,     1035,     1061,     1065
  410,     1010,     1010,     1010,     1018,     1023,     1040,     1060,     1086,     1090
  420,     1034,     1034,     1034,     1043,     1048,     1066,     1085,     1112,     1116
  430,     1056,     1056,     1056,     1065,     1071,     1089,     1109,     1136,     1141
  440,     1078,     1078,     1078,     1087,     1092,     1111,     1131,     1159,     1164
  450,     1100,     1100,     1100,     1109,     1115,     1134,     1155,     1184,     1188
  460,     1122,     1122,     1122,     1132,     1138,     1157,     1179,     1208,     1212
  470,     1143,     1143,     1143,     1152,     1158,     1178,     1199,     1229,     1233
  480,     1161,     1161,     1161,     1170,     1176,     1196,     1218,     1247,     1252
  490,     1179,     1179,     1179,     1189,     1195,     1214,     1236,     1266,     1270
  500,     1197,     1197,     1197,     1207,     1213,     1233,     1254,     1284,     1288
  510,     1213,     1213,     1213,     1223,     1229,     1248,     1270,     1300,     1304
  520,     1229,     1229,     1229,     1239,     1244,     1264,     1286,     1315,     1320
  530,     1245,     1245,     1245,     1254,     1260,     1280,     1301,     1331,     1335
  540,     1260,     1260,     1260,     1270,     1276,     1296,     1317,     1347,     1351
  550,     1276,     1276,     1276,     1286,     1292,     1311,     1333,     1362,     1367
  560,     1292,     1292,     1292,     1301,     1307,     1327,     1349,     1378,     1382
  570,     1307,     1307,     1307,     1317,     1323,     1343,     1364,     1394,     1398
  580,     1323,     1323,     1323,     1333,     1339,     1358,     1380,     1409,     1414
  590,     1338,     1338,     1338,     1347,     1353,     1373,     1394,     1424,     1428
  600,     1353,     1353,     1353,     1363,     1369,     1389,     1410,     1440,     1444
  700,     1508,     1508,     1508,     1518,     1524,     1544,     1565,     1595,     1599
  800,     1662,     1662,     1662,     1671,     1677,     1697,     1718,     1748,     1751
  900,     1814,     1814,     1814,     1824,     1829,     1849,     1870,     1900,     1903
 1000,     1966,     1966,     1966,     1976,     1981,     2001,     2022,     2051,     2055
 1100,     2117,     2117,     2117,     2127,     2132,     2152,     2173,     2203,     2206
 1200,     2268,     2268,     2268,     2278,     2283,     2303,     2324,     2353,     2357
 1300,     2419,     2419,     2419,     2429,     2434,     2454,     2474,     2504,     2507
 1400,     2570,     2570,     2570,     2579,     2585,     2604,     2624,     2654,     2657
 1500,     2720,     2720,     2720,     2730,     2735,     2755,     2775,     2805,     2808
 1600,     2870,     2870,     2870,     2880,     2885,     2905,     2925,     2955,     2958
 1700,     3020,     3020,     3020,     3030,     3035,     3055,     3075,     3105,     3108
 1800,     3170,     3170,     3170,     3180,     3185,     3205,     3224,     3254,     3257
 1900,     3320,     3320,     3320,     3330,     3335,     3354,     3374,     3404,     3407
 2000,     3470,     3470,     3470,     3479,     3484,     3504,     3524,     3554,     3557
```

#### Monster HP, B tier, no boss (getMonsterHealth(nil, L))

```
level,       d1,       d2,       d3,       d4,       d5,       d6,       d7,       d8,       d9
    1,     13.7,     20.6,     27.5,     34.4,     41.3,     48.3,     55.2,     62.1,     73.6
    2,     15.0,     22.5,     30.0,     37.5,     45.1,     52.7,     60.3,     71.9,     79.9
    3,     16.1,     24.1,     32.2,     40.3,     48.4,     56.5,     64.7,     76.9,     85.6
    4,     17.1,     25.6,     34.2,     42.8,     51.4,     60.0,     72.7,     81.6,     90.8
    5,     20.0,     30.0,     40.1,     50.2,     60.3,     73.9,     84.8,     94.6,      111
    6,     21.8,     32.7,     43.5,     54.6,     68.5,     80.1,     92.0,      104,      116
    7,     23.6,     35.4,     47.2,     61.7,     74.1,     86.7,     99.5,      109,      121
    8,     26.5,     39.8,     53.1,     66.5,     79.9,     93.5,      113,      113,      125
    9,     28.5,     42.8,     57.1,     71.6,     86.0,      101,      121,      117,      135
   10,     33.2,     49.8,     66.4,     83.3,      100,      122,      140,      135,      150
   11,     36.7,     55.0,     73.3,     91.9,      115,      134,      155,      140,      155
   12,     40.3,     60.4,     80.6,      105,      126,      148,      175,      144,      167
   13,     45.2,     67.9,     90.5,      113,      136,      164,      189,      154,      172
   14,     48.3,     72.4,     96.5,      121,      146,      175,      202,      159,      177
   15,     54.0,     81.0,      108,      139,      167,      196,      233,      173,      198
   16,     57.3,     86.0,      115,      147,      177,      214,      247,      183,      203
   17,     62.1,     93.2,      124,      156,      188,      227,      267,      190,      208
   18,     65.7,     98.5,      131,      165,      204,      240,      282,      197,      220
   19,     69.3,      104,      139,      179,      216,      259,      298,      211,      226
   20,     78.9,      118,      158,      198,      238,      286,      338,      229,      248
   21,     83.5,      125,      167,      210,      257,      302,      358,      237,      254
   22,     88.2,      132,      176,      226,      272,      328,      386,      251,      259
   23,     95.2,      143,      190,      239,      288,      347,      409,      259,      274
   24,      101,      151,      202,      253,      313,      368,      433,      268,      282
   25,      109,      163,      217,      280,      337,      403,      477,      296,      308
   26,      115,      173,      231,      290,      350,      418,      495,      306,      316
   27,      120,      180,      240,      301,      369,      434,      522,      321,      324
   28,      124,      186,      249,      317,      382,      460,      541,      331,      341
   29,      129,      193,      258,      329,      396,      477,      561,      341,      350
   30,      140,      210,      280,      352,      433,      511,      613,      374,      378
   31,      146,      219,      292,      375,      452,      540,      638,      388,      388
   32,      152,      228,      304,      390,      470,      562,      665,      409,      398
   33,      160,      240,      320,      403,      492,      592,      696,      422,      415
   34,      165,      248,      331,      422,      508,      611,      718,      445,      422
   35,      176,      264,      352,      449,      541,      651,      779,      471,      450
   36,      184,      276,      368,      463,      568,      679,      803,      492,      458
   37,      190,      284,      379,      486,      586,      700,      838,      507,      477
   38,      194,      291,      388,      497,      599,      716,      857,      532,      485
   39,      197,      296,      395,      506,      617,      742,      874,      548,      500
   40,      211,      316,      422,      537,      648,      779,      932,      591,      524
   41,      215,      323,      430,      548,      661,      803,      951,      611,      545
   42,      219,      329,      438,      558,      685,      818,      980,      643,      557
   43,      226,      338,      451,      578,      697,      834,      998,      664,      576
   44,      230,      345,      460,      589,      710,      863,     1034,      693,      589
   45,      244,      366,      488,      616,      750,      903,     1080,      736,      630
   46,      249,      373,      497,      633,      764,      928,     1100,      769,      643
   47,      253,      379,      506,      644,      789,      944,     1131,      787,      664
   48,      260,      390,      520,      655,      803,      961,     1151,      814,      678
   49,      264,      396,      528,      677,      817,      992,     1189,      834,      706
   50,      276,      414,      552,      706,      861,     1036,     1240,      893,      745
   51,      285,      427,      570,      719,      876,     1064,     1275,      915,      770
   52,      290,      435,      580,      738,      891,     1083,     1298,      947,      802
   53,      295,      442,      590,      751,      920,     1102,     1339,      986,      821
   54,      303,      454,      605,      775,      935,     1137,     1363,     1010,      848
   55,      315,      472,      630,      806,      982,     1183,     1430,     1071,      892
   56,      320,      480,      640,      820,      998,     1213,     1455,     1096,      927
   57,      330,      495,      660,      840,     1015,     1233,     1499,     1140,      948
   58,      335,      503,      670,      853,     1045,     1270,     1524,     1177,      979
   59,      343,      515,      686,      879,     1062,     1291,     1562,     1204,     1017
   60,      357,      535,      714,      914,     1113,     1353,     1623,     1283,     1067
   61,      363,      544,      725,      929,     1131,     1375,     1672,     1314,     1102
   62,      373,      560,      747,      951,     1150,     1398,     1700,     1358,     1127
   63,      379,      569,      759,      967,     1183,     1439,     1742,     1411,     1171
   64,      388,      583,      777,      995,     1202,     1462,     1771,     1445,     1209
   65,      403,      605,      806,     1032,     1257,     1528,     1859,     1525,     1265
   66,      409,      614,      818,     1048,     1276,     1552,     1889,     1582,     1313
   67,      420,      631,      841,     1071,     1311,     1596,     1932,     1620,     1342
   68,      427,      640,      853,     1087,     1331,     1619,     1962,     1670,     1383
   69,      436,      654,      872,     1116,     1350,     1655,     2015,     1732,     1434
   70,      452,      677,      903,     1156,     1408,     1714,     2087,     1812,     1500
   71,      458,      688,      917,     1182,     1430,     1761,     2134,     1870,     1547
   72,      471,      706,      941,     1200,     1468,     1788,     2168,     1940,     1604
   73,      478,      716,      955,     1217,     1490,     1827,     2226,     1987,     1641
   74,      488,      732,      976,     1249,     1522,     1854,     2275,     2049,     1690
   75,      505,      757,     1009,     1292,     1574,     1939,     2352,     2167,     1787
   76,      511,      767,     1022,     1317,     1594,     1964,     2383,     2213,     1824
   77,      523,      785,     1047,     1334,     1633,     1990,     2440,     2276,     1861
   78,      530,      795,     1060,     1351,     1653,     2028,     2472,     2324,     1911
   79,      537,      805,     1073,     1368,     1674,     2053,     2519,     2402,     1950
   80,      554,      831,     1108,     1427,     1738,     2118,     2597,     2492,     2050
   81,      565,      847,     1129,     1446,     1761,     2169,     2632,     2546,     2084
   82,      572,      858,     1143,     1464,     1783,     2197,     2694,     2585,     2133
   83,      579,      868,     1158,     1492,     1825,     2225,     2729,     2654,     2168
   84,      593,      889,     1185,     1510,     1848,     2267,     2780,     2696,     2231
   85,      611,      916,     1221,     1556,     1904,     2335,     2863,     2810,     2309
   86,      618,      927,     1236,     1592,     1939,     2364,     2898,     2857,     2361
   87,      626,      938,     1251,     1611,     1962,     2417,     2964,     2906,     2399
   88,      637,      955,     1273,     1631,     1986,     2447,     3000,     2987,     2466
   89,      644,      966,     1289,     1659,     2010,     2476,     3036,     3037,     2505
   90,      664,      995,     1327,     1709,     2090,     2563,     3142,     3162,     2608
   91,      679,     1018,     1358,     1731,     2118,     2597,     3184,     3220,     2654
   92,      688,     1031,     1375,     1771,     2157,     2657,     3258,     3314,     2731
   93,      696,     1044,     1392,     1793,     2184,     2691,     3301,     3374,     2778
   94,      709,     1063,     1418,     1816,     2212,     2740,     3361,     3454,     2842
   95,      730,     1094,     1459,     1879,     2298,     2820,     3458,     3574,     2973
   96,      746,     1119,     1492,     1902,     2327,     2855,     3535,     3675,     3024
   97,      755,     1132,     1510,     1944,     2368,     2918,     3580,     3759,     3092
   98,      764,     1146,     1528,     1967,     2397,     2954,     3643,     3826,     3178
   99,      777,     1166,     1554,     1991,     2425,     3006,     3689,     3931,     3231
  100,      799,     1199,     1599,     2058,     2518,     3091,     3828,     4066,     3359
  110,      967,     1451,     1934,     2491,     3048,     3780,     4666,     5297,     4345
  120,     1161,     1741,     2322,     2991,     3661,     4545,     5663,     6844,     5640
  130,     1383,     2075,     2767,     3566,     4383,     5448,     6795,     8607,     7246
  140,     1638,     2458,     3277,     4225,     5194,     6512,     8158,    10355,     8966
  150,     1930,     2895,     3859,     5013,     6162,     7708,     9700,    12374,    11021
  160,     2276,     3414,     4552,     5893,     7224,     9107,    11502,    14698,    13677
  170,     2654,     3981,     5308,     6875,     8455,    10733,    13564,    17405,    16754
  180,     3090,     4635,     6180,     8034,     9882,    12516,    15915,    20449,    20477
  190,     3594,     5391,     7188,     9319,    11464,    14578,    18586,    24035,    24847
  200,     4141,     6212,     8282,    10800,    13288,    16950,    21611,    27970,    30173
  210,     4766,     7149,     9532,    12434,    15378,    19629,    25026,    32477,    36252
  220,     5467,     8201,    10935,    14270,    17565,    22484,    28813,    37579,    42452
  230,     6233,     9350,    12466,    16275,    20040,    25788,    33053,    43121,    49320
  240,     7071,    10606,    14142,    18554,    22894,    29425,    37789,    49396,    56400
  250,     8035,    12052,    16069,    21034,    26028,    33530,    43066,    56536,    64393
  260,     9080,    13620,    18160,    23841,    29430,    37937,    48933,    64243,    73467
  270,    10261,    15391,    20522,    26882,    33275,    42981,    55440,    72901,    83364
  280,    11537,    17305,    23074,    30311,    37434,    48565,    62644,    82682,    94205
  290,    12924,    19386,    25847,    34014,    42116,    54660,    70604,    93308,   106563
  300,    14500,    21750,    29000,    38173,    47335,    61458,    79383,   104905,   119965
  310,    16196,    24294,    32392,    42650,    52892,    68941,    89156,   118066,   135021
  320,    18010,    27015,    36020,    47498,    58838,    76804,    99318,   131667,   150582
  330,    19881,    29822,    39762,    52559,    65192,    85117,   110062,   146355,   167390
  340,    21954,    32931,    43908,    57927,    71858,    93847,   121726,   162012,   185314
  350,    24224,    36337,    48449,    63933,    79315,   103611,   134777,   179343,   205160
  360,    26600,    39900,    53199,    70360,    87297,   114183,   148498,   197768,   226223
  370,    29220,    43829,    58439,    77153,    96016,   125615,   163489,   218102,   249393
  380,    31984,    47976,    63968,    84717,   105129,   137960,   179518,   239665,   273956
  390,    35025,    52538,    70051,    92788,   115259,   151276,   197338,   263399,   301244
  400,    38333,    57500,    76667,   101568,   126170,   165623,   215998,   289249,   330419
  410,    41779,    62669,    83559,   110718,   137794,   181063,   236269,   316327,   361244
  420,    45558,    68337,    91116,   120850,   150405,   198163,   257861,   346020,   395039
  430,    48676,    73014,    97351,   129364,   161129,   212304,   276884,   370839,   424268
  440,    52083,    78124,   104165,   138431,   171994,   227193,   296230,   397617,   454029
  450,    55624,    83437,   111249,   147609,   183849,   242857,   316808,   426126,   486108
  460,    59191,    88786,   118381,   157463,   196115,   259048,   338601,   454566,   518421
  470,    62261,    93391,   124521,   165459,   206020,   272104,   354469,   476344,   543049
  480,    64615,    96923,   129230,   171324,   213228,   281221,   366529,   491167,   560027
  490,    66922,   100382,   133843,   177734,   221106,   291006,   378627,   506644,   577027
  500,    69395,   104093,   138791,   184185,   229032,   301216,   390408,   521369,   593527
  510,    71335,   107002,   142670,   189269,   235294,   309021,   400980,   534844,   608664
  520,    73424,   110136,   146848,   194743,   241513,   317147,   411113,   547413,   623138
  530,    75434,   113151,   150868,   199886,   248369,   325898,   421158,   560501,   637467
  540,    77432,   116148,   154864,   205239,   254958,   334299,   432248,   574616,   653325
  550,    79632,   119449,   159265,   211000,   262051,   342638,   442876,   587791,   668489
  560,    81749,   122624,   163498,   216415,   268713,   351825,   454326,   601498,   683508
  570,    83854,   125781,   167708,   222045,   275640,   360644,   465041,   616274,   700109
  580,    86169,   129254,   172338,   228102,   283093,   369400,   476180,   630074,   715985
  590,    88396,   132593,   176791,   233796,   290096,   379037,   487231,   644420,   731715
  600,    90610,   135915,   181220,   239712,   297370,   388286,   499406,   659877,   749083
  700,   115524,   173286,   231048,   304759,   377297,   489687,   624376,   818031,   926710
  800,   148010,   222014,   296019,   389816,   482102,   624062,   792957,  1035270,  1130240
  900,   185864,   278796,   371729,   489160,   603532,   779487,   988683,  1287080,  1361080
 1000,   229389,   344084,   458779,   603107,   744392,   959527,  1212760,  1574520,  1624030
 1100,   279118,   418678,   558237,   733196,   904353,  1163750,  1467860,  1902400,  1917520
 1200,   335544,   503316,   671087,   880707,  1085660,  1394990,  1756430,  2271880,  2287840
 1300,   399093,   598640,   798186,  1046750,  1289660,  1654960,  2080130,  2687150,  2700430
 1400,   470194,   705292,   940389,  1232190,  1517710,  1943420,  2439510,  3147270,  3162760
 1500,   549178,   823767,  1098360,  1438610,  1769480,  2265790,  2840880,  3660840,  3676070
 1600,   636082,   954123,  1272160,  1665370,  2049220,  2621600,  3283630,  4227020,  4238710
 1700,   732238,  1098360,  1464480,  1916190,  2355360,  3010790,  3767690,  4845730,  4859760
 1800,   837071,  1255610,  1674140,  2189550,  2692440,  3439130,  4296740,  5521650,  5534680
 1900,   952098,  1428150,  1904200,  2489410,  3058300,  3903380,  4877110,  6262820,  6270590
 2000,  1076550,  1614830,  2153100,  2813440,  3455560,  4408280,  5504320,  7063520,  7073690
```

#### Monster damage per hit before mitigation, B tier, no boss (getMonsterDamage(nil, L))

```
level,       d1,       d2,       d3,       d4,       d5,       d6,       d7,       d8,       d9
    1,      4.5,      6.3,      9.0,      9.8,     10.8,     12.0,     13.4,     15.3,     17.6
    2,      4.9,      6.9,      9.9,     10.8,     11.9,     13.2,     14.7,     16.9,     19.3
    3,      5.4,      7.5,     10.7,     11.7,     12.9,     14.3,     16.1,     18.6,     21.3
    4,      5.8,      8.1,     11.6,     12.7,     13.9,     15.4,     17.7,     20.4,     23.3
    5,      6.2,      8.7,     12.5,     13.7,     15.0,     16.8,     19.2,     22.2,     25.4
    6,      6.7,      9.4,     13.4,     14.8,     16.3,     18.2,     20.8,     24.1,     27.4
    7,      7.2,     10.1,     14.4,     16.0,     17.5,     19.6,     22.4,     25.9,     29.5
    8,      7.8,     10.9,     15.5,     17.1,     18.8,     21.0,     24.1,     27.8,     31.6
    9,      8.3,     11.6,     16.6,     18.3,     20.1,     22.5,     25.8,     29.8,     33.8
   10,      8.9,     12.5,     17.8,     19.7,     21.6,     24.3,     27.8,     32.0,     36.1
   11,      9.8,     13.8,     19.7,     21.7,     23.9,     26.8,     30.7,     34.1,     38.4
   12,     10.8,     15.1,     21.6,     23.8,     26.2,     29.4,     33.8,     36.2,     40.9
   13,     11.8,     16.5,     23.6,     26.1,     28.6,     32.2,     37.0,     38.5,     43.3
   14,     12.9,     18.0,     25.8,     28.4,     31.2,     35.1,     40.3,     40.8,     45.7
   15,     14.0,     19.6,     28.0,     31.0,     34.1,     38.3,     44.0,     43.2,     48.4
   16,     15.2,     21.3,     30.4,     33.6,     36.9,     41.6,     47.8,     45.7,     51.0
   17,     16.5,     23.1,     33.0,     36.4,     40.0,     45.0,     51.8,     48.2,     53.6
   18,     17.8,     24.9,     35.6,     39.3,     43.2,     48.7,     56.0,     50.7,     56.4
   19,     19.2,     26.9,     38.4,     42.4,     46.6,     52.6,     60.5,     53.4,     59.2
   20,     20.8,     29.1,     41.6,     45.9,     50.5,     57.0,     65.7,     56.2,     62.3
   21,     22.5,     31.5,     45.0,     49.6,     54.6,     61.6,     71.0,     59.0,     65.2
   22,     24.2,     33.9,     48.5,     53.5,     58.9,     66.5,     76.7,     62.0,     68.3
   23,     26.1,     36.6,     52.2,     57.6,     63.4,     71.6,     82.6,     64.9,     71.5
   24,     28.1,     39.3,     56.1,     62.0,     68.2,     77.0,     88.9,     67.9,     74.6
   25,     29.7,     41.5,     59.3,     65.6,     72.1,     81.5,     94.1,     71.2,     78.0
   26,     31.3,     43.8,     62.6,     69.1,     76.1,     86.0,     99.3,     74.3,     81.3
   27,     33.0,     46.2,     66.0,     72.8,     80.2,     90.6,      105,     77.7,     84.7
   28,     34.7,     48.6,     69.4,     76.7,     84.4,     95.4,      110,     81.0,     88.3
   29,     36.5,     51.1,     73.0,     80.6,     88.7,      100,      116,     84.4,     91.8
   30,     38.5,     53.9,     76.9,     84.9,     93.6,      106,      122,     88.5,     95.7
   31,     40.5,     56.6,     80.9,     89.4,     98.4,      111,      129,     93.0,     99.4
   32,     42.5,     59.5,     85.0,     93.9,      103,      117,      135,     97.8,      103
   33,     44.7,     62.5,     89.3,     98.6,      109,      123,      142,      103,      107
   34,     46.8,     65.6,     93.7,      103,      114,      129,      149,      108,      111
   35,     49.1,     68.8,     98.3,      109,      119,      135,      157,      113,      115
   36,     51.5,     72.1,      103,      114,      125,      142,      164,      118,      120
   37,     53.9,     75.4,      108,      119,      131,      148,      172,      124,      124
   38,     56.3,     78.8,      113,      124,      137,      155,      180,      130,      128
   39,     58.8,     82.3,      118,      130,      143,      162,      188,      136,      133
   40,     61.6,     86.3,      123,      136,      150,      170,      197,      142,      137
   41,     64.4,     90.2,      129,      142,      157,      178,      207,      149,      142
   42,     60.5,     84.7,      121,      134,      147,      167,      194,      156,      147
   43,     62.6,     87.6,      125,      138,      152,      173,      201,      163,      153
   44,     64.7,     90.5,      129,      143,      157,      179,      208,      170,      159
   45,     66.9,     93.6,      134,      148,      163,      185,      215,      178,      165
   46,     69.0,     96.6,      138,      153,      168,      191,      222,      185,      171
   47,     71.2,     99.7,      142,      157,      173,      197,      230,      193,      177
   48,     73.4,      103,      147,      162,      179,      203,      237,      202,      183
   49,     75.7,      106,      151,      167,      184,      210,      244,      210,      190
   50,     78.1,      109,      156,      173,      190,      217,      253,      219,      197
   51,     80.6,      113,      161,      178,      196,      224,      261,      229,      204
   52,     83.0,      116,      166,      184,      202,      230,      269,      238,      211
   53,     85.5,      120,      171,      189,      208,      237,      277,      248,      219
   54,     88.0,      123,      176,      195,      214,      245,      286,      259,      226
   55,     90.7,      127,      181,      201,      221,      252,      295,      270,      234
   56,     93.3,      131,      187,      206,      227,      260,      304,      281,      242
   57,     96.0,      134,      192,      212,      234,      267,      313,      292,      250
   58,     98.7,      138,      197,      218,      241,      275,      322,      304,      258
   59,      101,      142,      203,      224,      247,      283,      331,      315,      267
   60,      104,      146,      209,      231,      255,      291,      341,      329,      276
   61,      107,      150,      215,      237,      262,      299,      351,      342,      285
   62,      110,      154,      221,      244,      269,      308,      361,      356,      295
   63,      113,      159,      227,      251,      276,      316,      371,      370,      304
   64,      116,      163,      233,      258,      284,      325,      381,      384,      314
   65,      120,      167,      239,      265,      292,      334,      393,      400,      324
   66,      123,      172,      246,      272,      300,      343,      403,      416,      335
   67,      126,      176,      252,      279,      308,      352,      414,      432,      345
   68,      129,      181,      258,      286,      315,      361,      425,      448,      356
   69,      132,      185,      265,      293,      323,      371,      436,      465,      367
   70,      136,      190,      272,      301,      332,      381,      448,      484,      379
   71,      139,      195,      279,      309,      340,      391,      460,      503,      391
   72,      143,      200,      286,      316,      349,      401,      472,      523,      403
   73,      146,      205,      293,      324,      358,      411,      484,      542,      415
   74,      150,      210,      300,      332,      366,      421,      496,      563,      428
   75,      154,      215,      308,      341,      376,      432,      510,      586,      441
   76,      157,      220,      314,      348,      384,      441,      520,      605,      453
   77,      160,      225,      321,      355,      392,      451,      532,      626,      464
   78,      164,      229,      328,      363,      400,      460,      543,      647,      476
   79,      167,      234,      334,      370,      409,      470,      554,      668,      489
   80,      171,      239,      342,      379,      418,      480,      567,      689,      502
   81,      174,      244,      349,      387,      427,      491,      579,      706,      515
   82,      178,      249,      356,      394,      435,      501,      591,      724,      529
   83,      182,      254,      363,      403,      444,      511,      603,      742,      542
   84,      185,      259,      371,      411,      453,      521,      616,      760,      556
   85,      189,      265,      379,      419,      463,      533,      629,      781,      571
   86,      193,      270,      386,      428,      472,      543,      642,      799,      585
   87,      197,      276,      394,      436,      481,      554,      655,      819,      600
   88,      201,      281,      401,      445,      491,      565,      668,      839,      615
   89,      205,      286,      409,      453,      500,      576,      681,      858,      630
   90,      209,      292,      418,      463,      511,      589,      696,      881,      647
   91,      213,      298,      426,      472,      522,      601,      710,      903,      664
   92,      217,      304,      435,      482,      532,      613,      725,      927,      682
   93,      222,      311,      444,      492,      543,      626,      740,      950,      701
   94,      226,      317,      453,      502,      554,      639,      755,      974,      719
   95,      231,      324,      462,      513,      566,      653,      772,     1000,      740
   96,      236,      330,      472,      523,      577,      666,      788,     1025,      759
   97,      240,      336,      481,      533,      589,      679,      804,     1051,      779
   98,      245,      343,      490,      543,      600,      692,      820,     1076,      799
   99,      250,      350,      499,      554,      612,      706,      836,     1103,      820
  100,      255,      357,      510,      566,      625,      721,      854,     1132,      843
  110,      311,      435,      621,      690,      762,      882,     1047,     1453,     1104
  120,      376,      526,      751,      835,      923,     1070,     1274,     1851,     1444
  130,      450,      629,      899,     1000,     1106,     1285,     1533,     2337,     1882
  140,      535,      749,     1070,     1191,     1318,     1536,     1836,     2936,     2352
  150,      632,      884,     1263,     1408,     1559,     1819,     2178,     2655,     2861
  160,      742,     1038,     1483,     1654,     1832,     2142,     2569,     3143,     3464
  170,      868,     1215,     1735,     1936,     2146,     2514,     3020,     3709,     4181
  180,     1008,     1412,     2017,     2252,     2497,     2931,     3524,     4344,     4977
  190,     1169,     1637,     2338,     2613,     2898,     3407,     4101,     5076,     5871
  200,     1347,     1886,     2694,     3013,     3343,     3936,     4742,     5892,     6886
  210,     1547,     2166,     3094,     3462,     3843,     4530,     5461,     6812,     8047
  220,     1717,     2404,     3434,     3847,     4272,     5045,     6092,     7612,     9387
  230,     1898,     2657,     3795,     4256,     4728,     5594,     6763,     8465,    10894
  240,     2096,     2935,     4193,     4706,     5232,     6200,     7507,     9411,    12631
  250,     2307,     3229,     4613,     5183,     5765,     6843,     8295,    10416,    10080
  260,     2533,     3547,     5067,     5697,     6340,     7536,     9148,    11502,    11384
  270,     2782,     3895,     5564,     6262,     6973,     8302,    10089,    12706,    12851
  280,     3044,     4262,     6089,     6858,     7640,     9110,    11083,    13977,    14443
  290,     3332,     4664,     6663,     7513,     8373,     9999,    12179,    15382,    16231
  300,     3634,     5088,     7268,     8202,     9146,    10935,    13333,    16860,    18167
  310,     3958,     5542,     7917,     8940,     9974,    11941,    14574,    18453,    20293
  320,     4305,     6028,     8611,     9733,    10862,    13023,    15911,    20174,    22634
  330,     4663,     6528,     9326,    10549,    11778,    14139,    17289,    21950,    25118
  340,     5053,     7074,    10106,    11440,    12779,    15359,    18801,    23902,    27432
  350,     5459,     7643,    10919,    12370,    13822,    16633,    20379,    25938,    29860
  360,     5892,     8249,    11784,    13359,    14933,    17991,    22061,    28113,    32424
  370,     6363,     8909,    12727,    14439,    16148,    19477,    23906,    30500,    35173
  380,     6853,     9594,    13706,    15562,    17408,    21021,    25821,    32982,    38030
  390,     7387,    10342,    14774,    16786,    18786,    22710,    27920,    35704,    41167
  400,     7941,    11117,    15881,    18057,    20214,    24461,    30095,    38531,    44419
  410,     8528,    11939,    17056,    19405,    21730,    26323,    32410,    41539,    47881
  420,     9167,    12834,    18335,    20875,    23384,    28358,    34941,    44834,    51674
  430,     9723,    13612,    19446,    22153,    24824,    30131,    37151,    47715,    54992
  440,    10323,    14452,    20645,    23534,    26379,    32050,    39543,    50841,    58590
  450,    10930,    15302,    21860,    24933,    27956,    33994,    41970,    54014,    62237
  460,    11554,    16175,    23108,    26372,    29575,    35992,    44461,    57269,    65982
  470,    12092,    16930,    24185,    27606,    30962,    37686,    46546,    59955,    69061
  480,    12498,    17496,    24995,    28526,    31988,    38914,    48024,    61798,    71164
  490,    12933,    18106,    25865,    29517,    33096,    40240,    49621,    63803,    73447
  500,    13353,    18694,    26706,    30472,    34161,    41514,    51149,    65710,    75619
  510,    13703,    19184,    27406,    31264,    35041,    42557,    52392,    67249,    77364
  520,    14057,    19680,    28114,    32063,    35929,    43612,    53646,    68797,    79125
  530,    14415,    20180,    28829,    32870,    36827,    44676,    54909,    70362,    80897
  540,    14775,    20685,    29551,    33686,    37734,    45751,    56185,    71941,    82688
  550,    15140,    21196,    30281,    34510,    38650,    46834,    57473,    73530,    84495
  560,    15509,    21713,    31018,    35341,    39573,    47928,    58773,    75135,    86313
  570,    15881,    22233,    31762,    36182,    40506,    49033,    60081,    76754,    88151
  580,    16257,    22760,    32514,    37030,    41449,    50146,    61403,    78384,    90004
  590,    16637,    23292,    33274,    37886,    42399,    51271,    62735,    80031,    91869
  600,    17020,    23828,    34040,    38751,    43359,    52406,    64080,    81691,    93754
  700,    21058,    29481,    42115,    47845,    53447,    64305,    78161,    99043,   113452
  800,    25470,    35658,    50939,    57762,    64435,    77229,    93420,   117805,   134749
  900,    30256,    42358,    60512,    68508,    76328,    91188,   109873,   137997,   157673
 1000,    35418,    49586,    70837,    80083,    89133,   106191,   127532,   159633,   182238
 1100,    40957,    57340,    81915,    92491,   102850,   122242,   146403,   182727,   208448
 1200,    46874,    65624,    93748,   105734,   117485,   139345,   166493,   207275,   236314
 1300,    53169,    74437,   106338,   119814,   133038,   157505,   187802,   233292,   265836
 1400,    59842,    83779,   119685,   134730,   149512,   176720,   210336,   260774,   297021
 1500,    66894,    93651,   133787,   150487,   166904,   196997,   234100,   289732,   329877
 1600,    74323,   104053,   148647,   167080,   185218,   218331,   259089,   320158,   364397
 1700,    82132,   114985,   164264,   184513,   204455,   240728,   285309,   352059,   400586
 1800,    90320,   126448,   180640,   202787,   224614,   264186,   312755,   385431,   438441
 1900,    98888,   138442,   197775,   221900,   245697,   288704,   341437,   420284,   477972
 2000,   107834,   150968,   215668,   241852,   267701,   314289,   371350,   456614,   519176
```

---

## 10. Porting notes and MAW bugs on the monster side

### 10.1 Porting

- The model is pure: given a level and the difficulty/mode flags it needs no game state except `Party.Count`. A C++
  port can be checked row by row against [data/balance_golden.csv](data/balance_golden.csv); the harness can be rerun
  on a later MAW commit to regenerate it (2.1).
- The alternative, shipping the golden table and interpolating, ties OpenYAMM to these item/skill curves forever. If
  OpenYAMM ever changes a curve the model reads (enchant strength, skill points, stat table), the model must move with
  it, which is exactly the coupling MAW's header comment warns about (E:5-9).
- Store per actor: resolved level (uncapped), family B level, tier, boss record (affix, HP and damage mult, level),
  unique flag. Do not reproduce the 16-bit proxy HP, the 255 level cap, NameId ranges or PlaceMon name parsing.
- Resolve levels per spawn from [data/map_levels.yml](data/map_levels.yml) keyed by map file; MAW's display-name keys
  merge maps that share a name.

### 10.2 MAW bugs found (record each as a deviation if fixed)

Model (section 5): two `buffPower` tables; Cover gate drops to 0 at GM; spell power uses Haste as Empower; dead
`wDmg - wDice - wFlat` terms.

Level resolution and tables:

- `mapLevels` duplicate keys: `"Temple of the Sun"` (d22.blv's 40/40/40 is overwritten by 6t4.blv's 15/24/25),
  `"pending"` (zdtl02.blv's 40/50/50, the map MAW gave monsters, is overwritten by 1/1/1). Both maps named
  `"Temple of the Sun"` also share one madness level (position 24 of 58).
- A-tier templates use the previous map's B level (6.1).
- The global `bolsterLevel` is clobbered inside the monster loop; chest gold on horizontal maps and in the arena reads
  the last monster's `base x 2.5` (or `x 6`) instead of the bolster (7.5).
- Starter maps add the reset bonus twice in their cap (7.3).
- `mapvars.mawBounty` is never cleared: after a bounty, every monster of that town keeps `base + bounty` levels, and
  Beyond Madness gives no kill experience there (7.5).
- Easy and Normal are the same difficulty index; bolster 70 is unreachable; the austerity table entries 7-9 are
  unreachable ([data/difficulty.yml](data/difficulty.yml)).
- Hard and Hell raise `Hi` only for slots whose current `Hi <= 3`, so after Nightmare or Doom the larger values
  survive a switch back down until a restart; `Dif` is never restored below Nightmare.
- Kill experience: the MM7 bonus reads the global `currentWorld`, set only by the training code.
- Experience requirement clamp at 2^31 - 1: from level 863 onward a character with that much experience can train
  every level for free ([data/exp_curve.yml](data/exp_curve.yml)).
- Table typos: `Affraid` (8 rows) and treasure without `L` (8 rows) ([MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md)).

Bosses and dimension maps ([data/bosses.yml](data/bosses.yml),
[data/dimension_affixes.yml](data/dimension_affixes.yml)):

- Dropped dimension maps always have 2-4 affixes, never 1 (`elseif bonus<=0.6` tests `bonus`, `zzMaw-Maps.lua:923`).
- Affixes 5 and 6 reflect `(100 - X) %` instead of `X %`; affix 7 heals a stale global instead of every monster;
  affix 13 only affects Stun; affix 14 turns every monster hit into Energy (`random() < X` without `/100`); affix 15
  does not change monster HP (only the leech reference); affix 33 compounds on reload; the proc list names a
  non-existent affix 34.
- An Omnipotent roll can replace a Broodlord roll after its HP multiplier was applied (HP x6 in total); seeded Madness
  specials use different multipliers from the random ones.
- Swapper, when hit, swaps with every eligible monster in turn.

---

## 11. Not covered

- **Validation against the running game.** The golden output comes from MAW's own code in a harness, not from MAW's
  in-game debug output or a save. The int conversion of fractional stats (2.1) and LuaJIT-specific behaviour were not
  checked against MMExtension.
- **Healing estimates** (3.12) and everything else that needs live game tables (`oldTable`, spell delays).
- **The player side of combat** that turns monster damage into HP loss (`calcMawDamage`, mitigation, crits, dodge):
  see [COMBAT.md](COMBAT.md) §1-2.
- **Per-map native family lists.** [data/map_levels.yml](data/map_levels.yml) has the bands, not which families are
  native on each map; those come from `mapstats.txt` pictures at runtime (and change under the Randomizer and in
  dimension maps). The arena's `monTbl` order was not enumerated.
- **Randomizer** pool shuffling and its density table beyond the numbers in [data/difficulty.yml](data/difficulty.yml);
  **Survival mode** (dead code); `AdaptiveMonstersStats.lua` (switched off by MAW).
- **Monster AI and movement helpers** (`nudgeMonsterAroundCorner`, out-of-bounds fixes, homing missiles, the MM6
  projectile restore), crowd control and monster spells beyond their damage multipliers.
- **Loot** beyond monster treasure fields (rarity rolls, enchant strength, item level): [ITEMS.md](ITEMS.md).
- **Multiplayer** boss and monster synchronisation.
- Whether the original MM8 table parser accepts `Affraid`, `+6` treasure cells and quoted thousands was not checked
  against the binary.

---

## 12. Corrections to existing docs

Errors or omissions in [COMBAT.md](COMBAT.md) and [README.md](README.md) found during this pass. Those files were
not edited.

- **README §4.5, COMBAT §3.2.** Says: `mapLevels` has "about 300" entries. Code: 208 entries (193 distinct names)
  covering all 207 mapstats rows; two duplicates overwrite real values (10.2).
- **COMBAT §3.1.** Says: "Relative to MAW: Easy/Normal ×0.5 ... Madness ×2.5/×1.75". Code: Those are the hit-table
  ratios; actual monster ratios also move with the difficulty-dependent expected character (9.2), e.g. Hell 1.63/1.26
  and Beyond Madness 4.14/2.50 at level 300.
- **README §2.2.** Says: "Weak/normal/strong variants are 0.66/1/1.5". Code: That is damage only; HP uses the
  MONSTERS.txt HP ratio to the B row, clamped to 0.6-1.8.
- **README §2.2, COMBAT §3.1.** Says: HP = "expected player damage per swing" × hits. Code: Power includes attack
  speed, crit overflow, enchants and hit chance: it is damage per base-recovery attack, closer to DPS than per swing.
- **COMBAT §3.2.** Says: Unique monsters, free progression `bolsteredLevel(partyLvl, old)`; "Madness: map-level
  based". Code: `partyLvl` has no −4; horizontal starter maps also use it; Madness is `M + 2(high − mid)` on fixed
  maps, else `3 × old`; uniques' HP and damage still come from the family B level.
- **COMBAT §3.2.** Says: Madness "within-map spread is ±2× the Low/Mid/High offsets". Code: Also ±2× the tier offset;
  non-native families use `Xslot = 0`, i.e. offset `−2 × mean`, and land far below M.
- **COMBAT §3.5, §4 table.** Says: "Insanity and Madness use seeded affix rolls ... and pity counters"; Insanity "×3
  specials, seeded". Code: Seeding and pity need `madnessMode` (`M:3030`); Road to Insanity rolls unseeded with chance
  ×3. Seeded Broodlord is HP ×2 and damage ×1.5 on top of the roll; seeded Omnipotent HP ×4, damage ×2 on top.
- **COMBAT §3.5.** Says: Summoner "spawns an A-tier add". Code: Tier roll A 75 %, B 25 %.
- **COMBAT §3.5.** Says: Boss HP mult `2.5·(1 + L/255)·U(1,1.5)`. Code: Correct, but L is the engine level capped at
  255, so the mult is at most 7.5.
- **COMBAT §3.6 table.** Says: Insanity: "Low ≥ 3 only". Code: Insanity is also `Mode 2`, so the Doom block applies
  too: Hi +2 and Dif +1; Madness also gets Dif +1.
- **COMBAT §3.6.** Says: Hard/Hell "+1 Hi when Hi ≤ 3". Code: Tested on the current value, not the backup (10.2); the
  Randomizer uses a different, older table.
- **COMBAT §4.** Says: "A new game gives 5000 gold and +10000/partyCount exp". Code: Only Doom, Road to Insanity and
  Beyond Madness; gold is set to 5000, not added.
- **COMBAT §4.** Says: Easy/Normal are distinguished by "CC cost (`getCCDiffMult`)". Code: `max((b − 100)/200 + 1, 1)`
  is 1 for both 0 and 50.
- **COMBAT §4 table.** Says: Turn-based limit blank for Insanity; item-level requirement blank for Madness. Code: Both
  apply (Insanity and Madness are `Mode 2`): requirement −6 (bolster 300+), −3 Doom, −3 insanity, so −12 in Madness.
- **COMBAT §6.8, README §2.4.** Says: Dimension maps have "1–4 random affixes". Code: Dropped maps have 2 affixes
  (70%), 3 (20%) or 4 (10%), never 1; maps granted on completion have 1-4.
- **COMBAT §6.8.** Says: Dimension drop: "Monster level must be ≥ 100 (70 in Madness)". Code: In Madness the map level
  (mean + 20 + Power × 10) must also reach 950, otherwise no drop; the pool `mapDungeons` (143 ids) includes outdoor
  maps 1-14.
- **COMBAT §6.8.** Says: Affix list "+resistance, CC resist, energy, HP" etc. as effects. Code: Several affixes do
  something else (10.2): HP does not change, CC only Stun, Energy always, reflect inverted, regen broken.
- **COMBAT §6.5.** Says: Bounty level `base + max(getPartyLevel(4) − BLevel/1.5, 0)`. Code: Correct, but it applies to
  every monster on the town map and is never cleared.
- **README §2.1.** Says: Horizontal: "fixed at about 2.5× their vanilla level". Code: Natives sit at `X+1.5mean-9` (X
  = their band value): about 2.5× the map band, with the band's spread and tier offsets kept at 1×.
