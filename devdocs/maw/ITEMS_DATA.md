# MAW item data: tables, patches, tooltip and item record

Status: investigation draft (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: MAW at commit `ef23ee17` (`/home/pjasicek/github/Maw-Mod-MMMerge`); MAW paths
are relative to its `Scripts/` folder unless they start with `Data/`. Base MMMerge is
`reference/mmerge_data_forus/Data/mmmerge.T.lod/`, which is what OpenYAMM's tables were imported from. This document
completes [ITEMS.md](ITEMS.md) with exact data; it does not repeat the rarity distribution ([RANDOMS.md](RANDOMS.md)) or
crafting ([CRAFTING.md](CRAFTING.md)).

## 1. Files

| File | Contents |
|---|---|
| [data/loot.yml](data/loot.yml) | Every loot constant and formula: loot tier, drop level, rarity bands and multipliers, upgrade cascade and pity, boss rules, enchant count, type roll, skill-enchant chance, strength curve, ranges, slot multipliers, read transforms, difficulty power, item power rolls, weapon damage and armour AC model with ladder rungs, attack speed, level requirement, Celestial rescaling, monster drops, gold, value, shops and reroll, loot filter, seeding. Computed tables: enchant strength by tier and rarity, level requirement by drop level, weapon damage by item power for every base weapon, armour AC by item power for every base armour piece, attack speed by item level |
| [data/legendary_affixes.yml](data/legendary_affixes.yml) | The 25 affixes (ids 11-35): text, exact effect and numbers, every `file:line` where each applies |
| [data/artifacts.yml](data/artifacts.yml) | Artifact rules and 103 drop-list entries plus 30 rule-only entries, keyed by OpenYAMM item id: budget coefficients, flat values, base multiplier, on-hit, drain and leech, wear requirements, buffs, immunities, attack speed, regeneration, spell bonus, id checks against our `items.txt` |
| [data/special_enchants.yml](data/special_enchants.yml) | Special-enchant pools, scaling, damage formula, leech and immunity rules, all 80 specials with MAW weights, base differences, tooltip text and MAW behaviour; damage-special ranges by item power |

All YAML files start with `# draft extracted from MAW ef23ee17`, parse with PyYAML, and keep lines within 120
characters. The computed tables come from running MAW's own functions (`Modules/MawCore/ItemLevel.lua`,
`Formulas.lua`, `Estimates.lua`, and slices of `General/zzMaw-Items.lua` and `General/zzMAW-Skills.lua`) under
Lua 5.4 against MAW's `ITEMS.txt`, with the init-time table edits applied. The scratch harness is not part of the
repository.

## 2. Findings from the extraction

Facts that are new relative to ITEMS.md, or that a port must decide on. Each is detailed in the YAML named.

1. **Weapon damage stops at item power 100; armour AC does not.** `getWeaponDamageForLevel` reads
   `ItemLevel.PowerFor(level)`, which is capped at 100 (`ItemLevel.lua:18-21`). Primordial drops reach power 120
   and the Crafting Cube 120, but a weapon at 120 deals exactly what it deals at 100. `collectArmorAC` reads
   `MaxCharges` directly (`zzMaw-Items.lua:2697-2700`), so armour keeps growing to 120 and beyond (loot.yml
   `weapon_damage`, `armour_ac`).
2. **Only the dice count of a weapon matters.** The table's dice sides and Mod2 are ignored for damage
   (`GetWeaponDamageRows`, `zzMaw-Items.lua:4585-4593`). The count only moves the minimum. With six dice on a
   one-handed item (1648 Stellar Bow) the rounded sides collapse to 1 at low power: `+8 14-14`.
3. **Ladder rungs come from contiguous unidentified names.** MM6 and MM7 families of three sit on rungs 1, 3.5
   and 6; singletons on 3.5. Item 67 is renamed "Mace" and 804 "Longsword" first (`zzMaw-Items.lua:406-407`).
4. **Clubs (Skill 39) have no base recovery**: attack speed 1.0 at every item level, while every other weapon
   slows from 0.75x to 1.95x of its base (loot.yml `attack_speed`). The tooltip rounds to tens: an axe at item
   level 0 prints 1.1, not 1.05.
5. **Rings never get a resistance as their second enchant**: enchant 2 resistances are re-rolled to 1..10 on
   every item (`zzMaw-Items.lua:1307-1310`). The first-enchant re-roll for non-rings is unreachable, because
   non-rings never roll 11-16.
6. **The Dodge swap is on Chain and Plate**, skills 10 and 11, and the Unarmed swap skips staves
   (`zzMaw-Items.lua:1176-1181`).
7. **The x1.5 for hats and crowns is applied on read**, not at generation (`collectEnchant`
   `zzMaw-Items.lua:2728-2730`, tooltip `Tooltip.lua:261-263`).
8. **Item skill bonuses are capped at twice the base skill** (`zzMaw-Items.lua:2605-2611`). This covers base
   skill enchants, school specials, meditation specials and artifact skills, and means an untrained skill gains
   nothing from items.
9. **Engine stat bonuses from items are zeroed** (`events.CalcStatBonusByItems`, `zzMaw-Items.lua:2566-2584`).
   Specials whose effect the engine delivered as a stat or skill bonus lose it: 25 "of Power" (+5 Level, now
   death and eradication immunity), 60 Monks', 61 Thieves', 67-70. Their slot weights are 0, so only legacy items
   or table-placed items carry them. Special 62 is re-added explicitly.
10. **Damage specials scale with an expected-character model**, not with the wearer: `getWeaponLevelDamage` uses
    the balance model's skill, stats and Might at the item's level, so the numbers depend on difficulty
    (special_enchants.yml `damage_specials_by_item_power`).
11. **Value bugs**: enchant 2 HP/SP misses `*100` and is fed the multiplied value; special 80 (Divines') never
    adds its value because `Bonus2 <= SpcItemsTxt.high` mixes 1-based and 0-based indices
    (`zzMaw-Items.lua:1936-1940`, `:1950`).
12. **Tooltip bug**: a second-enchant resistance is shown with +10 (`Tooltip.lua:293`) although
    `collectEnchant` adds +10 to the first enchant only (`zzMaw-Items.lua:2746-2748`).
13. **Carnage**: the text says half damage; the code multiplies every Carnage arrow hit by 0.25
    (`Modules/MawCore/Damage.lua:496-498`).
14. **Static map drop level uses the sum** of the map's Low, Mid and High levels when the map declares monsters
    (`zzMaw-Monsters.lua:1907-1909`, then x7/8). It is only a fallback (the median native monster level is used
    when known), but it looks like a mean was intended.
15. **Legendary 21 is not melee-only** (`Damage.lua:1063-1074`), legendary 13 blocks conditions from any
    source, and the legendary 11 skip uses `return`, which also skips the Shaman spell bonus on AoE hits.
16. **The loot filter cannot filter Legendary or Celestial**, and it only converts corpse drops and chest items,
    not ground items.
17. **`equipSlotWeights`** (`zzMaw-Items.lua:4375-4388`) is defined and never read: base enchant types are
    uniform.
18. **The shop reroll strength bump is cumulative**: before each of the 12 slots, `random(1,18) < MMLVL % 18`
    raises the strength for that slot and every later slot (`zzMaw-Items.lua:3967-3970`).
19. **Artifacts** (from artifacts.yml): the drop list has 104 entries and 103 unique ids (533 twice, 532
    probably meant); 98 is the number of budget entries; the artifact pity counters are stored by list position;
    "Vampiric" artifacts do nothing; MM6/MM7 artifact armour borrows the reference AC of the last row with the
    same unidentified name ("Artifact"/"Relic"), so its level growth is arbitrary.
20. **`vars.extraShown` is sticky**: once any ALT preview has been shown, the hint "Press alt to show craftable
    stats" never appears again in that save (`Tooltip.lua:330`, `:463`, `:465-469`).

## 3. Table diffs and patches

Full row and cell diffs of MAW's `ITEMS.txt`, `rnditems.txt` and `SPCITEMS.TXT` (from `Data/zMaw.T.lod`) against
base MMMerge, and the same changes as patches onto OpenYAMM's `items.txt`, `random_items.txt` and
`special_item_enchants.txt`. Wide tables exceed the usual line length.

Generated from the extracted tables; values are cell values after the trimming OpenYAMM applies
(`getCell`: ASCII whitespace only). Windows-1252 bytes are shown as `\x85`, `\x92`.
Notes cells are shown as word diffs: `[-removed-]{+added+}`, unchanged runs shortened with `...`.
"Commit" is the first MAW commit of `Data/zMaw.T.lod` from which the row (or cell) has held its final MAW value.

### 3.1 Provenance

| Set | File | md5 | Lines |
|---|---|---|---|
| MAW ef23ee17 `Data/zMaw.T.lod` | ITEMS.txt | `096329ce9cd3740a6342a3d686ab5bcd` | 2202 |
| MAW ef23ee17 `Data/zMaw.T.lod` | rnditems.txt | `76b6017b2df8386f12b2ee5c970a14f5` | 2212 |
| MAW ef23ee17 `Data/zMaw.T.lod` | SPCITEMS.TXT | `aca9567a415e5777e5f80cd9286c8608` | 94 |
| Base `reference/mmerge_data_forus/Data/mmmerge.T.lod/` | ITEMS.txt | `2a73f62af2d434e1f51e66e7bd1d70e6` | 2203 |
| Base `reference/mmerge_data_forus/Data/mmmerge.T.lod/` | rnditems.txt | `f17af6ab0e278ed7d847274f2e4e3435` | 2213 |
| Base `reference/mmerge_data_forus/Data/mmmerge.T.lod/` | SPCITEMS.TXT | `2984af05b8acafb67677cebc7f39f107` | 85 |
| Base `reference/mmerge_data_forus/Data/mmmerge.T.lod/` | STDITEMS.TXT | `efe1f7c46011cb18f8a063e62a44d469` | 42 |
| OpenYAMM `assets_dev/engine/data_tables/` | items.txt | `f20c6bb768d89938b7841af86f94df0a` | 2204 |
| OpenYAMM `assets_dev/engine/data_tables/` | random_items.txt | `64ec19599d8fce8a401a0931951177e7` | 2213 |
| OpenYAMM `assets_dev/engine/data_tables/` | special_item_enchants.txt | `2984af05b8acafb67677cebc7f39f107` | 85 |
| OpenYAMM `assets_dev/engine/data_tables/` | standard_item_enchants.txt | `efe1f7c46011cb18f8a063e62a44d469` | 42 |

- `reference/mmerge_datapatch/Data/mmmerge.T.lod` (md5 `4bce30ee6665f02f0709a5eb04b967f2`)
  holds the same four tables byte for byte (identical md5s).
  No newer base MMMerge copy is available locally, so "probably base update" in 3.1.1 is a judgement from
  content and MAW history, not a comparison against a newer MMMerge.
- All files are CRLF, tab separated. Base and OpenYAMM ITEMS keep Windows-1252 punctuation (`\x85`, `\x92`);
  the MAW ITEMS, rnditems and SPCITEMS are pure ASCII.
- `special_item_enchants.txt` and `standard_item_enchants.txt` are byte-identical to base SPCITEMS/STDITEMS.
  MAW does not ship STDITEMS.TXT, so standard enchants are unchanged by MAW.

- MAW history of ITEMS.txt: first in `15714657` (2023-09-19), 20 distinct versions, last change `b2705582` (2025-08-23).
- MAW history of rnditems.txt: first in `c2e0e17e` (2023-08-30), 6 distinct versions, last change `4d7f38d1`
  (2025-09-11).
- MAW history of SPCITEMS.TXT: first in `e9cbec6a` (2023-09-06), 12 distinct versions, last change `29774f5a`
  (2025-10-31).
- `Data/zMaw.T.lod` has 59 commits (`c2e0e17e` 2023-08-30 to `29774f5a` 2025-10-31); ef23ee17 itself does not touch it.

#### 3.1.1 MAW design or base-version difference?

The first MAW ITEMS.txt (`15714657`, "artifacts description updated") equals base except artifact Notes and
item 1574; the first rnditems.txt (`c2e0e17e`) equals base except 146, 272-278 and 283; the first SPCITEMS.TXT
(`e9cbec6a`) keeps base rows 1-73 and appends seven draft rows 74-80 (`of Fire Resistance`, `of Air
Resistance`, ..., `of Magic Resistance`), later replaced by the current 74-80. So MAW started from this base,
and every other difference arrived in later MAW commits. Most changes are clearly MAW design (artifact buffs,
armour/belt stats, potion renames, crafting items, enchant weights, new enchants). Rows that look like base
fixes or tool artefacts rather than MAW design:

- Text only, 13 rows (3.3.8): Windows-1252 `\x85`/`\x92` replaced by space/apostrophe or dropped. All arrive in
  one commit (`b2705582`, 2025-08-23) that also makes the whole MAW ITEMS.txt pure ASCII: an editor/tool
  re-encode (or a newer base); no gameplay content. Safe to skip or take.
- 1372 The DeathBlade: the base row is an MMMerge test item ("For testing... remove before final release");
  MAW blanks it to an `_artifact570` placeholder. Probably base cleanup, not MAW design.
- 1574 `Catalyst potion` (Value 500) -> `Empty Message Scroll` (Value 0), present from MAW's first ITEMS: the
  row sits in the empty message-scroll block (1575-1578 are `Empty Message Scroll`, Value 0). Probably base
  cleanup.
- 1637 Sacred Spear: Notes lose a lore clause and "(+1D9 if used two-handed)", while 1641 Trident keeps its
  "(+1D6 if used two-handed)". Unclear: text fix in base or MAW removing the two-handed spear note.
- 1621 Jeweled Dagger Mod1 `1d2` -> `2d2` (`befd51e0`): the only non-artifact weapon dice change. Unclear;
  `1d2` on a 300-gold Time of Wonders dagger looks like a data error that MAW (or a newer base) corrected.

### 3.2 Format and id alignment (base MMMerge vs OpenYAMM)

#### 3.2.1 items.txt

- Loader: `GameDataLoader::loadItemTable` -> `ItemTable::load` (`game/tables/ItemTable.cpp`). Rows are keyed by
  the numeric `Item #` in column 0 (`parseItemId`: digits only); non-numeric rows (title, header, blank) are
  skipped, row order does not matter, the table is sized to the largest id. Columns are read by position:
  0-16 = the 17 MMMerge columns, 17 `package_id`, 18 `canonical_id`, 19 `source_item_id`, 20 `content_flags`;
  the parser also reads optional positions 21-44 (tier, use action, set, effect profile, class roots, required
  Might/Accuracy, inventory size, ...), which no engine row fills.
- Base: 2201 id rows (0-2200, contiguous), header of 17 columns. MAW: 2201 id rows (0-2200), same 17-column header.
- OpenYAMM: 2202 id rows (0-2201, contiguous). Header = base header + `package_id`, `canonical_id`, `source_item_id`,
  `content_flags`.
  316 rows carry the extra columns:
  the spellbook rows 400-498 (`World:mm8`), 1202-1300 (`World:mm7`), 1902-2018 (`World:mm6`) with only
  `content_flags` set, and the OpenYAMM-only row 2201 (`Blaster Shotgun`, `package_id=engine`,
  `content_flags=ScatterBlaster`). All other rows have 17 cells.
- Ids line up 1:1 for 0-2200 (same item in the same id, same column order). MAW has no rows beyond 2200 and no
  missing ids. MM9 items are not in this table: they are appended from `worlds/mm9` (id range 10000-10999).
- Base has one trailing 15-cell blank row; MAW does not (no effect: non-numeric rows are skipped).
- OpenYAMM changed 8 base rows (cells in columns 0-16), plus added row 2201 and the extra columns above:

| Item # | Name | Changed cells (base -> OpenYAMM) | MAW touches row? |
|---|---|---|---|
| 999 | Gold | Equip Stat: `gold` -> `Gold`; Skill Group: `misc` -> `Misc` | no |
| 1000 | Gold | Equip Stat: `gold` -> `Gold`; Skill Group: `misc` -> `Misc` | no |
| 1001 | Gold | Equip Stat: `gold` -> `Gold`; Skill Group: `misc` -> `Misc` | no |
| 1306 | Governor's Armor | Equip Stat: `armor` -> `Armor` | no |
| 1307 | Yoruba | Equip Stat: `armor` -> `Armor` | yes: Notes |
| 1328 | Ania Selving | Equip Stat: `Bow` -> `Missile` | no |
| 2030 | Pendragon | Equip Stat: `cloak` -> `Cloak` | yes: Notes |
| 2045 | Atlas | Equip Stat: `cloak` -> `Cloak` | yes: Notes |

  These are case normalisations (`gold`/`misc`/`armor`/`cloak`) and one Equip Stat fix (`Ania Selving` Bow ->
  Missile). No MAW-changed cell overlaps them (MAW only changes Notes on 1307, 2030, 2045).
- Patch generator: key by Item #, copy columns 0-16 cell by cell, never whole rows (a whole-row copy from MAW
  would revert the Equip Stat fixes above on 1307, 2030 and 2045 and drop columns 17-20).

