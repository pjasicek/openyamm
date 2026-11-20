# Rule differences between MM6, MM7 and MM8

Status: investigation (2026-10-22). Part of the [vanilla mode investigation](README.md). Spells have their own page:
[SPELLS.md](SPELLS.md).

Everything here comes from local references. "Unverified" marks what could not be confirmed locally. Counts from
MMExtension are engine array sizes (`mmv(MM6, MM7, MM8)`), not data-file row counts.

Source shorthand:
- **CAB:** `reference/MMExtension/Scripts/Core/ConstAndBits.lua`
- **S00 / S01:** `reference/MMExtension/Scripts/Structs/00 structs.lua` / `01 common structs.lua`
- **OE:** `reference/OpenEnroth-git/src/Engine/` (MM7)
- **M8:** `re_mm8/mm8_orig/Data/Tables/` (original MM8)
- **MG:** `reference/mmmerge/Scripts/`
- **MD:** `reference/mmerge_data_forus/Data/Tables/`

## Overview

| Rule | MM6 | MM7 | MM8 |
|---|---|---|---|
| Classes | 6 kinds × 3 tiers = 18 | 9 kinds × 4 (base, tier 2, Light or Dark tier 3) = 36 | 8 kinds × 2 = 16 |
| Races | none (class kind only; unverified) | Human, Elf, Goblin, Dwarf | implied by class |
| Skills | 31 | 37 | 39 |
| Masteries | Normal, Expert, Master | + Grandmaster | + Grandmaster |
| Resistances | Fire, Cold, Electricity, Poison, Magic | Fire, Air, Water, Earth, Spirit, Mind, Body | same as MM7 |
| Conditions | 17 | 18 (+ Zombie) | 18 |
| Party | 4 created | 4 created | 1 created, up to 5 active from a roster of 50 (unverified that it starts with exactly 1) |
| Hirelings | 2 (78 professions) | 2 (59 professions) | none |
| Arcomage | none | 87 cards | 102 cards |
| Alchemy | potion mixing, no Alchemy skill | Alchemy skill, reagents 200-219, potions 221-271 | as MM7 |
| Items | 581 | 800 | 803 |
| Monsters | 174 | 265 | 268 |
| Spells | 99 | 99 | 99 + 33 racial slots |
| Calendar starts | 1165 | 1168 | 1172 |

## Classes and promotions

- **MM6** (CAB:697-717): six kinds, each linear through three tiers (the linear graph is unverified beyond the
  enum order).
  - Knight, Cavalier, Champion
  - Cleric, Priest, High Priest
  - Sorcerer, Wizard, ArchMage
  - Paladin, Crusader, Hero
  - Archer, BattleMage, WarriorMage
  - Druid, GreatDruid, ArchDruid
- **MM7** (CAB:718-756): Knight, Thief, Monk, Paladin, Archer, Ranger, Cleric, Druid and Sorcerer. Each promotes to
  tier 2 and then to a Light or Dark tier 3 (OE `Objects/CharacterEnumFunctions.h:140-176`).
- **MM8** (CAB:757-776): Necromancer/Lich, Cleric/Priest of Light, Knight/Champion, Troll/War Troll,
  Minotaur/Minotaur Lord, Dark Elf/Patriarch, Vampire/Nosferatu and Dragon/Great Wyrm. One promotion each.
- **HP and SP.** Base and factor per kind in MM6 and MM7 (S00:1083-1121); everything per class in MM8 (S00:1140-1153;
  M8 `Class HP SP.txt`, e.g. Dragon 50/10/50/5 on Intellect, Knight 35/5 with no SP).

## Races and starting stats

- **MM6:** no race constant; starting stats per class kind (S00:1096).
- **MM7:** starting stats per race (S00:1123-1127; OE `Objects/Character.cpp:72-110`); a 50-point bonus pool at
  creation (`Character.cpp:243-245`).
- **MM8:** starting stats per class (M8 `Class Starting Stats.txt`, e.g. Troll Might 14/35).

## Skills

