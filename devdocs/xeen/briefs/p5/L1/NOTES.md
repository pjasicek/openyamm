# P5 Clouds of the Ancients: L1 plan (MU-3, MU-4) for the phase 6 review

A5 sub-agent, 2026-11-21. This is a plan only: there is no geometry, no L2-L4 and no build. Nothing is built until a
decider has approved the board (`output/studio_cal/p5/mockups/board_p5.png`, small copy `board_p5_small.jpg`).

`output/studio_cal/p5/tools/design.py` holds the design as data (after X9's). `gen_l1.py` writes the three YAML files
here (plan, project, atmosphere). To change them, edit the design, then run `output/studio_cal/p5/tools/run.sh`. It
renders and measures (`render_p5.py`: the plan, the two blockouts, `figures.json`), writes the brief with the census
in `totals`, runs `oymap fmt`, `fmt --check` and `oymap validate --assets assets_dev`, and draws the board. The Python
steps run under an 8 GB cgroup cap. `paint_p5.py walk|shrine` makes one `codex exec` image call per view.

Validation: `fmt --check` is clean and `validate` reports no issues. The shape is X9's L1: an open-air BLV region
(`kind: indoor`, `profile: region`), the clouds as spaces with `at` (the middle, map units) and `extent`. Point
positions are in each point's `notes`, because an L1 plan has no point coordinates.

## D-56 applied (A5, sixteenth session, 2026-11-21)

`D56_DECISION.md` wins over this file where they differ. Applied in `output/studio_cal/p5/tools/design.py` and
`gen_l1.py` (the pre-D-56 copies `*.pre_d56` beside them), then `run.sh`: `fmt --check` clean, `validate` no issues.

- Q1-Q3, Q4, Q9 as drawn: one ring (29,137), no monsters, falls to X5's `entrance:p5_fall`; the note on its post at
  (4096, -4224), 547 from the stair house's door; `xeencloud`, X9's daylight block, no weather, `view_distance_scale`
  1.5.
- Change 3: the Pharaoh, Roland and the wedding Kalindra (a new row keeping npc 5001, not 11918) are peaceful,
  placed-only, uncounted, NoArena figures, made unkillable by the map's load event
  (`SetMm9ActorCanReceiveDamage(false)`).
- Change 4: `decor:cube` (-384, -320) and `decor:scepter` (384, -320), in the hands, are the installed item models
  (`item_xeen_12365.glb`, `item_xeen_12366.glb`) as S's scaled decorations, hidden until `state:wedding` (the
  cinematic's first event cue shows them).
- Change 5: `set:unification`'s rule now reads click, cinematic (every gameplay step an `event` cue; the voice only
  from the cue), the hook's narrative text once in the done event, then the certificate (never during the cinematic).
- Change 6: the fade to white uses A1's fade colour; black if A1 declines (final).
- Change 7, Q10: `poi:disc` (1216, 320), east of the pavilion's open south side and off the walking line, shown with
  `state:wedding`, moves the party to `entrance:fd03_roof`. The stair house's door is the way down both ways.
- Change 8: Dungeon M, at most 13 new textures, lettered by script in Fondamento (SIL OFL, shipped in
  `assets_dev/engine/fonts/truetype/`, licence `fondamento_ofl.txt`), source spellings ("Planets Edge").
- Change 9 (concept corrections) and change 10 (falls in D-54's shape) are L3 and L4 work.
- Census: **19 POIs** (D-20), the disc added; `state:wedding` shows the pavilion, the couple, the cake, the gift, the
  Cube, the Scepter and the disc.

## The source

The Clouds of the Ancients, MM5 maze 129 with x181-x183 (a 32 x 32 sky), its events and its text `dark/aazex129`
(`reference/mm4_5_world_of_xeen/unpacked/maps/dark_initial_state/mazex129.*`; read for layout and text, nothing
copied). Decoded (`output/studio_cal/p5/src/`):

- **One cloud road** over open sky. It leaves Darkstone Tower's roof in the south-east corner (a walled cupola at
  (28-30, 0-2); its door square (29,2) asks "Descend into Darkstone Tower?", :14; the run position is (29,3)). It
  spirals inward, counter-clockwise (north, west, south, east, and in again), for **358 squares** to the middle.
