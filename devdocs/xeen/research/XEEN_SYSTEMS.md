# World of Xeen: systems data for an MM6–MM8-style world

Research for the Xeen world design (monsters, items, classes, skills, spells, wells, guilds, pacing). Story, quests and
geography are covered by the other research notes in this folder. Written 2026-11-12.

**Sources and how each number was obtained**

| Data | Source | Confidence |
| --- | --- | --- |
| Monster stats (185 rows) | Decoded from the binary tables `raw/dark/xeen.mon` (90 rows, Clouds) and `raw/dark/dark.mon` (95 rows, Darkside) in `reference/mm4_5_world_of_xeen/unpacked/`; 60-byte records, layout from ScummVM `engines/mm/xeen/map.cpp` `MonsterStruct::synchronize` | Exact (original data) |
| Placements | `maps/{xeen,dark}_initial_state/maze*.mob.json` monster lists through each map's sprite table; Clouds maps read `xeen.mon`, Darkside maps `dark.mon` except Dragon Tower 1–4 and Dungeon of Death 4 (ids 117–120, 124), which read `xeen.mon` (ScummVM `Map::load`) | Exact; event spawns not counted |
| Monster mechanics | ScummVM `combat.cpp` (damage = strikes × d(dmgPerStrike), party hit roll against monster AC + 10, XP split over living members, Darkside XP ×2 below level 15 in World of Xeen) | ScummVM reading |
| Item, material, class, race, spell constants | ScummVM `devtools/create_mm/create_xeen/constants.cpp`, `en_constants.h` (originally from XEEN.EXE); material names from `raw/dark/mae.xen`, spell names from `raw/dark/spells.xen` | Exact (tables) |
| Wells, teachers, guild fees | Map text `text/{xeen,dark}/aaze*.txt.json` (the line after a well's name is usually its effect) | Text; magnitude where the text says it |
| MM6–MM8 comparables | `assets_dev/engine/data_tables/monster_data.txt` (merged MMerge rows; ids below are its `#` column), `items.txt`, enchant tables, `map_stats.txt`; MM9 conventions from `devdocs/mm9_rework/BALANCE_PLAN.md`, `devdocs/LOOT_POOL.md`, `devdocs/MONSTER_MODIFIERS.md` | Exact |

ScummVM sources were only read, for the formats (a temporary download, not kept). The decoders were throwaway scripts;
re-derive from the record layout above (16-byte name, XP u32, HP u16, AC, speed, attacks, hated class, strikes u16,
die, damage type, special, hit chance, ranged, monster type, 7 resistances, pad, gold u16, gems, item level, flying,
image, loop, effect, fx, 9-byte sound name) if a tool needs the tables.

**Conventions.** Ids: `X<n>` = row n of `xeen.mon`, `D<n>` = row n of `dark.mon` (the id the maps use). Xeen
resistances are percentages in the order Fire/Elec/Cold/Poison(acid)/Energy/Magic/Physical. Flags: R ranged attack, A
hits the whole party (`hatesClass` 15: every attack is resolved against all six members, which is how breath, spell
volleys and swarms work), F flying. Loot: gold, gems, `T<n>` item treasure level 1–7 (`itemDrop`). `*` = unique or
boss row. `→L` is the proposed MM6–MM8 level (section 2). MM6–MM8 resistances are written in `monster_data.txt` order
Fire/Air/Water/Earth/Mind/Spirit/Body/Light/Dark/Phys. Family codes: GOB goblinoids and orcs, BRU brutes (ogres,
trolls, giants, minotaurs), HUM humans and dwarves, CAS casters, UND undead, BEA beasts, SER serpents and lizards, VER
vermin (oozes, insects, arachnids, plants), FLY flyers and eyes, GOL golems, constructs and robots, ELE elementals,
DEM demons, DRA dragons and hydras. Progression numbers for MM6–MM8 worlds are in
[MM678_CALIBRATION.md](MM678_CALIBRATION.md).

## 1. Xeen monsters (both sides)

How to read Xeen numbers against MM6–MM8:

- **HP is tiny and damage is huge** compared with MM6–MM8 (Clouds Fire Dragon: 350 HP, 200 fire damage to every
  member; MM Red Dragon L80: 880 HP, 12d8). Xeen parties are six and hit several times a round; never port HP or
  damage directly.
- **XP scales differ by side.** Darkside rows were tuned for Darkside played alone (Castleview Goblin 1,000 XP against
  the Clouds Goblin's 150) and World of Xeen doubles kill XP below level 15 there. Levels below are set by role,
  placement and stats, not by XP.
- **Speed** decides turn order only (Xeen is turn based); attacks per round (`2×`) and A/R flags matter more.
- **Recolour variants already exist**: many rows share one sprite (`imageNumber`), ready-made tiers. Clouds:
  Guardian/Yak Lich/Yak Master, Insect Swarm/Stingers, Skeleton/Spirit Bones, Mad Fool/Polter-Fool, Jouster/Ghost Rider,
  Giant Snake/Guardian Asp, Mad Dwarf/Clan Sargent, Harpy/Queen, Yang Knight/Captain Yang, Castle/King's Guard,
  Wizard/Cult Leader, Gnome Vampire/Count Draco, Darzog/Clone, Frost Dragon/Xeen's Pet. Darkside: Cleric of Mok/Mok
  Heretic/Cult Leader, Cloud/Phase/Mega Dragon, Green/Energy Dragon, Dragon Mummy/Scraps, Fire Blower/Lava
  Dweller/Barkman, Onyx/Sky Golem, Slayer/Death/Doom Knight, Mystic/Magic/Mega Mage, Minotaur/Gorgon, Power Lich/Sandro,
  Enchantress/Sorceress/Morgana, Rogue/Thief/Master Thief, the four trolls, Vampire/Royal Vampire, Vampire Lord/Ct.
  Blackfang/Vampire King, Witch/Coven Leader, Master Wizard/Xenoc, Wizard/Valio, Ogre/Graalg, Orc Shaman/Shaalth, Orc
  Guard/Elite, Sewer Rat/Rooka, Barbarian/Yog, Giant/Gurodel, Medusa Sprite/Sharla.
- **Art**: every row's `imageNumber` has a sprite in the extraction (`raw/xeen/NNN.mon` + `.att` for Clouds rows,
  `raw/dark/NNN.mon` for Darkside rows; PNG frames in `sprites/{xeen,dark}/`). They are reference art for HD masters,
  not installable models.
- Single "Beholder Bat ×1" records in Darkside towns and castles (Olympus, Castle Kalindra 1–3, Ellinger's Tower 1/4,
  Pyramid 2–4, Escape Pods) sit in maps whose monster table has only slot 0 filled; they look like placeholder records
  and are left out of "Placed".
- Rows with "events/none" are spawned by scripts or unused in the initial state.

| Fam | Id | Name | HP | AC | Damage | XP | Spd | Special | Res F/E/C/P/En/M/Ph | Fl | Loot | Placed (initial state) | →L |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GOB | D23 | Goblin | 10 | 5 | 2×2d6 Ph | 1,000 | 30 |  | – |  | – | Castleview×52 | 3 |
| GOB | X5 | Goblin | 20 | 6 | 1d12 Ph | 150 | 15 |  | – |  | 5g T1 | Witch Tw 2×18, Witch Tw 1×9, Witch Tw 4×3 | 4 |
| GOB | D25 | Gremlin | 20 | 7 | 2×2d10 Ph | 2,000 | 35 |  | – |  | – | Castleview×16 | 5 |
| GOB | X6 | Orc | 25 | 5 | 1d10 Ph | 200 | 17 |  | 50/50/50/0/0/0/0 | R | 10g T1 | Area F2×27, Area F3×12, Area E2×7 +1 | 6 |
| GOB | D26 | Gremlin Guard | 50 | 10 | 2×6d5 Ph | 3,000 | 35 |  | – |  | – | Castleview×27 | 8 |
| GOB | D40 | Orc Guard | 60 | 10 | 3d10 Ph | 5,000 | 20 |  | – |  | 50g T2 | Temple of Bark 1×26, Temple of Bark 2×17, Temple of Bark 3×14 | 12 |
| GOB | D70 | Gettlewaithe* | 100 | 15 | 2×5d5 Ph | 5,000 | 35 |  | – |  | 2000g T5 | Castleview×1 | 15 |
| GOB | D43 | Orc Shaman | 50 | 15 | 5d5 Cold | 10,000 | 30 | sleep | 0/0/0/0/0/10/0 | RA | 75g 10gm T2 | Temple of Bark 4×9, Temple of Bark 3×8, Temple of Bark 2×4 | 20 |
| GOB | D74 | Orc Elite | 200 | 15 | 2×5d10 Ph | 15,000 | 40 |  | – |  | 100g T3 | Temple of Bark 3×12, Temple of Bark 4×5 | 25 |
| GOB | D75 | Shaalth* | 300 | 15 | 5d10 Cold | 20,000 | 50 | sleep | 0/0/0/0/0/20/0 | A | 1000g 50gm T5 | Temple of Bark 4×26 | 30 |
| BRU | D56 | Troll Grunt | 100 | 5 | 2d25 Ph | 10,000 | 50 |  | 50/50/50/50/0/0/0 |  | – | Troll Holes×29 | 18 |
| BRU | D42 | Ogre | 100 | 15 | 4d10 Ph | 10,000 | 30 |  | – |  | 100g | Area D3×34, Area C3×7 | 20 |
| BRU | X32 | Ogre | 90 | 17 | 4d8 Ph | 6,000 | 15 |  | 40/40/40/40/0/0/0 | R | – | Area C2×10, Area B3×6, Area C3×4 | 20 |
| BRU | X34 | Swamp Thing | 130 | 23 | 2d30 Ph | 6,000 | 12 |  | 0/30/30/30/0/0/0 |  | – | Area C4×7, Area D4×3 | 26 |
| BRU | D81 | Troll Guard | 200 | 10 | 2d35 Ph | 15,000 | 60 |  | 50/50/50/50/0/0/0 |  | – | Troll Holes×19 | 28 |
| BRU | D84 | Graalg* | 200 | 15 | 5d10 Ph | 20,000 | 50 |  | – |  | 1000g T5 | Area D3×1 | 30 |
| BRU | X57 | Cyclops | 200 | 16 | 2×2d40 Ph | 10,000 | 28 | confuse | 0/0/0/0/0/20/0 |  | 1300g 5gm | Area A4×10 | 36 |
| BRU | D82 | Troll Chief | 300 | 15 | 2d50 Ph | 20,000 | 65 |  | 50/50/50/50/0/0/0 |  | – | Troll Holes×15 | 38 |
| BRU | X53 | Ice Troll | 125 | 15 | 2×3d15 Ph | 14,000 | 25 |  | 0/50/100/50/0/0/0 |  | – | Area B4×8, Burlock Dungeon×2 | 38 |
| BRU | D83 | Hobstadt* | 400 | 20 | 2d50 Ph | 25,000 | 70 |  | 50/50/50/50/0/0/0 |  | 1000g T4 | Troll Holes×1 | 42 |
| BRU | D22 | Giant | 500 | 25 | 2×100d5 Ph | 100,000 | 45 | unconscious | – |  | 1000g T5 | Area D1×16, Area B1×4, Area C1×3 | 50 |
| BRU | D37 | Minotaur | 3000 | 80 | 100d4 Ph | 250,000 | 120 | aging | 0/0/10/0/0/50/60 |  | – | Lost Souls Dungeon 2×25, Lost Souls Dungeon 5×22, Lost Souls Dungeon 1×12 +2 | 60 |
| BRU | D88 | Gurodel* | 750 | 30 | 2×100d6 Ph | 100,000 | 60 | unconscious | – |  | 5000g T6 | Area D1×1 | 60 |
| BRU | D38 | Gorgon | 4000 | 90 | 100d3 Ph | 250,000 | 100 | stone | 0/0/0/0/0/60/70 |  | – | Lost Souls Dungeon 5×14, Lost Souls Dungeon 3×5, Lost Souls Dungeon 4×2 | 65 |
| HUM | X12 | Insane Begger | 10 | 3 | 2d6 Mag | 450 | 20 | insane | 0/0/0/0/0/20/0 |  | 1g | Rivercity×41 | 5 |
| HUM | X7 | Mad Dwarf | 30 | 6 | 2×2d4 Ph | 200 | 17 |  | 50/50/50/50/50/0/0 |  | 75g 2gm T1 | Dwarf Mine 3×16, Deep Mine Alpha×16, Dwarf Mine 1×14 +5 | 7 |
| HUM | X10 | Mad Fool | 30 | 4 | 2×2d5 Ph | 350 | 21 | insane | 0/0/0/0/0/10/0 |  | T2 | C.Burlock 1×9, C.Burlock 3×6, Burlock Dungeon×5 +1 | 8 |
| HUM | X74 | Clan Sargent | 60 | 10 | 2×2d6 Ph | 600 | 20 |  | 50/50/50/50/50/0/0 |  | 120g 3gm T2 | Deep Mine Omega×5, Deep Mine Kappa×3, Deep Mine Alpha×2 +1 | 10 |
| HUM | D54 | Rogue | 50 | 10 | 1d60 Ph | 5,000 | 30 |  | – |  | 70g | Southern Tw 1×24, Southern Tw 2×11, Southern Tw 4×8 +1 | 12 |
| HUM | D6 | Barbarian | 50 | 5 | 3×1d20 Ph | 5,000 | 40 |  | – | R | 100g T3 | Area B3×32, Area A2×9, Area A3×3 +1 | 12 |
| HUM | X18 | Robber | 50 | 8 | 2×2d8 Ph | 900 | 23 |  | – | R | 200g T2 | Rivercity×26 | 12 |
| HUM | X75 | Clan King* | 120 | 12 | 8d1 Mag | 2,000 | 22 | sleep | 50/50/50/50/50/0/0 | RA | 500g 10gm T3 | Deep Mine Omega×1 | 16 |
| HUM | D55 | Thief | 100 | 15 | 1d100 Ph | 10,000 | 40 |  | – |  | 200g | Southern Tw 4×12, Southern Tw 2×3 | 18 |
| HUM | X80 | Robber Boss | 115 | 14 | 2×2d12 Ph | 5,000 | 27 |  | – |  | 400g T4 | Rivercity×6 | 20 |
| HUM | X24 | Ninja | 65 | 25 | 4×3d5 Ph | 2,000 | 35 |  | 20/20/20/20/20/20/0 | R | 50g T3 | Area B3×10, Area A3×6, Area D4×1 | 22 |
| HUM | D89 | Yog* | 100 | 5 | 1d30 Ph | 25,000 | 60 |  | – |  | 200g T4 | Area B3×1 | 25 |
| HUM | X29 | Jouster | 80 | 20 | 2d40 Ph | 5,000 | 25 |  | – |  | 2000g T3 | Area D2×7, Area C2×3 | 25 |
| HUM | X35 | Evil Ranger | 100 | 20 | 2×4d5 Ph | 7,000 | 27 | poison | 25/25/25/80/0/0/0 | R | 500g 5gm T3 | Area C4×11, Area C3×8, Area B3×2 | 28 |
| HUM | D78 | Master Thief* | 100 | 20 | 1d250 Ph | 20,000 | 50 |  | – |  | 250g 20gm T4 | Southern Tw 4×1 | 30 |
| HUM | X38 | Yang Knight | 120 | 30 | 4×3d15 Ph | 8,000 | 24 |  | 30/30/30/30/0/0/0 |  | 1200g T3 | Rivercity×12 | 30 |
| HUM | X43 | Evil Archer | 75 | 22 | 5×4d6 Elec | 10,000 | 35 |  | 20/80/20/20/20/0/0 | R | 300g 10gm T4 | Area B3×9, Area B4×6 | 30 |
| HUM | X45 | Barbarian | 200 | 15 | 2×6d10 Ph | 10,000 | 30 |  | 50/50/50/50/0/10/0 |  | 25g T4 | Area A3×10, Area B2×7, Area C2×4 | 32 |
| HUM | X46 | Castle Guard | 100 | 30 | 2×10d6 Ph | 10,000 | 28 |  | 10/10/10/10/10/10/0 |  | 40g | C.Burlock 1×20, Burlock Dungeon×4, C.Burlock 2×4 | 32 |
| HUM | X82 | Captain Yang* | 200 | 35 | 6×3d16 Ph | 25,000 | 30 |  | 50/50/50/50/0/0/0 |  | 2500g T5 | Rivercity×1 | 40 |
| HUM | X84 | King's Guard | 150 | 35 | 4×10d6 Cold | 10,000 | 30 |  | 20/20/20/20/20/20/0 | R | 100g T5 | C.Burlock 1×9, C.Burlock 3×5 | 40 |
| HUM | D30 | Slayer Knight | 500 | 30 | 2d250 Ph | 50,000 | 50 |  | 50/50/50/50/50/0/0 |  | 50g T5 | Northern Tw 3×10, Northern Tw 1×6, Northern Tw 2×4 +1 | 45 |
| HUM | D31 | Death Knight | 750 | 50 | 2×2d250 Ph | 100,000 | 80 |  | 50/50/50/50/50/10/0 |  | 100g T6 | Northern Tw 3×5, Northern Tw 2×3, Northern Tw 4×3 | 55 |
| HUM | D71 | Doom Knight* | 1000 | 50 | 4×2d250 Ph | 500,000 | 100 | death | 80/80/80/80/80/20/0 |  | 200g T7 | Northern Tw 4×1 | 75 |
| CAS | X14 | Wicked Witch | 50 | 9 | 2d2 Mag | 1,200 | 23 | curse item | 0/0/0/0/0/50/0 | RA | 5gm | Witch Tw 3×9, Witch Tw 4×6 | 14 |
| CAS | X17 | Cleric of Yak | 60 | 8 | 2d10 Elec | 1,600 | 18 |  | 20/60/20/20/0/0/0 | RA | 8gm T2 | Ancient Temple of Yak×20 | 16 |
| CAS | X76 | Head Witch* | 80 | 12 | 3d5 Mag | 5,000 | 25 | curse | 0/0/0/0/0/60/0 | RA | 10gm T4 | Witch Tw 4×1 | 22 |
| CAS | X25 | Yak Priest | 80 | 12 | 2d15 Fire | 5,000 | 25 |  | 60/20/20/20/0/0/0 | RA | 400g 12gm T3 | Ancient Temple of Yak×7 | 25 |
| CAS | D8 | Cleric of Mok | 125 | 10 | 250d1 Elec | 30,000 | 40 |  | 10/100/10/10/10/10/0 | R | 10gm | Western Tw 2×6, Western Tw 3×6, Western Tw 1×2 +1 | 30 |
| CAS | X31 | Sorceress | 75 | 15 | 3d12 Fire | 10,000 | 27 |  | 80/0/0/0/0/30/0 | RA | 15gm T3 | Rivercity×7 | 30 |
| CAS | D60 | Sewer Hag | 75 | 10 | 10d25 Elec | 50,000 | 40 | insane | 0/100/0/100/0/20/0 | R | 10gm | Sandcaster Sewer×28 | 35 |
| CAS | X42 | Wizard | 75 | 17 | 2d30 Fire | 25,000 | 30 |  | 100/60/60/60/60/50/0 | RAF | 250g 25gm T3 | C.Basenji 2×6, C.Basenji 1×3, C.Basenji 3×2 | 38 |
| CAS | D50 | Enchantress | 100 | 25 | 3d150 Elec | 40,000 | 60 |  | 10/100/10/10/10/20/0 | R | 20gm | Sandcaster×17 | 40 |
| CAS | D9 | Mok Heretic | 150 | 12 | 500d1 Mag | 50,000 | 50 |  | 20/50/20/20/20/30/0 | R | 25gm T4 | Western Tw 4×10, Western Tw 3×3, Western Tw 2×1 | 40 |
| CAS | D35 | Mystic Mage | 200 | 20 | 10d20 Elec | 100,000 | 70 |  | 50/100/50/50/50/30/0 | RAF | 50gm | Eastern Tw 3×8, Eastern Tw 2×7, Eastern Tw 4×6 +1 | 45 |
| CAS | D86 | Valio* | 150 | 15 | 10d25 Mag | 60,000 | 60 |  | 50/30/30/30/40/30/0 |  | – | Castleview Sewer×1 | 45 |
| CAS | X50 | Sorcerer | 90 | 20 | 8d10 Cold | 30,000 | 40 |  | 30/30/100/30/30/70/0 | RA | 360g 40gm T4 | Tw of High Magic 3×4, High Magic Clouds×3, Tw of High Magic 2×2 +1 | 45 |
| CAS | X63 | Darzog Clone | 30 | 12 | 4d30 Elec | 30,000 | 35 |  | 0/0/0/0/0/10/0 | RA | – | Darzog's Tw 3×6, Darzog's Tw 2×1 | 45 |
| CAS | X85 | Cult Leader* | 110 | 22 | 3d30 Fire | 30,000 | 32 |  | 100/70/70/70/70/70/0 | RAF | 450g 30gm T5 | C.Basenji 3×1 | 45 |
| CAS | D62 | Witch | 150 | 15 | 10d10 Elec | 80,000 | 70 |  | 0/100/0/20/0/20/0 | RA | 10gm | Lakeside×18 | 50 |
| CAS | D65 | Wizard | 250 | 20 | 10d25 Mag | 60,000 | 125 |  | 50/30/30/30/30/30/0 | R | 20gm | Sandcaster×28 | 50 |
| CAS | D36 | Magic Mage | 300 | 25 | 10d30 Elec | 200,000 | 80 |  | 50/100/50/50/50/50/0 | RAF | 75gm | Eastern Tw 4×7, Eastern Tw 3×1 | 55 |
| CAS | D51 | Sorceress | 200 | 30 | 2d50 Mag | 80,000 | 80 |  | 10/20/10/10/10/80/0 | RA | 50gm T5 | Sandcaster×7 | 55 |
| CAS | D68 | Cult Leader* | 100 | 20 | 10d10 En | 100,000 | 60 |  | 50/50/50/50/100/50/0 | RA | 100gm T6 | Western Tw 4×1 | 55 |
| CAS | X87 | Darzog* | 150 | 25 | 4d30 Elec | 50,000 | 35 | stone | 20/20/20/20/20/0/0 | RA | 50gm T6 | Darzog's Tw 3×1 | 55 |
| CAS | D63 | Coven Leader* | 250 | 20 | 10d15 En | 120,000 | 100 | drain SP | 10/100/0/50/100/50/0 | RA | 20gm T6 | Lakeside×1 | 60 |
| CAS | D64 | Master Wizard | 500 | 25 | 2×10d40 Fire | 120,000 | 150 |  | 100/50/50/50/50/50/0 | R | 50gm | Sandcaster×7 | 60 |
| CAS | D77 | Morgana* | 300 | 35 | 2d60 En | 200,000 | 100 | paralyze | 50/50/50/50/100/80/0 | RA | 100gm T6 | Sandcaster×1 | 65 |
| CAS | D93 | Xenoc* | 700 | 35 | 10d50 En | 250,000 | 175 |  | 50/50/50/50/100/50/0 | A | 100gm T6 | Sandcaster×1 | 65 |
| CAS | D73 | Mega Mage* | 500 | 35 | 10d40 Elec | 500,000 | 100 |  | 80/100/80/80/80/80/0 | RAF | 100gm T6 | Eastern Tw 4×1 | 70 |
| UND | X8 | Skeleton | 20 | 5 | 2d6 Ph | 250 | 10 |  | 50/50/50/50/0/0/50 |  | – | Ancient Temple of Yak×42, Area E4×17, Area E3×11 +3 | 6 |
| UND | X9 | Zombie | 30 | 2 | 2×2d4 Ph | 300 | 4 | disease | 0/80/80/80/0/0/50 |  | – | Area E4×10, Area E3×6, Area D3×1 +2 | 9 |
| UND | X77 | Spirit Bones | 40 | 10 | 2d8 Ph | 2,000 | 10 | aging | 0/0/0/0/0/0/100 |  | – | Winterkill×20 | 15 |
| UND | X27 | Ghoul | 100 | 15 | 2×2d10 Ph | 3,500 | 20 | paralyze | 0/0/0/0/0/0/50 |  | – | Tomb of a 1000 Terrors×17 | 18 |
| UND | X78 | Polter-Fool | 50 | 15 | 2d16 Ph | 3,000 | 20 | aging | 0/0/0/0/0/0/100 |  | – | Winterkill×20 | 20 |
| UND | X33 | Tomb Guard | 50 | 25 | 4d5 Mag | 6,000 | 18 | aging | 0/0/0/0/0/0/60 | F | – | Tomb of a 1000 Terrors×9 | 24 |
| UND | X79 | Ghost Rider | 60 | 20 | 2d32 Ph | 4,000 | 30 | aging | 0/0/0/0/0/0/100 |  | – | Winterkill×20 | 25 |
| UND | X40 | Mummy | 60 | 15 | 2×2d20 Ph | 9,000 | 20 | disease | 0/80/80/80/80/0/50 |  | – | Sphinx Body×6, Sphinx Head×1 | 30 |
| UND | X48 | Gnome Vampire | 80 | 18 | 2×3d16 Ph | 12,000 | 36 | drain SP | 0/90/90/90/0/10/20 |  | – | Nightshadow×9 | 33 |
| UND | X41 | Yak Lich | 80 | 20 | 5d5 Mag | 20,000 | 27 | unconscious | 0/0/0/0/0/50/40 | RAF | – | Ancient Temple of Yak×9 | 35 |
| UND | X51 | Tomb Terror | 150 | 15 | 4d20 Mag | 13,000 | 27 | curse | 0/0/0/0/0/0/60 | F | – | Tomb of a 1000 Terrors×8 | 40 |
| UND | X86 | Count Draco* | 130 | 25 | 3d15 Mag | 35,000 | 40 | drain SP | 0/90/90/90/0/20/60 | A | – | Nightshadow×1 | 45 |
| UND | D39 | Higher Mummy | 400 | 20 | 10d40 Ph | 100,000 | 60 | curse item | 0/50/50/100/50/20/75 |  | – | Necropolis×24 | 50 |
| UND | D57 | Vampire | 400 | 30 | 10d10 Ph | 200,000 | 80 | weaken | 50/50/50/50/50/50/50 |  | – | C.Blackfang 3×10, C.Blackfang 2×8, C.Blackfang 1×3 | 50 |
| UND | X83 | Yak Master* | 160 | 22 | 5d10 Mag | 50,000 | 30 | death | 0/0/0/0/0/60/60 | RAF | – | Ancient Temple of Yak×1 | 50 |
| UND | D34 | Power Lich | 500 | 20 | 10d10 Mag | 200,000 | 60 | unconscious | 0/0/0/0/0/80/70 | RAF | – | Necropolis×5, C.Kalindra Dungeon×3 | 60 |
| UND | D58 | Vampire Lord | 500 | 35 | 10d30 Ph | 300,000 | 100 | sleep | 50/50/50/50/50/50/70 |  | – | C.Blackfang 3×10, C.Blackfang 2×5, C.Blackfang 1×1 | 60 |
| UND | D72 | Sandro* | 1000 | 20 | 10d10 Mag | 200,000 | 75 | death | 0/0/0/0/0/90/80 | RAF | 100gm T7 | Necropolis×1 | 70 |
| UND | D79 | Royal Vampire | 750 | 40 | 10d50 Ph | 400,000 | 125 | curse item | 50/50/50/50/50/50/65 |  | – | C.Blackfang 3×3 | 75 |
| UND | D91 | Ghost Mummy | 500 | 35 | 200d5 Ph | 500,000 | 175 | aging | 0/60/80/80/80/50/80 |  | – | Southern Sphinx 1×17 | 80 |
| UND | D49 | Skeletal Lich | 2000 | 30 | 1000d1 En | 500,000 | 200 | eradicate | 80/70/80/100/100/50/50 | R | – | Dungeon of Death 2×79 | 85 |
| UND | D92 | Phase Mummy | 500 | 35 | 200d6 Ph | 500,000 | 175 | drain SP | 0/70/80/80/80/60/85 |  | – | Southern Sphinx 2×4 | 85 |
| UND | D80 | Ct. Blackfang* | 1500 | 50 | 10d100 Ph | 2,000,000 | 150 | death | 75/75/75/75/75/75/75 |  | – | C.Blackfang 3×1 | 90 |
| UND | D15 | Dragon Mummy | 3000 | 30 | 2000d2 Ph | 2,000,000 | 100 | disease | 0/80/100/100/0/10/90 |  | – | Southern Sphinx 3×18, C.Kalindra Dungeon×2 | 100 |
| UND | D16 | Scraps* | 3000 | 30 | 2000d2 Ph | 2,000,000 | 100 |  | 0/80/100/100/0/10/90 |  | – | C.Kalindra Dungeon×1 | 100 |
| UND | D85 | Vampire King | 10000 | 60 | 10d250 Ph | 3,000,000 | 200 | eradicate | 80/80/80/80/80/80/90 |  | – | Dungeon of Death 2×5 | 110 |
| BEA | X1 | Giant Bat | 10 | 5 | 2d4 Ph | 60 | 20 |  | – | F | – | Dwarf Mine 1×15, Dwarf Mine 3×8, Dwarf Mine 2×7 +1 | 3 |
| BEA | D47 | Sewer Rat | 40 | 5 | 3d10 Ph | 2,000 | 35 |  | – |  | – | Castleview Sewer×33 | 5 |
| BEA | X11 | Tiger Mole | 40 | 10 | 2×2d12 Ph | 400 | 20 |  | – |  | – | Deep Mine Alpha×15, Dwarf Mine 3×10, Dwarf Mine 1×9 +5 | 9 |
| BEA | X13 | Giant Toad | 90 | 6 | 3d8 Ph | 500 | 17 | sleep | – |  | – | Area F4×7, Area F3×3 | 11 |
| BEA | X16 | Bat Queen | 50 | 10 | 2×2d15 Ph | 700 | 22 | weaken | – |  | – | Nightshadow×18 | 12 |
| BEA | D76 | Rooka* | 60 | 5 | 3d10 Ph | 5,000 | 40 | disease | – |  | 10gm T4 | Castleview Sewer×1 | 15 |
| BEA | D66 | Dark Wolf | 70 | 10 | 3×3d8 Ph | 10,000 | 70 |  | – |  | – | Area D4×12, Area C3×10, Area D3×6 | 18 |
| BEA | D44 | Sabertooth | 100 | 20 | 3×5d10 Ph | 10,000 | 60 |  | – |  | – | Gemstone Mines×28 | 20 |
| BEA | X36 | Snow Beast | 75 | 25 | 2×2d12 Ph | 7,000 | 32 |  | 0/0/90/0/0/0/0 |  | – | Area A3×10, Area A4×3 | 28 |
| BEA | X39 | Werewolf | 100 | 20 | 2×2d25 Ph | 9,000 | 28 | disease | 20/20/20/20/20/20/0 |  | – | C.Basenji 1×22, Basenji Dungeon×4 | 30 |
| BEA | D4 | Sewer Stalker | 250 | 30 | 3d100 Ph | 50,000 | 25 |  | 0/0/50/50/0/0/0 |  | – | Lakeside Sewer×11 | 35 |
| BEA | X56 | Sand Worm | 250 | 19 | 6d25 Ph | 10,000 | 30 | death | – |  | – | Area A1×5, Area A2×3, Area C1×2 +1 | 40 |
| BEA | D5 | Armadillo | 800 | 50 | 100d6 Ph | 60,000 | 15 | break weapon | 50/0/80/80/50/0/50 |  | – | Area E3×7, Area E2×6, Area F2×2 | 45 |
| BEA | D41 | Octopod | 2500 | 40 | 2d100 Pois | 250,000 | 80 | poison | 0/0/50/100/0/0/0 | AF | – | C.Blackfang Dungeon×5, Area F2×1 | 70 |
| SER | X3 | Giant Snake | 15 | 6 | 1d10 Ph | 100 | 18 | poison | – |  | – | Area F4×9, Area F3×2 | 4 |
| SER | X30 | Snake Man | 50 | 15 | 3d10 Ph | 5,000 | 26 |  | – |  | 100g T3 | Asp×18 | 24 |
| SER | X54 | Guardian Asp | 90 | 22 | 2d40 Ph | 15,000 | 35 | confuse | 0/0/0/0/0/50/0 |  | – | Asp×8 | 40 |
| SER | D46 | Killer Cobra | 1000 | 25 | 2d100 Ph | 25,000 | 100 | aging | 0/0/0/100/0/50/0 |  | – | Area F4×10, Area E4×5 | 45 |
| SER | D29 | Iguanasaurus | 2500 | 20 | 10d50 Ph | 100,000 | 30 | insane | 50/50/50/50/50/0/20 |  | – | Area B2×6, Area C2×5 | 60 |
| VER | X0 | Slime | 2 | 0 | 2×1d2 Pois | 50 | 25 |  | 0/0/0/100/0/0/0 |  | – | Vertigo×20 | 1 |
| VER | X2 | Doom Bug | 5 | 3 | 6d1 Pois | 75 | 17 |  | 0/50/50/100/50/0/0 |  | – | Vertigo×24 | 2 |
| VER | D48 | Sewer Slug | 25 | 2 | 2d10 Ph | 1,000 | 25 |  | 0/0/0/100/0/0/0 |  | – | Castleview Sewer×50 | 3 |
| VER | X73 | Breeder Slime | 20 | 2 | 1d8 Pois | 200 | 25 |  | 0/0/0/100/0/0/0 |  | – | Vertigo×2 | 4 |
| VER | X4 | Giant Spider | 20 | 4 | 1d8 Ph | 100 | 19 | poison | 0/50/50/50/50/0/0 |  | – | Deep Mine Kappa×32, Deep Mine Alpha×22, Deep Mine Theta×19 +6 | 5 |
| VER | D52 | Arachnoid | 50 | 10 | 3d5 Pois | 4,000 | 40 | poison | 0/0/0/100/0/0/0 |  | – | Area A3×8, Area B3×4, Area C1×3 +2 | 10 |
| VER | X15 | Insect Swarm | 30 | 10 | 10d1 Ph | 1,300 | 28 |  | 0/50/50/50/0/0/0 | AF | – | Area E3×7, Area D2×3 | 12 |
| VER | X19 | Giant Scorpion | 100 | 14 | 2d40 Ph | 1,000 | 28 | poison | 20/50/50/100/0/0/0 |  | – | Area A1×6, Area C1×6, Area A2×5 +2 | 16 |
| VER | D7 | Electrapede | 200 | 10 | 50d1 Elec | 10,000 | 50 | paralyze | 50/100/50/50/50/0/0 |  | – | Area A4×8, Area B4×2 | 18 |
| VER | X23 | Stingers | 50 | 15 | 20d1 Ph | 3,600 | 30 | weaken | 0/50/50/50/0/0/0 | AF | – | Area D4×7, Area C4×2 | 20 |
| VER | D45 | Sand Flower | 100 | 10 | 5×5d5 Ph | 10,000 | 50 | in love | 0/0/0/0/0/50/50 |  | – | Area C2×4, Area D2×3 | 22 |
| VER | D10 | Mantis Ant | 300 | 30 | 2×2d100 Ph | 40,000 | 40 | poison | 0/0/0/100/0/0/30 |  | – | Area E4×10, Area F4×8, Area F3×5 +1 | 40 |
| VER | D33 | Lava Roach | 500 | 20 | 5d50 Fire | 50,000 | 70 |  | 100/100/0/100/0/0/0 |  | – | Necropolis Sewer×13 | 40 |
| VER | D20 | Hell Hornet | 250 | 30 | 2×2d250 Pois | 50,000 | 50 | weaken | 50/50/50/100/50/0/50 | F | – | Area E1×8, Area F1×4 | 45 |
| FLY | D53 | Medusa Sprite | 30 | 5 | 3d3 Ph | 5,000 | 30 | stone | – | F | – | Area C4×29, Area B4×12, Area C3×4 +3 | 12 |
| FLY | X20 | Harpy | 80 | 7 | 2×2d15 Mag | 1,200 | 21 | in love | 0/0/0/0/0/50/0 |  | – | Witch Clouds×20 | 14 |
| FLY | X22 | Killer Sprite | 25 | 12 | 2×2d6 Elec | 1,600 | 35 | curse | 20/20/20/20/20/20/20 | F | 6gm | Area D4×9, Area D3×8, Area C3×5 +1 | 15 |
| FLY | D90 | Sharla* | 50 | 5 | 3d4 Ph | 10,000 | 50 |  | – | F | – | Area C4×1 | 18 |
| FLY | D18 | Beholder Bat | 75 | 15 | 5d5 Fire | 10,000 | 80 |  | 100/50/0/0/0/0/0 | AF | – | Gemstone Mines×46, Sandcaster Sewer×37, Ellinger's Tw 2×5 +14 | 20 |
| FLY | X81 | Harpy Queen | 120 | 10 | 2×2d25 Mag | 10,000 | 25 | weaken | 0/0/0/0/0/60/0 |  | – | Witch Clouds×1 | 25 |
| FLY | D21 | Gargoyle | 150 | 35 | 2×5d50 Ph | 30,000 | 30 |  | 0/0/0/0/0/20/0 |  | – | Area F3×9, Area F1×8, Area F2×7 | 30 |
| FLY | X47 | Gargoyle | 70 | 18 | 4×5d5 Ph | 11,000 | 32 | paralyze | 0/0/0/0/0/20/0 |  | – | Area C1×17 | 33 |
| FLY | X66 | Roc | 300 | 16 | 2×4d15 Ph | 20,000 | 28 | paralyze | – | F | – | Clouds of Xeen×15 | 40 |
| FLY | D27 | Griffin | 800 | 35 | 2×50d6 Ph | 60,000 | 150 |  | 0/0/0/0/0/80/0 |  | – | Area B1×10, Skyroad B1×8, Area C1×7 +3 | 50 |
| FLY | D59 | Vulture Roc | 2500 | 50 | 5d60 Ph | 200,000 | 150 |  | – | F | – | Area D2×10, Area E2×7, Area D3×6 | 55 |
| FLY | D28 | Gamma Gazer | 5000 | 60 | 7×10d20 En | 1,000,000 | 200 |  | 100/100/0/100/100/0/60 |  | – | Area A1×15, Area A2×4, Area B1×3 +2 | 80 |
| GOL | X21 | Guardian | 40 | 20 | 2×3d10 En | 1,500 | 25 | drain SP | 0/0/0/0/100/70/0 | F | 5gm | Cave of Illusion 4×10, Cave of Illusion 3×4, Cave of Illusion 1×3 +1 | 18 |
| GOL | X26 | Flying Feet | 40 | 14 | 2×4d5 Ph | 3,000 | 30 | sleep | 0/0/0/0/0/60/0 | F | – | Tw of High Magic 2×13, Tw of High Magic 4×11, Tw of High Magic 1×9 +2 | 20 |
| GOL | X28 | Water Golem | 150 | 16 | 2×2d25 Cold | 4,000 | 15 |  | 0/0/0/0/0/0/50 |  | 5gm | Cave of Illusion 3×8, Cave of Illusion 2×6, Cave of Illusion 4×5 +1 | 24 |
| GOL | X37 | Sand Golem | 80 | 18 | 40d1 Ph | 8,000 | 10 | sleep | 80/80/80/80/0/0/20 |  | 5gm | Area B1×6, Area A2×5 | 30 |
| GOL | X44 | Wood Golem | 100 | 10 | 2d50 Ph | 10,000 | 10 |  | 0/50/90/80/0/0/0 |  | 5gm | Newcastle Foundation×13, Golem Dungeon×13 | 30 |
| GOL | X49 | Carnage Hand | 200 | 10 | 2d60 Ph | 12,000 | 15 |  | 0/0/0/0/0/80/0 | F | 10gm | Darzog's Tw 1×8, Darzog's Tw 4×5, Darzog's Tw 2×4 | 35 |
| GOL | X52 | Earth Golem | 150 | 12 | 2×4d20 Ph | 14,000 | 20 |  | 80/90/90/80/0/0/20 |  | 6gm | Sphinx Dungeon×10, Sphinx Head×1 | 40 |
| GOL | X55 | Stone Golem | 200 | 18 | 2×3d30 Ph | 20,000 | 20 |  | 100/90/100/70/0/0/50 |  | 8gm | Golem Dungeon×14, Sphinx Body×12, Sphinx Head×1 | 45 |
| GOL | X58 | Iron Golem | 300 | 24 | 2×2d50 Ph | 25,000 | 24 |  | 90/100/100/80/50/0/50 |  | 10gm | Golem Dungeon×10 | 50 |
| GOL | X60 | Cloud Golem | 175 | 15 | 2×5d12 Elec | 30,000 | 26 |  | 0/100/0/100/60/0/80 | F | 10gm | High Magic Clouds×14, Clouds of Xeen×12 | 50 |
| GOL | X65 | Lava Golem | 500 | 23 | 2×2d50 Fire | 20,000 | 30 | break weapon | 100/80/0/100/50/0/50 |  | 10gm | Area F1×11, Area D1×4, Area E2×2 +2 | 55 |
| GOL | X62 | Xeen's Guard | 100 | 50 | 100d1 En | 20,000 | 50 |  | 80/80/80/80/20/0/50 |  | – | Xeen's C.Level 1×14, Xeen's C.Level 4×7, Xeen's C.Level 3×4 +1 | 60 |
| GOL | X67 | Diamond Golem | 1000 | 40 | 2×4d50 Ph | 30,000 | 30 | break weapon | 80/80/80/50/0/0/50 |  | 20gm | Golem Dungeon×9 | 70 |
| GOL | D2 | Annihilator | 1500 | 40 | 12×5d50 En | 1,000,000 | 200 |  | 80/80/100/100/0/0/80 | R | – | C.Alamar 2×50, Dungeon of Death 3×19, C.Alamar Dungeon×17 +2 | 80 |
| GOL | D87 | Sky Golem | 1000 | 50 | 2d100 Cold | 200,000 | 100 |  | 50/50/100/50/50/50/50 | RAF | – | Skyroad F1×11, Skyroad B3×6, Skyroad A2×5 +12 | 80 |
| GOL | D3 | Autobot | 2500 | 100 | 2×5d100 En | 1,000,000 | 200 |  | 50/50/100/100/0/0/50 | F | – | Dungeon of Death 3×11, C.Alamar Dungeon×6 | 95 |
| GOL | D24 | Onyx Golem | 10000 | 50 | 2d250 Mag | 1,000,000 | 100 | drain SP | 100/100/100/100/100/100/50 | AF | 100gm | Darkstone Tw 3×10, Darkstone Tw 1×6, Darkstone Tw 4×6 +1 | 100 |
| ELE | D32 | Lava Dweller | 1500 | 30 | 5d100 Fire | 500,000 | 40 |  | 100/100/0/100/50/0/50 | A | – | Area A1×10 | 80 |
| ELE | D1 | Whirlwind | 1000 | 10 | 5d100 Ph | 250,000 | 250 | confuse | 100/100/100/100/0/0/100 | A | – | Dungeon of Death 1×90, Elemental Plane of Air×8 | 85 |
| ELE | D17 | Earth Blaster | 1000 | 10 | 5d100 Ph | 250,000 | 100 |  | 100/90/90/100/0/0/90 | A | – | Elemental Plane of Earth×8 | 85 |
| ELE | D19 | Fire Blower | 1000 | 20 | 5d100 Fire | 250,000 | 60 |  | 100/50/0/100/50/0/50 | A | – | Elemental Plane of Fire×8 | 85 |
| ELE | D61 | Tidal Terror | 1000 | 10 | 5d100 Cold | 500,000 | 200 |  | 100/50/50/100/50/0/100 | AF | – | Elemental Plane of Water×8 | 85 |
| DEM | X64 | Demon | 300 | 30 | 3d33 Fire | 30,000 | 33 |  | 100/0/0/0/0/20/0 | RAF | – | Dungeon of Death 4×14, Volcano Cave 1×5, Volcano Cave 3×5 +1 | 55 |
| DEM | X70 | Devil | 350 | 30 | 3d33 Cold | 40,000 | 66 |  | 100/0/0/0/0/30/0 | RAF | – | Dungeon of Death 4×12, Volcano Cave 1×5, Volcano Cave 3×4 +1 | 65 |
| DEM | D67 | Screamer | 3000 | 50 | 10d20 Pois | 500,000 | 200 | poison | 0/0/0/100/0/0/60 | A | – | Dungeon of Death 2×22 | 90 |
| DEM | D94 | Barkman* | 40000 | 25 | 3×250d1 Fire | 4,000,000 | 100 |  | 100/50/0/100/0/0/0 |  | T6 | Temple of Bark 5×9 | 100 |
| DEM | X89 | Lord Xeen* | 500 | 25 | 1000d1 En | 600,000 | 50 | eradicate | 100/100/100/100/100/100/100 | RF | – | Dungeon of Death 4×39, Xeen's C.Level 4×1 | 110 |
| DRA | X59 | Water Dragon | 200 | 15 | 80d1 Cold | 50,000 | 26 |  | 50/0/100/90/0/0/0 | RA | – | Area D3×3 | 60 |
| DRA | X61 | Acid Dragon | 220 | 25 | 100d1 Pois | 60,000 | 22 |  | 0/0/0/100/0/0/0 | RA | – | Dragon Tw 2×6, Dragon Tw 4×6, Area D1×4 +2 | 65 |
| DRA | X71 | Great Hydra | 1000 | 27 | 12×10d10 Ph | 50,000 | 30 | poison | 50/50/50/100/50/0/0 |  | – | Area E1×3, Area F1×1 | 65 |
| DRA | X68 | Fire Dragon | 350 | 30 | 200d1 Fire | 80,000 | 28 |  | 100/0/0/0/0/0/0 | RA | – | Dragon Cave×17, Dragon Tw 3×8, Dragon Tw 2×3 +2 | 75 |
| DRA | D11 | Cloud Dragon | 2000 | 40 | 600d1 Cold | 500,000 | 150 |  | 0/50/100/100/50/25/50 | RA | 10gm | The Great Pyramid 1×35, Dragon Clouds×12, Skyroad D2×7 +18 | 80 |
| DRA | D13 | Green Dragon | 2500 | 50 | 500d1 Fire | 500,000 | 150 |  | 100/50/0/100/50/25/50 | RA | 10gm | Dragon Clouds×12, Skyroad E2×8, The Great Pyramid 1×5 +3 | 85 |
| DRA | X69 | Frost Dragon | 450 | 35 | 250d1 Cold | 100,000 | 30 |  | 0/0/100/0/0/0/0 | RA | – | Dragon Cave×14, Dragon Tw 3×8, Dragon Tw 2×3 | 85 |
| DRA | X88 | Xeen's Pet* | 400 | 35 | 250d1 Pois | 100,000 | 30 |  | 0/0/0/100/0/0/0 | RA | – | Xeen's C.Level 4×1 | 90 |
| DRA | X72 | Dragon King | 2000 | 45 | 400d1 En | 250,000 | 40 |  | 100/100/100/100/100/100/0 | RA | – | Dragon Tw 4×7, Dragon Cave×1, Dragon Tw 1×1 | 100 |
| DRA | D12 | Phase Dragon | 4000 | 80 | 750d1 Cold | 2,000,000 | 200 |  | 0/50/100/100/80/50/50 | RA | 20gm | Dragon Clouds×8 | 110 |
| DRA | D14 | Energy Dragon | 5000 | 100 | 1000d1 En | 2,000,000 | 250 |  | 80/80/60/100/100/30/50 | RA | 20gm | Dragon Clouds×21 | 115 |
| DRA | D69 | Mega Dragon* | 64000 | 100 | 10d200 En | 100,000,000 | 200 | eradicate | 100/100/100/100/100/100/90 | RA | 232gm | Skyroad A1×1 | 150 |

Note: Dungeon of Death 4 (Darkside map 124) reads `xeen.mon` (ScummVM), so its 39 id-89 records resolve to Lord Xeen;
they are probably Lord Xeen images in Sheltem's lair rather than 39 bosses. Check the map's events before relying on it.

## 2. Mapping onto MM6–MM8 three-tier families

### 2.1 Conversion rules

| Field | Rule | Basis |
| --- | --- | --- |
| Level | Set by role and region (section 5), then checked against the MM6–MM8 row of the same role. A family spans 1.5–2.5× level from A to C, as MM6–MM8 families do (Goblin 4/6/10, Ogre 15/20/28, Minotaur 39/59/79). | `monster_data.txt` |
| HP, XP | The MM6–MM8 curve, which almost every merged row follows: HP = L²/10 + 3L, XP = L(L+10) (L20: 100 HP, 600 XP; L50: 400/3,000; L100: 1,300/11,000). Bosses ×2–×4 HP, XP by their level. | measured on the table |
| AC | Band medians (BALANCE_PLAN 7.1): L1–5 5, 6–10 8, 11–15 14, 16–20 15, 21–30 20, 31–40 30, 41–55 35, 56–80 50, 81+ 90. Golems, knights, dragons +25–50%; casters, swarms −30%. Xeen AC ≥ 40 (Diamond Golem, Death Knight, Phase Dragon) marks the top of a band. | 7.1 |
| Damage per hit | Band medians: 3 / 8 / 11.5 / 16.5 / 22 / 30.5 / 38.5 / 50 / 72 for the bands above. Xeen multi-attack rows (Ninja 4×, Hydra 12×, Yang Knight 4×) get a shorter recovery (Rec 60–70 instead of 90–100) or `frenzy`, not 4× damage. | 7.1 |
| "A" (hits whole party) | Becomes an area monster spell (Fireball, Ice Blast, Lightning Bolt, Poison Spray, Dragon Breath, Shrapmetal, Mass Distortion) at E–M mastery, or a missile with `missile_blast` (MONSTER_MODIFIERS). Dragons and big casters only; swarms keep a single-target melee. | modifiers |
| Damage type | Fire→Fire, Elec→Air, Cold→Water, Poison/acid→Body (MM's "of Poison/Venom/Acid" are Body), Energy→Ener, Magic→Mind or Spirit spell, Phys→Phys. | special_item_enchants |
| Resistances | Per school from the level base (0 to L10, 5 to L25, 15 to L40, 18 to L55, 30 above; BALANCE_PLAN 3.2). Xeen 100 → `Imm`; 80–90 → 2×base+20; 50 → base+10; 20–30 → base; 0 where Xeen is 0 on an element it is themed against (fire dragon vs Cold) → 0. Xeen Energy has no school: put it into Light. Xeen Magic → Mind and Spirit. Xeen Physical 50–100 (ghosts, elementals, golems) → Phys 30–50 or `Imm` only for true incorporeals. | 3.2 |
| Special attack → `Bonus` | poison→Poison1–3, disease→Disease1–3, insane→Insane, sleep→Asleep, curse item→BrkItem, in love→Drunk, drain SP→DrainSP, curse→Curse, paralyze→Paralyze, unconscious→Uncon, confuse→Afraid, break weapon→Brkweapon, weaken→Weak, eradicate→Errad, aging→Agex2, death→Dead, stone→Stone. All exist in the table. Spell-borne conditions use `spell_conditions`. | `monster_data` Bonus column |
| Hated class | Xeen picks that class's members first (Mad Dwarf: dwarves; Witch: party). No MM6–MM8 column; use `relations.yml` only for faction feuds, otherwise drop. | combat.cpp |
| Loot | Xeen `T1–T7` → MM treasure level by the MM9 rule on proposed level (1–7→1, 8–15→2, 16–30→3, 31–44→4, 45–64→5, 65+→6), gold at MM7's gold per XP (BALANCE_PLAN 3.3). Xeen T7 (Doom Knight, Sandro) → an L6 drop plus the world's artifact chest rule. | 3.3 |

### 2.2 Proposed families

Tier cells: `Name L·HP·AC·dmg·XP`. HP and XP from the curve. Res in MM order (F/A/W/E/Mi/Sp/Bo/Li/Da/Ph), "base" =
level base. Model: **REUSE** an installed model (path stem under `assets_dev/worlds/*/models/`), **NEW** = new 3D model.

| Family | A | B | C | Res / Bonus / spell | MM6–MM8 comparables (id) | Model |
| --- | --- | --- | --- | --- | --- | --- |
| Goblins | Goblin 4·14·6·1d9·56 | Gremlin 6·22·10·2d4+2·96 | Gremlin Guard 10·40·14·2d6+4·200 | base; boss Gettlewaithe L15 ×3 HP, 2000 gold | Goblin/Shaman/King 550–552 (4/6/10) | REUSE mm6_gob2 (gremlins smaller, green skin tier) |
| Orcs | Orc Archer 7·26·8·1d8+3 R·119 | Orc Guard 12·50·14·3d4+5·264 | Orc Elite 25·138·20·3d7+10·875 | A: F/A/W +10; Shaman L20 (Ice Bolt E, `spell_conditions` asleep); boss Shaalth L30 | Lizard Archer 572 (7), Ogre Raider 593 (20), Magyar Soldier 479 (25) | REUSE mm9_dookmilitia (MM9 Half Orc) or mm9_lizardorc; NEW if Xeen's tusked orc is wanted |
| Mad dwarves | Mad Dwarf 7·26·8·2d4+3·119 | Clan Sergeant 12·50·14·3d4+5·264 | Clan King 18·86·16·2d6+6·504 (boss) | F/A/W/E +10; King casts Mass Fear-style sleep (`spell_conditions` asleep) | Dwarf/Warrior/Lord 520–522 (10/20/30) | REUSE mm6_dwa1 / mm7_m190 |
| Ogres | Ogre 18·86·15·2d5+12 (rock R)·504 | Ogre Brute 22·114·16·2d5+16·704 | Ogre Chief 30·180·18·2d5+22·1200 | elements +5; boss Graalg = C ×2 HP | Ogre/Raider/Chieftain 592–594 (15/20/28) | REUSE mm6_ogr |
| Trolls | Troll Grunt 18·86·18·2d10+5·504 | Troll Guard 28·162·28·3d10+7·1064 | Troll Chief 38·258·38·4d10+10·1824 | F/A/W/E base+10; Ice Troll = B with Water Imm; boss Hobstadt L42 | Troll Clubman/Warrior/Chieftain 58–60 (18/28/38), Mountain Troll 450 | REUSE mm8_m476 / mm7_m461 |
| Giants & cyclopes | Cyclops 36·238·30·2d20+10, Afraid·1656 | Giant 50·400·35·4d10+20, Uncon·3000 | Elder Giant 62·570·50·5d10+25·4464 | Mind base+10 (Xeen 20) | Cyclops Hunter 92 (36), Titan 409 (65) | REUSE mm8_m520; mm9_giant / mm6_ttn |
| Minotaurs | Minotaur 58·510·40·3d7+38, Agex2·3944 | Gorgon 65·618·45·3d7+44, Stone·4875 | Minotaur Lord 78·842·50·3d7+55·6864 | Mind/Spirit/Body base+10; Xeen gives them AC 80–90: use the band top | Minotaur Warrior 65 (59), Minotaur Lord 303 (79) | REUSE mm8_m484 / mm6_min1 (Gorgon: bronze tier) |
| Barbarians | Barbarian 12·50·12·3d7+1·264 | Raider 30·180·22·3d7+8·1200 | Chieftain 38·258·28·3d7+14·1824 | elements base+10 on B/C; boss Yog L25 | Magyar/Soldier/Matron 478–480 (14/25/37) | REUSE mm6_bar1 |
| Outlaws | Rogue 12·50·14·3d4+6·264 | Thief 18·86·20·3d4+12, Stealx2·504 | Master Thief 30·180·24·3d6+14·1200 | base; Robber Boss = C; bosses Master Thief, Rooka's gang | Rogue/Master Thief 407–408, 637–639 | REUSE mm6_thf |
| Ninjas | Ninja 22·114·28·2d6+12, Rec 60, shuriken R·704 | Shadow Ninja 30·180·32·2d6+16·1200 | Ninja Master 40·280·40·2d8+20·2000 | all elements base (Xeen 20 everywhere) | Master Monk 585 (27, AC 28) | REUSE mm6_mnk1 or mm7_m290 dark tier; NEW for a proper ninja |
| Archers & rangers | Evil Archer 20·100·16·2d6+6 R Air·600 | Evil Ranger 28·162·22·3d6+6 R, Poison2·1064 | Elite Ranger 36·238·28·3d6+12 R·1656 | A: Air base+20; B: Body base+20 | Master/Fire Archer 476–477 (19/29), Elf Ranger 249 (35) | REUSE mm6_arc1 / mm7_m154 |
| Burlock knights | Jouster 24·130·25·3d7+10·816 | Yang Knight 32·198·35·4d6+14, Rec 70·1344 | King's Guard 40·280·45·4d8+16, Ice Bolt·2000 | elements base+10; Castle Guard = B; boss Captain Yang L42 | Mercenary 194 (17), Ether Knight 154 (40) | REUSE mm6_kni / mm6_gua / mm9_guard |
| Dark knights | Slayer Knight 45·338·45·5d6+20·2475 | Death Knight 55·468·55·5d8+24, Afraid·3575 | Doom Knight 75·788·75·8d8+28, Dead·6375 (boss) | all elements base+10 | Death/Doom Knight, Cuisinart 565–567 (40/60/80) | REUSE mm6_kni (black/red tiers) |
| Witches | Wicked Witch 14·62·10·2d4+4 R, Curse·336 | Witch 32·198·18·Lightning Bolt E·1344 | Coven Witch 50·400·25·Psychic Shock M·3000 | Mind base+20, Air Imm on B/C; bosses Head Witch L22, Coven Leader L60 (DrainSP) | Harpy Witch 558 (19), Witch Doctor 606 (10), Grand Druid 519 (28) | REUSE mm9_hag or mm6_dru1; NEW for the pointed-hat Xeen witch |
| Sorceresses | Sorceress 30·180·16·Fire Bolt M·1200 | Enchantress 40·280·20·Lightning Bolt M·2000 | Grand Sorceress 55·468·30·Psychic Shock M·3575 | Mind/Spirit base+20; B Air Imm; boss Morgana L65 | Sorcerer/Wizard/Archmage 292–294 (25/35/50) | NEW (female caster) or REUSE mm6_dru1 |
| Wizards | Wizard 36·238·18·Fireball E·1656 | Sorcerer 45·338·22·Ice Blast M, Water Imm·2475 | Master Wizard 60·540·30·Incinerate M·4200 | Fire Imm on A/C; bosses Valio L45, Darzog L55 (+Clones L45), Xenoc L65 | Wizard 293 (35), Archmage 294 (50), Air Warlock 420 (50) | REUSE mm6_sor1 / mm7_m274 |
| Floating mages | Mystic Mage 45·338·20·Lightning Bolt M, F·2475 | Magic Mage 55·468·25·Starburst M·3575 | Mega Mage 70·700·35·Implosion GM·5600 (boss) | Air Imm, elements base+10 | Fire/Water/Air Warlock 418–420 | REUSE mm7_m426 (hovering) |
| Cultists | Cleric of Yak 16·74·14·2d4+4, Sparks·416 | Yak Priest 25·138·18·Fireball E·875 | Mok Heretic 40·280·24·Mind Blast M·2000 | Air base+20 on A; Cleric of Mok L30 = B'; bosses Cult Leader L45 (Clouds), L55 (Darkside) | Cleric/Priest of Baa 491–492 (15/25), Priest of the Moon 216 (30) | REUSE mm6_cle |
| Madmen | Insane Beggar 4·14·3·1d6, Insane·56 | Mad Fool 8·30·6·2d4+3, Insane·144 | — | Mind base+10 | Pirate 181 (8) | REUSE peasant models (mm6_pman_v2, mm6_mep) |
| Skeletons | Skeleton 6·22·8·3d4·96 | Spirit Bones 12·50·12·3d4+4, Agex2·264 | Skeleton Lord 16·74·14·3d4+6, Curse·416 | Body/Spirit Imm, Light base+20 | Skeleton/Warrior/Lord 397–399, 628–630 | REUSE mm6_ske |
| Rotting dead | Zombie 10·40·10·2d5+3, Disease1·200 | Ghoul 18·86·15·2d7+6, Paralyze·504 | Mummy 30·180·22·3d8+12, Disease2·1200 | Mind Imm, Body Imm, F base+20 on A | Zombie 429 (17), Ghoul 455 (13) | REUSE mm7_m438 / mm7_m470 / mm9_mummy |
| Spirits | Polter-Fool 18·86·25·2d7+6, Agex2·504 | Tomb Guard 26·146·30·3d7+11, Agex2·936 | Tomb Terror 40·280·35·4d8+16, Curse·2000 | Phys 30–50, Mind/Body Imm; Ghost Rider L25 = B variant | Ghost/Evil Spirit/Specter 547–549 (9/13/19), Barrow Wight 423 (26) | REUSE mm6_gst / mm9_ghost |
| Pyramid mummies | Higher Mummy 50·400·35·5d8+20, BrkItem·3000 | Ghost Mummy 75·788·45·8d8+28, Agex2·6375 | Phase Mummy 85·978·55·8d10+30, DrainSP·8075 | Body Imm, W/E base+20, Phys 30 | none above L30 in MM6–MM8; MM9 Petrified Mummy | REUSE mm9_mummy (three new tiers) |
| Liches | Yak Lich 35·228·20·Ener 5d6, Uncon·1575 | Power Lich 60·540·30·Shrapmetal M·4200 | Skeletal Lich 85·978·45·Dragon Breath M, Errad·8075 | Body/Mind Imm, elements base+10; bosses Yak Master L50 (Dead), Sandro L70 (Dead, Mind Imm) | Lich/Greater/Power 568–570 (20/30/40), Lich King 291 (40) | REUSE mm6_lch / mm9_lich / mm9_lichking |
| Vampires | Gnome Vampire 32·198·30·3d8+16, DrainSP·1344 | Vampire 48·374·40·3d8+28, Weak·2784 | Vampire Lord 62·570·50·3d8+38, Asleep·4464 | Body Imm, W/A base+20; Royal Vampire L75 elite; bosses Count Draco L45, Ct. Blackfang L90, Vampire King L110 | Vampire/Elder Vampire 416–417 (33/48) | REUSE mm8_m468 / mm7_m422 / mm9_nosferatu |
| Bats | Giant Bat 3·10·5·1d4·39 | Bat Queen 10·40·10·2d4+3, Weak·200 | Beholder Bat 20·100·15·Fire Bolt R·600 | base; C Fire Imm | Bat/Giant/Vampire Bat 481–483 (3/6/9) | REUSE mm6_bat (C: eye tier) |
| Spiders | Giant Spider 5·18·8·1d6+2, Poison1·75 | Arachnoid 10·40·12·2d5+3, Poison2·200 | Huge Spider 14·62·16·2d6+6, Poison3·336 | Body base+20 | Spider/Giant/Huge 634–636 (5/8/12) | REUSE mm6_spi1 |
| Swarms | Doom Bug 2·6·3·1d4, Poison1·24 | Insect Swarm 12·50·14·4d3, Rec 60·264 | Stingers 20·100·18·4d4+6, Weak·600 | Phys 20 (hard to hit), W/A base+10; Hell Hornet L45 elite | Dragonfly family 226–228; Wasp 118–120 | NEW (swarm cloud, particle-driven); Hornet REUSE mm8_m556 |
| Giant crawlers | Giant Scorpion 16·74·18·2d8+7, Poison2·416 | Electrapede 20·100·15·Air 4d6, Paralyze·600 | Mantis Ant 38·258·30·4d7+16, Poison3·1824 | Body Imm on C; Lava Roach L42 = Fire tier | Scorpicore 297 (36) | NEW (one arthropod rig, 3 meshes) |
| Oozes | Slime 2·6·2·1d4, Poison1·24 | Breeder Slime 4·14·4·1d6, splits (Lua)·56 | Sewer Slug 6·22·6·2d4+2·96 | Body Imm | Ooze/Acidic/Corrosive 589–591 (12/18/25) | REUSE mm6_ooz / mm9_jelly scaled down |
| Rats & sewer beasts | Sewer Rat 5·18·5·1d8+2, Disease1·75 | Rooka (boss) 12·100·12·3d6, Disease2·264 | Sewer Stalker 35·228·35·4d7+14·1575 | base; C Body/Water base+10 | Rats 619–621 (2/4/6), Greater Wererat 39 (15) | REUSE mm6_rat; C mm8_ratman |
| Wolves & cats | Dark Wolf 16·74·14·2d7+6·416 | Sabertooth 22·114·20·3d7+8, Rec 60·704 | Snow Beast 28·162·25·3d8+10·1064 | C Water Imm | Dire Wolf 85–86 (9/14) | REUSE mm8_wolf / mm9_wolf; Snow Beast mm9_bigfoot; Sabertooth NEW |
| Werewolves | Wolfman 20·100·20·2d12+12·600 | Werewolf 30·180·25·2d12+16, Disease2·1200 | Greater Werewolf 40·280·30·2d12+20·2000 | all base+5 | 643–645 (20/30/40), exact | REUSE mm6_wwf |
| Burrowers | Tiger Mole 9·35·10·2d6+3·171 | Sand Worm 38·258·30·4d8+14, Dead (rare)·1824 | Armadillo 45·338·60·5d6+20, Brkweapon·2475 | C Phys 30, W/E base+20 | Boulder 142–144 (high AC model) | NEW (mole, worm, armadillo) |
| Swamp things | Giant Toad 11·45·10·2d6+4, Asleep·231 | Swamp Thing 26·146·25·3d7+11·936 | Octopod 60·540·45·6d8+24, Poison3·4200 | B Air/Water/Earth base+10; C Body Imm | Tree 451–453 (12/18/25), Sea Terror 627 (48) | NEW toad and octopod; Swamp Thing REUSE mm7_m479 (Treant) |
| Serpents | Giant Snake 5·18·6·1d6+3, Poison1·75 | Guardian Asp 35·228·30·4d7+14, Afraid·1575 | Killer Cobra 45·338·35·5d6+20, Agex2·2475 | Body base+20; C Body Imm | Cobra/King/Queen 493–495 (5/10/14) | REUSE mm6_cob |
| Snake men | Snake Man 24·130·20·3d7+10·816 | Snake Warrior 32·198·28·4d6+14·1344 | Snake Lord 40·280·35·Poison Spray M·2000 | Body base+20 | MM8 Serpentmen, Naga | REUSE mm8_m524 / mm8_m624 |
| Great lizards | Iguanasaurus 60·540·50·6d8+24, Insane·4200 | (Fire/Lightning Lizard as A/B) | — | elements base+10 | Fire/Lightning/Thunder Lizard 505–507 (40/50/60) | REUSE mm6_drag |
| Harpies | Harpy 14·62·12·2d7+4, Drunk·336 | Harpy Hag 18·86·14·2d7+6, Curse·504 | Harpy Queen 24·130·18·2d7+10, Weak·816 | Mind/Spirit base+20 | Harpy/Hag/Witch 556–558 (14/17/19) | REUSE mm6_hrp |
| Sprites | Medusa Sprite 12·50·10·Stone (gaze), F·264 | Killer Sprite 16·74·20·Air 3d6, Curse, F·416 | Sprite Queen (Sharla) 20·100·22·Air 4d6·600 | all base (Xeen 20 all) | Sprite 244 (14), Will O' Wisp 99 (38) | NEW (tiny winged fey) or REUSE mm8_m528 |
| Gargoyles | Gargoyle 22·114·22·2d12+4·704 | Gargoyle Lord 33·208·28·2d12+8, Paralyze, Rec 70·1419 | Obsidian Gargoyle 40·280·40·2d12+12·2000 | Earth Imm, Water base+20 | Stone/Marble/Diamond 541–543 (16/22/33), 262–264 | REUSE mm6_gar / mm7_m234 |
| Great birds | Roc 35·228·25·3d10+15, Paralyze·1575 | Griffin 48·374·35·4d10+18·2784 | Vulture Roc 58·510·45·5d10+22·3944 | Mind base+20 on B | Roc/Greater Roc 391–392 (27/39), Royal Griffin 282 (30) | REUSE mm7_m390 / mm7_m258 |
| Eyes | Floating Eye 30 (MM 484) | Terrible Eye 40 (MM 485) | Gamma Gazer 75·788·60·Ener 6d8 + Implosion·6375 | C Fire/Air/Earth Imm | Flying/Terrible/Maddening Eye 484–486 | REUSE mm6_bh / mm9_eye |
| Material golems | Wood Golem 24·130·25·3d7+10·816 | Stone Golem 40·280·45·4d8+16·2000 | Iron Golem 52·426·60·5d8+22·3224 | Mind/Spirit/Body Imm; A Water/Earth base+20, Fire 0; Diamond Golem L70 (AC 90, Brkweapon); Onyx Golem L100 boss | Bronze/Brass/Gold Golem 277–279 (22/35/50), Juggernaut 158 (60) | REUSE mm7_m254 (material skins) |
| Elemental golems | Sand Golem 22·114·20·3d7+8, Asleep·704 | Water Golem 28·162·22·Water 3d8+10·1064 | Cloud Golem 50·400·30·Air 5d8+20, F·3000 | own school Imm; Earth Golem L40, Lava Golem L55 (Fire Imm, Brkweapon), Sky Golem L80 | Clay/Stone/Earth Elemental 235–237 (25/30/40) | REUSE mm7_m254 with elemental shader, or MM elementals |
| Magic constructs | Flying Feet 18·86·15·2d7+6, Asleep, F·504 | Guardian 24·130·30·Ener 3d6, DrainSP, F·816 | Carnage Hand 35·228·20·4d7+14·1575 | Mind/Spirit base+20; Xeen's Guard L60 elite (AC 80) | Plane Guardian 145 (50) | NEW (Xeen signature: boots, crystal guardian, giant hand) |
| Robots | Patrol Unit 50 (MM 622) | Annihilator 70·700·80·Ener 12d5+15, R·5600 | Autobot 90·1080·100·Ener 20d5+20, Errad·9000 | Mind/Spirit/Body Imm, W/E base+20 | Patrol/Enforcer/Terminator 622–624 (50/70/90) | REUSE mm6_rob1 |
| Elementals | Lesser (50) | Elemental (65) | Greater 80: Fire Blower, Whirlwind, Earth Blaster, Tidal Terror; Lava Dweller = Fire 80 | own school Imm + MM rows' profile | Greater Fire/Water/Earth/Air Elemental 75/78/81/84 (80) | REUSE mm6_fie1, mm6_aie1, mm6_ert, mm6_wel |
| Demons | Demon 50·400·35·Fireball M, R·3000 | Devil 62·570·45·Ice Blast M, R·4464 | Screamer 80·880·50·Body 8d8, Poison3·7200 | Fire Imm, Mind base+20; bosses Barkman L100 (Fire Imm, 4× HP), Lord Xeen L110 | Devil Spawn/Worker/Warrior 502–504, Devil Captain/Master/King 499–501 | REUSE mm6_demon / mm6_wdm / mm9_greaterdemon |
| Dragons (Clouds) | Water Dragon 60·540·50·Ice Blast M (breath)·4200 | Acid Dragon 66·634·55·Poison Spray M·5016 | Fire Dragon 75·788·60·Dragon Breath M·6375 | own element Imm, others base+10; Frost Dragon L85 elite; Dragon King L100 boss; Xeen's Pet L90 | Young Dragon 192 (60), Dragon 70 (70), Red/Blue/Gold 514–516 (80/90/100) | REUSE mm6_cdr1 / mm7_m182; King mm9_dragonking |
| Dragons (Darkside) | Cloud Dragon 80·880·70·Water 12d8 R·7200 | Green Dragon 88·1038·80·Fire 14d8 R·8624 | Phase Dragon 105·1418·100·Ener 16d8 R·12075 | Mind/Spirit base+20; Energy Dragon L115 elite; Mega Dragon L150 superboss (×10 HP) | Blue/Red Dragon 224–225 (90/100), Mega-Dragon 460 (100) | REUSE mm8_m492 / mm6_cdr1 |
| Hydras | Hydra 45 (MM 559) | Venomous Hydra 55 (MM 560) | Great Hydra 65·618·66·20d5, Poison3, Rec 60·4875 | Body Imm | Hydra/Venomous/Colossal 559–561 (45/55/65) | REUSE mm6_hyd |
| Undead dragons | Bone Dragon (MM 164, 45) | Undead Dragon (MM 165, 60) | Dragon Mummy 95·1188·80·Dark 10d8, Disease3·9975 | Body/Mind Imm; Scraps = boss C | Skeletal/Bone/Undead Dragon 163–165 (30/45/60) | REUSE mm8_m616 |

Counts: 51 families. About 41 reuse an installed model with new colour tiers; NEW models are needed for orcs (optional),
ninjas (optional), witches/sorceresses (female casters), swarms, giant crawlers, burrowers, toad, octopod, sabertooth,
sprites and the magic constructs (Flying Feet, Guardian, Carnage Hand, Xeen's Guard). Uniques (Lord Xeen, Barkman,
Dragon King, Xeen's Pet, Count Draco, Darzog, Morgana, Xenoc, Sandro, Ct. Blackfang, Clan King, Captain Yang,
Gettlewaithe, Shaalth, Hobstadt, Graalg, Gurodel, Yog, Sharla, Rooka, Valio, Master Thief) are single rows with
`modifiers.yml` behaviour (frenzy, blink, charge) as MM9 does for its bosses; most can use their family's model with a
unique tier.

Placement roles to keep (they make Xeen recognisable): Vertigo's slime/bug sewers, the orc outposts to burn (E2, F2),
the dwarf mines (spiders, moles, mad dwarves), Witch Tower goblins and witches, Rivercity's beggars/robbers/Yang
knights, Winterkill's three ghosts, Nightshadow's bats and gnome vampires, the Golem Dungeon's material ladder, the
Tower of High Magic's flying feet, Darzog's carnage hands, Castleview's goblins and gremlins, the troll holes, Bark's
orcs, the four Great Towers (thieves, mok clerics, mages, knights), Blackfang's vampires, Alamar's robots, the
Skyroad's cloud dragons.

## 3. Items

### 3.1 The Xeen item system

An item is `{category, base id, material byte, bonus byte, state}`. The single **material byte** chooses exactly one
of three kinds of modifier, so a Xeen item is never "steel sword of fire" but either "steel", "flaming" or "of might":

| Material byte | Kind | Weapon effect | Armour/accessory effect |
| --- | --- | --- | --- |
| 1–36 | Elemental prefix | + elemental damage | + that resistance |
| 37–58 | Metal/material prefix | + damage, + to-hit | + armour |
| 59–130 | Attribute prefix | + attribute while equipped | same |

Weapons can also carry an **effectiveness** bonus ("Dragon Slayer", "Undead Eater", "Golem Smasher", "Bug Zapper",
"Monster Masher", "Beast Bopper": extra damage against that Xeen monster type). Miscellaneous items carry a **special
power** with charges (one of 73 spell effects, from "light" to "the GODS!"). State bits: cursed, broken, identified.

**Bases** (damage `min–max` = `base–base×multiplier`; cost in gold):

- **Weapons** (34): long sword 3–9 (50), short sword 2–6 (15), broad sword 3–12 (100), scimitar 2–10 (80), cutlass 2–8
  (40), sabre 4–8 (60), club 1–3 (1), hand axe 2–6 (10), katana 4–12 (150), nunchakas 2–6 (30), wakazashi 3–9 (60),
  dagger 2–4 (8), mace 2–8 (50), flail 1–10 (100), cudgel 1–6 (15), maul 1–8 (30), spear 1–9 (15), bardiche 4–16
  (200), glaive 4–12 (80), halberd 3–18 (250), pike 2–16 (150), flamberge 4–20 (400), trident 2–12 (100), staff 2–8
  (40), hammer 2–10 (120), naginata 5–15 (300), battle axe 3–15 (100), grand axe 3–18 (200), great axe 3–21 (300),
  short bow 3–6 (25), long bow 5–10 (100), crossbow 4–8 (50), sling 2–4 (15); **Xeen Slayer Sword 6–24** (quest; the
  only weapon that harms Lord Xeen). The tables also name six Elder weapons (Long Sword, Dagger, Mace, Spear, Staff,
  Long Bow) from Swords of Xeen.
- **Armour** (AC, cost): robes 2 (20), scale armor 4 (100), ring mail 5 (200), chain mail 6 (400), splint mail 7 (600),
  plate mail 8 (1000), plate armor 10 (2000), shield 4 (100), helm 2 (60), boots 1 (40), cloak 1 (250), cape 1 (200),
  gauntlets 1 (100).
- **Accessories**: ring 100, belt 100, brooch 250, medal 100, charm 50, cameo 300, scarab 200, pendant 500, necklace
  1000, amulet 2000. **Misc** (power carriers): rod, jewel, gem, box, orb, horn, coin, wand, whistle, potion, scroll.
- Class restrictions are per base (`ITEM_RESTRICTIONS`, a class bitmask per weapon and armour base).

**Material ladder** (`METAL_DAMAGE` / to-hit / `METAL_LAC` armour):

| Material | Dmg | Hit | AC | | Material | Dmg | Hit | AC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wooden | −3 | −3 | −3 | | coral | +1 | +1 | +1 |
| leather | −6 | −4 | 0 | | crystal | +1 | +1 | +1 |
| brass | −4 | +3 | −2 | | lapis | +2 | +2 | +2 |
| bronze | −2 | +2 | −1 | | pearl | +2 | +2 | +2 |
| iron | +2 | +1 | +1 | | amber | +3 | +3 | +3 |
| silver | +4 | +2 | +2 | | ebony | +4 | +4 | +4 |
| steel | +6 | +3 | +4 | | quartz | +5 | +5 | +5 |
| gold | +8 | +4 | +6 | | ruby | +12 | +6 | +10 |
| platinum | +10 | +6 | +8 | | emerald | +15 | +7 | +12 |
| glass | 0 | 0 | 0 | | sapphire | +20 | +8 | +14 |
| | | | | | diamond | +30 | +9 | +16 |
| | | | | | obsidian | +50 | +10 | +20 |

Item generation draws "common" metals (wooden–platinum) and "rare" materials (glass–obsidian) by treasure level: level 2
gives material 1–4, level 4 gives 4–8 / 4–7, level 6 gives 8–9 / 9–13, level 7 platinum / obsidian (`MAKE_ITEM_ARR4`).

**Elemental prefixes** (weapon damage / armour resistance): fire: burning 2/5, fiery 3/7, pyric 4/9, fuming 5/12,
flaming 10/15, seething 15/20, blazing 20/25, scorching 30/30. Electricity: flickering 2/5, sparking 3/7, static 4/9,
flashing 5/12, shocking 10/15, electric 15/20, dyna 20/25. Cold: icy 2/5, frost 4/10, freezing 5/15, cold 10/20, cryo
20/25. Acid/poison: acidic 2/10, venemous 4/15, poisonous 8/20, toxic 16/25, noxious 32/40. Energy: glowing 2/5,
incandescent 3/7, dense 4/9, sonic 5/11, power 10/13, thermal 15/15, radiating 20/20, kinetic 30/25. Magic: mystic
5/5, magical 10/10, ectoplasmic 25/20.

**Attribute prefixes**: Might (might, strength, warrior, ogre, giant, thunder, force, power, dragon, photon: +2, 3, 5,
8, 12, 17, 23, 30, 38, 47); Intellect (clever … genius: +2 … +30); Personality (buddy … holy: +2 … +30); Speed (quick
… velocity: +2 … +30); Accuracy (sharp, accurate, marksman, precision, true, exacto: +3 … +30); Luck (clover …
leprechauns: +5 … +30); Hit points (vigor, health, life, troll, vampiric: +4, 6, 10, 20, 50); Spell points (spell …
arcane: +4 … +25); Armour (protection, armored, defender, stealth, divine: +2, 4, 6, 10, 16); Thievery (mugger …
pirate: +4 … +25). There is no Endurance prefix.

**Quest items** (separate quest inventory, 85 entries; selection): Deed to New Castle, Crystal Key to Witch Tower,
Skeleton Key to Darzog's Tower, Enchanted Key to Tower of High Magic, Jeweled Amulet of the Northern Sphinx, Stone of a
Thousand Terrors, Golem Stone of Admittance, Yak Stone of Opening, Xeen's Scepter of Temporal Distortion, Alacorn of
Falista, Elixir of Restoration, Wand of Faery Magic, Princess Roxanne's Tiara, Holy Book of Elvenkind, Scarab of
Imaging, Crystals of Piezoelectricity, Scroll of Insight, Phirna Root, Orothin's Bone Whistle, Barok's Magic Pendant,
Ligono's Missing Skull, the four Seasons tokens (Last Flower of Summer, Raindrop of Spring, Snowflake of Winter, Leaf of
Autumn), Ever Hot Lava Rock, the six Dolls (Cupie, Might, Speed, Endurance, Accuracy, Luck); Darkside: passes to the
five towns, keys to the four Great Towers, Ellinger's, Dragon, Darkstone, Bark, Lost Souls, Pyramid and Dungeon of
Death, Amulet of the Southern Sphinx, Dragon Pharoah's Orb, Cube of Power, Chime of Opening, ID cards, Vulture
Repellant, Bridle / Enchanted Bridle, Onyx Necklace, Dragon Egg, three Golden Statuettes (Pegasus, Dragon, Griffin),
Chalice of Protection, Jewel of Ages, Songbird of Serenity, Sandro's Heart, Ector's Ring, Vespar's Emerald Handle, Queen
Kalindra's Crown, Caleb's Magnifying Glass, Soul Box (with Corak), four gem rocks, Monga Melon, Energy Disks.

### 3.2 Proposal for the Xeen world's items

Follow MM9's pattern: the world's own `items.txt`, `random_items.txt`, `item_effects`/`item_sets` contributions in
`worlds/xeen/world.yml` with its own `idRanges` (MM9 holds items 10000–10999, monsters 9000–9999; pick free blocks
such as items 11000–11999 and monsters 8000–8999 after checking the Hesper and LoMM stages). Tier numbers come from
the MM9 ladders (BALANCE_PLAN 3.4), so the one random loot pool stays balanced.

**New bases** (each as MM6–MM8-style named rows per tier, numbers from the BALANCE_PLAN 3.4 ladder of the skill shown):

| Xeen base | MM skill / slot | Tiers worth adding | Note |
| --- | --- | --- | --- |
| Katana, wakizashi | Sword (1H; wakizashi as off-hand) | T2–T6 | MM6–MM8 have no katana; Ninja flavour |
| Scimitar, sabre | Sword 1H | T1–T4 | the merged table has only Goblin Scimitar (id 17) |
| Flamberge | Sword 2H | T4–T6 | the merged table has one (Barbarian Flamberge, id 1609) |
| Naginata, bardiche, glaive, pike | Spear (2H) / Axe 2H for bardiche | T2–T6 | polearm variety |
| Grand axe, great axe | Axe 2H | T3–T6 | |
| Nunchaku, flail, maul, cudgel | Mace (nunchaku 1H) | T1–T4 | |
| Sling | Throwing (MMerge skill) or Bow | T1–T2 | cheap starter missile |
| Robes | Leather (cloth, 0 recovery penalty) | T1–T3 | caster body armour |
| Scale, ring, splint mail | Chain / Plate | T2–T4 | fill MM's thin chain ladder |
| Brooch, medal, cameo, scarab, pendant, necklace | Amulet slot (variants) | T2–T6 | visual variety only |

**Prefix ideas onto existing enchant tables** (no engine change):

| Xeen modifier | MM6–MM8 table entry |
| --- | --- |
| Fire prefixes (burning … scorching) | special `of Fire` (1d6) → `of Flame` (2d12) → `of Infernos` (3d18) by tier; armour: standard `of Fire Resistance` |
| Electricity (flickering … dyna) | `of Sparks` → `of Lightning` → `of Thunderbolts`; armour `of Air Resistance` |
| Cold (icy … cryo) | `of Cold` → `of Frost` → `of Ice`; armour `of Water Resistance` |
| Acid/poison (acidic … noxious) | `of Poison` → `of Venom` → `of Acid` (Body); armour `of Body Resistance` |
| Magic (mystic … ectoplasmic) | armour `of Mind Resistance`; weapons: no MM equivalent (see engine list) |
| Energy (glowing … kinetic) | armour `of Protection` (+10 all) at the top two; weapons: no MM equivalent |
| Might / Intellect / Personality / Speed / Accuracy / Luck / HP / SP / Armour | standard `of Might`, `of Thought`, `of Charm`, `of Speed`, `of Precision`, `of Luck`, `of Health`, `of Magic`, `of Defense` |
| Thievery (mugger … pirate) | `Thieves'` (+3 Stealing/Disarm) or standard `of Disarming` |
| Photon/dragon (Might +38/+47) | `of The Dragon` (+25 Might, fire damage) at L6 |
| Vampiric (HP) | `Vampiric` (drain) |
| Dragon Slayer, Undead Eater | `Dragon Slaying`, `Undead Slaying` |
| Golem Smasher, Bug Zapper, Beast Bopper, Monster Masher | NEW slaying specials (need a monster-type tag for golems, insects and animals) |
| Metal/material ladder | Name ladders for the world's tiered bases (wooden/bronze T1, iron/silver T2, steel/crystal T3, gold/amber T4, platinum/ebony/quartz T5, ruby–obsidian T6). The prefix stays in the name, the numbers follow the MM tier ladder. Obsidian = the T6 top (Xeen's obsidian +50 damage is far off any MM curve). |
| Misc items with charged powers | Wands (MMerge wands, usable by anyone, with charges), scrolls and potions. Non-wand carriers (orb, horn, whistle, jewel, coin, box) as "charged trinkets" that reuse the wand mechanism. |

