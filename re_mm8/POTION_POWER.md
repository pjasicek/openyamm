# Potion power in original MM8

Checked on 2026-10-21 in `mm8_orig/MM8-Rel.exe` (SHA-256 `5326d564…`, see the [Rizin guide](RIZIN_GUIDE.md)) by
reading the disassembly; Ghidra decompilation was not available. Addresses are `MM8-Rel.exe` addresses, not those of
MMExtension's patched `mm8.exe`. A potion's power is the item record's `+0x04` field (MMExtension `Bonus`);
OpenYAMM keeps it in `InventoryItem::standardEnchantPower`.

## Where a potion gets its power

| Source | Power | Evidence |
|---|---|---|
| Random item generation (`GenerateItem`, `0x4552ca`) | 2d4 × treasure level, for every Bottle-type item except the empty bottle (220) | rolls at `0x455520`–`0x45564b` |
| Item on an indoor or outdoor map with power 0 | `rand % 15 + 5` (5–19) | indoor loader `0x45fd07`, outdoor loader `0x480544` |
| Item carried by a monster | `2 * (rand % 4) + 2` (2–8) | monster loot `0x425804`; the monster's random treasure goes through `GenerateItem` (`0x425905`) |
| Chest contents | no fix-up; random entries use `GenerateItem` (`0x44ee31`) | first-open routine `0x41fd30` fills only wand charges and gold |
| Alchemist special stock | `GenerateItem` type 44 (potions), so 2d4 × shop level | `0x4b99e4`; standard stock is empty bottles and reagents |
| Script `evt.GiveItem` | `GenerateItem(strength, type)` and then the id is replaced | opcode 0x29 at `0x44641a` |

Every potion placed in the MM6–MM8 maps and fixed chests stores power 0. OpenYAMM gives the fixed chest potions the
map rule (5–19), as MM7 does, since MM8 would leave them at 0.

## Drinking (`0x467aa9`, switch `0x4680fc`)

Power is used as stored, with no clamp to 1. Every timed potion lasts 30 minutes × power. Buffs go through the
player-buff `Apply` (`0x4571f2`), which replaces a buff only when the new one expires later.

| Potion | Effect |
|---|---|
| Cure Wounds / Magic Potion | power + 10 hit points / spell points |
| Divine Cure / Divine Power | 5 × power hit points / spell points |
| Haste, Heroism, Bless, Stoneskin, Water Breathing | player buff of fixed strength 5, Master; Haste does nothing when the drinker is Weak |
| Preservation, Shield, stat boosts, Luck Boost, the six resistances | player buff of strength 3 × power |
| Rejuvenation | age bonus reset to 0 |

The inspect popup (`0x41d549`, `0x41dac7`) prints "Power: N" for a Bottle only when power is not 0. Potion power does
not change the item's value (`0x4550e5`). Mixing a reagent into a bottle gives reagent power plus skill
(`0x415e0f`); mixing two potions gives their truncated average (`0x4160e3`).

## MMerge on top

`Scripts/Global/ExtraPotions.lua` handles the merged extra potions. Rejuvenation lowers a non-positive age bonus by
ceil(power / 10), otherwise the original reset runs. Divine Boost and Divine Protection give every temporary stat or
resistance 3 × power for 30 × power minutes. Protection from Magic is the only effect that clamps power to at least 1.
MMerge does not change how potion power is generated.
