# DD-12 Dungeon of Lost Souls (L4): notes

Lane A8 (agent `agent:xeen-a8-dd12`), phase 4 (session 9), 2026-11-21. Built from the MU-6 graph
(`devdocs/xeen/mockups/act4_graphs/dd12.graph.yml`) with decider D-42 (`mockups/act4_a8_decisions.md`), which wins.
One script, `output/studio_cal/dd12/tools/gen.py`, writes L1-L4 (playtests and this file by hand).
`output/studio_cal/dd12/cycle.sh L4 "<label>"` generates, formats, validates, builds, installs into the scratch root
`output/studio_cal/dd12/root` (data_tables a real copy; A2's provisional map card 9165 already in it), audits and
records. Not installed into assets_dev and not baked (the lane lead does both).

## What was built

Map 9165, `xeen_dd12.blv`, class M, under the ruined tower on D4's Isle of Lost Souls. Five floors going down 640
apart (L1 0, L2 -640, L3 -1280, L4 -1920, L5 -2560), rooms 512 high, the Soul Maze 384. 43 rooms/sectors,
39.0 M units², 16 doors (21 leaves: the five gates are pairs), 16 levers, the lift and its 4 buttons, 5 chests,
45 placed monsters, 5 loops. Four flights of 20 steps (352 wide, 1280 long), each with a plan of its own on both of
its floors; gates 2-4 stand at their heads. One closed lift shaft from the aviary (L5) to the lift head (L1).

- L1: the entrance hall (round, 1,094 across, hkm2b rubble masonry of D4's towers kit, roofless: sky faces under
  `xeen_darkside_fading`; the double door to D4 as two exit faces hkm1dl/hkm1dr; the carved plaque `xlsplaque` over
  the first gate), the hall of storage (grey brick cwb), the hourglass vault (behind a secret panel, chest T4), four
  "Minotaur Storage" rooms (stores; an `xlsglass` hourglass niche each; bones' find in the south-east one), the stair
  head, the lift head at the hall's west end.
- L2: the hall of the statue (it speaks as you come down; the stuck fourth lever), north and south walks round the
  cell block, three barred cells (xwcage bars raised by the three levers: two bone finds, a chest T4), the second gate.
- L3: the stagnant pool, the gallery of dials (four dials, the statue that says what to do), the Soul Waters (lever
  stuck until all four dials read 4; then once per member, A3's hook), the flooded walk, the Negative Soul Waters
  (chest T4), the third gate.
- L4: the hall of the plaque (the riddle), the hall of levers (12 levers on posts in four rows of three), the
  barracks (purse), the Minotaur's Private Reserve behind its portcullis (Minotaur Lord, hoard T5, Soul Waters), the
  fourth gate.
- L5: Alamar's statues (four verses), the Soul Maze (the letters S H E L T E M in ivy corridors, eswamp; the horned
  throne at the L's corner; an illusory wall under the second E to a dead end with bones and a chest T4), the fifth
  gate (a Minotaur Lord), the aviary (eight cages: six stat birds, the Parrot, the Songbird) and the lift's foot.

Monsters (D-42 (1)): Minotaur 11090 ×30, Gorgon 11091 ×12, Minotaur Lord 11092 ×3 (L1 8, L2 9, L3 9, L4 9, L5 10;
the entrance hall and the third and fourth gate halls quiet). Kill XP 95,145 → 23,786 per member (+1.2 % on 23.5k).

Slots (`project.yml`, = A2's row 9165): `Xeen Minotaur` tier 0 (Minotaur) 2-3 weight 75; `Xeen Minotaur` tier 1
(Gorgon) 1-2 weight 25; encounter 10 %; music 20; environment cave.

## The Soul Maze and the automap (D-42 (3))

The letters are corridors 256 wide on a 256 grid (3 by 5 cells, the M 5 by 5), 256 apart, y 1792-3072, x -864 (S) to
6560 (M). The maze lies north of every other floor's rooms, so on the journal map nothing of another floor is drawn
over it. Each letter is a room, joined to the next by one bridge cell (S-H at the top, H-E low, E-L at the top, L-T
along the foot, T-E at the top, E-M in the middle). The party enters at the M from the statues and leaves by the S.

**The letters read**, so the maze is (a), SHELTEM:
- in-game journal map after walking the maze (a menu input tour; the whole map shown, no zoom):
  `output/studio_cal/dd12/shots/automap/automap-zoom2.jpg` (full screen) and `automap_sheet.jpg` (the map pane);
- every outline revealed, drawn as the game draws them (grey by height from the party's floor), from the built BLV:
  `output/studio_cal/dd12/shots/automap_l5_maze.jpg` (the maze) and `automap_l5_full.jpg` (the whole map),
  `output/studio_cal/dd12/tools/automap.py`.

## Hooks and state

- `m24.arrival`: the first entry (timer, `dd12_arrived_once` 117440) and the plaque's click.
- `m24.gate1`-`gate5`: each gate's front side (the hall before it): the hook's question, then a Yes/No choice
  (`AskChoiceWithAnswerSteps`). Yes: `m24.gate_open` and the map's qbit `gateN` (117441-117445); a timer then swings
  both leaves apart (also after a refill). No: `m24.gate_shut`; the gate stays shut and asks again, no wave (D-42 (6)).
  From beyond, each gate opens by hand. Once answered, a plain double door.
- `m24.soul_waters_l3` (after the dials and the lever; `evt.ForPlayer(Players.Current)`), `m24.soul_waters_l4`.
- `m24.songbird` (the eighth cage): sets `bird_freed` 111480 and gives the Songbird 12526; the lift's four buttons
  test `bird_freed` (before it: "The cage does not move. Far below, something sings." at the top, "... The Songbird
  is still caged." below).
- `q-d25.throne`, else `q-d25.throne_again` (the throne and its dais).
- Map variables: the four hourglasses (flip back and forth; all four over: the vault panel grinds up for good), the
  four dials (1-4 and round), the Soul Waters running, the riddle, the finds, the six birds and the Parrot (each once,
  +2 to its stat for every member present: Luck, Endurance, Speed, Personality, Might, Accuracy, `AddValue(BaseX, 2)`
  under `evt.ForPlayer(Players.All)`), the statue's speech once a visit.
- The Negative Soul Waters take 25 HP (if 60 or more) and 10 SP (if 30 or more) from the drinking member: never kills.

## Arrivals and exits

- Inside: `entrance:d4_isle` (0, -352, 0) facing north (512), the start too.
- Out: the double door's two wings (exit faces `exit:door_left` hkm1dl, `exit:door_right` hkm1dr, the `exit`
  preset) to D4's `entrance:dd12_door`. **Measured** (`playtest_exit.yml`): (4096, -3072, 1377), facing south (a
  0.4 s step went to y -3378).
- D4's `door:dd12` (installed) still ends in "(The Dungeon of Lost Souls comes in a later part of the world.)" and
  its project entry has no `arrival:`: A6 to unseal it with `arrival: entrance:d4_isle`.

## Checks

- `oymap validate`: no issues; `oymap build`: 0 warnings (no two-sizes warning); `oymap audit --reach --solve` (oymap
  of 23:40): 0 errors, 0 warnings (12 `door.unused` infos: the eleven stuck levers and the stuck L2 lever never move);
  all 43 sectors reached with the doors out of the way. Logs: `output/studio_cal/dd12/build.log`, `audit.txt`.
- Textures: 29 distinct of 45, 3 new of 8 (`tools/xeen/texture_budget.py --root output/studio_cal/dd12/root`).

## Playtests

`output/studio_cal/dd12/four.sh` (ASSETS defaults to the scratch root):
- `playtest.yml`: the whole descent and the way back, 306 steps (see its header).
- `playtest_hostility.yml`: 30/12/3 hostile, none peaceful; the three kinds side by side do not fight.
- `playtest_exit.yml`: both wings to D4, the arrival measured.

## Pictures

From the scratch root (no bake: lights are the generator's only; the lead bakes after install), HUD off, every door
open, JPEG sheets in `output/studio_cal/dd12/shots/` (`tools/tour.py`, `tools/sheet.py`, `shoot.sh`):
- `things1_1..4.jpg`, `things2_1.jpg`: the entrance hall (plaque over the first gate, the double door's two wings,
  the open sky), the storerooms and hourglass niches, the lift head, the speaking statue, the cells, the gates (the
  smiling sun on the open leaves), the pool, the dials, the two Soul Waters, the levers on their posts, the Reserve,
  Alamar's statues, the maze's mouth, the throne, the illusion's dead end, the aviary's cages and the lift's cage.
- `rooms1_1..9.jpg`: every room from two corners and every flight from its foot and head (the maze letters' "a"
  shots stand outside the letters, in the void: see `maze_1..2.jpg`, twelve shots inside the letters).
- `automap/automap-zoom2.jpg`, `automap/automap_sheet.jpg`: the journal map after walking the maze (SHELTEM).
- Looked at and fixed: the statue model `7dec54` stood off its plinth (now `7dec55` everywhere); the MM7 braziers
  `brzier00` hang from the ceiling (the floor `brazir2f` is a hanging one too in the audit's class), so the braziers
  by the throne and between the statues hang on chains; shipped straw/hay sprites (`strwlg`, `strwsm`, `haybale2`)
  and `dec01` draw nothing in this world and were replaced (`7dec11` dirt heaps, `trasheap`, `7dec55`).
- To look at again after the bake: the maze's brightness (ambient 8 with a torch at a turn of each letter) and the
  aviary's eight cages (xwcage panels in the walls; the clicks name the birds), each with S's cage bird (below).

## Texture fit exceptions

None (the audit has no texture warnings).

## Dressing exceptions

None.

## Waiting on

Nothing: `xlsplaque`, `xlsgate`, `xlsglass` are in assets_dev (A6/the lead, 22:51) and used at their own sizes.

## Words needed

None. Two exit faces stand for the double door's two wings (XD-14's gate pattern), since an exit is one face.

## DECIDE (cheaper-to-reverse choices taken)

1. The lift head is at the hall of storage's west end (the graph had it beside the stair head): the maze had to lie
   clear of the other floors for its letters to read, and the shaft sits at the maze's west end. **Accepted, D-52.**
2. The maze's two halves meet once, through the L (the heart is on the path); the graph's second meeting would have
   drawn a stroke across the letters. **Accepted, D-52.**
3. The cells of the lost are three cells off the south walk (the walk is the cell row), so each lever has its bars. **Accepted, D-52.**
4. The gates' Yes is kept in map qbits 117441-117445 (the gates stay open after a refill), not map variables. **Decided by D-52 (`mockups/act4_a8_followups_d52.md`): kept.**
5. The birds, hourglasses and levers act on a click (no "Set it free?" / "Flip?" / "Pull lever?" question). **Accepted, D-52.**
6. The Negative Soul Waters take a fixed 25 HP / 10 SP rather than a tenth (the scripts read no current value). **Decided by D-52 (`mockups/act4_a8_followups_d52.md`): kept.**

## State and next steps

**Installed and baked** by the lane lead (below). Was ready to install (2026-11-21, 00:5x): L1-L4 generated, `fmt --check` clean, validate no issues, build 0 warnings,
audit 0 errors / 0 warnings, every playtest 4 of 4 from the scratch root (`output/studio_cal/dd12/four_final.txt`,
logs `output/studio_cal/dd12/run/four_003423`). For the lane lead:
1. `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd12`
2. `flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd12`
3. `ASSETS=$PWD/assets_dev output/studio_cal/dd12/four.sh`
Then A6 unseals D4's `door:dd12` (`arrival: entrance:d4_isle`); A3 registers the map qbits 117441-117445 (gate1-5).
`Xeen.Stages.darkside_sun` calls `evt.SetOutdoorSky`; whether it switches an indoor `open_sky` preset was not tested.

## Installed (session 9, lane lead)

- Installed 00:36 (`INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd12`, build `output/studio_cal/dd12/b_003623`: 43 rooms,
  1558 faces, 43 doors, 39 lights, 92 events, 5 chests). Audit of the L4 against assets_dev (`--reach --solve`,
  `output/studio_cal/a8_s9/audit/dd12.txt`): 0 errors, 0 warnings.
- Baked 00:36 (profile as DD-02's); `stale_bakes` none. Tests from assets_dev 4 of 4: playtest 306, playtest_hostility
  23, playtest_exit 31 steps (`output/studio_cal/dd12/run/four_003831`).
- Baked pictures `output/studio_cal/dd12/shots/baked_s9/` and `baked_s9_maze/` (sheets `baked_s9_a.jpg`, `baked_s9_b.jpg`,
  `baked_s9_maze.jpg`): the ruined tower under the fading sky with the plaque over gate 1, the hourglass niches, the
  stores and pool, the maze's ivy walks under their stone ceilings (brightness fine). Frames 25 and 26 are tour points
  against a monster and outside the map, not faults. The aviary cages have S's birds since session 19.
- Open: D4's `door:dd12` sealed (A6: `arrival: entrance:d4_isle`); qbits 117441-117445 to register (A3).

## Session 19 (A8): the cage birds

S's `xeen_cagebird` (row 4015, its `perch` idle) in each of the aviary's eight cages (`deco:cagebird_1..8`, gen.py; before:
`tools/gen_before_s19.py`): at the cage panel's centre 1 in from the wall line (the build refuses a point on it), 64 over
the floor (the panel's bottom, -2496), facing out (north wall 270, west 0, south 90). The cages are not recessed (S's
optional 48-64): the bars' gaps show `xwcage`'s own painted backing, not sky. Installed 08:57
(`output/studio_cal/dd12/b_085713`), baked 08:57, 0 stale, **4 of 4 from assets_dev** (playtest 306, hostility 23, exit
31; `output/studio_cal/dd12/run/four_085821`), audit of the installed map and of the project 0 errors / 0 warnings, baked
shots `output/studio_cal/dd12/shots/cages19_1.jpg` (the aviary's walls and three cages close).

## Session 21 (A8): AU's sounds

The room-filling beds `sound:bed_lower`, `bed_maze`, `bed_upper` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 24 (A8): merge point 35 tests

`playtest.yml`: the walk down the stair to L5 clears (1,500): a minotaur on the stair was no longer killed from L4
(merge point 33's storey-bound clears). No map change. 4 of 4 from assets_dev on merge point 35 (306).

## Session 26 (A8): F13 status lines, the Songbird's key

- The six stat birds (`evt:cage1`-`cage3`, `cage5`-`cage7`, +2 to a stat for the party, once) showed their thanks in a
  window (`message:`); `tools/gen.py` `bird()` now uses the studio's `text:` effect, a status line
  (`evt.StatusText(text, 6)`). The Parrot (`evt:cage4`, a prophecy to read) stays a window. Before:
  `output/studio_cal/a8_s26/before/dd12/`. Only the map Lua and studio file changed.
- Cage 8 (`evt:cage8`, event 16): A3's `m24.songbird` now needs Megan's key (12344) and refuses with its own status
  line. The map draws no cage opening of its own (the cage birds stay, nothing hides or opens), and the lift's events
  read `bird_freed`, which only the hook's success sets: the wiring needs no change.
- `playtest.yml`: the lark's gain on the status line; the Songbird first refused without the key ("Megan's father kept
  the key", no `bird_freed`), then `grant_item` 12344 and freed; the Minotaur's Private Reserve (`m24.soul_waters`,
  +2,000 experience) is a status line since A3's hook change.
- Installed 00:39 (no bake: neither .blv nor scene changed); audit 0 errors / 0 warnings, check_exits 0; tests from
  assets_dev 4 of 4 (12 of 12, `output/studio_cal/a8_s26/run/dd12/t004604`).

### Drop pockets

- check_drops: one pocket, the lid of `chest:negative` (L3, (1200, -2560), top at -1216, 64 over the floor; faces
  `ch1top*`, 6,144 square units). The party cannot climb onto a chest (step up 50), so it cannot be reached: kept.

## Session 28 (A8): D-89 identity (floors 3-5 in wet rock)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, severity 3: "good bone-and-rubble entrance, then tan
brick storerooms on every floor") asked for MM7 d02's darker wet rock on floors 3-5, pillars, low arches, side cells
and broken masonry in the maze. All in `tools/gen.py`'s "D-89 identity" block (generator reproduced the installed L4
first; snapshot `output/studio_cal/a8_s28/before/dd12/`).

- Floors 3-5: the set-piece halls (dials, Soul Waters, gates 3-5, plaque, levers, Alamar's statues, aviary) take a new
  `theme:deep`: d02's dark wet rock `c2b` on walls and ceilings over a 96 grey-brick footing (`cwb`), brick quoins
  (`ends`, not in the aviary: its cages reach the corners) and brick reveals, flags underfoot. The rock rooms (cells,
  pool, flooded walk, negative waters, barracks, reserve) in `c2b` with the same footing; the three flights down from
  L2 in `c2b`. New texture: `c2b` only (d02's own).
- Rock pillars (seven-sided) in the pool, negative waters, barracks and reserve; brick piers in the Soul Waters and
  Alamar's statues; low brick arches (spring 320, crown 464) across the gallery of dials, the flooded walk and the
  hall of the plaque; uneven rock ceilings (up to 64 under the floor above) in the pool, negative waters, barracks,
  reserve; the three L2 cells' walls rough.
- Three side cells cut into the rock on L3 (`room:side3a`/`side3b` off the flooded walk's north wall, `side3c` off the
  pool's west wall; 192-wide low arches; bones, a skull, a dim light), plan spaces and links added.
- L1-L2 brick rooms: a dark `c2b` base course (64) and cornice (448-480); the hall of storage under a barrel vault (640
  at its ridge; nothing stands above L1). The maze: its ivy over a 96 grey-brick footing, fallen masonry (`trasheap`)
  in five dead ends (H's two, E's top arm, M's first two legs; none on the walking line).
- `identity: {shape: hall, family: d02}` in `project.yml`; the name test: the round ruined base under the sky, the wet
  rock floors with pillars, arches and cells, the Soul Maze spelling SHELTEM.
- Installed 01:40, baked, audit 0 errors / 0 warnings, check_exits 0, check_drops 0 pockets (the chest lid no longer
  counts), MAW reserve 0, key_npcs 0; tests from assets_dev 12 of 12 (`output/studio_cal/a8_s26/run/dd12/c014000`).
- Pictures: before `output/studio_cal/a8_s28/dd12_before_sheet.jpg`, after (baked)
  `output/studio_cal/a8_s28/dd12_after_sheet.jpg` (tour `tools/tour.py things`).
- Rebuilt on oymap merge point 42 (the style world's chest 7gt002 for the chests without a `kind`): reinstalled 02:08,
  baked, audit 0 / 0, tests 12 of 12 (`output/studio_cal/a8_s26/run/dd12/c020752`).