#### 3.2.2 random_items.txt

- Loader: `ItemTable::load`, second loop. Rows keyed by numeric column 0; only columns 2-7 (treasure levels 1-6)
  are read into `randomTreasureWeights`; `Pic File` and the trailing name column are ignored.
- Base, MAW and OpenYAMM: 2200 / 2200 / 2200 id rows (1-2200), same header (`Item #`, `Pic File`, `1`..`6`), same
  title row and the same footer block (see 3.4.1). No row for 0 or 2201 (2201 therefore has all weights 0).
- OpenYAMM changed 300 base rows, all spellbooks, only in weight columns (levels) 2, 3, 4, 5, 6. Ids:
  400-497, 1202-1300, 1904-1914, 1917-1927, 1930-1940, 1943-1953, 1956-1966, 1969-1979, 1982-2018.

| Base -> OpenYAMM weights (changed levels) | Rows |
|---|---|
| 0 -> 2 | 400-401, 411-412, 422-423, 433-434, 444-445, 455-456, 466-467, 1202-1203, 1213-1214, 1224-1225, 1235-1236, 1246-1247, 1257-1258, 1268-1269, 1289, 1911-1914, 1924-1927, 1937-1940, 1950-1953, 1963-1966, 1976-1979, 1989-1992 |
| 0 -> 4 | 402-403, 413-414, 424-425, 435-436, 446-447, 457-458, 468-469, 1204-1205, 1215-1216, 1226-1227, 1237-1238, 1248-1249, 1259-1260, 1270-1271, 1908-1910, 1921-1923, 1934-1936, 1947-1949, 1960-1962, 1973-1975, 1986-1988 |
| 2 -> 4; 0 -> 1 | 404-406, 415-417, 426-428, 437-439, 448-450, 459-461, 470-472, 1206-1208, 1217-1219, 1228-1230, 1239-1241, 1250-1252, 1261-1263, 1272-1274 |
| 1 -> 2; 0 -> 1 | 407-410, 418-421, 429-432, 440-443, 451-454, 462-465, 473-476, 1209-1212, 1220-1223, 1231-1234, 1242-1245, 1253-1256, 1264-1267, 1275-1278 |
| 1 -> 3 | 477-478, 481-486, 488-489, 492-497, 1279-1280, 1283-1288, 1290-1291, 1294-1299, 1993-1994, 1999-2004, 2006-2007, 2012-2017 |
| 1 -> 4 | 479-480, 490-491, 1281-1282, 1292-1293, 1995, 1997, 2008, 2010 |
| 1 -> 2 | 487, 2005 |
| 0 -> 1 | 1300, 2018 |
| 2 -> 4 | 1904, 1906, 1917, 1919, 1930, 1932, 1943, 1945, 1956, 1958, 1969, 1971, 1982, 1984 |
| 2 -> 0 | 1905, 1907, 1918, 1920, 1931, 1933, 1944, 1946, 1957, 1959, 1970, 1972, 1983, 1985 |
| 1 -> 0 | 1996, 1998, 2009, 2011 |

  OpenYAMM re-weights the per-world spellbook copies. MAW also changes spellbook rows: 418, 1220 (see 3.4.3).

#### 3.2.3 special_item_enchants.txt and standard_item_enchants.txt

- Loader: `SpecialItemEnchantTable::load` (`game/items/ItemEnchantTables.cpp`). Keyed by position: every row
  whose column 0 and column 1 are both non-empty and whose column 0 is not `Bonus Stat` becomes the next entry;
  `get(id)` returns entry `id - 1`, so ids are the same 1-based indices as MAW's `Bonus2`.
  Columns read: 0 text, 1 suffix (also parsed to `SpecialItemEnchantKind` by exact lower-case match), 2-13 slot
  weights W1 W2 Miss Arm Shld Helm Belt Cape Gaunt Boot Ring Amul, 14 Value (`x2` = multiplier), 15 Lvl (first
  char), 16 description.
- Our file equals base, so our entries 1-73 = SPCITEMS 1-73 exactly (first data row is line 5, entry 73 is line 77).
- Ids 74-80 are **not free** in our loader: the footer comment rows `Treasure Level` / `A= 3 to 4` / `B= 3 to 5`
  / `C= 4 to 5` have text in both column 0 and 1 and load as junk entries 74-77 (kind `None`, all weights 0, so
  never rolled; `D= 5 to 6` has an empty column 1 and is skipped). The sums row (`\t\t505\t505...`) is skipped.
  Appending MAW 74-80 at the end of our file would give them ids 78-84. They must be inserted after entry 73
  (before the blank/sums/footer rows), or the footer rows removed. With MAW's file layout the footer becomes
  junk entries 81-84.
- `parseSpecialEnchantKind` only knows the 72 vanilla suffixes; `of Sparking` (73) and all MAW suffixes 74-80
  (`Paladins'`, `WarriorMage'`, ...) parse to kind `None`. `chooseSpecialEnchantId` skips kind `None`, so they
  would never be generated and have no effect until kinds/effects are added in code.
- Random enchant chances per treasure level are not read from any table: they are constants in
  `game/items/ItemEnchantRuntime.cpp` (standard 0/40/40/40/40/75, special 0/0/10/15/20/25, weapon special
  0/0/10/20/30/50), equal to the rnditems footer. The A-D level bands are hard-coded in `isSpecialRarityAllowed`.
- Standard enchants: `StandardItemEnchantTable::load`, same row rule, positional; ours = base STDITEMS; MAW has none.

### 3.3 ITEMS.txt: base -> MAW

202 rows changed, 427 cells. MAW-only rows: none. Base-only rows: none. Rows whose only difference is outside
the trimmed value: 0.

| Group | Rows | Cells |
|---|---|---|
| Body armour (Mod1/Mod2) | 32 | 54 |
| Belts | 15 | 27 |
| Potions | 35 | 65 |
| Crafting items (1041-1070) | 17 | 134 |
| Map item 290 | 1 | 7 |
| Artifacts and relics | 83 | 93 |
| Removed items | 1 | 16 |
| Text only: Windows-1252 punctuation removed | 13 | 13 |
| Other | 5 | 18 |

Changed cells by column: Notes 113, Name 57, Mod1 54, Mod2 45, Not identified name 31, Sprite Index 31, Pic File 21,
Equip Stat 21, Skill Group 20, material 16, Value 13, ID/Rep/St 1, VarA 1, VarB 1, Equip X 1, Equip Y 1.

#### 3.3.1 Body armour (Mod1/Mod2)

| Item # | Name | Skill | Mod1 | Mod2 | Commit |
|---|---|---|---|---|---|
| 84 | Leather Jerkin | Leather | 3 -> 8 | 2 -> 0 | 06913190 2024-10-27 |
| 85 | Hardened Leather Vest | Leather | 3 -> 8 | 4 (unchanged) | 06913190 2024-10-27 |
| 86 | Caravaner's Leather | Leather | 3 -> 8 | 6 -> 8 | 06913190 2024-10-27 |
| 87 | Regnan Leather | Leather | 3 -> 8 | 15 (unchanged) | 06913190 2024-10-27 |
| 88 | Alvarian Leather | Leather | 3 -> 8 | 24 (unchanged) | 06913190 2024-10-27 |
| 89 | Rusty Mail Vest | Chain | 6 -> 12 | 0 (unchanged) | 06913190 2024-10-27 |
| 90 | Steel Chainmail | Chain | 6 -> 12 | 6 -> 8 | 06913190 2024-10-27 |
| 91 | Minotaur Chainmail | Chain | 6 -> 12 | 12 -> 18 | 06913190 2024-10-27 |
| 92 | Siertal Chainmail | Chain | 6 -> 12 | 24 -> 28 | 06913190 2024-10-27 |
| 93 | Erudine Chainmail | Chain | 6 -> 12 | 32 -> 36 | 06913190 2024-10-27 |
| 868 | Crude Leather Armor | Leather | 3 -> 8 | 0 -> 1 | 06913190 2024-10-27 |
| 869 | Studded Leather | Leather | 3 -> 8 | 3 (unchanged) | 06913190 2024-10-27 |
| 870 | Officer's Leather | Leather | 3 -> 8 | 7 -> 6 | 06913190 2024-10-27 |
| 871 | Light Dragon Leather | Leather | 3 -> 8 | 11 -> 12 | 06913190 2024-10-27 |
| 872 | Royal Leather | Leather | 3 -> 8 | 21 -> 22 | 06913190 2024-10-27 |
| 873 | Disheveled Chain Mail | Chain | 6 -> 12 | 1 -> 0 | 06913190 2024-10-27 |
| 874 | Quality Steel Chain Mail | Chain | 6 -> 12 | 8 -> 6 | 06913190 2024-10-27 |
| 875 | Fine Chain Mail | Chain | 6 -> 12 | 16 (unchanged) | 06913190 2024-10-27 |
| 876 | Resplendent Chain Mail | Chain | 6 -> 12 | 22 -> 26 | 06913190 2024-10-27 |
| 877 | Golden Chain Mail | Chain | 6 -> 12 | 36 -> 34 | 06913190 2024-10-27 |
| 878 | Plate Armor | Plate | 18 (unchanged) | 2 -> 8 | 06913190 2024-10-27 |
| 1668 | Leather Armor | Leather | 3 -> 6 | 1 -> 0 | 06913190 2024-10-27 |
| 1669 | Reinforced Leather | Leather | 3 -> 8 | 5 -> 2 | 06913190 2024-10-27 |
| 1670 | Enchanted Leather | Leather | 3 -> 8 | 9 -> 5 | 06913190 2024-10-27 |
| 1671 | Dragon Leather | Leather | 3 -> 8 | 13 -> 11 | 06913190 2024-10-27 |
| 1672 | Imperial Leather | Leather | 3 -> 8 | 19 -> 20 | 06913190 2024-10-27 |
| 1673 | Chain Mail | Chain | 6 -> 10 | 2 -> 0 | 06913190 2024-10-27 |
| 1674 | Basic Steel Chain Mail | Chain | 6 -> 12 | 4 (unchanged) | 06913190 2024-10-27 |
| 1675 | Noble Chain Mail | Chain | 6 -> 12 | 14 (unchanged) | 06913190 2024-10-27 |
| 1676 | Royal Chain Mail | Chain | 6 -> 12 | 20 -> 24 | 06913190 2024-10-27 |
| 1677 | Majestic Chain Mail | Chain | 6 -> 12 | 30 -> 32 | 06913190 2024-10-27 |
| 1678 | Plate Mail | Plate | 18 (unchanged) | 4 -> 0 | 06913190 2024-10-27 |

