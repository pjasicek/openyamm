# MAW monster and map table diff

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Row-by-row diff of the two monster-side tables MAW overrides in `Data/zMaw.T.lod`
against the base MMMerge copies, and how each change maps onto OpenYAMM's tables.

- MAW: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`, `Data/zMaw.T.lod` entries `MONSTERS.txt` and
  `mapstats.txt` (MMVIII LOD, zlib payloads, extracted with a scratch script).
- Base: `reference/mmerge_data_forus/Data/mmmerge.T.lod/MONSTERS.txt` and `MapStats.txt`.
- OpenYAMM: `assets_dev/engine/data_tables/monster_data.txt` and `map_stats.txt`.

Rows are matched on the `#` id column and compared cell by cell. Values are quoted as they appear in the files.
Related documents: [BALANCE_MODEL.md](BALANCE_MODEL.md) (what MAW does with these columns at runtime),
[COMBAT.md](COMBAT.md) §3.4.

## 1. Summary

- `MONSTERS.txt`: 652 rows, same ids; **220 rows changed**. Changed cells by column: EXP 173, Attack1 damage 107,
  HP 95, AC 93, level 92, treasure 80, attack preference 40, Attack2 damage 23, spell 1 13, Attack1 type 11, special
  attack 9, Attack2 chance 3, spell 1 chance 2, special 1.
- `mapstats.txt`: 207 rows, same ids; **182 rows changed**. Changed cells: treasure level 129, monster label 115,
  monster picture 50, spawn difficulty 25, spawn count 23, name 1.

No row is added or removed in either table, and the column layout is identical to base.

Three MAW cells are only re-formatted (HP `1080` → `" 1,080 "` on 515, 516 and 642); MAW's file has been
round-tripped through a spreadsheet, so many EXP values are quoted with thousands separators (`"1,565"`). The original
engine parses these (vanilla data uses the same form, see OpenEnroth `Monsters.cpp:499-505`); OpenYAMM's
`MonsterTable::loadStatsFromRows` (`game/tables/MonsterTable.cpp:1018-1048`) uses `std::stoi`, which would read
`"1,565"` as 1 or fail. A conversion tool must normalise numbers.

## 2. What each changed column still does under MAW

MAW recomputes most monster numbers at runtime (see [BALANCE_MODEL.md](BALANCE_MODEL.md) §6-8), so a changed cell
does not mean what it means in Standard MMMerge:

- **LVL: fully effective.** `basetable.Level` is the input to every level formula; the B row's level (`BLevel`) is
  the family's reference level and sets HP and damage.
- **HP: only the A/B and C/B ratios matter** (clamped to 0.6-1.8, `Estimates.lua:700-708`). Absolute HP is replaced
  by the balance model.
- **AC: effective**, scaled by `(L + 10) / (LB + 10)` (`zzMaw-Monsters.lua:616`).
- **EXP: no effect.** `Experience` is recomputed on every map load and on kill (`zzMaw-Monsters.lua:607-614,
  4072-4081`). MAW's values equal its own formula at the row's base level (`20 L + L^1.8`, e.g. 1,565 at level 40).
- **Attack1/Attack2 damage: ratio only.** Absolute damage is replaced by the model. The dice still set the
  Attack2/Attack1 ratio (`Damage.lua:1703-1722`) and the dice of the extra ranged attack (`zzMaw-Monsters.lua:645-655`).
- **Attack types, Att%, spells, Use%, special attack, Pref: effective** as in the base game (damage kind, chances,
  spell choice and skill, on-hit condition, target preference).
- **Treasure: partly effective.** Gold dice are only raised, never lowered; the item % feeds `min(%, 50) x 0.3`; item
  level and type are partly replaced (`zzMaw-Items.lua:207-260`).
- **mapstats treasure level: effective** for the engine's chest and random-item generation, before MAW's own loot
  roller rescales items.
- **mapstats `MonN pic`, `dif`, `count`: effective.** They are the backup values `AdjustMonsterDensity` starts from,
  and the pictures define a map's native families (`currentMapMonsters`).
- **mapstats `Mon N` label: no effect** in either engine (OpenYAMM reads it as `monsterName` only when the picture is
  empty, `game/maps/MapAssetLoader.cpp:864`).

## 3. Mapping to OpenYAMM

### 3.1 `monster_data.txt`

- Same ids, same 39 columns and same header as base `MONSTERS.txt`.
- OpenYAMM differs from base only in the `Blood` column on 133 MM6 rows (475 onward), lacks rows 649-651 (Cactus
  A/B/C) and adds custom rows 901-906. None of these cells is touched by MAW: **all 220 changed rows patch cleanly by
  (id, column)**, with 0 conflicts.
- Parser gaps to close before applying MAW's rows:
  - quoted, comma-separated numbers (section 1);
  - letter attack preferences (`A`, `S`, `"D,S"`, `K`, `M`, `"F,C"`, `"P,C"`, `"K,A"`, `"A,S"`): OpenYAMM only
    accepts numeric `Pref` (`MonsterTable.cpp:1048-1049`), so the 40 changed `Pref` cells would read as 0. Base rows
    with letters (`CP`, `DR`, `XK`, ...) are dropped the same way today;
  - `Affraid` (8 rows): a MAW typo for `Afraid`. OpenYAMM matches the prefix `afraid` (`MonsterTable.cpp:416`), so
    these rows would lose their Fear attack, and the original parser most likely does the same. Treat it as a fix
    to record, not as data;
  - treasure cells `15%10D40+6` and `30%10D40+5` (rows 74, 75, 78, 81, 84, 104, 105, 117) lack the `L` of the item
    level. OpenEnroth's parser splits on `L` (`Monsters.cpp:459-490`), so these read as "no item"; most likely a
    MAW typo for `+L6`/`+L5`;
  - spell names `IceBolt` → `Ice Bolt` and `IceBlast` → `Ice Blast` are cosmetic for OpenYAMM, whose
    `SpellTable::findByName` also tries the compacted name (`game/tables/SpellTable.cpp:151-167`).

### 3.2 `map_stats.txt`

- Columns 0-31 are identical to base. OpenYAMM inserts an `area` column at 32 (the base `in area` moves to 33) and adds
  `world_id` at 34; MAW only changes columns 1, 11 and 16-27.
- OpenYAMM has rows 1-203 and 207 (plus MM9 rows from 9001); rows 204-206 (`Breach.odm`, `BrAlvar.odm`,
  `BrBase.blv`) do not exist. It differs from base only in the `Track` column of rows 46, 146, 148 and 166.
- All MAW cells patch cleanly by (id, column) except the one on missing row 206 (`BrBase.blv` treasure 1 → 6).
- Row 153 (`6d02.blv`) is renamed `The Abandoned Temple`. MAW needs this because its level tables are keyed by display
  name; OpenYAMM should key by file name (as in [data/map_levels.yml](data/map_levels.yml)) and can keep its name.

### 3.3 `Placemon.txt` (also overridden, monster-side)

Base has rows 0-162 (162 = `Placeholder`). MAW pads it with rows 162-1000 whose text is the row number, so that
bosses (NameId 221-299) and resurrected monsters (NameId = Id + 300) can be named at runtime by writing
`Game.PlaceMonTxt`. OpenYAMM should store the affix or the "resurrected" flag on the actor instead; the padding is
not data.

## 4. `MONSTERS.txt`: every changed row

Format: `` `id` `` name (tier): column base → MAW. Tier A/B/C is `id % 3` = 1/2/0. Columns: Level, HP, AC, EXP,
Treasure, Pref (attack preference), Special atk (`Bonus`), Atk1/Atk2 type and dmg, Atk2 % (`Att%`), Spell1 % and
Spell1 (`Use%`, `Spl,Mas,Skil`).

### 4.1 Regnan pirates (MM8, 10-18, 8 rows)

The Regnan casters get elemental melee (Air/Water/Fire) and bigger dice; the crossbowmen fire their Attack2 75 % of the
time. Under MAW only the damage kinds, the Attack2 chance and the Attack2/Attack1 dice ratio matter.

