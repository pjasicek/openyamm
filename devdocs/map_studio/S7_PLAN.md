# S7: consolidation (plan)

Status: done 2026-11-15, steps 0 to 8 (section 7 records the checks). Written as a plan the same day while S6 was
being built; the inventory re-taken at step 0 matched section 1.1 unchanged (52 files, the same line counts). The milestone row is PLAN.md section 12 (S7); the editor's dependents are in
[EDITOR_RETIREMENT.md](EDITOR_RETIREMENT.md); the layering is PLAN.md sections 1, 2 and 10a.

Exit (PLAN.md 12): the game is unchanged (tests, release scenarios, load times on MM6–MM9); every BLV and ODM
project rebuilds byte-identical; no source is compiled in two places.

## 0. Summary and recommended decisions

1. **The shared core goes to a top-level `core/`, not `openyamm-studio/core/`.** The game, Android, iOS and the
   release CI would otherwise depend on a folder that also holds the web app, the host, emsdk and eleven build trees;
   four sparse checkouts in `.github/workflows/packages.yml` list the folders they build and would need
   `/openyamm-studio/core/` instead of a plain `/core/`. `openyamm-studio/core/` keeps the studio's own modules
   (project, ops, check, preview, assets: 51 `.cpp`, about 92 000 lines), which the game never needs.
2. **Two libraries in `core/CMakeLists.txt`:** `openyamm_core` (the 44 game and engine sources the game already
   compiles) and `openyamm_core_compile` (the 8 editor sources of the indoor compiler and the outdoor build, plus the
   body of `tools/mm9_compile_indoor_source_main.cpp`). The game links only `openyamm_core`; tools, the unit tests and
   the studio link both.
3. **S7 makes the library, not the physical move of the 44 files.** They become `openyamm_core` where they stand
   (`game/...`, `engine/...`): one source list, one compile per build tree, every target links it. That meets all
   three exit conditions with CMake changes only, and their objects can be proven identical to today's. The 8 editor
   sources do move physically (to `core/compile/`), because `editor/` is deleted. Moving the 44 files into
   `core/io`, `core/format` ... is a follow-up (S7b, section 5): it rewrites 827 `#include` lines in 493 files
   (302 of them in `game/`, a tree other sessions edit daily) and first needs one more cut in `game/` (G1b,
   section 1.3). This deviates from the wording "move the reused sources into core/" in PLAN.md section 1; the lead
   or the user decides.
4. **Callers:** the indoor compiler keeps its name and arguments (`build/tools/mm9_compile_indoor_source`), so its 8
   callers do not change. The 18 callers of `openyamm-editor --headless-build-map` change to
   `openyamm-studio/build/oymap build-map` (same inputs, same files written; byte parity already shown on 11 maps
   by `openyamm-studio/tests/build_map_parity.sh`, extended to all 42 outdoor packages in section 4.5).

## 1. Inventory (from the code, 2026-11-15)

### 1.1 What `openyamm-studio/CMakeLists.txt` compiles from outside the studio

`OYMAP_INPLACE_SOURCES` (lines 40–101) holds 52 files: 33 from `game/` (36 003 lines), 11 from `engine/`
(5 495 lines), 8 from `editor/` (12 928 lines). It also compiles `tools/mm9_compile_indoor_source_main.cpp`
(273 lines) into `oymap`, `oymap_rpc`, `oymap_worker` and `oymap_tests` with `main` renamed
(`OYMAP_LEGACY_COMPILE_INDOOR`, line 164), and reads `game/events/EventRuntime.cpp` as text to list the event
functions (`cmake/EmbedEventFunctions.cmake`; not compiled, stays as it is).

"Also compiled by" is the game tree's targets today; every one of these is a second (or third) compile of the same
file, which is what "no source compiled in two places" removes.

| Module (PLAN.md 2) | Source | Lines | Also compiled by today |
|---|---|--:|---|
| io | `engine/AssetFileSystem.cpp` | 2 434 | openyamm_engine, openyamm_unit_tests |
| io | `engine/AssetPackIndex.cpp` | 309 | openyamm_engine, openyamm_unit_tests |
| io | `engine/AssetScaleTier.cpp` | 197 | openyamm_engine, openyamm_unit_tests |
| io | `engine/TextTable.cpp` | 138 | openyamm_engine, openyamm_unit_tests |
| io | `engine/ImageAssetPaths.cpp` | 312 | openyamm_engine, openyamm_unit_tests |
| io | `engine/render/CookedTextureHeader.cpp` | 37 | openyamm_engine, openyamm_unit_tests |
| io | `engine/models/CgltfImplementation.cpp` | 2 | openyamm_engine, openyamm_unit_tests |
| io | `engine/update/Sha256.cpp` | 178 | openyamm_engine, openyamm_unit_tests |
| text | `engine/Localization.cpp` | 469 | openyamm_engine, openyamm_unit_tests |
| text | `engine/TextCatalog.cpp` | 1 257 | openyamm_engine, openyamm_unit_tests |
| script | `engine/scripting/LuaStateOwner.cpp` | 162 | openyamm_engine, openyamm_unit_tests |
| script | `game/events/ScriptedEventProgram.cpp` | 897 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| script | `game/data/MapScriptSources.cpp` | 301 | openyamm_game, openyamm_unit_tests |
| format | `game/outdoor/OutdoorMapData.cpp` | 1 191 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| format | `game/indoor/IndoorMapData.cpp` | 1 510 | openyamm_game, openyamm_unit_tests, openyamm_event_asset_export, openyamm_indoor_source, openyamm-editor |
| format | `game/maps/MapDeltaData.cpp` | 803 | openyamm_game, openyamm_unit_tests, openyamm_indoor_source, openyamm-editor |
| format | `game/maps/MapIdentity.cpp` | 93 | openyamm_game, openyamm_unit_tests, openyamm_event_asset_export, openyamm-editor |
| scene | `game/maps/OutdoorSceneYml.cpp` | 3 539 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/maps/IndoorSceneYml.cpp` | 4 102 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/maps/SceneOverlayOperations.cpp` | 98 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/maps/SceneOverlayPaths.cpp` | 69 | openyamm_game, openyamm_unit_tests |
| scene | `game/maps/MapItemSourceYml.cpp` | 532 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/maps/MechanismAudioYml.cpp` | 115 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/maps/MistYml.cpp` | 348 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/indoor/IndoorWater.cpp` | 331 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| scene | `game/indoor/IndoorDaylight.cpp` | 151 | openyamm_game, openyamm_unit_tests |
| scene | `game/render/SkyState.cpp` | 550 | openyamm_game, openyamm_unit_tests |
| tables | `game/tables/SpriteTables.cpp` | 1 160 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| tables | `game/tables/Mm9MonsterAi.cpp` | 859 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| tables | `game/maps/MapRegistry.cpp` | 95 | openyamm_game, openyamm_unit_tests |
| terrain | `game/maps/TerrainTileData.cpp` | 298 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| collision | `game/indoor/IndoorGeometryUtils.cpp` | 2 714 | openyamm_game, openyamm_unit_tests, openyamm_indoor_source, openyamm-editor |
| collision | `game/indoor/IndoorMovers.cpp` | 731 | openyamm_game, openyamm_unit_tests, openyamm_indoor_source, openyamm-editor |
| collision | `game/indoor/IndoorPortalGraph.cpp` | 232 | openyamm_game, openyamm_unit_tests, openyamm_indoor_source, openyamm-editor |
| collision | `game/indoor/IndoorSectorFaceGrid.cpp` | 597 | openyamm_game, openyamm_unit_tests, openyamm_indoor_source, openyamm-editor |
| collision | `game/indoor/IndoorCollisionPrimitives.cpp` | 999 | openyamm_game, openyamm_unit_tests |
| collision | `game/indoor/IndoorMovementController.cpp` | 5 373 | openyamm_game, openyamm_unit_tests |
| collision | `game/indoor/IndoorPathfindingBuilder.cpp` | 128 | openyamm_game, openyamm_unit_tests |
| collision | `game/events/MechanismDistance.cpp` | 45 | openyamm_game, openyamm_unit_tests |
| collision | `game/outdoor/OutdoorGeometryUtils.cpp` | 1 045 | openyamm_game, openyamm_unit_tests, openyamm-editor |
| collision | `game/outdoor/OutdoorMovementController.cpp` | 3 855 | openyamm_game, openyamm_unit_tests |
| collision | `game/outdoor/OutdoorPathfindingBuilder.cpp` | 485 | openyamm_game, openyamm_unit_tests |
| collision | `game/pathfinding/PathMap.cpp` | 2 123 | openyamm_game, openyamm_unit_tests |
| collision | `game/pathfinding/PathPlanner.cpp` | 634 | openyamm_game, openyamm_unit_tests |
| compile | `editor/document/IndoorGeometryMetadata.cpp` | 1 796 | openyamm_indoor_source, openyamm-editor |
| compile | `editor/import/IndoorSourceGeometryCompiler.cpp` | 1 846 | openyamm_indoor_source, openyamm-editor |
| compile | `editor/import/IndoorDerivedGeometry.cpp` | 462 | openyamm_indoor_source, openyamm-editor |
| compile | `editor/import/ObjModelImport.cpp` | 1 870 | openyamm_indoor_source, openyamm-editor |
| compile | `editor/document/EditorDocument.cpp` | 5 580 | openyamm-editor |
| compile | `editor/document/OutdoorGeometryMetadata.cpp` | 558 | openyamm-editor |
| compile | `editor/document/OutdoorMapPackageMetadata.cpp` | 588 | openyamm-editor |
| compile | `editor/document/OutdoorTerrainMetadata.cpp` | 228 | openyamm-editor |
| compile | `tools/mm9_compile_indoor_source_main.cpp` (the legacy `compile-indoor`) | 273 | mm9_compile_indoor_source |