Unchanged non-artifact `Armor` rows: 94-98, 879-880, 1406, 1679-1680 (94 Rusty Breastplate 18/0, 95 Banded Plate
18/10, 96 Minotaur Plate 18/20, 97 Dark Knight Plate 18/32, 98 Dragoning Plate 18/46, 879 Splendid Plate Armor 18/24,
880 Noble Plate Armor 18/40, 1406 Wetsuit 4/0, 1679 Steel Plate Mail 18/16, 1680 Golden Plate Mail 18/36).

#### 3.3.2 Belts

| Item # | Name | Mod1 | Mod2 | Commit |
|---|---|---|---|---|
| 117 | Studded Leather Belt | 0 -> 1 | 0 (unchanged) | cb0b554f 2024-05-10 |
| 118 | Sturdy Belt | 0 -> 1 | 0 -> 2 | cb0b554f 2024-05-10 |
| 119 | Wyvern Leather Belt | 0 -> 1 | 0 -> 5 | cb0b554f 2024-05-10 |
| 120 | Steel Belt | 0 -> 1 | 0 -> 8 | cb0b554f 2024-05-10 |
| 121 | Artificer's Belt | 0 -> 1 | 0 -> 11 | cb0b554f 2024-05-10 |
| 902 | Leather Belt | 0 -> 1 | 0 (unchanged) | cb0b554f 2024-05-10 |
| 903 | Fine Belt | 0 -> 1 | 0 -> 2 | cb0b554f 2024-05-10 |
| 904 | Strong Belt | 0 -> 1 | 0 -> 5 | cb0b554f 2024-05-10 |
| 905 | Silver Belt | 0 -> 1 | 0 -> 8 | cb0b554f 2024-05-10 |
| 906 | Gilded Belt | 0 -> 1 | 0 -> 11 | cb0b554f 2024-05-10 |
| 1702 | Crude Leather Belt | 0 -> 1 | 0 (unchanged) | cb0b554f 2024-05-10 |
| 1703 | Mercenary Belt | 0 -> 1 | 0 -> 2 | cb0b554f 2024-05-10 |
| 1704 | Vanguard Belt | 0 -> 1 | 0 -> 5 | cb0b554f 2024-05-10 |
| 1705 | Warlord Belt | 0 -> 1 | 0 -> 8 | cb0b554f 2024-05-10 |
| 1706 | Sovereign Belt | 0 -> 1 | 0 -> 11 | cb0b554f 2024-05-10 |

All 15 non-artifact belts change. Artifact belts: 1326 and 1337 also get Mod1/Mod2 (listed under artifacts);
537 Berserker Belt keeps Mod1/Mod2 `0`/`0` (Notes change only).

#### 3.3.3 Potions

| Item # | Name (base) | Changed cells (base -> MAW) | Commit |
|---|---|---|---|
| 224 | Cure Weakness | Name: `Cure Weakness` -> `Energy Potion` | 113c0074 2024-01-26 |
| 225 | Cure Disease | Name: `Cure Disease` -> `Antidote` | 113c0074 2024-01-26 |
| 226 | Cure Poison | Name: `Cure Poison` -> `Hexbane` | 113c0074 2024-01-26 |
| 227 | Awaken | Name: `Awaken` -> `Lucidity` | 113c0074 2024-01-26 |
| 231 | Preservation | Name: `Preservation` -> `Protection` | 113c0074 2024-01-26 |
| 232 | Shield | Name: `Shield` -> `Meditation` | 3a3354c0 2024-01-28 |
| 233 | Recharge Item | Name: `Recharge Item` -> `Regeneration` | 113c0074 2024-01-26 |
| 234 | Stoneskin | Name: `Stoneskin` -> `Stone Skin` | 113c0074 2024-01-26 |
| 237 | Remove Fear | Name: `Remove Fear` -> `Magic Protection` | 113c0074 2024-01-26 |
| 238 | Remove Curse | Name: `Remove Curse` -> `Enchant Item` | 113c0074 2024-01-26 |
| 239 | Cure Insanity | Name: `Cure Insanity` -> `Stone to Flesh` | 113c0074 2024-01-26 |
| 240 | Might Boost | Name: `Might Boost` -> `Power Boost` | 113c0074 2024-01-26 |
| 241 | Intellect Boost | Name: `Intellect Boost` -> `Wisdom Boost` | 113c0074 2024-01-26 |
| 242 | Personality Boost | Name: `Personality Boost` -> `Resilience Boost` | 113c0074 2024-01-26 |
| 243 | Endurance Boost | Name: `Endurance Boost` -> `Lesser Element` | 113c0074 2024-01-26 |
| 244 | Speed Boost | Name: `Speed Boost` -> `Swiftness` | 113c0074 2024-01-26 |
| 245 | Accuracy Boost | Name: `Accuracy Boost` -> `Champion's Potion` | 4f4bfb0a 2024-01-30 |
| 246 | Flaming Potion | Name: `Flaming Potion` -> `Divine Restoration` | 4f4bfb0a 2024-01-30 |
| 247 | Freezing Potion | Name: `Freezing Potion` -> `Divine Cure` | 4f4bfb0a 2024-01-30 |
| 248 | Noxious Potion | Name: `Noxious Potion` -> `Divine Magic` | 4f4bfb0a 2024-01-30 |
| 249 | Shocking Potion | Name: `Shocking Potion` -> `Elemental Resistance` | 4f4bfb0a 2024-01-30 |
| 250 | Swift Potion | Name: `Swift Potion` -> `Self Resistance` | 4f4bfb0a 2024-01-30 |
| 251 | Cure Paralysis | Name: `Cure Paralysis` -> `Paladin's Potion` | 113c0074 2024-01-26 |
| 252 | Divine Restoration | Name: `Divine Restoration` -> `Pure Power`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 253 | Divine Cure | Name: `Divine Cure` -> `Pure Wisdom`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 254 | Divine Power | Name: `Divine Power` -> `Pure Resilience`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 255 | Luck Boost | Name: `Luck Boost` -> `Greater Element`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 256 | Fire Resistance | Name: `Fire Resistance` -> `Darkness`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 257 | Air Resistance | Name: `Air Resistance` -> `Divine Blessing`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 113c0074 2024-01-26 |
| 258 | Water Resistance | Name: `Water Resistance` -> `Twilight`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 259 | Earth Resistance | Name: `Earth Resistance` -> `Transcendence`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 113c0074 2024-01-26 |
| 260 | Mind Resistance | Name: `Mind Resistance` -> `Dawn`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 261 | Body Resistance | Name: `Body Resistance` -> `Pure Elemental Resistance`; Value: `750` -> `2000`; Not identified name: `White Potion` -> `Black Potion`; Sprite Index: `58` -> `60` | 308344e5 2024-01-27 |
| 262 | Stone to Flesh | Name: `Stone to Flesh` -> `Pure Self Resistance` | 308344e5 2024-01-27 |
| 263 | Slaying Potion | Name: `Slaying Potion` -> `Divine Resistance` | 308344e5 2024-01-27 |

#### 3.3.4 Crafting items (1041-1070)

Base rows are placeholders or replaced wholesale; full MAW rows (columns 1-16):

| Item # | Side | Pic | Name | Value | Equip | Skill | Mod1 | Mod2 | Mat | ID | Unid name | Spr | VarA | VarB | X | Y | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1051 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1051 | MAW | gem2 | Crafting Moonstone | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 396 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1052 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1052 | MAW | gem3 | Crafting Topaz | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 397 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1053 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1053 | MAW | gem5 | Crafting Amethyst | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 399 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1054 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1054 | MAW | item214 | Crafting Amber | 0 | Gem | Misc | 0 | 0 | 0 | 0 | Crafting Item | 145 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1055 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1055 | MAW | gem7 | Crafting Purple Topaz | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 401 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1056 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1056 | MAW | gem4 | Crafting Ruby | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 398 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1057 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1057 | MAW | gem8 | Crafting Sunstone | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 402 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1058 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1058 | MAW | gem9 | Crafting Emerald | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 403 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1059 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1059 | MAW | gem10 | Crafting Sapphire | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 404 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1060 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1060 | MAW | gem1 | Crafting Diamond | 0 | Gem | Misc | 0 | 0 | 5 | 0 | Crafting Item | 395 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1061 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1061 | MAW | crysball | The Eye | 0 | Gem | Misc | 0 | 0 | 1 | 0 | Crafting Item | 354 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1062 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1062 | MAW | 6hglass | Hourglass of Creation | 0 | Gem | Misc | 0 | 0 | 2 | 0 | Crafting Item | 351 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1063 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1063 | MAW | 7item361 | Crafting Cube | 0 | Gem | Misc | 0 | 1 | 2 | 0 | Crafting Item | 296 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1064 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1064 | MAW | item327 | Misterious Mirror | 0 | Gem | Misc | 0 | 0 | 0 | 0 | Crafting Item | 126 | 0 | 0 | 0 | 0 | 7b1900b4 2023-10-05 |
| 1065 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1065 | MAW | 7item362 | Ascension Emerald | 0 | Gem | Misc | 0 | 0 | 3 | 0 | Crafting Item | 300 | 0 | 0 | 0 | 0 | 3078e895 2024-03-26 |
| 1066 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1066 | MAW | wytprl | Scouring Pearl | 0 | Gem | Misc | 0 | 0 | 4 | 0 | Crafting Item | 367 | 0 | 0 | 0 | 0 | caee8493 2024-05-12 |
| 1067 | base | null | _potion/reagent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 153 | 0 | 0 | 0 | 0 |  |
| 1067 | MAW | memcryst | Oracle's Orb | 0 | Gem | Misc | 0 | 0 | 1 | 0 | Crafting Item | 411 | 0 | 0 | 0 | 0 | b2705582 2025-08-23 |

Notes (full):

- 1051 base: `Description here.`
  MAW: `A special Moonstone that allows to increase an item Enchant Strength by 2, up to 10 (right-click on an item
  with a base enchant to use)`
- 1052 base: `Description here.`
  MAW: `A special Topaz that allows to increase an item Enchant Strength by 2, up to 20 (right-click on an item with a
  base enchant to use)`
- 1053 base: `Description here.`
  MAW: `A special Amethyst that allows to increase an item Enchant Strength by 3, up to 30 (right-click on an item
  with a base enchant to use)`
- 1054 base: `Description here.`
  MAW: `A special Amber dthat allows to increase an item Enchant Strength by 3, up to 40 (right-click on an item with
  a base enchant to use)`
- 1055 base: `Description here.`
  MAW: `A special Purple Topaz that allows to increase an item Enchant Strength by 4, up to 50 (right-click on an item
  with a base enchant to use)`
- 1056 base: `Description here.`
  MAW: `A special Ruby that allows to increase an item Enchant Strength by 4, up to 60 (right-click on an item with a
  base enchant to use)`
- 1057 base: `Description here.`
  MAW: `A special Sunstone that allows to increase an item Enchant Strength by 4, up to 70 (right-click on an item
  with a base enchant to use)`
- 1058 base: `Description here.`
  MAW: `A special Emerald that allows to increase an item Enchant Strength by 4, up to 80 (right-click on an item with
  a base enchant to use)`
- 1059 base: `Description here.`
  MAW: `A special Sapphire that allows to increase an item Enchant Strength by 5, up to 90 (right-click on an item
  with a base enchant to use)`
- 1060 base: `Description here.`
  MAW: `A special Diamond that allows to increase an item Enchant Strength by 5, up to 100 (right-click on an item
  with a base enchant to use)`
- 1061 base: `Description here.`
  MAW: `This Eye allows to add a Special enchant to any equipment (right-click on an item with a base enchant to use)`
- 1062 base: `Description here.`
  MAW: `This Hourglass allows to add a second base enchant to any equipment (right-click on an item with a base
  enchant to use)`
- 1063 base: `Description here.`
  MAW: `This Cube allows to increase the base Strength and the Special enchant strength of any equipment (right-click
  on an item with a base enchant to use)`
- 1064 base: `Description here.`
  MAW: `This Mirror is able to create a copy of any equipment  (right-click on an item with a base enchant to use)`