- `10` Regnan Bandit (A): Atk1 dmg 4D10+8 -> 4D10+4
- `12` Regnan Brigadier (C): Atk1 dmg 8D10+8 -> 8D10+12
- `13` Regnan Crossbowman (A): Atk1 dmg 6D4+6 -> 6D2+6; Atk2 % 35 -> 75; Atk2 dmg 6D2+6 -> 6D2+4
- `14` Regnan Arbalester (B): Atk1 dmg 7D4+7 -> 7D2+7; Atk2 % 45 -> 75; Atk2 dmg 7D2+7 -> 7D2+8
- `15` Regnan Lieutenant (C): Atk1 dmg 8D4+8 -> 8D2+8; Atk2 % 55 -> 75; Atk2 dmg 8D2+8 -> 8D2+12
- `16` Regnan Sorcerer (A): Atk1 type Phys -> Air; Atk1 dmg 3D6+3 -> 3D10+3
- `17` Regnan Battlemage (B): Atk1 type Phys -> Water; Atk1 dmg 4d6+4 -> 4d10+6; Spell1 "Poison Spray,M,7" -> "Poison
  Spray,M,18"
- `18` Regnan Archmage (C): Atk1 type Phys -> Fire; Atk1 dmg 5D6+5 -> 5D10+9; Spell1 % 35 -> 30

### 4.2 Treasure only (35 rows: MM8 elementals, dragons, birds, turtles, overlords; MM7 dragons and titans)

Dragon-type gold dice become `300D10`/`400D10`, elemental item chances and levels are reshuffled, and `Ore` item
types are removed. The 8 cells without `L` before the item level are noted in section 3.1.

- `71` Dragon Flightleader (B): Treasure 250D12+L6 -> 300D10+L6
- `72` Great Wyrm (C): Treasure 250D16+L6 -> 400D10+L6
- `73` Lesser Fire Elemental (A): Treasure 15%10D30+L4 -> 30%10D40+L5
- `74` Fire Elemental (B): Treasure 15%10D40+L5 -> 15%10D40+6
- `75` Greater Fire Elemental (C): Treasure 15%10D40+L6 -> 30%10D40+6
- `76` Lesser Water Elemental (A): Treasure 10%10D30+L4 -> 20%10D30+L4; Spell1 "IceBolt,E,7" -> "Ice Bolt,E,7" (format
  only)
- `77` Water Elemental (B): Treasure 10%10D40+L5 -> 30%10D40+L5
- `78` Greater Water Elemental (C): Treasure 10%10D40+L6 -> 15%10D40+6; Spell1 "IceBlast,GM,10" -> "Ice Blast,GM,10"
  (format only)
- `79` Lesser Earth Elemental (A): Treasure 20%10D30+L4Ore -> 15%10D30+L4
- `80` Earth Elemental (B): Treasure 20%10D40+L5Ore -> 20%10D40+L5
- `81` Greater Earth Elemental (C): Treasure 15%10D40+L6Ore -> 30%10D40+5
- `82` Lesser Air Elemental (A): Treasure 10%10D30+L4 -> 15%10D30+L4
- `83` Air Elemental (B): Treasure 10%10D40+L5 -> 20%10D40+L5
- `84` Greater Air Elemental (C): Treasure 10%10D40+L6 -> 30%10D40+5
- `103` Efreeti Soldier (A): Treasure 50%10D20+L4Sword -> 30%10D40+L5
- `104` Efreeti Knight (B): Treasure 50%10D20+L4Sword -> 15%10D40+6
- `105` Efreeti Lord (C): Treasure 50%10D20+L5Sword -> 30%10D40+6
- `113` Sapphire Dragon (B): Treasure 250D12+L6 -> 300D10+L6
- `114` Ruby Dragon (C): Treasure 250D16+L6 -> 400D10+L6
- `115` Mist Hawk (A): Treasure 20D30 -> 15%10D30+L4
- `116` Storm Eagle (B): Treasure 25D30 -> 20%10D40+L5
- `117` Thunderbird (C): Treasure 30D30 -> 30%10D40+5
- `136` Young Dragon Turtle (A): Treasure 25%10D25+L4Sword -> 25%10D25+L6Sword
- `137` Dragon Turtle (B): Treasure 25%10D25+L5Spear -> 25%10D25+L6Spear
- `138` Elder Tortoise (C): Treasure 25%10D25+L5Dagger -> 25%10D25+L6Dagger
- `139` Rook (A): Treasure 30%10D25+L3Sword -> 30%10D25+L4Sword
- `140` Corbie (B): Treasure 40%10D25+L4Sword -> 40%10D25+L5Sword
- `141` Raven (C): Treasure 50%10D25+L5Sword -> 50%10D25+L6Sword
- `147` Plane Overlord (C): Treasure 40%250D12+L6 -> 40%300D10+L6
- `150` Crystal Guardian (C): Treasure 30%250D12+L6 -> 30%300D10+L6
- `198` Chaos Overlord (C): Treasure 30%250D12+L6 -> 30%300D10+L6
- `224` Blue Dragon (B): Treasure 250D12+L6 -> 300D10+L6
- `225` Red Dragon (C): Treasure 250D16+L6 -> 400D10+L6
- `410` Storm Titan (B): Treasure 250D12L5 -> 300D10L5
- `411` Blood Titan (C): Treasure 250D16+L6 -> 400D10+L6

### 4.3 Reworked families: level, HP and AC (93 rows, MM6 block 454-645)

Mostly MM6 families raised towards MM7/MM8 levels so that the per-map bands make sense: Magyar 14/25/37 →
40/50/60, Baa clerics 8/15/25 → 50/70/90, devils 30-70 → 50-120, the Terminator line 50/70/90 → 70/90/110. Level, the
HP ratios and AC are effective under MAW; the EXP values are not.

- `454` Ghast (A): Level 9 -> 13; HP 35 -> 55; AC 8 -> 14; EXP 171 -> 299; Treasure 10%5D4 -> 10%7D4; Atk1 dmg 1D7 ->
  2D7+2
- `455` Ghoul (B): Level 13 -> 17; HP 55 -> 79; AC 14 -> 20; EXP 299 -> 459; Treasure 10%7D4 -> 20%12D4; Special atk
  Paralyze -> Disease2; Atk1 dmg 2D7+2 -> 3D7+4
- `456` Revenant (C): Level 17 -> 21; HP 79 -> 107; AC 20 -> 26; EXP 459 -> 651; Treasure 25%12D4 -> 30%18D4; Atk1 dmg
  3D7+4 -> 4D7+6
- `478` Magyar (A): Level 14 -> 40; HP 61 -> 280; AC 16 -> 40; EXP 336 -> "1,565"; Treasure 5%5D10+L2Misc ->
  5%5D10+L3Misc; Atk1 dmg 3D7+3 -> 3D7+12
- `479` Magyar Soldier (B): Level 25 -> 50; HP 137 -> 400; AC 22 -> 50; EXP 875 -> "2,143"; Treasure 5%10D10+L3Misc ->
  5%10D10+L4Misc; Pref 0 -> S; Atk1 dmg 3D7+6 -> 3D7+24; Atk2 dmg 3D7+18 -> 3D7+36
- `480` Magyar Matron (C): Level 37 -> 60; HP 247 -> 540; AC 28 -> 60; EXP 1739 -> "2,787"; Treasure 10%20D10+L4Misc
  -> 10%20D10+L5Misc; Pref 0 -> S; Atk1 dmg 3D7+12 -> 3D7+36; Atk2 dmg 7D8 -> 7D12
- `484` Flying Eye (A): Level 30 -> 40; HP 180 -> 280; AC 25 -> 30; EXP 1200 -> "1,565"; Atk1 dmg 5D6 -> 7D6+15
- `485` Terrible Eye (B): Level 40 -> 50; HP 280 -> 400; AC 30 -> 35; EXP 2000 -> "2,143"; Pref 0 -> "D,S"; Special
  atk Afraid -> Affraid; Atk1 dmg 6D6 -> 8D6+20
- `486` Maddening Eye (C): Level 50 -> 60; HP 400 -> 540; AC 35 -> 40; EXP 3000 -> "2,787"; Pref 0 -> "D,S"; Atk1 dmg
  7D6 -> 9D6+25
- `490` Acolyte of Baa (A): Level 8 -> 50; HP 30 -> 400; AC 14 -> 35; EXP 144 -> "2,143"; Treasure 5%5D10+L1Mace ->
  5%20D100+L3Mace; Atk1 dmg 2D4 -> 10D6
- `491` Cleric of Baa (B): Level 15 -> 70; HP 67 -> 700; AC 18 -> 55; EXP 375 -> "3,495"; Treasure 5%10D10+L2Mace ->
  5%20D200+L4Mace; Atk1 dmg 2D4+4 -> 10D6+20; Spell1 "Harm,N,3" -> "Harm,N,20"