Engine work this needs, if wanted: Energy- and Magic-damage weapon specials (MM has `Ener` monster damage but no item
enchant), and slaying by monster type beyond the existing Dragon/Undead/Elemental/Ogre/Titan sets.

**Artifacts and relics** (flag `World:xeen`, as MM9's; MM6–MM8 caps: one-handed weapon average 24, two-handed 30,
missile 20; plate 75, chain 50, leather 32, shield 32, helm/boots/gauntlets 15; BALANCE_PLAN 3.4):

| Item | Slot | Proposed effect (MM terms) | Source idea |
| --- | --- | --- | --- |
| Xeen Slayer Sword | Sword 2H relic | 30 avg, Double vs Demons and Lord Xeen's kind, `of Doom`-style +stats; NoRandom (quest) | Clouds main quest |
| Elder weapons (6) | Sword, Dagger, Mace, Spear, Staff, Bow | a named set (MM9 `item_sets`), each at the artifact cap, set bonus +10 all resistances | Swords of Xeen data in WoX tables |
| Princess Roxanne's Tiara | Helm | +15 Personality, +15 Intellect, Mind Imm | Clouds quest item |
| Queen Kalindra's Crown | Helm | +20 Personality, +10 all resistances | Darkside quest item |
| Ector's Ring | Ring | +10 Might, +10 Endurance, regeneration | Darkside |
| Barok's Magic Pendant | Amulet | +30 SP, SP regeneration | Clouds |
| Orothin's Bone Whistle | Trinket (relic) | charged Summon/Turn Undead | Clouds |
| Alacorn of Falista | Wand (relic) | charged Cure / Remove Curse (MM7 has an "Alacorn Wand of Charms", id 951) | Clouds |
| Holy Book of Elvenkind | Relic book | +5 Learning, +10 Spirit magic | Clouds |
| Chalice of Protection | Relic | Day of Protection once a day | Darkside |
| Songbird of Serenity | Relic | +20 Mind resistance, cures Insane/Afraid while carried | Darkside |
| Jewel of Ages | Relic | Immunity to aging; restores the Fountain of Youth (quest) | Darkside |
| Vespar's Emerald Handle | Sword artifact (when rehilted) | 24 avg, `of Lightning` | Darkside |
| Four Seasons tokens | 4-piece set (ring, amulet, belt, cloak) | each +10 one resistance; set: +10 all stats | Clouds side quest |
| Golden Statuettes (3) | quest only | keep as quest items | Darkside |

