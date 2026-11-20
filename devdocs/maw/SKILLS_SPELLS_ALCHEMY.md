# MAW mod: skills, spells, classes, races, alchemy, respec

First-pass overview. Corrected on 2026-10-22 against the verified specs listed in [README.md](README.md); where they
differ, the spec documents win.

Analysis of `/home/pjasicek/github/Maw-Mod-MMMerge` (HEAD `ef23ee17`, 2026-10-22) against base MMMerge
(`reference/mmmerge`, `reference/mmerge_data_forus`). Paths below are relative to the MAW repo unless prefixed
with `OpenYAMM/`. Read-only analysis; table diffs were made with throwaway LOD and TXT diff scripts (not kept).

Note: `OpenYAMM/reference/Maw-Mod-MMMerge/` is an **older snapshot** (87 script files differ from the latest
repo). Use the standalone repo as the source of truth.

Shorthand: `S` = `Scripts/General/zzMAW-Skills.lua`, `SP` = `Scripts/General/zzMaw-Spells.lua`,
`AL` = `Scripts/General/zzAlchemy.lua`, `CL` = `Scripts/General/zzClasses.lua`,
`MC/x` = `Scripts/Modules/MawCore/x.lua`. Mastery index 1..4 = Novice/Expert/Master/Grandmaster (5 = Supreme).

---------------------------------------------------------------------------------------------------------------

## 0. The README is partly stale — trust the code

| README claim | Code reality |
|---|---|
| Ascension reduces mana cost 10/20/30/40 % | `(1 - 0.125*m)` → **12.5/25/37.5/50 %** (SP:2268, tooltip S:1565-1568) |
| Ascension "ascends spells of the current tier (tier 1 = cost-1 spells … tier 11 = cost-30)" | **No tiers in code.** One continuous Ascension skill level `s` scales every damage/heal spell's cost, damage and cast time (SP:2043-2074, 2264-2279) |
| "Press the icon top right on party creation to enable MAW classes" | That icon was MMMerge's *free class/portrait* toggle (base `MenuChooseCharacter.lua`, button at 588,54). MAW **deleted the button and forces free selection always on**; only "must be an unpromoted base class" remains (`Scripts/General/MenuChooseCharacter.lua` diff) |
| Speed: every 10 points = +1 % cast speed | `getSpellDelay` uses `floor(speed/SPELL_HASTE_DIVISOR)` with divisor **20** (S:408, `zzMaw-Stats.lua:171`); the Speed stat tooltip still prints `/10` (`zzMaw-Stats.lua:350`) |
| Dwarf: +3 Axe and Bodybuilding | Code: Dwarf +3 **Shield** and Bodybuilding (S:2385-2388). The Race PDF says Axe, Shield, BB. Axe missing in code |
| Troll: +2 mastery Regeneration | `Race Skillz.txt` gives `+` (one step); `Race Skills.txt` (min Master) is never read, so only the `+` applies |
| Click a misc skill to share it with the party | Click-share code is commented out (S:366-399). Sharing is now **automatic**: every party check takes the best member (S:2019-2124) |
| Alchemy GM makes black potions | `Potion settings.txt` requires mastery 3 (Master) for 252-261; only 262/263 need GM |

Also a real bug pattern: `if not vars.MAWSETTINGS.buffRework=="ON"` parses as `(not x)=="ON"` → **always false**.
Every "buff rework OFF" branch guarded that way is dead code: Heroism (SP:225), Regeneration spell (SP:377),
Protection from Magic cap (SP:452), the GM-school passive party buffs `elementalBuffs()` (SP:1047), the +20 % Haste
recovery in `GetAttackDelay` (S:557), meditation SP regen condition (S:1436). In practice MAW only works with the
buff rework ON (the default, `zz_Maw-initialize.lua:537`). An OpenYAMM port should implement **only** the
rework behaviour.

---------------------------------------------------------------------------------------------------------------

## 1. Skills

### 1.1 Engine-level changes

- **Skill value limits** (`Scripts/Structs/After/RemoveSkillValueLimits.lua:24-30`, diff vs mmmerge):
  `MaxSkillVal` 0xFF → **0x3FF (1023)** (base+bonus), `MaxSkillBase` 0x50 (80) → **0x1F4 (500)**. Expert bit stays
  at 10 (0x400/0x800/0x1000). The engine's own mace/staff stun/paralyze rolls are disabled (`and ebx, 0`, ~line 496-510)
  so MAW's scripted stun applies. One-time save migration re-encodes old mastery bits (S:1-22).
- **Skillz.dll port** (`MC/Skills.lua`, `MC/SkillsUI.lua`): extended skill ids 39..127 with storage in `vars`,
  mastery letters `B/N E M G S U A D` (Supreme/Ultimate/Ascended/Deity beyond GM, Skills.lua:191), class caps from
  `Class Skillz.txt` (128 rows), race modifiers from `Race Skillz.txt` (`E`, `M`, `+`, `0`, `g+` tokens = min/max/shift),
  race×class overrides from `Extra Skillz.txt` (**empty in MAW**, header only). The clamp on skill+bonus is raised to
  1023 with an asm patch (Skills.lua:836-862). SkillsUI shows extended skills on the character screen and in shop learn
  lists; at trainers the class row is swapped per player so race modifiers apply (SkillsUI.lua:560-602).
- **All stat bonuses from skills moved out of the engine**: `CalcStatBonusBySkills` returns 0 (S:402-404); MAW's item
  pipeline (`zzMaw-Items.lua:2835-3320`) recomputes attack/damage/AC/resistances from the tables below.

### 1.2 Weapon skills (S:24-138; applied in `zzMaw-Items.lua:2835-2950, 3150-3240`)

Per skill point, by mastery N/E/M/G:

| Skill | Attack/pt | Recovery %/pt | AC (% of weapon bonus per (skill+10)) | Res (same basis) | Damage | Special (by mastery) |
|---|---|---|---|---|---|---|
| Staff | 1/2/3/4 | 0/0/0/0 | 0/2/3/4 | 0/2/3/4 (**party-wide**: every equipped staff adds to all) | +2 %/pt (min 1/pt) | M: stun (the paralysis buff) 10 % × s/estimateSkill(lvl) for 2 s; G: 4 s stun, usable with Unarmed (half the Unarmed skill replaces Armsmaster, and the full Unarmed attack and +2/pt damage are added too, `IT:3189-3199`) |
| Sword | 1/2/3/4 | 0/1/1/2 | 0/0/1/2 | — | +2 %/pt | M: dual wield (not for Seraphim) |
| Dagger | 1/2/3/4 | 0/0/0/1 | — | — | +2 %/pt | E: dual wield; M+: crit +5 % plus 1 %/pt divided by min(1+monLvl/200, 4) (only the per-point part is divided), per hand (`zzMaw-Stats.lua:83-95`) |
| Axe | 1/2/3/4 | 0/1/1/1 | — | — | +2 %/pt | G: +1 % crit **damage** per point (`AXE_CRIT_DAMAGE_PER_SKILL`, `zzMaw-Stats.lua:52,100-110`) |
| Spear | **2/4/6/8** | 0 | 0/4/6/8 | — | +2 %/pt | M: one-handed; G: each hit makes target take +(2+0.02·s)% phys damage, stacking until death, ×1.5 with 2H halberd (`MC/Damage.lua:548-566`) |
| Bow | 1/2/3/4 | 0/1/1/2 | — | — | **+4 %/pt** + flat +1/pt | M: 2 arrows; G: fire arrows (highest of fire/phys) |
| Mace | 1/2/3/4 | 0 | — | — | +2 %/pt | M: stun 15 % × s/estimateSkill(lvl) × speedMult / min(1+lvl/150,3), 2 s; G: 4 s (both are the paralysis buff; `const.Minute*2`, 2 s per game minute, halved at M; `MC/Damage.lua:266-300`) |
| Blaster | 1/2/3/4 | 0 | — | — | +4 %/pt | fixed 40 recovery, 0.4 melee mult |
| Unarmed | 2/2/3/3 | 0/1/1/2 | — | — | +2 flat/pt (all four damage fields) | |

- **Base weapon recovery** (S:25-35, 425-440): Bow 100, Blaster 40, Staff 120, Axe 140, Sword 80, Spear 120,
  Mace 100, Dagger 60, × `(0.75 + itemLevel/500)` (item level capped 600), rounded to 10; two-handed ×1.25.
  Dual wield averages the two. Recovery is **multiplicative**: `delay = base / (1+bonus%/100) / swiftness ×
  armorPenalty / hasteMult` (S:442-617). A weapon skill pays its speed bonus once, not per hand.