- `492` Priest of Baa (C): Level 25 -> 90; HP 137 -> " 1,080 "; AC 22 -> 80; EXP 875 -> "5,093"; Treasure
  10%20D10+L3Misc -> 10%30D200+L5Misc; Pref 0 -> 2; Atk1 dmg 2D4+8 -> 10D6+40; Spell1 "Flying Fist,N,5" -> "Flying
  Fist,N,14"
- `496` Agar's Pet (A): Level 13 -> 30; HP 55 -> 180; AC 13 -> 25; EXP 299 -> "1,056"; Treasure 4D20 -> 10D20; Pref 0
  -> D; Atk1 dmg 1D12 -> 3D12
- `497` Agar's Monster (B): Level 15 -> 35; HP 67 -> 280; AC 15 -> 30; EXP 375 -> "1,302"; Treasure 6D20 -> 20D20;
  Pref 0 -> D; Atk1 dmg 1D12+6 -> 4D12+9
- `498` Agar's Abomination (C): Level 17 -> 40; HP 79 -> 280; AC 17 -> 35; EXP 459 -> "1,565"; Treasure 10D20 ->
  40D20; Pref 0 -> D; Atk1 dmg 2D12+6 -> 5D12+18
- `499` Devil Captain (A): Level 30 -> 80; HP 180 -> 880; AC 25 -> 100; EXP 1200 -> "4,264"; Atk1 dmg 2D8+10 -> 5D8+5;
  Atk2 dmg 3D8 -> 3D20
- `500` Devil Master (B): Level 50 -> 100; HP 400 -> 1300; AC 35 -> 120; EXP 3000 -> "5,981"; Atk1 dmg 2D8+15 ->
  6D8+10; Atk2 dmg 4D8 -> 4D20
- `501` Devil King (C): Level 70 -> 120; HP 700 -> 1800; AC 45 -> 150; EXP 5600 -> "7,927"; Atk1 dmg 2D8+20 -> 8D8+20;
  Atk2 dmg 5D8 -> 6D20
- `502` Devil Spawn (A): Level 20 -> 50; HP 100 -> 400; AC 20 -> 50; EXP 600 -> "2,143"; Atk1 dmg 2D6+8 -> 4D6+5
- `503` Devil Worker (B): Level 40 -> 70; HP 280 -> 700; AC 30 -> 70; EXP 2000 -> "3,495"; Atk1 dmg 2D6+14 -> 5D6+10
- `504` Devil Warrior (C): Level 60 -> 90; HP 540 -> " 1,080 "; AC 40 -> 90; EXP 4200 -> "5,093"; Atk1 dmg 2D6+20 ->
  7D6+20
- `508` Flame Drake (A): Level 24 -> 32; HP 129 -> 198; AC 20 -> 30; EXP 816 -> "1,152"; Atk1 dmg 10D4 -> 15D4
- `509` Frost Drake (B): Level 28 -> 45; HP 162 -> 337; AC 25 -> 45; EXP 1064 -> "1,846"; Atk1 dmg 12D4 -> 20D4
- `510` Energy Drake (C): Level 32 -> 58; HP 198 -> 510; AC 30 -> 60; EXP 1344 -> "2,653"; Atk1 dmg 15D4 -> 25D4
- `517` Druid (A): Level 10 -> 20; HP 40 -> 100; AC 12 -> 20; EXP 200 -> 620; Treasure 5%10D10+L1Misc ->
  5%10D10+L2Misc; Pref 0 -> K; Atk1 dmg 2D4+3 -> 4D4+15
- `518` Great Druid (B): Level 16 -> 30; HP 73 -> 180; AC 16 -> 28; EXP 416 -> "1,056"; Treasure 10%20D10+L2Misc ->
  10%20D10+L3Misc; Pref 0 -> K; Atk1 dmg 2D4+6 -> 4D4+25
- `519` Grand Druid (C): Level 28 -> 40; HP 162 -> 280; AC 22 -> 36; EXP 1064 -> "1,565"; Treasure 20%50D10+L3Misc ->
  20%50D10+L4Misc; Atk1 dmg 2D4+12 -> 4D4+35
- `520` Dwarf (A): Level 10 -> 20; HP 40 -> 100; AC 6 -> 20; EXP 200 -> 620; Treasure 5%5D10+L1 -> 10%10D10L2Axe; Atk1
  dmg 4D2+4 -> 4D2+8; Atk2 dmg 8D2+8 -> 8D2+12
- `521` Dwarf Warrior (B): Level 20 -> 30; HP 100 -> 180; AC 12 -> 30; EXP 600 -> "1,056"; Treasure 10%10D10L2Axe ->
  10%20D10+L3Axe; Atk1 dmg 4D2+8 -> 4D2+12; Atk2 dmg 8D2+16 -> 8D2+18
- `522` Dwarf Lord (C): Level 30 -> 40; HP 180 -> 280; AC 20 -> 40; EXP 1200 -> "1,565"; Treasure 25%20D10+L3Axe ->
  25%20D15+L4Axe; Pref 0 -> S; Atk1 dmg 4D2+16 -> 4D2+20; Atk2 dmg 8D2+32 -> 8D2+30
- `523` Dust Devil (A): Level 16 -> 33; HP 73 -> 207; AC 10 -> 14; EXP 416 -> "1,201"; Atk1 dmg 3D6 -> 8D6
- `524` Twister (B): Level 22 -> 44; HP 114 -> 325; AC 12 -> 20; EXP 704 -> "1,788"; Atk1 dmg 5D6 -> 12D6
- `525` Air Elemental (C): Level 33 -> 55; HP 207 -> 467; AC 14 -> 30; EXP 1419 -> "2,457"; Pref 0 -> S; Atk1 dmg 8D6
  -> 16D6
- `526` Rock Beast (A): Level 25 -> 30; HP 137 -> 180; AC 20 -> 40; EXP 875 -> "1,056"; Treasure 10D20 ->
  10%15D20+L2Ring; Atk1 dmg 10D3 -> 15D3
- `527` Earth Spirit (B): Level 30 -> 40; HP 180 -> 280; AC 25 -> 50; EXP 1200 -> "1,565"; Treasure 15D20 ->
  15%20D20+L3Ring; Atk1 dmg 15D3 -> 20D3; Atk2 dmg 12D3 -> 10D3
- `528` Earth Elemental (C): Level 40 -> 50; HP 280 -> 400; AC 30 -> 60; EXP 2000 -> "2,143"; Treasure 30D20 ->
  20%30D20+L4Ring; Pref 0 -> S; Atk2 dmg 20D3 -> 15D3
- `529` Fire Beast (A): Level 13 -> 26; HP 55 -> 145; AC 12 -> 15; EXP 299 -> 872; Atk1 dmg 2D8 -> 5D8
- `530` Fire Spirit (B): Level 26 -> 39; HP 145 -> 269; AC 15 -> 18; EXP 936 -> "1,511"; Atk1 dmg 5D8 -> 8D8
- `531` Fire Elemental (C): Level 39 -> 52; HP 269 -> 425; AC 18 -> 25; EXP 1911 -> "2,267"; Pref 0 -> S; Atk1 dmg 8D8
  -> 12D8
- `535` Fighter (A): Level 14 -> 32; HP 61 -> 198; AC 18 -> 38; EXP 336 -> "1,152"; Atk1 dmg 3D3+6 -> 5D3+10
- `536` Soldier (B): Level 24 -> 40; HP 129 -> 280; AC 24 -> 46; EXP 816 -> "1,565"; Atk1 dmg 3D3+10 -> 5D3+15
- `537` Veteran (C): Level 35 -> 48; HP 227 -> 374; AC 30 -> 54; EXP 1575 -> "2,022"; Atk1 dmg 3D3+14 -> 5D3+20; Atk2
  dmg 3D3+45 -> 3D3+30
- `538` Thug (A): Level 8 -> 14; HP 30 -> 61; AC 12 -> 20; EXP 144 -> 396; Treasure 5%3D20+L1Leather ->
  5%5D20+L1Leather; Atk1 dmg 2D4+1 -> 2D4+5
- `539` Ruffian (B): Level 14 -> 20; HP 61 -> 100; AC 14 -> 24; EXP 336 -> 620; Treasure 5%5D20+L2Leather ->
  5%10D20+L2Leather; Pref 0 -> "A,S"; Atk1 dmg 2D4+5 -> 2D4+10
- `540` Brigand (C): Level 22 -> 26; HP 114 -> 145; AC 16 -> 30; EXP 704 -> 872; Treasure 10%10D20+L3Leather ->
  10%15D20+L3Leather; Pref 0 -> "A,S"; Atk1 dmg 2D4+10 -> 2D4+15; Atk2 dmg 2D4+20 -> 2D4+25
