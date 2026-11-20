# Map craft calibration for a new MM6–MM8-style world (Xeen)

Research input for the Xeen world design (World of Xeen story, all-new maps). It answers one question: what
makes MM6–MM8 maps feel alive rather than bland, in numbers, and what the OpenYAMM pipeline already knows and can
build today. Quests, houses/services per town and world packaging are covered by a separate research note.

Written 2026-11-11 from this checkout. Everything measured here was read from the assets; nothing was changed.

## 0. Sources, method and units

| What | Where |
| --- | --- |
| Outdoor census (this note) | `map_craft/measure_outdoor.py` → `map_craft/outdoor_census.json`. Covers all 42 MM6–MM8 ODMs. It reads the ODM (`util/map_export.py`), the scene, the generated Lua (`RegisterEvent` hints and `contextActions` kinds), `map_stats.txt`, `house_data.txt` and `monster_data.txt` |
| Indoor census (this note) | `map_craft/measure_indoor.py` → `map_craft/indoor_census.json`. Covers all 161 BLVs: sector graph loops, secret/plate faces, trap/teleport/lever/summon events, uniques |
| Decoration survey | `level_generation/OUTDOOR_DECORATION_CALIBRATION.md`, `catalogues/outdoor_decorations/map_summary.csv` (42 maps, 17,929 visible sprites) |
| Canon dungeon survey | `design/kreegan_world/research/survey.json` (44 well-known dungeons), `ROOM_SHAPES_MM678.md` (161 BLVs), `level_generation/projects/hesper_dressing_study/README.md` |
| Calibrations accepted by the driver | `level_generation/OUTDOOR_CALIBRATION.md`, `SETTLEMENT_DENSITY.md`, `WILDERNESS_CALIBRATION.md`, `LANDSCAPE_DETAIL_CALIBRATION.md`, `REGIONAL_TRANSITION_CALIBRATION.md`, `SKETCH_LAYOUT_CALIBRATION.md`, `VISUAL_CALIBRATION.md`, `HOUSE_VARIETY.md`, `FRONTAGE_AND_TILE_CALIBRATION.md` |
| Ground, sky, weather | `level_generation/terrain/materials/README.md` + `TILESETS.md`, `terrain/MEADOW.md`, `terrain/GRASS_LOD.md`, `lighting/SKY_RENDERING.md`, `lighting/WEATHER_PLAN.md` |

**Units.**
- One terrain cell is 512 units; an ODM is 128 × 128 cells.
- The travel bounds are about ±23,143, a playable square about 46,000 units across (`map_navigation.txt`). Terrain continues about 9,000 units beyond each prompt.
- A **block** is 4,096 × 4,096 units (8 × 8 cells). The playable square holds about 128 blocks.
- The party walks at 384 units/s and runs at 768 (`OutdoorMovementDriver.h`). So 1,000 units is 1.3 s running or 2.6 s walking, and edge to edge is about 60 s running.
- Ordinary doors are 128 × 256.

**Census conventions.**
- A *POI* is a bound interaction collapsed within 400 units: service door, dungeon entrance, chest, fountain, well, shrine, obelisk, pedestal, stat challenge, campfire, ship, cauldron or sword-in-stone. Residences and map exits are left out.
- *POI NN* is the median distance from each POI to its nearest other POI.
- *Hostiles* means expected actors: each spawn marker gives the midpoint of its MapStats count, plus fixed hostile actors.
- *Start* is the party-start and N/S/E/W arrival markers.
- *Service* means any non-residence house door: shop, guild, temple, tavern, training, bank, stables, boats or throne.
- MM6 counts use the merged MMerge MapStats (often 3–5 or 4–6 per marker); MM7/MM8 use 1–3. Expect MM6 headcounts to run about 1.5–2× higher.

## 1. Outdoor maps measured

### 1.1 Medians by map type

Each type is a set of the 36 ordinary maps. A map can appear in several sets. The planes and the underwater Shoals
are listed separately.

| Type (maps) | Water % | Road % of land | Deco / block (central land) | Services | Residences | Dungeon entr. | Chests | Fountain + well | POIs | POI NN | Spawn markers | Hostiles | Hostile-group NN | Start → first fight | Start → first service |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Town hub, ≥13 services (17) | 26 | 2.9 | 4.0 | 17 | 22 | 4 | 6 | 5 | 38 | 1,520 | 48 | 150 | 3,090 | 4,350 (2,970–6,270) | 10,550 |
| Wilderness / outpost, ≤9 services (15) | 10 | 1.2 | 2.1 | 6 | 13 | 4 | 4 | 3 | 24 | 2,000 | 64 | 132 | 2,820 | 5,660 (4,940–9,850) | 17,410 |
| Desert (Dragonsand, Bracada, Ironsand) | 17 | 1.2 | 3.0 | 5 | 15 | 3 | 6 | 3 | 23 | 4,390 | 74 | 148 | 2,650 | 5,260 | 24,350 |
| Snow / high country (Kriegspire, Frozen Highlands, Nighon) | 6 | 1.8 | 1.9 | 8 | 15 | 6 | 2 | 8 | 30 | 1,800 | 71 | 142 | 3,020 | 2,340 | 10,550 |
| Swamp / wetland (Mire, Tatalia, Ironfist) | 38 | 3.0 | 3.3 | 14 | 17 | 5 | 3 | 4 | 26 | 2,020 | 80 | 366 (MM6) | 2,630 | 4,350 | 8,430 |
| Island, water ≥40 % (10) | 72 | 2.4 | 6.3 | 13 | 11 | 2.5 | 5 | 4.5 | 36 | 1,820 | 48 | 163 | 3,970 | 3,440 | 2,530 |
| Necropolis / cursed (Sweet Water, Deyja, Shadowspire, Barrows) | 10 | 1.5 | 4.3 | 4 | 13 | 4 | 6.5 | 3 | 27 | 2,750 | 53 | 106 | 3,000 | 4,940 | 17,410 |
| Elemental planes (Air, Fire, Water, Between) | 10 | 0 | 0.5 | 0 | 6 | 1.5 | 0 | 0 | 2 | — | 84 | 167 | 2,520 | 1,450 | — |

**Whole-set figures for the 36 ordinary maps.**

| Measure | Value |
| --- | --- |
| POI NN (p25 / median / p75) | 1,320 / 1,780 / 2,590 units, i.e. 1.7–3.4 s at a run between interest points |
| Hostile-group NN (centres) | 2,620 / 3,010 / 3,830 |
| Spawn markers | 45 / 58 / 71 |
| Hostiles at load | 111 / 147 / 193 |
| Start → first hostile marker | p10 1,970, median 5,010, p90 11,820 (about 6.5 s running at the median) |
| Start → first service door | 5,470 / 11,840 / 20,980. Arrival points are on the edges; many maps put the town away from most arrivals |

Map size in content terms: a typical playable map holds about **25–55 POIs, 3–5 dungeon entrances, 4–10 outdoor
chests, 2–40 loose items (median 22) and 110–150 hostiles at load** in MM7/MM8. MM6's merged counts push it to
160–390.

### 1.2 Every map

Columns:
- **Deco/blk** is the catalogue's initially visible sprites per block of central nonwater land.
- **Svc / res / dng / chest** are logical service doors, residences, dungeon entrances and outdoor chests.
- **Other devices**: native interactive decorations, plus event-bound trees, ships, tents, statues and graves ("ev").