- **The Pharaoh's note** (:15) is at (29,7), **two squares from the arrival**, before the first stop.
- **Eight "Rest Stop" signs** (:0) stand along the road, 23 to 335 squares from the arrival.
- **Nine game-name signs** (:2-10) stand in the four corners of the sky, off the road: south-east (by the cupola)
  "Inherit the Earth", "King's Bounty", "New World Computing"; north-east "Empire Deluxe", "Spaceward Ho!"; north-west
  "Planets Edge", "Vegas Games"; south-west "Tunnels and Trolls", "Nuclear War".
- **"Might and Magic"** (:1) is the last sign, at the road's end (12,17), beside the shrine.
- **The shrine** at (13,15): the Dragon Pharaoh (an object sprite), "Dragon Pharaoh, Guardian of Xeen" (:12), the
  refusal (:13), and the checks: the Cube, the Scepter and the four sleeper awards.
- **"The observatory is closed."** (:11) has no event in the source; A3's m42 gives it a door.
- **No monsters** (the MOB has none) and no chests.

## What the plan holds

**The idea:** the long way round. The source's spiral becomes one square ring of cloud road, 7,168 on a side, round
the shrine's high cloud in the middle. The shrine is in sight across 1,155 or more of open sky for the whole walk.
The road is a highway in the sky: 768 wide, a dashed line of cloud-stone flags down its middle, Rest Stop huts beside
it, and billboards on its outer shoulder naming the source's games in the source's corners. Then a causeway turns in.

**Room:** 26 x 26 cells (13,312 a side). North is up; x runs east and y north, with the shrine's middle at (0, 0).
Floors are over the arrival (0). The road climbs 64 at each pad, to 448 at the last Rest Stop; the shrine is at 512.

**The walk**, in order (distance along the road from the arrival; `figures.json` `stations`):

| Along | Space (floor) | What |
| ---: | --- | --- |
| 0 | Darkstone's crown (0) | Arrival `entrance:fd03_roof` (4608, -3968), facing north, out of the stair house: a small black copy of Darkstone's crown (radius 448, X5's black stone, skull frieze and slate cone) standing up through the cloud. Its door (4608, -4416) is the way down. |
| 217 | | **The Pharaoh's note** on a post by the door (4096, -4224): `m42.pharaoh_note` (question 4). |
| 1,361 | | 'New World Computing', on the crown's west rim facing the arrival. |
| 2,257 | the east road | 'King's Bounty'. |
| 4,433 | The first Rest Stop (64) | A Rest Stop hut on the outer (east) side (4352, 0), facing the road. |
| 6,225 | the east road | 'Inherit the Earth'. |
| 8,017-9,297 | The north-east turn (128) | 'Empire Deluxe' on the outer corner; 'Spaceward Ho!' after the turn. |
| 11,601 | The observatory (192) | A round pale-stone tower with a copper dome (0, 4672), radius 576; its door (0, 4096) faces the road: `m42.observatory`, "The observatory is closed." |
| 13,905-15,185 | The north-west turn (256) | 'Planets Edge'; 'Vegas Games' on the outer corner. |
| 18,769 | The second Rest Stop (320) | A hut on the outer (west) side (-4352, 0). |
| 22,353-23,633 | The south-west turn (384) | 'Tunnels and Trolls' on the outer corner; 'Nuclear War' after the turn. |
| 25,937 | The last Rest Stop (448) | A hut on the outer (south) side (0, -4352). The causeway leaves north from here. |
| 28,113 | the causeway's head | 'Might and Magic', the last sign (-640, -1408), facing the causeway (the source's (12,17)). |
| 29,137 | The Pharaoh's shrine (512) | **The dais** (0, -384), 1,024 x 704 and 64 high, facing south: two great stone hands 768 apart, held up open, 448 tall. `m42.shrine`. **The Dragon Pharaoh** (npc 5453) stands behind it (0, 192) (question 5). |

