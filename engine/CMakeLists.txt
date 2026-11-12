add_library(openyamm_engine
    BgfxContext.cpp
    AudioSystem.cpp
    ApplicationConfig.cpp
    AssetFileSystem.cpp
    AssetPackIndex.cpp
    AssetScaleTier.cpp
    AssetPaths.cpp
    UserDataPaths.cpp
    LogFile.cpp
    update/AppInstallation.cpp
    update/AppUpdater.cpp
    update/HttpTransport.cpp
    update/ReleaseManifest.cpp
    update/Sha256.cpp
    FontAsset.cpp
    Localization.cpp
    ImageAssetLoader.cpp
    ImageAssetPaths.cpp
    ImageMipmaps.cpp
    ParallelFor.cpp
    models/CgltfImplementation.cpp
    models/GltfModelLoader.cpp
    models/ModelAnimation.cpp
    models/ModelAsset.cpp
    models/ModelInstance.cpp
    render/CookedTexture.cpp
    render/CookedTextureHeader.cpp
    render/ModelRenderer.cpp
    render/TextureBlockCodec.cpp
    render/ModelEnvironment.cpp
    render/LightGrid.cpp
    SpriteAtlas.cpp
    EngineApplication.cpp
    scripting/LuaStateOwner.cpp
    TextTable.cpp
    TextCatalog.cpp
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
        openyamm_bgfx
        SDL3::SDL3
        physfs-static
        yaml-cpp::yaml-cpp
        ${OPENYAMM_LUA_TARGET}
    PRIVATE
        freetype
        libzstd_static
        openyamm_monocypher
)

if (WIN32)
    target_link_libraries(openyamm_engine PRIVATE winhttp)
elseif (UNIX AND NOT ANDROID AND NOT APPLE)
    # The updater loads the system's libcurl at runtime (engine/update/HttpTransport.cpp).
    target_link_libraries(openyamm_engine PRIVATE ${CMAKE_DL_LIBS})
endif()
