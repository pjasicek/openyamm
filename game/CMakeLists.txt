include(Ffmpeg)
include(FetchContent)
openyamm_configure_ffmpeg()

FetchContent_GetProperties(imgui SOURCE_DIR OPENYAMM_IMGUI_SOURCE_DIR)
FetchContent_GetProperties(bgfx SOURCE_DIR OPENYAMM_BGFX_FETCH_SOURCE_DIR)

add_library(openyamm_game STATIC
    render/RuntimeShader.cpp
    render/CinematicGrading.cpp
    render/WaterRenderer.cpp
    render/ShieldDomeRenderer.cpp
    render/WeatherRenderer.cpp
    render/SkyPresets.cpp
    render/SkyState.cpp
    render/SkyRenderer.cpp
    app/ScreenManager.cpp
    app/GameInputSystem.cpp
    app/ProfilingControl.cpp
    arcomage/ArcomageAi.cpp
    arcomage/ArcomageLoader.cpp
    arcomage/ArcomageRules.cpp
    data/ActorNameResolver.cpp
    debug/DebugConsole.cpp
    debug/GameplayDebugTrace.cpp
    debug/GameImGuiBgfxRenderer.cpp
    debug/ScreenshotCaptureService.cpp
    debug/ScreenshotTour.cpp
    debug/MenuInputTour.cpp
    data/GameDataRepository.cpp
    app/GameSession.cpp
    audio/GameAudioSystem.cpp
    audio/MusicStream.cpp
    tables/ChestTable.cpp
    tables/AwardTable.cpp
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
    events/ScriptedEventTimer.cpp
    tables/FaceAnimationTable.cpp
    fx/ParticleRecipes.cpp
    fx/ProjectileEffectBindings.cpp
    fx/ProjectileModelBindings.cpp
    tables/ItemModelBindings.cpp
    fx/SpellAuraEffectBindings.cpp
    fx/EffectSystem.cpp
    fx/EffectRenderer.cpp
    fx/import/EffectDefinitionLoader.cpp
    fx/import/EffectResourceLibrary.cpp
    fx/ParticleRenderer.cpp
    fx/ParticleSystem.cpp
    fx/WorldFxRenderer.cpp
    fx/WorldFxRenderResources.cpp
    fx/WorldFxSystem.cpp
    gameplay/GameMechanics.cpp
    gameplay/GameplayActionController.cpp
    gameplay/GameplayWorldItemPolicy.cpp
    gameplay/SearchableLootPropRuntime.cpp
    gameplay/LootContainerRuntime.cpp
    gameplay/GameplayCombatController.cpp
    gameplay/GameplayController.cpp
    gameplay/CorpseLootRuntime.cpp
    gameplay/ChestRuntime.cpp
    gameplay/BountyHuntRuntime.cpp
    gameplay/ArenaRuntime.cpp
    gameplay/AwardRuntime.cpp
    gameplay/GameplayBolsterRuntime.cpp
    gameplay/ActorBehaviorCatalog.cpp
    gameplay/ActorBehaviorRuntime.cpp
    gameplay/GameplayActorAiSystem.cpp
    gameplay/GameplayActorHitFeedback.cpp
    gameplay/MeleeContactEffects.cpp
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
    gameplay/GameplayAlchemyBenchInputController.cpp
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
    gameplay/TravelRuntime.cpp
    pathfinding/ActorPathRuntime.cpp
    pathfinding/PathMap.cpp
    pathfinding/PathPlanner.cpp
    audio/HouseVideoPlayer.cpp
    content/ContentManifest.cpp
    content/ContentTableComposer.cpp
    items/InventoryItemUseRuntime.cpp
    items/AlchemyBenchRuntime.cpp
    items/InventoryItemMixingRuntime.cpp
    maps/IndoorSceneYml.cpp
    maps/MapItemSourceYml.cpp
    maps/MapPresentation.cpp
    maps/MapDeltaData.cpp
    mm9/Mm9MapTransition.cpp
    mm9/Mm9BarrelRuntime.cpp
    mm9/Mm9PrimaryStats.cpp
    mm9/Mm9TeacherSchedule.cpp
    mm9/Mm9TransportRoute.cpp
    mm9/Mm9PositionedTransitionRuntime.cpp
    mm9/Mm9RudeDialogue.cpp
    mm9/Mm9SkillTrainer.cpp
    mm9/Mm9QuestMarkers.cpp
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
    items/WorldItemShape.cpp
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
    indoor/IndoorLightReach.cpp
    indoor/IndoorPortalGraph.cpp
    indoor/IndoorPortalVisibility.cpp
    indoor/IndoorWorldRuntime.cpp
    maps/MapAssetLoader.cpp
    maps/DecorationModelPlacement.cpp
    maps/ActorModelManifest.cpp
    maps/DecorationModelManifest.cpp
    maps/DecorationModelSet.cpp
    maps/MapDecorationTextures.cpp
    maps/MapIdentity.cpp
    maps/MapRegistry.cpp
    tables/MapStats.cpp
    gameplay/MasteryTeacherDialog.cpp
    tables/MonsterProjectileTable.cpp
    tables/MonsterTable.cpp
    tables/MergedBaseTables.cpp
    tables/NpcDialogTable.cpp
    tables/ObjectTable.cpp
    render/SpriteAtlasCook.cpp
    render/SpriteAtlasCache.cpp
    render/ActorModelPreview.cpp
    render/NativeSpriteTextureCache.cpp
    render/SpriteAtlasMipmaps.cpp
    outdoor/OutdoorBillboardRenderer.cpp
    outdoor/OutdoorSpatialFxRuntime.cpp
    outdoor/OutdoorGameplayInputController.cpp
    outdoor/OutdoorInteractionController.cpp
    outdoor/OutdoorLightingRuntime.cpp
    outdoor/OutdoorLightingData.cpp
    outdoor/OutdoorMapData.cpp
    outdoor/OutdoorNavigationData.cpp
    outdoor/OutdoorRenderData.cpp
    outdoor/OutdoorMechanismRuntime.cpp
    outdoor/OutdoorPresentationController.cpp
    outdoor/TerrainBushSet.cpp
    outdoor/TerrainDecorationData.cpp
    outdoor/TerrainDecorationRenderer.cpp
    outdoor/OutdoorTerrainMaterials.cpp
    outdoor/OutdoorRenderer.cpp
    outdoor/OutdoorGeometryUtils.cpp
    outdoor/OutdoorMeadow.cpp
    outdoor/OutdoorMovementController.cpp
    outdoor/OutdoorMovementDriver.cpp
    outdoor/OutdoorPathfindingBuilder.cpp
    outdoor/OutdoorPartyRuntime.cpp
    outdoor/OutdoorWorldRuntime.cpp
    outdoor/WeatherAudio.cpp
    outdoor/WeatherModel.cpp
    outdoor/WeatherPresentation.cpp
    party/Party.cpp
    party/EventSpellBuffs.cpp
    party/LloydsBeaconRuntime.cpp
    party/PartySpellSystem.cpp
    items/PriceCalculator.cpp
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
    tables/LiquidTable.cpp
    tables/TextureFrameTable.cpp
    outdoor/OutdoorGameView.cpp
    outdoor/OutdoorDistantSea.cpp
    ui/GameplayDialogueRenderer.cpp
    ui/HouseShopLayout.cpp
    ui/EnemyHealthBarRenderer.cpp
    ui/GameplayHudRenderer.cpp
    ui/GameplayUiSkin.cpp
    ui/GameplayBuffHud.cpp
    ui/GameplayHudCommon.cpp
    ui/GameplayHudOverlaySupport.cpp
    ui/GameplayHudOverlayRenderer.cpp
    ui/GameplayDebugOverlayRenderer.cpp
    ui/GameplaySpellTargetingOverlayRenderer.cpp
    ui/GameplayUiRenderer.cpp
    gameplay/GameplaySpeechRules.cpp
    gameplay/PartyHostileAlert.cpp
    gameplay/GameplayScreenRuntime.cpp
    ui/GameplayAlchemyBenchRenderer.cpp
    ui/GameplayAlchemyBenchView.cpp
    ui/GameplayPartyOverlayRenderer.cpp
    ui/GameplayUiOverlayOrchestrator.cpp
    ui/GameplayUiRuntime.cpp
    ui/KeyboardScreenLayout.cpp
    ui/MenuScreenBase.cpp
    ui/GameplayUiController.cpp
    ui/UiLayoutManager.cpp
    ui/MenuSettingsModel.cpp
    ui/MenuDesignScreen.cpp
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
    app/ContentSetup.cpp
    app/GameUpdater.cpp
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
elseif (ANDROID OR WIN32 OR APPLE)
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
            SDL3::SDL3
    )

    target_include_directories(openyamm
        PRIVATE
            ${CMAKE_SOURCE_DIR}
    )

    target_compile_features(openyamm PRIVATE cxx_std_20)

    if (APPLE)
        target_sources(openyamm PRIVATE app/AppleBundlePaths.cpp)
        include(AppleBundle)
        openyamm_configure_apple_bundle(openyamm)
    endif()

    if (OPENYAMM_ENABLE_GPROF_SAMPLING)
        if (NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR NOT UNIX OR APPLE)
            message(FATAL_ERROR "OPENYAMM_ENABLE_GPROF_SAMPLING requires GNU C++ on Linux.")
        endif()

        target_link_options(openyamm
            PRIVATE
                -pg
                -no-pie
        )
    endif()

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

        # OpenYAMM.exe of a versioned installation (packaging/UPDATER_PLAN.md 9.1): standard library and Windows only.
        add_executable(openyamm_launcher WIN32
            launcher/WindowsLauncher.cpp
            ${CMAKE_SOURCE_DIR}/engine/update/AppInstallation.cpp
            "${CMAKE_CURRENT_BINARY_DIR}/openyamm.rc"
        )
        target_include_directories(openyamm_launcher PRIVATE ${CMAKE_SOURCE_DIR})
        target_compile_features(openyamm_launcher PRIVATE cxx_std_20)
        if (MINGW)
            target_link_options(openyamm_launcher PRIVATE -municode)
        endif()
        set_target_properties(openyamm_launcher
            PROPERTIES
                OUTPUT_NAME OpenYAMM
                RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/launcher"
        )
    elseif (UNIX AND NOT APPLE)
        # OpenYAMM of a versioned installation (packaging/UPDATER_PLAN.md 9.1): standard library only.
        add_executable(openyamm_launcher
            launcher/LinuxLauncher.cpp
            ${CMAKE_SOURCE_DIR}/engine/update/AppInstallation.cpp
        )
        target_include_directories(openyamm_launcher PRIVATE ${CMAKE_SOURCE_DIR})
        target_compile_features(openyamm_launcher PRIVATE cxx_std_20)
        set_target_properties(openyamm_launcher
            PROPERTIES
                OUTPUT_NAME OpenYAMM
                RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/launcher"
        )
    endif()

    if (UNIX AND NOT APPLE AND NOT OPENYAMM_STATIC_LIBSTDCXX)
        target_link_options(openyamm
            PRIVATE
                "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
        )
    endif()

    if (OPENYAMM_STATIC_LIBSTDCXX)
        # Release packages need only the system's C library: libstdc++ of the build's newer compiler is not on older
        # distributions (packaging/check_linux_binary.sh).
        target_link_options(openyamm PRIVATE -static-libstdc++ -static-libgcc)
        target_link_options(openyamm_launcher PRIVATE -static-libstdc++ -static-libgcc)
    endif()
