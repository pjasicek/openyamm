# MAW crafting: complete specification

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`. This document supersedes
[ITEMS.md](ITEMS.md) §3 for crafting; the OpenYAMM design is in [CRAFTING_BENCH_DESIGN.md](CRAFTING_BENCH_DESIGN.md) and
the data draft in [data/crafting_items.yml](data/crafting_items.yml).

Paths are relative to the MAW `Scripts/` folder. Shorthand:

| Tag | File |
|---|---|
| AL | `General/zzAlchemy.lua` (crafting items, gems, drops, names, alchemy) |
| IT | `General/zzMaw-Items.lua` (caps, rarity, shops, values, U key, level requirement) |
| TT | `Modules/MawCore/Tooltip.lua` (ALT previews, tooltip-driven crafting) |
| MP | `Global/zzMAWPotions.lua` (potion-on-item crafting) |
| BITS | `General/zMaw_ItemBits.lua` (field packing) |
| MON | `General/zzMaw-Monsters.lua` (map completion, K key) |
| MAPS | `General/zzMaw-Maps.lua` (dimension maps) |
| CB | `General/zzzMaw_CraftingBag.lua` |
| SORT | `General/zzMaw-Item-Sorter.lua` |
| DMQ | `Global/zzMaw_DimensionalMapsQuest.lua` |

Numbers marked "computed" were produced by loading the MAW files above into a Lua 5.4 interpreter with MMExtension
shims and calling MAW's own functions (`GetGemCap`, `GetPrimordialMaxEnchantStrength`, `pity_chance`,
`normal_random`, `GetCraftingCubeCap`, `craftDropChances`). Seeded outcomes (which enchant the Eye picks for a
particular item) are not reproduced: MAW runs on LuaJIT's `math.random`, which is a different generator from Lua
5.4's, and OpenYAMM will use its own stream anyway (see §7.5).

---------------------------------------------------------------------------------------------------------------------

## 1. Summary

- 30 item ids, 1041-1070: 20 gem tiers, 8 special items, the Endless Potion and the Crafting Cube.
- Five potions also craft: Enchant Item (238), Lesser Element (243), Swiftness (244), Greater Element (255) and
  Darkness (256). Harden Item (236) has no MAW handler.
- The target of every operation is one item; the crafting item is consumed, except when an orb extracts.
- Two dispatch paths (§2): the engine's "use potion on item" hook for most items, and a hack in which building the
  target's tooltip performs the Crafting Cube, Endless Potion and every map operation.
- Sources (§6): monster kills with bad-luck protection, misc shops scaled by party gold, map first completion. No
  quest gives crafting items. Austerity has none at all.
- Previews (§7): ALT shows the Eye, Hourglass and Enchant Item results. Outcomes are seeded from the item's own fields,
  so they survive reloads and change when another crafting item touches the item. The Hourglass preview disagrees
  with the result for HP/SP enchants.

---------------------------------------------------------------------------------------------------------------------

## 2. How crafting is invoked

### 2.1 Path A: the potion-on-item hook (most items)

`Data/Tables/Potion settings.txt` rows 71-102 map potion ids to items and mark them "usable" (not drinkable):

| Pot id | Item | Note |
|---|---|---|
| 71-90 | 1041-1060 | gems; `evt.PotionEffects[70+tier]` (AL:759-784) |
| 91-98 | 1061-1068 | Eye, Hourglass, Pandora's Cube, Mirror, Emerald, Pearl, Oracle's Orb, Celestial Orb (AL:799-1006) |
| 99 | 1069 | Endless Potion; no `PotionEffects[99]`, so this path does nothing for it |
| 100-102 | 1067, 1068, 1069 | duplicate rows; harmless because the first match wins |

The player picks the crafting item up and right-clicks it onto an item in the current character's backpack. MMMerge's
dispatcher (`reference/mmmerge/Scripts/Structs/RemoveItemsLimits.lua:316-340` in the OpenYAMM tree) calls
`evt.PotionEffects[potId](false, targetItem, power, heldIndex)` with `power` = the held item's `Bonus`. A truthy
return makes the engine consume the held item and play a random glow. MAW's handlers return nothing and consume the
item themselves (`Mouse.Item.Number = 0`), then call `ShowCraftedItemEffect`.

Potions 238/243/244/255/256 (pot ids 18/23/24/35/36) use the same path (MP).

### 2.2 Path B: the tooltip hack (Crafting Cube, Endless Potion, map items)

The tooltip section `alchemy-craft-with-held-item` (sort key 130, TT:191-195, registered TT:900) calls
`UseItem(t.Item, Mouse.Item)` (AL:1037-1089) whenever an item information box is built while something is held. So
holding the cube and right-clicking an item **performs** the craft while the info box is being built. Consequences:

- The section runs before `items-enchant-stats` (sort 200), so the box that opens already shows the crafted item.
- Any info box qualifies, not only party items. Nothing in `UseItem` checks where the item is, so a cube held over a
  shop or chest item's info box should apply to that item (inferred from the code; not verified in game).
- Map items (290) receive the Eye, Hourglass, Emerald and Crafting Cube only through this path, because their
  `PotionEffects` handlers start with `IsBaseItemId(t.Number)`, which is false for 290.

### 2.3 Cooldown

`craftWaitTime` (AL:786-797) is set to 60 frames when `craftingItemUsed` is true, and counts down every frame. Only
the Oracle's Orb and Celestial Orb set `craftingItemUsed`; only gems and those two orbs check `craftWaitTime`. Its
purpose is the orbs: extraction leaves the orb on the cursor, and without the wait the next right-click would imprint
the affix straight back. Side effect: for one second after any orb use, gems fail silently.

### 2.4 Feedback

- `ShowCraftedItemEffect(it)` (AL:4-7) calls `MawCore.Engine.showItemEffect` (`Modules/MawCore/Engine.lua:141-144`):
  sets the engine's item-effect timer to 0x100 and ORs 0x10 into `Condition` (the enchant-glow flag), then plays
  sound 12070.
- Endless Potion: sound 12070 only, no glow (AL:1083-1088).
- Gem merge (U): status text only, no sound.
- Crafting-bag pickup: sound 133 and a status line (CB:243-244).
- Failures are status-bar texts (§3.13) or silent.

---------------------------------------------------------------------------------------------------------------------

## 3. The items

### 3.1 Table

Names, pictures and unidentified names are overwritten in Lua at `GameInitialized2` (AL:1297-1343); the LOD
`ITEMS.txt` rows are stale ("Crafting Moonstone", "The Eye", "Misterious Mirror", ...), and rows 1041-1050 and
1068-1070 are still MMMerge's `_potion/reagent` placeholders whose EquipStat, Skill and Material Lua never sets.
"Value" is `ItemsTxt.Value` (IT:2232-2243, AL:1336): it is what selling and other prices start from. "Shop price" is
`reagentPrices` (IT:2011-2040), used only on buy screens (HouseScreen 2 and 95). "Cells" are inventory sizes from
`itemSizeMap` (SORT:1817-1847). Every item's unidentified name is "Crafting Item", except the Endless Potion
("Potion Bottle").

| Id | Name (code) | Icon | Cells | Value | Shop price | Shop weight |
|---|---|---|---|---|---|---|
| 1041 | Lunar Shard (gem tier 1) | vCraft1 | 1×1 | 1,000 | 1,000 | gem roll |
| 1042 | Fire Topaz (2) | vCraft2 | 1×1 | 2,000 | 2,000 | gem roll |
| 1043 | Amethyst Chunk (3) | vCraft3 | 1×1 | 3,000 | 4,000 | gem roll |
| 1044 | Amber Droplet (4) | vCraft4 | 1×1 | 4,000 | 7,000 | gem roll |
| 1045 | Royal Amethyst (5) | vCraft5 | 1×1 | 5,000 | 12,000 | gem roll |
| 1046 | Gemcutter's Ruby (6) | vCraft6 | 1×1 | 6,000 | 20,000 | gem roll |
| 1047 | Solarstone (7) | vCraft7 | 1×1 | 7,000 | 30,000 | gem roll |
| 1048 | Erudite Crystal (8) | vCraft8 | 1×1 | 8,000 | 40,000 | gem roll |
| 1049 | Erathian Sapphire (9) | vCraft9 | 1×1 | 9,000 | 50,000 | gem roll |
| 1050 | Queen's Diamond (10) | vCraft10 | 1×1 | 10,000 | 60,000 | gem roll |
| 1051-1060 | "Ascended " + the names above (tiers 11-20) | vCraft1Asc..vCraft10Asc | 1×1 | 11,000-20,000 | 80,000-300,000 | gem roll (≤ tier 16) |
| 1061 | Eye of Void | vEye1 | 2×2 | 30,000 | 1,250,000 | 7 |
| 1062 | Creator's Hourglass | vHour1 | 1×2 | 20,000 | 750,000 | 7 |
| 1063 | Pandora's Cube | vCraft11 | 1×1 | 15,000 | 325,000 | 15 |
| 1064 | Archibald's Mirror | vMirror | 2×2 | 100,000 | 6,668,999 | 2 |
| 1065 | Emerald of Power | vCraft12 | 1×2 | 60,000 | 2,000,000 | 5 |
| 1066 | Pearl of Memory | vCraft13 | 1×1 | 25,000 | 1,000,000 | 7 |
| 1067 | Orb of Creation (all texts call it "Oracle's Orb") | vEternal2 | 2×2 | 80,000 | 3,000,000 | 3 |
| 1068 | Celestial Orb | vEternal1 | 2×3 | 200,000 | not sold | — |
| 1069 | Endless Potion | item280 | 1×2 | 0 | not sold | — |
| 1070 | Crafting Cube | picture of item 2076 (Control Cube) | 2×2 | 15,000 | 250,000 | 15 |

Gem shop prices for tiers 11-20: 80,000, 100,000, 120,000, 140,000, 160,000, 180,000, 200,000, 230,000, 260,000,
300,000 (only tiers ≤ 16 are ever stocked). Ground sprites: gems use sprite 141+tier (tiers n and n+10 share one);
1068 uses sprite 411; 1063 takes the Control Cube's sprite and 1070 takes 1063's old one (AL:1312-1335). The icon
`vCelest1` exists in `zVex.icons.lod` but nothing references it. Gem names in the U-key status messages come from a
second, different list (IT:4206: "Ascended Topaz", "Ascended Purple Amethyst", ...).

Selling: the MawCore shop filter refuses items with Value 0 and, unless their quest is done, items with Material 3
(`Modules/MawCore/SpecialItems.lua:109-129`). The Endless Potion (Value 0) and, through its LOD Material 3, the Emerald
of Power cannot be sold. The Emerald case looks unintended.

### 3.2 Common gates

| Gate | Gems | Eye | Hourglass | Pandora | Mirror | Emerald | Pearl | Oracle | Celestial Orb | Crafting Cube |
|---|---|---|---|---|---|---|---|---|---|---|
| Base item ids only (`IsBaseItemId`, IT:95-97) | yes | yes | yes | yes, or artifact | yes, or artifact | yes | yes | yes | yes | yes |
| Level requirement vs current character's `LevelBase` | yes | no | no | yes | no | no | no | no | no | own cap (§3.11) |
| Refuses Celestial items | silent | no | no | no | no | no | no | no | §3.10 | silent |
| `craftWaitTime` | silent | no | no | no | no | no | no | yes | yes | no |

Base ids are 1-151 (MM8), 803-936 (MM6), 1603-1736 (MM7). Crafting deliberately uses `IsBaseItemId` rather than
`IsEnchantableItem`, so the four "ancient" blasters (866, 867, 1666, 1667) can be crafted although loot never rolls
on them (IT:104-112). Artifacts are 500-543, 1302-1354, 2020-2049 (IT:101-103). The level requirement is
`GetLevelRquirement` (IT:4351-4373): 0 for non-equipment, 1 for Celestial, else
`floor(WearLevel(dropLevel + TierLevels))` with −6 at bolster ≥ 300, −3 Doom, −3 Insanity, minimum 1
([ITEMS.md](ITEMS.md) §1.7). It is compared with `Party[Game.CurrentPlayer].LevelBase`, the character whose
inventory is open, not the wearer.

Slot multipliers (`slotMult`, IT:1405), indexed by the item table's live `EquipStat`:

| EquipStat | 0 1H | 1 2H | 2 bow | 3 body | 4 shield | 5 helm | 6 belt | 7 cloak | 8 gauntlets | 9 boots | 10 ring | 11 amulet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mult | 1 | 2 | 1.25 | 1.5 | 1 | 1.25 | 1 | 1 | 1.25 | 1.25 | 0.75 | 1 |

Crafting reads `it:T().EquipStat` directly, while loot rolls and stat reads go through `GetItemEquipStat` and
`GetSlotMult` (IT:4390-4425), which force `twoHandedAxes` to slot 1 (×2) and multiply hats (helms with Mod2 0) by
1.5. MAW also rewrites the axe rows of the item table at runtime: while a Minotaur with Expert Axe is the current
player, 2H axes get `EquipStat 0` (`General/zzMAW-Skills.lua:1722-1766`). So a 2H axe's gem cap and Hourglass cap are
×1 (instead of ×2) whenever the axe's table row says 1H, and a hat's gem cap ignores the hat bonus that its displayed
enchant receives.

### 3.3 Gems (1041-1060)

**Handler**: `evt.PotionEffects[71..90]` (AL:759-784), `upgradeGem` (AL:726-757). Tier = `item id − 1040`.

**Order of checks** (the first that fails ends the attempt):

1. Target is a base item, else nothing.
2. `craftWaitTime > 0` or the target is Celestial: return silently.
3. `LevelBase < GetLevelRquirement(target)`: "Your level is too low (Level N required)".
4. Target has neither enchant 1 (`Bonus`) nor enchant 2 (`HasEnc2`): "No enchants". A special alone does not count.
5. No enchant can be raised: "Gem power is not enough".

**Effect**:

```
skill1   = Bonus >= 17                                   (enchant 1 is a skill enchant, 17-24)
cap1     = GetGemCap(tier, EquipStat, skill1)
cap2     = GetGemCap(tier, EquipStat, false)            (enchant 2 is never a skill)
frac1    = BonusStrength / cap1        (infinite if Bonus == 0)
frac2    = enc2Strength / cap2         (infinite if no enchant 2)
if frac1 <= frac2 and BonusStrength < cap1:  BonusStrength = min(BonusStrength + (skill1 ? 1 : 3), cap1)
elif frac2 <= frac1 and enc2Strength < cap2 and enc2Strength < 65535:
                                             enc2Strength = min(enc2Strength + 3, cap2, 65535)
