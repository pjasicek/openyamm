# MAW upstream sync: 7ddb228c → 88a9d7b4

Our MAW ruleset follows MAW `7ddb228c` (2026-11-18, [UPSTREAM_SYNC_7ddb228c.md](UPSTREAM_SYNC_7ddb228c.md)). MAW
`origin/main` is now `88a9d7b4` (2026-11-26): 34 commits (31 without merges), 29 files, +674/−398 lines. The local
MAW clone (`/home/pjasicek/github/Maw-Mod-MMMerge`) is fast-forwarded to `88a9d7b4`. MAW paths are relative to
`Maw-Mod-MMMerge/Scripts/`. Status 2026-11-26: everything marked **Port** is built; what each port changed is under [Ported](#ported).

Legend as in the previous syncs: **Port** = we must change our code or data to match; **Have** = we already match or
never had the problem; **N/A** = engine or MMExtension plumbing with no equivalent.

## Balance and formulas

| # | MAW change | Commit | Action and where |
|---|---|---|---|
| 1 | Damage floor: a mitigated hit keeps at least 1 % of its input (`Formulas.damageFloor` 0.1 → 0.01). The balance model's armour and resistance damage taken read the same floor (`Estimates.lua:418, 429`) | d24bdea5 | **Port**: the `0.1 * input` floor in `mawMitigatedDamage` (`MawCombatFormulas.cpp:228`) and the two `0.1` floors in `MawBalanceModel.cpp:705, 714`; the same in `tests/scenarios/solo_balance/model/mawmodel.py`. Regenerate `data/balance_golden.csv` with `harness/mawmon` |
| 2 | Austerity monster health: `hitToKillMonsterAusterity` {1,2,4,5,6,7,8,9,9.5} → {2,4,6,8,8,8,8.5,9,9.5} | b4c6b516 | **Port**: `HitsToKillMonsterAusterity` (`MawBalanceModel.cpp:329`), the Python model, the golden file |
| 3 | Grandmaster Shield: the 15 % cut on every hit is gone (013f04af "shield bug fix"); the one in the magic path stays, so it is now ×0.85 on non-physical hits only, once | 013f04af | **Port**: `inputs.grandmasterShield` applies only when `type != Physical` (`MawCombatFormulas.cpp:225`). DEVIATIONS 8 is no longer a deviation (MAW now applies it once, but not to physical hits). COMBAT_SPEC §2.4, §13 |
| 4 | Monster death explosions (`Object.AttackType == 4`) hit the party for ×0.4 | 0a2d2863 | **Port**: needs a way for the MAW monster-hit recompute to know the hit is MM8's death blast (`recordPartyProjectileImpact` from `OutdoorWorldRuntime.cpp:5107` / `IndoorWorldRuntime.cpp:19349` passes `Attack1`). Not for our own `detonate` modifier blasts |
| 5 | Carnage arrows: ×0.4 (was ×0.25, `Formulas.carnageDamageMult`), and the same ×0.4 now also scales the bow's fire aura and weapon enchantment damage and legendary 17 on a Carnage hit | ed2e57cd, 2ef24120, 1bfc1604 | **Port**: `MawCombatRules.cpp:1914` (0.25 → 0.4); the aura/enchant extras that are "added after, whole" (comment at :1907-1911) and legendary 17 (:1021) get ×0.4 on Carnage. GAPS D.5 note |
| 6 | Area damage by density: party hits on monsters from Carnage arrows and from area spells (`aoespells`) other than Sparks, Poison Spray, Ice Blast and Shrapmetal take the difficulty's `AoeMult` (new pipeline stage `aoe-density` after `damage-taken`): difficulty 1-3 ×1, 4-5 ×0.9, 6 ×0.8, Doom ×0.7, Road to Insanity ×0.65, Beyond Madness ×0.6 | 4d23c690 | **Port**: a column next to `MonsterDensity` (`MawBalanceModel.cpp:332`) or in `data/difficulty.yml`; applied in the MAW party-hit path after legendary 29 |
| 7 | `aoespells`: Fire Spike (7) out, 201 (MAW's Soul Drinker leech id) in. Read live by legendary 17's halving, the sheet's ÷2.5 on enchant damage, the leech 40 % roll, legendary 15's hit list and the Elementalist's area list (Damage.lua:174) | 4d23c690 | **Port**: `isAreaSpell` (`MawCombatRules.cpp:303`) and the Elementalist list (`MawClassSpells.cpp:234`) drop 7. 201 is **Have** (our Soul Drinker is 99, already listed) |
| 8 | Spell damage and cost: Inferno 12+1d7, 25 SP → 10+1d5, 50 SP; Prismatic Light 20+2d10, 35 SP → 12+1d7, 70 SP | e6dcec35 | **Port**: `tools/maw/generate_ruleset_patches.py` regenerates `patches/spells.txt` |
| 9 | Spell recovery by mastery: `spellPowers` gains `delay = {N, E, M, G}` for 37 spells (most get faster with mastery, e.g. Fire Bolt 110/110/100/90, Meteor Shower 200/200/200/180, Armageddon 250, Soul Drinker 300), written into `Game.Spells[id].Delay*` and MAW's `oldTable` | 024431c1 | **Port**: `spell_power_patch` in the generator parses `delay` into the four `… Recovery` columns (it already maps them for Spells2.txt). Our MAW recovery reads the table delay (`mawSpellDelay`, `MawCombatFormulas.cpp:318`; crowd control `mawCrowdControlDelay`), so no code change |
| 10 | Bow skill damage 4 % → 2 % per point (`skillDamage[Bow]`) | ed2e57cd | **Port**: `MawCharacterSheet.cpp:260` (Blaster stays 4 %); skill description texts |
| 11 | Supreme Armsmaster: level 30 / 50 (Road to Insanity) / 70 (Beyond Madness) → 20 / 32 / 50 | e203116c | **Port**: `mawSupremeArmsmaster` (`MawClassRules.cpp:999`) and any text that names the levels |
| 12 | The sheet's spell and heal power: weapon enchant extras ×1.015^Ascension (was ×1.02^). The combat path was already 1.015 | 2ef24120 | **Port**: `MawCombatRules.cpp:2118, 2159` (character sheet only) |
| 13 | The sheet's vitality: the Mana Shield part needs the skill above 0 and is capped at `fullHP × absorb / (1 − absorb)` with absorb 25/50/75/100 % by mastery (`manaShieldAbsorb`, now global) | cb4c0633 | **Port**: `MawCombatRules.cpp:501-505` caps with `mawManaShieldAbsorbFraction` |
| 14 | Divine Intervention: once per game day per party member (a cast inside the day is refused by setting the engine's 3-cast counter) | 9eae6676 | **Port**: `MawSpellRules::castRefusal` + `afterCast` with a per-member timestamp in `rulesetState`; a new SaveVersion |
| 15 | Monster hitstun: a non-melee hit (spell, missile, blaster) puts a monster into its hit reaction at most once per 3 game minutes per monster; melee hits (party or monster) always can. Cleared on map load (`MonsterHitstun.lua`, an engine patch at 0x40337E) | d405ea42, c1072c66 | **Port**: a new `MonsterRules` hook (Standard: always) asked by `canEnterHitReaction` in both worlds (`OutdoorWorldRuntime.cpp:3210`, `IndoorWorldRuntime.cpp:19841`), with a per-actor runtime time (not saved, as MAW) |
| 16 | Normal Arena (Page to Lord) gold is capped at 1,000,000 in total per game (`vars.normalArenaGold`) | 95c34b9d | **Port**: a rules hook on the Arena win reward (`ArenaRuntime.cpp:202`), the running total in `MawGameState`; a new SaveVersion. The Endless Arena is not capped |

## Items and resistances

| # | MAW change | Commit | Action and where |
|---|---|---|---|
| 17 | Resistance rework: an artifact's resistance stats are ordinary flat resistances, whole (no longer "best per element" resistance enchantments with only the fixed part flat), and the body armour skill's resistance percent now also multiplies every flat item resistance (`tab[11..16] × (1 + armorResMult)`; base resistance enchantments stay apart, best per element). Legendary 16 (×1.5) therefore no longer touches artifact resistances. Skill tooltip: "Bonus Enchant Resistances: +X %" | 79c5a83a, 03700aea | **Port**: `MawItemRules.cpp:1946-1962` (artifact budget resistances become flat), the MAW resistance total (item flat resistances × (1 + body skill %)), the armour skill tooltip lines (`MawSkillRules`) |
| 18 | Artifact resistance budgets doubled: Glomenmail 514 (stats 0.23 → 0.5, resistances → 0.75), 519 (0.75 → 1.5), 522 (resistances 0.3 → 0.6), Lady's Escort 1338 (0.5 → 1), Apollo 2041 (0.46 → 0.92), Odin 2044 (0.75 → 1.5) | 18b8eaf9, 79c5a83a | **Port**: `devdocs/maw/data/artifacts.yml` and the generated `engine/rulesets/maw/data/items.yml` (rerun `devdocs/maw/harness/itemsdata/artifacts/gen.py`; its paths point at an old scratchpad) |
| 19 | Artifact armour: `referenceAC` of an artifact is its own row (was the next rows with the same unidentified name, a bug) | a8dc9ee4 | **Port**: `reference_ac` = `printed_ac` for 20 artifacts in `items.yml` (1306, 1307, 1313, 1314, 1318, 1321, 1322, 1324, 1326, 1327, 2026-2028, 2030, 2031, 2041-2043, 2045, 2046); today several read 0, 3, 6 or 17 |
| 20 | Pandora's Cube on artifacts: +1 % per cube (was 2 %), and the quality now also raises the artifact's positive stat and resistance bonuses (`Artifacts.BonusesOf × ItemQualityMult`); the cube's text says so | f178d17c, 03700aea | **Port**: `ArtifactQualityStep` (`MawCraftingRules.cpp:28`), `artifactBonuses` scaled by `1 + qualityPercent / 100` for positive values, the cube text (`MawCraftingRules.cpp`) |
| 21 | Staff, Sword and Spear guard: the base is the weapon's flat damage row (`GetWeaponDamageRows`: half the level damage plus the flat, × artifact base mult × quality) instead of `Mod2 + reference × charges / 30`; `Formulas.chargesWeaponBonus` is gone | 03700aea | **Port**: `MawItemRules::weaponGuardBase` (`MawItemRules.cpp:1689`) from `mawWeaponDamage` (artifacts too, so `guardBase` in `items.yml` may go) |
| 22 | Carnage's text: "Explosive Impact! (40 % damage per arrow)" with the density mult; Carnage counts in the tooltip's enchant list | 2ef24120 | **Port**: `content/special_item_enchants_patch.txt` row 6 ("half damage") and the MAW tooltip |
| 23 | Two-handed axes and halberds count as two-handed for every gem and slot cap (`GetItemEquipStat`), not by who is selected | 024431c1 | **Have**: DEVIATIONS 66 is what MAW now does; the row can go |

## Classes and equipment

| # | MAW change | Commit | Action and where |
|---|---|---|---|
| 24 | Race classes: Dark Elf, Dragon, Minotaur and Troll classes only for their own race again (`Character selection.txt`'s ClassByRace); every other class stays free | 9de08eb9 | **Port**: `content/character_selection.yml` (each non-matching race loses those four) and its header comment |
| 25 | Shield skill for the Minotaur (Expert) and Minotaur Lord (Master) | 3d664715 | **Port**: generator regenerates `patches/class_skills.txt` |
| 26 | Equip rules moved from item-table rewrites and fake skills to an engine patch (`MawCore/Equip.lua`): Minotaurs hold two-handed axes and halberds in one hand, off hand at Master Axe; Dwarves and Minotaurs off-hand one-handed axes at Expert; Seraphim hold two-handed swords in one hand and never a sword in the off hand. The Wetsuit checks use these rules | 024431c1 | **Have**: `MawItemRules::wield` (`MawItemRules.cpp:2061`) already gives these results. The old per-race rewrite of axes into Dagger items is gone in MAW; we never had it |

## Not ported (N/A)

| # | MAW change | Commit | Why |
|---|---|---|---|
| 27 | Performance: hit refreshes, Ascension and indoor monster reveals batched per tick (`Scheduler.frame`, `Classes.presentSeq`) | d2c166e3 | MMExtension plumbing |
| 28 | Item sorter rewrite; solo "alchemy tab" and "crafting tab" bag flags (`vars.AlchemyBags`, B / AlchemyBagKey toggles, "C"/"A" markers) | b52e2279, 88a9d7b4, 024431c1 | Our inventory is our own; MAW's material routing is still an open item (HANDOFF phase 7 "Left") |
| 29 | Solo charge and potion hotkeys ignored on the inventory screen | 347dbe84 | Not ported by design |
| 30 | Omnipotent and Broodling spawns: `generateBoss` on the spawned monster (a nil index bug); corner nudge reads the monster by index | f26183a7, b5cb6f96 | **Have**: `MawMonsterRules::hatchBoss` gives each spawn its affix in the spawn request; the nudge is MMExtension plumbing |
| 31 | Damage message spell names only for spells; pool labels guard; manifest; guidebook | various | UI plumbing |

## Ported

- Generator (`tools/maw/generate_ruleset_patches.py`, `MAW_COMMIT = "88a9d7b4"`): `spell_power_patch` reads `delay`
  into the four `… Recovery` columns; `patches/spells.txt` (Inferno, Prismatic Light, 37 spells' recovery) and
  `patches/class_skills.txt` (Minotaur Shield) regenerated (1, 8, 9, 25).
- Model (1, 2): `MawDamageFloor = 0.01` (`MawBalanceModel.h`) in `physicalDamageTaken`, `magicDamageTaken` and
  `mawMitigatedDamage`; `HitsToKillMonsterAusterity`; `DAMAGE_FLOOR` in the Python model; `data/difficulty.yml`'s
  `monster_hp_hits_aust`. `data/balance_golden.csv` rebuilt with `harness/mawmon` (line ranges moved to `88a9d7b4`;
  run with a Lua 5.4 built from `build/_deps/lua-src`): only the six Austerity configurations' monster health moved,
  and at levels 1800-2000 the magic damage taken, vitality and monster damage of Hard to Nightmare Austerity, where the
  floor binds. The old harness on `7ddb228c` reproduced the committed file first.
- Combat (3-7, 10-13): Grandmaster Shield non-physical only (DEVIATIONS 8 retired); `recordMonsterBlastImpact` and
  `CharacterDamageHit::deathBlast` (×0.4 in `damage-recompute`, MM8's death blast only, not a detonate modifier);
  `MawCarnageDamageMultiplier` (0.4) on the shot and on the bow's aura and enchantment, legendary 17 ×0.4 on a Carnage
  hit (`PartyMissileSource::carnageArrow`, `MonsterDamageHit::carnageArrow`); the `area-density` stage with
  `mawDensityAreaMultiplier`; Fire Spike out of `isAreaSpell` and the Elementalist list; bow 2 %; Supreme
  Armsmaster from `mawSupremeArmsmasterLevel`; the sheet's 1.015^Ascension and Mana Shield cap.
- Items (17-22): artifact budget resistances are flat (`MawItemRules::applyItemEffects`); the body armour skill's
  percent on the items' own flat resistances (`CharacterCombatRows::itemResistanceScale`, applied in
  `buildCharacterSheetSummary`; the armour skill popup's new line); the six artifact budgets and twenty reference
  ACs in `data/items.yml` and `devdocs/maw/data/artifacts.yml`; `artifactBonuses` takes the item's quality;
  `ArtifactQualityStep = 1` and the cube's text; `weaponGuardBase` from `weaponDamage` (the `guard` key left
  `items.yml`); Carnage's text with its live percent.
- Hooks with save state (14, 16): `SaveVersionMawDailyLimits` (206) keeps
  `CharacterRulesetState::divineInterventionReadyGameMinutes` and `MawGameState::arenaGoldPaid`;
  `MawSpellRules::castRefusal`/`afterCast`; `MonsterRules::arenaWinGold`, read by `interactWithArena`.
- Hitstun (15): `MonsterRules::allowsHitReaction`, asked last by both worlds' `beginMapActorHitReaction`; the melee
  paths (`applyPartyAttackMeleeDamage`, monster melee) pass `melee`; MAW's per-monster times are runtime only and
  cleared by `mapLoaded`.
- Classes (24): `content/character_selection.yml` keeps the four race classes to their race.

## Checks

- Unit tests: the whole suite passes (3271 cases). New: `MawUpstreamSyncTests.cpp` (density multiplier, hitstun,
  Arena cap, Divine Intervention); save round trips carry the two new fields (`RulesetTests.cpp`). Changed numbers:
  the mitigation floor, Grandmaster Shield, Carnage 0.4, Supreme at 20, Inferno's cost, the guard rows
  (`MawGapTests`, `MawSpellClassTests`) and the Champion's sheet rows (`MawSpecExampleTests`, COMBAT_SPEC §11.1).

## Not done

- Nothing for the sync itself. The new texts are extracted and drafted in every language (LOCALIZATION.md, gap fill
  of 2026-11-26).
- MAW's per-race item-table rewrites are gone; ours never had them, so nothing to undo.