`openyamm_core` = the first 44 rows; `openyamm_core_compile` = the last 9. None of the 44 tests a preprocessor macro
other than `__ANDROID__` (`engine/AssetFileSystem.cpp:4, 375, 900, 911`, which includes `SDL3/SDL_system.h` on
Android); none uses `__FILE__`, and the game builds without LTO. Their objects therefore depend only on the compiler
and its flags, which section 4.3 uses.

The studio's own tree (`openyamm-studio/core`, `cli`, `wasm`, `tests`) is not part of `openyamm_core`. Its library
`oymap_core` keeps those files and links the two new libraries.

### 1.2 Third-party sources

- **cgltf** comes from bgfx's `3rdparty/` folder for the game (`engine/CMakeLists.txt` PRIVATE include,
  `tools/CMakeLists.txt:47-51`) and, when `build/_deps/bgfx-src` exists, for the studio too
  (`openyamm-studio/cmake/Deps.cmake`, else v1.15 is fetched). S7 vendors cgltf v1.15 as `third_party/cgltf/cgltf/cgltf.h`
  (MIT; checked equal to bgfx's copy with `cmp` before use) so the core does not reach into bgfx.
- **bx**: the 44 sources use `bx/math.h` (the movement code). In the game tree the core links `openyamm_bgfx`, which
  carries bx and its `BX_CONFIG_DEBUG` definition (`cmake/BgfxRuntime.cmake:271-274`), so the core sees bx exactly as
  the game does today; in the studio tree it links `oymap_bx` as now. No core file includes a bgfx header.
- **yaml-cpp 0.8.0, PhysicsFS 3.2.0, Lua 5.4.8**: the same pins in both trees (`cmake/Dependencies.cmake:19-28`,
  `openyamm-studio/cmake/Deps.cmake`). Lua's target is `${OPENYAMM_LUA_TARGET}` (`openyamm_lua`) in the game tree and
  `oymap_lua` in the studio tree.
- **musl math and zstd** are used only by the studio's own modules (`openyamm-studio/core/CoreMath.h`, history); they
  stay in the studio.

### 1.3 Headers the 44 sources reach that are not in the list

Headers only (types and inline code), which is why the studio links without their `.cpp`: `game/FaceEnums.h`,
`BinaryReader.h`, `StringUtils.h`, `game/events/EvtEnums.h`, `MechanismAudioProfile.h`, `ScriptedEventTimer.h`,
`game/indoor/IndoorFog.h`, `IndoorModelLighting.h`, `IndoorOpenSky.h`, `game/maps/MapPresentation.h`,
`DecorationModelPlacement.h`, `MapRuntimeRestrictions.h`, `MapArenaDefinition.h`, `MapItemSourceData.h`,
`OutdoorSceneProfile.h`, `game/outdoor/OutdoorNavigationData.h`, `OutdoorRenderData.h`, `OutdoorLightingData.h`,
`OutdoorCollisionData.h`, `OutdoorWeatherProfile.h`, `game/render/Mist.h`, `SkyClock.h`, `SkyPresets.h`,
`game/audio/WorldAmbientSounds.h`, `game/party/InventoryItem.h`, `game/rules/ActorRulesetFacts.h`,
`game/tables/MapStats.h`, `SurfaceAnimation.h`, `game/pathfinding/PathfindingTypes.h`, `engine/Utf8Text.h`,
`engine/ImageAssetLoader.h`.

Two still reach the gameplay runtime, so cut G1 (PLAN.md 10a) is only half made:
`game/indoor/IndoorGeometryUtils.h:5` includes `game/events/EventRuntime.h` (for `EventRuntimeState`, which pulls in
`Party.h`), and `game/events/MechanismDistance.cpp:38` defines the member `EventRuntime::calculateMechanismDistance`.
This does not stop the library (it compiles and links today), but a physical move into `core/` would make core
headers include `game/` (cut **G1b** in section 5, S7b).

### 1.4 Re-taking the inventory

S6 may add files (its cut G4, `CinematicLibrary.*`, S6_PLAN.md section 3). Before step 1, re-run the inventory and
update this section:

```sh
python3 - <<'EOF'
import os, re, pathlib
R = pathlib.Path('.').resolve()
studio = (R / 'openyamm-studio/CMakeLists.txt').read_text()
body = re.search(r'set\(OYMAP_INPLACE_SOURCES(.*?)\n\)', studio, re.S).group(1)
inplace = [l.strip().replace('${OPENYAMM_ROOT}/', '') for l in body.splitlines() if l.strip().startswith('${')]
targets = {}
for cm, base in [('game', 'game'), ('engine', 'engine'), ('tests', 'tests'), ('tools', 'tools'), ('editor', 'editor')]:
    text = (R / cm / 'CMakeLists.txt').read_text()
    for m in re.finditer(r'add_(?:library|executable)\((\S+)(.*?)\n\)', text, re.S):
        files = set()
        for tok in re.findall(r'[\w./${}-]+\.cpp', m.group(2)):
            tok = tok.replace('${CMAKE_SOURCE_DIR}/', '')
            if not tok.startswith('${'):
                files.add(tok if tok.startswith(('game/', 'engine/', 'tools/', 'editor/'))
                          else os.path.normpath(os.path.join(base, tok)))
        targets[m.group(1)] = files
for f in inplace:
    print(f, sum(1 for _ in open(R / f)), ','.join(t for t, fs in targets.items() if f in fs), sep='\t')
EOF
```

## 2. Callers of the old production steps

### 2.1 The indoor compiler (`editor/import/IndoorSourceGeometryCompiler`, `mm9_compile_indoor_source`)

The library `openyamm_indoor_source` (`tools/CMakeLists.txt:34-59`) is linked by `mm9_compile_indoor_source`
(`:61-62`) and `openyamm_indoor_source_tests` (`:77-85`, 23 cases from `tests/IndoorSourceGeometryCompilerTests.cpp`,
built only with `OPENYAMM_BUILD_TOOLS`, which CI turns off). In-process callers: `openyamm-studio/core/IndoorBuild.cpp`
(`compileIndoorSourceGeometry`), `openyamm-studio/core/IndoorLowering.{h,cpp}` and `core/View.cpp` (the `Editor::`
metadata types), `openyamm-studio/cli/Commands.cpp:48, 572-580` (`oymap compile-indoor`).

Command-line callers (all `build/tools/mm9_compile_indoor_source <glb> <geometry.yml> <out.blv> [doors.yml]
[faces.yml]`):

| Caller | Used by | Repoints to |
|---|---|---|
| `level_generation/projects/mm9r_common/dungeon/build.py:44, 446` (`COMPILER`) | the 44 shipped MM9 maps (`mm9r_*/convert.py`, through `dungeon.main`) | unchanged |
| `level_generation/projects/mm9r_anskramkeep/legacy_converter/convert.py:53` | the superseded Anskram pilot | unchanged |
| `level_generation/projects/hesper_stage/blv_build.py:43` | `hesper_d00`–`d13`, `d15`, `d16`, `hesper_pickups_test`, `hesper_walk_test` | unchanged |
| `level_generation/projects/hesper_undervault/build_undervault.py:29` | Hesper undervault | unchanged |
| `level_generation/projects/brackenford_greywatch/build_greywatch.py:20` | Greywatch `lg02` | unchanged |
| `tools/mm9_import_discovery/regenerate_mm9_maps.sh:42` (`MM9_COMPILE_INDOOR_SOURCE`) | the old MM9 import into `assets_editor_dev` | unchanged |
| `tools/mm9_import_discovery/generate_mm9_maps_from_manifest.py:74` (`--compile-tool`) | same | unchanged |
| `tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py:1628` (optional `--compile-tool`) | same | unchanged |

The target keeps its name and arguments; only its link changes (to `openyamm_core_compile`), so none of these
change. The tool's body moves to `core/compile/LegacyCompileIndoor.cpp` as `int runLegacyCompileIndoor(int argc,
char **argv)`; `tools/mm9_compile_indoor_source_main.cpp` becomes a three-line `main` calling it, and
`oymap compile-indoor` calls the same function instead of compiling the tool's file with `main` renamed (otherwise
that file is compiled in two places). Live documents that name the tests' target change it (section 2.4).

### 2.2 The outdoor build (`openyamm-editor --headless-build-map`)

The 18 code callers, every one `subprocess.run([ROOT/'build/editor/openyamm-editor', '--asset-root', X,
['--world', W,] '--headless-build-map', <map.yml>])`. None parses the output; all write it to a log.

| Caller | Asset root, world | Status |
|---|---|---|
| `level_generation/projects/hesper_out1/build_out1.py:1740` | `output/hesper_stage/assets_editor_dev` | live |
| `level_generation/projects/hesper_out2/build_out2.py:1523` | same | live |
| `level_generation/projects/hesper_out3/build_out3.py:1303` | same | live |
| `level_generation/projects/hesper_out4/build_out4.py:1648` | same | live |
| `level_generation/projects/brackenford_greywatch/build_brackenford.py:62` | `--asset-root` (default `/tmp/openyamm-brackenford-greywatch/assets_editor_dev`) | live |
| `level_generation/projects/brackenford_greywatch/verify_outdoor_source.py:39` | same `/tmp` root | live |
| `level_generation/projects/mm5_castleview_kalindra/build_native.py:231` | `<--stage>/assets_dev`, `--world mm5` | live |
| `level_generation/projects/mm5_castleview_kalindra/build_desert_material_study.py:94` | same | study |
| `level_generation/projects/mm5_castleview_kalindra/build_rim_study.py:70` | same | study |
| `level_generation/projects/mm9r_isleofashes/convert.py:1028` | `review_root.ASSETS` | dead: the project is superseded and `convert.py` exits at its start (its README) |
| `level_generation/terrain/mm6_new_sorpigal_transitions/build_fixture.py:51` | `assets_dev` | fixture |
| `level_generation/terrain/mm6_new_sorpigal_water/build_fixture.py:34` | `assets_dev` | fixture |
| `level_generation/terrain/mm6_remaining/transitions/prepare_review.py:43` | `assets_dev` | fixture |
| `level_generation/terrain/mm7/prepare_review.py:84` | `assets_dev` | fixture |
| `level_generation/terrain/mm8/prepare_bank_fixtures.py:62` | `assets_dev` | fixture |
| `level_generation/terrain/mm8/prepare_extra_bank_fixtures.py:53` | `assets_dev` | fixture |
| `level_generation/terrain/mm8/prepare_land_fixtures.py:92` | `assets_dev` | fixture |
| `level_generation/terrain/mm8/prepare_road_fixtures.py:83` | `assets_dev` | fixture |

The nineteenth file of PLAN.md's count is `tools/mm9_import_discovery/run_mm9_active_gate.sh`, which calls editor
switches that no longer exist (lines 119-133): it is deleted. `openyamm-studio/tests/build_map_parity.sh` names the
editor only in comments.

**Repoint:** `[ROOT/'openyamm-studio/build/oymap', 'build-map', <map.yml>, '--asset-root', X, ['--world', W]]`.
`oymap build-map` (`openyamm-studio/cli/Commands.cpp:3376-3430`) is the editor's `runBuildMap`
(`editor/headless/EditorHeadlessDiagnostics.cpp:3618-3664`) on the same `EditorDocument`, with the same defaults
(asset root `assets_dev`, world `mm8`, scale x1 with x4 surface textures; `engine/ApplicationConfig.cpp:48-54` and
`editor/app/main.cpp:93`). It differs only in the base path given to PhysicsFS (the root's parent instead of
`argv[0]`) and in printing the built path without quotes. The callers then need the studio built
(`openyamm-studio/build.sh`); their READMEs say so.

Everything a build writes: the `.odm` beside the source; with a map package, the `.map.yml`
(`EditorDocument.cpp:2938`) and the rows of `engine/data_tables/map_stats.txt` and `map_navigation.txt` in the
"editor development root" (`:2888-2936`): the asset root itself when it is named `assets_editor_dev`, else its
sibling of that name (`engine/AssetFileSystem.cpp:188-196`). The parity check (4.5) compares all four.

### 2.3 The editor's other entry points

| Entry | Callers | Replacement |
|---|---|---|
| `--headless-run-regression-suite <suite>` of the editor (`editor/app/main.cpp:101`; 20 suites of scene YAML round trips, package lifecycle, placement) | only the broken `run_mm9_active_gate.sh` and a historical note in `codex/game/indoor_texture_alignment_fix.md` | the studio's round trips over every shipped map (S1) and `oymap_tests`; the game's own `--headless-run-regression-suite` is a different program and stays |
| `--headless-compare-outdoor-scene` | none | none needed |
| The desktop GUI (`editor/app`, `editor/viewport`, `EditorSession`: 37 000 lines): hand edits of faces (texture, UV, flags, triggers), BModel import from OBJ or GLB with transforms, new or duplicated outdoor maps, `IndoorSourceGeometryImport` (mesh to indoor metadata), playtest and simulated face clicks | no script; people | the browser editor (S5) and `oymap`; see 3.5 |

### 2.4 Documents to update

Live instructions (wrong after S7 if left): `AGENTS.md` (subsystem list), `README.md:243, 321-322` (editor build and
screenshots), `level_generation/PIPELINE_STATUS.md:23-51`, `design/kreegan_world/WORK_PACKAGES/BUILDER_GUIDE.md:60,
127-128`, `design/kreegan_world/WORK_PACKAGES/README.md`, `level_generation/projects/hesper_out1/README.md`,
`level_generation/projects/brackenford_greywatch/REBUILD.md:49-50` (builds `openyamm-editor` and
`openyamm_indoor_source_tests`), `level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md:170, 1195`
(`openyamm_indoor_source_tests`), `devdocs/mm9_rework/HANDOFF_20261107_ORCHESTRATOR.md:55` (the full MM9 rebuild
script builds `openyamm-editor`), `devdocs/mm9_rework/overnight/AGENT_BRIEF.md:81`, `tools/PERF_PROFILING.md`,
`tools/VULKAN_DLSS_TEST.md`, `openyamm-studio/README.md:112-115, 557`, `openyamm-studio/CMakeLists.txt` header
comment, `devdocs/map_studio/{PLAN,EDITOR_RETIREMENT,README}.md`.

Historical records (map READMEs that say "built with `mm9_compile_indoor_source`", ledgers, xeen research) stay as
written: the tool still exists under that name.

## 3. Linking and CMake

### 3.1 `core/CMakeLists.txt` (new)

- `openyamm_core` STATIC: the 44 sources of 1.1 at their current paths (`${CMAKE_CURRENT_SOURCE_DIR}/../game/...`).
  PUBLIC include `${repo root}` and `third_party/cgltf`; PUBLIC links `yaml-cpp::yaml-cpp`, `physfs-static`,
  `${OPENYAMM_CORE_LUA_TARGET}`, `${OPENYAMM_CORE_BX_TARGET}`; on Android PRIVATE `SDL3::SDL3` (for
  `AssetFileSystem.cpp`'s Android branch). C++20.
- `openyamm_core_compile` STATIC: `core/compile/*.cpp` (the 8 moved editor files and `LegacyCompileIndoor.cpp`),
  PUBLIC link `openyamm_core`.
- **No compile options in this file.** The game tree compiles the core with the game's flags, so Android arm64 (clang,
  whose default `-ffp-contract=on` fuses multiply-adds) keeps today's code for the movement and collision files; the
  studio's `-ffp-contract=off` and `-fwasm-exceptions` stay `add_compile_options` at the studio's top level, before it
  adds `core/`, so the studio's bytes do not change either.
- The two dependency variables are set by whoever adds the directory: the game tree `openyamm_lua` and
  `openyamm_bgfx`, the studio tree `oymap_lua` and `oymap_bx`.

### 3.2 The game tree

| File | Change |
|---|---|
| `CMakeLists.txt` | set the two variables and `add_subdirectory(core)` after `openyamm_configure_runtime_shaders()` and before `add_subdirectory(engine)` (line 95); at deletion remove `OPENYAMM_BUILD_EDITOR` (line 35) and `add_subdirectory(editor)` (191-193) |
| `engine/CMakeLists.txt` | drop the 11 engine sources; `target_link_libraries(openyamm_engine PUBLIC openyamm_core)` |
| `game/CMakeLists.txt` | drop the 33 game sources from `openyamm_game`; link `openyamm_core` PRIVATE (it also arrives through the engine) |
| `tests/CMakeLists.txt` | drop the 44 sources from `openyamm_unit_tests` (all 44 are listed there today); link `openyamm_core` and `openyamm_core_compile`; add `IndoorSourceGeometryCompilerTests.cpp` inside `TEST_SUITE("indoor_source_compiler")`, so CI runs the 23 cases (`--test-suite=indoor_source_compiler` runs them alone) |
| `tools/CMakeLists.txt` | delete `openyamm_indoor_source` and `openyamm_indoor_source_tests`; `mm9_compile_indoor_source` links `openyamm_core_compile` only (no longer SDL and bgfx); drop `../game/indoor/IndoorMapData.cpp` and `../game/maps/MapIdentity.cpp` from `openyamm_event_asset_export` (they come through the engine) |
| `editor/CMakeLists.txt` (until deleted) | drop the 20 core game sources and the 8 compile sources from `openyamm-editor`; link `openyamm_core_compile`. A static library's object is pulled in when one of its symbols is missing, so an editor that compiled its own copy and also linked the core could get duplicate symbols |
| `android/app/src/main/cpp/CMakeLists.txt` | none: `main` links `openyamm_game`, which brings the core |
| `cmake/BgfxRuntime.cmake:704-711, 801-802` | at deletion remove the two `editor_preview_material` shaders (nothing in `game/` or `engine/` loads them; they are in the runtime shader list the APK and packages carry) |

The other duplicates in `openyamm_unit_tests` (about 190 game sources it compiles beside `openyamm_game`) are not
core sources and are not touched by S7.

### 3.3 The studio tree (`openyamm-studio/CMakeLists.txt`, `cmake/Deps.cmake`)

Delete `OYMAP_INPLACE_SOURCES` and `OYMAP_LEGACY_COMPILE_INDOOR`; set the two variables to `oymap_lua` and
`oymap_bx`; `add_subdirectory(${OPENYAMM_ROOT}/core ${CMAKE_BINARY_DIR}/openyamm_core)` after line 36; `oymap_core`
is the studio's own sources and links `openyamm_core_compile` PUBLIC. `Deps.cmake` drops the cgltf branch.
`cli/Commands.cpp` calls `runLegacyCompileIndoor`. `tests/link_closure.py:16-17` reads object folders that no longer
exist (`openyamm_indoor_source.dir`): point it at `build/core/CMakeFiles/openyamm_core{,_compile}.dir`.

### 3.4 CI

- `.github/workflows/packages.yml`: add `/core/` and `/third_party/cgltf/` to the sparse checkouts of the jobs that
  build C++: windows (line 230), linux (321), macos (422), android (556). Without it every package job fails at
  configure. This lands **in the same change** as step 2.
- `.github/workflows/studio.yml` (not committed yet): its path filters name `editor/import/**`, `editor/document/**`
  and `tools/mm9_compile_indoor_source_main.cpp`; replace with `core/**` and `third_party/cgltf/**`.

### 3.5 What in `editor/` has no replacement yet

**Blocks deletion until fixed (each small):**

1. `tests/ImageAssetLoaderTests.cpp:106` decodes `editor/assets/editor_ux_work/mockups/Level editor UI redesign
   mockup.png`; deleting `editor/` fails a game unit test. Point it at a PNG under `tests/` or `assets_dev/`.
2. The MM9 full rebuild: `output/mm9_rework/final_r7_20261107/r7.sh:11` (and r5, r6, r8, r8b) runs `cmake --build
   build --target openyamm openyamm_unit_tests openyamm-editor mm9_compile_indoor_source`, and
   `devdocs/mm9_rework/HANDOFF_20261107_ORCHESTRATOR.md:55` tells the next run to copy that script. With the target
   gone the build line fails and the script stops. The handoff is updated by S7; the scripts under `output/` are the
   user's local files: the user (or the next orchestrator) drops `openyamm-editor` from the copied line.
3. The 18 outdoor callers (2.2) until repointed; the outdoor build itself until `EditorDocument` and its metadata
   files live in `core/compile`.
4. Live documents that tell agents to build or run the editor (2.4), until updated.
5. `AssetFileSystem::getEditorDevelopmentRoot()` is used by `EditorDocument.cpp` (the table rows of 2.2).
   EDITOR_RETIREMENT step 6 removes it from the engine; the rule (root named `assets_editor_dev` is itself, else its
   sibling) then moves into `core/compile` beside the build, unchanged, and the game stops creating
   `assets_editor_dev/` on every development start (`engine/AssetFileSystem.cpp:636-661`). `hesper_stage/stage.py`
   (stage root named `assets_editor_dev`) and `tests/WorldMissileTests.cpp:253` keep working because the rule is
   kept.

**No replacement, nothing found relying on it** (the user approved deleting the editor; worth one line of
confirmation that their own hand workflow uses none of these): hand editing of shipped maps' faces in a 3D viewport
(texture, UV tiling and rotation, flags, triggers, scene overrides), OBJ or GLB BModel import and reimport into an
outdoor map with transforms (the build step that turns an imported model into BModels, `buildImportedBModel`, does
move and keeps working for packages that reference models), new and duplicated outdoor maps, the mesh-to-metadata
seeding `IndoorSourceGeometryImport.cpp` (EDITOR_RETIREMENT: port later if the studio wants it), "simulate face
click", and the editor's 20 headless regression suites.

## 4. Exit checks

All work files go under `output/s7/` (git-ignored). `<phase>` is `ref` (before step 1) or `new` (after the step being
checked).

### 4.0 Reference set, taken once before step 1

```sh
mkdir -p output/s7_reference/bin output/s7_reference/objects
git rev-parse HEAD > output/s7_reference/HEAD; git status --short > output/s7_reference/status.txt
cmake --build build --target openyamm openyamm_unit_tests openyamm-editor mm9_compile_indoor_source \
    openyamm_indoor_source_tests openyamm_event_asset_export -j25        # inside locks/cmake_build.lock
openyamm-studio/build.sh
cp build/editor/openyamm-editor build/tools/mm9_compile_indoor_source openyamm-studio/build/oymap \
    output/s7_reference/bin/                                              # SDL is static: the copies run anywhere
# objects of the 44 core sources, for 4.3
for f in $(sed -n '/^set(OYMAP_INPLACE_SOURCES/,/^)/ s|.*\${OPENYAMM_ROOT}/\(game/[^ ]*\.cpp\)|\1|p' \
        openyamm-studio/CMakeLists.txt); do
    mkdir -p "output/s7_reference/objects/$(dirname "$f")"
    cp "build/game/CMakeFiles/openyamm_game.dir/${f#game/}.o" "output/s7_reference/objects/$f.o"; done
for f in $(sed -n '/^set(OYMAP_INPLACE_SOURCES/,/^)/ s|.*\${OPENYAMM_ROOT}/\(engine/[^ ]*\.cpp\)|\1|p' \
        openyamm-studio/CMakeLists.txt); do
    mkdir -p "output/s7_reference/objects/$(dirname "$f")"
    cp "build/engine/CMakeFiles/openyamm_engine.dir/${f#engine/}.o" "output/s7_reference/objects/$f.o"; done
```

Then run 4.1, 4.2, 4.4 and 4.5 with the reference binaries and keep their results. Run the reference rebuilds of 4.5
twice (`ref` and `ref2`) and `diff -r` them: a difference there is non-determinism in the old route, found before
it can be mistaken for a regression.

### 4.1 Unit tests

```sh
cmake --build build --target openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests > output/s7/unit_<phase>.txt 2>&1; tail -4 output/s7/unit_<phase>.txt
./build/tests/openyamm_unit_tests --test-suite=indoor_source_compiler      # after step 3; before: build/tools/openyamm_indoor_source_tests
openyamm-studio/build.sh && openyamm-studio/build/oymap_tests
```

Pass: the same test-case and assertion counts as the reference (plus the 23 compiler cases from step 3), no new
failure; `oymap_tests` all pass.

### 4.2 Scenarios and regression suites

```sh
mkdir -p output/s7/scen_<phase>
while read -r s; do case "$s" in ''|'#'*) continue ;; esac
    rm -rf output/s7/user_<phase>; mkdir -p output/s7/user_<phase>
    SDL_AUDIODRIVER=dummy ./build/game/openyamm --user-data "$PWD/output/s7/user_<phase>" \
        --headless-run-scenario "$PWD/tests/scenarios/$s" > "output/s7/scen_<phase>/$(basename "$s" .yml).log" 2>&1
    echo "$s $?"; done < tests/scenarios/release/scenarios.txt | tee output/s7/scen_<phase>.txt
```

The 12 release scenarios must all pass. The moved code is movement, collision, pathfinding, map formats and scene
parsing for every world, so the MM9 scenarios run too (AGENTS.md: MM9 work validates MM6–MM8 and the other way):
the same loop over `ls tests/scenarios/mm9/*.yml` (38 files), and the game's suites
`./build/game/openyamm --world <w> --headless-run-regression-suite <suite>` for `indoor outdoor maps save scripts
transitions` with `<w>` = mm6, mm7, mm8. Pass: the same pass and fail lists as the reference (some cases fail today;
the lists are compared, not the totals).

### 4.3 The game's objects are unchanged

Step 2 changes only which target compiles a file, not its path, flags or defines, so its object must be the same file
byte for byte:

```sh
cd output/s7_reference/objects && find . -name '*.o' | while read -r o; do
    new="../../../build/core/CMakeFiles/openyamm_core.dir/__/${o#./}"
    cmp -s "$o" "$new" && echo "same ${o#./}" || echo "DIFFERENT ${o#./}"; done | sort | uniq -c -w4
```

Pass: 44 same. A difference is investigated with `objdump -d` before anything else (an include path that now
resolves a header to another copy, a define that reached the file). The same comparison on Android: the objects of
`android/app/.cxx/<config>/<hash>/arm64-v8a/` before and after (step 2's Android build, 4.7).

### 4.4 Load times on MM6–MM9

Headless, the loaders' own timing (`OPENYAMM_MAP_LOAD_TIMING=1`, stderr), five loads per map, median of the last
`total_ms`, and peak memory:

```sh
mkdir -p output/s7/load_<phase>
for wm in mm6:oute3.odm mm6:6d01.blv mm7:7out01.odm mm7:7d06.blv mm8:out01.odm mm8:d13.blv \
          mm9:isleofashes.blv mm9:sturmfordcity.blv mm9:1000terrors.blv; do
    for i in 1 2 3 4 5; do
        OPENYAMM_MAP_LOAD_TIMING=1 /usr/bin/time -f 'rss_kb=%M' ./build/game/openyamm --world "${wm%%:*}" \
            --headless-profile-map-load-full "${wm#*:}" > /dev/null 2> "output/s7/load_<phase>/${wm#*:}.$i.log"
    done; done
grep -h 'MapLoadTiming.*total_ms\|rss_kb' output/s7/load_<phase>/*.log     # per map: median total, max rss
```

Pass: per map, the median within the spread of the reference's five runs and peak memory within 1 %. With identical
objects (4.3) only the link layout differs, so a difference here means a busy machine: repeat. The desktop
measurement with the renderer (`output/mm9_rework/geometry_audit/run_loads.sh` pattern: `./tools/run_game.sh
--isolated ... --warmup 1 --seconds 1`, `[MapLoadTiming]` and `[LoadingReadiness]` from the run's `game.log`) is a
performance measurement in AGENTS.md's sense: ask the user for a quiet machine, or skip it when 4.3 shows 44 equal
objects.

### 4.5 Every BLV and ODM project rebuilds byte-identical

The compile steps are pure functions of their source packages, so the packages that exist locally are compiled by
the reference binaries and by the new ones and the outputs compared. The source GLBs and ODMs are git-ignored: this
runs on this machine, not in CI.

**Indoor: 66 packages** (16 `hesper_d*`, 45 `mm9r_*` including the Anskram legacy snapshot, Hesper undervault,
pickups and walk tests, Greywatch `lg02` and its calibration map), each through the old tool, the new tool and
`oymap compile-indoor`:

```sh
find level_generation -path '*/work/*' -prune -o -path '*/runtime/*' -prune -o -name '*.geometry.yml' -print |
while read -r g; do
    d=$(dirname "$g"); s=$(basename "$g" .geometry.yml); [ -f "$d/$s.glb" ] || continue
    key=$(echo "$d/$s" | tr / _)
    for run in "ref output/s7_reference/bin/mm9_compile_indoor_source" "tool build/tools/mm9_compile_indoor_source" \
               "studio openyamm-studio/build/oymap compile-indoor"; do
        name=${run%% *}; out=output/s7/indoor/$name/$key; mkdir -p "$out"
        ${run#* } "$d/$s.glb" "$g" "$out/$s.blv" "$out/doors.yml" "$out/faces.yml" > "$out/log" 2>&1
        echo $? > "$out/rc"
    done; done
diff -r -x log output/s7/indoor/ref output/s7/indoor/tool && diff -r -x log output/s7/indoor/ref output/s7/indoor/studio
```

**Outdoor: 42 packages** (4 Hesper, Brackenford `lg01` and its terrain lab, 9 Castleview copies with `--world mm5`,
4 MM6 ship and Sorpigal playtests, the superseded Isle of Ashes, 22 terrain fixtures), each copied into an empty
folder (4 files: `.map.yml`, `.scene.yml`, `.geometry.yml`, `.terrain.yml`) and built against a hard-link copy of its
asset root named `assets_dev`, one copy per route, so the map_stats and map_navigation rows land in the copy's
sibling and never in a real root (atomic writes replace the linked file, they do not write through it):

```sh
# packages: the indoor find above with `[ -f "$d/$s.map.yml" ]` in place of the .glb test; each gets the asset
# root and world its caller uses (2.2), assets_dev and mm8 for the fixtures and playtests
build() {  # <route> <dir> <stem> <root> <world>
    w=output/s7/outdoor/$1/$(echo "$2/$3" | tr / _); mkdir -p "$w"
    cp "$2/$3".{map,scene,geometry,terrain}.yml "$w/"
    root=output/s7/roots/$1/$(basename "$4")_$5/assets_dev
    [ -d "$root" ] || { mkdir -p "$(dirname "$root")"; cp -al "$4" "$root"; }
    case $1 in
        ref) output/s7_reference/bin/openyamm-editor --asset-root "$root" --world "$5" \
                 --headless-build-map "$w/$3.map.yml" ;;
        new) openyamm-studio/build/oymap build-map "$w/$3.map.yml" --asset-root "$root" --world "$5" ;;
    esac > "$w/log" 2>&1; echo $? > "$w/rc"
}
# after all packages: the .odm and .map.yml files, then the two tables of every scratch root
diff -r -x log output/s7/outdoor/ref output/s7/outdoor/new
for f in output/s7/roots/ref/*/assets_editor_dev/engine/data_tables/map_{stats,navigation}.txt; do
    cmp "$f" "${f/roots\/ref/roots\/new}"; done
