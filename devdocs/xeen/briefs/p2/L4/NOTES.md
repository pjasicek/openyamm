# P2 Plane of Air of Xeen: L4

A6, sixteenth and seventeenth sessions, 2026-11-21. The L1 is `../L1/` with D-58 applied (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); the gate per D-64 (`devdocs/xeen/reviews/D64_DECISION.md`). L2-L4 are written by `output/studio_cal/p2/tools/gen.py`, the playtests by `tools/gen_playtests.py` from the build, this file and `output/studio_cal/p2/measure.json` by `tools/notes.py`. Scripts: `v.sh` (generate, fmt, validate), `b.sh` (build, playtests, scratch install, audit), `run.sh` (playtests through the lane's game slots; `tools/check_falls.py` on the fall logs), `tour.sh`, `stage_install.sh` (stage, tests, `INSTALL=1` into assets_dev).

## What was built

- One open-air room (`plane_air`, every face a sky face) from the safety floor -6,000 to 4,096; six islands as rough floating rock: a ragged 24-corner top slab, two shrinking tiers with their own outlines, tapered roots on Pythagorean facings to a jagged underside, crags on the rims off every walking line, untouchable cloud skirts under the rims; the Wind Statue's island packed cloud.
- Five cloud-stone bridges (`7tws1f`) with untouchable wisps under them; the Stair of Wind, sixteen steps of 32 from the Eye (256) to the Sleeper's Aerie (768, the highest island), with pale-brick cheeks (`t09a01`).
- The Eye of the Winds: ten standing stones and the gate's two (`gn_mtl01`); between the gate's stones the curtain of wind, a translucent `xcwisp` platform with `flow: up`, opacity 0.8, tint [0.72, 0.86, 1.15] (D-64), solid until qbit 111765, then hidden and passable (`evt:gate_open` on a 1 s timer, `evt:passed_load` on load: P-1).
- The test's floor before S's pedestal: 'Accept the test of Air?' Yes runs A3's `m38.test_air` and shows group 60 (Sleeper's Guardian of Air 11702, two Whirlwinds 11701); `Xeen.planeTestCheck("air", 60)` each second sets 111765 when all three are dead.
- Nine storm plates (`xpascorch`, A3's `planes.storm`), none on a bridge or in the Eye; the Singing Stones (seven hollow stones, MM8's `gwspout` once per long face, `planes.singing_stones`); the storm cairn (`planes.cairn`); the statue's plinth (`m38.plaque_air`) in the middle of its island.
- Ways out (D-58 C5): the updraft in a ring of white stones by the arrival ('Ride the wind back to the Skyroads?', `leave: exit:d7_way_up`) and the return dais in the aerie, shown on `m38_air` (`leave: exit:d7_dais`); both to D7's `entrance:p2_return`.
- Falls (D-58 P2 Q1): a 1 s timer sends a party under -1,500 through A3's `Xeen.skyFallTo("p2")` onto the Gale Landing (`entrance:d7_fall`, -4096, -4096) from 850 above, with falling damage; the safety floor's step event does the same.

## Figures (`output/studio_cal/p2/measure.json`)

