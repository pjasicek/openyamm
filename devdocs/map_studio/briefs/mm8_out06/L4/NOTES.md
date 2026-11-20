# Shadowspire (mm8 out06.odm), outdoor rebuild

Scratch: `output/studio_cal/mm8_out06/` (scripts in `scripts/`, measures `cmp/cNN` and `cmp/cNN_old` by
`scripts/measure.sh`, walks `walks/`, pictures `pics/`, backups of the sketch before each scripted edit in
`r1_backup/`). Every oymap command `openyamm-studio/build/oymap` (outdoor batch eight from the lead's message on).

## Round one (2026-11-13)

### Scores (`oymap compare`, original against this project)

| Part | First sketch (c1) | End (c9) | End `--without rim` |
|---|---|---|---|
| **total** | **74.31** | **80.01** | **79.77** |
| heights | 86.57 | 88.47 | 88.41 |
| relief | 75.02 | 79.02 | 78.93 |
| cliffs | 93.89 | 93.02 | 94.90 |
| water | 81.56 | 94.75 | 94.75 |
| ground | 2.83 | 3.34 | 3.34 |
| roads | 97.18 | 97.18 | 97.18 |
| buildings | 59.07 | 80.30 | 80.30 |
| decorations | 95.12 | 95.28 | 95.28 |
| spawns | 98.41 | 95.24 | 95.24 |
| events | 90.00 | 100.00 | 100.00 |
| rim | 91.35 | 91.17 | (no weight) |

**Not within the outdoor band (90 %), and it cannot be with today's vocabulary:** the ground part (12 % of the
score) is 3 %. Shadowspire's ground is its own tile sets: `gdtyl` (the low tiles 1 to 12, grey dust, 57 % of the
land) and `gstyl` (grey stone, the east), with tar (`tartyl`, a water-flagged set) and its own water (738) and road
(774) rows (`tile_set_lookup [702, 738, 666, 774]`). The studio lays only mm8's fixed rows (grass 90, rock 342 ...,
water 126, road 414) and the measure compares by tile-set name, so no sketch can score the ground. With the ground
scored as the rest averages, the map would stand at about 90.6; the best possible total with ground at 3 % is about
88.4. Gap 1 below.

Walk: `playtest.yml`, 221 steps, passes two runs of two (`walks/final_1..2.log`) on the end project and the game
binary of 2026-11-13 evening; nothing by chance (positions from the build, poses fixed).

### What was scripted (the first sketch, from the original; not run again)

`scripts/first_sketch.sh` in order: `gen_skeleton.py` (project, plan, frame, a 32 x 32 grid of spot heights,
107 height points at the original's peaks and hollows the grid misses by 320 or more, water bodies from the
original's water and tar tiles, road centre lines from its road cells with their bed heights), `ground_zones.py`
(Ravenshore's, kinds read as gstyl = grass, tar = water), `describe.py` (s4c's, with one change: the 06n houses'
eave undersides no longer make them "hull"), `fix_first.py`, `gen_places.py` (scatter by 16-cell block and kind,
the three rune posts with their handlers, spawn areas from the original's packs and item points, timers and load
event), `actors_from_original.py`.

### Worked over (each a script in `scripts/`, its diff read)

- `water_a.py erode`: water outlines one cell in from the original's water tiles (81.6 to 94.8).
- `unit32.py`: grid in units of 32 (the town at 96, not 128).
- `hgreedy.py`: 31 more height points, only at the original's own peaks and hollows (heights +0.2).
- `r1_structures.py`: the Necromancers' Guild (hall 1024 x 3712 with battlements and a gable roof, two towers whose
  shoulders slope to a shaft 320 square that flares to 768 at 8576, caps), the Mad Necromancer's Lab (two
  five-sided wings, the six-sided hall with its pyramid roof, the passage walls and roof, the gate lintel, the
  causeway and steps), three pier decks at 264, the boat Smoke taken whole (`kind: model` from out06.odm, gangway
  model 81 runs house 481, the rest say "Smoke"), the cave's rock mouth as a doorway with a hood, the crypt's floor
  1280, the "Enter ...?" screens (371 guild, 372 lab). Buildings 59 to 80.
