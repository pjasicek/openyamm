# XD-07 Castle Burlock, L4: notes

`agent:xeen-a7-xd07` (lane A7), 2026-11-20. Key `xd07`, project `xeen_xd07`, stem `xeen_xd07.blv`, map_stats 9123,
music 29, world `xeen`, class M. Every project file of L1-L4 is written by `output/studio_cal/xd07/tools/gen.py`
(edit it and rerun `output/studio_cal/xd07/cycle.sh`: gen, fmt, validate L1-L4, build, install into the scratch root
`output/studio_cal/xd07/root`, audit); the playtests are hand-written. Not installed in `assets_dev` (the lane lead
installs). Sources: the MU-6 graph `devdocs/xeen/mockups/act2_graphs/xd07.graph.yml`, decisions D-4
(`act2_dungeon_decisions.md`, which win), D-3.1 (Burlock's arms), D-9.1, D-11, U-1.

## What was built

28 rooms (29 sectors), 56 M units² of floor, all rectangles; nothing stands over anything else.

```
 1280  [Old King's throne: the throw]        [Royal bedroom: Roxanne's chest T3]
           | door                                    | stair (20 x 32)
       [Gargoyle loft: chest T2]             [Princess's landing: door 4204, plaque]
           | stair                                   | stair
  640  [West gallery: 3 plaques]-[Fools' hall: plaque]   (east tower)
                                   | stair
    0  [West tower foot]=door=[GREAT HALL: plaque]--arch--[Well court: well]
                                  |   \ PORTCULLIS (Crusaders)   | door
                       [Throne room: the throne = 4201]   [Library: two books]
                          | door      \ open                | door
                 [East tower foot]   [Gallery of arms: doors 4202 / 4203, two armour plaques]
            [Kitchens]--door--[GATEHOUSE: arrival; castle door (sealed)]
                | stair (20 x 32)
 -640  [Wine cellar: storeroom]=IRON DOOR (116080)=[Cell block T2]--door--[Pit gallery: lever, sign]
           | barred (den side)                       | open                     | stair 160 wide, 288 high
       [Troll den T2]--open--[Old cistern: Black Liquid]                     PORTCULLIS (lever)
           | door                                                             |
       [Postern (sealed)]                                       -1152  [Dragon pit: Fire Dragon, hoard T3]
```

- **The court** (floor 0, MM7 Titans' Stronghold marble with the carved dado band, Burlock's banners and Castle
  Harmondale's tapestries): gatehouse (white Ironfist ashlar, the kit's portcullis between two Burlock crests, two
  King's Guards), great hall (3,072 by 2,048, 960 high, four pilasters, two chandeliers), throne room (2,560 square,
  1,152 high, the throne on a dais under a tall crest, two braziers), gallery of arms, library, well court, kitchens.
  Loop: great hall - well court - library - gallery of arms - throne room.
- **East tower** (the royal family's): foot behind the throne room, two stairs of 20 risers of 32, the princess's
  landing at 640, the royal bedroom at 1,280.
- **West tower** (given up to the fools and gargoyles, D-4): behind a closed door at its foot; fools' hall and the
  gallery of arrow slits at 640, gargoyle loft and the old throne at 1,280.
- **Cellars and dungeon** (-640, MM6 grey ashlar, MM7 dark flags): wine cellar (the storeroom: 12 barrels, casks and
  kegs in rows along its walls), cell block, pit gallery, old cistern (D-4: "Old cistern", no ice), troll den (cave
  rock), postern. Loop: cellar - cell block - cistern - den - cellar once the den's bar is lifted.
- **Dragon pit** (-1,152, cave rock): the Fire Dragon on its hoard mound; reached only by a stair 160 wide and 288
  high under the pit gallery, its portcullis raised by the warden's lever beside his "Do not pull" sign (D-4).

**Monsters** (MAPS §0: party 12-14, levels 10-24, treasure 2): 26 spawn markers with fixed tiers, about 47 hostiles:
Madmen 20 (slot 1: Raving Lunatic 12 at five markers, Mad Fool 8 at three, D-4), Gargoyles 12 (slot 2: Gargoyle 16 at
five, Gargoyle Lord 22 at three), Trolls 15 (slot 3: Troll 18 at ten, the Trolls A row, D-4). Kill XP about 18.2k,
4.56k per member against MAPS's 4.3k (+6 %). Placed: seven King's Guards 11143 (immobile, peaceful by the world's
relation `xeen_burlock_knights_d`) and the Fire Dragon 11642 (hostile, optional, outside the band, D-4).

**Chests** (5, U-1: random loot only, no invented items): gargoyle loft T2, Roxanne's T3 (q-c3.bedroom_chest), the
warden's strongbox T2, the trolls' loot T2, the hoard T3.

**Textures**: 43 distinct (cap 45), none new for this map; the royal kit's `xkportc`, `xkburcrst`, `xkburban`,
`xkarrow` (A6's). Families: court `t3s2b1`, `t3s2b`, `t3s2c`, `t3s2fl1`, `t3elr`, `xkburban`, `tap1/4/7`, `7t1books`,
`chb1dl/dr`, `7tws1f`, `tfb09r1i` (the throne's and bed's red cushions); gatehouse and towers `hcwall`, `hcwindo`,
`xkarrow`, `cstyl`, `csbr128`, `hclgdr`, `7tws1h`, `roof`; service and dungeon `cswl128`, `tfb09`, `tfb08`, `t5d1`,
`xwcage` (XD-04's bars); caves `gcav1flr`, `gcav2flr`; signs `sign128` (the plaques), `warnsign` (MM7's skull sign,
the warden's); chests `ch1*`; water `7wtrtyl`.

## Quest hooks (A3), house doors (A4), qbits

- `m5.crusaders_gate`: `evt:portcullis` (event 40): condition m4.done 110047, opens the portcullis; both branches call
  the hook (its fail text is the source's line).
- `xd07.dungeon_door`: `evt:dungeon_door` (28), condition 116080 (Artemus's key, a qbit), opens the iron door.
- `q-c3.bedroom_chest`: `evt:chest_roxanne` (12), condition 112061 (Q-C3 done).
- `xd07.old_throne`: `evt:old_throne_landed` (46), the throw's message once the party has landed (below).
- The nine plaques `xd07.plaque_*` (31-39), each on the wall of the room its hook names.
- `m5.throne` has no `call` (A3: "A4 places them"); the throne opens house 4201 (below), which is where it belongs.
- **House doors**: the throne itself (`platform:throne`, event 43, title "King Burlock") opens 4201 when m4.done holds,
  else "Only Crusaders are allowed to enter Castle Burlock." (A4's closed_text); `door:advisor` (gallery of arms, north
  wall) 4202; `door:builder` (gallery of arms, south wall) 4203; `door:roxanne_parlour` (princess's landing, east
  wall) 4204. A4 proposed `door:throne_room` for 4201: the map's id is `platform:throne`.
- **Map qbits** (110720-110759): `den_bar_lifted` 110720, `cage_lever_pulled` 110721. Read: m4.done 110047,
  m5.audience 111100 (not tested by the map), xd07.dungeon_key 116080, Q-C3 done 112061. Player bit 11070 (the Black
  Liquid, once per character).

## Sealed exits (X4 not built)

Every exit of XD-07 leads to X4 (Burlock Savannah), not built in phase 2: the project has no neighbours and the built
Lua no `MoveToMap` to another map.

- **Castle door** (`panel:castle_door`, gatehouse south wall, `hclgdr`): a message window ("The great doors are barred
  from outside ..."). To open: make it `exits: [{id: exit:x4_gate, room: room:gatehouse, wall: south, size: [384, 384],
  surface: hclgdr ...}]` in gen.py, a project neighbour `exit:x4_gate` to `xeen_x4.odm` at A5's gate arrival, and
  `evt:castle_door` the `exit` preset.
- **Postern** (`panel:postern_door`, west wall of the postern tunnel): a message window ("... a barge sunk across it.
  There is no way out here for now."). To open: the same with `exit:x4_moat` at A5's moat-bank arrival.
- **The old throne's throw** (D-4: onto X4 about 1,000 above the ground beside the west tower, ordinary fall damage).
  For now the throne shakes the screen, deals 20 damage and moves the party to the castle door inside the gatehouse
  (0, 384, 0); a one-second timer then calls `xd07.old_throne` ("You teleported into the air outside the tower!"),
  because a message window opened before an in-map teleport closes with it. To make it real: replace the `teleport`
  effect with `leave: exit:x4_air` (a neighbour to `xeen_x4.odm`, `one_way: true`, arrival about 1,000 above the
  ground beside the west tower; the game's fall damage replaces the 20), and move the hook call before it (a message
  shown on arrival in X4 is A3's to place, or keep it in the throne event: check that the window survives the move).
- **Arrivals proposed for A5** (D-11: X4's castle rise is at height 1,900 in X4's L1, still being approved; it may move):
  the castle door's outside arrival on the rise in front of the gate at z 1,900, facing away from the castle (south);
  the moat bank below the castle's west side for the postern; the throw's landing beside the west tower outside the
  walls at z about 2,900 (1,000 above the rise).

## Original lines (three or more)

"Only Crusaders are allowed to enter Castle Burlock." (aaze0014:8, the portcullis, through A3's hook and the throne's
else text); "The water refreshes you." (aaze0064:29, the well); "Black Liquid" (aaze0063:3, the old cistern, +2 Might
instead of +10); the nine plaques (aaze0064:6-8, aaze0065:0-3, aaze0066:5-6) and "You teleported into the air outside
the tower!" (aaze0065:7) through A3's hooks.

## Words needed (workarounds)

- No `store: true` on rooms yet (D-7.5): the wine cellar is a storeroom by count (12 containers).
- A message window opened before an in-map teleport closes with it: the throw's message comes from a timer after it.
- A condition with a hook in `else_effects`: the build warns that a click "does nothing the player sees"
  (`evt:portcullis`, `evt:dungeon_door`, `evt:chest_roxanne`); the hook shows A3's text there. Three build warnings,
  kept on purpose (a duplicated `locked_text` would drift from A3's text).
- `spawn_actor` in a scenario summons a hostile actor even of a family friendly to the party (the hostility test
  allows one hostile guard: the spawned one).

## Dressing exceptions

None: `oymap audit --world xeen --reach --solve` gives no dressing error or warning.

## Checks

All from the scratch root `output/studio_cal/xd07/root` (a hard-link copy of `assets_dev` with its own
`worlds/xeen/maps`, `events/maps`, and a **test-only map_stats row 9123** appended to its own copy of
`worlds/xeen/data_tables/map_stats.txt`, since A2's `source/map_rows.yml` has no XD-07 row and the game cannot load a
map without one), `build-xeen/game/openyamm --world xeen`:

- `validate` L1-L4 clean; `build` (28 rooms, 1,692 faces, 29 portals, 17 doors, 22 lights, 26 spawns, 46 events, 5
  chests; the three hook warnings above); `fmt --check` clean; `audit --reach --solve`
  (`output/studio_cal/xd07/audit.txt`): 0 faces in one plane, 28 of 28 sectors, no error or warning, info only
  (`click.silent` of the house doors and the hook branches); `oymap solve`: 4 steps (m4.done, then 116080, every lever
  and key reached), never reached 0.
- `playtest.yml` (191 steps) and `playtest_hostility.yml` (40 steps), 4 of 4 each: `output/studio_cal/xd07/four.out`,
  logs `output/studio_cal/xd07/run/`.
- `tools/xeen/texture_budget.py --root output/studio_cal/xd07/root --map xeen_xd07.blv`: 43/45, 0 new.
- Pictures: `output/studio_cal/xd07/look1_a.jpg`, `look1_b.jpg`, `look1_c.jpg` (26 rooms), `look2.jpg` (after the
  fixes). Fixed after looking: arrow slits and windows had been whole wall surfaces (a wall of slits, two rows of
  windows); they are now single panels every 384-768 clear of the openings. A white fountain-like statue (`sta1a`) was
  tried for an armour stand and dropped.

The playtest's setup shortcuts stand for what other maps give: m4.done 110047 (X1's M4, before the portcullis),
m5.audience 111100 (the King's topic, after the audience), 116080 (Artemus's topic), 112061 (Q-C3's end, Roxanne).

## Blocked and open

- **A2**: the map_stats row 9123 (slots below; lock 2, trap 1, perception 2, treasure 2, music 29, STONEROOM); the
  test root has a copy. `tools/xeen/balance.py` counts placed actors: the seven King's Guards (11143, 2,000 XP each,
  peaceful) must be left out of the kill count (a friendly row), and the Fire Dragon (11642, 6,375) belongs in the
  map's `traps` (D-1.2: optional, far above the band).
- **A4**: houses 4201-4204 are `planned: true` and have no rows in `house_data.txt` yet: the doors open "House #4201"
  ... (the playtest asserts a house dialog, not its title).
- **A1**: does an actor's radius keep a large monster out of a narrow passage (D-4)? The pit stair is 160 wide and 288
  high, the Fire Dragon 476 across and 487 high, and it flies.
- The library's two books are readable texts: the source's free Linguist and Astrologer have no skill in OpenYAMM.

## What the user should look at

The throne room and the audience through the throne; whether the Fire Dragon can be seen and stays in its pit; the two
armour stands (MM7's armoured dwarf statues `7dec54`/`7dec55` on plinths: no shipped suit of armour); the old throne's
throw (lands inside the castle door until X4 exists); the King's Guards standing still at their posts (immobile).

## Installed (2026-11-20, lane lead A7)

Built from this L4 (`output/studio_cal/xd07/a7_lead_build/`) and installed into `assets_dev` and the scratch root; baked (profile `tools/lighting/baked_indoors/profiles/xeen_xd07.yml`, `output/studio_cal/a7/bake_map.sh xd07 <root with the test row> --sources <repo>/assets_source`, then `output/studio_cal/a7/install_bake.py xd07`; 4.5 MB). The map does not load from `assets_dev` until A2 writes map_stats row 9123 (the slot lines above); A4's house rows 4201-4204 are missing (the doors open as "House #4201"). The scratch root's test rows are kept in step with `output/studio_cal/a7/sync_test_rows.py`.

## Rows, houses and the X4 switch (2026-11-20, lane A7, third session)

- **A2's row 9123** is live (slots Xeen Madman 5 [2,3] w40, Xeen Gargoyle 1 [1,2] w30, Xeen Troll 0 [1,2] w30) and
  **A4's houses 4201-4204** have their rows and residents. Artemus's, Emerson's and Roxanne's houses now open their one
  resident's talk directly, so `playtest.yml` asserts an open dialogue there (`dialog: {active: true}`, lines 97, 103,
  133); the throne room (4201) still opens as a house. From `assets_dev` with `--world xeen`: `playtest` 4 of 4
  (`output/studio_cal/a7/p2_xd07_four.out`), `playtest_hostility` 4 of 4 (`output/studio_cal/a7/p2_assets_four.out`);
  `audit --reach --solve` from `assets_dev`: no error, no warning (`output/studio_cal/a7/p2_audit_xd07.txt`).
- **The X4 switch.** `output/studio_cal/xd07/tools/gen.py` opens the castle door and the old throne's throw by itself
  once `assets_dev/worlds/xeen/maps/xeen_x4.odm` exists (`XD07_X4=1`/`0` overrides): neighbour `exit:x4_gate` to
  A5's arrival (-1024, 6768, 1760) facing south (direction 270; X4's gate at (-1024, 7168, 1888)), the exit face
  `exit:castle_door` (384 x 384, hclgdr) on the gatehouse's south wall and `evt:castle_door` an exit preset; neighbour
  `exit:x4_air` (one way) to A5's landing (-4608, 9728, 2900) facing east (briefs/x4/DOORS.md), `evt:old_throne` shakes,
  calls `xd07.old_throne` and leaves (the game's fall damage replaces the 20; the landing timer goes). Checked with a
  scratch build (`XD07_X4=1`, MoveToMap to both points); with X4 absent gen.py writes the installed L4 byte for byte.
  When X4 is in: `python3 output/studio_cal/xd07/tools/gen.py`, then
  `python3 output/studio_cal/xd07/x4_prepared/patch_playtest.py` (takes the door click and the throw out of
  `playtest.yml`, which go to `playtest_exit.yml`), cycle, playtests (`playtest playtest_exit playtest_hostility`),
  install into `assets_dev`, rebake.
- **The postern** stays sealed: A5's DOORS.md has no moat-bank arrival yet (asked for in the lane's report).

## X4 linked (2026-11-20, lane A7, third session)

X4 is installed (row 9102). gen.py opened the castle door and the throw (the switch above); `patch_playtest.py` moved
the door click and the throw out of `playtest.yml` into `playtest_exit.yml`; the three houses' asserts read the
resident (`dialog: {source_id: 4402}`, 4403, 4404; A4). **Measured on X4:** the castle door's arrival stands at Z 1757.7
(A5's ~1760); the ground under the throw's landing (-4608, 9728) is **1505, not ~1,900**, so the landing is now
(-4608, 9728, 2505) facing east, 1,000 over the ground as D-4 says (the ground there is 400 below the castle rise: A5
may want the spot nearer the tower). Checks in the fresh lane root `output/studio_cal/a7/root_x4`: build 0 warnings,
audit clean; `playtest_exit` (20 steps), `playtest` (187), `playtest_hostility` (40) every step 4 of 4
(`output/studio_cal/a7/x4_four2.out`, `x4_xd07_exit.out`; the 15:52 `build-xeen` binary dumps core on exit after every
scenario, A1's). Installed into `assets_dev`, re-baked. The postern stays sealed (no moat-bank arrival from A5 yet).

**A5's built X4 points (2026-11-20, later):** the exits now use A5's built arrivals (they supersede the provisional
DOORS.md ones above): XD-07 gate (-1024, 6912, 1808) south, throw (-4608, 9728, 2504) east; XD-25 (-11520, -9448, 1056)
south; XD-02 adit (20080, -16128, 1504) west; XD-26 mouth (-9216, 11208, 1824) south, sky crack (-7424, 14592, 3600)
south. Measured landing Z: 1802, 1505 (ground), 1057, 1505, 1821.5, 3593. Exit playtests 4 of 4 with clean exits in
`output/studio_cal/a7/root_x4` (`output/studio_cal/a7/x4_built_four.out`); installed, re-baked.

## D-24 and the postern (2026-11-20, fifth session, lane A7)

- **D-24 (merge point 10):** the studio's `leave` now writes `{direct = true}`: the old throne's throw moves the party
  to X4 at once, with no leave window (`playtest_exit.yml` presses no OK for it and asserts no dialogue on X4). **The
  party lands standing**: an ODM arrival puts the party on the ground at once (Z 1505 a tenth of a second after the
  move, full health), so the throw does no fall damage. D-4's fall needs A1's neighbour `keep_height` word (asked);
  then the playtest gets back its `party_health: {full: false}` assert.
- **The postern is live:** `exit:postern` (west wall of the postern tunnel, `t5d1`, the `exit` preset, "You lift the
  bar and slip out at the foot of the castle rise.") to `exit:x4_moat`, A5's point (-5120, 8448, 1312) facing west
  (X4 has no moat: the flat ground at the castle rise's west foot), one way. Measured landing Z 1313.
  `playtest_exit.yml`'s third part (event 41).
- Checks: build 0 warnings, audit clean; playtests in `output/studio_cal/a7/root_s5`, then from `assets_dev` 4 of 4
  (`output/studio_cal/a7/s5_xd07_four2.out`); installed, re-baked (`s5_bake_xd07.log`).

## Sixth session (2026-11-20, lane A7)

- **Lamp rule (A1's lights audit, merge point 14):** the two dais braziers were MM6's chained `brazir2f` standing on the floor: now `flamb00` flambeaux. Clean under the audit.
- **The postern lives in `gen.py` now.** The fifth session made the live postern by hand in L4 (studio history entry 1),
  so the sixth session's `gen.py` run for the lamp rule sealed it again (the walk and the exit test failed at the
  postern). `gen.py` writes `exit:postern`, `exit:x4_moat` and the `exit` preset whenever X4 is installed; the L4 it
  writes equals history entry 1's L4 except the two flambeaux (checked by diff). Never hand-edit this L4: change
  `output/studio_cal/xd07/tools/gen.py`.

## Merge point 15 doors (2026-11-20, lane A7)

A1's door check (`oymap audit`, [DOORS.md](../../../formats/DOORS.md)) found eight faults: `doors.half_wing` on doors 1,
5, 6, 7, 8, 9, 15 (one 256-wide leaf showing the single wing `chb1dl` or `chb1dr` over the whole doorway) and
`doors.wing_unmirrored` on the throne room's pair 13/14 (both leaves `chb1dl` the same way round). All in
`output/studio_cal/xd07/tools/gen.py` (`WINGS`, `WING_PAIR` before `objects_yml`, and `OPENINGS`):

- **Seven hinged pairs**, `{kind: hinged, leaves: 2, pictures: [[chb1dl, chb1dr]]}` (Castle Harmondale's left and
  right wing on the left and right leaf, seen from each side): `door:kitchens`, `door:west_tower`, `door:library_s`,
  `door:library_n`, `door:east_tower`, `door:bedroom`, `door:old_throne`. Their door ids stay (1, 5, 6, 7, 8, 9, 15:
  the left leaf); the build gave the right leaves 18-24 (`<id>.leaf2` in ids.lock.yml), so every playtest's
  `open_door`/`door_state` keeps working. Events, locks and keys are unchanged.
- **Their doorways are 288 wide** (were 256). A leaf 128 wide pivots in the middle of the 256-deep wall, so swung 90
  degrees its free end lay exactly in the room's wall face (14 new `faces in one plane` build warnings and audit
  `geometry.coplanar` warnings). `swing: 80` cleared them but narrowed the open doorway and hid the party from the
  kitchens: `playtest_hostility` failed 4 of 4 (step 32, the last spawned kind never saw the party through the
  kitchens door). At 288 each leaf is 144 wide, lies along the reveal when open and stands 16 out of it; the open
  doorway is as wide as before. The picture stretches 1.125 across and 1.5 up (it was 2 by 1.5 on the old leaf).
- **The throne room's pair** (sliding, 384 wide) has `pictures: [[chb1dl, chb1dr]]`: a left and a right wing.
- The wall-panel house doors (`door:advisor`, `door:builder`, `door:roxanne_parlour`) are panels, not door records:
  unchanged.

**Counts** (scratch root `output/studio_cal/xd07/root`): build warnings 0 before, 0 after; audit errors and warnings
0 before (`output/studio_cal/xd07/a7_xaudit_before_mp15.txt`, built with the pre-15 oymap), 0 after with the
merge-point-15 `oymap` (`a7_xaudit.txt`; also from `assets_dev`: `output/studio_cal/xd07/mp15/audit_assets_dev.txt`).
`oymap audit --doors-measure`: every pair `class feature door wing`, copies 1 x 1, partner the other wing.
`fmt --check` clean. Faces 1,691 -> 1,726, door records 17 -> 24.

**Pictures** (menu-input tour, `output/studio_cal/xd07/mp15/make_tour.py` -> `look.yml`; each door closed from both
sides, then opened by its event and seen from both sides): `output/studio_cal/xd07/mp15/look3_sheet1.jpg`,
`look3_sheet2.jpg`, full size in `mp15/look3/`. Wings read left and right from both sides, leaves meet in the middle,
open leaves lie against the reveals. (`look2_sheet*.jpg` is the rejected 80-degree version.) The old throne's door
stayed shut in its open shot: three gargoyles stood in the doorway (the walk opens it after the loft is cleared).

**Installed and re-baked** (`output/studio_cal/a7/s6_chain.sh d34y xd07`; `stale_bakes.py` 0 stale). From
`assets_dev`, every playtest 4 of 4, exit 0 (`output/studio_cal/xd07/mp15/chain2.out`, logs
`output/studio_cal/xd07/a7_xrun/`): `playtest` 187 of 187, `playtest_exit` 31 of 31, `playtest_hostility` 40 of 40,
`playtest_dragon` 17 of 17.

**For the user:** the double doors of the court and the towers swing apart into the room away from you; the throne
room's doors slide apart into the walls.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The Crusaders' portcullis `xkportc` at `scale: 1.75` (one picture up the 448-high gate; was 1.75 copies).
- The three cell bars' tops in `cswl128` (were `xwcage` along a 16-wide top: the band 1.8 times up).

### Texture fit exceptions

- `textures.storey_stacked` `xwcage`: the cell bars 512 high, two storeys of bars: a `module` texture under D-41 (no finding once A1 wires it).
- `textures.feature_border` `sign128` on `t3s2b1` (61 against 60): the brass name plaques by the doors, meant to read as plaques.
- `textures.feature_border` `warnsign` on `cswl128`: the warden's 'Do not pull' sign, meant to stand out.

## Merge point 17 (2026-11-20, ninth session, lane A7)

- The throw's neighbour `exit:x4_air` has `keep_height: true` (L4 and `tools/gen.py`): the party arrives in the air
  at 2,500 beside the west tower, falls to the ground at 1,505 and takes fall damage (105 → 66 and 58 → 39 HP in
  `playtest_exit.yml`, which now asserts the height on arrival, the landing and that the party is hurt).
- The cell bars' tops `cswl128` at [128, 256], the wall's size (the build keeps one size per texture). 0 build warnings.

## The Book of Languages (A3's relay, 2026-11-21, lane A7 fourteenth session)

`evt:book_languages` calls A3's `XeenQuests.hook("xd07.book_languages")` instead of its own text window: the first read
sets the shared Linguist gate (qbit 116240, award 420) that the Cloudside rhyme statues (X8, X9) ask, later reads give
the plain text. The playtest reads the book twice (the "(Linguist)" line and the bit, then the plain text). Rebuilt
(only the map's Lua changed), installed with its bake 2026-11-21 00:57; 16 of 16 from `assets_dev`:
`output/studio_cal/a7/s14_xd07_four.out`. The scratch root's own audit now shows 102 texture-fit errors from its stale
engine files; the same build audited with `--assets assets_dev` has 0 errors.

## Merge point 30 (2026-11-21, lane A7 twenty-third session)

- `panel:tap_landing` stood over 64 of `open:landing_stair` (merge point 30's panel warning) and its top ran 64 above
  the landing's ceiling. Moved to offset 32 (32 clear of the corner and of the stair's doorway) and bottom 64, so the
  tapestry (256 by 448, as the others) ends at the ceiling. Edited in `output/studio_cal/xd07/tools/gen.py`.

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:hearth_fire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