```

Castleview and Brackenford build against `/tmp` stages their scripts make (`build_native.py --stage`,
`build_brackenford.py --asset-root`); make those stages under `output/s7/stages/` first, or list the package as
skipped with the reason, as `build_map_parity.sh` does. A package the reference fails to build counts as passed only
if the new route fails the same way.

**The studio's projects:** the 22 L4 projects (`devdocs/map_studio/briefs/*/L4`, `devdocs/xeen/briefs/*/L4`) and the
two examples, built by the reference `oymap` and the new one:

```sh
source openyamm-studio/tests/calibration_projects.sh
calibration_projects "$PWD/assets_dev" "$PWD/output/studio_play/xeen_root" | while read -r name project root; do
    build_fresh_copy "output/s7/l4/ref/$name" "$project" "$root" output/s7_reference/bin/oymap
    build_fresh_copy "output/s7/l4/new/$name" "$project" "$root" openyamm-studio/build/oymap; done
diff -r -x stdout.json -x stderr.txt output/s7/l4/ref output/s7/l4/new
openyamm-studio/tests/native_vs_wasm.sh                  # native against wasm, 22/22, after the wasm build
```

(`stdout.json` names its work folder; compare it with the folder name replaced.) Pass: all identical.

**End to end, once after the callers are repointed:** one MM9 dungeon and one region through their converters into
scratch folders, before and after (`python3 level_generation/projects/mm9r_lichlab/convert.py --scratch
output/s7/e2e/<phase>/lichlab`, the same for `mm9r_sturmford_blv`; `diff -r` the two `runtime/` folders), one
terrain fixture script (`level_generation/terrain/mm8/prepare_land_fixtures.py`: `git status` shows no change to
tracked files and the `.odm` files equal the reference), and `hesper_out1/build_out1.py` against a hard-link copy of
the stage. These prove the Python callers reach the new binaries; the bytes are already proven above.

### 4.6 No source compiled in two places

```sh
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake -S openyamm-studio -B openyamm-studio/build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
python3 - <<'EOF'
import collections, json, re, pathlib
core = pathlib.Path('core/CMakeLists.txt').read_text()
sources = {pathlib.Path('core', p).resolve() for p in re.findall(r'\.\./[\w./-]+\.cpp', core)}  # the in-place list
sources |= {p.resolve() for p in pathlib.Path('core/compile').glob('*.cpp')}
for tree in ('build', 'openyamm-studio/build'):
    seen = collections.Counter(pathlib.Path(e['file']).resolve() for e in json.load(open(f'{tree}/compile_commands.json')))
    bad = {str(s): seen[s] for s in sources if seen[s] > 1}
    print(tree, 'core sources compiled more than once:', bad or 'none')