- `r1_events.py`: well (101), fountain water (104) with its stone "Fountain" (449), obelisk (150), the alchemist's
  kiosk redrawn (square turned 45 degrees on a plinth, roof of four tiers to a spike) with event 454 (Lloyd's Beacon)
  as a second door with the wall's own picture. Events 97.3 to 100.
- `r1_textures.py`: every town building gets its own models' texture roles (t19a/t19b walls, windows, posts,
  t19a05b roof, gn_mtl trim); describe left `wall` roles that the build laid as Ravenshore's thatch kit.
- `r1_doors.py`, `r1_shops.py`: doors on the original's walls (lab hall south, Umberpool north, Caverhill east,
  Mystical Mayhem north, Guild of Dark west), Supple Leather redrawn (describe's five boxes stood before its door:
  a cut-corner hall on a two-step plinth, the double door recessed), the rich halls' doors recessed.
- `r1_types.py`: the five poor1 houses as the original's (512 x 768, a steep gable with eaves 96; describe's tall
  middle box stood in front of the door).
- `r1_batch8.py`: the well's windlass `frame` (184, posts 64 to 24, beam 32); the alchemist's signpost carries the
  shop's event (`same_event_as`).
- `atmosphere.yml`: the original's daily fog. `scripts/gen_walk.py` wrote the walk from the build.

### Gaps (most harmful first)

1. **A map's own tile sets** (the whole ground part; the look of every picture): Shadowspire's gdtyl dust, gstyl
   stone and tar pools, its water row 738 and road row 774. The rebuild lays dirttyl/grastyl and blue water, so the
   tar pools are water and the grey wastes look brown and green. Field: `ground[].material` naming any tile set
   of the world (`gdtyl`, `gstyl`, `tartyl`) and a project word for the four rows (`tile_sets`), with liquids by set.
2. **Ground mist and the sky theme**: `out06_mist.scene.yml` (a grey-green mist layer) and the `necrotic` theme
   keyed by map name in `engine/rendering/sky/sky.yml`; the rebuild has neither (pictures: no haze). Fields:
   atmosphere `mist`, `sky_theme`.
3. **Pinnacles with sheer sides** in the east (towers of rock to 3840 dropping straight to 0): points are cones and
   the measured cliff lines (Ravenshore's `cliffs.py`, tried as variant `cl1`) scored lower, so the grid and points
   say them; heights 88.5, relief 79. A word for a column of rock (a closed cliff ring with a top height) would.
4. **Gable ends reaching past the end walls** (the poor1 houses' roofs overhang their gable ends by 160, with a flared
   skirt at 288); spike finials on almost every 06n roof (gn_mtl spikes); the pointed arch of the guild's gate;
   the rich halls' arched doorway (said as a recess). Fields: `gable_overhang`, a `finial` on a roof, an arch door.
5. Tar as a liquid (gap 1), the lab's passage as an arch (said as a lintel over the causeway), the causeway's solid
   sides (a bridge on piers).
6. Many 06n house types are still describe.py's boxes (med2, med3 with cut corners as three boxes, magic shops,
   the bank's roof on posts, the temple's front part 06n_temple_N_1 missing). Not reached this round.

### Tool defects

- `outdoor_ingame.py` runs `oymap build <project>` without `--out` (the build lands in the brief); `scripts/pics.sh`
  works round it with a scratch copy of the project.
- `scripts/variant.sh` of mine copied the L4 over a variant folder of the same name (my fault, lost one run).
- `climb` on a plinth part refuses 88 (more than 64) without saying which height per step works; two parts of 44.
- describe.py (s4c) writes identical stacked parts (the alchemist: three identical boxes, faces in one plane) and
  parts standing in front of doors (poor1, Supple Leather); its hull test calls every 06n house "other".

### Pictures

`pics/p1/diff/` (20 views of the town and landmarks, first sketch), `pics/t1/diff/` (61 interactive things, before
the shop and texture passes, edge agreement 0.604), `pics/t2/diff/` (the same 61 at the end). Worst at t1: views
whose camera stood in a neighbouring roof (House Arachnia) and the kit thatch walls (fixed by `r1_textures.py`).

