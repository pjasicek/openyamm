# DD-18 Sandcaster Sewer, L4: notes

The source's Sandcaster sewer (dark/aaze0032) rebuilt as a new M dungeon under D3 Sandcaster: an **optional** dungeon
(D-27): Barticus' members' room and the long tunnel under the desert to D5, built with the Map Studio from its graph
(`devdocs/xeen/mockups/act3_graphs/dd18.graph.yml`) and decider D-27 (`devdocs/xeen/mockups/act3_a8_decisions_b.md`,
which wins) by lane A8's sub-agent `agent:xeen-a8-dd18`, 2026-11-20. Key `dd18`, project `xeen_dd18`, stem
`xeen_dd18.blv`, map_stats 9171, world `xeen`, music 44.

**State.** L1-L4 `oymap validate` no issues, `fmt --check` clean, build 0 warnings. Installed in the scratch root
`output/studio_cal/dd18/root` only (the lane lead installs into assets_dev). `oymap audit --world xeen --reach --solve`
(`output/studio_cal/dd18/audit.txt`, `solve.txt`): 0 errors, 0 warnings, 0 faces in one plane, 0 dressing findings;
solve reaches 22 of 22 sectors in three steps (only doors), the exit to D3 listed. One info kept (below).

**Scratch** `output/studio_cal/dd18/`: `tools/gen.py` (plan, project, diagram; `python3 gen.py L1 L2 L3 L4`),
`tools/geo.py` (rooms, openings, themes), `tools/dress.py` (objects, wiring), `tools/tour.py` + `tools/sheet.py`
(tours and JPEG sheets), `cycle.sh` (generate, fmt, validate, build, install into the root, audit, record;
`LEVELS="L1 L2 L3 L4"`, `INSTALL=0`, `ROOT=`), `four.sh` (the three playtests N times, one game at a time, exact
PIDs; `ASSETS=` defaults to the root), `shoot.sh <tour>` (one tour run; `MAP=xeen_d3.odm` for D3), `run/` (logs),
`shots/` (sheets). **Every project file of L1-L4 except the playtests and these notes is written by the generator**;
each run recorded with `oymap record --author agent:xeen-a8-dd18`.

## The sewer

