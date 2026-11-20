# Solo action mode: balance and special skills (talents)

How strong one character is against content built for five, in MAW at Nightmare and Beyond Madness. What a solo
ruleset should change globally, and what the special skills (talents) of the [HUD study](../../level_generation/ui/solo_action_hud_20261113/README.md)
should contain so that:

- a well-built character feels strong;
- a medium one is OK but tough;
- an under-geared one struggles.

Research and proposal of 2026-11-13. Nothing in the game or its tables changes. The measurements are scenarios in
`tests/scenarios/solo_balance/`. The model and analysis scripts are in `tests/scenarios/solo_balance/model/`.

## 0. Summary

Revised on 2026-11-13 after the user's and the coordinator's review: the first pass (kept in §3.1–3.6 and §4.1–4.7
for its method) spread a solo's skill points over 6–8 skills and gave the medium tier no buffs. A real solo focuses
and drinks. §3.7 (focused builds, measured classes) and §3.8 (buffs from consumables) replace those tiers, and §4.0
replaces the first compensation.

**How MAW sizes a fight.** Every monster is sized against **one** expected character of its own level (§0.1, §2.1):

- **Monster HP:** a B-tier monster takes 3.5 of that character's attacks at Nightmare, 5 at Beyond Madness.
- **Monster damage:** it kills that character in 5.5 hits at Nightmare, 4 at Beyond Madness.
- **Party size** enters only through Cover. A party is five such characters: ×5 damage, five bodies, a healer and
  buff auras. Standing and trading, a party member loses 18 % of its HP per average group at Nightmare and 74–87 % at
  Beyond Madness.

**What a solo has.**

- **Experience:** five times the bank's (2.2 × the level to about 80, 1.8 × from 300), so monsters built around level
  217 meet a level-400 character.
- **Skill points:** 2,975 at content 100 (core skills at 39 against MAW's expected 19) and 10,080 at 220 (core at 74).
- **Loot:** every drop, so the best of five times as many. Crafting Cubes raise item power to the wearer's own level.
- **Buffs from consumables:** potions act as a caster for the drinker, scrolls as a fixed one. Together they give
  two-thirds to three-quarters of a party's buff value. Measured on a Champion: ×1.4–1.5 damage at level 100 and
  ×2.0–2.2 at level 200 (§3.8). Alchemy's mastery comes free to a party of one, so every class can brew them.

**Focused builds against the expected character** (§3.7; class factors measured in the game, content-level gear,
potion buffs):

| Build | Damage × | Effective HP × | HP per group, Nightmare | HP per group, Beyond Madness | Group time vs party |
|---|---|---|---|---|---|
| Minotaur, two 2H axes | 1.9–3.1 | 4.8–8.2 | 6–17 % | 72–154 % | 1.6–2.6 × |
| Troll / Vampire (Regeneration) | 0.8–1.2 | 1.2–10.7 | 0–75 % | 9–1,433 % | 4–6 × |
| Monk, Death Knight | 2.1–3.3 | 0.9–4.1 | 19–97 % | 224–1,077 % | 1.5–2.4 × |
| Knight, sword and shield | 1.6–1.9 | 2.5–4.9 | 54–84 % | 248–520 % | 2.6–3.0 × |
| Seraph 2H, Shaman melee | 1.4–2.0 | 0.7–1.8 | 154–247 % | 731–1,707 % | 2.4–3.5 × |
| Arch Mage (Fire), Elementalist | 2.8–4.4 | 0.2–1.4 | 77–472 % | 278–3,549 % | 0.6–1.8 × |
| Priest of Light | 0.9–1.2 | 0.7–1.6 | 234–459 % (plus self-heals) | 1,395–3,214 % | 4.2–5.5 × |

- **High-HP and regenerating classes are fine today.** The Minotaur, Troll, Vampire, Monk, Death Knight, the Dragon
  with its breath and the Knight play Nightmare as intended. At Beyond Madness the Minotaur and Troll stand and trade;
  everyone else uses potions and tactics.
- **Low-HP classes struggle**, and not for lack of damage: Seraph, Shaman in melee, Elementalist, Priest, and the
  Arch Mage when caught. A caster kills a group as fast as a party, or faster, at a distance.
- So the solo's gap is **one body** (HP per level 2–4 against 8–12), **conditions** (§3.6), **melee area damage** (MAW
  has no cleave) and **healing that costs a recovery**. It is not damage, and buffs only partly.

**The deadliest solo problem is conditions, not damage.**

- A paralysing or petrifying hit on the only member ends the game: `Party::hasActableMember`, Party.cpp:7569-7584.
- Basilisks, gorgons, cyclopes, medusas, gargoyles, crystal walkers and cockatrices land one with a 5–25 % chance per
  hit at MAW levels.
- A medium solo is paralysed in 86–99 % of the groups that have them (§3.6).

**Recommended compensation** (§4.0): replace the party's functions; do not multiply power.

1. **Condition safety:** paralysis, stone and sleep on a party of one become a 2-second stagger; death and
   eradication specials become heavy damage.
2. **Solo potions:** healing sized to the drinker's own HP. Divine Cure heals 35 % of the drinker's maximum, capped at
   2 × the expected HP at its power. The 1-second recovery per drink stays the cost.
3. **An HP floor:** a party of one has at least 0.6 × a Knight-line character's HP for its level.
4. **Native cleave** for two-handed weapons: two more targets at 35 %.
5. Small fixes: Nightmare revival at 50 %, and Exploding bosses on a party of one.

No global damage or damage-taken multiplier: the first pass's +50 % HP / −20 % taken / +20 % damage is withdrawn.

Result: every build except the Priest stays under about 110 % of its HP per group at Nightmare. At Beyond Madness the
strong builds are at 9–115 % and the others need 3–29 drinks per group (the Priest more, before its self-heals), at
two to three times the party's time: as MAW's author says, any class can finish it with consumables and tactics.

**Special skills** (§5) are for feel, identity and the party functions above, not raw power:

- The trees give self-sustain, area damage, crowd control, mobility, condition answers and HP for low-HP classes.
- Damage multipliers are halved against the first pass (§5.1).
- Nine trees, three tiers opened by Expert, Master and Grandmaster, choice nodes and keystones with trade-offs; no
  "+2 % damage" ranks.

**Point economy** (§6): one point per mastery reached in a tree's skill, plus scarce free points (promotions, every ten
maps cleared, at most 12). The study's "one per 10 levels" gives 40–90 points to a five-times-experience solo.

**Decisions** are in §10.

### 0.1 Correction: what the HP-per-pack measure does not say (2026-11-13)

MAW's author says a solo character of any class can finish Beyond Madness. That does not contradict the numbers
above; it contradicts how they were worded. Rechecked against the code:

- **Monsters are not divided by the party size.** Each monster's HP and damage are sized against **one** character of
  its own level (`MawBalanceModel::monsterHealth`/`monsterDamage`, MawBalanceModel.cpp:836-846). The party count only
  enters the Knight's cover term (`coverMultiplier`, :706). A party is simply five such characters.
- **Monster levels follow the level bank, not the character.** Each kill banks the awarded experience divided by 5
  whatever the party size (`MawExperienceRules.cpp:170`, `MawGameState::addBankedExperience`), and the map's bolster
  is the bank's level less 4 (`mawMapBolster`, MawMonsterLevels.cpp:404; `MawRules.cpp:424-454`). So monsters track
  the level a party member would have; the solo, with the whole award, has five times that experience. The curve
  (`experienceStep`: 1000 × level, steeper from 100) turns that into 2.2 × the bank's level up to about 80,
  2.0 × at 100 and 1.8 × from 300: a level-400 solo meets monsters built around level ~217, not 80.
- **Beyond Madness fixes monster levels per map** (`madnessLevel`, MawMonsterRules.cpp:604-609), so there the solo's
  higher level is pure margin.
- **What that level buys** (the model, `gap.py`): a pimped solo has ×2.2–3.0 the damage and ×3.4–6.0 the effective HP
  of the expected character the monsters are sized for; a medium solo ×0.9–1.4 and ×1.8–2.6. *Corrected in §3.7:
  that medium spread its points over seven skills and had no buffs. A focused solo with potion buffs has ×1.6–4.4
  damage (class-dependent) and ×0.2–10 effective HP (by class HP and regeneration).* A party has ×5 damage
  and five bodies. A pimped solo therefore kills about half as fast as a party and can absorb about as much as the
  whole party, with no healer, no buff auras and one body for every condition.
- **The measure is stand-and-trade.** "HP lost per pack" assumes the whole pack hits until it dies, with no potions,
  regeneration, kiting, terrain, ranged openers, area spells or crowd control. On that measure even a party member
  loses 74–87 % per pack at Beyond Madness: the mode is built around drinking and tactics. The fair comparison is the
  ratio to the party. Pimped solo against party: ×1.7 at Nightmare (pack-normalised: 0.32–0.50 against 0.18) and
  ×1.4–2.1 at Beyond Madness (1.06–1.58 against 0.74). Medium solo: ×10–16 and ×7–13.

So: **a well-built solo can finish Beyond Madness today** with consumables and tactics, as the author says; it is about
twice the work of a party. A medium build is far behind, mostly in damage. The compensation in §4 is sized for a solo
who fights like a party, and is therefore too large. Its revised aim is to replace the party's functions (sustain, buff
auras, condition protection, area damage), not to multiply power. The open decision in §10 on the size of the Lone Hero
rule now starts from "small or none".

### 0.2 Conditions under MAW: the Magic Protection flask (2026-11-13)

MAW keeps Protection from Magic at 50 charges and Grandmaster, re-set every half second, so while it is up it blocks
Weak, poison, disease, Paralyzed, Petrified, Dead and Eradicated and never runs out (`MawSpellRules.cpp:58-61`,
`:1369-1392`; the blocked list is `conditionAffectedByProtectionFromMagic`, Party.cpp:1205). The Magic Protection
potion (item 237, 5 charges, rechargeable; `rulesets/maw/content/potion_effects.yml:122-130`) gives that aura to the
whole party while it lasts and makes the drinker immune to Unconscious. So **in MAW a solo with the flask up is not
ended by paralysis or stone**; what stays open is sleep, fear and insanity, and the flask's supply and uptime. The
condition conversion in §4.0 is needed for Standard (where Protection from Magic has charges equal to the skill and
needs Grandmaster against death) or for a MAW solo without the flask, not as a general MAW rule.

### 0.3 Healing potions: the user's lean and comparable games (2026-11-13)

The user leans to 25 % of the drinker's maximum HP rather than 35 %. For comparison: Diablo III's health potion heals
60 % instantly on a shared 30 s cooldown (about 2 % of maximum HP per second at best); Diablo IV's heals 35 % over
3 s plus a flat amount, from a few carried charges refilled by drops. MM potions are fixed amounts with no cooldown
beyond the drink's recovery, and MAW's original solo rule is a 15 s cooldown. A percentage heal with only a 1 s drink
recovery and an unlimited stock is near immortality, so the share and a cooldown go together: **25 % on MAW's 15 s
cooldown** gives about 1.7 % per second, Diablo III's level of sustain.

**Decided (user, 2026-11-13): health potions stay exactly as MAW has them.** No percentage rule.

## 1. Method

1. **MAW's balance model, ported and checked.** `game/rules/maw/MawBalanceModel.cpp` was ported to Python
   (`model/mawmodel.py`). It reproduces `devdocs/maw/data/balance_golden.csv` exactly for power, vitality, HP and
   geared fraction at levels 10–500, Nightmare and Beyond Madness. The port takes the character's level, skill level,
   gear level, gear quality, buffs and the attacker's level as separate inputs, so a solo character differs from
   MAW's expected one where it really does.
2. **Real monsters from the game.** `monster_tables.yml` runs the console command `ruleset mapmonsters`, which writes
   every map's native families as the game resolves them:
   - level, HP, AC and Attack 1 damage;
   - Nightmare (horizontal progression, party of one) and Beyond Madness;
   - in `output/solo_balance/`.

   The model's monster HP equals the game's exactly (for example Rogue L30: 434 = 434; Blue Dragon L216: 13,780 =
   13,784). Damage differs by the attack's damage class (§2.1).
3. **Real fights in the game** (§3.5). A lone `testparty` Champion goes through five stages:
   - early (level 20, rare gear; still a Knight);
   - mid (level 50, epic);
   - late (level 100, ancient);
   - endgame (200, legendary) and extreme (500, celestial).

   On native outdoor maps it attacks a C-tier native 60 times through the real attack path (`party_attack`), then
   takes hits from 3 (Nightmare) or 4 (Beyond Madness) B-tier natives in 1- and 3-second windows from full HP
   (`hp show`).
4. **The fight model** (`model/sim.py`). One character against a group of N monsters that all attack. It reports
   **HP used**: the share of maximum HP the group takes before the last one dies, with no potion or healing.
   - Below 30 %: strong.
   - 30–80 %: OK but tough.
   - Over 100 %: dies unless it heals, pulls one at a time or blocks well.

   Time units come from the code:
   - **Character:** one model "power" attack per 100 recovery ticks = 1.667 s
     (`ticksToRecoverySeconds`, GameMechanics.cpp:3991-3994, ×2.1333).
   - **Monster:** a melee monster attacks every `recovery × 2.1333 / 128` s × U(0.9, 1.2)
     (OutdoorWorldRuntime.cpp:1997-2000, GameplayActorAiSystem.cpp:550-575), which is 1.40 s at recovery 80.
5. **Tiers.** "Pimped", "medium" and "under-geared" are defined in §3.3 with their assumptions. The game measurements
   anchor the model; the encounters of §4.5 use each map's real monster numbers.

The fight model is deliberately pessimistic in two ways:

- every monster of the group attacks from the first second;
- the player never blocks, kites or heals.

It is optimistic in one: monsters do not get extra ranged attacks, and bosses have no affixes, except in §4.6.
Read the absolute percentages as a scale and the ratios between tiers and difficulties as the result.

## 2. The rules as they are

### 2.1 How MAW sizes a fight

The expected character of level L has two numbers (MawBalanceModel.cpp; BALANCE_MODEL.md §3):

- **Power:** damage per attack at recovery 100, with speed, crits, enchants and hit chance (`power`, :755-800).
- **Vitality:** HP divided by the share of damage that gets through (`vitality`, :710-725).

Monsters are sized from these (`monsterHealth`/`monsterDamage`, :836-846, with the hit tables at :297-300):

```
B-tier HP     = power(L_B)    × hitsToKillMonster[d]   × tier ratio (A/C 0.6–1.8) × boss HP (2.5–7.5)
B-tier damage = vitality(L_B) / hitsToKill[d]          × (A 0.66, C 1.5) × boss damage (1.2–1.4)
```

| d | Difficulty | hitsToKillMonster | hitsToKill | Group size (`MonsterDensity`, :303-314) |
|---|---|---|---|---|
| 3 | MAW | 2 | 7 | 1–3 |
| 5 | Hell | 3 | 6 | 1–4 |
| 6 | Nightmare | 3.5 | 5.5 | 2–4 |
| 9 | Beyond Madness | 5 | 4 | 3–6 |

- Vitality depends on the attack's class (physical, magic, or the mix; :710-725). That is why dragons, titans and
  elementals hit 1.2–1.6 × harder than the mixed number at Beyond Madness: magic gets through more.
- The party size enters only through Cover (`coverMultiplier`, :695-708). The solo and party tables written by
  `monster_tables.yml` are identical.
- DEVIATIONS row 151: the size used is the one the map was resolved with.

The expected character assumes:

