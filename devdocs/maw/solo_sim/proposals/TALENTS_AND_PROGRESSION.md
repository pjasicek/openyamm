# Solo power curve through character progression (proposal)

Status: proposal, 2026-11-14. Nothing is implemented. Scope: what the solo character's own progression (talents,
mastery caps, promotions, class mechanics, a farming currency) could add so a fully built MAW solo of any melee class
rolls through Beyond Madness (BM), and what casters need. Siblings: [POWER_GAP.md](POWER_GAP.md) (how much is
missing) and [ITEMS_AND_CRAFTING.md](ITEMS_AND_CRAFTING.md) (the gear side). Inputs: the solo simulation of
2026-11-14 (`output/maw_solo_sim/`, [../scripts/realfight.py](../scripts/realfight.py)), the talents as built
([TALENTS.md](../../../solo_action/TALENTS.md), `assets_dev/engine/data_tables/talents.yml`), the earlier design
([BALANCE_AND_TALENTS.md](../../../solo_action/BALANCE_AND_TALENTS.md) §4.0, §5) and `game/rules/maw/`. MAW Lua at
8967ae88. Line numbers are from the tree on 2026-11-14.

**A direction to confirm first.** On 2026-11-13 the user set talents as "a layer on top: a little power, without
throwing the balance out" (BALANCE_AND_TALENTS.md §5.0). The new goal (a maxed solo rolls through BM, "real
upgrades and a real power curve") needs a real power layer. This proposal keeps the 17 talents as the feel layer and
puts the power curve into separate, solo-only mechanisms, so either decision stays possible.

---------------------------------------------------------------------------------------------------------------------

## 1. Diagnosis

All numbers: BM, character stage 500 (monsters level ~302 here, 300-320 in the route), seed 1 of `pool_out_madness`,
unless stated. The expected character MAW sizes monsters against has, at level 302, **20,483 HP** and **14,002
power**; a B monster has 70,009 HP and hits **36,800 physical / 71,220 magic** before defences.

### 1.1 The 10 % floor makes defence a solved, capped stat

