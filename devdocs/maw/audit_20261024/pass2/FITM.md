# FITM — function inventory of MAW's item files (second pass)

Files inventoried (MAW `ef23ee17`, paths relative to `Maw-Mod-MMMerge/Scripts/`):
`General/zzMaw-Items.lua` (IT), `General/zzzMaw_Artifacts.lua` (AR), `General/zMaw_ItemBits.lua` (IB),
`Global/zzMaw_Legendaries.lua` (LG), `Modules/MawCore/Artifacts.lua` (MA), `ItemLevel.lua` (IL), `ItemFields.lua` (IF),
`SpecialItems.lua` (SI). OpenYAMM paths are relative to the repository root; `MIR` = `game/rules/maw/MawItemRules.cpp`,
`MCS` = `game/rules/maw/MawCharacterSheet.cpp`, `MMR` = `game/rules/maw/MawMonsterRules.cpp`,
`MCR` = `game/rules/maw/MawCombatRules.cpp`. Read-only; nothing built or run. The working tree is moving: line numbers
of MCR differ from pass 1's (e.g. `legendaryProtection` is now at MCR:2198).

Known items respected (not re-reported): DEVIATIONS 6, 12-17, 22, 30, 33, 37-46, 64-66, 70-73, 131-141; GAPS A1.2,
A1.5, A1.16, A2.2-A2.6, A2.10, A2.14, A4.4, L4.3, L4.5, L5.6, L6.4 (except FITM-2-3), D.10; pass 1 ITM-1…8, ITM-L1…L8,
ITM-A1…A10, CMB-1, CLS-1, CHM-1, MON-1/2, ALC-12, SKL-2.

## Findings