else: "Gem power is not enough", gem kept

GetGemCap(tier, equipStat, skill) (AL:715-721):
  cap = round(tier / 20 * PrimordialMax)
  if skill: cap = ceil(max(sqrt(cap), cap / 10))         (Formulas.skillEnchantPower)
  return ceil(cap * slotMult[equipStat])

PrimordialMax = round(ceil(100 * diffPower) * 25 / 20)   (GetPrimordialMaxEnchantStrength, IT:477-480)
diffPower     = 1.2 Insanity or Madness, 1.1 Doom, 1.05 True Nightmare, else 1   (IT:552-561)
```

The weaker enchant is chosen **relative to its own cap**, so a skill enchant at 8/10 loses to a stat enchant at
70/125. The gem's `Power` argument is unused. An enchant already above the cap (Primordial drops roll up to 125 % of
the loot curve) blocks that enchant; if both are above the cap the gem is refused. Gems never touch the special
enchant, item power or quality. The cap uses the normal enchant curve (`encStrUpNormal`) even in Austerity.

`100 * 1.1` is `110.00000000000001` in IEEE doubles, so `ceil` gives 111 and Doom's PrimordialMax is **139**, not
the 138 that exact arithmetic gives. The same artefact makes every Doom enchant roll `ceil(x * 1.1)` one point high
for round x.

**Caps, computed** (`GetGemCap` for each slot multiplier; skill columns are skill-enchant caps):

Easy, Normal, MAW, Hard, Hell (PrimordialMax 125):

| Tier | ×1 | ×1.25 | ×1.5 | ×2 | ×0.75 | skill ×1 | skill ×1.25 | skill ×1.5 | skill ×2 | skill ×0.75 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 8 | 9 | 12 | 5 | 3 | 4 | 5 | 6 | 3 |
| 2 | 13 | 17 | 20 | 26 | 10 | 4 | 5 | 6 | 8 | 3 |
| 3 | 19 | 24 | 29 | 38 | 15 | 5 | 7 | 8 | 10 | 4 |
| 4 | 25 | 32 | 38 | 50 | 19 | 5 | 7 | 8 | 10 | 4 |
| 5 | 31 | 39 | 47 | 62 | 24 | 6 | 8 | 9 | 12 | 5 |
| 6 | 38 | 48 | 57 | 76 | 29 | 7 | 9 | 11 | 14 | 6 |
| 7 | 44 | 55 | 66 | 88 | 33 | 7 | 9 | 11 | 14 | 6 |
| 8 | 50 | 63 | 75 | 100 | 38 | 8 | 10 | 12 | 16 | 6 |
| 9 | 56 | 70 | 84 | 112 | 42 | 8 | 10 | 12 | 16 | 6 |
| 10 | 63 | 79 | 95 | 126 | 48 | 8 | 10 | 12 | 16 | 6 |
| 11 | 69 | 87 | 104 | 138 | 52 | 9 | 12 | 14 | 18 | 7 |
| 12 | 75 | 94 | 113 | 150 | 57 | 9 | 12 | 14 | 18 | 7 |
| 13 | 81 | 102 | 122 | 162 | 61 | 9 | 12 | 14 | 18 | 7 |
| 14 | 88 | 110 | 132 | 176 | 66 | 10 | 13 | 15 | 20 | 8 |
| 15 | 94 | 118 | 141 | 188 | 71 | 10 | 13 | 15 | 20 | 8 |
| 16 | 100 | 125 | 150 | 200 | 75 | 10 | 13 | 15 | 20 | 8 |
| 17 | 106 | 133 | 159 | 212 | 80 | 11 | 14 | 17 | 22 | 9 |
| 18 | 113 | 142 | 170 | 226 | 85 | 12 | 15 | 18 | 24 | 9 |
| 19 | 119 | 149 | 179 | 238 | 90 | 12 | 15 | 18 | 24 | 9 |
| 20 | 125 | 157 | 188 | 250 | 94 | 13 | 17 | 20 | 26 | 10 |

True Nightmare (131), Doom (139) and Insanity/Madness (150), stat caps only (skill caps differ from the table above
by at most 2):

| Tier | NM ×1 | NM ×1.25 | NM ×1.5 | NM ×2 | NM ×0.75 | Doom ×1 | Doom ×1.25 | Doom ×1.5 | Doom ×2 | Doom ×0.75 | Ins ×1 | Ins ×1.25 | Ins ×1.5 | Ins ×2 | Ins ×0.75 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 7 | 9 | 11 | 14 | 6 | 7 | 9 | 11 | 14 | 6 | 8 | 10 | 12 | 16 | 6 |
| 2 | 13 | 17 | 20 | 26 | 10 | 14 | 18 | 21 | 28 | 11 | 15 | 19 | 23 | 30 | 12 |
| 4 | 26 | 33 | 39 | 52 | 20 | 28 | 35 | 42 | 56 | 21 | 30 | 38 | 45 | 60 | 23 |
| 6 | 39 | 49 | 59 | 78 | 30 | 42 | 53 | 63 | 84 | 32 | 45 | 57 | 68 | 90 | 34 |
| 8 | 52 | 65 | 78 | 104 | 39 | 56 | 70 | 84 | 112 | 42 | 60 | 75 | 90 | 120 | 45 |
| 10 | 66 | 83 | 99 | 132 | 50 | 70 | 88 | 105 | 140 | 53 | 75 | 94 | 113 | 150 | 57 |
| 12 | 79 | 99 | 119 | 158 | 60 | 83 | 104 | 125 | 166 | 63 | 90 | 113 | 135 | 180 | 68 |
| 14 | 92 | 115 | 138 | 184 | 69 | 97 | 122 | 146 | 194 | 73 | 105 | 132 | 158 | 210 | 79 |
| 16 | 105 | 132 | 158 | 210 | 79 | 111 | 139 | 167 | 222 | 84 | 120 | 150 | 180 | 240 | 90 |
| 18 | 118 | 148 | 177 | 236 | 89 | 125 | 157 | 188 | 250 | 94 | 135 | 169 | 203 | 270 | 102 |
| 20 | 131 | 164 | 197 | 262 | 99 | 139 | 174 | 209 | 278 | 105 | 150 | 188 | 225 | 300 | 113 |

All 20 rows for every difficulty are in the data draft's `gem_cap_formula` (the formula reproduces them exactly).

**Gems needed, computed.** The cheapest way to raise one enchant from 0 to the tier-20 cap is to always use the lowest
tier whose cap is above the current strength (Easy..Hell):

| Slot | Gems used, 0 → cap | Of those, tiers 17-20 | Tiers 17-20 in tier-16 gems (via U) |
|---|---|---|---|
| 1H, shield, belt, cloak, amulet (×1, cap 125) | 45 | 9 | 249 |
| Bow, helm, gauntlets, boots (×1.25, cap 157) | 60 | 12 | 360 |
| Body armour (×1.5, cap 188) | 65 | 13 | 369 |
| Two-handed (×2, cap 250) | 85 | 17 | 489 |
| Ring (×0.75, cap 94) | 40 | 8 | 240 |
| Skill enchant on ×1 (cap 13) | 13 | 3 | 39 |

The last 20 % of a cap is where most of the cost lies, because tiers 17-20 only exist through merging (3, 9, 27, 81
tier-16 gems each).

**Tooltip** (TT:143-163): tier, "Max Power" (the ×1 cap), "Bonus: 3 (1 on skills)", the skill cap and four slot lines
(2H, body, "Helm-Boots-Gloves-Bow" using equipStat 5, rings), plus the U-key and drop-tier texts. There is no preview
of which enchant a gem would raise on a given item.

### 3.4 Gem merge (U)

`events.KeyDown` (IT:4207-4275), inventory page only (`CurrentScreen 7`, `CurrentCharScreen 103`):

1. First U: scan tiers 1..19 in order; for the first tier with ≥ 3 gems whose `BonusStrength == 0` in
   `Party[j].Items` for any member, show "Convert <name> into <next name>? (U)". If none: "No gem to upgrade".
2. A second U (no other key in between; any other key clears `gemUpgrading`) rescans from tier 1, removes three gems
   of the first eligible tier and gives one gem of the next tier with `evt.Add("Items", id)` (it lands on the cursor),
   then sets the new gem's `BonusStrength` to 0 and shows "<name> created".

Details:

- One merge per confirmation, lowest tier first; there is no way to choose the tier.
- Only the currently loaded backpacks count. Gems in a character's other multibag bags (§8.2) are invisible.
- The confirm step does not check that it merges the tier that was announced.
- `BonusStrength ~= 0` excludes gems from an older "ascended flag" design (the commented-out tooltip at TT:144-151).
- Tier 20 cannot be merged further. Tiers 17-20 never drop and are not sold, so U is their only source.

Cost in tier-1 gems: tier n = 3^(n−1) (tier 16 = 14,348,907, so in practice players merge from dropped
mid tiers).

### 3.5 Eye of Void (1061)

`evt.PotionEffects[91]` (AL:799-826).

- Gates: base item; `Bonus2 == 0` (no special), else silent. No level, Celestial or enchant-count check.
- Effect: seed `math.randomseed(Number*10000 + MaxCharges*1000 + Bonus*100 + BonusStrength*10 + Charges)`; roll
  `random(1, total)` over SPCITEMS rows whose `Lvl` is D (`enchants[6] = {3}`), weighted by `ChanceForSlot[EquipStat]`
  (`itemStrength[6]`, IT:405-440). `Bonus2 = row + 1`. The Eye is consumed and the item glows.
- Unlike loot (IT:1206-1295), the Eye does not swap Ascension/Lichs' against Dragon/Darkness to match the item's
  melee or caster enchants, and does not avoid 40/41 on Legendary affix 19 items.

Pool D per slot (computed from MAW's `SPCITEMS.TXT`; Bonus2 id, name, chance):

| Slot | Pool |
|---|---|
| 1H, 2H (total 154) | 6 Ice, 9 Thunderbolts, 12 Infernos, 15 Acid 13.0 % each; 39 Ascension, 43 Earth, 46 The Dragon 6.5 %; 1 Protection, 2 The Gods, 16 Vampiric, 40 Lichs', 41 Darkness, 51 The Sky, 54 The Troll, 55 The Unicorn 3.2 %; 25 Power, 80 Divines' 1.3 % |
| Bow (164) | as weapons plus 3 Carnage 6.1 % (others scaled down: elements 12.2 %) |
| Body armour (122) | 36 Shielding 20.5 %; 50 Phoenix, 54 Troll 16.4 %; 1, 2, 43, 51, 55 8.2 %; 80 Divines' 4.1 %; 25 Power 1.6 % |
| Shield (127) | 36 Shielding 23.6 %; 50, 54 15.7 %; 1, 2, 43, 51, 55 7.9 %; 80 3.9 %; 25 1.6 % |
| Helm (107) | 50 Phoenix, 51 Sky, 55 Unicorn 18.7 %; 1, 2, 43, 54 9.3 %; 80 4.7 %; 25 1.9 % |
| Cloak (87) | 36 Shielding 23.0 %; 1, 2, 43, 51, 54, 55 11.5 %; 80 5.7 %; 25 2.3 % |
| Belt, gauntlets, boots (67) | 1, 2, 43, 51, 54, 55 14.9 %; 80 Divines' 7.5 %; 25 Power 3.0 % |
| Ring, amulet (157) | nine school specials 26-34 and 1, 2, 43, 51, 54, 55 at 6.4 % each; 80 3.2 %; 25 1.3 % |

The item note says "add a Special enchant to any equipment that has already 2 base enchants"; the code does not check.
The MAW README says "an item with at least 1 normal enchant"; the code does not check that either.

### 3.6 Creator's Hourglass (1062)

`evt.PotionEffects[92]` (AL:828-845).

- Gates: base item; `Bonus > 0`, `BonusStrength > 0` and no enchant 2, else silent. No level or Celestial check.
- Effect (same seed formula as the Eye):

```
type     = RollEnchantType(item, exclude = Bonus)   uniform 1..10, rings 1..16, rerolled while == Bonus (IT:880-887)
mult     = max((BolsterAmount - 100) / 1000 + 1, 1)  Easy..MAW 1, Hard 1.05, Hell 1.1, Nightmare 1.2, Doom/Ins/Mad 1.5
cap      = min(100 * mult * slotMult[EquipStat], 65535)
strength = min(round(BonusStrength * (1 + 0.25 * random())), cap)
SetEnc2(item, type, strength)
```

- Enchant 2 never becomes a skill enchant, and is never the 10 % skill roll of loot. When enchant 1 is a skill
  enchant (strength 3-26), enchant 2 inherits that small number.
- The cap is 100 × slot (125 × slot for Primordial loot, gem tier 17+ above it on Easy..Hell), so on strong items the
  Hourglass hits its cap.
- The note says it needs "1 base and a special enchant"; the code does not require a special.

### 3.7 Pandora's Cube (1063)

`evt.PotionEffects[93]` (AL:847-868); constants IT:717-747, BITS:113, 254-270.

- Gates: base item or artifact; `GetCubeQualityStep > 0` else "Only weapons and armor can be refined"; level
  requirement; quality < 20 else "Item quality reached its limit".
- Effect: `quality = min(quality + step, 20)` stored in `BonusExpireTime` bits 20-24. Weapon damage rows
  (`GetWeaponDamageRows`) and armour AC (`collectArmorAC`) are multiplied by `1 + quality/100`.
- Step by `MawItemRarity` (IT:691-715): Common, Uncommon 20; Rare 10; Epic 7; Ancient 5; Primordial, Legendary 4;
  Celestial 1; artifacts 2. Cubes to reach 20 %: 1, 1, 2, 3, 4, 5, 5, 20, 10. The last step is clipped (Epic:
  0 → 7 → 14 → 20).
- `CanTakeCube` (IT:729-736) accepts EquipStat ≤ 2 with a weapon skill, Shield/Leather/Chain/Plate skills, and any
  "Misc"-skill (40) item except EquipStat 12 (wands). Helms, belts, cloaks, gauntlets and boots have AC in MAW, so
  that is useful; **rings and amulets also pass**, take the cube and gain a quality value that multiplies nothing.
- Celestial items are not refused (step 1). Because the step follows the current rarity, a Pearl that removes an
  enchant lowers the rarity (enchant count) and raises the step.

### 3.8 Archibald's Mirror (1064)

`evt.PotionEffects[94]` (AL:870-882).

- Gates: base item or artifact. Nothing else: no level, Celestial, cooldown or enchant check.
- Effect: the mirror on the cursor becomes a copy: `Number, Bonus, BonusStrength, Charges, Bonus2, MaxCharges,
  BonusExpireTime` are copied. `Condition` is not copied, so the copy is unidentified, unbroken and not hardened.
  The target glows; the mirror is not "consumed", it is replaced by the copy.
- Copies artifacts (the README says "artifacts excluded"), Celestials, legendary affixes, quality and drop level. Two
  copies have identical Eye and Hourglass outcomes (§7.2).

### 3.9 Emerald of Power (1065)

`evt.PotionEffects[95]` (AL:884-940).

- Gates: base item. Silent if no upgrade exists.
- Effect, first rule that applies:
  1. If item `Number + 1` has the same `NotIdentifiedName` (the next rung of the same family), become it. This does
     not check that `Number + 1` is a base id.
  2. Weapons (EquipStat ≤ 2): among all base items of the same skill and EquipStat, the one with the smallest
     `power > current`, `power = (Mod1DiceCount * Mod1DiceSides + 1) / 2 + Mod2`. (The mean of the dice is
     `count * (sides + 1) / 2`; the formula is slightly off, which only affects ordering.) The search spans all
     three games' bands, so the result can be another game's weapon.
  3. Armour: the same search with `power = Mod1DiceCount + Mod2` and the same `Skill` and EquipStat.
- Enchants, item power, quality and rarity are kept; only `Number` changes. The ladder tier of the new base raises
  the level requirement by up to 3 per rung (`TierLevels`).
- Calls `Game:ExitHouseScreen()` after every success, even outside houses.
- The LOD note ("right-click on an unequipped item to increase its tier by 1") is the only text; nothing checks
  "unequipped".

### 3.10 Pearl of Memory (1066)

`evt.PotionEffects[96]` (AL:942-969).

- Gates: base item with at least one of enchant 1, enchant 2, special; else silent.
- Effect: repeat `random(1, 3)` until it names a present enchant (so uniform over present ones). Removing enchant 1
  promotes enchant 2 into slot 1 and clears `Charges`; removing enchant 2 clears `Charges`; removing the special sets
  `Bonus2 = 0`.
- **Not seeded**: the result depends on whatever state `math.random` is in, so it is not predictable and not stable
  across reloads, unlike every other MAW craft.
- Promotion moves a resistance enchant into slot 1, where reads add +10 (ITEMS.md §1.5), and the
  ancient/primordial/legendary bits survive, so a "Primordial" item can have one enchant.
- OpenYAMM lets the player pick the enchantment on the Workbench instead of rolling (DEVIATIONS.md 35,
  CRAFTING_BENCH_DESIGN.md §6.4).

### 3.11 Oracle's Orb (1067, named "Orb of Creation")

`evt.PotionEffects[97]` (AL:971-989); affix storage BITS:192-226.

- Gates: base item; `craftWaitTime == 0`. Sets the 60-frame cooldown on every attempt, successful or not.
- Empty orb (`BonusStrength == 0`) on an item with a legendary affix: the orb's `BonusStrength` becomes the affix id
  (11-35) and the item loses its affix. The orb stays on the cursor.
- Charged orb (`10 < BonusStrength < 1000`) on any base item: the item gets that affix, keeping its tier and
  Celestial bits; the orb is consumed. An affix the item already had is **overwritten without warning**.
- Otherwise nothing, silently.
- Tooltip (TT:165-174): uncharged "Right click a legendary item to store its power", charged "Adds the following
  legendary power to an item:" plus the affix text. The uncharged branch also appends `legendaryEffects[0]`, which
  is nil.

### 3.12 Celestial Orb (1068)

`evt.PotionEffects[98]` (AL:991-1006).

- Gates: base item; `craftWaitTime == 0`. Sets the cooldown.
- Charged orb (`BonusStrength == 1`) on a non-Celestial item: the item becomes Celestial; the orb is consumed.
- Empty orb on a Celestial item: the item loses Celestial; the orb becomes charged.
- Anything else: "Invalid Item".
- A Celestial item's enchant strengths and `MaxCharges` are rewritten from the viewer's level on every stat refresh
  and tooltip (`updateCelestialItem`, IT:1622-1660): `tier = min(LevelBase, 1.2 * totalLevel)/11 + 5`,
  `strength = round(ceil(encStrUp(tier) * diffPower) * (1.25 if Primordial) * slotMult)` (skill enchants /10),
  `MaxCharges = GetPrimordialCharges(level)`. Only enchants that exist are rescaled: a Celestial made from a
  one-enchant item stays one-enchant. Extracting freezes the numbers at the last rewrite.

### 3.13 Crafting Cube (1070)

`craftingCubeOnItem` (AL:1019-1035), reached only through Path B.

- Gates: base item, not Celestial (both silent).
- `cap = GetCraftingCubeCap(Party[Game.CurrentPlayer].LevelBase) = min(floor(level / 5), 120)` (AL:1015-1017; 120
  is `GetPrimordialCharges(math.huge)`). At or above it: "Item power reached the limit for your level (cap)".
- Effect: `MaxCharges = min(MaxCharges + step, cap)`, step 2 on EquipStat ≤ 3 (1H, 2H, bow, body armour), else 4.
- Item power drives weapon damage, armour AC, special-enchant scaling, attack speed and value (ITEMS.md §1.6).
- The level requirement does **not** rise for items that store their drop level (bits 9-19 of `BonusExpireTime`,
  everything generated by current MAW). Only legacy items without a stored drop level reconstruct it from
  `MaxCharges`.
- Cap by player level, computed: 1 → 0, 20 → 4, 50 → 10, 100 → 20, 200 → 40, 300 → 60, 400 → 80, 500 → 100,
  600+ → 120. The ALT line "Item Bonus Power: X/255" (TT:470-474) shows the hard cap 255, not this one.
- The note also says it moves a Dimension Map (§5).

### 3.14 Endless Potion (1069)

`UseItem` (AL:1083-1088), Path B.

- Targets: potions 231, 232, 233, 237, 245, 251, 257, 263 (Protection, Meditation, Regeneration, Magic Protection,
  Champion's, Paladin's, Divine Blessing, Divine Resistance). The other twelve charge potions (§9.3) are not
  accepted, which matches the item note.
- Effect: `Charges = (Charges == 0 ? 6 : Charges) + BonusStrength`; sound 12070; consumed.
- Charge encoding: a fresh potion has `Charges 0` = 5 uses. Drinking does 0 → 5, then −1 while > 2, and consumes the
  potion at 2 (AL:247-256). Remaining uses = `Charges − 1` (5 when 0), which is what the tooltip prints (TT:112-122),
  so "0 counts as 6" keeps the arithmetic consistent.
- `BonusStrength = min(best party Alchemy skill + 10, 100)` at drop time (AL:691-697).

### 3.15 Messages

| Text | Where |
|---|---|
| Your level is too low (Level N required) | gems, Pandora (AL:767, 857) |
| No enchants | gems (AL:773) |
| Gem power is not enough | gems (AL:780) |
| Only weapons and armor can be refined | Pandora (AL:851) |
| Item quality reached its limit | Pandora (AL:862) |
| Invalid Item | Celestial Orb (AL:1001) |
| Item power reached the limit for your level (N) | Crafting Cube (AL:1025) |
| No other completed dungeon to move this map to | Crafting Cube on a map (AL:1069) |
| This potion has not enough power | Enchant potions below their power (MP) |
| Convert X into Y? (U) / X created / No gem to upgrade | U key (IT:4239-4271) |

Silent failures: Eye on an item with a special; Hourglass without enchant 1 or with enchant 2; Emerald without an
upgrade; Pearl without enchants; Oracle's Orb with nothing to do; every operation on a non-base item; gems on
Celestial items or during the cooldown.

### 3.16 Notes versus code

| Item | Text claims | Code does |
|---|---|---|
| Eye | needs 2 base enchants (note); needs 1 (README) | needs no special only |
| Hourglass | needs 1 base enchant and a special (note) | needs enchant 1, no enchant 2 |
| Pandora's Cube | weapons and armour | also helms, belts, cloaks, gauntlets, boots, rings, amulets |
| Mirror | "any equipment (artifacts excluded)" (README) | base items and artifacts; copy is unidentified |
| Emerald | "unequipped item", "+1 tier" | no equipped check; next rung or nearest stronger base of any game |
| Oracle's Orb | named Oracle's Orb in notes and tooltip | item name "Orb of Creation" (AL:1294) |
| Crafting Cube | README: "increases base stats and special enchant strength" | current code: item power; base-stat quality is Pandora's Cube |
| Gems | LOD notes "by 2, up to 10" etc. | replaced by the tooltip; +3 (+1 skill) up to the tier cap |
| README | "14 new crafting items" | 30 ids |
| README | "outcome predetermined, ALT shows it" | only Eye, Hourglass and Enchant Item have previews; Pearl is unseeded |

---------------------------------------------------------------------------------------------------------------------

## 4. Potion-on-item crafting

All in MP, via Path A with `power = Mouse.Item.Bonus`. Power is checked first, then the target; a weak potion
reports "This potion has not enough power" even on an invalid target. Brewing mastery comes from `Potion settings.txt`.

| Potion | Pot | Brew | Power | Target | Effect |
|---|---|---|---|---|---|
| 238 Enchant Item | 18 | Expert (P+G) | none in code (text says 20) | base item with no enchant 1, no enchant 2, no special | enchant 1 (below) |
| 243 Lesser Element | 23 | Master | ≥ 40 | base item, `Bonus2 == 0`, `Skill < 7` | special `random(1,4)*3+2`: 5 Frost, 8 Lightning, 11 Flame, 14 Venom |
| 244 Swiftness | 24 | Master | ≥ 40 | same | special 59 Swift |
| 255 Greater Element | 35 | Master | ≥ 55 | same | special `random(1,4)*3+3`: 6 Ice, 9 Thunderbolts, 12 Infernos, 15 Acid |
| 256 Darkness | 36 | Master | ≥ 100 | same | special 41 "of Darkness" |
| 236 Harden Item | 16 | Expert | — | — | MAW's handler is commented out ("not working", MP:93-104); the engine's native Harden path presumably still runs (not verified) |

- `Skill < 7` means Staff, Sword, Dagger, Axe, Spear, Bow and Mace: bows qualify, blasters and non-weapons do not.
- Base enchants on the weapon do not matter; only an existing special blocks. The specials are permanent (vanilla
  coating potions are temporary).
- Lesser and Greater Element are **unseeded** and have no preview.
- Darkness computes an unused `enchNumber`. `potionPowerRequirement[256] = 50` (AL:284-290) only applies when drinking,
  and 256 is not drinkable.

**Enchant Item** (MP:54-91):

```
seed      = vars.enchantSeedList[Number] + MaxCharges     (per-save list of 2501 random numbers, made on first use)
type      = random(1,10) == 1 ? random(17, 24)           (skill: Alchemy..Unarmed, no Dodge/Unarmed swaps)
          : ring ? random(1, 16) : random(1, 10)
