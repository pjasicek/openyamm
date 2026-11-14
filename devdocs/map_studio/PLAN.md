# Map Studio implementation plan

Status: 2026-11-12. Milestones S0 and S1 are built ([S0.md](S0.md), [S1.md](S1.md): what exists, what it taught,
what was left); S2 onwards is plan. The design, research and mockups are in the private
artifact linked from [README.md](README.md); this file turns them into work. Revised the same day after the
pre-implementation review; what changed and why is in section 14.

The plan rests on three findings from reading the code:

1. Most of what the studio needs already exists in C++ without rendering: ODM and BLV readers and writers
   (`game/outdoor/OutdoorMapData.cpp`, `game/indoor/IndoorMapData.cpp`), scene parsers and overlays
   (`game/maps/*SceneYml.cpp`, `SceneOverlayOperations.cpp`), movement and collision
   (`game/indoor/IndoorMovementController`, `game/outdoor/OutdoorMovementController`), pathfinding
   (`game/pathfinding/`), and Lua handler enumeration (`ScriptedEventProgram::loadFromLuaText`).
2. The old editor contains two production build steps that 60+ map projects depend on: the indoor compiler
   (`editor/import/IndoorSourceGeometryCompiler`, run by `mm9_compile_indoor_source`) and the outdoor
   `--headless-build-map`. They move into the core first; the rest of `editor/` is deleted.
3. About a third of the ~150 000 lines of Python in `level_generation/projects` is generic: terrain shaping, road
   tiles, scatter, spawn placement, walkability and floor queries (35 private `floor_below`-style samplers), scene and
   Lua scaffolding, staging. Porting this to C++ is the largest single piece of work in the plan (roughly 50 000
   lines of Python to read and re-express); section 2a sizes and orders it. Project scripts keep only
   project-specific work.

## 1. Layering and repository layout

The studio is built first, completely, in its own folder. `editor/` is not touched until S7. `engine/` and `game/`
(other sessions work there) receive only the four small cuts of section 10a, early, each as its own reviewed change;
everything else there stays as it is until the shared core moves out and the old editor goes (milestone S7).

```
openyamm-studio/      everything of Map Studio
  core/               map data and logic, no platform dependencies (native + WebAssembly); new code here.
                      Documents, revisions, transactions and history live here, not in a front end
  cli/                oymap command line (C++), including `oymap serve` (the core as a long-lived process)
  wasm/               Emscripten bindings, builds openyamm-core.wasm + TypeScript types; used by the hosted page only
  host/               oymap host: thin Node/TypeScript process over `oymap serve`: WebSocket, MCP server, jobs,
                      game bridge
  web/                browser editor: React, Dockview, three.js, Monaco
  schema/             JSON Schemas of the project format, the brief and the operations
  kits/               door library, room themes, building kit manifests, calibration.yml (data, not code)
  calibration/        briefs, builds, reports and GAPS.md (see CALIBRATION.md)
  tests/              studio tests
engine/, game/        the four cuts of section 10a early, otherwise unchanged until S7; the studio compiles the
                      sources it needs from them in place
editor/               unchanged until S7, then deleted (see EDITOR_RETIREMENT.md)
```

Until S7 the studio's CMake project (enabled with `OPENYAMM_BUILD_STUDIO`, off by default) compiles the existing
`engine/` and `game/` sources it needs (the format readers and writers, scene parsers, tables, movement and
pathfinding, `ScriptedEventProgram`) and the indoor compiler sources from `editor/import/` directly, the way
`tests/` and `tools/` already do. Nothing is copied, so no code exists twice; new code lives only in
`openyamm-studio/`. A change the studio needs inside `game/` or `engine/` (for example a missing scene key in a
parser) is made there as a normal, separately reviewed change, with the usual MM6–MM9 checks.

What compiles in place today, checked by include closure on 2026-11-12:

- **Clean (no SDL, bgfx or gameplay headers):** `OutdoorMapData`, `IndoorMapData`, `OutdoorSceneYml`,
  `IndoorSceneYml`, `SceneOverlayOperations`, `game/pathfinding/*`, `ScriptedEventProgram`, `LuaStateOwner`, the
  table classes (`MapStats`, `MonsterTable` and the rest), `OutdoorMovementController` (bx only), the indoor compiler
  (`IndoorSourceGeometryCompiler`, `ObjModelImport`, `IndoorGeometryMetadata`). S0 needs only these. An include
  closure is not a link closure: the scene parsers also link `MapItemSourceYml`, `MechanismAudioYml`, `MistYml`,
  `IndoorWater`, `IndoorDaylight`, `SkyState` and `Mm9MonsterAi` (all clean), and `EditorDocument.cpp`, clean by its
  includes, links the texture size lookup in `engine/ImageAssetLoader.cpp` (SDL, bimg): cut G5 below. The list
  that builds today is in `openyamm-studio/CMakeLists.txt`.
- **Tangled, so not usable in place:** `IndoorMovementController` and `IndoorDerivedGeometry` reach
  `EventRuntime.h` and `Party.h` through `IndoorGeometryUtils.h`, and the controller calls
  `EventRuntime::calculateMechanismDistance`; overlay discovery and collision-set building sit in
  `MapAssetLoader.cpp` (SDL, bgfx, `std::async`, `YAML::LoadFile`); table loading with ruleset patches and the Lua
  path helpers sit in `GameDataLoader.cpp` (147 headers, bgfx among them). The studio needs all of these by S1 and
  may not copy them, which is why section 10a cuts them out early instead of at S7.

Two build targets of the core, and no third: **native** (the command line, `oymap serve` behind the host, CI) and
**WebAssembly** (the hosted page only). The host never loads the wasm core.

At S7 the reused sources move into `openyamm-studio/core/` (or a top-level `core/`, decided then) as the library
`openyamm_core`, the game links it, and the compile-in-place lists disappear (AGENTS.md: no forwarding layers that
hide duplicated ownership). The module table below describes that end state; until S7 "move" reads as "compile in
place".

CMake at S7: `openyamm_core` (static). Dependencies: yaml-cpp, PhysicsFS, Lua
(`openyamm_lua`), cgltf (currently taken from bgfx's `3rdparty` folder; vendor it under `third_party/` or fetch it so
the core does not depend on bgfx), zstd, and a PNG encoder for preview renders (stb_image_write, header only).
`openyamm_engine` stops exporting SDL3 and bgfx to targets that only need assets. The repeated game source lists in
`editor/`, `tools/` and `tests/` CMake files collapse into links against `openyamm_core` and `openyamm_game`.

## 2. The core, module by module

