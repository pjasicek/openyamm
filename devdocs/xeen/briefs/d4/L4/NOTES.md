# D4 Lakeside and Blackfang, L4 (2026-11-20, A6)

The approved L1 (MU-3, board `level_generation/xeen_art/phase4/d4/board_d4.png`) built to L4 with decider D-36 (and
D-39, A8's entrance names). The project files here (and L2, L3) are written by
`output/studio_cal/d4/tools/gen.py`; never edit them by hand. Build folder, tools, tours and logs:
`output/studio_cal/d4/` (PROGRESS.md lists the commands).

## How it is written

- `gen.py` reads L1's plan, sketch and project, A4's `source/towns/d4.yml` (houses 4651-4667), A3's hooks with `map: D4`
  (every one wired or the script stops), D3's installed border row (y 19 of `xeen_d3.odm`) and the world's decoration
  bindings (S's `xeen_batstorm`). The land is a function sampled on the 4-cell grid (L1's points and the rises between
  them, the lake's bed and shores, the Snow River's cut, D3's border blended in over y 100-108), with terraces (the
  town 1,120, the crag top 3,104, the camp 2,304, the clearing 1,888, the grove 1,504, Ector's 1,440, the Isle 1,104
  with its knoll 1,376, the brow 2,272, the ledges), cliffs (the rim, Blackfang's four faces, the lair's rock face),
  two ridges and peak fields.
- The lake is two bodies (north of y 70, south of y 69) notched round the Isle and the two skerries on whole cells.
- Doors into dungeons are live only when the BLV is installed, A2's map_stats row names it and its studio sidecar lists
  the door's entrance (`ENTRANCE` in gen.py); until then each shows a short sealed line.

## What was built

- **Lakeside** (A4's d4.yml, Darkside town kit): the guild 4651 (two storeys of t09 ashlar over a t09b11b floor band,
  a t09 window in every other bay of both storeys, a slate gable roof with eaves, its carved double door 256 wide as
  two leaves of `t09a03a`, the second mirrored), smithy, tavern, temple, Lakeside
  Yachts with the ferry jetty at x 72 and the ferry moored along it, ten houses; every house but the guild, the Yachts
  and Old Gill's shows A4's closed text until `q-d22.done` (113441). The mirror 4656 on the square (Xeen.useMirror),
  Naomi (5318) in the stocks facing the guild's door; the square paved (t09a02a) with the town well, two market stalls,
  two benches; barrels in pairs by the tavern's and the smithy's walls.
- **The guild's riddle** (q-d22.guild_door): answered (113442) the door opens the guild; else the hook's riddle and the
  map's "What am I?" (witch, witches, a witch): right runs q-d22.guild_right (membership); wrong runs
  q-d22.guild_wrong and the trapdoor into DD-20's sewer half (`entrance:d4_trapdoor`, live since session 12). A
  separate **back stair** (a cellar hatch in the guild's west wall) leads members (113442) into DD-20's coven hall
  (`entrance:d4_guild`, live since session 12); before 113442 it reads "A cellar door. The front door asks first."
  (D-42 (1)).
- **DD-20's shaft** between the Eel House and the Yachts: "Climb down to the sewer?" (Yes/No buttons, D-72) then a move to
  DD-20's `entrance:d4_shaft` (a structure has no `leave` effect: Lua from the sidecar), open from day one (D-36 (4));
  live since session 12.
- **Skiff's beached boat** on the shingle east of the Boathouse: "There is a sign here that reads 'This boat under
  repair.'" and its locker (a chest) behind "Search the boat? (Yes/No)".
- **The Isle of Lost Souls**: its jetty, A4's Isle Ferry (house 4667, Tern) on `thing:isle_ferry` (`poi:isle_boat`,
  cell 73.4, 73.6) with a skiff moored by it, the Isle's sign, graves, dead trees, bones; **DD-12's ruined round tower**
  (D-42 (2): 1,040 across, roofless; a 640 base of hkm2bs with its door a hinged pair of `hkm1dl` leaves, 128 each,
  mirrored, under a ruined crown of stubs to 1,280, `thing:isle_tower_crown`); the door asks A3's m24.isle_door
  (`lost_souls_key`; refused: "Locked. Two iron-bound leaves, and a keyhole."), then sealed until DD-12 lists
  `entrance:d4_isle`.
- **Castle Blackfang** on its crag top (3,104), 17,600 from the ferry jetty's end: a battlemented curtain of black
  rubble (hkm2bs), four round towers (16 sides: each face one 128 bay; hkm2bs, one hkm3b skull-frieze storey, a top
  storey of yellow-glass hkm3elw windows on alternate faces, xtslate cones), the keep (six storeys of hkm2bs with one
  hkm3elw window per face and storey, each a bay aside of the one below, the skull frieze as its seventh storey, a slate
  hip roof), six beacon fires (dec60) on the curtain's walk, and **S's bat storm** (`xeen_batstorm`, row 4003) over the
  keep (z 6,204) and the south-east tower (z 5,904) (`BAT_STORM_SPOTS`), its shrieks a 9-second map timer playing the
  shipped `bat_aware` at both spots. The crag's faces are cliffs (south 1,200 into the lake, west 900, east 800, north
  700): no way up on foot.