### Unsure

- Events 102 and 103 (two more wells) have no faces in the original: not built.
- The original's spawn group 10 is made hostile on load (event 4); areas have no group word, so the load event runs
  but names no spawned group.

## Round two: the user's 10 places (2026-11-13)

The user walked the play root and sent 10 poses. Each was taken in both maps from the same camera
(`output/studio_cal/mm8_out06/user10.yml`, pitch in degrees): before `pics/u0/`, after `pics/u2/` (`diff/NN-uNN.png`
side by side with edges). The models at each pose were found by rays from the camera through the original's faces
(`scripts/u_hits.py`) and dumped face by face (`an/u/m*.txt`, `an/u/w*.txt` in each building's own frame,
`scripts/faces.py`). Every change is in `scripts/r2_user.py` (numbers from those faces; backup of the project before
it: `r2_backup/`; tried first on a scratch copy by `scripts/r2_try.sh`). The walk was written again from the build by
`scripts/gen_walk.py` (doors moved: Mystical Mayhem, Guild of Dark, the weaponsmith, the training hall, the tavern,
House Umberpool); its steps are otherwise the same.

### Scores (`oymap compare`, the studio binary of this evening)

| Part | Round one (c10) | Round two (c11) |
|---|---|---|
| **total** | **91.21** | **91.52** |
| total `--without rim` | 90.95 | 91.25 |
| heights | 88.49 | 88.55 |
| relief | 79.04 | 79.08 |
| buildings | 80.31 | 82.27 |
| others | unchanged | unchanged |

Pictures at the 10 poses: edge agreement 0.621 before, 0.720 after (`pics/u0/pixels.json`, `pics/u2/pixels.json`).

### The 10 places

