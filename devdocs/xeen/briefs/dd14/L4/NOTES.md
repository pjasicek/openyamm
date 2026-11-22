# DD-14 Castle Blackfang, L4: notes

New M (large) dungeon on D4's crag (dark maze0045-0048: the castle's three levels and its dungeon), story M27, built
with the Map Studio from `devdocs/xeen/mockups/act4_graphs/dd14.graph.yml` and decider D-42
(`mockups/act4_a8_decisions.md`, which wins) by `agent:xeen-a8-dd14` (lane A8 session 9), 2026-11-21. Key `dd14`,
project `xeen_dd14`, stem `xeen_dd14.blv`, map_stats 9167, world `xeen`, music 3. Entered only by Ambrose's griffin
(D-36).

## State and next steps

**Session 9, D-52 follow-ups (sub-agent, 2026-11-21 04:00-04:45): ready to reinstall.** Every change went through the
generator (`tools/gen.py`, `tools/dress.py`); the L4 matched `.oymap/last` before (no hand edits). Recorded
(`agent:xeen-a8-dd14`). Validate: no issues; build 0 warnings (no "two sizes for one texture"). Audit of the installed
map (`output/studio_cal/dd14/audit.txt`) and of the project (`oymap audit devdocs/xeen/briefs/dd14/L4 --assets
output/studio_cal/dd14/root_s9 --reach --solve`, `audit_project_s9.txt`): **0 errors**, 1 warning (`ride.no_switch`,
kept, below), infos only.

**Scratch root:** a fresh `output/studio_cal/dd14/root_s9` (`cp -al assets_dev` at 04:00, `worlds/xeen/data_tables/` a
real copy, identical to assets_dev's at the time; the old `root` was stale in 378 places: actors.yml, the quests Lua,
D4/D1/D6 maps). `cycle.sh`, `four.sh` and `shoot.sh` default to it.

**Playtests from the root, 4 of 4 each:** `playtest` (309 checks) and `playtest_hostility` (55) in
`output/studio_cal/dd14/run/four_041439` (summary `four_s9b.txt`); `playtest_octopods` (127) in
`output/studio_cal/dd14/run/four_041635` (summary `four_s9c.txt`; its earlier version in four_041439 failed 2 of 4 on
a test fault, fixed in the test: fists and two presses missed too often against armour 36).

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd14`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd14`, then
`ASSETS=$PWD/assets_dev output/studio_cal/dd14/four.sh` (playtest, playtest_hostility, playtest_octopods).

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd14/cycle.sh` (regenerates L4 from `tools/gen.py`, fmt,
validate, build, install into the root, audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against
`.oymap/last` first if anyone edited it by hand.

**Scratch** `output/studio_cal/dd14/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes, furniture), `tools/dress.py` (objects, wiring, atmosphere), `tools/tour.py rooms|things|fix <name>` +
`tools/sheet.py` (tours, JPEG sheets), `tools/texsheet.py`, `texsize.sh` (texture sizes), `cycle.sh`, `four.sh`
(`ASSETS=`, `N=`, `TESTS=`), `shoot.sh <tour>`, `run/` (logs), `shots/` (sheets). **Every project file of L1-L4 except
the playtests and these notes is written by the generator.** `pic_L4tmp/`, `pic_build/`: a throwaway copy built once
with Ambrose and the griffin unhidden for the pictures (the tours' console cannot show a hidden group); the root was
reinstalled from the generator after.

### Session 9 changes (D-52)

1. Rest slot: `{monster: Xeen Vampire, tier: 5, per_marker: [2, 3], weight: 100}` only (= A2's row 9167; the Gnome
   Vampire 32 in ~10 % of rests accepted, D-52 (1)).
2. The five cistern octopods are A2's indoor row **11473** (`Xeen Octopod D`, `stand`, no swimmer AI), each just inside
   the pool's edge: west bank (1776, 1152) and (1776, 2560), south bank (2176, 752), north bank (2176, 2960), the far
   (east) ledge (2576, 1600). From the bank or ledge by each, the party's blow lands and the octopod hits back.
3. **Ambrose** (row 11917, `npc: 5512`, actor 0) stands beside his griffin by the perch (96, -1840, facing north), in the
   griffin's group 30: hidden until m25.done, shown on every load after, never hidden on DD-14 (D-52). **Queen
   Kalindra** (row 11918, `npc: 5001`, actor 49, group 31) stands by her bench (-880, -192), her back to the bars;
   hidden on load once done 111542 (`evt:queen_load`). `evt:figures_load` (load): `evt.SetMm9ActorCanReceiveDamage
   (ActorIndex("monster:ambrose"|"monster:queen"), false)`. Both peaceful, immobile, not counted.
4. The perch (`evt:ambrose`, now titled "Griffin's perch") asks "Are you ready to leave this awful place, friends?" from
   m25.done and on Yes only calls `XeenQuests.hook("m27.fly_out")` (A3's hook holds the move to D4 (6144, 5120, 1216)
   facing 1024, direct); before m25.done "A griffin's perch, empty." Ambrose's own topic "Fly us out" (A3's, from
   m25.done) does the same.
