# DD-13 Ogre Forts: L4 notes

Lane A7 phase 3 (agent `xeen-a7-dd13`), 2026-11-20. Map 9166, `xeen_dd13.blv`, class S, `world: xeen`, on D2 Sprite
Forest and Ogre Pass. Built from the MU-6 graph `devdocs/xeen/mockups/act3_graphs/dd13.graph.yml` with D-25
(`mockups/act3_a7_decisions.md`, which wins): the party stays in the burning hall (Q9), the kennel's cats are the
Kennel Sabertooth row in the ogres' faction, a peace-then-burn playtest, the east gate's inside point by explicit
coordinates (Q10). Generator: `output/studio_cal/dd13/tools/gen.py` (writes L1-L4; never hand-edit the written files);
cycle `output/studio_cal/dd13/cycle.sh`; playtests `output/studio_cal/dd13/play.sh <name>` and `four.sh`; tour
`output/studio_cal/dd13/shots.sh` (`shots.yml`).

## What was built

Two timber blockhouses on floor 0 and their cellars with the ogres' run at -512. x east, y north: the west fort (north of
D2's pass road) has its gate on its south side, the east fort (south of the road) on its north side.

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| West gateway | 0 | 768 × 256 | — | Through the palisade (xopalis); the exit to D2 south (the yard, xodaylt) |
| West fort gate | 0 | 1,024 × 704 | — | **Start**; the gate's two leaves south, the blockhouse's double door north |
| West fort hall | 0 | 1,792 × 1,600, pitched roof 512-768 | — | Fire pit ("Burn?"), six hides, the long table of plates |
| West bunkhouse | 0 | 1,152 square | 4 Ogre (10) | Four log bunks; the ladder hole down (east wall) |
| Plunder store | 0 | 1,152 square, `store` | 2 Ogre (11) | Sacks, barrels, Kramer's strongbox (chest T3); the trapdoor down (by the west wall, hinged east) |
| West cellar | -512 | 3,968 × 640 | 3 Ogre (12) | Barrels, meat; both pole ladders up; the run's mouth south |
| The ogres' run | -512 | 320 wide, about 4,000 long | 2 Ogre, 2 Ogre Brute (13) | Rock tunnel with timber beams under the road; bends in several segments |
| Sardaj loot | -512 | 768 × 736 | 3 Ogre Brute (15) | The brutes' pile (chest T3), the broken disk case (Graalg's boast) |
| East cellar | -512 | an L, 1.78 M | 1 Ogre, 2 Ogre Brute (14) | Beer casks; the run from the north, the kennel's ramp east, Graalg's ladder in its north-east arm |
| Kennel | 0 → -512 | 1,152 × 768, floor a ramp | 4 Kennel Sabertooth (16) | Its floor falls 512 west to the east cellar; the log gate into the hall |
| Graalg's quarters | 0 | 1,152 × 1,024 | 2 Ogre Chief (17) | His cart-sized bed, the strongbox (chest T3 + the 2 Energy Disks), the trapdoor (hinged west) |
| East fort hall | 0 | 1,792 × 1,600, pitched roof | — | Bigger fire pit ("Burn?"), Graalg's seat of antlers and bones, six hides |
| East fort gate | 0 | 1,024 × 704 | — | **D2's east arrival**; the gate's two leaves north, the hall's double door south |
| East gateway | 0 | 768 × 256 | — | The exit to D2 north |

