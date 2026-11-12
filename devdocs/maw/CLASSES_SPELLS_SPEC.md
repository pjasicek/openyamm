# MAW classes, spells, buffs and potions: implementation spec

> Formulas updated to MAW `8fbb48d1` (2026-11-05) and `8967ae88` (2026-11-12) where [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) and [UPSTREAM_SYNC_8967ae88.md](UPSTREAM_SYNC_8967ae88.md) list a change.

Status: specification draft (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at commit `ef23ee17`, compared with base
MMMerge (`reference/mmmerge`, `reference/mmerge_data_forus`) and with OpenYAMM as of today. This document gives every
number the MAW ruleset needs for spells, Ascension, buff auras, crowd control, classes, races and alchemy, with the code
location of each. It extends [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) §2-5 and corrects it where the code
says otherwise (§8). The code wins over the MAW README and over in-game tooltips; where a tooltip disagrees with the
code it is said.

Data drafts (all headed "draft extracted from MAW ef23ee17"):

| File | Contents |
|---|---|
| [data/spells.yml](data/spells.yml) | all 111 spells: base MMMerge, OpenYAMM table and `BackendSpellRule`, MAW values, notes, what changes; plus 39 class variants |
| [data/buff_auras.yml](data/buff_auras.yml) | reservation math, lifecycle, every aura and utility aura, potion competition |
| [data/crowd_control.yml](data/crowd_control.yml) | CC table, duration formula, diminishing returns, targeting, costs |
| [data/class_perks.yml](data/class_perks.yml) | Seraphim, Death Knight, Shaman, Elementalist, Assassin, Knight, Dragon; class table changes |
| [data/promotions.yml](data/promotions.yml) | cross-world promotion lists, random final class, Elder/Ultimate, Lich reset |
| [data/race_bonuses.yml](data/race_bonuses.yml) | flat skill bonuses, mastery tokens, resistances, special racial rules |
| [data/potion_effects.yml](data/potion_effects.yml) | every potion 221-290 in a schema that also expresses the Standard potions |
| [data/potion_recipes.yml](data/potion_recipes.yml) | the 87 recipes, 43 reagents, reagent power and drops |

Shorthand for §0-4 and §8.1 (MAW paths): `SP` = `Scripts/General/zzMaw-Spells.lua`,
`S` = `Scripts/General/zzMAW-Skills.lua`, `ST` = `Scripts/General/zzMaw-Stats.lua`,
`IT` = `Scripts/General/zzMaw-Items.lua`, `DM` = `Scripts/Modules/MawCore/Damage.lua`,
`F`/`FO` = `Scripts/Modules/MawCore/Formulas.lua`, `CL` = `Scripts/General/zzClasses.lua`,
`E` = `Scripts/Modules/MawCore/Estimates.lua`, `TW` = `Scripts/General/SpellsTweaks.lua`,
`TI` = `Scripts/General/zzMaw-Timers.lua`. Sections 5-7 define their own shorthand (there `SK` is
`MawCore/Skills.lua` in §5-6 but `zzMAW-Skills.lua` in §7). OpenYAMM paths are prefixed
`OpenYAMM/`. `s` = skill level, `m` = mastery 1..4 (N/E/M/G), 0 = not learned. Time: one game minute
(`const.Minute`) is shown to players as 2 real seconds (`F:9`, `gameMinuteSeconds`). Worked numbers come from
Lua 5.4 ports of the formulas in the session scratchpad (`lua_spells/`, `lua_classes/`, `lua_alchemy/`).

---------------------------------------------------------------------------------------------------------------

## 0. Summary

- **Spells**: 37 damage spells use MAW's own `spellPowers` table, 6 healing spells use a heal table, 13 CC spells
  use the CC table, 25 buff spells and 3 utility spells become mana-reserving auras. 16 rows of `Spells2.txt`
  change cost or delay. OpenYAMM keeps spell numbers in two places, `spells.txt` and the hard-coded
  `BackendSpellRule` switch, and the switch wins for about 48 spells; a ruleset table override alone would be
  silently ignored (§1.8).
- **Ascension** (the Learning skill) is a single dial: damage dice `×(1+0.02s)·1.02^s`, flat damage
  `×(1+0.01s²)·1.02^s`, heals `×(1+0.02s)·1.015^s` / `×(1+0.01s²)·1.015^s`, mana `×(1+0.125s)·1.04^s·(1−0.125m)`,
  cast time `×1.015^s`. Mastery is the only cost reduction (§2).
- **Auras** reserve `cost / (classSPFactor + EnlightenmentMastery/2)` percent of the caster's maximum mana while on,
  are re-applied every 0.5 s (so monster Dispel never sticks) and compete with potions for the stronger value (§3).
- **CC** lands without a resistance roll (except Stun); duration = base × mastery step × `1.015^asc` /
  `(1 + res/100)`, ×2 solo, then diminishing returns per monster and group, then ÷2 on bosses for groups 2-3 (§4).
- **Classes, races, alchemy**: §5-7, with data files. The largest surprises: MAW never reads `Race Skills.txt`,
  Shaman spell damage never ascends, three "boost" potions do nothing, and Empower Magic uses Haste's numbers.

---------------------------------------------------------------------------------------------------------------

## 1. Spells

### 1.1 Cost

The engine reads `Game.Spells[id].SpellPoints<Mastery>`, a global table. MAW rewrites that table for the
selected or casting character before every cast and every frame (`ascension()`, SP:2541-2570, called from
`PlayerCastSpell` SP:136-142, `Action` SP:2116-2119 and the scheduler SP:2144-2164). OpenYAMM should compute the
cost per caster instead. The per-category rules:

| Category | Spells | Cost |
|---|---|---|
| Damage (`spells` list, SP:1888) | 2 6 7 8 9 10 11 15 18 20 22 24 26 29 32 37 39 41 43 44 52 59 65 70 76 78 79 84 87 90 93 97 98 99 103 111 123 | `min(ceil(base[m] · (1+0.125s) · 1.04^s · (1−0.125m_a) · P), 65000)` (SP:2264-2279) |
| Healing (SP:2108) | 49 54 55 68 74 77 | same curve on the healing-table cost, `round` instead of `ceil`, then `ceil` into `Game.Spells` (SP:2355-2366, 2387-2434) |
| CC (CCMAP keys) | 34 35 48 60 62 63 66 81 92 94 96 113 122 | `ceil(base[m] · (1+0.2s) · 1.03^s · (1−0.125m_a) · P)`; 122 fixed 15/15/25/30 (SP:2182-2196) |
| Auras and utility auras | §3 | `0` SP; the aura reserves mana instead (SP:2483-2496) |
| Everything else | Town Portal, Fly, cures, ... | `Spells2.txt` value, unchanged |

`base[m]` is the `Spells2.txt` cost for the caster's school mastery (Chain Lightning M/G overridden to 20/30 in
Lua, SP:1883-1885). `s`, `m_a` are the Ascension level and mastery (§2.1). `P` is the Personality factor
`0.99^(Personality / (10 + 0.06 · min(partyTotalLevel, 1000)))` (SP:2172-2179), where `partyTotalLevel` is
`getTotalLevel()`, the sum of the party's per-continent levels (`zzzMaw_Experience.lua:262-273`), not the
character's level. Examples (Lua): Personality 100 at total level 100 → ×0.939; 300 at 200 → ×0.872;
1000 at 1000 → ×0.866; 2000 at 1000 → ×0.750. Mass Distortion GM is special:
`ceil(min(LevelBase, 255)^1.4 / 12.5 · P)` (SP:2275-2277).

Death Knights and Assassins skip all of this (`ascension()` returns early, SP:2549-2557); their costs are fixed
(§5.3, §5.6).

### 1.2 Damage

`events.CalcSpellDamage` (SP:1937-2040), for the spells in `spellPowers` (SP:1892-1933) plus the internal ids 200
(Lifedrain) and 201 (Souldrinker) that MAW swaps in on impact for its leech fix (SP:3781-3790):

1. Mass Distortion (44) returns early: `HP · 0.15 + HP · s · 0.005` of the engine's `t.HP` (SP:1939-1942), then the
   bolster divisor stage (§1.5).
2. `diceMin, diceMax, add` from `spellPowers`; Empower Magic multiplies all three (§3.4, uses the wrong row);
   then `diceMax × spellDiceScale(asc)`, `add × spellAddScale(asc)`, rounded (SP:2043-2060, F:153-163).
   Elementalist stacks then multiply `diceMax` and `add` by `1 + 0.1·stacks` (SP:1970-1973).
3. Roll: `add + Σ_{1..s} rand(diceMin..diceMax)`; if `diceMin == diceMax` the fixed `add + diceMax·s` with the
   **unscaled** `diceMax` (SP:1976-1986: it reads `spellPowers[t.Spell].diceMax`, so fixed-per-point spells
   Meteor Shower 9, Starburst 22, Armageddon 98 and Mass Distortion get no Ascension on the per-point part).
4. Mastery multipliers: Fire Spike ×8/6 at M, ×10/6 at GM; Lifedrain ×5/3 at M, ×7/3 at GM (SP:1988-2002).
5. Death Knights and Dragons (class 10/11) stop here (SP:2005-2007).
6. `× (1 + max(Int, Pers)/1000)` (SP:2011-2015, `getIntellectDamageMultiplier` ST:296-298), crit roll with
   `getCritInfo(pl, "spell")` (COMBAT.md).
7. `+ (enchant damage + Fire Aura damage) · 1.015^asc` of each active item slot 0-2, `/2.5` on AoE spells
   (SP:2021-2037, list SP:2094).

Monster resistance, damage randomisation and difficulty scaling come after, in the damage pipeline
(COMBAT.md). Table deltas and MAW numbers per spell: §1.4 and `data/spells.yml`.

### 1.3 Cast time

`getSpellDelay` (ST:162-241), also written into `Game.Spells[id].Delay<M>` on cast (ST:156-160):

- Assassin: `GetAssassinSpellDelay` = 2 × attack delay; Dragon Fear 122: 120; no school mastery: 150.
- CC spells: `round(tableDelay[m] · 1.015^(asc − schoolSkill))`, no Speed, Haste or armour term (ST:211-217).
- Everything else: `round(tableDelay[m] / (1 + floor(Speed/20)/100) · 1.015^asc / hasteDiv / enchant) · armour`,
  where `asc` counts only for damage, healing and CC spells (0 for auras and utility), `hasteDiv = 1 +` the Haste
  aura or potion multiplier (§3.4), `enchant = 1.1` with a "spell haste" item (Bonus2 40, IT:2087-2095), `armour =
  1 + offhand-shield and body-armour impair %/100` (weapon impair table S:37-43: Leather 10/10/0/0/0, Chain
  20/20/10/0/0, Plate 20/20/10/10/0, Shield 10/10/0/0/0 for unskilled/N/E/M/G).
- Elementalist: ×1.5 then ÷`(1 + 0.05·stacks)` (ST:228-236); Flame Blast 123: 1.5 × attack delay; map affix 27
  divides by `(1 − p/100)`.

### 1.4 Every changed spell

Costs and delays are `[N, E, M, G]`; "dmg" is `add + diceMin..diceMax per point`. Base = MMMerge `Spells2.txt`.
Rows not listed keep the base numbers (they may still be aura/CC, see §3-4).

| Id | Spell | Base cost / delay / dmg | MAW cost / delay / dmg | Other changes |
|---|---|---|---|---|
| 2 | Fire Bolt | 2 / 110,110,100,90 / 0+1-3 | = / = / 8+1-2 | |
| 6 | Fireball | 8 / 100,100,90,80 / 0+1-6 | = / = / 0+1-8 | AoE |
| 7 | Fire Spike | 10 / 150 / 0+1-6 | = / **100** / 0+1-10 | M ×8/6, G ×10/6 |
| 8 | Immolation | 15 / 120 / 0+1-6 | aura 40 % / = / 10+1-30 | aura (§3) |
| 9 | Meteor Shower | **20** / 100,100,100,90 / 8+1 | **40** / **200,200,200,180** / 2+1 | per-point part not ascended |
| 10 | Inferno | **25** / = / 12+1-2 | **50** / = / 12+1-7 | |
| 11 | Incinerate | 30 / 90 / 15+1-15 | = / = / 19+1-21 | |
| 15 | Sparks | **4** / 110,100,90,80 / 2+1 | **4,8,10,12** / = / 0+1-4 | |
| 18 | Lightning Bolt → **Chain Lightning** | 10 / 100,100,90,70 / 0+1-8 | **10,10,20,30** / **100,80,100,120** / 12+1-8 | chains, §1.5 |
| 20 | Implosion | 20 / 100,100,100,90 / 10+1-10 | = / = / 20+1-12 | |
| 22 | Starburst | **30** / **90** / 20+1 | **60** / **140** / 7+1 | per-point part not ascended |
| 24 | Poison Spray | **2** / 110,100,90,70 / 2+1-2 | **2,4,5,6** / = / 5+1-3 | |
| 26 | Ice Bolt | 4 / 110,100,90,80 / 0+1-4 | = / = / 6+1-7 | |
| 29 | Acid Burst | 10 / 100,100,90,80 / 9+1-9 | = / = / 4+1-14 | |
| 32 | Ice Blast | 25 / 80 / 12+1-6 | = / = / 6+1-6 | |
| 37 | Deadly Swarm | 4 / 110,100,90,80 / 5+1-3 | = / = / 8+1-5 | |
| 39 | Blades | 8 / 100,100,90,80 / 0+1-9 | = / = / 7+1-7 | |
| 41 | Rock Blast | 15 / 90,90,90,80 / 10+1-10 | = / = / 8+1-8 | |
| 43 | Death Blossom | **25** / **100,100,100,90** / 20+1 | **50** / **180,180,180,160** / 4+1-2 | |
| 44 | Mass Distortion | 30 / 90 / 25 % HP | GM: level formula / = / 15 % + 0.5 %/pt | §1.5 |
| 49 | Remove Curse | 5 / 120 | heal table 0,5,10,20 / = | becomes a heal, §1.6 |
| 52 | Spirit Lash | 15 / 100 / 10+1-8 | = / = / 20+**2**-16 | Master range 384 |
| 54 | Shared Life | **25** / **150** | table 12 (unused), heal table M/G 25/40 / **200,200,200,150** | rewritten, §1.6 |
| 55 | Resurrection | 30 / **1000** | heal table GM 100 / **1000,1000,1000,300** | heals, §1.6 |
| 56 | Telepathy | 1 / 110,100,90,80 | aura 120 % | becomes the Meditation aura |
| 59 | Mind Blast | 4 / **110** / 3+1-3 | = / **120,110,100,90** / 12+1-6 | |
| 63 | Mass Fear | **15** / **80** | **40** / **200** | CC |
| 65 | Psychic Shock | 25 / 110,110,110,100 / 12+1-12 | = / = / 25+1-25 | |
| 68 | Heal | 2 / 100 | heal table 2,4,6,8 / = | §1.6 |
| 70 | Harm | 4 / 110,100,90,80 / 8+1-2 | = / = / 4+1-4 | |
| 74 | Cure Disease → **Greater Heal** | 15 / 120 | heal table M/G 15/25 / = | §1.6 |
| 76 | Flying Fist | 25 / 110,110,110,100 / 20+1-10 | = / = / 20+1-5 | |
| 77 | Power Cure | 30 / 100 | heal table GM 30 / = | §1.6 |
| 78 | Light Bolt | 5 / 110,100,90,80 / 0+1-4 | = / = / 12+1-2 | |
| 79 | Destroy Undead | **10** / 120,110,100,90 / 16+1-16 | **50** / = / 45+1-45 | |
| 82 | Summon Wisp | **25** / 140 | **25,50,75,100** / = | §1.5 |
| 84 | Prismatic Light | 35 / 135,135,120,100 / 25+1 | = / = / 30+**2**-6 | |
| 87 | Sunray | 50 / 150,150,150,135 / 20+1-20 | = / = / 60+1-60 | |
| 90 | Toxic Cloud | 15 / 120,110,100,90 / 25+1-10 | = / = / 15+1-9 | |
| 91 | Vampiric Weapon → **Vampiric Aura** | 20 | aura 150 % | §3 |
| 93 | Shrapmetal | 30 / 90,90,80,70 / 0+1-6 | = / = / 0+1-7 | |
| 97 | Dragon Breath | 50 / 120,120,120,100 / 0+1-25 | = / = / 0+1-28 | |
| 98 | Armageddon | 55 / 250 / 50+1 | = / = / 50+1 | now ascended (flat part only) |
| 99 | Souldrinker | 60 / 300 / 25+1-8 | = / = / 25+1-5 | |
| 103 | Darkfire Bolt | **30** / 120 / 0+1-17 | **20** / = / 46+1-28 | |
| 111 | Lifedrain | **5** / **100,90,90,90** / (engine) | **5,5,10,15** / **100,100,100,100** / 0+1-22 | M ×5/3, G ×7/3 |
| 122 | Fear (dragon) | 5 / 120 | **15,15,25,30** (Lua) / 120 fixed | CC |
| 123 | Flame Blast (dragon) | 10 / 100,100,90,90 | §5.10 | class spell |

All aura spells (3 4 5 8 14 17 25 28 36 38 46 47 50 51 56 58 69 71 73 75 83 85 86 91 95) and utility auras
(1 12 27) cost 0 SP under MAW. Insanity mode replaces the healing table (`getBaseHealingSpells`, SP:2335-2343):
Remove Curse cost 15/30/60, base 20/40/60, +8/12/16; Resurrection 300, 450 + 50; Heal 6/15/24/40, 12/24/36/48,
+6/9/12/15; Greater Heal 45/100, 50/100, +16/25; Power Cure 150, 50 + 12.

