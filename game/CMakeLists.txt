add_executable(openyamm
    ChestTable.cpp
    EventIr.cpp
    EventRuntime.cpp
    EvtProgram.cpp
    MapDeltaData.cpp
    GameDataLoader.cpp
    HouseTable.cpp
    IndoorDebugRenderer.cpp
    IndoorMapData.cpp
    MapAssetLoader.cpp
    MapRegistry.cpp
    MapStats.cpp
    MonsterTable.cpp
    ObjectTable.cpp
    OutdoorMapData.cpp
    OutdoorGeometryUtils.cpp
    OutdoorMovementController.cpp
    OutdoorMovementDriver.cpp
    SpawnPreview.cpp
    SpriteTables.cpp
    StrTable.cpp
    TerrainDebugRenderer.cpp
    main.cpp
    GameApplication.cpp
)

target_include_directories(openyamm
    PRIVATE
        ${CMAKE_SOURCE_DIR}
)

target_compile_definitions(openyamm
    PRIVATE
        OPENYAMM_BGFX_SHADER_DIR="${OPENYAMM_RUNTIME_SHADER_DIR}"
)

target_link_libraries(openyamm
    PRIVATE
        openyamm_engine
)

target_compile_features(openyamm PRIVATE cxx_std_20)
add_dependencies(openyamm openyamm_runtime_shaders)

if (UNIX AND NOT APPLE)
    target_link_options(openyamm
        PRIVATE
            "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
    )
endif()