- 1065 base: `Description here.`
  MAW: `The Ascension Emerald is a rare, mystical stone, shimmering with a deep green hue reminiscent of ancient
  emeralds. This enchanting gem holds the power to enhance the very essence of an item, elevating its tier
  (right-click on an unequipped item to increase its tier by 1, if available).`
- 1066 base: `Description here.`
  MAW: `The Scouring Pearl is a mystical item valued for its power to erase one random enchant from any enchanted item.`
- 1067 base: `Description here.`
  MAW: `Description here.`

Ids 1041-1050 and 1068-1070 stay `_potion/reagent` placeholders in MAW. 1022-1023 (Power Stone) are in
"Other". Material column values: 5 for the ten gems, 1/2/3/4 for the special crafting items.

#### 3.3.5 Map item 290

Base rows are placeholders or replaced wholesale; full MAW rows (columns 1-16):

| Item # | Side | Pic | Name | Value | Equip | Skill | Mod1 | Mod2 | Mat | ID | Unid name | Spr | VarA | VarB | X | Y | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 290 | base | item180 | Protection from Magic | 750 | Bottle | Misc | 0 | 0 | 1 | 0 | White Potion | 58 | 0 | 0 | 0 | 0 |  |
| 290 | MAW | map | Map | 0 | N / A | Misc | 0 | 0 | 1 | 0 | Map | 382 | 0 | 0 | 0 | 0 | fd8d6069 2024-09-18 |

Notes (full):

- 290 base: `Grants Protection from Magic (as the spell) for 30 minutes per point of potion strength.  (To drink, pick
  the potion up and right-click over a character's portrait.  To mix two potions, pick up one and right-click it over
  the other.)`
  MAW: `A map made from stretched hides and vellum.`

#### 3.3.6 Artifacts and relics

