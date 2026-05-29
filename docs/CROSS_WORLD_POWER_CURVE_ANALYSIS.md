# Cross-World Power Curve Analysis

This document compares the combat power curves visible in the current OpenYAMM data for the merged MM6-MM8 style
runtime and the imported MM9 data. It focuses on what a party would face when worlds are mounted together and players
can move between MM6, MM7, MM8, and MM9 continents.

## Source Data

Measured sources:

- Classic MM6-MM8 merged monster table: `assets_dev/engine/data_tables/monster_data.txt`
- Classic class HP/SP scaling: `assets_dev/engine/data_tables/class_multipliers.txt`
- Classic items, artifacts, relics, and special items: `assets_dev/engine/data_tables/items.txt`
- Classic standard and special enchant tables:
  - `assets_dev/engine/data_tables/standard_item_enchants.txt`
  - `assets_dev/engine/data_tables/special_item_enchants.txt`
- Classic placed monsters: `assets_dev/worlds/mm6/maps/*.scene.yml`,
  `assets_dev/worlds/mm7/maps/*.scene.yml`, and `assets_dev/worlds/mm8/maps/*.scene.yml`
- MM9 monster source table: `assets_dev/worlds/mm9/source/data/MONSTERS.txt`
- MM9 actor source table used as a related reference: `assets_dev/worlds/mm9/source/data/ACTOR.txt`
- MM9 weapon and unique item list: `assets_dev/worlds/mm9/source/data/MASTERITEMLIST.csv`
- MM9 skill descriptions: `assets_dev/worlds/mm9/source/data/SKILL AND MASTERY DESC.csv`
- MM9 placed monster-like DAT objects from generated scene compatibility files:
  `assets_dev/worlds/mm9/maps/*.scene.yml`
- Runtime formulas:
  - `game/gameplay/GameMechanics.cpp`
  - `game/party/Party.cpp`
  - regression tests under `tests/GameplayRuleRegressionTests.cpp`, `tests/CharacterSheetRegressionTests.cpp`,
    and `tests/PartyRegressionTests.cpp`

Method notes:

- Classic density uses `initial_state.actors[*].monster_info_id` in generated scene YAML.
- MM9 density uses `model_instances[*].source_class` matched back to MM9 monster table names, base names, or model names.
  This intentionally excludes obvious props and chests. Some DAT object classes remain unmatched, especially civilians,
  shopkeepers, props, and numbered/variant classes such as `Magreeb2`.
- The MM9 matched-placement numbers should be read as conservative hostile/monster-like counts, not a complete population
  inventory.

## Monster Table Curves

Raw table summary:

| Table | Rows | Median level | Median HP | Median AC | Median primary attack avg | Median EXP | Median recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Classic MM6-MM8 merged monsters | 652 | 19 | 93 | 14 | 16 | 504 | 80 |
| MM9 monsters | 134 | 30 | 225 | 24.5 | 23 | 1800 | 30 |

Level-binned medians:

| Level band | Classic count | Classic HP/AC/dmg/EXP | MM9 count | MM9 HP/AC/dmg/EXP |
| --- | ---: | --- | ---: | --- |
| 1-5 | 159 | 6 / 5 / 3 / 24 | 9 | 11 / 8 / 5 / 59 |
| 6-10 | 75 | 30 / 8 / 8 / 144 | 12 | 37 / 10 / 9.5 / 236.5 |
| 11-20 | 122 | 73 / 14 / 14 / 416 | 29 | 95 / 15 / 14 / 689 |
| 21-35 | 113 | 162 / 20 / 22.5 / 1064 | 30 | 225 / 24.5 / 23.8 / 1800 |
| 36-60 | 113 | 374 / 35 / 38 / 2475 | 36 | 525 / 35 / 38.5 / 4500 |
| 61-100 | 69 | 880 / 66 / 55 / 7200 | 16 | 945 / 75 / 51.5 / 8400 |
| 101+ | 1 | 1937 / 100 / 72 / 16875 | 2 | 22800 / 250 / 134 / 41500 |

The MM9 monster table is not just shifted upward in level. It also compresses action cadence: median recovery is 30
instead of 80. If recovery units are consumed similarly, a median MM9 monster gets actions far more often than a median
classic monster. Even where MM9 level-band damage looks close to classic damage, action frequency and HP usually make the
actual threat higher.

