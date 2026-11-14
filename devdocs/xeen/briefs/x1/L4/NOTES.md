# X1 Vertigo Meadows, L4 (2026-11-13)

Xeen's starting outdoor map, a new map with no original, built from `devdocs/xeen/MAPS.md` (X1 sheet and layout
sketch), WORLD_DESIGN.md 5.1, QUESTS.md Act I and PLAN_YAML_NEEDS.md section 3. Built and played in MM7's world as
a stand-in (`world: mm7`), as XD-01 to XD-05 are. Map file `xeen_x1.odm`, map_stats row 9130.

## How it is written

The project files (`project.yml`, `plan.yml`, `sketch.yml`, `atmosphere.yml`) are written by
`output/studio_cal/x1/tools/gen.py`; `playtest.yml` by `tools/gen_walk.py` from the built map (door positions,
ground heights, event numbers). Edit the scripts, run `output/studio_cal/x1/v.sh` (generate, fmt, validate, build,
install into the scratch root, terrain materials, walk). Every number is a design value. The land is a 32 x 32 grid
of spot heights from a height function (hills, knolls, the creek's valley, banks at the dungeon doors), three rim
forms and one cliff line.

## What was built

- **Vertigo** (centre about [52, 48]): a walled core 20 x 12 cells (10,240 x 6,144) with four gates, the square
  (start, fountain, money tree, Mayor Gunther's notice), main street and north/south streets; a stone bridge over
  Pitchfork Creek to the south bank (guild row, Joe's shop and warehouse yard); training and stables outside the
  west and east gates. 14 services open MM7 house rows under Vertigo's names: Norman's Ironworks (9), Vertigo
  Armoury (47), Gilbert's Hexes (85), alchemist (117), bank (286), town hall (203, a hall with a clock tower), Lady
  Geraldine's Tavern (240), the Adventurer's Inn (1607, MM7 Tatalia's inn), temple (311, with a spire), Fire/Air/
  Water/Earth guilds (129/135/140/146), Thylon's Training (1571), stables (461). 18 residence doors (MM7 residence
  rows 1101-1108, 1121-1127 under Xeen names), Oslo's hut, Celia's hut, Myra the Herbalist. Joe's shop: a message.
- **The meadows**: orchard road east to the pyramid knoll and the rim (rows of fruit trees), the delta pond with
  Orothin's two statue isles, the obelisk, Fountain of Ability (+2 Luck permanent, once), Waters of Power (+25 HP),
  Wishing Well, Shrine of Poison (+5 Body resistance, once), the Spring Druid's rune stone, Derek's camp, the Water
  Reflector on the rim (a message), the sealed travel pyramid (a message), three signposts.
- **The northern hills** (to about 2,300): two orc outposts plus one east (fire, crate, three placed orcs each).
- **Toad Meadow** hamlet (Myra, Old Valia's cottage, one house) on swamp ground; the **Witch Tower** (three round
  storeys, each set off further north-east) on its rise; the **Forest of the Walking Dead** (dead trees, bones).
- **The rim**: the east edge is a 900-unit cliff at x 104 above water at height 0; the creek's outflow runs to it.
- **Entrances** (doorways with `into`; all lead into the built dungeons, which are in `xeen_root`):
  XD-01 Joe's warehouse doors (south bank, to its start on the loading dock); XD-01 culvert grate on the riverbank
  (barred until qbit 110012, which XD-01 sets from inside; then to the culvert sill); XD-02 Red Dwarf Mines portal
  (north-west hills); XD-03 the Clan King's shaft head (barred until qbit 110031, set by XD-03's lever; a window says
  so; then to the shaft head); XD-04 Witch Tower door (needs the Crystal Key, item 2110, from Old Valia's cottage; a
  window names Valia); XD-05 orc caves' mouth (north-east hills); XD-06 Temple of Yak (dead forest), sealed with a
  window: not built. **The dungeons' own exits still lead to Emerald Island** (their projects say 7out01.odm); they
  are not mine to change. Changing their `to:` to `xeen_x1.odm` with arrival points at these doors is the next step.
- **Errand**: Mayor Gunther's window on arrival (M1/M2, a one-shot timer). Joe's warehouse key under the rain barrel
  in his yard (item 2176, as XD-01 names it).
- **Edges**: west road to X3 (stand-in 7out03 Erathia), north road to X7 (stand-in 7out04 Tularean Forest).
- **Monsters** (stand-ins as the XD maps): slot 1 Goblin (orcs, 6 meadow areas, 12 hill areas, 3 at the tower),
  slot 2 Dragonfly (toads and snakes, 10 areas in Toad Meadow), slot 3 Skeleton Warrior (12 areas in the dead
  forest); 59 spawn markers; 9 placed orcs; 12 townsfolk and 2 gate guards (Harmondale's actor rows).

## Scale against shipped MM6-8 outdoor maps (oymap metrics)

| | X1 | Harmondale | Erathia | Emerald Is. |
|---|--:|--:|--:|--:|
| BModels | 58 | 114 | 124 | 98 |
| building footprint median | 589,824 | 286,720 | 451,584 | 226,304 |
| nearest building gap median | 1,664 | 646 | 640 | 366 |
| relief | 3,456 | 4,000 | 7,872 | 2,176 |
| spawn markers | 59 | 43 | 48 | 11 |
| decorations | 492 | 570 | 547 | 147 |

Town extent: Vertigo with its suburbs about 38 x 25 cells, Harmondale's bowl 34 x 30 (floor 24 x 12). Square to
XD-02 9,700 units, to the shaft 10,100, to XD-05 16,700, to the Witch Tower 26,600 (Harmondale's castle to the White
Cliff Caves about 40,000). Judgement: distances and town extent sit in the shipped range; the buildings are
bigger and sparser than MM7's (2 x 2-cell shops, gaps of 1,664 against 640) and fewer (58 models): the town reads
roomy and a little empty between rows. Halving plot sizes and adding sheds, fences and wells would bring it in.

## Textures

One family per area: the town and hamlet from Harmondale's (MM7 home town) house kits (`plaster`, `timber`, `grey`,
`rich`, `stone`, `poor`); the town wall and witch tower `stone` kit; dungeon doorways `dirt` frames with `7solid01`
doors, as Harmondale's White Cliff Caves door; Joe's warehouse door `chb1dl` in `7t1butts`. Ground: grass_meadow,
swamp (Toad Meadow), soil. Decorations from MM7 maps: Harmondale's trees, flowers, rocks and fruit tree (`tree37`),
Deyja's dead trees (`tree41`, `tree42`, `bush10`), swamp trees `swptree1/2` (the first pass used `tree33/36`,
which are snowy firs: replaced after the pictures). Nothing generated; `level_generation/textures_xeen/` untouched.
Textures to generate: a carved stone portal for the dwarf mine, a skull-hung cave mouth for the orcs, a crystal
lock door for the Witch Tower.

## The walk

`playtest.yml`, 305 steps: new game in the square; the errand window; ten core houses (temple, bank, alchemist,
magic, town hall, armoury, ironworks, tavern, the inn's event, a residence), training through the west gate, the
bridge, four guilds; the rain barrel's key; the culvert grate barred; into XD-01; the stables; up the north road
into XD-02; the shaft head barred (window), then open into XD-03; into XD-05; down the south road to Toad Meadow;
the tower barred (window); Valia's key; into XD-04; Myra; out along the west road to the travel prompt (declined).
After each dungeon the walk returns with `load_map` (the dungeons lead elsewhere). Passed 305 of 305 five times
(once on batch seven, four on batch eight); the final build two of two (`output/studio_cal/x1/run/walk_4.log`,
`walk_5.log`). Installed in `output/studio_play/xeen_root` (with its terrain material file) and loaded in a desktop
run: the square with Gunther's window (`pics/load_check.png`). Play:
`./tools/run_game.sh --isolated x1 --world mm7 --map xeen_x1.odm --assets "$PWD/output/studio_play/xeen_root" --visible --seconds 0`

## Pictures

`output/studio_cal/x1/tour/` (34 shots, `captions.yml`), contact sheets in `output/studio_cal/x1/pics/`
(`sheet1-4.png`, `sheet_fix.png`), plan `pics/plan.png`, sketch `pics/sketch.png`. Run: `tour.yml` via
`tools/run_game.sh --isolated ... --set debug.screenshot_tour_path=...`.

## Gaps (most harmful first)

1. **Doorways stand free on slopes**: the mine, shaft, orc and Yak doors are a dirt frame with a black door on a
   grassy mound; nothing reads as a cave mouth or a timbered adit. A cliff behind the door left the door's floor
   above the ground in front (the doorway takes the height at its middle) and the party could not reach it. Wanted:
   a doorway that cuts its own notch into a cliff, or `doorway.floor`.
2. **The world rim**: the game draws no void; water at 0 below a 900 cliff stands for the stars, and a fall is a
   swim, not death. Needs engine work E5 (edge-fall trigger, sky below the horizon).
3. **No waterfall** where the creek reaches the rim.
4. **Mirror, stables' routes, pyramid, boat**: no mirror network; the stable opens MM7's J.V.C Corral with its MM7
   routes; the pyramid and Nystor's boat are messages only (`not built yet: ... neighbours`).
5. **Adventurer's Inn**: house 1607 runs its event but opens no house dialog in a headless run; the roster screen
   was not checked in a desktop run.
6. Orc outposts cannot be burned (no destructible camp word); the drums' map state (XD-05) is not read.
7. Obelisk riddle is one word in a message (no Cloudside riddle exists).
8. Residences open MM7 Harmondale residents under Vertigo names; Myra, Oslo, Celia, Valia have no NPCs.

## Tool defects

- An item given by an event lands in the hand, where a `{item: n}` condition does not see it (known): the tower's
  condition also accepts `evt.GetHeldItemId() == 2110`.
- `walk_to` outdoors is straight-line only ("no indoor path map"): every leg through gates needed waypoints.
- Two parts with walls in one plane (the town hall's hall and tower front) hid the door's face from the pick
  (the hall's name event fired) while `audit` reported 0 coplanar pairs; fixed by setting the tower 128 forward.
- `oymap build` warns `scatter: 12 of 488 decorations found no place` without naming the entries.

## Second pass: the user's walk and the review (2026-11-13)

Inputs: the user's walk (points below) and `output/studio_cal/x1/review/REVIEW.md` (by eye against ten shipped
towns). Backup of the first pass: `output/studio_cal/x1/pass2_backup/`. New generator modules: `tools/town.py`
(house shapes, plots, streets, the wall) and `tools/dress.py` (ground, paths, trees, flowers, the road check);
`gen.py` imports both, `gen_walk.py` routes by the streets. Pictures: `output/studio_cal/x1/pass2/` (`before/`,
`a3/` = final, `sheet_*`, `compare_before_after_shipped.jpg`, review tour `tools/gen_review.py`).

What changed, by point:
- **Ground**: the town floor is grass; dirt only under roads, the three lanes, door aprons (1 cell, skipped where
  the street's own band reaches the door), paths, the square and Joe's yard.
- **House kinds**: seven shapes in parts: hip cottage, gable-end house with a porch on posts, L house, jettied
  two-storey shop (upper storey on `bottom: 256` reaching out), round tower house (round part, cone) behind a
  gabled entry, round thatched hut (`tiers`), barn with a lean-to, forge (chimney part and an open shed on
  `posts`); plus the town hall's clock tower and the temple's porch and round spire. Kits plaster (cream),
  timber, grey, stone, poor, rich mixed per street; thatch roofs (`hhp2rf`) on some; red-brown `7hhr1rf` on
  towers. Homes are 1 x 1 or 1 x 1.5 cells (were 1.5 x 1.5); hanging shop signs (`signs` `hang`, 7sgarm,
  sgweapon, sgmagi, 7sgalch, 7sgbank, 7sgtvrn, sgtempl, the guilds', 7sgtrain, 7sgstabl).
- **Placement**: every plot turned 4-25 degrees (round huts turned to face their road); homes grouped round
  two lanes and yards behind the shops; the main street bends twice; leftover ground is gardens (fences),
  wells, sheds, trees.
- **Paths**: every door has an apron and a dirt path to the nearest road or lane (`ground` lines); a hard check in
  `dress.py` refuses a build where any road comes within 0.55 cell of a building or a path crosses one. The road
  under a house (-2905.9, 4519.1) was the guild lane under Joe's shop: the lane now ends a cell short of it.
- **Life**: one tree per house placed in its yard, flower strips under side walls, flowers round the fountain,
  five wells (`frame`, two roofed), three market stalls (open parts on posts with a sill), five sheds/barns,
  fences round two gardens and the stable pen, barrels, casks, firewood, hay; 23 townsfolk (were 12), 4 guards.
- **Walls**: 12 runs, each a building of a footing course (`cwb`, 64 out each side) under a crenellated wall 256
  thick (`parapet` 96, `battlements`, castle kit `Ch1b1`, Erathia's wall texture); 8 round towers (corners with
  cone roofs, the rest crenellated) about every 2,500-3,500; four gatehouses of two round towers and a
  crenellated passage 448 over the road. Each run is its own building, so its top follows the ground run by run.
- **Farm belt**: hedged fields with crop rows south of the creek and west of the town, orchard rows, two barns,
  tree clumps to the wall, the existing orchard road.
- **Road rips** (-4813.8, 15068.4 and -1491.9, 15860.3): cobble roads on slopes other than straight or 45 degrees
  (2:7 on the north road) broke into loose tiles. Every cobbled road is now straight runs and 45-degree steps.
- **Monsters**: Goblin 3-5 (was 2-4), Dragonfly 2-4, Skeleton 2-5 per marker; markers 59 to 40 in 14 camps of
  2-4; nothing within 6 cells of a gate; orc outposts 5 placed orcs each (were 3).
- **Dead forest** (-8871.9, -6258.1): dead trees 90 to 230 in 40 clumps, bones 38, rocks 32, dirt mounds;
  `bush10`/`bush11` dropped (they draw as checkered green pillars in this world).
- **Waterfall** (23106, 2452): the creek's end at the rim gets a sloping slab in `7wtrtyl` from the lip to the
  water below (`stairs` `ramp`, 43 degrees), rocks either side and the brook sound (`Snd_Brook`).

Words missing (built the nearest honest form): a **waterfall** (vertical animated water from a lip, with spray;
here a ramp slab in the water texture, which reads as a dark sheet); **spray/mist decorations** (none in MM7's
table); an **arch** over a gate (the passage is level); a **battered wall base** (`taper` scales a part about
its middle, so a long run cannot slope; a wider footing stands for it); **battlements on `kind: wall`** (walls
built as buildings instead); a **fence** (a low wall of planks, `trim11_32`); a **cart** (not placed).
Limits met: a map holds dirt and two more kinds of land, so the dead forest's "dark soil" is plain dirt and the
rim cliff cannot be rock; ground zones snap to whole cells, plots to half cells (fine placement only by `turn`).

The walk: `playtest.yml` 388 steps (doors from the build, routed along the bent streets): passed
(`run/walk_p2_1.log`, `walk_p2_2.log`). Installed in `output/studio_play/xeen_root` with its terrain file.

Still not like a shipped town: the street bands (road plus transition tiles) leave the core browner than
Harmondale's, whose houses stand further from the roads; trees are one kind of big broadleaf and hide houses
from above; roofs are all brown (no red accent like Ironfist or Sorpigal's red trees); the waterfall is a dark
slab, not falling water; walls are one dark texture.

## Exits to Vertigo (2026-11-13)

The five dungeons' exits to X1 now lead here (their projects changed, not this one): XD-01's yard gate to
[-1930, 2918] facing west and its culvert sill to [-1536, 4900] facing south; XD-02's portal to [-10240, 16131], XD-03's
hatch to [-1024, 17565], XD-04's tower door to [12288, -11619] and XD-05's mouth to [9216, 16643], all facing south.
Each is 400 in front of its doorway's face (read from `build/export.json`), on open ground, away from the doorway
model; pictures facing out and back to the door: `output/studio_cal/x1/exits_pics/sheet.jpg`. No marker was needed:
the project files and `gen.py` are unchanged. `tools/gen_walk.py` now goes into XD-05 by the mouth and out by its own
exit (event 18 from XD-05's `ids.lock.yml`), checks the map and the arrival, and walks off downhill; the other
dungeons still return by `load_map` (391 steps). Backup before the change: `output/studio_cal/x1/exits_backup/`.
Coming from a dungeon onto X1 for the first time opens Mayor Gunther's errand window (the one-shot timer); the
dungeon playtests close it on their walk off.

## Tree spacing, wild density, edges and town density (2026-11-13)

From the user's walk: the dead forest stood in tight knots with bare dirt between (pass two read "denser, in clumps"
literally: 230 trees in 40 clumps, nearest tree 0.59 cells, 5 others within 2 cells). The land south of the town
"felt ultra empty". The north road and the creek stopped 17 cells short of the map edge. Measured against shipped
maps (Deyja, Tularean Forest, Harmondale, Shadowspire, Murmurwoods, Mire; towns Harmondale, Ravenshore, Erathia,
New Sorpigal, Alvar, Tatalia). The numbers and the rules are in the round's procedure section ("Tree spacing
(measured)" and the sections after it). Backup: `output/studio_cal/x1/trees_backup/`. Pictures:
`output/studio_cal/x1/trees_pics/` (`cmp_1-4.jpg` before/after, `cmp_deyja.jpg` beside Deyja).

- **Trees**: every stand (dead forest, meadow broadleaf, hill trees, swamp trees) is placed by
  `dress.even_stand`: one dart throw over all its kinds, at least 1.4 cells apart (1 in 12 at 1.0), kinds drawn per
  tree, thinning over the last 3 cells to a third. The dead forest is 139 trees: nearest 1.81 / 1.49 / 1.15 cells
  (Deyja 1.97 / 1.35 / 0.97), R 1.45 (1.47), rim 2.38 against core 1.69 (2.47 / 1.70). Bones, rocks and dead bushes
  stay in their small clumps. The ground stays bare soil.
- **Wilds**: rolling ground (`roll` in gen.py: swells up to about 1,000, none in the town, the hamlet, at doors
  or places, or near the rim). The 8 x 8 relief went from 45 to 141. Bare stretches more than 3 cells from
  anything get one thing each (groves, bushes, rocks, flowers; bones and dead trees by the forest; swamp trees in
  the marsh's east). Eight bare soil patches. An old campfire with bones (66, 107), a grave cairn (88.5, 110), a
  fallen stone ring (78-83, 56-60), and a goblin camp at (77, 109).
- **Edges**: the west road, the north road and Pitchfork Creek run to the terrain's edge (cell 0), as shipped
  roads to neighbours do. The orchard road and the outflow end at the rim, as before.
- **Town**: 12 plain homes on the fringe (outside the north gate, east, south bank) and 4 homes enlarged to
  1.5 x 1.5 cells, with paths. Buildings 43 to 54, median footprint 313k to 420k. The coverage of the town's hull
  stays 0.11 (shipped 0.19-0.45): the creek, fields and gardens lie inside it.
- Walk: passed (`run/walk_trees_1.log`, `walk_trees_2.log`). The scratch root's XD-01 to XD-05 event files and
  XD-03's map were stale (XD-05 led to 7out01): copied from `xeen_root`.

## Pass three: town feel by the numbers, ways in, waterfall, walls, even scatter (2026-11-14)

By `openyamm-studio/calibration/town_feel.py` (TOWN_FEEL.md) and the batch O-A to O-F words. Backup of the project
and generators before the pass: `output/studio_cal/x1/pass3_backup/`. Generators changed: `tools/gen.py`, `town.py`,
`dress.py`, `gen_walk.py`; new `tools/tree_spread.py` (the tree-spacing measure of OUTDOOR_REBUILD_PROCEDURE.md).
Measure the built map against its own root: `town_feel.py output/studio_cal/x1/root/worlds/mm7/maps/xeen_x1.odm
--world mm7 --assets output/studio_cal/x1/root` (with `--assets output/studio_play/xeen_root` the checker reads the
installed scene, not the build's).

**Town feel: 7 figures outside the shipped ranges before, 0 after** (before = the installed trees-pass map):

| figure | before | after | shipped |
|---|--:|--:|---|
| doors facing a compass axis | 0.27 | 1.0 | 0.77..1.0 |
| road turns of 80-100 deg | 0.33 | 0.5 | 0.36..1.0 |
| straight road run, longest | 9230 | 3584 | 3072..5655 |
| straight road run, median | 1340 | 1947 | 1024..3072 |
| magic shop to alchemist | 1127 | 2843 | 1147..5677 |
| stables rank from centre | 0.84 | 0.80 | 0..0.81 |
| monster groups on the map | 46 | 53 | 47..88 |
| flowers per cell round the town | 0.142 | 0.091 | 0..0.096 |
| tavern rank by distance to arrival | 0.44 | 0.16 | 0.05..0.95 (10 of 12 towns 0.05-0.33) |
| monster group size, median / largest | 4 / 5 | 2.5 / 3 | 1..4 / 2..16 |
| wild group spacing variation | 0.48 | 0.67 | 0.46..2.08 |
| wild group to nearest group, median | 713 | 1974 | 403..2433 |
| nearest group to a town door | 5984 | 5345 | 171..6796 |
| terrain height range in town (p5-p95) | 32 | 640 | 0..2080 |
| slope p90 / flat share | 0.0 / 0.94 | 0.438 / 0.81 | 0..0.481 / 0.73..0.97 |
| door level range p10-p90 | 0 | 640 | 0..680 |
| mirror share | 0.31 | 0.38 | 0.19..0.61 |

- **Houses square**: every house in Vertigo, the hamlet's cottage and hut on the compass axes; 4 plain fringe homes,
  the hamlet's third house and the two wild huts keep a turn (7 of 51). Plots on half cells (the studio refuses finer).
  The irregularity is in plot sizes (1 x 1 to 2.5 x 2), setbacks and gaps.
- **Streets**: the main street now breaks into runs of 2-7 cells: the two north-row lanes and the inn lane are cobbled
  and meet it at offset junctions (x 44.5 north, 45.5 south; the bank lane at 56.5), it turns twice at right angles
  round the square's east side (57, 44 to 57, 46) to a moved east gate (62.5, 46); the west road leaves the west
  gate in a right-angle dog-leg (38.5, 44 to 38.5, 46); the orchard road in a 45-degree jog round the east houses
  (63.5, 46 to 66, 43.5), then a right angle at 73. The lanes stop at the foot of the terrace; steps (`stairs`) carry
  them up, and dirt strips run on to the back houses (a cobbled road's bed cuts the terrace and the shops' backs).
- **Relief**: the upper town, a terrace at 1280 (`heights.terraces`, slope 2) behind the north row of shops, which
  stand `against: slope` (back walls left out, the hill through them; the forge's chimney lowered to 512 so it does
  not stand above the terrace); the town hall stands on the terrace with steps down to the main street; the north
  street climbs on a ramp. 640 of relief, doors on two levels.
- **Services**: the tavern on the square's north side (54.5, 41), the inn by the west gate (MM7 counts the inn as a
  tavern: in the middle it ranked 0.08 from the centre, under the shipped 0.09), the alchemist in the inn's old house
  on the main street; the stables half a cell south.
- **Monsters**: slots' dice Goblin 2-3, Dragonfly 1-3, Skeleton Warrior 2-4 (were 3-5, 2-4, 2-5); 50 markers in 46
  spots of 1-3 with empty stretches; two by the hill cache, two by the marsh chest, two by Derek's chest, one by the
  mine, the orc mouth, the tower door and the Temple of Yak; outposts 3 placed orcs each (were 5). gen.py refuses a
  build with a marker within 4,500 of a Vertigo door (plain fringe homes included): the shaft head is 3,000 from the
  north fringe homes, so it has no guard; the town bridge is inside the town, so no group guards it.
- **Flowers**: crops 0.9 to 0.35 a cell, hedges 1.6 to 0.9 a cell of side, the west meadow's flowers 40 to 24, the
  middle meadow's 30 to 24.

**Ways in** (each click face where the old doorway's was, measured with `oymap things`: so the dungeons' exits still
arrive 400 in front, facing out; no arrival point moved):
- Red Dwarf Mines: `cave_mouth` at [44, 31], 1024 square, shell 7grastyl, mouth 448 x 352, floor 1184; dark face
  at Y 16531 (was 16531).
- Orc Caves: `cave_mouth` at [82, 30], roughness 0.7, mouth 512 x 384, floor 1376; face Y 17043 (was 17043).
- The Clan King's shaft: `hatch` (wedge) at [62, 28], 1024 square, mouth 384 x 192, floor 1472; face Y 17965 (was).
- Culvert grate: `culvert` at [61, 53.916], depth 64, outflow 256; face Y 5291 (was 5291).
- Witch Tower: the doorway with a pointed `arch`, 352 high; unchanged place (face Y -11219).
- Temple of Yak (not built, sealed): `cave_mouth` with `mouth.form: door` at [30.5, 96], 1536 x 1024, crest 512 over
  floor 1088, a ridge at 1664 behind it; the forest path now ends in front of it (it ran through the rise).
- Joe's warehouse doors: unchanged doorway.
Every door event and condition is as before (ids.lock gains only hint events and the wall runs' name events).
Measured: a cave mouth's dark face lies `depth` + 72 behind the footprint's front, a culvert's `depth` + 64 behind
the headwall's front; neither is said in the schema.

**Waterfall**: `kind: waterfall` from the creek's lip [103.9, 60] down the rim to [105.3, 60], 1280 wide (was a
sloping slab in 7wtrtyl); rocks and the brook sound kept.

**Walls**: the 12 runs are `kind: wall` (were buildings with a footing course): 384 thick, `batter` 64 over 192,
crenellated (`parapet` 96, `battlements`) where level; the two runs that climb from the street to the terrace (tower
NE to the east gate, the west gate to tower NW) have `top: follow`. Towers and gatehouses stay buildings. Garden and
pen fences are `kind: fence` (were low walls of planks).

**Even scatter**: the stands are one scatter entry each with `kinds`, `spacing`, `close_share`/`close_spacing`,
`edge_thin` (3, 0.35) and `spacing_group: trees` (was one entry per tree from `dress.even_stand`, which still runs
only to keep the wild fill clear). Measured with `tools/tree_spread.py` (nearest median / 10th / least, R, rim /
core):

| stand | pass two's even_stand | the words | shipped |
|---|---|---|---|
| dead forest (spacing 1.6) | 1.80 / 1.49 / 1.15, R 1.41, 1.89 / 1.77 | 1.93 / 1.48 / 1.02, R 1.45, 2.21 / 1.80 | Deyja 1.97 / 1.35 / 0.97, R 1.47, 2.47 / 1.70 |
| west meadow | 1.64 / 1.09 / 1.02, R 1.44 | 1.82 / 1.02 / 0.46, R 1.39 | Harmondale 2.35 / 1.36 / 0.73, R 1.75 |
| hills | 3.54 / 2.67 / 2.56, R 2.20 | 2.97 / 1.76 / 1.21, R 1.97 | |
| marsh | 2.31 / 1.78 / 1.51, R 1.58 | 2.01 / 1.37 / 1.08, R 1.44 | Mire 2.71 / 1.70 / 0.40, R 1.82 |
The west meadow's 0.46 pair is a yard tree beside a farm-belt clump tree west of the training hall (not the stand).
At spacing 1.4 the dead forest came out R 1.38; 1.6 brings it to Deyja's.

**Z-fighting**: 3 pairs (were 31): the temple's spire stood in the nave's back wall (11 pairs; moved 24 out), the
old wall runs' footings and walls (14). Left: two wall-run ends at the south gate (384 square units each) and the
hill signpost (10).

**The walk** (`playtest.yml`, 395 steps, routes changed for the new streets, the temple via the square's east
side, the cave stands half a cell before the new faces): passed two of two against the scratch root
(`run/walk_p3_final_1.log`, `walk_p3_final_2.log`). Installed in `output/studio_play/xeen_root` with `oymap install`
and `outdoor_materials.py`; town_feel on the installed map: 0 figures outside. The dungeons' own playtests were not
run (their arrivals did not move; the new floors under them: mine 1184 = arrival z, orc 1376 =, shaft 1472 under
1500, culvert 584 under 620).

**Pictures**: the desktop display is down (`SDL_Init failed: The video driver did not add any displays`, one try).
Data drawings only: `output/studio_cal/x1/pass3/town_sketch.png` (render-sketch of the town),
`pass3/pics/plan.png`, `plan_town.png`, `iso.png` (`oymap render`). To take when the display is back, then the
by-eye review against the shipped towns' sheets in `output/studio_cal/x1/review/` (`sheet_harmondale.jpg`,
`sheet_erathia.jpg`, `sheet_ravenshore.jpg` ...): the town from four sides (does the upper terrace and its stepped
lanes read; do the shops' backs into the slope show no gaps), the main street from both gates, the square with the
tavern, the town hall's steps, the east gate and the orchard road's jog, the west dog-leg; the mine and orc cave
mouths, the shaft hatch, the culvert on the bank, the Witch Tower's pointed door, the Temple of Yak's door in its
rise; the rim waterfall from the orchard road's end and from below; the walls' battered foot and the two following
runs; the dead forest beside Deyja's sheet.

**Words missing / limits met**: plots and areas snap to half and whole cells (fine placement only by `turn`, which
the town now avoids); a cobbled lane's road bed levels the land across it, so a lane cannot climb a terrace beside a
house built against it (steps instead); `against: slope` warns when a back node lies on a road bed or ramp; the
wedge hatch, cave mouth and culvert do not say where their click face lies relative to `at` (measured above); a
spawn area's `at` is whole cells only; no group can guard the shaft head without coming within 4,500 of the north
fringe homes.

## Pass four: the by-eye review's seven faults (2026-11-14)

From `output/studio_cal/x1/review/REVIEW_PASS3.md` ("not yet"). Backup of the project and generators before the pass:
`output/studio_cal/x1/pass4_backup/` (`project/`, `tools/`). Generators changed: `tools/gen.py`, `town.py`, `dress.py`,
`gen_walk.py`. Pictures: `output/studio_cal/x1/review/pass4/` (`a/`, `b/`, `old/` = the review's three tours at the
same poses, `tour_*.yml`, `run_all.sh`; `key/`, `falls/` the iteration views; contact sheets `sheet_*.jpg`).

1. **Terrace**: the upper town is a step at its front (`slope: 0`, height 1152, 512 over the street; was 1280 on a
   two-cell slope), held by a stone retaining wall (`kind: wall` in five runs along y 41.5, 512 thick over the step,
   48 over the terrace, Harmondale's fieldstone `chb1`). The north-row shops stand on the street (floor 640, 1.5 cells
   deep, no `against`) with their backs to the wall; the armoury is 1 cell wide (the main street's 45-degree step).
   The steps climb the whole 512 (`rise`; they climbed the default 256 and stood as a loose block), in the wall's
   gaps, whose ends flank them; the town hall's flight ends at its tower. The north street ramp climbs 512 over two
   cells.
2. **Rim falls**: three `waterfall` sheets (the creek's width in the middle, two outer sheets spreading to the foot);
   two crag buildings in the water below the rim, each a few leaning many-sided parts (`shape: outline`, `taper`) in
   grey rock `t2bs`, their tops stepped to the land above; boulders along the lip and at the foot. The outflow
   meanders (12 points; it was four straight runs). Missing words: a **rock face** on the terrain (the world's slope
   layer draws every cliff in the earth tint, `cliff_from: dirt`, and an mm7 map has no rock ground), **spray/foam**
   at a fall's foot (no decoration), a **waterfall from a higher top water** (the creek is 576, so the drop is 576).
3. **Culvert**: lower and wider (mouth 320 x 320, headwall 960 x 448) in the town wall's stone `cwb`, set into a quay
   wall (two `kind: wall` runs along the south bank, 400 high) so it no longer stands free. The river lies right behind
   it, so no earth can rise over it; the face is where it was.
4. **Stalls**: hip roofs on their posts (the lean-to's high back wall read as a broken building).
5. **Walls**: runs in light dressed `cwb`, towers and gatehouses in coursed `cnb` with red cone roofs on the corners
   and gate towers; batter 128 over 320 (was 64 over 192); WALL_H 512 (was 576); the gates are a short wall between
   the two gate towers with a round-arched `gates` opening 448 x 416 (was a level passage); the creek side left open
   (south runs, the south gatehouse and two towers dropped), its corner towers standing as the wall's ends.
6. **Ways in**: mine shell grey rock `t2bs` with two torches, timber, barrels and a spoil heap; orc mouth red-brown
   rock `cwb1` (the dragon cave's) with skull piles, two red flags, bones, a skeleton, a fire; shaft head a stone
   hatch `cnb` with timber and a barrel; a ridge behind each cave (1700 / 1880) so the hill rises over the shell.
   Only decorations bound to 3D models are used (sprites read as specks). Every click face is where it was (`oymap
   things`: Y 16531, 17043, 17965, 5291, -11219).
7. **Ground**: no square of soil at each door (only the paths to doors more than a cell from a road); the square
   3 x 3 (was 4 x 4).

Town feel on the installed map: 0 figures outside (terrain range 512, slope p90 0.125, flat share 0.88, door levels
512). The walk (`playtest.yml`, 387 steps; the town hall's door is clicked from the steps, `gen_walk.py` `stairs`):
passed against `output/studio_play/xeen_root` (`output/studio_cal/x1/run/walk_p4_1.log`, `walk_p4_2.log`), run by
`output/studio_cal/x1/walk_xeen.sh`. Installed there with `oymap install` and `outdoor_materials.py`.
Left: the two gate walls' ends inside the east and west gate towers lie on the runs' ends (two hidden coplanar pairs).
Before/after at the review's poses: `output/studio_cal/x1/review/pass4/compare_1.jpg`, `compare_2.jpg`. Still not like a
shipped map: the rim's cliff away from the falls is the earth slope; the cave shells are still smooth-edged humps (now
rock, dressed and in a rising hillside); the crags read as grey slabs from the side; the street bands stay brown.

## Pass five: the user's walk of pass four (2026-11-14)

The user: "much better", and five points. Backups before the pass: `output/studio_cal/x1/pass5_backup/` (`project/`,
`tools/`) and XD-04's `output/studio_cal/xd04/pass5_backup/project/`. Generators changed: `tools/gen.py`, `dress.py`
(the tower path), `gen_walk.py`. Pictures: `output/studio_cal/x1/pass5/` (`before/` at the user's four poses on the
pass-four install, `final/` the same poses and ten more on the pass-five install, `compare_1.jpg`, `compare_2.jpg`
before/after, `final_sheet.jpg`; shipped references `shipped_doors.jpg`, `shipped_falls.jpg`).

1. **Dungeon doors read as dungeon doors** (Joe's warehouse door stood free in the yard). Shipped towns, measured with
   `oymap things` (`pass5/things/`) and pictured (`pass5/shipped/`): a dungeon door in a town is either a door in a
   building of its own (Erathia's sewer house MTSewer: planks, CWB stone and a black 7solid01 door; Tatalia's wine
   cellar in a poor house; Ravenshore's Merchant House of Alvar; Free Haven's stone porches against a hill) or a
   grated outfall in a bank (Erathia's Sewer_*); never a frame on open ground; the hover text says "Enter <name>"
   (MM7, MM8; MM6 shows nothing and asks on the click). Now: Joe's warehouse is a timber building (2.5 x 2.5 cells,
   gable roof) with the loading door in its west wall: a dark 7solid01 opening 256 x 352 in a stone `cwb` frame,
   standing torches either side (`dec06`, the MM8 standing torch model), casks; the click face stays at x -1529 (was
   -1530), so XD-01's arrival is unchanged. The shaft head, the Witch Tower door and the Temple of Yak got torches
   (the Yak door two skull piles too); the mine already had them, the orc mouth its flags and fire, the culvert is
   Erathia's grate in a quay wall. Every other click face is where it was.
2. **Waterfall**: the three `kind: waterfall` sheets are gone. The fall is a building standing in the water at the
   cliff's foot (`thing:rim_falls`, floor 0, its plot from x 105 so it stands at the water's level), whose parts reach
   back over the earth slope to the lip: a box 768 deep, 512 wide (the creek's width), 584 high, whose east wall is
   four bays of `7wtrtyl` as a liquid face flowing down (the sheet, upright, from the creek's level to the water) and
   whose roof is the creek's water running on to the lip (a liquid face flowing east); two rock cheeks (`outline`
   parts in `t2bs`, tapering) either side make the notch; the crags, boulders and brook sound stay. Studio fault for
   the lead's list: see the final report (the `waterfall` word follows the terrain).
3. **Witch Tower door** on the tower's north side (`turn: 180`, at [88, 82.4]; face y -9387, was the south side,
   y -11219), in the tower's grey `cnb` with a dark pointed door (was a dirt frame), two torches; the tower path ends
   at it. XD-04's exit to X1 (`devdocs/xeen/briefs/xd04/L4/project.yml`) now arrives at [12288, -8987, 850], 400 north
   of the face, `direction: 90` (north, facing away); its `playtest.yml` asserts the new arrival and walks off north.
   XD-04 rebuilt (`--out output/studio_cal/xd04/build`) and installed in `output/studio_play/xeen_root`.
4. **Monsters by habitat**: dragonflies (slot 2) over the swamp round the tower (`pop:tower_flies`, were two goblin
   groups), over the outflow and the pond (`pop:creek_flies`, 4 groups, were orc groups on the creek bank); orcs only
   at camps: a new west camp (fire, crate, bones at [23.5, 62.3]) with two groups, the south goblin camp, the old
   campfire (were open-meadow groups); skeletons at the grave cairn (one group added to `pop:dead`). 51 spawn points
   (were 50). town_feel on the installed map: 0 figures outside (groups on the map 54, wild group to nearest group
   1,630, spacing variation 0.73).
5. **Guards**: measured in the shipped towns (`pass5/guards/measure.py`, `measure.txt`, actors of the scene files):
   Harmondale 7 guards to 30 townsfolk, New Sorpigal 5 to 38, Tatalia 8 bowmen to 33, Ravenshore 20 defenders to
   45; about half walk alone in the streets (300-2,000 from a house door, 2,000-4,700 apart), the rest stand in pairs
   350-850 apart at gates and bridges; Erathia has none at the start. Now 13 guards (MM7 `404`, were 4): a pair at
   each gate and the bridge (about 560 apart) and five alone in the streets inside the walls.

The walk (`playtest.yml`, 388 steps; the tower's barred door and the way in from the north): passed two of two against
`output/studio_play/xeen_root` (`output/studio_cal/x1/run/walk_p5_1.log`, `walk_p5_2.log`, by `walk_xeen5.sh`).
Installed there with `oymap install` and `outdoor_materials.py`.
XD-04's playtests against `xeen_root` after the move: `playtest.yml` 174 of 174 and `playtest_m4.yml` 77 of 77, four
of four each (`output/studio_cal/xd04/run/p5_four.out`, by `output/studio_cal/xd04/four_xeen.sh`).
Left: the falls' block and cheeks are plain shapes (no foam or spray at the foot, no curl at the lip); the tower's door
frame stands out from the round wall as a box; the warehouse has no sign naming it (only the hover text).

## Pass six: monsters and the town's spread by the numbers (2026-11-14)

The user's walk of pass five: "monster packs are not that many", and "not sure if the town isn't too stretched out
beyond the walls, compared to other MM7-MM8 cities; maybe OK". Backup before the pass: `output/studio_cal/x1/pass6_backup/`
(`project/`, `tools/`, and `town_feel.py` and `TOWN_FEEL.md` as they were). Generators changed: `tools/gen.py`,
`tools/town.py`. Checker: `openyamm-studio/calibration/town_feel.py` (new figures, a `--start` profile, and a fix: spawn
indices 4-12 are one monster at a fixed tier, as `game/SpawnPreview.cpp` reads them; it read 1-9 as dice groups).
Pictures: `output/studio_cal/x1/pass6/` (`pics/plan_town_before.png`, `plan_town_after.png`; `after/` and
`after_sheet.jpg`, ten in-game views of the suburbs and the new camps from `tour_after.yml`).

**Monsters** (placed actors plus spawn markers x the mean of their slot's dice; land = cells not water; along the roads
= monsters within 1,500 of a road tile outside the town per 1,000 of road):

| map | monsters | groups | per 100 land cells | along roads | ones / 2-3 / 4+ | largest |
|---|--:|--:|--:|--:|---|---|
| Emerald Island 7out01 | 40 | 13 | 3.36 | (road 13,824) | 0.15 / 0 / 0.85 | 3.5 |
| Harmondale 7out02 | 250 | 73 | 1.55 | 0.32 | 0.33 / 0 / 0.67 | 16, 16, 15 |
| Erathia 7out03 | 91 | 63 | 0.66 | 0.12 | 0.56 / 0.44 / 0 | 2 |
| Tularean Forest 7out04 | 47 | 47 | 0.47 | 0.05 | 1 / 0 / 0 | 1 |
| Deyja 7out05 | 108 | 57 | 0.81 | 0.15 | 0.11 / 0.89 / 0 | 2 |
| Tatalia 7out13 | 94 | 51 | 0.78 | 0.06 | 0.16 / 0.84 / 0 | 2 |
| Dagger Wound out01 | 110 | 49 | 2.99 | (road 14,848) | 0.06 / 0.73 / 0.2 | 3.5 |
| Ravenshore out02 | 196 | 71 | 1.69 | 0.18 | 0.01 / 0.86 / 0.13 | 14, 11, 9 |
| Alvar out03 | 122 | 61 | 0.84 | 0.11 | 0 / 1 / 0 | 2 |
| New Sorpigal oute3 | 96 | 30 | 2.42 | 0.21 | 0.27 / 0 / 0.73 | 4 |
| Free Haven outc2 | 72 | 18 | 0.54 | 0.14 | 0 / 0 / 1 | 4 |
| Castle Ironfist outd3 | 377 | 88 | 4.26 | 0.58 | 0.06 / 0.03 / 0.91 | 5 |
| **X1 before** | 134 | 54 | 1.01 | 0.08 | 0 / 1 / 0 | 3 |
| **X1 after** | 208 | 68 | 1.57 | 0.25 | 0.06 / 0.69 / 0.25 | 6, 4, 4 |

X1 was inside the all-town ranges but under every start map (1.55-3.36 a hundred land cells, 0.18-0.32 along the
roads), with no lone monsters and no packs of four. Changes:
- Slot dice Goblin 2-4, Dragonfly 2-4, Skeleton Warrior 2-5 (were 2-3, 1-3, 2-4).
- The roads out: an orc camp by the west road (fire, crate, bones at [11.5, 41.8]; two markers at [12, 43]) with
  dragonflies over the creek beside it ([6, 48], [17, 48]); an orc camp on the north road in the hills (props at
  [72.8, 9.2]; two markers at [72, 10]).
- Habitat: two more skeleton groups in the dead forest ([24, 99], [37, 102]), two more toad groups in the marsh
  ([86, 101], [77, 83]). 61 spawn markers (were 51).
- The orc outposts 4, 6 (the middle one, [56, 23]) and 4 orcs (were 3 each).
- Lone wanderers (placed, one each): a skeleton in the dead forest [35, 89], an orc scout on the hill path [47, 17], a
  goblin on the west road [20, 45], a dragonfly over the marsh [86, 70].
- Nothing within 4,500 of a Vertigo door (gen.py's check; nearest group 5,368).

**Town spread** (house-sized models within 1,536 of a town door or of such a model, by footprint, from the centroid of
the service doors; core = median distance):

| town | 90th pct | farthest | core | fringe / core | farthest / core | beyond 1.5 x core |
|---|--:|--:|--:|--:|--:|--:|
| Harmondale | 5,950 | 8,665 | 4,612 | 1.29 | 1.88 | 0.03 |
| Erathia (Steadwick) | 6,719 | 7,864 | 3,540 | 1.90 | 2.22 | 0.29 |
| Tatalia | 9,990 | 11,020 | 4,641 | 2.15 | 2.37 | 0.38 |
| Ravenshore | 13,228 | 17,027 | 6,069 | 2.18 | 2.81 | 0.24 |
| New Sorpigal | 4,542 | 4,711 | 2,962 | 1.53 | 1.59 | 0.13 |
| Free Haven | 9,589 | 10,449 | 6,552 | 1.46 | 1.59 | 0.09 |
| **X1 before** | 9,540 | 10,747 | 4,660 | 2.05 | 2.31 | 0.40 |
| **X1 after** | 7,824 | 9,319 | 3,940 | 1.99 | 2.37 | 0.24 |

Before: the largest share of footprint outside the core of any of these (0.40; Tatalia 0.38, start maps at most
0.29): the town ran east-west from x 32.7 to 71.5, plain homes strung out beyond the stables and west of the training
hall. Changes (town.py `SUBURB_W`, `SUBURB_E`, `FRINGE`; gen.py `TOWN_THINGS`):
- The four plain fringe homes farthest out dropped: (33, 43) west of the training hall, (68.5, 41), (70.5, 47),
  (71, 41) beyond the stables; the east barn `thing:shed_east` (69.3, 38.6) dropped.
- The training hall 2 x 2 at x 39, by the west gate (was 2.5 x 2 at 36); `west_houses#3` (a barn) in its old place
  at (36, 41) (was 32, 47); `east_houses#3` (the round hut) at (68.5, 45) south of the orchard road east of the
  stables (was 68.5, 46.5; it stays farther out than the stables, so the stables' rank from the centre stays 0.80).
  Their door events are unchanged (ids.lock).
- A barrel by the old training spot moved to (35.5, 42.4).
The south bank (guilds, Joe's) is not in the measure's town: the town's door cluster (4,000 link) stops at the creek.

**town_feel on the installed map**: 0 figures outside, both plain and `--start` (stables rank 0.80, monster groups 68,
group size median 3, largest 6, wild group spacing 2,241 / variation 0.69, nearest group to a door 5,368).

**The walk** (`playtest.yml`, 388 steps, regenerated by `gen_walk.py`): passed two of two against
`output/studio_play/xeen_root` (`output/studio_cal/x1/run/walk_p6_1.log`, `walk_p6_2.log`, by `walk_xeen6.sh`).
Installed there with `oymap install` and `outdoor_materials.py`. Every dungeon click face and the waterfall untouched;
the build's 42 unplaced scatter decorations are as in pass five's project.
Left: the west-road camp stands on a rise north of the road, out of sight from the road itself (pictured in
`after/06-west_road_camp.png`).

## The new waterfall (2026-11-14)

The user saw pass five's falls as a water box with a dirt strip between the creek and its top, between blocky rock
boxes. Backup before the change: `output/studio_cal/x1/falls_backup/` (`project/`, `tools/`). Generator changed:
`tools/gen.py` only. Pictures: `output/studio_cal/x1/falls/` (`before/` on the pass-six install, `after/`, `after2/`,
`after3/` the iterations, `final/` on the new install, same poses: the user's (21758.5, 2119.5, 990.2, yaw 3.088,
pitch -37.7), from below on the water, from the north and south sides, far out, from the creek above the lip, close;
`compare_1.jpg`, `compare_2.jpg` before beside after; `tour_*.yml`, `run.sh`).

- `thing:rim_falls` is the studio's `kind: waterfall` (no longer a building): `line [[104, 60], [106, 60]]`, top 576
  (the creek), foot 0 (the water below the rim), `lean` 220, `spread` 1.7, `back` 768, `pool` 768, `rock_size` 400,
  `rise` 64, rock `t2bs`. The build cuts 3 nodes at the lip and makes 7 of the stream's its bank.
- Dropped: the two crag buildings `thing:falls_crags_n`, `thing:falls_crags_s` (leaning outline parts) and the four
  boulders under the new top water (103.3-103.6, 59-61). The other eight boulders and the brook sound stay.
- Iterations: the word's defaults (upright sheet, crags 0.45 of the width standing 160 over the creek) left the notch
  floor at the foot bare dirt and two tall pillars; `pool` 768 carries the foot water over the notch floor to the sea,
  `back` 768 shortens the top water's overhang on the banks; `lean`/`spread` near Alvar's give the sheet its bend and
  fan; the crags at `rise` 64 end level with the meadow (640), so from below they read as the notch's rock cheeks.

Town feel on the installed map: 0 figures outside, plain and `--start` (`output/studio_cal/x1/falls/town_feel.txt`,
`town_feel_start.txt`). The walk (`playtest.yml`, 388 steps, unchanged): passed two of two against
`output/studio_play/xeen_root` (`output/studio_cal/x1/run/walk_falls_1.log`, `walk_falls_2.log`, by `walk_xeen7.sh`).
Installed there with `oymap install` and `outdoor_materials.py`.
Left: the rim's cliff either side of the crags is the terrain's earth-tinted slope (MM7's slope layer takes the dirt
tint, `cliff_from`; Alvar's falls stand in grey rock models); the top water face is a shade darker than the creek's
terrain water and shows its upstream edge and its sides over the banks; the sheet shows its triangles' diagonals in
the texture; no foam or spray at the foot.
