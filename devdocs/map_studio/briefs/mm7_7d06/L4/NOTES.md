# Temple of the Moon (mm7 `7d06.blv`), L4 rebuild: notes

Round 3 of the self-correcting loop (2026-11-12), continuing the hand-drawn project of the brief's author (thirteen
review takes; see `devdocs/xeen/HANDOFF.md`, "The Temple of the Moon in detail"). The project stays hand-drawn:
every change to `rooms.yml`, `objects.yml` and `wiring.yml` was written by hand; scripts in
`output/studio_cal/mm7_7d06/tools/` only read the original's export and measure (face lists, floor and ceiling
rasters, plane and ramp fits, plan overlays). Scratch, pictures and repros are in `output/studio_cal/mm7_7d06/`;
the project as found is in `output/studio_cal/mm7_7d06/r3_backup/`.

## Where it stood (start of round 3)

- 45 rooms, 3 doors (both double doors drawn as one lifting t1d1 leaf, MM6's texture), 19 chests, 17 spawns,
  23 events; placeholders for 4 guards, floor items and the two fire-bolt emitters.
- `oymap compare`: **87.7 %** (distances 85.8 %, textures 93.9 %), 484 points, 3 without a floor in the rebuild.
- `compare.py`: 21 in / 13 near / 1 out.
- No playtest in L4. The author's 190-step playtest was in its session scratchpad
  (`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/59f2852b-.../scratchpad/play_ceil2/playtest.yml`, last run
  190 of 190 at 17:06); copied here as `playtest.yml`.

## Where it stands (end of round 3)

- 46 rooms, 5 door leaves (two double doors of two leaves each, the secret wall), 2 switches, 1 plate, 19 chests,
  17 spawns, 26 events; placeholders for the 4 guards and the floor items only.
- `oymap compare 7d06.blv --world mm7 --with <L4>`: **88.6 %** (distances 85.8 %, textures 95.9 %), 1 point without
  a floor in the rebuild.
- `compare.py`: 22 in / 12 near / 1 out (the out is still the smallest sector's area: the original has tiny sectors).
- Rooms reached: 46 of 46 (`audit --reach`: 39 with the doors as they start). `oymap solve` opens it in the
  original's order: step 1 both double doors, step 2 the secret lifting wall (the original: doors 5+6 and 7+8, then
  door 4).
- Playtest: **191 of 191 steps pass** (headless, from `output/studio_cal/mm7_7d06/run/`, log
  `playtest_l4_final.log`). Added to the author's walk: both leaves of the south door checked open, the north door
  opened by its button and both leaves checked, an 11 s wait in the fire lane.
- In-game pairs (`ingame_compare.py`, root `output/studio_cal/mm7_7d06/root`, sheets in
  `output/studio_cal/mm7_7d06/ingame_r3/diff/`): mean edge agreement 0.868 over 10 places I changed; nave to apse
  0.97, nave to stair arch 0.94, stair run 0.92, nave from apse 0.91, north passage 0.90, south aisle wall 0.87,
  east climb 0.84, alcove 0.80, south double door 0.79, west descent 0.74 (caves too dark to compare by edges).

Per sector (start, end; points): nave 13 (64) 0.937 to 0.955; north passage 18 (1) 0.764 to 0.944; south passage
20 (2) 0.869 to 0.974; aisles 14/15 0.920/0.933 to 0.955/0.973; stair 12 (18) 0.898 to 0.920; door halls 28/29
0.944/0.942 to 0.956/0.967; west descent 4 (26) 0.813 to 0.851; dormitory 25 0.958 to 0.969; caves 1, 2, 3, 5-11
within 0.005 of where they were (east climb 5 is still the worst at 0.710, north cavern 3 0.827, descent bend 1
0.782).

## What changed

Shape:
- **Dome** (`room:moon_nave` ceiling levels): four stacked levels on the measured profile instead of one straight
  frustum: the upright 'wall' collar +96 to +224, twb1a bands to 490 from the centre at +480, 264 at +736, and the
  'wall' cap of 96 at +800 (the original: 552 at +224, 490-506 at +480, 244-288 at +736, 96 at +800). The 12-gon is
  turned 15 degrees so the temple axis and the cross axis cross the middle of a side. The ribs are 12 raking beams 16
  deep under the three bands (the original's are flush 'wall' strips); the collar beams and the 160 block are gone.
- **Columns**: each of the six aisle columns has the original's 'wall' plinth (128 square, 24 high) and capital (128
  square, 16 high, under the ceiling) as platforms round the shaft.
- **Temple stair**: the flight's risers stand where the original's do (64 deep, x 128 to -384) with a level landing
  room at the foot, instead of 9 even steps of 75 over the whole length; the flight sides' tops are 'wall'
  (`top_surface`).
- **Dormitory alcove**: its barrel vault, measured (walls to -160, twb2 facets to -96 and -64, flat crown), as a
  whole-ceiling level with a second on its flat top.
- **West descent**: the ramp from the north cavern widened west to the original's wall (x -1664 at its foot); the
  rock island redrawn from the original's floor on a 64 grid (16 points). This removed two "no floor" points.
- **East climb**: plateau lowered from +160 to +130 (rise top, bend landing, upper ramp foot), the measured best fit
  (rise best top 110, bend best level 147, upper ramp best foot 137); the rise's inner corner moved 12 east so the
  slope lands on a whole unit. Same score as before (0.711 to 0.710).

Surfaces:
- Passages: the original's panel sequence on both side walls (twb3d niche, twb1, tws1a relief, twb1, twb3d; 256
  high) with twb2 above for the vault's lower facets, instead of a repeating twb3d band.
- Aisles: the two tws2c skull panels in the outer wall's dado.
- Temple stair run: four tws1a carved panels, tws1c and c1t1b1 at the cave mouth, and the tfs1 sill strip as a plate.
- Cave mouths: 24 `threshold`s of cfb1 (the 16-deep mouths had cwb1 rock on their floors).
- Inner rooms' doorways: twb1 reveal and 7tfb11 thresholds (the alcove arch, the lifting wall's slot, the study
  mouth), as the original's.

