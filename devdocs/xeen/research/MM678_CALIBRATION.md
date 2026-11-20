# MM6–MM8 world calibration (and MM9 as reworked)

These are the numbers behind "what a good MM6–MM8 world contains", measured from the installed OpenYAMM data on
2026-11-11, for designing a new world in the same style. Xeen source material is covered separately.

**How the numbers were made.** Python over:
- `assets_dev/worlds/<w>/maps/*.scene.yml` (placed actors, spawn points, entities). Overlay scenes are skipped.
- BLV geometry through `util/map_export.parse_blv_file`: faces, sectors, door count, and floor area
  (facet types 3/4, portals skipped).
- Map Lua `contextActions`: `enter_house` house ids, chest ids, and the well / fountain / shrine / obelisk / pedestal
  kinds.
- `engine/data_tables/map_stats.txt`, `house_data.txt`, `outdoor_travels.txt`, `transport_locations.txt`,
  `town_portal_switch.txt`, and `monster_data.txt` (levels of the family's A, B and C rows).
- For MM9, `worlds/mm9/data_tables/{vendors,service_venues,transport_routes,map_transitions}.txt`.

**Definitions used throughout:**
- **Est. mons**: the monsters on a first visit under the original rules. It adds the placed hostile actors, the
  fixed-tier spawns (spawn index 4–12, one monster each), and each group spawn (index 1–3) times the mean of its
  map_stats count range (e.g. `3-5` counts as 4).
- MM6 counts include peasants, which MM6 places as monster spawns.
- **Dif** is the A/B/C tier odds of a group spawn, from the original table:

  | d1 | d2 | d3 | d4 | d5 |
  |---|---|---|---|---|
  | 90/8/2 | 70/20/10 | 50/30/20 | 30/40/30 | 10/50/40 |

- **Chests** are chest slots that are stocked in the scene and opened by the map's events. For MM9 they are the
  `obj_treasurechest*` props.
- **Floor tiles** is the floor area in 512×512 units, the size of one outdoor terrain tile. An ODM is 128×128 tiles.
- **Hops** counts map-edge or obvious boat links from the start map. `boat/tun` marks maps reached only by boat,
  tunnel or portal.
- **Services**: W weapon, A armour, M magic, Al alchemist, G guilds, Tm temple, Tv tavern, Bk bank, Tr training,
  St stables, Bt boats, TH town hall / throne / castle, Se seer, Ci Circus of the Sun tent, Inn Adventurer's Inn.
  MM9 adds Gen (general store) and Lib (library).
- **Res**: residences (enterable `House` entries).
- **Dungeons**: `.blv` files a map's events move the party to. Some MM6–MM8 entrances go through house dialogs and
  are not counted.
- **Tres**: map_stats treasure level 0–6. **MM6 has 6 on every map, so it carries no information there.** For MM6,
  read difficulty from Lock/Trap (0–20 / 0–10) and the item spawn levels.

## 0. Headline numbers

| | MM6 Enroth | MM7 Antagarich | MM8 Jadame | MM9 Chedian (rework) |
|---|--:|--:|--:|--:|
| Outdoor maps (playable) | 15 | 13 | 9 + 4 planes (+ tutorial) | 19 open-air BLVs (12 regions + 7 cities) |
| Indoor maps (real dungeons) | 37 (+ arena, Oracle, NWC, 13 MMerge stubs) | 61 (+ arena, NWC) | 45 (+ arena, NWC) | 24 (+ arena) |
| Outdoor maps with a town (≥1 shop/temple/tavern) | 12 | 11 | 9 | 7 cities + 2 villages (Lindisfarne, Yorwick) |
| Est. monsters on an outdoor map, median / max | 202 / 410 | 122 / 288 | 165 / 261 | 57 / 139 (placed only) |
| Est. monsters in a dungeon, median / mean / max | 113 / 142 / 474 | 37 / 46 / 184 | 35 / 42 / 142 | 54 / 76 / 239 |
| Dungeon class S (<40) / M (40–100) / L (>100) | 4 / 13 / 20 | 31 / 26 / 4 | 25 / 18 / 2 | 10 / 8 / 6 |
| Dungeon median faces / sectors | 2231 / 50 | 1993 / 20 | 1844 / 15 | 7594 tris / 25 |
| Chests: outdoor total (median per map) | 68 (3) | 88 (7) | 95 (6) | 27 (1) |
| Chests: indoor total (median per dungeon) | 262 (7) | 317 (4) | 204 (2) | 111 (4) |
| Est. monsters, whole world | ≈8,650 | ≈4,470 | ≈4,130 | ≈2,330 hostile placed (BALANCE_PLAN: 2,723 counted) |
| Item spawn points by level L1…L6(7) | 117/103/87/61/21/25 | 254/170/272/278/242/116 | 4/15/18/40/20/62/14 | 27/38/82/71/84/91 |
| Wells / fountains / shrines / obelisks / pedestals | 19/40/29/16/5 (+14 boosts) | 40/6/17/15/0 | 27/6/0/9/0 | 1/0/10/0/0 |

Services, summed over the outdoor maps:

| Services | MM6 | MM7 | MM8 | MM9 |
|---|---|---|---|---|
| Shops | W14 A14 M15 Al4 | W8 A8 M7 Al6 | W6 A6 M7 Al5 | W8 A8 M16 Al5 Gen6 Lib6 |
| Guilds | 36 | 27 | 9 | – |
| Temple / tavern / bank / training | 14 / 21 / 6 / 10 | 9 / 11 / 5 / 7 | 6 / 11 / 4 / 5 | 8 / 7 / 7 / 8 |
| Stables / boats | 9 / 12 | 7 / 6 | 5 / 6 | 8 docks |
| Halls / castles | 12 | 3 | 1 | – |
| Residences | 308 | 181 | 224 | (houses are walk-in rooms) |

**Reading the headline:**
- **MM6 is the dense, grindy end.** It has about 200 monsters per outdoor map, big dungeons (median 113 monsters,
  50 sectors) and a guild for every school. Gameplay is spawn-driven: wilderness maps have almost no placed actors,
  only spawn points.
- **MM7 and MM8 are the calibrated middle.**
  - Outdoors: 120–170 monsters per map.
  - Dungeons: many small ones. The median is about 35–40 monsters, 15–20 sectors and 2–4 chests.
  - A few large set pieces: MM7 Castle Harmondale, Nighon and Eeofol tunnels, the Maze; MM8 the Wasp Nest and the
    Abandoned Temple.
- **MM9 as reworked** has fewer, larger fights per map. All monsters are placed; there are no respawning spawn
  points. Its density was grown toward MM7 by act, see §6.

## 1. Per-world map tables

Columns are defined in the introduction. The MM9 "Placed" column counts hostile placed actors; MM9 has no monster
spawn points. MM9 map_stats rows carry no Dif values.

#### MM6 outdoor maps
| Map | Name | Hops | Services | Res | Dungeons | Monster families (dif, level A–C) | Tres | Lock/Trap | Placed+spawns (grp/fix/item) | Est. mons | Chests | Well/Fount/Shrine/Obel/Ped |
|---|---|--:|---|--:|---|---|--:|---|---|--:|--:|---|
| oute3 | New Sorpigal | 0 | A Al Bk Bt G4 M St TH Tm Tr Tv W | 22 | 3 | BGoblin d1 L4-10; PeasantM2 d1 L2-10 | 6 | 0/1 | 43 + 40/16/0 | 219 | 18 | 3/3/1/1/0 |
| outd3 | Castle Ironfist | 1 | A2 Bt2 G5 M Se St TH2 Tm2 Tr Tv2 W2 | 20 | 5 | LizardArch d1 L4-11; Bloodsucker d3 L2-8; PeasantM3 d1 L3-7 | 6 | 2/3 | 44 + 80/0/0 | 410 | 6 | 1/3/1/1/0 |
| oute1 | Eel Infested Waters | 1 | Bt2 M Tm Tv2 | 8 | 1 | SeaSerpent d3 L28-48; Cockatrice d3 L13-17; ElemWater d2 L14-36 | 6 | 5/6 | 0 + 62/0/0 | 202 | 2 | 0/2/1/1/0 |
| oute2 | Misty Islands | 1 | A Al Bk Bt G5 M TH2 Tm Tr Tv W | 13 | 1 | PeasantM3 d2 L3-7; PeasantF3 d2 L3-7 | 6 | 2/2 | 22 + 32/0/0 | 182 | 5 | 1/3/1/1/0 |
| outc3 | Mire of the Damned | 2 | A Ci7 M St Tm Tv2 W | 26 | 3 | BGhost d2 L9-19; BHarpy d2 L14-19; Skeleton d4 L6-14 | 6 | 3/7 | 15 + 89/0/0 | 402 | 3 | 0/1/1/1/1 |
| outd2 | Bootleg Bay | 2 | A Bt2 Ci7 M Tm2 Tr Tv2 W | 10 | 4 | PeasantM4 d3 L6-10; PeasantF4 d3 L6-10; LizardArch d3 L4-11 | 6 | 3/2 | 16 + 37/0/0 | 188 | 5 | 2/3/1/1/1 |
| outb3 | Dragonsand | 3 | Ci5 | 6 | 2 | DragonLand d5 L50-70; DragonCover d5 L80-100; DragonCave d5 L40-60 | 6 | 8/10 | 0 + 74/0/0 | 206 | 6 | 0/3/1/1/1 |
| outc2 | Free Haven | 3 | A2 Bk Bt2 G9 M3 Se St2 TH3 Tm Tr Tv3 W2 | 65 | 4 | BArcher d2 L9-29; PeasantM2 d5 L2-10 | 6 | 4/6 | 58 + 48/0/0 | 280 | 2 | 2/1/1/1/0 |
| outa3 | Hermit's Isle | 4 | – | 0 | 1 | BTitan d5 L65-95; BHydra d5 L45-65; SeaSerpent d5 L28-48 | 6 | 7/8 | 0 + 93/0/0 | 324 | 2 | 0/1/0/2/0 |
| outb2 | Blackshire | 4 | A Al Bk Ci7 G4 M St Tm2 Tr Tv2 W | 18 | 2 | DragonCave d3 L40-60; Werewolf d2 L20-40; ElemAir d2 L16-33 | 6 | 6/8 | 28 + 43/0/0 | 162 | 8 | 2/3/1/1/0 |
| outc1 | Frozen Highlands | 4 | A2 Al Bk G4 M St TH2 Tm Tr Tv2 W2 | 35 | 2 | BHarpy d3 L14-19; Barbarian d3 L14-37; BArcher d3 L9-29 | 6 | 4/6 | 40 + 59/12/0 | 309 | 2 | 2/6/1/1/0 |
| outa2 | Paradise Valley | 5 | A M Tm Tr Tv W | 16 | 0 | DragonCover d3 L80-100; BHydra d3 L45-65; BTitan d3 L65-95 | 6 | 7/8 | 0 + 51/12/0 | 141 | 3 | 0/1/0/1/0 |
| outb1 | Kriegspire | 5 | A M St Tr Tv W | 21 | 5 | BMinotaur d2 L39-79; ElemEarth d2 L25-40; BDragonFly d2 L24-32 | 6 | 6/8 | 0 + 33/0/0 | 98 | 2 | 2/3/2/1/1 |
| outd1 | Silver Cove | 5 | A Bk Bt2 Ci G5 M2 St TH2 Tm Tr Tv2 W | 46 | 3 | Druidess d2 L10-28; BGargoyle d3 L16-33 | 6 | 4/5 | 35 + 47/0/0 | 200 | 3 | 1/4/1/1/0 |
| outa1 | Sweet Water | 6 | – | 2 | 1 | Demon d3 L20-60; DemonFly d3 L30-70 | 6 | 8/9 | 0 + 20/0/0 | 60 | 1 | 1/2/0/1/1 |

#### MM6 indoor maps (sorted by estimated monsters)
| Map | Name | Faces | Sectors | Floor tiles | Est. mons | Item spawns | Chests | Tres | Lock/Trap | Class |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|---|
| zddb01 | Dragon's Lair | 104 | 2 | 29 | 1 | 0 | 0 | 6 | 1/1 | S |
| 6t4 | Temple of the Sun | 470 | 8 | 27 | 13 | 2 | 9 | 6 | 3/2 | S |
| zdwj02 | Devil Outpost | 60 | 3 | 25 | 16 | 0 | 2 | 6 | 1/1 | S |
| 6t2 | Temple of the Fist | 298 | 13 | 18 | 31 | 3 | 3 | 6 | 2/1 | S |
| 6d03 | Shadow Guild Hideout | 995 | 23 | 57 | 48 | 5 | 3 | 6 | 2/2 | M |
| 6d13 | The Monolith | 985 | 27 | 126 | 48 | 2 | 2 | 6 | 3/5 | M |
| 6t8 | Temple of the Snake | 781 | 23 | 68 | 52 | 1 | 9 | 6 | 5/5 | M |
| 6d07 | Silver Helm Outpost | 1949 | 41 | 99 | 56 | 3 | 6 | 6 | 3/3 | M |
| 6d08 | Shadow Guild | 1299 | 45 | 82 | 60 | 4 | 12 | 6 | 4/3 | M |
| cd3 | Castle Kriegspire | 3094 | 165 | 254 | 73 | 39 | 7 | 6 | 6/6 | M |
| 6d19 | Agar's Laboratory | 772 | 20 | 175 | 76 | 4 | 1 | 6 | 5/9 | M |
| 6d14 | Tomb of Ethric the Mad | 1184 | 50 | 173 | 77 | 3 | 8 | 6 | 4/5 | M |
| 6d16 | Warlord's Fortress | 2665 | 40 | 121 | 87 | 9 | 18 | 6 | 5/6 | M |
| 6d20 | Caves of the Dragon Riders | 1670 | 21 | 257 | 88 | 5 | 13 | 6 | 6/10 | M |
| 6d09 | Snergle's Iron Mines | 2239 | 60 | 155 | 90 | 12 | 12 | 6 | 3/3 | M |
| 6d15 | Icewind Keep | 2320 | 33 | 151 | 97 | 4 | 8 | 6 | 4/5 | M |
| 6d18 | Gharik's Forge | 2561 | 48 | 216 | 97 | 17 | 8 | 6 | 7/8 | M |
| 6t5 | Temple of the Moon | 1226 | 27 | 153 | 102 | 23 | 3 | 6 | 3/2 | L |
| sci-fi | Control Center | 3001 | 93 | 675 | 113 | 0 | 11 | 6 | 5/8 | L |
| hive | The Hive | 4072 | 81 | 414 | 132 | 0 | 5 | 6 | 10/10 | L |
| 6d06 | Dragoons' Caverns | 2669 | 71 | 225 | 136 | 22 | 9 | 6 | 2/3 | L |
| 6d10 | Dragoons' Keep | 1888 | 48 | 132 | 158 | 20 | 4 | 6 | 3/3 | L |
| sewer | Free Haven Sewer | 1737 | 119 | 509 | 163 | 42 | 7 | 6 | 4/2 | L |
| 6d12 | Silver Helm Stronghold | 1431 | 32 | 77 | 168 | 1 | 4 | 6 | 3/4 | L |
| 6t6 | Supreme Temple of Baa | 2898 | 67 | 185 | 182 | 14 | 7 | 6 | 4/4 | L |
| 6t3 | Temple of Tsantsa | 3040 | 67 | 134 | 183 | 3 | 6 | 6 | 2/1 | L |
| 6d05 | Snergle's Caverns | 1270 | 36 | 196 | 186 | 6 | 1 | 6 | 3/3 | L |
| 6d04 | Hall of the Fire Lord | 2231 | 142 | 331 | 187 | 10 | 11 | 6 | 2/2 | L |
| 6d11 | Corlagon's Estate | 1942 | 81 | 265 | 196 | 18 | 11 | 6 | 4/4 | L |
| 6t1 | Temple of Baa | 3214 | 50 | 1773 | 200 | 4 | 6 | 6 | 2/1 | L |
| 6d01 | Goblinwatch | 2290 | 59 | 353 | 206 | 15 | 10 | 6 | 0/1 | L |
| 6d02 | Abandoned Temple | 4110 | 67 | 735 | 220 | 21 | 6 | 6 | 1/1 | L |
| 6t7 | Superior Temple of Baa | 3368 | 78 | 688 | 245 | 14 | 8 | 6 | 4/4 | L |
| 6d17 | Lair of the Wolf | 5381 | 124 | 1157 | 309 | 14 | 11 | 6 | 5/6 | L |
| pyramid | Tomb of VARN | 3479 | 216 | 4183 | 344 | 0 | 6 | 6 | 8/8 | L |
| cd2 | Castle Darkmoor | 4665 | 195 | 2324 | 353 | 5 | 1 | 6 | 5/5 | L |
| cd1 | Castle Alamos | 5315 | 181 | 662 | 474 | 26 | 14 | 6 | 5/5 | L |

#### MM7 outdoor maps
| Map | Name | Hops | Services | Res | Dungeons | Monster families (dif, level A–C) | Tres | Lock/Trap | Placed+spawns (grp/fix/item) | Est. mons | Chests | Well/Fount/Shrine/Obel/Ped |
|---|---|--:|---|--:|---|---|--:|---|---|--:|--:|---|
| 7out01 | Emerald Island | 0 | A Al G4 M Tm Tr Tv W | 14 | 2 | Dragonfly d1 L2-8 | 0 | 0/1 | 28 + 11/0/0 | 66 | 7 | 5/0/0/0/0 |
| 7out02 | Harmondale | 1 | A Al Bk G7 M St TH Tm Tr Tv W | 16 | 2 | Goblin d3 L4-10; Swordsman d3 L10-24 | 0 | 2/1 | 138 + 43/0/6 | 288 | 12 | 3/1/0/1/0 |
| 7out03 | Erathia | 2 | A Al Bk Bt G3 M St TH Tm Tr Tv W | 35 | 5 | Fighter Leather d2 L8-22; Griffin d1 L15-30 | 1 | 4/2 | 37 + 28/20/14 | 113 | 13 | 5/2/1/1/0 |
| 7out04 | The Tularean Forest | 2 | A Al Bk Bt G4 M St TH Tm Tr Tv W | 23 | 3 | Treant d1 L12-25; Elf Spearman d2 L14-30; Fighter Chain d2 L14-35 | 1 | 4/2 | 33 + 46/1/7 | 80 | 9 | 1/1/1/1/0 |
| out11 | The Barrow Downs | 2 | Tv | 6 | 5 | AGog d1 L7-18; Ghost d1 L9-19; Gargoyle d1 L16-33 | 2 | 5/3 | 0 + 65/0/13 | 130 | 9 | 2/0/1/1/0 |
| 7out05 | Deyja | 3 | Al G2 M St Tm Tv | 20 | 3 | Harpy d2 L14-19; Zombie d3 L9-17 | 2 | 6/3 | 22 + 50/0/7 | 122 | 8 | 6/0/1/1/0 |
| 7out06 | The Bracada Desert | 3 | Al Bt G2 M St Tm Tv | 15 | 3 | Golem d2 L22-50; Griffin d2 L15-30 | 2 | 6/3 | 29 + 37/0/12 | 103 | 6 | 3/1/1/1/0 |
| 7out13 | Tatalia | 3 | A2 Bk Bt G St Tm Tr Tv W2 | 22 | 5 | Archer d3 L9-29; ATroll d3 L18-38 | 2 | 8/4 | 37 + 43/0/21 | 123 | 1 | 3/0/2/1/0 |
| out14 | Avlee | 3 | A Bk Bt G2 St Tm Tr Tv W | 13 | 3 | Elf Spearman d3 L14-30; AWyvern d3 L19-37; Elemental Water d3 L14-36 | 2 | 8/4 | 39 + 64/0/13 | 167 | 7 | 4/0/2/1/0 |
| 7out15 | Shoals | 4 | – | 0 | 1 | Sea Monster d5 L28-48 | 1 | 1/1 | 0 + 28/0/28 | 56 | 1 | 0/0/1/1/0 |
| out09 | Evenmorn Island | 4 | Bt G Tv | 3 | 2 | Skeleton Warrior d3 L6-14; Ghost d2 L9-19; Gargoyle d1 L16-33 | 2 | 8/4 | 0 + 48/0/7 | 96 | 6 | 0/0/2/1/0 |
| out10 | Mount Nighon | boat/tun | A G M Tm Tr Tv W | 13 | 2 | Warlock d2 L25-50; Roc d3 L27-51; Hydra d1 L45-65 | 3 | 10/5 | 30 + 71/0/9 | 172 | 9 | 5/1/1/1/0 |
| out12 | The Land of the Giants | boat/tun | – | 1 | 3 | ADragon d3 L80-100; Titan d3 L65-95; Devil d3 L30-70 | 6 | 20/9 | 0 + 66/0/14 | 132 | 0 | 2/0/0/1/0 |

#### MM7 indoor maps (sorted by estimated monsters)
| Map | Name | Faces | Sectors | Floor tiles | Est. mons | Item spawns | Chests | Tres | Lock/Trap | Class |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|---|
| mdt09 | Wromthrax's Cave | 282 | 2 | 880 | 1 | 3 | 0 | 3 | 10/5 | S |
| mdt15 | The Small House | 1568 | 27 | 116 | 2 | 0 | 2 | 6 | 20/10 | S |
| mdk01–05, mdr01–05, mdt01–05 | 15 Dwarven Barrows (I–XV), each | 691–1591 | 5–11 | 16–56 | 4–60 | 4–36 | 0–3 | 1 | – | 12 S, 3 M |
| 7d28 | The Dragon's Lair | 503 | 3 | 81 | 7 | 14 | 0 | 1 | 5/3 | S |
| mdt11 | The Hidden Tomb | 764 | 8 | 35 | 8 | 20 | 6 | 4 | 12/6 | S |
| 7d18 | Lord Markham's Manor | 1001 | 6 | 12 | 10 | 0 | 5 | 2 | 10/5 | S |
| mdt10 | William Setag's Tower | 170 | 5 | 21 | 10 | 4 | 1 | 2 | 8/4 | S |
| mdt14 | The Bandit Caves | 666 | 9 | 26 | 12 | 5 | 3 | 1 | 6/3 | S |
| 7d13 | Zokarr's Tomb | 1018 | 13 | 27 | 18 | 10 | 0 | 2 | 5/3 | S |
| mdt12 | The Dragon Caves | 932 | 11 | 366 | 21 | 12 | 3 | 6 | 20/10 | S |
| 7d31 | Fort Riverstride | 4201 | 34 | 82 | 22 | 0 | 20 | 1 | 4/3 | S |
| 7d16 | The Wine Cellar | 1168 | 11 | 27 | 23 | 4 | 4 | 3 | 13/7 | S |
| 7d19 | Grand Temple of the Moon | 1993 | 19 | 45 | 27 | 24 | 7 | 3 | 9/4 | S |
| t04 | The Hall of the Pit | 847 | 10 | 166 | 28 | 11 | 3 | 2 | 9/4 | S |
| 7d20 | The Mercenary Guild | 2583 | 27 | 60 | 29 | 14 | 20 | 4 | 11/5 | S |
| 7d12 | Clanker's Laboratory | 2786 | 26 | 55 | 33 | 0 | 14 | 4 | 14/7 | S |
| t03 | Grand Temple of the Sun | 1529 | 16 | 73 | 33 | 31 | 4 | 3 | 9/4 | S |
| 7d21 | White Cliff Cave | 3073 | 26 | 276 | 34 | 28 | 9 | 0 | 2/1 | S |
| 7d27 | Colony Zod | 4433 | 28 | 279 | 35 | 29 | 6 | 5 | 20/10 | S |
| 7d22 | The Hall under the Hill | 2659 | 24 | 326 | 37 | 28 | 2 | 1 | 6/3 | S |
| 7d09 | The Titans' Stronghold | 2048 | 35 | 1131 | 41 | 44 | 12 | 5 | 16/8 | M |
| 7d14 | The School of Sorcery | 2045 | 18 | 64 | 41 | 17 | 2 | 2 | 10/5 | M |
| 7d17 | The Tidewater Caverns | 1516 | 13 | 297 | 48 | 34 | 4 | 2 | 9/4 | M |
| 7d33 | Castle Gryphonheart | 3531 | 44 | 182 | 48 | 39 | 7 | 2 | 6/3 | M |
| t01 | Temple of the Light | 3924 | 66 | 558 | 48 | 45 | 4 | 5 | 15/8 | M |
| 7d25 | Celeste | 3973 | 31 | 512 | 52 | 0 | 0 | 3 | 20/7 | M |
| 7d37 | The Haunted Mansion | 1948 | 15 | 57 | 52 | 0 | 11 | 2 | 12/6 | M |
| 7d30 | Castle Lambent | 2951 | 29 | 412 | 54 | 20 | 9 | 4 | 12/6 | M |
| d01 | The Erathian Sewers | 4280 | 55 | 285 | 54 | 24 | 4 | 1 | 5/2 | M |
| t02 | Temple of the Dark | 3590 | 47 | 162 | 54 | 30 | 20 | 5 | 15/8 | M |
| 7d34 | The Red Dwarf Mines | 3833 | 54 | 390 | 55 | 29 | 5 | 1 | 5/2 | M |
| 7d08 | The Tularean Caves | 4975 | 40 | 632 | 56 | 34 | 7 | 1 | 4/3 | M |
| d04 | The Temple of Baa | 2617 | 32 | 126 | 57 | 30 | 5 | 3 | 11/5 | M |
| d03 | Castle Gloaming | 3540 | 49 | 675 | 59 | 16 | 9 | 4 | 12/6 | M |
| 7d10 | The Breeding Zone | 2374 | 33 | 147 | 60 | 0 | 2 | 1 | 10/5 | M |
| 7d06 | The Temple of the Moon | 2744 | 31 | 147 | 62 | 7 | 7 | 0 | 0/1 | M |
| 7d11 | The Walls of Mist | 4316 | 57 | 1821 | 65 | 14 | 4 | 1 | 10/5 | M |
| 7d15 | Watchtower 6 | 1934 | 20 | 445 | 71 | 28 | 4 | 3 | 11/6 | M |
| 7d23 | The Lincoln | 3985 | 43 | 335 | 80 | 20 | 4 | 6 | 20/10 | M |
| 7d32 | Castle Navan | 4421 | 36 | 424 | 88 | 19 | 20 | 2 | 6/3 | M |
| 7d24 | Stone City | 4090 | 41 | 186 | 95 | 16 | 13 | 1 | 6/3 | M |
| 7d26 | The Pit | 5466 | 40 | 1454 | 96 | 0 | 4 | 3 | 20/7 | M |
| 7d07 | Thunderfist Mountain | 6094 | 57 | 531 | 98 | 44 | 20 | 4 | 10/5 | M |
| d02 | The Maze | 3423 | 72 | 553 | 107 | 73 | 7 | 5 | 12/6 | L |
| 7d29 | Castle Harmondale | 4847 | 72 | 354 | 164 | 38 | 10 | 0 | 1/1 | L |
| 7d36 | Tunnels to Eeofol | 5884 | 77 | 998 | 174 | 81 | 0 | 5 | 10/5 | L |
| 7d35 | Nighon Tunnels | 6797 | 71 | 926 | 184 | 50 | 0 | 2 | 8/4 | L |

#### MM8 outdoor maps
| Map | Name | Hops | Services | Res | Dungeons | Monster families (dif, level A–C) | Tres | Lock/Trap | Placed+spawns (grp/fix/item) | Est. mons | Chests | Well/Fount/Shrine/Obel/Ped |
|---|---|--:|---|--:|---|---|--:|---|---|--:|--:|---|
| out01 | Dagger Wound Island | 0 | A Al Bk Bt G M TH Inn Tm Tr Tv W | 20 | 4 | Lizardmen Warrio d1 L4-8; Wimpy Pirate War d1 L8-15; Couatl d1 L1-4 | 0 | 0/0 | 61 + 46/0/4 | 168 | 20 | 3/1/0/1/0 |
| out02 | Ravenshore | 1 | A Al Bk Bt2 G2 M2 St Inn Tm Tr Tv2 W | 45 | 6 | Human Mercenary d3 L10-24; Centaur d1 L11-18; Dire Wolf d1 L9-19 | 1 | 1/1 | 143 + 59/0/0 | 261 | 13 | 3/1/0/1/0 |
| out03 | Alvar | 2 | A Al Bk G2 M St Tm Tr Tv2 W | 45 | 3 | Dark Elf Warrior d2 L15-39; Ogre Warrior d1 L15-28; Wasp Warrior d1 L15-23 | 1 | 2/1 | 26 + 61/0/4 | 148 | 10 | 3/1/0/1/0 |
| out05 | Garrote Gorge | 2 | A M St Tm Tr Tv W | 17 | 4 | Naga d3 L20-38; Wimpy Dragon d2 L15-60; Dragon Hunter d3 L15-45 | 2 | 3/2 | 3 + 53/20/2 | 165 | 6 | 3/0/0/1/0 |
| out06 | Shadowspire | 2 | A Al Bk Bt G M St Tm Tr Tv W | 33 | 4 | Vampire (monster d2 L20-40; Skeletons Archer d2 L11-17; Bone Dragon d1 L30-60 | 2 | 4/2 | 27 + 56/0/7 | 139 | 6 | 3/1/0/1/0 |
| out13 | Regna | 2 | A Al Bt G M Tm Tv W | 16 | 5 | Pirate Warrior M d3 L18-50; Pirate Crossbowm d1 L18-50; Pirate Mage Male d3 L25-75 | 4 | 10/5 | 16 + 64/0/0 | 144 | 8 | 3/1/0/1/0 |
| out04 | Ironsand Desert | 3 | G St Tv | 12 | 4 | Gog d1 L10-19; Troll d2 L18-38; Cyclops d2 L24-48 | 2 | 3/2 | 33 + 74/0/0 | 181 | 11 | 3/0/0/1/0 |
| out07 | Murmurwoods | 3 | G Tv | 10 | 3 | Will ' O Wisp d3 L15-38; Thunder Lizard d3 L20-38; Unicorn d3 L25-45 | 3 | 4/2 | 19 + 81/0/0 | 181 | 5 | 3/0/0/1/0 |
| out08 | Ravage Roaming | 3 | Bt Tv | 6 | 4 | Wyvern d3 L19-37; Gorgon d3 L25-45; Ogre Warrior d3 L15-28 | 3 | 4/2 | 6 + 71/0/10 | 148 | 15 | 3/0/0/1/0 |
| elema | Plane of Air | boat/tun | – | 8 | 1 | Air Elemental d3 L50-80; Thunderbird d3 L39-79; Raven Man d3 L40-60 | 4 | 10/5 | 0 + 68/0/0 | 136 | 1 | 0/0/0/0/0 |
| elemf | Plane of Fire | boat/tun | – | 6 | 2 | Fire Elemental d3 L50-80; Efreeti d3 L45-65; Salamander d3 L29-69 | 4 | 10/5 | 0 + 70/0/0 | 140 | 0 | 0/0/0/0/0 |
| elemw | Plane of Water | boat/tun | – | 6 | 0 | Water Elemental d3 L50-80; Triton d3 L20-45; Dragon Turtle d3 L50-90 | 4 | 10/5 | 22 + 97/0/0 | 216 | 0 | 0/0/0/0/0 |
| out15 | Tutorial | boat/tun | – | 0 | 0 | – | 0 | 0/0 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| pbp | Plane Between Planes | boat/tun | – | 0 | 7 | Ether Knight d3 L40-71; Plane Guardian d3 L50-90; Nightmare d3 L50-90 | 5 | 20/10 | 0 + 112/0/0 | 224 | 0 | 0/0/0/0/0 |

#### MM8 indoor maps (sorted by estimated monsters)
| Map | Name | Faces | Sectors | Floor tiles | Est. mons | Item spawns | Chests | Tres | Lock/Trap | Class |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|---|
| d09 | Merchant House of Alvar | 1338 | 8 | 27 | 0 | 0 | 0 | 3 | 0/0 | S |
| d34 | Small Sub Pen | 1011 | 6 | 26 | 10 | 0 | 0 | 4 | 8/4 | S |
| d48 | Ilsingore's Cave | 520 | 4 | 440 | 11 | 0 | 1 | 4 | 18/8 | S |
| d49 | Yaardrake's Cave | 366 | 3 | 314 | 11 | 0 | 1 | 5 | 18/9 | S |
| d15 | Chain of Fire | 1844 | 10 | 66 | 14 | 0 | 1 | 3 | 10/6 | S |
| d28 | Tomb of Lord Brinne | 390 | 5 | 18 | 14 | 0 | 0 | 2 | 0/0 | S |
| d47 | Old Loeb's Cave | 1209 | 9 | 165 | 15 | 7 | 0 | 4 | 16/8 | S |
| d46 | Church of Eep | 343 | 3 | 24 | 16 | 0 | 1 | 2 | 6/4 | S |
| d40 | Uplifted Library | 1096 | 9 | 46 | 18 | 0 | 1 | 4 | 6/3 | S |
| d26 | The Crypt of Korbu | 1109 | 9 | 91 | 20 | 10 | 0 | 4 | 12/7 | S |
| d37 | Prison of the Lord of Fire | 238 | 5 | 34 | 22 | 10 | 0 | 6 | 20/10 | S |
| d21 | Vampire Crypt | 1239 | 6 | 80 | 24 | 0 | 4 | 3 | 9/4 | S |
| d30 | War Camp | 298 | 15 | 24 | 26 | 12 | 0 | 5 | 12/7 | S |
| d36 | Prison of the Lord of Air | 1727 | 10 | 160 | 26 | 0 | 2 | 6 | 20/10 | S |
| d38 | Prison of the Lord of Water | 2057 | 12 | 88 | 26 | 0 | 5 | 6 | 20/10 | S |
| d08 | Dire Wolf Den | 2488 | 15 | 68 | 27 | 0 | 1 | 2 | 4/2 | S |
| d43 | Ancient Troll Home | 1768 | 13 | 68 | 28 | 0 | 4 | 3 | 7/5 | S |
| d45 | Chapel of Eep | 1837 | 12 | 51 | 28 | 0 | 12 | 2 | 4/3 | S |
| d18 | Naga Vault | 1486 | 15 | 48 | 28 | 7 | 2 | 3 | 12/7 | S |
| d14 | Cyclops Larder | 1881 | 17 | 75 | 32 | 0 | 4 | 4 | 14/7 | S |
| d16 | Dragon Hunter's Camp | 1864 | 17 | 107 | 32 | 0 | 9 | 3 | 8/5 | S |
| d39 | Prison of the Lord of Earth | 403 | 5 | 142 | 32 | 0 | 0 | 6 | 20/10 | S |
| d06 | Pirate Outpost | 2339 | 13 | 75 | 35 | 0 | 7 | 1 | 4/2 | S |
| d31 | Pirate Stronghold | 2090 | 16 | 75 | 36 | 0 | 9 | 4 | 9/4 | S |
| d22 | Temple of the Sun | 758 | 6 | 46 | 38 | 9 | 0 | 3 | 7/4 | S |
| d35 | Escaton's Palace | 3262 | 34 | 243 | 40 | 25 | 5 | 6 | 20/10 | M |
| d10 | Escaton's Crystal | 2581 | 16 | 112 | 42 | 0 | 1 | 5 | 20/10 | M |
| d41 | Dark Dwarf Compound | 2821 | 33 | 109 | 42 | 0 | 20 | 4 | 8/4 | M |
| d17 | Dragon Cave | 1486 | 10 | 597 | 44 | 19 | 0 | 5 | 15/8 | M |
| d27 | Castle of Air | 2314 | 18 | 109 | 44 | 0 | 13 | 5 | 15/9 | M |
| d13 | Troll Tomb | 5655 | 38 | 85 | 44 | 16 | 0 | 3 | 4/3 | M |
| d44 | Grand Temple of Eep | 3140 | 27 | 98 | 48 | 0 | 11 | 3 | 8/5 | M |
| d20 | Mad Necromancer's Lab | 1614 | 28 | 123 | 52 | 0 | 5 | 4 | 11/6 | M |
| d25 | Barbarian Fortress | 2241 | 18 | 94 | 53 | 0 | 10 | 5 | 10/5 | M |
| d32 | Abandoned Pirate Keep | 2363 | 22 | 80 | 54 | 4 | 16 | 4 | 11/5 | M |
| d23 | Druid Circle | 2747 | 20 | 182 | 56 | 0 | 6 | 4 | 10/5 | M |
| d29 | Castle of Fire | 1783 | 15 | 97 | 56 | 5 | 5 | 5 | 15/9 | M |
| d12 | Ogre Fortress | 2832 | 24 | 183 | 70 | 0 | 2 | 2 | 5/3 | M |
| d07 | Smuggler's Cove | 3044 | 17 | 346 | 72 | 0 | 15 | 2 | 3/2 | M |
| d24 | Balthazar Lair | 1656 | 31 | 71 | 74 | 22 | 0 | 4 | 10/6 | M |
| d33 | Passage Under Regna | 2130 | 15 | 317 | 80 | 0 | 0 | 4 | 9/5 | M |
| d19 | Necromancers' Guild | 4128 | 28 | 250 | 82 | 0 | 12 | 4 | 8/4 | M |
| eleme | Plane of Earth | 4174 | 34 | 295 | 96 | 0 | 11 | 4 | 10/5 | M |
| d05 | Abandoned Temple | 3917 | 33 | 268 | 116 | 0 | 8 | 1 | 1/1 | L |
| d11 | Wasp Nest | 1999 | 13 | 109 | 142 | 0 | 0 | 2 | 6/3 | L |

#### MM9 outdoor maps
| Map | Name | Hops | Services | Res | Dungeons | Monster families (dif, level A–C) | Tres | Lock/Trap | Placed+spawns (grp/fix/item) | Est. mons | Chests | Well/Fount/Shrine/Obel/Ped |
|---|---|--:|---|--:|---|---|--:|---|---|--:|--:|---|
| bootcamp | Ravensford | 0 | – | – | 0 | – | 0 | 0/0 | 5 + 0/0/0 | 5 | 5 | 0/0/2/0/0 |
| isleofashes | Isle of Ashes | 1 | – | – | 1 | Skeleton d0 L3-16; Dragonfly d0 L2-5 | 1 | 0/0 | 74 + 0/0/8 | 74 | 3 | 0/0/1/0/0 |
| drangheim | Drangheim | 2 | – | – | 2 | Thrall L8-18; Dragonfly L2-5; Highwayman L8-22 | 2 | 3/2 | 32 + 0/0/8 | 32 | 3 | 0/0/0/0/0 |
| frosgardcity | Frosgard City | 2 | A Al Bk Gen Lib2 M2 Tm Tr Tv W | – | 1 | – | 2 | 8/6 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| guberland | Guberland | 2 | – | – | 3 | Dragonfly L2-5; Highwayman L8-22 | 2 | 4/2 | 40 + 0/0/6 | 40 | 0 | 0/0/1/0/0 |
| lindisfarne | Lindisfarne | 2 | Al Gen M | – | 3 | Magreeb L16-33; Evil Sorcerer L25-50; Thrall L8-18 | 2 | 8/4 | 57 + 0/0/6 | 57 | 1 | 1/0/1/0/0 |
| sturmford | Sturmford | 2 | – | – | 1 | Thrall L8-18; Dragonfly L2-5 | 1 | 3/1 | 102 + 0/0/8 | 102 | 4 | 0/0/1/0/0 |
| thjorgard | Thjorgard | 2 | – | – | 2 | Icky L7-18; Highwayman L8-22; Gezzampt L15-28 | 2 | 3/4 | 50 + 0/0/8 | 50 | 2 | 0/0/1/0/0 |
| thronheim | Thronheim | 2 | – | – | 2 | Basilisk L15-30; Gezzampt L15-28; Nosferatu L20-48 | 2 | 9/5 | 60 + 0/0/8 | 60 | 3 | 0/0/1/0/0 |
| arslegardcity | Arslegard City | 3 | A Bk Gen Lib M4 Tm Tr Tv W | – | 4 | – | 4 | 9/16 | 1 + 0/0/0 | 1 | 0 | 0/0/0/0/0 |
| drangheimcity | Drangheim City | 3 | A Bk M Tm Tr Tv W | – | 1 | – | 0 | 2/1 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| frosgard | Frosgard | 3 | – | – | 3 | Wolf L20-40; Bigfoot L18-38; Gezzampt L15-28 | 3 | 8/6 | 49 + 0/0/8 | 49 | 2 | 0/0/1/0/0 |
| guberlandcity | Guberland City | 3 | A Al Bk Lib M4 Tm Tr Tv W | – | 0 | – | 1 | 2/3 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| mountainpass | Mountain Pass | 3 | – | – | 0 | Wolf L20-40; Imp L4-10; Winged Mutant L27-51 | 3 | 5/10 | 106 + 0/0/10 | 106 | 1 | 0/0/0/0/0 |
| sturmfordcity | Sturmford City | 3 | A Bk Gen M Tm Tr Tv W | – | 1 | – | 0 | 2/1 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| thjorgardcity | Thjorgard City | 3 | A Al Bk Gen Lib M Tm Tr Tv W | – | 1 | – | 1 | 2/3 | 0 + 0/0/0 | 0 | 0 | 0/0/0/0/0 |
| thronheimcity | Thronheim City | 3 | A2 Al Bk Lib M Tm2 Tr2 Tv W2 | – | 0 | – | 2 | 5/3 | 1 + 0/0/0 | 1 | 1 | 0/0/0/0/0 |
| yorwick | Yorwick | 4 | Gen M | – | 3 | Ghost L33-55; Nosferatu L20-48; Evil Sorcerer L25-50 | 3 | 8/12 | 110 + 0/0/8 | 110 | 2 | 0/0/1/0/0 |
| afterworld | The Afterworld | 5 | – | – | 1 | Horde L34-54; Banshee L35-65; Mummy L20-40 | 4 | 12/16 | 1 + 0/0/0 | 1 | 0 | 0/0/0/0/0 |

#### MM9 indoor maps (sorted by estimated monsters)
| Map | Name | Faces | Sectors | Floor tiles | Est. mons | Item spawns | Chests | Tres | Lock/Trap | Class |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|---|
| dragonstadium | Dragon's Lair | 1917 | 4 | 469 | 1 | 0 | 2 | 6 | 20/20 | S |
| dungeonofsecrets | Dungeon of Secrets | 5463 | 11 | 141 | 0 | 3 | 0 | 2 | 17/10 | S |
| hallofthegods | Hall of the Gods | 2377 | 2 | 1773 | 0 | 0 | 0 | 4 | 18/18 | S |
| klusoshouse | Kluso's House | 1850 | 11 | 92 | 20 | 5 | 1 | 2 | 17/10 | S |
| ruinedtemple | Ruined Temple | 4059 | 10 | 227 | 20 | 8 | 3 | 3 | 17/8 | S |
| templeofhonk | Temple of Honk | 6107 | 23 | 246 | 0 | 5 | 4 | 5 | 8/20 | S |
| tasaracademy | Ta'Sar Academy | 7650 | 30 | 312 | 20 | 8 | 4 | 2 | 10/7 | S |
| lindisfarnemonastery | Lindisfarne Monastery | 14996 | 8 | 1588 | 0 | 0 | 0 | 2 | 7/7 | S |
| traininghall | Training Hall | 7364 | 14 | 274 | 31 | 10 | 4 | 4 | 12/16 | S |
| bathhouse | The Bathhouse | 2644 | 21 | 613 | 35 | 12 | 3 | 5 | 15/18 | S |
| verhoffinruins | Verhoffin Ruins | 6282 | 31 | 513 | 42 | 14 | 5 | 4 | 0/16 | M |
| inventastorca | Inventa Storca | 9845 | 27 | 414 | 22 | 10 | 0 | 3 | 7/9 | S |
| dookscastle | Dook's Castle | 7538 | 12 | 486 | 56 | 12 | 7 | 2 | 8/7 | M |
| yanmirsfort | Yanmir's Fort | 12236 | 28 | 1193 | 65 | 20 | 10 | 3 | 10/12 | M |
| drangheimprison | Drangheim Prison | 14782 | 92 | 461 | 50 | 14 | 5 | 2 | 12/2 | M |
| connectingtunnels | Connecting Tunnel | 5019 | 32 | 577 | 87 | 8 | 2 | 4 | 3/12 | M |
| anskramkeep | Anskram Keep | 10386 | 48 | 466 | 86 | 18 | 7 | 1 | 12/2 | M |
| darkpassageway | Dark Passageway | 5869 | 28 | 1672 | 94 | 24 | 7 | 5 | 20/18 | M |
| thjoradmine | Thjorad Mine | 13143 | 60 | 833 | 108 | 18 | 2 | 2 | 8/6 | L |
| wizardslab | Wizard's Lab | 12170 | 16 | 969 | 131 | 22 | 3 | 4 | 8/16 | L |
| beethoven | Beet Hoven | 9155 | 40 | 2266 | 156 | 24 | 6 | 1 | 2/1 | L |
| lichlab | Lich Lab | 14764 | 66 | 1443 | 172 | 24 | 7 | 4 | 17/16 | L |
| 1000terrors | Thousand Terrors | 18751 | 20 | 3166 | 205 | 28 | 13 | 6 | 20/20 | L |
| chasmofthedead | Chasm of the Dead | 13609 | 63 | 1215 | 239 | 28 | 16 | 3 | 15/8 | L |
## 2. Dungeon sizes

Classes used in the tables:
- **S**: fewer than 40 estimated monsters.
- **M**: 40–100.
- **L**: more than 100.

Faces are MM6–MM8 polygons and MM9 triangles, so MM9 face counts run about 3–4× higher for the same room.

| | S | M | L | Typical S | Typical M | Typical L |
|---|---|---|---|---|---|---|
| MM6 | 4 | 13 | 20 | temple shrine (Fist, Sun): 300–500 faces, 8–13 sectors, 1–3 chests | Shadow Guild, Monolith: 1000–2000 faces, 25–45 sectors, 5–12 chests | Alamos, Darkmoor, VARN, Lair of the Wolf: 3500–5400 faces, 120–216 sectors, 100–470 monsters |
| MM7 | 31 | 26 | 4 | the 15 Barrows, small manors and towers: 700–1600 faces, 5–11 sectors, 0–3 chests | castles and temples: 2000–4500 faces, 20–50 sectors, 4–20 chests | Castle Harmondale, Nighon and Eeofol tunnels, the Maze: 3400–6800 faces, 70–77 sectors |
| MM8 | 25 | 18 | 2 | caves, crypts, the four Lord prisons: 240–2000 faces, 3–17 sectors | strongholds and temples: 1600–4200 faces, 15–35 sectors | Wasp Nest, Abandoned Temple: 2000–3900 faces, 13–33 sectors |
| MM9 | 10 | 8 | 6 | Kluso, Ruined Temple, Honk, Ta'Sar | forts and castles: 6–15k triangles | Chasm, 1000 Terrors, Lich Lab, Beet Hoven, Wizard's Lab, Thjorad Mine: 9–19k triangles |

**What the calibration says:**
- MM7/MM8 dungeons are short. Their median is 35–40 monsters, 2–4 chests, about 20 sectors and 2,000 faces: a
  20–40 minute visit. Each world has 2–4 large set pieces.
- MM6 is the outlier. It has the most map content of the three, and its dungeons are long; no new world should copy
  that ratio.
- **Chests per dungeon:** MM7 median 4 (max 20), MM8 median 2 (max 20).
- **Item spawn points per dungeon** (loot lying on the floor):
  - MM7: up to 81 (the Tunnels to Eeofol); about 25 is typical.
  - MM8: mostly 0. MM8 moved floor loot into monster drops and chests.

**Quest-critical dungeons.** These come from the qbits set and the quest items given in each map's decompiled
script. The full lists are in §5.
- **MM6:** 9 of 37. Each holds a memory crystal, a proof, the control cube or the finale.
- **MM7:** about 16 of 61 on one story path. The Light and Dark branches use different dungeons.
- **MM8:** about 20 of 45 plus the 4 planes. The alliance choice means a party skips some of them.
- **MM9:** 16 of 24.

Promotions use another 7–20 dungeons per world. In all three games **roughly a third to a half of the dungeons are
optional.** Those are side-quest, loot or teacher dungeons, typically S or M.

### Dungeon placement per outdoor map

These are the `.blv` files each outdoor map's events move the party to:

| World | Pattern |
|---|---|
| MM6 | 0–5 dungeons per map. Kriegspire 5 (Agar, Dragon Riders, Superior Temple, Kriegspire, Devil Outpost); Bootleg Bay 4 temples; New Sorpigal 3 (Goblinwatch, Abandoned Temple, Gharik's Forge). Towns like Free Haven reach their sewers through a house dialog. |
| MM7 | 1–5 per map. Erathia 5 and Tatalia 5 (manor, cellar, caverns, Mercenary Guild, dragon cave); Barrow Downs 5 (Stone City, mansion, barrows). Harmondale's castle is entered through a house dialog. |
| MM8 | 3–5 per region, almost always a quest dungeon, a lair or cave, and one optional dragon cave (d47–d49). Regna 5; the Plane Between Planes 7 (finale). |
| MM9 | 0–4 per region; most cities have one. |

## 3. Progression

### Monster level and treasure against distance from the start

Mean A-tier level and maximum C-tier level of each map's encounter families, by hops from the start map (MM6 has no
Tres values, see the introduction):

| World | Hops | Map | A level | Max C | Tres | Lock/Trap |
|---|---|---|--:|--:|--:|---|
| MM8 | 0 | Dagger Wound | 4 | 15 | 0 | 0/0 |
| MM8 | 1 | Ravenshore | 10 | 24 | 1 | 1/1 |
| MM8 | 2 | Alvar / Garrote / Shadowspire / Regna | 15–25 | 39–75 | 1–4 | 2–10/1–5 |
| MM8 | 3 | Ironsand / Murmurwoods / Ravage Roaming | 17–20 | 45–48 | 2–3 | 3–4/2 |
| MM8 | gate | elemental planes; Plane Between Planes | 50+ | 80–90 | 4; 5 | 10/5; 20/10 |
| MM7 | 0 | Emerald Island | 2 | 8 | 0 | 0/1 |
| MM7 | 1 | Harmondale | 7 | 24 | 0 | 2/1 |
| MM7 | 2 | Erathia / Tularean / Barrow Downs | 11–13 | 30–35 | 1–2 | 4–5/2–3 |
| MM7 | 3 | Deyja / Bracada / Tatalia / Avlee | 12–18 | 19–50 | 2 | 6–8/3–4 |
| MM7 | 4 | Shoals, Evenmorn | 9–28 | 48 | 1–2 | 8/4 |
| MM7 | gate | Mount Nighon; Land of the Giants | 25; 65 | 65; 100 | 3; 6 | 10/5; 20/9 |
| MM6 | 0 | New Sorpigal | 3 | 10 | – | 0/1 |
| MM6 | 1 | Castle Ironfist / Misty Isles; Eel-Infested Waters (boat) | 3; 18 | 7–11; 48 | – | 2/2–3; 5/6 |
| MM6 | 2 | Mire / Bootleg Bay | 5–10 | 11–19 | – | 3/2–7 |
| MM6 | 3 | Free Haven; Dragonsand | 6; 57 | 29; 100 | – | 4/6; 8/10 |
| MM6 | 4 | Frozen Highlands, Blackshire, Hermit's Isle | 12–46 | 37–95 | – | 4–7/6–8 |
| MM6 | 5–6 | Silver Cove, Kriegspire, Paradise Valley, Sweet Water | 13–63 | 33–100 | – | 4–8/5–9 |

**MM9 rework** (start Ravensford): the Isle of Ashes and Sturmford are levels 2–18. The clan regions are 8–40 (Mountain
Pass 51). Yorwick is 20–55 and the Afterworld 20–65. Treasure tiers go 1 → 4, from monster level (§6).

**The rule all four follow:**
- Level and treasure rise with the number of map edges from the start. Roughly: +5–8 A-tier levels and +1 treasure
  level per hop for the first 2–3 hops, then a plateau of level 15–25 regions the party can take in any order.
- The endgame zones are cut off by a gate (a tunnel, the planes, a portal or a story key). They are not simply
  further away.
- **"Trap" maps break the gradient.** These are deliberately over-levelled maps next to low ones:
  - MM6 Dragonsand (dragons, level 40–100, three hops from the start) and Eel-Infested Waters (one boat hop).
  - MM8 Garrote Gorge (dragons up to 60) beside Ravenshore.
  - MM7 Land of the Giants.
- The trap maps are visible, scary and avoidable, and they hold the best loot or a grandmaster teacher.
- **Lock and Trap difficulty** follows the same curve: 0–1 at the start, about 4 mid-world, 8–10 late, 20 at the
  finale.

### Starting areas

All three openings are a self-contained safe pocket. It has a complete service set, 2–3 entry dungeons, d1 monster
families of level 1–15, 3–5 drinkable wells with small permanent or temporary bonuses, and a forced one-way exit (a
boat or a long road).

| | Pocket | Services | Res. | Monsters | Dungeons | Extras |
|---|---|---|--:|---|---|---|
| MM6 New Sorpigal | the town and its surroundings | 12 types: W A M Al Tm Tv Bk Tr St Bt TH + 4 guilds | 22 | goblins and peasants d1, about 220 est. incl. peasants | Goblinwatch (S/M, 206 est.), Abandoned Temple (L), Gharik's Forge (late) | 3 wells, 3 fountains, shrine, obelisk; 18 chests |
| MM7 Emerald Island | an island; Harmondale follows | W A M Al Tm Tv Tr + 4 guilds (no bank or stables) | 14 | Dragonfly d1 only, 28 placed + 11 spawns (66 est.) | Temple of the Moon (M, 62), Dragon's Lair (S, 7) | 5 wells; the scavenger hunt; boat out only |
| MM8 Dagger Wound | an island chain; Ravenshore follows | 12 + the Adventurer's Inn (roster) | 20 | Lizardmen, wimpy pirates, Couatl d1, about 170 est. | Abandoned Temple (L, 116), Pirate Outpost (S), Uplifted Library, Plane of Earth gate | 3 wells, fountain, obelisk; 20 chests |

**Second map:** the main hub (Harmondale, Ravenshore, Castle Ironfist). It sits at d1–d3, holds 140 placed actors with
townsfolk in MM7/MM8, and the story's first branching quests.

### Non-town wilderness maps

These maps have 0–3 services, often only a tavern or a boat.

| Map | Services | Res. | Monsters | Dungeons | Character |
|---|---|--:|---|---|---|
| MM6 Dragonsand | 0 | 6 | 3 dragon families d5 | VARN pyramid, NWC | Treasure on a deadly map |
| MM6 Sweet Water | 0 | 2 | demons | the Hive | Endgame |
| MM6 Hermit's Isle | 0 | 0 | titans, hydras d5 | Supreme Temple of Baa | Island reached by boat |
| MM6 Paradise Valley | 6 | 16 | dragons, titans | 0 | Hidden grandmaster teachers |
| MM7 Barrow Downs | tavern | 6 | 3 families d1 | 5, 15 barrows | Stone City |
| MM7 Shoals | 0 | 0 | sea monsters d5 | the Lincoln | Water, reached by boat |
| MM7 Land of the Giants | 0 | 1 | dragons, titans, devils d3 | 3 | Endgame |
| MM7 Evenmorn | boat, guild, tavern | 3 | undead | Temples of Sun and Moon | Island |
| MM8 Murmurwoods | guild, tavern | 10 | wisps, thunder lizards, unicorns d3 | 3 | Forest |
| MM8 Ravage Roaming | boat, tavern | 6 | wyverns, gorgons, ogres | 4 | Wilds |
| MM8 Ironsand | guild, stable, tavern | 12 | gogs, trolls, cyclops | 4 | Desert |
| MM8 elemental planes | 0 | – | – | 0–2 each | Whole maps that are a dungeon |

**What makes them interesting (counted in the data):**
- **Encounter density** stays at the town maps' level or above: 130–220 estimated monsters. MM6 islands reach 320.
- **More dungeon entrances per map than towns have**, 3–5. MM7's Barrow Downs places 15 barrows as small optional
  dungeons.
- **Drinkable or usable features.** Every map has an obelisk (one clue each to a hidden treasure). Each map has 2–6
  wells or fountains. MM6 adds a stat shrine per map, one active per month, and pedestals for the statuettes.
- **More floor treasure** (item spawn points): MM7 13–28 per wilderness map against 0–7 in towns.
- **One faction or monster theme per map**, drawn from 2–3 families at the same d-level.
- **A guarded unique:** a dragon or titan lair, a grandmaster teacher, or an artifact chest.
- **No safety:** wilderness maps have few or no residences and no temple, and a boat or tavern is the only service.

## 4. Transport

**Map-edge travel** (`outdoor_travels.txt`, walking off the map edge with food):
- MM6: a 5 × 3 grid with 5 days per edge. Its islands (Misty Isles, Eel-Infested Waters) have no edges.
- MM7: 5 days, some 7.
- MM8: 5, 10 or 15 days. Garrote Gorge to Ravage Roaming is 10–15 days.
- Across all 90 edge entries: 68 are 5 days, 6 are 7, 11 are 10, 1 is 15. Five entries are 0–1 days (the MM7 Shoals
  ↔ Avlee hop).

**Stables and boats.** Each house has up to 3 route slots in `transport_locations.txt`:

| | Route slots | Days min / median / max | Departures per week per slot | Destinations |
|---|--:|---|--:|--:|
| MM8 | 25 | 2 / 3 / 8 | 1.6 | 9 (8 outdoor + arena) |
| MM7 | 35 | 1 / 3 / 7 | 2.3 | 9 |
| MM6 | 36 | 1 / 3 / 30 | 2.1 | 14 (incl. the arena and 3 long hauls of 14–30 days) |
| Between continents (MMerge) | 6 | 6–30 | 1 | Ravenshore, Erathia/Emerald Island, New Sorpigal |
| MM9 docks (`transport_routes.txt`) | 47 (42 docks + 5 special passages; 8 named ships) | 1 / 3 / 6 | one destination per weekday per ship | 8 |

Notes on the route network:
- Each route has 1–3 departure days per week. Towns have 1 stable and 1 dock (MM6 Free Haven and Bootleg Bay: 2
  docks). Coaches link land neighbours in 2–3 days, boats link islands. One dock usually reaches 3 destinations on
  alternating days.
- MM6 has two stables in Free Haven and 9 stables in all. Its houses' schedule notes read like
  "Free Haven C2,S,Tu,4": the map, the weekdays and the days of travel.
- The arena is reachable only by coach, once a week (Sunday) in all three games.

**Town Portal** (`town_portal_switch.txt`) has 6 destinations per continent:

| Continent | Destinations |
|---|---|
| Jadame | Alvar, Ravenshore, Balthazar's Lair, Regna, Shadowspire, Dagger Wound |
| Antagarich | Castle Harmondale, Tularean Forest, Steadwick, Nighon, Celeste, the Pit |
| Enroth | Blackshire, Free Haven, Misty Isles, New Sorpigal, Silver Cove, Frozen Highlands |
| Chedian | Thjorgard, Sturmford, Drangheim, Guberland, Frosgard, Thronheim |

- Each destination is unlocked by its own qbit (visiting the town's fountain or statue).
- A global page with qbit 309 lists the continents.
- MM9 marks the Dark Passageway, the Thousand Terrors and the Afterworld as `noTeleportMaps`.

**Lloyd's Beacon:** free placement, so there is no data to calibrate.

**Design rule:**
- The start pocket connects to the hub by a single boat or road.
- The hub's stable and dock reach 3–5 maps.
- Remote areas cost 5–10 days of walking or a boat leaving once a week.
- Town Portal covers 6 towns, chosen to include at least one late-game base.

## 5. Quest inventory

Where each world's quest state lives in the merged base:
- `engine/data_tables/english/quests.txt` (1,719 bits) has an `Owner` column: MM8 is bits 1–511, MM7 512–1023, MM6
  1024–1535, and the Shared range 1536–1719 holds promotions, guild joins, the arena and Arcomage.
- `autonote.txt` uses the same `Owner` column.
- `npc.txt` has no world column; its NPC ids fall in blocks: MM8 1–339, MM7 340–785, MM6 786–1183, random map NPCs
  1184+.

Main-quest and side-quest counts are by quest text and giver (±3). Promotion counts are exact: they come from the
script events that change a character's class.

### Main quest

| | Journal steps | How it is chained |
|---|---|---|
| MM6 | about 15 (9 story bits + 6 High Council tasks) | Letters → Regent → the six lords → expose Silvertongue → the Oracle: 4 memory crystals (`6t6`, `cd1`, `cd2`, `cd3`) → control cube (`pyramid`) → Archibald and the Ritual of the Void (`sci-fi`) → the Hive. 9 seer hints. |
| MM7 | 30 bits, about 23 per playthrough | 17-step shared trunk: scavenger hunt (6 items) → Lord of Harmondale (castle `7d29`, dwarves `7d34`) → Erathia/Tularea intrigue with paired choices (Riverstride plans `7d31`, Loren `7d08`) → arbiter. Then **Light (6) or Dark (7)** via Celeste `7d25` or the Pit `7d26`: proving trial (Walls of Mist `7d11` / Breeding Zone `7d10`), altar pieces (`t01`/`t02`), Xenofex (Colony Zod `7d27`), soul jars, the Small House `mdt15` → the Lincoln `7d23`. |
| MM8 | 30 bits, about 24 per playthrough | Caravan → pirate outpost `d06` → the crystal → the **alliance**: recruit 3 of 5 candidate factions with one task each (Necromancers `d19` or Sun `d22`; Dragons `d17` or Dragon Hunters `d16`; Minotaurs `d24`) → sink the Regnan fleet (`d33`, `d34`) → 4 elemental planes and hearts (`d27`, `d29`) → Escaton (`d10`, `d35`) → 4 lord prisons (`d36`–`d39`) in the Plane Between Planes. 24 seer stages, 18 history chapters. |
| MM9 | 7 chapters; 43 playthrough segments | Prologue → pledges from 6 clans, the open act → council → Arslegard → Six Fires → the tomb. 16 of 24 dungeons are on the story path. |

### Side quests, promotions and mini-systems

| | MM6 | MM7 | MM8 | MM9 rework |
|---|---|---|---|---|
| Journal lines with text | 61 (52 real quests) | 77 | 71 | 143 (main, side and promotion together) |
| Side quests | ~26 | ~19 | ~30 | 16 standalone; ~49 walkthroughs including promotions |
| Promotions | 6 lords × 2 tiers = 12 promotions, ~17 journaled quests | 9 classes × 3 (first tier, then Light or Dark) = 27 promotions, ~28 lines | 8 classes × 1 tier (Knight and Dragon have 2 steps) | 12 composite lines (4 first tier + 7 second tier + Lich), 1–3 tasks each, 53 test segments |
| Promotion dungeons | 7 | ~20 (incl. 15 barrows for Initiate) | 7 | 8 |
| Guild membership | 17 joins (11 magic + 6 thieves/mercenary), 25 membership NPCs | 11 magic guilds, 26 membership NPCs | none (class by race) | none |
| Seer | 9 hint stages | – | 24 hint stages | – |
| Arena | 4 tiers (Page → Lord) | 4 tiers | yes | yes (a Gladiator labour) |
| Arcomage | – | 13 taverns, 1 quest | 11 taverns, 2 quests | – |
| Obelisks (one clue each → a hidden treasure) | 15 | 14 | 9 | – |
| Wells/fountains with an autonoted effect | 44 | 31 | 27 | 1 well |
| Shrines and altars | 12 monthly stat shrines, one per map and active in its month; 7 Moon altars; 4 elemental shrines; 7 pedestals for statuettes | 12 outdoor shrines plus ~16 altars | – | 10 stat stones |
| Other | Circus of the Sun (moving tents); dice NPC; 6 Dragon Towers; stable price-fixing | Harmondale castle with its own history book; 7 throne rooms; bounty hunts; golem parts; 3 statuettes | bounty hunts; cheese and Pure-stat potion fetches; Adventurer's Inn roster of 50 | Fleet Foot; walk-in shops; clan pledges |

### NPCs, hirelings and teachers

| | MM6 | MM7 | MM8 | MM9 |
|---|---|---|---|---|
| Named NPCs (`npc.txt`) | 398 | 446 | 339 | 442 RUDE dialogue files |
| NPCs in houses / houses with NPCs | 367 / 330 | 247 / 195 | 264 / 235 | – |
| NPCs with topics / distinct topics | 192 / 215 | 332 / 393 | 299 / 495 | – |
| Hirelings | 173 fixed house NPCs (of 332 with a profession, 72 professions) | random street peasants (540 names × 12 Recruit professions) | random peasants + 50 roster characters | 15 (13 paid, 2 story) |
| Teacher NPCs / skill offers | 91 / 92 (31 skills) | 144 / 145 (35) | 105 / 105 (35) | 69 / 115 (23 skills: 46 Expert, 46 Master, 23 Grandmaster) |
| Teacher places (`trainer_places.txt`) | 98 | 124 | 106 | 78 (Thjorgard City alone has 20) |

- **Professions:** `npc_professions.txt` lists 77 shared professions.
- **Teacher topics:** `teacher_topics.txt` has 178 topics shared by all worlds: 69 Expert, 69 Master, 40
  Grandmaster.
- **MM9 trainers by town:** Thjorgard 28, Sturmford 20, Drangheim 18, Frosgard 16, Guberland 10, Thronheim 10,
  Yorwick 8, Lindisfarne 5. Teachers stand in the street and on the roads, not only in houses.
- **Calibration:** about 100–145 teacher offers per world. That is about 3 per skill: Expert, Master and Grandmaster
  in different towns, with the Grandmaster one usually in a late or remote map.

## 6. How MM9 became a world package, and what a new world must provide

### `world.yml`

`world.yml` is parsed by `game/content/ContentManifest.cpp`. MM6–MM8 each use 22–28 lines (`id`, `name`,
`sourceGame`, `start.map`, `actorMovement`, `completion`). MM9 uses 249. Its keys:

| Group | Keys |
|---|---|
| Identity | `id` (= folder name), `name`, `sourceGame`, `contentSchemaVersion`, `dependencies: [engine]` |
| Start, death, saves | `start {map, introMovie}`; `partyDeath {map, position, yaw, keepGold, when[], otherwise{movie, reloadAutosave}}`; `autosave: arrival` |
| Story | `qbits {begin: 90000, end: 99999, mapping}`; `objectives`; `completion {qbit, continent, art, headline, text, layout, variants}` |
| Movement and AI | `partyMovement {eyeHeight 152, collisionRadius 38, collisionHeight 169, maxStepHeight 40.96}`; `actorAwareness`; `actorCombat`; `actorMovement.levelRadiusLimit` |
| Flags | `npcFollowers`, `streetNpcs`, `tavernHirelings`, `friendlyActorsBlockParty`, `combatLog`, `formations`, `fleetFoot`, `chestArtifactsOnly`, `groundGoldByItemTier` |
| Map lists | `openAirMaps` (19 BLVs with sky that follow the outdoor spell rules), `noTeleportMaps` (3) |
| Audio | `music {repeatGapSeconds, battleTrack, battleFadeSeconds}`, `musicAreas`, `ambience`, `ambientSounds` |
| Ids and tables | `idRanges`, `tableContributions` (below) |

### Id ranges

A new world must choose ranges that overlap none of these:

| Domain | MM9 | Hesper (staged, not mounted) |
|---|---|---|
| items | 10000–10999 | 11000–11999 |
| objects | 20000–20999 | 21000–21999 |
| monsters | 9000–9999 | 10000–10999 |
| vendors | 30000–30999 | 9300–9499 |
| decorations (row numbers) | 2001–2999 (engine 1–673) | 3001–3999 |
| sounds | 50000–59999 | 60000+ |
| qbits | 90000–99999 | 100000+ |
| map_stats rows | 9001–9080 (44 used) | – |

### Table contributions

`tableContributions` take one of two modes:
- **`append`**: the world's rows are added after the engine's base table, inside the world's declared id range. MM9
  appends items, readable_scrolls, item_effects/sets/aliases, random_items, object_descriptors,
  complex_item_pictures, monster_data/descriptors, sounds (×2), vendors and their aliases and stock,
  service_venues and their aliases, and decorations.
- **`distribution`**: world-local tables. MM9's are map_transitions, teacher_schedules, transport_routes,
  skill_trainers and hirelings.

**Warning:** the loaders for the distribution tables (`GameDataLoader::loadMm9*`, runtime in `game/mm9/`, 28 files)
return early unless the world is `"mm9"`. A new world needs that code generalised, or it has to use the engine's
MM6–MM8 tables (house_data, transport_locations, `npc.txt`).

### What else a world provides

Inside the world folder: `maps/<stem>.{odm|blv}` with `.scene.yml`, `.lighting`, `.bake.json` (optionally
`.cinematics.yml`); `events/maps/<stem>.lua`, `events/common/`, `behaviors/`; `journal/`, `dialogue/`, `ui/maps`
(minimaps); `data_tables/`, `icons_x2/`, `sprites/`, `textures(_x4)/`, `audio/`, `music/`, `videos/`;
`models/{actors,decorations,indoor_decorations,decoration_overlays}.yml` (GLBs installed with
`tools/install_model.py --world <w>`); `terrain_materials/` (an ODM will not load without it),
`terrain_decorations/`, `modifiers.yml`, `relations.yml`, `shields.yml`.

Decorations follow `devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`:
- The world's own `decoration_data.txt` rows go above the engine's last row (673), in increasing order with unique
  names.
- A map entity's `decoration_list_id` is its row number − 1.
- Once maps reference ids, those ids must never change.

**Engine rows the world still adds in `assets_dev/engine/`:** `map_stats.txt` rows (the world_id column assigns
the map to the world, and entering it switches worlds); a `continent_settings.txt` row (death map, skies, loading
pictures); a `character_selection.yml` continent entry; small rows in character_data, chest_data, object_list and
monster_projectiles; a `town_portal_switch.txt` page plus a slot on the global page. For MAW:
`rulesets/maw/worlds/<w>/balance.yml`, `bolster_maps.txt` rows and per-map pack reserves. For releases: an entry in
`tools/packaging/packs.yml`.

**C++ that hard-codes four continents:**

| Place | What it hard-codes |
|---|---|
| `NewGameScreen.cpp` ~2517 | continent cards |
| `NewGameScreenPartySheet.cpp` ~1550 | portrait world filter |
| `GameplayUiRuntime.cpp` ~263 | Dimension Door portals |
| `GameApplication.cpp` ~12600 | world → continent id |
| `MawItemRules.cpp` ~2544 | continent id per world |
| elsewhere | 28 `== "mm9"` checks |

### How MM9 was brought to MM6–MM8 density (`devdocs/mm9_rework/`)

- **One converter per map:** `level_generation/projects/mm9r_<map>/` builds on the shared `mm9r_common`. It compiles
  geometry, doors, lights, decorations, actors, loot tiers, the scene and the Lua, and bakes lighting.
- **Regions became open-air BLVs**, not ODMs (decided 2026-11-02 from the Isle of Ashes pilot):

  | | BLV | ODM |
  |---|---|---|
  | Triangles | 30.4k | 72.6k |
  | GPU p95 | 0.88 ms | 2.34 ms |
  | Textures | 310 MB | 492 MB |

  The BLV also keeps MM9's own tunnels and trails, which a heightmap resample broke.
- **Cities are BLV with sky.** Shops are walk-in rooms behind door portals: 48 vendors and 16 temple/training/bank/
  tavern venues, all opened through dialogue.
- **Density growth by act** (`tools/mm9_import_discovery/mm9_density_targets.py`):
  - Act 1 ×1.9, act 2 ×1.4 (its early clan maps ×1.0), the war ×2.3, the finale ×5 (Thousand Terrors ×2).
  - Counted monsters went from 1,476 to 2,723.
  - Before growth the outdoor median was 45 monsters in packs of 1.8, against MM7's 108 in packs of 2.5.
- **Fleet Foot replaces Fly** (Air 21: speed ×1.25/1.5/1.75). With no flying over packs, every placed pack is a
  forced fight, and the balance counts on that.
- **Loot:**
  - Treasure level by monster level: L1–7 → 1, 8–15 → 2, 16–30 → 3, 31–44 → 4, 45–64 → 5, 65+ → 6.
  - Monster gold ×2.2; item drop chance ×1.6, capped at 75 %.
  - Ordinary chests hold 3 items. Artifacts come only from 15 black chests (`chestArtifactsOnly`).
  - Promotion XP 16.5k / 37.5k; the target end level is about 69.
- **Composite promotions** (`worlds/mm9/dialogue/promotions.yml`, `MM9.Promotions` in `mm9_common.lua`): each of
  MM9's 11 promotion quests promotes every MMerge class line of its theme. One quest serves 3–4 class lines, so a new
  world can write about 8–12 thematic promotion quests instead of one per class (MM7 needed 27).
- **Teachers** are NPCs placed on the maps (`skill_trainers.txt`, 115 offers), not guild houses.

### Authoring new maps from scratch

Start from `level_generation/README.md`.

**Tools:** Blender through MCP; `mm9_compile_indoor_source` (BLV) and `openyamm-editor --headless-build-map
x.map.yml` (ODM); `tools/export_{indoor,outdoor}_scene_yml.py`; `tools/terrain_materials.py`;
`tools/lighting/bake_{outdoor,indoor,decorations}.py`; `tools/DECORATION_PLACEMENT.md`.

**Calibration:**
- ODM: 128 × 128 tiles of 512 units; Z = byte × 32; doors about 128 × 256; eye height 176; gaps between buildings
  464–735 (`OUTDOOR_CALIBRATION.md`).
- BLV: corridors 256–528 wide, doorways 256, steps ≤ 32.
- A mid-size dungeon in Hesper's playbook has 31 sectors, 14 doors, 64 monsters and 6 chests. That matches the MM7/MM8
  M class above.

**Track record:**

| Project | Result | Time |
|---|---|---|
| Brackenford town ODM + Greywatch Vault BLV | First maps built from scratch, using MM8 art | About 2 days, ~9 revision passes |
| Hesper | 22 maps: 4 ODMs, 16 dungeons, an undervault and test rooms; 86 monsters with 3D models | About 10 days with many parallel agents. Staged in `output/hesper_stage`; not in `assets_dev`, ending chain unbuilt |
| MM5 Castleview–Kalindra | Environment-only ODM: 326 BModels, 45 premises, no NPCs or monsters | Accepted 2026-09-09 |
| MM9 conversions (for comparison) | 18 BLVs | About 8.8 h of active time with up to 5 agents |

No document gives hours per map for work from scratch.

**For Xeen specifically,** read `level_generation/projects/mm5_world_feasibility/FEASIBILITY.md` first. It proposes
Darkside as 16 ODMs (6 surface, 6 sky, 4 planes) and about 22 BLVs. Its decoded source data is in
`reference/mm4_5_world_of_xeen/unpacked/`.

## 7. Targets for a new MM6–MM8-style world

Taken from the medians above, with MM7/MM8 as the reference:

| Item | Target |
|---|---|
| Outdoor maps | 9–13, with 1 start pocket, 1 hub, 5–8 regional towns and 2–4 wilderness or trap maps; plus 1–4 gated endgame zones |
| Towns | Start and hub get the full set (W A M Al, 2–7 guilds, Tm Tv Bk Tr St Bt, a hall). Regional towns get 6–9 services. Wilderness gets 0–3. 6–45 residences per town; 13–20 is typical. |
| Dungeons | 40–60. About 55 % S (≤40 monsters, ~1,000 faces, ~10 sectors, 1–3 chests), 40 % M, 2–4 L set pieces. About 1/3 story, 1/4 promotion, the rest optional. 3–5 entrances per outdoor map. |
| Outdoor encounters | 120–170 estimated monsters per map from 2–3 families at one d-level; the start at d1; 3–5 wells or fountains, 1 obelisk and 0–1 shrine per map; 5–13 chests |
| Level curve | Start A-tier level 2–4 (C ≤ 15); hub A 7–10; regions A 12–20 in any order; gated endgame A 50+, C 90–100. Lock/Trap 0 → 4 → 10 → 20. |
| Transport | 25–35 stable and boat route slots, 2–3 days each, 1–3 departures per week; 5-day map edges (10 for wilderness); 6 Town Portal towns |
| Quests | Main quest about 25–30 journal steps with one major branch or alliance choice. 20–30 side quests. 8–12 composite promotion quests (MM9 model). 10–15 obelisks; 25–45 drinkable features; one mini-game system (arena, Arcomage or shrines). |
| NPCs | 300–450 named NPCs, two thirds with topics; about 100–145 teacher offers |
| Monsters | 4,000–4,500 on a first visit across the world (MM6's ~8,600 is too grindy) |
