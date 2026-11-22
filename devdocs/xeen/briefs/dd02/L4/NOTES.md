# DD-02 Ellinger's Tower (L4): notes

Lane A8 (agent `agent:xeen-a8-dd02`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd02.graph.yml`) with decider D-26 (`mockups/act3_a8_decisions_a.md`), which wins
where they differ. One script, `output/studio_cal/dd02/tools/gen.py`, writes all four levels: L1 plan and project,
L2 the same with extents and heights, L3 the rooms, L4 the objects and wiring. The playtests and this file are written
by hand. `output/studio_cal/dd02/cycle.sh L4` generates, formats, validates, builds, installs into the scratch root
`output/studio_cal/dd02/root` and audits.

## What was built

Map 9151, `xeen_dd02.blv`, class M, inside Castleview's walls on D1 Castleview Vale. It carries M17 (the question, the
gauntlet, the password, Ellinger), M18 (his list) and M19/M26 (Ellinger takes the disks in his study). Party 20-22,
band 14-24, 50 monsters, treasure 2 (the boot closet 3), music 34.

There are 32 rooms on five floors, 480 apart, as the graph has them: ground 0, the gauntlet 480, the library 960, the
tapestry floor 1440 and the study 1920. Floor area is 31.2 M units² (27.6 M walkable). Every room's ceiling stays at
least 64 under the floor of any room above it. The plan frame is x east, y north.

| Floor | Rooms (texture theme) | Monsters |
| --- | --- | --- |
| 0 | Entry hall (arrival, exit, dead mirror, 2 columns), Hall of the Question, storeroom ($), lift shaft foot | store: 3 Vampire Bats |
| 0-1 | Main stair, flight 1 (behind the question's door) | — |
| 1 | Stair landing, Hall of Wards (two warded circles, td1), bat roost (broken window), tapestry gallery (3 tapestries), back stair foot | wards: 4 Flying Feet, 2 Guardians; roost: 6 Vampire Bats; gallery: 4 Flying Feet |
| 1-2 | Main stair flight 2, back stair flight 1 | — |
| 2 | Stair landing, the library (bookcases, 2 stacks, 3 lecterns, chandelier), reading room ($), Gargoyle gallery (columned bays), back stair landing | library: 4 Gargoyles; reading: 2 Gargoyles, 2 Gargoyle Lords; gallery: 4 Gargoyles, 4 Lords |
| 2-3 | Main stair flight 3, back stair flight 2 | — |
| 3 | Stair head, Tapestry maze (3 tapestries hung on frames, 3 wall tapestries; an arm east), Beholder loft (roof beams), trapped walk (320 wide, 4 trap plates), back stair top, crate room (storeroom, $), last stair foot | maze: 5 Vampire Bats; loft: 6 Beholder Bats; walk: 4 Beholder Bats |
| 3-4 | The last stair (from the walk's west end only) | — |
| 4 | Top landing, the last door, Ellinger's study (desk, list, charts, shelf, boot rack, Ellinger), lift head, boot closet ($$) | Ellinger (peaceful) |

The main stair is a switchback column at x 768-1408 with lanes 288 wide and flights of 15 steps of 32. Flight 4 rises in
lane R above flight 2 and is reached only from the trapped walk's west end. The servants' back stair is a second
switchback at x 3968-4608. The lift shaft (x -1024 to -512, y 1344-1856) is one room 2,400 tall. It opens only at
the ground floor (the entry hall) and at the top (the lift head): **no opening on floors 1-3** (D-26).

**Critical path:** entry, the question's door, the main stair to the tapestry floor, the maze, the loft door, the loft,
the trapped walk round the outer wall, the last stair, the last door, the study. The gauntlet floor and the library
floor are optional, as the graph has them. They hold the two library books, the Book of Sorcerer's Knowledge and two
chests.

**Loops:** the back stair joins floors 1-3 behind tapestries (the tapestry gallery ↔ the gargoyle gallery ↔ the
tapestry maze's arm), and after M17 the lift closes entry ↔ study into a ring.

**Counts:** 32 sectors (20-45), 31.2 M units² (30-90), 50 monsters (45-75), 4 chests (3-7), 11 doors (6-16):

- the question's door;
- the doors of the store, the roost, the reading room, the loft, the last door and the boot closet;
- two secret panels;
- two lift gates.

There is also one lift. No spawn points.

## Monsters and kill experience

All are placed, on the world's rows (D-26, the graph's mix): Vampire Bat 11311 (L14) ×14, Beholder Bat 11312 (L20) ×10,
Gargoyle 11540 (L16) ×10, Gargoyle Lord 11541 (L22) ×6, Flying Feet 11600 (L18) ×8, Guardian 11601 (L24) ×2. Groups 1-10
by room, no `hostile`, no map relations.

Kill XP (the rows' experience): 14×336 + 10×600 + 10×416 + 6×704 + 8×504 + 2×816 = 24,752, **6.19k per member** of four.
That is 9 % over the graph's 5.7k.

**Ellinger** stands immobile behind his desk (group 20). Since session 7 he is A2's row **11901** `Xeen Ellinger`
(faction `xeen_character_ellinger`, friendly to the party in `relations.yml`), as Crodo is 11900. Until then his body
was the engine's peaceful Peasant 364.

The map card's slots, for A2's row:

- `Xeen Night Bat`: tier b, 2-3, weight 40;
- `Xeen Gargoyle`: tier a, 2-3, weight 35;
- `Xeen Construct`: tier a, 1-2, weight 25.

Encounter chance is 0, since all monsters are placed. The scratch root carries a test row for 9151 in this form.

## Mechanisms and hooks

- **The question** (`evt:question`, the question hall's side of `door:question`). Before `question_passed` (111340) a
  click runs `m17.question` (A3's text) and asks with three buttons: "Let him take up his sword", "Cut him down" and
  "I just don't know".
  - Answer 1 or 2 runs `m17.question_right` (qbit, once). A one-second timer (`evt:question_open`) then opens the door
    ("The stair door swings open.").
  - Answer 3 runs `m17.question_wrong` ("Begone!" with a "Leave the tower" button). Then comes a direct move (no
    leave window) onto D1 at the tower door's return point.
  - A message window before a direct `MoveToMap` is lost in the map change, so the "Begone!" window comes first and
    its button moves. Closing it moves too (the fallback step).
  - Once the question is passed the door is a plain door. From the stair's side it is always plain
    (`evt:question_back`).
- **The password** (`evt:pass`, from the last door's side). The studio's `question` asks "Who do you seek?" (aaze0056:2).
  "Ellinger" runs `m17.password` ("You may pass!", qbit 111341 once; its else text later) and opens the door. Any other
  answer runs `m17.password_wrong` ("Begone!"). It asks on every visit, as the source does. From the study's side the
  door is plain.
- **The lift** (D-9.2, D-26). `lift:cage` is a floor 448 square, 16 thick, travel 1,920, speed 480 (4 s), in the closed
  shaft. It has four buttons:
  - call at the foot (entry hall) and call at the top (lift head);
  - "up" inside the shaft at the foot and "down" inside it at the top (height 2,032).

  Each button has the condition `XeenQuests.can("m17.tower_lift")` and runs the hook otherwise, which shows its fail
  text: "The lift does not move. ...", before `m17.done`. The cage carries two gates:
  - the foot gate is open while the cage is down;
  - the top gate rises with the cage, at speed 48, so it is fully open only after the cage has arrived (no fall into
    the empty shaft).
- **Ellinger** (NPC 4954). The studio cannot give a placed indoor monster its NPC (Words needed, as DD-04), so his desk
  (`platform:desk`, hover "Ellinger") runs `evt.SpeakNPC(4954)`. A3's topic "Alamar" with the orb sets `m17.done`,
  `chest_still` and `m18.started`. A step cue the first time the party enters the study: "Ellinger looks up from a
  desk heaped with star charts and boots."
- **The Book of Sorcerer's Knowledge** (library lectern, D-26). This follows the hook's `where`, which names the library;
  the graph put it on a study shelf.
  - A member who has read it gets `m17.sorcerer_book_again`.
  - The clicking member's `ActualIntellect` ≥ 20 (items and potions count) gives +2 BaseIntellect, player bit 11312 and
    `m17.sorcerer_book`.
  - Below 20, the member takes physical damage of a tenth of the member's present hit points, counted in tens. The
    scripts read no maximum: `IsAtLeast(MaxHealth, n)` is always true. Then `m17.sorcerer_book_hurt`; nothing is used
    up.
- **Book of Fire / Book of Electricity** (library lecterns). +5 FireResistance / AirResistance, once per character
  (player bits 11313 / 11314), with the source's titles and "+20 Fire (permanent)." rescaled to "+5 Fire
  (permanent)." / "+5 Elec. (permanent).". A second read gives "You learn nothing more from the book." (aaze0054:5-8,
  :11). No hooks exist for these two; the map writes them.
- **Book o' Boots** (the boot rack by the desk): `m17.book_of_boots`. **Ellinger's list** (side table):
  `m18.sources_note` after `m18.started` (111360). Before that it shows "Columns of figures about energy disks.
  Ellinger has not finished it."
- **The dead mirror** (entry hall, A6's silvered glass `xkmirror` in a t1trima frame, D-37 (2)). Flavour only, no prompt (D-26): "The mirror does not
  respond." (aaze0053:11) before `m26.stage4` (111522). After it: "The mirror shows Ellinger's study, and a small sign:
  'Private. Use the one in the square.'"
- **Tapestries** (aaze0054:0-2):
  - The gallery: the west two say "Nothing happens"; the east one ("Click") opens the back stair's secret panel
    `door:back1`.
  - The maze: the west and north ones say "Click. Nothing happens."; the one at the arm's east end ("Click") opens
    `door:back3`.
  - Both panels are secret slide-up leaves of the wall's marble, and can also be found and clicked.
- **Trapped walk:** four floor plates of t1f2 (a visible tell on t1f3). Each step casts Fire Bolt (spell 2, expert,
  level 8) from the outer wall at the plate: "A bolt of fire leaps from the wall!".
- **Arrival:** a one-time window (`arrived_once` 117080). Every entry: the status line "Ellinger's Tower.".

## Qbits, player bits, items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | 117080 | the map's own (provisional block 117080-117119); the only map qbit used |
| `question_passed` | 111340 | M17, set by `m17.question_right`; read by the door and its timer |
| `password` | 111341 | M17, set by `m17.password` (read only through the hook) |
| `m17_done` | 111342 | M17, read by `m17.tower_lift` (A3's topic sets it) |
| `m18_started` | 111360 | M18, read by Ellinger's list |
| `m26_stage4` | 111522 | M26, read by the dead mirror |
| player bit | 11312 | Book of Sorcerer's Knowledge (+2 Intellect) |
| player bit | 11313 | Book of Fire (+5 Fire resistance) |
| player bit | 11314 | Book of Electricity (+5 Air resistance) |

There are no items of the map's own. The playtest grants the orb (12331) for Ellinger's topic. Map variables: only the
studio's `once.*`.

## Exit

`exit:d1` is on the entry hall's west wall: the front door, t1d3, 192 × 320. It uses the `exit` preset (the game's
window "Do you wish to leave Ellinger's Tower?", D-24) and leads to `exit:d1_tower`, **live** onto D1 at A6's return
point for the tower door (D1 event 102, `thing:ellinger_tower`, its face at 3285, 9321): **(2560, 9216, 1152), facing
east (0)**. Facing east means facing the tower: A6 gave that facing, not the brief's "facing away". Measured with
`playtest_exit.yml`: the party lands there and walks off north on D1. The question's answer 3 lands at the same point
(`playtest_b.yml`).

**D1's door into this map** (A6's `door:dd02`): the start point is **(-1216, 640, 0), facing east (0)**, just inside the
front door.

## Textures (32 distinct, 1 new: xkmirror; cap 45, ≤ 8 new)

- MM6 Agar's Laboratory 6d19 (the towers family):
  - walls: t1wl0lg (rose and white marble brick: entry, store, maze, closet), t1wl9ctl (column walls, once over the trim,
    the plain t1wl4cts above: question hall, wards, library, reading room, study, last door), t1wl4cts (stairs,
    shaft, lift head), t1wl7ctb (roost, loft, walk,
    back stair, crate room);
  - floors: t1f1, t1f2, t1f3;
  - the rest: ceiling t1c3, trim band t1trima, doors t1d3, columns t1spcla, the carved niches t1spclb over the
    question's door and the last door, and the roost's broken window t1wl1ctl.
- MM7 Castle Harmondale 7d29 tapestries: tap1, tap4, tap7.
- Furniture: bookcases bookcas1, bookcas2; desks and lecterns deskside, desktop.
- The rest:
  - the wards' circles: td1;
  - the mirror: xkmirror (A6, Xeen's new texture; session 7), framed in t1trima;
  - the chests: MM6 ch1, 7 textures;
  - buttons: 7t1butt, 7t1butts.
- `python3 tools/xeen/texture_budget.py --root output/studio_cal/dd02/root`: DD-02 M 32/45, 0/8 new. Nothing waits on
  A6.

## Original lines

- "Exit Ellinger's Tower?" (dark/aaze0053:0): the exit's hover title.
- "The mirror does not respond." (aaze0053:11): the dead mirror.
- "Tapestry" / "Click" / "Nothing happens" (aaze0054:0-2): the tapestries.
- "Book of Fire" / "+20 Fire (permanent)." → "+5" / "Book of Electricity" / "+20 Elec. (permanent)." → "+5" / "You
  learn nothing more from the book." (aaze0054:5-8, :11).
- "Who do you seek?" (aaze0056:2): the last door's question. "You may pass!" and "Begone!" are A3's hooks.
- A3's hooks carry the question (aaze0053:3-4), the Book of Sorcerer's Knowledge (aaze0056:5-7, +2) and the Book of
  Boots (:9).

## Presentation

Music 34 (map_stats). Placed sounds:

- wind at the roost's broken window and under the loft's roof (`whistling wind`);
- the wards humming (`humming`);
- something simmering in the study (`bubbling cauldron01`).

Lights: 23. The marble rooms are lamplit (ambient 18-24), the wards pulse blue, the loft is red (the bats' eyes), and the
bat floors are dim (12). There is no bake in the scratch root: the lane lead bakes after install.

## Pictures looked at

- `output/studio_cal/dd02/look1_1.jpg` to `look1_4.jpg`: 45 shots of every room, each door closed and open, both secret
  panels open, the stairs, the lift head and the shaft from the foot.
- `look2_sheet.jpg`: after the fixes.

Fixed after look1:

- The entry's two columns stood on the walking line from the front door and hid it. Now two columns stand by the north wall's corners, off every line between the doors.
- A sconce sat in the store's doorway.
- The lift gates were a stretched t1doors smear. Now they are 224-wide openings with the t1d3 door.
- The mirror was a curtain (t1curtl). Now it is glass2.
- The star charts were a brick-looking panel. Now they are a table.
- The chests were two kinds (17 textures). Now they are one kind, ch1.

Floor area was raised from 29.7 to 31.2 M: wider entry, study, store, closet and maze, and a longer loft.

The secret panels show the engine's red secret pulse to a party with Perception.

## Checks (scratch root, `--world xeen`)

- `oymap validate`: no issues. `oymap build`: 0 warnings.
- `oymap audit --reach --solve`: no error and no warning. 0 faces in one plane. 32 of 32 sectors reached with every door
  out of the way (3 with the doors as they start). The only finding is one info (the password's answer).
- Dressing: 0 findings. The crate room is a storeroom (`store: true`) with 7 barrels and 3 sacks in clumps by its
  walls, and its chest by the west wall.
- `fmt --check`: clean on L1-L4.
- Playtests (`output/studio_cal/dd02/four.sh`, 4 of each; logs in `output/studio_cal/dd02/four2.out` and
  `run/four_*`):
  - `playtest.yml` (204 steps): the critical path through every mechanism, the lift both ways, a reload;
  - `playtest_b.yml`: answer 3 puts the party on D1;
  - `playtest_hostility.yml`;
  - `playtest_exit.yml`: the front door onto D1.

## Words needed

1. **`monsters[].npc` indoors** (objects.yml), as DD-04 found. Workaround: Ellinger's desk runs `evt.SpeakNPC(4954)`;
   clicking Ellinger himself says nothing. (A1)
2. **A message that survives a direct map move** (`leave` / `MoveToMap(..., {direct = true})` after a
   `SimpleMessage`): the window is lost in the move. Workaround: the "Begone!" window is a one-button choice whose
   button (or closing it) makes the move. (A1)
3. **A stat read for scripts** (a member's maximum hit points): `IsAtLeast(MaxHealth, n)` is true for every n.
   Workaround: a tenth of the present hit points, read in tens with `IsAtLeast(HP, n)`. (A1)

## Dressing exceptions

None (the audit has no finding).

## Texture fit exceptions

- `textures.family_switch` on the dead mirror (faces of xkmirror beside t1c3): the dark t1c3 strips are the mirror's
  frame (D-37 (2): "a frame or trim if the wall round it is unlike it"); the check reads them as wall tiles. Kept.

## DECIDE

- ~~Ellinger's body~~: settled, A2's row 11901 (session 7).
- **Where the Book of Sorcerer's Knowledge lies.** As built, the library (A3's hook text). The graph puts it on a shelf
  in the study.
- **Arrival facing on D1.** As built, A6's return point facing east, toward the tower. The brief asks for "facing away".
  The fix is one line (`D1_FACING`) if A6 agrees.

## What the user should look at

- The question's door: three buttons. The third puts the party back in Castleview at once, after "Begone!".
- The last door asks "Who do you seek?" on every visit (type Ellinger).
- Talking to Ellinger means clicking his desk, not him.
- The lift: after Ellinger has spoken, call it at either end. Inside the shaft one button goes up at the foot and one
  goes down at the top. The top gate opens slowly as the cage arrives.
- The tapestries: only one in each tapestry room hides the real button.
- The trapped walk's plates are visible as a different floor tile.

## State and next steps

L4 is complete in the scratch root. The lane lead installs into `assets_dev` and bakes. A2 writes the map row from
the slot lines (the scratch root carries a test row).

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 12 oymap (byte for byte the agent's build), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh dd02`; `b_182855`). Baked (`a8_s5/bake.sh dd02 <scratch root>`,
  profile `tools/lighting/baked_indoors/profiles/xeen_dd02.yml`, XD-08's values; `stale_bakes.py` 0). Baked pictures
  `output/studio_cal/dd02/baked_a.jpg` (looked at): the marble halls bright, as 6d19 is; the tapestry gallery's red
  blocks are the secret panels' pulse for a party with Perception; library, stairs and doors read right.
- **Waiting on:** A2's row 9151 (tests from assets_dev: `ASSETS=$PWD/assets_dev output/studio_cal/dd02/four.sh`);
  **Ellinger's body is the engine's Peasant 364**, a stand-in: A2 to give him a character row of his own as Crodo's
  11900 (`Xeen Ellinger`, peaceful, a mage's look), then the map takes it.
- A2's row 9151 landed; **playtests from assets_dev 4 of 4** under D-32's levelRadiusLimit 60
  (`output/studio_cal/a8_s5/d32_all.out`): playtest, playtest_b, playtest_hostility, playtest_exit.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/dd02/tools/gen.py`, copy before the
change `gen_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The gargoyle gallery's first west sconce stood in the library arch (y 1184-1632): now on the west wall south of it (y
  896).

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/dd02/audit_lights.txt`): lights
  errors/warnings before **2/0 (in_doorway, wall_missing)**, after **0/0**; no dressing finding. **Light exceptions:**
  none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd02` (build `output/studio_cal/dd02/b_192836`), baked
  (`output/studio_cal/a8_s5/bake.sh dd02 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_dd02.yml`),
  `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from assets_dev, each 4 of 4**
  (four.sh; record `output/studio_cal/dd02/lights_post.out`): playtest 4/4 (204 steps); playtest_b 4/4 (15 steps);
  playtest_hostility 4/4 (29 steps); playtest_exit 4/4 (16 steps).
- **Pictures** `output/studio_cal/dd02/shots/lights_mp14/`, looked at: the sconce on the gallery's west wall beside the
  library arch.

## Session 7 batch (texture fit, Ellinger's row, the mirror, sounds)

By `agent:xeen-a8-dd02` (lane A8 session 7), 2026-11-20. Changed in the generator
(`output/studio_cal/dd02/tools/gen.py`; before the change `gen_before_s7.py`, which reproduced the installed L4 byte for
byte first). Two records: "session 7: texture fit ..." and "session 7: the mirror's frame in dark marble t1c3".

- **Ellinger** is A2's row **11901** `Xeen Ellinger` (a mage's robe; faction `xeen_character_ellinger`, friendly in
  `relations.yml`), in place of the Peasant 364 stand-in. NPC 4954 still talks through the desk. `playtest_hostility`
  asserts one 11901, not hostile, and no 364; `playtest` asserts him in the study before the talk.
- **t1wl9ctl** (a band one storey high: columns under a Greek-key frieze) was 1.5 times up 384-high walls (2.6 in the
  study, 2 whole in the question hall). `theme:hall` now lays it once as a band over the trim (32-288) with the
  plain column-wall blocks t1wl4cts above it to the ceiling (128 in the 416 rooms, 256 in the question hall, 416 in
  the study). The columns stand on the trim and the frieze runs round each hall at one height. This also clears the
  question hall's `storey_stacked` warnings.
- **Desks**: deskside (wood under a brass edge, a band 64 high) is scaled to each platform's rise (`scale` = rise/64)
  so the edge shows once at the top: lecterns 1.25, reading table 1.125, desk and tables 1.25, boot racks 1.5 and 2.5.
  desktop (a 2:1 picture with a lion, a note and an inkwell) lies once on tops cut to 2:1: desk and reading table
  256 x 128 (were 384 x 128) at scale 2, charts 192 x 96 at 1.5, the list 128 x 64. An `offset` brings the picture's
  corner to each top's corner. The lecterns show its corner, and the boot racks' long tops are the dark marble t1c3
  (as the bookcases' tops). Two candles moved onto the smaller tops.
- **The dead mirror** (D-37 (2)): A6's `xkmirror` in place of glass2, 192 x 288 as a tile, in a frame of 32-wide
  t1c3 strips. A t1trima frame washed out in the hall's bright bake, so the glass read as a white sheet.
- **Sounds**: `xeen_lift` (`evt.PlaySoundName("xeen_lift", -768, 1600, 960)`, the shaft halfway up the cage's travel)
  on each of the four lift events when the cage moves (not on the refusal). The bed `xeen_amb_tower` is one source in
  the middle of the tower (the library floor, z 1024), radius 5200, inner radius 2600, volume 0.35. It reaches every
  room on the five floors, so no two beds stack.
- **Audit** (`oymap audit --reach --solve`): before 29 errors, 9 warnings (21 `trim_tiled` t1wl9ctl, 8 `trim_tiled`
  deskside, 5 `tile_seams` desktop, 4 `storey_stacked` t1wl9ctl); after **0 errors, 2 warnings** (the mirror frame's
  `family_switch`, kept above); 32 of 32 sectors reached; no dressing, door or light finding. Build: 0 warnings,
  including merge point 17's one-size-per-texture warning. Textures: 32 distinct (glass2 out, xkmirror in: 1 new).
- **Tests** from assets_dev after the second install and its bake (`output/studio_cal/dd02/s7_post.out`, logs
  `run/four_220246`; the first install's run `s7_post_1.out` passed the same): playtest 4/4 (204 steps), playtest_b
  4/4 (15), playtest_hostility 4/4 (31), playtest_exit 4/4 (16). `stale_bakes.py` lists no DD-02 bake.
- **Pictures** `output/studio_cal/dd02/shots/s7/b/` (sheets `sheet_0-2.jpg`; the first take without HUD-off in
  `shots/s7/`), looked at:
  - the mirror near, mid and wide: the pale glass in its dark frame. It reads as a mirror catching the hall's light.
  - the question hall and the wards: columns on the trim, the frieze at one height, plain blocks above.
  - the library, a lectern (the desk picture's corner, the brass edge once), the reading table and Ellinger's desk
    (the desk top once, whole).
  - Ellinger in his mage's robe behind the desk; the study's tall walls; the boot racks; the charts; the shaft and
    the lift head.

## Session 8: rebake (darker xkmirror)

Lane lead (A8 session 8). A6's `xkmirror` v2 (luma 204 -> 134, dim pewter) for the pale dead mirror; rebaked 22:59
(`output/studio_cal/a8_s8/rebake_mirrors.out`, profile unchanged; `stale_bakes` none). **Not yet done:** the mirror
pictures (`a8_s8/tour_dd02.yml`) and the tests 4 of 4 from assets_dev (`a8_s8/queue_polish1.sh`).

**Session 9 (lane lead):** done. Pictures `output/studio_cal/dd02/shots/s8/` (sheet `output/studio_cal/a8_s9/dd02_s8.jpg`):
the mirror is dim pewter in its `t1c3` frame. The room around it is as bright as session 7's shot (no change from the
rebake; a lower profile like DD-03's is a polish option). Tests from assets_dev 4 of 4 (playtest 204, playtest_b 15,
playtest_hostility 31, playtest_exit 16 steps; `output/studio_cal/dd02/run/four_232829`).

**Session 9, polish (lane lead):** the marble rooms baked bright; profile lowered as DD-03's (`direct_scale` 2.0 -> 1.6,
`max_lighting` 1.5 -> 1.25; before: `output/studio_cal/dd02/xeen_dd02_profile_before_s9.yml`), rebaked 00:54, `stale_bakes`
none; tests from assets_dev 4 of 4 (`output/studio_cal/dd02/run/four_005521`). Pictures `output/studio_cal/dd02/shots/s9/`
(45, sheet `shots/s9_check.jpg` against the older bake): a little less washed; the pale marble itself sets the look.

## Merge point 30 (2026-11-21, lane A7 twenty-third session)

- `panel:mouth4` (the mouth over the last door) stood over 128 of the doorway's 224 (merge point 30's panel warning):
  the carving hung 32 into the door's top. The last door (`open:pass_study`) is now 320 high instead of 352 (its top at
  2240, where the carving starts), and the carving is centred over the door (offset 96, 128 wide, 2240 to 2336) instead
  of over the wall's middle. The door's `t1d3` (160 by 320 at scale 1.25) now shows one whole picture up the leaf
  instead of a sliver of a second. Edited in `output/studio_cal/dd02/tools/gen.py` (the panel and `op('pass_study')`).

## Session 23 (A8): review fixes (rows 77, 78)

- **The marble rooms were washed out** (review row 78: brick pattern dominating, floor near white). The bake profile
  `tools/lighting/baked_indoors/profiles/xeen_dd02.yml` is now `direct_scale` 0.9, `max_lighting` 0.9,
  `ambient_scale` 0.45 (was 1.6 / 1.25 / 0.9; before: `output/studio_cal/a8_s23/xeen_dd02_profile_before_s23.yml`).
  Tried by recomposing the saved passes first (`a8_s23/dd02_rc/`: A 1.1 / 1.0 / 0.6 still pale, B chosen). Mean
  luminance of the eleven review poses 158 -> about 113 (entry), 93-110 -> 63-80 (library); no texel clipped white.
  The textures (6d19's t1wl0lg, t1f1, t1wl9ctl, t1wl4cts) are unchanged: the light, not the marble, was the fault.
- **D-48 / row 77:** `sound:tower_bed` (`xeen_amb_tower`) is `pan: false` (gen.py).
- Before/after at the same poses: `output/studio_cal/a8_s23/shots/dd02_before_sheet_*.jpg`, `dd02_after_sheet_*.jpg`.

## Session 26 (A8): F13 status lines, the stale bake

- `evt:book_fire` and `evt:book_elec` (+5 Fire / Air resistance once per character) showed their gain in a window
  (`message:`); `tools/gen.py` `book()` now gives it as the studio's `text:` effect, a status line
  (`evt.StatusText(text, 4)`). Before: `output/studio_cal/a8_s26/before/dd02/`. Only the map Lua and studio file changed.
- `playtest.yml`: the two books' gain is checked on the status line (was a window assert).
- The .blv and scene had been reinstalled 23:59 for the new actor heights (only `height:` lines) without a bake; rebaked
  00:28 (`output/studio_cal/a8_s26/sub1/bake.sh dd02`), `stale_bakes` none for the map.
- Installed 00:27; audit 0 errors / 0 warnings, check_exits 0, check_drops 0; tests from assets_dev 4 of 4 (16 of 16,
  `output/studio_cal/a8_s26/run/dd02/t003440`).

## Session 29 (A8): D-89 identity (F12)

Review 2.2 ("6d19 rose marble done well, but a mansion: a straight corridor for the walk round the outer wall") and
2.3 "Towers are towers". `identity: {shape: tower, family: 6d19}` in project.yml. All in `tools/gen.py`'s "D-89
identity" block (before: `output/studio_cal/a8_s29/before/dd02/`; the generator reproduced the installed L4 first).

- **Set piece: the octagonal outer wall of floors 3-4** (`OCT`: x -1664..5632, y -384..4352, corners cut 1280). Every
  room on it shows windows to the sky (flush `sky: true` faces, 128 x 224, framed in t1trima; new `atmosphere.yml`
  `open_sky` preset `xeen_darkside_day`, D1's sky before M17 is done):
  - floor 3: **the trapped walk follows the octagon** (south side y -384..-64, the south-east diagonal, the east side
    x 5312..5632, then the stub west into the loft as before): two 135-degree bends, seven windows (three south, one
    on the diagonal, three east, the last at the stub's far end); the last stair's foot reaches down to the walk's
    west end (y -384..832) with a window in its south wall. Plates, bolts (from the outer wall), lights and the four
    beholder bats moved with it; event ids unchanged.
  - floor 4: **the study's north-west corner is cut by the octagon** (windows in its west and north-west walls, above
    the column band); its south and east walls are **bookcase walls** floor to ceiling (bookcas2/bookcas1, two rows),
    the west shelf platform gone. **The boot closet moved into the octagon's north-west corner** (x -896..256,
    y 3840..4352, a diagonal wall): windows north and north-west; rack, chest (now x -96) and sconce moved.
- **The bat roost's broken window is open to the sky:** a jagged hole of five sky panels (`panel:window` keeps its id
  and text).
- **The library's south wall** is a bookcase wall, one case floor to ceiling.
- MP42: `chest:crates` faced its front into the west wall: now `facing: s`.
- No new texture (the sky faces carry t1c3): textures 31/45, 0/8 new. Rose marble kept everywhere.
- `playtest.yml`: the walk's waypoints follow the octagon; the boot closet's at its new place (no hook changed).
- Audit 0 errors / 0 warnings (the first try with bookcase *panels* gave 5 `family_switch`; whole bookcase walls with
  `bands: false` clear them). check_exits 0, check_drops 0, `stale_bakes` none. Installed and baked 02:32; tests from
  assets_dev 4 of 4 (16 of 16, `output/studio_cal/a8_s26/run/dd02/c023202`).
- Pictures: `output/studio_cal/a8_s29/shots/dd02_before.jpg` / `dd02_after2.jpg` (tours `a8_s29/dd02_tour_before.yml`,
  `dd02_tour_after.yml`: the same shots, the walk's and closet's moved to their new rooms).
- Left: the stairs are still straight switchbacks (2.2's "straight stairs"); the floors 0-2 rooms are not on the
  octagon (the review asks only floors 3-4).
