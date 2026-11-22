add_executable(openyamm_event_asset_export
    event_asset_export_main.cpp
    EventIr.cpp
    EventIrLegacyImport.cpp
    LegacyLuaExport.cpp
    legacy_events/EvtProgram.cpp
    ../game/items/ItemEnchantTables.cpp
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

# The legacy indoor build (core/compile/LegacyCompileIndoor.cpp); its callers use this name.
add_executable(mm9_compile_indoor_source mm9_compile_indoor_source_main.cpp)
target_link_libraries(mm9_compile_indoor_source PRIVATE openyamm_core_compile)

# MM9 balance probe: engine-built reference parties against each chapter's monster packs
# (devdocs/mm9_rework/BALANCE_PLAN.md section 4). Read-only.
add_executable(openyamm_balance_probe balance_probe_main.cpp)
target_include_directories(openyamm_balance_probe PRIVATE
    ${CMAKE_SOURCE_DIR} ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty)
target_link_libraries(openyamm_balance_probe PRIVATE openyamm_game openyamm_engine yaml-cpp::yaml-cpp)

# Read-only native save inspection for generated-map reward and persistence reviews.
add_executable(openyamm_levelgen_inspect_save levelgen_inspect_save_main.cpp)
target_include_directories(openyamm_levelgen_inspect_save PRIVATE
    ${CMAKE_SOURCE_DIR} ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty)
target_link_libraries(openyamm_levelgen_inspect_save PRIVATE openyamm_game openyamm_engine yaml-cpp::yaml-cpp)

# The co-op lobby service (tools/lobby_server_main.cpp): the engine's rendezvous server alone, with the network
# library and nothing else of the game, so that it builds and runs on a small server.
add_executable(openyamm_lobby_server
    lobby_server_main.cpp
    ${CMAKE_SOURCE_DIR}/engine/net/ByteStream.cpp
    ${CMAKE_SOURCE_DIR}/engine/net/EnetTransport.cpp
    ${CMAKE_SOURCE_DIR}/engine/net/RendezvousProtocol.cpp
    ${CMAKE_SOURCE_DIR}/engine/net/RendezvousServer.cpp)
target_include_directories(openyamm_lobby_server PRIVATE ${CMAKE_SOURCE_DIR})
target_link_libraries(openyamm_lobby_server PRIVATE openyamm_enet)