strength  = min(power, 500) / 5                           (stored into the integer field, then read back)
strength  = ceil(strength * slotMult[EquipStat])
if skill: strength = max(sqrt(strength), ceil(strength / 10))   (not rounded)
enchantSeedList[Number] += random(1, 1000)                (the next item of this base id rolls differently)
```

Strength by power (stat enchants): power 20 → 4 (1H), 8 (2H), 6 (body), 5 (bow/helm), 3 (ring); 50 → 10/20/15/13/8;
100 → 20/40/30/25/15; 200 → 40/80/60/50/30; 500 → 100/200/150/125/75. At power 500 this is about the loot curve's top
non-Primordial roll.

---------------------------------------------------------------------------------------------------------------------

## 5. Dimension map crafting

Map item 290 ("Dimension Map", MAPS:1037) fields (MAPS:959-1000): `BonusStrength` = target map index;
`BonusExpireTime`, `Bonus2`, `Charges % 1000`, `Charges / 1000` = affixes 1-4; `Bonus` = number of active affixes
(0 means 4); `MaxCharges` = power. Monster level on the map = `power*10 + 20 + mean(map Low, Mid, High)`
(`getDimensionMapLevel`, MAPS:804-807); density `1 + (power*nAff + 20*nAff)/300`.

All through Path B, `UseItem` (AL:1038-1074):

| Item | Gate | Effect |
|---|---|---|
| Eye of Void, Creator's Hourglass | `0 < Bonus < 4` | `Bonus + 1`: activates the next stored affix |
| Emerald of Power | `MaxCharges < 255` | `MaxCharges = min(MaxCharges + 5, 255)`: **+50 monster levels** |
| Crafting Cube | another completed dungeon of the same kind exists | moves the map to a random completed dungeon of the same kind (outdoor list `overworldMaps`, AL:1009); seeded by `BonusStrength + Bonus2*1000 + Charges + 1000000`, then reseeded with `os.time()` |

The Eye and Hourglass do the same thing here. A map with `Bonus 0` (all four active) refuses both.

Map item sources (context for §6): kills at monster level ≥ 100 (70 in Madness) once the Dimensional Maps quest is
done, with pity (MAPS:826-937); a repeat completion of a dimension map (MON:2665-2697); the quest itself (DMQ). The
kill drop's affix count has a bug: `elseif bonus<=0.6` tests the variable instead of the roll (MAPS:917-926), so drops
have 4 affixes 10 %, 3 affixes 20 %, **1 affix 70 %** and never 2. The quest map uses the intended 10/20/70 % for
4/3/2 (DMQ:59).

---------------------------------------------------------------------------------------------------------------------

## 6. Where crafting items come from

### 6.1 Monster kills (AL:1118-1236)

Skipped for reanimated monsters (`Ally == 9999`), resurrected ones (`NameId > 300`), and in Madness on bounty maps,
`zarena.blv`, `d42.blv` and `7d05.blv`.

**Seeding**: Insanity uses the per-monster-type LCG (`getMonsterSeed(mon.Id)`); otherwise `mapvars.MonsterSeed[index]`
(the corpse's loot seed), written back next tick. Before each special item the engine seed advances by
`seed*1664525 + 1013904223 mod 2^32`. Drops are therefore fixed per save and per monster.

```
lvl       = getMonsterLevel(mon)                         (bolstered/unique/boss level)
b         = sqrt(lvl / 10) * extra                        (/ players in multiplayer; 0 in Austerity)
extra     = 10 if 220 <= NameId < 300 (bosses)
          * 1/(5 - variant) for Broodling bosses (variant 1-3)
          * 3 for the 24 "no corpse" monster ids (AL:1116)
          * (1 + (mapPower*nAff + 20*nAff) / 800 * 1.5) on dimension maps
