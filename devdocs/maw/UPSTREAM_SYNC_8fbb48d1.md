# MAW upstream sync: ef23ee17 → 8fbb48d1

Our MAW ruleset was ported from MAW `ef23ee17` (2026-10-22). MAW `origin/main` is now `8fbb48d1` (2026-11-04): 55
commits, 31 files, +1641/−133 lines. This file lists every net change (reverted work such as the hireling XP
multiplier is left out), where it lands in OpenYAMM and what we should do. Paths on the MAW side are relative to
`Maw-Mod-MMMerge/Scripts/`. Status 2026-11-05: implemented, except the decisions in §10 (see there for what was built and how it was checked).

Legend: **Port** = change our code/data to match; **Decide** = needs a user decision; **Have** = we already match or
do better; **N/A** = engine/multiplayer plumbing with no equivalent.

## 1. Balance (largest gameplay effect)

All of these are in commits "balance pass 1", "reduced spell damage", "better assumptions", "formula fix" and
"small fix".

| # | MAW change | Ours | Action |
|---|---|---|---|
| B1 | Player armour vs monster level: `Formulas.armorDivisorPerLevel` 6 → 1 (`AC / (200 + L)`); used for real damage taken (zzMaw-Stats.lua:1060) and the estimate | `MawCombatFormulas.cpp:234` `200 + 6 * level`; `MawBalanceModel.cpp:672` | **Port** both. Armour becomes far stronger at high monster levels |
| B2 | Player resistance vs monster level: `resistanceDivisorPerLevel` 12 → 1 (`R / (100 + L)`) | `MawCombatFormulas.cpp:266` `100 + 12 * level`; `MawBalanceModel.cpp:678`; check the sheet's "share removed" (`SkillRules::resistanceCut`) uses the same function | **Port** |
| B3 | Spell damage: `spellSkillBase` 1.025 → 1.02 and a new `spellDamageMult = 0.7` on dice and add of every damage spell (`ascendSpellDamage`, zzMaw-Spells.lua:2079) and in the spell-power estimate | `mawAscendedSpellDice` (`MawCombatFormulas.cpp:332-340`) uses 1.025 and no 0.7; `MawBalanceModel::spellPower` lines 800-801 | **Port**: 1.02 everywhere; ×0.7 in the damage path and the model. Keep the Ascension tooltip's percents without the 0.7 (MAW's tooltip shows `spellAddScale` only) — `MawSkillRules.cpp:499` calls `mawAscendedSpellDice`, so split the 0.7 out |
| B4 | Estimate: `STAT_SHARE` 0.25 → 0.2 (share of worn enchants counted as stats) | `MawBalanceModel::stat` line 583 `* 0.25` | **Port** |
| B5 | Estimate: flat HP from enchants now `totalEnchantPower × 0.2 × geared × (1 + min(strength/50, 5))`, strength = max enchant strength at the level (was `stat/10 × min(1 + stat/500, 5) × 4`) | `MawBalanceModel::health` lines 604-605 | **Port** |
| B6 | Estimate: cover gate `{0, 1}` → `{0, 1, 1, 1}` (Master/GM now count); tank vitality ratio fixed at 2 (was `1 + 6L/(L+240)`) | `MawBalanceModel.cpp:80` `CoverGate`, line 702 | **Port** (and fix the comment at line 78) |
| B7 | Estimate: `getMeleeSkill` no longer ×1.5 (`skill + 10 × legendaryRamp`); armsmaster and spell paths keep ×1.5 | `MawBalanceModel::attack` line 717, `power` line 747 | **Port** (only `meleeSkill`; leave `armsSkill`) |
| B8 | Monster damage per damage kind: `getPlayerEstimatedVitality(lvl, kind)` uses physical-only mitigation for physical attacks and magic-only for everything else (no 50/50 blend); `getMonsterDamage(mon, lvl, kind)` used for attack 1, attack 2, spells and the info box. Map affix 14 (attacks become magic) rescales by magic/physical damage | `MawBalanceModel::vitality`/`monsterDamage` (one blended value); `MawMonsterRules.cpp:578-596` sets `attack1Damage` and `attack2Damage` from it; spells use `attack1Damage` × `mawMonsterSpellMultiplier` | **Port**: `vitality(level, optional<CombatDamageType>)`, per-kind cache; compute attack 1/2 from their own types and the spell from its element; rescale under affix 14. Traps (`MawCombatRules.cpp:2290`) keep the blended value as MAW does. Check `MawMonsterInspect` shows the per-kind numbers |
| B9 | Bolster experience banked = the sum of each member's *capped* award (`experienceAwarded`), not the uncapped `experience × healthRatio` | `mawMemberKillExperience`, `MawExperienceRules.cpp:186` `share.banked = experience * healthRatio` | **Port**: `banked = award` |

