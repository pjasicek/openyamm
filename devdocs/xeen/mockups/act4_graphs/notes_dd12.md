## DD-12 Dungeon of Lost Souls

D4 (the Isle of Lost Souls, by ferry) · M · party 37 → 39 · 38–55 (MAPS 35–55) · 45 · treasure 4 (hoard 5) · Story
M24; Q-D25, Minotaur Lord

![DD-12](act4_graphs/dd12.svg)

The source's five-level dungeon (dark maze0078–0082, texts aaze0078–0082) becomes one BLV of five floors. The floors
go down 640 apart from the ruined tower's base: L1 at 0, L2 at −640, L3 at −1280, L4 at −1920, L5 at −2560. Each floor
has one of A3's five cheerful gates (`m24.gate1`–`gate5`, Yes opens). Each floor also keeps the source's own puzzle:
hourglasses, levers, dials and the Soul Waters, the lever riddle, and the Soul Maze with the birds. The map has 35
review rooms, about 38–42 sectors and about 40 M units², of which the maze is about 14.

- **Monsters:** only the minotaur family, as in the source (D37 Minotaur and D38 Gorgon, Lost Souls 1–5) and MM7's
  Maze: Minotaur 38 (30), Gorgon 45 (12), Minotaur Lord 55 (3). In the story they are the coven's rejects (q-d22's
  prisoner: "the rejects end up on the Isle of Lost Souls"). As in the source, the strongest are at the bottom: L1 8,
  L2 9, L3 9, L4 9, L5 10. The entrance hall (the arrival, D-11.3) and the third and fourth gate halls are quiet. A Minotaur Lord
  keeps the Reserve, another the maze's heart, and the third the fifth gate.
- **Path:**
  - **L1:** D4's double door; the entrance hall in the ruined tower's base (D4's hkm2 rubble, its broken roof open to
    the sky); the carved plaque and the first gate. Then the hall of storage and its four "Minotaur Storage" rooms
    (stores) to the stair head.
  - **L2:** the speaking statue; north or south walk round the cell block to the second gate.
  - **L3:** the stagnant pool; the gallery of dials and the Soul Waters, or the flooded walk and the Negative Soul
    Waters; then the third gate.
  - **L4:** the plaque's riddle; the hall of levers; the fourth gate.
  - **L5:** Alamar's four statues at the maze's mouth; the Soul Maze, west then east; the fifth gate (a Minotaur Lord);
    the aviary and the Songbird of Serenity.
- **Off the path:**
  - L1: the hourglass vault (T4), which opens once all four hourglasses are flipped.
  - L2: the cells of the lost. Three levers raise three cells' bars and the fourth lever is stuck: two finds and a T4
    chest.
  - L3: the Negative Soul Waters (T4; drinking costs a tenth of HP and SP, never kills).
  - L4: the Minotaur's Private Reserve (the hoard T5 and the second Soul Waters) behind the riddle's lever; the
    barracks (a find).
  - L5: the heart of the maze (the horned throne, Q-D25); the maze's dead end behind an illusory wall ("An
    illusion!", T4).
- **Loops (6):**
  - the two ways through Minotaur Storage;
  - north and south round L2's cells;
  - L3's dry and wet ways;
  - L4's barracks;
  - the maze's halves, which meet directly and again at the heart;
  - after the Songbird, the lift from the aviary to L1's lift head (open question 2).
- **States:**
  - **The key:** Megan's `lost_souls_key` on D4's door (D-12.1: the Isle's only gate).
  - **The gates:** Yes opens a gate's two leaves, and they stay open; No calls `gate_shut`, the gate stays shut and
    asks again, with no wave.
  - **The hourglasses:** four map variables, which open the vault panel.
  - **L2's levers:** three two-state cell bars.
  - **L3's dials:** four map variables. All at 4, then the lever, and the Soul Waters run; otherwise "The lever is
    stuck."
  - **L4's riddle lever:** row three of four from the north, the east lever. It opens the Reserve's door; the other
    eleven levers are stuck.
  - **The lift:** `m24.bird_freed` starts it.
  - **The throne:** `q-d25.done`.
- **Exits (the `exit` preset, D-24):**
  - One door, both ways: the inside face of the entrance hall's double door.
  - Inside arrival **`entrance:d4_isle` at (0, −352, 0)** in the map's frame. The frame has x east, y north and z 0 on
    L1's floor; the entrance hall is round, radius 512, centred on (0, 0), with the door in its south wall at y −512.
    The party faces north (MoveToMap 512), with the carved first gate ahead.
  - The way out lands at D4's `entrance:dd12_door` (72, 67), a step south of the tower's door, facing south (1536)
    down the path to the jetty (72, 73) and the ferry back (`poi:isle_boat`, house 4667). The exit means "leave for the
    Isle". D4's "Enter the Isle of Lost Souls Dungeon?" (aaze0022:0) is the entrance's meaning.
- **Hooks (all 11 placed):**
  - The entrance hall: `m24.arrival` (the first entry's message and the plaque's click) and `m24.gate1`.
  - The gate halls: `m24.gate2`–`gate5`; `m24.gate_open` and `m24.gate_shut` at every gate.
  - The aviary's last cage: `m24.songbird`.
  - The horned throne at the maze's heart: `q-d25.throne` and `q-d25.throne_again`.
- **Answer-givers:**
  - The gates: the carving ("Answer gladly and the way opens", `m24.arrival`) and Megan's M20 line ("all doors that
    ask you to cheer up").
  - The dials: L3's statue.
  - The lever riddle: L4's plaque.
- **Textures:** The Maze, MM7 d02, as A6's `dungeon_families` assigns it (eswamp, cwb1, cwb, cfb1, ceb1sa, t5s1c,
  c1d1, trim12_32). The entrance hall uses D4's towers kit (hkm2b, hkm2bw, hkm2d) to match the ruined tower. The Soul
  Waters are mm7 7wtrtyl, and the cages and cell bars XD-04's `xwcage`. About 22 of 45 textures, 3 new:
  - `xlsplaque`: the carved plaque, once.
  - `xlsgate`: one wing of a "think positive" gate, a smiling half-sun behind iron bars, mirrored on the other leaf.
  - `xlsglass`: the hourglass niche, once per face.
