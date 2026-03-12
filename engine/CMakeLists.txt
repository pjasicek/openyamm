add_library(openyamm_engine
    ApplicationConfig.cpp
    AssetPaths.cpp
)

target_include_directories(openyamm_engine
    PUBLIC
        ${CMAKE_SOURCE_DIR}
)

target_compile_features(openyamm_engine PUBLIC cxx_std_20)

target_compile_definitions(openyamm_engine
    PUBLIC
        OPENYAMM_DEV_ASSETS_DIR="${OPENYAMM_DEV_ASSETS_DIR}"
)
