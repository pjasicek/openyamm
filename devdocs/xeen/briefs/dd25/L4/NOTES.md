# DD-25 Bosco's Hall, L4: notes

New town BLV on D5 (the dwarf king's hall in the crag over his terrace; source dark/aaze0013:13-17), built with the Map
Studio from `devdocs/xeen/mockups/act5_graphs/dd25.graph.yml` and decider D-62 (`mockups/act5_a8_decisions_b.md`,
which wins) by `agent:xeen-a8-dd25` (lane A8 session 13), 2026-11-21. Key `dd25`, project `xeen_dd25`, stem
`xeen_dd25.blv`, map card 9122 (A2's real row: encounter 0, no slots, treasure "-", music 31), world `xeen`.

## State and next steps

**Ready to install** (from the scratch root, all checks clean). Every project file of L1-L4 except the playtests and
these notes is written by `output/studio_cal/dd25/tools/gen.py` (geo.py: rooms and openings; dress.py: objects and
wiring). Recorded (`agent:xeen-a8-dd25`). Validate: no issues (L1-L4); build 0 warnings; `fmt --check` clean; audit of
the installed map (`output/studio_cal/dd25/audit.txt`) and of the project (`audit_project.txt`) with `--reach
--solve`: **0 errors, 0 warnings** (texture fit, doors, lights, dressing), infos only (`click.silent` on the six house
doors: they open a house screen).

Playtests from the root, **4 of 4 each**: `playtest` (104 checks), `playtest_goblet` (35), `playtest_hostility` (37):
`output/studio_cal/dd25/run/four_052136`.

**The lead:** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd25`, then `flock output/studio_cal/a8_s5/lights/post.lock
output/studio_cal/a8_s5/lights/post.sh dd25` (bake profile: post.sh's default copy of `xeen_xd08.yml`; it runs
`ASSETS=$PWD/assets_dev output/studio_cal/dd25/four.sh`; `LOCK=none` if the caller already holds the session's game
lock). Pictures of the baked map: `output/studio_cal/dd25/shoot.sh t1` (and `t2`) with `ASSETS=$PWD/assets_dev`.
**Before the playtests pass from assets_dev, A4's house rows 4701-4706 must be there** (Waiting on, below).

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd25/cycle.sh` (gen, fmt, validate, build, install into the root,
audit, record; `LEVELS="L1 L2 L3 L4"` for all). `python3 output/studio_cal/dd25/tools/sync_root.py` refreshes the root
from assets_dev (relinks changed world files, copies the tables afresh, writes the test house rows).

## What was built

One frame: x east, y north, z 0 = the gate's sill (D5's 2688). 10 rooms (sectors):

- **Gate passage** (512 x 896, ceiling 384): the gate's two leaves on the east wall at x 2304 (two exit faces, `t09a03a`
  left and `t09a03b` right as seen from inside, 192 x 320 each; the `exit` preset to D5), the arrival
  `entrance:d5_bosco` at (2048, 0, 0) facing west, two guards in the corners by the gate.
- **Gate hall** (768 x 1280): the Alehall's front (4702) on the south wall, the first door from the gate (about 900);
  a pair of ale barrels beside it to the east, never before the door; the wide arch west to the great hall, the arch
  north to the smiths' gallery.
- **Great hall** (2048 x 1536, ceiling 768): the round hearth (7cdb, a campfire on top) in the middle, the plain well
  against the south wall (7wtrtyl in a cwb kerb), three benches by the walls, two chandeliers, two townsfolk.
- **Smiths' gallery** (2176 x 512): Bosco's Forge (4701, hdp1b/hdp1d under shingle eaves, sgweapon) and the
  Mailwright's Burrow (4705, hdp2b/hdp2d) on the north wall, 768 apart; between them the **forge bay** (a low recess,
  its fire and pulsing glow inside); an anvil block by the wall west of the Forge; one townsfolk at the west end.
  The loop: gate hall, great hall, smiths' gallery.
- **Burrow lane** (1280 x 512): the Tinker's Burrow (4706) on the south wall; one townsfolk; the **guild stair** (12
  steps, 0 to -384) from its west end down to the **Deep Guild hall** (1280 x 1024 at -384): the Deep Guild of Earth's
  door (4703, hdm1b/hdm1d, sgearth) on the west wall, the crystal vein (crclstr, crys5, crys6) by the north wall, two
  floor candle stands.
