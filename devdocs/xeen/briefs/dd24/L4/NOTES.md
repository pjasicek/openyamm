# DD-24 Giants' Hall: L4 notes (lane A7, thirteenth session, 2026-11-21)

Built by the lane lead from `devdocs/xeen/mockups/act5_graphs/dd24.graph.yml` and D-47
(`devdocs/xeen/mockups/act5_a7_decisions.md`, DD-24 APPROVAL and Q22-Q26). Generator:
`output/studio_cal/dd24/tools/gen.py` (L1-L4; never hand-edit the written files); cycle
`output/studio_cal/dd24/cycle.sh` (builds against the scratch root `output/studio_cal/dd24/root`, which held the two
new textures before they were installed).

## What was built

Gurodel's hall in the hillside behind his hold on D5, at giant scale: 12 rooms, 12 sectors, 12.28 M units² (S: at most
15 and 20), 5 doors (two hinged pairs), 2 loops, 2 chests T5, 19 distinct textures of 30 (2 new). Floor 0: the porch
(the way out), the great doors (a hinged pair 384 x 512, `xdgiantd` with the right leaf mirrored), the threshold, the
longhall (2,048 x 1,024 x 1,024: two tables of split trunks, the fire trench, the law stone), the larder (a storeroom,
its chest), the sleeping hall (furs, hearth), the boulder store; the Great Stair (640 wide, 26 steps up 1,024, 1,024
of headroom). Floor 1,024: the landing, the throne hall's double doors (`xdgiantd` pair), the throne hall (sandstone
blocks, plank roof, a smoke hole 1,408 above the floor, the bloody throne of `xdthrone`, two braziers), Gurodel's hoard
behind it, the trophy gallery (its side door into the throne hall). The little ones' crack: a path 128 wide and 256 high
climbing 1,024 over 3,520 (16 degrees) from the boulder store to the trophy gallery. Music 31. Open sky preset
`xeen_darkside_failing` (D-47, Act V's sun stage; never `xeendark1`).

- **Peace and war (D-47 Q22):** the People (A2's rows 11083 Cyclops 38 x 9, 11084 Giant 50 x 17, 11085 Elder Giant
  58 x 4; faction `xeen_giants_people`) are placed friendly; A2's relations turn them on `q-d16.war` 113321, Q-D12's
  113242 / 113244 and `q-d16.hall_attacked` 113323. A timer (D-37's pattern, `evt:hall_struck`) watches every placed
  actor while none of those bits is set: one turned on the party (a blow) calls A3's `q-d16.hall_attacked`, and the whole
  People turn, here and on D5 (one faction).
- **The bloody throne:** both its seat and its back call A3's `q-d16.throne` (refuses at peace "Gurodel would
  notice."; at war two Energy Disks and 14,000 once, only without `friends` 113320; then "Nothing left on it but the
  blood."). **The hoard chest** opens only when A3's `q-d16.hoard` allows (at war); at peace its fail text. **The larder
  chest** opens at peace. **The law stone:** A3's `q-d16.law_stone`. **The threshold at war:** A3's
  `q-d16.war_threshold` (once per war, `war_announced` 113324) on the first step into the threshold.
- **Giant scale (D-47 Q26):** A2's giant rows are about 300 tall: the 128 x 256 crack keeps them out (playtest), the
  448- and 512-high doors let them through (playtest).

## Count and rest

30 placed, 20.80k per member (D-47 Q23); rest encounters 0 (D-47 Q25: encounter 0, no slots).

## New textures (A6 registers them; D-47 Q24)

`xdgiantd` (one wing of a giant double door, logical 128 x 256 drawn on a 192 x 512 leaf, the right leaf mirrored)
and `xdthrone` (black wood stained with old blood, a seamless 128 x 128 tile): Codex,
`level_generation/textures_xeen/a7_dd24_giant/` (specs.yml, raw/, refs/, finished/, sheets/check_*.png), gains 1.157
and 1.339, `xdthrone` seam pass; installed with `xtex.py install --root assets_dev --world xeen`, masters in
`assets_source/worlds/xeen/textures_x4/`. `xdthrone` came out a saturated red-brown rather than near-black (luma 38,
saturation 199): it reads as stained wood in the game; a darker second version is cheap if wanted.

**`xdthrone` v2 installed (D-51 item 4, fourteenth session, 2026-11-21).** Codex v2 asked for near-black, almost
colourless wood with the old blood the only clear red; finished with `tone: {like: [mm8/gkp1ceil], factor: 0.22,
saturation: 0.7}` (`saturation` is a new `tone` key in `xtex.py`: each texel pulled toward its own grey). D-51 named a
factor of about 0.35; v2's raw came back darker than v1's, so 0.35 gave luma 29 and 0.22 meets the target. Checks: mean
luma 21.3 (p5/p50/p95 6/19/36), saturation 106.5, seams 0.66/0.96 (v1: luma 37.8, saturation 199). Chosen in the game
against the hall's sandstone walls and plank roof (`output/studio_cal/dd24/s14/throne_v1_v2.jpg`, top v1, bottom v2,
unbaked root): v2 stands out black from the warm room and still reads as planks, beams and pegs close up. Installed with
`xtex.py install --root assets_dev --world xeen`, master in `assets_source/worlds/xeen/textures_x4/xdthrone.png`, map
re-baked (`output/studio_cal/a7/s14_dd24_install.out`). v1 stays in `raw/` and as
`finished/xdthrone_v1_master.png`.

## Exits and arrivals

- **Arrival `entrance:d5_hold`** (the map's start): room:threshold (0, 384), floor 0, facing north, 384 inside the great
  doors. D5's great doors (A6) name it.
- **Exit to D5 (fifteenth session, 2026-11-21):** the porch's south wall holds `exit:mouth` (512 x 256, `xddaylt`),
  the `exit` preset (`evt:way_out`, "Leave the Giants' Hall", the game's leave window) to D5's named arrival
  `entrance:dd24_hold` (11264, 10752, 2688) facing south (1536); the party lands at z 2689. `playtest_exit.yml`: out
  through the great doors and the mouth to D5, then back in by D5's great doors (D5's event 40).
- **The People's challenge on arrival (A3's relay):** the arrival (0, 384) stands inside `room:threshold`, so
  `evt:war_line`'s step does not run on the way in. `evt:war_arrival` (load, at war) marks map var `war_arrived`;
  `evt:war_arrival_say` (timer) then runs `q-d16.war_threshold` if the party stands in the threshold room (a message
  from a load event is lost with the map's loading, checked; a save loaded elsewhere in the hall shows nothing). The
  hook's own `once` (war_announced 113324) keeps it to once per war. `playtest_exit.yml` enters at war and sees it.

## Map qbits

None (118090-118099 unused): A3's Q-D16 bits carry every state.

## Dressing exceptions

- The longhall's two fires (`ckfyr00`) stand in the fire trench on the walking line's side (92 from it): the trench is
  the hall's set piece; the party steps over its 24-high kerb.

## Checks

- `oymap validate`: no issues; build 0 warnings; `oymap audit --world xeen --reach --solve`: 0 errors, 1 warning (above),
  lights, doors and texture fit clean.
- Playtests (`playtest.yml` 73 steps: peace walk, law stone, larder chest, the throne and the hoard refusing, a blow
  turning the hall, the hoard and the throne at war, reload, the threshold's challenge; `playtest_friends.yml`: friends
  then war, no second pair; `playtest_crack.yml`: the crack against a Giant and a Cyclops, a Giant through the larder
  door; `playtest_hostility.yml`): each passed in the root; 4 of 4 from `assets_dev` in `output/studio_cal/a7/s13_dd24_four.out`.
- Pictures (unbaked, root): `output/studio_cal/dd24/shots/sheet.jpg`.
- D-49 (2026-11-21) confirms the return to D5 at (86, 43) facing south, about 1,500 from Gurodel; A6 measures it.
- Fifteenth session (2026-11-21, merge point 22): the exit to D5 opened and the arrival's war challenge; installed with
  its bake 01:50:48, every playtest 4/4 from `assets_dev` (walk 73, friends 14, crack 24, hostility 26, exit 28:
  `output/studio_cal/a7/s15_dd24_four.out`).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): rebuilt; the peaceful-group load event now runs once per fill (map var
  `studio_peaceful_groups`), first of the load events. Only the generated Lua changed (BLV, scene and studio file byte
  for byte the installed ones; `output/studio_cal/a7/s19/`), so no rebake; installed 06:10:39, stale bakes 0. Audit
  from `assets_dev` 0 errors, the kept warnings (`output/studio_cal/a7/s19/audit/dd24.txt`); playtests 2 of 2 from
  `assets_dev` (`output/studio_cal/a7/s19/two_dd24.out`).
