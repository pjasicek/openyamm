# MAW mod: combat math, stats, monsters, difficulty, bolster, progression

> Formulas updated to MAW `8fbb48d1` (2026-11-05) and `8967ae88` (2026-11-12) where [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) and [UPSTREAM_SYNC_8967ae88.md](UPSTREAM_SYNC_8967ae88.md) list a change.

First-pass overview. Corrected on 2026-10-22 against the verified specs listed in [README.md](README.md); where they
differ, the spec documents win.

Analysis of `/home/pjasicek/github/Maw-Mod-MMMerge` (HEAD `ef23ee17`), compared with base MMMerge
(`reference/mmmerge`, `reference/mmerge_data_forus`). All paths below are relative to
`Maw-Mod-MMMerge/Scripts/` unless stated. "L" = monster level, "lvl" = player level.

**Read this first: the README is out of date.** The mod is half-way through a migration
("MawCore greenfield", `Modules/MawCore/README.md`) and most of the numbers in `README.md` describe
an older version. Examples:

- Monster HP and damage are no longer fixed curves ("×2 early, ×12 at L100, ×250 at L250"). They
  come from a model of the expected player at that level (section 3.1).
- The difficulty multipliers are not "0.6/0.8/1/1.5/2/3". They are hits-to-kill tables (section 4).
- Speed gives +1% attack speed per 10 points, not 2%.
- Accuracy and Luck crit values scale with monster level (weapon hits only).
- Nightmare does not ban saving near monsters. Saving costs food instead.
- Bosses ("elites") appear on every difficulty from MAW upward, on every map, not only in
  Nightmare dungeons.

The code is the authority. Where this document quotes README behaviour, it says so.

---

## 0. Architecture in one page

- **Load path.** `General/zzzzzMaw_Core.lua` → `Modules/MawCoreMain.lua`. The modules load in one
  explicit order (`MawCoreMain.lua:44-65`): Engine, Fixes, SpecialItems, Formulas, ItemLevel,
  Artifacts, Estimates, Classes, Pipeline, Scheduler, ItemFields, Tooltip, Save, Skills,
  SkillTooltip, SkillsUI, MonsterHP, DamageState, Damage, Sync. Loading a module only defines
  things; `MawCore.start()` activates them.
- **Damage.** Two ordered pipelines of named stages in `Modules/MawCore/Damage.lua`:
  - `DamageToMonster`: 36 named stages including `publish` (`Damage.lua:1464-1504`; the file header still
    says 30).
  - `DamageToPlayer`: 8 stages (`Damage.lua:1970-1983`).
  - `Global/zzzzzMaw_Damage.lua` registers them from `Global/` so they run last among the mod's
    handlers, and re-registers them on every save load.
  - `Pipeline.lua` is a generic "ordered named stages" helper with `describe()`. **OpenYAMM should
    copy this concept directly:** stage order *is* the damage formula.
- **Formulas.** `Modules/MawCore/Formulas.lua` holds pure functions that both the effect code and
  the tooltips call (armour, resistance, crit, hit, regen).
- **Balance model.** `Modules/MawCore/Estimates.lua` rebuilds "the average character at level L"
  (stats, HP, AC, resistances, attack, DPS). Monster HP and damage are ratios of that model.
- **Monster ledger.** `MonsterHP.lua` keeps real monster HP above the engine's 16-bit cap.
- **Scheduler.** `Scheduler.lua` runs one `events.Tick` with named interval tasks; there are
  34 `every(...)` registrations. Separately, `General/zzMaw-Timers.lua` is a game-time
  accumulator driver ("MawTimer").
- **Engine boundary.** `Engine.lua` is the only core file allowed to use `mem.*`. Legacy files
  still patch freely: hooks at 0x425893, 0x4256DB, 0x4376AC, 0x4B30EF, 0x48CD4D, 0x4485EC and
  others (section 8.3).
- **MMMerge's own bolster is switched off.** `General/zzMaw-Monsters.lua:2134-2137` sets
  `Game.UseMonsterBolster=false` on every LoadMap. MAW replaces the whole AdaptiveMonstersStats
  system with its own level/HP/damage code. MAW's copy of `AdaptiveMonstersStats.lua` differs from
  MMMerge only in small ways (section 6.6).

---

## 1. Stat rework

### 1.1 Statistic effect ("1 effect every 5 points")

`General/zzMaw-Stats.lua:947-951`:

```lua
function events.GetStatisticEffect(t) if t.Value >= 25 then t.Result = math.floor(t.Value/5) end end
```

Below 25 the vanilla breakpoint table applies. From 25 up, the effect is linear: 500 → +100. This
"effect" is the vanilla channel: flat melee damage, attack, HP and SP factor, AC and so on.

### 1.2 Per-stat bonuses (exact code)

| Stat | Effect | Source |
|---|---|---|
| **Might** | Physical damage × (1 + Might/1000), i.e. +1% per 10, not level-scaled (`GetMightDamageMultiplier`). Applied to melee *and* bow. The flat part is the statistic effect. In real hits, `mightLevelSwap` swaps the "player level" term for the monster level, but the function ignores level, so the ratio is 1. | `zzMaw-Stats.lua:263-267`, `Damage.lua:432-437`, `zzMaw-Items.lua:3321-3355` |
| **Intellect / Personality** | Spell damage × (1 + max(Int, Per)/1000) (`CalcSpellDamage`). Spell crit damage uses **Intellect** only: Int/(dim·4) + 1.5. | `zzMaw-Spells.lua:2013-2017`, `Formulas.lua:177-183` |
| **Personality** | Healing × (1 + Per/min(1000+3·lvl, 4000)). Mana cost × 0.99^(Per/(10 + 0.06·min(totalLevel,1000))). SP pool adds 2× the statistic effect per class SP factor. | `zzMaw-Spells.lua:80-82, 2172-2179`, `zzMaw-Items.lua:3128-3141` |
| **Endurance** | HP × (1 + End/1000). The flat statistic effect is added to the level term of the class HP formula. | `zzMaw-Items.lua:3096-3126` |
| **Accuracy** | Melee/bow crit multiplier = Acc/dim + 1.5, with dim = min(250 + 2.5·L, 2000), or 3000 in madness. L is the monster level for weapon hits only; spell and enchant/aura crits, tooltips and the stats screen use `round(getTotalLevel())`. GM Axe adds +0.01×skill. | `Formulas.lua:165-183`, `zzMaw-Stats.lua:98-111` |
| **Speed** | Melee/ranged recovery: bonusSpeed += floor(Speed/10) (≤21: (Speed−13)/4). Spell haste: floor(Speed/20)% (`SPELL_HASTE_DIVISOR=20`). Chance to be hit (dodge) = 1/(1 + Speed/(100+estimateStat(L))·0.5). | `zzMAW-Skills.lua:408-423`, `zzMaw-Stats.lua:162-245`, `Formulas.lua:76-80` |
| **Luck** | Crit chance = Luck/min(500+5·L, 3000) + 5% (L as for Accuracy: monster level for weapon hits only). All six resistances += statistic effect of Luck (+1 per 5). | `Formulas.lua:169-171`, `zzMaw-Items.lua:3088-3094` |

Crit details (`getCritInfo`, `zzMaw-Stats.lua:61-142`):

- Dagger at Master or above adds +5% + 0.01·s/min(1+L/200, 4) crit chance, per hand.
- Fate/Hour-of-Power buff adds `GetBuffMultiplier(Fate)`.
- Map affixes 20 and 21 cut crit chance and crit damage.
- The 100% cap is lifted by legendary 14, which also adds +10%.
- Heals never crit (the "heal" type returns 0).

Bug: the Speed tooltip shows spell haste as floor(Speed/10) plus 20 for the haste enchant
(`zzMaw-Stats.lua:351-354`). The real code uses /20 and ×1.1 (`zzMaw-Stats.lua:171-175, 227`).
The README's "2% attack / 1% cast per 10 Speed" is stale.

### 1.3 Armour class → physical damage taken

From `Formulas.lua:58-63`:

```
taken = 1 / (AC / (200 + L) + 1)
```

L is the attacking monster's level. Physical damage then gets, in order (`calcMawDamage`,
`zzMaw-Stats.lua:1037-1158`):

- GM Shield ×0.85.
- Map affix 28 cuts AC.
- Class cuts:
  - Shaman: /(1 + 0.01·Air skill).
  - Death Knight: /(1 + 0.01·Body skill) for physical, Dark skill for magic.
- Special 36 "of Shielding" ×0.85 (physical only).

`applyPostMitigation` then applies:

- A **floor of 10% of the input damage** (`Formulas.damageFloor=0.1`), taken on the input before the GM Shield cut.
- Legendary 18 ×0.9.
- Legendary 22: 0.97^(monsters within 512), floored at 0.5.
- A flat Shaman (Water) / Seraph (Spirit) reduction, never below 25% of the hit, with `lvl = getTotalLevel()`:
  `round(getMonsterDamage(nil,lvl+1)·skill/estimateSkill(lvl)·avgTaken/2·0.99^estimateSkill(lvl))`.

Legendaries 18/22 and the flat cut run after the floor, so a hit can end below 10% of its input. Full spec:
[COMBAT_SPEC.md](COMBAT_SPEC.md) §2.4.

### 1.4 Resistances (player side)

Player resistances are **level-dependent and hyperbolic**. The README's 2^(res/100) formula is the
*monster* side (section 2.6). From `Formulas.lua:65-74`:

```
taken = 1/(res/(100 + L) + 1) × 1/(itemRes/100 + 1)
```

- `itemRes` is the "normal enchant resistance" from items, stored separately in
  `vars.normalEnchantResistance`. Legendary 16 multiplies it by 1.5.
- Ring resistance enchants are halved: `resistanceEnchantPower` = roll·100/200.
- The magic path also applies the Shield buff: ×max(1 − buffMult, 0.7) under the buff rework,
  otherwise ×0.85.
- GM Shield ×0.85 is applied **a second time** for magic (`zzMaw-Stats.lua:1045-1053` and again
  at `1086-1095`). That is 0.7225 total, very likely a bug.
- Map affix 29 cuts resistance.
- Resistance ≥ 65000 means immune. Lich gets Mind and Body immunity, Vampire gets Mind
  (`zzMaw-Stats.lua:1349-1383`).
- Racial resistances are +25+lvl:
  - Elves: the four elements.
  - Troll: Water and Earth.
  - Goblin: Air and Earth.
  - Dwarf: Mind and Earth.
  - Dragon: Fire +100+2·lvl.
- Randomisation (`rand=true`): res' = res + min(res, 1−res)·(U+U−1). It never happens: traps call
  `calcMawDamage` without `rand`, and the only `rand=true` call is in an unreachable branch. Traps are mitigated at
  the victim's own `LevelBase`.

