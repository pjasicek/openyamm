cmake_minimum_required(VERSION 3.22)

project(OpenYAMM VERSION 0.1.0 LANGUAGES C CXX)

if (WIN32)
    enable_language(RC)
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
option(OPENYAMM_USE_VULKAN "Use Vulkan for the desktop renderer and build SPIR-V shaders." OFF)
if (OPENYAMM_USE_VULKAN AND (ANDROID OR APPLE))
    message(FATAL_ERROR "OPENYAMM_USE_VULKAN currently supports Linux and Windows desktop builds only.")
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

set(OPENYAMM_RUNTIME_SHADER_DIR "${CMAKE_BINARY_DIR}/runtime/shaders")
set(OPENYAMM_BGFX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bgfx-src")
set(OPENYAMM_BX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bx-src")
set(OPENYAMM_BIMG_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bimg-src")
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
if (WIN32)
    include(InstallRequiredSystemLibraries)
    string(REPLACE ";" "|" OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS "${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS}")
    get_filename_component(OPENYAMM_RELEASE_COMPILER_RUNTIME_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)
    set(OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES ON)
    set(OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS "${OPENYAMM_RELEASE_COMPILER_RUNTIME_DIR}")
endif()

set(OPENYAMM_RELEASE_ROOT_DIR "${CMAKE_BINARY_DIR}/release")
set(OPENYAMM_RELEASE_STAGE_DIR "${OPENYAMM_RELEASE_ROOT_DIR}/$<CONFIG>/OpenYAMM")
set(OPENYAMM_RELEASE_ZIP_PATH "${OPENYAMM_RELEASE_ROOT_DIR}/OpenYAMM-windows-$<CONFIG>.zip")
set(OPENYAMM_FLATPAK_OUTPUT_DIR
    "${CMAKE_BINARY_DIR}/flatpak"
    CACHE PATH
    "Output directory for local Flatpak release builds."
)

if (OPENYAMM_BUILD_DESKTOP_EXECUTABLE)
    add_custom_target(openyamm_windows_release_zip
        COMMAND "${CMAKE_COMMAND}"
            "-DOPENYAMM_RELEASE_STAGE_DIR=${OPENYAMM_RELEASE_STAGE_DIR}"
            "-DOPENYAMM_RELEASE_ZIP_PATH=${OPENYAMM_RELEASE_ZIP_PATH}"
            "-DOPENYAMM_RELEASE_EXECUTABLE=$<TARGET_FILE:openyamm>"
            "-DOPENYAMM_RELEASE_RUNTIME_DLLS=$<JOIN:$<TARGET_RUNTIME_DLLS:openyamm>,|>"
            "-DOPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS=${OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS}"
            "-DOPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES=${OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES}"
            "-DOPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS=${OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS}"
            "-DOPENYAMM_RELEASE_SHADER_DIR=${OPENYAMM_RUNTIME_SHADER_DIR}"
            "-DOPENYAMM_RELEASE_ASSET_DEV_DIR=${OPENYAMM_DEV_ASSETS_DIR}"
            "-DOPENYAMM_RELEASE_SETTINGS_TEMPLATE=${CMAKE_SOURCE_DIR}/settings_release.ini"
            -P "${CMAKE_SOURCE_DIR}/cmake/CreateOpenYammReleasePackage.cmake"
        DEPENDS openyamm openyamm_runtime_shaders
        VERBATIM
    )

    add_custom_target(openyamm_flatpak_release
        COMMAND "${CMAKE_SOURCE_DIR}/packaging/flatpak/build_flatpak.sh"
            "--output-dir=${OPENYAMM_FLATPAK_OUTPUT_DIR}"
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        USES_TERMINAL
        VERBATIM
    )

    add_custom_target(openyamm_flatpak_clean
        COMMAND "${CMAKE_SOURCE_DIR}/packaging/flatpak/build_flatpak.sh"
            "--output-dir=${OPENYAMM_FLATPAK_OUTPUT_DIR}"
            "--clean-only"
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        USES_TERMINAL
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
