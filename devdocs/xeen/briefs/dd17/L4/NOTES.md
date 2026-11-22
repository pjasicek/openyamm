# DD-17 Castle Alamar, L4: notes

New L dungeon on D6's mesa (dark maze0049-0051: Castle Alamar Levels 1-3), story M33 and Q-D26's roof hatch, built
with the Map Studio from `devdocs/xeen/mockups/act5_graphs/dd17.graph.yml` and decider D-61
(`mockups/act5_a8_decisions.md`, which wins) by `agent:xeen-a8-dd17` (lane A8 session 12, sub-agent), 2026-11-21. Key
`dd17`, project `xeen_dd17`, stem `xeen_dd17.blv`, map_stats 9170, world `xeen`, music 50.

## State and next steps

**Built, not installed.** L1-L4 written by the generator; L4 recorded (`agent:xeen-a8-dd17`); `oymap fmt --check`
clean; validate: no issues; build 0 warnings (no "two sizes for one texture"); audit of the installed scratch map
(`output/studio_cal/dd17/audit.txt`, `--reach --solve`): **0 errors**, 9 warnings (8 `tile_seams` on the belt beds and
1 `question.answer`, both kept below), infos only.

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd17`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd17` (bake, stale check,
`four.sh` from assets_dev), or `ASSETS=$PWD/assets_dev output/studio_cal/dd17/four.sh` alone.

**Resume:** `output/studio_cal/dd17/cycle.sh L4 "<label>"` (generate, fmt, validate, build, install into the scratch
root, audit, record), then `python3 output/studio_cal/dd17/tools/tests.py` (rewrites the six playtests from the
geometry and `ids.lock.yml`), then `output/studio_cal/dd17/four.sh` (`N=`, `TESTS=`, `ASSETS=`). Diff the L4 against
`.oymap/last` first if anyone edited it by hand.

