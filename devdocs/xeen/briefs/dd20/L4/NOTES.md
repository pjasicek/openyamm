# DD-20 Lakeside Coven and Sewer, L4: notes

New M dungeon under D4's Lakeside (dark maze0033 the coven, maze0034 the sewer), Q-D22 The Coven and Q-D20's Golden
Dragon, built with the Map Studio from `devdocs/xeen/mockups/act4_graphs/dd20.graph.yml` and decider D-42
(`mockups/act4_a8_decisions.md`, which wins) by `agent:xeen-a8-dd20` (lane A8 sessions 8 and 9), 2026-11-20. Key
`dd20`, project `xeen_dd20`, stem `xeen_dd20.blv`, map_stats 9173, world `xeen`, music 28.

**Rests:** sewer stalkers at Dif 5 (10 % Wererat 18, 50 % Stalker 25, 40 % Matriarch 35); the Wererat share is a
named exception, D-46.

## State and next steps (session 9, 2026-11-20): installed and baked by the lane lead (below)

**Reached:** L1-L4 written by the generator, `oymap validate` no issues, build 0 warnings (no "two sizes for one
texture"), installed into the scratch root `output/studio_cal/dd20/root` only, recorded (`agent:xeen-a8-dd20`, last
label "antechamber bench off her door; playtests written"). Audit (`output/studio_cal/dd20/audit.txt`, `--reach
--solve`): **0 errors** (fit, doors, lights, dressing), 2 warnings (the mirror, below), 1 info (the cistern ladder's
`bemv` squashed, a ladder's own look). `oymap solve` (`solve.txt`): 25 of 25 sectors in two steps (the cells' cage
fronts last, on the four freed bits), never reached 0; both exits live. **All three playtests 4 of 4 from the root**
(below). The root's `worlds/xeen/data_tables/` re-copied from assets_dev in session 9 (A2 had added row 9121); row 9173
is A2's own (present in assets_dev).

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd20`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd20`, then
`ASSETS=$PWD/assets_dev output/studio_cal/dd20/four.sh`. A6: D4's two doors and the trapdoor move (see "Arrivals").

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd20/cycle.sh` (regenerates L4 from `tools/gen.py`, fmt,
validate, build, install into the root, audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against
`.oymap/last` first if anyone edited it by hand.

**Scratch** `output/studio_cal/dd20/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes), `tools/dress.py` (objects, wiring), `tools/tour.py rooms|things|fix <name>` + `tools/sheet.py` (tours, JPEG
sheets), `cycle.sh`, `four.sh` (the three playtests N times, one game at a time, exact PIDs; `ASSETS=`, `N=`, `TESTS=`),
`shoot.sh <tour>`, `run/` (logs), `shots/` (sheets). **Every project file of L1-L4 except the playtests and these
notes is written by the generator.**

## Measurements

`oymap metrics` (`output/studio_cal/dd20/metrics.json`): **25 sectors** (M 20-45), **59.7 M units² of floor**
(M 30-90), 3 loops, doorways 224-448 wide; **9 doors** (16 door records: the seal's second leaf, four cage fronts, the
hatch, the bolt), 5 chests, 47 bound events, **45 placed monsters + 4 peaceful prisoners** (not counted).
Textures (`tools/xeen/texture_budget.py --root output/studio_cal/dd20/root --map DD-20`): **41 of 45, 0 new**.

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Witch | 11170 | 32 | 1,344 | hall 2, walk 2, brewery 3, dormitory 3, gaol 2, her room 1 | 13 |
| Coven Witch | 11171 | 40 | 2,000 | walk 1, antechamber 2, her room 1 | 4 |
| Head Witch | 11173 | 45 | 2,475 | her room (group 5 with two of the above) | 1 |
| Sewer Stalker | 11401 | 25 | 875 | slop pit 2, cross 3 + 4 hidden, main drain 3, cistern 2, warren 4, east drain 2, outfall 4 | 24 |
| Stalker Matriarch | 11402 | 35 | 1,575 | warren 1, outfall 1, cross 1 hidden | 3 |
| Camilla, Aretha, Isabella, Rhett | 11906-11909 | 10 | - | the four cages, peaceful, immobile, groups 20-23 | 4 (not counted) |

