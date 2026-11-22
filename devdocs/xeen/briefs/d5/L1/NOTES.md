# D5 Desert of Doom: L1 plan (MU-3, MU-4) for the phase 5 review

A6, 2026-11-20. A plan only: there is no geometry. Nothing is built until a decider has approved the board. The three
YAML files here are written by `level_generation/xeen_art/phase5/d5_brief.py` (edit the script, then run it, `oymap fmt`
and `oymap validate devdocs/xeen/briefs/d5/L1 --assets assets_dev`: no issues). Drawings, measures and the board:
`level_generation/xeen_art/phase5/` (`d5_render.py`, `d5_concepts.py`, `board_d5.py`; outputs in `d5/`).

## What the plan holds

Source: Darkside C1 (the Quivering Forest, a giant's lair, the energy resistance fountain; dark/aaze0009), C2 (the
Desert of Doom, boulders 1, 2 and 7, the Shrine of Great Power, a lamp, the munchies; aaze0010), D1 (the Northern Tower,
the Parabolic Barrier, Gurodel, Bosco, the Fountain of Might, the broken pyramid; aaze0013), D2 (the Great Pyramid, the
Perishing Sands, boulders 3-6, a lamp, the sewer's exit; aaze0014). Places moved where the design needs them.

- **Centre and south-east: the Perishing Sands** (1,000-1,700): high amber dunes and a white salt pan (90, 92) at about
  1,000, the map's lowest ground. **The Great Pyramid** (DD-15) rises alone from the dunes at (64, 86): 12 x 12 cells at
  its foot, about 3,600 high, great sandstone blocks (MM6 `egybigb`/`egybiga`) under a gilded capstone. Its door at the
  foot of the north face (64, 80): green stone, two leaves (m28.door). A tomb robbers' camp at its south-east corner.
  The **boulder field** by the road (80-90, 79-88): the weathered sign (q-d24.sign) and seven great Enchanted Boulders
  (q-d24.boulder_1-7, answer). A Sandcaster caravan swallowed by the sand at the pan's edge; a genie lamp on a dune
  crest; **the tunnel grate** (DD-18, dd18.d5_grate) in the southern hills' foot at (101, 102).
- **West: the Desert of Doom** (1,300-2,400): stony mesas and dry wadis rising to the western hills (the D6 border,
  2,100-3,000): the obelisk on a red knoll by the road (46, 72); **the Last Water**, a spring pool under palms with the
  Fountain of Endurance (+2, permanent); the **Shrine of Great Power** on a mesa (31, 88); a dead prospector in a wadi;
  a genie lamp in a ruined hill shrine (24, 98); a munchies spot.
- **North: the Griffin Cliffs and the northern highlands** (2,500-3,000, the crest 3,750 at (80, 30)). The cliffs (600-
  1,200 high) run from the pass to the valley; the highland road climbs them in switchbacks from the desert road (74, 73)
  to Highland Fork (76, 53). On the highlands: **Gurodel's hold** (82-91, 43-49), a ring of slabs round his fire, and
  behind it **the great doors of the Giants' Hall** (DD-24) in the hillside (86, 42); **Bosco's Hall** (DD-25), a carved
  stone double door in a crag (61, 46); **the Northern Tower** (DD-08) on a knoll (69, 40) at the Barrier's vertex; the
  Fountain of Might by the rim (102, 31); an abandoned dwarf prospectors' camp (102, 50); the griffins' eyrie on a cliff
  ledge (50, 54).
- **The Parabolic Barrier**: a bowed line of Ancient metal frames from the rim at x 46 to the rim at x 100, its vertex at
  (73, 35), with a shimmering curtain between them (`gn_mtl` frames, `xaenergy` pylons, `xafield` curtain). It cannot be
  crossed; behind it only bare rock and the drop (410 cells, not counted as land). The source has only the name (a
  mirror destination in darkmirr.txt); here it is a landmark (see the open question).
- **North-west: the Quivering Forest** (2,300-3,300): pale aspens that never stop trembling; a wild cyclopes' lair
  (35, 40) with its "Destroy?" device and hoard; the Fountain of Energy Resistance (+5 Air, permanent) at the Barrier's
  west end (47, 29).
- **East: the forest's end.** The level valley at 1,500 out of D4's Forest of Peril (D-36), the last firs; the broken
  travel pyramid on the north slope (95, 72) with its fallen capstone (94, 74): obelisks.dark_hoard.
- **South: the Gemstone spurs**, closed high ground continuing D2's north border (no crossing).

## Figures (`d5_render.py`, `level_generation/xeen_art/phase5/d5/measure.json`)

| Figure | Target (MAPS D5, §0 checklist) | Plan |
| --- | --- | --- |
| Hostiles at load | 110 | 110: markers 47 (lizards 15 x 2.5, birds 21 x 2, cyclopes 11 x 2.5) = 107; placed 3 Griffins at the eyrie |
| Kill XP per member | 52.3k (±15 %) | 55.6k (+6.2 %): lizards 25.4k (Dif 3), birds 15.6k + eyrie 2.1k (Dif 2), cyclopes 12.5k (Dif 1); MM7's tier odds, XP = L(L+10) |
| Monster band | A 32-42, C 55 | Iguanasaurus 42/50/55 (Dif 3), Vulture Roc 30 / Roc 38 / Griffin 48 (Dif 2), wild Cyclops 36 / Giant 50 / Elder Giant 62 (Dif 1). Out of band: 2 % of the cyclopes are Elder Giants 62 (over C 55); 70 % of the birds are Vulture Rocs 30 (2 under A 32, as D4's rocs) |
| The People (peaceful) | — | 6 at the hold (D-47: 11083 Cyclops 38 x3, 11084 Giant 50 x2, 11085 Elder Giant 58 x1, faction `xeen_giants_people`), not in the 110; +3.9k per member on the war route; Gurodel 5452 |
| Encounter areas (4,096²) | 3-8 of 6-30 | E1 sands 6.6, E2 pyramid dunes 6.7, E3 cliffs 9.8, E4 forest 11.8, E5 Desert of Doom 10.6 |
| Quiet land | at least 1/3 | 60 % (the highlands are the giants' quiet quarter) |
| POIs (D-15/D-20 census) | desert band 20-25 | 23 (the boulder field one set piece; 30 if each boulder counted); spacing median 6,250 |
| Outdoor chests | 4-10, a reason each | 6: the lair's hoard, the eyrie, the caravan wreck, the prospector, the dwarf camp, the robbers' camp |
| Dungeon entrances | 3-6 | 5: DD-15, DD-08, DD-24, DD-25, the DD-18 grate |
| Obelisk; devices | 1; >= 4 kinds, one permanent | 1; fountains x3, shrine, lamps x2, boulders, capstone, lair; permanent: Endurance +2, Air resistance +5 |
| Relief inside the box | >= 2,500 | 987-3,566 (2,579) on the drawing's model; the crest point is 3,750 |
| First fight, edge arrivals | 2,000-6,000 | from D4 (105, 80): 4,000 (E1); from D6 (23, 64): 3,070 (E5) |
| Dungeon-exit and town arrivals | 6,000 rule; Bosco's town buffer 2,500 | grate 2,610, pyramid 3,980, Bosco's door 2,700, DD-24 doors 7,400, tower 7,330 |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest 5,540 at (108, 40); 0.11 |
| Roads | 1-4 % | 1.2 % roads + 1.4 % lanes |
| Textures | phase 5 outdoor cap (<= 12 new beyond the kits) | 2 proposed (below) |

## Edges

- **East, D4 (D-36 (7)):** the crossing at y 80, the level valley at 1,500 (D4's x 19 column: 1,504-1,536 at y 76-84).
  D5's east border column x 109 carries D4's installed x 19 column cell for cell (border points one cell in, the
  drawing's model forced exactly: difference 0 on every span; `d5/edge_d4.json`). D5's east rim repeats D4's west-rim
  spans word for word. Arrival `entrance:d4_road` (105, 80) facing west; the road runs out to x 127 at y 80.
- **West, D6:** the Forbidden Zone pass at y 64, 1,700 over y 62-66 (`edge_d5_d6.json`, unchanged). D5's west column
  x 19 carries the file cell for cell (difference 0; `d5/edge_d6.json`). The west rim repeats D6's east-rim spans and heights
  ([0, 24] level 0; [24, 58] ridge 2,600-3,300; [58, 70] level 1,700; [70, 128] ridge 2,500-3,000). Arrival `entrance:d6_pass` (23, 64) facing east.
- **South, D2 (no crossing):** D5's y 109 row continues D2's installed y 19 row (mean difference 11; 320 only at the
  corner x 19, where D6's file wins), falling from x 100 to D4's 1,248 at the south-east corner (D2's row there is
  2,500: the corner follows the crossing neighbour). The south rim repeats D2's north-rim words (the Gemstone Range).
- **North: the world rim** at y 24.

## Double doors and texture fit (the user's rules of 2026-11-20, for L3/L4)

Build these as **two leaves** with mirrored wing pictures, opening apart:

- **The Great Pyramid's door**: green stone with the Pharaoh's sign (m28's fail text); proposed new `xdpyrdor`, one
  wing used mirrored on the pair (MM6 `egydrlgl`/`egydrlgr` as X6's Sphinx if green stone is not wanted).
- **DD-24's great doors** (D-47): two leaves 384 x 512, A7's new `xdgiantd` (one wing, mirrored on the pair).
- **Bosco's Hall**: a carved stone double door (MM7 Stone City 7d24's dwarf doors or `t09a03a`/`t09a03b`).
- **The Northern Tower**: two iron-bound leaves (`hkm1dl`/`hkm1dr`, towers kit); the lintel "Grnd rdr f Vwlss Knghts"
  as one sign picture placed once over the door: proposed new `xdvowel`.
- **The grate** is a grate (one leaf), not a double door.

Texture fit: the pyramid's courses tile only along their seamless axis; a hieroglyph or dragon frieze (the signature
concept's band round the foot) only along its axis; the tower one window per storey per face.

## Textures

Kits first: the ancient kit (Barrier, broken pyramid: `gn_mtl`, `xahull`, `xafield`, `xaenergy`), the towers kit
(Northern Tower), MM6's Tomb of VARN set for the pyramid (`egybigb`, `egybiga`, `egytrma`), MU-2's D5 ground row
(sand_ripples, dirt_cracked, rock_red, snow, soil_stony) and dressing (tree62c, tree63b, tree28, rock10/14/24, plant50/
54). Proposed new (2 of 12): `xdpyrdor` (the pyramid's green-stone door wing: m28 names it), `xdvowel` (the Voweless
Knights' lintel: q-d17 names the line). `xdgiantd` is DD-24's (A7, D-47). None made now.

## MU-4 concepts

Two `codex exec` calls (`d5_concepts.py`), one per view; raw returns, prompts and logs in
`level_generation/xeen_art/phase5/d5/raw/`.

- **Arrival** from D4 (105, 80) looking west (`d5_arrival_v1.png`): the last firs, the road past the boulder field, the
  pyramid far off, the broken travel pyramid right, the cliffs and the Barrier faint. Against the plan: a paved road
  (the plan: a stony track), the broken pyramid nearer, the boulders smaller.
- **Signature**: the Great Pyramid from the dune crest (82, 98), about 60 degrees, looking north-west
  (`d5_signature_v1.png`). Chosen over the boulder field: the pyramid is the map's name and story (M28-M30) and is
  seen from both arrivals. Against the plan: stepped courses and a dragon frieze (kept as an L3 idea), trees left.

## Quest hooks placed

m28.door (pyramid), q-d17.tower_door (tower), q-d24.sign / boulder_1-7 / answer / answer_wrong (boulder field),
obelisks.d5 (knoll), obelisks.dark_hoard (capstone), dd18.d5_grate (grate); DD-24's doors with `entrance:d5_hold`
(D-47); Gurodel 5452 at his fire.

## Requests (via the orchestrator)

- A2: map_stats 9112 with the three slots (Xeen Iguanasaurus Dif 3 [2,3], Xeen Roc Dif 2 [1,3], Xeen Giant Dif 1
  [2,3]); the People rows 11083-11085 (the sketch names 11080-11082 until they exist: validate refuses unknown rows);
  the Act V recount with D5 at 55.6k.
- A3: Q-D27 hooks for D5's two lamps (aaze0010:11-14, aaze0014:15-18); the Shrine of Great Power, the three fountains
  (aaze0009:3-5, aaze0013:9-11) and the lair's "Destroy?" (aaze0009:1-2) as map hooks or map-local lines with rescaled
  values; the munchies line (aaze0010:18); the six boulders' "leaves behind..." treasures after q-d24.solved; "The pyramid
  portal has been destroyed." (aaze0013:12) on the broken pyramid; check the qbit numbers in project.yml (marked A3).
- A7: DD-24's inside arrival `entrance:d5_hold` as in its notes; D5's return point (86, 43) facing south.
- A8: inside arrivals for DD-15 (the green door), DD-08 (the tower door) and DD-25 (Bosco's door); DD-18's
  `exit:d5_grate` lands at D5 (101, 102) facing north.
- S: the Enchanted Boulder model (a great rock with a weathered face), the genie lamp (shared with D4), the People's
  look on the MM8 cyclops / MM9 giant (with DD-24).

## Open questions

In the board (`level_generation/xeen_art/phase5/d5/board_d5.png`) and the report's DECIDE list: the People's count,
the forest's giants, the boulders' census and treasure, the Parabolic Barrier, the fourth +2 Endurance, the pyramid's
size, the broken pyramid's place, the rescaled devices.

## D-49 applied (A6 sub-agent, 2026-11-21)

`d5_brief.py` carries the decider's changes (`D49_DECISION.md` wins over the text above where they differ):

- **Boulders in two clusters** (change 1, Q3): the sign and boulders 3-6 by the desert road (85-86, 80-82), boulders 1,
  2 and 7 by the west road (37-38, 70-71; about 5,000 from the obelisk knoll and 6,000 from the Last Water). Each a
  chained ring within 400: one spot each. POIs 24 (cap 25 at L4). No chests. After `q-d24.solved` the six crumble and
  are hidden (A3's `crumbled_1-6`); the seventh gives 12529.
- **The broken pyramid is one spot** (change 2, Q7): the fallen capstone within 400 of the pyramid's click, by the road
  (95, 72-73).
- **The People** (Q1): six on 11083 x3, 11084 x2, 11085 x1 (faction `xeen_giants_people`), Gurodel 5452 on 11085;
  not counted. The Quivering Forest's wild cyclopes on 11080-11082 (slot 3), hostile (Q2).
- **The Barrier** (change 4, Q4): Ancient frames and an `xafield` curtain, a blocking BModel to the fly ceiling; no
  event, not a POI. The rim rule `rim: {cliff_y: 24, fall: death, sides: [north]}` in project.yml.
- **The Last Water** gives **+2 Luck** (A2's swap of D-49 Q5's Accuracy: the least-served permanent stat);
  `d5.last_water` is A3's hook.
- **Band** (change 3): A 30-42, C 62.
- **Qbits and items** checked against A3's files: m28.started 111560, Key to the Ancient Pyramid 12348, q-d17.key
  113341; hall_attacked 113323, lair_destroyed 116180 and crumbled_1-6 113481-113486 added.
- **POI spacing** (change 5): the median of about 6,250 is accepted: 20-25 POIs on about 7,200 land cells cannot reach
  a 1,300-2,600 median; the 6,000 rule (farthest about 5,540) and the wild-land figure (0.11) hold (as D-40's line for
  X7).
- **The four-map corner** (Q6): the shared edge file's y 106-109 now blend to D1's installed corner (2,636 / 2,440 /
  2,260 / 2,176); D5's x 19 column carries it cell for cell. The installed D1 and D2 disagree at the four-map point
  (2,176 against 2,496); there is no crossing there, and it is left as is.
- **Textures** (change 8): `xdpyrdor` (the pyramid door's wing, mirrored on the pair) and `xdvowel` (the Voweless
  Knights' lintel, once) are the lead's; DD-24's doors `xdgiantd` (A7's); Bosco's door shipped `t09a03a`/`t09a03b`;
  the Northern Tower `hkm1dl`/`hkm1dr`.
