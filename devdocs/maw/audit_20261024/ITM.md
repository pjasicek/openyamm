# ITM — items, loot, artifacts, shops, values

Auditor scope: rarity and pity, loot tier and item power, enchant rolls and slot magnitudes, special pools and their
effects, legendary affixes, artifacts, value and prices, level requirement, shop stock, item reads, item-field saves.
MAW paths are relative to `Maw-Mod-MMMerge/Scripts/`. OpenYAMM paths are relative to the repository root. Nothing was
built or run.

Legendary affixes (ITM-L*) and artifacts (ITM-A*) were audited in two sub-passes. Their findings follow the main list
below, in the same format.

## Main findings

### ITM-1: Indoor ground items lose every MAW item field (rarity, enchant 2, item power, legendary, map and craft data)
Severity: P1
Confidence: confirmed (both sides read; no runtime check)
MAW: General/zMaw_ItemBits.lua:1-36, 157-173 — MAW packs every new field into the item's own struct (Charges,
BonusExpireTime, MaxCharges, Bonus2). A dropped item keeps them wherever it lies.
OpenYAMM: game/indoor/IndoorWorldRuntime.cpp:3490-3577 — `writeIndoorHeldItemPayload` and
`readIndoorHeldItemPayload` store an indoor sprite object's item as the raw 0x24-byte MM record. They keep the id,
flags, enchant 1, special, artifactId, rarity and temporary bonus, but not `InventoryItem::rulesetFields` (and not the
wand charges). Paths that write through it:
- `dropHeldItemToWorld` (:16767): the player drops an item indoors.
- `spawnMonsterDeathDropItem` (:14579): monster death drops, including MAW's no-corpse crafting drops and dimension
  maps from `lootWithoutCorpse` (:14428-14447).
- :3787 and :19656.

Picking the item up again (:15146) rebuilds it with empty `rulesetFields`. For example, a Legendary sword dropped and
picked up in a dungeon comes back with:
- no rarity, no second enchantment, no legendary affix;
- item power 0, so weapon damage and AC fall to the level-0 rows;
- drop level 0, so the level requirement changes.

A dimension map loses its target map, and a sealed spellbook, an Oracle's Orb or an Endless Potion loses its
`craftState`. Outdoors is fine: `OutdoorWorldRuntime::WorldItemState` holds a full `InventoryItem`, saved by
SaveGame.cpp:3694-3742. Chest views and corpse views also keep full items.
Not covered by: no related row. GAPS L7.2 covers gathering items, not their fields. HANDOFF §3.7 claims the fields
round-trip.
Suggested fix: carry the full `InventoryItem` (or at least its `rulesetFields`) beside `rawContainingItem` in
`MapDeltaSpriteObject` and save it. Indoor world items then match the outdoor `WorldItemState`. Add a scenario: drop a
MAW item indoors, save, load, pick it up, and compare.

### ITM-2: Hats inflate HP and SP enchantments (the ×1.5 is applied before the vitality growth)
Severity: P2
Confidence: confirmed
MAW: General/zzMaw-Items.lua:2722-2730 (`collectEnchant`) runs `vitalityEnchantPower(power, GetSlotMult(it))` on the
stored strength. `GetSlotMult` (:4407-4425) already includes the hat ×1.5 (helm with `Mod2 == 0`). Only then is the
result multiplied by `ceil(×1.5)`. So the growth term is p / 50 / (1.25 × 1.5). The tooltip
(Modules/MawCore/Tooltip.lua:257-264) uses the same order.
OpenYAMM: game/rules/maw/MawItemRules.cpp:1426-1427 multiplies the power by 1.5 first. It then calls
`mawEnchantReadPower` with `readSlotMultiplier` (:113-116, which includes the hat ×1.5 again). The growth term becomes
1.5p / 50 / 1.875 = p / 62.5 instead of p / 93.75. The inspect line repeats the same order (:1805-1806).

Examples (stored HP strength p, hat):

| p | MAW | OpenYAMM | Difference |
|---|---|---|---|
| 100 | 311 | 390 | +25 % |
| 300 | 1890 | 2610 | +38 % |

Not covered by: no related row.
Suggested fix: compute `mawEnchantReadPower` on the stored power with the hat-inclusive slot multiplier, then apply
`ceil(×1.5)` for hats (both in `applyItemEffects` and `inspectLines`).

### ITM-3: Horned Helm (891) is not treated as a hat
Severity: P3
Confidence: confirmed
MAW: zzMaw-Items.lua:2728 and :4421 test a hat as `EquipStat == 5 and Mod2 == 0`. 891 Horned Helm is `Mod1 = 1`,
`Mod2 = 0` (AC 1, no MAW patch), so MAW reads its enchantments ×1.5 and raises its HP/SP slot multiplier. Its gem cap
(GetSlotMult) is affected too.
OpenYAMM: MawItemRules.cpp:108-111 tests `baseArmorClass == 0`. items.yml:411 gives 891 base AC 1 (dice + Mod2), so it
is a helm. Phynaxian Crown (1325) is Mod1 0 / Mod2 0 and is an artifact, so it is unaffected.
Not covered by: no related row.
Suggested fix: decide whether to keep MAW's quirk. If yes, store a "hat" flag (Mod2 == 0) per base in items.yml rather
than deriving it from base AC. Otherwise add a deviation row.