- **King's steps** (four steps up 128) to the throne hall's two hinged leaves (`hdr1dl|hdr1dr`, opening apart).
- **Throne hall** (1536 x 1280 at z 128, ceiling 768 over its floor): a three-step dais across the west end (levels at
  +32, +64, +96); Bosco's empty throne on it (seat and a carved hdr1b back) under his banner (`xdbosban`, once, 160 x
  320); the King's Hall door (4704, hdr1b front, hdm1d door) behind the dais, south of the throne; the long tasting
  table on the north wall (two goblets, two plates) and the taster's stool; the Chalice (7dec48, hidden) in the
  table's middle; two braziers (flamb00) on the floor by the dais; two guards inside the leaves.

House doors are clicked wall panels (A4's door ids; `evt.EnterHouse`, as XD-07). Each front is three panels laid once
(160 x 320, the 128 x 256 pictures at 1.25), the timber fronts under an 80-high shingle band (hhm1rf), the services'
signs (64 x 64 at 96) above.

## Measurements

`oymap metrics` (`metrics.json`): **10 sectors** (S 6-15), floor **10.4 M units²** of rooms (12.0 with platform and
level tops; S 7-20), 1 loop; **8 doors**: the gate (two leaves, the exit), the throne hall's hinged pair, six house
doors. 0 chests, 0 counted monsters, kill XP 0. Lights: 11 room lights, 14 sconce lights, 4 glows (hearth, forge,
braziers, crystal), plus the candle stands' own: 31. Decorations: 32 (14 sconces, 2 chandeliers, 2 braziers, 2 candle
stands, 2 fires, 3 crystals, 2 barrels, 4 table pieces, the Chalice). Textures (`tools/xeen/texture_budget.py --root
output/studio_cal/dd25/root --map DD-25`): **27 of 30, 1 new** (`xdbosban`, the lead's, linked into the root).

| Who | Row | Where | Count |
|---|---|---|---|
| Bosco's Guard | 11054 (A2's, faction xeen_bosco_hall, `stand`) | gate passage (2176, ±384), throne hall (-2176, ±416); immobile, group 10 | 4 (uncounted) |
| Peasant Dwarf | 322, 313, 325, 316 (MM7 engine rows) | great hall NW (-1088, 560) and by the well (608, -576), gallery west end (-400, 1232), lane east end (-112, -1264); immobile, group 11 | 4 (uncounted) |

Walking lines: the guards and townsfolk stand off the lines between the openings (384 clear where the room allows;
the gate guards 384 either side of the arrival line, the throne guards 416 off the door line).

Exit, measured (`playtest.yml`): out by the leave window to D5 at **(-512, 9216, 2689) facing 0** (east,
`entrance:dd25_door`). Inside arrival for A6: `entrance:d5_bosco` **(2048, 0, 0) facing 1024** (west): D5's
`door:dd25` gets `into: {map: xeen_dd25.blv, arrival: entrance:d5_bosco}`. Map qbit used: 117680 `arrived_once` (A3's
`dd25_arrived_once`); read: 113343 (`q-d17.done`).

## Mechanisms and texts

- Arrival (`evt:arrive`, a one-shot timer while 117680 is clear): A3's `dd25.arrival` (its line, sets 117680).
- Throne (`platform:throne` and its back, hover "Bosco's throne"): A3's `dd25.throne`. Well (hover "Well"): A3's
  `dd25.well`. All three lines are A3's hooks (`source/npcs/dd25.yml`); none inline.
- Chalice: `evt:chalice` (load) shows `deco:chalice` while 113343 is set.
- Six house doors: `evt.EnterHouse(4701-4706)`. A residence with one resident opens straight onto him (the engine):
  the Mailwright (5405), the Tinker (5406) and Bosco (5401) talk at once; the services show their house screens.
- No change after Q-D17's oath (Q38).

## Waiting on

- **A4: house rows 4701-4706.** `source/towns/dd25.yml` is `planned: true`, so `data_tables/house_data.txt` and
  `house_animations.txt` have no rows for the six houses yet. The root holds **test rows** written by A4's own
  generator with the flag dropped in memory (`tools/house_rows.py`; also the npc house column of 5401-5406). A4 drops
  `planned: true` (and fills `arrivals: d5_bosco` with (2048, 0, 0), direction 1024) when the map installs.
- **S:** the four Peasant Dwarf bindings for Xeen (they draw now as MM7's peasant sprites, not dwarves: not the map's
  fault) and 11054's recolour (the guards draw now on `xeen_dwa1`'s base skin).
- **A6:** D5's `door:dd25` into this map (above).

## Town feel exceptions

