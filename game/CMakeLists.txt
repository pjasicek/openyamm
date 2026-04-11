include(Ffmpeg)
openyamm_configure_ffmpeg()

add_executable(openyamm
    app/ScreenManager.cpp
    arcomage/ArcomageAi.cpp
    arcomage/ArcomageLoader.cpp
    arcomage/ArcomageRules.cpp
    data/ActorNameResolver.cpp
    app/GameSession.cpp
    audio/GameAudioSystem.cpp
    tables/ChestTable.cpp
    tables/JournalAutonoteTable.cpp
    tables/JournalHistoryTable.cpp
    tables/JournalQuestTable.cpp
    tables/CharacterInspectTable.cpp
    tables/CharacterDollTable.cpp
    tables/ClassSkillTable.cpp
    events/EventDialogContent.cpp
    events/EventIr.cpp
    events/EventRuntime.cpp
    events/EvtProgram.cpp
    tables/FaceAnimationTable.cpp
    gameplay/GameMechanics.cpp
    gameplay/GameplayController.cpp
    gameplay/GameplayDialogController.cpp
    gameplay/GameplayOverlayInputController.cpp
    gameplay/GameplayPartyOverlayInputController.cpp
    gameplay/GenericActorDialog.cpp
    gameplay/HouseInteraction.cpp
    gameplay/HouseServiceRuntime.cpp
    gameplay/StoryTextFormatter.cpp
    audio/HouseVideoPlayer.cpp
    items/InventoryItemUseRuntime.cpp
    maps/MapDeltaData.cpp
    data/GameDataLoader.cpp
    outdoor/HeadlessOutdoorDiagnostics.cpp
    tables/HouseTable.cpp
    tables/IconFrameTable.cpp
    items/ItemEquipPosTable.cpp
    items/ItemEnchantTables.cpp
    items/ItemEnchantRuntime.cpp
    items/ItemGenerator.cpp
    items/ItemRuntime.cpp
    tables/ItemTable.cpp
    indoor/IndoorDebugRenderer.cpp
    indoor/IndoorMapData.cpp
    maps/MapAssetLoader.cpp
    maps/MapRegistry.cpp
    tables/MapStats.cpp
    gameplay/MasteryTeacherDialog.cpp
    tables/MonsterProjectileTable.cpp
    tables/MonsterTable.cpp
    tables/NpcDialogTable.cpp
    tables/ObjectTable.cpp
    outdoor/OutdoorBillboardRenderer.cpp
    outdoor/OutdoorGameplayInputController.cpp
    outdoor/OutdoorInteractionController.cpp
    outdoor/OutdoorMapData.cpp
    outdoor/OutdoorPresentationController.cpp
    outdoor/OutdoorRenderer.cpp
    outdoor/OutdoorGeometryUtils.cpp
    outdoor/OutdoorMovementController.cpp
    outdoor/OutdoorMovementDriver.cpp
    outdoor/OutdoorPartyRuntime.cpp
    outdoor/OutdoorWorldRuntime.cpp
    party/Party.cpp
    party/PartySpellSystem.cpp
    items/PriceCalculator.cpp
    tables/ReadableScrollTable.cpp
    tables/PortraitFxEventTable.cpp
    tables/PortraitEnums.cpp
    tables/PortraitFrameTable.cpp
    tables/RaceStartingStatsTable.cpp
    tables/RosterTable.cpp
    maps/SaveGame.cpp
    audio/SoundCatalog.cpp
    SpawnPreview.cpp
    party/SkillData.cpp
    tables/SpeechReactionTable.cpp
    ui/SpellbookUiLayout.cpp
    party/SpellSchool.cpp
    tables/SpellTable.cpp
    tables/SpellFxTable.cpp
    tables/SpriteTables.cpp
    tables/StrTable.cpp
    tables/SurfaceMaterialTable.cpp
    tables/TextureFrameTable.cpp
    outdoor/OutdoorGameView.cpp
    ui/GameplayDialogueRenderer.cpp
    ui/GameplayHudRenderer.cpp
    ui/GameplayHudOverlayRenderer.cpp
    ui/GameplayOverlayContext.cpp
    ui/GameplayPartyOverlayRenderer.cpp
    ui/HudUiService.cpp
    ui/MenuScreenBase.cpp
    ui/GameplayUiController.cpp
    ui/UiLayoutManager.cpp
    ui/screens/MainMenuScreen.cpp
    ui/screens/ArcomageScreen.cpp
    ui/screens/LoadGameScreen.cpp
    ui/screens/LoadingOverlayScreen.cpp
    ui/screens/NewGameScreen.cpp
    scene/IndoorSceneRuntime.cpp
    scene/OutdoorSceneRuntime.cpp
    app/main.cpp
    app/GameApplication.cpp
    app/GameSettings.cpp
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
        Threads::Threads
        yaml-cpp::yaml-cpp
)

target_compile_features(openyamm PRIVATE cxx_std_20)
add_dependencies(openyamm openyamm_runtime_shaders)
openyamm_target_link_ffmpeg(openyamm)

find_library(OPENYAMM_M_LIBRARY m)
if (OPENYAMM_M_LIBRARY)
    target_link_libraries(openyamm PRIVATE "${OPENYAMM_M_LIBRARY}")
endif()

find_library(OPENYAMM_ATOMIC_LIBRARY atomic)
if (OPENYAMM_ATOMIC_LIBRARY)
    target_link_libraries(openyamm PRIVATE "${OPENYAMM_ATOMIC_LIBRARY}")
endif()

if (UNIX AND NOT APPLE)
    target_link_options(openyamm
        PRIVATE
            "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
    )
endif()
