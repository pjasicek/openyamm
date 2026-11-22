## XD-16 Volcano Cave

X7 · M · party 48 → 52 · 42–58 · 40 · treasure 5 · Q-C26 (the two skulls, the way to Shangri-La)

![XD-16](act5_graphs/xd16.svg)

The source's Volcano Cave (xeen maze0046–0048, three 16 × 16 levels, aaze0046–0048) as one BLV of three floors going
down into Mount Firestone, 640 apart (0, −640, −1,280). It has 24 review rooms, about 30 sectors, about 38 M units²
and 7 doors.

- **What it is.** A burning cave behind the demon and devil idols at the mountain's west foot. A demon skull and a
  devil skull keep the way to Shangri-La shut. Break both, and the rock at the bottom of the cave opens onto the
  hidden valley.
- **Critical path.**
  1. The mouth (`entrance:x7_mouth`, quiet), the ash gallery and the fire lake.
  2. Over the crust causeway to the devil skull's island (`q-c26.devil_skull`).
  3. The north shore, the fissure and the iron door to the demon skull's shrine (`q-c26.demon_skull`).
  4. The cinder run to the stair head, down to the stair foot and the lever hall.
  5. The four lever stones lower the four slabs; the gate run and the deep stair.
  6. The obsidian landing, the glass caves, the magma heart's west ledge and the last cave, whose rock stands open
     once both skulls are broken (`q-c26.done`).
  7. The cool passage, and its end into Shangri-La (`q-c26.way`).
