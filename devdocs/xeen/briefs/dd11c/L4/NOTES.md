# DD-11C Troll Holes, third pocket (Hobstadt's hall): L4 notes

Lane A7 phase 3 (agent `xeen-a7-dd11`), 2026-11-20. Map 9164, `xeen_dd11c.blv`, class S, `world: xeen`. Built from the
MU-6 graph `devdocs/xeen/mockups/act3_graphs/dd11c.graph.yml` and `notes_d2.md` with D-25
(`mockups/act3_a7_decisions.md`), which wins: Hobstadt's court is its own peaceful row (Hobstadt's Guard 11075,
faction `hobstadt`, Q7), the warren's wild trolls hostile, tribute or trial befriends the holes' trolls only, the trolls'
stair's top is the `exit` preset with no question. Generator `output/studio_cal/dd11c/tools/gen.py` (shared
`output/studio_cal/dd11/tools/lib.py`; writes L1-L4; never hand-edit the written files). Cycle
`output/studio_cal/dd11/cycle.sh dd11c`; playtests `play.sh dd11c <name>`, `four.sh`; pictures `shots.sh dd11c`.
Scratch root `output/studio_cal/dd11/root` (shared).

## What was built

x east, y north; the pit (D2's third, widest hole) is at the origin, the hall straight east of it.

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| Pit bottom | 0 | octagon 1,024 across, shaft to 896 | — | Start; D2's sky; the hall gate east, the trolls' stair west, a hide flap south |
| Hall gate | 0 | 640 × 768 | 2 Hobstadt's Guard (30) | Before the carved log doors (two leaves, open at load) |
| Hobstadt's hall | 0 | 2,048 × 1,536, root vaults | 6 Hobstadt's Guard (30), Hobstadt (31) | The court in two rows; the throne of stacked boulders (t66cave) at the east end; the plate before it |
| The guild's gold | 0 | 640 × 640 | — | Through the east wall south of the throne: the sacks (A3's hoard) and the strongbox (T4) |
| The trolls' stair | 0 → 384 | 256 × 1,152 | — | Root-floored ramp west to the sod hatch (the exit) |
| Gnawed tunnel | 0 | 320 wide, 2,432 long (south, then east) | 3 Troll (10) | Behind the hide flap; the bone run comes up its south side |
| Trophy cave | 0 | 1,024 square | 3 Troll (11) | Trophies (hides) on the north wall, a chest (T3) |
| Cold slope | 0 → −512 | 256 × 1,152 | — | Down to the cold |
| Frost seep | −512 | 1,024 square | 2 Ice Troll (14) | Blue light, the stars-through-cracks line |
| Ice trolls' den | −512 | 1,024 square | 2 Ice Troll (13) | Their cache (T3); the antler door north |
| Bone run | −512 → 0 | 256 × 1,504 | 2 Troll (12) | Bone-paved, climbing to the gnawed tunnel (the loop) |

**Counts and sizes** (`output/studio_cal/dd11c/metrics.json`): 11 rooms (12 sectors with sector 0), 10.0 M units², 394
faces, 21 monsters (8 Hobstadt's Guard 11075 at 28, 8 Troll 11690 at 18, 4 Ice Troll 11692 at 38, Hobstadt 11073 at
42), 3 chests (T4 hoard, T3, T3), 3 doors (4 door records: the hall's two leaves, the hide flap, the antler door), 1 loop.

**Textures:** 14 distinct, 0 new: 7dirttyl, xohide, xdbark, xobones, xopoles, t66cave (the throne), xodaylt, the plain
chest set. Cap 30. MM8 snow on the cold floors was tried and dropped (a white floor in a
dirt cave; pictures `sheet2.jpg`, the fix `sheet3.jpg`).

**Hostility (D-25 Q7).** Every monster placed without the hostile flag: the world's relations.yml decides. Court and
Hobstadt (xeen_trolls_hobstadt) friendly at load, long on 113263; wild trolls (xeen_warren_trolls) long at load,
friendly on 113261/113262, long again on 113263 (the later rule wins).

**Map card.** As DD-11A: music 8, cave, treasure 3, encounter 10 (D-33), slot 1 `Xeen Warren Troll` tier 1 [2, 3] weight 100;
test row 9164 in the scratch root until A2 writes it. The court and Hobstadt are placed only (not card slots).

## Q-D13 in the hall

- **Talking to Hobstadt:** he is NPC 5110 (`monsters[].npc`, merge point 22): clicked while he is at peace, he talks.
  `plate:before_throne` (192 × 1,280 across the hall at x 2,688) still greets the party unasked once, the first time it
  crosses it while he lives and the court is not hostile (`evt:approach`, event 2): the source's Hobstadt is a step
  event before his throne (dark `maze0040`, square (7, 24), any facing: his portrait and "I am Hobstadt, Strongest of
  the Trolls. You will: ...", aaze0040:10-11, :13), spoken before anyone asks. The throne (`evt:throne`, event 16, hover
  "Throne") no longer speaks for him: while he lives and is at peace "A throne of stacked boulders. Hobstadt stands
  before it and watches you."; while he fights "Hobstadt stands before his throne with his club raised. He is done
  talking."; after his death A3's `q-d13.throne` (a Troll member is promoted; others read "The throne is vacant.",
  aaze0040:8-9). Once he is hostile (113263) the quest needs no talk: his death opens the hoard and the throne.
