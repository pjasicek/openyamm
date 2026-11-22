# DD-04 The Gremlin Court (L4): notes

Lane A8 (agent `agent:xeen-a8-dd04`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd04.graph.yml`) with decider D-26 (`mockups/act3_a8_decisions_a.md`), which wins
where they differ. All four levels are written by one script, `output/studio_cal/dd04/tools/gen.py` (L1 plan and
project; L2 the same with extents and heights; L3 the rooms; L4 objects and wiring); the playtests and this file are
written by hand. `output/studio_cal/dd04/cycle.sh L4` generates, formats, validates, builds, installs into the
scratch root `output/studio_cal/dd04/root` and audits.

## What was built

Map 9153, `xeen_dd04.blv`, class S, on D1 Castleview Vale; Q-D1 The Gremlin Court. Party 19-20, band 14-22,
Gettlewaithe 24, 28 monsters, treasure 2 (the court's treasury 3), music 2.

The graph's ten review rooms as twelve rooms (12 sectors, 12.93 M units², walkable 11.1 M), in the plan frame x east,
y north, the tiny door's sill at y 0; the upper floor at 0, the burrows below at -384. No room of one floor lies over
a room of the other.

| Room | Size | Texture family | Monsters |
| --- | --- | --- | --- |
| The tiny door | 320 × 640, 240 high | burrow (7d08) | — (arrival, the exit) |
| The burrow | crooked, 384-640 wide, 1,664 long | burrow | 4 court Gremlins 11024 |
| Hall of pranks | 1,280 × 1,024 | burrow | 4 court Gremlins, 2 court Saboteurs 11025; chest T2 |
| The waiting room | 768 × 640 | t09 ashlar, plank floor | 3 court Gremlins (heralds) |
| The Gremlin Court | 1,792 × 1,536, 704-832 high | t09 ashlar, beamed roof | Gettlewaithe 11023, 3 Gremlin Guards 11026; the treasury T3 |
| The wall's old cellar | 1,024 × 1,280 and an arm 512 × 1,024 | t09 ashlar | 4 army Gremlins 11027 |
| The larder | 640 × 768 | t09 ashlar | 2 army Gremlins |
| Bolt-hole | ramp 832 long, down 384 | burrow | — |
| The mighty army | 1,536 × 1,280 at -384 | burrow | 5 army Gremlins; pay chest T2 |
| Sappers' tunnel | 320 wide, about 4,100 long | burrow | — |
| Trapdoor stair | 12 steps up 384 | burrow | — |
| The sappers' last dig | 704 × 512, a pool | burrow, water | — |

Critical path: tiny door, burrow, hall of pranks, waiting room (door), court (door). Loops: (1) hall of pranks,
cellar (broken arch), larder (door), court (the servants' hatch, secret), waiting room; (2) burrow, bolt-hole,
barracks, sappers' tunnel, trapdoor stair (trapdoor), larder, cellar, hall of pranks.

Counts: 12 sectors (≤ 15), 12.93 M units² (≤ 20), 28 monsters (15-30), 3 chests (0-3), 5 doors (3-8: waiting room,
court, larder, the secret servants' hatch, the trapdoor), no spawn points (all placed: the court and the army are
rows of their own, A2's). 1 exit.

## Monsters and kill experience

All placed, on A2's rows (D-26): court side 11024 Gremlin 14 (11), 11025 Gremlin Saboteur 18 (2), 11026 Gremlin Guard
22 (3, group 1), Gettlewaithe 11023 24 (group 2, immobile on his dais); army 11027 Gremlin 14 (11: cellar group 10,
larder 11, barracks 12). Court groups 3 (burrow), 4 (hall of pranks), 5 (waiting room). No `hostile` and no map
relations: the world's `relations.yml` decides (court friendly, hostile on 113024, friendly on 113026; army hostile
until 113026).

Kill experience L(L+10): 22 × 336 + 2 × 504 + 3 × 704 + 816 = 11,328, **2.83k per member** of four (MAPS 2.5k; the
graph's 2.83k, +13 %). On the peace route the party kills the 11 army gremlins and the 3 guards: 5,808, 1.45k each.

The map card's slot repeats D1's family (`Xeen Gremlin`, tier a, 2-3, weight 100) for the row only; there are no
spawn markers and the encounter chance is 0 (a rest must not bring D1's hostile gremlins into a court at peace).

## Mechanisms and hooks

- **Court peaceful at load, army hostile** (D-26): by the rows' factions; checked in `playtest_hostility.yml`.
  Gettlewaithe has his own faction `xeen_gremlins_king` (D-37): friendly at load and after `court_peace`, no rule on
  `court_hostile`, so a roused court leaves him on his dais until he is struck himself.
- **Gettlewaithe speaks through his throne.** The studio has no word to give a placed indoor monster its NPC (Words
  needed), so clicking the throne or the dais (`evt:throne`, `evt:dais`) runs `evt.SpeakNPC(4955)` while he lives:
  his first greeting is the challenge (aaze0029:83, A4's `greet[0]`), the second "Back to petition the king?"; A3's
  topics run the three rounds. After his death the throne says the treasury stands beside it, and once the treasury
  is searched it gives `q-d1.throne`'s else_text.
- **`court_hostile` on a blow** (`evt:court_roused`): the engine has no event for "a monster was attacked" (Words
  needed). A timer every second, while neither `court_hostile` nor `court_peace` is set, asks each court actor
  (indices 0-16, the `monster:c..` ids, which sort first) `evt.IsMapActorHostile(i)`; a struck court gremlin turns on
  the party (and rouses its faction near it), the timer sets 113024 and says "The court shrieks for its guards!", and
  A2's relations turn the whole court, guards and king. "The Mayor's demand" and the rude answers set it through
  A3's topics as well. Checked in `playtest_kill.yml` (a blow of 1 at a burrow gremlin) and `playtest.yml`.
- **`q-d1.guards_beaten`**: a timer when group 1 (the three guards) is dead, once.
- **`q-d1.gettlewaithe`**: a timer when `monster:c00_gettlewaithe` is dead, once, with the line "Gettlewaithe,
  Imperator Primus of the Gremlins, topples off his throne of chairs." A load event hides his group once
  `gettlewaithe_slain` is set, so a refill does not bring him back.
- **`q-d1.throne`**: the treasury chest beside the throne (`chest:throne`, T3, 600 gold, two rolls, the 3 Energy
  Disks 12334 of the hook's `map_gives`). Its condition is `throne_searched` or `XeenQuests.can("q-d1.throne")`
  (slain and no peace); refused, it runs the hook for its fail text ("The throne is occupied. Mostly by a very
  nervous gremlin."). The first opening runs the hook (its line, `throne_searched`).
- **`q-d1.court_guards`** has no call (A3: "reads court_hostile"): the guards follow `court_hostile` by the world's
  relations, as every court gremlin does.
- `q-d1.court_entrance` and `q-d1.sabotage` are D1's (A6).
- **The servants' hatch**: a secret slide-up door of ashlar (both faces the wall's own, `secret: true`), hover
  "Loose stones", opened from either side.
- **The trapdoor**: a hinged plank door at the head of the trapdoor stair.
- **The sappers' tunnel ends at water** (D-26: no link to DD-01): a step event on the last dig's pool, "Beyond the
  mud you hear water running: the town's drains."; a quiet running-water sound beyond.
- The "stooping" tiny door is only a look: its passage is 240 high (the party's collision height is 192); the
  audit reaches every sector from the start.

## Qbits and items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | 117040 | the map's own (provisional block 117040-117079): the arrival window once per game |
| `court_won` | 113021 | Q-D1 (read only through the hooks) |
| `court_hostile` | 113024 | Q-D1: set by `evt:court_roused` (and A3's topics) |
| `guards_beaten` | 113025 | Q-D1: `q-d1.guards_beaten` |
| `court_peace` | 113026 | Q-D1: read (the timer stops; A3's "Submit or die" sets it) |
| `gettlewaithe_slain` | 113027 | Q-D1: `q-d1.gettlewaithe`; read by the throne and the load event |
| `throne_searched` | 113028 | Q-D1: `q-d1.throne`; read by the throne and the treasury |

No player bits. Item: Energy Disk 12334 (3, in the treasury). Map variables: only the studio's `once.*`.

## Exit

`exit:d1` on the tiny door's south wall (a gremlin-sized arched door, 96 × 192, t09a03c), the `exit` preset (the
game's window "Do you wish to leave The Gremlin Court?", D-24), to `exit:d1_burrow`: **live** onto D1 at
(2304, 10880, 1153), facing north (90), away from the burrow (`thing:dd04_burrow`, its face at (2304, 10467); the
party lands 413 north of it). Measured with `playtest_exit.yml` (actual 2304, 10880, 1153).

**D1's door into this map** (A6's `door:dd04`): the start point **(0, 256, 0), facing north (90)**, just inside the
tiny door.

Note for A6: D1's sketch has `entrance:dd04_burrow` at [68, 42] facing **s**; the brief asks the arrival to face
away from the burrow, which is north (the party stands north of the burrow's face, outside the wall).

## Textures (19 distinct, 1 new; cap 30, ≤ 4 new)

- Burrows, hall of pranks, bolt-hole, barracks, sappers' tunnel, trapdoor stair: MM7 Tularean Caves (7d08): `cwb1`
  walls and roofs, `cfb1` floors.
- Court, waiting room, wall cellar, larder: D1's t09 grey ashlar (MM8's Darkside town kit): `t09a01` walls over the
  base course `t09b11b`, the town's flags `t09a02b`, `t09a02a` overhead; the court's beamed plank roof `gkp1ceil`
  (MM8; session 7: the carved panel `t09a10a` was a picture meant once, tiled 12-28 times); the waiting room's
  herringbone planks `t09a05b`; the arched plank doors `t09a03c`; plain boards `t09b10a` (benches, table, dais, the
  throne of chairs, the gears, the trapdoor); the sign's plaque `t09b11a`.
- The court's rug before the dais: `carpt01` (MM6's parlour rug, stolen). The graph's "carpet of the mill's sails"
  (`t68a13a`) was tried and dropped: the pale linen read as a glowing white strip in the court (look1).
- The last dig's pool: MM8 water `wtrtyl` (fluid bit).
- **New: `xdmayor`** (A6's, installed and registered in `source/textures.yml`): Mayor Snarfblad's portrait with a
  moustache added, on the court's north wall above the throne. Nothing waits on A6.
- `python3 tools/xeen/texture_budget.py --root output/studio_cal/dd04/root`: DD-04 S 19/30, 1/4 new.

## Original lines

- "I am Gettlewaithe, Imperator Primus of the Gremlins! ..." (dark/aaze0029:83): his first greeting (A4), shown when
  the throne is clicked.
- "Excellent. Your display of respect has earned you your lives. ..." (aaze0029:87), "The answer is no! You will now
  suffer the consequences of your audacity. Guards!" (:93), "Well, um, perhaps I can do something about those
  naughty, naughty pranksters. ..." (:95), "I am always at your service, sir." (:98): A3's topics, heard here.
- "Nothing here." (aaze0029:2): the waiting room's east bench.

## Presentation

Music 2 (map_stats). Placed sounds: the army's fire (`7campfire`), water seeping in the sappers' tunnel (`drip01`),
the drains beyond the last dig (`rushing water loop`, quiet). Lights: 12 (lanterns and sconces in the burrows, the
court's chandelier and the throne, the cellar, the larder, the army's fire, a cold light at the pool). Ambient 9-24:
burrows dim, the court side lit. No bake in the scratch root: the lane lead bakes after install.

## Pictures looked at

`output/studio_cal/dd04/look1_a.jpg`, `look1_b.jpg` (32 shots: every room, the tiny door from inside, each door
closed and open, the hatch closed and open, the trapdoor, the stair, the pool) and `look2_sheet.jpg` (after the
fixes). Fixed after look1: the sailcloth carpet and dais top (glowing white) became a rug and boards; the meander
parquet `t09a10b` on benches, table, throne and trapdoor (read as carved blocks) became plain boards `t09b10a`.
The burrows are dark and the court side flat-lit: no bake in the scratch root.

## Checks (scratch root, `--world xeen`)

- `oymap validate` no issues; `oymap build` 1 warning (the pool's second liquid face: one face of the two written
  with `liquid` lies in the compiled map; the other is merged away, harmless); `oymap audit --reach --solve` no error,
  no warning, faces in one plane 0; every sector reached from the start with every door out of the way (9 of 12 with
  the doors as they start); `fmt --check` clean on L1-L4.
- Dressing (`oymap audit --world xeen`): 0 errors, 0 warnings (barrels, casks, sacks and buckets in pairs by walls;
  nothing in a walking line).
- `scale_bands.py`: largest room (the court, 3.46 M) below the shipped 25th percentile (a class S map); typical
  ceiling at the 71st percentile.
- Playtests (`output/studio_cal/dd04/four.sh`): `playtest.yml` (the army's loop, the peace route, the hatch, out to
  D1), `playtest_kill.yml` (a blow rouses the court, Gettlewaithe killed, the treasury and its disks, a reload),
  `playtest_hostility.yml`, `playtest_exit.yml`: each 4 of 4
  (`output/studio_cal/dd04/four2.out`, after the last change; `four1.out` before the texture fixes).

## Words needed

1. **`monsters[].npc` indoors** (objects.yml): the scene's actor record has `npc_id` (MM7's shipped dungeons use
   it; the outdoor sketch has `npc`), but a placed indoor monster cannot be given one. Workaround: the throne and
   the dais run `evt.SpeakNPC(4955)`; clicking Gettlewaithe himself says nothing. (A1)
2. **An event when a monster is attacked** (a `trigger: attacked` with a group or a monster, or a condition
   `{hostile: {group: n}}`): the engine has none. Workaround: a one-second timer over the court actors' indices with
   `evt.IsMapActorHostile`; the index list must follow the ids (gen.py writes it from the ids, sorted court first).
   (A1, A3)

## Dressing exceptions

None (the audit has no warning).

## DECIDE

- Decided (D-37 (1)): Gettlewaithe has a faction of his own and turns only when struck himself; done in session 7
  (A2's faction, this map's tests). One engine gap remains for A1 (see session 7).

## What the user should look at

- The court: the throne of stacked chairs, the portrait above it, the stolen rug, the chandelier.
- The secret servants' hatch shows the engine's red secret pulse on the court's east wall for a party with
  Perception (as every secret face does).
- Talking to Gettlewaithe means clicking his throne (or the dais), not him.
- A blow at any court gremlin rouses the whole court with a status line.
- The tiny door: a gremlin-sized door in a passage the party fits.

## State and next steps

L4 complete in the scratch root. The lane lead installs into `assets_dev` and bakes; A2 writes the map row from the
slot line (the scratch root carries a test row copied from 9138's form).

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 11 oymap (byte for byte the agent's build), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh dd04`, `install_stage.py`; `b_175051`); `oymap audit --world xeen
  --assets assets_dev --reach --solve` on the installed map: no error or warning (`audit_assets_dev.txt`).
