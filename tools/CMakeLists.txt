add_executable(openyamm_event_asset_export
    event_asset_export_main.cpp
    EventIr.cpp
    EventIrLegacyImport.cpp
    LegacyLuaExport.cpp
    legacy_events/EvtProgram.cpp
    ../game/indoor/IndoorMapData.cpp
    ../game/maps/MapIdentity.cpp
    ../game/tables/HouseTable.cpp
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
FetchContent_GetProperties(imgui SOURCE_DIR OPENYAMM_IMGUI_SOURCE_DIR)

add_executable(mm9_compile_indoor_source
    mm9_compile_indoor_source_main.cpp
    ../editor/document/IndoorGeometryMetadata.cpp
    ../editor/import/IndoorSourceGeometryCompiler.cpp
    ../editor/import/ObjModelImport.cpp
    ../game/indoor/IndoorGeometryUtils.cpp
    ../game/indoor/IndoorMapData.cpp
    ../game/indoor/IndoorPortalGraph.cpp
    ../game/maps/MapDeltaData.cpp
)

target_include_directories(mm9_compile_indoor_source
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_link_libraries(mm9_compile_indoor_source
    PRIVATE
        openyamm_engine
        yaml-cpp::yaml-cpp
)

target_compile_features(mm9_compile_indoor_source PRIVATE cxx_std_20)

add_executable(mm9_dialogue_pipeline
    mm9_dialogue_pipeline_main.cpp
    Mm9RudeTranscode.cpp
)

target_include_directories(mm9_dialogue_pipeline
    PRIVATE
        ${CMAKE_SOURCE_DIR}
)

target_link_libraries(mm9_dialogue_pipeline
    PRIVATE
        openyamm_engine
        yaml-cpp::yaml-cpp
)

target_compile_features(mm9_dialogue_pipeline PRIVATE cxx_std_20)

add_executable(mm9_animated_model_probe
    mm9_animated_model_probe_main.cpp
    ../game/mm9/Mm9AnimatedModelResolver.cpp
    ../game/mm9/Mm9AnimatedModelSidecar.cpp
    ../game/render/AnimatedModelAsset.cpp
)

target_include_directories(mm9_animated_model_probe
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_link_libraries(mm9_animated_model_probe
    PRIVATE
        yaml-cpp::yaml-cpp
)

target_compile_features(mm9_animated_model_probe PRIVATE cxx_std_20)

add_executable(mm9_animated_model_render_smoke
    mm9_animated_model_render_smoke_main.cpp
    ../game/maps/MapIdentity.cpp
    ../game/maps/Mm9EventsYml.cpp
    ../game/maps/OutdoorSceneYml.cpp
    ../game/mm9/Mm9AnimatedActorBinding.cpp
    ../game/mm9/Mm9AnimatedActorVisual.cpp
    ../game/mm9/Mm9AnimatedModelResolver.cpp
    ../game/mm9/Mm9DtxTexture.cpp
    ../game/mm9/Mm9AnimatedModelSidecar.cpp
    ../game/mm9/Mm9ScriptedBillboardVisuals.cpp
    ../game/mm9/Mm9ScriptedObjectRuntime.cpp
    ../game/render/AnimatedModelAsset.cpp
    ../game/render/AnimatedModelRenderer.cpp
)

target_include_directories(mm9_animated_model_render_smoke
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_compile_definitions(mm9_animated_model_render_smoke
    PRIVATE
        OPENYAMM_BGFX_SHADER_DIR="${OPENYAMM_RUNTIME_SHADER_DIR}"
)

target_link_libraries(mm9_animated_model_render_smoke
    PRIVATE
        openyamm_engine
        yaml-cpp::yaml-cpp
)

target_compile_features(mm9_animated_model_render_smoke PRIVATE cxx_std_20)
add_dependencies(mm9_animated_model_render_smoke openyamm_runtime_shaders)

add_executable(mm9_animated_model_viewer
    mm9_animated_model_viewer_main.cpp
    ../game/debug/GameImGuiBgfxRenderer.cpp
    ../game/mm9/Mm9DtxTexture.cpp
    ../game/mm9/Mm9AnimatedModelSidecar.cpp
    ../game/render/AnimatedModelAsset.cpp
    ../game/render/AnimatedModelRenderer.cpp
    ../game/render/TextureFiltering.cpp
    ${OPENYAMM_IMGUI_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
)

target_include_directories(mm9_animated_model_viewer
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

set_property(
    SOURCE ../game/debug/GameImGuiBgfxRenderer.cpp
    APPEND
    PROPERTY INCLUDE_DIRECTORIES
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/examples/common/imgui
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

target_compile_definitions(mm9_animated_model_viewer
    PRIVATE
        OPENYAMM_BGFX_SHADER_DIR="${OPENYAMM_RUNTIME_SHADER_DIR}"
)

target_link_libraries(mm9_animated_model_viewer
    PRIVATE
        openyamm_engine
        imgui::imgui
        yaml-cpp::yaml-cpp
)

target_compile_features(mm9_animated_model_viewer PRIVATE cxx_std_20)
add_dependencies(mm9_animated_model_viewer openyamm_runtime_shaders)