| Pose | Model (original) | What differed | Done / missing word |
|---|---|---|---|
| 1 | 06n_magic_N, _N_1 (Mystical Mayhem) | three overlapping boxes, the door on a blank north wall (no door bay listed), no entrance, no plinth or spikes | one hall with cut corners (outline from the faces) on a green plinth 16, a recess 512 wide and deep under the roof with the double door at its back, hip in one ring (144 in, 96 up) to a flat top, two spikes (obelisks), sgMAGIC on the front corners. The same for its twin Guild of Dark (06n_magic_W, turned west, sgSPELL). The recess narrows twice by 45-degree cheeks (word: a recess of several widths, as New Sorpigal's SLuckN) |
| 2, 3 | 06n_alchemistW, SignPost_W (Wolves' Bane) | plinth a stepped box with kit windows; board centred on its post | plinth 16 without windows and a skirt sloping 48 in to the kiosk (`taper`); the signpost as the original's: a post 32 with an arm to the west and the board under it. The original's two door steps not said |
| 4 | the east path's ledge (terrain) | the path rose into a rounded hill; the original's ledge at 1280 stands under a sheer wall to 2784 | five height points at the original's nodes (84..86, 87 at 1280; 87, 87..88 at 2784, 2624). The wall is still a grid slope, not sheer (round one's gap 3: a column of rock) |
| 5 | 06n_tav_S, _S_1 (Black Company) | the floor on the ground, the court a flat yard, the middle part ran through both wings (coplanar) | base course 128 (`plinth`), the middle part between the wings, the original's eight steps of 16 and a landing at the door, sgTvrn on the wings, four spikes. Treads drawn in the riser texture: stairs ignore `textures.top` (tool defect below). One roof over the three parts with a flat top not said |
| 6 | 06n_armor_S, _S_1 (Supple Leather) | plinth tiers grey with kit windows, too narrow | tiers at the original's offsets (walls, 32, 128, a slope out to 224), tops t19a05a, no windows, three spikes. The steps before the door and the front's notch not said (outlines are convex) |
| 7 | 06n_weap_S, _S_1 (Blooded Daggers) | three boxes, no plinth, no signs, spikes or pyramids | one cut-corner hall on a plinth 32 (t19b11a, top t19a05a), frieze 48, eaves 32, hip with two spikes, sgWeap either side of the door, eight pyramids on the plinth. The plinth's front notch (128) and the eaves' edge band not said |
| 8 | 06n_stableW (Guild Caravans) | no corral, no sign | the corral as a part 16 high with a hole (the ground rail) and a `railing` 112 up on corner posts; the sign hanging from an arm on its north-west post (`same_event_as` the stable). The original's posts run above the rail to 352 (word: railing posts taller than the rail) |
| 9 | 06n_training_S, _S_1 (Assassin's School) | one storey 256, door at the ground in a plain wall, no steps | block 768 of two storeys (t19b below, t19a windows above), pyramid roof with a spike, the double door 128 up in a frame part over four steps of 32 and a landing, sgTRAIN over it, four corner pyramids. The steps' sloping cheek walls not said |
| 10 | 06n_rich2N (House Umberpool) | one plain box, no window row, door in a recess | base course 64, the upper storey with its row of windows over the whole footprint, the front wall with its gate and the open hall behind it, two steps to the door, hip with eaves 64. The gate is a pointed arch (said as a lintel half-way up it; word: a pointed arch opening) |

### Faces in one plane (z-fighting), outdoors

The studio's coplanar check (`core/Coplanar`) runs on indoor builds only. `scripts/coplanar_odm.py <export.json>`
does the same on an exported ODM: drawn BModel faces (not invisible) in one plane within 1 unit, facing the same way,
overlapping more than 8 square units (Sutherland-Hodgman in the plane), within a model and between models.

| | pairs facing the same way |
|---|---|
| the original out06.odm | 7 (the boat, a dungeon entrance, a dock) |
| round one's build (c10) | 904 |
| round two (c11) | 36 |

Removed: 20 parts that were exact copies of another part of the same building (describe.py's med2/med3 and others:
two or three identical boxes, 72 pairs on each med3); the magic shops', weaponsmith's and training hall's boxes
(one outline part each now); six L-shaped houses and the crypt whose parts ran through each other along a shared
wall (now shortened to meet: buildings 7, 8, 10, 14, 32, 36, 44); the lab's two court parts inside its wings (their
T01A12C walls are now the wings' own inner walls); the tavern's middle part; the pier decks (now ending at the head's
edges). Left, all the studio's own geometry (tool defects below): 16 on the corral's railing, 2 on each wall sign
and signpost, 2 on each house with a gable roof and eaves 96 (5, 6, 12, 15, 45), 1 on the boat taken whole (the
original's own). 247 pairs face opposite ways; they are faces inside closed parts where parts meet (a hanging part's
underside on another's top) and are not drawn against each other.

What a studio check needs outdoors: the same as the indoor one over the built ODM's BModels (all models together,
since separate structures overlap: the pier decks), skipping invisible faces, reporting the structure and part ids
of both faces; ideally also a check that warns when two parts of one building are identical or share a wall plane.

### Walk

`playtest.yml`, 221 steps (written again from the build by `scripts/gen_walk.py`: six door poses moved), passes two
runs of two (`walks/r2_1.log`, `walks/r2_2.log`). Installed in `output/studio_play/rebuilds_root` with its terrain
materials (`outdoor_materials.py --build`); a desktop run loads it (`pics/load_r2.png`, `pics/load_r2.log`).

### Missing words (round two)

- A recess of several widths (the magic shops' entrance narrows by two 45-degree cheeks; New Sorpigal's SLuckN).
- A pointed arch opening in a wall (House Umberpool's gate; round one's guild gate).
- A sheer column or wall of rock (the east path's ledge; round one's gap 3).
- Railing posts standing higher than the rail (the corral's posts to 352 over a rail at 224).
- A convex-only outline cannot say a front notch (the weaponsmith's plinth, the armourer's steps); one roof over
  several parts with a flat top (the tavern); the eaves' edge band apart from the frieze (the weaponsmith).

### Tool defects (round two)

- `kind: stairs` without `ramp` ignores `textures.top`: every tread is drawn in `wall` (core/OutdoorThings.cpp
  `raiseStairs`; only the ramp reads `top`). Shows on `thing:tavern_steps` and `thing:training_steps`
  (`oymap export output/studio_cal/mm8_out06/build/calib_shadowspire.odm`: 41 faces, all t19b10a).
- A part's `railing`: the rails of two walls overlap at each corner and their tops lie in the plane of the corner
  post's top (16 pairs on `thing:building_33`'s corral, `scripts/coplanar_odm.py an/b12.json --list`).
- Wall signs and signposts: the picture is drawn 1 unit in front of the board's own face of the same size (2 pairs a
  board: buildings 39, 40, 41, 42, 43, `shop_sign_1`, `stable_sign`).
- Gable roofs with `eaves` 96: the gable's edge piece overlaps the gable wall at the ridge (56 square units, 2 pairs
  on buildings 5, 6, 12, 15, 45).