### 1.5 Special behaviour (beyond numbers)

- **Chain Lightning (18)**: on a hit with object mastery > 1, a copy with mastery − 1 and the caster's current Air
  skill flies to the closest monster with HP > 0 within 768 of the struck one (DM:399-428). Hits = mastery
  (N 1, E 2, M 3, GM 4), each at full damage. The search excludes only the struck monster, so it can bounce back
  and forth between two monsters, and it does not check hostility (peasants and summons are valid targets).
- **Mass Distortion (44)**: after the 15 % + 0.5 %/pt, the result is divided by `sqrt(mult)` with mult 1 at bolster
  ≤ 100, 1.4 at 150, 1.8 at 200, 3 at 300, Doom (600) `3.33·(1 + lvl/75)` and ×`2·(1 + lvl/80)` more on bosses,
  ×4 in Austerity, then multiplied by `max(1, (level/250)²)` (DM:363-396). MMMerge's resistance check for Slow and
  Mass Distortion is forced to pass (TW:24-41).
- **Stun (34)**: the only CC with a success roll (§4.5); on success MMMerge's hook paralyses for 1 game minute plus
  `s·m` ticks (TW:50-58).
- **Invisibility (19)**: refused while the enemy detector is yellow or red; Master `(15 + s) × 1.5` game minutes,
  GM `(30 + 2s) × 1.5` (SP:157-175, 711-716); stripped on a red detector in Insanity (SP:3849-3857).
- **Fly (21)**: unchanged as a spell (not an aura). At bolster > 100 or in Austerity, any hit by the party turns Fly
  into Feather Fall with the same expiry, except on 11 maps (`elema/elemf/elemw/out12/outa1/outa2/outa3/outb2/outb3/
  out05/out07.odm`) (DM:317-329, SP:1018).
- **Summon Wisp (82)**: if the engine did not summon (cap reached), MAW spawns monster 97 at power C (id 99, ally
  group 9999) while fewer than `2m − 3` wisps live (M 3, GM 5) (SP:3435-3455).
- **Raise Dead (53)** GM also clears Eradicated (SP:250-260). **Mistform (114)**: −75 % physical damage taken
  (DM:1729-1731). **PfM (75)** blocks Unconscious (SP:676-685). **Enchant Item (30)** no longer turns a strong
  catalyst into a Philosopher's Stone (TW:197-210).
- **Solo scrolls** (`Party.High == 0`): Jump (16), Fly (21), Water Walk (27), Town Portal (31) and Lloyd's Beacon
  (33) scrolls are given back after use (SP:1101-1122); a Fly scroll sets Fly for 7 hours at GM, recovery 120.
- **Madness**: Town Portal refused with enemies nearby (SP:3728-3735).
- **Spellbooks**: generated books become sealed school books 971-979 (SP:3637-3726); TAB cycles school pages
  (SP:3539-3563). See SKILLS_SPELLS_ALCHEMY.md §2.8.
- **Dead pre-rework code**: the old Heroism, Regeneration and PfM branches are guarded by
  `not vars.MAWSETTINGS.buffRework=="ON"` and never run; the old Day of the Gods, Day of Protection, protection
  spells and Hour of Power handlers still run on cast (SP:546-653) but the aura pass overwrites their values within
  0.5 s. Port neither.

### 1.6 Healing spells

Heal = `(Base[m] + Scaling[m] · s) × heal mult`, with Base and Scaling Ascension-scaled (§2.2) and
`heal mult = 1 + Personality / min(1000 + 3·LevelBase, 4000)`, × `(1 − affix31/100)` (SP:80-100). Heals never
crit (SP:88-89). Shaman: Base and Scaling of 49, 54, 55, 68 and 74 (not Power Cure) × `(1 + Σ7 schools/400)`
(SP:2370-2384).

| Spell | Cost N/E/M/G | Base | Per point | Notes |
|---|---|---|---|---|
| Heal 68 | 2/4/6/8 | 4/8/12/16 | 2/3/4/6 | engine heal `5 + (m+1)s` subtracted from the bonus so the net is MAW's (SP:333-335) |
| Remove Curse 49 | –/5/10/20 | –/10/20/30 | –/4/6/8 | also cures Curse |
| Greater Heal 74 | –/–/15/25 | –/–/25/40 | –/–/7/10 | also cures Disease |
| Shared Life 54 | –/–/25/40 | 0 | –/–/7/9, used as `s/2` | then −3s (M) / −4s (G), floor 0 |
| Resurrection 55 | GM 100 | 150 | 21 | target may be Dead/Eradicated |
| Power Cure 77 | GM 30 | 15 | 4 | every member; engine `10 + 5s` subtracted |

Heal multiplier examples (Lua): Personality 200 at level 100 → ×1.154; 1000 at 500 → ×1.40; 2000 at 1000 → ×1.50.
Heal GM at Body 20: 136 HP at Ascension 0, 197 at 10, 328 at 20, 550 at 30 (cost 8/20/31/62). Greater Heal GM at
Body 30: 340 / 513 / 839 / 1375.

**Shared Life** (SP:824-1003): participants are members not Dead, Eradicated or Stoned, taken highest HP first and
stopping before the running total of HP plus heal would drop below 0. Their HP is pooled, the heal added, and the
pool given back evenly in rounds up to each member's maximum; nobody can die from it.

**Auto-target heals** (`autoTargetHeals`, default on, `zz_Maw-initialize.lua:11`): quick- or attack-casting 68, 74
or 49 heals the member with the lowest HP fraction (`pickLowestPartyMember`, CL:238-257), spends the cost, sets the
recovery and plays the effect (SP:1182-1331). Death Knights are excluded. Quick-casting 55 is broken: it indexes
`Party[idx]` with an undefined `idx` and would use Greater Heal's numbers (SP:1287-1294). Legendaries 34 and 35
refund mana / recovery from overheal (SP:1149-1180).

### 1.7 Targeting changes

- Projectile spells cast with no monster under the mouse re-aim the projectile at the closest visible hostile
  (SP:3739-3778).
- Auto-target heals (§1.6), scripted CC targeting (§4.5), Shrinking Ray splash targets (§4.5), Chain Lightning
  bounces (§1.5).
- Spirit Lash at Master: range forced to `0x180` = 384 (SP:1009-1014).
- MAW's "Homing Projectiles" setting steers every projectile each frame (S:735-743); not spell-specific, see
  COMBAT.md.

### 1.8 What changes in OpenYAMM

OpenYAMM has `assets_dev/engine/data_tables/spells.txt` (identical to MMMerge `Spells2.txt` except Charm 60, mana
15 instead of 5) and `OpenYAMM/game/party/PartySpellSystem.cpp:642-990` (`resolveBackendSpellRule`), whose explicit
mana, recovery and damage override the table (`resolveManaCost` :613-624, `rollSpellDamage` :1036-1063):

- explicit mana for 1-9 11-18 25 28 30 31 33 36 38 42 51 56 69 75 76 78 82 83 85 86 91 100-103 111-114 122-125;
- explicit recovery for the same set minus 15;
- explicit damage for 2 6 7 9 10 11 15 18 20 22 24 26 29 32 37 39 41 43 52 59 65 70 76 78 79 84 87 90 93 97 98 99 103
  111 123.

The rule already disagrees with the table for Fire Spike/Ice Bolt/Blades/Dragon Breath (add 1 instead of 0), Death
Blossom (2 per point, linear), Flying Fist (30 + 1-5 instead of 20 + 1-10), Shrapmetal (linear 1 + 6), Flame Blast
(10 + 1-10), Lifedrain (3/5/7 per point, recovery 100/80/80/80), Vampire Charm (20 mana) and several recoveries
(56, 101, 102, 103, 112, 113, 122, 123, 124, 125). Heal itself is `5 + 2s` (:1409).

Recommendation:

1. Move every number out of `BackendSpellRule` into `spells.txt` (keep only target kind, effect kind, required
   mastery and projectile counts in code), fixing the divergences above as Standard data. Then a ruleset can
   override `spells.txt` whole.
2. Add `spells.txt` columns: `DamageDiceMin` (default 1; MAW 2 for 52 and 84, 0.5 for 44), `DamageMasteryMult`
   (`1,1,1.333,1.667` for 7; `1,1,1.667,2.333` for 111), `AscensionKind` (damage/heal/cc/none), `AoE` (for the
   enchant divisor), `ChainTargets` (18: mastery). Standard rows keep the defaults.
3. Add `spell_scaling.yml` per ruleset for the formulas in §1.1-1.3 and §2 (Ascension constants, personality
   curve, CC cost curve), plus `heal_spells.yml` (cost/base/per-point per mastery and difficulty) and the CC and
   aura tables (§3-4). Standard rulesets omit them and keep vanilla behaviour.
4. Mana cost and recovery become functions of the caster (Ascension, Personality, Speed, armour, class), computed
   at cast time; the spellbook tooltip calls the same functions.

Row-by-row field changes are in `data/spells.yml` (`change:` on each spell).

---------------------------------------------------------------------------------------------------------------

## 2. Ascension

### 2.1 Level and mastery

| Character | Ascension level `s` | Mastery `m_a` | Source |
|---|---|---|---|
| Normal | Learning skill, `GetSkill` (items included) | Learning mastery | SP:2233-2236, 1955-1956 |
| Elementalist | `Σ(Fire, Air, Water, Earth base skill)/4` (floored for cast time) | forced 4 | SP:2239-2250, 1958-1968, ST:180-187 |
| Shaman | cost and healing: `Σ(Fire..Body base skill)/7`; damage, cast time, CC: Learning | forced 4 (cost/heal) | SP:2251-2259 |
| Death Knight, Assassin | none: `ascension()` returns early | – | SP:2549-2557 |

`Class Skillz.txt` gives Shamans no Learning (§5.4), so Shaman spell damage, cast time and CC duration never
ascend while their costs and heals do. The Learning skill no longer gives experience (`GetLearningTotalSkill`
returns 0) and old Learning points were refunded once (S:1537-1560). Its mastery texts read "mana cost reduced by
12.5/25/37.5/50 %".

### 2.2 Formulas

| Quantity | Multiplier | Source |
|---|---|---|
| Damage dice max | `(1 + 0.02s) · 1.02^s` | F:153-159 |
| Damage flat add | `(1 + 0.01s²) · 1.02^s` | F:161-163 |
| Heal per point | `(1 + 0.02s) · 1.015^s` | SP:2063-2067 |
| Heal base | `(1 + 0.01s²) · 1.015^s` | SP:2063-2067 |
| Mana (damage, heal) | `(1 + 0.125s) · 1.04^s · (1 − 0.125m_a)` | SP:2268, 2362 |
| Mana (CC) | `(1 + 0.2s) · 1.03^s · (1 − 0.125m_a)` | SP:2185 |
| Cast time (damage, heal) | `1.015^s` | ST:227 |
| Cast time (CC) | `1.015^(s − schoolSkill)` | ST:211-217 |
| CC duration | `1.015^s` (not Dragon Fear) | SP:1409-1412 |
| Weapon enchant and Fire Aura damage added to spells | `1.015^s` | SP:2028 |

Touches: the 37 damage spells, the 6 healing spells and the 13 CC spells of §1.1. Not touched: auras, utility,
cures, travel, summons, Raise Dead; Meteor Shower, Starburst, Armageddon and Mass Distortion per-point damage
(§1.2 step 3).

### 2.3 Curve (Lua, `lua_spells/ascension.lua`)

`m` is the mastery a character typically has at that level (N from 1, E 7, M 12, GM 20 under horizontal rules).

| s | m | dice | flat add | heal/pt | heal base | mana | CC mana | cast time, CC duration |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1.05 | 1.04 | 1.04 | 1.03 | 1.02 | 1.08 | 1.015 |
| 5 | 1 | 1.24 | 1.41 | 1.19 | 1.35 | 1.73 | 2.03 | 1.077 |
| 10 | 2 | 1.54 | 2.56 | 1.39 | 2.32 | 2.50 | 3.02 | 1.161 |
| 12 | 3 | 1.67 | 3.28 | 1.48 | 2.92 | 2.50 | 3.03 | 1.196 |
| 15 | 3 | 1.88 | 4.71 | 1.63 | 4.06 | 3.24 | 3.89 | 1.250 |
| 20 | 4 | 2.29 | 8.19 | 1.89 | 6.73 | 3.83 | 4.52 | 1.347 |
| 25 | 4 | 2.78 | 13.44 | 2.18 | 10.52 | 5.50 | 6.28 | 1.451 |
| 30 | 4 | 3.36 | 20.98 | 2.50 | 15.63 | 7.70 | 8.50 | 1.563 |
| 40 | 4 | 4.83 | 45.65 | 3.27 | 30.84 | 14.40 | 14.68 | 1.814 |
| 50 | 4 | 6.87 | 89.36 | 4.21 | 54.74 | 25.76 | 24.11 | 2.105 |
| 60 | 4 | 9.68 | 162.79 | 5.38 | 90.40 | 44.71 | 38.30 | 2.443 |
| 75 | 4 | 15.93 | 364.81 | 7.64 | 174.88 | 98.28 | 73.43 | 3.055 |
| 100 | 4 | 35.44 | 1193.19 | 13.30 | 447.64 | 340.91 | 201.80 | 4.432 |

Mana at a fixed mastery (s = 5/10/20/30/50): no mastery 1.98/3.33/7.67/15.41/51.52, Novice 1.73/2.91/6.71/13.48/
45.08, GM 0.99/1.67/3.83/7.70/25.76.

### 2.4 Worked examples (Lua)

Fire Bolt (8 + 1-2 per point) at Fire 20 GM, cost 2, delay 90, Personality ignored:

| Ascension s / m | dice max | add | average damage | cost | damage per SP | delay |
|---|---|---|---|---|---|---|
| 0 / – | 2 | 8 | 38 | 2 | 19.0 | 90 |
| 5 / N | 2 | 11 | 41 | 4 | 10.2 | 97 |
| 10 / E | 3 | 20 | 60 | 5 | 12.0 | 104 |
| 20 / G | 5 | 66 | 126 | 8 | 15.8 | 121 |
| 30 / G | 7 | 168 | 248 | 16 | 15.5 | 141 |
| 50 / G | 14 | 715 | 865 | 52 | 16.6 | 189 |

Incinerate (19 + 1-21) at Fire 30 GM, cost 30: average 349 / 432 / 544 / 891 / 1464 / 3873 at the same steps, cost
30 / 52 / 75 / 116 / 232 / 773, damage per SP 11.6 / 8.3 / 7.3 / 7.7 / 6.3 / 5.0. Small spells keep their
efficiency because the flat add grows fastest; big spells lose efficiency. Burst and damage per second rise with
Ascension in every case, which is the point of the skill.

### 2.5 Tooltip and consistency issues (do not port)

- The Ascension skill tooltip prints heal multipliers `(1+0.05s)·1.02^s` and `(1+0.03s²)·1.02^s`
  (`MawCore/SkillTooltip.lua:169-170`), not the applied `(1+0.02s)·1.015^s` and `(1+0.01s²)·1.015^s`
  (at s = 20: shows ×2.97 / ×19.3, real ×1.89 / ×6.73). Its mana line multiplies `(mult − 1)` by the mastery
  factor, which is not the applied formula (SkillTooltip.lua:171-172).
- Shaman: two different Ascension sources (§2.1).
- Fixed-per-point spells ignore Ascension on the per-point part (§1.2).

---------------------------------------------------------------------------------------------------------------

## 3. Buff rework (auras)

Data: [data/buff_auras.yml](data/buff_auras.yml). Only the "Buff Rework ON" path is specified; the OFF path is
mostly dead code (SKILLS_SPELLS_ALCHEMY.md §0).

### 3.1 Lifecycle

