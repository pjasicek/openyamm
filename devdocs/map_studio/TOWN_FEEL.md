# Town feel: measured rules for outdoor towns

What makes an MM6-MM8 town feel like one, measured on thirteen shipped towns (2026-11-13) for a builder of a new
outdoor map. Each rule gives the shipped range (min..max over the towns, median in brackets) and where to look. The
user's list (Vertigo Meadows, 2026-11-13): not too symmetric; houses different yet of one or two styles; paths that
fit the houses and are not all straight lines and right angles; services where they make sense; monsters on guard
points, not spread evenly; enough props; a buff well or shrine somewhere; flat land or small hills.

House density, tree spacing, wild-land density and road and river ends at the map edge are measured by another
round: see [OUTDOOR_REBUILD_PROCEDURE.md](OUTDOOR_REBUILD_PROCEDURE.md). This file does not repeat them.

**Checker:** `python3 openyamm-studio/calibration/town_feel.py <map.odm> --world <w> [--assets <root>]
[--town x0,y0,x1,y1]` prints every figure below against its shipped range and flags those outside (`OUT`);
`--shipped` prints the thirteen towns, `--json` the raw figures. Run it before the user plays a new map, and
read the flags together with the pictures: a figure inside the range does not make a town feel right, a figure
outside it is a place to look.

**Towns measured** (in-game pictures: `output/studio_townfeel/shots/<map>/`, four oblique overviews `01-04` from
south, east, north and west, and nine street views `05-13` from three points of the town; noon, HUD off):
MM6 New Sorpigal (`oute3`), Free Haven (`outc2`), Castle Ironfist (`outd3`), Silver Cove (`outd1`); MM7 Harmondale
(`7out02`), Steadwick in Erathia (`7out03`), Tatalia (`7out13`, footprint given by hand: the automatic cluster splits
the town), Pierpont in the Tularean Forest (`7out04`); MM8 Ravenshore (`out02`), Alvar (`out03`), Shadowspire
(`out06`), Garrote Gorge (`out05`), Dagger Wound (`out01`). Bracada (`7out06`) has no town on the ground (three
houses round a stable below Celeste) and is left out of the ranges.

**How the town is found:** the house doors (`oymap things`, every `EnterHouse`) are clustered (single link, 4000
units); the cluster with the most services is the town, and the town is the land within 1536 of one of its doors.
House types come from `engine/data_tables/house_data.txt`, monsters from `monster_data.txt` and the spawn slots from
`map_stats.txt`, each with the map's world's own rows (`worlds/<w>/data_tables/`: Xeen's houses and monsters; until
2026-11-20 only the engine's were read, so a Xeen map's monster figures were wrong). Monsters are the scene's placed actors plus its spawn
points (type 3; as the game reads them: index 1-3 a group of slot M1-M3 sized by the mean of `map_stats.txt`'s dice,
4-12 one monster of a slot at a fixed tier; until 2026-11-14 the checker read 1-9 as dice groups); peasants, guards, defenders,
sergeants, apprentices and adventurers by name are civilians, everything else counts as a threat.


## 1. One or two house styles, many house shapes

The single strongest signal. A town is one family of wall and roof textures, with many different house models in it.

| figure | shipped | notes |
|---|---|---|
| share of houses in the main wall family | 0.39..1.0 (0.79) | MM7 and MM8: 0.78..1.0 (Harmondale 0.79, Ravenshore 0.82, Alvar, Shadowspire, Garrote Gorge 1.0). MM6 mixes more (0.39..0.55) |
| styles with 10 % or more of the houses | 1..4 (1) | MM7 and MM8 1-2: Ravenshore t14 (dark-elf town) and t06 (ogre/dock), Dagger Wound t03 huts and t02 |
| share of houses that are the most common model | 0.06..0.41 (0.15) | the same model is never more than about one house in six (New Sorpigal's row of HseP2a copies: 0.41, the top) |
| distinct house shapes per house | 0.42..0.96 (0.59) | 13-31 different shapes per town |

So: pick one style family (Ravenshore's `t14`, Harmondale's `Hh*`: poor `Hhp`, middle `Hhm` and rich `Hhr` grades of
one human style), optionally a second for one quarter (docks, a guild row), and build at least 12 different house
models from it: poor, middle and rich sizes, one and two storeys, L and T plans, porches. Services may break the
style (temples, castles, guild towers). Pictures: `shots/7out02/01-over-from-south.png` (one roof family, every
house a different shape), `shots/out02/01-over-from-south.png`, `shots/outd1/01-over-from-south.png`.

The family of a texture is MM8's numbered set (`t14a05` -> `t14`) or the first two letters of its name (`Hhm1b3`,
`Hhp1b`, `7hhr1el3` -> `hh`; `PXSTRRE` -> `px`).