**Counts and sizes.** 14 rooms, **15 sectors** (the BLV's sector 0 counted), 1,022 faces, floor about 18.5 M units² by
the outlines (`oymap metrics`: 19.89 M with platform tops), **25 monsters** all placed (12 Ogre 11066 at 18, 7 Ogre
Brute 11067 at 22, 2 Ogre Chief 11068 at 30, 4 Kennel Sabertooth 11413 at 22), **3 chests** (T3 each), **10 doors**
(14 leaves: the two gates and the two blockhouse doors have two each; the two trapdoors since merge point 22), 3 loops (round each blockhouse and its cellar;
gate to gate through the run and back over D2). Kill XP per member L(L+10)/4: 12 × 504 + 7 × 704 + 2 × 1,200 + 4 ×
704 = 16,192 / 4 = **4.0k** (the graph's 4.0k).

**Textures.** 18 distinct at load + xoburn by event = **19, 0 new** (cap 30): one family, XD-05's MM8 Ogre Fortress
(d12): gkp1ceil (plank walls on posts, roofs, table), gcav2flr (beaten earth floors), gcav1flr (cellar and run rock,
the pits' rims), gkp1flr (straw: bunks, kennel, Graalg's), xopalis (gateways, the kennel's log gate), gkp103a/gkp103b
(the door leaves), xohide (hides), xobones (Graalg's seat), xochar/xoburn (XD-05's charred and burning timber),
xodaylt (the gateways' view out), t66abc10a (ladders, door edges, table legs), t66abc11a (the run's beams), the gt002
chest set.

**Map card (test row in the scratch root until A2 writes 9166).** Music 13; environment cave; treasure 3; lock 6,
trap 3, perception 6; refill 672; bolster LowerToEqual; **encounter 0**; slot 1 `Xeen Ogre`, tier 1, [2, 3], weight
100 (for the card only). Encounter 0 because the halls are empty "out hunting", a burned fort must stay empty, and a
rest spawn of the generic Xeen Ogre row would be hostile after a peace (DECIDE 1).

## The three rules of 2026-11-20 (checked by hand: A1's audit checks are not shipped)

- **Lights.** Every light is one of: a wall torch's flame (torch01 on its wall at 160, the light 24 in front of the
  wall at 184), a fire pit's (pit fire, blaze and embers 48-120 over the pit's centre, the pit a floor fixture with a
  fire decoration on it), the burn's fire on a burning wall (24 in front of the wall, 240 up), the gateways' daylight
  (24 in front of the exit face), or daylight through a burnt roof (24 under the roof's peak; burned stage only). The
  list with each light's room, wall distance and height against the ceiling is
  `output/studio_cal/dd13/lights_check.txt`. No light or lamp in a doorway, on a leaf, or in mid-air; `oymap audit`'s
  `lights.*` checks (light in solid, lamp in solid) report nothing (one torch that stood inside the loot cave's rough
  wall was fixed by dropping its rough walls).
- **Double doors.** The two fort gates and the two blockhouse doors are `leaves: 2`, `slide_left`, parting in the
  middle, with MM8's plank pair gkp103a (left wing, handle at its right) and gkp103b (right wing) on both faces
  (pictures 01, 02, 04, 22). Narrow doors (bunks, plunder store, Graalg) are single hinged plank leaves, one picture
  each, fitted.
- **Texture fit.** One-off pictures are fitted once: the door wings (stretched over their leaf), each hide (a 128 × 256
  cover panel with xohide fitted once since merge point 24), the exit view (xodaylt at its true size, fitted once per exit). Walls (gkp1ceil,
  xopalis, gcav1flr) and floors repeat only seamless tiles; no band or panel is tiled along a wall.

## The burn (D-25 Q9, XD-05's drum method, XD-23's stage)

- **The question** `evt:pit_w` / `evt:pit_e` (the halls' fire pits, "Fire pit"): the source's line in the question
  window, "You've found an Ogre fort, but the Ogres are out hunting. Burn?" (aaze0015:7), "Burn (Yes/No)?". No: "You
  leave the fort standing, for now." (asked again next click). Yes:
  1. A3's hook (`q-d11.fort_west` / `fort_east`): sets `west_burned` 113224 / `east_burned` 113225 and `hostile`
     113222, shows aaze0015:7-8 ("... The fort collapses in a heap of burning timbers and smoldering ash.").
  2. The hall's four walls (full-wall panels) and roof (a ceiling region) `set_texture` xoburn; the six hides (and the
     west hall's table, its legs and plates) burn away (`damage_destructible`, wood); the pit's fire roars (a pulsing
     light at the pit, four pulsing lights on the burning walls, the "raging fire loop"), the pit's calm fire off.
  3. `evt:burn_out_*` 4 s later: every timber face of that fort charred (xochar: walls and roofs of its gateway, gate
     room, hall and side rooms, the two double doors, the pit's top), the roof down round the pit (three charred heaps,
     platforms shown and made solid; a path stays open from the door to the pit and between the side doors), the
     pit's fire and the fort's wall torches gone (decorations hidden, lights off), embers glowing in the pit,
     daylight through the burnt roofs.
- **Burned stage** `evt:stage_w` / `evt:stage_e` (every load with the fort's qbit, D-23): the same charred faces,
  rubble, fires and torches out, daylight through the roofs, and that fort's monsters hidden: the west fort's bunks,
  plunder store and cellar (groups 10, 11, 12); the east fort's kennel cats, Graalg's chiefs and cellar (16, 17, 14).
  The run (13) and the Sardaj loot cave (15) keep theirs. `evt:standing_*` hides the rubble (hidden, passable) on every
  load while the fort stands. The way in from D2 stays open (the gates still open and close, charred).
- **The strongbox** `evt:strongbox` (chest preset, "Chest"): locked by `not peace` (113223); open: A3's
  `q-d11.fort_search` (fort_disks 113226, aaze0015:23 once, then "The strongbox is empty.") and the chest with the 2
  Energy Disks 12334 (the hook's map_gives) and T3 loot; after a peace the hook's "Graalg's strongbox. Graalg is your
  friend. Graalg would notice." and the chest stays shut. Searchable after the east fort burns (playtest).
- **Peace then burn (D-12.3):** with `friends` 113221 the forts' ogres and the kennel's cats are peaceful (A2's
  relations, faction pass: placed without a `hostile` key so the relations decide); a burn sets `hostile` and every
  pass ogre and cat is hostile again **in the same visit** (playtest_peace: 3 s after the burn, 0 friendly, 21 ogres
  and 4 cats hostile).

## Exits (D-24: `exit` preset, the game's leave window)

- **West gate** (`exit:gate_w` in the west gateway's south wall) → `exit:d2_west`, D2 **(4096, 13824, 2016) facing
  south**. Measured: the party stands at z **2017** 2 s after landing (`playtest_exit.yml`, z 2000-2035).
- **East gate** (`exit:gate_e` in the east gateway's north wall) → `exit:d2_east`, D2 **(11776, 11776, 2048) facing
  north**. Measured: z **2049** 2 s after landing (z 2032-2065).
- **Inside points for A6 (D2's doors into DD-13):** west, the map's start **(0, -64, 0) in room:gate_w, facing north
  (90)**; east, explicit coordinates **(7552, 32, 0) in room:gate_e, facing south (270)** (`DD13_EAST_INSIDE`): just
  inside the east gate's leaves, the hall's double door ahead.

## Original lines

- "You've found an Ogre fort, but the Ogres are out hunting. Burn?" (dark/aaze0015:7): both pits' question.
- "The fort collapses in a heap of burning timbers and smoldering ash." (aaze0015:8): A3's fort hooks.
- "You search the fort and find 2 energy disks." (aaze0015:23): A3's fort_search at the strongbox.
- "We are Ogres! We take what we want. Yesterday, we took the Sardaj's Energy disks!" (aaze0015:16): scratched on the
  broken disk case in the Sardaj loot cave (a window).

## Checks (scratch root `output/studio_cal/dd13/root`, binaries of merge point 11; today's: the last section)

- `oymap fmt --check` clean, `validate` L1-L4 no issues, `build` 13 warnings (below), `audit --reach --solve`
  (`output/studio_cal/dd13/audit.txt`): no error, no warning; 0 coplanar pairs; every sector reached with the doors
  out of the way; infos only (t66abc10a squashed on ladder rails, the AmbientSound variables never read).
- Build warnings kept: the hide slabs' 16-unit ends (t66abc10a stretched over 16 × 256: the studio stretches a block's
  `end_surface`; 12 warnings), and the west table's top "rests on nothing over most of its footprint" (it stands on
  four leg blocks at its corners).
- Playtests from the root with `--world xeen`, each **4 of 4** (`output/studio_cal/dd13/four.out`, logs in
  `output/studio_cal/dd13/run/`): `playtest.yml` (155 steps: the war route, both burns, the strongbox, Graalg's
  ladder, the burned-stage reload, out by the east gate), `playtest_peace.yml` (40: peace, strongbox barred, burn,
  hostile in the same visit), `playtest_hostility.yml` (26), `playtest_exit.yml` (34: both gates, the east inside point, landings measured; its last four runs in
  `output/studio_cal/dd13/four_exit.out`).
- Pictures `output/studio_cal/dd13/shots/` (sheets `sheet1-4.jpg`), unbaked (the lead bakes). Shots 24-31 are the
  burned stage set by console (`qbit set`, `event 24/23`); the console run does not hide the actors in a frozen tour, so
  the bunks' and Graalg's monsters still show there: the hiding is checked after a reload in `playtest.yml`.

## Words needed

- **No two-leaf hinged door:** `leaves: 2` is for sliding leaves only, so the gates part sideways into the walls (they
  read as two wings; a pair of swinging leaves would be closer to a fort gate).
- (Both merge-point-22 gaps closed by merge point 24: a `cover` panel over a whole-wall panel, and dec24x bound for
  dungeons. See "Merge point 24" below.)
- **`window: true` on a timer `text` event** shows a status line, not a window; the arrival window is a `script` with a
  `message` effect.
- **xopoles' see-through bars show magenta speckle** through their holes (as in XD-05's cage gate; D-25 Q15's check 3):
  the kennel's gate uses the opaque log texture xopalis instead.

## Dressing exceptions

None (audit clean). Barrels in pairs by walls in both cellars and the plunder store (a `store: true` storeroom with its
sacks and bags), casks in pairs, bones by walls; nothing within 192 of a door or 320 in front of an opening (casks and a
bag moved for the audit's three first errors).

## DECIDE

1. *Rest encounters.* Encounter 0 (no rest spawns): the halls are empty, burned forts stay empty, and a spawned generic
   Xeen Ogre would be hostile after a peace. Option: 10 % with the slot (rests then spawn hostile ogres even in a
   peaceful fort, unless A2 adds a pass-faction slot row). Default 0.
2. *The fallen roof.* Charred heaps round the pit with daylight lights under the roofs' peaks; the roof faces stay
   whole (charred), no visible hole. Options: keep; a roof region with a hole (needs a ceiling opening word); a
   generated "burnt rafters against sky" texture (1 of the 4 allowed). Default keep.
3. *The gateways' view* (xodaylt, XD-05's sunny hills) on Darkside's D2. Options: keep; a new Darkside yard picture
   (palisade and pass road under a dim sky, 1 of 4). Default keep.

## For the user

- Arrive in the west fort's gate: open the gate's two leaves behind you to see them part; the blockhouse's double door
  ahead. In the hall, click the fire pit: Yes burns the hall round you (the walls blaze, the hides go, 4 s later all
  black, the roof down round the pit, daylight through it). Leave and come back: the west fort a charred, empty ruin.
- The run under the road (beams overhead, "cart wheels rumble overhead"), the Sardaj loot cave's disk case (Graalg's
  boast), the kennel's ramp up to Graalg's hall, the strongbox (2 Energy Disks) in his quarters.
- With Graalg's friendship the forts are peaceful and the strongbox stays shut; burning a hall turns them all at once.

## D-34: smoke holes open to the sky, the Darkside view, encounter 0 (2026-11-20, lane A7, seventh session)

Generator before: `output/studio_cal/dd13/tools/gen_before_d34.py`.

- **Roofs.** Each hall's roof is now a gable whose ridge runs north-south through its fire pit (both pits stand on
  their hall's centre line; the pyramid roof had its peak 416 off the pit). At the ridge over the pit a smoke hole: a
  raised ring 448 across on the roof planes (704 on its sides, 768 at the ridge) up to a flat top 352 across at 880,
  `ceiling_points` + `ceiling_lines` (the studio's `ceiling_levels` cannot stand on a `ceiling_points` roof); the top
  is `region:hall_*_sky` with `sky: true`, the ring's leaning sides belong to `region:hall_*_roof` (they burn and char
  with the roof). `atmosphere.yml` (written by gen.py): `open_sky: {mode: open, preset: xeen_darkside_day}`, no
  daylight block, no weather. **The preset is named by its own name**: `xeendark1` is `sky.yml`'s alias of a sky
  *texture* name, which the indoor `preset` key does not resolve (it fell back to a clear blue noon sky).
- **Roof patch** `platform:roof_patch_*` (gkp1ceil, 352 square, 863-879 just under the sky top, so no slit of sky shows
  past it): drawn by default and by `evt:standing_*` (show, solid); the burn sets it `xoburn`; `evt:burn_out_*` and the
  burned stage `evt:stage_*` hide it (and make it passable).
- **Tie beams:** two smoke-blackened beams (xochar, beams have no id to char) across each hole 80 either side of the pit,
  just under the ring (top on the roof planes 96 beyond the ring, 645-677): seen against the sky from the hall's floor.
  They cost **four build warnings** ("rests on nothing over most of its footprint": the studio has no word for a
  beam fixed to a leaning roof at its ends); kept. Build warnings 17 (12 hide ends, the table, the 4 beams).
- **Rubble** under the hole: `rubble_w3` moved under the hole's north edge, new `rubble_w4` and `rubble_e4` (charred
  rafters fallen through the hole), shown with the other heaps after the burn.
- **Floors pinned:** the patch is the highest floor over each pit, so the pit fire (`ckfyr00`), its three lights and the
  fire sounds take `floor_height: 24` (the pit's top), the hall sky lights `floor_height: 0`.
- **Lights:** under each hole (at the pit, 680 up, radius 1700, [128, 120, 108]) off until the burn; the side rooms'
  burnt-roof lights dimmed to [118, 110, 100] radius 1000; the gateways' daylight [96, 88, 76] radius 420 (was a noon
  [200, 205, 215] radius 700).
- **Gateways:** `xddaylt` (new, D-34 (3); `level_generation/textures_xeen/a7_dd13_daylt/`, one Codex worker, v1 kept,
  references two pictures of D2's pass under xeendark1, tone gain 1.10; x4 master in
  `assets_source/worlds/xeen/textures_x4/`; A6 to register) in place of XD-05's sunny `xodaylt`. Also on DD-11A-C's hatches.
- **Doors (A1's door check, merge point 15):** the three narrow single doors (bunks, plunder store, Graalg's, 192 wide)
  showed one wing of the gates' pair (`doors.half_wing`): now MM6's single plank door `d2smldor`, fitted once. Textures
  20 of 30 (xddaylt and d2smldor new to the map; xodaylt gone).
- **Encounter 0:** A2's row 9166 (D-34 (1)).
- **Pictures** from `assets_dev` after the bake: `output/studio_cal/dd13/d34_baked/` (sheets `d34_baked_a.jpg`,
  `d34_baked_b.jpg`): both stages by day and night. The standing hall takes no sky light (day and night alike), so the
  built roof fallback was not needed. Unbaked: `d34/`, `d34b/`, `d34c/`.
- **Checks:** fmt clean, validate no issues, audit `--reach --solve` no error or warning (lights and doors included);
  installed, baked (`stale_bakes.py` 0); from `assets_dev` with row 9166: `playtest` (155 steps), `playtest_peace` (40),
  `playtest_hostility` (26), `playtest_exit` (34) **4 of 4 each** (`output/studio_cal/a7/s7_dd13_chain.out`).
- For the user: burn a hall and look up through the smoke hole by day and by night; the gateways' view of the pass.

### Build warnings kept

(The hides' 12 and the table's are gone since merge point 21, below.)

- `rooms[8|9].beams[0|1]` rest on nothing: the tie beams across the smoke holes, fixed to the roof planes at their ends.

## Merge points 21 and 22: trapdoors, hides, decorations hidden by events (2026-11-21, lane A7, fifteenth session)

Generator before: `output/studio_cal/dd13/s15/gen_before_s15.py` (L4 before: `s15/L4_before/`). Binaries of merge point
22 (01:40:33).

- **Trapdoors** (`door:plunder_trap` on `open:plunder_cellar`, `door:graalg_trap` on `open:graalg_cellar`): one plank
  leaf each (gkp1ceil at its size, both faces; t66abc10a edges), `thickness: 16`, `swing: 95` (gen.py `TRAP_SWING`),
  hinged on the side away from the ladder's top (the plunder store's ladder is on the hole's west side: `hinge: east`;
  Graalg's on its east: `hinge: west`), so the open leaf hangs on the far side of the hole from the ladder. Events
  `evt:trap_plunder` (30, door 14) and `evt:trap_graalg` (29, door 13), door presets "Trapdoor". The bunkhouse's ladder
  hole stays open. `playtest.yml` opens the plunder store's from below before climbing up through it and Graalg's from
  above before climbing down and back up (154 steps).
- **Trapdoors' direction (for A1):** `swing` > 0 swings the leaf **down into the room below**, as the README says, and
  it **ends open** (hanging under the hinge). Pictures from the west cellar under the plunder store's trapdoor, opened by
  `event 30` in a screenshot tour (scratch root, unbaked): `output/studio_cal/dd13/s15/trap/` (sheet
  `s15/trap_sheet.jpg`): `01` closed, `03`/`04`/`05`/`06` about 0.3, 0.6, 1.2 and 2.7 s after (the leaf drops on the
  hole's east side, hanging from about 0.6 s on), `07` open from the store above, `08` the open leaf from the east, the
  ladder clear under the hole. The sign is right: nothing flipped. **`state: open` at load** (a scratch build only,
  `s15/L4_stateopen/`, scene `state: 0` against 2 for closed): both trapdoors load open, hanging down
  (`s15/trap_open_at_load/`, sheet `s15/trap_open_at_load_sheet.jpg`). The installed map keeps them closed.
- **Hides:** not `cover` panels. A cover panel may not overlap another panel of its wall, and the halls' walls are each
  one whole-wall panel with an id (the burn's `set_texture`), so validate refuses them ("Words needed"). They stay
  16-thick slabs against the wall, their ends now `end_surface: {texture: t66abc10a, size: [32, 128], fit: false}`:
  the 12 "stretched" build warnings are gone.
- **Decorations by event:** the pit fires, the forts' wall torches and the west table's plates are hidden by
  `{hide: deco:x}` (`evt.SetSprite(n, 0)`) in place of their 28 trigger-only destructibles (ids.lock.yml keeps the old
  destructible numbers; the hides 26-37 and the table 38-42 are unchanged). `playtest.yml` checks them with
  `sprite_shown` / `sprite_hidden` (decorations 12 and 11 the pit fires, 57 and 49 two torches, 33-35 the plates). The
  burnt-out logs in each pit (dec24x, `hidden: true`, shown by the burn) wait on a dungeon binding ("Words needed");
  the fallen roof stays charred platform heaps: no dungeon decoration is a heap of roof timbers.
- **The west table's legs** are set in from its corners (24-40 from its edges); the "rests on nothing" warning is gone.
- **Checks** (scratch root `output/studio_cal/dd13/root`, `xcycle.sh`): fmt clean, validate no issues, build **4
  warnings** (the tie beams, kept below), audit `--reach --solve` (`output/studio_cal/dd13/a7_xaudit.txt`) **0 errors,
  0 warnings**, 5 infos (t66abc10a squashed on 54 faces, was 78; the AmbientSound variables never read), 1,022 faces,
  14 door records, 14 of 14 sectors with the doors out of the way; `--dressing` no error or warning. Installed with its
  bake 2026-11-21 01:56 (`install_baked.sh`), `stale_bakes.py`: none for DD-13 (the one stale bake listed is
  xeen_x2's). From `assets_dev`: `playtest` (154 steps), `playtest_peace` (40), `playtest_hostility` (26),
  `playtest_exit` (34) **4 of 4 each** (`output/studio_cal/a7/s15_dd13_four.out`, logs in
  `output/studio_cal/dd13/a7_xrun/`).

## Merge point 24: hides as cover panels, embers in the pits (2026-11-21, lane A7, seventeenth session)

Generator before: `output/studio_cal/dd13/s17/gen_before_s17.py` (L4 before: `s17/L4_before/`, which the old generator
reproduced exactly). Binaries of merge point 24 (03:13:18).

- **Hides:** the twelve hides are now `cover` panels (`panel:hide_w1`-`w6`, `panel:hide_e1`-`e6`; 128 x 256, bottom 64,
  xohide fitted once) hung 2 in front of the halls' whole-wall panels, at the old slabs' spots; the destructibles
  (`destructible:hide_*`, numbers unchanged) are `of` the panels and burn them away to the wall. The slabs are gone.
- **Embers:** `EMBERS_DECO = True`: dec24x in each pit (`deco:embers_w` 12, `deco:embers_e` 11), `hidden: true`, shown
  by `evt:burn_out_*` and on every load with the fort's qbit. Every later decoration number moved up by 2; `playtest.yml`
  follows (pit fires 14/13, torches 59/51, plates 35-37; embers hidden before the burn and shown after and after the
  reload).
- Pictures (scratch root, unbaked): `output/studio_cal/dd13/s17/sheet.jpg` (the hides on both halls' walls, a close
  one), `s17/burn_sheet.jpg` (the west hall burned: the logs in the pit, the walls charred, no hides).
- Checks: fmt clean, validate clean, build 4 warnings (the tie beams, as before), audit `--reach --solve` 0 errors, 0
  warnings. Installed with its bake 2026-11-21 03:28 (`install_baked.sh`), stale bakes 0. From `assets_dev`:
  `playtest` (158 steps), `playtest_peace` (40), `playtest_hostility` (26), `playtest_exit` (34) **4 of 4 each**
  (`output/studio_cal/a7/s17_dd13_four.out`).


## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:fire_e`, `deco:fire_w`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
