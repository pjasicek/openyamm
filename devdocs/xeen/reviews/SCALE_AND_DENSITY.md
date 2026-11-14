# Xeen review: scale and density

Review, 2026-11-13. Checks the numbers in [WORLD_DESIGN.md](../WORLD_DESIGN.md), [MAPS.md](../MAPS.md) and
[MONSTERS_AND_ITEMS.md](../MONSTERS_AND_ITEMS.md) against the shipped MM7 and MM8 maps, and the six built test maps
(X1, XD-01 to XD-05 in `output/studio_play/xeen_root`) against the same maps. Nothing in the design files was
edited; each finding ends with proposed text.

## Method and sources

- **Dungeons**: `oymap metrics` on every MM7 and MM8 BLV with 3+ sectors (60 + 44) and on XD-01 to XD-05. Monsters
  are estimated as every monster spawn point times the mean of its map_stats slot range, plus placed actors. Chests
  are bound `OpenChest` events. Script `output/xeen_review/scale/dungeons.py`, results in `dungeons.json` and
  `dungeons.txt`. Room sizes from `openyamm-studio/calibration/scale_bands.py`.
- **Outdoor heatmaps**: `output/xeen_review/scale/heatmaps.py` grids each map into 16 × 16 cells of 4,096 units and
  counts seven layers per cell: expected hostiles, decorations, building footprint, bound events, chests, road tiles
  and water tiles. Statistics use the central 12 × 12 cells, where the party walks. The maps are 7out01–06, 7out13,
  out01–out08 and X1 as built. One image per map is in `heat_<map>.png`, one image per layer with all 16 maps on a
  shared colour scale is in `layer_<layer>.png`, and the numbers are in `stats.json` and `heat_table.txt`. Region
  shapes come from `clusters.py` (`clusters.txt`).
- The figures already in `research/MM678_CALIBRATION.md` and `research/MAP_CRAFT_CALIBRATION.md` are reused where they
  agree with these measurements. Where the two disagree, this review's own measurement is given.
- Estimates differ a little from MM678_CALIBRATION's (for example Harmondale: 254 here, 288 there) because placed
  townsfolk are filtered by name. The comparisons below use one method throughout.
- Play time was not measured; floor area and sector counts stand in for the length of a run.

## Summary

| # | Finding | Shipped | Design / built | Severity |
| --- | --- | --- | --- | --- |
| 1 | "S" dungeons are specified and built at M size | S median 8–9 sectors, 12–17 M units², 22–26 monsters | S band 10–20 sectors, 20–35 M; built "S" XD-03/05: 24–25 sectors, 29–44 M, 40 monsters | High |
| 2 | The dungeon class table is inconsistent and its L band is too low | L: 122–176 monsters | WORLD_DESIGN says L > 100; MONSTERS says L 70–120 | High |
| 3 | The dungeon count and class mix in WORLD_DESIGN do not match MAPS | — | WORLD_DESIGN: 54 (27/21/6); MAPS lists 59 BLVs (26 S / 27 M / 6 L) | High |
| 4 | The world's monster total is about 25 % above the stated 4,700 | MM7 ≈ 4,470, MM8 ≈ 4,130 | about 5,900 from the built sizes | Medium |
| 5 | Outdoor packs are too big per marker, and camps are scattered as even dots | 1–3 per marker (slot 1 2–5 on start maps); largest encounter region 8–40 cells | X1: 3–5 / 2–4 / 2–5; 10 regions, largest 5 cells, 6.4 hostiles per occupied cell | High |
| 6 | X1 carries 7 dungeon entrances and is the densest map measured | Start maps 2–4 dungeons; MM7/MM8 maps 1–6 | X1: 6 + FD-05; 157 events, 1,183 decorations | Medium |
| 7 | The sheets name 5–11 outdoor POIs; shipped maps hold 20–55 | non-town maps 20–31 POIs | D5 6, D6 5, X7 7, D4 7 (named items) | High for D4–D6 and X7 |
| 8 | One hostile band (110–150) is applied to every map type | start 40–168, hub 216–254, wilderness 142–185 | 110–150 for all 13 | Medium |
| 9 | Three Cloudside maps in a row open with almost no services | MM7 hop 2–3 maps: temple on 6 of 7, training on 4 of 7 | X3, X4 (Asp), X5: 0–1 services until their quests | Medium |
| 10 | Dungeons are door-heavy | M doors p75: 16 (MM7), 24 (MM8) | XD-02 34, XD-04 29, XD-03 22 | Low |
| 11 | Small inconsistencies (adjacency, treasure 0, chests in the start pocket, finale counts) | — | see §11 | Low |