**Treasure level placement curve.** Use MM9's stage table (BALANCE_PLAN 3.3) on the proposed monster level: levels 1–7
→ treasure level 1, 8–15 → 2, 16–30 → 3, 31–44 → 4, 45–64 → 5, 65+ → 6. Chests a step above the area's monsters (MM9's
act tiers). Xeen's own drop tags agree in shape: Clouds ordinary monsters T1–T4, bosses T5–T6; Darkside T2–T7.
Artifacts only from fixed sources and level-7 chest slots (set `chestArtifactsOnly` if the world should follow MM9's
black-chest rule). Section 5 gives the regions' levels.

## 4. Classes, races, skills, spells, wells and guilds

### 4.1 Classes and races

| Xeen class | HP/level | XP base | Spells | Starting skill | MMerge class (`class_skills.txt`) | Fit |
| --- | --- | --- | --- | --- | --- | --- |
| Knight | 10 | 1,500 | — | Arms Master | Knight | direct |
| Paladin | 8 | 2,000 | Clerical (early ranks) | Crusader | Paladin | direct |
| Archer | 7 | 2,000 | Sorcerer (early ranks) | — | Archer | direct |
| Cleric | 5 | 1,500 | Clerical | — | Cleric | direct |
| Sorcerer | 4 | 2,000 | Sorcerer | Cartographer | Sorcerer | direct |
| Robber | 8 | 1,000 | — | Thievery | Thief | direct |
| Ninja | 7 | 1,500 | — | Thievery | Monk line (its last promotion is "Ninja") | partial: Xeen ninja is a base class |
| Barbarian | 12 | 1,500 | — | — | none (Knight or Troll race as stand-in) | conflict |
| Druid | 6 | 1,500 | Druidic (mix of both) | Direction Sense | Druid | direct |
| Ranger | 9 | 2,000 | Druidic (early ranks) | Path Finder | Ranger | direct |

