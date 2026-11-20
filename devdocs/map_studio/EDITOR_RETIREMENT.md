# Retiring `editor/`

**Done in S7 (2026-11-15, [S7_PLAN.md](S7_PLAN.md)).** The indoor compiler and the outdoor build live in
`core/compile/` (library `openyamm_core_compile`); `mm9_compile_indoor_source` keeps its name and arguments; the
outdoor callers run `openyamm-studio/build/oymap build-map`; the `assets_editor_dev` rule moved from the engine into
`core/compile/EditorDocument.cpp`; `editor/` is deleted. The rest of this page is the plan as written.

The desktop editor (`editor/`, 56 681 lines: ImGui, bgfx and SDL) is replaced by Map Studio. Most of it can be
deleted, but two parts are production build steps today and move into the core first. This happens in the last
milestone (S7 in [PLAN.md](PLAN.md)), after the studio is complete in `openyamm-studio/`; until then nothing here
changes. Inventory taken 2026-11-12; re-check it before starting.

## What still depends on it

- **The indoor compiler.** `tools/CMakeLists.txt:34-58` builds the library `openyamm_indoor_source` from
  `editor/document/IndoorGeometryMetadata.cpp`, `editor/import/IndoorSourceGeometryCompiler.cpp`,
  `IndoorDerivedGeometry.cpp` and `ObjModelImport.cpp`; `mm9_compile_indoor_source` (`tools/CMakeLists.txt:60-61`,
  `tools/mm9_compile_indoor_source_main.cpp`) and `tests/IndoorSourceGeometryCompilerTests.cpp` link it.
  Callers: `tools/mm9_import_discovery/{regenerate_mm9_maps.sh, generate_mm9_maps_from_manifest.py,
  transcode_mm9_dat_to_blv.py}`, `level_generation/projects/mm9r_common/dungeon/{build.py, package.py}` (used by all
  46 `mm9r_*` projects), `hesper_stage/{blv_build.py, blv_kit.py}`, `hesper_undervault/build_undervault.py`,
  `brackenford_greywatch/build_greywatch.py`, `mm9r_anskramkeep/legacy_converter/convert.py`.
- **The outdoor build.** `openyamm-editor --headless-build-map` is called by `hesper_out1..4/build_out*.py`,
  `mm9r_isleofashes/convert.py`, `brackenford_greywatch/{build_brackenford, verify_outdoor_source}.py`, the three
  `mm5_castleview_kalindra` builders, and the terrain fixtures under `level_generation/terrain/mm6_*`, `mm7`, `mm8`.
- **Shaders.** `cmake/BgfxRuntime.cmake:700-706, 795-796` compiles `vs_/fs_editor_preview_material`.
- **`assets_editor_dev/`** (git-ignored, 4 GB locally). `engine/AssetFileSystem.cpp:186-194` derives it and
  `:636-661` creates it on every development start; nothing mounts it. Its `worlds/mm9/maps` holds the old MM9 import
  that current converters read (`mm9r_isleofashes/convert.py`, `generate_mm9_events.py`, about 15
  `level_generation/props/mm9_*_claude` scripts); `hesper_stage/stage.py` names its staging root after it;
  `tests/WorldMissileTests.cpp:253` reads `output/hesper_stage/assets_editor_dev`.
- **Docs.** `README.md` (editor build and screenshots), `AGENTS.md` (subsystem list), `level_generation/PIPELINE_STATUS.md`,
  `tools/PERF_PROFILING.md`, `tools/VULKAN_DLSS_TEST.md`, `design/kreegan_world/WORK_PACKAGES/BUILDER_GUIDE.md`,
  `devdocs/mm9_rework/*`, about ten project READMEs and `mm9r_common/DUNGEON_PLAYBOOK.md`.
- **Already broken:** `tools/mm9_import_discovery/run_mm9_active_gate.sh:119-133` calls editor switches that no longer
  exist.

Release packaging and Android do not build the editor (`.github/workflows/packages.yml` passes
`-DOPENYAMM_BUILD_EDITOR=OFF -DOPENYAMM_BUILD_TOOLS=OFF`).

## Order

1. **Move the indoor compiler** (`IndoorGeometryMetadata`, `ObjModelImport`, `IndoorSourceGeometryCompiler`,
   `IndoorDerivedGeometry`) into `core/compile`. Vendor or fetch cgltf so the core does not reach into bgfx's
   `3rdparty` folder. Repoint `tools/CMakeLists.txt` and the test. Keep `mm9_compile_indoor_source` with the same
   name and arguments so no caller changes. Run the compiler tests in CI.
2. **Move the outdoor build** out of `editor/document/EditorDocument.cpp` (`buildImportedBModel` :1105,
   `buildOutdoorGeometryFromSourcePackage` :1273, `compileOutdoorGeometryBytes` :1392, the scene serialisers
   :4586/:4836/:4963, the `map_stats`/`map_navigation` row writers :1862-2041) and the outdoor metadata files into
   `core/compile` and `core/scene`. Ship `oymap build-map` with the editor's `--asset-root` and `--world` options.
3. **Prove parity.** Rebuild every BLV and ODM project through the new commands and compare with the old outputs
   byte for byte.
4. **Repoint the 19 callers** of `build/editor/openyamm-editor` to `oymap build-map`.
5. **Delete:** `editor/app/`, `editor/viewport/`, `editor/headless/`, `editor/document/EditorSession.*`,
   `EditorDocument.*` (after step 2), `IndoorSourceGeometryImport.*` (port later if the studio wants mesh-to-metadata
   seeding), `editor/assets/editor_ux_work/`, the editor shaders and their `BgfxRuntime.cmake` entries,
   `OPENYAMM_BUILD_EDITOR` and the root `add_subdirectory(editor)`, `run_mm9_active_gate.sh`, `/.openyamm-editor.ini`
   in `.gitignore`, the README editor section and `res/editor_*.webp`.
6. **Engine clean-up:** remove `deriveEditorDevelopmentRoot`, `m_editorDevelopmentRoot`,
   `getEditorDevelopmentRoot()` and the folder creation from `AssetFileSystem`; adjust
   `tests/AssetFileSystemTests.cpp:150-191`.
7. **`assets_editor_dev/` stays for now** as the MM9 import archive. Rename it (for example `assets_mm9_import/`)
   in a separate change that updates its ~50 readers, `hesper_stage`'s staging name and `WorldMissileTests.cpp:253`.
8. **Remove the unused tracked leftovers** `assets_dev/worlds/mm8/maps/out01.{map,geometry,terrain}.yml`.
   Keep the sidecars under `level_generation/`: they are compile inputs the core still reads.
9. **Docs:** add `core/` and `studio/` to the AGENTS.md subsystem list and drop `editor/`; update the other documents
   listed above.

The game, Android and release packaging are unaffected at every step.
