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
tests/build_map_parity.sh  # oymap build-map against maps the editor built: the same bytes (OYMAP=<binary> for another tree)
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
            [--dressing]
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
  the land at its ends, humped by `rise`, or level at `height` on piers: a pier; an end on the land stands `raise`
  over the lowest land across it and 32 beyond, or halfway up where the land falls more than twice that across it, so
  no side meets a step over half the fall: P3 2026-11-24, D4's Snow River bridge), `well`, `fountain`, `obelisk`,
  `chest`, `crate`, `sign`, `platform`, `stairs`, `doorway` (a door in a frame against a slope: the way into a cave)
  and `decoration` (one decoration of the game's table by name). What a click does is said with the structure:
  `title`, `house`, `into`, `chest` (level, random_items, items), `effects` (text, gold, add, subtract, set,
  autonote, qbit, clear_qbit, give_item, teleport, lua), `once`, `lua`. `actors` place townsfolk and guards by
  their monster row (`monster`, `at`, `count`, `spread`, `group`, `hostile`). Any structure may say
  `translucent: true` (Xeen merge point 23, D5's Barrier curtain): its faces draw see-through, blended by their
  texture's own alpha and sorted back to front, and stay solid; the build lists them in the scene's
  `bmodel_faces.translucent_faces` (devdocs/INDOOR_TRANSLUCENT_FACES.md, "Outdoor BModel faces"). No opacity number
  outdoors: give the texture a graded alpha.
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
  The numbers events name things by are kept in ids.lock.yml `cogs`. As indoors (Xeen, 2026-11-20): `{player_bit:
  n}` as a condition and an effect (`clear_player_bit`), the bit of the member who clicks; `question: {ask, answers,
  message, wrong_text, wrong_effects}` asked after `once` and the lock, the rest running on a right answer, the
  `wrong_effects` (effect words, as indoors) on any other; and in any of the
  handler's Lua `ShowThing("thing:x")` / `HideThing("thing:x")`, written as the calls `{show}` and `{hide}` write
  (statements), so a Lua branch changes what is drawn at once. A world without kits of its own (Xeen) may name any
  shipped world's texture, as the game mounts them all.
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
  A side that leads to two maps (Xeen's X4 south edge, D-11.6) gives each neighbour a `span: [from, to]` (units along
  the side: x for north and south, y for east and west) and its `arrival` and `direction`: such a neighbour is no
  travel table row (one map per side); the game reads it from a world's `edge_spans` table (`map, edge, from, to,
  to_map, side, days, at, facing`: `game/tables/MapStats.h` `MapEdgeSpan`), which the world's generator writes. The
  party meeting the side inside a span goes the span's way, elsewhere the side's own row's.
- **Named arrivals** (D-4: a dungeon with several mouths): every build lists the map's arrivals in build.json
  (`named_arrivals`): `start`, and each plan.yml entrance of kind arrival or both (outdoors where its sketch point
  stands; indoors at its objects.yml `arrivals` entry `{entrance, room, at, facing}`, else at the start when the
  start's room realises the entrance's space, else in the middle of such a room). `oymap install` writes them into the
  map's `<stem>.studio.yml` (`arrivals`). A door of another map names one with `into: {map: xeen_xd10.blv, arrival:
  entrance:x5_south}` (instead of `at`; its facing too unless `facing` is given), an indoor exit with its neighbour's
  `arrival: entrance:<id>` (instead of `[x, y, z]`; its facing unless `direction` is given). The build looks the name
  up in the installed map (the mount first): a map not installed yet gives its start with a warning, an installed map
  without the name is an error listing the names it has. Build the target map and install it first.
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
  import: heights as in the source map (`raise` moves them). `from.world` takes them from another world's map
  (`from: {world: mm7, map: 7out03.odm, models: [...]}`: Nystor's ship on Xeen's X2); otherwise the project's own.
  `drop_overlaps: true` drops, of each two faces taken that lie in one plane over each other (the same way, or back to
  back where that is seen), the smaller (the later of two alike): a shipped model that flickers in its original
  (MM7's Lady Catherine: hull boards and trim back to back; P3 2026-11-24).
- **A Blender model** (`kind: model` with `from: {glb: <file>}`, `core/OutdoorGlb`; Hesper H-44, 2026-11-25): a
  landmark or a dungeon's mouth made in Blender in map units (`scale` otherwise) and exported as glTF with Blender's
  defaults (+Y up; `up: z` for a file in the map's axes). The file lies beside the project, else in the world's folder
  of the asset root. Each mesh is a BModel named after the structure (the mesh in its second name); its triangles of
  one material that lie in one plane, share an edge and carry one continuous picture are joined into convex faces of
  up to 20 corners. A material is the world's texture of its name (Blender's `.001` endings left off), or what
  `textures` maps it to: a name, or `{texture, liquid, flow, invisible, untouchable}` (a collision-only slab, foliage
  one walks through); a texture the world lacks is refused, as for every structure. UVs become texels by the
  picture's size in the game (a face without UVs lies one texel to a unit). `at` puts the model's middle there with
  its lowest point on the land (`raise` over it, `turn` about its middle); without `at` the file's coordinates are
  the map's. Faces are solid unless `ethereal` or a material says otherwise. `click` names the meshes that run the
  click, the others say the `hint`. Refused with the face named and where it stands: a face under `min_area` (32
  square units), a corner sharper than `min_angle` (2 degrees: a sliver whose picture does not run on into its
  neighbour), a concave face, more than `face_budget` faces in a mesh (1000). Not for a model: `trigger: step`,
  `drop_overlaps`. Example: `examples/glb_gate` (the fixture `tests/fixtures/glb/box_arch.glb`, made by
  `make_box_arch.py` there with `blender --background`).
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
  `verge` on a box's gable (2026-11-24, Xeen's classic Clouds kit: the slopes run on that far past each gable end,
  with a barge board `barge` high under the roof's edge there in the `trim` texture; the eaves' fascia runs on
  with them; `verge_walls` names the ends that take it, the other flush where a wing or shed stands against it);
  `pent` on a part (a skirt roof round the walls at a storey); `flare` (walls leaning out, a batter the other way:
  Castle Gryphonheart's bailey); `porches[].open_corner` (a recess to its wall's end open at that corner, the wall
  across standing back by its depth: HouseR2S); `doors[].sill` (a door standing over its row's foot, a whole door
  high, the rows above over it: the King's Library door); bridge `kerb_width` (it was read only on walkways) and
  `arches.spans` (openings of their own widths: Erathia's viaduct); sign arms `toward` in degrees (the guild sign's
  three boards); platform `chamfer` (an octagonal deck); culvert `grating` (bars before the dark face, the upright
  ones from 2 under the water: P3 2026-11-24); tent
  `roof: hip` (a pavilion) and a door on a closed tent's front (`textures.door`, `door_width`, `door_height`); a
  doorway's `facing` (n, e, s, w before `turn`; it was read nowhere) and `textures.roof` for its gable portico (a
  turf hood); a doorway's `hood` has no back faces on the frame's front (P3 2026-11-24: X1's Witch Tower door). `oymap audit` warns of a solid decoration in a doorway's way (`thing.in_doorway`, indoors: within its
  radius and the party's 37 of the line through a portal's middle, 0 to 128 to either side: XD-01's stash keg), and
  of a face the party cannot step over standing across a doorway's way out (`face.in_doorway`, P3 2026-11-24: walking
  straight out of the opening along every line across it, the party's middle does not get its radius past the
  jambs; faces over 50 from foot to top, their top over 50 over the sill and their foot under the head and 160 over
  the sill; not a door's leaf, a face over the opening itself, a clicked panel across it, or a drawn face as high as
  the opening: XD-14's long tables, 64 high and 64 off the wall across three doors, an invisible wall only a jump
  passed). An error on Xeen's maps, a warning on others.
- Not built (the build says so in its warnings): boats and stables as travel (a house's service); the plan's
  containers and landmarks unless the sketch draws them as structures.

**A larger map: ODM v2** (Hesper H-33, 2026-11-25; `core/OutdoorGrid`). project.yml `terrain: {side: 160}` (an even
number from 32 to 256; 128, the classic ODM, when left out) builds the map on that many samples a side, written as an
OpenYAMM ODM v2 (`OpenYAMM ODM v2` at 0x40, the side at 0x50: game/outdoor/OutdoorMapData.h `terrainSide`). The
sketch's cells then run 0 to the side (map units: (cell - side / 2) x 512, 40 960 from the middle at 160), and
everything that read 128 reads the side: the lowering, ground, rim, places, things, the sketch's checks and picture,
the walk and the readers of a built map, and the browser editor (`web/src/edit/cells.ts`, set when a project opens).
The square the party walks grows with the side (23 143 x side / 128: 28 928 at 160, nodes 24 to 136, a rim of 24
rows in the north and west and 23 in the south and east); build.json gives it as `outdoor_bounds` with `terrain_side`,
and the world's map_navigation row must carry it (the game's default is the classic square). A ridge's crest stands
15 cells out by default on such a rim (12 on the classic 18 and 19 rows) and may stand up to 20. Faces past the
classic frame keep their texels inside the format's 16 bits by whole 4096-texel periods; bridge footings are held to
the map's frame. A sketch's `map_cells`, when given, must be the side. `oymap compare` reads classic maps only. A
classic project builds exactly as before (33 projects byte for byte; unit cases in `tests/OdmV2Tests.cpp`). Example:
`examples/odm_v2_vale`.

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
own surface. Doors (`oymap schema objects`) slide (`slide_up`, `slide_down`) or swing (`kind: hinged`); a wide door
that reads as double-winged (great hall doors, a castle gate) is `kind: hinged, leaves: 2`: two leaves on the two jambs
swinging apart from the middle, its `surface` one wing (mirrored on the right leaf) or `pictures` one per leaf
(`leaves: 2` on a sliding kind parts the halves sideways or up and down); `lifts` are
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
timer | load`). A room's step event also runs on the tops of its low platforms (standing on its floor, at most 50
high: the game's step up) that run no step event of their own, so a landing on a heap in the room runs it (A7's
DD-11B, Xeen merge point 31); a higher or hanging platform and a level need `sources` (a sky map's clouds and XD-12's
balcony stand in rooms whose floor is the fall below).

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
- **Objects** (`oymap schema objects`): `monsters` (placed, with `group`, `hostile`, `immobile` or `leash` (a home
  radius, the scene's `leash_radius`), `above_floor` (a flyer, or a swimmer in a `water` volume, starts that high over
  its floor), and for a boss `hp` and `name`) and `items`; `decorations` of the engine's table
  and of the project's world's (its `decorations` contribution, with the world's `models/indoor_decorations.yml`);
  `movers` (with `parts`, `block`, riders via `rides`); `plates`, `floors` (lava, water); `ladders`; `sounds`;
  lights with `on: false` and `pulse`; `secret: true` on a door; platforms and wall panels with an `id` as click
  sources.
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
  reads; `wrong_effects`, effect words run on a wrong answer, since 2026-11-20); `trigger: leave`; a decoration as an event's source; `once` on doors, texts, teleports and scripts. A
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
  MM8 dungeons' exits `{picture: 1}`); effects `leave: <neighbour>` (an exit from any event; since decider D-24 `leave` moves at once; ask with
  `question`, or use the `exit` preset for the game's window), `shake: {strength,
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