### ITM-4: A Celestial item's popup shows the drop-time numbers, not the wearer-level ones
Severity: P3
Confidence: confirmed
MAW: Modules/MawCore/Tooltip.lua:205 calls `updateCelestialItem(it)` (zzMaw-Items.lua:1622-1661) before the tooltip is
built. That rewrites the item's enchant strengths and MaxCharges to the current member's level, so the enchant lines,
"Item level", attack speed, special texts and value all show the scaled numbers.
OpenYAMM: the stats use the wearer level (MawItemRules.cpp:1395-1417; combat in MawCombatRules.cpp:417-432), but
`inspectLines` does not:
- enchant lines use the stored `standardEnchantPower` and `secondStandardEnchantPower` (:1810-1811);
- "Attack speed" and "Item level" use the stored `fields.itemPower` (:1845-1846, :1873);
- `enchantDescription` (special damage range and stat texts) uses the stored `itemPower` (:1655-1690);
- `fullValue` (:1505) uses the stored values too.

So a Celestial reads as its drop-level self while it acts at the wearer's level.
Not covered by: GAPS A2.14 (popup lines) does not mention Celestial; D.10 covers the cap only.
Suggested fix: compute the Celestial powers (the same helper as `applyItemEffects`) for the viewer in `inspectLines`,
`enchantDescription` and `fullValue`.

### ITM-5: Morcarack (place-name 160) does not get boss loot
Severity: P3
Confidence: confirmed
MAW: zzMaw-Items.lua:268-293. `mon.NameId > 220 or mon.NameId == 160` gets boss treatment:
- 100 % drop;
- grade lvl / 20 + 2, clamped 2-6;
- `LootContext` boss = true, so the rarity roll uses ÷4 and ×2, +1 tier, the D pool and an enchantable-only re-roll.
OpenYAMM: game/rules/maw/MawMonsterRules.cpp:892 sets `result.boss = pFacts->bossAffix != 0`. Nothing marks
NameId 160, so Morcarack drops as a regular monster.
Not covered by: GAPS A2.7 (boss loot, done) covers affixed bosses only.
Suggested fix: treat the unique with place-name 160 as boss loot in `corpseLoot` (chance, grade, `result.boss`).

### ITM-6: Stored drop level is rounded; MAW floors it, so some level requirements are one higher
Severity: P3
Confidence: confirmed
MAW: zzMaw-Items.lua:1127 `SetStoredDropLevel(it, dropLevel)`. EncodeRarity (zMaw_ItemBits.lua:160) floors it.
`GetLevelRquirement` (:4351-4373) reads that floored level.
OpenYAMM: MawItemRules.cpp:990 stores `mawRound(dropLevel)`. Drop levels are fractional in shops (0.75 × total
level) and on the 7/8 map fallback, so `mawLevelRequirement` (MawItemFormulas.cpp:376-384) can come out one level
higher than MAW's. Reagents (:815) use MAW's round, which is correct there.
Not covered by: no related row.
Suggested fix: store `floor(dropLevel)` for equipment.

### ITM-7: Standard-only specials still grant their Standard bonuses under MAW
Severity: P3
Confidence: confirmed (reachable only through placed or fixed items)
MAW: zzMaw-Items.lua:2566-2585 sets every item stat (0-23, skill stats included) from MAW's own table (`t.Result = 0`
first). GetSkill (:2587-2610) rebuilds item skill bonuses from MAW's table only. So these specials, which MAW does not
list, give nothing:
- Thievery 35, Monks' 60, Thieves' 61, Assassins' 67: their skills;
- Barbarians' 68: its AC;
- Storm 69: its Air resistance;
- Ocean 70: its Water resistance and Alchemy.

MAW zeroes 67-70's weights where they could roll; 35, 60 and 61 have no weight in the table. So these come only from
placed or fixed items.
OpenYAMM: MawItemRules.cpp:456-467 falls back to `ItemEnchantRuntime::applySpecialEnchantBonus` for any special not
handled. Examples: Monks' +3 Dodging and Unarmed, Thieves' +3 Stealing and Disarm, Storm +20 Air and half missile
damage, Ocean +10 Water and +2 Alchemy (ItemEnchantRuntime.cpp:521-640).
Not covered by: GAPS A2.2 (Standard specials under MAW, done) covers the immunity pairs, Protection, Gods and schools
only.
Suggested fix: under MAW, give no stat or skill effect for specials outside MAW's handled set. Keep only engine powers
MAW keeps (Water Walking, Feather Falling, Carnage).

### ITM-8: Small enchant-roll differences
Severity: P3
Confidence: confirmed
MAW and OpenYAMM differ in two places:
- **Strength sync.** MAW zzMaw-Items.lua:1296-1299 sets enchant 2 to enchant 1's strength whenever they are within 1,
  even when enchant 1 is a skill enchant (strength about 3-10 after the sqrt). OpenYAMM MawItemRules.cpp:1059 skips the
  sync for skill enchants, so low-tier items keep enchant 2 one point apart where MAW equalises them.
- **Clubs.** MAW :1179 turns a rolled Unarmed (24) into Armsmaster only for skills 1-7 (staves and clubs, skill 39,
  keep Unarmed). OpenYAMM :1021 converts it on every weapon except staves, clubs included.

Not covered by: no related row.
Suggested fix: drop the `!isSkillEnchant(type1)` condition, and exclude clubs from the Unarmed swap. Or record both as
deviations.