B1-B8 shift the whole curve (monster HP/damage are fitted from the model), so re-run the balance tests and the
`testparty` stages after porting, and refresh BALANCE_MODEL.md.

## 2. New boss affixes

Commits "added 3 new bosses", "new boss". `SkillList` gains **Unstoppable, Berserker, Cryptic, Skilled** (rolled like
the other 14; an Omnipotent boss does *not* get them and does not spawn them on death, `OmnipotentExcluded`). Boss
skill is now read through `getBossSkill(mon)` (the stored effective skill, not the name's first word), which is what
makes Cryptic work.

| Affix | Effect in MAW |
|---|---|
| Unstoppable | Immune to all crowd control: CC targeting and splash skip it, `checkDebuffDuration`/`calcDebuffDuration` return 0, no Stun spell stun (`stage_stunSpellPrime`), no retaliation stun |
| Berserker | Damage × (2 − HP/maxHP): up to double at low HP (`getMonsterDamage`) |
| Cryptic | Named "Cryptic X" but carries a hidden random other affix (seeded in Madness: `getCrypticSkill`) |
| Skilled | 40 % of the party's weapon hits miss it (`PlayerHitOrMiss`); its hits cannot be dodged (no speed dodge, Dodging GM chance 0); drops 4 Horseshoes (656) on death |

Ours: `MawBossAffix` (`MawMonsterRules.h:240`), names `MawMonsterRules.cpp:366`, roll list `:34-50`,
`mawHasBossAffix` (Omnipotent covers every affix `< Broodlord`).

**Port**: append the four after `Omnipotent` (the value is saved in `ActorRulesetFacts::bossAffix`; do not renumber),
add them to the roll list, keep `mawHasBossAffix`'s Omnipotent rule to the original 14, and add an "effective affix"
for Cryptic (a second saved byte → save version bump). Hooks: CC application and DR (`MawSpellFormulas`/`MawCombatRules`
crowd control, stun chance, retaliation stun), monster damage (Berserker, at hit time from current HP), the party hit
roll and dodge (`mawGrandmasterDodgeChance`, `mawChanceToBeHit` path), kill drops. Tests per affix.

## 3. Spells and skills

| # | MAW change | Ours | Action |
|---|---|---|---|
| S1 | Dragon Fear (122) reads its CC power from the **Dragon Ability** skill (CCMAP School was Mind, which dragons lack, so it always lasted the Novice duration); a new `MonsterAttacked` handler re-applies the debuff through `applyCCDebuff` (Ascension, resistance, diminishing returns) | `mawCrowdControlSpell` 122 `{4, 2, false, true}` (`fixed`), DEVIATIONS 19 keeps MAW's flat Novice duration on purpose | **Port**: drop `fixed`, read the Dragon Ability mastery/skill; update DEVIATIONS 19 |
| S2 | Monster-missile homing made frame-rate independent: lock cone (0.5/3)° per game tick × ticks elapsed (max 32), about 21° per real second | DEVIATIONS 181: 300° a second (user, 2026-10-27) | **Have** (ours is the user's firmer choice). Update DEVIATIONS 181's MAW column |
| S3 | Ascension tooltip uses the effective Ascension (Elementalist/Shaman average) and adds a "Control spells mana cost" row (`ccManaScale`); mana in green when cheaper than base | `MawSkillRules.cpp:493-506` already reads per-use Ascension | **Port** the CC mana row and the green-below-base colouring in `texts.yml:857` |
| S4 | Dagger Master and Dodging GM descriptions now state the real formulas | `texts.yml:736-826` already describe them correctly | **Have** |
| S5 | Healing/mana formulas moved into `Formulas` (`healScalingScale`, `spellManaScale`, `ccManaScale`): same numbers | — | **Have** |
| S6 | Push (dragon breath knockback) list cleared on map load; dragon push skipped at monster level 0 | `mawDragonPushDistance` clamps level ≥ 1; world pushes do not survive a load | **Have** |
| S7 | `stage_stunSpellPrime` restored the Earth resistance into the wrong slot (`const.Skills.Earth`) | our stun does not zero resistances | **N/A** |
| S8 | Old-save Learning conversion loop fixed (stopped at the first converted member) | MAW save migration | **N/A** |

## 4. Hirelings and NPC texts

| # | MAW change | Ours | Action |
|---|---|---|---|
| H1 | Scholar (4) / Teacher (13) / Instructor (14): Ascension +2/+4/+6 (was +5/+10/+15), only for members who have learned Ascension (Learning), best one counts | `hiredNpcSkillBonus` (`NpcFollowerRuntime.cpp:242-247`) is shared with Standard: 5/10/15, given to everyone | **Port** as a ruleset hook (Standard keeps MMMerge's values); the "learned only" test at the member, e.g. in `Party.cpp:2124` or a `SkillRules` hook |
| H2 | Merchant: Gypsy 48 +3, Negotiator 49 +4, Duper 50 +8 restored | same table already has them | **Have** |
| H3 | `zzMAW_SkillTextCompatibility.lua`: trainer speeches 414-416, 1382-1384, 1950-1951 rewritten for Ascension; hints 519-521, 1480-1481, 1988 and topics 414-416, 1058-1060, 1571-1572 say Ascension; topics 1031-1033 Diplomacy → Alchemy; legacy 1946-1947; follower descriptions 2324, 2333, 2334 (Ascension +2/+4/+6), 2343/2344 (Counselor/Barrister: no bonus), 2369 (Negotiator +4 Merchant) | `npc_topic_text.txt` still says "Learning ... experience" (414, 519, 1950, 2324, 2333, 2369); the ruleset patches `npc_topic.txt` but not `npc_topic_text.txt` | **Port**: add an `npc_topic_text.txt` patch to `ruleset.yml` with these rows; check `teacherSpeech` still finds the numbers |

## 5. Artifacts

`zzzMaw_Artifacts.lua`, `zzMaw-Items.lua`, `Tooltip.lua` ("fixed artifacts", "fixes"). Our MAW artifacts keep
Standard's powers (`ItemEnchantRuntime.cpp`) and take stats/on-hit/swiftness from `rulesets/maw/data/items.yml`.

| # | MAW change | Ours | Action |
|---|---|---|---|
| A1 | Justice (1329): on-hit 0.8 physical, ×2 vs Undead | `items.yml:101` has no `on_hit` (Standard has the ×2 vs Undead) | **Port**: `on_hit: {kind: Physical, damage: 0.8, versus: {Undead: 2}}` |
| A2 | Thor (2021): also knocks the target back (force 800 × power/L^0.75, the dragon push formula with the artifact's spell power) | Lightning Bolt only (`MawCombatRules.cpp:3066`) | **Port** via `pushActor` |
| A3 | Swift (−20 recovery) also on Elderaxe 504, Wyrm Spitter 506, Longseeker 512, Herald's Boots 518, Lightning Crossbow 532 | Standard gives 504/512/518/532 `attackRecoveryReductionTicks`, which MAW's delay ignores; `items.yml` has `attack_delay: 0.9` only on 515, 1302, 2024, 2025 | **Port**: `attack_delay: 0.9` on the five |
| A4 | An artifact's resistance above its flat part counts as *enchant* resistance (the separate pool, max not sum: `vars.normalEnchantResistance`) | `MawItemRules::applyItemEffects` artifact branch adds the budget to base resistances | **Port**: route the budget's resistance stats into `itemResistanceEnchants` (max), keep `flat` (e.g. Splitter's 65000) as base |
| A5 | New MAW buffs/immunities: Staff of the Swamp 511 Shield + disease/poison/paralysis immunity; Trident 528 water breathing; Feather Fall for the party from 522, 1331, 1338; immunities on 518 (sleep), 534 (fear, stone, paralysis, sleep), 537 (fear) | Standard's runtime already gives all of these (511 half missile damage, 528 water walking, feather falling per member) | **Have**; check that one member's feather falling protects the party |
| A6 | Tooltip: lines "Permanent … for the party", "Immune to …", "Regenerates Hit/Spell Points"; a stat ≥ 65000 shows "Immune"; "Quest Item:" prefix kept | Our artifact tooltip (`MawItemRules.cpp:1988-2045`) shows stats, on-hit, schools, Swift only | **Port** the power lines and "Immune" |

## 6. Items, crafting, dimension maps, shops

| # | MAW change | Ours | Action |
|---|---|---|---|
| I1 | Spellbook shops: tiers 3 and 6 sell up to spell level 10 (was 9) (`Data/Tables/House rules.txt` rows 279, 282) | `content/house_rules_patch.txt` patches rows 277 and 281 only | **Port**: add `279 #1 10` and `282 #1 10` |
| I2 | Dimensional Maps quest: first tier 100 → 80; step 30 shrinking by 1 per tier to 10 (80, 110, 139, …, 490, 500: 22 turn-ins instead of 37) | `dimension_maps.yml:14-16` and `MawDimensionData::nextQuestTier` (`MawDimensionMaps.cpp:249`) use the old `[below, step]` list | **Port**: `first_step`/`last_step`, loop-based `nextTier`; old saves' stamped tiers map onto the new ladder as upstream's does; update `maw_dimension_maps.yml` |
| I3 | Crafting Cube on a map: Plane of Earth (map 10) removed from `overworldMaps`; reroll count kept in Condition bits 16-23 so rerolls give new seeds | `MawCraftingRules.cpp:578-583` special-cases map 10 as outdoor; our seed already changes with `craftCount` | **Port** the map-10 removal (and invert the ALC-15 test, `MawGapTests.cpp:1565`); reseeding **Have** |
| I4 | Celestial tooltip: "scale with player level, up to level 500" (no 1000 for Madness). Code unchanged (uncapped, 500 in Madness) | D.10 (2026-10-24) chose the old tooltip's 600/1000 caps (`MawItemRules.cpp:51-52`) | **Decide**: 500 for both, or keep 600/1000 |
| I5 | Randomizer: monster density clamped after randomizing (crash fix) | — | **N/A** unless our randomizer can produce Low > High |

## 7. Trainer Hints (new opt-in feature)

`MawCore/TrainerHint.lua` (944 lines, community PRs #68/#69), MAW settings switch "Trainer Hints" (default OFF, per
save). It adds a block to the skill tooltip:

- "Next mastery: Master (skill **7** required)", green when met, red when not; then the nearest teacher:
  "Name - House, Map (this map | outside | next map | coach/boat | Continent)".
- Or "Learned automatically at skill N." (MAW's mastery ladders and solo auto-mastery skills), "Requires a class
  promotion first.", "Highest mastery for this class reached.", "Grand Master reached.", "No trainer found."
- Teachers come from the NPC teacher topics (`teacher_topics.txt`) plus `zzMAW_MoveTrainers.lua`'s moves. Ranking:
  the party's map (in a dungeon also its outdoor map), then maps one walk or one coach/boat away
  (`outdoor_travels.txt`, `transport_*.txt`), then the continent, then elsewhere.

Ours: nothing. **Port** (both rulesets could use it; MAW has it off by default): a preference in Settings → Rules, the
index built from our teacher topic and house tables, the text through `SkillRules`' tooltip values. Medium-size work;
mastery ladders (`mawSkillMasteryLadder`) and moved teachers (`npc_extra_houses.yml`) already exist.

## 8. Not applicable

`MonsterAttackSpeed.lua` (a per-monster attack speed API with no caller yet), the cursor clamp at the dialog edge
(`Fixes.lua`, `Engine.windowClientSize`/`moveCursorBy`), Arena reload screen exit, the multiplayer `HireCharacter` hook,
the settings page layout, MawCore README.

## 9. Dimension maps: do they work? (audit 2026-11-05)

Yes, end to end; the existing unit tests (`*imension*`, ALC-4/13/15) and `maw_dimension_maps.yml` pass.

- **Drop**: same gates as MAW (`zzMaw-Maps.lua:826-939` vs `MawMonsterRules.cpp:218-290`): quest unlocked (tier 500
  rewarded), monster level ≥ 100 (70 in Beyond Madness on 950+ maps), `0.001 × pool share` with bad-luck protection ×
  level/100 / (maps dropped here + 1), bosses ×10, Broodlings ÷ (5 − tier), no drop from raised monsters. The unlock is
  reachable through event 10040 on NPCs 314, 413 and 794.
- **Loot filter**: never turns a map into gold, in MAW or ours. Ours: item 290 is patched to value 0 / `N / A`
  (`patches/items.txt:95-96`), and `lootFilterFacts` skips priceless items; corpse extras skip the filter anyway.
  Hazard: the base row 290 is a 750-gold "Bottle" potion, so losing that patch row would make maps filterable potions
  bound for the alchemy bag. Maps go into the open bag (no bag tag).
- **Differences**:
  - MAW drops the map on the ground; ours puts it in the corpse (on the ground or to the party when there is no corpse),
    so an unsearched corpse loses it.
  - Ours never rolls a map from actors without procedural death loot (MM8 arena, event spawns with `dropsLoot=false`),
    and the Beyond Madness bounty/arena/7d05 early return (`MawMonsterRules.cpp:982`) also skips the map roll, where MAW
    skips only the crafting drops there. Edge cases; worth aligning.
  - The quest ladder is the old one (I2) and the Cube's map-10 rule is stale (I3).
- **Test gap**: no test earns the unlock through the oracle, kills a monster, loots the map from the corpse and checks
  the filter leaves it. A scenario with a level-255 monster, forced bad luck and a strict filter would cover the chain.

## Suggested order

1. B1-B9 together, then the balance tests, `testparty` stages and BALANCE_MODEL.md.
2. I1, I2, I3, A1, A3, S1, H1, H3 (small data and rule changes).
3. The four boss affixes (save version bump), A2, A4, A6, S3.
4. Trainer Hints.
5. Decide I4; the dimension-map edge cases and the end-to-end test.

## 10. Implementation (2026-11-05)

The user kept our Celestial caps (600/1000, GAPS D.10) and our 300° a second homing (DEVIATIONS 181), and asked for
MAW's coloured stats menu (DEVIATIONS 137). Everything else above is built:

- **Balance (B1-B9)**: `mawArmorDivisor`/`mawResistanceDivisor` (`MawBalanceModel.h`), used by `mawMitigatedDamage`
  and the model; `mawSpellDiceScale`/`mawSpellAddScale` and `MawSpellDamageMultiplier` (`MawCombatFormulas`);
  `EnchantStatShare`, the flat HP formula, `CoverGate`, `TankVitalityRatio`, the melee skill without x1.5
  (`MawBalanceModel.cpp`); `MawDamageClass` and `vitality`/`monsterDamage` per class; `mawMonsterBaseDamage`
  (`MawMonsterRules`) sizes attack 1, attack 2 and player-school monster spells by their kind, and the Energy map
  affix rescales a converted hit (`map-energy`, now after `damage-recompute`); the inspect panel's spell row follows;
  `mawMemberKillExperience` banks the capped award. The harness (`harness/mawmon/lua/harness.lua`, line ranges moved
  to 8fbb48d1) regenerated `data/balance_golden.csv` from MAW's own Lua, and the golden test passes: the model matches
  MAW at every level and configuration. `difficulty.yml` relative_to_maw and the Rules panel numbers are regenerated.
- **Bosses (§2)**: Unstoppable, Berserker, Cryptic (save 151, its hidden affix) and Skilled, appended after Omnipotent;
  `tests/MawBossAffixTests.cpp`. Dragon Fear reads Dragon Ability (DEVIATIONS 19). The four have no badge art yet (the
  skull badge shows).
- **Data**: spellbook shops 3 and 6 (`house_rules_patch.txt`), the oracle ladder (`dimension_maps.yml` first_step /
  last_step, `nextQuestTier`; old tiers move onto the new ladder), the Cube's Plane of Earth (`MawCraftingRules.cpp`).
- **Artifacts (§5)**: Justice's on-hit, five more Swift artifacts (`items.yml`), Thor's knockback, budget resistances
  into the enchantment pool (`MawArtifactBonuses::flat`), tooltip power lines (`artifactPowerLines`,
  `mawRegenerationArtifact`).
- **Hirelings and texts (§4)**: `SkillRules::followerSkillBonus` / `followerSkillBonusNeedsSkill` (MAW: Ascension
  +2/+4/+6, learned only); `content/npc_topic_text_patch.txt` and the topic names in `npc_topic_patch.txt`.
- **Ascension tooltip (S3)**: `asc_cc_mana`, `asc_mana_change`, `asc_cc_mana_change`.
- **Trainer Hints (§7)**: `game/rules/maw/MawTrainerHints.*`, preference `trainerHints` (save 152), off by default.
  The user then asked for a journal trainer finder for both rulesets with a per-continent Ledger of Teachers sold in
  taverns, which also gates these hints: `level_generation/ui/journal_trainers_20261105/` (in progress).
- **Coloured stats**: `SkillRules::statLabelRgb` (MAW's ColouredStats colours), drawn by the stats page renderer. Not
  checked in a capture: no scripted input opens the stats page.

Tests: unit suite 2607/2611 (the four failures are effects and MM6 event tests of other sessions' uncommitted work);
all 51 ruleset scenarios pass (`maw_difficulty_change` and `maw_dimension_maps` and `maw_bounty` updated for the new
numbers, ladder and boss roll).