Objects and events:
- Double doors: `kind: slide_left, leaves: 2`, speed 50 (the original's two door records: 160 sideways each at 50),
  surfaces t1d1b (door hall side) and t1d1a (anteroom side), the original's MM7 textures.
- The two buttons beside the double doors (the original's doors 9 and 10, 7t1butt, event 2/3 on them): switches on
  the door halls' west walls that open both leaves, once.
- Fire-bolt crossfire: `evt:fire_bolts`, `trigger: timer, every: 5`, two `cast` effects with the original's points
  and arguments (event 51: Fire Bolt, mastery 2 = expert, level 1, from (-2619, 7850) to (-2619, 4008) and from
  (-2619, 4050) to (-2619, 7896), one unit above the floor). The built Lua's timer entry is the same as the
  original's (`intervalHalfMinutes = 5`). The emitter placeholders are gone.
- Aisle torches moved to the corner diagonals, where the original's are (within 25 of its points).

## Features that worked

`walls[].panels[]` (offset/length/height; 30 panels), whole-ceiling `ceiling_levels` with a level on a flat top
(alcove), stacked levels to any depth with `top_outline` (dome), `threshold`, platforms with `base` hanging under a
ceiling (capitals), flight `top_surface`, doors `slide_left` with `leaves: 2` and `back_surface`, switches with
`off`/`on` surfaces, `trigger: timer` with `cast`, a plate used for its surface, and `levels` against the room's
walls (already in the author's nave: the sunken floor runs to the east walls; that item of the open list is done).

## Refused or worse (with repros)

1. **An arched opening into a vault's end.** The passages' (and anteroom arms') vault is drawable, but the
   pointed arch at each end of a passage is then refused:
   `rooms.yml: openings[0].apex: a gabled opening's `apex` is the height of its point above the sill: at least 16
   above `height` (where its sides end) and at least 16 below the lower of the two ceilings`.
   The apex is checked against the room's ceiling (the vault's springing), not the upright end of the whole-ceiling
   level; only a rectangle may rise into that end. Repro: `output/studio_cal/mm7_7d06/repro/vault_arch_end/`
   (`oymap validate` it). So the passages keep a flat ceiling at -64 and the arms keep theirs.
2. **Climbing `path` on the wide caves**: valid once its bends were wide enough, but worse: east climb 87.7 to 87.3
   (sector 5 0.711 to 0.656), descent bend 87.7 to 86.9 (sector 1 0.779 to 0.561). Messages on the way: "the floor
   rises 51 over 160 units of path, and on the inside of the bend ... 1 for each unit: too steep", "the widened path
   crosses itself", and "have no facing parallel walls within 512 units" for a first leg that is not a Pythagorean
   direction. Not kept. Repro and both trials: `output/studio_cal/mm7_7d06/repro/climbing_path_wide_cave/`.
3. **Threshold on a wall without thickness** (north-east chamber to its neck): refused as documented ("the opening
   is in a wall without thickness ... drop `threshold`"); correct behaviour.

## Gaps still open, most harmful first

1. **Twisting and uneven cave floors** (the largest loss: sectors 3, 5, 1, 2 lose about 30 of the 55 point-units the
   map still loses). The north cavern's rise is one plane in the original (rms 9, rising 0.17 per unit toward 28
   degrees) whose high contour meets the temple-stair arm and the north-east chamber's mouth on a diagonal; the east
   climb turns while it climbs, with cross-slopes up to 180 over 600; the descent bend's turn and foot are one plane
   falling north-east; the south cavern's islands have sloped rock banks. Straight ramps need level ends, so every
   turn needs a level landing and every joint a wall where the original is open (the east climb's rise and upper
   ramp stand against each other along y -512). A climbing path has one width (item 2 above). Fields that would say
   it: an outline room whose floor is a plane in any direction with openings on its sloped sides, or floor heights
   at points (uneven floors), or a path whose width changes along it.
2. **Openings into vaults** (passages, anteroom arms, temple stair run): an arch may not rise into a whole-ceiling
   level's upright end, and no opening may rise above a leaning side, so the original's vaults that open in their
   own profile stay flat ceilings (passages -64, arms -32, stair run +128 with upright rock). Field: let `apex` and
   `height` rise into a whole-ceiling level's upright end (up to 16 under its top line) and under a leaning side.
3. **Placed monsters and floor items**: the four temple guards (the captain carries the Longbow, a scavenger-hunt
   item) and the floor items, among them the moon floor tile, the critical path's goal: the built map has no goal.
   Field: objects.yml actors (family, rank, level, carried item) and items (named or random by treasure level).
4. **Secret faces**: the library's lifting wall and the two rock-face chests are plain clickable faces; the original
   hides them behind perception (`mechanisms.secret_faces` 0 against 4). Field: `secret: true` on doors and chests.
5. **A door leaf's picture**: the original's double doors carry one round seal in four quarter textures (a/b upper,
   c/d lower, the right leaf mirrored, origin at the doorway's centre). Here both leaves of a door take one surface
   per side from the leaf's corner, so each shows a piece of one quarter. Field: a surface per leaf, a lower surface
   (or a split height), and the texture's origin at the doorway's centre.
6. **Curved dome and flush ribs**: the dome is three straight bands; the ribs are beams 16 deep, the original's are
   'wall' strips in the surface. Field: a curve on a ceiling level (a profile of heights and insets) and stripes on a
   leaning side.
7. **The west steps**: the original's five 128 treads rise 28 then 20 each to -436, the last riser stepping into the
   apse at its line; a flight must end on a floor of its own room, so the gallery keeps a 32 strip along the apse and
   the steps rise evenly. Field: a flight that ends at an opening onto the next room's floor; uneven rises.
8. **Zero-thickness walls**: the temple's arches into the passages, the stair's arch, the anterooms' mouths and the
   study's mouth are faces of one space in the original; here rooms stand 32 apart, so every such arch has a reveal.
   Field: a wall owned by one side only.

## Tool defects

- `oymap build` refuses a ramp joint with a face number only: `rooms.yml: the indoor compiler refused the lowered
  map: indoor native face is non-planar after coordinate quantization: 558`, no room named and no earlier warning
  (S3 says such faces are named first). The ramp alone builds; the face is at a joint. Repro:
  `output/studio_cal/mm7_7d06/repro/nonplanar_ramp_face_number/` (`oymap build ... --out .../build`).
- A plate whose corners stand exactly 16 from its room's walls is refused, though the message asks for "at least
  16"; 17 passes. Repro: `output/studio_cal/mm7_7d06/repro/plate_exactly_16/README.txt`.
- `oymap compare assets_dev/worlds/mm7/maps/7d06.blv --world mm7 ...` (the path form `export` takes) fails with
  "the world mm7 has no map assets_dev/worlds/mm7/maps/7d06.blv"; it takes the bare name `7d06.blv` only.
- `compare` points on the nave's rim edge (y 5120) take the sunken floor in the rebuild and the rim in the original
  (four of the 40 worst points, "the floor is 128 lower"), and vertical rays escape through the original's ceiling
  seams ("where the original has nothing within 4096"): sampling artefacts, both known.
- The headless run gives no sign whether a fire bolt flies or hits: no status line in 11 s in the lane (the scenario
  runner's `party()` shows no hit points).

## Unsure in the original

- Whether the fire bolts hurt a party standing in the lane: the casts start one unit above the floor; neither map was
  watched in a desktop run. The original's script also lists event 51 in `levitateTrapEvents`, which the engine
  reads only for pressure-plate faces (none carry event 51), so the build's lack of it should change nothing.
- The original stores the double doors open (state 2) with their leaves in the wall slots; I take the closed state
  from the playtest's and `solve`'s behaviour of the original (event 2/3 opens them).
- The 'wall' floor ring at +224 outside the dome's surface (radius 544 to 608) and the small 'wall' drum above the
  cap (+800 to +864): not visible from the floors; not drawn.

## Not done

- L3 is not updated (this round edits L4 only), so L3 and L4 geometry now differ: the dome, columns, stair landing,
  alcove vault, west descent ramp and island, and the east climb's heights are L4's alone.
- The anteroom arms' and the hidden passage's vaults (gap 2); the north cavern's rise (gap 1): every honest variant I
  measured either scored the same or put a wall where the original is open.

## Where I was tempted by score

Nowhere did a variant score higher against the measured shape. The east-climb plateau change was made for the
measured heights though it scores the same; the two climbing-path trials scored lower and were dropped for that and
because they narrowed the original's widening passages.

## Round four (2026-11-12, night)

Brief: `devdocs/map_studio/rounds/ROUND_FOUR.md`. The project as found is in `output/studio_cal/mm7_7d06/r4_backup/`;
measures are in `output/studio_cal/mm7_7d06/compare_r4_start/` and `compare_r4_end/`.

### Where it stands

| | start of round four | end |
|---|---|---|
| `oymap compare` score | 88.8 % | **94.3 %** |
| shape (distances) | 86.4 % | 93.1 % |
| textures | 96.1 % | 97.1 % |
| points without a floor in the rebuild | 3 | 0 |
| mean floor / ceiling difference | 6.5 / 30.6 | 1.7 / 13.2 |
| `compare.py` (in / near / out) | 22 / 12 / 1 | 31 / 3 / 1 |
| rooms | 46 | 37 |
| playtest | 191 of 191 | **257 of 257** (log `output/studio_cal/mm7_7d06/playtest_r4_end.log`) |

Rooms reached: 37 of 37 (`audit --reach`: 28 with the doors as they start). `oymap solve` opens it in three waves, the
original's order: 28 sectors on foot; both double doors (+7); the secret lifting wall (+2).

Per cave sector (start, end): north cavern 3 0.828 to 0.956; east climb 5 0.686 to 0.958; descent bend 1 0.734 to
0.901; high east pocket 6 0.836 to 0.917; northeast chamber 7 0.882 to 0.929; northeast pocket 8 0.877 to 0.942;
sinkhole 9 0.889 to 0.948; west neck 10 0.830 to 0.902; entry tunnel 11 0.865 to 0.912; west descent 4 0.851 to 0.873;
south cavern 2 0.891 to 0.897; cave mouth 30 0.796 to 0.775. Temple: passages 18/20 0.944/1.000 to 0.988/1.000,
anterooms 21/24 0.928/0.930 to 0.964/0.975, stair 12 0.922 to 0.933, nave 13 0.980 to 0.979.

In-game pairs (16 places changed this round, `output/studio_cal/mm7_7d06/ingame_r4/diff/`, cameras in
`output/studio_cal/mm7_7d06/shots_r4.yml`): mean edge agreement 0.834; stair run 0.94, climb turn 0.89, north cavern
0.84 to 0.89, passage vault 0.87, anteroom arm 0.81, west steps 0.82; the dark rock caves are near the noise floor of
the measure (entry tunnel 0.76). Looked at: the passage and arm vaults and their arches match the original's
profile; the cavern's rise and the stair mouth line up; the high pocket showed the shelf as cfb1 floor (fixed, below).

### What changed

Uneven floors and roofs (the caves). Each cave below is one room with `floor_points` / `ceiling_points` at the places
where the original's surface changes slope, measured from the original. The points were chosen with a helper,
`output/studio_cal/mm7_7d06/tools/fitsurf.py` (read-only: it picks, greedily and up to the procedure's budget, from the
original's own surface vertices and the room's corners those that bring a surface of flat triangles, triangulated
shortest lines first as the build does, closest to the original's; it writes nothing). Its proposals were written into
rooms.yml by small one-off Python edits (whole diff checked), then each room was built and measured with
`tools/surfdiff.py` (the rebuilt surface minus the original's on a grid) and `oymap compare`, and corrected by hand:
mouths given level sills, roof corners on a mouth raised so the mouth stays open, points that made slivers steeper than
allowed dropped, a few slope-break lines (`floor_lines`) added where the original's triangles run long. Because the
originals' cave surfaces are themselves flat triangles between few points, the points chosen are a subset of the
original's vertices; no room took all of them.

| Room (original sector) | outline | floor points (lines) | roof points | score | trial (traced) |
|---|---|---|---|---|---|
| north cavern (3), was 4 rooms | 35 | 23 (7) | 41 | 0.956 | 0.961 with 24 (5) and 103 |
| descent bend (1), was 4 rooms | 16 | 10 (1) | 25 | 0.901 | 0.894 with 11 (13) and 26 |
| east climb (5), was 5 rooms | 24 | 16 (5) | 37 | 0.958 | |
| west neck (10), was 2 rooms | 11 | 9 (1) | 17 | 0.902 | |
| high east pocket (6) | 18 | 6 (1) | 29 | 0.917 | |
| entry tunnel (11) | 20 | 14 | 10 (a ridge line) | 0.912 | |
| northeast chamber (7) | 18 | level | 36 | 0.929 | |
| northeast pocket (8) | 13 | level | 25 | 0.942 | |
| spider sinkhole (9) | 17 | level | 18 | 0.948 | |
| west descent (4) | 14 | level | 36 | 0.873 | |
| south cavern (2) | 31 | level | 39 | 0.897 | |

The trial (`output/studio_floor/temple/project2`) scored the map 91.1 %; with the same two caves this project stood at
91.1 % too (north cavern 0.959 against 0.961, bend 0.899 against 0.894) before the other caves were done. The north
cavern's floor rms against the original is 8.4 (trial 8.9), its roof's 32 (trial 24.5 with 103 points).

Sills the original rakes, now level: the north cavern's mouth to the west descent (-512), the bend's mouth to the
south cavern (-320; the original -256 to -320), the climb's mouth to the pocket (+352; the original +320 to +384). The
mouth from the climb into the high pocket moved to the original's line (y -1024); the pocket's floor rises from it to
+448. The pocket's rock shelf was first drawn as steep floor; it wore cfb1 where the original's leaning face is cwb1
rock, so its wall now stands upright halfway up the shelf (y -1984). The south cavern's southern island is redrawn from
the original's footprint at floor level (64 grid).

Vaults (arches into a vault's upright end now build):
- Both passages: the original's pointed twb2 vault (walls to -160, facets to -96 at 64 in, ridge -64), their four
  arches rising into the vault's ends to 336 (sides 256, shoulder on the facet line).
- Both anteroom arms: now rooms of their own (`room:anteroom_n_arm`, `room:anteroom_s_arm`, 16 short of the square),
  under the original's vault (walls to -160, facets to -96 at 96 in, ridge -64), arched at both ends (sides 256, point
  336).
- The temple stair run: the original's cwb1 rock vault (walls to 0, leaning in 128 to the crown at +128), its cave
  mouth the vault's upright end, the west leaning side stopping at y 5616 so the flight's mouth rises to +128 in an
  upright side (two outline points on the west wall; its panels are addressed as `wall: 5`). Its north end is upright
  where the original's leans (below). The north cavern's roof at the stair mouth came down to 0 so that the cavern's
  wall above the mouth does not stand in the stair's plane.

Objects and events:
- Fire bolts: the original's call is `evt.CastSpell(2, 2, 1, ...)`, which GrayFace's decompile reads as Mastery Novice,
  Skill 2 (`reference/mmext-scripts/Decompiled_Scripts/mm7/D06.lua` line 214), and the engine's `castEventSpell` takes
  (spell, skill level, mastery). Round three's notes had read it as expert, level 1. Now `mastery: normal, level: 2`;
  the built Lua is `evt.CastSpell(2, 2, 1, -2619, 7850, -415, -2619, 4008, -415)` and the second cast likewise, the same
  call as the original's (z in the project's frame, 320 lower), on the same 5 half-minute timer.
- The 12 bookcases have `random_items: 0`: each gives only its scroll or book, as the original's do. The cabinets keep
  their random items. The two rock-face chests and the lifting wall stay plain clickable faces.

West steps (target 4): the gallery is now two levels whose west diagonals reach the apse's line at the parapets, as the
original's; the sunken floor reaches the apse between them; the flight has the original's 5 treads (to_height -436)
and ends on a strip 16 deep at -436 against the apse's line, so the step up into the apse is the original's riser of
20 at x -2496. Still refused: a flight that ends at the opening onto the next room's floor (`to` on the room's wall with
`to_height` -436 or -416: "there is no floor at -416 at the flight's `to` point: the floors there are at -544 (the
room's floor and the tops of the levels, platforms and steps that hold the point or have it on their edge)"; repro
`output/studio_cal/mm7_7d06/repro/flight_to_opening/`). The stair arch onto the nave floor: the landing touching the
nave's east wall (no reveal) still builds only with the warning "opening open:temple_stair_nave is in a wall without
thickness and leaves wall round it: the two rooms' walls lie in one plane and one will show through the other; move
room:temple_stair_landing and room:moon_nave at least 16 apart there", so the 32 reveal stays (a wall owned by one side
only is still without a word).

Playtest: extended over everything this round changed: the east climb to the high pocket and back (asserting the
plateau at about +150 and the pocket floor at +448), the west descent, neck and sinkhole (floor -896), the northeast
chamber and pocket, the west steps' top tread (-436) and the south anteroom arm.

### New features that worked

`floor_points`, `floor_lines`, `ceiling_points`, `ceiling_lines` (a ridge line along the entry tunnel), rough walls
over an uneven floor, arches rising into the upright end of a whole-ceiling level (passages, arms), an opening rising
into an upright side of a vault (the flight's mouth in the stair run), a flight's `to_height`, `random_items: 0`,
`cast` with level and mastery in the engine's order. Tried and not kept: `steep_floor` for the pocket's rock shelf
(builds, but the shelf wears the floor's texture).

### Refused (exact messages, repros)

1. An arch as high as the vault's end (the original's passage and arm mouths are the vault's whole profile):
   "openings[0].apex: the gabled opening leaves the wall of room:passage: 64 units from its side it reaches 320 but the
   wall, with the upright end of the ceiling levels over it, stands to 320 there: lower `apex` or `height`, or make the
   opening narrower". Equal heights are refused; the arches stop 16 under the ridge (336). An apex of 351 with the
   shoulder 1 unit under the facet passes, which would leave a sliver of wall: not used. Repro
   `output/studio_cal/mm7_7d06/repro/vault_arch_full/`.
2. A cave mouth that follows an uneven roof: "openings[0].apex: the gabled opening leaves the wall of room:climb: 448
   units from its side it reaches 752 but the room's ceiling is at 576 there (a sloped ceiling) and the wall does not go
   on above it (only the upright end of a ceiling level without an `outline` does): keep `apex` at 208 or less". So
   every cave mouth is a rectangle up to the roof's lowest point over it, while the original's portals follow the roof
   (the climb's mouth into the pocket rises from +576 at its sides to +768). Repro
   `output/studio_cal/mm7_7d06/repro/cave_mouth_uneven_roof/`.
3. A flight ending on the next room's floor (above, item 4). Repro `output/studio_cal/mm7_7d06/repro/flight_to_opening/`.
4. An opening under a leaning side (the stair run's north hip over the flight's mouth): "openings[30].height: the
   opening reaches 128 but the lower ceiling of its two rooms is at 0 there (a sloped ceiling), and the wall of
   room:temple_stair ends at 0 there" (documented: only upright ends). The hip is drawn upright instead.

### Gaps still open, most harmful first

1. **The south cavern's islands** (sector 2, the largest loss left, 5.3 point-units): the original's islands stand on
   rock banks (the floor rises up to 200 against their south-west sides) and the roof comes down to them all round
   (to 0 and -64 within 128 of them, to -319 over the southern island's north overhang); a pillar stands upright from
   floor to roof. Field: a pillar with a sloping foot and head (a bank and a roof skirt), or floor and roof points on a
   pillar's outline.
2. **Cave mouths under uneven roofs** are rectangles to the roof's lowest point (refused item 2): every cave mouth
   here is lower at its middle than the original's. Field: an opening whose top follows the two rooms' roofs
   (`height: roof`).
3. **Raking sills** (three mouths here: west descent, bend to south cavern, climb to pocket): an opening needs a level
   sill. Field: a sill that follows the floor between two points of different height.
4. **Rock banks and shelves wear the floor's texture**: a steep triangle of an uneven floor takes the room's floor
   surface, where the original's leaning rock faces are cwb1 (the high pocket's shelf). Field: a surface for floor
   triangles steeper than a slope (`steep_surface`).
5. **The west descent** (sector 4, 0.873): its ramp is still a separate straight ramp room and its walls differ by
   100 to 500 in places (the island's ends, the ramp's sides); not redrawn this round.
6. **Placed monsters and floor items** (the four guards, the captain's longbow, the moon floor tile: the map's goal).
7. **The door seal across both leaves** (one picture in four quarters from the doorway's centre).
8. **Curved dome bands and flush ribs** (three straight bands; ribs as beams 16 deep).
9. **Walls without thickness on one side**: the stair arch's 32 reveal, the passages' 32 end walls, the anteroom arms'
   16 joints and their 32 mouths, the study mouth.
10. **An arch as high as a vault's end** (refused item 1): the passage and arm arches stop 16 under the ridge.
11. **A leaning side over an opening** (refused item 4): the stair run's north hip is upright. The hidden passage's
    last-leg vault (a lower vaulted ceiling over part of a path room) is not drawn.

### Tool defects

- `oymap solve` and `audit --reach` stop at a cave mouth 179 high (an uneven roof's corner on the mouth) that the
  headless game walks the party through: in round four's northeast chamber (roof point +51 over a floor at -128) the
  playtest walked into the chamber while `solve` said "stopped at the opening from sector 20 (room:ne_chamber_entry)
  into sector 19 (room:ne_chamber) at (1232, 3328, -128), face 2699: blocked by face 1339 (texture cwb1) at (1196,
  3328, 20)". The blocking face stands at +20, below the roof point. Repro:
  `oymap audit output/studio_cal/mm7_7d06/repro/low_mouth_solve --assets assets_dev --reach` ("blocked by face 12 ...
  at (-28, 0, 27)"). One of the two is wrong about the gap a party passes; the project now gives that mouth 256.
- A roof point on an opening's wall silently lowers the whole opening to it (the north cavern's mouth into the west
  descent ramp, the northeast pocket's mouth: both closed to a slit until found by `compare`). A warning when an
  opening ends lower than, say, 192 above its sill would have caught it.
- Fixed since round three: `oymap compare` takes the path form of a map; a non-flat face is named with its room.

### Where score and shape pulled apart

- No change was kept for its score alone. The pocket's rock shelf as steep floor was the closer surface on paper but
  wore the floor's texture where the original has a leaning cwb1 face; as an upright wall half way up it scores higher
  (sector 6 0.903 to 0.917), so here score and shape agreed.
- The stair mouth's roof at 0 instead of the stair's +128 lost 0.002 in the north cavern's sector; kept, because the
  cavern's wall would otherwise stand in the stair vault's plane.
- The west steps' change and the south island's redraw were measured from the original and scored the same; kept.

## Round five (2026-11-13, night)

Brief: `devdocs/map_studio/rounds/ROUND_FIVE.md` and the lead's task message. The project as found is in
`output/studio_cal/mm7_7d06/r5_backup/`; measures in `output/studio_cal/mm7_7d06/compare_r5_start/` and `compare_r5_end/`.
Scripted edits (each number measured from the original, whole diff checked) are in
`output/studio_cal/mm7_7d06/r5_edits/` (`mouths_edit.py`, `vaults_edit.py`, `shelf_edit.py`, `islands_edit.py`,
`west_ramp_edit.py`, `bookcases_edit.py`, `prune_edit.py`); read-only helpers added in `tools/`: `mouths.py` and
`mouthpts.py` (the original's portals beside the rebuild's, projected onto each room's wall), `zat.py` (the original's
floor or roof height at points), `prune.py` (each roof point's weight against the original's roof).

### Where it stands

| | start of round five | end |
|---|---|---|
| `oymap compare` score | 94.7 % | **95.2 %** |
| shape (distances) | 93.6 % | 94.4 % |
| textures | 97.1 % | 97.1 % |
| `compare.py` (in / near / out) | 31 / 3 / 1 | 26 / 2 / 7 (the doorway counts and widths: see tool defects) |
| rooms | 37 | 38 (the hidden passage's vaulted last leg) |
| build warnings | 7 placeholders + 3 answerable | 3 placeholders (nothing the vocabulary can say) |
| playtest | 257 of 257 | **195 of 195, four runs of four** (logs `play_r5_final_1.log` to `_4.log`) |

Rooms reached 38 of 38; `oymap solve` opens it in the original's order (28 on foot; both double doors; the secret wall).
Cave sectors (start, end): north cavern 3 0.957 to 0.968, ne chamber 7 0.937 to 0.958, descent bend 1 0.901 to 0.919,
entry tunnel 11 0.912 to 0.925, west neck 10 0.912 to 0.959, cave mouth 30 0.775 to 0.831, west descent 4 0.875 to 0.880,
stair 12 0.933 to 0.941, south cavern 2 0.897 to 0.898, high pocket 6 0.962 to 0.957 (below).

### Contents

- **Monsters: 4 of 4 placed** (objects.yml `monsters`), at the original's points, group 54: three temple guards
  (monster 403, Swordsman A) at (-5568, 4800) and (-5568, 5440) in the library and (-5120, 6784) in the dormitory, and
  the captain (404, Swordsman B) at (-5568, 6784). Their records carry no Aggressor bit and their kind's table makes
  them peaceful to the party (the game's own reading: `clear_hostiles` never touches them), so `hostile` is left out,
  as the original's; no `hp` or `name`: the original's are the kind's (40 and 79 hit points, unique name 0, so the game
  shows "Swordsman" and "Guard"). **What the record cannot hold:** the captain's carried item, 845 (the Longbow, a
  scavenger hunt item) in the actor's `carried_item_id`: placeholder `ph:captain_longbow`; field `monsters[].carries`.
- **Lying items: 1 of 1 placed**: the moon floor tile (1438) at (-4160, 6336) in the hidden study, the original's only
  sprite object. It is the map's goal; nothing in the original's script tests or sets anything when it is taken (the
  hunt's quest bit 516 is set and cleared on Emerald Island), so no event goes with it. The playtest ends by taking it.
- **Random floor items: 0 of 7**: the original's item spawn points (type 2: three in the high east pocket of levels 1,
  2, 1 and four in the northeast pocket of level 1) have no word: `items` takes a fixed item and `spawns` only monster
  slots. Placeholders `ph:floor_items_high_east` and `ph:floor_items_ne_pocket` give their points and levels; field
  `spawns[].item_level` (or `items[].treasure_level`).
- **Monster spawns: 17 of 17** now at the original's points and slots (five stood 30 to 920 away: the two nave bat
  groups, the south cavern's bats, the northeast chamber's rats and the pockets'); every spawn now stands at the
  original's x and y exactly.
- **Chests: 7 of 7 with the original's contents as far as a chest can say them** (the original's chest records 1 to 7;
  record 8 is on no face). The Wealthy Hat (1433) in the hat cabinet as the original's record 5; the random rolls by
  count and level: records 1 to 4 are levels (2, 1, 1), (2, 1, 1, 1), (2, 1, 1), (3, 2, 1), the hat cabinet (3, 2, 1),
  the sinkhole panel (3, 3, 1) and the south cavern panel (2, 2, 1) **and trapped** (its flag 1; now `trap_level: 1`).
  A chest takes one `treasure_level` for all its rolls, so each keeps the level it had (the lowest of its rolls for the
  cabinets, the highest for the panels). The lowering reads `random_levels` (one level per roll, written as the chest
  record), but the schema does not have the key, so `validate` refuses it: tool defects below.
- **Bookcases: 15 of 15 as the original's** (events 29 to 43): each searchable face is a clicked block
  (`platform:bookcase_l01` to `l10` in the library, `s1` to `s5` in the study, a jutting case two blocks back to back,
  one per face) with a `script` event: unless its map variable is set, set it and give the face's scroll or book. The
  12 bookcase chests are gone (chests 19 to 7).

### Events (the original's against the rebuild's; `oymap flow` both)

| original | rebuild | |
|---|---|---|
| 1: doors 1 to 3 toggle | none | dead in the original (no such doors, no face carries it) |
| 2, 3: door 9/10 pressed in, doors 5+6 / 7+8 open (on the leaves and the buttons) | `evt:door_double_s`/`_n` on the leaves, `evt:button_s`/`_n` on the switches | same; the button is a flat switch whose face changes, not a block that moves in 15 |
| 4: door 4 open (title Door, secret faces) | `evt:secret_wall`, door `secret: true`, title Door | same (secret now) |
| 21 to 25: chests 1 to 5 | `evt:chest_cabinet_1` to `_4`, `evt:chest_cabinet_hat` | same, rolls of one level per chest (above) |
| 26, 27: chests 6, 7 on secret rock faces | `evt:chest_rock_sinkhole`, `evt:chest_rock_south_cavern` | differs: a thin box against the wall, not a secret face of it |
| 28: chest 8 | none | on no face in the original |
| 29 to 43: bookcases, once each by map variable | `evt:bookcase_*` | same (the build's `GiveItem(id)` for the original's `AddValue(InventoryItem(id))`) |
| 51: fire bolts on a 5 half-minute timer | `evt:fire_bolts` | same call |
| 100: leave to 7out01 | `evt:exit` | same |

Of the original's 27 live events, 25 match and 2 differ (the rock-face chests).

### Playtest

195 steps, four runs of four pass (and a fifth after the last objects change). Reordered so that it ends at the goal:
the caves, the nave and the fire lane as before; then the north wing (the button opens both leaves; the dormitory's
guard and captain are passed at their posts and asserted alive and unharmed, a `lua_event` with
`evt.CheckMonstersKilled`); then the south wing: both leaves of the south door, the library's guards (alive), the
south case's two faces searched (one Torch Light scroll each, nothing on a second search), the secret wall lifted,
the study's Torch Light book taken once, and **the moon floor tile picked up from the floor** (`pick_up`, then
`has_item(1438)`). The walk back and the exit are no longer in it (the brief asks the walk to end at the goal). A
first version turned the guards hostile (`evt.SetMonGroupBit(54, MonsterBits.Hostile, 1)` in a `lua_event`) to fight
them as a player wanting the Longbow would; the game never applied it (tool defects).

### What changed (shape)

- **Cave mouths from the original's portals** (target 3): roof points on each shared wall at the original portal's
  corners (projected onto both rooms' walls), so `height: full` follows them and every mouth has the original's
  shouldered profile instead of a rectangle (e.g. into the climb: sides to -64, shoulders to +64, flat; the exit
  mouth's arch to +448; the pocket mouth +576, +704, +768, +640). Raking sills: the climb into the pocket (+320 to
  +384), the bend into the south cavern (-256 to -320), the north cavern into the west descent (-576 to -512), the neck
  into the sinkhole (-896 to -832) and the neck into the northeast pocket (-64, was 0). The cave mouth room and the
  northeast chamber's entry have roofs by points (9 and 7) instead of sloped flat ceilings. Ten of twelve mouths now
  match the original's profile point for point (`tools/mouths.py`); the two left are the entry tunnel's and the west
  neck's, whose lower corner is a steep bank (below).
- **Vaults** (target 5): the eight vault-end mouths (both passages at both ends, both anteroom arms at both ends) are
  the vault's whole profile (`trim_to_wall: true, height: full`), no longer 16 under the ridge; the temple stair's west
  side leans to y 5760 as the original's and the flight's mouth under it is cut along the lean (`trim_to_wall`); the
  stair's cave mouth is the stair vault's profile (+128 at the shoulders) and its "wall without thickness" warning is
  gone; the hidden passage is the original's L as an outline, and its last leg a room of its own under the original's
  pointed twb2 vault (walls to -160, facets -96, ridge -64), open by its whole profile to the passage and the study.
- **Steep rock wears cwb1** (target 4): `floor_surfaces: [{steeper_than: 1.0, surface: cwb1}]` (the original's cave
  floors: cfb1 all under 0.8, cwb1 all over 1.4). The high pocket's shelf is the bank it is: the south wall back on the
  bank's top line, floor points on its top and foot. Two compromises the rules force: its foot stands 16 further out
  (y -1904 and -1900 for -1920) because the build takes at most 2 for each unit of run as floor and the original's bank
  rises 2.24; its top is +688, 16 under the roof, where the original's meets the roof at +704. Sector 6 fell 0.962 to
  0.957 with it; kept, because it is the original's form where the upright wall half way up was not.
- **South cavern islands** (target 6): little. The original's north island stands on banks that rise 2.0 to 2.75 for
  each unit of run onto upright feet (a corner at (1280, 768) stands upright from -320 to -64 between two banks), which
  floor points cannot hold; the west bank alone is built (a point at the island's corner, +240 over 136, cwb1), and the
  bend's mouth now rakes as the original's (f175). The east bank needs a point on the island's tip whose triangle
  inside the island the build refuses as too steep (tool defect). The roof's skirt round the islands is not drawn: the
  room was already over the point budget.
- **West descent** (target 7): the ramp room by points from the original's faces f230 to f233 (level along the
  descent, rising to -576 and -512 at its north corners) and its roof by six points (-380 to -260, the mouth's line),
  instead of a straight ramp under a flat ceiling. Its walls were checked against the original on a plan overlay
  (`ov_r5_west.png`): within one or two rock bumps of it; not redrawn. Sector 4 0.875 to 0.880; its worst points are
  rays along the ramp's west wall, which runs straight where the original's bends.
- **Warnings answered**: the hidden passage's wall pair (gone with the outline), the stair mouth's wall without
  thickness (gone with the profile mouth), the stair sill plate that ran no event (now a `floor_surfaces` region of
  tfs1 between a floor line and the north wall, the plate removed).
- **Point budget**: the north cavern's roof has 44 points (round four 41; +5 on mouths, 4 interior points dropped by
  `tools/prune.py`; dropping 8 lowered sector 3 to 0.915, so 44 stays), the south cavern's 40 (47 with the mouths' 8,
  7 interior points dropped). No room takes the original's points one for one.

### New words: worked and refused

Worked: `monsters` (with `group`), `items`, `doors[].secret`, platforms with an `id` as click sources (15),
`trim_to_wall` with `height: full` (8 vault ends, the flight's mouth under the lean, the stair mouth, the hidden vault),
`height: full` following roof points along a wall (12 cave mouths in strips), raking sills by floor points on both
rooms,
`floor_surfaces` by `steeper_than` and by `at` (the stair sill), `steep_floor`, `trap_level`, `lua_event` with
`evt.CheckMonstersKilled` in the playtest, `pick_up`.

Refused (repros under `output/studio_cal/mm7_7d06/repro/`):
1. A bank steeper than 2 for each unit of run (the original's are 2.0 to 3.0): "the floor of room:high_east_pocket rises
   2.04 for each unit of run ... At most 2 for each unit of run can be built as a floor". Documented; the banks moved
   out 16.
2. A floor point on two corners of a rock island: the triangle inside the island, never built, is refused as too steep
   ("rises 3.64 for each unit of run between [384, 512] at 240, [480, 416] at 0, [416, 640] at 0"). Repro
   `pillar_inside_steep/` (`oymap validate` it). A defect, I believe: the island's inside is no floor.
3. A floor point where the bank meets the roof: "at [3072, -2048] the ceiling ... is at 704 and its floor at 704: the
   ceiling stays at least 16 above the floor everywhere". Documented; the top is 16 lower.
4. `random_levels` on a chest: "objects.yml: chests[4].random_levels: unknown key" (the lowering reads the key,
   `core/IndoorLowering.cpp` 10944, and writes a chest record with one level per roll, but the schema lacks it).
   Repro `chest_random_levels_schema/`.
5. A negative item id in a chest's `items` (the original's own code for a random item of a level) passes `validate`
   and then fails the build: "the scene file the build wrote is not accepted: could not parse item-source field
   item_id: yaml-cpp: error at line 275, column 18: bad conversion". Repro `chest_random_levels/` (`oymap build` it).
6. A hidden-passage `path` whose last leg (128) is shorter than its width: "the widened path crosses itself"
   (documented; the room is an outline now).

### Compromises undone and left

Undone: the cave mouths as rectangles to the roof's lowest point; the three level sills (and two more found raking in
the original); the arches 16 under the ridge (8); the stair run's upright north hip; the hidden passage's flat last leg;
the high pocket's shelf as an upright wall; the stair sill plate; placeholders for the guards and the moon tile; the
bookcases as chests.

Left: the bank feet 16 out and tops 16 under the roof (rules); one treasure level per chest; the rock-face chests not
secret and not faces; the captain's Longbow; the random floor items; the walls 16 to 32 thick where the original's
have none (the passage and arm joints, the stair arch's reveal, the study mouth, now also the hidden vault's ends).

### Gaps still open, most harmful first

1. **The captain's carried Longbow** (a scavenger hunt item; the rebuild cannot give it). Field: `monsters[].carries`.
2. **Item spawn points**: 7 random floor items in the two pockets. Field: `spawns[].item_level` or `items[].treasure_level`.
3. **The south cavern's islands** (sector 2, 5.1 point-units still): banks steeper than 2 onto upright feet and the
   roof's skirt round them. Fields: a pillar with a sloping foot (a bank as part of the island), a floor point allowed
   on an island's corner without the inside triangle counted; and the roof's points over budget.
4. **Rock-face chests** (two): a chest that is a face of the wall and secret. Fields: `chests[].secret`, a wall panel
   as a chest's face (`chests[].panel`).
5. **One treasure level per chest**: `random_levels` into the schema (the lowering already has it).
6. **The west descent's ramp side** (sector 4, 0.880): its west wall bends where the rebuild's is straight; nearest to
   a redraw, not a missing word.
7. The door seal across both leaves; the curved dome and flush ribs; walls without thickness on one side (as before).

### Tool defects

- **Scenario `lua_event` drops world effects**: `evt.SetMonGroupBit(54, MonsterBits.Hostile, 1)` in a `lua_event` step
  passes, but the group never turns (`clear_hostiles` kills nobody, `killed=0` in `play_r5_b.log`):
  `ScenarioRuntimeDriver::runLuaEvent` runs the event without `applyEventRuntimeState`, and the next real event clears
  the pending requests (`EventRuntime.cpp` 4749). Shown by the playtest's second version, log `output/studio_cal/mm7_7d06/play_r5_b.log`.
- `random_levels` is read by the lowering but not in the schema (refused item 4); a negative item id passes `validate`
  and breaks the build with a yaml-cpp message (refused item 5).
- Steepness counted on floor triangles inside a rock island (refused item 2).
- `calibration/compare.py` counts each strip of a shaped mouth as a doorway: `scale.doorway_width.count` 95 against the
  original's 28, median 128 against 512, so the doorway lines turned "out" when the mouths became the original's shape.
- `ingame_compare.py`: "rebuilt: no floor under exit-mouth at -1170, -3650; skipped" for a point 12 inside the entry
  tunnel's wall line where the original has floor.

### Pictures

`output/studio_cal/mm7_7d06/ingame_r5/diff/` (cameras `shots_r5.yml`; taken before the last roof pruning, which
touched only interior roof points away from the cameras): mean edge agreement 0.816 over 17 pairs; stair mouth 0.89,
library guards 0.86 (the two guards and the cases where the original's stand), the hidden vault 0.75 (its profile is
the original's; the difference is the bands on its side walls). The caves are near the measure's noise floor; the
mouths' shouldered tops read alike in both. One thin dark line under the northeast pocket neck's roof in the rebuild
(`07-ne-pocket-neck.png`, top right): a crack between roof triangles, not traced.

### Where score and shape pulled apart

- The high pocket's bank (sector 6, 0.962 to 0.957): kept for the original's form.
- The south cavern's banks: every fuller attempt (four and three bank tops) lowered sector 2 (0.886, 0.893) because the
  original's upright island corner cannot be said and the floor round it rose too; only the one honest bank is kept.
- Roof points dropped for the budget cost 0.001 (north cavern 0.972 to 0.968 at 44 points; 40 points cost 0.05 and
  was not done).

## Round six (2026-11-13)

Brief: `devdocs/map_studio/rounds/ROUND_FIVE.md` (rules) and the lead's round-six task message. The project as found is
in `output/studio_cal/mm7_7d06/r6_backup/`; measures in `compare_r6_start/` and `compare_r6_end/`. Scripted edits and
read-only helpers of this round are in `output/studio_cal/mm7_7d06/r6_edits/`: `islands6.py` (the islands' outlines and
bank points, numbers from the original's faces, whole diff checked), `scfit.py`/`scfit2.py`/`scprune.py` (read-only
fits of the south cavern's roof: scratch builds measured against the original on a 64 grid; logs in `r6_fit/`),
`apply_roof.py` and `trial.sh` (a fit's points into a scratch copy, compared). Every other edit was by hand.

### Where it stands

| | start of round six | end |
|---|---|---|
| `oymap compare` score | 95.2 % | **95.9 %** |
| shape (distances) | 94.4 % | 95.2 % |
| textures | 97.1 % | 97.7 % |
| placeholders | 3 | **0** |
| build warnings | 0 | 0 (one new opening-pair warning answered with `from_wall`/`to_wall`) |
| playtest | 195 steps | **211 of 211, four runs of four** (`play_r6_end_1.log` to `_4.log`) |

Sectors (start, end): south cavern 2 0.898 to 0.929, west descent 4 0.880 to 0.928, sinkhole 9 0.950 to 0.964, east
climb 5 0.968 to 0.971, west neck 10 0.959 to 0.963; the rest within 0.002. `oymap solve`: 28 on foot; both double doors
(+7); the secret wall (+3); 38 of 38.

### Contents (target 1)

- The captain carries the Longbow: `monsters[].carries: longbow` (845). The built actor record is the original's in
  every field the game reads (monster 404, 459, 79 hit points, carried item 845, group 54).
- The seven random floor items are item spawn points (`spawns[]`, `kind: item`) at the original's points and levels:
  high east pocket 6 (level 1), 10 (2), 16 (1); northeast pocket 7, 13, 20, 22 (all 1). The built spawn records match
  the original's (type 2, index = level); the original's group 51 is used by no script.
- Every chest's rolls are at the original's levels (`random_levels`): records 1 to 7 are written exactly as the
  original's item lists (-2 -1 -1; -2 -1 -1 -1; -2 -1 -1; -3 -2 -1; 1433 -3 -2 -1; -3 -3 -1; -2 -2 -1, the last trapped).
- No placeholder is left.

### Behaviour

Events, the original's 27 live ones against the rebuild's: **27 match**. New this round: events 26 and 27 (the rock-face
chests) are clicks on a cws1d face of the cave wall that open the chest, as the original's (round five: a thin box).
What still differs: the faces carry no secret flag (the original's pulse red for a party that finds secrets: picture
`ingame_r6/diff/15-bay-rock-chest.png`), and the buttons 2/3 are flat switches, not blocks that press in 15.

Playtest (211 steps, four runs of four): as round five, plus the bay's rock-face chest (event 22, trapped; the immortal
party opens it on the second click if the trap goes off) and the sinkhole's (event 21), and in the dormitory the captain
killed for his Longbow (`combat_loot` with `expected_item_id: 845`, then `has_item(845)`). Killing him turns group 54
on the party, as in the original; the walk then fights the dormitory's guard and the library's two, and asserts that
the whole group is dead after the library (round five asserted them alive, since nobody touched the captain). The item
spawns are not asserted: by the game's rule one roll in five gives nothing.

### What changed

- **Door seal** (target 2): both double doors fold (`fold: true`), as the original's leaves do (only their free edges
  move, 160 of 192, shrinking into the wall's slot), and carry `pictures` in two rows of two: t1d1a, t1d1b over t1d1c,
  t1d1d, meeting at the doorway's centre, reading the same from both rooms (no `back_pictures`). No `mirror`: the
  original's four quarters are four bitmaps and none of its faces carries a flip flag; besides, `mirror` is refused on a
  folding leaf (repro below). Game pictures, the original left: shut `doors_r6/pair_01-s-door-shut.png`, from the
  anteroom `pair_03-n-door-shut-from-anteroom.png`, opening `pair_04-s-door-opening.png`, open `pair_05-s-door-open.png`
  (tour `doors_r6/tour_*.yml`, event 24 here, the original's event 2). The seal reads as the original's, shut and while
  the leaves fold. What differs: the original's doorway is 384 wide with its four corners filled by 128 x 64 triangles
  (an octagonal frame round the leaves, f1569, f1571, f1574, f1575); here the doorway is a 320 rectangle (a door leaf
  needs a rectangle, and a wall panel is a rectangle).
- **South cavern's islands** (target 3): the northern island is the original's island top at -64 (13 corners), upright
  on its north side, on banks on its west, south and east (floor points on the bank tops at -80 and on the feet at -320;
  the east bank, refused in round five, now builds). Its upright corner at (1280, 768) between two banks is a bank top
  here (a point has one height), and the feet stand where no triangle rises more than 2 (the original's banks rise 1.5
  to 2.8). The island's upright corners take floor points at -320, because a pillar's corner takes the height of the
  floor surface drawn through it (without them the north side rose to -140). The southern island leans out by up to
  128: its outline is halfway between foot and top. **The roof's skirt**: the roof comes down to -64 on both islands'
  20 outer corners, with `ceiling_lines` round each island's hull so that the islands' insides take no slope from
  elsewhere (the 5 inner corners then lie at -64 too, checked in the export). Point budget: the roof has 44 points (round five 40): 13 kept from round five (the mouths' and walls' 11 that are not -64, and the +64 points (2080, -608), (1356, 102)), the islands' 20 outer corners at -64, 9 +64 points chosen by a forward fit among the original's own +64 roof vertices ((1664, 768), (1152, -640), (1536, 1280), (1024, 1024), (768, 1280), (960, 1600), (1280, 1408), (1664, -384), (1280, -1152); `r6_fit/fwd_hullp.log`), and the bay wall's two corners (2560, -64) and (2432, 0) at -64 (the original's wall top there, so that the chest panel is the original's 256 high). Removed to make room: 27 of round five's points, the -64 wall corners (1088, 1920), (768, 640), (1152, 512), (512, -256), (384, -128), (1920, -1408), (2432, -768), (2528, -64), (1888, 224), (2016, 1088), (1536, -384), (144, -128) and the helpers (1536, -256), (1152, 1472), (1920, -512), (1280, 512), (1024, -384), (1408, -256), (768, -512), (512, -384), (1088, 1600), (2048, 896), (492, -896), (256, -768), (1664, 128), (640, -896), (1920, 384). So the room's base is now the plateau (+64) and several outer walls stand 384 high where the original's are 256 (its wall skirts): the measure prefers a roof without island skirts (s2 0.929 with the best 44 points of a fit that leaves the islands' corners at +5 to +64, against 0.917 skirted at the same count before the banks' move below); I kept the skirt, the original's shape the task asks for. The floor has 19 points, the outline 34.
- **The south loop's banks**: its south walls stand on the middle line of the original's steep banks (f29 to f35,
  rising 4 for each unit from -320 to -64), as the islands' upright sides stand for their leaning ones: (640, -992),
  (896, -1248), (1600, -1504) for (640, -960), (960, -1248), (1600, -1472). Sector 2 0.921 to 0.930.
- **Rock-face chests and the lifting wall** (target 4): the lifting wall was already `secret: true` (round five). The
  chests are now wall panels with ids (cws1d, the original's faces f2236 and f39) wired as `script` events with
  `open_chest`; the chests have no box (`box_of`). For the bay's chest the bay's walls were redrawn on the original's
  corners ((2560, -512) to (1792, 128)), so that its chest face is a wall of its own.
- **Carved rock**: the original's other cws1 and cws1a faces that lie on cave walls are panels now: f32, f42, f44 (south
  cavern), f144 (sinkhole), f108 (north cavern), f65/f2609 (east climb). Textures 97.3 to 97.7.
- **West descent ramp** (target 5): its west wall bends at (-1408, 1152) as the original's (f25, f26), from the
  descent's north wall at x -1536; the roof gets the wall top there (-384). Sector 4 0.880 to 0.907. Its island's west
  tip moved 100 east, to the middle of the original's leaning end (f157, f1430): 0.907 to 0.928.

### Refused or not said (repros under `output/studio_cal/mm7_7d06/repro/`)

1. `mirror` on a folding leaf: "objects.yml: doors[0].pictures: `mirror` turns over a picture that is stretched over its
   part of the door; door:seal folds, so its pictures lie at their own size as the game lays them. Drop `mirror` (and
   name a texture that is drawn mirrored), or drop `fold`". Documented; this map needs none. Repro `door_fold_mirror/`.
2. `pillar_inside_steep/` no longer reports the island's inside; it now reports a real floor triangle of the repro
   (2.07), correctly.
3. Not refused, but no word: a chest opened from a wall panel must still name some box (`box_of`), here
   chest:cabinet_hat, whose own event never opens it. A field `chests[].panel` (or `box_of` left out when an
   `open_chest` names it) would say it straight.

### Gaps still open, most harmful first

1. **Secret faces on panels**: the rock-face chests do not pulse for a perceptive party (field `panels[].secret`).
2. **The island's carvings**: the original's cws1a/cws1 faces on the islands (f87, f89, f96, f97, f100, f2486, f2489,
   f2490, f135, f153) cannot be said: a pillar takes one surface (field: `pillars[].sides` or panels on a pillar).
3. **Wall skirts of the south cavern**: within 44 roof points the outer walls of the bay and the northern loop stand
   384 high where the original's roof comes down to 256 (field: a roof that comes down along the walls by a skirt width,
   or more points).
4. **The double doors' octagonal frame** (384 wide, corners filled by triangles; here a 320 rectangle). Field: a
   chamfer on a door's opening, or a triangular panel.
5. **Upright edges between banks** (the north island's corner at (1280, 768)): a floor by points has one height at a
   point. Field: a bank that is part of a pillar (a sloping foot).
6. Curved dome and flush ribs; walls without thickness on one side (as before).

### Pictures

`output/studio_cal/mm7_7d06/ingame_r6/` (cameras `shots_r6.yml`: the lead's ten from `output/studio_temple/shots.yml`
and ten where this round changed things; `bright/` holds the same pairs lifted for the eye, original left): mean edge
agreement 0.812. Best: `diff/08-nave-to-apse.png` 0.98, `diff/19-door-s-seal.png` 0.91 (and `doors_r6/pair_04-s-door-
opening.png`), `bright/13-island-south-north-side.png` (the roof flaring onto the island as the original's). Worst:
`diff/03-south-cavern.png` 0.56 (the lead's camera stands against a rock face in both maps: texture noise only),
`diff/17-west-ramp-bend.png` 0.73 (the descent's roof crease differs). Looked at: the rock-face chests sit where the
original's do (one grate each; the original's bay chest shows its red secret tint); the islands' banks and skirts read
as the original's; the doors' seal is whole across both leaves.

### Where score and shape pulled apart

- The south cavern's roof: a roof without the islands' skirts measures better (s2 0.929 against 0.917 at 44 points);
  the skirted roof is kept, the original's shape. With the banks' middle line and the bay's corner the room ends at
  0.929.
- The north island's corner (1280, 768) as a bank top raises the floor beside it where the original's is -320 (+176
  at (1316, 734)); kept, because the banks either side are the original's.

## Ninth merge lines (2026-11-13, afternoon)

Copy before: `output/studio_cal/mm7_7d06/m9_backup/`.

- **The rock-face chests**: `secret: true` on panel:rock_chest_south_cavern and panel:rock_chest_sinkhole (the
  original's faces 39 and 2236 carry the secret flag; with the library's secret wall the build now has the original's
  four secret faces). Picture `output/studio_cal/mm7_7d06/m9_pics/sheets/02-rock-chest-sinkhole.png` (as the original;
  the camera stands 320 higher in the original: `compare`'s vertical offset).
- **Playtest made independent of chest rolls**: the library step (its scroll) and the study bookcase step (its book)
  each failed once in four runs with the packs full of what the chests rolled (about 35 items): the item stayed on the
  cursor and was counted 0. The packs are now emptied before both, as the Lincoln's and the Hive's playtests do (the
  log line "packs before the library" shows them). Eight of eight, then four of four after the cabinets' change.
- **Audit, squashed pictures**: the cabinets' tops took 7t1cab stretched (4 to 1): now `top_surface` 7t1cabs 64x128,
  the original's (faces 1960 to 1964). Left, the studio's: the cabinets' and bookcases' ends are always stretched to
  fit (7t1cabs 0.5 down, 7t1books2 2 across; the original lays both 1:1; `fit: false` is ignored on `end_surface`);
  the exit panel 7solid01 (one dark colour, stretched); cwb1/cfb1/twb3d/wall on rough and sloped faces (laid from z).
  Click.silent 17 (the original 30).
- **Scores**: 95.9 % before and after (sector-weighted 95.921 both), offset agreement 0.447 both.

## Round seven (2026-11-13, evening)

The project as found is in `output/studio_cal/mm7_7d06/r7_backup/`; measures in `compare_r7_start/` and
`compare_r7_end/`. Scripted edits (numbers from the original's export, whole diffs checked) and read-only helpers are in
`output/studio_cal/mm7_7d06/r7_edits/`: `split_south.py`, `split_south_loop.py`, `split_north_loop.py`,
`split_north_cavern.py` (rooms of one space), `cave_mouth.py`, `stair_vault.py`, `thresholds.py`, `west_island.py`,
`notes7.py`/`notes7b.py` (notes only); helpers `prune7.py` (backward choice of roof points by the roof's rms against
the original's, scratch builds), `fullroof.py`/`fixsteep.py` (candidate lists), `assemble.py`/`replay.py`, `walldev.py`
(the original's walls against an outline), `zgrid.py`, `pts.py`/`cats.py`/`offs.py` (reading `points.json`). Work
copy `r7_work/`, trials `r7_t_*`, fits `r7_prune/`.

### Where it stands

| | start of round seven | end |
|---|---|---|
| `oymap compare` | 95.9 % (95.92) | **97.5 %** (97.48) |
| distances / textures | 95.2 % / 97.7 % | 97.2 % / 98.2 % |
| offset agreement (not in the score) | 0.447 | 0.460 |
| rooms | 38 | 42 (the south cavern 4 rooms, the north cavern 2) |
| `audit --strict --original 7d06.blv` | 0 pairs | 0 pairs in one plane (the original has 2, its secret wall) |
| playtest | 211 steps, 4 of 4 | 213 steps, **4 of 4** (`play_r7_end_1.log` to `_4.log`) |

Sectors (start, end): south cavern 2 0.929 to 0.980, temple stair 12 0.941 to 0.992, cave mouth 30 0.831 to 0.962, west
descent 4 0.928 to 0.961, east climb 5 0.971 to 0.991, entry tunnel 11 0.925 to 0.944, descent bend 1 0.920 to 0.947,
north cavern 3 0.968 to 0.976, high pocket 6 0.958 to 0.975, ne pocket 8 0.959 to 0.980, west neck 10 0.963 to 0.974.
`oymap solve`: 32 on foot, both double doors (+7), the secret wall (+3): 42 of 42. Events: unchanged (the built Lua is
byte for byte round six's); 27 of 27 as the original's.

### What changed and why (each the original's shape, measured)

1. **No `rough` walls** (95.9 to 96.5). `walldev.py` measured the original's cave walls against each outline: median
   0 off in every cave; they run straight between corners, which the outlines take. `rough` only pushes walls inward
   (up to 40), so it made every cave narrower than the original's. Removed from all 11 caves. The entry tunnel alone
   fell (its original walls stand about 13 inside its outline); its sector came back with the cave mouth (below).
2. **South cavern roof** (target 1; s2 0.946 to 0.980): base -64 (the original's walls and island tops: its 67 roof
   vertices at -64) and the original's own +64 vertices (the plateau's edge: 87) as points, so the outer walls are
   256 high under the original's skirt. That is about 100 points, so the sector is now four rooms of one space
   (the procedure: a room that needs more is several rooms): split at the waist on the original's line y 256 between its
   wall corners f10/f45, and each loop cut from its island to the outer wall (two cuts each). The rooms touch along the
   cuts and are open over the whole line (no wall, no reveal; builds with no warning), with the same floor and roof
   points on each cut. Roof points per room 25, 30, 25, 28; the +64 vertices taken one for one.
3. **The islands' carved faces** (round six gap 2, partly): with each loop cut round its island, the islands' sides
   are room walls; f96 (cws1), f97/f2489/f2490, f100/f2486 (south island) and f87, f89 (north island) are wall panels.
   Texture pairs cws1a against cwb1 went from 44 rays to 0.
4. **Cave mouth** (30: 0.831 to 0.962; 11 to 0.944): the original's floor outline with its pinch (x -1024), floor by the
   original's 7 heights, roof by 17 points; no longer a convex ramp. The start keeps its built point (`at`).
5. **Temple stair vault** (12: 0.944 to 0.992): flight and landing under the original's twb2 pointed vault (-288 at the
   walls, +8 on the axis at the foot; 0 and +104 at the head), by roof points; the arch into the nave is the landing
   vault's own end (`height: full`), reveal twb2 and 7tfb11 floor (was a shouldered arch and flat sloping ceilings).
   Flight and landing walls offset [0, 88] to the original's picture height.
6. **Thresholds**: 7tfb11 through 13 temple doorways (the original's floor runs through them; was twb3d).
7. **Roof points chosen anew** (`prune7.py`: from round six's points plus the original's roof vertices inside each
   outline, mouth profiles kept, backward elimination by rms on a 64 grid): east climb 40 (rms 27.0 to 16.1), high pocket
   38 (34.5 to 26.8), west descent 40, ne chamber 40, descent bend 40; north cavern split on its floor line from (-256,
   3840) to (768, 3712) into the body (40, rms 27.7) and the upper floor (19, rms 1.3). No room above 40.
8. **West descent island** (4: 0.936 to 0.962): redrawn from f150-f162, f1430-f1447: upright sides on their foot, leaning
   ones on the middle line (the east end was 32 to 64 inside the original's foot).
9. **Double doors**: leaf edges twb1a (`edge_surface`), the original's (door record 6, face 1530).

### Decided against

- Pruning by `compare`'s score: every point set was chosen by its rms against the original's roof, not the measure.
  (For the north cavern the full candidate list scores lower than a 52-point subset; the rms choice was kept.)
- Moving the double doors' picture split off the eye height: 64 rays (t1d1a/b against c/d) hit the split at exactly
  -256 in both maps and fall to different faces; a measure tie, not a difference.
- Nave 7tws2/twb1 offsets (the worst offset rows): they differ wall by wall of the octagon; bands take one surface per
  room, so only per-wall full-length panels would say them. Not done; offsets do not count in the score.
- The dome: measured again, the original's dome is itself three straight bands (rings at +224, +480, +736, +800), so
  "curved" is no gap; the ribs stay beams 16 deep (flush strips in a leaning side have no word).

### Gaps still open, with repros (`output/studio_cal/mm7_7d06/repro/`)

1. **Panels on a pillar**: north cavern island f135 (cws1), west descent island f153 (cws1) stay plain rock (13 rays);
   the south cavern needed four rooms to say its carvings. Repro `pillar_carved_face/` ("pillars[0].panels: unknown key").
2. **Octagonal door frame**: the double doorway is 384 x 320 with 128 x 64 corner triangles; a door needs a rectangle.
   Repro `door_octagonal_frame/` ("a door leaf needs a rectangular opening").
3. **Leaning pillars and walls** (west island ends, south island): upright on the middle line.
4. **Upright corner between two banks** (north island (1280, 768)): a floor point has one height.
5. **Exit wall**: the original's is 512 at its corners, 640 in the middle; a panel (exit) is a rectangle, so 640 across.
6. Flush dome ribs; walls without thickness on one side (as before).

### Tool notes

- `build` warns that the apse altar's top slab "rests on nothing over most of its footprint"; it stands on the bowl
  platform's flared top (`top_size` 128 x 256 under a 160 x 320 slab): the check ignores `top_size`.
- The 15 bookcase events warn of a silent click when their variable is set; the original's are silent too (kept).
- `project.yml` has no `map_stats.reference`, so `audit --strict` must be given `--original 7d06.blv`.

### Pictures

`output/studio_cal/mm7_7d06/ingame_r7b/diff/` (cameras `shots_r7b.yml`, 26 pairs, mean edge agreement 0.833; round
six 0.812). Best: `26-nave-to-apse.png` 0.98, `23-north-cavern-rise.png` 0.95, `14-stair-arch-from-nave.png` 0.92 (the
arch and vault now the original's). Worst: `18-west-island-north.png` 0.67 and `17-west-island-east-end.png` 0.72
(the island's leaning faces), `02-mouth-to-exit.png` 0.75 (the exit wall's pentagon against a rectangle). Interactive
things: `things_r7/rebuilt/contact.png` beside `things_r7/original/contact.png`. Installed into
`output/studio_play/rebuilds_root` and loaded (`r7_loadcheck.png`).