## Checked and matching (main pass)
- **Rarity.**
  - Band widths and caps, the difficulty band multipliers, and the boss ÷4 window (`mawRarityBands`).
  - The upgrade multiplier: difficulty × min(60 + t, 80) / 80 × 2 for bosses × the dimension map factor.
  - Cascade order Celestial → Legendary → Primordial → Ancient.
  - Shop redirect: Ancient at 0.04, no pity. No Legendary or Celestial in shops or Austerity. Omnipotent forces
    Celestial.
- **Pity.**
  - `pity_chance` = base^(1.38 − base·n/2).
  - Counter growth only for rarities above the result that could be rolled, by the multiplier; reset on success.
  - Artifact pity +1 a failure.
  - All counters and drop counts saved (SaveGame.cpp:834-872).
- **Loot tier and power.**
  - Loot tier: grade + floor(level / 15) + map-power and Arena bonus + boss + Omnipotent + fractional round-up.
  - Item power: PowerFor and rollTierCharges ranges (12-20, 16-20, 20-24 with +2, ×1.2 with +4, cap 255).
  - Shop drop level 0.75 × total level.
- **Enchant strength.**
  - encStrUp, normal and Austerity.
  - Strength ranges by rarity, and the different ceil and round order for Common-Epic versus ranged rarities.
  - Difficulty power 1.2, 1.1 or 1.05.
  - Skill nerf ceil(max(√x, x/10)) before the slot multiplier.
  - Slot multipliers 1, 2, 1.25, 1.5, 1, 1.25, 1, 1, 1.25, 1.25, 0.75, 1 (halberds two-handed via items_patch).
  - Enchant 2 floored.
- **Enchant types.** Rings 1-16, others 1-10. Enchant 2 effectively 1-10. Duplicate re-roll within the group. 10 %
  skill enchants, with the Dodge → Armsmaster swap on chain and plate.
- **Specials.**
  - Pools by grade (3 A+B, 4 A-C, 5 B-D, 6 D, D only for bosses) weighted by `ChanceForSlot` of the patched SPCITEMS.
  - The 39/40/41/46 melee/caster swap and the legendary 19 swap (same result in either order).
  - Ruleset specials 39, 40, 74-80 parse and roll.
