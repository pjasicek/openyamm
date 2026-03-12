cmake_minimum_required(VERSION 3.24)

project(OpenYAMM VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(OPENYAMM_BUILD_EDITOR "Build the editor target." OFF)
option(OPENYAMM_BUILD_TOOLS "Build the tools targets." OFF)

set(OPENYAMM_DEV_ASSETS_DIR
    "${CMAKE_SOURCE_DIR}/assets_dev"
    CACHE PATH
    "Path to the development assets directory."
)

add_subdirectory(engine)
add_subdirectory(game)

if (OPENYAMM_BUILD_EDITOR)
    add_subdirectory(editor)
endif()

if (OPENYAMM_BUILD_TOOLS)
    add_subdirectory(tools)
endif()