**Kill XP:** 13 × 1,344 + 4 × 2,000 + 2,475 + 24 × 875 + 3 × 1,575 = **53,672 for the party, 13.4k per member**.

## Mechanisms

- `evt:arrive` (timer, once): the arrival window "LAKESIDE'S UNDERSIDE. ..." on the first arrival by any way in
  (`arrived_once` 117400).
- **Initiation cauldron** (hall, two steps from the stair's foot, event 39): the studio's question "Initiation
  cauldron. The brew smells of toad and ambition. Drink?" / "Drink (Yes/No)?"; Yes runs A3's `q-d22.initiation`
  (cold before `riddle_answered` 113442 or after her death; joins: `joined` 113449, Warlock promotion; then "It is
  still toad."). Joined, the coven is friendly (A2's relations).
- **The Moon seal** (hall to the witches' walk, event 28): a hinged pair, `t1d1a|t1d1b` over `t1d1c|t1d1d`, doors 6 and 7.
- **The Head Witch** (actor 26, group 5): `evt:head_witch_dead` (timer) runs A3's `q-d22.head_witch` at her death
  (`head_witch_slain` 113447): the coven hostile again. **Her chest** (event 54, the hoard): opens to a member or over
  her body and runs `q-d22.witch_chest` (the Necropolis pass 12336, `pass_found` 113448; else "The chest holds hats.");
  shut, the hook's fail text "The Head Witch is standing next to it." Her mirror (41), her bed's purse (53, then
  "Nothing here.").
- **The brewery's three cauldrons** (17 Personality, 16 Endurance, 18 Speed): the map only calls A3's hooks (+2 base,
  once per character, player bits 11345-11347; again "You have had your fill."); a recipe skull by each (49, 48, 50).
- **The four cages** (cells, events 10 Camilla, 8 Aretha, 12 Isabella, 14 Rhett; actors 11, 7, 29, 38): the click runs
  A3's hook (her or his line, 500 XP, freed bit 113443-113446) and hides the prisoner at once (`SetMonGroupBit`
  Invisible); a timer sinks the cage front (doors 12, 11, 13, 14; map vars 4, 3, 5, 6); again the hook's "Nothing
  here."; `evt:prisoners_load` hides each freed prisoner on every load (D-42 (3)). No `in_visit`: they go at once.
- **The ambush** (D-18, D-42 (7)): actors 0-4 (group 6, four Stalkers and a Matriarch) placed hidden; the first step
  onto the cross shows them ("Things climb out of the side drains!", `ambush_shown` map var 0), kept with the map.
- **The store's hatch**: the bolt (event 36, a lever on the store's east wall) opens the hatch (door 15, `hatch_open`
  map var 7): "You draw the bolt. ..."; then "The bolt is drawn; the hatch lies open." The hatch (35): from the cistern
  "The hatch is bolted from above." until then; "The hatch lies open over the ladder." The cistern's ladder climbs
  through it.
- **The trapdoor** (sump, step, event 52): "The trapdoor is shut fast above you." (one way in, D-42 (4)).
- **The Dragon** (the niche's alcove, event 1): A3's `q-d20.dragon` (the Golden Dragon 12350, `dragon_found` 113402;
  then "The niche is empty."); the dead adventurer's journal page two steps short (42); the hideout's dead man (38:
  journal and his pack once, +400 gold).
- Finds once (map vars): the sump's bones (+250), a dormitory bed (+150), the store's shelf (+200); the warren, pump
  room, gaol and dormitory chests; drain grates and the lake bars talk (32, 45, 46, 40).

## Dressing

Coven: braziers and a chandelier over the initiation cauldron, two stone benches by the sigil (session 9), sconces;
her room: bed, chest, framed mirror, dresser with candles, shelf; brewery: three cauldrons on hearths, skulls on
ledges; dormitory: four beds; store: barrels in a pair, sacks, a keg, a shelf. Sewer: heaps of filth in the slop pit,
the warren's midden and bones, bones in the sump, the hideout and the niche, the pump room's box and bucket; torches.
Audit: 0 dressing findings. **Dressing exceptions:** none.

## Playtests

`output/studio_cal/dd20/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd20.blv`. Logs `output/studio_cal/dd20/run/four_*`.

| Test | Steps | What |
|---|---|---|
| `playtest.yml` | 250 (311 asserts) | starts on D4; in by `evt.MoveToMap` to `entrance:d4_guild` (arrival window, position), her chest shut from afar, out by the cellar door (33), in by `evt.MoveToMap` to `entrance:d4_trapdoor` (no window; the trapdoor line); sump bones; the hatch bolted from below; the ambush hidden, shown on the first step onto the cross, kept after a save and reload; the hideout's journal and pack; the east drain, shaft, outfall, niche: journal, the Dragon, "The niche is empty."; the warren's chest; the drain stair; the four cages (each line, each hidden at once, fronts sunk, "Nothing here.", all four hidden after a save and reload); the gaol's chest; the initiation cold, joined, "still toad", the coven friendly; the seal's two leaves; the mirror, her bed, her chest (the pass); she dies: head_witch_slain, the coven hostile; the brewery: a skull, Personality +2 then "You have had your fill.", Endurance and Speed +2; a dormitory bed, the shelf, the bolt, the open hatch |
| `playtest_hostility.yml` | 67 | 13, 4, 1, 24, 3 hostile at load, none peaceful; the four prisoners peaceful; coven and stalkers side by side do not fight; after joined (113449) the coven peaceful (kept after a save and reload), stalkers hostile; after head_witch_slain (113447) the coven hostile |
| `playtest_exit.yml` | 49 | start (`entrance:d4_guild`), up the Guild's back stair, the cellar door's window (33), OK: D4 measured; in by `evt.MoveToMap` to `entrance:d4_shaft` (measured), the ladder's window (34), OK: D4 measured |

**Results: all three 4 of 4, exit 0** (`output/studio_cal/dd20/run/four_233733`, summary `four_s9.txt`): playtest 311, hostility 67, exit 49 asserts passed in each run.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From D4 |
|---|---|---|---|
| `entrance:d4_guild` (map start) | (-640, -384, 0), north (512) | (-640, -384, 0) | `door:dd20_guild` (the Guild's cellar hatch) |
| `entrance:d4_trapdoor` | (3456, -640, -512), east (0); one way, "The trapdoor is shut fast above you." | within 64, z -512 | `q-d22.guild_wrong`'s move |
| `entrance:d4_shaft` | (14208, -1152, -512), west (1024) | (14208, -1152, -512) | `door:dd20_sewer` |

| This map's exit | To D4 | Measured on D4 | Facing |
|---|---|---|---|
| `exit:guild` (the landing's south wall, event 33, "Cellar door") | `entrance:dd20_guild` (-1024, -13312, 1120) | **(-1024, -13312, 1121)** | west (1024; given by the move, the runner reads no yaw) |
| `exit:shaft` (the ladder, event 34, "Ladder") | `entrance:dd20_shaft` (3072, -9728, 1120) | **(3072, -9728, 1121)** | north (512; given by the move) |

D4's L4 (`devdocs/xeen/briefs/d4/L4/`) names all three inside arrivals (`entrance:d4_guild`, `d4_trapdoor`,
`d4_shaft`) and both of its own arrivals as above. For A6: D4's installed guild door still runs `q-d22.guild_wrong`
with a status line ("... comes in a later part of the world.") instead of the move to `entrance:d4_trapdoor`, and the
cellar hatch and the shaft are sealed until DD-20 is installed; D4's `plan.yml` gives `entrance:dd20_guild` facing `e`
while its NOTES and studio file give 1024 (west).

## Pictures (looked at)

`output/studio_cal/dd20/shots/rooms1_1..6.jpg` (every room from two corners, every stair), `things1_1..3.jpg` (every
interactive thing; the seal shut and open; the cages shut and open; the ambush shown), `fix1_1.jpg`, `fix2_1.jpg`
(the fixes). **No bake in the root** (the lane lead bakes after install). Changed after looking (session 9, in
`tools/geo.py` / `dress.py`): the store's hatch lay off the 256 grid and showed four quarters of its picture (moved
128 south, corners on the grid; the bolt with it); the cross's street grate showed two half grates (off-grid grates
now slide their picture by the remainder); the antechamber's bench stood in front of the Head Witch's door (now along
the west wall); the coven hall read bare (two stone benches along the west wall, by the sigil). Still plain: rooms are
boxes; the sewer is one rock texture throughout; the Head Witch's bed and the dormitory beds read as low slabs; the
pump room is nearly empty; the cross's corner tour shots stand inside its piers (the tour's corners, not the map).