Damage kinds map to resistances through `damageKindResistance` (`zzMaw-Stats.lua:977-988`):

| Damage kind | Resistance used |
|---|---|
| Fire | Fire |
| Air | Air |
| Water | Water |
| Earth | Earth |
| **Spirit (6) and Mind (7)** | Mind |
| Body | Body |
| **Light (9)** | worst of {Mind, Body} |
| **Dark (10)** | worst of {Fire, Air, Water, Earth} |
| **Energy (12)** | worst of all six |
| Kinds not in the table | no resistance, only the 10% floor |

The code keeps `max(taken)` but names the variable "best". Behaviourally it picks the lowest
resistance, as the tooltip says.

The stats screen shows "% damage taken vs same-level monster" with
`MawReferenceLevel()=round(getTotalLevel())`, which is the sum of banked levels on all continents,
not the character level (`zzMaw-Stats.lua:54-59, 868-897`).

### 1.5 Hit and dodge

**Player hits monster** (`Formulas.mawHitChance`, `Formulas.lua:112-122`; hook at 0x4256DB in
`General/zMaw-hooks.lua:176-196`):

```
overPar = (7.5 + atk)/(getPlayerEstimatedAttack(L) + 10) − 1
chance  = clamp(0.75 + overPar·0.5 + blessBonus, 0.25, 1.0)
```

- `blessBonus` runs from 0.05 to 0.10 with buff skill (cap `skillEffectCap.buff=50`).
- Monster AC is no longer used for hitting; its recalculation is vestigial.
- The stats screen shows "100% up to level X" by binary search (`hitCapLevel`).

**Monster hits player** (hook at 0x425893, `General/zzMaw_MonsterHit.lua`):

```
P(hit) = 1/(1 + Speed/(100 + estimateStat(L))·0.5)
```

The hook covers melee. For spell and missile hits (MonsterAction 2/3 or an object) the player pipeline
rolls Speed again, so Speed dodges elemental damage too.

GM Dodging adds dodge 1 − 1/(1 + (s+10)/200) on top, against every monster attack type. Dragons get none. A dodge
plays face expression 33.

---

## 2. Damage pipeline

### 2.1 DamageToMonster stage order (`Damage.lua:1464-1541`)

```
context → puppet-zero → remote-owner-zero → seraph-on-hit-heal → elementalist-learning →
elementalist-stack-reset → engine-reset (Result = raw t.Damage; engine maths discarded) →
reveal-nearby → monster-vs-monster → cover-flag → weapon-stun → stun-death-cleanup →
fly-removal → stun-spell-prime → mass-distortion → sparks-chain → weapon-recompute →
pain-reflection-flag → res-and-retaliation (÷2^(res/100)) → dragon-attack → shaman-on-hit →
dk-attack → assassin-attack → retaliation → boss-affixes → survival-gate → legendaries
(enchant/aura adds, post-res) → artifact-on-hit → damage-taken (leg. 29) → map-affixes →
friendly-fire-zero → leech → track-and-clamp (status msg) → monster-hp (ledger) →
final-clamp (ceil, ≤32500) → publish (MawMonsterDamage event)
```

`sparks-chain` is Chain Lightning: it fires for `Object.Spell == 18` (Lightning Bolt) and spawns a full-strength
copy with one mastery less (`Damage.lua:399-428`); it is not a Sparks effect. Full spec:
[COMBAT_SPEC.md](COMBAT_SPEC.md) §5.

### 2.2 Melee and ranged base hit (`stage_weaponRecompute`, `Damage.lua:444-499`)

```
dmg = round((U[min,max] + U[min,max])/2)          -- average of two rolls (triangular)
dmg × damageMultiplier[Melee|Ranged] × mightLevelSwap
crit:   × critMult   (getCritInfo with monster level)
Weak:   × 0.5
arrow (Object.Spell == 133) whose ammunition has special 3 "of Carnage": × 0.25
```

Blaster shots (`Hit.Spell == 135`) use the melee min/max and melee multiplier and are never resisted (Energy).

- `min` and `max` come from the engine's `GetMeleeDamageMin/Max` / `GetRangedDamageMin/Max`. MAW
  rewrites those through `itemStats` in `zzMaw-Items.lua`, which adds Might's statistic effect and
  multiplies by (1 + Might/1000) at `zzMaw-Items.lua:3321-3355`.
- Assassins subtract an "isolation" term.
- Unarmed is forced to 0 for two `GetSkill` calls after `PlayerAttacked` (`zzMaw-Stats.lua:1385-1394`).
  `PlayerAttacked` is a monster attacking the party, so this disables the engine's Unarmed-GM evasion; MAW zeroes
  all skill bonuses through `CalcStatBonusBySkills` anyway. This is a hack.

### 2.3 Attack speed, recovery and the damage multiplier

From `events.GetAttackDelay`, `zzMAW-Skills.lua:440-616`.

**Weapon base recovery.** `baseRecovery[skill] × (0.75 + itemLevel/500)`, rounded to tens. The
item level is capped at 600; two-handed weapons get ×1.25 (`getItemRecovery`,
`zzMAW-Skills.lua:425-438`). Base values:

| Weapon | Base recovery |
|---|---|
| Bow | 100 |
| Blaster | 40 |
| Staff | 120 |
| Axe | 140 |
| Sword | 80 |
| Spear | 120 |
| Mace | 100 |
| Dagger | 60 |

Higher-level weapons are therefore slower.

**Dual wield.** The base is the average of the two hands. A skill's speed bonus is paid only once.

**bonusSpeed** (percentage points) is the sum of:

- `skillRecovery[skill][m]·s`.
- Armsmaster `s·Speed[m]`.
- Class terms: Death Knight + Water s, Seraph + Light s·m/2, Assassin stacks.
- Speed statistic: floor(Speed/10).
- Haste (+20) only when the buff rework is off. That branch is dead (`not x == "ON"` is always false).

**Multiplicative assembly:**

```
totalSpeed = 1/(1+bonusSpeed/100) / swiftness × (1 + armourImpair/100) / hasteMult
Result     = round(baseSpeed × totalSpeed)
```

- `swiftness` = 1 + 0.3 for a two-handed weapon with enchant 41/59, +0.15 one-handed.
- `armourImpair` comes from `weaponImpair` for the body armour and shield masteries
  (`zzMAW-Skills.lua:37-42`):

  | Armour | Novice / Expert / Master / GM |
  |---|---|
  | Leather | 10 / 0 / 0 / 0 |
  | Chain | 20 / 10 / 0 / 0 |
  | Plate | 20 / 10 / 10 / 0 |
  | Shield | 10 / 0 / 0 / 0 |

- `hasteMult` = 1 + GetBuffMultiplier(Haste).

**The engine floor of 30 recovery** is patched to 1 (`Modules/MawCore/Fixes.lua:29-35`, address 0x42DA51+1).

**The key trick (`zzMAW-Skills.lua:600-611`).** The function stores
`damageMultiplier[idx].Melee = Result / round(100·totalSpeed) ≈ baseSpeed/100`, and every melee or
ranged hit is multiplied by that factor. So slow weapons hit proportionally harder, and DPS
depends only on bonus speed, not on weapon base speed. This is the README's "damage multiplied by
attack speed".

**Spell delay** (`getSpellDelay`, `zzMaw-Stats.lua:162-245`):

```
delay = round(base/(1 + floor(Speed/20)/100) × 1.015^ascension / hasteDiv / (1.1 if spell-haste enchant)) × armourImpair
```

- Elementalists ×1.5 and /(1+0.05·stacks).
- Control spells use their own curve: base × 1.015^(ascension − school skill).
- No school mastery means delay 150.
- Map affix 27 slows casting.
- `events.PlayerCastSpell` writes the result into `Game.Spells[..].Delay*` before each cast
  (global table mutation).

### 2.4 Weapon enchant damage and how it flows into spells

**Range.** Damage enchants (`enchantbonusdamage`, `zzMaw-Items.lua:~2040-2061`, ids 4-15, 39, 46)
roll a range centred on `levelDamage × Coeff × ENCHANT_DAMAGE_MULT(1)`:

- `levelDamage = getWeaponLevelDamage(itemLevel)`.
- There is a floor of {min,max}·0.5, ×2 for two-handed weapons (`enchantDamageRange`, `:2066-2081`).

**Applied damage** (`calcEnchantDamage`, `:2125-2155`):

```
damage = R(round(lo), round(hi)) × legendary19 (×1.5) × [leg. 26: crit] × GetPlayerBaseRecovery/100 ÷ 2^(res/100)
```

Legendary 19 multiplies before the recovery factor. The enchant result is not rounded; the aura result is. The
element's resistance is applied separately from the physical part. Enchant 39 is spell-only and enchant 46 is
weapon-only.

**Fire Aura buff** (spell 4 only; `calcFireAuraDamage`, `:4287-4318`). "Vampiric" auras are leech, not damage.

- `GetWeaponLevelDamage × {0.10, 0.15, 0.20, 0.25}[mastery]`, minimum {3,6,12,24} (×2 for
  two-handed).
- × item base recovery/100, ÷ 2^(fireRes/100).

**Melee path** (`stage_legendaries`, `Damage.lua:973-1019`): adds the aura and enchant damage of
both hands *after* the physical resistance division. The added part is tracked in
`t.ElementalDamage` for "magical leech". Bow and blaster add the bow-slot enchant and aura (for blaster shots
both come from the bow-slot item, not the blaster). The aura on a bow takes the max, not the sum.

**Spell path** (`events.CalcSpellDamage`, `zzMaw-Spells.lua:1937-2040`):

- Base: `dmgAdd + Σ_{skill} U[diceMin,diceMax]`.
- Ascension scaling (`Formulas.spellDiceScale/spellAddScale`):
  `(1+0.02s)·1.02^s` on dice and `(1+0.01s²)·1.02^s` on the add.
- × (1 + max(Int,Per)/1000) × crit.
- **Plus, for every equipped slot 0..2 (main hand, off hand, bow):** `calcEnchantDamage` +
  `calcFireAuraDamage` with isSpell, × 1.015^ascension, **÷ 2.5 for AoE spells** (= the README's
  "40%"). This share is added before stage 19 with resistance 0, so it is resisted by the spell's element, not
  the enchant's.
- The README says "main hand only"; the code loops over three slots.
- Dragons, classes 10/11 and Death Knights return before scaling.
- Mass Distortion (44) is HP-based: 0.15·HP + 0.005·skill·HP of the proxy HP. It is rescaled in
  the pipeline by `/mult^0.5·max(1,(L/250)²)` and by the ledger scale.