Xeen levels: next level costs `base × 2^(L−1)` up to level 12, then +1,024,000 per level; kill XP is split over the
living members. MM6–MM8 use 1,000 × L per level for everyone, so Xeen's class XP bases have no MM counterpart.

| Xeen race | HP/lvl | SP adj. | Resistances (fire/elec/cold/poison/energy/magic) | Racial skill (ScummVM table) | MMerge race |
| --- | --- | --- | --- | --- | --- |
| Human | 0 | 0 | 7/7/7/7/7/7 | Swimming | Human |
| Elf | −2 | +2 Int | 0/0/0/0/5/5 | — | Elf |
| Dwarf | +1 | −1 | 2/2/2/2/2/20 | Danger Sense | Dwarf |
| Gnome | −1 | +1 | 5/5/5/20/5/0 | Spot Secret Doors | none (NEW race, or skin of Dwarf/Goblin) |
| Half-Orc | +2 | −2 | 10/10/10/0/0/0 | — | Goblin (closest), Troll |

The racial-skill column is ScummVM's `NEW_CHAR_RACE_SKILLS`; the printed manual in the extraction is images only, so it
was not checked against it. Xeen also has alignment (Good/Neutral/Evil) gating a few items and events; MM6–MM8 have none
(MM7's Light/Dark path is the closest).

### 4.2 Secondary skills

Rules from ScummVM `Party::checkSkill`: Mountaineer and Path Finder need **two** members with the skill, Swimming and
Crusader need **every** member, the rest one member. Teachers and prices are from the map text.

| Skill | Xeen effect | Teacher (price) | MM6–MM8 mechanic | Verdict |
| --- | --- | --- | --- | --- |
| Thievery | lock picking %, Robber/Ninja | class | Disarm Traps + Stealing | map |
| Arms Master | + to-hit | Rivercity (300), Castle Kalindra (free) | Armsmaster skill | map (teacher) |
| Astrologer | +2 SP/level for druids/rangers | Book of Astrology (Castle Burlock 1), Way of Astrology (Castle Kalindra 2) | Meditation | map |
| Prayer Master | +2 SP/level for clerics/paladins | Area A2 (free, after a 10,000 gold urn), Lakeside Sewer (10,000) | Meditation | map |
| Prestidigitator | +2 SP/level for sorcerers/archers | Tower of High Magic (quest), Sandcaster (1,000 gems) | Meditation | map |
| Body Builder | +1 HP/level | Rivercity (1,000) | Bodybuilding | map (teacher) |
| Merchant | better prices | Area D2 Clouds (6,000), Sandcaster (5,000) | Merchant | map (teacher) |
| Danger Sense | gem lights when monsters are near | Castle Kalindra (free) | Perception / the HUD alert | merge into Perception |
| Spot Secret Door | gem lights at thin walls | Area E3 Clouds (500), Area E4 Darkside (500) | Perception (MM has no secret-wall cue) | quest/skill check on a few secret doors |
| Linguist | read foreign inscriptions (events) | Sandcaster (25,000) | none; events can test an award | award gating texts (fits) |
| Cartographer | automap | Vertigo (100), Castleview (10) | automap is free in MM | conflict: drop, or award for map notes |
| Direction Sense | compass | Castleview Sewer (1,000) | compass is free | conflict: drop |
| Navigator | no time lost in deserts | Rivercity (2,000), Sandcaster (10,000) | outdoor travel days (MM8 foot-travel table) | award that shortens foot travel (fits) |
| Path Finder | cross forests (2 members) | Vertigo (2,500), Castleview (1,500) | forests are walkable | award opening forest paths or shortcuts; never a hard blocker |
| Mountaineer | cross mountains (2 members) | Rivercity (5,000) | slopes are terrain | award for marked climbs (rope/ledge events) |
| Swimming | enter water (all members) | Rivercity (100), Castleview (250) | Water Walk spell, MM9 Fleet Foot | award for shallow-water wading; conflicts with Water Walk if made a blocker |
| Crusader | entry to Castle Burlock (all members) | quest: destroy the witches, Falista dubs the party (Clouds F4) | quest bit / award | award (fits) |
| Tracker | no effect found in ScummVM | — | — | drop |

Shangri-La's sage teaches every skill for 100,000 gold. Eastern Tower level 4 offers +5 levels (permanent) for all
secondary skills: a fountain-style trade that MM6–MM8 cannot express unless awards are removable.

### 4.3 Spells

Three lists of 39 (Clerical, Sorcerer, Druidic; druids get a mix, Paladin/Archer/Ranger only the early ranks). Costs:
SP (or SP per caster level, `/lvl`) plus gems. Learned by buying from guilds (membership required), from statues and
quests. Rank = position in the class's spell order (DARK_SPELL_OFFSETS), the closest thing to a spell level.

| Xeen spell | Rank | Cost | MM6–MM8 equivalent | Xeen spell | Rank | Cost | MM6–MM8 equivalent |
|---|---|---|---|---|---|---|---|
| Light | C1/S1 D | 1 | Torch Light (Fire 1) | Finger of Death | S21 | 10+4g | NEW party spell (monster FoD exists) or Souldrinker |
| Awaken | C2/S2 D | 1 | Awaken (Water 1) | Walk on Water | C21 D | 7 | Water Walk (Water 5) |
| First Aid | C3 D | 1 | Heal (Body 2) | Acid Spray | C22 D | 8 | Poison Spray (Water 2) |
| Magic Arrow | S3 D | 2 | Fire Bolt / Light Bolt (low, unresisted) | Teleport | S22 | 10 | none on MM maps (in-map jump): drop or Telekinesis |
| Revitalize | C4 D | 2 | Cure Weakness (Body 1) | Cure Poison | C23 D | 8 | Cure Poison (Body 6) |
| Sleep | S4 D | 3+1g | Stun / Slow (Earth 1-2); MM has no party Sleep | Fantastic Freeze | S23 | 15+5g | Ice Blast (Water 10) |
| Flying Fist | C5 D | 2 | Flying Fist (Body 10) | Cure Disease | C24 D | 10 | Cure Disease (Body 8) |
| Toxic Cloud | S5 D | 4+1g | Toxic Cloud (Dark 2) | Super Shelter | S24 | 15+5g | drop (rest anywhere is default) |
| Cure Wounds | C6 D | 3 | Heal (Body 2) | Deadly Swarm | C25 | 12 | Deadly Swarm (Earth 4) |
| Jump | S6 D | 4 | Jump (Air 5) | Recharge Item | S25 | 15+10g | Recharge Item (Water 6) |
| Energy Blast | S7 D | 1/lvl+1g | Light Bolt (Light 1) | Cure Paralysis | C26 | 12 | Cure Paralysis (Mind 6) |
| Pain | C7 D | 4 | Harm (Body 4) | Dancing Sword | S26 | 3/lvl+10g | Blades (Earth 6) |
| Shrapmetal | S8 D | 1/lvl | Shrapmetal (Dark 5) | Golem Stopper | S27 | 20+10g | NEW: Paralyze vs golems only |
| Suppress Poison | C8 D | 4 | Cure Poison (Body 6), weak | Hypnotize | C27 | 15+4g | Charm / Enslave (Mind) |
| Insect Spray | S9 D | 5+1g | NEW: damage vs insects only (or Deadly Swarm) | Create Food | C28 | 20+5g | none (food is gold in MM): drop or make a Body "Feast" ritual |
| Prot. from Elements | C9 D | 1/lvl+1g | Fire/Air/Water/Earth Resistance (one cast = all four: NEW combined buff) | Item to Gold | S28 | 20+10g | drop (Merchant/shops) |
| Levitate | S10 D | 5 | Feather Fall (Air 2) / Fly | Fiery Flail | C29 | 25+5g | Fire Spike / Incinerate (Fire) |
| Sparks | C10 D | 1/lvl+1g | Sparks (Air 4) | Poison Volley | S29 | 25+10g | Poison Spray (Water 2) |
| Suppress Disease | C11 D | 5 | Cure Disease (Body 8), weak | Etherealize | S30 | 30+10g | drop (walk through walls) |
| Wizard Eye | S11 D | 5+2g | Wizard Eye (Air 1) | Town Portal | C30 | 30+5g | Town Portal (Water 9) |
| Identify Monster | S12 D | 5 | ID Monster skill | Enchant Item | S31 | 30+20g | Enchant Item (Water 8) |
| Turn Undead | C12 D | 5+2g | Turn Undead (Spirit 4) | Stone to Flesh | C31 | 35+5g | Stone to Flesh (Earth 7) |
| Beast Master | C13 D | 5+2g | Charm (Mind 5), animals only | Incinerate | S32 | 35+10g | Incinerate (Fire 11) |
| Clairvoyance | S13 D | 5+2g | Fate (Spirit 3) / Telepathy | Raise Dead | C32 | 50+10g | Raise Dead (Spirit 9) |
| Cold Ray | C14 D | 2/lvl+4g | Ice Blast (Water 10) | Mega Volts | S33 | 40+10g | Starburst-lite / Lightning Bolt M |
| Lightning Bolt | S14 D | 2/lvl+2g | Lightning Bolt (Air 7) | Moon Ray | C33 | 60+10g | Shared Life-like heal + damage: NEW or Sunray at night |
| Bless | C15 D | 2/lvl+1g | Bless (Spirit 2) | Day of Sorcery | S34 | 40+10g | Hour of Power (Light 9) |
| Fire Ball | S15 D | 2/lvl+2g | Fireball (Fire 6) | Mass Distortion | C34 | 75+10g | Mass Distortion (Earth 11) |
| Holy Bonus | C16 D | 2/lvl+1g | Heroism (Spirit 7) | Day of Protection | C35 | 75+10g | Day of Protection (Light 8) |
| Power Shield | S16 D | 2/lvl+2g | Shield / Stone Skin | Prismatic Light | S35 | 60+10g | Prismatic Light (Light 7) |
| Heroism | C17 D | 2/lvl+3g | Heroism / Hour of Power | Holy Word | C36 | 100+20g | Destroy Undead (Light 2) GM / Armageddon-lite vs undead |
| Lloyd's Beacon | S17 D | 6+2g | Lloyd's Beacon (Water 11) | Inferno | S36 | 75+10g | Inferno (Fire 10) |
| Detect Monster | S18 | 6 | Detect Life (Spirit 1) | Elemental Storm | S37 | 100+10g | Meteor Shower (Fire 9) |
| Power Cure | C18 D | 2/lvl+3g | Power Cure (Body 11) | Resurrect | C37 | 125+20g | Resurrection (Spirit 11) |
| Nature's Cure | C19 D | 6 | Heal + Cure (Body) | Implosion | S38 | 100+20g | Implosion (Air 9) |
| Time Distortion | S19 | 8 | none (escape combat): Invisibility-like or drop | Sun Ray | C38 | 150+20g | Sunray (Light 10) |
| Dragon Sleep | S20 | 10+4g | NEW: Paralyze vs dragons only | Divine Intervention | C39 | 200+20g | Divine Intervention (Light 11) |
| Frost Bite | C20 D | 7 | Ice Bolt (Water 4) | Star Burst | S39 | 200+20g | Starburst (Air 11) |

Summary: about 60 of 76 map directly or nearly to an MM6–MM8 spell; the rest are monster-type specials (Insect Spray, Dragon
Sleep, Golem Stopper, Beast Master), movement Xeen's grid needs and MM does not (Teleport, Etherealize, Super Shelter,
Time Distortion, Item to Gold, Create Food) or a combined buff (Prot. from Elements). Gem costs have no MM
counterpart; drop them (or reuse reagents if the ruleset has them). No change to the shared spell table is proposed:
the world uses the MM6–MM8 schools, with Xeen names only in guild flavour text.