`mawMitigatedDamage` (`MawCombatFormulas.cpp:220-280`) divides by AC or resistance, then the class cuts (Death Knight
Blood/Unholy and Shaman Air, `:235`, `:245`; set in `mawClassDefense`, `MawClassRules.cpp:815-845`), the Grandmaster
Shield ×0.85 (`:225`), Shielding ×0.85 and the Shield aura, and only then floors the hit at 10 % of its input
(`withFloor`, `:226-230`; MAW's `Formulas.damageFloor = 0.1`, `Formulas.lua:42`, applied at `zzMaw-Stats.lua:761`).
At the wall the floor binds:

| Build (stage 500) | Physical taken | Magic taken (fire / body) | Note |
|---|---|---|---|
| Champion, sword and shield | 10.0 % | 10.0 / 10.0 % | every type on the floor |
| Lich King (DK), Body 70, Dark 70 | 10.7 % | 10.0 / 12.3 % | its ÷1.7 class cuts buy almost nothing |
| Minotaur Lord | 22.6 % | 15.3 / 21.9 % | |
| Arch Mage | 41.7 % | 33.1 / 44.1 % | far from the floor |

Only four layers act after the floor: legendaries 18 and 22, the Seraph/Shaman flat cut (`:229`), the Shield Wall
talent and Mana Shield (`absorbCharacterDamage`, `MawCombatRules.cpp:2566-2591`). So for melee, more AC, resistance or
class cut is worthless from about stage 300; the sibling proposals reach the same conclusion. The expected character
is floored the same way (`Estimates.lua:391, 402`), so the raw magic hit is about 4.3 × its HP / 4.

### 1.2 HP is the one scaling stat, and Bodybuilding caps it by class

HP = (base + HP/level × (level + Endurance effect + Bodybuilding × mastery)) × (1 + Endurance/1000) × (1 + 0.5/1/1.5/2
% × Bodybuilding) (`MawClassRules.cpp:196-205`, `MawSkillRules.cpp:461-480`). The mastery enters twice, so Expert
against Grandmaster is a factor of about 2.5 at the same skill points. MAW caps Bodybuilding at Expert for Seraphim and
Death Knights, Basic for Shamans and Elementalists (`class_skills.columns.txt:29`), Expert for the Arch Mage
(`class_skills.txt:302`), Grandmaster for the Champion and Great Wyrm (`:292`, `:286`).

| Build | Bodybuilding | HP at stage 500 | × expected HP | One landed magic hit |
|---|---|---|---|---|
| Minotaur Lord / War Troll / Great Wyrm | GM 69-77 | 52-58k | 2.6-2.8 | 12-13 % |
| Champion | GM 60 | 33.9k | 1.66 | 21 % |
| Lich King (DK) | **E 40** | 11.6k | 0.57 | 61 % |
| Archangel (Seraph) | **E 31** | 8.0k | 0.39 | 84 % before the flat cut |
| Arch Mage | **E 56** | 8.1k | 0.40 | 288 % (Mana Shield pays) |

### 1.3 The curve breaks between stage 200 and 500

The solo stays at ~1.6 × the monsters' level, but what that buys shrinks. The expected character's power grows about
as level^3.0 (446 → 14,002 from level 97 to 302) and its HP as level^2.3 (1,548 → 20,483); the solo's HP ratio to it
falls (Champion 2.0 → 1.66) while the floor removes its mitigation edge. Champion, sword and shield:

| Stage (monster level) | HP | Landed magic hit | Time to kill a B monster | Groups beaten, pulls of 4 | Single pulls |
|---|---|---|---|---|---|
| 200 (97) | 3,060 | 10 % of HP | 2.0 s | 98 % | — |
| 500 (302) | 33,912 | 21 % of HP | 3.9 s | 1 % | 48 % |

At stage 200 every melee build beats 86-100 % of groups in pulls of four; at stage 500 1-10 % (Troll 57, Seraph 47,
Dragon 84). A Champion loses half its **single** pulls at stage 500.

### 1.4 Melee is single-target in group content

Every monster is sized for one expected character, and BM groups are 3-6. The Dragon wins because its breath is an
area attack on the lowest resistance (realfight: 75 % of the group, `DM:657-664`). Giving melee a 60 % cleave in the
simulation cuts the time per monster by 35-45 % (Champion 3.6 → 2.2 s, two-handed 3.2 → 1.8 s), but alone it lifts
survival only a few points: speed without toughness dies.

### 1.5 The talents are flat, small and run out

- Passives are a share of the **base** stat, by design (`MawSoloTalents.cpp:28-33`): Weapon Training at rank 5 is
  +10 % of base Might/Endurance/Speed, about +2 % HP and a few % damage for a Champion with 431 Endurance.
- Resolve multiplies resistances that are already past the floor, and three of the nine it raises (spirit, light,
  dark, `MawSoloTalents.cpp:63-80`) are not read by MAW's mitigation (`MawCombatRules.cpp:247-254`,
  `MawCombatFormulas.cpp:85-113`). It does nothing at the wall.
- Shield Wall is the right kind of layer (×0.5 after the floor, `MawCombatRules.cpp:2575-2579`) at 15 % uptime.
- One point per 10 levels (`talents.yml:14`, `SoloTalents.cpp:172-175`): 50 points at stage 500, ~80 at the end of
  BM (level ~804), and the whole table costs 61. From level ~610 a solo has nothing to spend on.

Altogether the talents are worth about ×1.2 on damage against groups (Cleave, Whirlwind) and ×1.1 on toughness;
POWER_GAP.md measures ×14 effective power missing for pulls of four.

### 1.6 Casters cannot be judged by this simulation

