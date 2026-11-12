# MAW (MMMerge) — item side: analysis for an OpenYAMM ruleset

First-pass overview. Corrected on 2026-10-22 against the verified specs listed in [README.md](README.md); where they
differ, the spec documents win.

Repo analysed: `/home/pjasicek/github/Maw-Mod-MMMerge` (HEAD `ef23ee17`). All paths below are relative to
`Scripts/` unless stated. Line numbers are from that checkout.

Sources read: `General/zzMaw-Items.lua` (4606 lines), `General/zzAlchemy.lua` (the crafting code actually lives
here, not in the item files), `Global/zzMAWPotions.lua` (potion-on-item crafting),
`General/zzMaw-Item-Sorter.lua`, `General/zzMaw-MultiBag.lua`, `General/zzzMaw_CraftingBag.lua`,
`General/zzzMaw_Artifacts.lua`, `General/zMaw_ItemBits.lua`, `General/zzzzMalekith-Randomizer.lua`,
`Global/zzMaw_Legendaries.lua`, `Global/ExtraArtifacts.lua`, `Modules/MawCore/{ItemFields,ItemLevel,SpecialItems,
Artifacts,Tooltip,Formulas,Estimates}.lua`, `General/zzMAW-Skills.lua` (attack speed), `General/zzMaw-Monsters.lua`
(drop level, K key), `General/zz_Maw-initialize.lua` (key bindings, settings page), `Data/Tables/*`, the three
text tables inside `Data/zMaw.T.lod`, and the image-only PDF `MAW 5.0 Loot Guide.pdf` (14 pages, read visually).

**Important framing.** The README is partly stale. The code now has **8 rarities** (Common, Uncommon, Rare, Epic,
Ancient, Primordial, Legendary, Celestial), **28 crafting items + Endless Potion + Crafting Cube** (20 gem tiers and
8 special items), not "14". The code is mid-migration into a "MawCore" layer (`Modules/MawCore/README.md`), so many
legacy globals coexist with newer, documented helpers. Where README and code disagree this document follows the code
and flags the difference.

---------------------------------------------------------------------------------------------------------------------

## 1. Item generation

### 1.1 Pipeline

```
events.PickCorpse (zzMaw-Items.lua:161)
   seeds RNG (§1.13), rewrites monster gold dice, drop %, TreasureItemLevel (= item "grade" 1-6)
   LootContext.set{monsterLevel, boss, omnipotent}
   -> engine generates the item ->
events.ItemGenerated (zzMaw-Items.lua:973)
   LootContext.take()          one corpse feeds exactly one drop
   reseed math.random from vars.SeedList[itemNumber]   (§1.13)
   0.5% artifact substitution (§4.1)
   misc-shop crafting-material substitution (§3.6)
   enchantable base item -> full MAW roll (rarity, charges, enchants, affix, celestial)
   loot filter -> convert to gold (§1.15)
```

Chests/map objects without a corpse context use `MawMapDropLevel()` (zzMaw-Monsters.lua:1926) as the drop level:
the median native monster level of the map (`totalLevel[...]`), else a static estimate from `mapLevels`
(map Low/Mid/High), party level (free progression), madness tables or map-affix power (`Power*10+20`).

`events.GenerateItem` (zzMaw-Items.lua:1) only clamps treasure strength 7 to 6. `ItemGenerated` returns early on
`t.Strength==7`, on screens 16/21 (party creation etc.), and on map index 0.

"Enchantable" = `IsEnchantableItem`: base equipment id bands MM8 1-151, MM6 803-936, MM7 1603-1736, minus the four
"ancient weapons" (blasters 866, 867, 1666, 1667) (zzMaw-Items.lua:95-112).

### 1.2 Monster drop chance and item grade (zzMaw-Items.lua:207-299)

Gold (`TreasureDice`), for monster variant tier 1/2/3 (`Id % 3`: 1=weak, 2=mid, 0=strong):
`newGold = (bolsterLevel2 + lvl) * 7.5`, ×0.5 weak, ×2 strong. If the monster had gold and `newGold` is larger,
`DiceCount = DiceSides = min(sqrt(newGold), 255)`.

Regular monsters with no fixed item (`mon.Item==0`, not a boss):

- `TreasureItemPercent = ceil(sqrt(mon.Level) * (1+tier) * 0.5 + min(origPercent,50) * 0.3)`;
  ×0.5 in Doom (`vars.Mode==2`), ×0.75 at bolster 300.
- grade: `itemTier = (max(baseLevelOfMiddleVariant, mapLevels.Low) + 10*tier) / 20`, fractional part rolled as a
  chance, clamped 1..6 → `TreasureItemLevel`. If it rounds to ≤0, the drop % is multiplied by `2^(itemTier-1)`.
- 70% of drops have their item type forced to "any" (`TreasureItemType=0`).

Bosses (`NameId` 221-300 or 160): 100% drop (Broodling bosses 30/10/4% by variant). Grade
`lvl/20 + 2` (fraction rolled), clamped 2..6, where lvl is the base or unique monster level. "Omnipotent" bosses
force a Celestial. Resurrected monsters (`NameId>300`): drop % ÷4, gold dice ÷4.

A boss drop that is not an enchantable base item is re-rolled with `Item:Randomize` (the handler re-enters itself;
`LootContext.restore` exists for that, zzMaw-Items.lua:978-986).

### 1.3 Loot tier — the master number (zzMaw-Items.lua:1107-1143)

```
dropLevel = monster level (getMonsterLevel: bolstered/unique/boss level)       -- corpse
          = MawMapDropLevel()                                                   -- chest/object
          = getTotalLevel() * SHOP_LEVEL_SHARE(0.75)                            -- shops (party level!)
lootTier  = t.Strength (grade 1..6)
          + floor(dropLevel / TIER_LEVELS(15))
          + GetEnchantTierBonus()   = floor(max((mapAffix.Power - 28)/2, 0)) + 20 in the Arena (d42.blv)
          + 1 boss + 1 omnipotent
          + 1 with probability (dropLevel % 15)/15
```

The party's level does not count except in shops. Rarity odds stop changing at tier 20; enchant strength keeps
growing to tier 37.

### 1.4 Rarity roll

`const.Rarity = {Common=1, Uncommon=2, Rare=3, Epic=4, Ancient=5, Primordial=6, Legendary=7, Celestial=8}`.

**Band roll (Common..Epic)** — `GetEnchantChance` / `GetEnchantBands` (zzMaw-Items.lua:624-665):

| threshold | Base | PerTier | Cap |
|---|---|---|---|
| Epic | 5 | 0.75 | 20 |
| Rare | 20 | 2 | 60 |
| Uncommon | 60 | 1 | 80 |
| Common | 100 | 0 | 100 |

Band widths are the differences between consecutive thresholds (Epic=E, Rare=R−E, Uncommon=U−R, Common=100−U),
multiplied by a per-difficulty `rarityBandMult` and renormalised to 100:

| difficulty index | Epic | Rare | Uncommon |
|---|---|---|---|
| 1-3 (bolster 40/70/100 = Easy/Normal/MAW) | 1 | 1 | 1 |
| 4 (bolster 150, Hard) | 1.5 | 1.4 | 1.4 |
| 5 (bolster 200, Hell) | 2 | 1.8 | 1.6 |
| 6 (bolster 300, Nightmare) | 2.5 | 2.2 | 1.8 |
| 7 Doom | 3 | 2.6 | 2 |
| 8 Road to Insanity | 4 | 3 | 2.2 |
| 9 Beyond Madness | 5.5 | 3.4 | 2.4 |

One uniform roll walks the bands best-first. **Bosses divide the roll by `BOSS_ROLL_DIVISOR=4`** (only the top 25%
of the table is reachable, so never Common; Rare disappears at high tiers on hard difficulties).

**Upgrade cascade (only if the band roll gave Epic)** — `RollItemRarity` (zzMaw-Items.lua:782-820). For rarity =
Celestial, Legendary, Primordial, Ancient (in that order), first success wins:

