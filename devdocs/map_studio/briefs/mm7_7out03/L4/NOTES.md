# Erathia (7out03, mm7): rebuild notes

## Round one (2026-11-14): a map nobody had rebuilt, with the outdoor words of batches O-A to O-F

Project `calib_erathia` (map `calib_erathia.odm`, map_stats row 9703; the other calib rows are 9603, 9701-9720, 9802,
9806, 9130-9135, and Castle Ironfist's rebuild is in `mm6_outd3`). Scratch: `output/studio_cal/mm7_7out03/` (`an/`
the original's export and analyses, `scripts/`, `cmp/cNN` the measures, `pics1/`, `pics2/` same-camera pictures,
`playcheck/` a desktop run of the play root, `repro/` tool defects, `run/` the walks). Binary: `openyamm-studio/build/oymap`
as it stood (nineteenth merge).

| Part | Start (c00) | End (c35) |
|---|--:|--:|
| **total** | **75.0** | **88.8** |
| total `--without rim` | 74.5 | 88.0 |
| heights | 68.9 | 78.2 |
| relief | 64.9 | 72.0 |
| cliffs | 91.1 | 96.5 |
| water | 97.3 | 98.1 |
| ground | 87.4 | 91.1 |
| roads | 99.4 | 99.4 |
| buildings | 38.4 | 88.3 (footprints 92.6 %, tops ~79 %) |
| decorations | 98.1 | 99.8 |
| spawns | 66.1 | 80.6 |
| events | 52.8 | 88.0 |
| rim (skyline) | 83.1 | 85.1 |

**Not within the outdoor band: 88.8 against 90.** What is left is mostly the land (heights 78, relief 72, rim 85: see
"The land" below) and forms the words do not say; nothing was bent to the measure.

Walk: `playtest.yml` (39 steps: new game into the map, Griffin's Rest, Queen Catherine's Smithy and the town hall
through their built doors, the healers' chest, the castle side door refusing without Catherine's Key, off the south edge
to the Bracada Desert and back) two of two on the end project (`run/final1.log`, `run/final2.log`; also `w1..w3`).
Faces in one plane (`oymap audit --original 7out03.odm` on the play root, `audit_final.txt`): 9 pairs, 3 as the
original's (in the Lady Catherine, taken as it is), **6 new, all studio defects** (below): above the original's 3.

Installed: `oymap install` into `output/studio_play/rebuilds_root` and `outdoor_materials.py --build`; a desktop run
of the play root loads it (`playcheck/run.log`, eight pictures `playcheck/0N-*.png`). Run:

    SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated erathia --world mm7 --map calib_erathia.odm --assets "$PWD/output/studio_play/rebuilds_root" --visible --seconds 0

### How the project was written (scripts in `output/studio_cal/mm7_7out03/scripts/`, each run on a copy, diff read)

