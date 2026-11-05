# MAW combat calculation spec

> Formulas updated to MAW `8fbb48d1` (2026-11-05) where [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) lists a change.

Status: specification for implementation and tests (2026-10-22). Built since (2026-10-24): the MAW ruleset in
`game/rules/maw/` and `assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`. Every path below is
relative to `Maw-Mod-MMMerge/Scripts/` unless stated. Summary-level material lives in [COMBAT.md](COMBAT.md); this
document is the exact version of the per-hit maths and supersedes COMBAT.md where they differ (section 12 lists the
differences).

The numbers in section 11 were produced by running MAW's own Lua (the files and line ranges named in 11.1) under a
Lua 5.4 interpreter with MMExtension shims, not by re-deriving them by hand.

Contents:

1. Conventions, units and engine contracts
2. Shared formulas (statistic effect, crit, hit, mitigation, buffs, monster numbers, map affixes)
3. Character-sheet inputs that combat reads (`itemStats`)
4. Attack recovery and cast delay
5. Player → monster: the 36 `DamageToMonster` stages
6. Player → monster by attack path
7. Monster → player: hit, dodge, cover and the 8 `DamageToPlayer` stages
8. Leech, healing, regeneration
9. Crowd control
10. Order of operations and rounding
11. Worked examples (golden values)
12. Corrections to existing docs
13. Bugs and quirks found in the code (decide: copy or fix)
14. Not covered
- Appendix A: the balance model (`Estimates.lua`) with reference values

---

## 1. Conventions, units and engine contracts

### 1.1 Notation

| Symbol | Meaning |
|---|---|
| `L` | Level of the monster involved, `getMonsterLevel(mon)` (2.6) unless stated |
| `lvl` | Player `LevelBase` |
| `TL` | `getTotalLevel()`: sum of the banked continent levels `vars.MMLVL[1..4]` (`zzzMaw_Experience.lua:262-272`) |
| `(s, m)` | Skill points and mastery, `m` ∈ {0 none, 1 Novice, 2 Expert, 3 Master, 4 GM}; 5 = Supreme (Armsmaster) |
| `E(v)` | Statistic effect of a stat value (2.1) |
| `U()` | `math.random()`, uniform in [0, 1) |
| `R(a, b)` | `math.random(a, b)`, LuaJIT: `floor(U()·(b−a+1)) + a`; integer when `a`, `b` are integers |
| `round(x)` | MAW global, `floor(x + 0.5)` (`General/zz_Maw-initialize.lua:315-322`) |
| `mround(x)` | MMExt `math.round = bit.tobit`: nearest, ties to even, int32 wrap (MMExt `Core/Common.lua:476`) |
| `trunc(x)` | Conversion to C int when a Lua float is handed back to the engine (inferred: toward zero) |
| `res%1000` | Monster resistances are read modulo 1000 almost everywhere (marker values live in the thousands) |
| `diff` | `GetDifficulty()` (2.7) |

**Time.** `const.Minute` = 256 game ticks = 2 real seconds at normal speed; 128 ticks per real second
(`Formulas.gameMinuteSeconds = 2`, `Modules/MawCore/Formulas.lua:10`). Recovery and spell delays are in engine
recovery units; MAW's own DPS maths divides them by 60 to get seconds (`General/zzMaw-Stats.lua:1217`), which matches
OpenYAMM's `ticks/128·2.1333` conversion.

**Monster resistance index = damage kind** for Fire 0, Air 1, Water 2, Earth 3, Phys 4, Spirit 6, Mind 7, Body 8,
Light 9, Dark 10 (`damageKindMap`, `General/zzMaw-Stats.lua:922-933`). Energy 12, Magic 5 and Dragon 50 have no
monster column: `table.find(damageKindMap, kind)` is nil and the resistance used is 0. Write
`monRes(kind) = mon.Resistances[kind] % 1000` (0 for kinds without a column).

**Player resistance ids** (for `GetResistance`): 10 Fire, 11 Air, 12 Water, 13 Earth, 14 Mind, 15 Body.

### 1.2 Mastery-indexed tables

`baseRecovery` (`General/zzMAW-Skills.lua:25-35`): Bow 100, Blaster 40, Staff 120, Axe 140, Sword 80, Spear 120,
Mace 100, Dagger 60.

Lua tables written `{[0]=a, b, c, d, e}` have index 1 = `b`. Tables written `{a, b, c, d, e, [0]=0}` have index
1 = `a`. The values below are by mastery N/E/M/GM (and Supreme where it exists).

| Table | N | E | M | GM | Sup | Source |
|---|---|---|---|---|---|---|
| `weaponImpair` Leather (% delay) | 10 | 0 | 0 | 0 | | `:37-43` (index 0 = 10 too) |
| `weaponImpair` Chain | 20 | 10 | 0 | 0 | | |
| `weaponImpair` Plate | 20 | 10 | 10 | 0 | | |
| `weaponImpair` Shield | 10 | 0 | 0 | 0 | | |
| `skillAttack` per point: Staff/Sword/Dagger/Axe/Bow/Mace/Blaster | 1 | 2 | 3 | 4 | | `:45-56` |
| `skillAttack` Spear | 2 | 4 | 6 | 8 | | |
| `skillAttack` Unarmed | 2 | 2 | 3 | 3 | | |
| `skillRecovery` per point: Sword, Bow, Unarmed | 0 | 1 | 1 | 2 | | `:59-70` |
| `skillRecovery` Axe | 0 | 1 | 1 | 1 | | |
| `skillRecovery` Dagger | 0 | 0 | 0 | 1 | | |
| `skillRecovery` Staff, Spear, Mace, Blaster | 0 | 0 | 0 | 0 | | |
| `skillDamage` % per point (all masteries): 2, Bow and Blaster 4 | | | | | | `:72-83` |
| `skillAC` (% of weapon attack per point+10): Staff | 0 | 2 | 3 | 4 | | `:86-103` |
| `skillAC` Sword | 0 | 0 | 1 | 2 | | |
| `skillAC` Spear | 0 | 4 | 6 | 8 | | |
| `skillAC` Dodging (flat per point) | 4 | 5 | 6 | 6 | | |
| `skillResistance` Staff (same shape as skillAC) | 0 | 2 | 3 | 4 | | `:107-124` |
| `bodybuildingHP` (% HP per point) | 0.5 | 1 | 1.5 | 2 | | `:105` |
| `skillItemAC` Leather/Chain/Plate (% of armour AC per point) | 3 | 4 | 5 | 6 | | `:125-131` |
| `skillItemAC` Shield | 4 | 6 | 8 | 10 | | |
| `skillItemAC` Dodging | 5 | 5 | 10 | 10 | | |
| `skillItemRes` Leather | 2 | 3 | 4 | 5 | | `:132-138` |
| `skillItemRes` Chain | 1 | 2 | 3 | 4 | | |
| `skillItemRes` Plate | 0 | 1 | 2 | 3 | | |
| `skillItemRes` Shield | 4 | 6 | 8 | 10 | | |
| `skillItemRes` Dodging | 0 | 5 | 5 | 10 | | |
| `armsmasterSkill.Damage` per point | 0 | 1 | 1 | 1.5 | 2 | `:149-153` |
| `armsmasterSkill.Speed` per point | 0 | 0 | 1 | 1 | 1 | |
| `armsmasterSkill.Attack` per point | 1 | 1 | 1 | 1 | 1 | |
| `dkDamageSkill` per point | 0.5 | 0.75 | 1 | 1 | | `:155` |
| `fireAuraDamage` (share of weapon level damage) | 0.10 | 0.15 | 0.20 | 0.25 | | `General/zzMaw-Items.lua:4283` |
| `fireAuraMinDamage` (×2 two-handed) | 3 | 6 | 12 | 24 | | `:4286` |

Caps: `skillCap` Alchemy 60, Cover (50) 30, Mana Shield (51) 50, Retaliation (53) 50; a skill above `2·cap` reads as
`2·cap` (`General/zzMAW-Skills.lua:162-213`). `skillEffectCap.buff = 50`, `.dayBuff = 75` (caster skill a buff counts,
`:169-172`). Item skill bonuses cannot raise a skill above twice its base (`General/zzMaw-Items.lua:2605-2611`).

`GetGradualMasteryValue(tbl, s, m)` (`General/zzMaw-Stats.lua:1480-1495`) ramps a mastery table linearly instead of
stepping: thresholds `th = {0, 4, 7, 10}` (`{0, 8, 16, 25}` Insanity, `{0, 10, 24, 40}` Madness,
`masteryThresholds`, `:1497-1505`); for `m ≥ 1`, `from = th[m]`, `to = th[m+1]` or `1.4·from` for GM; value =
`tbl[m−1] + (tbl[m] − tbl[m−1])·clamp((s − from)/(to − from), 0, 1)`. **Only the balance model, DK skill damage and a
few tooltips use it; live combat code mostly indexes the step value `tbl[m]` directly.** `masteryForSkill(S)` is the
highest `i` with `S ≥ th[i]` (`:1462-1469`).

### 1.3 Engine contracts MAW relies on

MAW runs on the MM8 engine through MMExtension. These are the engine values the Lua reads; OpenYAMM must reproduce them
in the MAW ruleset.

- **Damage events.** `events.CalcDamageToMonster(t)` fires inside the engine's monster damage routine
  (MMExt `Core/events.lua:2350-2371`): `t.Damage` = the raw damage the engine passes in, `t.Result` = the engine's
  post-resistance value, `t.DamageKind`, `t.Monster`, `t.MonsterIndex`, and for MM8 `t.Player`/`t.PlayerIndex` when the
  attacker pointer is a party member. `events.CalcDamageToPlayer(t)` has `t.Damage`, `t.Result`, `t.DamageKind`,
  `t.Player`, `t.PlayerIndex` (`:1925-1935`). Both run MAW's pipeline last among mod handlers
  (`Global/zzzzzMaw_Damage.lua:7-13`); `Maps/BrBase.lua:1410` only sets a rage flag.
- **What `t.Damage` holds.** Melee and arrows: the engine's own roll (discarded by stage 17). Spells: the value returned
  by `events.CalcSpellDamage` (6.7). Mass Distortion: computed from the engine's (proxy) monster HP.
