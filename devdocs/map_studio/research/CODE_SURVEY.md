# Research: code survey for the studio (2026-11-12)

Read-only surveys of `editor/`, the map code in `engine/` and `game/`, and the Python builders in
`level_generation/` and `tools/`. PLAN.md and EDITOR_RETIREMENT.md use these findings; this file keeps the details.
Line numbers were correct on 2026-11-12; re-check them.

## `editor/` (56 681 lines)

- `app/` 16 740 (`EditorMainWindow.cpp` 15 753), `viewport/` 13 720, `document/` 17 381 (`EditorSession.cpp` 7 675,
  `EditorDocument.cpp` 5 570), `import/` 4 777, `headless/` 4 063.
- **Worth keeping:** the indoor compiler (`import/IndoorSourceGeometryCompiler`, entry `.cpp:1541-1844`), driven by
  node-name prefixes `ROOM_`, `PORTAL_`, `INTERACT_`/`IPVAR_`/`STATIC_`, `TRIGGER_`, `MECH_`, `DECOR_`/`LIGHT_`/`SPAWN_`;
  rooms and portals must be authored as meshes. `IndoorDerivedGeometry` builds per-sector BSP and outlines (7 000
  outline limit, int16 limits). `ObjModelImport` (OBJ, glTF via cgltf, coplanar merge). `IndoorGeometryMetadata`: the
  indoor `geometry.yml` schema. 23 doctest cases in `tests/IndoorSourceGeometryCompilerTests.cpp`, not run in CI.
- Outdoor sidecars: `map.yml`, `geometry.yml` (BModel imports), `terrain.yml` (hex height, tile, attribute maps).
  Build logic in `EditorDocument.cpp` (`buildImportedBModel` :1105, `buildOutdoorGeometryFromSourcePackage` :1273,
  `compileOutdoorGeometryBytes` :1392, scene serialisers :4586/:4836/:4963, map-stats rows :1862-2041).
- Undo stores full scene text snapshots (capped at 256); no operations. Not worth porting.
- Users: `mm9_compile_indoor_source` (46 `mm9r_*` projects, Hesper dungeons, Brackenford), `--headless-build-map`
  (19 scripts). See EDITOR_RETIREMENT.md.

## Engine and game map code

- Third-party: SDL3 3.4.2, bgfx stack, FFmpeg n8.0.1, Lua 5.4.8 (`openyamm_lua`), PhysicsFS 3.2.0 (zip support),
  yaml-cpp 0.8.0, imgui, freetype, spdlog, fmt, Monocypher, zstd. No JSON library (JSON parsed with yaml-cpp, glTF with
  cgltf).
- `openyamm_engine` exports SDL3 and bgfx PUBLIC; `openyamm_game` is one ~450-source library; game source lists are
  repeated in game, editor, tools and tests CMake files.
- **Formats:** ODM reader and writer (`game/outdoor/OutdoorMapData.cpp:327, 909, 993`; BModels written without BSP),
  BLV reader and writer (`game/indoor/IndoorMapData.cpp:553, 1068`; always version 8). Both free of SDL and bgfx.
- **Scene:** parsers in `game/maps/OutdoorSceneYml.cpp` (3 512 lines) and `IndoorSceneYml.cpp` (4 075, 279 key
  strings); overlays via `SceneOverlayOperations`; discovery in `MapAssetLoader.cpp:3963-3990` (`<stem>_*.scene.yml`
  or `<stem>.scene.*.yml`). Writers only in the editor and incomplete.
- **Map Lua:** path and overlay helpers in `GameDataLoader.cpp:229-447` (`<base>_*.lua`, `<base>.fixup.lua`),
  overlays appended as text, then `ScriptedEventProgram::loadFromLuaText` (`ScriptedEventProgram.cpp:705`), which
  enumerates handlers with a stub `evt`. `EventRuntime` (12 210 lines, 224 `evt` functions) executes them;
  `ISceneEventContext` has 10 pure virtuals (stub in `tests/EventScriptingTests.cpp:33`).
- **AssetFileSystem:** PhysicsFS-based; SDL only under Android; PhysicsFS supports Emscripten and memory/IO mounts;
  one global instance per process.
- **Collision:** `IndoorMovementController`, `OutdoorMovementController`, pathfinding (`PathMap`, `PathPlanner`),
  `--headless-check-indoor-reachability` (`HeadlessOutdoorDiagnostics.cpp:4581`). `IndoorGeometryUtils.h` includes
  `EventRuntime.h` only to pass `EventRuntimeState*`.
- **Wasm risks:** `std::async` and threads in `MapAssetLoader`; yaml-cpp exceptions plus Lua longjmp; `std::filesystem`
  and `current_path()`; `SDL_GetTicksNS` and `SDL_LoadBMP_IO` in `MapAssetLoader`; wasm32 `size_t`.

## Python builders and checks

- ~150 000 lines in `level_generation/projects` (991 files): `mm9r_common` 22 669, 46 `mm9r_*` projects 59 124,
  `hesper_*` 33 150, `mm5_*` 18 203, `brackenford_*` 11 367; `tools/**/*.py` ~98 000.
- No Python writes BLV binaries: all routes write a GLB plus `geometry.yml` and run `mm9_compile_indoor_source`
  (`mm9r_common/dungeon/package.py`, `hesper_stage/blv_kit.py`, `transcode_mm9_dat_to_blv.py`). Outdoor routes write
  `map.yml`/`geometry.yml`/`terrain.yml` and run `--headless-build-map`. `transcode_mm9_dat_to_odm.py` writes ODM bytes
  (stale MM9 ODMs). Two scripts splice BModels into existing ODMs.
- `util/map_export.py` (readers for ODM, BLV, DLV) is referenced by about 256 Python files.
- Scene YAML: no shared writer; four projects build dicts by hand.
- Generic checks worth porting: `hesper_stage/check_walkability.py`, `mm9r_common/sector_audit.py`,
  `actor_floor_audit.py`, `camera_gate.py`, `check_actor_sizes.py`, `check_decoration_ids.py`, `hesper_out4/check_relief.py`,
  door-sound presence, light caps, density algorithm, hole and portal sweeps, `tools/lighting/stale_bakes.py`,
  `check_winding.py`. 35 hand-written floor/height samplers exist across projects.
- About a third of project code is generic: terrain shaping (Hesper `height_at`/`grade`/`flatten`), road rasterisation
  and tile selection, building kits, scatter with clearance, spawn placement, door tables and Lua scaffolding,
  staging and installation (four implementations), tour and scenario writers (37 `make_tour.py`, 39
  `make_scenarios.py` copies).
- Calibration data: `level_generation/reference_maps.json`, `reference_notes.json`, `evidence/mm{6,7,8}/*.json`,
  `catalogues/**` (Ravenshore, Alvar, Garrote catalogues; `outdoor_decorations/inventory.json` for 42 ODMs),
  `tools/mm9_import_discovery/mm9_density_targets.yml`; much calibration is prose in Markdown.
- Asset indexes: `engine/models/*decorations*.yml`, `decoration_data.txt` (676 rows), `textures_x4/inventory.json`
  (4 103 textures), surface materials `textures.yml`, `engine/terrain_materials/library.yml`, `items.yml`; about 2 678
  GLBs with no central tags or thumbnails.
