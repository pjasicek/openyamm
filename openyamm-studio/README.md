# OpenYAMM Map Studio

One C++ core for maps, built natively and to WebAssembly, with a command line (`oymap`) in front of it and a small
Node host (`host/`) that serves it to agents as an MCP server. The browser editor comes in a later milestone. Design
and plan: [devdocs/map_studio](../devdocs/map_studio/README.md); what exists today:
[S0](../devdocs/map_studio/S0.md), [S1](../devdocs/map_studio/S1.md), [S2](../devdocs/map_studio/S2.md),
[S3](../devdocs/map_studio/S3.md).

The studio has its own build tree and never touches the game's `build/`. It links the shared core
([`../core`](../core/CMakeLists.txt): the game and engine sources it shares with the game, and the indoor compiler and
outdoor build in `core/compile/`), compiled once in this tree; nothing is copied.

## Build and test

```
./build.sh                 # native: build/oymap, build/oymap_tests (reuses build/_deps of the game when present)
./build.sh wasm            # WebAssembly: build-wasm/oymap.js, run with node (wasm/README.md)
build/oymap_tests          # unit tests
tests/read_all_maps.sh     # oymap reads every .odm and .blv under assets_dev
tests/audit_all.sh         # oymap audit over every map, findings counted per world
tests/import_all.sh        # every map imports into a valid project; every scene file round-trips
tests/build_map_parity.sh  # oymap build-map against maps the editor built: the same bytes
tests/link_closure.py      # which sources a game source needs at link time (from the game's build objects)
tests/native_vs_wasm.sh    # the native and the wasm core write the same bytes
node schema/rpc/gen.mjs --check    # the request list's lint; generated/rpc.ts is current
node schema/rpc/contract/run.mjs --native build/oymap [--wasm build-wasm/oymap_rpc.js]   # the request list's contract
tests/run_slice.sh --shots # builds the slice dungeon, walks it in the game, takes its screenshots
tests/run_shapes.sh --shots # builds the shapes gallery (bent rooms, a path, stairs, a ramp) and walks it in the game
calibration/compare.py <project> calibration/originals/<map>.metrics.json   # a rebuild against its original
tests/run_rewire.sh        # the two rewire overlays play the same as the shipped maps (root, mount and a control)
(cd host && npm install && npm test)   # the MCP server end to end; `node test/mcp.test.mjs --play` also plays a scenario
```

## Commands

```
oymap export <map.odm|map.blv | project> [--world <w> --assets <asset root> [--mount <folder>]] [--summary] [--pretty] [--out <file>]
                                                                         a map as JSON; with a world and a root also its door records
oymap audit <map file> --world <w> --assets <asset root> [--reach] [--solve] [--json] [--original <map>] [--strict]
                                                                         a map as the game reads it, checked
oymap metrics <map file> --world <w> --assets <asset root> [--reach] [--out <file>]   comparison metrics as JSON
oymap flow <map file> --world <w> --assets <asset root> [--event <n>]   what each handler tests and does
oymap things <map file> --world <w> | <project> --assets <asset root> [--json]   every interactive thing: kind,
                                                                         textures, what it changes, where it is used
oymap solve <map file> --world <w> --assets <asset root> [--json]   the order an indoor map opens up, and what each step needs
oymap probe <map file> --world <w> --assets <asset root> --from x,y,z --to x,y,z [--doors-open]   why a walk fails
oymap compare <original map> --world <w> --with <project | second map> --assets <asset root> [--out <folder>] [--step n] [--without <list>]
                                                                         how alike two indoor maps are, by rays from the original's floors;
                                                                         two outdoor maps: layer by layer on the terrain's grid (below)
oymap import <map file> --world <w> --assets <asset root> --to <folder>   a shipped map as an overlay project
oymap render <map file> --world <w> --assets <asset root> --out <file.png> [--view plan|iso] [--size n]
                                                                         outdoor: water, shore and roads as the tiles have them
oymap scene-roundtrip <scene.yml> ...                                   the writer loses nothing of these scenes
oymap build-map <map.yml-or-scene.yml> [--asset-root <dir>] [--world <id>]   outdoor build of a map package (core/compile)
oymap schema [<name>]                                                    the project format's JSON Schemas
oymap validate <project> [--assets <asset root>] [--mount <folder>] [--json]   schemas and cross-file checks
oymap fmt <project> [--check]                                            canonical form
oymap build <project> [--out <dir>] [--assets <asset root>] [--mount <folder>] [--dry-run] [--json]
oymap install <project> --mount <folder> --assets <asset root>           copy a build into a mount folder
oymap install <project> --root <scratch asset root>                      copy a build into a scratch root
oymap ground <map.blv> --ground <ground.yml> --world <w> --assets <asset root> --out <folder> [--stem <stem>]
      [--world-materials <world.yml>] [--exclude <faces file>]      an open-air map's ground weights outside a project
oymap edit <project> --ops <file|-> [--dry-run] [--expect <rev>] [--allow-issues] [--author <a>] [--label <l>] [--json]
                                                                         one transaction
oymap status <project> [--json]                                          source revision, lock hash, outside edits, history
oymap record <project> --author agent:<name> [--label <what>]            name the author of edits made outside the tool
oymap lock prune <project> [--dry-run]                                   drop the lock's entries of ids the project lacks
oymap pins list|show|import|add|claim|reply|resolve|accept|reopen|decline|keep|tour ...   the review pins (below)
oymap undo <project> / oymap redo <project>                              the latest change, also an outside edit
oymap query <project> [--id <id> | --list <collection>]                  read part of a project
oymap assets <text> --assets <asset root> [--world <w>] [--kind decoration|texture|monster|item|sound] [--limit n]
oymap render-sketch <project> --out <file.png> [--size n] [--region x,y,w,d] [--no-labels]   an outdoor sketch as a plan
oymap new <folder> --id <stem> --name <name> [--world <w>] [--stats-id n]   an empty indoor project
oymap script-reference --assets <asset root> [--world <w>]               helpers, selectors and enumerations of the scripts
oymap event-functions                                                    the game's evt.<name> functions
oymap serve [--assets <root>]                                            JSON-RPC on standard input and output: the
                                                                         request list (schema/rpc/) and run/commands/ping
oymap call <method> [<params JSON> | -] [--assets <root>]                one method of the request list
```

Commands that read a map from an asset root (`audit`, `flow`, `solve`, `render`, `metrics`, `probe`, `compare`,
`export`) take `--mount <folder>`: a build's mount folder read in front of the root, as the game's `--extra-mount`
does. `validate` and `build` take it too (S8g): the mount's data tables, sounds and (outdoors) textures count where
the root's do. They also take a **project folder** in place of the map file and `--world`: the project is built into a
private folder and read as the game would read it (`oymap solve examples/shapes_gallery --assets assets_dev`), so
a project is audited, solved, rendered and measured without installing it (its card needs no `map_stats` for
that). A map may also be given by its path in the asset root (`assets_dev/worlds/mm7/maps/7d06.blv`), which names
its world.

How the measuring commands read a map:

- `compare` casts 50 rays from stand points of the original (every 256 units; `--step`) in both maps. Both maps
  are read with every moving part as the party first sees it: the scene's starting state, then what the map's
  load events do on a first visit. A stand point exactly on a ledge, a sunken panel's edge or a wall's line moves
  up to 48 to the nearest place that stands 16 clear of floor edges and faces; a floor's edge is part of the floor
  in both maps; a ray into the seam of two faces meets the nearer; points inside a part that is shut at the start
  are left out. `--out` writes `report.json` (totals, sectors, the 40 worst points), `points.json` (every point
  that differs, by sector, with all that differs at it), two plan pictures and `shots.yml`. `--without
  clear-points,floor-edges,seams,blocks,load-events` switches parts of this back to the reading before
  2026-11-13, to tell what each did to a score.