- **The gatehouse** at the crag's west foot on the north-shore track (cell 77.4, 53): two round towers and a
  battlemented gate block, the gate a hinged pair of `chb1dl` (192 each, the second mirrored); it never opens: A3's
  m25.blackfang_gate. After `m25.done` (111503) its click asks "Would you like my griffin to fly you inside?" and Yes
  flies the party to DD-14's `entrance:d4_griffin` (D-42 (3); the gate asks `XeenQuests.can("m25.gate_flight")`, Yes
  calls A3's hook; sealed with a status line until DD-14 lists the entrance). DD-14's griffin sets the party down at `entrance:dd14_griffin`.
- **The bat storm's knock-down** (m25.bat_storm): a `when_flying` timer (1 s) over the crag top (cells 81-94 x 41-56,
  above 2,700) ends Fly (`evt.RemovePartyBuff("Fly")`, merge point 18), moves the party to the north-shore track by
  the gatehouse and calls the hook (its status line).
- **The north and the mountain**: the Snow Springs' tarn (2,272), the Snow River down its cut to the lake under the shore
  bridge, the snow track to the Fountain of Great Resilience (daily +200 HP) where the rims meet, the roc nest, the frozen
  pilgrim; Magic Mountain (to 4,160), Xanthus and Slibo's camp (two gabled tents of the shipped tent textures, the fire, the Fountain of Great Magic, daily
  +200 SP, Slibo 5317), the genie's lamp on the Wizard's Seat, the woodcutters' clearing with Ector's woodpile
  (q-d21.woodpile), the lair path up to **DD-23's cave mouth** in the rock face (q-d15.lair_door's line, then Yes/No buttons
  "Enter the cave?" (D-72; the window shows the hook's line with the question under it), `entrance:d4_mouth` (D-39); live since session 11: A7's DD-23 lists it, and DD-23's mouth returns
  to `entrance:dd23_lair`).
- **The Forest of Peril**: **Leafpoint** (5319, MM7 Treant 453, friendly by the map's relations) in a ring of great trees
  (tree69, tree60a) at (42, 61); **Ector** (5320) by his cabin (no house) with his chopping block; the hunters' hide and
  trunk; two animal traps (a step, once, 20 damage).
- **The west shore and the heath**: Gull Knoll's obelisk (obelisks.d4, dark_4), the coven's reed cauldron (daily: +100 SP
  or Poisoned), the Witches' Circle (seven stones, the cauldron, three skulls on stakes with the recipes, the offering
  chest), the Sandcaster wagon's strongbox, Gallows Knoll's gibbet and purse; the desert road's end sign (D5 sealed).
  The cauldron is a one-member gamble, so D-70 rule 4 applies, not rule 1 (D-71).
- **The east shore**: Well Fork's Fountain of Magic Resistance (+5 Mind and Body, once per character by a player bit),
  the five-stone cairn (q-c24.cairn), Mirabeth's statue, the falls' lip chest, the Octopod Falls over the east rim,
  the Rimward crags.
