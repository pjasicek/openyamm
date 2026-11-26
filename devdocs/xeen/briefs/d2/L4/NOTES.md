# D2 Sprite Forest and Ogre Pass, L4 (2026-11-20, A6)

Built from the approved L1 mock-up (`../L1`, board `level_generation/xeen_art/phase3/d2/board_d2.png`) with the
decider's changes D-23 (and D-25 for the troll holes and DD-13's east gate; `devdocs/xeen/DECISIONS.md`). Map file
`xeen_d2.odm`, map_stats 9109, `world: xeen`, `continent: 7` (Darkside: sky `xeendark1` by the continent, A3's Lua the
failing-sun stages), music 33, treasure 3, lock 6 / trap 3, no weather. Installed in `assets_dev`, baked.

## How it is written

Every project file of L2-L4 is written by `output/studio_cal/d2/tools/gen.py` (L1 stays the approved mock-up). Run
`output/studio_cal/d2/v.sh`: generate, fmt, validate L2-L4, build into `output/studio_cal/d2/build`, the census
(`tools/measure.py`, adapted from A5's X4 `measure_x4.py`: D-20 POIs, first fights, the parley fire's and the troll
returns' distances, the 6,000 rule), X1's `measure.py` (quiet land) and `dress_check.py`. Then
`present/install_bake.sh` (install, terrain weights, the bake under `output/studio_cal/a6_bake.lock`, stale check),
`tour_only.sh <set> <label>` (engine screenshot tour after a bake, HUD off; sets `l3`, `a` in `tools/tour.py`),
`walk.sh <scenario> <log>` (headless, `--world xeen`), `present/redo_minimap.sh` (X1's scripts), `final_tests.sh`
(walk twice, hostility, final tour). `tools/gen_walk.py` writes `playtest.yml` from the build;
`tools/gen_hostility_d2.py` writes `playtest_hostility.yml`. The generator asserts that every A3 hook with `map: D2`
is used, and checks D-23's and D-25's distances (no marker within 1,500 of the parley fire, none within 2,500 of a
village door, every troll circle at least 512 from each DD-11 return spot).

Live checks (X5's `X3_LIVE` pattern): the west edge is live when `worlds/xeen/maps/xeen_d1.odm` exists, the east edge
when `xeen_d3.odm` exists (both live since the 19:10 install), each dungeon door when its BLV exists AND A2's
map_stats row names it (without the row the game cannot resolve the map: DD-09 and DD-11A-C were installed before
their rows). Live since the 19:55 install: every way in (DD-06, DD-09, DD-10B, DD-11A-C, DD-13's two gates). Overrides: `D2_D1_LIVE=1`, `D2_D3_LIVE=1`, `D2_DD09_LIVE=1` and so on. DD-13's east gate takes
A7's explicit inside point from the constant `DD13_EAST_INSIDE` in gen.py (None until A7 gives it; D-25 b).

## What was built

- **Land**: the forest floor 920-1,100 falling gently to **the world rim at y 104** (D-23: a cliff of about 940 to
  the stars, water at 0, rocks along the lip, stacks below); the Gemstone foothills 1,250-2,800 rising north to the
  **Gemstone Range** (crags 3,000-4,400, its foot at y 19-22 so it shows from the pass and the adit); the **Gemstone
  Spur** along x 80 (crests 3,000-3,700, broken into tops) with **Ogre Pass's saddle** at 2,050; the Whispering Glades
  1,150-1,500; the east descent to the D3 road at 1,300; the Southern Woods 1,000-1,500.
- **The Glimmerbrook** (D-23): rises at the range's foot (52, 21), runs under the caravan road (log bridge) and the
  forest track (footbridge), past the great tree, and falls off the rim at x 58 (**Sprite Falls**, a waterfall
  structure to the stars). It touches no map edge.
- **Sharla's treehouse village** (A4's 4551-4555), route (a): five giant trunks, each a 12-sided foot (radius 360-440)
  with root buttresses on every wall but the door's, a round foot door (`tavsmdr`) with a standing torch (`dec06`) each side,
  a tapered trunk (taper 0.72) 940-1,150 high in the new bark `xdbark`, a plank deck round it at 640-720 with a
  railing (none on Sharla's), shipped crowns on top (`tree69`, `tree62a`, `tree12`, `tree10`, sunk into the trunk's
  top, two smaller ones beside); three rope walks (bridges with rope railings) between the other four decks;
  **only Sharla's stair** climbs (to her deck at 672 with **the treehouse chest**, q-d10.treehouse); a ring of caps on
  the green. **Sharla's stair** (A6's review) is an open plank flight winding round the trunk outside the deck's rim:
  a `walkway` on [x, y, z] points (a ring of 900 round the trunk, 77 degrees of arc from the north-west foot at z 996,
  a level landing half way), kerbs as stringers, posts to the ground, open underneath, a plank handrail on the posts each
  side (two thin walkways). Its head (`thing:sharla_stair_head`) is a short level landing beside the flight's top end
  running in onto the deck, its own walkway without piers or kerbs (a walkway stands piers at every point of its line:
  the old stub's two posts stood up through the deck's edge), 2 over the deck. Doors face the green (turned plots, not compass axes).
- **The great tree of Bark**: a 16-sided trunk 1,520 across with root buttresses, 448 foot + 2,600 tapered trunk,
  **DD-09's door** in its north foot (q-d9.bark_door, bark_key 12342), caps round its roots. **S's crown**
  (`xeen_greatcrown`, decoration row 4001, one placement at the trunk's middle, raise 2,848 = the trunk's top less 200,
  z 3,840; about 4,650 across, its top about 6,500 over the ground). The studio writes no facing for a decoration (a
  structure's `turn` on a decoration is dropped silently), so the trunk is turned instead: plot `turn` 168.75 (180 less
  half a facet) puts the trunk's 16 corners at 0, 22.5, ... degrees, on the crown stub's (measured on the built BModel;
  the door now looks 11.25 degrees west of north). Nothing else stands under the crown (caps and the bowl only).
- **Nibbler's Hollow** (4556): a hollow stump with buttresses under the great tree, its door to the glade; his bowl.
- **Ogre Pass**: the west fort (knoll 2,000) and the east fort (knoll 2,150), each a log palisade with battlements, a
  blockhouse and a beacon fire, **DD-13's gate** in the palisade (west looks south, east looks north); **their charred
  ruins** (a ruined blockhouse in `vlcwl2`, stumps and burned-out fires) hidden at load and swapped in by load events
  on q-d11.west_burned / east_burned (the gate doorway stays: DD-13's way in stays open); Graalg's **parley fire** in
  the saddle (fire, ring of stones, his log seat, bones); Kramer's wrecked strongbox below the west fort.
- **Graalg's ogres** (A2's rows, A2's relations decide their mood, the map carries no hostility of its own for them):
  22 pass ogres (11066 Ogre ×14, 11067 Brute ×6, 11068 Chief ×2: the two fort yards of 8 and two road groups of 3),
  **Graalg** (11064, talking actor 5108) and two **Graalg's Brutes** (11065) at the parley fire.
- **Troll country**: three troll holes (pits, q-d13.troll_holes, DD-11A/B/C), bones, a dead adventurer's pack (chest);
  the **Forbidden Fruit** hut (A6's review: a small hut of Ravenshore's boulder stone between dark timber posts under
  Darkside's mossy slate `xlslatemos`, its front open east to the brink path; a plank counter along its south wall
  with the four fruits as food bowls, each eaten once: +2 to a stat and a condition; a pair of barrels by the wall,
  the label at the counter's end);
  **the Brink** (the sprites' lookout bench by the falls); the Dewdrop Spring (+100 SP); the fairy ring (+200 HP, cure
  poison); a woodcutter's box; a cairn at the rim.
- **The Southern Woods**: **the Southern Tower** (DD-06; Castle Ironfist's seamless ashlar `hcwall` under `xtslate`, no
  windows; q-d19.tower_door with its NO THIEVES fail line; a brass plate), the thieves' drop under a stump, the **Shrine of the Elements** (four standing
  stones, +5 Fire, Air, Water, Earth resistance once), the **Leprechaun's pot** (a ring of rocks at the rim, Perception
  4), the Whispering Stone.
- **Foothills and pass**: the **obelisk** (obelisks.d2, BENEATH, the seamless ashlar `cswl128`), **DD-10B's adit** (a timbered doorway in
  the foothill rock), the crystal seam (Might 30), the genie's lamp on its ledge, the Glimmer Pool (+20 Luck), the
  milestone on the Sandcaster road, crystal clusters on the range's foot and the spur.
- **Dressing**: the Sprite Forest (A6's review: denser and darker round the village, the great tree and the troll
  holes) a stand of the dark crowns `tree60a`, `tree62a`, `tree12`, the fir `tree30`, `tree61a` and a few `tree10`,
  30 per 100 cells at spacing 1.05 (west), 28 (troll country), 26 round the great tree's glade and in the Southern
  Woods; undergrowth `plant32` (dark shrub), `plant05` and `bush03` (ferns), a few stumps `plant47`, clusters of caps
  `mushrm01-03` (S's glowing mushrooms when they exist); `tree25`, `tree62a`, `tree12` thin in the foothills and the
  pass; `rock16`, `6rock07`, crystals `crys5`, `crys6`, `crclstr`. Stands leave clearings round every set piece and
  way in (the troll holes' 4 by 4 cells, the great tree's 9 by 10).

## Monsters (A2's rows)

- Slots (project.yml = A2's live row 9109 after A2's kill-XP recount, 25.5k kill XP): wolves Dif 3 [2, 3] w40,
  trolls Dif 3 [2, 3] w35, `Xeen Dark Sprite` Dif 3 [2, 3] w25 (Gorgon 11534 / Elder Gorgon 11535, the Queen 11536 the
  rare third). The change left the built ODM, scene and Lua byte-identical (no reinstall).
- 51 markers in five areas: E1 foothill wolves 13, E2 wild sprites 4 (west glades: the first fight from D1) + 6
  (Whispering Glades), E3 trolls 14, E5 woods wolves 14 (the first fight from D3). At [2, 3]: 127.5 + 22 placed =
  **150 hostiles at load** (149.5; A2: kill XP 1.03). The eight village sprites are A2's village
  rows 11537 ×5, 11538 ×3 (faction `xeen_sprites_village`: friendly, hostile after 113203).
- Events: `evt:sprites_slain` (timer, once: every village sprite dead runs q-d10.sprites_slain); the two fort swaps
  (load). q-d10.sprites_hostile and q-d11.pass_ogres are A2's relations (no map Lua).

## Measured

- Build (19:10 install): 13 buildings, 3,559 entities, 51 spawn points; BModels 49, 3,908 faces, 7,840 triangles
  (S's crown: LOD triangles 14,832 / 7,480 / 2,528 / 2, one placement, in place of 16 `tree69` crowns). Earlier build
  (oymap 17:26:09, after A6's review): 13 buildings, 3,578 entities, 51 spawn points; warnings: the brook laid 2 cells wide and
  following the land (no level), 27 terrace nodes in water, the three pits' corners between nodes, the waterfall's cut,
  road cells over the brook (the bridges carry them), the "not built yet" notes.
- `oymap audit --reach --solve --dressing` (`output/studio_cal/d2/run/audit_final.txt`, 19:10 install): 0 errors, 2 warnings (the
  waterfall's own faces, below). `fmt --check` clean. `dress_check.py`: no barrels or crates; the lanterns beside the
  village doors are listed as "before" a door by X1's script (25 out, 260 aside), the audit passes them.
- Size: 128 cells, playable square [19, 19, 90, 90]; relief 920 (the forest at the rim) to 4,400 (the range); the rim
  0 below.
- Hostiles 150 (see above); **quiet central land 0.77**; encounter regions [8, 5, 5, 3, 3, 3, 1, 1, 1, 1] (the denser stands split the largest).
- **POIs 29** by the D-20 census (bound events chained within 400, one set piece one spot; residences, NPCs, Graalg,
  the road-end signs and event-less landmarks out). Chests 5 with reasons (Kramer's strongbox, the dead adventurer's
  pack, the thieves' drop, the woodcutter's box, the treehouse chest) and the pot of gold (a search, not a chest).
- First fights: from the D1 arrival (21, 60) 4,864, from the D3 arrival (106, 44) 4,438, from the new-game start 4,789. Town buffer: nearest hostile to a
  village door 4,990.
- **Parley fire**: nearest hostile (pass ogre) 3,032 (D-23: ≥ ~1,500). From the west the caravan road passes one road
  group (66, 39.5) before the fire (the west fort's yard stands 3,000 north of the road behind its palisade); from the
  east one road group (94, 40.5).
- **D-25 troll returns**: nearest troll marker to the DD-11A return spot 1,749, DD-11B 2,414, DD-11C 1,856 (≥ 512).
- 6,000 rule: farthest land 5,798 (cell 85, 103); land more than 3 cells from anything 0.13.
- BModel faces 3,951 (audit; 3,679 before A6's review: Sharla's open stair with its posts and handrails, the hut).
- Textures: **1 new** (`xdbark`, registered in `source/textures.yml`, master in
  `assets_source/worlds/xeen/textures_x4/`), the towers kit's `xtslate`, the Darkside kit's `xlslatemos` and MM8's
  t06 boulder set (`t06a01`, `t06a10`: the fruit hut). Shipped: `tavsmdr` (MM6, the round doors),
  `t68a13mm` (MM8, decks, stair, rope walks, palisades), `swpcnr2` (MM6, the falls' rocks), `hhp2rf` (MM7, the
  blockhouses' thatch), `vlcwl2` (MM6, the charred ruins), `hcwall` (MM6, the tower), `cswl128` (MM6, the obelisk),
  and the kits' panels (`hhm1b2le/re`, `hhm3ch`, `chb1`, `7gt002a/b`, `trim2_32*`).
- Texture fit (the user's rule, 2026-11-20), fixed in the 19:10 install: `hkm3b` (a one-storey panel, a skull frieze
  over a bone band) tiled up the tower and the obelisk in bands: now seamless ashlar; the castle kit's rubble `ch1b1`
  stood in the tower's window bays and the strip over its door: the tower's walls, trim and windows all `hcwall`, no
  windows (a round part's window bay is two 256-high faces 145 wide, so the arrow slit `xkarrow`, 128 x 256, tiled in
  it: a studio word to fit a window picture to its bay is missing); the timber kit's window wall `hhm1bw` (a house wall
  with a window) stood in the strip over every trunk door and its trim band `trim2_32a` lay across the feet's flat
  tops: both bark now. Kept: the trunk doors `tavsmdr` (one arched plank door in its own stone frame per door face),
  the dungeon ways in (`7solid01`, the dark into-map face), the decks' planks, the bark.
- Double doors (the user's rule): D2 has none. The trunk doors are single arched plank doors 99-187 wide; DD-06's door
  (130), DD-10B's adit (256), DD-13's gates (320) and the pits are the plain dark into-map face `7solid01`, no wing
  picture. (The studio has `door.leaves: 2` for a building's door.)
- Walk (`playtest.yml`, 302 steps): every door of A4's six houses opens (the residences their person's talk), the great
  tree's door refuses without the bark key, Sharla's stair is climbed to her deck and the chest refuses while the
  sprites live; the robbery turns the village, the sprites die, sprites_slain is set and the chest gives two Energy
  Disks; the troll holes, the fruit, the brink, the fairy ring, the obelisk (dark_2), the adit, the seam, Kramer's box,
  both fort gates, Graalg's talk, the tower (refused, then with the key), the shrine, the genie, the milestone; a burned
  fort (113224 + 113222) turns every ogre on reload; the west edge to D1 (A2's travel row, 5 days) and back is walked;
  the east road's end sign. Results: see "Tests" below.
- `playtest_hostility.yml`: at load the 22 pass ogres hostile, Graalg's three and the village sprites peaceful, the
  slot kinds hostile; with friends (113221) the pass ogres peaceful (also over a reload); with a burned fort every ogre
  hostile; with the robbery (113203) the village sprites hostile.
- Bake (`present/bake_profile.json`, D1's Darkside sun: azimuth 300, elevation 38, sun 2.2, sky 0.4): installed,
  `stale_bakes.py` 0 stale. Minimap `icons_x2/xeen_d2.png` (X1's scripts). Terrain materials: D2's entry in
  `worlds/xeen/terrain_materials/world.yml` (grass shade [0.62, 0.73, 0.6], dirt [0.74, 0.7, 0.66]: darkened in A6's
  review); weights
  written; the liquid edges run on a scratch root changed no file (D2's shores use masks the world already has).

## Tests

**Session 10 install** (21:33 oymap; bake by `output/studio_cal/a6/install_baked.sh`): every dungeon door names its
entrance (D-37: `entrance:d2_trunk`, `d2_hole` x3, `adit`, `d2_west`, `d2_east`, `d2_door`, read from each BLV's
studio sidecar; DD-13's east gate now lands at A7's (7552, -160, 0)); AU's `xeen_fire_ignite` plays once at a fort
the first time D2 loads after it burned (map variables `west_fort_fire_heard`, `east_fort_fire_heard`). Audit
`run/audit.txt` 0 errors, texture fit 0; walk 2/2 (`run/walk_s10a.log`, `walk_s10b.log`), hostility 2/2
(`host_s10a.log`, `host_s10b.log`); D2 not stale; minimap redone.

**19:55 install** (bake `output/studio_cal/a6/bake_xeen_d2_195410`): DD-13's two gates and DD-10B's adit live (A2's
rows 9166, 9160); the trunk doors' lights are MM8's standing torch `dec06` (the lantern `dec07` has an indoor model
only and drew nothing outdoors), 384 aside of each door's middle just outside the root buttresses; one root cap moved
off the great tree's door line (dress_check: 0 doors with something before them). The walk (372 steps) goes in at
each gate and the adit and out again: DD-13's west gateway lands at (4096, 13824, 2017), its east at
(11776, 11776, 2049), DD-10B's mouth at (-15360, 16384, 1697). Logs `run/walk_i1.log`, `walk_i2.log`, `host_i1.log`;
audit `run/audit_final.txt` 0 errors; tour `pics/sheet_gates.jpg`.

**19:10 install** (S's crown, the trunk turned, Sharla's stair head, DD-06/DD-09/DD-11A-C live with their inside points,
the D3 edge, the east road cleared, texture fit), from `assets_dev` on build-xeen: see PROGRESS.md for the log names
(`output/studio_cal/d2/run/walk_h1.log`, `walk_h2.log`, `host_h1.log`), audit `run/audit_final.txt` 0 errors (the two
falls warnings), `towns.py --strict` exit 0, `stale_bakes.py` 0, minimap redone. The walk (351 steps) adds: through
DD-06's door with the key to (640, 1700) and out by its front door (event 17, the leave window) to (15872, -7680);
into DD-09 with the bark key to (0, -1920) and out by its trunk door (33) to (-11264, -6656); down each troll hole to
A7's point ((96, -32) / (96, -32) / (128, -64)) and out by its sod hatch to its return spot; off the east edge to D3
(prompt, OK) at (-22528, 10240) and back off D3's west edge to (21504, 10240). Tours: `pics/sheet_crown.jpg` (crown,
stair head, doors, east road), `pics/sheet_fit.jpg` (texture fit, the tower, the holes, the road's end).

Earlier:

From `assets_dev` with `--world xeen` on the 17:10:53 game, after A6's review fixes, their install and bake (oymap
17:26:09, bake `present/bake_175357`, `stale_bakes.py` 0): `playtest.yml` **2 of 2** (`output/studio_cal/d2/run/
walk_f1.log`, `walk_f2.log`: the walk now climbs Sharla's open stair point by point), `playtest_hostility.yml`
**pass** (`host_f1.log`), `tools/xeen/towns.py --strict` exit 0 (`run/towns_strict.txt`). A first walk pair failed at
the D1 crossing only because D1's agent had reinstalled xeen_d1.odm over its bake mid-run; rerun after D1's bake. Earlier: the walk failed twice on Sharla's stair (the walker came at it from the side; the walk now
lines up on the stair's foot), `walk_3.log` passed on the previous build.

## Original lines

| Line | Where | Source |
| --- | --- | --- |
| "Inside the hut you find a basket labeled "Forbidden Fruit"." | the Forbidden Fruit label | aaze0012 (C4) |
| "You realize that you shouldn't have eaten the coconut of confusion." | the coconut | aaze0012 |
| "Yuk! The plum of unconsciousness." / "Yuk! The pear of paralysis." / "Yuk! The orange of sleepiness." | the other fruits | aaze0012 |
| "Troll Hole.  Descend?" and "Enter the Ancient Temple of Bark?" | the pits, the great tree's door (A3's hooks) | aaze0012 |
| "In this treehouse there once lived many sprites, but someone murdered the lot of them. You find two energy disks." | the treehouse chest (A3's hook) | aaze0012 |

The fruit lines were changed after the bake: the rebuilt ODM was byte-identical (only the map's Lua changed), the bake
stays valid (`stale_bakes.py` 0), and the walk (2 of 2) and the hostility test were run again on it.

## Town feel exceptions

`town_feel.py --small` (`output/studio_cal/d2/run/town_feel.txt`): 19 figures outside the shipped ranges. The village
is five giant trunks round a green (D-23), not a town of houses:
- doors facing a compass axis 0.2, mirror partners 0.8: the trunks turn their doors to the green on purpose.
- door to nearest road 444, town cells of road 0.31, straight road run 768 / 1,024: one winding lane and a mossy
  green; no streets in a sprite village.
- services in town 2, enterable residences 3, service to service 5,946, farthest service 3,199: A4's d2.yml has two
  services and three bowers; the trunks stand far apart because each is 700-900 across with its deck.
- building to building (wall 1,880 / 2,067, middle 3,093 / 3,521): the same giant trunks and decks.
- thematic models in town 0, wells and fountains on the map 0 (the Dewdrop Spring and the Glimmer Pool are not counted
  as such), flat terrain share 1.0 (the village terrace), fringe/core 1.2 and farthest/core 1.2 (five trunks in one
  ring): the village's form.

## Dressing exceptions

- `geometry.coplanar` ×2: Sprite Falls' water face and its bank face meet in one plane over 57-67 square units (the
  studio's waterfall cut at the rim); not visible from the brink.

## Open items

- None of D2's ways in is waiting any more (19:55).
- Glowing mushrooms: shipped `mushrm*` caps stand in for MU-2's gap (S's glowing decorations when they exist).

## Words the studio lacked

- A decoration's facing: `turn` is in the schema for every structure but the build writes facing 0 for a decoration
  (OutdoorThings.cpp placeDecoration); the great tree's trunk was turned to meet S's crown instead. A1: write the turn
  or refuse it.
- A window picture fitted to a round part's window bay (once per face): the bay is two 256-high faces, so a 256-high
  slit tiles twice (the Southern Tower has no windows for it).
- Village sprites on decks: actors stand on the land only (none placed on the decks).
- A dungeon door's second arrival into one BLV (DD-13's two gates): A1's second-arrival word (D-25 b).
- `town_feel` has no form for a village of giant trunks (see the exceptions).

## Doors and arrivals for the other lanes

House doors (build.json; event ids from ids.lock.yml): Sharla's Treehouse 4553 (-19489, -10606, 992) evt 1; Light
Guild of the Treetops 4552 (-15401, -10236, 992) evt 3; Dewdrop Potions 4551 (-20622, -13079, 992) evt 5; Mossbell's
Bower 4554 (-15450, -13020, 992) evt 7; Thistledown's Bower 4555 (-17890, -15270, 992) evt 9; Nibbler's Hollow 4556
(-9685, -5888, 992) evt 11. Ways in and their arrivals (the dungeon exits come back to the arrival, facing away from the
door; MoveToMap direction east 0, north 512, west 1024, south 1536):
- DD-09 door in the great tree: door (-11337, -6934, 992) evt 13, looks 11.25 degrees west of north (the trunk turned
  to S's crown); into DD-09 at (0, -1920, 0) facing north (512); arrival (42, 77) = (-11264, -6656, 992), north (512).
- DD-13 west gate: into DD-13's start (0, -64, 0) facing north (512); east gate: into A7's (7552, 32, 0) facing south
  (1536). DD-10B adit: into A8's (0, 192, 0) facing north (512).
- DD-13 west gate: dark face (4096, 14328, 2192) evt 49, looks south; arrival (72, 37) = (4096, 13824, 2016), south
  (1536).
- DD-13 east gate: dark face (11776, 11170, 2342) evt 52, looks north; arrival (87, 41) = (11776, 11776, 2048), north
  (512).
- DD-06 Southern Tower: door (15937, -8305, 1056) evt 20, looks north; into DD-06 at (640, 1700, 0) facing south
  (1536); arrival (95, 79) = (15872, -7680, 1056), north (512).
- DD-10B adit: dark face (-15360, 17272, 1860) evt 44, looks south; arrival (34, 32) = (-15360, 16384, 1696), south
  (1536).
- DD-11A-C into A7's points (96, -32, 0), (96, -32, 0), (128, -64, 0), facing east (0).
- DD-11A pit (61, 76): face (-1536, -6144, 1040) evt 32; return spot (60, 76) = (-2048, -6144, 992), facing west (1024),
  512 from the pit's middle (about 256 from its lip).
- DD-11B pit (71, 84): face (3584, -10240, 1008) evt 33; return spot (70, 84) = (3072, -10240, 960), west (1024).
- DD-11C pit (68, 98): face (2048, -17408, 976) evt 34; return spot (67, 98) = (1536, -17408, 928), west (1024).
- West edge (D1, live): D2's west start (21, 60) = (-22016, 2048, 992) facing east (0); the road crosses x 0 at y 60.
  The tests' start and the respawn: `entrance:forest_edge` (22, 60) = (-21504, 2048, 992), east.
- East edge (D3, live, 5 days, A2's edge span): off D2's east edge to D3's west start (-22528, 10240, 1312) facing east
  (0); D3's west edge to D2's east start `entrance:east_road` (106, 44) = (21504, 10240, 1312) facing west (1024). The
  road's last stretch (104.5-128, 42.5-45.5) is kept clear of trees.

## What the user should look at when playing

- The village from the lane and from the green: the trunks, the doors with their torches, the rope walks; climb
  Sharla's stair to her deck.
- The great tree from the glade and from the village (S's crown).
- Ogre Pass from the caravan road below the west fort: the two forts, Graalg at his fire.
- Sprite Falls from the Brink (the waterfall over the rim).
- Pictures: `output/studio_cal/d2/pics/sheet_l3a.jpg` (L3), `sheet_final_*.jpg` (final), `sheet_fix.jpg` (A6's review:
  the hut, the stair, the village, the forest round the great tree and the troll holes), heights `pics/height.png`.

- Session 12 (2026-11-21): AU's outdoor bed (E9) from `output/studio_cal/a6/beds/d2.yml`, read by gen.py; reinstalled with
  bake, walk 2/2 and hostility on assets_dev.

## D-58: the fall from D7 (A6, 2026-11-21, sixteenth session)

`entrance:d7_fall` at (15872, -6656, 1056), facing south, 1,024 north of the Southern Tower's door (zone C3-D4, `d7_cd34`). Checked against the installed map (`output/studio_cal/a6/s16/fall_points.py`): a whole flat cell (the 3 x 3 nodes level), no water or lava, no decoration or wall within 256, no hostile with a ranged attack within 5,888 (placed actors and spawn markers with their slot monsters). The entrance is kind `both` in the plan only so that it does not become the party start (the studio takes the first `arrival`). The map and its scene are unchanged by the point (byte-identical), so only the studio sidecar was installed and the bake stays valid. The fall tests (D-54's shape) run from D7.

## The small lamp (A6, 2026-11-21, twenty-seventh session)

- `thing:genie_lamp` (event 46) pays once by the named map variable `genie_lamp_rubbed` (was the silent `once`); a
  second rub says "The lamp is cold. Its genie has gone back in for good." (the walk asserts it).

## D-85: the edge arrivals (A6, 2026-11-21, thirtieth session)

- The chains found the party Stoned by sprites right after arriving from D1. Measured (`output/studio_cal/a6/s30/d85.py`):
  the first wild sprites (`pop:west_sprites` 1, slot 3) stood 4,789 from the west arrival, the first wolves
  (`pop:woods_wolves` 1) 4,438 from the east one. Moved, count and slot kept: west sprites 1 from (22, 69) to (22, 72),
  the built marker 6,001 from `start` / `entrance:forest_edge` and 6,061 from `entrance:west_road`; woods wolves 1 from
  (101, 52) to (100, 54), the nearest built marker 6,027 from `entrance:east_road` (centres tried in a scratch copy,
  `a6/s30/try_d2.py`: D-15's first-fight band ends at about 6,000). `gen.py` refuses a circle within 5,120 of an edge
  arrival.
- Graalg (5108) at the parley fire: the forts' garrisons stand 3,081-5,919 (ogres throw rocks on 20 % of attacks);
  D-23 put the fire between the forts, so it went to a decider (thirtieth report), not moved.

## D-87: Graalg kept at the fire, ranged disablers (A6, 2026-11-21, thirty-first session)

- D-87.2: the parley fire stays between the forts (D-23; the fort ogres' rock carries no condition). Test
  `playtest_graalg_parley.yml`: fresh load, a level-24 party at the fire, no clear: no member gains a condition in 5 s;
  Graalg (actor 22) talks (passed 2026-11-21).
- D-87.3: D2's sprites (slot 3 Gorgon and Elder Gorgon Sprites: Stone and Curse by missile; the court's placed Medusa
  and Killer Sprites) stand 6,001 and more from every arrival point and giver (`output/studio_cal/a6/s31/d85.py`).

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt on merge point 41, installed with its bake 01:20. Dungeon doors with rows 5034, 5037, 5039, 5041-5043, 5045; house_doors hook added. F10: the west-rim wolf (12, 30) to the south-west corner (28, 101), the woods' wolf beyond the east rim (120, 70) to the north-east corner (104, 24): zones 663/340 -> 416 tiles. Walk (window steps, the treehouse chest's status lines), hostility, daily, Graalg parley pass; audits 0.

## Rim rebuild (2026-11-23, agent xeen-rimmap-c: U-12, D-106, D-109, D-112, D-113)

- The rim sea is the void (`terrain.void [[0, 105, 127, 127]]`), 32 hull pieces (MB's rim.py fix: no 1-cell piece on
  the map's last cell 127.5, which `oymap validate` refuses: `hull_033` is no longer placed), 12 return points; Sprite
  Falls' lip (58, 105) down the spillway, foot -2,400.
- Checks: audit 0 errors, 0 warnings; `void.occupied` 0, doors, walls, town_fit 0, empty zones, props, check_wild clean,
  check_faces 1 (sprite_falls), D-85 0 / DIS 0. Build warning kept: `gates.road_off` on `footbridge`.
- Tests: walk x2 and hostility pass.
- Generated twice (the rescue's return points from the first build's land, `XEEN_WILD_MAPS`), built, villagers placed, recorded (`agent:xeen-rimmap-c`), checked in a private hard-link root, installed with its bake, terrain weights, the minimap re-rendered and its void painted (`tools/xeen/void_minimap.py`). Scripts `output/xeen_rimmap_c/build.sh`, `install.sh`, `tests.sh`, `tours.py`; logs `output/xeen_rimmap_c/run_<key>/`; captures `output/xeen_rimmap_c/cap/<key>_after/` (day and night, against `output/xeen_rim/before/<key>/`).

## Final outdoor round (2026-11-24, `xeen-fb3-final-dark`)

- DD-11A/B's troll-hole landings follow A7's moved starts: `HOLE_INSIDE` (80, -208) and (144, -208); `gen_walk.py`
  likewise.
- D-120: the fairy ring and its nine caps at `FAIRY` (21.5, 96.5) in the village's empty south-west corner (it stood at
  (16, 88), past the bounds at cell 18.9); a calm patch there. Three wolf markers past the bounds moved in: (16, 38) to
  (22, 36), (112, 80) to (106, 78), (118, 95) to (107.5, 86) (`reach.spawn`).
- The rope walks: the four tree decks they join stand at 700 (the guild's was 720, house 1's 680: a walk's end met its
  deck 34-40 under it, `bridges.step`). The charred stumps on the palisade lines are shown only when the palisade is
  hidden: `town_fit_check props.in_wall` now skips a decoration shown by the event that hides the model.
- Classic kit `fit_maps`, `dd10b_adit` hood, `footbridge`/`log_bridge` ends from the studio.
- Checks: town_fit 0, check_reach 0, check_faces 0, door 0, wall 0, check_wild 0, audit 0 errors, D-85 0. Playtests:
  walk 391, hostility 67 pass.

## Hull collision rebuild, D-136, D-138 (2026-11-24, `xeen-fb3-hull`)

- The world's hull is solid now (its bindings carry `collision: model`; oymap `oymap_1944` pinned by the orchestrator).
- D-138: troll markers moved past D-15's 2,000 from the Troll Holes' return spots (their circles' edges):
  `pop:trolls` 1 (58, 79) to (56, 80.5) (was 1,717 from DD-11A's, now 2,315), 4 (63, 96) to (61.5, 95.5) (1,824 from
  DD-11C's, now 2,325), 3 (72, 89) to (72, 89.5) (its circle's edge 1,989 from DD-11B's). The troll plain is flat
  (land 900-1,000): no spot short of the trolls' 5,120 notice range is hidden by the land, so they stand at the nearest
  places past 2,000 that still face the holes. Built: spawn 23 at (-4768, -8384), 3,524 from DD-11A's; spawn 30 at
  (-1568, -16192), 3,334 from DD-11C's. `gen.py` now refuses any marker circle within 2,000 of a hole's return
  spot (was 512, trolls only).
- D-136 (kept): Q-D11's fort camps, groups 1 and 2 (Ogres, Ogre Brutes, an Ogre Chief each: no row shoots or casts,
  so no member moved), stay at the DD-13 gates, 927-1,691 from `entrance:dd13_west`/`dd13_east`; they guard the gates
  from outside. `v.sh` runs `x2/check_d85.py --kept-group 1 --kept-group 2`.

## D-142, D-157, D-162, F59, F63 (2026-11-25, `xeen-fb4-outdoor3` sub-agent D)

- `gen.py d142_enforce()` (common/d142.py): 11 circles moved: west sprites 1 (party start 5,600 < 5,888), seven troll
  circles off the DD-11 holes (2,196-3,808 before), woods wolves 2 off the tower lane, and (F63, `hull_reason`) west
  sprites 3 and woods wolves 6 in from the bounds. D2 is in `check_arrivals.D142_EXITS`.
- The road ogre groups 3, 4 three cells down the caravan road (62.5, 42.5) and (96.5, 42.2): 4,096 from DD-13's gate
  exits (3,119 / 3,132 before). Kept groups (D-136, D-162): 1, 2 only (Q-D11's fort camps at DD-13's gates;
  `check_d85.py --kept-group 1 --kept-group 2`).
- `landmark_crystals_4` sunk 32 into the pass's south slope (`decorations.slope`, 26 over its rim before).
- Left: `faces.on_land` 1, the log bridge's deck (the bridge-end pad kind, common/wild.py DECK_LIFT is off).
- D-196 (2026-11-26, A6 doors): the Southern Tower's 192 x 384 door shows the tower kit's `xvtdoor` once, fitted over
  the leaf (`classic_kit.py`), not MM7's framed `hkm1d` (1.5 doors). Audit 0, door_check 0, 4 of 4 playtests;
  installed with its bake 19:37. Captures `output/xeen_fb/p6_doors/shots/d2_installed/`.