Class overrides (dragon, Death Knight spell-melee, assassin spells) re-roll melee damage and add
both hands' enchants again (`Damage.lua:597-870`).

### 2.5 Dual wield

"Benefit fully from both weapons" works like this:

- The engine's MeleeDamageMin/Max already sum both hands.
- MAW averages base recovery instead of using the slower hand.
- Both hands' enchants and auras are added. Each enchant is scaled by the average base recovery of both hands
  (`GetPlayerBaseRecovery`); each aura by its own item's recovery.
- Armsmaster damage is halved on both hands when an off-hand weapon is held.
- Dagger crit chance is per hand.
- The Axe GM crit bonus is applied once.
- Minotaurs can dual-wield axes (race file, out of scope).

### 2.6 Monster resistances (player → monster)

`resDivide(dmg, res) = dmg / 2^((res % 1000)/100)` (`Damage.lua:39-41`) is deterministic, not a
vanilla immunity roll.

- `res % 1000`, because Fire resistance historically carried an HP multiplier in the thousands,
  and the Stun spell parks 65000 there for one tick.
- Index mapping is `damageKindMap` (`zzMaw-Stats.lua:922-933`): monster columns 0 Fire, 1 Air,
  2 Water, 3 Earth, 4 Phys, 6 Spirit, 7 Mind, 8 Body, 9 Light, 10 Dark. **Energy (12) has no
  column, so monsters do not resist energy.**
- GM Bow uses min(Fire, Phys) resistance. Dragon breath uses the minimum of all columns.
- **Cap:** every resistance is `min(base + affix12, base_affix + 200, 999)`
  (`zzMaw-Monsters.lua:600-605, 108-125`). 200 equals ÷4 at most, so there are no immunities.
- Monster versus monster: attacker `getMonsterDamage/3`, divided by the target's physical
  resistance in stage 9 and again by the damage kind's resistance in stage 19.

Additive multipliers after resistance:

- Spear GM stacks: +(2 + 0.02·s)·weaponSpeedMult % physical taken per hit, ×1.5 two-handed,
  reset on death. The stacks amplify every physical hit on that monster by anyone, including the hit that adds
  the stack.
- Legendary 29: +1% all damage taken per hit.

### 2.7 Crits

- Chance: Luck/min(500+5L, 3000) + 0.05, plus dagger and Fate.
- Multiplier: stat/dim + 1.5, with dim = min(250+2.5L, 2000|3000). Spells use dim·4.
- L is the monster level only for weapon hits. Spell crits (`CalcSpellDamage`), enchant/aura crits (legendary 26),
  all tooltips and the stats screen use `round(TL)`, the party's total banked level. Full spec:
  [COMBAT_SPEC.md](COMBAT_SPEC.md) §2.2.
- The cap of 1 is removed by legendary 14, which also multiplies total damage by max(crit, 1).
- Crit text: the engine's attack/shoot/kill message strings are swapped by a hook at 0x4376AC
  (`zzMaw-Stats.lua:954-974`). The pipeline's status line then appends "(CRIT!)".

### 2.8 Leech (`stage_leech`, `Damage.lua:1207-1326`)

Leech is measured in **health bars**, not damage:

```
heal = min(dealt, monsterMaxHP)/HPtable[B-variant] × playerMaxHP × leech%
```

- The physical part uses melee or ranged leech%; the elemental part uses the spell leech%.
- Per-attack floor: `fullHP·leech/5·recovery/100`. AoE spells /2.5; spells 9, 22 and 43 /4.
- Life Drain (200/201) heals 10%.
- Legendary 31 converts half of it to mana. Legendary 27 sends overheal to the lowest party
  member.
- Only damage the monster could absorb counts, so overkill does not leech.
- Missing from this list: Death Coil (+20 % of the bar, ×1.5 at Dark Master), dragon regen leech, the full leech
  table, the minimum leech using the current attack/spell delay, map affix 32 and legendary 31's conversion. Full
  spec: [COMBAT_SPEC.md](COMBAT_SPEC.md) §3.7 and §8.1.

### 2.9 DamageToPlayer (`Damage.lua:1583-1800`)

Stages: remote-owner-zero, item-refresh, death-seed-mark, damage-recompute, boss-affixes-player,
survival-gate, map-affixes-player, legendaries-and-shields.

**Order inside `damage-recompute`:**

1. Reflected damage: return Result^0.85.
2. Pain Reflection: Result^0.85.

   In both cases `Result` is the engine's own (vanilla) result for that damage kind, with no MAW mitigation; mana
   shield and the death thresholds still apply.
3. **Player spells hitting players** (friendly fire) are recomputed from ascension dice with
   distance falloff (1 − d/512) and no crit.
4. **No monster attacker** (traps, objects, falls indoors): `getMonsterDamage(nil, totalLevel)`,
   /3 for spell-type 15 objects, × min((11 − 2·PerceptionMastery)/10, 1). Perception therefore
   cuts trap damage to ×0.9 / 0.7 / 0.5 / 0.3.
5. Dodge (GM Dodging) or the Speed roll for spells and missiles: Result = 0.
6. **Monster damage:**
   - `getMonsterDamage(mon)`.
   - Attack 2: × (avg dice of Attack 2)/(avg dice of Attack 1), and its damage type is used.
   - Monster spells: `monsterSpellMultiplierList[spell]` (`zzMaw-Monsters.lua:1937-1963`), for
     example Fire Bolt 0.75, Incinerate 1.35, Meteor 0.3, Psychic Shock 1.25, Mass Distortion 0.4.
     **Ice Blast is listed twice (1.2, then 0.75); the last entry wins.**
   - Map affix 14 changes the type to energy, always: the roll compares U with a power ≥ 20.
   - Monster spells with id ≥ 100 and action-2/3 hits without a projectile keep the engine's vanilla damage.
   - Roll × (U(75,125) + U(75,125))/200.
   - Monster debuffs: Dark Grasp/DamageHalved ×0.7, Shrinking Ray ×0.7, the minimum of the two.
   - `calcMawDamage` with the monster level.
7. Solo Cover ×0.5.
8. **Disease amplifies damage:** D1 ×1.25, D2 ×1.5, D3 ×2. The effect is halved for a solo
   party.
9. Exploding boss (check `NameId > 220`, strict): the hit is halved, then `Result/PartyCount` is applied to every
   member including the target, directly to HP after the mana shield, outside the pipeline (no mitigation, no
   cheat-death).

**Order after `damage-recompute`:**

1. Boss on-hit affixes (section 3.5).
2. Map affixes 1/2/10:
   - +X% damage.
   - X% chance of a double "crit".
   - +X% of the player's max HP.
3. Mana shield, legendary 15 and Seraph Divine Protection (cheat death, 150 game minutes = 5 real minutes
   cooldown). Legendary 15 sets HP to a quarter and cancels the hit; Divine Protection heals 25 % and leaves the
   target at 1 HP at worst.
4. **Bolster ≥ 300 (Nightmare and above) death thresholds:**
   - HP < −fullHP: Dead (SP=0).
   - HP < −2·fullHP: Eradicated.
   - Insanity with `enableDisintegrate`, HP < −10·fullHP and party > 1: **the character is
     dismissed permanently ("Disintegrated")** (`Damage.lua:1907-1934`).

Mist Form: the engine's rule is bypassed by zeroing the buff for one tick in `PlayerAttacked`, and
the pipeline applies ×0.25 to physical damage (`zzMaw-Stats.lua:690-717`). This is a hack.

### 2.10 Homing projectiles (`zzMAW-Skills.lua:618-744`, task `skills/homing-projectiles`, every frame)

- Toggled by `vars.MAWSETTINGS.homingProjectiles` (default ON, in the MAW SETTINGS page).
- **Player missiles that have a monster target** are re-aimed every frame straight at the target:
  speed is kept and the aim point is Z + 0.75·BodyHeight. This is perfect homing.
- Excluded: Meteor Shower, Sparks, Starburst, Poison Spray, Ice Blast and Shrapmetal, plus remote
  players' objects.
- **Monster missiles** (owner kind Monster or 2) are re-aimed at the party (Z + 120) only while
  the horizontal angle between their velocity and the direction to the party is below **0.5°**.
- Strafing slowly keeps the lock; sprinting sideways breaks it, and once broken it never
  re-acquires.