### 4.4 Wells, fountains and shrines

Xeen's wells are temporary (until rest) unless the text says permanent. MM6–MM8 have the same idea (MM6/MM7 fountains
and pedestals: temporary stat buffs, a few one-time permanent ones), so all of these fit as event scripts; limit the
permanent ones per character with QBits.

| Map | Well | Effect (from text) | MM form |
| --- | --- | --- | --- |
| Clouds D2, B3, C1, C3, E2 | Wells of Might, Accuracy, Intellect, Endurance, Personality, Speed | +50 to that stat | temp stat |
| Clouds A1, A4, C3, D3, E2, F3 | Shrines of Energy, Cold, Magic, Electricity, Fire, Poison | +50 that resistance (pray) | temp resistance |
| Clouds A3, F3 | Fountains of Great Protection, Protection | +5 AC (Protection) | temp AC |
| Clouds F3 | Fountain of Ability | +5 levels (temp) | temp level |
| Nightshadow | Well | +10 levels (temp) | temp level |
| Asp | Well | +100 HP (likely) | temp HP |
| Shangri-La | Well | +1 level, permanent | one-time per character |
| Castle Basenji | Well | +5,000 XP, +10 fire resistance | one-time |
| Clouds statues (Witch, High Magic, Clouds of Xeen) | Statue offerings | +5,000 / +50,000 XP | quest reward |
| Darkside A1 | Fountain of Super Resilience | +2,500 HP (temp) | temp HP |
| Darkside A3, A4 | Wells of Resilience, Spells, Might (+25), Protection | toughness, SP, Might, AC | temp |
| Darkside B1, C1, D4, F2 | Fountains of the Elements, Energy, Elemental and Magic Resistance | +50 resistances | temp |
| Darkside C2 | Shrine of Great Power | prayer answered only on the quest | quest |
| Darkside D1, E1, F1, F4 | Fountains of Might, Great Magic, Great Resilience (+500 HP), Great Protection (+50 AC) | large buffs | temp |
| Darkside F4 | Fountain of Youth | removes unnatural aging (after the Jewel of Ages quest) | quest-gated cure |
| Necropolis; Northern Tower 4 | Well of Death; Throne of the Dunce | kills; joke | trap; flavour |
| Western Tower 2, 3; Eastern Tower 4 | Fountains; Minimal Abilities, Life, Book of Fantastic Knowledge | +10 fire / cold resistance permanent; stats raised | one-time |
| Dragon Clouds | Well of Fantastic Skill | +50 levels (temp) | endgame temp level |