A world that declares its own map ids (`world.yml` `idRanges.maps`, as Xeen does) owns its maps' table rows: its
generator writes them and the game reads them through `tableContributions` (`devdocs/xeen/lanes/TABLES.md`). `oymap
install <project> --root <root>` then copies only the map's files into `worlds/<world>/` (map, scene, script,
`.studio.yml`, cinematics, ground files) and writes no `map_stats`, travel, bolster or sky row; such a world's maps may
install straight into `assets_dev` (`--root assets_dev`), since every file lands in the world's own folder. `--mount <folder> --assets <root>` writes no engine tables into the mount either (the root's world.yml decides).

`oymap audit` checks that light fixtures hang where they belong (`lights.*`; `core/Audit.h` `auditLightFixtures`,
numbers in `devdocs/xeen/formats/LIGHTS.md`) on Xeen's indoor maps, and on any other indoor map with `--lights`
(`--lights-measure` adds each fixture's numbers). A fixture's mount comes from `engine/models/light_fixtures.yml` (and a
world's `models/light_fixtures.yml`), else its model binding (`swing`: hung, `mount: wall`: on a wall), else its row's
hint: a hung lamp's top reaches the ceiling and its foot stays clear of the floor and of openings; a wall fixture has
a wall within 64 of its middle (the game's own search), not a door leaf, not inside an opening; a standing one rests
on the floor or on a decoration; no fixture, map light or decoration light lies in the rock. The shipped maps'
findings are the calibration (`output/xeen_a1/lights_mm678.txt`).

`oymap audit` checks door leaves and their pictures (`doors.tiled`, `doors.half_wing`, `doors.wing_unmirrored`;
`core/Audit.h` `auditDoorTextures`, numbers in `devdocs/xeen/formats/DOORS.md`) on every Xeen map, indoor and outdoor,
and on any other map with `--doors` (`--doors-measure` adds each leaf's numbers): a door picture shown more than once
across its leaf, one wing of a double door on a single wide leaf, a pair of leaves showing one wing the same way round;
outdoors also `doors.lone_wing`, `doors.part_picture`, `doors.narrow_pair` and `doors.off_steps` (merge point 41).
Outdoors also `houses.buried_door` (a warning; P2 feedback F27, `tools/xeen/town_fit_check.py`'s rule): the land
32 to 160 before a door stands more than 48 over its sill. Outdoors `oymap audit` and the build warn of
`faces.back_to_back` (F31): two drawn faces in one plane facing opposite ways, open space on a side (the game draws
outdoor faces from both sides, so they flicker); the build also of `gates.road_off` (F28): a wall gate's passage or
a bridge's head whose road tiles are centred more than 128 off its middle (road tiles are whole cells).
What each texture is comes from `engine/models/texture_classes.yml` (and a world's `models/texture_classes.yml`),
written by `tools/xeen/texture_classes.py`.

`oymap audit` checks that pictures fit their faces (`textures.feature_repeated`, `textures.feature_cut`,
`textures.trim_tiled`; `textures.storey_stacked` by the texture's `storey_stack`, D-41; warnings
`textures.tile_seams`, `textures.feature_border`, `textures.family_switch`; `core/Audit.h` `auditTextureFit`, numbers in `devdocs/xeen/formats/TEXTURE_FIT.md`) on every
Xeen map and on any other map with `--textures`: a picture meant once (a window, a sign, a panel) repeated or cut off, a
band tiled up its face, a texture whose edges do not meet repeated over a large face, a picture whose border is unlike
the wall it is set into, two unlike wall textures side by side. It judges surfaces: the touching faces of one texture
in one plane whose pictures continue each other. `--textures-measure` prints every surface's copies and the pairs of
neighbouring surfaces. Building parts lay a picture once per bay with `textures.<role>: {texture, fit: true, size: [w,
h]}` (only in the lowest row unless `upper_walls` names the role); an open part's posts in the `trim` lay it on its end.

`oymap audit` checks the props' dressing (`dressing.door`, `dressing.doorway`, `dressing.walking_line`, `dressing.wall`,
`dressing.clump`; `core/Audit.h` `auditDressing`, numbers in `devdocs/xeen/formats/DRESSING.md` and decision D-7.1) on
Xeen's maps, and on any other map with `--dressing`. A room with `store: true` in rooms.yml is a storeroom (clumps and
a second row allowed), as is any room with 8 or more containers. What the audit cannot read from a built map, the
storerooms and the decorations that hang, it takes from the project when given one, and from the installed map's
`<stem>.studio.yml` (`storerooms`, `hanging_decorations`, `trap_doors`, written by `oymap install`) when given the map.
Outdoors the same classes are judged by the houses: a house door is a model's faces whose event enters a house
(`dressing.door`: a container 320 in front or 192 beside, anything else of radius 24+ within its radius and 128 before
it), containers within 512 of a model's wall keep within 240 of it (`dressing.wall`), the walking line runs from 64
before one house door to 64 before another, at most 2048 apart with no wall between (`dressing.walking_line`; a prop
within its radius and 64 of a model's wall is off the line, but must still leave 128 free beside it), and no prop's
body comes within 64 of a road's middle line away from a wall (`dressing.road`); an info line (`dressing.outdoor`)
counts the props, doors and lines checked. The classes (decision D-14): containers are barrels, kegs, casks, sacks,
bags, crates, boxes, buckets, firewood and log piles (hint `wood`); set pieces are any decoration with an event, trees,
statues, pillars, columns, altars, hearths, fires, braziers, cauldrons, vats, fountains, pedestals, shrines, obelisks,
stalls, rocks and boulders; the rest (hay among them) are other props.

With the dressing (Xeen's maps; others with `--dressing`) the audit checks what props and chests stand on and the
chests' looks, the checks of `tools/xeen/check_props_support.py` with its numbers (`core/Audit.h` `auditPropSupport`):
`support.floating` (nothing within 24 under a prop's middle), `support.overhang` (part of its footprint more than 24
over the ground or floor), `support.edge` (a drop of more than 64 within 48 of it; set pieces warnings, plants and
natural rocks not judged), `chest.look` (a chest that is none of the shipped ones), `chest.entrance` (a chest in front
of a house door, an exit, a door, a teleport or a cave mouth) and `chest.title` (a warning: a hover title naming a
place). The ground outdoors is the game's terrain triangles, split north-west to south-east.

Indoors the dressing also checks props inside props or walls by their drawn outlines, the four rules of
`tools/xeen/check_prop_overlap.py` with its numbers (`core/Audit.h` `auditPropOverlap`, F40, 2026-11-24): a prop's
footprint is the plan outline of its bound 3D model (engine/models/indoor_decorations.yml and the world's) as the game
places it (scale, height jitter, yaw), else its collision circle; chests are their faces' box. `prop.overlap` (two props'
lower bodies drawn more than 8 into each other at a shared height; two natural formations a warning), `prop.wall` (a
prop more than 8 into a wall, or with no floor under its middle; loose heaps, bones and formations a warning unless
more than half in it), `item.hidden` (a ground item or a treasure spawn inside a prop's drawn outline, more than 10 in a
wall or over no floor; within a prop's radius plus 20 a warning) and `prop.squeeze` (a warning: a gap of 1 to 96 between
two props' collision circles, open at both ends).

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
- **Translucent surfaces** (any surface's `translucent`: an opacity, or `{opacity, tint, two_sided}`): the faces laid
  with it go into the scene's `translucent_faces` (devdocs/INDOOR_TRANSLUCENT_FACES.md), drawn blended over what lies
  behind and still solid (they collide and block sight, missiles and clicks). A paper screen that breaks (XD-22,
  D-25): a door in an opening between two rooms, with no event, `surface: {texture: ..., translucent: 0.6}`, and a
  destructible `of` it; the opening's portal lets the rooms behind draw, and breaking the leaf opens the way. The
  build warns of translucent faces it cannot find in the compiled map.
- **Parts of a clicked platform** (rooms.yml `part_of: <platform id>` on a platform without an `id`, or on a beam;
  2026-11-24, XD-02's winch): a thing built of several blocks that the player uses as one (a capstan's drum, its iron
  head and its bars) runs the platform's click on every part, and the parts change with the platform (`hide`, `show`,
  `texture`). `tools/xeen/check_wiring_rules.py` `click.covered` warns of a part standing on a clicked platform
  without it.
- **Hinged leaves in both rooms** (2026-11-24, F44): a hinged leaf (not a trapdoor) opens away from whoever opens it,
  so it swings through its doorway: it is built as a rotating mover (`kind: rotating`, `extra_rooms`) whose faces are
  listed in the opening's two rooms, and is drawn while either room is seen (XD-05's gate leaves vanished when the yard
  was seen alone through a window). `tools/xeen/check_door_leaves.py` `leaf.swing_room` checks it.
- **Touch events** (wiring `touch: true` on a clicked event whose source is a door, wall panel, platform, switch or
  exit): the source's faces also run the event when the party walks into them, once per contact (leaning on it does
  not run it again; `once: true` for one time only). Xeen's mirages (XD-10, D-4): `{preset: door, source:
  door:mirage, action: open, touch: true, text: ...}` instead of a plate before the wall. The build gives the faces the
  touch bit beside the click bit and writes the scene's `party_movement: {touch_faces: run}`, without which the game
  runs no touch face (devdocs/INDOOR_OPEN_SKY.md "Party movement").
- **Arenas** (objects.yml `arena`, XD-20; MM7's 7d05 keeps the same in a hand-made `7d05_1.scene.yml`): `{monsters:
  [11010, 11699], party: {room, at, facing}, marks: [{room, at}, ...], ring: {room, at, radius, count}}`. The build
  writes the scene's `arena` block (`marks` and the ring's marks, at least 20, each on the highest floor at its place
  as the start is) and the arena's `runtime_restrictions` (`arena: true`, `allow_save_game: false`,
  `allow_lloyds_beacon: false`: no saving, no Lloyd's Beacon, the fight refilled on each visit). The opponents are the
  world's monster rows in the range, less NoArena and peasant rows (NoArena from `bolster_monsters`); a range with no
  monster_data row is an error. The arena master is any NPC with topic 704 (the four difficulties, the gold, awards
  46-49): `evt.SpeakNPC(<npc>)` from a booth, or a placed NPC. Not in an overlay project.
- **Outdoor sounds** (sketch.yml `sounds`, E9): the scene's `ambient_sounds` outdoors, as objects.yml's indoors:
  `{id: sound:surf, at: [40, 88], sound: waves.wav, radius: 6000, inner_radius: 2500, volume: 0.6}` (`at` in cells,
  `height` over the ground, default 64; radii in game units; `wait`, `loop`, `day_only`, `night_only`, `on: false`
  for a sound a script switches on by `AmbientSound<number>`; `pan: false` for one heard centred, as objects.yml's and
  an overlay's sounds take it too, D-48). The game plays them as indoors
  (devdocs/AMBIENT_SOUNDS.md).
- **Damage hooks** (XD-19, DD-16): a wiring event with `trigger: monster_damage` (no `source`; `monsters: [<monster
  ids>]` and/or `actors: [<placed monster ids>]` to act on those only) is the map's MonsterDamage hook, registered on load (`RegisterMonsterDamageHook`)
  and run before each hit on a monster lands; `{set_damage: 0}` makes the hit do nothing, and a `lua` effect reads the
  hit as `hook` (`hook.monsterId`, `hook.damage`, `hook.attack`: melee, missile, spell or other, `hook.weaponItemId`,
  `hook.byParty`; E11). Indoors only.
- **Decorations shown by an event** (DD-13): objects.yml `decorations[].hidden: true` starts the decoration away (the
  BLV entity's invisible flag and the scene's `decoration_flags`: not drawn, not solid, its light dark), and the
  wiring effects `{show: deco:x}` / `{hide: deco:x}` bring it and take it (`evt.SetSprite(<its number>, 1 | 0)`). A
  block resting on three or more leg blocks round its middle (a table top on four legs) rests on them. A block's
  `end_surface` takes `fit: false` to lie at its size instead of stretched.
- **Chests shown by an event** (merge point 25, P5's wedding gift): objects.yml `chests[].hidden: true` starts the
  chest's box away (its faces Invisible and Untouchable: not drawn, not solid, not clicked), and `{show: chest:x}` /
  `{hide: chest:x}` bring it and take it whole (`evt.SetFacetBit(<its cog>, Invisible | Untouchable, 0 | 1)`); the map's
  saved state keeps the face bits. Indoors; the build warns when no event shows a hidden chest.
- **Outdoor arrivals on a structure** (merge point 25, A6): a named arrival (and an edge arrival point) whose sketch
  point lies on a structure's walkable top stands on that top (D6's `entrance:dd16_hatch` on the cooled crust, 26 over
  the lava): from the land up, while the first face above within 192 looks up and can be stood on, the point goes up
  onto it; a face looking down (a roof's underside) ends it. A structure that starts hidden counts; one never solid
  does not. Lifted more than 64, the build warns (a point in the middle of a cave mouth's mound, not in front of it).
- **Indoor smoke** (merge point 25, D-51): a decoration of the engine's `smoke` row (decoration_data Flags EmitSmoke,
  no sprite) puffs smoke indoors too, as outdoors (`{id: deco:wisp, room: ..., decoration: smoke, at: [...]}`); hidden
  (`hidden: true`, `{hide: deco:x}`) it stops.
- **Merge point 22 (2026-11-21)**: a door in an opening `in: floor` is a **trapdoor**: one hinged leaf filling a
  rectangular hole, its top flush with the upper floor (`surface`, the picture once over the leaf; `back_surface`
  under it, `edge_surface` round it), `hinge: north|south|east|west` (the side of the hole it turns on), `swing` 1 to
  120 down into the room below (about the underside's edge) or -1 to -120 up into the room above (about the top's
  edge), `thickness` (16, at most the floor's), `speed`, `auto_close_seconds`; the scene's rotating mover with a level
  axis, the same way for whoever opens it (no `side`). A wall panel with `cover: true` (and an `id`) stands 2 in front
  of a wall built whole behind it, so a destructible `of` it burns or breaks away to the wall (DD-13's hides); since
  merge point 24 it may stand in front of another panel (a hall wall that is one whole-wall panel for a burn's
  `set_texture`), which is then built whole behind it, as are the wall's bands (two covers may not overlap). Indoor
  `monsters[].npc: <npc id>` writes the scene actor's `npc_id`: clicked while peaceful it talks as that NPC (outdoor
  actors already took `npc`). `ActorIndex("monster:x")` in any wiring Lua becomes the placed monster's actor index.
  `oymap audit` counts a cinematic's `event` cues as run (no `event.unbound`). A neighbour's named arrival keeps its
  facing on every exit that names it (it reached only the first).
- **Trapdoors** (objects.yml `lifts[].trap: true`): a lift that drops the party into the room below is no ride, so
  `oymap audit` asks for no switch at its stops (`ride.no_switch`); install lists it in `<stem>.studio.yml`
  (`trap_doors`). A destructible's `on_destroyed` and `on_damaged` events count as run by the game (no
  `event.unbound`). A new dungeon's arrival text may wait on quest and player bits (`{not: {qbit: arrived_once}}`,
  XD-13's stages), not on a map variable or a death.
- **Water volumes** (`objects.yml water`: `of` a room or level, or an `outline`, with `top`, `bottom`, `liquid`,
  `tint`, `current`, `fog`): the party swims there; the surface the player sees is a platform with `solid: false`.
  `tint` multiplies the view by mix(1, tint, 0.6) while the eye is under; `fog` (`color_rgb` 0-255, `near_distance`,
  `far_distance`, optional `sky`) replaces the map's fog there; with `sky` above 0 the outdoor view's haze and sky colour
  give way to it too (`sky: 1` for a sea seen from inside).
- **Turning movers** (merge point 30, A8's levers): a mover with `turn: {pivot: [x, y, height], axis: x|y|z, degrees}`
  in place of `travel` turns about that line from its start to its end (the scene's rotating mover, `mover.rotation`,
  eased; `speed` in degrees per second, default 90), its parts with it: a lever's arm and grip as one mover (FD-01's
  two linear movers per lever). The pivot's height is measured as `bottom` is; every corner stays in the room and
  under its ceiling all the way round; nothing rides it.
- **Two warnings** (merge point 30, A7): a ladder that climbs through a hole in a floor and stands less than 10 inside
  the hole's edge (its rails pass through the rim; edges on the ladder room's walls do not count); a wall panel over
  part of a doorway in its wall, or a `fit` panel over a whole one (the doorway cuts its picture).
- **Ways out** (`exits`, a door's `into`, the `exit` preset): the game asks "leave?" only when the party leaves a
  dungeon (BLV) for an outdoor map; from an outdoor map the move is immediate (D-72).
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
  `group`, `hp`, `name`, `immobile`, `leash`, `hidden`, `carries`; `scene.items`: `position`, `item`, `gold`): the records a new
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

## Xeen feedback words (merge point 40, 2026-11-22)

From the user's play feedback of 2026-11-21 (`devdocs/xeen/reviews/USER_FEEDBACK_20261121.md`). Unit cases in
`tests/OutdoorTests.cpp` and `tests/CoreTests.cpp` ("F16: ...").

- **The entrance window into a dungeon (F16)** (`readMoveScreen`, core/Project): every way into a .blv (an outdoor
  door's or structure's `into`, a `teleport` with `map`, an indoor `exit` toward a neighbour) shows the MM6-MM8
  entrance window by default: the map's name, the stairs picture, "Do you wish to enter X?", OK and Close
  (evt.MoveToMap's seventh and eighth numbers `0, 1`). `screen: none` moves directly (`{direct = true}`: a fall, a
  throw, an answered question); `screen: {text: <row>, picture: <n>}` shows the line of that row of trans.txt in
  place of the question (a world adds its own rows: `data_tables/english/trans.txt`, below); `house` is the older
  name of `text`. Into an outdoor map nothing is shown (leaving a dungeon, the game asks itself). The `leave` effect
  stays a direct move (D-24). Before, every studio move into a dungeon was direct and maps asked their own Yes/No.
- **A world's entrance lines** (decision D-90): the game reads a world's `data_tables/english/trans.txt` (columns `id`,
  `Transition Description`, `Note`; a header row first) through world.yml `tableContributions` (`{table: trans,
  idDomain: <its range>, mode: append, path: data_tables/english/trans.txt}`); the ids must lie in the world's
  declared range and clear of the engine's 1-1593 (Xeen: `transitions` 5001-5999). `tools/l10n.py` collects the
  lines.
- **`oymap audit`, entrance windows** (Xeen's maps; others with `--dressing`): `entrance.no_window` (warning) for a
  move into another .blv with text and picture 0 and no `{direct = true}`; `entrance.question` (error) for a handler
  that asks Yes or No (evt.AskQuestion, AskChoiceWithAnswerSteps) and moves into a .blv: the window asks.
- **`carries`** on an outdoor sketch actor: the number of an item it carries (its corpse holds it), as objects.yml's
  monsters indoors.
- **A platform's fitted top** (rooms.yml blocks, objects.yml platforms: `top_surface: {texture, size, fit: true}`):
  the picture is stretched once over the whole top (a lectern's book, a desk's papers); before, `fit` was ignored on
  tops and a small top showed a piece of the picture.
- **An exit's default surface** (objects.yml `exits[]` without `surface`): the black face MM7 and MM8 draw at their
  dungeon exits, `7solid01` (MM7 style) or `solid01` (MM8 style, Xeen's maps by their `terrainTileset`); MM6's keep the
  room's door picture.
- **`identity`** (project.yml, decision D-89): `{shape: cave | mine | tower | temple | castle | sewer | ship | hall,
  family: <the shipped BLV it is laid as>, seen: [three things the party must see]}`. `oymap install` copies `shape`
  into the map's `<stem>.studio.yml`; the audit of a cave or a mine checks its cave shape (below).
- **Cave shape** (`oymap metrics`: `cave_shape`, per map and per room of at least 256 x 256 of floor; core/Metrics
  `caveShapeOf`): `floor_uneven_share` (floor area not level with its room's main floor: sloped, or a level piece more
  than 16 above or below), `ceiling_spread` (the mean distance of the ceiling from its room's main ceiling height),
  `ceiling_uneven_share`, and `wall_rough_share` (wall area leaning more than 5 degrees or running more than 5 degrees
  off the 45-degree grid). Measured (2026-11-22, floor / ceiling / walls): MM8 d17 0.61 / 291 / 0.98, d12 0.35 / 194 /
  0.39, d13 0.54 / 84 / 0.19; MM7 7d07 0.35 / 84 / 0.66, 7d08 0.42 / 223 / 0.71; MM6 6d05 0.31 / 74 / 0.06, 6d09
  0.12 / 13 / 0.07 (MM6's mines are cut on the grid). Built halls: MM8 d01 0.15 / 65 / 0.08, d27 0.30 / 72 / 0.16, d35
  0.07 / 15 / 0.03; MM7 7d29 0.17 / 71 / 0.11, 7d13 0.56 / 43 / 0.17 (stairs); MM6 6d16 0.10 / 35 / 0.06, sewer
  0.04 / 61 / 0.09. **Targets** (`caveShapeTargets`, just under the lowest of the MM7 and MM8 caves): floor 0.30,
  ceiling 80, walls 0.18. Xeen's caves on 2026-11-22: XD-18 0.09 / 24 / 0.12, XD-05 0.27 / 357 / 0.13, XD-10
  0.29 / 488 / 0.13, XD-16 0.23 / 17 / 0.41, DD-10A 0.05 / 119 / 0.35, DD-11A 0.20 / 111 / 0.27, XD-02 0.20 / 83 /
  0.30, XD-03 0.24 / 298 / 0.18.
- **`oymap audit`, cave shape**: `identity.cave_shape` (warning) for each of the three numbers below its target on a
  map whose `identity.shape` is `cave` or `mine`.

## Xeen feedback words (merge point 41, 2026-11-22)

From the user's play feedback of 2026-11-21 (`devdocs/xeen/reviews/USER_FEEDBACK_20261121.md`, F6/F3 and F2/F8).
Unit cases in `tests/OutdoorTests.cpp` ("chests outdoors", "the ground things stand on") and `tests/CoreTests.cpp`.

- **Outdoor chests are the shipped chest (F6-R1)**: a sketch structure `kind: chest` is built of a chest kind's faces
  (core/ChestKinds, shared with the indoor chests), MM7's 7out01 `chest_N` for `7gt002`: 96 x 64, a body 64 high, a
  lid sloping at 45 degrees to a top 32 deep at 80, 19 faces (end 16, middle 64, end 16 on the long sides and the
  lid; one picture on each short end, a strip above it). `chest_kind` (`ch1` to `ch5`, `7gt002`, `gt002`, `ch001` to
  `ch006`) picks the kind; left out, the style world's: mm8 `gt002`, mm7 and Xeen `7gt002`, mm6 `ch1`. Its front (the
  lid's own picture, `7gt002e`) looks **north** before `turn` (degrees clockwise: `turn: 180` faces south). A chest
  with its own `textures` (`wall`, `top`) stays the plain 9-face box of before, with a warning; crates are unchanged.
  Before, every outdoor chest was the 9-face box with one plank picture tiled over its sides.
- **Things stand on the game's ground (F6-R2)**: the game's outdoor ground is two flat triangles per cell, split from
  the north-west to the south-east corner (`outdoorNativeTerrainHeight`); the studio stood things on a bilinear
  height, up to about 32 off on uneven cells. Decorations (`kind: decoration` and scattered), actors and spawn points
  now stand on `LoweredOutdoorMap::groundHeightAt`; a chest or a crate stands at the lowest of it under its four
  footprint corners (the higher side sinks into the slope). Structures keep the stored height.
- **Decorations solid by their 3D model (2026-11-24)**: the game keeps a decoration's native collision, an upright
  cylinder of decoration_data.txt's radius and height (none at radius 0), which a long or hollow model does not fill
  (Xeen's world hull was walked through and over the world's edge). A binding in `engine/models/decorations.yml` or
  the world's `models/decorations.yml` with `collision: model` makes the outdoor build raise, under each
  `kind: decoration` structure that uses it, a model `collision:<id>` of its 3D model's own triangles (its base mesh),
  every face hidden (Invisible: not drawn, still solid), placed as the game places the model
  (`core/OutdoorDecorationCollision.h`). An indoor binding in `models/indoor_decorations.yml` accepts the same
  option. Studio writes the triangles into the owner room's BLV faces and identifies them in the scene so both
  sight and projectiles hit the solid parts. Movement, including walking through holes or under arches, follows
  the native faces on both map types.
  A binding may specify `collision_model: worlds/<world>/models/<proxy>.gltf` for a simpler physical mesh.
  `collision_model: lod` takes the visible model's coarsest LOD instead (the last mesh of its `openyamm_lods`, the
  base mesh when it has none). Mind a tree's coarsest LOD: a 4-triangle impostor card, no solid; and a proxy lower
  than the party's step (128) is climbed over, not a stop (scratch X4 2026-11-24: 7rock08/09 proxies).
  Author it in the visible model's coordinates. Studio uses the visible model's height, orientation and offsets
  to place it. Set the decoration's table radius to zero for a hollow prop whose opening a cylinder would fill.
  Outdoor scatter keeps its existing cylinder unless the binding also sets `collision_scatter: true`, intended
  for permanent structural or rock pieces. Ordinary scattered vegetation, wall mounts and initially hidden
  decorations receive no baked triangles. Bind a changing or destructible prop through its dynamic mechanism.
- **Scatter keeps to level spots (F6-R3)**: a scattered decoration on walkable ground (not `steep: true`) refuses a
  spot where the game's ground within its radius (decoration_data.txt's Radius) varies by more than 48.
  Set `support_radius` on the scatter entry to specify its ground footprint in map units. It checks the same
  candidate positions, so an established stand can keep its layout when its physical cylinder is replaced.
- An indoor map can use a model for a chest by naming a decoration in `objects.yml`, for example
  `{id: chest:cargo, room: room:hold, at: [640, 320], decoration: hh_breach_cache, treasure_level: 5}` in Hesper.
  The usual `preset: chest` on `source: chest:cargo` keeps its container, trap and loot. The body uses the world's
  decoration binding and any lid parts play their `open` and `close` clips. Outdoors use a `kind: decoration`
  structure with the same `decoration` and a `chest: {level: 5, random_items: 3}` block.
  A different world that mounts the Hesper assets can bind its own decoration row to the same
  `worlds/hesper/models/hh_breach_cache.glb` body and `hh_breach_cache_lid.glb` part.
- **Indoor chests: `facing` is the long axis (F6-R5)**: an indoor chest's `facing` is the direction its width runs;
  its **front** (the lock, the sloping lid's own picture) is the side 90 degrees anticlockwise of it, so `facing: east`
  shows the front to the north.
- **Chests turn and stand by D-99 (2026-11-22)**: a chest that gives no `facing` is turned by the build: against a wall
  (a side within 64 of one) its back to that wall and its front to the room, the wall leaving the most room in front
  first (so a chest in a niche faces out of it), then the nearest; standing free, its front toward the doorway its room
  is entered by from the party's start (the start itself in the start's room), squared to the room's walls
  (`chestRuleDegrees`). Give `facing` only for a turn the rule would not give. The build warns `chest.facing` when a
  chest of a kind with a given `facing` has its front within 64 of a wall, stands end-on to the wall by it with its back
  to the room, or stands free with its back (more than 100 degrees) to its room's entrance, and `chest.placement` when
  any chest's footprint is under 128 from a doorway of its room (in front of it or beside it), by a hole in its floor
  or ceiling, or under 64 from the line between two doorways' middles.
  `oymap audit` (Xeen's maps, others with `--dressing`) fails the built map's chests by the same numbers
  (`chest.facing`, `chest.placement`; core/ChestKinds.h holds both), indoors and on outdoor models. A sloping lid's
  chest is turned by whole quarters only (its slopes stay flat on whole units). The rule sees the room's outline and
  openings; the audit sees every face higher than the chest and every portal, so a pillar or a tall block beside a
  chest can still fail it: give that chest the `facing` the audit passes.
- **A wing door is a double door (F2)**: an outdoor building door that says no `leaves` and whose picture is one wing
  of a double door (texture_classes.yml `door: wing`: MM7's `7hhr1d2`, MM8's `t06a03`, `t09a03a`, `chb1dl` ...) is
  built as two leaves (`leaves: 2`), the first showing the left wing (of the picture and its `twin` the first by
  name: `7hhr1d1`, `t06a03`), the second it mirrored; what `tools/xeen/house_doors.py`'s `double_doors_sketch` wrote
  into each sketch. `leaves: 1` keeps a wing alone; on a listed door bay under 192 wide it stays alone, with a
  warning. The classes are read from the build's asset root (`readOutdoorDoorPictures`; without one nothing changes).
- **`leaves: 2` on a wall whose bays are not listed (F2)**: the wall is laid out round one door bay 256 wide (two
  leaves of 128) centred where the door's bay was, the stretches beside it in bays of about 128 (a window next to the
  door and every second bay out, posts at the ends), one window over the pair's middle in the rows above. Before,
  the pair shared one bay of about 128 (64-wide leaves). A listed wall keeps its bays, byte for byte.
- **A leaf shows its picture whole (D-91 §3)**: each leaf of a pair (a building door, a door cut into the roof, a
  `doorway`'s halves, a single `doorway` too) lays its picture once across at the picture's own width from the
  texture classes, the second leaf mirrored: X6's 256-wide `egydrlgl` and D6's `swdoora` whole on each leaf instead
  of half of it. A 128 wing is laid as before; a picture the classes do not know keeps 128. To fit a picture without
  squeezing it, make each leaf as wide as the picture (a `[door, 512]` bay for a 256 picture).
  A standalone `doorway` can fit a painting of any supported size to each leaf with
  `textures: {door: {texture: grate, fit: true, size: [128, 128]}}`. Use the artwork's native texel dimensions.
- **Cave mouths buried in their hill (F8)**: a `cave_mouth` that is not `free` no longer pulls the land under its
  side edges to the floor: a hill there stays, and the nodes on and one cell beyond its sides and back rise to the
  shell near them, as far as the land in its mouth and tunnel stays within 32 of the floor; only the front stays at
  the floor. The build warns `caves.wings` where the shell beside the rim stands more than 64 over the land beside
  it (make the footprint as wide as the mouth and its rim, as `house_doors.bury_mouths_sketch` does) and
  `caves.dome` where it stands more than 64 over the land behind it. Hatches are unchanged.
- **`form: shelter | blocked` on a cave mouth with no `into` (D-91 §2)**: `shelter` is a shallow open overhang
  (`mouth.depth` 160 when left out, the back narrowing only to 0.95) whose back and tunnel are the shell's rock (or
  `textures.door`), its floor the lit land; put its light (a fire, a brazier: `kind: decoration`) and contents under
  it. `blocked` fills the mouth at its face with a heap of rubble in the shell's rock (or `textures.door`) whose crown
  stands out before it; give it a click line (`effects: [{text: The adit has fallen in.}]`). Neither goes with `into`
  or `mouth.form: door`. A cave mouth with no `into` and no form is a dark way in that leads nowhere: the build warns
  `caves.blind_mouth`, `oymap install` lists it in `<stem>.studio.yml` (`blind_mouths`), and `oymap audit` of the
  project or the installed map says `caves.blind_mouth` (error).
- **`oymap audit`, door rules of `tools/xeen/door_check.py` (F2)**, on outdoor door faces beside `doors.tiled`,
  `doors.half_wing` and `doors.wing_unmirrored`: `doors.lone_wing` (a wing alone on a leaf 96 or more wide),
  `doors.part_picture` (a door picture, single or wing, shown less than 0.75 times across its leaf; a single picture
  split half and half over a pair is one, no exemption), `doors.narrow_pair` (two leaves under 192 together),
  `doors.off_steps` (a door more than 32 along its wall from the middle of a model named `..._steps` or `..._stairs`
  reaching within 128 of its wall before it). Errors on Xeen's maps; warnings on the others (`--doors`), where the
  203 shipped maps have 5 lone wings (MM8 elemf `gnecdr4l` x4, MM7 7out02 `hhm1d2`), 2 parts of a picture and 3
  narrow pairs (MM7 7out13's portal, MM6 outd2). Indoor leaves are not judged by them (their texels are measured off
  the stored pose, which reads a slice on many shipped doors).

## Merge point 42 (2026-11-22)

Unit cases: `tests/OutdoorTests.cpp` "D-90: items lie on the ground outdoors", `tests/CoreTests.cpp` "a chest without
a kind or surface is its style world's chest", "a platform's fitted top is laid once over its underside too".

- **Items on the ground outdoors (sketch.yml `items`, D-90's bare finds)**: `{id: item:<name>, item: <number or
  name>, at: [x, y], height: <over the ground>, gold: <amount, heaps only>}`, written into the scene's starting
  `sprite_objects` as the shipped outdoor maps hold theirs (MM7 out11 has 63) and as objects.yml `items` indoors;
  `item` names a row of the engine's or the world's items.txt (a name only where one row has it), drawn by the
  object_list.txt row of its sprite index (refused when none draws it). The item stands on the game's ground at `at`
  (`groundHeightAt`), `height` higher. The game lets a resting item down onto the terrain or a model's top under it
  (`settleRestingWorldItems`), and **a decoration is no floor**: a key "on a barrel's lid" (a `kind: decoration`
  barrel) ends inside the barrel, on the ground. The build warns when `height` is above 0 and no structure's top lies
  within 24 of it there; put such an item on the ground beside the barrel, or on a structure (a `crate`, a
  `platform`, a `deck`). Checked in X1 (a scratch build, `output/xeen_a1/mp42/x1items/`): both keys load and are
  picked up (`pick_up`).
- **Indoor default chest by style world**: an objects.yml chest without `kind` or `surface` is its style world's
  chest, as outdoors (`defaultChestKind(studioStyleWorld(...))`): mm8 `gt002`, mm7 and Xeen (MM7's tiles) `7gt002`,
  mm6, MM9 and other worlds `ch1`. Before, Xeen's maps got MM6's `ch1`. MM6-MM9 projects unchanged.
- **A platform's underside follows a fitted top**: a platform whose `top_surface` has `fit: true` (and no
  `bottom_surface`) lays the picture once over its underside too, as over the top; before, the underside took the
  room's texel size and the audit counted it `textures.feature_repeated` (P1-P4's vents, 1.5 times). `size` is the
  picture's own size in texels (left out: 128), not the face's.

## Xeen pins round P4 (2026-11-24)

Unit cases in `tests/OutdoorTests.cpp`: "P4: a rough cave mouth's shell has no two faces on each other, whatever its
seed" (960 builds), the plot-floor case ("a plot's floor as the sketch says it") and the road-bed case ("a road lies
level across its width").

- **Cave mouth shells** (`core/OutdoorWaysIn.cpp` `caveFaces`): a mound point that `roughness` shakes onto or within 8
  of the footprint's side, front or back lies on it at its unshaken place in that plane (shaken along the plane it
  could pass its neighbour and fold the shell onto itself: X5's `xd10_north`, whose rim fills its 576 width); a
  column from a point to itself (the front's foot at the footprint's corner) is not shaken; cuts of the front and the
  footprint's edge closer than 8 are one (the front's corner kept). The randoms are drawn as before, so other points
  keep their places.
- **A building's floor on a platform** (`levelPlots`): a said `floor` on a plot that overlaps a drawn `kind: platform`
  stands exactly there, and the land under it takes the step of 32 at or under it (hidden by the platform). Off a
  platform the floor keeps the nearest step with the land flush, as before. X2's stalls at 1040 on a court topped at
  1040 had the land rounded up to 1056 through the paving.
- **Road beds by things** (`gradeRoads`): the build warns `roads: the bed of <road> lowers the land N within a cell of
  <thing>` where a bed lowers a node by more than 64 within a cell of a building's plot or of a portal, fountain,
  well, obelisk, stone ring, trilithon or arch (X3's Newcastle stair under the mirror's dais). A warning: end the road
  at the thing's edge or give it `bed`.

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
It is deployed at https://oyeditor.jasicek.net/ (2026-11-22, version 3.0.0): nginx settings in
`packaging/server/nginx-oyeditor.conf`, upload with `web/scripts/deploy_hosted.sh`, steps in
`packaging/server/README.md`.

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
