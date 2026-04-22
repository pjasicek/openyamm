add_executable(openyamm_unit_tests
    UnitTestMain.cpp
    GameplayActorAiSystemTests.cpp
    GameplayProjectileServiceTests.cpp
    SpellbookUiLayoutTests.cpp
    TestGameStubs.cpp
    ../game/gameplay/GameplayActorAiSystem.cpp
    ../game/gameplay/GameplayActorService.cpp
    ../game/gameplay/GameplayProjectileService.cpp
    ../game/fx/ParticleRecipes.cpp
    ../game/fx/ParticleSystem.cpp
    ../game/ui/SpellbookUiLayout.cpp
    ../game/tables/MonsterTable.cpp
    ../game/tables/ObjectTable.cpp
    ../game/tables/SpellTable.cpp
    ../game/tables/SpriteTables.cpp
)

target_include_directories(openyamm_unit_tests
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${CMAKE_SOURCE_DIR}/third_party/doctest
        ${OPENYAMM_BGFX_SOURCE_DIR}/include
        ${OPENYAMM_BIMG_SOURCE_DIR}/include
        ${OPENYAMM_BX_SOURCE_DIR}/include
)

target_compile_features(openyamm_unit_tests PRIVATE cxx_std_20)

target_link_libraries(openyamm_unit_tests
    PRIVATE
        openyamm_bgfx
        SDL3::SDL3
        yaml-cpp::yaml-cpp
)

add_test(NAME openyamm_unit_tests COMMAND openyamm_unit_tests)
