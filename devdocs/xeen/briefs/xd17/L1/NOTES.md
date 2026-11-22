# XD-17 Shangri-La: L1 plan (MU-3, MU-4) for the phase 5 review

A5, 2026-11-20. This is a plan only: there is no geometry. Nothing is built until a decider has approved the board
(`output/studio_cal/xd17/mockups/board_xd17.png`, small copy `board_xd17_small.jpg`).
`output/studio_cal/xd17/tools/gen_l1.py` writes the three YAML files here (project, plan, atmosphere) from
`places.py`, the one list of places for the brief, the drawings and the concepts. To change them, edit `places.py` or
the script, then run `output/studio_cal/xd17/tools/run.sh`. It generates the files, runs `oymap fmt`, renders,
writes the census into `totals`, runs `oymap fmt --check` and `oymap validate --assets assets_dev`, and draws the board.
The Python steps run under an 8 GB cgroup cap. Validation: no issues; `fmt --check`: canonical.

## D-50 applied (A5, 2026-11-21)

Decider D-50 (`briefs/x9/L1/D50_DECISION.md`) approved the plan with changes. Applied in `places.py`, `gen_l1.py`,
`render_xd17.py` and `board_xd17.py` (copies before it: `*_before_d50.py`), `run.sh` rerun (validate: no issues). Where
the text above differs, this section and D-50 win.

1. Lacey (monster 11915, MM8 unicorn, NPC 4719) and Stumpy (11916, MM7 treant, `stand`, NPC 4718) are placed peaceful
   actors, not counted; their talk waits on A1's NPC-on-a-placed-monster word (D-47).
2. The well calls A3's `xd17.well` (20,000 experience once per character, the award Found Shangri-La; :27 then :4).
3. The pyramid's arrival is `entrance:d6_pyramid` (0, 3200, 256) facing south (1536); the click calls A3's
   `xd17.pyramid` (Xeen.travelPyramid("shangrila") after m30.done); D6's far end is not built.
4. Both ways out are `exit` presets (D-24), the window's meaning "Leave Shangri-La?" (aaze0049:32); the throat to
   XD-16's `entrance:xd17_way` (4864, -18176, -1280) facing north; the rockfall calls `xd17.cleft_opened` first, then
   X7's `entrance:xd17_cleft` (4096, 8192, 2496) facing west (1024).