```
base chance:  Celestial 0.002, Legendary 0.03, Primordial 0.04, Ancient 0.12   (rarityUpgradeChance)
chance = pity_chance(base, counter) * mult      (Ancient has no pity)
mult   = rarityDifficultyMult[d]                1,1,1,1.1,1.2,1.4,1.6,1.8,2 for d=1..9
       * min(60+tier, 80)/80                    (the Uncommon curve: 0.75 at tier 0 -> 1 at tier 20)
       * sqrt(lootMultiplier)                   (always 1 in practice; LootContext.multiplier is never set)
       * 2 for bosses                            (BOSS_RARITY_MULT)
       * (1 + (mapPower*nAffixes + 20*nAffixes)/400)   for dimension maps
```

Shops: Legendary/Celestial/Primordial blocked; Ancient uses the Primordial base (0.04) and has no pity
(`shopRarityRedirect`). Austerity mode and shops block Legendary/Celestial (`noLegendary`). Omnipotent forces
Celestial.

**Bad-luck protection** (`pity_chance`, zzMaw-Items.lua:4471):
`chance' = base ^ (1.38 − base*failures*0.5)` (returns 1 once base≥1). Counters (`vars.primordialPityCounter`,
`legendaryPityCounter`, `celestialPityCounter`) grow by `mult` on every Epic-band roll that ended below that rarity
and that could legally have produced it; reset to 0 on success. Right after a reset the chance is far below nominal
(Legendary 0.79% ≈ 26% of 3%; Primordial 1.18% ≈ 29%; Celestial 0.019% ≈ 9%); it becomes certain after
`2.76/base` units of counter (Legendary 92, Primordial 69, Celestial 1380). With the exponent 1.38 the average
wait is 0.961–0.990 × 1/base ([RANDOMS.md](RANDOMS.md) §4.3). The same function drives artifact drops and
crafting-item drops.

**Published odds.** The PDF tabulates the resulting distribution per difficulty for regular monsters and bosses at
tiers 0-20. Examples at tier 20+: MAW regular 20/20/40/16.3/2.23/0.78/0.61% (Common..Legendary), "1 in 27 Ancient or
better, Celestial 1 in 2,400"; MAW boss "1 in 4 Ancient+, Celestial 1 in 310"; Beyond Madness boss 0/0/0/38.7/35.8/
13.2/11.4%. The PDF contains unrendered template placeholders (`{dip['Legendary']:.0%}`, `{affix_mult(30):.2f}`),
which means it is generated from the code by a script. For OpenYAMM this is a ready-made **golden test table** for a
unit test of the rarity roller. `GetRarityDistribution` (zzMaw-Items.lua:835) is the no-pity form; the PDF is the
pity long-run average and differs in the third digit ([RANDOMS.md](RANDOMS.md) §5.2).

### 1.5 Enchants

Item struct mapping: base enchant 1 = `Bonus`/`BonusStrength`; base enchant 2 = packed into `Charges` (§2);
special enchant = `Bonus2` (1-based index into SPCITEMS); legendary affix, tier, celestial, quality and drop level
are bitfields in `BonusExpireTime`.

`enchantCountByRarity`: Common 0, Uncommon 1, Rare 2, Epic and above 3 (2 base + 1 special). Uncommon gets enchant
1; Rare and above also get enchant 2; Epic and above get the special.

**Type** (`RollEnchantType`, zzMaw-Items.lua:880): uniform 1..10 (Might, Int, Pers, End, Acc, Speed, Luck, HP, SP,
AC). Rings roll 1..16 (adds the six resistances). 10% of first enchants become a skill enchant 17..24 (Alchemy,
Repair, Disarm, IdItem, IdMonster, Armsmaster, Dodge, Unarmed); Dodge (23) is swapped to 22 on Chain/Plate body
armour (skills 10/11) and Unarmed (24) to 22 on weapons of skills 1-7 (staves keep Unarmed). If enchant 1 is empty
but enchant 2 exists, enchant 2 moves into slot 1. Afterwards a resistance enchant 1 is re-rolled to 1..10 on
non-rings, and a resistance enchant 2 on every item, rings included, so rings only get a resistance as enchant 1.
Duplicates are re-rolled.

**Strength** (`rollEnchantStrength`, zzMaw-Items.lua:466):

```
encStrUp(tier) = 1 + 2*tier                    (tier <= 12)
               = 25 + min((tier-12)*3, 75)      (tier > 12; 100 at tier 37)
Austerity:      tier + 2 (tier<=30), 32 + (tier-30)*2
strength = encStrUp(lootTier) * diffPower * random(Min..Max)/20
   Common..Epic Min=8  Max=20  (40-100%)
   Legendary    16..20         (80-100%)
   Ancient      20..25         (100-125%)
   Primordial / Celestial 25   (125%)
diffPower = 1.2 insanity (Road to Insanity / Beyond Madness), 1.1 Doom, 1.05 true Nightmare, else 1
```

Post-processing: skill enchants `ceil(max(sqrt(x), x/10))` (Formulas.lua:21). Slot multiplier (`slotMult`,
zzMaw-Items.lua:1405) applied to both base enchants: 1H 1, 2H 2, bow 1.25, body armour 1.5, shield 1, helm 1.25
(×1.5 more for helms with no AC, i.e. hats/crowns, applied when stats are read, not at generation), belt 1, cloak 1,
gauntlets 1.25, boots 1.25, ring 0.75, amulet 1.
If the two enchant strengths differ by ≤1 they are synchronised.

Read-time transforms (not baked): HP/SP enchants `p * (1 + min(p/50/slotMult, 5))` (Formulas.lua:27);
resistance enchants: +10 on the first enchant only, rings count half (`p*100/200`), displayed as a reduction
percentage `1 − 1/(1+p/100)`. Skill enchants apply only from enchant 1.

**Special enchant** (zzMaw-Items.lua:1206-1223): pool chosen by grade:
`power = clamp(grade, 3, boss ? 6 : 5)`; pools are SPCITEMS `Lvl` groups: 3 → A+B, 4 → A+B+C, 5 → B+C+D,
6 → D only (only bosses with grade 6 reach the "strongest pool"). Weighted by `ChanceForSlot[equipStat]`.
Then: "of Ascension"(39)/"Lichs'"(40) vs "of The Dragon"(46)/"of Darkness"(41) are swapped to match whether the
base enchants are melee (Might/Acc) or caster (Int/Pers) oriented (zzMaw-Items.lua:1267-1295). Legendary affix 19
(+50% weapon enchant damage) avoids 40/41.

Special-enchant stat scaling: `bonusEffects[id].statModifier * min(1 + MaxCharges/25, 5)` (Formulas.chargesStatMult);
school enchants give `floor(MaxCharges/4)+5` skill; meditation enchants `floor(MaxCharges*3/20)+3`.
Damage specials (4-15, 39, 46) scale with **item-level weapon damage**, not a fixed range (`enchantDamageRange`,
zzMaw-Items.lua:2067: `avg = levelDamage * Coeff`, coefficient 0.2/0.3/0.4 for the three elemental grades, 0.25-0.45
body, 0.5 for 39/46; floor `{min,max} * 0.5` (×2 on 2H)). They are also multiplied by the weapon's base attack-speed
factor (§1.10), and README: main-hand damage enchants add to spell damage (40% for AoE/shotgun spells).

### 1.6 Item power / item level (`MaxCharges`)

`MaxCharges` (u8) is repurposed as **item bonus power**; item level = `MaxCharges * 5` (`ItemLevel.PerPower`).

```
PowerFor(level) = min(floor(level/5), 100)
rollTierCharges (zzMaw-Items.lua:512):
  Common..Epic       round(c * random(12..20)/20)          60-100%
  Legendary          round(c * random(16..20)/20)          80-100%
  Ancient            max(round(c * random(20..24)/20), c+2)   100-120%
  Primordial/Celest. max(round(c*1.2), c+4)                120%
  cap 255 (u8)
```

What MaxCharges drives:
- **Weapon damage** (`getWeaponDamageForLevel`, Modules/MawCore/Estimates.lua:120). With `power=PowerFor(itemLevel)`,
  `flatPower=floor(power/2)`: `diceOnly = 8*2 + 2*2*(power−flatPower)`, `flatOnly = tierFlat + 2*flatPower`,
  `tierFlat = 16*(ladderTier−1)/5`, halved for one-handed weapons. `GetWeaponDamageRows` splits that into
  Attack/flat and dice sides, × artifact base multiplier × cube quality. At game init every base weapon's dice sides
  and Mod2 are rewritten to this model (zzMaw-Items.lua:1410-1436); shields get `Mod2*2 + dice`. Weapon damage is
  capped at item power 100 (item level 500); armour AC is not.