- The angle ignores Z, so flying up or down does not help.
- Tested once a rendered frame, so the lock grows with the frame rate. OpenYAMM uses a frame-rate independent
  rate instead, 300° a second, firm enough to hit a party strafing in flight (DEVIATIONS.md #181).
- Cosmetic projectiles without a target (obelisk, lava fireballs) get pulled toward the party.
  This is a known issue noted in a code comment.

### 2.11 Power and Vitality (shown on the character screen)

`calcPowerVitality(pl)`, `zzMaw-Stats.lua:1189-1346`. The reference level is `MawReferenceLevel`,
the sum of all banked levels.

**Melee (M):**

```
DPS1 = (avg·(1 + min(cc,1)·(cm−1)) + enchants_2hands)/(delay/60) × hitChance × damageMultiplier.Melee × max(cc,1)
```

`enchants` = enchant + aura + artifact on-hit, all "power" averages.

**Ranged (R):** the same, with bow ×2 at Master (two arrows).

**Spell (S):** only when the quick spell or attack spell is a damage or heal spell.

```
power = add + skill·(diceMin+diceMax)/2
```

- Life Drain ×5/3 at Master, ×7/3 at GM.
- × (1 + Int/1000), or the Personality heal curve for heals.
- × crit, + enchants × 1.02^ascension, ÷2.5 for AoE.
- ÷ (getSpellDelay/60) × max(cc, 1).
- Counted as a single hit or single target, as the README says.

**Vitality (V):**

```
fullHP' = (GetMaxHP + manaShieldSP·efficiency) / dodgeFactor
taken   = [ (1−acRed)·0.5 + Σ_{6 elems}(1−res)·(0.5/8) + (1−energyRes)·(0.5/8)·2 ] × chanceToBeHit
V       = fullHP'/taken
```

- `dodgeFactor` = 1/(1 + (GMdodge+10)/200).
- Physical counts for 50% and magic for 50%: six elements plus energy counted twice, over 8 parts.

**Display:**

- The stats screen rewrites engine label strings: `GlobalTxt[47]` "Condition" becomes
  `M/R/S:x/y/z` and `GlobalTxt[172]` "Quick Spell" becomes `Vitality: v`.
- The resistance labels (`GlobalTxt[87,6,240,70,142,29]`) become "% taken vs reference level +
  raw value, green if enchant-boosted". They are restored when leaving the screen.
- A 250 ms scheduler task, poked on change, keeps the labels updated (`zzMaw-Stats.lua:791-908,
  1161-1180`).
- Right-clicking the Power label (stat id 5234672) shows the Melee/Ranged/Spell Power breakdown
  and the leech percentages.

**Estimates.lua** is the model behind monster sizing, not the displayed Power. Functions:

- `getPlayerEstimatedPower(L)`: expected melee damage per standard swing, including speed and haste
  multipliers.
- `getPlayerEstimatedVitality(L)`: expected effective HP including Cover.
- `getPlayerEstimatedAttack(L)`, `getPlayerEstimatedSpellPower(L)`,
  `getPlayerEstimatedHealing(L)`.

They are built from `estimateStat(L) = (17 + 0.2·min(L,500) + totalEnchantPower(L)·0.25·gearedFraction(L))·DayOfTheGods`,
`estimateSkill(L)` (skill points per level spread over 5 skills), weapon, armour and resistance
models and legendary ramps (L100→420). See `Estimates.lua:93-600`. These depend on many tables
from other files (`GetMaxEnchantStrength`, `GetLootTier`, `GetExpectedEnchantFraction`,
`GetPrimordialCharges`, `GetBuffStatPct`, `buffPower`, `skillItemAC/Res`, `armsmasterSkill`,
`skillDamage/Recovery/Attack`, `bodybuildingHP`, `fireAuraDamage`, `enchantbonusdamage`,
`MawCore.ItemLevel`). Porting monster stats therefore needs the item and skill rulesets ported
first, or a precomputed table.

---

## 3. Monsters

### 3.1 HP and damage: the model is relative to the expected player

From `Estimates.lua:458-495, 678-726`:

```
getMonsterHealth(mon) = getPlayerEstimatedPower(Lb) × hitToKillMonster[diff] × clamp(FullHP_tier/FullHP_B, 0.6, 1.8) × boss.HealthMult
getMonsterDamage(mon) = getPlayerEstimatedVitality(Lb) / hitToKill[diff] × {A:0.66, B:1, C:1.5} × boss.DamageMult
```

- `Lb = totalLevel[B variant of the family]`. **HP and damage always use the B-tier level.**
- The A and C differences come from base-table HP ratios and the 0.66/1.5 factors.
- Bosses' own higher level is used only for display, resistance, crit and AC maths.

The hits-to-kill tables, indexed by `GetDifficulty()`:

| diff | Name | Bolster | `hitToKillMonster` (HP = n player-swings) | `hitToKill` (player dies in n hits) | Austerity HP / dmg |
|---|---|---|---|---|---|
| 1 | Easy **and Normal** (bug, see section 4) | 0, 50 | 1 | 14 | 1 / 15 |
| 2 | (bolster 70, unreachable) | – | 1.5 | 10 | 2 / 10 |
| 3 | MAW | 100 | 2 | 7 | 4 / 5 |
| 4 | Hard | 150 | 2.5 | 6.5 | 5 / 4 |
| 5 | Hell | 200 | 3 | 6 | 6 / 3 |
| 6 | Nightmare | 300 | 3.5 | 5.5 | 7 / 2.5 |
| 7 | Doom (Mode 2) | 600 | 4 | 5 | 8 / 2 |
| 8 | Road to Insanity | 600 | 4.5 | 4.5 | 9 / 1.5 |
| 9 | Beyond Madness | 600 | 5 | 4 | 9.5 / 1 |

Relative to MAW: Easy/Normal ×0.5 HP and ×0.5 damage; Hard ×1.25/×1.08; Hell ×1.5/×1.17;
Nightmare ×1.75/×1.27; Doom ×2/×1.4; Insanity ×2.25/×1.56; Madness ×2.5/×1.75. These are the hit-table ratios
only; the actual monster ratios also move with the difficulty-dependent expected character, e.g. Hell 1.63/1.26
and Beyond Madness 4.14/2.50 at level 300 ([BALANCE_MODEL.md](BALANCE_MODEL.md) §9.2).

"Player swing" means `getPlayerEstimatedPower`, which includes attack speed, crit overflow, enchants and hit
chance: damage per base-recovery attack, closer to DPS than to damage per swing. Full spec:
[BALANCE_MODEL.md](BALANCE_MODEL.md) §3.10 and §6.

**Old curve (README numbers, now commented out).** `zzMaw-Monsters.lua:4160-4202`:

```
damage = (3 + L^0.88)·(1.15 + L/9)·(1 + L/400)·diffMult
```

At L100 that is about 60·15.3, which is where "×12 at L100" came from. The current model
reproduces the intent, keeping pace with player HP and defences, without fixed multipliers.

**HP above 32000.** The engine HP field is 16-bit. Templates get min(HP, 32000), rounded to tens
above 1000. Real HP lives in `mapvars.MawMonsterHP[index] = {max, hp, proxy}`; the pipeline
converts real damage into proxy damage that keeps the bar percentage, and kills by sending 32500
(`MonsterHP.lua`). Per-hit damage is capped at 32500 (`stage_finalClamp`).

**Spawn path.** `recalculateMonsterTable()` rewrites all 651 `Game.MonstersTxt` entries **on
every map load** (`zzMaw-Monsters.lua:416-665`): level, resistances, HP table, Experience and
AC = base·(L+10)/(LB+10). Then `recalculateMawMonster()` re-syncs every live map monster (HP,
attacks, level and resistances from the template, unique-monster levels and bosses). It reruns
when `Map.Monsters.High` changes, which is polled in `events.Action` and in the monster tooltip.

### 3.2 Monster levels (bolster and horizontal), from `recalculateMonsterTable`

**Shared definitions:**

- `bolsterLevel = getPartyLevel() − 4`, where `getPartyLevel` is the sum of the levels banked on
  *other* continents.
- Austerity: `^1.015`.
- Plus 20 per reset of this dungeon (`vars.mapResetCount`).
- Dimension map: = Power·10 + 20.
- Madness (non-starting map): fixed map level.

**Map-native adjustment** (`mapLevels[name] = {Low, Mid, High}`, 208 entries with 193 distinct names covering
all 207 mapstats rows; two duplicates overwrite real values; `zzMaw-Monsters.lua:963-1592`; madness progression
tables at `:1594-1811`). Full spec: [BALANCE_MODEL.md](BALANCE_MODEL.md) §7.

- The 1–3 monster families named in MapStats are sorted by B level and pinned to Low/Mid/High
  (`extraBolster = mp.X − LevelB`). `adjust = (mean − mp.X)·1.5`, or 1 in madness, compresses them
  toward the mean (horizontal and arena only).
- Non-native monsters move halfway toward the [Low, High] band.

**Free progression** ("monster bolster ON"):

```
totalLevel = bolsteredLevel(bolsterLevel, base.Level + extraBolster)
```

`bolsteredLevel(floor, n)` (`zzMaw-Monsters.lua:5-13`) adds the *vanilla* experience between
`floor` and `floor+n` (500·L·(L−1)) on top of the *MAW* curve at `floor`. Because MAW's curve is
steeper above level 100, a monster of base level 30 on top of a bolster of 200 gains fewer than
30 levels.

**Horizontal progression** ("monster bolster OFF", `Game.freeProgression==false`):

- Starter maps (`horizontalMaps`: Dagger Wound, Abandoned Temple, Emerald Island, Temple of the
  Moon, Dragon's Lair, Castle Harmondale, New Sorpigal, Goblinwatch):
  `min((base+extra)·2.5, bolsteredLevel(bolster+bonus, base+extra))`.
- All other maps:
  `max(2.5·base + 2.5·extra − 5 − 1.5·(base−LevelB) + adjust − 4 + bonus, 5)`.
  The flattener 0.6·2.5 shrinks the A/B/C spread.
- So monsters everywhere are about **2.5× their vanilla level**, independent of the party, which
  is why "monsters scale up to 250+".

**Other modes:**

- **Madness:** fixed per-map level `500·(position/campaignLength)^1.2` along each game's map
  progression (MM6 54, MM7 52, MM8 58 steps). The Breach is 1100. Within-map spread is ±2× the
  Low/Mid/High offsets and ±2× the tier offset, via `bolsteredLevel`. Non-native families use `Xslot = 0`, i.e. an
  offset of −2 × mean, and land far below the map level.
- **Arena (d42):** `6·base − 4.8·(base−LevelB) + 2·adjust`, plus `600 + 3.5·overflow` beyond the
  table.
- **Bounty:** `base + mapvars.mawBounty`.

**Unique monsters** (NameId 1..219), stored once per map in `mapvars.oldUniqueMonsterTable`:

- Free progression: `bolsteredLevel(partyLvl, oldLevel)`, where `partyLvl` has no −4. Horizontal starter maps also
  use this.
- Horizontal, non-starter map: `oldLevel·2.5`.
- Madness: `M + 2·(High − Mid)` on maps with a fixed level M, else `3 × oldLevel`.
- Uniques' HP and damage still come from the family's B level.

Level is capped at 255 in the engine field, while `totalLevel[]` and `uniqueMonsterLevel[]` hold
the real value. `getMonsterLevel(mon)` (`zzMaw-Monsters.lua:1884-1895`) is the accessor every
formula uses.

### 3.3 Speed, ranged attacks and AI

- **Melee speed-up.** For monsters with Velocity > 150 and no Attack-1 missile, hostile on load
  or once neutral monsters join combat, `v' = v/2 + 300`: 200→400, 300→450, 400→500
  (`zzMaw-Monsters.lua:81-152`). Spawned adds get Velocity 350.
- **Extra ranged attack.** Outdoors, not on starting maps, at bolster ≥ 200 (Hell+) or in bounty
  maps: pure-melee non-flying monsters get Attack2 as a missile with chance 10/20/30% for A/B/C.
  The damage is a weaker copy of Attack1 (`:632-658`).
- Every monster's AIType is reset to 0 (aggressive) except type 1 (`:229-231, 3655-3661`).
- The Steal bonus (20) becomes 17 (`:50-56`).
- Diseases below level 20 become poisons (`:3741-3747`).
- Doom: each monster with chance √L·2% gains a random on-hit condition that unlocks by level
  (poison/weak/fear → curse, disease, paralysis, insanity, stone, sleep/unconscious, ageing, SP
  drain, death, eradication; `:3691-3740`).
- Turn-based movement in Doom and Austerity is limited to 370 units per phase (`:3664-3679`).
- Stuck-monster helpers:
  - `nudgeMonsterAroundCorner` (`MonstersProcessed`, indoor, within 350) probes `RoomFromPoint`
    along the line and side-steps.
  - `checkOutOfBound` every 2 s.
  - Some sprites are shrunk to 0.75 (behemoth, minotaur, MM6 demons).
- MM6 projectile restore (`mawTick_RestoreProjectiles`) swaps monster missile object types every
  frame, and drives those hits itself through `PlayerAttacked` (random target, Cover and
  Retaliation, then `DoDamage(10000)` recomputed by the pipeline) (`:3807-4008`). Its Cover loop skips the last
  party member and never fires for a solo character.

### 3.4 Resistance caps, removed or reduced abilities

- Resistance cap at 200 (section 2.6). No immunities on the monster side.
- **Dispel.** No script or table reduces monster Dispel Magic: MAW's MONSTERS.txt (extracted from
  `Data/zMaw.T.lod`) has the same six Dispel casters as base. The effective change comes from the
  **buff rework**. Party buffs are mana-reserved "auras" in `vars.mawbuff`, and `mawBuffApply`
  (`zzMaw-Spells.lua:2863`) rewrites them every 0.5 s, so an engine dispel is undone within half a
  second.
- MAW's `MONSTERS.txt` overrides 173 EXP values, 107 damage values, 95 HP values, 92 levels and
  80 treasure values compared with base mmerge. Most are MM6 families: Magyar L14→40,
  Ghast/Ghoul +4, the Regnan casters' attack types become elemental, Ghoul paralyse becomes
  Disease2, and so on. The MapStats table is also overridden in that LOD.

### 3.5 Bosses ("elites"), from `zzMaw-Monsters.lua:2866-3110`

**Spawning:**

- Active at **BolsterAmount ≥ 100 (MAW and above), on every map**, generated by the host.
- Count = ceil((monsterCount − 30)/150), or /60 in Doom. Map affix 16 adds more; affix 19 turns
  some monsters into bosses; affix 17 promotes tiers.
- Candidates are C-tier (id%3==0) non-peaceful generic monsters.
- NameId is 221..299, and the name is "<Affix> <monster name>" in `Game.PlaceMonTxt`. **The affix
  is parsed back from the first word of the name everywhere.**

**Stats:**

- Level = `MawBossLevel` = C level + (C − B).
- HP mult = `2.5·(1 + L/255)·U(1,1.5)`, with L the engine level capped at 255, so at most 7.5. Austerity
  flattens both terms by 4.
- Damage mult = U(1.2, 1.4). Spell skill × damage mult.
- Treasure: gold dice √(100L) d √(100L), 100% item drop, item level +1, random item type.
- Sprite scale ×1.4 indoors and ×2 outdoors; Omnipotent is scaled up further.

**Affixes** (`SkillList`) and their effects:

| Affix | Effect |
|---|---|
| Summoner | On hitting a player (40%, or always on melee) spawns an add halfway between (tier A 75 %, B 25 %) |
| Venomous | Poison3 on hit |
| Plagueborn | Disease3 on hit |
| Fixator | Targets the lowest-max-HP member, ignores Cover, Weak on hit |
| Exploding | Halves the hit and applies half/PartyCount to every member (section 2.9) |
| Thorn | Reflects any physical hit (arrows included)^0.85 to the attacker |
| Reflecting | Reflects non-melee damage^0.85 (dragon damage becomes energy) |
| Adamantite | Damage − 4·L^1.15 with L = `mon.Level` (≤ 255), rounded, minimum ¼ |
| Swapper | Swaps positions with the party on hit. When hit, **negates every player hit** while any other active hostile non-boss monster exists, swapping through all of them in turn |
| Regenerating | +1%·0.99^hits FullHP/(1+L/50) every 0.1 s |
| Puller | `evt.Jump` pulls the party toward it |
| Leecher | Within 1500, drains 5% max HP (not below 1) and 5% current SP per 0.5 s, × ((1500−d)/1500)², ×4 in turn-based |
| Swift | Doubles its per-frame displacement, which is position teleporting |
| Shadow | Cancels Wizard Eye within 2000 |

Boss on-hit conditions bypass condition immunities. Full spec: [COMBAT_SPEC.md](COMBAT_SPEC.md) §6.12 and §7.5.

**Special bosses:**

- **Broodlord**: 1%·chanceMult. HP ×1.5, damage 1.5–1.8. On death spawns 3 "Broodling" bosses
  one tier down.
- **Omnipotent**: 0.1%·chanceMult. All affixes, HP ×4, damage 2–2.5. On death spawns one boss of
  every affix plus 3 Broodlings.
- chanceMult: Doom 2, Insanity 3.
- Only Beyond Madness uses **seeded** affix rolls (LCG on `vars.MawBossSeed + map hash +
  bossCounter`) and **pity counters** for Broodlord and Omnipotent (`:3115-3235`): the seed needs `insanityMode`
  and the branch also needs `madnessMode` (`:3030`). Road to Insanity rolls unseeded with chanceMult 3. The seeded
  Broodlord is HP ×2 and damage ×1.5 on top of the U(1.2, 1.4) roll; the seeded Omnipotent is HP ×4 and damage ×2
  on top of it (the HP/damage values above are the unseeded path).

**Multiplayer:** `General/zzBossSync.lua` keeps the boss table (names, set, data) on the host and
pushes snapshots in bursts to clients, which purge stale marks. It also has an F9 debug dump
(Shift slow, Alt to a file, Ctrl auto). There are no gameplay rules in it.

### 3.6 Density (`AdjustMonsterDensity`, `zzMaw-Monsters.lua:770-926`)

`Game.MapStats[i].Mon{1..3}{Low,Hi,Dif}` is rewritten in BeforeLoadMap from a backup.

`monsterDensity[diff] = {Low, Hi}`; the spread applied is (Low, Hi − 3):

| Difficulty | Low | Hi | Notes |
|---|---|---|---|
| 1–3 (Easy, Normal, MAW) | 1 | 3 | vanilla |
| 4 Hard | 1 | 4 | +1 Hi when Hi ≤ 3 |
| 5 Hell | 1 | 4 | +1 Hi when Hi ≤ 3 |
| 6 Nightmare | 2 | 4 | Low ≥ 2, Hi +1, Dif +1 (more C-tier) |
| 7 Doom | 2 | 5 | Low ≥ 2, Hi +2, Dif +1 |
| 8 Insanity | 3 | 5 | Doom block (Insanity is also `Mode 2`: Hi +2, Dif +1), then Low ≥ 3 |
| 9 Madness | 3 | 6 | Doom block (Dif +1), then Low ≥ 3, Hi +3 |

The Hard/Hell "Hi ≤ 3" test reads the current value, not the backup. The Randomizer uses a different, older
table. Full spec: [BALANCE_MODEL.md](BALANCE_MODEL.md) §10.2.

Kill experience is scaled down to compensate:

```
GetMonsterExpMult = sqrt(densityMean(MAW)/densityMean(diff))
```

A non-multiple-of-50 BolsterAmount is forced to 100. Dimension maps multiply Hi by
1 + (Power·nAff + 20·nAff)/300.

### 3.7 `pseudoSpawnpoint` (`General/pseudoSpawnpoint.lua`)

A utility, not a density mechanic.

- `pseudoSpawnpoint{monster, x, y, z, count ("a-b" | {a,b} | n), powerChances {A%,B%,C%}, radius, group, transform}`.
- Picks a random point in the radius; indoors it must be inside a room (with a "dead a unit below
  floor" fix).
- Rolls the tier, calls `SummonMonster(classId·3−2+tier)` and applies `transform`.
- Gives up 20 below the monster limit. Errors out after 20 failed placements.
- With `vars.seed` (seeded modes) it reseeds the RNG from spawn parameters and map name.

Used by bosses (Summoner, Broodlord, Omnipotent), the arena, bounty, survival, alchemy, a spell,
and MAW map scripts (`Maps/7out01.lua` 20 calls, `7out05` 18, `7out02` 9, `7d21`, `7d24`, `7d29`,
`7d06`, `7d37`): extra hand-placed packs on MM7 maps.

### 3.8 Respawn on exit and map completion

**Respawn on exit** (`zzMaw-Monsters.lua:2206-2263`). At Nightmare (300), Doom, Insanity and
Madness (600), indoors only:

- On first LoadMap every generic monster's spawn record is saved.
- On LeaveMap, if `mapvars.monsterMap.cleared == false`, every dead or removed generic monster
  (not bosses, not puppets) is revived at its spawn: full HP, `NameId = Id + 300` (shown as
  "Resurrected <name>"), Exp/4, hidden from the map. Removed corpses lose gold and items.
- `cleared` becomes true when ≥ 65% are dead at bolster ≥ 300, with the message "Monsters are
  weakened and can no longer resurrect" (`:2785-2794`).
- Insanity: resurrected monsters give 0 exp and no loot.

**Completion** (`checkMapCompletition`, `:2568-2796`, on every kill and every 10 s):

- Required ratio = 0.99^floor(n/100). Hidden or friendly monsters are excluded.
- On-screen percentage at (500, 377): red while respawn is armed, yellow once safe or outdoors,
  green when complete.
- First completion awards:
  - `exp = ceil(m^0.7·(C·20 + C^1.8)/3/1000)·1000` (8967ae88), where C is the level of the map's monsters (the
    middle of its own B rows, else the average level of its hostile monsters) and m is the kill count ×0.67 in
    Nightmare, ×0.5 at 600, ×0.8 in Insanity. Without monster levels, and on a dimension run,
    `exp = ceil(m^0.7·(L·20 + L^1.8)/3·(bolster+L)/L/1000)·1000` with L the map mean level clamped to 1..100 and
    bolster the run's power ×10 (the horizontal-mode bolster = 2L is gone). Madness has its own formula.
  - Gold = ceil(exp^0.9/1000)·1000.
  - Items 1070 (crafting) and 2 gems of tier min(ceil(C/25+0.5), 16), else min(ceil((L+bolster)/25+0.5), 16). Dimension maps give a reward by
    affix count only in Madness; elsewhere a completed dimension map gives a new map item (when the quest is
    done) and no crafting item.
  - `addBolsterExp(exp)`; each member gets `round(exp·5/PartyCount/1000)·1000`.
- Completed dungeons can be **reset** (yes/no prompt at the entrance, `zzMaw-Maps.lua:183-237`).
  The reset forces respawn and adds +20 bolster levels per reset, with no completion reward again.
  Not available in Insanity.

---

## 4. Difficulty

**Storage:**

- `Game.BolsterAmount`, the reused MMMerge "bolster %" slider in ESC → Controls → Extra Settings,
  step 50, range 0..250 (`General/MenuExtraSettings.lua:308-317`). Labels: 0 Easy, 50 Norm.,
  100 MAW, 150 Hard, 200 Hell, 250 → Nightmare prompt.
- Saved into `vars.ExtraSettings.BolsterAmount` on BeforeSaveGame and restored on load.
- Mirrored to multiplayer clients as host state (`Sync.lua:46-52`).
- The **game mode** is chosen on the party-creation screen (screen 21 regulator, values 0/2/4/6/8:
  Normal, Doom, Road to Insanity, Beyond Madness, Austerity) and frozen into
  `vars.Mode/insanityMode/madnessMode/AusterityMode` at BeforeNewGameAutosave
  (`MenuExtraSettings.lua:232-302`). The modes are Doom = `Mode 2`, Insanity = `Mode 2 +
  insanityMode`, Madness = all of those + `madnessMode` + forced horizontal, Austerity = its own
  flag.
- Mode 1 ("Survival", `zzMaw-Survival.lua`) is unreachable from the menu, and its
  `survivalMonsterTable` calls a commented-out `calcDices`. It is dead code.
- A new game in Doom, Road to Insanity or Beyond Madness sets gold to 5000 (not added) and gives
  +10000/partyCount exp. Madness also resets levels and skills to 1.

**When the difficulty can change.** Anytime, from the menu: Action 113 (close the settings)
recalculates monsters. Overrides:

- `vars.trueNightmare` re-forces 300 on every settings close and every map load.
- Mode 2 re-forces 600.
- Picking 250 triggers a typed yes/no `Question` (`nightmare()`, polled every 0.5 s,
  `:2799-2840`). "yes" sets `trueNightmare=true` and 300, permanently. Anything else reverts to
  Hell (200).

`GetDifficulty()` (`zzMaw-Stats.lua:1507-1530`): madness 9, insanity 8, Mode 2 7, bolster ≥ 300 6,
≥ 200 5, ≥ 150 4, ≥ 100 3, ≥ 70 2, else 1.

**Bug: Easy (0) and Normal (50) both map to 1**, so every table indexed by difficulty (HP, damage,
density, rarity) treats them the same. The comments say "bolster 40 / 70". Only the dead survival
code and poison scaling distinguish them. CC cost does not: `getCCDiffMult` = max((b−100)/200+1, 1) is 1 for both,
and its value is never used anyway (the cost code is commented out, the other call discards it).

Effects by difficulty (beyond sections 3.1 and 3.6):

| Effect | Easy | Norm | MAW | Hard | Hell | Nightmare | Doom | Insanity | Madness |
|---|---|---|---|---|---|---|---|---|---|
| Monster HP / damage tables | d1 | d1 | d3 | d4 | d5 | d6 | d7 | d8 | d9 |
| Bosses on all maps | – | – | yes | yes | yes | yes | ×2.5 count, ×2 specials | ×3 specials, not seeded | seeded, pity |
| Rarity weight mult (`rarityDifficultyMult`) | 1 | 1 | 1 | 1.1 | 1.2 | 1.4 | 1.6 | 1.8 | 2 |
| Epic/Rare/Uncommon band mult | – | – | – | 1.5/1.4/1.4 | 2/1.8/1.6 | 2.5/2.2/1.8 | 3/2.6/2 | 4/3/2.2 | 5.5/3.4/2.4 |
| Enchant strength (`GetDifficultyExtraPower`) | 1 | 1 | 1 | 1 | 1 | 1.05 (trueNightmare) | 1.1 | 1.2 | 1.2 |
| Monster item-drop % | | | | | | ×0.75 | ×0.5 | ×0.5 | ×0.5 |
| Item level requirement | | | | | | −6 | −3 more | −3 more (−12 total) | −12 (as Insanity) |
| Attacking cancels Fly (except 11 maps) | | | | yes | yes | yes | yes | yes | yes (and Austerity) |
| Outdoor ranged attack for melee monsters | | | | | yes | yes | yes | yes | yes |
| CC difficulty mult (control spells; computed but never used) | 1 | 1 | 1 | 1.25 | 1.5 | 2 | 3 | 5 | 5 |
| Save costs food (or blocked if short) | | | | | | yes | yes | yes | yes |
| No Lloyd/Town Portal near enemies | | | | | | yes | yes | yes | yes |
| Respawn on exit (< 65%) | | | | | | yes | yes | yes | yes |
| Death below −HP / eradication below −2HP | | | | | | yes | yes | yes, plus disintegrate | yes |
| Turn-based move limit 370 | | | | | | | yes | yes | yes (and Austerity) |
| Learning thresholds | 4-7-10 or 6-12-20 (horizontal) | | | | | | 6-12-20 | 8-16-25 | 10-24-40 |

Rows 1–3 are in `zzMaw-Items.lua:604-660, 552-561`. The item-drop row is in
`zzMaw-Items.lua:245-247, 4362-4370`. The CC row is in `zzMaw-Spells.lua:1352-1364`.

**Nightmare details:**

- **Saving costs food** when not on a completed map (`CanSaveGame`, `zzMaw-Monsters.lua:2140-2170`):
  - Outdoors: 0 food, or 3 with enemies nearby.
  - Indoors: 2 food, or 10 with enemies nearby (the yellow or red enemy detector).
  - Without enough food the save is refused.
  - The README's "can't save near monsters" is approximately this.
- Lloyd's Beacon and Town Portal are refused while the detector is yellow or red.

**Insanity extras:**

- No map ever refills (RefillDays 1e9).
- No dungeon reset.
- Indoors food is capped at 15 + monsters/25 and the excess is refunded outdoors.
- Debug-console usage logging (`vars.q1/r1/s1`, Ctrl/Alt+F1, an `Editor` metatable wrap;
  `zzMaw-Monsters.lua:3239-3318, 3750-3764`).
- Bounty: one at a time.

**Madness extras:**

- Run-wide death counter. It is written to an **obfuscated file** `Scripts/Modules/Multiplayer/Synchronization/Players/PlayerData.txt`
  keyed by a new-game seed (`SeedDeaths`, `:2289-2534`).
- A red 5-minute "combat" timer starts after taking damage. Loading or quitting while it runs
  counts as a death, with a warning on the load or quit action.
- Arena and bounty kills give 0 exp.
- Crit dim cap 3000.

**Doom** (`MAWBOLSTER[600]` shows Doom/Insane/Mad.): the effects in the table plus the on-hit
conditions from section 3.3.

---

## 5. Bolster: free versus horizontal progression

**Banked levels** (`zzzMaw_Experience.lua:228-294`):

- `vars.MMLVL = {MM8, MM7, MM6, other}` (continent index from
  `TownPortalControls.MapOfContinent`).
- All bolster experience goes into one pool `vars.EXPBEFORE`. `calcLevel(pool)` is computed, and
  the level delta since the last call is credited to `MMLVL[currentWorld]`.
- Sources:
  - Kills: Σ per-member awarded exp/5 (`addBolsterExp(bolsterExp/5)`), none from the arena.
  - Quest and event exp: per-member slice; the hook makes the bank independent of party size.
  - Map completion exp.
- `getPartyLevel(world)` = Σ MMLVL of the *other* worlds. `getTotalLevel()` = Σ all.

**Monster bolster** (section 3.2): `getPartyLevel() − 4`. On your current continent you are never
bolstered by your own levels; levels you gained elsewhere become monster levels when you arrive.
This is the README example (MM6 at 100, then MM7 +100, MM8 +180, back to MM6 +80). The stats
screen tooltip on Level/Exp (stat 13/14) lists the per-continent banked levels and the bolster per
continent, max(level−4, 0) (`zzMaw-Stats.lua:459-467`).

**Free progression switch** (`Game.freeProgression`, an extra-settings toggle saved in
`vars.ExtraSettings`, mirrored to `vars.freeProgression`):

- **Horizontal (OFF):** native maps ×2.5 levels, item level requirements, teleporters in the
  starting towns (map scripts, out of scope).
- **Learning thresholds** for the "horizontal skills" (weapons, armour, magic schools and
  utilities `{0..23,27,28,30,32,33,35,38}`) become **6/12/20** for Expert/Master/GM
  (`GetLearningRequirements`, `zzMAW-Skills.lua:215-233`). Other skills keep 4/7/10.
  Doom uses 6-12-20 even in free progression; Insanity 8-16-25; Madness 10-24-40.
- **Switching from free to horizontal mid-game** strips masteries the character no longer
  qualifies for and stores them in `vars.storedMasteries`. Switching back restores them
  (`horizontalModeMasteries`, `zzMAW-Skills.lua:1976-2016`). This is polled every 0.5 s and on
  every Action.
- Free progression: shop item strength is nerfed if the continent's banked level is low
  (`zzMaw-Items.lua:2445-2470`).

**Mastery phase-in** (`GetGradualMasteryValue`, `zzMaw-Stats.lua:1480-1505`): a mastery's table
value ramps linearly from its threshold skill to the next threshold (GM: to 1.4× its own
threshold) instead of stepping. Thresholds are `masteryThresholds()` = {0,4,7,10} normal,
{0,8,16,25} insanity, {0,10,24,40} madness.

---

## 6. Experience, solo, survival, timers, zombies, bounty, arena, maps

### 6.1 Experience curve (`zzzMaw_Experience.lua:7-45`)

```
expStep(L) = 1000·L·max(1 + (L−100)·0.01, 1)
```

This is vanilla up to level 100, then each level costs 1% more per level above 100: level 200
costs 2× vanilla per step. The curve is a table to level 2000 and extrapolated beyond. The engine
level-up checks are hooked at 0x4B30EF (trainer) and 0x48CD4D (portrait indicator), with the
result clamped below 2^31.

**Kill experience** (`events.MonsterKillExp`, `:148-223`):

- `mon.Experience = round((lb·20 + lb^1.8)·L/lb)`, where lb = clamp(max(baseLevel, L/3), ≤ 100).
- MM7 world: min(×2, +1000). **This uses the global `currentWorld`, which is set only when
  training, so it is stale.**
- × the density compensation from section 3.6.
- Per living member: `exp/aliveCount × (monsterHP/expectedHP(playerLevel))`, capped at
  `(lvl+1)·1000` per kill.
- Monsters tougher than "standard for your level" give proportionally more.
- Resurrected (Insanity), multiplayer and bounty/arena (Madness) kills give 0.

**Quest and event experience** (hook at 0x4485EC): `value·(1 + partyLvl/100) + 500·partyLvl`, then
×5/partyCount per member.

**Solo "5× experience":** there is no special case. Kill exp is split by living members, and
quest and completion exp use ×5/PartyCount, so a solo character gets five times what each member
of a five-person party gets. Other solo rules, out of scope here: Cover halves the hit instead of
redirecting it (`soloCoverDamageTaken=0.5`), disease and poison effects are halved, and multibag
and similar features.

### 6.2 Survival (`zzMaw-Survival.lua`)

This is dead or legacy code:

- Mode 1 cannot be selected.
- The Emerald Island wave spawner has 100 waves; an elite at each wave end raises the map level
  by 3.
- It has its own HP formula and a difficulty HP table (0.6/0.8/1/1.4/1.8/3, the README numbers).
- It relies on the commented-out `calcDices`.

What remains live: `survivalMaps` and the `survival-gate` pipeline stages, which are no-ops unless
`vars.SuvivalMode`. Recommendation: do not port it.

### 6.3 Timers (`zzMaw-Timers.lua`)

`mawTick_TimerDriver` runs every frame:

- It converts the `Game.Time` delta to seconds (128 ticks/s), with dt = 0 when paused, a small
  step on rollback and a cap of 2 s.
- It feeds accumulators running these tasks:

  | Task | Interval |
  |---|---|
  | horizontal masteries | 0.5 s |
  | MawRegen (HP/SP regen and meditation) | 0.1 s |
  | Leecher | 0.5 s |
  | checkOutOfBound | 2 s |
  | eliteRegen | 0.1 s |
  | mappingRegen | 1 s |
  | checkMapCompletion | 10 s |
  | nightmare prompt | 0.5 s |
  | elemental buffs | 1 s |
  | mawBuffApply | 0.5 s |
  | elementalist stacks | 0.1 s |
  | poison | 1 s |
  | charges | 1 s |

- At most 2 catch-up steps per frame in real time, 20 in turn-based.
- The file also sets boss names `PlaceMonTxt[200..205, 304]`, duplicated in `zSERIOUSMAW.lua`.

### 6.4 ZombiePlayers (`General/ZombiePlayers.lua`)

Only fixes against MMMerge:

- Conditional creature portraits (dragon, minotaur, troll zombies) are recognised by face id.
- The original face and voice are captured before transformation and restored when the condition
  is cured, with a hook before the engine's zombie-heal gate.
- The expression is reset.
- Multiplayer save-data sync (`GatherPartySaveData`).

No combat changes.

### 6.5 Bounty hunt (`General/BountyHunt.lua` vs MMMerge)

- **Chedian (ours, 2026-11-09)**: MM9's six Jarls keep the bounty office of their region (MM9_SUPPORT.md, "MAW's people
  in Chedian"): the hunt is posted in the city under the region's name, its target placed when the party next enters
  the region (`spawnPendingBountyHunt`), and the region, not the city, must be cleared first.

- **Reward** = round(baseLevel + getTotalLevel-ish (`getPartyLevel(4)`))·100. MMMerge uses
  monster level·100.
- **Monster** is picked from the arena's level-sorted C-tier table `monTbl` instead of the
  town's list. Its level is `base + max(getPartyLevel(4) − BLevel/1.5, 0)` (`mapvars.mawBounty`;
  `recalculateMonsterTable` reruns). That bonus applies to every monster on the town map and is never cleared.