### FITM-2-1: Monsters raised by Nightmare/Doom revival keep full corpse gold and item chance; MAW quarters both
Severity: P2
Confidence: confirmed (read both sides)
MAW: zzMaw-Monsters.lua:2245-2253 marks a revived monster with `NameId = Id + 300`. IT:231-261 then recomputes its
regular treasure (the branch runs for `NameId > 300`), and IT:265-267 divides the result: `TreasureItemPercent / 4` and
`TreasureDiceSides / 4` (at least 1). Only Road to Insanity / Beyond Madness zero them instead
(zzMaw-Monsters.lua:4139-4145). Result in Nightmare and the Doom modes: a risen monster drops an item a quarter as
often and about a quarter of the gold (dice count unchanged, sides /4).
OpenYAMM: MMR:871 empties the corpse only for `risen && insanityMode` (or Madness's rewardless maps). Otherwise
`corpseLoot` (MMR:897-950) rolls the full chance and full gold dice for a risen actor (`reviveSlainMonsters`,
`game/indoor/IndoorWorldRuntime.cpp:15659-15710`, sets `risen` and leaves loot alone). With MON-1 (risen give full XP)
this makes leaving and re-entering a Nightmare dungeon a full-value loot farm.
Not covered by: GAPS A4.4 ("risen monsters drop nothing" is about crafting drops, which do match); MON-1 (experience
only); ALC-12 (reagents). No DEVIATIONS row.
Suggested fix: in `MawMonsterRules::corpseLoot`, for `pFacts->risen` outside insanity, divide the final item chance by 4
(MAW rounds) and the gold dice sides by 4 (min 1) after the normal regular-monster computation.

### FITM-2-2: Staff/Sword/Spear armour and the staff's party resistance read the wrong weapon base (about 1.5x MAW)
Severity: P2
Confidence: confirmed (both sides read; COMBAT_SPEC §3.3 states MAW's formula, the code does not follow it)
MAW: IT:3226-3247 `addWeaponACRes` and IT:3294-3316 `addStaffPartyRes` use
`bonusBase = txt.Mod2 + round(referenceWeaponAttack[id] * MaxCharges / 30)` (Formulas.chargesWeaponBonus). `txt.Mod2` is
the upscaled flat of the item's ladder rung (IT:1416-1430: `round(weaponTierFlat(rung))`, halved for one-handers) and
`referenceWeaponAttack` the Mod2 of the top rung of its run (IT:2614-2633), i.e. 16 (two-handed/staff) or 8. MaxCharges is
uncapped (up to 255) and quality is not applied. Artifacts (MaxCharges 0) use their printed Mod2 after the artifact
upscaler (x2 one-handed, x3 two-handed, IT:2334-2346).
OpenYAMM: MCS:396-405 (Staff/Sword/Spear armour) and MCS:448-457 (`mawStaffPartyResistance`) use
`damage->shownBonus` from `weaponDamage`, i.e. `flat + 2*floor(P/2)` (halved one-handed), P capped at 100, times quality;
artifacts a tier-6 weapon at the party's level.
Examples (top-rung staff, GM Staff 50, AC row 4 %, x(s+10) = 60): P = 40: MAW base 16 + 21 = 37 -> 89 AC; ours
16 + 40 = 56 -> 134 AC. P = 100: MAW 69, ours 116. Only above P ~ 190 does ours fall below MAW (cap 100). The same base
feeds the staff resistance every party member gets. One-handed sword, P = 40: MAW 19, ours 28.
Not covered by: GAPS L5.6 (party-wide staff resistance, marked done: the share is right, the base is not); SKL pass-1
"Staff/Sword/Spear AC from weapon attack x (s+10)" (checked the shape, not the base). No DEVIATIONS row.
Suggested fix: compute the guard base as MAW does: the base item's rung flat (two-handed vs halved as the upscaler
decides: staves, two-handed axes/swords, halberds whole) plus `round(topRungFlat * itemPower / 30)` with the uncapped
item power (Celestial: the wearer-level power), no quality; artifacts their upscaled printed Mod2. Store the needed
numbers in `items.yml` bases/artifacts if they are not there.

### FITM-2-3: A dragon's item bonuses to Dodging and Unarmed are not tripled (extends GAPS L6.4)
Severity: P3
Confidence: confirmed
MAW: IT:3003-3015 `applyDragonMult` triples `tab[1..16]` and also `tab[82]` and `tab[83]`, the item skill slots
(skill + 50) of Dodging (32) and Unarmed (33), i.e. the dragon's Scales and Fangs. Sources: Dodge/Unarmed skill
enchants (23/24) and artifacts such as Hands of the Master (1313) or Hareck's Leather (1318). GetSkill (IT:2587-2611)
then caps at twice the trained skill.
OpenYAMM: MIR:1245-1274 `applyEquippedEnchantEffects` triples the stats, HP, SP, AC and resistances only;
`itemSkillBonuses` are untouched.
Not covered by: GAPS L6.4 ("items x3 done: item stats, HP, AC and resistances; the sheet's armour pieces and skills" -
the armour skills, not item skill bonuses).
Suggested fix: in the dragon branch, also triple the item's own additions to `itemSkillBonuses["Dodging"]` and
`["Unarmed"]` (still bounded by the twice-trained cap).

### FITM-2-4: Boss drops follow the item table's weights; MAW picks one of the 12 equipment types uniformly
Severity: P3
Confidence: confirmed (mechanism); the distribution below is computed from our tables
MAW: zzMaw-Monsters.lua:3016 gives every boss `TreasureItemType = random(1, 12)` (const.ItemType Weapon, Weapon2H,
Missile, Armor, Shield, Helm, Belt, Cloak, Gauntlets, Boots, Ring, Amulet); the corpse branch IT:268-299 keeps it, and
IT:978-985 only re-rolls as "any" when the result is not enchantable. Each equipment type is 1/12 of boss drops.
OpenYAMM: MMR:946-948 sets every boss drop to `LootItemKind::Any`; `ItemGenerator::generateRandomInventoryItem` keeps
enchantable items and `chooseRandomBaseItem` (`game/items/ItemGenerator.cpp:294-339`) weights them by
`random_items.txt`. At treasure level 6 the enchantable bases weigh: body armour 23.6 %, rings 16.9 %, one-handed
weapons 10.7 %, shields 8 %, two-handed ~7.7 %, bows 2.7 %, belts/cloaks/gauntlets ~4.5 % each. So bosses give about
3x MAW's body armour and 2x its rings, a third of its bows.
Not covered by: RANDOMS.md lists draw B5 (`U{1..12}`) but nothing implements it; no GAPS/DEVIATIONS row.
Suggested fix: for `result.boss`, roll a uniform equipment kind (12 kinds) and filter the item roll to it, falling back
to any enchantable when the kind has no candidate.

### FITM-2-5: The artifact popup shows MMMerge's "(Special Powers: ...)" numbers, not MAW's scaled bonuses and effects
Severity: P3
Confidence: confirmed
MAW: AR:344-432 `MawArtifactOnHitText` builds the effect lines (on-hit range at the artifact level, "xN damage vs",
Vampiric, the spell, "+50 % skill in <schools>", "Permanent <buffs>", "Immune to ...", "Swift", Cycle of Life, "Drains 3
HP", the red negative leech, the wear requirement). Tooltip.lua:495-534 strips the description's "(Special ...)" part
and a leading "(...)" summary, then prints `Artifacts.BonusesOf` (MA:186-224) stat and skill lines and those effect
lines.
OpenYAMM: MIR:1769-1773 adds only "Artifact level"; the description is items.txt's, e.g. 2023 Excalibur "(Special
Powers: +30 Might)" and 504 Elderaxe "(Might +20, Swift, 6-12 points of Cold damage, Minotaur)" - wrong under MAW (504 is
not Swift there, its Might follows the budget). No line shows an artifact's actual MAW stats.
Not covered by: GAPS A2.14 (base item lines) and L4.3/L4.5; no row for artifact popups.
Suggested fix: under MAW, cut the "(Special" tail / leading "(...)" from artifact descriptions and add inspect lines
from `MawArtifact` (stats/skills at the party level, on-hit range, versus kinds, spell, schools, buffs, immunities,
Swift, drain, leech, wear rule).