## 2. Square houses, irregular placement

The shipped towns are not irregular by turning houses: they are irregular by where the houses stand.

| figure | shipped | notes |
|---|---|---|
| doors facing a compass axis (within 5 deg) | 0.77..1.0 (1.0) | eleven of thirteen towns 0.88..1.0; only Pierpont's tree houses (0.77) and Castle Ironfist turn some |
| houses with a mirror partner about the best axis through the town | 0.19..0.61 (0.26) | the MM6 towns are the most regular (New Sorpigal 0.56, Silver Cove 0.61); MM7 and MM8 0.19..0.36 |
| door facing the nearest road square (within 15 deg) | 0.28..0.71 (0.43) | about half the houses face their street; the rest stand side-on or back to it |

So: keep houses on the compass axes (turn at most one in five), but break the grid: unequal plot sizes, houses set
back by different amounts, some side-on to the street, gaps with a tree or a well, no street mirrored across the
centre. A mirror share above 0.4 reads as planned (New Sorpigal's twin fountains and twin rows,
`shots/oute3/01-over-from-south.png`); MM7 and MM8 stay near 0.25.


## 3. Paths: a lane to every door, few long straights, mostly right-angle turns

Road tiles are the built roads (MM6 and MM8 cobble and dirt-road sets, MM7's `7drsr`); MM6 and MM7 towns also
use plain dirt for plazas and lanes (`dirttyl`, the grass-dirt edges `grdrt`), counted as worn ground.

| figure | shipped | notes |
|---|---|---|
| doors with a road or dirt lane within 1024 | 0.81..1.0 (1.0) | eleven towns 0.96..1.0; Tatalia 0.84, Pierpont 0.81 (forest) |
| door to nearest road or dirt lane, median | 147..381 (221) | the lane comes right up to the door |
| town cells of road or dirt | 0.37..0.98 (0.75) | towns stand on worn ground: dirt plazas, not grass with a road through |
| road length on compass axes (+-10 deg) | 0.66..1.0 (0.98) | roads in towns run on the axes; Garrote Gorge (0.66) and Dagger Wound (0.85) wander |
| road turns of 80-100 deg | 0.36..1.0 (0.93) | the tile roads turn at right angles; Shadowspire (0.36), Garrote Gorge (0.55) and Dagger Wound (0.64) use 45-deg jogs |
| junction branch angles of 80-100 deg | 0.17..0.6 (0.52) | half the junction angles are not right angles: T and Y joins, offset crossings |
| straight road run, median | 1024..3072 (1712) | two to six cells between turns |
| straight road run, longest | 3072..5655 (4608) | no straight longer than about 11 cells (5.6k) inside a town |

So the "not all straight lines or right angles" the user asks for comes from short runs (2-6 cells), offset and
three-way junctions and dirt lanes and plazas between the roads, not from curving roads: the tile roads themselves
are axis-aligned with right-angle turns. Every door gets a lane (dirt, or road) within a few hundred units. The
longest straight stays under about 5.6k. Pictures: `shots/outc2/01-over-from-south.png` (Free Haven's cobble lanes
jog round the houses), `shots/7out02/01-over-from-south.png`.


## 4. Services: a full set, in a few clusters, the tavern near the way in

| figure | shipped | notes |
|---|---|---|
| services in town | 6..25 (11) | a town has weapon, armour, magic, alchemist (MM7/MM8), tavern, temple, bank, training, stables or boats; Free Haven 25 with all nine guilds |
| enterable residences | 8..56 (19) | |
| weapon shop to armour shop | 384..5830 (1571) | in seven of eleven towns under 2.1k (Pierpont 384, Free Haven 561, Steadwick 896); Silver Cove, Ravenshore and Dagger Wound split them across quarters |
| magic shop to alchemist | 1147..5677 (2171) | |
| guild to nearest guild, median | 512..10156 (1830) | guilds stand in pairs or rows (Castle Ironfist 512, Pierpont 1025, Harmondale 1640) |
| service to nearest service, median | 1012..2424 (1640) | services are one to five houses apart: clusters, not one per corner |
| tavern rank by distance to the arrival (0 = the house nearest it) | 0.05..0.95 (0.20) | ten of twelve towns 0.05..0.33: the tavern is among the first houses from where the party arrives; Steadwick 0.56, Shadowspire 0.95 |
| tavern rank from the centre (0 centre, 1 edge) | 0.09..0.86 (0.40) | taverns are not at the edge as a rule: the arrival side, not the rim |
| stables rank from the centre | 0.0..0.81 (0.42) | coaches stand inside the town as often as at its edge |
| boats rank from the centre | 0.68..1.0 (1.0) | docks are always at the edge, on the water |
| temple rank from the centre | 0.0..1.0 (0.71) | temples are mostly towards the edge or on their own rise (Ravenshore, Garrote Gorge, Steadwick) |

The arrival is the party's start markers (`party start`, `north start` ...) and the stables and boats. So: put the
tavern on the side the party enters from (the first or second building on the road in), weapon and armour shops next
to each other or across one street, magic and alchemist close, guilds in a pair or a row, docks on the shore, the
temple apart or raised. Pictures: `shots/out02/` (Ravenshore's shop street), `shots/7out03/`.


## 5. Monsters: groups on guard points, the town kept clear

| figure | shipped | notes |
|---|---|---|
| monster groups on the map (spawn points and placed groups) | 18..88 | Free Haven 18 (its second slot is peasants) |
| monsters on the map (est.) | 47..377 | |
| monsters per 100 land cells (cells not water) | 0.47..4.26 | Pierpont 0.47, Steadwick 0.66, Harmondale 1.55, Ravenshore 1.69, Castle Ironfist 4.26 |
| monsters within 1500 of a wild road per 1000 of road (road tiles outside the town; maps with 30,000 of road or more) | 0.03..0.58 | what the party meets travelling: Harmondale 0.32, New Sorpigal 0.21, Ravenshore 0.18, Steadwick 0.12 |
| groups of one / of four or more (share) | 0..1 / 0..1 | by world: MM6 4-5 a group, MM7 Pierpont all ones, MM8 twos and threes |
| group size, median | 1..4.5 | MM6 3-4, MM7 1-2, MM8 2-3.5 from the map's `map_stats` dice; placed camps go to 14-16 (Harmondale's goblins, Ravenshore's pirates) |
| wild group to nearest group, median | 403..2433 (1393) | groups stand in clusters |
| spacing variation (std/mean of that distance) | 0.46..2.08 (0.81) | uneven: clusters and empty stretches; below 0.5 reads as an even sprinkle |
| wild groups within 2000 of a chest, dungeon entrance, bridge or camp | 0.0..0.79 (0.21) | about one group in five guards something; New Sorpigal's crates 0.79 |
| groups within 2500 of a wild chest, median | 0..7 (2) | a guarded chest has about two groups by it |
| wild group to nearest dungeon entrance, median | 7438..23867 (10687) | |
| monster groups inside the town | 0..7 (3) | spawn points reach the town's edge; New Sorpigal, Free Haven, Alvar, Pierpont and Dagger Wound keep it clear (nearest group 4.5k-6.8k from a door) |
| nearest group to a town door | 171..6796 (630) | |

**Start and early maps** (`--start`; Emerald Island `7out01`, Harmondale, Dagger Wound, Ravenshore, New Sorpigal) are
denser than the later towns' maps and mix pack sizes:

| figure | start maps | |
|---|---|---|
| monsters per 100 land cells | 1.55..3.36 | Harmondale 1.55, Ravenshore 1.69, New Sorpigal 2.42, Dagger Wound 2.99, Emerald 3.36 (the two islands are small: 3,684 and 1,191 land cells) |
| monsters within 1500 of a wild road per 1000 of road | 0.18..0.32 | Ravenshore 0.18, New Sorpigal 0.21, Harmondale 0.32 (the islands have under 30,000 of road) |
| groups of one | 0.01..0.33 | |
| groups of four or more | 0.13..0.85 | |
| largest group | 3.5..16 | Harmondale's goblin camps 15-16, Ravenshore's pirates 14 |

So: group sizes from the map's dice (two to four), more where a camp is (10-16 placed), clusters with gaps
(spacing variation above 0.5), about one group in five next to a chest, an entrance or a bridge, two groups by each
guarded chest, and the starter towns kept clear (no group within about 4.5k of a door). A town that is not a start
town may have spawn points at its edge. On a start map: about 1.5-3.5 monsters a hundred land cells, a few groups
within reach of each road out, some lone monsters and some packs of four or more, one camp much bigger than the rest.


## 5b. Town spread: a compact town, a short fringe

The built footprint of the town: models of house size (at least 256 square and 300 high; walls, towers, gates,
bridges, stalls, signs, wells, steps left out; shipped maps split a house into parts, so each counts by its footprint)
within 1536 of a town door or of such a model, measured from the centroid of the town's service doors. The core
radius is the footprint-weighted median distance.

| figure | shipped | start maps | notes |
|---|---|---|---|
| fringe / core (90th percentile / median distance) | 1.29..3.79 | 1.29..2.18 | Harmondale 1.29, Free Haven 1.46, New Sorpigal 1.53, Steadwick 1.90, Tatalia 2.15, Ravenshore 2.18, Garrote Gorge 3.79 (strung along its gorge) |
| farthest / core | 1.43..5.06 | 1.59..2.81 | |
| footprint beyond 1.5 x the core radius | 0.0..0.38 | 0.03..0.29 | Harmondale 0.03, Free Haven 0.09, New Sorpigal 0.13, Ravenshore 0.24, Steadwick 0.29, Tatalia 0.38 |
| 90th percentile distance | 4358..13228 | | Harmondale 5,950, Steadwick 6,719, Tatalia 9,990, Ravenshore 13,228 |
| farthest building | 4711..17027 | | |

So: the services and most houses in one block; houses outside it (beyond the walls, by the stables) a quarter of the
built footprint or less, the last of them within about twice the core radius. Plain fringe homes strung out along the
roads beyond the suburbs read as sprawl.


## 5c. Small towns (`--small`)

A town of nine services or fewer (Xeen's Nightshadow; decision D-20, 2026-11-20) is judged with `--small`: its size
figures by the thirteen towns and four small shipped towns the main ranges leave out, Deyja (`7out05`), Mount Nighon
(`out10`), Paradise Valley (`outa2`) and Kriegspire (`outb1`) (`--shipped` prints them too); the spread and the magic
shop to the alchemist keep only their upper bound. Every other figure keeps its range; one still outside is kept with
a line under "Town feel exceptions" in the map's NOTES.md.

| figure | `--small` | the four small towns (Deyja, Nighon, Paradise Valley, Kriegspire) |
|---|---|---|
| services in town | 5..25 | 5, 7, 5, 6 |
| enterable residences | 6..56 | 10, 6, 16, 11 |
| service to nearest service, median | 854..2424 | 1724, 1891, 854, 1650 |
| tavern rank from centre | 0.0..0.94 | none, 0.0, 0.8, 0.94 |
| town built share | 0.15..0.37 | 0.22, 0.19, 0.32, 0.15 |
| farthest service | 3203..16598 | 3203, 5320, 3554, 5585 |
| service pair median | 1526..8789 | 2254, 5169, 1526, 2978 |
| town core radius | 2360..6552 | 2883, 4141, 2360, 3076 |
| 90th percentile distance, farthest building | up to 13228, 17027 | 4365/4867, 6285/6285, 5549/6259, 5660/6164 |
| magic shop to alchemist | up to 5677 | 5239 (Deyja; the others have no pair) |


## 6. Props: trees and flowers in town, thematic models, wells

Sprite decorations per terrain cell (512 x 512) inside the town and in the 3072-wide band round it. Shipped towns
are bare by OpenYAMM standards: the engine's ground decorations (grass, low bushes) add the rest, and are not counted.

| figure | shipped | notes |
|---|---|---|
| trees per cell in town | 0.008..0.13 (0.03) | one tree per 8-100 cells; New Sorpigal 0.13 (fruit trees), Dagger Wound 0.07 (palms) |
| flowers, plants, bushes per cell in town | 0.0..0.244 (0.07) | Steadwick 0.24, Dagger Wound 0.21, Ravenshore 0.19, Harmondale 0.13 |
| rocks per cell in town | 0.0..0.072 (0.01) | Ravenshore and Alvar 0.04-0.07 |
| thematic sprites per cell in town | 0.0..0.056 (0.0) | barrels, kegs, torches, campfires, rune posts (Shadowspire) |
| thematic models in town | 1..31 (10) | wells, fountains, wagons, signs, docks, bridges, gazebos, tents, cannons (Dagger Wound), shrines |
| trees per cell round the town | 0.011..0.186 (0.03) | |
| flowers per cell round the town | 0.0..0.096 (0.02) | |
| wells and fountains in town | 0..5 (3) | |

So: a few trees and flower beds inside the town (gardens, by houses, round a plaza), rocks only on rough ground,
and props as models: wells and fountains (two to five), signposts at the junctions, a wagon or crates by the
stables and shops, docks with boats, bridges. Picture: `shots/oute3/01-over-from-south.png` (fountains, trees and
flower beds by every house row).


## 7. A buff well, a shrine and an obelisk

Every shipped map has exactly one obelisk; most have one or two shrines or altars (MM6/MM7, none in MM8).

| figure | shipped | notes |
|---|---|---|
| wells and fountains on the map | 3..8 (5) | |
| wells, fountains and altars that give a stat or a resistance | 0..7 (3) | temporary +10..+50 or permanent +2 to a stat, a resistance, gold, HP or SP |
| of those in town | 0..3 (1) | |
| obelisks | 1..1 | |

So: three to eight wells and fountains, two or three of them giving something (one in town, the rest out in the
wild), one plain "Refreshing!" well, one that poisons, an obelisk, and a shrine or altar (MM6/MM7).


## 8. Flat ground, with the town on a rise or in a fold where the land allows

| figure | shipped | notes |
|---|---|---|
| terrain height range in town (p5-p95) | 0..2080 (544) | New Sorpigal and Shadowspire flat (0); Harmondale 864, Steadwick 960, Castle Ironfist 2080 (the castle mound) |
| slope p90 in town (rise per run) | 0.0..0.48 (0.12) | Harmondale the steepest (0.48): houses on the valley side |
| flat share (slope <= 0.02) | 0.73..0.97 (0.84) | even the hilly towns are 3/4 flat: terraces and flat house plots on a sloping site |
| door level range p10-p90 | 0..680 (160) | Harmondale 640, Steadwick 680, Garrote Gorge 512: houses on different levels |

So: the ground under each house is flat, but the town as a whole may lie on a slope or between low hills: about
500-1000 of relief and a few doors 500 above the others gives Harmondale's feel
(`shots/7out02/01-over-from-south.png`: the town in a valley, hills and snow behind). Ravenshore's town is flat
(160); the relief is round it. A dead-flat town (range 0, flat share above 0.95) is within range but is the MM6
starter look.


## Vertigo Meadows (Xeen X1, `output/studio_play/xeen_root`, mm7) against the ranges

`town_feel.py xeen_x1.odm --world mm7 --assets output/studio_play/xeen_root`, 2026-11-13; pictures in
`output/studio_townfeel/shots/xeen_x1/`. 7 of 59 figures outside:

| figure | Vertigo | shipped | change |
|---|---|---|---|
| doors facing a compass axis | 0.27 | 0.77..1.0 | square the houses to the axes (at most one in five turned); get irregularity from setbacks, plot sizes and gaps instead |
| road turns of 80-100 deg | 0.33 | 0.36..1.0 | lay the in-town roads as axis runs with right-angle turns and 45-deg jogs, not odd angles |
| longest straight road run in town | 9230 | 3072..5655 | break the long straight (the street along the wall) with a jog or a junction every 2-6 cells |
| magic shop to alchemist | 1127 | 1147..5677 | marginal; fine as is |
| stables rank from centre | 0.84 | 0.0..0.81 | marginal: the stables sit at the rim; shipped coaches are mid-town as often |
| monster groups on the map | 43 | 47..88 | add a few groups, at chests, the dungeon doors and the bridge |
| flowers per cell round the town | 0.116 | 0.0..0.096 | marginal; thin the beds outside the walls slightly |

Inside but at an edge: monster group size median 4 (the shipped top) with spacing variation 0.47 (the shipped
floor, 0.46): the groups are the largest and the most evenly spread of any town. Make them two to three, in
clusters with empty stretches between. Ground fully flat (height range 0, flat share 0.96, the shipped top): give
the town some relief, a rise or terraces of 500-1000 as Harmondale and Steadwick have. One house style (0.92) and 16
shapes, a lane at every door, services clustered: these are within the shipped ranges. Trees in town 0.126 are near
the shipped top (New Sorpigal 0.13).

**Pass six (2026-11-14, the user: "monster packs are not that many", "the town too stretched out beyond the walls"):**
the new figures on the installed map, `--start`, before / after: monsters per 100 land cells 1.01 / 1.57 (1.55..3.36),
along the roads 0.08 / 0.25 (0.18..0.32), groups of one 0.0 / 0.06, of four or more 0.0 / 0.25, largest 3 / 6;
fringe / core 2.05 / 1.99 (1.29..2.18), farthest / core 2.31 / 2.37, footprint beyond 1.5 x core 0.40 / 0.24
(0.03..0.29). See `devdocs/xeen/briefs/x1/L4/NOTES.md`, pass six.