| Item # | Name (base) | Changed cells (base -> MAW) | Commit |
|---|---|---|---|
| 500 | Elsenrail | Notes: (Accuracy [-+40,-]{++60,+} [-10-20-]{+20-40+} points of L...he universe. | f1e5ce77 2024-01-16 |
| 501 | Glomenthal | Notes: (Might [-+40,-]{++60,+} [-10-20-]{+20-40+} points of D...he universe. | f1e5ce77 2024-01-16 |
| 502 | Terminus | Notes: (Armsmaster skill +7, Air Resistance [-+30)-]{++100)+} As a child,...s a mystery. | f1e5ce77 2024-01-16 |
| 504 | Elderaxe | Notes: (Might [-+20,-]{++100,+} Swift, [-6-12-]{+12-24+} points of C... herdmaster. | f1e5ce77 2024-01-16 |
| 505 | Volcano | Notes: [-(10-20-]{+(20-40+} points of Fire damage, Fire Resistance [-+40)-]{++80)+} The mad art...or the tool. | c6ddd1ac 2023-11-26 |
| 506 | Wyrm Spitter | Notes: (Endurance [-+20,-]{++60,+} Dragon Slay...wmarsh Pass. | f1e5ce77 2024-01-16 |
| 507 | Guardian | Notes: [-(+10-]{+(+20+} to all attributes, [-10-20-]{+20-40+} points of B...arger world. | f1e5ce77 2024-01-16 |
| 508 | Foulfang | Notes: (Vampiric, [-10-]{+20+} points of P...de, is lost. | 15714657 2023-09-19 |
| 509 | Scepter of Kings | Notes: (Personality + [-40,-]{+80,+} Regenerate ... seen again. | f1e5ce77 2024-01-16 |
| 510 | Breaker | Notes: (Might [-+20,-]{++30,+} Endurance [-+20,-]{++30,+} [-10-20-]{+20-40+} points of B...Silver Rose? | f1e5ce77 2024-01-16 |
| 513 | Serendine's Preservation | Notes: (Regenerates Spell Points, Endurance [-+30)-]{++70)+} A mage know... weaknesses. | f1e5ce77 2024-01-16 |
| 514 | Glomenmail | Notes: [-(+10-]{+(+20+} to all statistics, [-+10-]{++20+} to all resi...ly, coveted. | f1e5ce77 2024-01-16 |
| 515 | Supreme Plate | Notes: (Swift, [-+15-]{++45+} Speed, [-+15-]{++45+} Accuracy, K...these suits. | f1e5ce77 2024-01-16 |
| 518 | Herald's Boots | Notes: (Speed + [-30,-]{+60,+} Swift, Immu...ivil unrest. | f1e5ce77 2024-01-16 |
| 520 | Drogg's Helm | Notes: (Personality [-+15,-]{++60,+} Intellect [-+15,-]{++60,+} Regenerates...erstand why. | f1e5ce77 2024-01-16 |
| 521 | Crown of Final Dominion | Notes: (Intellect [-+50,-]{++100,+} of Dark Mag... lost crown. | f1e5ce77 2024-01-16 |
| 522 | Archangel Wings | Notes: (Feather Falling, Intellect + [-30,-]{+40,+} All magic r...stic powers. | f1e5ce77 2024-01-16 |
| 523 | Snake | Notes: (Slows target,{+ Speed +100,+} Water Resis...der as well. | f1e5ce77 2024-01-16 |
| 525 | Finality | Notes: [-(10-20-]{+(20-40+} points of Fire damage, Slow, Speed [--20)-]{+-20, Accuracy +120)+} When the ar...hian courts. | f1e5ce77 2024-01-16 |
| 527 | Spiritslayer | Notes: (Vampiric, Might [-+50,-]{++80,+} Luck -40) M...ery essence. | f1e5ce77 2024-01-16 |
| 528 | Trident of Rulership | Notes: (Water Breathing, [-+70-]{++140+} Water Resistance, [--70-]{+-40+} Fire Resist...the surface. | f1e5ce77 2024-01-16 |
| 529 | Blade of Mercy | Notes: (Might [-+40,-]{++100,+} [-4-10-]{+Accuracy +100, 8-20+} points Electrical damage,[- Accuracy -40,-] Necromancer...uffered end. | f1e5ce77 2024-01-16 |
| 532 | Lightning Crossbow | Notes: (Swift, [-Accuracy-]{+Might+} [--50,-]{++60,+} {+Speed +60,  +}Dark Elf) An...good effect. | f1e5ce77 2024-01-16 |
| 533 | Last Stage Cuirass | Notes: (Personality [-+80,-]{++140,+} Intellect [-+70,-]{++140,+} [--30-]{+-100+} Mind and [-Spirit-]{+Body+} resistances... using them. | b273d175 2024-03-14 |
| 534 | Herondale's Lost Shield | Notes: ...ralysis, and Sleep; [-Personality-]{+Endurance+} [--15,-]{++50,+} Luck -15) T...nt energies. | f1e5ce77 2024-01-16 |
| 535 | Ring of Fusion | Notes: (of Water, Alchemy skill + 5, Intellect [-+40,-]{++60,+} Endurance -...om the user. | f1e5ce77 2024-01-16 |
| 536 | Lucky Hat | Notes: (Luck + [-90,-]{+100,+} Personality... flattering! | f1e5ce77 2024-01-16 |
| 537 | Berserker Belt | Notes: (Might [-+100,-]{++120,+} Immune to F...ect warrior. | f1e5ce77 2024-01-16 |
| 1302 | Puck | Notes: (Speed [-+40,-]{++80,+} Swift) Anci...nmistakable. | f1e5ce77 2024-01-16 |
| 1303 | Iron Feather | Notes: (Might [-+40,-]{++80,+} [-6-15-]{+12-30+} points of E...nly problem. | f1e5ce77 2024-01-16 |
| 1305 | Corsair | Notes: ...sarm skill +5, Luck [-+40)-]{++80)+} Corsair is ...e of others. | f1e5ce77 2024-01-16 |
| 1307 | Yoruba | Notes: ...nditions, Endurance [-+25)-]{++100)+} Named after...tal reasons. | f1e5ce77 2024-01-16 |
| 1308 | Splitter | Notes: (Explosive impact, Fire [-Resistance +50)-]{+Immunity)+} Though powe...m the blast. | f1e5ce77 2024-01-16 |
| 1309 | Ghoulsbane | Mod1: `1d9` -> `1d18`; Mod2: `19` -> `30`; Notes: (Undead slaying, Immunity to paralysis, [-3-18-]{+6-36+} fire damage...in 1083 A.S. | f1e5ce77 2024-01-16 |
| 1310 | Gibbet | Mod1: `3d6` -> `3d9`; Mod2: `18` -> `30` | f1e5ce77 2024-01-16 |
| 1311 | Charele | Mod1: `3d9` -> `3d15`; Mod2: `18` -> `30` | f1e5ce77 2024-01-16 |
| 1312 | Ullyses | Notes: (Accuracy [-+50,-]{++80,+} [-9-12-]{+18-24+} water damag...Elvish make. | f1e5ce77 2024-01-16 |
| 1314 | Seven League Boots | Notes: (Speed [-+40,-]{++80,+} of Water Ma...these boots. | f1e5ce77 2024-01-16 |
| 1317 | Ethric's Staff | Notes: (Of Dark Magic, Meditation skill [-+15,-]{++8,+} Decrease Hi...d the staff. | 6b83b83b 2024-07-09 |
| 1318 | Hareck's Leather | Notes: [-(Stealing-]{+(Dagger+} skill +5, D...lking, Luck [-+50,-]{++100,+} All Resistances [--10)This-]{+-20)This+} leather arm...wife's hand. | 306abc05 2025-08-16 |
| 1319 | Old Nick | Notes: (Disarm Skill +5, [-8-]{+54+} points of P....aren't you? | f1e5ce77 2024-01-16 |
| 1321 | Glory Shield | Notes: ...+5, Body Resistance [--10,-]{+-20,+} Mind Resistance [--10)-]{+-20)+} One of five...sed attacks. | c6ddd1ac 2023-11-26 |
| 1322 | Kelebrim | Notes: ... attacks, Endurance [-+50,-]{++100,+} Earth Resistance [--30)-]{+-60)+} One of the ...Earth magic. | f1e5ce77 2024-01-16 |
| 1323 | Taledon's Helm | Notes: (Of Light Magic, Personality [-+15,-]{++45,+} Might [-+15,-]{++45,+} Luck -40, G...n Steadwick. | f1e5ce77 2024-01-16 |
| 1325 | Phynaxian Crown | Notes: (Of Fire Magic, Water Resistance [-+50,-]{++100,+} Personality...sed attacks. | c6ddd1ac 2023-11-26 |
| 1326 | Titan's Belt | Mod1: `0` -> `1`; Mod2: `0` -> `19`; Notes: (Might [-+75,-]{++115,+} Speed -40) ...e trade off. | cb0b554f 2024-05-10 |
| 1327 | Twilight | Notes: (Speed [-+50,-]{++80,+} Luck [-+50,-]{++80,+} All resistances [--15,-]{+-30,+} Evil) The s... overlooked. | f1e5ce77 2024-01-16 |
| 1329 | Justice | Mod1: `2d4` -> `2d8`; Mod2: `16` -> `24` | f1e5ce77 2024-01-16 |
| 1330 | Mekorig's Hammer | Notes: ...+75, Air Resistance [--50)-]{+-100)+} This is the...er provides. | c6ddd1ac 2023-11-26 |
| 1333 | Elfbane | Notes: [-(Of-]{+(Speed +100, Of+} Shielding, ...ut a goblin. | f1e5ce77 2024-01-16 |
| 1334 | Mind's Eye | Notes: [-(+15-]{+(+30+} Intellect, [-+15-]{++30+} Personality... of a human. | f1e5ce77 2024-01-16 |
| 1335 | Elven Chainmail | Notes: (of Recovery, [-+15-]{++30+} Speed, [-+15-]{++30+} Accuracy, E...ate attacks. | f1e5ce77 2024-01-16 |
| 1336 | Forge Gauntlets | Notes: [-(+30-]{+(+60+} Fire Resistance, [-+15-]{++30+} Might, [-+15-]{++30+} Endurance, ...s Mekorig's. | f1e5ce77 2024-01-16 |
| 1337 | Hero's Belt | Mod1: `0` -> `1`; Mod2: `0` -> `24`; Notes: (+5 Armsmaster skill, [-+15-]{++30+} Might, Rege... the dragon. | cb0b554f 2024-05-10 |
| 1338 | Lady's Escort | Notes: (Water walking, Feather falling, [-of-]{+all+} [-Protection,-]{+resistance +10,+} Female) A m... soon after. | f1e5ce77 2024-01-16 |
| 2020 | Mordred | Mod1: `2d3` -> `2d6`; Mod2: `10` -> `15` | f1e5ce77 2024-01-16 |
| 2021 | Thor | Notes: ...  (Special Powers:  {+Might +75, +}Force) | f1e5ce77 2024-01-16 |
| 2022 | Conan | Notes: ...  (Special Powers:  {+Accuracy+150, +}Devil and Dragon Slaying) | f1e5ce77 2024-01-16 |
| 2023 | Excalibur | Notes: ...  (Special Powers:  [-+30-]{++100+} Might) | f1e5ce77 2024-01-16 |
| 2024 | Merlin | Notes: .... (Special Powers:  [-Swiftness-]{+Swiftness,+} [-and-]{+Intellect+} [-+40-]{++120, Personality +120, +200+} Spell Points) | f1e5ce77 2024-01-16 |
| 2025 | Percival | Notes: ...s.  (Special Powers:{+ Speed +40,+}  Swiftness and Carnage) | f1e5ce77 2024-01-16 |
| 2026 | Galahad | Notes: ...rs:  Protection and [-+25-]{++100+} [-Hit Points)-]{+Endurance)+} | f1e5ce77 2024-01-16 |
| 2027 | Pellinore | Notes: ...  (Special Powers:  [-+30-]{++120+} Endurance, ...egeneration) | f1e5ce77 2024-01-16 |
| 2028 | Valeria | Notes: ...ers:  Shielding and [-+30-]{++80+} Accuracy) | f1e5ce77 2024-01-16 |
| 2029 | Arthur | Notes: ...  (Special Powers:  [-'of-]{++20+} [-the-]{+all+} [-Gods'-]{+stats'+} and [-+25-]{++100+} Spell Points) | f1e5ce77 2024-01-16 |
| 2030 | Pendragon | Notes: ...  (Special Powers:  [-+30-]{++60+} Luck, [-Thievery,-]{++5 Dagger Skill,+} Immunity to Poison) | 306abc05 2025-08-16 |
| 2031 | Lucius | Notes: ...  (Special Powers:  [-+30-]{++80+} Speed) | f1e5ce77 2024-01-16 |
| 2032 | Guinevere | Notes: ...  (Special Powers:  [-+30-]{++100+} Spell Point...Dark Magic') | f1e5ce77 2024-01-16 |
| 2033 | Igraine | Notes: ...  (Special Powers:  [-+25-]{++100+} Spell Point...irit Magic') | f1e5ce77 2024-01-16 |
| 2034 | Morgan | Notes: ...  (Special Powers:  [-+20-]{++80+} Spell Point...arth Magic') | f1e5ce77 2024-01-16 |
| 2035 | Hades | Notes: ... +20 Poison Damage, [-+20-]{++60+} Luck, Thiev...egeneration) | f1e5ce77 2024-01-16 |
| 2036 | Ares | Notes: ...:  +30 Fire Damage, [-+25 -]{++100  +}Fire Resistance) | f1e5ce77 2024-01-16 |
| 2037 | Poseidon | Notes: ...  (Special Powers:  [-+20-]{++40+} Might, [-+20-]{++40+} Endurance, [-+20-]{++40+} Accuracy, -...d -10 Speed) | f1e5ce77 2024-01-16 |
| 2038 | Cronos | Notes: ...  (Special Powers:  [-+100-]{++120+} [-Hit Points-]{+Endurance+} and [--50-]{+-60+} Luck) | f1e5ce77 2024-01-16 |
| 2039 | Hercules | Notes: ...  (Special Powers:  [-+50-]{++100+} Might, [-+20-]{++60+} Endurance, and -30 Intellect) | f1e5ce77 2024-01-16 |
| 2040 | Artemis | Notes: ...  (Special Powers:  [-+20-]{++40+} Electricity damage, [--10-]{+-20+} to Elemental Resistances) | c6ddd1ac 2023-11-26 |
| 2041 | Apollo | Notes: ...  (Special Powers:  [-+20-]{++40+} to Resistan...0 Endurance) | c6ddd1ac 2023-11-26 |
| 2042 | Zeus | Notes: ...pecial Powers:  +50 [-Hit Points,-]{+Endurance,+} +50 [-Spell Points,-]{+Personality,+}  +50 Luck, and -50 Intellect) | f1e5ce77 2024-01-16 |
| 2043 | Aegis | Notes: ... effects, Shielding [-+20-]{++100+} Luck, and -20 Speed) | f1e5ce77 2024-01-16 |
| 2044 | Odin | Notes: ...  (Special Powers:  [-+50-]{++60+} to Elemental Resistances and -40 Speed) | f1e5ce77 2024-01-16 |
| 2045 | Atlas | Notes: ...  (Special Powers:  [-+100-]{++120+} Might and -40 Speed) | f1e5ce77 2024-01-16 |
| 2046 | Hermes | Notes: ...  (Special Powers:  [-+100-]{++140+} Speed and -40 Accuracy) | f1e5ce77 2024-01-16 |
| 2049 | Hera | Notes: ...  (Special Powers:  [-+50-]{++100+} Hit Points, [-+50-]{++100+} Spell Point...Personality) | f1e5ce77 2024-01-16 |

#### 3.3.7 Removed items

Full rows, base -> MAW:

| Item # | Side | Pic | Name | Value | Equip | Skill | Mod1 | Mod2 | Mat | ID | Unid name | Spr | VarA | VarB | X | Y | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1372 | base | 7item249 | The DeathBlade | 666 | Weapon2 | Sword | 4d5 | 2 | Special | 6 | Two-Handed Sword | 155 | of Vigor | 50 | 25 | 155 |  |
| 1372 | MAW | null | _artifact570 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | _artifact570 | 153 | 0 | 0 | 0 | 0 | 5c6d6da4 2023-10-05 |

Notes (full):

- 1372 base: `For testing\x85 remove before final release.`
  MAW: `Description here.`

#### 3.3.8 Text only: Windows-1252 punctuation removed

| Item # | Name (base) | Changed cells (base -> MAW) | Commit |
|---|---|---|---|
| 282 | Divine Transcendence | Notes: Increases the [-character\x92s-]{+character's+} level by 20...her potion.) | b2705582 2025-08-23 |
| 888 | Metal Shield | Notes: ...n the original color[-\x85-] | b2705582 2025-08-23 |
| 898 | Fancy Hat | Notes: ...emulate the nobleman[-\x85-] | b2705582 2025-08-23 |
| 922 | Brass Ring | Notes: ...ell it for something[-\x85-]{+ +}but don't expect much. | b2705582 2025-08-23 |
| 1442 | Abbey Normal Golem Head | Notes: ....  It looks a little[-\x85-]{+ +}strange.  It... functional. | b2705582 2025-08-23 |
| 1465 | Sewer Key | Notes: ...wasn't in the sewers[-\x85 -]{+ +}it was hidin... whole time. | b2705582 2025-08-23 |
| 1629 | Supreme Axe | Notes: ... sold or traded away[-\x85-] | b2705582 2025-08-23 |
| 1641 | Trident | Notes: ...to this activity as [-piracy\x85(+1D6-]{+piracy(+1D6+} if used two-handed). | b2705582 2025-08-23 |
| 1651 | True Crossbow | Notes: ...mystery at this time[-\x85-] | b2705582 2025-08-23 |
| 1658 | Dark Hammer | Notes: ...etting them?' arises[-\x85-] | b2705582 2025-08-23 |
| 2081 | Tanir's Bell | Notes: ...ll silver bell seems[-\x85-]{+ +}wrong.  It s... than it is. | b2705582 2025-08-23 |
| 2094 | Cobra Egg | Notes: The heavy egg of a large bird or reptile[-\x85-]{+ +}or monster. | b2705582 2025-08-23 |
| 2105 | Cloak of Baa | Notes: ....  An ominous symbol[-\x85-] | b2705582 2025-08-23 |

#### 3.3.9 Other

| Item # | Name (base) | Changed cells (base -> MAW) | Commit |
|---|---|---|---|
| 1022 | _potion/reagent | Pic File: `null` -> `item281`; Name: `_potion/reagent` -> `Power Stone`; Equip Stat: `0` -> `N / A`; Skill Group: `0` -> `Misc`; Not identified name: `0` -> `Stone`; Sprite Index: `153` -> `137`; Notes: [-Description-]{+Quest+} [-here.-]{+Item: A facet carved stone of dark glassy rock. When tapped it produces a high bell tone.+} | 5c6d6da4 2023-10-05 |
| 1023 | _potion/reagent | Pic File: `null` -> `item297`; Name: `_potion/reagent` -> `Power Stone`; Equip Stat: `0` -> `N / A`; Skill Group: `0` -> `Misc`; Not identified name: `0` -> `Stone`; Sprite Index: `153` -> `138`; Notes: [-Description-]{+Quest+} [-here.-]{+Item: A facet carved stone of dark glassy rock. When tapped it produces a medium bell tone.+} | 5c6d6da4 2023-10-05 |
| 1574 | Catalyst potion | Name: `Catalyst potion` -> `Empty Message Scroll`; Value: `500` -> `0` | 15714657 2023-09-19 |
| 1621 | Jeweled Dagger | Mod1: `1d2` -> `2d2` | befd51e0 2024-10-12 |
| 1637 | Sacred Spear | Notes: ... before the Silence [-and remained in production almost towards the end of the Heavenly Forges, in that period -]serving cere...hese in any [-capacity (+1D9 if used two-handed).-]{+capacity.+} | 504f506c 2024-11-18 |

#### 3.3.10 As a patch onto OpenYAMM items.txt

- Mapping: same Item #, same column names and positions for columns 0-16 (ours = base header + 4 extra columns).
  The patch is exactly the 427 cells above; no id remapping.
- MAW-touched rows with OpenYAMM extra columns (17-20) set: none. Keep 17-20 as they are.
- Three-way cells where OpenYAMM already differs from base: 0.
- MAW-touched rows that OpenYAMM also changed (different cells, so no overwrite if patched by cell):
  1307 (ours: Equip Stat; MAW: Notes), 2030 (ours: Equip Stat; MAW: Notes), 2045 (ours: Equip Stat; MAW: Notes).
- Result: applying MAW cell by cell overwrites no OpenYAMM fix. Text-only rows replace our Windows-1252
  punctuation with ASCII (no gameplay effect).
- Engine-side conflicts outside items.txt (not cell conflicts): item 290 is potion 70 `Protection from Magic` in
  `engine/data_tables/potion_settings.txt`, so making it a Map needs that row removed or remapped; the potion
  renames 224-263 (and value/unidentified-name/sprite changes 252-261) change what the potion ids mean, so
  `potion_settings.txt`, the mixing table and potion effects must follow MAW's potion design, not just names.

Compact patch for all non-Notes cells (`id: Column=value`):

```
84: Mod1=8; Mod2=0
85: Mod1=8
86: Mod1=8; Mod2=8
87: Mod1=8
88: Mod1=8
89: Mod1=12
90: Mod1=12; Mod2=8
91: Mod1=12; Mod2=18
92: Mod1=12; Mod2=28
93: Mod1=12; Mod2=36
117: Mod1=1
118: Mod1=1; Mod2=2
119: Mod1=1; Mod2=5
120: Mod1=1; Mod2=8
121: Mod1=1; Mod2=11
224: Name=Energy Potion
225: Name=Antidote
226: Name=Hexbane
227: Name=Lucidity
231: Name=Protection
232: Name=Meditation
233: Name=Regeneration
234: Name=Stone Skin
237: Name=Magic Protection
238: Name=Enchant Item
239: Name=Stone to Flesh
240: Name=Power Boost
241: Name=Wisdom Boost
242: Name=Resilience Boost
243: Name=Lesser Element
244: Name=Swiftness
245: Name=Champion's Potion
246: Name=Divine Restoration
247: Name=Divine Cure
248: Name=Divine Magic
249: Name=Elemental Resistance
250: Name=Self Resistance
251: Name=Paladin's Potion
252: Name=Pure Power; Value=2000; Not identified name=Black Potion; Sprite Index=60
253: Name=Pure Wisdom; Value=2000; Not identified name=Black Potion; Sprite Index=60
254: Name=Pure Resilience; Value=2000; Not identified name=Black Potion; Sprite Index=60
255: Name=Greater Element; Value=2000; Not identified name=Black Potion; Sprite Index=60
256: Name=Darkness; Value=2000; Not identified name=Black Potion; Sprite Index=60
257: Name=Divine Blessing; Value=2000; Not identified name=Black Potion; Sprite Index=60
258: Name=Twilight; Value=2000; Not identified name=Black Potion; Sprite Index=60
259: Name=Transcendence; Value=2000; Not identified name=Black Potion; Sprite Index=60
260: Name=Dawn; Value=2000; Not identified name=Black Potion; Sprite Index=60
261: Name=Pure Elemental Resistance; Value=2000; Not identified name=Black Potion; Sprite Index=60
262: Name=Pure Self Resistance
263: Name=Divine Resistance
290: Pic File=map; Name=Map; Value=0; Equip Stat=N / A; Not identified name=Map; Sprite Index=382
868: Mod1=8; Mod2=1
869: Mod1=8
870: Mod1=8; Mod2=6
871: Mod1=8; Mod2=12
872: Mod1=8; Mod2=22
873: Mod1=12; Mod2=0
874: Mod1=12; Mod2=6
875: Mod1=12
876: Mod1=12; Mod2=26
877: Mod1=12; Mod2=34
878: Mod2=8
902: Mod1=1
903: Mod1=1; Mod2=2
904: Mod1=1; Mod2=5
905: Mod1=1; Mod2=8
906: Mod1=1; Mod2=11
1022: Pic File=item281; Name=Power Stone; Equip Stat=N / A; Skill Group=Misc; Not identified name=Stone; Sprite Index=137
1023: Pic File=item297; Name=Power Stone; Equip Stat=N / A; Skill Group=Misc; Not identified name=Stone; Sprite Index=138
1051: Pic File=gem2; Name=Crafting Moonstone; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=396
1052: Pic File=gem3; Name=Crafting Topaz; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=397
1053: Pic File=gem5; Name=Crafting Amethyst; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=399
1054: Pic File=item214; Name=Crafting Amber; Equip Stat=Gem; Skill Group=Misc; Not identified name=Crafting Item; Sprite Index=145
1055: Pic File=gem7; Name=Crafting Purple Topaz; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=401
1056: Pic File=gem4; Name=Crafting Ruby; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=398
1057: Pic File=gem8; Name=Crafting Sunstone; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=402
1058: Pic File=gem9; Name=Crafting Emerald; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=403
1059: Pic File=gem10; Name=Crafting Sapphire; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=404
1060: Pic File=gem1; Name=Crafting Diamond; Equip Stat=Gem; Skill Group=Misc; material=5; Not identified name=Crafting Item; Sprite Index=395
1061: Pic File=crysball; Name=The Eye; Equip Stat=Gem; Skill Group=Misc; material=1; Not identified name=Crafting Item; Sprite Index=354
1062: Pic File=6hglass; Name=Hourglass of Creation; Equip Stat=Gem; Skill Group=Misc; material=2; Not identified name=Crafting Item; Sprite Index=351
1063: Pic File=7item361; Name=Crafting Cube; Equip Stat=Gem; Skill Group=Misc; Mod2=1; material=2; Not identified name=Crafting Item; Sprite Index=296
1064: Pic File=item327; Name=Misterious Mirror; Equip Stat=Gem; Skill Group=Misc; Not identified name=Crafting Item; Sprite Index=126
1065: Pic File=7item362; Name=Ascension Emerald; Equip Stat=Gem; Skill Group=Misc; material=3; Not identified name=Crafting Item; Sprite Index=300
1066: Pic File=wytprl; Name=Scouring Pearl; Equip Stat=Gem; Skill Group=Misc; material=4; Not identified name=Crafting Item; Sprite Index=367
1067: Pic File=memcryst; Name=Oracle's Orb; Equip Stat=Gem; Skill Group=Misc; material=1; Not identified name=Crafting Item; Sprite Index=411
1309: Mod1=1d18; Mod2=30
1310: Mod1=3d9; Mod2=30
1311: Mod1=3d15; Mod2=30
1326: Mod1=1; Mod2=19
1329: Mod1=2d8; Mod2=24
1337: Mod1=1; Mod2=24
1372: Pic File=null; Name=_artifact570; Value=0; Equip Stat=0; Skill Group=0; Mod1=0; Mod2=0; material=0; ID/Rep/St=0; Not identified name=_artifact570; Sprite Index=153; VarA=0; VarB=0; Equip X=0; Equip Y=0
1574: Name=Empty Message Scroll; Value=0
1621: Mod1=2d2
1668: Mod1=6; Mod2=0
1669: Mod1=8; Mod2=2
1670: Mod1=8; Mod2=5
1671: Mod1=8; Mod2=11
1672: Mod1=8; Mod2=20
1673: Mod1=10; Mod2=0
1674: Mod1=12
1675: Mod1=12
1676: Mod1=12; Mod2=24
1677: Mod1=12; Mod2=32
1678: Mod2=0
1702: Mod1=1
1703: Mod1=1; Mod2=2
1704: Mod1=1; Mod2=5
1705: Mod1=1; Mod2=8
1706: Mod1=1; Mod2=11
2020: Mod1=2d6; Mod2=15
```

Notes cells to take verbatim from MAW (113): 282, 290, 500-502, 504-510, 513-515, 518, 520-523, 525, 527-529, 532-537,
888, 898, 922, 1022-1023, 1051-1066, 1302-1303, 1305, 1307-1309, 1312, 1314, 1317-1319, 1321-1323, 1325-1327, 1330,
1333-1338, 1372, 1442, 1465, 1629, 1637, 1641, 1651, 1658, 2021-2046, 2049, 2081, 2094, 2105.

### 3.4 rnditems.txt: base -> MAW

#### 3.4.1 Title, header and footer blocks

- Non-item rows identical in base and MAW (after trimming): yes. Raw text identical: yes.
- The file has no ring/amulet or other extra tables; after the item list (ending at 2200) there are four blank
  rows and this block, unchanged by MAW and equal to OpenYAMM's random_items.txt and code constants:

```
Bonus chance by level %		1	2	3	4	5	6
	Standard	0	40	40	40	40	75
	Special	0	0	10	15	20	25
Weapons	Special %	0	0	10	20	30	50
```

#### 3.4.2 Changed item rows

93 rows changed, 196 cells; all in weight columns 3, 4, 5, 6. No MAW-only or base-only ids. Item names refer to
MAW ITEMS.txt names where they differ.

| Item # | Name (MAW ITEMS) | Base L1-6 | MAW L1-6 | Ours L1-6 | Commit |
|---|---|---|---|---|---|
| 146 | Focal Ring | 0 0 0 0 20 30 | 0 0 0 0 0 10 | = base | c2e0e17e 2023-08-30 |
| 252 | Pure Power | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 253 | Pure Wisdom | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 254 | Pure Resilience | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 255 | Greater Element | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 256 | Darkness | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 257 | Divine Blessing | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 258 | Twilight | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 259 | Transcendence | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 260 | Dawn | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 261 | Pure Elemental Resistance | 0 0 0 2 1 0 | 0 0 0 0 2 1 | = base | 30a2eea7 2024-01-26 |
| 264 | Pure Luck | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 265 | Pure Speed | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 266 | Pure Intellect | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 267 | Pure Endurance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 268 | Pure Personality | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 269 | Pure Accuracy | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 270 | Pure Might | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 271 | Rejuvenation | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 272 | Essence of Might | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 273 | Essence of Intellect | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 274 | Essence of Personality | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 275 | Essence of Endurance | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 276 | Essence of Accuracy | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 277 | Essence of Speed | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 278 | Essence of Luck | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 279 | Potion of Doom | 0 0 0 2 1 0 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 280 | Divine Boost | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 281 | Divine Protection | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 282 | Divine Transcendence | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 283 | Potion of the Gods | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | c2e0e17e 2023-08-30 |
| 284 | Pure Fire Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 285 | Pure Air Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 286 | Pure Water Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 287 | Pure Earth Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 288 | Pure Mind Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 289 | Pure Body Resistance | 0 0 0 0 2 1 | 0 0 0 0 0 0 | = base | 30a2eea7 2024-01-26 |
| 318 | Invisibility | 0 0 2 1 0 0 | 0 0 0 1 1 0 | = base | 4d7f38d1 2025-09-11 |
| 418 | Invisibility | 0 0 0 1 0 0 | 0 0 0 0 1 0 | 0 0 0 2 1 0 | a1d6693c 2025-09-09 |
| 700 | Rejuvenation Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 701 | Pure Might Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 702 | Pure Accuracy Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 703 | Pure Personality Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 704 | Pure Endurance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 705 | Pure Intellect Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 706 | Pure Speed Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 707 | Pure Luck Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 708 | Slaying Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 709 | Stone To Flesh Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 710 | Might Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 711 | Intellect Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 712 | Personality Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 713 | Endurance Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 714 | Speed Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 715 | Accuracy Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 716 | Flaming Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 717 | Freezing Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 718 | Noxious Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 719 | Shocking Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 720 | Swift Potion Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 721 | Cure Paralysis Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 722 | Divine Restoration Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 723 | Divine Cure Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 724 | Divine Power Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 725 | Luck Boost Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 726 | Fire Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 727 | Air Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 728 | Water Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 729 | Earth Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 730 | Mind Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 731 | Body Resistance Recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | ca14dbf0 2024-08-08 |
| 751 | Divine Boost recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 752 | Divine Protection recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 753 | Divine Transcendence recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 754 | Essence of Luck recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 755 | Potion of the Gods recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 756 | Potion of Doom recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 757 | Pure Fire Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 758 | Pure Air Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 759 | Pure Water Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 760 | Pure Earth Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 761 | Pure Mind Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 762 | Pure Body Resistance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 763 | Essence of Might recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 764 | Essence of Intellect recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 765 | Essence of Personality recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 766 | Essence of Accuracy recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 767 | Essence of Endurance recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 768 | Essence of Speed recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 769 | Protection from Magic recipe | 0 0 0 0 1 1 | 0 0 0 0 0 0 | = base | 3bd64361 2024-03-27 |
| 1120 | Invisibility | 0 0 2 1 0 0 | 0 0 0 1 1 0 | = base | 4d7f38d1 2025-09-11 |
| 1220 | Invisibility | 0 0 0 1 0 0 | 0 0 0 0 1 0 | 0 0 0 2 1 0 | a1d6693c 2025-09-09 |
| 1820 | Invisibility | 0 0 2 1 0 0 | 0 0 0 1 1 0 | = base | 4d7f38d1 2025-09-11 |

#### 3.4.3 As a patch onto OpenYAMM random_items.txt

- Same ids, same column positions (2-7 = levels 1-6). Rows touched by both OpenYAMM and MAW: 418, 1220.

| Item # | Level | Base | Ours | MAW | Status |
|---|---|---|---|---|---|
| 418 | 4 | 1 | 2 | 0 | **conflict** |
| 418 | 5 | 0 | 1 | 1 | same change |
| 1220 | 4 | 1 | 2 | 0 | **conflict** |
| 1220 | 5 | 0 | 1 | 1 | same change |

- Patch = the MAW L1-6 values above for 93 rows; 2 cell(s) conflict with an OpenYAMM change (both sides moved
  level 4 of the Invisibility spellbooks in opposite directions); a patch generator must not blindly overwrite
  them. Everything else applies without touching an OpenYAMM change. The footer needs no patch.
- Superseded by the user's decision D4 (2026-10-24, audit DAT-3): in the MAW ruleset every spellbook row, 418 and 1220
  included, takes MAW's weights, also where only OpenYAMM changed them (the generator's `maw_keys` list,
  `tools/maw/generate_ruleset_patches.py`). Standard keeps OpenYAMM's raised weights.

### 3.5 SPCITEMS.TXT: base -> MAW

Base has 73 enchant rows (ids 1-73), MAW 80 (1-80). Header rows are identical. Ids are 1-based positions.

#### 3.5.1 Changed rows 1-73

18 of 73 rows changed, 51 cells. By column: W1 7, W2 7, Miss 7, Belt 1, Gaunt 1, Boot 1, Lvl 11, Ring 1, Amul 1, Bonus
Stat 2, Name Add 2, Value 4, Arm 2, Shld 2, Helm 2.
Suffix text (column 1, the kind key in our parser) changed on: 39, 40.

| Id | Suffix (base) | Changed cells (base -> MAW) | Commit |
|---|---|---|---|
| 1 | of Protection | W1: `0` -> `5`; W2: `0` -> `5`; Miss: `0` -> `5`; Belt: `0` -> `10`; Gaunt: `0` -> `10`; Boot: `0` -> `10`; Lvl: `B` -> `D` | 20e7b38a 2024-08-13 |
| 20 | of Freedom | Lvl: `D` -> `C` | eab2c750 2024-01-05 |
| 23 | of The Medusa | Lvl: `D` -> `C` | eab2c750 2024-01-05 |
| 36 | of Shielding | Ring: `5` -> `0`; Amul: `5` -> `0`; Lvl: `B` -> `D` | be767fb3 2024-11-11 |
| 39 | Ogre Slaying | Bonus Stat: `Double Damage vs. Ogres` -> `Spell damage+int/pers`; Name Add: `Ogre Slaying` -> `of Ascension`; W1: `20` -> `10`; W2: `20` -> `10`; Miss: `20` -> `10`; Lvl: `A` -> `D` | ca14dbf0 2024-08-08 |
| 40 | Dragon Slaying | Bonus Stat: `Double damage vs Dragons` -> `Spells Drain Hit points from target and Increased Spell speed.`; Name Add: `Dragon Slaying` -> `Lichs'`; W1: `20` -> `5`; W2: `20` -> `5`; Miss: `20` -> `5`; Value: `X 2` -> `X 3`; Lvl: `A` -> `D` | 306abc05 2025-08-16 |
| 42 | of Doom | Value: `750` -> `2000`; Lvl: `B` -> `C` | c6ddd1ac 2023-11-26 |
| 44 | of Life | Value: `2000` -> `1500`; Lvl: `D` -> `C` | 29774f5a 2025-10-31 |
| 47 | of The Eclipse | Lvl: `D` -> `C` | f0675503 2024-11-14 |
| 53 | of The Sun | Value: `1000` -> `1500` | c6ddd1ac 2023-11-26 |
| 54 | of The Troll | Lvl: `C` -> `D` | 29774f5a 2025-10-31 |
| 55 | of The Unicorn | Lvl: `C` -> `D` | 06913190 2024-10-27 |
| 63 | Elemental Slaying | W1: `20` -> `0`; W2: `20` -> `0`; Miss: `20` -> `0` | 06913190 2024-10-27 |
| 64 | Undead Slaying | W1: `20` -> `0`; W2: `20` -> `0`; Miss: `20` -> `0` | 06913190 2024-10-27 |
| 67 | Assassins' | W1: `20` -> `0`; W2: `20` -> `0`; Miss: `20` -> `0` | c6ddd1ac 2023-11-26 |
| 68 | Barbarians' | W1: `20` -> `0`; W2: `20` -> `0`; Miss: `20` -> `0` | c6ddd1ac 2023-11-26 |
| 69 | of the Storm | Arm: `20` -> `0`; Shld: `20` -> `0`; Helm: `20` -> `0` | c6ddd1ac 2023-11-26 |
| 70 | of the Ocean | Arm: `20` -> `0`; Shld: `20` -> `0`; Helm: `20` -> `0` | c6ddd1ac 2023-11-26 |

Slot weights as full vectors for the changed rows (W1 W2 Miss Arm Shld Helm Belt Cape Gaunt Boot Ring Amul):

```
 1 of Protection          base  0  0  0 10 10 10  0 10  0  0 10 10 | MAW  5  5  5 10 10 10 10 10 10 10 10 10
20 of Freedom             base  0  0  0 10 10 10 10 10  0  0 10 10 | MAW  0  0  0 10 10 10 10 10  0  0 10 10
23 of The Medusa          base  0  0  0  5  5  5  5  5  0  0  5  5 | MAW  0  0  0  5  5  5  5  5  0  0  5  5
36 of Shielding           base  0  0  0 25 30  0  0 20  0  0  5  5 | MAW  0  0  0 25 30  0  0 20  0  0  0  0
39 Ogre Slaying           base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW 10 10 10  0  0  0  0  0  0  0  0  0
40 Dragon Slaying         base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW  5  5  5  0  0  0  0  0  0  0  0  0
42 of Doom                base 10 10 10 10 10 10 10 10 10 10 10 10 | MAW 10 10 10 10 10 10 10 10 10 10 10 10
44 of Life                base  0  0  0 10 10 10 10 10 10 10 10 10 | MAW  0  0  0 10 10 10 10 10 10 10 10 10
47 of The Eclipse         base  0  0  0  0  0  0 10 10  5 10 10 10 | MAW  0  0  0  0  0  0 10 10  5 10 10 10
53 of The Sun             base  5  5  5 10 10 10 10 20 20 10 10 10 | MAW  5  5  5 10 10 10 10 20 20 10 10 10
54 of The Troll           base  5  5  5 20 20 10 10 10 10 10 10 10 | MAW  5  5  5 20 20 10 10 10 10 10 10 10
55 of The Unicorn         base  5  5  5 10 10 20 10 10 10 10 10 10 | MAW  5  5  5 10 10 20 10 10 10 10 10 10
63 Elemental Slaying      base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
64 Undead Slaying         base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
67 Assassins'             base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
68 Barbarians'            base 20 20 20  0  0  0  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
69 of the Storm           base  0  0  0 20 20 20  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
70 of the Ocean           base  0  0  0 20 20 20  0  0  0  0  0  0 | MAW  0  0  0  0  0  0  0  0  0  0  0  0
```

#### 3.5.2 New rows 74-80 (full)

| Id | Bonus Stat | Name Add | W1 | W2 | Miss | Arm | Shld | Helm | Belt | Cape | Gaunt | Boot | Ring | Amul | Value | Lvl | Description | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 74 | +10 Spell points and Regenerate Spell points over time. | Paladins' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 10 | 10 | 5 | 5 | 5 | 1500 | C | 20 per 20 acc | 20e7b38a 2024-08-13 |
| 75 | +15 Endurance and +5 Armor. | WarriorMage' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 10 | 10 | 5 | 5 | 5 | 1500 | C | 20 int 20 might | 20e7b38a 2024-08-13 |
| 76 | +10 Intellect and Luck. | Shadows' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 10 | 10 | 5 | 5 | 5 | 1500 | C | 20 int 20 acc | 20e7b38a 2024-08-13 |
| 77 | +30 Fire Resistance and Regenerate Hit points over time. | Rangers' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 2000 | C | Fire Res (+30), Regen hpts | 20e7b38a 2024-08-13 |
| 78 | +10 Spell points, Speed, Intellect. | Elementals' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 3000 | C | Int (+10), Spd (+10), SP (+10) | 20e7b38a 2024-08-13 |
| 79 | +10 Endurance and Accuracy. | Selfs' | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 3000 | C | End (+10), Acc (+10) | 20e7b38a 2024-08-13 |
| 80 | +10 Endurance and Accuracy. | Divines' | 2 | 2 | 2 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5000 | D | End (+10), Acc (+10) | 39de13ad 2024-03-14 |

Raw MAW lines (quotes as in the file):

```
 +10 Spell points and Regenerate Spell points over time.	Paladins'	5	5	5	5	5	5	5	10	10	5	5	5	1500	C	"20 per 20 acc"
 +15 Endurance and +5 Armor.	WarriorMage'	5	5	5	5	5	5	5	10	10	5	5	5	1500	C	"20 int 20 might"
 +10 Intellect and Luck.	Shadows'	5	5	5	5	5	5	5	10	10	5	5	5	1500	C	"20 int 20 acc"
 +30 Fire Resistance and Regenerate Hit points over time.	Rangers'	5	5	5	5	5	5	5	5	5	5	5	5	2000	C	"Fire Res (+30), Regen hpts"
" +10 Spell points, Speed, Intellect."	Elementals'	5	5	5	5	5	5	5	5	5	5	5	5	3000	C	"Int (+10), Spd (+10), SP (+10)"
 +10 Endurance and Accuracy.	Selfs'	5	5	5	5	5	5	5	5	5	5	5	5	3000	C	"End (+10), Acc (+10)"
 +10 Endurance and Accuracy.	Divines'	2	2	2	5	5	5	5	5	5	5	5	5	5000	D	"End (+10), Acc (+10)"
```

#### 3.5.3 Non-enchant rows

Rows after the last enchant, base vs MAW (trimmed, blank rows shown as empty lines):

```
--- base
+++ MAW
@@ -1,8 +1,10 @@
+
+
 
 		505	505	505	345	315	310	245	305	200	185	375	370
 
 Treasure Level	If treasure Level = 3 add all A and B
 A= 3 to 4	If treasure Level = 4 add all A and B and C
 B= 3 to 5	If treasure Level = 5 add al B and C and D
 C= 4 to 5	If treasure Level = 6 add all D
-D= 5 to 6
+
```

The sums row (`505 505 505 345 ...`) is unchanged although MAW changed weights, so it is stale in MAW; no
loader reads it. MAW drops the `D= 5 to 6` comment row and pads blank rows to 19 tabs.

#### 3.5.4 As a patch onto OpenYAMM special_item_enchants.txt

- Rows 1-73: ours = base, so the 18 changed rows above apply by position unchanged (ours line N = base line N).
- Rows 74-80: insert the seven MAW lines directly after line 77 (`of Sparking`), before the blank, sums and
  footer rows. Ids then match MAW `Bonus2` 74-80, and the footer junk entries move from 74-77 to 81-84.
  Alternatively drop the footer comment rows (they are documentation only).
- Kinds: the MAW suffixes of 74-80 parse to `SpecialItemEnchantKind::None`; until the parser and effects are
  extended they are never rolled (`chooseSpecialEnchantId` skips `None`) and grant nothing on items that
  carry them.
- Id 39: suffix `Ogre Slaying` (kind known) -> `of Ascension` (kind None in our parser). Patching it removes
  the base effect from every item with enchant 39; nothing replaces it until MAW's effect is coded.
- Id 40: suffix `Dragon Slaying` (kind known) -> `Lichs'` (kind None in our parser). Patching it removes
  the base effect from every item with enchant 40; nothing replaces it until MAW's effect is coded.
- MAW suffixes 74-80 known to our parser: none.

## 4. Item tooltip specification

MAW builds the item box through the engine's `BuildItemInformationBox` event, which the engine raises three times
per box: once with `Name`, once with `Type`, `BasicStat` and `Enchantment`, and once with `Description`
(`Structs/extraEditableDescriptions.lua:18-24`). One handler runs registered sections in sort order
(`Modules/MawCore/Tooltip.lua:64-74`, registrations `:897-909`). The engine then lays the box out in its usual
order: name, type line, basic stat, enchantment line, description, value. Below, every line MAW produces, in that
order, with colour (RGB) and condition. "ALT" means `extraDescription`: ALT held XOR the setting "Extra Item
Tooltip" = ON (`zzMaw-Items.lua:1663-1679`).

### 4.1 Base equipment (`IsEnchantableItem`: ids 1-151, 803-936, 1603-1736 without blasters)

Side effect first: building the type pass calls `updateCelestialItem`, which rewrites a Celestial's enchant
strengths and `MaxCharges` from the current character (`Tooltip.lua:205`). A port must compute this on read.

| Line | Text | Colour | Condition | Source |
|---|---|---|---|---|
| Name | `<prefix> <item name> <suffix>`: the special's Name Add as prefix if it starts with an upper-case letter, else as suffix; with no special, the base enchant 1 suffix from STDITEMS | see rarity row | identified item, name pass | `Tooltip.lua:351-363` |
| Name colour and prefix | "Celestial " cyan (120,240,255); "Legendary " yellow (255,255,30); "Primordial " red (255,0,0); "Ancient " orange (255,128,0); else by enchant count: 3 purple (163,53,238), 2 blue (0,150,255), 1 green (30,255,0), 0 white | as listed | first match in that order | `Tooltip.lua:364-391` |
| Type | engine `Type: ...`, then `\nAttack Speed: <getItemRecovery(it, 0)/100>` | engine default | weapon whose skill has a base recovery (dagger, sword, mace, bow, staff, spear, axe, blaster) | `Tooltip.lua:716-723` |
| Basic stat, armour | `Armor: +<AC>`; AC = base + round(referenceAC x MaxCharges/40), x quality | engine default | EquipStat 3-9, base AC > 0, MaxCharges > 0 (otherwise the engine's own `Armor: +N`) | `Tooltip.lua:209-238` |
| Basic stat, weapon | `Attack: +<bonus>  Damage: <min>-<max>` (two spaces) from `GetWeaponDamageMinMax` | engine default | EquipStat 0-2, always | `Tooltip.lua:240-250` |
| Quality suffix | `\nQuality bonus: +<q>%` appended to the basic stat | orange (255,190,90) | cube quality q > 0 | `zzMaw-Items.lua:748-754` |
| Enchantment, enchant 1 | `<stat name> +<power>`; HP/SP shown as round(p x (1 + min(p/50/slotMult, 5))); hats/crowns ceil(p x 1.5); resistances as `<reduction>%` of (p + 10), x1.5 first with legendary 16 on the current character | stat name coloured, number default | `Bonus > 0` | `Tooltip.lua:254-275` |
| Enchantment, enchant 2 | same format, placed ABOVE enchant 1 (`enc2 \n enc1`) | as above | second enchant present | `Tooltip.lua:276-297` |
| ALT preview, Hourglass | `<stat> +<strength>` above the existing lines; the whole block re-wrapped in grey | grey (100,100,100) | ALT, enchant 1 present, no enchant 2 | `Tooltip.lua:298-331` |
| ALT preview, Enchant Item | `<stat> +X` | grey | ALT, item with no enchant at all | `Tooltip.lua:333-350` |
| Description, legendary | affix text (affixes 21 and 22 add a live line, see legendary_affixes.yml); replaces the flavour text | yellow (255,255,30) | legendary affix | `Tooltip.lua:392-425` |
| Description, special | special text: `checktext` with scaled numbers, or the overridden SPCITEMS text; then a blank line | light yellow (255,255,153) | `Bonus2 > 0` | `Tooltip.lua:426-433` |
| ALT preview, Eye | text of the special the Eye of Void would add | grey | ALT, enchant 1 present, no special | `Tooltip.lua:434-464` |
| Hint | `Press alt to show craftable stats` | grey | enchant 1 with strength, not ALT, no preview shown before in this save (`vars.extraShown`) | `Tooltip.lua:465-469` |
| Item power | `Item Bonus Power: <MaxCharges>/255` | grey | ALT | `Tooltip.lua:471-474` |
| Fire Aura | `<Fire|Flame|Inferno|Hell> Aura: adds <N> Fire Damage to any attack` and a blank line, prepended | light yellow | weapon, buff rework ON, Fire Aura active, mastery >= 1 | `Tooltip.lua:728-744` |
| Vampiric Aura | `Vampiric Aura: damage done will restore player HP.` and a blank line, prepended | light yellow | weapon, buff rework ON, Vampiric Aura active | `Tooltip.lua:745-750` |
| Power | `Power: +x%` green (0,255,0) or `Power: -x%` red (255,0,0); x = change of the best of melee/ranged/spell DPS, 2 decimals | green/red | EquipStat <= 11, current character has an item in the matching slot (`slotMap`), change not 0 | `Tooltip.lua:579-689`, `slotMap` `zzMaw-Items.lua:2495-2508` |
| Vitality | `Vitality: +y%` / `-y%` | green/red | as Power | same |
| Level | `Level Required: <N>` after a blank line | red (255,0,0) if the current character's LevelBase < N, else default | base equipment | `Tooltip.lua:692-714` |
| Celestial | `Celestial Items cannot be upgraded with crafting Gems or Cubes, but scale with player level, up to level 600.` (1000 in Beyond Madness), replacing the level line | cyan (120,240,255) | Celestial | `Tooltip.lua:706-711` |
| Value | engine `Value: <N>`, N from `events.CalcItemValue`: getItemValue x0.4 outside shops; in buy screens value^(1 + 0.08 x count) | engine default | always | `zzMaw-Items.lua:1897-2009` |

Stat name colours (`itemStatName`, `zzMaw-Items.lua:1682-1708`): Might (255,0,0), Intellect (255,128,0),
Personality (0,127,255), Endurance (0,255,0), Accuracy (255,255,0), Speed (127,0,255), Luck (255,255,255),
Hit Points (0,255,0), Spell Points (0,100,255), Armor Class (230,204,128), Fire Resistance (255,70,70), Air
Resistance (173,216,230), Water Resistance (100,180,255), Earth Resistance (153,76,0), Mind Resistance
(200,200,255), Body Resistance (255,192,203), skills 17-24 "<Skill> skill" (255,255,153). Enchant 18 is labelled
"Repair skill".

### 4.2 Artifacts (and the four blasters)

| Line | Text | Colour | Condition | Source |
|---|---|---|---|---|
| Description | the table note with its leading `(...)` and any `(Special ...)` part removed | default | artifact | `Tooltip.lua:495-509` |
| Stat lines | `<stat name>: <signed value>`, sorted by stat id | stat colours; negative numbers red (255,64,64) | each non-zero stat of `Artifacts.BonusesOf` | `Tooltip.lua:510-516` |
| Skill lines | `<Skill> skill: <signed value>` | label (255,255,153) | each skill bonus | `Tooltip.lua:517-523` |
| On-hit lines | text from `MawArtifactOnHitText` | orange (255,170,60) | on-hit rules | `Tooltip.lua:524-528` |
| Artifact level | `Artifact Level: <party total level>` after a blank line | cyan (120,240,255) | always | `Tooltip.lua:532-533` |
| Basic stat | `Armor: +<AC>` (level-scaled, x base multiplier, x quality) or `Attack: +B  Damage: lo-hi` | default | armour with AC > 0 / weapon | `Tooltip.lua:537-560` |
| Type | `\nAttack Speed: <x>` appended | default | weapon skill with a base recovery | `Tooltip.lua:561-573` |

Power/Vitality lines appear as for base items. No level-requirement line.

### 4.3 Other item kinds (out of item-data scope, listed for completeness)

Potions (charges, heal amounts, ALT recipe list), reagents (`Power: N`), gems and the special crafting items
(tier, caps, Oracle's Orb affix, Celestial Orb state, Endless Potion charges), maps (item 290: map level, affixes,
craft/quality/density bonuses) and skill books (`You need at least <mastery> skill in <skill>`), sections 100-130,
300 and 320 of `Tooltip.lua`. Section 130 performs crafting while the tooltip is built; a port must not.

### 4.4 Port notes

- Compute everything from a read-only item and a character snapshot; MAW mutates the item (Celestial) and the
  equipped item (comparison swap, `Tooltip.lua:604-678`).
- Fix the enchant-2 resistance +10, or document it.
- The `Attack Speed` number is base recovery / 100 (lower is faster); print it as an interval or as DPS.

## 5. Proposed OpenYAMM item record

### 5.1 What OpenYAMM has

`InventoryItem` (`game/party/Party.h:45-66`): `objectDescriptionId`, `quantity`, size and grid position,
`identified`, `broken`, `stolen`, `hardened`, `standardEnchantId` (u16), `standardEnchantPower` (u16),
`specialEnchantId` (u16), `artifactId` (u16), `ItemRarity rarity` (Common/Artifact/Relic/Special,
`game/tables/ItemTable.h:26-32`), `currentCharges`, `maxCharges` (u16, wand charges),
`temporaryBonusRemainingSeconds`. `EquippedItemRuntimeState` (`game/party/CharacterState.h:128-142`) repeats the
same fields per equipment slot. Save code: `writeValue`/`readValue` for `InventoryItem` at
`game/maps/SaveGame.cpp:535-576` and for `EquippedItemRuntimeState` at `:729` and `:745`; `SaveVersion` is 93
(`:24`), the latest item gate is `SaveVersionHardenedItems = 92` (`:104`).

### 5.2 What MAW stores per item

| MAW field | Meaning | Range | OpenYAMM home |
|---|---|---|---|
| `Bonus` / `BonusStrength` | base enchant 1 type / strength | 1-24 / 0-65535 in practice | existing `standardEnchantId` / `standardEnchantPower` |
| `Charges` bits | base enchant 2 | type 0-63, strength 0-65535 | new `secondEnchant` |
| `Bonus2` | special enchant | 1-80 | existing `specialEnchantId` |
| `MaxCharges` | item power | 0-255 | new `itemPower` (do not reuse `maxCharges`, which wands use) |
| `BonusExpireTime` bits 6-7 | Ancient 1 / Primordial 2 | 0-2 | new `ancientTier` |
| bits 0-5 | legendary affix (id - 10) | 0-25 | new `legendaryAffixId` (store 11-35) |
| bit 8 | Celestial | bool | new `celestial` |
| bits 9-19 | drop level | 0-2047 | new `dropLevel` |
| bits 20-24 | cube quality % | 0-20 | new `qualityPercent` |
| (derived) | rarity Common..Celestial | 1-8 | new `lootRarity`, stored |
| (derived from fields) | crafting preview seed | | new `craftSeed` |
| `Charges` (potions) | potion charges | | existing `currentCharges` (alchemy scope) |

### 5.3 Proposal

```cpp
struct ItemAffixRoll
{
    uint16_t typeId = 0;   // standard enchant type 1-24 (MAW range 0-63)
    uint16_t power = 0;    // stored strength, before read transforms
};

// Loot-rule data of one item. All zero = a vanilla item (Standard ruleset, quest items, potions, artifacts).
struct ItemLootData
{
    uint8_t lootRarity = 0;        // 0 = none, 1..8 = Common..Celestial; stored, never derived
    uint8_t ancientTier = 0;       // 0, 1 = Ancient, 2 = Primordial
    bool celestial = false;
    uint8_t legendaryAffixId = 0;  // 0 or 11..35 (legendary_affixes.yml keys)
    uint16_t itemPower = 0;        // MAW MaxCharges; item level = 5 * itemPower
    uint16_t dropLevel = 0;        // level the item was generated at; drives the level requirement
    uint8_t qualityPercent = 0;    // Pandora's Cube, 0..20
    ItemAffixRoll secondEnchant;   // MAW base enchant 2
    uint32_t craftSeed = 0;        // deterministic crafting previews; set at generation
};
```

- Add `ItemLootData loot;` to both `InventoryItem` and `EquippedItemRuntimeState`, and copy it in
  `makeInventoryItem(..., runtimeState)` and `copyItemToEquippedRuntimeState` (`Party.cpp:1538`, `:1670`, per
  [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md)).
- Keep `standardEnchantId/Power` as enchant 1 and `specialEnchantId` as the special, so Standard code and saves
  are unchanged. Keep OpenYAMM's `ItemRarity` (artifact/relic/special material class) separate from
  `lootRarity`; they answer different questions.
- Store `lootRarity` explicitly. MAW derives it from the tier bits and the enchant count (`MawItemRarity`,
  `zzMaw-Items.lua:691-715`), so removing an enchant with the Pearl lowers the rarity of a Rare or Epic item.
- Artifacts need no per-item level: MAW reads the party total level live and never reads the level it writes
  (artifacts.yml `rules.level`). They can carry `qualityPercent`.
- Celestial values are computed on read from the wearer; do not write them back (`updateCelestialItem`).
- The second enchant's power must allow 16 bits (MAW clamps at 65535); in practice it stays below a few hundred.

### 5.4 Save format

- One new gate, for example `SaveVersionItemLootData = <next free version>` (the ruleset investigation reserves
  94 for the ruleset id; both can share one bump).
- Write after `hardened` in `writeValue(InventoryItem)` and at the end of `EquippedItemRuntimeState`: one
  presence byte, then the fields only when the record is not all zero. Standard saves grow by one byte per item.
  Read with `(reader.version() < SaveVersionItemLootData || readValue(reader, value.loot))`.
- `InventoryItem` is also the record for world items, chests, corpses, house stock and the held item, so the one
  change covers them all (`SaveGame.cpp:3828`, `:3924-4042` for the content-package scan, which needs no change).
- Per-save MAW state that is not per item belongs in the ruleset block of `GameSaveData`: pity counters
  (primordial, legendary, celestial, artifact roll, per-artifact counts keyed by item id rather than MAW's list
  position, per-affix counts, crafting-item counters), the save seed and per-stream counters (replacing
  `vars.SeedList`, `enchantSeedList`, monster and boss seeds), shop kinds, loot-filter setting, and the
  "preview shown" flag if the hint is kept.
- Migration: a Standard save never contains `ItemLootData`; switching rulesets is not supported mid-game, so no
  conversion of existing items is needed.

## 6. Corrections to existing docs

Not edited here; listed for the owners of those files.

[README.md](README.md):

- §4.4, `items.txt` row: MAW's ITEMS.txt fills only 1051-1067 among the crafting ids; 1041-1050 and 1068-1070
  remain `_potion/reagent` placeholders and get their names from Lua. The renamed potions are 224-263 (35 rows),
  not 221-263. "DeathBlade removed" is most likely base cleanup (the base row is marked as a test item).
- §4.4, `random_items.txt` row: MAW zeroes potions 264-289 and recipe scrolls 700-731 and 751-769 (732-750 are
  not touched), moves black potions 252-261 from levels 4-5 to 5-6, cuts the Focal Ring (146) and re-weights the
  Invisibility spellbooks 318, 418, 1120, 1220, 1820. Two of those cells (418 and 1220, level 4) conflict with
  OpenYAMM's own spellbook re-weighting.
- §4.4, `special_item_enchants.txt` row: ids 74-77 are not free in our loader (footer comment rows load as junk
  entries), and renaming 39/40 removes our Ogre/Dragon Slaying kinds. See sections 3.2.3 and 3.5.4.
- §4.4, group 3: the README lists 98 artifacts; that is the number of budget entries. The drop list has 104
  entries and 103 unique ids.

[ITEMS.md](ITEMS.md):

- §1.5 type roll: the Dodge swap applies to Chain and Plate (skills 10 and 11), not Leather and Chain; the
  Unarmed swap applies to weapons of skills 1-7, so staves keep Unarmed. Enchant 2 resistances are re-rolled on
  every item, rings included, so rings only get a resistance as enchant 1.
- §1.5 strength: the hat/crown x1.5 is applied when stats are read, not at generation.
- §1.6: weapon damage is capped at item power 100 (item level 500); armour AC is not.
- §1.9: the printed attack speed is rounded to tens of recovery (axe at item level 0 prints 1.1, not 1.05).
  Clubs (Skill 39) have no base recovery and stay at 1.0.
- §1.11: the reroll's extra strength is rolled before each slot with `random(1,18) < MMLVL % 18` and stays
  raised for the remaining slots. The armour kinds `{31,32,33,34,5}` are used for armour and shield slots in any
  shop, not "armour shops".
- §1.13 SPCITEMS: Protection moved B -> D (it was B in base, not A). Also changed: Life D -> C, Eclipse D -> C,
  Ogre/Dragon Slaying (39/40) A -> D, Doom B -> C. Slot chances zeroed: Elemental and Undead Slaying (63, 64),
  Assassins' and Barbarians' (67, 68) on weapons, Storm and Ocean (69, 70) on armour, shield and helm, Shielding
  (36) on rings and amulets.
- §1.13 rnditems: see the README item above (recipe scrolls 700-731 and 751-769).
- §4.1: 104 list entries, 103 unique ids (533 twice); 98 is the number of `artifactPower` budgets.
- §4.2: the level written into a dropped artifact is never read; `artifactPowerMult` is dead; "Vampiric"
  artifacts do nothing; the startup dice doubling still feeds the weapon-skill AC and resistance bonus. Details in
  [data/artifacts.yml](data/artifacts.yml).
- §4.3: affix 21 multiplies every damage in its stage, not only melee; affix 22 is multiplicative (0.97^n,
  floored at 0.5); affix 13 blocks conditions from any source; affix 17 also halves for arrows.
- §6: the enchant-2 resistance line shows +10 that the stats do not get.
- §8.2: quest artifacts in chests are replaced only when their Value is at least 20000.

## 7. Not covered

- Rarity distribution tables and the PDF comparison ([RANDOMS.md](RANDOMS.md)).
- Crafting items, gems, cube quality steps, potion crafting and their previews ([CRAFTING.md](CRAFTING.md)).
  loot.yml lists shop prices and drop substitution only.
- Potions, reagents and alchemy (charges, effects, recipes): [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md).
- Dimension maps (item 290) and map affixes beyond their loot-tier and rarity bonuses.
- The balance model (`Estimates.lua`) beyond `getWeaponLevelDamage`, and Power/Vitality
  (`calcPowerVitality`): [COMBAT.md](COMBAT.md).
- How skills scale weapon damage, AC and resistances (`addWeaponRows`, `addArmorSkillAC`, `addWeaponACRes`) and
  the leech formula: [COMBAT.md](COMBAT.md).
- Multibag, crafting bag, sorter, Randomizer and the K pull key ([ITEMS.md](ITEMS.md) §4.4, §5).
- Multiplayer item sync (`Modules/MawCore/Sync.lua`).
- Other text tables in `zMaw.T.lod` (MONSTERS, mapstats, POTION, POTNOTES, class, Placemon) and
  `Data/Tables/Potion settings.txt`.
- Runtime verification: nothing was run inside MMExtension; values come from reading and from running MAW
  functions outside the game.