- Baked: `output/studio_cal/a8_s5/bake.sh dd04 <scratch root>` (profile `tools/lighting/baked_indoors/profiles/
  xeen_dd04.yml`, XD-08's values; `--sources assets_source`), `.lighting` and `.bake.json` installed;
  `stale_bakes.py` lists none. Baked pictures `output/studio_cal/dd04/baked_a.jpg`, `baked_b.jpg` (looked at: the
  court, the Mayor's portrait, the waiting room and the stone reads right; the burrows and the sappers' tunnel dim, as
  meant; the pool's water at the tunnel's end).
- A2's row 9153 landed; **playtests from assets_dev 4 of 4**: `playtest_kill` 39 and `playtest_hostility` 27
  (`run/four_175648/`); `playtest` 104 and `playtest_exit` 16 (`run/four_180050/`, after A6 re-baked D1 at 17:59:
  the 17:57 D1 reinstall over its older bake made D1 fail to load for three runs, "cooked for different geometry").
  The exit still lands at (2304, 10880, ~1153) on the new D1.
- **A6's return point** (18:15): the exit lands on D1 at A6's point for D1's event 170, (2048, 11264, 1152) facing
  1536 (south, studio direction 270) (`tools/gen.py`, copy before `gen_before_a6pts.py`). Rebuilt (`b_181514`, only
  the `MoveToMap` line changed), installed; `playtest` 104 and `playtest_exit` 16 from assets_dev 4 of 4
  (`run/four_181739/`).

## Session 7 batch (court roof texture fit, D-37 hostility)

Agent `agent:xeen-a8-dd04`, 2026-11-20. Generator copy before the session: `tools/gen_before_s7.py`; the unchanged
generator reproduced the installed L4 byte for byte (snapshot `output/studio_cal/a8_s7/snap/dd04/`).

- **Texture fit (merge point 16).** The court's hipped roof carried `t09a10a`, MM8's carved meander panel (a picture
  meant once, 64 × 64, that meets itself nowhere), 12-28 times on each of its four faces (1,792 × 779 and 905 × 1,536).
  Stretched once it would be a 64-pixel panel over a whole roof face, so the roof became a tile: MM8's beamed plank
  ceiling `gkp1ceil` (128 × 128, its own size, `scale: 2`: 7 × 3 and 3.5 × 6 copies per face). Texture count stays
  19. Merge point 17: every declared size in the generator is its picture's own; the rebuild's build log shows no
  size warning (its one warning is the pool's liquid face, as before).
- **D-37 (1).** Row 11023 is in A2's `xeen_gremlins_king` (relations.yml: friendly at load and after 113026, no rule
  on 113024). The map's wiring never set him hostile (the relations did), so no wiring change: only notes in the
  generator and the tests. `playtest_hostility.yml` now saves at load and plays two branches: (1) a blow at a burrow
  gremlin sets `court_hostile`, guards, saboteurs and gremlins turn, Gettlewaithe stays friendly (also 6 s later and
  after the guards fall); `guards_beaten`, then "Submit or die" at his throne (event 22) sets `court_peace` and
  `court_won`, and the court and army are friendly; (2) a blow at Gettlewaithe sets `court_hostile` (the timer saw him
  turn) and the court turns. `playtest_kill.yml` now asserts the king still friendly after the burrow blow.
- **Engine gap for A1:** a struck Gettlewaithe does not stay hostile. `IndoorWorldRuntime::
  refreshConditionalMonsterRelations` gives every actor of a faction with any QBit rule its faction's current relation
  whenever any rule switches; `court_hostile` switches the court's rule, so the king (his faction has the
  `court_peace` rule) is put back to friendly a second after the blow (probe `output/studio_cal/dd04/s7_pre/
  probe_king.yml`: hostile right after the blow, friendly after the timer). Fix there: only actors whose faction's
  party relation changed. Branch (2) does not assert his lasting hostility until then (its note says so).