One magic hit is 288 % of an Arch Mage's HP; Mana Shield (Grandmaster 50, 5 HP per SP) turns its 8,150 SP into ~40k
absorbed. In stand-and-trade the Arch Mage, Priest and Elementalist lose at every multiplier tried (×4 HP, ×4 damage,
×0.25 taken: 0-54 %). Their real tools (range, Fear and other crowd control, Blink) are not simulated, so their
target in §3 uses single pulls.

---------------------------------------------------------------------------------------------------------------------

## 2. Mechanisms

All six are solo-only (`options().soloRun`, the gate the talents use). None enters `MawBalanceModel` or kill
experience (`monsterHealth(member level)`, MawExperienceRules.cpp:176-193), so monsters stay MAW's for everyone.
Sim proxies in brackets: H = max HP ×, D = damage ×, T = damage taken ×, L = melee leech, C = cleave share (§3).

### M1. Lone Guard: earned class cuts act after the floor

**Change.** In a solo run the cuts a class or skill earns move from before the floor to after it, next to
legendaries 18/22: Death Knight Blood (physical) and Unholy (magic) ÷(1 + skill/100), Shaman Air ÷(1 + Air/100),
Grandmaster Shield ×0.85, Shielding ×0.85, the Shield aura. AC and resistances stay before the floor.

**Numbers.** Lich King with Body 70 and Dark 70: ×0.59 on both kinds (today ~×1). Shaman Air 70: ×0.59. Champion
with a Grandmaster shield: ×0.85. [DK T 0.59, Champion T 0.85]

**Time.** Grows with the class's own school skills, which a solo raises anyway (35,700 skill points at level 800).

**Parties.** Keep solo-only: a party DK sits near the expected character's level, where the change would be smaller
but would still move MAW's party balance.

**Cost, hooks.** Small. One flag in `MawMitigationInputs`, set in `characterMitigation` (`MawCombatRules.cpp:233-266`);
apply the listed factors inside `withFloor` (`MawCombatFormulas.cpp:226-230`) when set. Shares the post-floor clamp
with ITEMS_AND_CRAFTING's Ward (at least ×0.25 in total). Unit tests beside the existing mitigation tests.

**Risks.** Shaman Air plus its Water flat cut becomes very tanky; watch the clamp. It makes classes with cuts better
than classes without, which is the point (class identity) but needs M4 for the Champion line.

### M2. Lone Discipline: Bodybuilding to Grandmaster for every class

**Change.** A solo may train Bodybuilding one mastery above its class cap at its first promotion and up to
Grandmaster at its final one, at the usual thresholds (BM 10/24/40) and teacher prices. MAW already lifts mastery caps
for a party of one (`MawSoloMasterySkills`, `MawSkillFormulas.h:55-59`, applied in
`MawSkillRules::applyProgressionMasteries`, `MawSkillRules.cpp:1450-1485`). Regeneration stays class-locked (Troll,
Dragon, Vampire identity).

**Numbers.** Raising Bodybuilding from 40 to 77 costs ~2,200 skill points, trivial at stage 500. HP: Lich King 11.6k →
~28k (×2.4), Archangel 8.0k → ~19k (×2.4), Arch Mage 8.1k → ~13k (×1.6). Classes keep their HP per level (DK 7,
Archangel 5, Champion 8, Minotaur Lord 12), so the order of tanks is unchanged. It supersedes the "HP floor" rule R3
of BALANCE_AND_TALENTS.md §4.0. [DK and Seraph H 2.4, Arch Mage H 1.6]

**Time.** Paid in skill points and teacher gold; the final step comes with the promotion.

**Parties.** Solo-only: in a party the low-HP classes have a tank and a healer.

**Cost, hooks.** Small: the trainer's mastery cap lookup (the `soloMastery` query, `MawTrainerHints.cpp:168, 251`)
and `applyProgressionMasteries`. Teacher prices escalate × (1 + masteries held) (`MawSkillFormulas.cpp:143-151`):
leave that.