MM9 also has a much harder boss outlier shape. Classic merged data has one row above level 100, while MM9 has level-500
style rows with tens of thousands of HP. These cannot be allowed into a shared encounter economy as ordinary level values.

## Placed Monster Density

Classic generated scenes:

| World | Maps | Combat maps | Placed actors | Median actors per combat map | P90 actors per combat map | Weighted median level / HP / AC / dmg / EXP |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| MM6 | 73 | 28 | 377 | 1 | 45.1 | 2 / 6 / 5 / 3 / 24 |
| MM7 | 79 | 38 | 826 | 7 | 55.8 | 3 / 9 / 6 / 3 / 39 |
| MM8 | 71 | 25 | 507 | 6 | 69.2 | 18 / 86 / 0 / 18 / 504 |

Top dense examples:

| World | Map | Count | Median level | Median HP | Median dmg | Total EXP |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| MM6 | `outc2` | 58 | 2 | 6 | 3 | 1659 |
| MM6 | `znwc` | 55 | 1 | 3 | 3 | 1268 |
| MM7 | `7out02` | 142 | 4 | 13 | 5 | 16491 |
| MM7 | `7d29` | 63 | 17 | 79 | 18 | 24923 |
| MM8 | `out02` | 143 | 18 | 86 | 30 | 106225 |
| MM8 | `d50` | 80 | 31 | 189 | 41 | 115429 |

MM9 matched monster-like scene objects:

| Matched maps | Matched objects | Weighted median level / HP / AC / dmg / EXP |
| ---: | ---: | --- |
| 15 | 447 | 18 / 103 / 14 / 15 / 756 |

Top matched MM9 examples:

