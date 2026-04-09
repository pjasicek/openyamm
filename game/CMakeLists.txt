if (NOT DEFINED OPENYAMM_FFMPEG_SOURCE_DIR OR OPENYAMM_FFMPEG_SOURCE_DIR STREQUAL "")
    set(OPENYAMM_FFMPEG_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-src")
endif()

set(OPENYAMM_FFMPEG_BUILD_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-build")
set(OPENYAMM_FFMPEG_INSTALL_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-install")
set(OPENYAMM_FFMPEG_INCLUDE_DIR "${OPENYAMM_FFMPEG_INSTALL_DIR}/include")
set(OPENYAMM_FFMPEG_LIBAVFORMAT "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavformat.a")
set(OPENYAMM_FFMPEG_LIBAVCODEC "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavcodec.a")
set(OPENYAMM_FFMPEG_LIBSWRESAMPLE "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libswresample.a")
set(OPENYAMM_FFMPEG_LIBSWSCALE "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libswscale.a")
set(OPENYAMM_FFMPEG_LIBAVUTIL "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavutil.a")

add_custom_command(
    OUTPUT
        "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
        "${OPENYAMM_FFMPEG_LIBAVCODEC}"
        "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
        "${OPENYAMM_FFMPEG_LIBSWSCALE}"
        "${OPENYAMM_FFMPEG_LIBAVUTIL}"
    COMMAND ${CMAKE_COMMAND} -E make_directory "${OPENYAMM_FFMPEG_BUILD_DIR}"
    COMMAND bash "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
        --prefix=${OPENYAMM_FFMPEG_INSTALL_DIR}
        --disable-programs
        --disable-doc
        --disable-network
        --disable-autodetect
        --disable-everything
        --disable-asm
        --disable-avdevice
        --disable-avfilter
        --enable-static
        --disable-shared
        --enable-avcodec
        --enable-avformat
        --enable-avutil
        --enable-swresample
        --enable-swscale
        --enable-protocol=file
        --enable-demuxer=ogg
        --enable-demuxer=mp3
        --enable-decoder=theora
        --enable-decoder=vorbis
        --enable-decoder=mp3
        --enable-decoder=mp3float
        --enable-parser=vorbis
        --enable-parser=mpegaudio
    COMMAND ${CMAKE_MAKE_PROGRAM} -j4
    COMMAND ${CMAKE_MAKE_PROGRAM} install
    WORKING_DIRECTORY "${OPENYAMM_FFMPEG_BUILD_DIR}"
    DEPENDS "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
    COMMENT "Building bundled FFmpeg static libraries for house video playback"
    VERBATIM
)

add_custom_target(openyamm_ffmpeg_build
    DEPENDS
        "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
        "${OPENYAMM_FFMPEG_LIBAVCODEC}"
        "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
        "${OPENYAMM_FFMPEG_LIBSWSCALE}"
        "${OPENYAMM_FFMPEG_LIBAVUTIL}"
)

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
    ui/screens/LoadMenuScreen.cpp
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
        "${OPENYAMM_FFMPEG_INCLUDE_DIR}"
)

target_compile_definitions(openyamm
    PRIVATE
        OPENYAMM_BGFX_SHADER_DIR="${OPENYAMM_RUNTIME_SHADER_DIR}"
)

target_link_libraries(openyamm
    PRIVATE
        openyamm_engine
        "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
        "${OPENYAMM_FFMPEG_LIBAVCODEC}"
        "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
        "${OPENYAMM_FFMPEG_LIBSWSCALE}"
        "${OPENYAMM_FFMPEG_LIBAVUTIL}"
        Threads::Threads
        yaml-cpp::yaml-cpp
        m
        atomic
)

target_compile_features(openyamm PRIVATE cxx_std_20)
add_dependencies(openyamm openyamm_runtime_shaders openyamm_ffmpeg_build)

if (UNIX AND NOT APPLE)
    target_link_options(openyamm
        PRIVATE
            "-Wl,-rpath,$ORIGIN/../_deps/sdl3-build"
    )
endif()
