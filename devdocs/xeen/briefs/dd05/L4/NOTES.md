# DD-05 Western Tower of Mok (L4): notes

Lane A8 (agent `agent:xeen-a8-dd05`), phase 4 (session 8), 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act4_graphs/dd05.graph.yml`) with decider D-42 (`mockups/act4_a8_decisions.md`), which wins.
One script, `output/studio_cal/dd05/tools/gen.py`, writes L1-L4 (playtests and this file by hand).
`output/studio_cal/dd05/cycle.sh L4 "<label>"` generates, formats, validates, builds, installs into the scratch root
`output/studio_cal/dd05/root` (data_tables a real copy; map card 9154 already in it, A2's provisional row), audits and
records.

**Installed and baked** (session 9, lane lead, 23:38; tests 4 of 4 from assets_dev; one stand-in left: the Pegasus, "Waiting on").

## What was built

Map 9154, `xeen_dd05.blv`, class M, on D1. Four floors 640 apart (L1 0, L2 640, L3 1280, L4 1920), inside 3,456
square (larger than D1's tower, D-42 (6)). 29 rooms/sectors, 31.75 M units², 12 doors (13 leaves: the chapel's pair),
4 chests, 45 placed monsters + Humble and Pious, 5 loops. Six stairs (20 steps each) in four lanes, two per pair of
floors in different places: L1-L2 east (E1) and south (W1); L2-L3 west (W2) and outer (E2); L3-L4 altar (W1) and
tower (E1).

- L4: hoist room (arrival, rope-window exit, store), bone gallery (3 bone finds), chapel (d22 marble, gtemprf cone
  ceiling with ring beams, altar + xmoktap sun, chandelier, two standing candelabra; double doors gtempdor1 pair),
  vestry (hoard chest T5), tapestry walk (3 xmoktap; middle one's button slides the secret panel), cells (2 bed finds).
- L3: cloister (windows t19b04c), Pious's cell, fountains of cold and venom, upper dormitory (chest T4), stair landing.
- L2: landing, kitchen (store, hearth fire, chest T4), refectory (table, benches, 2 lamps), fountains of fire and
  lightning (2 Stone Golems), lower dormitory (purse), Humble's cell.
- L1: stair hall, hall of alcoves (two crysdisc discs, the Pegasus (a stand-in, "Waiting on") on ledges in gtempw2 niches), novices'
  dormitory (2 bed finds), mirror hall (xkmirror in a gstntilev frame), hall of the warded door (front-door exit,
  Heretic Lord + 3 Iron Golems; golem height 215 under a 512 ceiling), guardians' gallery (3 Stone Golems, chest T4).

Monsters (D-42): Mok Heretic 11220 ×22, Heretic Priest 11221 ×11, Heretic Lord 11222 ×3, Cult Leader 11223 ×1,
Stone Golem 11581 ×5, Iron Golem 11582 ×3 (L4 10, L3 12, L2 10, L1 13). Kill XP 57,155 → 14.29k per member. Humble
11910 (group 40) and Pious 11911 (group 41), immobile, from their own rows/factions, not counted.

Slots (`project.yml`, = A2's row): `Xeen Heretic` tier 0 (Mok Heretic) 2-3 weight 75; `Xeen Heretic` tier 1 (Heretic
Priest) 1-2 weight 25; encounter 10 %.

## Hooks and state

- `q-d6.tower_key` (altar), `q-d6.cult_leader` (timer on `kills: monster:cult_leader`), `q-d6.l1_alcoves` (either disc
  or ledge: the map gives 2 × 12334, hides both discs by `evt.SetSprite(n, 0)`), `q-d20.pegasus` (statuette hidden
  after), `q-d6.front_door` (the front-door exit's else branch until `tower_opened`; then the exit preset),
  `q-d6.fountain_water/body` (L3), `fire/air` (L2) (`evt.ForPlayer(Players.Current)` then the hook).
- Humble/Pious: a step event on entering the cell (and the bed) asks the plea and "Slay him anyway?" (Yes/No buttons).
  No: A3's `q-d6.humble`/`pious`; Yes: the source's kill line and the map's `humble_slain` 117361 / `pious_slain`
  117362. Either hides the group at once; a load event hides it again (and re-hides discs/statuette by their bits).
- Map qbits (provisional block 117360-117399): `arrived_once` 117360, `humble_slain` 117361, `pious_slain` 117362.
  Player bits used through A3's hooks: 11341-11344.
- Exits: rope window (`exit:d1_rope` → D1 `entrance:dd05_rope`), front door (`exit:d1_door` → D1 `entrance:dd05_door`).
  **Measured on D1** (`playtest_exit.yml`, D1 as installed 2026-11-20): the rope lands at **(-16896, 16896, 1601)
  facing north (512)** (a 0.4 s step forward goes +306 north, away from the tower); the front door lands at
  **(-16896, 14848, 1601) facing south (1536)** (the step goes south, away from the door).
  Inside arrivals: `entrance:d1_rope` (1376, 1472, 1920) facing south (= start, measured); `entrance:d1_door`
  (0, -1536, 0) facing north. D1's `door:dd05_rope`/`door:dd05_front` are still `listed_only` (sealed) and name no
  arrival: A6 (only leaving DD-05 into D1 is tested).

## Checks

- validate: no issues; build 0 warnings (no size warning); `fmt --check` L1-L4 clean; recorded ("first L4 ...").
- audit (`output/studio_cal/dd05/audit.txt`, oymap 22:38): 0 errors; 2 warnings (below); 29 of 29 sectors reached
  with doors out of the way; infos only click.silent on the clerics' beds (the AskChoice the analysis cannot see).
- Textures: `texture_budget.py`: DD-05 M 25/45, 1/8 new (xmoktap, installed by the lead, no stand-in).
- Session 9 (oymap 23:02): rebuilt once (the Pegasus stand-in, below); validate no issues, build 0 warnings, audit
  (`output/studio_cal/dd05/audit.txt`) 0 errors, the same 2 warnings, 29 of 29 sectors reached with doors out of the
  way; ids.lock.yml unchanged. The root's `worlds/xeen/data_tables/` re-copied (A2 had added 9121's rows since) and
  D1's six files re-linked to the installed D1.

## Playtests

All three 4 of 4 from the scratch root: `output/studio_cal/dd05/run/four_233024` (before the Pegasus rebuild) and
`output/studio_cal/dd05/run/four_233710` (after it, the map as it installs).

- `playtest.yml` (232 steps): the critical path rope → front door (header comment). The walks into Humble's and Pious's
  cells now use `walk_to ... expect: dialog`: the cell's step event opens the plea on the threshold, as on foot.
- `playtest_hostility.yml` (40 steps): at load 22/11/3/1 heretics and 5/3 golems hostile, none peaceful; Humble and
  Pious peaceful, one each, shown. Mok Heretic, Stone Golem, Heretic Priest, Iron Golem and Heretic Lord spawned side
  by side in the hoist room (128 apart, nearer each other than the party): `ai_trace` 0 actor targets in 12 s, none
  hurt (nor Humble, Pious).
- `playtest_exit.yml` (51 steps): (1) the rope window's exit window, OK → D1 at entrance:dd05_rope, a step forward
  north; (2) from the start's save, loaded, in the door hall: the front door without the key gives "Locked, and warded
  from both sides. ..." (tower_opened clear, still in DD-05); with 12338 "... the heretics' wards on the door die ..."
  (tower_opened); a save and a load keep it; the door again: exit window, OK → D1 at entrance:dd05_door, a step
  forward south.

## Pictures

No bake in the root (the lead bakes after install). `output/studio_cal/dd05/shoot.sh <tour>` with
`tools/tour.py rooms|things <name>` (HUD off, every door open), sheets by `tools/sheet.py`:
`output/studio_cal/dd05/shots/rooms1_1..7.jpg` (every room from two corners, every stair from foot and head) and
`things1_1..3.jpg` (the chapel's cone, beams and chandelier, the altar under the daubed sun, the chapel's double doors,
the tapestry walk's three xmoktap, the vestry, the rope window, the alcoves and discs, the mirror, the front door, the
fountains, the cells, the kitchen, the refectory, the guardians); `things3/` the alcoves after the rebuild. Read: the
cone's pyramid of gtemprf with the four tie beams reads as a timber ring round the chandelier; the tapestries and the
sun read whole; the discs lie on their ledges; the Iron Golems clear the door hall's ceiling. One fix: the Pegasus's
`sta1a` drew MM6's 3D fountain (266 high, water jets) on the north ledge; now a stand-in (Waiting on). (`rooms1`
frame 50 is a camera point under the east stair's flight, not a map fault.)

## Waiting on

- **The Golden Pegasus on the north alcove's ledge** (`deco:pegasus`): a stand-in, MM7's gold goblet `7dec48`. No
  shipped decoration shows a golden statuette indoors in this world (`sta1a` is bound to `mm6_deco_fountain.glb`;
  `dec96`, the gold eagle on a ball, has no indoor model and no sprite picture here). The model exists:
  `worlds/xeen/world_items/models/item_xeen_12349.glb` (the item's ground model). Request (lead/A1): a Xeen decoration
  row (the world's range, after 4009, e.g. `xeen_pegasus`) bound in `worlds/xeen/models/indoor_decorations.yml` to that
  model (height about 43); then swap the name in `gen.py` (`deco('pegasus', ...)`) and rebuild. Session 9: S's row
  4012 `xeen_pegasus` exists, but oymap refuses a world decoration in an indoor objects.yml (A1/studio). The events only hide it
  by number (`evt.SetSprite(2, 0)`), so the swap changes nothing else.

## Texture fit exceptions

- `textures.family_switch` on the dead mirror (xkmirror beside its gstntilev frame strips, 2 warnings): the dark strips
  are the mirror's frame (D-37 (2)); kept, as DD-02's.

## Dressing exceptions

None (the audit has no dressing finding).

## Words needed

1. A clicked event on a placed monster (Humble, Pious): workaround a step event on entering the cell plus the bed.

## State and next steps

Session 9, D-52 follow-up (DD-14's sub-agent, 2026-11-21 04:20): **ready to reinstall** (one change: `pan: false` on
`sound:tower_bed`, AUDIO.md "Indoor beds"; rebuilt from `tools/gen.py`, recorded "session 9: the tower bed pan false
(D-48)"). Validate no issues, build 0 warnings, audit of the installed map (`output/studio_cal/dd05/audit.txt`) 0
errors and 0 warnings (infos only). Tests 4 of 4 from a fresh root `output/studio_cal/dd05/root_s9` (`cp -al
assets_dev` 04:15, `worlds/xeen/data_tables/` a real copy; `cycle.sh`, `four.sh`, `shoot.sh` default to it):
playtest 232, playtest_hostility 40, playtest_exit 51 steps (`output/studio_cal/dd05/run/four_042010`, summary
`four_s9c.txt`). **The Pegasus swap is not done:** S's `xeen_pegasus` (row 4012 in
`worlds/xeen/models/decoration_data.txt`) is refused by `oymap validate` and `build` ("there is no decoration named
xeen_pegasus in decoration_data.txt": the studio's indoor objects read only the engine's table, not the world's
`tableContributions` decorations; A1/studio). The ledge keeps the goblet `7dec48` (picture
`output/studio_cal/dd05/shots/s9_ledge_1.jpg`); the swap is one word in `gen.py` once the studio takes world rows.

Session 9 (2026-11-20): **ready to install.** Done: the cell walks fixed in `playtest.yml` (`expect: dialog`),
`playtest_hostility.yml` and `playtest_exit.yml` written, all three 4 of 4 from the root; exits measured on D1; room
and thing tours read; one map change (the Pegasus stand-in, gen.py; rebuilt, recorded "s9: Pegasus stand-in 7dec48");
audit 0 errors. Open: the Pegasus decoration (Waiting on); D1's two doors into DD-05 (A6).

Lead's install/bake/test: `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd05`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd05`, then
`ASSETS=$PWD/assets_dev output/studio_cal/dd05/four.sh`.