| Map | Count | Median level | Median HP | Median dmg | Total EXP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mountainpass` | 76 | 20 | 120 | 25 | 96592 |
| `sturmford` | 56 | 4 | 15 | 6.8 | 13416 |
| `yorwick` | 48 | 44 | 423 | 35 | 139474 |
| `isleofashes` | 46 | 3 | 11 | 5 | 19281 |
| `thronheim` | 44 | 20 | 120 | 16 | 43882 |
| `guberland` | 40 | 6.5 | 26.5 | 8 | 16614 |

This is the main content-curve problem:

- MM6 and MM7 contain many dense maps that are still weighted toward very low-level placed actors.
- MM8 starts substantially higher, with several dense maps already around classic mid-game values.
- MM9 placement, after conservative matching, looks closer to MM8 mid-game density but has much higher table rewards and
  a faster action cadence.

## Party Scaling

Classic class HP/SP scaling is table-driven:

| Class | Base HP | HP/level | Base SP | SP/level | Mana stat |
| --- | ---: | ---: | ---: | ---: | --- |
| Knight | 35 | 5 | 0 | 0 | none |
| Champion | 35 | 8 | 0 | 0 | none |
| Archer | 30 | 3 | 5 | 1 | Intellect |
| Sniper | 30 | 6 | 5 | 3 | Intellect |
| Cleric | 30 | 2 | 15 | 3 | Personality |
| PriestLight | 30 | 3 | 15 | 5 | Personality |
| Sorcerer | 20 | 2 | 15 | 3 | Intellect |
| Lich | 20 | 3 | 25 | 6 | Intellect |
| Dragon | 50 | 10 | 50 | 5 | Intellect |
| GreatWyrm | 50 | 10 | 50 | 10 | Intellect |
| Troll | 45 | 5 | 0 | 0 | none |

Runtime HP/SP formulas in `GameMechanics.cpp` add base + per-level scaling, then effective stat bonus, plus direct
Bodybuilding or Meditation skill bonuses. Experience required for the next level is:

```text
1000 * currentLevel * (currentLevel + 1) / 2
```

Training grants skill points as:

```text
5 + newLevel / 10
```

Shared combat experience is split only across characters able to receive it, then Learning adds a per-character bonus:

| Learning mastery | Bonus percent |
| --- | ---: |
| Normal | 9 + skill |
| Expert | 9 + 2 * skill |
| Master | 9 + 3 * skill |
| Grandmaster | 9 + 5 * skill |

This means a high-Learning party converts dense high-EXP regions into accelerated level gain. MM9's median monster EXP
is 1800 versus 504 in the classic merged table, so bringing MM9 rewards over unmodified would quickly inflate the shared
party curve.

## Item, Artifact, And Skill Damage

Classic weapon table base damage by material:

| Material | Count | Median base+mod avg | Max base+mod avg | Examples |
| --- | ---: | ---: | ---: | --- |
| Normal material 3 | 34 | 9.8 | 21 | Stellar Bow, Devilbone Bow, Griffin Bow |
| Normal material 5 | 23 | 14 | 26.5 | Headsman's Poleaxe, Grand Poleaxe, Minotaur Axe |
| Normal material 6 | 84 | 10.8 | 28 | Minotaur Herdsman Axe, Labyrinth Grapple |
| Normal material 8 | 37 | 14 | 28 | Headsman's Reaver, Dragonning Blade |
| Artifact | 29 | 22.5 | 33 | Charele, Volcano, Guardian |
| Relic | 22 | 22.2 | 31 | Finality, Hercules, Amuck |
| Special | 14 | 22.2 | 31 | Axe of Balthazar, Zokarr's Axe, Noblebone Bow |

Classic high-end weapons are not just bigger dice. They carry large stat boosts, skill boosts, speed/recovery effects,
slaying multipliers, elemental adders, vampiric effects, and defensive side effects. Examples visible in the item table:

- Artifact/relic weapons commonly sit around 20-33 average base weapon damage before character Might, skill, Armsmaster,
  enchantment, and multi-attack effects.
- Special weapon bonuses add fixed or dice-based elemental damage, double damage against families, recovery reduction,
  vampiric healing, and explosive/carnage effects.
- Standard enchant levels add +1 to +25 stat/skill/resource/AC/resistance values depending on item level and slot.
- Special enchantments include +10 all stats, +10 all resistances, +5 character level, 50 percent magic school boosts,
  half missile damage, regeneration, and multiple slaying effects.

MM9 weapon table by item level:

| MM9 item level | Count | Median avg | Max avg | Examples |
| ---: | ---: | ---: | ---: | --- |
| 1 | 11 | 5 | 10.5 | Halberd, Hammer, Flail |
| 2 | 13 | 6 | 12 | Throwing Axe, Ronenguard Bill |
| 3 | 10 | 7.2 | 10.5 | Yagar Axe, Composite Bow |
| 4 | 11 | 8 | 12 | Battle Witch, Regimental Halberd |
| 5 | 12 | 10 | 12 | Flamberge, The Chopper |
| 6 | 27 | 10.5 | 30 | Mevan Sword, Stouka Couta, Blutterbunger |

MM9 unique weapons have a wide spread. The top outliers are competitive with classic artifacts, but many level-6 named
weapons have only normal mid-tier dice and rely on item effects, set effects, or recovery rather than raw dice.

MM9 skill descriptions show a related but not identical scaling model:

- Weapon skills add attack bonus at Normal, often damage at Expert, and multi-attack or recovery improvements at Master
  or Grandmaster.
- Armor, Shield, Dodge, Bodybuilding, Meditation, Learning, and Armsmaster have direct defensive/resource/progression
  effects.
- MM9's skill list is less school-granular for magic than MM6-MM8, using Elemental, Light, Dark, and Spirit instead of
  the classic nine schools.

## Combat Mechanics Differences

Current OpenYAMM classic runtime formulas:

- Monster hit chance rolls `1..(targetAC + 2 * monsterLevel + 10)`, then hits if `roll + attackBonus > targetAC + 5`.
- Monster damage is direct dice + bonus.
- Monster resistance can halve incoming non-irresistible damage up to four times based on resistance rolls.
- Character attack profiles combine item dice, Might bonus, skill damage, Armsmaster-like effects, enchantment bonuses,
  permanent bonuses, magical bonuses, and attack recovery.
- Character ranged attacks select dragon breath, blaster, wand, bow, or fallback melee depending on equipment and range.
- Party progression is level-gated by experience, training, and skill-point expenditure.

MM9 content brings different assumptions:

- Its source monster recovery values are commonly much lower than classic values.
- Its table rewards are higher at comparable practical encounter tiers.
- Its maps tend to be real-time first-person spaces with DAT object placement rather than the classic actor/spawn model.
- Its skills and magic schools need semantic mapping, not a raw one-to-one copy of classic skill ids.

The safest conclusion is that raw monster level is not a portable power scale between MM6-MM8 and MM9.

## Design Implications

1.  A single "level equals level" comparison will fail.

    MM9 level 20 often behaves closer to a classic higher-threat actor because of HP, recovery, reward, and encounter
    cadence. Classic MM6 and MM7 placed actors can be extremely numerous but individually weak.

2.  Density matters as much as table stats.

    MM7 `7out02` has 142 placed actors at low median level. MM8 `out02` has 143 actors at median level 18 and more than
    100k table EXP. MM9 `mountainpass` has 76 matched monster-like objects at median level 20 and nearly 97k table EXP.

3.  Party power is item and skill dominated by mid-to-late game.

    HP per level is predictable, but actual survivability and damage are dominated by artifacts, relics, enchantments,
    Armsmaster/weapon mastery, multi-attacks, spell buffs, resistances, and recovery reduction.

4.  Rewards are part of balance, not just monster difficulty.

    If MM9 rewards stay raw while classic progression remains raw, a party can over-level the classic continents quickly
    after clearing MM9 mid-tier content.

5.  Boss rows and special encounters need explicit encounter classification.

    MM9 level-500 and similar rows should never be scaled by a generic formula that treats level as linear.

## Proposed Cross-Continent Solution

### 1. Introduce An Effective Encounter Power Rating

Add a data-derived power rating used by runtime bolstering, reward scaling, and travel warnings. Do not use raw level as
the shared scale.

Suggested monster power inputs:

- Table level, but capped or transformed logarithmically for boss outliers.
- Effective HP.
- Effective AC against a reference party hit profile.
- Primary and secondary attack average damage.
- Recovery/action frequency.
- Ranged/spell use probability.
- Damage type and special attack tags.
- Resistances and immunities.
- Placed group count and local encounter clustering.

Suggested rough score shape:

```text
monster_power =
    hp_factor
  * offense_factor(avg_damage, recovery, ranged_or_spell_pressure)
  * defense_factor(ac, resistances, immunities)
  * special_factor