- **Off the path.** These rooms lie off the critical path:
  - The smoking passage (a real chest, the source's (15,11)) and the vault of chests: six chests on a dais, five of
    them traps that burst in flame (DECIDE 2), one real.
  - The slag pocket (a chest by an old dwarf's pack) and the steam vents (a chest).
  - The ember pocket (a chest).
- **Loops (3).**
  - Round the fire lake: the north shore, the fissure and the shrine, back by the cinder run to the south shore.
  - Floor −1: the lever hall from the stair foot directly or through the steam vents.
  - Round the heart: in by the glass caves and the west ledge, out by the east ledge and the ash pits.
- **Set pieces.** The fire lake: a tall cavern round a lake of lava lit from below, with the devil skull's black altar
  on an island in the middle. The magma heart: a round pool of lava at the mountain's root with a ring ledge, and
  beyond it the last cave's wall of bare rock.
- **Monsters and kill XP.** Demon 42 (11630) × 20, Devil 50 (11631) × 14, Screamer 58 (11632) × 6: the source's
  demons and devils (its 25 placed) with the family's top tier on the lower floors.
  - XP: **27.34k per member** (109,344 / 4) against MAPS's 26.6k (+2.8 %).
  - Floor counts: floor 0 18 (Demon 12, Devil 6), floor −1 12 (Demon 6, Devil 5, Screamer 1), floor −2 10 (Demon 2,
    Devil 3, Screamer 5).
  - Each skull has the source's guard of three: three Demons in the shrine, three Devils on the island.
  - Quiet rooms (D-11.3): the mouth and the cool passage (XD-17's way back arrives there), the vault of chests.
  - Groups of 2–3. Rest encounters 10 % from the demons (D-39; DECIDE 6). 40 is under M's floor of 45 (MAPS §0's
    count, DECIDE 1).
  - No boss (MAPS §0).
- **Treasure.** Five real chests at T5: the smoking passage, the vault's real chest, the slag pocket, the steam vents
  and the ember pocket. The five trap chests hold nothing (the source's).
- **Original lines.** These are used as follows:
  - aaze0046:0 and :1: the two altars' questions ("… you have a sudden desire to smash it.  Destroy?").
  - aaze0046:4 "You smash the skull." (the 250,000 experience dropped; A3's hook texts follow it).
  - aaze0046:6 "The chest explodes!" and :2 "The chest is empty.": the trap chests.
  - aaze0046:5 "Leave the Volcano Cave?": the exit preset's meaning (D-24).
  - aaze0047:0–1 and aaze0048:0–1 "Down Level?" / "Up Level?": the stairs' signs.
  - X7's "Enter the Volcano Cave?" (aaze0017:1) is A5's door question.
- **Door to X7.** A5's `thing:xd16_mouth` (`door:xd16`) at [66.5, 45]: a 384 × 384 mouth in black rock between the
  demon and devil idols, front at (1024, 9728, 2250), facing west.
  - **Inside arrival proposed:** `entrance:x7_mouth`, in the cave mouth about 256 inside, facing east (0) into the
    cave.
  - **Return:** the exit preset to X7's `entrance:xd16_mouth` (512, 9728, 2250) facing west (1024).
- **Way to XD-17.** The cool passage's end calls `q-c26.way` (true with done) and moves the party to XD-17's
  proposed `entrance:xd16_way`, at the valley's cave mouth. XD-17's way back arrives at this map's proposed
  `entrance:xd17_way`, at the passage's far end facing down toward the last cave. Before done the rock's click is
  the hook's fail text: "Bare rock, hot to the touch. Two skulls in the cave behind you seem to be grinning about
  it." So the game itself points back to the skulls, as X7's idols do.
- **Hooks.** The graph places these:
  - `q-c26.demon_skull`: the shrine's altar.
  - `q-c26.devil_skull`: the island's altar.
  - `q-c26.way`: the rock's click before done (fail text) and the passage's end with done.

  `x7.idols` is X7's. Map qbits: 118050–118053 the four lever stones, 118054 the way's rock drawn open, 118055–118059
  the five trap chests.
- **Textures.** MM7 Thunderfist 7d07 (A6's line, D-45): its dark brown-black rock `c2b`, `cfb1` floors, `DIRT` and
  `7dirttyl` ash floors, 7d07's `Lava` (`floors: lava`), `Ch1b1` and `cwb1` worked stone in the shrines, `7solid01`
  and `t5d1` slabs and doors, `trim9_32` on the altars. About 16 of 45; at most one new (`xvskull`, the altars' carved
  face, optional). Music 7, map id 9142.

**DECIDE items (XD-16)** (options in the graph file; the proposed default first)

1. **Count.** (a) 40 of the demons family, 27.34k (+2.8 %), a NOTES exception under M's 45 (as DD-07, D-39).
   (b) 45, 30.07k (+13 %). (c) 36 demons and four Lava Golems 55, 28.73k (+8 %).
2. **The exploding chests.** (a) Five trap chests that glow and smoke faintly, fire damage 50 on each member once,
   then empty, and one real T5 chest. (b) The same with no tell (the source's gamble). (c) Six ordinary chests with
   the engine's chest traps and loot.
3. **The gate stones.** (a) Four lever stones round a pillar, each lowering one of four slabs in a row, one-way
   (D-43). (b) One lever, one slab. (c) No gates.
4. **The way into Shangri-La.** (a) A rock slab that stands open whenever `q-c26.done` is set, a cool passage beyond
   and an exit to XD-17. (b) A crust bridge rising from the heart's pool (a lift). (c) No door: the exit at the bare
   wall.
5. **Lava.** (a) `floors: lava` (it burns) on the lake, the river and the heart, sunk 128 with crust edges. (b) Light
   and decoration only.
6. **Rest encounters.** (a) 10 % from the demons. (b) 0.

**Requests to other lanes**

- **A2:** row 9142 (encounter 10 %, a demons slot at the highest Dif, cave); the Act V recount (40 monsters,
  27.34k).
- **A3:** ORIGINAL_LINES rows for aaze0046:0–2, :4–6 and aaze0047:0–1; the trap chests' and the lever stones' texts as
  map-local lines; confirm `q-c26.way`'s two places (the rock before done, the passage's end after).
- **A5 (X7, XD-17):** X7's `door:xd16` into `entrance:x7_mouth` once XD-16 is installed. XD-17's arrival from XD-16,
  `entrance:xd16_way`, and its way back to XD-16's `entrance:xd17_way`.
- **A6:** `xvskull` registered if it is made.
- **A4, AU, S, A1:** nothing.

**State and next steps.** The graph, the SVG and these notes are written (lane lead, 2026-11-20, twelfth session).
The render printed no overlap; the PNG from headless Chrome (`output/studio_cal/a7/phase5_graphs/xd16.png`) was looked
at. Nothing is built or installed. Next: the decider answers the DECIDE items, then L1.