- **Casting** a buff spell (spellbook action 142 or a cast, SP:2737-2759) never spends SP; it toggles the aura
  (`mawBuffCast`, SP:2788-2861). Cast by a member who does not hold it: that member becomes the holder (ownership
  moves, the old holder's reservation is released), recovery = `getSpellDelay` (no Ascension term), the effect
  animation plays on every member. Cast by the holder: the aura switches off ("Buff Disabled").
- **Check**: the holder's unreserved pool must cover the new reservation (`currentManaPool ≥ cost`), except inside
  a house (SP:2823-2831). There is no check against current SP.
- **Application**: `mawBuffApply` (SP:2863-3008) runs every 0.5 s (TI:95), on map load, after a cast and on
  multiplayer sync. It clears the listed party and member buffs (SP:2647-2649, 2866-2888) and re-sets every held
  aura's engine buff with expiry now + 1 week. An unconscious or dead holder's aura is skipped (no effect) but its
  reservation stays; it resumes when the holder recovers. A holder who left the party gives neither.
- **Reading strength**: every effect site asks `getBuffSkill(spell, pl)` (SP:3204-3215), which returns the holder's
  **base** school skill (no item bonus, SP:3098-3099) capped at 50 (75 for 83, 85, 86; S:169-172), mastery and
  `LevelBase`, or the drinker's potion when stronger (§3.6).
- **R** on the spellbook screen removes every aura (SP:22-27). Nothing else removes them: no duration, rest does not
  clear them.
- **Temple, scroll, pedestal**: a scroll or pedestal (`IsSpellScroll` or target kind 4) stores the map name as the
  holder; a cast while a house screen is open (temple donation) stores "Temple". Both use a fixed caster: skill 7,
  Master, level 40 (`getSpecialBuffSkill`, SP:3079-3081). Map-name auras are dropped on entering a different
  **outdoor** map (they survive dungeons); "Temple" auras are dropped on the next map load (SP:2694-2734).
- **Dispel**: monster Dispel Magic clears expiry times, and the 0.5 s pass restores them; auras are effectively
  immune. MAW does not change Dispel itself.
- **Solo and specials**: a solo party always has Wizard Eye (power 10, skill 2) and Torch (power 3); an NPC
  follower with profession 38 gives Wizard Eye; vampires get Preservation at night and indoors; a Shadow or
  Omnipotent boss within 2000 removes Wizard Eye (SP:2957-3005).

### 3.2 Reservation

`reserved % = cost / (SPFactor[class] + EnlightenmentMastery/2)` of the maximum SP pool (`GetFullSP`), summed over
the auras the character holds; `SP ≤ maxSP − Σ reserved` at all times (`buffManaLock`, SP:3010-3063; regen cap
S:1478-1481). `SPFactor` is the class's SP-per-level factor from `Class HP SP.txt` (snapshot at start, SP:2576-2598):
Cleric/Druid/Sorcerer/Necromancer 3, Priest/Wizard/Great Druid 4, Arch Mage/Lich/Warlock/Priest of Light or Dark/
Arch Druid/High Priest/Master Wizard 6, Elementalist 4/6/8, Paladin/Ranger/Seraphim tier 1 = 1, Shaman 1/1.5/2
(override). Death Knights and the Thief line reserve nothing (pool forced full, SP:3055-3058). Utility auras reserve
a flat `round(cost · (1 − EnlightenmentMastery/10))` (5, 5, 20). Legendary 32 reserves HP instead (HPFactor).
Meditation regen also shrinks with the reserved share: pool `fullSP · (1 − share)^0.5` (FO:208-219).

Reserved percent by SPFactor (Lua, `lua_spells/buffs.lua`):

| Aura (cost) | f=1 | f=2 | f=3 | f=4 | f=6 | f=8 | f=6, Enlightenment GM |
|---|---|---|---|---|---|---|---|
| Resistances (60) | 60 | 30 | 20 | 15 | 10 | 7.5 | 7.5 |
| Pain Reflection (10) | 10 | 5 | 3.3 | 2.5 | 1.7 | 1.2 | 1.2 |
| Immolation (40) | 40 | 20 | 13.3 | 10 | 6.7 | 5 | 5 |
| Shield, Stone Skin, Bless, Fate, Hammerhands (75) | 75 | 37.5 | 25 | 18.8 | 12.5 | 9.4 | 9.4 |
| Fire Aura (90) | 90 | 45 | 30 | 22.5 | 15 | 11.2 | 11.2 |
| Haste, Preservation, Heroism, Meditation, Regeneration (120) | 120 | 60 | 40 | 30 | 20 | 15 | 15 |
| Empower Magic, Day of Protection, Vampiric Aura (150) | 150 | 75 | 50 | 37.5 | 25 | 18.8 | 18.8 |
| Protection from Magic (180) | 180 | 90 | 60 | 45 | 30 | 22.5 | 22.5 |
| Day of the Gods (200) | 200 | 100 | 66.7 | 50 | 33.3 | 25 | 25 |
| Hour of Power (300) | 300 | 150 | 100 | 75 | 50 | 37.5 | 37.5 |

Example: an Arch Mage (f = 6) holding Haste, Shield, Stone Skin, Heroism and Fire Resistance reserves
20 + 12.5 + 12.5 + 20 + 10 = 75 %. A Priest of Light with Day of the Gods, Day of Protection and Hour of Power needs
108 %, so one of them has to go to another caster. Hybrids at f = 1 can hold one cheap aura at most.

### 3.3 Aura table

`m` = holder's school mastery. Multiplier buffs: `Base/100 + Scaling·s/1000`. Flat buffs:
`(Base + level/4) · (1 + Scaling/100 · s)`. Stat part: `min(10 + s/5, 20)` % of the total stat (Light `s/7`).
With s capped at 50 every multiplier and flat buff tops out at double its base.

| Spell | Reserve | Effect | Cap at s = 50 | Applied (code) |
|---|---|---|---|---|
| Fire/Air/Water/Earth/Mind/Body Resistance 3/14/25/36/58/69 | 60 | res `(10 + L/4)(1 + 2 %·s)` to its element, plus Int/Speed/Luck/End/Pers/Might `min(10 + s/5, 20)` % | ×2, 20 % | IT:3017-3058 |
| Fire Aura 4 | 90 | weapons add fire damage = weapon item-level damage × 10/15/20/25 % by mastery, at least 3/6/12/24 (×2 two-handed); also on spells | – | IT:4280-4300 |
| Haste 5 | 120 | attack and spell recovery ÷ `(1.10 + 0.002s)` | 20 % | S:590-597, ST:220-227 |
| Immolation 8 | 40 | engine Immolation, damage 10 + 1-30 per point, Ascension-scaled | – | SP:1897, 2946-2952 |
| Shield 17 | 75 | magic damage taken × `(1 − 0.15 − 0.003s)`, floor 0.7 | 30 % | ST:1075-1080 |
| Empower Magic 28 | 150 | spell dice and add × `(1 + mult)`; **coded with Haste's row**: 10 % + 0.2 %/pt (tooltip 15 + 0.3) | 20 % | SP:2043-2053 |
| Stone Skin 38 | 75 | AC `(20 + L/4)(1 + 2 %·s)` (tooltip says L/2) | ×2 | IT:3077-3081 |
| Bless 46 | 75 | attack `(20 + L/4)(1 + 2 %·s)` melee and ranged, Accuracy `min(10 + s/5, 20)` %, hit chance `+5 % + 5 %·min(s,50)/50` | ×2, 20 %, +10 % | IT:2950-2959, 3069-3074, FO:89-110 |
| Fate 47 | 75 | crit chance `+5 % + 0.1 %·s` | 10 % | ST:113-121 |
| Preservation 50 | 120 | engine Preservation on every member | – | SP:2623 |
| Heroism 51 | 120 | melee damage `×(1 + 0.15 + 0.003s)` on (damage + Might effect) | 30 % | IT:3320-3340 |
| Meditation 56 (was Telepathy) | 120 | party SP/s `(0.01 · fullSP^0.35 · E^1.4 + 1)(1 + 0.02s)`, E = `estimateSkill(holder level)` | – | S:1466-1470 |
| Regeneration 71 | 120 | party HP/s `sqrt(fullHP) · (L^0.65 (1 + 0.05s))^1.25 · 0.005` | – | S:1363-1374 |
| Hammerhands 73 | 75 | unarmed damage `×(1 + 0.15 + 0.003s)` | 30 % | IT:3333-3336 |
| Protection from Magic 75 | 180 | engine PfM, power 50, re-set every 0.5 s (no charge loss), plus Unconscious immunity | – | SP:2904-2907, 676-685 |
| Day of the Gods 83 | 200 | all 7 stats `min(10 + s/7, 20)` % (max with each resistance aura's stat %, not added) | 20 % at s 70 | IT:3039-3074 |
| Day of Protection 85 | 150 | all 6 resistances `(10 + L/4)(1 + 2 %·s/1.4)` (max with single auras) | ×2.07 at s 75 | IT:3035-3058 |
| Hour of Power 86 | 300 | Haste, Shield, Stone Skin, Fate at `s/1.5`, each the stronger of HoP and the own aura | 20/30/×2/10 % | SP:3156-3180, ST:116-119 |
| Vampiric Aura 91 (was Vampiric Weapon) | 150 | party leech +5 % melee, +2.5 % ranged, +2.5 % spell | – | IT:3272-3276 |
| Pain Reflection 95 | 10 | engine Pain Reflection on every member | – | SP:2633 |
| Torch Light 1 | 5 flat | torch power = mastery + 1 | – | SP:2874-2875 |
| Wizard Eye 12 | 5 flat | engine Wizard Eye | – | SP:2637 |
| Water Walk 27 | 20 flat | engine Water Walk | – | SP:2640 |

Fly, Invisibility, Feather Fall, Detect Life and the racial buffs stay timed spells.

Values (Lua): multiplier buffs at s = 0/10/20/30/40/50: Haste 10/12/14/16/18/20 %, Shield and Heroism
15/18/21/24/27/30 %, Fate 5/6/7/8/9/10 %, stat 10/12/14/16/18/20 % (Day of the Gods 10/11.4/12.9/14.3/15.7/17.1 %).
Flat buffs (resistance / AC or attack / Day of Protection): s 7, L 40 (temple caster): 22.8 / 34.2 / 22.0;
s 20, L 50: 31.5 / 45.5 / 28.9; s 30, L 100: 56 / 72 / 50; s 50, L 200: 120 / 140 / 102.9; s 50, L 400:
220 / 240 / 188.6; Day of Protection at s 75, L 400: 227.9.

### 3.4 Meditation and Regeneration auras

Both are multiplied by MAW's regeneration multiplier (`MawRegen`, S:1384-1490): ×2 after 20 s without losing HP
(or SP), ×4 more when no enemy is detected. Meditation does not help classes 10, 11 (Dragons), 34-37 (Thief
line) and 56-58 (Death Knight) (S:1344). Regeneration takes the max of the aura and a Regeneration potion buff
`sqrt(fullHP)·S^1.25·(M+1)/1000`, and uses `buffPower[71].Base` (5) where `Scaling` (2) was meant.

| Holder level, s | Meditation SP/s at max SP 300 / 1000 / 3000 | Regeneration HP/s at max HP 500 / 2000 / 8000 |
|---|---|---|
| 40, 7 | 3.2 / 4.3 / 5.7 | 3.3 / 6.5 / 13.0 |
| 50, 20 | 4.5 / 6.2 / 8.4 | 6.4 / 12.8 / 25.5 |
| 100, 30 | 8.9 / 12.8 / 18.0 | 14.8 / 29.6 / 59.3 |
| 200, 50 | 22.2 / 32.9 / 47.3 | 39.6 / 79.3 / 158.6 |
| 400, 50 | 49.8 / 74.9 / 109.1 | 69.6 / 139.2 / 278.5 |

(in combat after a recent loss: multiplier 1; `estimateSkill` 9.8 / 11.4 / 19.1 / 33.7 / 62.2 at levels 40 / 50 /
100 / 200 / 400, E:73-95.)

### 3.5 Party and member engine buffs

The engine buff slot each aura drives (for save compatibility and HUD icons): party 6/0/17/4/12/1 (resistances),
8 Haste, 10 Immolation, 14 Shield, 15 Stone Skin, 9 Heroism, 13 PfM, 2 Day of the Gods, 16 Torch, 19 Wizard Eye,
18 Water Walk; member 1 Bless, 4 Fate, 11 Preservation, 12 Regeneration, 6 Hammerhands, 10 Pain Reflection. Power
and Skill of the engine buff are mostly zeroed: every MAW effect reads `getBuffSkill`, the engine slot is only an
"on" flag (plus Torch power, PfM power, Immolation caster).

### 3.6 Potions against auras

Per buff, the drinker uses the stronger of the party aura and their own potion (SP:3204-3215), compared by
`Base + Scaling·s/10 (+ level/4 for flat buffs)` (SP:3192-3202). A potion acts as a Master caster with
`s = 50(f − 1)` (70 for 83/85) and `level = 0.5·P·f`, `f = 0.75 + 0.75·min(P, 200)/200` (SP:3111-3135). Haste,
Shield and Stone Skin also compare Hour of Power at `s/1.5` (`bestBuffSource`), Fate does it separately (ST:116-119).
Potions are never consulted for Fate, Meditation, Regeneration and Hammerhands (no player passed). Auras and
potions never add up. Potion effects and power examples: §7.4-7.5.

### 3.7 What changes in OpenYAMM

OpenYAMM's buffs are timed with hard-coded durations and powers (`OpenYAMM/game/party/PartySpellSystem.cpp:1065`
`resolvePartyBuffDurationSeconds`, :1164 `resolvePartyBuffPower`, :1289/:1335 character buffs) on `PartyBuffId` /
`CharacterBuffId` (`OpenYAMM/game/party/Party.h:217-260`). A MAW ruleset needs:

1. An aura state per party: spell → holder (member id, or a fixed temple/scroll caster with a scope: map or
   outdoor region), saved with the game.
2. A reservation pass that recomputes each member's available maximum SP whenever auras, max SP, class or
   Enlightenment change (not on a 0.5 s timer), and clamps SP; regen respects it.
3. Effects computed from the aura table (`buff_auras.yml`) at the use site, not stored as buff power. Drive the
   existing party/character buff slots as "active" flags so HUD icons keep working.
4. Dispel against auras needs an explicit rule (README §6 suggests suppression for N seconds).
5. Spellbook UI: "Reserved: x %, held by NAME" in the tooltip, toggle on cast, and a clear-all action.

---------------------------------------------------------------------------------------------------------------

## 4. Crowd control

Data: [data/crowd_control.yml](data/crowd_control.yml).

### 4.1 CC table (`CCMAP`, SP:1337-1350, extras SP:1441-1449, 1663-1666)

| Spell | Base (game min) | School read for mastery | DR group | Path | Debuff |
|---|---|---|---|---|---|
| Stun 34 | 2 (tooltip only) | Earth | – | engine, scripted roll | engine stun + MMMerge paralysis |
| Slow 35 | 6 | Earth | 1 | scripted | Slow |
| Charm 60 (Mind) | 10 | Mind | 2 | scripted | Charm |
| Charm 113 (Vampire) | 10 | **Dark Elf ability** (bug) | 2 | scripted | Charm |
| Berserk 62 | 4.5 | Mind | 2 | scripted, no engine aim | Berserk |
| Mass Fear 63 | 3 | Mind | 2 | engine path | Fear |
| Fear 122 (Dragon) | 4 | **Mind** (bug) | 2 | engine path | Fear |
| Enslave 66 | 5 | Mind | 2 | scripted, no engine aim | Enslave |
| Paralyze 81 | 3 | Light | 3 | scripted | Paralyze |
| Shrinking Ray 92 | 4, flat | Dark | 1 | impact, m targets | ShrinkingRay, power 2 |
| Dark Grasp 96 | 6 | Dark | 1 | scripted | ArmorHalved, Slow, DamageHalved, MeleeOnly |
| Turn Undead 48 | 5 | Spirit | 2 | engine path, undead only | Fear |
| Control Undead 94 | 10 | Dark | 2 | scripted, undead only | Enslave |

`ChanceMult`, `BaseCost` and `ScalingCost` are only read by Stun (ChanceMult) and by commented-out code.
Shrinking Ray and Dark Grasp's DamageHalved both cut monster damage to ×0.7 and do not stack (DM:1575-1578,
1753-1760).

### 4.2 Duration

`duration = base · step[m] · 1.015^asc / (1 + res/100)` (SP:1406-1427), `step = 0.5 / 0.65 / 0.8 / 1` for N/E/M/G
(mastery < 1 reads as N), Shrinking Ray flat 1; `asc` = Ascension (Learning) level; `res` = the monster's
resistance of the spell's element. Then ×2 for a solo party, then diminishing returns (§4.3), then ÷2 on bosses
(NameId 220-299) for groups 2 and 3 only. Dragon Fear skips the Ascension and resistance terms. Scripted and impact
casts extend an existing debuff (max); engine-path casts cap the engine's own expiry at the MAW value (min).

Real seconds, party, first cast, non-boss (Lua, `lua_spells/cc.lua`):

| Spell | N, asc 0, res 0 | GM, asc 0, res 0 | GM, asc 20, res 0 | GM, asc 20, res 50 | GM, asc 50, res 100 |
|---|---|---|---|---|---|
| Slow, Dark Grasp | 6.0 | 12.0 | 16.2 | 10.8 | 12.6 |
| Charm (both), Control Undead | 10.0 | 20.0 | 26.9 | 18.0 | 21.1 |
| Berserk | 4.5 | 9.0 | 12.1 | 8.1 | 9.5 |
| Mass Fear, Paralyze | 3.0 | 6.0 | 8.1 | 5.4 | 6.3 |
| Enslave, Turn Undead | 5.0 | 10.0 | 13.5 | 9.0 | 10.5 |
| Shrinking Ray (any mastery) | 8.0 | 8.0 | 10.8 | 7.2 | 8.4 |
| Dragon Fear (Mind 0 → N step) | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |

### 4.3 Diminishing returns (SP:1734-1852)

Per monster and group, MAW records every applied CC (start, end). The ratio = CC time of that group inside the last
10 game minutes (20 s; the code comment says 30 s) / 10 minutes. Duration multiplier: ratio ≥ 0.60 → immune
(nothing applied or recorded), ≥ 0.45 → ×0.25, ≥ 0.30 → ×0.5, ≥ 0.15 → ×0.75, else ×1. Group 1 (Slow, ArmorHalved,
DamageHalved, MeleeOnly, ShrinkingRay, and any unlisted debuff) is exempt and skips the boss halving; group 2 =
Fear, Charm, Berserk, Enslave; group 3 = Paralyze. History is per map (`mapvars.ccHistory`, cleared on leaving).

Simulation (Lua): an 8 s group-2 CC recast the moment it ends: 8 s, 4 s, then immune for 9 s, then 2 s. On a boss
the same spell gives 4, 3, 2, 1, 1, 1 s, then immunity: halving after DR lets bosses be controlled more often.
A 3 s stun recast every 3 s settles at 0.8-1.5 s.

### 4.4 Targeting and paths

