# Spells in MM6, MM7 and MM8

Status: reference (2026-10-22). Part of the [vanilla mode investigation](README.md).

## Sources

- Spell ids and names per game: GrayFace's `const.Spells`, which branches on `mmver`
  (`reference/MMExtension/Scripts/Core/ConstAndBits.lua:1636-1870`).
- MM7 costs, recovery and damage: OpenEnroth's table (`reference/OpenEnroth-git/src/Engine/Spells/Spells.cpp:193`).
  OpenEnroth names spell 68 `FIRST_AID`; MMExtension and the MM8 table call the MM7/MM8 spell Heal.
- MM8 costs and damage: the original `re_mm8/mm8_orig/Data/Tables/Spells2.txt` and `Spells.txt` from
  `re_mm8/mm8_orig/Data/EnglishT.lod`.
- MM6 costs and damage: **not verified**. No original MM6 spell table exists locally, and the Might and Magic fandom
  wiki refuses automated fetches.

OpenYAMM's `assets_dev/engine/data_tables/spells.txt` is the MMerge table, which uses the MM8 layout. So is
`assets_dev/worlds/mm6/_legacy/tables/Spells.txt`; it is not the original MM6 table.

## Structure

- All three games have 9 schools of 11 spells with the same id ranges: Fire 1-11, Air 12-22, Water 23-33,
  Earth 34-44, Spirit 45-55, Mind 56-66, Body 67-77, Light 78-88, Dark 89-99.
- MM6 has Normal, Expert and Master ranks. MM7 added Grandmaster.
- MM8 adds racial ability books: Dark Elf 100-103, Vampire 111-114 and Dragon 122-125 (the other slots in 100-132
  are unused).
- MM6 and MM7 use ids 100-102 for shooting (arrow, fire arrow, blaster). MM8 moves them to 133-137.

## Full list by slot

"=" means the same as the column to the left. **Bold** marks a change from MM6, or in the MM8 column a change from MM7.

| # | MM6 | MM7 | MM8 |
|---|---|---|---|
| **Fire** ||||
| 1 | Torch Light | = | = |
| 2 | Flame Arrow | **Fire Bolt** | = |
| 3 | Protection from Fire | **Fire Resistance** | = |
| 4 | Fire Bolt | **Fire Aura** | = |
| 5 | Haste | = | = |
| 6 | Fireball | = | = |
| 7 | Ring of Fire | **Fire Spike** | = |
| 8 | Fire Blast | **Immolation** | = |
| 9 | Meteor Shower | = | = |
| 10 | Inferno | = | = |
| 11 | Incinerate | = | = |
| **Air** ||||
| 12 | Wizard Eye | = | = |
| 13 | Static Charge | **Feather Fall** | = |
| 14 | Protection from Electricity | **Air Resistance** | = |
| 15 | Sparks | = | = |
| 16 | Feather Fall | **Jump** | = |
| 17 | Shield | = | = |
| 18 | Lightning Bolt | = | = |
| 19 | Jump | **Invisibility** | = |
| 20 | Implosion | = | = |
| 21 | Fly | = | = |
| 22 | Starburst | = | = |
| **Water** ||||
| 23 | Awaken | = | = |
| 24 | Cold Beam | **Poison Spray** | = |
| 25 | Protection from Cold | **Water Resistance** | = |
| 26 | Poison Spray | **Ice Bolt** | = |
| 27 | Water Walk | = | = |
| 28 | Ice Bolt | **Recharge Item** | = |
| 29 | Enchant Item | **Acid Burst** | = |
| 30 | Acid Burst | **Enchant Item** | = |
| 31 | Town Portal | = | = |
| 32 | Ice Blast | = | = |
| 33 | Lloyd's Beacon | = | = |
| **Earth** ||||
| 34 | Stun | = | = |
| 35 | Magic Arrow | **Slow** | = |
| 36 | Protection from Magic | **Earth Resistance** | = |
| 37 | Deadly Swarm | = | = |
| 38 | Stone Skin | = | = |
| 39 | Blades | = | = |
| 40 | Stone to Flesh | = | = |
| 41 | Rock Blast | = | = |
| 42 | Turn to Stone | **Telekinesis** | = |
| 43 | Death Blossom | = | = |
| 44 | Mass Distortion | = | = |
| **Spirit** ||||
| 45 | Spirit Arrow | **Detect Life** | = |
| 46 | Bless | = | = |
| 47 | Healing Touch | **Fate** | = |
| 48 | Lucky Day | **Turn Undead** | = |
| 49 | Remove Curse | = | = |
| 50 | Guardian Angel | **Preservation** | = |
| 51 | Heroism | = | = |
| 52 | Turn Undead | **Spirit Lash** | = |
| 53 | Raise Dead | = | = |
| 54 | Shared Life | = | = |
| 55 | Resurrection | = | = |
| **Mind** ||||
| 56 | Meditation | **Remove Fear** | **Telepathy** |
| 57 | Remove Fear | **Mind Blast** | **Remove Fear** |
| 58 | Mind Blast | **Mind Resistance** | = |
| 59 | Precision | **Telepathy** | **Mind Blast** |
| 60 | Cure Paralysis | **Charm** | = |
| 61 | Charm | **Cure Paralysis** | = |
| 62 | Mass Fear | **Berserk** | = |
| 63 | Feeblemind | **Mass Fear** | = |
| 64 | Cure Insanity | = | = |
| 65 | Psychic Shock | = | = |
| 66 | Telekinesis | **Enslave** | = |
| **Body** ||||
| 67 | Cure Weakness | = | = |
| 68 | First Aid | **Heal** | = |
| 69 | Protection from Poison | **Body Resistance** | = |
| 70 | Harm | = | = |
| 71 | Cure Wounds | **Regeneration** | = |
| 72 | Cure Poison | = | = |
| 73 | Speed | **Hammerhands** | = |
| 74 | Cure Disease | = | = |
| 75 | Power | **Protection from Magic** | = |
| 76 | Flying Fist | = | = |
| 77 | Power Cure | = | = |
| **Light** ||||
| 78 | Create Food | **Light Bolt** | = |
| 79 | Golden Touch | **Destroy Undead** | = |
| 80 | Dispel Magic | = | = |
| 81 | Slow | **Paralyze** | = |
| 82 | Destroy Undead | **Summon Elemental** | **Summon Wisp** |
| 83 | Day of the Gods | = | = |
| 84 | Prismatic Light | = | = |
| 85 | Hour of Power | **Day of Protection** | = |
| 86 | Paralyze | **Hour of Power** | = |
| 87 | Sun Ray | Sunray (spelling only) | = |
| 88 | Divine Intervention | = | = |
| **Dark** ||||
| 89 | Reanimate | = | = |
| 90 | Toxic Cloud | = | = |
| 91 | Mass Curse | **Vampiric Weapon** | = |
| 92 | Shrapmetal | **Shrinking Ray** | = |
| 93 | Shrinking Ray | **Shrapmetal** | = |
| 94 | Day of Protection | **Control Undead** | = |
| 95 | Finger of Death | **Pain Reflection** | = |
| 96 | Moon Ray | **Sacrifice** | **Dark Grasp** |
| 97 | Dragon Breath | = | = |
| 98 | Armageddon | = | = |
| 99 | Dark Containment | **Souldrinker** | = |

