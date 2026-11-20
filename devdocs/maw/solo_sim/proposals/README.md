# Making a maxed solo clear Beyond Madness: proposals (2026-11-14)

The goal (user, 2026-11-14): a fully built solo character should be able to complete Beyond Madness. Grinding should
pay in real, felt upgrades, a Path of Exile–like power curve, until the character rolls through the content. Not an
immediate change: a direction (talent tree, crafting, mechanics, whatever fits).

Four independent proposals, written from the [solo simulation](../README.md) and its [results](../RESULTS.md):

| File | Angle | Numbers |
| --- | --- | --- |
| [POWER_GAP.md](POWER_GAP.md) | How much power a solo lacks, per build and difficulty ([power_gap_sweep.py](power_gap_sweep.py)) | measured |
| [TALENTS_AND_PROGRESSION.md](TALENTS_AND_PROGRESSION.md) | Talents, keystones, mastery caps, defence after the floor, Legend points | measured with scaled multipliers |
| [ITEMS_AND_CRAFTING.md](ITEMS_AND_CRAFTING.md) | One crafting currency, chosen enchants, item quality past the cap, armour Ward | formulas; hours estimated |
| [ENDGAME_LOOP.md](ENDGAME_LOOP.md) | A repeatable farm (Rift Atlas), its currency, loot past the caps, pinnacles | formulas; hours estimated |
| [DISCORD_DISTILL.md](DISCORD_DISTILL.md) | What the MAW Discord and its developer say about solo, the top difficulty and endgame (2023–2026) | quotes with dates |
| [TALENT_TREE_V2.md](TALENT_TREE_V2.md), [TALENT_TREE_V2_RESULTS.md](TALENT_TREE_V2_RESULTS.md) | The solo rules as a talent tree v2 (innate Bodybuilding, keystones, caster and ranged rows, Legend lines), simulated with range and actives; mockups in `level_generation/ui/solo_talents_v2_20261114/` | measured |
| [SOLO_RULES.md](SOLO_RULES.md) | Port checks against MAW, the leech floor explained, seven concrete solo rules and five grind layers ([solo_rules_check.py](solo_rules_check.py)) | measured |

This page merges them. Nothing here is built.

**Later direction (2026-11-15):** the user's aims for the power curve, the early game measured
([early_cut_sweep.py](early_cut_sweep.py)), the gear problem of the simulated kits and saves, and the next steps for
the simulator are in [devdocs/solo_action/POWER_CURVE_DIRECTION.md](../../../solo_action/POWER_CURVE_DIRECTION.md).

**The Discord check** ([DISCORD_DISTILL.md](DISCORD_DISTILL.md), "How this changes the recommendation") confirms the
wall: the only 5.0 BM solo is a Dragon. It finds that the 90 % reduction cap (our 10 % floor) and a barely clearable
top difficulty are deliberate MAW design. So the layer below should be an opt-in, solo-only OpenYAMM option. It
should start from what the MAW developer proposed or accepted himself:
- a solo mode with more skill points;
- a stronger solo leech (the floor itself is already in 5.0);
- flat-stat gems;
- cubes past +20 %;
- a ring per completed game.

Its farm should not let maps drop maps. [SOLO_RULES.md](SOLO_RULES.md) turns this into seven rules and five grind
layers and measures them:
- Sustain turns out to be a feel lever only.
- Bodybuilding to Grandmaster, class cuts after the floor and melee area hits carry the rules.
- Legend points carry Beyond Madness: every melee build reaches 85–100 % of pulls of four at 300 points.

## Where they agree

- **The wall is Beyond Madness itself.** At character level 500 its monsters are about level 321; on every other
  difficulty they are 226–240. Against Road to Insanity that is ×3.4 HP and ×3.0–3.4 damage. A group kills a Knight
  in about 2 s (5–6 s in Road to Insanity) while each monster takes 5–7 s to kill.
- **The gap.** A melee or bow solo at Beyond Madness L500 needs about ×14 effective power (HP × damage) to beat 90 %
  of the groups pulled four at a time. It needs about ×120 to take whole groups at a "mash" pace. At the end of the
  route the estimate is about ×60 and ×500.
- **Defence is capped.** A hit never drops below 10 % of its raw damage (`mawMitigatedDamage`,
  `game/rules/maw/MawCombatFormulas.cpp:226`). Melee solos already take 10–24 % of a hit; a sword-and-shield Champion
  sits on the floor for every type. More armour or resistance does nothing. Only these still scale:
  - HP and healing;
  - kill speed;
  - multipliers applied after the floor (legendary affixes, the class flat cut).
- **HP is capped by class.** Bodybuilding mastery counts twice in the HP formula. Death Knights and Seraphim (Expert)
  have 0.4–0.6× the HP MAW sizes monsters against; Grandmaster Minotaurs, Trolls and Dragons have about 2.7×.
- **Gear stops growing near item level 450–640.** Item power, the enchant curve, the Crafting Cube cap and the gem
  tiers all cap there. MAW's balance model already assumes capped gear, so above level 500 a level lead is worth L³,
  not L⁶: the 1.6× lead is ×35 at the end of Nightmare but ×3.6 at the end of Beyond Madness.