- No outdoor coplanar check in `oymap build`/`audit` (above); this round's count is `scripts/coplanar_odm.py`.

## Round three: the user's places A to E (2026-11-13)

Poses in `output/studio_cal/mm8_out06/user_r3.yml` (and `lab_views.yml`, `cave_views.yml`, `d_views.yml`; all in
`all_r3b.yml`). Before: `pics/r3a/`, `pics/r3lab/`, `pics/r3cave/`; after: `pics/r3after/` (`diff/NN-name.png`, the
original left). Every change is in `scripts/r3_user.py` (numbers from the original's faces; tried on scratch copies
by `scripts/r3_try.sh`); backup of the project before it: `r3_backup/`.

### Scores (`oymap compare`)

| Part | Round two (c11) | Round three (c12) |
|---|---|---|
| **total** | **91.52** | **92.10** |
| total `--without rim` | 91.25 | 91.83 |
| heights | 88.55 | 88.63 |
| relief | 79.08 | 79.16 |
| buildings | 82.27 | 86.05 |
| others | unchanged | unchanged |

Faces in one plane facing the same way (`scripts/coplanar_odm.py`): 36, as before (all the studio's: railing
corners, signs 1 unit off their boards, gable eaves at the ridge).

### The places

| Place | Model (original) | What differed | Done |
|---|---|---|---|
| A | d20out_S, _S_1, _S_2, _S_3 (the Mad Necromancer's Lab; the user's "dragon cave" poses stand in its passage) | a roof slab over the whole passage and a lintel; straight inner wing walls; one hall wall texture with kit (thatch) posts and a window over the door; a causeway 1216 wide from the shore | the passage open to the sky under three arch ribs 64 deep (1312 at the walls to 1504 over the middle), the first the gate on two posts from the tar; the wings' inner walls step out under the third rib (each wing two convex parts); the hall in four rows of panels (T01A12C/D, the door row with the original's bays, T01A01C, T01A12B) under the pyramid; the walk as the original's: eight steps of 32 between cheek walls, a deck 448 wide and 64 thick at 1056, a ten-sided landing, a strip 256 to the door; the land's notch at the steps' foot |
| A (the dragon cave proper) | d49out_W, _W_1 (Yaardrake's Cave) | a box with a flat door on a smooth hill (the hill a cell west of the original's) | the two models taken whole (no form says a rock mound with a mouth); the land under them as the original's by three `ridges` (shelf 2144 under the mound and mouth, back edge 2880, the cliff under the mouth) |
| B | 06n_magic_N (Mystical Mayhem) | the recess floor flickers between the plinth's top (t19a05a) and the hall's underside (t19a05b) at 112 | not changed: a studio drawing source (below) |
| C | 06n_rich2E (Caverhill Hall) | the kit's (Ravenshore's) door t14a03 in a recess of one box | the original's form (its twin House Umberpool's, turned east): the front wall with its gate, the open hall, base course 64, the house with door t19b03b, two steps, the upper storey with its window row; also the Blood Bank's kit door (t19b03b now), Umberpool's gate lintel ends (kit window), Supple Leather's cut walls (kit window t19a04b) and the Necromancers' Guild hall's kit thatch row |
| D | 06n_training_S, _S_1 (Assassin's School) | the roof a hip with a ridge east-west (a box's default inset 112), its spike off the ridge: not symmetrical | a pyramid (`hip: 416`) to one apex over the middle, as the original's |
| E | Dock_W_2 (the pier) | a deck in a trough of kerbs 64, ending in the air over the shore | a flat deck (rails flush), the ramp down to the shore (192), the gate frame of two posts and a beam over its land end (`kind: wall` with a gate) |