- `541` Stone Gargoyle (A): Level 16 -> 22; HP 73 -> 114; AC 18 -> 28; EXP 416 -> 701; Treasure 5%5D10+L2Amulet ->
  10%10D10+L2Amulet; Pref 0 -> "F,C"; Atk1 dmg 2D12 -> 2D12+4
- `542` Marble Gargoyle (B): Level 22 -> 33; HP 114 -> 207; AC 22 -> 40; EXP 704 -> "1,201"; Treasure
  10%10D10+L2Amulet -> 20%25D10+L3Amulet; Pref 0 -> "F,C"; Atk1 dmg 2D12+4 -> 2D12+8
- `543` Diamond Gargoyle (C): Level 33 -> 44; HP 207 -> 325; AC 26 -> 50; EXP 1419 -> "1,788"; Treasure
  20%25D10+L3Amulet -> 20%25D10+L4Amulet; Pref 0 -> "F,C"; Atk1 dmg 2D12+8 -> 2D12+12
- `544` Genie (A): Level 33 -> 55; HP 207 -> 467; AC 35 -> 55; EXP 1419 -> "1,201"; Pref 0 -> M; Atk1 dmg 8D4+8 ->
  12D4+12; Spell1 "IceBolt,M,10" -> "Ice Bolt,M,10" (format only)
- `545` Djinn (B): Level 44 -> 66; HP 325 -> 634; AC 45 -> 65; EXP 2376 -> "1,788"; Pref 0 -> M; Atk1 dmg 10D4+10 ->
  15D4+15
- `546` Efreet (C): Level 55 -> 77; HP 467 -> 824; AC 55 -> 75; EXP 3575 -> "2,457"; Pref 0 -> M; Special atk Afraid
  -> Affraid; Atk1 dmg 12D4+12 -> 20D4+20
- `547` Ghost (A): Level 9 -> 19; HP 35 -> 93; AC 25 -> 35; EXP 171 -> 580; Special atk Afraid -> Affraid; Atk1 type
  Dark -> Earth; Atk1 dmg 1D6+6 -> 3D6+6
- `548` Evil Spirit (B): Level 13 -> 29; HP 55 -> 171; AC 30 -> 45; EXP 299 -> 963; Atk1 type Dark -> Earth; Atk1 dmg
  2D6+6 -> 4D6+9
- `549` Specter (C): Level 19 -> 39; HP 93 -> 269; AC 35 -> 55; EXP 551 -> "1,458"; Atk1 type Dark -> Earth; Atk1 dmg
  3D6+6 -> 5D6+12
- `553` Guard (A): Level 11 -> 28; HP 45 -> 162; AC 16 -> 34; EXP 231 -> 963; Treasure 5%3D20+L1Armor ->
  5%5D20+L2Armor; Atk1 dmg 3D3+5 -> 3D3+10
- `554` Lieutenant (B): Level 19 -> 34; HP 93 -> 217; AC 24 -> 38; EXP 551 -> "1,251"; Treasure 5%5D20+L2Armor ->
  5%10D20+L3Armor; Atk1 dmg 3D3+10 -> 3D3+15
- `555` Captain (C): Level 33 -> 40; HP 207 -> 280; AC 32 -> 42; EXP 1419 -> "1,565"; Treasure 10%10D20+L3Armor ->
  10%20D20+L4Armor; Atk2 dmg 3D3+40 -> 3D3+30
- `562` Defender of VARN (A): Level 35 -> 55; HP 227 -> 467; AC 40 -> 50; EXP 1575 -> "2,457"; Atk2 dmg 5D6 -> 9D6
- `563` Sentinel of VARN (B): Level 55 -> 65; HP 467 -> 617; AC 50 -> 60; EXP 3575 -> "3,133"; Atk2 dmg 6D6 -> 12D6
- `564` Guardian of VARN (C): Level 65 -> 85; HP 617 -> 978; AC 60 -> 80; EXP 4875 -> "4,671"; Atk2 dmg 8D6 -> 15D6
- `565` Death Knight (A): Level 40 -> 60; HP 280 -> 540; AC 45 -> 65; EXP 2000 -> "2,787"; Treasure 10%10D100+L4Plate
  -> 10%20D100+L4Plate; Special atk Afraid -> Affraid; Atk1 dmg 4D5+20 -> 4D6+20; Atk2 dmg 4D6 -> 6D6
- `566` Doom Knight (B): Level 60 -> 80; HP 540 -> 880; AC 65 -> 85; EXP 4200 -> "4,264"; Treasure 10%20D100+L5Plate
  -> 10%40D100+L5Plate; Special atk Afraid -> Affraid; Atk1 dmg 4D5+30 -> 4D8+30; Atk2 dmg 6D6 -> 8D6
- `567` Cuisinart (C): Level 80 -> 100; HP 880 -> 1300; AC 85 -> 100; EXP 7200 -> "5,981"; Treasure 30%40D100+L6Plate
  -> 30%80D100+L6Plate; Special atk Afraid -> Affraid; Atk1 dmg 4D5+40 -> 4D10+40; Atk2 dmg 8D6 -> 12D6
- `568` Lich (A): Level 20 -> 40; HP 100 -> 280; AC 15 -> 25; EXP 600 -> "1,565"; Treasure 10%10D20+L3Misc ->
  10%30D20+L3Misc; Atk1 dmg 3D8+6 -> 5D8+20
- `569` Greater Lich (B): Level 30 -> 55; HP 180 -> 467; AC 20 -> 30; EXP 1200 -> "2,393"; Treasure 10%15D20+L4Misc ->
  10%45D20+L4Misc; Pref 0 -> "A,S"; Atk1 dmg 4D8+12 -> 6D8+28
- `570` Power Lich (C): Level 40 -> 70; HP 280 -> 700; AC 25 -> 40; EXP 2000 -> "3,495"; Treasure 30%30D20+L5Misc ->
  30%90D20+L5Misc; Atk1 dmg 5D8+20 -> 7D8+36
- `574` Medusa (A): AC 20 -> 30; EXP 1575 -> "1,302"; Pref 0 -> K; Atk1 dmg 4D4+8 -> 4D4+12
- `575` Medusa Enchantress (B): Level 40 -> 45; HP 280 -> 337; AC 25 -> 45; EXP 2000 -> "1,846"; Pref 0 -> K; Atk1 dmg
  5D4+10 -> 6D4+18
- `576` Gorgon (C): Level 45 -> 55; HP 337 -> 467; AC 30 -> 60; EXP 2475 -> "2,457"; Pref 0 -> K; Atk1 dmg 6D4+12 ->
  8D4+24
- `580` Minotaur (A): Level 39 -> 59; HP 269 -> 525; AC 30 -> 54; EXP 1911 -> "2,720"; Atk1 dmg 3D7+25 -> 4D7+25
- `581` Minotaur Mage (B): Level 59 -> 79; HP 525 -> 861; AC 35 -> 74; EXP 4071 -> "4,185"; Atk1 dmg 3D7+40 -> 4D7+40
- `582` Minotaur King (C): Level 79 -> 99; HP 861 -> 1277; AC 40 -> 94; EXP 7031 -> "5,799"; Atk1 dmg 3D7+60 -> 4D7+60
- `586` Swordsman (A): Level 10 -> 20; HP 40 -> 100; AC 10 -> 20; EXP 200 -> 620; Atk1 dmg 3D7+4 -> 3D5+8
- `587` Expert Swordsman (B): Level 17 -> 26; HP 79 -> 145; AC 15 -> 26; EXP 459 -> 872; Atk1 dmg 3D7+6 -> 3D5+11
- `588` Master Swordsman (C): Level 24 -> 32; HP 129 -> 198; AC 20 -> 32; EXP 816 -> "1,152"; Atk1 dmg 3D7+8 ->
  3D5+15; Atk2 dmg 3D7+20 -> 3D5+20