- **First sketch** `gen_first.py` (New Sorpigal's, adapted): 32 x 32 spot heights in units of 32, water outlines,
  ground zones (grass, dirt, snow: the map's third tile set, row 342, is MM7's snow), the roads traced over the
  original's road tiles (54 lines, to the map edge where they leave it), spawn points, the town's people, decorations as
  scatter with their **decoration groups** (5, 6, 7 forests, 10 flowers) and the fruit trees, the brook sounds and the
  town's planted things placed. Then `gen/describe.py` for the houses (35 said).
- `r1_things.py`, `r2_things.py`, `r3_bandit.py`: the things describe.py left out (below, by word), the signposts' arms
  (board and way from each original board), the fruit trees' events, the houses it could not fit.
- `merge_parts.py`: describe.py's L and T houses were overlapping boxes whose walls ran through each other (355 pairs
  of faces in one plane); each group of boxes of one foot and height became one bent outline part on the boxes' own
  edges (the nineteenth merge's concave outlines). `r4_fixes.py` the remaining shared planes, each by the original's
  line. 355 pairs to 6.
- `floors.py`: every house on its original floor (the town's terraces: plots left to their land's mean sat 64-224 low);
  `r5_land.py`: `foundation: 0` (the original's walls end at their floors), Fort Riverstride's banks (terraces at 1024)
  and riverbed (a cut at 0), the viaduct's bridgeheads, Blayze's notch (a cut at 864).
- `r6_forms.py`, `r7_forms.py`: forms redrawn from the original's faces where `tops.py` (Harmondale's replica of the
  measure's building form) showed the most lost: the fort's upper storey, the town hall, the viaduct's deck width, the
  quay's T, the plaza's courts, troughs and steps, the castle keep's ring, the stone decks under three houses, the
  hidden tomb's mound, the Alchemist and the magic shop, the House 10 porches. `r8_events.py`: homes say "House";
  plaza and fort carry no event of their own. `r9_scatter.py`: the 7dec33 on the lake `on: water`, lone rocks `steep`.
- The land: `maze.py` (the trench labyrinth as 25 level terraces and 25 knolls as `peaks`), `peaks_points.py` (height
  points on the original's peaks and hollows the build misses), `crests.py` (40 `ridges` along crests and valley
  floors), `cliffs.py` (206 cliff lines where the original falls 800 or more), `levels.py` (6 town terraces),
  `ground.py`, `water.py` (the lake cut through its islands), `spawns.py` (one area per original marker).
- `apply.sh` replays everything after `an/sketch_c11.yml` in order (the scripts that pick by a build's misfit read the
  saved `an/last_diff_c14.npy`, `an/last_diff_c21.npy`).

### The new words, where the original has their forms, and how they did

- **`kind: culvert`** (the three sewer outfalls, Sewer_S/_E, MTSewer_N): pipe mouths 488 x 504 with a 48 ring
  (`pipe`), the dark face 384 back carrying the original's MoveToMap (501, 506, 507), "Sewer" (466) on the rest, water
  out over the bank. Good: the pictures match (`pics1/diff/06..08`). The town outfall's grating of bars before its dark
  face has no word (a portcullis is a door's); its `outflow: 0` (the original's water there is the lake's).
- **`bridge.arches`** (the viaduct, Bridge_E/_1): deck 512 with kerbs 64 x 80 at 1328, three arches on piers 128,
  soffit 1280, piers to the river; the end ramps as `stairs` with `ramp`. Good (`pics1/diff/05`), but the original's
  spans are 384, 576, 384 (the middle wider): the word has one span.
- **Gatehouse over the river** (Fort Riverstride): said as `kind: wall` across the river with a pointed `gate` over the
  water, the upper storey a building on a hidden `deck` at the block's top. Four limits of the word (gaps 2-4 below):
  the block (1920 thick) had to be two walls of 960; the gate is 512 wide and 576 high where the original's arch is
  about 640 wide and 1000 high; the road's passage through the block along its line has no word.
- **Scatter `group`** + **`set_sprite`/`hide` of `group:<n>`** (the seasonal trees, load event 500): three load
  events by `condition: {season: ...}`: autumn and winter pictures for groups 5, 6, 7, flowers (10) hidden, the fruit
  trees bare; spring/summer pictures. Builds; not seen in a winter game (the pictures are of a summer day).
- **`events[].trigger: leave`** (the griffin kill check, event 2): built as the original's onLeave.
- **`kind: cave_mouth`** (the hidden tomb, Ninja__1/_2): a DIRT mound with the dark face (508), floor 0 in its hollow.
  The original hides the door face until the five stones are played (SetFacetBit): no word (and the game's outdoor
  click on a face shown by an event is a known engine limit), so the door is open here. The five stones are platforms
  with the original's Lua (402..406).
- **`kind: doorway`** (the bandit caves, Bandit_): a CWB frame looking south-east; its turf roof has no word.
- **`kind: tent`** (the healers' pavilions): closed, walls 256 leaning 24, ridge 400, houses 926..928. A tent may not
  carry a `hint`, so the original's "Tent" (91) on the canvas is missing; the original's roof is a low hip with a
  cross ridge, the tent's a gable.
- **`kind: deck`** (the quay, DockPrt_S*): a T at 192. A chamfered outline (the pier heads' cut corners) put posts in
  one another (4 pairs); drawn square-cornered.
- **Round parts, cones, eaves/fascia, parapets, `eaves_walls` with own eaves, concave outlines** (Castle
  Gryphonheart): the bailey a solid block 512 high inside a parapet of 80 (7t1butts), four round towers (12 sides,
  walls to 3296, a band 48 and 32 out, a cone of Her1rf to 3552), the west gate block, the keep as two wings bent round
  its open court (hips falling to both sides from the ridge at 3680, court eaves 288), the court turret. The survey
  said battlements: the original's parapets and tower tops are plain; no battlements were drawn.
- **`fountain` with `size`** (the plaza troughs, 210) and a ring fountain (208), **`platform`**, **`stairs`**: the
  plaza's courts and steps. The troughs' and pool's water lies 64 under the court's top in the original; a basin
  cannot be sunk into a platform (gap 3), so they stand on it.
- **`heights.terraces`, `cuts`, `peaks`, `ridges`, `cliffs`** (the maze, the town, the gorge, the fort's river, the
  notch): see the land.
- **`kind: model`** (the Lady Catherine): taken as it is, as Ravenshore's ships (no word says a ship).

### The land

Heights 68.9 to 78.2. Of the error left, 43 % lies on nodes beside drops of 1200 or more and 29 % beside drops of
600 to 1200 (Erathia's mountains are sheer: 2292 cells too steep to walk). Cliff lines, points at peaks, hollows and
ledges, crests and terraces each moved the heights by tenths; another pass of points at lower thresholds moved
nothing. The maze is held by 25 terraces and 25 knolls (its box mean error 778 to 469); its thin 4800 walls one node
wide (x 18, y 83..92 and the like) are cliffs and ridges but a terrace's filled outline may still cover a wall node.
Not tried: `heights.rough` to raise the relief (it would raise the relief figure without being the original's land).

### Missing words (most harmful first)

1. **A roof round an open court** (Castle Gryphonheart's keep GH1_W_3: one roof whose ridge ring at 3680 falls to the
   outer walls and into the court). Drawn as two bent wings meeting at x 768 (two seams). Field: `roof: ring` (or
   `court: <outline>` on an outline part).
2. **A gate through a thick wall** (Fort Riverstride): `wall.thickness` stops at 1024 (the block is 1920); a gate's
   `height` stops at the wall's height over its highest ground (the arch over the riverbed is about 1000, the wall is
   576 over the banks); a gate must keep the wall's thickness clear of both ends (512 wide, not 640). Repro: the
   project's `thing:fort_n`/`fort_s` with `thickness: 1920` or a gate of 1024 high (validate refuses).
3. **A passage along a building** (the fort's road at 1088 east-west through the block under an arch) and **a
   recess in a part's wall** (the castle's gate door 320 back in the gate block; the town hall's door in a porch 256
   into the hall; the Alchemist's under its eaves). Field: `doors[].recess: <depth>`; `parts[].passage`.
4. **A basin sunk into a platform** (the plaza's troughs and pool, water 64 under the court): `platform.holes` as
   parts have.
5. **One name on several things** (the original's "House", 51, on 22 homes; "Well", 201, on five wells): each built
   thing says its own, so 19 events more than the original (events 88 %; town_feel counts 15 wells and fountains for
   the original's 8). Field: `same_event_as` for a `hint` (`hint_as: <id>`).
6. **A `hint` on a tent** (the healers' "Tent", 91).
7. **Arches of their own spans** (the viaduct: `arches.spans: [384, 576, 384]`).
8. **A pent roof round a storey** (House 10E/W: a skirt roof 128 out at the first floor).
9. **A grating in a culvert** (MTSewer_N_1's bars).
10. **A turf roof over a doorway** (Bandit_), **hanging shop signs between two buildings** (wep arm S: sgWEAPON, 7sgarm).
11. **A pavilion roof** (HealerTent_*: a low hip with a cross ridge over leaning canvas walls).
12. **A sequence puzzle** (the five stones: Lua here) and **a face shown by an event** (the tomb's door).
13. **A texture the original uses that the catalogue lacks**: `Hhr1bWALL` (Griffin's Rest, Havest and Talreish
    residences) is refused for mm7 (`oymap assets hhr1bwall --world mm7` lists none; the game finds it); 7hhr1b drawn.

### Tool defects (repros in `output/studio_cal/mm7_7out03/repro/`)

- **Diagonal sign arms overlap at the post** (`sign_diagonal_arms`: a sign with arms `ne` and `sw` builds 2 pairs of
  faces in one plane, 25 square units each): signposts 1 and 2 (the original's 2-way BN signs). 4 of the 6 new pairs.
- **A door cut into a gable lies on the gable** (`aframe_door_gable`: a gable part, walls 128, `door_height: 256`,
  door on the gable end: the door face and the gable face in one plane): Blayze's A-frame. 2 of the 6 new pairs.
- **Posts at a deck's chamfered corners stand in one another** (the quay with its pier heads' cut corners: 4 pairs;
  `cmp_c32.build.log`; not reproduced on dry land in a small project).
- **`oymap install`'s way back follows `arrival_side`**: with the original's own row (Erathia's east edge arrives on
  Harmondale's "right") the install pointed Harmondale's *east* edge (7out02's Right column) to the rebuild in
  `rebuilds_root`. The project says `arrival_side: west` (Harmondale's west edge is the real way back) and the root's
  7out02 row was put back by hand to the original's Right column (7out04 down 7): the only file touched outside the
  install, a replaced copy (one link), not `assets_dev`.
- `town_feel.py` counts a well's `hint` as a second well (15 against 8 on the map); see gap 5.

### Town feel (`town_feel.py`, the original 0 figures outside)

Six outside: wells and fountains on the map 15 and in town 10, buff specials in town 5 (gap 5's per-thing names),
flat ground in town 0.62 against 0.73 (the terraces the coarse land does not hold; 6 town terraces were drawn), tavern
rank 0.06 against the original's 0.09, flowers in town 0.253 against 0.244 (the same count, placed by the build).

### Unsure

- The spawn markers of index 8 (slot 3) and 11: the original's row has no third monster; the build places them.
- The travel row's "right" for the east edge (above): read as a quirk of the original's table.
- The seasonal events were not seen in a game set in autumn or winter.

## Round two (2026-11-14/15): batch O-H's words and every building beside the original's

Binary `openyamm-studio/build/oymap` after the O-H merge. Backup of the project before the round:
`output/studio_cal/mm7_7out03/r2_backup/`. Scratch: `output/studio_cal/mm7_7out03/r2/` (`measure.sh`, `cmp/r2a..r2d`,
`scripts/`, `run/`), pictures `output/studio_cal/mm7_7out03/bshots/r2a` (all 53 buildings, 1273 views) and `bshots/r2b`
(the 26 changed ones, 660 views), compact sheets `r2/sheets_a/`, `r2/rows_a_*.jpg`, `r2/rows_b_*.jpg`.

| Part | End of round one (c35) | O-H words (r2a) | End of round two (r2d) | r2d without `heights.nodes` |
|---|--:|--:|--:|--:|
| **total** | **88.8** | **91.3** | **91.4** | **89.5** |
| total `--without rim` | 88.0 | 89.8 | 89.9 | 88.7 |
| heights | 78.2 | 87.4 | 87.4 | 78.2 |
| relief | 72.0 | 78.7 | 78.7 | 72.0 |
| cliffs | 96.5 | 97.5 | 97.5 | 96.5 |
| water / ground / roads | 98.1 / 91.1 / 99.4 | same | same | same |
| buildings | 88.3 | 88.0 | 88.7 | 88.6 |
| decorations | 99.8 | 99.7 | 99.7 | 99.8 |
| spawns | 80.6 | 79.8 | 79.8 | 80.6 |
| events | 88.0 | 95.3 | 95.3 | 95.3 |
| rim | 85.1 | 86.5 | 86.5 | 85.1 |

**`heights.nodes` (the lead's ruling: counted like a whole-model import).** Taken: 2749 of the original's nodes in 26
blocks of the 16 x 16 tiles, every node within one of a node beside a drop of 1200 or more (8 neighbours), inside the
square 19..109 (`output/studio_s4u/gen_nodes.py <sketch> <orig heights npy> 1200 1`, blocks at [90, 25], [96, 19],
[56, 33], [64, 33], [80, 32], [99, 32], [73, 48], [80, 48], [96, 56], [19, 64], [33, 67], [48, 65], [64, 71], [81, 77],
[103, 64], [19, 80], [32, 80], [48, 80], [64, 80], [80, 80], [97, 81], [19, 96], [32, 96], [48, 96], [92, 96], [96, 96];
each block's `notes` says so). 69 of them lie in water and keep the water's level. With them 91.4 %, without 89.5 %
(both measured on the same project, `r2/measure.sh` drops the block for the second).

### O-H's words applied (from `output/studio_s4u/eall`, `ewords.py`; the copy and the project differed only by them)

- `heights.nodes` (above).
- Fort Riverstride as one `kind: wall` 1920 thick, a pointed gate 640 wide and 1000 high over the riverbed,
  `passage_along` at 1088 (384 wide, 320 high): the two halves of round one and their notes gone.
- The keep of Castle Gryphonheart one box round its `court` (eaves 288), its ridge ring at 3680; the side door now
  `wall: w` of that box.
- `hint_shared` on the 22 homes ("House"), 5 wells ("Well") and the three healers' tents ("Tent", now allowed): events
  88.0 to 95.3.
- The plaza's troughs as `holes` 64 deep in their strips (`raise` 128 to 64).

### Every building pictured beside the original (`building_shots.py`), what changed

Read from the original's models with `r2/scripts/hull.py` (plan outline per level), `doorpos.py` (door faces) and
`texcmp.py` (texture areas per pair, `r2/texcmp_a.txt`); edits in `r2/scripts/r2_b1.py` .. `r2_b5.py` (each run on a
copy in `r2/tryN`, validated and built, then copied in).

- Royal Steeds (Stables_S): was one closed box under a lean-to; now the closed barn (west, gable ridge north-south,
  1088 to 1216) and the open stall on posts under a low lean-to (east).
- Griffin's Rest: timber kit (grey planks) to the rich panels (7hhr1bs2, Hhm1rf roof) as the original's.
- Bank of Erathia: a stepped cross with four gables to the original's octagon under a hip cut flat (`cap` 160).
- Master Guild of Body: stepped cross with gables to the ten-sided hall under a hip, its double door 256 back under the
  roof between posts (`porches` `recess`).
- Lead Transformations: grey stone kit and gable to the original's hhm2 plaster panels and a hip.
- Her Majesty's Magics: gable to hip, the door 256 back under the shop's own roof between posts.
- In Her Majesty's Service: a flat-topped outline to the hall with its cut north-west corner (door on it, a post under
  the roof there), a capped hip, the south annex under its own low gable; trim TRIM3_16a.
- Paramount Guild of Spirit: stepped outline to six walls (north corners cut), capped hip, door on the south bay 2.
- Adept Guild of Mind: trim 7trimd. Eversmyle and Julian (Hmhouse_j): the closed front room became the open porch on
  posts it is. Wolverton and Talion (Hphouse_j): stepped crosses to octagons under a steep capped hip (doors on the
  octagon's west and south walls as the original's).
- Ravenswood (Hut-a_E): a square box turned 45 to the round hut under a thatch cone.
- Barnes Home: a pyramid 496 high of plaster to a low hip of 7hhr1rf (128), walls 7hhr1bs2.
- Castro, Ravenhill (Hpoor_j1): tan plaster (hhm2) to the original's dark stone (Hhp2b1, Hhp2el/ers), timber gables;
  Laraselle, Tish timber gables; Guthwulf, Agraynel Hhp2b2 gables; Hillier 7t1cabs gable (all had the kit's stone
  Hhm3ch gable).
- House 10 (Org, Quixote): Hhm3 corner panels instead of the plaster kit's tan ones; the porch parts on posts removed
  (the original has none: House 10E_1/W_1 are the roof's ends).
- Blayze's A-frame: no plaster windows or posts on its stub walls.
- House of Solace: rebuilt from the original's faces: the stone hall (CHB1, 352, band), a storey of the rich panels
  over all of it (128, windows), one hip, two square corner towers to 864 each with a rich lantern under a small hip;
  the double door in the west front.
- Steadwick Townhall: the door 256 back in the hall (`door.recess`, O-H); the roof over the entrance 512 wide (was
  1024 on two tan posts at its ends); walls 7hhr1bs2.
- Talreish Residence: the box under the overhanging storey became its one pillar (7hhr1p, 128 x 48); the storey
  reaches 856 as the original's.
- Castle Gryphonheart: the plaster kit's tan corner panels (they read as windows on the bailey) gone; the gate block
  at the original's foot line, 192 thick, its door at the back of a round-arched recess 512 wide, 448 high
  (`porches` `recess` `arch`).
- Fort Riverstride: the block in the original's darker Hhp2b2; the keep's storey with its slit windows (Ch1bw).
- Signposts 1-7: boards 256 x 96 to the original's 96 x 32 (`width`, `board_height`).

Coplanar pairs I made on the way (castle gate into the bailey's top, the training hall's eaves over its porch) were
taken out (r2_b3.py): end 3 pairs, all the original's.

Not looked at again after the last batches: the castle gate (the r2b picture was taken with the 256-thick gate of
batch 2: the arch showed as a band without its opening; batch 3 changed the gate after that picture), Talreish,
House 10, Barnes's walls and the signposts. They build and measure; their pictures are still to take.

### What still differs, with the word it needs

1. **Walls leaning out** (Castle Gryphonheart's bailey 150 over 512, its towers about 40 at the top): `batter` takes only
   an inward lean (validate: "must be greater than 0"). Field: a negative `batter` or `flare`. The bailey is drawn
   at its top line.
2. **The castle's side door on the court wall at the bailey's top** with the stairs (456) up the east side: not
   attempted; the door stays on the keep's west wall.
3. **A half-hip (Dutch gable)** (House 10E/W: the roof's ends hipped up to 992, gabled above with stone gables set
   back 16). Drawn as a gable with eaves 64.
4. **A door on a closed tent and a pavilion roof** (the healers' tents: a wooden door Hhm3d on the canvas, a low hip
   with dark frame edges): the tents are plain gables without a door picture.
5. **A recess open at a corner** (the magic shop's and guild of Body's porches run the whole front between corner
   posts; validate refuses a recess reaching the wall's end): drawn over the middle two bays.
6. **Platforms with cut corners** (the alchemist's octagonal deck, the Spirit guild's twelve-sided deck: the latter
   has none here).
7. Round one's gaps 7-13 (spans, pent roof, grating, turf roof, hanging signs, sequence puzzle, Hhr1bWALL) stand.

### Checks

- `oymap audit --original 7out03.odm` on `rebuilds_root`: 3 pairs, 3 as the original's, 0 new (`r2/audit_final.txt`).
- Walk (`playtest.yml`, 39 steps) two of two against `output/studio_play/rebuilds_root` (`r2/run/f1.log`, `f2.log`);
  also two of two on the mount after the O-H words and after batch 2.
- Installed into `rebuilds_root` with `oymap install` and `outdoor_materials.py`; `outdoor_travels.txt` unchanged
  by the install (O-H's way-back fix).