### 4.5 Guild membership

Fees from the map text: Vertigo free (25 gold dues), Nightshadow's Moon Guild 250, Rivercity 500, Asp Guild 500,
Winterkill's Mindmeld Guild "closed" (a 1,000 gold bribe), Shangri-La's wizards free; Castleview 50, Sandcaster's Mirage
Guild 20,000, Lakeside free for a riddle, Necropolis 50,000, Olympus free.

Clouds guilds stock five tiers (`CLOUDS_GUILD_SPELLS`): Vertigo the first ranks (Light, First Aid, Magic Arrow, Sleep,
Sparks …), Nightshadow and Rivercity the middle (Fire Ball, Turn Undead, Lloyd's Beacon, Fantastic Freeze), Asp and
Winterkill the top (Town Portal, Raise Dead, Resurrect, Holy Word, Inferno, Mass Distortion, Teleport). Darkside does
the same over its five towns. **Fit:** MM6's guild membership (bought, required to buy spells) is the same model, so
membership-gated spell shops by tier are a direct mapping; the expensive memberships (20,000, 50,000) are the late
tiers. Other Xeen societies usable as awards: the Drawkcab society in Castleview (+25,000 XP), Bark membership (Temple
of Bark), the Plague Cult in Vertigo.

**What conflicts.** Grid movement skills (Mountaineer, Path Finder, Swimming) as hard blockers, the free automap and
compass skills, gem spell costs, Xeen's exponential class XP, the Barbarian class, the Gnome race, Teleport/Etherealize
(wall passing on 3D maps), and the +50-level wells (keep them temporary and late). **What fits.** Skill teachers with
gold prices, guild membership tiers, temporary and one-time wells, statue offerings for XP, awards (Crusader, Linguist,
Navigator), quest items as relics, the Seasons set, slaying weapons.

## 5. Difficulty pacing

Levels are the proposed MM levels of the monsters placed in each map's initial state (count-weighted range and typical
value); event spawns are not counted. Treasure level by the section 3.2 rule.

