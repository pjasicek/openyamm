cmake_minimum_required(VERSION 3.22)

project(OpenYAMM VERSION 0.1.0 LANGUAGES C CXX)

if (WIN32)
    enable_language(RC)
endif()

# SDL's Cocoa/UIKit backends are Objective-C and bgfx's Metal renderer is Objective-C++.
if (APPLE)
    enable_language(OBJC OBJCXX)
    set(CMAKE_OBJCXX_STANDARD 20)
    set(CMAKE_OBJCXX_STANDARD_REQUIRED ON)
endif()

if (IOS)
    add_compile_definitions(OPENYAMM_IOS=1)
endif()

if (CMAKE_VERSION VERSION_GREATER_EQUAL 4.0 AND NOT DEFINED CMAKE_POLICY_VERSION_MINIMUM)
    set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
endif()

if (POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

include(FetchContent)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_BUILD_RPATH_USE_ORIGIN ON)

option(OPENYAMM_BUILD_EDITOR "Build the editor target." OFF)
option(OPENYAMM_BUILD_TOOLS "Build the tools targets." OFF)
option(OPENYAMM_BUILD_TESTS "Build the unit test target." ON)
option(OPENYAMM_BUILD_DESKTOP_EXECUTABLE "Build the desktop OpenYAMM executable." ON)
option(OPENYAMM_USE_SYSTEM_SDL3 "Use an installed SDL3 package instead of fetching it." OFF)
option(OPENYAMM_BGFX_DEBUG "Build bgfx with its debug checks (every GL call checked) for diagnostic builds." OFF)
option(OPENYAMM_USE_VULKAN "Use Vulkan for the desktop renderer and build SPIR-V shaders." OFF)
if (OPENYAMM_USE_VULKAN AND (ANDROID OR APPLE))
    message(FATAL_ERROR "OPENYAMM_USE_VULKAN currently supports Linux and Windows desktop builds only.")
endif()
option(OPENYAMM_STATIC_LIBSTDCXX
    "Link libstdc++ and libgcc statically into the Linux executables, as the release packages do." OFF)
if (OPENYAMM_STATIC_LIBSTDCXX AND (WIN32 OR ANDROID OR APPLE))
    message(FATAL_ERROR "OPENYAMM_STATIC_LIBSTDCXX is for Linux desktop builds.")
endif()
option(
    OPENYAMM_ENABLE_GPROF_SAMPLING
    "Link the desktop executable for low-overhead gprof histogram sampling without call-arc instrumentation."
    OFF
)
set(OPENYAMM_RUNTIME_SHADER_PATH
    ""
    CACHE STRING
    "Runtime shader path embedded in the desktop executable. Empty selects the platform default."
)

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

openyamm_configure_lua()
openyamm_configure_monocypher()
include(SpriteAtlasCodecs)

set(OPENYAMM_RUNTIME_SHADER_DIR "${CMAKE_BINARY_DIR}/runtime/shaders")
# The checkouts may live outside the build tree (FETCHCONTENT_SOURCE_DIR_<NAME>, as packaging/apple/build_ios.sh uses).
FetchContent_GetProperties(bgfx SOURCE_DIR OPENYAMM_BGFX_SOURCE_DIR)
FetchContent_GetProperties(bx SOURCE_DIR OPENYAMM_BX_SOURCE_DIR)
FetchContent_GetProperties(bimg SOURCE_DIR OPENYAMM_BIMG_SOURCE_DIR)
openyamm_configure_bgfx_runtime()
openyamm_configure_runtime_shaders()

add_subdirectory(engine)
add_subdirectory(game)

if (ANDROID)
    add_subdirectory(android/app/src/main/cpp)
endif()

set(OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS "")
set(OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES OFF)
set(OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS "")
if (WIN32 AND NOT CMAKE_CROSSCOMPILING)
    include(InstallRequiredSystemLibraries)
    string(REPLACE ";" "|" OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS "${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS}")
    get_filename_component(OPENYAMM_RELEASE_COMPILER_RUNTIME_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)
    set(OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES ON)
    set(OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS "${OPENYAMM_RELEASE_COMPILER_RUNTIME_DIR}")
endif()

