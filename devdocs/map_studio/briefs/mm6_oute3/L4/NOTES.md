# New Sorpigal (mm6 oute3.odm), outdoor rebuild, held out

Scratch: `output/studio_cal/mm6_oute3/` (`an/` analyses of the original, `scripts/`, `cmp/cNN` measures with
`cNN_old` = `--without rim`, `pics/` same-camera pictures, `run/` walk logs, `backup_first/` the project before each
scripted edit). Map stats row 9603, project id `calib_newsorpigal`.

## Round one (2026-11-13, `openyamm-studio/build/oymap`; final checks with outdoor batch eight)

### Scores (`oymap compare`)

| Part | First sketch (c1) | Grid unit 32 (c2) | End (c19, batch eight) |
|---|---|---|---|
| **total** | **88.0** | **88.2** | **92.8** |
| total `--without rim` | 88.5 | 88.7 | 93.2 |
| heights | 94.2 | 94.7 | 95.2 (96.7 without rim) |
| relief | 88.6 | 89.0 | 89.6 (93.3) |
| cliffs | 83.1 | 84.6 | 88.6 (89.7) |
| water | 99.8 | 99.8 | 99.8 |
| ground | 84.2 | 84.2 | 85.7 |
| roads | 96.2 | 96.2 | 97.5 |
| buildings | 72.1 | 72.1 | 92.4 |
| decorations | 98.9 | 99.1 | 99.1 |
| spawns | 75.9 | 75.9 | 74.1 |
| events | 78.7 | 78.7 | 91.5 |
| rim (skyline) | 96.9 | 96.7 | 96.8 |

The very first build (c0, before water and ground outlines were fixed for the closed inside test) was 85.8.
Events fell to 68.1 between c2 and c3 when false pairs went (a house's name event on its walls paired with the
Dragon Tower's keyhole); they rose to 91.5 from real handlers. Two honest forms measured lower and were kept: the
Abandoned Temple's door as a doorway in the hill (92.9 to 92.7; describe.py had made a gabled house 672 over the
land) and the volcano by its peak alone (see tool defects).

### Walk

`playtest.yml`, 140 steps, passes three runs of three on the final project (`run/w8.log`, `w9.log`, `w10.log`,
about 2 minutes each): new game on the rebuilt map at the original's party start; north through the gate to the
central fountain (event runs: "Refreshing!" until its midnight refill); one hour on (the Town Hall opens at 10, as in
house_data.txt); Town Hall, Savings House, Traveler's Supply, the coach house, A Lonely Knight, the Knife Shoppe, the
Common Defense, the Seeing Eye, Blades' End, the training grounds, a house of one resident (Isao Magistrus), Buccaneers'
Lair shut by day (opens 18 to 6, as the original); the south well; up the hill on foot to the temple (325), along it
to the Initiate Guild of the Elements (1214) and to the keep's loggia and the Initiate Guild of the Self (189); out of
the gate, east along the shore road, up the pier's ramp onto its deck (160) and the Odyssey's gangway (496); west to
the path and on foot up Goblinwatch's hill to its door, locked without the key; out by the west road to Castle
Ironfist's map (outd3) and back (the game lands the party at x -23076, on the row it left by). Walks between places
are `walk_to`; doors are used from the rebuild's own `oymap things` stand points, each checked against the original's.

### What was scripted

- **The first sketch** (`scripts/first_sketch.sh`: `gen_first.py`, then `gen/describe.py` copied from
  `output/studio_s4c/gen/`, then the placed decorations): 32 x 32 spot heights (unit 32: unit 64 had put the town's
  160 at 128), the sea as outlines of the original's water nodes in strips cut through every island (an outline has no
  holes; 17 bodies, 20 of 16641 nodes off), ground zones from the original's corner kinds, roads over its road tiles,
  spawn points as packs, the people standing in the town, decorations (every planted thing in the town and every
  clicked one placed, the rest by clump and 8 x 8 block), and 36 buildings, 17 crates, 5 signs, 3 platforms and the
  obelisk by describe.py. Not run again.
