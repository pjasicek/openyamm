# D7 The Skyroads: L4 notes (A6 sub-agent, sixteenth session, 2026-11-21)

D7 is Act VI's sky road over the whole Darkside (party 50-75): an open-air BLV of cloud roads and islands with
Olympus, the four element corners, the Megadragon's roost and the Sky Lake. It is built from the L1 plan with D-58
applied (`../L1/D58_DECISION.md`; `../L1/NOTES.md` "D-58 applied") and D-61's amendment for the Alamar hatch.

**Built and tested in the scratch root `output/studio_cal/d7/root/assets_dev`, not installed.** The lead installs it
with `INSTALL=1 output/studio_cal/d7/stage_install.sh` once the orchestrator has added `xeen_d7.blv` to `world.yml`'s
`openAirMaps` (the script refuses otherwise).

## Route: the studio

X9's and P5's route (`../../x9/L4/NOTES.md`, `../../p5/L4/NOTES.md`): one open-air room `room:air` from the safety
floor at -6,000 to the sky at 6,400, every wall, floor and ceiling a sky face; the room is 128 x 88 cells, cut to
x ±32,640 (a BLV's coordinates are int16). Atmosphere: `open_sky` preset `xeen_skyroads` (alias `xeenroads`),
`view_distance_scale` 2, no weather (Q9).

| Script (`output/studio_cal/d7/tools/`) | Writes |
| --- | --- |
| `gen.py` | rooms.yml for L3 and L4 (and L3's start) |
| `gen_plan.py` | plan.yml and project.yml for L2-L4 from L1's; the falls from A3's `Xeen.SkyFalls` |
| `gen_objects.py` | objects.yml, wiring.yml, atmosphere.yml (A3's hooks by name; the dungeon doors' switches) |
| `gen_playtests.py` | the ten playtests (from the build's ids.lock.yml); `--probe` checks every walk leg with `oymap probe` |

The design is `level_generation/xeen_art/phase6/d7_design.py` with its D-58 block, and the outlines and the L2 snaps
are `d7_geom.py`'s (the spans and spacing measured at L1 are the ones built).

| Shell script (`output/studio_cal/d7/`) | Does |
| --- | --- |
| `run.sh` | the L1 (render, measure, brief, fmt, validate, board) |
| `setup_root.sh` | the scratch root (hard links; data_tables and world.yml copied, `xeen_d7.blv` in its openAirMaps) |
| `v.sh`, `b.sh`, `cycle.sh` | generate + fmt + validate; build; build + install in the root + audit |
| `tests.sh` | the playtests N times through lane A6's two game slots |
| `a.sh` | the audits (project with the lanes' full set, and the map installed in the root) |
| `stage_install.sh` | a hard-link stage of assets_dev, install, audit, playtests 2x, then `INSTALL=1` new file + rename |

There are no hand edits: the generators are the source.

## What was built

- **Clouds:** every island a hanging cloud (`xccloud` top, `xccloudsd` sides) with two or three flared roots.
- **Roads (D-8):** every ring road, spur, the dragon road and the three causeways are cloud slabs with a band of
  cloud-stone flags (`7tws1f`) a third of their width down the middle, laid exactly over the slab (same slope, 6
  over it) and on 416 into each island; the causeways' bands stop at Olympus' gates. Rope bridges: `t66floor` decks,
  `hwm2rf` rails (X8's).
- **Corners:** a cloud spit from each corner cloud out to corners.yml's tip, ending in a flagged disc where the sky
  asks; a blank 'Zone' board beside each spit.
- **Olympus:** the cloud paved in `7tws1f`, a low balustrade (`hwm1b` footing band) open at the gates and the jetty;
  three gates of open gilded posts (`ctflor5`, no leaves, no griffins); A4's 13 houses as blocks of pale ashlar
  (`gtempw1`, MM8's temple stone; MM7's `hwm2wall` read as brown fieldstone in game) with gilt-trimmed cornices,
  `hwm2d` doors and the five service signs; the temple on the square's north side with a six-column portico and a
  stepped gold dome; Soul Storage's walk-in vault; the Mirror of Olympus (`xkmirror` in a gilt frame); four statues
  (`7dec54`) on plinths; Lucio's marble jetty; the ants' lookout; DD-26's grate. Olympus is small from the rope (D-8).
- **The Pyramid's Door:** the golden capstone floating 64 over its cloud, the sky door (`xdpyrdor`) in a porch on its
  east face; `entrance:dd15_sky` before it (D-61's "near the apex": the capstone is the Great Pyramid's apex).
- **The roost:** the black crag, bones, the hatch of weathered metal, the Megadragon on it, the hoard.
- **The Sky Lake:** water (`wtrtyl`, liquid water) in the bowl, an island of cloud, the four scarab stalls with canvas
  awnings (`tentrf1`), two bottles, the board.
- **Boards (D-7):** the 18 boards and the four zone boards on P5's blank `xp5brd`, the Rest Stops' huts (P5's) with
  `xp5rest`; their words on hover (the `text` preset's title) and as a status line on a click.
- **Hatches:** seven roof hatches as plates of weathered metal (`gn_mtl03`).
- **Set pieces:** the four merchants' gilded sky-barges, S's decorations (rows 4051-4054, radius 0, no collision; one
  tint per cargo's element: smoke `xeen_skybarge_fire` (-29277, 2797) facing 325, dust `xeen_skybarge_air` (-1553,
  20276) facing 184, steam `xeen_skybarge_water` (6976, -19504) facing 56, mud `xeen_skybarge_earth` (29449, 4231)
  facing 22.5). Each lies along its island's rim fully over the void, its deck level with the island, its port
  gangplank resting on the island; each hangs at the island's floor height over the void (no floor under it). Not
  boardable: the merchant (the click's point) stands on the island at the gangplank's foot, and a click on the barge
  runs the riddle. The dust barge lies on the north crossing's north rim, so the causeway's mouth stays clear; its
  merchant moved from the causeway's mouth to (-1518, 19830). Lucio's celestial boat (`xeen_skyboat`, row 4055) is
  moored along the jetty's north-east side at (1429, 2423), deck 1780, prow out to the void (facing 327); the jetty's
  north-east rail stops 832 short of the end, so the boat shows alongside. Also four toll booths beside the road with
  the toll's line across it, the rope's frame, the castaways' bones and lean-to, the Broken Launch's plain marble
  jetty.

## Wiring (A3's hooks by name)

| Thing | Event |
| --- | --- |
| Falls | `evt:fall_check` (one-second timer, under -1,000) and `evt:fall_floor` (the safety floor) call A3's `Xeen.skyFallD7()` (the six zones) |
| Corners | step on the tip: 'What do you seek?'; the element's name runs `m38.corner_<element>` (A3's `Xeen.toPlane`), any other answer `m38.corner_wrong` |
| Tolls (D-6) | step on the toll's line: `Xeen.toll("north"/"east"/"south"/"west", <its pair's group 70-73>, ...)`; map variables `d7_toll_<key>` |
| Merchants | the barge (`deco:barge_<cargo>`): `Xeen.merchantRiddle(cargo, ...)` |
| Lamps (Q-D27) | `Xeen.genieLamp("d7_tired"/"d7_kind"/"d7_angry", ...)` |
| Bottles, scarab stalls | `d7.bottle_*`; `d7.scarab_<element>` after the hook's own question |
| Roof hatches (D-4) | the hook's question, then `d7.hatch_ddNN` ('Bolted from below.') |
| Alamar's hatch (D-5, D-61) | before `m33.done` into DD-17, after into FD-01 (`q-d26.hatch`, then the exit); both sealed with the source's locked lines until their maps are live; after `m33.done` A3's "Castle Alamar is gone." |
| The Megadragon (D-3) | a two-second check of its group runs `q-d26.slain`; a load event hides it once 113520 is set |
| Pyramid's sky door | 'Enter the Pyramid?' and the exit to DD-15 after `m30.done` once DD-15 is live; else a sealed line |
| Olympus | `evt.EnterHouse(4801-4814)`, `Xeen.useMirror(4807, ...)`, `m31.statue_1-4`, the vault door open on `m30.done`, `m31.soul_storage` (shelves), `m31.true_name_plaque`, `m31.arrival` on Lucio's jetty |
| The rope | 'Descend to the Darkness Below?' to D1's `entrance:d7_rope` (by name from D1's studio.yml) |

**Switches** (`gen_objects.LIVE`): DD-15 `entrance:d7_sky`, DD-17 and FD-01 `entrance:d7_roof`, DD-26
`entrance:d7_stair`: each door goes live when its BLV is in assets_dev and its studio.yml lists the arrival.

## Figures (L4)

| Figure | Value |
| --- | --- |
| Placed | 50 in 19 groups (Griffins 12, Sky Golems 8, Cloud Dragons 8, Cloud Golems 22), all fixed; + the Megadragon (uncounted); + 8 Sky Bandits 11116 (peaceful, uncounted, two per toll) |
| Kill XP a member | 48,802 (53,021 with the Megadragon; bandits A2's 7.15k line) |
| POIs / chests | 56 / 5 at treasure 6 (the hoard holds Wyrmfang 12530 and the roof key 12377) |
| D-1 longest empty stretch | ring 8,128; inner road 6,956; north causeway 7,703 (all ≤ 8,192) |
| D-1 POI nearest-neighbour max | 8,149 (≤ 8,192) |
| D-2 Megadragon leash circle | 6,808 from every walkable place but its road; castaway island 11,340, its bridge 9,497 (≥ 5,888) |
| First fights | rope 4,399; returns 4,472-5,724; roofs 3,075-5,838; sky door 3,938; Olympus' arrivals 5,477 and 8,719 (town buffer) |
| Walkable | 480.5 M units² (roads 147.1 M, Olympus 63.7 M); quiet 80 % |
| Build | 1 room, 4,303 faces (9,594 triangles), 130 events, 5 chests, 0 lights; 27 textures, none new (Dungeon L, cap 70) |

## Checks

| Check | Result |
| --- | --- |
| validate L2-L4 (scratch root) | no issues |
| build | one warning kept: "liquid and flow: 13 of 23" (X8's, X9's) |
| audit, project, `--reach --solve --dressing --lights --doors --textures` | 0 errors, 0 warnings (`output/studio_cal/d7/audit.txt`) |
| audit, installed in the scratch root | 0 errors, 0 warnings; faces in one plane 0 (`audit_root.txt`) |
| walk legs (`gen_playtests.py --probe`) | 105 of 105 straight-walkable |

Playtests, headless, `build-xeen/game/openyamm` (merge point 25), from the scratch root, two runs each:

| Playtest | Covers |
| --- | --- |
| `playtest.yml` | rope's head, the whole ring through the four corners, the inner road, Olympus by its south-west gate, the square, the north and east gates, Lucio's jetty (`m31.arrival`'s bit). The hostile groups are cleared first: the walk checks the ways (`playtest_hostility` counts the groups) |
| `playtest_hostility.yml` | 12/8/8/22 of the four rows and the Megadragon hostile, the eight bandits peaceful, nobody hurt in 20 s |
| `playtest_corner.yml` | the Fire Corner's tip asks; a wrong answer runs `m38.corner_wrong` ("The sky says nothing.") and the party stays |
| `playtest_megadragon.yml` | the Megadragon at its post with the party in sight for 30 s; the hoard gives Wyrmfang and the roof key |
| `playtest_fall_ab12` ... `ef34` | one fall per zone (D-54): the landing within 256 of A3's point on D6, D5, D4, D1, D2, D3; every member's HP the same 0.5 s and 20 s after |

Results: 20 of 20 (`output/studio_cal/d7/tests_final.log`, logs `xrun/run_044834`); the fall probe `xrun/run_042336`.

**Falls: damage differs by map (reported).** Every fall arrives at the SkyFalls ground + 850 with `keepHeight` and
falls the whole way (probe `output/studio_cal/d7/probe/`, z sampled every 0.1 s from the arrival): yet on D5
(1024, -4608), D1 (-6656, 6144) and D2 (15872, -6656) the level-55 party loses nothing (315/142/198/132), while on D6
and D4 it loses about a third (214/97/136/90, D-6.2). D3's point lies 127 under its SkyFalls ground (lands at 1,313
against 1,440), so its fall is 977 (197/89/126/83); one run in three before took no damage there. The playtests hold
each map's measured values; the D-54 check (nothing lost in the 20 s after) passes on all six.

## Dressing exceptions

None. Containers: the five chests only (the hoard by the crag, the castaways' by their bones and lean-to, the camp's,
the pack by the launch); booths, huts and boards stand off the walking lines (the walk's 105 legs are clear).

## Texture fit exceptions

None. Boards and signs are `fit` once per face; the mirror once at 3x; `hwm1b` only on the balustrade's sides and the
statue plinths (a footing band once up).

## Words the studio lacked (workarounds)

- **A leash for an indoor monster:** since merge point 26 the Megadragon has `leash: 1024` (session 18; it was
  `immobile`); `playtest_megadragon` checks it within 1,280 of its post after 10 s and 30 s.
- **World decorations in a BLV:** since merge point 26 the lamps are S's `xeen_genielamp` (clicked: the event's source
  is the decoration) and each Rest Stop hut has two of S's `xeen_bench` against its back wall (`floor_height` the hut's
  floor: without it the studio stood them on the roof); the gilt blocks and the plank benches are gone (session 18).
- **A fall zone indoors:** the timer plus the safety floor (X8's).

## Blocked / open

- Session 18 (A6, 2026-11-21): Alamar's hatch (event 49) live into DD-17's `entrance:d7_roof` before `m33.done`
  (without the Soul Box DD-17's `m33.roof_arrival` sets the party back on the roof), the Pyramid's sky door (event 105)
  into DD-15's `entrance:d7_sky` after `m30.done`; `playtest_doors` walks both and a lamp. Still sealed: the hatch into
  FD-01 after `m33.done` (A7/A8).
- Session 19 (A6, 2026-11-21, installed 06:44): DD-26's grate (event 104) asks A3's `q-d28.sewer_grate` question
  "Descend into the sewer?" (aaze0037:1) and moves to DD-26's `entrance:d7_stair` (0, 0, 0) facing 512. D-66: the
  grate, Alamar's hatch (49) and the sky door (105) ask with the map's own Yes/No buttons (`AskChoiceWithAnswerSteps`)
  and move at once (`{direct = true}`). The sky door calls A3's `d7.pyramid_door` first (before `m30.done` its
  "Access Denied!", as DD-15's side); Soul Storage's door (127) shows `m31.soul_storage`'s fail_text (A3).
  `playtest_doors` also walks the grate (No stays, Yes in) and asserts "Access Denied!".
- The roof arrivals `entrance:dd02_roof` ... `dd14_roof` wait on A7's and A8's roof stairs.
- S: the Sky Bandit skin (the barges, the celestial boat, the genie lamp and the benches are in).
- AU's D7 sounds are in (session 26, AUDIO.md session 5): the four corner tips carry their plane's bed as a panned
  point sound (radius 2,500, 128 over the tip; Earth at 0.9), `sound:megadragon_sleep` (key 14) on the roost, off
  on the kill (evt 80, after `q-d26.slain`) and on every load once slain (evt 81: `AmbientSound14` = 2), and three
  dragon calls (wait 25-60 s, about 1,024 over the roads; the cap's call stands over the void, so its height counts
  from the safety floor). The sky bed (`xeen_amb_sky`, `pan: false`) stays under them.
- No new textures were made: `xsbarge` and `xsglow` were not needed (S's barge models carry their own textures; no
  corner glow was drawn).

## S28-S29: Olympus dressed (A6, 2026-11-21, G3 review row 57; installed 17:16)

- **Houses** (`d7/tools/gen.py` `facade_parts`): MM8 temple marble walls (`gtempw1` at scale 2) on a blue-grey
  `gtempflr` plinth (open at each door; clipped where two houses touch), gilt-capped marble pilasters at the corners and
  between the bays, one blue-glass window (`gtempdor1`, `fit`, once) in a gilt frame per bay, the door in a gilt frame
  under a marble hood, a gilt frieze, a marble cornice, a parapet with gilt coping round the roof terrace and four gilt
  finials. The faces against another house or the vault are left plain. The Dock and Hermes' house stand 96 lower
  than their neighbours (the Training Grounds, Athena's house), which they touch, so their trim lines do not meet in
  one plane.
- **Temple**: a portico of six round (12-sided) marble columns with gilt capitals, architrave, gilt frieze, cornice and
  a raking pediment; carved blind panels (`gtempw2`, once each) on its sides; the gold dome on a marble drum.
- **Gates** (D-8 kept: no leaves, no statues): each an open propylon, two round columns each side on a pedestal and a
  marble lintel, gilt frieze and cornice across the road (entablature at 872-1,080 over the paving, clear of the
  houses' trim levels). At the north gate, between the temple and the Spirit Guild, the inner column of each pair
  would stand in a house and is left out; the lintel rests on their walls there.
- **Textures**: 30, all shipped (new to the map: `gtempflr`, `gtempdor1`, `gtempw2`; none new to the world; Dungeon L,
  cap 70). Faces 8,179 (was 4,303 at L4; open air, no bake).
- **Checks**: build 0 warnings; audit (`--dressing`, from assets_dev) 0 errors, 0 warnings, faces in one plane 0 (the
  S28 draft had 63: door frames against the doors' and hoods' planes, the touching houses' trim, the gates against the
  houses; fixed); stage 22 of 22 runs (N=2), from assets_dev 11 of 11 (`a6/s29/d7/tests_ad.log`), the walk through
  all three gates included. Before/after `output/studio_cal/a6/s29/d7/sheet_d7_before_after.jpg` (12 poses).

## S30: the Mirror of Olympus framed (A6, 2026-11-21, installed 19:30)

- The mirror read as a plain brown slab (xkmirror tiled at scale 3 under a head bar only). Now a gilt (`ctflor5`)
  frame on all four sides: a sill (448 x 48 x 32), two posts (44 x 56, standing 4 proud of the sill and head), the
  head (448 x 48 x 48); the silvered glass (356 x 24 x 356) placed once, uncut (`fit: true`), sunk 4 into the sill,
  the head resting on it and the posts. Sill and posts click as the mirror (`evt:mirror_sill`, `_post_w`, `_post_e`:
  Xeen.useMirror(4807)). 8,197 faces, coplanar 0, audit 0/0; stage 11 of 11; MAW reserve rewritten (59 of 59).
  Before/after `output/studio_cal/a6/s30/d7/sheet_before.jpg`, `sheet_after.jpg`.

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt and installed 01:29 (open air, no bake); MAW reserve rewritten (59 copies). F16: Alamar's roof hatch, the Pyramid's sky door and the Olympus sewer grate lose their Yes/No: the hook decides, then the entrance window with rows 5050 (5062 into FD-01 after m33.done), 5047, 5061. The hatch checks Corak's Soul Box before DD-17 (m33.roof_arrival's refusal on the status line). Stage 11/11; audit 0.
