# Harmondale (7out02, mm7): rebuild notes

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