- `604` Cannibal (A): Level 6 -> 10; HP 21 -> 40; AC 5 -> 12; EXP 96 -> 263; Atk1 dmg 3D3+2 -> 3D3+6
- `605` Head Hunter (B): Level 8 -> 12; HP 30 -> 50; AC 7 -> 15; EXP 144 -> 328; Atk1 dmg 3D3+4 -> 3D3+8
- `606` Witch Doctor (C): Level 10 -> 15; HP 40 -> 67; AC 9 -> 20; EXP 200 -> 431; Atk1 dmg 3D3+6 -> 3D3+12
- `616` Cannibal (A): Level 6 -> 10; HP 21 -> 40; AC 5 -> 12; EXP 96 -> 263; Atk1 dmg 1D9+2 -> 1D9+6
- `617` Head Hunter (B): Level 8 -> 12; HP 30 -> 50; AC 7 -> 15; EXP 144 -> 328; Atk1 dmg 1D9+4 -> 1D9+8
- `618` Witch Doctor (C): Level 10 -> 15; HP 40 -> 67; AC 9 -> 20; EXP 200 -> 431; Atk1 dmg 1D9+6 -> 1D9+12
- `622` Patrol Unit (A): Level 50 -> 70; HP 400 -> 700; AC 60 -> 80; EXP 3000 -> "3,495"; Atk1 dmg 10D5+10 -> 12D5+15
- `623` Enforcer Unit (B): Level 70 -> 90; HP 700 -> " 1,080 "; AC 80 -> 100; EXP 5600 -> "5,093"; Atk1 dmg 12D5+15 ->
  20D5+20
- `624` Terminator Unit (C): Level 90 -> 110; HP 1080 -> " 1,540 "; AC 100 -> 120; EXP 9000 -> "6,926"; Atk1 dmg
  20D5+20 -> 30D5+30
- `628` Skeleton (A): Level 6 -> 20; HP 21 -> 73; AC 8 -> 30; EXP 96 -> 620; Treasure 4D6 -> 3%10D4+L2Ring; Atk1 dmg
  3D4 -> 3D4+6
- `629` Skeleton Knight (B): Level 10 -> 26; HP 40 -> 114; AC 10 -> 36; EXP 200 -> 872; Treasure 7D6 -> 3%10D8+L3Ring;
  Special atk Afraid -> Affraid; Atk1 dmg 3D4+2 -> 3D4+9
- `630` Skeleton Lord (C): Level 14 -> 32; HP 61 -> 162; AC 14 -> 42; EXP 336 -> "1,152"; Treasure 5%10D6+L2Sword ->
  3%10D12+L4Ring; Atk1 dmg 3D4+6 -> 3D4+12
- `631` Sorcerer (A): Level 25 -> 35; HP 137 -> 227; AC 14 -> 18; EXP 875 -> "1,302"; Treasure 10%10D10+L2Staff ->
  10%10D10+L3Staff; Pref 0 -> "K,A"; Atk1 dmg 9D4 -> 12D4
- `632` Magician (B): Level 35 -> 50; HP 227 -> 400; AC 18 -> 30; EXP 1575 -> "2,143"; Treasure 10%20D10+L3Staff ->
  10%20D10+L4Staff; Atk1 dmg 12D4 -> 16D4
- `633` Warlock (C): Level 50 -> 65; HP 400 -> 617; AC 30 -> 50; EXP 3000 -> "3,133"; Atk1 dmg 16D4 -> 20D4
- `643` Wolfman (A): Level 20 -> 30; HP 100 -> 180; AC 20 -> 25; EXP 600 -> "1,056"; Pref 0 -> "P,C"; Atk1 dmg 2D12+12
  -> 2D12+16
- `644` Werewolf (B): Level 30 -> 40; HP 180 -> 280; AC 25 -> 30; EXP 1200 -> "1,565"; Pref 0 -> "P,C"; Atk1 dmg
  2D12+16 -> 2D12+20
- `645` Greater Werewolf (C): Level 40 -> 50; HP 280 -> 400; AC 30 -> 35; Atk1 dmg 2D12+20 -> 2D12+24

### 4.4 EXP, preference, special-attack and dice changes without a level change (82 rows)

EXP changes here have no effect under MAW (section 2). The rows that matter are the `Pref` letters, the damage kinds
(Wyrm Water → Earth/Fire, Oozes Water → Poison) and the special-attack typos.

- `475` Archer (A): EXP 171 -> 232
- `476` Master Archer (B): EXP 551 -> 580; Pref 0 -> A
- `477` Fire Archer (C): EXP 1131 -> "1,009"; Pref 0 -> A; Spell1 % 40 -> 20
- `481` Bat (A): EXP 39 -> 67; Atk1 dmg 1D3 -> 1D3+2
- `482` Giant Bat (B): EXP 96 -> 145; Atk1 dmg 1D3+2 -> 2D3+2
- `483` Vampire Bat (C): EXP 171 -> 232; Atk1 dmg 2D3+2 -> 2D3+4
- `487` Blood Sucker (A): EXP 24 -> 43; Atk1 dmg 1D2 -> 1D2+2
- `488` Brain Sucker (B): EXP 56 -> 92; Atk1 dmg 1D2+2 -> 2D2+2
- `489` Soul Sucker (C): EXP 144 -> 202; Atk1 dmg 2D2+2 -> 2D2+4
- `493` Cobra (A): EXP 75 -> 118
- `494` King Cobra (B): EXP 200 -> 263
- `495` Queen Cobra (C): EXP 336 -> 396
- `505` Fire Lizard (A): EXP 2000 -> "1,565"
- `506` Lightning Lizard (B): EXP 3000 -> "2,143"
- `507` Thunder Lizard (C): EXP 4200 -> "2,787"
- `511` Wyrm (A): EXP 3000 -> "2,143"; Atk1 type Water -> Earth
- `512` Giant Wyrm (B): EXP 4200 -> "2,787"
- `513` Great Wyrm (C): EXP 5600 -> "3,495"; Atk1 type Water -> Fire
- `514` Red Dragon (A): EXP 7200 -> "4,264"
- `532` Water Beast (A): EXP 336 -> 396; Spell1 "IceBolt,N,3" -> "Ice Bolt,N,3" (format only)
- `533` Water Spirit (B): EXP 816 -> 785; Spell1 "IceBolt,N,5" -> "Ice Bolt,N,5" (format only)
- `534` Water Elemental (C): EXP 1656 -> "1,353"; Pref 0 -> S; Spell1 "IceBolt,N,7" -> "Ice Bolt,N,7" (format only)
- `550` Goblin (A): EXP 56 -> 92
- `551` Goblin Shaman (B): EXP 96 -> 145
- `552` Goblin King (C): EXP 200 -> 263; Pref 0 -> D
- `556` Harpy (A): EXP 336 -> 396; Pref 0 -> M
- `557` Harpy Hag (B): EXP 459 -> 504; Pref 0 -> M
- `558` Harpy Witch (C): EXP 551 -> 580; Pref 0 -> M
- `559` Hydra (A): EXP 2475 -> "1,846"
- `560` Venomous Hydra (B): EXP 3575 -> "2,457"
- `561` Colossal Hydra (C): EXP 4875 -> "3,133"
- `571` Lizard Man (A): EXP 56 -> 92
- `572` Lizard Archer (B): EXP 119 -> 173
- `573` Lizard Wizard (C): EXP 231 -> 295; Pref 0 -> A
- `577` Peasant (A): EXP 56 -> 92
- `578` Peasant (B): EXP 75 -> 118
- `579` Peasant (C): EXP 96 -> 145
- `583` Novice Monk (A): EXP 144 -> 202
- `584` Initiate Monk (B): EXP 416 -> 467
- `585` Master Monk (C): EXP 999 -> 917; Spell1 "IceBolt,M,6" -> "Ice Bolt,M,6" (format only)
- `589` Ooze (A): EXP 264 -> 328; Atk1 type Water -> Pois
- `590` Acidic Ooze (B): EXP 504 -> 542; Atk1 type Water -> Pois; Atk1 dmg 3D6 -> 2D6
- `591` Corrosive Ooze (C): EXP 875 -> 828; Atk1 type Water -> Pois; Atk1 dmg 5D6 -> 3D6
- `592` Ogre (A): EXP 375 -> 431
- `593` Ogre Raider (B): EXP 600 -> 620
- `594` Ogre Chieftain (C): EXP 1064 -> 963
- `595` Peasant (A): EXP 11 -> 21
- `596` Peasant (B): EXP 24 -> 43
- `597` Peasant (C): EXP 39 -> 67
- `598` Peasant (A): EXP 11 -> 21
- `599` Peasant (B): EXP 24 -> 43
- `600` Peasant (C): EXP 39 -> 67
- `601` Cutpurse (A): EXP 39 -> 67
- `602` Bounty Hunter (B): EXP 75 -> 118
- `603` Assassin (C): EXP 119 -> 173
- `607` Peasant (A): EXP 11 -> 21
- `608` Peasant (B): EXP 24 -> 43
- `609` Peasant (C): EXP 39 -> 67
- `610` Apprentice Mage (A): EXP 24 -> 43
- `611` Journeyman Mage (B): EXP 96 -> 145; Spell1 "IceBolt,N,1" -> "Ice Bolt,N,1" (format only)
- `612` Mage (C): EXP 200 -> 263
- `613` Follower of Baa (A): EXP 39 -> 67
- `614` Mystic of Baa (B): EXP 75 -> 118
- `615` Fanatic of Baa (C): EXP 119 -> 173
- `619` Common Rat (A): EXP 24 -> 43
- `620` Large Rat (B): EXP 56 -> 92
- `621` Giant Rat (C): EXP 96 -> 145
- `625` Sea Serpent (A): EXP 1064 -> 963; Atk1 dmg 2D20+25 -> 1D20+25
- `626` Sea Monster (B): EXP 1656 -> "1,353"; Atk1 dmg 2D20+35 -> 1D20+35
- `627` Sea Terror (C): EXP 2784 -> 2,022; Special atk Afraid -> Affraid; Atk1 dmg 2D20+45 -> 1D20+45
- `634` Spider (A): EXP 75 -> 118
- `635` Giant Spider (B): EXP 144 -> 202
- `636` Huge Spider (C): EXP 264 -> 328
- `637` Thief (A): EXP 144 -> 202
- `638` Burglar (B): EXP 264 -> 328
- `639` Rogue (C): EXP 504 -> 542
- `640` Titan (A): EXP 4875 -> "3,133"; Pref 0 -> F
- `515` Blue Dragon (B): HP 1080 -> " 1,080 " (format only); EXP 9000 -> "5,093"; Treasure 250D12+L6 -> 300D10+L6
- `516` Gold Dragon (C): HP 1300 -> " 1,300 " (format only); EXP 11000 -> "5,981"; Treasure 250D16+L6 -> 400D10+L6
- `641` Noble Titan (B): EXP 6375 -> "3,872"; Treasure 250D12+L5 -> 300D10+L5; Pref 0 -> F
- `642` Supreme Titan (C): HP 1187 -> " 1,187 " (format only); EXP 9975 -> "5,530"; Treasure 250D16+L6 -> 400D10+L6;
  Pref 0 -> F