- **Beyond Madness has nowhere to farm.** There are no refills, resets or rewarding repeatables. Dimension maps exist
  elsewhere but climb faster than the solo, and several item reads use the level bank (about half a solo's level).
- **The current talents are a feel layer.** They give about ×1.2 damage and ×1.1 toughness and are full by about
  level 610.
- **A flat buff fails.** A player buff of ×2.75 or more turns Nightmare, Doom and Road to Insanity into a walkover.
  New power must be:
  - earned by grinding;
  - gated to Road to Insanity, Beyond Madness and the endgame farm; or
  - conditional on monsters being far above you.

## Where they differ

- **Monster side or player side.** POWER_GAP.md calls the simplest fix a Beyond Madness monster cut: about ÷3.75 HP
  and damage at the high stages, roughly Road to Insanity's numbers. That makes Beyond Madness playable but adds no
  power curve. The other three put the power on the player, earned by grinding, which is what the goal asks for.
- **How long it takes.** ITEMS_AND_CRAFTING.md's 15-hour stage gives about ×6 effective power, under the measured
  ×14, so its "90 % after 15 h" is optimistic. ENDGAME_LOOP.md's ~40 h for pulls and ~100 h for whole groups fits the
  measured gap better. Both are estimates until the farm is simulated.
- **Defence after the floor appears three times:**
  - the talents' class cuts moved after the floor (M1);
  - the items' armour Ward;
  - the Legend points' damage-taken line.

  They multiply, so they need one shared clamp (the proposals suggest no lower than ×0.25 in total).
- **Two currencies for one job:** Essence (salvage, items) and Rift Shards (drops, endgame). One should do.

## Recommended direction

One farm, one currency, three sinks. Rules fixes first, because they are cheap and measured.

1. **Measure first** (simulation work, no game changes):
   - **Calibration.** Run `realfight.py` with a character at MAW's own expected power for level 500 (ENDGAME_LOOP
     §1.7). The model says that character should beat pulls of four; 17 of 22 simulated builds do not. Every target
     below shifts if the simulated character is far below the model.
   - **Port bug.** Fix the Seraph/Shaman flat-cut deviation (`mawClassDefense`, `MawClassRules.cpp:834`, missing MAW's
     chanceToBeHit × legendaryDamageTaken factor).
   - **Ranged and Fear.** Add a ranged approach and Fear to the fight model. Today the Dragon, Archer and casters are
     judged as melee.
2. **Rules fixes, solo only** (talents M1, M2; items M2):
   - **Class cuts after the floor.** The Death Knight's Body/Dark and Seraph-like cuts start to matter again.
   - **Bodybuilding to Grandmaster for every class** through promotions.
   - **Choosing enchant types.** Endurance in place of wasted Intellect and Personality, about ×2 HP.
   - **Measured effect at Beyond Madness L500, pulls of four:** the Death Knight goes from 1 % to 49 % and the Seraph
     from 47 % to 64 %.
3. **The farm: Rift Atlas** (endgame M1, M3, M6):
   - repeatable dimension maps at a tier the player chooses, in every mode including Beyond Madness;
   - a next map on every clear;
   - loot whose caps continue past today's (item power to 255, enchant curve to 175);
   - a guardian every 10 tiers with a drop for a slot you choose;
   - MAW's monster model stays capped and pinned by a test, so monsters never follow these gains.
4. **One currency, from rift drops and salvage** (items M1 merged with endgame M2). It has three sinks:
   - **Ascension:** item quality past 20 % at a rising cost, about ×1.8 weapon damage at full quality.
   - **Ward:** the same Ascension on armour cuts damage after the floor, inside the shared clamp.
   - **Legend points:** uncapped points for HP, damage, damage taken and speed (talents M5), earned only on Road to
     Insanity, Beyond Madness and in rifts.
5. **Identity layer** (talents M3, M4, M6):
   - **Oaths:** one class keystone at each world promotion, one against magic and one for damage or healing.
   - **Sweeping Blows:** melee hits nearby monsters too.
   - **Retuned talents** that keep their value.

**Targets** (realfight, Beyond Madness, the route's real groups, no potions):

| When | Pulls of four | Whole groups | Seconds per monster |
| --- | --- | --- | --- |
| Today, stage 500 | Dragon 84 %, Troll 57 %, Seraph 47 %, others 0–10 % | – | 2–17 |
| Rules fixes and Oaths, stage 500 | every melee build ≥ 75 %, median ≥ 85 % | – | ≤ 2.5 |
| About 40 h of rifts | every melee and bow build ≥ 90 % | ≥ 50 % | ≤ 4 |
| About 100 h of rifts | 100 % | ≥ 90 % | ≤ 1.5 ("mash") |
| Nightmare to Road to Insanity, no grinding | unchanged | unchanged | unchanged |
| A party of five | the same stage at about 5× the hours per member | | |

**Next measurement step:** add a rift phase to `harness/SoloRoute.cpp` (specified in ENDGAME_LOOP §3). The phase picks
a tier, builds runs from real group sizes, books loot and currency, re-gears, and charges time per run. Then
`realfight.py` turns the hours-versus-power targets above from estimates into measurements.

## Decisions for the user

1. **Where the power comes from:**
   - grinding on the player side (recommended, matches the goal);
   - a Beyond Madness monster cut (÷3.75);
   - both.
2. **Who gets what:**
   - the rules fixes and Legend points for solo only, as the talents are;
   - the farm and currency for everyone, with parties needing about 5× the hours per member.
3. **Where power can be earned:** decided 2026-11-14: every difficulty of the MAW solo run, no gate (SOLO_RULES.md §6).
   The rules become solo-run talents, and grinding pays talent and Legend points.
4. **Talents:** stay the feel layer (the 2026-11-13 decision) with the curve from the systems above, or become the
   power layer themselves.
5. **Bodybuilding:** Grandmaster for every class, or one step above the class cap.
6. **Oaths:** a pick of two per promotion, or one fixed keystone per class.
7. **The shared clamp** for everything after the floor (×0.25 proposed).
8. **The experience curve** to balance against: MAW's current 0.5 % per level past 100, or the 1 % of earlier 5.0
   releases that the Discord players played.