gem       : P = 0.006 * b * (1.5 in Insanity/Madness)                       no pity
            tier = clamp(floor(normal(max(lvl^0.6/4 + 1, lvl/40), sd 2)), 1, 16)
special i : P = pity_chance(base_i, counter_i) * b                          per item, in id order 1061..1070
            success: counter_i = 0;  failure: counter_i += round(b)
pity_chance(c, f) = c ^ (1.38 - c*f*0.5)            (IT:4471-4478; 1 when c >= 1)
```

| Item | Eye | Hourglass | Pandora | Mirror | Emerald | Pearl | Oracle | Celestial Orb | Crafting Cube |
|---|---|---|---|---|---|---|---|---|---|
| base_i | 0.0002 | 0.0002 | 0.001 | 0.00001 | 0.00025 | 0.0002 | 0.00006 | 0.0000025 | 0.001 |
| chance just after a drop (% of base) | 4 % | 4 % | 7 % | 1 % | 4 % | 4 % | 2 % | 1 % | 7 % |
| counter units to certainty (2.76/base) | 13,800 | 13,800 | 2,760 | 276,000 | 11,040 | 13,800 | 46,000 | 1,104,000 | 2,760 |

The pity counters are global (`vars.craftPityCounters`). Bosses add `round(b)` ≈ 10 × more counter per failed kill.
Because the counter grows by `round(b)` but the chance is multiplied by `b`, the long-run rate is slightly below
`base × b` when `b` is just above an integer (80 % of nominal at level 20). Monsters below level 2.5 have
`round(b) = 0`, so their pity never grows. Ground drops use `SummonItem` at the corpse; the nine water monster ids
(AL:1117) use `evt.Add` instead. The Endless Potion and reagents drop from a separate handler (§9.2).

**Expected drops per 1000 kills, computed** as the renewal rate of the pity process (1000 / expected kills between
drops). The specials do not depend on difficulty; gems are ×1.5 in Insanity and Madness; Austerity is 0 everywhere.
Difficulty changes these numbers only through the monster level it produces.

Regular monsters:

| Level | b | Gems Easy-Doom | Gems Ins/Mad | Eye | Hourglass | Pandora | Mirror | Emerald | Pearl | Oracle | Cel. Orb | Cube |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 1.41 | 8.5 | 12.7 | 0.22 | 0.22 | 1.13 | 0.011 | 0.28 | 0.22 | 0.066 | 0.0028 | 1.13 |
| 50 | 2.24 | 13.4 | 20.1 | 0.42 | 0.42 | 2.11 | 0.021 | 0.53 | 0.42 | 0.126 | 0.0053 | 2.11 |
| 100 | 3.16 | 19.0 | 28.5 | 0.62 | 0.62 | 3.11 | 0.031 | 0.78 | 0.62 | 0.187 | 0.0079 | 3.11 |
| 200 | 4.47 | 26.8 | 40.2 | 0.84 | 0.84 | 4.21 | 0.042 | 1.05 | 0.84 | 0.253 | 0.0106 | 4.21 |
| 400 | 6.32 | 37.9 | 56.9 | 1.24 | 1.24 | 6.20 | 0.063 | 1.55 | 1.24 | 0.374 | 0.0157 | 6.20 |

Bosses (×10):

| Level | b | Gems Easy-Doom | Gems Ins/Mad | Eye | Hourglass | Pandora | Mirror | Emerald | Pearl | Oracle | Cel. Orb | Cube |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 14.1 | 85 | 127 | 2.9 | 2.9 | 14.2 | 0.15 | 3.6 | 2.9 | 0.87 | 0.036 | 14.2 |
| 50 | 22.4 | 134 | 201 | 4.5 | 4.5 | 22.2 | 0.23 | 5.6 | 4.5 | 1.36 | 0.057 | 22.2 |
| 100 | 31.6 | 190 | 285 | 6.5 | 6.5 | 31.9 | 0.33 | 8.1 | 6.5 | 1.97 | 0.083 | 31.9 |
| 200 | 44.7 | 268 | 402 | 9.1 | 9.1 | 44.5 | 0.47 | 11.4 | 9.1 | 2.77 | 0.117 | 44.5 |
| 400 | 63.2 | 379 | 569 | 12.8 | 12.8 | 61.7 | 0.65 | 16.0 | 12.8 | 3.88 | 0.164 | 61.7 |

"No corpse" monsters (×3) at level 100: gems 56.9, Pandora and Cube 9.3, Eye 1.9, Mirror 0.094 per 1000. In words, a
level-100 regular kill yields a Pandora's Cube every ~320 kills, an Eye every ~1,600, a Mirror every ~32,000 and a
Celestial Orb every ~127,000.

**Gem tier distribution, computed** (MAW's `normal_random`, 200,000 samples):

| Monster level | Mean μ | Mean tier | Distribution (≥ 0.5 %) |
|---|---|---|---|
| 20 | 2.51 | 2.4 | T1 40 %, T2 20 %, T3 17 %, T4 12 %, T5 7 %, T6 3 %, T7 1 % |
| 50 | 3.61 | 3.3 | T1 21 %, T2 17 %, T3 20 %, T4 18 %, T5 13 %, T6 7 %, T7 3 %, T8 1 % |
| 100 | 4.96 | 4.5 | T1 7 %, T2 10 %, T3 15 %, T4 19 %, T5 19 %, T6 15 %, T7 9 %, T8 4 %, T9 2 % |
| 200 | 7.01 | 6.5 | T3 4 %, T4 9 %, T5 15 %, T6 19 %, T7 19 %, T8 15 %, T9 9 %, T10 5 %, T11 2 % |
| 400 | 10.10 | 9.6 | T5 2 %, T6 4 %, T7 9 %, T8 14 %, T9 19 %, T10 19 %, T11 16 %, T12 10 %, T13 5 %, T14 2 % |
| 600 | 15.0 | 14.3 | T10 2 %, T11 4 %, T12 9 %, T13 15 %, T14 19 %, T15 19 %, T16 31 % |

`floor` of a normal centred on μ biases the mean half a tier down; the clamp to 1 piles the low tail onto tier 1.

### 6.2 Shops (IT:1035-1095)

When a buy screen (HouseScreen 2 or 95) generates stock in a house with id ≤ 110, outside Austerity, each stock item
that is non-equipment (EquipStat ≥ 12) with probability 0.3, or that is of the "Gem" class (EquipStat 19, the MM8
gems such as Zircon 177), always, is replaced:

```
P(special) = min((PartyGold / 20,000,000)^0.7, 1)
special: Eye 7, Hourglass 7, Pandora 15, Mirror 2, Emerald 5, Pearl 7, Oracle 3, Crafting Cube 15   (of 71)
else gem: tier = 1 + min(floor(P / 25) + k, 15),  k = 0 (70 %), 1 (25 %), 2 (5 %)
          P = getPartyLevel(4) = banked levels of continents 1-3
