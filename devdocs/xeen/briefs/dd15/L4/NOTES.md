# DD-15 Great Pyramid, L4: notes

New L dungeon on D5 (the source's dark maze0083-0086: the Royal Pyramid, the registry level, the Ancient pad maze and
the Dragon Pharaoh's apartments), story M28 (and M30, M36: the Pharaoh), built with the Map Studio from
`devdocs/xeen/mockups/act5_graphs/dd15.graph.yml` and decider D-61 (`mockups/act5_a8_decisions.md`, which wins) by
`agent:xeen-a8-dd15` (lane A8 session 12), 2026-11-21. Key `dd15`, project `xeen_dd15`, stem `xeen_dd15.blv`,
map_stats 9168 (A2's row), world `xeen`, music 46.

## State and next steps

**Done: ready to install.** Every project file of L1-L4 except the playtests and these notes is written by the
generator (`output/studio_cal/dd15/tools/gen.py`, `geo.py`, `dress.py`); recorded (`agent:xeen-a8-dd15`). Validate L1-L4:
no issues; build: 0 warnings (no "two sizes for one texture"); audit (`--reach --solve`, `output/studio_cal/dd15/audit.txt`):
**0 errors**, 5 warnings (kept, below); `fmt --check` clean.

**Installed and baked (A8 session 15, D-66 item 8):** the bake profile
`tools/lighting/baked_indoors/profiles/xeen_dd15.yml` is `direct_scale` 1.2, `max_lighting` 1.0 (was 1.6 / 1.25; the
rest unchanged); rebaked from assets_dev, 4 of 4 (342/20/47/39, `output/studio_cal/dd15/run/four_063855`), merge
point 27's Lua (peaceful groups once per fill) installed with it. Baked tour `output/studio_cal/dd15/shots/baked3_rooms/`
(sheet `output/studio_cal/a8_s15/dd15_baked3_sheet.jpg`), measured by `output/studio_cal/a8_s15/floor_luma.py`: the floor
patch above the portrait frame is within +4 % of its texture's mean luma in the antechamber, throne hall, bedchamber
(`egyflora` 113: 112-117), atrium (`egyflore` 132: 134-137) and galleries (`egyflord` 147: 148-149), against +20-27 %
on the old profile; no clipped 16 x 16 block (mean >= 250) in the lower view. `egyflora` reads as its own saturated
blue-and-white tile, no glare: no `xdpyrflr` needed.

**Scratch root** `output/studio_cal/dd15/root` (`cp -al assets_dev` 04:45; `worlds/xeen/data_tables/` a real copy;
refreshed from assets_dev by `tools/sync_root.py` at 05:12 and 05:31: A3's m28 hooks and helpers, D7, A2's row 9168).

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd15`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd15` (bake, then
`four.sh` from assets_dev), then the baked tour `ASSETS=$PWD/assets_dev output/studio_cal/dd15/shoot.sh things` (and
`rooms`), sheets with `python3 output/studio_cal/dd15/tools/sheet.py output/studio_cal/dd15/shots/things <prefix>`.

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd15/cycle.sh` (regenerates L4 from the generator, fmt, validate,
build, install into the root, audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against `.oymap/last` first if
anyone edited it by hand. `four.sh` (`ASSETS=`, `N=`, `TESTS=`; every game inside `a8_s9/slot.sh`), `shoot.sh <tour>`
(`tools/tour.py rooms|things <name>` writes the tour), `tools/texsheet.py`, `tools/sync_root.py`.

## What was built

One BLV of four stepped floors 768 apart in one frame (x east, y north, z up), each smaller than the one below. Rooms
are rectangles (the sky corridor an L), 128 walls; the split halls (atrium x4, galleries x2, number hall x2,
processional x3, cloister x2, pad hall x3, antechamber x2, throne hall x3) touch and open on their whole length.

- **L1, the Royal Pyramid (0), MM6's Tomb of VARN:** the entrance hall inside the green doors (north wall y 5120; a
  porch behind them that is never entered: the doors' click is the exit), Reception (west, benches, the history statue)
  and Information (east, the counter and the strongbox), the four torch chapels in the corners (each a lever and two
  niche panels; the plaque in the north-east one), the Visitor's Atrium (four sectors, four brazier stands), the ring:
  the west gallery, the south gallery (the atrium's south door, the stair door), the number hall (eight niches on its
  east wall, the two rule statues on its west wall), the Overseer's Office (desk and note) and vault off the south-east
  chapel; behind the stair door the grand stair (0 to 768, two storeys, a head across its north end) and the Pharaoh's
  lift shaft (0 to 2304) east of it.
- **L2, the registry level (768):** the stair head, the processional (three sectors, four verse statues), the registry
  room (the bronze door, the brass plaque `xdregplq`), the registry stair (768 to 1536), the west tomb (six sarcophagi,
  the chest), the east tomb (the gilded sarcophagus), the north cloister (two sectors, four columns), the embalmers'
  room (table, jars, the salts' find).
- **L3, the pad maze (1536), the Ancient sw kit:** the maze landing, the pad hall (three sectors; four pads: sun
  `swcirc1`, eye `egyswbof` x8, scarab `swfloor6`, bird `egyflorb` x2), the five sealed cells (sun: chest; eye: the
  Overseer's map on a screen; scarab: the weapon rack; bird: the second bird; far: the apex stair's door), each with a
  pad back (`swcirc2`) to the hall's landing spot (-960, 640); the apex stair (1536 to 2304).
- **L4, the Pharaoh's apartments (2304):** the apex landing, the antechamber (two sectors, four gilded columns, the
  book stand, the lift's gate and call button), the throne hall's great doors (egydrlgl|egydrlgr), the throne hall
  (three sectors, 896 high: the gilded dais and throne at its north end, the Pharaoh before it, the vat), the bedchamber
  (bed, tapestry, wall safe, the carved button, the secret door), the sky corridor (sw kit, the sky door at its north
  end).

## Measurements

`oymap metrics` (`output/studio_cal/dd15/metrics.json`): **51 sectors** (L 50-75; the porch counts; the graph's "about
58" is not met), **125-132 M units² of floor** (L 120-200; geo.py 125.3 by outline, metrics 132.3 with the stair
heads), 5 components (the cells are joined by pads), **21 doors** (35 door records: eight hinged pairs, the lift, the
switches), 5 chests, 10 local teleports, 82 bound events, **70 placed monsters** + the Pharaoh. Textures
(`python3 tools/xeen/texture_budget.py --root output/studio_cal/dd15/root --map DD-15`): **60 of 70, 1 new**
(`xdregplq`); the graph planned about 40.

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Tomb Mummy | 11270 | 42 | 2,184 | L1 20 (8 hidden in the chapels' niches), L2 10, L3 4 | 34 |
| Pyramid Guard | 11271 | 52 | 3,224 | L1 10, L2 8, L3 4, L4 2 | 24 |
| Ghost Mummy | 11273 | 62 | 4,464 | L2 2 (cloister, embalmers), L3 4 (pad hall, eye cell) | 6 |
| Royal Mummy | 11272 | 65 | 4,875 | L4: apex landing 2, antechamber 4 | 6 |
| Dragon Pharaoh | 11919 | - | - | throne hall, npc 5453, peaceful, immobile, unkillable | 1 (not counted) |

By floor: L1 30, L2 20, L3 12, L4 8 (the graph's). Quiet: the entrance hall, the throne hall, the bedchamber, the sky
corridor. **Kill XP:** 207,666 for the party, **51.92k per member** (D-61: 50.4k, +3.0 %).

Rest encounters (`project.yml`, = A2's row 9168): `{monster: Xeen Mummy, tier: 2, per_marker: [2, 3], weight: 100}`,
encounter 10 %, treasure 5, lock 12, trap 6, perception 12, music 46.

## Mechanisms

- **Arrival** (`evt:welcome_first`, timer once): the first arrival sets 117560 and calls A3's `m28.welcome_statue`
  (the welcome statue's window); clicked, the statue says it again.
- **The green doors** (`door:green`, two hinged leaves of A6's `xdpyrdor`, the wing mirrored on the right leaf): their
  click is the exit (`evt:exit_green`, `{exit: exit:d5_door}`: the game's leave window, D-24) to D5's
  entrance:dd15_door; the leaves never open.
- **The torches** (D-61 Q2): four plate levers (`egyswbof`, lit `egyswbon`), one on each chapel's lever wall: one way,
  each sets its map qbit (117561 ne, 117562 nw, 117563 sw, 117564 se), shows the chapel's two niche mummies (groups
  21-24, actors 33-40), shows the hidden torch over the lever and the atrium's brazier (`flamb00` on its stand) and
  switches the brazier's light on, plays `xeen_fire_ignite`; a second pull "The lever is stuck." (aaze0083:39). When
  all four bits are set the lever's Lua calls `m28.torches` (once, 111561). `evt:torch_<k>_load` re-shows each lit
  torch's pair, torch, brazier and light on every load (D-18). The plaque by the north-east lever: `m28.torch_plaque`.
- **The stair door** (two leaves of xdpyrdor): `m28.stair_door` (A3: "Access denied!" until 111561); `evt:stair_open`
  (timer) opens it once 111561 is set and on every load after.
- **The number hall** (optional, D-61 Q3): eight niche panels each run A3's `Xeen.pyramidNiche(1-8, ...)` (117565-117572;
  the eighth calls `m28.niches`, 117573); `evt:vault_open` (timer) opens the vault door once 117573 is set; before it
  the door says "The vault door is locked. Eight numbers bolt it.". Answer-givers: the rule statues
  (`m28.rule_statue_1/2`) and the Overseer's note (`m28.overseer_note`).
- **The registry** (on the path): the bronze door's click asks (message "A bronze door with a lock of numbered keys.
  Above it, in raised letters: STARFLEET REGISTRY NUMBER NCC.", ask "Registry?", answers 1701, NCC-1701, NCC1701,
  NCC 1701); right: `m28.registry_lock` (111562) and the door slides up; wrong: "Incorrect!" (aaze0084:7).
  `evt:registry_open` keeps it open on later loads. The plaque: `m28.registry_plaque`.
- **The pad maze:** `m28.maze` on the first step into the pad hall (it sets 117576 itself). Pads are 256 plates with
  `teleport` step events (in-map, party facing south) and the `Teleport` sound; every cell's pad back lands at
  (-960, 640, 1536). The eye cell's screen: `m28.pad_map`. The scarab cell's rack: one random T5 weapon (kind 20) once
  (117578), then "Nothing here.".
- **The Pharaoh's lift** (D-61 Q4): `lift:cage` (384 square, travel 2304) in the shaft; the top gate `door:lift_gate`
  (xwcage bars) moves with it. Call buttons at the foot (stair room) and the top (antechamber), ride buttons in the cage;
  each asks `XeenQuests.can("m28.lift")` (117577), else the hook's line "A gilded cage. It answers only to the
  Pharaoh's guests.". **The throne hall's first entry** (`evt:throne_reached`, step on its three sectors) calls
  `m28.audience` (117577).
- **The Dragon Pharaoh** (11919, `npc: 5453`, actor 49): before his throne on the dais; peaceful, immobile, group 50;
  `evt:figures_load` makes him unkillable on every load (P5's way). His topics are A3's.
- **The Brew of Pure Power** (D-61 Q6 (b)): the vat's first click in a visit `m28.brew` (the warning, sets the map
  variable `brew_warned`, cleared on every load by `evt:brew_reset`); a second click `m28.brew_drink` (50 fire to the
  clicking member, "... He did warn you.") and the fire sound.
- **The bedchamber:** the tapestry `m28.tapestry`; the bed "Nothing here." (aaze0086:3); the wall safe (`chest:safe`,
  container 0) runs A3's `Xeen.pharaohSafe` (20-30-1; "No Luck."; `m28.safe`, 117574) and opens its chest; the carved
  button opens the secret door to the sky corridor for good (117575, `evt:secret_open` on later loads).
- **The Prime Directive:** the book stand calls `m28.prime_directive` (A3: once 111565, then its else text).
- **The sky door** (D-58, D-61 Q9; D7 installed 04:53, the lead's change of brief): before m30.done the hook
  `d7.sky_door_dd15` fails with "Access Denied!"; after it the map asks "Step out onto the Skyroads?" (Yes: the hook,
  then `evt.MoveToMap(11424, 2560, 1408, 1024, ..., "xeen_d7.blv", {direct = true})`; No: nothing). D7's door:dd15
  comes back to `entrance:d7_sky`.

## Arrivals and exits

| Name | Where | Facing |
|---|---|---|
| entrance:d5_door (and start) | (0, 4736, 0), entrance hall, 384 inside the green doors | 1536 (south) |
| entrance:d7_sky | (0, 2944, 2304), sky corridor, 256 inside the sky door | 1536 (toward the throne) |
| exit to D5 (green doors) | measured: D5 (0, -7168, 1249) | 512 |
| exit to D7 (sky door, after m30.done) | measured: D7 (11424, 2560, 1408) | 1024 |

D5's door:dd15 (A6) is still its sealed line ("The green doors do not move ..."): A6 points it at entrance:d5_door.

## Playtests

`output/studio_cal/dd15/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map xeen_dd15.blv`;
logs `output/studio_cal/dd15/run/four_*`, summaries `four_1.txt` (the build before the statue and pad fixes, 16/16)
and `four_2.txt`, `four_3.txt` (the final build).

| Test | Checks | What |
|---|---|---|
| `playtest.yml` | 342 | starts on D5, moves in to entrance:d5_door (position and facing); the welcome window (117560); the stair door "Access denied!"; the four torches (each pair hidden then shown, a second pull stuck; the fourth: m28.torches' window, 111561, the stair door open); the lift refused at the foot; up the grand stair; the processional; the registry wrong ("Incorrect!") then 1701 (111562, the door open), the plaque; up the registry stair; m28.maze (117576); every pad to its cell (sun: the chest; eye: the map; scarab: the find once, then "Nothing here.") and back, the bird, the second bird to the far cell and its pad back; the apex stair; the book; the lift refused at the top; the great doors, the throne hall (117577); the Pharaoh's The orb ("Bring it."); the Brew's two clicks (full health, the warning, still full, the drink: not full); the tapestry, the bed, the safe ("No Luck.", then 20-30-1: 117574 and the chest's gold), the button (117575, the secret door open), through it; the lift called up, down to the grand stair (z 0), up again (z 2304); out by the green doors to D5 (0, -7168) facing 512 |
| `playtest_reload.yml` | 20 | the north-east torch: its pair hidden, shown by the lever, the lever stuck; a reload: 117561 kept, the pair still shown, alive and hostile, the north-west pair still hidden |
| `playtest_sky.yml` | 47 | before m30.done the sky door's "Access Denied!"; with 111600 the question, No stays, Yes lands on D7 at (11424, 2560) facing 1024; D7's way back in: entrance:d7_sky (0, 2944, 2304) facing 1536 |
| `playtest_hostility.yml` | 39 | 34 / 24 / 6 / 6 mummies hostile at load (the hidden niche eight counted), none peaceful; the Pharaoh peaceful, hp 880; the four kinds side by side in the throne hall do not fight each other or him; the Pharaoh struck 40 times: hp 880, still peaceful |

The pads are crossed in the tests by a short forward step from 48 outside the pad's edge (`movement_segment` with
`loose_tolerance`, its stop the cell's landing spot).

## Families and textures

MM6's Tomb of VARN (`egy*`, A6's assign): `egybiga` halls, `egywalg1` Reception/Information, `egywlf` atrium, `egywld`
chapels, `egymeda` galleries, `egywla` number hall, `egywlj` offices, `egybigb` stairs, `egywlh` processional (once up
the wall), `egywle` tombs, `egywlc` the Pharaoh's rooms; floors `egyflord`, `egyflore`, `egyflorc`, `egyflorf`, `egyflora`;
ceilings `egyceilb`, `egyceild`; trims `egytrmc`; `egywalgm` furniture; `egycol64` columns; doors `egydrsmc`, `egydrsmd`,
`egydrsml|egydrsmr`, `egydrlgl|egydrlgr`; niches `egywlspa`, `egywlspb`, `egyspca`; tapestry `egywlspc`; plaque frame
`egywlhle`; levers `egyswbof`/`egyswbon`. A6's `xdpyrdor` (green doors, stair door), `xngold5` (dais, throne, vat, the
cage floor, the gilded sarcophagus), `xwcage` (the lift gate). The Ancient kit on L3, the apex stair and the sky
corridor: `swll4dk`, `swfloor2b`, `swceilf`, `swdoorc`, `swankdk`, `swdoora` (sky door), `swpnl` (rack), `trekscrn`
(the pad map), pads `swcirc1`, `swcirc2`, `swfloor6`. New: **`xdregplq`** (the lead's, 128 x 64), once, whole.

## Texture fit exceptions

- `textures.family_switch` (trekscrn on swll4dk in the eye cell): the Overseer's map is a screen hung on the steel wall;
  the colour change is the screen's.

## Audit warnings kept

- `question.answer` x4 (the registry door's 1701, NCC-1701, NCC1701, NCC 1701): the answer is given by the plaque beside
  the door (A3's `m28.registry_plaque`: "REGISTRY NCC-1701 ... the lock wants the number") and the plaque's own picture;
  the audit does not read hook texts.

## Dressing exceptions

None (audit: 0 dressing findings).

## Lines for A3 (map-local, ORIGINAL_LINES)

- The verse statues: aaze0084:1-4 (window on click, status line on the step before each).
- The registry: message "A bronze door with a lock of numbered keys. Above it, in raised letters: STARFLEET REGISTRY
  NUMBER NCC." (after aaze0084:5), ask "Registry?", "Incorrect!" (aaze0084:7), "The registry door stands open.".
- The torches: "The torch flares up. In the niches, something stirs!", "The lever is stuck." (aaze0083:39).
- The pads: "The glyph of the sun|eye|scarab|bird flares beneath you, and the hall is gone.", "The second bird flares
  beneath you.", "The pad sets you down in the pad hall.".
- The rack: "Among the guards' rusted spears, one weapon is worth taking." / "Nothing here." (aaze0086:3).
- The vault door: "The vault door is locked. Eight numbers bolt it."; the throne: "The Pharaoh's throne. He is using it.";
  the bed: "Nothing here." (aaze0086:3); the button: "Click. Beside the button, a panel of the wall slides aside." /
  "The button is pressed in."; the lift: "The gilded cage sinks down the shaft to you." / "climbs the shaft to you." /
  "climbs to the Pharaoh's apartments." / "sinks to the grand stair."; the embalmers' jar: "A jar of embalming salts,
  and a purse the embalmers hid under it. (+400 gold)"; the sky door's question "Step out onto the Skyroads?" (the
  hook's own).
- Titles: "Reception", "Information", "Overseer's Office", "Visitor's Atrium" (the atrium's south door) (aaze0083:1-4),
  "Exit the Great Pyramid" (aaze0083:0), "Statue", "Bubbling Vat", "Ornate Bed", "Tapestry", "Wall Safe", "Book",
  "Button" (aaze0084:0, aaze0086).

## Sounds for AU

Torch ignition `xeen_fire_ignite` (also on the Brew's drink); the pads `Teleport`; the vat `bubbling cauldron01` (a
placed point sound); the lift `xeen_lift`; beds `xeen_amb_necropolis` (L1 north and south, L2, L4) and
`xeen_barrier_loop` (L3), all `pan: false`; wind at the sky door `whistling wind`.

## DECIDE (cheaper to reverse; listed in the report)

1. The green doors never open: their click is the exit (the porch behind them is a closed sector).
2. The talking statues are figures in a niche (`egywlspb` wall panels, step plates before them): the world has no
   Egyptian statue decoration (7dec54/55 are MM7's dwarves). S could make one later; the events would keep their ids.
3. The welcome statue speaks once by itself on the first arrival (117560), then on a click.
4. The sky door asks with the map's own Yes/No and moves to D7 directly (no second leave window).
5. The embalmers' find is 400 gold (the graph's "salts, a reagent").
6. Sectors 51 and textures 60 of 70 (both in the band; the graph's 58 and 40 are not met).

## What the user should look at

The green doors from inside, the atrium with the braziers lit (light all four torches), the chapels' niche mummies
waking, the registry plaque, the pad hall from the landing, the throne hall with the Pharaoh, the lift ride.

## Session 21 (A8): AU's sounds

The four torch levers play AU's `xeen_torch_light` (was `xeen_fire_ignite`, which stays on the Brew's drink); the pads and the vat unchanged. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 24 (A8): merge point 35 tests

`playtest.yml`: the walk off the cage at the shaft's foot clears (1,500): a ground-floor guard met it, no longer
killed by the clear at the top (merge point 33). Rebuilt under oymap 12:46:47 for A1's room step tops
(`evt:throne_reached` on the dais; only the .blv changed), installed 17:15, baked, every test 4 of 4 from assets_dev
on merge point 35; audit 0 / 5 (as before).

## Session 26 (A8, 2026-11-22)

- D-89 (INWARD): the antechamber's door on L4 (`door:ante`, event 17) runs A3's `m28.antechamber_door` (the Queen's
  pyramid key 12348; else its line naming Queen Kalindra). L1-L3 are open to clear. `reach.stranded` now lists the four
  monsters behind it (by design: the solve has no key).
- F16: the sky door (event 67) is `d7.sky_door_dd15` then the `exit:` effect's standard entrance window (OK/Close).
- F12d: the book stand shows the open book (`xnpbook` 128 x 128, `fit`), the Overseer's desk papers (`desktop`
  128 x 64, `fit`): `size` is the picture's own size, `fit` stretches it once over the top.
- Tests: playtest (the door refused, then the key granted), playtest_sky (Close, OK). Installed 00:28, baked, 16/16 from
  assets_dev; audit 0 errors / 9 warnings (the registry answers and the four stranded monsters).

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the five chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. The fitted
book-stand and desk tops stand on the floor (no underside faces). Installed, baked; audit 0 errors / 9 warnings (all
as before: family_switch, four stranded monsters, four question.answer on the registry door), check_exits 0,
check_drops 0; tests 4 of 4 (16 of 16, output/studio_cal/a8_s26/run/dd15/c021959). Chest pictures:
output/studio_cal/a8_s29/shots/dd15_chests.jpg (all four on the floor against a wall).
