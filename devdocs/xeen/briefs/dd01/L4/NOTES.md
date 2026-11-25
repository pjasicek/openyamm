# DD-01 Castleview Sewer, L4: notes

The source's Castleview sewer (dark/aaze0030) rebuilt as a new M dungeon on D1 Castleview Vale: story step **M16**
(Nadia's onyx necklace in the rats' nest) and side quest **Q-D5** (Valio the Simple and Rooka the Rat Queen), built with
the Map Studio from its graph (`devdocs/xeen/mockups/act3_graphs/dd01.graph.yml`) and decider D-26
(`devdocs/xeen/mockups/act3_a8_decisions_a.md`, which wins) by lane A8's sub-agent `agent:xeen-a8-dd01`, 2026-11-20.
Key `dd01`, project `xeen_dd01`, stem `xeen_dd01.blv`, map_stats 9150, world `xeen`, music 44.

**State.** L1-L4 `oymap validate` no issues, `fmt --check` clean, build 0 warnings. Installed in the scratch root
`output/studio_cal/dd01/root` only (the lane lead installs into assets_dev). `oymap audit --world xeen --reach --solve`
(`output/studio_cal/dd01/audit.txt`, `solve.txt`): 0 errors, 0 faces in one plane, 0 dressing findings, one warning
kept (below); solve reaches 23 of 23 rooms in three steps, both exits to D1 listed. **Playtests: all five 4 of 4
from the root** (`run/four_180159`).

**Scratch** `output/studio_cal/dd01/`: `tools/gen.py` (plan, project, diagram; `python3 gen.py L1 L2 L3 L4`),
`tools/geo.py` (rooms, openings, themes), `tools/dress.py` (objects, wiring), `tools/tour.py` + `tools/sheet.py`
(tours and JPEG sheets), `cycle.sh` (generate, fmt, validate, build, install into the root, audit, record;
`LEVELS="L1 L2 L3 L4"`, `INSTALL=0`, `ROOT=`), `four.sh` (the five playtests N times, one game at a time, exact PIDs;
`ASSETS=` defaults to the root), `shoot.sh <tour>` (one tour run), `run/` (logs), `shots/` (sheets).
**Every project file of L1-L4 except the playtests and these notes is written by the generator**; each run recorded
with `oymap record --author agent:xeen-a8-dd01`.

## The sewer