**Scratch** `output/studio_cal/dd17/`: `tools/gen.py` (plan, project, diagram, the 1.3 enlargement `scale_doc`),
`tools/geo.py` (rooms, openings, the dial hall's rings, furniture), `tools/dress.py` (objects, wiring, the cinematic),
`tools/tests.py` (playtests), `tools/tour.py` (pictures), `cycle.sh`, `four.sh`, `root/` (scratch root: `cp -al
assets_dev` with a real `worlds/xeen/data_tables/` copy, refreshed 05:10 for A3's hooks), `run/` (logs), `exp/` (the A1
evidence runs), `shots/`. **Every project file of L1-L4 except this file is written by the generator and tests.py.**

**Session 15 (A8, D-66, A3's segment 77):** the four Heads ask one Yes/No each with their own text, `The Head
speaks: "<Element> power field operational." Shut the field down?`; the gate's typed prompt is the source line whole,
"The time is right. What is Alamar's true name?" (aaze0050:19); no `SetMessage` before either (D-65 B1). The dais,
the hatch and the vault release ask with Yes/No buttons (`AskChoiceWithAnswerSteps`, as DD-15's sky door and DD-08's
roof): each such event's condition is `continueStep == 1` (Yes), its else branch asks (`dress.ask_yes_no`), so the
YAML keeps its doors, textures, cinematic and leave. The arrival line shows once per real entry: `evt:visit_load` arms
`evt:arrival` only when `in_visit` is clear (set on load, cleared by `evt:visit_end` on leave, DD-09's pattern), so a
load inside the castle greets nobody. `playtest_belt.yml` (D-66 item 7): forward held 1.2 s over the fire belt's
mouth plate rides to the far end facing 512, a tap lands there facing 512 and stays; it works since A1's merge point 28
(game 06:49:47: the fault was the scenario runner) and is in `four.sh`'s default set; the main playtest's two belt
rides now assert facing 512 too. Backups of
the generator before this: `tools/dress_before_s15.py`, `tools/tests_before_s15.py`; scratch root `root_s15/`
(fresh `cp -al` of assets_dev with a real tables copy). The solve no longer walks the Heads' Yes branches (the event
flow explores `AskQuestionWithAnswerSteps` steps but not `AskChoiceWithAnswerSteps`'s; A1 asked): all 51 sectors are
still reached and the audit has 0 errors.

## What was built

One BLV of three floors 640 apart in the castle's frame (x east, y north): drawn at the graph's sizes and written
enlarged 1.3 in x and y (heights, doors, plates, lifts and furniture keep their sizes) to reach the L band.

- **L1, the works (0):** the gatehall (arrival, the gate's exit), the pillared Hall of Order (four `swaled` machine
  columns, the first statue), the west and east wards, the barracks, the moat watch and the parts store (a storeroom:
  barrels and kegs), the four conveyor belts north to the four Lava Heads (each belt a long hall and its end, `swr2dk`
  roller bed under green tubes), the two maintenance galleries behind the Heads, the stair hall (0 to 640; the stair
  up the north wall to a head along the east wall) and the sump (bones, the find, the door's lever).
- **The dial hall (0 to 1216):** four ring chasms (water outermost, then air, fire, earth) in U shapes round the gate
  island on the hall's east wall; the ring walls, the island and the outer lip are 640 high; the chasm floor is the
  glowing lattice (`swflora`), each chasm lit in its element's colour; one bridge slab per chasm on the west line
  (a lift lying on the chasm floor, level with the rims while its dial reads nine); a radial cut through the ring
  walls' south arms lets a fallen party walk out to the sump.
- **L2, the dial floor (640):** the outer walk (south walk in two parts, four corner bays, west, north and east walks),
  the four sundial alcoves behind their `xafield` leaves (dial on a girder plinth, `xasundial` once on its top, an
  `xaenergy` panel behind), the watchers' post, the lift core behind the true-name gate.
- **L3, the deck (1280):** the trapdoor deck over the dial hall (six `xatrapplt` trapdoors), the lift head, the robot
  bay (the vault release), the screen room (consoles of `trekscrn`), the Hall of Vengeance (the third statue, "Come
  to ME!"), the Power Juice, the hatch room (`xahull` shaft, the ladder, the roof hatch), the antechamber, the
  strongroom (the hoard), Command Central in three parts (main floor, the throne apse with the dais, the machine bay).

## Measurements

`oymap metrics` (`output/studio_cal/dd17/metrics.json`): **51 sectors** (L 50-75), **130.7 M units² of floor** (114.6
walkable; L 120-200), 8 loops, one component, every sector reached with doors clear. **24 doors** (three blast-door
pairs `swdoora` parting in the middle, the true-name gate's hinged pair of `xaglyph`, nine single `swdoorb` doors, the
sump's and the strongroom's doors, four `swtrpnl` maintenance doors, four `xafield` leaves) plus 11 lifts (the lift,
four slabs, six trapdoors) and 4 switches (42 door records). **7 chests** (six T5, the T6 hoard), 2 finds (the sump,
the juice). Textures (`tools/xeen/texture_budget.py --root output/studio_cal/dd17/root --map DD-17`): **39 of 70, 5
new** (`xalavahd`, `xalavahdx`, `xasundial`, `xaglyph`, `xatrapplt`).

| Who | Row | Level | Where | Count |
|---|---|---|---|---|
| Patrol | 11610 | 50 | Hall of Order 3, wards 2+2, barracks 2, watch 2, returns 2+2, south walk 1+1, bays 2x4, west walk 1, east walk 2, deck 2 | 30 |
| Annihilator | 11611 | 62 | Hall of Order 1, wards 1+1, barracks 1, store 2, stair hall 2, west walk 2, north walk 2, east walk 1, post 1, deck 2, robot bay 2, Hall of Vengeance 2 | 20 |
| Autobot | 11612 | 75 | stair hall's head 1, the island 2, deck 1, robot bay 1, Hall of Vengeance 1 | 6 |
| Lesser Fire / Air / Water / Earth Elemental | 11620 / 11624 / 11625 / 11626 | 55 | two at each Head | 8 |
| Gamma Gazer | 11572 | 65 | watch 1, north walk 1, post 2, screen room 2 | 6 |
| Sheltem | 11924 | - | the throne apse, hidden, peaceful, immobile, unkillable (group 40) | 1 (not counted) |
| Corak | 11912 | - | on the dais, hidden, peaceful, immobile, unkillable (group 41) | 1 (not counted) |

By floor: L1 33, L2 24, L3 13 (the graph's). **Kill XP:** 275,380 for the party, **68.85k per member** (MAPS 67.9k,
+1.4 %, D-61). Groups: 1 robots, 2 gazers, 3-6 the elementals, 40 Sheltem, 41 Corak.

## Mechanisms

- **Arrival** (`evt:visit_load` + `evt:arrival`, a timer once per real entry until m33.done; a load inside the
  visit does not re-arm it, `in_visit` / `evt:visit_end`): at the gate `m33.arrival`
  (the Soul Box: its window, inside 111660; without it the hook's refusal line, voiced the first time, and the move to
  D6's `entrance:dd17_gate` (-6656, 4608, 2208) facing 1536); at the roof (the party above 1000) `m33.roof_arrival`
  and a refused party back to D7's `entrance:dd17_roof` (-18688, 8448, 1536) facing 1024. arrived_once 117600.
- **Belts (D-61 Q11):** each belt's mouth plate and a back plate near its far end run the `teleport` preset to the
  belt's end (direction 90, north), with "The floor lurches and carries you along." and a rumble stand-in. The Head
  room's floor sets a map variable on entry; the maintenance door is bolted ("A maintenance door. It is bolted on the
  other side.") until then, then works both ways.
- **Heads and fields (Q12, D-66):** the Head panel (`xalavahd`) asks one Yes/No, "The Head speaks: \"<Element> power
  field operational.\" Shut the field down?" (aaze0049:7-10 with the question); No leaves it; Yes calls A3's `m33.head_<element>`
  (117601-117604, "The Head goes dark. Somewhere above, a field dies."), drops the field (one-way), darkens the Head
  (`xalavahdx`), its glow light and its hum and the field's crackle stop (AmbientSound map variables). A load event
  keeps all of it after a reload. Afterwards the hook's "The <Element> Head is dark and cold."
- **Sundials and slabs (Q13):** each dial calls A3's `Xeen.alamarSundial(key, eventId, continueStep)` (the question,
  the turn, the at-nine and off-nine lines, the dial bits 117611-117614 and 111663); when it returns true the event
  sets the slab from the dial's bit (`evt.SetDoorState` of the slab, its number from ids.lock.yml) with the grind. The
  load event (`evt:dials_load`) calls `Xeen.alamarSundialsSync()` and then sets every slab from its bit.
- **The gate:** `door:gate`'s click: while the gate is shut and `Xeen.alamarSundialsSync()` says all four read nine, the
  typed question "The time is right. What is Alamar's true name?" (aaze0050:19 whole, D-66; no message before it); "Sheltem" calls
  `m33.true_name_gate` (gate_open 111661, autonote 4134) and opens both leaves; anything else `m33.true_name_wrong`.
  Before nine the hook's "The time is not right. Access denied!"; open, "The gate stands open." A load event keeps it open.
- **The lift:** the button at either end toggles it once gate_open is set; before: "Access to the upper floor is
  denied!" (aaze0050:0).
- **Trapdoors (Q18):** six `lifts[].trap` plates (`xatrapplt`, 192 square, in holes in the deck over the chasms): a step
  drops the plate and the party 1,280 to the chasm floor ("The hatched plate drops away under you!"); the first, by the
  lift head, is titled "A plate seamed like a hatch.". The way back: the radial cut, the sump, its lever and door, the
  stair hall.
- **Command Central (Q15-Q17):** the dais plate (in front of the apse) asks "Before the throne. Open the Soul Box?"
  (Yes/No, D-66) while `m33.sheltem` can run; Yes calls it (the box for the Cube of Power, done 111662, the voiced lines), then
  `cinematic:self_destruct` (16 s: the cue `evt:show_figures` shows Sheltem's and Corak's groups, the castle's groan and
  shakes, three subtitles), whose done event leaves to D6's `entrance:dd17_gate` at once. Without the gate or the box,
  the hook's line. `evt:figures_load` makes both figures unhurtable on every load.
- **Others:** the robot bay's vault release (Yes/No "Vault release. Pull?", one-way, 117605, the strongroom's door; kept on load); the
  Power Juice calls A3's `m33.power_juice` (+2 Might once per member, player bit 11369); "Come to ME!" once (117606);
  the three propaganda statues speak on approach (once until a refill) and when clicked (aaze0049:2-4), the crackling
  statue on the island (aaze0049:5); the sump's bones (+1500 gold and a T5 ring, once).
- **Throne and statues (D-66 item 8, A8 session 17):** Sheltem's throne is S's `xeen_throne_steel` (Ancient steel,
  dark teal cushion) at (-3840, -4000) on the dais top (1312) facing east, its click on the decoration (`deco:throne`,
  event 85, "The throne is empty..."); the girder seat and back blocks are gone. Sheltem (hidden until the cinematic)
  now stands before it on the dais at (-3616, -4000) (a body of radius 76 inside the throne's 70 otherwise), and the
  cinematic's first subtitle says "Before the throne, Sheltem is there...". The three propaganda statues and the
  true-name statue are S's `xeen_statue_teal` (teal metal on its own steel plinth) for MM6's `sta1a`, the girder
  plinths dropped: statue1 (-1584, -3536) and statue2 (464, 3376) where they stood, facing south over their plates;
  statue3 moved from (-2496, 1328), which stood on the walking line through the hatch room's door, to (-2992, 1408) by
  the north wall west of that door, its plate with it; the true-name statue on the island (992, -256) facing west.
  The clicks stay on the decorations (events 77/79/81/92).
- **The hatch (Q14, D7 installed 04:53):** the roof hatch's click calls `q-d26.alamar_hatch` ("Bolted from above." until
  roof_unlocked 113521), then "Climb up through the hatch?" (Yes/No) and the leave to D7's `entrance:dd17_roof`.

## Playtests

**Session 15, from assets_dev:** seven tests 4 of 4: `playtest` 280 steps, `playtest_dials` 43, `playtest_hatch` 30,
`playtest_refused` 22, `playtest_exit` 16, `playtest_hostility` 39 (`run/four_064538`), `playtest_belt` 23 and the main
again with the belt facings on the merge point 28 game (`run/four_065226`). A3's segment 77 passes normal and
`--reload` with no greeting after a load.

Before (session 12):

`output/studio_cal/dd17/four.sh` from the scratch root, `--world xeen --map xeen_dd17.blv`: **all six 4 of 4** on the
final build (`run/four_052721`, summary `four_final2.txt`): `playtest` 270 steps, `playtest_dials` 43,
`playtest_hatch` 30, `playtest_refused` 22, `playtest_exit` 16, `playtest_hostility` 39. Each starts on D6 and moves in
with `evt.MoveToMap` (with the Soul Box granted, except the refusal test).

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | From |
|---|---|---|
| `entrance:d6_gate` (= start) | (0, -4736, 0), north (512) | D6's door:dd17 (A6) |
| `entrance:d7_roof` | (-2832, 2336, 1280), east (0), the ladder's foot | D7's door:dd17 (A6, q-d26.hatch) |

| Way out | To | Measured |
|---|---|---|
| The gate's exit preset (`exit:gate`, OK) | D6 `entrance:dd17_gate` (-6656, 4608, 2208) facing 1536 | position and facing asserted (playtest_exit) |
| m33.arrival refused | D6 `entrance:dd17_gate` | asserted (playtest_refused) |
| The cinematic's done event | D6 `entrance:dd17_gate` | asserted (playtest) |
| The hatch | D7 `entrance:dd17_roof` (-18688, 8448, 1536) facing 1024 | asserted (playtest_hatch) |
| m33.roof_arrival refused | D7 `entrance:dd17_roof` | asserted (playtest_refused) |

## Ids

- Map qbits: 117600 arrived_once, 117601-117604 the Heads off (fire, air, water, earth; A3's hooks set them), 117605
  vault open, 117606 "Come to ME!"; read: 117611-117614 (A3's dial bits), 111660-111664 (M33), 113521 (Q-D26).
- Player bits: 11369 (A3's m33.power_juice). Map variables: `visit`, `sump_open`, `sump_find`, `bolt_<element>`,
  `statue1..3_heard`; A3's named `dd17_sundial_<element>`.
- Slot (= A2's row 9170, D-61 Q21): `{monster: Xeen Robot, tier: 2, per_marker: [1, 2], weight: 100}`, encounter 10.

## A1 confirmations (D-61 RELAYS), evidence in `output/studio_cal/dd17/exp/` and `run/`

1. **In-map move from a step plate keeps the facing given: FAILS.** The ride happens on a short press
   (`exp/belt_seg.log`, `exp/belt_back_seg.log`: the party lands at the belt's end) but faces **0 (east)**, not the
   compiled `evt.MoveToMap(..., 512, ...)`, and drifts on; with the key **held** across the plate the line shows and the
   party walks on with no ride (`exp/belt_press.log`: 3 s forward, at (-2496, -1520)). The playtest steps onto the plates
   with short presses and asserts positions only.
2. **A horizontal slab as a two-state door: works** (lifts with `thickness`, raised and lowered by the dial events and
   the load event; playtest and playtest_dials, the party crosses all four).
3. **A `trap` lift through 1,280 of open air: works** (playtest: the plate and the party fall to the chasm floor).
4. **Hidden actors shown by a cinematic and a leave after `evt.PlayCinematic`: works** (playtest: Sheltem and Corak
   `hidden: false` 4 s into the cinematic, then D6 at entrance:dd17_gate).

## Texture fit exceptions

- `tile_seams` `swr2dk` (the four belt beds, 8 faces): the roller bed's repeat line across the belt is the rollers.

## Audit warnings kept

- `question.answer` (the gate's "Sheltem"): the answer is given outside the map (Olympus's plaque, m31.true_name_plaque;
  the Pharaoh's M28 line), as the riddle's design says.
- `ride.no_switch` (4, doors 2-5, the bridge slabs `lift:slab_air|earth|fire|water`; since oymap 09:31): each slab is
  a two-state bridge set from afar by its element's sundial on L2 (and by the load event), not a ride. A party on the
  chasm floor (a trapdoor's fall) that stands on a lowered slab is not meant to ride it up: it walks out to the sump
  through the radial cut. A switch at the slab would bypass the dial puzzle (D-61 Q13). Kept (A8 session 22, audit
  under oymap 12:43: 0 errors, 13 warnings).

## Dressing exceptions

None (audit 0 dressing findings).

## Lines for A3 (map-local)

The Heads' joined prompts `The Head speaks: "<Element> power field operational." Shut the field down?`
(aaze0049:7-10 with A3's question, D-66); the statues (aaze0049:2-5); "Come to ME!" (aaze0051:2); "The
floor lurches and carries you along."; "A maintenance door. It is bolted on the other side."; "A crackling <element>
field bars the alcove."; "The hatched plate drops away under you!"; "A heavy door. It is worked from the other side.";
"The lever drops. The door to the stair hall grinds up."; "Vault release. Pull?"; "Far off, a heavy door grinds up.";
"The strongroom's door is sealed. Its release is somewhere else."; "The time is right. What is Alamar's true name?" (aaze0050:19 whole, D-66);
"The gate stands open."; the lift's two lines; the throne, the screens, the bones; the cinematic's three subtitles.

## Sounds for AU (engine stand-ins placed now)

Belt rumble (`xeen_phase_shift` on each ride; bed `xeen_machine_stamp_loop`), the four Head hums (`humming`, stopped by
the Head), the field crackle (`xeen_barrier_loop`, stopped with the field), the dial clank and slab grind (`6stone
door0101`), the gate's chimes (`xeen_power_up` on approval), the trapdoor clang (none yet), the klaxon (none yet) and the
groan (`xeen_castle_groan`, XD-19's). Beds `pan: false`.

## Waiting on

- Nothing for Sheltem: his look (row 11924's body, `xsor_h`) is seen in game (session 19): a tour with a proper entry
  (started on D6, the Soul Box given, `evt.MoveToMap` to the gate arrival, the world frozen for the pictures;
  `output/studio_cal/a8_s19/dd17_tour.py`, `dd17_shoot.sh`) shows him robed and staffed before the throne and Corak beside
  him once their groups' Invisible bit is cleared as the cinematic cue does (`output/studio_cal/a8_s19/dd17/entry19b_4.jpg`,
  `_5.jpg`). The session-17 screenshot tour (started inside the map) had shown neither.
- No texture stand-ins (the five new textures installed 05:05).

## DECIDE

1. **The island is a platform in the dial hall** (the graph's room:island merged), the chasms U-shaped round it on the
   hall's east wall, so the lift core lies beyond the gate in that wall. Cheaper than a room inside a ring.
2. **The trapdoors and falls land on the chasm floor**, which runs out to the sump through a radial cut (the graph's
   sump at 640 under the chasm). Same costs: hit points and a climb.
3. **Enlarged 1.3** to the L band (sectors 51, 131 M units²); the belts and Command Central split into rooms as the
   graph's sector count says.
4. **The hatch is live** (D7 installed; the lane lead's change of brief).

## Pictures (looked at)

`output/studio_cal/dd17/shots/look1_1..4.jpg` (32 shots, `tools/tour.py look1`, `shoot.sh look1`; doors, slabs and the
gate opened by the tour's commands; unbaked, the HUD stayed on): the gatehall's blast door, the Hall of Order's machine
columns and statue, the wards, the fire belt's tube walls over the roller bed, the Fire and Water Heads (`xalavahd`
between two `xaenergy` panels, the elementals), the returns, the sump's braced walls and lattice mouth, the stair hall,
the south walk, a bay's field (`xafield` over the alcove), the water dial's alcove, the dial hall from the lip (the
rings, the raised slabs) and over the chasms, the island's gate (the `xaglyph` leaves open) and statue, the lift core,
the deck with its hatched trapdoors, the robot bay, the screen room's consoles, the Hall of Vengeance, the hatch room's
ladder and roof hatch, the juice dispenser, the antechamber, the strongroom's hoard, Command Central and the throne
apse, the moat watch, the north walk's statue. Session 17's baked tour `dd17/shots/statues17/` shows S's steel throne
and the four teal statues. Plain still: the dial plinths are grey blocks (the dial face shows only
from above). No bake in the root (the lane lead bakes after install).

## Session 21 (A8): AU's sounds

The six trapdoors (`evt:trap_t1`-`t6`) play AU's `xeen_trapdoor` with the drop; `cinematic:self_destruct` sounds `xeen_klaxon` at 5 s and 11.5 s (the groan at 9.5 s stays); the four Lava Heads' `sound:hum_*` are their element's plane bed as point sounds (`xeen_amb_plane_air|earth|fire|water`, volume 0.35, earth 0.7), still stopped by the Head. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8, 2026-11-22)

- D-89 (A3 34th's request): `evt:arrival` no longer moves a party without the Soul Box back out (D6's gate and D7's
  hatch check the box before the move). Inside, `m33.arrival` / `m33.roof_arrival` run only when they would pass
  (`XeenQuests.can`), so a boxless party (before D6's check lands) sees nothing. `tools/dress.py` `arrival_lua`;
  `tools/tests.py` playtest_refused now asserts no line, no window, no move.
- F16: the roof hatch (event 47) is `q-d26.alamar_hatch` then the `exit:` effect's standard entrance window (OK/Close);
  no "Climb up through the hatch?". playtest_hatch: bolted, Close stays, OK to D7.
- D-91: the three sliding blast-door pairs (gate_hall, hall_stair, ante_command; 448 openings) showed one swdoora split
  over both leaves (half a picture each, D6's fault); each 224 leaf now shows the whole swdoora, the right one mirrored
  (stretched 224 x 448). The true-name gate's hinged pair (xaglyph, left/mirrored) was already right.
- Audit: the trap plate t6's `textures.feature_cut` error (its top half a picture off the grid) fixed with
  `offset: [96, 0]` on that plate only; `entrance.question` gone. Audit 0 errors / 13 warnings (as before: tile seams,
  the true-name answer, rides).
- F13: the power juice's lines are status lines (A3's hook): the main playtest checks `status()`.
- Installed 00:26, baked, tests 28/28 from assets_dev (all seven playtests 4 times).

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator (gen.py L4 + tests.py) reproduced the L4
unchanged; the build changed only the seven chests: the style world's 7gt002 chest in place of MM6's ch1, same
places, none moved. Installed, baked; audit 0 errors / 14 warnings: the 13 of before plus MP42's new support.edge on
the true-name statue (decoration 16, on the gate island 4 units in from its south edge over the 640 chasm; left
for the lead: dress.py DECOS true_name_statue [768, -192] -> [768, -144] clears it). check_exits 0, check_drops 0; tests 4 of 4 (28 of 28,
output/studio_cal/a8_s26/run/dd17/c022040). Chest pictures: output/studio_cal/a8_s29/shots/dd17_chests.jpg and
dd17_barracks.jpg (the barracks chest from another side; a robot stood in the first view).

- 2026-11-22 fixup (fourth orchestrator, for A8): the true-name statue (`dress.py` DECOS) moved from [768, -192] to
  [768, -144] (L4 (992, -256) -> (992, -192)), off the gate island's edge: the audit's `support.edge` is gone (warnings
  14 -> 13, errors 0). Installed 03:02, baked 03:03; check_exits 0, check_drops 0, MAW reserve and check 0; tests 28/28
  from assets_dev (`output/xeen_fixups/dd17/c030228`). Backup of the generator `output/xeen_fixups/dd17/dress.py.before`.