### FITM-2-6: MAW's poison-duration hook is re-registered on every map load (question: MAW bug, effectively ~50 s)
Severity: P3
Confidence: plausible (MMExt `events.X = f` adds a handler per closure; needs a runtime check in MAW)
MAW: IT:1496-1506 defines `events.DoBadThingToPlayer` inside `events.LoadMap`, so each map load in a session adds
another handler. One poisoning then runs all of them: the first sets 25 s, each further one adds 5 (cap 50). After
five or six map loads every poisoning lasts 50 s, and a repeat adds 5 per handler.
OpenYAMM: MCR:2578-2589 `characterConditionApplied`: 25 s, +5 per repeat, cap 50 (the written intent, GAPS A1.5).
Not covered by: GAPS A1.5 (done, follows the code as written). No DEVIATIONS row.
Suggested fix: decide; if the intended 25/+5 is kept, add a DEVIATIONS row ("MAW re-registers the handler per map load,
so poison usually lasts 50 s").

### FITM-2-7: Spell-speed special (40) still works from a broken weapon
Severity: P3
Confidence: confirmed
MAW: IT:2087-2095 `HasSpellHasteEnchant` reads `pl:GetActiveItem(i)`, which skips broken items
(`reference/mmmerge/Scripts/Structs/00 structs.lua:1703-1708`).
OpenYAMM: `game/rules/maw/MawSpellRules.cpp:585-587` tests the three slots' `specialEnchantId` without `broken`.
Not covered by: no related row.
Suggested fix: require `!broken` on each slot.

### FITM-2-8: Small loot-roll differences
Severity: P3
Confidence: confirmed
- Monsters that carry a specific item (`mon.Item ~= 0`) keep the table's treasure chance, level and type in MAW
  (IT:231 tests `mon.Item == 0`); MMR:927-950 applies MAW's chance/grade/70 % "any" to every non-boss.
- The special's melee/caster swap counts the enchant types before the duplicate re-roll in MAW (IT:1267-1295, re-roll at
  IT:1312-1322); MIR:1034-1038 re-rolls first (MIR:1100-1118 counts after). Only changes the swap when both enchants
  rolled the same Might/Accuracy/Int/Pers type.
- The quest-item sell refusal reads "you will still need that item" (MIR:877); MAW names the item (SI:64, `%24`) and also
  puts the refusal in the merchant's hover text (SI:96-106, 125-127). The special-enchant immunities print "Enchantment
  protects <name> from <thing>" in MAW (IT:1458-1476); ours block silently.
Not covered by: no related rows.
Suggested fix: optional; skip the regular-monster rewrite when the actor carries an item; the rest cosmetic.

## Checked and matching (summary; the full table follows)

- Item fields (IB, IF): enc2 strength clamp 65535, drop level 0-2047, quality 0-20, rarity tier/affix/celestial kept
  apart — `ItemRulesetFields` holds each separately (save round-trip per pass 1; indoor ground items are ITM-1).
- Item level (IL): PowerFor min(floor(L/5), 100), hard cap 255, ladder rungs by NotIdentifiedName run with MAW's 67/804
  renames, TierLevels 3/rung, WearLevel L-(10+0.09L), the 7/8 fallback drop level.
- Generation (IT:973-1369): artifact roll 0.5 % pity outside shops on enchantable items; shop crafting substitution;
  reagent level; loot tier incl. dimension bonus floor((P-28)/2) and Arena +20; band roll, boss /4; cascade, shop
  redirect, pity growth by multiplier incl. map affixes; Omnipotent -> Celestial; item power ranges; enchant types (ring
  1-16, enc2 effectively 1-10), 10 % skill enchant, strength formulas by rarity, skill nerf, slot multiplier (ceil / floor),
  sync; special pools by grade with the boss-only top pool; 19 and melee/caster swaps (same result in either order);
  Ancient/Primordial/Celestial/Legendary marks; affix pick 1/(n+1).
- Value (IT:1897-2040, 2194-2325): getItemValue terms, rounding, x0.4/x(1+0.08n), sealed books, gem and crafting buy
  prices, crafting material values, every spellbook value (MM8/MM7/MM6 tables, Dark/Light x2, the ten single books),
  Greater Heal names, Insanity book multipliers and tier map.
- Corpse loot (IT:161-327): gold (B-level + bolster) x7.5 by tier, chance, grade, Doom/Nightmare scaling, boss
  grade/100 %/Broodling; seeding is DEVIATIONS 14.
- Celestial (IT:1622-1661): tier L/11+5 with the 1.2x total-level cap, x1.25 x slot, skills /10, power
  GetPrimordialCharges (caps per D.10).
- Character sheet (IT:2692-3356): armour AC with reference x P/40 and quality, Legendary 28 x1.5, enchant collection
  (except ITM-2/3), specials table, artifact budget, weapon rows (bow +skill, staff half-Unarmed, two axes x0.9 each 2H,
  armsmaster split with an off-hand weapon, blaster, per-skill floor, GM bow refund), armour-skill AC/resistance with the
  Austerity floor, dragon x3 of stats/AC/resistances, luck to resistances, slot attack rows, armsmaster attack (not
  staves), unarmed rows, leech flags (16/41/40, Hades, vampire race, DK). AC excludes Speed's effect as MAW's
  `CalcStatBonusByItems` does (IT:2581-2583; GameMechanics.cpp:2337-2343 takes the ruleset rows).
- Wear/shop/chest (IT:4130-4202): level requirement on equip, Doom unidentified wear block, Doom chest Disarm check,
  identify IdRepSt^2 and repair x5.
- Artifacts (AR): on-hit table, Slow and spells (dev 72), vampiric flag (dev 70), Hades -10 % leech, Ethric's drain
  (ITM-A8), Cycle of Life, wear requirements, buffs (dev 73, ITM-A9), immunities (ITM-A5), x0.9 delay, CountItemBonuses
  disabled (our artifact branch drops Standard's stats/skills; Standard's Swift ticks and flat regen are unused by MAW's
  delay/regeneration paths).