- **Scripted** (Slow, both Charms, Berserk, Paralyze, Enslave, Dark Grasp, Control Undead; `castCCSpell`,
  SP:1486-1544): target = valid monster under the mouse, else the visible valid monster whose debuff expires
  soonest; valid = alive, visible, hostile, within 4800, undead if required. No target: "Spell Failed", recovery 30,
  no SP. Otherwise SP is spent first, then DR is checked (an immune target wastes the cast), the effect object or
  colour is shown on success, recovery = `getSpellDelay`, and selection moves to the next ready member. Berserk and
  Enslave quick casts bypass the engine's aim mode (SP:1546-1579).
- **Engine path** (Mass Fear, Dragon Fear, Turn Undead; SP:1581-1656): for one tick every monster's resistance and
  level are zeroed (would apply) or the resistance set to 65000 (DR-immune, or a non-undead for Turn Undead), the
  engine applies the debuff, values are restored and the expiry capped to MAW's duration. The `30/(30 + L/4)` roll
  is computed but unused, so these always land.
- **Impact** (Shrinking Ray; SP:1658-1732): the projectile has no damage; on impact the struck monster plus `m − 1`
  others within 512 (nearest unshrunk first, then those whose shrink ends soonest) are shrunk.
- **Stun** (DM:334-357): `chance = 30 / (30 + L/4)`, `L = max(round(((level/4 + res + 30)/(1 + 0.01s) − 30)·4), 0)`,
  L ×2 on bosses (`calcEffectChance`, SP:1855-1865), ×`(1 − affix13/100)`. Success zeroes Earth resistance and level
  for the engine; failure sets resistance 65000.

### 4.5 Cost and delay

Cost: `ceil(SpellsCost[m] · (1 + 0.2s) · 1.03^s · (1 − 0.125m_a) · P)` with the Ascension level and mastery
(SP:2182-2196); Dragon Fear fixed 15/15/25/30. Delay: `round(tableDelay[m] · 1.015^(asc − schoolSkill))`, no
Speed, Haste or armour; Dragon Fear 120 (ST:167, 211-217). So a high school skill shortens CC casts and Ascension
lengthens them.

### 4.6 Other sources that use DR

Mace/Staff Master+ stun (paralysis 1 game minute at M, 2 at GM, chance `s/estimateSkill(level) · 0.15` (mace) or
`0.10` (staff) × melee speed / `min(1 + level/150, 3)`, DM:266-301), Knight Charge (solo, 1.5/2/2.5 minutes,
S:953-1000), Death Knight Icy Touch slow, Asphyxiate paralysis and Death Grasp (DM:262-264, 770-814). Retaliation's
GM stun (25 % per stack, 1 minute, half on bosses) is not DR-tracked (DM:892-898).

### 4.7 What changes in OpenYAMM

`OpenYAMM/game/gameplay/GameplayActorService.cpp:303` (`tryApplySharedSpellEffect`) applies vanilla MMMerge CC:
a resistance roll `100 + s + 2.5·m > resistance` (never at ≥ 200, :80-89) and skill-scaled vanilla durations. A MAW
ruleset needs: the CC table and duration formula, a per-actor DR ledger (three groups, 10-minute window,
saved with the map like other actor state), boss detection (NameId 220-299 maps to our boss flag), the solo
multiplier, scripted target selection for single-target CC, Shrinking Ray multi-target impact and the Stun roll.
Confirm the clock: OpenYAMM stores `...RemainingSeconds` computed with `minutesToSeconds(m) = 60m`, while MAW's
durations are game minutes shown as 2 real seconds each.

---------------------------------------------------------------------------------------------------------------

## 5. Classes

Shorthand for this section and §6 (MAW repo paths): `CL` = `Scripts/General/zzClasses.lua`,
`MCC` = `Scripts/Modules/MawCore/Classes.lua`, `S` = `Scripts/General/zzMAW-Skills.lua`,
`SP` = `Scripts/General/zzMaw-Spells.lua`, `ST` = `Scripts/General/zzMaw-Stats.lua`,
`IT` = `Scripts/General/zzMaw-Items.lua`, `DM` = `Scripts/Modules/MawCore/Damage.lua`,
`F` = `Scripts/Modules/MawCore/Formulas.lua`, `TT` = `Scripts/Modules/MawCore/SkillTooltip.lua`,
`SK` = `Scripts/Modules/MawCore/Skills.lua`. `s` = skill level, `m` = mastery 0..4. One game minute = 2 real
seconds (F:10). "Armsmaster way" means the bonus is added to the weapon's flat damage, multiplied by the weapon
skill's damage % and halved when an off-hand weapon is held (IT:2878-2919).

Data: [data/class_perks.yml](data/class_perks.yml), [data/promotions.yml](data/promotions.yml). Class-specific
spells (Death Knight, Assassin, Elementalist rotation, Dragon) are in [data/spells.yml](data/spells.yml).

### 5.1 Registry and shared class rules

| Class line | Ids | Kind | Source |
|---|---|---|---|
| Seraphim, Angel, Archangel | 53-55 | 17 | MCC:647, `Class Extra.txt` |
| Death Knight, Death Lord, Lich King | 56-58 | 18 | MCC:649 |
| Shaman, Sekhem, Marabou | 59-61 | 19 | MCC:648 |
| Elementalist, Elemental Adept, Master of Elements | 62-64 | 20 | MCC:651 |
| Thief, Rogue, Assassin, Spy ("assassin" rework) | 34-37 | 11 | MCC:653-655 |

Shared rules:

- Spell books cannot teach Death Knights, Elementalists or Assassins (`CanLearnSpell` NeedMastery = 5,
  MCC:482-493, 589-593).
- Death Knights and Assassins reserve no mana for buffs: their current mana pool is forced to the maximum
  (SP:3055-3058).
- The Meditation buff gives no SP regeneration to classes 10, 11 (dragons), 34-37 (thief line), 56-58 (DKs)
  (S:1344, 1467).
- For Seraphim, Shaman, Death Knight and Assassin the "second skill costs less" set is magic 12-22 only
  (S:240-241).
- Class presentation (school names, spell texts and costs) is swapped when a character is selected
  (`Classes.present`, MCC:679-694). An engine does not need this; per-character tables do it.

### 5.2 Seraphim (holy melee)

HP 40 + 3/4/5 per level, SP 15 + 1/2/3 per level from Personality (`Class HP SP.txt`). Perks:

| Perk | Formula | Source |
|---|---|---|
| Mind: holy damage | `s·(m+1)/2` flat melee damage, armsmaster way (1/1.5/2/2.5 per point) | IT:2888-2893 |
| Body: heal on hit | `round(s^1.3 · m · 2 · meleeDamageMult · (1 + Personality/1000))` HP to the lowest HP % member, per physical melee hit; clears Unconscious | DM:106-150 |
| Light: attack speed | `+ s·m/2` % (0.5/1/1.5/2 % per point) | S:536-539 |
| Light: blade | two-handed swords equip as one-handed, so a shield fits; no level gate | CL:170-226 |
| No sword dual wield | `CanDualWield` false for swords | S:1787-1792 |
| Spirit: flat reduction | `flat = round(monsterDamage(L+1) · s/estimateSkill(L) · avgTaken/2 · 0.99^estimateSkill(L))`, L = total level; `damage = max(damage − flat, 0.25·damage)` after resistances | ST:742-776 |
| Divine Protection | a hit ≥ current HP: heal 25 % max HP and the hit leaves 1 HP; cooldown 150 game minutes (5 real minutes) | DM:1888-1905 |

Worked heal-on-hit values (Lua, damage multiplier 1, Personality 100/500): s5 N 18/24, s10 E 88/120, s20 M 324/442,
s30 G 732/999, s50 G 1423/1940. The class description (CL:164) still describes the old "2 per point in Light and
Mind" rules.

### 5.3 Death Knight

HP 35 + 4/5/7, SP fixed 60/80/100 (SPFactor 0), no SP from items (MCC:838-840). Schools renamed Frost (Water),
Blood (Body), Unholy (Dark) (MCC:212-214).

Resource: each physical melee hit restores 10/15/20 SP (Death Knight/Death Lord/Lich King), ×1.5 on a killing hit
(MCC:17-21, DM:784-791). Blood Leech and Death Grasp are toggles paid per hit.

Spells by mastery (opening the spellbook wipes spells 1-99 and grants these, MCC:458-480):

| School | N | E | M | G |
|---|---|---|---|---|
| Frost | 26 Icy Touch (15) | 27 Water Walk (0) | 29 Frostbite (30) | 32 Ice Bomb (50) |
| Blood | 68 Blood Leech (6/hit) | 71 Regeneration (0) | 76 Asphyxiate (70) | 74 Superior Blood Leech (12/hit) |
| Unholy | 91 Vampiric Aura (0) | 90 Death Coil (30) | 96 Death Grasp (15/hit) | 97 Death Breath (100) |

Weapon-damage spells (`DKDamageMult`, MCC:23-30; DM:698-742): damage = melee roll × crit + weapon enchant damage,
÷ the spell element's resistance, × melee damage multiplier, ×0.5 if Weak, × the multiplier for the governing
school's mastery: Icy Touch [1, 1, 1.2, 1.2] (Frost), Frostbite [1.5, 1.5, 1.5, 2] (Frost), Ice Bomb 0.75 per
shard, Asphyxiate [1.1, 1.1, 1.1, 1.4] (Blood), Death Coil [1, 1, 1, 1.2] (Unholy), Death Breath 0.6. Spell delay
equals the attack delay (MCC:877-886). Costs are fixed (no Ascension, MCC:108-131).

Spell effects: Icy Touch at Frost ≥ E slows (power `floor(m/2)·2`, 1 game minute, through diminishing returns,
DM:795-807); Asphyxiate paralyses 2 game minutes (DM:808-814); Death Coil heals 20 % of the damage dealt, 30 % only
at Unholy Master exactly (DM:1285-1293); Death Grasp makes the target deal ×0.7 damage for 1 game minute per hit,
GM adds MeleeOnly (DM:262-264, 770-783); Blood Leech heals `max(FHP^0.5 · s^1.5/70 · (1 + m/4), 2s)` per hit,
Superior ×2 (F:248-250, DM:743-768). Examples: FHP 1000 s10 E → 21 HP/hit; FHP 5000 s30 G → 332 (Superior 664).

Passives:

| School | Effect | Source |
|---|---|---|
| Frost, Unholy | flat melee damage `GetGradualMasteryValue({0.5, 0.75, 1, 1}, s, m) · s` each, armsmaster way | S:155, IT:2880-2887, ST:1480-1505 |
| Frost | `+s` % attack speed | S:532-535 |
| Blood | physical damage taken ÷ `(1 + s/100)`; +10 % melee / +5 % ranged physical leech (stacks with vampiric) | ST:778-787, 1063; IT:3286-3290 |
| Unholy | non-physical damage taken ÷ `(1 + s/100)` | ST:1072 |

`GetGradualMasteryValue` ramps a rank's value from the previous rank's value between the mastery thresholds
(normal 0/4/7/10; GM ramps to 1.4× its threshold), so a fresh mastery is a gradual gain. Per-school totals (Lua):
s3 N 1.1, s5 E 2.9, s8 M 6.7, s10 G 10, s50 G 50.

Toggling: clicking 68, 74 or 96 in the spellbook (action 142) toggles "on attack" (MCC:843-857). The quick-cast
branch (MCC:859-874) compares and stores `t.Param` instead of the spell id, so toggling by quick cast is broken.
Blood Leech subtracts its 6 SP per hit without checking the current SP (DM:754-757).

### 5.4 Shaman

HP 25 + 3/4/5, SP 10 + 1 per level, Intellect+Personality. Every school gives a melee perk:

| School | Effect | Source |
|---|---|---|
| Fire | melee adds `max(0.001·s · monster current HP, s)` fire damage, ÷ fire resistance | DM:1047-1054 |
| Air | all damage taken (physical and magic) ÷ `(1 + s/100)` | ST:778-781 |
| Water | flat reduction, same formula as Seraph Spirit | ST:742-776 |
| Earth | `s·m/2` flat melee damage, armsmaster way | IT:2894-2898 |
| Spirit | melee damage × `(1 + s/100)` (like Heroism) | IT:3338-3347 |
| Mind | `+s^1.25` SP per melee hit | DM:673-693, F:242-244 |
| Body | `+max(round(FHP^0.5 · s^1.5/70 · (0.5 + m/2)), s)` HP per melee hit | DM:673-693, F:237-239 |

Spells: damage of spells 1-98 except 44 × `(1 + Σ(Fire..Body skill)/200)` (DM:1118-1128); healing-spell per-point
scaling × `(1 + Σ/400)` (SP:2370-2380). Ascension for spell cost and healing is `Σ(Fire..Body)/7` with mastery forced
to GM (SP:2251-2259). Spell damage (SP:1956) and cast time (ST:176-188) read the Learning skill instead, and
`Class Skillz.txt` gives Shamans no Learning, so Shaman spell damage and cast time never ascend while costs do.

Worked values (Lua): FHP 1000 s10 E Body 21 HP/hit, Mind 17.8 SP/hit, Fire 1 % of current HP; FHP 5000 s30 G 415 HP,
70 SP, 3 %.

### 5.5 Elementalist

HP 15 + 2/2.5/3 (2.5 set in Lua, CL:606), SP 30 + 4/6/8, Intellect.

- **Learns by casting** (DM:152-195). Each hit of an own offensive spell 1-44 on a hostile monster adds
  `tier^1.5 · monsterLevel^0.5 · √(Party.Count)` (no party factor in Insanity) to that school's progress, ÷3 for AoE
  spells except Sparks and Poison Spray (`aoespells`, SP:2094). Tier t unlocks at progress
  `[0, 0, 500, 1500, 5000, 10000, 20000, 40000, 80000, 160000, 320000][t]` (MCC:43) and school mastery
  `[N, N, N, N, E, E, E, M, M, M, G][t]` (DM:155). Insanity: Invisibility needs GM. Always known: Fire Bolt,
  Sparks, Poison Spray, Deadly Swarm (MCC:495-507). Hits needed (Lua, level-50 targets, party 4, single target of
  the previous tier): tier 3 ≈13, tier 5 ≈31, tier 8 ≈77, tier 11 ≈358.
- **Ascension** = `Σ(Fire..Earth)/4` (floored for cast time) with mastery forced to GM (SP:2239-2250, 1958-1968,
  ST:180-187). The class cannot learn Learning.
- **Base casts 50 % slower** (ST:228-229).
- **Stacks k** (+1 per offensive cast, MCC:532-537): damage dice max and flat add × `(1 + 0.1k)` (SP:1970-1973);
  delay × `1.5/(1 + 0.05k)` (ST:228-236); cost `ceil(round((base + k) · (1+0.125a) · 1.04^a · 0.5) · (1 + 0.075k) ·
  personality)` (SP:2270-2272). k=4: ×1.4 damage, delay ×1.25; k=10: ×2 damage, delay ×1.0.
- **Decay**: after `max(4 · spellDelay, 128)` ticks without a cast the stacks halve (floor) every 0.5 game minute
  (MCC:300-315, 533; `zzMaw-Timers.lua:97`). **Reset**: a melee or arrow hit (DM:197-209) or quick-binding an
  offensive spell in the spellbook (MCC:541-553).
- **Rotation** (MCC:45-61, 317-349, 509-587): on the spellbook screen each of the six cast slots (four extra quick
  spells, attack spell, quick spell) records a category from its spell: single `{2, 11, 20, 26, 29, 37, 39}`,
  shotgun `{2, 15, 24, 37}`, aoe indoor `{6, 10, 18, 32, 41}` / outdoor `{6, 9, 18, 22, 32, 41, 43}` (single is
  checked first). After a cast the slot is replaced by a random known spell of its category. **R** on the skills
  screen toggles it (S:2263-2269). Stack gain lives inside the rotation handler, so with the rotation disabled, or
  before the spellbook screen has been opened once, casts build no stacks.

### 5.6 Assassin (Thief line rework)

HP 25 + 3/4/5/5 (was 35 + 4/6/8/8), SP = energy 60/70/80/80 flat (was 0 + 0/1/1/1); items give no SP, instead
`+10 · Assassination mastery` (SP:3628-3634). Schools renamed Combat (Fire), Subtlety (Air), Poisons (Water),
Assassination (Earth) (MCC:257-260). Combo points 0-5 (shown above the portrait, CL:693-704).

| School | Effect | Source |
|---|---|---|
| Combat | melee costs `50 − 5m` energy (unskilled 50 … G 30), arrows half; chance `0.10 + 0.01s` to refund 15 energy (arrows half chance, spells none) | MCC:365-387 |
| Subtlety | each paying melee hit +1 speed stack (+0.5 arrow), max 5, attack speed `+ s·stacks/2` %, stacks drop 4 game minutes after the last paying hit; a kill refunds `(1+m)·5` energy and gives +1 combo point | MCC:388-413, S:540-550 |
| Poisons | energy regeneration `(0.6 + 0.2m)·10` per second (6/8/10/12/14); melee adds `max(0.001·s · current HP, s)` water damage ÷ water resistance | S:1478-1481, F:262-264, DM:1055-1062 |
| Assassination | flat damage `s·(1+m)` (2/3/4/5 per point), armsmaster way, × Heroism; cut by `min(0.8, 0.2·(n−1))`, n = living monsters within 384 of the target, target included (arrows/spells: half the cut) | IT:2899-2912, MCC:365-432, DM:467-481 |