| Side | Region (maps) | Monster levels | Typical | Treasure | Notes |
| --- | --- | --- | --- | --- | --- |
| Clouds | Vertigo (town, sewers) | 1–4 | 2 | 1 | slimes, doom bugs |
| Clouds | Areas F3, F4, E3, E4 (south) | 4–11 | 6 | 1 | orcs, skeletons, zombies, toads, snakes; orc outposts |
| Clouds | Dwarf Mines 1–5, Deep Mines α–ω | 3–10 (Clan King 16) | 5–7 | 1–2 | spiders, moles, mad dwarves |
| Clouds | Witch Tower 1–4, Witch Clouds | 4–25 | 4–14 | 1–3 | goblins, witches, harpies |
| Clouds | Rivercity | 5–40 | 12 | 2 | beggars, robbers; Yang knights and Captain Yang late |
| Clouds | Nightshadow | 12–45 | 12 | 2–4 | bats, gnome vampires, Count Draco |
| Clouds | Cave of Illusion 1–4 | 18–24 | 21 | 3 | water golems, guardians |
| Clouds | Areas C3, C4, D2, D3, D4 (swamps) | 12–28 | 20 | 3 | sprites, rangers, swamp things, jousters |
| Clouds | Winterkill, Asp, Tomb of 1000 Terrors | 15–40 | 20–24 | 3 | ghosts; snake men and asps; ghouls, tomb guards |
| Clouds | Ancient Temple of Yak | 6–50 | 6 (42 skeletons) | 2–5 | Yak priests, liches, Yak Master |
| Clouds | Areas A1–C2 (north: desert, snow) | 16–40 | 30 | 3–4 | scorpions, sand worms, barbarians, ninjas, cyclops, ice trolls, gargoyles |
| Clouds | Tower of High Magic, High Magic Clouds | 20–50 | 20–50 | 3–5 | flying feet, sorcerers, cloud golems |
| Clouds | Castles Burlock and Basenji (+dungeons), Newcastle | 8–45 | 32 | 4 | guards; werewolves, wizards, Cult Leader |
| Clouds | Darzog's Tower 1–4 | 35–55 | 35–45 | 4–5 | carnage hands, Darzog |
| Clouds | Golem Dungeon, Sphinx | 30–70 | 45 | 4–6 | the golem ladder, mummies |
| Clouds | Clouds of Xeen | 40–50 | 40 | 4–5 | rocs, cloud golems |
| Clouds | Areas D1, E1, F1 (lava), Volcano Cave | 55–65 | 55–60 | 5 | lava golems, acid dragons, hydras, demons, devils |
| Clouds | Xeen's Castle 1–4 | 60–110 | 60 | 5–6 | Xeen's guards, Xeen's Pet, Lord Xeen |
| Clouds | Dragon Cave | 75–100 | 75 | 6 | fire and frost dragons, Dragon King |
| Darkside | Castleview, its sewer | 3–15 (Valio 45) | 3 | 1 | goblins, gremlins; slugs, rats |
| Darkside | Areas A2–A4, B3, B4, C4, D4 | 10–18 | 12 | 2 | barbarians, arachnoids, electrapedes, medusa sprites, dark wolves |
| Darkside | Southern Tower 1–4 | 12–30 | 12–18 | 2–3 | rogues, thieves, Master Thief |
| Darkside | Temple of Bark 1–4 (5) | 12–30 (Barkman 100) | 12–30 | 2–3 | orc guards, shamans, elites, Shaalth |
| Darkside | Troll Holes, Gemstone Mines, Sandcaster Sewer | 18–42 | 20–28 | 3 | trolls, sabertooths, beholder bats, sewer hags |
| Darkside | Areas C3, D3 | 18–55 | 20 | 3 | ogres, dark wolves, vulture rocs |
| Darkside | Western Tower 1–4 | 30–55 | 30–40 | 3–4 | clerics of Mok, heretics, Cult Leader |
| Darkside | Areas E1–F4 (east) | 30–55 | 40–45 | 4–5 | gargoyles, cobras, mantis ants, hornets, armadillos |
| Darkside | Lakeside, Necropolis and sewers | 35–70 | 40–50 | 4–5 | witches, mummies, liches, sewer stalkers, lava roaches |
| Darkside | Sandcaster | 40–65 | 50 | 5 | wizards, enchantresses, Xenoc, Morgana |
| Darkside | Eastern and Northern Towers | 45–80 | 45–55 | 5 | mages; slayer, death and doom knights |
| Darkside | Areas A1, B1, B2, C1, C2, D1, D2 | 50–80 | 50–80 | 5–6 | griffins, giants, iguanasaurus, gamma gazers, lava dwellers |
| Darkside | Castle Blackfang 1–3 (+dungeon) | 50–90 | 60 | 5–6 | vampires, Ct. Blackfang, octopods |
| Darkside | Lost Souls Dungeon 1–5 | 60–65 | 60 | 5 | minotaurs, gorgons |
| Darkside | Castle Kalindra dungeon | 60–100 | 80 | 6 | power liches, dragon mummies |
| Darkside | Castle Alamar, Great Pyramid, Southern Sphinx | 80–100 | 80 | 6 | robots; cloud dragons; mummies |
| Darkside | Skyroad A1–F4 | 80 (Mega Dragon 150) | 80 | 6 | cloud and green dragons, sky golems |
| Darkside | Elemental Planes, Darkstone Tower, Dragon Tower | 65–100 | 85–100 | 6 | greater elementals; onyx golems; dragons |
| Darkside | Dungeon of Death 1–4 | 55–110 | 85 | 6 | whirlwinds, skeletal liches, screamers, vampire kings, robots, demons |
| Darkside | Dragon Clouds | 80–150 | 110 | 6 | energy and phase dragons |