Two levels in one frame (x east, y north, heights from the arrival floor at the hatch ladder's foot):

| Level | Rooms | What |
|---|---|---|
| Town drains (0) | square shaft (the hatch, arrival), the drain cross (four piers, a sump), west drain, guild-row shaft, the jammed sluice, north drain, gate shaft, east drain (the cellar's floor grate in its south walk), market shaft, temple shaft, Felix's tunnel, Valio's bed, overflow cistern | 4 Dire Rats, 6 gremlins, 3 Gremlins, 4 Vampire Bats, 4 + 3 Dire Rats |
| Deep culverts (-512) | overflow stair (0 to -512), deep cistern, outfall tunnel, rat runs, nest culvert (the flooded one), nest ramp (-512 to -224), the rat queen's nest (-224), bone slide (-224 to -480), bone midden (-480), drowned cellar (-480, under the east drain) | the rest |

The drains have a slow sewage channel (MM6 `swprrf3`, the engine's sewage liquid) down their middles (the east drain's
along its north side, so its south walk holds the floor grate); the cross, the overflow and the deep cistern have
pools, the cellar a sunken corner of standing sewage. The five shafts are 512 square and 1,280 tall, Castleview's grey
ashlar up to street grates, with an iron ladder on one wall.

**Measured:** 23 rooms, **24 sectors** (M 20-45), **35.4 M units² of floor** (`oymap metrics`; M 30-90), 7 doors (+3
movers, 3 levers: 13 door records), 5 chests, **50 placed monsters** (+ Valio's hidden trap monster), 26 lights,
10 placed sounds, 28 decorations.

## Monsters (all placed, Xeen rows of A2)

| Who | Row | Level | Where | Count |
|---|---|---|---|---|
| Dire Rat | 11393 | 10 | west drain 4, overflow 4, market shaft 3, rat runs 3, nest mouth 4 (the culvert's four), midden 3 | 21 |
| Vampire Bat | 11311 | 14 | east drain 4, deep cistern 4 | 8 |
| Gremlin | 11020 | 14 | sluice 4, north drain 3, cellar 3 | 10 |
| Gremlin Saboteur | 11021 | 18 | sluice 2, cellar 1 | 3 |
| Wererat | 11400 | 18 | rat runs 3, nest 4 | 7 |
| Rooka the Rat Queen | 11403 | 24 | the nest (`monster:rooka`, group 5) | 1 |
| Valio | 11193 | 45 | Valio's niche, **hidden** (group 20), shown hostile once `valio_angered` | (trap, D-1.2) |

**Kill XP** L(L+10): 21 x 200 + 8 x 336 + 10 x 336 + 3 x 504 + 7 x 504 + 816 = 16,104 for the party, **4.03k per
member** (D-26's 4.03k). No monster stands below the culvert's high-water line (D-26 Q5): the culvert's four Dire Rats
wait at the nest's mouth, floor -224, above the water's top (-240).

## Mechanisms

- **The sluice** (D-26, XD-10's route): `switch:sluice_lever` on the sluice house's north wall toggles
  `mover:water` (the culvert's sewage: one block from the culvert's floor to 16 under its roof, sinking 290 in 5 s,
  its top 18 under the floor) and `mover:sluice_gate` (the gate the gremlins wedged 160 up, dropping onto the channel's
  floor). The map variable `sluice_shut` follows it and picks the window: shut "...The gate drops shut, the channel
  stills, and somewhere below you water drains away with a long gurgle."; opened "...the old culvert floods to its
  roof." Clicked while flooded, the water says "The old culvert is flooded to its roof. Somewhere above, the town's
  sluice is pouring into it." A refill resets lever, water and variable together. Played: refused (flooded, the line),
  shut (drained), opened (flooded again), shut, then walked through.
- **The cellar's floor grate** (D-26): a hole in the east drain's south walk over the drowned cellar, covered by
  `mover:grate` (an 8-high slab with one round grate, d1lggrt); `switch:grate_bolt` high on the cellar's north wall
  slides it 240 east, once (`grate_open`; afterwards "The bolt is drawn; the grate lies open above the ladder.").
  From above the grate says "The grate is bolted from below." (hover "Sewer Drain"). `ladder:cellar` climbs 480 from
  the cellar to the walk. Played: refused from above, the party walking onto the shut grate toward the ladder stays on
  the drain's floor (z 8: the ladder is not taken down through it), bolt drawn, climbed up.
- **The outfall** (D-26): the outfall tunnel's east wall is the exit face (the round grate); `switch:outfall_bar` is a
  two-state bar: lifted it sets **`q-d5.outfall_unbarred` = 117001** (provisional, for A3) "You lift the iron bar out of
  its brackets. The grate swings free on the mill gorge."; dropped it clears it. The exit's condition is that qbit
  ("The grate is barred. The iron bar across it lifts out from this side." otherwise). D1's grate (D1 event 222) reads
  the same name. Played both states.
- **Four bolted shafts** (D-26): the ladder panels of the guild-row, gate, market and temple shafts say "The grate is
  bolted from above. You hear the town over your head." (hover "Sewer Drain", dark/aaze0030). Their finds: **Red
  Liquid** (+2 Might, player bit **11310**) and **Green Liquid** (+2 Endurance, player bit **11311**) on ledges at the
  guild-row and temple shafts' feet, once per character, by event (the source's "+5 Might (permanent)." rescaled to
  +2); the market shaft's chest of dropped things; a gate guard's skeleton in the gate shaft (his purse, 150 gold, once
  per game behind map qbit `guard_purse` **117002**; then "Nothing here.", dark/aaze0030).
- **The hatch** (the way in and out): the ladder on the square shaft's south wall; its foot is the exit face (the
  `exit` preset: the game's "Do you wish to leave...?" window; "Exit the Sewer?" dark/aaze0030 is its meaning).
- **Rooka** (`monster:rooka`, row 11403): a timer event runs A3's once-hook `q-d5.rooka` at her death
  (rooka_slain 113101, 3,000 XP, "Rooka the Queen Rat is dead. Down the tunnel, someone in a bed cheers.").
- **The heap of shiny things** in the nest (a trash heap, hover "Heap of shiny things"): A3's once-hook `m16.necklace`
  (the onyx necklace 12332, necklace_found 111321; then its else text). Played: the necklace once.
- **Valio** (NPC 4957): his **bed** (`platform:bed`, hover "Bed", dark/aaze0030) opens his talk (`evt.SpeakNPC(4957)`,
  topic Rats; see Words needed); once `valio_angered` (113104) is set the bed says "The bed is empty, its blankets
  thrown back." His **chest** runs A3's `q-d5.valio_chest` on its opening; a timer event shows the hidden monster
  Valio (11193, group 20) once `valio_angered` is set (`q-d5.valio_angry`; map variable `valio_shown`, reset by a
  refill with the actors). Played both ways: paid (Rats after Rooka, chest, no anger) and early (the yell, Valio shown
  hostile, still shown after a save and a reload).
- **Felix the Tinker** (NPC 4958, A4's row in `source/towns/d1.yml`, written while I built): his workbench at his
  tunnel's end (`platform:felix_bench`, hover "Felix the Tinker") opens his talk (`evt.SpeakNPC(4958)`): the compass
  and the sluice hint (D-26). Sells nothing.
- `evt:arrive`: a one-shot timer window on the first arrival only (`arrived_once` **117000**): "THE CASTLEVIEW SEWER.
  The ladder from the square ends ankle-deep in something you decide is water. Down here the town's rats keep what they
  steal, Nadia's onyx necklace among it, in the nest of the Queen Rat they call Rooka. Four more shafts come down from
  the streets, their grates bolted from above: this hatch is the way back up."

## Exits (live to D1) and arrivals

Measured on the installed D1 (A6's reinstall of 17:57, files linked into the root; the party dropped from 6,000 and
read back, `output/studio_cal/dd01/run/zprobe2.log`): ground 1,228 at (1088, 3328) beside the hatch (1,165-1,246 round
it: the square slopes), the mill gorge's floor 833 everywhere within 256 of (7936, 8192).

| This map's exit | To | Arrival on D1 | Facing |
|---|---|---|---|
| `exit:hatch` (ladder foot, square shaft) | `xeen_d1.odm` | (1088, 3328, 1228): 192 west of the hatch thing:dd01_hatch (1280, 3328) | west (180°, game 1024), away from it |
| `exit:outfall` (outfall grate, once unbarred) | `xeen_d1.odm` | (7936, 8192, 833): 256 east of the outfall grate thing:dd01_outfall (7680, 8192), in the gorge | east (0°), away from it |

**D1's doors into this map (A6):** the hatch should arrive at this map's start, **(0, -1088, 0) facing north (90°,
game 512)**, the ladder's foot; the outfall grate (once `q-d5.outfall_unbarred` is set) at **(4096, -4864, -512) facing
west (180°, game 1024)**, inside the grate by the bar. D1's hatch event (145) and outfall event (222) still say the
sewer is not open yet.

## Original lines

"Exit the Sewer?" (dark/aaze0030, the leave window's meaning); "Sewer Drain" (the grates' hover, dark/aaze0030);
"Rubble" / "Bones" / "Nothing here." (dark/aaze0030); "The barrel is empty." (dark/aaze0030); "Red Liquid", "Green
Liquid", "+5 Might (permanent)." rescaled to "+2 Might (permanent)." (dark/aaze0030); "Bed" (Valio's, dark/aaze0030);
Valio's and Rooka's lines are A3's hooks (aaze0030:10-25); Felix's is A4's (aaze0030:1, D-26).

## Ids

- Map qbits (block 117000-117039, provisional): `arrived_once` **117000**, `outfall_unbarred` **117001** (A3: register
  as `q-d5.outfall_unbarred`, the name D1 reads), `guard_purse` **117002**.
- Quest bits read/set through A3's hooks: 113100-113104 (q-d5), 111321 (m16.necklace_found).
- Player bits (provisional): **11310** Red Liquid, **11311** Green Liquid.
- Map variables: `sluice_shut`, `grate_open`, `valio_shown` (+ the studio's `once.*`).
- NPCs: 4957 Valio the Simple (bed), 4958 Felix the Tinker (bench). Monster 11193 Valio (hidden, group 20).

## Textures (one family)

**27 distinct of 45, 0 new** (`tools/xeen/texture_budget.py --root output/studio_cal/dd01/root --map DD-01`). MM6
Shadow Guild Hideout `6d03` and its MM6 sewer stone (dungeon_families `sewers`): block stone `d1wlbct1` (cross,
sluice, niche) with jambs `d1wlbre1`, the wet sewer walls `d1wldle2` (drains) and `d1wldle3` (cisterns), the old
mossy stone `d1medbw` (east drain, cellar), rough stone `d1wle` (culverts, tunnels, the rats' caves), the outlet panel
`d1wldsp`, flags `d2flor2`, planks `bemvwal` (Valio's floor and bed, Felix's bench), straw `d1sbpa` (the nest), timber
`bemh`/`bemv` (bench rail, cellar ladder), doors `beemdorc` and the iron `d8dore` (sluice house, outfall door, the
sluice gate), the round grate `d1lggrt` (shaft tops, outfall, floor grate), the ladder `d1ladder`, sewage `swprrf3`.
Castleview's grey ashlar `t09a01` over `t09b11b` in the five shafts (D1's kit). Chest and lever pictures add the
rest. For A6: DD-01's family is 6d03 + the MM6 sewer stone (d1wldle2/3, d1medbw, d1wle, d1lggrt, d1ladder, swprrf3).

## Dressing (D-7)

`oymap audit --world xeen` on the installed map: **0 dressing findings** (the first L4 had two bones on walking lines,
moved). Props: two barrels as a pair by the cellar's east wall (one clicked: "The barrel is empty."), bones and a
skeleton, trash heaps in the rat runs and the nest, dirt in the nest, a brazier by Felix's bench, wall torches.
**Dressing exceptions:** none.

**Audit warning kept:** `ride.no_switch` on door 8 (the floor grate): the party can stand on the 8-high slab, and the
bolt that moves it is in the cellar below. The grate slides level (it does not carry anyone) and is moved once, from
below, by design (D-26).

## Playtests

`output/studio_cal/dd01/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd01.blv`; the root has a test map_stats/bolster row for 9150 (copied from XD-01's with this map's name, stem,
continent 7, music 44, slots below) until A2 writes it. Logs `output/studio_cal/dd01/run/four_*`.

| Test | What |
|---|---|
| `playtest.yml` | the critical path through every mechanism (header), the boss, the hooks and back |
| `playtest_hostility.yml` | 21, 8, 10, 3, 7, 1 at load (+ Valio hidden: 51), none peaceful; a Wererat, Dire Rat, Vampire Bat and Gremlin side by side in the cross do not fight each other, the last targets the party |
| `playtest_valio.yml` | the chest opened before Valio pays: the yell, chest_opened and valio_angered, Valio shown hostile, the bed empty, still shown after a save and a reload |
| `playtest_exit_hatch.yml` | the hatch exit, the game's window, OK: D1 within 128 of (1088, 3328), z 1,150-1,300; walks west |
| `playtest_exit_outfall.yml` | barred, bar up, down (barred again), up; exit, OK: D1 within 128 of (7936, 8192), z 820-860; walks east |

**Results: all five 4 of 4, exit 0** (`output/studio_cal/dd01/run/four_180159`, summary `four1.out`): playtest 182
steps, hostility 28, valio 23, exit_hatch 21, exit_outfall 20 asserts passed in each run.

## Pictures (looked at)

`output/studio_cal/dd01/shots/rooms2_1..5.jpg` (37 poses: every room and interactive thing, the culvert flooded,
draining and drained, the grate shut and open), `fix1_1.jpg` (the grates), `d1arr_1.jpg` (the two D1 arrivals facing away and looking back at the
hatch and the outfall's culvert: the outfall arrival stands on the gorge floor a few hundred from the river). PNG
folders deleted for the disk; `tools/tour.py rooms <name>` and `shoot.sh` remake them. What I changed after looking: the rats'
caves had MM6's sewer-pipe end (`swpend2a`) as walls (it reads as wood panelling) and bright straw floors (now rough
`d1wle` over flags, straw only in the nest); Felix's tunnel floor was garish planks (now flags); the shafts' ceilings,
the outfall's and the floor grate's round grates were cut by the texture grid (the outfall grate scaled to its face,
the floor grate and its hole moved onto the grid, the east drain's channel moved north for it). **No bake in the root**
(the lane lead bakes after install): lighting is the build's own.
Still plain: the nest and the midden are boxes with rough walls, the cistern vaults flat; the sluice gate is a slab of
the iron door picture; the shafts' ceilings show four small street grates each (the texture grid).

## Words needed

1. **A talking monster indoors** (objects.yml `monsters` take no `npc`; `core/IndoorBuild.cpp` writes `npc_id: 0`,
   while outdoor sketches have `npc:`). Workaround: Valio talks from his bed and Felix from his workbench (clicked
   platforms running `evt.SpeakNPC(id)`); neither has a body. When the word exists: Felix as an immobile talking actor
   at his bench (needs a peaceful body row of his own, A2), Valio stays in his bed (the source never shows him).
2. **A surface offset** (texture origin) for a single picture on a face: the round grates fall on the world's texture
   grid; the floor grate was moved onto it.

## Waiting on, and requests

- **A2**: map row 9150 (slots below); record the two liquids as fixed by event (+2 Might / +2 Endurance, once per
  character, bits 11310/11311).
- **A3**: register `q-d5.outfall_unbarred` = 117001 (D1 reads that name), `arrived_once` 117000, `guard_purse`
  117002, player bits 11310, 11311.
- **A6**: D1's two doors into this map (start points above); D1's event 145 (hatch) and 222 (outfall) to the exit
  preset / door into `xeen_dd01.blv`.

## What the user should look at when playing

- The hatch shaft and the drain cross; the four other shafts' ladders (bolted) and their finds.
- The sluice lever: watch the culvert's water from the rat runs drain and, after "Open", flood again.
- The cellar's grate: refused from the east drain, opened from below, the ladder up through it.
- Valio in his bed (talk from the bed), his chest before and after Rooka; Felix at his bench.
- Whether the rats' caves (rough stone over flags) and the plain nest read as a rat queen's lair.

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 11 oymap (byte for byte the agent's build) and installed into assets_dev by temp file
  and rename (`output/studio_cal/a8_s5/rebuild.sh dd01`; `b_180459`).
- Baked (`output/studio_cal/a8_s5/bake.sh dd01 <scratch root>`, profile
  `tools/lighting/baked_indoors/profiles/xeen_dd01.yml`, XD-08's values; `stale_bakes.py` 0). Baked pictures
  `output/studio_cal/dd01/shots/baked_a.jpg`, `baked_b.jpg` (37 shots, looked at): drains, shafts, the cross, the
  sluice gate, Felix's bench and Valio's bed read right; the culvert's water seen from the rat runs is a flat blue
  panel filling the culvert mouth until drained (the sinking-water mover's front face), worth a look in play; the
  hatch shaft's ceiling shows four small grates (no texture-offset word, as noted above).
- A3 (18:05): 117001 is `m16.outfall_unbarred` (D1's side `m16.outfall`); the map's bar sets and clears it.
- **Waits on A2's row 9150** for the playtests from assets_dev (`ASSETS=$PWD/assets_dev output/studio_cal/dd01/four.sh`).
- **A6's return points** (18:15): the exits land on D1 at A6's points for D1's events 145 and 222: the hatch
  (1024, 3072, 1152) facing east (0), the outfall (8192, 8192, 832) facing east (`tools/gen.py`, copy before
  `gen_before_a6pts.py`; the two exit playtests' asserts moved with them). Rebuilt (`b_181515`, only the Lua's two
  `MoveToMap` lines changed), installed; the bake stays valid (`stale_bakes.py` lists no A8 map).
- A2's row 9150 landed; **playtests from assets_dev 4 of 4** (`run/four_181612/`, `four_assets_dev.out`):
  `playtest` 182, `playtest_hostility` 28, `playtest_valio` 23, `playtest_exit_hatch` 21, `playtest_exit_outfall` 20.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/dd01/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- Felix's brazier (`brzier00`, chained) hangs from his tunnel's ceiling (384 clear; height 236), its top 2 into it.
- **Named arrival for A6:** `arrivals` gains the outfall's arrival for the plan's existing entrance
  `entrance:d1_outfall` (the brief named it `entrance:dd01_outfall`; DD-01's entrances are named after the neighbour, as
  `entrance:d1_hatch`, and an arrival must name a plan entrance): inside the grate at **(4096, -4864, -512) facing west
  (1024)**; `xeen_dd01.studio.yml` lists it. D1's way in can name it: `into: {map: xeen_dd01.blv, arrival:
  entrance:d1_outfall}`.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/dd01/audit_lights.txt`): lights
  errors/warnings before **1/0 (ceiling_on_floor)**, after **0/0**; no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd01` (build `output/studio_cal/dd01/b_192638`), baked
  (`output/studio_cal/a8_s5/bake.sh dd01 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_dd01.yml`),
  `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from assets_dev, each 4 of 4**
  (four.sh; record `output/studio_cal/dd01/lights_post.out`): playtest 4/4 (182 steps); playtest_hostility 4/4 (28
  steps); playtest_valio 4/4 (23 steps); playtest_exit_hatch 4/4 (21 steps); playtest_exit_outfall 4/4 (20 steps).
- **Pictures** `output/studio_cal/dd01/shots/lights_mp14/`, looked at: the brazier hangs on its chain at the end of
  Felix's tunnel, over his bench.

## Session 7 batch (sewer bed, A8 session 7, 2026-11-20)

- AU's `xeen_amb_sewer` (62800, trickles and drips) as the sewer's bed: three sources in `tools/dress.py` `sounds()`
  (copy before: `dress_before_s7.py`): west drain (-1280, 0), east drain (3584, 0), rat runs (1280, -3840); radius
  3200, inner 1000, volume 0.4 (inner circles apart, ~4,300-4,900 between sources). The ten placed drips and water
  loops stay.
- Audit (oymap 20:45:55, texture fit): 0 errors before and after; 1 warning (`ride.no_switch`, as before). Recorded,
  installed, baked; tests from assets_dev 4 of 4 (182, 28, 23, 21, 20 steps; `output/studio_cal/dd01/s7_post.out`).
- No pictures: nothing drawn changed.

## Session 21 (A8): AU's sounds

The room-filling beds `sound:bed_east`, `bed_south`, `bed_west` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8): actor heights, ladders out of the pools

- Rebuilt for the new actor heights in the monster tables (the scene's `height:` lines; `check_actor_heights.py` no
  longer names the map's Night Bats).
- **F14:** check_drops found four pockets, the sunken sewage (`swprrf3`) the party could drop into and not leave on
  foot: the cross's sump (64 down), the overflow pool (96), the deep cistern's pool (64 below its floor -512) and the
  sluice channel (96). `tools/dress.py` `ladders()` adds iron rungs (`bemv`, as `ladder:cellar`) up one straight edge of
  each: `ladder:cross_sump` (0, 152) north, `ladder:overflow_pool` (-1152, -1416) north, `ladder:deep_pool`
  (-1152, -4488) north, `ladder:sluice_channel` (-1608, 1024) east. check_drops 0. The drains' channels (48 down) are
  left on foot. Before: `output/studio_cal/a8_s26/before/dd01/`.
- `playtest.yml`: Nadia's necklace in the nest (`q-d5` hook) is a status line since A3's hook change (was a window).
- Installed 00:52 and baked; audit 0 errors / 1 warning (`ride.no_switch`, as before), check_exits 0; tests from
  assets_dev 4 of 4 (20 of 20, `output/studio_cal/a8_s26/run/dd01/t005617`). Pictures of the sump and sluice ladders:
  `output/studio_cal/a8_s26/sub1/shots/dd01/`.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the five chests: the style world's 7gt002 chest (95 faces) in place of MM6's ch1 (55 faces), same places, none
moved. Installed, baked; audit 0 errors / 1 warning (ride.no_switch, as before), check_exits 0, check_drops 0; tests
4 of 4 (20 of 20, output/studio_cal/a8_s26/run/dd01/c021833). Chest pictures:
output/studio_cal/a8_s29/shots/dd01_chests.jpg (all four on the floor against a wall).

## D-166: the sluice hinted and visible (agent `xeen-cv45`, 2026-11-25, issue #45; run files output/cv45/)

- **The flooded water's click** (`evt:culvert_water`, status line, D-90): "The culvert to the Rat Queen's den is
  flooded. Its sluice is worked from the sluice house, at the far north-west of the upper level." Valio's Rats topic
  (`source/quests/q-d5.yml`, his first line and his "still alive" line) ends with the same two sentences; Felix's
  greeting is unchanged. Tables rebuilt (`build_world.py`: npc_topic_text.txt and xeen_quests.lua only).
- **The sluice lever** (`dress.py` `SLUICE_LEVER_AT`): moved from the north wall's far end (-1280, 2048) to the east
  wall at (-896, 1600), 384 north of the iron door and in line with the gate, at twice the standard size (post 16 x 64,
  arm 80 out, arm at 128); titled "Sluice" (was "Sluice lever"). Its lamp: `deco:torch_sluice_lever` (torch02 on the
  east wall beside it, its own id so the other torches keep theirs) and `light:sluice_2` (radius 640, the lamp colour).
  Seen from the west drain's arch and from the iron door (captures below). No grate or water front on the culvert mouth.
- **Felix** (`monster:felix`, NPC 4958): on Picard the Aged's peaceful indoor row 11922 (xeen_sor1 xsor_g, the old
  scholar's grey-brown robe and white hair; the Elder Druid's row likewise carries two NPCs), immobile, group 21, at
  (-2990, -2720) by the west end of his bench; clicked, he talks (the bench still does). Not counted; key_npcs lists
  him (actor 12). "Words needed 1" is done for Felix. The actors after him moved up one: Rooka 36 -> 37, Valio's
  monster 46 -> 47 (`playtest_valio.yml`, `tests/scenarios/xeen/side_quests/q-d5_rooka.yml` follow).
- **Tests:** `playtest.yml` stands just inside the iron door (-1000, 1152) facing the lever (460 away) and presses the
  interact key: event 34, the gate drops, the culvert drains, the nest is reached through it; Felix is talked to by the
  interact key on his body; Valio's topic and the water's line are asserted. `playtest_hostility.yml` counts Felix
  (52 actors). All five 4 of 4 from assets_dev (189, 29, 23, 21, 20 asserts); Q-D5 side quest and story segment 45
  pass (their culvert-line asserts updated).
- **Checks:** audit 0 errors, 1 warning (`ride.no_switch`, as before); check_exits 0, check_drops 0, check_identity 0;
  key_npcs 0 errors; check_actor_heights clean; MAW pack reserve rerun (51 of 51); xeen_balance --check ok;
  stale_bakes 0. Installed (a8_rebuild b_122417) and baked straight after (12:26).
- **Captures** `output/cv45/shots_dd01/` (looked at): the lever and its lamp from the iron door and from the arch,
  close; Felix at his bench; the flooded culvert from the rat runs.