EOF
rg -n '(game|engine)/[A-Za-z/]+\.cpp' openyamm-studio/CMakeLists.txt tools/CMakeLists.txt tests/CMakeLists.txt \
    | rg -f <(rg -o '(game|engine)/[A-Za-z/]+\.cpp' core/CMakeLists.txt)      # must print nothing
rg -n 'editor/' --glob '*.{cpp,h,txt,cmake,yml}' CMakeLists.txt cmake core engine game tests tools openyamm-studio/cli \
    openyamm-studio/core openyamm-studio/CMakeLists.txt .github                  # after deletion: nothing
```

Pass: "none" for both trees; the two searches print nothing.

### 4.7 Android and the other platforms

Android compiles the moved sources (its `main` links `openyamm_game`, `android/app/src/main/cpp/CMakeLists.txt:54`)
but never the editor (`android/app/build.gradle:96`, `OPENYAMM_BUILD_EDITOR=OFF`) or the compile library (tests
and tools are off). Build the release APK after step 2 and after the deletion step:
`android/build_release_apk.sh`, then the release test `android/test_release_apk.py` on the emulator as usual. Compare
the arm64 objects of the 44 files as in 4.3. No Vulkan build is involved. Windows, macOS and the Linux package
build in `.github/workflows/packages.yml` on the next push to `main` (or by `workflow_dispatch` with an empty
version on a branch); their sparse checkouts must already list `/core/` (3.4).

## 5. Steps

Each step is one change, small enough to review alone, checked before the next starts, and undone by reverting its
own files. Every step edits shared files that other sessions also change (`game/CMakeLists.txt`,
`tests/CMakeLists.txt` and `AGENTS.md` carry other sessions' unstaged edits today): targeted edits only, inventory
re-taken just before.

| # | Change | Check | Undo |
|---|---|---|---|
| 0 | S6 merged. Re-take the inventory (1.4) and update 1.1. Take the reference set (4.0) and the reference results of 4.1, 4.2, 4.4, 4.5 (twice) | the reference rebuilds are deterministic; record the known failures | nothing to undo |
| 0b | Prove the two outdoor routes already agree: reference editor against the current `oymap build-map` on all 42 packages (4.5's outdoor run with `new` = the current oymap), and the reference tool against current `oymap compile-indoor` on all 66 | identical, so repointing is separate from moving | none |
| 1 | Vendor cgltf v1.15 in `third_party/cgltf/` (`cmp` with `build/_deps/bgfx-src/3rdparty/cgltf/cgltf.h`); the studio uses it; licence line in `COPYRIGHT` | studio builds; `native_vs_wasm.sh` 22/22; studio's L4 bytes unchanged | revert the folder and `Deps.cmake` |
| 2 | `core/CMakeLists.txt` with `openyamm_core` over the 44 files at their paths; game tree and studio tree link it (3.2, 3.3), `editor/CMakeLists.txt` stops listing them; `packages.yml` sparse checkouts (3.4). CMake only: no source file changes | 4.3 (44 objects equal), 4.1, 4.2, 4.4, 4.6 (for the 44), the 22 L4 projects (4.5), Android APK (4.7) | revert the CMake files |
| 3 | Move the compile module: `git mv` the 8 editor files (and headers) to `core/compile/`, `LegacyCompileIndoor.cpp` out of the tool's main, `openyamm_core_compile`; update the includes in `tools/`, `tests/IndoorSourceGeometryCompilerTests.cpp`, `editor/` and 5 studio files; tools and tests as in 3.2. The `Editor` namespace stays (renaming it is a later, compile-only change) | 4.5 indoor (66, old tool against new tool and `oymap compile-indoor`), outdoor (42), L4 (22); 4.1 with the 23 compiler cases; the editor still builds and its `--headless-build-map` gives the same bytes | `git mv` back, revert CMake |
| 4 | Repoint the 18 outdoor callers (2.2) to `oymap build-map`; the dead Isle of Ashes call too, so no reference to the editor binary remains | 4.5 end to end; `rg 'openyamm-editor' level_generation tools` prints nothing | revert the 18 files |
| 5 | Documents of 2.4; `.github/workflows/studio.yml` paths; `link_closure.py`; `ImageAssetLoaderTests.cpp`'s PNG (3.5 item 1); tell the user about the local rebuild scripts (3.5 item 2) | 4.1; links in the changed documents resolve | revert |
| 6 | Delete `editor/` (`app/`, `viewport/`, `headless/`, `document/EditorSession.*`, `import/IndoorSourceGeometryImport.*`, `assets/editor_ux_work/`, `CMakeLists.txt`), `OPENYAMM_BUILD_EDITOR` and `add_subdirectory(editor)`, the two editor shaders and their `BgfxRuntime.cmake` lines, `tools/mm9_import_discovery/run_mm9_active_gate.sh`, `/.openyamm-editor.ini` in `.gitignore`, `res/editor_{1,2}.webp` | fresh configure of `build/` (the cached `OPENYAMM_BUILD_EDITOR=ON` then only warns), full build, 4.1, 4.2, 4.6 including the `editor/` search, Android APK (the shader list changed) | `git revert` of the deletion commit |
| 7 | Engine clean-up (EDITOR_RETIREMENT 6): the `assets_editor_dev` rule moves from `AssetFileSystem` into `core/compile` beside the outdoor build; remove `deriveEditorDevelopmentRoot`, `m_editorDevelopmentRoot`, `getEditorDevelopmentRoot()` and the folder creation; adjust `tests/AssetFileSystemTests.cpp:150-191` | 4.5 outdoor again, tables included; 4.1; a development start with no `assets_editor_dev/` does not create it; 4.4 | revert |
| 8 | Remove the tracked leftovers `assets_dev/worlds/mm8/maps/out01.{map,geometry,terrain}.yml` (EDITOR_RETIREMENT 8); mark S7 done in PLAN.md 12 and EDITOR_RETIREMENT.md | `rg 'out01.map.yml' assets_dev` readers: none | revert |

Not in S7 (separate changes, EDITOR_RETIREMENT 7): renaming `assets_editor_dev/` to `assets_mm9_import/` with its
~50 readers.

**S7b, the physical move (optional, after S7):** module by module into `core/io`, `core/format`, `core/scene`,
`core/tables`, `core/script`, `core/collision`, each with its data headers of 1.3, a scripted include rewrite
(`sed` over the 493 files that include the 44 headers, plus those that include the moved data headers), and the same
checks as step 2 (objects then differ only in the embedded file path: compare `objdump -d` output instead of
`cmp`). Before `core/collision` can move without including `game/`: **cut G1b**, `IndoorGeometryUtils.h` takes a
small mechanism-state view instead of `EventRuntimeState`, and `EventRuntime::calculateMechanismDistance` goes back to
`EventRuntime.cpp` (it is a member of a game class). G1b changes a per-frame collision path, so it is measured like
any game change (4.1, 4.2, 4.4 and an outdoor and indoor FPS check). Do S7b only in a window agreed with the
sessions working in `game/`.

## 6. Risks and how each is caught

| Risk | Caught by |
|---|---|
| A moved file compiles differently in its new target (flags, defines, an include path that finds another copy of a header, such as cgltf) | 4.3: 44 objects compared with `cmp`, desktop and Android |
| Android arm64 changes behaviour because the core is built with the studio's `-ffp-contract=off` | rule in 3.1 (no flags in `core/CMakeLists.txt`); 4.3 on the Android objects |
| `BX_CONFIG_DEBUG` differs between the core and the game | the core links `openyamm_bgfx` in the game tree; configure once with `-DOPENYAMM_BGFX_DEBUG=ON` and build |
| Duplicate or missing symbols from static libraries (a target that compiles its own copy and links the core) | 4.6; step 2 removes the copies from every list in the same change; full build of all targets |
| CI package jobs fail: their sparse checkouts lack `/core/` | 3.4 in the same change as step 2; check locally with a sparse worktree of the linux list (`git worktree add`, `git sparse-checkout set --no-cone <list>`, configure) |
| The compile outputs drift | 4.5 on all 66 indoor, 42 outdoor and 24 studio packages, against binaries copied before step 1 |
| The old route is not deterministic and hides or fakes a drift | the reference rebuild is run twice first (4.0) |
| A parity run writes into a real asset root's tables | hard-link copies named `assets_dev`; atomic replacement never writes through a link |
| A workflow still needs the editor after deletion (MM9 rebuild script, Hesper builder guide, Brackenford rebuild notes) | 3.5 and 2.4; the `rg` searches of 4.6 and step 4; the user is told about the local `output/` scripts |
| Outdoor callers fail because the studio is not built | the callers' READMEs; a missing binary fails at once with "No such file", not silently |
| S6 or another session adds a core source to a game list during S7 | inventory re-taken at step 0 and before step 2; 4.6 run at every step |
| A game unit test reads a file under `editor/` | found: `ImageAssetLoaderTests.cpp:106`, fixed in step 5 before the deletion; 4.1 after step 6 |
| Load time or memory changes on MM6–MM9 | 4.4 at steps 2, 6 and 7; with equal objects a change points to a busy machine |
| Removing the editor root from the engine changes where map rows land | the rule is kept in `core/compile` unchanged; 4.5's table comparison after step 7 |

## 7. Record (2026-11-15)

Work files and logs are in `output/s7/` and `output/s7_reference/` (git-ignored). Deviations from the plan:

- cgltf is bgfx's copy (`build/_deps/bgfx-src/3rdparty/cgltf`, "Version: 1.15" but newer than the v1.15 tag: 135
  diff lines), vendored byte-equal so the game's object is unchanged; the studio's fetch of the v1.15 tag is gone.
- The content job's sparse checkout (`packages.yml`, the one that builds the cooker) also configures the game tree, so
  five lists got `/core/` and `/third_party/cgltf/`, not four. A copy of the Linux list configures.
- `openyamm_core_compile` is `EXCLUDE_FROM_ALL`: the game and Android do not compile it.
- CI runs only the installation unit tests (`--source-file=...`), so the 23 compiler cases are compiled there but run
  locally (`--test-suite=indoor_source_compiler`).
- `ImageAssetLoaderTests.cpp` reads `assets_dev/engine/icons_x2/micon2.png` instead of the editor's 2.4 MB mockup.
- The moved files were moved with `mv`, not `git mv` (nothing staged): git shows them deleted and `core/compile/` new.
- Outdoor parity: 42 packages; the fixtures' and studies' stored fingerprints are older than today's scene fields, so
  the parity run drops them as the fixture scripts do. 33 build, 9 fail the same way in every route (Brackenford
  `lg01`: missing `pickup_event`; five playtest copies and the terrain lab: no source-backed BModels; Castleview's
  terrain study: an OBJ in a deleted `/tmp` folder; two Castleview studies: an invalid interactive face).
  Castleview and Brackenford were built against `assets_dev` (their `/tmp` stages do not exist).

Checks: the 44 core objects byte-equal to the reference (desktop 44/44; Android arm64 43/44 equal and
`CgltfImplementation` equal with debug info stripped, its DWARF names the vendored header's path); indoor 66/66,
outdoor 42/42 with the map tables, studio L4 22 + 2 examples identical to the reference at steps 1, 2, 3 and 7;
reference runs repeated twice identical; native against wasm 22/22; no core source compiled twice in either tree;
unit tests, release scenarios (12/12), MM9 scenarios and the game's suites with the reference's pass and fail lists;
load medians within the reference spread and peak memory within 1 % at step 2 (the controlled run; later game
binaries also carry other sessions' game edits, and Isle of Ashes then measured 1.6 % higher); end to end: Lich Lab
and the Sturmford region through their converters equal the installed maps, the MM8 land fixtures and Hesper `hes_out1`
through `oymap build-map` equal the editor's output. Android: the release native build
(`:app:externalNativeBuildRelease`, arm64) after steps 2 and 6, objects compared; the APK itself was not packaged
(it needs `android/repack_runtime_assets.sh` and the release keystore password) nor run on the emulator.

