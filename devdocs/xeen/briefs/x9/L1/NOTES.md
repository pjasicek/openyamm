# X9 Clouds of Xeen: L1 plan (MU-3, MU-4) for the phase 5 review

A5, 2026-11-20. This is a plan only: there is no geometry, no L2-L4 and no build. Nothing is built until a decider
has approved the board (`output/studio_cal/x9/mockups/board_x9.png`, small copy `board_x9_small.jpg`).

`output/studio_cal/x9/tools/design.py` holds the design as data. `gen_l1.py` writes the two YAML files here (plan,
project). To change them, edit the design, then run `output/studio_cal/x9/tools/run.sh`. It renders and measures
(`render_x9.py`: the plan, the signature blockout, `figures.json`), writes the brief with the census in `totals`, runs
`oymap fmt`, `fmt --check` and `oymap validate --assets assets_dev`, and draws the board. The Python steps run under
an 8 GB cgroup cap. `tune_chain.py --apply` is a design aid: it spaces the rope bridges evenly down both chains and
keeps the unseen way at nine cells. Run it only after islands move.

Validation: `fmt --check` is clean and `validate` reports no issues. The shape is X8 Cloudreach's L1, an open-air BLV
region with the islands as spaces with `at` (the middle, map units) and `extent`. Point positions are in each
point's `notes`, because an L1 plan has no point coordinates.

## What the plan holds

**Source:** the Clouds of Xeen, MM4 maze 27 with x106-x108 (a 32 x 32 sky), its events and its text
`xeen/aaze0027`. The source's layout is kept:

- a long southern cloud with the arrival in its middle, four rhyming statues and two roc nests on it;
- an open gap, crossed by "Xeen--9N.": the source's nine squares north over the sky (with Levitate);
- the northern cloud: Slick's four booths west of the way north, the prize stand at (12,29), Castle Xeen's gate at
  (16,29), and the "Xeen's Aviary" sign at (26,26) over five roc nests in the north-east corner;
- lone clouds with offering statues down both sides.

**Room:** 88 x 84 cells (45,056 x 43,008 units). This is about 70 % of an outdoor map's side, by X8's rule (76 x 64
for 60 %). North is up; x runs east and y north, with the middle at (0, 0).

**Regions**, south to north:

- **The stair clouds (south, 320-512).** These are one cloud with waists, built round the source's long cloud:
  - **The cloud stair's head** (0, -16896), floor 320. XD-12's cloud stair arrives here at `entrance:xd12_roof`
    (0, -17920) facing north. It is quiet.
  - On the neck north: "Danger! Go back!" (aaze0027:7).
  - **The brink** (0, -11776), floor 448: the cloud thins to wisps over the gap. "Xeen--9N." (aaze0027:6) stands at
    the unseen way's foot. This is the signature camera.
  - **The west and east statues** (+-7168, -17152), floor 384: two rhyming statues each, m34.statue_1-4 (aaze0027:2-5).
    Two rocs stand by each pair; they are the first fight.
  - **The south-west and south-east nests** (+-13312, -15616), floor 512: a roc nest each and six rocs each. The
    south-west nest has a hollow with a chest.
- **The unseen way.** It is a 512-wide path nine cells (4,606) due north from the sign. It falls 192 to **Xeendom's
  landing** (0, -4424), floor 256, where "Now entering Xeendom" (aaze0027:8) stands. How faint it is: question 1.