**Risks.** None beyond balance; the HP formula and tooltips already handle any mastery.

### M3. Sweeping Blows: melee area as a scaling talent

**Change.** A new melee passive (3 ranks, needs Master of the tree's skill): every melee swing also strikes up to
1 / 2 / 4 more monsters (one-handed, dual wield and two-handed: +1 at rank 3) within reach in ±60°, at 40 % + 0.25 %
per point of the weapon skill (at most 75 %; 61 % at skill 86). The Cleave active stays as the burst. This replaces
the native cleave R4 of BALANCE_AND_TALENTS.md §4.0.

**Numbers.** At 60 %: time per monster −35 to −45 %. The Seraph's Body heal on hit (DM:106-150) applies per struck
target at its share, which ties M3 to the Seraph's sustain. [C 0.6]

**Time.** Grows with the weapon skill to the 75 % cap (skill 140).

**Parties.** Solo-only; a party already has ×5 damage.

**Cost, hooks.** Medium. The talent strikes exist: `PartyAttackConfig::talentShare` / `talentExtraBlow` and
`pickTalentTargets` (TALENTS.md stage 3). Run the extra blows on every ordinary swing instead of on a cooldown; one
to-hit roll per target.

**Risks.** Experience per group is unchanged (it is per kill). Area melee against a group that includes a
Paralyzing or Exploding monster triggers more specials; R1 condition safety (BALANCE_AND_TALENTS.md §4.0) matters more.

### M4. Oaths: a class keystone at each world promotion (ascendancy)

**Change.** MAW turns final classes Elder at two worlds' promotions, Ultimate at three and Supreme at four (×1.25 /
1.5 / 1.75 HP and SP per level, `MawClassRules.cpp:175-189`, DEVIATIONS 183). In a solo run each of those steps also
grants one Oath: a pick of one from two class keystones, kept for the run (respec at a training hall for the
promotion's teacher price). An MM6-MM8 run gets two picks, a run with Chedian three. Each line gets one answer to
magic (the Elder pick) and one power or sustain pick (Ultimate). Proposed for the lines that are weak late:

| Line | Elder (defence) | Ultimate (power) | Sim proxy |
|---|---|---|---|
| Knight, Paladin | **Spellbreaker** (shield): the GM Shield cut becomes ×0.7 on every damage type after the floor; a raised shield blocks magic at half its physical rate. / **Juggernaut** (two-handed): ×0.7 damage taken after the floor while you struck in the last 2 s; no stagger | **Crusader**: 10 % melee leech (MAW's leech path, `mawLeech`, `MawClassRules.cpp:847-910`) / **Warlord**: Armsmaster damage counts double, +20 % attack speed, −10 % max HP | T 0.7, L 0.1 |
| Death Knight | **Lichborne**: Unholy's magic cut counts double (÷(1 + 2·Dark/100)) / **Blood Fortress**: the same for Blood, and Blood Leech heals ×2 | **Frost Wyrm**: Frost gives 1.5 % attack speed per point; Ice Bomb strikes everything in 4 m / **Unholy Might**: Death Coil and Death Breath +50 % | Tm 0.42 |
| Seraphim | **Sanctified**: ×0.7 magic damage after the floor / **Bulwark of Spirit**: Spirit's flat cut ×1.5 and its 25 % floor to 15 % | **Avatar**: +25 % Light attack speed; the Body heal also counts M3's targets at full / **Divine Protection** every 60 s instead of 5 minutes | T 0.7 |
| Monk | **Diamond Soul**: Grandmaster Dodging also dodges spells and missiles at half its chance | **Iron Fist**: 10 % melee leech / **Flurry**: +25 % attack speed | T 0.75, L 0.1 |
| Arch Mage, Elementalist, Lich, Warlock | **Ward**: +2 × level to all six resistances (stage 500: +1,000, magic taken 33 → ~18 %) / **Archon**: Mana Shield absorbs 10 HP per SP above the skill cap of 50 (`MawSkillFormulas.cpp:96-99`) | **Overload**: area spells +25 % per monster hit beyond the first (at most +75 %) / **Spell Surge** every 15 s | Tm 0.55 |
| Priest, Cleric, Druid | **Battle Cleric**: the Seraph's Body heal on every melee hit (DM:106-150), from the Body skill / **Martyr**: overhealing becomes a shield up to 30 % of max HP | **Zealot**: Light spells heal for 25 % of the damage dealt / **Sanctuary**: Day of Protection gives ×0.85 after the floor | — |
| Minotaur, Troll, Vampire, Dragon, archers, Assassin | one defence and one damage pick each, sized like the rows above (the four are already the strong solos: keep theirs to feel, e.g. +30 % damage) | | D 1.3 |

**Time.** Tied to promotions, which come from story progress in each world: the Oaths arrive in the mid campaign,
before the BM wall.

**Parties.** Solo-only. MAW's promotions are a party mechanic; an Oath per member would double-dip on content sized
for five.

**Cost, hooks.** Medium to large: the talents table gains `tree: oath`, `class_line` and `requires_promotion` fields
(`SoloTalentTable::loadFromYaml`), a fourth column on the Talents page, ~16 effects, most of them a number in an
existing hook (mitigation flag of M1, `mawLeech`, `mawClassAttackSpeedPercent`, the flat cut). The promotion count
is `MawRules::promotionWorlds` (`MawClassRules.cpp:178`).

**Risks.** Sixteen effects to test; start with the Knight, DK, Seraph, Monk and caster rows. A wrong pick costs a
respec, never a run.

### M5. Legend points: the farming curve (Paragon, with an atlas source)

**Change.** A second, uncapped currency. Points come from levels **only on Road to Insanity and Beyond Madness**:
one per 2 levels above 200 on BM, one per 4 on Road to Insanity, none below (POWER_GAP.md: a player buff that
helps BM trivialises Nightmare-Insanity; the difficulty is fixed at new game, so the rate is the gate). Plus one
point the first time the solo completes a dimension map of a new Power (MAW's endless map loop, COMBAT.md §6 item 6).
Four lines, free reallocation at a training hall:

| Line | Per point | Limit | Hook |
|---|---|---|---|
| Vitality | +1 % max HP (final, after Bodybuilding and Endurance) | none | `applyResourceBonuses`, `MawSkillRules.cpp:461-480` |
| Ferocity | +1 % damage (weapons, spells, breath) | none | the melee multiplier (`mawClassMeleeMultiplier`, `MawClassRules.cpp:787`) and `spellDamageScale` |
| Warding | ×0.995 damage taken, after the floor | 150 points (×0.47) | `legendaryDefense`, `MawCombatRules.cpp:2612-2619`, inside the shared ×0.25 clamp |
| Alacrity | +0.5 % attack and cast speed | 50 points (+25 %) | `mawAttackDelay` bonus percent (`MawCombatFormulas.cpp:295-298`) |

**Numbers.** Stage 500 (level 500): 150 points, e.g. 50/50/50 → H 1.5, D 1.5, T 0.78. End of BM (level ~804): ~300
points → H 2, D 2, T 0.61. Dimension maps in BM drop only once their level reaches 950 (COMBAT.md §6), so the atlas
source is post-campaign: the chase after BM is cleared.

**Time.** The experience step is 1000·L·(1 + (L − 100)·0.5 %) (`MawExperienceCurve.cpp:14-17`): 1.5M per level at 500,
3.6M at 800, so points come ~2.4 × slower per experience late. Linear lines also lose relative value (the 300th
Vitality point is +0.25 % of the total). Diminishing returns without a hard cap: farming always pays, less and less.

**Parties.** Solo-only. If ever offered to parties, at one fifth of the rate.

**Cost, hooks.** Medium: a saved `legendPoints` allocation on `Character` (save version bump, as 182 did for talents),
four hooks above, a Legend tab beside Skills / Talents. Must not feed `MawBalanceModel` or kill experience.

**Risks.** Unbounded Vitality and Ferocity: at level 1,000+ (dimension maps) a solo outgrows everything. That is the
genre's endgame; the ×0.25 total post-floor clamp keeps it mortal.

### M6. Retune the 17 talents so they keep their value

**Change.** Resolve becomes ×0.98 magic damage taken after the floor per rank (×0.90 at 5) and reads only the six
resistances MAW uses. Weapon Training, Marksman and Attunement add their percent to final damage and final HP (still
not stats, so no compounding through Might or Endurance). Shield Wall's cooldown at rank 3 drops to 30 s (uptime 20 %).
Talent points stay one per 10 levels; points beyond the table's 61 turn into Legend points on RtI/BM.

**Numbers.** Together ≈ ×1.1 HP, ×1.1 damage, ×0.9 magic taken for a full melee or caster tree: still the feel layer.

**Time, parties.** As now. **Cost.** Small: `MawSoloTalents::applyStatPassives` and the table. **Risks.** None.

---------------------------------------------------------------------------------------------------------------------

## 3. Recommended set and a target the simulation can check

**Recommended:** M1 + M2 first (cheap, they fix the DK and Seraph, the classes MAW's own rules make weak late), then
M3 and M6, then M4 (Knight, DK, Seraph, Monk, caster rows first) and M5. With ITEMS_AND_CRAFTING's Ward on top, the
post-floor layers multiply; keep one shared clamp.

**What the set does** (realfight, BM stage 500, five seeds, median; groups beaten pulling four, no potions / seconds of
fighting per monster). Columns are cumulative. "Oaths" uses the Elder and Ultimate proxies of M4's table.

| Build | Today | M1 + M2 | + M3 (C 0.6) | + M4 (two Oaths) | + M5, 150 pts (stage 500) | + M5, 300 pts (end of BM) |
|---|---|---|---|---|---|---|
| Champion, sword and shield | 1 % / 3.6 s | 2 % / 3.8 | 7 % / 2.3 | 20 % / 2.8 | 79 % / 2.4 | 94 % / 2.0 |
| Champion, two-handed | 3 % / 3.2 | 3 % / 3.2 | 10 % / 1.8 | 27 % / 2.2 | 85 % / 2.0 | 95 % / 1.7 |
| Minotaur Lord, dual | 10 % / 3.5 | 10 % / 3.5 | 17 % / 2.0 | 51 % / 2.6 | 92 % / 2.1 | 100 % / 1.7 |
| War Troll | 57 % / 16.7 | 57 % / 16.7 | 54 % / 10.5 | 59 % / 8.1 | 89 % / 5.8 | 100 % / 4.6 |
| Lich King (DK) | 1 % / 3.8 | 49 % / 6.2 | 62 % / 3.9 | 76 % / 4.1 | 95 % / 3.0 | 100 % / 2.3 |
| Archangel (Seraph) | 47 % / 4.8 | 64 % / 5.2 | 65 % / 3.4 | 86 % / 3.6 | 95 % / 2.6 | 100 % / 2.0 |
| Master (Monk) | 2 % / 3.6 | 2 % / 3.6 | 4 % / 2.1 | 16 % / 2.8 | 74 % / 2.4 | 92 % / 2.0 |
| Great Wyrm (Dragon) | 84 % / 2.0 | 84 % / 2.0 | 84 % / 2.0 | 88 % / 1.6 | 100 % / 1.0 | 100 % / 0.8 |
| Arch Mage, single pulls | 8 % | 11 % (with Ward) | — | — | 31 % | 78 % |

Rules alone (M1-M4) rescue the DK and Seraph and make every melee class a "Dragon today" candidate; the Legend points
carry the rest of the way, and the Champion, Monk and Troll need them most. On Road to Insanity and Doom at stage
500, M1-M4 alone already give every melee build 86-100 % (today, Insanity / Doom: Champion 54-59 / 70-84 %, DK 49 /
55 %, Monk 46 / 56 %, Seraph 89 / 97 %), so M5's rates there can stay low or zero. Nightmare at stage 500 is already
96-100 % today.

**Power target** (to check before tuning numbers):

| Check | Today | Target |
|---|---|---|
| BM stage 500, every melee build, pulls of 4 | 1-57 % (Dragon 84 %) | ≥ 75 % each, median ≥ 85 %, ≤ 2.5 s per monster (the Dragon today, for every class) |
| BM end (≈ 300 Legend points), every melee build, pulls of 4 | — | ≥ 90 %, ≤ 2.0 s per monster; single pulls 100 % |
| BM end, whole groups at once | — | the Dragon and Troll ≥ 90 %; POWER_GAP.md's ×120 for others is the item proposal's stage 3 territory |
| BM stage 200; Nightmare stage 500 | 86-100 %; 96-100 % | unchanged by M5 (no Legend points below level 200 or below Road to Insanity) |
| Casters, single pulls | Arch Mage 8 %, Priest 0 % | ≥ 75 % at the end of BM; until realfight models range, use the opener variant (`results_opener_*`) |
| Parties | — | identical tables and results (every mechanism gated on `soloRun`) |

**Running the check.** The table above came from a scratch copy of realfight.py (not committed) that scales each
build's harness rows before `fight()`:

```
d['hp'] *= H;  d['regen_full'] *= H;  d['regen_half'] *= H
for key in ('emp_melee_per_attack', 'breath_per_attack', 'spell_dps', 'ranged_dps', 'seraph_heal'): d[key] *= D
for row in d['grid'].values(): row[1] *= Tp; row[2:12] = [x * Tm for x in row[2:12]]    # after-floor proxies
d['leech_melee'] += L
# Cleave: player_attacks() gets a copy of the melee attack with aoe=True and dmg x (1 + 2C)/3 (full blow on the
# target, C on the others, at realfight's 75 % area share); the sim picks whichever is worth more per swing.
# Single pulls: chunks of 1 instead of 4 in evaluate().
```

Per-build values for each column: M1 + M2: DK H 2.4, Tp = Tm 0.59; Seraph H 2.4; Champion (shield) T 0.85; Arch Mage
H 1.6. M4: Champions, Minotaur T 0.7, L 0.1; Monk T 0.75, L 0.1; DK Tm 0.42; Seraph T 0.7; Troll and Dragon D 1.3;
Arch Mage Tm 0.55. M5: 150 points H 1.5, D 1.5, T × 0.78; 300 points H 2, D 2, T × 0.61. The second-order check
belongs in the harness (`SoloHarness.cpp` with `soloRun` effects on), once any of M1-M5 is built.

**Caveats.** Stand-and-trade expected values: no potions, Fear or other crowd control, range or kiting. The Seraph's
flat cut is OpenYAMM's, 25-40 % larger than MAW's (a port bug to fix separately; it lowers the Seraph rows a little).
The Oath proxies are uniform multipliers; the real keystones are conditional (shield held, attacked recently), which
the harness must model before numbers are final.

## 4. Decisions for the user

1. Talents stay the feel layer and the power curve comes from M1-M5, or the talent table itself becomes the power
   layer?
2. M5's gate: Legend points only on Road to Insanity and Beyond Madness (recommended), or every difficulty?
3. M2: Bodybuilding to Grandmaster for every class, or one step above the class cap only?
4. M4: Oaths as a pick of two per promotion, or a fixed keystone per class (simpler, no choice)?
5. M3 replaces the native cleave R4, or both?