## Ids

- Map qbit: `arrived_once` 117400 (block 117400-117439, provisional). Hatch, ambush, finds, cage fronts: map variables
  (13: `ambush_shown` 0, `once.arrive` 1, `bed_found` 2, `cage_*_open` 3-6, `hatch_open` 7, `once.head_witch_dead` 8,
  `hideout_pack` 9, `shelf_found` 10, `sump_purse` 11, `witch_bed_found` 12).
- Read/set through A3's hooks: 113442-113449 (Q-D22), 113402 (Q-D20); player bits 11345-11347 (A3's cauldrons). Items
  given by hooks: the Necropolis pass 12336, the Golden Dragon 12350.
- Groups: 1 coven, 5 the Head Witch's three, 2 stalkers, 6 the ambush (hidden), 20-23 the prisoners.
- Slot for A2: `{monster: Xeen Sewer Stalker, tier: 5, per_marker: [2, 3], weight: 100}`, encounter 10 (as row 9173).

## Texture fit exceptions

- `tfb2` / `xkmirror` (`textures.family_switch`, two faces): the Head Witch's mirror is pale silvered glass in a frame of
  dark worn flags; the contrast is the mirror's.

## Dressing exceptions

None (audit: 0 dressing findings).

## Words needed

1. **A party facing check in the scenario runner** (A1): `party_position` has no yaw, so the arrivals' facings are the
   moves' own values, not measured.
