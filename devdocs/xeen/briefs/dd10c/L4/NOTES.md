# DD-10C Gemstone Mines, north pocket (L4): notes

Lane A8 (agent `agent:xeen-a8-dd10c`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd10c.graph.yml`) with decider D-27 (`mockups/act3_a8_decisions_b.md`), which wins
where they differ. **D-27 moved this pocket to Act V** (D6's lower band 38-50, D6's own families, 20 monsters,
treasure 5): the geometry is built now with DD-10A and DD-10B and **kept in scratch**; monsters, the exit to D6, the
install and the bake are phase 5 (below, "What phase 5 adds").

All four levels are written by `output/studio_cal/dd10c/tools/gen.py`, which imports the mine's shared pieces from
DD-10A's `output/studio_cal/dd10a/tools/mine.py` (as DD-10B does: themes, timber sets, rails, vein panels and events,
the refill, the false vein, the exit), so the three pockets read as one mine. The playtest and this file are written by
hand. `output/studio_cal/dd10c/cycle.sh` generates, formats, validates, builds, installs into the scratch root
`output/studio_cal/dd10c/root`, audits and records (`LEVELS="L1 L2 L3 L4"`).

## What was built

Map 9161, `xeen_dd10c.blv`, class S, on D6 The Forbidden Zone (phase 5); Q-D7 The Gemsmiths (repeatable: Hector's
diamonds, D-27 "only from the north adit"). Party 48-51, music 18, treasure 5 (map card; the one chest is tier 5).

Six rooms on one level (floors at 0, the lava seam sunk 48), in the plan frame x east, y north, the adit's mouth at y 0:

| Room | Size | Texture | Phase 5 monsters | What |
| --- | --- | --- | --- | --- |
| North adit | 384 × 896, 352 high | timbered (7d35) | — | arrival; two timber sets, rails, the boarded mouth (sealed), the plank door north |
| Lava gallery | about 2,690 × 770 plus a south bay to y 704, 448-576, rough | 6d18 black vlcwl3a | 4 | the lava seam in the south bay, two glowing rocks |
| Diamond cavern | about 2,110 × 2,050, 640-960, rough | 7d35 cwb1 walls, black vlcwl3a roof and pillars | 6 | five diamond veins, the false vein, two black pillars, two stalactites |
| Crystal grotto | 768 × 768 octagon, 384-576 | 7d35, MM8 gcrysc3 crystals | 2 | a geode: six crystals out of its walls, the dead miner and his chest (T5) |
| The collapse | about 1,790 × 1,220, 480-704, rough | 7d35 | 4 | eight tipped roof slabs ("Rubble"), boulders, under the hole in the roof |
| Roach nest | about 2,180 × 1,020, 448-576, rough | 7d35, black egg cases | 4 | ten egg cases in three clutches, warm ash, embers, bones |

Links as the graph: adit -door- lava -open- diamond -door- grotto; lava -door- collapse -open- nest -open- diamond.
Critical path adit, lava, diamond; return diamond, nest, collapse, lava, adit; one loop (lava, diamond, nest,
collapse). No exit yet: the adit's mouth is a boarded panel with a line (sealed, below).

**Measured** (`oymap metrics`, `output/studio_cal/dd10c/metrics.json`): 6 sectors (≤ 15), **10.94 M units²** (≤ 20),
0 monsters now (20 in phase 5: 15-30), 1 chest (0-3), 3 doors (3-8), 0 exits (1 in phase 5), 16 lights (10 room and
glow lights, two of them over the seam and one the lava's spill into the cavern; a white glint before each of the six
veins), 5 placed sounds, 19 decorations. Largest room the diamond cavern (3.63 M); ceilings 352-960 (median 624). Walkable 9.36 M.

## Mechanisms and hooks

- **Veins** (D-27, the shared `mine.py`): five diamond veins in the diamond cavern's walls (edges 0, 1, 2, 3, 5 of
  `DIAM`), each a wall panel of A6's `xdvdiam` (256 × 384, drawn once, `fit`) with a white glint light 96 in front.
  Hover "Diamond vein" (dark/aaze0039:1-4). A click with the vein's map variable clear sets it, gives one diamond rock
  (12360, the hook's `map_gives`), runs A3's `q-d7.diamond_veins` (sets `q-d7.dug` 113144) and says "You work a
  diamond rock out of the vein."; spent: "You've got all this vein has to offer." (aaze0039:10).
- **The false vein** (D-27): a sixth panel of the same picture on the north-west wall (edge 8, nearest the lava) with
  its own glint, hover "Diamond vein": "A gem exploded!" (aaze0039:11) and **28 fire to every member**, once (map
  variable `false_vein`); then the spent line. Scaled to Act V: a level-48 party has 280 / 128 / 177 / 118 hit points
  (Knight, Cleric, Archer, Sorcerer; the playtest's log): 28 is 10-24 %, 16 % of the average member (DD-10A/B's 16 at
  level 25 was 15 %). It does not come back with a refill. `GEM_DAMAGE` in gen.py.
- **Refill** (`evt:refill`, a load event): when `q-d7.refill_c` (113143) is set, the five veins' variables go back to
  0, the bit is cleared and the status says "The veins glitter again: the God of Minerals has been at work." refill_a
  and refill_b are the other pockets' and are left alone. The God of Minerals is in DD-10B; played here as DD-10A's
  test does (his hook's do-list by an event script): picked, re-entered unpaid (still spent), paid, re-entered (full,
  refill_c clear, refill_a/b still set), picked again (dug set again), re-entered (no second refill).
- **The sealed adit** (`evt:adit_mouth`): the boarded mouth in the adit's south wall says "Boards and fallen rock close
  the adit's mouth from outside. There is no way out here yet." Phase 5 turns it into the exit (below).
- **Rubble** (`evt:rubble`, the graph's 'Rubble'): the biggest slab says "Rubble from a fallen roof. Nothing under it
  but more rock."
- `evt:arrive`: a one-shot window on the first arrival (`arrived_once` 117240): "THE GEMSTONE MINES, NORTH POCKET.
  Heat breathes out of the rock ... Hector the diamond smith wants five diamond rocks; the veins give one each. Few who
  come here go back, they say." `evt:enter`: a status line on every entry.
- Three plank doors (single leaves, 224 wide: no double door in this map); one chest.

## Qbits, variables, items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | **117240** | map qbit (provisional block 117240-117279): the arrival window, once per game |
| `q-d7.refill_c` | 113143 | A3's: read and cleared by this pocket's entry; set (with refill_a, refill_b) by the God's hook in DD-10B |
| `q-d7.dug` | 113144 | A3's: set by every vein through the hook |

No player bits. Map variables: `diamond_1`-`diamond_5`, `false_vein` (+ the studio's `once.arrive`). Items: diamond rock
12360 (one per vein).

## Monster spots (phase 5)

None placed (D-27). `gen.py`'s `MONSTER_SPOTS` holds 20 marked spots, the graph's split, each with a group and a slot
('a' the commoner kind, 'b' the heavier): lava gallery group 1 (400, 1450) a, (1000, 1500) a, (1500, 1450) b,
(1900, 1400) a; diamond cavern group 2 (2700, 1100) a, (3300, 700) a, (3900, 900) b, (4000, 1600) a, (3400, 2000) b,
(2700, 1900) a; crystal grotto group 3 (4800, 1344) b, (5050, 1300) a; the collapse group 4 (0, 2100) a,
(600, 2300) a, (900, 2600) b, (500, 2950) a; roach nest group 5 (1800, 2600) a, (2400, 2700) a, (3000, 2700) b,
(2800, 3000) a. All on open floor off the slabs, crystals and seam. D-32: nothing here keeps a big monster in a room
(every opening is 320-400 high).

Map card slots are **provisional** (the root's test row and `project.yml`): Xeen Eye tier 5, 2-3, weight 60; Xeen
Robot tier 5, 1-2, weight 40 (MAPS §0's "Floating Eye, Terrible Eye, Patrol"); encounter chance 0, environment cave,
lock 10, trap 5, perception 8, treasure 5, refill 672 days. A2 replaces them with D6's families.

## What phase 5 adds

1. **Monsters** (A2 picks D6's families: no Lava Roach, Arachnoid Queen or Sand Golem; 20 at 38-50, groups 2-3):
   set `PHASE5_ROWS = {'a': <row>, 'b': <row>}` and `PHASE5_MONSTERS = True` in gen.py (the spots above; facing and
   per-room counts as wanted), the map card slots in `PROJECT['map_stats']`, the plan's `population` and totals
   (`fixed_actors`, `monsters_about`); `playtest.yml` gets the `actor_count` asserts and `clear_hostiles` on its walks
   (DD-10B's), and a `playtest_hostility.yml` (DD-10B's / XD-27's); kill XP in the report (MAPS §0: about 11.5k).
2. **The exit to D6** (A6 builds D6's north adit): set `D6_LIVE = True` and `D6_ARRIVAL` to A6's return point outside
   the adit, measured headless on the installed D6 (`status()`, XD-26's NOTES "Measured heights"). gen.py then drops
   the boarded panel and its line, adds the `exits` object `exit:d6` (the `exit` preset, the game's own "Do you wish to
   leave …?" window; "Exit the Gemstone Mines?" aaze0039:0 is its meaning) and drops `listed_only` from the
   neighbour (checked: that variant validates). Add `playtest_exit.yml` (the window's OK pressed, XD-11's
   `playtest_exit_x3.yml`; DD-10B's for the shape), and replace the playtest's sealed-adit step. **D6's door into this
   map lands at the start: (0, 192, 0), facing north (90°, game 512)**, just inside the adit's mouth.
3. **Map row**: A2 writes 9161 (`source/map_rows.yml`); `source/maps.yml`'s DD-10C row still says Act III (party
   23-27, levels 16-28, treasure 3, group DD-10+11): to Act V (party 48-51, 38-50, treasure 5, 20 monsters).
4. **Install and bake** (the lane lead): `oymap install devdocs/xeen/briefs/dd10c/L4 --root assets_dev --build
   output/studio_cal/dd10c/build` after a fresh `cycle.sh`; a bake profile
   `tools/lighting/baked_indoors/profiles/xeen_dd10c.yml` with DD-10B's values (units_per_texel 16, page_size 2048,
   padding 2, samples 128, bounces 3, light_size 24, direct_scale 2.0, bounce_scale 5.0, ambient_scale 0.9,
   blur_radius 2, max_lighting 1.5) and `output/studio_cal/a8_s5/bake.sh dd10c assets_dev`; then
   `ASSETS=$PWD/assets_dev TESTS="playtest playtest_hostility playtest_exit" output/studio_cal/dd10c/four.sh`.
5. Pictures again with monsters and the bake; the hostility playtest 4 of 4.

## Textures (16 distinct, cap 30; 0 new of 4)

MM7 Nighon Tunnels 7d35 (D-27, `dungeon_families.yml` mines): `cwb1` walls and the cavern's walls (the veins' own
ground: `xdvdiam` is painted on cwb1, so the panels match their wall), `cfb1` floors, `trim9_32` posts, jambs, plank
doors and the boarded mouth, `trim9_32a` caps and lagging; the world's `xnrustirn` (the rails); A6's **`xdvdiam`** on
the six veins (installed and registered: nothing waits on A6); **MM6 Gharik's Forge 6d18 `vlcwl3a`** (black glittering
cooled-lava rock) on the lava gallery's walls and roof, the cavern's roof and pillars, the seam's rim and the egg
cases; **`lavatyl`** for the seam (the engine's shader lava: no picture, self-lit, the burning bit); MM8 d37's
`gcrysc3` for the geode's crystals (as DD-10B's throne and God). Chest pictures make the rest.
`python3 tools/xeen/texture_budget.py --root output/studio_cal/dd10c/root --map DD-10C`: S 16/30, 0/4 new.

Texture fit (the user's rule): each vein panel shows its picture once, whole; the rock, lava rock and crystal are
seamless tiles; nothing one-off is tiled.

## Original lines (dark/aaze0039)

"Diamond vein" (:1-4, the hovers); "You've got all this vein has to offer." (:10); "A gem exploded!" (:11). Phase 5
adds "Exit the Gemstone Mines?" (:0, the leave window's meaning).

## Presentation

Music 18. Placed sounds: air at the boarded mouth (`whistling wind`), the seam (`lava loop`), seepage in the cavern
(`drip02`), the collapse settling (`rumble`), the geode (`humming`). One lantern (`torch02`) on the adit's west wall and
one on the collapse's west wall (solid wall, no doorway, no door leaf); room lights are plain lights in open air, none
inside geometry; the seam's two lights hang 112 over the lava (the lamp rule: no fixture, a glow). Ambient 12-16:
timber lit, caves dark; red light along the seam and spilling into the cavern's west end, cold white light and glints
in the cavern, a cold glow in the geode, a warm glow over the nest's ash. **No bake in the scratch root** (the lane
lead bakes after the phase-5 install).

## Dressing

`oymap audit --world xeen --reach --solve`: 0 errors, 0 warnings. One container (the grotto's chest by the east wall,
700 from its door); the seam lies in a bay of the south wall off both walking lines (adit to cavern, collapse to
cavern); the slabs in the collapse's north-west half off the door-to-nest line; the cavern's crystals, spoil and skull
by its walls. **Dressing exceptions:** none.

## Checks (scratch root, `--world xeen`)

- `oymap validate` L1-L4 no issues; `oymap build` 0 warnings; `fmt --check` clean on L1-L4; recorded L1-L4.
- `oymap audit --reach --solve` (`output/studio_cal/dd10c/audit.txt`): no error, no warning, 0 faces in one plane;
  6 of 6 sectors on foot with the doors out of the way.
- Playtest (`output/studio_cal/dd10c/four.sh`, logs `output/studio_cal/dd10c/run/four_192841/`): **`playtest.yml` 4
  of 4** (71 asserts, 61 steps): no monsters, the arrival window once, the sealed adit, the doors, five veins (one rock
  each, dug set, the spent line), the false vein's 28 fire once (immortality off for it) and spent after, the dead
  miner's chest (1,500 gold), the rubble, the loop back, re-entered unpaid (spent), paid, re-entered (full, refill_c
  clear, refill_a/b kept, the false vein stays spent), a vein again (dug set again), re-entered (no second refill).
  No hostility or exit test yet (no monsters, no exit: phase 5).
- Map row: the root carries REAL copies of `map_stats.txt` and `bolster_maps.txt` with a test row 9161 (copied from
  DD-10B's test row 9160: this map's name and stem, treasure 5, lock 10, trap 5, perception 8, the provisional slots).

## Pictures looked at

`output/studio_cal/dd10c/shots/look1_1..3.jpg` (27 shots: every room, each door closed and open, every vein wall, the
false vein, the geode, the chest and miner, the nest's clutches, the collapse), `seam1_1.jpg` (the seam from above) and
`look2_1..2.jpg` (after the fixes). Fixed after look1: the seam was MM6 6d18's `6voltyl`, which the engine draws as a
grey volcanic tile (no lava at all): now `lavatyl`, the shader's lava; the rubble was one long low block that read as a
wall: now eight roof slabs tipped every way with boulders between. (Validate caught a crystal through the grotto's wall
before any picture.) PNG
folders deleted; `tools/tour.py <name> [filters]` and `shoot.sh <name>` remake them.
Still plain: `gcrysc3` is a bright, saturated cyan in the unbaked root (as in DD-10B); the rough cave walls read
smooth; the lighting is flat until the bake.

## Words needed

None.

## DECIDE

- **The seam's lava.** D-27 names "MM6 6d18 lava"; 6d18's lava face is `6voltyl`, which the engine draws as its grey
  picture (the liquid shader knows only `lavtyl`/`lavatyl`/`hdlav*`). Built with `lavatyl` (MM6's lava face name, the
  shader's lava), 6d18's `vlcwl3a` round it. Reverse: `SEAM_LAVA` in gen.py.
- **The cavern's "black rock".** The veins' picture is painted on 7d35's brown `cwb1`, so the cavern's walls stay cwb1
  (the panel-background rule) and the black (`vlcwl3a`) is its roof, its pillars and the lava gallery. If A6 repaints
  `xdvdiam` on black rock, the cavern's `theme:black` wall becomes `vlcwl3a` (one line).
- False-vein damage 28 (Act V scaling, above).
- Map card values (lock 10, trap 5, perception 8) are test values for A2.

## What the user should look at

- The lava gallery: the seam in its bay, the black rock; does it read as "cooling lava"?
- The diamond cavern: the veins on brown rock under a black roof; the false vein beside the lava's opening.
- The geode's cyan before the bake.

## State and next steps

Phase 3 complete in the scratch root (geometry, veins, refill, false vein, seam, lights, sounds, dressing). Nothing
waits on A6's textures. Phase 5: "What phase 5 adds" above. Never installed into assets_dev.

## Session 7 (A8, 2026-11-20; scratch only, not installed)

The shared `mine.py` changes reach DD-10C's generator (copy before: `tools/gen_before_s7.py`): the cart side at scale
1.5, the veins refill on a fresh entry only (`in_visit`, `evt:visit_end`), the timber and exit planks at their own
size with scale. Regenerated, validates, builds with no warning; not rebuilt into its root or played (phase 5).

## Session 13: phase 5 (A8, 2026-11-21, decider D-62; this section wins over the phase-3 text above)

`gen.py` (copy before: `tools/gen_before_s13.py`; the L4 before: `output/studio_cal/dd10c/L4_before_s13/`, which the
unchanged generator reproduced exactly, so there were no hand edits) sets the phase-5 switches:

- **Monsters (D-62 Q48):** `PHASE5_MONSTERS = True`, a third slot `'c'` on the two former `'b'` spots in the lava
  gallery (1500, 1450) and the collapse (900, 2600), `PHASE5_ROWS = {'a': 11570, 'b': 11571, 'c': 11610}`: Floating
  Eye 40 x14, Terrible Eye 50 x4, Patrol 50 x2 = 46,000 kill XP, **11.50k per member** (MAPS §0 11.5k, 0.0 %). By room:
  lava 3 + 1 Patrol, cavern 4 + 2 Terrible, grotto 1 + 1 Terrible, collapse 3 + 1 Patrol, nest 3 + 1 Terrible. The
  plan's populations and totals (20 fixed actors) follow.
- **Map card (Q50):** encounter 10, one slot `Xeen Eye` Dif 0, 2-3, weight 100 (Floating Eye only). A2's row 9161 has
  landed with the same values (lock 10, trap 5, perception 8, treasure 5, CAVE).
- **The cold nest (Q49):** the room is "Cold nest"; the warm ash is cold (`7dec11` "Cold ash."), the burning-rock
  embers are a plain rock (`6rock03`), the nest's light is cold grey (150, 165, 190); the middle clutch's first egg
  case is `platform:eggs`, hover "Empty egg cases", line "Split and cold. Whatever hatched here was eaten by whatever
  lives here now." (event 17).
- **The exit (D6_LIVE):** the boarded panel and its line are gone; the adit's mouth is `exit:d6` with the exit preset
  (event 18; aaze0039:0 its meaning) to D6's **`entrance:dd10c_adit`** (-9216, -16384, 2688) facing 512
  (`D6_ARRIVAL`, D6's named arrival; A6's height 2688 stands). The plan's entrance is renamed
  **`entrance:d6_adit`** (D-37): the sidecar lists it at (0, 192, 0) facing 512. **A6:** D6's `door:dd10c` names
  `into: {map: xeen_dd10c.blv, arrival: entrance:d6_adit}` and drops its placeholder.
- **Playtests:** `playtest.yml` (20 monsters asserted and cleared on the walk; the egg cases' line; every re-entry goes
  out by the exit to D6 and back, so the leave event ends the visit and the refill runs as in the game),
  `playtest_exit.yml` (out to D6, position and facing asserted), `playtest_hostility.yml` (all hostile, no
  infighting). `four.sh` runs all three.
- Scratch root `output/studio_cal/dd10c/root_s13` (a fresh `cp -al` of assets_dev with a real copy of the tables);
  the old `root` is stale.

### Lines for A3

- The egg cases (map-local, D-62 Q49): "Split and cold. Whatever hatched here was eaten by whatever lives here now."
- Hector's D-27 line: not in the map (Hector is D1's; A3 checks `q-d7.yml`).

## Session 23 (A8): the cold nest (review row 52)

- The nest read as warm as the mine. It has its own theme `theme:cold`: MM6 6d18's blue-grey broken volcanic stone
  `vlcflord` (scale 2) on walls and roof, hoarfrost `7snow` underfoot, ambient 14 (was 12), its light pale blue
  (160, 200, 255) r 1400 (was grey (150, 165, 190) r 1200), and ice in three corners (the white crystal clusters
  `crys6` (1560, 2320), `crclstr` (3440, 2830), `crys5` (2000, 3150), clear of the walking line from the collapse to
  the diamond cavern; a first spot at (2330, 2400) stood on that line and was moved). The heat has gone out of this
  pocket: D-62 Q49's "Split and cold" now shows.
- Not done (optional in the review): a calmer rock than 7d35's speckled `cwb1` in the tunnels. The diamond veins
  (`xdvdiam`) are painted on cwb1, so the cavern's walls must stay cwb1 to match them; a second rock elsewhere would
  split the mine's look. Left for a decider if wanted.
- Before/after: `output/studio_cal/a8_s23/shots/dd10c_before_sheet_1.jpg`, `dd10c_after_sheet_1.jpg`.

## Session 25 (A8): the frost floor toned

The nest's hoarfrost `7snow` (mean 235 of 255, the whitest floor the MM6-MM8 sets have; Xeen borrows no MM9 art, D-44)
baked near white under the profile's direct 2.0 / bounce 5.0 / max 1.5. The profile
(`tools/lighting/baked_indoors/profiles/xeen_dd10c.yml`) now has A7's XD-19 numbers: direct 1.2, bounce 3.0, ambient
0.9, max 1.0 (before: `output/studio_cal/a8_s25/before/xeen_dd10c_profile_before_s25.yml`). Chosen by recomposing the
saved passes three ways (`a8_s25/rc/`: A 1.2/3/1.0, B 1.6/4/1.0, C the old scales with max 1.0); A is the only one
where the frost shows its texture. Installed by recompose (the same passes, no map change).

| Pose (`a8_s25/tours/dd10c_*.yml`) | before: mean / white px / lower half | after |
|---|---|---|
| cold nest | 151 / 12 % / 198 | 116 / 0 % / 161 |
| nest from the diamond cavern | 115 / 10 % / 136 | 88 / 1 % / 111 |
| nest west | 131 / 23 % / 163 | 107 / 2 % / 146 |
| nest north | 126 / 15 % / 148 | 99 / 2 % / 128 |
| lava gallery, adit, diamond cavern, collapse | 56, 87, 71, 59 | 46, 61, 51, 50 |

The rest of the mine is about a quarter darker (the old max 1.5 let the lanterns overbright the adit too); torches and
the lava still read. Sheets `output/studio_cal/a8_s25/shots/dd10c_before_sheet_1.jpg`, `dd10c_after_sheet_1.jpg`,
both nest rows in `dd10c_before_after.jpg`. Tests from assets_dev **4 of 4** (playtest 102, exit 23, hostility 21;
`output/studio_cal/dd10c/run/four_183944`); audit 0 / 0; `stale_bakes`: none.


## Session 26 (A8): mine door pictures (F12)

- The three plank doors (events 9-11: `door:adit`, `door:grotto`, `door:collapse`) showed the timber strip `trim9_32`
  tiled across their leaves; DD-10A's shared `tools/mine.py` `door()` now lays MM6's rough plank door `d2smldor` once,
  `fit`, over each 224 x 320 leaf. Edges and tops stay timber.
- Installed 00:57, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd10c/c005649`); audit 0 / 0;
  check_exits 0, check_drops 0.

