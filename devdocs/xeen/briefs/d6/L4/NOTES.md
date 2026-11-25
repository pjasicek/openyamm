# D6 The Forbidden Zone, L4 (2026-11-21, A6 sub-agent)

Built from the approved L1 (`../L1`, written by `level_generation/xeen_art/phase5/d6_brief.py`) with D-49's and
D-50's changes. Lane rules: `devdocs/xeen/lanes/README.md`.

## How it is written

- `output/studio_cal/d6/tools/gen.py` writes L2, L3 and L4 (project, plan, sketch, atmosphere); never edit them by hand.
  `output/studio_cal/d6/v.sh`: gen, fmt, validate L2-L4, build into `output/studio_cal/d6/build`, measure.
- `tools/measure.py` (from D4's), `tools/gen_walk.py` -> `playtest.yml`, `tools/gen_hostility_d6.py` ->
  `playtest_hostility.yml`, `tools/tour.py` + `look.sh` (tours), `stage.sh` / `walk.sh` (pre-test stage).
- Install only through `output/studio_cal/a6/install_baked.sh xeen_d6 devdocs/xeen/briefs/d6/L4
  output/studio_cal/d6/build output/studio_cal/d6/present/bake_profile.json`, then `present/redo_minimap.sh`.

## What was built

- **Castle Alamar** on its mesa (floor 2,304) in a horseshoe moat of lava (`lavtyl`, 1,550) open to the south: a curtain
  wall, four square towers (seven storeys), a keep (nine storeys) and a gatehouse, in the Control Center's seamless dark
  teal wall `swll4dk` with one lit `xaenergy` panel in a bay of every storey face, an `xahull` plating crown band once
  along each top (xahull is `trim_u`: it may not repeat up a face), `gn_mtl03` roofs and trim. The gate is a hinged
  pair of `swdoora` (the second leaf mirrored), m33.castle_door's line; DD-17 sealed until it exists. Four energy
  pylons (`xaenergy`, the conduit once per face) on the approach ramp only, `xafield` curtains along each side of the
  ramp. **Ruin state** (set:alamar): every whole part hidden and the ruin parts shown on load when m33.done (111662):
  `xahullbn` stubs (the studio's `ruin` word), the fields dark (hidden), FD-01's stair (a pit in the broken
  gatehouse's floor, m39.depths_door, sealed until FD-01) on DD-17's gate spot.
- **The D-50 travel pyramid** outside the moat's mouth (56.5, 62), `gn_mtl02` cladding, its click
  `Xeen.travelPyramid("alamar_gate")`; `entrance:xd17_pyramid` beside it, no marker within 2,000 (keep-clear).
- **Corak's pod** nose-up in the lava lake at (72.5, 67.5): a 12-sided hull 640 in radius of `xahullbn` under a
  `gn_mtl03` nose cone, its round hatch (`a2c`, one leaf) turned south-east toward a tongue of black rock; the hatch
  is m29.pod_door (A3: the fail line until lava_cooled) into DD-16's `entrance:d6_hatch` (live). **The crust**: a pier
  of cooled rock (`voltyl` deck, `vlcwl1lg` sides) at 1,466 over the lava from the hatch to the tongue, hidden until
  `lava_cooled` (111564) shows it on load. DD-16's way out `entrance:dd16_hatch` lies on it 384 before the hatch,
  facing south-east, at the whole cell (74, 69) = (5120, -2560); **but the studio writes a named arrival at the
  terrain's height (the lava bed, 1,440), not the crust's 1,466, and sketch points take whole cells only**, so a party
  sent there burns (A7, session 15): DD-16's exit keeps A7's measured crust point (5076, -2516, 1466) until A1 lets an
  outdoor arrival stand on a structure's top (request, session 15). Sheltem's pod upright in its crater (78, 38), `swll4dk` hull, d6.sheltem_hatch's line.
- **Necropolis** (A4's d6.yml 4751-4762): walls of t09 ashlar 704 high with battlements, square corner towers, a
  gatehouse with the `xnpgate` crest once over the gate; the gate a 256 x 256 opening with two leaf pairs of
  `chb1dl`/`chb1dr` (128 each, the picture once): outside they ask d6.necropolis_gate (item 12336; else A3's refusal),
  inside they are always open (D-49 change 8). The guild and the temple two-storey halls with double doors (t09a03a,
  two leaves), the market, the embalmer and the Warm Barrel cottages, six tombs of Zokarr's Tomb stone (twb2, twb1
  caps); the Square of Mourning paved, the mirror (`thing:np_mirror`, 4756) with the talking skull (d6.skull) one
  spot, the three Books of the Dead (lecterns with `xnpbook` once on each top; d6.book_dead_1-3), the barrel by the
  Warm Barrel's wall (beside its door), DD-21's crypt stair (grille pair gkp103a, sealed until DD-21).
- **Griffin Pass** (64, 96): Ambrose (5512, D-52 row 11917) and the Tethered Griffin (11913) in group 6, hidden on load
  by m25.camp_gone after m25.done; the tent and the fire stay. m25.flight (his topic) moves itself to DD-14 (A3).
- **The wilds**: obelisks.d6 on Obelisk Knoll; the Fountain of Super Resilience (+100 HP daily) and a pilgrim's pack;
  three genie lamps (`Xeen.genieLamp`: d6_pinnacle on a basalt plinth, d6_islet on the islet, d6_crag); the archers'
  camp (three tents, a fire, the strongbox; the burn question on the standard beside it, d6.archers_camp); DD-10C's
  adit (an open cave mouth, sealed until DD-10C), two boarded mines, the prospector; the griffin's nest; the broken
  pyramid (ruin, no click); the Well of Warding (+20 four resistances until rest, daily); the Ancient locker; the
  pilgrim's cart; the zone sign (d6.zone_sign); the empty climbers' camp (a tent, no click: no Freeda); a roofless
  watchtower of the dead; the cinder vent, an Ancient spar and wyrm bones in the cinder plains (landmarks, no click);
  the lava falls (`xeen_lavafall`) where the Slag Run and the north falls pour over the rims.
- Rim rule `{cliff_x: 24, cliff_y: 24, fall: death, sides: [north, west]}`; sky xeendark1 (A3's Lua stage); atmosphere
  `ash: 40`, `view_distance: 1.8`.

## Monsters (A2's rows)

- Markers: 33 (E1 gazers 17 in the Ancient field, slot 1; E4a/E4b griffins 8 + 8 on the southern peaks, slot 2).
- Placed: 14 lava dwellers (Lesser Fire Elemental 11620 x11, Fire Elemental 11621 x3, A2's D-58 names; leash 1,024 over the lake and shores, none within 2,500 of the hatch's
  way out with its radius), 12 archers (11104 x9, 11105 x3), 18 robots in nine groups (11610 x16, 11611 x2).
- **42 markers (D-49 Q8) became 33 markers + 18 placed robots**: the studio's markers carry no group, so D-49 change 7's
  hide on load (D-36's coven pattern) needs the robots placed. Hostiles at load stay 110; the robots never refill.
  Slot 3 (Xeen Robot) of row 9113 is unused by markers.

## Measured (`tools/measure.py`, build of 2026-11-21)

| Figure | Target | D6 |
| --- | --- | --- |
| Hostiles at load | 110 | 110.0 (33 markers x 2 + 44 placed) |
| Kill XP per member | 71.1k (D-49: 73.4k) | 73.3k |
| POIs (D-20 census) | at most 28 | 27 |
| Outdoor chests | 4-10 | 6 |
| First fight from D1 (south_road) | 2,000-6,000 | 4,671 |
| First fight from DD-10C's adit point | under 6,000, no marker within 2,000 | 3,508 (placed archers' camp nearer than any marker) |
| Pyramid arrival | no marker within 2,000 | 3,367 to the nearest fight |
| Hatch way out | no lava dweller + radius within 2,500 | checked in gen.py; 4,471 to the nearest fight |
| Town buffer (Necropolis doors) | 2,500 | 3,168 |
| 6,000 rule | none over 6,000 | farthest 5,910 (62, 83); 0 tiles over |
| Quiet land (over 3,000 from a fight) | at least 1/3 | 0.49 |
| Relief inside the box (land, lava and rim out) | at least 2,500 | 800-3,520 (2,720) |
| Encounter areas (4,096 squared) | 6-30 | E1 19.6, E4a 9.3, E4b 10.3, E2 robots 6.5 |
| Roads | 1-4 % | 2.7 % |
| Model triangles (tools/tris.py) | - | 12,347 (10,737 shown at load, 1,610 hidden: the ruin, the crust, FD-01's stair) |

- **Spacing:** the median POI spacing of about 4,050 is accepted (D-49 change 5, as X7's 3,280): 22-28 POIs on this
  much land cannot reach a 1,300-2,600 median.
- **Four-map corner:** the installed D1 and D2 disagree at the four-map point (2,176 against 2,496); there is no
  crossing there; it is left as is. D6's x 109 column carries `edge_d5_d6.json` for y 0-109 (y 106-109 = 2,636 / 2,440
  / 2,260 / 2,176); the y 109 row repeats D1's installed y 19 row.

## Tests

- `oymap audit ... --reach --solve --dressing`: 0 errors, 0 warnings.
- Installed with its bake 01:22:30 (a6/bake_xeen_d6_012045); not stale. Walk (`playtest.yml`, 263 steps) 2/2
  (run/walk_g1, walk_g2) and hostility (run/host_g1) pass on assets_dev. `oymap audit xeen_d6.odm --world xeen --assets
  assets_dev --dressing --lights --doors --textures`: 0 errors, 0 warnings. towns.py --strict exit 0. Minimap
  installed.
- **The crust (D-49 Q4, A1 confirmed at merge point 21):** a party set over the hidden crust falls into the lava and
  burns (400 -> -52 HP in 6 s); with lava_cooled the crust is shown and a party on it keeps 400 HP for 6 s.
- Session 14 (A6 lead): the walk (`D6_WALK_FLIGHT=1 tools/gen_walk.py`, 301 steps) also takes Ambrose's flight to
  DD-14 (A3 switched `Xeen.onMap` to `evt.GetCurrentMapName`), crosses the east edge to D5 and back over the border
  pass (y 64) and the south edge to D1 and back (A3's travel rows, 7 and 5 days), landing on `entrance:east_pass` and
  `entrance:south_road`; the Necropolis Guild and the Grave Market (A4's hours 21:00-6:00) show the hours line by day.

## Texture fit exceptions

- None flagged by the audit. xahull appears only as one 256 band per wall top (trim_u).

## Dressing exceptions

- None flagged.

## Town feel exceptions

`town_feel.py xeen_d6.odm --world xeen --assets assets_dev --small` (5 services, D-20): 9 figures outside the shipped
ranges, each kept:
- Road or dirt cells in town 1.0, flat terrain share 1.0: the city of the dead stands on one paved terrace (L1's 1,650);
  no grass grows in the Forbidden Zone's ash.
- Trees in and around the town 0: the Darkside's volcanic waste has no living trees (dead swamp trees on the plains).
- Enterable residences 0: the six tombs are A4's residences 4757-4762 with doors; the checker counts by house_data's
  kind (A4's generator).
- Monsters near wild roads 0.02, wild group spacing 3,338 / variation 0.28: few and strong (D-49 Q8), the fights in
  two placed camps, the robots on the mesa and the birds on the peaks; the roads run through the quiet flats.
- Wells and fountains 2: the hot spring's fountain and the Well of Warding; the lava land has no other water (D-40).

## Open items

- DD-10C's adit (session 14): the mouth centred in its timber frame (it stood a cell west of it), its shell in
  `vlcwl1lg`, the frame at the mouth's front, the crag from y 98 at 3,584 (peaks 3,700/3,600) so no sky shows behind the
  mouth from the north, the boarded mines at the crag's foot (`tour/s14adit2`).
- Castle Alamar at night (session 14): `xaenergy` (the cyan strips and green lights glow, always) and `xafield` (glowing
  throughout) have surface maps (`level_generation/xeen_art/nightglow/`); with Settings' Surface materials on, the
  windows read as lit cyan slits at 20,700 and the ramp's fields glow (`pics/sheet_s14night.jpg`). With the setting off
  (its default) the castle stays dark at night.

- Ambrose's row 11917 is live (D-52). The D1 and D5 edges are walked both ways (session 14).
- D1's `entrance:north_road` (64, 19) lies past the travel line (about 22,528 from the middle): a party arriving from
  D6 that steps north is asked again at once; D1's next install moves it to y 21 (A6).
- D5 is installed: the east edge is in the frame (no sign). Session 18 (installed with bake 05:58): DD-10C's adit,
  DD-21's crypt stair (`entrance:d6_stair`) and Castle Alamar's gate (`entrance:d6_gate`) are live. The gate asks A3's
  `m33.castle_door` words as its question ("... Enter?"; the hook's own message box before a move never asked; since
  session 24 Yes/No buttons whose own text is that line, D-72, as the adit's "A timbered adit into the mountain.
  Enter the Mine?"), Yes moves into DD-17, whose `m33.arrival` refuses a party without the Soul Box and sets it back at
  `entrance:dd17_gate`; the walk checks No, Yes and the refusal, and goes in and out of DD-21 and DD-10C. FD-01
  phase 6.
- Session 19 (A6, 2026-11-21): DD-22 live. Sheltem's hatch (event 44) calls A3's `d6.sheltem_hatch`: before `m33.done`
  its sealed line (the party stays), after it the status line and into DD-22's `entrance:d6_hatch` (0, -832, 0); DD-22's
  hatch (its event 19, "Exit Escape Pod 2?" OK) sets the party down at `entrance:dd22_hatch` (7168, 12288, 1952)
  facing south. The walk checks the sealed line, then in and out with `m33.done` set.
- AU's beds (`output/studio_cal/a6/beds/xeen_d6.yml`, from level_generation/sounds/xeen_20261120/review/beds/d6.yml) are in; `sound:alamar_hum` (scene key 1) is switched off by evt:alamar_hum after m33.done.

## Doors and arrivals for the other lanes (world X, Y, Z, facing: 0 east, 512 north, 1024 west, 1536 south)

- `entrance:dd16_hatch` (A7, DD-16's way out): (5076, -2516, 1466) on the crust, facing 1792 (south-east); the
  studio's whole-cell point is (5120, -2560).
- `entrance:dd17_gate` (A8): (-6656, 4608, 2208), facing 1536. `entrance:dd21_stair`: (17408, -11776, 1664), facing
  512. `entrance:dd10c_adit`: (-9216, -16384, 2624), facing 512.
- `entrance:xd17_pyramid` (A3 PyramidArrivals.alamar_gate, A5): (-5120, 1024, 1856), facing 512.
- `entrance:necropolis_gate` (A4): (13824, -6656, 1664), facing 1536; the mirror is `thing:np_mirror`.
- `entrance:south_road` (D1's edge): (0, -20992, 1824), facing 512. `entrance:east_pass` (D5): (20992, 0, 1696),
  facing 1024.

## D-58: the fall from D7 (A6, 2026-11-21, sixteenth session)

`entrance:d7_fall` at (13824, -7680, 1664), facing south, on the Necropolis square, 740 from the mirror (zone A1-B2, `d7_ab12`). Checked against the installed map (`output/studio_cal/a6/s16/fall_points.py`): a whole flat cell (the 3 x 3 nodes level), no water or lava, no decoration or wall within 256, no hostile with a ranged attack within 5,888 (placed actors and spawn markers with their slot monsters). The entrance is kind `both` in the plan only so that it does not become the party start (the studio takes the first `arrival`). The map and its scene are unchanged by the point (byte-identical), so only the studio sidecar was installed and the bake stays valid. The fall tests (D-54's shape) run from D7.

**Merge point 25 (A6, 04:00):** with A1's oymap 03:57:50 an outdoor named arrival on a structure's walkable top stands
on it: `entrance:dd16_hatch` is now (5120, -2560, 1466) facing 1792 (south-east), on the crust, no point moved; the map
and the scene are byte-identical, so only the sidecar was installed (bake valid). `entrance:d7_fall` and
`entrance:necropolis_gate` rose to 1,672 on the square's paving. Walk 2/2 and hostility pass on the 03:57:50 game from
assets_dev (`output/studio_cal/d6/run/mp25_*.log`). DD-16's exit can now name `entrance:dd16_hatch` (A7).

## D-85: missile range round Ambrose (A6, 2026-11-21, thirtieth session)

- Measured (`output/studio_cal/a6/s30/d85.py`): the seventh west griffin marker stood 4,433 from Ambrose (5512).
  Moved, slot kept: `pop:west_griffins` 7 from (55, 101) to (47, 102) (6.3 cells from DD-10C's adit return, D-49's
  2,000 kept). Warning left: west griffins 6 at 5,201. The D1 arrival's first hostile is now east griffins 6 at
  5,689 (the Tethered Griffin, 4,749, is Ambrose's own and peaceful). `gen.py` refuses a circle within 5,120 of Ambrose
  (west griffins 6 excepted: its circle reaches 4,345 but its marker stands at 5,201).

## D-87: the field eyes off Sheltem's hatch (A6, 2026-11-21, thirty-first session)

- Slot 1 (Floating Eye: Paralyze by missile; Terrible Eye: Insane) is a ranged disabler: five field markers stood
  3,024-5,370 from `entrance:dd22_hatch`. Moved, count and slot kept: `pop:field_gazers` 7, 8, 11, 12, 15 from (70, 34),
  (84, 32), (72, 42), (84, 40), (76, 49) to the field's rim (66, 31), (92, 31), (70, 53), (91, 46), (80, 54), and 17
  from (100, 53) to (99, 52) (its circle reached into 5,888 of the D5 arrival). Built: the nearest eye 6,608 from any
  arrival point or giver; kill XP 73.3k unchanged. `gen.py` refuses an eye circle within 5,888 of `D87_ARRIVALS`.
- Kept by D-87: Ambrose 5,201 (west griffins 6, melee).

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt on merge point 41, installed with its bake 01:11: the gate's whole `swdoora` per 256 leaf (doors.part_picture 0). F16: Alamar's gate checks Corak's Soul Box before the move (m33.arrival's refusal on the status line; DD-17 no longer throws a party out), then the window with row 5049; the adit's Yes/No gone (row 5040). F10: the eye at (74, 27) to the north-west corner (28, 28): 738 -> 499 tiles. Walk (gate with and without the Soul Box), hostility, daily pass; audits 0.

## Rim rebuild (agent xeen-rimmap-b, 2026-11-23; U-12, D-109, D-114, F28; run files output/xeen_rimmap_b/d6/)

- **The void and the burnt hull.** The rim sea is `void:rim_sea` (`terrain.void`); 64 hull pieces along the north
  and west rims, one in three on the burnt plating (`*bn`). The two lava falls stand on the land's edge
  (`lavafall_1` (44, 24.02) pouring north, `lavafall_2` (24.02, 51) pouring west). D-114 (no spillway for sand and
  lava): their gaps hold plain burnt faces (`xeen_hullfbn`, new), so from the void the lava pours in front of hull
  (`cap_extra/05`, `06`, `08`). From the land the falls show as the lava river's glowing lip (`03`, `07`), as before.
  Rescue: 24 return points along both rims. Campfire events (Ambrose's and the archers' fires, D-104) come with it.
- **F28: the Necropolis gate on its road.** `NP_GATE` and `NP_ARRIVAL` 91.0 → 91.5 (the gate lane on x 91 lays the
  tiles 91–92); gatehouse, walls and leaves follow; `gen_walk.py`'s four gate poses and `tools/xeen/town_walls.yml`'s
  seal moved with them. `town_fit_check` 0 (was `gates.road_off` 249 off); the entry is dropped from
  `tools/xeen/town_fit_pending.yml`. Picture `cap_extra/01-gate_from_road.png`: the cobbles run into the arch.
- Kit fix found here: a hull piece on the map's last cell (centre 127.5, refused by validate) is skipped
  (`common/rim.py`; X5 and D2 had the same piece).
- **Checks** (private root): audit 0 errors (5 kept back-to-back warnings: the pods, the gatehouse, the wall joint,
  all kept by `check_faces.py`), `void.occupied` 0, door_check 0, wall_check 0, town_fit 0, D-85/D-87 0, empty zones
  pass, props support 0, check_wild clean, check_faces clean, house signs 0. town_feel: 10 figures outside.
- **Tests**: walk (377 steps), daily and hostility 2 of 2, `d6_ambrose_flight`, `hooks_d5_d6`.
- **Pictures**: `output/xeen_rim/after/d6/` (clear weather; against `output/xeen_rim/before/d6/`),
  `output/xeen_rimmap_b/d6/cap_extra/`, sheets `output/xeen_rimmap_b/d6/sheet_extra.jpg`, `sheet_rim.jpg`. The void
  stays dark under the Darkside haze.
- Side quests crossing it, normal and `--reload` (2026-11-23, after the installs): pass (rim doc §6, map agent MB).
  Story segments and promotions: held for the orchestrator's single chain run after all 12 rim maps.

## D-142, D-157, D-162, F59, F63, F66 (2026-11-25, `xeen-fb4-outdoor3` sub-agent D)

- `gen.py d142_enforce()` (common/d142.py, per slot): 6 circles moved: three west griffin circles off DD-10C's adit
  (2,441-3,012 < 4,096; the old D-85 exception west griffins 6 now 7,380 from Ambrose), east griffins 5 off DD-21's
  stair (4,092), two eye circles off the field tracks (D-157). A moved circle keeps build()'s rules (town doors,
  Ambrose, the arrival clearances, D-87.3's 5,888 for the eyes) and F63's 768 from the bounds and the hull.
- Not moved (DECIDE 2026-11-25): Alamar's robots, groups 14-19 (2,985-4,924 from DD-17's gate / FD-01's stair and the
  XD-17 pyramid, 5,888 needed: only the mesa's north rim behind the castle is far enough) and the lake's fire
  elementals, groups 1-4 (no lava 5,888 from both DD-16's hatch and the pyramid but a thin north-shore strip). They
  stay `check_d85` warnings and D6 stays out of `check_arrivals.D142_EXITS` until the decider rules.
- F59: the cinder vent sinks 32 (its foot hung 26 over the cinder slope), the smoke with it. F66: the second tavern
  barrel to (84.25, 82.25) (it stood through the tavern's corner). F63: the nine archers round the fire between the
  tents, (35.0, 85.9) spread 1.0 (the fifth stood inside the first tent).

## D-164 (2026-11-25, agent xeen-fb4-outdoor4; installed with its bake 11:41)

- Alamar's robots: groups 14-19 on the north half of the mesa (`ROBOT_SPOTS`: east flank (58.6, 44), north rim
  (54.8, 39) for the Annihilators, (47.4, 39), (49.3, 37.9), west flank (41.6, 44), (43.2, 42.6)); 11, 12 stay; 13 from
  (58, 40) (one robot in the moat at 1,536, one on the cliff at 2,089) to (57.9, 42.4) under the north-east tower. 16
  Patrols + 2 Annihilators, every robot 0.69+ cells inside the mesa's edge on its top (2,264-2,299). Nearest robot
  6,586 from DD-17's gate / FD-01's stair (was 3,118), 9,291 from the XD-17 pyramid (was 2,731). gen.py refuses a
  robot spot under ROBOT_CLEAR (5,888) and its spread from either, prints one under ROBOT_AIM (6,400).
- The lava dwellers (14, leash 1,024): group 1 in the moat's east arm (63, 46), group 2 in its west arm (36.5, 46)
  spread 0.8 and its Elemental (37, 43.5), groups 3 and 4 on the lake's north shore ((67.9, 57.8), (66.8, 58.5) spread
  0.5; their Elementals (69.5, 57.6), (68.8, 57.3)). `LAVA_CLEAR`: every home 6,144 and its spread from the DD-16
  hatch, the pyramid and the gate (the drawn point and its built whole cell), replacing D-49 (4)'s 2,500 hatch rule.
  The shore's band is narrow: x 67.6-68.2 at y 57.8 for a 0.5 spread. Nearest: 6,275 from the hatch, 6,598 from the
  pyramid. `tools/xeen/check_reach.yml` keeps groups 1, 2, 4 (fliers over the lava; group 3 now stands on the shore).
- `xeen_d6` is in `check_arrivals.D142_EXITS`; no kept groups; `check_d85` 0, `common/d85.py` 0 FF and 0 FFW lines.
- First fight, headless (`output/xeen_fb/p4_outdoor4/d6/fight/`, an immortal level-30 party set down at each arrival,
  every placed hostile logged for 60 s): at the gate the nearest robot stays at 6,586 and none targets the party in
  the minute (inside D-15's 4,096-8,192 band; no ambush, so no mesa leash); at the pyramid the nearest lava dweller
  stays at 6,597. Captures `output/xeen_fb/p4_outdoor4/d6/tour/`.
- `gen_hostility_d6.py` reads a build's scene (argv 1) or the installed map's: it read the lane's stale
  `output/studio_cal/d6/build` and kept the old elemental homes. Rerun it after an install (regen.py runs it before).