- It spawns as a **C-tier boss** (`generateBoss`) with 5–15 escorts (tiers 55/30/15%).
  Omnipotent bounties bring 100–200 extra.
- A map note "Bounty" is placed and removed on kill.
- Kill credit is matched by the boss **name**, not the monster id.
- A new bounty is given only if the town map is fully cleared ("You need to clear the area
  COMPLETELY first.").
- Insanity: only one open bounty across towns, and the text names the map.
- The MM8 bounty topic behaves like MM6/MM7 (hook at 0x4b080e). Bounty maps also get the outdoor
  ranged attack.

### 6.6 AdaptiveMonstersStats (MAW copy vs MMMerge)

The file is dead at runtime because MAW sets `UseMonsterBolster=false` every map. The diffs:

- The "Bolster multipliers" settings page becomes the **MAW SETTINGS** page:
  - It is created in `MultiplayerInitialized`.
  - It reuses Multiplayer UI utilities.
  - The HP/AC/Damage/Hit/MoveSpeed regulators are commented out.
  - MAW's switches populate it: Buff Rework, M&M6 Projectiles, Homing, Friendly damage, Loot
    filter, Extra item tooltip (`zz_Maw-initialize.lua:536-574`).
- The `GenerateArenaMonster` handler is commented out.
- `PrepareMapMon` runs only for monsters whose FullHP still equals the table's.
- Monster spell generation no longer requires SpellChance > 0.
- The AC-penalty hook drops `add esi, eax` and adds a party-slot guard. That matches the older
  mmerge_data_forus version.

### 6.7 Arena (`Global/zzMaw_Arena.lua`)

New. MMMerge has no script arena; it uses the engine's Page..Lord arena.

- "Endless Arena" topic on NPC 313 in d42.blv.
- A level is 3 waves. Each wave has 6 sub-waves with tier mixes and counts: 80/20/0 ×8–10 down to
  a single C-tier boss.
- The monster family is `monTbl[(level·3−2+k) % #monTbl]`, level-sorted C-tier ids.
- Level formula is in section 3.2. +600 when you exceed the table.
- Reward: level·20000 gold. Checkpoint `vars.highestArenaWave`.
- No loot from generic kills, no bolster, 0 exp in Madness.
- Party buffs are snapshotted and restored across the reload.
- Multiplayer owner, join and progress events.
- `Fixes.lua` also patches the *engine* arena draw (fallback to the 12 nearest-level types)
  because MAW's rescaled levels left the Lord range empty and caused a division by zero.

### 6.8 `zzMaw-Maps.lua`: what it changes

1. **MM6 sprite restore** for maps 137–203: rocks, flowers and corpses get MM6 decoration names
   (`:1-71`).
2. **Outdoor refill disabled.** The listed outdoor maps get RefillDays 1e9; Insanity applies it to
   all maps (`:73-85`).
3. **Dungeon reset system.**
   - `dungeonCompletedList` is keyed by file name, with a migration from display names.
   - `tryResetDungeon` prompts on a completed dungeon's entrance and sets RefillDays 0 for that
     one visit.
   - `addDungeonEntrance` re-wires the entrance events of ~30 outdoor maps (all MM8, all MM7
     outdoor, MM6 New Sorpigal and others), keeping special gates: Escaton's Crystal key,
     Ancient Troll Home qbit, Regna tower qbit, Goblinwatch key.
4. **Used-barrel tracking.** It detects stat changes after event ≥ 20000 and turns those sprites
   into "Empty Barrel" event 19999 so barrels cannot be re-farmed after a reset (`:240-282`).
5. **Arena monster table `monTbl`** (`:750-791`).
6. **Dimension maps** (item 290, the "mapping" end-game):
   - Drop chance 0.1%, × completed-map share, × L/100, /(dropped+1), with pity, ×10 from bosses.
     Monster level must be ≥ 100 (70 in Madness). In Madness the map level (mean + 20 + Power × 10) must also
     reach 950, otherwise there is no drop.
   - Using the item teleports to a random completed map from the pool `mapDungeons` (143 ids, outdoor maps 1-14
     included). Dropped maps have 2 (70 %), 3 (20 %) or 4 (10 %) random affixes of 33, never 1; maps granted on
     completion have 1–4, all active (`affixPowerTable` base + Power·scale; reductions shown as %). Also
     randomised monster families, density × (1 + (Power·nAff + 20·nAff)/300) and level Power·10 + 20. Full spec:
     [RANDOMS.md](RANDOMS.md) §2.10.
   - Completing a dimension map drops another map.
   - The affix list is in `Modules/MawCore/Tooltip.lua:787-822`: monster damage, crit, fireball,
     dragon breath, physical/magic reflect, regen, status pierce, summon on death, % HP damage,
     speed, +resistance, CC resist, energy, HP, boss density, tier up, boss HP/damage,
     become-boss, and player crit chance/damage, regen, physical/magic damage, move speed,
     attack speed, cast speed, armour, resistance, miss, healing, leech, buffs. These are the tooltip names;
     several affixes do something else: HP does not change, CC resist only affects Stun, Energy applies always,
     reflect is inverted and regen is broken ([BALANCE_MODEL.md](BALANCE_MODEL.md) §10.2).

---

## 7. UI and keyboard additions (combat scope)

**Stats-screen right-click texts** (`zzMaw-Stats.lua:300-668`):

| Stat | Text |
|---|---|
| Might | bonus % |
| Intellect | bonus % + spell crit damage |
| Personality | heal bonus, cost reduction |
| Endurance | % and flat HP |
| Accuracy | crit damage |
| Speed | melee/ranged/spell haste, dodge chance vs reference level |
| Luck | crit chance vs reference level (plus "with dagger") |
| HP | breakdown (Endurance, Bodybuilding, items, base) and regen/s with % |
| SP | regen/s |
| AC | physical reduction vs level and total average reduction including block |
| Power (label) | M/R/S Power and leech text |
| stat 11 | active legendaries |
| Level/Exp | banked levels per continent and bolster per continent |
| Melee/ranged attack | hit chance or "100% up to level X" |
| Melee damage (16) | lifetime damage, healing, regen and leech recount, party % matrix |
| Ranged damage (18) | the same per map |
| Resistances | rules text |

**Labels rewritten:** M/R/S Power, Vitality, resistance % columns, "HP x%" and "Mana x%" when
buffs reserve the pool.

**Monster right-click** (`BuildMonsterInformationBox`, `zzMaw-Monsters.lua:1965-2130`):

- Real HP (ledger) and Level.
- Attack 1/2 and spell damage as a 95% interval, **already reduced by the selected character's
  mitigation at the monster's level.** Hold **ALT** for unreduced values (`baseDamageValue`, set
  in KeyDown/KeyUp).