After the ceremony (`state:wedding`, m42.done 111840): **the pavilion** (0, 960), white canvas and gold on four posts,
1,536 x 1,024, open to the south. Under it stand **Prince Roland** (-224, 960) and **Queen Kalindra** (224, 960)
(question 6). Inside are **a cake** on a table (576, 832) and **the wedding gift** chest (-576, 1088) (question 7).

Boards that stand off a pad stand on a small lobe of cloud pushed out 640 from the road's middle line, so their legs
are off the road. Huts stand on the pads' outer sides. Nothing stands on the walking line (the dressing rule).

**No short cut:** the crown and the last Rest Stop are 1,445 apart over the sky, and the stop is 448 higher.

**Ways in and out:**

- **In:** FD-03's roof stair, once M41's seal is broken (m41.seal_broken 111820), comes up into the stair house at
  `entrance:fd03_roof` (4608, -3968, 0), facing north (MoveToMap direction 512).
- **Down:** the stair house's door, an `exit` preset (D-24) whose meaning is the source's "Descend into Darkstone
  Tower?" (aazex129:14), to FD-03's `entrance:p5_stair` (A7 names it). The source settles the way back. It is the
  same door both ways, so the plan's entrance is `kind: both`.
- **Falls:** as X8 and X9. They land on X5 at (-4608, 2304), on Darkstone's rock top (ground 1,500), 224 before the
  tower's north door and facing it (south, 1536). This is X5's `entrance:p5_fall` (A6; question 3). X5's tower is
  A6's `thing:darkstone` at cell [55, 61], (-4608, 1536). Its base radius is 544, its door is on the north face, and
  the rock's top is about 2,048 across.
- **After the ending:** question 10.

## The ending (`set:unification`)

A3's `m42.shrine` (requires the Cube, the Scepter and m38.fire/air/earth/water; takes the two; sets done; award 417;
40,000 experience; D-38's voiced line) starts the cinematic `unification`. A5 writes it in `xeen_p5.cinematics.yml`
at L4, in the format of `devdocs/mm9_rework/MM9_CUTSCENES.md`. It is skippable and about 35 s long:

1. Close on the dais. The Cube and the Scepter are set in the hands (a decoration show, or S's held models). The
   Pharaoh's line "Let the two faces of Xeen be one world again." (`xeen_vo_pharaoh_unification`) plays, with a
   subtitle.
2. A rising pull-back over the ring. Four far chimes: the sleepers answer.
3. Up into the sky and a fade to white: "the sky turns over". An `event` cue shows `state:wedding` (the pavilion,
   the couple, the cake and the gift) while the screen is white. It is a gameplay step, so it also runs on a skip.
4. Fade in on the pavilion: Roland and Kalindra under it, the Pharaoh turning to them with his book (an actor `face`
   cue). A subtitle.
5. The party's own view. The done event gives the completion certificate (A4's `world.yml` `completion`).

A load event on m42.done shows the same state on every later visit.

