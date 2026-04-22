cmake_minimum_required(VERSION 3.24)

project(OpenYAMM VERSION 0.1.0 LANGUAGES C CXX)

include(FetchContent)
include(FindPkgConfig)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_BUILD_RPATH_USE_ORIGIN ON)

option(OPENYAMM_BUILD_EDITOR "Build the editor target." OFF)
option(OPENYAMM_BUILD_TOOLS "Build the tools targets." OFF)
option(OPENYAMM_BUILD_TESTS "Build the unit test target." ON)
option(OPENYAMM_USE_SYSTEM_SDL3 "Use an installed SDL3 package instead of fetching it." OFF)

set(OPENYAMM_DEV_ASSETS_DIR
    "${CMAKE_SOURCE_DIR}/assets_dev"
    CACHE PATH
    "Path to the development assets directory."
)

set(OPENYAMM_WINDOW_WIDTH
    1600
    CACHE STRING
    "Default application window width."
)

set(OPENYAMM_WINDOW_HEIGHT
    900
    CACHE STRING
    "Default application window height."
)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

include(Dependencies)
include(BgfxRuntime)

pkg_check_modules(OPENYAMM_LUA54 QUIET IMPORTED_TARGET lua5.4)

if (OPENYAMM_LUA54_FOUND)
    set(OPENYAMM_LUA_TARGET PkgConfig::OPENYAMM_LUA54)
else()
    pkg_check_modules(OPENYAMM_LUA53 REQUIRED IMPORTED_TARGET lua5.3)
    set(OPENYAMM_LUA_TARGET PkgConfig::OPENYAMM_LUA53)
endif()

set(OPENYAMM_RUNTIME_SHADER_DIR "${CMAKE_BINARY_DIR}/runtime/shaders")
set(OPENYAMM_BGFX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bgfx-src")
set(OPENYAMM_BX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bx-src")
set(OPENYAMM_BIMG_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bimg-src")
openyamm_configure_bgfx_runtime()
openyamm_configure_runtime_shaders()

add_subdirectory(engine)
add_subdirectory(game)

if (OPENYAMM_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if (OPENYAMM_BUILD_EDITOR)
    add_subdirectory(editor)
endif()

if (OPENYAMM_BUILD_TOOLS)
    add_subdirectory(tools)
endif()
