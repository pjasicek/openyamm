include(FetchContent)

FetchContent_GetProperties(imgui SOURCE_DIR OPENYAMM_IMGUI_SOURCE_DIR)
FetchContent_GetProperties(bgfx SOURCE_DIR OPENYAMM_BGFX_FETCH_SOURCE_DIR)

add_executable(openyamm-editor
    app/main.cpp
    app/EditorApplication.cpp
    app/EditorMainWindow.cpp
    app/EditorImGuiBgfxRenderer.cpp
    document/EditorDocument.cpp
    document/OutdoorGeometryMetadata.cpp
    document/OutdoorMapPackageMetadata.cpp
    document/OutdoorTerrainMetadata.cpp
    document/EditorSession.cpp
    import/ObjModelImport.cpp
    headless/EditorHeadlessDiagnostics.cpp
    viewport/EditorOutdoorViewport.cpp
    ${CMAKE_SOURCE_DIR}/game/data/ActorNameResolver.cpp
    ${CMAKE_SOURCE_DIR}/game/SpawnPreview.cpp
    ${CMAKE_SOURCE_DIR}/game/indoor/IndoorGeometryUtils.cpp
    ${CMAKE_SOURCE_DIR}/game/indoor/IndoorMapData.cpp
    ${CMAKE_SOURCE_DIR}/game/outdoor/OutdoorMapData.cpp
    ${CMAKE_SOURCE_DIR}/game/outdoor/OutdoorGeometryUtils.cpp
    ${CMAKE_SOURCE_DIR}/game/events/ScriptedEventProgram.cpp
    ${CMAKE_SOURCE_DIR}/game/maps/IndoorSceneYml.cpp
    ${CMAKE_SOURCE_DIR}/game/maps/MapDeltaData.cpp
    ${CMAKE_SOURCE_DIR}/game/maps/OutdoorSceneYml.cpp
    ${CMAKE_SOURCE_DIR}/game/maps/TerrainTileData.cpp
    ${CMAKE_SOURCE_DIR}/tools/legacy_events/EvtProgram.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/ChestTable.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/HouseTable.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/ItemTable.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/MapStats.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/MonsterTable.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/ObjectTable.cpp
    ${CMAKE_SOURCE_DIR}/game/tables/SpriteTables.cpp
    ${CMAKE_SOURCE_DIR}/tools/legacy_events/StrTable.cpp
    ${OPENYAMM_IMGUI_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
)

target_include_directories(openyamm-editor
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

set_property(
    SOURCE app/EditorImGuiBgfxRenderer.cpp
    APPEND
    PROPERTY INCLUDE_DIRECTORIES
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/examples/common/imgui
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_compile_definitions(openyamm-editor
    PRIVATE
        OPENYAMM_BGFX_SHADER_DIR="${OPENYAMM_RUNTIME_SHADER_DIR}"
)

target_link_libraries(openyamm-editor
    PRIVATE
        openyamm_engine
        imgui::imgui
        yaml-cpp::yaml-cpp
)

target_compile_features(openyamm-editor PRIVATE cxx_std_20)
add_dependencies(openyamm-editor openyamm_runtime_shaders)

find_library(OPENYAMM_M_LIBRARY m)
if (OPENYAMM_M_LIBRARY)
    target_link_libraries(openyamm-editor PRIVATE "${OPENYAMM_M_LIBRARY}")
endif()

find_library(OPENYAMM_ATOMIC_LIBRARY atomic)
if (OPENYAMM_ATOMIC_LIBRARY)
    target_link_libraries(openyamm-editor PRIVATE "${OPENYAMM_ATOMIC_LIBRARY}")
endif()

if (UNIX AND NOT APPLE)
    target_link_options(openyamm-editor
        PRIVATE
            "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
    )
endif()