- Effect name, Experience (as computed for the current member), Current HP, active debuffs with
  seconds left, spear and legendary-29 stacks.
- A dormant `resistanceRework` branch.

**Status line:** "X hits/shoots Y for N points!", "inflicts N points killing Y!", "hits for a total
of N points!" for AoE, plus "(CRIT!)". Also "*Swap*", "Dungeon Completed!" / "Map Completed! You
gain …" (EscMessage unless `disableCompletitionMessage`), "Not enough food", "Can't teleport now",
"Monsters are weakened…".

**HUD:** completion % at (500, 377); Madness death timer at (500, 450) and death count on the
stats screen.

**Keys in these files:**

| Key | Action |
|---|---|
| K (`teleportDeadMonstersAndCraftingKey`, default 75) | Pulls up to 30 corpses and 30 crafting items or maps to the party |
| R then Y on the stats Damage screen | Reset the current map's damage recount |
| ALT held | Unreduced monster damage |
| F9 / Shift / Alt / Ctrl+F9 | Boss debug |
| Ctrl/Alt+F1 | Logged as console use in Insanity and Madness |

G/V potions, R/T/E sorting and others live in item files.

---

## 8. Mapping to a clean data-driven C++ ruleset, and improvements

### 8.1 Suggested ruleset shape (OpenYAMM)