- One-off edits, each in `scripts/`, diff checked, numbers from the original's faces (`scripts/faces.py`):
  `r1_edits.py` (events on doors only, no foundations, road beds, the bridges, fence, planters, gate and its sign,
  fountains, wells, pier, ship, sign events), `r2_events.py` (orchard, rock chest, buoy, camp fire, sword in the
  stone, dimension pedestal, sign names), `r3_buildings.py` (the keep and the Dragon Tower), `r4_land.py` (crater,
  volcano, Goblinwatch's summit, the strip south of the harbour lane), `r5_paths.py` (the five dirt paths),
  `r6_entrances.py` (the three dungeon ways and their screens, Goblinwatch's key), `r7_water.py` (fountain and well
  handlers), `r8_fixes.py` (untitled doors, the temple door's cleft), `r9_wells.py` (batch eight's well `frame`),
  `r10_temple.py` (the temple's recessed door), `r11_recesses.py` (doors set back on four buildings). The road jogs
  were squared by hand (the original has no diagonal road tiles).

### What the measure does not see (things pass)

`oymap things`: original 95, rebuild 86 (`an/things_orig.txt`, `an/things_r2.txt`). Every house, shop, guild, the
temple, the ship and the three dungeon ways open what the original's do; every door now stands within 16 of the
original's except Buccaneers' Lair (one of its three doors with event 27, the west one), the Odyssey (its click is the
whole model 2 of the ship, the original's one face) and Goblinwatch's upper house door (1463, on the ground storey).
Per kind:
- Houses and shops: the original runs a building's event from the door face only; so does the rebuild (doors carry
  house and title, no name event on walls).
- Fountains: an eight-sided basin with water; the water and the rim carry the event (the original: water only).
- Wells: twelve-sided ring, batch eight's frame (two uprights, shingle gable 32), event on the whole well.
- Signs: the five free-standing ones say their shop's name (stable's enters the coach house); the five hanging signs
  on shop walls (armorpor, STOREMID, Magicpor, BLKSMMID, TRAINING) are not built (gap 4).
- Crates: the original's 17, chests 1 to 18 with their events (default contents; the original's are random too).
- Decorations: the nine apple trees pick once and go bare (a load event keeps them bare), the rock opens a chest, the
  buoy sets off the volcano, the camp fire calls the island's packs once, the sword wants Might 25, the pedestal and
  orb open the dimension door.
- Pictures: `pics/r1/` (107 pairs at every thing of the original and 12 fixed views, the project before the last four
  edits; edge agreement 0.687), `pics/r2/` the final project (running at the end of the round; same cameras). Taken
  through `scripts/pics_copy.sh` (see tool defects). Best: the gate from the south 0.84 (`diff/01-e2-EntranceN.png`),
  the keep 0.68 with its loggia and gable as the original's (`14-keep-from-south.png`), the town from the south 0.67
  (Dragon Tower, fence, houses in place). Worst: cameras that the scripted placement put inside a facing house (0.13,
  `39-e53-HseP2aN_1.png`: both maps show a wall; not a fault of the map), the obelisk in its crater (before r4).
- Seen in the play root (`output/studio_cal/mm6_oute3/playroot_check/start.png`): the gate's board reads mirrored on
  its south face; the gate's pillars are square stone piers where the original's are round with caps.
- Coplanar faces: `oymap audit ... --original oute3.odm` on the play root lists none.

### Gaps (most harmful first)

1. **An overhanging upper storey on posts** (the two west-end houses HseR3W, HseR3W_1: the ground storey 256 behind
   the upper one, which stands on two posts at its corners): a recess open at a corner is refused. Built: the door bay
   recessed only. Field: a recess that reaches the corner with a post there, or `posts` on a recess.
2. **An invisible step plate** (BridgeT, event 221: the face under the north bridge's west end that calls up four
   goblins once): a platform is drawn. Not built. Field: `invisible: true` on a platform with `trigger: step`.
3. **Round pillars with caps on a gate** (EntranceN): a wall with a gate opening. Field: `piers: round` on a wall's
   gate, or round parts on a wall.
