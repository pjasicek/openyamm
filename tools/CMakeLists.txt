add_executable(openyamm_event_asset_export
    event_asset_export_main.cpp
    EventIr.cpp
    EventIrLegacyImport.cpp
    LegacyLuaExport.cpp
    legacy_events/EvtProgram.cpp
    ../game/indoor/IndoorMapData.cpp
    ../game/items/ItemEnchantTables.cpp
    ../game/maps/MapIdentity.cpp
    ../game/party/SkillData.cpp
    ../game/tables/HouseTable.cpp
    ../game/tables/ItemModelBindings.cpp
    ../game/tables/ItemTable.cpp
    ../game/tables/MapStats.cpp
    ../game/tables/MergedBaseTables.cpp
    legacy_events/StrTable.cpp
)

target_include_directories(openyamm_event_asset_export
    PRIVATE
        ${CMAKE_SOURCE_DIR}
)

target_link_libraries(openyamm_event_asset_export
    PRIVATE
        openyamm_engine
        yaml-cpp::yaml-cpp
)

target_compile_features(openyamm_event_asset_export PRIVATE cxx_std_20)

FetchContent_GetProperties(bgfx SOURCE_DIR OPENYAMM_BGFX_FETCH_SOURCE_DIR)

add_library(openyamm_indoor_source STATIC
    ../editor/document/IndoorGeometryMetadata.cpp
    ../editor/import/IndoorSourceGeometryCompiler.cpp
    ../editor/import/IndoorDerivedGeometry.cpp
    ../editor/import/ObjModelImport.cpp
    ../game/indoor/IndoorGeometryUtils.cpp
    ../game/indoor/IndoorMovers.cpp
    ../game/indoor/IndoorMapData.cpp
    ../game/indoor/IndoorPortalGraph.cpp
    ../game/indoor/IndoorSectorFaceGrid.cpp
    ../game/maps/MapDeltaData.cpp
)

target_include_directories(openyamm_indoor_source
    PUBLIC
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_link_libraries(openyamm_indoor_source
    PUBLIC
        openyamm_engine
        yaml-cpp::yaml-cpp
)

target_compile_features(openyamm_indoor_source PUBLIC cxx_std_20)

add_executable(mm9_compile_indoor_source mm9_compile_indoor_source_main.cpp)
target_link_libraries(mm9_compile_indoor_source PRIVATE openyamm_indoor_source)

# Read-only native save inspection for generated-map reward and persistence reviews.
add_executable(openyamm_levelgen_inspect_save levelgen_inspect_save_main.cpp)
target_include_directories(openyamm_levelgen_inspect_save PRIVATE
    ${CMAKE_SOURCE_DIR} ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty)
target_link_libraries(openyamm_levelgen_inspect_save PRIVATE openyamm_game openyamm_engine yaml-cpp::yaml-cpp)

if (OPENYAMM_BUILD_TESTS)
    add_executable(openyamm_indoor_source_tests
        ../tests/UnitTestMain.cpp
        ../tests/IndoorSourceGeometryCompilerTests.cpp
    )
    target_include_directories(openyamm_indoor_source_tests PRIVATE ${CMAKE_SOURCE_DIR}/third_party/doctest)
    target_link_libraries(openyamm_indoor_source_tests PRIVATE openyamm_indoor_source)
    add_test(NAME openyamm_indoor_source_tests COMMAND openyamm_indoor_source_tests)
endif()
