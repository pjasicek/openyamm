add_executable(openyamm_event_asset_export
    event_asset_export_main.cpp
    EventIr.cpp
    EventIrLegacyImport.cpp
    LegacyLuaExport.cpp
    legacy_events/EvtProgram.cpp
    ../game/tables/HouseTable.cpp
    ../game/tables/MapStats.cpp
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