Two levels in one frame (x east, y north, heights from the arrival floor at the shaft ladder's foot):

| Level | Rooms | What |
|---|---|---|
| Under Sandcaster (0) | street shaft (arrival, 640 square, 1,280 tall, one round street grate overhead), Barticus' members' room (south, behind a door under the `xstraining` sign, the pay box beside it), main drain (a channel of slow water), stalker warren and its breeding vault, the great cistern (four pillars, a pool, stepped-fret vault 896 high), the alcoves (three niches), the cobra drain (a wide warm channel), the broken drain | stalkers, Matriarchs, Asps, Killer Cobras |
| The long tunnel (-640) | rubble slope (0 to -640) to the tunnel head (the milestone), mantis gallery, mantis nest and its egg cells, drowned vault (standing water, a strongbox), the long tunnel west in three lengths (east, the sand drift, west; 10,400 long), the desert gate (the grate, the prospector's pack) | mantis ants |

Added to the graph for the class band (20+ sectors) and for reasons in the rooms: the warren's breeding vault (the
graph's "collapsed side vault"), the three alcove niches (the graph's "corridor of niches"), the egg cells (the
graph's "egg cells in the walls"), the rubble slope as its own sloped room, the long tunnel in three lengths.

**Measured** (`oymap metrics`, `metrics.json`): **22 sectors** (M 20-45), **48.6 M units² of floor** (M 30-90),
7 doors, 5 chests, **50 placed monsters**, 29 lights (+19 torches), 7 placed sounds, 17 props.

## Monsters (all placed, Xeen rows of A2; no hornets)

| Who | Row | Level | Where | Count |
|---|---|---|---|---|
| Sewer Stalker | 11401 | 25 | main drain 4, warren 4, breeding vault 2, cistern 4, alcoves 2 | 16 |
| Stalker Matriarch | 11402 | 35 | warren 1, breeding vault 1, broken drain 2 | 4 |
| Guardian Asp | 11490 | 30 | cistern 2, cobra drain 6, broken drain 2 | 10 |
| Killer Cobra | 11491 | 38 | cobra drain 2, broken drain 2 | 4 |
| Mantis Warrior | 11371 | 30 | gallery 6, nest 2, egg cells 2, long tunnel 2 | 12 |
| Mantis Queen | 11372 | 38 | nest 3, egg cells 1 | 4 |

**Kill XP** L(L+10): 16 x 875 + 4 x 1,575 + 10 x 1,200 + 4 x 1,824 + 12 x 1,200 + 4 x 1,824 = 61,292 for the party,
**15.3k per member** (the graph's 14.6k + 5 %, D-27's "A2 confirm +5 %"). The shaft, the members' room, the tunnel head,
the drowned vault, the sand drift, the west tunnel and the desert gate are empty; the first fight is the main drain's
four stalkers, behind the shaft's east door.

## Mechanisms

- **The pay box** (D-27): a carved slot (`panel:paybox`, 6d08's glyph `d5smtrb`) on the shaft's south wall beside the
  members' room's door, under Barticus' sign. Clicked while `gym_paid` (A3's 116120) is clear, the map asks
  "It costs 5,000 gold to use the gym. Pay?" (typed Yes/No; the studio's question form). Yes runs A3's once-hook
  `dd18.pay_box`: with 5,000 gold it takes them, sets gym_paid and says "Enjoy the facilities."; short of gold the
  source's "What do ya think this is, a charity gym? Come back when you have enough gold." Any other answer: the
  status line "Get lost!" (dark/aaze0032:4). Once paid the box runs the hook again, which says "Paid up. Enjoy the
  facilities." with no question and no charge. The members' room's door itself is not locked (the hook design: the
  brews and the book ask `dd18.members_room`, "Members only. The pay box is by the door.").
- **The brews** (D-27): the Vitamin Brew (a glass, `dec35`) and the Protein Brew (a bucket, "thick enough to chew")
  on the brews' shelf against the members' room's south wall. Each asks `dd18.members_room` first, then gives the
  clicking member (`evt.ForPlayer(Players.Current)`) +2 base Endurance / +2 base Might once (player bits **11318** /
  **11319**) with A3's texts (`dd18.vitamin_brew`, `dd18.protein_brew`); a member who has drunk gets
  `dd18.brew_again` ("One per member. Barticus counts.").
- **The Art of Bodybuilding** (dark/aaze0032:6): the stone bench along the room's west wall (`platform:bench`):
  members only, then A3's `dd18.bodybuilding`.
- **The desert grate** (D-27): a round iron grate (`d1lggrt`, once on its 384-square face) on the desert gate's
  west wall runs A3's `dd18.tunnel_grate`: "Sand blows through the bars. The bolt is on the other side." while
  `d5_tunnel` (116121) is clear. The exit to D5 is **sealed** (below).
- **The alcoves**: the empty niches' back walls (a carved jamb) say "Nothing here." (hover "Alcove", dark/aaze0032:11);
  the middle niche holds the chest.
- **Sewer Drain**: three grated outlets (main drain, cistern, cobra drain; hover "Sewer Drain", dark/aaze0032:0):
  "Water trickles through the grate from the city above."
- **The milestone** in the tunnel head (a stone, `6rock04`): "Cut in the stone: TO THE DESERT."
- `evt:arrive`: a one-shot timer window on the first arrival only (`arrived_once` **117280**): "THE SANDCASTER SEWER.
  The ladder from the street ends by a door under Barticus' sign: his members' room, where the brews are kept. Barticus
  says the stalkers got in. East, the drains run round the city's old cistern, and they say there is a passage in the
  sewer that leads a long ways under the desert."

**Audit info kept:** `click.silent` on event 10 (the grate) when 116121 is set: the grate's event becomes the exit
preset in phase 5 (below), so the silent case never plays.

## Exits and arrivals

| This map's exit | To | Arrival | Facing |
|---|---|---|---|
| `exit:shaft` (the ladder's foot, north wall of the shaft; the game's leave window) | `xeen_d3.odm` | **(-17408, 15872, 1504)**: 256 south of the street shaft's iron lid (thing:dd18_shaft, 512 square at (-17408, 16384)), on open ground, ground measured 1,480-1,540 | south (270°, game 1536), away from the lid and Barticus' Gym |
| `panel:desert_grate` (sealed) | `xeen_d5.odm` (phase 5) | - | - |

Measured in `playtest_exit.yml` (headless, the window's OK pressed; the party then walks 384 south on D3). Pictures
`shots/d3arr_1.jpg`, `d3arr2_1.jpg`: east of the lid the party would face a house wall 600 away; south of it, open
ground and the lane bending south-west.

**D3's door into this map (A5):** `thing:dd18_shaft` (D3 event `evt:thing:dd18_shaft`, door:dd18) should arrive at
this map's start, **(0, 128, 0) facing south (270°, game 1536)**: the shaft ladder's foot, facing the members' room's
door under Barticus' sign. ("Descend to the sewer?" is A5's, as the entrance preset's meaning.)

**The desert grate (sealed until phase 5):** `project.yml` `neighbours` keeps `exit:d5_grate` to `xeen_d5.odm`
(`listed_only`, arrival [0, 0, 0] until A6 gives D5's point). Unsealing is one change in `tools/dress.py`: an `exits`
entry `exit:d5_grate` on the desert gate's west wall in place of `panel:desert_grate`, and `evt:desert_grate`
becoming `{preset: exit, source: exit:d5_grate, condition: {qbit: d5_tunnel}, locked_text: <A3's tunnel_grate
fail text>}` (`XeenQuests.can("dd18.tunnel_grate")` reads the same bit); D5's arrival from the
neighbour's row. **D5's way in (A6, phase 5)** should land at **(-7680, -5696, -640) facing east (0°)**, inside the
grate.

## Original lines

"Sewer Drain" (dark/aaze0032:0, the outlets' hover); "It costs 50,000 gold to use the gym. Pay?" rescaled to 5,000
(dark/aaze0032:3, the pay box's question); "Get lost!" (dark/aaze0032:4, the wrong answer); "Enjoy the facilities."
(dark/aaze0032:5, A3's hook); "What do ya think this is, a charity gym? ..." (dark/aaze0032:14, A3's hook); "Art of
Bodybuilding", "Vitamin Brew", "Protein Brew" (dark/aaze0032:6-9, hovers); "Alcove" (dark/aaze0032:11); "There is a
passage in the sewer that leads a long ways under the desert." (dark/aaze0031:33, in the arrival window).

## Ids

- Map qbits (block 117280-117319, provisional): `arrived_once` **117280**. A3's: `gym_paid` **116120** (set by
  `dd18.pay_box`), `d5_tunnel` **116121** (read by `dd18.tunnel_grate`).
- Player bits (provisional, A3 already lists them in `source/npcs/dd18.yml`): **11318** Vitamin Brew, **11319** Protein
  Brew.
- Map variables: none.

## Textures (two families)

**24 distinct of 45, 0 new** (`tools/xeen/texture_budget.py --root output/studio_cal/dd18/root --map DD-18`).
Under Sandcaster, MM6 Shadow Guild `6d08` (dungeon_families `sewers`): rubble brick `d5walc` (drains, shaft, warren),
carved sandstone `d5walba` (members' room, cistern and its pillars, drowned vault), jambs `d5walbre`/`d5walble`
(reveals, the alcoves' backs), flags `d5florc`/`d5florb`, the stepped-fret ceilings `d5ceila`/`d5ceild`, the lattice
door `d5dorsma`, the glyph `d5smtrb` (pay box, members' room's band), water `orwtrtyl`. The tunnel and the mantis
diggings in MM8 Passage Under Regna `d33`: its rock `t68a02b` (laid at 512: at 256 it read busy) over `t68a03b` and
`t68a03a`. MM6's sewer grate `d1lggrt` (the street grate, once over the shaft by a texture offset; the outlets; the
desert grate) and ladder `d1ladder`; A6's `xstraining` sign over the members' room's door. Chests and the decorations'
models add the rest. Note for A6: d33's rock is grey, not sand-coloured; the tunnel's lights are warm (sand) to tie it
to the city above.

## Dressing (D-7)

`oymap audit --world xeen --dressing` on the installed map: **0 findings** (the first L4 had two nest props on the
walking line between the nest's openings, moved). Props: a pair of barrels by the members' room's east wall, trash
heaps and bones in the warren, rocks by the broken drain's walls, dirt mounds and bones in the nest and egg cells,
sand drifts by the tunnel's walls and the gate. Chests stand by walls, clear of doors and openings. **Dressing
exceptions:** none.

**Lights** (the user's rule): torches (`torch02`) on walls at 224; the point lights hang in the rooms' air below the
ceilings with no fixture (the shaft's daylight just under its grate, the gate's daylight by its grate); none in a
doorway or inside geometry.

## Playtests

`output/studio_cal/dd18/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd18.blv`; the root has a test map_stats/bolster row for 9171 (DD-01's with this map's name, stem, treasure 3,
continent 7, music 44, the slots below) until A2 writes it; D3's row 9110 is live. Logs `output/studio_cal/dd18/run/`.

| Test | What |
|---|---|
| `playtest.yml` | the members' room refused before paying; the pay box: no gold (charity gym), No (Get lost!), paid (5,000 taken, gym_paid), paid up (no charge); both brews once for member 1 (refused again), the Vitamin Brew for member 2; the book; the drains, the cistern, the rubble slope, the long tunnel to the grate (refused, d5_tunnel clear), every chest, the milestone, an alcove, a drain grate, back to the shaft |
| `playtest_hostility.yml` | 16, 4, 10, 4, 12, 4 at load (50), none peaceful; a stalker, an Asp, a Mantis Warrior and a Queen side by side in the cistern do not fight each other, the last targets the party |
| `playtest_exit.yml` | the shaft's exit, the game's window, OK: D3 within 128 of (-17408, 15872), z 1,480-1,540; walks south |

**Results: all three 4 of 4, exit 0** (`output/studio_cal/dd18/run/four_190550`, summary `four1.out`): playtest
172, hostility 27, exit 24 checks passed in each run.

## Pictures (looked at)

`output/studio_cal/dd18/shots/rooms1_1..4.jpg` (30 poses: every room and interactive thing), `fix1_1.jpg` (after the
fixes), `fix2/small.jpg` (the street grate), `d3arr_1.jpg` and `d3arr2_1.jpg` (D3's lid and arrival). What I changed
after looking: the shaft's ceiling showed eight cut street grates (now one, centred by a texture offset, the shaft made
640 square); the tunnel's rock at 256 was busy and cold (laid at 512, the tunnel's lights warmed); the desert grate was
the lattice door's picture and read as one more door (now the round sewer grate); the bench and shelf tops tiled the
glyph (now flags); the cistern's pillars tiled the jamb picture (now carved sandstone). **No bake in the root** (the
lane lead bakes after install): lighting is the build's own.
Still plain: the members' room is a carved box with a bench, a shelf, a block and two barrels (no weights: no
decoration fits); the broken drain reads as a flagged room with rough walls more than a collapse.

## Words needed

1. **A ceiling picture placed once** (`fit` on a room's ceiling surface is not honoured: the shaft's street grate tiled
   with `fit: true`). Workaround: the grate laid at the shaft's size with a texture `offset` of half a repeat.

## Waiting on, and requests

- **A2**: map row 9171 (slots below); record the two brews as fixed by event (+2 Endurance / +2 Might, once per
  character, bits 11318/11319); confirm the +5 % (15.3k per member).
- **A3**: register `arrived_once` 117280; 116120, 116121, 11318 and 11319 are already A3's. No hook mismatch.
- **A5**: D3's door into this map (start point above; D3's lid event to the entrance preset into `xeen_dd18.blv`).
- **A6 (phase 5)**: D5's grate and its arrival point; this map's way in from D5 above.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/dd18/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The alcoves' north torch stood on the main drain's lattice door (0.8): now at 0.55 of that wall.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/dd18/audit_lights.txt`): lights
  errors/warnings before **2/0 (in_doorway, on_moving_face)**, after **0/0**; no dressing finding. **Light exceptions:**
  none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd18` (build `output/studio_cal/dd18/b_192918`),
  **assets_dev has no map_stats row 9171 yet (A2), so the game cannot load the map from assets_dev**: the bake from
  assets_dev failed (`could not load map`). Baked instead from the map's scratch root `output/studio_cal/dd18/root`
  (which has the row; its four map files were replaced by the installed ones, byte for byte), installed into assets_dev
  by `a8_s5/bake.sh dd18 <root>`; `stale_bakes.py --check` lists none of the lane's maps. **Playtests not run from
  assets_dev (the brief: skip without the row)**; from the scratch root, each 4 of 4
  (`ASSETS=output/studio_cal/dd18/root four.sh`; record `output/studio_cal/dd18/lights_post2.out`): playtest 4/4 (172
  steps); playtest_hostility 4/4 (27 steps); playtest_exit 4/4 (24 steps). Rerun from assets_dev when A2's row lands.
- **Pictures** `output/studio_cal/dd18/shots/lights_mp14/01-torch_10.png` (from the scratch root), looked at: the torch
  on the alcoves' north wall, clear of the lattice door.

## Session 7 batch (sewer bed, A8 session 7, 2026-11-20)

- AU's `xeen_amb_sewer` (62800) as the bed over the drains and the wet tunnels, not the sand end (the desert gate and
  the sand drift keep their wind): four sources in `tools/dress.py` `sounds()` (copy before: `dress_before_s7.py`):
  alcoves (2304, -896) and cistern (6528, 512) radius 3200 volume 0.4; tunnel east (1664, -5696) and mantis nest
  (4608, -7424) radius 3000 volume 0.35; inner 1000 each, apart.
- Audit: 0 / 0 before and after. Recorded, installed, baked; tests from assets_dev 4 of 4 (172, 27, 24 steps;
  `output/studio_cal/dd18/s7_post.out`). No pictures: nothing drawn changed.
- One size per texture (merge point 17's build warning; `tools/geo.py`, copy before: `geo_before_s7.py`): the shaft's
  street grate is `d1lggrt` at its own 256 at scale 2.5 with offset [102, 102] (was size [640, 640] offset [256, 256]);
  the pay box `d5smtrb` at its own 32 x 32 with `fit`. Build warnings 0, audit 0 / 0. Re-installed, re-baked, tests 4
  of 4 again (`s7_post17.out`: 172, 27, 24). Pictures `output/studio_cal/dd18/shots/s7/` (looked at: the round grate
  centred over the shaft, as before).

## Session 21 (A8): AU's sounds

The room-filling beds `sound:bed_cistern`, `bed_drains`, `bed_nest`, `bed_tunnel` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8): a ladder out of the cistern pool (F14)

- `check_drops` found the great cistern's pool (`level:cistern_pool`, `orwtrtyl`, 96 deep) a pocket: a party that
  stepped in could not climb its 96 edge. It now has iron rungs on its north edge (`ladder:cistern_pool`, at
  6528, -16, height 96, exit 6528, 64; `bemv` as XD-21's and XD-18's), from `tools/dress.py` `objects()['ladders']`
  (before: `output/studio_cal/a8_s26/before/dd18/`). The drains' channels (48 deep) and the drowned vault (48) are
  steps. check_drops 0.
- New `playtest_ladder.yml`: set down in the pool, the party climbs out onto the cistern floor (4 of 4,
  `output/studio_cal/a8_s26/run/dd18/t005825`).
- Installed 00:52, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd18/c005154`) plus the
  ladder's 4 of 4; audit 0 / 0; check_exits 0.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:27). The generator reproduced the L4 unchanged; the build changed
only the five chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. Installed,
baked; audit 0 errors / 1 warning: MP42's new support.edge on the Protein Brew bucket on the brews' shelf (96 deep,
128 high: no spot on it is 48 from its front; kept, a rule question for the studio), check_exits 0, check_drops 0;
tests 4 of 4 (16 of 16, output/studio_cal/a8_s26/run/dd18/c022736). Chest pictures:
output/studio_cal/a8_s29/shots/dd18_chests.jpg (all four on the floor).