**Observations for the design:**

- Each side was built as a full 1–max game: both start at level 1–4 (Vertigo, Castleview). Clouds' content tops out
  around MM level 75–100 (Dragon Cave), Darkside's at 110–150. A merged world played Clouds-then-Darkside repeats the
  low band; either keep two starts (MM7-style two continents on one world map) or shift Darkside's early areas up
  (Castleview 15–25, its environs 20–30) so the whole runs about L1–110 like MM7's L1–100.
- MM7 reference (`map_stats.txt` treasure column, 0–6): Emerald Island and Harmondale 0, Erathia and the Tularean Forest
  1, Deyja, Bracada, Evenmorn, Barrow Downs, Tatalia and Avlee 2, Mount Nighon 3, Land of the Giants 6. Clouds' bands
  line up with it: Vertigo/south ≈ Emerald–Harmondale, the swamps and mines ≈ Erathia, the north and the castles ≈
  Deyja/Bracada, the lava and Xeen's Castle ≈ Nighon, the Dragon Cave ≈ Land of the Giants.
- Xeen packs are large in towns and dungeons (Castleview 96, Rivercity 93, Dungeon of Death 1–2 196) and small outdoors
  (8–30 per 16×16 area). MM6-like density suits the dungeons; outdoors, one Xeen area is a fraction of an MM map, so
  several areas make one MM outdoor map and their monster sets become its three `map_stats` slots.
- Xeen's own drop tags rise with the same bands (T1–T2 early, T3–T4 mid, T5–T7 bosses), which supports the section 3.2
  treasure rule without special cases.
- Bolster: give the world's maps `LowerToEqual` rows in `bolster_maps.txt` as MM7 and MM9 have (BALANCE_PLAN 3.7).