## Figures (`render_p5.py`, `output/studio_cal/p5/mockups/figures.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Size | MAPS: small | Room 26 x 26 cells. The clouds span 19.9 x 21.8 cells. |
| Walkable cloud | X9 272 M, X8 124 M | **53.8 M units²** |
| The walk | the source: 358 squares | **29,137** from the arrival to the dais: 76 s walking (384 a second), 38 s running. Road spans are 1,513-2,201 between pads; the causeway is 1,374. |
| Sky round the shrine | no jump across | 1,155 at the least (to the observatory's pad) |
| Monsters | none (or a last guardian) | **0** (question 2) |
| Points of interest | small | **18** by the census (D-20: chained within 400): 10 boards, 3 Rest Stops, the note, the way down, the observatory's door, the shrine and the gift. 17 without the gift. The nearest-neighbour median is 1,985 (547-3,746). |
| Chests | treasure 6 | 1, the wedding gift (T6), after m42.done (question 7) |
| Heights | - | The crown 0; the road +64 a pad, to 448; the shrine 512 |
| Hooks | m42 by name | m42.pharaoh_note, m42.observatory, m42.shrine; state:wedding on m42.done |
| Original lines | at least 3 | aazex129:0-15, all of them |
| Textures | S 30 (4 new), M 45 (8 new) | About 20 with blank boards; about 30 with lettered ones (question 8) |

**Texture estimate** (shipped and kits first; L3 confirms the names):

- the cloud top and side (X8's `xccloud`, `xccloudsd`);
- X9's cloud-stone flags;
- X5's Darkstone set (`gtrlwal1`, `hkm3b`, `xtslate`, `7solid01`);
- the huts: a plank wall, shingles and the bench wood (3);
- the observatory: pale stone, copper and a door (3);
- the shrine: pale gold paving, gold trim and the hands' stone (3; DD-15's kit if it fits);
- the pavilion: white canvas and gold (2; X9's canvas if it is plain).

That is about 18. New textures:

- the REST STOP sign;
- the board;
- with question 8 (a), ten lettered faces on that board.

## Original lines (dark/aazex129)

| Line | Where |
| --- | --- |
| "Rest Stop" (:0) | the three Rest Stop huts' signs |
| The ten game names (:1-10) | the ten boards, in the source's corners and order; "Might and Magic" last, by the causeway's head |
| "The observatory is closed." (:11) | the observatory's door (m42.observatory) |
| "Dragon Pharaoh, Guardian of Xeen" and the refusal (:12-13) | m42.shrine's fail_text |
| "Descend into Darkstone Tower?" (:14) | the meaning of the stair house's exit window |
| "A message reads: It's a long road ahead ..." (:15) | the note (m42.pharaoh_note) |

## Hooks placed

- **A3's, by name:** `m42.pharaoh_note` (the note's post), `m42.observatory` (the observatory's door),
  `m42.shrine` (the dais; true starts the cinematic).
- **Read:** m42.done (111840) for `state:wedding`; m41.seal_broken (111820) is FD-03's, for the way up.
- **New, asked of A3:** the board and Rest Stop lines as the map's own text; the disc's line if question 10 (b).

## MU-4 concepts

`tools/paint_p5.py` made one `codex exec` call per view, with no retry. Both came back on the first attempt (77 s and
73 s). The results are `output/studio_cal/p5/mockups/raw/p5_walk_v1.png` and `p5_shrine_v1.png`, each with its prompt
(.txt) and log (.log) beside it.

The references were:
1. the plan's blockout at the view's camera;
2. X9's approved concept (D-50), for this world's clouds;
3. the xeen_cloud_sea sky at noon;
4. for the shrine only, A4's three portraits (npc15453, npc14405, npc15001; `output/studio_cal/p5/src/portraits.png`).

**'walk'** looks from the crown's north edge (3328, -3328), eye z 176, yaw 105 degrees, up the east road. It shows:
- the cloud road with its flagstone centre line;
- blank coloured boards on the right shoulder;
- the Rest Stop hut with its bench and blank green sign;
- the observatory's copper dome;
- the shrine's two raised stone hands on their gold-rimmed cloud across the sky on the left.

Against the plan (the plan wins at L2-L3):
- The shrine's cloud is painted level with the road. It is 512 above the start, so its underside shows.
- The observatory stands on its own cloud across a gap. The plan widens the road round it.
- The north-east turn is out of frame, so the road reads as straight.
- The hut is nearer and larger than drawn.

**'shrine'** looks from the causeway's head (0, -1920), eye z 672, north, after the ceremony. It shows:
- the dais;
- the hands holding a glowing blue Cube and the golden Scepter;
- the Dragon Pharaoh in a blue-and-gold headdress, reading from a book;
- Roland and Kalindra;
- the white-and-gold pavilion with garlands and the cake;
- blank boards on the ring behind.

Against the plan:
- The hands stand on tall columns; the plan has 448 over a 64 dais.
- All three figures stand on the dais. In the plan the Pharaoh stands behind it and the couple under the pavilion.
- The observatory is painted twice and given banners.
- The causeway reads as a paved plaza.

## Open questions for the decider

1. **The walk's length and shape.**
   - Options:
     - (a) One ring round the shrine: 29,137 from the arrival to the dais (76 s walking, 38 s running), room 26 x 26
       cells, three Rest Stops and the observatory. The source has eight stops on a 358-square spiral.
     - (b) A three-quarter ring that starts at the north-east (about 21,000).
     - (c) A ring and a half, nearer the source's spiral (about 45,000, room about 34 cells).
   - Recommendation: (a). The source's length is kept as an idea, not a duration, and the shrine is always in sight.
2. **Monsters** (maps.yml 0; MAPS says "none, or a last guardian").
   - Options:
     - (a) None, as in the source. The fight is FD-03's (45 monsters at 60-85); the walk is the rest after it.
       "Don't forget to recast your spells" stays the Pharaoh's joke.
     - (b) One last guardian: a placed Ancient sentinel boss at the causeway's foot (an A2 row, about level 85).
     - (c) A peaceful sentinel with one line.
   - Recommendation: (a).
3. **Falls.**
   - Options:
     - (a) To X5, on Darkstone's rock 224 before the tower's north door (-4608, 2304, 1500), facing it, with
       falling damage. The way back up is FD-03's stair; A7 keeps its gong floors raised once rung.
     - (b) An invisible wall round every cloud, so the finale has no falls.
     - (c) A fall puts the party back on the crown with damage (in the map).
   - Recommendation: (a). It is the world's rule (WORLD_DESIGN 3.1, "replaces walls at the sky maps' edges") and
     X8's and X9's.
4. **The Pharaoh's note.**
   - Options:
     - (a) Where the source has it: on a post by the stair house's door at the start, two squares from the arrival
       ("It's a long road ahead ..." reads as a send-off). A3 changes m42.pharaoh_note's `where`.
     - (b) By the last Rest Stop, as m42.yml and MAPS say now.
     - (c) Both.
   - Recommendation: (a). The source is unambiguous: (29,7), before the first stop.
5. **The Dragon Pharaoh at his shrine.**
   - Options:
     - (a) A peaceful placed figure behind the dais: an A2 row and S's golden dragon in a blue-and-gold headdress
       (A4's portrait), shared with DD-15, uncounted. The shrine stays the click.
     - (b) Only in the cinematic.
     - (c) A statue of him.
   - Recommendation: (a). The cinematic needs an actor anyway.
6. **Roland and Kalindra.**
   - Options:
     - (a) Peaceful placed figures under the pavilion, hidden until m42.done and shown by the cinematic's event cue.
       Their talk comes later, with A1's NPC-on-a-placed-monster word (D-47).
     - (b) The pavilion alone; the couple appear only in the cinematic's subtitle.
     - (c) As (a), with A3's after-lines now.
   - Recommendation: (a).
7. **Treasure** (maps.yml says treasure 6, monsters 0).
   - Options:
     - (a) One T6 chest, the wedding gift in the pavilion, shown with it.
     - (b) None.
     - (c) A T6 cache at each Rest Stop (3).
   - Recommendation: (a): one chest with a reason. The source has none.
8. **The ten boards' faces** (textures).
   - Options:
     - (a) Lettered faces: one Codex board picture, with the ten names lettered on it by script in a period typeface
       (no letters from Codex). That is eleven new textures plus the REST STOP sign, about 30 in all: class M
       (cap 45) with a new-texture exception (ROADMAP 5.2 allows 8).
     - (b) One blank board, with the names given by click and hover. That is 2-3 new textures, about 20 in all:
       class S (cap 30).
     - (c) Five two-sided boards (6 new).
   - Recommendation: (a). Reading them as you walk is the source's joke.
9. **Sky.**
   - Options:
     - (a) `xeencloud`, as on every sky map (the lanes' rule). The cinematic's fade to white is the sky turning over.
     - (b) A finale preset (A6): a golden late-day cloud sea.
     - (c) `xeencloud`, then the new preset after m42.done.
   - Recommendation: (a). It is the cheapest to reverse.
10. **The way out after the ending.**
    - Options:
      - (a) The stair house only (the source's "Descend into Darkstone Tower?"): the walk back, or a spell.
      - (b) As (a), and after m42.done a cloud-stone disc by the pavilion that moves the party to the crown (an
        in-map teleport, one line from A3).
      - (c) The cinematic's done event moves the party home (a town the decider names).
    - Recommendation: (b). The ending is not followed by a 29,000 walk back, and the source's way down stays.

## Requests (for the orchestrator to relay; none of these files is A5's)

- **A2:**
  - map_stats row 9119 (Clouds of the Ancients, `xeen_p5.blv`): encounter 0, treasure 6, lock 0, trap 0,
    perception 0, refill 672, music 15, PLAINS. No slots and no bolster row: the game loads no map without its row.
  - Peaceful placed-only rows, uncounted and NoArena: the Dragon Pharaoh (shared with DD-15), Prince Roland and
    Queen Kalindra (questions 5 and 6).
- **A3:**
  - m42.pharaoh_note's `where` moved to the stair house at the start (question 4).
  - The eleven sign lines aazex129:0-10 as the map's text.
  - ORIGINAL_LINES rows for aazex129:0-11 and :14.
  - m42.shrine calls `evt.PlayCinematic("unification", <done event>)` and gives the certificate in the done event.
  - The disc's line, if question 10 is (b).
- **A4:** the completion certificate (`world.yml` `completion`) on m42.done.
- **A6:**
  - On X5: `entrance:p5_fall` at (-4608, 2304, 1500) facing south (1536), and a keep-clear point there
    (question 3). Check it against the rock's top.
  - Textures:
    - X8's cloud pair, X9's cloud-stone and X5's Darkstone set;
    - a pale gold shrine stone;
    - new: the board (with ten faces, question 8) and the REST STOP sign. Register them in `source/textures.yml`.
  - A finale sky preset, if question 9 is (b) or (c).
- **A7:**
  - FD-03's roof stair: its top is `entrance:p5_stair`, facing down the stair.
  - The seal's way up leads to P5's `entrance:fd03_roof` (4608, -3968, 0), facing north (512).
  - The gong floors stay raised once rung, so the way back up after a fall stays open.
  - Say if the stair house should differ from X5's crown look.
- **A8:** DD-15 uses the same Dragon Pharaoh figure (question 5) if it places him as an actor.
- **S:**
  - Figures: the Dragon Pharaoh (with a book), Prince Roland and Queen Kalindra.
  - Decorations: the shrine's two stone hands, the Cube and the Scepter set in them (shown after m42.done), a cake
    on a table, and a bench for the Rest Stops.
- **AU:**
  - Wind (X8's).
  - For the cinematic, four far chimes (the sleepers) and a short wedding fanfare.
  - The Pharaoh's line is D-38's `xeen_vo_pharaoh_unification`.
- **A1:**
  - Confirm that a cinematic's `event` cue can show a hidden structure and placed actors on an open-air BLV
    mid-visit (`state:wedding`). The README's `show`, `hide` and `show_actors` exist; X9's castle-gone state only
    flips between visits.
  - The NPC-on-a-placed-monster word (D-47), for the talk in questions 5 and 6.
- **Orchestrator:**
  - `openAirMaps` for P5.
  - The MAPS P5 row (treasure, the note's place) after the answers.

## Blocked

Nothing blocks L1. L2 waits on:
- the decider's answers;
- A2's row 9119;
- A7's FD-03 roof stair, for the way in and down.

L4's tests from `assets_dev` also need A3's sign lines, S's figures (no stand-ins) and A4's certificate.