- Damage floor: every weapon skill point is worth at least +1 average damage (`zzMaw-Items.lua:2928-2935`).
- **Armsmaster** (S:149-160, 912-936): per point Damage 0/1/1/1.5/**2 (Supreme)**, Speed % 0/0/1/1/1, Attack 1 all
  ranks; scales with the weapon-skill damage %; split between hands; **not with staves**. Black Knight / Champion can
  reach **Supreme** (`Class Skillz.txt` row 35 `S`), auto-learned at Armsmaster 30 (50 insanity, 70 madness,
  S:2587-2595); the code grants the Supreme effects to classes 16-19 (Knight and Cavalier too) at GM and that skill
  threshold, regardless of the `S` letter; knights (class 16-19) with GM Armsmaster at the requirement get
  +floor(armsmaster/10) to every melee weapon skill, capped at 2× base (S:2598-2620).
- **Minotaur/Dwarf axe dual wield** (S:2642-2724): on the inventory screen 1H axes are re-skinned as daggers
  (`txt.Skill=2`) for Dwarf and Minotaur; Minotaur also gets 2H axes as off-hand daggers. A fake Dagger mastery is
  set for the single equip click (`tempSkillForEquip`). Axe E → 1H off-hand, Axe M → 2H off-hand (Minotaur).
  Each 2H axe in a dual-axe setup costs −10 % damage (`zzMaw-Items.lua:2856-2872`; PDF says 15 %).

### 1.3 Armour skills — armour grants magic resistance (S:125-138; `zzMaw-Items.lua:2960-2990`)

Body armour skill (of the worn body armour) scales the **AC summed from all worn armour**; Shield scales the shield.
Per skill point, as % of that AC:

| Skill | AC %/pt N/E/M/G | Resistance %/pt N/E/M/G (applied to all 6 res) | Recovery penalty % (unskilled/N/E/M/G) |
|---|---|---|---|
| Leather | 3/4/5/6 | 2/3/4/5 | 10/10/0/0/0 |
| Chain | 3/4/5/6 | 1/2/3/4 | 20/20/10/0/0 |
| Plate | 3/4/5/6 | 0/1/2/3 | 20/20/10/10/0 |
| Shield | 4/6/8/10 | 4/6/8/10 | 10/10/0/0/0; GM: −15 % all damage taken (`zzMaw-Stats.lua:1044-1052`) |
| Dodging | flat AC 4/5/6/6 per point | — | M: usable with Leather; G: dodge chance `1-1/(1+(s+10)/200)` (`MC/Damage.lua:1665-1675`) |

The armour/shield penalties also slow **spell** recovery (`zzMaw-Stats.lua:191-209`).

### 1.4 Other skills

- **Bodybuilding**: +0.5/1/1.5/2 % max HP per point (S:105, `zzMaw-Items.lua:3117`).
- **Regeneration / Meditation — continuous** (`MawRegen`, S:1338-1492, called every 0.1 s):
  - HP/s = `hpRegenRate[m] · sqrt(estimatedHealth(s^1.4) · fullHP)`, rate 5/7.5/10/10 % (`MC/Formulas.lua:185-194`);
    GM × `(1 + (1-hp%)^2)`. SP/s = `spRegenRate[m] · sqrt(estimatedMana(s^1.4/2) · pool)`, rate 2/2.5/3/4 %
    (Formulas.lua:196-218); pool shrinks with reserved buff mana (`(1-reserved)^0.5`).
  - Multipliers: ×2 after ~20 s without taking HP/SP loss, ×4 when no enemy detector (out of combat).
  - Items: special enchants +2 % HP/10 s style; Regeneration buff adds `fullHP^0.5·s^1.25·(m+1)/1000`.
  - Dragon: Regeneration also gives melee life leech (S:1494-1501).
- **Learning → Ascension** (S:1537-1568): Learning bonus to XP removed (`GetLearningTotalSkill = 0`), retroactive
  refund of all points spent in Learning (S:1544-1560). The migration also sets Learning to 0 for everyone, new games
  included, so nobody starts with Ascension. See §2.4.
- **Perception**: reduces trap and lava damage 10/30/50/70 % (S:1570-1573).
- **Alchemy cap 60** (skill cap table S:162-167; GetSkill clamps at 2× cap).
- **New extended skills** (ids 50-53, via Skillz):
  - **Cover (50)** (S:2171-2181, 1222-1313): 10 % + 1 %/pt chance (cap 30 pts → 40 %) to redirect a hit to the covering
    member (highest HP among successful rolls). N physical attacks, E other (elemental) attacks, M spells, G: attacking
    gives +15 % next-cover. Converted monster missiles use a second, uncapped formula (`zzMaw-Monsters.lua:3883-3990`).
    Toggle **P** on the skills screen. Solo: a successful cover halves the hit. Learned at training halls. Mastery
    ladder auto-learn 6/12/20 (8/20/30 insanity).
  - **Retaliation (53)**: unlocked automatically when Cover hits its cap (S:185-196). 1 %/pt chance after a cover to
    store a counter-attack. Damage, a 25 %/stack stun (2 s, 1 s on bosses) and −30 %/stack recovery apply at every
    mastery; mastery only raises the stack cap to 3 at GM; stacks expire after 10 s. Ladder 10/24/40, cap 50.
  - **Mana Shield (51)**: mana absorbs 25/50/75/100 % of every hit while enabled (`zzMaw_Legendaries.lua:61-90`); cap
    50; toggle **M**. Ladder 6/12/20 (8/20/32 insanity). Learned at magic/alchemy shops.
  - **Enlightenment (52)**: +0.5/1/1.5/2 % mana per point; divides buff reservation cost by `classSPScaling + m/2`.
- **Mastery caps for those four** come from `Class Skillz.txt` rows 50-53 (e.g. Cover: Knight M, Black Knight/Champion
  G, Monk E, Troll M, Seraphim M/Archangel G, DK M/Lich King G; Mana Shield & Enlightenment for most casters).

### 1.5 Shared misc skills (party-wide, automatic)

| Check | Rule (S line) |
|---|---|
| Repair (S:2019-2031) | best party `s·m` > item IdRepSt. Plus **auto-repair** on each Regeneration tick if best `s·m ≥ IdRepSt` (S:1316-1335) |
| Identify Item (S:2058-2070) | best `s·m` > IdRepSt; a follower with profession 4 identifies everything (S:2294-2300) |
| Merchant (S:2034-2056) | best `s·m` (+ Glamour `skill·power`); M+ or total ≥ 45 → 100; `t.Result = 7 + best` |
| Disarm Traps (S:2072-2081) | best `s·m` |
| Identify Monster (S:2083-2124) | needs best `s·m ≥ monsterLevel − avg party level` or a GM; mastery of best member unlocks N/E/M(spells)/G info |

**Solo**: misc skills 24,25,26,29,31,34,37 get mastery automatically at skill 1/4/7/10 (S:2126-2168), restored when the
party grows. NPC follower skill bonuses use **max instead of sum** (`Global/NPCFollowersSkills.lua:46` diff).

OpenYAMM already has party-wide utility skills (`OpenYAMM/game/party/Party.cpp:5106-5170`: Repair, Disarm, Merchant,
ID Item, ID Monster, Alchemy, Perception). MAW only changes the formulas (merchant cap, ID-monster level gate,
auto-repair).

### 1.6 Skill-point economy: "second school costs half"

`refundSharedCost` (S:238-262), run on every "+" click (Action 121): raising skill X from `s` to `s+1` normally costs
`s+1`; MAW refunds so that the real cost is `ceil((s+1)/n)`, where `n = 1 +` the number of **other** skills in the
shared set already at ≥ `s+1`. Shared set (S:1135): **weapons 0-7, magic schools 12-20 and the Dark Elf and Vampire
abilities 21-22 together** (Dragon Ability 23 is not in it; so a second weapon, or a school matching a weapon
level, is also discounted — README only mentions schools). For Shaman/Seraph/DK/Assassin
only magic 12-22 count. A one-time migration refunds the difference for old saves (S:1136-1218). Mastery
restoration uses the same discount (S:264-298).

### 1.7 Mastery learning requirements (horizontal mode) and teacher prices

`GetLearningRequirements` (S:215-233) applies only to `horizontalSkills` (weapons, armour, magic, racial abilities,
Bodybuilding, Meditation, Regeneration, Dodging, Unarmed, Armsmaster, Learning — S:219). Skill level needed for E/M/G:

| Mode | E | M | G |
|---|---|---|---|
| Free progression (bolster on) | 4 | 7 | 10 (vanilla) |
| Horizontal (bolster off), and Doom (`vars.Mode==2`, also set by Insanity/Madness) in either progression | 6 | 12 | 20 |
| Insanity | 8 | 16 | 25 |
| Madness | 10 | 24 | 40 |

Teacher gold (S:1841-1874): base E/M/G = 1000/4000/20000 (doom 2000/10000/50000, insanity 10k/50k/250k, madness
15k/300k/1.25M), **× (1 + number of horizontal skills the character already has at that mastery)**. Teacher dialogue
numbers are rewritten in place (S:1886-1949), `CanTeachSkillMastery` enforces it (S:1950-1973). Prices never depend on
progression. The escalation also counts respec-remembered masteries, with an off-by-one, and the engine still refuses
parties that cannot pay the vanilla price ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) §2.3-2.4). Switching free→horizontal
strips masteries above the new requirement and stores them; they are re-granted when the level is reached or when
switching back (S:1976-2011, restore in S:283-291).

### 1.8 Mastery auto-grant

- After respec / mode switch: `restoreMasteries` re-grants a stored mastery (`vars.oldPlayerMasteries`,
  `vars.storedMasteries`) as soon as the "+" click reaches the requirement (S:264-298).
- Extended skills: `autoLearnMastery` with `skillMasteryLadder` (S:176-181, 322-335).
- Armsmaster Supreme (S:337-346). Solo misc masteries (§1.5).

### 1.9 Respec (`Scripts/Global/zzMAWRespec.lua`)

NPCs 314, 413, 794 (the Oracle, Judge Grey, the Seer — one per continent) get a two-step topic ("Skill reset info" →
"I want to reset"). Cost **1000 gold × character level**. Effect: every skill > 1 goes back to 1, masteries stripped
and remembered (`respecMastery` stores the max mastery ever held); points refunded using the shared-cost discount
for the shared set and the triangular `s(s+1)/2 − 1` for others; Alchemy is not touched (level and mastery kept);
custom skills 50-53 reset to 1. Safety floor: skill points at least `Σ_{i=2..level} (4 + floor(i/10 + 1))` minus
Alchemy spend. Bug: line 63 checks `table.find(assassinClass, pl.Class)` with the global `pl`, not `p`.

### 1.10 Trainers, training, shops

- `Global/zzMAW_MoveTrainers.lua`: when `enableAllTrainers` (default true) moves 21 distinct teacher NPCs (64 entries:
  43 moves, 21 restores, on 19 map keys) into houses (table of `{npcId, houseId}` per ODM). The moves cover five skill
  groups (racial, Dodging, Unarmed, ID Monster, Regeneration); the rest relies on base teachers. The guidebook PDF lists
  locations for Race skill E/M/G, Unarmed/Dodge/ID Monster/Regen, Alchemy, Armsmaster and **Ascension E/M/G** per
  continent, but its Alchemy, Armsmaster and Ascension lines are base teachers ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md)
  §1.3-1.4).
- Training takes 2 days (0 when `vars.ChallengeMode` is set, which happens only during an online multiplayer
  session) (S:1616-1626); training-hall level caps rescaled `base^1.5/20·10` (madness `/10`); a sum of trainings on
  other continents is computed but never used, and only the current continent's halls are rescaled (S:1627-1675).
- Shops open at 05:00 instead of 06:00 (S:1577-1587). `House rules.txt` diff: spellbook shop types 1 and 5 sell one
  more tier (4→5, 5→6).

---------------------------------------------------------------------------------------------------------------

## 2. Spells

### 2.1 Table deltas (`Data/Tables/Spells2.txt` vs base, costs N/E/M/G and delays)

| Spell | Cost | Delay |
|---|---|---|
| Fire Spike (7) | = | 150 → 100 |
| Meteor Shower (9) | 20 → 40 | 100/100/100/90 → 200/200/200/180 |
| Inferno (10) | 25 → 50 | = |
| Sparks (15) | 4 → 4/8/10/12 | = |
| Lightning Bolt (18) | (Lua: M 20, G 30, SP:1884) | E 100→80, M 90→100, G 70→120 |
| Starburst (22) | 30 → 60 | 90 → 140 |
| Poison Spray (24) | 2 → 2/4/5/6 | = |
| Death Blossom (43) | 25 → 50 | 100/../90 → 180/../160 |
| Shared Life (54) | 25 → 12 (never used: M/G only, the healing table sets 25/40) | 150 → 200 (N/E/M) |
| Resurrection (55) | = | G 1000 → 300 |
| Mind Blast (59) | = | 110 → 120/110/100/90 |
| Mass Fear (64) | 15 → 40 | 80 → 200 |
| Destroy Undead (79) | 10 → 50 | = |
| Summon Wisp (82) | 25 → 25/50/75/100 | = |
| Darkfire Bolt (103) | 30 → 20 | = |
| Lifedrain (111) | 5 → 5/5/10/15 | 90 → 100 (E/M/G) |
| Flame Blast (123, dragon) | Lua: 25/40/50/60 (CL:315-318) | delay = 1.5× attack delay |
| Dragon Fear (122) | Lua: 15/15/25/30 | 120 fixed |

### 2.2 Damage rebalance (`spellPowers`, SP:1892-1933; vanilla from base Spells2 DamageAdd/DiceSides)

Damage = `dmgAdd + Σ_{skill} rand(diceMin..diceMax)` (fixed `diceMax·skill` when min==max), then Ascension scaling
(§2.4), then ×(1 + max(Int, Pers)/1000), crit, + weapon enchant damage (÷2.5 for AoE). Death Knights and Dragons
skip the stat, crit and enchant steps (SP:2005-2020). Full spec: [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §1.

| Spell | Vanilla add + 1dX/pt | MAW add + dice/pt | Notes |
|---|---|---|---|
| Fire Bolt 2 | 0 + 1d3 | 8 + 1d2 | |
| Fireball 6 | 0 + 1d6 | 0 + 1d8 | |
| Fire Spike 7 | 0 + 1d6 | 0 + 1d10 (M ×8/6, G ×10/6) | |
| Immolation 8 | 0 + 1d6 | 10 + 1d30 | buff-aura (§2.6) |
| Meteor Shower 9 | 8 + 1 | 2 + 1 | |
| Inferno 10 | 12 + 1d2 | 12 + 1d7 | |
| Incinerate 11 | 15 + 1d15 | 19 + 1d21 | |
| Sparks 15 | 2 + 1 | 0 + 1d4 | |
| Lightning→**Chain Lightning** 18 | 0 + 1d8 | 12 + 1d8; hits 1/2/3/4 targets: each bounce goes to the closest living monster within 768, hostile or not, and may return to a previous target (DM:399-428) | renamed |
| Implosion 20 | 10 + 1d10 | 20 + 1d12 | |
| Starburst 22 | 20 + 1 | 7 + 1 | |
| Poison Spray 24 | 2 + 1d2 | 5 + 1d3 | |
| Ice Bolt 26 | 0 + 1d4 | 6 + 1d7 | |
| Acid Burst 29 | 9 + 1d9 | 4 + 1d14 | |
| Ice Blast 32 | 12 + 1d6 | 6 + 1d6 | |
| Deadly Swarm 37 | 5 + 1d3 | 8 + 1d5 | |
| Blades 39 | 0 + 1d9 | 7 + 1d7 | only physical spell |
| Rock Blast 41 | 10 + 1d10 | 8 + 1d8 | |
| Death Blossom 43 | 20 + 1 | 4 + 1d2 | |
| Mass Distortion 44 | 25 % HP | **15 % + 0.5 %/pt of monster HP**, then ÷ `sqrt(bolster multiplier)` and × `max(1, (level/250)²)` (DM:363-396); GM cost = `min(lvl,255)^1.4/12.5` | |
| Spirit Lash 52 | 10 + 1d8 | 20 + 2d16; Master range 0x180 (SP:1009) | |
| Mind Blast 59 | 3 + 1d3 | 12 + 1d6 | |
| Psychic Shock 65 | 12 + 1d12 | 25 + 1d25 | |
| Harm 70 | 8 + 1d2 | 4 + 1d4 | |
| Flying Fist 76 | 20 + 1d10 | 20 + 1d5 | |
| Light Bolt 78 | 0 + 1d4 | 12 + 1d2 | |
| Destroy Undead 79 | 16 + 1d16 | 45 + 1d45 | |
| Prismatic Light 84 | 25 + 1 | 30 + 2..6 | |
| Sunray 87 | 20 + 1d20 | 60 + 1d60 | |
| Toxic Cloud 90 | 25 + 1d10 | 15 + 1d9 | |
| Shrapmetal 93 | 0 + 1d6 | 0 + 1d7 | |
| Dragon Breath 97 | 0 + 1d25 | 0 + 1d28 | |
| Armageddon 98 | 50 + 1 | 50 + 1 | |
| Souldrinker 99 | 25 + 1d8 | 25 + 1d5 | |
| Darkfire Bolt 103 | 0 + 1d17 | 46 + 1d28 | |
| Lifedrain 111 | 0 | 0 + 1d22 (M ×5/3, G ×7/3) | |

Other per-spell changes (SP:117-671, 742-798, 1008-1122, 3435-3455, 3739-3790):
Invisibility can't be cast near enemies, duration `(15 + s)·1.5` (M) / `(30 + 2s)·1.5` (G) game minutes (the
tooltip says 15+1.5 min/pt / 30+3, SP:711-716); Raise Dead GM also removes
Eradication; Protection from Magic grants immunity to **Unconscious** (SP:676-685); Fly is cancelled when attacking at
higher difficulty except 11 listed maps; Summon Wisp: MAW adds a wisp only when the engine refused to summon, up to
`2m−3` alive (SP:3435-3455); projectile spells cast without a mouse target
re-aim at the closest visible hostile (SP:3739-3778); solo: Town Portal/Lloyd/Fly/Water Walk/Jump (spell 16) scrolls are
not consumed (SP:1101-1122); Shared Life rewritten (redistributes pool, never kills, SP:824-1003); Mistform = −75 %
physical damage.

### 2.3 Extra healing spells (Body/Spirit) — `getBaseHealingSpells` (SP:2334-2353)

Heal = `(Base[m] + Scaling[m]·skill) × ascension × (1 + Personality/min(1000+3·lvl, 4000))` (SP:80-100). Heals
cannot crit (SP:88-89); map affix 31 cuts healing.

| Spell | Cost N/E/M/G | Base | Per point | Notes |
|---|---|---|---|---|
| Heal (68) | 2/4/6/8 | 4/8/12/16 | 2/3/4/6 | |
| Remove Curse (49) → heal + cure curse | –/5/10/20 | –/10/20/30 | –/4/6/8 | Spirit's extra heal |
| Cure Disease (74) → **Greater Heal** | –/–/15/25 | –/–/25/40 | –/–/7/10 | Body's extra heal, also cures disease |
| Shared Life (54) | –/–/25/40 | 0 | –/–/7/9 (halved, M −3·s, G −4·s) | |
| Resurrection (55) | G 100 | 150 | 21 | |
| Power Cure (77) | G 30 | 15 | 4 | whole party |

Insanity values are ×3-ish (SP:2336-2343). **Auto-target heals** (`autoTargetHeals`, default on): quick-casting 68,
74, 49 or 55 heals the lowest-HP% member without targeting (SP:1182-1331); 55 is broken (undefined `idx`, Greater
Heal numbers, dead members excluded; SP:1287-1294). Shaman: five of the six heals × (1 + Σschools/400); Power Cure
is excluded (loop `i=1,5`, SP:2378).
Legendaries 34/35 refund mana / recovery from overheal.

### 2.4 ASCENSION (replaces Learning)

One "Ascension level" `s` (the Learning skill; Elementalist uses Σ(Fire..Earth)/4 with mastery forced to GM, floored for
cast time; Shaman Σ(12..18)/7 with mastery forced to GM, for cost and healing only, while damage, cast time and CC
duration read Learning, which Shamans cannot learn; DK/Assassin bypass it) with mastery `m` (SP:2233-2261). Recomputed
on every action/selection (SP:2116-2164):

- **Mana cost** (damage, heal and CC spells): `baseCost × (1 + 0.125 s) × 1.04^s × (1 − 0.125 m) × 0.99^(Pers / (10 + 0.06·min(totalLevel,1000)))`
  (SP:2172-2179, 2264-2279). CC spells use `(1 + 0.2 s) × 1.03^s` (SP:2182-2196).
- **Damage**: dice max × `(1 + 0.02 s)·1.025^s`, flat add × `(1 + 0.01 s²)·1.025^s` (`MC/Formulas.lua:153-163`);
  fixed-per-point spells (Meteor Shower, Starburst, Armageddon) roll the unscaled per-point value (SP:1984).
- **Healing**: per-point × `(1 + 0.02 s)·1.015^s`, base × `(1 + 0.01 s²)·1.015^s` (SP:2063-2067).
- **Cast time**: × `1.015^s` (`zzMaw-Stats.lua:227`); CC spells × `1.015^(s − schoolSkill)`.
- **CC duration**: × `1.015^s`.

Sample multipliers:

| s | dice | flat add | heal/pt | heal base | mana (N) | mana (G) | cast time |
|---|---|---|---|---|---|---|---|
| 5 | ×1.24 | ×1.41 | ×1.19 | ×1.35 | ×1.73 | ×0.99 | ×1.08 |
| 10 | ×1.54 | ×2.56 | ×1.39 | ×2.32 | ×2.91 | ×1.67 | ×1.16 |
| 20 | ×2.29 | ×8.19 | ×1.89 | ×6.73 | ×6.71 | ×3.83 | ×1.35 |
| 30 | ×3.36 | ×20.98 | ×2.50 | ×15.63 | ×13.48 | ×7.70 | ×1.56 |
| 50 | ×6.87 | ×89.36 | ×4.21 | ×54.74 | ×45.08 | ×25.76 | ×2.11 |

(The first pass printed the mastery-0 cost in the "mana (N)" column; the values above are Novice, m = 1.)

So Ascension is a pure power/cost dial: damage per mana stays roughly flat while burst per cast and per second rise;
mastery is the only cost *reduction*. Class caps for Learning changed a lot (`Class Skills.txt` row Learning: knights,
trolls, thieves lose it; most casters reach G). The skill tooltip prints the current multipliers
(MC/SkillTooltip.lua:166-185), but its healing and mana lines use different formulas from the code
([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §2.5). Spell tooltips are regenerated per selected character with the
ascended numbers, "Recovery time", and "Not Learned / Can't learn" (SP:2281-2332, 2436-2539).

### 2.5 Control effects (CC rework, SP:1334-1865)

`CCMAP` (SP:1337-1351): base duration (game minutes; 1 min = 2 s), cost base/scaling, school, debuff:

| Spell | Base | Debuff |
|---|---|---|
| Stun | 2 min (unused: the duration is MMMerge's) | (handled separately; the only CC with a roll, `30/(30 + L/4)`) |
| Slow | 6 min | Slow |
| Charm (Mind, 60) / Vampire Charm (`const.Spells.Charm` = 113, CCMAP school DarkElfAbility) | 10 min | Charm |
| Berserk | 4.5 min | Berserk |
| Mass Fear | 3 min | Fear |
| Fear (dragon, 122, school Mind) | 4 min | Fear |
| Enslave | 5 min | Enslave |
| Paralyze | 3 min | Paralyze |
| Shrinking Ray | 4 min, flat; `m` targets in total (`m − 1` extra) in 512 radius | ShrinkingRay (power 2) |
| Dark Grasp | 6 min | ArmorHalved + Slow + DamageHalved (×0.7 monster damage, not ½; does not stack with Shrinking Ray) + MeleeOnly |
| Turn Undead | 5 min | Fear (undead only) |
| Control Undead | 10 min | Enslave (undead only) |

- **Always lands** (no resistance roll) unless blocked by diminishing returns, except Stun (above); duration =
  `base × [0.5, 0.65, 0.8, 1][mastery] × 1.015^ascension / (1 + resistance/100)`, ×2 solo, ÷2 on bosses (NameId
  220-299) for DR groups 2 and 3 only (Slow, Dark Grasp and Shrinking Ray are not halved). Dragon Fear (122) skips
  the Ascension and resistance terms (SP:1409-1412). Full spec: [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §4.
- **Diminishing returns** per monster per group (1 slow/damage-cut — exempt, 2 fear/charm/control, 3 stun/paralyze):
  CC time in the last 10 game minutes ≥15 % → ×0.75, ≥30 % → ×0.5, ≥45 % → ×0.25, ≥60 % → immune (SP:1734-1852).
- Slow, Charm, Berserk, Paralyze, Enslave, Dark Grasp, Control Undead are **fully scripted** single-target casts (mouse
  target or the lowest-remaining-duration visible hostile within 4800), Berserk/Enslave bypass engine aiming
  (SP:1486-1579). Others patch resistance/level for one tick so the engine applies, then re-time (SP:1581-1656); they
  always land (the hit roll is unused, SP:1607-1619).
- Mass Distortion/Slow engine resistance check always passes (`SpellsTweaks.lua:39` diff vs mmmerge).

### 2.6 Buff rework (mana-reserved auras, SP:2572-3424)

Every buff spell becomes a **toggle**: casting it reserves a percentage of the caster's max mana until toggled off; an
unconscious holder's aura is suspended (the reservation stays) and resumes on recovery (SP:2902-2903); duration is
effectively infinite (1 week, refreshed). Reserved % = `Cost / (classSPScaling + EnlightenmentMastery/2)` (SP:2761-2785;
class scaling = SP per level, DK 3/6/9, Shaman 1/1.5/2, Assassin 7.5). Utility spells (Torch, Wizard Eye, Water Walk)
reserve flat mana × `(1 − EnlightenmentMastery/10)` (SP:3048-3049). Temple/scroll/pedestal buffs apply as a fixed caster
(skill 7, Master, level 40); scroll/pedestal auras survive dungeons and drop on entering a different outdoor map, temple
auras drop on the next map load (SP:2694-2734). **R** in the spellbook clears all buffs (SP:22-27).

| Spell | Cost% base | Effect (Base + Scaling per skill) |
|---|---|---|
| Fire/Air/Water/Earth/Mind/Body Resistance (3,14,25,36,58,69) | 60 | +10 res (+level/4) × (1+2 %/pt) **and** +10-20 % of one stat (Int/Speed/Luck/End/Pers/Might) |
| Haste (5) | 120 | +10 % +0.2 %/pt recovery speed |
| Shield (17) | 75 | −15 % −0.3 %/pt magic damage |
| Stone Skin (38) | 75 | +20 AC (+level/4; the tooltip says /2) × (1+2 %/pt) |
| Bless (46) | 75 | +20 attack (+level/4) × (1+2 %/pt), +10-20 % Accuracy |
| Fate (47) | 75 | +5 % +0.1 %/pt crit |
| Heroism (51) | 120 | +15 % +0.3 %/pt melee damage |
| Empower Magic (28) | 150 | spell damage; the code reads **Haste's** row, so +10 % +0.2 %/pt (SP:2048) |
| Hammerhands (73) | 75 | +15 % +0.3 %/pt unarmed damage |
| Meditation (56, replaces Mind spell) | 120 | party SP regen ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §3.4) |
| Regeneration (71) | 120 | party HP regen; uses the `Base` value where `Scaling` was meant (S:1370-1371) |
| Preservation (50), Pain Reflection (95), PfM (75), Fire Aura (4), Vampiric Aura (91), Immolation (8) | 90/150/180/40/120/10 | permanent; Preservation and Pain Reflection as vanilla; PfM never loses charges and blocks Unconscious; Fire Aura is weapon item-level damage × 10-25 % (IT:4280-4300); Vampiric Aura is a fixed party leech (IT:3272-3276); Immolation is MAW damage 10 + 1-30/pt |
| Day of the Gods (83) | 200 | +10-20 % of all 7 stats (1 % per 7 Light) |
| Day of Protection (85) | 150 | all resistances (Light skill counts 2/3) |
| Hour of Power (86) | 300 | Haste+Shield+Stoneskin+Fate at skill/1.5 |

Caster skill counted for buffs is the **base** school skill (item bonuses ignored), capped at 50 (day buffs 75)
(S:169-172, SP:3098-3099).

### 2.7 Cast speed (`getSpellDelay`, `zzMaw-Stats.lua:162-245`)

`delay = vanillaDelay[mastery] / (1 + floor(Speed/20)/100) × 1.015^ascension / hasteMult / 1.1 (spell-haste enchant) ×
(1 + armour/shield penalty)`; Ascension applies only to damage, healing and CC spells; CC delay has no Speed, Haste or
armour term and uses `1.015^(asc − school)` (ST:211-217); Elementalist ×1.5 then ÷(1 + 5 %·stacks); Assassin = 2× attack
delay; Flame Blast = 1.5× attack delay.

### 2.8 Extra quick spells, spell books, misc

- `ExtraQuickSpells.lua` is MMMerge's 4 extra quick-spell slots (keys F5-F9 per the shortkey sheet); MAW only fixes
  the SP check to use the caster's mastery cost (diff lines 43-49).
- **Spellbook rework** (SP:3637-3726, `MC/Tooltip.lua:868-895`): every generated spellbook becomes a sealed
  "<School> Magic Book" (items 971-979, real book id in BonusStrength) that reveals itself when a character with the
  required school mastery (from the book's IdRepSt: <5 N, 5 E, 10 M, 15 G) hovers it. New icons per tier.
- **TAB** in the spellbook cycles school pages the character knows (SP:3539-3563).
- `zzMaw-BookSwitches.lua` is **not** about spells: it fixes clickable bookshelf secret doors in 7d12 and 7d37.

---------------------------------------------------------------------------------------------------------------

## 3. Classes

### 3.1 New classes (`Class Extra.txt`, `Class HP SP.txt`, `Class Skills/Skillz.txt`)

| Kind | Ids | Tiers | HP base/lvl | SP base/lvl, stat | Promotion qbits |
|---|---|---|---|---|---|
| 17 Seraphim | 53-55 | Seraphim, Angel, Archangel | 40 / 3,4,5 | 15 / 1,2,3, Personality | Cleric's |
| 18 Death Knight | 56-58 | Death Knight, Death Lord, Lich King | 35 / 4,5,7 | 60,80,100 / 0, Int (no SP from items) | Knight's |
| 19 Shaman | 59-61 | Shaman, Sekhem, Marabou | 25 / 3,4,5 | 10 / 1, Int+Pers | Druid's |
| 20 Elementalist | 62-64 | Elementalist, Elemental Adept, Master of Elements | 15 / 2,2→2.5 (CL:606),3 | 30 / 4,6,8, Int | Sorcerer's |

(Thief/Rogue/Assassin/Spy are reworked into an **Assassin** energy class too, see 3.3.)

Starting skills (`Class Starting Skills.txt`, columns indexed by class/2; F = has, C = can choose):
Seraphim: Sword, Light free; Spear, Shield, Chain, Plate, Spirit, Merchant, Repair, BB, Meditation choosable.
Death Knight: Axe, Plate, Dark, Perception free; Sword, Bow, Water, Body, ID Item, Merchant, Repair, BB, Regeneration,
Armsmaster. Shaman: Dagger, Earth free; Mace, Leather, Water, Spirit, Body, Meditation, Perception, Alchemy, Learning.
Elementalist: Staff, Fire free; Dagger, Leather, Air, Water, Earth, ID Item, Merchant, ID Monster, Alchemy.
Portrait 76 (zombie troll) now a Troll DK available at start (`Character portraits.txt` diff).

Perks (class description shown on right-click of the class name at creation; tooltips in MC/SkillTooltip.lua:338-485):

- **Seraphim** (CL:163-226; `zzMaw-Items.lua:2889`; `MC/Damage.lua:1889-1903`): Mind adds `s·(m+1)/2` flat melee damage
  (armsmaster-like); Body heals the most injured member on hit (`s^1.3·m·meleeDamageMult·(1+Pers/1000)·2`, DM:119);
  Light +0.5/1/1.5/2 % attack speed per point and lets a 2H sword be held in one hand with a shield; Spirit flat damage
  reduction; no sword dual wield; **Divine Protection**: a lethal hit heals 25 % max HP instead, 5 min (150 game min)
  cooldown.
- **Death Knight** (CL:521-596; `MC/Classes.lua:17-225, 458-486, 757-887`): schools renamed Frost (Water), Blood (Body),
  Unholy (Dark). Cannot learn spell books; each mastery rank unlocks one spell: Frost Icy Touch/Water Walk/Frostbite/
  Ice Bomb (100-120 % / 150-200 % / 75 % of weapon damage), Blood Blood Leech/Regeneration/Asphyxiate (110-140 %, 4 s
  stun)/Superior Blood Leech, Unholy Vampiric/Death Coil (100-120 %)/Death Grasp/Death Breath (60 %). Spell costs fixed
  (Icy Touch 15, Frostbite 30, Ice Bomb 50, Blood Leech 6/hit, Asphyxiate 70, Death Coil 30, Death Grasp 15/hit, Death
  Breath 100). Blood Leech/Death Grasp are **on-attack toggles**. Spell delay = attack delay. Frost and Unholy add
  0.5/0.75/1/1 damage per point, ramping gradually between mastery thresholds (`GetGradualMasteryValue`); Frost +1 %
  attack speed/pt; Blood −% physical damage and +10 % physical leech; Unholy −% magic damage. Buffs reserve nothing.
  Also: SP gained per melee hit 10/15/20 (×1.5 on kill), Icy Touch slows, Death Coil heals 20 % (30 % only at Master),
  and a quick-cast toggle bug ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §5.3).
- **Shaman** (CL:488-515; MC/SkillTooltip.lua:341-374): every school gives a melee perk: Fire `s/10` % of the target's
  **current** HP as fire damage, at least `s`, then ÷ fire resistance; Air −% all damage; Water flat damage reduction;
  Earth `s·m/2` melee damage; Spirit +s % melee damage only (healing scales with Σ7 schools/400, spell damage with
  Σ/200; DM:1118-1128); Mind restores `s^1.25` SP per hit; Body leeches HP per hit. "Every 7 skill levels adds 1
  Ascension": Σ/7 with mastery forced to GM, for cost and healing only.
- **Elementalist** (CL:599-665; MC/Classes.lua:300-363, 488-587; `MC/Damage.lua:160-190`): learns Fire/Air/Water/Earth
  spells by **casting** (progress `tier^1.5·monsterLevel^0.5` per hit, × √(party size) outside Insanity, ÷3 for AoE
  except Sparks/Poison Spray; thresholds 0…320000; tier mastery gates N×4, E×3, M×3, G); cannot learn Ascension (it
  equals Σschools/4 with mastery forced to GM; cast time floors it); 50 % slower base casts; each offensive cast adds a
  stack (+10 % damage, +5 % cast speed, +1 base cost and +7.5 % total cost), halved after `max(4·delay, 128)` ticks
  without casting and then every 0.5 game minute, reset by weapon/spellbook use; no stacks when the rotation is off or
  never bound. Quick-spell slots are re-rolled randomly within the slot's category (single target / shotgun / AoE);
  **R** on the skills screen toggles the rotation.
- **Assassin** (Thief line; MC/Classes.lua:68-101, 239-292, 365-450, 589-640): schools renamed Combat/Subtlety/Poisons/
  Assassination; SP = energy (60-80 base, regen `(0.6+0.2m)·10`/s from Poisons). Melee costs 50−5m energy (m = Combat
  (Fire) mastery), grants a combo point (max 5); arrows cost half and give 0.5 combo; Assassination adds +10 max
  energy per mastery. Spells cost combo points (Fireball 5, Fire Spike 3, Lightning Bolt (18) 5, Poison Spray 3, Acid
  Burst 3, Stun 3, Blades 3, Mass Distortion 4) and deal 75-400 % of melee damage. Assassination adds `s·(1+m)` damage
  reduced 20 % per nearby monster (the target counts; cut capped at 80 %); with too little energy the whole bonus is
  lost. Spells known by mastery, not books.

### 3.2 Promotions (CL:7-158)

- `promotionList[kind]` lists for each class kind the MM6 promotion qbits (2), MM7 promotion qbits (4) and MM8
  promotion (qbit or award). **Any** world's promotion promotes the character (cross-world). MAW classes reuse:
  Seraphim→Cleric, DK→Knight, Shaman→Druid, Elementalist→Sorcerer.
- If a kind has several final classes (e.g. MM7 Light/Dark), the character gets a **random** one (CL:118-127).
- Completing the promotion on 2 or 3 worlds renames the class "Elder X"/"Ultimate X" and multiplies its HP/SP factors
  by 1.25/1.5 (CL:96-108) — note this rewrites `Game.Classes` globally.
- MAW classes have a mid promotion (Step 0→1) from the first-tier qbits (`midPromo`, CL:51-60, 131-145).
- Lich at level 1 is reset to Necromancer (CL:723-733).
- Missing above: step 0 can jump to step 2; promotions are party-wide qbit checks; a `promotionCount` reuse bug
  ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §5.9).

### 3.3 Rebalanced vanilla classes (table diffs)

`Class HP SP.txt`: Priest Light/Dark +1 HP, +1 SP/level; Patriarch +1 HP; **Dragon HPFactor 10→5 (Great Wyrm keeps
10), SPFactor 5/10 → 0** (fixed SP 60/120, CL:320-325); Knight 5→4, Cavalier 7→6; Minotaur 4→6, Minotaur Lord 6→12;
Monk 5→4; Master/Ninja SP 1→2; Ranger line gets SP (base 5, +1 IP); **Thief line: HP 35→25 and HP per level
4/6/8/8 → 3/4/5/5, SP base 60/70/80 (energy)**; Troll 5→6, War Troll 8→12; Nosferatu, Lich, Arch Mage, Dark Arch
Mage, Master Wizard, High Priest +1 HP/level; Warlock, Arch Druid, High Priest +1 SP/level.

`Class Starting Stats.txt`: Dragon Might/End/Acc/Speed/Luck 11/30 → 14/50, +3 per point; Dark Elf Int 11/25 → 14/30,
"+ add" 1 → 2.

Skill caps (summary only; the game uses `Class Skillz.txt`, not `Class Skills.txt`, see
[TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) §6.1-6.2): in short — hybrids and archers get Master/GM in
more weapons and all four elements (Master Archer/Sniper G); knights gain Staff/Axe up to G but lose Learning; clerics
get Bow; **Ranger line gets all 7 non-light/dark schools to E/M**; the Thief line gets elements (G in all four for
Assassin/Spy), Dodging E/M/G/G, and loses Shield, Armsmaster and Learning; Monks lose Armsmaster; Minotaurs get
Spirit/Mind/Body, Meditation, Regeneration, Learning M/G; Monks get Regeneration, Alchemy G; Vampires get Staff,
Bodybuilding, Armsmaster G; misc skills (ID Item, Repair, Disarm, ID Monster, Alchemy) opened widely at Basic.
Dragons lose Meditation (refunded, CL:346-361) and Learning; Troll and War Troll lose Learning too. Black
Knight/Champion Armsmaster **S**.

---------------------------------------------------------------------------------------------------------------

## 4. Races

| Race | Flat skill bonus: +3 and +floor(base/10) (S:2350-2400) | Mastery modifiers (`Race Skillz.txt`; `Race Skills.txt` is not read) | Other (Race PDF; code elsewhere) |
|---|---|---|---|
| Human | Leather, Chain, Plate, Shield | **+1 mastery** on ID Item, Merchant, Repair, Perception, Disarm, ID Monster, Alchemy | |
| Vampire | — | Vampire Ability min Master; lost forced Meditation | leech 5 % melee / 2.5 % ranged & spell (×2 for vampire class) (`zzMaw-Items.lua`); Preservation 22:00-04:59 and indoors; Mind immunity (ST:1363-1365) |
| Dark Elf | Bow, Spear, Meditation | Dark Elf Ability min Master | +25 + level to Fire, Air, Water, Earth (ST:1367-1368) |
| Minotaur | Axe | Axe min Expert; Dagger 0 (axes off-hand); lost Plate E+1 and BB +1 | dual-wield 1H+2H at Axe E, 2H+2H at Axe M |
| Troll | Regeneration, Mace, Staff | Regeneration `+` (one step) | +25 Water/Earth res (+1/level) |
| Dragon | — | all weapons/armour 0; Dragon Ability, Dodging(Scales), Unarmed(Fangs) min Master | fangs/breath/scales scale with level (MC/Classes.lua:715-841), all item-derived stats, HP, SP, AC and resistances ×3 (IT:3002-3015), fire res +100 + 2 × level |
| Undead | — | — | Mind & Body immunity |
| Elf | Bow, Spear, Meditation | lost Meditation +1 | +25 + level to Fire, Air, Water, Earth (ST:1367-1368) |
| Goblin | Sword, Mace, Dagger, Leather | — | +25 Air/Earth res |
| Dwarf | Shield, Bodybuilding (Axe per PDF, missing in code) | Axe min Expert | 1H axe dual wield at Axe E; +25 Mind/Earth res |
| Zombie | — | — | Zombie condition |

`Race Skills.txt` grew 33 columns (race × Seraphim/DK/Shaman), but MAW never reads it
(`Scripts/Structs/RacialSkills.lua` is empty); only `Race Skillz.txt` counts, so base racial bonuses such as Human
Learning +1 or Goblin Disarm +1 are gone ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) §6.4). `Extra Skillz.txt` is
header-only.

---------------------------------------------------------------------------------------------------------------

## 5. Alchemy

### 5.1 How base MMMerge alchemy works (what OpenYAMM implements today)

Reagent + bottle → base potion with power = reagent power + alchemy skill; two potions mix through the MM8 `POTION.TXT`
matrix (about 2,400 cells: 1,486 E3 and 566 E4 explosions, many dilution/catalyst cells); mixing needs the result's
mastery; power of a mix = average; effects are vanilla MM8 (`Cure Wounds 10+power`, buffs 30 min/power) plus
MMMerge's ExtraPotions (essences, pure stats, rejuvenation...). OpenYAMM mirrors this
(`OpenYAMM/game/items/InventoryItemMixingRuntime.cpp`, effects hard-coded in `InventoryItemUseRuntime.cpp`: the
dispatch is `ConsumePotion` at 1099-1275; 168-417 are helpers).

### 5.2 MAW tables

- **New mix matrix** in `Data/zMaw.T.lod/POTION.TXT` (extract it from the LOD to read it): only **87
  recipes** over 100 columns; there are no explosion or dilution cells, but the engine's mastery check still fails
  under-skilled mixes. `POTNOTES.TXT`, `ITEMS.txt` (potion names),
  `class.txt`, `SPCITEMS.TXT`, `rnditems.txt`, `MONSTERS.txt`, `mapstats.txt`, `Placemon.txt` are also overridden in that LOD.
- `Potion settings.txt`: same 0-70 layout, flags changed (233, 246-250, 263 become drinkable; 238, 243, 244, 255, 256
  usable; 264-290 neither = removed), and rows 71-102 added so gems/crafting items 1041-1069 go through the
  "use potion on item" path (`evt.PotionEffects[71..98]`; 99 is the Endless Potion with no effect function, 100-102
  duplicate 1067-1069). The Notes column is shifted versus real item names — use
  ITEMS.txt names.

### 5.3 Recipe tree (ITEMS.txt names; "+" = mix)

| Tier (mastery) | Recipes |
|---|---|
| Base (0) | reagent + bottle: Red 222 **Cure Wounds**, Blue 223 **Magic Potion**, Yellow 224 **Energy Potion**, Gray 221 **Catalyst** |
| Secondary (Novice) | R+B = 226 **Hexbane** (purple); R+Y = 225 **Antidote** (orange); B+Y = 227 **Lucidity** (green) |
| Tertiary (Expert) | R+O 228 **Haste**, R+P 229 **Heroism**, R+G 230 **Bless**; B+O 231 **Protection**, B+P 232 **Meditation**, B+G 233 **Regeneration**; Y+O 234 **Stone Skin**, Y+P 235 **Water Breathing**, Y+G 236 **Harden Item**; O+P 237 **Magic Protection**, P+G 238 **Enchant Item**, O+G 239 **Stone to Flesh** |
| White (Master) | Orange + {Haste/Heroism/Bless} 245 **Champion's**, + {Prot/Med/Regen} 243 **Lesser Element**, + {Stone Skin/Water B./Harden} 244 **Swiftness**, + {MagicProt/Enchant/StoneToFlesh} 250 **Self Resistance**; Purple + same groups → 240 **Power Boost**, 241 **Wisdom Boost**, 242 **Resilience Boost**, 249 **Elemental Resistance**; Green + same groups → 247 **Divine Cure**, 248 **Divine Magic**, 246 **Divine Restoration**, 251 **Paladin's** |
| Black (Master; 262/263 GM) | Red + {240-242} 252 **Pure Power**, + {243-245} 257 **Divine Blessing**, + {246-248} 258 **Twilight**, + {249-251} 261 **Pure Elemental Resistance**; Blue + groups → 253 **Pure Wisdom**, 256 **Darkness**, 260 **Dawn**, 263 **Divine Resistance**; Yellow + groups → 254 **Pure Resilience**, 255 **Greater Element**, 259 **Transcendence**, 262 **Pure Self Resistance** |

The in-game **ALT** tooltip prints exactly this per potion (`potionRecipeText`, AL:544-583; shown by
`MC/Tooltip.lua:124-130`, "Press alt to show recipe list" otherwise).

### 5.4 Effects (AL:62-271, 283-542; `Global/zzMAWPotions.lua`)

Duration of every timed potion: **6 h + 6 min × best party Alchemy skill at GM** (AL:78-85). Drinking with enemies
detected costs 60 recovery, charged to whichever member acts. Power is clamped to 500. Potions marked † have **5
charges** (AL:283); the Endless Potion 1069 recharges only 8 of them (231, 232, 233, 237, 245, 251, 257, 263). Full
spec: [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §7.4.

| Id | Name | Effect | Power req |
|---|---|---|---|
| 222 | Cure Wounds | HP 20 + 25 % of an estimated HP pool at "level = power" (AL:412-427) | |
| 223 | Magic Potion | SP 10 + 25 % of estimated SP pool | |
| 224 | Energy Potion | cure + immunity Weak, Sleep | |
| 225 | Antidote | cure + immunity Disease, Poison | |
| 226 | Hexbane | cure + immunity Curse, Paralysis | |
| 227 | Lucidity | cure + immunity Fear, Insanity | |
| 228† | Haste | attack speed % (buff curve 5.5); divides spell recovery too (ST:218-224) | |
| 229† | Heroism | melee damage % | |
| 230† | Bless | attack + accuracy % | |
| 231† | Protection | Shield (magic dmg %) + Preservation | 20 |
| 232† | Meditation | +ceil(√power/1.5)+1 Meditation skill | |
| 233† | Regeneration | Regeneration buff at skill power/2, GM | |
| 234† | Stone Skin | AC | |
| 235† | Water Breathing | no drowning | 20 |
| 236 | Harden Item | (vanilla, on item) | |
| 237† | Magic Protection | PfM; the 0.5 s aura pass rewrites the buff to Power 4, Skill 10 while the timer runs (SP:2985-2990), so the power (5 + power/10 charges, ≥50 blocks death/eradication) has no effect; any PfM also blocks Unconscious | |
| 238 | Enchant Item | random base enchant on an item with no Bonus, Bonus2 or second enchant, strength = min(power,500)/5 × slot mult (10 % chance of a skill enchant, √-nerfed; jewellery rolls 1-16) (`zzMAWPotions.lua:58-96`) | none (text says 20) |
| 239 | Stone to Flesh | cure + immunity Stoned | 20 |
| 240† | Power Boost | Might + Accuracy (temp): only sets the engine TempMight etc. timers with `Skill = 0`, never their Power, and has no aura row, so it gives nothing on a fresh character (AL:165-176) | |
| 241† | Wisdom Boost | Intellect + Personality (same defect) | |
| 242† | Resilience Boost | Endurance + Speed + Luck (same defect) | |
| 243 | Lesser Element | random tier-2 elemental enchant on a weapon | 40 |
| 244 | Swiftness | "of Swiftness" (Bonus2 59) on a weapon | 40 |
| 245† | Champion's | Haste + Heroism + Bless | |
| 246 | Divine Restoration | cure + immunity to every condition but Dead/Eradicated, plus Unconscious | 40 |
| 247† | Divine Cure | HP 50 + 35 % of pool | |
| 248† | Divine Magic | SP 50 + 35 % of pool | |
| 249† | Elemental Resistance | F/A/W/E res + stats % | |
| 250† | Self Resistance | Mind/Body res + stats % | |
| 251† | Paladin's | Shield + Stone Skin + Preservation | |
| 252 | Pure Power | **permanent** Might+Accuracy +20 per 50 power, highest only | |
| 253 | Pure Wisdom | permanent Int+Pers | |
| 254 | Pure Resilience | permanent End/Speed/Luck | |
| 255 | Greater Element | tier-3 elemental enchant | 55 (text 50) |
| 256 | Darkness | "of Darkness" (Bonus2 41) | 100 (drink-table req 50) |
| 257† | Divine Blessing | all 7 stats % (Day of the Gods curve) | |
| 258 | Twilight | sets the current age to 60 once (BirthYear, AgeBonus 0); ageing continues | none |
| 259 | Transcendence | permanent skill points `5·step² + 15·step`, step = floor(power/50), only the increase over the best step drunk | |
| 260 | Dawn | sets the current age to 20 once; ageing continues | none |
| 261 | Pure Elemental Res. | permanent +30 per 50 power F/A/W/E | |
| 262 | Pure Self Res. | permanent +30 per 50 power Mind/Body | |
| 263† | Divine Resistance | all resistances (Day of Protection curve) | |
| 264-299 | — | "Potion Deleted in MAW" | |

**Potion buff strength** (SP:3111-3215): a potion acts as a Master-rank caster with skill `50·(f−1)` (70 for
DoG/DoP) and caster level `0.5·power·f`, where `f = 0.75 + 0.75·min(power,200)/200`. Examples:

| Power | Haste | Shield/Heroism | Fate (no potion grants it) | stat % |
|---|---|---|---|---|
| 0 | +7.5 % | 11.2 % | 3.8 % | 7.5 % |
| 50 | +9.4 % | 14.1 % | 4.7 % | 9.4 % |
| 100 | +11.2 % | 16.9 % | 5.6 % | 11.2 % |
| 200+ | +15.0 % | 22.5 % | 7.5 % | 15 % |

Flat buffs (Stone Skin, Bless attack, resistances) use `level_p = 0.5 × P × f` with P up to 500, so they keep
growing past 200.

**Non-stacking with Light/other buffs**: `getBuffSkill` returns the stronger of the party caster's aura and the
drinker's own potion for each buff (SP:3204-3215), so potions and spells never add up. The comparison is on
`buffStrength` (SP:3192-3202), not on the applied value, and Hour of Power counts for Haste/Shield/Stone Skin. Potions
are per-drinker; spell auras are party-wide.

### 5.5 Reagents, power, drops

- Reagent power (AL:587-633, `MC/Tooltip.lua:134-139`): `base × (1 + bonus·0.25/20) + 0.75·bonus`, base 1/5/10/20/30
  per tier (gray top tier 45), `bonus` = item level (`partyLevel/5` on generation, AL:641-651; `partyLevel/2` for
  monster drops; `partyLevel` is `getPartyLevel()`, the summed level of the other continents, not the character
  level). Alchemy adds +0.5·s at Master, +s at GM. Capped at 255; the excess /2 is added to the Alchemy skill
  as a hidden bonus (via `skillCapExtra`). The engine then mixes as usual (average of the two).
- Monster drops (AL:654-698): Master 1 %, GM 2 % per kill (best party member), tier by monster level; when item level +
  `s × m / 2` would exceed 200, a random ready potion 221-224 drops instead, with that sum as power (AL:683-689). GM:
  0.2 % **Endless Potion** (1069, `BonusStrength = min(s + 10, 100)`, the number of charges it adds, AL:1011).
- Black-potion quests: MAW's turn-in handlers replace MMMerge's duplicates (`Global/zzMAW_PotionQuests.lua`).

### 5.6 Hotkeys (S:1039-1122)

**G** drinks the strongest Cure Wounds (222) carried by Party[0], **V** the strongest Magic Potion (223), solo only,
15 s cooldown each, status text. Their formulas differ from drinking: G heals `round(power^1.4)+10`; V *displays*
`power^1.4·2/3+10` but adds `20 + 2·power`. Divine Cure/Magic (247/248) are not used. Not a design to copy.

### 5.7 Fit with OpenYAMM's alchemy bench

What we have (`OpenYAMM/game/items/AlchemyBenchRuntime.{h,cpp}`, `GameplayAlchemyBenchInputController.cpp`): a full-screen
bench with an ingredient list (all packs, filters), a **recipe book** built from reagent settings + unlocked potion
autonotes (`buildBook`), preview with outcomes (Known / Unknown / TooDifficult / KnownExplosive), Mix / Mix All,
search, and a **chain planner** that brews missing intermediate potions from known recipes, never risking an explosion,
assuming average power for mixes and `alchemyLevel + reagentPower` for reagents.

What MAW needs:

1. **Data swap (no code):** MAW `potion.txt` matrix, `potnotes.txt`, `potion_settings.txt`, item names/notes for 221-263
   and the reagent table. Because MAW has no explosions, `KnownExplosive` never triggers; the planner works as is.
2. **"All recipes known"** ruleset flag: MAW shows every recipe (ALT). The bench should treat every MAW recipe as known
   (bypass the autonote gate in `isPotionRecipeKnown`), or auto-unlock all potion notes at new game.
3. **Reagent power formula**: `reagentPower()` today reads the definition; MAW's depends on the reagent's **item level**
   (`Bonus`) and Alchemy mastery (+0.5s/+s), with a 255 cap. Needs a per-ruleset formula (or a data-driven curve) in
   `InventoryItemMixingRuntime::reagentPower` and in `AlchemyChainPlanner::tryRecipe` (which currently uses
   `alchemistLevel + reagentPower`).
4. **Potion effects as data**: MAW effects are formula-heavy (6 h duration, charges, power requirements, per-drinker
   buffs that compete with spell auras, permanent step ladders). OpenYAMM's effects are a C++ switch. A
   `potion_effects.yml` (per item: kind = heal/restore/immunity/buff/permanentStat/permanentRes/skillPoints/age/
   itemEnchant, targets, curve parameters, duration, charges, min power) would serve MAW and clean up vanilla too.
5. **Charges** on potions (5 uses, Endless Potion recharge) — inventory item field exists (`Charges`) in MAW; ours
   already has `currentCharges` / `maxCharges` (`Party.h:62-63`); only the semantics and tooltip are missing.
6. Crafting gems/cube/eye/hourglass/mirror/pearl/orbs are routed through the potion-on-item path (rows 71-102,
   effects `evt.PotionEffects[71..98]`, AL:712-1089; the Crafting Cube and Endless Potion are not potion effects but
   go through the tooltip path) — that is item crafting scope, but the bench could host it (see §7).

---------------------------------------------------------------------------------------------------------------

## 6. UI elements and keyboard shortcuts

UI:
- Skill hint window rebuilt in Lua for every skill (`MC/SkillTooltip.lua:61-95`): mastery rows coloured white (can
  reach), yellow (reachable after promotion), red (never); "Bonus: +N"; per-row Supreme/Ultimate/... names.
  Dynamic bodies: Regeneration (current HP/s, next level), Meditation (SP/s, next level), Ascension (all six
  multipliers), Spear GM stack %, armour (current AC from items, bonus AC/res), Cover/Mana Shield (chance,
  efficiency, enabled state), Retaliation (power/vitality coefficients, damage), Mace stun chance vs your level,
  Armsmaster Supreme requirement, class school texts for Shaman/DK/Seraph/Elementalist (spell-learning progress %)/
  Assassin, dragon Fangs/Scales.
- Weapon/armour skill tooltips get an auto-generated per-mastery table "Attack | Speed | AC | Res" (S:748-939).
- Spell tooltips: ascended damage numbers, mana reserved and who holds the aura, recovery time, CC duration vs a
  same-level monster, "Not Learned"/"Can't learn" (SP:2436-2539).
- Misc header on the skills screen re-padded for the extended skills (S:2184-2233).
- Elementalist and Assassin stack counters drawn above each portrait (CL:639-649, 694-704).
- Potion tooltips: dynamic effect text, heal amounts, charges, recipe list on ALT; reagent "Power: N"; gem tier/cap.
- Teacher dialogues rewritten with the real requirement and price (S:1886-1949).
- Character creation: free class/portrait selection always on; MAW class descriptions on right-click.
- Settings page "MAW settings": Buff Rework, M&M6 Projectiles, Homing Projectiles, Friendly damage, Loot filter,
  Extra item tooltip (`zz_Maw-initialize.lua:537-566`); external `MAWSettings.lua` for keys and flags.

Keys (`zz_Maw-initialize.lua:1-40`, guidebook PNG):

| Key | Where | Action |
|---|---|---|
| G / V | map, solo | drink strongest HP / SP potion, 15 s cooldown |
| E | map, solo knight | Charge to target (500-3000 range), paralyses 1.5/2/2.5 min by tier, 25 s cooldown (S:953-1037) |
| E | inventory | give alchemy/crafting items to this player when sorting |
| P / M | skills screen | toggle Cover / Mana Shield |
| R | skills screen | toggle Elementalist rotation |
| R | spellbook | remove all buffs |
| R / T / C / G | inventory | sort current tab / all players' current tab / player's all tabs / everything |
| R | shop | reroll wares |
| TAB | spellbook | next school page |
| U | inventory | 3 gems → 1 higher gem |
| ALT / ALT+TAB | inventory | show possible enchants / recipes (+ pin) |
| K | map | teleport up to 30 corpses/crafting drops to you |
| L | map | unstuck (Z +100, 5 min cooldown) |
| O | map | disable bow |
| F5-F9 | map | extra quick spells |

---------------------------------------------------------------------------------------------------------------

## 7. Mapping to a data-driven OpenYAMM ruleset, and cheap high-value improvements

OpenYAMM has **no ruleset concept yet** (`OpenYAMM/devdocs/vanilla/README.md`): every gameplay table comes from
`assets_dev/engine/data_tables/`. The vanilla investigation already proposes `assets_dev/engine/rulesets/<id>/` overriding
named engine tables, with the ruleset id stored in the save. MAW fits as `engine/rulesets/maw/`.

### 7.1 Table overrides (pure data, our existing tables)

| OpenYAMM table | MAW variant from |
|---|---|
| `class_skills.txt` | `Class Skillz.txt` rows 0-38 + 12 new class columns; needs **Supreme** letter for Armsmaster |
| `class_multipliers.txt` | `Class HP SP.txt` |
| `class_extra.txt` | `Class Extra.txt` (kinds 17-20) |
| `class_starting_skills.txt`, `class_starting_stats.txt` | MAW versions |
| `race_skills.yml` | `Race Skillz.txt` mastery modifiers (`Race Skills.txt` is not read) |
| `spells.txt` | `Spells2.txt` cost/delay diffs + `spellPowers` damage (our table already has DamageBase/DiceSides columns) |
| `potion_settings.txt`, `english/potion.txt`, `english/potnotes.txt`, `items.txt` (221-299 names/notes) | MAW LOD + settings |
| `house_rules.txt` | spellbook shop tiers |
| `english/class.txt` | class names/descriptions (MAW LOD + CL descriptions) |

### 7.2 New data tables (one schema, two rulesets)

- `skill_rules.yml`: per weapon/armour skill and mastery — attack/pt, recovery %/pt, damage %/pt, AC %/pt, res %/pt,
  impair %, special flags (dual wield, stun, crit, stacks), base weapon recovery; Armsmaster rows; Bodybuilding %;
  regen/meditation rates; skill caps (Alchemy 60, Cover 30...). Vanilla rows reproduce MM8.
- `mastery_requirements.yml`: skill level per mastery per difficulty mode and teacher price ladders (+ escalation).
- `spell_scaling.yml`: Ascension constants (0.02, 0.01, 1.025, 1.04, 0.125, 0.125/mastery, 1.015), healing table,
  CC table (`CCMAP`), DR thresholds, buff-aura table (`buffSpell`/`buffPower`), personality cost curve.
- `potion_effects.yml` (see 5.7) and `reagent_power` curve.
- `race_skill_bonuses.yml`: flat +3 and +1 per 10 per race and skill; racial resistances; axe off-hand rules.
- `class_perks.yml`: declarative hooks for the four new classes where possible (school → perk kind + formula), with
  the remaining class mechanics (DK spells by mastery, Elementalist casting progress/stacks, Assassin energy/combo
  points, Seraph Divine Protection) as named C++ behaviours selected by the table.

### 7.3 Code changes (cannot be data alone)

Buff auras with mana reservation (largest system change: buff UI, regen pool, save state); continuous regeneration;
Ascension scaling in spell cost/damage/cast time; scripted CC with diminishing returns; shared-cost skill discount;
respec service and remembered masteries; cross-world/random promotions and Elder/Ultimate scaling (do it per
character, not by mutating the class table); extended skills Cover/Mana Shield/Retaliation/Enlightenment; four new
classes and the Assassin rework; axe dual wield; spellbook sealing; auto-target heals; potion charges and per-drinker
potion buffs that compete with auras.

### 7.4 Cheap, high-value improvements (we are not bound by vanilla UI)

1. **Recipe book already exists — make it MAW-aware**: show every recipe as a tree (base → secondary → tertiary →
   white → black) with the real *effect at the power you would brew*, the power requirement and charges; one click
   "brew N" via the existing chain planner. Replaces ALT tooltips.
2. **Potion quick-slots** on the HUD (2-4 slots per character, bound to keys, cooldown ring) instead of hidden solo-only
   G/V keys; pick "strongest of type" automatically; work in parties; use one heal formula.
3. **Skill tooltips with next-level and next-mastery numbers** for every skill (we already compute them): "at 21: +2 %
   damage, +1 attack; Expert at 12: recovery bonus 1 %/pt".
4. **Respec preview**: before paying, show refunded points, gold cost, masteries that will auto-return and at which
   level; optional "plan" mode to allocate points in a sandbox before committing.
5. **Skill-point cost preview** on the "+" button: show the discounted cost (`ceil((s+1)/n)`) and why, so the
   shared-school discount is visible instead of being a surprise refund.
6. **Ascension panel**: a slider/graph of damage, mana cost and cast time vs Ascension level for the selected spell,
   and damage per mana / per second at the current level.
7. **Aura panel** for the buff rework: list active auras, who holds them, reserved mana bar segment on the portrait,
   one-click toggles, and which potion buffs are being overridden by an aura (non-stacking made visible).
8. **CC feedback**: show DR state on monster inspect ("Fear: 50 % duration, immune in 3 s").
9. **Mastery requirement and teacher price shown in the skill tooltip** for the current difficulty mode, with
   where the nearest teacher is (from the moved-trainer table).
10. **Class creation screen**: perk cards for MAW classes instead of a right-click wall of text; class/skill matrix
    (the guidebook HTML) built into the screen.
11. Fix the inconsistencies listed in §0 and §5.6 rather than porting them.

---------------------------------------------------------------------------------------------------------------

## Appendix: raw table diffs

- `Class Extra.txt`: +12 rows 53-64 (kinds 17-20).
- `Class HP SP.txt`: +12 rows; vanilla changes listed in §3.3.
- `Class Starting Stats.txt`: Dragon Might/End/Acc/Spd/Luck 11/30→14/50, +add 1→3; Dark Elf Int 11/25→14/30, +add
  1→2.
- `Character portraits.txt`: portraits 67/68 race →Dragon, 69/70 →Minotaur, 76 → Troll DK available at start, +row 77.
- `Class Skills.txt`: +12 columns; per-skill cap changes for ~40 classes (see §3.3; full list reproducible with
  a column-wise diff of the two TXT files).
- `Class Skillz.txt` (MAW only; the table the game uses): rows 0-38 differ from MAW `Class Skills.txt` in 157 cells
  (19 of them in the 12 new class columns); rows 50-53 caps for Cover, Mana Shield, Enlightenment, Retaliation;
  Armsmaster S for Black Knight/Champion.
- `Race Skills.txt` (never read by MAW): +33 race×class columns; Plate/BB Minotaur removed, racial abilities E→M,
  Meditation forced E removed for Vampire/Dark Elf/Dragon, Elf Meditation +1 removed, Troll Regeneration →M, Dragon
  Dodging/Unarmed M.
- `Race Skillz.txt` (MAW only): Human `+` on 7 misc skills; Troll Regeneration `+`; Minotaur/Dwarf Axe `E`; Dragon
  weapons/armour `0`, abilities `M`.
- `Class Starting Skills.txt`: new starting-skill slots 26 Seraphim, 28 DK, 29 Shaman, 31 Elementalist (27 and 30 are
  promotion slots, used by mercenaries only); Knight starts Plate instead of Leather, Paladin Plate, Thief gets the four
  elements and loses Stealing/Dodging/Learning, Ranger Bow free, Vampire Sword choice / Dagger free, Dragon/Thief/Rogue
  lose Learning.
- `Spells2.txt`: §2.1. `House rules.txt`: spellbook shop 1: 4→5, 5: 5→6.
- `Potion settings.txt`: flags §5.2, +31 rows (gems/crafting 1041-1069).
- `Extra Skillz.txt`: header only.
- Scripts vs mmmerge: `SpellsTweaks.lua` (Slow/Mass Distortion always apply; catalyst→Philosopher's Stone disabled),
  `ExtraQuickSpells.lua` (mastery-aware SP check), `NPCFollowersSkills.lua` (max instead of sum),
  `RemoveSkillValueLimits.lua` (limits 1023/500, engine stuns off), `MenuChooseCharacter.lua` (free selection forced).
