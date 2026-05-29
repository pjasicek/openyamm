include(Ffmpeg)
include(FetchContent)
openyamm_configure_ffmpeg()

FetchContent_GetProperties(imgui SOURCE_DIR OPENYAMM_IMGUI_SOURCE_DIR)
FetchContent_GetProperties(bgfx SOURCE_DIR OPENYAMM_BGFX_FETCH_SOURCE_DIR)

add_library(openyamm_game STATIC
    app/ScreenManager.cpp
    app/GameInputSystem.cpp
    arcomage/ArcomageAi.cpp
    arcomage/ArcomageLoader.cpp
    arcomage/ArcomageRules.cpp
    data/ActorNameResolver.cpp
    debug/DebugConsole.cpp
    debug/GameplayDebugTrace.cpp
    debug/GameImGuiBgfxRenderer.cpp
    data/GameDataRepository.cpp
    app/GameSession.cpp
    audio/GameAudioSystem.cpp
    tables/ChestTable.cpp
    tables/JournalAutonoteTable.cpp
    tables/JournalHistoryTable.cpp
    tables/JournalQuestTable.cpp
    tables/CharacterInspectTable.cpp
    tables/CharacterDollTable.cpp
    tables/ClassMultiplierTable.cpp
    tables/ClassSkillTable.cpp
    events/EventDialogContent.cpp
    events/EventRuntime.cpp
    events/ScriptedEventProgram.cpp
    tables/FaceAnimationTable.cpp
    fx/ParticleRecipes.cpp
    fx/ParticleRenderer.cpp
    fx/ParticleSystem.cpp
    fx/WorldFxRenderer.cpp
    fx/WorldFxRenderResources.cpp
    fx/WorldFxSystem.cpp
    gameplay/GameMechanics.cpp
    gameplay/GameplayActionController.cpp
    gameplay/ArenaRuntime.cpp
    gameplay/GameplayCombatController.cpp
    gameplay/GameplayController.cpp
    gameplay/CorpseLootRuntime.cpp
    gameplay/ChestRuntime.cpp
    gameplay/BountyHuntRuntime.cpp
    gameplay/GameplayBolsterRuntime.cpp
    gameplay/GameplayActorAiSystem.cpp
    gameplay/GameplayActorService.cpp
    gameplay/GameplayDialogController.cpp
    gameplay/GameplayDialogUiFlow.cpp
    gameplay/GameplayFxService.cpp
    gameplay/GameplayHeldItemController.cpp
    gameplay/GameplayHudInputController.cpp
    gameplay/GameplayInputController.cpp
    gameplay/GameplayInteractionController.cpp
    gameplay/GameplayItemService.cpp
    gameplay/GameplayWorldItemInteraction.cpp
    gameplay/InteractiveDecorationRules.cpp
    gameplay/MonsterSpellSupport.cpp
    gameplay/MercenaryRecruitmentRuntime.cpp
    gameplay/GameplayOverlayInputController.cpp
    gameplay/GameplayPartyOverlayInputController.cpp
    gameplay/GameplayProjectileService.cpp
    gameplay/GameplayScreenController.cpp
    gameplay/GameplayScreenState.cpp
    gameplay/GameplaySaveLoadUiSupport.cpp
    gameplay/GameplaySpellActionController.cpp
    gameplay/GameplaySpellService.cpp
    gameplay/GenericActorDialog.cpp
    gameplay/HouseInteraction.cpp
    gameplay/HouseServiceRuntime.cpp
    gameplay/JournalQuestRuntime.cpp
    gameplay/NpcFollowerRuntime.cpp
    gameplay/ReputationRuntime.cpp
    gameplay/StealingRuntime.cpp
    gameplay/SavePreviewImage.cpp
    gameplay/StoryTextFormatter.cpp
    gameplay/TreasureRuntime.cpp
    gameplay/TurnBasedCombatRuntime.cpp
    pathfinding/ActorPathRuntime.cpp
    pathfinding/PathMap.cpp
    pathfinding/PathPlanner.cpp
    audio/HouseVideoPlayer.cpp
    content/ContentManifest.cpp
    items/InventoryItemUseRuntime.cpp
    items/InventoryItemMixingRuntime.cpp
    maps/IndoorSceneYml.cpp
    maps/MapDeltaData.cpp
    maps/Mm9EventsYml.cpp
    mm9/Mm9DialoguePackage.cpp
    mm9/Mm9JournalContent.cpp
    mm9/Mm9InteractionRouting.cpp
    mm9/Mm9DialogueRuntime.cpp
    mm9/Mm9DialogueUi.cpp
    mm9/Mm9AnimatedActorBinding.cpp
    mm9/Mm9AnimatedActorVisual.cpp
    mm9/Mm9AnimatedModelResolver.cpp
    mm9/Mm9AnimatedModelSidecar.cpp
    mm9/Mm9DtxTexture.cpp
    mm9/Mm9DatWorld.cpp
    mm9/Mm9DatPhysicsQuery.cpp
    mm9/Mm9DatCollisionWorld.cpp
    mm9/Mm9DatLevelRuntimeLoader.cpp
    mm9/Mm9DatPartyRuntime.cpp
    mm9/Mm9DatRuntimeDevEntry.cpp
    mm9/Mm9DatSceneRuntime.cpp
    mm9/Mm9DatWorldRenderer.cpp
    mm9/Mm9DatWorldRuntime.cpp
    mm9/Mm9SkyLayer.cpp
    mm9/Mm9ObjectLayer.cpp
    mm9/Mm9LightLayer.cpp
    mm9/Mm9SoundLayer.cpp
    mm9/Mm9SpawnLayer.cpp
    mm9/Mm9ServiceRuntime.cpp
    mm9/Mm9ScriptRuntime.cpp
    mm9/Mm9ScriptedObjectRuntime.cpp
    maps/OutdoorSceneYml.cpp
    maps/TerrainTileData.cpp
    data/GameDataLoader.cpp
    outdoor/HeadlessOutdoorDiagnostics.cpp
    tables/HouseTable.cpp
    tables/IconFrameTable.cpp
    items/ItemEnchantTables.cpp
    items/ItemEnchantRuntime.cpp
    items/ItemGenerator.cpp
    items/ItemRuntime.cpp
    tables/ItemTable.cpp
    indoor/IndoorRenderer.cpp
    indoor/IndoorGameView.cpp
    indoor/IndoorCollisionPrimitives.cpp
    indoor/IndoorGeometryUtils.cpp
    indoor/IndoorLightingRuntime.cpp
    indoor/IndoorMapData.cpp
    indoor/IndoorMovementController.cpp
    indoor/IndoorPathfindingBuilder.cpp
    indoor/IndoorPartyRuntime.cpp
    indoor/IndoorPortalGraph.cpp
    indoor/IndoorPortalVisibility.cpp
    indoor/IndoorWorldRuntime.cpp
    maps/MapAssetLoader.cpp
    maps/MapIdentity.cpp
    maps/MapRegistry.cpp
    tables/MapStats.cpp
    gameplay/MasteryTeacherDialog.cpp
    tables/MonsterProjectileTable.cpp
    tables/MonsterTable.cpp
    tables/MergedBaseTables.cpp
    tables/NpcDialogTable.cpp
    tables/ObjectTable.cpp
    outdoor/OutdoorBillboardRenderer.cpp
    outdoor/OutdoorSpatialFxRuntime.cpp
    outdoor/OutdoorGameplayInputController.cpp
    outdoor/OutdoorInteractionController.cpp
    outdoor/OutdoorLightingRuntime.cpp
    outdoor/OutdoorMapData.cpp
    outdoor/OutdoorPresentationController.cpp
    outdoor/OutdoorRenderer.cpp
    outdoor/OutdoorGeometryUtils.cpp
    outdoor/OutdoorMovementController.cpp
    outdoor/OutdoorMovementDriver.cpp
    outdoor/OutdoorPartyRuntime.cpp
    outdoor/OutdoorWorldRuntime.cpp
    party/Party.cpp
    party/EventSpellBuffs.cpp
    party/LloydsBeaconRuntime.cpp
    party/PartySpellSystem.cpp
    items/PriceCalculator.cpp
    render/AnimatedModelAsset.cpp
    render/AnimatedModelRenderer.cpp
    tables/ReadableScrollTable.cpp
    render/TextureFiltering.cpp
    tables/PortraitFxEventTable.cpp
    tables/PotionMixingTable.cpp
    tables/PotionNoteTable.cpp
    tables/PortraitEnums.cpp
    tables/PortraitFrameTable.cpp
    tables/RaceStartingStatsTable.cpp
    tables/RosterTable.cpp
    maps/SaveGame.cpp
    scenario/ScenarioHeadlessCommand.cpp
    scenario/ScenarioRuntimeDriver.cpp
    scenario/ScenarioRunner.cpp
    scenario/ScenarioYamlLoader.cpp
    audio/SoundCatalog.cpp
    SpawnPreview.cpp
    party/SkillData.cpp
    tables/SpeechReactionTable.cpp
    ui/SpellbookUiLayout.cpp
    party/SpellSchool.cpp
    tables/SpellTable.cpp
    tables/SpellFxTable.cpp
    tables/TransitionTable.cpp
    tables/SpriteTables.cpp
    tables/SurfaceMaterialTable.cpp
    tables/TextureFrameTable.cpp
    outdoor/OutdoorGameView.cpp
    ui/GameplayDialogueRenderer.cpp
    ui/GameplayHudRenderer.cpp
    ui/GameplayHudCommon.cpp
    ui/GameplayHudOverlaySupport.cpp
    ui/GameplayHudOverlayRenderer.cpp
    ui/GameplayDebugOverlayRenderer.cpp
    ui/GameplaySpellTargetingOverlayRenderer.cpp
    ui/GameplayUiRenderer.cpp
    gameplay/GameplaySpeechRules.cpp
    gameplay/GameplayScreenRuntime.cpp
    ui/GameplayPartyOverlayRenderer.cpp
    ui/GameplayUiOverlayOrchestrator.cpp
    ui/GameplayUiRuntime.cpp
    ui/KeyboardScreenLayout.cpp
    ui/MenuScreenBase.cpp
    ui/GameplayUiController.cpp
    ui/UiLayoutManager.cpp
    ui/screens/MainMenuScreen.cpp
    ui/screens/ArcomageScreen.cpp
    ui/screens/CutsceneVideoScreen.cpp
    ui/screens/LoadGameScreen.cpp
    ui/screens/LoadingOverlayScreen.cpp
    ui/screens/NewGameScreen.cpp
    ui/screens/WinGameScreen.cpp
    scene/IndoorSceneRuntime.cpp
    scene/OutdoorSceneRuntime.cpp
    app/main.cpp
    app/GameApplication.cpp
    app/KeyboardBindings.cpp
    app/GameSettings.cpp
    ${OPENYAMM_IMGUI_SOURCE_DIR}/backends/imgui_impl_sdl3.cpp
)