- `solve` and `audit --reach` walk as the game's party does where the path map's own walk does not: across a gap
  it strides at a walk (144 wide, from the movement code's numbers; never measured in the game), not into a gap
  narrower than its body (74), down through where a floor that moves has moved away, and carried only by floors
  the game carries with (up and down, or a level slide with `carry`). `solve` takes a branch of a handler once an
  event the party can use has set the map variable or bit it tests, uses an event from in front of its face as
  well as from its sector, follows `evt.SetFacetBit` switching a barrier off, shows a step that opens more of one
  sector (`more of sector n`), and ends with `stopped at` (the openings the walk does not pass, and why) and
  `waiting` (branches not taken, and for want of what). `audit --reach --json` has `unreached_sectors` and
  `stopped_at`.
- `probe` ends with `target reached: yes|no`: the planner calls a route found when it ends within 96 of the target.
- `flow` runs handlers without a game: questions about the party answer a party of four with nothing; item
  counts and party-member item tests are tests, taken both ways.
- `assets` lists liquids (`orwtrtyl`, `lavatyl`, `wtrtyl`: drawn by the liquid shader, no picture) beside the
  texture files, and gives each texture's `width` and `height`.

```oymap compile-indoor <source.glb> <geometry.yml> <output.blv> [doors.yml] [face_groups.yml]
```

`compile-indoor` runs `core/compile/LegacyCompileIndoor.cpp`, the same function as
`build/tools/mm9_compile_indoor_source`: same arguments, same bytes.

## Outdoor projects (S4)

An outdoor project is `project.yml`, `plan.yml` and `sketch.yml` (`oymap schema sketch`; every field is described
there). `oymap build` makes a classic ODM with its scene and script:

- **Land** (`core/OutdoorLowering`, the algorithm is told at its top): `heights.grid` holds spot heights (the land's
  height at the middle of each block of 4 or more cells) read as rounded ground; height points correct it where
  they stand; cliffs stay breaks; water lies on the corners of cells with a level shore round it; roads lie level
  across (`bed`: the bed's height at each point of the line); the ground under a building's plot is made level.
- **Ground** (`core/OutdoorGround`): `ground` zones by kind (dirt and two more kinds of land per map; a zone may lie
  on steep ground only, `steeper_than`), the tiles chosen as the shipped maps choose them (a line of dirt between
  two kinds, the twelve tiles toward dirt, shore tiles, variants); `roads` as road tiles one cell wide in a dirt
  bed with the classic bends, T pieces, ends and diagonal steps.
- **Buildings** (`core/OutdoorBuildings`; the forms are measured on Ravenshore, Harmondale, New Sorpigal and Dagger
  Wound and told at the file's top): a plot is a building of `parts` (a box, a convex `outline` or a many-sided
  `round`, each with `bottom`, `wall_height` and its own roof), `turn`ed as a whole. Walls are bays of panels 128
  wide in rows of 256, as the shipped houses are: `walls: {s: [post_left, window, door, window, post_right]}` (roles
  of the plot's `kit` and `textures`, or a texture's own name), laid out by rule when not listed. Roofs: `flat`
  (with `parapet`, `battlements`), `hip`, `gable`, `lean_to`, `cone`, `none`, with `roof_height` or `roof_pitch`,
  `eaves`, `fascia`, `hip`, `ridge`, `ridge_along`. Doors: the plot's own (`house` or `into`, placed by
  `door: {part, wall, bay}`, or `door: none`) and more in `doors`. A plot that says nothing is the world's ordinary
  house. A building's walls say its `title`. Textures the world lacks are refused when the build has an asset root.
- **Structures** (`core/OutdoorThings`): `structures` are what is no house of the plan: `kind: building` (a plot's
  words on its own ground), `wall` (a line with a walkable level top, `gates`, `battlements`), `bridge` (a deck on
  the land at its ends, humped by `rise`, or level at `height` on piers: a pier), `well`, `fountain`, `obelisk`,
  `chest`, `crate`, `sign`, `platform`, `stairs`, `doorway` (a door in a frame against a slope: the way into a cave)
  and `decoration` (one decoration of the game's table by name). What a click does is said with the structure:
  `title`, `house`, `into`, `chest` (level, random_items, items), `effects` (text, gold, add, subtract, set,
  autonote, qbit, clear_qbit, give_item, teleport, lua), `once`, `lua`. `actors` place townsfolk and guards by
  their monster row (`monster`, `at`, `count`, `spread`, `group`, `hostile`).
- **What things do** (`core/OutdoorEvents`; measured with `oymap flow` on both towns, told at the file's top): a
  plot's door, a door of `doors`, a part of a building and a structure say what a click does with the indoor
  wiring's words: `condition` (qbit, item, map_var, award, gold, stat, season, kills, lua, not, any, all; names from
  project.yml `qbits` and `items`), `locked_text` and `else_effects` when it does not hold, `effects`, `once`,
  `lua`. So a house door is shut while a quest bit is set, a chest opens only with its key (`chest` with a
  `condition`, `take_item`), a part has a `title` of its own (each shop of a joined block) or is clicked itself
  (`parts[].effects`), a structure's body says a second name (`hint`), a signpost has `arms`. Events nobody clicks:
  the sketch's `events` (`trigger: load` or `timer` with `every`), and a structure with `trigger: step` (its faces
  one can stand on run the event). What events change: `{show: id}`, `{hide: id}` (a structure or a plot's building;
  `hidden: true` starts it hidden), `{set_sprite: {of, to}}` (a decoration's picture: a picked tree),
  `{set_texture: {of, from, to}}` (a model's faces of one texture), `{show_actors: group}` (`actors[].hidden`).
  The numbers events name things by are kept in ids.lock.yml `cogs`.
- **Spawn points and decorations** (`core/OutdoorPlaces`): encounter `areas` become spawn points of a monster slot
  (`count` markers, half a cell apart); `scatter` places decorations by kind and number over an area, clear of
  water, roads, buildings, structures and ground too steep to walk (`steep: true` allows it), evenly or in
  `clusters`.
- **Leaving the map** (`core/OutdoorInstall`): project.yml `neighbours` of `kind: edge` with a `side` become the
  map's row of `engine/data_tables/outdoor_travels.txt` when `oymap install` copies the build (and each
  neighbour's own row is pointed back, unless `one_way`); the plan entrance that names the neighbour (`kind:
  arrival` or `both`, placed by a sketch point) becomes the arrival point `<side> start`. `arrival_side` is the side
  of the other map the party arrives on (left out: the side facing this map); the table says it in MMerge's words,
  which the game reads as `up` the north start, `down` the south start, `left` the **east** start and `right` the
  **west** start (S8g: before 2026-11-16 the studio wrote `left` for a west arrival, so every east-west way arrived
  on the wrong side, or at the party start). The square the party can
  walk is the game's own (23143 units from the middle), not `frame.playable`.
- **Air** (`atmosphere.yml`): `sky`, `fog`, `precipitation` (rain, snow), `daily_fog`, `fog_tint` go into the
  scene's environment. **The sky's paintings, the fog's colour and the weather by chance are not in the scene:** the
  game takes them from the map's row of `engine/data_tables/bolster_maps.txt`, keyed by the map's number, whose
  `Continent` gives the skies from clear to storm (`continent_settings.txt`). `oymap install` writes that row
  (`core/OutdoorInstall`): the reference map's (`map_stats.reference`) under the project's number, else a plain row
  on the world's own continent; over it project.yml `map_stats.continent`, and atmosphere.yml `weather: {rain,
  snow}` (rain and snow by the world's chances) and `sky` (one sky for every weather). A map installed without the
  row is drawn under the fallback sky `sky05`, grey haze (every picture of a rebuild before 2026-11-13).
- Event and chest numbers are kept in `ids.lock.yml` (an outdoor project has one since this batch). `oymap
  validate` runs everything the build checks (a dry build; with `--assets` also the names looked up there).
- **Forms added on 2026-11-13** (batch three): `roof: hip` and `gable` on an `outline` or `round` part (a house
  with cut corners: a hip slopes alike from every wall, or with `hip` has its ridge drawn in; a gable closes every
  wall up to its two slopes), `taper` on a part (a spire that draws in, a cap that flares), a plot's `floor`
  (the ground is levelled there, not at the land's mean), `ramp: true` on stairs (one sloping slab), a doorway's
  `depth` and `hood`. Not built: one peaked roof over a hall that is not convex (a part is convex), an arcade.
- **Words of outdoor batch five** (2026-11-13; each in the schema, with unit cases in `tests/OutdoorTests.cpp`):
  the rim (below); `heights.ridges` (a line of nodes at a height, `width` nodes across, `slope` back to the land:
  dykes, ledges, channels one node wide) and `heights.rough` (an area's ground moved by about `amount`, node by
  node or in bumps of `scale` cells); `scatter[].line` with `closed` (a row or a ring of `count`, planted where
  drawn); `doors[].storey` (a door up a storey); `cap` on a hip roof (cut flat); bridge `kerb` to 512 and `rise` with
  `height` (an arch); `click` on a model (which models run the click, the rest say the `hint`); `switch` (a model
  shown and hidden with another); `into.screen` (the "Enter ...?" screen before a map); `lua_before` (steps
  before the house, map or chest); `events[].trigger: daily | weekly` (`hour` for daily).
- **Words of outdoor batch seven** (2026-11-13; counted first on the 42 shipped outdoor maps with
  `output/studio_s4h/scripts/forms.py`; each in the schema, with unit cases in `tests/OutdoorTests.cpp`): an open
  part on `posts` (with `post_every`, a `sill` on `sill_walls`, a ceiling under its roof: pavilions, shrines);
  `porches` on a wall's bays (a roof on posts, a canopy without them, or `recess: true`, the stretch set back under
  the part's roof with the door at its back); roof `tiers` (a cone or hip in rings: thatched round halls, beehive
  huts); `signs` on walls (flat, or `hang` across the wall under an arm); a `railing` round a flat top (open, with
  a barrier that is not drawn); `holes` in a flat top with a pit (a hatch's pit); a door's `step` (a slab, or with
  `front` a stoop); obelisk `sides: 8`, `taper`, `tip`, `plinth`; a signpost's `post` width and each arm's own
  `board`; a well's `post`. `oymap things` reads outdoor maps (faces by event, clicked decorations; kinds house,
  chest, exit, name, panel). A part's `outline`, `size`, `radius` or `sides` on a part of another shape is refused
  (an outline without `shape: outline` was built as a box). `oymap assets --world` lists the world's own textures
  and the engine's only. A scatter entry places by its own words (splitting one no longer moves the others). A
  height point that raises a node on a cliff line stays there.
- **A map's own tile sets, mist and sky theme** (batch s4j, 2026-11-13; counted on the 42 shipped outdoor maps with
  `output/studio_s4j/measure.py`: 12 use tile sets the world's usual rows do not have, 13 have ground mist, 25 a sky
  theme): sketch `tile_sets: {dirt, water, road}` (the plain ground by the master tile, MM8 only: dirttyl, plntyl,
  gdtyl; the water and road sets by name or row), `ground[].material` naming any ground or liquid set of the world
  (gstyl, plsatyl, `"846"`), `water.bodies[].tile_set` (tar pools and lava laid in a ground set, no beach); a road
  set without its own diagonal pieces (MM6's) jogs with round bends. atmosphere.yml `mist` (the scene's `mist`
  block, checked by the game's parser) and `sky_theme` (`oymap install` writes the map's row of
  `engine/rendering/sky/sky.yml` `maps` in the root, or in the mount's own copy). `compare` reads the transitions'
  plain corners as the map's own plain ground (grey dust on Shadowspire), tar and lava as kinds of their own, and
  invisible faces as no building (neither top nor plan); `render` draws tar and lava dark. Over a grid, height
  points whose fades overlap take the mean of their corrections; a door without `title` says the building's title
  or nothing; a `kind: building` refuses `trigger` and words it has no door to run.
- **Things no form says** (`kind: model`): models of a shipped outdoor map of the project's world, taken as they
  are by name (`from: {map: out02.odm, models: [Boat3RTex_Etr]}`), to `at` (or where they stood), with the
  structure's words on all their faces: ships, wagons, the crystal, cannons, tents, a crane. The smallest building
  import: the project's own world, no turning, heights as in the source map (`raise` moves them).
- **A waterfall** (`kind: waterfall`, `core/OutdoorFalls`, the shipped falls measured at its top: Alvar's on out03,
  2,880 down a sheer cliff, and Emerald Island's chutes on 7out01): `line` gives the lip's middle and the way the
  water falls, `top` the stream's level at the lip, `foot` the pool's; `width` comes from the river at the lip. The
  build cuts the land in front of the sheet (and makes the stream's last nodes beside the cut its bank) and raises one
  model: the top water from `back` up the stream to the lip (its first 256 rising out of the stream from under the
  stream's water when `back` is over 1,024, then 2 over it), the sheet as one plane (upright, or its foot `lean` out and `spread` wider),
  let through and flowing down, the foot water `pool` out into the pool, a crag of rock at each edge (`rocks`,
  `rise`, `rock_size`, `seed`) and a low bank of dirt along each side of the top water (`banks`). Textures: `water`,
  `rock`, `bank`. The game draws all its water by the liquid shader; texels in each face's own plane give every face
  the same flow, so the picture does not tear along the triangles. Limits of the game's water (S8e, 2026-11-15): a
  model's water face is opaque and its waves finer than the land's water, so the top water reads a shade darker
  than a shallow stream beside it; an upright water face is drawn with the waves of a level one (streaks).
  `floor` said under the water that reaches a plot stands there (a fall's pool built as a building at a cliff's
  foot); the build says so.
- **Item spawn points**: an area of `kind: items` with a `level`; a chest's `random_levels: [7, 3, 3, 3]`.
- **The rim** (`core/OutdoorRim`, the shipped maps' rims measured at its top): the land beyond the square the party
  walks (nodes 19 to 109), half the map, seen and never walked. `frame.rim` entries give a side or a stretch of it
  (`span`) a `form`: `level` (a sea, flat ground, or a shelf between two heights with `roughness`) or `ridge` (a
  bank `crest` cells out whose top rises and falls between `height: [low, high]`, the land falling to its `floor`
  first and to the map's edge behind it); `frame.edge` holds the outermost row of each side. The rim starts from
  the land at the square's edge, keeps valleys open where roads and rivers run out, never changes the square, and
  height points, cliffs and water apply on it as anywhere. Where no entry speaks the heights (grid, bands) say the
  land, as before. An entry without a form shapes nothing (the build warns); its old `depth` is retired.
- **Words of workstream S8d** (2026-11-16, from Castle Ironfist's and Erathia's rebuilds; each in the schema, opt-in,
  with unit cases `S8d: ...` in `tests/OutdoorTests.cpp` and repros in `output/s8d/repro/`): `roof: vault` on a box
  (a gable whose slopes are a curve across the ridge: `tiers` from each eaves side with a flat crown between, as
  the temples', or a half ellipse `roof_height` high in `vault_segments`; its ends closed in the `gable` texture);
  `half_hip` on a box's gable (the ends hipped up to that height, a small gable above: Erathia's House 10);
  `pent` on a part (a skirt roof round the walls at a storey); `flare` (walls leaning out, a batter the other way:
  Castle Gryphonheart's bailey); `porches[].open_corner` (a recess to its wall's end open at that corner, the wall
  across standing back by its depth: HouseR2S); `doors[].sill` (a door standing over its row's foot, a whole door
  high, the rows above over it: the King's Library door); bridge `kerb_width` (it was read only on walkways) and
  `arches.spans` (openings of their own widths: Erathia's viaduct); sign arms `toward` in degrees (the guild sign's
  three boards); platform `chamfer` (an octagonal deck); culvert `grating` (bars before the dark face); tent
  `roof: hip` (a pavilion) and a door on a closed tent's front (`textures.door`, `door_width`, `door_height`); a
  doorway's `facing` (n, e, s, w before `turn`; it was read nowhere) and `textures.roof` for its gable portico (a
  turf hood). `oymap audit` warns of a solid decoration in a doorway's way (`thing.in_doorway`, indoors: within its
  radius and the party's 37 of the line through a portal's middle, 0 to 128 to either side: XD-01's stash keg).
- Not built (the build says so in its warnings): boats and stables as travel (a house's service); the plan's
  containers and landmarks unless the sketch draws them as structures.

`oymap compare <original.odm> --world <w> --with <project | second map> --assets <root> --out <folder>` measures a
rebuild against its original (`core/OutdoorCompare`, the method is told at its top): one score from eleven parts
(heights 15 %, relief 6 %, cliffs 6 % over the square the party walks; rim 8 %; water 10 %, ground 12 %, roads 8 %,
buildings 15 %, decorations 8 %, spawn points 4 %, events 8 %). The rim is judged by its skyline, not node by node:
eyes 4 cells inside the square's edge every 2 cells along it (so the land beside one eye does not decide all its
lines), 192 over the original's land, look out over 150 degrees, a sight line every 3 degrees; the lines are grouped by the region their horizon lies in, and in each group the two maps' horizons are
compared rank by rank (6 degrees apart is nothing alike) and by their ups and downs, so a rim described by its
form and not traced can agree. `--without rim` judges as before 2026-11-13 (heights 20, relief 8, cliffs 7 over
the whole map; the skyline reported with no weight). `shots.yml` adds the rim's six worst regions seen from the
measure's eyes (`rim-*`). Also since then: an upright face is as high as its top edge where it stands (a railing
over an arch); a model whose pixels others cover stands at the middle of its corners, not its stored centre; party
starts are not decorations; an event whose handler has no title and does nothing is not counted; `differences.json`
names the decorations without a partner of their kind (`decorations_only_in_original`, `..._rebuilt`). Earlier: decorations are paired nearest first within a region's width (16
cells), by kind and whatever the kind, so where the regions' borders run does not count (a clump need not be
split at them any more); an event number on models that stand apart is a thing at each (not one at their common
middle); a face that stands upright covers the pixels its foot runs through (a ring without a roof has its ring). The buildings part is 0.3 the shared footprint, 0.3 the models found under the other map's
buildings (however a building is cut into models) and 0.4 the form: how alike the buildings' tops are over the land, a score for each of the 64 regions of 16 x 16 cells (A1 the north-west), and the worst
regions with what differs there. It writes `report.json`, `differences.json` (every region's differences, every
building with its partner or without one: models that lie at least half under one another are one building in
both maps, however each cuts it into models, `models_original` and `models_rebuilt` naming them; spawn points
and events only one map has, decoration kinds),
`heights.png`, `ground.png`, `objects.png` (original, rebuild, difference), `regions.png` and `shots.yml`. A map
against itself scores 100 % in every part.

The game draws the ground of an outdoor map only from its terrain material file, and pictures need a scratch root:

```
cp -al assets_dev output/my_root                                           # once; never assets_dev itself
build/oymap install <project> --root output/my_root
calibration/outdoor_materials.py <project> --root output/my_root          # the map's material file (tools/terrain_materials.py)
calibration/outdoor_ingame.py <project> <world> <original.odm> <compare folder>/shots.yml <out> --root output/my_root
```

`outdoor_ingame.py` takes the same views in the original and in the rebuild (the twelve worst regions) and writes
the pairs with their difference sheets, both maps under the same weather (`--weather <n|auto>`, `--time HH:MM`;
it prints the sky each side was drawn under). Angles: a shot of `shots.yml` has `yaw` in radians (0 east,
counter-clockwise) and `pitch` in degrees (negative down); a playtest's `set_pose` has `yaw` and `pitch` both in
radians. `oymap render-sketch` draws every building's parts as the build reads them (doors as red ticks) and the
structures (walls, bridges and stairs as lines, the rest as marks). Headless runs (`--headless-run-scenario` with `--extra-mount`) need no
material file.

## A project

A folder of text files (`project.yml`, `plan.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`, `atmosphere.yml`,
written by hand or by an agent, and `ids.lock.yml`, written by the build and kept in git). Each has a JSON Schema in
`schema/`, compiled into `oymap`; `oymap schema rooms` prints one, and every field carries its description there.
The files are the truth: edit them with anything, then `oymap fmt` and `oymap validate`. They hold no YAML comments
(use `notes:`).

[examples/gatehouse_cellars](examples/gatehouse_cellars) is the reference project: six rooms, five openings, two
click doors, a gate raised by a lever, a keyed door, two chests, spawns, lights, torches and an exit.
[examples/shapes_gallery](examples/shapes_gallery) shows every room shape: an L-shaped hall with a pillar and a
dais, a corridor drawn as a path, a flight of steps, a lift, a closet behind a hinged door, a ramp and a cave whose outline bends inward.

Rooms (`oymap schema rooms`): an `outline` of any simple shape or a corridor `path` with a `width`; `slope: {to,
toward, steps}` for a ramp or a flight of stairs; `pillars`, `platforms`, and `walls` for single walls with their
own surface. Doors (`oymap schema objects`) slide (`slide_up`, `slide_down`) or swing (`kind: hinged`); `lifts` are
blocks of floor an event raises and lowers. Rooms joined by an opening have facing parallel walls 0 to 512 apart; that gap is the wall's thickness.
Tunnels: a `path` room with a `section` (its cross-section as an outline of [across, up] points, carried along the
path and mitred at bends: six-sided, with banks, walls and chamfers, as the shipped tunnels), path points
`[x, y, z]` for a floor height at each point, openings `shape: section` at a tunnel's ends, square ends
(`section.start`, `section.end`) for a plain doorway or a door, doorways in the sides of tunnels and of path rooms
that climb, and plates across their floors.
Floors that are not level in a room with an outline: `floor_points` (heights at points, flat triangles between them,
as the shipped maps' cave floors are made; `floor_plane` for one plane in any direction, `floor_lines` for the
lines planes meet along) and the same for the roof with `ceiling_points`; `levels[].bank` for sides that slope
(a trench, a funnel, a mound); `top_slope` and `top_heights` on a platform (a wedge, a ramp that is not a room);
`from_height` and `open_below` on a flight. A floor too steep to walk (over 0.9 for each unit of run) is refused
unless the room says `steep_floor: true`.
Wiring events (`oymap schema wiring`): presets with a `condition` (item, qbit, map_var, gold, stat, award, autonote,
kills, lua, not, any, all), `effects` and `else_effects` (gold, add, subtract, set, autonote, qbit, items, text,
damage, cast, summon, teleport, lights_on, lights_off, lua); events without a clicked object (`trigger: step |
timer | load`).

Words added since 2026-11-12 (each is described in its schema, has a unit case in `tests/CoreTests.cpp` and stands
in `examples/shapes_gallery`):

- **Surfaces**: `floor_surfaces` and `ceiling_surfaces` (parts of an uneven floor or roof by steepness or place);
  `bottom_surface` and `thickness` on a platform with a sloping top (a hanging ramp); `top_surface` on a chest (a
  desk); texture names may hold a hyphen (`sign01-1`).
- **Openings**: a mouth that follows uneven floors and roofs along its wall (`width: full, height: full`), also as
  a gable or an arch standing on an uneven sill; `trim_to_wall: true` (an opening cut to the upright end of a
  vault or hip over its wall; with `height: full` the wall's whole profile); `from_wall` and `to_wall` where two
  rooms face each other across several pairs of walls (the build warns until they are given).
- **Floors and blocks**: `solid: false` (drawn, not solid: a false floor) and `visible: false` (solid, not drawn)
  on platforms and raised levels; a raised level over an uneven floor (a loft over a floor that sags); a flight
  that ends in a doorway (`to` on a wall, `to_height` the sill); a ridge (`top_scale: [1, 0]`) over chamfered
  corners; a tunnel section with a single highest point.
- **Objects** (`oymap schema objects`): `monsters` (placed, with `group`, `hostile`, `immobile`, and for a boss
  `hp` and `name`) and `items`; `movers` (with `parts`, `block`, riders via `rides`); `plates`, `floors` (lava,
  water); `ladders`; `sounds`; lights with `on: false` and `pulse`; `secret: true` on a door; platforms and wall
  panels with an `id` as click sources.
- **ids.lock.yml** also keeps `lights` (the numbers `evt.SetLight` switches lights by) and `sounds`.
- **project.yml `migrated`**: answers a warning about a rule that changed (the warning names the word to add).
- **Tools**: `oymap metrics` counts `decoration_lights` and `light_sources` (torches); `oymap assets` says for each
  decoration whether dungeons draw it as a 3D model (`indoor_model`: every dungeon, named maps only, or none);
  `oymap validate --assets` notes a world the asset root does not hold.
- **Indoor code batch six (2026-11-13)**: `monsters[].hidden` (starts invisible) and `monsters[].carries` (an item
  left in the corpse); a placed monster's record repeats its kind's experience in `monster_id`, as the shipped
  records do; effects `show_actors`, `hide_actors`, `set_texture: {of, to}`, `passable`, `solid`, `show`, `hide`
  (faces of a door, or of a platform or wall panel with an `id`, by a cog number the lock keeps); wiring `side` (a
  door's event for one side of its leaf; a second event for the other side); `question` (an answer the handler
  reads); `trigger: leave`; a decoration as an event's source; `once` on doors, texts, teleports and scripts. A
  surface may leave out `size` for a liquid; a chest's `items` refuses a roll written as a negative number;
  `ids.lock.yml` forgets removed ids; a `path` takes 64 points. `solve` and `audit --reach`: a kill test waits until
  its monsters are reached, steps onto and off a ramp's end, ladders, sectors too low to stand in are niches;
  `oymap flow` follows the answers of a question.

- **What the user found playing Gharik's Forge (2026-11-13)**, as words and checks for every map:
  `switches[].kind: lever` (the shipped maps' lever: a post 8 by 8 and 32 high and an arm 4 thick to `reach` 40 from
  the wall, a door record of its own that sinks 16; `base` the post's surface, `height` the arm's middle, default
  122) and `kind: button` (MM7's and MM8's push button: a block `size` [32, 32] standing `depth` 16 out of the wall,
  pushed in to 1 short of it; `sides`), moved by the switch's own event: to its end, back and forth where the event
  `toggles`, by the branch where it has a `condition` and `else_effects`; a plate's picture follows its state the
  same way (a toggling plate keeps it in the map variable `toggle.<name>`). `chests[].kind` (`ch1` to `ch5`,
  `7gt002`, `gt002`, `ch001` to `ch006`): end, middle and end on both long sides and the top, as the shipped chests
  are; a chest without a `surface` is its world's plain chest of a kind and size (the build warns of a `surface` that
  is a kind's middle). Lifts and movers: what stands over one (start, spawns, items, monsters, a chest with `rides`)
  stands on its top as it stands at the map's start (`state: up`, `state: end`); a decoration there or a chest without
  `rides` is refused, as is a `floor_height` inside the part's block. `floors[].kind: liquid` (the fluid bit only:
  lava's look that does not burn). A thing on a wall lies wholly on one face of it (refused partly over a corner strip
  or a panel). The build stands a door leaf 2 back from each face of a wall as thick as itself and sends it 2 past
  its jamb, leaves out a mover's sides that lie inside its room's walls, and ends ladder rails 2 under the floor they
  climb to: all three put faces in one plane over each other before.
- **Indoor code batch nine (2026-11-13)**, each in its schema with unit cases: `spawns[].group` (the actor group of
  what spawns there: MM7's maps use 51 and 56; `show_actors`/`hide_actors` name spawn groups too); an opening's
  `reveal` and `back_reveal` (a frame of its own, two-sided: the half toward `to` beyond the wall's middle); a door's
  `edge_surface`, `top_surface`, `bottom_surface` (a leaf's ends, top and underside, laid at their size; they had
  all-zero coordinates); a surface's `offset: [u, v]` (every surface); `chests[].lid: v` (MM6's carved lids);
  `set_texture` with `face: top` (a platform's top alone) and the effect `set_sprite: {of: deco, to}` (ids.lock.yml
  `decorations` lists the numbers, written anew each build); `panels[].secret`; `decorations[].hangs` and `inside`,
  `monsters[].inside`; wiring `window` (a clicked `text` shows a window where its title names a sign or its text is
  over 65 characters). Sideways leaves stop at the jamb with their trailing end drawn 2 inside the leaf. Default
  hover names of clicked events (Door, Chest, Exit, Lever, Button, Switch). `build` drops a `.leaf2` whose door has one leaf. Checks, warnings of `build` and
  findings of `audit`: the party's eye outside the sector the game draws from (`core/EyeSector`,
  `geometry.eye_sector`), pictures squashed one way (`core/Looks`, `texture.squashed`, info in audit), things
  floating or hanging from nothing (`thing.floating`), things inside each other, blocks that look like chests,
  chests named otherwise than as what opens, clicked things without a name or silent when their condition fails,
  MM6's switch plate in another world, questions whose answers the player has not met (`question.answer`, by
  `solve`'s order), branches of clicked things that show nothing (`click.silent`, info). Hanging decorations (a
  swinging model, a chandelier) without `height` are hung with their top 2 into the ceiling. `compare` reads texture offsets (`offsets` and `offset_agreement` in the report; a ray on the
  same texture at another phase counts half; `--without offsets`). `things` gives `hover` and flags things without
  one, and places decorations in their sector; `solve` files a clicked face's event under the room in front of it
  and counts what placed monsters carry.
- **Indoor code batch ten (2026-11-13)**, from the user's walk through the Abandoned Temple and XD-04, each in its
  schema with unit cases: `secret` and `id` on `floor_surfaces`/`ceiling_surfaces` entries (a region of a floor or
  roof, level ones drawn with points all at their height and lines round the region, whose faces carry the engine's
  secret flag: the Temple's walkway traced on hall 8's ceiling) and `secret` on `plates` (with or without an event);
  effects `{secret: id}` and `{clear_secret: id}` (`evt.SetFacetBit(cog, FacetBits.IsSecret, 1|0)`; `{secret: {of:
  id, face: top}}` a platform's top alone), and effects that change faces (`set_texture`, `show`, `hide`,
  `passable`, `solid`) now also name plates and regions; plates side by side are cut into the floor as one hole.
  A beam's `top` (level while its underside rakes), and a raking beam whose top meets a ceiling level's flat top at
  one end is cut level there as under the room's own ceiling (the Temple's box walls: 5 pairs of faces in one plane
  with the lantern's walls gone). `liquid: water | liquid | lava` and `flow: down | up | left | right` on any surface
  (the fluid bit makes a picture that is no shader liquid ripple: XD-04's brew; flows scroll it; measured on every
  MM6-8 BLV), and the build warns of faces of a shader liquid, or of a texture the project lays as a liquid, without
  the bit. MM6's `lid: v` laid across the lid as the Forge's chest has it. Text: a message window only for things to
  read (titles naming a sign, notice, book, scroll, note, slate, terminal, tablet, plaque, inscription, or `window:
  true`); every other text is a status line, over 30 characters held 2 s plus 1 s per 15 characters (at most 6),
  `seconds` on the event says it outright (`evt.StatusText(text, seconds)`). `items[].gold` (a heap of gold's amount;
  the build warns of a heap without one); a wall decoration's `at` and `floor_height`; `uneven` in the surface
  schema; a platform's `end_surface` with `fit: false`. Every `build`, `--out` too, keeps the project's
  `ids.lock.yml` up to date again (the private builds of `export`, `compare`, `audit` build a copy). `audit`: faces
  in one plane also with the moving parts a quarter, half and three quarters along; matched against the original
  (`--original <map>`, by default a project's `map_stats.reference` or `base`): a pair the original has at the same
  place (same two textures, same plane, middles within 128) is info, the rest warnings, with `--strict` errors (exit
  1); a summary line `faces in one plane: N pairs, M as the original, K new` (JSON `coplanar`).
- **From the user's walk through Goblinwatch (2026-11-13)**: a switch plate on a block's top, level or sloping in one
  plane (`side: top` with `at` and `size` on the plan; it lies in the top's plane 2 off it, as the console's sixteen
  on its 45-degree top); the 2 of reveal before a shut leaf that stands 2 back from its wall's faces is laid with the
  leaf's own picture (it showed as a light line round the leaf).
- **Indoor code batch eleven (2026-11-14)**, the words most indoor projects' notes asked for, each in its schema with
  unit cases: atmosphere.yml `mist` indoors (the scene's `mist` block, checked by the game's parser: the Lab's
  `d20_mist.scene.yml` exactly); `neighbours[].screen: {house, picture}` (MoveToMap's seventh and eighth numbers: the
  MM8 dungeons' exits `{picture: 1}`); effects `leave: <neighbour>` (an exit from any event), `shake: {strength,
  seconds[, at, radius]}` (evt.CameraShake), `player_bit`/`clear_player_bit` and the condition `player_bit` (once per
  character: the Forge's event 91), `give_item: {level, kind}` (a random item: the Fortress's GiveItem(6, 25));
  objects.yml `relations` (a map's own monster relations, set by the build's load event `evt:studio_relations`).
- **Faces in one plane** (`core/Coplanar`): every pair of drawn faces in one plane, facing the same way, that overlap
  by more than a sliver (8 square units and 1.5 wide), as the map starts and with every moving part at the other end
  of its way: a warning of `oymap build` naming both faces' rooms and objects, and a `geometry.coplanar` finding of
  `oymap audit` (originals too).
- **`oymap things <map | project>`** (`core/Things`): every interactive thing (faces grouped by the event a click runs,
  clicked decorations): kind (door, lever, button, switch, chest, exit, teleport, panel, decoration), textures, what
  using it changes (the faces of the doors it moves, of the textures it sets), where a player stands to use it, and
  what overlaps it (faces in one plane, a plate over two faces of its wall). `calibration/things_shots.py` takes a
  picture of each from there in the game, and where using it is harmless one after using it and one after using it
  again (`--near x,y,r`, `--kinds`, a contact sheet).
- **S8c (2026-11-15)**, from the user's walks through XD-02 and XD-05 and the Hive's and the Lab's rounds, each in its
  schema with unit cases in `tests/S8cTests.cpp` (repros under `output/studio_cal/<key>/repro/`): rooms.yml
  `stalactites` (`at`, `radius`, `length`, `sides`, `surface`: three narrowing blocks hanging from the roof, the top
  one's top following it); a path's `bend_radius` (and `bend_pieces`): each bend an arc tangent to its stretches, also
  for tunnels with a section; `platforms` on a tunnel's flat floor (under its roof; not over its leaning sides); an
  opening's `lintel` (the doorway's top through the wall); project.yml `new` (a new dungeon: true by default where the
  project has a `map_code`), and the build warns of a new dungeon with no arrival text (a timer event without a
  condition with a `message` or `text`, or a load event's status line). Defaults: a torch or sconce on a `wall`
  without `height` hangs at 128 (the shipped maps' commonest; it stood on the floor); of several pairs of facing walls
  an opening takes the thinnest that holds its width with 16 each side (the Lab took a pair 192 apart where its rooms
  met 0 apart). Checks: the build warns of a decoration the world draws nothing for (no 3D model binds it for the map
  and its sprite's pictures are in no sprites folder of the asset root: MM6's `stltite1-3` in MM7), and no longer
  says a block whose top follows a sloping roof by `top_heights` rests on nothing; `oymap solve` (and `audit --solve`,
  `reach.stranded`) names placed monsters and monster spawn points in sectors it never reaches, fliers too, and counts
  items lying on the map as the map's once their place is reached; `oymap audit` warns of a ride (a moving part whose
  deck stops beside a floor at both ends) with an end where no clicked thing that moves it is within the game's 512
  of a rider's eye, facing him with nothing drawn between (`ride.no_switch`), leaves out of `thing.floating` a
  project's decorations with `hangs: true` or on a wall, and of `click.silent` faces without the clickable bit (step
  plates); `solve`, `audit --reach`, `probe` and `compare` leave out the faces of a sector with no floor and no portal,
  which the game never meets (the Lab's sector 23); `oymap things` tries nearer places to use a thing from.

To try a built map in the game, install it into a mount folder and start the game with it in front of the assets;
nothing is copied into `assets_dev`:

```
openyamm-studio/build/oymap build <project> --assets assets_dev
openyamm-studio/build/oymap install <project> --mount output/my_mount --assets assets_dev
build/game/openyamm --asset-root assets_dev --extra-mount output/my_mount --world mm6 --map <id>.blv
```

A mount folder is laid out like an asset root and holds only the build's files (and, for a new map, a copy of
`map_stats.txt` with the map's row; for an outdoor map also `outdoor_travels.txt` and `bolster_maps.txt` with its
rows). S8g: an install into a mount that has these tables starts from the mount's own copy and adds the asset root's
rows it lacks, so several maps installed into one mount keep each other's rows (X1 and X2); a row the root changed
since is not taken: remove the mount's table to start afresh. `--root <scratch asset root>` (a hard-link copy:
`cp -al assets_dev output/my_root`) still works for tools that take an asset root and nothing else.

## Editing a project: transactions and history

`oymap edit` applies a list of operations as one transaction: all of them or none. It answers with the semantic diff
(`objects.yml: door:gate changed speed`), the validation issues the change introduces and fixes, and the new source
revision. A change that introduces issues is refused unless `--allow-issues`; `--expect <revision>` refuses when the
project has moved on. Operations: `add` (or `<kind>.add`), `set`, `remove`, `set_value`, `patch` (JSON Patch on an
object or a file; a path segment into a list of maps with ids is an id); `oymap edit` without arguments lists the
collections. `--author user|agent:<name>` and `--label` go into the history entry.

**Three classes of file** (devdocs/map_studio/S5_BROWSER_EDITOR.md 2.4.1, slice S5a1):

- **Source** (`project.yml`, `plan.yml`, `sketch.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`, `atmosphere.yml`):
  the **source revision** is a 128-bit content hash of these alone (the first 32 hex digits of a SHA-256 over their
  canonical text); `expect_revision`, the history and undo see only them.
- **Record** (`ids.lock.yml`): the engine numbers builds gave. Builds (and `import`, and `oymap lock prune`) write
  it under the project lock; every change is a JSON line of `.oymap/lock.log` (who, at which source revision, which
  entries). It is never undone and never a history entry; a lock changed from outside (a `git checkout`) is taken as
  the new record and noted in `lock.log`. **Builds keep the numbers of ids the project no longer has**, so an undo
  that brings a door back gives it its number again; `oymap lock prune <project>` drops them (indoor projects, by the
  rule of what is live in `core/IndoorLowering.cpp` `retiredLockEntries`; outdoor and overlay projects keep every
  entry). A map with more than 75 variables names the retired ones and the prune. A build is its source revision plus
  its lock hash; both are in `build.json`.
- **Review** (`review/pins.yml`): the pins document, below. Its own counter and log; never in the revision or undo.

The source files stay the truth. `.oymap/` (git-ignored) keeps the last state the tool saw and a history of changes
with the source files before and after. An edit made with another tool is found on the next read, recorded as an
`outside` entry with its diff, and can be undone like any transaction. **`oymap record <project> --author
agent:<name> --label "<what>"`** names the author of such edits: it records the change on disk now and puts the
author and label on every unattributed `outside` entry since that author's last entry (and lists them). Agents that
write files with a generator run it after each run. A history kept by an older core (one revision over every file,
`build` entries for lock changes) is re-keyed on first open (`.oymap/migrations.log`); undo passes over its `build`
entries.

## Pins from the game (S5a1)

`pin <text>` in the game's debug console writes the note, the pose (as `loc` prints it) and the game's own picture
into the pin inbox (`pins_inbox/` in the repository for `tools/run_game.sh --isolated` runs; `[debug]
pin_inbox_path`). Every `oymap install` (`--mount` and `--root`) writes `worlds/<world>/maps/<stem>.studio.yml` beside
the map (the project folder, the source revision and lock hash the build was made from), and the game copies them
into each pin. Then:

```
oymap pins import pins_inbox [--project <folder>]... [--search <folder>]...   file each pin into its project
oymap pins list <project> [--status open] [--json]       the pins (open, claimed, resolved, accepted, declined)
oymap pins claim <project> pin:p3 --by agent:<name>      take one before working on it
oymap pins tour <project> --pin pin:p3 --out tour.yml --shots <folder>   a screenshot tour at the pins' poses
oymap pins resolve <project> pin:p3 --by agent:<name> --text "<what was done>" --picture <after.png>
oymap pins reply|decline <project> pin:p3 --by <author> --text "..." [--picture ...]
oymap pins accept|reopen <project> pin:p3 [--text "..."]  the person's
oymap pins keep <project> pin:p3                          keep its picture in review/pictures/ (in git)
python3 calibration/pins_page.py                          output/studio_review/pins.html: every project's pins, before and after
```

The importer files a pin into the project its studio file names, else into the one project that builds or overlays
its map (`--project` settles two; without `--project`, projects are searched under `--search`, `OYMAP_PROJECT_ROOTS`
or `devdocs/map_studio/briefs` and `devdocs/xeen/briefs`: not `output/studio_cal`, whose many scratch copies of each
project would make every match by name ambiguous). Its picture moves into
`<project>/.oymap/pins/pictures/` (outside git), the pin file into `<inbox>/imported/`; a pin whose picture has not
arrived yet waits for the next import. `review/pins.yml` is pins format 1 (`schema/pins.schema.json`): `counter`, and
per pin the text, `on` (a top-level id, with `file` where two files share it) or `at`, the pose, picture, author,
times, the source revision and lock hash it was made against, `status`, `claimed_by` and the thread of `replies`
(each with its revision and pictures). A format 0 file is read as format 1 and written as format 1 on its next
change. Every change raises `counter` and appends to `.oymap/pins/log.jsonl`. The request list has the same methods
(`pins.*`, `project.record`, `project.lock_prune`).

## Walk mode and Play here (S5a4)

In the browser's 3D view, `G` walks the map: the host builds the project (`host.walk_prepare`), and the WebAssembly
core in a Web Worker (`build-wasm*/oymap_worker.mjs`, served at `/core/`) loads what the build wrote beside the map,
`<stem>.walk.yml` (the movement state: a `studio_walk` block with the party's size, the doors by project id, the rooms
by sector and an outdoor map's bounds, then the scene without what movement never reads) and outdoors
`<stem>.walk.terrain` (tile attributes and land mask), with the asset root's `decoration_data.txt`, all from the host's
`/walk/` route. Each frame sends the keys to `walk.step` (`schema/rpc/walk.rpc.json`); the game's own movement
controllers move a party of the game's size. A click takes the mouse (pointer lock), `Esc` gives it back, a second
`Esc` leaves; WASD or the arrows walk, Shift runs, Space jumps; a click while looking opens or shuts the door, lift or
mover in the middle of the view (`walk.toggle`; an open door is drawn away). Events, monsters, traps, ladders and
swimming do not run: `F5` (Play here) builds, installs into the host's mount and starts the game at the camera
(`game.play_here`: `tools/run_game.sh --isolated` with `--extra-mount` and the launch directives
`debug.startup_console_file`, a `tp` to the pose, and `debug.exit_pose_path`); when the game closes, the camera goes
where the party stood (`game_exited`). The walk's yaw turns into a direction through the core's own sin and cos, so
a recorded walk gives the same poses natively and in WebAssembly (`walk.replay`; the contract suite's `walk_indoor`,
with the shapes gallery's hinged door, and `walk_outdoor` on Harmondale).

```
node web/scripts/walk.mjs [--only shapes] [--no-play]     walk mode and Play here in headless Chrome: shots, timings
node web/scripts/camera_check.mjs [--skip-game]           the studio's camera against the game's at one pose
```

The 3D view keeps the game's camera (eye 160 indoors, 176 outdoors or world.yml's, 60 degrees of vertical field of
view): in a view narrower than 16:9 the field of view widens so the game's whole frame fits (walk mode outlines it;
`web/src/viewport/gameCamera.ts`).

## Scorecard, compare, jobs and flow (S5a5)

The host runs what takes more than about a second as **jobs** (`host/src/jobs.mjs`; `schema/rpc/jobs.rpc.json`:
`jobs.start`, `list`, `status`, `cancel`, notices `job_progress` and `job_done`), never on lane I: on **lane J**, a
second `oymap serve` of the same binary, the checks (`check.audit` with `reach` and `solve`: one walk serves the solve
and the audit's questions) and `compare.run`; as processes of their own, the Python checks (`calibration/scale_bands.py
--json`, `town_feel.py --project --report-json`, `building_shots.py --mount`; local mode only, `session.hello`'s
`host.python`) and the game's runs (`pins_tour`: `pins.tour`'s shots at the pins' poses, built and installed into the
project's play mount; `playtest`: the project's scenario `runs` times). Each lane runs one job at a time; cancel kills
lane J's core (started again for the next job) or the job's process group. A job's files (result, log, pictures) are in
`<project>/.oymap/jobs/<revision>/<job>/` (the newest 40 kept), served at `/job/<key>/<revision>/<job>/<file>`; every
kind's result has an output schema (`$defs/<kind>_job_result`).

**Background checks**: when a browser opens a project, and a few seconds after each change, the host queues for the
revision the checks, the compare of a rebuild (its `map_stats.reference`) or the room sizes of a new dungeon, and an
outdoor map's town feel, unless they ran for that revision (`--background off` stops them). The browser's
**Scorecard** shows one card per check with the revision it belongs to (greyed when older); **Jobs** every job with
its last line and a cancel; **Pictures** the game's pictures by job; the Pins panel's **Tour pins in the game** button
runs a pins tour and shows each pin's picture in its thread, to reply or resolve with. The **Compare** view draws the
original (`view.original_mesh`, from the asset root, moved by the compare's vertical offset) beside the rebuild with one
camera, and the worst places (outdoors also the 64 regions) to go to; the plan's **compare heat** shows every stand
point's or block's score. The **Flow** view draws the solve's steps as columns of rooms, openings and doors with the
events that open them, the critical path to `plan.yml`'s goals, and the wiring with links to the objects.

```
node web/scripts/s5a5_shots.mjs [--only gallery|fortress|xd04|harmondale|jobs|tour]   screenshots of the above
```

map_exec's `oymap()` runs only the commands that still have no method (export, flow of every handler, things on a
shipped map, install into a scratch root, scene-roundtrip, build-map, compile-indoor); the others answer exit 2 with
their method (`compare.run`, `check.metrics`, `check.probe`, `project.import`, `project.fmt`, `view.render_sketch`,
`pins.tour` came with S5a5).

## Overlay projects: changing a shipped map

`oymap import` writes a project whose `base` is a shipped map, with the map's doors, events and sectors named in
`ids.lock.yml` (`door:d57`, `evt:e20`). A wiring event with `replaces: evt:e20` takes that handler's place;
`oymap build` writes `<map>_<project id>.lua` (only the handler is replaced: timers, titles and chest links stay)
and runs it against the base script. [examples/goblinwatch_vault](examples/goblinwatch_vault) and
[examples/new_sorpigal_wells](examples/new_sorpigal_wells) are the reference overlays. An overlay also changes the
base map's scene (S6, S8a: lights, sounds, spawns, destructibles, water, ladders, and new monsters and floor items)
and its cinematics (S8a): below, and [examples/s8a_isle_extras](examples/s8a_isle_extras) for all of it at once.

## MM9 profiles and extras (S6)

devdocs/map_studio/S6_PLAN.md has the plan and the game changes S6 needed (G1-G5, made in the game since; the
studio writes what they read since S8a, below).

- **Overlay projects that change a scene** (`objects.yml scene`): `oymap import` now names a shipped map's scene things
  in ids.lock.yml (`light:k<key>` pulsing lights, `sound:a<key>` ambient sounds, `destructible:k<id>`, `water:<name>`,
  `spawn:s<index>`) and gives the card its profile (`region`: open to the sky with terrain, `city`, `dungeon`). An
  overlay project adds pulsing lights, ambient sounds, spawn points, destructibles (on the base map's face cogs or
  decorations) and water volumes at absolute positions, changes and removes the base map's own (`scene.changes`,
  `scene.removals`), and atmosphere.yml's `open_sky`, `scene_fog`, `daylight`, `terrain` and `mist` replace the base
  scene's blocks. `oymap build --assets` writes `<stem>_<project id>.scene.yml` (each touched list whole: the game
  replaces a list with an overlay's), checked with the game's overlay reader over the base scene, and new things'
  numbers in ids.lock.yml (lights from 49001, sounds and destructibles from 60001); install copies it beside the map
  (and takes away one the project no longer makes). `view.overlay` (and the drawer's **Overlay** tab, MCP `map_view`)
  shows the base map's things with what the project does to each. Examples: `examples/s6_overlay_goblinwatch` (MM6),
  the Isle of Ashes overlay in `output/studio_s6/isle` (MM9 region).
- **Destructibles** (`objects.yml destructibles`: `of` a platform, level, panel, plate, region, door or decoration;
  `hp`, `damage`, `trigger_only`, `material`, `sound`, `effect_scale`, `on_destroyed`, `on_damaged`), effects
  `destroy`, `damage_destructible`, `breakable`, `unbreakable`, condition `destroyed`; events run by them take
  `trigger: call` (no source).
- **Water volumes** (`objects.yml water`: `of` a room or level, or an `outline`, with `top`, `bottom`, `liquid`,
  `tint`, `current`): the party swims there; the surface the player sees is a platform with `solid: false`.
- **Ladders** take `grab_in_air`; **sounds** `day_only` and `night_only`; a **surface** `sky: true` (the faces where an
  open sky shows); atmosphere.yml's scene blocks above also build into a new map's scene.
- **Cinematics** (`wiring.yml cinematics`: shots with a camera `at` and `look_at` (a point or an object's id) or
  `yaw`/`pitch`, `fov`, moving shots by `keys`, `party: true`; cues `event`, `sound`, `subtitle`, `fade`, `letterbox`,
  `shake`, `monster` with `action`), played by the effect `{cinematic: id}` or `{cinematic: {id, then: <event>}}`:
  `<stem>.cinematics.yml` beside the map, checked by the format's rules and then by the game's own parser
  (`game/gameplay/CinematicLibrary.cpp`, part of the shared core since G4).
  The drawer's **Cinematics** tab draws the timeline and the camera at a scrubbed time.
- **Mods** (`oymap mod pack|install|disable|enable|list`, `schema/mod.schema.json`): builds packed into a mod folder
  with a manifest and the table rows the maps add (`tables/<table>.append.txt`, `.override.txt`); `install --layout
  merged` writes the loose mods folder (the game mounts it in front of every named mod) and composes each table from
  the asset root's and every installed mod's rows; `disable` takes a mod's files out and composes the tables again,
  `enable` puts them back; `--layout named` writes `mods/<id>/` and adds the mod to `mods/enabled.yml`: the game's
  named mods ([devdocs/NAMED_MODS.md](../devdocs/NAMED_MODS.md)), mounted at its next start in the list's order, with
  their table rows composed by the game; `mods disable|enable <id>` in the game's console switches one for the next
  start.
- **The MCP App viewer**: the resource `ui://openyamm/viewer` (`host/src/viewer.html`) and the tool `map_view` that
  names it; `node web/scripts/s6_shots.mjs` shows it in a stand-in host.
- Test map: `examples/s6_breakwater` (a barricade and a barrel that break, a pool with a ladder, a yard open to the sky,
  a night sound and an arrival cinematic) with its `playtest.yml`.

S6's second run:

- **Leaning ladders**: `ladders[].top_at`, the top's point on the plan when it is not over `at` (45 degrees at most);
  `exit` defaults to 64 beyond it; the rails lean along the line and the rungs follow it. The game climbs it along the
  line (its leaning ladders, 2026-10-31). Test map `examples/s6_loft` with a `playtest.yml` that climbs it up and down.
- **Mods in the request list**: `mod.pack` (projects built first, `maps: [first, last]` declaring the mod's map numbers as
  mod.yml `idRanges.maps`), `mod.list` (merged, named and packed mods with their numbers and ranges) and
  `mod.map_number` (the first free map number of the mod's range, else the world's world.yml `idRanges.maps`, else the
  studio's 9400 to 9999; taken: the asset root's map_stats, every mod in the folder, the projects given; overlapping
  ranges warned of). Command line: `oymap mod pack ... --maps 9500-9549 [--build]`, `oymap mod map-number --world <w>
  --assets <root> [--mods <folder> --mod <id>] [<project>...]`. The host names its own mods folder `default`
  (`--mods`, default output/studio_host/mods); the project list's **Mods** view lists it and packs projects into it, the
  New project form proposes the number of the world or of a mod; MCP `map_new` proposes one when none is given.
- **The world view**: `world.view` (projects by world, their maps, and links where the map cards' `neighbours` lead, to
  another project's map or a shipped map; a rebuild or overlay stands for its original; the objects that use each
  neighbour; ways out the files name by `map:` that no neighbour declares, kind `undeclared`). The project list's
  **World map** draws each world: outdoor maps on a grid by their map edges' sides, dungeons round the map they open
  from (`web/src/model/world.ts`).
- **Lighting bakes as jobs** (`jobs.start` kind `lighting_bake`, the Jobs tab's Bake lighting; local only: Blender and
  the game): the project built, a hard-link copy of the asset root made under output/studio_host/bake_roots (never the
  asset root), the build installed into it, `tools/lighting/bake_indoor.py` or `bake_outdoor.py` run on it, the
  sidecar's pages drawn as pictures and the game's view from the start before and with the bake (`host/src/lighting.mjs`);
  the copy is removed. `samples` and `units_per_texel` params; the sidecar and its recipe stay in the job's folder.
- **The Overlay tab's tools** (Author mode): pick a thing on its plan and change it (a base thing by an entry of
  `scene.changes`, the project's own in place), take a base thing out or put it back, delete one of the project's, add
  a light, a sound or a spawn point by a click, move the project's own (`web/src/model/overlayEdit.ts`).
- `node web/scripts/s6b_shots.mjs [--bake]` takes these pictures (output/studio_s6b/shots/).

S8a (the game's G1, G2, G5 written by overlay projects; devdocs/map_studio/S8_PLAN.md):

- **Ladders in an overlay** (`objects.yml scene.ladders`: `position` [x, y, z] of the foot, `facing`, `height`,
  `top_at` for a leaning one, `width`, `reach`, `exit`, `grab_at_top`, `grab_in_air`, as a new map's ladders say them;
  no rails are built: an overlay adds no faces). `oymap import` names the base map's ladders `ladder:<id>` in
  ids.lock.yml `ladders`; `scene.changes` moves one (`offset` [dx, dy, dz]), turns it (`facing`) or changes `width`,
  `reach`, `exit`, `grab_at_top`, `grab_in_air`; `scene.removals` takes one out. The scene overlay's `ladders` is the
  base list with these, then the overlay's own (the game replaces the list).
- **Monsters and floor items in an overlay** (`scene.monsters`: `position`, `monster`, `facing`, `hostile: true`,
  `group`, `hp`, `name`, `immobile`, `hidden`, `carries`; `scene.items`: `position`, `item`, `gold`): the records a new
  map's `monsters` and `items` make, written as the overlay's `authored_content.actors` and `sprite_objects`, each in
  the base map's sector at its place. The game appends them after the base scene's (and earlier overlays'), so the base
  map's actor numbers stay and the overlay's follow: the build counts the base scene's actors and those of the world's
  overlays applied before its own, and what names an overlay's monster by number (wiring `kills: {monster}`, a
  cinematic's `look_at` of a monster and its `monster` cues) gets that number; `kills: {group}`, `show_actors` and
  `hide_actors` may name a group of the base map's actors and spawn points. The world's own monsters and items (its
  world.yml `tableContributions` appending to monster_data, monster_descriptors and items: MM9's) may be named.
  `hostile: false` is refused (a new map makes a group peaceful by an event on entering the map, which an overlay does
  not add).
- **Cinematics overlays** (`wiring.yml cinematics` in an overlay project): `<stem>_<project id>.cinematics.yml`, which
  the game merges by name after the map's own (G2). `oymap import` names the base map's cinematics `cinematic:<name>`
  in ids.lock.yml `cinematics`; one of the project's of that id replaces it in place, another is added (build.json
  `cinematics_replaced`, `cinematics_added`). Cues name the base map's events by their lock ids (`evt:e31014`) as well
  as the overlay's; an overlay's events may play a base cinematic by its lock id. Checked by the game's own parser;
  installed beside the map (and removed when the project has none any more).
- `view.overlay` lists ladders (base and added), the added monsters (with their actor numbers) and items, and
  `cinematics` (each base one kept or replaced, the project's added); the Overlay tab places ladders, monsters and items
  by a click and moves a base ladder by its `offset`; MCP `map_view` lists what the overlay touches.
- Example: `examples/s8a_isle_extras` (Isle of Ashes: a ladder up the fort's wall, a Skeletoid as actor 77, a
  longsword, a new cinematic and `book_sinking` replaced) with its `playtest.yml` (35 steps, played headless with the
  build installed into a mount; fails without the mount).

## Ground for open-air maps (S8b)

An indoor map open to the sky can have its ground drawn as an outdoor map's terrain: blended library materials
instead of its textures (devdocs/INDOOR_OPEN_SKY.md "Terrain"), as MM9's regions are. atmosphere.yml `ground`
(opt-in; new indoor maps only, not with `terrain`, which names files made elsewhere):

```yaml
ground:
  layers:                                # one to four, one weight channel each, in this order
    - {material: grass, textures: [cgrajnkrow], color: [64, 72, 24]}
    - {material: dirt, textures: [thjodbs7wo]}
  materials: [{name: dirt, repeat: 480}] # the world's materials changed, or new ones (`library` and the keys)
  slope: {material: cliff}               # steep ground; default the world's; {off: true} for none
  grass: worlds/mm9/terrain_decorations/drangheim_blv.yml
```

- A layer's `material` is one of the world's (worlds/<world>/terrain_materials/world.yml `materials`) or of the
  ground's `materials`; its `textures` are the surfaces whose faces are that ground (floors, banks by
  `floor_surfaces`, platform tops: any face). `color` (0-255, the colour the ground should read as) gives its tint
  over the library material's mean colour, no channel lifted over the brightness ratio; or `tint` itself; neither:
  none. `cliff_tint` the steep ground's.
- `oymap build --assets` rasterises those faces of the built map from above (the topmost face over a 32-unit texel
  wins), gives texels no face covers their nearest face's layer, blurs each layer over `edge_softness` (default the
  world's), normalises and writes `<stem>_blv_weights0.png` (2048 square, RGBA) and `<stem>_blv.yml` (the material
  file: the weighted layers, then the slope material and the materials' variants, at most eight) beside the map,
  and the scene's `terrain` block (`materials`, the textures on the weighed faces, `grass`). A floor 128 or more under
  another ground face (a tunnel under a hill) is drawn as a face with its texture (`exclude_faces`) unless `covered:
  terrain`. The material file is read back by the game's own `parseTerrainMaterialConfig`; refused: an unknown
  material or library material, a library picture missing from the root, a texture in two layers, more than four
  layers, no face of a ground texture. Warned: a layer texture on no face, a grass file not in the root, ground
  without `open_sky`.
- `oymap install` puts the pair in `worlds/<world>/terrain_materials/` of the root or mount (and takes away an old
  pair it wrote when the project has no ground any more).
- The same steps as MM9's `level_generation/projects/mm9r_common/terrain_blend.py` (scipy's Gaussian and nearest
  feature transform ported): on all twelve MM9 regions, fed terrain_blend's own inputs (its layer order, texture
  colours and exclusions) by `oymap ground`, the weights are identical texel for texel and the material files
  equal value for value (`output/s8b/parity/parity.py`). The PNGs are compressed differently (the core's own
  deflate: fixed codes, 1.3 to 2 times the size of the zlib streams terrain_blend.py writes).
- Test map: `examples/s8b_meadow` (a hollow open to the sky: a grass hill, a dirt track, a rock knoll whose steep
  sides take the world's cliff), with its `playtest.yml`.

## S8g: what the Xeen map agents found (2026-11-16)

Defects and words from the Act II maps (devdocs/xeen/ACT2_BUILD.md; each map's NOTES.md). Unit cases in
`tests/S8gTests.cpp` and `tests/OutdoorTests.cpp`.

- **East-west travel** (`core/OutdoorInstall`): the arrival word is the game's (east arrival `left`, west arrival
  `right`; see "Leaving the map"). A project whose `arrival_side` was set to work round the old words must say the
  true side now (Erathia's and Harmondale's west edges, X1 and X2 were changed with it).
- **Installs into one mount** keep each other's table rows (above, "To try a built map in the game").
- **Sounds** (`objects.yml sounds[].sound`): any .wav the game finds for the world: its own `worlds/<w>/audio` and the
  engine's `engine/audio` (subfolders by the file's name or its path), of the asset root and of `--mount`, in any case,
  with or without `.wav`. Before, only `worlds/<w>/audio` of the root counted (`rushing water loop`, `drip01` refused).
- **`--mount` on validate and build**: see "Commands".
- **Two wiring events of one id** are refused (they were built as one handler with both sources).
- **`rules.no_spells: true`** (project.yml): the scene's `runtime_restrictions: {allow_spellcasting: false}`, indoors
  and outdoors (the spellbook, quick spells and scrolls refused, as in MM7's Shoals); refused in an overlay project.
  The game's refusal line is its underwater one ("You can't do that while underwater").
- **`walls[].bands: false`** (rooms.yml): the wall's own `surface` runs from floor to ceiling over the room's bands.
  Left out, as before, the bands lie under the wall's surface (the Hive's dome walls rely on it).
- **`map_stats.bolster`** (project.yml: `LowerToEqual`, `AllToEqual`, `OriginalStats`, `none`): the `Bolster kind` of
  the map's row of `bolster_maps.txt`. An indoor map gets a row only with it (the reference's row under the map's
  number, else a plain row on the world's continent whose monsters may take new spells, as the shipped dungeons');
  an outdoor map's row (always written) takes the kind from it.
- **A doorway's `floor`** (sketch.yml, outdoors): the sill's height against the plan's datum (`raise` on top); left
  out, the land's at the doorway's middle.
- **A model's `turn`** (sketch.yml `kind: model`): the models taken turn about their middle, degrees clockwise seen
  from above (MM7's ships lie north to south; X2's river runs east to west).
- **Monster hostility (2026-11-16, `core/MonsterRelations`)**: sketch.yml `relations` outdoors, the same list as
  objects.yml's (one reader and one event `evt:studio_relations` for both; the schema is common.schema.json
  `$defs/relations`). The game sets a monster's relation to the party by its kind (each tier's number), never by
  group. The build warns, with the row to add, where MMerge's `hostile.txt` leaves a slot's monsters friendly to the
  party, where placed monsters without `hostile` are friendly beside hostile ones of their kind, and where two kinds
  both hostile to the party are set on each other (kept apart by `{of: [...], toward: <kind>, relation: friendly,
  both_ways: true}`); kinds of a `reference` row's own slots are left as shipped, so rebuilt shipped maps stay quiet.
  The build reads `hostile.txt` and `map_stats.txt` beside `monster_data.txt` (none: no check). Unit cases in
  `tests/MonsterRelationsTests.cpp`, `OutdoorTests.cpp` and `CoreTests.cpp`.