5. The residences' doors are `door:maurice`, `door:alexander`, `door:pilar`, `door:benedict`, `door:elona`,
   `door:murray`, `door:sally`, `door:martok` (A4's town file has them).
6. POIs 18 (well, pyramid, crystal, 15 doors); the falls are a landmark with no event.
7. L3 keeps the valley's depth (about 8,800 to the pyramid, 7,600 to the tower from the arrival), sets the anvil
   against the forge wall between its doors, and builds Pilar's pavilion as a small house with a door.
8. Textures: Dungeon L, cap 70, no new textures planned (estimate 40-55).
- Q3 the summit a backdrop of studio masses, 5,600 over the floor, `view_distance_scale` 1.25, no smoke; Q4 the
  signature from the library steps east-north-east; Q5 the crystal in the cliff by the mouth (`xd17.crystal`); Q6 the
  fair preset, no theme, ash or weather; Q7 pool, notch and stream built, the fall decoration behind a switch until
  S's `xeen_waterfall` exists; Q8 the back passage a slot open to the sky; Q9 the far end on D6 (A6).

## What the plan holds

**Route:** an open-air BLV (`kind: indoor`, `profile: region`), X8 Cloudreach's studio route
(`briefs/x8/L4/NOTES.md`): one room open to the sky, the valley floor as ground (atmosphere `ground` layers at L3),
the cliffs, buildings, pyramid and well standing in it. `open_sky` names the preset `fair` (never a texture alias).

**Source:** xeen maze0049 and aaze0049. A green court of 5 x 9 tiles in a ring of houses, the well in the court's
middle (7, 8), the way in at the south (7, 0, "Leave Shangri-La?"), the pyramid at the court's north end (7, 14). The
plan keeps that order on an uneven valley floor: south the way in, the court and its well in the middle, the pyramid
north on a terrace against the cliff.

**Frame:** map units, x east, y north; the datum (0, 0, 0) is the well. The valley sits in X7's compass: the back
passage leaves westward (X7's cleft faces west) and Firestone's summit stands over the north-east rim.

- **The valley:** an uneven oval floor 12,928 x 10,368 (about 436 cells of 512), nearly flat, with terraces of 256
  (the library, the pyramid terrace) and 384 (the temple). A ring of black basalt cliffs closes it: 2,300 high in the
  south, 2,600-2,900 west and north, 3,300 in the north-east, jagged along the crest; the room's sky faces stand
  beyond the crest. Cool air, no ash, no monsters.
- **The first square** (south): out of the cave mouth onto a paved square. Tavern Xanadu stands on its west side and
  Arm and Hammer's long forge on its east, both doors on the square. Benedict's crooked house and Martok's lodge are
  just beyond.
- **The court** (middle): a lawn 2,560 x 3,584 inside a flagstone walk. The +1 level well stands in its middle and
  Lacey grazes beside it. Every lane starts at its corners. An Education, Maurice, Alexander and Psychic Sally have
  their doors on or near its walk.
- **The west terrace:** the Public Library's colonnade and steps (256), facing the court; the signature camera stands
  on the steps. Above it is the Earth Temple (384), squat dark stone with a turfed roof, half sunk into the cliff foot.
- **The pyramid terrace** (north): steps up from the court's north end to the small stone travel pyramid against the
  north cliff. Murray's villa, the valley's biggest house, stands on the terrace's east end.
- **The pool and the falls** (north-east): a cold pool at the east cliff's foot, fed by a white fall from a notch
  1,728 up the cliff. A stream runs south along the cliff foot to a sinkhole. Princess Pilar's pavilion stands on the
  north shore, and the Light guild's round white tower with its gilded dome (1,536, the tallest roof) stands west of
  the pool.
- **The orchard** (south-east): fruit trees in uneven rows, Stumpy rooted in the middle. Elona's house stands at the
  orchard's west edge.
- **The north-west lane:** from the court past Maurice's house along the cliff foot to the back passage.
- **The cave mouth:** a low black throat 768 deep in the south cliff, the end of XD-16's cool passage.
- **The back passage:** a slot of rock open to the sky, 384 wide and 2,087 long, from the north-west cliff to the
  inside of X7's rockfall.
- **Firestone's summit:** a backdrop cone over the north-east rim, 5,600 above the floor and about 14,300-15,400
  from the cameras (question 3). It is drawn for the view, not to X7's heights: X7's crater rim stands about 2,400
  above the cleft.

## Every door (A4's `source/towns/xd17.yml`)

| House | A4 door id | Building | Door point, facing | Floor | Indoor id (request to A4) |
| --- | --- | --- | --- | --- | --- |
| 4353 Tavern Xanadu (tavern; Wilbur, Kublai Khan) | `door:tavern_xanadu` | building:tavern_xanadu | (-1856, -3072), e | 0 | same |
| 4351 Arm and Hammer, arms | `door:arm_and_hammer_arms` | building:arm_and_hammer | (-128, -3456), w | 0 | same |
| 4365 Arm and Hammer, armour (D-5.1's second door) | `door:arm_and_hammer_armour` | building:arm_and_hammer | (-128, -2688), w | 0 | same |
| 4352 Earth Temple (Mother Terra) | `door:earth_temple` | building:earth_temple | (-4864, 768), e | 384 | same |
| 4354 Shangri-La Wizard's Guild (Light; Brunhilde) | `door:guild_light` | building:guild_light | (2560, 2368), s | 0 | same |
| 4355 An Education (Jack Alltrades, Learning GM) | `door:an_education` | building:an_education | (-1600, 1216), e | 0 | same |
| 4356 Public Library (Meditation, Fire, Body GMs) | `door:public_library` | building:public_library | (-3264, -1280), e | 256 | same |
| 4357 Maurice's House | `door:houses#1` | building:maurice | (-1856, 2304), e | 0 | `door:maurice` |
| 4358 Alexander's House (Body Building GM) | `door:houses#2` | building:alexander | (1568, 1664), w | 0 | `door:alexander` |
| 4359 Princess Pilar's Pavilion (Dodging GM) | `door:houses#3` | building:pilar | (4480, 3072), s | 0 | `door:pilar` |
| 4360 Benedict's House (Unarmed GM) | `door:houses#4` | building:benedict | (-1984, -1792), e | 0 | `door:benedict` |
| 4361 Elona's House (Bow GM) | `door:houses#5` | building:elona | (2560, -2784), n | 0 | `door:elona` |
| 4362 Murray's Villa (Staff GM) | `door:houses#6` | building:murray | (1792, 3840), s | 256 | `door:murray` |
| 4363 Psychic Sally's (the seer) | `door:houses#7` | building:sally | (1632, -1280), w | 0 | `door:sally` |
| 4364 Martok's Lodge (Dark Elf GM) | `door:houses#8` | building:martok | (-3712, -3008), n | 0 | `door:martok` |

Fifteen doors on fourteen buildings. Every door faces a compass axis and has a lane within 320 of it. No prop goes in
front of a door or on a lane (`places.LANES` are the walking lines).

## Arrivals, ways out, the pyramid, the well

- **In from XD-16: `entrance:xd16_way`** at (-1280, -4736), floor -64, 512 out of the cave mouth, facing north
  into the valley. This is the arrival camera. A7's cool passage end (D-47 Q4) calls A3's `q-c26.way` (true with
  `q-c26.done`) and moves the party here.
- **Back to XD-16:** the back of the throat at (-1280, -5888) asks "Leave Shangri-La?" (aaze0049:32), then goes to
  XD-16's **`entrance:xd17_way`** (A7: about 256 inside the passage's far end, facing back down to the last cave).
  Neighbour `exit:xd16_way`.
- **Out to X7:** the inside of the rockfall at (-7680, 3712). The first time, it calls A3's `xd17.cleft_opened`
  (sets `cleft_open` 116140, once, a status line: "You shift the last stones from the inside. The cleft is open both
  ways now."). Then it moves the party to X7's **`entrance:xd17_cleft`**, (3994, 8192, 2500) facing west (1024),
  X7's `places.CLEFT_ARRIVAL`. It is always open from this side. Neighbour `exit:x7_cleft`.
- **In from X7: `entrance:x7_cleft`** at (-7296, 3648), 384 inside the stones, facing east down the passage, 1,694
  from the valley. X7's `door:xd17` opens on `xd17.cleft` (reads `cleft_open`) and leads here. X7's generator
  (`places.PROPOSED['xd17']`) already names this arrival and opens the door once XD-17 is installed with it.
- **The travel pyramid** at (0, 4032) on the pyramid terrace (256), its portal face south at (0, 3584). It calls
  `Xeen.travelPyramid("shangrila")` (xeen_common.lua: opens on `m30.done`, to `alamar_gate`). Before M30 it shows the
  source's line: "The moons are not aligned. You are unable to pass." (aaze0049:25). The arrival from the far pyramid
  is `entrance:pyramid` at (0, 3200, 256) facing south (1536) over the court (`Xeen.PyramidArrivals.shangrila`,
  A3). Neighbour `pyramid:alamar`: D6 at Alamar's gate, or DD-17 (question 9).
- **The +1 level well** at (0, 0): "Congratulations, You found Shangri-La! +1 Level (permanent)" (aaze0049:27), then
  "The water is cool and refreshing." (aaze0049:4). It works once per character. What +1 level means in MM6-MM8 terms
  is question 1.
- **Stumpy (4718)** is rooted in the orchard at (4608, -2304). **Lacey (4719)** grazes by the well at (448, -384),
  590 from it, within 512 of her spot. Both are peaceful and speak their A4 topics; how they are built is question 2.
- **The hidden crystal** is set in the cliff 450 east of the cave mouth, at eye height, at (-832, -5216), facing the
  valley. Clicked, it gives A3's line (question 5). Benedict's greeting explains it ("broadcast to millions from the
  hidden crystal in the wall").
- **Hint people** (A3's npcs/xd17.yml): Maurice (the sword), Alexander (the Sphinx, GOLUX), Princess Pilar (the
  key), Elona (the password, "laboratory"; M23), Psychic Sally (the mirror and the Seer topic). They live in their
  houses; no outdoor place.

## Figures (render_xd17.py, `output/studio_cal/xd17/mockups/figures.json`)

`town_feel.py` reads ODMs only, so the town figures are measured on the plan by `render_xd17.py` with TOWN_FEEL's
definitions. The town is the floor within 1,536 of a door, the centre is the service doors' centroid, and the bands
are §5c's `--small` bands. Shangri-La has 5 services; MM6's Paradise Valley, the nearest shipped analogue, has 5 and
16 residences.

| Figure | Target | Plan |
| --- | --- | --- |
| Services | `hidden` 4-6 (towns.py) | **5**: weapon, armour, temple, tavern, Light guild (D-5.1) |
| Residences | 8 +- 3 (WORLD_DESIGN 5.1) | **10**: An Education, Public Library, eight hint people |
| Buildings; doors | A4's 15 houses | 14; 15 (Arm and Hammer has two) |
| Weapon to armour | 384-5,830 | 768 (one forge, two doors) |
| Service to nearest service, median | 854-2,424 | 1,770 (768, 768, 1,770, 4,878, 5,726) |
| Farthest service | 3,203-16,598 | 4,970 |
| Town core radius | 2,360-6,552 | 3,530 |
| Fringe / core; footprint beyond 1.5 core | 1.29-3.79; 0-0.38 | 1.73; 0.22 |
| 90th percentile; farthest building | up to 13,228; 17,027 | 6,120; 7,113 |
| Town built share | 0.15-0.37 | 0.156 (at the low end: a garden town) |
| Tavern rank from arrival / from centre | 0.05-0.95 / 0-0.94 | 0.08 / 0.15 (the first house on the way in) |
| Temple rank from centre | 0-1.0 (apart or raised) | 0.77, on the west terrace at 384 |
| Doors on compass axes | 0.77-1.0 | 1.0 |
| Doors with a lane within 1,024; door to lane | 0.81-1.0; median 147-381 | 1.0; median 0, farthest 320 |
| House to nearest house, median | - | 1,498 |
| Door levels p10-p90 | 0-680 | 0-256 |
| Wells and fountains | 3-8 a map, 0-3 in town | 1 (exception below) |
| Monsters; spawn points; chests | none (MAPS, D-5.1) | 0; 0; 0 |
| Valley floor; cliffs | - | 12,928 x 10,368 (~436 cells); crest 2,333-3,304 |
| Walks | - | arrival to first door 1,722, to the tavern door 1,761, to the well 4,906; well to pyramid 3,584; well to the passage 6,542; passage 2,087 |
| Summit from the cameras | inside the view distance | 15,373 (arrival), 14,310 (signature); view distance x1.25 = 20,240 |
| Points of interest | - | 19: the well, the pyramid, the crystal, the falls and 15 doors (plus Stumpy and Lacey) |
| Textures | proposed cap 70 (Dungeon L; ROADMAP 5.2 has no open-air town class) | estimate 40-55: the Cloudside town kit (MU-5), pale marble for the library and guild, a gilded dome, basalt cliffs (X7's), ground layers (grass, flagstone, packed earth). New: none named |

**Town feel exceptions:**

- Wells and fountains 1 (shipped 3-8 a map). The source has one well, and the +1 level well is the whole point. The
  pool and the fall stand in for the rest. This is not a buff device.

## The concepts (MU-4), and what L3 corrects

One `codex exec` call per view, no retries (`raw/xd17_arrival_v1.png`, `raw/xd17_signature_v1.png`). Both keep the
blockout's composition: green valley, black basalt ring, gilded tower, pyramid, white fall, Firestone with a smoke
thread over the north-east rim. Where they differ from the plan (fixed at L3, not in a new concept):

- Both compress the valley's depth. The pyramid and the tower stand nearer than the plan's 8,800 and 7,600 from
  the arrival.
- The arrival puts the forge's open fire and an anvil on the square in front of the forge. At L3 the anvil stands
  against the wall between the two doors (the dressing rule).
- The signature shows Pilar's pavilion as a domed gazebo across the pool. The plan's pavilion is a small house with
  a door (house 4359).

## Source lines used (aaze0049)

- :4 "The water is cool and refreshing." (the well after its gift)
- :25 "The moons are not aligned. You are unable to pass." (the pyramid before M30)
- :27 "Congratulations, You found Shangri-La! +1 Level (permanent)" (the well's first use; the second line is
  question 1's)
- :32 "Leave Shangri-La?" (both ways out)
- The NPC lines are A3's and A4's (ORIGINAL_LINES.md rows 167-187, 289-293).

## Open questions for the decider

1. **The well's +1 level.** QUESTS has no permanent levels (X8's explorer statue became +2 Speed and an award,
   `x8-sky.yml`). D-5.1 keeps "the +1 level well", and WORLD_DESIGN 5.1 says "rescaled".
   - Options:
     - (a) Experience to the drinker's next level, once per character, plus an award "Found Shangri-La". The
       drinkers still train elsewhere: Shangri-La has no training hall (D-5.1).
     - (b) +1 base level, as the source has it.
     - (c) X8's pattern: an award and +2 to one stat.
   - Recommendation: (a). The map is the same in every case; A3 writes the hook and A2 enters it in the ledger.
2. **Stumpy and Lacey.**
   - Options:
     - (a) Both placed as peaceful actors with topics (A4's plan). This needs S's models with clips and A1's NPC on
       a placed monster.
     - (b) Both as animated decorations whose click speaks (`evt.SpeakNPC`). There is no AI, and they cannot be
       attacked.
     - (c) Lacey as an actor grazing within 512 of the well, Stumpy as a rooted animated decoration.
   - Recommendation: (c). A tree does not walk. Both are blocked on S's models in every case.
3. **Firestone's summit over the rim.**
   - Options:
     - (a) A backdrop cone of studio masses beyond the north-east crest, 5,600 above the floor, with
       `view_distance_scale` 1.25. A smoke thread only once A6/S have an effect for it.
     - (b) No summit: the cliffs alone close the sky.
   - Recommendation: (a), without smoke until there is an effect. It tells the player where the valley is, and it is
     what makes the green read as hidden. It is drawn for the view, not to X7's heights.
4. **The signature view.**
   - Options:
     - (a) From the library steps (-3008, -1408), eye 554, looking east-north-east (28 degrees): the court, the well
       and Lacey, the pool, the white fall, the guild's dome and the summit. This is what is drawn.
     - (b) From the pyramid terrace, looking south over the whole valley to the cave mouth, with the summit behind
       the camera.
   - Recommendation: (a).
5. **The hidden crystal.**
   - Options:
     - (a) In the cliff by the cave mouth, at eye height, facing the valley. Every visitor is "on camera" from the
       first step. This is what is drawn.
     - (b) In Benedict's house front.
     - (c) No object: Benedict's line alone.
   - Recommendation: (a), with a short A3 line on click.
6. **The sky inside.**
   - Options:
     - (a) The fair preset, no theme, no ash: the valley clears. This is what is drawn.
     - (b) Fair with X7's ashen theme.
     - (c) Fair with the shipped `lush` theme, if an open-air BLV takes a sky theme. A1 must confirm: sky.yml's
       `maps` keys are map file names, and every row today is an ODM.
   - Recommendation: (a); (c) if A1 confirms.
7. **The water.**
   - Options:
     - (a) A cold pool, a white fall from the east cliff, and a stream to a sinkhole. The fall is S's `xeen_waterfall`,
       a water preset of the sand-fall build. This is what is drawn.
     - (b) The pool and the stream only, from a spring under the cliff. No new model.
     - (c) No water.
   - Recommendation: (a), with (b) as the fallback if S cannot make the fall.
8. **The back passage.**
   - Options:
     - (a) A slot open to the sky, 384 wide and 2,087 long, with X7's arrival at its west end. This is what is drawn:
       one sky room, and it is cheaper.
     - (b) A dark tunnel with a door at the valley end.
   - Recommendation: (a).
9. **The pyramid's far end.** WORLD_DESIGN 3.3 says "the one in Castle Alamar's dungeon (D6)", xeen_common.lua says
   `alamar_gate`, and ROADMAP 5.6 says Castle Alamar.
   - Options:
     - (a) On D6, outside Alamar's gate: the Lua's name, and an outdoor landing like the first pair.
     - (b) Inside DD-17.
   - Recommendation: (a). Only this map's neighbour row changes (`pyramid:alamar`, `to:` today `xeen_d6.odm`).

## Requests (for the orchestrator to relay; none of these files is A5's)

- **A4:**
  - Rename the eight residence doors `door:houses#1` to `#8` to indoor ids: `door:maurice`, `door:alexander`,
    `door:pilar`, `door:benedict`, `door:elona`, `door:murray`, `door:sally`, `door:martok`. An indoor map's house door
    is its wiring event's source. Studio ids must match `^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9_]*$` (no `#`), and
    `tools/xeen/towns.py` (`wiring_doors`) compares those sources with the town file's `door:`. The other seven ids
    stay as they are.
  - Confirm Stumpy's and Lacey's places as drawn: the orchard (4608, -2304), and by the well (448, -384).
- **A3:**
  - A hook for the well, `xd17.well`: aaze0049:27 on first use, :4 after, once per character, the gift per question 1.
  - A short line for the crystal, `xd17.crystal`, in Benedict's voice.
  - A pyramid hook like `m7.pyramid_x1` (reads `m30.done`), and `Xeen.PyramidArrivals.shangrila = {0, 3200, 256,
    1536, "xeen_xd17.blv"}`. The far end, `alamar_gate`, is the map lane's (question 9).
  - A first-arrival status line (the studio warns a new map without one).
  - `q-c26.way`'s `where` names XD-17's `entrance:xd16_way`.
  - ORIGINAL_LINES rows for aaze0049:4, :25, :27 and :32.
- **A2:**
  - The map_stats row 9120: no slots, encounter 0, music 51, continent 6, environment plains, as in project.yml.
  - The well in the permanent ledger (question 1).
  - Lacey's peaceful unicorn row if question 2 is (a) or (c).
- **A6:**
  - The ground layers for the valley: grass, flagstone, packed earth, and basalt for the steep ground (X7's `basalt`).
  - Pale marble for the library and the guild, and a gilded dome.
  - The texture cap for an open-air town BLV (70 proposed).
  - The fair preset as named; the theme per question 6.
  - Optional: a thin smoke effect for the summit (question 3).
- **A7:**
  - XD-16's cool passage end: the exit preset to XD-17's `entrance:xd16_way` (facing north into the valley), and
    XD-16's `entrance:xd17_way` for the way back.
  - The passage rises toward the valley. XD-17's throat floor is -128 to -64 and its arrival is at -64.
- **S:**
  - Lacey: a white unicorn with idle, graze, turn and talk clips. MM6's Unicorn sprites (m545) are the reference,
    through the HD master step.
  - Stumpy: an old gnarled fruit tree with a face in its knot, with an idle sway.
  - `xeen_waterfall`: the sand-fall build with a water preset, about 1,700 high, pouring west into the pool
    (question 7).
  - The pyramid, the well and the cliffs are studio masses; no models are asked for them.
- **A1:** Confirm three things:
  - whether an open-air BLV takes a sky theme (question 6);
  - that `view_distance_scale` 1.25 is affordable in a small open-air map;
  - that house doors in an open-air BLV enter by `evt.EnterHouse` from a door face, as XD-07 and XD-13 do.
- **AU:** Sounds for the fall and the stream, the forge's hammer on the first square, the tavern's murmur, and birds
  by day. Music 51.

## Files

- Brief: `devdocs/xeen/briefs/xd17/L1/{project,plan,atmosphere}.yml` and this file. There is no `sketch.yml`: an
  indoor project has none.
- Scripts in `output/studio_cal/xd17/tools/`:
  - `places.py`, the places;
  - `gen_l1.py`, the brief;
  - `render_xd17.py`, the plan, the blockouts and the figures;
  - `paint_xd17.py`, the Codex concepts;
  - `board_xd17.py`, the board;
  - `run.sh`, the whole chain.
- Drawings in `output/studio_cal/xd17/mockups/`:
  - `plan_xd17.png`;
  - `blockout_arrival.png`, `blockout_signature.png`;
  - `board_xd17.png`, `board_xd17_small.jpg`;
  - `figures.json`;
  - the raw Codex returns in `raw/` (`xd17_arrival_v1`, `xd17_signature_v1`: the image, the prompt `.txt` and the
    log), one call each, no retries.