Combo points: +1 per paying melee hit, +0.5 per paying arrow, +1 per kill. A melee hit without enough energy (or on
a non-hostile) loses the whole flat Assassination bonus and builds nothing (MCC:431). Spells are known by mastery
(Combat m+1, Subtlety m+2, Poisons m+1, Assassination m+1 entries of their lists, MCC:96-101, 595-625), cost energy
and combo points (Fireball 5, Fire Spike 3, Lightning Bolt 5, Poison Spray 3, Acid Burst 3, Stun 3, Blades 3, Mass
Distortion 4) and deal 75-400 % of a melee hit (MCC:69-94, DM:820-870). Spell delay = 2 × attack delay
(MCC:448-450). Full list in spells.yml.

### 5.7 Vanilla classes: HP/SP, skill caps, starting skills

`Class HP SP.txt` (OpenYAMM `class_multipliers.txt` is identical to base MMMerge today):

| Class | Base MMMerge HPBase/HPFactor/SPBase/SPFactor/Stat | MAW |
|---|---|---|
| Priest of the Light, Priest of the Dark, High Priest | 30/3/15/5/P | 30/4/15/6/P |
| Patriarch | 25/4/10/4/I | 25/5/10/4/I |
| Dragon | 50/10/50/5/I | 50/5/50/0/I; Lua SPBase 60 (CL:320-322) |
| Great Wyrm | 50/10/50/10/I | 50/10/120/0/I; Lua SPBase 120 (CL:323-325) |
| Warlock, Arch Druid | 20/4/10/5/IP | 20/4/10/6/IP |
| Knight, Cavalier | 35/5, 35/7 | 35/4, 35/6 |
| Minotaur, Minotaur Lord | 30/4, 30/6 | 30/6, 30/12 (also CL:667-671) |
| Monk | 35/5 | 35/4 |
| Master, Ninja | SPFactor 1 | SPFactor 2 |
| Ranger, Hunter, Bounty Hunter, Ranger Lord | SPBase 0; Ranger 0/0/- | SPBase 5; Ranger 5/1/IP |
| Thief, Rogue, Assassin, Spy | 35/4/0/0/-, 35/6/0/1/I, 35/8/0/1/I ×2 | 25/3/60/0/I, 25/4/70/0/I, 25/5/80/0/I ×2 |
| Troll, War Troll | 45/5, 45/8 | 45/6, 45/12 |
| Nosferatu | 30/4 | 30/5 |
| Lich, Arch Mage, Dark ArchMage, Master Wizard | HPFactor 3 | HPFactor 4 |

New rows: see §5.1 classes and `class_perks.yml` (`new_rows`).

**Skill caps.** The authoritative table is `Class Skillz.txt`: `SK:265-285` parses it and `projectEngineTable`
(SK:350-362, called at SK:874-876) overwrites `Game.Classes.Skills`, so the engine and trainers read it.
`Class Skills.txt` differs from it in about 90 cells and only feeds base MMMerge before the overwrite. Letters
N/B=1, E, M, G, S=Supreme (Black Knight/Champion Armsmaster), `=`/`-` none. Per-cell diff of base MMMerge
`Class Skills.txt` against MAW `Class Skillz.txt` (rows 0-38, vanilla classes; `-` = none):

```text
Staff: Archer N→E, WarriorMage N→M, MasterArcher N→M, Sniper N→M, Druid N→E, GreatDruid N→M, Warlock N→M, ArchDruid
    N→M, Knight E→M, Cavalier E→M, BlackKnight E→G, Champion E→G, Paladin N→E, Crusader N→M, Hero N→M, Villain N→M,
    Ranger N→E, Hunter N→E, BountyHunter N→E, RangerLord N→E, Vampire -→E, Nosferatu -→M
Sword: WarriorMage E→M, MasterArcher E→M, Sniper E→M, MinotaurLord E→M, Hunter E→M, BountyHunter E→M, RangerLord
    E→M, WarTroll M→G
Dagger: Archer E→M, WarriorMage E→M, MasterArcher E→G, Sniper E→G, Wizard E→M, Lich E→M, ArchMage E→M, Dark Archmage
    E→M, Master Wizard E→M
Axe: WarriorMage E→M, MasterArcher E→M, Sniper E→M, Knight E→M, Cavalier E→M, BlackKnight M→G, Champion M→G,
    Minotaur E→M, MinotaurLord M→G, Crusader E→M, Hero E→M, Villain E→M, Ranger M→E
Spear: Archer M→E, DarkElf -→E, Patriarch -→M, Crusader E→M, Hero E→M, Villain E→M, Hunter E→M, BountyHunter E→G,
    RangerLord E→G, WarTroll E→M
Bow: Cleric N→E, Priest N→M, PriestLight N→M, PriestDark N→M, Druid N→E, GreatDruid N→E, Warlock N→E, ArchDruid N→E,
    BlackKnight E→M, Champion E→M, BountyHunter M→G, RangerLord M→G, Rogue E→M, Assassin E→M, Spy E→M, Troll N→E,
    WarTroll N→M, High Priest N→M
Mace: Cleric M→E, BlackKnight M→G, Champion M→G, Assassin E→M, Spy E→M, Nosferatu E→M
Shield: Cleric M→E, Thief N→-, Rogue N→-, Assassin N→-, Spy N→-, Troll -→E, WarTroll -→M
Leather: Knight M→E, Cavalier M→E, BlackKnight M→E, Champion M→E, Wizard E→M, Lich E→M, ArchMage E→M, Dark Archmage
    E→M, Master Wizard E→M
Chain: PriestLight E→M, PriestDark E→M, MinotaurLord M→G, Paladin E→M, Crusader E→M, Hero E→M, Villain E→M, Assassin
    E→M, Spy E→M, High Priest E→M
Plate: Minotaur M→E, MinotaurLord M→E, Hero M→G, Villain M→G
Fire: Archer N→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter N→E, BountyHunter E→M,
    RangerLord E→M, Thief -→E, Rogue N→M, Assassin N→G, Spy N→G
Air: Archer N→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter N→E, BountyHunter E→M, RangerLord
    E→M, Thief -→E, Rogue N→M, Assassin N→G, Spy N→G
Water: Archer N→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Patriarch M→G, Ranger -→E, Hunter N→E,
    BountyHunter E→G, RangerLord E→G, Thief -→E, Rogue N→M, Assassin N→G, Spy N→G
Earth: Archer N→E, WarriorMage E→M, MasterArcher M→G, Sniper M→G, Ranger -→E, Hunter N→E, BountyHunter E→M,
    RangerLord E→M, Thief -→E, Rogue N→M, Assassin N→G, Spy N→G
Spirit: Minotaur N→E, MinotaurLord E→M, Paladin N→E, Crusader E→M, Hero M→G, Villain M→G, Ranger -→E, Hunter N→E,
    BountyHunter E→M, RangerLord E→M
Mind: Minotaur N→E, MinotaurLord E→M, Paladin N→E, Crusader E→M, Hero M→G, Villain M→G, Ranger -→E, Hunter N→E,
    BountyHunter E→M, RangerLord E→M, Vampire E→M, Nosferatu M→G
Body: Minotaur N→E, MinotaurLord E→M, Paladin N→E, Crusader E→M, Ranger -→E, Hunter N→E, BountyHunter E→M,
    RangerLord E→M
Light: MasterArcher N→G, Hero N→G, RangerLord -→E, High Priest M→G, Master Wizard M→G, n/u M→G
Dark: Sniper N→G, Villain N→G, BountyHunter -→E, High Priest M→G, Master Wizard M→G, n/u M→G
IdentifyItem: Archer -→M, WarriorMage -→M, MasterArcher -→G, Sniper -→G, Cleric -→N, Priest -→N, PriestLight -→N,
    PriestDark -→N, Knight -→N, Cavalier -→E, BlackKnight -→E, Champion -→E, Minotaur -→N, MinotaurLord -→N, Monk
    -→E, Initiate -→M, Master -→M, Ninja -→M, Paladin -→E, Crusader -→M, Hero -→M, Villain -→M, Troll -→N, WarTroll
    -→N, Dark Archmage M→G, Peasant -→N, n/u -→N, High Priest -→N, Master Wizard M→G
Merchant: PriestLight M→G, PriestDark M→G, Monk -→N, Initiate -→N, Master -→N, Ninja -→N, Hero E→M, Villain E→M,
    Ranger N→M, Hunter N→M, BountyHunter N→M, RangerLord N→M, Peasant -→N, n/u -→N, High Priest M→G
Repair: MasterArcher E→M, Sniper E→M, Dragon -→N, GreatWyrm -→N, Druid -→N, GreatDruid -→N, Warlock -→N, ArchDruid
    -→N, Minotaur -→N, MinotaurLord -→N, Monk -→N, Initiate -→N, Master -→N, Ninja -→N, Vampire -→N, Nosferatu -→N,
    Sorcerer -→E, Necromancer -→E, Lich -→M, ArchMage E→M, Dark Archmage E→M, Peasant -→N, n/u -→N, Master Wizard
    E→M
Bodybuilding: WarriorMage E→M, MasterArcher E→M, Sniper E→M, Cleric N→M, Priest N→M, PriestLight N→M, PriestDark
    N→M, DarkElf -→E, Patriarch -→M, GreatWyrm M→G, Druid -→E, GreatDruid -→E, Warlock -→E, ArchDruid -→E,
    BlackKnight M→G, Champion M→G, Hunter E→M, BountyHunter E→M, RangerLord E→M, Vampire -→E, Nosferatu -→M,
    Sorcerer -→E, Wizard -→E, Necromancer -→E, Lich -→E, ArchMage -→E, Dark Archmage -→E, Peasant -→N, High Priest
    N→M, Master Wizard -→E
Meditation: WarriorMage E→M, MasterArcher E→M, Sniper E→M, PriestLight M→G, PriestDark M→G, Patriarch E→G, Dragon
    M→-, GreatWyrm M→-, Minotaur -→E, MinotaurLord -→M, Monk -→E, Initiate -→M, Master -→G, Ninja -→G, Hero E→M,
    Villain E→M, Ranger N→E, Hunter N→M, BountyHunter N→M, RangerLord N→M, Rogue -→E, Assassin -→M, Spy -→M, Vampire
    -→E, Nosferatu -→G, Lich M→G, ArchMage M→G, High Priest M→G, Master Wizard M→G
Perception: Cavalier E→M, BlackKnight E→M, Champion E→M, Paladin N→E, Crusader N→M, Hero N→M, Villain N→M, WarTroll
    N→E
Regeneration: Dragon E→M, GreatWyrm E→G, Minotaur -→N, MinotaurLord -→E, Monk -→N, Initiate -→E, Master -→E, Ninja
    -→E, Vampire E→M, Nosferatu M→G
DisarmTraps: Cleric -→N, Priest -→N, PriestLight -→N, PriestDark -→N, Dragon -→N, GreatWyrm -→N, Druid -→N,
    GreatDruid -→N, Warlock -→N, ArchDruid -→N, Knight N→E, Cavalier N→M, BlackKnight N→M, Champion N→M, Paladin
    -→N, Crusader -→N, Hero -→N, Villain -→N, Sorcerer -→N, Wizard -→N, Peasant -→N, n/u -→N, High Priest -→N
Dodging: Dragon -→M, GreatWyrm -→G, Thief M→E, Assassin M→G, Spy M→G
Unarmed: Dragon -→M, GreatWyrm -→G, WarTroll E→M
IdentifyMonster: Archer -→N, WarriorMage -→N, MasterArcher -→N, Sniper -→N, Cleric E→M, Priest E→G, PriestLight E→G,
    PriestDark E→G, DarkElf -→N, Patriarch -→N, Knight N→E, Cavalier N→E, BlackKnight N→E, Champion N→E, Minotaur
    -→N, MinotaurLord -→N, Paladin -→M, Crusader -→M, Hero -→G, Villain -→G, Thief -→N, Rogue -→N, Assassin -→E, Spy
    -→E, Peasant -→N, n/u -→N, High Priest E→G
Armsmaster: MasterArcher E→M, Sniper E→M, Cleric -→E, Priest -→E, PriestLight N→E, PriestDark N→E, Patriarch E→M,
    Cavalier M→G, BlackKnight G→S, Champion G→S, Minotaur M→E, Monk M→-, Initiate M→-, Master M→-, Ninja M→-,
    Crusader E→M, Hero E→M, Villain E→M, Thief M→-, Rogue M→-, Assassin M→-, Spy M→-, Vampire N→M, Nosferatu N→G,
    High Priest N→E
Alchemy: DarkElf E→M, Patriarch E→G, GreatDruid M→G, Knight -→N, Cavalier -→N, BlackKnight -→N, Champion -→N, Monk
    -→M, Initiate -→G, Master -→G, Ninja -→G, Paladin -→N, Crusader -→E, Hero -→E, Villain -→E, Ranger N→M, Hunter
    N→G, BountyHunter N→G, RangerLord N→G, Thief E→M, Rogue E→G, Assassin M→G, Spy M→G, Troll -→E, WarTroll -→E,
    Nosferatu M→G, Wizard M→G, ArchMage M→G, Dark Archmage M→G, Peasant -→N, n/u -→N, Master Wizard M→G
Learning: MasterArcher M→G, PriestLight M→G, PriestDark M→G, DarkElf E→M, Patriarch E→G, Dragon M→-, GreatWyrm G→-,
    Warlock M→G, ArchDruid M→G, Knight N→-, Cavalier N→-, BlackKnight N→-, Champion N→-, Minotaur N→M, MinotaurLord
    N→G, Paladin N→M, Crusader N→M, Hero N→G, Villain N→G, Ranger E→M, Hunter E→M, BountyHunter E→G, RangerLord E→G,
    Thief E→-, Rogue E→-, Assassin E→-, Spy E→-, Troll N→-, WarTroll N→-, Vampire N→M, Nosferatu N→G, Lich M→G,
    ArchMage M→G, Dark Archmage M→G, High Priest M→G, Master Wizard M→G
```

Caps of the twelve new classes and the extended skills 50-53 (Cover, Mana Shield, Enlightenment, Retaliation) are
listed in `class_perks.yml` (`skill_caps.new_classes`). Lua also forces Dragon Fangs/Scales caps to M/G (CL:338-342).

**Starting skills** (`Class Starting Skills.txt`, column = class id / 2; the labels of columns 27-31 are wrong but
only 26, 28, 29, 31 are used by step-0 classes): Seraphim free Sword, Light; Death Knight free Axe, Plate, Dark,
Perception; Shaman free Dagger, Earth (choices include Learning, which its caps forbid); Elementalist free Staff,
Fire. Vanilla: Thief free Fire/Air/Water/Earth and loses Dodging, Stealing, Learning; Rogue loses Learning; Knight
free Plate instead of Leather; Paladin Plate instead of Leather; Ranger Bow free, Perception choice; Vampire Dagger
free, Sword choice; Dragon loses Learning. `Class Starting Skillz.txt` is read by no script.

### 5.8 Knight line extras

- **Charge** (S:950-1037): key E, solo party only, knights 16-19. Target 500-3000 units away; the party dashes in
  20 frames; the target is paralysed 1.5/2/2.5/2.5 game minutes (Knight/Cavalier/Black Knight/Champion) through
  diminishing returns; cooldown 25 s (`zzMaw-Timers.lua:99`).
- **Armsmaster Supreme** (S:2587-2620): at GM Armsmaster with base skill ≥ 30 (50 Insanity, 70 Madness), every melee
  weapon skill gets `+floor(armsmaster/10)`, capped at twice the base skill. Black Knight/Champion reach `S`.

### 5.9 Promotions (CL:7-155)

- `promotionList[kind]` holds MM6 (2 qbits), MM7 (4 qbits) and MM8 (qbit plus an award index < 105 or a second
  qbit) for every kind; MAW kinds reuse Cleric (Seraphim), Knight (DK), Druid (Shaman) and Sorcerer (Elementalist).
  Several vanilla kinds share another kind's qbits (Dark Elf/Ranger/Thief → Archer on MM6, Monk → Troll on MM8 ...).
  Full table in `promotions.yml`.
- On every map load and global event `n` = number of worlds with a completed promotion for the kind (0-3). Any member
  of that kind with step < 2 becomes a step-2 class, a step-0 character skipping step 1. With several step-2 classes
  (e.g. Cleric → Light, Dark or High Priest; Sorcerer → Arch Mage, Dark ArchMage, Master Wizard) one is chosen
  **at random** (CL:111-129).
- `n ≥ 2`: every step-2 class of the kind gets HPFactor and SPFactor × `0.75 + 0.25n` (×1.25 "Elder", ×1.5
  "Ultimate") and its name changed (CL:62-108). This rewrites the global class table. Examples: Champion 8 → 10/12 HP
  per level; Master of Elements SP 8 → 10/12; Archangel HP 5 → 6.25/7.5.
- MAW kinds have a mid promotion (step 0 → 1) from the first-tier qbits of the borrowed line (CL:50-60, 131-145).
- Lich at level 1 is reset to Necromancer once (CL:723-733).
- Bugs: the global `promotionCount` is overwritten with the candidate class list while iterating the party
  (CL:117), which can spuriously promote a later member in the same call; MM8 awards are read from `Party[0]` only.

OpenYAMM today promotes only when event scripts set the class (`OpenYAMM/game/events/EventRuntime.cpp:576`, 9934);
promotion trees come from `class_extra.txt` kind/step (`OpenYAMM/game/tables/ClassSkillTable.cpp:412-500`) with a
hard-coded fallback (`OpenYAMM/game/party/SkillData.cpp:357-604`); class names are a fixed 53-entry array
(`OpenYAMM/game/party/SkillData.cpp:47`). MAW needs: 12 more class ids, a qbit-driven promotion check after qbit
changes, a rule for the random pick (deterministic or a choice dialog is better), and Elder/Ultimate as a
per-character multiplier rather than a class-table rewrite.

