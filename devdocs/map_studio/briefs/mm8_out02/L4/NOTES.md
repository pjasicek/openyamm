# Ravenshore (mm8 out02.odm), outdoor rebuild

Scratch: `output/studio_cal/mm8_out02/`. Round two used `output/studio_lead/oymap_outdoor3` for every oymap command
(`scripts/measure2.sh`, `scripts/walk2.sh`, `scripts/pictures2.sh`); the project as round two found it is in
`r2_backup/`, its measures in `r2cNN/` (start `r2c0`, end `r2c10`), pictures in `r2_town0/` (start) and
`r2p1_town/`, `r2p1_worst/` (end).

## Round five (2026-11-13, `openyamm-studio/build/oymap` of the ninth merge, 13:55)

Project before round five: `output/studio_cal/mm8_out02/r5_backup/`. Scratch: `output/studio_cal/mm8_out02/r5/`;
measures `cmp_start`, `cmp_start_m8` (the project as found, measured with `output/studio_lead/oymap_before_merge9`
on a copy), `cmp_a` (goal one), `cmp_b` (end), each with `_old` (`--without rim`), by `scripts/measure5.sh`.

| Part | Start, old binary | Start | After the proof lines (a) | End (b) |
|---|---|---|---|---|
| **total** | **92.20** | **92.22** | **92.22** | **92.18** |
| total `--without rim` | 91.52 | 91.54 | 91.54 | 91.50 |
| heights | 88.22 | 88.22 | 88.22 | 88.22 |
| relief | 76.87 | 76.87 | 76.87 | 76.87 |
| cliffs | 96.81 | 96.81 | 96.81 | 96.81 |
| water | 96.54 | 96.54 | 96.54 | 96.54 |
| ground | 91.67 | 91.67 | 91.67 | 91.67 |
| roads | 93.03 | 93.03 | 93.03 | 93.03 |
| buildings | 90.29 | 90.29 | 90.32 | 90.36 |
| decorations | 99.63 | 99.81 | 99.81 | 99.81 |
| spawns | 98.31 | 98.31 | 98.31 | 98.31 |
| events | 99.39 | 99.39 | 99.39 | 98.79 |
| rim (skyline) | 88.17 | 88.17 | 88.17 | 88.17 |

**Decorations**: 99.63 to 99.81 from the merge alone (scatter seeded by each entry's own words; same project, old
against new binary); nothing of this round moved them. **Events** 99.39 to 98.79 from one cause: Caori's Curios'
sign on its post is a thing of its own with the shop's name (one event only in the rebuild; the original's sign
faces carry the shop's name event 196). Buildings 90.29 to 90.36.

Walk (`playtest.yml`, 136 steps): passes two runs of two on the final project, twice (`r5/walk_b_1..2.log`; again on the game binary rebuilt at 15:13 by another session, `r5/walk_e_1..2.log`), eleven walks
without a jump; the council hall's door now used at the original's bay (pose x 12800 to 12928).

### Applied: the proof lines (`output/studio_s4h/scripts/proof_r.py`, `proof3.py r`), checked against the faces

