# DD-26 Olympus Sewer, L4: notes

New S dungeon under D7's Olympus (dark maze0038, aaze0038), side quest Q-D28 Cyrano's Tribble, built with the Map
Studio from `devdocs/xeen/mockups/act6_graphs/dd26.graph.yml` and decider D-65 (`mockups/act6_a8_decisions.md`, which
wins) by `agent:xeen-a8-dd26` (lane A8 session 14), 2026-11-21. Key `dd26`, project `xeen_dd26`, stem
`xeen_dd26.blv`, map_stats 9178, world `xeen`, music 44.

## State and next steps

**Built in the scratch root only** (`output/studio_cal/dd26/root`: `cp -al assets_dev`, `worlds/xeen/data_tables/` a
real copy taken after A2's row 9178, A3's `q-d28` and A4's house 4815 landed; no test rows). Validate: no issues (L1-L4); build 0 warnings; audit of the installed map and of the
project (`--reach --solve --dressing --lights --doors --textures`, `output/studio_cal/dd26/audit_project.txt`):
**0 errors, 0 warnings**, one `click.silent` info (the house door: it opens a house screen). Solve: 10 of 10 sectors
at once by foot (6 with the doors shut), the vault after the password; the exit to D7 listed. `fmt --check` clean.
Texture budget 24/30, 0 new.

**Next (the lane lead):** DD-26 was installed and baked at 06:33 before D-67; reinstall the D-67 changes:
`INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd26`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd26` (rebake: the bed, the
spillway and the outfall moved; then `four.sh` from assets_dev). Baked pictures:
`ASSETS=$PWD/assets_dev output/studio_cal/dd26/shoot.sh things1`. `four.sh` now includes `playtest_in` (D7's grate, A6's, open since 06:44).

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd26/cycle.sh` (gen.py, fmt, validate, build, install into the root,
audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against `.oymap/last` first if anyone edited it by hand.
`python3 output/studio_cal/dd26/tools/sync_root.py` refreshes the root from assets_dev (relinks changed world files,
copies the tables afresh).

**Scratch** `output/studio_cal/dd26/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes), `tools/dress.py` (objects, wiring), `tools/tour.py rooms|things <name>` + `tools/sheet.py`, `tools/texsheet.py`,
`tools/house_rows.py`, `tools/sync_root.py`, `cycle.sh`, `four.sh` (`ASSETS=`, `N=`, `TESTS=`, `LOCK=`; every game
through `a8_s14/game.lock`), `shoot.sh <tour>`, `run/` (logs), `shots/` (sheets), `tex/` (texture sheets, schemas).
**Every project file of L1-L4 except the playtests and these notes is written by the generator.**

## What was built

One level at z 0 (x east, y north, z up); the channels sunk 128, the cistern 256:

- **Marble stair** (t3s2 marble: the knot-band dado `t3s2b` 256 high, `t3s2b1` above): the arrival at its foot
  (0, 0, 0) facing north; fourteen steps of 32 climb south to a head at 448 under the grate (the exit face, `xwcage`);
  the pinned scroll (`scroll`, once) on the west wall by the foot.
- **South conduit** (marble, 3,584 x 640): its sky-water channel (`7wtrtyl`) down the middle in two runs, walkways of
  256 on both banks, a dry crossing at x 0 between the stair and the den's door; the channels' ends slope up (bank 160).
- **Pets Unlimited** (d01's dressed stone `cwb`): the den's plank pair (`hhm1d|hhm1d2`) in the conduit's north wall;
  Cyrano's counter door (`door:pets_unlimited`, house 4815, `hhm1d` once) between two low counters on the north wall;
  five empty hanging cages (MM7's `7dec05`, hung from the vault by the build); the bed (`t2bedsht` on planks, 288 x 160)
  with its head against the east wall under a plank headboard 32 thick, 128 over the sheet (D-67 item 9); a food bowl.
- **West and east culverts** (d01's stone-channel face: `wall` blocks under rough `cfb1`, `tfb07` flags): channels along
  the outer walls, broken where the grates open; walkways of 320 along the inner walls; drain TR in the west culvert's
  inner wall.
- **West spillway** and **the outfall** behind grates (`xwcage`, slide up): a pool along the outer wall, a dry floor of
  288; the weir's ledge with the T6 chest and drain IB; the outfall's barred mouth and drain ES.
- **The gods' cistern** (marble, 4,864 x 1,024, vault 768): a clear basin sunk 256 between walkways of 320, its ends
  sloping up; drain BL in the north wall; the tribble door's landing off the east wall.
- **Tribble door** (marble landing): the bronze pair (`gcs05a|gcs05b`, two hinged leaves 192 x 384, gilt edges) with the
  voice's grille mouth (`xwcage`, 64 x 128) above.
- **Offering vault** (MM8 Temple of the Sun: `gtempw1`, `gtempflr`, gold-knotted `gtemprf` coffers): the T6 chest on a
  ledge on the east wall, a gilt statue (`7dec55`), gilded cups (`7dec46`, `7dec48`), bags of coin, a vase.

## Measurements

`oymap metrics` (`metrics.json`): **10 sectors** (S 6-15), **13.4 M units² of rooms** (14.4 with level tops; S 7-20; the
graph's "about 11"), 1 loop (the ring), **4 doors** (6 leaves: the den's pair, two grates, the bronze pair), **2 chests**
(T6), 20 placed monsters. Textures (`tools/xeen/texture_budget.py --root output/studio_cal/dd26/root --map DD-26`):
**24 of 30, 0 new** (five of them the chests' `7gt002*`).

Walking room (D-65 change 3; D-67 item 7): Xeen caps every indoor body's radius at 60 (`levelRadiusLimit`, D-32,
`world.yml`), so the Water Elemental (radius 100, 202 high) moves as a body 120 wide. Width cannot bind against
walkways and openings of 256 or more (conduit 256 + 256, culverts 320, cistern 320, spillway and outfall 288; every
opening on a walking line 256-384 wide); only its height of 202 can. **The lowest opening on a walking line is 320**
(the conduit's mouths, the culvert mouths, the den's door) and **every ceiling is 448 or more**. A body-size reach
check in the audit stays an A1 backlog item (D-67). `playtest_hostility.yml` walks one (D-68 Q2): a Water Elemental
from the east culvert's far end up the culvert, through the culvert mouth (320) and at least 1,000 along the cistern's
walkway to the party there.
The den's door, both grates, the four drains and the landing open onto dry floor (B2). Channels and pools along a wall
stop 16 short of it (no ledge to walk along), and the spillway's and the outfall's walls are 32 thick (no recess a
chasing body can wedge into: in a first run the elemental stuck in the outfall grate's 128-deep recess).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Lesser Water Elemental | 11625 | 55 | 3,575 | conduit 3, west culvert 3, spillway 2, cistern 2, east culvert 3, outfall 2, vault 1 | 16 |
| Water Elemental | 11710 | 62 | 4,464 | cistern 2, vault 2 | 4 |

**Kill XP** 75,056 for the party, **18.76k per member** (D-65). Groups of 2-3 (groups 1-8, one faction); the stair, the
den and the landing are quiet. Rest encounters (= A2's row 9178): `{monster: Xeen Water Elemental, tier: 0,
per_marker: [1, 2], weight: 100}`, encounter 10.

## Mechanisms (A3's q-d28 hooks)

- `evt:arrive` (timer, once while 117800 is clear): `q-d28.arrival` (its line, arrived_once 117800).
- `evt:scroll` (panel:scroll, hover "Scroll"): `q-d28.scroll` ("Search the drains.").
- `evt:drain_tr|ib|bl|es` (hover "Drain"): `q-d28.drain_*` (the piece once, 117801-117804, the autonote with the last;
  then "Drain" on the status line).
- `evt:bed` (hover "Bed"): `q-d28.bed` (one random T6 item, 117806; then "Nothing here.").
- `evt:pets_unlimited` (door:pets_unlimited, hover "Pets Unlimited", event 12): `evt.EnterHouse(4815)`; a residence
  of one opens straight onto Cyrano Jones (5614): Tribbles (25,000, `bought` 113560), Companions after.
- `evt:den_door` (the plank pair, hover "Cyrano sells the password.", aaze0038:12).
- `evt:tribble_door` (landing side): `Xeen.tribbleDoor(eventId, continueStep)`: the voice (aaze0038:5) is the typed
  prompt's own text with no message before it (B1); tribbles/tribble in any case: `q-d28.tribble_door` (117805,
  "Correct! You may pass.") and both leaves open (doors 5, 6); anything else `q-d28.tribble_wrong`. Once open it asks
  nothing. `evt:tribble_back` (vault side) opens the pair; `evt:tribble_load` opens it on every load while 117805 is set.
- `evt:exit` (the grate at the stair's top, hover "Climb up to Olympus", event 10): the map's own Yes/No "Climb up to
  Olympus?" (`AskChoiceWithAnswerSteps`, D-67 item 8, D-66; A3's `q-d28.stair_exit` line): Yes moves to D7's
  `entrance:dd26_stair` (`{direct = true}`), No stays.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d7_stair` (= start) | (0, 0, 0), north (512) | (0, 0, 0) facing 512 | D7's `evt:sewer_grate` (A6, still sealed): `evt.MoveToMap(0, 0, 0, 512, 0, 0, 0, 0, "xeen_dd26.blv")` |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| the grate at the stair's top | D7 `entrance:dd26_stair` (-8704, 8192, 1808) | **(-8704, 8192, 1808)** | 0 |

## Ids

- Map qbits (A3's names): arrived_once 117800, drain_tr 117801, drain_ib 117802, drain_bl 117803, drain_es 117804,
  door_open 117805, bed 117806 (117807-117839 free). Read by the tribble test: bought 113560.
- Doors: den 1-2, outfall grate 3, spillway grate 4, the bronze pair 5-6. Chests 0 (spillway), 1 (vault).

## Playtests

`output/studio_cal/dd26/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd26.blv`: see "Test runs" below for the 4-of-4 results.

| Test | What |
|---|---|
| `playtest.yml` | from D7: the arrival (position, facing, A3's line); the scroll; the den's pair; Cyrano at the counter; the bed once, then "Nothing here."; the four drains once each, then "Drain"; both grates; the spillway's chest; the password ("TRIBBLE"), both leaves; the vault's chest |
| `playtest_password.yml` | the prompt's own text is the voice; a wrong word ("Wrong! You may not pass!", shut, 117805 clear); a save and a load; "Tribbles" ("Correct! You may pass.", open); a save and a load (still open; a click asks nothing); into the vault |
| `playtest_tribble.yml` | with 20,000 gold "yes": "Maybe some other time."; with 25,000 "no": the same; "Yes": 25,000 taken, the Tribble 12362, bought 113560; Companions: the TRIBBLES line. A4's house 4815 (real since 06:3x) |
| `playtest_exit.yml` | up the stair, the grate: "Climb up to Olympus?", No stays, Yes: D7 at (-8704, 8192, 1808) facing 0 |
| `playtest_hostility.yml` | 16 + 4 hostile at load, none peaceful; a Water Elemental from the east culvert's far end comes through the culvert mouth (320) and at least 1,000 along the cistern's walkway, within 900 of the party 2,000 west of the mouth (D-68 Q2; it shoots: its first attack is a Water missile, so it stops about 750 off, not at melee range); both kinds spawned side by side in the cistern do not take each other on |
| `playtest_in.yml` | from D7 (A6's grate, event 104, open since 06:44): "Descend into the sewer?", Yes: the stair's foot (0, 0, 0) facing 512 |

## Texture fit exceptions

None (audit: 0 texture findings).

## Dressing exceptions

None (audit: 0 dressing findings).

## Waiting on

- Nothing: A6 opened D7's `evt:sewer_grate` (104) at 06:44; `playtest_in.yml` passes 4 of 4 against it.
- No test rows: A2's map row 9178 and monster rows 11625/11710, A3's `q-d28` hooks and topics, A4's house 4815 and npc
  5614 (`towns/dd26.yml`, no longer `planned`) are all real; the root's tables are a plain copy of assets_dev's.

## Lines for A3 (map-local, written inline)

- The den's door hover: "Cyrano sells the password." (aaze0038:12).
- The grille mouth over the bronze pair (status line): "A voice waits behind the grille."
- The exit's hover "Climb up to Olympus" and its question "Climb up to Olympus?" (`q-d28.stair_exit`'s line, written inline).

## Sounds for AU

`xeen_amb_sewer` beds over the conduit and the cistern (`pan: false`); `rushing water loop` on the conduit's two runs;
`water lapping loop` at the cistern's basin; `drip03` in the cistern (wait 4-10 s); `waterfall loop1` at the outfall's
barred mouth. Tribble purring in the den is AU's (none placed: no shipped purr).

## DECIDE (all six accepted by D-67)

1. **The scroll is a wall panel** (the shipped `scroll` picture, 64 x 64 shown at 96, as XD-14's pinned scrolls), not a
   decoration: no shipped note or scroll decoration has an indoor model. Hover "Scroll", click A3's hook.
2. **Four doors, not the graph's five**: the vault's inner grille behind the bronze pair is left out (the pair alone
   keeps the vault; S's band is 3-8).
3. **The statue stands** (`7dec55` by the north wall): no decoration lies toppled.
4. **The channels' and the basin's ends slope up** (bank 160 and 288), so a party (or an elemental) that falls in walks
   out at an end; the long sides stand upright.
5. **Floor 13.4 M units²** against the graph's "about 11" (S's cap is 20): the 256 walkways and the cistern's 320 ones.
6. **The cages are empty hanging cages** (`7dec05`) hung from the den's vault; MM7's other two cages hold a skeleton and
   a prisoner, wrong for a pet shop.

## Pictures (looked at, scratch root, no bake)

`output/studio_cal/dd26/shots/things1_1..3.jpg` (the arrival, the stair and its grate, the scroll, the conduit, the den's
door, the counter and Cyrano's door, the bed, both culverts, a drain, the spillway's grate and room, the cistern and its
basin, drain BL, the bronze pair and its grille, the vault and its chest, the outfall), `fix1_1.jpg` (the den after the
cages were hung from the vault). Changed after looking: the cages first floated over the counters with a skeleton and a
prisoner in two of them (now empty, hung from the vault).

## Test runs

All five 4 of 4 from the scratch root (`output/studio_cal/dd26/run/four_061947`, summary `four_s14.txt`): playtest 119
checks, password 41, tribble 45, exit 15, hostility 21. `playtest_in.yml` waits on A6.

## Session 14 follow-up (D-67)

D-67 (`mockups/act6_a8_followups_d67.md`, DD-26 part) accepted the six DECIDE items and asked for four changes, all
made in the generators: the grate's own Yes/No (item 8), the bed's headboard (item 9, the bed turned so its head meets
the east wall), the walking-room reasoning above (item 7) and the reach step in `playtest_hostility.yml`. The reach
step found the elemental wedged in the outfall grate's recess and walking a 64 ledge beside the culvert's channel: the
channels now stop 16 from the wall and the spillway's and outfall's walls are 32 thick (both rooms 96 nearer the
culverts; their contents moved with them). Audit 0 errors, 0 warnings. Pictures: `shots/fix2_1.jpg` (the bed with its
headboard, the stair's grate, the outfall, the spillway, the east culvert; unbaked).

D-67 runs from the root (real rows only): all five 4 of 4 (`run/four_064443`, `four_s14b.txt`: playtest 119, password
41, tribble 45, exit 30, hostility 32), and `playtest_in` 4 of 4 against A6's opened grate (`run/four_064721`, 18).

## Session 21 (A8): AU's sounds

`sound:tribbles` (AU's `xeen_tribble_purr`, radius 1,000, inner 300, 0.45) purrs in the den. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8, 2026-11-22)

- F16: the stair grate's exit (event 10) no longer asks "Climb up to Olympus?": the `exit:` effect shows the standard
  entrance window (OK/Close) to D7's entrance:dd26_stair (`tools/dress.py`; playtest_exit: Close stays, OK leaves).
  Audit 1 `entrance.question` error -> 0 / 0. Installed 00:15, baked, tests 24/24 from assets_dev. D7's own sewer grate
  question into this map (A6's event 104, playtest_in's `answer_input: Yes`) changes with A6's D7 F16 rebuild.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:27): the generator reproduced the L4 unchanged and the build equals
the installed map (its two chests are already 7gt002; the fitted bed top stands on the floor), nothing to install;
audit 0/0, check_exits 0, check_drops 0. Chest pictures: output/studio_cal/a8_s29/shots/dd26_chests.jpg (vault) and
dd26_spill.jpg (the weir's ledge), both against a wall.