Each module lists where its code comes from. "Move" means the file leaves `game/` or `engine/` for `core/`, with
includes updated; "split" means a large file is cut and only the pure part moves; "new" is new code.

| Module | Contents | Source |
|---|---|---|
| `core/io` | `AssetFileSystem`, `AssetPackIndex`, `AssetPaths`, `AssetScaleTier`, `TextTable`, byte-source interface | Move from `engine/`. Add `mountMemory` and `mountIo` (PhysicsFS `PHYSFS_mountMemory`/`PHYSFS_mountIo`) for zips held in JavaScript. Android branch stays behind its `#ifdef`. |
| `core/format` | `BinaryReader`, `OutdoorMapData` + writer, `IndoorMapData` + writer, `MapDeltaData`, `.nav`, `.render` and `.lighting` data | Move from `game/outdoor`, `game/indoor`, `game/maps`. Already free of SDL and bgfx. |
| `core/scene` | Scene parsers, overlays, `SceneOverlayOperations`, `MapItemSourceYml`, `MechanismAudioYml`, `MapPresentation`; **scene writers**; `MapPackage` (path rules, overlay discovery, companion files, `build*MapStateFromScene`) | Move the parsers. Writers are new code over `core/CanonicalYaml` (S0 has the one for a new indoor map), with `EditorDocument::serialize*` (`editor/document/EditorDocument.cpp:4586, 4836, 4963`) as the reference for keys, and are completed to parity with the parsers (the editor's indoor writer emits ~150 of 279 keys). `MapPackage` is split out of `game/maps/MapAssetLoader.cpp` (5 324 lines): only path rules and pure assembly move; textures, threads and collision-set building stay or go to `core/collision`. |
| `core/tables` | `MapStats`, `HouseTable`, `MonsterTable`, `DecorationTable`, `JournalQuestTable`, `ObjectTable`, `ChestTable`, `MergedBaseTables`, `MapRegistry`, `ContentTableComposer`, `RulesetDefinition`, `ContentManifest`, `WorldDecorations`; a table loader | Move the classes. Split the file list and ruleset patching out of `GameDataLoader::loadInternal` (`game/data/GameDataLoader.cpp`, 5 737 lines) into a `TableLoader` both game and core use. |
| `core/script` | `LuaStateOwner`, `ScriptedEventProgram`, Lua path and overlay helpers, a sandbox runner with stub `evt` bindings and a stub `ISceneEventContext` | Move `engine/scripting/LuaStateOwner` and `ScriptedEventProgram`. Split the path helpers out of `GameDataLoader.cpp:229–447` and delete the editor's copies. The full `EventRuntime` (12 210 lines, 224 `evt` functions) stays in `game/`; the core records calls instead of executing them. Remove `dofile`/`loadfile` from the sandbox's base library. |
| `core/terrain` | `TerrainMaterialConfig`, `TerrainTileData`, the terrain-material path rule; **new** heightfield operations, road rasterisation with corner-mask tile selection, material weight generation | Move the parsers; the path rule leaves `game/outdoor/OutdoorTerrainMaterials.cpp` (which includes bgfx). Port `tools/terrain_materials.py weights` and the generic parts of `height_at`/`grade`/`flatten` (four Hesper copies) and Castleview's `terrain_tiles.py`. |
| `core/collision` | Indoor and outdoor movement controllers, collision primitives, geometry utils, sector face grid, portal graph, `PathMap`, `PathPlanner`, pathfinding builders; **new** collision-set builders and a reachability flood | Move. Cut the `EventRuntime.h` include from `IndoorGeometryUtils.h` (it is there only to pass `EventRuntimeState*`) by introducing a small `MechanismStateView`. Collision-set building leaves `MapAssetLoader.cpp:2288, 4782`. `bx::Vec3` stays (bx builds for wasm) or is replaced by a core vector type. |
| `core/compile` | Indoor compiler (`IndoorGeometryMetadata`, `ObjModelImport`, `IndoorSourceGeometryCompiler`, `IndoorDerivedGeometry`); outdoor build (`buildImportedBModel`, `buildOutdoorGeometryFromSourcePackage`, `compileOutdoorGeometryBytes`, the `map.yml`/`geometry.yml`/`terrain.yml` metadata, `map_stats`/`map_navigation` row writers) | Move from `editor/import` and `editor/document`. The legacy sidecar formats stay supported: 115 indoor and 103 outdoor `geometry.yml` files in `level_generation/` use them. |
| `core/project` | **New.** The text project format (section 4), stable id allocation, import of shipped maps into projects, lowering of a project to the compile inputs | New. |
| `core/ops` | **New.** Documents, revisions, operations, transactions, semantic diff, history, the canonical file writer | New (section 5). The same code serves `oymap edit`, `oymap serve` and the hosted page; no front end keeps its own copy. |
| `core/check` | **New.** Validation and scorecards; the flow graph | New, porting the generic audits (section 6). |
| `core/preview` | **New.** Software renderer for plans and isometric views with labels, PNG output | New. Not part of the game renderer; it draws data, not materials. |
| `core/assets` | **New.** Asset catalogue: decorations and their models, building and door kits, wall textures, surface materials, terrain materials, creatures, with sizes, worlds, tags and thumbnail paths | Indexes existing files: `engine/models/*decorations*.yml`, `decoration_data.txt`, `level_generation/textures_x4/inventory.json`, `assets_source/**/surface_materials/textures.yml`, `engine/terrain_materials/library.yml`, `catalogues/outdoor_decorations/inventory.json`, cooked model bounds. |

Behaviour rule for every move: the game's load paths for MM6–MM9 must not change behaviour, load time, memory or
save-game layout identity. Each move lands with the unit tests, the release scenarios and a load-time comparison on
a few maps of every world (AGENTS.md MM9 rules).

## 2a. The Python port

**Dropped as a milestone deliverable on 2026-11-13** (the user asked the lead to decide). The rebuild loop gave the
core a better target than parity with the Python kits: every word is measured against the shipped maps and played,
which the kits never were. Nothing is ported for its own sake; a generic piece moves into the core only when a map
needs it, as the rule "order by need" below already says, and the MM9 converters and project scripts keep their
Python. **Set-piece import with face matching (S3) is dropped as well:** lifting faces from shipped maps into a
project would skip the vocabulary the rebuilds test, and in new dungeons it brings the mixed-source look the user
called a "Frankenstein's monster"; the shipped forms come in as measured words instead (lever and button kinds,
chest kinds, door pictures). The section below is kept as the record of what was planned.

The decision "the engine's C++ is the only implementation" means the generic Python that builds good maps today is
re-expressed in the core. This is the bulk of S3 and S4, not a side effect of them. The Python stays the
specification until its replacement passes parity.

| Area | Python today | Goes to | Milestone |
|---|---|---|---|
| Dungeon shell | `mm9r_common/dungeon/` (11 500 lines: `rooms.py`, `geometry.py`, `wall_splits.py`, `floors.py`, `movers.py`, `water.py`, `package.py`), `hesper_stage/blv_kit.py` (980) | `core/project` lowering, `core/compile` | S0 slice (boxes and openings only), S3 (the rest) |
| Dungeon dressing | `dungeon/lights.py`, `lighting.py`, `density.py`, `objects.py`, `treasure.py`, `pickups.py`, `people.py`, `ambient.py`, `destructibles.py` | `core/ops` (populate, dress), `core/check` | S3 |
| Checks | the audits listed in section 6; 35 private floor samplers | `core/check`, `core/collision` | S1 |
| Terrain and roads | Hesper `height_at`/`grade`/`flatten` (four copies), Castleview `terrain_tiles.py`, `tools/terrain_materials.py weights` | `core/terrain` | S4 |
| Outdoor placement | building kits, scatter with clearance, spawn placement | `core/ops` | S4 |
| Scaffolding | scene dict writers (four), door tables and Lua scaffolding, staging and installation (four), `make_tour.py` (37 copies), `make_scenarios.py` (39) | `core/scene` writers, `core/script`, `oymap build`/`playtest` | S1–S2 |

Rules for the port:

- **Parity before replacement.** For each ported piece, the same input is built by the Python route and by the core,
  and the two results are compared with the studio's own metrics and checks (section 6), not byte for byte: the
  target is "as good as the kit", measured. A piece that cannot reach parity keeps its Python caller.
- **Algorithms, not code**, and only the generic parts. MM9 conversion (`mm9r_*` converters reading MM9 data),
  project-specific scripts and one-off fixes are not ported; they call `oymap` when they are next touched.
- **Order by need.** The vertical slice (S0) decides the first pieces; after that a piece is ported when a
  calibration or Xeen map needs it. Nothing is ported for completeness.
- The Python projects that exist keep working unchanged throughout. No existing map is rebuilt through the core
  unless its owner chooses to.

## 3. Building for WebAssembly

WebAssembly serves the hosted page only (section 9). The command line, the host and CI use the native core. A CI job
builds the core with emsdk and runs a smoke test from S0 on, so the code stays portable while the hosted page itself
waits for S5; nothing else depends on wasm before then. emsdk is not installed on the development machine yet.

- Emscripten (current emsdk), `-fwasm-exceptions` (yaml-cpp throws; the scene loaders catch) and
  `-sSUPPORT_LONGJMP=wasm` (Lua raises errors with longjmp through the `evt` callbacks).
- Native and wasm builds of the same project must give byte-identical BLV, ODM and scene files (section 11): a map
  whose bytes depend on where it was built would change its layout identity and reset saved map state. No fast-math,
  no `long double`, no iteration over unordered containers on the way to output.
- No pthreads at first. `Engine::parallelFor` already runs serially with one thread; the `std::async` calls that move
  with `MapPackage` get a serial path. Threads (with COOP/COEP headers) can come later for heavy compiles.
- File access goes through `core/io` byte sources: zips mounted through a JavaScript `PHYSFS_Io` that reads byte
  ranges on demand (section 9, "Assets in the hosted page"; a 1.6 GB package is never loaded whole), project
  files through MEMFS mirrored to OPFS or to the File System Access directory. Remove `std::filesystem::current_path()`
  from the Lua sidecar lookup and avoid `YAML::LoadFile` in core code.
- PhysicsFS is a process-wide singleton: one `AssetFileSystem` per wasm instance, one instance per worker.
- Check wasm32 hazards: `size_t` is 32-bit (sentinels written into 64-bit fields), and any serialised
  `unordered_map` iteration order.
- Bindings: a C ABI with JSON in and out for operations and queries, plus transferable `ArrayBuffer`s for meshes and
  images. TypeScript types are generated from `openyamm-studio/schema`.

## 4. The project format

A map project is a folder of text files plus a few images, meant to live in git and to be written by people,
agents and the studio alike. JSON Schemas in `openyamm-studio/schema/` describe every file; the core validates against them.

```
<project>/
  project.yml       map card: id, world, kind (outdoor | indoor), profile (odm | dungeon | region | city),
                    template, base (for overlay projects), neighbours and travel, map-stats row, monster slots
  plan.yml          zones, bubbles, mission graph (rooms, locks, keys), points of interest, landmarks, notes
  rooms.yml         indoor shell: rooms (outline, band, floor, ceiling, theme), openings, stairs, ramps, lifts
  terrain/          height.png (16-bit), tiles.png, weights*.png, terrain.yml (banks, sea level, liquids)
  geometry/         imported meshes (GLB) with <name>.faces.yml: stable face ids and their settings
  objects.yml       buildings, decorations, doors, lights, spawns, actors, chests, items, anchors, placeholders,
                    ladders, water volumes, destructibles, ambient sounds
  wiring.yml        behaviour presets and connections
  scripts/          hand-written Lua handlers
  atmosphere.yml    sky, fog, weather, daylight, music, footsteps
  review/pins.yml   review pins
  ids.lock.yml      stable id → engine id (sectors, faces, events, doors, chests, BModels)
```

- **The files are the truth.** There is no hidden document state: a project is exactly its files, and anyone may
  change them with any tool (the studio, `oymap edit`, a text editor, an agent's file edit). The core reads them,
  validates them and reports what changed (section 5).
- **Canonical form.** The core writes every project file in one fixed form: fixed key order per schema, fixed
  indentation and number formatting, lists sorted by id where order has no meaning. Files carry **no YAML comments**
  (yaml-cpp cannot keep them); every object has a `notes:` field instead, and the schema rejects nothing for having
  one. A hand-edited file is rewritten into canonical form by the next studio write or by `oymap fmt`, so a diff shows
  the change and nothing else. `oymap fmt --check` is the test that a file is already canonical.
- **Readable ids.** Everything has a stable id such as `room:vault`, `door:d36`, `evt:lever_gate`.
  `ids.lock.yml` keeps the engine numbers the compiler assigned, so rebuilding a map keeps event and door numbers,
  overlays still apply, and saves see the same layout where nothing changed.
- **Overlay projects.** A project with a `base` (a shipped map) stores only its changes and compiles to
  `<stem>_<mod>.scene.yml` and `<stem>_<mod>.lua` overlays. A full copy (`studio detach`) becomes a new map.
- **Import of shipped maps.** `oymap import <map>` reads ODM or BLV, the scene, overlays and the map Lua into a
  project: sectors are grouped into rooms, faces get ids, events become presets where they match a preset exactly and
  stay as Lua otherwise. Import is how the viewer, audits and overlay editing work on all MM6–MM9 maps.
- **Face settings survive re-import.** `geometry/<name>.faces.yml` keys settings by the mesh's node and material
  names first (the indoor compiler's existing convention: `INTERACT_`, `MECH_`, `TRIGGER_` nodes), which survive any
  reshaping in Blender. Faces without a name are matched by position, normal and texture as a fallback; matched faces
  keep events, flags and door membership, unmatched faces are listed.
- **Legacy inputs.** The existing `geometry.yml` (indoor and outdoor), `map.yml` and `terrain.yml` sidecars remain
  valid compile inputs. A project can reference them, so existing pipelines move over when they choose to.

### World projects

A world with many linked maps (Xeen has about 70) needs a plan above the maps. A world project holds:

```
<world>/
  world.yml         faces and layers per map (Xeen: cloudside and darkside; surface, sky, plane, finale),
                    default sky, death map and Town Portal page per face, level and treasure bands per map
  travel.yml        typed links: map edges (days), boats and stables (schedules), paired pyramids (gate QBit),
                    mirror networks (discovery QBit), one-way links (tower roof to sky map), falls (sky to surface,
                    with position mapping), scripted transitions
  story.yml         the world's critical path: main-quest steps placed on maps and rooms, with the QBits and items
                    each needs and gives
  maps/<code>/      the map projects, referring to the world by map code
```

The flow graph then solves across maps: a key found in one dungeon opens a door in another, and the checks can say
that step M17 is unreachable before step M12.

### Conditions, states and rules

Three shared vocabularies, used by every file above (from Xeen's needs, `devdocs/xeen/PLAN_YAML_NEEDS.md`):

- **Conditions:** QBit, item, item count, party award, stat or skill check, time of day, day or month, password,
  dialogue choice, kill count. Doors, presets, encounters, points of interest and states use the same form, so the
  flow graph can reason about all of them.
- **Staged states:** named states keyed by a condition that show or hide BModel groups (including translucent "out of
  phase" ones), add or remove actor groups, open or close houses, seal or open wings, and override atmosphere or
  music. Used by Newcastle, Castle Kalindra, cursed towns. Compiled to the existing face-bit, group and overlay
  mechanisms.
- **Map rules:** no Fly, no spells, no teleport, weather override, a no-spawn buffer around towns, the world rim
  (sides, cliff band, fall to death or to a target map), fall-through floors on open-air maps.

Mechanisms and presets to add from the same source: illusory walls, water-level movers, conveyors, trapdoors,
teleport mazes, barrier generators, wave summons, kill counters, obelisk riddles, destructible camps, genie lamps,
outdoor teachers, market stalls. Pocket sets (several disconnected parts in one indoor project, entered by falling),
towers stacked around a stair or lift core, and indoor maps with exits to several outdoor maps are part of the
indoor profile.

## 5. Operations, transactions and history

Edits from the browser and from tools are operations applied by the core. Direct edits of the project files are
equally valid (section 4); operations are the convenient and checked way, not the only way.

- **Everything in this section lives in `core/ops`**, so `oymap edit` (no host), `oymap serve` (behind the host) and
  the hosted page (no host at all) behave the same. The host and the web app keep no document state of their own.
- An operation is JSON with an `op` name and arguments, for example `room.add`, `room.set_heights`,
  `opening.add`, `door.place` (library kind) or `door.from_faces`, `preset.add`, `connect`, `spawn_zone.fill`,
  `terrain.raise`, `road.add`, `building.place`, `asset.placeholder`. The catalogue is in `openyamm-studio/schema/ops/`.
- Operations prefer relations over coordinates: anchors (`room:vault.N`, corners, centre, named sockets), connections
  between anchors, zones with counts. The core snaps to the grid and the world's metrics. Raw coordinates are allowed
  as an override.
- A batch of operations is one transaction with `dry_run` and `fail_fast`. The result is a semantic diff, a check
  delta (tier 0, section 6) and the new revision.
- **Revision = content.** A project's revision is a hash over its canonical files, computed by the core; handles
  are `doc@<short hash>`. It needs no running process and no counter, so two `oymap` processes, the host and a text
  editor can never disagree about it. A write against an older revision is rejected with a semantic diff of what
  changed since (whoever changed it, by whatever means), so a person and several agents can edit the same map.
- **History = file snapshots.** Each transaction, and each outside edit the core notices on its next read, stores
  the changed files' previous contents in `<project>/.oymap/history/` (git-ignored) with the operations that caused
  it, when there were any. Undo, redo, checkpoints and revert restore snapshots; they do not replay or invert
  operations, so they stay correct after hand edits. The log of operations is kept for the record and for review,
  not as the source of state. Writes are temp-file-plus-rename under a project lock file.
- The studio never creates git commits; committing stays with the user.

## 6. Checks, scorecards and the flow graph

Three tiers, cheapest first.

- **Tier 0, inside every operation:** schema, snapping, units, references (unbound clickable faces, events without a
  handler, handlers without a binding, missing textures, door records without geometry), scale against
  `world.yml` party metrics and door, corridor and step standards.
- **Tier 1, per iteration (seconds):** incremental compile keyed by content hash per room or terrain chunk;
  reachability flood from the party start using the movement controllers and `PathMap`; lock-and-key solve over the
  flow graph; step height, head clearance and gaps; sector and floor ownership; actor floor contact and sizes;
  decoration ids; door sounds present; light caps; translucent-face limits; terrain slope; density against the
  calibration bands; Lua lint of generated handlers. Output: a scorecard with ids and fix hints.
- **Tier 2, milestones (minutes):** labelled camera sets from `core/preview`; real views through the game's screenshot
  tours; a headless playtest through `--headless-run-scenario` that walks the critical path and asserts QBits, doors
  and actors.

Ported from existing scripts (generic parts only): `hesper_stage/check_walkability.py`,
`mm9r_common/sector_audit.py`, `actor_floor_audit.py`, `camera_gate.py`, `hesper_stage/check_actor_sizes.py`,
`check_decoration_ids.py`, the generic half of `door_sound_check.py`, `hesper_out4/check_relief.py`,
`dungeon/lights.py` caps, `dungeon/density.py` (algorithm only), `tools/indoor_hole_sweep.py` and
`indoor_portal_sweep.py` as tour generators. Calibration targets come from `level_generation/evidence/**`,
`catalogues/**` and `tools/mm9_import_discovery/mm9_density_targets.yml`; prose-only targets in the calibration
Markdown files are converted into a machine-readable `openyamm-studio/kits/calibration.yml` as they are needed.

**Flow graph.** Nodes are rooms (groups of sectors), edges are portals, stairs, lifts, teleports and drops; doors make
edges conditional. Conditions come from presets exactly. For hand-written and generated Lua the core runs each
handler in the sandbox, forcing every `evt` comparison both ways (bounded per handler) and recording what it reads
and which doors it opens; such edges are marked **approximate**, and what the sandbox cannot resolve (keys given by
`Global.lua` topics or by other maps, timers, kill counts) is listed as unknown instead of guessed. A project may
state a condition by hand (`wiring.yml`), which overrides the derived one. Output:
the graph as data, the critical path from the party start to the goals in `plan.yml`, and issues (unreachable rooms,
keys behind their own lock, one-way traps without a way back).

## 7. The command line: `oymap`

Native C++ in `openyamm-studio/cli`, linked to the core. Every command prints JSON with `--json`.

```
oymap import <map> [--world mm6] [--to <project>]   shipped map → project
oymap open|overview|query <project> ...             summaries and paged queries
oymap edit <project> --ops ops.json [--dry-run]     apply a transaction
oymap fmt <project> [--check]                       rewrite the project files in canonical form
oymap history <project> [undo|redo|revert <rev>]    snapshots and the operation log
oymap serve                                         the core as a long-lived process: JSON-RPC on stdio (for the host)
oymap check <project> [--tier 1] [--only ...]       scorecard
oymap flow <project> [--png out.png]                mission graph and critical path
oymap render <project> --cameras <set> --out dir    labelled plan and isometric views
oymap build <project> [--install mods|dev]          compile ODM or BLV, scene, Lua, overlays
oymap build-map <map.yml|scene.yml>                 legacy outdoor build (replaces editor --headless-build-map)
oymap compile-indoor <glb> <geometry.yml> <out.blv> legacy indoor build (mm9_compile_indoor_source stays as alias)
oymap playtest <project> --scenario <yml>|--walk-critical-path
oymap assets search <query>                         the asset catalogue
oymap export <map> --json                           replaces util/map_export.py for scripts
```

`oymap export` gives the 256 Python files that import `util/map_export.py` a supported reader; they move over when
touched, not in one sweep.

## 8. The host and the MCP server

`openyamm-studio/host` is a thin Node/TypeScript process (current Node LTS) started with `oymap host` or
`oymap studio` (host plus browser). It exists because the MCP SDK and the WebSocket server are TypeScript; it holds no
map logic and no document state.

- **Core:** the host starts one native `oymap serve` child and forwards operations and queries to it as JSON-RPC over
  stdio. That gives the host the real file system, threads and exactly the binary the command line uses; there is no
  wasm core in Node and no "wasm or native" choice per job. If the child dies the host restarts it; nothing is lost,
  because the files are the state (sections 4 and 5).
- **Access:** listens on 127.0.0.1 only, checks `Origin` against an allow list (the local page and the hosted page's
  origin), and requires a **pairing token** printed at start and passed by the browser (in the URL the host opens,
  or pasted into the hosted page). Without it any web page open in the user's browser could drive the host.
- **Documents:** owned by `oymap serve` (revisions, transactions, history: section 5). Files are written with
  temp-file-plus-rename (`assets_dev` files are hard links; never edit in place).
- **Jobs:** compile, render, playtest and bake run as jobs with progress; the game bridge starts
  `build/game/openyamm --headless-run-scenario` or `./tools/run_game.sh --isolated <name>` with a tour.
- **Browser:** WebSocket JSON-RPC with the same operation and query schemas as MCP, and HTTP on the same port for
  texture and mesh bytes.
- **MCP:** TypeScript MCP SDK 2.x, Streamable HTTP plus a stdio relay (`oymap mcp`). It speaks protocol revisions
  2025-11-25 and 2026-07-28. The tools:

| Tool | Notes |
|---|---|
| `map_open`, `map_overview`, `map_edit`, `map_validate` | Always loaded (`anthropic/alwaysLoad`). Handles are `doc@revision` (the content hash of section 5). |
| `map_query`, `map_flow`, `map_render`, `map_assets`, `map_api` | Read only (`readOnlyHint`), concise by default, paged. |
| `map_build`, `map_playtest` | MCP Tasks where the client supports them; `job_start`/`job_status` otherwise (Codex stops calls after 60 s). |
| `map_pins`, `map_history`, `map_exec` | `map_history revert` asks first (elicitation, with a `dry_run` fallback). `map_exec` runs JavaScript against the typed core API in an isolated context and returns what it prints. |

Results carry `structuredContent` with an `outputSchema` plus a short text summary, at most about 2 000 tokens;
large data goes behind resource links. Images are one contact sheet at most 1 568 pixels on the long edge.
Server instructions put the loop (open, edit, check, render, build) in the first 512 characters. A `map-studio` skill
documents the loop, the scale standards and the camera sets. An MCP App viewer (`ui://openyamm/viewer`) comes in S6
for Claude Desktop, claude.ai, VS Code and Cursor.

**State after S2** ([S2.md](S2.md)): the host is plain JavaScript modules (no build step), started with
`node openyamm-studio/host/src/host.mjs mcp|serve`; the `oymap host`, `oymap studio` and `oymap mcp` shortcuts are
not made. It uses the TypeScript MCP SDK **1.32.2**, the newest on npm on 2026-11-12, which speaks protocol
2025-11-25: the "SDK 2.x" and revision 2026-07-28 this section and the research note name were not what npm
ships, so nothing here relies on them. All fourteen tools exist and are tested through the SDK's own client over
stdio. Not made yet, and why: Streamable HTTP (no client here needs it before the browser), jobs and MCP Tasks
(build and playtest answer within the call; the longest playtest so far takes about 20 s), `structuredContent` with
output schemas (results are JSON text), elicitation on undo, HTTP for texture and mesh bytes (S5), the `map-studio`
skill (after the evaluation has settled the tool texts). `map_exec` runs in a `node:vm` context whose only door is
the core; that is a convenience boundary against mistakes, not a security sandbox.

## 9. The web app

`openyamm-studio/web`: React, Dockview, three.js (WebGPU renderer with WebGL2 fallback), three-mesh-bvh, Monaco, Zustand.

- One client interface, two backends: the local host over WebSocket (**local mode**), or the wasm core in a worker
  for the hosted page (**hosted mode**). Both speak the same operation and query schemas.
- Screen as designed: stage bar, tool rail, tool options bar, plan view and 3D view, inspector with Properties,
  Connections and Notes, drawer with Library, Checklist, Issues and Outline, command palette.
- 3D views draw from data the core produces (meshes, materials, labels). Terrain blending, lightmaps and fog are the
  only shaders ported from the game; the exact look comes from Play here.
- Walk mode uses the core's movement controllers in the worker, so it collides like the game.

### What each mode can do

| | Local mode (host on the user's machine) | Hosted mode (static page, no host) |
|---|---|---|
| View, walk, flow graph, checks tier 0 and 1, labelled renders | yes | yes |
| Review pins | yes | yes (saved in the project folder or exported) |
| Edit through operations, undo and history | yes | yes in Chromium (File System Access); Firefox and Safari open a folder or zip read-only and export a zip |
| Build ODM or BLV, scene and Lua | yes | yes (same core; byte-identical by test) |
| Play here, playtests, lighting bakes, screenshot tours | yes (needs the game) | no: the page says so and offers the project to a local install |
| Agents and live pairing | yes | only by pairing with a local host (token; Chromium and Firefox. Safari blocks `ws://127.0.0.1` from an https page) |

Hosted mode is delivered in that order: view and review first, then editing, then build. It is the last part of S5,
and nothing before S5 depends on it.

### Assets in the hosted page

A player's install is about 3.3 GB (`engine.zip` alone 1.6 GB), textures are cooked `.oytex` (zstd-framed block-compressed
images with mips: BC7, BC1, BC4 and BC5 on desktop, ETC2 and EAC on Android), and a wasm32 heap ends at 4 GB. So:

- **Packages are read by byte range, never loaded whole.** The user picks the install folder (or single zips); the
  worker keeps `File` handles and serves `PHYSFS_Io` reads with synchronous range reads (`FileReaderSync`, or OPFS
  sync access handles for copies). Only each zip's central directory is held in memory.
- **Textures do not pass through the wasm heap as pixels.** The core returns the cooked file's bytes; the page
  un-frames them (zstd) and uploads the blocks directly where the GPU takes them (`texture-compression-bc`
  in WebGPU, the matching WebGL2 extensions), and decodes on the CPU to RGBA only where it cannot.
  Views start from a low mip and refine; an LRU cache bounds GPU memory.
- **One map at a time** in the worker; tables and the asset catalogue are loaded once. A memory budget (target:
  under 1 GB of wasm heap on the largest MM9 region) is an acceptance check of S5.
- **Repo checkouts** (`assets_dev/` as loose files, 12 GB) are opened through the same directory handle, read on
  demand.
- Local mode has none of these limits: the page asks the host, which reads through the native core and serves
  texture bytes over HTTP on 127.0.0.1.

## 10. Game-side changes

### 10a. Early cuts the studio depends on (S1)

The review found four places (and S0 a fifth) where code the studio must reuse is tangled with rendering or gameplay (section 1).
Copying it is not allowed, so each is cut out in `game/` as a small change that only moves code and narrows
includes: no behaviour, load-time, memory or save-identity change, the usual MM6–MM9 checks, its own review, and
agreed with whichever session is working in that file at the time. Until a cut lands, the studio does without the
feature that needs it rather than working around it.

| # | Cut | Needed for |
|---|---|---|
| G1 | `MechanismStateView`: `IndoorGeometryUtils.h` and `IndoorMovementController` stop including `EventRuntime.h` (they only read mechanism state); `calculateMechanismDistance` becomes a free function in its own small file | Indoor reachability and floor queries (S1), walk mode, lowering through `IndoorDerivedGeometry` in a small target |
| G2 | Map package rules: scene overlay discovery (`MapAssetLoader.cpp:3963-3990`), companion-file paths and the Lua path and overlay helpers (`GameDataLoader.cpp:229–447`) into files without SDL, bgfx or threads | Import of shipped maps with their overlays (S1) |
| G3 | `TableLoader`: the table file list and ruleset patching out of `GameDataLoader::loadInternal`, used by the game and the studio | Checks against the tables, the asset catalogue (S1) |
| G4 | Collision-set builders out of `MapAssetLoader.cpp` (`:2288`, `:4782`) into `game/indoor` and `game/outdoor` files without texture or thread code | Reachability on built and imported maps (S1) |

| G5 | Texture size lookup without SDL and bimg: `findSurfaceTextureLogicalSize` and what it needs out of `engine/ImageAssetLoader.cpp` into a file that reads sizes from headers (`readImageDimensions`, the cooked texture header) | `oymap build-map`, the old outdoor build through `EditorDocument` (found in S0, [S0.md](S0.md)); UVs of imported building meshes |

**State after S1:** G1, G2 and G5 are made (unstaged, for review; [S1.md](S1.md), "The cuts"). G3 and G4 were not
needed: the table classes and the path map builders link cleanly, which `openyamm-studio/tests/link_closure.py`
shows from the game's own build objects (an include closure had suggested otherwise).

These are the same cuts section 2 lists for S7; doing them at S1 keeps each one small and makes S7 a move of files
that are already clean. S0 needed none of them.

### 10b. Development features

Small and separate from the studio, each behind its own review:

1. A development mount for a build output folder (`--extra-mount <dir>`), so playtests and Play here load a project's
   build without copying into `assets_dev`.
2. Reload the current map when its files change, behind a development switch; keep the party where it stands.
3. Named mod folders with a manifest and an enabled list (`AssetFileSystem::mountMods` mounts one merged folder
   today).
4. Scenario steps the studio needs that are missing (to be listed when S2 writes its first playtests).

**State after S2:** item 1 is made (unstaged, for review): `--extra-mount <dir>` in the game and in headless
scenario runs, `InstalledContentOptions::extraMountRoot` and `AssetFileSystem::mountExtraDevelopmentRoot`, on
development roots only, for a folder's engine files and its worlds' `maps`, `events` and `textures`; `oymap install
--mount` writes such a folder and `oymap ... --mount` reads one. Item 2 (reload) is not made: it changes how the
running game holds a map and wants its own review; until then a playtest starts the game again, which takes
seconds headless. Item 3 is untouched. Item 4: the first playtests needed no new step (`play_lua` with `click`,
`door_state`, `loot_chest` and `log` was enough).

## 11. Tests

- **Unit (doctest):** core modules; extend `openyamm_unit_tests` or add `openyamm_core_tests`. Move
  `tests/IndoorSourceGeometryCompilerTests.cpp` (23 cases) with the compiler and run it in CI (today it only builds
  with `OPENYAMM_BUILD_TOOLS`, which CI turns off).
- **Round trips over every shipped map:** parse → write → parse equality for all scene files and overlays of MM6–MM9;
  import → build equality for the compile inputs; run locally against `assets_dev` and in CI against a small committed
  fixture set.
- **Compiler parity:** rebuilding the 46 `mm9r_*` projects, the Hesper dungeons and the outdoor projects through the
  core gives byte-identical BLV and ODM files to the old route before the old route is removed.
- **Wasm:** a CI job builds the core with emsdk (from S0: build and a smoke test) and runs the same round trips
  under Node. **Native against wasm:** a fixture set of projects is built by both and the BLV, ODM and scene bytes
  must be equal.
- **Canonical form:** `oymap fmt --check` passes on every file the studio writes; write → read → write is stable.
- **History:** undo and revert restore exact file bytes, including after an outside edit between two transactions;
  two processes writing against the same revision: one wins, the other gets the diff.
- **Port parity (section 2a):** each ported builder piece against its Python source on shared inputs, compared by
  metrics and checks.
- **Host and MCP:** Vitest; the MCP Inspector CLI snapshots `tools/list` and replays calls.
- **Web:** Playwright on the five acceptance maps.
- **Agent evaluation:** 20–40 real tasks (the five rebuilds, Castleview–Kalindra on the core, Brackenford revisions,
  a Hesper dungeon, MM9 dungeon checks, the MM6–MM8 audit, addressing ten pins), measured on tool calls, tokens, tool
  errors, checks passed, pins per map and time; transcripts read back to refine tool descriptions.

## 12. Milestones

Each milestone ends with its acceptance test. Sizes are relative (S, M, L, XL). Calibration ([CALIBRATION.md](CALIBRATION.md))
runs through all of them: the calibration maps drive the work, the held-out maps check it, Xeen Act I is the first
new map.

| # | Milestone | Size | Contents | Accepted when |
|---|---|---|---|---|
| S0 | Skeleton, briefs and a vertical slice | M | `openyamm-studio/` CMake project compiling the clean sources in place (section 1); `oymap` with `export` and `build-map`/`compile-indoor` equivalents; schema v0 for the project format and the brief, with the canonical writer and `oymap fmt`; L0–L3 briefs written for the four calibration maps; **the slice:** a small dungeon (five to eight box rooms, openings, one keyed door, one lever, a few spawns and lights) written by an agent as `plan.yml`, `rooms.yml`, `objects.yml` and `wiring.yml`, lowered by a first `oymap build` to BLV, scene and Lua, and walked in the game from a scratch asset root; wasm CI build with a smoke test | `oymap` reads every MM6–MM9 map; the briefs exist and the schema can hold them; the slice dungeon is walked start to goal in a headless scenario and you accept its screenshots as a plain but correct map; every lesson from the slice is applied to schema v0 before S1 builds on it |
| S1 | Read side and metrics | L | The five cuts of section 10a; `oymap build-map` (moved from S0 with G5); scene writers at parity; import of shipped maps into projects; ids lock; checks tier 0 and 1; flow graph; labelled renders; comparison metrics; the read commands | All maps import and round-trip; the audit finds the walkthrough issues (Goblinwatch key E, Gharik's lever 35, the Necromancer's Lab dead handlers); metrics computed for the calibration originals; the game is unchanged after each cut |
| S2 | Operations, host and agent interface | L | Documents, revisions and history in the core; operations for Wire, Populate and Dress; overlay compile; `oymap serve`; the host; the MCP server; `map_exec`; asset catalogue and placeholders; game-side dev mount and reload; agent evaluation v1 | An agent re-wires Goblinwatch's vault and New Sorpigal's wells as an overlay that plays the same in a scripted playtest; a hand edit between two agent transactions is detected, diffed and undoable |
| S3 | Indoor authoring through operations | XL | Rooms, caves, stairs, spirals, openings; lowering to the compiler; themes and face paint; door library and door from named faces; lifts; liquids; set-piece import with face matching; the dungeon part of the Python port (section 2a) with parity checks. No browser: agents work through `oymap` and MCP, people review through labelled renders, game tours and Play | Temple of the Moon and Warlord's Fortress calibrated; Goblinwatch, the Necromancer's Lab and Gharik's Forge rebuilt within bands; Xeen dungeons XD-01 to XD-05 built |
| S4 | Outdoor authoring through operations | XL | Map card and zones; landform and heightmap import; road splines with MM tile selection; plots; kit library; building import; scatter; landmarks; the terrain and placement part of the Python port. No browser, as S3 | Ravenshore and Harmondale calibrated; New Sorpigal and Shadowspire within bands; Vertigo Meadows built. **From here agents build complete indoor and outdoor maps; everything after is comfort and reach** |
| S5 | Browser editor | XL | In this order: (a) local mode view and review: web app shell, plan and 3D views, walk mode, flow graph view, pins, live pairing; (b) authoring UI over the operations of S2–S4 (stage bar, tools, inspector, Wire stage); (c) hosted mode with the wasm core and the asset plan of section 9 | (a) You walk the calibration and held-out maps in the browser, pin one, and an agent resolves the pins live; (b) you rebuild one room wing and one town block by hand; (c) the hosted page opens a player's install, stays inside its memory budget and builds the slice dungeon byte-identical to the native build |
| S6 | MM9 profiles and extras | L | Open-air BLV terrain, water volumes, ladders, destructibles, pulsing lights, cinematics timeline, MCP App viewer, named mods and sharing | An MM9 region edited as an overlay; a mod installed and switched off in the game |
| S7 | Consolidation | L | Move the reused sources into `openyamm_core`; the game links it; repoint `mm9_compile_indoor_source` and the 19 `--headless-build-map` callers; delete `editor/` per [EDITOR_RETIREMENT.md](EDITOR_RETIREMENT.md) | Game unchanged (tests, release scenarios, load times on MM6–MM9); every BLV and ODM project rebuilds byte-identical; no source compiled in two places |

S0 to S4 need no UI: one reader, one set of checks, the agent tools and full map authoring for every pipeline. The
browser editor (S5) is built against operations that have already made real maps. If the work has to stop early, the
end of S2 (audits and overlay edits of every shipped map) and the end of S4 (complete new maps by agents) are the
two points where what exists is whole and useful on its own.

Why the slice is in S0: the project format and the lowering from rooms to BLV are the plan's least proven parts, and
everything from S1 on builds on them. One small real map at the start is the cheapest way to find what the format
cannot say. The slice lowers through the existing indoor compiler. `compileIndoorSourceGeometry` takes a mesh
file path and a metadata struct, so the lowering writes the mesh (named `ROOM_`/`PORTAL_`/`MECH_` nodes) into the
project's build folder and fills the metadata in memory, the same inputs the Python kits produce; an in-memory mesh
entry point is a later, optional change to the compiler. It takes its room and opening rules from `mm9r_common/dungeon/rooms.py` and `geometry.py`, and
needs none of the `game/` cuts. Its code is the start of `core/project`, not a throwaway.

**State after the first part of S3** ([S3.md](S3.md)): S0 to S2 are done. S3 has its room shapes (any simple
outline, paths, stairs, ramps, pillars, platforms), wiring conditions and effects, the script reference, projects
read without installing and the calibration comparison; its acceptance rows (two calibrated dungeons, three
rebuilds, five Xeen dungeons) are open, as are hinged doors, lifts, liquids, shaped ceilings, set-piece import and
the Python port.

## 13. Risks

- **Three oversized files** (`MapAssetLoader.cpp`, `GameDataLoader.cpp`, `EventRuntime.cpp`) mix pure logic with
  textures, threads and gameplay. They are split, not moved, with behaviour checks after each cut.
- **Regressions in the game.** All worlds share the moved code. Every move is measured for behaviour, load time and
  memory on MM6, MM7, MM8 and MM9 maps.
- **Writer parity.** Scene writers lose data today. Round-trip tests over every shipped scene come before any writer
  is used to save.
- **Generated content.** Generated map Lua and MM9 converter outputs are never written by the studio; it writes
  overlays or changes go through the converters.
- **Saves.** Rebuilt maps change their layout identity and reset map state in saves. `ids.lock.yml` keeps ids stable;
  overlays do not touch layout.
- **ODM BModel BSP.** The outdoor writer writes BModels without generating a BSP (as imported maps do today). Confirm
  the runtime never needs it before the outdoor milestone.
- **Toolchain.** yaml-cpp exceptions with Lua longjmp under wasm; the PhysicsFS singleton; physical-path APIs.
  Found in S0 (`openyamm-studio/wasm/README.md`): Emscripten is pinned to 4.0.10 because newer libc++ fails on
  `std::vector<bx::Vec3>` (raising the pin needs a newer bx or a core vector type); `YAML::Emitter` breaks the wasm
  program's exit, so every writer the core reaches goes through `core/CanonicalYaml`, which rules out reusing the
  editor's scene serialisers as they are (section 2, `core/scene`: their key lists are the reference, their code is
  not moved).
- **yaml-cpp nodes alias their tree.** Assigning or sorting nodes rewrites the document; the non-const `operator[]`
  adds keys. It corrupted a project file once in S0. Rules are in `openyamm-studio/README.md`; code that holds
  `YAML::Node` values is reviewed for it.
- **Scope.** The Python port (section 2a) and the web UI are the two largest parts. The port is ordered by what the
  calibration and Xeen maps need and checked for parity piece by piece; the UI comes after the operations it drives
  have made real maps (S5), and the plan is whole at the end of S2 and of S4 if it stops there.
- **A format fixed too early.** Schema v0 is written before any map is built from it. The S0 slice and the first
  calibration builds will change it; until the end of S3 the schema carries a version and `oymap` migrates projects
  forward, and the briefs are re-checked against each version.
- **The early cuts in `game/`.** G1–G4 touch files other sessions work in. Each is move-only, small and announced;
  if one is blocked, the feature that needs it waits, and nothing is copied.
- **Hosted mode.** Lazy package reads, compressed-texture upload and the 4 GB heap are unproven here. Hosted mode is
  last in S5 and is cut down to view and review if the memory budget cannot be met.
- **Compiling in place until S7.** Other sessions change `game/` and `engine/` meanwhile; a change there can break the
  studio's build. The studio's CI job catches it; fixes go into the studio's source lists, not into copies.
- **Calibration leaks.** A builder that has seen the original map proves nothing. Builders run without access to the
  target map's files, and transcripts are checked.

## 14. Changes from the pre-implementation review (2026-11-12)

The session that took over the plan reviewed it against the code before S0, at the user's request, and the user asked
for the fundamental problems to be fixed in the plan. What changed:

| # | Problem found | Change | Where |
|---|---|---|---|
| 1 | The project format and the rooms-to-BLV lowering were first exercised at S4, after three milestones built on them; calibration builds could not start before S4; the browser editor came before any authoring | A vertical slice in S0; indoor and outdoor authoring through operations are S3 and S4; the browser editor is S5, built over operations that already made maps | 12 |
| 2 | Porting the generic third of the Python builders (about 50 000 lines, the dungeon kit alone 11 500) was one sentence | Sized, ordered and given parity rules | 2a, 11, 13 |
| 3 | "No change to `game/` until S7" did not hold: the indoor movement controller, overlay discovery, table loading and collision-set building are tangled with `EventRuntime`, SDL, bgfx and threads, and S1 needs them | Include closures recorded; four move-only cuts G1–G4 scheduled at S1; S0 needs none | 1, 10a |
| 4 | Two sources of truth: files open to any editor, but revisions and undo in an operation log kept by the TypeScript host, which `oymap edit` and the hosted page do not have; yaml-cpp drops comments and formatting | The files are the truth; revision is a content hash; history is file snapshots; all of it in `core/ops`; canonical form with `notes:` fields and `oymap fmt` | 4, 5, 7, 11 |
| 5 | The host loaded the wasm core "or the native `oymap` for heavy jobs": two code paths and a file system through Node | The host is a thin process over a native `oymap serve`; wasm serves the hosted page only, kept alive by a CI build from S0; pairing token | 1, 3, 8 |
| 6 | The hosted page had no plan for a 3.3 GB install, cooked textures, the 4 GB heap, or for what it can do without the game | A capability table per mode; packages read by byte range; textures uploaded compressed; a memory budget as an acceptance check; hosted mode last in S5 | 9, 13 |

Smaller changes made at the same time: face settings keyed by node names first (4); flow-graph edges derived from
Lua marked approximate, unknowns listed, hand-stated conditions allowed (6); native and wasm builds must be
byte-identical (3, 11); two named stopping points (12).

Not changed, and still to do before S0 starts: re-check the MCP facts in `research/MCP_AND_AGENT_TOOLS.md` against
the current specification and client documents (not needed before S2), and write the S0 task list.