target_include_directories(openyamm_game
    PRIVATE
        ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

set_property(
    SOURCE debug/GameImGuiBgfxRenderer.cpp
    APPEND
    PROPERTY INCLUDE_DIRECTORIES
        ${OPENYAMM_IMGUI_SOURCE_DIR}
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/examples/common/imgui
        ${OPENYAMM_BGFX_FETCH_SOURCE_DIR}/3rdparty
)

if (NOT OPENYAMM_RUNTIME_SHADER_PATH STREQUAL "")
    set(openyammBgfxShaderDir "${OPENYAMM_RUNTIME_SHADER_PATH}")
elseif (ANDROID OR WIN32)
    set(openyammBgfxShaderDir "runtime/shaders")
else()
    set(openyammBgfxShaderDir "${OPENYAMM_RUNTIME_SHADER_DIR}")
endif()

target_compile_definitions(openyamm_game
    PRIVATE
        OPENYAMM_NO_DESKTOP_MAIN
        OPENYAMM_BGFX_SHADER_DIR="${openyammBgfxShaderDir}"
)

target_link_libraries(openyamm_game
    PRIVATE
        openyamm_engine
        imgui::imgui
        Threads::Threads
        yaml-cpp::yaml-cpp
)

target_compile_features(openyamm_game PRIVATE cxx_std_20)
add_dependencies(openyamm_game openyamm_runtime_shaders)
openyamm_target_link_ffmpeg(openyamm_game)

find_library(OPENYAMM_M_LIBRARY m)
if (OPENYAMM_M_LIBRARY)
    target_link_libraries(openyamm_game PRIVATE "${OPENYAMM_M_LIBRARY}")
endif()

find_library(OPENYAMM_ATOMIC_LIBRARY atomic)
if (OPENYAMM_ATOMIC_LIBRARY)
    target_link_libraries(openyamm_game PRIVATE "${OPENYAMM_ATOMIC_LIBRARY}")
endif()

if (OPENYAMM_BUILD_DESKTOP_EXECUTABLE)
    add_executable(openyamm
        app/DesktopMain.cpp
    )

    target_link_libraries(openyamm
        PRIVATE
            openyamm_game
    )

    target_include_directories(openyamm
        PRIVATE
            ${CMAKE_SOURCE_DIR}
    )

    target_compile_features(openyamm PRIVATE cxx_std_20)

    if (WIN32)
        file(TO_CMAKE_PATH "${CMAKE_SOURCE_DIR}/packaging/windows/openyamm.ico" openyammWindowsIconPath)
        configure_file(
            "${CMAKE_SOURCE_DIR}/packaging/windows/openyamm.rc.in"
            "${CMAKE_CURRENT_BINARY_DIR}/openyamm.rc"
            @ONLY
        )
        target_sources(openyamm
            PRIVATE
                "${CMAKE_CURRENT_BINARY_DIR}/openyamm.rc"
        )
        set_target_properties(openyamm
            PROPERTIES
                WIN32_EXECUTABLE "$<OR:$<CONFIG:Release>,$<CONFIG:MinSizeRel>>"
        )
    endif()

    if (UNIX AND NOT APPLE)
        target_link_options(openyamm
            PRIVATE
                "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
        )
    endif()

    install(TARGETS openyamm
        RUNTIME DESTINATION bin
    )

    install(DIRECTORY "${OPENYAMM_RUNTIME_SHADER_DIR}/"
        DESTINATION "share/openyamm/runtime/shaders"
    )

    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets")
        install(DIRECTORY "${CMAKE_SOURCE_DIR}/assets/"
            DESTINATION "share/openyamm/assets"
            FILES_MATCHING
                PATTERN "*.zip"
        )
    endif()
endif()