```

Then:

```text
encounter_power = sum(monster_power for active group)
map_pressure = percentile(encounter_power over map-local clusters)
```

The exact constants should be tuned from regression scenarios, but this shape is better than using level alone.

### 2. Keep Native Continent Curves As Authored

When the party is playing a continent's native progression, prefer original table stats and authored density:

- MM6 early areas should remain low-stat, high-learning beginner content.
- MM7 can keep its wider low-level outdoor density and mid-game dungeon spikes.
- MM8 should remain a higher-starting continent.
- MM9 should retain its own encounter identity, but its runtime action cadence and reward output must be normalized when
  hosted inside the shared engine.

This avoids flattening all worlds into one generic curve.

### 3. Use Continent Entry Bands

Define continent bands in world or map metadata:

| Band | Intended party state |
| --- | --- |
| Starter | Fresh or near-fresh party |
| Early | First promotions, low enchantment access |
| Mid | Several trained levels, basic expert/master skills |
| High | Artifacts/relics possible, broad master/GM access |
| Epic | Endgame, boss rows, extreme resistances and unique mechanics |

Travel can be open, but map pressure should be visible to systems:

- Low-band party entering high-band content: scale rewards conservatively, warn through map metadata/UI if desired, and
  avoid silently downscaling unique bosses.
- High-band party entering low-band content: optionally bolster normal monsters toward a minimum challenge floor, but do
  not inflate quest-critical peasants, civilians, or scripted set pieces.

### 4. Normalize MM9 Combat Runtime Values Into Shared Semantics

For MM9-hosted monsters, import source table values into the shared actor schema with explicit interpretation fields:

- `source_world: mm9`
- `source_recovery_model: mm9`
- `effective_recovery_seconds` or equivalent shared action cadence
- `effective_reward_scale`
- `encounter_power_override` for bosses and special scripted fights

Do not hide this behind generic compatibility behavior. Make the MM9 interpretation explicit in the imported data or in
the MM9 monster loader, then feed the normal shared gameplay systems.

Important normalization targets:

- Recovery/action cadence: MM9 median recovery is 30 while classic median is 80. Decide whether MM9 recovery values
  represent the same unit before using them directly. If not, convert them at import or table-load time.
- Rewards: MM9 median EXP is about 3.6x the classic median. Rewards should be scaled by effective encounter power and
  intended continent band.
- Boss rows: cap raw level contribution and use explicit boss power profiles.

### 5. Add Party Power Rating

Use party power rather than average level for dynamic decisions.

Suggested party power inputs:

- Effective HP and SP after class table, stats, Bodybuilding, Meditation, and temporary level modifiers.
- Effective AC and resistances after equipment, buffs, and artifact effects.
- Best melee and ranged attack profiles per member:
  - damage range
  - attack bonus
  - recovery
  - multi-attack effects
  - slaying effects against current monster family
- Spell access and spell skill/mastery.
- Consumable and wand access if those are treated as normal combat resources.
- Artifact/relic/special item count and item power rating.
- Learning skill should affect progression forecasts, not direct combat power.

This lets a level-20 artifact-loaded party and a level-20 weak-equipment party produce different scaling decisions.

### 6. Scale Rewards With Encounter Power

Reward scaling should be explicit:

```text
reward_multiplier = adjusted_encounter_power / native_encounter_power
```

Then clamp by continent band. This keeps high-level party bolstering from producing absurd leveling loops and prevents
MM9's raw reward table from trivializing MM6-MM8 progression.

Learning should apply after the final shared reward, preserving the existing character-specific bonus behavior.

### 7. Gate Or Classify Artifacts By Item Power

Create item power ratings for artifacts, relics, specials, and high-tier MM9 uniques. Inputs:

- Base dice and recovery.
- Stat boosts.
- Skill boosts.
- Damage adders.
- Slaying multipliers.
- Defensive immunities/resistances.
- Regeneration, missile shielding, vampiric effects, and spell-school boosts.
- Negative side effects.

Use this rating for random generation and cross-continent balancing:

- Starter and early continents should not randomly produce high-power artifacts unless the original content explicitly
  placed them.
- If a high-power artifact is obtained early through an authored quest, accept it as authored and let party power rating
  react to it.
- Do not remove or nerf unique items silently. Use item power to adjust future encounter pressure and reward prediction.

### 8. Treat MM9 As A Core Content Package With A Tuned Challenge Profile

MM9 should not be bolted on as a separate ruleset. It should be mounted as core content with a world-local challenge
profile:

```yaml
challenge_profile:
  source_curve: mm9
  native_start_band: early
  recovery_interpretation: mm9_dat
  reward_scale_policy: encounter_power
  boss_level_policy: explicit