- **Special effects.**
  - The bonusEffects table (ids, stats, modifiers, 48's pair).
  - chargesStatMult min(1 + P/25, 5). Schools ⌊P/4⌋ + 5; Meditation specials 38/47/55/66 ⌊3P/20⌋ + 3, capped at 2× the
    trained skill.
  - Immunity pairs 18-23 and 25. "of Identifying" +3 / +3. "of Power" gives no +5 Level.
- **Read transforms.** HP/SP growth (non-hat), resistance +10 on the first enchant, ring halving, best per element
  (A1.1), skill enchants from enchant 1 only. Celestial strength round(ceil(encStrUp(L/11 + 5) × power) × 1.25 × slot),
  skills / 10. Celestial power GetPrimordialCharges.
- **Weapons and armour.** Weapon damage rows by power, rung and dice. Armour AC base + round(ref × P / 40) × quality.
  Ladder rungs include MAW's renames of 67 (Mace) and 804 (Longsword).
- **Level requirement.**
  - (drop level + 3 × (rung − 1)) × 0.91 − 10.
  - −6 from Nightmare (Doom and insanity included, as bolster ≥ 300), −3 Doom, −3 insanity; floor, minimum 1.
  - Celestial 1, non-base 0.
  - Checked on equip against the member's base level (Party.cpp:5000).
- **Value.**
  - getItemValue terms: enchant 1 HP/SP sqrt form, AC ×2, skill s² × 100; power / 20 base bonus.
  - Special factor below 11 multiplies (×2.5 more at 10), else adds; scaling specials × P / 20.
  - Legendary ×2.5. Sell and filter ×0.4. Buy value^(1 + 0.08 × count) with +2 for Ancient and Primordial.
  - MAW rounding steps. Gem and special buy prices (reagentPrices).
- **Shops.**
  - Crafting-material substitution: gems always, 30 % of other non-equipment, wands included.
  - Special chance min((gold / 20M)^0.7, 1) with weights 7/7/15/2/5/7/3/15.
  - Gem tier 1 + min(floor(P / 25) + {0 70 %, 1 25 %, 2 5 %}, 15).
  - Reroll cost (floor(P' / 15) + min(floor(own / 18) + 2, 5))² × 250 with P' = getPartyLevel(4) − min(own / 2, 54).
- **Corpse loot.**
  - Regular chance ceil(√L × (1 + tier) × 0.5 + min(%, 50) × 0.3), ×0.5 Doom modes, ×0.75 Nightmare.
  - Grade (max(family B level, map Low) + 10 tier) / 20 with fractional round-up and the 2^(g−1) penalty.
  - 70 % any kind.
  - Boss grade max(base level, map Low) / 20 + 2 in 2-6. Broodling 30/10/4 %.
- **Loot filter.** Thresholds Common-Primordial and the placed-item rank (1 + enchants). Chest gold 10 × (band mean +
  bolster) × 1/2/4 × U(0.66, 1.32). Removed potions 264-289 become 252-263.
- **Saves.** `ItemRulesetFields` round-trips in inventory, equipped runtime state, outdoor world items, chest and corpse
  views (SaveGame.cpp:722-920, 1119-1150, 3694-3742). Indoor world items do not (ITM-1).
</content>
</invoke>

## Legendary affixes (sub-pass)

### ITM — legendary affixes (MAW ids 11-35)

Scope: the 25 legendary affixes: roll, storage, wear rules and each effect. MAW paths relative to
`Maw-Mod-MMMerge/Scripts/` (DM = `Modules/MawCore/Damage.lua`, IT = `General/zzMaw-Items.lua`, ST =
`General/zzMaw-Stats.lua`, SP = `General/zzMaw-Spells.lua`, SK = `General/zzMAW-Skills.lua`, LG =
`Global/zzMaw_Legendaries.lua`). OpenYAMM: MCR = `game/rules/maw/MawCombatRules.cpp`, MIR =
`game/rules/maw/MawItemRules.cpp`. Known rows respected: GAPS L4.1, L4.6, L5.7, L5.8, §11 D.11 (21 melee only),
DEVIATIONS 71.

### ITM-L1: Legendary 11 never shortens recovery after a melee kill
Severity: P2
Confidence: confirmed (read both sides; the unit test sets the recovery by hand, so it passes)
MAW: DM:1099-1116 — on a single-target kill, the *next tick* halves `pl.RecoveryDelay`, i.e. the recovery the
attack just set.
OpenYAMM: MCR:2752-2757 halves `recoverySecondsRemaining` inside `applyPartyHitEffects`, which the melee path calls
at `game/gameplay/GameplayActionController.cpp:1154`, before the attack's own recovery is applied at :1434
(`Party::applyRecoveryToMember` takes `max(current, recovery)`, Party.cpp:6474). The member was ready, so 0 is halved
and the full recovery is then set. Melee kills (the affix's main use) get nothing, in real time and turn-based
(`storeMemberTurnRecovery`). Spell kills work (combat events arrive after the cast's recovery). The test
`MawGapTests.cpp:1112-1115` sets `recoverySecondsRemaining = 2` before calling the rule, so it does not see this.
Not covered by: GAPS L4.1 (marked done), no DEVIATIONS row.
Suggested fix: carry a "halve recovery" flag on the attack result and apply it after the attack's recovery (or
halve in `applyRecoveryToMember` for that attack); add a test through the action controller.

### ITM-L2: Legendaries 14, 29 and 17 sit at the wrong places in the monster damage pipeline
Severity: P2
Confidence: confirmed (stage order read on both sides)
MAW: DM:1506-1540 order is resistance (with spear and 29 stacks *added* at DM:546-577) → boss affixes
(Adamantite, DM:928-929) → `stage_legendaries` (DM:972-1116: adds each hand's enchant and Fire Aura damage, then 17's
2 % HP, then ×21, then ×max(critChance,1) for 14) → `stage_damageTaken` (DM:1133-1138: ×(1+29 stacks/100) on the
whole hit, "every post-res addition included"). So 14's over-crit and 29's stacks multiply the enchant/aura damage
and 17's extra, and Adamantite never cuts the enchant/aura damage, 17's extra or 21's bonus. 14's factor uses the
melee crit chance (`getCritInfo(pl,false,monsterLevel)`) for every hit kind.
OpenYAMM: 14 multiplies only the rolled base (`critFactor`, MCR:250-254, used at MCR:1446, 1717, 1885, 1956); spells
use the spell crit chance at the party's banked level (MCR:1875-1883). 29 and the spear stacks multiply `hit.amount`
in `damage-taken-stacks` (MCR:731-754) *before* the `resistance` stage adds the hand's enchant/aura elements
(MCR:793-805), and 17's extra is added after it (MCR:818-851), so neither is multiplied by 29. `boss-affixes`
(Adamantite, MCR:859-868) runs *after* `legendary-blows`, so it cuts 17's extra, 21's bonus and the
enchant/aura damage. Example: base 100 after resistance, Adamantite flat 500, 17 extra 1000: MAW 25 + 1000 = 1025,
ours max(1100 − 500, 275) = 600. Also, an area spell always gets +1 % for its own stack (MCR:743-744) while the
stored stack is added only 40 % of the time (MCR:2674-2681); MAW multiplies by the stored stacks only.
Not covered by: GAPS L4.1, A1.x rows; DEVIATIONS 46 (missiles' enchant typing only). No related row.
Suggested fix: apply 14's over-crit factor and 29's stacks as late stages on the final amount (after 17/21 and the
elements), and run Adamantite before the enchant/aura elements and `legendary-blows` are added (or apply it to the
base only). Count this blow's 29 stack only when it is really stored.

### ITM-L3: Legendary 15 triggers before Mana Shield
Severity: P3
Confidence: confirmed
MAW: DM:1866-1886 — `calcManaShield` first, then 15 fires only if what is left is still ≥ HP.
OpenYAMM: MCR:2146 calls `legendaryProtection` before the Mana Shield (MCR:2148-2157). A hit that is lethal before
the shield but not after spends the 150-minute cooldown and sets HP to max/4 (which can lower HP: a member at 60 %
hit by 70 % that the shield would halve ends at 25 %).
Not covered by: GAPS A1.7 / L4.1 (done), DEVIATIONS 71 (lists the shields, not their order).
Suggested fix: run Mana Shield, then legendary 15, then Divine Protection, as MAW.

### ITM-L4: Legendaries 18 and 22 cut after the Shaman/Seraph flat reduction instead of before
Severity: P3
Confidence: confirmed
MAW: ST:762-776 `applyPostMitigation` — damage floor, ×0.9 (18), ×max(0.97^n, 0.5) (22), then the flat class
reduction `max(d − flat, d/4)`.
OpenYAMM: `mawMitigatedDamage` applies the floor and the flat reduction together (`MawCombatFormulas.cpp:226-230`),
then the `legendary-defense` stage (MCR:1001-1015) cuts. Different numbers for Shaman/Seraph wearers (100 dmg, flat
50: MAW 40, ours 45).
Not covered by: no related row.
Suggested fix: move the flat reduction after the 18/22 cut (e.g. pass the legendary multiplier into
`mawMitigatedDamage`).

### ITM-L5: Legendary 24 restores a share of the full bars, not of the pools left after reservation (its own text)
Severity: P3
Confidence: confirmed
MAW: DM:1083-1097 uses `GetMaxHP`/`getMaxMana` (zz_Maw-initialize.lua:446-458, SP:3489-3504: the current HP/mana
pool after buffs reserve theirs); MAW's text (IT:1614-1616) says so, and our items.yml copies that text.
OpenYAMM: MCR:2745-2750 heals 10 % of `effectiveMaximumHealth` and 5 % of `effectiveMaximumSpellPoints` (full bars).
A caster reserving half their mana gets twice MAW's SP (then clamped to the pool by the aura pass).
Not covered by: no related row.
Suggested fix: use max − `reservedHitPoints`/`reservedSpellPoints` (as `MawSpellRules.cpp:1391-1394` does).

### ITM-L6: Legendary 27 never sends the overheal to an unconscious member
Severity: P3
Confidence: confirmed
MAW: DM:1312-1318 → `pickLowestPartyMember` (zzClasses.lua:238-257): lowest HP share among all members not Dead or
Eradicated, so an unconscious member (negative HP) is picked first and can be brought back.
OpenYAMM: MCR:2944-2965 considers only `conscious(candidate)` members.
Not covered by: no related row.
Suggested fix: exclude only dead and eradicated (and petrified, if desired as a deliberate deviation).

### ITM-L7: Legendary 30 threshold: MAW multiplies max(HP, SP) by the efficiency; we follow its text (question)
Severity: P3
Confidence: confirmed
MAW: DM:1908-1916 — `fullHP = max(fullHP, fullSP) * manaShieldManaEfficiency(pl)`; the efficiency is
1 + skill^1.4/60 ≥ 1 (LG:92-102), so the threshold is the larger bar × efficiency (HP 1000, SP 200, Mana Shield 30:
2960). The text says "SP multiplied by mana shield efficiency instead, if higher".
OpenYAMM: MCR:3302-3313 `max(fullHP, fullSP × efficiency)` (same example: 1000). Matches the text, not the code; no
deviation row.
Not covered by: no related row (A1.7 covers the thresholds, not 30).
Suggested fix: decide; if the text is kept, add a DEVIATIONS row ("MAW code multiplies HP too").

### ITM-L8: Legendary 28 says "doubled", gives ×1.5 (MAW bug ported as-is?)
Severity: P3
Confidence: confirmed
MAW: text IT:1597 "AC gained from armors is doubled"; code IT:2713-2715 ×1.5. ITEMS.md §4.3 notes it.
OpenYAMM: `MawCharacterSheet.cpp:374` ×1.5 with the "doubled" text in `rulesets/maw/data/items.yml` (28).
Not covered by: no DEVIATIONS/GAPS row.
Suggested fix: keep ×1.5 and correct the tooltip text (or ×2), and record it either way.

## Checked and matching
- Roll: every Legendary and Celestial drop rolls one affix of 11-35, weighted 1/(count+1) by the save-wide drop
  counts (IT:1234-1240, 1372-1399; MIR:1068-1087); counts saved (`SaveGame.cpp:839/872`); stored per item
  (`ItemRulesetFields::legendaryAffixId`, SaveGame.cpp:736/908).
- 19's special swap (40→39, 41→46) and the melee/caster swap give the same result in our order (MIR:1091-1127).
- Active only while equipped and not broken, no stacking (MIR:180-198; IT:3386-3391 EnumActiveItems + table.find).
- 12 echo 40 % Might/Acc ↔ Int/Pers on base stat enchants only (IT:2731-2741; MIR:610-625; per-enchant rounding only).
- 13 blocks monster special attacks (LG:35-42 DoBadThingToPlayer; GameplayCombatController.cpp:1104-1108).
- 14 +10 % crit chance and no 100 % cap (ST:133-138; MawCombatFormulas.cpp:186) — placement in ITM-L2.
- 15 quarter of full HP, 150 game minutes, conscious only, cooldown saved (DM:1870-1885; MCR:2159-2176,
  SaveGame.cpp:614/675) — order in ITM-L3.
- 16 ×1.5 on the collected best resistance enchant per element (ST:1120-1123; MIR:1404, 1425-1430); popup (A2.14).
- 17 2 % current HP through physical resistance, ×0.5 arrows and area spells, melee/ranged speed multiplier, DK and
  Assassin spells melee, others 1.015^Ascension, blasters as spells (DM:1021-1044; MCR:825-851) — placement ITM-L2.
- 18 ×0.9, 22 ×max(0.97^n, 0.5) with monsters within 512 minus radius (ST:723-768; MCR:1001-1015, 2410-2421) —
  order in ITM-L4.
- 19 ×1.5 on enchant and Fire Aura damage, melee, missiles and spells (IT:2097-2104, 2136, 4296; MCR:551, 569, 1564).
- 20 Meditation ×(1 + reserved share) (Formulas.lua:207-217; MawSkillRules.cpp:977-983).
- 21 +5 %/monster within 512, cap ×2, melee only per D.11 (DM:1063-1073; MCR:855-858).
- 23 coverer heals 3 % (SK:1294-1296, MON:3982-3984; MCR:2117-2122).
- 25 Ascension +10, 33 Staff/Sword/Dagger/Axe/Spear/Mace +10, once, interplay with Supreme Armsmaster's 2× cap
  equivalent (SK:2597-2627; MIR:1289-1301, MawClassRules.cpp:269-282).
- 26 enchant and Fire Aura roll their own crits on blows and spells; arrows roll one for both (minor)
  (IT:2137-2145, 4297-4304; MCR:1449-1455, 1496-1500, 1552, 1886-1908).
- 29 1 % per attack, 40 % for area spells, reset on death/revival (DM:569-577, ST:936-945; MCR:2672-2681) — placement
  ITM-L2.
- 31 half the heal to mana at the same bar share, half to HP (DM:1222-1228, 1300-1309; MCR:2930-2938).
- 32 auras reserve HP with the class HP factor; utility auras flat (SP:2762-2790, 3029-3040; MawSpellRules.cpp:203-206,
  802-845, 1039-1054).
- 34 refund floor(cost × overheal share), 35 recovery ×(1 − share/2) on heal spells (SP:1149-1180;
  MawSpellRules.cpp:644-665, PartySpellSystem.cpp:1445-1455, 3015-3018).
- Texts of all 25 affixes match MAW's, including 24's and 29's GameInitialized2 rewrites (IT:1572-1619;
  `rulesets/maw/data/items.yml:7-33`).

## Artifacts (sub-pass)

### ITM — artifacts sub-audit

Scope: MAW artifact data, scaling and behaviours (MawCore/Artifacts.lua, artifactPower and mawArtifacts in
zzMaw-Items.lua, zzzMaw_Artifacts.lua, ItemLevel.lua) against `assets_dev/rulesets/maw/data/items.yml`,
`MawItemData`, `MawItemRules`, `MawCombatRules`, `MawSkillRules`, `MawClassRules`.
MAW paths are relative to `Maw-Mod-MMMerge/Scripts/`; OpenYAMM paths to the repository root.
Known and not re-reported: DEVIATIONS 15, 16, 46, 70, 72, 73, 74; GAPS A2.5, A2.6, L4.3, A1.16.

### ITM-A1: Guardian (507) is a one-handed artifact in items.yml; MAW makes it two-handed
Severity: P2
Confirmed: yes (both sides read)
MAW: General/zzMaw-Items.lua:1410-1414 sets EquipStat 1 (two-handed) for the halberds {46-50, 507, 838-840,
1638-1640} at GameInitialized2. GetSlotMult (zzMaw-Items.lua:4407-4425) then returns 2 for 507, so its budget unit
(Artifacts.lua:71-80) is doubled. IsTwoHandedWeapon (zzMaw-Items.lua:4555) is true, so GetWeaponDamage/GetWeaponDamageRows
(4569-4593) give it full two-handed dice and flat damage.
OpenYAMM: `content/items_patch.txt` makes 507 `Weapon2`, but `data/items.yml:41` has
`507: {slot_mult: 1, two_handed: false}`. Effect: `MawItemRules::applyItemEffects` (MawItemRules.cpp:1338-1356)
multiplies its 7 × 0.43 stat budget by 1 instead of 2. `MawItemRules::weaponDamage` (:1146-1153) builds its base damage
with `pArtifact->twoHanded == false`, which halves both dice and flat. The on-hit range and recovery read the patched
item (`isTwoHanded`), so those are already two-handed, and the item is inconsistent with itself.
Not covered by: GAPS A2.4 (halberds two-handed; only the equip stat was patched, not the artifact row); no DEVIATIONS row
Suggested fix: set 507 to `slot_mult: 2, two_handed: true` in items.yml and in the generator that writes it.

### ITM-A2: Tournament Bow (531) and Ethric's Staff (1317) use ladder rung 6; MAW reads 3.5 and 1.357
Severity: P3
Confirmed: yes
MAW: GetWeaponFlatDamage (zzMaw-Items.lua:4562-4567) gives tier 6 only to IsArtifactWeapon items, meaning those in
artWeap1h/artWeap2h (2330-2331). 531 and 1317 are in neither list, so they read `LadderTier` of their NotIdentifiedName
run: 531 is alone (3.5) and 1317 sits in the 1316-1330 "Relic" run (1.357). Our own spec records this:
devdocs/maw/data/artifacts.yml:1239-1250, 1876-1892, 4136.
OpenYAMM: items.yml gives 531 and 1317 no `rung`, so `MawItemData` defaults it to 6 (MawItemData.cpp `rung` default 6).
Only 532 got `rung: 3.5`. Result: 531's flat damage is 8 instead of 4 (one-handed halving), and 1317's is 16 instead
of 1.14.
Not covered by: no related row
Suggested fix: add `rung: 3.5` to 531 and `rung: 1.357` to 1317, and fix the generator that dropped them.

### ITM-A3: Printed AC of ring, amulet and helm artifacts outside artArmors is lost
Severity: P3
Confirmed: yes
MAW: collectArmorAC (zzMaw-Items.lua:2691-2717) counts `Mod1DiceCount + Mod2` for every item with Skill 40 except
EquipStat 12 (wands), so rings and amulets count too. Artifacts not in artArmors keep their printed AC unscaled:
Arthur 2029 (5), Odin 2044 (10), Guinevere 2032 (2), Igraine 2033 (2), Morgan 2034 (3), Aphrodite 2047 (4),
Athena 2048 (4), Hera 2049 (6).
OpenYAMM: these are `base: flat` in items.yml with no `printed_ac`, so `MawItemRules::armorClass` (:1181-1191) returns
0, and `baseStats` replaces the table AC with that 0. Separately, `mawArmorBreakdown` (MawCharacterSheet.cpp:512-548) only
sums off-hand, armour, helm, belt, cloak, gauntlets and boots, so ring and amulet AC would be dropped even if the printed
value were present.
Not covered by: no related row (artifacts.yml note 5 records only MAW's tooltip/sheet mismatch)
Suggested fix: write `printed_ac` for `flat` artifacts, and include the amulet and ring slots in `mawArmorBreakdown`.

### ITM-A4: Standard artifact powers under MAW: Galahad/Pellinore +20 AC dropped, Excalibur's skill-scaled attack kept
Severity: P3
Confirmed: yes for the code; Excalibur's MAW-side value is plausible (see below)
MAW: artifactBuffs (zzzMaw_Artifacts.lua:735-749) give Galahad (2026) and Pellinore (2027) Stoneskin 20, and Excalibur
(2023) Bless with power 3 (refreshBuff sets Power = 3). The engine's GetMeleeAttack, which MAW reads
(zzMaw-Stats.lua:470, 1203), therefore sees at most +3 attack from it.
OpenYAMM: the artifact branch of `MawItemRules::applyItemEffects` (MawItemRules.cpp:1306-1320) runs Standard's effects
and then restores all of `magicalBonuses` except melee/ranged attack and damage. Two consequences:
(a) Standard's Stoneskin stand-in, `magicalBonuses.armorClass += 20` for 2026/2027 (ItemEnchantRuntime.cpp:1290-1300),
is discarded. DEVIATIONS 73 says these stay "Standard's item powers (... +20 AC ...)".
(b) Excalibur's Standard Bless, `mmergeItemBuffPower(member, "Sword")` = max(3, Sword level × rank / 2) on melee and
ranged attack (ItemEnchantRuntime.cpp:1268-1276), is kept and reaches `summary.combat.attack` (GameMechanics.cpp:2449),
which is MAW's hit-chance attack. At Grandmaster Sword 50 that is +100 attack against MAW's +3, on top of dev 73's
Bless hit-chance bonus.
Not covered by: DEVIATIONS 73 (it describes the intended Stoneskin AC, which the code drops, and does not mention a Bless
attack bonus)
Suggested fix: in the artifact branch, carry Standard's armour class for the Stoneskin artifacts (or add a flat 20), and
do not keep Standard's Excalibur attack (or keep only 3).

### ITM-A5: Medusa's Mirror (1341) grants no stone immunity in either ruleset
Severity: P3
Confirmed: yes (no code path found)
MAW: artifactImmunities[1341] = Stone (zzzMaw_Artifacts.lua:827-828), and MMMerge's ExtraArtifacts.lua:986 has the same.
OpenYAMM: 1341 has no case in `applyRareItemBonus` (ItemEnchantRuntime.cpp:824-1443), no effect profile or flags in
items.txt, and no immunity field in items.yml. Its "of the Medusa" text sits in a column parsed as an integer (0). The
MAW branch (Standard effects plus budget) therefore gives no Petrified immunity, and Standard does not either.
Not covered by: GAPS L4.3 ("immunities are Standard's powers, which match": they do not for 1341)
Suggested fix: add Petrified immunity for 1341. It is a Standard fix as well, so it needs the user's agreement.

### ITM-A6: Artifact on-hit damage is paced by the artifact's own recovery; MAW uses the two hands' average
Severity: P3
Confirmed: yes
MAW: MawArtifactOnHitDamage (zzzMaw_Artifacts.lua:455-466) multiplies by `GetPlayerBaseRecovery(pl, it)/100`. For a melee
weapon that is the average of both held weapons' getItemRecovery (zzMaw-Items.lua:2106-2122); only a bow uses its own.
OpenYAMM: `artifactHitRange` (MawCombatRules.cpp:692) uses `weaponRecovery(rules, weapon)`, the artifact's own pace,
although `enchantPace` (:504-521) already implements MAW's average for enchantments. Dual wielding a fast and a slow
weapon differs.
Not covered by: no related row
Suggested fix: use `enchantPace(...)` in `artifactHitRange`, which needs the character and item table.

### ITM-A7: Artifact on-hit damage passes through stages that MAW runs before it
Severity: P3
Confirmed: yes for melee; plausible for the missile crit
MAW: the "artifact-on-hit" stage comes after "boss-affixes" and "legendaries" (Modules/MawCore/Damage.lua:1489-1496). So
the Adamantite cut and Legendary 21's ×(1 + 0.05n) never touch it, and it is resisted by its own kind
(zzzMaw_Artifacts.lua:512-513), arrows included (Percival Fire, Ullyses Water, Artemis Air).
OpenYAMM: the on-hit roll is added to the blow itself (MawCombatRules.cpp:1502-1516) or to the arrow's range (:1570-1576).
Then the "boss-affixes" stage (Adamantite, :862-870) and Legendary 21 (:854-857) act on `hit.amount`, which includes it.
On missiles it also joins the arrow's min/max, so it is resisted as physical and crits with the arrow at impact.
Not covered by: DEVIATIONS 46 (covers the bow slot's damage enchantment and Fire Aura, not artifact on-hit)
Suggested fix: keep the artifact share apart and add it after those stages, or extend DEVIATIONS 46 and record the stage
order.

### ITM-A8: Ethric's Staff spares every class whose name contains "Lich", Lich King included
Severity: P3
Confirmed: yes
MAW: artifactDrain[1317] = {HP = -3, ExemptClass = const.Class.Lich} (zzzMaw_Artifacts.lua:604-606, 616-625). Only the
Lich class is spared.
OpenYAMM: `MawCombatRules::updateArtifacts` (MawCombatRules.cpp:2353-2359) spares any member whose canonical class name
contains "Lich". "Lich King" (the final Death Knight promotion, `content/class_patch.txt:7`) is therefore spared too.
Not covered by: no related row
Suggested fix: compare the class to the Lich class itself.

### ITM-A9: Horn of Ros and Ghost Ring buffs are applied only when absent, so they can lapse for up to a game minute
Severity: P3
Confirmed: plausible (needs a runtime check)
MAW: refreshBuff (zzzMaw_Artifacts.lua:755-762) extends ExpireTime to now + 3 game minutes on every 2 s tick, so the buff
never lapses while the item is held.
OpenYAMM: `updateArtifacts` (MawCombatRules.cpp:2236-2262) re-applies Detect Life and Preservation only when
`hasPartyBuff`/`hasCharacterBuff` is false. The buff lasts 6 s and is checked every game minute (2 s), so it expires
before it is renewed. MAW's buffs carry skill 3 (Master); ours are cast at Expert.
Not covered by: DEVIATIONS 73 (the buffs are ported; their refresh is not discussed)
Suggested fix: refresh while held (extend the expiry each tick) instead of re-applying once it is gone.

### ITM-A10: Artifacts have no level requirement; MAW's is 1-3
Severity: P3 (negligible)
Confirmed: yes
MAW: GetLevelRquirement (zzMaw-Items.lua:4351-4373) applies to artifacts too. The drop level is 0, plus TierLevels of the
ladder run (for example 1302-1315 reach +15), which gives max(1, floor(L - 10 - 0.09L)) = 1 to 3.
OpenYAMM: `MawItemRules::levelRequirement` (MawItemRules.cpp:1475-1482) returns 0 for anything that is not a base item.
This only matters to a level 1-2 character, and the popup does not show the line.
Not covered by: no related row
Suggested fix: optional. Compute it from the rung, or record it as a deviation.

## Checked and matching
- Every artifactPower entry (98) against items.yml: all stat, skill and Flat coefficients identical (script check), and
  no MAW entry sets baseStatMultiplier.
- Drop list: membership and weights equal mawArtifacts (104 slots, 533 twice, 532 absent; the drop-0 entries cover the
  quest, placed and shop artifacts and the blasters). Pity is 0.005^(1.38 - 0.0025 × failures), with +1 per miss and a
  reset on success, saved in SaveGame (artifactPity, artifactDrops). Shops are excluded. The roll is limited to
  enchantable base items: the bases list equals MAW's id bands minus the four blasters (415 ids).
- Budget unit: encStrUp(L/15 + min(1 + L/15, 6)) × difficulty power × slot multiplier at the party's total level. Skill
  unit is ceil(max(√u, u/10)) × slot. Resistances go to the sheet resistance, not the item-enchant channel (as MAW), and
  rings are halved. The HP/SP read transform is applied. Our code rounds before the transform and MAW after, which
  differs by about 1-3 points on HP/SP and ring resistances (not reported).
- Slot multipliers of all artifacts, hats at 1.875 included (Mod2 = 0 helms 521, 536, 1325). Two-handedness of every
  weapon artifact except 507 (ITM-A1). Dice counts with the MAW Mod1 patches (1309, 1310, 1311, 1329, 2020).
- Artifact armour: the artArmors set equals our `base: armor` set. Printed and reference AC are recomputed from the
  composed table (NotIdentifiedName runs, MAW patches for 1326/1337) and all match. The formula is
  printed + round(ref × PowerFor(total level) / 40) × quality.
- Artifact weapon damage is a tier-6 weapon at the party's level (GetWeaponDamageRows split, quality).
  weaponLevelDamage ignores the flat term, as MAW's levelDamage does.
- On-hit table: kinds, coefficients, MultVs kinds and factors, Slow on 523/525 at Sword skill, spells for
  1308/2025 (Fireball), 2021 (Lightning Bolt when the target survives) and 2035 (Acid Burst). The enchantment 46
  reference range and its two-handed floor read the patched equip stat. Elemental on-hit damage is not crit, as in MAW.
- Spell-school bonuses (artifactSpellBonus, all 17 entries mapped correctly), half the trained skill within the 2×
  cap. Attack-speed ×0.9 on 515, 1302, 2024 and 2025, applied after the delay recompute, broken items excluded.
- HP regeneration artifacts {509, 520, 1337, 1331, 1335, 2027} and SP artifacts {513, 1334, 1331, 2024, 2032, 2033,
  2034} give 0.2 %/s each (MawSkillRules.cpp:968-985).
- Hades' −10 % melee leech and the vampiric artifacts (dev 70). Cycle of Life's pool, middle, half-transfer and wake-up
  match. Ethric's −3 HP per 5-minute tick (except ITM-A8).
- Wear requirements: MAW's artifactWearReq equals MMMerge's WearItemConditions (same ids and checks). Immunity ids equal
  MMMerge's for 1307, 1309, 1322, 1332, 2030 and 2043 (1341 is ITM-A5).
- Value: artifacts and blasters keep the table value in both. "Artifact level" is the party's total level, read live.