- `652` Reactor (A): Special 0 -> ''

### 4.5 Cosmetic only (2 rows)

- `244` Sprite (A): Spell1 "IceBolt,E,4" -> "Ice Bolt,E,4" (format only)
- `246` Water Elemental (C): Spell1 "IceBlast,G,12" -> "Ice Blast,G,12" (format only)

## 5. `mapstats.txt`: every changed row

Columns: `Treasure lvl` (`Tres 0-6`), `MonN pic` (the spawn picture the engine uses), `MonN label` (a display
column), `MonN dif` (spawn difficulty 1-5, the A/B/C mix), `MonN count` (`#`, spawn count range).

### 5.1 Treasure level set to 6 (129 maps)

Every listed map changes its treasure level from the value shown to 6. The other 78 rows (46-50, 71, 97, 130, 132,
137-205) were already 6, so under MAW every map has treasure level 6; MAW's loot roller then rescales items by level.

| id | file | name | base | id | file | name | base |
|---|---|---|---|---|---|---|---|
| 1 | out01.odm | Dagger Wound Island | 0 | 72 | 7out13.odm | Tatalia | 2 |
| 2 | out02.odm | Ravenshore | 1 | 73 | out14.odm | Avlee | 2 |
| 3 | out03.odm | Alvar | 1 | 74 | 7out15.odm | Shoals | 1 |
| 4 | out04.odm | Ironsand Desert | 2 | 75 | d01.blv | The Erathian Sewers | 1 |
| 5 | out05.odm | Garrote Gorge | 2 | 76 | d02.blv | The Maze | 5 |
| 6 | out06.odm | Shadowspire | 2 | 77 | d03.blv | Castle Gloaming | 4 |
| 7 | out07.odm | Murmurwoods | 3 | 78 | d04.blv | The Temple of Baa | 3 |
| 8 | out08.odm | Ravage Roaming | 3 | 79 | 7d05.blv | The Arena | 1 |
| 9 | elema.odm | Plane of Air | 4 | 80 | 7d06.blv | The Temple of the Moon | 0 |
| 10 | eleme.blv | Plane of Earth | 4 | 81 | 7d07.blv | Thunderfist Mountain | 4 |
| 11 | elemf.odm | Plane of Fire | 4 | 82 | 7d08.blv | The Tularean Caves | 1 |
| 12 | elemw.odm | Plane of Water | 4 | 83 | 7d09.blv | The Titans' Stronghold | 5 |
| 13 | out13.odm | Regna | 4 | 84 | 7d10.blv | The Breeding Zone | 1 |
| 14 | pbp.odm | Plane Between Planes | 5 | 85 | 7d11.blv | The Walls of Mist | 1 |
| 15 | out15.odm | Tutorial | 0 | 86 | 7d12.blv | Clanker's Laboratory | 4 |
| 16 | d05.blv | Abandoned Temple | 1 | 87 | 7d13.blv | Zokarr's Tomb | 2 |
| 17 | d06.blv | Pirate Outpost | 1 | 88 | 7d14.blv | The School of Sorcery | 2 |
| 18 | d07.blv | Smuggler's Cove | 2 | 89 | 7d15.blv | Watchtower 6 | 3 |
| 19 | d08.blv | Dire Wolf Den | 2 | 90 | 7d16.blv | The Wine Cellar | 3 |
| 20 | d09.blv | Merchant House of Alvar | 3 | 91 | 7d17.blv | The Tidewater Caverns | 2 |
| 21 | d10.blv | Escaton's Crystal | 5 | 92 | 7d18.blv | Lord Markham's Manor | 2 |
| 22 | d11.blv | Wasp Nest | 2 | 93 | 7d19.blv | Grand Temple of the Moon | 3 |
| 23 | d12.blv | Ogre Fortress | 2 | 94 | 7d20.blv | The Mercenary Guild | 4 |
| 24 | d13.blv | Troll Tomb | 3 | 95 | 7d21.blv | White Cliff Cave | 0 |
| 25 | d14.blv | Cyclops Larder | 4 | 96 | 7d22.blv | The Hall under the Hill | 1 |
| 26 | d15.blv | Chain of Fire | 3 | 98 | 7d24.blv | Stone City | 1 |
| 27 | d16.blv | Dragon Hunter's Camp | 3 | 99 | 7d25.blv | Celeste | 3 |
| 28 | d17.blv | Dragon Cave | 5 | 100 | 7d26.blv | The Pit | 3 |
| 29 | d18.blv | Naga Vault | 3 | 101 | 7d27.blv | Colony Zod | 5 |
| 30 | d19.blv | Necromancers' Guild | 4 | 102 | 7d28.blv | The Dragon's Lair | 1 |
| 31 | d20.blv | Mad Necromancer's Lab | 4 | 103 | 7d29.blv | Castle Harmondale | 0 |
| 32 | d21.blv | Vampire Crypt | 3 | 104 | 7d30.blv | Castle Lambent | 4 |
| 33 | d22.blv | Temple of the Sun | 3 | 105 | 7d31.blv | Fort Riverstride | 1 |
| 34 | d23.blv | Druid Circle | 4 | 106 | 7d32.blv | Castle Navan | 2 |
| 35 | d24.blv | Balthazar Lair | 4 | 107 | 7d33.blv | Castle Gryphonheart | 2 |
| 36 | d25.blv | Barbarian Fortress | 5 | 108 | 7d34.blv | The Red Dwarf Mines | 1 |
| 37 | d26.blv | The Crypt of Korbu | 4 | 109 | 7d35.blv | Nighon Tunnels | 2 |
| 38 | d27.blv | Castle of Air | 5 | 110 | 7d36.blv | Tunnels to Eeofol | 5 |
| 39 | d28.blv | Tomb of Lord Brinne | 2 | 111 | 7d37.blv | The Haunted Mansion | 2 |
| 40 | d29.blv | Castle of Fire | 5 | 112 | mdk01.blv | Barrow VII | 1 |
| 41 | d30.blv | War Camp | 5 | 113 | mdk02.blv | Barrow IV | 1 |
| 42 | d31.blv | Pirate Stronghold | 4 | 114 | mdk03.blv | Barrow II | 1 |
| 43 | d32.blv | Abandoned Pirate Keep | 4 | 115 | mdk04.blv | Barrow XIV | 1 |
| 44 | d33.blv | Passage Under Regna | 4 | 116 | mdk05.blv | Barrow III | 1 |
| 45 | d34.blv | Small Sub Pen | 4 | 117 | mdt01.blv | Barrow IX | 1 |
| 51 | d40.blv | Uplifted Library | 4 | 118 | mdt02.blv | Barrow VI | 1 |
| 52 | d41.blv | Dark Dwarf Compound | 4 | 119 | mdt03.blv | Barrow I | 1 |
| 53 | d42.blv | Arena | 1 | 120 | mdt04.blv | Barrow VIII | 1 |
| 54 | d43.blv | Ancient Troll Home | 3 | 121 | mdt05.blv | Barrow XIII | 1 |
| 55 | d44.blv | Grand Temple of Eep | 3 | 122 | mdr01.blv | Barrow X | 1 |
| 56 | d45.blv | Chapel of Eep | 2 | 123 | mdr02.blv | Barrow XII | 1 |
| 57 | d46.blv | Church of Eep | 2 | 124 | mdr03.blv | Barrow V | 1 |
| 58 | d47.blv | Old Loeb's Cave | 4 | 125 | mdr04.blv | Barrow XI | 1 |
| 59 | d48.blv | Ilsingore's Cave | 4 | 126 | mdr05.blv | Barrow XV | 1 |
| 60 | d49.blv | Yaardrake's Cave | 5 | 127 | mdt09.blv | Wromthrax's Cave | 3 |
| 61 | d50.blv | NWC | 0 | 128 | mdt10.blv | William Setag's Tower | 2 |
| 62 | 7out01.odm | Emerald Island | 0 | 129 | mdt11.blv | The Hidden Tomb | 4 |
| 63 | 7out02.odm | Harmondale | 0 | 131 | mdt14.blv | The Bandit Caves | 1 |
| 64 | 7out03.odm | Erathia | 1 | 133 | t01.blv | Temple of the Light | 5 |
| 65 | 7out04.odm | The Tularean Forest | 1 | 134 | t02.blv | Temple of the Dark | 5 |
| 66 | 7out05.odm | Deyja | 2 | 135 | t03.blv | Grand Temple of the Sun | 3 |
| 67 | 7out06.odm | The Bracada Desert | 2 | 136 | t04.blv | The Hall of the Pit | 2 |
| 68 | out09.odm | Evenmorn Island | 2 | 206 | BrBase.blv | Basement of the Breach | 1 |
| 69 | out10.odm | Mount Nighon | 3 | 207 | 7nwc.blv | The Strange Temple | 1 |
| 70 | out11.odm | The Barrow Downs | 2 |  | | |  |

