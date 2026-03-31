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
        --enable-decoder=theora
        --enable-decoder=vorbis
        --enable-parser=vorbis
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
    ActorNameResolver.cpp
    GameAudioSystem.cpp
    ChestTable.cpp
    CharacterInspectTable.cpp
    CharacterDollTable.cpp
    ClassSkillTable.cpp
    EventDialogContent.cpp
    EventIr.cpp
    EventRuntime.cpp
    EvtProgram.cpp
    FaceAnimationTable.cpp
    GameMechanics.cpp
    GenericActorDialog.cpp
    HouseInteraction.cpp
    HouseServiceRuntime.cpp
    HouseVideoPlayer.cpp
    InventoryItemUseRuntime.cpp
    MapDeltaData.cpp
    GameDataLoader.cpp
    HeadlessOutdoorDiagnostics.cpp
    HouseTable.cpp
    IconFrameTable.cpp
    ItemEquipPosTable.cpp
    ItemEnchantTables.cpp
    ItemEnchantRuntime.cpp
    ItemGenerator.cpp
    ItemRuntime.cpp
    ItemTable.cpp
    IndoorDebugRenderer.cpp
    IndoorMapData.cpp
    MapAssetLoader.cpp
    MapRegistry.cpp
    MapStats.cpp
    MasteryTeacherDialog.cpp
    MonsterProjectileTable.cpp
    MonsterTable.cpp
    NpcDialogTable.cpp
    ObjectTable.cpp
    OutdoorMapData.cpp
    OutdoorGeometryUtils.cpp
    OutdoorMovementController.cpp
    OutdoorMovementDriver.cpp
    OutdoorPartyRuntime.cpp
    OutdoorWorldRuntime.cpp
    Party.cpp
    PartySpellSystem.cpp
    PriceCalculator.cpp
    ReadableScrollTable.cpp
    PortraitFxEventTable.cpp
    PortraitEnums.cpp
    PortraitFrameTable.cpp
    RosterTable.cpp
    SaveGame.cpp
    SoundCatalog.cpp
    SpawnPreview.cpp
    SkillData.cpp
    SpeechReactionTable.cpp
    SpellSchool.cpp
    SpellTable.cpp
    SpellFxTable.cpp
    SpriteTables.cpp
    StrTable.cpp
    OutdoorGameView.cpp
    main.cpp
    GameApplication.cpp
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
