## DD-17 Castle Alamar

D6 · L · party 52 → 55 · 50–75 (no boss row) · 70 · treasure 5 (hoard 6) · Story M33 (and Q-D26's roof hatch from D7,
D-58)

![DD-17](act5_graphs/dd17.svg)

The source's Castle Alamar Levels 1–3 (dark maze0049–0051) as one BLV of three floors, 640 apart (0, 640, 1280). Maze
52, "Castle Alamar Dungeon", is FD-01 Alamar Depths (phase 6), not this map. It has 45 review rooms, about 66 sectors,
about 146 M units² and 24 doors (four of them field leaves), plus four bridge slabs. The inner gate, the stair hall's
doors, the true-name gate and Command Central's doors are two-leaf pairs.

- **What it is.** Sheltem's fortress of teal Ancient steel. On L1, four conveyor belts carry the party one way to four
  Lava Heads, and each Head powers an energy field on L2. Behind the fields are four element sundials. Set to nine,
  they raise four bridges over the ring chasms to the true-name gate. Behind the gate a lift rises to L3: the trapdoor
  deck and Command Central, where Corak comes out of the Soul Box to face Sheltem.
- **Critical path.** The route is:
  1. The gatehall (`m33.arrival`) and the Hall of Order.
  2. The west ward. Ride the fire belt to the Fire Head and shut it down. Come back through the west return, then do
     the same with the water belt.
  3. The east ward: the air and earth belts and their Heads, out by the east return.
  4. The stair hall up to the south walk. Round the outer walk, the four sundials behind their dropped fields, each set
     to nine.
  5. The west walk, the dial hall's four bridges and the gate island (`true_name_gate`: Sheltem). The lift core up to
     the deck.
  6. The deck, the Hall of Vengeance, the antechamber and Command Central. The dais plate asks first, then
     `m33.sheltem`, the cinematic and the leave to D6.
- **Off the path.** These rooms lie off the critical path:
  - Dead ends with chests (T5): the robot barracks, the moat watch, the parts store, the watchers' post, the robot bay
    (also the vault lever) and the screen room.
  - The strongroom: the hoard (T6), opened by the robot bay's lever.
  - The power juice: a find (DECIDE 9).
  - The sump under the chasm: a find. It is reached only by falling, and its door opens from inside.
  - The hatch room: Q-D26's hatch to D7.
- **Loops (7).** These are:
  - The four belt loops. The belt goes in, and the Head-side bolted door comes out; after that the loop works both ways.
  - The dial floor's outer walk round the chasm.
  - The chasm loop: a fall to the sump, then back up by the stair hall.
  - The deck loop by the hatch room.
- **Set pieces (4).** These are:
  - The conveyor works: four belts, four Lava Heads ("Fire power field operational."), two elementals of its element at
    each Head.
  - The dial hall: four ring chasms under the deck. Each ring has one bridge slab on the west line, standing level only
    while its sundial reads nine. The ring lips are lit in the elements' colours. The crackling statue and the gate
    stand on the island.
  - The trapdoor deck: a chequer of teal and hatched plates over the chasm; the hatched ones drop to the sump.
  - Command Central: the empty throne, the screens, the Soul Box, Corak and Sheltem, the self-destruct.
- **Monsters (70) and kill XP.** Patrol 50 (11610) × 30, Annihilator 62 (11611) × 20, Autobot 75 (11612) × 6, the
  Lesser Fire, Air, Water and Earth Elementals 55 (11620, 11624–11626) × 2 each at their Heads, and Gamma Gazer 65
  (11572) × 6 in the posts and windows.
  - XP: **68.85k per member** (275,380 / 4) against MAPS's 67.9k: **+1.4 %**.
  - Floor counts: floor 0 33, floor 1 24, floor 2 13.
  - Quiet rooms (D-11.3): the gatehall and the hatch room, the two map doors. The belts, the dial alcoves, the lift,
    the antechamber and Command Central are empty too.
  - Groups of 2–3. Rest encounters 10 % from the robots (DECIDE 11).
  - Sheltem is not a fight (QUESTS M33). He is a placed figure shown by the cinematic (DECIDE 5). Corak is DD-16's row
    11912, placed hidden. Neither is counted.
- **Puzzle answers in the world.**
  - Nine: Atlas in Olympus (npc 5611, topic Nine: "Alamar's birth number is nine"), and each slab rising when its dial
    reads nine.
  - Sheltem: Soul Storage's plaque in Olympus (`m31.true_name_plaque`) and the Pharaoh's M28 line. The crackling statue
    on the island says plainly that a true name is asked for, then crackles.
  - The fields: each Head names its field, and the fields stand in front of the sundials of the same element.
  - The trapdoors: hatched seams, with a hover on the first one.