5. `m27.queen_cell` moved off the bench to the cell's entry: `evt:queen_cell`, a step event on the cell's floor (while
   queen_seen 111544 is unset; the hook is once and not after done). The bench (`evt:queen`) now says "A stone bench."
   and after done "The cell is empty. The Queen has gone home."
6. `pan: false` on the beds `sound:roost` and `sound:yard_wind` (AUDIO.md "Indoor beds"); the point sounds still pan.
7. The perch's `SpeakNPC(5512)` and the bench's `SpeakNPC(5001)` workarounds are gone; both figures talk themselves.

## What was built

Four floors 640 apart in one frame (x east, y north, z up): the dungeon -640, the ground floor 0, the upper floor
640, the walls 1280. The inside is larger than the outside (D-42's general rule from DD-05 (6)): the courtyard is
2,560 x 2,048, the castle's plan about 5,400 x 7,200 with the back stair and the question room outside the four
ranges.

- **L1, the walls (1280), open to the sky** (`atmosphere.yml` `open_sky: {mode: open, preset: xeen_darkside_fading}`;
  the walks' and courtyard's ceilings are sky faces at 1792): the griffin's landing on the south walk (arrivals,
  coffins in a row against the outer parapet, the bones' notes, Ambrose's perch and griffin, the yard gate), the
  west, north and east walks (the gargoyles; the east walk's four fire plates), the north-west tower (the gong), the
  north-east tower (two coffins), the keep's top chamber (the bat roost: strongbox, roof trapdoor). Inner parapets:
  openings 224 above the walk over the courtyard; the walls between walk and courtyard are 32 thick.
- **The two stair towers** (south-west, south-east): one room each from 640 to 1792, a hanging head floor at 1280
  along two walls (the tower's top storey) and twenty steps up the south wall; their feet are the L2 ends of the ring
  (the graph's sw_stair2/se_stair2).
- **L2 (640):** the long gallery (portraits), the black chapel (double doors, altar, candelabra), the library
  (bookcases, the Lineage on a lectern), the keep's upper hall (two chandeliers, the gong's panel north into the
  Count's study: desk, ledger, strongbox), the Countess's rooms (bed, dressing table, the jewel box), the sleeping
  hall (six coffins, three sleepers).
- **The grand stair hall** (0 to 1152): the keep door from the courtyard, twenty steps up to a head gallery at 640
  that opens onto the keep's upper hall and the library; the Count's hall's double doors under it.
  **The servants' back stair** (0 to 1152) behind the kitchen and the Countess's rooms.
- **L3 (0):** the courtyard (open sky; the dry fountain, three gargoyles on plinths; the courtyard stair, forty steps
  up its south wall to a head at 1280 and the yard gate), the kitchen, the cask cellar (a store; the trapdoor), the
  great hall (long table, xbfcrest on the end wall, two chandeliers, the screens passage), the Count's hall (dais,
  black throne under xbfcrest, candelabra, chandelier; the bar behind the dais and the crypt's door), the family
  crypt (four named stone coffins on biers, braziers).
- **The dungeon stair** (-640 to 0): its head behind the bar, twenty steps down north, the gaolers' post at its foot
  (the graph's dstair_foot); under the head the question room's door and the undercroft.
- **The dungeon (-640):** the question room (racks, strongbox), the cells (three barred cells, the Queen's at the far
  end), the ladder shaft under the cellar, the Queen's cell, the pillared undercroft (twelve pillars, four rows of
  three), the black cistern (a pool 96 deep with banks, five octopods, the chest on the far ledge).

## Measurements

`oymap metrics` (`output/studio_cal/dd14/metrics.json`): **31 sectors** (M 20-45; the graph's "large: 40-45" aim is
not met: the stair feet are the towers' and the dungeon stair's own lower floors), **74.1 M units² of floor** (62.9
walkable; M 30-90), 11 loops; **12 doors** (19 door records: four double doors as hinged oak pairs `chb1dl|chb1dr`, five
single doors, the bar, the yard gate, the study's panel, the trapdoor (a mover) and two switches), 5 chests, 62 bound
events, **70 placed monsters** + Ambrose's griffin, Ambrose and the Queen (not counted). Textures (`tools/xeen/texture_budget.py --root
output/studio_cal/dd14/root --map DD-14`): **42 of 45, 1 new** (`xbfcrest`).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Vampire | 11291 | 40 | 2,000 | towers 2+2+2, roost 2, gallery 3, chapel 2, library 2, keep hall 3, sleeping hall 2 + 3 sleepers, cellar 2, kitchen 2, stair hall 2, great hall 3, dungeon stair 2, cells 2, undercroft 3 | 39 |
| Vampire Lord | 11292 | 50 | 3,000 | chapel 2, keep hall 1, Countess 2, great hall 1, crypt 2 sleepers, undercroft 2 | 10 |
| Royal Vampire | 11295 | 58 | 3,944 | the Count's hall (his group) | 3 |
| Count Blackfang | 11294 | 70 | 5,600 | the Count's hall (group 5) | 1 |
| Gargoyle Sentinel | 11551 | 38 | 1,824 | west walk 3, north walk 2, east walk 2, courtyard 3 | 10 |
| Gargoyle Overlord | 11552 | 45 | 2,475 | north walk 1, east walk 1 | 2 |
| Octopod D | 11473 | 50 | 3,000 | the cistern's pool by its edge, stationary (A2's indoor row, no swimmer AI, D-52) | 5 |
| Tethered Griffin | 11913 | 30 | - | the landing's perch, peaceful, immobile, shown from m25.done | 1 (not counted) |
| Ambrose | 11917 | 35 | - | beside the griffin, npc 5512, peaceful, immobile, no damage, shown from m25.done | 1 (not counted) |
| Queen Kalindra | 11918 | 40 | - | her cell, npc 5001, peaceful, immobile, no damage, hidden once done | 1 (not counted) |

By floor: L1 17, L2 20, L3 19, the dungeon 14 (the graph's). **Kill XP:** 163,622 for the party, **40.9k per member**
(MAPS 39.2k, +4.4 %, D-42's figure).

## Mechanisms

- `evt:arrive` (timer, once): A3's `m27.landing` window ("Castle Blackfang's battlements ...") on the first arrival by
  either griffin way (`dd14_arrived_once` 117480, A3's).
- **Ambrose** (A2's row 11917, actor 0, `npc: 5512`), beside his griffin by the perch: clicked, he talks; his topic
  "Fly us out" (A3's, from m25.done, aaze0045:1) runs `m27.fly_out`, whose own move sets the party down on D4 at
  entrance:dd14_griffin (6144, 5120, 1216) facing west (1024), `{direct = true}`. **The perch** (`evt:ambrose`): from
  m25.done the question "Are you ready to leave this awful place, friends?" (Yes: `m27.fly_out` only; No: nothing);
  before it "A griffin's perch, empty." **The griffin** (A2's Tethered Griffin 11913, group 30, D6's figure) and Ambrose
  (same group) are hidden until m25.done (`evt:griffin_load`, every load). Neither Ambrose nor the Queen takes damage
  (`evt:figures_load`, D-51's word).
- **The Count** (actor 16, group 5 with his three Royal Vampires): `evt:count_dead` (timer) runs `m27.blackfang` at his
  death (blackfang_slain 111540, once: "every coffin lid in the castle slams shut at once ...") and plays the coffin lid
  sound; `evt:bar_lifts` (timer) opens `door:bar` once blackfang_slain is set (again after a refill: map var
  `bar_open`). **The bar** (`evt:bar`): `m27.dungeon_stair` before (its fail text, the source's aaze0047:0, D-42 (6)),
  then "The bar is lifted; the stair lies open."; **the step before it** (`plate:stair_force`, the throne room) runs the
  same hook until his death.
- **Sleepers** (D-18, D-42 (5)): five hidden actors, each its own group, standing on their coffins (groups 11-13 the
  sleeping hall's dorm_w1, dorm_w3, dorm_e2; 14, 15 the Dutchess and the Lady). The first opening shows the group, plays
  the lid, gives the coffin's find ("The lid flies back and a vampire rises from the coffin!"); then "The coffin is
  empty." (aaze0047:2). They still rise after the Count's death. Shown sleepers stay shown after a save and a load.
- **Coffins:** the landing's six "The coffin is empty."; the sleeping hall's three find coffins; the north-east tower's
  one find and one empty; the south-east tower's loot (+1500 gold and a level-4 ring, once); the crypt's four named on
  hover (aaze0047:6-9): the Countess's empty, the Count's "own coffin ... his strongbox stands at its foot" (the hoard,
  T5).
- **The gong** (north-west tower, `xngong` panel): "You hear a rumbling in the distance." (aaze0045:7), the first stroke
  slides open `door:study_panel` in the keep's upper hall (map var `study_open`); before it the panel "is set fast".
- **The yard gate** (the courtyard stair's head onto the landing; iron bars): from either side "The gate is barred on
  the courtyard side." until `switch:yard_bar` (on the stair's head) lifts it: "You lift the bar. ..." (map var
  `yard_gate_open`).
- **The trapdoor** (the cask cellar's floor over the ladder shaft): `switch:hatch_bolt` in the shaft draws the bolt
  ("You draw the bolt. The trapdoor at the ladder's top falls open.", map var `hatch_open`); from the cellar "A trapdoor
  in the floor, bolted from below." until then; `ladder:shaft` climbs 640 through it.
- **Fire plates** (east walk, four 384 x 256 plates in paler slabs, a clear line along the inner parapet): Fire Bolt
  (spell 2, expert, level 8) from the merlons' slits, "Fire leaps from a slit in the merlons!"; the landing's notes
  ("Floor traps are regularly spaced") answer them.
- **The Queen** (A2's row 11918, actor 49, `npc: 5001`) by the stone bench in her cell: entering the cell runs
  `m27.queen_cell` (`evt:queen_cell`, a step on the cell's floor; its text once, queen_seen 111544, not after done);
  clicked, she talks: A3's topic "The crown" (queen_found 111543 and autonote 4127; with the crown 12374: done 111542,
  the Pyramid key, `m27.ambrose_return` flies everyone to D1). Hidden on every load once done (`evt:queen_load`). The
  bench: "A stone bench."; after done "The cell is empty. The Queen has gone home."
- **The roof trapdoor** (the roost's ceiling, D-42 (7)): "A trapdoor in the roof, bolted from above. Wind howls over it."
- Finds once (map vars): the south-west tower's bones (diary aaze0045:4, +300), the jewel box (+800), the cask (+150);
  read: the landing's notes (aaze0045:5), Zarkon's diary and the rat-eaten one (aaze0047:4-5), the Lineage, the
  ledger, the portraits, the altar, the crests, the long table, the throne.

## Dressing

Coffins (six-sided outlines of weathered planks, stone ones on biers in the crypt), the long table with goblets and
plates, the chapel's altar and candle stands, the dais and throne, bookcases and a lectern, the desk, the bed and
dressing table, the kitchen's hearth and table, barrels in pairs (kitchen), casks and barrels in the cellar (`store:
true`), racks and a skull pile in the question room, bones in the cells and the shaft, chandeliers (keep's upper hall,
great hall, the Count's hall), sconces and torches on walls, braziers (`flamb00`) in the crypt's corners. Audit: 0
dressing findings. **Dressing exceptions:** none.

## Texture fit exceptions

None (audit: 0 texture findings). One info: `bemv` (the ladder) squashed, the ladder's own look.

## Audit warnings kept

- `ride.no_switch` (door 17, the cellar's trapdoor): it is opened only from below, by the bolt in the shaft (the
  graph's "bolted from below"); nobody rides it.

## Playtests

`output/studio_cal/dd14/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd14.blv`. Logs `output/studio_cal/dd14/run/four_*`, summary `four_s9.txt`.

| Test | Steps | What |
|---|---|---|
| `playtest.yml` | 309 checks | starts on D4; flown in to entrance:d4_griffin (m27.landing window, position); before m25.done Ambrose and the griffin hidden and the perch "empty"; after it the perch's No (stays) and Yes (m27.fly_out: D4 at (6144, 5120) facing 1024 within 64); flown in again to entrance:d6_griffin (no second window; the griffin and Ambrose shown, peaceful); Ambrose struck 40 times (7 hits): hp 228/228, still peaceful; Ambrose clicked, "Fly us out": D4 at (6144, 5120) facing 1024; flown in again; the landing's coffin, notes, the yard gate barred; the south-west tower's diary and purse, down its stair; the sleeping hall: a sleeper hidden, shown by its coffin (+300), kept after a save and a load, then "The coffin is empty.", a find coffin; the Countess's door and jewel box; the keep's upper hall, the grand stair's head and down; the Count's hall's double doors (both leaves); the bar's refusal and the step's; the Count dies: m27.blackfang, blackfang_slain, the bar lifts, then its status line; the crypt: the Dutchess hidden, shown, the Countess's empty, the hoard; the dungeon stair down, the question room's door and chest, the cells; into the Queen's cell: m27.queen_cell's text and queen_seen 111544, not again on the way back in; the Queen struck 40 times (8 hits): hp 280/280, still peaceful; the Queen clicked, "The crown" (queen_found, not done); the shaft's diary, the bolt opens the trapdoor, the ladder up, the trapdoor from above, the cask, the cellar door, the kitchen, the courtyard, up the courtyard stair, the gate barred, the bar lifts it, onto the landing; the gong opens the panel, the ledger, the study's chest; the roof trapdoor, the roost's chest; the Lineage; a fire plate; the south-east tower's loot then empty; the chapel's two leaves; the crown (clicking the Queen): done, the flight to D1 measured; flown back in: the Queen hidden, Ambrose shown, the bench "The Queen has gone home."; a save and a load: the same |
| `playtest_hostility.yml` | 55 checks | 39, 10, 3, 1, 10, 2, 5 hostile at load (sleepers counted), none peaceful; the griffin and Ambrose hidden, the Queen shown and peaceful; after m25.done and a load the griffin and Ambrose shown peaceful; vampires, gargoyles, the griffin and Ambrose side by side on the landing do not fight (Ambrose unhurt, still peaceful) |
| `playtest_octopods.yml` | 127 checks | four sworded Knights; from the bank or ledge by each of the five octopods (actors 9-13): the party's Attack hurts it (trace `damaged` within 9 s) and it hits the party (trace `impact` within 9 s); each press follows a cure, since the octopod's touch leaves members unable to act |

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d4_griffin` (= start) | (0, -1472, 1280), north (512) | (0, -1472, 1280) | D4's gate, m25.gate_flight (A6): `evt.MoveToMap(0, -1472, 1280, 512, 0, 0, 0, 0, "xeen_dd14.blv")` |
| `entrance:d6_griffin` | the same spot (D-42) | (0, -1472, 1280) | D6's m25.flight (phase 5) |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| Ambrose's Yes (m27.fly_out) | D4 `entrance:dd14_griffin` (6144, 5120, 1216) | **(6144, 5120, 1217)** | west (1024, the move's own) |
| The crown (m27.ambrose_return, A3's move) | D1 (-9728, -3072, 1664) | **(-9728, -3072, 1665)** | west (1024, the move's own) |

The roof trapdoor (D7, phase 6) is bolted; the D7 lane would add `entrance:d7_roof` under it in the roost.

## Ids

- Map qbit: `dd14_arrived_once` 117480 (A3's; block 117480-117519). Read: m25.done 111503, blackfang_slain 111540,
  done 111542, queen_seen 111544 (set by m27.queen_cell; queen_found 111543 and crown 111541 through A3's topic). Player bits: none.
- Map variables: `bar_open` 1, `wine_found` 2, the coffins' 3-12, `once.count_dead` 13, `study_open` 14, `hatch_open`
  15, `jewels_found` 16, `tower_purse` 17, `yard_gate_open` 18, `once.arrive` 0.
- Groups: 1 vampires, 2 gargoyles, 3 octopods, 5 the Count's four, 11-15 the sleepers, 30 the griffin and Ambrose,
  31 the Queen. Actor indices (objects.yml's monsters sorted by id): 0 Ambrose, 9-13 the octopods, 16 the Count, 31
  the griffin, 49 the Queen, 53 the Dutchess, 56 the sleeper in coffin dorm_w1.
- Slots (= A2's row 9167, encounter 10, D-52 (1)): `{monster: Xeen Vampire, tier: 5, per_marker: [2, 3], weight: 100}`.

## Words needed

1. (Done: `party_position` takes `facing`/`facing_within`; the D4 set-downs are checked at 1024.)

## DECIDE

1. **Rooms merged:** the graph's sw_stair2, se_stair2 and dstair_foot are the lower floors of the two-storey stair
   rooms (31 sectors, M band; the graph's 40-45 "large" aim not met). Cheaper than a stair column of separate rooms.
2. **The yard gate stands at the courtyard stair's head** (its bar on the stair's side), not at its foot: the same
   rule (barred from the walls, lifted from the courtyard side).
3. **Thin inner parapets:** the walks' inner walls are 32 thick so the strip where the walk's sky meets the
   courtyard's reads as a thin line; the alternative is no opening over the courtyard.
4. **Rest slots:** settled by D-52 (1): one slot, vampires Dif 5 [2, 3] w100 (as built).
5. The keep's upper hall reaches the library across the grand stair's head gallery (the graph's open link).
6. The bats boiling out of the roost (sound and particles) are not built.
7. **Ambrose stays after done** (session 9): D-52 says DD-14's Ambrose is shown from m25.done and never hidden (the
   only way out without spells), so after the Queen's done only she is hidden; the session's brief said "both hidden
   after done". Cheaper to reverse: one `hide_actors: 30` under `evt:queen_load` would hide him too.
8. **The bench's own line** "A stone bench." before done (session 9): the click had to say something once the talk
   moved to the Queen herself; the perch's "A griffin's perch, empty." likewise before m25.done.

## Open

- **Octopods (A1/A2):** settled by A2's row 11473 (D-52 (5)): reached, hit back and hurt (`playtest_octopods`, 4 of 4).
  S's octopod model draws them (red, at the waterline), no longer the Sea Monster stand-in. For A1, not a map issue:
  the octopod's touch sets a condition that keeps members from attacking until cured (the test cures before each
  press), and party_attack's 40 swings by a level-42 Knight hit the peaceful figures 7-8 times only.
- **A4:** 5512's and 5001's `actors:`/`place` lines name rows 11917 and 11918 on DD-14 (D-52); D6's flight `{direct =
  true}` was listed here before.
- **A6:** D4's gate (m25.gate_flight) and D6's flight should move to (0, -1472, 1280) facing 512.
- No bake in the root (the lane lead bakes after install).

## Pictures (looked at)

`output/studio_cal/dd14/shots/rooms1_1..8.jpg` (every room from two corners, the stair rooms from their heads),
`things1_1..5.jpg` (every interactive thing), `fix1_1.jpg`, `fix2_1.jpg` (the fixes: planked coffins, the cells'
bars, the parapets from below), `fix3_1.jpg` (Ambrose's griffin, built once unhidden for the picture: MM7's griffin
stands by its perch). Changed after looking: the gallery's portraits on Navan's green clashed
with their grey stone (the gallery is now `cwb` with `cwbport-1`/`-3`); the cistern's slab showed its frieze twice
(scale 2); the walks' inner parapets showed a wide lintel beam (32-thick walls now); the library's bookcase ends and
the yellow coffins (planks now, six-sided); the cells had no cells (three barred cells along the west wall). The tours'
`lua evt.SetMonGroupBit` commands did not show the hidden sleepers in pictures (the playtests check them). Session 9: `shots/s9_dd14_1.jpg` (HUD off): the cistern with the five
octopods at the pool's edge, Ambrose beside his griffin, the Queen by her bench (from `s9_figures` and `s9_ambrose`). Still
plain: the castle's rooms are boxes; the coffins read as plank boxes; the courtyard is a dark brick well; the octopods drew as the Sea Monster stand-in before session 9.

## Installed (session 9, lane lead)

- Installed 00:47 at the orchestrator's request (A3's segment 57 and A6's D4 rebuild wait on it), with the octopods'
  check still open (A1/A2, "Open"): `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd14`, build
  `output/studio_cal/dd14/b_004755` (31 rooms, 2146 faces, 19 doors, 41 lights, 66 events, 5 chests). Audit of the L4
  against assets_dev (`--reach --solve`, `output/studio_cal/a8_s9/audit/dd14.txt`): 0 errors, 1 warning
  (`ride.no_switch`, the cellar trapdoor that opens only from below).
- Baked 00:47 (profile from post.sh's template, as DD-20's); `stale_bakes` none. Tests from assets_dev 4 of 4: playtest
  255 checks, playtest_hostility 47 (`output/studio_cal/dd14/run/four_004954`); `playtest_octopods` not run (fails
  outside the map).
- Baked pictures `output/studio_cal/dd14/shots/baked_s9/` (sheets `baked_s9_a.jpg`, `baked_s9_b.jpg`): the walks under
  the fading sky, the gallery's portraits, the great hall's crest and throne, the crypt's coffins, the cistern. The
  cistern's octopods draw as the Sea Monster stand-in (sharks): the octopod's model is not the map's (S/A2). One frame
  shows broken blue triangles: the camera inside a vampire.

## Reinstalled (session 9, lane lead, D-52)

- Reinstalled 04:21 (`b_042149`, 70 events), baked, `stale_bakes` none. From assets_dev: playtest_hostility 55 and
  playtest_octopods 127 checks 4 of 4 (`output/studio_cal/dd14/run/four_042310`); playtest failed once at step 164 (the
  struck Queen: a member left disabled by the castle's fights made 2 weapon attacks of 40). The playtest now cures the
  party before both strikes (before: `output/studio_cal/dd14/playtest_before_s9_cure.yml`); 313 checks 4 of 4
  (`output/studio_cal/dd14/run/four_042618`). Audit 0 errors / 1 warning (the cellar trapdoor).
- Ambrose (11917, npc 5512, actor 0) and Queen Kalindra (11918, npc 5001, actor 49) are placed in assets_dev: A3 can
  move segment 61's perch click and segment 67's cell click to talks. Polish: the Queen faces the wall by her bench.

## Session 23 (A8): the Queen turned

- Queen Kalindra (`monster:queen`) faced east, into the wall by her bench; she now faces west (`facing: 180`), toward
  the cell's open grille door and the party coming in (dress.py). Nothing else changed.
- Before/after: `output/studio_cal/a8_s23/shots/dd14_before_sheet_1.jpg`, `dd14_after_sheet_1.jpg`.
- Installed 16:34, rebaked 16:43 (`stale_bakes` none). playtest_hostility 4/4 (55), playtest_octopods 4/4 (127).
  **playtest fails 4/4 at step 115 (line 167):** the walk west through the Count's hall sticks at (-231, 2766, 0). This
  predates session 23: the same run on the 06:34 files (`output/studio_cal/a8_s23/root`) fails at the same step
  (`output/studio_cal/dd14/run/four_164713`); playtest.yml unchanged since 04:26. Open for the next A8 session.

## Session 24 (A8): merge point 35 tests

`playtest.yml` fights the Count's hall's mouth before the walk west to the bar: since merge point 33 an indoor clear
stays on its storey, so the gallery walks at z 640 no longer kill the Royal Vampires below, and Royal Vampire 1 (actor
50) stood in the walk at (-231, 2766). `clear_hostiles(950)` at (300, 2750) kills exactly two guards (actors 50, 52);
the Count (1,080 off) and the third guard (1,105 off) stay until the existing clear at (-700, 2752). No map change. 4
of 4 from assets_dev on merge point 35 (315/55/127); 0 stale bakes; audit 0 / 1.

## Session 26 (A8): lectern tops, door leaves, drop pockets

- F12d: the library's lectern (`platform:lectern`) shows an open book on its top (`xnpbook`, 128 x 128, `fit`), the
  study's desk (`platform:desk`) papers (`desktop`, 128 x 64, `fit`): one picture stretched once over each top, from
  `tools/geo.py` (`BOOKTOP`, `DESKTOP`). Was the table planks `7trimda`.
- F12: doors 2 and 3 (events 34, 35: `door:cellar_kitchen`, `door:countess_dorm`) showed 7d13's blank slab `twb1a`;
  they take the castle's iron-bound door `t5d1` (as the keep, crypt and question-room doors), 128 x 256 fitted to the
  224 x 384 leaf (`tools/dress.py` `SINGLE`). Before: `output/studio_cal/a8_s26/before/dd14/`.
- Installed 00:46, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd14/c004535`); audit 0 / 1
  (the trapdoor's `ride.no_switch`, as before); check_exits 0; `stale_bakes` none.

### Drop pockets

`check_drops` lists four; none is a trap:
- The lower castle (z -736..688: ground floor, dungeon, cistern; doors 34-42, lever 49): the grand, dungeon, back and
  courtyard stairs are flights over their rooms' continuous floors, and their treads share no edge with those floors,
  so the check misses them (it also pairs floors of different storeys that line up from above). The playtest walks the
  way back the brief built: the shaft's bolt and ladder (-640 to 0), the kitchen, the courtyard stair and the yard
  gate's bar onto the landing (1280). The cistern's water lies between sloped banks (-736 to -640), walkable.
- The great hall's long table top (`7trimda`, z 80), the library's bookcase top (`twb2`, z 896) and the hall's dais
  (`t3s2fl1`, z 32, rise 32): furniture tops the check reaches only through floors of the storey above lined up with
  their edges; from a top the party steps down onto the floor it stands on, and the dais is a 32 step.

## Session 27 (A8): D-89 identity, a castle, not a manor

`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2 called DD-14 "a manor" (tan and green brick boxes, yellow tiles, plank-box
coffins). Changed in the generator only (`tools/geo.py` "D-89 identity" block, `coffin_plat()` and `biers()`;
`tools/gen.py` `IDENTITY`; `tools/dress.py` the force plate's floor); the generator reproduced the installed L4 first
(snapshot `output/studio_cal/a8_s27/before/dd14/`). The story beats are untouched: the griffin's landing and perch,
Ambrose and his flight out, the Queen's cell, the battlements, the bar and the crypt.

- **project.yml `identity:`** `{shape: castle, family: 7d32, seen: [the griffin's landing on the battlements with its
  coffins, dark halls under pointed ribs and the Count's hall, the crypt under its pointed vault and the Queen's cell]}`.
- **Dark halls:** the halls in Navan's grey block (cwb, were green ceb1sa) and every pale marble floor (t3s2fl1, the
  "yellow tiles") now dark flags (7tfb11) over a dark base course (cfb1, 48) in the halls, chapel, library and
  gallery; the corner towers in dark brick (`wall`, were tan twb2; D4's hkm3b is a footing panel and refused: 20
  `trim_tiled`/`storey_stacked` errors); the Count's dais topped in the chapel's dark red stone (cwb1).
- **Pointed ribs** (`ribs()`): raking beam pairs meeting under the ceiling's middle every 512 across the great hall,
  the keep's upper hall, the Count's hall, the chapel, the long gallery, the Countess's rooms, the sleeping hall, the
  library and the study (none within 256 of a chandelier). The halls are stacked under each other, so the ribs stand
  under flat ceilings (a vault would cut the floor above).
- **Pointed vaults where nothing stands above:** the family crypt (ridge 832 along its length, `ceiling_points`) and
  the north-west and north-east towers' top storeys (cones 384 over their walls).
- **Coffins:** every coffin is a lidded six-sided stone coffin on a 64 bier (were plank boxes on the landing, in the
  sleeping hall and the north-east tower); the south-east tower's loot coffin stone, on its storey without a bier.
- **"Torn faces"** in the design's `baked_s9_a.jpg`: the tour camera stands inside a Vampire at the south-west tower's
  head (blue robe and skin shards; the same in `s27_before` shot 06): no geometry fault.
- Not built: red and black banners (no banner picture in the world's sets; D-44/U-1 allow no new art here), bats and
  guano in the roost (the roost's ceiling holds the roof trapdoor, left alone).
- Textures 42 of 45, 1 new (unchanged). Installed and baked; audit **0 errors / 1 warning** (`ride.no_switch`, kept),
  check_exits 0, check_drops 0; tests **12/12** from assets_dev (`output/studio_cal/a8_s26/run/dd14/c012155`); stale
  bakes none.
- **Name test** (things tour): before `output/studio_cal/a8_s27/dd14_before_sheet.jpg`, after (baked)
  `dd14_after_sheet.jpg` (unbaked preview `dd14_pre_sheet.jpg`). The arrival is the battlements under the sky; the
  first fight rooms (walks, sleeping hall) show the parapets and the stone coffins; the signature rooms (the Count's
  hall, the crypt) read as a dark castle under ribs and vaults.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the five chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. The fitted tops
stand on the floor (no underside faces). Installed, baked; audit 0 errors / 1 warning (ride.no_switch, as before),
check_exits 0, check_drops 0; tests 4 of 4 (12 of 12, output/studio_cal/a8_s26/run/dd14/c021942). Chest pictures:
output/studio_cal/a8_s29/shots/dd14_chests.jpg (all four on the floor; the cistern chest on the pool's ledge).

## Session 29 (A8, 2026-11-22): identity family exception

- `check_identity.py` measures 43 % in 7d32: the assigned 7d32 with 7d13's crypts make 60 % together; the halls' grey
  block (`wall`, 23 %) is the 27th session's castle look. Recorded as an exception in the tool (`EXCEPTIONS`).