- **Xeendom (north, 256-1,024).**
  - **Slick's carnival** (-3072, 3328), floor 448: a paved cloud plaza west of the Xeen road, with A3's four booths:
    - Might: a high-striker with a bell and a hammer;
    - Speed: the gremlin's race track;
    - Endurance: the treadmill;
    - Accuracy: a shooting line with a straw bullseye 1,536 west at the plaza's end.

    The plaza is quiet.
  - **The back lot** (-9472, 7424), floor 512: the bridge from the north-west isle lands here, by three Cloud Golems
    (the source's (7,25-27)).
  - **The gate causeway** (0, 9472), floor 704: Slick's prize stand on its west side (m34.prize_stand), and the gate
    at its head. It is quiet.
  - **Castle Xeen** (0, 15104): a closed shell of 7,168 x 6,656 (A7's outer castle) on its own cloud (base 768),
    with an apron 1,024 wide round it.
    - The walls are 2,688 high, the four round corner towers 3,200 (radius 768) and the keep 3,712, so that XD-19's
      four floors fit inside.
    - The style is XD-19's: black stone with gold friezes and caps.
    - Three Cloud Golems stand on the east apron by the aviary stair.
  - **Xeen's Aviary** (11520, 13312), floor 1,024: a high cloud ringed with rock spurs, reached by a cloud-stone stair
    (4,130, rising 256) from the castle's east apron.
    - "Xeen's Aviary" (aaze0027:9) stands at the stair's head.
    - It holds three roc nests, the rocs' hoard, six rocs and six griffins.
- **The west chain:** four lone clouds, each with an offering statue, from the south-west nest to the north-west isle.
  Rope bridges of 3,551-3,664 join them, and a fifth bridge (3,399) goes on to the back lot. The north-west isle has
  a cache.
- **The east chain:** three lone clouds, two of them with offering statues, from the south-east nest to the aviary.
  Rope bridges of 3,863-4,022 join them. The east horn has a lost traveller's pack.
- **The Dragon Clouds** (18944, 18176), floor 2,048: high above the aviary, 3,892 from it, with a dragon-head rock.
  - There is no link to them. FD-04's roof (phase 6) is the only way in, at `entrance:fd04_roof`.
  - They are empty until Q-F1 has a brief (no q-f1.yml exists yet). See question 8.

**Loops:** two rings run from the stair head up a chain to Xeendom and back over the unseen way. The west ring goes
through the carnival. The east ring goes through the aviary and round the castle's apron. The critical path is the
stair head, the brink, the unseen way, the landing, the plaza and the gate.

## Figures (`render_x9.py`, `output/studio_cal/x9/mockups/figures.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Monsters placed | 50 (MAPS; sky maps 50-60, all placed) | **50**, in 19 groups of 2-3, all fixed (no markers) |
| Kill XP per member | 26.1k | **26.0k** (-0.4 %): Rocs 11561 (38) x38 = 69,312; Griffins 11562 (48) x6 = 16,704; Cloud Golems 11592 (50) x6 = 18,000; 104,016 for the party |
| Monster band | 35-55 | 38-50. The source has Rocs and Cloud Golems (maze 27's two sprite kinds); the Griffin is the great birds' C tier |
| Size | ~70 % of an ODM | room 88 x 84 cells; the clouds span 70 x 75 cells |
| Walkable cloud | X8: 124 M units² for 60 | **256.5 M units²**, plus the castle shell's 48.2 M (question 7) |
| Quiet cloud | at least a third | **51 %** of the cloud lies over 2,048 from any group |
| First fight | 2,000-6,000 from each arrival | from the stair head 5,938 (the west statue rocs); from XD-19's return point 4,169 (the apron golems) |
| Rope bridges | D-6.2: 3,500-4,000 | 3,399-4,022. The aviary stair is 4,130, the cloud necks 2,189-3,252, the Xeen road 3,958 + 2,716 |
| The unseen way | "nine squares north" | 4,606 (9 x 512), falling 192 |
| Points of interest | X8's L1: 13 | **29** by the census (chained within 400; the arrival and return out): 4 signs, 4 rhyming statues, 5 roc nests, 6 offering statues, 4 booths, the prize stand, the gate, 4 chests. The nearest-neighbour median is 2,541 (1,180-7,371) |
| Chests | treasure 5 | 4, all T5: the south-west hollow, the north-west cache, the east pack, the rocs' hoard |
| Heights | - | stair head 320; south 384-512; chains 384-704; the landing 256; the plaza 448; the gate 704; the castle 768 (walls to 3,456, keep to 4,480); the aviary 1,024; the Dragon Clouds 2,048 |
| Ways in and out | XD-12's roof; falls to X2 | XD-12's cloud stair (one way up); XD-19's gate both ways; FD-04's roof (sealed); every fall to X2 |
| Textures | indoor cap | X8's set (xccloud, xccloudsd, 7tws1f, t66floor, hwm2rf, gkp1flr) plus XD-19's exterior kit. New: the awning canvas, the bullseye, the unseen way's wisp top (requests) |

Monster placement, by area:

- the south: rocs 6 + 6 at the nests and 2 + 2 at the statues;
- the west chain: rocs 2, 3, 2, 2 and three golems in the back lot;
- the east chain: rocs 2, 2, 3;
- the aviary: rocs 3 + 3 and griffins 3 + 3;
- the castle's east apron: three golems.

Walking golems stand 300 or more inside the rims, as on X8. Rocs and griffins fly.

## Castle Xeen's gate (D-47, Q14 and its relays to A5)

- **The gate:** two leaves in the shell's south wall at (0, 11776), facing south, built under the double-door rule.
  - It is XD-19's door into A7's `entrance:x9_gate`.
  - Its condition is A3's `m34.gate`: "Enter Castle Xeen?" / "No one may enter Castle Xeen without a cupie doll!"
    (aaze0027:40, :10).
- **The return point:** `entrance:xd19_gate` at (0, 11264, 768), facing south (1536), on the causeway 512 before the
  leaves (the source's (16,28)). Both XD-19's exit and the scepter cinematic's direct leave land here.
- **The castle gone:** `state:castle_gone` on m35.done (111707).
  - The shell (walls, towers, keep and leaves) is hidden and `link:gate` is sealed. The castle's cloud stays.
  - A click on the gate's spot reads "The great Castle Xeen recently stood here." (aaze0027:44).
  - The return point stays, for the cinematic's leave and for a Lloyd's Beacon set inside.
  - Indoor `hide`/`passable` effects exist (Map Studio README, indoor batch six).
- **"Xeen's Aviary":** at the head of the aviary stair, by the rookery, as in the source (question 3).

## Falls and arrivals

- **Falls:** as X8 (`briefs/x8/L4/NOTES.md`, "Falls"):
  - a one-second check moves a party below z -1,000, and the room's floor at -6,000 catches the rest;
  - the move goes through A3's `Xeen.skyFall` (`{direct = true, keepHeight = ...}`) to X2.
- **The landing on X2 (proposed; X2 is A5's map, unchanged):** (-14592, 2816), cell [35.5, 58.5], ground 768,
  facing east (0).
  - It is on Darzog's island, between the tower's east door (-16031, 3014) and the island jetty [38.6, 61].
  - It is 1.5 cells inside the shore, where the island is at its full 768.
  - No decoration or entity stands within 1,600 in the installed `xeen_x2.scene.yml`.
  - The point is 7,100 from X8's lake landing (-10240, 8448).
  - The party falls with damage; a level-46 party loses little. The tower door is ten steps away, and Darzog's disc
    and the cloud stair lead back up. This is question 2.
  - At X2's next install, A5 adds a keep-clear point there.
- **Arrival from XD-12:** `entrance:xd12_roof` (0, -17920, 320), facing north (MoveToMap direction 512): the top step
  of the cloud stair rising out of the cloud sea, as on X8.
  - A8's `exit:clouds_of_xeen` is sealed today ("The cloud thins to fog above the last step."). It points here once
    X9 is installed.
  - There is one way up; down is by falling, by Lloyd's Beacon, or through XD-19.
- **No Fly:** no BLV casts it (X8's finding). The rule is kept in project.yml as a record.

## Original lines (xeen/aaze0027)

| Line | Where |
| --- | --- |
| "Roc Nest.  Destroy?" (:0) | the five nests |
| The four statue rhymes (:2-5) | A3's m34.statue_1-4, the west and east statues |
| "Xeen--9N." (:6) | the brink, at the unseen way's foot |
| "Danger! Go back!" (:7) | the neck from the stair head to the brink |
| "Now entering Xeendom" (:8) | Xeendom's landing |
| "Xeen's Aviary" (:9) | the head of the aviary stair |
| "No one may enter Castle Xeen without a cupie doll!" (:10), "Enter Castle Xeen?" (:40) | the gate (m34.gate) |
| Slick's patter (:12-26, :31, :41-43) | A3's booths and prize stand |
| "Offering" (:33) | the six offering statues |
| "The great Castle Xeen recently stood here." (:44) | the gate's spot after m35.done |

Not used: "You are unable to understand the strange runes." (:1), until the Linguist gate exists (as X8). Also unused:
"+ 50,000 experience" (:34) and "Luck Game" (:36), which is a label with no event in the source.

## Hooks placed

- **A3's, by name:**
  - m34.might_game, m34.speed_game, m34.endurance_game, m34.accuracy_game, m34.prize_stand;
  - m34.gate (the gate's condition);
  - m34.statue_1 to m34.statue_4.
- **Read:** m35.done (111707) for the castle-gone stage. m21.crodo_freed (110501) is read by XD-12's stair, not by
  X9.
- **New, asked of A3:**
  - the five roc nests;
  - the six offering statues;
  - the four sign texts;
  - the castle-gone line;
  - a first-arrival line.

## MU-4 concept

`tools/paint_x9.py` made one `codex exec` call with no retry. It came back on the first attempt. The result is
`output/studio_cal/x9/mockups/raw/x9_signature_v1.png`, with its prompt (.txt) and log (.log) beside it.

The references were:
1. the blockout `blockout_signature.png`, from the brink at (256, -11232), eye z 624, looking north;
2. X8's approved bridge concept, for this world's clouds;
3. the xeen_cloud_sea sky at noon.

The painting shows:
- the brink's cloud lip with a blank signpost;
- a wisp path over the gap to the landing;
- the plaza with four striped booths (bell pole, track, treadmill, bullseye) and bunting;
- the stone road up to Castle Xeen: black walls, gold caps and friezes, a gold double gate;
- the aviary's rock spurs and nests with rocs on the right;
- the dragon-head cloud high in the corner;
- statues and rope bridges on the left chain.

Against the plan (the plan wins at L2-L3):

- The castle is painted about twice as large and nearer than the blockout. At 23,000 it spans 18 degrees.
- The four booths stand in one row; the plan spreads them over the plaza.
- The unseen way reads as a visible cloud path (question 1 decides how faint it is).
- The painter added a banner on a pole in the right foreground and two gryphon statues at the gate.

## Open questions for the decider

1. **The unseen way ("Xeen--9N.").**
   - Options:
     - (a) A faint way: a 512-wide path nine cells due north of the sign, its top a wispy cloud texture that is hard
       to see. The sign is the clue, and a fall costs the climb back through XD-12.
     - (b) A plain causeway or rope bridge, with no puzzle.
     - (c) Truly invisible faces. This needs a new studio word (A1).

     In every case both chains are a visible way round.
   - Recommendation: (a). It is reversible by a texture.
2. **Where falls land on X2.**
   - Options:
     - (a) One point on Darzog's island, between the tower's east door and the jetty: ground 768, with falling
       damage. The way back up is next to it.
     - (b) Lake Darzog's water east of the island. There is no damage (X8's middle zone), but reaching the island
       then needs Medin's boat or Water Walk.
     - (c) The X9 position scaled over X2's lake.
   - Recommendation: (a).
3. **"Xeen's Aviary" (aaze0027:9).**
   - Options:
     - (a) On X9, at the head of the aviary stair by the roc rookery: the source's (26,26), at eye height.
     - (b) On the castle shell's wall, naming XD-19's inner aviary (A7's note).
     - (c) Both.
   - Recommendation: (a). XD-19 may sign its own court inside.
4. **The monster mix** (50 monsters, MAPS 35-55).
   - Options:
     - (a) As drawn: Rocs 38 x38, Griffins 48 x6 (the aviary), Cloud Golems 50 x6 (the back lot and the apron);
       26.0k.
     - (b) The source's two kinds only: Rocs x40 and Cloud Golems x10; 25.7k.
     - (c) As (a), with two Lesser Air Elementals (55, XD-19's) in place of two golems; 26.3k, reaching the band's
       top.
   - Recommendation: (a).
5. **Offering statues and nests.** The source has 9 offering statues and 7 roc nests.
   - Options:
     - (a) As drawn: 6 offering statues (one per chain cloud; an item of treasure 5 for Crusaders, once per party)
       and 5 nests (2 south, 3 in the aviary).
     - (b) The source's 9 and 7.
     - (c) X8's 2 and 3.
   - Recommendation: (a). The census gives 29 POIs.
6. **Slick's figure.**
   - Options:
     - (a) A peaceful placed figure behind the prize stand: an A2 row on a recoloured shipped merchant, not counted.
       The booths and the stand stay the clicks.
     - (b) No figure. Slick speaks through his booths only (m34 as written).
     - (c) An NPC with a portrait at the stand. This needs an A4 id, and A3 makes the stand a topic.
   - Recommendation: (a), with (b) until S has the binding.
7. **Size and fill.** The room is 88 x 84 and the walkable cloud is 256.5 M units², twice X8's 124 M for 60
   monsters. 51 % of the cloud is quiet: the stair head, the brink, the landing, the plaza and the gate are quiet by
   design.
   - Options:
     - (a) As drawn.
     - (b) Islands 15 % smaller (about 190 M), with spans of up to 4,500.
     - (c) As drawn, plus six rocs over the plaza's edges (kill XP +2.7k).
   - Recommendation: (a).
8. **The Dragon Clouds (Q-F1).**
   - Options:
     - (a) Built now: 2,048 high, north-east of the aviary and 3,900 from it, empty and sealed, with FD-04's arrival
       named `entrance:fd04_roof`. Q-F1's riddle, runes and dragons are added with its brief.
     - (b) Reserved now and built later, which means an X9 rebuild.
   - Recommendation: (a). It is a landmark now and cheap to fill.

## Requests (for the orchestrator to relay; none of these files is A5's)

- **A2:**
  - map_stats row 9107 (Clouds of Xeen, `xeen_x9.blv`): encounter 0, treasure 5, lock 10, trap 5, perception 5,
    refill 672, music 21, PLAINS.
  - Its slots: Xeen Roc tier 1 [2, 3] weight 80 and Xeen Elemental Golem tier 2 [1, 3] weight 20.
  - Its bolster_maps row.
  - The Act V recount at 26.0k.
  - The placed rows 11561, 11562 and 11592 already exist.
  - For question 6 (a): a peaceful, placed-only "Slick the Gamemaster" row, not counted and NoArena.
- **A3:**
  - Hooks for the five roc nests: aaze0027:0, Yes/No, and experience. The source pays 50,000; X8's harpy nests pay
    500.
  - Hooks for the six offering statues, as X8's.
  - The four sign texts, the castle-gone line aaze0027:44 and a first-arrival line.
  - ORIGINAL_LINES rows for aaze0027:0, :6-9, :33 and :44.
  - m34's `where` texts matched to the drawn booths. The accuracy booth's bullseye is at the plaza's west end.
  - `Xeen.skyFall` takes the X2 island point.
  - The Linguist gate for the rhymes (shared with X8).
- **A4:** none (X9 has no town and no houses). For question 6 (c): an NPC id for Slick.
- **A6:**
  - Textures: X8's xccloud and xccloudsd, and the 7tws1f flags.
  - New textures:
    - a red-and-white striped awning canvas;
    - a straw bullseye;
    - a wispy top for the unseen way (question 1 (a)).
  - The castle shell in XD-19's exterior kit (MM8 d35 black stone and gold friezes).
  - The sky preset `xeencloud` (it exists).
  - Register the new textures in `source/textures.yml`.
- **A7:**
  - XD-19's gate footprint: width, height and the two leaf pictures (gnecdr1l/r) for both faces.
  - The shell's outside, for the castle to match its interior: 7,168 x 6,656, walls of 2,688 for four floors 640
    apart. Say if the aviary court should open in the shell's roof.
  - XD-19's exit preset and the scepter's leave: X9's `entrance:xd19_gate` (0, 11264, 768), facing south (1536).
  - X9's gate leads to XD-19's `entrance:x9_gate`.
- **A8:** XD-12's `exit:clouds_of_xeen` to X9's `entrance:xd12_roof` (0, -17920, 320), facing north (512), once X9
  is installed.
- **S:**
  - For question 6 (a): Slick's figure binding (a recolour of a shipped merchant or showman).
  - Optional:
    - a doll shelf for the prize stand;
    - a high-striker (a bell pole) model;
    - ground models for the doll items 12367-12371, if they lack them (GROUND_ITEMS_3D: a missing model draws a
      placeholder).
  - With Q-F1: the dragon-head rock.
- **AU:** wind (X8's), roc cries, the high-striker's DING on a win, and a fairground loop at the plaza.
- **Orchestrator:** as for X8, whether `world.yml` lists X9 in `openAirMaps` (outdoor spells in the open air).
- **A5 (own):** at X2's next install, a keep-clear point at the fall landing (-14592, 2816).

## Blocked

Nothing blocks L1. L2 waits on:
- the decider's answers;
- A2's row 9107, without which the game cannot load the map (X8's lesson);
- A7's gate footprint.

L4's walk from `assets_dev` also needs A8's XD-12 exit and A3's nest and offering hooks.

## D-50 applied (A5 sub-agent, 2026-11-21)

`D50_DECISION.md` wins over the text above. Applied in `design.py` (the old one kept as `design.py.pre_d50`), then
`run.sh` (validate: no issues):

1. The unseen way is 768 wide, still due north from the sign (4,606, nine cells), with a cloud-stone lip at each end
   (`landmark:lip_south` at the sign's foot, `landmark:lip_north` under "Now entering Xeendom").
2. Slick's plaza is 6,144 x 4,608 at (-2560, 2560). Its booths are spread over it, 2,382-2,819 from their
   neighbours: Might (-1024, 1280), Speed (-1536, 3968), Endurance (-4352, 3840), Accuracy's line (-3712, 1536). The
   bullseye is 1,536 west of the line on the west rim (-5248, 1536). The Xeen road still runs up the plaza's east
   side.
3. The gate uses the exit preset's leave with the condition `m34.gate` (L4 says how). There is no map question.
4. Falls land on X2 at `entrance:x9_fall` as installed, (-15360, 3072), ground 768, facing east. D-50's
   (-14592, 2816) failed the dragon check and moved toward the tower door (the lead, 2026-11-21).
5. The castle shell is closed on every side, roof included.
6. The castle uses A7's measured XD-19 outside, 10,560 x 10,400 (inside 10,240 x 10,080): X9 x -5280..5280,
   y 11136..21536, centre (0, 16336). This is XD-19's frame + (0, 16096). It is not D-50's assumed 7,168 x 6,656.
   - The gate stays at (0, 11776), 640 behind the south towers' faces.
   - The return point stays at (0, 11264).
   - Heights over the base (768): walls 3,584, towers 4,096, keep 4,608, so XD-19's highest room (3,456 over the sill)
     fits inside.
   - No gryphon statues and no banners.
7. The Dragon Clouds are built empty and sealed, `entrance:fd04_roof` named.
8. Textures: Dungeon L, cap 70. Shipped canvas is tried first. New textures are the bullseye and the wisp top only.
9. The castle-gone stage, the return point and the aviary sign stay as drawn.

The wider shell (and its cloud, now a rounded rectangle 1,024 beyond the walls, shared with L4 in `geom.py`) moved
the aviary east 1,920, to (13440, 13440), so its stair stays 4,138. The Dragon Clouds moved with it to (20864, 18304),
still 3,892 from the aviary and 1,024 above it. With the aviary there, the east chain was retuned (`tune_chain.py`,
control (17000, -2000)): spans 3,880, 3,765, 3,750 and 3,895.

The room grew to 96 x 90 cells.

Figures now:
- 272.5 M units² of walkable cloud;
- 53 % quiet;
- bridges 3,399-3,895;
- the back lot's neck 3,890 and the Xeen road 4,105, both on cloud;
- the signature's castle spans 25.8° at 23,009;
- the first fight from the return point is 5,896.