- skill points spread over five skills (`skill`, :477-490);
- gear from a share of drops that grows with difficulty (`gearedFraction`, :547-569);
- 0.2 stat per level from black potions (`stat`, :571-593);
- **all party buff auras** cast at its own estimated skill: Haste, Heroism, Bless, Fate, Stone Skin, Shield, the
  resistances and Day of the Gods (`buffMult`/`buffFlat`).

Without those buffs the expected character deals ×0.64 and survives ×0.74 (port, level 100, Nightmare). That
×2.1 is the first thing a lone knight loses.

### 2.2 Difficulty: Nightmare and Beyond Madness

From COMBAT.md §4 and `MawMonsterRules::adjustMapEncounters`, MawMonsterRules.cpp:1797-1879.

| | Nightmare | Beyond Madness |
|---|---|---|
| Model index; HP / damage hits | 6; 3.5 / 5.5 | 9; 5 / 4 |
| Group size per spawn | min ≥ 2, max +1; tier mix one step harder (`Dif` +1) | min ≥ 3, max +3; `Dif` +1 |
| Monster levels | horizontal: about 2.5 × the map band (4 → 241); free: band + banks | fixed per map, 500 · (position/length)^1.2, up to 500; levels spread ±2 × the band offsets |
| Mastery thresholds (skill for E/M/G) | 4/7/10 free, 6/12/20 horizontal (`mawMasteryRequiredLevel`, MawSkillFormulas.cpp:131-141) | 10/24/40 |
| Teacher prices E/M/G | 1k/4k/20k | 15k/300k/1.25M, × (1 + masteries already held) (:143-151) |
| Extra | saving costs food; no Town Portal near enemies; dungeons left below 65 % cleared revive their dead; death below −HP | all of Nightmare; death count; loading or quitting within 5 minutes of a hit counts as a death; no mercenaries; Arena and bounties give nothing |

Real monster numbers, B tier, from `ruleset mapmonsters`:

| Map | Nightmare L / HP / damage | Beyond Madness L / HP / damage |
|---|---|---|
| Ravenshore, Mercenary | 31 / 449 / 116 | 30 / 328 / 109 |
| Garrote Gorge, Dragonette | 108 / 2,660 / 1,817 | 225 / 24,920 / 22,096 |
| Dragon Cave, Dragon Flightleader | 166 / 6,880 / 6,273 | 418 / 210,350 / 245,023 |
| Plane of Fire, Fire Elemental | 171 / 7,400 / 6,898 | 363 / 129,760 / 146,133 |
| Titans' Stronghold, Storm Titan | 190 / 9,770 / 9,699 | 437 / 238,590 / 278,876 |
| The Hive, Devil Master | 226 / 15,710 / 9,933 | 507 / 319,640 / 174,006 |
| Plane Between Planes, Ether Champion | 209 / 12,540 / 8,068 | 447 / 254,160 / 133,272 |

### 2.3 To-hit, mitigation, recovery

- **Character hits monster** (COMBAT.md §1.5): `0.75 + 0.5 · ((7.5 + attack)/(expected attack(L_mon) + 10) − 1) +
  Bless`, clamped to 0.25–1. Monster AC no longer matters for hitting.
- **Physical damage taken:** `1/(AC/(200 + L_attacker) + 1)`. **Magic:** `1/(res/(100 + L_attacker) + 1) × 1/(item
  resistance/100 + 1)`; the divisors are at MawBalanceModel.h:31-39. Mitigation is measured against the attacker's
  level, so a higher character level does not soften it by itself; only more AC and resistance do. There is a 10 %
  damage floor.
- **Monster hits character:** `1/(1 + Speed/(100 + expected stat(L_mon)) · 0.5)`. Grandmaster Dodging adds
  `1 − 1/(1 + (s+10)/200)`.
- **Recovery:**
  - Weapon base recovery: sword 80, dagger 60, mace and bow 100, staff and spear 120, axe 140. It is scaled by
    `0.75 + item level/500` and ×1.25 two-handed.
  - Hits are multiplied by base/100, so weapon speed does not change DPS.
  - Measured recoveries of the solo Champion: 0.95 s at level 20, 0.42–0.72 s from level 100. Damage per second is
    damage × hit rate / recovery.