4. **Hanging shop signs carrying the shop's name event** (five shops): part `signs` have no event of their own;
   batch eight's `same_event_as` lets a structure carry a building's event, but these are part signs. Not built. Field:
   `signs[].title`.
5. **A small panel of a wall carrying an event** (the Dragon Tower's keyhole, event 231; the Savings House's secret
   panel, event 225, a scroll of Fly once; Buccaneers' Lair's high secret exit to Dragonsand, event 104 at 544 to 672):
   the keyhole's event is on the whole shaft; 225 is not built; 104 is a ground-floor door with no title. Field:
   `panels[]` on a part (a wall bay with its own event and height).
6. **One event on three doors** (Buccaneers' Lair, event 27): the west door only. Field: `doors[].same_event_as`.
7. **A spawn marker's tier** (the original's markers 10 and 11, the slots' C monsters, on the north-east islands): an
   area takes a slot only. Field: `areas[].tier`. Spawns part 74.1.
8. **The fence's plinth, posts and the planters' slopes**; the bridges' level middles and arches (a humped deck);
   the wells' event on the ring (the original: water only).
9. **The overhanging house at Goblinwatch** (event 63, a door at 1984 to 2240, over a ground the castle's model
   reaches from below): on the ground storey here.

### Tool defects

- **MM7 diagonal road tiles in an MM6 map**: at a one-cell jog of a road the build lays the staircase pieces
  (`7drsrne1/2`, rows 793-794 of the road set) which MM6's set does not have (the original lays two round bends), and
  `tools/terrain_materials.py` has no rule for them, so `outdoor_materials.py` and `outdoor_ingame.py` fail ("No
  terrain material rule matches tile 7drsrne1"): no picture can be taken and the game has no material file for the
  map. Repro: build this project, `python3 openyamm-studio/calibration/outdoor_materials.py
  devdocs/map_studio/briefs/mm6_oute3/L4 --root <root>`. Worked round for pictures and the play root only:
  `scripts/pics_copy.sh` adds a one-cell stub north of each jog's upper bend in a copy (`pics_project/`), and the play
  root's material file was made from that copy's build (4 road cells differ from the installed map).
- **Height points add up**: four points round a peak raised the nodes between two of them to 5376 (the peak 4064);
  eight to 4576. Kept the peak alone (`r4_land.py`).
- **`outline.py` of the models' scripts assumes a half-open inside test**; since the closed test every outline of node
  squares took a node more to the south and east (the sea a cell into every north and west shore: c0). Fixed in this
  scratch copy (`cells_of`, `raster_closed`).
- **describe.py** made the humped bridges gabled buildings, the Abandoned Temple's door frame a house 672 over the
  land, and put doors without a place on the first part's front (the temple's inside its hall).
- A door without `title` says its structure's id (`thing:building_24`); an empty title is needed for the original's
  nameless ways.
- `play_lua`'s `status()` read empty after a status text (fountain, Goblinwatch's lock); the walk checks the event
  and the dialog instead.

### Unsure

- Whether the north well's 100 gold (event 109: a party with no gold, once) and the wells' refill timing (65534,
  65535) are meant as written; kept as the handlers say.
- The fountains' stores are empty until the first midnight in both maps.

### Run

```
./tools/run_game.sh --isolated nsorp --assets output/studio_play/rebuilds_root --world mm6 --map calib_newsorpigal.odm
```
(installed with `oymap install ... --root output/studio_play/rebuilds_root`; bolster row 9603 written; map_stats row
9603; travel row west to outd3.)

## Round two: the user's 21 places (2026-11-13)

The user walked the play root and sent 21 poses where the rebuild looks least like the original. Each was taken in
both maps from the same camera (`output/studio_cal/mm6_oute3/user21.yml`; pitch in degrees as the tour script takes
it): before `pics/u0/`, after `pics/u2/` (`diff/NN-uNN.png` side by side with edges). The models at each pose were
found by casting rays from the camera through the original's faces (`scripts/u_hits.py`) and dumped face by face
(`an/u/m<model>.txt`, `scripts/faces.py`). Every change is in `scripts/r12_user.py` (numbers from those faces; backup
of the project before it: `r2_backup/`; diff checked on a scratch copy `r2/proj` first).