2. A `lua_event` `evt.MoveToMap` from DD-20 to D4 did not move the party in the headless runner (the move from D4 into
   DD-20 did); the playtest leaves by the cellar door's window instead. Not looked into.

## DECIDE

1. **The trapdoor's line** fires on every step into the sump (also when the party walks in from the drains), not only
   on the arrival: kept as a status line (the cheaper option); a map variable would limit it to the drop.
2. **The coven hall's two benches** (session 9, dressing only): remove if the hall should stay an empty rite floor.

## Open

- The Warlock promotion is not played (no Great Druid in the test party); the hook's text and `joined` are.
- The cistern ladder is not climbed in a test (the hatch opens, the ladder stands under it in the pictures).
- Not checked in a picture: the prisoners' and the Head Witch's looks after freeing / in combat (the test checks hidden
  and hostility only).

## Layout (one frame: x east, y north as D4, origin under the Guild's centre)

- Coven, z 0 (7d06 dressed stone `7tws2` at scale 2, one storey per 512 wall; `tws2b` in the Head Witch's room; dark
  flags `7tfb11`, block ceilings `twb2`, slab doors `twb1`, the store in `wall` brick): Guild's back landing (640) and
  stair down north into the coven hall (initiation cauldron on a hearth two steps from the stair's foot); the Moon
  seal's double doors (hinged pair, `t1d1a|t1d1b` over `t1d1c|t1d1d`, 448 square) to the witches' walk; antechamber,
  Head Witch's room (bed, chest, framed `xkmirror`, dresser and candles), brewery (three cauldrons on hearths, a
  talking recipe skull by each, aaze0033:12-14); east of the hall the gaol and the dormitory, the store south of it
  (`store: true`, floor hatch with a bolt).