- **Ladder tier**: each base family (same `NotIdentifiedName`) is mapped onto tiers 1..6 by position
  (`ItemLevel.LadderTier`, ItemLevel.lua:24-46); the best family member gets +16 flat (2H).
- **Armour AC**: `base AC + referenceAC(top sibling) * MaxCharges/40`, × quality (`collectArmorAC`,
  zzMaw-Items.lua:2692; legendary 28 ×1.5).
- **Special-enchant scaling**, value, and level requirement.

### 1.7 Level requirement (zzMaw-Items.lua:4351, ItemLevel.lua:66)

```
dropLevel = GetStoredDropLevel(it)  (bits 9-19 of BonusExpireTime)
            or reconstructed from MaxCharges (undo the rarity inflation) * 5
L   = dropLevel + (ladderTier−1)*3          [TierLevels: +0..15 by base-family rung]
req = min(L − (10 + 0.09*L), 0.8*dropLevel)  [ItemLevel.WearLevel, GUARD_MARGIN 10, WEAR_SHARE_CAP 0.8 (8967ae88)]
      −6 at bolster ≥300, −3 Doom, −3 insanity;  floor, min 1
Celestial: 1.   Non-equipment (EquipStat>11): 0.   Artifacts: none.
```

Enforced in `events.CanWearItem` (zzMaw-Items.lua:4130), which uses the *player's* `LevelBase`. In Doom,
unidentified items cannot be worn at all. Gems and the Pandora's Cube also require the level.

### 1.8 Celestial items (zzMaw-Items.lua:1622)

A Celestial is Primordial + legendary affix + "grows with you". On every stat refresh and tooltip build
(`updateCelestialItem`) its strengths are **recomputed from the wearer's level**:
`lvl = min(pl.LevelBase, 1.2*totalLevel)`, `tier = lvl/11 + 5` (madness: `min(lvl,500)/11+5`),
`strength = encStrUp(tier) * diffPower * 1.25 * slotMult` (skill enchants /10), `MaxCharges = GetPrimordialCharges(lvl)`.
No level requirement; gems and cubes refuse it (the tooltip says it scales to level 600, or 1000 in madness).

### 1.9 Attack speed on weapons (zzMAW-Skills.lua:425)

```
getItemRecovery = round10( baseRecovery[skill] * (0.75 + min(itemLevel,600)/500) ),  ×1.25 (round10) for 2H
baseRecovery: Dagger 60, Sword 80, Mace 100, Bow 100, Staff 120, Spear 120, Axe 140, Blaster 40
```

It is a **base recovery (delay) value**: the final attack delay is `baseSpeed * speedMultipliers`, and the melee/ranged
damage multiplier is `totalSpeed/speedBefore ≈ baseSpeed/100` (zzMAW-Skills.lua:598-608). So slow weapons hit
proportionally harder and DPS is neutral, but the recovery floor ("speed cap") becomes harder to reach as item level
pushes base recovery up to 1.95×. Dual wield averages both hands. The tooltip prints `Attack Speed: baseSpeed/100`
on the type line, rounded to tens of recovery (e.g. Axe at item level 0 = 1.1). Clubs (Skill 39) have no base
recovery and stay at 1.0. Elemental enchants and spells are not affected by it (README);
the code does multiply enchant damage by `GetPlayerBaseRecovery`, so enchants follow the same pace.

Artifacts "Swift" (515, 1302, 2024, 2025): attack delay × 0.9. Special 41/59 (Darkness/Swift): +0.3 swiftness
multiplier on 2H, +0.15 per 1H.

### 1.10 Value and gold (zzMaw-Items.lua:1897-2040)

```
bonus1 = BonusStrength*100;   HP/SP: 5*(sqrt(2s+100)-10)*100;   AC: *2;   skill(17-24): s^2*100
bonus2 = enc2Strength*100;    HP/SP: 5*(sqrt(2*bonus2+100)-10)   (note: no *100, and fed the already *100 value: bug)
mult   = MaxCharges/20
basePriceBonus = ItemsTxt.Value * mult
special: v = SPCITEMS.Value (* mult if the special scales);  v<11 -> basePriceBonus *= v (*2.5 more if v==10)
                                                            else basePriceBonus += v
value  = Value + basePriceBonus + bonus1 + bonus2;   legendary affix: *2.5
buy screens (HouseScreen 2/95): value ^ (1 + 0.08*count), count = #enchants + max(tier,2) for ancient/primordial
elsewhere (sell, loot filter): value * 0.4
round: >200k to 1000, >50k to 500, >1000 to 100, >100 to 10
```

Gold in chests (gold item ids 187-189 etc.) is rewritten once per map: `10 * (mapLevel + bolsterLevel) * {1,2,4} *
U(0.66..1.32)`. Merchant ≥ GM or >15 skill forces `House.Val=1` and `GetMerchantTotalSkill=100` (overflow fix).
Spell book prices are rewritten by tier, doubled again ×5/×10/×20 in insanity shops. Crafting-item base values:
gem tier i = i×1000; specials 15k-200k (zzMaw-Items.lua:2233-2243); misc-shop selling prices in `reagentPrices`
(gems 1,000→300,000; Eye 1.25M, Hourglass 750k, Pandora's Cube 325k, Mirror 6,668,999, Emerald 2M, Pearl 1M,
Oracle's Orb 3M, Crafting Cube 250k).

### 1.11 Shops

- Stock rolls through the same `ItemGenerated` with `dropLevel = 0.75*totalLevel`, no Legendary/Celestial/Primordial,
  rare shop Ancients (priced as tier 2).
- Shops with house ≤110 (weapon, armour and magic shops plus the first alchemist, 110; only the magic shops and that
  alchemist stock non-equipment): any stock item with EquipStat ≥12 (30%) or of the "Gem" class (EquipStat 19, MM8
  valuable gems such as Zircon 177; reagents are EquipStat 13) becomes a crafting material: with chance
  `min((PartyGold/20,000,000)^0.7, 1)` a special item weighted
  {Eye 7, Hourglass 7, Pandora 15, Mirror 2, Emerald 5, Pearl 7, Oracle 3, Crafting Cube 15}; otherwise a gem of tier
  `1 + floor(P/25)` (+1 at 25%, +2 at 5%), capped at 16, where P = `getPartyLevel(4)`, the banked levels of
  continents 1-3 (zzMaw-Items.lua:1035-1095). Richer parties see better stock.
- **R (key 82) in a buy screen rerolls the shop** (`refreshItems`, zzMaw-Items.lua:3922-3984). Cost
  `(GetTier(partyLevel) + strength)^2 * 250` gold, where `partyLevel = getPartyLevel(4) − min(MMLVL[world]/2, 54)` and
  `strength = min(floor(MMLVL[world]/18)+2, 5)`. Before each slot the strength is raised by 1 when
  `random(1,18) < MMLVL % 18` (probability ((MMLVL mod 18) − 1)/18), and once raised it stays raised for the
  remaining slots. Each slot is re-randomised with the shop's remembered item kinds (`vars.shopType`, rebuilt from
  current stock on `ShopItemsGenerated`; armour and shield slots use kinds {31,32,33,34,5} in any shop), set
  identified, icon pointer refreshed. The status
  text "Press R to refresh new items (20000 gold)" is stale (the price is dynamic and not shown).
- Doom: identify cost `IdRepSt^2`, repair House.Val 5.
- `MawCore/SpecialItems.lua`: shops always identify/repair quest/special items, buy them once their quest is done,
  sell-once uniques (with seer re-issue bits cleared), prices for 0-value items.

### 1.12 Anti-save-scum seeding (zzMaw-Items.lua:33-403, 987-996; zzAlchemy.lua:1118-1160)

- `vars.seed = os.time()` the first time it is needed; stored in the save.
- **Per-map monster seeds** (non-insanity): on first `LoadMap`, map seed = `vars.seed + Σ byte(name,i)*i*13 +
  MapStatsIndex*47`; the monster seeds are chained (each one is derived from the state left by monster i−1 plus
  i*97, advanced 50+(i%20) steps; [RANDOMS.md](RANDOMS.md) §3.2), stored in `mapvars.MonsterSeed[i]`. `PickCorpse`
  sets `Game.RandSeed` and `math.randomseed` from it, then stores the advanced engine seed back next tick. In
  Easy..Doom that post-kill write-back makes regular-corpse gold, drop chance and base id drift across reloads, and kill
  order matters everywhere through `SeedList`.