### 5.2 Monster pool, count or difficulty changes (38 maps)

These change which families spawn (and therefore which families are "native" and pinned to the
[map_levels.yml](data/map_levels.yml) bands), how many, and the tier mix.

- `1` out01.odm Dagger Wound Island: Mon2 count 1-3 -> 2-5; Mon3 pic Couatl (winged snake) -> Wimpy Pirate Crossbowman
  (Female); Mon3 label Couatl (winged snake) -> Wimpy Pirate Crossbowman (Female)
- `112` mdk01.blv Barrow VII: Mon1 pic AGog -> Zombie; Mon1 label AGog -> Zombie; Mon2 pic Rat -> AGog; Mon2 label Rat
  -> AGog
- `113` mdk02.blv Barrow IV: Mon1 pic Skeleton Warrior -> Zombie; Mon1 label Skeleton Warrior -> Zombie; Mon2 pic Bat
  -> Skeleton Warrior; Mon2 label Bat -> Skeleton Warrior
- `114` mdk03.blv Barrow II: Mon1 pic Zombie -> Ghoul; Mon1 label Zombie -> Ghoul; Mon2 pic Rat -> Zombie; Mon2 label
  Rat -> Zombie
- `115` mdk04.blv Barrow XIV: Mon1 pic Ghoul -> Wight; Mon1 label Ghoul -> Wight; Mon2 pic Bat -> Ghoul; Mon2 label
  Bat -> Ghoul
- `116` mdk05.blv Barrow III: Mon1 pic Ghoul -> Wight; Mon1 label Ghoul -> Wight; Mon2 pic Rat -> Ghoul; Mon2 label
  Rat -> Ghoul
- `117` mdt01.blv Barrow IX: Mon1 pic AGog -> Skeleton Warrior; Mon1 label AGog -> Skeleton Warrior; Mon2 pic Bat ->
  AGog; Mon2 label Bat -> AGog
- `118` mdt02.blv Barrow VI: Mon2 pic Rat -> Ghoul; Mon2 label Rat -> Ghoul
- `119` mdt03.blv Barrow I: Mon2 pic Bat -> Ghoul; Mon2 label Bat -> Ghoul
- `120` mdt04.blv Barrow VIII: Mon2 pic Rat -> Ghoul; Mon2 label Rat -> Ghoul
- `121` mdt05.blv Barrow XIII: Mon1 pic Ghoul -> Wight; Mon1 label Ghoul -> Wight; Mon2 pic Bat -> Ghoul; Mon2 label
  Bat -> Ghoul
- `122` mdr01.blv Barrow X: Mon1 pic AGog -> Skeleton Warrior; Mon1 label AGog -> Skeleton Warrior; Mon2 pic Rat ->
  AGog; Mon2 label Rat -> AGog
- `123` mdr02.blv Barrow XII: Mon1 pic Skeleton Warrior -> Zombie; Mon1 label Skeleton Warrior -> Zombie; Mon2 pic Bat
  -> Skeleton Warrior; Mon2 label Bat -> Skeleton Warrior
- `124` mdr03.blv Barrow V: Mon1 pic Skeleton Warrior -> Zombie; Mon1 label Skeleton Warrior -> Zombie; Mon2 pic Rat
  -> Skeleton Warrior; Mon2 label Rat -> Skeleton Warrior
- `125` mdr04.blv Barrow XI: Mon1 pic Zombie -> Ghoul; Mon1 label Zombie -> Ghoul; Mon2 pic Bat -> Zombie; Mon2 label
  Bat -> Zombie
- `126` mdr05.blv Barrow XV: Mon1 pic Zombie -> Ghoul; Mon1 label Zombie -> Ghoul; Mon2 pic Rat -> Zombie; Mon2 label
  Rat -> Zombie
- `143` outc1.odm Frozen Highlands: Mon2 pic Barbarian -> BArcher; Mon2 label Barbarian -> BArcher; Mon3 pic BArcher
  -> Ogre; Mon3 label BArcher -> Ogre
- `155` 6d04.blv Hall of the Fire Lord: Mon1 dif 4 -> 5; Mon2 dif 2 -> 1; Mon2 count 2-4 -> 1-3
- `156` 6d05.blv Snergle's Caverns: Mon2 pic BBat -> Cockatrice; Mon2 label BBat -> Agar's Pet
- `157` 6d06.blv Dragoons' Caverns: Mon1 label FighterLeath -> Thug; Mon2 pic FighterChain -> Nobleman; Mon2 label
  FighterChain -> Nobleman; Mon2 dif 3 -> 1
- `158` 6d07.blv Silver Helm Outpost: Mon1 pic Nobleman -> PeasantF3; Mon1 label Nobleman -> Cutpurse; Mon1 dif 3 ->
  5; Mon1 count 3-4 -> 3-8; Mon2 pic BMonk -> BThief; Mon2 label BMonk -> BThief; Mon2 dif 3 -> 4; Mon2 count 3-4 ->
  3-5; Mon3 pic Guard -> BMonk; Mon3 label Guard -> BMonk; Mon3 dif 3 -> 1; Mon3 count 2-4 -> 2-3
- `159` 6d08.blv Shadow Guild: Mon1 count 2-4 -> 4-6; Mon2 pic PeasantF3 -> FighterLeath; Mon2 label PeasantF3 ->
  Thug; Mon2 dif 5 -> 3
- `160` 6d09.blv Snergle's Iron Mines: Mon1 dif 4 -> 3; Mon2 pic BOoze -> BGargoyle; Mon2 label BOoze -> Stone
  BGargoyle; Mon2 dif 4 -> 3; Mon3 pic Demon -> ElemEarth; Mon3 label Demon -> Earth Elemental
- `161` 6d10.blv Dragoons' Keep: Mon1 pic FighterChain -> Nobleman; Mon1 label FighterChain -> Swordsman; Mon1 dif 3
  -> 4; Mon2 pic BRat -> Guard; Mon2 label BRat -> Guard; Mon2 dif 5 -> 2; Mon2 count 4-8 -> 2-4
