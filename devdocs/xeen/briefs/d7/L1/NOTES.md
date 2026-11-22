# D7 The Skyroads: L1 plan (MU-3, MU-4) for the phase 6 review

A6 (sub-agent), 2026-11-21. This is a plan only: no geometry, no L2-L4, no build. Nothing is built until a decider
has approved the board (`level_generation/xeen_art/phase6/d7/board_d7.png`, page `board_d7.html`).

`level_generation/xeen_art/phase6/d7_design.py` holds the design as data. `d7_render.py` draws and measures it (the
plan, the Olympus inset, two blockouts, `d7/measure.json`); `d7_brief.py` writes the three YAML files here;
`d7_falls.py` checks the fall landings against the installed Darkside scenes (`d7/falls.json`); `d7_paint.py` makes
one `codex exec` call per concept; `board_d7.py` draws the board. To change anything, edit the design and run
`output/studio_cal/d7/run.sh` (8 GB cgroup cap; it runs everything but the paintings). `oymap fmt`, `fmt --check` and
`oymap validate --assets assets_dev`: no issues.

The shape is X9's L1: an open-air BLV region, the islands as spaces with `at` (the middle, map units) and `extent`;
point positions are in each point's `notes` or `behaviour`. Olympus follows XD-17's town (zones `part_of` the town,
`buildings`, `house_door` points).

## D-58 applied (A6 sub-agent, sixteenth session, 2026-11-21)

D-58 (`D58_DECISION.md`) approved the plan with changes. They are applied in `d7_design.py` (a "D-58" block at its
end that moves things and records each move in `D58_MOVES`; the data above it is the L1 that was reviewed) and
measured by `d7_geom.py` (`road_stretches`, `poi_nn`). The scripts as they were are kept beside them as
`*.pre_d58`. The paintings were not redone. `run.sh` rerun; `oymap fmt`, `fmt --check`, `validate --assets
assets_dev`: no issues. Where this section and the text below differ, this section holds.

