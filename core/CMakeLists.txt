# The shared core (devdocs/map_studio/S7_PLAN.md): the code the game, its tests and tools, and Map Studio share. One
# source list, compiled once per build tree.
#
#   openyamm_core          asset files, text, scripts, the map formats, scene files, tables, movement, collision and
#                          pathfinding: game and engine sources compiled where they stand
#   openyamm_core_compile  the indoor compiler and the outdoor build (core/compile/, moved from the old editor in S7)
#
# Whoever adds this folder sets OPENYAMM_CORE_LUA_TARGET and OPENYAMM_CORE_BX_TARGET: the game tree its Lua and
# openyamm_bgfx (which carries bx and BX_CONFIG_DEBUG), Map Studio oymap_lua and oymap_bx. No compile options here:
# the core is compiled with the flags of the tree that adds it, so the game's objects stay the game's (Android arm64
# keeps its contraction) and the studio keeps its -ffp-contract=off.
add_library(openyamm_core STATIC
    # Asset files, text and hashes.
    ../engine/AssetFileSystem.cpp
    ../engine/AssetPackIndex.cpp
    ../engine/AssetScaleTier.cpp
    ../engine/TextTable.cpp
    ../engine/ImageAssetPaths.cpp
    ../engine/render/CookedTextureHeader.cpp
    ../engine/models/CgltfImplementation.cpp
    ../engine/update/Sha256.cpp
    ../engine/Localization.cpp
    ../engine/TextCatalog.cpp
    # Map event scripts.
    ../engine/scripting/LuaStateOwner.cpp
    ../game/events/ScriptedEventProgram.cpp
    ../game/data/MapScriptSources.cpp
    # Map formats.
    ../game/outdoor/OutdoorMapData.cpp
    ../game/indoor/IndoorMapData.cpp
    ../game/maps/MapDeltaData.cpp
    ../game/maps/MapIdentity.cpp
    # Scene files.
    ../game/maps/OutdoorSceneYml.cpp
    ../game/maps/IndoorSceneYml.cpp
    ../game/maps/SceneOverlayOperations.cpp
    ../game/maps/SceneOverlayPaths.cpp
    ../game/maps/MapItemSourceYml.cpp
    ../game/maps/MechanismAudioYml.cpp
    ../game/maps/MistYml.cpp
    ../game/gameplay/CinematicLibrary.cpp
    ../game/indoor/IndoorWater.cpp
    ../game/indoor/IndoorDaylight.cpp
    ../game/render/SkyState.cpp
    # Tables.
    ../game/tables/SpriteTables.cpp
    ../game/tables/Mm9MonsterAi.cpp
    ../game/maps/MapRegistry.cpp
    ../game/maps/TerrainTileData.cpp
    # Movement, collision and pathfinding.
    ../game/indoor/IndoorGeometryUtils.cpp
    ../game/indoor/IndoorMovers.cpp
    ../game/indoor/IndoorPortalGraph.cpp
    ../game/indoor/IndoorSectorFaceGrid.cpp
    ../game/indoor/IndoorCollisionPrimitives.cpp
    ../game/indoor/IndoorMovementController.cpp
    ../game/indoor/IndoorPathfindingBuilder.cpp
    ../game/events/MechanismDistance.cpp
    ../game/outdoor/OutdoorGeometryUtils.cpp
    ../game/outdoor/OutdoorMovementController.cpp
    ../game/outdoor/OutdoorPathfindingBuilder.cpp
    ../game/pathfinding/PathMap.cpp
    ../game/pathfinding/PathPlanner.cpp
)

get_filename_component(openyammCoreRoot "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
target_include_directories(openyamm_core
    PUBLIC
        ${openyammCoreRoot}
        ${openyammCoreRoot}/third_party/cgltf
)
target_compile_features(openyamm_core PUBLIC cxx_std_20)
target_link_libraries(openyamm_core
    PUBLIC
        yaml-cpp::yaml-cpp
        physfs-static
        ${OPENYAMM_CORE_LUA_TARGET}
        ${OPENYAMM_CORE_BX_TARGET}
)

if (ANDROID)
    # engine/AssetFileSystem.cpp reads the APK's assets through SDL on Android.
    target_link_libraries(openyamm_core PRIVATE SDL3::SDL3)
endif()

# The indoor compiler (GLB and geometry.yml to .blv) and the outdoor build (map package to .odm): the tools, the unit
# tests and Map Studio link it; the game does not (nor is it built unless a target links it).
add_library(openyamm_core_compile STATIC EXCLUDE_FROM_ALL
    compile/IndoorGeometryMetadata.cpp
    compile/IndoorSourceGeometryCompiler.cpp
    compile/IndoorDerivedGeometry.cpp
    compile/ObjModelImport.cpp
    compile/EditorDocument.cpp
    compile/OutdoorGeometryMetadata.cpp
    compile/OutdoorMapPackageMetadata.cpp
    compile/OutdoorTerrainMetadata.cpp
    compile/LegacyCompileIndoor.cpp
)
target_link_libraries(openyamm_core_compile PUBLIC openyamm_core)