## Installed (session 9, lane lead)

- Installed 23:38 (`INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd05`, build `output/studio_cal/dd05/b_233812`: 29 rooms,
  1385 faces, 13 doors, 23 lights, 56 events, 4 chests). Audit of the L4 against assets_dev (`--reach --solve`,
  `output/studio_cal/a8_s9/audit/dd05.txt`): 0 errors, the 2 mirror warnings.
- Baked twice: the first bake (profile as DD-02's: `direct_scale` 2.0, `max_lighting` 1.5) blew the chapel's d22 marble
  near white; the profile lowered as DD-03's (`direct_scale` 1.6, `max_lighting` 1.25; before:
  `output/studio_cal/dd05/xeen_dd05_profile_before_s9.yml`), rebaked 23:41; `stale_bakes` none. Pictures
  `output/studio_cal/dd05/shots/baked_s9b/` (sheet `baked_s9b_a.jpg`): the marble reads pale blue-grey, the tapestries
  and the cone's timber whole.
- Tests from assets_dev 4 of 4 after the second bake: playtest 232, playtest_hostility 40, playtest_exit 51 steps
  (`output/studio_cal/dd05/run/four_234242`).
- Not done while the Pegasus is a stand-in (S's decoration row; "Waiting on"); D1's two doors into DD-05 still sealed
  (A6).

## Reinstalled (session 9, lane lead)

- `pan: false` on `sound:tower_bed` (D-48); reinstalled 04:24 (`b_042410`), baked, 4 of 4 from assets_dev
  (`output/studio_cal/dd05/run/four_042450`), audit 0 / 0. The Pegasus is still the goblet stand-in: S's
  `xeen_pegasus` (world decoration row 4012) is rejected by `oymap validate`/`build` because indoor objects read only
  the engine's decoration table (A1). Swap `deco('pegasus', ...)` in gen.py once the studio reads world rows.

## Session 24 (A8): merge point 35 tests

`playtest.yml`: the walk down the east stair to L1 clears (1,500): a guard at the stair's foot was no longer killed
from L2 (merge point 33's storey-bound clears). Rebuilt under oymap 12:46:47 for A1's room step tops
(`evt:humble_ask`, `evt:pious_ask` on the beds' tops; only the .blv changed), installed 17:15, baked, every test 4 of
4 from assets_dev on merge point 35; audit 0 / 0.

## Session 26 (A8, 2026-11-22)

- D-90 (c): the Golden Pegasus (12349) stands on the north alcove's ledge (0, 1152, 96) and the key to the Western
  Tower (12338) on the altar (-1472, 1216, 2016) as 3D ground items. Gone: the stand-in goblet `deco:pegasus` (ends the
  wait on S's `xeen_pegasus` row), its load-time `SetSprite`, `evt:pegasus`, `evt:ledge_n` and `evt:altar`. A3's
  `q-d20.pegasus` and `q-d6.tower_key` are `map_gives`. `tools/gen.py` `ITEMS_PLACED`.
- Tests: playtest picks both up (`pick_up`; the key from the altar's south side, clear of the Cult Leader's body).
  Installed 00:36, baked, 12/12 from assets_dev; audit 0 / 0.
- Drop pockets: `check_drops` lists the refectory's two benches (40 high beside the table, (352/672, 320) on L2) as
  pockets; the party steps off a bench. A check artifact, no change.

## Session 27 (A8): A3 35th's requests

- `project.yml` qbits `key_found` (113122) and `pegasus_found` (113401) dropped (both are ground items since D-90; A3
  deletes the bits). The Cult Leader preaches at (-1152, 1600), north of the altar walk (was (-1216, 1216), on it): his
  body no longer falls between the walk's end and the key on the altar and takes its click. Generator only (`gen.py`;
  snapshot `output/studio_cal/a8_s27/before/dd05/`). Installed and baked; audit 0/0, check_exits 0, check_drops 0;
  tests 12/12 from assets_dev (`output/studio_cal/a8_s26/run/dd05/c012329`).

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the four chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. Installed,
baked; audit 0/0, check_exits 0, check_drops 0; tests 4 of 4 (12 of 12, output/studio_cal/a8_s26/run/dd05/c021850).
Chest pictures: output/studio_cal/a8_s29/shots/dd05_chests.jpg (all four on the floor against a wall).

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:kitchen_fire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
