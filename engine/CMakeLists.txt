add_library(openyamm_engine
    BgfxContext.cpp
    AudioSystem.cpp
    DisplayModes.cpp
    ApplicationConfig.cpp
    AssetPaths.cpp
    UserDataPaths.cpp
    LogFile.cpp
    update/AppInstallation.cpp
    update/AppUpdater.cpp
    update/HttpTransport.cpp
    update/ReleaseManifest.cpp
    net/ByteStream.cpp
    net/EnetTransport.cpp
    net/LanDiscovery.cpp
    net/LoopbackTransport.cpp
    net/NetCompression.cpp
    net/RendezvousClient.cpp
    net/RendezvousProtocol.cpp
    net/RendezvousServer.cpp
    FontAsset.cpp
    ImageAssetLoader.cpp
    ImageMipmaps.cpp
    ParallelFor.cpp
    models/GltfModelLoader.cpp
    models/ModelAnimation.cpp
    models/ModelAsset.cpp
    models/ModelInstance.cpp
    render/CookedTexture.cpp
    render/ModelRenderer.cpp
    render/TextureBlockCodec.cpp
    render/ModelEnvironment.cpp
    render/LightGrid.cpp
    SpriteAtlas.cpp
    EngineApplication.cpp
    # meshoptimizer (MIT, shipped with bgfx): vertex cache order of loaded model triangles.
    ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/meshoptimizer/src/allocator.cpp
    ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/meshoptimizer/src/vcacheoptimizer.cpp
)

target_include_directories(openyamm_engine
    PUBLIC
        ${CMAKE_SOURCE_DIR}
    PRIVATE
        ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty
)

target_compile_features(openyamm_engine PUBLIC cxx_std_20)

if (OPENYAMM_USE_VULKAN)
    target_compile_definitions(openyamm_engine PRIVATE OPENYAMM_USE_VULKAN=1)
endif()

target_compile_definitions(openyamm_engine
    PUBLIC
        OPENYAMM_DEV_ASSETS_DIR="${OPENYAMM_DEV_ASSETS_DIR}"
        OPENYAMM_WINDOW_WIDTH=${OPENYAMM_WINDOW_WIDTH}
        OPENYAMM_WINDOW_HEIGHT=${OPENYAMM_WINDOW_HEIGHT}
)

target_link_libraries(openyamm_engine
    PUBLIC
        openyamm_core
        openyamm_bgfx
        SDL3::SDL3
        physfs-static
        yaml-cpp::yaml-cpp
        ${OPENYAMM_LUA_TARGET}
    PRIVATE
        freetype
        libzstd_static
        openyamm_monocypher
        openyamm_enet
)

if (WIN32)
    target_link_libraries(openyamm_engine PRIVATE winhttp)
elseif (UNIX AND NOT ANDROID AND NOT APPLE)
    # The updater loads the system's libcurl at runtime (engine/update/HttpTransport.cpp).
    target_link_libraries(openyamm_engine PRIVATE ${CMAKE_DL_LIBS})
endif()

if (APPLE AND NOT IOS)
    # DisplayModes.cpp reads the panel's native display mode.
    target_link_libraries(openyamm_engine PRIVATE "-framework CoreFoundation" "-framework CoreGraphics")
endif()