- **Stat getters.** Every `CalcStatBonusBySkills` result is 0: the handler at `General/zzMAW-Skills.lua:402-404` sets
  `Result = 0` and is registered after the MiscTweaks handlers that try to add Staff+Unarmed, Dragon and Meditation
  bonuses (`General/MiscTweaks.lua:572-746`), so those are wiped. `CalcStatBonusByItems` returns the `itemStats` rows
  (section 3, `General/zzMaw-Items.lua:2566-2584`); the engine stores the result as an int (`trunc`). With those, the
  engine values are (inferred from MM7/MM8 engine structure, and consistent with how MAW's own code compensates):

  | Getter | Value |
  |---|---|
  | `GetMeleeDamageMin/Max` | `E(Might) + trunc(row42/43)`, at least 1 (dragons: 6.10) |
  | `GetRangedDamageMin/Max` | `trunc(row46/47)` (no flat Might effect) |
  | `GetMeleeAttack` / `GetRangedAttack` | `E(Accuracy) + trunc(row40)` / `E(Accuracy) + trunc(row44)` |
  | `GetArmorClass` | `trunc(row10 − E(Speed)) + E(Speed)` + engine buff AC (Speed's AC bonus cancelled, `:2581-2583`) |
  | `GetResistance(i)` | base + `trunc(row[i+1])` + racial term (2.4) |
  | `GetFullHP` | `HPBase[class] + HPFactor[class]·(LevelBase + E(Endurance)) + trunc(row8)` |
  | `GetFullSP` | `SPBase + SPFactor·LevelBase + trunc(row9)` (rows include MAW's own SP terms) |

- **Engine extras switched off.** `ItemAdditionalDamage` → 0 (`Global/zzMaw_Legendaries.lua:6-20`),
  `ModifyItemDamage` → 0 (`General/zzMaw-Items.lua:2555-2557`), engine vampirism off (`:2462-2491`). Engine recovery
  floor 30 → 1 (`Modules/MawCore/Fixes.lua:29-35`, the `push 30` at `0x42DA51`).
- **Hit rolls.** Player→monster uses MAW's chance through the hook at `0x4256DB` (`General/zMaw-hooks.lua:175-197`);
  monster→player through the hook at `0x425893` (`General/zzMaw_MonsterHit.lua:12-31`). Spells have no to-hit roll.
- **Monster HP.** The engine field is 16-bit; real HP above 32000 lives in a per-map ledger (6.14).

---

## 2. Shared formulas

### 2.1 Statistic effect

`E(v) = floor(v/5)` for `v ≥ 25` (`General/zzMaw-Stats.lua:947-951`). Below 25 the vanilla table applies:
21-24 → 4, 19-20 → 3, 17-18 → 2, 15-16 → 1, 13-14 → 0, 11-12 → −1, 9-10 → −2, 7-8 → −3, 5-6 → −4, 3-4 → −5, 0-2 → −6.

Percentage stat terms (all with divisor `STAT_DAMAGE_DIVISOR = 1000`, `:263-267`, `:296-298`):

- Might: physical damage `×(1 + Might/1000)` (applied in the sheet rows, 3.5). `GetMightDamageMultiplier` ignores its
  level argument, so `mightLevelSwap` (`Modules/MawCore/Damage.lua:432-437`) is always exactly 1.
- Spell damage: `×(1 + max(Int, Per)/1000)` (6.7).
- Endurance: HP `×(1 + End/1000)` (3.6). Healing: `×(1 + Per/min(1000 + 3·lvl, 4000))` (8.3).

### 2.2 Critical hits — `getCritInfo(pl, dmgType, monLvl)` (`General/zzMaw-Stats.lua:61-142`)

```
monLvl  = monLvl or MawReferenceLevel()           -- MawReferenceLevel = round(TL)  (:54-59)
chance  = Luck/min(500 + 5·monLvl, 3000) + 0.05                               (Formulas.critChance)
dim     = min(250 + 2.5·monLvl, 2000)    -- 3000 in Madness                    (Formulas.critDiminishingLevel)
if dmgType == "spell": mult = Int/(4·dim) + 1.5
elif dmgType == "heal":  return 0, 0, false     -- heals never crit
else:                    mult = Accuracy/dim + 1.5
mult = round(mult·100)/100                       -- 2-decimal rounding happens here
if not dmgType:                                  -- nil/false: weapon hits, arrows included
    per hand i in {0 offhand, 1 main}: item skill Dagger (and not an axe id) and Dagger m ≥ 3:
        chance += 0.05 + 0.01·sDagger/min(1 + monLvl/200, 4)          -- per hand, stacks for two daggers
    first hand holding an axe, Axe m == 4: mult += 0.01·sAxe            -- once
if buff rework on and pl.SpellBuffs[Fate].ExpireTime ≥ now:
    (s, m) = Fate caster (47); (s2, m2) = Hour of Power caster (86); s = max(s, s2/1.5); m = max(m, m2)
    chance += GetBuffMultiplier(Fate, s, m) = 0.05 + 0.001·s
if map affix 20: chance −= power20/100          -- raw percentage points (affix 20 is not a "reduction" affix)
if map affix 21: mult = (mult − 1)·(1 − power21/100) + 1
if legendary 14: chance += 0.10 (no cap) else chance = min(chance, 1)
success = U() < chance
```

Who passes which level: weapon hits, dragon and class overrides pass the target's `L`. **Spells
(`CalcSpellDamage`), enchant/aura crits (legendary 26) and every tooltip pass nothing**, so they scale against
`round(TL)`, the party's own total banked level, not the target.

### 2.3 Player hits monster — `Formulas.mawHitChance` (`Modules/MawCore/Formulas.lua:85-151`)

```
atk     = (range == 0 ? pl:GetMeleeAttack() : pl:GetRangedAttack()) + bonus      -- bonus: engine argument
exp     = getPlayerEstimatedAttack(L)                                            -- Appendix A
overPar = (7.5 + atk)/(exp + 10) − 1
chance  = clamp(0.75 + overPar·0.5 + blessBonus, 0.25, 1.0)
blessBonus = 0 unless buff rework on and the player's Bless buff active:
             0.05 + 0.05·min(sBless, 50)/50, sBless = getBuffSkill(Bless) skill
hit = chance ≥ U()        (General/zMaw-hooks.lua:175-197; events.PlayerHitOrMiss may still override, MAW has none)
```

Monster AC plays no part. Applies to melee, arrows and blaster shots; spells always hit.

### 2.4 Player mitigation — `calcMawDamage(pl, kind, D0, rand, monLvl, ratioOnly)` (`General/zzMaw-Stats.lua:1037-1158`)

`monLvl` defaults to `pl.LevelBase`. Monster hits pass the attacker's `L`; traps pass nothing (player level); friendly
fire passes the caster's level.

```
d = D0
if offhand item is a shield and Shield m == 4: d ×= 0.85                       -- (A) all kinds
if kind == Phys(4):
    AC = pl:GetArmorClass(); if affix 28: AC ×= (1 − p28/100)
    d  = round(d / (AC/(200 + monLvl) + 1))                                  -- Formulas.armorDamageTaken
    d  = classCut(d, Body)                                                     -- (C)
    if vars.shieldEnchant[id] (special enchant 36 "of Shielding" worn): d ×= 0.85
    return post(d)
d = classCut(d, Dark)                                                          -- (C)
if Shield buff (party buff 14 or Shield potion), buff rework on:
    (s, m) = bestBuffSource(Shield): d ×= max(1 − (0.15 + 0.003·s), 0.7)       -- s ≤ 50 → never below 0.7
(rework off, dead path: ×0.85 if player buff 11 or party buff 14)
if offhand shield and Shield m == 4: d ×= 0.85                                 -- (B) second time: magic gets 0.7225
if kind not in damageKindResistance: return post(round(d))                     -- e.g. Magic 5, Dragon 50
for each resistance id r in damageKindResistance[kind]:
    base   = pl:GetResistance(r)
    item   = vars.normalEnchantResistance[id][r+1] (×1.5 with legendary 16)
    total  = base·(1 − p29/100) if affix 29 else base
    taken  = 1/(total/(100 + monLvl) + 1) · 1/(item/100 + 1)
keep the r with the LARGEST taken (the weakest resistance)
if that r's base ≥ 65000: return 0                                             -- immunity (Lich, Vampire)
if rand and taken > 0: taken = max(0, taken + min(taken, 1 − taken)·(U() + U() − 1))   -- never reached (13)
return post(round(d·taken))

classCut(d, dkSkill): Shaman: d/(1 + 0.01·sAir); Death Knight: d/(1 + 0.01·s[dkSkill]) (Body for Phys, Dark for magic)
post(d):                                                                        -- applyPostMitigation :761-776
    d = max(d, 0.1·D0)                        -- floor on the ORIGINAL input, before any shield
    if legendary 18: d ×= 0.9
    d ×= max(0.97^n, 0.5) with legendary 22, n = active monsters within 512 of the party
    if not ratioOnly and flat = flatClassReduction(pl) > 0: d = max(d − flat, 0.25·d)
    return d                                  -- float; engine truncates
```

`damageKindResistance` (`:977-988`): Fire {10}, Air {11}, Water {12}, Earth {13}, Spirit {14}, Mind {14}, Body {15},
Light {14, 15}, Dark {10, 11, 12, 13}, Energy {10..15}. Spirit and Mind both use Mind resistance.

`flatClassReduction(pl)` (`:742-759`), 0 when unconscious/dead/eradicated; Shaman uses Water skill, Seraphim Spirit:

```
lvl  = TL;  (_, _, _, avgTaken) = getPlayerEstimatedVitality(lvl + 1)
flat = round(getMonsterDamage(nil, lvl + 1)·(skill/estimateSkill(lvl))·avgTaken/2·0.99^estimateSkill(lvl))
```

Because the flat cut and legendaries 18/22 run after the 10 % floor, a hit can end below 10 % of its input.

Player resistance inputs: `GetResistance` includes items, armour-skill resistance, Luck's `E(Luck)` on all six
(`General/zzMaw-Items.lua:3088-3094`), buff-rework resistance auras, and racial terms from
`General/zzMaw-Stats.lua:1349-1383`: Dark Elf/Elf (race 2, 7) +25+lvl Fire/Air/Water/Earth; Troll +25+lvl Water/Earth;
Goblin +25+lvl Air/Earth; Dwarf +25+lvl Earth/Mind; Dragon Fire +100+floor(2·lvl); Lich Mind and Body = 65000;
Vampire Mind = 65000. (MiscTweaks' racial +5 terms are wiped by `itemStats`.) Ring resistance enchants count half,
first enchant +10 before halving (`General/zzMaw-Items.lua:2743-2750`).

### 2.5 Buff values under the buff rework

`GetBuffMultiplier(spell, s, m) = Base[m]/100 + Scaling[m]·s/1000` (`General/zzMaw-Spells.lua:2655-2660`). The live
`buffPower` table is the one `Global/zzMaw_Mapping.lua:25-58` installs on every `AfterLoadMap` (it overrides the
`zzMaw-Spells.lua:2670-2692` table): Base/Scaling per spell, equal at all masteries:

| Spell | Base | Scaling | Used as |
|---|---|---|---|
| Fire/Air/Water/Earth/Mind/Body Res (3, 14, 25, 36, 58, 69) | 20 | 2 | flat `(Base + level/4)·(1 + Scaling·s/100)` |
| Haste 5 | 10 | 2 | delay ÷ (1 + 0.10 + 0.002·s) |
| Shield 17 | 15 | 3 | magic ×max(1 − 0.15 − 0.003·s, 0.7) |
| Empower Magic 28 | 15 | 3 | **not read**: `ascendSpellDamage` uses Haste's row (13) |
| Stone Skin 38 | 20 | 2 | AC flat |
| Bless 46 | 20 | 2 | attack flat + hit bonus (2.3) |
| Fate 47 | 5 | 1 | crit chance |
| Heroism 51 | 15 | 3 | melee damage ×(1 + 0.15 + 0.003·s) |
| Meditation 56, Regeneration 71 | 10 / 5 | 2 / 2 | regen (8.4) |
| Hammerhands 73 | 15 | 3 | unarmed damage multiplier |
| Day of the Gods 83 | 20 | 2 | stat % |
| Day of Protection 85 | 20 | 2 | resistances flat |
| Hour of Power 86 | 10 | 2 | its skill counts as s/1.5 for Haste/Shield/Stoneskin/Fate |

The caster skill is capped at 50 (75 for 83/85/86) in `getCasterBuffSkill` (`General/zzMaw-Spells.lua:3083-3110`).
With map affix 33 the table is scaled by `(1 − p33/100)` in place on each map load, without a reset first (13).

### 2.6 Monster numbers used per hit

- **Level** `getMonsterLevel(mon)` (`General/zzMaw-Monsters.lua:1884-1895`): generic (`NameId == 0`) →
  `round(totalLevel[mon.Id])`; unique → `round(mapvars.uniqueMonsterLevel[i])`; boss → `bossData.Level`; else
  `mon.Level`. `mon.Level` itself is capped at 255 and is what Adamantite, Regenerating, the Stun spell, the CC engine
  path, Mass Distortion's `(Level/250)²` and Elementalist learning read.
- **Damage** `getMonsterDamage(mon, level)` (`Modules/MawCore/Estimates.lua:458-495`):
  `Vit(Lb)/hits[diff]` with `Lb = totalLevel[MawTierB(mon.Id)]` (always the B-tier level of the family),
  `hits = {14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4}` (Austerity `{15, 10, 5, 4, 3, 2.5, 2, 1.5, 1}`); ×0.66 for tier A
  (`Id%3 == 1`), ×1.5 tier C (`Id%3 == 0`); × `bossData.DamageMult` for `220 ≤ NameId ≤ 300`.
  `Vit` = `getPlayerEstimatedVitality` (Appendix A). With `mon = nil` the result is the raw `Vit(level)/hits`.
- **HP** `getMonsterHealth(mon, level)` (`Estimates.lua:678-726`): `Power(Lb)·hitsM[diff]·clamp(FullHP_tier/FullHP_B,
  0.6, 1.8)·bossHealthMult`, `hitsM = {1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5}` (Austerity `{1, 2, 4, 5, 6, 7, 8, 9,
  9.5}`). `HPtable[id] = round(getMonsterHealth({Id=id, Level=TLv}, TLv))` per template (no boss factor), ×(1+p15/100)
  with map affix 15 (`General/zzMaw-Monsters.lua:596-599, 659-663`); leech measures against it (8.1).
- **Resistances**: template `min(base + p12, p12 + 200, 999)` per column, column 5 skipped (`:600-605`); a hit is
  divided by `2^(monRes/100)`, so the strongest possible cut is ÷4 (plus affix 12).
- **Boss stats** (`generateBoss`, `:2972-3110`): `Level = min(round(MawBossLevel), 255)` stored, `bossData.Level`
  uncapped; `HealthMult = 2.5·(1 + Level/255/f)·(1 + 0.5·U()/f)` (f = 4 Austerity, else 1), ×(1+p18/100);
  `DamageMult = 1.2 + 0.2·U()` (Broodlord `1.5 + 0.3·U()`, ×1.5 HP; Omnipotent `2 + 0.5·U()`, ×4 HP), ×(1+p18/100);
  monster `SpellSkill` ×DamageMult.

### 2.7 Difficulty index

`GetDifficulty()` (`General/zzMaw-Stats.lua:1507-1530`): Madness 9, Insanity 8, `vars.Mode == 2` 7, else by
`Game.BolsterAmount`: ≥300 → 6, ≥200 → 5, ≥150 → 4, ≥100 → 3, ≥70 → 2, else 1 (Easy 0 and Normal 50 both 1).
Combat code that reads `Game.BolsterAmount` directly: fly removal (>100), Mass Distortion table, poison DoT
(`/100`), death thresholds (≥300).

### 2.8 Map affix power (`General/zzMaw-Maps.lua:1084-1128`)

`power = base + mapPower·scale`; affixes {13, 21-33} are "reductions" and become
`reductionPercent(power) = (1 − 1/(power/100 + 1))·100` rounded to 2 decimals; proc affixes {3, 4, 8, 9, 14, 19} are
capped at 100. `getMapAffixPower(n)` is `false` outside dimension maps. Combat-relevant affixes:

| n | base, scale | Effect (where) |
|---|---|---|
| 1 | 20, 0.5 | monster damage ×(1 + p/100) (7.6) |
| 2 | 10, 1 | U() < p/100: monster hit ×2 (7.6) |
| 5 / 6 | 7, 0.15 | phys / non-phys player hits reflect `hit·(1 − p/100)` to the attacker (stage 30; 13) |
| 7 | 1, 0.1 | monster regen (bugged, 13) |
| 10 | 5, 0.1 | monster hit + p % of the player's full HP (7.6) |
| 12 | 30, 2 | + p to all monster resistances (cap moves with it) |
| 13 | 30, 1 | Stun spell hit chance ×(1 − p/100) |
| 14 | 20, 1 | monster hit becomes Energy when U() < p — always, p ≥ 20 (13) |
| 15 | 20, 1.5 | monster HP and `HPtable` ×(1 + p/100) |
| 18 | 15, 1 | boss HP and damage mult ×(1 + p/100) |
| 20 / 21 | 10, 0.2 | crit chance − p/100 / crit damage share ×(1 − p/100) |
| 22 | 20, 1 | player regen ×(1 − p/100) |
| 23 / 24 | 15, 0.5 | player phys / non-phys damage ×(1 − p/100) |
| 26 / 27 | 15, 0.5 | attack delay / spell delay ÷(1 − p/100) |
| 28 / 29 | 15, 0.5 | player AC / resistance ×(1 − p/100) |
| 30 | 15, 0.5 | U() < p/100: player hit = 0 |
| 31 / 32 | 15, 0.5 | healing / leech ×(1 − p/100) |

---

## 3. Character-sheet inputs that combat reads (`itemStats`, `General/zzMaw-Items.lua:3358-3445`)

`itemStats(index)` rebuilds 50+ rows per character (`plItemsStats[index]`) whenever equipment or buffs change and on
every cast and hit (`mawRefresh`). Phase 1 collects items; the table is then published so `GetSkill` sees item skill
bonuses; phase 2 adds everything that depends on effective skills. Row numbers are 1-based stat id + 1
(1-7 stats, 8 HP, 9 SP, 10 AC, 11-16 resistances) plus 40-47 (`statMap`, `:3467-3486`): 40 melee attack, 41/42/43
melee base/min/max, 44 ranged attack, 45/46/47 ranged base/min/max.

### 3.1 Weapon rows — `addWeaponRows` (`:2812-2947`), once per equipped item with skill ≤ 7 or 39

```
skip if: item skill > 7 (and ≠ 39); or main hand is a Blaster and this item is not an "ancient weapon"
(bonus, sides) = GetWeaponDamageRows(it)                                      (:4585-4593)
    (wDmg, wDice, wFlat) = getWeaponDamageForLevel(ItemLevel(it), twoHanded, GetWeaponFlatDamage(it))  (Appendix A)
    split = wDmg − wDice − wFlat
    bonus = (split/2 + wFlat)·Q;  sides = (split/2 + wDice)/max(diceCount, 1)·Q
    Q = artifact base mult × quality mult;  ItemLevel(it) = 5·MaxCharges (artifacts: TL)
skill = item skill (axe ids → Axe 3);  (s, m) = Armsmaster (m = 5 "Supreme" for classes 16-19 at the requirement)
(s2, m2) = weapon skill
if Bow: bonus += s2
if Staff: (s, m) = (sUnarmed/2, mUnarmed) if Staff m2 == 4 else (0, 0)       -- staves never get Armsmaster
mult    = 1 + s2·skillDamage[skill]/100
side    = sides·mult;  add = bonus·mult
armsDmg = armsmasterSkill.Damage[m]·s·mult
two axes held: side, add ×= (1 − 0.1 per two-handed axe)
Staff: armsDmg = 2·s·mult  (= sUnarmed·mult at GM staff)
class terms added to armsDmg (each ×mult):
    Death Knight: GV(dkDamageSkill, sWater, mWater)·sWater + GV(dkDamageSkill, sDark, mDark)·sDark
    Seraphim:     sMind·(mMind + 1)/2
    Shaman:       sEarth·mEarth/2
    Assassin:     sEarth·(1 + mEarth); vars.assassinDamage[id] = armsDmg (×(1 + Heroism mult) when Heroism on)
offhand item present, this item is not a bow, offhand not a shield: armsDmg /= 2   (applies to both hands)
Blaster: armsDmg = 0
floor, once per weapon skill: add += max(s2 − (bonus + sides·diceCount/2 + armsDmg/mult)·(mult − 1), 0)
tot = armsDmg + add
non-bow: row40 += round(bonus); row41 += round(bonus); row42 += diceCount + round(tot);
         row43 += round(side)·diceCount + round(tot)
bow:     row44 += round(bonus); row45 += round(bonus); row46 += round(diceCount) + add;
         row47 += round(side)·diceCount + add
```

`GV` = `GetGradualMasteryValue`. Dual wielding: both weapons add their own rows, so `GetMeleeDamageMin/Max` sum both
hands.

### 3.2 Attack rows

- Bless (rework, buff 1 active): `+(Base[m] + level/4)·(1 + Scaling[m]·s/100)` to rows 40 and 44 (`:2950-2959`).
- Per slot 0-3: best non-bow `skillAttack[skill][m]·s` → row 40; bow slot → row 44. GM bow: rows 46/47 −= `sBow`
  ("remove vanilla calculation", `:3168-3171`); with skill bonuses already 0 the net effect is that the `+sBow` of 3.1
  is taken back unmultiplied at GM.
- Armsmaster (`m > 0` and the main hand holds an item that is not a staff, `MawArmsmasterApplies`,
  `General/zzMAW-Skills.lua:157-160`): row 40 += `s`·1. Unarmed characters get no Armsmaster attack or speed.
- Unarmed rows apply when `mUnarmed ≥ 1` and both hands are empty, or when the main hand is a staff and Staff `m ≥ 4`:
  row 40 += `skillAttack[Unarmed][m]·s`, rows 41/42/43 += `2·s` (`:3183-3209`). This is on top of the staff's
  `armsDmg` above: a GM staff gets both.

### 3.3 Armour class and resistance rows

- Armour items: `ac = diceCount + Mod2 + round(referenceAC·MaxCharges/40)` (artifacts: own power), × quality, rounded;
  legendary 28 ×1.5; summed into row 10 and into `armorAC`/`shieldAC` (`:2692-2717`).
- Armour skill: row 10 += `mround(armorAC·skillItemAC[body][m]·s/100) + mround(shieldAC·skillItemAC[Shield][m]·s/100)`;
  rows 11-16 += same with `skillItemRes` (`:2963-3000`). Austerity floor `round(s·m)·2` each.
- Weapons: row 10 += `round(skillAC[skill][m]·bonusBase/100·(s+10))`, rows 11-16 += `skillResistance` likewise
  (Staff only), `bonusBase = Mod2 + round(referenceWeaponAttack·MaxCharges/30)` (`:3213-3247`). Every equipped staff in
  the party adds its resistance term to everyone (`:3294-3316`).
- Dodging: `skillAC[Dodging][m]·s` with no body armour, or at Master+ with leather (`:3173-3176`).
- Dragon race: rows 1-16 ×3 (`:3003-3015`); dragon AC/resistances also get the Classes handler terms (6.10).

### 3.4 Buff-rework stat rows (`addBuffStats`, `:3019-3085`)

For the six resistance auras: row(11..16) += `max(buff, DoP)` with
`buff = (Base[m] + level/4)·(1 + Scaling[m]·s/100)` and Day of Protection `(Base + level/4)·(1 + Scaling·s/100/1.4)`.
Each aura (or Day of the Gods) also raises its paired stat by `pct = min(10 + s/5, 20)/100` (Day of the Gods
`min(10 + s/7, 20)/100`) of (items + base). Accuracy uses Bless or Day of the Gods. Stone Skin: row 10 +=
`(Base + level/4)·(1 + Scaling·s/100)`.

### 3.5 Damage multipliers on the rows (`applyDamageMultipliers`, `:3320-3356`)

```
might = row1 + MightBase + MightBonus (+ party buff 2 power); B = E(might); mm = might/1000
hero  = Heroism active (rework): 0.15 + 0.003·s else 0
ham   = Hammerhands active and the unarmed rows applied: 0.15 + 0.003·s else 0
sham  = Shaman: sSpirit/100
for r in 42, 43:  r += (r + B)·mm;  r += (r + B)·hero;  r += (r + B)·ham;  r += (r + B)·sham
for r in 46, 47:  r += (r + B)·mm
```

Since the engine adds `B` to melee min/max itself, the melee range is exactly
`(rowRaw + B)·(1+mm)·(1+hero)·(1+ham)·(1+sham)` (before `trunc`). Ranged rows get only the multiplied share of `B`
and no Heroism.

### 3.6 HP and SP rows

```
HP (addHP :3097-3128): endurance = row4 + EndBase + EndBonus + endurance buff; endEff = E(endurance)
    (s, m) = Bodybuilding; m2 = 5 if m ≥ 4 else m; BBHP = s·m2
    baseHP = HPBase + HPFactor·(lvl + endEff + BBHP); full1 = baseHP + row8
    endBonus = full1·endurance/1000; full2 = full1 + endBonus
    BBBonus = full2·bodybuildingHP[min(m,4)]·0.01·s
    row8 += endBonus + BBBonus + HPFactor·BBHP
SP (addMana :3131-3146): total = SPFactor·lvl + SPBase + SPFactor·(2·E(Per) + sMed·m2Med) + row9
    row9 += total·enlightenment(s52, m52) + SPFactor·E(Per)        -- enlightenment {0.5,1,1.5,2} % per point
```

### 3.7 Leech table (`addWeaponACRes`, `:3213-3291`)

`lifeLeech[id] = {Melee, Ranged, Spell}`, rebuilt each refresh:

| Source | Melee | Ranged | Spell |
|---|---|---|---|
| Special 41 "of Darkness" or 16 "Vampiric" in slots 0-2 (flag, no stacking) | 0.10 | 0.05 | 16 only: 0.10 |
| Special 40 "Lichs'" in slots 0-2 | | | 0.10 |
| Artifact drain (Hades 2035) | −0.10 | | |
| Vampiric Weapon aura (91) active | +0.05 | +0.025 | +0.025 |
| Vampire race (×2 for classes 40/41) | +0.05 | +0.025 | +0.025 |
| Death Knight (`Formulas.dkBloodLeech`) | +0.10 | +0.05 | |

Artifacts flagged `Vampiric` (Foulfang 508, Spiritslayer 527, Mordred 2020) give no leech (13).

---

## 4. Attack recovery and cast delay

### 4.1 Weapon recovery — `getItemRecovery(it)` (`General/zzMAW-Skills.lua:425-440`)

```
base = baseRecovery[skill] (axe ids → Axe); unknown skill → 100
base = round(base·(0.75 + min(ItemLevel(it), 600)/500)/10)·10
two-handed (EquipStat 1): base = round(base·1.25/10)·10
```

### 4.2 `events.GetAttackDelay` (`:442-617`), then three later handlers

```
melee:
    any hand holds a Blaster (skill 7): Result = 40, damageMultiplier.Melee = 0.4, stop (no other term)
    for hand i in 0 (offhand), 1 (main) with item skill < 8:
        speed[i] = getItemRecovery(it)
        each weapon skill pays skillRecovery[skill][m]·s once (a two-handed axe in slot 0 does not pay)
        special 41 or 59 on the item: swift += 0.3 if two-handed else 0.15
        Staff with m ≥ 4: + skillRecovery[Unarmed][mU]·sU once
    empty main hand (and not a dragon, see 13): + skillRecovery[Unarmed][mU]·sU once
    base = average of the weapon hands present (sum if one)
    main hand holds an item that is not a staff: bonus += sArms·armsmasterSkill.Speed[mArms]
ranged:
    bow slot item: base = getItemRecovery(bow); bonus = skillRecovery[skill][m]·s; special 41/59: swift += 0.3
both:
    Death Knight: bonus += sWater;  Seraphim: bonus += sLight·mLight/2
    Assassin (stack timer not expired): bonus += sAir·AttackSpeedStack/2, else stacks reset to 0
    base = 100 if 0
    bonus += GetSpeedBonusFromStat(Speed) = (Speed − 13)/4 if Speed ≤ 21 else floor(Speed/10)
    (rework off: +20 with Haste — dead code, 13)
    disableBow and ranged (tooltip state): base = 100, bonus = 0
    ts  = 1/((100 + bonus)/100)/swift
    ts ×= 1 + (weaponImpair[offhand skill][m] + weaponImpair[body armour skill][m])/100
    rework on and Haste (party buff 8 or potion): ts /= max(1 + 0.10 + 0.002·sHaste, 1)
    before = round(100·ts);  Result = round(base·ts)
    damageMultiplier.[Melee|Ranged] = Result/before          -- ≈ base/100: slow weapons hit harder
    ranged with disableBow: Result = melee delay
then (registration order):
    artifacts 515, 1302, 2024, 2025 worn: Result ×= 0.9 each; Result = max(Result, 0)
                                                               (General/zzzMaw_Artifacts.lua:856-871)
    dragon race: Result ×= 1 + 0.015·s (s = Dragon Ability for breath/ranged, Unarmed for melee)
                                                               (Modules/MawCore/Classes.lua:804-815)
    map affix 26: Result = mround(Result/(1 − p26/100))       (Global/zzMaw_Mapping.lua:19-23)
```

`damageMultiplier` is only set by the first handler, so Swift artifacts and affix 26 change speed without changing
damage per hit, and a dragon's slower attacks are compensated inside its damage formula instead (6.10). The
multiplier is refreshed whenever `GetAttackDelay` runs (every `itemStats`).

### 4.3 Spell delay — `getSpellDelay(pl, spell)` (`General/zzMaw-Stats.lua:162-245`)

```
Assassin: return 2·pl:GetAttackDelay()                                (Modules/MawCore/Classes.lua:448-450)
spell 122 (dragon Fear): return 120
(s, m) = school skill (raw, without item bonus); m == 0: return 150
haste  = floor(Speed/20); enchant = 1.1 if any of slots 0-2 has special 40 else 1
asc    = Learning skill if spell is a damage spell, healing spell or CC spell, else 0
         (Elementalist: floor(Σ_{schools 12-15} s/4))
armour = 1 + (weaponImpair[offhand][m] + weaponImpair[body armour][m])/100
CC spell: return round(oldTable[spell][mSchool]·1.015^(asc − sSchool))              -- no haste, no armour
hasteDiv = rework and Haste active: max(1 + 0.10 + 0.002·sHaste, 1) else 1
delay = round(oldTable[spell][m]/(1 + haste/100)·1.015^asc/hasteDiv/enchant)·armour
Elementalist: delay ×= 1.5; delay /= 1 + 0.05·stacks
spell 123 (Flame Blast): delay = round(pl:GetAttackDelay(true)·1.5)
affix 27: delay /= (1 − p27/100)
return round(delay)
```

`oldTable[spell][m]` = the Delay columns of `Data/Tables/Spells2.txt` (snapshot at `GameInitialized2`, `:148-154`).
Before every cast `Game.Spells[spell].Delay[max(1, mastery)] = getSpellDelay(...)` (`:156-160`); for a Death Knight a
later handler writes `pl:GetAttackDelay()` instead (`Modules/MawCore/Classes.lua:877-886`). Scripted CC casts set the
recovery to `getSpellDelay` directly; a failed CC cast costs 30.

---

## 5. Player → monster: the `DamageToMonster` pipeline

`Modules/MawCore/Damage.lua:1464-1504` declares 36 named stages; `Pipeline:run` executes them in order and stops when
a handler sets `t.Stop` (`Modules/MawCore/Pipeline.lua:99-109`). The pipeline also runs for monster-vs-monster hits and
for 0-damage engine calls (e.g. the zeroed elemental part of a melee swing); most stages gate on `t.Hit.Player` or
`t.Result ~= 0`. `t.Hit = WhoHitMonster()` = `{Player, Object, Spell, Monster, MonsterAction, ...}`.

| # | Stage | Lines | Effect |
|---|---|---|---|
| 1 | context | 89-91 | `t.Hit = WhoHitMonster()` |
| 2 | puppet-zero | 93-98 | multiplayer: puppet target → `Result = 0`, stop |
| 3 | remote-owner-zero | 1169-1193 | multiplayer: hit owned by another client → 0, stop |
| 4 | seraph-on-hit-heal | 108-150 | Seraphim melee heal (8.2); runs on the engine's `Result`, before the reset |
| 5 | elementalist-learning | 155-195 | Elementalist spell progress (6.10) |
| 6 | elementalist-stack-reset | 199-209 | Elementalist melee or arrow hit: stacks = 0 |
| 7 | engine-reset | 214-216 | `Result = t.Damage` (engine resistance discarded) |
| 8 | reveal-nearby | 220-229 | Doom indoors: monsters within 256 shown on the map |
| 9 | monster-vs-monster | 233-241 | monster attacker: `Result = round(getMonsterDamage(att)/3/2^(Res[4]/100))` |
| 10 | cover-flag | 245-258 | melee phys hit by a GM Cover player: next cover roll +0.15 (7.3) |
| 11 | weapon-stun | 266-302 | Mace/Staff Master+ stun (9.4) |
| 12 | stun-death-cleanup | 305-312 | next tick, dead monster: paralysis cleared |
| 13 | fly-removal | 317-329 | `BolsterAmount > 100` or Austerity, not `flyAllowedMaps`: Fly becomes Feather Fall |
| 14 | stun-spell-prime | 334-358 | Stun spell 34 roll (9.3) |
| 15 | mass-distortion | 364-395 | spell 44 rescale (6.7) |
| 16 | sparks-chain | 399-428 | **Lightning Bolt (18)** chain, despite the name (6.7) |
| 17 | weapon-recompute | 444-499 | the melee/bow/blaster base (5.1) |
| 18 | pain-reflection-flag | 503-511 | monster Pain Reflection buff (19) → the reflected hit is `^0.85` (7.4) |
| 19 | res-and-retaliation | 517-589 | kind remaps, stacks, the resistance division (5.2) |
| 20 | dragon-attack | 597-671 | dragon race replacement (6.10) |
| 21 | shaman-on-hit | 674-693 | Shaman melee leech and mana (8.2) |
| 22 | dk-attack | 698-818 | Death Knight replacement and effects (6.10) |
| 23 | assassin-attack | 822-870 | Assassin spell replacement (6.10) |
| 24 | retaliation | 876-903 | Cover-earned Retaliation stacks (7.3) |
| 25 | boss-affixes | 907-956 | Thorn, Reflecting, Adamantite, Swapper, Regenerating (6.12) |
| 26 | survival-gate | 960-964 | dead Survival mode: 0 outside survival maps |
| 27 | legendaries | 973-1130 | enchant/aura adds and class/legendary terms (5.3) |
| 28 | artifact-on-hit | `General/zzzMaw_Artifacts.lua:523-550` | artifact on-hit damage (6.9) |
| 29 | damage-taken | 1134-1139 | legendary 29 stacks: `Result ×= 1 + stacks/100` |
| 30 | map-affixes | 1142-1164 | affixes 23/24 cut, 30 miss, 5/6 reflect (2.8) |
| 31 | friendly-fire-zero | 1197-1202 | setting off and target neither hostile nor shown hostile: 0 |
| 32 | leech | 1207-1326 | 8.1 |
| 33 | track-and-clamp | 1333-1445 | damage recount and status text only; `Result` unchanged |
| 34 | monster-hp | `Modules/MawCore/MonsterHP.lua:90-111` | real-HP ledger → proxy damage (6.14) |
| 35 | final-clamp | 1453-1458 | `Result = min(ceil(Result), 32500)` |
| 36 | publish | 1541 | `events.call("MawMonsterDamage", t)` |

### 5.1 Stage 17, weapon-recompute (`Damage.lua:444-499`)

```
gate: Hit.Player and (kind == Phys or (Object.Spell == 133 and Object.Item.Bonus2 == 3) or Hit.Spell == 135)
      and t.Player and damageMultiplier[idx] exists
if no Object or Hit.Spell == 135 (blaster shot):       -- melee path
    d = round((R(minM, maxM) + R(minM, maxM))/2)          minM/maxM = GetMeleeDamageMin/Max
    Assassin: d −= assassinationDamage(pl, mon, Object)   (6.10)
    mult = damageMultiplier.Melee
else:                                                  -- arrows
    d = round((R(minR, maxR) + R(minR, maxR))/2)
    Assassin: assassinationDamage(...) called for its side effects only
    mult = damageMultiplier.Ranged
Result = d·mult·mightLevelSwap (= 1)
(chance, cm, crit) = getCritInfo(pl, nil, L); crit: Result ×= cm
player Weak: Result ×= 0.5
arrow whose item has special 3 "of Carnage": Result ×= 0.25
```

### 5.2 Stage 19, res-and-retaliation (`Damage.lua:517-589`)

```
Hit.Player and Hit.Spell == Blades (39): kind = Phys
Object.Spell 200 or 201 (Lifedrain, Souldrinker): kind = Dark
res = monRes(kind) (nil → 0)
arrow (Object.Spell 133) and the bow slot holds a Bow and Bow m ≥ 4: res = min(Res[0]%1000, Res[4])
if Result == 0: stop this stage
spear: melee phys hit, main hand Spear, Spear m ≥ 4:
    mapvars.spearDamageIncrease[mon] += (2 + 0.02·sSpear)·damageMultiplier.Melee·(1.5 if two-handed)
legendary 29 holder: unless (melee non-phys) or (AoE spell and U() > 0.4): legendaryDamageTaken[mon] += 1
if kind == Phys: Result ×= 1 + spearDamageIncrease[mon]/100   -- the stack just added counts; any attacker's phys hit
t.RetaliationRes = res
Result = Result/2^(res%1000/100)
```

Both stack tables reset when the monster dies (`General/zzMaw-Stats.lua:936-944`). For a monster-vs-monster hit this
divides a second time (stage 9 already used physical resistance).

### 5.3 Stage 27, legendaries (`Damage.lua:973-1130`)

```
skip if Result == 0 or no Hit.Player
fireRes = mon.Res[0]%1000
melee phys swing (no Object, kind Phys): for hands 0, 1:
    aura  += calcFireAuraDamage(pl, it, fireRes, speedMult=true)          (6.8)
    if special of `it` is a damage enchant: ench += calcEnchantDamage(pl, it, monRes(ench.Type), rand=true)
arrow or blaster shot (Object.Spell 133 or Hit.Spell 135), item in the BOW slot:
    aura = max(aura, calcFireAuraDamage(bow, fireRes, true)); ench += calcEnchantDamage(bow, ...)
Result += aura + ench;  t.ElementalDamage += aura + ench
legendary 17 (melee phys or any object hit):
    x = 0.02·currentRealHP(mon)  (Mass Distortion: 0.02·mon.HP proxy)
    x /= 1 + mon.Res[4]/100                                            -- linear, not 2^
    AoE spell or arrow: x ×= 0.5
    melee: x ×= damageMultiplier.Melee; arrow: ×damageMultiplier.Ranged;
    other spell: DK/Assassin ×damageMultiplier.Melee, else ×1.015^sLearning
    Result += x
Shaman melee phys: Result += max(currentRealHP·0.001·sFire, sFire)/2^(mon.Res[0]%1000/100)
Assassin melee phys: Result += max(currentRealHP·0.001·sWater, sWater)/2^(mon.Res[2]%1000/100)
legendary 21: Result ×= min(1 + 0.05·(active monsters within 512 of the party), 2)       -- every hit type
legendary 14: Result = mround(Result·max(chance, 1)), chance from getCritInfo(pl, nil, L)
legendary 24: next tick, monster dead: HP += 10 % full HP, SP += 5 % full SP
legendary 11: AoE spell or Hit.Spell == 133: RETURN (skips the Shaman line below);
              else next tick, monster dead: RecoveryDelay /= 2
Shaman, spell 1..98 except 44, Result > 0: Result ×= 1 + Σ_{schools 12-18} s/200
```

Note the enchant/aura adds are computed after stage 19, with their own element's resistance, so they are not divided
twice. `t.ElementalDamage` feeds the spell-leech share (8.1).

---

## 6. Player → monster by attack path

### 6.1 Melee, one weapon

Rows (3.1) → `GetMeleeDamageMin/Max` → stage 17 roll × `damageMultiplier.Melee` × crit × Weak → stage 19 spear stacks
and `÷2^(monRes(Phys)/100)` → stage 27 aura and enchant of that hand → leech → ceil. Hit chance 2.3 uses
`GetMeleeAttack`.

### 6.2 Dual wield

- Rows of both weapons are summed into one min/max (one roll per swing); Armsmaster `armsDmg` is halved on each hand.
- Base recovery is the average of both hands; each weapon skill's recovery bonus is paid once (4.2).
- Stage 27 adds both hands' enchants and auras. Each enchant is scaled by `GetPlayerBaseRecovery` = the average base
  recovery of both hands (6.8); each aura by its own item's recovery.
- Dagger crit chance applies per dagger; the Axe GM crit-damage bonus once (2.2).
- Two axes (Minotaur, Dwarf with the race perk): rows ×(1 − 0.1 per two-handed axe).

### 6.3 Unarmed

No weapon rows. Unarmed rows (3.2): attack `skillAttack[Unarmed][m]·s`, damage +`2·s` to min/max; Hammerhands
multiplier on the rows (3.5); base recovery 100, `skillRecovery[Unarmed][m]·s` bonus. The engine's own fist damage is
added by the engine (not covered, 14). The engine's Unarmed GM evasion is suppressed (7.1).

### 6.4 Staff with GM Unarmed

Staff GM: Armsmaster never applies to staves (neither damage, speed nor attack). Instead `armsDmg = sUnarmed·mult`
(mult from Staff skill) **and** the unarmed rows (+`2·sUnarmed` damage, unarmed attack) both apply, and the unarmed
recovery bonus is paid. Hammerhands' multiplier also applies.

### 6.5 Bow

Rows 44-47 (3.1: `bonus += sBow`, skill damage 4 %/point; at GM the flat `+sBow` is taken back, 3.2). Stage 17
ranged path with `damageMultiplier.Ranged`. GM Bow: resistance = `min(Fire%1000, Phys)` (5.2). Stage 27 adds the
bow's enchant and the max of the bow aura. The engine decides how many arrows fly (MAW's Power display assumes two
from Master); each arrow is its own hit. Arrows with "of Carnage" (special 3) explode: the blast goes through stage
17 with ×0.25. Ranged leech is the Ranged column.

### 6.6 Blaster

In a hand: delay fixed 40, `damageMultiplier.Melee = 0.4`, offhand weapon rows disabled, `armsDmg = 0`. Shots
(`Hit.Spell == 135`) use the **melee** min/max and melee multiplier in stage 17. Damage kind Energy has no monster
column, so blaster damage is never resisted. Stage 27 adds the enchant/aura of the item in the bow slot, not the
blaster.

### 6.7 Spells

**Base roll — `events.CalcSpellDamage(t)` (`General/zzMaw-Spells.lua:1937-2040`)**, `t.Skill` = school skill points,
`t.Mastery`, `t.HP` = target's engine HP:

```
spell 44: return HP·(0.15 + 0.005·Skill)                      -- before anything else (no crit, Int, enchant)
spellPowers[spell] missing: keep the engine value
(dMin, dMax, add) = spellPowers[spell]                         (:1892-1933)
caster is a player:
    asc = sLearning (Elementalist: Σ_{12..15} s/4, mastery 4)
    (dMin, dMax, add) = ascendSpellDamage(asc, m, spell):       (:2043-2060)
        e = 1 + GetBuffMultiplier(HASTE, s28, m28) if Empower Magic aura on, else 1      -- Haste's row (13)
        dMin = round(dMin·e); dMax = round(dMax·e·(1 + 0.02·asc)·1.02^asc)
        add = round(add·e·(1 + 0.01·asc²)·1.02^asc)
    Elementalist: dMax = round(dMax·(1 + 0.1·stacks)); add = round(add·(1 + 0.1·stacks))
if 1 < spell < 132 or spell 200/201:
    Result = add + Σ_{i=1..Skill} R(dMin, dMax), or add + spellPowers.dMax·Skill when dMin == dMax
spell 7 Fire Spike: Master ×8/6, GM ×10/6;  spell 200 Lifedrain: Master ×5/3, GM ×7/3
caster class 10/11 (dragon) or Death Knight: return here
(chance, cm, crit) = getCritInfo(pl, "spell")                  -- against round(TL)
Result ×= 1 + max(Int, Per)/1000;  crit: Result ×= cm
for slots 0, 1, 2 (offhand, main, bow), each item present:
    x = (calcEnchantDamage(pl, it, 0, rand=true, isSpell=true) + calcFireAuraDamage(pl, it, 0, false, true))
        ·1.015^asc
    AoE spell: x /= 2.5
    Result += x
```

`spellPowers` (dice per skill point `dMin..dMax`, flat `add`): Fire Bolt 2 {1-2, 8}; Fireball 6 {1-8, 0}; Fire
Spike 7 {1-10, 0}; Immolation 8 {1-30, 10}; Meteor Shower 9 {1-1, 2}; Inferno 10 {1-7, 12}; Incinerate 11 {1-21, 19};
Sparks 15 {1-4, 0}; Lightning Bolt 18 {1-8, 12}; Implosion 20 {1-12, 20}; Starburst 22 {1-1, 7}; Poison Spray 24
{1-3, 5}; Ice Bolt 26 {1-7, 6}; Acid Burst 29 {1-14, 4}; Ice Blast 32 {1-6, 6}; Deadly Swarm 37 {1-5, 8}; Blades 39
{1-7, 7}; Rock Blast 41 {1-8, 8}; Death Blossom 43 {1-2, 4}; Mass Distortion 44 {0.5-0.5, 15} (unused, see above);
Spirit Lash 52 {2-16, 20}; Mind Blast 59 {1-6, 12}; Psychic Shock 65 {1-25, 25}; Harm 70 {1-4, 4}; Flying Fist 76
{1-5, 20}; Light Bolt 78 {1-2, 12}; Destroy Undead 79 {1-45, 45}; Prismatic Light 84 {2-6, 30}; Sunray 87 {1-60, 60};
Toxic Cloud 90 {1-9, 15}; Shrapmetal 93 {1-7, 0}; Dragon Breath 97 {1-28, 0}; Armageddon 98 {1-1, 50}; Souldrinker
99/201 {1-5, 25}; Darkfire Bolt 103 {1-28, 46}; Lifedrain 111/200 {1-22, 0}; Flame Blast 123 {1-25, 0}. These Lua
values, not the `Spells2.txt` dice columns, are what is rolled.

`aoespells = {6, 7, 8, 9, 10, 15, 22, 24, 32, 41, 43, 84, 93, 97, 98, 99, 123}` (`:2094`).

**Then the pipeline** with `t.Damage` = that roll: stage 7 reset, 14-16 spell specials, stage 19 resistance of the
spell's damage kind (the enchant part included: spell enchants are resisted as the spell's element), stage 22/23 class
replacements, 24 retaliation, 25 bosses, 27 legendary 17/21/14 and the Shaman spell multiplier, 29 legendary 29, 30
affix 24, 32 spell leech, 35 ceil.

Categories:

- **Single target** (Fire Bolt, Incinerate, Implosion, Ice Bolt, Acid Burst, Deadly Swarm, Mind Blast, Psychic Shock,
  Harm, Flying Fist, Light Bolt, Destroy Undead, Sunray, Darkfire Bolt): exactly the above.
- **AoE** (`aoespells`): the roll is per target; enchant share ÷2.5; legendary 17 ×0.5; legendary 29 stacks only 40 %
  of the time; minimum leech ÷2.5 (Meteor Shower 9, Starburst 22, Death Blossom 43 a further ÷4); Elementalist
  learning ÷3 (except Sparks and Poison Spray); legendary 11 does nothing.
- **Shotgun / multi-projectile** (Sparks, Poison Spray, Ice Blast shards, Meteor Shower, Starburst, Death Blossom,
  Shrapmetal): every projectile that hits runs the whole pipeline with its own roll.
- **Chain Lightning (18)**: stage 16, when the bolt (`Object.Spell == 18`) has `SpellMastery > 1`, spawns object 2060
  (type 455) at the target, `SpellMastery − 1`, skill = the caster's current Air skill, aimed at the closest living
  monster within 768 other than the one hit. Every link is a full-strength hit; Expert/Master/GM hit up to 2/3/4
  targets. Not in `aoespells`.
- **Mass Distortion (44)**: base `HP·(0.15 + 0.005·s)` on the engine's proxy HP. Stage 15 then
  `Result = Result/mult^0.5·max(1, (mon.Level/250)²)` with `mult` by `Game.BolsterAmount`: 0/50/100 → 1, 150 → 1.4,
  200 → 1.8, 300 → 3, 600 → `3.33·(1 + L/75)` (bosses ×`2·(1 + mon.Level/80)`), other → 1; Austerity ×4. Stage 19
  Earth resistance. The ledger (6.14) converts the proxy-based number to real HP (`×max/FullHP`), so it is a share of
  real current HP.
- **Lifedrain (111) / Souldrinker (99)** are renamed 200/201 on `MonsterAttacked` (`:3781-3791`), are Dark, roll from
  their own `spellPowers`, and leech 10 % of the damage bar plus the spell leech (8.1).
- **Blades (39)** becomes physical in stage 19 (physical resistance, spear stacks apply).
- **DoT**: Immolation (8) is an aura under the buff rework; the engine's party buff 10 ticks and each tick is a spell-8
  hit through `CalcSpellDamage` and the pipeline (tick rate: 14). Toxic Cloud (90) is a slow projectile hit.
- **Stun (34)**: see 9.3; its resistance becomes 0 or 65000 for the tick, both `%1000 = 0`, so its damage is never
  resisted. It has no `spellPowers` row (engine damage).
- **Elementalist** casts: see 6.10.

### 6.8 Weapon enchants and the Fire Aura

**Damage enchants** (`enchantbonusdamage`, `General/zzMaw-Items.lua:2047-2061`): `{min, max, Type, Coeff}`
4 {3,4,Water,0.2}, 5 {9,12,Water,0.3}, 6 {18,24,Water,0.4}, 7 {2,5,Air,0.2}, 8 {6,15,Air,0.3}, 9 {12,30,Air,0.4},
10 {1,6,Fire,0.2}, 11 {3,18,Fire,0.3}, 12 {6,36,Fire,0.4}, 13 {5,5,Body,0.25}, 14 {12,12,Body,0.35},
15 {24,24,Body,0.45}, 39 {20,40,Fire,0.5} spells only ("of Ascension"), 46 {20,40,Fire,0.5} weapons only ("of The
Dragon").

```
enchantDamageRange(it, id) (:2067-2082):
    avg  = GetWeaponLevelDamage(it)·Coeff·1                      -- ENCHANT_DAMAGE_MULT = 1
    k    = (2 if two-handed else 1)·0.5                         -- ENCHANT_FLOOR_SHARE
    lo   = max(avg·min/mean, min·k); hi = max(avg·max/mean, max·k), mean = (min + max)/2
calcEnchantDamage(pl, it, res, rand, isSpell, calcType) (:2125-2155):
    0 if no enchant, or 39 on a weapon hit, or 46 on a spell
    d = rand ? R(round(lo), round(hi)) : (lo + hi)/2
    d ×= 1.5 with legendary 19
    legendary 26: getCritInfo(pl, isSpell ? "spell" : nil) [no level → round(TL)]; damage call and crit: d ×= cm
    d ×= GetPlayerBaseRecovery(pl, it)/100       -- bow: its own recovery; else the average of the held weapons
    return d/2^(res%1000/100)
GetWeaponLevelDamage(it) = getWeaponLevelDamage(ItemLevel(it), twoHanded, GetWeaponFlatDamage(it))   (Appendix A)
```

**Fire Aura** (buff 4 active under the rework), `calcFireAuraDamage(pl, it, res, speedMult, isSpell, calcType)`
(`:4287-4319`):

```
0 if no item, item number 0 or item EquipStat > 2
(s, m) = getBuffSkill(4)          -- only the mastery matters
d = max(GetWeaponLevelDamage(it)·fireAuraDamage[m], fireAuraMinDamage[m]·(2 if two-handed else 1))
d ×= 1.5 with legendary 19; legendary 26 crit as above
d /= 2^(res/100)                  -- res as passed (the pipeline passes Fire %1000; spells pass 0)
speedMult: d ×= getItemRecovery(it)/100
return round(d)
```

### 6.9 Artifact on-hit (`General/zzzMaw_Artifacts.lua:445-550`)

Stage 28. Melee phys swing: both hands; arrow/blaster shot: bow slot. Per artifact in `artifactOnHit` (not broken):

```
(lo, hi) = enchantDamageRange(it, 46, MawArtifactLevel() = TL)
d = R(round(lo), round(hi))·Damage·GetPlayerBaseRecovery(pl, it)/100
d ×= MultVs[monster kind] (×2 vs the listed kinds)
d /= 2^(monRes(DamageKind or Phys)/100)
OnHit side effect (cast Slow/Fireball/Lightning Bolt/Acid Burst at caster power) fires once per hit
Result += d;  non-physical d also counts as ElementalDamage
```

Coefficients: 500 Elsenrail 1 Light; 501 Glomenthal 1 Dark; 503 Judicious Measure 0.8 ×2 Ogre; 504 Elderaxe 0.6 Water;
505 Volcano 1 Fire; 506 Wyrm Spitter 0.8 ×2 Dragon; 507 Guardian 1 Body; 508 Foulfang 0.5 Body; 510 Breaker 1 Body;
523 Snake (Slow only); 525 Finality 1 Fire + Slow; 529 Blade of Mercy 0.5 Air; 538 Mace of the Sun 0.8 ×2 Elemental;
539 Ebonest, 540 Sword of Whistlebone 0.8 ×2 Dragon; 541 Axe of Balthazar 1 Water; 542 Noblebone Bow 1 Phys;
1303 Iron Feather 1.2 Air; 1308 Splitter 0.7 Fire + Fireball; 1309 Ghoulsbane 1 Fire ×2 Undead; 1310 Gibbet 0.9 Fire ×2
Undead/Dragon/Demon; 1312 Ullyses 1.2 Water; 1319 Old Nick 1.1 Water ×2 Elf; 1333 Elfbane 0.8 ×2 Elf; 2021 Thor 0.7 +
Lightning Bolt; 2022 Conan 0.9 ×2 Dragon/Demon; 2023 Excalibur 1 ×2 Dragon; 2025 Percival 0.6 Fire + Fireball; 2035
Hades 2 Water + Acid Burst (and −10 % leech); 2036 Ares 1.4 Fire; 2040 Artemis 1.2 Air.

### 6.10 Class overrides

**Dragon race** (portrait race 5; classes 10 Dragon, 11 Great Wyrm). Sheet (`Modules/MawCore/Classes.lua:715-821`,
handlers registered last):

```
effLevel = lvl; b = getPartyLevel(4) + 1 (= banked levels on the three continents + 1)
if lvl/b > 1.2: effLevel = min(lvl/2, b);  effLevel = min(effLevel, 600 (900 Madness))
fang(k)   = round(((1 + Fang.Damage[m]·s/100)·(2·effLevel + 30)·(1 + Might/1000) + E(Might)·Might/1000)
                  ·k·(1 + 0.015·s))                          s, m = Unarmed; Fang.Damage = {4, 6, 8, 10}
MeleeMin/Max rows = fang(0.75) / fang(1.25)   (engine adds E(Might))
breath(k) = round(((1 + Breath.Damage[m]·s/100)·(20 + 2·effLevel) + E(Might))·(1 + Might/1000)·k·(1 + 0.015·s))
                                                             s, m = Dragon Ability; Breath.Damage = {3, 4, 5, 6}
RangedMin/Max rows = breath(0.75) / breath(1.25)
MeleeAttack row += Fang.Attack[m]·s + 10                      Fang.Attack = {2, 3, 4, 5}
AC += (1 + Scales.AC[m]/100·s)·(effLevel + 40) − s·skillAC[Dodging][m]       Scales.AC = {2, 3, 3, 4} (Dodging s, m)
each resistance += Scales.Res[m]/100·s·(effLevel + 40)                        Scales.Res = {1, 1, 2, 3}
SP from items = 0; delay ×(1 + 0.015·s) (4.2)
```

Pipeline stage 20 (`Damage.lua:597-671`):

```
melee (no Object):
    Dragon Ability s ≥ Unarmed s: knockback push, mult = sFang/mon.Level^0.75, force 800·mult, 60·mult^0.5 ticks
    d = round((R(mn, mx) + R(mn, mx))/2)·1;  crit (target L): d ×= cm   (the crit tag is overwritten, not or'd)
    class 10: SP = min(SP + 10, 60);  class 11: SP = min(SP + 20, 120)
    Result = d/2^(monRes(kind)/100)                 -- no damageMultiplier (dragons have none: it is 1)
breath (kind 50) or Flame Blast (Spell 123):
    d = round((R(rmn, rmx) + R(rmn, rmx))/2); crit: d ×= cm
    spell 123: d ×= 0.7 (m ≤ 2), 0.85 (m = 3), 1 (m = 4) of Dragon Ability
    d = d·0.75 + d·U()·0.25 + d·U()·0.25
    Result = d/2^(min over all monster columns of Res%1000 /100)
```

Dragon classes also skip Int/crit/enchant in `CalcSpellDamage` and never get the GM Dodging roll (7.4); the Speed
roll still applies.
Dragon regen leech: melee leech += `sRegeneration/estimateSkill(L)·0.05` (`General/zzMAW-Skills.lua:1494-1501`).

**Death Knight** (classes 56-58). Sheet: Water and Dark `GV(dkDamageSkill)·s` damage (3.1), attack speed `+sWater`,
phys damage taken `/(1 + 0.01·sBody)`, magic `/(1 + 0.01·sDark)`, leech +10 % melee/+5 % ranged, no SP from items,
spell delay = attack delay. Stage 22 (`Damage.lua:698-818`):

```
spell in DKDamageMult {26 Icy Touch, 29 Frostbite, 32 Ice Bomb, 76 Asphyxiate, 90 Death Coil, 97 Death Breath}:
    d = round((R(mn,mx) + R(mn,mx))/2)·1;  crit (target L)
    d += Σ_{hands 0,1} (calcFireAuraDamage(it, res 0) + calcEnchantDamage(it, res 0, rand=false))   -- averages
    d /= 2^(mon.Resistances[kind] (or Res[4] if nil) %1000/100)
    Result = d·damageMultiplier.Melee;  Weak ×0.5
    Result ×= DKDamageMult[spell][m of its school]:
        26 {1,1,1.2,1.2} Water; 29 {1.5,1.5,1.5,2} Water; 32 {0.75 all} Water; 76 {1.1,1.1,1.1,1.4} Body;
        90 {1,1,1,1.2} Dark; 97 {0.6 all} Dark
kind Phys (melee or arrows):
    active spell 68 Blood Leech: heal bloodLeech = max(FullHP^0.5·sBody^1.5/70·(1 + mBody/4), 2·sBody), SP −6
    active spell 74: twice that, SP −12 (SP may go negative)
    active spell 96 Dark Grasp and SP ≥ 15: SP −15, monster DamageHalved debuff for calcDebuffDuration(1 minute)
        (group 1: no DR); Dark m ≥ 4 also MeleeOnly
    SP += spRegen {56: 10, 57: 15, 58: 20}, ×1.5 if this hit's damage > the monster's current HP
spell 26 with Water m ≥ 2: Slow (power floor(m/2)·2) for calcDebuffDuration(1 minute)
spell 76: Paralyze for calcDebuffDuration(2 minutes) (group 3: DR and boss halving)
```

Spell costs are fixed (`DKManaCost`, `Modules/MawCore/Classes.lua:108-121`); spells are unlocked by school mastery.

**Assassin** (Thief line 34-37). Sheet: Earth `sEarth·(1 + mEarth)` damage stored as `vars.assassinDamage`, attack
speed stacks, spell delay = 2× attack delay, spells cost combo points. `assassinationDamage(pl, mon, obj)`
(`Modules/MawCore/Classes.lua:365-432`), called by stage 17 (melee, subtracted; arrows, side effects) and stage 23:

```
restore = 0.1 + 0.01·sFire; cost = 50 − 5·mFire; spell object (1..99): both 0; any object: both halved
U() < restore: SP = min(FullSP, SP + 15)
next tick, monster dead: SP += (1 + mAir)·5; stacks = min(stacks + 1, 5)
if SP ≥ cost and monster shown hostile:
    arrow (Spell > 100): stacks += 0.5, AttackSpeedStack += 0.5 (cap 5), stack timer 4 game minutes
    melee: stacks += 1, AttackSpeedStack += 1 (cap 5), timer 4 game minutes
    n = monsters within 384 of the target (not dead/removed), mult = min(0.8, (n − 1)·0.2)
    SP −= cost; return assassinDamage·(0.5 if object)·mult
else: return assassinDamage              -- the whole Earth bonus is subtracted
```

Stage 23 for spells in `assassinSpells` (`:69-94`):

```
d = round((R(mn,mx) + R(mn,mx))/2)·1 − assassinationDamage(...); crit (target L)
d += Σ_{hands} (aura(res 0) + enchant(res 0, average)); d /= 2^((Res[kind] or Res[4])%1000/100)
Result = d·damageMultiplier.Melee; Weak ×0.5
Result ×= DamageMult: Fireball 1, Fire Spike 2.5, Lightning Bolt 1.5, Poison Spray 0.75, Acid Burst 3, Stun 1.5,
          Blades 3, Mass Distortion 4 (then ÷2^(Res[3]%1000/100) again); every other listed spell has 0 → 0 damage
StackCost (consumed at cast, refused if short): Fireball 5, Fire Spike 3, Lightning Bolt 5, Poison Spray 3,
          Acid Burst 3, Stun 3, Blades 3, Mass Distortion 4
```

Melee phys hits also add Water `max(currentHP·0.001·s, s)` (5.3). Energy: `(0.6 + 0.2·mWater)·10` SP per second (8.4).

**Elementalist** (62-64). Ascension skill = `Σ_{Fire,Air,Water,Earth} s/4` (damage) and its floor (delay); stacks
`+1` per cast of an offensive spell, decay to `floor(stacks/2)` every half game minute once `max(4·delay, 128)` ticks
pass without casting (`Modules/MawCore/Classes.lua:300-315, 509-539`), reset by any melee or arrow hit (stage 6).
Per stack: dice max and add ×(1 + 0.1·stacks) (rounded), delay ÷(1 + 0.05·stacks) on top of ×1.5, cost +1 base and
+7.5 %. Learning (stage 5): `+= tier^1.5·mon.Level^0.5·PartyCount^0.5` (no party term in Insanity), ÷3 for AoE
except Sparks/Poison Spray; a spell unlocks at `{0, 0, 500, 1500, 5000, 10000, 20000, 40000, 80000, 160000,
320000}[tier]` with school mastery ≥ `{1,1,1,1,2,2,2,3,3,3,4}[tier]`.

**Shaman** (59-61). Sheet: Earth `sEarth·mEarth/2` damage; Spirit melee ×(1 + sSpirit/100); Air damage taken
`/(1 + 0.01·sAir)`; Water flat cut (2.4). Hits: Fire `%HP` add, spell ×(1 + Σ/200) (5.3); Body leech and Mind mana
(8.2); heals ×(1 + Σ_{12..18} s/400) (8.3). Ascension for costs and heals = average of the seven schools; damage still
uses Learning.

**Seraphim** (53-55). Sheet: Mind `sMind·(mMind + 1)/2` damage; attack speed `+sLight·mLight/2`; Spirit flat cut
(2.4). On-hit heal (8.2) and Divine Protection (7.6).

### 6.11 Legendary affixes that touch damage

| # | Effect | Where |
|---|---|---|
| 11 | kill with a single-target, non-arrow hit: recovery halved | 5.3 |
| 12 | stat enchants echo 40 % into their counterparts | 3 (`:2734-2742`) |
| 14 | +10 % crit chance, no cap; damage ×max(chance, 1) | 2.2, 5.3 |
| 15 | lethal hit: HP = full/4, hit = 0, cooldown 150 game minutes | 7.6 |
| 16 | item resistance ×1.5 | 2.4 |
| 17 | +2 % current HP per hit (×0.5 AoE/arrows), ÷(1 + phys res/100) | 5.3 |
| 18 | damage taken ×0.9 | 2.4 |
| 19 | enchant and aura damage ×1.5 | 6.8 |
| 21 | ×(1 + 0.05 per monster within 512), max ×2, every hit | 5.3 |
| 22 | damage taken ×max(0.97^n, 0.5) | 2.4 |
| 23 | successful cover: +3 % HP | 7.3 |
| 24 | kill: +10 % HP, +5 % SP | 5.3 |
| 26 | enchants and aura can crit | 6.8 |
| 27 | leech overheal goes to the most injured member | 8.1 |
| 28 | armour AC ×1.5 | 3.3 |
| 29 | +1 % damage taken per hit, stacking until death | 5.2 |
| 30 | death threshold uses max(full HP, full SP)·mana-shield efficiency | 7.6 |
| 31 | leech heals SP too, both halved | 8.1 |
| 33 | +10 melee weapon skill | (skill hook) |
| 34 / 35 | overheal refunds mana / cuts recovery | 8.3 |

### 6.12 Boss affixes on incoming player damage (stage 25, `Damage.lua:907-956`)

Gate `220 ≤ NameId < 300` and `t.Player`; the affix is the first word of `Game.PlaceMonTxt[NameId]`.
Omnipotent has every effect.

- **Thorn**: kind Phys → `Party[slot]:DoDamage(Result, Phys)`: the current `Result` (after the class overrides, before
  enchant adds) goes to the attacker through the player pipeline as a reflected hit (`^0.85`, 7.4).
- **Reflecting**: kind ≠ Phys → `DoDamage(Result, kind)`; dragon kind 50 is sent as Energy.
- **Adamantite**: `Result = round(max(Result − 4·mon.Level^1.15, Result/4))` (`mon.Level` ≤ 255).
- **Swapper**: for every map monster with HP > 0, active, shown, hostile and not a boss: `Result = 0` and the boss
  swaps positions with it, in sequence. Every player hit is negated while such a monster exists, at any distance.
- **Regenerating**: `mapvars.regenerating[mon] += 1` (hits count; −1 after death), feeds 8.5.

### 6.13 Monster vs monster

Stage 9: `round(getMonsterDamage(attacker)/3/2^(target.Res[4]%1000/100))`; stage 19 then divides by
`2^(monRes(kind)/100)` again. Party hits on monsters that are neither hostile nor shown
hostile are zeroed in stage 31 while the "Damage on Friendly Units" setting is OFF, its default
(`General/zz_Maw-initialize.lua:540`).

### 6.14 Real monster HP and the final clamp

`MonsterHP.apply(mon, realMax, fraction)` (`Modules/MawCore/MonsterHP.lua:63-85`): engine `FullHP = min(realMax,
32000)`, rounded to tens above 1000; a ledger `{max, hp, proxy}` exists only when `realMax > 32000`. Stage 34:

```
no ledger entry: nothing
reconcile: engine HP changed outside the pipeline → hp += (mon.HP − proxy)·max/FullHP (clamped)
real = Result (spell 44: ×max/FullHP)
hp −= real; hp ≤ 0: Result = 32500 (kill), entry removed
else: target = max(ceil(hp/max·FullHP), 1); Result = max(mon.HP − target, 0); proxy = mon.HP − Result
```

Stage 35 then `Result = min(ceil(Result), 32500)`. The engine subtracts the integer `Result` from the proxy HP.

---

## 7. Monster → player

### 7.1 Before the pipeline: target, hit roll, cover

`events.PlayerAttacked` fires when a monster attack or missile reaches the party, before the engine resolves it.
MAW's handlers:

- **Cover and Fixator** retarget the hit (`General/zzMAW-Skills.lua:1222-1313`, 7.3).
- **Mist Form** (`General/zzMaw-Stats.lua:705-717`): if the target's player buff 26 is active, its expiry is saved, set
  to 0 for one tick (so the engine's own Mist Form rule does not apply) and restored next tick; while the restore is
  pending the pipeline quarters physical monster damage (7.4).
- **Unarmed GM evasion off** (`General/zzMaw-Stats.lua:1385-1394`): the next two `GetSkill(Unarmed)` calls return 0.
  Inferred purpose: the engine's Unarmed-GM dodge roll never succeeds.
- **MM6 projectiles** (`General/zzMaw-Monsters.lua:3884-4008`): for restored MM6 projectile types MAW picks the target
  itself (random conscious member, its own cover rules, 7.3) and calls `DoDamage(10000, Attack1.Type)` with a custom
  attacker record, which the pipeline recomputes.

**Engine hit roll** (`General/zzMaw_MonsterHit.lua:12-31`, hook `0x425893`):
`hit = chanceToBeHit(Speed, L) ≥ U()`, `chanceToBeHit = 1/(1 + Speed/(100 + estimateStat(L))·0.5)`
(`Formulas.lua:76-80`). Monster AC, level and the vanilla formula are not used.

### 7.2 The `DamageToPlayer` stages (`Modules/MawCore/Damage.lua:1970-1983`)

| # | Stage | Lines | Effect |
|---|---|---|---|
| 1 | remote-owner-zero | 1959-1968 | multiplayer object of another client: 0, stop |
| 2 | item-refresh | 1561-1565 | next tick: `mawRefresh` (hits can break equipment) |
| 3 | death-seed-mark | 1568-1573 | Madness: start the "loading in combat counts as death" timer |
| 4 | damage-recompute | 1583-1800 | the whole base computation (7.4) |
| 5 | boss-affixes-player | 1803-1841 | boss on-hit effects (7.5) |
| 6 | survival-gate | 1844-1848 | dead Survival mode |
| 7 | map-affixes-player | 1938-1956 | affixes 1, 2, 10 (7.6) |
| 8 | legendaries-and-shields | 1859-1935 | mana shield, legendary 15, Divine Protection, death thresholds (7.6) |

Shaman/Seraphim flat cut, legendaries 18 and 22 are inside `calcMawDamage` (2.4), not here.

### 7.3 Cover and Retaliation

```
required mastery: 1 if action 0/1 and that attack's Type == Phys; 3 if action 2 (spell 1); else 2
attacker is a Fixator boss: target = conscious member with the lowest max HP; no cover roll
candidates i: Cover s > 0, toggled on (vars.covering[i], key P), m ≥ required, i ≠ target (solo: the target itself)
    chance = min(0.10 + 0.01·s, 0.40), +0.15 when the one-shot flag from DamageToMonster stage 10 is set
each candidate rolls U() < chance; among successes the highest CURRENT HP covers (first on ties)
covered: Shield sound/animation on the original target
    party: the coverer takes the hit (t.PlayerSlot = coverer)
    solo:  the target keeps it; DamageState solo-cover flag → ×0.5 in 7.4
    legendary 23 on the coverer: +3 % max HP
    Retaliation (skill 53): U() ≤ s/100 → stacks + 1, capped at 1 (GM: 3), time = now
```

MM6-projectile variant (`General/zzMaw-Monsters.lua:3935-3995`): Expert required regardless of attack type, chance
`1 − (0.99^s − 0.05)`, bonus +0.30, best = highest HP fraction, and the loop never considers the last party slot
(13). Retaliation is the same.

Retaliation is spent on the coverer's next hit (DamageToMonster stage 24, `Damage.lua:876-903`):

```
valid if stacks > 0 and stack time + 5 game minutes > now; below GM count stacks as 1
(DPS1, _, _, vit) = calcPowerVitality(pl, false)                          (General/zzMaw-Stats.lua:1189-1346)
Result += round(DPS1^0.25)·round(vit^0.25)·sRetaliation·stacks/2^(RetaliationRes%1000/100)
U() < 0.25·stacks: monster Paralyze (buff 6) expires at now + 1 game minute (bosses 0.5 minute), no DR, overwrites
next tick: RecoveryDelay ×= max(1 − 0.3·stacks, 0); stacks = 0
```

`calcPowerVitality` against `ref = round(TL)`:

```
DPS1 = round(( (mn+mx)/2·(1 + min(cc,1)·(cm − 1)) + Σ_{hands 0,1, EquipStat ≤ 2} (enchAvg + auraAvg + artifactAvg) )
             /(delay/60)·hitChance(atk, ref)·damageMultiplier.Melee·max(cc, 1))
       cc, cm = getCritInfo(pl, nil, ref); enchAvg = calcEnchantDamage(.., res 0, rand false, "power");
       auraAvg = calcFireAuraDamage(.., res 0, speedMult false, "power")
vit  = round(fullHP'/reduction)
       fullHP' = (GetMaxHP + [mana shield on] getMaxMana·round(eff·100)/100)·(1 + dodging/200)
                 dodging = sDodging + 10 at GM, else 0; dragons: no dodge term
       r_k = 1 − calcMawDamage(pl, k, 10000, false, ref, ratioOnly=true)/10000 for k in Phys, Fire, Air, Water, Earth,
             Mind, Body, Energy
       reduction = ((1 − r_Phys)·0.5 + Σ_{6 elements}(1 − r_k)·0.0625 + (1 − r_Energy)·0.125)·chanceToBeHit(Speed, ref)
```

### 7.4 Stage 4, damage-recompute (`Damage.lua:1583-1800`)

```
data = custom attacker (MM6 projectiles) or WhoHitPlayer()
reflected hit (Thorn, Reflecting, affix 5/6 DoDamage): Result = Result^0.85, return      -- engine-mitigated input
monster Pain Reflection hit (flag from DamageToMonster stage 18): Result = Result^0.85, return
player Pain Reflection buff (10) active: flag "reflecting" (the reflected hit's DamageToMonster stage 18 skips)
party arrow (Spell 133) hitting a party member: keep the engine value, return
party spell 1..132 hitting a party member (own AoE too close):
    (dMin, dMax, add) = ascendSpellDamage(caster sLearning, mLearning, spell)
    d = (add + Σ_{i=1..Object.SpellSkill} R(dMin, dMax))·max(1 − dist(party, object)/512, 0)
    Result = calcMawDamage(pl, kind, d, false, caster.LevelBase); return          -- no crit, no Int, no enchants
no monster attacker (traps, hazards, falls, drowning, objects):
    if kind ∉ {Phys, Water} or indoors:
        d = getMonsterDamage(nil, TL)                     -- model damage at the party's total level, by difficulty
        object with SpellType 15: d /= 3
        d ×= min((11 − 2·mPerception)/10, 1)              -- ×1, 0.9, 0.7, 0.5, 0.3 for none..GM
        Result = calcMawDamage(pl, kind, d)               -- mitigated at the player's own LevelBase
    return                                               -- outdoor Phys/Water (falls, drowning): engine value
mon = attacker; L = getMonsterLevel(mon)
dodge = 1 − 1/(1 + (sDodging + 10)/200) at Dodging GM, else 0; dragons 0
roll = U()
speedDodged = (action ∈ {2, 3} or data.Object) and not (chanceToBeHit(Speed, L) ≥ U())
if dodge ≥ roll or speedDodged: Result = 0, face expression 33, return
D = getMonsterDamage(mon)                                                            (2.6)
action 1 (Attack 2): t.Damage = D·avg(Attack2)/avg(Attack1), kind = Attack2.Type, avg = add + count·(sides + 1)/2
action 0 (Attack 1): t.Damage = D, kind = Attack1.Type
(actions 2/3 keep the engine's t.Damage here)
t.Damage == 0 and Result == 0: return
kind Phys and this player's Mist Form restore pending: t.Damage ×= 0.25
affix 14 and U() < p14: kind = Energy
object hit with 0 < Spell < 100: t.Damage = D·monsterSpellMultiplierList[Spell] (×1 if absent)
t.Damage = round(t.Damage)
t.Damage ×= (R(75, 125) + R(75, 125))/200
t.Damage ×= min over the attacker's active debuffs {DamageHalved (Dark Grasp) 0.7, ShrinkingRay 0.7}
Result = calcMawDamage(pl, kind, t.Damage, false, L)                                 (2.4)
solo cover flag: Result ×= 0.5
disease: Disease3 ×2, else Disease2 ×1.5, else Disease1 ×1.25; solo: factor = (factor − 1)/2 + 1
attacker NameId > 220 and Exploding (or Omnipotent): Result /= 2;
    every member (target included): HP −= calcManaShield(member, Result/PartyCount); face animation 24
```

`monsterSpellMultiplierList` (`General/zzMaw-Monsters.lua:1937-1963`): Fire Bolt 0.75, Lightning Bolt 0.95, Poison
Spray 0.5, Fireball 0.5, Light Bolt 1.1, Incinerate 1.35, Acid Burst 1.15, Ice Blast 0.75 (listed twice, 1.2 then
0.75; the later key wins), Blades 1.1, Rock Blast 0.6, Sparks 0.5, Implosion 0.8, Mass Distortion 0.4, Shrapmetal 0.4,
Mind Blast 0.8, Dragon Breath 0.7, Harm 0.75, Toxic Cloud 1.15, Psychic Shock 1.25, Meteor Shower 0.3, Deadly Swarm
0.85, Spirit Lash 0.65. Monster spells ≥ 100 keep the engine's (vanilla) damage.

Mitigation level summary: monster hits use the attacker's `getMonsterLevel`; traps the victim's `LevelBase`; party
friendly fire the caster's `LevelBase`.

### 7.5 Stage 5, boss affixes on the player (`Damage.lua:1803-1841`)

Attacker `220 ≤ NameId < 300`; the effects are direct field writes, so condition immunities (legendary 13, enchant
protections, `DoBadThingToPlayer`) do not block them:

| Affix | Effect |
|---|---|
| Summoner | `U() < 0.4` or kind Phys: a family monster (75 % tier A, 25 % B) spawns between party and boss |
| Venomous | `Poison3 = now` |
| Plagueborn | `Disease3 = now` |
| Fixator | `Weak = now` (and targeting, 7.3) |
| Swapper | party and boss swap positions and facing |
| Puller | `evt.Jump` towards the boss (ZAngle 128, speed 1000) |
| Exploding | 7.4 |
| Leecher | timed drain, 7.8 |
| Omnipotent | all of the above |

### 7.6 Stages 7 and 8

```
map affixes (attacker = monster unless a multiplayer puppet):
    affix 1, monster, Result > 0: Result ×= 1 + p1/100
    affix 2 (any source, traps included): U() < p2/100 → Result ×= 2
    affix 10, monster, Result > 0: Result += FullHP·p10/100
legendaries and shields:
    Result = calcManaShield(pl, Result)                               (Global/zzMaw_Legendaries.lua:61-102)
        (s, m) = Mana Shield (51); active when s > 0 and toggled on for the slot (key M)
        eff = 5 if s == 50 else 1 + min(s, 50)^1.4/60
        absorb = Result·{0.25, 0.5, 0.75, 1}[m]; cost = round(absorb/eff)
        absorb = min(absorb, SP·eff); Result = round(Result − absorb); SP = max(SP − cost, 0)
    legendary 15, conscious and alive, Result ≥ HP, cooldown over:
        HP = FullHP/4; cooldown = now + 150 game minutes (5 real minutes); Result = 0
    Seraphim, conscious and alive, Result ≥ HP, cooldown over:
        HP += round(GetMaxHP·0.25); cooldown 150 game minutes; Result = min(Result, HP − 1)
    BolsterAmount ≥ 300, next tick:
        full = GetFullHP (legendary 30: max(FullHP, FullSP)·manaShieldEfficiency)
        HP < −full: Dead, SP = 0;  HP < −2·full: Eradicated
        Insanity with enableDisintegrate, HP < −10·full, more than one member: character dismissed ("Disintegrated")
```

The pipeline's `Result` is a float; the engine subtracts it as an int (inferred truncation).

### 7.7 Thorn, Reflecting and map reflection

The reflected amount is `DoDamage(x, kind)` on the attacker: the engine runs its own `CalcDamageToPlayer` on `x`
(vanilla MM8 handling of that kind), then MAW's stage 4 returns `engineResult^0.85` without any MAW mitigation.
Stages 5-8 still run on it (mana shield, death thresholds). `x` is the hit after the class overrides and before
enchant adds (bosses), or after affixes 23/24 with the affix share removed (`hit·(1 − p/100)` for affixes 5/6).

### 7.8 Damage over time on the party

- **Poison** (`General/zzMaw-Items.lua:1495-1569`, every real second): Poison3/2/1 deal
  `ceil(FullHP·{1 %, 0.5 %, 0.25 %})·mult`, `mult = BolsterAmount/100` (×2 Insanity, ÷2 solo), never below HP 1. A
  new poisoning sets the counter to 25 (+5 per repeat, cap 50; 20 when the condition appears without the event); the
  condition ends when the counter reaches 0.
- **Leecher boss** (`General/zzMaw-Monsters.lua:3390-3432`, every 0.5 s): within 1500, `k = ((1500 − d)/1500)²`
  (×4 turn-based): HP −= `floor(acc + FullHP·k·0.05)` (not below 1), SP −= `floor(acc + SP·k·0.05)`, fractions kept.

### 7.9 Solo rules in combat

Cover halves the hit instead of redirecting; disease amplification halved; poison DoT halved; scripted CC durations
×2 (engine-path pre-check ×3); the Cover/Retaliation "not yourself" rule is lifted.

---

## 8. Leech, healing, regeneration

### 8.1 Leech (DamageToMonster stage 32, `Damage.lua:1207-1326`)

```
gate: Hit.Player and Result > 0 (after friendly-fire zero)
refHP = HPtable[B-tier id of mon.Id]
full  = GetMaxHP(pl) (legendary 31: getMaxMana(pl))
counted = min(Result, realMax(mon)); elem = min(ElementalDamage, counted)       -- no leech from overkill
base = counted/refHP·full; elemHeal = elem/refHP·full; both ×(1 − p32/100); phys = base − elemHeal
heal = 0; floor = 0
kind Phys, melee:  heal = phys·(L.Melee + dragonRegenLeech) + elemHeal·L.Spell
                   floor = full·(L.Melee + dragonRegenLeech)/5·pl:GetAttackDelay()/100
kind Phys, arrow:  heal = phys·L.Ranged + elemHeal·L.Spell; floor = full·L.Ranged/5·pl:GetAttackDelay(true)/100
Hit.Spell 200 (Lifedrain): heal = 0.1·base, spell := 111;  201 (Souldrinker): heal = 0.1·base, spell := 99
0 < spell < 132: heal += base·L.Spell; floor = full·L.Spell/5·getSpellDelay(pl, spell)/100
                 AoE: floor /= 2.5; spells 9, 22, 43: floor /= 4
Death Knight, spell 90 (Death Coil): heal += 0.2·base·(1.5 if Dark m == 3)
heal ≥ 0: heal = ceil(max(heal, floor)) else heal = floor(heal)                  -- Hades' drain is not floored
legendary 31: heal /= 2; SP = min(getMaxMana, SP + heal); heal = heal/full·GetMaxHP
overheal = round(HP + heal − full); HP = min(full, HP + heal)
legendary 27, overheal > 0: the lowest-HP-fraction member gets `overheal`
```

`L.*` is the leech table (3.7); `dragonRegenLeech = sRegeneration/estimateSkill(L)·0.05` for dragons.

### 8.2 Class on-hit heals

- **Seraphim** (stage 4, before the engine reset, melee phys, engine `Result ≠ 0`):
  `heal = round(sBody^1.3·mBody·2·damageMultiplier.Melee·(1 + Per/1000))` to the member with the lowest HP fraction;
  clears Unconscious if HP > 0.
- **Shaman** (stage 21, melee phys, `Result > 0`): `SP = min(SP + sMind^1.25, getMaxMana)`;
  `HP = min(HP + max(round(FullHP^0.5·sBody^1.5/70·(0.5 + mBody/2)), sBody), FullHP)`.
- **Death Knight**: Blood Leech, Superior Blood Leech, SP regen per hit (6.10).

### 8.3 Healing spells

```
heal = (Base[m] + Scaling[m]·s)·(1 + Per/min(1000 + 3·lvl, 4000))·(1 − p31/100)        -- no crit
(Scaling, Base) = (round(scaling·(1 + 0.02·asc)·1.015^asc), round(base·(1 + 0.01·asc²)·1.015^asc))
asc = Learning skill (Elementalist: Σ_{12-15} s/4; Shaman: Σ_{12-18} s/7, then Base and Scaling ×(1 + Σ_{12-18} s/400))
```

`getBaseHealingSpells` (`General/zzMaw-Spells.lua:2334-2353`), N/E/M/GM, Base + Scaling per point:

| Spell | Base | Scaling | Insanity Base | Insanity Scaling |
|---|---|---|---|---|
| 49 Remove Curse (Spirit) | 0/10/20/30 | 0/4/6/8 | 0/20/40/60 | 0/8/12/16 |
| 54 Shared Life (pool) | 0 | 0/0/7/9 | 0 | 0/0/7/9 |
| 55 Resurrection | GM 150 | GM 21 | GM 450 | GM 50 |
| 68 Heal (Body) | 4/8/12/16 | 2/3/4/6 | 12/24/36/48 | 6/9/12/15 |
| 74 Cure Disease (Body) | 0/0/25/40 | 0/0/7/10 | 0/0/50/100 | 0/0/16/25 |
| 77 Power Cure (party) | GM 15 | GM 4 | GM 50 | GM 12 |

Application (`General/zzMaw-Spells.lua:177-543`): 49 and 74 heal the target up to max; 55 also revives
(`HP = max(HP + heal, heal)` next tick when dead); 68 assumes the engine heals its vanilla `5 + (m + 1)·s` and adds
`round(heal − (5 + (m + 1)·s))` without a max-HP cap (13); 77 likewise with `10 + 5·s`, capped. Quick-cast heals
target the member with the lowest HP fraction (`processAutoTargetHeal`, `:1182-1249`). Legendary 34 refunds
`floor(cost·overheal/heal)` SP; legendary 35 sets the recovery to `floor(delay·(1 − overheal/heal/2))`.

### 8.4 Regeneration and meditation (`MawRegen`, `General/zzMAW-Skills.lua:1384-1492`, every 0.1 s)

```
per member with condition < 14, 17 or 18:
    mult = 1 if HP dropped since the last tick or within the last 200 ticks (20 s), else 2;  ×4 out of combat
           (out of combat = neither enemy detector colour); affix 22: timeMultiplier ×(1 − p22/100)
    HP: acc += getBuffHealthRegen(pl)/10·mult; HP = min(Full, HP + floor(acc)); acc %= 1
    getBuffHealthRegen:
        rate = {0.05, 0.075, 0.10, 0.10}[mRegeneration]; hpPerSec = rate·sqrt(getPlayerEstimatedHealth(s^1.4)·Full)
        GM: ×(1 + (1 − max(HP/Full, −1))²)
        + Full·0.002 per worn special 37/44/50/54/66 or regen artifact
        + Regeneration (71) active: max(Full^0.5·(cl^0.65·(1 + 0.05·s))^1.25·0.005, Full^0.5·sB^1.25·(mB + 1)/1000)
          (s, cl = caster skill and level from getBuffSkill(71); sB, mB = the player buff's stored skill)
    SP (Insane excluded; under the rework only with a mana pool):
        meditation: pool = Full or ceil(Full·(1 − reserved)^0.5) with buffs reserving `reserved` of it
                    perSec = {0.02, 0.025, 0.03, 0.04}[m]·sqrt(getPlayerEstimatedMana(s^1.4/2)·pool)
                    legendary 20: ×(1 + reserved)
        acc += (perSec/10 + Full·0.0002 per SP-regen artifact)·mult
             + Meditation aura (56), classes outside {10, 11, 34-37, 56-58}:
               (pool^0.35·estimateSkill(casterLevel)^1.4·0.001 + 0.1)·mult·(1 + 0.02·s)
             + dragon class 10: 0.2·mult, class 11: 0.5·mult
             + Assassin: (0.6 + 0.2·mWater)·10/10 (no mult)
        SP = min(Full, SP + floor(acc)), capped by the current mana pool under the rework
```

The engine's own `Regeneration` event additionally gets `+max(Full·0.01 − 1, 0)` HP per worn special 37/44/50/54 and
SP per 38/47/55 (`General/zzMaw-Stats.lua:670-689`); its tick interval is the engine's.

### 8.5 Monster regeneration

- **Regenerating boss** (`General/zzMaw-Monsters.lua:3585-3601`, every 0.1 s, only after it has been hit):
  `mon.HP += FullHitPoints·0.01·0.99^hits/(1 + mon.Level/50)` on the engine proxy (the ledger reconciles), ×elapsed/12.8
  in turn-based.
- **Map affix 7** (`:3604-3609`) reads an undefined global `mon` (13).

---

## 9. Crowd control

### 9.1 CC table (`CCMAP`, `General/zzMaw-Spells.lua:1337-1351`)

| Spell | Duration | School / resistance | Debuff | Group |
|---|---|---|---|---|
| Stun (34) | 2 min | Earth | engine stun | 9.3 |
| Slow (35) | 6 min | Earth | Slow | 1 |
| Charm (Mind, id 60) | 10 min | Mind | Charm | 2 |
| Charm (`const.Spells.Charm`, Dark Elf) | 10 min | Dark Elf ability / Mind | Charm | 2 |
| Berserk (62) | 4.5 min | Mind | Berserk | 2 |
| Mass Fear (63) | 3 min | Mind | Fear | 2 |
| Fear (122, dragon ability) | 4 min | Mind | Fear | 2 |
| Enslave (66) | 5 min | Mind | Enslave | 2 |
| Paralyze (81) | 3 min | Light | Paralyze | 3 |
| Shrinking Ray (92) | 4 min (flat) | Dark | ShrinkingRay, power 2 | 1 |
| Dark Grasp (96) | 6 min | Dark | ArmorHalved, Slow, DamageHalved, MeleeOnly | 1 |
| Turn Undead (48) | 5 min | Spirit | Fear (undead only) | 2 |
| Control Undead (94) | 10 min | Dark | Enslave (undead only) | 2 |

Durations are game minutes (2 real seconds each). `getCCDiffMult` exists but its result is never used (13).

### 9.2 Duration and diminishing returns

```
applyCCDebuff(mon, cc, pl, spell, res, engineApplied)                    (:1406-1427)
    d = cc.Duration·{0.5, 0.65, 0.8, 1}[mSchool]       (Shrinking Ray: ×1)
    spell ≠ 122: d ×= 1.015^sLearning/(1 + res/100)    -- res = raw monster resistance of cc.DamageKind
    solo: d ×= 2
    d = calcDebuffDuration(mon, cc, d)
    engineApplied: expire = min(expire, now + d) else expire = max(expire, now + d)
calcDebuffDuration(mon, cc, d)                                            (:1817-1852)
    group of the first debuff: Slow, ArmorHalved, DamageHalved, MeleeOnly, ShrinkingRay → 1;
                               Fear, Charm, Berserk, Enslave → 2; Paralyze → 3
    group 1: return d                                   -- no DR, no boss halving
    ratio = time this monster spent under this group's CC in the last 10 game minutes (20 s) / 10 game minutes
    mult  = 0 if ratio ≥ 0.6; 0.25 if ≥ 0.45; 0.5 if ≥ 0.3; 0.75 if ≥ 0.15; else 1
    mult == 0: return 0 (not recorded)
    d ×= mult; boss (220 ≤ NameId < 300): d /= 2
    record [now, now + d] in the monster's history; return d
```

Scripted casts (Slow, both Charms, Berserk, Paralyze, Enslave, Dark Grasp, Control Undead; `castCCSpell`,
`:1486-1544`) always land on one target (mouse target, else the visible hostile one whose debuff expires first, within
4800); the effect shows only if the duration is > 0. Engine-path CC (Mass Fear, the dragon's Fear, Turn Undead;
`:1581-1656`): for one tick every monster's resistance to the spell becomes 0 and `Level` 0 when
`checkDebuffDuration(mon, cc, Duration·(3 if solo)) > 0`, else 65000 (resisted); Turn/Control Undead on a non-undead:
65000. Next tick (100 ticks for Dark) resistances/levels are restored and every monster whose debuff grew is capped
with `applyCCDebuff(..., engineApplied=true)`. Shrinking Ray applies on projectile impact to the target plus
`max(m, 1) − 1` more monsters within 512 (preferring unaffected ones) (`:1660-1732`).

### 9.3 Stun spell (34)

Stage 14 (`Damage.lua:334-358`): `newLevel = calcEffectChance(mon.Level, Res[Earth], sEarth, 0.01, mon)` with
`calcEffectChance = max(round((((Level/4 + res) + 30)/(1 + s·0.01) − 30)·4), 0)`, ×2 for bosses (`:1855-1865`);
`hit = 30/(30 + newLevel/4)`, ×(1 − p13/100). `hit > U()`: Earth resistance 0 and `Level` 0 for one tick (the engine
applies its stun); else Earth resistance 65000 (the engine resists). Either way stage 19 reads `res%1000 = 0`.

### 9.4 Weapon stun and other monster debuffs

- **Mace/Staff** (stage 11, `Damage.lua:266-302`): melee phys hit, main-hand Mace (or Staff) at Master+:
  `chance = s/estimateSkill(L)·{0.15 Mace, 0.10 Staff}·damageMultiplier.Melee/min(1 + L/150, 3)`;
  `chance > U()`: Paralyze (buff 6) for `calcDebuffDuration(2 minutes, halved at exactly Master)` (group 3: DR and
  boss halving), extending, never shortening.
- **Retaliation**: 7.3. **DK**: Icy Touch Slow, Asphyxiate Paralyze, Dark Grasp (6.10).
- **Monster damage debuffs**: DamageHalved (Dark Grasp) and ShrinkingRay each make the monster deal ×0.7; they do not
  stack (`Damage.lua:1575-1578`).

---

## 10. Order of operations and rounding

**Player → monster, melee/bow:** roll `round((R + R)/2)` on integer min/max → ×`damageMultiplier` → ×crit (crit mult
pre-rounded to 0.01) → ×0.5 Weak → ×0.25 Carnage blast → ×(1 + spear %) → ÷`2^(res%1000/100)` → class replacement
(dragon/DK/assassin) → + Retaliation → boss (Adamantite `round`, Swapper 0) → + aura (`round`) + enchants (float) +
legendary 17 + Shaman/Assassin %HP → ×legendary 21 → `mround(×max(chance,1))` legendary 14 → Shaman spell mult →
+ artifact on-hit → ×(1 + legendary 29 %) → affixes 23/24, 30 → friendly zero → leech → ledger → `ceil`, ≤ 32500.

**Player → monster, spells:** dice per skill point with `round`ed ascended dice and add → mastery factor (Fire Spike,
Lifedrain) → ×(1 + max(Int, Per)/1000) → ×crit → + Σ slots (enchant + aura)·1.015^asc (÷2.5 AoE) → pipeline as above
from stage 7 (no weapon recompute).

**Monster → player:** `getMonsterDamage` → attack-2 ratio → ×0.25 Mist → spell multiplier → `round` → ×roll
(0.75-1.25, triangular) → ×0.7 debuff → GM Shield → AC (`round`) or class cut, Shield buff, GM Shield again,
resistance (`round`) → floor 10 % of the pre-shield input → ×0.9 legendary 18 → ×legendary 22 → − flat class cut
(≥ 25 %) → ×0.5 solo cover → ×disease → Exploding split → boss on-hit → ×affix 1, ×2 affix 2, + affix 10 → mana
shield (`round`) → cheat-death checks → engine `trunc` → death thresholds next tick.

**Clamps:** monster resistances ≤ base + affix12 + 200 and ≤ 999; Shield buff ≥ 0.7; crit chance ≤ 1 (no cap with
legendary 14); hit chance 0.25-1; per-hit damage to monsters ≤ 32500 proxy points; Mass Distortion's factor is
`max(1, ...)`; leech counts at most the monster's max HP.

---

## 11. Worked examples (golden values)

### 11.1 Method

The values were computed by loading MAW's own code under Lua 5.4: `Modules/MawCore/{Formulas, ItemLevel, Pipeline,
DamageState, MonsterHP, Estimates, Damage}.lua` whole, and these line ranges verbatim: `General/zzMaw-Items.lua`
444-561, 574-878, 889-893, 2047-2155, 2555-3486, 4283-4319, 4390-4404, 4555-4607; `General/zzMAW-Skills.lua` 24-174,
402-617, 1494-1501; `General/zzMaw-Stats.lua` 5-12, 52-142, 162-245, 253-267, 296-298, 719-1158, 1462-1530;
`General/zzMaw-Spells.lua` 80-83, 1018, 1337-1351, 1892-2094, 2655-2692; `General/zzMaw-Monsters.lua` 18-40,
1884-1895, 1938-1962, 4370-4373; `General/zzzMaw_Artifacts.lua` 48-286, 445-550; `General/zzzMaw_Experience.lua`
278-290; `General/zzClasses.lua` 455-469; `Global/zzMaw_Legendaries.lua` 61-102; `Modules/MawCore/Classes.lua`
715-755; MMExt constants from `reference/mmmerge/Scripts/Core/ConstAndBits.lua`. `buffPower` is the
`Global/zzMaw_Mapping.lua` table; `oldTable` comes from `Data/Tables/Spells2.txt`. The DamageToMonster and
DamageToPlayer pipelines were run stage by stage with the real `Damage.pipe`/`Damage.playerPipe` objects.

**RNG convention for golden tests:** every integer draw `R(a, b)` returns `floor((a + b)/2)`; every float draw `U()`
returns a fixed `u`. "No crit" runs use `u = 0.999`, "crit" runs `u = 0.0`. Monster-side runs use `u = 0.5` and force
the Speed roll to "hit" (otherwise `0 ≥ 0` would count as a dodge). Engine `trunc` is applied to sheet values.

**Common setup.** Single character, `vars.MMLVL = {L, 0, 0, 0}` (so `TL = L` and the spell/enchant crit reference level
is `L`), buff rework ON, no buffs, no legendaries, no map affixes, monster at full HP, no ledger (HP < 32000).

**Monster.** Generic B-tier (`Id % 3 == 2`, `NameId 0`), `totalLevel = L`, resistances Fire 50, Phys 10, Dark 20,
all others 0. Attack 1 physical melee; its dice do not matter (MAW replaces them).

| | L50 MAW (diff 3) | L150 MAW | L50 Hell (diff 5) | L150 Hell |
|---|---|---|---|---|
| HP (`getMonsterHealth`, also `HPtable`) | 552 | 3859 | 861 | 6162 |
| `getMonsterDamage` | 156.2788 | 1263.4933 | 190.3438 | 1558.7955 |

**Champion** (class 19, HP 35 + 8/level), built from the MAW-difficulty balance model and kept unchanged for Hell:
all seven stats `round(estimateStat(L))`; Sword and Bow `round(1.5·estimateSkill(L))` at the mastery that skill buys;
Armsmaster, Chain and Bodybuilding `round(estimateSkill(L))` (Bodybuilding capped at Master). Gear without enchants,
all at item level L (`MaxCharges = L/5`): two-handed sword (3 dice, family of one → ladder tier 3.5), longbow
(5 dice), chain mail (AC 30, `referenceAC` 30). The sheet below is the output of the real `itemStats`.

| | L50 | L150 |
|---|---|---|
| Stats (E) | 89 (17) | 279 (55) |
| Sword/Bow, Armsmaster/Chain/Bodybuilding | 17 GM; 11 GM (BB Master) | 40 GM; 26 GM (BB Master) |
| Sword `getWeaponDamageForLevel` (wDmg, wDice, wFlat) → bonus, sides | 54, 36, 18 → 18, 12 | 114, 76, 38 → 38, 25.333 |
| Rows 40 / 42 / 43 | 97 / 54.874 / 103.879 | 224 / 196.963 / 369.628 |
| Melee min-max, attack | 71-120, 114 | 251-424, 279 |
| Melee recovery: base, bonus, delay, `damageMultiplier` | 90, 53, 59, 59/65 = 0.907692 | 100, 133, 43, 43/43 = 1 |
| Rows 44 / 46 / 47 | 94 / 36.013 / 63.238 | 219 / 166.779 / 288.284 |
| Bow min-max, attack | 36-63, 111 | 166-288, 274 |
| Bow recovery: base, bonus, delay, multiplier | 90, 42, 63, 63/70 = 0.9 | 110, 107, 53, 53/48 = 1.104167 |
| AC, each resistance, HP | 63, 34, 1059 | 136, 110, 4087 |
| Hit chance melee / bow, MAW (Hell) | 0.6013 / 0.5927 (0.5973 / 0.5887) | 0.6170 / 0.6106 (0.6124 / 0.6061) |
| Crit chance, crit mult | 0.1687, 1.74 | 0.2732, 1.95 |
| Chance to be hit, MAW (Hell) | 0.8093 (0.8149) | 0.7312 (0.7417) |

Worked row check (L50 sword): mult = 1 + 17·2/100 = 1.34; add = 18·1.34 = 24.12; armsDmg = 1.5·11·1.34 = 22.11;
floor term `17 − (18 + 12·3/2 + 22.11/1.34)·0.34 < 0`; tot = 46.23 → round 46; row 42 = 3 + 46 = 49, row 43 =
round(16.08)·3 + 46 = 94; Might: `49 + (49 + 17)·0.089 = 54.874`, `94 + 111·0.089 = 103.879`; engine `17 + 54 = 71`,
`17 + 103 = 120`.

**ArchMage** (class 46): stats as above; Fire, Dark, Earth and Staff `round(1.5·estimateSkill(L))` = 17 / 40 GM;
Learning (ascension) `round(estimateSkill(L))` = 11 / 26 GM; a two-handed staff, no enchants. Spell crit chance
0.1687 / 0.2732, spell crit mult `89/1500 + 1.5 = 1.56` / `279/2500 + 1.5 = 1.61` (reference level L). Fireball delay
`round(80/1.04·1.015^11) = 91` / `round(80/1.13·1.015^26) = 104`; Dragon Breath delay 113 / 130.

### 11.2 Player → monster (identical at MAW and Hell; only the monster's HP differs)

| Attack | Base value | After stage 17 / CalcSpellDamage | Crit | After stage 19 | Final no crit | Final crit |
|---|---|---|---|---|---|---|
| L50 melee | R(71,120) = 95 | ×0.907692 = 86.2308 | 150.0415 | ÷2^0.1 = 80.4562 / 139.9937 | **81** | **140** |
| L50 bow | R(36,63) = 49 | ×0.9 = 44.1 | 76.734 | 41.1468 / 71.5954 | **42** | **72** |
| L150 melee | R(251,424) = 337 | ×1 = 337 | 657.15 | 314.4321 / 613.1426 | **315** | **614** |
| L150 bow | R(166,288) = 227 | ×1.104167 = 250.6458 | 488.7594 | 233.8608 / 456.0286 | **234** | **457** |
| L50 Fireball | 17×R(1,13) = 119 | ×1.089 = 129.591 | 202.162 | ÷2^0.5 = 91.6347 / 142.9501 | **92** | **143** |
| L50 Drag. Breath | 17×R(1,45) = 391 | ×1.089 = 425.799 | 664.2464 | ÷2^0.2 = 370.6796 / 578.2601 | **371** | **579** |
| L150 Fireball | 40×R(1,23) = 480 | ×1.279 = 613.92 | 988.4112 | 434.107 / 698.9123 | **435** | **699** |
| L150 Drag. Breath | 40×R(1,81) = 1640 | ×1.279 = 2097.56 | 3377.0716 | 1826.032 / 2939.9116 | **1827** | **2940** |

Ascended dice: `round(8·(1 + 0.02·11)·1.025^11) = round(12.81) = 13`, `round(28·1.6007) = 45`; at 26:
`1.52·1.025^26 = 2.8885` → 23 and 81. Fireball and Dragon Breath have `add = 0`. Stages that changed the value:
17 (or the spell roll), 19, 35 (`ceil`); every other stage is a no-op in this setup.

**Mass Distortion** (Earth 17 / 40, monster at full HP, Earth resistance 0):

| | HP | `HP·(0.15 + 0.005·s)` | Stage 15 | Final |
|---|---|---|---|---|
| L50 MAW | 552 | 129.72 | ×1 | **130** |
| L150 MAW | 3859 | 1350.65 | ×1 | **1351** |
| L50 Hell | 861 | 202.335 | ÷1.8^0.5 = 150.8116 | **151** |
| L150 Hell | 6162 | 2156.7 | 1607.5093 | **1608** |

**Enchant and aura** (Champion, MAW, sword with special 12 "6-36 Fire", Fire Aura at GM, u = 0.999):

| | L50 | L150 |
|---|---|---|
| `GetWeaponLevelDamage(sword)` | 79.6581 | 304.1628 |
| Enchant 12 range (Coeff 0.4) | 9.1038-54.6227 | 34.7615-208.5688 |
| Enchant: R(9,55) / R(35,209) × base recovery/100 ÷ 2^0.5 | 32·0.9 ÷ 1.4142 = 20.3647 | 122·1.0 ÷ 1.4142 = 86.2670 |
| Aura: max(0.25·WLD, 48) ÷ 2^0.5 × recovery/100, round | max(19.91, 48) → 33.941·0.9 → **31** | 76.04 → **54** |
| Stage 19 → stage 27 → final | 80.4562 → 131.8208 → **132** | 314.4321 → 454.6991 → **455** |
| `t.ElementalDamage` | 51.3647 | 140.2670 |

**Dragon** (class 10, MAW; stats as above, Unarmed and Dragon Ability 17 / 40 GM; `effLevel = L`):

| | L50 | L150 |
|---|---|---|
| Fang min-max (rows + E(Might)) | 378-619 | 2606-4306 |
| Breath min-max | 266-443 | 1754-2924 |
| Delay (melee = breath) | round(100/1.08) = 93 × 1.255 = 116.715 | 79 × 1.6 = 126.4 |
| Fang: roll → ÷2^0.1 → final | 498 → 464.6504 → **465** | 3456 → 3224.562 → **3225** |
| Fang crit: ×cm → ÷2^0.1 → final | 866.52 → 808.4917 → **809** | 6739.2 → 6287.8959 → **6288** |
| Breath: roll × (0.75 + 0.5u) → final | 354 × 1.2495 = 442.323 → **443** | 2339 × 1.2495 = 2922.5805 → **2923** |
| Breath crit (u = 0: spread 0.75) | 354 × 1.74 × 0.75 = 461.97 → **462** | 2339 × 1.95 × 0.75 = 3420.7875 → **3421** |

### 11.3 Monster → player (Champion; Attack 1 physical, and a Fireball, spell 6, kind Fire)

| | getMonsterDamage | round, ×roll 1.0 | Taken factor | Before rounding | Final |
|---|---|---|---|---|---|
| L50 MAW melee | 156.2788 | 156 | AC 63 vs 200+300: 0.888099 | 138.5434 | **139** |
| L50 MAW Fireball | ×0.5 = 78.1394 | 78 | res 34 vs 100+600: 0.953678 | 74.3869 | **74** |
| L150 MAW melee | 1263.4933 | 1263 | AC 136 vs 1100: 0.889968 | 1124.0296 | **1124** |
| L150 MAW Fireball | 631.7467 | 632 | res 110 vs 1900: 0.945274 | 597.4133 | **597** |
| L50 Hell melee | 190.3438 | 190 | 0.888099 | 168.7388 | **169** |
| L50 Hell Fireball | 95.1719 | 95 | 0.953678 | 90.5994 | **91** |
| L150 Hell melee | 1558.7955 | 1559 | 0.889968 | 1387.4601 | **1387** |
| L150 Hell Fireball | 779.3978 | 779 | 0.945274 | 736.3684 | **736** |

The 10 % floor does not bind. Hits to fall (HP 1059 / 4087): L50 7.6 (MAW) and 6.3 (Hell) melee hits; L150 3.6 and
2.9. The example character has no enchants, so its AC (63 / 136) is far below the model's (112 / 366, Appendix A):
the model expects 7 and 6 hits.

---

## 12. Corrections to existing docs

COMBAT.md:

1. "`DamageToMonster`: 35 stages (`Damage.lua:1464-1504`)" — there are 36 named stages including `publish`
   (the file header still says 30).
2. Stage "sparks-chain" is Chain Lightning: it fires for `Object.Spell == 18` (Lightning Bolt), spawning a full-strength
   copy with one mastery less, not a Sparks effect (`Damage.lua:399-428`).
3. §1.2 and §2.7: Accuracy/Luck crit values scale with the monster's level only for weapon hits. Spell crits
   (`CalcSpellDamage`), enchant/aura crits (legendary 26), all tooltips and the stats screen use `round(TL)`, the
   party's total banked level.
4. §1.4: "Randomisation (`rand=true`, used only for non-monster damage such as traps)" — traps call `calcMawDamage`
   without `rand`; the only `rand=true` call sits in a branch that cannot be reached. Resistance randomisation never
   happens. Traps are mitigated at the victim's own `LevelBase`.
5. §1.3/§1.4: the flat Shaman/Seraphim cut uses `lvl = getTotalLevel()`, and together with legendaries 18/22 it runs
   after the 10 % floor, so a hit can end below 10 % of its input. Also note the Shield-skill (special 36 "of
   Shielding") ×0.85 is physical only, and the floor is taken on the input before the GM Shield cut.
6. §2.2: "blaster with Bonus2==3 ("Carnage"/explosive): × 0.25" — the ×0.25 is for arrows (`Object.Spell == 133`)
   whose ammunition item has special 3 "of Carnage". Blaster shots (`Hit.Spell == 135`) use the melee min/max and
   melee multiplier and are never resisted (Energy).
7. §2.2: "Unarmed is forced to 0 ... so the engine's own unarmed bonus does not leak in" — the hook fires on
   `PlayerAttacked` (a monster attacking the party), so it disables the engine's Unarmed-GM evasion; MAW zeroes all
   skill bonuses through `CalcStatBonusBySkills` anyway.
8. §2.3: "The engine floor of 30 recovery is patched to 1 (`Fixes.lua:370-378`)" — the patch is at
   `Modules/MawCore/Fixes.lua:29-35` (the file has 109 lines). "Haste (+20) only when the buff rework is off" — that
   branch is dead (`not x == "ON"` is always false).
9. §2.4: the spell enchant share is resisted by the spell's element (it is added before stage 19 with resistance 0),
   not by the enchant's element. The Fire Aura is only the Fire Aura buff (spell 4); "vampiric" auras are leech, not
   damage. For blaster shots the enchant/aura comes from the bow slot item, not the blaster.
10. §2.5: dual-wield enchants are each scaled by the average base recovery of both hands (`GetPlayerBaseRecovery`),
    auras by their own item's recovery; Armsmaster damage is halved on both hands when an offhand weapon is held.
11. §2.6: monster-vs-monster damage is divided by physical resistance in stage 9 and again by the damage kind's
    resistance in stage 19. Spear stacks amplify every physical hit on that monster by anyone, including the hit that
    adds the stack.
12. §2.8: missing leech sources and terms: Death Coil (+20 % of the bar, ×1.5 at Dark Master), dragon regen leech,
    the full leech table (3.7), the minimum leech using the current attack/spell delay, map affix 32, and
    legendary 31's conversion.
13. §2.9 #6/#9: Exploding applies `Result/PartyCount` to every member including the target, directly to HP after mana
    shield, outside the pipeline (no mitigation, no cheat-death). The Exploding check uses `NameId > 220` (strict).
    Monster spells with id ≥ 100 and action-2/3 hits without a projectile keep the engine's vanilla damage.
14. §2.9: the reflected/Pain-Reflection `^0.85` is applied to the engine's own (vanilla) result for that damage kind,
    with no MAW mitigation; mana shield and death thresholds still apply.
15. §3.5 boss table: Thorn reflects any physical hit (arrows included), not only melee; Adamantite uses `mon.Level`
    (≤ 255) and rounds; Swapper negates every player hit while any other active hostile non-boss monster exists and
    swaps through all of them in turn; boss on-hit conditions bypass condition immunities.
16. §4 table "CC difficulty mult (control spells)" and the note that CC cost distinguishes Easy and Normal:
    `getCCDiffMult`'s value is never used (the cost code is commented out, the other call discards it).
17. §2.9 "Seraph Divine Protection (cheat death, 150-minute cooldown)" — 150 game minutes = 5 real minutes; legendary
    15 sets HP to a quarter and cancels the hit, Divine Protection heals 25 % and leaves the target at 1 HP at worst.
18. §1.5: the monster hit hook covers melee; for spells and missiles the pipeline rolls Speed again. GM Dodging's roll
    applies to every monster attack type, dragons excluded.
19. §2.4 "Damage enchants (ids 4-15, 39, 46)" is right, but the per-hit roll is `R(round(lo), round(hi))` and the
    legendary 19 ×1.5 multiplies before the recovery factor; the aura result is `round`ed, the enchant result is not.

README.md:

20. §2.3 "10 % of a hit always gets through" — not after the Shaman/Seraphim flat cut and legendaries 18/22 (see 5).
21. §2.3 "Accuracy raises crit damage and Luck crit chance (both against the monster's level)" — weapons only; spells
    use the party's total level (see 3).
22. §2.3 "recovery bonuses multiply instead of adding" — imprecise: skill, Armsmaster, Speed and class bonuses add
    into one percentage `B` and recovery is divided by `1 + B/100`; swiftness (specials 41/59), armour impairment,
    Haste, Swift artifacts, dragons and map affix 26 then multiply separately.
23. §2.6 "Crowd control always lands" — the Stun spell still rolls `30/(30 + newLevel/4)`; engine-path CC lands only
    when diminishing returns allow; DR and boss halving apply only to fear/charm/berserk/enslave and paralysis (mace
    and staff stuns included); slows, Dark Grasp and Shrinking Ray have neither.
24. §2.3 "Weapon enchant damage also adds to spells" — and is resisted as the spell's element (see 9).
25. §2.2 "Monsters do not resist Energy" — also: blaster shots are Energy, so blasters are never resisted.

---

## 13. Bugs and quirks found in the code (decide: copy or fix)

New relative to README §6; each is a deliberate-deviation candidate.

1. **Empower Magic reads Haste's numbers**: `ascendSpellDamage` uses `GetBuffMultiplier(const.Spells.Haste, ...)`
   (`General/zzMaw-Spells.lua:2048`) instead of spell 28's row (15/3 vs 10/2).
2. **`buffPower` is replaced on every map load** by `Global/zzMaw_Mapping.lua:25-58` with different resistance and Day
   of Protection values (20 instead of 10); with affix 33 the live table is scaled in place each load without reset,
   so repeated loads compound the nerf.
3. **Map affix 14** compares `U() < power` with `power ≥ 20`: every monster hit becomes Energy (`Damage.lua:1735`).
4. **Map affix 7 regen** uses an undefined global `mon` (`General/zzMaw-Monsters.lua:3604-3609`).
5. **Global `pl` in `GetAttackDelay`**: the unarmed/dragon check reads `pl.Face` of whatever global `pl` last held
   (`General/zzMAW-Skills.lua:508`).
6. **Vampiric artifacts give no leech**: `MawArtifactVampiric` only feeds the unused `gotVamp` tables; leech comes only
   from specials 16/40/41 (3.7).
7. **Legendary 11 `return`s from the legendaries stage** on AoE spells and arrows, skipping the Shaman spell
   multiplier after it (`Damage.lua:1102-1104`).
8. **Dragon SP gain caps instead of adding**: `pl.SP = min(pl.SP + 10, 60)` lowers SP above 60 (`Damage.lua:625-629`).
   Dragons also ignore Weak (stage 20 overwrites stage 17's result).
9. **Assassin out of SP** loses the whole Earth bonus on every hit (`assassinationDamage` returns the full
   `assassinDamage`); spells in `assassinSpells` with `DamageMult = 0` deal 0.
10. **DK Blood Leech can drive SP negative** (no check before `SP −= 6/12`).
11. **Heal (68) adds MAW's share without a max-HP cap** (`General/zzMaw-Spells.lua:368`).
12. **MM6-projectile cover loop skips the last party slot** (`for i=0,#cover-1` with a 0-based table,
    `General/zzMaw-Monsters.lua:3948`).
13. **Poison counters mix roster index and party slot** (`vars.poisonTime[t.PlayerIndex]` vs `[i]`).
14. **Unused CC difficulty multiplier** (`getCCDiffMult`) and dead "rework off" branches (`not x == "ON"`) in Haste,
    Hammerhands, Heroism, Regeneration and elemental buffs.
15. **Mass Distortion and Adamantite use the 255-capped `mon.Level`**; Mass Distortion's `(Level/250)²` therefore never
    exceeds 1.04.
16. **Boss gates differ**: `220 ≤ NameId < 300` in most places, `≤ 300` in `getMonsterDamage/Health` and Retaliation
    stun, `> 220` for Exploding.
17. **Resistance immunity check** only looks at the chosen (weakest) resistance's base value; affix 29 is applied to
    the total but the 65000 test uses the unreduced base.
18. **`calcEffectChance` and `applyCCDebuff` read raw monster resistances** (no `%1000`), unlike every damage path.
19. **Map affixes 5/6 reflect `(100 − p) %`** of the hit (`affixCut(t.Result, 5)` = `Result·(1 − p/100)`,
    `Damage.lua:1154-1163`) while the tooltip promises `p %`.
20. **Dagger and Axe crit bonuses also apply to arrows** (`getCritInfo(pl, false, L)` checks the hands, not the
    attack).

---

## 14. Not covered

- **Engine internals assumed, not verified in the binary**: the exact `GetMeleeDamageMin/Max` composition (fist
  damage when unarmed, the `max(1, ...)` clamp), how MM8 rounds/truncates floats returned by hooks, whether the
  `0x425893` monster-hit routine also runs for missiles (verified 2026-10-24, audit FMON-2-1: it does for objects
  500-545, so arrows and Body/Mind/Spirit missiles take two Speed rolls; MAW's "M&M6 Projectiles" swap the elemental
  ones, which skip it, the special attack and Pain Reflection and strike a random conscious member, OVR2-2-1;
  `CombatRules::monsterMissileRules`), the number of arrows per
  bow mastery, which object hits pass through the `0x4256DB` player-hit routine (blaster, dragon breath).
- **Engine tick rates** for Immolation damage, the engine `Regeneration` event and party-buff ticks.
- **`Data/Tables` monster attacks and spell kinds** for specific monsters (only the per-hit rules are specified).
- **Buff-rework mana reservation** (`mawBuffCast`, `getBuffCost`, `buffManaLock`), Shared Life (`doSharedLife`) and
  potion buff strength: they decide whether a buff is active and its skill, not the per-hit maths.
- **Homing, knockback (`mawTick_MonsterPush`), Swift and Puller movement**, Summoner/Broodlord spawn details.
- **Elementalist spell rotation and mana cost**, Assassin and DK spell-cost presentation, Celestial item updates,
  `GetEnc2` and quality multipliers (item format, see ITEMS.md).
- **Multiplayer stages** (puppet, remote owner, sync) and the Survival mode stage (dead code).
- **Doom on-hit conditions** for ordinary monsters (`General/zzMaw-Monsters.lua:3691-3747`) and difficulty-dependent
  monster spell skill; only boss on-hit effects are specified.
- The balance model's `getPlayerEstimatedSpellPower` and `getPlayerEstimatedHealing` (tooltip and tuning helpers, not
  per-hit inputs).

---

## Appendix A. The balance model (`Modules/MawCore/Estimates.lua`)

Monster damage and HP, the player hit chance, the Speed dodge, the Shaman/Seraphim flat cut and the regen rates all
read this model. Everything is a pure function of the level, `GetDifficulty()` and the mode flags. `th` = mastery
thresholds (1.2); `ramp(L) = clamp((L − 100)/320, 0, 1)` (legendary ramp); `m(L) = masteryForSkill(skill(L))`.

```
skill(L)      = (sqrt(1 + 8·(P/5 + 1)) − 1)/2
    P = 0 if L < 2 else 5(L−1) + 5q(q−1) + q(r+1), q = floor(L/10), r = L − 10q
buffRamp(s)   = clamp((s − th[2])/(th[3] − th[2]), 0, 1)
row(t, s, m)  = t[1] if m ≤ 1 else GetGradualMasteryValue(t, s, m)
capS(sp, s)   = min(s, 75 for 83/85/86 else 50)
buffFlat(sp, s, m, L, div=4) = (row(Base) + L/div)·(1 + row(Scaling)/100·capS)·buffRamp(s)
buffMult(sp, s, m)           = row(Base)/100·buffRamp(s)·(1 + 0.02·capS)
lootTier(L)   = L/15 + min(1 + L/15, 6)
encStrUp(t)   = 1 + 2t (t ≤ 12) else 25 + min(3(t − 12), 75)          (Austerity: t + 2 / 32 + 2(t − 30))
extraPower    = 1.2 Insanity, 1.1 Doom, 1.05 true Nightmare, else 1
maxEnchant(L) = encStrUp(lootTier(L))·extraPower·1.1
totalEnchant(L) = 3·13.75·maxEnchant(L)
geared(L)     = (L + 20)/(L + 100)·EF(lootTier, drops(L, dens[diff]), diff)/EF(lootTier, drops(L, 1), 9)
    dens = {0.40, 0.40, 0.40, 0.43, 0.43, 0.47, 0.59, 0.66, 0.70};  drops(L, d) = (L/(3.6 + L/140) + 1)·d
stat(L)       = (17 + 0.2·min(L, 500) + totalEnchant(L)·0.25·geared(L))·(1 + min(10 + skill/7, 20)/100·buffRamp(skill))
```

`EF(tier, n, diff)` = `GetExpectedEnchantFraction` (`General/zzMaw-Items.lua:822-877`):

```
bands: thresholds T_r = min(Base_r + PerTier_r·tier, Cap_r):
       Epic 5/0.75/20, Rare 20/2/60, Uncommon 60/1/80, Common 100/0/100
       widths from Epic to Common: max(T_r − T_previous, 0)·bandMult[diff][r], normalised to 1
       bandMult (Epic/Rare/Uncommon): diff 4 1.5/1.4/1.4, 5 2/1.8/1.6, 6 2.5/2.2/1.8, 7 3/2.6/2,
                                      8 4/3/2.2, 9 5.5/3.4/2.4
epic split: k = {1,1,1,1.1,1.2,1.4,1.6,1.8,2}[diff]·T_Uncommon/80
            for r = Celestial (0.002), Legendary (0.03), Primordial (0.04), Ancient (0.12):
                c = min(base_r·k, 1); dist[r] = epic·left·c; left −= left·c
            dist[Epic] = epic·left
value(r) = enchants(r)/3 · mean(r)/1.25, enchants Common 0, Uncommon 1, Rare 2, others 3;
           mean = (Min + Max)/40 with Celestial/Primordial 25-25, Ancient 20-25, Legendary 16-20, others 8-20
EF = Σ over rarities sorted by value ascending: value(r)·(cum_r^n − cum_{r−1}^n)       (best of n drops)
```

Health, armour and resistance:

```
perLevel(L) = min(6L/210, 6) + 3   (Madness: 330)
health(L)   = (25 + perLevel·L + (stat/5 + skill·row({1,2,3}, skill, min(m,3)))·perLevel
                 + 4·(stat/10)·min(1 + stat/500, 5))
              ·(1 + GV(bodybuildingHP, skill, min(m,3))·skill/100)·(1 + stat/1000)
P(L)        = PowerFor(L) = min(floor(L/5), 100);  primordial(L) = min(max(round(1.2·P), P + 4), 255)
worn(L)     = 116·(1 + primordial(L)/40)·geared(L)
AC(L)       = worn·(1 + 0.5·ramp + row(skillItemAC[Chain], skill, m)·skill/100)
              + buffFlat(Stone Skin 38, skill, m, L, 4)
res(L)      = worn·row(skillItemRes[Chain], skill, m)·skill/100 + buffFlat(Fire Resistance 3, skill, m, L) + E(stat)
enchRes(L)  = maxEnchant(L)·0.5·(1 + 0.5·ramp)
phys(L)     = max(1/(AC/(200 + L) + 1), 0.1)
magic(L)    = max(1/(res/(100 + L) + 1)·max(1 − buffMult(Shield 17), 0.7)·1/(enchRes/100 + 1), 0.1)
toHit(L)    = 1/(1 + stat/(100 + stat)·0.5)
legTaken(L) = (1 − 0.1·ramp)·(1 − (1 − 0.97^5)·ramp)
cover(L)    = 1 if row({0,1}, skill, m) ≤ 0, else 1/((1 − p) + p/ratio):
              p = min(0.1 + 0.01·skill, 0.4)·gate; ratio = 1 + 6L/(L + 240), or 2 when the LIVE party has one
              member (so solo play changes monster damage)
Vit(L)      = health/((phys·0.5 + magic·0.5)·toHit·legTaken)·cover          -- getPlayerEstimatedVitality
```

Weapon, attack and power:

```
getWeaponDamageForLevel(IL, twoHanded, flat):
    pw = min(PowerFor(IL), 255); fp = floor(pw/2); pFlat = 2·fp; pDice = 4·(pw − fp)
    dice = 16 + pDice; flatAll = flat + pFlat; levelDamage = pFlat + pDice/2   (one-handed: all three halved)
    return dice + flatAll, dice, flatAll, levelDamage
weaponFlat(L) = min(0.5L, 16);  tierFlat(t) = 16·(clamp(t, 1, 6) − 1)/5 (3.5 → 8)
getWeaponLevelDamage(IL, 2H, flat) = ((levelDamage + arms)·(1 + 0.02·skill(IL)) + statFlat)·(1 + stat(IL)/1000)
    arms = GV(armsmasterSkill.Damage, 1.5·skill(IL), mFor(1.5·skill(IL)))·1.5·skill(IL); statFlat = E(stat(IL))
    one-handed: arms/2, statFlat/2
meleeSkill(L) = 1.5·skill(L) + 10·ramp(L)
Attack(L) = (wDmg − wDice − wFlat)/2 + wFlat + GV(skillAttack[Sword], meleeSkill)·meleeSkill
            + GV(armsmasterSkill.Attack, skill, m)·skill + E(stat) + buffFlat(Bless 46, skill, m, L)
            with (wDmg, wDice, wFlat) = getWeaponDamageForLevel(L, true, weaponFlat(L))
Power(L):
    mult = 1 + 2·meleeSkill/100; arms = GV(armsmasterSkill.Damage, 1.5·skill)·1.5·skill
    scalable = 0.75·(wDmg − wDice − wFlat) + wFlat + 0.5·wDice + arms
    d = 1.5 + scalable·mult + max(meleeSkill − scalable·(mult − 1), 0)
    d = (d + E(stat))·(1 + buffMult(Heroism 51))·(1 + stat/1000)
    d ×= 1 + GetSpeedBonusFromStat(stat)/100 + GV(skillRecovery[Sword], meleeSkill)·meleeSkill/100
           + GV(armsmasterSkill.Speed, 1.5·skill)·1.5·skill/100;  d ×= 1 + buffMult(Haste 5)
    cc = critChance(stat, L) + 0.1·ramp + buffMult(Fate 47); cm = critDamageMult(stat, L) − 1
    d ×= 1 + min(cc, 1)·cm
    encLeg = (1 + 0.5·ramp)·(1 + min(cc,1)·cm·ramp)
    WLD = getWeaponLevelDamage(L, true, weaponFlat(L))·encLeg
    d += WLD·0.5·min(L/100, 1) + WLD·GV(fireAuraDamage, skill, m)
    d ×= min(1 + 0.25·ramp, 2)·(1 + 0.15·ramp)·max(cc, 1)
    return d·min(0.75 + 0.05 + 0.05·min(skill, 50)/50, 1)
getMonsterHealth(nil, L) = Power(L)·hitsM[diff];  getMonsterDamage(nil, L) = Vit(L)/hits[diff]
```

(`GV(t, S)` without a mastery uses `masteryForSkill(S)`; the Bless hit bonus in the last line is
`blessHitBonusForSkill(skill)`.)

Reference values (harness output, buff rework on, normal mode, `buffPower` from `zzMaw_Mapping.lua`):

| L | skill | stat | geared | maxEnchant | health | AC | res |
|---|---|---|---|---|---|---|---|
| MAW 1 | 1.0000 | 21.4569 | 0.1149 | 3.5933 | 54.21 | 15.10 | 4.15 |
| MAW 10 | 4.0442 | 27.2151 | 0.1271 | 6.2333 | 105.57 | 19.39 | 6.05 |
| MAW 50 | 11.4269 | 88.8651 | 0.2839 | 17.9667 | 661.75 | 111.60 | 73.98 |
| MAW 100 | 19.1023 | 177.8568 | 0.3943 | 29.7000 | 1895.96 | 219.26 | 153.11 |
| MAW 150 | 26.4490 | 279.4524 | 0.4732 | 40.7000 | 4069.87 | 365.87 | 253.25 |
| MAW 200 | 33.6797 | 394.7924 | 0.5380 | 51.7000 | 7597.88 | 553.39 | 380.13 |
| MAW 300 | 48.0000 | 634.5806 | 0.6132 | 73.7000 | 16135.73 | 1021.19 | 694.59 |
| Hell 50 | 11.4269 | 95.8501 | 0.3177 | 17.9667 | 678.85 | 120.13 | 78.01 |
| Hell 150 | 26.4490 | 300.5969 | 0.5175 | 40.7000 | 4226.29 | 391.87 | 268.58 |
| Hell 300 | 48.0000 | 681.4520 | 0.6660 | 73.7000 | 17039.36 | 1093.05 | 737.50 |

| L | phys | magic | toHit | Vit | Power | Attack |
|---|---|---|---|---|---|---|
| MAW 1 | 0.9317 | 0.9473 | 0.9188 | 62.80 | 13.7336 | 5.3125 |
| MAW 10 | 0.9306 | 0.9415 | 0.9034 | 124.97 | 33.2182 | 26.6475 |
| MAW 50 | 0.8175 | 0.6769 | 0.8095 | 1093.95 | 275.8004 | 162.9155 |
| MAW 100 | 0.7849 | 0.6175 | 0.7575 | 3569.36 | 799.3734 | 266.9081 |
| MAW 150 | 0.7504 | 0.5577 | 0.7309 | 8844.45 | 1929.7361 | 380.3096 |
| MAW 200 | 0.7167 | 0.5005 | 0.7148 | 18860.48 | 4141.0339 | 499.4092 |
| MAW 300 | 0.6620 | 0.4006 | 0.6984 | 50878.17 | 14499.9495 | 749.2000 |
| Hell 50 | 0.8063 | 0.6734 | 0.8034 | 1142.06 | 286.8386 | 164.9155 |
| Hell 150 | 0.7373 | 0.5537 | 0.7272 | 9352.77 | 2054.1008 | 385.3096 |
| Hell 300 | 0.6466 | 0.3968 | 0.6964 | 54874.96 | 15778.3228 | 759.2000 |

Monster B-tier at MAW (diff 3): HP = 2·Power, damage = Vit/7 (L50: 551.60 / 156.2788; L150: 3859.47 / 1263.4933;
L300: 28999.90 / 7268.3097). Hell (diff 5): HP = 3·Power, damage = Vit/6 (L50: 860.52 / 190.3438; L150: 6162.30 /
1558.7955; L300: 47334.97 / 9145.8260). The model's own values change with difficulty because `geared` reads the
difficulty's drop density.