**`Ruleset` chosen at new game** (`vanilla_mmerge` | `maw`), stored in the save header and
immutable unless a migration says otherwise. MAW's own sub-settings:

- difficulty
- mode (Normal/Doom/Insanity/Madness/Austerity)
- progression (free/horizontal)
- homing on/off
- buff rework
- friendly fire

Make the mode flags immutable after creation. Make difficulty mutable, with the
`irreversible: true` rule for Nightmare.

**`assets_dev/engine/rulesets/maw/*.yml`, pure data:**

- `difficulty.yml`: per level — HP hits, damage hits, Austerity variants, density {low, hi, difBump},
  rarity mult, band mults, enchant power, drop %, item-level req delta, CC mult, flags (fly
  cancel, outdoor ranged, food-save, no-teleport, respawn-on-exit + 65% threshold,
  death thresholds, boss count divisor, special-boss chance mult, seeded bosses, learning
  thresholds, exp mult).
- `formulas.yml`: every constant in `Formulas.lua`, the stat divisors (1000, 5, 10, 20), crit
  constants, armour/resistance divisor base and per-level, damage floor, speed-dodge share,
  hit-chance par/slope/clamps.
- `map_levels.yml`: Low/Mid/High per map *file name* (MAW keys by display name and needs a
  localisation fallback), horizontal starter maps, madness progression index.