- **Original lines.** These are used as follows:
  - aaze0049:0: the exit's meaning.
  - aaze0049:2–4: the three propaganda statues, one per floor.
  - aaze0049:5: the crackling true-name statue.
  - aaze0049:6–10: the Lava Heads.
  - aaze0050:0: the lift before the gate opens.
  - aaze0050:1–21: the sundials and the gate.
  - aaze0051:0–3: the Power Juice label, "Come to ME!" and "Command Central".
  - aaze0051:4 ("You Fools!") and the +5 levels are not used.
- **Door to D6.** A6's `door:dd17`, the double gate on the approach (two leaves, the `swdoora` family, D-49). It is
  sealed with a line until DD-17 exists, and is rubble after `m33.done`.
  - **Inside arrival proposed:** `entrance:d6_gate`, in the gatehall about 256 inside the leaves at about
    (0, −3328, 0), facing north (512).
  - **Return:** the exit preset to D6's installed `entrance:dd17_gate` (−6656, 4608, 2208), facing south (1536). This
    matches D6, and FD-01's stair point is the same spot. The refusal and the leave after the cinematic land there too.
- **Hatch to D7.** The hatch arrives at `entrance:d7_roof`, at the ladder's foot in the hatch room, about
  (−2304, 1280, 1280), facing east (0). D7's `entrance:dd17_roof` is at (−18688, 8448, 1536), facing west (D7 L1
  NOTES). Before `roof_unlocked` the hatch reads "Bolted from above."
- **Hooks.** The graph places these:
  - `m33.arrival`: the gatehall (and the hatch arrival, DECIDE 4).
  - `m33.sundials`: the four dial alcoves (`Xeen.alamarSundial`, no hook call).
  - `true_name_gate` and `true_name_wrong`: the island's text prompt.
  - `m33.sheltem`: the dais plate.
  - `q-d26.alamar_hatch`: the hatch room.

  `m33.castle_door` and `m33.robots_gone` are D6's. Map qbits:
  - 117600 `dd17_arrived_once`;
  - 117601–117604 the Heads off (fire, air, water, earth);
  - 117605 the vault open;
  - 117606 "Come to ME!" heard;
  - 117611–117614 each dial at nine (from A3's helper).

  The rest of 117600–117639 is free.
- **Textures.** MM6 Control Center's main sw set (A6's assignment): teal `swll4dk` walls, green grids, `swr2dk`/`swr4dk`
  belt beds, `trekscrn` screens, `swdoora`/`swdoorb` leaves, `xafield` fields (0.5) and `xaenergy` panels. About 36
  of 70 textures; 5 are new: the Lava Head lit and dark, the sundial face, the glyph gate and the trapdoor plate. It
  reads apart from DD-22 (red accents), FD-01 (darker and burnt), DD-16 (Lincoln) and XD-19 (black and gold). Music 50,
  map id 9170.

**DECIDE items** (options in the graph file; the proposed default first)