- **Audit** (`oymap audit --assets assets_dev --reach --solve`): before 4 errors (`textures.feature_repeated`, faces
  160-163), 0 warnings; after 0 errors, 0 warnings (the info `texture.squashed` on `t09b10a` stays).
- **Install and tests:** recorded (`ce732ee2`), `b_215210` installed, baked 22:04 (`stale_bakes` lists only XD-09,
  not this map), tests from assets_dev 4 of 4 each (`run/four_220417/`): `playtest` 104, `playtest_kill` 39,
  `playtest_hostility` 70, `playtest_exit` 16 steps.
- **Pictures** (`output/studio_cal/dd04/shots/s7/`, `sheet.jpg`): the court from its door, the roof from below (south,
  the north-east hip, the west face) and Gettlewaithe on his dais before the throne from the side and the front. The
  roof reads as one timber roof; its beams run up the long faces and across the hip ends; no seam or stretch.

## Session 8: the struck king stays hostile (merge point 18)

The probe reran on game 22:38:19 (`output/studio_cal/dd04/s8_probe/`): a blow at Gettlewaithe turns him, the timer sets
`court_hostile` and turns the court, and he is still hostile 11 s later (merge point 18 resets only factions whose
relation really changed). `playtest_hostility.yml` branch (2) now asserts it (right after the court turns and 8 s
later): 76 steps, 4 of 4 from assets_dev (`run/four_224251/`).