- `monster_scaling.yml`: tier factors 0.66/1/1.5, HP ratio clamp 0.6–1.8, the horizontal 2.5×
  multiplier and flattener 0.6, the arena 6× and 0.8, speed formula v/2+300 with threshold 150,
  the outdoor-ranged rule, monster spell multipliers.
- `bosses.yml`: affix definitions with an explicit enum, HP and damage rolls, treasure, sprite
  scale, the Broodlord/Omnipotent cascade.
- `map_affixes.yml`: 33 entries {base, scale, kind: reduction|proc|flat}.
- `exp_curve.yml`.

**C++ systems:**

- `MonsterStatResolver::resolve(monsterId, MapContext, RulesetState) → {level (int, uncapped), maxHp (int64), attackDamage[], resist[], speed, exp, ac}`.
  Pure and computed at spawn or map load from the data plus the balance model. Do **not** mutate
  the shared monster table per map the way MAW mutates `Game.MonstersTxt`.
- `BalanceModel` (Estimates): pure functions of (level, difficulty, mode) memoised into a
  per-ruleset lookup table (levels 1–2000) on ruleset load. It depends on the item, skill and buff
  curves, so build it after those rulesets exist, and verify it against MAW's own debug print
  loops at the bottom of `Estimates.lua`.
- `DamagePipeline<ToMonster|ToPlayer>`: copy MAW's named-stage concept. Stages are C++ functions;
  constants come from YAML. A `DamageContext` records each stage's input and output, which gives
  breakdown tooltips and a combat log for free.
- `ProgressionState` in the save: `bankedLevels[world]`, `bolsterExpPool`, `mapResetCount[map]`,
  `dungeonCompleted[mapFile]`, `trueNightmare`, `highestArenaWave`, boss seed and pity counters,
  `storedMasteries`.
- Per-map state: completion record, respawn table, boss table (index → affix enum, level, mults),
  per-monster stacks (spear, legendary 29), real HP.

### 8.2 Cheap, high-value improvements over MAW (not limited by the vanilla UI)

1. **New-game difficulty and mode picker with an explanation table.**
   - Show HP and damage relative to MAW, density, loot, and the special rules (food-save,
     respawn, permadeath "disintegrate", seeded bosses, irreversibility).
   - Default to MAW. Confirm irreversible choices once, in the UI, not with a typed "yes" prompt.
   - Show the ruleset and difficulty in the save list.
   - Fix Easy == Normal (MAW's bug). Make the table explicit so Normal gets its own row.
2. **Damage breakdown tooltip and combat log.** For each hit, record: roll, ×weapon speed factor,
   ×Might, ×crit, +enchant (per element), ÷2^(res/100), boss affix effect, leech. Show the last N
   hits in a log panel and on hover over floating numbers. The same for incoming hits: AC %,
   resistance %, Shield, floor, disease amplification, mana shield.
3. **Monster inspect panel.**
   - Effective level (uncapped), real HP bar, tier (A/B/C), boss affix with a one-line description.
   - Each resistance as "takes 35% damage" (2^(−res/100)) instead of raw numbers.
   - Damage interval vs the selected character and vs unmitigated (a toggle button, not an
     invisible ALT).
   - Estimated hits to kill with your Power; exp for each member.
   - Respawn-on-exit warning.
   - Note that energy is unresisted.
4. **Power/Vitality panel.** Show the breakdown (base, speed, crit, enchants, hit chance) and a
   slider or field for the reference monster level. MAW silently uses the sum of all banked
   levels. Also show block and dodge chance and the "100% hit up to level X".
5. **Bolster panel.** Show banked levels per continent, the current bolster, and the predicted
   level range of this map's monster families. Explain free versus horizontal and what switching
   does to masteries. MAW buries this in a Level right-click.
6. **Map completion HUD.** A progress bar with the required ratio, the 65% respawn-safe mark, a
   reward preview and the reset count.
7. **Save rule feedback.** Show "Saving here costs 10 food" on the save button instead of a status
   line after clicking.
8. **Proper homing.** Make homing a projectile property with a turn rate and lock cone, simulated
   in the projectile update. MAW overwrites every object's velocity every frame from Lua, so its
   behaviour depends on frame rate and the cosmetic projectiles bug occurs.
9. **Deterministic sim-tick scheduling** for regeneration, leech auras, boss regen and DoTs,
   instead of MAW's frame-polled game-time accumulators with catch-up caps and turn-based
   special cases.
10. **Fix MAW bugs while porting, and document each as a deviation:**
    - Easy == Normal difficulty index.
    - GM Shield ×0.85 applied twice to magic.
    - Speed and spell-haste tooltip mismatches (/10 vs /20, +20 vs ×1.1).
    - Ice Blast's duplicate spell-multiplier key.
    - The stale `currentWorld` in the MM7 exp doubling.
    - Swapper negating player hits even when swapping with a far-away monster.
    - Survival dead code.
    - The dispel "reduction" being an artefact of re-applying buffs every 0.5 s. Make it explicit,
      for example monster dispel only suppresses aura buffs for N seconds.
11. **Show the real resistance rule in the character sheet**: Light = min(Mind, Body), Dark = min
    of the elements, Energy = min of all, with the governing resistance highlighted.

### 8.3 Hacks around vanilla limits that a native engine should replace

| MAW hack | Why it exists | Native replacement |
|---|---|---|
| HP proxy ledger (`MonsterHP.lua`), 32500 damage clamp, HP rounded to tens | 16-bit monster HP | 64-bit HP, no clamp |
| `totalLevel[]` / `uniqueMonsterLevel[]` beside `mon.Level ≤ 255` | byte level | int level |
| Fire resistance thousands as an HP multiplier; Stun writes resistance 65000 and Level 0 for one tick; `res % 1000` everywhere | no side storage on monster records | explicit monster fields and status flags |
| `engine-reset` stage discarding the engine's damage | event fires after the engine computed damage | compute once in the ruleset pipeline |
| Rewriting `Game.MonstersTxt` (651 entries) and `Game.MapStats` density on every map load; `lastMonsterNumber` polling to catch new spawns | monster stats only come from global templates | resolve stats per spawn |
| `damageMultiplier` produced as a side effect of `GetAttackDelay` | only hook available | weapon speed factor computed in the damage function |
| `Game.Spells[..].Delay*` / `SpellPoints*` rewritten before casts | engine reads the table | per-caster cost and delay functions |
| `GlobalTxt` label rewriting on 250 ms polls (M/R/S, Vitality, resistance %, HP%/Mana%) | no custom stat UI | real UI widgets |
| Crit message string swap (0x4376AC); status-line text assembly across ticks with `RunNextTick` | engine message path | combat log events |
| Unarmed forced to 0 for two `GetSkill` calls; Mist Form zeroed for one tick; Fly converted to Feather Fall on attack | suppress engine rules | rules simply not in the ruleset |
| Engine hooks for hit and dodge rolls (0x4256DB, 0x425893), exp curve (0x4B30EF, 0x48CD4D), event exp (0x4485EC), recovery floor patch (0x42DA51), arena divide-by-zero fallback | native code | ruleset functions |
| Boss affix encoded in the `PlaceMonTxt` name and parsed with `string.match`; NameId ranges 220–299 bosses and 300+ "resurrected" | no per-monster extra data | monster fields |
| Swift = teleporting the monster by its last displacement each frame; speed bonus = writing Velocity on attack; `nudgeMonsterAroundCorner` and `checkOutOfBound` | AI/pathing limits | speed multiplier, proper pathing, fix spawn data |
| Homing via per-frame velocity overwrite; MM6 projectile type swaps per frame | no projectile behaviour hooks | projectile definitions |
| Respawn by reviving dead monster records on LeaveMap | no spawn system access | explicit respawn table |
| Timer driver and scheduler polling (34 tasks, ~13 MawTimers); `nightmare()` and `horizontalModeMasteries()` polled every 0.5 s | no event for settings change | event-driven on setting change |
| Death-counter file with hex-obfuscated path; debug console logging | anti-cheat for Madness and Insanity runs | if wanted, a save-header ironman flag with an autosave-only policy |
| Multiplayer `Sync`/`BossSync` burst snapshots | late-join races | out of scope for now |

### 8.4 Comparison notes with OpenYAMM's current code

- `game/gameplay/GameplayBolsterRuntime.cpp` implements the **MMMerge** adaptive bolster:
  per-monster style and kind, HP soft cap 3000→5000, level ease-out 130, reward mult ≤ 10. MAW
  disables exactly that system, so MAW needs a separate `MawMonsterStatResolver`, not a
  configuration of the existing bolster.
- `ArenaRuntime.cpp` and `BountyHuntRuntime.cpp` model the vanilla/MMMerge arena and bounty.
  MAW's Endless Arena and its boss-bounty with escorts, clear-gate and name matching are different
  features and should be ruleset-specific runtimes.
- `GameMechanics.cpp`: MAW replaces essentially every combat formula there: hit, dodge,
  statistic effect ≥ 25, AC/resistance mitigation, crit, recovery, monster damage. It is cleaner
  to let the ruleset own a `CombatFormulas` interface with vanilla and MAW implementations than to
  branch inside GameMechanics.