```

`P(special)` per replaced slot, computed: 10k gold 0.5 %, 100k 2.5 %, 1M 12.3 %, 5M 37.9 %, 10M 61.6 %, 20M+ 100 %.
The Celestial Orb and Endless Potion are never sold. In `house_data.txt`, ids 1-109 are weapon, armour and magic
shops and 110 is the first alchemist, so in practice the substitution happens in magic shops on all three continents
and in one alchemist; the other alchemists (111-127) never stock crafting items. Rerolling a shop (R, IT:3922-3984)
regenerates stock through the same hook.

### 6.3 Map completion (MON:2568-2797)

The first time a map's required share of monsters dies (0.99^floor(n/100); 100 % in Insanity outside monster maps):

- Normal: gold, experience, **one Crafting Cube and two gems** of tier `min(ceil((L + bolster)/25 + 0.5), 16)`,
  where `L` = mean map level clamped 1..100, `bolster` = 2L in horizontal progression, 0 in free progression,
  `madnessMapLevels` in Madness, `power*10` on dimension maps. Austerity: no items. Message "Map Completed! You gain
  N Exp, G Gold and a Crafting Material".
- Computed gem tier: L 10 → T1 free / T2 horizontal; 20 → T2 / T3; 40 → T3 / T6; 60 → T3 / T8; 80 → T4 / T11;
  100 → T5 / T13. Free progression ignores how far the monsters were bolstered, so late free-progression maps give
  low gems.
- A dimension map reaches this branch only in Madness (outside Madness its dungeon is already in
  `dungeonCompletedList`, which takes the earlier "Dungeon Completed!" branch). There the reward is by affix count:
  1 → Crafting Cube, 2 → Eye, 3 → Hourglass, 4 → Emerald, 0 → nothing (`rewards[0] = 0`).
- Repeat completions (after a dungeon reset) give no crafting items; a completed dimension map gives a new map item
  when the Dimensional Maps quest is done.

### 6.4 Quests, chests and other

- No quest gives crafting items. The Dimensional Maps quest (DMQ) gives map items and gold/experience.
- Crafting ids have weight 0 in `rnditems.txt`, so chests and random loot never contain them.
- Endless Potions drop only for an Alchemy Grandmaster party (§9.2).
- The K key (MON:4432-4464) pulls up to 30 crafting items and map items lying on the map to the party.

---------------------------------------------------------------------------------------------------------------------

## 7. ALT preview and seeding

### 7.1 What is previewed

`extraDescription = ALT held XOR setting "Extra Item Tooltip"` (IT:1665-1679). With it on, the enchant section
(TT:198-476) adds grey lines:

| Preview | Shown when | Apply runs when | Code |
|---|---|---|---|
| Hourglass: "<Stat> +N" | `Bonus ~= 0`, `BonusStrength ~= 0`, no enchant 2 | same | TT:298-331 vs AL:828-845 |
| Enchant Item: "<Stat> +X" (type only) | blank item | same | TT:333-349 vs MP:54-91 |
| Eye: special text | `Bonus > 0` and `Bonus2 == 0` | `Bonus2 == 0` (also blank items) | TT:434-464 vs AL:799-826 |
| "Item Bonus Power: X/255" | always | — | TT:470-474 |

Without ALT, items with enchant 1 show "Press alt to show craftable stats". Nothing previews gems, Pandora's Cube,
the Mirror, the Emerald (which base it becomes), the Pearl (which enchant goes), the orbs, the Crafting Cube or the
Lesser/Greater Element potions.

### 7.2 Seeds

- Eye and Hourglass: `Number*10000 + MaxCharges*1000 + Bonus*100 + BonusStrength*10 + Charges` (AL:805, 830; TT:300,
  438). No save seed, so the outcome is a pure function of the item's fields, identical in every save and game, and
  identical for Mirror copies. The terms overlap (MaxCharges reaches 255 × 1000 > 10000), so different items collide.
- Enchant Item: `vars.enchantSeedList[Number] + MaxCharges` (per save; the list itself is made with unseeded randoms).
- Pearl, Lesser Element, Greater Element: unseeded.
- After an Eye or Hourglass, `math.random` stays seeded with the item seed; only the map-cube path restores
  `os.time()`.

"Save and reload does not change the outcome; using another crafting item does" (README). Gems change
`BonusStrength` (+30 per gem in the seed), the Crafting Cube and Emerald change `MaxCharges` and `Number`, so players
can step through outcomes by interleaving gems or cubes and watching ALT. Pandora's Cube changes `BonusExpireTime`,
which is not in the seed, so it does not reroll.

### 7.3 The preview/apply drift

The Hourglass preview is a second copy of the roll that transforms HP and SP enchants and the apply path does not:

- If enchant 1 is HP (8), the preview first inverts an old HP formula, `power = floor((-100 + sqrt(100^2 +
  200*power))/2)`. The SP branch is dead because it tests `t.Bonus == 9` (the tooltip struct) instead of
  `t.Item.Bonus`.
- If the rolled enchant 2 is HP or SP, the preview applies the vitality read transform with `mult` = the
  **difficulty** multiplier instead of the slot multiplier (`GetSlotMult` is called and its result discarded).
- These happen before the random factor and the cap, so the cap clips the wrong number.

Computed with the random draw fixed at 0.5 (shown = what the enchant line displays after applying):

| Enchant 1 | Rolled enchant 2 | Slot | Stored after apply | Shown after apply | Preview showed |
|---|---|---|---|---|---|
| Might 40 | End | ×1 | 45 | 45 | 45 |
| Might 40 | HP | ×1 | 45 | 86 | 81 |
| HP 40 | End | ×1 | 45 | 45 | 19 |
| HP 40 | SP | ×1 | 45 | 86 | 26 |
| SP 40 | HP | ×1 | 45 | 86 | 81 |
| HP 80 | HP | ×2 | 90 | 171 | 54 |
| Might 90 | SP | ×1.5 | 101 | 237 | 150 |

Non-HP/SP results match because both copies call `RollEnchantType` and then `random()` in the same order after the
same seed. The Eye copy is the same as the apply path apart from its stricter gate. The comment at TT:445-447 ("must
stay identical") documents the intent.

### 7.4 Preview side effects

- Building a tooltip runs `updateCelestialItem`, which writes the item (TT:204).
- With a cube, Endless Potion or map-crafting item held, building a tooltip performs the craft (§2.2).
- The Enchant Item preview creates `vars.enchantSeedList` if it is missing.

### 7.5 What OpenYAMM should keep

The behaviour worth keeping is: the result is fixed before you commit, survives reload, is shown exactly, and changes
when the item changes. LuaJIT-exact outcomes are not needed. A per-item `craftSeed` stored on the item (assigned at
generation) plus a per-item craft counter, mixed with the operation id, gives that for every operation, including
the Pearl and the element potions. See the design document §4.

---------------------------------------------------------------------------------------------------------------------

## 8. Routing, storage and pickup

### 8.1 Crafting bag (CB)

- Shift+B on the inventory page flags or unflags the current multibag bag (`vars.CraftingBags[rosterIndex][bag]`),
  "<name>'s bag is now a crafting bag" / "... is no longer a crafting bag" (CB:20-55). A yellow "C" is drawn over
  flagged bag buttons on screens 7 and 13 (CB:59-93).
- `events.PickObject` (CB:195-254): when a ground object holding 1041-1070 is picked up and the picker's active bag is
  not flagged, the item goes into the first flagged, non-active bag with room: the picker's bags first, then the other
  members' in party order. Placement is first fit on a stored 14×9 grid (CB:96-170). Message "You found an item
  (<name>)!" plus " -- <owner>" for another member; sound 133.
- Only ground pickups route. Shop purchases, `evt.Add` gifts (map completion, water-monster drops, U merges) and chest
  items are not routed.

### 8.2 Multibag and sorting

- Every character has 5 bags (25 grids when solo) stored as serialised lists ([ITEMS.md](ITEMS.md) §5.2). Crafting
  items in inactive bags are invisible to U (§3.4) and to crafting (only the open backpack is a target).
- E toggles an "alchemy player"; sorting sends potions 220-299, reagents and every crafting item to that character
  (SORT:39-56, 117-205). `alchemyItemsOrder` (SORT:751-758) sorts them Endless, Celestial Orb, Mirror, Oracle's Orb,
  Emerald, Pandora, Crafting Cube, Pearl, Eye, Hourglass, then gems from tier 20 down.

### 8.3 Pull key

K (`teleportDeadMonstersAndCraftingKey`, default 75) moves up to 30 corpses and up to 30 crafting or map items lying
on the map to the party: "Teleported N monsters and M crafting items" (MON:4432-4464).

---------------------------------------------------------------------------------------------------------------------

## 9. Alchemy interplay

### 9.1 One dispatcher

Crafting items are potion ids 71-98 in the same `Potion settings.txt` and go through the same "use potion on item"
dispatcher as Enchant Item and the element potions (§2.1). The held item's `Bonus` is passed as power to all of them;
only the five potions read it. MAW's drink override (`events.UseMouseItem`, AL:62-271) handles ids 221-299 except 290,
so crafting items are never drinkable.

The potions that craft come from the MAW recipe tree ([SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) §5.3):
Enchant Item = Purple + Green (Expert); Lesser Element = Orange + {Protection, Meditation, Regeneration}; Swiftness =
Orange + {Stone Skin, Water Breathing, Harden Item}; Greater Element = Yellow + {Lesser Element, Swiftness,
Champion's}; Darkness = Blue + the same group (all Master). Their power is the brewed power (average of the two
potions mixed), so Darkness at 100 needs strong reagents or a high Alchemy skill.

### 9.2 Reagents and the Endless Potion

- Reagent power: `floor(base * (bonus*0.25/20 + 1) + bonus*0.75)` plus 0.5 × Alchemy skill at Master or 1 × at GM,
  capped at 255 with the excess /2 added to the hidden Alchemy skill bonus (AL:601-632). `bonus` (the reagent's
  `Bonus`) = `floor(partyLevel/5)` for generated reagents (AL:641-651). It is applied by rewriting the item table's
  `Mod1DiceCount` while the reagent is on the cursor.
- Monster reagent drops (AL:654-704): party Alchemy Master 1 %, GM 2 % per kill; tier
  `round(clamp(baseLevel/20 * (U/2 + 1.75), 1, 5))` from the unbolstered table level; `Bonus = round(partyLevel/2)`;
  if `Bonus + skill*mastery/2 > 200` the drop becomes a ready potion 221-224 of that power. Unseeded.
- With any GM alchemist: 0.2 % per kill an Endless Potion with `BonusStrength = min(best skill + 10, 100)`.

### 9.3 Charges

`potionUsingCharges` (AL:283): 228-235, 237, 240-242, 245, 247-251, 257, 263 have 5 uses (§3.14 encoding). The
Endless Potion recharges only the eight listed in §3.14.

### 9.4 Collisions with OpenYAMM's hard-coded potion ids

`game/items/InventoryItemMixingRuntime.cpp:19-26` fixes vanilla potion ids for item-target actions. MAW reuses those
ids for different potions:

| Id | OpenYAMM action today | MAW potion |
|---|---|---|
| 233 | Recharge wand | Regeneration (drinkable, 5 charges) |
| 236 | Harden Item | Harden Item (same) |
| 246-250 | Flaming, Freezing, Noxious, Shocking, Swift weapon coatings | Divine Restoration, Divine Cure, Divine Magic, Elemental Resistance, Self Resistance |
| 263 | Dragon Slaying coating | Divine Resistance |

Under MAW these must come from ruleset data (`potion_effects.yml` / `crafting_items.yml` item-target operations), not
from constants, or MAW's Regeneration potion would recharge wands.

---------------------------------------------------------------------------------------------------------------------

## 10. MAW bugs and oddities in this area

Each needs a decision (fix and record a deviation, or keep):

1. Hourglass preview drift (§7.3).
2. Eye preview shown only with enchant 1, apply works on blank items (§7.1).
3. Pearl, Lesser Element and Greater Element unseeded (§3.10, §4).
4. Crafting performed by building a tooltip; may apply to shop or chest items (§2.2).
5. Crafting reads the live item table: 2H axes lose their ×2 cap when a Minotaur is current; hat caps ignore ×1.5
   (§3.2).
6. Pandora's Cube accepted and wasted on rings and amulets (§3.7).
7. Oracle's Orb imprint silently destroys an existing affix (§3.11).
8. Mirror copies artifacts despite the README; the copy loses its identified flag (§3.8).
9. Emerald closes the house screen; its weapon power formula is off by `(count−1)/2` (§3.9).
10. Emerald of Power unsellable because of LOD Material 3 (§3.1).
11. Doom caps one point high from a floating-point `ceil` (§3.3).
12. U merges only one triple per confirmation, lowest tier, loaded backpacks only (§3.4).
13. Dimension map kill drops never have 2 affixes (§5).
14. Level checks use the current character, not the wearer (§3.2).
15. Gem cooldown after orb use and several silent failures (§2.3, §3.15).
16. Shop substitution limited to house ids ≤ 110, which includes one alchemist only (§6.2).
17. The "Item Bonus Power X/255" line shows the hard cap, not the cube cap (§3.13).
18. Oracle's Orb tooltip concatenates a nil affix text when empty (§3.11).

---------------------------------------------------------------------------------------------------------------------

## 11. Corrections to existing docs

These documents were not edited; the corrections are listed here.

**[ITEMS.md](ITEMS.md)**

- §1.11 and §3.2: shop gem tier is `1 + floor(P/25)` (+1 at 25 %, +2 at 5 %), capped at 16, not `floor(P/25)`. P is
  `getPartyLevel(4)`, the banked levels of continents 1-3.
- §1.11: "a reagent (EquipStat 19)" is the "Gem" class (MM8 valuable gems such as Zircon 177); reagents are EquipStat
  13. "Misc shops (house ≤ 110)" are weapon, armour and magic shops plus the first alchemist (110); only magic shops
  and that alchemist stock non-equipment.
- §3.1: the 60-frame cooldown is set only by the two orbs, which are Path A items; it protects orb extraction, not
  repeated tooltip builds. The Crafting Cube, Endless Potion and map uses have no cooldown (they are consumed).
- §3.2 gem row: Doom's PrimordialMax is 139 (floating-point `ceil(100*1.1) = 111`), not 138. The weaker enchant is
  chosen relative to its own cap. The level check uses the current character.
- §3.2 table: 1067's item name is "Orb of Creation"; only its texts say "Oracle's Orb".
- §3.2 Pandora row: also accepts helms, belts, cloaks, gauntlets, boots, rings and amulets (the last two wastefully).
- §3.2 Mirror row: the copy does not keep `Condition`, so it is unidentified.
- §3.2 map paragraph: the Emerald adds 5 map **power**, which is +50 monster levels, not +5 map level. The Eye and
  Hourglass unlock an affix only on maps with 1-3 active affixes.
- §3.2 U key: one triple per confirmation, lowest eligible tier, only loaded backpacks, result on the cursor.
- §3.5: the boss multiplier applies to `220 <= NameId < 300` (the loot code's boss range is 221-300 or 160). Gem
  drops have no pity. Pity counters grow by `round(bonusRoll)`, so monsters below level 2.5 never accumulate pity.
- §3.5: Endless Potion `BonusStrength` is `min(best Alchemy skill + 10, 100)` and it needs any GM alchemist.
- §2 (Charges row): potions use `Charges` as remaining uses + 1 (0 = fresh = 5 uses).

**[SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md)**

- §5.2: the crafting rows are pot ids 71-102 (99 is the Endless Potion, with no effect function; 100-102 duplicate
  1067-1069).
- §5.4: the Endless Potion recharges only 8 of the 20 charge potions (231, 232, 233, 237, 245, 251, 257, 263).
- §5.5: the Endless Potion's 0.2 % drop gives `BonusStrength = min(skill + 10, 100)`, which is the number of charges
  it adds, not a potion power.
- §5.7 item 6: the crafting effect ids are `evt.PotionEffects[71..98]`; the Crafting Cube and Endless Potion are not
  potion effects at all but the tooltip path.

**[COMBAT.md](COMBAT.md)** §5 (map completion): "or a reward by affix count for dimension maps" only happens in
Madness; outside Madness a completed dimension map gives a new map item (when the quest is done) and no crafting item.
The gem tier cap ("max") is 16.

**[README.md](README.md)** §2.4: "Holding ALT previews the predetermined result" applies to the Eye, Hourglass and
Enchant Item only; the Pearl and element potions are random. §6 "Eye and Hourglass notes state requirements the code
does not check" is right; add that the Hourglass preview drift also affects enchant 1 = HP (§7.3), not only an HP/SP
result.

---------------------------------------------------------------------------------------------------------------------

## 12. Not covered

- Exact seeded outcomes (which special an Eye gives a specific item): LuaJIT's generator was not emulated.
- In-game verification of: the tooltip path applying to shop or chest items; whether paperdoll (equipped) items reach
  the potion-on-item hook; the native Harden Item behaviour; how the engine parses the placeholder EquipStat "0" of
  rows 1041-1050 and 1068-1070.
- The visual glow sprite and sound 12070's content.
- `MAW 5.0 Loot Guide.pdf` (image only) was not re-read for crafting tables; ITEMS.md read it for rarity odds.
- Multiplayer: drops divided by players in game; host authority for crafting was not traced.
- The value and sell-price formulas for equipment after crafting (ITEMS.md §1.10 covers them).
- Older-save migrations of crafting fields (legacy rarity values, the "ascended" gem flag).