| Map | Name | Biome | Water % | Road % land | Deco / blk | Svc / res / dng / chest | Fount+well / shrine / obelisk | Other devices | POIs | POI NN | Spawns → hostiles | Start→fight | Start→service |
|---|---|---|--:|--:|--:|---|---|---|--:|--:|---|--:|--:|
| mm6/outa1 | Sweet Water | blighted | 1 | 1.7 | 4.51 | 0 / 0 / 1 / 1 | 3 / 0 / 1 | ped 1 | 7 | 9104 | 20 → 60 | 5094 | – |
| mm6/outa2 | Paradise Valley | lush highlands | 8 | 2.7 | 1.85 | 6 / 15 / 0 / 3 | 1 / 0 / 1 | fire 1 | 12 | 1219 | 63 → 153 | 3536 | 20902 |
| mm6/outa3 | Hermit's Isle | island | 43 | 1.3 | 2.38 | 0 / 0 / 1 / 1 | 1 / 0 / 1 | – | 4 | 8513 | 93 → 324 | 3122 | – |
| mm6/outb1 | Kriegspire | highlands | 0 | 1.8 | 1.93 | 6 / 15 / 6 / 2 | 5 / 2 / 1 | ped 1, fire 1, tree ev 1 | 25 | 1798 | 33 → 98 | 12672 | 26097 |
| mm6/outb2 | Blackshire | dry settlement | 1 | 2.1 | 2.67 | 21 / 17 / 2 / 6 | 5 / 1 / 1 | food tree 77 | 36 | 1279 | 43 → 134 | 18460 | 6707 |
| mm6/outb3 | Dragonsand | desert | 33 | 1.2 | 2.97 | 5 / 6 / 2 / 5 | 3 / 1 / 1 | ped 1 | 17 | 5427 | 74 → 206 | 5359 | 33837 |
| mm6/outc1 | Frozen Highlands | snow | 6 | 2.9 | 2.86 | 18 / 30 / 2 / 2 | 8 / 1 / 1 | fire 3 | 36 | 1824 | 71 → 305 | 2335 | 10550 |
| mm6/outc2 | Free Haven | temperate city | 14 | 4.1 | 2.78 | 31 / 63 / 3 / 2 | 3 / 1 / 1 | barrel 3, fire 3, food tree 19 | 48 | 2003 | 48 → 222 | 6616 | 5160 |
| mm6/outc3 | Mire of the Damned | haunted wetland | 38 | 3.0 | 3.28 | 14 / 14 / 3 / 3 | 1 / 1 / 1 | ped 1, fire 1, food tree 72 | 25 | 1415 | 89 → 386 | 3971 | 7899 |
| mm6/outd1 | Silver Cove | coastal grassland | 52 | 2.5 | 4.87 | 19 / 42 / 3 / 3 | 5 / 1 / 1 | fire 2, sword-stone 3 | 38 | 1950 | 47 → 172 | 2635 | 27673 |
| mm6/outd2 | Bootleg Bay | tropical coast | 63 | 4.3 | 6.21 | 19 / 8 / 4 / 5 | 5 / 1 / 1 | ped 1, fire 2, food tree 6 | 38 | 1425 | 37 → 172 | 1600 | 7618 |
| mm6/outd3 | Castle Ironfist | wooded highlands | 40 | 5.6 | 1.96 | 22 / 17 / 5 / 5 | 4 / 1 / 1 | fire 1, sword-stone 1 | 37 | 2347 | 80 → 366 | 4352 | 8427 |
| mm6/oute1 | Eel Infested Waters | islands | 87 | 0.8 | 3.79 | 6 / 6 / 1 / 2 | 2 / 1 / 1 | sword-stone 1 | 14 | 4088 | 62 → 202 | 5599 | 1868 |
| mm6/oute2 | Misty Islands | island settlement | 84 | 3.8 | 3.9 | 16 / 13 / 1 / 5 | 4 / 1 / 1 | barrel 1, fire 4, food tree 8, tree ev 6 | 39 | 1057 | 32 → 164 | 2972 | 2532 |
| mm6/oute3 | New Sorpigal | coastal village | 70 | 2.3 | 6.32 | 17 / 22 / 3 / 16 | 5 / 1 / 1 | barrel 4, fire 5, food tree 15, sword-stone 1, tree ev 6 | 54 | 1133 | 56 → 224 | 4598 | 5470 |
| mm7/7out01 | Emerald Island | island village | 93 | 5.6 | 7.09 | 11 / 7 / 2 / 3 | 6 / 0 / 0 | fire 2, sign deco 9, tent ev 1, lever ev 1 | 27 | 1539 | 11 → 38 | 17737 | 4065 |
| mm7/7out02 | Harmondale | temperate highlands | 2 | 2.1 | 3.94 | 19 / 16 / 2 / 10 | 5 / 1 / 1 | fire 3, tree ev 8, tent ev 1 | 52 | 1331 | 43 → 244 | 4829 | 20976 |
| mm7/7out03 | Erathia | temperate city | 16 | 3.0 | 4.03 | 15 / 30 / 11 / 11 | 7 / 2 / 1 | barrel 1, fire 1, sign deco 7, tree ev 8, tent ev 2, lever ev 1 | 57 | 1165 | 48 → 111 | 4930 | 23277 |
| mm7/7out04 | Tularean Forest | forest | 39 | 2.6 | 4.55 | 17 / 20 / 4 / 7 | 4 / 2 / 1 | fire 4, sign deco 3, tree ev 9, tent ev 1 | 45 | 1258 | 47 → 52 | 11599 | 11840 |
| mm7/7out05 | Deyja | necropolis | 18 | 1.3 | 2.11 | 7 / 20 / 4 / 7 | 7 / 2 / 1 | – | 27 | 3061 | 50 → 108 | 4776 | 17409 |
| mm7/7out06 | Bracada Desert | desert city | 7 | 0.7 | 1.77 | 9 / 15 / 3 / 6 | 4 / 2 / 1 | – | 24 | 4393 | 37 → 80 | 5261 | 8025 |
| mm7/7out13 | Tatalia | wetland coast | 26 | 1.1 | 3.63 | 13 / 22 / 6 / 1 | 4 / 3 / 1 | – | 26 | 2017 | 43 → 86 | 8307 | 15368 |
| mm7/out09 | Evenmorn Island | ruined island | 85 | 0.0 | 9.47 | 4 / 3 / 2 / 6 | 3 / 3 / 1 | barrel 4 | 18 | 3194 | 48 → 96 | 2122 | 2042 |
| mm7/out10 | Mount Nighon | snow mountains | 10 | 0.3 | 1.73 | 8 / 13 / 6 / 7 | 8 / 1 / 1 | – | 30 | 1239 | 71 → 151 | 523 | 705 |
| mm7/out11 | Barrow Downs | burial landscape | 9 | 0.8 | 4.75 | 1 / 6 / 6 / 7 | 2 / 2 / 1 | barrel 1, fire 2, tree ev 6 | 26 | 2429 | 65 → 130 | 5724 | 24270 |
| mm7/out12 | Land of the Giants | barren highlands | 42 | 0.1 | 3.52 | 0 / 1 / 5 / 0 | 1 / 1 / 1 | – | 8 | 7687 | 66 → 132 | 5660 | – |
| mm7/out14 | Avlee | forest coast | 28 | 0.7 | 1.97 | 11 / 13 / 3 / 2 | 5 / 3 / 1 | fire 5, tree ev 10, tent ev 1 | 39 | 1366 | 64 → 134 | 6068 | 19629 |
| mm8/out01 | Dagger Wound Island | tropical islands | 70 | 2.6 | 11.83 | 15 / 19 / 5 / 7 | 5 / 0 / 1 | buff ped 1, stat chal 1, barrel 13, fire 1, food tree 43, sign deco 9, ship ev 3, hut ev 9 | 53 | 1690 | 46 → 110 | 3762 | 2119 |
| mm8/out02 | Ravenshore | temperate city | 26 | 4.2 | 7.07 | 19 / 54 / 7 / 12 | 4 / 0 / 1 | buff ped 1, stat chal 2, barrel 23, fire 12, sign deco 4, grave ev 1 | 53 | 1547 | 59 → 190 | 3777 | 27579 |
| mm8/out03 | Alvar | temperate city | 7 | 3.4 | 6.68 | 13 / 36 / 4 / 9 | 5 / 0 / 1 | buff ped 1, stat chal 1, barrel 20, fire 1, cauldron 2 | 38 | 1921 | 61 → 122 | 6266 | 15289 |
| mm8/out04 | Ironsand Desert | desert + lava | 17 | 1.6 | 4.04 | 2 / 21 / 5 / 7 | 0 / 0 / 1 | buff ped 1, stat chal 1, barrel 8, fire 2, cauldron 1, grave ev 1 | 23 | 832 | 74 → 153 | 1776 | 24354 |
| mm8/out05 | Garrote Gorge | grass and dirt forts | 1 | 1.9 | 1.55 | 7 / 18 / 4 / 4 | 3 / 0 / 1 | fire 1, cauldron 1 | 21 | 1762 | 73 → 185 | 9126 | 17412 |
| mm8/out06 | Shadowspire | necropolis | 10 | 2.1 | 4.18 | 13 / 33 / 4 / 6 | 3 / 0 / 1 | buff ped 1, stat chal 1, barrel 11, grave ev 1 | 31 | 1518 | 56 → 120 | 1824 | 12473 |
| mm8/out07 | Murmurwoods | forest | 0 | 1.2 | 10.08 | 2 / 10 / 3 / 2 | 2 / 0 / 1 | buff ped 2, stat chal 1, barrel 10, statue ev 5 | 20 | 5111 | 81 → 163 | 10939 | 7789 |
| mm8/out08 | Ravage Roaming | dry grassland | 14 | 1.3 | 1.64 | 3 / 6 / 8 / 10 | 0 / 0 / 1 | buff ped 1, stat chal 1, barrel 2, fire 5, cauldron 1, grave ev 1 | 31 | 867 | 71 → 142 | 12038 | 37897 |
| mm8/out13 | Regna | tropical island | 74 | 0.0 | 6.55 | 9 / 16 / 6 / 6 | 4 / 0 / 1 | buff ped 2, stat chal 1, barrel 10, fire 1, sign deco 4, ship ev 2 | 34 | 2001 | 64 → 128 | 10565 | 1792 |
| mm8/elema | Plane of Air | no terrain, islands | 0 | 0 | 2.97 | 0 / 14 / 1 / 0 | 0 / 0 / 0 | 428 `dec57` path markers | 1 | – | 68 → 136 | 10425 | – |
| mm8/elemf | Plane of Fire | lava 74 % | 74 | 0 | 0 | 0 / 6 / 2 / 0 | 0 / 0 / 0 | – | 3 | 1141 | 70 → 140 | 1096 | – |
| mm8/elemw | Plane of Water | seabed | 0 | 0 | 0.96 | 0 / 6 / 0 / 0 | 0 / 0 / 0 | 148 coral/seaweed | 0 | – | 97 → 216 | 404 | – |
| mm8/pbp | Plane Between Planes | otherworld | 19 | 0 | 0 | 0 / 0 / 7 / 0 | 0 / 0 / 0 | – | 7 | 16536 | 112 → 224 | 1810 | – |