## Texture fit exceptions

None (no `textures.*` warning).

## Session 28 (A8): D-89 identity (the court's heaps of stolen things)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, severity 3: "the town's stolen things (the dungeon's
joke) barely visible") asked for the hall heaped with the town's missing things and low crooked burrows with a
child-size first door. In `tools/gen.py`'s "D-89 identity" block; the generator reproduced the installed L4 first
(snapshot `output/studio_cal/a8_s28/before/dd04/`).
- Both south corners of the court heaped: stacked crates (`crate_w64` once per face, four each, two of them turned),
  two cart wheels stacked, a barrel, a keg, a flour sack and a bag each; three more crates in the hall of pranks'
  north-east corner. Baskets and crockery were dropped (no model draws them in Xeen's dungeons); two props first put
  on the hall of pranks' walking line were dropped (`dressing.walking_line`).
- The tiny door (240) and the burrows (416) stay as built: the party's 192 clears them, and lowering them further
  would cut the gremlins' fights.
X
- Installed 02:03 (oymap merge point 42), baked; audit 0 / 0, check_exits 0, check_drops 0, MAW 0, key_npcs 0.
- Tests: `playtest_exit`, `playtest_hostility`, `playtest_kill` 4 of 4 each (`output/studio_cal/a8_s26/run/dd04/c020205`,
  `t020732`); **`playtest` fails at step 60** (`execute_event
  5`, the treasury under the throne while Gettlewaithe lives: no "The throne is occupied." window, `q-d1.throne`'s
  failText). The same run against the map as installed before this session (hard-linked root with the old .blv and
  scene) fails the same way, with 113027/113028 clear: not this map's change. Reported to A3.
- Pictures: before `output/studio_cal/a8_s28/shots/dd04_before.jpg`, after (baked)
  `output/studio_cal/a8_s28/shots/dd04_after.jpg` (tour `output/studio_cal/dd04/s28_before.yml`).

## Session 29 (A8, 2026-11-22)

- `playtest` step 60 (and its twin after the peace): event 5's refusal "The throne is occupied." is a status line
  since A3 35th (`q-d1.throne` has `failStatus = true`: refusal lines of finds default to the status line), so no
  window opens. Not a fault: the two steps now read `status()` and check that 113028 stays clear. All four tests 16/16
  from assets_dev (`output/studio_cal/a8_s26/run/dd04/t021801`). No map change.