What is right and should not change: 13 surface maps (MM7 13, MM8 9); map-edge travel of 5 days; 3 families per
map; lock/trap 0 → 20; the size of the built rooms (upper-quarter room area at the shipped median, percentile 51–65;
ceilings at percentile 37–82); chests per built dungeon (4–6 against an MM7 M median of 4); monsters per sector in
the built dungeons (1.2–1.7 against MM7's 1.75); roads on X1 (1.6 % of land against 0.7–5.6 %); X1's town
concentration (top tenth of cells holds 84 % of the building area, shipped 54–99 %).

## 1. "S" dungeons are specified and built at M size

**Shipped** (oymap metrics, p25 / median / p75, classed by estimated monsters):

| | Sectors | Floor (M units²) | Monsters | Chests | Doors |
| --- | --- | --- | --- | --- | --- |
| MM7 S (29 maps) | 6 / 8 / 18 | 6 / 12 / 19 | 10 / 22 / 30 | 0 / 2 / 5 | 4 / 6 / 10 |
| MM7 M (27) | 24 / 35 / 47 | 38 / 86 / 137 | 52 / 56 / 68 | 3 / 4 / 7 | 6 / 11 / 16 |
| MM7 L (4) | 71 / 71 / 72 | 132 / 180 / 222 | 150 / 169 / 176 | 0 / 3 / 7 | 1 / 8 / 19 |
| MM8 S (23) | 5 / 9 / 13 | 11 / 17 / 20 | 16 / 26 / 30 | 0 / 1 / 4 | 0 / 4 / 6 |
| MM8 M (19) | 16 / 23 / 31 | 25 / 32 / 60 | 45 / 54 / 76 | 0 / 4 / 10 | 5 / 11 / 24 |
| MM8 L (2) | 17 / 22 / 27 | 35 / 46 / 57 | 122 / 129 / 136 | 2 / 4 / 5 | 28 / 56 / 84 |

**Built:**

| Code | Design class | Sectors | Floor | Monsters | Chests | Doors | Loops | Reads as |
| --- | --- | --: | --: | --: | --: | --: | --: | --- |
| XD-01 Joe's Warehouse | S | 26 | 21.7 | 32 | 5 | 18 | 1 | S by monsters, M by sectors |
| XD-02 Red Dwarf Mines | M | 43 | 42.0 | 71 | 6 | 34 | 2 | M |
| XD-03 Deep Mine | S | 24 | 28.9 | 40 | 5 | 22 | 1 | **M** |
| XD-04 Witch Tower | M | 33 | 39.2 | 54 | 4 | 29 | 6 | M |
| XD-05 Orc Caves | S | 25 | 44.4 | 40 | 4 | 5 | 7 | **M** |

Comparators of the same role: MM7 White Cliff Cave (25 sectors, 66 M, 34 monsters), Temple of the Moon (30, 37, 64),
the MM7 Red Dwarf Mines (53, 100, 55), Zokarr's Tomb (12, 7, 18), the Wine Cellar (10, 7, 23).

The cause is in the calibration, not in the builds. MAP_CRAFT §6.3 sets S at 10–20 sectors and 20–35 M units². That
band came from the "canonical dungeons" survey, which leaves out the small ones. Against all shipped BLVs it sits at
the S **p75 and above**: the MM7 S median is 8 sectors and 12 M, the MM8 median 9 and 17. Every built "S" Xeen
dungeon has 24–26 sectors, the shipped **M** p25. The world therefore has almost no short dungeons. Shipped worlds
have 45–52 % of dungeons under 40 monsters and 41–45 % under 20 M units². The built Act I set has 1 of 5 under 40
monsters and none under 20 M.

**Change.** In WORLD_DESIGN §6, replace the first paragraph with:

> Size classes, measured on all shipped MM7/MM8 BLVs (`reviews/SCALE_AND_DENSITY.md` §1):
> **S** 6–15 sectors, 7–20 M units², 15–30 monsters, 0–3 chests, 3–8 doors: a 10–20 minute visit (the Wine Cellar,
> Zokarr's Tomb, a Barrow). **M** 20–45 sectors, 30–90 M units², 45–75 monsters, 3–7 chests, 6–16 doors (the Temple of
> the Moon, White Cliff Cave). **L** 50–75 sectors, 120–200 M units², 120–180 monsters (Castle Harmondale, the Nighon
> Tunnels). An S brief that grows past 15 sectors is cut or re-classed as M; it does not stay "S".

Also: XD-03 and XD-05 are re-classed M in MAPS.md (their built size), and XD-01 is kept as the upper-bound S. New S
briefs (XD-13, XD-21 to XD-27, DD-04, the DD-10 and DD-11 pockets, DD-13, DD-16, DD-21 to DD-24, DD-26, FD-02)
carry the line "S: at most 15 sectors and 20 M units²" in their L1 brief.

## 2. The dungeon class table is inconsistent and its L band is too low

WORLD_DESIGN §6 defines L as more than 100 monsters, and MONSTERS_AND_ITEMS §3 sets L at 70–120. The shipped L
dungeons hold 122–176 monsters (MM7 150 / 169 / 176, MM8 122–136), and MM7's have 71–72 sectors (MAP_CRAFT's
"35–55" is again below the shipped value). By the design's own definition, a 70–100 monster "L" is an M. The design
names six L set pieces (Darzog's Tower, Dragon Cave, Castle Xeen, Blackfang, Great Pyramid, Alamar), against MM7's
4 and MM8's 2. If all six are built to the shipped L size, they alone hold about 900 monsters.

**Change.** In MONSTERS_AND_ITEMS §3, change the Dungeons row to:

> | Dungeons | S 15–30, M 45–75, L 120–180; 1.5–2.5 per sector, uneven. At most four L set pieces at full L size; the other
> story fortresses are large M (70–100) | Measured MM7/MM8 bands, `reviews/SCALE_AND_DENSITY.md` §1–2 |

In MAPS.md, mark Castle Xeen, Castle Alamar, the Great Pyramid and Darzog's Tower as L. Make Castle Blackfang and the
Dragon Cave large M (70–100 monsters, 40–45 sectors). MM7's 4 L include one optional (the Maze). If the Dragon Cave
stays L, Darzog's Tower should become large M instead.

## 3. The dungeon count and class mix in WORLD_DESIGN do not match MAPS

The dungeon tables in MAPS.md, counted:

| | S | M | L | BLV files |
| --- | --: | --: | --: | --: |
| Cloudside XD (without the Shangri-La town and the arena) | 11 | 11 | 3 | 25 |
| Darkside DD (the DD-10 and DD-11 pockets as 3 each; without Bosco's Hall) | 14 | 12 | 3 | 29 |
| Finale FD-01 to FD-05 | 1 | 4 | 0 | 5 |
| **Total** | **26** | **27** | **6** | **59** |

WORLD_DESIGN §3.2 and §6 say 54 (27 / 21 / 6) and "about 55 % small". The MAPS totals line says "27 S, 21 M, 6 L".
The real list is 44 % S on paper, and about 20 % once finding 1 is taken into account. On top of these come 2 town
BLVs, the arena, 3 sky maps, 4 planes and P5, for **70 BLV files**. MM7 has 61 (15 of them Barrows of 5–11 sectors),
MM8 45.

At the built sizes the projected underground is about 3,000 M units² of floor (26 S × 32 + 27 M × 41 + 6 L × 180).
MM7's is 4,315 and MM8's 1,481, so the total area is in range. The problem is the mix: Xeen has no short dungeons.

**Change.** In WORLD_DESIGN §6, replace the table with the counted one above and add:

> Target mix: 30 S (half of all dungeons, at the S size of the class table), 24 M, 4 L, ≈ 58 BLVs. To get there, the
> following move from M to S: XD-13 Newcastle Keep stage 1, DD-04 Gremlin Court, XD-24 Nightshadow Crypt (kept S),
> DD-02 Ellinger's Tower (14–20 levels, a 4-floor tower of 12–15 sectors), DD-06 Southern Tower and XD-10 Cave of
> Illusion; FD-04 Dragon Tower and FD-05 Dungeon of Death become one optional dungeon.

Also correct the totals line in MAPS.md and the §3.2 row "Dungeons (BLV): about 52" in WORLD_DESIGN to "59 (+2 town
BLVs, arena)". In §6, change "Finale: 2 / 2 / 0 = 4" to "1 / 4 / 0 = 5", or drop FD-05 as proposed.

## 4. The world's monster total is about 25 % above the stated 4,700

MONSTERS §3 assumes 13 ODMs × 135 + 240 (sky) + 220 (planes) + 2,400 (dungeons) ≈ 4,700. With the measured sizes:

| Part | Basis | Monsters |
| --- | --- | --: |
| 13 ODMs | X1 as built 172; the design band's top 150 for the rest | 1,970 |
| Sky and planes | as designed | 460 |
| 26 S dungeons | built S mean 37 (XD-01, 03, 05) | 960 |
| 27 M dungeons | built M mean 62 (XD-02, 04) | 1,670 |
| 6 L | shipped L median 150 | 900 |
| **Total** | | **≈ 5,960** |

That is 1.33 × MM7 (4,470) and 1.44 × MM8 (4,130), with the experience that goes with it. With findings 1–3 applied
(30 S at 22, 24 M at 58, 4 L at 150, outdoor at the per-type bands of finding 8), the total is about 4,900. That
matches "two games' worth" without MM6's grind.

**Change.** In MONSTERS §3, change the Whole world row to:

> | Whole world | **≈ 4,900 monsters** on a first visit: outdoors ≈ 1,900 (per-type bands), sky and planes 460, dungeons
> ≈ 2,550 (30 S × 22, 24 M × 58, 4 L × 150) | MM7 ≈ 4,470, MM8 ≈ 4,130. Re-count after each act's builds; a built
> act over its share by more than 15 % is trimmed |

## 5. Outdoor packs are too big per marker, and camps are scattered as even dots

**Shipped** map_stats per-marker ranges on all 15 maps measured: 1–3 for every slot, except slot 1 at 2–5 on the
start and hub maps (7out01, 7out02, out01, out02, out05). From the heatmaps, the central 12 × 12 cells:

| | Cells with monsters | Regions (8-connected) | Largest region | Hostiles per occupied cell |
| --- | --: | --: | --: | --: |
| MM7 7out02–06, 7out13 | 21–45 | 3–7 | 8–31 | 2.4–5.6 (median 3.2) |
| MM8 out01–out08 | 31–58 | 2–8 | 13–40 | 2.7–5.0 (median 4.0) |
| **X1 as built** | 27 | **10** | **5** | **6.4** |

`layer_monsters.png` shows the difference. Shipped maps run encounter **areas**: bands and patches several cells long
(Harmondale's north-east band, Ravenshore's west, Murmurwoods' ring) with empty quarters between them. X1 has ten
separate lumps of 1–5 cells spaced almost evenly over the map. Each lump is a camp of 3–5 per marker, as large as
MM6's packs (the design text's "packs of 2–5").

This comes from MAPS' preamble and MONSTERS §3 ("packs of 2–5"). X1's second pass followed them: markers went from 59
to 40, group size from 2–4 to 3–5. The total is still in band (172), but the map reads as hops between fortified
dots.

**Change.** In MONSTERS §3, change the Surface ODM row to:

> | Surface ODM | 45–70 spawn markers at **1–3 per marker** (slot 1 may be 2–5 on start and hub maps, as MM7/MM8), plus placed
> camps; hostiles at load by map type (below). Monsters form 3–8 **encounter areas** of 6–30 cells of 4,096
> (a valley, a wood, a river bank) with markers 500–1,500 apart inside, and leave at least a third of the land cells
> without monsters in two or three large quiet quarters. No more than 3 areas of a single cell (camps, a lair) |
> Measured, `reviews/SCALE_AND_DENSITY.md` §5 |

For X1: set the slots to 2–5 / 1–3 / 1–3, go back to 55–60 markers, and merge the ten camps into four areas: the
northern hills' orc country, Toad Meadow, the dead forest and the orc outposts' road. That keeps the 140–170 total.

## 6. X1 carries 7 dungeon entrances and is the densest map measured

X1's sheet lists XD-01 to XD-06, and FD-05 (Dungeon of Death) is placed on X1 too: 7 dungeons. Shipped start maps
have 2 (Emerald Island), 3 (New Sorpigal) and 4 (Dagger Wound), and no shipped MM7/MM8 surface map has more than 6.
The sheet's own note says "2–3 entry dungeons".

The built X1 is also at the top of every content layer:

| | X1 | Shipped range (15 maps) |
| --- | --: | --- |
| Hostiles at load | 172 | 40–254 (start maps 40–135) |
| Bound events | 157 | 46–160 |
| Decorations | 1,183 | 141–1,847 (MM7 141–564) |
| Land cells with fewer than 3 decorations (central) | 23 | 17–112, median 57 |

X1 is twice as decorated as any MM7 map and has fewer quiet cells than every shipped land map except Murmurwoods.
X1 is not too sparse. Earlier "too empty" comments were about local gaps, not the total.

Act I as a whole (X1 + XD-01..05 ≈ 172 + 237 = 409 monsters) is in line with MM7's Emerald + Harmondale + their
dungeons, so the act is not over-filled. The issue is that one map carries both the start pocket and the hub role.

**Change.** In MAPS.md, X1 sheet:

- Move FD-05 Dungeon of Death to X6 (the desert's ruins), or merge it with FD-04 (finding 3).
- Change the Notes row to: "The safe pocket of calibration: complete services, three entry dungeons near the town
  (XD-01, XD-02, XD-05), two that need the next step (XD-03 by the mine cart, XD-04 by Valia's key) and one late
  return (XD-06). Six dungeons are the most any shipped map has; nothing more goes on X1. Decorations at most 800
  (MM8 town level); keep ≥ 40 central land cells with fewer than 3 decorations as open meadow."

## 7. The sheets name 5–11 outdoor POIs; shipped maps hold 20–55

Named items per sheet (Outdoor content + Town + Dungeons rows):

| Map | Content | Town items | Dungeons | Named total | Shipped analogue (POIs) |
| --- | --: | --: | --: | --: | --- |
| X1 | 11 | 5 | 6 | 22 | Harmondale 52, Dagger Wound 53 |
| X2 | 9 | 4 | 3 | 16 | Ravenshore 53, Erathia 57 |
| X3 | 8 | 2 | 4 | 14 | Mire 25, Tatalia 26 |
| X4 | 7 | 4 | 4 | 15 | Tularean 45, Alvar 38 |
| X5 | 9 | 3 | 5 | 17 | Frozen Highlands 36, Nighon 30 |
| X6 | 9 | 4 | 4 | 17 | Bracada 24, Ironsand 23 |
| X7 | 7 | 2 | 5 | 14 | Land of the Giants 8 (endgame), Garrote 21 |
| D1 | 10 | 4 | 6 | 20 | Ravenshore 53 |
| D2 | 7 | 4 | 5 | 16 | Murmurwoods 20, Avlee 39 |
| D3 | 7 | 3 | 3 | 13 | Bracada 24, Alvar 38 |
| D4 | 7 | 2 | 4 | 13 | Avlee 39, Regna 34 |
| D5 | 6 | 3 | 4 | 13 | Ironsand 23 |
| D6 | 5 | 3 | 5 | 13 | Shadowspire 31, Deyja 27 |

The checklist's 25–55 is in the MAPS preamble, but nothing in the sheets budgets the other 10–40 POIs (wells, camps,
signposts, graves, chests with a reason, stat challenges, barrels). The built X1 shows what then happens: the builder
filled the map with decorations and town houses (1,183 decorations, 157 events), not with devices out in the land.
The heat images show this: X1's events sit in the town (`heat_xeen_x1.png`, events), while Ravenshore, Alvar and
Shadowspire spread single-event cells over the whole map.

The maps most at risk of reading empty are **D4, D5, D6 and X7**: 13–14 named items, no full town at first visit,
and wilderness bands. They are also the maps where MAPS_CRAFT expects 20–31 POIs.

**Change.** Add a row to every sheet in MAPS.md, after "Outdoor content":

> | POI budget | named items N; add M generic devices to reach the type band: wells/fountains a, camps with fire b, graves or
> ruins with chests c, signposts at forks d, one stat challenge or buff pedestal; at most 6,000 of road or open land
> without a POI or fight |

with these figures (type band from MAP_CRAFT §6.2):

| Map | Type | POI target | Add |
| --- | --- | --: | --: |
| X1, X2, D1 | town hub | 40–50 | +20–30 |
| X4, D3 | town + wilderness | 30–40 | +15–25 |
| X3 | swamp | 25–30 | +11–16 |
| X5 | snow | 28–35 | +11–18 |
| X6, D5 | desert | 20–25 | +7–12 |
| D2 | forest | 22–30 | +6–14 |
| D4 | lake / island-like | 30–35 | +17–22 |
| X7, D6 | trap / cursed | 22–28 | +8–15 |

## 8. One hostile band (110–150) is applied to every map type

The MAPS preamble and MONSTERS §3 use "110–150 hostiles at load" for every surface map. The shipped maps vary by role
(estimates from the heatmaps, MM678_CALIBRATION in brackets):

| Role | Shipped | Design |
| --- | --- | --- |
| Start pocket | 7out01 40 (66), out01 135 (168) | X1 110–150; built 172 |
| Hub with town | 7out02 254 (288), out02 216 (261) | X2, D1 110–150 |
| Town + country, hop 2–3 | 7out03 111, 7out04 52, out03 122, out06 120 | X3, X4, D2, D3 |
| Wilderness | out04 153, out05 185, out07 181, out08 142 | X5, X6, D4, D5 |
| Trap / endgame | Land of the Giants 132, Nighon 172 | X7, D6 |

The shipped pattern: the start map is light, the hub is the heaviest (its country is wide and the town is buffered),
wilderness is heavier than town maps (130–185), and town maps of the middle are lighter (50–120).

**Change.** In MONSTERS §3, add below the table:

> Hostiles at load by map role: start pocket 90–140 (X1); hub 160–220 with none inside the town buffer (X2, D1);
> town maps of the middle 100–130 (X3, X4, D2, D3); wilderness 140–185 (X5, X6, D4, D5); trap and endgame 130–170,
> few and strong (X7, D6). Sky maps 60–100, planes 40–70 as above.

In the MAPS preamble, replace "110–150 hostiles at load" with "hostiles at load by map role (MONSTERS_AND_ITEMS §3)".

## 9. Three Cloudside maps in a row open with almost no services

The towns of X3 (Nightshadow, Newcastle), X4 (Asp; Castle Burlock is a castle BLV with an 8-residence village) and
X5 (Winterkill) start cursed or unbuilt. On first arrival, at party level 10–20:

| Map | Services before the town's quest |
| --- | --- |
| X3 | Moon Guild at night only |
| X4 | Castle Burlock's armoury, temple, training (Crusaders-only gate) |
| X5 | Mindmeld Guild only |

In MM7, the hop 2–3 maps have a temple on 6 of 7 (all but the Barrow Downs) and training on 4 of 7. Every MM8
map has a tavern. With these three maps in a row, the party must return to X2 or X1 for every heal and level-up
during Act II. That is the source's structure, but it was built on 1-square towns 2 steps apart, not on 5-day map
edges.

**Change.** In WORLD_DESIGN §5.1, add under the Cloudside table:

> Every cursed or unbuilt town has one working service at the edge from day one, outside the curse: X3 a
> tavern-and-temple at Ebenezer's camp, X4 Asp's Travel Pit (stables) and a roadside temple, X5 Kai Wu's monastery
> as temple and training. Castle Burlock's village services do not need the Crusaders title.

## 10. Dungeons are door-heavy

Built doors: XD-02 34, XD-04 29, XD-03 22, XD-01 18, XD-05 5. Shipped M p25 / median / p75: 6 / 11 / 16 (MM7),
5 / 11 / 24 (MM8). Shipped S median: 4–6. Four of five built dungeons are above the shipped M p75. The difference is
mostly gates and pens (XD-01's six pens, XD-02's cart gates), which is fine for set pieces but costs play time.

**Change.** In MAP_CRAFT's checklist reference in WORLD_DESIGN §6, add: "Doors: S 3–8, M 6–16, L up to 25; pens and
gates count."

## 11. Smaller consistency points

- **Adjacency.** The X3 sheet lists "X5 edge" as an arrival, but X5 and X3 do not touch in the §3.1 grid (X2 lies
  between them). The D1 sheet's Arrivals row omits D6, which the D6 sheet lists ("D1 (south, a long mountain road)").
  Fix the two rows.
- **The first hop by road is a +8 jump.** X1's roads lead to X3 (A 10–15) and X7 (40–55, trap); the hub X2 (6–10)
  is reached only by Nystor's boat. Shipped worlds put the hub one road hop away (Harmondale A 7, Ravenshore 10).
  Either give X1 a road edge to X2 (the river road) or set X3 to A 8–12.
- **Treasure on the start maps.** The design sets X1 Tres 1 (built map_stats 9130: 1). Every shipped start map is 0
  (Emerald, Dagger Wound) and the hubs 0–1. Proposed: X1 Tres 0, X2 and D1 Tres 1.
- **Outdoor chests in the start pocket.** X1 as built has 6, at the bottom of the 4–10 band. Shipped start maps hold
  7 (Emerald), 17–20 (Dagger Wound, New Sorpigal). Proposed in the X1 sheet: "8–12 outdoor chests, half of them in
  plain sight for a level-1 party."
- **Dungeons per map**, as counted from the sheets: X1 7, D1 6, D6 6 (with a DD-10 pocket), X5 5, X7 5, D2 5
  (7 with the pockets), the rest 3–4. Shipped: 1–6. Only X1 is over; the rest is in band.
- **Rooms.** The built room sizes are right: upper-quarter room area at the shipped percentile 51–65, the largest
  rooms at 34–76, ceilings at 37–82. Only doorway width is at the shipped minimum (256, percentile 9) in four of five
  maps; MM7's own median is also 256, so this is noted only.

## Files

- `output/xeen_review/scale/heatmaps.py`, `clusters.py`, `dungeons.py`: the measurement scripts (read-only on the
  repository; run from the repository root).
- `output/xeen_review/scale/heat_<map>.png`: seven layers per map. `layer_<layer>.png`: one layer, all 16 maps, shared
  colour scale (cream = none, dark red = the 95th percentile of non-empty cells; blue = water without content; the
  grey frame is the central 12 × 12).
- `output/xeen_review/scale/stats.json` (grids and statistics), `heat_table.txt`, `clusters.txt`, `dungeons.json`,
  `dungeons.txt`, `metrics/`.