- Legendaries file (LG): ItemAdditionalDamage zeroed (MAW computes its own adds), 13 immunity, 15 cooldown, Mana Shield
  formula incl. the unclamped mana cost and efficiency 5 at skill 50 (`MawSkillFormulas.cpp:43-76`).
- Special items (SI): quest-bound list, sell-once list and seer bits 199-201, prices, identify/repair always allowed.
  OpenYAMM's own "I lost it" seers can hand back Eclipse (mm8_common.lua:140) or Kilburn's Shield (mm6_common.lua:24-29)
  after a sale, but `soldUniqueItems` refuses the second sale, so no money loop.

## Inventory (MAW function / handler / statement -> OpenYAMM counterpart -> status)

Status: OK = matches; F = new finding here; K = known (row or pass-1 id); N/A = not applicable (debug, multiplayer, dead
code, isRedone data set, UI replaced); S = belongs to another area and is covered there.

### General/zzMaw-Items.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | GenerateItem (1) | treasure level 7 -> 6 | `levelSevenGivesRareItem` false, `ItemGenerator` level-six redirect | OK (GAPS A2.6) |
| 2 | getMonsterSeed (33) | Insanity per-type seed chain | `RandomStream` CorpseLoot domain | K DEV 14 |
| 3 | getBossLootSeed (64) | boss loot seed | same | K DEV 14 |
| 4 | IsBaseItemId (95) | base id bands | `filtersLoot`, `items.yml` bases | OK |
| 5 | IsArtifactId (101) | artifact id bands | `items.yml` artifacts | OK |
| 6 | IsEnchantableItem (110) | bases minus ancient weapons | `MawItemData::baseItem`, `isEnchantable` | OK (ALC-6 for blasters) |
| 7 | LootContext.set/markBoss/take/restore (132-159) | corpse -> generator context | `ItemGenerationRequest` dropLevel/boss/omnipotent | OK |
| 8 | PickCorpse seeding (161-205) | RNG reseeding | `RandomStream` | K DEV 14 |
| 9 | PickCorpse gold (210-228) | (bolster + B level) x7.5 by tier | MMR:896-913 | OK |
| 10 | PickCorpse regular chance/grade/type (231-261) | non-boss loot | MMR:927-950 | OK; carried-item case F FITM-2-8 |
| 11 | PickCorpse risen quarter (265-267) | NameId>300 /4 | none | F FITM-2-1 |
| 12 | PickCorpse boss (268-299) | 100 %, grade lvl/20+2, Broodling, Omnipotent | MMR:917-924 | OK; Morcarack K ITM-5; boss type F FITM-2-4 |
| 13 | PickCorpse loot-filter flags, CallDefault corpse removal (301-326) | filter state; corpse removed after pick | `filtersLoot` at roll time; corpse views | K DEV 17 / N/A |
| 14 | CastTelepathy (329) | reseed for Telepathy preview | — | K DEV 14, ALC (pity) |
| 15 | LoadMap seeds (357) | per-map monster seeds | — | K DEV 14 |
| 16 | GameInitialized2 (405) | 67/804 renames, special pools by level | items patch, `chooseSpecialEnchantId` pools | OK |
| 17 | encStrUpNormal/Austerity (444-456) | strength curve | `mawEnchantStrengthCurve` | OK |
| 18 | applyDifficulty, rollEnchantStrength (461-475) | ceil/round order by rarity | `mawEnchantStrength` | OK |
| 19 | GetPrimordialMaxEnchantStrength (477) | gem cap | `MawCraftingRules` (MIR n/a) | K DEV 40 |
| 20 | GetLootStrength/GetLootTier (484-490) | artifact level tier | MIR:1323-1325 | OK |
| 21 | GetMaxEnchantStrength (492) | estimator only | `MawBalanceModel` | S (balance) |
| 22 | GetMaxItemCharges/GetItemChargesCap (504-510) | cap 255 | `mawItemPower` | OK |
| 23 | rollTierCharges, GetPrimordialCharges (512-529) | item power by rarity | `mawItemPower`, `mawItemPowerRange` | OK |
| 24 | GetItemDropLevel (531) | stored level, legacy fallback | `fields.dropLevel` | OK (legacy N/A; rounding K ITM-6) |
| 25 | GetDifficultyExtraPower (552) | 1.2/1.1/1.05 | `MawRules::lootConfig` | OK |
| 26 | GetEnchantTierBonus (563) | map affix and Arena tier bonus | MIR:965-967 | OK |
| 27 | const.Rarity, rarityUpgradeChance, shopRarityRedirect, BOSS_* (574-602) | constants | `MawItemFormulas.cpp` | OK |
| 28 | rarityDifficultyMult, rarityPityField, enchantChances (604-629) | tables | `UpgradeDifficultyMultipliers`, `mawRarityBands` | OK |
| 29 | GetEnchantChance, GetEnchantBands, rarityBandMult (631-665) | band widths | `mawRarityBands` | OK |
| 30 | enchantStrengthRange, enchantCountByRarity (667-685) | ranges | `mawEnchantStrengthRange` | OK |
| 31 | MawItemRarity (691) | rarity read back | `fields.lootRarity` stored | OK |
| 32 | cubeQualityStep, CanTakeCube, GetCubeQualityStep (717-746) | Pandora's Cube | `MawCraftingRules::refineQuality` | K DEV 37 |
| 33 | MawQualityText (748) | popup line | inspect line (GAPS A2.14) | OK |
| 34 | GetRarityBaseMultiplier, GetRarityMultiplier (757-780) | upgrade multiplier incl. map affixes | `mawRarityUpgradeMultiplier`, MIR:972-973 | OK |
| 35 | RollItemRarity (782) | cascade and pity | `mawRollRarity` | OK |
| 36 | enchantStrengthMean ... GetExpectedEnchantFraction (822-877) | expected loot (balance) | `mawLongRunRarityShares`, balance model | S (balance) |
| 37 | RollEnchantType (880) | 1-10 / rings 1-16 | `rollEnchantType` | OK |
| 38 | TIER_LEVELS, GetTier (889-893) | 15 | `mawLootTier` | OK |
| 39 | BeforeLoadMap (895) | Austerity curve switch | `config.austerity` | OK |
| 40 | AfterLoadMap chest gold (903-928) | gold piles by band and bolster | `chestGoldAmount` | OK (MAW skips slot 0: negligible) |
| 41 | AfterLoadMap chest loot filter (930-970) | placed items to gold | `filtersLoot` | K DEV 17 |
| 42 | ItemGenerated (973-1369) | the whole roll | `rollEnchantments`, `rollPlainItem`, `adjustShopStock` | OK; small order F FITM-2-8; K ITM-6, ITM-8, DEV 15, 41 |
| 43 | get_affix (1372) | 1/(n+1) weights | `pickLeastFound` | OK |
| 44 | slotMult (1405) | slot multipliers | `mawEnchantSlotMultiplier` | OK |
| 45 | GameInitialized2 (1410) | halberds two-handed; weapon upscaler; shield Mod2 x2 + dice | items patch; `items.yml` bases | OK (507 K ITM-A1) |
| 46 | GameInitialized2 (1439) | ColouredStats | — | K DEV 137 |
| 47 | DoBadThingToPlayer (1458) | special immunity pairs + message | Standard immunities under MAW | OK (GAPS A2.2); message F FITM-2-8 |
| 48 | GameInitialized2 (1477), (1508) | special texts | `special_item_enchants_patch.txt` | OK |
| 49 | LoadMap -> DoBadThingToPlayer (1496) | poison duration | MCR:2578-2589 | F FITM-2-6 |
| 50 | poisonTimer (1513) | real-time poison | MCR:2463-2516 | OK (GAPS A1.5; CHM bolster note) |
| 51 | legendaryEffects, LEGENDARY_AFFIX_COUNT (1572-1610) | affix texts, count 25 | `items.yml` legendary_affixes | OK |
| 52 | GameInitialized2 (1612) | texts of 24, 29 | `items.yml` | OK |
| 53 | updateCelestialItem (1622) | Celestial at the wearer's level | MIR:1162-1166, 1405-1416 | OK (D.10; popup K ITM-4) |
| 54 | UpdateExtraDescription, KeyDown/KeyUp Alt (1663-1679) | extra tooltip | — | K DEV 137 / GAPS H.7 |
| 55 | GameInitialized2 (1682) | stat names and colours | `mawEnchantStatName` | OK |
| 56 | bonusEffectsBase, bonusEffects (1742-1799) | special stat table | `applyMawSpecial` | OK (ITM-7 for others) |
| 57 | checktext (1802) | special popup texts | `enchantDescription` | OK (GAPS A2.14) |
| 58 | CalcItemValue (1897) | value, sealed books, shop gem prices | `itemValue`, `shopBuyValue` | OK |
| 59 | getItemValue (1920) | MAW value | `mawItemValue`, `fullValue` | OK (K DEV 12, 65) |
| 60 | reagentPrices (2011) | buy prices | `MawCraftingData` | OK |
| 61 | enchantbonusdamage, ENCHANT_* , enchantDamageRange (2047-2082) | enchant damage | `MawCombatRules` | S (CMB) |
| 62 | HasSpellHasteEnchant (2087) | special 40 | `MawSpellRules.cpp:585` | F FITM-2-7 |
| 63 | GetLegendary19Mult (2098) | x1.5 | MCR | OK (pass 1) |
| 64 | GetPlayerBaseRecovery (2106) | enchant pace | `enchantPace` | OK (artifact pace K ITM-A6) |
| 65 | calcEnchantDamage (2125) | enchant damage roll | MCR | S (CMB) |
| 66 | enchantList (2158) | tooltip helper | — | N/A |
| 67 | modifiedBookValues(MM6), GameInitialized2 (2194-2288) | Greater Heal, book and material values | `content/items_patch.txt` | OK (all values compared) |
| 68 | getBookTier, CalcItemValue (2289-2325) | Insanity book prices | `spellbookTier`, `shopBuyValue` | OK |
| 69 | artWeap1h/2h/artArmors, GameInitialized2 (2330-2346) | artifact lists, printed upscaler | `items.yml` base kinds | OK; upscaled Mod2 feeds F FITM-2-2 |
| 70 | BuildItemInformationBox / artifactTextBuilder (2350-2366, commented) | — | — | N/A |
| 71 | replaceNumber (2369) | only commented callers | — | N/A |
| 72 | ancientWeapons (2382) | blasters | — | OK (ALC-6) |
| 73 | CalcStatBonusByItems (2385, commented) | — | — | N/A |
| 74 | BeforeNewGameAutosave, BeforeLoadMap (2421-2441) | clear new-game item charges | Standard-generated starter items, no ruleset fields | OK |
| 75 | Action (2444, commented) | — | — | N/A |
| 76 | ItemAdditionalDamage (2462) | engine vampirism off | `applyStandardItemEffects` drops it | K GAPS A1.2 |
| 77 | slotMap (2495) | comparison slots | `comparisonLines` | OK |
| 78 | calculateStatsAdd (2512) | unused | — | N/A |
| 79 | ModifyItemDamage (2555) | engine item damage 0 | slaying x2 still applied | K CMB-1 |
| 80 | plItemsStats init (2559) | per-player table | `Character` bonuses | N/A |
| 81 | CalcStatBonusByItems (2566) | item stats replace engine; black potions; AC minus Speed effect | MAW sheet rows, GameMechanics.cpp:2337-2343 | OK (black potions K SKL-2) |
| 82 | GetSkill (2587) | item skills, artifact schools x0.5, cap 2x trained | `addCappedSkillBonus`, MIR:1352-1370 | OK |
| 83 | GameInitialized2 (2614) | referenceAC/referenceWeaponAttack | `items.yml` reference AC; weapon reference missing | F FITM-2-2 |
| 84 | bonusBaseEnchantSkill (2642) | skill enchant map | `addBaseEnchant` | OK |
| 85 | makeSet, buildSets (2659-2676) | sets | — | N/A |
| 86 | IsArtifactWeapon, IsArtifactItem (2679-2688) | artifact tests | `MawItemData::artifact` | OK |
| 87 | collectArmorAC (2692) | armour AC, L28 | `armorClass`, MCS:374, 512-548 | OK (ring/amulet K ITM-A3) |
| 88 | collectEnchant (2722) | read transforms, echo, resistance best, skill slot | MIR:1419-1440 | OK (hats K ITM-2/3) |
| 89 | collectEquipEffects (2758) | specials, 62, schools, Meditation | `applyMawSpecial` | OK |
| 90 | collectArtifactBonuses (2797) | artifact budget | MIR:1305-1370 | OK |
| 91 | addWeaponRows (2812) | weapon damage rows | MCS:143-301 | OK |
| 92 | addBless (2950) | Bless attack | buff code | S (SPL; DEV 33) |
| 93 | addArmorSkillAC (2963) | armour/shield skill % | MCS `mawArmorBreakdown` | OK |
| 94 | applyDragonMult (3003) | x3 incl. Dodging/Unarmed item skills | MIR:1245-1274 | F FITM-2-3 |
| 95 | addBuffStats (3019) | buff-rework stats | spell rules | S (SPL) |
| 96 | addLuckRes (3088) | luck to resistances | MCS:421 | OK |
| 97 | addHP (3097) | HP | skill rules | S (SKL) |
| 98 | addMana (3131) | SP | — | K CLS-1 |
| 99 | addSlotAttackRows (3149) | skill attack, bow GM refund, Dodging AC | MCS:303-331, 414-418 | OK |
| 100 | addMiscAttack (3183) | armsmaster attack, unarmed rows, dead hammerhands branch | MCS:333-344 | OK |
| 101 | addWeaponACRes (3213) | weapon guard AC/res; leech flags | MCS:391-405; MCR leech | F FITM-2-2 (leech OK, DEV 70) |
| 102 | addStaffPartyRes (3294) | staff resistance to all | MCS:437-457 | F FITM-2-2 |
| 103 | applyDamageMultipliers (3320) | might/heroism/unarmed/Shaman | MCS:345-361 | S (CMB) |
| 104 | itemStats (3358) | phase order; Celestial update; moon cloak MaxCharges 0 | sheet rows / item effects | OK |
| 105 | equipSpellMap, equipSpellSlot, meditationBonusItemMap, statMap (3447-3486) | maps | `applyMawSpecial` | OK |
| 106 | artifactPower (3506-3834) | budgets | `items.yml` artifacts | OK (pass 1 script check) |
| 107 | artifactHpRegen/SpRegen (3836) | regen artifacts | `MawSkillRules.cpp` | OK |
| 108 | ARTIFACT_SPELL_SKILL_BONUS, artifactSpellBonus (3840-3875) | schools | `spell_bonus` | OK |
| 109 | AfterLoadMap mawRefresh, Action (3879-3890), mawRefresh (3891) | recompute triggers | recomputed per frame/equip | N/A |
| 110 | mawPlayerBaseStats (3903) | unused, buggy | — | N/A |
| 111 | KeyDown R, refreshItems (3922-3984) | shop reroll | `shopRerollCost`, `tryRerollStock` | K DEV 13 |
| 112 | ShopItemsGenerated, GetMerchantTotalSkill, mawStoreShop (3987-4046) | merchant fix, shop types | `merchantValue` | K DEV 45 |
| 113 | artifactPowerMult (4049) | only dead callers | — | N/A |
| 114 | playerToPartyBuff, statToPlayerbuff, CalcStatBonusByItems (4074-4127) | potion vs party buff, max | potion aura flats | S (SPL; DEV 33) |
| 115 | CanWearItem (4130) | Doom identify, level | `wearRefusal`, `levelRequirement` | OK (artifacts K ITM-A10) |
| 116 | CanOpenChest (4145) | Doom Disarm | `chestOpenRefusal` | OK (trapped chests by decision, PHASE9 Q1) |
| 117 | GetShopItemTreatment (4172/4179 commented, 4189) | Doom identify/repair price | `shopServiceMultiplier` | OK |
| 118 | craftingNames, KeyDown U (4206-4275) | gem merge | Workbench | K DEV 42 |
| 119 | Tick (4277, commented) | — | — | N/A |
| 120 | fireAuraDamage, calcFireAuraDamage (4283-4319) | Fire Aura | MCR | S (CMB) |
| 121 | AfterLoadMap isRedone chest fix (4321) | other data set (item 1466 is not "Emerald Island" here) | — | N/A |
| 122 | GetLevelRquirement (4351) | level requirement | `mawLevelRequirement` | OK (K ITM-6) |
| 123 | equipSlotWeights (4375) | unused | — | N/A |
| 124 | GetItemEquipStat (4390) | two-handed axes as 1 | `mawEnchantSlotMultiplier` | OK |
| 125 | GetSlotMult (4407) | incl. hat x1.5 | `readSlotMultiplier` | OK (K ITM-2/3) |
| 126 | GameInitialized2 (4427) | SPStats = Personality | — | K CLS-1 |
| 127 | GetItemSkill (4435) | axes skill 3 | canonical skills | OK |
| 128 | LoadMap potion reroll (4450) | 264-289 -> 252-263 | `placedItemId` | OK |
| 129 | PITY_EXPONENT, pity_chance (4471) | pity | `mawPityChance` | OK |
| 130 | mawArtifacts, mawArtifactsKeep (4481-4521) | drop list; keep list commented | `items.yml` drop weights | OK (K DEV 15, 16) |
| 131 | AfterLoadMap chest artifacts (4523-4536) | placed artifacts re-rolled | placed artifacts kept | K DEV 16 |
| 132 | AfterLoadMap Doom starting items (4537-4552) | MaxCharges 2/4 | Doom item power | K CHM-1 |
| 133 | IsTwoHandedWeapon (4555) | 2H test | `twoHanded` | OK |
| 134 | GetWeaponFlatDamage (4562) | rung flat, artifacts tier 6 | `mawWeaponDamage` | OK (K ITM-A2) |
| 135 | GetWeaponDamage, GetWeaponDamageRows, MinMax, LevelDamage (4569-4607) | weapon rows | `mawWeaponDamage` | OK |