- Cells, z -256 (7d17 `c2b`/`cfb1`): four cages on the north side (`xwcage`/`xwiron`), Rhett's at the east end by
  the drain stair.
- Sewer, z -512 (7d17; plank walks `7trimd`, water `7wtrtyl`, grates `d1lggrt` overhead, `cws1d` drain mouths and lake
  bars): slop pit, drain cross (ambush), main drain to the trapdoor sump (hatch picture `7gt002c` in its roof), the
  cistern under the store (ladder up to the hatch), pump room, hideout, warren, east drain, outfall (tidal pool), the
  Dragon's niche (`cws1` alcove, bones two steps short), jetty shaft (ladder, exit).

## Installed (session 9, lane lead)

- Installed 23:39 (`INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd20`, build `output/studio_cal/dd20/b_233941`: 25 rooms,
  1239 faces, 16 doors, 37 lights, 55 events, 5 chests). Audit of the L4 against assets_dev (`--reach --solve`,
  `output/studio_cal/a8_s9/audit/dd20.txt`): 0 errors, the 2 mirror warnings.
- Baked 23:40 (profile as DD-02's); `stale_bakes` none. Pictures `output/studio_cal/dd20/shots/baked_s9/` (sheets
  `baked_s9_a.jpg`, `baked_s9_b.jpg`): the coven warm and dim under its candles, the cells and sewer dark but legible.
- Tests from assets_dev 4 of 4: playtest 250 steps (311 checks), playtest_hostility 67, playtest_exit 49
  (`output/studio_cal/dd20/run/four_234052`).
- Open: D4's cellar hatch and jetty shaft still sealed, `q-d22.guild_wrong` does not yet move the party to
  `entrance:d4_trapdoor`, D4's plan gives `entrance:dd20_guild` facing `e` against 1024 elsewhere (A6).
- A3's relay (session 9): the trapdoor line on every step into the sump. `tools/dress.py` (before:
  `dress_before_s9_trapdoor.py`): `evt:trapdoor` is now a timer that checks once per visit (map variable
  `trap_checked`, appended last so earlier variables keep their numbers; cleared by `evt:trapdoor_reset` on leave)
  whether the party stands under the trapdoor (3328..3584, -768..-512, z <= -448) and only then says "The trapdoor is
  shut fast above you."; `playtest.yml` asserts the line on the drop and its absence on a walk and back under the
  trapdoor (before: `output/studio_cal/dd20/playtest_before_s9_trapdoor.yml`). Built into the root, audit 0 errors,
  recorded. Playtest in the root (315 checks), reinstalled 00:41 (`b_004101`), rebaked, 4 of 4 from assets_dev
  (playtest 315 checks, hostility 67, exit 49; `output/studio_cal/dd20/run/four_004150`), audit 0 errors / 2 mirror warnings.

## Session 22 (A8): the outfall walks both ways

A3-side's Q-D20 run found the outfall "one way" (stuck at (14559, 140) walking back from (14600, 1728) to (14550, 0)).
It is not the map: `oymap probe` walks both ways on one floor (z -512, sector 19), and a game probe from the niche back
to the east drain arrives when the walk clears hostiles (`output/studio_cal/a8_s22/probe/dd20_back4.yml`). Without
that the walk sticks at the niche's mouth against a live Sewer Stalker (actor 34, from (12672, 1920)): six stalkers of
the warren and the outfall follow the party into the niche (`probe/run3/log.txt`). No map change.