### Scores (`oymap compare`, the studio binary of 21:34; round one re-measured with it)

| Part | Round one (c19_now) | Round two (c20) |
|---|---|---|
| **total** | **92.8** | **93.5** |
| total `--without rim` | 93.2 | 93.8 |
| buildings | 92.4 | 95.9 |
| events | 91.5 | 92.6 |
| decorations | 99.1 | 98.9 (a scatter tree lost its place to a slab) |
| others | unchanged | unchanged |

Pictures at the 21 poses: edge agreement 0.644 before, 0.750 after (`pics/u0/pixels.json`, `pics/u2/pixels.json`).

### The 21 places

| Pose | Model (original) | What differed | Done / missing word |
|---|---|---|---|
| 1 | TavFrntW, TavBckW (A Lonely Knight) | porch drawn as a solid stone wall 768 high; hall 32 low; ground storey drawn twice (coplanar) | porch as an open part on 4 posts with a balcony railing (parapet 96), slab and step as platforms, plinth 32, hip 224 reaching out 32, door one bay 256, upper doors 60/61 up a storey. The open part also stands two posts against the wall (word: posts on chosen walls) |
| 2 | BlackSMW (Knife Shoppe) | body 224 too wide with a recessed door; no brick floor or roof over the west front | body 896 by 640 on a plinth 32, roof canopy 256 out, brick slab and step as platforms. The roof runs on over the porch in the original; here a flat canopy (word: eaves on one wall, or a porch roof continuing the roof's slope) |
| 3 | BankE (Savings House) | porch inside the body (body 224 too wide), two door panels stacked, flat roof | body 640 by 512 on plinth 32, hip of TAVRF; porch on two posts with a balcony the upper door (62) opens onto; slab. Roof reaching 128 over the porch not said (word: eaves on one wall). Secret panel 225 still not said (gap 5) |
| 4 | GenStorE (Traveler's Supply) | two door panels side by side; no chimney | door one bay 256, chimney part. Hip ends cut to a small gable (jerkinhead) not said; hanging sign STOREMID (gap 4) |
| 5 | StablesE (coach house) | a lean-to box 896 square | gabled house 896 by 512 (shingle gable ends) and an open stall on posts with a low wall to the north. Its side low walls run 224 only (word: a sill on part of a wall) |
| 6 | TrainingE | two overlapping plain boxes, no entrance recess, no windows | one block 768 by 1024, two storeys of THctr/THctrW1, recess 128 over the door bays, roof band 80 reaching 64 out. Crest and TRAINING sign over the door not said; the band and its underside share the `trim` role (word: a soffit role) |
| 7, 8 | ThievesN (Buccaneers' Lair) | seven boxes with flat roofs and a wooden band 128 | a centre with a hip and three wings with cut corners, roofs rising 128 over 64 to flat tops (hip with `cap`); a door in each wing's end, each opening house 191 (the original: one event on three doors; `doors[].same_event_as` still missing, gap 6) |
| 9 | SmKeepFrnt (loggia, Guild of the Self) | ceiling timber, back door two panels | ceiling t1c2, door one bay 256. Floor greener than the original: ground transition tiles (batch nine) |
| 10 | TempleS | back of the porch two door panels, ceiling plain | door one bay 256 under a ceiling of t1f1 |
| 11 | MagicGS (Guild of the Elements) | brick roofs, gables on the wings, two door panels | every part under Pxshings rising 64 over 128 to flat tops, door one bay 256, lantern walled THle/Thre. Finial not said |
| 12 | D18N (Gharik's Forge's house) | two walled boxes over the porch | body 768 by 512 on a plinth, hip 192, canopy 192 deep over the whole front on two posts 256 in from the ends, slab. Granite door frame not said |
| 13 | SLuckN (Shrine of Luck) | a closed box; the shrine's event 261 missing | open recess 256 by 320 in the north front, tiled floor, the altar with event 261 (its handler as the original's), gable ends t1w11a. The recess widens to 384 behind 128 in the original (word: a recess of two widths) |
| 14 | HseR3W_1 (and HseR3W) | upper storey not overhanging; gap 1 of round one | upper storey as a hanging part reaching 256 past the ground storey, posts under its outer corners (an open part), door in the ground storey. Gap 1 closed, but the open part adds two posts against the ground wall |
| 15 | MercN (Blades' End) | hip 96 over a wooden band 56; door two panels; no steps | plinth 32, roof rising 128 over 64 to a flat top, door one bay 256, two steps as platforms. The original's cut corner facets not said |
| 16 | TownE (Town Hall) | court of grass; wooden bands under the roofs | court paved T3C2 (platform), roofs 128 without bands. Its course is 16 (plinth goes in 32s); ground before it greener (batch nine tiles) |
| 17 | DEnterS (Abandoned Temple door) | door flush with the hill | the door at the back of a mouth 256 deep (`hood`), floor and step as platforms. The frame's little gable roof (TDoorA) not said |
| 18 | EvilKC (Goblinwatch keep, north) | no entrance (its door hidden behind the centre's wall), four windows a row | the whole-width box removed; entrance D2LgDor recessed 96 in the centre's front, two-window bays, hip 448 to a ridge 128 and a spire |
| 19 | EvilKC/L/R from above | no corner towers, wings 128 too high | four towers 128 square with pyramids, wings 384 with parapet 128 round their terraces |
| 20 | EvilKC (roof and windows) | small | the same changes |
| 21 | EvilKC/KR (south) | eight doors along the ground of the south front; no ledge | south front plain Tewd with its windows above; the ledge 256 high in front (two walls, open between). Event 63 (house 1463) moved to a door up a storey in the centre's east wall over the east wing's terrace (the original's is inside, onto a gallery: gap 9) |

### Walk

The walk failed twice in four runs at the pier's ramp (step 110): an actor on the shore stood in the way and the
party stepped off into the water (it was in the way in round one's logs too). `playtest.yml` now starts the ramp
from its foot (`set_pose` at x -1480). Final project: two runs of two (`run/r2w5.log`, `run/r2w6.log`).

### Missing words (round two)

- `porches[].floor` counts from the part's foot, so over a `plinth` a porch slab at the floor cannot be said (four
  slabs drawn as platforms). Repro: `output/studio_cal/mm6_oute3/r2/` building_22 with `floor: 32` lays its top 32
  over the floor.
- Eaves on one wall, or a porch roof that continues the roof's slope (BlackSMW, BankE).
- Posts of an open part on chosen walls only (porches on posts against a wall, the overhang of HseR3W).
- A sill on part of a wall (StablesE's stall); a recess of two widths (SLuckN); a soffit role apart from the band.
- Still open from round one: hanging shop signs with their events, panels with their own events, one event on
  several doors, the keep's inner gallery, the gate's round pillars and mirrored sign, the bridge's step plate.
- Batch nine (not worked round): the ground before several doors (poses 2, 3, 9, 16) is a grass-dirt transition tile
  drawn greener than the original's pure dirt; the measure counts the same kind.

### Tool defects

- The MM7 jog road tiles of round one are no longer laid: with the studio binary of 21:34 the round-one project and
  this one build without 7drsrne tiles, and `outdoor_materials.py` runs on the project's own build. The play root's
  material file is now made from it.
- The binary changed during this round (21:34); both rounds were measured again with it.

### Installed

`oymap install ... --root output/studio_play/rebuilds_root` and `outdoor_materials.py --root ... --build
output/studio_cal/mm6_oute3/build`; the game loads it (`output/studio_cal/mm6_oute3/playroot_check/r2_tavern.png`).
`oymap audit` there: faces in one plane 0 pairs.

## Cleanup: z-fighting and town feel (2026-11-14, `openyamm-studio/build/oymap` of the fourteenth merge)

Backup before: `output/studio_cal/mm6_oute3/cleanup_backup/`. Scripts (each run once, its diff read):
`output/studio_cal/mm6_oute3/cleanup/edit_ns.py`, `edit_ns2.py`, `edit_ns_roads.py`; helpers `near.py` (faces of a
map's models near a point), `roads_tf.py`, `mirror_tf.py` (town_feel's road runs and mirror pairs).

**Faces in one plane: 58 to 2** (the original 0). Changed, each from the original's faces:
- Temple (building_2): the cross's north-south block as two arms meeting the east-west block (p1, p1s), not one block
  through it (their flat tops lay in one plane).
- The Seeing Eye (16): the main range starts at the west wing's east wall (door bay 5 to 3, same place).
- Guild of the Elements (17): the middle range only between the two wings (MagicGS: one U; door bay 2 to 0).
- Town Hall (21): the arms start at the spine's east wall; the west bump ends inside the spine, its west hip 128 (TownE face 24).
- Bank (25): the porch part over the original's two posts (BankE: x -10880..-10848, inset 32, its balcony floor the same rectangle), posts on its east wall only.
- Tavern (35): its porch part has no posts of its own; the original's four posts are platforms on the slab, 28 wide and 4 in from its edge (the original's are 32 and flush: a platform's 64 skirt below `raise` would run down the slab's side).
- Gharik's Forge (32): the canopy without corner posts; the original's two posts (D18N, 64 behind the front) are platforms on the slab.
- Shrine of Luck: stands on its floor (128..240) 4 off the floor's back edge (its back is in the wall).
- The pier's ramp: `rise` 160 to 122; it ended 38 above the deck (198 against 160).

Left, with why: building_2 p3/p4 (1 pair): the door recess's ceiling and the hanging upper storey's underside are the
same face at 256 over the recess; the recess cannot sit under a part with `bottom` without both (studio limit).
pier/pier_ramp (1): both forms draw an end face at x -1112; the pier's lies inside the ramp, unseen.

**Town feel** (`town_feel.py`, rebuild against `oute3.odm`):
- Longest straight road 7680 to 3072 (original 3072): the inner block's street was one ring; the original's north and
  south runs stop at x 43 and start at 46 (two dirt cells). Now two halves.
- Mirror share 0.64 to 0.56 (original 0.56): Buccaneers' Lair's doors listed east door first, as the original's first
  door of house 191 (x -11928); the checker keeps one door per house. No shape change.
- Still outside: wild group to nearest chest 1407 (shipped floor 1436 is this original's own value): spawn points are
  placed by the build inside their areas; 29 units.

**Score** 93.46 to 93.52 % (roads 97.5 to 98.5; buildings 95.9 to 95.8: the post platforms are models the measure finds
no partner for; kept, they are the original's posts). **Walk** 142 steps, two of two (`cu_walk1.log`, `cu_walk2.log`).
**Installed** in `output/studio_play/rebuilds_root` with terrain materials. Desktop load check not possible:
"SDL_Init failed: The video driver did not add any displays". **Pictures** (`oymap render`, no display):
`output/studio_cal/mm6_oute3/cu_pics/before.png`, `after.png`.

## Roof words (2026-11-14, `openyamm-studio/build/oymap` of the nineteenth merge)

Backup `output/studio_cal/mm6_oute3/roofwords_backup/`; edited by hand (trial copy `roofwords/try/`).
- BlackSMW (the Knife Shoppe): the flat porch canopy replaced by the roof itself reaching 256 over the west front
  (`eaves: 256, eaves_walls: [w]`), soffit at 448 as the original's. The original's west slope is shallower (1:3 over
  384); the studio's hip keeps one pitch (1:1) and its north and south slopes meet in a ridge, not the original's flat
  top 128 wide. The soffit takes the trim (cbmxbrck; the original CedHWal1).
- BankE (the Savings House): the hip reaching 128 over the porch (`eaves: 128, eaves_walls: [e]`): its four slopes,
  band and soffit now as the original's faces (planes exact; soffit bemhwal against BemHwal1).

**Score** 93.52 to 93.53 % (buildings 95.83 to 95.94; other parts unchanged). **Pairs** 2 to 2. **Walk** two of two
(142 steps). Installed in `rebuilds_root` with terrain materials. **Pictures** to take: both roofs beside the original.