endif()

# Host-side preparation shares the runtime format/filtering code, without requiring a graphics context.
if (NOT CMAKE_CROSSCOMPILING)
    add_executable(openyamm_sprite_atlas_cook EXCLUDE_FROM_ALL
        ../tools/cook_sprite_atlases_main.cpp
        ../tools/SpriteAtlasEncode.cpp
        ../tools/TextureBlockEncode.cpp
        render/SpriteAtlasCook.cpp
        render/SpriteAtlasMipmaps.cpp)
    # The ASTC encoder is compiled into openyamm_bgfx (bimg's astc-encoder); tools/TextureBlockEncode.cpp calls it.
    target_include_directories(openyamm_sprite_atlas_cook PRIVATE ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/astc-encoder/include)
    target_link_libraries(openyamm_sprite_atlas_cook PRIVATE openyamm_engine libzstd_static openyamm_atlas_encoders)
    add_executable(openyamm_model_texture_cook EXCLUDE_FROM_ALL
        ../tools/cook_model_textures_main.cpp
        ../tools/CookModelGeometry.cpp
        ../tools/TextureBlockEncode.cpp)
    target_include_directories(openyamm_model_texture_cook PRIVATE ${CMAKE_SOURCE_DIR}
        ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/astc-encoder/include ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty)
    target_link_libraries(openyamm_model_texture_cook PRIVATE openyamm_engine libzstd_static openyamm_atlas_encoders)
    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets_source/engine/sprites_new")
        add_custom_target(openyamm_cook_sprite_atlases
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/cook_sprite_atlases.py"
                --source "${CMAKE_SOURCE_DIR}/assets_source/engine/sprites_new"
                --output "${OPENYAMM_DEV_ASSETS_DIR}/engine/sprites_new"
                --profile desktop --cooker "$<TARGET_FILE:openyamm_sprite_atlas_cook>"
            DEPENDS openyamm_sprite_atlas_cook
            COMMENT "Preparing changed sprite atlas runtime pages"
            VERBATIM)
    endif()
    # Desktop asset cooks into assets_dev (openyamm_cook_assets): incremental, they redo only what changed (receipts
    # record each cook's COOK_REVISION/COOKER_REVISION, not the cooker binary) and run with every openyamm build unless
    # OPENYAMM_COOK_ON_BUILD is off. Android cooks only on demand: tools/cook_android.sh. The cooks need the
    # assets_source checkout; release checkouts package the committed cooked files.
    option(OPENYAMM_COOK_ON_BUILD "Run the desktop asset cooks (openyamm_cook_assets) with every openyamm build" ON)
    add_custom_target(openyamm_cook_assets COMMENT "Desktop asset cooks done")
    # World surface textures: the x4 sources in assets_source (tools/cook_surface_textures.py).
    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets_source" AND IS_DIRECTORY "${OPENYAMM_DEV_ASSETS_DIR}/worlds")
        add_custom_target(openyamm_cook_surface_textures
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/cook_surface_textures.py" --profile desktop
                --sources "${CMAKE_SOURCE_DIR}/assets_source" --output "${OPENYAMM_DEV_ASSETS_DIR}"
                --cooker "$<TARGET_FILE:openyamm_model_texture_cook>"
            DEPENDS openyamm_model_texture_cook
            COMMENT "Cooking changed world surface textures"
            VERBATIM)
        add_dependencies(openyamm_cook_assets openyamm_cook_surface_textures)
    endif()
    # 3D models (tools/cook_models.py): source GLBs in assets_source cook into assets_dev (geometry passes, compressed
    # textures).
    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets_source")
        add_custom_target(openyamm_cook_models
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/cook_models.py" --profile desktop
                --source "${CMAKE_SOURCE_DIR}/assets_source" --output "${OPENYAMM_DEV_ASSETS_DIR}"
                --cooker "$<TARGET_FILE:openyamm_model_texture_cook>"
            DEPENDS openyamm_model_texture_cook
            COMMENT "Cooking changed 3D models"
            VERBATIM)
        add_dependencies(openyamm_cook_assets openyamm_cook_models)
    endif()
    # Obsidian HUD art (sources in assets_source) and portrait face set atlases (tools/cook_ui_textures.py), cooked
    # into assets_dev for desktop.
    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets_source" AND IS_DIRECTORY "${OPENYAMM_DEV_ASSETS_DIR}/engine/icons_x2")
        add_custom_target(openyamm_cook_ui_textures
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/cook_ui_textures.py"
                --assets "${OPENYAMM_DEV_ASSETS_DIR}" --cooker "$<TARGET_FILE:openyamm_model_texture_cook>"
            DEPENDS openyamm_model_texture_cook
            COMMENT "Cooking changed HUD art"
            VERBATIM)
        add_dependencies(openyamm_cook_assets openyamm_cook_ui_textures)
    endif()
    # Enhanced sky textures (sources in assets_source, tools/cook_sky_textures.py), cooked into assets_dev for desktop.
    if (IS_DIRECTORY "${CMAKE_SOURCE_DIR}/assets_source/engine/rendering/sky")
        add_custom_target(openyamm_cook_sky_textures
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/cook_sky_textures.py" --profile desktop
                --assets "${OPENYAMM_DEV_ASSETS_DIR}" --cooker "$<TARGET_FILE:openyamm_model_texture_cook>"
            DEPENDS openyamm_model_texture_cook
            COMMENT "Cooking changed sky textures"
            VERBATIM)
        add_dependencies(openyamm_cook_assets openyamm_cook_sky_textures)
    endif()
    if (OPENYAMM_COOK_ON_BUILD AND TARGET openyamm)
        add_dependencies(openyamm openyamm_cook_assets)
    endif()
    if (IS_DIRECTORY "${OPENYAMM_DEV_ASSETS_DIR}/engine/sprites_new")
        add_custom_target(openyamm_verify_sprite_atlases
            COMMAND "$<TARGET_FILE:openyamm_sprite_atlas_cook>"
                --verify "${OPENYAMM_DEV_ASSETS_DIR}/engine/sprites_new" desktop
            DEPENDS openyamm_sprite_atlas_cook
            COMMENT "Validating prebuilt sprite atlas runtime pages"
            VERBATIM)
        if (TARGET openyamm)
            add_dependencies(openyamm openyamm_verify_sprite_atlases)
        endif()
    endif()
endif()

target_link_libraries(openyamm_game PRIVATE libzstd_static)