- **The skerries' lures**: the smuggler's strongbox (West Skerry) and a genie's lamp (East Skerry), by water walking or
  flight.
- **The coven** (placed, A2's `xeen_coven` relations: hostile, friendly after `q-d22.joined` 113449): the Circle 8
  (Witches x5, Coven Witches x2, the Coven Mother), the reeds 6 (x4, x2); hidden by the load event once
  `XeenQuests.can("q-d22.coven_gone")` (the Head Witch dead, 113447); the Circle's chest and skulls stay.
- **The octopods** (D-200, U-19, 2026-11-26: "octopus should act like e.g. water elemental mm6 or the sea monster in
  mm6 in hermits isle"): five placed water monsters (Octopod x3, Great Octopod x2) in the two deep basins, MM6's sea
  serpents' kind (A2's rows 11470/11471: classic AI, `Fly N`, the `Swimmer` kind walks on water, the Water ink; no
  MM9 swimmer profile). They are hostile by their relation `short` (2,560), with no Aggressor bit (the sketch's
  `hostile: true` dropped: the bit makes a monster engaged from the start, noticing a party at the 10,240 engagement
  range). Each is a post on a home radius `leash: 1500` (`OCTOPOD_LEASH`, enforced last on every step), so it never
  leaves its basin. gen.py stops if a home radius comes within 500 of land, if the leash plus 2,560 reaches the jetty,
  the Isle landing or the waterfront (`OCTOPOD_NOTICE`; every home is 2,800 or more), or if a Paralyze Octopod's home
  less its leash is within 5,888 of an arrival (`D87_RANGE`). Homes: group 3 Octopod (59, 63) (moved from (60, 64)
  for D-87), group 4 Great Octopod (65, 59.5), group 5 Octopod (86, 65.5), group 6 Octopod (93.5, 66.5), group 7
  Great Octopod (85, 74) (groups 4 and 5 swapped their rows, so the count and Act IV's XP stay). A party on a basin's
  beach within 2,560 of an octopod (the west basin's north beach at (66.5, 55.5) is 2,190 from group 4; the East
  Skerry's south-west beach 2,300 from group 7) is noticed. The octopod comes to its leash edge and shoots its ink,
  about 45 a shot every 2 to 3 s: a level-50 solo Knight (290) is down to 82 after 15 s. Once hit or engaged, it keeps
  the engagement range and shoots up to 5,120. Lakeside's jetty and waterfront stay quiet
  (`tests/scenarios/xeen/d4_octopods_shore.yml`).
- Atmosphere `view_distance: 1.6` (the scene's `rendering.view_distance_scale`): the keep reads from the jetty's end
  with the default view distance setting (session 11, `output/studio_cal/d4/pics/sheet_s11.jpg`). Frame cost at the
  signature pose, 1.6 against a scratch 1.0 (visible runs back to back, relative: other sessions were running): both
  held the 120 Hz cap; draws 161 against 132, triangles 319k against 247k, world render CPU 723 against 696 us, GPU
  p50 2.2 against 2.4 ms (noise); `output/studio_cal/d4/perf/`.
- Sky `xeendark1` and A3's `Xeen.applyDarksideSky()` on load; terrain entry `xeen_d4.odm` in the world's
  terrain_materials/world.yml (grass and dirt shades, the lead's darkrock slope).

## Monsters (A2's rows)

Row 9111 is A2's and not in the world yet; the tests mount `output/studio_cal/d4/rows` (the world's map_stats with
this row). The slots, as project.yml: 1 Xeen Mountain Gargoyle Dif 2 [2, 3] (weight 30), 2 Xeen Roc Dif 1 [1, 3]
(55), 3 Xeen Coven Dif 1 [2, 3] (15; no markers, the coven is placed). Markers: E1 gargoyles 13 (slot 1), E2 uplands
rocs 12, E3 Rimward rocs 8 (stretched north to the falls' lip: D-36), E5 heath rocs 14 (slot 2).

## Measured

| Figure | Target | Built |
| --- | --- | --- |
| Hostiles at load | 120 (D-36: 119.5 accepted) | 119.5: markers 47 (13 x 2.5 + 34 x 2) = 100.5, placed 19 (14 coven, 5 octopods) |
| POIs (D-20 census) | at most 35 | 33 |
| Outdoor chests | at most 10 | 10 |
| Encounter areas (4,096 squared) | 6-30 each | E1 10.2, E2 13.1, E3 6.5, E5 9.0 |
| First fight from D3's arrival | 2,000-6,000 | 5,317 (Rimward rocs) |
| Town buffer | 2,500 | nearest hostile to a town door 5,257; square 10,240, dock 7,384, Isle landing 6,734 |
| 6,000 rule; wild land | none over 6,000; at most 0.16 | farthest 5,989 at (39, 83); 0.143 |
| Relief in the box | at least 2,500 | 1,056-4,160 (3,104) |
| Quiet central land | at least 1/3 | 0.65 |
| Roads | 1-4 % | 0.7 % road tiles (the lanes are dirt ground lines) |
| Model triangles | | 7,322 (none hidden at load) |
| Entities | | 1,079 decorations, 35 models |

## Tests

- Audit (`oymap audit ... --reach --solve --dressing --lights --doors --textures`, oymap 22:38:19, session 11,
  run/audit_s11_all.txt): 0 errors; 2 warnings (the studio's waterfall faces, `thing:octopod_falls`, kept: the
  studio's own sheet over its bank).
- Walk (`playtest.yml`, 338 steps, `gen_walk.py`; run/walk_s11_f1.log, walk_s11_f2.log on assets_dev after the
  22:52 install, session 11): the Isle's door refused then sealed with the key, the Isle Ferry's
  house screen; every Lakeside house door (closed texts, the Yachts' screen); the riddle wrong ("Begone") then right
  ("Correct", 113442) and the guild open; the back stair, the mirror, the shaft's question, Skiff's boat, Naomi; the
  town road to Well Fork and up the Sandcaster road over the brow to the D3 arrival; the gatehouse's refusal; the bat
  storm's knock-down (Fly cast, flown up from the crag top, set down on the north shore, Fly gone), the gate's griffin
  question after m25.done (DD-14 sealed); the obelisk (dark_4), Leafpoint, Ector, the woodpile, the lair path, DD-23's
  question into DD-23 at `entrance:d4_mouth` and out by its mouth to `entrance:dd23_lair`, Slibo, both fountains, the cairn, Mirabeth, a skull, the west
  road's sign; off the south edge to D3 and back (A2's travel row landed): D4's south start.
- Hostility (`playtest_hostility.yml`, rewritten for D-200 by `gen_hostility_d4.py`): the coven hostile at load,
  the octopods hostile, over water and within their leash (+150) after 20 s each, with the party at the start, on
  the waterfront (no ink there: no attack_ranged in the decision trace), on the East Skerry's south-west beach (the
  nearest octopod, group 7, attacks from the water: 8 attack_ranged on the party in 20 s, and stays at its leash
  edge, 1,502) and in the water (`octo_check.py`: 0 out of water or leash). Leafpoint, Slibo and the peasants are
  peaceful. Joined: the coven is peaceful. The Head Witch dead: both groups hidden on load. The Circle's chest opens.
- D-200's shore proof (`tests/scenarios/xeen/d4_octopods_shore.yml`, solo level 50, no clear_hostiles): 30 s at the
  jetty's end unhurt with no shot; 15 s on the west basin's north beach: group 4's Great Octopod to its leash edge
  (1,500), 6 attack_ranged on the party, 290 down to 82, the only hostile within 5,120; all five over water within
  their leash.

## Texture fit exceptions

- None (0 `textures.*` findings). The gatehouse has no arrow slits: `xkarrow` laid on its towers repeated across a
  face (an error); slits wait for a `fit: true` pass.

## Dressing exceptions

- None.

## Town feel exceptions

`town_feel.py --small` (Lakeside holds five services in town; the Isle Ferry, 4667, stands on the Isle), measured on a
scratch build with the coven's doors open (`D4_TOWN_OPEN=1 gen.py <scratch briefs>`: the installed doors ask Q-D22 and
the guild's riddle first, so the checker sees no service; `output/studio_cal/d4/tf/town_feel--small.txt`). Session 10
fixed two figures: trees in town 0 (six trees beside or behind houses, `TOWN_TREES`) and road or dirt 1.0 (grass yards,
`TOWN_YARDS`). Kept:
- Straight road run, longest 1,536 (shipped 3,072-5,655): no street runs through Lakeside; the forest track and the
  Sandcaster road end at the paved square, and the checker sees road only within 1,536 of a door.
- Service to nearest service, median 2,878 (shipped up to 2,424): the five services stand round a square 10 by 6 cells
  (guild west, smithy east, tavern and temple south, the yachts north on the shore), as the L1 plan.
- Boats rank from centre 0.07 (shipped 0.68-1.0): the town is built round its ferry jetty, which is its middle (D-12.1,
  D-36's signature view from the jetty's end); the shore is the town's north side.
- Wild group to nearest group, median 3,444 (shipped up to 2,433) and spacing variation 0.26 (shipped 0.46 up): 119.5
  hostiles (D-36) on a map that is half lake, rim and snowfield, their groups spread by the 6,000 rule.

## Open items

- Lit windows at night: `hkm3elw`'s surface maps apply since merge point 18: with Surface materials on the keep's
  and towers' windows glow at night and read from the jetty's end; off, they stay dark
  (`output/studio_cal/d4/pics/sheet_s11_mat.jpg`, `pics/s11_sig_night_crop.jpg`). The beacon fires are too small at
  17,600.
- A2: map_stats row 9111 (the D3-D4 travel row has landed; D4-D5 later).
- Haze: the tours' random weather (the lead confirmed); every tour shot now runs `sky weather 0` and `weather clear`
  (pics/sheet_final3.jpg reads clearly). The map has no `fog` line.
- A8: DD-12, DD-14, DD-20 (the doors go live by themselves on a rebuild once each BLV is installed with its map_stats
  row and lists its entrance). DD-23 is live.
- The ground: a classic map holds dirt and two more grounds: grass and snow; the desert heath is dirt.

## Doors and arrivals for the other lanes

| Door | Entrance inside | Outside return point (x, y, z, facing) |
| --- | --- | --- |
| DD-12 ruined tower (two leaves, lost_souls_key) | `entrance:d4_isle` | entrance:dd12_door (4096, -3072, 1376) facing 1536 (south) |
| DD-20 guild back stair hatch (members) | `entrance:d4_guild` | entrance:dd20_guild (-1024, -13312, 1120) facing 1024 (west, beside the hatch) |
| DD-20 guild trapdoor (wrong answer) | `entrance:d4_trapdoor` | one way (no return) |
| DD-20 shaft by the jetty | `entrance:d4_shaft` | entrance:dd20_shaft (3072, -9728, 1120) facing 512 (north) |
| DD-23 cave mouth | `entrance:d4_mouth` | entrance:dd23_lair (-9216, 10752, 2304) facing 1536 (south) |
| Blackfang's gate (griffin after m25.done) | `entrance:d4_griffin` | entrance:dd14_griffin (6144, 5120, 1216) facing 1024 (west), cell (76, 54) |

Town arrivals (A4): `lakeside_square` (4608, -13312, 1120) facing 512; `lakeside_dock` (4608, -9216, 1056) facing
1536; `isle_landing` (4096, -4096, 1120) facing 512. D3's north edge into D4 (A5): `entrance:south_road`
(12288, -20992, 2112) facing 512 (cell 88, 105).

## Session 12 (A6, 2026-11-20, merge point 20)

- **DD-20 live** (A8 installed it with `entrance:d4_guild`, `d4_shaft`, `d4_trapdoor`): the back stair, the shaft and
  the wrong riddle answer (trapdoor) move into DD-20; DD-20's exits land at (-1024, -13312) facing west (the back
  stair) and (3072, -9728) facing north (the shaft). The plan's `entrance:dd20_guild` faces west, as the sketch and
  DD-20's exit. The walk goes in and out three times (trapdoor -> ladder, back stair -> cellar door, shaft -> ladder).
  DD-12 and DD-14 still sealed. Installed with bake 23:52:55; audit 0 errors (the 2 waterfall warnings); stage walk
  369 steps and hostility pass; walk 2/2 and hostility on assets_dev.
- **Rim glow `below_deg` 1.5** (D-36, merge point 20 lights the horizon cloud banks): captures
  `output/studio_cal/a6/rim/sheet_d4_v4.jpg`, `crop_d4_v4_vs_v3.jpg` (night v3 above, v4 middle, day below).

- Session 12 (2026-11-21): AU's outdoor bed (E9) from `output/studio_cal/a6/beds/d4.yml`, read by gen.py; reinstalled with
  bake, walk 2/2 and hostility on assets_dev.

## D-58: the fall from D7 (A6, 2026-11-21, sixteenth session)

`entrance:d7_fall` at (5632, -13312, 1120), facing west, on Lakeside's square by the ferry dock and the mirror (zone E1-F2, `d7_ef12`). Checked against the installed map (`output/studio_cal/a6/s16/fall_points.py`): a whole flat cell (the 3 x 3 nodes level), no water or lava, no decoration or wall within 256, no hostile with a ranged attack within 5,888 (placed actors and spawn markers with their slot monsters). The entrance is kind `both` in the plan only so that it does not become the party start (the studio takes the first `arrival`). The point does not change the map or the scene, but the rebuild also took A2's/S's new actor sizes for the octopods (11470: radius 60, height 80), so D4 was reinstalled with a new bake (a6/bake_xeen_d4_*, s16); walk and hostility rerun from assets_dev. The fall tests (D-54's shape) run from D7.

## The small lamps (A6, 2026-11-21, twenty-seventh session)

- The seat's lamp (event 73, `lamp_seat_rubbed`) and the skerry's (event 95, `lamp_skerry_rubbed`) pay once by a named
  map variable (was the silent `once`); a second rub says "The lamp is cold. Its genie has gone back in for good." and
  "The lamp is cold and still wet. Its genie has gone." The walk rubs each twice (gold once, the line the second time).

## D-87: ranged disablers (A6, 2026-11-21, thirty-first session)

- The only ranged disablers are the three placed Octopods (Paralyze by missile, in the water). Since D-200 they
  move and shoot, so D-87 measures a leashed placement at its home distance less its leash (`common/d85.py`,
  `tools/xeen/check_arrivals.py`). Measured that way, the old homes failed: groups 3 and 4 were 4,797 from the start
  (the griffin perch), 4,961 from DD-12's door and 5,835 from the Isle landing. Groups 4 and 5 swapped rows (tier A
  to (86, 65.5), tier B to (65, 59.5)), and group 3's home moved from (60, 64) to (59, 63) in its basin. Now the
  Paralyze Octopods' nearest approaches are 6,029 (group 5) and 6,060 (group 3) from DD-12's door, 6,303 from the
  start and 6,403 from the Isle landing (group 5): `d85.py` DIS 0. The Great Octopods (Poison3, damage only) are D-85 report lines,
  not D-87 errors: group 4 is 4,797 from the start and 4,961 from DD-12's door, group 7 5,234 from the Isle landing
  and 5,884 from the dock. None notices a party there (leash + 2,560 is short of all four).
- Kept by D-87: Leafpoint 5,391 (the reed witches: Lightning Bolt and Psychic Shock, damage only).

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt on merge point 41, installed with its bake 01:20. F16: the sewer shaft and the gargoyles' lair lose their Yes/No (rows 5055, 5058; q-d15.lair_door's look is the row); the griffin's offer stays a choice (D-90 1(d)) with the buttons 'Fly in' / 'Stay here' and a direct move. F10: the heath roc (31.5, 92.5) to the west edge (21.5, 64): 592 -> 338 tiles. Walk, hostility, daily pass; audits 0; plants installed (F5).

- 2026-11-22 fixup (fourth orchestrator, for A6): event 53 "The boat's locker" no longer asks "Search the boat?
  (Yes/No)" (orchestrator decision, as X7's den chest): the chest opens at once and the status bar reads "You search
  the beached boat and open its locker." (`gen.py` `thing:boat_locker` `effects`, backup
  `output/xeen_fixups/d4/gen.py.before`). Installed with its bake 03:05:43; L4 and assets_dev audit 0 errors / 8
  warnings, doors 0, empty zones pass, D-85 as before (1 FAIL, `entrance:dd23_lair`, unchanged), props 6 overhang
  warnings; walk, hostility and daily pass from assets_dev. No other Yes/No chest is left in the Xeen world (the
  combination and password chests of DD-03 and DD-06 are puzzles).