- Monsters 30 (27 placed hostile, 3 hidden); kill XP 32,044 a member (D-58: 32.04k); first fight 3,134 from the arrival.
- Walkable 46.9 M (island tops 36.3 M, bridges 8.02 M, stair 2.52 M); 282 platforms (19 crags, 37 roots, 130 cloud skirts and wisps); build {'sectors': 2, 'vertices': 4560, 'faces': 3852, 'portals': 0, 'doors': 0, 'lights': 0, 'spawns': 0, 'entities': 6, 'events': 29, 'chests': 2}.
- **P-2 (measured):** the stair's cheeks stand 217 to 259 over its steps (minimum at the last step) and 288 over the Eye at the foot; the curtain 576 and the gate's stones 640 over the Eye; the aerie (768) is the highest floor (next 320), so no drop reaches it. `playtest_bypass` pushes into the curtain (stays on the Eye) and round both gate stones (the party walks off the rim and is thrown back onto the Gale Landing; never on the stair).
- POIs 10 (arrival and updraft, statue, Singing Stones, storm cairn, basket and cache, the Eye and the test, the gate, the aerie and sleeper, the dais); chests 2 at treasure 6 (the test's in the aerie, the trapped basket cache); the find: Air Resistance x2 by the basket.

## Playtests (headless, `run.sh`, N=2 from assets_dev after the install of 2026-11-21 07:39 (session 20, S's pieces); 18 of 18 in the stage before it)

- `playtest`: 2 of 2
- `playtest_bypass`: 2 of 2
- `playtest_fall_eye_east`: 2 of 2
- `playtest_fall_kite_west`: 2 of 2
- `playtest_fall_stones_north`: 2 of 2
- `playtest_hostility`: 2 of 2
- `playtest_sleeper`: 2 of 2
- `playtest_test`: 2 of 2
- `playtest_way_up_column`: 2 of 2
- falls: HP held 20 s (`tools/check_falls.py`: HP 0.5 s after the landing equal HP 20 s later; everyone alive).

The falls (D-54's shape): a new party's HP is random, so each member is set to 200, 140, 140, 140 before the fall; every fall of 850 costs the level-60 party 112, 49, 69, 46 (Knight, Cleric, Archer, Sorcerer), asserted exact 0.5 s after the landing and again 20 s later. A sorcerer at under 47 HP dies of a misstep (falling damage, D-6.2).

## Tour

`output/studio_cal/p2/pics/contact_t1.png` (`tour1.yml`): arrival, islands from high, the statue's isle, the north bridge, the Singing Stones, the Kite Isle, the Eye from high, the gate from the test's floor and close, before and after the test (the after shots set qbit 111765 and run `event 9`, evt:gate_open), the stair, the aerie.

## Deviations from L1 (each one line)

- The gate is a curtain platform, not a door (D-64).
- `xpastone` not made: MM8's shipped `gwspout` (pierced rock) is the Singing Stones' face.
- The way-up disc moved in to (-4931, -4723) (L1's point lay 50 from the rim); the storm cairn moved in onto its island.
- Island rims have 24 corners (the studio's platform limit), not 48; crags break the skyline.

## S's pieces (twentieth session, 2026-11-21)

- The Air Sleeper on his couch (`xeen_sleeper_air`, row radius 290): clicked, A3's `m38.sleeper_air` (its three answers; awake sets the qbit, the award and 10,500 experience).
- The statue on A6's plinth (`m38.plaque_air` on the plinth and on the statue); the test's pedestal 208 from its plate's centre, facing it.
- The return dais: S's disc on the studio disc's top, both hidden until the sleeper wakes; the dais rises the second the qbit is set (`evt:dais_show`, a 1-s timer) and on every load after (`evt:dais_load`); clicked on either, the dais's question and D7's return.
- Every binding turns by `yaw_offset` -90 (`facing` is where the front looks; the sleeper's head on the viewer's left). New playtest `playtest_sleeper` (the three answers, the dais hidden then shown, kept over a reload, Yes to D7).
- The couch stands under the dome's middle (4736, 3712), not L1's (4864, 3840): there its radius met a dome column; the updraft's column over the way-up disc asks like it (`evt:way_up_column`).
- The studio's `liquid and flow` warning counts the five decorations (17 wanted, 5 not found; the 12 liquid faces all found): A1.

## The wrecked basket (session 25)

- S's `xeen_balloonbasket` (row 4058, radius 64, solid) on Kite Isle at (-3712, 4224), z 320, facing 0 (the raised side on its rocks to the north); clicked, `evt:basket`: A3's `planes.basket` (the logbook). The find lies 115 and 160 east of its middle.
- The balloonist's cache moved from (-5056, 3840), 1,400 away, to (-3824, 4400), 209 north-west of the basket among its rocks, facing south-west, off the way from the bridge (the L1 design `level_generation/xeen_art/phase6/planes_design.py` and L1 rewritten): 'wedged in the basket' holds. The freed west rim took two more crags (six on Kite Isle; the kite_west fall still passes). Installed 09:46:44 (stage 18 of 18, from assets_dev 18 of 18, audit 0/0) (`output/studio_cal/a6/s25/`).

## Blocked (no stand-ins)

- None.

## Dressing exceptions

- None (no props; the standing stones, crags and Singing Stones are set pieces off the walking lines).

## S32 (2026-11-22, A6 32nd session)

Rebuilt and installed 01:36-01:39 (merge point 41): the way up, its column, the dais and its disc move into D7 through the standard entrance window (no Yes/No: F16, `planes/pieces.py d7_return_lua`); MAW reserve rewritten; stage tests all pass (sleeper and daily lines are status lines since D-90). The plate tops still show their picture 1.5x (18 audit errors, a studio fault: A1).

## S33 (2026-11-22, A6 33rd session: merge point 42)

The plates' `top_surface` is `{texture: xpascorch, size: [128, 128], fit: true}` (`size` is the picture's own size, 128;
`fit` lays it once over the 192 plate, and since merge point 42 once over its underside too). Rebuilt and installed
~02:00 through the stage (all stage tests pass); the 18 `textures.feature_repeated` errors are gone: the assets_dev
audit is 0 errors, 0 warnings. MAW reserve rewritten, `xeen_balance.py --check` passes.