- **A3's topics** (NPC 5110): Give gold (tribute 113261), Sacrifice one (trial 113262, War Troll), Fight to the death
  (hostile 113263), Thieves' gold (after a deal).
- **A fight turns all** (`evt:court_fight`, event 8, a 2 s timer, once): a court troll or Hobstadt killed while 113263 is
  clear sets 113263 ("The court roars. Every troll under the forest is your enemy now."), so attacking without the
  topic turns the court and the wild trolls too.
- **His death** (`evt:hobstadt_slain`, event 14, kill timer): A3's `q-d13.hobstadt` (hobstadt_slain 113264) and "Hobstadt
  falls across the foot of his throne. The throne is vacant."; on every later load his group (31) is hidden
  (`evt:hobstadt_gone`).
- **The hoard**: the sacks (`evt:sacks`, event 15) call A3's `q-d13.hoard` (done 113266, 4,000 experience and 2,500
  gold; before a deal or his death its fail text; after, its else text). The strongbox (T4, `evt:chest_hoard`, event 4)
  opens under the same condition, else it runs the hook for the fail text (no map copy of A3's text).
- Map qbits 110980-110989: **none used**; A3's 113261-113266 read by number.

## Ways in and out (D-24, D-25)

- **In (A6's side):** D2's third hole (event 34) drops the party at the map's start, **(128, −64, 0) in room:pit, facing
  east (direction 0)**, toward the hall gate and the open log doors.
- **Out:** the trolls' stair's sod hatch (`evt:hatch`, event 12, the `exit` preset, no question) to `exit:d2_return`,
  A6's point **(1536, −17408, 928) facing west (180°)**. `playtest_exit.yml` measures the landing at
  **(1536, −17408, 929)**.

## Original lines

- Hobstadt's "I am Hobstadt, Strongest of the Trolls ..." and his three choices (aaze0040:10-11, :13; A3's NPC 5110).
- "Throne" (the hover) / "The throne is vacant." (aaze0040:8-9; A3's q-d13.throne).
- "Chest" (aaze0040:0). Ours: the landing, the gate's, the seep's, the trophies', the throne's while fighting, the
  court's roar, his fall.

## Checks (scratch root `output/studio_cal/dd11/root`, merge point 12)

- `fmt --check`, `validate` (L1-L4 no issues), `build` (0 warnings), `audit --reach --solve`
  (`output/studio_cal/dd11c/audit.txt`): no error or warning; 5 of 11 sectors on foot with the doors as they start (the
  warren behind the hide flap), 11 with them open; infos: two stretched faces (the hatch's daylight, one dirt face).
- Playtests 4 of 4 each (`output/studio_cal/dd11c/four.out`, logs `output/studio_cal/dd11c/run/`):
  - `playtest.yml` 77 steps: landing, the gate's peace, the hoard's refusal (sacks and strongbox), Hobstadt speaks on the
    plate, Give gold (113261, gold paid), the court still peaceful and the wild trolls friendly, the sacks (113266, the
    gold) and their else text, the strongbox, the throne's "Thieves' gold", the whole warren in peace (both chests, the
    seep's line, the antler door, the bone run), the trolls' stair, "RELOAD ok at step 73".
  - `playtest_fight.yml` 33: Fight to the death (113263), every troll kind hostile, the throne refuses talk, his death
    (113264 and the line), the vacant throne's fail text, the sacks to his killers, reload with his group hidden.
  - `playtest_hostility.yml` 46: court and Hobstadt peaceful, the warren hostile, kept over a reload; tribute befriends
    the warren and keeps the court; a gate guard killed without the topic sets 113263 and turns all (kept over a reload);
    kinds leave each other alone.
  - `playtest_exit.yml` 15; `playtest_x5_trolls.yml` 12: on X5 with tribute and trial set, X5's trolls (11070/11071)
    stay hostile, also after a reload (D-25 Q7's scope check).
- Pictures `output/studio_cal/dd11c/shots/` (`sheet1.jpg`, `sheet2.jpg`, `sheet3.jpg`), unbaked. Fixed after looking:
  the white snow floors (dirt now), the crystal decoration (pink coral in this world: stalagmites now).

## Dressing exceptions

None (audit clean). The throne (a set piece) stands against the east wall north of the hoard's opening, off the walking
line from the gate to the hoard.

## For the user

- Walk up the hall between the two rows of the court: Hobstadt speaks as you come before his throne; click him to
  talk again.
- Try a blow at a court troll without his challenge: every troll under the forest turns.
- Whether Hobstadt and his guards read as a king's court (they share the trolls' model; A2's looks).

## Sixth session (2026-11-20, lane A7)

- **D-33 (2):** rest encounters 10 % (`lib.py` map card; A2's row has it).
- **Lamp rule:** lights written with negative heights (meant as absolute z) lay under the floor, and the burrow's or
  stair's daylight above its ceiling: each now over its floor inside its room (`gen.py`; A1's audit and
  `output/studio_cal/a7/lampcheck.py` clean).

## D-34: the Darkside view at the hatch (2026-11-20, lane A7, seventh session)

- The sod hatch's view (`exit:hatch`, an upright face at eye level) is DD-13's new `xddaylt` (D2's pass road between
  dark forest and rock under the dim amber-grey sky) in place of XD-05's sunny Cloudside meadow `xodaylt`; the shared
  `DAY_LIGHT` (the shaft's and the burrow top's daylight) dimmed from a noon white [205, 200, 185] to the Darkside's
  [150, 140, 122] (`output/studio_cal/dd11/tools/lib.py`; before: `lib_before_d34.py`). Picture:
  `output/studio_cal/a7/s7_look/dd11a/01-hatch_day.png`.
- Audit no error or warning, build warnings 0. Installed, re-baked; from `assets_dev`: playtest (77), playtest_fight (33), playtest_hostility (46), playtest_x5_trolls (12), playtest_exit (15) 4 of 4 each
  (`output/studio_cal/a7/s7_mp15_chain.out`).

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The hide flap's doorway 128 wide (was 224).
- The trophy cave's hides: two single `xohide` panels 128 x 256 with roots between (`panel:trophies_2` added; was one of 512).
- The guild's sacks heap in `straw`.
- The shared `DAY_LIGHT` is now in L4 as D-34 meant ([150, 140, 122]).
- Audit: no `textures.*` finding.

## Fifteenth session (2026-11-21, lane A7 sub-agent)

- **Hobstadt talks himself** (merge point 22, `monsters[].npc`): `monster:hobstadt` carries `npc: 5110` (scene actor
  12). Kept: `plate:before_throne` and `evt:approach`, because the source greets the party unasked there (its step
  event at square (7, 24), aaze0040:10-11), and the plate's condition (no greeting once 113263 or 113264 is set). The
  throne's "speak for him" branch is gone (its line now); its fight line and A3's `q-d13.throne` after his death stay.
- `playtest.yml` (80 steps): the plate's greeting and Give gold as before, then the throne's line, then Hobstadt
  clicked (`interact_actor` 12) for "Thieves' gold". `playtest_fight.yml` still opens the fight from the plate.
- `xcycle.sh`: build warnings 0, audit 0 errors, 0 warnings. Installed with bake (01:52:20), stale bakes 0. From
  `assets_dev`, 4 of 4 each: `playtest` 80, `playtest_fight` 33, `playtest_hostility` 46, `playtest_exit` 15,
  `playtest_x5_trolls` 12 (`output/studio_cal/a7/s15_dd11c_four.out`).

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.12 / 168 / 0.21 -> 0.32 / 180 / 0.20; family d43 27 %
  (Hobstadt's hall).
- No change in s29.
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/dd11c/shots/`  (01-1_arrival.png, 02-2_hall.png, 03-3_trophy.png); all eight maps on
  one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named: Hobstadt's hall in d43's cut stone behind
  the hall gate with its trolls and throne, the trophy cave's skull heap.

- 2026-11-22 fixup (fourth orchestrator, for A7): `project.yml` had lost `map_code: DD-11C` and `units: {plan_grid: 512}`: s28's D-89 `identity` line in `output/studio_cal/dd11c/tools/gen.py` ended in a `#` comment that swallowed the rest of that line. Line split, L4 regenerated (only those two keys), rebuilt (BLV identical, studio file only), installed, no rebake; audit 0/0, exits 0, drops 0, tests 20/20 from assets_dev. `quests.py` keyed the map `DD11C` without it (DD-11B's player bit 11294 error); it now fails any L4 project whose key maps.yml does not know.