### 5.10 Dragon (race + classes 10/11)

Dragons are handled by race (portrait race 5). Summary (details and worked numbers in `race_bonuses.yml`):
Fangs (Unarmed) and Scales (Dodging) renamed and auto-learned; melee and breath damage are computed from an
effective level (LevelBase, halved when far above the party, cap 600/900) instead of weapons (MCC:715-815); Flame
Blast 25/40/50/60 SP, 0.7/0.85/1.0 of breath damage, delay 1.5 × ranged delay (CL:309-318, DM:632-668); Dragon Fear
15/15/25/30 SP, delay 120 (SP:1385-1389, ST:167); fixed SP pool 60/120 refilled +10/+20 per melee hit and +2/+5 per
second; items ×3; cannot dodge; Meditation removed and refunded; HP 5/10 per level; starting physical stats 14/50.

Worked values (Lua, Might 100, party level = level): level 20, Fangs 10 E: melee 106-177, attack +40, recovery ×1.15;
level 100, Fangs 30 M: 935-1559, +130, ×1.45; level 200, Fangs 50 G: 3725-6208, +260, ×1.75. Breath at the same
skills: 80-133, 658-1097, 2426-4043.

### 5.11 OpenYAMM mapping

| Need | Where |
|---|---|
| 12 new class rows, HP/SP changes | `class_extra.txt`, `class_multipliers.txt`, `english/class.txt`; extend `CanonicalClassNames` (`OpenYAMM/game/party/SkillData.cpp:47`) |
| Caps from `Class Skillz.txt`, `S` mastery for Armsmaster | `class_skills.txt` plus a fifth mastery level in `SkillMastery` |
| Starting skills/stats | `class_starting_skills.txt` (3 used new columns), `class_starting_stats.txt` |
| Class perks | data-driven hooks (`class_perks.yml`): flat damage, % reductions, on-hit heal/leech/SP, attack speed per school; named behaviours for DK spell book, Elementalist learning/rotation/stacks, Assassin energy/combo, Divine Protection |
| Fixed SP pools and "no SP from items" | per-class flags in the class table |
| Promotions | qbit-driven promotion table (`promotions.yml`) |

## 6. Races

Data: [data/race_bonuses.yml](data/race_bonuses.yml).

### 6.1 Flat skill bonus (S:2348-2400)

`GetSkill` returns `skill + bonus + floor(baseSkill/10)` for the listed skills, also when the skill is unlearned
(level 3 at mastery 0).

| Race | +3 (+1 per 10 base levels) |
|---|---|
| Human | Leather, Chain, Plate, Shield |
| Dark Elf, Elf | Bow, Spear, Meditation |
| Minotaur | Axe |
| Troll | Regeneration, Mace, Staff |
| Goblin | Sword, Mace, Dagger, Leather |
| Dwarf | Shield, Bodybuilding (the Race PDF also says Axe; the code does not) |
| Vampire, Dragon, Undead, Zombie | none |

### 6.2 Mastery modifiers

`Race Skills.txt` is dead data in MAW: MAW ships an empty `Scripts/Structs/RacialSkills.lua`, replacing the MMMerge
struct that read it. Only `Race Skillz.txt` applies, through the Skillz port (SK:216-247, 288-303, 336-346): per
character `v = classCap + shift`, then clamp to the token's max and min. The shift applies even when the class has
no cap (cap 0 + `+` = Novice), and `0` forbids the skill. Race limits reach the engine only at trainers, where the
class row is swapped per player (`Scripts/Modules/MawCore/SkillsUI.lua:558-599`).

| Race | Tokens |
|---|---|
| Human | `+` on Identify Item, Merchant, Repair, Perception, Disarm Traps, Identify Monster, Alchemy |
| Vampire | Vampire Ability min M |
| Dark Elf | Dark Elf Ability min M |
| Minotaur | Dagger 0, Axe min E |
| Troll | Regeneration `+` |
| Dragon | all weapons and armour 0; Dragon Ability, Dodging, Unarmed min M |
| Dwarf | Axe min E |

Dropped versus base MMMerge (OpenYAMM `race_skills.yml` today): Human Learning +1; Vampire Perception +1; Dark Elf
Merchant +1; Minotaur Axe +1, Plate min E +1, Bodybuilding +1; Dragon Identify Monster +1; Elf Meditation +1; Goblin
Disarm +1; Dwarf Axe +1, Repair +1; forced Meditation E for Vampire/Dark Elf/Dragon casters; racial abilities min E
(now M).

OpenYAMM's rule (`OpenYAMM/game/tables/ClassSkillTable.cpp:365-410`) is MMMerge's: `max(cap, min) + add` only when
the class cap is above zero, no max. MAW needs a `max_mastery` (forbid) and a shift that also applies at cap 0.

### 6.3 Resistances (ST:1349-1383)

The base MMMerge +5 racial rules (`MiscTweaks.lua:673-703`) run first and are wiped by MAW's item stat handler
(IT:2566-2584 sets the result to 0); only these remain:

| Race | Resistance |
|---|---|
| Undead | Mind and Body immune |
| Vampire | Mind immune |
| Elf, Dark Elf | Fire, Air, Water, Earth +25 + level |
| Troll | Water, Earth +25 + level |
| Goblin | Air, Earth +25 + level |
| Dwarf | Mind, Earth +25 + level |
| Dragon | Fire +100 + 2 × level (plus Scales: all six +`[1,1,2,3]% · s · (effLevel + 40)`) |

### 6.4 Special rules

- **Axe dual wield** (S:2642-2724): while a Dwarf or Minotaur is shown on the character/inventory screen, 1H axes
  are re-skinned as one-handed daggers, and for Minotaurs 2H axes too (so a Minotaur can hold a 2H axe in one hand).
  The equip click sets a temporary Dagger skill: Expert (off hand allowed) at Axe ≥ E for 1H axes, or Axe ≥ M for a
  Minotaur's 2H axe, otherwise Novice. With two axes held each 2H axe costs −10 % of axe damage (IT:2856-2873).
  Minotaurs cannot use real daggers (Dagger cap 0).
- **Vampire**: +5 % melee, +2.5 % ranged and spell leech, doubled for the Vampire/Nosferatu classes (IT:3277-3285);
  Preservation kept up between 21:00 and 04:59 or indoors, except map 7d25 (SP:1081-1088, 2957-2967); Mind immune.
- **Troll**: Regeneration +3 and mastery +1; Water/Earth resistance.
- **Dragon**: §5.10.
- **Undead**: Mind/Body immunity; otherwise MMMerge rules. **Zombie**: unchanged MMMerge `ZombiePlayers.lua`.
- **Portraits** (`Character portraits.txt`): 67/68 (Lich Dragon, Dragon Ghost) become race Dragon, 69/70 (Minotaur
  Lich/Zombie) race Minotaur; 76 (Zombie Troll) becomes a Troll Death Knight available at start; new 77 Lich Troll.
- **Starting stats** (`Class Starting Stats.txt`): Dragon Might/Endurance/Accuracy/Speed/Luck 11/30 → 14/50 with +3
  per point; Dark Elf Intellect 11/25 → 14/30 with +2 per point.

---------------------------------------------------------------------------------------------------------------

## 7. Alchemy and potions

Shorthand in this section: `AL` = `Scripts/General/zzAlchemy.lua`, `MP` = `Scripts/Global/zzMAWPotions.lua`,
`SP` = `Scripts/General/zzMaw-Spells.lua`, `IT` = `Scripts/General/zzMaw-Items.lua`,
`ST` = `Scripts/General/zzMaw-Stats.lua`, `SK` = `Scripts/General/zzMAW-Skills.lua`,
`F` = `Scripts/Modules/MawCore/Formulas.lua`, `E` = `Scripts/Modules/MawCore/Estimates.lua`,
`TT` = `Scripts/Modules/MawCore/Tooltip.lua`. The mix matrix,
`POTNOTES.TXT` and `ITEMS.txt` come from `Data/zMaw.T.lod` (MM8 LOD: directory at 0x120, 76-byte entries, each file
has a 0x60 header with the zlib-compressed size at 0x44 and the unpacked size at 0x58). Worked numbers come from a Lua
5.4 port of the formulas: `<scratchpad>/lua_alchemy/potions.lua` (run with `lua potions.lua <difficulty>`), the matrix
from `matrix.py` / `gen_recipes.py` in the same folder.

Data drafts: [data/potion_effects.yml](data/potion_effects.yml) (every potion 221-290 in the proposed schema, plus the
Standard effects OpenYAMM implements today), [data/potion_recipes.yml](data/potion_recipes.yml) (87 recipes, 43
reagents, reagent power and drop rules).

### 7.1 How MAW takes over drinking

MAW replaces the engine's drink path for items 221-299 except 290 (`events.UseMouseItem`, AL:62-264; `t.Allow=false`).
The order inside the handler is the rule set:

1. **Power cap.** `it.Bonus` (the potion power) is clamped to `POTION_POWER_CAP = 500` and written back to the item
   (AL:67-69, AL:298).
2. **Duration** of every timed effect: `6 game hours + max over party members with Alchemy mastery >= GM of
   6 game minutes x skill` (AL:78-85). `skill` is `GetSkill`, which MAW clamps to 2x the Alchemy cap of 60 = 120
   (SK:162-167, SK:203-212) plus the hidden reagent excess (7.2). So: 6 h base, 12 h at GM 60, up to 18 h at 120.
3. **Who acts.** The drinker if its recovery is 0, else the selected member, else the first ready member; with nobody
   ready: "Player must be active to consume the potion" (AL:87-111). A recovering character can therefore be fed a
   potion on another member's turn.
4. **Power requirement** (`potionPowerRequirement`, AL:284-290): 231 Protection 20, 235 Water Breathing 20,
   239 Stone to Flesh 20, 246 Divine Restoration 40, 256 Darkness 50 (dead entry: 256 is not drinkable). Below it:
   "This potion has not enough power", the potion is kept. The item-use potions check their own thresholds (7.4).
5. **Effects** in fixed order: heals (222/223/247/248), Regeneration, Meditation, Magic Protection, condition cure +
   immunity, engine buff timers, potion auras, black-potion ladders, age, Transcendence (AL:117-246).
6. **Consumption** (AL:248-258): potions in `potionUsingCharges` (228-235, 237, 240-242, 245, 247-251, 257, 263;
   AL:283) store uses in `item.Charges`: 0 = fresh, treated as 6; each drink decrements; drinking at 2 removes the
   bottle. A fresh bottle is 5 drinks; the tooltip shows `Charges-1` (TT:116-122). Everything else is consumed.
7. **Combat cost**: only while the enemy detector is red or yellow, the acting member gets `SetRecoveryDelay(60)`
   (AL:260-262). Out of combat drinking is free.