## Session 28 (A8): D-89 identity (vein crystals, timber, rails, slopes)

The design review (`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, DD-10A/B/C severity 3: "a timbered adit with rails, then
rock boxes with flat vein panels") asked for timber sets along the galleries, rails and the cart deeper, irregular
stopes with slopes and rock pillars, each vein framed by shipped gcrys clusters. Generators reproduced the installed L4
first (snapshots `output/studio_cal/a8_s28/before/<key>/`).
- Shared (`dd10a/tools/mine.py` `vein_crystals()`): every vein panel, the false vein too, gets a cluster of three
  tapering crystal shards at both ends (out 56-108 from the wall line, clear of `rough`), in the gem's MM8 d37
  crystal: ruby `gcryswal`, emerald `gcrysc1` (trim_u 16 x 32, enlarged 5 times so one repeat covers a shard),
  sapphire and diamond `gcrysc3` (at each map's existing size). Shards stand square to the map (a turned tapering
  block's faces are not flat on whole units) and may stand on a sloping floor. `write_levels(..., identity)` writes
  `identity:` into L4's project.yml.
- DD-10C: the lava gallery's west end timbered (two sets across it), the rails run in from the adit's door to an
  abandoned ore cart; the diamond cavern's, the collapse's and the cold nest's floors slope. `identity: {shape: mine,
  family: 7d35}`. Audit 0 errors / 1 warning (cave shape: 16 % of the floor uneven against 30 %: the lava gallery
  stays level round its sunken seam, the grotto is a geode of steep crystal). check_exits 0, check_drops 0.
- Installed 01:50, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/dd10c/c014928`).
- Pictures: before `output/studio_cal/a8_s28/dd10c_before_sheet.jpg`, after `output/studio_cal/a8_s28/shots/dd10c_after.jpg`.