Ground mix per map (% of cells by material family): `level_generation/terrain/materials/TILESETS.md#maps`.

### 1.3 Decorations by type

These are whole-map visible sprite counts from the catalogue. For the full palettes see
`OUTDOOR_DECORATION_CALIBRATION.md#practical-palettes-above-the-terrain-material`.

| Type | Trees | Low plants / flowers | Dry plants | Rocks | Dead wood | Remains / ritual | Working props | Fires / lights |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| Temperate city (Ravenshore, Alvar, Erathia, Free Haven) | 170–620 | 190–280 | 0–80 | 40–205 | 0–5 | 0–6 | 1–35 (barrels, trash, cauldrons) | 1–15 |
| Forest (Murmurwoods, Tularean) | 230–1,480 | 0–190 | 0 | 35–207 | 1–141 stumps | 0 | 0–10 | 0–4 |
| Wilderness grass/dirt (Garrote, Ravage, Paradise Valley) | 130–135 | 0–53 | 0–151 | 60–85 | 0–35 | 0–5 | 1–2 | 1–5 |
| Desert (Dragonsand, Bracada, Ironsand) | 0–86 | 0 | 126–290 | 53–225 | 0 | 0–137 bones | 0–9 | 0–2 |
| Snow (Frozen Highlands, Nighon, Kriegspire) | 129–469 | 0–22 | 0 | 2–102 | 0–13 | 0 | 0 | 0–3 |
| Swamp (Mire, Tatalia) | 300–390 | 0 | 0 | 0–84 | 0 | 0 | 0 | 0–1 |
| Island (New Sorpigal, Dagger Wound, Regna, Emerald) | 50–370 | 40–280 | 0 | 11–45 | 0 | 0–9 | 0–13 | 1–5 + 68 smoke emitters |
| Necropolis (Shadowspire, Deyja, Barrow Downs) | 0–370 | 0–70 | 0–172 | 9–159 | 84–275 | 95 skeletons + 225 rune posts (Shadowspire) | 0–11 | 0–2 |
| Plane of Air | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 428 path markers (one descriptor) |

Density (central land, sprites per block): Garrote 1.6, Ravage 1.6, Bracada 1.8, Dragonsand 3.0,
Shadowspire 4.2, Alvar 6.7, Ravenshore 7.1, Murmurwoods 10.1, Dagger Wound 11.8.

Share of central land farther than 2,048 from any sprite: 7 % (Dragonsand) to 61 % (Garrote). Open space is a
design tool, not a defect, *if* terrain, architecture or a view fills it.

### 1.4 Monster groups and spacing

| Measure | MM6 (merged MapStats) | MM7 / MM8 |
| --- | --- | --- |
| Monsters per spawn marker | 1–6 (typically 2–4, 3–5 or 4–6) | 1–3 (Ravenshore Human Mercenary 2–5) |
| Spawn markers per map (p25 / med / p75) | 40 / 56 / 73 | 47 / 59 / 66 |
| Hostiles at load (p25 / med / p75) | 159 / 202 / 265 | 108 / 128 / 151 |
| Families per map | 3 encounter slots (A/B/C), weighted by difficulty tiers | same |
| Markers within 1,600 of each other | mostly isolated (1 marker per cluster) | the same, except tight packs: Ravenshore wolves are 10 groups of 3–5 markers, marker NN 257–375 |
| Group-centre NN (p10 / med / p90) | 2,610 / 3,320 / 4,450 | 2,240 / 2,820 / 4,730 |