## Session 26 (A8, 2026-11-22)

- D-90 (c): the Golden Dragon (12350) lies at the alcove's foot (15680, 1856, -512) as a 3D ground item; the alcove's
  click event is gone (A3's `q-d20.dragon` becomes `map_gives`; the panel stays as the alcove picture). project.yml
  `items: {golden_dragon: 12350}`.
- F12(b): the seven coven doors (events 23-27, 30, 31) show MM6's temple door `t1d1` (fit) instead of the slab `twb1`.
- F14: the cross sump, the cistern's still water and the outfall's tidal pool are 48 deep (were 64-96): the party
  wades back out; `check_drops` 3 -> 0 pockets.
- Tests: playtest picks the dragon up (`pick_up`), Camilla's thanks on the status line (A3's hook). Installed 00:35,
  baked, 12/12 from assets_dev; audit 0 / 0.
- q-d20's and q-d22's stuck walks (at (14720, 1873, -512) and (6843, 1300, -256)) are test matters: the probe walks
  both; a Sewer Stalker (11401, hostile, the cross's ambush; actors 44 and 40) stands in the walk and A3's walk_to has no
  `clear_hostiles`.

## Session 27 (A8): A3 35th's request

- `project.yml` qbit `dragon_found` (113402) dropped (the Golden Dragon is a ground item since D-90; A3 deletes the
  bit). Generator only (`gen.py`). Installed (studio.yml only, no bake); audit 0/0, check_exits 0, check_drops 0; tests
  12/12 from assets_dev (`output/studio_cal/a8_s26/run/dd20/c012832`).

## Session 28 (A8): D-89 identity (the coven hall parted, the sewer lined)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, severity 3: "huge empty brown-brick halls with a few
cauldrons; one rock throughout the sewer") asked to halve the halls, add drying herbs, jar shelves, a pentagram floor,
and the sewer in 7d17 wet stone with plank walks. In `tools/geo.py`'s "D-89 identity" block (`identity:` in `gen.py`);
the generator reproduced the installed L4 first (snapshot `output/studio_cal/a8_s28/before/dd20/`).
- The coven hall (2,560 square) parted by an arcade of four dressed-stone piers (7d06 `7tws2`, 160 square, at x 320)
  into the rite hall (the star, benches, the sigil, the initiation cauldron) and an east aisle (the dormitory and gaol
  doors, shelves); the piers stand clear of every playtest's walking line.
- A five-pointed star of pale flags (`tfb2`, 2 high, 768 across) in the rite hall's floor at (-640, 640); no pentagram
  picture exists in MM6-MM8, so the star is geometry.
- Shelves of jars (`7t1cabs` blocks, 288 high) on the hall's north and east walls and the brewery's south wall. No
  herb picture or decoration exists: no drying herbs.
- The cells, the sewer's chambers and the warren lined with dark brick (`wall`, the store's) to 160 under 7d17's wet
  rock; the drains keep their timber kerb and plank walks.
- Not done: halving the halls' outlines (it would move every coven monster, door and test); the arcade halves the coven
  hall's read instead. DECIDE in the session report.
- `identity: {shape: sewer, family: 7d06}`.
- Installed 01:51, baked; audit 0 / 0, check_exits 0, check_drops 0, MAW 0, key_npcs 0; tests from assets_dev 12 of
  12 (`output/studio_cal/a8_s26/run/dd20/c015047`).
- Pictures: before `output/studio_cal/a8_s28/shots/dd20_before.jpg`, after (baked)
  `output/studio_cal/a8_s28/shots/dd20_after.jpg` (tour `output/studio_cal/a8_s28/dd20_tour.yml`, 26 of `tour.py rooms`).
- Rebuilt on oymap merge point 42 (the style chest): reinstalled 02:09, baked, audit 0 / 0, tests 12 of 12
  (`output/studio_cal/a8_s26/run/dd20/c020911`).