### General/zzzMaw_Artifacts.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | artifactOnHit table (48-281) | on-hit kinds, coefficients, MultVs, Vampiric, OnHit | `items.yml` on_hit | OK |
| 2 | MawArtifactSpellPower, castAt (52-64) | spell at wielder's skill | `updateArtifacts` | K DEV 72 |
| 3 | MawArtifactVampiric (283) | flag | `mawLeech` | K DEV 70 |
| 4 | damageKindName, kindName, playerBuffName, immunityName (294-338) | text helpers | — | F FITM-2-5 |
| 5 | MawArtifactOnHitText (344) | artifact effect lines | MIR:1769-1773 (level only) | F FITM-2-5 |
| 6 | ARTIFACT_ONHIT_ENCHANT, MawArtifactLevel (445-453) | level = party total | `artifactHitRange` | OK |
| 7 | MawArtifactOnHitDamage, MawArtifactOnHitPower (455-474) | range x pace | `artifactHitRange` | OK (pace K ITM-A6) |
| 8 | resistanceFor, onHitForItem (481-518) | resisted by its kind; spells | MCR:1502-1516, 1570-1576 | K ITM-A7 |
| 9 | MawArtifactOnHit (523) | pipeline stage, elemental share | MCR | K ITM-A7, DEV 46 |
| 10 | overTimeHPSP (561) | skip dead/stone/erad | `updateArtifacts` | OK |
| 11 | sharedLife (570) | Cycle of Life | `updateArtifacts` | OK |
| 12 | artifactDrain, artifactLeech (604-614) | Ethric -3, Hades -10 % | MCR | K ITM-A8 |
| 13 | RegenTick (616) | drain / Cycle tick | 5-minute tick (GAPS L4.3) | OK |
| 14 | artifactWearReq, Wetsuit (633-706) | wear rules | `ItemRuntime` class/race rules; Wetsuit `GameMechanics.cpp:3637` | OK for MAW (equal to MMMerge's; OpenYAMM's Wetsuit rule is its own Standard one, outside MAW scope) |
| 15 | CanWearItem (708) | Wetsuit slots, requirements | same | OK (see 14) |
| 16 | artifactBuffs, refreshBuff, partyHasItem, mawTick_ArtifactBuffs, GameInitialized2 (735-794) | permanent buffs, Horn of Ros | `updateArtifacts`, Standard powers | K DEV 73, ITM-A4, ITM-A9 |
| 17 | artifactImmunities, DoBadThingToPlayer (800-848) | immunities | Standard powers | OK (1341 K ITM-A5) |
| 18 | artifactAttackSpeed, GetAttackDelay (856-871) | x0.9 | `mawArtifactAttackDelayMultiplier`, MCR:1241 | OK |
| 19 | Game.CountItemBonuses = noop (880) | MMMerge artifact stat bonuses off | artifact branch restores stats/skills (MIR:1305-1320) | OK (Excalibur attack K ITM-A4) |