- **Dressing and lights:**
  - The entrance, the five gates and D4's door are double doors (two leaves). The storage doors, the Reserve and the
    barracks have single leaves.
  - L1's four storerooms are stores, with clumps by the walls and none on the line between their doors. The Reserve's
    casks stand in pairs.
  - L4's lever posts stand in four rows of three with clear aisles.
  - The maze has wall torches at its turns. Braziers stand on the floor beside the throne's dais and between Alamar's
    statues, clear of the maze's mouth. A lamp hangs in each aviary alcove's head.
  - Minotaurs are 200 high (radius capped at 60, D-32). The maze's corridors are 256 wide and 384 high, and nothing
    needs to be kept in.
- **Lines:**
  - aaze0078: the plaque, "Minotaur Storage", the hourglass.
  - aaze0079: the statue's lost-souls speech, the levers, "The lever is stuck."
  - aaze0080: the stagnant water, the Soul Waters, the dials and their statue, the Negative Soul Waters.
  - aaze0081: the lever riddle, "Minotaur's Private Reserve", the second Soul Waters.
  - aaze0082: Alamar's four verses, "An illusion!", the six stat birds, the Parrot of Prophecy, the Songbird.
  - The source's "How could you be so negative? Begone!" stays in the ledger. A3's `gate_shut` text is used.

**Kill XP against MAPS §0.** 30 × 1,824 + 12 × 2,475 + 3 × 3,575 = 95,145, which is **23.79k per member**, +1.2 % on
DD-12's row (23.5k).

**Outdoor door check (D4 L1, `briefs/d4/L1/`).** D4's `entrance:dd12_door` at cell (72, 67) faces south. Its door is
`door:dd12`, two leaves (hkm2d1/hkm2d2), with the condition `lost_souls_key`. This matches the graph's one door, both
ways. Points for A6:

- **The inside arrival.** `entrance:d4_isle` at (0, −352, 0) in DD-12's frame, facing north. D4's `door:dd12` names it
  as its `arrival` (D-37).
- **Where the tower stands.** The tower's door at (72, 67) is two cells north of the knoll's top (72, 69, 1,400), so
  the path from the jetty climbs over the top and down to the door. Either keep that, or stand the tower on the top
  with its door on the south face at about (72, 68.5).
- **A refusal without the key.** For example: "Locked. Two iron-bound leaves, and a keyhole." (A3's text if wanted.)
- **The tower's look.** The entrance hall is the tower's ground floor: round, about 1,024 across, roof broken open. The
  outside should show a ruined round tower of at least that width with no upper floors to enter.

**Open questions** (options and recommendations in the graph file):
1. Families: the minotaur family only, 30/12/3 (proposed), or a ghostly second family (Tomb Terror 40 or a new "Lost
   Soul" tier).
2. The way back: a two-stop lift from the aviary to L1 after the Songbird (proposed), walking back, or a second Isle
   door.
3. The Soul Maze spells SHELTEM in its walls on the automap, with the throne in the L (proposed), or a plain labyrinth.
4. The birds: six stat birds at +2 each for the party present, once each (proposed; +12 per member), three, or none.
5. The Soul Waters: experience once per member, L3 1,000 and L4 2,000 (proposed), +5 resistances, or flavour only.
6. A No at a gate: it stays shut and asks again, with no wave (proposed); a hidden pair shown; or "Begone!" back to the
   entrance.

**Requests:**
- **A6:**
  - Register `xlsplaque`, `xlsgate` and `xlsglass` in `textures.yml`.
  - On D4's `door:dd12`, name `arrival: entrance:d4_isle` (0, −352, 0, facing north).
  - The tower: its width, its place on the knoll and the refusal line.
- **A3:** two player bits and texts for the Soul Waters (if 5a). The birds', dials' and riddle's source lines go in the
  ORIGINAL_LINES ledger. Q-D25 is level 32 while DD-12 is 37–39; align it if wanted.
- **A2:** confirm the mix (11090–11092: 30/12/3, 23.79k). Record the birds' +2 × 6 (if 4a) and the Soul Waters'
  experience (if 5a) in the Act IV ledger.