- **Shield block (prototype, removed 2026-11-14 by the user's decision):** a raised shield took 40/55/70/85 % off
  physical hits by mastery and could not attack. A solo run has no held block.

### 2.4 Experience

- **Kill experience** (`grantKillExperience`, MawExperienceRules.cpp:90-174; `mawMemberKillExperience`, :176-193):
  - The monster's experience is split between the members who receive it.
  - It is scaled by monster HP over `monsterHealth(member level)`, where the member level is min(the member's,
    the banked level).
  - It is capped at (level + 1) × 1,000 per kill.
- **Quest and event experience:** × 5 / party size per member (:70-88). **Map completion:** the same (:292).
- **Banks:** the banked levels that drive bolster receive awards / 5, so a solo's bank grows like one party member's.
  Monster levels therefore do not follow the solo's own, higher level.
- **The curve:** `1000 · L · max(1 + (L − 100) · 0.005, 1)` per level (MawExperienceCurve.cpp:14-17), quadratic to 100
  and steeper after.

A solo therefore earns five times a member's experience. Its level, as a multiple of the content's level:

| Content level | 2 × exp | 3 × exp | 5 × exp (full solo) | Ratio |
|---|---|---|---|---|
| 20 | 28 | 34 | 44 | 2.20 |
| 50 | 71 | 86 | 111 | 2.22 |
| 100 | 138 | 164 | 202 | 2.02 |
| 200 | 263 | 307 | 371 | 1.86 |
| 300 | 389 | 451 | 543 | 1.81 |
| 500 | 641 | 740 | 886 | 1.77 |

**Standard MMMerge** is different (ExperienceRules.cpp:13-29, `bolster_formulas.txt` row `def HP`):

- Experience is shared the same way.
- MMMerge's bolster raises monster HP and damage with the **average party level**, which for a solo is its own,
  inflated level.
- So in Standard the extra levels are largely eaten by bolster, and the solo's edge comes from skill points and
  loot, not from levels.

### 2.5 The skill system in MAW

- **Points:** 5 + ⌊level/10⌋ per level (`mawLevelUpPoints`, MawSkillFormulas.cpp:202-212). Raising a skill to s
  costs s.
  - **Shared cost:** weapons, and the magic schools with the racial abilities, form sets. Raising one costs
    ⌈s/n⌉, where n is 1 + the skills of its set already at s or above (`mawSharedRaiseCost`, :153-162). A second
    weapon or school costs half.
  - At level 100 a character has 955 points (the model's five skills at 19 each). A solo at 202 has 2,965: about
    29 in seven skills, or 31 in six.
- **Mastery:** reached at a skill level (§2.2) and then bought from a trainer. MAW phases a mastery's table value in
  over the band to the next threshold (`GetGradualMasteryValue`), so there are no cliffs.
- **What skills give, per point** (SKILLS_SPELLS_ALCHEMY.md §1.2-1.4; MawCombatRules, MawSkillRules):
  - **Weapons:** attack 1/2/3/4 per point by mastery (spear 2/4/6/8). Damage +2 % per point (bow and blaster +4 %).
    Recovery 0/1/1/2 % per point for sword and bow.
  - Weapon specials:
    - **Dagger:** off-hand at Expert, crits from Master.
    - **Sword:** off-hand at Master.
    - **Axe:** +1 % crit damage per point at Grandmaster.
    - **Mace:** 15 % stun at Master, 4 s at Grandmaster.
    - **Staff:** stun; with Grandmaster Unarmed.
    - **Spear:** one-handed at Master; stacking +2 % physical damage at Grandmaster.
    - **Bow:** two arrows at Master, fire arrows at Grandmaster.
  - **Armour:** body armour scales all worn AC by 3/4/5/6 % per point and gives resistance per point (leather
    2–5 %, chain 1–4 %, plate 0–3 %). Shield: 4/6/8/10 % per point; −15 % all damage at Grandmaster.
    Unskilled armour slows attacks by 10–20 %.
  - **Others:**
    - Bodybuilding: +0.5/1/1.5/2 % HP per point.
    - Armsmaster: damage 0/1/1/1.5 per point, speed 0/0/1/1 % per point, attack +1 per point.
    - Dodging: AC per point; dodge chance at Grandmaster.
  - **Regeneration:** 5/7.5/10/10 % × √(expected HP at level skill^1.4 × own max HP) per second; Grandmaster ×(1 +
    missing²); ×2 after 20 s without loss, ×4 out of combat (MawSkillFormulas.cpp:214-237, MawSkillRules.cpp:1337-1580).
    For a solo with Regeneration at its level's skill this is **4–10 % of maximum HP per second in combat**. It halves
    the HP a medium solo loses per pack (§3.4). Only some classes learn it: Dragon M/G, Troll M/G, Vampire M/G,
    Minotaur, Monk, Death Knight (MAW `class_skills.txt`). The knight line does not.
  - **Magic:**
    - Ascension (Learning) raises damage per die ×(1 + 0.02 s) · 1.025^s and flat damage ×(1 + 0.01 s²) · 1.025^s,
      at a matching cost.
    - Buffs are auras that reserve a share of maximum mana.
    - Crowd control always lands, ×2 duration solo, with diminishing returns.
    - Heals: (base + per point × skill) × Ascension × Personality.
    - Mana Shield absorbs 25–100 % of every hit at up to 5 HP per SP.

### 2.6 What assumes four or five characters

| Assumption | Where | Effect on one character |
|---|---|---|
| Monster HP is several attacks of one member; five members attack | hit tables, §2.1 | 5 × time to kill |
| Monster damage spreads over five; healers heal | §2.1 | 5 × the damage taken |
| Buff auras from casters | expected character | ×0.64 damage, ×0.74 survival without them; a non-caster has none except scroll, pedestal and temple auras at skill 7, Master, level 40 (MawSpellRules.cpp:1249) |
| Potions heal 20 + 25 % of the **expected** HP at the potion's power | `potion_effects.yml` 222, `estimatedPool` (MawPotionRules.cpp:92-96, MawItemRules.cpp:3068) | a medium or pimped solo has 1.7–3.4 × the expected HP, so a Cure Wounds heals 5–10 % of it (§4.2 G5); drinking costs 60 ticks, 1 s |
| Any member can act | `hasActableMember` (Party.cpp:7569-7584), `shouldTriggerPartyDefeat` (GameApplication.cpp:15254-15262) | Paralyzed, Petrified, Unconscious or Dead on the only member is a defeat at once |
| Conditions are cured by party members | special attacks (GameplayCombatController.cpp:1096-1105: chance = monster level × attack level %, ≥ 100 % from level 100; save at :1014-1032: R/(R + 30) with R = Luck bonus + the matching resistance) | see §3.6 |
| Bosses: Fixator picks the lowest-HP member; Exploding halves the hit then adds half / party size to every member | COMBAT.md §3.5 | a solo always takes the full hit; Exploding gives no reduction |
| Group sizes grow at Nightmare and Beyond Madness | `adjustMapEncounters` | the solo faces 3 and 4.5 monsters on average |
| Nightmare revival below 65 % cleared | COMBAT.md §3.8 | a solo clears slowly and leaves to restock: more revived maps |
| Item breaking | Ogres, Cyclopes and others with BrkArmor/BrkWeapon | measured: the mid-stage Champion's weapon and armour broke in Ravage Roaming, and it fought the next map barehanded |
| Teacher prices × (1 + masteries held) | MawSkillFormulas.cpp:143-151 | a solo trains seven or eight skills to Grandmaster: the eighth Grandmaster costs 8 × |
| Turn-based mode | each member acts once a round | one action per round against 3–6 monsters |
| MAW's existing solo rules | Cover halves the hit (MawCombatRules.cpp:1175-1182, :2499-2547); poison ÷2 (:2885-2894); disease bonus ÷2; crowd control ×2 (MawSpellFormulas.cpp:115-126); misc skills get mastery at 1/4/7/10; travel scrolls kept (MawSpellRules.cpp:1106, 1123); 25 bags (MawItemRules.cpp:2785); Knight Charge (DEVIATIONS 48) | all help; none touches the core 5 × 5 gap |

## 3. The solo power gap in numbers

### 3.1 At parity

One character of the content's level with MAW's expected gear and buffs, against the average group (model):

| | Nightmare | Beyond Madness |
|---|---|---|
| Attacks per B monster | 3.5 (party: 0.7) | 5 (party: 1) |
| Group's time to kill | 17.5 s (party: 3.5 s) | 37.5 s (party: 7.5 s) |
| Time to die against the whole group | 2.6 s (party member: 12.8 s) | 1.2 s (party member: 6.2 s) |
| HP used per group | 455 % (party member: 18 %) | 1,842 % (party member: 74 %) |

The gap is the square of the party size: five times slower to kill, while taking five times the hits for five times
as long. "HP used" grows with N(N + 1)/2 of the group: 6 at Nightmare, about 12 at Beyond Madness.

### 3.2 What five times the experience buys

At content level 100, Nightmare, the medium solo (§3.3) is level 202 against a party member's 100. Its ratios to the
expected character:

| Change from the expected character | Damage | Effective HP |
|---|---|---|
| None | 1.00 | 1.00 |
| Without the party's buffs | 0.64 | 0.74 |
| Level 202, skill points over 7 skills (29 each), gear of level-100 loot, no buffs | 0.92 | 2.17 |
| + gear from three times the drops (one character gets them all) | 0.98 | 2.54 |
| + Haste, Heroism, Bless and Stone Skin | 1.47 | 2.77 |
| Pimped: 6 skills at 31, Ancient/Legendary-grade gear (0.9), every buff | 2.34 | 5.99 |

Extra levels mostly buy HP: about 9 HP per level and Bodybuilding. Damage comes from gear (content level), skill
level and buffs. In damage a medium solo is one party member; in HP it is two and a half.

### 3.3 The three tiers

| | Under-geared | Medium | Pimped |
|---|---|---|---|
| Experience | 2 × a member's (rushes, skips maps): 1.4 × the content's level | 5 ×: §2.4 | 5 × |
| Skill points spread over | 8 skills | 7 | 6 |
| Gear | 0.6 × the expected geared fraction at the content's level | best of 3 × the drops at the content's level: 0.43–0.87 | 0.9 (Ancient/Legendary with crafting) |
| Buffs | none | none today; Haste, Heroism, Bless, Stone Skin with G3 (§4.2) | all eight |
| Regeneration | no | class-dependent, not counted unless stated | not counted unless stated |

### 3.4 Today: HP used per average group

Melee character, no compensation, no healing. Party of five for reference.

| Content level | Under-geared | Medium | Pimped | Party member |
|---|---|---|---|---|
| **Nightmare** | | | | |
| 20 | 745 % | 215 % | 40 % | 18 % |
| 50 | 883 % | 188 % | 33 % | 18 % |
| 100 | 1,036 % | 183 % | 33 % | 18 % |
| 150 | 1,317 % | 232 % | 40 % | 18 % |
| 220 | 2,058 % | 305 % | 54 % | 18 % |
| **Beyond Madness** | | | | |
| 25 | 2,595 % | 873 % | 323 % | 87 % |
| 50 | 2,935 % | 610 % | 149 % | 87 % |
| 100 | 4,832 % | 737 % | 133 % | 87 % |
| 200 | 9,842 % | 1,095 % | 186 % | 87 % |
| 300 | 15,141 % | 1,873 % | 363 % | 87 % |
| 450 | 20,844 % | 2,164 % | 536 % | 87 % |

What the table shows:

- **The gap grows with level:** solo levels fall from 2.2 to 1.8 × the content's, and gear and enchants cap from
  level 465.
- **Regeneration** (Troll, Dragon, Vampire) changes it a lot. At Nightmare 100 the medium solo goes 183 % → 88 %; at
  Beyond Madness 200, 1,095 % → 816 %.
- **Without compensation,** only a pimped character plays Nightmare as intended. Beyond Madness is harder than for a
  party even for a pimped solo, but not impossible: see the correction in §0.1.

### 3.5 Game measurements

`anchor_<difficulty>_<stage>.yml`: a lone Champion (Knight at the early stage) from `testparty`. Its gear is of the
stage's rarity and **of its own level**, so above content-level loot when its level ratio is above 1. It has no buffs
and no Regeneration.

- **DPS:** from 60 real attacks on a C-tier native: average applied damage × hit rate / average recovery.
- **Incoming:** HP lost to the B-tier group in 1- and 3-second windows from full HP; the Immortal cheat is on during
  a 2-second approach.
- **HP used:** for the B-tier group killed one by one, `incoming/N × time per kill × N(N + 1)/2 / maximum HP`.

| Difficulty, stage | Map (B level) | Level ratio | Max HP | DPS | Time per B | Incoming/s | HP used |
|---|---|---|---|---|---|---|---|
| Nightmare, early 20 | Ravenshore (31) | 0.65 | 331 | 16 | 28.9 s | 85 | 1,476 % |
| Nightmare, mid 50 | Alvar (55) | 0.91 | 2,733 | 79 | 11.8 s | 94 | 82 % |
| Nightmare, mid 50 | Ravage Roaming (65) | 0.77 | 2,733 | 74 | 16.4 s | 136 | 164 % |
| Nightmare, mid 50 | Garrote Gorge (108) | 0.46 | 2,641 | 50 | 53.4 s | 507 | 2,049 % |
| Nightmare, late 100 | Ravage Roaming (65) | 1.54 | 7,404 | 471 | 2.6 s | 164 | 11 % |
| Nightmare, late 100 | Garrote Gorge (108) | 0.93 | 7,404 | 395 | 6.7 s | 187 | 34 % |
| Nightmare, late 100 | Plane of Fire (171) | 0.58 | 7,404 | 256 | 28.9 s | 2,341 | 1,826 % |
| Nightmare, endgame 200 | Garrote Gorge (108) | 1.85 | 13,704 | 1,070 | 2.5 s | 62 | 2 % |
| Nightmare, endgame 200 | Plane of Fire (171) | 1.17 | 13,704 | 962 | 7.7 s | 983 | 110 % |
| Nightmare, endgame 200 | Plane Between Planes (209) | 0.96 | 13,704 | 1,256 | 10.0 s | 1,470 | 214 % |
| Nightmare, extreme 500 | Plane of Fire (171) | 2.92 | 41,596 | 5,060 | 1.5 s | 255 | 2 % |
| Madness, mid 50 | Ravenshore (30) | 1.67 | 1,496 | 83 | 3.9 s | 35 | 23 % |
| Madness, late 100 | Ironsand Desert (94) | 1.06 | 4,957 | 221 | 9.3 s | 292 | 138 % |
| Madness, late 100 | Murmurwoods (150) | 0.67 | 4,957 | 173 | 43.5 s | 1,612 | 3,541 % |
| Madness, endgame 200 | Murmurwoods (150) | 1.33 | 12,939 | 1,380 | 5.5 s | 436 | 46 % |
| Madness, endgame 200 | Garrote Gorge (225) | 0.89 | 12,939 | 1,735 | 14.4 s | 4,782* | 1,327 % |
| Madness, extreme 500 | Garrote Gorge (225) | 2.22 | 45,655 | 4,630 | 5.4 s | 1,759 | 52 % |
| Madness, extreme 500 | Plane of Fire (363) | 1.38 | 45,655 | 3,317 | 39.1 s | 14,903* | 3,193 % |
| Madness, extreme 500 | Plane Between Planes (447) | 1.12 | 45,655 | 2,926 | 86.9 s | 19,659* | 9,352 % |

\* At least one window ended at 0 HP; the rate is a lower bound.

- **The incoming numbers are noisy:** the monsters' approach, flying dragons, and three samples per map. Reruns
  differed by about 2 × in single windows.
- **The thresholds agree with the model's pimped tier** at a level ratio of 1.5–2. With gear of its own level the
  character needs about 1.2–1.5 × the content's level at Nightmare and 1.5–2.2 × at Beyond Madness to lose under half
  its HP per group. Five times the experience gives 1.8–2.2 ×, so a pimped solo is viable at Nightmare today.
- **Magic damage at high Beyond Madness levels:** fire elementals at 363 and the Plane Between Planes at 447 took a
  level-500 celestial character in 2–3 seconds. Its resistances were not built.
- **Other findings from the runs:**
  - Monsters broke the mid-stage character's weapon and armour (Ravage Roaming): attack 132 → 20.
  - Indoors, `party_attack` hit nothing: 0 hits on Ogre Fortress. The outdoor maps were used instead (§9).

### 3.6 Conditions on the only member

- **Chance per landed hit:**
  - The special attack fires with (monster level × attack level) % (GameplayCombatController.cpp:1104): 61 % for a
    level-61 Basilisk, 100 % from level 100.
  - The character saves with probability R/(R + 30) (:1014-1032): R is the Luck bonus plus the mind resistance for
    Paralyze and Insane, or the earth resistance for Stone.
  - Mind and Earth immunity (:1034-1058) and MAW's status-immunity legendary affix (MawCombatRules.cpp:3066-3069)
    block it entirely.
  - Protection from Magic blocks Unconscious only (:3071-3074).
- **Expected number of landed hits per group:** HP used × hitsToKill × the character's effective-HP ratio.

| Encounter | Tier (compensated) | Resistance | Per landed hit | Hits per group | Paralysed or petrified per group |
|---|---|---|---|---|---|
| Basilisks, Nightmare L61 | under | 33 | 24 % | 24 | 100 % |
| | medium | 87 | 13 % | 14 | 86 % |
| | pimped | 252 | 6 % | 1.5 | 8 % |
| Basilisks/Gorgons, Nightmare L100 | medium | 161 | 13 % | 14 | 86 % |
| | pimped | 388 | 6 % | 1.3 | 8 % |
| Basilisks, Beyond Madness L137 | medium | 209 | 10 % | 45 | 99 % |
| | pimped | 463 | 5 % | 15 | 55 % |

**Monsters with run-ending specials** (MAW `monster_data`):

- **Paralyze:**
  - Young Basilisk, Cyclops (all three ranks), Brass Gorgon;
  - Crystal Walker/Sentry/Guardian;
  - Marble/Obsidian/Diamond Gargoyles, Revenant;
  - Medusa (MM7), Agar's Pet and Monster.
- **Stone:** Basilisk and Elder Basilisk, Bronze and Iron Gorgon, Queen and Empress Medusa, Medusas (MM6),
  Agar's Abomination (×2).
- **Dead:** Ancient Wyvern, Minotaur Lord, Blood and Supreme Titans, Assassin.
- **Eradicate:** Blaster Guys, Mega-Dragons, Terminator Unit.
- **Unconscious:** Earth Elementals, Ghost, Specter, Greater Werewolf.
- **Asleep:** Floating and Flying Eyes, Genie, Djinn.
- **Doom challenge modes:** √L · 2 % of all monsters get a random on-hit condition, these included.

In a party these are a nuisance. Solo, they decide the run regardless of HP.

### 3.7 Focused builds, measured classes (rework, 2026-11-13)

§3.3–3.4 spread skill points evenly over 6–8 skills and gave the medium tier no buffs. A real solo focuses and drinks.
This section replaces those tiers with concrete builds.

**How each build is made** (`model/builds.py`):

- **Level:** five times the bank's experience (§2.4): 111 at content level 50, 202 at 100, 405 at 220, 508 at 280,
  800 at 450.
- **Skill points:** the budget `skill_points(L)` (1,120 / 2,975 / 10,080 / 15,260 / 35,700). Alchemy is bought first
  (10 + content/4, at most 60): a party of one gets Alchemy's mastery at skill 1/4/7/10 whatever its class
  (`MawSoloMasterySkills`, MawSkillFormulas.h:57-59). The rest is spread over **three core skills**: 23, 39, 74, 94
  and 150. Armour gets 0.6 × that, other skills half. Racial skills get +3 + 10 % (Minotaur Axe, Troll Mace and
  Regeneration).
- **Gear:**
  - *content*: the best of five times the drops at the content's level (drops are rolled at the map's monster level,
    `MawRules::mapDropLevel`, MawRules.cpp:405-431);
  - *crafted*: the same enchants, with weapon and armour power raised to the solo's own level by Crafting Cubes.
    Their cap is `floor(character level / 5)`, the **wearer's** level, not the content's (CRAFTING.md §3.13).
  - *pimped*: crafted, with Ancient/Legendary-grade enchants (0.9 of the maximum).
- **Buffs:**
  - potions brewed by the solo (§3.8), at the reagent power of the content plus 2 × Alchemy;
  - plus its own auras where its class has the school.
- **Class factors measured in the game** (`classes_late.yml`, `classes_endgame.yml`): every class of MAW's four test
  parties at the late (level 100) and endgame (level 200) stages, against one durable target. The C++ rules decide
  dual wielding, Death Knight and Shaman damage, spells and HP:

| Class (test stage) | Damage / s vs Champion, L100 / L200 | HP vs Champion, L100 / L200 | Notes |
|---|---|---|---|
| Champion (sword and shield) | 1.00 (278 / 719 per s) | 1.00 (6,461 / 14,130) | |
| Minotaur Lord, one 2H axe | 1.12 / 0.63 | 1.32 / 1.09 | |
| Minotaur Lord, **two 2H axes** | **1.78 / 1.05** | 1.32 / 1.09 | the second axe: ×1.59 / ×1.66 |
| Archangel (Seraph), 1H sword + shield → 2H sword | 0.69 → 0.79 / 0.79 → 0.88 | 0.39 / 0.35 | 2H: ×1.14 / ×1.11 |
| War Troll | 0.66 / 0.62 | 1.34 / 1.42 | Regeneration G |
| Nosferatu | 1.02 / 0.69 | 0.52 / 0.48 | Regeneration G |
| Great Wyrm (claws; breath not measured) | 0.44 / 0.15 | 1.10 / 1.13 | Regeneration G |
| Master (Monk) | 1.90 / 1.29 | 1.09 / 0.83 | |
| Lich King (Death Knight) | 1.29 / 1.69 | 0.57 / 0.45 | |
| Marabou (Shaman), melee | 1.47 / 1.46 | 0.30 / 0.27 | |
| Assassin | 0.91 / 1.24 | 0.37 / 0.35 | |
| Hero (Paladin) | 0.50 / 0.41 | 0.62 / 0.68 | |
| Ranger Lord | 0.99 / 0.76 | 0.49 / 0.56 | |
| Master Archer (melee; the bow is not measured, §9) | 0.79 / 0.30 | 0.56 / 0.53 | |
| Arch Mage: Incinerate / Fireball per target / Chain Lightning | 2.39 / 0.94 / 1.18; 3.17 / 0.97 / 1.62 | 0.25 / 0.35 | per cast 1,488 / 518 / 815 at L100, 5,941 / 1,606 / 3,378 at L200; cast time from MAW's delay (90/80/100 × 1.015^Ascension / Speed) |
| Priest of Light: Light Bolt | 1.04 / 0.85 | 0.38 / 0.32 | |
| Master of Elements (melee 0.15 / 0.35) | spells assumed as the Arch Mage's | 0.18 / 0.13 | |

Spells were cast five times at a boss-strong target and read from its hit points (`cast_spell`, `actor remaining`):
`party_attack` counts a spell's projectile only when it lands within the call, so it cannot measure spells.

Precision: each `testparty apply` rolls the gear anew. Comparisons within one apply are paired: the attack rolls are
seeded per attack, so the potions, the second axe and the two-handed sword compare like for like. Comparisons between
classes and stages carry about ±20 %. The test parties' own `solo` (Champion) and `solo_caster` (Arch Mage) profiles
(HANDOFF.md §0.3, item 11) were used for the anchors in §3.5. The four five-member parties cover the other classes: a
member's damage and HP do not depend on the party's size.

**Results.** Each cell gives damage × / effective HP × against the expected character the monsters are built for,
then the group's time to kill against the party's, HP used per group standing and trading, and Divine Cure drinks per
group to stay above half HP. Gear: content level. Buffs: the build's own potions.

| Build | Nightmare 50 | Nightmare 100 | Nightmare 220 |
|---|---|---|---|
| Party of five (reference) | 5 / 5 / 1.0 / 18 % / – | same | same |
| Minotaur, two 2H axes (Axe, Armsmaster, Bodybuilding) | 3.1 / 8.0 / 1.6 / 6 % / 0 | 2.0 / 7.7 / 2.5 / 10 % / 0 | 2.1 / 5.3 / 2.4 / 17 % / 0 |
| Knight, sword and shield (Sword, Shield, Armsmaster) | 1.6 / 4.6 / 3.0 / 61 % / 0 | 1.7 / 4.9 / 2.9 / 54 % / 0 | 1.8 / 3.1 / 2.8 / 84 % / 2 |
| Seraph, 2H sword (Sword, Armsmaster, Light; own Bless, Heroism, Day of the Gods) | 1.4 / 1.8 / 3.5 / 184 % / 2 | 1.7 / 1.7 / 3.0 / 159 % / 2 | 1.7 / 1.1 / 2.8 / 235 % / 3 |
| Troll (Mace, Regeneration, Bodybuilding) | 0.9 / 8.4 / 5.5 / 0 % / 0 | 0.9 / 10.0 / 5.4 / 0 % / 0 | 0.9 / 6.9 / 5.5 / 0 % / 0 |
| Vampire (Sword, Regeneration, Dark) | 1.2 / 2.3 / 4.1 / 34 % / 0 | 0.9 / 2.4 / 5.4 / 30 % / 0 | 0.9 / 1.5 / 5.6 / 75 % / 1 |
| Dragon, claws only | 0.5 / 4.2 / 9.8 / 25 % / 0 | 0.2 / 4.1 / 25 / 51 % / 0 | 0.2 / 2.1 / 26 / 313 % / 15 |
| Arch Mage, Fire (Fire, Ascension, Meditation; own Haste) | 3.2 / 1.1 / 1.6 / 137 % / 1 | 4.3 / 1.4 / 1.2 / 77 % / 0 | 4.3 / 0.7 / 1.2 / 154 % / 2 |
| Shaman, melee (Staff, Air, Ascension; own Haste, Stone Skin) | 1.9 / 1.5 / 2.6 / 165 % / 1 | 2.0 / 1.5 / 2.5 / 154 % / 1 | 2.0 / 0.9 / 2.5 / 247 % / 3 |
| Elementalist (four elements) | 2.8 / 0.7 / 1.8 / 232 % / 1 | 3.8 / 0.5 / 1.3 / 233 % / 1 | 3.6 / 0.3 / 1.4 / 472 % / 3 |
| Priest of Light (Light, Body, Spirit, Ascension; own Bless, Heroism, Day of the Gods) | 1.2 / 1.6 / 4.2 / 234 % / 2 | 1.1 / 1.5 / 4.7 / 283 % / 3 | 1.1 / 0.9 / 4.7 / 459 % / 6 |
| Monk (Unarmed, Dodging, Armsmaster) | 3.0 / 4.1 / 1.7 / 19 % / 0 | 2.2 / 3.0 / 2.2 / 40 % / 0 | 2.3 / 1.5 / 2.2 / 97 % / 2 |
| Death Knight (Sword, Dark, Armsmaster) | 2.2 / 2.5 / 2.3 / 47 % / 0 | 2.9 / 2.2 / 1.7 / 42 % / 0 | 3.0 / 1.4 / 1.7 / 74 % / 1 |

| Build | Beyond Madness 100 | Beyond Madness 280 | Beyond Madness 450 |
|---|---|---|---|
| Party of five (reference) | 5 / 5 / 1.0 / 87 % / – | same | same |
| Minotaur, two 2H axes | 2.4 / 8.2 / 2.1 / 72 % / 2 | 1.9 / 5.4 / 2.6 / 142 % / 10 | 1.9 / 4.8 / 2.6 / 154 % / 20 |
| Knight, sword and shield | 1.9 / 4.5 / 2.6 / 248 % / 8 | 1.6 / 3.0 / 3.0 / 436 % / 23 | 1.6 / 2.5 / 3.0 / 520 % / 47 |
| Seraph, 2H sword | 1.9 / 1.6 / 2.7 / 731 % / 10 | 1.6 / 1.1 / 3.0 / 1,204 % / 25 | 1.7 / 0.9 / 3.0 / 1,419 % / 49 |
| Troll | 1.0 / 10.7 / 5.0 / 9 % / 0 | 0.8 / 7.0 / 6.4 / 57 % / 1 | 0.8 / 6.3 / 6.2 / 100 % / 12 |
| Vampire | 0.9 / 2.2 / 5.3 / 569 % / 10 | 0.8 / 1.5 / 6.4 / 1,065 % / 30 | 0.8 / 1.2 / 6.3 / 1,433 % / 67 |
| Arch Mage, Fire | 4.4 / 1.4 / 0.6 / 278 % / 3 | 3.7 / 0.6 / 0.8 / 764 % / 15 | 3.8 / 0.4 / 0.7 / 1,147 % / 38 |
| Shaman, melee | 2.0 / 1.4 / 2.4 / 769 % / 8 | 1.7 / 0.9 / 2.9 / 1,377 % / 22 | 1.7 / 0.7 / 2.9 / 1,707 % / 45 |
| Elementalist | 4.0 / 0.5 / 0.7 / 833 % / 4 | 3.1 / 0.2 / 0.9 / 2,384 % / 17 | 3.1 / 0.2 / 0.9 / 3,549 % / 42 |
| Priest of Light | 1.1 / 1.4 / 4.5 / 1,395 % / 17 | 0.9 / 0.9 / 5.5 / 2,714 % / 49 | 0.9 / 0.7 / 5.4 / 3,214 % / 95 |
| Monk | 2.5 / 3.1 / 2.0 / 224 % / 6 | 2.1 / 1.3 / 2.4 / 683 % / 32 | 2.1 / 0.9 / 2.4 / 1,077 % / 85 |
| Death Knight | 3.3 / 2.0 / 1.5 / 269 % / 4 | 2.8 / 1.4 / 1.8 / 480 % / 12 | 2.8 / 1.1 / 1.8 / 573 % / 24 |

The Dragon's breath and the Archer's bow were not measured (the runner's attack is always in melee reach); their rows
undersell them. Beyond Madness rows for them are left out.

**Gear and crafting.** Crafting Cubes are worth as much as a tier:

| | Content gear | Crafted (item power at own level) | Pimped |
|---|---|---|---|
| Minotaur, Nightmare 100 | 2.0 / 7.7, 10 % | 2.8 / 8.7, 5 % | 3.3 / 12.4, 1 % |
| Knight, Nightmare 220 | 1.8 / 3.1, 84 % | 2.5 / 3.9, 48 % | 2.7 / 4.8, 35 % |
| Minotaur, Beyond Madness 280 | 1.9 / 5.4, 142 % | 2.6 / 6.9, 71 % | 2.9 / 8.0, 52 % |
| Knight, Beyond Madness 280 | 1.6 / 3.0, 436 % | 2.2 / 3.9, 245 % | 2.4 / 4.6, 194 % |

**What it says:**

- **A focused solo deals 1.6–4.4 × the expected character's damage,** not 0.9–1.4 ×. Focus (core skills at 39 instead
  of 29 at content 100), potions (§3.8) and five times the drops each count. A party deals 5 ×, so a solo's groups
  take 1.2–3 × the party's time, except for weak-damage builds (Troll 5–6 ×, Priest 4.5 ×, Dragon claws).
- **Effective HP is where classes split.** HP per level ranges from 2–4 (Arch Mage, Elementalist, Priest, Seraph's
  first tier) to 8–12 (Champion, Minotaur Lord, War Troll, Great Wyrm under MAW's class table). Measured HP against
  the Champion runs from 0.13 (Master of Elements) to 1.42 (War Troll).
- **Fine today at Nightmare** (under half HP per group, no potions): Minotaur, Troll, Vampire, Monk, Death Knight, the
  Dragon (when it uses the breath) and the Knight. The Arch Mage is fine at a distance: it kills a group faster than a
  party, but it must not be hit.
- **Struggling at Nightmare:** low-HP melee (Seraph, Shaman in melee), the Elementalist and the Priest. They need 2–6
  drinks per group or kiting.
- **At Beyond Madness** only the high-HP or regenerating builds stand and trade (Minotaur, Troll, and the Knight when
  crafted). Everything else needs potions in the tens per group or real tactics: pulling, kiting, corners, crowd
  control. That is consistent with MAW's author: any class can finish it with consumables and tactics, at two to three
  times the party's time and a large potion budget.

### 3.8 Buffs from consumables

Every buff a party's caster keeps up has a consumable form. MAW makes potions act as a caster and scrolls as a fixed
one.

| Source | Buffs | Strength | Duration | From |
|---|---|---|---|---|
| Haste (228), Heroism (229), Bless (230), Stone Skin (234) potions | one aura each | a Master caster with s = 50(f − 1), level 0.5·P·f, f = 0.75 + 0.75·min(P, 200)/200 (CLASSES_SPELLS_SPEC.md §3.6, §7.4) | 6 game hours per drink, +6 minutes per point of the best Grandmaster Alchemy (12 h at 60); 5 drinks per bottle | brewed (tertiary: Expert Alchemy) |
| **Champion's Potion (245)** | Haste + Heroism + Bless | as above | as above; Endless Potion recharges | brewed (white: Master) |
| **Paladin's Potion (251)** | Shield + Stone Skin + Preservation | as above | as above | brewed (white) |
| Protection (231) | Shield + Preservation | as above, power ≥ 20 | as above | brewed |
| Elemental (249) and Self Resistance (250) | the six resistance auras, and +10–20 % of a stat each | as above | as above | brewed (white) |
| **Divine Blessing (257)** | Day of the Gods: +min(10 + s/7, 20) % all stats, s = 70(f − 1) | 15 % at power ≥ 200 | as above | brewed (black, Master) |
| Divine Resistance (263) | Day of Protection | as above | as above | brewed (black, GM) |
| Magic Protection (237) | Protection from Magic; immune to Unconscious | Power 4, Skill 10 | as above | brewed |
| Pure Power/Wisdom/Resilience (252–254), Pure Resistances (261, 262), Transcendence (259) | **permanent**: +20 per stat per 50 power (+200 at 500), +30 resistance per 50 power, skill points 5k² + 15k | best step only | permanent | brewed (black) |
| Power, Wisdom, Resilience Boost (240–242) | +10 + P temporary stats (OpenYAMM gives what MAW's tooltip promises, DEVIATIONS) | | timed | brewed |
| Buff scrolls: Bless 345 (20 gold), Fire/Air/... Resistance (30), Fate 346 (30), Haste 304 (50), Stone Skin 337 (50), Shield 316 (75), Preservation 349 (75), Heroism 350 (100), Protection from Magic 374 (200), Day of the Gods 382 (350), Pain Reflection 394 (400), Day of Protection 384 (500), Hour of Power 385 (600) | the spell's aura | fixed caster: skill 7, Master, level 40 (MawSpellRules.cpp:1249); unchanged by MAW's port | until the party enters a different outdoor map (they survive dungeons) | shops (item values; shop prices add the merchant markup), drops |

Notes on the table:

- **Potions and auras never add up.** Per buff, the stronger of the party aura and the drinker's potion counts
  (§3.6 of the spec). For a solo the potion *is* the aura.
- **Potion power.** A potion's power is its reagents' power plus Alchemy: with Grandmaster, 2 per point.
  - Reagents dropped by monsters have item level about half the banked level of the other continents (AL:683-684).
    Their power is `base(1 + B/80) + 0.75 B`, base 1–45 by tier, at most 255.
  - With Alchemy at 10 + content/4 the solo brews about power 100 at content level 50, 156 at 100, 270–310 at 220–280
    and 375 at 450. Black potions need Master, the last two GM.
- **What the potions give.** In the model (Knight, content gear):

| Content level | No buffs | Scrolls | Potions | Party's casters |
|---|---|---|---|---|
| Nightmare 50 | 1.31 / 3.79 | 1.87 / 4.81 | 1.64 / 4.55 | 2.19 / 5.58 |
| Nightmare 100 | 1.29 / 4.01 | 1.87 / 4.92 | 1.73 / 4.90 | 2.45 / 6.35 |
| Nightmare 220 | 1.20 / 2.56 | 1.79 / 3.05 | 1.76 / 3.10 | 2.55 / 4.06 |
| Beyond Madness 280 | 1.04 / 2.48 | 1.58 / 2.94 | 1.63 / 3.04 | 2.28 / 3.87 |
| Beyond Madness 450 | 0.96 / 2.10 | 1.49 / 2.45 | 1.63 / 2.55 | 2.18 / 2.86 |

  (damage × / effective HP × against the expected character.)
- **Measured in the game** (paired runs on the same Champion and target, `classes_*.yml`):
  - Champion's Potion: ×1.38 damage per second at level 100 (power 150), ×2.04 at level 200 (power 300).
  - Plus Paladin's Potion and Divine Blessing: ×1.53 / ×2.16, HP +5.5 % / +7.2 %. At level 200 most of it is Bless:
    the hit rate against a level-222 target went 0.52 → 0.80.
  - The Heroism and Bless scrolls: ×1.83 at level 100, and nothing at level 200. Their fixed level 40 cannot keep up.

So: **consumables give a solo two-thirds to three-quarters of the party's buffs** in the model and in the game. Scrolls
are cheap and as good as potions up to about level 100; potions take over after that. Both last long enough to be
always on (a 5-drink bottle covers 30–60 game hours of one buff). The solo's real gap is therefore not buffs. It is:

- **one body:** classes with 2–4 HP per level;
- **conditions** (§3.6);
- **area damage** for melee: MAW has no cleave;
- **healing** that costs a recovery each time: Divine Cure heals 35 % of the *expected* HP at its power, which is
  10–25 % of a high-HP solo.

## 4. The compensation model

### 4.0 Revised compensation (2026-11-13): replace the party's functions

§3.7–3.8 show that a focused solo with brewed buffs already has 1.6–4.4 × the expected character's damage. The party's
×5 damage makes groups take 1.2–3 × as long, which is the "twice the work" MAW's author describes. What a solo really
lacks is what four companions provide: more bodies, a healer, someone to cure a paralysed member, and area damage for
melee. The compensation replaces those and nothing else.

| Rule | Proposal | Replaces |
|---|---|---|
| R1 Condition safety (was G4) | on a party of one, monster-applied Paralyzed, Petrified and Asleep become a 2-second stagger, then 20 s immune to that condition. Dead and Eradicated specials deal 50 % of current HP instead. Insane and Afraid last at most 6 s. Boss on-hit conditions are converted too | the cleric who cures, and the four members who keep the party "able to act" |
| R2 Solo potions (was G5): **withdrawn, the user's decision 2026-11-13: health potions stay as MAW has them** | ~~for a party of one, HP and SP potions heal from the drinker's own maximum: Cure Wounds 20 + 25 %, Divine Cure 50 + 35 %, at most 2 × the expected pool at the potion's power. Drinking keeps its 60-tick (1 s) recovery and gets no extra cooldown~~ | the healer |
| R3 HP floor | a party of one has at least 0.6 × the HP a Knight-line character would have at its level (HP per level at least about 6 in MAW's class table) | the other bodies, for classes with 2–4 HP per level |
| R4 Native cleave | two-handed swords, axes, maces and staves strike up to two more monsters in a ±50° arc for 35 % (the README's proposal, at a lower share). Special skills raise it | the party's spread damage, for melee; casters already have area spells |
| R5 Small fixes (G8, G9) | Nightmare revival at 50 % cleared; Exploding bosses deal only the halved hit to a party of one | rules written for five |
| — | no global HP, damage-taken or damage multiplier (G1, G2 withdrawn); no scroll-level rule (G3 withdrawn: potions brewed by every class already give 65–75 % of the party's buffs, scrolls cover the early game) | |

Effect on the focused builds (`model/revised.py`). Each cell: HP used per group today → with R2–R4, then group time
against the party's and Divine Cure drinks per group with R2.

| Build | Nightmare 50 | Nightmare 100 | Nightmare 220 |
|---|---|---|---|
| Minotaur, two 2H axes | 6 → 5 %, 1.1 ×, 0 | 10 → 9 %, 1.7 ×, 0 | 17 → 15 %, 1.7 ×, 0 |
| Knight, sword and shield | 61 → 61 %, 3.0 ×, 0 | 54 → 54 %, 2.9 ×, 0 | 84 → 84 %, 2.8 ×, 1 |
| Seraph, 2H sword | 184 → 93 %, 2.5 ×, 1 | 159 → 73 %, 2.1 ×, 1 | 235 → 108 %, 2.0 ×, 2 |
| Troll | 0 → 0 %, 3.8 ×, 0 | 0 → 0 %, 3.8 ×, 0 | 0 → 0 %, 3.8 ×, 0 |
| Vampire | 34 → 23 %, 4.1 ×, 0 | 30 → 17 %, 5.4 ×, 0 | 75 → 43 %, 5.6 ×, 0 |
| Arch Mage, Fire | 137 → 59 %, 1.6 ×, 0 | 77 → 45 %, 1.2 ×, 0 | 154 → 90 %, 1.2 ×, 1 |
| Shaman, melee | 165 → 81 %, 2.6 ×, 1 | 154 → 69 %, 2.5 ×, 1 | 247 → 111 %, 2.5 ×, 2 |
| Elementalist | 232 → 68 %, 1.8 ×, 1 | 233 → 50 %, 1.3 ×, 0 | 472 → 102 %, 1.4 ×, 1 |
| Priest of Light | 234 → 146 %, 4.2 ×, 3 | 283 → 151 %, 4.7 ×, 3 | 459 → 245 %, 4.7 ×, 6 |
| Monk | 19 → 19 %, 1.7 ×, 0 | 40 → 40 %, 2.2 ×, 0 | 97 → 97 %, 2.2 ×, 1 |
| Death Knight | 47 → 42 %, 2.3 ×, 0 | 42 → 29 %, 1.7 ×, 0 | 74 → 51 %, 1.7 ×, 0 |

| Build | Beyond Madness 100 | Beyond Madness 280 | Beyond Madness 450 |
|---|---|---|---|
| Minotaur, two 2H axes | 72 → 54 %, 1.3 ×, 0 | 142 → 106 %, 1.6 ×, 2 | 154 → 115 %, 1.6 ×, 2 |
| Knight, sword and shield | 248 → 248 %, 2.6 ×, 6 | 436 → 436 %, 3.0 ×, 11 | 520 → 520 %, 3.0 ×, 13 |
| Seraph, 2H sword | 731 → 301 %, 1.7 ×, 7 | 1,204 → 497 %, 1.9 ×, 13 | 1,419 → 586 %, 1.9 ×, 15 |
| Troll | 9 → 9 %, 3.1 ×, 0 | 57 → 52 %, 4.0 ×, 0 | 100 → 86 %, 3.9 ×, 1 |
| Vampire | 569 → 412 %, 5.3 ×, 10 | 1,065 → 780 %, 6.4 ×, 21 | 1,433 → 1,078 %, 6.3 ×, 29 |
| Arch Mage, Fire | 278 → 162 %, 0.6 ×, 3 | 764 → 446 %, 0.8 ×, 11 | 1,147 → 669 %, 0.7 ×, 18 |
| Shaman, melee | 769 → 346 %, 2.4 ×, 8 | 1,377 → 620 %, 2.9 ×, 16 | 1,707 → 768 %, 2.9 ×, 21 |
| Elementalist | 833 → 181 %, 0.7 ×, 4 | 2,384 → 516 %, 0.9 ×, 13 | 3,549 → 769 %, 0.9 ×, 21 |
| Priest of Light | 1,395 → 744 %, 4.5 ×, 20 | 2,714 → 1,448 %, 5.5 ×, 40 | 3,214 → 1,714 %, 5.4 ×, 48 |
| Monk | 224 → 224 %, 2.0 ×, 5 | 683 → 683 %, 2.4 ×, 18 | 1,077 → 1,077 %, 2.4 ×, 29 |
| Death Knight | 269 → 195 %, 1.5 ×, 4 | 480 → 349 %, 1.8 ×, 9 | 573 → 416 %, 1.8 ×, 10 |

What is not in these numbers, and moves them in the solo's favour:

- **The Priest's self-heals.** At content 100 a Greater Heal (Body Grandmaster, Ascension 34) heals about
  `(40·(1 + 0.01·34²) + 10·(1 + 0.02·34)·34) · 1.015^34 · (1 + Personality/1,606)` ≈ 2,100 HP for about 250 SP. That
  is about 40 % of the Priest's HP every 2.3 s, while it does not attack: a healer-hybrid trades damage for an
  unending fight.
- **Mana Shield for casters:** 25–100 % of every hit paid with SP at up to 5 HP per SP. Not counted.
- **Kiting, corners, pulling single monsters and crowd control:** the stand-and-trade measure assumes the whole group
  hits from the first second. A single pulled monster costs a sixth of a Nightmare group's HP use.
- **Crafting** (§3.7): Crafting Cubes are worth a tier. A crafted Knight at Beyond Madness 280 loses 245 % instead of
  436 %.

And against the solo:

- conditions without R1;
- item breaking (Ogres, Cyclopes);
- bosses (§4.6).

**Targets** (§4.1) still apply, read per build rather than per tier:

- A well-built solo of a sturdy class is strong.
- A well-built solo of a fragile class is OK but tough: it needs potions and tactics.
- An under-geared or unfocused solo struggles, as in §3.4.

§4.1–4.7 below are the first pass with generic tiers and a large global multiplier. They are kept for the method and
for the under-geared tier; their compensation numbers are superseded.

### 4.1 Targets

| HP used per average group | Nightmare | Beyond Madness |
|---|---|---|
| Pimped ("feels strong") | ≤ 25 % | ≤ 60 % |
| Medium ("OK but tough") | 25–80 % | 80–200 % (the party itself is at 87 %) |
| Under-geared ("struggles") | 150–400 %: pull singles, block, drink | above 400 %: not viable, as for an under-geared party |

Required factors on (damage × effective HP), from §3.4:

- Nightmare: medium ×3–5, pimped ×1.3–2.2.
- Beyond Madness: medium ×5–18, pimped ×2.5–10.

Both grow with level. The split:

- a **flat global rule** of about ×2.25, which also lifts the under-geared;
- **special skills that scale with skill level**, about ×1.4 at Expert and ×2–3 fully built, which covers the growth
  with level.

### 4.2 Global rules for a party of one ("Lone Hero")

These apply in solo action mode only, on MAW and on Standard, from a rules hook (`CombatRules`/`SkillRules`, with
MAW's numbers in the ruleset).

| Rule | Proposal | Why |
|---|---|---|
| G1 Lone vitality | maximum HP ×1.5; damage taken ×0.8 (after mitigation and the 10 % floor, before Mana Shield) | effective HP ×1.875: half of what five pools of HP give. Lone Wolf in Divinity: Original Sin 2 gives +30 % Vitality and doubled points ([gamepressure](https://www.gamepressure.com/originalsinii/regular/zf91e0)) |
| G2 Lone offence | damage dealt ×1.2 (weapons, spells, breath) | together with G1, ×2.25 on (damage × effective HP) |
| G3 Self-sufficient buffs | (a) a solo caster's auras reserve half; (b) scroll, pedestal and temple auras on a solo use the character's level and MAW's estimated skill for it, not skill 7, Master, level 40 (MawSpellRules.cpp:1249) | MAW's monsters assume the buffs; this gives a lone knight Haste, Heroism, Bless and Stone Skin for gold: ×1.5 damage, ×1.1 effective HP for the medium tier |
| G4 Condition safety | on the only member, monster-applied Paralyzed, Petrified and Asleep become a 2-second stagger (cannot act, takes hits), then 20 s immune to that condition; Dead and Eradicated from a special attack deal 50 % of current HP instead; Insane and Afraid last at most 6 s. Bosses' on-hit conditions, which bypass immunities, follow the same conversion | §3.6: otherwise the run ends on a die roll |
| G5 Solo potions | the pool of HP and SP potions is min(the drinker's maximum, 2 × the expected pool at the potion's power); a 10 s shared potion cooldown in solo (MAW's own solo potion keys had 15 s, GAPS L7.6) | today a Cure Wounds heals 5–10 % of a medium or pimped solo; with G5, 25 % every 10 s ≈ 2.5 %/s, a quarter to half of what Regeneration gives a solo Troll |
| G6 Groups | unchanged at Nightmare; at Beyond Madness optionally Road to Insanity's (3–5) | not used in the numbers below; it would halve Beyond Madness's HP used (N(N + 1)/2: 12.4 → 9) |
| G7 Experience | unchanged: five times a member's, kill cap (level + 1) × 1,000 | already the solo's main compensation |
| G8 Nightmare revival | 50 % cleared instead of 65 % for a party of one | a solo clears slower and leaves to restock |
| G9 Boss affixes | Exploding: a party of one takes only the halved hit; Fixator unchanged | Exploding's split is meant for five |

In Standard MMMerge, G1–G2 and G4–G5 apply as they are. G3 is moot: Standard buffs are timed casts. MMMerge's bolster
follows the solo's own level, so Standard needs no more than this.

### 4.3 What the special skills provide

The fight model's melee build (§5.2, Two-Handed and Armour trees) at each tier:

| Tier reached | Picks used in the model | Effect |
|---|---|---|
| Expert | Cleave (2 more targets at 40 % + 0.4 %/skill point, max 80 %), Brace (−5 % − 0.2 %/point damage taken, max −25 %) | ≈ ×1.4–1.6 against groups |
| Master | Reaving (2 % + 0.04 %/point of damage dealt as HP, max 6 %), Iron Hide (+10 % + 0.2 %/point HP, max +30 %) | ≈ ×1.5 more |
| Grandmaster | Executioner (×2 below 25 % HP, −10 % above 75 %), Last Stand (−50 % taken for 6 s, 60 s cooldown, assumed up for every other group) | ≈ ×1.3–2 more |

How the tiers use them:

- **Under-geared:** Expert only.
- **Medium:** Expert and Master.
- **Pimped:** all three, as the character's skill opens them.

The skill at Expert/Master/Grandmaster is 6/12/20 at Nightmare (horizontal) and 10/24/40 at Beyond Madness.
Effects grow with the skill: Cleave's share is 44 % at skill 10, 60 % at 50 and 80 % from 100.

### 4.4 Power curves

HP used per average group, melee: today → with the global rules → with global rules and special skills.

| Content level | Under-geared | Medium | Pimped | Party member |
|---|---|---|---|---|
| **Nightmare** | | | | |
| 20 | 745 → 331 → 232 % | 215 → 65 → 45 % | 40 → 18 → 12 % | 18 % |
| 50 | 883 → 393 → 268 % | 188 → 54 → 29 % | 33 → 15 → 7 % | 18 % |
| 100 | 1,036 → 460 → 302 % | 183 → 50 → 24 % | 33 → 14 → 3 % | 18 % |
| 150 | 1,317 → 586 → 371 % | 232 → 59 → 27 % | 40 → 18 → 3 % | 18 % |
| 220 | 2,058 → 914 → 550 % | 305 → 74 → 28 % | 54 → 24 → 3 % | 18 % |
| **Beyond Madness** | | | | |
| 25 | 2,595 → 1,155 → 1,155 % | 873 → 356 → 216 % | 323 → 144 → 87 % | 87 % |
| 50 | 2,935 → 1,304 → 789 % | 610 → 204 → 120 % | 149 → 66 → 38 % | 87 % |
| 100 | 4,832 → 2,148 → 1,244 % | 737 → 198 → 90 % | 133 → 59 → 24 % | 87 % |
| 200 | 9,842 → 4,376 → 2,352 % | 1,095 → 265 → 99 % | 186 → 83 → 14 % | 87 % |
| 300 | 15,141 → 6,730 → 3,356 % | 1,873 → 455 → 140 % | 363 → 162 → 19 % | 87 % |
| 450 | 20,844 → 9,261 → 4,125 % | 2,164 → 530 → 108 % | 536 → 239 → 13 % | 87 % |

The same as a chart. Logarithmic scale; U under-geared, M medium, P pimped, 5 the party member.

```
NIGHTMARE, today                                NIGHTMARE, compensated
 1000% | U     U     U     U                     1000% |
       |                         U                     |                   U     U
       |  M     M     M     M     M                    | U     U     U
  100% |                            <- dies       100% |                              <- dies
       |   P     P     P     P     P                   |  M
       |    5     5     5     5     5                  |    5   M 5   M 5   M 5   M 5
   10% |                                          10% |   P
       |                                               |         P     P     P
       |                                               |                           P
    1% +------------------------------              1% +------------------------------
          20    50   100   150   220                      20    50   100   150   220

BEYOND MADNESS, today                           BEYOND MADNESS, compensated
10000% |                   U     U     U        10000% |
       |             U                                 |                         U     U
       | U     U                  M     M              |                   U
 1000% |  M           M     M                     1000% | U     U     U
       |   P    M                  P     P             |
       |         P           P                         |  M
  100% |    5     5    P5     5     5     5 <- dies 100% |   P5   M 5   M 5   M 5   M 5   M 5 <- dies
       |                                               |         P
       |                                               |               P           P
   10% |                                          10% |                     P           P
    1% +------------------------------------        1% +------------------------------------
          25    50   100   200   300   450                25    50   100   200   300   450
```

Notes on the curves:

- **Nightmare pimped falls to about 3 % from content level 100:** five times the experience, every buff and 0.9 gear
  make it a power fantasy; the special skills add little there (5.8 % without the Grandmaster tier). See §10, item 1.
- **Beyond Madness medium stays near the party's line (90–216 %):** tough, as intended for the hardest mode, and
  playable with G5 potions, blocking and pulling.
- **Under-geared Beyond Madness stays unplayable;** under-geared Nightmare is hard (230–550 %).

### 4.5 Encounters

Each map's real B-tier family from `ruleset mapmonsters`, with its own HP, Attack 1 damage and recovery. The
groups are 3 (Nightmare) and 4.5 (Beyond Madness). Each cell gives **time to kill the group / time to die against the
whole group / HP used**, today → compensated. Melee build as in §4.3.

**Nightmare (horizontal):**

| Encounter (B level) | Under-geared | Medium | Pimped |
|---|---|---|---|
| Goblinwatch, Goblin Shamans (6) | 19 s / 3.2 s / 399 % → 16 s / 6.0 s / 177 % | 15 s / 5.0 s / 202 % → 12 s / 9.3 s / 84 % | 10 s / 10.2 s / 63 % → 8 s / 19.1 s / 28 % |
| Shadow Guild Hideout, Ruffians (26) | 27 / 2.7 / 683 % → 14 / 5.3 / 212 % | 18 / 6.7 / 178 % → 7 / 14.4 / 36 % | 8 / 17.0 / 33 % → 4 / 34.4 / 10 % |
| Ravenshore, Mercenaries (31) | 27 / 2.4 / 759 % → 14 / 4.8 / 234 % | 18 / 6.1 / 191 % → 6 / 14.9 / 32 % | 8 / 15.7 / 34 % → 4 / 35.8 / 7 % |
| Dragoons' Caverns, Expert Swordsmen (49) | 28 / 2.4 / 768 % → 14 / 4.8 / 233 % | 17 / 6.8 / 165 % → 6 / 17.0 / 26 % | 7 / 17.2 / 29 % → 4 / 40.1 / 6 % |
| Necromancers' Guild, Necromancers (85) | 29 / 1.7 / 1,172 % → 15 / 3.4 / 345 % | 18 / 5.3 / 219 % → 6 / 14.0 / 31 % | 7 / 12.9 / 39 % → 3 / 31.2 / 5 % |
| Garrote Gorge, Dragonettes (108) | 31 / 1.4 / 1,519 % → 15 / 2.8 / 440 % | 18 / 4.6 / 263 % → 6 / 12.2 / 35 % | 7 / 10.6 / 47 % → 3 / 26.3 / 5 % |
| Dragon Cave, Dragon Flightleaders (166) | 36 / 1.0 / 2,281 % → 17 / 2.2 / 634 % | 19 / 3.3 / 394 % → 5 / 9.2 / 45 % | 7 / 7.3 / 68 % → 3 / 19.0 / 7 % |
| Plane of Fire, Fire Elementals (171) | 36 / 1.1 / 2,210 % → 17 / 2.3 / 612 % | 19 / 3.5 / 373 % → 5 / 9.7 / 42 % | 7 / 7.7 / 65 % → 3 / 20.1 / 6 % |
| Titans' Stronghold, Storm Titans (190) | 38 / 1.0 / 2,580 % → 18 / 2.1 / 705 % | 20 / 3.2 / 413 % → 5 / 9.2 / 44 % | 7 / 7.0 / 71 % → 3 / 18.7 / 6 % |
| Colony Zod, Devil Warriors (204) | 39 / 1.1 / 2,458 % → 18 / 2.3 / 665 % | 20 / 3.5 / 381 % → 5 / 10.2 / 38 % | 8 / 7.6 / 66 % → 3 / 20.6 / 5 % |
| The Hive, Devil Masters (226) | 41 / 1.0 / 2,701 % → 19 / 2.2 / 719 % | 21 / 3.5 / 395 % → 5 / 10.3 / 37 % | 8 / 7.4 / 70 % → 3 / 20.4 / 4 % |
| Dragon Caves, Blue Dragons (216) | 40 / 0.8 / 3,313 % → 19 / 1.7 / 888 % | 20 / 2.7 / 497 % → 5 / 8.0 / 50 % | 8 / 5.9 / 87 % → 3 / 16.0 / 7 % |

**Beyond Madness:**

| Encounter (B level) | Under-geared | Medium | Pimped |
|---|---|---|---|
| Goblinwatch (25) | 45 s / 1.5 s / 2,129 % → 37 / 2.8 / 947 % | 32 / 3.2 / 715 % → 14 / 6.4 / 178 % | 21 / 5.6 / 264 % → 10 / 11.2 / 71 % |
| Shadow Guild Hideout (47) | 47 / 1.3 / 2,528 % → 22 / 2.7 / 681 % | 27 / 3.6 / 544 % → 10 / 7.6 / 109 % | 14 / 7.1 / 141 % → 6 / 14.6 / 36 % |
| Dragoons' Caverns (133) | 79 / 0.9 / 6,201 % → 36 / 1.9 / 1,558 % | 40 / 3.4 / 826 % → 11 / 9.4 / 91 % | 16 / 7.8 / 144 % → 7 / 19.6 / 23 % |
| Necromancers' Guild (262) | 107 / 0.4 / ≫ → 46 / 1.0 / 3,942 % | 49 / 1.6 / 2,130 % → 12 / 4.9 / 178 % | 18 / 3.3 / 400 % → 7 / 9.2 / 30 % |
| Garrote Gorge (225) | 99 / 0.4 / ≫ → 43 / 0.9 / 3,852 % | 44 / 1.7 / 1,878 % → 11 / 4.9 / 168 % | 16 / 3.5 / 341 % → 6 / 9.5 / 29 % |
| Dragon Cave (418) | 132 / 0.2 / ≫ → 53 / 0.5 / ≫ | 58 / 0.9 / 4,364 % → 13 / 3.2 / 281 % | 22 / 1.5 / 1,039 % → 8 / 4.9 / 58 % |
| Plane of Fire (363) | 125 / 0.3 / ≫ → 51 / 0.6 / ≫ | 57 / 1.1 / 3,848 % → 13 / 3.5 / 275 % | 22 / 1.8 / 834 % → 7 / 5.7 / 53 % |
| Titans' Stronghold (437) | 134 / 0.3 / ≫ → 53 / 0.6 / ≫ | 58 / 1.0 / 4,045 % → 13 / 3.5 / 247 % | 22 / 1.6 / 985 % → 8 / 5.2 / 52 % |
| Colony Zod (477) | 136 / 0.4 / ≫ → 54 / 0.9 / ≫ | 57 / 1.7 / 2,472 % → 13 / 5.8 / 129 % | 22 / 2.5 / 634 % → 7 / 8.0 / 19 % |
| The Hive (507) | 135 / 0.4 / ≫ → 53 / 0.9 / ≫ | 56 / 1.7 / 2,390 % → 13 / 5.8 / 123 % | 22 / 2.4 / 632 % → 7 / 7.9 / 19 % |
| Dragon Caves (466) | 137 / 0.2 / ≫ → 54 / 0.6 / ≫ | 58 / 1.0 / 4,125 % → 13 / 3.5 / 247 % | 22 / 1.5 / 1,045 % → 8 / 4.9 / 55 % |

≫: over 10,000 %, a minute of fighting against a death in under a second. Dragons, titans and elementals at Beyond
Madness hit 1.5–1.6 × harder than other monsters of their level (magic against weaker resistances). That is where a
Warding pick (§5.6) earns its place.

### 4.6 Bosses

A group with one boss: the boss is fought last, HP ×5 (MAW 2.5–7.5), damage ×1.3. HP used, today → compensated.

| Encounter | Under-geared | Medium | Pimped |
|---|---|---|---|
| Nightmare, Ravenshore | 1,529 → 536 % | 385 → 74 % (20 s) | 68 → 17 % (13 s) |
| Nightmare, Garrote Gorge | 3,060 → 1,025 % | 531 → 84 % | 94 → 15 % |
| Nightmare, Dragon Cave | 4,597 → 1,495 % | 793 → 108 % | 137 → 19 % |
| Nightmare, The Hive | 5,446 → 1,716 % | 796 → 92 % | 141 → 14 % |
| Beyond Madness, Ravenshore | 3,963 → 1,759 % | 1,237 → 333 % | 419 → 127 % |
| Beyond Madness, Garrote Gorge | ≫ → 6,740 % | 2,809 → 297 % | 509 → 59 % |
| Beyond Madness, Dragon Cave | ≫ | 6,531 → 520 % | 1,554 → 127 % |
| Beyond Madness, The Hive | ≫ → 8,477 % | 3,577 → 225 % | 945 → 42 % |

Bosses are where a medium solo has to use everything: cooldowns, potions, block and crowd control. That is the
"tough" the user asked for.

### 4.7 Archers and casters

Same model, different assumptions, compensated (today → compensated):

- **Archer:**
  - DPS as the melee build: MAW normalises weapon damage by recovery; a Master bow looses two arrows.
  - 3 seconds of free shots before melee monsters arrive outdoors. They move at v/2 + 300 in MAW, about
    450–500 units/s.
  - 0.85 × effective HP (leather).
  - No cleave; Volley from Master.
- **Caster:**
  - Spell power over melee power from MAW's own model: about 1.5 × at Nightmare levels 20–100 and about 1 × at
    Beyond Madness, falling to 0.75–0.9 × from level 300.
  - Area spells hit the whole group at 50 %.
  - 0.55 × HP: Sorcerer 3 HP per level against the model's 9. Mana Shield is not counted (§5.5).

| | Archer: medium | Archer: pimped | Caster: medium | Caster: pimped |
|---|---|---|---|---|
| Nightmare 20 | 185 → 39 % | 21 → 7 % | 188 → 53 % | 35 → 14 % |
| Nightmare 100 | 162 → 12 % | 17 → 0 % | 153 → 32 % | 27 → 4 % |
| Nightmare 220 | 281 → 16 % | 28 → 0 % | 365 → 62 % | 64 → 9 % |
| Madness 50 | 597 → 163 % | 116 → 43 % | 512 → 157 % | 125 → 51 % |
| Madness 200 | 1,147 → 97 % | 153 → 6 % | 927 → 160 % | 157 → 22 % |
| Madness 450 | 2,342 → 147 % | 497 → 13 % | 2,689 → 381 % | 667 → 95 % |

- **Archers are the safest solos outdoors.** Kiting is real play, not cheese, as long as Hell's and Nightmare's extra
  ranged attacks for melee monsters (10/20/30 % by tier outdoors) keep it honest.
- **Casters fall behind at high levels:** their single-target damage drops under melee from level 300 and their HP is
  half. Their trees therefore carry Ward and Mana Shield ties (§5.4, §5.5), and MAW's Mana Shield (25–100 % absorbed at
  up to 5 HP/SP) is their real second HP bar.

## 5. Special skills

### 5.0 The user's direction (2026-11-13)

Talents are a layer **on top**: they help and add a little power without throwing the balance out (focused builds are
already viable, §3.7–3.8). Points: **one per 10 levels**, since a solo gains many levels. Examples the user gave for
melee: small per-point stat gains (about +2 % to Might, Endurance and Speed per point), a Cleave active on a cooldown,
an improved Charge (shorter cooldown per point), and later perhaps a short attack-speed burst after building rage.
Archers, casters and support get the same shape. The sketch below (passives capped at 5 ranks, actives whose ranks
shorten cooldowns or lengthen effects) supersedes the larger per-skill trees of §5.2–5.7 where they disagree; those
remain as a pool of ideas. Numbers are first guesses to be tuned in play.

Revised by the user on 2026-11-13: no tree for every class (health potions stay as MAW has them), Cleave hits up to
five, a Whirlwind active, Frenzy as a timed attack-speed buff with no rage yet, Ward dropped (Mana Shield covers it),
support merged into the caster tree, the caster gains Blink (as in WoW) and +2 % Endurance and healing.

At one point per 10 levels a solo has about 15 points at the end of one world (level ~150) and 40–60 in a long MAW run
(level 400–600). The trees cost 20 (melee), 17 (ranged) and 24 (caster) points to fill, so a long run fills one tree
and most of a second; a short run picks.

| Tree | Node | Kind | Per rank (max ranks) |
|---|---|---|---|
| Melee | Weapon Training | passive | +2 % Might, Endurance and Speed (5) |
| Melee | Cleave | active | next swing hits up to 5 in its arc at 60 %, cooldown 12 s, −2 s per rank (3) |
| Melee | Whirlwind | active | a spin hitting every monster in melee reach around at 50 %, cooldown 20 s, −3 s per rank (3) |
| Melee | Frenzy | active | +25 % attack speed for 6 s, cooldown 30 s, +1 s duration per rank (3) |
| Melee | Charge | active | dash to the target and stagger it, cooldown 25 s, −3 s per rank (3) |
| Melee | Shield Wall | active | with a shield: 50 % less damage for 6 s, cooldown 60 s, −10 s per rank (3) |
| Ranged | Marksman | passive | +2 % Accuracy and Speed (5) |
| Ranged | Volley | active | five arrows in a cone at 60 %, cooldown 12 s, −2 s per rank (3) |
| Ranged | Disengage | active | leap back 4 m, cooldown 15 s, −2 s per rank (3) |
| Ranged | Pinning Shot | active | the target is slowed by half for 4 s, cooldown 10 s, +1 s per rank (3) |
| Ranged | Steady Aim | passive | after standing still for 1 s, +3 % critical chance (3) |
| Caster | Attunement | passive | +2 % Intellect, Personality, Endurance, spell damage and healing (5) |
| Caster | Blink | active | teleport 15 m forward (as WoW's Blink), cooldown 15 s, −2 s per rank (3) |
| Caster | Spell Surge | active | the next spell costs no SP and hits ×1.5, cooldown 45 s, −5 s per rank (3) |
| Caster | Mana Font | passive | +1 SP per 5 s per 10 levels (5) |
| Caster | Purify | active | cure one condition and 5 s immunity to it, cooldown 30 s, −5 s per rank (3) |
| Caster | Resolve | passive | +2 % to all resistances (5) |

A rage resource for melee can come in a later pass.

### 5.1 Rules of the trees

**Revision (2026-11-13).** Focused solos already have 1.6–4.4 × the expected character's damage (§3.7), so the trees
are for feel, identity and the party's functions. They are not a power layer. Against the tables below:

- **Halve every damage multiplier and every flat damage-taken reduction:** Momentum, Sunder, Executioner, Hunter's Mark,
  Inferno Heart, Brace, Last Stand, Shield Wall and the like.
- **Keep at full value** what a solo lacks:
  - sustain: Reaving, Bloodrush, Second Wind, Mend, Lay on Hands, Drain;
  - crowd control: Frost Nova, Tremor, Terrify, Pinning Shot;
  - mobility: Blink, Sidestep, Charge, Disengage;
  - condition answers: Iron Will, Molting, Purge, Aegis;
  - area damage: Cleave on top of R4, Whirlwind, Volley, Tail Sweep;
  - the HP skills, which matter to fragile classes: Iron Hide, Iron Constitution.
- A fully built tree should then be worth about ×1.3–1.6 on (damage × effective HP), not ×2–3.
- The Grandmaster keystones stay, as trade-offs.


- **A tree per school, tied to an MM skill.** Its tiers open at Expert, Master and Grandmaster of that skill. The
  trainer stays the gate, as in MM.
- **Choice nodes.** Each tier offers two or three skills and the school point of that tier buys one. A free point
  (§6) buys a second one from a tier already open. This is Dragonflight's octagon nodes and Path of Exile's
  notables, not linear ranks
  ([Blizzard on the Dragonflight trees](https://worldofwarcraft.blizzard.com/en-gb/news/23797209)).
- **No filler.** Every skill changes a decision:
  - when to swing, block or move;
  - which target;
  - when to spend a cooldown.

  Blizzard dropped classic "+1 % per rank" talents as "boring" and "inconsequential"
  ([Engadget, 2011](https://www.engadget.com/2011-12-08-ghostcrawler-on-seeing-the-forest-for-the-talent-trees.html)).
  The Skyrim community's main perk mod made the same complaint about +20 % per rank
  ([Ordinator changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/496978857)).
- **They grow with the MM skill.** A skill's numbers are "X + Y per point of the school's skill, at most Z", with the
  maximum reached around skill 100. A Grandmaster at 60 is far stronger than one at 40, so skill points keep their
  value; MAW's own skill tables are built the same way.
  - The skill read is the base skill plus item bonuses, as attacks read it.
  - The caps keep Beyond Madness's skill 100+ characters from breaking the curve.
- **Multipliers are few and large, and conditional:** ×1.1–×2 on a condition (below 25 % HP, after a block, while a
  monster is adjacent), not always-on. Diablo 4's "×" multipliers are 10–60 % each and stack multiplicatively; its
  season 2 had to turn some into additive bonuses ([Maxroll](https://maxroll.gg/d4/resources/in-depth-damage-guide)).
- **Keystones at Grandmaster have a cost:**
  - Executioner gives less damage to healthy monsters.
  - Whirlwind makes the character take more damage while it spins.
  - The keystone skills of the Fire, Water and Earth trees each raise spell cost or reduce mobility.

  This follows Path of Exile's keystones ([official tree](https://pathofexile.com/passive-skill-tree)).
- **What every solo needs is free, not a point:**
  - each school's first Expert active (HUD study);
  - the block;
  - the Kick;
  - the potion slot.

  Dragonflight grants what everyone would take ([Blizzard](https://worldofwarcraft.blizzard.com/en-gb/news/23797209)).
- **Cooldown economy.** A group dies in 3–20 s and the next comes 20–40 s later:
  - 8–20 s cooldowns are per-group tools;
  - 45–90 s cooldowns are boss tools;
  - one 5–10 minute "cheat death" per tree at most.

  Cooldowns tick in real time, run on in turn-based mode by turn (1 turn = 2 s, as MAW's crowd-control minutes), and
  are saved.
- **Actives** go on the action bar with their cooldown. **Passives** with a trigger show a proc (HUD study).
- **Notation:**
  - **A** active (cooldown), **P** passive.
  - "/pt" means per point of the tree's skill.
  - Damage percentages are of a normal attack or cast at that moment, with all its multipliers. Durations halve on
    bosses, and crowd control follows MAW's diminishing returns (CLASSES_SPELLS_SPEC.md §4).

### 5.2 Melee

**Two-Handed** (two-handed sword, axe, mace, staff, spear, halberd; the wielded weapon's skill)

| Tier | Choice A | Choice B | Choice C |
|---|---|---|---|
| Expert | **Cleave** (P): swings also strike up to 2 other monsters in a ±50° arc in reach for 40 % + 0.4 %/pt (max 80 %). Free Expert active: **Heavy Blow** (A, 8 s): 150 % + 0.5 %/pt, staggers 1 s | **Momentum** (P): each hit on the same target within 3 s adds +4 % + 0.04 %/pt damage, up to 5 stacks; switching targets resets | — |
| Master | **Reaving** (P): 2 % + 0.04 %/pt of melee damage dealt heals you (max 6 %), doubled below 35 % HP | **Sunder** (A, 20 s): the next blow sets the target's physical resistance to 0 for 8 s and it takes +20 % + 0.2 %/pt (max +40 %) from you | **Wide Arc** (P): Cleave's arc becomes ±80°, and Cleave counts the main target's knockback |
| Grandmaster | **Executioner** (P, keystone): ×2 damage to monsters below 25 % HP; ×0.9 to monsters above 75 % | **Whirlwind** (A, 15 s): a 1.2 s spin striking everything in reach for 150 % + 1 %/pt (max 250 %); you take +20 % damage meanwhile | **Juggernaut** (P, keystone): no knockback or stagger, −15 % − 0.1 %/pt damage taken (max −25 %) while you attack; recovery +10 % |

The README's proposal that two-handed swords and axes cleave natively at half damage is the alternative to making
Cleave a skill (§10). The numbers in §4 used the skill.

**Sword and Board** (Shield)

| Tier | Choice A | Choice B | Choice C |
|---|---|---|---|
| Expert | Free: **Shield Bash** (A, 8 s): 60 % + 0.5 %/pt and a 1.5 s stagger; blocking (40/55/70/85 %) is baseline. **Riposte** (P): a block within 0.4 s of the blow (a parry) makes your next swing +50 % + 0.5 %/pt (max +100 %) and ready at once | **Guarded Advance** (P): walk at full speed with the shield raised; missiles from the front are blocked at the full rate | — |
| Master | **Shield Wall** (A, 45 s): 6 s of −60 % − 0.3 %/pt (max −80 %) all damage from the front 180°, while you can still swing | **Spell Ward** (P): the block also takes magic damage at half the physical rate | **Shield Charge** (A, 20 s): dash up to 8 m, knock down the first monster 2 s (the generalised Knight Charge) |
| Grandmaster | **Bulwark** (P): blocked missiles return to the shooter at 50 % of their damage | **Aegis** (A, 90 s): 4 s of 100 % block from every side and immunity to conditions | **Rally** (A, 90 s): heal 30 % + 0.2 %/pt of maximum HP over 6 s; +20 % damage meanwhile |

Facing matters: the block works only against the front 180°, which also fixes the open prototype point that "a blow
from behind is blocked too". The skill blocks the hit on a key, not a menu: the action's skill element.

**Dual Wield and Dagger** (Dagger; one-handed Sword from Master; MAW's Dwarf and Minotaur axes)

| Tier | Choice A | Choice B | Choice C |
|---|---|---|---|
| Expert | Free: **Flurry** (A, 10 s): three strikes in 0.6 s at 60 % + 0.3 %/pt each. **Opening Strike** (P): ×2.5 against a monster not targeting you, or from behind | **Fleet** (P): +15 % movement while a dagger or two weapons are held; dodging a blow (§5.6) readies the next swing | — |
| Master | **Venom** (P): hits poison: 4 % + 0.04 %/pt of the hit per second for 5 s, 3 stacks | **Twin Fangs** (P): when both hands hit the same target within 1 s, both crit for +25 % crit damage | **Shadowstep** (A, 15 s): blink behind the target; your next attack counts as Opening Strike |
| Grandmaster | **Thousand Cuts** (P, keystone): recovery −30 %, damage per hit −15 %; crits shorten the cooldown of your actives by 0.5 s | **Assassinate** (A, 30 s): 400 % + 3 %/pt; if it kills, the cooldown resets | **Evasion Mastery** (P): after a dodge, 2 s of +30 % dodge chance and crits |

**Armsmaster** (shared by every melee build)

| Tier | Choice A | Choice B |
|---|---|---|
| Expert | Free: **Kick** (A, 4 s): push back 2 m, 1 s stagger (Dark Messiah). **Footwork** (P): for 3 s after a Kick +20 % damage | **Bloodlust** (P): a kill in melee refunds 50 % of your recovery |
| Master | **Charge** (A, 15 s): rush up to 10 m to the target, knock it down 1.5 s; MAW's solo Knight Charge (DEVIATIONS 48) becomes this for every melee class | **Weapon Swap** (P): switching weapon sets is instant, and the first attack after a switch gets +30 % |
| Grandmaster | **Battle Trance** (A, 90 s): recovery halved for 8 s + 0.05 s/pt (max 12 s) | **Warlord** (P, keystone): Armsmaster's damage per point counts double; −10 % maximum HP |

### 5.3 Ranged: Bow

The baseline stays: two arrows at Master and fire arrows at Grandmaster (MAW). Bow is the solo-friendly tree outdoors.

| Tier | Choice A | Choice B | Choice C |
|---|---|---|---|
| Expert | Free: **Quick Shot** (A, 6 s): a shot without the draw at 70 %. **Hunter's Mark** (P): your first hit marks a monster; marked monsters take +15 % + 0.15 %/pt (max +30 %) from you | **Pinning Shot** (A, 12 s): the target is slowed 50 % for 4 s, and rooted 1 s on a crit | — |
| Master | **Volley** (A, 20 s): five arrows in a 30° cone at 70 % + 0.3 %/pt each | **Skirmisher** (P): no movement penalty while drawing; +5 % damage per 5 m to the target, up to +20 % | **Disengage** (A, 15 s): leap 6 m backwards; the next shot within 2 s crits |
| Grandmaster | **Rain of Arrows** (A, 45 s): a 4 m area takes 8 volleys over 2 s, 80 % + 0.5 %/pt each | **Deadeye** (P, keystone): crits pierce one monster in line and ignore physical resistance; −15 % attack speed | **Splinter** (P): fire arrows explode for 25 % + 0.2 %/pt in 2 m |

### 5.4 Caster damage (one tree per element)

All of them build on MAW's spells, Ascension and auras; they add solo tools, not just more damage. Each tree's free
Expert active is listed first.

| School | Expert | Master | Grandmaster |
|---|---|---|---|
| **Fire** | Free: **Kindling** (P): three Fire Bolt hits make the next Fireball free and +30 %. Choose: **Burning** (P): fire spells burn for 20 % + 0.2 %/pt of the hit over 3 s / **Heat Shimmer** (P): −15 % fire damage taken | **Flame Ward** (A, 30 s): 6 s; monsters striking you in melee take your Fire Bolt's damage, −30 % fire taken / **Combustion** (A, 25 s): burns on every monster in 8 m deal their remaining damage at once | **Inferno Heart** (P, keystone): fire damage +40 % + 0.2 %/pt, spell cost +25 % / **Phoenix** (P, 10 min): a killing blow makes you explode for three Fireballs and stand up at 30 % HP |
| **Air** | Free: **Blink** (A, 10 s): teleport 8 m forward. Choose: **Static** (P): bolt hits jump 25 % + 0.2 %/pt to the nearest other monster / **Tailwind** (P): +15 % movement out of melee range | **Storm Shield** (A, 30 s): 5 s; missiles aimed at you are deflected (75 %) / **Chain Mastery** (P): Chain Lightning gets two more targets at 50 % | **Storm Call** (A, 60 s): 5 s of lightning on up to 4 monsters a second at 120 % + 1 %/pt / **Eye of the Storm** (P, keystone): you take −30 % from missiles and +20 % from melee |
| **Water** | Free: **Frost Nova** (A, 20 s): freeze everything in 4 m for 2 s (bosses 1 s). Choose: **Chill** (P): Ice Bolt slows 30 % for 3 s / **Deep Freeze** (P): Frost Nova +1 s + 0.01 s/pt | **Ice Barrier** (A, 30 s): absorb 20 % + 0.3 %/pt of maximum HP for 10 s / **Shatter** (P): frozen monsters take +50 % from your next hit | **Winter's Grasp** (P, keystone): your crowd control lasts +50 %; your damage −15 % / **Comet** (A, 45 s): Ice Blast that also freezes for 1.5 s |
| **Earth** | Free: **Stone Hide** (A, 30 s): −30 % − 0.1 %/pt damage taken for 10 s. Choose: **Tremor** (A, 15 s): knock down everything in 4 m for 1 s / **Rooted** (P): no knockback; +10 % physical resistance while standing still | **Rock Armour** (P): Stone Skin reserves half / **Quake** (A, 30 s): 4 s; monsters in 6 m are slowed 40 % and take 40 % + 0.3 %/pt per second | **Stone Form** (A, 120 s): 4 s invulnerable, cannot act or move / **Mountain** (P, keystone): +30 % maximum HP, −20 % movement and cast speed |
| **Light** | Free: **Radiance** (P): undead and demons within 5 m take 10 % + 0.1 %/pt of your weapon or spell damage per second | **Smite** (A, 12 s): 200 % + 1 %/pt Light, double against undead and demons / **Sanctuary** (P): Day of Protection also gives 10 % damage reduction | **Sun's Wrath** (A, 90 s): Sunray on everything in view / **Blinding Light** (A, 45 s): stun all in 8 m for 2 s |
| **Dark** | Free: **Drain** (P): spell hits heal 4 % + 0.04 %/pt of the damage (max 8 %) | **Shadow Step** (A, 15 s): teleport to a target's back / **Curse of Frailty** (A, 20 s): target takes +25 % from all sources for 8 s | **Soul Harvest** (P): kills refund 10 % SP and 5 % HP / **Pact** (P, keystone): spells cost HP instead of SP at 2 HP per SP, +20 % spell damage |
| **Mind** (control) | Free: **Clarity** (P): crowd-control spells cost 15 % less. Choose: **Terrify** (A, 25 s): Mass Fear 3 s in front | **Iron Will** (P): immune to Afraid, Insane and Paralyzed (even with G4: no stagger) / **Dominate** (A, 60 s): Charm one non-boss for 10 s; it fights for you | **Mind Over Matter** (P, keystone): 20 % of damage taken is paid with SP at 2 HP per SP; −20 % maximum SP / **Mass Hysteria** (A, 90 s): Berserk on every monster in 10 m for 4 s |

Casters also get **Ward**, a cross-school pick that takes the slot of any Expert choice in Fire, Air, Water or Earth:
resistance to that element +25 % + 0.25 %/pt. It answers dragons' and elementals' magic damage at Beyond Madness
(§4.5).

### 5.5 Healing and support (Body, Spirit)

Party heals become self-heals; party buffs become personal ones.

| School | Expert | Master | Grandmaster |
|---|---|---|---|
| **Body** | Free: **Mend** (P): Heal on yourself +25 %, and its recovery −30 %. Choose: **Purge** (A, 30 s): remove poison, disease, weakness and curses; immune for 5 s / **Vital Flow** (P): 1 % + 0.02 %/pt of maximum HP per second while a monster is within 5 m (max 3 %) | **Lay on Hands** (A, 60 s): heal 40 % + 0.2 %/pt of maximum HP at once / **Second Breath** (P): Greater Heal also cures conditions | **Undying** (P, 5 min): a killing blow leaves you at 1 HP with 2 s of immunity / **Bloodbond** (P, keystone): your heals are 50 % stronger, 25 % of overhealing becomes a shield for 5 s; −15 % damage |
| **Spirit** | Free: **Spirit Tide** (A, 120 s): 30 % of maximum SP over 8 s. Choose: **Guardian Spirit** (P): your auras reserve 25 % less (on top of G3) | **Spirit Link** (P): 10 % of damage taken goes to SP instead, 2 HP per SP / **Ancestral Guard** (A, 60 s): summon a spirit that draws monsters' attacks for 6 s (HP = 50 % of yours) | **Resurgence** (P, 10 min): when you would die, rise at 50 % HP / **Bless the Blade** (P, keystone): Heroism and Bless at full power without reserving mana, other auras cost 25 % more |

**Mana Shield** (MAW skill 51) is the caster's survival tool. Tie it in through Mind and Spirit:

- Mind Over Matter and Spirit Link stack with it, up to the 5 HP-per-SP efficiency cap.
- G1's ×0.8 damage taken is applied before Mana Shield, so mana pays less.

### 5.6 Defence and survival

**Armour** (the worn body armour's skill: Leather, Chain or Plate)

| Tier | Choice A | Choice B | Choice C |
|---|---|---|---|
| Expert | **Brace** (P): −5 % − 0.2 %/pt damage taken from the front (max −25 %) | **Light Step** (Leather only, P): +10 % movement and Dodging's dodge chance from Expert (normally Grandmaster) at half its value | **Ward** (P): −10 % − 0.2 %/pt magic damage (max −30 %) |
| Master | **Iron Hide** (P): +10 % + 0.2 %/pt maximum HP (max +30 %) | **Spell Lining** (P): +25 % + 0.25 %/pt to the resistance your armour skill gives | **Unbreakable** (P): your worn items never break; no stagger from blows under 10 % of your HP |
| Grandmaster | **Last Stand** (A, 60 s): −50 % damage taken for 6 s | **Bastion** (P, keystone): AC from armour +50 %; movement −15 % | **Adaptive** (P): after taking magic damage of an element, +50 % resistance to it for 8 s |

**Dodging**

| Tier | Choice A | Choice B |
|---|---|---|
| Expert | Free: **Sidestep** (A, 6 s): dash 3 m, 0.3 s of invulnerability. **Evasion** (P): +5 % + 0.05 %/pt dodge against missiles | **Slippery** (P): Sidestep breaks roots and slows |
| Master | **Counter** (P): a dodge readies your next attack, +30 % | **Second Sidestep** (P): Sidestep has two charges |
| Grandmaster | **Untouchable** (A, 60 s): 3 s of dodging every attack | **Flow** (P, keystone): each dodge +10 % damage for 5 s (stacks 3); −20 % maximum HP |

**Survival** (Bodybuilding)

| Tier | Choice A | Choice B |
|---|---|---|
| Expert | Free: **Second Wind** (P, 60 s): below 35 % HP, heal 25 % over 3 s. **Tough** (P): stagger and knockback last half as long | **Bloodrush** (P): heal 1 % + 0.02 %/pt of maximum HP per second while a monster is within 5 m (max 3 %): the non-Regeneration classes' share of what a Troll has |
| Master | **Iron Constitution** (P): +10 % + 0.2 %/pt maximum HP (max +30 %) | **Hold the Line** (P): while below 50 % HP, −20 % damage taken |
| Grandmaster | **Undying** (P, 5 min): a killing blow leaves you at 1 HP with 2 s of immunity | **Titan's Blood** (P, keystone): potions heal 50 % more and their cooldown halves; −10 % damage |

Undying and Resurgence never stack: one cheat-death at a time.

### 5.7 The Dragon

The four Dragon Abilities spells stay on the bar ([DRAGON.md](DRAGON.md)). The Dragon has Regeneration (Master/GM)
and no weapons or body armour, so its trees replace Two-Handed, Shield and Armour.

| Tree (skill) | Expert | Master | Grandmaster |
|---|---|---|---|
| **Fangs** (Unarmed / MAW's Fangs) | Free: **Rend** (P): claw hits bleed 15 % + 0.2 %/pt of the hit over 4 s. Choose: **Bite** (P): every third chained blow bites for +50 % | **Tail Sweep** (A, 15 s): everything in the rear half circle, 140 % + 0.5 %/pt, knockdown 1 s; the Dragon's cleave / **Ferocity** (P): kills give +20 % recovery speed for 5 s | **Pounce** (A, 20 s): leap 10 m to a target, 200 %, stun 2 s / **Apex** (P, keystone): +25 % melee damage; the breath costs 50 % more |
| **Scales** (Dodging in MAW) | Free: **Guard**: the block button raises the forelegs, a 40/55/70/85 % block by Scales mastery | **Harden Scales** (A, 30 s): −40 % damage taken for 6 s / **Molting** (P): no condition lasts more than 3 s | **Dragonhide** (P): magic damage −20 % − 0.1 %/pt (max −35 %) / **Ancient** (P, keystone): +40 % HP, −20 % movement and no Flight in combat |
| **Breath** (Dragon Ability) | Free: **Roar** (A, 20 s): Fear in front, 3 s | **Flame Blast** cost −25 % / **Kindled Breath** (P): the breath sets burns, 20 % over 3 s | **Searing Breath** (A, 45 s): a 3 s held cone, 60 % + 0.5 %/pt of the breath every 0.25 s, 10 % SP a second / **Wing Storm** (A, 60 s): Wing Buffet in 360° with a 2 s knockdown |

## 6. Point economy

**Recommended:**

- **School points:** one per mastery reached (Expert, Master, Grandmaster) in a tree's skill, spent only in that tree.
  Each buys one choice of the tier it opens. This ties the trees to MM's skills and trainers and is the same in every
  progression mode.
- **Free points:**
  - one at each promotion (two in MMMerge);
  - one per ten maps cleared (MAW's completion state; Standard: a map whose monsters are all dead), at most 10.

  A free point buys a second choice in an open tier, in any tree.
- **The free Expert active** of each tree costs nothing (HUD study).

Typical totals:

| | Trees trained | School points | Free points | Total | Skills on offer |
|---|---|---|---|---|---|
| Melee (2H, Armour, Armsmaster, Survival, Dodging) | 5 | 15 | 2 + 6–10 | 23–27 | 37 |
| Caster (two elements, Body, Spirit, Mind) | 5 | 15 | 2 + 6–10 | 23–27 | 39 |
| Mid-run (Master in 4 trees) | 4 | 8 | 1 + 3 | 12 | — |

Choices remain: a full build has about two-thirds of what its trees offer, and each tier is one-of-two or one-of-three
unless a scarce free point is spent there.

**Why not one point per 10 levels plus promotions** (HUD study §"Point gain"):

| Solo level at the end of the game | Points at one per 10 levels | |
|---|---|---|
| Free progression, about 200 | 20 + 2 | |
| Horizontal Nightmare, about 400 (content 220) | 40 + 2 | everything in five trees |
| Beyond Madness, about 890 (content 500) | 89 + 2 | everything in every tree |

- Levels depend on five times the experience and on the progression mode, a fourfold spread.
- Points would also arrive before the masteries that open the tiers. At Beyond Madness the Grandmaster tier opens at
  skill 40, solo level about 250.

If levels must count, use the **banked level** (party-equivalent: 1 per 10 banked levels): 10 in free, 22 at
Nightmare's end, 50 at Beyond Madness's. It still overflows in Beyond Madness, so cap it at 12 (§10).

**Respec:** MAW's skill respec (1,000 gold × level, at the three continents' respec NPCs) also resets special skills.
Changing one choice in a tier at any trainer of that skill costs that mastery's teacher price.

## 7. MAW rules that interact or conflict

- **The balance model is the yardstick.** MAW sizes monsters from `MawBalanceModel` on every map load; every solo
  multiplier must stay outside it:
  - Monster HP and damage stay MAW's.
  - G1–G2 act on the character.
  - Kill experience reads `monsterHealth(member level)` (MawExperienceRules.cpp:176-193). G1–G2 must not feed back
    into it, or a stronger solo would earn less.
- **Bolster and banks:** a solo's banks grow as one member's (awards / 5), so free-progression bolster never sees the
  inflated solo level. Keep it. Standard's MMMerge bolster does see it (§2.4).
- **Cover:** solo Cover already halves its own hit (MawCombatRules.cpp:2499-2547). It stacks with G1. Knights who
  train Cover get up to ×1.25 effective HP (40 % chance at the 30-skill cap; BALANCE_MODEL.md §3.7).
- **Party size at resolve time** (DEVIATIONS 151): a solo who hires a follower keeps the monsters it resolved with
  until the next load. Keep it.
- **The density experience multiplier** `sqrt(mean MAW density / mean density)` (MawBalanceModel.cpp:848-855) already
  pays less per kill for larger groups. If G6 shrinks Beyond Madness's groups for solo, recompute it from the solo's
  density, or a solo earns more experience per group.
- **Beyond Madness's death count and the 5-minute hit window** turn G4's stagger and Undying into important rules.
  A "death" is a defeat, and an Undying save is not one.
- **Doom challenge modes:** √L · 2 % of monsters gain random on-hit conditions, death and eradication included. G4
  is the only thing between them and a lost run.
- **Regeneration and Bloodrush:** MAW's Regeneration is class-locked and large (4–10 %/s for a solo). Survival's
  Bloodrush (max 3 %/s) gives other classes a third of it. Troll, Dragon and Vampire remain the natural solo races.
- **Map completion and dimension runs:**
  - Completion experience ×5 / party size per member: unchanged.
  - Dimension maps add `Power × 10 + 20` levels and multiply group maxima by 1 + (P + 20)·n/300 (MawMonsterRules.cpp:
    1869-1878). Solo they are the pimped tier's content, and the encounter tables there need a "Dimension" column
    once tuned (§9).
- **Crafting and the loot filter:** one character gets every material, so a solo crafts 3–5 × faster per slot. The
  "Sell trash" rule compares items with the **mean party level** (LootFilter.cpp), which for a solo is its inflated
  level, so content-level drops look like trash. Use the banked level for a party of one.
- **MAW in MM9** (`rulesets/maw/worlds/mm9/balance.yml`, MM9_BALANCE_DESIGN.md):
  - Pack reserves set MM9's density per map; G6 would need a solo reserve factor in `mm9_pack_reserve.py`.
  - MM9 hirelings are scaled to "a fifth of a member" (`MawClassRules::scaleHirelings`), which in solo is a fifth of
    the only character: a real share. Leave it.
  - MM9's quest experience caps, not applied yet ([BALANCE_PLAN.md](../mm9_rework/BALANCE_PLAN.md)), must use the
    ×5 / party size rule.
- **Turn-based mode:** a solo acts once per round, so cooldowns count in turns (§5.1). The 370-unit move limit at Doom
  and up applies to the party only.
- **Talents and MAW's class kits:** some MAW class mechanics already are talents:
  - the Assassin's combo points;
  - the Elementalist's stacks;
  - the Death Knight's and Shaman's damage cuts;
  - the Seraph's speed.

  Their trees should not duplicate them. For example the Assassin's Dagger tree swaps Flurry for "Finisher spends
  combo points".

## 8. Expected outcomes

With the revised compensation (§4.0), by build rather than by tier. The figures are per average group, standing and
trading, with content-level gear and brewed buffs.

**Nightmare:**

- **Sturdy melee (Minotaur, Troll, Monk, Death Knight; the Dragon with its breath):** strong.
  - Groups take 1.7–3.8 × the party's time and cost 0–97 % of HP.
  - The Troll and Vampire are slow, 4–6 × the party's time, but never in danger.
- **The Knight (sword and shield):** OK. 54–84 % per group without blocking; the block and Knight Charge make it
  comfortable.
- **Fragile builds (Seraph, Shaman in melee, Elementalist, Arch Mage caught in melee):** OK but tough after R2–R4: 45–111 %,
  one or two drinks per group.
- **Casters at range:** clear faster than a party.
- **The Priest:** 146–245 % on damage alone, but its Greater Heal (about 40 % of its HP per cast) makes it an unending
  fighter. Slow (4–5 × the party's time).
- **Bosses:** about double a group (§4.6).
- **Under-geared or unfocused solos:** struggle, as §3.4 shows.

**Beyond Madness:**

- **Stand and trade:** only the Minotaur (54–115 %) and the Troll (9–86 %).
- **Everyone else:** 3–29 drinks per group, or pulling, kiting and crowd control. Groups take 1.5–3 × the party's time;
  casters take less.
- **Crafting** (Cubes to own level) roughly halves a melee build's damage taken per group.
- **A weak or unfocused build** (Priest without healing, under-geared) is not viable.

That is the picture MAW's author describes: any class can finish Beyond Madness solo, with consumables and tactics, at
two to three times the work.

## 9. Test plan

**Built for this study** (in `tests/scenarios/solo_balance/`; run from the repository root):

- `monster_tables.yml`: every map's native families, Nightmare (party of one and of five) and Beyond Madness, written
  to `output/solo_balance/`.
- `anchor_{nightmare,madness}_{early,mid,late,endgame,extreme}.yml`: the measurements of §3.5. They are generated by
  `model/gen_anchor.py`; the C-tier attack target is chosen so a blow cannot kill it.
- Run them:

  ```
  ls tests/scenarios/solo_balance/*.yml | xargs -P5 -I{} sh -c \
    './build/game/openyamm --headless-run-scenario {} > output/solo_balance/logs/$(basename {} .yml).log 2>&1'
  python3 tests/scenarios/solo_balance/model/parse_anchor.py
  python3 tests/scenarios/solo_balance/model/anchor_margin.py
  ```

- `classes_late.yml`, `classes_endgame.yml`: every class of MAW's four test parties at the late (level 100) and
  endgame (level 200) stages against one durable target. They measure:
  - melee damage per second (`party_attack`);
  - spells, cast directly and read from the target's hit points (`cast_spell`, `actor remaining`);
  - HP (`hp show`);
  - Champion's, Paladin's and Divine Blessing potions, and the Heroism and Bless scrolls, on the Champion;
  - a second two-handed axe for the Minotaur, and a two-handed sword for the Seraph.

  Generated by `model/gen_classes.py`.
- The model (`model/mawmodel.py`, checked against `balance_golden.csv`) and its uses:
  - `gap.py` (§3);
  - `calib.py` (§4.4);
  - `encounters.py` (§4.5–4.6, it reads the TSV tables);
  - `archetypes.py` (§4.7);
  - `builds.py` (§3.7–3.8: focused builds, class factors, potion buffs);
  - `revised.py` (§4.0).

  Changing a number in §4.2 or §5 is one constant in `calib.py`.

**Needed once solo mode exists:**

1. **A two-sided fight step** in the runner: `solo_fight`, with the member and actors and a timeout. The member
   attacks the nearest hostile through the real attack path at its real recovery while the actors fight back. It
   reports time to kill, HP lost, potions drunk and whether the member died.
   - Today `party_attack` heals the actor after every blow and `advance_runtime` lets monsters hit an idle party, so
     time to kill and time to die are measured separately and combined.
   - It also fixes the gap found here: indoors `party_attack` landed 0 of 100 attacks, because the party is placed
     64 units off the actor, which can be inside a wall. Give it a reachable placement or an indoor check.
   - `party_attack` also needs a `range` option: it always places the party in melee reach, so bows and the Dragon's
     breath cannot be measured. It also misses spells whose projectiles land after the call (§3.7 reads those from
     the target's HP).
2. **Scenarios per tier and difficulty:**
   - Tiers via `testparty` stages with a gear-rarity override. Today a stage's rarity is fixed: add `+rarity:<r>` to
     the console command.
   - Encounters: Ravenshore, Garrote Gorge, Dragon Cave, Plane of Fire, Titans' Stronghold, The Hive.
   - Bands to assert: pimped ≤ 25 % (Nightmare) / ≤ 60 % (Beyond Madness); medium within 25–80 % / 80–200 %; under
     ≥ 150 %.
   - Each a few minutes long: like the playthroughs, not routine tests and not in CI.
3. **G4 scenario:** a lone member hit by a Basilisk, a Medusa and a Titan (Dead) must stagger, not lose.
   `assert: {condition}` and `party_defeat {expect_game_over: false}` exist.
4. **G5 scenario:** a solo drinks a Cure Wounds: heal = 20 + 25 % of min(own max, 2 × expected at its power); a second
   drink within 10 s is refused.
5. **Unit tests:**
   - each special skill's formula with its per-point scaling and cap;
   - the point economy: points from masteries, promotions and cleared maps; spending; respec;
   - the Lone Hero multipliers off for a party of two.
6. **Desktop play** by the user at both difficulties with three save files (one per tier). The bands of §4.1 are a
   starting point; "feels strong" is decided in play.

## 10. Open decisions

1. **Compensation size.** The revised set R1–R5 (§4.0) with no global multipliers, or nothing beyond R1 (conditions)?
   The data say sturdy focused builds need nothing; fragile classes need R2–R4.
2. **Conditions (R1):** stagger 2 s plus 20 s immunity, and death/eradication as 50 % of current HP? At every
   difficulty, or Beyond Madness only?
3. **Potions (R2):** sized to the drinker, no extra cooldown (the 1 s recovery is the cost)? Or MAW's original 15 s solo
   cooldown with a stronger heal?
4. **HP floor (R3):** 0.6 × a Knight-line character's HP for a party of one, or leave fragile classes fragile and let
   the Survival tree carry it?
5. **Cleave (R4):** native for two-handed weapons at 35 % (the README proposal was half damage), or only as a special
   skill?
6. **Beyond Madness groups:** keep 3–6, or Road to Insanity's 3–5 for a party of one? Not needed by the revised
   numbers.
7. **Special skills' strength:** for feel and identity, with damage multipliers halved (§5.1)? Or none of the
   damage-type skills at all, only sustain, crowd control, mobility and area?
8. **Points:** mastery-based school points plus scarce free points (recommended), or levels? If levels, which:
   banked levels, capped?
9. **Respec:** at trainers per tier for the mastery's price, plus a full reset with MAW's respec?
10. **Magic trees:** all schools as proposed, or start with melee, bow and Survival?
11. **Standard ruleset:** the same R1–R5? Standard's bolster follows the solo's own level, so its numbers need their
    own check.
12. **Special skills in party mode:** one tree per member as the HUD study asks, or solo only? Party mode would need
    the trees at about half strength, because every group is already sized for five.
13. **Measuring the bow and the breath:** a runner change so `party_attack` can attack from range (§9). Until then the
    Archer's and Dragon's rows understate them.

## Sources

- **Code and data:**
  - `game/rules/maw/` (MawBalanceModel, MawExperienceRules, MawExperienceCurve, MawSkillFormulas, MawCombatRules,
    MawMonsterRules, MawSpellRules, MawPotionRules, MawItemRules);
  - `game/gameplay/GameplayCombatController.cpp`, `GameMechanics.cpp`, `game/party/Party.cpp`,
    `game/app/GameApplication.cpp`;
  - `assets_dev/engine/rulesets/maw/` (patches, `potion_effects.yml`, `class_skills.txt`);
  - `devdocs/maw/` (BALANCE_MODEL.md, COMBAT.md, COMBAT_SPEC.md, SKILLS_SPELLS_ALCHEMY.md, DEVIATIONS.md,
    MM9_BALANCE_DESIGN.md).
- **Other games:**
  - **WoW:**
    - classic filler talents ([Two-Handed Weapon Specialization](https://warcraft.wiki.gg/wiki/Two-Handed_Weapon_Specialization_(Classic)));
    - the Mists redesign ([Engadget](https://www.engadget.com/2011-12-08-ghostcrawler-on-seeing-the-forest-for-the-talent-trees.html),
      [PC Gamer](https://pcgamer.com/mists-of-pandaria-will-fix-talents-once-and-for-all-say-blizzard));
    - Dragonflight class and spec trees, choice nodes and gates ([Blizzard](https://worldofwarcraft.blizzard.com/en-gb/news/23797209));
    - Delves and Brann as the solo companion ([Blizzard](https://worldofwarcraft.blizzard.com/en-us/news/24104270),
      [PC Gamer](https://pcgamer.com/games/world-of-warcraft/wow-the-war-within-s-new-mini-dungeons-are-annihilating-solo-players-while-groups-sleepwalk-through-them-for-free-loot)).
  - **Diablo:**
    - Diablo 2 players setting: monster HP ×(players + 1)/2 ([Maxroll](https://maxroll.gg/d2/resources/player-settings));
    - Diablo 3: +50 % HP per extra player, damage scaling removed ([Engadget](https://www.engadget.com/2013-04-03-diablo-iii-gets-massive-multiplayer-improvements-in-1-0-8.html));
    - Diablo 4 additive and "×" multipliers ([Maxroll](https://maxroll.gg/d4/resources/in-depth-damage-guide)).
  - **Path of Exile:** keystones ([official tree](https://pathofexile.com/passive-skill-tree)); party scaling, +50 %
    life per member ([poedb](https://poedb.tw/Partying)).
  - **Grim Dawn:** masteries and devotion ([official guide](https://www.grimdawn.com/guide/character/devotion)).
  - **Skyrim:** perks gated by skill and Armsman's +20 % ranks ([UESP](https://en.UESP.net/wiki/Skyrim:Perk)); the
    critique of front-loaded % perks ([Ordinator](https://steamcommunity.com/sharedfiles/filedetails/changelog/496978857)).
  - **Elden Ring:** multiplayer boss HP ×1.6 / ×2.3 ([wiki](https://eldenring.wiki.gg/wiki/Multiplayer_Correction)).
  - **Divinity: Original Sin 2:** Lone Wolf ([gamepressure](https://www.gamepressure.com/originalsinii/regular/zf91e0)).
  - **Might and Magic solo challenges** (anecdotal: bows, turn-based retreat):
    [GOG forum](https://www.gog.com/forum/might_and_magic_series/soloing_self_handicapping).
- **Not verified:**
  - Delve HP numbers;
  - whether Elden Ring spirit ashes raise boss HP;
  - Dragon's Dogma's solo-without-pawns numbers;
  - Titan Quest's mastery bar sizes.

  None of them is used in a number above.