### General/zMaw_ItemBits.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | DecodeEnc2/EncodeEnc2 (18-34) | type 0-63, strength 0-65535 | `secondStandardEnchantId/Power` (uint16) | OK |
| 2 | GetEnc2, GetEnc2Type/Strength, SetEnc2*, HasEnc2, ClearEnc2 (37-75) | accessors | fields | OK |
| 3 | isArtifact (120) | legacy decode guard | — | N/A |
| 4 | DecodeRarity/EncodeRarity/SetRarity (134-173) | tier/affix/celestial/level/quality packing, legacy layout | separate fields | OK (legacy N/A) |
| 5 | HasRarityData (175) | marker test (value code) | `fullValue` always prices the special | OK |
| 6 | GetAncientTier, IsAncient/Primordial, HasLegendaryAffix, GetLegendaryAffix, IsCelestialItem (180-209) | reads | `lootRarity`, `legendaryAffixId` | OK |
| 7 | SetAncientTier, SetLegendaryAffix, SetCelestialItem (213-235) | writes | fields | OK |
| 8 | Get/SetStoredDropLevel (238-246) | floor, 0-2047 | `dropLevel` clamp 2047 | OK (rounding K ITM-6) |
| 9 | Get/SetItemQuality, ItemQualityMult, CUBE_QUALITY_MAX (113, 254-269) | quality 0-20 % | `qualityPercent` | OK |

