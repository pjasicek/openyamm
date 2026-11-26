# FD-04 Dragon Tower and the Dungeon of Death, L4 (lane A7, seventeenth session, 2026-11-21)

Map 9182, class M, on X7, `xeen_fd04.blv`, music 13, `world: xeen`. Briefs: `output/studio_cal/a7/phase6_common.md`
(and phases 5, 4, 3), the FD-04 section of `output/studio_cal/a7/phase6_maps.md`, D-57
(`devdocs/xeen/mockups/act6_a7_decisions.md`), the graph `devdocs/xeen/mockups/act6_graphs/fd04.graph.yml`.

## How to rebuild

- Every project file (L1-L4) is written by `output/studio_cal/fd04/tools/gen.py` (`--levels` writes L1-L3). Never
  hand-edit them; diff L4 against `L4/.oymap/last` before rerunning after a hand edit. Then
  `oymap record devdocs/xeen/briefs/fd04/L4 --author agent:xeen-a7-fd04 --label "..."`.
- `bash output/studio_cal/fd04/cycle.sh`: gen, fmt, validate and build against the scratch root
  `output/studio_cal/fd04/root` (it holds the two new textures), install into that root, audit (--reach --solve).
- `python3 output/studio_cal/fd04/tools/gen_tests.py` writes the nine playtests from `ids.lock.yml` and the built
  scene's actor order (run it after a build that may move ids).
- Playtests: `ROOT=$PWD/output/studio_cal/fd04/root KEY=fd04 TESTS="playtest_gongs playtest_crossword
  playtest_terminal playtest_alister playtest_shrine playtest_dragons playtest_exit playtest_roof playtest_hostility"
  N=4 bash output/studio_cal/a7/xfour.sh` (logs in `output/studio_cal/fd04/a7_xrun/`).
- The nest's eggs are S's `xeen_dragonegg` (row 4048, `S_EGG` in gen.py, twenty-first session): three on the eggs'
  rock, one hidden by `evt:egg` and on load with 118146. The lizard is S's `xeen_lizard` (row 4049, `S_LIZARD`,
  twenty-second session): placed hidden on Alister's spot facing 0 and shown by `evt:alister_gone` and its load event.

## What was built

One BLV. x east, y north, z 0 = the gate hall's floor (X7's crag top 2,600).

**The tower** (four floors 1,280 apart, z 0 / 1,280 / 2,560 / 3,840, inside a square of 3,072): the stair winds up in
the wall as three ramps (path rooms 288 wide and 288 high, slope about 0.5): the first up the west side from the
stair's foot (floor 0, south-west) to the first landing (north-west), the second along the north side to the second
landing (north-east), the third down the east side to the third landing (south-east). Every opening between a
dragon hall and a landing, a ramp, an alcove or a gallery is 256 x 288 (D-32, D-57 Q29); the three tower doors
(dormitory, tome room, roof stair) are 256 x 256.

- Floor 0: the gate hall (arrival `entrance:x7_gate`, Alister's alcove west, the stair's foot south-west, Sandro's
  black iron door north at the head of the cellar well); a low passage east that turns north into the scorched hall
  (two Acid Dragons at its north end, about 1,450 from its opening; the opening is out of sight of the gate).
- Floor 1: the ring hall round a pier (Acid 4, Fire 2), the dormitory (beds, a chest; a door to the landing and a low
  opening to the hall: the loop), the bone alcove (q-f1.note_fraud, q-f1.note_forever).
- Floor 2: the nest round a sunk bowl of black rock with the eggs' rock (q-f1.egg; Fire 4, Frost 2), the hatchery
  (Fire 2, Frost 2; q-f1.note_balls; the loop), the last climber (q-f1.note_eye, the potion q-f1.endurance, a chest).