## Rim rebuild (2026-11-23, agent xeen-rimmap-c: U-12, D-106, D-109, D-112, D-113)

- The rim sea is the void (`terrain.void [[0, 0, 127, 23], [104, 24, 127, 127]]`), 54 hull pieces, the corner at
  (104, 24), 18 return points; Octopod Falls' lip (104, 67) down the spillway, foot -2,400; the bright face's glow over
  the void (`cap/d4_after/12`, `15`, `19`).
- The hull pieces beside the spillway stand at the banks' height and on the hills in steps (`cap/d4_after/02`, `07`,
  `12`): the kit's way (as X1), left.
- Checks: audit 0 errors (6 warnings `support.overhang` dec60 set pieces, was 8), `void.occupied` 0, doors, walls,
  town_fit 0, empty zones, props, check_wild clean, D-85 0 / DIS 0. `gate_check.py` here is a stale copy of D1's
  (reads `xeen_d1.scene.yml`, calls D1's `in_gate_lane`): not run.
- Tests: walk x2 and hostility pass.
- Generated twice (the rescue's return points from the first build's land, `XEEN_WILD_MAPS`), built, villagers placed, recorded (`agent:xeen-rimmap-c`), checked in a private hard-link root, installed with its bake, terrain weights, the minimap re-rendered and its void painted (`tools/xeen/void_minimap.py`). Scripts `output/xeen_rimmap_c/build.sh`, `install.sh`, `tests.sh`, `tours.py`; logs `output/xeen_rimmap_c/run_<key>/`; captures `output/xeen_rimmap_c/cap/<key>_after/` (day and night, against `output/xeen_rim/before/<key>/`).

## Final outdoor round (2026-11-24, `xeen-fb3-final-dark`)

- `snow_bridge` meets the land at both ends (the studio's bridge-end rule): town_fit's 2 `bridges.step` errors gone.
- D-120: the skerry strongbox and the skerry genie lamp are kept in `tools/xeen/check_reach.yml` (`water walk or
  fly`, Act IV); `tests/scenarios/xeen/d4_skerry_water_walk.yml` walks to the strongbox on Water Walk (and fails
  without it: the party is hurt). The five octopods (groups 3-7, water monsters on a leash, D-200) are kept groups there.
- A Lakeside villager stood on the graveyard isle (the ferry's house is there): `villagers.yml` Lakeside `avoid`
  the isle; spots re-placed.
- The Fountain of Magic Resistance at `WARDING_WELL` (84.75, 95.5) west of Well Fork: at (88.6, 97.4) it hung 43 over
  the brow's slope (`things.overhang`).
- Classic kit `fit_maps`. Checks: town_fit 0 (kept: Blackfang's beacons), check_reach 0 (kept as above), door 0, wall
  0, check_wild 0, D-85 0. check_faces 1 (the isle tower crown's open edge, old). Audit: 1
  `textures.feature_repeated` xvswin (model 3): c7's kit. Playtests: walk 426, hostility 87 pass.

## Hull collision rebuild, D-136's Druid (2026-11-24, `xeen-fb3-hull`)

- The world's hull is solid now (`collision: model`; oymap `oymap_1944` pinned by the orchestrator).
- D-136 named "Druid 30" (group 47, 1,227 from `entrance:dd20_guild`) to move. It is one of Lakeside's D-96
  villagers (row 517, "the coven's robed women"): the map's load event `evt:studio_relations` makes rows 349, 364,
  517 and 598 friendly and `studio_peaceful_groups` clears group 47's hostile bit, so it neither fights nor casts at
  the party. The first-fight check read only the world's relations: `tools/xeen/check_arrivals.py` now leaves out
  placed actors whose row the map's own onLoad Lua makes friendly (`World.map_friendly`). Not moved (the spots file is
  generated by `villagers.py --place`); D-85 0 errors.