- **Insanity mode**: per *monster type* LCG (`a=1664525, c=1013904223, m=2^32`) in `vars.monsterSeeds[Id]`,
  advanced on kill, on loot and on Telepathy.
- **Bosses**: `vars.seed + mapHash(×31) + index*1337 + Id*2003 + mapvars.BossSeed[index]` (spawn counter).
- `CastTelepathy` does not preview the real drop: it generates the treasure at cast time under different rules (no
  loot context) and consumes a seed the corpse would have used ([RANDOMS.md](RANDOMS.md) §3.8).
- **Per-item-number sequence**: `vars.SeedList[0..2500] = i*1e9 + random`; every `ItemGenerated` reseeds
  `math.random` from the list entry for that base item id and replaces the entry. In shops and chests only MAW's roll
  on top is sequenced; the base items are unseeded.
- Crafting drops in `MonsterKilled` use the same seeds and LCG-advance once per special item.
- Crafting outcomes are seeded from the target item's own fields (§3.3).
- Nightmare and above (README): no saving or teleporting with monsters nearby; dungeons respawn if left early.

### 1.13 Data-table changes (Data/zMaw.T.lod vs base MMMerge `mmmerge.T.lod`)

The LOD is MMVIII format, zlib-compressed entries: `class.txt, ITEMS.txt, mapstats.txt, MONSTERS.txt, Placemon.txt,
POTION.TXT, POTNOTES.TXT, rnditems.txt, SPCITEMS.TXT`.
- **SPCITEMS.TXT**: Ogre Slaying → "of Ascension" (39: spell damage + Int/Pers), Dragon Slaying → "Lichs'" (40:
  spell leech + cast speed); seven new hybrid specials 74-80 (Paladins', WarriorMage', Shadows', Rangers',
  Elementals', Selfs', Divines'); slot chances zeroed for Elemental and Undead Slaying (63, 64) and Assassins' and
  Barbarians' (67, 68) on weapons, Storm and Ocean (69, 70) on armour, shield and helm, Shielding (36) on rings and
  amulets; several `Lvl` grades re-assigned (Protection B→D, now on all slots, Ogre/Dragon Slaying 39/40 A→D, Doom
  B→C, Life D→C, Eclipse D→C, Freedom/Medusa D→C, Troll/Unicorn C→D, Shielding B→D). Full diff:
  [ITEMS_DATA.md](ITEMS_DATA.md) §3.5.
  In-code text overrides follow at `GameInitialized2` (immunity specials now give two immunities each, see
  `protectionMessages` zzMaw-Items.lua:1458).
- **ITEMS.txt**: 202 rows changed. Leather/chain body-armour dice rebalanced (leather 8, chain 12), belts gain AC
  (1 dice + 0..11), potions renamed/repurposed (224-263), item 290 becomes "Map" (dimension maps), crafting items
  1051-1067 get pictures/sprites (names are overridden again in Lua, zzAlchemy.lua:1297-1343), Power Stones 1022/1023,
  some artifact dice raised (Ghoulsbane, Gibbet, Charele, Justice, Mordred, Titan's/Hero's Belt), 1372 DeathBlade
  removed.
- **rnditems.txt**: removed potions (264-289) and recipe scrolls 700-731 and 751-769 (732-750 untouched) from
  treasure tables, black potions pushed to higher treasure levels, Focal Ring nerfed. Full diff:
  [ITEMS_DATA.md](ITEMS_DATA.md) §3.4.
- `Data/Tables/Potion settings.txt`: potion ids 71-90 → items 1041-1060 (gems), 91-98 → 1061-1068, all "Usable"
  (i.e. applied by right-clicking the potion onto an item); rows 99-102 are malformed duplicates.
- `Complex item pictures.txt`: identical to base MMMerge. `ObjList.txt`: only non-item changes (45 new spell or
  projectile object descriptors 700-743 plus "Snow" 12013).
- Icons: `zVex.icons.lod` holds crafting icons `vCraft1..13`, `vCraft1Asc..10Asc`, `vEye1`, `vHour1`, `vMirror`,
  `vEternal1/2`, `vCelest1`, spellbook skins `sb*`; `zMaw.icons.lod` holds 2H mace art; `zMaw.games.lod` holds maps.

### 1.14 Loot filter (zzMaw-Items.lua:930-970, 1345-1364; settings zz_Maw-initialize.lua:569)

MAW settings switch "Loot Filter": OFF / Common / Uncom. / Rare / Epic / Ancient / Primordial. A monster drop at or
below the threshold is deleted and its 0.4× value added as gold ("You found N gold! (Rare Longsword filtered)").
Chest items at or below the threshold are converted into gold-pile items once per map (`mapvars.lootFiltered`).
`itemPower` order: 1 common, +1 per enchant, ancient 5, primordial 6, legendary 7, celestial 8.

### 1.15 Other loot hooks

- Fixed artifacts in chests with Value ≥ 20000 are re-rolled as boss loot at strength 6 (`it:Randomize(6,0)`,
  zzMaw-Items.lua:4523). The protective `mawArtifactsKeep` list is entirely commented out, so all such chest
  artifacts, quest rewards included, are replaced. This looks unintended.
- Potions 264-289 on the ground or in chests become a random 252-263.
- `isRedone`: base items with MaxCharges 0 in chests or on the ground are randomised at `lootLevel = clamp(mapLevel/20+1,
  2, 6)`.
- Doom start: starting enchantable items get MaxCharges 2 (4 in insanity).
- Reagents get `Bonus = round(min(dropLevel,totalLevel)/3)` (/8 austerity), alchemy-GM monster reagent drops, Endless
  Potion drops (§3).
- K (75, configurable `teleportDeadMonstersAndCraftingKey`): pulls up to 30 corpses and 30 crafting items or maps on
  the map to the party (zzMaw-Monsters.lua:4432). This is a loot-pickup QoL feature.

---------------------------------------------------------------------------------------------------------------------

## 2. Per-item data storage (Modules/MawCore/ItemFields.lua, General/zMaw_ItemBits.lua)

MAW keeps the 0x24-byte MM8 item struct and packs everything into existing fields:

| offset | field | MAW meaning |
|---|---|---|
| 0x00 | Number | item id |
| 0x04 | Bonus | base enchant 1 type (1-24) |
| 0x08 | BonusStrength | base enchant 1 strength. Also the payload of crafting items (Oracle's Orb affix id, Celestial Orb charged flag, Endless Potion charges, gem "ascended" flag) |
| 0x0C | Bonus2 | special enchant (1-based SPCITEMS index, up to 80); gold amount on gold items |
| 0x10 | Charges (i4) | **enchant 2 bitfield**: bit 22 marker `0x400000`, bits 16-21 type (0-63), bits 0-15 strength (0-65535); bits 23-30 free. Also potion charge counters (remaining uses + 1; 0 = fresh = 5 uses), map-affix pairs (`affix*1000+affix`), MP sync ids (not routed through the accessors) |
| 0x14 | Condition | vanilla flags (identified, broken, hardened, ...); bits 11-30 free, "earmarked by the gem-sockets design" (a planned socket feature) |
| 0x18 | BodyLocation | equip slot |
| 0x19 | MaxCharges (u8) | **item bonus power** (item level = ×5), cap 255 |
| 0x1A | Owner | untouched |
| 0x1C | BonusExpireTime (i8) | **rarity bitfield** (new layout): bit 30 marker `0x40000000`; bits 0-5 legendary affix (1-25, stored as id−10); bits 6-7 tier (1 Ancient, 2 Primordial); bit 8 celestial; bits 9-19 drop level (0-2047); bits 20-24 cube quality (0-20 %). Without a marker the same field holds the artifact level (1-1000), a map-affix id on map items, or the vanilla temp-enchant expiry. Legacy values (1/2 tier, 11-35 affix, +100 celestial) are still decoded |

Notes for a clean engine:
- **Rarity is not stored**; it is derived (`MawItemRarity`, zzMaw-Items.lua:691): celestial > legendary affix >
  tier > enchant count.
- Bags (multibag) and sorting copy items into Lua tables field by field, which drops the padding byte and
  round-trips integers through Lua doubles (hazard 2 in ItemFields.lua). Corrupted NaN bags are detected at save time
  (zzMaw-Item-Sorter.lua:698) and block saving.
- Side state in `vars` (save-global): `seed`, `SeedList`, `enchantSeedList`, `monsterSeeds/Counters`, pity counters
  (`primordial/legendary/celestialPityCounter`, `artifactRollPity`, `artPity[]`, `craftPityCounters[]`,
  `legendaryAffixDropped[]`), `mawbags[rosterIndex][bag] = {items...}` (CurrentBag = tab*100+bag), `CraftingBags`,
  `alchemyPlayer`, `shopType`, `MAWSETTINGS.{lootFilter,extraItemTooltip}`, `RandomizerMode/Randomizer/
  OriginalItemOrder/ItemFound`, `legendaries[]` (derived, rebuilt on refresh). Per-map: `MonsterSeed[]`, `BossSeed[]`,
  `chestGoldFix`, `lootFiltered`.

**OpenYAMM mapping.** `InventoryItem` (`game/party/Party.h:45`) has one standard enchant id/power, one special, an
`artifactId`, an `ItemRarity` enum (the table's Common/Artifact/Relic/Special, which is a different concept), and
`current/maxCharges`. A MAW ruleset needs explicit fields, not bit packing:

```cpp
struct ItemAffixRoll { uint16_t typeId; uint32_t power; };       // "base enchant"
// in InventoryItem (or a std::optional<RulesetItemData> to keep vanilla saves lean):
std::array<ItemAffixRoll, 2> baseEnchants;  // MAW: 2; vanilla: 1
uint16_t specialEnchantId;
uint8_t  lootRarity;        // Common..Celestial, stored, not derived
uint8_t  legendaryAffixId;  // 0 = none
uint16_t itemPower;         // MAW "MaxCharges", do NOT reuse maxCharges (wands/potions need it)
uint16_t dropLevel;
uint8_t  qualityPercent;    // Pandora's Cube
uint32_t craftSeed;         // see §3.3 / §8
std::vector<uint16_t> sockets;  // optional: the "gem sockets" MAW already earmarked
```

Store the rarity explicitly, because it is a rule-relevant fact and deriving it from enchant counts breaks when the
Pearl of Memory removes an enchant. Keep the vanilla `ItemRarity` (artifact/relic) separate. Version the save
section per ruleset.

---------------------------------------------------------------------------------------------------------------------

## 3. Crafting

### 3.1 Mechanics of use

All crafting items are "usable potions" (`Potion settings.txt` 71-98): pick the item up and **right-click it onto
the target item** → `evt.PotionEffects[id](IsDrunk, target, Power)`; `Mouse.Item` is the consumable. Crafting Cube
(1070), Endless Potion (1069) and the map-crafting uses go through `UseItem(it, usedIt)` (zzAlchemy.lua:1037), which
is called from the **tooltip builder** (`Tooltip.lua:191`, section "alchemy-craft-with-held-item"). Right-clicking an
item while holding one of these builds its info box, and building the box performs the action. A 60-frame cooldown
(`craftWaitTime`) is set only by the Oracle and Celestial orbs, which are potion-path items: it protects orb
extraction, not repeated tooltip builds. The Crafting Cube, Endless Potion and map uses have no cooldown (they are
consumed).
`ShowCraftedItemEffect` plays a glow on the item and sound 12070.

### 3.2 The items (ids, current names from zzAlchemy.lua:1252-1343)

| id | name (code) | potion id | effect (exact) | gates |
|---|---|---|---|---|
| 1041-1060 | 10 gems × normal/"Ascended": Lunar Shard, Fire Topaz, Amethyst Chunk, Amber Droplet, Royal Amethyst, Gemcutter's Ruby, Solarstone, Erudite Crystal, Erathian Sapphire, Queen's Diamond (+ Ascended …) = **gem tiers 1-20** | 71-90 | `upgradeGem` (zzAlchemy.lua:726): picks whichever base enchant is lower **as a fraction of its own cap**; +3 (+1 for skill enchants); cap `GetGemCap(tier) = ceil(round(tier/20 * PrimordialMax) * slotMult)`, PrimordialMax = `round(ceil(100*diffPower)*25/20)` = 125 at normal (131/139/150 at Nightmare/Doom/Insanity; Doom's floating-point `ceil(100*1.1)` is 111); skill cap `ceil(max(sqrt,/10))`. Fails with "Gem power is not enough" when both are at cap | base item, level requirement met by the current character, not Celestial, needs ≥1 base enchant |
| 1061 | Eye of Void | 91 | add a **special enchant** from the strongest pool (power 6 = grade D) | `Bonus2 == 0` only. The note says it needs 2 base enchants, but the code does not check |
| 1062 | Creator's Hourglass | 92 | add **base enchant 2**: type `RollEnchantType(excl. enchant 1)`; strength `min(round(BonusStrength*(1+0.25*rand)), 100*max((bolster-100)/1000+1,1)*slotMult)` | enchant 1 present, enchant 2 absent. The note says it also needs a special; the code does not |
| 1063 | Pandora's Cube | 93 | **quality** +step % on the base stat (weapon damage rows or armour AC), cap 20%. Step: Common/Uncommon 20, Rare 10, Epic 7, Ancient 5, Primordial/Legendary 4, Celestial 1, artifacts 2 | weapons, armour, shields, helms, belts, cloaks, gauntlets, boots, rings and amulets (the last two wastefully), level requirement; base items and artifacts |
| 1064 | Archibald's Mirror | 94 | **duplicate**: the mirror on the cursor becomes a copy of the target (Number, enchants, charges, MaxCharges, BonusExpireTime; Condition is not copied, so the copy is unidentified) | base items **and artifacts** (README says artifacts are excluded; the code allows them) |
| 1065 | Emerald of Power | 95 | **upgrade base type**: next sibling in the same family (`Number+1` with the same unidentified name), else the weakest stronger base item of the same skill and slot | base item; also exits the house screen (bug-ish) |
| 1066 | Pearl of Memory | 96 | **remove one random enchant** (enchant 1 / 2 / special, uniform over the present ones; if enchant 1 is removed, enchant 2 is promoted) | not seeded, so not predetermined |
| 1067 | Oracle's Orb (item name "Orb of Creation"; only its texts say "Oracle's Orb") | 97 | empty orb on a legendary item: **extracts** the affix into the orb's BonusStrength and strips it from the item. Charged orb: **imprints** the affix on any base item (celestial status kept) | base item |
| 1068 | Celestial Orb | 98 | empty: strips celestial from an item and charges the orb (BonusStrength=1); charged: makes a non-celestial base item celestial | base item |
| 1069 | Endless Potion | via UseItem | +BonusStrength charges to charge potions {231,232,233,237,245,251,257,263} (`Charges` 0 counts as 6) | drops only when any party member is a GM alchemist: 0.2%/kill, `BonusStrength = min(best Alchemy skill + 10, 100)` |
| 1070 | Crafting Cube | via UseItem | **item power** `MaxCharges += 4` (+2 on 1H/2H/bow/body armour) up to `min(floor(playerLevel/5), 120)` (120 = best Primordial roll) | base item, not Celestial |

Map items (290, dimension maps): Eye/Hourglass unlock an affix (`Bonus` 1→4), only on maps with 1-3 active
affixes; Emerald +5 map **power** (MaxCharges), i.e. +50 monster levels; Crafting Cube moves the map to another
completed dungeon of the same kind (seeded by the map's own fields).

**U key (85) in the inventory**: merges 3 gems of tier n (with `BonusStrength==0`) from the party's loaded backpacks
into one gem of tier n+1, one triple per confirmation, lowest eligible tier first, result on the cursor. The first
press shows "Convert X into Y? (U)" and the second press confirms (zzMaw-Items.lua:4207). Full spec:
[CRAFTING.md](CRAFTING.md) §3.4. Gems drop only up to tier 16 (`GEM_DROP_MAX_TIER`); tiers 17-20 exist only through U.

### 3.3 Predetermined outcomes and the ALT preview

- Eye and Hourglass seed `math.randomseed(Number*10000 + MaxCharges*1000 + Bonus*100 + BonusStrength*10 + Charges)`
  (zzAlchemy.lua:805, 830). The tooltip with ALT runs the same seeded roll and prints the would-be result in grey
  (Tooltip.lua:298-331 for Hourglass, 434-464 for Eye; the comments say "must stay identical"). Applying a gem or
  cube changes BonusStrength/MaxCharges, so the predicted outcome changes. That is the documented "if you use any
  crafting item the outcome will change". Reloading does not change it. The seed contains no save seed, so the
  result is the same in every save.
- The Hourglass preview recomputes strength with slightly different HP/SP handling than the apply path, so the
  preview can differ from the result for HP/SP enchants (a latent bug; share one function).
- Enchant Item potion (238): seed `vars.enchantSeedList[itemId] + MaxCharges`; ALT shows "<Stat> +X" on blank items.
- Pearl, Mirror, Emerald and the orbs are deterministic by construction or simply unseeded. The Lesser and Greater
  Element potions (§3.4) are unseeded too.

### 3.4 Potion-based crafting (Global/zzMAWPotions.lua)

Right-click a potion onto an item (power = potion `Bonus`):
- **Enchant Item (238, pot 18)**: blank base item → base enchant 1. Type as in loot (10% skill, rings 1-16); strength
  `min(power,500)/5 × slotMult`, skill enchants `max(sqrt, /10)`.
- **Lesser Element (243, pot 23)**, power ≥40, weapon without a special → special 5/8/11/14 (Frost, Lightning, Flame,
  Venom).
- **Greater Element (255, pot 35)**, power ≥55 → 6/9/12/15 (Ice, Thunderbolts, Infernos, Acid).
- **Swiftness (244, pot 24)**, power ≥40 → special 59 "Swift".
- **Darkness (256, pot 36)**, power ≥100 → special 41 "of Darkness" (vampiric + speed).
- Harden Item (pot 16) is disabled ("not working").

### 3.5 Drop rates (zzAlchemy.lua:1091-1238)

Per kill (not reanimated, not `NameId>300`; disabled on madness bounty or arena maps):

```
bonusRoll = sqrt(level/10) * extraRoll           (0 in Austerity; / players in multiplayer)
extraRoll = 10 boss (220 <= NameId < 300), 1/(5-variantTier) broodling, 3 for "no corpse" monsters,
            (1 + (mapPower*nAff + 20*nAff)/800*1.5) on dimension maps
gem:    P = 0.006 * bonusRoll * (1.5 insanity), no pity;   tier = floor(N(max(lvl^0.6/4+1, lvl/40), sd 2)), clamp 1..16
special i: P = pity_chance(base_i, counter_i) * bonusRoll, counter += round(bonusRoll) on failure
   Eye 0.0002, Hourglass 0.0002, Pandora 0.001, Mirror 0.00001, Emerald 0.00025, Pearl 0.0002,
   Oracle's Orb 0.00006, Celestial Orb 0.0000025, Crafting Cube 0.001
```

The boss range here differs from the loot code's (221-300 or 160). Because counters grow by `round(bonusRoll)`, regular
monsters below level 2.5 (bonusRoll < 0.5) never accumulate pity. Special drops reseed `math.random` from an LCG step of
`Game.RandSeed` per item. Full spec: [CRAFTING.md](CRAFTING.md) §6.1.

Items from water monsters go straight to the inventory (`evt.Add`), others spawn on the ground (`SummonItem`).
Reagent drops (alchemy Master/GM, 1%/2%) and their potion conversion are alchemy scope.

### 3.6 Shop availability: see §1.11 (misc shops, gold-scaled special-item chance).

---------------------------------------------------------------------------------------------------------------------

## 4. Artifacts, legendaries, randomizer

### 4.1 Artifact drops (zzMaw-Items.lua:1006-1033)

Any non-shop enchantable drop has `pity_chance(0.005, vars.artifactRollPity)` to become an artifact from
`mawArtifacts` (104 entries, 103 distinct ids across the three games: 533 appears twice, so it has double weight,
and 532 is absent; 98 is the number of `artifactPower` budgets). The pick uses `get_affix(vars.artPity)`, which
weights by `1/(N*(count+1))`, so artifacts found less often are favoured. Enchants are cleared, and
`BonusExpireTime` is set to the party total level (1..1000); that stored level is never read (§4.2).

### 4.2 Artifact power (Modules/MawCore/Artifacts.lua; data `artifactPower` zzMaw-Items.lua:3506-3835)

- An artifact's **level = party total level** (`ItemLevel.OfItem` returns `getTotalLevel()` for artifacts), so it
  scales with the party forever. The tooltip shows "Artifact Level: N".
- Stats are a **budget**: one coefficient unit = one perfect Epic enchant of that slot and level,
  `encStrUp(GetLootTier(level)) * diffPower * slotMult`; whole artifact ≈ 3 units (`Artifacts.Slots`). Skills use
  `skillEnchantPower(unit) * slotMult`. Resistances and HP/SP go through the same read transforms as enchants. `Flat`
  is for numbers outside the budget, `baseStatMultiplier` deviates base damage or AC from "a top-tier weapon at that
  level". 98 entries, with drawbacks allowed (negative coefficients).
- Base weapon damage ignores the printed dice: an artifact is a tier-6 weapon of its family at item level =
  party level, × multiplier. Legacy `artifactPowerMult` (dead) and the init-time dice doubling/tripling
  (zzMaw-Items.lua:2330-2346) still exist; the doubled dice still feed the weapon-skill AC and resistance bonus.
  The level written into a dropped artifact is never read. "Vampiric" artifacts do nothing (their flag feeds
  only unused tables). Details: [data/artifacts.yml](data/artifacts.yml).
- `General/zzzMaw_Artifacts.lua` holds the behaviour tables: `artifactOnHit` (DamageKind, Damage coefficient ×
  "of the Dragon" enchant curve, MultVs per monster kind, Vampiric, OnHit spell casts), applied as a damage-pipeline
  stage; `artifactDrain` (Ethric's Staff −3 HP/tick except Liches), `artifactLeech` (Hades −10%), Cycle of Life (543)
  HP sharing, `artifactWearReq` (race/class/sex gates, Wetsuit slot rules), `artifactBuffs` (permanent Shield,
  Stoneskin, Bless, Water Breathing, Preservation; Horn of Ros grants Detect Life while carried), `artifactImmunities`,
  `artifactAttackSpeed`, regen tables `artifactHpRegen/SpRegen`, `artifactSpellBonus` (+50% of the base school skill).
  `Global/ExtraArtifacts.lua` ships empty to override the MMMerge version.
- `ancientWeapons` (blasters) are artifacts that sit inside the base id bands.

### 4.3 Legendary affixes (25; `legendaryEffects` zzMaw-Items.lua:1572-1601; effects scattered,
some in Global/zzMaw_Legendaries.lua)

Rolled by `get_affix(vars.legendaryAffixDropped)` (affixes found less often are favoured), stored as id 11-35. Active
only while equipped (`vars.legendaries[rosterIndex]`, rebuilt in `itemStats`). Effects: 11 kill → halve recovery; 12
Might/Acc ↔ Int/Pers 40% echo; 13 status immunity (blocks conditions from any source); 14 +10% crit, overcrit → damage;
15 cheat death (25% HP, 5 min CD); 16 +50% resistance enchants; 17 2% current HP hit (1% AoE and arrows); 18 −10% damage
taken; 19 +50% weapon enchant damage; 20 meditation scales with reserved mana; 21 +5% damage per nearby enemy
(multiplies every damage in its stage, not only melee; tooltip shows the live value); 22 damage taken ×0.97 per nearby
enemy, multiplicative, floored at 0.5 (live); 23 cover heals 3%; 24 kill restores HP/SP; 25 +10 Ascension; 26 enchants
can crit; 27 overheal leech to most injured; 28 armour AC ×2 (code: ×1.5); 29 stacking +1% damage taken; 30 death
threshold from SP×shield efficiency; 31 leech restores mana (halved); 32 buffs reserve HP instead of mana; 33 +10 melee
weapon skill; 34 overheal refunds mana; 35 overheal reduces recovery.

### 4.4 Randomizer (zzzzMalekith-Randomizer.lua)

Toggle on party creation ("Randomizer" tumbler at 485,55 on screen 21) → `vars.RandomizerMode`. It shuffles a fixed
list of ~100 **quest/key-like unique items** (MM8 32, MM7 40, MM6 29 ids, offset per game; keys are listed but not
used) with `os.time()` (not save-seeded). On map load, chest and ground instances are swapped to their shuffled
counterpart once (`vars.ItemFound` records the new id for chests and ground items but the original id for grants);
quest/NPC grants (Actions 404/14) are swapped in the inventory. The second half
of the file shuffles monster types across maps (out of item scope).

---------------------------------------------------------------------------------------------------------------------

## 5. Inventory tools

### 5.1 Item sorter (zzMaw-Item-Sorter.lua; keys from zz_Maw-initialize.lua:28-32, user-editable `MAWSettings.lua`)

Only on the inventory page (`CurrentScreen 7`, `CurrentCharScreen 103`):
- **R (82)** sort the current character's backpack. Items are lifted into a Lua list, sorted by height desc (a 1-high
  item wider than 1 counts as 1.5), then skill, then item id, and re-added with `evt.Add` (engine auto-placement).
- **T (84)** sort all party backpacks as one pool (items are re-added to the current player, with overflow to the
  others).
- **E (69)** toggle the "alchemy player": while set, potions (220-299), reagents and crafting items go first in
  `alchemyItemsOrder` and are routed to that character.
- **C (67)** sort all 5 (or 25 when solo) bags of the current character (`sortMultibag`), filling bag 1, then 2, ...
- **G (71)** sort all bags of the whole party (`gigaChadSort`; solo = C).
- Potion bottle height is 1 or 2 depending on `vars.SmallerPotionBottles`.
- Save guard: `CanSaveGame` scans `vars.mawbags` for NaN corruption, blocks a manual save, and warns on autosave.

### 5.2 Multibag (zzMaw-MultiBag.lua)

- Every character has **5 bags** (a "bag" is a whole 14×9 backpack grid). Solo characters also get **5 tabs**
  (`CurrentBag = tab*100 + bag`), so 25 grids. The README's "store up to 5 items" is a typo for 5 inventories.
- UI: five bag buttons `SlChar1..5U/D` at X = 455+i*30 (485..605), Y = 372; five tab buttons at Y = 445 (solo only);
  visible on screens 7, 13, 15 and the Adventurer's Inn character view (29). The active one is drawn pressed.
  Buttons are hidden while an item tooltip is open (Tooltip section "multibag-buttons") and during Arcomage.
- Keys: solo **1-5** switch bag (1 is blocked while holding an item), **Shift+1-5** switch tab; party **Shift+1-5**
  switch bag.
- Implementation: on switch, the visible grid is serialised into `vars.mawbags[roster][bag]` (item fields and grid
  location) and the target bag is rebuilt into the item records. A held item is handed through a
  `DoGameAction(110)` round trip. This is fragile (the corruption guard exists for a reason).

### 5.3 Crafting bag (zzzMaw_CraftingBag.lua)

**Shift+B** in the inventory flags or unflags the current bag as a crafting bag (a yellow "C" marker is drawn on the
bag button). Picking up a crafting item (1041-1070) from the ground while the active bag is not flagged sends it
into the first flagged bag with room: the picker's own bags first, then other party members'. The message is "You
found an item (X)! -- <owner>". Placement is first-fit on a 14×9 grid.

---------------------------------------------------------------------------------------------------------------------

## 6. Tooltip changes (Modules/MawCore/Tooltip.lua — one `BuildItemInformationBox`, 13 ordered sections)

`extraDescription` = ALT held XOR setting "Extra Item Tooltip = ON" (zzMaw-Items.lua:1663-1679).

Equipment (section 200 "items-enchant-stats"):
- **Name**: special-enchant name added as a prefix (if it is capitalised) or a suffix, else the base enchant
  suffix. Colour by rarity: white common, green (30,255,0) 1 enchant, blue (0,150,255) 2, purple (163,53,238) 3,
  orange "Ancient …", red "Primordial …", yellow "Legendary …", cyan (120,240,255) "Celestial …".
- **Basic stat line** replaced: weapons `Attack: +B  Damage: lo-hi` from the actual damage rows (so the shown number
  is the dealt number); armour `Armor: +N` with item-power AC. Orange suffix `Quality bonus: +N%` when cubed.
- **Enchantment lines**: coloured stat name and `+N` per base enchant (enchant 2 above enchant 1); HP/SP shown
  post-amplification, resistances as a %, hats ×1.5. The enchant-2 resistance line shows a +10 that the stats do
  not get (only enchant 1 gets it). ALT on a 1-enchant item: the grey would-be Hourglass enchant.
  ALT on a blank item: grey `<Stat> +X` (the Enchant Item potion preview).
- **Description**: the yellow legendary affix text (with live numbers for affixes 21/22, the nearby-enemy count
  within 512 units) replaces the flavour text. The special-enchant text is recomputed with scaled numbers
  (`checktext`: actual damage ranges, stat values × chargesStatMult, school/meditation bonus). ALT on items without a
  special: the grey would-be Eye special. Hint "Press alt to show craftable stats". ALT: grey
  `Item Bonus Power: X/255`.
- Section 230 **Power/Vitality compare**: temporarily swaps the hovered item into the current character's
  corresponding slot (`slotMap`: rings compare to one fixed ring slot, 1H to the main hand), recomputes stats twice,
  runs `calcPowerVitality`, and prints `Power: +x%` (green or red, max of melee/ranged/spell DPS) and
  `Vitality: ±y%`, then restores everything (HP/SP pools too). Nothing is shown if the slot is empty or the item does
  not change Power/Vitality.
- Section 240: `Level Required: N` (red if too high); Celestial explanation line; `Attack Speed: X.XX` appended to the
  type line.
- Section 250: Fire Aura / Vampiric Aura lines on weapons when those buffs are active (buff rework).
- Artifacts (210/220): "(Special Powers…)" stripped and regenerated: one line per stat and skill bonus (red for
  negatives), orange on-hit effect lines, cyan `Artifact Level: N`, item-level Attack/Damage/Armor, Attack Speed.
- Crafting (120): gem tooltip with Tier, Max Power, Bonus 3 (1 on skills), skill cap, per-slot caps (2H, body, helm/
  boots/gloves/bow, rings) and U-key and drop-tier text. Oracle's Orb shows the stored affix, Celestial Orb shows
  its charged state, Endless Potion shows "Increases Charges by N".
- Potions (100): power-based heal amounts, `Charges: N`, ALT recipe list ("Press alt to show recipe list"); reagents
  show "Power: N" (110).
- Maps (300), skill books (320): out of item scope.
- Name, enchantment and description are built in separate passes of the engine's info box; the compare section
  mutates live equipped items to measure (a hack the engine has to support).

---------------------------------------------------------------------------------------------------------------------

## 7. Keyboard shortcuts and UI elements in this area

| key (default, configurable in `MAWSettings.lua`) | context | action |
|---|---|---|
| R 82 `currentBagSortKey` | inventory page | sort current backpack |
| T 84 `partyBagSortKey` | inventory page | sort all party backpacks |
| E 69 `AlchemyBagKey` | inventory page | toggle the alchemy-items recipient |
| C 67 `multiBagSortKey` | inventory page | sort all bags of the current character |
| G 71 `partyMultyBagSortKey` | inventory page | sort all party bags |
| U 85 (hard-coded) | inventory page | gem 3→1 upgrade (press twice) |
| Shift+B (hard-coded) | inventory page | toggle crafting bag |
| 1-5 / Shift+1-5 | inventory, chests (13), 15, inn | switch bag / tab (solo vs party semantics, §5.2) |
| R 82 (hard-coded) | shop buy screens | reroll shop stock for gold |
| ALT (hold) | any tooltip | extra item info (inverted by the setting) |
| K 75 `teleportDeadMonstersAndCraftingKey` | world | pull corpses and crafting items to the party |
| G 71 / V 86 `health/manaPotionKey` | world, solo | drink the strongest red/blue potion (15 s CD); same default G as party sort, different screen |
| right-click a held crafting item onto an item | inventory | craft |

UI elements: 10 multibag buttons and the crafting-bag "C" markers; settings page switches "Loot Filter" and "Extra
Item Tooltip" (screen `BolsterFineTuning`, Y 340/380); Randomizer tumbler on party creation; status-bar messages
(sort results, loot filter gold, "Press R to refresh…", crafting errors); a save-blocking corrupted-bag dialog; all
tooltip lines in §6; item glow + sound on craft.

---------------------------------------------------------------------------------------------------------------------

## 8. Mapping onto OpenYAMM and cheap high-value improvements

General principle: implement MAW as a **ruleset module** selected at new game (`ruleset: maw` in the save header)
that owns (a) a data file (YAML/TXT) of every constant above and (b) a small number of C++ policy hooks:
`rollLoot(context)`, `itemStats(item)`, `itemValue(item, context)`, `levelRequirement(item, character)`,
`applyCraft(consumable, target)`, `previewCraft(...)`. Vanilla MMMerge is the default implementation of the same
interface. Nearly all MAW item logic is formulas over tables, so it is a good fit for data plus about 5 functions.

| feature | data-driven vs code | notes and improvements |
|---|---|---|
| Rarity tiers, band thresholds, difficulty band multipliers, upgrade chances, boss divisor/mult, pity exponent | **data** (tables in §1.4) | One `RarityRoller` with unit tests reproducing the PDF tables (`GetRarityDistribution` is closed-form). Keep the pity counters in the save's ruleset block |
| Loot tier, encStrUp, strength ranges, slot multipliers, charges rolls, item-level → damage/AC | **data + one formula module** | Express curves as piecewise-linear tables (`encStrUp` is one already) so modders can tune them without code |
| Enchant types, skill-enchant 10%, resist only on rings, dedup, melee/caster special swap | data (weights per slot) plus small code | Replace "roll then re-roll" with weighted tables per slot |
| Special-enchant pools by grade | **already data** (SPCITEMS `Lvl` + `ChanceForSlot`) | Ship MAW's SPCITEMS as a ruleset overlay of the engine table |
| Seeding | engine service | Provide a deterministic `LootRng` keyed by (saveSeed, mapId, actorId or chest id, roll counter) instead of mutating the global RNG. This gives MAW's anti-scum for free and makes headless scenario tests reproducible. Per-item crafting seed = hash(saveSeed, itemUid, craftCounter), stored on the item (`craftSeed`), so previews never depend on fragile field arithmetic |
| Shop reroll | code (house service) + data cost formula | Add a visible **"Reroll stock (N gold)" button** in the shop UI with the real price, instead of a hidden R key and a stale "20000" message |
| Loot filter | engine setting + data thresholds | Do it properly: filter by rarity **and** slot/type, show a pickup log ("Filtered: Rare Longsword → 312 g"), and offer "auto-sell filtered" vs "leave on ground highlighted". Treat filtered loot as gold at pickup, not by deleting the item at generation |
| Level requirement | data formula | Show it in the tooltip with "(you: 37)" and grey out unusable items in the shop grid |
| Celestial "scales with you" | code (stat recompute on read) | Compute on read from the wearer's level, never write back to the item (MAW mutates the item on every tooltip) |
| Attack speed | data (`baseRecovery`, item-level slope) | Print it honestly as "Attack interval ×1.30, damage ×1.30" or as DPS, not a bare "1.30" |
| Value | data formula | Fix the bonus2 HP/SP price bug; separate buy/sell multipliers as data |
| Artifacts budget | **already data-shaped** (`artifactPower`, `artifactOnHit`, wear reqs, buffs, immunities) | Move to `engine/.../artifacts_maw.yml`; on-hit as a damage-pipeline stage. Note the `mawArtifactsKeep` bug (quest artifacts in chests get deleted); make it an explicit allow-list in data |
| Legendary affixes | data list + code effects | Each affix is a hook id on shared combat/stat systems; keep the "least-found-first" pick |
| Crafting consumables | data (consumable → operation + params) + ~10 operations in code | Operations: `raiseWeakestEnchant(step, capByTier)`, `addSpecial(pool)`, `addSecondEnchant`, `addQuality(stepByRarity)`, `addItemPower(step, capByLevel)`, `duplicate`, `upgradeBase`, `removeRandomEnchant`, `extract/imprintAffix`, `extract/imprintCelestial`, `addCharges`, `mergeGems(3→1)` |
| Multibag / crafting bag / sorter | **engine UI**, not ruleset | Implement as real containers, not grid swapping (§8.1) |

### 8.1 Concrete cheap, high-value improvements (not limited by the vanilla UI)

1. **Crafting / socketing panel instead of item-on-item right-clicks.** Two slots ("Item", "Reagent") plus a result
   preview, an Apply button and a reagent picker listing owned crafting items with counts. The preview is the same
   deterministic function the apply path uses, with no ALT and no tooltip side effects. This removes the
   "tooltip-performs-the-craft" hack, the 60-frame cooldown and the preview/apply drift. Gem merge (U) becomes a
   "Combine 3 → 1" button in the same panel, showing how many upgrades are possible. MAW already earmarked gem
   sockets (`Condition` bits 11-30). If a later MAW version adds sockets, the panel absorbs them.
2. **Comparison tooltips done right**: side-by-side "Equipped vs Hovered" with per-stat deltas (green/red) for the
   whole stat sheet (Might, AC, resistances, HP, DPS, Vitality), comparing against **both** rings or both hands and
   picking the better swap. Compute on a copied character snapshot (never mutate the live item as MAW does). A cached
   `calcPowerVitality(snapshot)` is cheap. Power/Vitality % stays as the headline line.
3. **Tooltip structure**: fixed layout of header (name + rarity colour + item level + level requirement), base stats
   (damage range, attack interval, AC, quality %), enchants with their roll quality ("49 / 61 max, 80%"), special,
   legendary affix, value. A rarity frame or border colour on inventory icons is a cheap way to see rarity at a
   glance.
4. **Stash / shared storage**: replace the 5×(5) per-character bags with a party **stash** at inns/houses (or
   anywhere when solo) plus named tabs. Same save cost and no record juggling. Keep "bags" as tabs of one container
   type so the solo 25-grid and the party 5-grid are one feature with different capacities (data).
5. **Sort buttons** on the inventory and stash panels (by type, rarity, item level, value), with keys still bound.
   Auto-route rules ("send crafting items / potions / reagents to X or to the Crafting tab"), which generalises MAW's
   alchemy player and crafting bag into one data-driven routing table.
6. **Loot filter as a real system**: rule list (rarity ≥, slot, has legendary, item level ≥ party−N), actions
   (pick up, auto-gold, ignore/hide label, highlight). Add ground **loot labels/beams coloured by rarity**
   (cheap in a 3D renderer) and a "pull loot / crafting items" key (MAW's K).
7. **Shop reroll** as a button with the computed price, plus an optional "rarity of stock" summary line.
8. **Drop-rate transparency**: a "Loot" page in the party/stats screen showing current loot tier, difficulty
   multipliers and pity progress (MAW shows nothing about pity). The PDF exists because players wanted this.
9. **Deterministic RNG streams** as an engine feature (scenario tests, multiplayer, anti-scum) rather than
   per-feature seeding.
10. **Unify duplicated code paths**: one item-roll function used by drops, shops, Enchant Item potion, Hourglass and
    previews. MAW has four slightly different copies of "roll an enchant".

### 8.2 Inconsistencies and bugs worth not copying

- README says 14 crafting items, but the code has 20 gem tiers plus 10 specials. Item notes for Eye and Hourglass state
  prerequisites the code does not enforce. README says the Mirror excludes artifacts; the code allows them.
- `mawArtifactsKeep` is fully commented out, so quest-reward artifacts in chests are replaced by random loot when
  their Value is at least 20000.
- Legendary 28 is described as "doubled" but applied as ×1.5. The shop message "20000 gold" is wrong.
- Value formula: the enchant-2 HP/SP branch is missing `*100` and is fed the already multiplied value.
- `LootContext.multiplier` is never set (always 1), so `0.005*multiplier` artifact chances and `sqrt(lootMultiplier)`
  are dead parameters.
- Tooltips mutate items (`updateCelestialItem` writes enchant strengths and MaxCharges; the compare section swaps
  equipped items).
- `Potion settings.txt` rows 99-102 map potion ids to duplicate items.
- The Pearl of Memory and Randomizer are not save-seeded, unlike everything else.