## The hosted page (S5c)

The same web app with the core in the page's worker instead of a host (`web/src/hosted/`; S5_BROWSER_EDITOR.md 2.2
"Hosted mode", PLAN.md 9): a person opens the game's files (a player's install, its packages, or a checkout's
`assets_dev`) and a project (a folder: read-write through File System Access in Chromium; read only elsewhere, then
a working copy in the origin's private storage; a zip; or a new or imported one), and views, edits, walks, checks
on request and builds there, byte-identical to the native build. Exports: the project, the build, and the build as
a mods folder (zips, or written into a folder). Play here, playtests, the Python checks and agents need the studio
on the person's computer: the page pairs with `oymap studio --allow-origin <the page's origin>` from a button, after
the browser's local-network prompt; the token is pasted, kept in the tab's session storage and sent as a WebSocket
subprotocol, never in a URL.

```
./build.sh wasm                                    # the core (build-wasm/oymap_worker.mjs and .wasm)
(cd web && npm run build && node scripts/stage_hosted.mjs --version <v>)   # hosted_site/studio/<v>/ as an origin serves it
node web/scripts/hosted_server.mjs --port 8790     # a local static origin standing in for it
node web/scripts/s5c_hosted.mjs                    # Chrome and Firefox end to end: install, slice, 22 projects, budgets, pairing
node tests/hosted_node.mjs --core build-wasm/oymap_worker.mjs --assets <install> --out <folder> <project>...
python3 tests/extract_install.py <install> <folder>   # an install as a development tree, for the native reference
```

`hosted_site/` is what a deploy copies to the page's own origin: `studio/<version>/` per release (the app with its
`index.html`, the core under `core/`, `version.json`, the service worker `sw.js` with the release's file list),
`studio/versions.json`, and an `index.html` sending a visitor to the newest version. The headers a static host
should send are in `web/scripts/hosted_server.mjs` (the content security policy allowing only the page itself and a
paired studio on 127.0.0.1, `application/wasm`, immutable caching of `assets/` and `core/`) and the compressed
copies `stage_hosted.mjs` writes beside each text and wasm file (`<file>.br`, `<file>.gz`, sent with
`Content-Encoding` to a browser that accepts them, `Vary: Accept-Encoding`); a real host should do the same.

**Speed and size (S8f).** The wasm core stays at `-O3` with Emscripten's dlmalloc. Tried and not kept: mimalloc
(CMake `OYMAP_WASM_MALLOC=mimalloc`: an indoor commit about 15 % sooner, but Castle Darkmoor's checks job grows the
wasm memory to 1.1 GB against dlmalloc's 193 MB, past the hosted page's 1 GB), `-Os` (the core 1.86 MB as Brotli
instead of 2.2, every edit about 30 % slower), `-O2` (the same size as `-O3`), ThinLTO (5 % larger, no measurable
gain), no `-fPIC` (no gain), wasm-opt's `-Os`/`-Oz` after linking (no smaller). The first opening of a project was
slow in Chrome (8-15 s on a checkout's `assets_dev`) not because of the wasm's lazy compilation (V8's
`--no-wasm-lazy-compilation` changed nothing) but because the asset folder's file input kept its 81 000 files in the
page's form state, which Chrome copies into the history entry on each address change: the start page empties its
inputs once it has their files. After an edit the tree its answer parses from each changed file's text is kept
for the read-back the next call did again, and its JSON for the next `project.open`; the app loads the history after
the views; the view mesh is built with one group lookup per run of a texture. The budgets are measured with
`node web/scripts/s5c_hosted.mjs --parts budgets --gestures` (the person's own gestures through the app's edit
session, timed to the 3D view drawing the new mesh, beside S5c's direct calls), `--parts firstopen` (the opening
alone, with the core's download size), `--site <staged site>`, `--native <oymap>` and `--chrome-args` for
experiments.

## The host and the MCP server

```
cd host && npm install
node src/host.mjs mcp                      # MCP over standard input and output
node src/host.mjs serve --port 8765        # WebSocket JSON-RPC for the browser editor (prints the pairing address)
node src/host.mjs studio --allow-origin https://studio.example   # also lets that hosted page pair (S5c)
node src/call.mjs --list                   # the tools as a client sees them
node src/call.mjs map_flow '{"map":"6d01.blv","world":"mm6","event":20}'
```

The host holds no map logic and no state: it starts `oymap serve` and maps its tools onto its commands
(`map_open`, `map_overview`, `map_edit`, `map_validate`, `map_query`, `map_flow`, `map_render`, `map_assets`,
`map_api`, `map_build`, `map_playtest`, `map_pins` (over `oymap pins` since S5a1), `map_history`, `map_exec`, and
`map_new` since S3). To use it
from Claude Code:
`claude mcp add map-studio -- node <repo>/openyamm-studio/host/src/host.mjs mcp`. Options: `--assets`, `--game`,
`--mount` (where builds are installed; default `output/studio_host/mount`), `--oymap`.

## Layout

```
core/      new code: JSON and canonical YAML writers, schema validation, projects, operations and history, lowering,
           build, install, export, audit, reachability, event flow, import, renders
cli/       the oymap commands
host/      the Node host: MCP server, WebSocket endpoint, one-shot tool caller
eval/      the agent evaluation: tasks, checks, results
schema/    the project format, schema v0
examples/  reference projects
tests/     unit tests, fixtures and the acceptance scripts
wasm/      notes on the WebAssembly build
cmake/     dependencies and the schema embedding
```

## Rules for code here

- yaml-cpp nodes alias the tree they come from. Look keys up through a `const YAML::Node` (the non-const
  `operator[]` adds the key), never assign one node to another to move it (it rewrites the tree; sort positions, not
  nodes), and do not use `YAML::Emitter` (it breaks the wasm build's exit; use `core/CanonicalYaml`).
- Output must not depend on the platform: no unordered containers on the way to output, numbers through
  `formatNumber`, files through `write*FileAtomically`.
- Coding style as in the repository's AGENTS.md.
