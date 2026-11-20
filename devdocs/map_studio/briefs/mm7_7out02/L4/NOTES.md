# Harmondale (7out02, mm7): rebuild notes

## Round two after outdoor batch nine (2026-11-13 evening; round seven overall)

Named "round two" by the lead, after New Sorpigal's and Shadowspire's; the older "Round two" further down is the
morning's. Project before: `output/studio_cal/mm7_7out02/r7_backup/` (`r2_backup/` holds the morning's round two and
was left as it was). Scratch `output/studio_cal/mm7_7out02/r7/`; measures `cmp_start`, `cmp_end` (and `_old`,
`--without rim`) by `scripts/measure7.sh`; trials by `scripts/quick7.sh` on `r7/try`. Every edit is a script in
`scripts/` applied in order by `scripts/apply7.sh <folder>` to the backup's sketch (its diff checked each time).

| Part | Start | End | Start `--without rim` | End `--without rim` |
|---|---|---|---|---|
| **total** | **89.92** | **90.23** | **86.91** | **87.22** |
| buildings | 87.62 | 89.71 | 87.62 | 89.71 |
| every other part | unchanged | unchanged | unchanged | unchanged |

Heights 86.61, relief 74.19, cliffs 96.99, water 89.90, ground 84.06, roads 95.05, decorations 96.29, spawns 100,
events 98.28, rim 90.83. Buildings: footprints shared 92.44 % (start 90.38), tops alike 80.66 % (start 76.97).
**Within the outdoor band (90 %).**

### Batch nine's words: none apply

`oymap export` of the original: `tile_set_lookup [90, 126, 342, 414]` (MM7's usual grass, water, snow, road rows; the
build lays the same), no sky texture, no `7out02_mist.scene.yml`, no row for 7out02 in `engine/rendering/sky/sky.yml`
`maps`. So no `tile_sets`, `mist` or `sky_theme`. The measure's change (invisible faces are not tops) did not move the
footbridge's score by itself: the deck's form was wrong (below).

### Faces in one plane (`scripts/coplanar_odm.py`, Shadowspire's, on the build's export)

| | pairs facing the same way |
|---|---|
| the original 7out02.odm | 65 (62 between its two identical Temple3_N models, 1 Temple3_N/_1, 1 HHP4E) |
| start (round six's project) | 273 |
| end | 50 |

Left: 43 the studio's sign defect (batch ten: the picture 1 unit before its board: 14 shop signs, both signposts' three
arms, the gate sign, and the bank's new wall sign); 4 the town hall's two eaves soffits overlapping at the wing's inside corner (no eaves per wall);
2 the fort's hatch and the chest in its pit (a platform reaches to the ground, so its sides stand in the chest's
planes); 1 the shrine altar's hidden plinth top in the shrine floor's plane (inside the altar).

### What changed (each from the original's faces, `scripts/faces7.py r7/orig.json <model> <x0> <y0>`; bay textures
read from the original at each bay's middle by `sk7.bays`)

- **Footbridge** (`bridge7.py`): the original's deck sags (landings 640, middle 544, rails 768 to 864, no piers);
  round three's `rise: 96` arched it the wrong way, on piers, under a kerb of 352 read off the invisible barrier. Now
  level at 592, kerb 208, `piers: 0`. Buildings +0.24.