- **MM6** (CAB:446-479).
  - Has: 7 weapons including Blaster; Shield, Leather, Chain, Plate; 9 magic schools; Identify Item, Merchant,
    Repair, Bodybuilding, Meditation, Perception, Diplomacy, Thievery, Disarm Traps, Learning.
  - Does not have: Dodging, Unarmed, Identify Monster, Armsmaster, Stealing, Alchemy or Club.
  - Thievery is unused (GrayFace's MM6 patch readme). Diplomacy usage is unverified.
  - No per-class caps table: each kind has StartingSkills codes (0 not available, 1 given, 2 choosable, 3 learnable;
    S00:1097-1100). Every learnable skill reaching Master is unverified.
- **MM7** (CAB:480-519).
  - Adds Dodging, Unarmed, Identify Monster, Armsmaster, Stealing and Alchemy.
  - Diplomacy and Thievery are unused (OE `Objects/CharacterEnums.h:238-239`). Club is a hidden skill.
  - Caps: 36 classes × 37 skills (OE `mm7_data.cpp:900`).
- **MM8** (CAB:520-561).
  - Removes Diplomacy and Thievery. Adds Dark Elf, Vampire and Dragon abilities and Regeneration.
  - In the original class table nobody can learn Blaster, Dodging, Unarmed or Stealing, and Dragons have no
    weapon or armour skills (M8 `Class Skills.txt`).
  - Base skill limit 60, base plus bonus 63.

## Light and Dark magic

- **MM6:** unverified locally. MMerge's MM6-style High Priest and Master Wizard have both at Master, but that is
  MMerge's version.
- **MM7:** chosen at the final promotion and mutually exclusive (OE `mm7_data.cpp`).
  - Priest of the Sun and ArchMage: Light at Grandmaster. Priest of the Moon and Lich: Dark at Grandmaster.
  - Hero and Master Archer: Light at Novice. Villain and Sniper: Dark at Novice.
  - No Light or Dark at party creation.
- **MM8:** Light only for Cleric (Master) and Priest of Light (Grandmaster); Dark only for Necromancer (Master) and
  Lich (Grandmaster).

## Damage, resistances and conditions

- **Damage kinds:** MM6 Physical, Magic, Fire, Electricity, Cold, Poison, Energy. MM7/MM8 Fire through Dark, plus
  Energy 12; MM8 adds Dragon 50 (CAB:668-694).
- **Monster immunity value:** 200 in MM6/MM7, 65000 in MM8 (CAB:237-241).
- **Conditions:** 17 in MM6 (ending with Eradicated); MM7/MM8 add Zombie (CAB:569-592).
- **Stats:** the seven primary stats are the same in all three.

## Party, hirelings and recruitment

- **MM6/MM7:** 4 members, 2 hireling slots, an NPC profession table (S00:1224-1236, 562-566).
- **MM8:** a roster of 50 with 5 active slots (S00:1240-1243). No hirelings and no profession table.
- **Portrait limits:** 12, 25, 30.

## Arcomage, alchemy and items

- **Arcomage:** none in MM6; 87 card kinds in MM7, 102 in MM8 (S01:3206).
- **Potions:** MM6 mix matrix ids 160-188 and no Alchemy skill; house type 4 is "General Store" rather than
  "Alchemist" (CAB:1424). MM7/MM8 use ids 222-271 with reagents (OE `Objects/ItemEnums.h:355-426`).
- **Item tables:** 581 / 800 / 803 items, 14 / 24 / 24 standard enchants, 59 / 72 / 72 special enchants (S00:301-303).
  MM7 artifacts are 500-552 (spawnable 500-528). MM6 and MM8 artifact ranges are unverified.
- **Monster kinds and targeting** differ per game (CAB:187-265).

## Other constants

| Constant | MM6 | MM7 | MM8 |
|---|---|---|---|
| Party buffs | 16 | 20 | 20 |
| Character buffs | 16 | 24 | 27 (Glamour, Levitate, Mistform) |
| Guild join costs | 17 | 11 | 11 |
| Transport locations | 36 | 35 | 25 |
| Awards | 87 | 104 | 104 |
| NPC data | 400 | 501 | 551 |
| Map stats | 100 | 77 | 77 |

- **House types:** MM6 has General Store, Element Guild, Thieves Guild and Oracle; MM7 has good and evil Seers.
- **Blaster:** MMExtension needs a script to make Blasters shoot in MM8. That vanilla MM8 Blaster handling is broken
  is unverified.

## What MMerge changed relative to MM8

MMerge runs on the MM8 engine. Its changes fall into fixes, which vanilla mode might keep (open question 3 in the
README), and additions, which it drops. The split below is a first guess.

**Likely fixes:**
- Fire Spikes and Shield (MG `General/SpellsTweaks.lua`).
- Dragon attack and armour class bonuses (`MiscTweaks.lua:570-626`).
- Blaster in MM8.
- Bounty hunts working in MM8 the way they did in MM6/MM7 (`BountyHunt.lua:220`).

**Additions:**
- **Classes and races.**
  - 53 class slots laid out MM7-style, plus Dark Archmage, Peasant, High Priest and Master Wizard
    (`MiscTweaks.lua:303-357`).
  - 11 races with racial skill modifiers (`Structs/RacialSkills.lua`, MD `Race Skills.txt`) and racial resistances
    and immunities (`MiscTweaks.lua:22-33, 672-702`).
- **Party.**
  - Party creation of 1-5 characters with continent-dependent choices (`MenuChooseCharacter.lua`).
  - Mercenaries at inns (`NPCMercenaries.lua`).
  - MM6/MM7-style followers in the MM8 engine (`NPCFollowers.lua`).
  - Reputation, beg, threaten and bribe topics (`Global/Reputation.lua`).
- **Skills.**
  - Blaster at Grandmaster for every class.
  - Dodging, Unarmed and Stealing re-enabled. Stealing works on monsters too (`Stealing.lua`).
  - Skill limits raised to 80 and 255 (`Structs/After/RemoveSkillValueLimits.lua`).
  - Extra teachers: temples teach Unarmed, Dodging, Regeneration and Merchant; single-school guilds teach Learning
    or Meditation (`MiscTweaks.lua:718-754`).
- **Light and Dark.** MM7-style paths on Antagarich and Enroth, a quest to switch path
  (`Quest_EnrothDarkArts.lua`), and Enroth Grandmaster quests.
- **Formulas.**
  - Regeneration works as in MM7.
  - Meditation gives flat SP regeneration, and classes without SP get linear SP from Meditation
    (`MiscTweaks.lua:636-670, 731-739`).
- **Spells** (`SpellsTweaks.lua`).
  - A new success formula for Slow, Mass Distortion and Stun; Stun paralyses.
  - Town Portal: always works at Grandmaster; at Master only when no enemies are near.
  - Control Undead reworked.
  - Monster changes: Power Cure heals nearby monsters, monsters cast Sunray instead of Paralyze, and Deadly Swarm
    and Flying Fist are enabled for monsters.
- **Playable Zombie condition** (`ZombiePlayers.lua`).
- **Monsters and world.**
  - Monster bolster (`AdaptiveMonstersStats.lua`).
  - Arena travel costs 4 days and no food.
  - Changed turn-based movement speed.
- **Items.**
  - 4 extra quick-spell slots.
  - Usable items (`UsableItems.lua`).
  - Extra potions (`Global/ExtraPotions.lua`).
  - Alchemy catalysts add their powers together; a catalyst of power 70+ becomes a Philosopher's Stone via
    Enchant Item.

## What each vanilla ruleset needs

| Ruleset | Needs |
|---|---|
| MM8 | The original M8 class, skill, HP/SP and starting-stat tables; 39 skills; 5 of 50 party; no hirelings; MM8 spell table and damage; drop MMerge additions |
| MM7 | 36 classes and 4 races; 37 skills; Grandmaster caps table (OpenEnroth has one); party of 4 and 2 hirelings; MM7 Light/Dark promotion; Arcomage with 87 cards; MM7 spell table and damage |
| MM6 | 18 classes; 31 skills with no Grandmaster; 5 resistances and 7 damage kinds; 17 conditions; party of 4 and 2 hirelings; no Arcomage; MM6 potion mixing; 581-item table; MM6 spells, including 23 new effects |

Source tables for MM7 and MM6 are the main gap: see
[CONTENT_PROVENANCE.md](CONTENT_PROVENANCE.md#original-data-available-locally).