### Global/zzMaw_Legendaries.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | getDistanceToMonster (1) | helper for 21/22 | `setNearbyMonsters` (MCR:2440-2460) | OK |
| 2 | ItemAdditionalDamage (6) | engine add damage 0 | not used under MAW | OK |
| 3 | changePlayer (23) | UI helper | — | N/A |
| 4 | DoBadThingToPlayer (35) | Legendary 13 | `immuneToMonsterSpecialAttacks` | OK |
| 5 | LoadMap (45) | 15 cooldown init | `legendaryProtectionReadyGameMinutes` | OK (order K ITM-L3) |
| 6 | calcManaShield (61) | shield formula | `mawManaShield` | OK |
| 7 | manaShieldManaEfficiency (92) | efficiency, 5 at 50 | `mawManaShieldEfficiency` | OK (>50 capped by skillCap 50 in MAW) |
| 8 | GetTraveledDistance, AfterLoadMap, Timer (108-118, commented) | debug | — | N/A |

### Modules/MawCore/Artifacts.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | Artifacts.Slots (128) | 3 | budget unit | OK |
| 2 | PowerOf, Has, LevelOf (131-144) | data access, level | `MawItemData::artifact`, total level | OK |
| 3 | EnchantUnit, StatUnit, SkillUnit (149-164) | budget units | MIR:1323-1360 | OK |
| 4 | isResistanceStat, isVitalityStat (169-178) | transforms | `mawEnchantReadPower(first=false)` | OK |
| 5 | BonusesOf (186) | rounded bonuses | MIR:1338-1365 | OK (round order noted by pass 1); A1 K ITM-A1 |
| 6 | BaseMult (229) | no entry sets it | — | OK |