### Walk

`playtest.yml`, 233 steps: now walks up the lab's steps and deck to its door on foot, and into Yaardrake's Cave's
mouth on its shelf before clicking the black face; Caverhill's door pose moved. Passes two runs of two
(`walks/r3b_1.log`, `walks/r3b_2.log`). Installed in `output/studio_play/rebuilds_root` with its terrain materials;
a desktop run loads it (`pics/load_r3.png`).

### Gaps (round three)

- **A cave mouth built into the terrain** (Yaardrake's Cave; the same kind on Emerald Island and Regna): no word;
  the models taken whole. Word defined in the lead's message (`kind: cave_mouth`).
- An arch rib's curved top (three facets each side) said as one slope; the gate's carved boss not said.
- A concave outline: the wings' 64 upright where the passage widens lies 12 inside the slant (dropped).
- The pier gate's knee braces; the hall's pyramid apex is 64 east of the outline's middle in the original.
- A pointed arch opening (Caverhill's gate, as Umberpool's): a lintel half-way up.

### Tool defects (round three)

- **A part's underside under its recess** (B): a hanging part (`bottom` > 0) with a `porches` recess keeps its
  underside over the whole outline, recess included; on a plinth part whose top is at the same height the recess
  floor is two faces in one plane facing opposite ways, and the game draws both (it does not cull outdoor faces):
  `thing:building_41` and its twin `building_43`, faces t19a05a up and t19a05b down at z 112
  (`oymap export output/studio_cal/mm8_out06/build/calib_shadowspire.odm`). The underside should leave out the
  recess; `coplanar_odm.py` (and the studio's check) count opposite-facing pairs as harmless, which they are not
  where both are seen.
- `kind: stairs` refuses exactly 45 degrees (8 x 32 over 256, the lab's original flight): the line is 257 long.

## Roof words (2026-11-14, `openyamm-studio/build/oymap` of the nineteenth merge)

Backup `output/studio_cal/mm8_out06/roofwords_backup/`; edits by `output/studio_cal/mm8_out02/roofwords/edit.py notch2`
and `output/studio_cal/mm8_out06/roofwords/edit_tavern.py`.
- Blooded Daggers and Blades: the plinth's front notch, cut back 128 at x 584..1096 (measured on the original; the
  older note said 576..1088), one flat top over the outline.
- Black Company (06n_tav_S, _S_1): the middle and both wings as one U outline under one hip roof (roof 112, eaves
  16), as the original's single roof; walls, door (wall "4") and both signs carried over bay for bay. The original's
  ridges are flat 64 wide and its wing ends steeper (1:1); the studio's hip rises to a ridge line at one pitch. Its
  floor stands 32 below the original's (as before).
- Not done: Supple Leather's steps before the door (a stepped landing out of the plinth, not a roof word).

**Score** 92.10 to 92.11 % (buildings 86.06 to 86.13; other parts unchanged). **Pairs** 3 to 3 (1 as the original).
**Walk** two of two (229 steps). Installed in `rebuilds_root` with terrain materials. **Pictures** to take: the
weaponsmith's notch, the Black Company roof, beside the original.

## Supple Leather's roof (2026-11-14, the gate pictures)

Backup `output/studio_cal/mm8_out06/regress_backup/`. The house beside Blooded Daggers (06n_armor_S, _S_1) had its
roof in the plinth's teal t19a05a and a ridge at 680 that buried its three spikes (496 to 752). Not the roof words:
the backup before them builds the same model, and the roof has been teal since the first measured pass (pics/t2,
2026-11-13 21:00): the hall gave no roof texture of its own, so it took the building's (t19a05a), and its
`roof_height` 224 stood 120 over the original's ridge at 560. Now the hall's roof is t19a05b and 120 high (ridge 560,
the original's). The other three rebuilds checked by the highest sloped face of every building against the original
models under it: none has its roof in a plinth's texture, and no spike stands buried.

**Score** 92.11 to 92.12 % (buildings 86.13 to 86.17; other parts unchanged). **Walk** two of two (229 steps).
Installed in `rebuilds_root` with terrain materials.