```

The loader can then convert MM9 source data into shared runtime stats while preserving provenance.

### 9. Build Regression Coverage Around Representative Encounters

Recommended test fixtures:

- MM6 low-density and high-density early outdoor encounters.
- MM7 dense outdoor map such as `7out02`.
- MM8 high-density mid/high map such as `out02` or `d50`.
- MM9 `sturmford`, `mountainpass`, `yorwick`, and a boss/special map.
- Party presets:
  - fresh party
  - level 10 no artifacts
  - level 25 normal equipment
  - level 40 with several artifacts
  - high-Learning party for reward-growth checks

Each fixture should assert:

- imported placed actor count or matched MM9 monster-object count;
- median and total encounter power;
- expected reward range after scaling;
- no generic boss row is accidentally treated as linear level content;
- classic authored content remains unchanged when no cross-world scaling is active.

## Recommended Initial Implementation Order

1.  Add an offline analysis tool or test helper that computes monster power from the existing classic and MM9 tables.
    Keep it deterministic and table-driven.

2.  Add world/map challenge metadata for starter/early/mid/high/epic bands.

3.  Add item power rating for artifacts, relics, specials, and MM9 unique weapons.

4.  Add party power rating using existing `GameMechanics::buildCharacterAttackProfile`, effective HP/SP, AC,
    resistances, and item power.

5.  Convert MM9 monster recovery and reward semantics explicitly at import/load time before they enter shared combat.

6.  Apply optional dynamic bolstering only where map metadata allows it:
    normal hostile monsters yes, civilians and scripted bosses no unless explicitly opted in.

7.  Add reward scaling after monster stat scaling and before Learning bonuses.

8.  Cover representative maps and party presets with focused regression tests.

## Bottom Line

MM6-MM8 and MM9 can coexist, but not by treating raw level, HP, or EXP as directly comparable. The shared scale should be
an effective encounter power rating that includes HP, AC, damage, recovery, special attacks, resistances, density, party
power, and item power. Native content should keep its authored feel, while cross-continent play should use explicit
world/map challenge profiles, MM9 source-value normalization, item power classification, and reward scaling.