- `162` 6d11.blv Corlagon's Estate: Mon1 dif 4 -> 3
- `163` 6d12.blv Silver Helm Stronghold: Mon1 label Nobleman -> Swordsman; Mon2 label FighterChain -> Fighter; Mon2
  count 3-6 -> 3-5; Mon3 dif 3 -> 1
- `165` 6d14.blv Tomb of Ethric the Mad: Mon1 dif 4 -> 1; Mon2 count 4-7 -> 6-9; Mon3 count 2-3 -> 3-4
- `166` 6d15.blv Icewind Keep: Mon2 pic Guard -> Nobleman; Mon2 label Guard -> Nobleman; Mon2 dif 4 -> 2; Mon2 count
  3-5 -> 2-4
- `167` 6d16.blv Warlord's Fortress: Mon1 pic FighterLeath -> Guard; Mon1 label FighterLeath -> Guard; Mon1 count 2-4
  -> 4-6; Mon2 label FighterChain -> Fighter; Mon2 count 2-4 -> 3-5; Mon3 label KnightPlate -> Death Knight; Mon3 dif
  5 -> 1; Mon3 count 2-4 -> 2-3
- `168` 6d17.blv Lair of the Wolf: Mon3 pic BOoze -> BDragonFly; Mon3 label BOoze -> Flame Drake; Mon3 dif 5 -> 1;
  Mon3 count 5-7 -> 2-3
- `172` 6t1.blv Temple of Baa: Mon1 pic Cleric -> BMonk; Mon1 label Cleric -> BMonk
- `173` 6t2.blv Temple of the Fist: Mon1 dif 3 -> 4; Mon1 count 2-4 -> 3-4; Mon2 count 3-5 -> 5-8
- `175` 6t4.blv Temple of the Sun: Mon1 pic BMonk -> Druidess; Mon1 label BMonk -> Druid; Mon1 dif 4 -> 1
- `176` 6t5.blv Temple of the Moon: Mon1 label Druidess -> Druid; Mon2 count 3-5 -> 9-15
- `178` 6t7.blv Superior Temple of Baa: Mon1 label Cleric -> Acolyte of Baa; Mon1 dif 5 -> 1; Mon1 count 3-6 -> 3-5;
  Mon2 label Druidess -> Druid; Mon2 dif 4 -> 5; Mon2 count 3-6 -> 3-4; Mon3 dif 3 -> 5
- `181` cd2.blv Castle Darkmoor: Mon2 label BBeholder -> Flying Eye; Mon3 pic Ogre -> KnightPlate; Mon3 label Ogre ->
  KnightPlate; Mon3 dif 5 -> 2
- `183` sewer.blv Free Haven Sewer: Mon2 pic Cleric -> BMonk; Mon2 label Cleric -> BMonk
- `200` zdtl02.blv pending: Mon1 pic 0 -> FighterChain; Mon1 label 0 -> Fighter; Mon1 dif 1 -> 5; Mon1 count 1-1 ->
  3-6; Mon2 pic 0 -> Sorcerer; Mon2 label 0 -> Sorcerer; Mon2 dif 1 -> 3; Mon2 count 1-4 -> 3-4; Mon3 pic 0 ->
  Barbarian; Mon3 label 0 -> Magyar; Mon3 count 1-4 -> 2-3

### 5.3 Label column only (30 maps, MM6)

Only the display column changes (MM6 sprite names replaced by monster names); no effect in either engine.

- `137` outa1.odm Sweet Water: Mon1 label Demon -> Devil Spawn; Mon2 label DemonFly -> Devil Captain
- `138` outa2.odm Paradise Valley: Mon1 label DragonCover -> Red Dragon
- `139` outa3.odm Hermit's Isle: Mon3 label SeaSerpent -> Sea Serpent
- `140` outb1.odm Kriegspire: Mon2 label ElemEarth -> Earth Elemental; Mon3 label BDragonFly -> Flame Drake
- `141` outb2.odm Blackshire: Mon1 label DragonCave -> Fire Lizard; Mon3 label ElemAir -> Air Elemental
- `142` outb3.odm Dragonsand: Mon1 label DragonLand -> Wyrm; Mon2 label DragonCover -> Red Dragon; Mon3 label
  DragonCave -> Fire Lizard
- `144` outc2.odm Free Haven: Mon2 label PeasantM2 -> Apprentice Mage
- `146` outd1.odm Silver Cove: Mon1 label Druidess -> Druid; Mon2 label BGargoyle -> Stone BGargoyle
- `147` outd2.odm Bootleg Bay: Mon1 label PeasantM4 -> Cannibal; Mon2 label PeasantF4 -> Cannibal; Mon3 label
  LizardArch -> Lizardman
- `148` outd3.odm Castle Ironfist: Mon1 label LizardArch -> Lizardman; Mon3 label PeasantM3 -> Hermit
- `149` oute1.odm Eel Infested Waters: Mon1 label SeaSerpent -> Sea Serpent; Mon2 label Cockatrice -> Agar's Pet; Mon3
  label ElemWater -> Water Elemental
- `150` oute2.odm Misty Islands: Mon1 label PeasantM3 -> Hermit; Mon2 label PeasantF3 -> Cutpurse
- `151` oute3.odm New Sorpigal: Mon2 label PeasantM2 -> Apprentice Mage
- `152` 6d01.blv Goblinwatch: Mon1 label BRat -> Common BRat
- `154` 6d03.blv Shadow Guild Hideout: Mon2 label FighterLeath -> Thug
- `164` 6d13.blv The Monolith: Mon1 label Druidess -> Druid; Mon2 label ElemEarth -> Earth Elemental; Mon3 label
  ElemWater -> Water Elemental
- `169` 6d18.blv Gharik's Forge: Mon2 label ElemFire -> Fire Elemental; Mon3 label ElemFire -> Fire Elemental
- `170` 6d19.blv Agar's Laboratory: Mon1 label BBeholder -> Flying Eye; Mon2 label Cockatrice -> Agar's Pet
- `171` 6d20.blv Caves of the Dragon Riders: Mon1 label KnightPlate -> Death Knight; Mon2 label DragonLand -> Wyrm
- `174` 6t3.blv Temple of Tsantsa: Mon1 label PeasantM4 -> Cannibal; Mon2 label PeasantF4 -> Cannibal
- `177` 6t6.blv Supreme Temple of Baa: Mon1 label Cleric -> Acolyte of Baa; Mon2 label Demon -> Devil Spawn; Mon3
  label ElemFire -> Fire Elemental
- `179` 6t8.blv Temple of the Snake: Mon2 label PeasantM1 -> Peasant; Mon3 label DragonCover -> Red Dragon
- `180` cd1.blv Castle Alamos: Mon2 label Barbarian -> Magyar; Mon3 label ElemAir -> Air Elemental
- `182` cd3.blv Castle Kriegspire: Mon2 label Cockatrice -> Agar's Pet; Mon3 label BDragonFly -> Fire Drake
- `184` pyramid.blv Tomb of VARN: Mon1 label Jackalman -> Defender of Varn; Mon3 label BRobot -> Patrol Unit
- `185` oracle.blv Oracle of Enroth: Mon1 label PeasantM1 -> Peasant
- `186` sci-fi.blv Control Center: Mon1 label BRobot -> Patrol Unit
- `187` hive.blv The Hive: Mon1 label Demon -> Devil Spawn; Mon2 label DemonFly -> Devil Captain; Mon3 label
  DemonQueen -> Devil Queen
- `189` zddb01.blv Dragon's Lair: Mon1 label DragonCover -> Red Dragon
- `202` zdwj02.blv Devil Outpost: Mon1 label Demon -> Devil Spawn

### 5.4 Rename (1 map)

- `153` 6d02.blv Abandoned Temple: Name Abandoned Temple -> The Abandoned Temple

## 6. Not covered

- The other `zMaw.T.lod` tables (`ITEMS.txt`, `rnditems.txt`, `SPCITEMS.TXT`, `POTION.TXT`, `POTNOTES.TXT`,
  `class.txt`) and `Data/Tables/*.txt`: see [ITEMS.md](ITEMS.md) and
  [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md).
- Runtime edits to the same tables, which never touch the files: `AdjustMonsterDensity` rewrites
  `Mon{1..3}{Low,Hi,Dif}` on every load, map 96's pool is changed in code, the Randomizer shuffles pools,
  `recalculateMonsterTable` rewrites 651 monster rows on every load (see [data/difficulty.yml](data/difficulty.yml) and
  [data/monster_scaling.yml](data/monster_scaling.yml)).
- Whether the original MM8 parser accepts `Affraid` and the `+6` treasure cells was not verified against the binary.