| Change | What was done | Figure |
| --- | --- | --- |
| D-1 spacing | 11 groups moved along the roads (none added) and 16 POIs moved within or with their islands; the Blackfang hatch island and the Pyramid's Door moved a little. A group or a POI spot counts for a road when it lies within 2,048 of the walking line or belongs to an island the road passes through; boards and Rest Stops are not counted. | longest empty stretch: ring **8,128**, inner road **6,956**, north causeway **7,703** (was 15,488 / 19,632 / 9,303); POI nearest-neighbour max **8,149** (was 13,096). Figures after L2's snaps onto the clouds (below) |
| D-2 castaway's island | The first castaway's island moved to (-31104, 15104), west of the West Lookout outside the ring; its rope bridge (1,934) runs from the Lookout's west rim. The island and the bridge now count as walkable places for the breath rule. | island 11,340 and bridge 9,497 from the leash circle; every walkable place but the roost and its road **6,808** (needs 5,888) |
| D-3 Megadragon unique | Built at L4: a load event hides it once A3's Q-D26 kill qbit is set (D4's coven pattern). | blocked on A3's qbit name |
| D-4/D-5 roofs | Seven roof arrivals stay arrivals; D7's hatches give the source line and a refusal; Alamar's and the Pyramid's doors both ways when their maps are live (L4). | none of DD-02 ... DD-26 lists a D7 arrival yet |
| D-6 tolls | Four toll points built at L4; the eight Sky Bandits wait on A2's row (no stand-in). | blocked on A2 / A3 |
| D-7 boards | The 18 boards on P5's blank face `xp5brd` (`xp5rest` for the Rest Stops), text on hover only. | no new board textures |
| D-8 concepts | Followed at L3 (Olympus small, plain marble jetty, cloud roads with a paved band, open gilded gate posts, temple on the square's north side, no kerbs, no planting). | - |
| Q1-Q10 | Defaults as decided; Q5 no scarab items (A3's hooks), Q8 roost on Alamar's hatch, leash 1,024, Q9 `xeen_skyroads` with `view_distance_scale` 2. | - |

Moves (from `D58_MOVES`; positions in map units):

- **Groups:** the Watch's second griffins onto the north road (-9216, 18432); the east road's sky golems north to
  (28160, 12800); cloud golems to (21504, -18432) on s1, (14080, -18432) on s2 and (28160, -11776) on e3; the south
  griffins to (1024, -17920); the Lookout's griffins just south of it (-28160, 11072); the east dragons over the
  launch road (-20736, -4864); the Broken Launch's sky golems onto the causeway to Olympus' south-west gate
  (-11264, 768), 3,806 from the town's rim; the cap dragons over the east causeway (4608, 5632) and over the lake
  road (13056, -512).
- **POIs:** the Dust merchant toward the causeway head (-1536, 17024); the tired lamp on the Watch's south lip
  (-17152, 17408), 7,241 from the hoard; the kind lamp (17664, 17408); DD-14's hatch with its island (25088, 15104);
  DD-07's hatch to the junction's west side (26624, -5632); the elements bottle to the Earth Corner's Rest Stop
  (28160, -17920) (the South Rest Stop is now a quiet stop); the south toll (-6912, -18432); the camp's strongbox
  (-14848, -18944); the Smoke merchant (-28928, 3200); DD-05's hatch (-27648, -4608); the four scarab stalls on the
  lake's north-west shore (14080, -3840) to (14848, -3072) and the A2 bottle beside them (15360, -2816); the C3 bottle
  on the east shore (19968, -5120); the sky door with the capstone, now at (9728, 2560).
- **Arrivals moved with their hatches:** `dd05_roof` (-27136, -5120), `dd07_roof` (27136, -6144), `dd14_roof`
  (25088, 14592), `dd15_sky` (11776, 2560).

First fights after the moves: rope 4,399 (the east dragons), returns 4,472-5,724, roofs 3,075-5,838, the sky door
3,938, Olympus' arrivals 5,477 and 8,719 (town buffer). Walkable 480.5 M; quiet 80 %.

**L2 snaps (`d7_geom.snap_onto_clouds`, `snap_olympus`, also in `D58_MOVES`):** the L1 put 14 boards, POIs and
arrivals on or past their island's outline; each moved straight toward its island's middle until 384 inside (32 to
304 units). This includes `entrance:p1_return`, `p2_return` and `p4_return` (corners.yml's (±27136, ±17408) lie past
the corner clouds; now (±27456, ±17728)). Olympus' three gates moved onto the town cloud and open to a lane (south-west
(-7936, 4352), north (-3072, 10560) with a 768-wide causeway, east (-320, 5792)); Lucio's Dock (1.5 x 1.5 cells) to
(-1152, 4224) beside the jetty, which now runs from the cloud (-1984, 4064) through `entrance:olympus_dock`
(-640, 3200) to the boat (1536, 1792). The 'XEEN Skyroad' board moved off the launch road's walking line.

## What the plan holds

**Source:** MM5's Skyroads, dark mazes 89-112 (Sky A1-F4, a 6 x 4 grid of 16 x 16 squares over the Darkside), texts
`dark/aaze0089-0099` and `aazex100-112`. A mosaic of the 24 squares: `phase6/d7/src/sky_grid.png`. The source is a
ring road round the whole sky with four element corners, clouds hung on it, Olympus at C2, the Pyramid's door at D2
and the Sky Lake at E3. Kept:

- the ring and the corners: Fire A1 (north-west), Air F1, Earth F4, Water A4, as `corners.yml`;
- the rope at A3, the Megadragon at A1-A2 ('DANGER! Mega Dragon' at A2 and B1);
- the four Merchants of the Elements on their squares (Smoke A2, Dust C1, Steam D4, Mud F2);
- the Sky Lake's four scarab sellers and its two bottles;
- a toll of sky bandits on each side, 'Eat at Joe's' and 'Speeding??' boards, Rest Stops;
- the roof hatches on the squares over their dungeons.

Moved for the design:

- the Megadragon leaves the ring for a dead-end road (it guarded the Fire Corner in the source);
- Olympus is joined to the roads (no sky ferry; D-5.3's boats only sail up);
- an inner road crosses the sky from the rope to the Sky Lake through Olympus.

**Room:** 128 x 88 cells (65,536 x 45,056): one outdoor map's side long (MAPS: ~1 ODM), the source's 3:2. North is up;
x runs east and y north, with the middle at (0, 0). One source square is 10,923 x 11,264.

**The Skyroad** is a ring of cloud road 768 wide with a band of cloud-stone flags (`7tws1f`) down its middle. Its
centre lines are x = ±28,160 and y = ±18,432. It is 190,872 round through the islands' middles. The north road lies at
1,280, the south road at 768, and the east and west roads climb between them.

On the ring, clockwise from the north-west:

| Square | Island | Floor | What |
| --- | --- | --- | --- |
| A1 | The Fire Corner | 1,280 | step-off (m38.corner_fire), 'Fire Zone', Rest Stop, `entrance:p1_return` |
| B1 | The Griffin Watch | 1,280 | griffins 3 + 2; 'DANGER! Mega Dragon' facing the roost; the tired genie's lamp |
| C1 | The North Crossing | 1,280 | Rest Stop; the Dust merchant; the causeway south to Olympus' north gate |
| D1 | The North Toll | 1,280 | toll ('Pay us 10,000 gold or else!'); 'Speeding??'; spur to DD-08's hatch |
| E1 | The East Rest Stop | 1,280 | Rest Stop; the kind genie's lamp |
| F1 | The Air Corner | 1,280 | step-off (m38.corner_air), 'Air Zone', Rest Stop, `entrance:p2_return`; spur to DD-14's trapdoor |
| F2 | The Mud Wharf | 1,152 | toll ('You have invaded our territory ...'); the Mud merchant |
| F3 | The Eastern Tower's junction | 1,024 | Rest Stop; 'Speeding???'; DD-07's hatch; the Sky Lake road |
| F4 | The Earth Corner | 768 | step-off (m38.corner_earth), 'Earth Zone', Rest Stop, `entrance:p3_return` |
| E4 | The South Rest Stop | 768 | Rest Stop; the 'test of the elements' bottle |
| D4 | The Steam Post | 768 | the Steam merchant; spur to DD-06's hatch |
| C4 | Joe's Corner | 768 | toll ('Many apologies, good folks, but this is a robbery.'); 'Eat at Joe's' |
| B4 | The Skywaymen's Camp | 768 | the bandits' strongbox (T6); cloud golems 3; 'Eat at Joe's' |
| A4 | The Water Corner | 768 | step-off (m38.corner_water), 'Water Zone', Rest Stop, `entrance:p4_return`; DD-02's and DD-03's hatches |
| A4 | The West Toll | 832 | toll ('Hold! The toll for passing this part of the road is 10,000 gold!') |
| A3 | The Rope's Head | 1,024 | the Dark Grove rope (`entrance:d1_rope`); 'XEEN Skyroad'; 'Eat at Joe's'; Rest Stop; DD-05's hatch |
| A2 | The Smoke Post | 1,152 | the Smoke merchant; 'DANGER! Mega Dragon' at the dragon road's foot |
| A2 | The West Lookout | 1,216 | griffins 2; a rope bridge to the first castaway's island |

The inner road, west to east:

- **The Broken Launch** (B3), floor 1,152: the gods' old launch, a marble jetty with no boat, the source's 'Olympus
  Launch'. Sky golems 3, a lost traveller's pack, and the bottle 'Evil Genies NEVER let their victims off the hook'.
  A rope bridge south leads to the Genie's Rock (the angry genie) and on to the second castaway's island.
- **Olympus** (C2), floor 1,792, 9,728 x 7,680, the highest cloud. It has three gates, north, south-west and east,
  each two gilded posts with no leaves (inside: below).
- **The Pyramid's Door** (D2), floor 1,408: the Great Pyramid's golden capstone floating over a cloud, its sky door to
  DD-15 both ways after m30.done, and cloud dragons 3 + 2 circling it.
- **The Sky Lake** (E3), floor 896: a cloud bowl with a shallow lake, the four scarab stalls in a row on the west shore,
  two bottles and the 'Sky Lake' board. The lake road goes on to the Eastern Tower's junction.

**The Megadragon's Roost** (B2), floor 1,536:

- The Megadragon (11654, 125, leash 1,024) sleeps on Castle Alamar's roof hatch. The hatch reads 'Descend to Castle
  Alamar?' and then 'The door is locked. Scratched on the surface are some words: The Megadragon has the key!'
  (aaze0089:4-5). Its hoard (T6) lies beside it.
- Its road (6,217) leaves the Smoke Post. Nothing else leads there.
- Its leash circle stands **6,808** from every other walkable place; D-54's rule needs 5,888 (Ice Blast's 5,120 + 768,
  applied to Dragon Breath). A party on any required road is out of its reach.
- The first castaway's island (A2 at 12,14, as the bottle says) is 4,326 from the circle: inside the breath, a risk
  and not a route.

**Olympus** (`plan_olympus.png`; A4's `source/towns/d7.yml`):

- **The square**: the Mirror of Olympus (house 4807) in its middle with `entrance:olympus_square` beside it, and the
  four prophecy statues (m31.statue_1-4) at its corners.
- **The temple court** (north): the Temple of Olympus (4803, a gold dome and a portico of six columns), with the Light
  guild (4805) and the Spirit guild (4806) either side.
  - Soul Storage is a small walk-in vault between the Light guild and the temple, its door to the south. The door
    runs m31.soul_storage (Chosen Ones only); the shelf gives the box, and the true-name plaque
    (m31.true_name_plaque) hangs by the last shelf.
- **The east lane**: the Forge of the Gods (4801), the Nectar House (4802) and the Hall of Heroes (4804), doors to the
  square.
- **The gods' row** (west):
  - Zeus (4813), Hera (4814; Ligono waits here, Q-C19) and Athena (4810) face the square;
  - Hermes (4811) and Atlas (4812) stand on the south lane;
  - Adonis (4809) is in the back lane on the west rim, the ants' lookout terrace beside it (his line, aaze0037:17).
  - DD-26's stair is under a marble grate in the back lane behind the row (`entrance:dd26_stair`).
- **Lucio's dock** (south-east): Lucio's Dock (4808) and a marble jetty out over the void with a celestial boat moored
  at its end. `entrance:olympus_dock` is on the jetty's town end; m31.arrival fires on the first landing.

**Loops:**

- the ring itself;
- the west loop: the rope, the inner road to Olympus, out of the north gate and round by the Fire Corner;
- the east loop: Olympus' east gate, the Pyramid's door, the Sky Lake, up the east road and home by the north.

## Figures (`d7_render.py`, `phase6/d7/measure.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Monsters placed | 50 (MAPS; sky maps all placed) | **50** in 19 groups of 2-3, all fixed |
| Kill XP per member | 48.5k | **48.8k** (+0.6 %): Griffins 11562 (48) x12 = 33,408; Sky Golems 11594 (75) x8 = 51,000; Cloud Dragons 11650 (70) x8 = 44,800; Cloud Golems 11592 (50) x22 = 66,000; 195,208 for the party. With the Megadragon (125, 16,875) 53.0k |
| Monster band | 50-75, Megadragon 125 | 48-75 (the griffins are the source's B1 birds; question 4), Megadragon 125 |
| Not counted | - | the Megadragon; 8 sky bandits, peaceful until a refusal (question 3) |
| Size | ~1 ODM | room 128 x 88 cells; the ring 190,872 round |
| Walkable cloud | X9: 272 M units² for 50 | **483.4 M** (roads 149.2 M, Olympus 63.7 M) |
| Quiet | at least a third | **80 %** of the walkable cloud is over 2,048 from any group: the roads are narrow, so a group covers little road (question 1) |
| First fight | 2,000-6,000 from each arrival | rope 5,538; corners' returns 4,222-4,720; roofs 3,665-5,724; the Pyramid's door 2,290; Olympus' arrivals keep the town buffer (nearest group 5,948 from the town's rim) |
| Roads | - | ring links 3,172-11,177; spurs 1,362-6,217; rope bridges 1,640-3,984. Between quiet stops (Rest Stops, corners, posts) 6,333-27,147 |
| By road from Olympus | - | the rope 26,776; the Sky Lake 25,833; the corners: Fire 39,488, Water 39,784, Air 42,560, Earth 50,430; the roost 47,228 |
| Points of interest | X9: 29 | **56** by the census (chained within 400; arrivals out): 35 on the roads, 21 in Olympus. The 18 boards are hover-only landmarks, not POIs (question 7). The four scarab stalls are one spot. Nearest-neighbour median 2,636 (724-13,096) |
| Chests | treasure 6 | 5, all T6: the hoard, two castaways' strongboxes, the skywaymen's strongbox, a lost traveller's pack |
| Heights | - | the south road 768, the north road 1,280, the spurs 704-1,216, the Sky Lake 896, the Pyramid's Door 1,408, the roost 1,536, Olympus 1,792 |
| Textures | Dungeon L cap 70 (as X9) | about 30 named (below); 2 new |

Groups, by place (`pop:` ids in plan.yml):

- **The north road:**
  - cloud golems 3 between the Fire Corner and the Griffin Watch;
  - griffins 3 + 2 at the Watch;
  - cloud golems 3 between the North Toll and the East Rest Stop;
  - sky golems 2 between the East Rest Stop and the Air Corner.
- **The east road:**
  - sky golems 3 and cloud dragons 3 between the Air Corner and the Mud Wharf;
  - cloud golems 3 on each of the next two stretches.
- **The south road:**
  - cloud golems 2, 3 and 3 (the camp);
  - griffins 2 between the Steam Post and Joe's Corner;
  - cloud golems 2 before the Water Corner.
- **The west road:** griffins 3 north of the rope, and griffins 2 at the West Lookout.
- **The inner road:** sky golems 3 at the Broken Launch, cloud dragons 3 + 2 round the Pyramid's Door.

Walking golems stand on the road's middle line (384 from each edge) or 300 or more inside an island's rim. Griffins
and dragons fly.

## Ways in and out

| Entrance | Where (z) | From / to | Kind |
| --- | --- | --- | --- |
| `entrance:olympus_dock` | (-640, 3200, 1792), facing n | Lucio's boats from D1, D3, D4 (D-5.3, routes 424-426, after m30.done) | arrival (A4's name) |
| `entrance:olympus_square` | (-4608, 6400, 1792), facing n | the Darkside mirrors, Town Portal | arrival (A4's name) |
| `entrance:d1_rope` | (-24576, -6656, 1024), facing e | D1's Dark Grove rope (m30.grove_rope, D-23); back down to D1's `entrance:d7_rope` | both |
| `entrance:p1_return` ... `p4_return` | (±27136, ±17408) at the corners' Rest Stops, facing the road | P1-P4's way out (corners.yml) | arrival |
| `entrance:dd02_roof`, `dd03_roof` | (-27136, -18432) and (-26624, -19968), 768 | Ellinger's Tower (A8), Castle Kalindra stage 4 (A8) | arrival, one way up |
| `entrance:dd05_roof` | (-28416, -5632, 1024) | the Western Tower (A8) | arrival, one way up |
| `entrance:dd06_roof` | (5632, -14848, 704) | the Southern Tower (A7) | arrival, one way up |
| `entrance:dd07_roof` | (29184, -6656, 1024) | the Eastern Tower (A7) | arrival, one way up |
| `entrance:dd08_roof` | (5632, 15104, 1152) | the Northern Tower (A8) | arrival, one way up |
| `entrance:dd14_roof` | (23552, 14080, 1152) | Castle Blackfang's roost trapdoor (A8) | arrival, one way up |
| `entrance:dd15_sky` | (10752, 3584, 1408), facing w | the Great Pyramid's sky door (A8): DD-15's `entrance:d7_sky` | both, after m30.done |
| `entrance:dd17_roof` | (-18688, 8448, 1536), facing w | Castle Alamar's roof hatch (A8): DD-17's `entrance:d7_roof` | both, with the Megadragon's key |
| `entrance:dd26_stair` | (-8704, 8192, 1792), facing e | the Olympus Sewer (A8): DD-26's `entrance:d7_stair` | both |
| the corners' tips | (±30464, ±20480) | P1-P4's `entrance:d7_fall` after 'What do you seek?' and the element's name | exit |
| falls | anywhere off the clouds | the surface beneath, `entrance:d7_fall` (below) | exit |

**No Fly** (WORLD_DESIGN 3.4): no BLV casts it; `rules.no_fly` stays as a record. **The way down** is D-5.3's:
falls, Olympus' mirror and Town Portal, plus the rope and the two two-way doors.

## Falls (D-6.2, D-54)

The sky over the Darkside is cut in a 3 x 2 grid by the source squares (A-B, C-D, E-F; rows 1-2 and 3-4). A fall
lands on the map beneath, at one named arrival per map, `entrance:d7_fall`.

- The landings sit by a way back up where one exists.
- Falling damage is about a third of a level-55 party's HP, as D-6.2.
- As X8 and X9: a one-second check below z -1,000 and the room's floor at -6,000 run A3's `Xeen.skyFall`.

`d7_falls.py` measured each landing against the installed scene:

| Zone (squares) | Map | Landing (ground) | Why there | Nearest actor | Nearest decoration |
| --- | --- | --- | --- | --- | --- |
| A1-B2 | D6 (A6) | (13824, -7680, 1664), facing s | 1,024 before the Necropolis' gate (the mirror inside) | 11,520 | 1,133 |
| C1-D2 | D5 (A6) | (0, -8704, 1248), facing n | 1,536 before the Great Pyramid's door (its sky door goes back up) | 15,477 | 3,315 |
| E1-F2 | D4 (A6) | (5632, -13312, 1120), facing w | Lakeside's square, by the ferry dock's Olympus slot and the mirror | 2,254 (a townsman) | 3,304 |
| A3-B4 | D1 (A6) | (-6656, 6144, 1152), facing s | 1,024 north of Lucio's Jetty; the rope is 8,300 north | 6,326 (a peasant) | 928 |
| C3-D4 | D2 (A6) | (15872, -6656, 1056), facing s | 1,024 before the Southern Tower's door (its roof goes up) | 17,194 | 375 |
| E3-F4 | D3 (A5) | (-15360, 11776, 1440), facing e | outside Sandcaster's south gate, by the Sky Stair and Lucio's Jetty | 1,316 (a peasant) | 1,416 |

The D1 grove by the rope's foot was the first choice, but seven electrapedes stand within 3,072 of it, so the landing
moved to the jetty. Each map's owner confirms a whole cell, flat ground, 256 clear round, and no water or lava at
install (requests).

## The corner contract (`phase6/corners.yml`, unchanged)

| Corner | Square | Tip (step-off) | Hook | Plane's arrival | Return here |
| --- | --- | --- | --- | --- | --- |
| Fire, north-west | A1 | (-30464, 20480), floor 1,280 | m38.corner_fire | P1 `entrance:d7_fall` | `entrance:p1_return` (-27136, 17408), facing se |
| Air, north-east | F1 | (30464, 20480), 1,280 | m38.corner_air | P2 `entrance:d7_fall` | `entrance:p2_return` (27136, 17408), facing sw |
| Earth, south-east | F4 | (30464, -20480), 768 | m38.corner_earth | P3 `entrance:d7_fall` | `entrance:p3_return` (27136, -17408), facing nw |
| Water, south-west | A4 | (-30464, -20480), 768 | m38.corner_water | P4 `entrance:d7_fall` | `entrance:p4_return` (-27136, -17408), facing ne |

- Each tip asks 'What do you seek?' (the source's line). Any other answer runs m38.corner_wrong.
- A plain fall near a corner, without the question, lands on the surface below like any other fall.
- The Megadragon's leash circle is 10,295 from the Fire Corner's cloud; the nearest place to it is the West
  Lookout, 6,808. corners.yml's note "the Megadragon's road also runs here" is honoured by the dragon road's
  sign and the roost's view, not by the dragon on the corner (question 8).

## MU-4 concepts

`d7_paint.py` made one `codex exec` call per view, with no retry. Both came back on the first attempt:
`phase6/d7/raw/d7_arrival_v1.png` and `d7_signature_v1.png`, each with its prompt (.txt) and log (.log).

Each call had three references:
1. the blockout from the camera;
2. X9's approved concept, for this world's clouds;
3. the Darkside's amber noon sky, which the `xeen_skyroads` preset inherits.

- **The arrival is the Dark Grove rope**, not Lucio's dock.
  - The dock lands inside Olympus, a town arrival like any harbour, and the signature already shows the city.
  - The rope lands on the open Skyroad and must teach the map in one look: the road, a golem guard, Olympus as the goal
    far off, the capstone and its dragons, the lake islands.
  - Camera: (-24576, -6656), eye 1,200, facing 24 degrees (east-north-east).
- **The signature is Olympus across the cloud roads**, not the Megadragon's road.
  - Olympus is the map's identity, its main story stop (M31), and every visitor sees it.
  - The Megadragon is optional, and its road is a dead end that most parties walk once.
  - Camera: on the east causeway at the Pyramid's Door, (6144, 4608), eye 1,616, facing 164 degrees (west). The city's
    middle is 11,000 away.

Against the plan (the plan wins at L2-L3):

- **Arrival.**
  - Olympus is painted larger and nearer: it is 25,600 away and should be small.
  - The painter added a winged statue on Olympus.
  - The launch became an arched marble bridge-head.
  - The road is fully paved; the plan has cloud with a paved band.
- **Signature.**
  - The gate has gilded leaves (the plan has open posts) and griffin statues.
  - The temple stands on the gate's axis; the plan puts it on the square's north side.
  - The causeway has carved kerbs.
  - Cypresses and flowers were added (no planting is planned; question 6 keeps the gates and the town's layout).

## Original lines (dark/aaze0089-0099, aazex100-112)

| Line | Where |
| --- | --- |
| 'Fire Zone' (0089:0), 'Water Zone' (0092:0), 'Air Zone' (x109:0), 'Earth Zone' (x112:0) | the four corners' boards |
| 'What do you seek?' (0089:6, 0092:8, x109:6, x112:5) | the corners' question |
| 'DANGER!  Mega Dragon' (0090:0, 0093:0) | the dragon road's foot; the Griffin Watch |
| 'Descend to Castle Alamar?' / 'The door is locked. ... The Megadragon has the key!' (0089:4-5) | Alamar's roof hatch |
| 'XEEN Skyroad' (0092:1) | at the rope, the inner road's start |
| 'Eat at Joe's' (0091:0, 0096:0, x100:0), 'Speeding??' (x101:0), 'Speeding???' (x109:1), 'Rest Stop' (x105:0, x108:0), 'Sky Lake' (x107:0) | the boards |
| the four tolls' lines (0097:2-3, x109:3-4, x100:2-3, 0092:3-4) | the tolls |
| the four riddles (0090:4-10, 0097:4-10, x104:4-10, x110:0-6) | the merchants |
| three genies (0093:11-14, x105:11-14, 0099:0-7) | the lamps |
| four bottles (x103:1-2, x107:2-3) | the bottles |
| the four scarab sellers (x107:4-11) | the Sky Lake's stalls |
| 'Descend to the North Tower?' (x101:4), 'Descend into the South Tower?' (x104:0), 'Descend to the East Tower?' (x111:4), 'Descend to Castle Blackfang?' (x109:5), 'Enter West Tower?' (0091:1), 'Descend into Ellinger's Tower?' (0092:5), 'Descend into Castle Kalindra?' (0092:6), 'Enter the Pyramid?' (x102:0) | the hatches and the sky door |
| 'Pull up the rope?' (0091:6), 'Descend to the Darkness Below?' (0091:5), 'Bucket o' Darkness' (0091:7) | the rope |
| Adonis's 'The people are so small they look like ants' (0037:17) | his house, by the ants' lookout |

Not used: 'Begone, impudent fools!' (the corners' wrong answer; A3's m38.corner_wrong has its own line), the
Lucio/Lucky boatmen's offers (the boats only sail up), and the 'Super Goober!' and paradox genies.

## Hooks placed

- **A3's, by name:**
  - m31.arrival (the dock), m31.soul_storage, m31.true_name_plaque, m31.statue_1 to m31.statue_4;
  - m38.corner_fire, m38.corner_air, m38.corner_earth, m38.corner_water, m38.corner_wrong;
  - m30.grove_rope (D1's side; its yes branch moves the party to `entrance:d1_rope`).
- **Read:** m30.done 111600 (the sky door, the vault), mirror_olympus 119012.
- **New, asked of A3:**
  - four tolls;
  - four riddles;
  - three lamps under Q-D27 (`d7_tired`, `d7_kind`, `d7_angry`);
  - four bottle texts;
  - Q-D26 (the Megadragon: the hoard, the key, Alamar's hatch);
  - the hatches' "Bolted from below." line;
  - the scarab sellers (question 5);
  - D7's six fall zones in `Xeen.skyFall`;
  - ORIGINAL_LINES rows for the lines above.

## Textures (Dungeon L, cap 70, as X9)

Shipped first:

- the world's cloud: `xccloud`, `xccloudsd`;
- the Skyroad's band and Olympus' paving: `7tws1f`, Celeste's marble, as on X9;
- rope bridges: `t66floor` (as X8);
- Olympus in MM7 Celeste's set:
  - `Hwm2WALL`, `Hwm1b`, `Hwp1bWALL` (walls and plinths);
  - `HWM2RF` (roofs), `T3S2B` (gold band), `7trimda` (trim);
  - `CWDL` and `CWDR` (gates), `Hwm2d` (house doors);
  - the signs `sgWEAPON`, `7sgtvrn`, `7sgtrain`, `sgLIGHT`, `sgspirit`;
- the hatches' surround `xwcloudst`, and the sky door `xdpyrdor` (D5's);
- P5's Rest Stop hut set and boards (shared);
- the Sky Lake: the engine's indoor water liquid.

About 30 in all. Every name above was checked in `assets_dev`.

New (2, after approval):

- `xsbarge`: the merchants' gilded sky-barges, one sheet in four element tints;
- `xsglow`: the corners' element glow under the tips, one sheet.

## Open questions for the decider

The plan is drawn on the default of each question.

1. **Size of the ring.**
   - Options:
     - (a) As drawn: one ODM side (128 x 88). The ring is 190,872 round, the walkable cloud 483 M, and a corner is
       39,488-50,430 by road from Olympus.
     - (b) The ring at 80 % (room 104 x 72): about 150,000 round and about 380 M of cloud. The corners come 8,000-10,000
       nearer.
     - (c) As (a) plus an inner south road from the Genie's Rock to the Steam Post (about 9,000), which cuts the walk
       to the Earth and Water corners.
   - Evidence: MAPS asks ~1 ODM; the source's ring runs round the whole sky; X9 is 272 M for 50 monsters. Quiet is 80 %
     because a group covers little of a 768-wide road.
   - Default: (a). Everything at L2 depends on it.
2. **Tower roofs.**
   - Options:
     - (a) One way up (WORLD_DESIGN 3.3, D-5.3): seven roof stairs (DD-02, 03, 05, 06, 07, 08, 14) arrive on D7, and
       D7's hatches read the source's line and "Bolted from below." The Pyramid's sky door and Alamar's roof are both
       ways.
     - (b) All both ways: the source's "Descend to ...?" lines. DD-14's L4 note already expects `entrance:d7_roof`.
     - (c) As (a) but only the four towers of Mok, the Pyramid and Alamar; no Ellinger, Kalindra or Blackfang hatch.
   - Default: (a). The A7/A8 roof work (seven roof rooms) and the hatch count depend on it.
3. **Sky bandits.**
   - Options:
     - (a) A toll hook plus two placed peaceful "Sky Bandits" per toll. This needs a new A2 row (about level 55, the
       thieves' tier D on BThief C). They turn hostile on a refusal and are not counted: 8 in all, 7.15k a member if
       all are fought.
     - (b) Text only: pay, or refuse and they shrug and step aside.
     - (c) Hostile from the start, counted in the 50, with golems cut to keep 48.5k.
   - Evidence: the source has bandits on 20 of 24 squares, pay or fight. No family of people stands at 50-75.
   - Default: (a). The A2 row, A3's hooks and S's binding depend on it.
4. **The monster mix.**
   - Options:
     - (a) As drawn: Griffins 48 x12, Sky Golems 75 x8, Cloud Dragons 70 x8, Cloud Golems 50 x22; 48.8k.
     - (b) No griffins (the band strictly 50-75): Sky Golems 8, Cloud Dragons 8, Cloud Golems 34; 49.4k.
     - (c) As (a) with Green Dragons 80 x3 (the source's E2) in place of three Cloud Golems; 52.0k (+7 %).
   - Evidence: the source's lines are griffins B1, sky golems F1/B3/A2, cloud dragons D2, green dragons E2; D-50 used
     the griffin at 48.
   - Default: (a).
5. **Scarab sellers.**
   - Options:
     - (a) Four A3 hooks with `Xeen.payGems`, as the source's offers (300-600 gems, rescaled), with four resistance
       scarabs from A2.
     - (b) Four A4 street-vendor houses (the Crossroads' route).
     - (c) One A4 shop with four stalls as dressing.
   - Default: (a).
6. **Olympus' ways in.**
   - Options:
     - (a) As drawn: three causeways, from the north road, the Broken Launch and the Pyramid's Door. The gates are open
       gilded posts.
     - (b) The source's: an island reached only by Lucio's boats and a sky ferry from the Broken Launch.
     - (c) The north causeway only.
   - Evidence: D-5.3's boats only sail up, so a party that comes up the rope needs a road to Olympus. WORLD_DESIGN 3.4
     keeps fortress doors only; Olympus is a town.
   - Default: (a).
7. **POI count.**
   - Options:
     - (a) 56 as drawn, with the boards hover-only.
     - (b) The boards clickable: 74.
     - (c) About 45: drop the two road bottles and the West Toll, and fold the north toll into the North Crossing.
   - Evidence: X8 13, X9 29; town hubs 35-55 (D-20); D7 is a sky map with a 13-door town.
   - Default: (a).
8. **The Megadragon.**
   - Options:
     - (a) As drawn: on Alamar's roof hatch at the end of the dragon road, 6,808 clear of every other road. The hatch
       opens with the hoard's key, both ways.
     - (b) As (a), but Alamar's roof stays sealed; Q-D26 pays the hoard only.
     - (c) The source's: on the Fire Corner. M38 then needs the dragon dead first.
   - Default: (a).
9. **The failing sun.**
   - Options:
     - (a) One preset, `xeen_skyroads`: the full Darkside day above the haze.
     - (b) Two more presets for the fading and failing stages, switched by A3's qbits as on the surface.
   - Default: (a). D7 opens after M30, when the surface is "failing"; (b) is cheap to add later.
10. **Fall landings.**
    - Options:
      - (a) As listed: one `entrance:d7_fall` per surface map, by a way back up, with a third of HP in damage.
      - (b) One landing for the whole sky, at D1's jetty.
      - (c) X8's scaled mapping onto each map.
    - Default: (a). Six owners' arrivals depend on it.

## Requests (for the orchestrator to relay)

- **A2:**
  - map_stats row 9114 (The Skyroads, `xeen_d7.blv`): encounter 0, treasure 6, lock 12, trap 6, perception 6,
    refill 672, music 30, plains. Its slots are as in project.yml; add its bolster_maps row.
  - The Act VI recount: 48.8k (53.0k with the Megadragon).
  - With question 3 (a): a "Sky Bandit" row of about 55, in its own faction, peaceful until struck or refused.
  - Q-D26's hoard artifact and the Alamar roof key item.
  - With question 5 (a): four resistance scarabs.
- **A3:**
  - The new hooks above, Q-D26, D7's six zones in `Xeen.skyFall`, and the ORIGINAL_LINES rows.
  - The corners' question flow: the map asks 'What do you seek?' and calls m38.corner_<element> or corner_wrong.
- **A4:**
  - d7.yml's door ids as drawn (13 doors and the mirror; positions in plan.yml).
  - The `at` of `olympus_square` (-4608, 6400, 1792) and `olympus_dock` (-640, 3200, 1792).
  - With question 5 (b): four vendor houses.
- **A6 (own, the surface):**
  - `entrance:d7_fall` on D1, D2, D4, D5 and D6 at the landings above.
  - D1's `entrance:d7_rope` at the rope's foot (-8192, 14336, 1088), facing 768, and the rope's yes branch to D7's
    `entrance:d1_rope`.
  - `xsbarge` and `xsglow` in `source/textures.yml` after approval.
- **A5:** D3's `entrance:d7_fall` at (-15360, 11776, 1440), facing east (whole cell, flat, 256 clear, no water), at
  D3's next install.
- **A7:** DD-06's and DD-07's roof stairs up to D7's `entrance:dd06_roof` and `entrance:dd07_roof` (question 2).
- **A8:**
  - The roof exits up from DD-02, DD-03 (stage 4), DD-05, DD-08 and DD-14 to D7's `entrance:ddNN_roof` (question 2).
  - DD-15's sky door both ways: DD-15's `entrance:d7_sky`, and D7's `entrance:dd15_sky`.
  - DD-17's roof hatch: `entrance:d7_roof`, and D7's `entrance:dd17_roof`.
  - DD-26's stair: `entrance:d7_stair`, and D7's `entrance:dd26_stair`.
- **S:**
  - the Rest Stop hut (shared with P5);
  - the merchants' barges;
  - the celestial boat moored at Lucio's dock;
  - the Megadragon's binding (11654, a big MM8 dragon);
  - the Sky Bandit body (question 3);
  - the genie lamp (D5/D6's).
- **AU:** wind (X8's); a hum at each corner in its element; dragon calls; the bandits' whistle.
- **Orchestrator:** list D7 in `world.yml` `openAirMaps` at install (outdoor spells in the open air), as X9.

## Blocked

Nothing blocks L1. L2 waits on:
- the decider's answers;
- A2's row 9114 (the game cannot load the map without it, X8's lesson).

L4's walk from `assets_dev` also needs A3's corner and toll hooks, A4's doors, and the planes' `entrance:d7_fall`.