- **Town houses** (`hhm7.py 1|2|3`: Bowes HHM5S, Temper HHM5N, Mark Manor HHM6N): ground storey 1152 x 384, a bump
  256 x 128 on one long side, the upper storey jettied 32 out on its soffit, the main gable 256 and the bump's cross
  gable 128. Round six: the bump a second box over the whole depth (Mark Manor's main box twice). 45 pairs.
- **Tavern** (`tavern7.py`): an L of jettied storeys (wing gable north-south, hall gable east-west, the north bump
  with the door on it); round six's hall ran through the wing and a lean-to "back range" stood where only the bump is.
- **Bank** (`bank7.py`): one eight-sided block (corners cut 128) under a hip cut flat at 448 (`cap`), the 7sgbank sign
  west of the door (no round had it); three overlapping gabled boxes before. 20 pairs.
- **Guild of Body** (`bodyguild7.py`): its wings 128 deep south of the block (were 384 through it).
- **Temple** (`temple7.py`): the tower one block 384 square from the front (64 too far north and drawn twice to 512
  and 896), windows in the 512..768 row only, nave eaves 32 with no fascia (ridge 641 as the original's).
- **Otto's Oddities** (`magicshop7.py`): two wings with cut-back north ends, the middle block with the door in the
  court, the upper storey under its hip; four overlapping boxes before.
- **Town hall** (`townhall7.py`): the west wing x 128..640, y -102..410 (it ran 1408 through the east block).
- **Castle** (`castle7.py`): the main body in two boxes each side so the ruined front towers stand beside it.
- **The Arbiter's base** (`arbiter7.py`): a sixteen-sided middle whose sides are the arms' inner ends.
- **Hillsmen/Stillwater** (`doublehouse7.py`, HHM7W) and **Farswell/Hume** (`longhouse7.py`, house16_S, the same
  design turned): one block 768 x 2048 with end gables 512 deep (ridge 352 up, eaves 32) and the middle's gable, the
  windowed annex 168 high under its lean-to; round six had a lean-to end 320 wide and the annex through the house.
- **Guild of Air** (`airguild7.py`): the front wing before the block (it ran from the block's north wall).
- **Training hall** (`training7.py`): the twelve-sided hall's south flat 8 inside the block's south wall (the
  original's hall has walls only north of the block); hidden, removes 2 pairs.
- **Guild of Water** (`waterguild7.py`, `waterpools7.py`): p4, p5, p7, p8 were copies inside p1 and p3; the two
  fountain basins as the original's L of water at 48 in a kerb 32 wide and 80 high with the court open (round two's
  kerb was a solid block over the court); the door CHB1DL.
- **The fort's trap plates** (`forttrap7.py`): 8 back from the hatch's hole (their sides were in the pit's walls).

Each was checked in the game (`r7/pics_changes/`, `r7/pics_end/` against `r7/pics_before/`, 18 same-camera pairs,
edge agreement 0.674 before, 0.702 after): Temper 0.72 to 0.80, the tavern 0.72 to 0.78, the bank 0.67 to 0.74,
Otto's 0.77 to 0.82, the double house 0.79 to 0.83, the footbridge 0.47 to 0.55; none lower by more than 0.01.

### Walk and install

`playtest.yml` unchanged (69 steps), two runs of two on the end project (`r7/walk_end_1..2.log`; also `walk_a_*`
after the first edits). Installed in `output/studio_play/rebuilds_root` with `outdoor_materials.py --build
r7/build_play`; a desktop run loads it (`r7/playcheck/arrival.png`, `run.log`). Build warnings the same 13 as at the
start.

### Missing words (round seven)

- **A bridge that sags** (`rise` below 0) and **a bridge's open railing** (posts and a rail over an undrawn barrier,
  as parts have): the footbridge.
- **Roofs that join**: a cross gable carried into the main roof (the town houses' bumps, the tavern's hall into its
  wing, the double houses' middles into their end gables, Otto's hips into its flat middle); each part's roof stands
  alone, so a gable end shows above the neighbouring slope.
- **Eaves on chosen walls** (the town hall's wing: its soffit overlaps the east block's).
- **A row of its own in `upper_walls`** (the temple tower's single window row; drawn as two stacked parts).
- **Bays narrower than 96** (the bank's corner walls carry two 90-wide panels in the original).
- **Panels squashed to a short wall** (the annexes' Hhm1bw windows fill 168 in the original; the studio crops 256).
- **One event on several parts** (the Guild of Water's channels do not let the party drink; the basins do).
- **Dormers** (the tavern's and Temper Residence's) and **a roof cut flat along a ridge** (the double houses' middles).

### Unsure

- The temple's belfry reads dark between its pillars where the original shows sky (as at the start of the round).
- The training hall's south flat drawn 8 in: not a shape anyone sees; said here because it is not the original's line.

## Round six (2026-11-13, `openyamm-studio/build/oymap` of the eleventh merge, then the twelfth: outdoor batch eight)

Project before round six: `output/studio_cal/mm7_7out02/r6_backup/`. Scratch: `output/studio_cal/mm7_7out02/r6/`;
measures `cmp_start` (start), `cmp_c` (end of my own changes, eleventh-merge binary), `cmp_d` (end, with batch
eight's lines, twelfth-merge binary), each with `_old` (`--without rim`), by `scripts/measure6.sh <tag>`; single
trials by `scripts/quick6.sh <tag> <copy>` into `r6/q_<tag>`.

| Part | Start | Start `--without rim` | End (d) | End `--without rim` |
|---|---|---|---|---|
| **total** | **89.18** | **86.20** | **89.92** | **86.91** |
| heights | 86.04 | 78.23 | 86.61 | 78.68 |
| relief | 73.59 | 68.32 | 74.19 | 68.59 |
| cliffs | 96.77 | 89.79 | 96.99 | 89.99 |
| water | 88.65 | 88.65 | 89.90 | 89.90 |
| ground | 84.04 | 84.04 | 84.06 | 84.06 |
| roads | 92.65 | 92.65 | 95.05 | 95.05 |
| buildings | 87.73 | 87.73 | 87.61 | 87.61 |
| decorations | 96.02 | 96.02 | 96.29 | 96.29 |
| spawns | 100 | 100 | 100 | 100 |
| events | 95.00 | 95.00 | 98.28 | 98.28 |
| rim (skyline) | 90.55 | (no weight) | 90.83 | (no weight) |

**Not within the band: 89.92 against 90.** Every change below is the original's form; nothing was bent to the
measure. What is left is mostly a measure fault (the footbridge, below: about 0.2 of the total) and gaps.

Walk (`playtest.yml`, 69 steps): two runs of two on the final project (`r6/walk_d_1..2.log`; also `walk_a_*`,
`walk_b_*` before the batch-eight lines), no jump. Installed: `oymap install ... --root output/studio_play/rebuilds_root`
with its terrain material file (`outdoor_materials.py`); a desktop run loads it (`r6/playcheck/arrival2.png`).

### What moved the scores

- **Height grid in units of 32** (`scripts/grid32_6.py`): the samples are the same spot heights, unrounded (the
  original's own height step; 359 of 1024 were rounded by 32). Heights +0.35, total +0.11.
- **The outlet stream** in two stretches (its narrow head x 79, y 97..104, 3 wide; then 4 wide down the original's
  centre line): water 88.65 to 89.90.
- **The spire knoll** (G4) as the original's stepped pyramid: two ring ridges (768, 1600) round the tip point (3200),
  replacing round one's cliff line through the tip that cut its east half down; its grass skirt (a ring line, width
  2) and snow cap (round one's grass polygon had a dirt polygon inside it, so nothing was laid: the knoll was bare
  dirt in the pictures where the original's is a white cone on grass). Heights +0.18.
- **Roads on the original's cells**: the valley road north (y 14..40), the bend to it, the trunk south of the gate
  (y 46..62), the trunk's end, the west road's crest and the south road's bends (y 104..116). Roads 92.65 to 95.05.
- **Castle**: no title, so its walls say nothing (the original's castle models carry no event; only the gate's
  leaves, event 301); the door is in `doors` with the title. Events +0.8.
- **Batch eight's lines** (`output/studio_s4i/scripts/proof.py h`, copied to `r6/proof_batch8.py`, applied to the
  project; before: `r6/sketch_before_batch8.yml`): the trap's three other plates `same_event_as: thing:fort_trap`
  (one event on four plates, as the original's 236), the three wells' windlass frames, the town hall's `chbw`.
  Events 95.80 to 98.28, buildings +0.06.
- **Mind guild and Kern Residence** (`scripts/stonehouses6.py`; from the faces of Mind GuildW/_1 and house 12N,
  12N_1, 12N_2): a plank deck 32 high (7t1beds1, top 7t1books1), the core on it (Mind: CHB1S stone, the arched double
  door CHB1DL/DR on the west wall; Kern: Hhp1b, door and window on the north wall), a gable roof (Her1rf, gable ends
  Hhp1b), porches on posts (TRIM2_32) out to the deck's edge (Mind all round, Kern east and west, 1024 long). Each
  had two identical hip-roofed boxes over the whole deck (the doubled parts of round four's scan). Buildings -0.15:
  the honest form measures lower; kept. Pictures `r6/pics_changes2/diff/01..04` (0.44 to 0.58), `r6/pics_porch/`.
- **Weider Residence**: gable ends in 7trimda planks, eaves 48, fascia 32 (TRIM2_32a), as Human House1_E; it had a
  stone gable flush with the walls (`05-weider-e.png`).

### Decided against

- **The trap as the dais's own step event** (tried before batch eight: `r6/trytrap`): validate accepts `trigger`,
  `condition` and `effects` on a `kind: building` structure and the build writes no event; the trap vanished. Batch
  eight's `same_event_as` then said it properly.
- **A ridge along the white massif's north cliff top** (F7, y 104, the original's heights): with `slope: 2` it
  raised the ledge across the cliff (the slope leaks to the low side); with `slope: 0` it leaves a step the original
  has not. Both wrong shapes; +0.05 at most. Not kept (gap 2).
- **Ground outlines at a finer tolerance** (round two measured +1.4 for ground): nearer a trace; not done. Ground
  polygons moved out by half a cell to undo the build's half-open test: refused (ground takes whole cells).
- **A lake bay at water level** (points at 0 and a wider outline at x 84..88, y 77): the water did not spread there;
  not kept.
- The footbridge's high deck to meet the measure's 992: a wrong shape (below).

### Gaps (most harmful first)

1. **The homes' walls say the home's name**: the original's homes share one name event ("House", 265) on all their
   models; plots cannot share an event (`same_event_as` is for structures). Two of the rebuild's events are extra
   (Temper Residence, Withersmythe's Home): events 98.28 instead of 100. Field: `same_event_as` (or a `hint`) on
   plots.
2. **A cliff's top height**: a cliff's top nodes take the grid samples behind it, so where the land rises from the
   cliff's edge (the white massif over the ledge, F7; the gate knoll's north face; the hill north-east of the fort)
   the top stands 300 to 1000 too high. The heights' largest losses lie within a node of cliff lines (0.061 of the
   part's 0.134). Field: a cliff `top` height per point.
3. **A bridge's railing**: the original's footbridge has posts at its ends, sloping hand rails (TRIM2_16a, 720 to
   864) and an invisible barrier to 992; the rebuild's `kerb: 352` (round three, read off the invisible faces) is a
   solid plank wall (`r6/pics_changes2/diff/12-footbridge-w.png`). Field: `railing` on bridges (as on parts: posts,
   rail, undrawn barrier).
4. **A roof continuing over a porch**: the originals' porch roofs run on from the main roof's slope above the wall
   top (Kern: 288 at the posts to 464 under the main roof); a porch's back may not be above its wall's top, so the
   porches lie under the eaves at nearly flat pitch. And posts every 128 along a porch (`post_every` is for open
   parts only). Fields: `porches[].from_roof`, `porches[].post_every`.
5. **A gable roof's overhang at the gable ends** (barge boards: Weider, the Mind guild, the long house): eaves only
   at the eaves sides.
6. Still open: round five's 3, 5, 6; round two's 5, 8, 9, 10.

### Tool defects (round six)

- **`oymap compare` reads invisible faces as building tops**: the original's footbridge (NewOut2Bridge_) has an
  invisible, untouchable ceiling (7trimda, attributes 0x20003108) at 992 over its whole span and invisible barriers,
  so its top reads 992 over the deck where one walks at 544..640; the rebuild's true deck loses about 405 of the
  2570 footprint pixels the whole map loses in form (`scripts/tops6.py`, a replica of the measure), about 0.2 of the
  total. Repro: `output/studio_cal/mm7_7out02/repro/invisible_faces/run.sh`. Flag 0x2000 is FACE_IsInvisible.
- **A `kind: building` structure takes `trigger: step`, `condition` and `effects` silently and builds no event**:
  `output/studio_cal/mm7_7out02/repro/building_step_event/run.sh`.
- A ground `line` of width 1 drawn as a closed ring lays nothing (as the schema says for one line of corners), with
  no warning.
- A lake polygon over land that the grid holds above the water's level draws no water there and says nothing.

### Pictures (round six; same camera in both maps)

- **Changed places** (`r6/pics_changes2/`, 13 pairs, 0.558): best the trunk (0.70), the castle gate (0.70), the
  stream (0.69), the north road (0.65); the Mind guild 0.54/0.58, Kern 0.54/0.44, Weider 0.46 (snow on the hill
  behind it in the original; a scatter tree), the knoll 0.43/0.54 (before its snow and grass were said).
- **Interactive things** (`r6/pics_things6/`, round four's 118 cameras, taken before batch eight's lines): 118
  pairs, 0.604 (round five 0.598). Up: the castle's walls (`e49` 0.57 to 0.81), the Mind guild (`e28` 0.48 to 0.56),
  Kern Residence (`e54`, `e55` 0.44/0.45 to 0.50/0.54), a crate, a signpost. Down: Weider's back wall (`e59` 0.80 to
  0.71: the roof's eaves now match the original's; a scatter tree stands behind it), the rest by 0.03 or less.
  Looked at the changed ones; no fault left that the words can say beyond the gaps above.

### Scripted (round six, `output/studio_cal/mm7_7out02/scripts/`)

`measure6.sh`, `quick6.sh`, `walk6.sh`, `pics6.sh`; analysis: `herr6.py` (r6/), `blobs6.py` (height misses by
stretch), `extrema6.py`, `clifftop6.py` (loss beside each cliff line), `win6.py`, `gconf6.py`, `gwin6.py`, `wrow6.py`,
`tops6.py` and `topwin6.py` (the measure's building form, per model); edits: `grid32_6.py`, `stonehouses6.py`,
`daistrap6.py` (the refused trial), `gpad6.py` (refused); stream, knoll, roads, castle and Weider by hand-checked
edits from these printouts.

## Round five (2026-11-13, `openyamm-studio/build/oymap` of the ninth merge, 13:55)

Project before round five: `output/studio_cal/mm7_7out02/r5_backup/`. Scratch: `output/studio_cal/mm7_7out02/r5/`;
measures `cmp_start`, `cmp_start_m8` (the project as found, measured with the binary before the merge,
`output/studio_lead/oymap_before_merge9`, on a copy), `cmp_a` (goal one), `cmp_b` (end), each with `_old`
(`--without rim`), by `scripts/measure5.sh <tag> [project] [binary]`.

| Part | Start, old binary | Start | After the proof lines (a) | End (b) |
|---|---|---|---|---|
| **total** | **89.21** | **89.23** | **89.16** | **89.18** |
| total `--without rim` | 86.24 | 86.26 | 86.18 | 86.20 |
| heights | 85.99 | 86.02 | 86.04 | 86.04 |
| relief | 73.52 | 73.55 | 73.59 | 73.59 |
| cliffs | 96.73 | 96.77 | 96.77 | 96.77 |
| water | 88.65 | 88.65 | 88.65 | 88.65 |
| ground | 84.04 | 84.04 | 84.04 | 84.04 |
| roads | 92.65 | 92.65 | 92.65 | 92.65 |
| buildings | 86.84 | 86.84 | 87.60 | 87.73 |
| decorations | 95.85 | 96.02 | 96.02 | 96.02 |
| spawns | 100 | 100 | 100 | 100 |
| events | 97.44 | 97.44 | 95.00 | 95.00 |
| rim (skyline) | 90.52 | 90.55 | 90.55 | 90.55 |

**Decorations**: 95.85 to 96.02 from the merge alone (the scatter seeded by each entry's own words; same project,
old against new binary); no change of this round moved them (96.02 at start, after the proof lines and at the end).
Heights, relief, cliffs and rim moved by 0.02 to 0.04 with the binary too. **Events** fell 97.44 to 95.00 from one
cause: the fort's trap as four step plates (three events only in the rebuild, at the plates; see below), a right
form that measures lower. Buildings rose 86.84 to 87.73.

Walk (`playtest.yml`, 69 steps, 63 before): passes two runs of two on the final project, twice (`r5/walk_d_1..2.log`; again on the game binary rebuilt at 15:13 by another session, `r5/walk_e_1..2.log`); no
jump in any walk; the dais climbed on foot by its north flight (0.57 s) as in round four. New: the town hall's and the
weapon shop's doors used where the original's are, the fort's chest opened in its pit (the soldier's diary fragment,
item 1509).

### Applied: the proof lines (`output/studio_s4h/scripts/proof_h.py`, `proof3.py h`), each checked against the
original's faces (`r5/orig.json`, `scripts/texbox.py`, `scripts/model5.py`)

- **Training hall** (Training2N): the twelve-sided hall and its roof in rings as the proof says; checked: outline
  x -10928..-10032, y 11328..12096, rings 256 to 448 to 512 to 544 with insets 128 to 192, 128, 80 (the proof's
  [[144, 192], [128, 64], [80, 32]] is the mean of the first ring's insets), door Hhm2d at the north flat. Pictures
  `pics_final/diff/01-training-n.png` 0.71.
- **Skinner's hut** (Hut-a_E): the sixteen-sided ring 128 high, beehive roof [[64, 112], [256, 80]], door block;
  matches the model to the unit (x -18728..-18208 against -18216). `03-hut-e.png` 0.58 (scatter trees differ).
- **Fire guild** (FireGuild_W): the cut-corner body, the recessed porch over three bays, `floor: 384` as the proof;
  **added** the stone lantern on the roof which the proof left out (faces 17-24, 51-63: an eight-sided Hhm3ch stack
  192 by 256 from 768 to 896, a Hhm1rf cap drawn in 64 to 960, a chimney 64 by 128 to 1024; `scripts/fireguild5.py`,
  two parts, `tiers: [[64, 64]]` for the cap). `05-fireguild-w.png` 0.71, `06-fireguild-se.png` 0.74.
- **Shrine** (Shrine_, Shrine__1): open on posts with low walls (`posts: 32, sill: 128`, the way in on wall 6) as
  the proof; **added** (`scripts/shrine5.py`): eaves 16 (the roof at 7440 against the posts' 7456), the ceiling in
  7t1books1 (the cone's dark underside; the default was a light trim), the altar as its own thing (`kind: obelisk`,
  64 square drawing in to 48 at 280 under a 40 pyramid to 320, Hhp2b2, on a hidden plinth to the floor; the prayer
  runs from it, the shrine's other faces say "Shrine" as the original's event 222). Also fixed while checking: the
  shrine stood 81 east of the original (part at 337 against the original's centre 7680: now 256), 32 too high
  (`floor: 64`: posts 128 to 384, roof to 576 as the original's) and 12 too narrow (radius 230 to 242: posts' outer
  faces 224 from the middle). `08-shrine-s.png` 0.68, `09-shrine-inside.png` 0.55 to 0.71 after the ceiling.
  Not said: the lectern west of the altar (42 by 96, 12 to 38 high).
- **Obelisk 1** (obelisk 3): eight sides, 128 drawing in to 80, tip 128 to 960, plinth 416 by 32, T2BEDSHT, as the
  proof. `10-obelisk-s.png` 0.63 (the land behind differs).
- **Both signposts** (3 way signE, 3 way signE_1): post 32, arms 32 high at 192 to 224 with their own boards
  (S_West, S_South, S_East), as the proof. `12-sign1-n.png` 0.61, `15-sign2-w.png` 0.68.
- **The fort's pit, hatch, chest and trap**, decided from the original (Fort_ faces 21-38, `scripts/fort5.py`): the
  original's trap (event 236, step) **is the dais's top round the pit** (four faces at 384), the hatch (event 235,
  7trimda) lies flush in the top over a pit 128 by 64, 64 deep, with a Trim12_32 frame 8 high round it, and the
  chest (56 high) stands in the pit, its top 8 under the hatch. So: the proof's hole (moved 3 south to the
  original's y 4061..4125), the hatch in the hole flush with the top (raise 56, it lay on the top before), and the
  trap as **four step plates round the hole** inside the old 432 square, each with the trap's condition and effects
  (qbit 760: the first stepped on springs it, the others then do nothing). The studio's chest is 80 high, so the pit
  is 88 deep and the chest stands 24 under the fort's floor (`raise: -24`): its top at 376, the original's. Not the
  proof's one hole with no trap: that loses the trap. Pictures `17-fort-pit-above.png` 0.85, `18-e90-fort-chest.png`
  0.82, `19-e113-fort-hatch.png` 0.76: the hatch lies 8 under the plates where the original's frame stands 8 over
  the top, and the plates' joins show as lines on the top.
  A click on the closed hatch from the dais's north edge opens the chest under it, **in the original too**: the
  game's pick passes the hatch's face (`repro/hatch_pick/`: the original's event 117 at the same hit point,
  296.97 away). The walk asserts the chest from there.

### Applied: other wrong forms of round four (each from the original's faces)

- **Town hall** (THallaS, Thalb; `scripts/townhall5.py`): p1 had the veranda's post line for walls and TRIM3_32
  bays standing in for posts. Now the east block's walls where the original's are (x -13696..-12928, y 13542..14694),
  a veranda on posts along the front (128 deep, out to the west post line) and down the west side to the wing, its
  ceiling 7gt002a, eaves 64; the front's bays CHB1EL, CHB1ER, the double door (CHB1DL as the door, CHB1DR as a wall
  bay beside it), CHB1EL, CHB1ER; the east wall's CHBW windows. `20-townhall-s.png` 0.65: veranda, posts and double
  door as the original's; the original's upper roof is a gable with a stone end over the lower hip (not one part's
  roof), and its veranda has a post every 200 (a porch has posts at its two front corners only).
- **Weapon shop** (Weaponsmith_S; `scripts/weapon5.py`): its door stands at the back of a recess 256 deep under the
  roof, open at the south-east corner with one TRIM3_32 post; it was flush in the front wall at bay 3. Now
  `porches: [{wall: s, bays: [3, 5], depth: 256, recess: true, posts: 32}]`, the door at bay 4 (x -6536..-6408, the
  original's). Bays 3 to 6 (to the corner) are refused (see tool defects), so the corner bay is a wall where the
  original has a post. `22-weapon-s.png` 0.64.
- **Torrent's hut** (A-House_S; `scripts/hut2_5.py`): an A-frame of 7trimd planks, ridge 592 over the floor; the
  rebuild had a stone gable over plastered bays to 727. Now gable ends and walls in 7trimd, no windows, ridge 592.
  The walls stay 256 (a door needs half its height in the wall, and at 128 the door comes out squashed), where the
  original's roof comes down to 80. `23-hut2-s.png` 0.69, `24-hut2-e.png` 0.73.
- **Castle** (PC01 FrntDoor_E_1, PC07, PC08, PC10, PC11; `scripts/castle5.py`): the gatehouse's walls 256 under a
  parapet of 160 with battlements, the four corner towers' walls 592 under a parapet of 64 with battlements (they had
  a plain block to 864 and pyramid roofs). The gate's parapet in ch1b1: the castle's clean-stone load event swaps
  ch1b1 and validate refuses a swap of a texture no face has. `25-castle-gate-e.png` 0.65. Not said: the crown's
  overhang over the narrower tower shaft, the gate's parapet standing 32 out over its wall, and the low pyramid
  inside each crown; the side walls (`ruin_n`, `ruin_s`, flat at 384) stand over the original's crenellated main
  body (PC02, merlons at 848).

### Decided against, and why

- The proof's fort line as written (one hole, the trap plate taken out): the trap is the top round the pit in the
  original; four plates keep it.
- One trap plate over the whole top: it would cover the pit.
- The hamlet's stone houses with their porch on posts and stone gables, the Mind guild (round four's 73-e54, 74-e55,
  46-e27, 47-e28): not done this round (the vocabulary has the porch; the houses need their walls and roofs redrawn
  from the models as the town hall's were). Next round.
- The weapon shop's recess to the corner: refused by validate; three bays instead of four.

### Gaps (most harmful first)

1. **One event on several faces of different things**: the fort's trap is one step event on four faces; the plates
   carry four events (three only in the rebuild, events 97.44 to 95.00). The town hall's double door: the original
   runs both leaves by one event; one door bay is the house, the other leaf a wall bay. Field: `same_event_as` on a
   structure, or a door `bays: [2, 3]`.
2. **A recess open at a corner** (the weapon shop): `porches[].recess` may not reach an end wall. Field: allow the
   recess to the wall's end (its side open, a post at the corner).
3. **The fort's hatch frame** (Trim12_32, 16 wide and 8 high round the hole): a hole has no rim. Field:
   `holes[].rim: [width, height]`. And a chest of another height (the original's is 56 high).
4. **A porch with posts along it** (the town hall's veranda: posts every 200): posts stand at its front corners only.
   Field: `porches[].post_every`.
5. **A roof of two forms** (the town hall's lower hip under a gable with stone ends; Torrent's roof down to 80 over a
   door 256 high in the gable end; the fire guild's east gable end): one part's roof is one form. Fields: a gable
   end's own height for its door, `hip` per end.
6. **Crenellated crowns wider than their shaft** (the castle's towers: shaft 256, crown 320 on a corbel).
7. Still open from round four: the homes' walls say the home's name (gap 2); round two's 5, 8, 9, 10.

### Tool defects (round five)

- `oymap validate` refuses a recess reaching an end wall with "reaches 256 into the part, through it or to within 16
  of another wall: make it shallower", though the depth is not the cause (any depth fails over bays 3..6 of the
  weapon shop): the message points at the wrong field.
- A `walls` bay naming a texture without a digit (`chbw`) is refused as "no role and no texture's name"; the texture
  exists (`oymap assets chbw`). Worked round with the `window` role.
- `raise` below zero (the chest at -24) is accepted silently; it is what the pit needs, but nothing says a thing may
  stand under the land.
- The scenario's `set_pose` at z 160 inside the weapon shop's recess put the eye in the recess's ceiling (nothing
  picked, "did not pick a target"); z 0 and half a second fixed it. Worth a warning from the runner.
- The headless pick passes a closed hatch to the chest under it, in the original as in the rebuild
  (`repro/hatch_pick/`); not a studio defect.

### Pictures (round five; same camera in both maps)

- **Changed places** (`r5/pics_final/`, 26 pairs, edge agreement 0.666): best `17-fort-pit-above.png` 0.85,
  `18-e90-fort-chest.png` 0.82, `06-fireguild-se.png` 0.74, `24-hut2-e.png` 0.73; worst `21-townhall-sw.png` 0.48 (a
  scatter tree in front of the camera since the reseeding), `11-obelisk-e.png` 0.54, `02-training-ne.png` 0.57 (the
  land and trees round the obelisk and behind the hall differ).
- **Interactive things** (`r5/pics_things5/`, round four's 118 cameras, contact sheets `r5/things5_sheet_*.png`):
  118 pairs, 0.598 (round four 0.584). Up: the fire guild's door (`42-e23` 0.41 to 0.78, `43-e24` 0.50 to 0.70), the
  watch fires (`e93` 0.47 to 0.70), the signposts (`e117`, `e119`, `e118` 0.58 to 0.61 up to 0.69 to 0.74), the
  skinner's hut (`e53` 0.53 to 0.66), the training hall (`e5` 0.49 to 0.62), the obelisk (0.56 to 0.67), the shrine
  (`e85` 0.66 to 0.77), the body guild (0.46 to 0.56). Down: Torrent's door (`94-e80` 0.53 to 0.43: the camera stands
  close before the gable end, where the rebuild's walls rise upright to 256 under the A where the original's slopes
  meet the ground; gap 5), a fort stand (0.80 to 0.72) and the town hall's corner (`02-e2` 0.51 to 0.46), the rest by
  0.02 to 0.06 (scatter trees moved by the reseeding). Worst as in round four: the stable's crate (`91-e77` 0.22, the
  stable's dark inside is the original's baked lighting), the fruit trees and the tavern (scatter trees in front).
- `oymap things` on the original and the project: `r5/things_orig.txt` (101 things, 2 without a hover name: the
  gate sign and the trap), `r5/things_end.txt` (121; 5 without a hover name: the gate sign and the four trap plates).

### Scripted (round five, `output/studio_cal/mm7_7out02/scripts/`)

`measure5.sh`, `walk5.sh`, `pics5.sh`, `cams5.py` (cameras at a distance from a target), `texbox.py` (a model's faces
by texture), `model5.py`; edits: `fort5.py`, `shrine5.py`, `fireguild5.py`, `hut2_5.py`, `weapon5.py`,
`townhall5.py`, `castle5.py` (each prints what it replaces; the batch's `proof_h.py` and `proof3.py` copied into
`r5/`).

## Round four (2026-11-13, `openyamm-studio/build/oymap` of the eighth merge, 11:19)

Project before round four: `output/studio_cal/mm7_7out02/r4_backup/`. Scratch of this round:
`output/studio_cal/mm7_7out02/r4/`; measures `cmp_r4start` .. `cmp_r4c` (and `_old`, `--without rim`) by
`scripts/measure3.sh <tag>`, printed to four places by `scripts/score4.py`.

| Part | Start | End | Start (`--without rim`) | End (`--without rim`) |
|---|---|---|---|---|
| **total** | **89.16** | **89.21** | **86.21** | **86.24** |
| heights | 85.97 | 85.99 | 78.18 | 78.21 |
| relief | 73.48 | 73.52 | 68.23 | 68.27 |
| cliffs | 96.77 | 96.73 | 89.79 | 89.78 |
| water | 88.65 | 88.65 | 88.65 | 88.65 |
| ground | 83.92 | 84.04 | 83.92 | 84.04 |
| roads | 92.65 | 92.65 | 92.65 | 92.65 |
| buildings | 86.57 | 86.84 | 86.57 | 86.84 |
| decorations | 96.20 | 95.85 | 96.20 | 95.85 |
| spawns | 100 | 100 | 100 | 100 |
| events | 97.44 | 97.44 | 97.44 | 97.44 |
| rim (skyline) | 90.32 | 90.52 | (90.32, no weight) | (90.52, no weight) |

End is `cmp_r4e`. Steps between: `r4a`/`r4b` the dais, `r4c` all of batch six's lines, `r4d` the temple and the
doubled parts (no change in any part), `r4e` the watch fires' shelves.

Walk (`playtest.yml`, 63 steps): passes two runs of two, twice, on the final project (`playtest_r4_d_1..2.log`,
`playtest_r4_e_1..2.log`; also `playtest_r4_b_*`, `_c_*` before the last fixes).
The party now climbs the fort's dais on foot by its north flight (0.57 s, no jump, in every run) instead of being set
on its top. No walk here is slowed by the game's headless path planning (the dais walks take 0.7 s of game time each).

### What changed (each checked against the original's export before it went in)

- **The fort's dais, redrawn as the original's Fort__1** (not batch six's line): the original is an octagon 608
  across, flats 320 wide facing north, east, south and west, two steps of 32 (treads of 40) on the four flats only,
  and on each diagonal a low parapet (64 over the top, 34 thick, astride the edge: four Trim12_32 blocks). Round three
  drew two rings of steps all round, which batch six made climbable with `climb: 40` from every side, diagonals too.
  Now: the top an `outline` part (7gt003a walls, 7trimd top), four `stairs` (rise 64, tread 32, 320 wide; every flight
  gets the hidden slope and Untouchable risers by itself) and four `platform` parapets. The trap plate is 432 square
  (batch six said 480 or less: 480 reaches the parapets' inner faces on the diagonals). Buildings 86.65 against
  86.57 with the rings. Walked from eight sides on both maps (`scripts/daisrun4.sh`, logs `r4/walk/`): the four flats
  on foot in 0.73 s, no jump, in both; the diagonals stop at the parapet in both, and the walker's one jump got on top
  in 4 of 4 on the original and 2 of 4 on the rebuild (north-east and south-east timed out at the foot): no way up on
  foot in either.
- **The B5 fin** (`heights.ridges`): drawn from its west end with `width: 2`, batch six's line (mean difference from
  the original over the fin 156 to 90 by its measure). Rim 90.32 to 90.53.
- **The dyke's grass** (`ground[].line`, width 3 along [[93, 78], [89, 81], [89, 88], [87, 89], [82, 90]]): batch
  six's line. Ground 83.92 to 84.04.
- **Seasonal forests** (`scatter[].id`, `scripts/seasons4.py`, diff checked): every scatter entry of the forest kinds
  takes the id the original's decorations inside its area carry: `scatter:broadleaf` (id 5), `scatter:firs` (6),
  `scatter:pines` (7), `scatter:flowers` (10), none (0). Batch six's copy gave every flower the id; the two town
  beds by the west road (47 flowers) and the original's nine loose flower06 are id 0 and stay in autumn, so their
  entries have none. The original gives 89 of its 157 firs (7tree16) id 5, so in every season they show the
  broadleaf picture (summer 7tree13, autumn 7tree14, winter 7tree15); the 19 scatter entries of 7tree16 whose area
  holds both are split into two entries with the original's counts (193 broadleaf, 70 firs, 16 pines, 180 flowers
  against the original's 193, 70, 16, 175). Three load events as event 250's three branches: `evt:forest_summer`
  (spring and summer: 7tree13, 7tree16, 7tree22, flowers shown; batch six had no summer branch, so the seasonal
  singles 7tree14/15/17/18/24 would have stood in summer in their autumn and winter pictures), `evt:forest_autumn`,
  `evt:forest_winter`. The split moves where the build places the later scatter's decorations: decorations 96.20 to
  95.85 with nothing of the form changed (the regions' decoration scores move up and down all over the map), kept.
- **The east gate's arch and sign** (batch six's lines): the timber arch as a bridge without piers (448 at the pillars
  to 608 at its crown) and the board hung under it (`hang`, `blank`: event 1, no title, no handler; MM7's own
  7hhr1bwall for the original's Hhr1bWALL, which MM7 lacks). The measure leaves a blank event out on both sides.

- **Found in the pictures of the interactive things, fixed** (each against the original's faces):
  - the temple's spire tower was drawn three times over itself (p4 = p5 = p6, p7 = p8 = p9: faces in one plane) and
    stood 768 high under a top that began at 896, so the top floated over a gap; the original's Temple3_N is closed
    to 896 and opens into a belfry of four corner pillars (48 square, 896 to 1112) under a closed storey to 1232. Now
    one tower to 896, four pillar parts, the storey from 1112 (`r4/sketch_before_temple.yml` before);
  - the weapon shop and the spirit guild each had their first part twice (identical parts p1 and p2); the second
    removed (`r4/sketch_before_dups.yml` before). A scan of both projects found these and three in Ravenshore;
  - the west and north watch fires' rings stood on a plinth and half in a slope: the original levels four nodes for
    each (2080 over the gorge, 800 at the rim's foot). Height points on the nodes the grid missed; the north shelf's
    fourth node is a vertex of the east rim's cliff line and stays 672 (a point there moved the next node instead).

### Decided against, and why

- `climb: 40` on two rings (batch six's line): the original has steps on four flats and parapets on the diagonals;
  the rings would let the party walk up where the original's cannot. Replaced by the original's form (above).
- The trap at 480 square: it would cut into the parapets; 432.
- Flowers of the town beds under `scatter:flowers`: the original keeps them in every season (id 0).

### Gaps (most harmful first)

1. **The hatch and the chest in its pit**: in the original the chest (event 117, chest 6) sits in a pit 64 deep
   under the hatch (event 235 makes the hatch invisible) at the dais's middle, and the trap's floor (event 236) is the
   dais's top round the pit. The rebuild's chest stands on top of the dais (a box 80 high, visible from everywhere,
   pictures `r4/pics_changes/diff/01..09`) and the trap is a plate 8 high on the top. A part has no holes, and one
   step event cannot lie on several platforms. Fields: a part's `holes` (or a `pit` structure), a chest `raise` below
   a part's top, and `same_event_as` on platforms.
2. **Homes' walls say the home's name**: the original's homes say "House" on their walls (event 265, one event on
   every home) and the residence's name only on the door; the rebuild's plot `title` puts the name on every wall
   (three of these are the measure's three events only in the rebuild: Temper Residence, Withersmythe's Home, and the
   castle's title). Field: a plot `hint` for its walls beside the door's `title` (or a plot with `door: none` and its
   door in `doors`, not tried: it renumbers events the walk uses).
3. Still open from round three: the steps' slope (closed this round), thin ground strips (closed), seasonal scatter
   (closed), the gate sign (closed); round two's 5, 8, 9, 10 stand.

### Tool defects (round four)

- **`oymap things` refuses outdoor maps**, the original and a project alike ("7out02.odm is not an indoor map"):
  `output/studio_cal/mm7_7out02/repro/things_outdoor/run.sh`. The interactive things were pictured with this round's
  own list instead (`scripts/things4.py`: faces grouped by event from the build's export, decorations with events
  from its scene, one camera each in front of the largest upright face).
- **A part with `outline` but no `shape: outline` is built as a box of the whole plot, and validate is silent**:
  `output/studio_cal/mm7_7out02/repro/outline_without_shape/run.sh` (the dais came out 1024 square).
- **`oymap assets --world mm7` lists textures MM7 lacks** (`trim9_32a`, only in worlds/mm8), which validate then
  refuses: `output/studio_cal/mm7_7out02/repro/assets_other_world/run.sh`. MM7's own is `7trim9_32a`.
- **Scatter placement depends on the entries before it**: splitting one entry into two (same area, same total count)
  re-places decorations all over the map and moves the decorations part by 0.35 with no change of form.
- Game, not studio: the party stands on a hidden slope's plane past its top edge (z 414.6 at 37 in from the dais's
  north edge, 30 over the top), on the original exactly as on the rebuild (`r4/probe/o2.log`, `p2.log`); the walk's
  band allows it.

### Pictures (round four; same camera in both maps, `calibration/outdoor_ingame.py`)

Folders under `output/studio_cal/mm7_7out02/r4/`; contact sheets of the interactive things, least alike first:
`things_sheet_01.png` .. `_15.png` (`scripts/sheet4.py`). All looked at.

- **Places changed** (`pics_changes/`, 15 pairs, edge agreement 0.739): the dais from all eight sides and from above
  0.74 to 0.81 (`diff/09-dais-top-from-north.png` 0.81, `04-dais-from-south-east.png` 0.78); flights on the flats,
  parapets on the diagonals and the octagon as the original's. Batch six's rings from the north
  (`output/studio_s4g/pics/dais_after/diff/01-dais-from-north.png`, 0.72) against `diff/01-dais-from-north.png` (0.76).
  What still differs there: the chest box on top where the original shows the hatch's frame (gap 1); the stair treads'
  texture reads lighter. Gate from the east 0.76 (arch and board as the original's; the posts smoother), from the
  west 0.64 (the hill beside the road is bare dirt and larger in the rebuild: not this round's). Dyke 0.74; the B5 fin
  0.70; a forest of the seasonal ids 0.55 (a scatter tree in front of the camera; both show broadleaf trees in summer).
- **Interactive things** (`pics_things/`, 118 pairs, one per event, 0.584): best the hamlet's plaster houses
  (`diff/76-e57-hamlet-houses-2.png` 0.87, `78-e59` 0.81), the fort's trap and chest (0.82, 0.83), wells (0.79).
  Worst, what the player sees that differs (none of it this round's work; for the next):
  - the stable's crates (`diff/91-e77-chest-4.png` 0.23, `110-e107-wagon-crate-2.png` 0.39): the original's stable
    is dark inside, the rebuild's lit as outside (face shading the measure does not see);
  - houses of the wrong kind: the hamlet's stone houses with a porch on posts and stone gables
    (`73-e54`, `74-e55`, guild of Mind `46-e27`, `47-e28`, 0.45) are plaster-and-timber boxes with hip roofs; the
    training hall and the magic shop (`05-e5`, `06-e6`, `09-e9`) are round with thatched cones in the original, boxes
    with slate in the rebuild; the hermits' huts (`72-e53`, `71-e52`) round beehives in the original, square stone
    huts here, `94-e80` an A-frame drawn as a gable; the two shrines (`112-e111`, `99-e85`) open wooden pavilions in
    the original, closed towers here; the obelisk (`89-e70`) slender and white in the original, a wide stone shaft here;
  - doors in a porch: the fire guild (`42-e23`), the weapon shop (`33-e14`, `32-e13`) and the town hall (`01-e1`)
    have their door recessed under an open porch in the original, flush in the rebuild (gap: arcade/open bays);
  - the signposts (`115-e114` .. `118-e117`): a small post with arms in the original, a wide low box in the rebuild;
  - the castle's gate (`67-e48`) and court (`68-e49`): crenellated in the original, plain walls here.
- **Fixed after looking** (`pics_fix/`, same cameras): the temple's spire now has the original's belfry
  (`diff/02-e4-temple.png`, `11-temple-spire-from-north.png` 0.66: the top no longer floats); the west watch fire's
  ring no longer stands on a plinth over the gorge (`08-e84-fire-ring-west.png` 0.64 to 0.76, `10-e93` 0.47 to 0.70);
  the north one lies on its shelf (`07-e82` 0.65 to 0.69); the weapon shop and spirit guild unchanged to the eye.

### Scripted (round four, `output/studio_cal/mm7_7out02/scripts/`)

`seasons4.py` (scatter ids by the original's decorations inside each entry's area; its printout in
`r4/seasons4.out`), `daiswalk4.py` and `daisrun4.sh` (the dais from eight sides, either map), `walk4.sh`,
`things4.py` (interactive things' cameras), `score4.py`.

## Round three (2026-11-13, `openyamm-studio/build/oymap`)

Project before round three: `output/studio_cal/mm7_7out02/r3_backup/`. Measures `cmp_r3start` .. `cmp_final3` (and
`_old`, the judging before the morning of 2026-11-13: `--without rim`), by `scripts/measure3.sh <tag>`.

| Part | Start (new) | End (new) | Start (old) | End (old) |
|---|---|---|---|---|
| total | 87.75 | 88.84 | 85.49 | 86.21 |
| heights | 85.2 | 86.0 | 77.3 | 78.2 |
| relief | 72.3 | 73.5 | 67.0 | 68.2 |
| cliffs | 92.2 | 96.8 | 87.6 | 89.8 |
| water | 88.6 | 88.6 | 88.6 | 88.6 |
| ground | 83.9 | 83.9 | 83.9 | 83.9 |
| roads | 91.2 | 92.6 | 91.2 | 92.6 |
| buildings | 86.5 | 86.6 | 86.5 | 86.6 |
| decorations | 96.0 | 96.2 | 96.0 | 96.2 |
| spawns | 100 | 100 | 100 | 100 |
| events | 95.7 | 97.4 | 95.7 | 97.4 |
| rim (skyline) | 82.0 | 86.3 | (82.0, no weight) | (86.3) |

Walk (`playtest.yml`, now 59 steps): passes three runs of three (`playtest_r3_e_1..3.log`), no jump anywhere.

### What changed

- **From the code agent's copies** (`output/studio_s4f/item2_h`, `item4_h`, `item5_h`): both bridges as arches
  (ravine bridge `height 640, rise 176, kerb 112`; footbridge `height 544, rise 96, kerb 352`), the wells' refills as
  calendar timers (`weekly`; `daily, hour: 1`), the four `heights.ridges`. Total 87.75 -> 88.06.
- **Ridges** (`heights.ridges`, read off the original's heights with `scripts/ridgefind.py`, which lists one-node
  ridges the build misses): the north ridge carried on to the hill (to [90, 42]), the south spur followed down to the
  hill above the lake (to [70, 75]), and three more: F3's short ridge, F6's 640 dyke along the lake's south side, the
  narrow crest at the white massif's foot over the footbridge's east end. Cliffs 95.9 -> 96.8.
- **The rim**: 13 rim peaks of the original as height points (`scripts/rimpeaks.py`: highest in 7 x 7 and 256 over
  the mean, that the grid misses by 256+), the west rim's crest as a ridge. Rim 82.0 -> 85.3.
- **The west gorge** (A5/B5): its walls redrawn as cliff lines on the original's top nodes (north and east wall,
  south and west wall, the trench west of it, each its own drop), the rock fin between its two arms as a ridge (the
  grid samples the gorge floor on both sides of it), one point on the west wall, and the west road on the original's
  cells (its diagonal steps on the east side, as the original's; its branch north at x 10). Roads 91.2 -> 92.6,
  rim 85.3 -> 86.3.
- **Events**: the three wells' stone says `hint: Well` (the original's 217 on every face but the water); the world's
  dimensional travel pedestal and orb (`7out02_dimensional_travel.scene.yml`, event 1777: the measure reads the
  original with this overlay, and the rebuild lacked it) as two decorations running `evt.OpenDimensionDoor()`; the
  fruit trees bare (7tree30) in autumn and winter by a load event (`evt:fruit_trees_bare`, the original's 250 for
  ids 51-58). Events 95.7 -> 97.4.
- **The fort's dais** (Fort__1): two steps of 32 to a top 64 over the fort's floor, as the original's (one block
  128 high before); the chest, trap floor and hatch lowered with it.
- **The walk**: step 34's chance (below) removed; the west gorge walked down to where the game offers the way to
  Erathia (declined); the pedestal's event run by its number (dimension door pending).

### The rim: kept the grid, added peaks

The grid of spot heights beyond the square is the step-4 grid every height here is said with (allowed: at most
32 x 32), not a trace. The code agent's described rim (`frame.rim`, ridge forms per side from the original's
statistics) scored the rim part 54 against the grid's 82, and its pictures show why: the described ridge puts a cone
where the original's west skyline is a long snow-capped shoulder (`output/studio_s4f/pics/rim_orig_h/diff/07-rim-w.png`
against `rim_desc_h/diff/07-rim-w.png`, edge agreement 0.42 against 0.34). The grid holds the original's skyline; what
it missed were the single high mounds between its samples, so those were added as peaks (what height points are
for), and the west rim's crest edge as a ridge. No `frame.rim` entry.

### The walk's step 34

In the code agent's failing run the party stood at (8192, 4518), against the north face of the fort's dais, and the
walker's jumps did not get it up the 128 block; on the rerun one jump did. In this engine the party does not walk up
the dais at all: with the original's form (two steps of 32) it still stops at the first riser and gets on only by a
jump. On the original map it walks straight up (`repro/fort_step/orig_walk.log`: 0.8 s, no jump), because the
original's Fort__1 carries an invisible sloped face over each flight of steps (7trimd, attributes 0x3108, normal
(0, 40940, 51175)), which the build does not draw. The walk now puts the party on the dais's top at its north edge
(off the trap's floor, asserted) and walks it onto the trap: 0.33 s, no jump, in all three runs.

### Gaps (round three; most harmful first)

1. **Steps without a walking ramp**: the build draws a stepped part (a dais's two 32 steps, `stairs` without
   `ramp`) without the invisible slope the original's models have over their steps; the engine's party then does not
   climb them (fort dais, F4). Field: the build adding the hidden ramp face to steps (or `steps: {ramp: hidden}`).
2. **Thin ground strips**: the original paints grass along one-cell ridges and dykes (the 640 dyke on the lake's
   east side, x 89, y 81-88; the strips round G5's shelf); a ground polygon cannot be one cell wide under the build's
   half-open test. Field: `ground[].line` with a width. Ground stays 83.9.
3. **Seasonal scatter**: load event 250 changes the pictures of all the forest trees (ids 5, 6, 7: about 200 trees)
   and hides the flowers (id 10) in autumn and winter; scatter has no id to address. Field: `scatter[].id` (an event
   variable) addressable by `set_sprite`/`hide`. Only the fruit trees (single decorations) are said.
4. **The gate sign** (event 1, nameless, no handler; TS_E: a board 192 x 80 hung at 512-592 under the timber arch
   over the east road): a sign is a post with a board, nothing hangs one from an arch, and a nameless do-nothing
   event has no word. Field: `sign.hang` (a board on a beam) and an event with no title.
5. **A model of several pieces**: the original's fort ring (Fortc_) is one model of four pieces; the rebuild's four
   walls pair one of them with it (footprint 0.19) and leave the rest unpaired; likewise the castle's 16 PC models
   against one plot. (Measure side; see tool defects.)
6. Round two's gaps 1 (now: the rim kept as the grid, see above), 2 (ridges: now said), 4 (calendar timers: now
   said), 6 (well hints: now said), 7 (arches: now said) are closed; 3 (cliff lines one node off) is closed in the
   gorge only; 5, 8, 9, 10 stand.

### Tool defects (round three)

- **Headless walk hangs** on a dais of one 64 riser: `output/studio_cal/mm7_7out02/repro/fort_step/run.sh
  output/studio_cal/mm7_7out02/repro/fort_step/one64_project one64` (the project with the dais as one round part 64
  high): the game sat at 100 % CPU in `walk_to` for over 3 minutes without a single WALK line (killed). With two 32
  steps the same scenario ends in 5 s (`walk_two32.log`).
- **No sprites in a headless run**: decorations cannot be clicked by `press_interact` (`ped06`, `dec57` load
  "failed size=0x0", `INTERACT failed has_hit=false`): the pedestal is tested by `execute_event`.
- `oymap compare` pairs models one to one: a model of disjoint pieces (Fortc_, the fort ring) is paired with one of
  the rebuild's pieces and the others count as only in the rebuild. Repro: `cmp_final3/differences.json`,
  `buildings`, Fortc_ overlap 0.186 and `thing:fort_ring_*` only in the rebuild.
- `heights.ridges` with `width: 2` on a diagonal raised floor nodes beside the line ([14, 79], [18, 78]) instead of
  the second node across the crest; kept width 1.
- A road's `bed` must have one height per point: changing a line by text needs the bed changed too (validate says
  so; not a defect, a trap).

### Where score and the original's form pulled apart

- The bridges' arches measure the same as the level decks (buildings 86.5 either way): kept the arches.
- Channels (ridges at height 0) for the gorge measured lower than the cliff lines (total 88.4 against 88.5) and
  widened it: not kept; cliff lines on the original's top nodes kept.
- Nothing else measured against its form this round.

### Pictures (round three)

`output/studio_cal/mm7_7out02/ingame_town_r3/` and `ingame_worst_r3/` (`scripts/pictures3.sh r3 final3`).
Town: edge agreement 0.699 (round two 0.701; the same within noise). The measure's 12 worst regions and 6 rim
views: 0.582 (these are other places than round two's, which were all on the rim). Best: `town_r3/diff/02-town-from-east.png`
(0.78), `town_r3/diff/01-town-from-south.png` (0.75), `worst_r3/diff/04-region-F7.png` (0.73: the white massif and the
road ledge). Worst: `worst_r3/diff/09-region-F3.png` (0.38: the original's grass-topped stepped ridge north-east of
the fort and the grassy flanks of the two hills behind it; the rebuild shows the hills' flanks as bare cliff faces and
the ridge as dirt), `worst_r3/diff/12-region-G4.png` (0.46) and `14-rim-C1.png` (0.46). In
`07-region-B5.png` the gorge now has the original's walls and road (0.47; a scatter tree in front of the camera).

### Scripted (round three, `output/studio_cal/mm7_7out02/scripts/`)

`measure3.sh` (both judgings), `walk3.sh` (build, install, walk N times), `pictures3.sh`, `ridgefind.py`,
`rimpeaks.py`; the ridges, peaks, gorge lines and events were written from their printouts by hand-checked edits.

### Unsure

- `thing:wagons` (kind `model` from 7out02.odm's Wagon_W models) was in the project before this round; it takes the
  original's own models, which the rules' "never its model's vertices" may forbid. Left as found.
- Event 1777 belongs to the world's overlay scene, not to the original 7out02.odm; the measure counts it, and a
  rebuild that replaced the map would lose the pedestal without it, so it is drawn.

## Round two

Round two of the outdoor rebuild loop, 2026-11-13, with `output/studio_lead/oymap_outdoor3`. Project as it stood
before round two: `output/studio_cal/mm7_7out02/r2_backup/` (round one's: `r1_backup/`). Scratch, scripts, measures
and pictures: `output/studio_cal/mm7_7out02/` (round two's measures are `cmp_r2start` .. `cmp_tv2`, the final).

## Scores (`oymap compare 7out02.odm --world mm7 --with <project>`)

| Part | Round 1 start | Round 2 start | Round 2 end |
|---|---|---|---|
| total | 68.7 | 83.8 | 85.5 |
| heights | 75.4 | 76.8 | 77.3 |
| relief | 64.3 | 66.5 | 67.0 |
| cliffs | 72.8 | 87.6 | 87.6 |
| water | 43.8 | 88.0 | 88.6 |
| ground | 55.5 | 79.2 | 83.9 |
| roads | 91.2 | 91.2 | 91.2 |
| buildings | 60.0 | 81.4 | 86.2 |
| decorations | 99.3 (old measure) | 94.5 | 96.0 |
| spawns | 75.5 | 100 | 100 |
| events | 63.4 | 95.7 | 95.7 |

All twelve worst regions (F1, C1, H4, H1, G8, H6, A2, A3, F8, H8, H2, H3) lie wholly outside the playable square
(the backdrop rim). Height error inside the square: mean 87 (95 at the start of round two), 90.5 % of nodes within
256; outside: mean 191, 74.7 % within 256.

Walk (`playtest.yml`, 49 steps): passes three times in a row (`playtest_r2_final1..3.log`).

## What changed in round two

- **Cliff sides.** Seven cliff lines had segments whose low side was the other side (one `down` for a line that ran
  round the lake and then along the foot of the white massif): the build dug a trench at the massif's foot (F7: the
  rebuild lay 258 low on average inside the square). Each line is now split where its low side flips, each piece with
  its own drop (`scripts/cliffsides.py`, gaps joined by `fixgaps.py`). Heights 76.8 -> 77.3, water 88.0 -> 88.7.
- **Ground.** The outlines ran through the grass's edge nodes, and the build's half-open inside test drops about
  half of those: every region had more dirt than the original (1267 grass corners lost against 138 gained). Each
  region's outline is now chosen among drawings through the edge nodes, one node outside, or one node outside on the
  east and south only, by the corners the build's test keeps (`scripts/ground2.py`, tolerance 1.0/1.5, 580 points).
  Ground 79.2 -> 83.9.
- **Town decorations.** The four town regions' scatter boxes (C3, D3, C4, D4) are replaced by the original's clumps
  there (joined within 2 cells; a box round each clump, a one-cell circle round a lone tree; `scripts/towndeco.py`):
  the flower beds by the west road, the street trees. Elsewhere the regional scatter stays. Decorations 94.5 -> 96.0.
- **Buildings, by their tops** (`scripts/tops.py` reads the tops as the measure does; `topview.py` prints them):
  - castle: curtain and rear walls 384 high and 128 thick (were 656 and 320), the court 256, the gate block only
    along the front, two short east walls, the middle upgrade tower 704 with a 64 parapet (`castle.py`);
  - stable: the roof's ridge east-west (it ran north-south): form 0.48 -> 0.84;
  - the Arbiter's base: the original's eight-pointed star of narrow arms (an eight-sided middle and eight outline
    arms, `arbiter.py`) instead of two squares: form 0.70 -> 0.91;
  - the ravine bridge over the south road: a bridge structure (deck 768, kerbs to 928) instead of a box plot;
  - water guild: the fountain court's rims 80 high (were 256 with a 208 parapet);
  - town hall walls 320 and roofs 256; temple spire moved to the front of the nave, the lean-to behind it removed;
  - porch roofs on the long house and the double house (`porches.py`); the tavern's lower back range;
  - the White Cliff cave door: `depth` 448 on the mound, moved onto it.
  Buildings 81.4 -> 86.2.
- **Actors.** Group 60 (the lockdown squad, 15, hidden), group 71 (the raiders, 75, hidden, as six camps with count
  and spread) and group 85 (one, hidden, nothing shows it in the original either) from the original's scene
  (`actors2.py`).
- **Events** (`events2.py`): the castle door opens once the castle is the party's or the butler has met them, else
  the world's `MM7.EnterCastleHarmondaleOutdoor()` (locked before the scavenger hunt, then the butler); the Arbiter's
  door opens his house until there is a verdict, then the original's branches (new Arbiter, film, history page) in
  `else_effects`, and drops the judges as followers; load events: the intro film (519, 648), the MMerge region state
  (`MM7.UpdateHarmondaleInvasion`, `MM7.UpdateJudgeGreyDeath`), the lockdown (695: squad shown, bank emptied, 693/694
  cleared), the raiders (774: group 71 shown); timers: the squad beaten (every 15, `kills` group 60), the wells'
  refresh (gold weekly, Might daily, as play-time timers).
- **Walk.** Extended: Tempered Steel's door refuses while qbit 695 is set and opens once it is cleared; stepping onto
  the fort's floor springs the trap once (qbit 760).
- **atmosphere.yml**: `weather` left out, so the install writes this map's bolster row as map 63's (checked in the
  mount: row 9702 `x - x`). Pictures now show the same sky (7plansky3) on both sides.

## Scripted (`output/studio_cal/mm7_7out02/scripts/`, each read-only on the original's export or scene)

`measure2.sh` (the loop with the round-two binary), `cliffsides.py` (+ `fixgaps.py`, `setcliffs.py`), `ground2.py`,
`towndeco.py`, `castle.py`, `arbiter.py`, `porches.py`, `actors2.py`, `events2.py`, `pictures2.sh`; analysis:
`herr2.py`, `herr3.py`, `blobs.py`, `dump.py` (heights), `gdiff.py` (ground corners), `decopair.py` (the measure's
decoration pairing), `decomap.py`, `tops.py`, `topview.py`.

## Gaps (most harmful first)

1. **The rugged rim** (all twelve worst regions; half the nodes, 46 % of their nodes within 256 in the outer rows):
   not traced, as asked. Field: `frame.rim` (edge height, roughness) or a finer grid outside the playable square.
2. **One-node ridges and ledges inside the square** (E4: 39 steep cells in the original, 0 in the rebuild; the
   winding 640 ridges at x 66-74, y 56-60 and x 87-101, y 58-65; the 640 channel between the hill and the massif at
   x 84-104, y 100-103): a step-4 grid and points cannot hold a feature one node wide; 21 more peak points measured
   nothing (86 -> 86 mean error) and broke band ranges, so they were not kept. Field: `heights.ridges[]` (line,
   height, width) or a cliff pair with a shared top.
3. **Cliff lines one node off** after simplification (0.75 cells): most of the remaining inside error sits beside
   the lines. Kept: a finer simplification is a trace.
4. **Calendar timers**: the wells refresh weekly and daily (at one at night) in the original; a timer counts play in
   the map. Field: `events[].trigger: daily|weekly` with an hour.
5. **Seasonal trees** (load event 250: three trees and the eight fruit trees change picture by season and by the
   apples picked): not said. `set_sprite` with `season` conditions could say most of it in four load events; not
   done this round.
6. **A well's second event** (wells carry 217, a title-only hint, beside their drink event): two of the five
   unpaired events (C2, C5). `structures[].hint` may say it; not tried.
7. **The footbridge's arch** (deck 544 at the ends to 640 in the middle, railings to 992): a bridge deck is level
   and a kerb at most 256. Field: `bridge.arch` (rise) and a kerb up to 512.
8. **The gate sign** (event 1, no handler; D3) still has no words.
9. **Group 56 made hostile unless the path of Light** (load event 249): no actors of that group on this map; left out.
10. **Event 51's monsters killed check** and 50's lockdown run every load in the original; ours runs the lockdown
    on load and the kill check on a 15-step timer with `once`.

## Tool defects

- `oymap compare` places a model by its stored bounding centre, not its vertices: the original's six Wagon_W pieces
  (and one Temple3_N) are listed "only in the original" at [64, 74] (Wagon_W_5's stored centre is garbage:
  bounding_center [0, -5187, 11153]); the wagons in the stable yard at [53.4-54.4, 42] pair with nothing. Repro:
  `oymap compare 7out02.odm --world mm7 --with devdocs/map_studio/briefs/mm7_7out02/L4 --assets assets_dev --out x`
  and `x/differences.json` `buildings`, state `only in the original`, names Wagon_W*.
- `oymap compare` reads an upright face's foot at the face's highest point: the footbridge NewOut2Bridge_ reads 992
  over the whole ravine (its arch faces), so a level deck at the true height (640) scores worse (see below).
- The picture script's background job exits 1 when both runs succeed (its last `tail` of two logs); harmless.
- `outdoor_ingame.py` defaults to `openyamm-studio/build/oymap`: with the round-two binary pass `--oymap`.

## Where score and the original's form pulled apart

- Footbridge: deck 960 with a 32 kerb measured buildings 83.1, the true form (deck 640, kerb 256, the most a kerb
  may be) 82.6. Kept the true form.
- Tavern: deepening the hall to the original's model depth measured 86.1 against 86.2; the original is a hall and a
  lower back range, so that is what was drawn (86.2).
- Ground at tolerance 0.7 measured 85.3 against 83.9 for 1.0/1.5 (757 points against 580): kept the coarser.
- 21 peak points inside the square: no change in the measure, refused by validate (band ranges): not kept.

## Unsure in the original

- What the original's castle wall tops really are: the measure reads the curtain walls at 384, though PC09 reaches
  656 (ruined, stepped walls); drawn at 384.
- Event 236 (the fort's trap) is taken as a step trigger on the fort's centre floor, as in round one.

## Pictures

Town (`output/studio_cal/mm7_7out02/ingame_town_r2a/diff/`, edge agreement 0.701, round one 0.61; both maps under
7plansky3): best `02-town-from-east.png` (0.78), `01-town-from-south.png` (0.75), `06-fort-from-south.png` (0.69).
Worst regions (`ingame_worst_r2a/diff/`, 0.61): `10-region-H8.png` (0.33: the south-east corner's map edge and a
dark cliff-face strip on the rim slope) and `01-region-F1.png` (0.49: a scatter tree in front of the camera, the rim
hill's crest). In `03-main-street-east.png` the alchemist's lowest tier stands a little nearer the camera than the
original's.

## Cleanup: z-fighting and town feel (2026-11-14, `openyamm-studio/build/oymap` of the fourteenth merge)

Backup before: `output/studio_cal/mm7_7out02/cleanup_backup/`. Scripts: `output/studio_cal/mm7_7out02/cleanup/edit_h.py`,
`edit_h_tf.py`, `edit_h_tf2.py`, `edit_h_terraces.py` (`edit_h_terraces2.py` tried and reverted); helpers
`groups_tf.py`, `flat_tf.py`. The group-60 change was a `sed` on sketch.yml (`hostile: true` dropped on 15 lines).

**Faces in one plane: 7 to 6** (the original 65; 231 was an earlier count, this binary gave 7 at the start). Changed:
the shrine's altar stands on the step without a plinth (Shrine_ faces 42-49: shaft 128..280, tip to 320); the buried
plinth's top lay in the step's top. Left, with why: town hall p1/p2 (4): each part's 64 eave runs into the other at
the corners where they join; the original's roof is continuous and the studio has no per-wall eaves. fort_chest and
fort_hatch (2): the hatch platform's 64 skirt runs down the pit beside the chest; under the closed hatch, and the hatch
is hidden once open, so they are never seen.

**Town feel** (rebuild against `7out02.odm`):
- Monster groups in town 10 to 6 (original 6): the lockdown squad (group 60) was authored `hostile: true`; the original's
  are hidden only and turned hostile by `SetMonGroupBit(60, Hostile)` in the invasion event (MM7.UpdateHarmondaleInvasion).
- Wells and fountains 9 to 6 (original 6): the terrace and hamlet wells' frames said "Well" (only the market well's does
  in the original), and the residences' walls said their own names (Farswell); the original's residence walls say
  "House" (event 265), huts "Hut" (266). The 14 residences now have their name and house on the door only (`doors`), the
  walls "House"/"Hut". Events part 98.3 to 98.2 (114 of 114 events, 112 paired).
- Flat share in town 0.58 to 0.70 (original 0.78, range from 0.73): six terraces as level ridges at the original's
  plateaus (640, 640, 288, 480, 640, 0). Still under: the rest are the 4-cell grid's ramps between terraces and a shelf
  at 224 beside the temple that a ridge does not change (applied after ridges); a word for a level terrace area is missing.
- Still outside: wild group to nearest dungeon entrance 24581 to 24502 (the shipped top 23867 is this original's own):
  spawn places are the build's inside their areas.

**Score** 90.23 to 90.23 % (relief 74.2 to 74.4, cliffs 97.0 to 96.6, buildings 89.7 to 89.8). **Walk** two of two.
**Installed** in `rebuilds_root` with terrain materials; desktop load check impossible (no display). **Pictures**:
`output/studio_cal/mm7_7out02/cu_pics/before.png`, `after.png` (`oymap render`).

## Roof words (2026-11-14, `openyamm-studio/build/oymap` of the nineteenth merge)

Backup `output/studio_cal/mm7_7out02/roofwords_backup/`; edits by `output/studio_cal/mm8_out02/roofwords/edit.py tavern`
and by hand.
- The tavern's upper storey: the wing and the hall as one outline under one gable roof (the hall's gable runs into
  the wing's to its ridge). Gate: height difference 8.8 to 2.6.
- The town hall (eaves on chosen walls): p1 `eaves_walls: [s, e, n, {wall: w, from: 576}]` (its west wall's eaves
  only where it stands free of the wing, 64 past the inner corner, which the wing's south eaves cover), p2 `[s, n, w]`.
  Whole walls (`[s, e, n]` on p1, as batch O-D's copy) took the free 640 of p1's west eaves away and cost 0.04 in
  buildings; the stretch keeps them.
- Not done: the other "roofs that join" (the town houses' bumps, the double houses' middles, Otto's hips into its flat
  middle): each needs its building redrawn from the original's faces first.

**Score** 90.23 to 90.23 % (buildings 89.81 to 89.82; other parts unchanged). **Pairs** 6 to 2 (the town hall's 4
gone). **Walk** two of two (69 steps). Installed in `rebuilds_root` with terrain materials. **Pictures** to take: the
tavern's roof, the town hall's inner corner, beside the original.