TOWN_FEEL 5c's small-town figures applied by hand (town_feel.py reads ODMs only; D-62 Q32):
- Services in town: 3 (Forge, Alehall, Deep Guild) against 5..25: WORLD_DESIGN 5.2's three services win (D-62 Q32).
- Enterable residences: 3 (King's Hall, Mailwright, Tinker) against 6..56: WORLD_DESIGN's two plus the King's Hall
  (D-62 Q32, A4's towns.py takes 3).
- Service to nearest service, median 2,132 (Alehall-Forge 2,132; Deep Guild-Forge 4,899): inside 854..2424. The tavern
  is the first door from the gate (TOWN_FEEL 4).

## Texture fit exceptions

None (0 errors, 0 warnings). The gate's right leaf is `t09a03b` (the pair's own right-hand picture) rather than
`t09a03a` mirrored: exit faces take a surface, and only door `pictures` can mirror (DECIDE 1).

## Dressing exceptions

None (the audit flags no prop; the hearth, the well, the benches, the table and the anvil are blocks, off the lines).

## Sounds for AU

Beds `xeen_amb_mine` (great hall, throne hall, Deep Guild; `pan: false`), the Alehall's murmur `xeen_amb_tavern` at its
door, campfire at the hearth and in the forge bay, and the forge's hammer as the shipped `metal vs metal01l` with a
2-6 s wait in the bay. AU may give a distant hammering loop in its place (D-62).

## DECIDE (cheaper-to-reverse options taken)

1. The gate's leaves: `t09a03a` + `t09a03b` (one texture more) since an exit face cannot mirror; the alternative is a
   hinged pair `t09a03a` mirrored on an opening to a porch with the exit behind it (one sector and one door more).
2. The King's Hall door stands on the dais south of the throne (west wall), not straight behind it, where the throne's
   back would hide it.
3. Door pictures where the graph named wall strips: King's Hall `hdm1d` in an `hdr1b` front (the graph's `hdp1er` is an
   end strip), Mailwright and Tinker `hdp2d` in `hdp2b`, the Deep Guild `hdm1d` in `hdm1b`.
4. Hostility: a blow on one townsfolk turns all four Peasant Dwarves (MM7's peasant faction; they flee as Wimps); the
   guards stay peaceful. A blow on a gate guard turns the two gate guards only (not the throne pair, not the
   townsfolk). The test asserts exactly this.

## What the user should look at

The house fronts (eaves, signs) and the forge bay; the throne on its dais under the banner (plank seat and carved
back); the Chalice on the table after Q-D17; the peasant townsfolk (MM7 sprites until S binds dwarves).

## Session 21 (A8): AU's sounds

`sound:anvil` is AU's `xeen_forge_hall_loop` (radius 2,400, inner 500, volume 0.35, no wait; was the shipped `metal vs metal01l` with a wait). Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 28 (A8): D-89 identity (raw-rock halls)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, severity 3: "brick corridors with timber house fronts:
a town street, not a dwarf hall in the crag") asked for 7d24's raw-rock vaults over the great hall and the lane, brick
only on the house fronts, rock-cut pillars and a higher hall, forge glow and anvils in the smiths' gallery. In
`tools/geo.py`'s "D-89 identity" block (+ one light in `dress.py`, `identity:` in `gen.py`); the generator reproduced
the installed L4 first (snapshot `output/studio_cal/a8_s28/before/dd25/`).
- `theme:hall` (gate passage, gate hall, great hall, smiths' gallery, King's steps): walls in 7d24's raw rock `cwb1`
  over a 96 dressed-stone base course (`cwb`); the timber corner strips gone. Dressed stone stays on the house fronts
  and in the throne hall (`theme:throne`).
- The great hall 1,024 high (was 768) under a raw-rock vault to 1,344 along its east-west ridge, on four rock-cut
  octagonal pillars at (-1024, ±352), (384, 384), (576, -320), clear of the playtests' walking lines (a first
  placement at (-768, 416) blocked `playtest_hostility`'s walk to (-800, 400)). The burrow lane under a rock vault
  (640 at its ridge).
- Two anvils (stone block, flared iron top `xnrustirn`) flank the forge bay's mouth, a pulsing forge-glow light on them.
- `identity: {shape: hall, family: 7d24}`.
- `playtest.yml`: Bosco's Forge (4701) and the Deep Guild of Earth (4703) now open straight onto their one resident
  (Durgan 5402, Stonebeard 5404) instead of the house window (changed in data outside this map around 01:50, the
  binary unchanged); the two asserts follow it.
- Installed 01:50, baked; audit 0 / 0, check_exits 0, check_drops 0, MAW 0, key_npcs 0; tests from assets_dev 12 of 12
  (`output/studio_cal/a8_s26/run/dd25/t015539`).
- Pictures: before `output/studio_cal/a8_s28/shots/dd25_before.jpg`, after (baked)
  `output/studio_cal/a8_s28/shots/dd25_after.jpg` (tour `shots/t1.yml`).

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:hearth_fire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Fixtures without a click: `deco:forge_fire`. Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