- Floor 3: the high hall (Frost 2, Phase 3), a low arch into the crown (2,048 high: the Energy Dragon and two Phase
  Dragons), the Wyrm's gallery (the Wyrm's Hall's door, house 4853; the loop), the tome room (q-f1.tome, a bed, a
  chest), the roof stair (12 steps to its head at 4,224 under an open hatch, `open_sky` xeen_cloud_sea).

**The Dungeon of Death** (north of the tower and under it):

- The cellar well: Sandro's door at its head (z 0), 32 steps down to the crossword (z -1,024).
- The crossword (3,072 x 2,048, 768 high, dark slate floor): twelve word strips of pale cells (`xfgrid`, cells of 128)
  that cross where their letters match (CORAK x CASTLEVIEW at A, SANDCASTER x CASTLEVIEW at T, NECROPOLIS x
  CASTLEVIEW at I and x MIRROR at R; KALINDRA x WINTERKILL at N, SCEPTER x WINTERKILL at R and x SPHINX at P, VAMPIRE x
  XEEN at E; ALAMAR stands alone); gen.py checks every crossing letter, that no floor is closed off and that no plates
  touch only at a corner. Twelve clue plaques (FD-03's `xdplaque` reused): across clues on the west or east wall at
  their rows, down clues on the north or south wall at their columns. A right answer lights the word: its cells'
  plates take `xfword` and a glow light over it comes on (on every load with its qbit). The descent's gate (north) is
  A3's q-f2.crossword.
- The descent (24 steps down to z -1,792); Sandro's halls: the welcome hall ("Welcome" on the way in), Do Not Disturb
  (four coffins, q-f2.coffin; a chest), the ballroom (double doors gnecdr1l/gnecdr1r from the welcome hall; dead
  chandeliers), two game rooms, the Shrines of Lesser Evil (Minor, Lesser) and of Great Evil (Great, Ultimate:
  destructibles with their questions), the Throne of the Dead (thrones on a dais, Sandro's note q-f2.note); the bone
  stair (24 steps down to z -2,560).
- The gong hall: four gongs (`xngong`, two on each side wall, at y 8992 and 9568, 32 clear of the east wall's doorway to
  the fountain either side; merge point 30's panel warning), a lamp-glow under each (light, `on: false`) lit when
  it is rung (map variables gong1-gong4, kept by the map's save and relit by load events); the lever by the iron
  shutter: before the four, "The lever won't budge." and the voice (one window); after them the shutter rises for good
  (118144). The chest: opened before the shutter with any gong rung, it clears the four and a timer a second later
  puts the lamps out with A3's q-f2.gongs_reset ("The gongs fall silent."). The fountain (heals, any time).
- Maintenance (papers), the control room (the main terminal: A3's q-f2.terminal / terminal_wrong; a computer), the
  Lord Xeen Machine's hall: the engine (a destructible; "Lord Xeen Machine. Destroy?") among four cores (XD-19's core
  textures) with their terminals; broken: q-f2.machine, a shake, the cores' glows out and their faces dark, the
  machine's sound off; dark on every load with 118145.

**Alister** (D-57 Q27): `monster:alister` (A2's row 11923, A4's npc 5705, `hostile: false`, group 60, immobile) in the
alcove; unkillable (`evt.SetMm9ActorCanReceiveDamage`, load); A3's topic "Dragon egg" takes the egg and sets 118147;
a timer (every second, not while the talk is open) hides group 60 the second after the talk closes, in the same
visit; hidden on every load with 118147; the lizard he became (`deco:lizard`, S's `xeen_lizard`) is shown in his place.

## Counts

- 39 rooms, 39 sectors, 64.9 M units² of floor (`oymap metrics`; M's band 20-45 sectors, 30-90 M units²).
- 60 monsters (D-57 Q22): Acid 11641 x6, Fire 11642 x8, Frost 11643 x6, Phase 11652 x5, Energy Dragon 11653 x1
  (tower 26); Lich Lord 11282 x10, Power Lich 11284 x6, Skeletal Lich 11285 x8, Doom Knight 11152 x4, Autobot 11612 x6
  (dungeon 34); **100,224 per member** (gen.py's sum of L(L+10) x count / 4). By floor: 0: 2, 1: 6, 2: 10, 3: 8;
  -1: 2, -2: 20, -3: 12. Plus Alister (peaceful, not counted).
- 5 chests T6 (dormitory, last climber, tome room, crypt, gong hall). 11 door records: 9 doors (the ballroom's pair
  is two leaves) and the lever.
- Textures: 42 distinct in the built map (cap 45): 6d04's vlcwl2, vlcwl4, vlcflore, vlcgnrc1, vlcdora, vlcceila;
  d19's gnecwal1, gnecwal3, gnecflr, gnecclg2, gn_mtl03, tws1f, gnecdr1l/gnecdr1r, gnecdr2, gnecdr3, gnecdr6,
  gnecstpt, t1beds2, t1books1, trim9_32; sci-fi.blv's swll4dk, swfloor2b, swceilf, swdoora, swpnl, trekscrn; XD-19's
  xcorefire/xcorewater/xcoreair/xcoreearth; XD-03's xngong; FD-03's xdplaque; the shipped chest faces; new: xfgrid,
  xfword.

## New textures (for A6's registry; masters for `assets_source/worlds/xeen/textures_x4/`)

Made by Codex through `level_generation/textures_xeen/xtex.py --project output/studio_cal/fd04/tex` (specs.yml,
raw/, finished/, v1 of each, `picture` kind), installed into `output/studio_cal/fd04/root` only:
- `xfgrid` (128 x 128, a floor cell): a pale cream marble slab with faint grey veins in a thin bevelled dark-bronze
  border (gain 0.66, luma 147).
- `xfword` (128 x 128): the same cell glowing warm amber from inside (gain 0.84, luma 154).

## Map rows and test rows

A2's rows had all landed when the build started (03:40): map 9182 (encounter 0, no slots, treasure 6, music 13, lock
20, trap 10, perception 20), monsters 11284/11285 (ordinary tiers), 11923 Alister; items 12375, 12376. A4's house 4853
and npc 5705 landed at about 04:40 (relay): the root's tables were refreshed (`refresh_tables.py`). **No test rows**.

## Map qbits (118130-118149)

118130 Sandro's door open; 118131-118142 the twelve words (1a, 5a, 6a, 13a, 21a, 24a, 40a, 44d, 45d, 47d, 76d, 77d);
118143 crossword done; 118144 shutter up; 118145 machine broken; 118146 egg taken; 118147 Alister gone; 118148 the
Ultimate shrine broken; 118149 the code entered (all named in A3's q-f1/q-f2). Map variables: alister_hidden, gong1-4,
reset_pending.

## Original lines

- "Exit Dragon Tower?" (dark/aazex117:4): the gate's exit preset meaning.
- "Bed" / "Nothing here." (aazex118:0-1, aazex120:0-1): the beds.
- "Welcome", "Ballroom", "Game Room", "Do Not Disturb", "Coffin" (aazex122:0-5): signs on the way in, the crypt door's
  title, the coffins' hover.
- "Throne of the Dead", "The Master's Throne", "You feel strange." (aazex122:8-10).
- "Shrine of Minor/Lesser/Great Evil.  Destroy?" (aazex122:17, :15, :13); the Ultimate's with A3's tell (:11).
- "Gong", "Lever", "The lever won't budge.", "A voice booms: Ring the four gongs and then pull the lever. Touch any
  treasure and you'll have to start over!" (aazex123:0-3); "Fountain", "Ahh, refreshing!" (aazex123:4-5).
- "Lord Xeen Machine. Destroy?" (aazex124:0); "Table", "You find some papers that tell of the World of Xeen maintenance
  schedules..." (:1-2); "A message flashes on the terminal screen: Fire/Water/Air/Earth Core Operational" (:3-6);
  "Main Terminal / Enter Code" (:7); "Computer" (:8); "Maintenance", "Control Room" (:12-13).
- Crossword prompts "N Across/Down: <clue>. Answer?" (aazex121:11-188 as A3's hooks give them).
- New map lines (no source text): the arrival "The Dragon Tower: warm black stone, and somewhere far above, something
  very large breathing."; the gongs' "The gong rings, and the lamp under it flares up." / "The gong rings again. Its
  lamp is already lit."; the lever's "The lever moves. Somewhere in the wall chains run, and the iron shutter rises." /
  "The lever is down."; "The shrine lies broken."; the computer's "Its lights blink in an order you cannot follow.";
  the core terminals' "... Core Offline"; the roof hatch's title "Climb onto the Dragon Clouds" and its Yes/No
  "Climb up through the hatch?" (D-66, nineteenth session).

## Exceptions

- Audit warning `textures.family_switch` (swll4dk beside trekscrn): the main terminal's screen on the control room's
  wall, meant.
- Audit `question.answer` warnings (126 since the nineteenth session, one per accepted answer variant: each name with
  and without "The ", a trailing full stop, no or a curly apostrophe, Scepter or Sceptre): the crossword's twelve answers are names the
  main story gives before FD-04 opens (D-57 Q25, A3's q-f2 riddles block); "Computer" is FD-03's heads' (Q35).
- Dressing: the gong hall's chest stands by the north wall (the source's "middle of the floor" kept to the wall rule).

## Blocked on

- S: the Energy Dragon's, Power Lich's and Skeletal Lich's own skins (D-57 Q30). Alister's body (`Xeen Alister`,
  `xeen_cle` with the druid skin `xcle_h`, bound by descriptor to row 11923; S's eleventh session), the lizard and the
  eggs are in.
- A5: X7's `door:fd04` into `entrance:x7_gate` (with the key check q-f1.tower_door) and confirming the return clears the
  gate's leaves; X9's door in the dragon-head rock to `entrance:x9_clouds` (X9's evt:fd04_door is sealed "(Not open
  yet.)" until FD-04 installs).
- A6: register xfgrid, xfword; the FD-04 family lines (6d04 tower, d19 halls, sci-fi machine floor).

## DECIDE (cheaper-to-reverse option taken)

- The spiral stair is three walked ramps (slope about 0.5) in the tower's wall, not steps: one room each, no dragon
  can enter them (288 high).
- The crossword's clues are clicked plaques on the walls (not step plates on the cells): walking the hall never
  prompts; the cells are the floor's word strips. ALAMAR crosses nothing (D-57: the strips need not form a true grid).
- Sandro's door is the door at the head of the cellar stair in the gate hall's north wall (the "cellar well").
- The Ultimate shrine's "falling dust" is the shake and a stone sound only (D-63 13 accepts it; a `smoke` puff is
  optional polish); the throw that follows is `{leave: exit:x7_gate}`, at once, no window (D-63 13, D-24).

## Measurements and checks

- Build (`output/studio_cal/fd04/build.log`): 0 warnings. `fmt --check` clean; L1-L4 validate clean.
- Audit (`output/studio_cal/fd04/audit.txt`, --reach --solve, dressing and lights on): **0 errors**; warnings:
  `question.answer` 56 and `textures.family_switch` 1 (see Exceptions); infos: click.silent 4 (the descent gate in
  qbit combinations that cannot occur), state.never_read 2 (AmbientSound5, A3's fd04_goober).
- `playtest_exit.yml`: the leave window's OK lands on X7 at **(-17920, 16384, 2593) facing 1536** (entrance:fd04_door).
- `playtest_roof.yml`: from the roof stair's head (-1312, 608, 4224) the hatch asks the map's own Yes/No (D-66; X9 is a
  BLV, so no leave window): No stays, Yes lands on X9 at **(20352, 17280, 2048) facing 512** (entrance:fd04_roof).
- `playtest_dragons.yml`: after 30 s with the party at each hall's low opening every dragon is still in its own hall on
  its floor; they crowd the openings (nest dragons at (644, 900, 2560) by the landing's opening, the crown's at
  (900, 600, 3840) by the gallery's, the high hall's at (196, -280, 3840) by the landing's) and none passes; none in
  the stair's ring.
- `playtest_hostility.yml`: nothing targets the party for 10 s at entrance:x7_gate nor at entrance:x9_clouds; all 60
  hostile at their exact counts, Alister peaceful; spawned dungeon monsters never fight each other.
- `playtest_alister.yml`: struck twenty times, Alister is alive and peaceful; three eggs shown in the nest; the egg
  once (118146, the second click "Two eggs are left"; the third egg hidden, two shown); his paying talk takes it;
  hidden two seconds after the talk closes (same visit); hidden after a reload, two eggs still shown.
- `playtest_gongs.yml`, `playtest_crossword.yml`, `playtest_terminal.yml` (Goober, SUPER Goober, then "cOmPuTeR" pays
  2,000 once), `playtest_shrine.yml` (the fountain heals; Minor Evil +1,000; the Ultimate's tell, No, Yes: out to X7 at
  entrance:fd04_door at once with no window (D-63 13), nobody dead, 118148).
- **Every playtest 4 of 4** from the scratch root (`output/studio_cal/fd04/four_final.out`, logs
  `output/studio_cal/fd04/a7_xrun/<test>_<n>.log`): gongs 51/51, crossword 122/122, terminal 33/33, alister 35/35,
  shrine 31/31, dragons 105/105, exit 15/15, roof 15/15, hostility 38/38, each run 1-4.
- Headless runs: the root's `worlds/xeen/world.yml` is a real copy of assets_dev's without the `openAirMaps` entries
  `xeen_d7.blv`, `xeen_p1.blv` .. `xeen_p4.blv` (named but not installed: FD-03's finding); the lead keeps or drops it.

## What the user should look at

- Pictures: `output/studio_cal/fd04/shots/` (contact sheets `sheet1.jpg`, `sheet2.jpg`), tour `shots.yml`.
- The crossword from the cellar stair's foot: the pale word strips on the slate, four words lit amber (xfword and
  their glows); the cells' bronze borders read as a grid.
- The roof stair's hatch shows its ceiling texture, not the cloud sky, in the unbaked tour (shot 08): to check after
  the lead's bake (FD-03's hatch is the same pattern).
- The liches, Energy Dragon and Alister wear stand-in looks until S's skins land.
- Dark rooms are only the missing bake.

## Installed (2026-11-21, lane A7 lead, seventeenth session)

- `xfgrid`, `xfword` installed in `assets_dev` (`xtex.py install --root assets_dev --world xeen`; masters in
  `assets_source/worlds/xeen/textures_x4/`); root tables refreshed, rebuilt with merge point 25's oymap (build warnings
  0), installed with its bake 04:52:29 (`install_baked.sh`, profile `tools/lighting/baked_indoors/profiles/xeen_fd04.yml`),
  stale bakes 0. Audit from `assets_dev` 0 errors, 56 warnings (the kept `question.answer` lines;
  `output/studio_cal/fd04/audit_assets_dev.txt`). **36/36 from `assets_dev`** (gongs 51, crossword 122, terminal 33,
  alister 35, shrine 31, dragons 105, exit 15, roof 15, hostility 38; `output/studio_cal/a7/s17_fd04_four.out`).
- Baked look up through the roof hatch: the cloud sky shows (`output/studio_cal/a7/s17_look/hatches.jpg`, lower row;
  the unbaked tour's shot 08 looked at the shaft's walls, not the opening).
- Open: S's skins (Energy Dragon, Power and Skeletal Lich), Alister's body, the lizard and egg decorations
  (`S_LIZARD` / `S_EGG` in gen.py); A5's X7 `door:fd04` (key check) and X9's door to `entrance:x9_clouds`.

## Eighteenth session (2026-11-21, lane A7 lead)

- D-63 13: the Ultimate shrine's throw is `{leave: exit:x7_gate}` (at once, no window); `playtest_shrine` lands on X7 at entrance:fd04_door with no window and nobody dead. The lizard and eggs: still no decoration from S (`worlds/xeen/models/` and the engine decorations checked at 05:40).
- Installed with its bake 05:19:26 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 56 warnings (the 55 kept crossword `question.answer` and the family switch, as before) (`output/studio_cal/a7/s18/audit/fd04.txt`); **36/36 from `assets_dev`** (gongs 51, crossword 122, terminal 33, alister 35, shrine 29, dragons 105, exit 15, roof 15, hostility 38; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): the peaceful-group load event runs once per fill (map var `studio_peaceful_groups`),
  first of the load events.
- The crossword (A3's request): every answer also accepted with a trailing full stop, without or with a curly
  apostrophe, and Scepter/Sceptre in every form of 1 Across ("Scepter.", "Xeens Sceptre", "Xeen's Sceptre."); case and
  outer spaces the game already ignores. Only the listed names: "Sceptor" and "Staff." stay wrong
  (`variants()` in `output/studio_cal/fd04/tools/gen.py`; playtest_crossword answers "Xeens Sceptre.", "VAMPIRE.",
  "Kalindra’s", "corak." and checks the two wrong ones).
- D-66: the roof hatch to X9 (a BLV) asks the map's own Yes/No "Climb up through the hatch?" (no hook, nothing before
  it), Yes moves at once to entrance:fd04_roof's coordinates with `{direct = true}`, as DD-08's roof does;
  playtest_roof answers No (stays) then Yes.
- Only the Lua and the studio file changed (BLV and scene byte for byte the installed ones), so no rebake; installed
  06:15:44, stale bakes 0. Audit from `assets_dev` 0 errors, 127 warnings (126 kept `question.answer`, the family switch)
  (`output/studio_cal/a7/s19/audit/fd04.txt`); playtests 2 of 2 from `assets_dev` (`output/studio_cal/a7/s19/two_fd04.out`).

## Twenty-first session (2026-11-21, lane A7 lead)

- The nest's eggs: `S_EGG = 'xeen_dragonegg'` (lane S's row 4048: the Dragon Egg item's own ground model at 2.34x,
  58 x 40) in gen.py; three on the eggs' rock at z 2,512 (facings 20, 140, 260), `deco:egg_3` hidden by `evt:egg` and
  by `evt:egg_load` with 118146. `S_LIZARD` stays None (no lizard from S). playtest_alister asserts the three eggs shown,
  then the third hidden and two shown after the take and after the reload (`sprite_hidden` / `sprite_shown`).
- Baked shots `output/studio_cal/a7/s21/shots/fd04/` (eggs_north, eggs_east): the three eggs lie on the rock.
- Installed with its bake 08:03:55, stale bakes 0. Audit from `assets_dev` 0 errors, 127 warnings (126 kept
  `question.answer`, the family switch) (`output/studio_cal/a7/s21/audit/fd04.txt`). **36/36 from `assets_dev`**
  (`output/studio_cal/a7/s21/four_fd04.out`).

## Twenty-second session (2026-11-21, lane A7 lead)
- **The lizard:** `S_LIZARD = 'xeen_lizard'` (lane S's row 4049: MM8's Thunder Lizard, still, 50 tall, origin at its
  feet) in gen.py; `deco:lizard` hidden at Alister's spot (-1040, -768) facing 0 (east, out of the alcove; the tail
  reaches 59 behind, short of the west wall), `inside: deco:lizard` on `monster:alister` (the build's "stand inside
  each other" warning: he is hidden when it shows). `evt:alister_gone` and `evt:alister_gone_load` show it.
  playtest_alister (gen_tests.py) asserts it hidden at the start, shown the second after his paying talk and after the
  reload (40 steps).
- Built with the oymap of merge point 29, installed with its bake 09:02:02 (`output/studio_cal/a7/s22/install.sh`),
  stale bakes 0. Audit from `assets_dev` 0 errors, 127 warnings (the kept ones; `output/studio_cal/a7/s22/audit/fd04.txt`).
  **36/36 from `assets_dev`** (`output/studio_cal/a7/s22/four_fd04.out`).
- Baked shots `output/studio_cal/a7/s22/shots/fd04/` (alcove_before, alcove_lizard, lizard_near, lizard_side; sheet
  `../fd04_sheet.jpg`): the green lizard stands in the alcove facing out. The tour sets 118147 and runs
  `evt:alister_gone_load` (event 2) by console: the timer does not run during a tour.

## Twenty-seventh session (2026-11-22, lane A7)

- Tests (gen_tests.py): Alister's name is the NPC row's, "Alister, Druid" (merge point 41, F9-R2: an actor with an NPC
  id shows the NPC's name); "Two eggs are left", the Shrine of Minor Evil and "CODE ACCEPTED" are status lines (A3's
  hooks, D-90); `status()` reads a line once, so the terminal's answer is checked in the read that logs it. 36/36.
- `chest:tome` (chest.front): at (-1130, 880) facing n, its back to the east wall south of the door, its front to the
  room (it faced the tome's stand 20 away). Both exits' `7solid01` at one size. Installed with its bake.
- F14: `check_drops.py` lists nothing (the descent and the bone stair are steps on a continuous floor, which the check
  now joins; the eggs' rock likewise). Build warning kept: `7solid01` squashed on the roof hatch's trigger (black).

## D-181 (agent xeen-fb5-dungeon, 2026-11-26)

- The fountain room's `sta1a` (MM6's basin-less fountain) stands in a basin now: eight kerb stones (octagon 384
  across, inner 320, 64 high) round a water floor 16 under the kerb's top, the fountain at (1568, 9280) on the water
  line (`tools/xeen/check_fountains.py`).

## F75 (2026-11-26, agent:xeen-fb5-dungeon-f75)

Every dragon leashed (gen.py `LEASH`, 32-1,536) so a chase stops 64 clear of D-32's 256 x 288 openings instead of
sinking into the frame; seven posts moved deeper (ring hall 2, nest 2, high hall 2, crown 1); the hatchery's second
pair stands beside the first and holds its post (leash 32: 768 wide, too narrow for four dragons to move clear of its
two openings). `playtest_dragons` allows the nest's egg bowl (96 down). `check_monster_fit.py`: 68 stuck -> 0.

## D-186 (2026-11-26, agent:xeen-fb5-dungeon2)

Captures of the hatchery at rest from both doors and from above (`output/xeen_fb/p5_dungeon2/fd04/rest/`, crops
`rest_01_crop.jpg`, `rest_04_crop.jpg`; after a 20 s fight from the nest door `fight/`): the second pair's bodies ran
through the first's (a frost dragon's wing through the red's head, a frost head through a red wing), so D-186's
fallback applied. Group 25 moved to the nest: the Fire Dragon at (-506, 256) north of the egg bowl (leash 480), the
Frost Dragon at (100, -450) south-east of it (leash 512), both from `check_monster_fit.py --suggest`, 687+ from every
other dragon and off the bowl's bank (a post at (-506, 102) stood on the bank at z 2469, which `gen_tests.py`'s hall
test refuses). D-186 named the nest's south-west quarter; it already holds three of the nest's six. Counts kept
(`COUNTS`); the hatchery now holds one pair, the nest eight. `gen_tests.py` reads actor indices from
`output/studio_cal/fd04/root` (of 2026-11-21): its FD-04 scene and BLV were refreshed from the stage before the
playtests were regenerated. Fit 0, audit 0 errors, playtests 9 of 9, installed and baked; after captures
`output/xeen_fb/p5_dungeon2/fd04/after/`. Not mine: `check_ledge_shots` reports one error at the machine's lip
(z -1888, the Autobots of group 54), already on HEAD's FD-04.