Black potions (252-254, 259, 261, 262) `return` before step 6 when they would not improve anything ("Can't benefit
anymore"), so a useless black potion is not consumed (AL:205-215, AL:236-241).

### 7.2 Reagents, reagent power and drops

Reagent ids, tiers and the base power MAW uses (`reagentList`, AL:587-599): five tiers per colour with base
1/5/10/20/30 (gray: 1/5/10/20/**45**) for the MM8 set 200-219 and the MM7 set 1002-1021; MM6 herbs 1762-1764 are 1.
The LOD `ITEMS.txt` still says 50 / 75 for the top tier; `mawTick_ReagentPower` overwrites the shared
`ItemsTxt[n].Mod1DiceCount` while a reagent is on the mouse and restores it afterwards (AL:601-633).

```
reagentPower = floor(base*(1 + B*0.25/20) + 0.75*B)      (B = reagent item Bonus = item level; base if B = 0)
             + 0.5*s  (Alchemy Master)   or  + s  (Alchemy GM)          s, m of Game.CurrentPlayer
if > 255: power = 255 and the player's Alchemy gets + min(floor((excess)/2), 900) as a hidden bonus (AL:621-628,
          AL:634-637 via skillCapExtra, SK:207-210)
potion power (reagent + bottle, engine) = reagentPower + Alchemy skill (GetSkill)
```

So the effective per-skill-point contribution is 1 (engine) at Novice/Expert, 1.5 at Master, 2 at GM, which is what
the GM description says (AL:707-709). Reagent item level: generated reagents `min(floor(getPartyLevel()/5), 255)`
(AL:641-651); monster drops `round(getPartyLevel()/2)` (AL:683-684). `getPartyLevel()` is the sum of `vars.MMLVL` of
the **other** continents (`zzzMaw_Experience.lua:278-289`), not character level. The tooltip shows
`round(...)` of the first line only, without the Alchemy part (TT:134-139).

Reagent power before Alchemy, by item level B (Lua):

| base | B=0 | B=10 | B=50 | B=100 | B=200 |
|---|---|---|---|---|---|
| 1 | 1 | 8 | 39 | 77 | 153 |
| 5 | 5 | 13 | 45 | 86 | 167 |
| 10 | 10 | 18 | 53 | 97 | 185 |
| 20 | 20 | 30 | 70 | 120 | 220 |
| 30 | 30 | 41 | 86 | 142 | 255 |
| 45 (gray) | 45 | 58 | 110 | 176 | 307 -> 255 |

Monster drops (AL:654-698): chance `(m-2)%` of the best party Alchemy mastery m >= Master (1 % Master, 2 % GM) per
kill, none from reanimated monsters. Tier `round(clamp(baseLevel/20 x (1.75 + rand/2), 1, 5))`, uniform among the 8
reagents of the tier (MM8 and MM7 sets, AL:700-705). If `Bonus + best_s*best_m/2 > 200` the drop becomes a random
potion 221-224 with that sum as power (best skill and best mastery may come from different members). At GM, an
extra 0.2 % roll drops the **Endless Potion** 1069 with `BonusStrength = min(best_s + 10, 100)` (AL:690-697).

### 7.3 Mixing: the 87-recipe matrix

MAW's `POTION.TXT` has 100 result columns (222-290, 806, 1041-1070). Of its 10,000 potion-x-potion cells,
**174 are numeric (87 unordered recipes, all symmetric) and 9,826 are `no`; there is no E1-E4 cell.**
OpenYAMM's current `english/potion.txt` (base MMMerge) has 70 columns with 616 numeric, 2,987 E3, 1,153 E4, 42 E2,
30 E1 and 72 `no` directed cells. The 220 (bottle) row is the column header, and the 221 (catalyst) row holds colour
labels, as in base.

| Tier | Mastery (Potion settings) | Rule | Count |
|---|---|---|---|
| Secondary | Novice | R+B = 226 Hexbane, R+Y = 225 Antidote, B+Y = 227 Lucidity | 3 |
| Tertiary | Expert | base x secondary (9) and secondary x secondary (O+P 237, P+G 238, O+G 239) | 12 |
| White | Master | secondary x tertiary group of three: O x {228-230 / 231-233 / 234-236 / 237-239} = 245 / 243 / 244 / 250; P x ... = 240 / 241 / 242 / 249; G x ... = 247 / 248 / 246 / 251 | 36 |
| Black | Master (262, 263: GM) | base x white group: R x {240-242 / 243-245 / 246-248 / 249-251} = 252 / 257 / 258 / 261; B x ... = 253 / 256 / 260 / 263; Y x ... = 254 / 255 / 259 / 262 | 36 |

The full list with names is in `data/potion_recipes.yml`. The ALT recipe tooltips (`potionRecipeText`, AL:544-583)
match the matrix exactly.

Rules around the matrix:
- **Power of a mix** is the engine's average of the two inputs (MAW does not hook it).
- **Mastery**: required mastery is per result (Potion settings column 3). MAW does not override the engine's check,
  so mixing a result above the mixer's mastery still fails the base way (OpenYAMM:
  `requiredFailureDamageLevel`, `InventoryItemMixingRuntime.cpp:70-85`, an explosion of level = required mastery).
  "No explosions" is true of the matrix, not of under-skilled mixing.
- **Catalyst** (221) mixing is base MMMerge (`MiscTweaks.lua:780-786`, unchanged by MAW): catalyst + catalyst gives
  `max(min(round(max(T + 0.5M, 0.5T + M)), s*m/2), T, M)`; catalyst + potion sets the potion to the catalyst power.
  OpenYAMM implements `max(T, M)` for catalyst + catalyst (`InventoryItemMixingRuntime.cpp:364-381`), a pre-existing
  deviation from base.
- Potion settings flags (`Data/Tables/Potion settings.txt` vs base): 233 and 246-250 and 263 become drinkable;
  236, 238, 243, 244, 255, 256 are usable-on-item; 264-290 neither (removed; names "Potion Deleted in MAW", AL:18-20);
  rows 71-102 route gems and crafting items 1041-1069 through the potion-on-item path (item crafting scope). The
  Notes column of rows 25-31 is shifted against ITEMS.txt names; use ITEMS.txt.

### 7.4 Every potion: exact effect

`P` = potion power after the 500 clamp. "Aura" = the potion acts as a buff-aura caster for the drinker only (7.5).
Timed = rule duration from 7.1.

| Id | Name | Effect (code truth) | Req | Uses | Source |
|---|---|---|---|---|---|
| 221 | Catalyst | drinkable flag, but no branch: drinking wastes it | - | 1 | AL:62-264 |
| 222 | Cure Wounds | HP `round(20 + 0.25 x estHP(P))` | - | 1 | AL:118-120, AL:412-427 |
| 223 | Magic Potion | SP `round(10 + 0.25 x estSP(P))` | - | 1 | AL:121-123 |
| 224 | Energy Potion | cure + timed immunity: Weak, Asleep | - | 1 | AL:346-347 |
| 225 | Antidote | cure + immunity: Disease 1-3, Poison 1-3 | - | 1 | AL:348 |
| 226 | Hexbane | cure + immunity: Curse, Paralysis | - | 1 | AL:349 |
| 227 | Lucidity | cure + immunity: Fear, Insanity | - | 1 | AL:350 |
| 228 | Haste | aura Haste: attack and spell delay / (1 + 0.10 + 0.002s) | - | 5 | AL:332-344, ST:218-224, SK:588-597 |
| 229 | Heroism | aura Heroism: melee damage x (1 + 0.15 + 0.003s) | - | 5 | IT:3325-3345 |
| 230 | Bless | aura Bless: attack `(20 + lvl/4)(1 + 0.02s)`, Accuracy `+min(10 + s/5, 20)%`, hit chance `+0.05 + 0.001s` | - | 5 | IT:2950-2958, IT:3068-3076, F:89-110 |
| 231 | Protection | aura Shield: magic damage x max(1 - 0.15 - 0.003s, 0.7); engine Preservation | 20 | 5 (E) | ST:1072-1082 |
| 232 | Meditation | +`ceil(sqrt(P)/1.5) + 1` Meditation skill levels, per character | - | 5 (E) | AL:138-141, AL:273-281 |
| 233 | Regeneration | Regeneration buff skill `floor(P/2)` GM: HP/s `sqrt(fullHP) x s^1.25 x 0.005` | - | 5 (E) | AL:131-136, F:257-259, SK:1364-1376 |
| 234 | Stone Skin | aura Stone Skin: AC `(20 + lvl/4)(1 + 0.02s)` | - | 5 | IT:3077-3082 |
| 235 | Water Breathing | engine Water Breathing timer | 20 | 5 | AL:311-318 |
| 236 | Harden Item | on item; engine behaviour (MAW override commented out) | - | 1 | MP:93-105 |
| 237 | Magic Protection | party PfM Power `5 + floor(P/10)`, Skill 3 (4 if P >= 50) - but overwritten to Power 4 / Skill 10 every 0.5 s aura pass while the timer runs; PfM also blocks Unconscious | - | 5 (E) | AL:145-153, SP:2985-2990, SP:676-685 |
| 238 | Enchant Item | on an unenchanted base item: 10 % skill enchant 17-24 else 1-16 (EquipStat 10) / 1-10; strength `min(P,500)/5 x slotMult` (ceil); skill enchants `max(sqrt(x), ceil(x/10))`; seeded per item type | none in code | 1 | MP:54-92 |
| 239 | Stone to Flesh | cure + immunity: Stoned | 20 | 1 | AL:351 |
| 240 | Power Boost | sets only the timers of engine TempMight, TempAccuracy; **Power never set** | - | 5 | AL:165-176, AL:318-319 |
| 241 | Wisdom Boost | same, TempIntellect, TempPersonality | - | 5 | AL:320 |
| 242 | Resilience Boost | same, TempEndurance, TempSpeed, TempLuck | - | 5 | AL:321 |
| 243 | Lesser Element | weapon (skill < 7, Bonus2 = 0): Bonus2 `rand(1..4)x3+2` = of Frost / Lightning / Flame / Venom | 40 | 1 | MP:28-40 |
| 244 | Swiftness | weapon: Bonus2 59 (Swift) | 40 | 1 | MP:41-53 |
| 245 | Champion's | auras Haste + Heroism + Bless | - | 5 (E) | AL:332-344 |
| 246 | Divine Restoration | cure + immunity: the 13 conditions of 224-227, 239 plus Unconscious | 40 | 1 | AL:352 |
| 247 | Divine Cure | HP `round(50 + 0.35 x estHP(P))` | - | 5 | AL:124-126 |
| 248 | Divine Magic | SP `round(50 + 0.35 x estSP(P))` | - | 5 | AL:127-129 |
| 249 | Elemental Resistance | auras 3/14/25/36: Fire/Air/Water/Earth res `(10 + lvl/4)(1 + 0.02s)`, Int/Speed/Luck/End `+min(10 + s/5, 20)%` | - | 5 | IT:3043-3066 |
| 250 | Self Resistance | auras 58/69: Mind/Body res, Personality/Might % | - | 5 | IT:3043-3066 |
| 251 | Paladin's | auras Shield + Stone Skin; Preservation | - | 5 (E) | AL:332-344 |
| 252 | Pure Power | permanent Might, Accuracy `floor(P/50) x 20`, best step only | - | 1 | AL:188-216, IT:2577-2579 |
| 253 | Pure Wisdom | permanent Intellect, Personality, same ladder | - | 1 | AL:306 |
| 254 | Pure Resilience | permanent Endurance, Speed, Luck, same ladder | - | 1 | AL:307 |
| 255 | Greater Element | weapon: Bonus2 `rand(1..4)x3+3` = of Ice / Thunderbolts / Infernos / Acid | 55 | 1 | MP:15-27 |
| 256 | Darkness | weapon: Bonus2 41 (of Darkness) | 100 | 1 | MP:1-14 |
| 257 | Divine Blessing | aura Day of the Gods: all 7 stats `+min(10 + s/7, 20)%` (wide span) | - | 5 (E) | IT:3039-3066 |
| 258 | Twilight | BirthYear set so current age = 60, AgeBonus = 0; ageing continues | none in code | 1 | AL:219-222 |
| 259 | Transcendence | skill points `5k^2 + 15k`, k = floor(P/50); only the gain over the best k drunk | - | 1 | AL:225-245 |
| 260 | Dawn | current age = 20 | none in code | 1 | AL:223-226 |
| 261 | Pure Elemental Res. | permanent Fire/Air/Water/Earth res `floor(P/50) x 30` | - | 1 | AL:201-204 |
| 262 | Pure Self Res. | permanent Mind/Body res `floor(P/50) x 30` (GM to brew) | - | 1 | AL:201-204 |
| 263 | Divine Resistance | aura Day of Protection: every res `(10 + lvl/4)(1 + 0.02s/1.4)` | - | 5 (E) | AL:520-528, IT:3035-3062 |

"5 (E)" = five uses and the Endless Potion can add more (7.6). Immunities are stored per character in
`vars.PlayerAlchemyBuffs[index][cond]` and enforced in `DoBadThingToPlayer` (AL:356-406; poison and disease use one
key each). Stat ladders are added in `CalcStatBonusByItems` from `vars.BlackPotions` (IT:2577-2579).

**The HP/SP pool estimate** used by 222/223/247/248 is MAW's balance model of an average character of level `P`
(`getPlayerEstimatedHealth`, E:253-300 and `getPlayerEstimatedMana`, E:302-345): base 25 HP (15 SP), 3..9 per level
growing to the cap by level 210 (330 madness), stats from `estimateStat` (17 + 0.2/level + enchant power x geared
fraction x Day-of-the-Gods share), Bodybuilding / Meditation / Enlightenment at the expected skill
(`estimateSkill = skillLevelFromPoints(skillPointsAtLevel(lvl)/5)`), x `(1 + stat/1000)`. It depends on the
difficulty (`GetDifficulty`: loot density and rarity tables, insanity/madness mastery thresholds). Ported in
`potions.lua`.

**Worked examples** (Lua, difficulty 3 = bolster 100; Doom and Beyond Madness after the slash):

| Power | Cure Wounds HP | Magic Potion SP | Divine Cure HP | Divine Magic SP | est. HP / SP of a level-P character |
|---|---|---|---|---|---|
| 10 | 46 / 48 / 48 | 34 / 36 / 35 | 87 | 84 | 106 / 96 |
| 50 | 185 / 201 / 140 | 181 / 194 / 123 | 282 | 290 | 662 / 685 |
| 100 | 494 / 556 / 380 | 553 / 597 / 323 | 714 | 810 | 1896 / 2170 |
| 200 | 1919 / 2265 / 1646 | 1928 / 2103 / 1180 | 2709 | 2736 | 7598 / 7673 |
| 500 | 11114 | 7497 | 15582 | 10532 | 44376 / 29949 |

| Power | f | skill s | caster lvl | Haste | Heroism, Shield | Stone Skin AC, Bless attack | Bless hit | stat % | element res (249/250) | DoG % (257) | DoP res (263) | 233 HP/s at 1000 HP | 232 Meditation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 0.79 | -10.6 | 3.9 | 7.9 % | 11.8 % | 16.5 | 3.9 % | 7.9 % | 8.7 | 7.9 % | 8.7 | 1.2 | +4 |
| 50 | 0.94 | -3.1 | 23.4 | 9.4 % | 14.1 % | 24.2 | 4.7 % | 9.4 % | 14.9 | 9.4 % | 14.9 | 8.8 | +6 |
| 100 | 1.13 | 6.3 | 56.3 | 11.2 % | 16.9 % | 38.3 | 5.6 % | 11.2 % | 27.1 | 11.2 % | 27.1 | 21.0 | +8 |
| 200 | 1.50 | 25.0 | 150 | 15.0 % | 22.5 % | 86.2 | 7.5 % | 15.0 % | 71.2 | 15.0 % | 71.2 | 50.0 | +11 |
| 500 | 1.50 | 25.0 | 375 | 15.0 % | 22.5 % | 170.6 | 7.5 % | 15.0 % | 155.6 | 15.0 % | 155.6 | 157.2 | +16 |

(The regeneration column is before the x2 unhurt / x4 no-enemies multipliers, SK:1395-1407.)

Correction (2026-10-23): the resistance columns (249/250, 263) use the buffPower base of 10 from `zzMaw-Spells.lua`.
`zzMaw_Mapping.lua` replaces that table with base 20 on every map load (`AfterLoadMap`), so in play a resistance aura
or potion gives the Stone Skin numbers: 38.3 at power 100, 86.2 at 200. The implementation follows the live table.

| Power | black step | 252-254 per stat | 261/262 per res | 259 total skill points |
|---|---|---|---|---|
| 10 | 0 (refused, kept) | 0 | 0 | 0 |
| 50 | 1 | +20 | +30 | 20 |
| 100 | 2 | +40 | +60 | 50 |
| 200 | 4 | +80 | +120 | 140 |
| 500 (cap) | 10 | +200 | +300 | 650 |

### 7.5 Potion buffs and auras compete; they never add

`setPotionBuff` stores, per character index, the expiry and power of each aura spell the potion copies
(SP:3138-3147; `potionBuffSpells`, AL:332-344). Every reader of a buff calls `getBuffSkill(spell, pl)`
(SP:3204-3215): it computes the party caster's `(s, m, level)` and the potion's `(s_p, Master, level_p)`, and keeps
the stronger by `buffStrength = Base + Scaling x s/10 (+ level/4 for flat buffs)` (SP:3192-3202). Haste, Shield and
Stone Skin also consider Hour of Power at `s/1.5` (`bestBuffSource`, SP:3170-3180). So a potion only matters when it
beats the party's aura, and is per drinker, while auras cover the party.

Potion strength (SP:3111-3135): `f = 0.75 + 0.75 x min(P, 200)/200`, `s_p = 50(f - 1)` (70 for Day of the Gods and Day
of Protection), `level_p = 0.5 x P x f` (P up to 500, so flat buffs keep growing past 200 while multiplier buffs stop).
At low power the skill is **negative** (-12.5 at P = 0), which the code relies on (IT:3051-3053). Engine buff
timers are kept alive across the 0.5 s aura reset through `vars.buffToIgnore[slot][buff]` (AL:165-176,
SP:2878-2885), keyed by **party slot**, while the potion powers are keyed by character index.

### 7.6 Charges and the Endless Potion

`potionUsingCharges` (AL:283): 228, 229, 230, 231, 232, 233, 234, 235, 237, 240, 241, 242, 245, 247, 248, 249, 250,
251, 257, 263. The Endless Potion (1069) used on a potion adds charges only to `chargePotions` = 231, 232, 233, 237,
245, 251, 257, 263 (AL:1011): `Charges = (Charges == 0 ? 6 : Charges) + BonusStrength` (AL:1083-1088), i.e.
`BonusStrength` (= best Alchemy + 10, max 100 at drop time) extra drinks.

### 7.7 Solo hotkeys G / V (SK:1039-1122)

Solo only, not on screen 21, 15-tick cooldown on a `const.Minute/2` timer. G drinks the strongest 222 in Party[0]'s
items and heals `round(P^1.4) + 10` (10: 35, 50: 249, 100: 641, 200: 1675). V drinks the strongest 223, **shows**
`round(P^1.4 x 2/3) + 10` and **adds** `20 + 2P` (10: 27 shown / 40 added; 200: 1120 / 420). Neither checks charges,
power requirements or recovery, and neither uses the drink formula of 7.4. Do not port as is.

### 7.8 OpenYAMM today, and a schema for both rulesets

What OpenYAMM does now (base MMMerge rules):

- Mixing: `InventoryItemMixingRuntime::mixItems` (`InventoryItemMixingRuntime.cpp:272-430`): reagent + bottle
  `power = alchemyLevel + reagentPower(definition.mod1)` (line 331), potion + potion via `PotionMixingTable`
  (`game/tables/PotionMixingTable.cpp:85-178`, reads the 220 header row and `no` / `E<n>` / id cells), average power,
  mastery failure, autonote unlock. The mixer is the party's best Alchemy member (lines 453-468); MMMerge uses the
  current player. Hard-coded item ids: 233 recharge, 236 harden, 246-250 and 263 weapon enchants (lines 19-26).
- Bench and planner: `AlchemyBenchRuntime.cpp` (`buildBook` 366, `isPotionRecipeKnown` 122, preview outcomes 562-569,
  `AlchemyChainPlanner::tryRecipe` 871 assumes `alchemistLevel + reagentPower` and the average).
- Effects: `InventoryItemUseRuntime.cpp` `ConsumePotion` (lines 1099-1275) and helpers (139-417). 222/223 heal
  `10 + P`; 224-227, 237-239, 251, 262 cure; 228-230, 234, 235 fixed strength 5 for `30 min x P`; 231 Preservation,
  232 Shield `3P`; 240-245, 255-261 `+3P` temporary stats/resistances; 252 cures all, 253/254 `5P` HP/SP; 264-270
  `+50` permanent (no once-per-character gate, unlike the engine's `UsedBlackPotions`); 271-290 MMMerge
  ExtraPotions (essences +15/-5 once, Doom, Divine Boost/Protection `3P`, +20 level, Gods, +40 resistances once,
  PfM). Item fields: `InventoryItem.standardEnchantPower` holds the power; `currentCharges` / `maxCharges` already
  exist (`game/party/Party.h:45-66`).
- Data: `potion_settings.txt`, `english/potion.txt`, `english/potnotes.txt`, `reagent_settings.txt`.

What a MAW ruleset needs from code (beyond swapping those four tables): the reagent-power formula with item level and
mastery bonus (and its 255 cap), per-potion charges, a power-requirement gate, fixed 6 h durations with the GM
extension, per-character timed immunities, potion-as-aura buffs resolved against the party's auras, best-step
permanent ladders, set-age, item-use enchant potions keyed by data instead of item ids, and "drink in combat costs 60
for whoever is ready".

**Recommended schema** (`potion_effects.yml`, one per ruleset, drafted for MAW in `data/potion_effects.yml` with a
`standard_reference` block showing that every current OpenYAMM effect fits):

```yaml
rules:
  power_cap: 500                         # 0 = none
  duration: {hours: 6, gm_alchemy_minutes_per_skill: 6}    # Standard: {per_power_minutes: 30}
  combat_recovery: {value: 60, only_when_enemies_near: true}
  recovery_payer: any_ready_member       # Standard: drinker
  aura_potion: {mastery: 3, fraction: {min: 0.75, max: 1.5, full_power: 200},
                skill: {span: 50, span_day_buffs: 70}, caster_level_per_power: 0.5}
potions:
  228:
    use: drink                           # drink | item | none (replaces Potion settings Drinkable/Usable)
    min_power: 0
    charges: 5
    rechargeable: true
    effects:
      - aura_buff: {spell: 5}            # MAW
      # Standard: - buff: {id: Haste, strength: 5, unless: Weak}
```

Effect kinds: `restore {pool, amount}`, `cure [..]`, `immunity [..]`, `buff {id, strength}`, `aura_buff {spell}`,
`skill_bonus {skill, amount}`, `party_buff {id, power, mastery}`, `permanent_stat` / `permanent_resistance
{.., amount, limit: once_per_character | best_step | none}`, `skill_points {amount, limit}`, `age {set_years |
modifier | clear_magic_age}`, `level_modifier`, `item_effect {action: harden | random_standard_enchant |
special_enchant | temporary_special_enchant | recharge_wand, ..}`. Amount expressions: a number, `linear [a, b]`
(a + bP), `pool_share {pool, flat, share}` (MAW estimate), `step {per, value}`, `step_quadratic {per, a, b}`,
`sqrt_ceil {div, add}`, `half_floor`. Reagents go in the recipe file: `power_formula` (Standard: `mod1 + skill`;
MAW: the item-level curve), drop rules and the recipe list, so the bench's recipe book and chain planner read one
source. MAW shows every recipe (ALT tooltip), so the ruleset should also mark all recipes as known.

Cheap wins: show charges, the required power and the computed effect at the potion's power in the tooltip (the
numbers in 7.4); show "overridden by aura of X" when `getBuffSkill` would pick the aura; replace G/V with the
quick-slot design in SKILLS_SPELLS_ALCHEMY.md §7.4 using the normal drink formula.

---------------------------------------------------------------------------------------------------------------

## 8. Corrections to existing docs

Nothing in the other documents was edited. `SSA` = [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md),
`README` = [README.md](README.md).

### 8.1 Spells, Ascension, auras, crowd control

| Doc claim | Code |
|---|---|
| SSA §2.4 sample table, column "mana (N)" ×1.98/3.33/7.67/15.41/51.52 | those are mastery **0**; Novice (m = 1) is ×1.73/2.91/6.71/13.48/45.08 (`(1 − 0.125m)`, SP:2268) |
| SSA §2.4 "Shaman Σ(12..18)/7 at GM" | Σ/7 with mastery forced to GM, for cost and healing only; damage, cast time and CC duration read Learning, which Shamans cannot learn (§2.1) |
| SSA §2.4 "Damage: dice max × …, flat add × …" | true, except fixed-per-point spells (Meteor Shower, Starburst, Armageddon) roll the unscaled per-point value (SP:1984) |
| SSA §2.2 "×(1 + Int/Per bonus)" | `1 + max(Int, Pers)/1000`; Death Knights and Dragons skip the stat, crit and enchant steps (SP:2005-2020) |
| SSA §2.2 Lightning "hits 1/2/3/4 targets" | each bounce goes to the closest living monster within 768, hostile or not, and may return to a previous target (DM:399-428) |
| SSA §2.2 Mass Distortion "15 % + 0.5 %/pt" | then ÷ `sqrt(bolster multiplier)` and × `max(1, (level/250)²)` (DM:363-396) |
| SSA §2.2 Invisibility "15+1.5 min/pt (M) / 30+3 (G)" | that is the tooltip; code `(15 + s)·1.5` and `(30 + 2s)·1.5` game minutes (SP:711-716) |
| SSA §2.2 "solo: Town Portal/Lloyd/Fly/Water Walk/Feather scrolls are not consumed" | spell 16 is **Jump**, not Feather Fall (SP:1107) |
| SSA §2.2 "Summon Wisp keeps 2m−3 wisps" | MAW only adds a wisp when the engine refused to summon, up to `2m − 3` alive (SP:3435-3455) |
| SSA §2.1 "Shared Life 25 → 12" | the 12 is never used: Shared Life is M/G only and the healing table sets 25/40 (SP:2397-2399) |
| SSA §2.3 "quick-casting 68, 74, 49 or 55 heals the lowest-HP% member" | 55 is broken (undefined `idx`, Greater Heal numbers, dead members excluded) (SP:1287-1294) |
| SSA §2.3 "Shaman: all heals × (1 + Σschools/400)" | five of six: Power Cure excluded (loop `i=1,5`, SP:2378) |
| SSA §2.3 heal formula | heals cannot crit (SP:88-89); map affix 31 cuts healing |
| SSA §2.5 table "Stun 2 min" and "Always lands … unless blocked by DR" | Stun's CCMAP duration is unused; Stun is the only CC with a roll `30/(30 + L/4)` and its duration is MMMerge's (DM:334-357, TW:50-58) |
| SSA §2.5 "÷2 on bosses" | only groups 2 and 3; Slow, Dark Grasp and Shrinking Ray are not halved (SP:1826-1841) |
| SSA §2.5 duration formula | Dragon Fear (122) skips Ascension and resistance (SP:1409-1412) |
| SSA §2.5 "Charm (Mind, 60) / Dark Elf Charm" | `const.Spells.Charm` in MM8 is 113, the **Vampire** Charm, but its CCMAP school is DarkElfAbility; Dragon Fear's is Mind (SP:1341, 1344) |
| SSA §2.5 "Shrinking Ray … one extra target per mastery" | `m` targets in total (`m − 1` extra) (SP:1717-1719) |
| SSA §2.5 "Dark Grasp … DamageHalved" | DamageHalved is ×0.7 monster damage, not ½, and does not stack with Shrinking Ray (DM:1575-1578, 1753-1760) |
| SSA §2.5 "Others patch resistance/level for one tick so the engine applies" | correct; add that they always land (the hit roll is unused, SP:1607-1619) |
| SSA §2.6 Empower Magic "+15 % +0.3 %/pt spell damage" | the code reads **Haste's** row: +10 % +0.2 %/pt (SP:2048) |
| SSA §2.6 Stone Skin "+20 AC (+level/2)" | `level/4` (IT:3079-3080); the tooltip says /2 (SP:3293) |
| SSA §2.6 "Preservation, Pain Reflection, PfM, Fire Aura, Vampiric Aura, Immolation: as vanilla, permanent" | Fire Aura is weapon item-level damage × 10-25 % (IT:4280-4300); Vampiric Aura is fixed party leech (IT:3272-3276); PfM never loses charges and blocks Unconscious; Immolation is MAW damage 10 + 1-30/pt; costs 90/150/180/40/120/10 |
| SSA §2.6 "until toggled off or the caster falls unconscious" | an unconscious holder's aura is suspended, the reservation stays, and it resumes on recovery (SP:2902-2903) |
| SSA §2.6 "Caster skill counted for buffs is capped at 50 (day buffs 75)" | and it is the **base** school skill, item bonuses ignored (SP:3098-3099) |
| SSA §2.6 "Utility spells reserve flat mana" | reduced by `(1 − EnlightenmentMastery/10)` (SP:3048-3049) |
| SSA §2.6 "temple/scroll/pedestal buffs … dropped when leaving the map" | scroll/pedestal auras survive dungeons and drop on entering a different outdoor map; temple auras drop on the next map load (SP:2694-2734) |
| SSA §2.6 Meditation / Regeneration "party SP/HP regen" | formulas in §3.3-3.4; Regeneration uses the `Base` value where `Scaling` was meant (S:1370-1371) |
| SSA §2.7 cast speed | Ascension applies only to damage, healing and CC spells; CC delay has no Speed/Haste/armour term and uses `1.015^(asc − school)` (ST:211-217) |
| SSA §2.4 "skill tooltip prints the current multipliers" | the healing and mana lines of that tooltip use different formulas from the code (§2.5) |
| README §2.6 "Crowd control always lands" | except Stun (§4.4) |
| README §6 "Monster Dispel … only looks reduced because auras are re-applied every 0.5 s" | the re-apply restores every aura within 0.5 s, so Dispel has no lasting effect at all (TI:95) |

### 8.2 Classes and races

| Doc claim | Code |
|---|---|
| SKILLS_SPELLS_ALCHEMY.md §3.1 Seraphim Body heal "`s^1.3·m·speed·(1+Pers/1000)·2`" | the factor is the melee damage multiplier, not speed (DM:119) |
| §3.1 DK "Frost and Unholy add 0.5/0.75/1/1 damage per point" | ramps gradually between mastery thresholds (`GetGradualMasteryValue`, ST:1480-1505) |
| §3.1 DK spells list | complete, but misses: SP gained per melee hit 10/15/20 (×1.5 on kill), Icy Touch slow, Death Coil heal 20 % (30 % only at Master), spell delay = attack delay, fixed costs, quick-cast toggle bug |
| §3.1 Shaman "Fire `s/10` % of target HP" | of the target's **current** HP, at least `s`, then ÷ fire resistance (DM:1047-1054) |
| §3.1 Shaman "Spirit +s % melee damage and healing" | melee damage only; healing scales with `Σ7 schools/400`, spell damage with `Σ/200` (DM:1118-1128) |
| §3.1 Shaman "Every 7 skill levels adds 1 Ascension"; §2.4 "Shaman Σ(12..18)/7 at GM" | Σ/7 with mastery **forced** to GM, for cost and healing only; damage and cast time read Learning, which Shamans cannot learn |
| §2.4 "Elementalist uses Σ(Fire..Earth)/4 at GM" | mastery is forced to GM (not "if GM"); cast time floors the value |
| §3.1 Elementalist "halved after ~1 s of no casting" | after `max(4·delay, 128)` ticks, then halved every 0.5 game minute; no stacks when the rotation is off or never bound |
| §3.1 Elementalist progress `tier^1.5·monsterLevel^0.5` | also × √(party size) outside Insanity, ÷3 for AoE except Sparks/Poison Spray; tier mastery gates N×4, E×3, M×3, G |
| §3.1 Assassin "Melee costs 50−5m energy" | m = Combat (Fire) mastery; Assassination also adds +10 max energy per mastery; arrows cost half and give 0.5 combo |
| §3.1 Assassin spell list | Poison Spray (3 combo) missing; Lightning Bolt is the 5-point one |
| §3.1 Assassin "Assassination adds `s·(1+m)` damage reduced 20 % per nearby monster" | cut capped at 80 %, counts the target; with too little energy the whole bonus is lost |
| §3.2 Promotions | missing: step 0 can jump to step 2; promotions are party-wide qbit checks; `promotionCount` reuse bug |
| §3.3 "Dragon HP 10→5/level, SP from 0" | Dragon HPFactor 10→5 only; Great Wyrm keeps 10; SPFactor 5/10 → 0 |
| §3.3 "Thief line: HP 35→25" | HP per level also 4/6/8/8 → 3/4/5/5 |
| §3.3 "+1 HP/level" list | High Priest also gets +1 HP and +1 SP per level |
| §3.3 "Assassin/Spy reach M in elements and G Dodging/Armsmaster" | `Class Skillz.txt`: G in all four elements, Dodging E/M/G/G, **no** Armsmaster or Learning for the whole Thief line |
| §3.3 "Dragons lose Meditation (refunded)" | also lose Learning; Troll and War Troll lose Learning too |
| Appendix "`Class Skillz.txt` rows 0-38 identical to MAW `Class Skills.txt`" | about 90 cells differ; `Class Skillz.txt` wins (SK:350-362, 874-876) |
| §4 / Appendix `Race Skills.txt` changes (Troll Regeneration →M, abilities E→M ...) | `Race Skills.txt` is not read at all (empty `Structs/RacialSkills.lua`); only `Race Skillz.txt` applies |
| §4 "Troll: Regeneration min Master and `+`" | `+` only (one step) |
| §4 Dark Elf / Elf "Other" empty | +25 + level to Fire, Air, Water, Earth (ST:1367-1368) |
| §4 Dragon "+100 fire res" | +100 + 2 × level; Dragon "triple jewellery values" is all item-derived stats, HP, SP, AC and resistances ×3 (IT:3002-3015) |
| §4 Vampire | also Mind immunity (ST:1363-1365); preservation window is 21:00-04:59 (MAW's hour is fractional, audit CLS-6) |
| README §2.7 "random final class is picked when there are several" | correct; add that the Elder/Ultimate multiplier changes the class for every character of it |
| README §2.7 Dragons "lose HP per level" | Dragon only (5 instead of 10); Great Wyrm unchanged at 10 |

### 8.3 Alchemy and potions

Against `SKILLS_SPELLS_ALCHEMY.md` §5 and `README.md` §2.8:

1. §5.4 / README 2.8 "Power Boost / Wisdom Boost / Resilience Boost: Might + Accuracy (temp)" and the tooltip
   "10 + (1 x Power)": the code only sets the timers of engine TempMight etc. with `Skill = 0` and never sets their
   Power (AL:165-176); there is no aura row for them. In practice they give nothing on a fresh character.
2. §5.4 "237 Magic Protection: PfM with 5 + power/10 charges; >= 50 power also blocks death/eradication": the 0.5 s
   aura pass rewrites the buff to Power 4, Skill 10 while the potion timer runs (SP:2985-2990), so the power has no
   effect; any PfM also blocks Unconscious (SP:676-685).
3. §5.4 "258 Twilight / 260 Dawn: fixes age at 60 / 20, power req 50": no power requirement in code
   (`potionPowerRequirement`, AL:284-290); they set the current age once (BirthYear, AgeBonus 0) and ageing continues.
4. §5.4 "238 Enchant Item ... text says 20": confirmed no check; also requires no Bonus, Bonus2 or second enchant;
   jewellery (EquipStat 10) rolls 1-16.
5. §5.5 "GM: 0.2 % Endless Potion (1069, power = skill+10)": `BonusStrength = min(s + 10, 100)` is the number of
   **charges** it adds, and only to 231, 232, 233, 237, 245, 251, 257, 263 (AL:1011, AL:1083-1088).
6. §5.5 "reagents whose power would exceed 200 drop as a ready potion": the test is item level + `s x m / 2` > 200
   (not reagent power); the potion is a random 221-224 with that sum as power (AL:683-689).
7. §5.5 `partyLevel/5`, `partyLevel/2`: `getPartyLevel()` is the summed level of the other continents
   (`zzzMaw_Experience.lua:278-289`), not character level.
8. README 2.8 / §5.2 "no explosions": true of the matrix (zero E cells), but the engine's mastery check still fails
   under-skilled mixes. The matrix has 87 recipes over 100 columns, not "every other cell no" over the base 70.
9. §5.2 "264-289 neither = removed": 264-**290** (290 PfM too). Gem rows are 71-**102** (1069 appears twice).
10. §5.4 "Drinking in combat costs 60 recovery": only with enemies detected, charged to whichever member acts (7.1).
11. §5.4 "228 Haste: attack speed %": it divides spell recovery too (ST:218-224).
12. §5.4 potion-strength table lists a Fate column: no potion grants Fate. Flat buffs (Stone Skin, Bless attack,
    resistances) use `level_p = 0.5 x P x f` with P up to 500, so they keep growing past 200 (7.4 table).
13. §5.4 "getBuffSkill returns the stronger ... potions and spells never add up": correct, but the comparison is on
    `buffStrength` (SP:3192-3202), not on the applied value, and Hour of Power is included for Haste/Shield/Stone Skin.
14. §5.1 "effects hard-coded in InventoryItemUseRuntime.cpp:168-411": the dispatch is `ConsumePotion` at 1099-1275;
    168-417 are helpers (permanent +50, buff helper, ExtraPotions 271-290).
15. §5.7 item 5 "needs a field": `InventoryItem` already has `currentCharges` / `maxCharges` (`Party.h:62-63`);
    only semantics and tooltip are missing.
16. README 2.8 "most have 5 charges": 20 of the 43 MAW potions; none of the cures, heals 222/223 or black potions.

---------------------------------------------------------------------------------------------------------------

## 9. Not covered

### 9.1 Spells, Ascension, auras, crowd control

- Monster spellcasting and MAW's monster spell damage multipliers (`zzMaw-Monsters.lua:1939-1961`), spell
  resistance, damage randomisation, difficulty scaling and the crit formulas: [COMBAT.md](COMBAT.md).
- `getCCDiffMult` (SP:1352-1364) is computed in the engine-path tick (SP:1635-1638) but never used; not specified.
- Engine patches whose purpose is not stated: `mem.nop(0x426CD3, 6)` next to the Shared Life hook (SP:1006).
- Legendary item effects that touch spells (19, 26, 32, 34, 35) and map affixes 13, 27, 31 are only named; see
  [ITEMS.md](ITEMS.md) and [COMBAT.md](COMBAT.md).
- Homing projectiles and the M&M6 projectile restoration settings, extended skills Cover, Mana Shield and
  Retaliation, and the spellbook seal UI: [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) §1.4, §2.8.
- The engine's own Stun knock-back and duration, the Immolation tick rate and `GetWeaponLevelDamage` (Fire Aura)
  were not re-derived.
- Multiplayer branches of every spell (RemoteData, MultiplayerData) were ignored.

### 9.2 Classes and races

- `getMonsterDamage`, `estimateSkill`, `getPlayerEstimatedVitality` and `mightLevelSwap`, used by the flat
  reductions and dragon damage, are documented in COMBAT.md; no numbers are given here for the flat reductions.
- Exact MM8 engine meaning of `SPStats` value 3 set for dragons (CL:322, 325) was not checked.
- Class descriptions and creation-screen text (CL:164, 492, 522, 605) and `MenuChooseCharacter.lua` were not
  re-audited beyond what SKILLS_SPELLS_ALCHEMY.md §0 says.
- Multiplayer variants (`SendHeal`, online lowest-HP target, remote cast skipping) were ignored.
- Dragon Flight and Wing Buffet (124/125) keep vanilla behaviour; not re-checked.
- The Respec interaction with class-specific skills is covered only by SKILLS_SPELLS_ALCHEMY.md §1.9.

### 9.3 Alchemy and potions

- Gem, cube, eye, hourglass, mirror, pearl, orb and Crafting Cube use through the potion path (AL:712-1101,
  Potion settings rows 71-102) and crafting drop rates (AL:1092-1230): item crafting scope (ITEMS.md).
- Black-potion quest turn-ins (Thistle 181, Rihansi 203, Talion 212, Kelvin 234, Galvinus 246) live in MAW's
  `GLOBAL.lua`; `zzMAW_PotionQuests.lua` only removes MMMerge's duplicate handlers. Their rewards were not traced.
- `POTNOTES.TXT` (autonote text per recipe) was extracted but not diffed against base.
- Austerity mode renames 232-237, 252-256, 261-263 to "Potion Deleted in Austerity" (AL:22-37) but does not block
  their effects or recipes; not traced further.
- Whether the engine fires `UseMouseItem` for the usable-only potions dropped on a portrait (MAW's handler would then
  consume them with no effect) was not verified in game.
- The `const.Minute/2` timer to real seconds for the G/V cooldown, and game-hour to real-time conversion of the 6 h
  duration, were not measured.
- Multiplayer sync of potion state (`MawCore/Sync.lua:65-66`).
