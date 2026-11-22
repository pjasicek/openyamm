# D3 Sandcaster and the Aging Forest: L1 plan (MU-3, MU-4) for the phase 3 review

A5, 2026-11-20. A plan only: there is no geometry. Nothing is built until a decider has approved the board. The three
YAML files here are written by `output/studio_cal/d3/tools/gen_l1.py`; edit the script, then run
`output/studio_cal/d3/tools/run.sh` (generate, `oymap fmt`, render, the census into `totals`, `oymap validate
--assets assets_dev`, the drawings and the board). Validation: no issues.

## D-28 applied (A5, seventh session)

The decider approved the plan with changes (DECISIONS D-28). Applied in `gen_l1.py`, rerun with `run.sh` (validate: no
issues). The tables below keep the first figures; the measures after the changes:

| Figure | Target | After D-28 |
| --- | --- | --- |
| Height range inside the box (land) | >= 2,500 | **818-3,367 = 2,549** (render's land model; Venom Pond 864) |
| Wrath crest; Lakeside saddle | 3,100-3,400; <= 1,900 | peaks 3,100-3,400 at x 92-100, y 24-37 (two ridges broken by a 2,600 saddle at [98, 27]); the D4 road's saddle 1,850 at [88, 24] |
| West-bank hills; Howling ridge | ~2,400; 1,900-2,200 | 2,400 at [73, 23]; ridge 1,900-2,200 along x 23-27, y 56-98, falling west to D2's 1,300-1,700 |
| POIs (D-20 census) | 35-55 | 52 (the courier's chest moved to the crest's north shoulder; no new POI) |
| Quiet land | >= 1/3 | 61 % |
| First fight, map edges | 2,000-6,000 | D2 road 4,300; D4 road 2,500 |
| Town arrivals (D-15) | buffer 2,500 | square 8,400, caravan yard 5,800 (no jetty arrival: D-28) |
| 6,000 rule; wild land | none over 6,000; <= 0.16 | farthest 5,500 at [65, 72]; 0.087 |
| Encounter areas | 6-30 of 4,096² | dune scrub 6.9, Wrath hills 7.1 (shoulders only), Howling Woods 12.9, Venom fen 13.8 |
| Hostiles; kill XP | 135; 34.8k ±15 % | 135.5; 37.4k |

Changes: the broken Wrath crest east of the river (x 90-102, y 22-40, 6+ cells inside the north edge), the D4 road over
the Lakeside saddle, the Wrath Spring at the head of a gorge between the crest's road shelf and the west-bank hills; the
Howling ridge; the Wrath hills' mantis area drawn round the walkable shoulders (road shelf, north shoulder, south foot),
not the crest; the great oak and its nest moved to (53, 65), about 2,900 east of the forest road, with the oak lane;
Lucio's Jetty departs only (no `entrance:lucio_jetty`, the neighbour listed only); the caravan yard a fenced pocket in
sight of the south gate; Celia and Derek's cottage at [64, 46] on the Venom road about 1,400 from the ring's edge, its
door south toward Venom Pond; the two fruit huts with their own looks and lines (the pear hut on the river's south bank,
the fig hut in the forest; once per character, A2's boons); DD-18's shaft, DD-19's gate and DD-07's door sealed with a
line until their maps are installed; the high path to the crest's north shoulder (the courier's satchel there closes the
6,000 rule at the north-east corner).

## What the plan holds

- **North-west: Sandcaster.** A walled sandstone city on a terrace (1,500) under the last Gemstone crags (D2's range
  ends here, to 3,400), the desert edge north of it. It is 20 x 19 cells and holds all 40 of A4's d3.yml city doors:
  - the guild row on the north wall and the Sky Stair (Lucio's Jetty 4649 on its top) at the north-west corner;
  - the square with the mirror (4612) and Omid's deep well;
  - the temple and Barticus' Gym on the west lane, with DD-18's street shaft beside the gym (D-27);
  - the tavern, first inside the south gate, and the bazaar street to the east gate;
  - the wizard quarter on a raised inner terrace (1,700): five sealed doors (4613-4617) and the guild gate into DD-19,
    open from the start (q-d14.quarter_gate).
  Two gates, south and east, each with the pass check (q-d8.sandcaster_gate). Both open from inside, as D1's gates do.
  The caravan yard (stables 4611) stands outside the south gate.
- **Centre: the Crossroads (1,250).** Six roads meet in a market ring: west to D2, north-west to the city, north to
  the dunes, east over Wrath Bridge, south-east to Venom Pond, south into the Aging Forest. Six striped stalls stand
  between the roads (4641-4646, Caleb's workshop the sixth) with a trough well in the middle. Celia and Derek's
  cottage (4647) is on the Venom road, about 1,500 from the ring (A3's hook says "by the Crossroads").
- **East: the River of Wrath.** It bursts from a cave at the Wrath Spring (81, 21) in the Wrath hills and runs south
  in a cut 300-700 deep. Past Wrath Bridge it turns east through the river meadows and falls off the east rim at the
  Wrath Falls (y 64). On a knoll by the rim north of the falls stands the Great Eastern Tower (DD-07, the key door,
  q-d18.tower_door). The Rim Watch, a ruin with a locker, sits on the bluff over the falls. The bright face's glow
  stands above the east rim (sky).
- **South-west and south.**
  - The Howling Woods on the hills toward D2: mantis ants, the howling stone, the mantis mound, and the smugglers'
    rope over the south rim.
  - The Aging Forest, red and gold: quiet but for three hell hornet nests. It holds the great oak, Cornelius's glade
    (outdoor Perception teacher), a fruit hut, the aged skeleton and the edge cairn. Vespar's ruin, with the emerald
    handle (q-d8.handle), is at its north edge by the caravan road.
- **South-east: Venom Pond and the fen (900).** Thaddeus's hut (4648) and the Fountain of Youth (q-d18.fountain) are
  on its east shore. The drowned skiff is here, and the Fountain of Great Protection by the rims' corner. Cobras live
  in the fen.

## Figures (render_d3.py, `output/studio_cal/d3/mockups/figures.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Obelisk; device kinds | 1; >= 4, one permanent | 1 (dune knoll outside the east gate, obelisks.d3); wells, fountains, shrines, two fruit huts (+2 permanent), cairn, oak; Fountain of Youth (Q-D18) |
| POIs | MAPS 30-40; D-20 35-55 | **52** by the D-20 census (chained within 400; service doors, mirror, gates and dungeon doors in; residences, Cornelius, exits, landmarks out): Sandcaster 20, Crossroads 7, wild 25. See question 1 |
| POI spacing | 1,300-2,600 | nearest-neighbour median 1,830 (720-12,720) |
| Dungeon entrances | 3-6 | 3: DD-18 street shaft (D-27), DD-19 guild gate, DD-07 door; all sealed until their maps exist |
| Outdoor chests | 4-10, a reason each | 8: swallowed caravan, mantis mound, aged skeleton, drowned skiff, mages' cart, smugglers' rope, fallen courier, Rim Watch locker |
| Spawn markers; hostiles at load | 45-70; 135 | 47; 135.5 (117.5 from markers + 18 placed hornets) |
| Kill XP per member | 34.8k +-15 % | 37.4k (+7 %): mantis 11.5k, cobras 9.6k, sand worms 8.8k, hornets 7.5k |
| Encounter areas (4,096²) | 3-8 of 6-30 | 4 + 3 nests: dune scrub 6.9, Wrath hills 8.4, Howling Woods 12.9, Venom fen 13.8 |
| Quiet land | >= 1/3 | 60 % (the nests counted as fight land, radius 3 cells) |
| First fight, map-edge arrivals | 2,000-6,000 | D2 road 4,300; D4 road 2,500 |
| Town arrivals (D-15) | town buffer 2,500 | square 8,400, caravan yard 5,800, jetty 12,500; nearest fight to a city door 3,600, to a stall 3,200, to Celia's cottage 5,500, to Thaddeus's hut 4,300, to Cornelius 2,600 |
| Roads | 1-4 % | 3.1 % road (+ 2.3 % lanes) |
| Height range | >= 2,500 | 900-3,400 (the crags outside the box; inside it 900-2,300) |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest land 5,700 (at [64, 69]); 0.086 of the land over 3,000 from anything |
| Towns | compact | Sandcaster 10.2k x 9.7k, 39 buildings, 10.3 per 100 cells (shipped 3.6-11.2), 14 services: full town_feel at L4. Crossroads: 6 stalls, ring radius 2.8 (`--small`) |
| Textures | outdoor cap 120 | the sandcaster kit and MU-2's D3 ground only; no new textures named |

Monsters: slot 1 Xeen Mantis Dif 1 [2,3] (Howling Woods 12, Wrath hills 12), slot 2 Xeen Cobra Dif 1 [2,3] (Venom
fen 12), slot 3 Xeen Sand Worm Dif 1 [2,3] (dune scrub 11). Placed: three hornet nests, each with five Hell Hornets
(11350, level 35) and one Hornet Swarm (11351, level 42). There is no Hornet Queen (level 50, over C 45).

## Choices

- **Edges:**
  - West, y 44: D2's caravan road arrives at the same y, with a level span 32-56 at 1,300 as D2's east edge. D2's
    other spans continue: crags [0, 32], wooded hills [56, 104], rim [104, 128].
  - North, x 88: the Lakeside road to D4. D4 is not planned, so it aligns to this x.
  - East and south: the world rim at x 104 and y 104 (D-23).
- **The river (D-23):** it rises and falls inside D3, touches no map edge, and nothing crosses D2's edge.
- **Lucio's Jetty (D-5.3):** a timber jetty on the top of the Sky Stair. It is a boat neighbour (route 425) gated on
  m30.done, with an `entrance:lucio_jetty`. A4's d3.yml has no arrival for the return boat (question 6).
- **DD-18 (D-27):** a street shaft with an iron lid against the south-east corner of Barticus' Gym, under his sign.
  It uses the entrance preset ("Descend to the sewer?", D-24) and asks nothing of its own. It is 900 from the gym door
  and off the walking line between that door, the Quiet House's door and the west lane. It stays sealed until A8 gives
  the inside point.
- **The pass:** the caravan yard is outside the walls, so the caravan from Castleview does not bypass Q-D8. Town
  Portal, the mirror and Lucio arrive inside, and the gates open from inside.
- **Moved from the source:**
  - The Eastern Tower moves from F3's middle to a knoll by the rim north of the falls (q-d18 says "by the rim"), so
    that the signature view holds it.
  - Celia and Derek's cottage moves from F4 to the Crossroads, after A3's hook.
- **Kits:** the sandcaster kit. MM8 t07 ochre and orange sandstone in three grades for the houses; MM6 hc pink ashlar
  for the guilds and the quarter; t30 for the walls; MM6 tents for the stalls (plot `kit` names are the studio's mm7
  ones for now: rich, plaster, poor, stone, castle; L3 names the textures). Ground per MU-2's D3 row.

## MU-4 concepts

Two `codex exec` calls (`tools/paint_d3.py`), one per view, no retry, both on the first attempt. The results are
`mockups/raw/d3_arrival_v1.png` and `d3_signature_v1.png`, with prompts and logs beside them.

- **Arrival**, from D2's road at [15, 44] looking east-north-east. It has the walled city on its terrace, the Sky Stair
  with its jetty beam, the pink quarter towers, the Crossroads' tents down the road, Vespar's ruin and the red-gold
  Aging Forest on the right. Against the plan:
  - the quarter reads as a castle, taller than planned;
  - the jetty looks like a crane arm;
  - the rim glow is only a warm horizon.
- **Signature**, from the south bank at [84, 62] looking east. It has the River of Wrath pouring off the rim into the
  stars, the gold glow along the rim, the Eastern Tower at the left and the Rim Watch ruin. It follows the blockout;
  the tower stands nearer than planned.

## Original lines (to wire at L4; A4's flavour file and A3's hooks)

- "Special today! Vulture Repellant, only 25,000 gold!" / "Vulture Repellant doesn't work." (`dark/aaze0031:19`, `:25`)
- "The wizards in this town are sensitive to insults. Watch what you say!" (`dark/aaze0031:29`)
- "Spotting secret doors is an art that has taken many years to master ..." (Cornelius, `dark/aaze0020:1`)

## Quest hooks placed

q-d8.handle (Vespar's ruin), q-d8.sandcaster_gate (both gates), q-d14.quarter_gate (DD-19), q-d18.tower_door (DD-07),
q-d18.fountain (Fountain of Youth), q-c22.cottage (4647), obelisks.d3, M25 (Natasha 4619), Q-D15 (Caleb 4646), Q-D19
(Thaddeus 4648), Cornelius (teachers_plan `cornelius`).

## Open questions for the decider

1. **POI band.** MAPS' D3 sheet says 30-40. D-20 set 35-55 for X4, the other two-town map, once service doors count.
   The census gives 52, of which Sandcaster's 14 services, mirror, well, 2 gates and 2 dungeon doors are 20. Keep 52
   (D-20's band), or cut to about 40 by taking the clicks off the 5 signposts and 3-4 small devices (the 6,000 rule
   then rests on fights and the doors)?
2. **Celia and Derek's cottage.** It is by the Crossroads, as A3's q-c22 hook says. The source has it in F4 by Venom
   Pond. Keep it?
3. **The caravan yard** stands outside the south gate, so the caravans do not bypass the pass. Keep it there, or put
   it inside the walls (the stables are then a free way in)?
4. **Fruit huts.** There are two forbidden fruit huts (+2 Might and Weak; +2 Intellect and Insane; D2's rule), on top
   of D2's one: keep two, or one?
5. **Levels above the sheet's A band 20-28.** The cobras' A is 30 (MAPS names 30/38/45) and the placed Hell Hornets
   are 35. Kill XP is 37.4k against 34.8k (+7 %, inside the 15 % rule). Keep, or cobras at Dif 0?
6. **D4 crossing and Lucio's return.** The D4 crossing is at x 88; confirm it. Lucio's boat back from Olympus needs
   an arrival `sandcaster_jetty`, which is not in A4's d3.yml.

## Files

- Brief: `devdocs/xeen/briefs/d3/L1/{project,plan,sketch}.yml` (this folder).
- Scripts: `output/studio_cal/d3/tools/`:
  - `gen_l1.py`, the brief;
  - `render_d3.py`, the drawings, figures and census;
  - `paint_d3.py`, the Codex concepts;
  - `board_d3.py`, the board;
  - `run.sh`, the whole chain.
- Drawings: `output/studio_cal/d3/mockups/`:
  - `plan_d3.svg`, `plan_d3.png`, `plan_d3_2x.png`;
  - `blockout_arrival.png`, `blockout_signature.png`;
  - `board_d3.png`, `figures.json`;
  - the raw Codex returns in `raw/`.