- **Council hall's canopy** (02sw_corner_ 57, 60): a porch without posts over bays 1 and 2 of the upper hall's south
  wall, 128 out, t14abcd11 under it. While checking, **the door moved to the original's bay** (`scripts/council5.py`):
  the wall is t14c07, the window t14c12c, the door t14c03 (x 12864..12992), t14c01, t14c06; round four had the door
  at bay 1 (the window's place), so the canopy hung over the window and half the door. `04-e106-council-hall.png`
  0.85, `08-council-canopy-wide.png` 0.79.
- **The terrace's railing** before Needful Things (02nw_corner_ 32-60): t14abcd10 posts, a t14abcd11 rail 192 to
  208, as the proof. `07-needful-from-street.png` 0.76.
- **sgMAGIC on Needful Things' wall**, 320 to 384 over the third bay, as the proof.
- **Both wells** (well1N, well1W): ring 256 across, 80 high, post to 216, no roof, as the proof; **the form is still
  not the original's**: the original's well has two tapered T1cabs uprights on the ring's rim at its north and south
  ends (64 by 24 at the foot to 24 by 24 at 184) and a beam 24 by 32 across them at 184 to 216, a windlass frame; the
  proof's `post` is one square post in the water's middle. From the west the two read alike
  (`pics_final/diff/01-well2-w.png` 0.77), from the east and north the frame differs (`27-well1-e.png` 0.71). Kept
  (nearer than round four's roofed well); gap 1.

### Applied: other wrong forms of round four

- **Shop signs on walls** (`scripts/signs5.py`, which finds the part, wall and bay under each of the original's sg*
  faces): sgtrain (Gymnasium), sgtvrn (Kessel's Kantina), sgweap (Keen Edge), sgspell (Vexation's Hexes, upper storey),
  sgarm (the Polished Shield), sginn (the inn's entrance, by hand: an outline part's wall '2'): 64 by 64 over the bay
  nearest the original's board (32 to 64 off its middle), bottoms over the wall's foot as the original's. And
  (`scripts/signs5b.py`) the Self Guild's board hung across its east wall (`hang`; top 224, the original's 256:
  the arm must stay 32 under the wall's top) and Caori's Curios' sign as a post with one arm south and sgMAGIC
  hanging from it (`kind: sign`, board 152 to 216). Pictures `11-sign-train.png` 0.81, `12-sign-tvrn.png` 0.85,
  `14-sign-spell.png` 0.81, `18-sign-caori.png` 0.82, `pics_retake/diff/03-sign-selfguild-ne.png` 0.52 (the board
  as the original's; the Self Guild's roof behind it is the flat-topped block of round three, a hip in the original).
  Not drawn: sgalch (02ne_corner_ y -7328: the rebuild's north-east block has no wall there), sgbank (32 west of
  the end of the bank's part p8), the second tavern's sign under its balcony and the stable's on a stall post.
- **Door slabs of the poor lanes** (`scripts/steps5.py`): Botham Hall, Dotes Family Hovel, Hall of the Tracker, House
  of Nosewort, Jack's Hovel, Holden's Hovel: `door.step` 64 out, as wide as the door, its top level with the floor
  (`height: 0, front: 0`), t14a05b, as each 02delf_poor house's slab; Aznog's Hovel a stoop 128 out falling 16
  (t14a05, the original's two slabs). Built, but they show little: the rebuild levels the land under a plot to its
  floor, where the original's houses stand on a base course 32 over the street (`20-step-jack.png` 0.78,
  `22-step-aznog.png` 0.63: Aznog's slab is under the land at its front).
- **The four cut-corner middle houses** (02delf_med1W_1, 02delf_med1S_1, 02delf_med1S, 02delf_med1W: market_middle 1
  to 3 and the waterfront Hostel; `scripts/cutcorner5.py`): one body on an outline with the two front corners cut 128
  (t14abcd02), walls 256, a t14d01 band 32, a hip 192 high whose ridge starts 160 inside the front (read from the
  models' top vertices); round four had two crossing boxes, a gable with a band of 64 and a hip with one of 112 to
  120 (the stone gable end over a thick band of round four's pictures). `24-house-market2.png` 0.87,
  `26-house-market3.png` 0.78, `pics_retake/diff/01-house-hostel-nw.png` 0.80, `23-house-market1.png` 0.64 (land
  behind). The back end is hipped where the original's is a gable.

### Decided against, and why

- The wells' frame as two platforms and a bridge-beam: three things for one model, the beam a bridge (a form faked
  with another), and the drink event split; kept the proof's post and listed the gap.
- The fountains (square, with spouts), the vault's hatch (a round hatch by a rail), the caves' mouths, the tomb, the
  south-east block's porch (round four's list): not reached this round.

### Gaps (most harmful first)

1. **A well's windlass frame** (two uprights on the rim and a beam): `post` is one post in the middle. Field:
   `frame: {posts: [w, d], beam: [w, h], taper}` on a well.
2. **A thing's faces carrying a building's event** (Caori's sign says the shop's name in the original): a sign is
   its own event. Field: `same_event_as: building:<id>` (the same field as Harmondale's trap needs).
3. **A plot on a base course over the street** (the poor lanes' houses 32 over the land, their door slabs standing
   out): a plot's land is levelled to its floor. Field: `plinth` (the floor this much over the land round it).
4. **A roof with one hip end and one gable end** (the four cut-corner houses).
5. Round four's gaps 3 (Caori's and Needful Things' overlap) and round three's 1 to 4 stand; 1 (railing) and 2 (wall
   sign) are closed.

### Tool defects (round five)

- The shop signs' bays: a sign stands over the middle of a bay, so a board off a bay's middle (six of eight here, 32
  to 64 off) cannot be placed where the original's is. `signs[].offset` would.
- See Harmondale's NOTES (round five) for the rest.

### Pictures (round five; same camera in both maps)

- **Changed places** (`r5/pics_final/`, 28 pairs, 0.725; retakes in `r5/pics_retake/` where a tree stood in front):
  best `24-house-market2.png` 0.87, `12-sign-tvrn.png` 0.85, `04-e106-council-hall.png` 0.85; worst
  `17-sign-selfguild.png` 0.36 and `25-house-hostel.png` 0.42 (trees in front of the camera in both maps; retaken),
  `15-sign-arm.png` 0.49 (the Polished Shield's block: the rebuild's long flat thatch roof over the street front where
  the original has a gable and a porch roof on posts: round four's south-east block, still open).
- **Interactive things** (`r5/pics_things5/`, round four's 162 cameras, contact sheets `r5/things5_sheet_*.png`):
  162 pairs, 0.678 (round four 0.676). Up: the cut-corner houses (`e27` 0.55 to 0.77, `e28` 0.50 to 0.71, `e25`
  0.66 to 0.85, `e23`/`e24` 0.48 to 0.56), the wells (0.64 to 0.72, 0.68 to 0.74), the council hall (0.80 to 0.84).
  Down: none by more than 0.06 (`e120-chest-5` 0.50 to 0.44, `e58` 0.59 to 0.54: the Hostel's front from close by,
  its hip now the original's but its floor 32 under the original's). Worst, all of them wrong forms still open
  (`things5_sheet_01.png`): the caves' mouths (`45-e134`, `60-e155`, `44-e133`: 0.00 to 0.42, the doorway stands
  elsewhere in its mound), the south-east block (`14-e103`, `15-e104`: the original's Polished Shield front has a
  porch roof on posts, the rebuild a flat block), the Oracle (`20-e110`, `22-e111`: the original's door and windows
  stand at the back of a porch recessed under the roof on a wooden floor; the rebuild's front is flush). The words
  for these two exist now (`porches` with `posts`, `recess`): the next round's first items.
- `oymap things`: `r5/things_orig.txt` 162, `r5/things_end.txt` 165, none without a hover name in either.

### Scripted (round five, `output/studio_cal/mm8_out02/scripts/`)

`measure5.sh`, `walk5.sh`, `pics5.sh` (with Harmondale's `cams5.py`, `texbox.py`); edits: `signs5.py`, `signs5b.py`,
`steps5.py`, `cutcorner5.py`, `council5.py` (the YAML-rewriting ones checked by diff: only the plots named changed).

## Round four (2026-11-13, `openyamm-studio/build/oymap` of the eighth merge, 11:19)

Project before round four: `output/studio_cal/mm8_out02/r4_backup/`. Scratch of this round:
`output/studio_cal/mm8_out02/r4/`; measures `r4c0` (start) .. `r4c4` (end) and `_old` (`--without rim`) by
`scripts/measure3.sh <name>`.

| Part | Start | End | Start (`--without rim`) | End (`--without rim`) |
|---|---|---|---|---|
| **total** | **92.09** | **92.20** | **91.41** | **91.52** |
| heights | 88.22 | 88.22 | 87.14 | 87.14 |
| relief | 76.87 | 76.87 | 74.04 | 74.04 |
| cliffs | 96.81 | 96.81 | 95.40 | 95.40 |
| water | 96.54 | 96.54 | 96.54 | 96.54 |
| ground | 91.67 | 91.67 | 91.67 | 91.67 |
| roads | 93.03 | 93.03 | 93.03 | 93.03 |
| buildings | 90.22 | 90.29 | 90.22 | 90.29 |
| decorations | 99.63 | 99.63 | 99.63 | 99.63 |
| spawns | 98.31 | 98.31 | 98.31 | 98.31 |
| events | 98.17 | 99.39 | 98.17 | 99.39 |
| rim (skyline) | 88.17 | 88.17 | (88.17, no weight) | (88.17, no weight) |

Walk (`playtest.yml`, 136 steps, 113 before): passes two runs of two, twice, on the final project
(`walk_r4final_d_run1..2.log`, `walk_r4final_e_run1..2.log`; also `_a_`, `_b_` before the doubled parts went), about
30 s each, not slowed by headless path planning. New: the council hall's porch
stair climbed on foot from the yard (seven steps of 32, 0.93 s); Needful Things' street stair climbed on foot into the
terrace, the shop's door used from the terrace, then the stair east from the terrace into the deck's stairwell up to
the deck (eight steps of 16 each). All eleven walks of the run without a jump, in all four runs.

### What changed (each checked against the original's export before it went in)

- **The north-east block's upper storey** (batch six's lines, checked: 02ne_corner_'s upper rows of p3 and p4 start at
  288 over a band 256 to 288 of t14abcd11): `band: 32` on p3 and p4 with the band's texture `t14abcd11` (batch six's
  copy left the band to the kit's trim, t14a05b), p3's upper south wall with the door bay 128 wide between two of 64.
  The locked door (event 494) now stands where the original's does (x 17130 to 17258, 288 to 544, t14a03). Measure
  unchanged (it reads tops). The walk's pose at the door moved with it.
- **Needful Things' two flights** (02nw_corner_): the terrace (p4) in three parts round the street stair's recess
  (128 wide, 224 deep, as batch six's copy) and the deck (p5) in three round the stairwell from the terrace, after the
  original: the deck 384 wide from x 12784 to 13168 (it was 448, 64 into Keen Edge), the stairwell 224 by 128, the
  deck's south edge a strip 32 thick and 320 high along the whole deck (the original's parapet strip; batch six's copy
  had it 224 long and 256 high). Keen Edge's ground floor (p6) moved to the original's x 13168 to 13552 (it stood 64
  east and was 64 wider) with its south wall's three bays.
- **Needful Things itself** (p2; not in batch six's list, found in the pictures of the terrace): the original's shop
  stands on the terrace, its front at y -7260 from 128 to 384 with the door (t14d03) there, under a low gable (t14b05,
  ridge 448), x 12144 to 12784. The rebuild had a flat block 1216 wide and 384 deep with its door at the street's
  level half inside the terrace, and its east end over the deck. Now the original's: p2 standing on a base 128 high,
  its south wall [t14d07, t14d04c, t14d12ba, door, t14d06], gable 64. The walk walks up to the door from the stair and
  uses it. Buildings 90.23 to 90.29.
- **The ships' names**: the original runs a ship's service from one face (its cabin door, models 120 and 113) and
  every other face says the ship's name (events 184 and 200, which the measure now counts). `click: [120]` and
  `hint: The Dauntless`, `click: [113]` and `hint: Wind`. Events 98.17 to 99.39. The walk boards the Dauntless from the
  pier and uses the cabin door (before, it clicked the hull from the pier, which the original does not open).

- **Doubled parts** (found by a scan after Harmondale's temple): the poor market's house 2 and the lanes' houses 10
  and 13 each had their first part twice (identical p1 and p2, faces in one plane); the second removed
  (`r4/sketch_before_dups.yml` before). No part of the measure moved (`r4c4` equals `r4c3`).

### Decided against, and why

- Batch six's p4/p5 split as written: its deck pieces kept the old 448 width and its south strip ended at the
  stairwell; drawn after the original's faces instead (above).

### Gaps (most harmful first)

1. **A railing**: the terrace before Needful Things has a balustrade along its south edge (t14abcd10 posts, a
   t14abcd11 rail 192 to 208) in the original; a part's `parapet` is solid. Not drawn. Field: `parapet` with posts and
   a rail (open), or a `railing` structure.
2. **A sign on a wall**: the original's sgMAGIC board over Needful Things' t14d12ba bay (320 to 384, 64 wide); a bay is
   one texture from floor to row top. Not drawn. Field: a bay split in height, or a sign `on` a wall.
3. **Caori's Curios and Needful Things overlap by 128** (p1 reaches x 12272, the original's shop begins at 12144):
   p1 left as round three drew it (its door 64 off the original's too); the overlap is inside both.
4. Round three's gaps 1 (ledge slope per side), 2 (rim shelf with a hill), 3 (switch on some faces), 4 (one event on
   two doors) stand; 5 (storey door's texture and place) is closed.

### Tool defects (round four)

- `oymap things` refuses outdoor maps (Harmondale's NOTES, `output/studio_cal/mm7_7out02/repro/things_outdoor/`);
  the interactive things were pictured from this round's list (`output/studio_cal/mm7_7out02/scripts/things4.py`).
- The other defects of this round are in Harmondale's NOTES ("Round four").

### Pictures (round four)

Folders under `output/studio_cal/mm8_out02/r4/`; contact sheets of the interactive things, least alike first:
`things_sheet_01.png` .. `_18.png`. All looked at.

- **Places changed** (`pics_changes2/`, final project, 9 pairs, edge agreement 0.777; `pics_changes/` the first take
  before Needful Things was redrawn): Needful Things' stair close up 0.63 to 0.72 (`diff/04-needful-stair-close.png`),
  the deck from the terrace 0.63 to 0.74 (`06-needful-deck-from-terrace.png`), the terrace from the street 0.75 to 0.78
  (`03-needful-terrace-from-south.png`): the shop now stands on the terrace with its door, window and low gable as
  the original's; missing still the terrace's railing and the shop's sign (gaps 1, 2), and the round tower beside it
  reads plain plaster where the original's has a thatched skirt. The upper door 0.82 (`01-upper-door-from-south.png`:
  door, band and windows line up), Keen Edge 0.83, the council's porch stair 0.76 (unchanged).
- **Interactive things** (`pics_things/`, 162 pairs, 0.676): best the crystal (`diff/63-e159-crystal.png` 0.98), the
  lanes' thatched houses (`147-e84`, `141-e78` 0.96 to 0.97), the ships (`62-e157-ship-dauntless.png` 0.94), the
  slate-roofed waterfront houses (0.95, 0.96). Worst, for the next round (none of it this round's work):
  - the caves' mouths (`45-e134`, `60-e155` smugglers' cove, 0.00; `44-e133`, `59-e154` wolf den): the camera at the
    mouth sees the original's arch and dark way in and the rebuild's earth: the rebuild's doorway stands elsewhere in
    or behind its mound;
  - roofs: the market's and waterfront's middle houses (`86-e23`, `87-e24`, `91-e28`, `88-e25`, `120-e57`, `121-e58`,
    0.48 to 0.66) have plain hips in the original and in the rebuild a stone gable end over a deep thatch band;
  - the poor lanes' houses' front steps (a slab before the door: `129-e66`, `133-e70`, `145-e82`) are missing;
  - signs on walls (`01-e1`, `13-e102`, `39-e129`, `16-e105`) and the council's door canopy (`17-e106`) are missing;
  - the fountains (`42-e132`, `58-e153`): a square stone fountain with spouts in the original, a low round pillar in a
    basin here; the wells (`30-e121`, `31-e122`): a stone ring with a single post in the original, a roofed well here;
    the vault's hatch (`49-e138`, `61-e156`): a round hatch by a rail in the original, a wooden box here; the tomb
    (`40-e130`) differs; the south-east block's porch (`15-e104`, `14-e103`).

## Round 3

Scratch as before; every oymap command `openyamm-studio/build/oymap` (`scripts/measure3.sh` measures under both
judgings, `scripts/walk3.sh` and `walk3x3.sh` play, `scripts/pictures3.sh` and `pics_r3.sh` take pictures). The
project as round three found it: `r3_backup/`; measures `r3cNN/` (new judging) and `r3cNN_old/` (`--without rim`),
start `r3c0`, end `r3c12`; every variant tried singly in `r3v/<name>/` with its edit in `r3v/edits/` and its measure
in `r3v_<name>.txt`.

### Scores (`oymap compare`, original against this project)

| Part | Start (new) | End (new) | Start (old) | End (old) |
|---|---|---|---|---|
| heights | 87.47 | 88.23 | 87.13 | 87.14 |
| relief | 75.74 | 76.84 | 74.60 | 74.03 |
| cliffs | 96.08 | 96.80 | 94.56 | 95.39 |
| water | 94.58 | 96.54 | 94.58 | 96.54 |
| ground | 90.42 | 91.67 | 90.42 | 91.67 |
| roads | 93.01 | 93.03 | 93.01 | 93.03 |
| buildings | 89.94 | 90.22 | 89.94 | 90.22 |
| decorations | 99.63 | 99.63 | 99.63 | 99.63 |
| spawns | 98.31 | 98.31 | 98.31 | 98.31 |
| events | 96.95 | 98.17 | 96.95 | 98.17 |
| rim (skyline) | 73.43 | 78.94 | (no weight) | (no weight) |
| **total** | **90.20** | **91.35** | **90.91** | **91.41** |

"New" is the judging since the morning of 2026-11-13 (heights, relief and cliffs over the playable square only, the
land beyond it by its skyline); "old" is `--without rim`. Walk: `playtest.yml`, 113 steps (83 before), passes three
runs of three, twice (`walk_r3a_run1..3.log`, `walk_r3final_run1..3.log`). Pictures (same cameras, both maps):
`r3p0_backup_worst/` (the project as round three found it) against `r3p1_worst/` (end), edge agreement 0.684 to
0.693 (region-H5 0.76 to 0.83, region-B5 0.67 to 0.81, east-shoulder 0.63 to 0.70); town `r3p1_town/` 0.764
(round two's end 0.761).

### What changed (each a script in `scripts/`, applied to the project, its diff read)

- **The code agent's proofs** (`apply_s4f.py`, lines taken from `output/studio_s4f/item4_r`, `item5_r`): the
  north-east block's upper-storey locked door (event 494, `doors[].storey: 2`), the inn's upper floor with a
  flat-topped hip (`roof_height: 576, cap: 384`), `into.screen` on the den (353), the cove (351) and the crystal
  (355), the Hostel's key-building as `lua_before`, the crystal's `click: [77]` and `hint: Escaton's Crystal`.
  Events 96.95 to 98.17.
- **The crystal's last step**: the code agent's walk failed there because the crystal's way in now shows the
  "Enter Escaton's Crystal?" screen (`into.screen`), and the walk did not answer it; the click itself hit the door
  face and ran its event. The walk now answers the screen. No fault in the build.
- **Rows and rings** (`rows_r3.py`, after the code agent's `rows.py`): 13 entries of `scatter[].line` (105
  decorations): the 35-stone rectangular kerb by the Hostel (`closed`), the stone ring of rock16, the avenue of
  tree12, the gardens' plant rows and rings. Kept only where the build's even places stand within 1.1 steps and 0.3
  cells of the original's (paired one to one); the tight clumps of a bed (4 plants in half a cell) stay single.
  `rows.py` counted an id as named once by substring (rock22_1 inside rock22_10), which left three stones of the kerb
  out and drew it as a broken row 3 cells off; fixed here. The stone circle north of the camp (34 stones of rock17)
  is a spiral walked in from the east with uneven steps (0.5 to 1.3 cells): as a row its stones would stand up to 0.8
  cells off, so it stays placed stone by stone. Decorations unchanged (99.63).
- **The rim** (`land_r3.py`): see "The rim" below.
- **Land inside the square** (`land_r3.py`, numbers from `hprint.py`, `hdiff.py`, `ridge_search.py`): nine
  `heights.ridges`: the east upland's face over the town is a cliff to about 1300 and then a shoulder rising to 2200
  over three cells (two lines, the lip and the shoulder; the cliff alone had held the shelf's 2200 to its edge), the
  inlet's north ledge at 1900, the gully at the headland's east end, ledges on the west upland's inner face north of
  the den, under the east cliff above the seer and by the seer's ring, on the west pass's and the east cut's north
  walls. `ridge_search.py` lists long thin groups of nodes the build misses by 600 or more and says the original's
  form across them; only ledges, ridges and channels were tried, each singly (`r3v_cand_N`), and kept when the
  measure rose. The chapel spur's east face one node west (x 28, as the original's spur ends). The east cut's south
  side is a slope in the original (the floor rising to the shelf over five cells), not a cliff: the measured cliff
  line's last three points went (`cut_r3.py`).
- **Water**: the sea's outline a cell in along every shore (`inset.py`, `townshore_r3.py`: the build's sea had stood a
  cell beyond the original's water tiles all round; the town's harbour shore taken back where the inset passed
  them); the middle river split, 3 cells wide from the upper bridge down (`river_r3.py`, it had been 4 and a cell
  north and east); the north pond a cell smaller on the east and south (`pond_r3.py`; now cell for cell the
  original's). Water 94.58 to 96.54, ground 90.42 to 91.67.
- **The pier's guards** (`guards_r3.py`): the original's model 92 (one of three named Dock_W: eight invisible
  upright faces, the rails along the west pier's arm and head and a pair at each end where a ship berths) taken
  whole as `thing:pier_guards`. See gap 3.
- **Walk** (113 steps): into the Dire Wolf Den through its "Enter?" screen (house 353); the north-east block's
  upper-storey door says "Door" and opens nothing; the crystal's other faces say "Escaton's Crystal"; the crystal
  shut without the key; the Hostel with the four Hearts builds the key (quest bit 286, the key to the hand, then
  the hall opens), the key put in a pack; the crystal with it through its "Enter?" screen (house 355) into d10.

### The rim

The original's rim: sea on the south (98 % of its nodes at 0); the east a shelf of 2144 to 2848 with a crest
running north and south at x 118 to 121; the north two shoulders of the uplands (2304) with the north road's low
grassland between; the west an upland shelf with a hill of 3700 at [10, 62], then the headland to 6400, then sea.
Round two said all of it with the grid of spot heights (the same 32 x 32 grid as inside the square, every 4 cells),
the bands and the points, and carried two `frame.rim` entries that shaped nothing (no `form`; `depth` retired).

- Kept the grid as the rim's description on the north, east and west, removed the two old entries (no warnings
  left), and added `frame.rim` for the south sea (`form: level, height: 0`) and `frame.edge` (0 north, west and
  south; 2304 east, the original's outermost row and column) in place of round one's 8000 cliff along row and column
  1.
- Why not `frame.rim` forms on the other sides: a level shelf on the east (`[2144, 2848]`, roughness 70) measured
  +0.03 under the new judging (rim 73.68 against 73.42) and -0.9 under the old, and it loses the crest at x 118 to
  121 that the grid's spot heights keep; level shelves on the north's ends and the west lose 5 points of the rim
  part (68.4) because the west's hill and the headland are no shelf: `frame.rim` has no word for a shelf with a
  hill on it, and the headland is the points' work either way (`r3v_rim4`, `r3v_rim5`). Neither form is a trace;
  the grid is the coarser of the two descriptions the rules allow and the closer here.
- Roughness: beyond the square the original's uplands are rough (a node 35 off the mean of its eight neighbours on
  the east, 49 on the west, 42 on the north) and the grid's land was smooth (17, 29, 21). Three `heights.rough`
  areas with amounts chosen to meet the original's figures (25, 35, 35 give 33, 48, 41: `roughzone.py`), not to
  maximise the measure (amount 60 measured higher still). Rim part 76.88 to 78.11; the old judging, node by node,
  pays 0.2 for the bumps not being at the original's places. Inside the square the build's walkable ground is about
  as rough as the original's (26.9 against 30.7 in the basin), so no rough area there (one measured lower, as the
  code agent found).

### Gaps (most harmful first)

1. **A ledge's slope on one side only**: the east upland over the town is a cliff to about 1300 and then a shoulder
   rising to the shelf over three cells; `heights.ridges[].slope` runs back on both sides (the low side would lift the
   town's edge), so the shoulder is two ridge lines a node apart. Field: `slope` per side (`slope_left`,
   `slope_right`), or a ridge's `rise_to` on its high side.
2. **A shelf with a hill on it** (the west upland beyond the square: 2304 with a hill of 3700): `frame.rim` level
   is one height or a band; so the grid says it. Field: rim entries that take height points (or `form: level` with
   `peaks`).
3. **A switch on some faces of a model**: the original's pier guards (model 92) are eight invisible faces of which
   two (facet group 12, the north pair where Wind berths) follow the ship; `switch` takes the whole model. Taken
   whole without a switch: while Wind is away the north end stays closed (the original opens it). Field: `switch`
   with a face selection (`faces: [4, 5]` of the model), or `from.faces`.
4. **One event on two doors**: the inn's upper floor has a second door face over the canopy with the same event
   (209) as the ground door; a second `doors[]` entry is a second event (unpaired in the measure), so the upper door
   is only its texture. Field: `doors[].same_event_as`.
5. **A storey door's own texture**: `doors[].storey` takes the kit's door texture (t14c03), not the texture its bay
   names (the original's t14a03), and its row starts at 256 where the original's starts at 288 over a trim band
   (see Tool defects).
6. Still open from rounds one and two: one roof over a non-convex hall (the Sanctum), an arcade (the council tower),
   the ships' empty hint events (184, 200). Said now: the transition screens, the upper-storey door, the flat-topped
   hip, the steps before a house, a model's hint, rows and rings.

### Tool defects and findings

- **A storey door takes the kit's door texture**, not its bay's (`t14a03` named in `upper_walls`; built `t14c03`),
  and stands 32 lower and 64 east of the original's face. Repro: `output/studio_cal/mm8_out02/repro/storey_door_texture/check.sh`.
- **The rim part is decided by the land within a cell of an eye**: eyes stand 192 over the original's land and the
  first sample is half a cell out, so a rebuild node 300 to 400 higher than the original's beside one eye reads as
  a horizon 30 to 45 degrees up on every sight line from it. B5 (one eye at (19, 76)) and H5 (one eye at (109, 60))
  are among the worst regions for that alone. Repro: `output/studio_cal/mm8_out02/repro/rim_eye_sensitivity/run.sh`
  (`scripts/skyline.py` draws the measure's sight lines). Starting the samples a cell or two out, or the rebuild's
  eye on the rebuild's land, would judge the rim and not the square's edge.
- **A model import of several models is one model**: the measure pairs models one by one, so four of each ship's
  five pieces and three of the crystal's four are "only in the original" (`r3c12/differences.json`, buildings), though
  their faces are the same.
- **Wind still cannot be clicked after its load event in a headless run, in the original too**, with today's game
  (09:34): `repro/wind_hidden/probe_original.yml` fails at the interaction (`repro/wind_hidden/original_r3.log`).
- The code agent's `rows.py` counted ids by substring (see above).
- `oymap compare` writes into a shared place: two compares of the same project run at once fail ("the map has no
  event script"); `measure3.sh` runs them one after the other.

### Score against form

- The rim's roughness lowers the old judging by 0.2 and raises the new by 0.6: the original's uplands are that rough;
  amounts set to the original's figures, not to the measure's best.
- The east shelf as a `frame.rim` level form would measure +0.03 (new) and is the vocabulary's word for a shelf, but
  it loses the crest the grid keeps; the grid stays.
- The stone circle stays stone by stone (a row would place its stones up to 0.8 cells off).

### Unsure

- Whether the original's two invisible guard faces at the north end of the west pier are meant to block the party
  while Wind is there (they become solid with the ship) or are a leftover; kept as the original has them.

## Round 2

### Scores (`oymap compare`, original against this project)

| Part | Start | End |
|---|---|---|
| heights | 87.0 | 87.1 |
| relief | 74.4 | 74.6 |
| cliffs | 94.0 | 94.6 |
| water | 92.9 | 94.6 |
| ground | 86.1 | 90.4 |
| roads | 93.0 | 93.0 |
| buildings | 86.5 | 89.8 |
| decorations | 94.4 | 98.8 |
| spawns | 98.3 | 98.3 |
| events | 95.1 | 97.0 |
| **total** | **89.1** | **90.8** |

Worst regions at the end: A6 72.3 (headland backdrop), B5 74.6, D2 75.0, A3 75.3, E3 76.3, C1 77.4 (B6, the inlet,
61.9 at the start, is no longer among them). Town pictures: edge agreement 0.700 at the start, 0.761 at the end, the
same sky (plansky3, weather step 0) on both sides. Walk: `playtest.yml`, 83 steps (54 before), passes three runs out of
three (`walk_r2_run1..3.log`).

### What changed (each a script in `scripts/`, its diff checked, kept only where the measure rose or the form came closer)

- **Decorations** (`scatter_r2.py`): round one's scatter, split at the measure's region borders, is gone. What the
  original plants is placed: in the town every tree (the avenue, the gardens' trees, the big trees south of the
  square), every plant (beds, hedges, the garden borders) and every rock of a tight row or ring (the garden kerbs),
  the stone circle of rock17, the camp's fence rows, hedges and cages, the bed north of the town, and everywhere the
  things set down (cauldrons, buoys on the water, campfires, bottle, bowls): 438 structures of kind decoration,
  positions taken from the original. What grows is scatter: natural clumps whole (none of 4 or more at 1.6 cells
  outside the planted places), the rest per kind in 8 x 8 blocks over the box round its members. Counts per kind are
  the original's; the 15 `null` entries (decoration 0, no picture) are not placed.
- **Buildings**: the four houses of model 02delf_rich2 (`rich2.py`: Hostel, Bluesawn Home, Arius' House, House
  Understone) as the original's one model turned: body and wing as outline parts with cut corners and hip roofs, bays
  from the faces. The Adventurer's Inn (`inn.py`) described anew: ground floor of eight sides with an entrance bay,
  jettied upper floor, hip roof, entrance canopy (round one had a cross of gabled boxes). Bridges (`bridges_r2.py`):
  deck 608 with a kerb 144 for the railings (round one 864 over the brackets, no rail). Heights from the tops picture
  (`tops_r2.py`, `heights_r2.py`): the three 02delf_poor2 houses walls 384, the two warehouses walls 416 with roofs
  160, the north-west block's tower cone 512, Steele's Vault and the Self Guild's west end two storeys, the Sanctum's
  towers at the original's middles and radii. The cave mouths have `depth` and `hood` (den 256/320, cove 212/528).
  The crate stacks say Sealed Crate (event 407).
- **Events and people** (`events_r2.py`, from `oymap flow` of the original, `an/r2_orig_flow.txt`, and the
  original's handlers): both ships and the Hostel lock while the pirates hold the town; the Hostel builds the Conflux
  Key from the four Hearts; the crystal opens for the key or once opened (map variable), and `evt:crystal_gone`
  hides it after the endgame; the fountain as the MMerge supplement the game runs (portal bit, gold twice, dimension
  door); load events 1 (new home), 3 (the endgame), 4 (the pirate invasion, in words: shows group 10, empties the
  bank, qbit 57; else hides them); timers 131 (invaders defeated, every 15) and 132 (dire wolves, every 20, summons
  the last wolf). The 78 invaders of the original (group 10, Regnan Bandit/Brigadier/Pirate along the shore) as 32
  hidden actor entries by clump and kind. `oymap flow` of the rebuild (`an/r2_bp_flow.txt`) now differs from the
  original's only in numbering, the split event 3, the transition screens (gap 5), the upstairs door (gap 4) and the
  empty hints.
- **Land and water**: the edge cliff along the west column ends at y 102 where the upland meets the sea (it made a
  dirt strip along the sea); the inlet's water as the original's tiles (from y 84; a low rock shelf behind it under
  the cliff ring); the north pond a diamond round [82.5, 12.5]; two height points from a search over the original's
  peaks, hollows and ledges (`hgreedy.py`: of about 200 tried singly none moved the land parts by more than 0.01 %,
  two were kept) and two at the vault's cliff foot (the vault had stood 300 to 600 up on the cliff's slope).
- **Ground** (`ground_r2.py`, round one's `ground_zones.py` with its constants as parameters): zones to the east
  column and the south row (the build takes points on 128 now), dirt opened by 2 (the pass floors), outlines at 0.6
  cells (round one 0.9): 19 zones, 704 points.
- **Walk**: the inn's door, the Hostel (house 899), The Dauntless from the pier head (house 480), both shut while
  qbit 57 is set, and at the end, back in Ravenshore by `load_map`, the crystal shut without item 610 and leading to
  d10 with it.

### The models taken from the original

The two ships and the crystal stand exactly where the original's do (their models' extents match the original's to
the unit). The Dauntless is clicked from the west pier's head and enters house 480 (the captain's two boat routes);
Wind enters house 483 (the smuggler's two routes) and is hidden until `evt:smuggler_ship` (qbit 10); the crystal
leads to d10 with item 610. What an import cannot say: it cannot be turned (not needed here); the whole thing is
clicked, so the crystal's other faces cannot say "Escaton's Crystal" (event 404) while its door says "Enter
Escaton's Crystal", and the ships' second events (184, 200: empty hints) are not there; the pier's two faces that
the original makes untouchable while Wind is away (facet group 12 on Dock_W) cannot share the ship's switch.

### Gaps (most harmful first)

1. **Roughness of the ground** (relief 74.6: the original rises 213 a cell, the rebuild 185; every region). Height
   points do not help (see above). Field: `heights.rough` per area (amplitude, scale).
2. **Rows and rings of decorations** (the town's garden kerbs and hedges, the avenue, the stone circle, the camp's
   fence): placed singly, 438 structures. Field: `scatter[].line` with `closed` and spacing.
3. **A model import's faces**: one event for the whole (crystal 404 hint, ships 184/200), and no shared switch with
   another structure (Dock_W's gangway faces, group 12). Fields: `hint` on a model, `door_models` naming the models
   that carry the click; `cog` shared between structures.
4. **A door on an upper storey**: the north-east block's locked door at 288 to 544 (event 494, "The door is
   locked"; only its texture t14a03 is there) and the inn's second door over its canopy (event 209). Field:
   `doors[].storey` (a door in `upper_walls`).
5. **The transition screen of a way into a map**: the original's MoveToMap passes the house of the "Enter ...?"
   picture (351 cove, 353 den, 354 Alvar's house, 355 crystal) and icon 1; the build writes 0, 0. Field:
   `into.screen`.
6. **A hip roof with a flat top** (the inn: 1024 x 384 at 928); the build's hip on an outline slopes to a ridge (960).
   Field: honour `hip` (or a `cap`) on outline parts.
7. **Steps before the house**: a plot door runs condition, house, effects, lua; the original's Hostel plays the movie
   and takes the Hearts before it enters. Field: `effects_first` or `lua_before`.
8. Still open from round one: one peaked roof over a non-convex hall (the Sanctum), an arcade (the council tower).

### Tool defects and findings

- **A model hidden at build and shown by its load event stays unclickable in a headless scenario, in the original
  too**: with qbit 10 set and the load event run (`execute_event` 160 here, 2 in out02.odm) the Wind ship is not
  picked from the pier, while the same pose picks it when it is built visible. Repro:
  `output/studio_cal/mm8_out02/repro/wind_hidden/` (`probe.yml` on `visible_mount` passes, on `../mount` fails;
  `probe_original.yml` on the shipped out02.odm fails). So the walk does not test Wind. Probably the runtime's
  SetFacetBit outdoors (or the harness), not oymap.
- `differences.json` does not name the original's decorations without a partner (only counts by kind and region);
  `scripts/decopair.py` pairs as the measure does and lists them.
- The measure counts the 15 `null` entities (decoration 0) and the empty hint events (184, 192, 200, 202) as things to
  pair.
- The schema says `hip` is "not for an outline or round part", but the build takes it on outline parts (the Hostel).
- In a scenario, `lua_event` with `evt.MoveToMap` from an indoor map does not move the party; `load_map` does.
- Round one's `scripts/tops.py` was overwritten by mistake in round two (now `tops_r2.py`).

### Score against form

- Every change above raised the measure or left it equal; none lowers the form. A cliff along the headland's north
  face (y 71) where the original breaks by about 1,600 lowered the land parts slightly (cliffs 94.0 to 93.5) and was
  not kept: its line did not follow the original's break closely enough to be the truer form.
- The town camera before Needful Things (`needful-things-door`, edge agreement 0.43) stands under the Hostel's eave:
  the rebuild draws the roof's underside there, the original does not. The view is not a fault of the street.

### Unsure

- The endgame and invasion events run on every arrival as the original's do (event 4 empties the bank on each
  arrival while the town is held); kept as the original.

## Round 1

Scratch: `output/studio_cal/mm8_out02/` (backup of the project as it stood: `r1_backup/`; every measure `cNN/`;
scripts `scripts/`; pictures `ingame_town/`, `ingame_town_final/`, `ingame_worst/`).

### Scores (`oymap compare`, original against this project)

| Part | Start | End |
|---|---|---|
| heights | 85.5 | 87.0 |
| relief | 72.7 | 74.4 |
| cliffs | 86.4 | 94.0 |
| water | 92.2 | 92.9 |
| ground | 55.9 | 85.3 |
| roads | 80.6 | 93.0 |
| buildings | 69.6 | 79.9 |
| decorations | 97.7 | 97.1 |
| spawns | 98.3 | 98.3 |
| events | 77.2 | 87.6 |
| **total** | **79.7** | **87.6** |

Worst regions at the end: B6 56.5 (inlet arch, ships' approach), E7 62.3 (the captain's ship), B3 66.5 (den mouth),
B5 70.6, A6 70.7 (headland backdrop), B2 71.6. Walk: `playtest.yml`, 49 steps (33 before), passes.

### What changed

- **Ground**: zones written from the original's corner kinds (`scripts/ground_zones.py`): grass under everything,
  the rock bands, dirt wider than the build's own lines (town yards, beaches, den, chapel spur), grass inside dirt
  (between the town's houses), rock again where dirt covered it. Outlines Douglas-Peucker 0.9 cells, blocks under
  6 to 9 corners left out. 28 zones, about 350 points. The `steeper_than` rock zones are gone (the rebuild's steep
  cells are not the original's, so rock fell on plateau tops).
- **Things that are not houses** (`scripts/add_things.py`): the Tomb of Lord Brinne (wings, stepped body, spire,
  cap, west door into d28), the two cave mouths as doorways (d08, d07), four piers (two T-shaped timber piers, deck
  256 wide at 264), four crate stacks, the meadow camp's three chests (chests 6 to 8), the vault's kerb and hatch,
  the five clickable decorations (reagent tree and rock, potion tree, buoy, the tree with a chest), MAW's dimension
  pedestal (the rulesets' overlay of the original), the seer's star dais as parts of the oracle's plot, Botham Hall
  back as its own house (it had been a third part of Neblick's House), Lua for wells, obelisk and fountain as the
  original's handlers do.
- **Council hall** (`scripts/council.py`), **Sanctum** (`scripts/sanctum.py`), **Chapel of Eep**
  (`scripts/chapel.py`) described anew from their faces (`scripts/faces.py`, `scripts/elev.py` draw them):
  porch deck and stair, L-shaped hall, tower, terrace with ramp; the Sanctum's narrowing hall with its north notch
  and three round towers, not turned; the chapel's ten-sided hall and two drums. The Sanctum's footprint in
  plan.yml 5.5 x 6.5 to 5 x 6 so its levelled floor stays on the terrace (576; the original 640).
- **Needful Things**: the terrace 128 up and its two flights of steps; the footbridge onto Vexation's Hexes' deck.
- **Land**: the terrain's zero border row and column as an edge cliff; cliff lines measured from the original's
  breaks (`scripts/cliffs.py`, breaks over 640, chained, simplified 0.75) outside the headland, the hand-drawn ones
  kept on the headland where measured ones scored worse; the temple terrace as a cliff ring 640 high; the west
  arm's sheer sea face; the inlet's north face at y 80; the den mouth's floor; the crystal's plinth (land 320 high
  with upright sides). Lanes house 6 moved half a cell off the river.
- **Water**: the river in three widths from the original's water tiles (2, 4, 3 cells) with the oxbow and the wide
  bend as ponds; the sea's edge along the headland's west arm.
- **Roads** (`scripts/roads_town.py`): the paved ring round the square and the blocks, the cross street, the lane
  to the south pier, the garden loop, the east lane, the lanes' paved street (it was a dirt path), the north shore
  road's end. Extra lines reuse the link `road:harbour_plaza`.
- **Scatter** (`scripts/scatter_clusters.py`): each kind's clumps of 4 or more (single linkage 1.6 cells) as
  their own entries, one per 16 x 16 region they lie in (the measure counts by region), the rest per block;
  decorations on steep ground say `steep`. Counts per kind are the original's. The crystal's plinth is
  `keep_clear`.
- **Atmosphere**: `atmosphere.yml` with the original's daily fog (20/10/5).

All `scripts/` read `an/orig.json` (`oymap export assets_dev/worlds/mm8/maps/out02.odm`) and write the sketch; each
change was measured (`scripts/measure.sh cNN`) and kept only where the score rose or the form came closer.

### Gaps (most harmful first)

1. **Ships** (10 models of the two ships at the west pier, houses 480 The Dauntless and 483 Wind: the boat
   services). Not built; `plots` of both ships stay `form: none`. Field: a `kind: ship` (hull, masts, gangway
   door with `house`), or a model import.
2. **Escaton's Crystal** (4 models, shards to 2048, the door into d10 when the party holds item 610). Only its
   plinth (land) is said. Field: a model import or `kind: crystal`; and a door with a `condition`.
3. **Conditional chest**: the Vault of Time opens chest 19 only with Emperor Thorn's Key; `chest` opens on every
   click before `lua`, so the hatch here only takes the key. Field: `chest.condition`, or the chest's number in Lua.
4. **Conditional plot door**: the council hall's terrace door asks for qbit 59 and otherwise speaks to NPC 3; here
   it always leads in. Field: `doors[].condition` / `lua`.
5. **One title per plot**: the four corner blocks are 3 to 5 models, each with its own shop's name on its walls
   (9 name events of the original unpaired). Field: `parts[].title` (or each door's title on its own part's walls).
6. **Hip and gable roofs on chamfered houses** (02delf_rich2: the Hostel, Arius' House, Bluesawn Home, House
   Understone): their corners are cut at 45 degrees and the cut walls carry windows; a hip needs a box, an outline
   part only takes flat or cone. So the boxes cover the chamfers (the town camera before Needful Things stands in
   the Hostel's box corner). Field: `roof: hip|gable` on an `outline` part.
7. **A second, title-only event on a model** (vault 408, fountain 449, crates 407, cave mouths 401/402): one
   structure has one event. Field: `hint` beside `title`.
8. **Tapered and flared parts** (the tomb's spire and cap), **arches** (the council tower's arcade), **hoods**
   (the den's dirt hood 576 x 896, the cove's rock arch): a doorway is a 64-deep frame. Fields: `taper` on a part,
   `depth`/`hood` on a doorway.
9. **One peaked roof over a non-convex hall** (the Sanctum): three cones. Field: a roof over several parts.
10. **Sloping slab** (the council terrace's ramp, the piers' ramps from the quay at 192 to 264): steps of 16.
11. **Chest of mixed levels** (chest 11 in the tree: one of level 7, three of level 3). Said as level 3.
12. **Weather by chance**: the original rains by its `bolster_maps.txt` row (keyed by map number); this map has
    its own number. Field: an atmosphere word for the world's weather chances.
13. **A plot's floor**: levelled at the mean of the land under it, so a building at a terrace's edge sinks
    (Sanctum 576 against 640). Field: `floor` on a plot.

### Tool defects

- **Ground zones never reach the east column and the south row of corners** (x or y = 128): points stop at 128
  and the inside test is half-open, so the all-over grass zone leaves dirt along the whole east and south edges
  (115 cells of column 127 here, 0 in the original). Repro: `output/studio_cal/mm8_out02/repro/ground_edge_nodes/check.py`.
- **`validate` refuses two cliff lines that share an end point**: cliffs `[[95,13],[98,18],[98,22],[96,23]]` and
  `[[96,23],[94,24],[92,27],[96,31]]` give "cliffs[1] ends at [96, 23], 2.2 cells short of heights.cliffs[0]".
  Repro: `oymap validate output/studio_cal/mm8_out02/repro/cliff_shared_end --assets assets_dev`. Worked round by
  joining such lines into one.
- **Decorations are measured by region**: a clump drawn as one circle across a region border lost 8 points of the
  part (97.7 to 89.6); clumps are now split at region borders (see below).
- The build's "reach onto water or its shore; they stand at the water's level" names lanes_poor 6 and the Sanctum
  even after the first was moved off the shore and the second stands at 576.

### Score against form

- Clumped scatter is closer to the original's look than even spread and first measured lower; splitting clumps at
  the measure's region borders brought the part back to 97.1 (from 97.7 even). Kept clumped.
- The measured cliff lines on the headland scored worse than the hand-drawn ones (narrow ridges with a low side
  on both hands chain into one line with one `down`); kept the hand-drawn ones there.
- The terrain's border row and column at 0 are said with an 8000 drop cliff along the edge: the original's land,
  far beyond the travel prompts.

### Unsure in the original

- The fog's colour in the pictures: the original's fog is lavender, the rebuild's grey-blue, with no fog tint in
  either scene; possibly the day's sky.
- The fountain: `out02.lua` gives gold and the town-portal bit; the MMerge handler (`oymap flow`) opens the
  dimension door. The rebuild follows `out02.lua`.

## Cleanup: z-fighting and town feel (2026-11-14, `openyamm-studio/build/oymap` of the fourteenth merge)

Backup before: `output/studio_cal/mm8_out02/cleanup_backup/`. Scripts: `output/studio_cal/mm8_out02/cleanup/edit_r.py`
(trims box parts to where they meet, slicing their bay lists), `edit_r2.py`, `edit_r_tf.py`; `cleanup_parts.py` lists a building's parts.

**Faces in one plane: 205 to 46** (1 the original's ship; the original 7). Changed:
- Aznog's Hovel (lanes_poor 9): p2 was p1 again: dropped (28 pairs).
- market_rich 1, 2: p1 only south of / west of p2; market_rich 6, 7: the low wing only where it stands out of the hall, flat-topped.
- waterfront_rich 1: p3 lay wholly inside p1 (a second east front): dropped; p2 only north of p1.
- ne_block: p1 stops at p4, p2 only east of p4 and north of p3; the tavern's door and sign are p3's (its west wall had the
  same door bay over p2's); p6 only its lean-to over p4's top (ridge kept at 616).
- oracle: p2 (the cross roof) hangs on p1's fascia at 272 with a 16 band (ridge kept at 400).
- The two pier arms end at their heads' sides; the council ramp 32 wider into the terrace (the original's ramp has no east side).

Left (45), with why: nw_block (23 pairs, 13 parts): its parts lie in each other (Keen Edge's p3 wholly inside p7, its
door inside p7's outline); it needs a redraw from 02nw_corner_'s faces, not a trim. Its steps beside the terrace (8
pairs, under 640 square units each). The body/wing soffits of market_rich 3-5 and waterfront_rich 2 (8): two 64 eaves
meeting at the join (no per-wall eaves). dancing_ogre p1/p5 (5, 5120 units). building_1 hall/towers (2): round flat tops
at one height overlapping (the original's d45out_S has tops at 2304 in several models too). ne_block p4/p6 (3, was 3 at 107k
units, now 15k). Council ramp (3: its foot under ground against terrace_west, its side against `middle`).

**Town feel**: magic shop to alchemist 5693 to 5690 (the shipped top 5677 is this original's): the Apothecary's front at
the original's y -7328 (02ne_corner_), 112 north of where it stood; the remaining 13 units are the door's bay middle
against the original's face middle. Nothing else outside.

**Score** 92.18 to 92.18 % (every part unchanged). **Walk** two of two. **Installed** in `rebuilds_root` with terrain
materials; desktop load check impossible (no display). **Pictures**: `output/studio_cal/mm8_out02/cu_pics/before.png`, `after.png`.

## North-west block (2026-11-14, `openyamm-studio/build/oymap` with batches O-A to O-F)

Backup before: `output/studio_cal/mm8_out02/nw_backup/`. Work in `output/studio_cal/mm8_out02/nw/`: `faces.py` (a
model's faces in the plot's frame; `orig_faces.txt` is 02nw_corner_, models 50-54), `edit_nw.py` (the redraw),
`edit_eaves.py`, `edit_ogre.py`, `edit_ne.py`, `edit_ramp.py`, `check.sh` (fmt, build, install, audit, compare).

**Faces in one plane: 46 to 3** (1 the original's ship; the original 7). Changed:
- nw_block, redrawn from 02nw_corner_ part by part, no part inside another: Caori's Curios is one twelve-sided tower
  (p1: middle 368,1500, sides 128 at 256 out, walls t14a01 to 768 with t14a05 above 256, door t14a03 south, t14a04b
  west and north, eaves 64, cone to 1280); the box under it and the fourteen-sided p8 are gone. Keen Edge's ground storey
  is three boxes that meet (p6 west block 1648..2032 x 988..2012 with sgWeap on its east end, p3 the door block
  2032..2288 x 860..1756 with the door t14d03 at 2032..2160 as the original's, p7 the corner 1904..2032 x 860..988),
  flat tops at 256 (the roof walk); its upper storey p10 (1648..2032 x 1628..2012) and p12 (an outline with the cut
  corner 2288,1756 to 2032,2012), hip roofs to 704 with eaves 64 except where they meet. Vexation's Hexes' gable 64
  high with eaves 32 (was 48 and a 16 fascia). Every bay's texture as the original's faces.
- The street steps and the deck steps lie exactly in the terrace's recess and the deck's stairwell (they were one or
  two units off and cut into p4, p4c, p5, p5b).
- market_rich 3-5, waterfront_rich 2: the wing's eaves only on its three outer walls (`eaves_walls: [1, 2, 3]`).
- dancing_ogre p1: fascia 32 (the original's band t14abcd11 384..416), not 40 into p5's wall.
- ne_block p6: the lean-to starts on p4's top (616) with no walls or fascia, still to 640.
- Council ramp: 4 north, same length and slope, its foot and top end off the walls' planes.

Left (2 new): building_1's round tops at 2304 overlapping the hall's (the original's d45out_S has such tops too).

**Score** 92.18 to 92.19 %: heights 88.22, relief 76.85, cliffs 96.72, water 96.54, ground 91.67, roads 93.03,
buildings 90.43 to 90.46 (90.53 after the redraw; the wings' missing side eaves and the ramp cost 0.07), decorations
99.81, spawns 98.31, events 98.79, rim 88.17. Region F5 (the block) 91.6 to 91.7 %.

**Gaps** (words missing):
- Eaves along part of a wall: the original's wing soffits start at the body's wall; `eaves_walls` takes whole walls,
  so 128 of each wing side has no eaves (market_rich 3-5, waterfront_rich 2). Field: `eaves_walls` entries with a
  stretch, or eaves clipped where they enter another part.
- One roof over two parts: Keen Edge's upper storey is not convex (an L with a cut corner) under one hip roof; drawn as
  two hips meeting. Field: an outline part that may be concave, or `roof_with: <part>`.
- A parapet on some walls only: the roof walks of Keen Edge and the Hexes have a low wall (t14a05b top at 320) on
  their east edge only; not drawn. Field: `parapet_walls`.

**Walk** two of two. **Pictures**: plan views `output/studio_cal/mm8_out02/nw/pics/nw_original_before_after_x3.png`
(original, before, after), whole maps `original.png`, `before.png`, `after.png`.

## Roof words (2026-11-14, `openyamm-studio/build/oymap` of the nineteenth merge)

Backup `output/studio_cal/mm8_out02/roofwords_backup/`; edits by `output/studio_cal/mm8_out02/roofwords/edit.py`
(batch S4R's gate edits `keen2`, `parapet`, `wings3`); checks `roofwords/rw.sh`, `walk.sh`.
- Keen Edge's upper storey: p10 and p12 as one outline (an L with its corner cut) under one hip roof, eaves 64 and
  192 over wall 0 (the roof walk's corner) through `eaves_walls`. Gate: tops overlap 0.670 to 0.929.
- Keen Edge's roof walk: `parapet: 64` on p3 with `parapet_walls: [{wall: e, from: 256}, {wall: n, to: 96}]`, top
  t14a05b. Gate: tops 1.000.
- market_rich 3-5, waterfront_rich 2: the wings' eaves from the body's wall onward (`{wall: 0, to: 128}`, `{wall: 4,
  from: 448}`), the bodies' eaves stopped across the wings (wall 3, gap 192 to 1088). Gate: undersides 0.749 to 0.889.
- Not done: the Sanctum's peaked roof over its non-convex hall (three cones in the original; the concave outline takes
  hip or gable roofs, not a cone).

**Score** 92.19 to 92.20 % (buildings 90.46 to 90.52; other parts unchanged). **Pairs** 3 to 3 (1 as the
original). **Walk** two of two (136 steps). Installed in `rebuilds_root` with terrain materials. **Pictures** to take
(no display): Keen Edge's L roof and parapet, the Hostel's wing soffits, each beside the original.