Dispersed families (Ravenshore centaurs, marker NN 1,180–2,200) and tight packs coexist on one map. A guarded
dungeon entrance is optional (`WILDERNESS_CALIBRATION.md`). Of Ravenshore's three entrances, one has a pack
within 1,400 and two have none within 5,500.

Driver decisions on headcount:
- Brackenford's first wilderness (14 enemies, 2 camps) read as empty. It became 73 hostiles in 11 areas with quiet gaps (`WILDERNESS_REVISION.md`).
- MM9's target is "MM8-like outdoors: 100–180 monsters per map in packs per encounter area, with quiet gaps", "never overcrowded or out of place" (`devdocs/mm9_rework/BALANCE_PLAN.md`).

### 1.5 Readings that matter for a new map

1. **Every ordinary map has exactly one obelisk** (35 of 36). It is a fixed rhythm device: one word of a riddle, written to the autonotes; the riddle leads to a treasure.
2. **Water carries a large share of the map.** The median town or island is 26–72 % water. Coastlines give the edges of the playable land, view lines and boat or ferry anchors. A land-locked map (Kriegspire, Murmurwoods, Garrote) needs relief and screens instead.
3. **Roads are scarce: 1–4 % of land cells.** They link town, gates and regional exits only. Caves, camps and treasure stay off-road (driver, `test_img/1249.png`).
4. **POIs are about 1,500–2,000 apart: 2–3 s of running.** Sparse maps (Sweet Water, Hermit's Isle, Land of the Giants, Bracada) still have 5,000–9,000 gaps, but fill them with fights and terrain.
5. **First fight within 2,000–6,000 of most arrivals**, with no fight inside the town. On ordinary maps the town is often far from edge arrivals (median 11,800); boat, coach and teleport arrivals land in town.
6. **Interest is layered**: architecture and landforms (BModels, relief), interaction devices (this section), dressing sprites (trees/rocks/props), and activity (smoke, fires, NPCs, sound). A large sprite total did not save Brackenford from looking bare; the layers' placement did.

## 2. Catalogue of recurring interest devices

Frequencies are over the 36 ordinary MM6–MM8 outdoor maps unless stated. Effects come from the bound Lua:
Kind = MM6 / MM7 / MM8.

| Device | How it is built | Frequency (per map) | What it does | Notes for Xeen |
| --- | --- | --- | --- | --- |
| Obelisk | BModel, event `Obelisk` | **1 on 35 of 36 maps** | One riddle word into the autonotes (QBit); the full riddle finds a buried treasure | Xeen's riddle and "word" quests map directly; keep one per map |
| Fountain | BModel(s) or deco, `Drink from Fountain` | MM6 1–6 (median 3); MM7 0–2; MM8 0–2 | MM6: +2 **permanent** stat with a MapVar charge count; heal HP/SP; cure; temporary stat or resistance; autonote of the effect | Xeen is full of stat fountains: one permanent and one or two temporary per map |
| Well | BModel | 0–8 (median 2); MM7 dominant (1–7) | Gold if broke, temporary stat, resistance, cure, rare permanent stat, rare damage | Pair one well with each settlement |
| Shrine / altar | BModel | MM6 0–2, usually 1 (calendar shrine); MM7 0–3 altars; MM8 0 | MM6: +stat in a given month (`calendar`); MM7 altars give a stat, teleport or quest | A month- or day-bound shrine fits Xeen's calendar puzzles |
| Buff pedestal (MM8 `dec44`–`dec55`) | Native interactive deco, global events 531+ | 0–2; on 8 of 14 MM8 maps | Day of the Gods, Haste, Shield, resistances, Stone Skin … | Planning range 1–2 per map (`LANDSCAPE_DETAIL_CALIBRATION.md`) |
| Stat challenge (MM8 `dec40`–`dec43`) | Native deco, events 543–570 | 0–2; on 8 MM8 maps | Stat ≥ tier threshold grants skill points; completion bits are shared by tier | Allocate own state if it must reward independently |
| MM6 pedestal (`ped0x`) | Deco + `SetSprite` | 5 MM6 maps, one each | Statuette quests | Quest-item sockets |
| Barrel (stat barrel) | Native deco `dec03`, `smlbarel`, `bigbarel`, `7dec32` | Outdoor: 2–23 on 8 of 14 MM8 maps, MM6 0–4. Indoor: MM6 on 23 of 51 BLVs (~12 each), MM7 18 of 63, MM8 5 of 47 | Random colour: +2 permanent to one of seven stats (global events 269–275) | Coloured barrels are a cheap "something to click" layer in work yards and dungeons |
| Cauldron, trash heap | `dec26`; `dec23` / `trasheap` / `7dec01` | Cauldron 0–2 (4 maps); trash 12 in Ravenshore's working district | Cauldron: +2 permanent fire/water/air/earth resistance (events 277–280); trash: rummage (global events 281+) | Rough districts and camps |
| Campfire / fire | `ckfyr00`, `dec24`/`25`, `7dec02` | Median 1, up to 12 (Ravenshore); on 23 maps | Light; some give food | A camp's centre |
| Food / fruit tree | `6tree06`, `tree06a`, `plant34`; MM7 seasonal trees | MM6 6–77 food trees; MM7 seasonal fruit trees (43 events) | Food, seasonal apples (item) | Orchards and oases |
| Signpost | MM6/MM7 sign BModels (115 models, 22 maps); MM7/8 sign decos (`7dec33`, `dec30`) | 3–9 at forks and gates | Direction text ("East to Harmondale", "Welcome to …") | Every exit road and fork |
| Sword in the stone | `swrdstn` | 4 MM6 maps, 1–3 each | Actual Might ≥ 60 pulls an artifact sword once (Silver Cove event 220) | Optional set piece |
| Bridge | BModel assembly | 55 bridge models in 18 maps | Crossing | Must sit 64+ above terrain; check full deck contact |
| Ships, docks, boats | BModels and decos | Ships or wrecks in 19 maps; docks in 19 | Boat service, wreck chest, landing craft | A Xeen coast or sky-dock |
| Towers, ruins, camps | BModel kits | Towers in 16 maps; tent/camp kits in 11; ruins in 2 | Landmarks; many are dungeon entrances (Dragon Hunter Camp, War Camp, Pirate Outpost, Silver Helm Outpost) | Outposts as small BLVs |
| Standing stones | BModels | 4 maps (8 models) | Landmark or quest | A stone circle is a one-per-world event, not scatter |
| Caves / dungeon entrances | Small BModel mouth (Ravenshore `d08entrance` is 576 × 896 × 576) set into a terrain cleft | Median 3.5 (0–11); MM7 Erathia 11, MM8 Ravage 8 | `MoveToMap` to a BLV, with a key check where needed | 3–6 per wilderness map |
| Outdoor chests | Small BModel or crate, `OpenChest` | Median 5 (0–16; New Sorpigal 16 crates) | Fixed or random loot | Next to an entrance or a camp, behind a guard |
| Loose items | Scene sprite objects | Median about 30 (0–132) | Pickups | Bones, weapons at camps |
| Hermit, seer, oracle | A lone house | Hermit's Hut (Kriegspire), The Seer, The Oracle | Quest givers | Xeen's lone sages |
| Circus | 12 house rows (tents and wagons) | MM6 only: one circus that moves with the seasons (Bootleg Bay, Dragonsand rows in the table) | Games for prizes | A seasonal Xeen fair |
| Arena | Separate BLV | One per game (`zarena`, `7d05`, `d42`) | Fights for gold | One per world |
| Cairn | none in MM6–MM8 data | 0 | — | New device if wanted |

Combined, an MM6 map has about **8–12 interaction devices** besides houses and chests. These are fountains, wells,
the shrine, the obelisk, a pedestal and food trees. An MM8 map has about **4–6 kinds**: wells, obelisk, buff
pedestals, stat challenges, barrels and cauldrons. The obelisk and a fountain or well appear on nearly every map;
the others rotate.

## 3. Indoor dungeon craft

### 3.1 Canonical dungeons

Source: `survey.json`, 44 well-known dungeons, p25 / median / p75.

| | MM6 (16) | MM7 (15) | MM8 (13) |
|---|---|---|---|
| Floor area (M units²; one cell is 0.26 M) | 50 / 100 / 220 | 24 / 73 / 90 | 20 / 28 / 65 |
| Floor levels | 3 / 3 / 4 | 3 / 4 / 5 | 3 / 3 / 5 |
| Doors | 13 / 25 / 36 | 4 / 10 / 25 | 4 / 12 / 24 |
| Monsters (estimated) | 130 / 188 / 218 | 34 / 54 / 72 | 32 / 44 / 78 |
| Monsters per sector (median) | 2.6 | 1.9 | 2.5 |
| Chests | 6 / 6 / 10 | 4 / 5 / 8 | 1 / 2 / 7 |
| Pressure plates | 2 / 17 / 29 | 0 / 1 / 4 | 0 / 6 / 16 |
| Secret faces | 0 (MM6 does not use the flag) | 0 / 2 / 9 | 0 / 2 / 8 |

By group (DUNGEON_PLAYBOOK §1, medians):

| Group | Sectors | Doors | Lights | Monsters | Chests | Switch events |
| --- | --: | --: | --: | --: | --: | --: |
| Starter | 22 | 10 | 22 | 61 | 3 | 9 |
| Mid | 31 | 14 | 32 | 64 | 6 | 14 |
| Large | 47 | 27 | 39 | 120 | 5 | 25 |

### 3.2 All 161 BLVs: topology and mechanics

From `indoor_census.json`; maps with at least 3 sectors.

| p25 / median / p75 (share of maps with any) | MM6 (44) | MM7 (60) | MM8 (44) |
|---|---|---|---|
| Occupied sectors | 22 / 45 / 72 | 8 / 24 / 39 | 9 / 14 / 22 |
| Loops, sector graph (links − sectors + 1) | 1 / 2 / 5 (80 %) | 0 / 2 / 4 (65 %) | 0 / 0 / 1 (45 %) |
| Pressure-plate faces | 1 / 4 / 18 (86 %) | 0 / 1 / 12 (57 %) | 0 / 4 / 14 (59 %) |
| Secret faces | — (0 %) | 0 / 1 / 6 (62 %) | 0 / 1 / 4 (61 %) |
| Trap events (`DamagePlayer` / `CastSpell` on a bound face) | 0 / 0 / 4 (50 %) | 0 / 0 / 1 (30 %) | 0 / 0 / 0 (25 %) |
| Local teleports | 0 / 0 / 2 (43 %) | 0 / 0 / 0 (15 %) | 0 / 0 / 0 (7 %) |
| Door or lever events (`SetDoorState`) | 5 / 14 / 24 (93 %) | 2 / 5 / 10 (87 %) | 1 / 4 / 9 (77 %) |
| Summon events | 34 % of maps | 0 % | 5 % |
| Named or unique actors (bosses) | 30 % of maps | 17 % | 16 % |
| Clickable faces | 46 / 94 / 141 | 47 / 106 / 174 | 24 / 94 / 161 |
| Height range (units) | 1,020 / 1,720 / 2,590 | 1,050 / 1,800 / 2,860 | 1,140 / 1,870 / 2,860 |

Of maps with 8 or more sectors, **29 % are trees with no loop**: linear or branching with dead ends. The median
dungeon has 1–2 loops, usually a ring around a central hall or two routes between levels. Large maps have 5–38.

### 3.3 Space and shape rules

All measured; from `ROOM_SHAPES_MM678.md`, `hesper_dressing_study`, DUNGEON_PLAYBOOK.
- **Rooms.** A typical room is 0.5–1.3 M units² (about 1,800–2,000 × 1,300–1,400). A hall is about 3,200–3,700 × 2,100–2,300; great halls run 2,400–4,600 long. Corridors are 256–528 wide.
- **Ceilings.** 256–328 up to 1 M units², 464–592 for mid rooms, 1,088 for halls of 8 M or more. Hesper sets a floor of 384: the party's eye is at 160.
- **Non-orthogonal rooms.** MM6 42 %, MM7 51 %, MM8 61 %. Rooms with a 64+ height range: 48 / 71 / 74 %. Sloped or vaulted ceiling area: 31 / 46 / 56 %. A first Hesper set of square boxes (8 % non-orthogonal) was rejected: "basically every dungeon is squares and rectangles".
- **Dressing.** 36–74 % of sectors have no decoration. A dressed room has about 3–4 props near the walls, and 81–91 % of BLV decorations are lights. The real dressing is the BLV geometry.
- **Palette.** One wall texture covers 45–87 % of walls, plus 2–3 accents and 1–2 floors: about 12 keys.
- **Set pieces seen in the canon.** A 16-sided stepped round hall (`6t3`), chamfered tower rooms (`cd3`), an oval room with curved step banks (`t01`), ramps round pits (MM8 `d12`, `d22`), lifts and stateful puzzles (Lincoln, Control Center), 7 levels in a small footprint (Temple of Baa), a town underground (Stone City).
- **Interaction density.** 50–300 clickable faces, 10–40 door switches, a few plates, 3–7 chests (10–15 in the richest), and boss rooms in roughly a fifth of maps.

### 3.4 What OpenYAMM supports now

| Feature | Status | Doc |
| --- | --- | --- |
| Linear doors, lifts, platforms (BLV mechanisms) | Runtime full; the new-map compiler writes linear movers | `level_generation/GAMEPLAY_AND_SCRIPTING.md`, `PIPELINE_STATUS.md` |
| Rotating movers (hinged doors, levers, pendulum and swinging traps, spinners, trapdoors) and climbable ladders | Done 2026-10-30, opt-in scene `mover` / `ladders` | `devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md` |
| Destructible walls, boards, props | Done: BLV `destructibles`, hp, effect, events, saved, `evt.DamageDestructible`; ODM has `OutdoorDestructible` | `devdocs/INDOOR_DESTRUCTIBLES.md` |
| Pulsing lights | Done: sine intensity/radius, `evt.SetLight` | `devdocs/INDOOR_PULSING_LIGHTS.md` |
| Placed ambient sounds | Done for BLV (radius, loop, day/night, tied to a sprite); **none for ODM** | `devdocs/AMBIENT_SOUNDS.md` |
| In-engine cinematics, camera shake | Done 2026-11-06: `<stem>.cinematics.yml`, `evt.PlayCinematic`, `evt.CameraShake`, any world | `devdocs/mm9_rework/MM9_CUTSCENES.md` |
| Actor scripting (boss phases, timers, summons, wards) | Done: per-actor Lua over native AI | `devdocs/ACTOR_SCRIPTING_INVESTIGATION.md` |
| Monster modifiers (blink, charge, frenzy, kites, true aim …) | Done, `worlds/<w>/modifiers.yml` | `devdocs/MONSTER_MODIFIERS.md` |
| Energy shields, faction relations | Done, `shields.yml`, `relations.yml` | `devdocs/ENERGY_SHIELDS_AND_RELATIONS.md` |
| Animated decorations (chest lids, bells, banners, whole-model clips) | Done 2026-11-10, indoor and outdoor | `devdocs/ANIMATED_DECORATIONS.md` |
| Indoor baked lightmaps | Done, opt-in `<map>.lighting` | `devdocs/INDOOR_BAKED_LIGHTING.md` |
| Outdoor baked lighting | All 42 ODMs; re-bake after decoration changes (`tools/lighting/stale_bakes.py`) | `tools/lighting/baked_outdoors/README.md` |
| Open sky, fog and glass in BLVs | Done, opt-in (`sky: {mode: open}`, `fog`, `translucent_faces`) | `devdocs/INDOOR_OPEN_SKY.md`, `INDOOR_FOG.md`, `INDOOR_TRANSLUCENT_FACES.md` |
| Traps, plates, secret faces, teleports | Face flags (PressurePlate, TriggerByMonster/Object, IsSecret, Lava, Fluid); effects in Lua; `evt.MoveToMap` for teleports | `GAMEPLAY_AND_SCRIPTING.md` |
| Surface materials (relief, metal, glass, glowing windows) | Done for BLV/BModel faces; New Sorpigal fully produced | `devdocs/SURFACE_MATERIALS_PLAN.md` |
| Walkability audit (risers ≤32, monster paths) | `level_generation/projects/hesper_stage/check_walkability.py` | `design/kreegan_world/DUNGEON_PLAYBOOK.md` §5 |

**Engine limits to design around** (DUNGEON_PLAYBOOK §2):
- At most 4 static lights per draw point.
- Monsters climb at most 50 and path over steps of at most 40. Risers of 32 or less; deliberate drops of 128 or more.
- Face texture names are 10 bytes at most.
- No back-to-back walls (z-fighting).
- About 20 decorations per sector.
- A view should cross at most 3–4 portals.

## 4. Ground, sky and weather: what exists and what Xeen needs

### 4.1 Ground

**The terrain is drawn only from ground materials.**
- Each world's `terrain_materials/world.yml` maps tile families to library materials, and `tools/terrain_materials.py weights` writes the per-map weights.
- Tile ids still carry the flags: water 0x2, burn 0x1, shore 0x100.
- A world that is not mm6/mm7 reads the MM8 tile table (`TerrainTileData.cpp`). That is the only table with lava (`lavtyl`, burn + liquid), tar, red rock, dark stone, hardpan and dunes. It has **no snow tile**.
- A Xeen world can probably map MM8 families to any material, e.g. `gstyl` → `snow`, through `world.yml`. **Verify this before relying on it.**

| Family | Engine library material | Native maps | Grass / plants (MEADOW) |
| --- | --- | --- | --- |
| Grass | `grass_meadow` + `grass_patchy` | 22 | yes: `meadow`, `coastal_grass`, `woodland_grass` |
| Dirt / soil / stony | `dirt_cracked`, `soil`, `soil_stony` | most | edge tufts |
| Sand dunes / flat | `sand_ripples`, `sand_flat`, `sand` (beach) | 11 | no |
| Snow | `snow` | 8 | no (no snow plant family) |
| Swamp | `swamp` (moss with standing pools) | 4 | `marsh_reed` |
| Volcanic | `rock_ground`, `gravel_volcanic` | 6 | no |
| Badlands / hardpan | `dirt_cracked`, `mud_cracked`, `ground_crust` | 6 | `dry_tuft`, `dead_tuft` |
| Rock | `rock_layered`, `rock_red`, `rock_cliff` (all slopes) | 3 + all | no |
| Roads | `road_pebbles`, `road_flagstone` | 34 | — |
| Liquids (procedural) | water (per world), `sewage_mm6`, `slime_water_mm7`, `lava` (self-lit crust), `tar` | — | — |
| Hesper-only (staged, not in assets_dev) | `ceramic_plating`, `creep_resin` (emissive), `glass_obsidian`, `slag_crust`, `slag_molten` (emissive) | — | — |

Material options: two blended layers plus a cliff layer, macro tint, a variant sample, specular, `wet_sheen`,
`pools`, and per-map `shade`. `emissive {color, threshold}` exists, used only by Hesper. The budget is 8 layers per map.

### 4.2 Sky and weather

Source: `assets_dev/engine/rendering/sky/sky.yml`.
- **Presets:** `clear`, `fair`, `cloudy`, `overcast`, `rain`, `storm`, `winter_overcast`, `ember`, `plane_fire`, `plane_air`, `always_dark`, `night_stars`, `underwater`, plus 25 `legacy_*` presets from the painted skies. The legacy set includes **`legacy_cloudsabove`, `legacy_skycity01`**, `legacy_stormclds` and `legacy_sunsetclouds`.
- **Themes (15)** recolour any preset: `volcanic`, `ashen`, `necrotic`, `haunted`, `gloomy`, `otherworldly`, `frozen`, `arid`, `tropical` …
- **Preset schema:** time-of-day keyframes, up to 2 cloud layers, `horizon_ring`, a moon texture whose alpha can make a broken moon, `orbit_ring` with lights, and `below_horizon: sky` (open sky beneath, as on the Plane of Air).
- **Weather** (`weather.yml`): rain, snow and ash (ash is opt-in per map); wind, lightning, wet surfaces; deterministic per (map, day).

### 4.3 Xeen needs against what exists

| Xeen need | Exists | Missing / to build |
| --- | --- | --- |
| Clouds side: sky islands / cloud world | `no_terrain` ODM (Plane of Air: BModel islands only); `plane_air` + `below_horizon: sky`; `legacy_cloudsabove`, `legacy_skycity01` | No walkable cloud ground material, no cloud "liquid" or fall-into-void rule; OY-392 open bug on `elema` arrival. Alternative: an open-sky BLV (MM9's outdoor route) |
| Lava fields | `lavtyl` + lava liquid with crust, Burn damage outdoors and indoors, `gravel_volcanic`, `plane_fire`, `volcanic`/`ashen` themes, ash fall | Ember flakes (proposed only); no harmful-liquid key besides the burn flag |
| Crystal | `glowing`/`glass`/polished-stone surface classes; Hesper `glass_obsidian` | Crystal ground material, emissive crystal decoration models |
| Ancient / sci-fi tech (Xeen's Ancients, the Sheltem ship) | Hesper's 12 style kits, emissive materials, energy shields, modifiers, MM6 Control Center / MM7 Lincoln BLV references | A Xeen tech kit (own textures through `textures_x4` style generation) |
| Darkside twilight | `always_dark`, `night_stars`, themes `otherworldly`/`gloomy`/`necrotic`, keyframed skies | A permanent-dusk preset (data only); no aurora layer; `ambient_tint` is not applied to world light |
| Desert, snow, swamp, forest | Full materials, themes, rain/snow, swamp pools | Snow and desert have no plant families |
| Towers, pyramids, castles | BModels, open-sky BLVs, rotating movers, ladders | Kits per landmark; pyramid sandstone through surface materials |
| Outdoor ambient sound (waterfalls, wind, machines) | BLV only | ODM ambient sounds |

## 5. Lessons from this repo's from-scratch and converted maps

### 5.1 Verdicts

Only verdicts recorded from the driver (user) are counted. Agent or integrator sign-offs are marked as such.

| Project | Kind | Verdict | What was liked / disliked | Source |
| --- | --- | --- | --- | --- |
| Brackenford v1 (`lg01.odm`) | New MM8-style town | **Rejected** despite a full functional matrix | Doors 2× native (256 × 512), crate-texture windows, boat doors, chimneys, props on roads | `level_generation/VISUAL_CALIBRATION.md` |
| Brackenford facade → density → sketch | Revisions | Kit accepted, then "wide plot spacing" rejected; then the parallel rectangular grid rejected (the driver drew a sketch) | House gap 1,866 → 832 (Ravenshore 594–608); unequal loops, diagonals, raised manor | `DENSITY_REVISION.md`, `SKETCH_REVISION.md`, `SKETCH_LAYOUT_CALIBRATION.md` |
| Brackenford frontage revision | Revision | **Accepted** | Doors close to shared streets (median 688 → 371 from road cells), no spur per door, 0 tile-corner mismatches (was 3,258), filled court edges | `OUTDOOR_CALIBRATION.md`, `FRONTAGE_REVISION.md` |
| Brackenford wilderness / landscape / exits / roads | Revisions | Accepted step by step | 14 → 73 hostiles in 11 areas; pond; cave in a cleft; bridge 64+ above terrain; soil patches; decorations 564 → 1,166; roads continue past exits; no roads to caves or camps | `WILDERNESS_REVISION.md`, `LANDSCAPE_REVISION.md`, `ROAD_PURPOSE_REVISION.md` |
| Greywatch Vault (`lg02.blv`) | New BLV | No driver rejection recorded | Agent-found: flat cave facade, lift trigger, light levels | `projects/brackenford_greywatch/` |
| Castleview–Kalindra (MM5 region) | New ODM, environment only | Milestones signed off by the agent's goal process; the driver gave scope and silhouette input | 46,814 model triangles, 3.3× Ravenshore's, with 10.7 % tiny triangles; later trimmed | `projects/mm5_castleview_kalindra/COMPLETION.md`, `GEOMETRY_COST_AUDIT.md` |
| Hesper out1–out4 | New sci-fi ODMs | User feedback in rounds; playthrough pending | Village "nicer than the salvage", then "Harmondale-sized … bigger, against cliffs, more kinds of house"; out2 "too empty" → about 470 dressing pieces by ground type; out4 "almost all flat, feels wrong" → relief 32–5,920; Meshy houses replaced by 40–120-face BModels "in the manner of MM6–8"; music "too idyllic" | `projects/hesper_out1,2,4/README.md` |
| Hesper D0–D16 | New BLVs | User play found faults | "Every dungeon is squares and rectangles" (8 % non-orthogonal); monsters stuck on 64 steps and trenches; empty big rooms, low ceilings, invisible lights, wall-painted valves | `design/kreegan_world/DUNGEON_PLAYBOOK.md` §7 |
| New Sorpigal geometry pilot | Detail on existing BModels | In progress | Borrowed granite trim "looked pasted on"; 12-unit recesses invisible on dark rubble; "looks the same as the original" counts as a failure; silhouette beats relief; lighting file must not grow | `projects/mm6_sorpigal_geometry_pilot/PLAYBOOK.md` |
| MM9 rework (45 maps) | Converted, not invented | ODM route **rejected** for MM9 outdoors (terrain resampling broke tunnels); BLV + open sky chosen | Density "never overcrowded"; Tomb at 5× density cut to 2×; play-test faults (doorway faces in wrong rooms, cracks) | `devdocs/mm9_rework/README.md`, `BALANCE_PLAN.md`, `mm9r_common/DUNGEON_PLAYBOOK.md` |
| LoMM maps | Survey only | No choice yet | FPS-wide rooms with half the detail density of MM6–8; monster density must rise | `devdocs/lomm/README.md` |

### 5.2 Pitfalls that recur

1. **Scale before quantity.** Door, window and texel scale were wrong before anything else. Calibrate one house against a native module before placing a town.
2. **Numbers are not composition.** Correct spacing on a rectangular grid still failed. Sketch the road graph and frontage first.
3. **Global totals hide holes.** More trees in a remote grove do not fix an empty town-side meadow. Check local heatmaps and the player's route views.
4. **Flat reads wrong.** The Hesper Crown and early terrain were too level. MM maps use height ranges of about 2,200–8,000 (median about 4,000) with terraces, shoulders and screens.
5. **Empty is a choice.** Every open patch needs a written purpose; otherwise the driver calls it "too empty".
6. **Roads have purposes.** None to caves, camps or treasure.
7. **Monster pathing.** Steps over 32 strand monsters; run the walkability audit.
8. **Geometry cost.** Keep model triangles near Ravenshore's 14k per ODM. Micro-detail (ropes, melon patches) cost the most and showed the least.
9. **Agent self-acceptance is not acceptance.** The driver rejected a fully tested map on looks. Verify fixes at the reported poses.

### 5.3 Realistic production route and effort today

**New ODM.** Reference route: Brackenford for MM-art worlds; Hesper out1 for new-art worlds.
1. Read `OUTDOOR_CALIBRATION.md` and `VISUAL_CALIBRATION.md`. Pick a district and biome from `catalogues/outdoor_decorations/`.
2. Build a small building kit at native scale (128 × 256 doors, 1 texel per unit; `brackenford_house_kit.py`, `hesper_out1/houses.py`).
3. Plan the terrain, road graph and frontage in data on the 128² grid.
4. Author in Blender (MCP) or with headless scripts. Build with `openyamm-editor --headless-build-map` (`build_brackenford.py` / `hesper_out1/build_out1.py`).
5. Run `tools/terrain_materials.py weights`, make the minimap (`minimaps/README.md`), and bake (`tools/lighting/`).
6. One static readback, then screenshot tours (`run_game.sh --isolated`, tour YAML).
7. Effort:
   - Brackenford took about 1 day to build and about 1–2 days for **9 driver rounds**: scale → density → composition → frontage/tiles → wilderness → landscape → exits → road purpose.
   - With the calibrations now written, budget 1–2 days and 3–5 rounds per map.
   - Decoration models are 3D now (sprites retired). A new world either reuses the engine `mm6/7/8_deco_*` models or makes its own through the Meshy/Codex prop route, which is the larger cost.

**New BLV.** Reference route: Hesper D0–D16.
1. Plan the room graph and state graph in `make_dungeon_plans.py`.
2. Author headless with `hesper_stage/blv_kit.py` + `blv_build.py` (or `build/tools/mm9_compile_indoor_source`).
3. Write the Lua.
4. Run `check_walkability.py`, a headless scenario and screenshot tours.
5. Effort: Hesper built 16 dungeons, a hub and 4 ODMs in about 6 days (2026-10-19 → 10-25) across parallel sessions with an integrator. That is roughly 0.5–1 day per dungeon once the kit and style textures exist, plus user play-fix rounds.

**Open-sky BLV as an "outdoor"** (MM9 route, `mm9r_common/outdoor_blv.py`). Use it where a map needs overhangs, tunnels, floating islands or vertical stacking the heightfield cannot hold. Candidates: Xeen's Castle of Clouds, Sky Road and Tower interiors. On MM9 it cost less: 30k vs 72.6k triangles, GPU p95 0.88 vs 2.34 ms. Open-sky BLVs take terrain materials, weather and the meadow (`devdocs/INDOOR_OPEN_SKY.md`); check what else a map needs before choosing per map.

## 6. "Not bland" checklist with numeric targets

Targets are the measured MM6–MM8 interquartile ranges, adjusted by the driver's verdicts. Treat them as review
triggers: a value outside the range needs a written reason.

### 6.1 Every outdoor map

| Check | Target |
| --- | --- |
| Obelisk | exactly 1 |
| Distinct interaction-device kinds (fountain, well, shrine, pedestal, barrel, cauldron, fire, sign, tree …) | ≥ 4, and one permanent-effect device (stat fountain or shrine) per map |
| Unique POIs (merged at 400) | 25–55 (sparse special maps ≥ 10) |
| POI nearest-neighbour median | 1,300–2,600 units; no walked route longer than ~6,000 (8 s run) without a POI, fight, landmark view or set piece |
| Dungeon entrances | 3–6 (city 4–11) |
| Outdoor chests | 4–10, each with a reason: a guard, a hidden spot or a camp |
| Loose items | 10–50 |
| Spawn markers / hostiles at load | 45–75 markers / 110–150 hostiles (MM6-crowded style 160–260); 3 families per map (A/B/C) |
| Encounter areas | 8–15 named areas of unequal size; group-centre NN 2,600–3,800; tight packs (marker NN ≈ 250–400) and loose patrols both present; ≥ 3 attractive quiet places |
| Arrival → first fight | 2,000–6,000 (no fight inside the town buffer) |
| Roads | 1–4 % of land cells; town, gates and exits only; continue ≥ 8,000 past each travel prompt |
| Relief | height range ≥ 2,500 (mountain maps 5,000–8,000); terraces and shoulders screen at least one reveal per quadrant |
| Decoration groups | tree, low-plant, rock and prop layers counted separately; every open patch > 2,048 across has a written purpose |
| Activity layer | ≥ 1 fire or smoke source per settlement or camp; signposts at every exit fork (3–9) |
| Bridges and water | bridge decks ≥ 64 above terrain along the whole span; ponds as native water cells with a dirt collar |
| Model triangles | near Ravenshore's 14k per ODM (Castleview's 47k was judged costly and trimmed); tiny triangles < 1 % (Ravenshore 0.38 %) |

### 6.2 By map type

| Type | Water | Deco / block | POIs | Services / residences | Devices beyond the common set | Feel |
| --- | --- | --- | --- | --- | --- | --- |
| Town hub | 10–40 % | 4–7 | 35–55 | 13–20 / 20–55 (house gap 450–950, 13 forms per 44 homes) | Barrels or trash in work yards (10–25), 1–2 buff pedestals, 1 stat challenge, wells by squares | Opposing frontages, a named square, gardens at court edges, town-side meadow not empty |
| Wilderness | 0–15 % | 1.5–3 | 20–30 | 0–9 / 5–15 (hamlet or outpost) | Camps with fire and supplies, sword-stone or standing-stone set piece, 1–2 shrines | Large quiet stretches, but each with a view; packs in hollows and woods |
| Desert | 5–35 % | 2–4 (dry plants, rocks, bones) | 15–25 | 2–9 / 6–20 | Oasis fountain, bone fields, ruin chests | 7–30 % of land farther than 2,048 from any sprite, by design; palms only at water |
| Snow / high country | 0–10 % | 1.5–3 | 25–35 | 6–18 / 13–30 | Wells or fountains 5–8 (warmth, cure), caves 2–6 | Snow trees on shelves, dirt-side vegetation in valleys (Frozen Highlands mix) |
| Swamp | 25–40 % | 2–3.5 | 20–30 | 5–15 / 10–25 | Swamp pools, food trees, a haunted shrine | Wet/dry pockets; no aquatic carpet |
| Island | 50–90 % | 4–12 | 15–55 | 6–17 / 6–22 | Docks, a ship or wreck chest, buoys, smoke | Dense planting on small land; boat arrivals in town |
| Cursed / necropolis | 5–20 % | 2–4.5 (bare trees, rune posts, remains) | 20–30 | 4–13 / 13–33 | Graves with events, cauldrons, rune circles | One repeated ritual motif, not every spooky prop |
| Plane / special (Clouds, Darkside wastes, lava) | any | 0–3 (one dominant motif, e.g. 428 path markers) | 3–10 | 0 / few | Set pieces carry the map | Terrain or architecture as the main layer |

### 6.3 Every dungeon

| Check | Target (MM7/MM8 scale; MM6-scale "big crowded" maps double the monster counts) |
| --- | --- |
| Size class | S: 10–20 sectors, 20–35 M units²; M: 20–35 sectors, 40–70 M; L: 35–55 sectors, 70–110 M |
| Floor levels | 2–4 (1 only for a cave); overlaps small |
| Loops | ≥ 1 for M and L (median 1–2); at most a third of maps purely linear |
| Monsters | S 20–35, M 35–65, L 70–120; about 2–2.5 per sector, never evenly spread |
| Chests | 3–7 (S 2–4) |
| Doors and switch events | M 8–16 doors, 5–14 door events |
| Secrets | MM7/MM8 style: 1–6 secret faces per M dungeon, each with a clue and a safe return |
| Plates / traps | 1–15 plates; traps on 1 map in 3 (1–4 trap events) |
| Local teleports | optional; 1 map in 5 |
| Boss | named or unique actor in about 1 dungeon in 5 (MM6 1 in 3); not on the arrival trigger |
| Set pieces | 1 signature room (round, octagonal or stepped hall) + 1–2 scripted moments (power on, shutter, cave-in) |
| Shape | ≥ 40 % non-orthogonal rooms; 25 %+ sloped or vaulted ceilings; risers ≤ 32; ceilings ≥ 384 |
| Dressing | 1 main wall texture (45–85 %), ≤ 12 keys; 3–4 props per dressed room; lights with visible sources; ≤ 4 lights per floor point |
| Clickable faces | 50–170 |

### 6.4 Review gates

1. Same-scale plan with POIs, encounter areas and quiet areas marked. Measure POI NN and group NN with `map_craft/measure_outdoor.py` once the map is mounted.
2. Player-height route views: arrival → first POI, town → country, country → special site, return.
3. Local scenery heatmaps (`level_generation/scripts/measure_landscape.py`) rather than totals.
4. Walkability audit and Wizard Eye view for every BLV.
5. The driver's eye decides. Expect 3–5 review rounds per new map and plan them into the schedule.