## MM6 compared with MM7

- **Same name and slot (49).** Every "=" in the MM7 column, counting Sun Ray/Sunray.
- **Same spell, different slot (22).** Fire Bolt, Feather Fall, Jump, Poison Spray, Ice Bolt, Enchant Item,
  Acid Burst, Turn Undead, Remove Fear, Mind Blast, Charm, Cure Paralysis, Mass Fear, Destroy Undead, Paralyze,
  Hour of Power, Shrinking Ray and Shrapmetal. Four of them also changed school:
  - Telekinesis: Mind to Earth.
  - Protection from Magic: Earth to Body.
  - Slow: Light to Earth.
  - Day of Protection: Dark to Light.
- **Renamed (5).** Protection from Fire, Electricity, Cold and Poison became Fire, Air, Water and Body Resistance,
  because the resistance set changed. First Aid became Heal.
- **Only in MM6 (23).** Flame Arrow, Ring of Fire, Fire Blast, Static Charge, Cold Beam, Magic Arrow,
  Turn to Stone, Spirit Arrow, Healing Touch, Lucky Day, Guardian Angel, Meditation, Precision, Feeblemind,
  Cure Wounds, Speed, Power, Create Food, Golden Touch, Mass Curse, Finger of Death, Moon Ray, Dark Containment.
- **New in MM7 (23).** Fire Aura, Fire Spike, Immolation, Invisibility, Recharge Item, Earth Resistance,
  Detect Life, Fate, Preservation, Spirit Lash, Telepathy, Mind Resistance, Berserk, Enslave, Regeneration,
  Hammerhands, Light Bolt, Summon Elemental, Vampiric Weapon, Control Undead, Pain Reflection, Sacrifice,
  Souldrinker.

## MM7 compared with MM8

- **Replaced spells.**
  - Summon Elemental became Summon Wisp (up to 5 wisps at Grandmaster).
  - Sacrifice became Dark Grasp: the target can't cast or shoot, is slowed, and has its armour class and melee
    damage halved. Recovery is 120 instead of Sacrifice's 200/150.
- **Mind reorder.** Telepathy moved to slot 56 and costs 1 SP instead of 4. Remove Fear moved to 57. Mind Blast
  moved to 59 and costs 4 SP instead of 2.
- **Damage rebalance** (MM7 value from OpenEnroth's table, MM8 value from the MM8 description):

  | Spell | MM7 | MM8 |
  |---|---|---|
  | Meteor Shower (per meteor) | 1-8 per skill point | 8 + 1 per skill point |
  | Inferno | 12 + 1 per skill point | 12 + 2 per skill point |
  | Ice Blast (per shard) | 12 + 1-3 per skill point | 12 + 1-6 per skill point |
  | Rock Blast | 1-8 per skill point | 10 + 1-10 per skill point |
  | Flying Fist | 30 + 1-5 per skill point | 20 + 1-10 per skill point |
  | Shrapmetal (per piece) | 6 + 1-6 per skill point | 1-6 per skill point |

- **Everything else** has the same cost and recovery in both games.
- **Racial ability books (MM8 only).**
  - Dark Elf: Glamour, Travelers' Boon, Blind, Darkfire Bolt.
  - Vampire: Lifedrain, Levitate, Charm, Mistform.
  - Dragon: Fear, Flame Blast, Flight, Wing Buffet.

## What this means for vanilla mode

- **Vanilla MM7 and MM8** can share one spell implementation; they need a per-ruleset table and the few changed
  formulas.
- **Vanilla MM6 needs 23 spells we don't implement.** Most need a new effect (Ring of Fire, Fire Blast,
  Static Charge, Guardian Angel, Lucky Day, Precision, Meditation, Feeblemind, Speed, Power, Create Food,
  Golden Touch, Mass Curse, Finger of Death, Moon Ray, Dark Containment and others). MM6 also needs a different
  id-to-spell mapping, its own resistance set for the protection spells, and no Grandmaster rank.
- **MM6 events that cast spells** by id (for example Flame Arrow in `D08`/`D09`, see
  `reference/mmext-scripts/Decompiled_Scripts/mm6orig/txt/`) need ids for the active ruleset.