# Cross builds (the MinGW-w64 toolchain links its runtime statically) package with host-built tools.
if (CMAKE_CROSSCOMPILING)
    set(OPENYAMM_HOST_SPRITE_ATLAS_COOK "" CACHE FILEPATH "Host sprite atlas cooker used while cross-compiling.")
    set(OPENYAMM_RELEASE_COOKER "${OPENYAMM_HOST_SPRITE_ATLAS_COOK}")
    if (NOT ANDROID AND NOT IOS)
        find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
    endif()
else()
    set(OPENYAMM_RELEASE_COOKER "$<TARGET_FILE:openyamm_sprite_atlas_cook>")
endif()

set(OPENYAMM_RELEASE_CONTENT_DIR
    ""
    CACHE PATH
    "Prebuilt release content (index.json and packs/) for the release package; empty packages assets_dev."
)
option(OPENYAMM_RELEASE_THIN
    "Build the small release package: the game without content packs, which it downloads on the first start." OFF)
set(OPENYAMM_RELEASE_VERSION "dev" CACHE STRING
    "Release name of the desktop package: its app/<version> folder and the version the updater compares.")
if (WIN32)
    set(openyammReleasePlatform "windows-x64")
    set(openyammReleaseArchiveSuffix ".zip")
else()
    set(openyammReleasePlatform "linux-x64")
    set(openyammReleaseArchiveSuffix ".tar.gz")
endif()
set(OPENYAMM_RELEASE_ROOT_DIR "${CMAKE_BINARY_DIR}/release")
set(OPENYAMM_RELEASE_STAGE_DIR "${OPENYAMM_RELEASE_ROOT_DIR}/$<CONFIG>/OpenYAMM")
set(OPENYAMM_RELEASE_ARCHIVE_PATH
    "${OPENYAMM_RELEASE_ROOT_DIR}/OpenYAMM-${openyammReleasePlatform}-$<CONFIG>${openyammReleaseArchiveSuffix}")

# iOS packages its assets into the app bundle instead (packaging/apple/build_ios.sh).
if (OPENYAMM_BUILD_DESKTOP_EXECUTABLE AND NOT IOS)
    # The versioned installation of packaging/UPDATER_PLAN.md 9.1 as a zip (Windows) or tar.gz (Linux).
    add_custom_target(openyamm_release_package
        COMMAND "${CMAKE_COMMAND}"
            "-DOPENYAMM_RELEASE_STAGE_DIR=${OPENYAMM_RELEASE_STAGE_DIR}"
            "-DOPENYAMM_RELEASE_ARCHIVE_PATH=${OPENYAMM_RELEASE_ARCHIVE_PATH}"
            "-DOPENYAMM_RELEASE_EXECUTABLE=$<TARGET_FILE:openyamm>"
            "-DOPENYAMM_RELEASE_RUNTIME_DLLS=$<JOIN:$<TARGET_RUNTIME_DLLS:openyamm>,|>"
            "-DOPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS=${OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS}"
            "-DOPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES=${OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES}"
            "-DOPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS=${OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS}"
            "-DOPENYAMM_RELEASE_SHADER_DIR=${OPENYAMM_RUNTIME_SHADER_DIR}"
            "-DOPENYAMM_RELEASE_ASSET_DEV_DIR=${OPENYAMM_DEV_ASSETS_DIR}"
            "-DOPENYAMM_RELEASE_PYTHON=${Python3_EXECUTABLE}"
            "-DOPENYAMM_RELEASE_COOKER=${OPENYAMM_RELEASE_COOKER}"
            "-DOPENYAMM_RELEASE_CONTENT_DIR=${OPENYAMM_RELEASE_CONTENT_DIR}"
            "-DOPENYAMM_RELEASE_THIN=${OPENYAMM_RELEASE_THIN}"
            "-DOPENYAMM_RELEASE_LAUNCHER=$<$<TARGET_EXISTS:openyamm_launcher>:$<TARGET_FILE:openyamm_launcher>>"
            "-DOPENYAMM_RELEASE_VERSION=${OPENYAMM_RELEASE_VERSION}"
            -P "${CMAKE_SOURCE_DIR}/cmake/CreateOpenYammReleasePackage.cmake"
        DEPENDS openyamm openyamm_runtime_shaders $<$<TARGET_EXISTS:openyamm_launcher>:openyamm_launcher>
        VERBATIM
    )
endif()

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