### Modules/MawCore/ItemLevel.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | PerPower, POWER_CAP, POWER_HARD_CAP, MaxPower, Max (5-15) | 5, 100, 255 | `MawItemFormulas.cpp` | OK |
| 2 | PowerFor (18) | min(floor(L/5), 100) | `mawItemPowerForLevel` | OK |
| 3 | Tiers, ExpectedTier, buildLadder, LadderTier (23-52) | rungs by run | `items.yml` bases rung | OK |
| 4 | PerTier, TierLevels (54-59) | 3 per rung | `mawLevelRequirement` | OK |
| 5 | OfItem (61) | artifact level / MaxCharges x5 | `weaponDamage`, `armorClass` | OK |
| 6 | GUARD_MARGIN, WearLevel (70-75) | L - (10 + 0.09L) | `mawLevelRequirement` | OK |
| 7 | ForDrop (77) | monster level or 7/8 fallback | `MawRules::mapDropLevel` | OK |

### Modules/MawCore/ItemFields.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | Registry (282) | field documentation | `ItemRulesetFields.h` | N/A (documentation) |
| 2 | describe (331) | debug dump | — | N/A |

### Modules/MawCore/SpecialItems.lua

| # | MAW (line) | What | OpenYAMM | Status |
|---|---|---|---|---|
| 1 | QuestBound (32) | quest bits/awards | MIR:828-841 | OK |
| 2 | Prices (44) | values of value-0 items | `items_patch.txt:814-821` | OK |
| 3 | SellOnce (56) | once a game, seer bits | MIR:844-850 | OK |
| 4 | Text (62) | refusal texts | MIR:861, 877 | OK; item name F FITM-2-8 |
| 5 | questDone (67) | any bit or award | MIR:870-873 | OK |
| 6 | soldOnce (87) | saved set | `MawGameState::soldUniqueItems` | OK |
| 7 | setSellRefusal (96) | refusal in merchant hover text | refusal only on the sell attempt | F FITM-2-8 (cosmetic) |
| 8 | refuses (109) | identify/repair always; value 0 refuses | `canSellItemToHouse` value > 0; no identify/repair refusal | OK |
| 9 | sold (131) | mark, clear seer bit, LostItems | `itemSold` (MIR:881-898) | OK (LostItems N/A: OpenYAMM's seer topic, no money loop) |
| 10 | lostItContinent, GotItem (152, 174) | register priced items for "I lost it" | OpenYAMM's own seer lists | N/A |
| 11 | start / GameInitialized2 (162-173) | install filter and prices | items patch + `sellRefusal` hook | OK |