1. **Conveyor halls.** No floor-current word exists.
   - (a, proposed) A plate at the belt's mouth moves the party in-map to the far end, and a plate there carries it
     forward again. Bolted Head-side doors close the loops.
   - (b) A chain of plates about 512 apart (the source's cell-by-cell carry).
   - (c) A1 adds a floor-current word.

   Depends on: A1 for (c).
2. **Energy fields.**
   - (a, proposed) Four `xafield` leaves before the L2 sundials, each dropped by shutting its L1 Lava Head (one-way,
     D-43).
   - (b) The fields close the Head rooms instead.
   - (c) As (a), and the robots also carry `shields.yml` energy shields while their Head stands (needs an A1 word).
3. **Rings and bridges.**
   - (a, proposed) One two-state slab per ring on the west line, level only while its dial reads nine. This needs
     per-dial qbits from A3's helper.
   - (b) The source's 12 slabs per ring (48 slabs).
   - (c) No rings.

   Depends on: A3, and A1 for a horizontal slab as a door.
4. **After `m33.done`, and the two-way hatch into a castle that self-destructs.** Q-D26 is level 60 and M33 is 53, so
   most parties open the hatch after the castle is gone.
   - (a, proposed) DD-17 is entered only before `m33.done`. The hatch works both ways while the castle stands, and its
     arrival also calls `m33.arrival`. After `m33.done`, D7's hatch stays shut with a new line.
   - (b) After `m33.done` the hatch leads into FD-01.
   - (c) A ruin stage of DD-17.

   Depends on: A3, A6 (D7), the FD-01 lane, and an amendment to D-58 D-5.
5. **Sheltem.**
   - (a, proposed) A placed peaceful row 11924 "Sheltem", hidden until the cinematic, with his own look (S). Corak
     11912 is placed hidden.
   - (b) The cinematic only, with no figures.
   - (c) A boss fight (against M33's story).
6. **The confrontation's start.**
   - (a, proposed) A dais plate asks "Before the throne. Open the Soul Box?", so the room, the strongroom and the
     chests stay reachable first.
   - (b) The hook fires on entering the room.
7. **Where the cinematic sets the party down.**
   - (a, proposed) D6's `entrance:dd17_gate`.
   - (b) A new `entrance:dd17_escape` about 1,024 down the ramp, facing the ruin.

   Depends on: A1 (a leave after `evt.PlayCinematic`, as XD-19).
8. **Trapdoor deck.**
   - (a, proposed) Six hatched `trap` plates drop through the chasm to the sump (1,280), with a hover on the first.
   - (b) A drop to a 640 ledge.
   - (c) A plain deck.
9. **XEEN Power Juice** (the source's +5 levels).
   - (a, proposed) 2,500 experience once per character.
   - (b) +2 Might once per character.
   - (c) Dropped.
10. **Monsters.**
    - (a, proposed) Robots 56, eight Head elementals and six Gamma Gazers: 68.85k (+1.4 %).
    - (b) Robots only: 69.50k (+2.4 %).
11. **Rest encounters.**
    - (a, proposed) 10 % from the robots, one slot. At Dif 5 about 40 % are Autobots (D-46).
    - (b) 0.

**Requests to other lanes**

- **A1:** confirm these:
  - an in-map `evt.MoveToMap` from a step plate, keeping the facing given (DECIDE 1);
  - a horizontal floor slab as a two-state door (3);
  - a `trap` lift dropping through two floors of open air (8);
  - hidden placed actors shown by the cinematic, and a leave after `evt.PlayCinematic` (5, 7; shared with XD-19).
- **A2:**
  - the row 11924 "Sheltem" (peaceful, placed only, unkillable);
  - Castle Alamar in the `where` of the elementals (11620, 11624–11626) and the eyes (11572);
  - the robots' rest slot;
  - the Act V recount: DD-17 68.85k;
  - the Power Juice in the Act V ledger.
- **A3:**
  - `Xeen.alamarSundial` also sets map qbits 117611–117614 while each dial reads nine;
  - the Heads' question "Shut the field down?" and an "offline" line;
  - `m33.arrival`'s `where` adds the hatch arrival, and `m33.sheltem`'s `where` becomes the dais plate's question;
  - the D7 hatch's line after `m33.done` for DECIDE 4 (a), and `q-d26.hatch` reads `m33.done`;
  - the Power Juice's player bits and texts;
  - ORIGINAL_LINES rows for aaze0049:0–10, aaze0050:0–21 and aaze0051:0–4.
- **A4:** none. Atlas's topic Nine (5611) already answers the dials.
- **A6:**
  - D6's `door:dd17` names `arrival: entrance:d6_gate`; the return point stays as installed;
  - D7's hatch after `m33.done` (DECIDE 4);
  - register the five new textures (`xalavahd`, `xalavahdx`, `xasundial`, `xaglyph`, `xatrapplt`).
- **AU:**
  - the belt rumble, the four Head hums and the field crackle;
  - the dial clank and slab grind, the gate's two chimes and the trapdoor clang;
  - the self-destruct klaxon and the castle's groan;
  - D-38's `xeen_vo_sheltem_refusal` and `xeen_vo_sheltem_corak`.
- **S:**
  - Sheltem's look on an existing caster body (DECIDE 5);
  - one Alamar propaganda statue decoration (four uses: three statues and the crackling one, teal metal).
- **FD-01 lane (phase 6):** DD-17 never blocks FD-01's stair. DD-17 is sealed after `m33.done`, and FD-01's stair is in
  D6's ruined gatehouse.

**State and next steps.** The graph, the SVG, the PNG and these notes are written. The render printed no warnings, and
the PNG (`output/studio_cal/a8_s10/png/dd17.png`) was checked by eye. Five state lines are drawn as labels only (the
four fields, the bridges), because their lines would cross the floor bands' boxes. Nothing is built or installed.
Next: the decider answers the DECIDE items, then L1.
