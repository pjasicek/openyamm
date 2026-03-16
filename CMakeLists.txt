cmake_minimum_required(VERSION 3.24)

project(OpenYAMM VERSION 0.1.0 LANGUAGES CXX)

include(FetchContent)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_BUILD_RPATH_USE_ORIGIN ON)

option(OPENYAMM_BUILD_EDITOR "Build the editor target." OFF)
option(OPENYAMM_BUILD_TOOLS "Build the tools targets." OFF)
option(OPENYAMM_USE_SYSTEM_SDL3 "Use an installed SDL3 package instead of fetching it." OFF)

set(OPENYAMM_DEV_ASSETS_DIR
    "${CMAKE_SOURCE_DIR}/assets_dev"
    CACHE PATH
    "Path to the development assets directory."
)

set(OPENYAMM_WINDOW_WIDTH
    1280
    CACHE STRING
    "Default application window width."
)

set(OPENYAMM_WINDOW_HEIGHT
    720
    CACHE STRING
    "Default application window height."
)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

include(Dependencies)

set(OPENYAMM_RUNTIME_SHADER_DIR "${CMAKE_BINARY_DIR}/runtime/shaders")
set(OPENYAMM_BGFX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bgfx-src")
set(OPENYAMM_BX_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bx-src")
set(OPENYAMM_BIMG_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/bimg-src")
file(GLOB OPENYAMM_ASTC_ENCODER_SOURCES "${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/astc-encoder/source/*.cpp")

if (NOT TARGET openyamm_bgfx)
    find_package(OpenGL REQUIRED)
    find_package(Threads REQUIRED)

    if (UNIX AND NOT APPLE)
        find_package(X11 REQUIRED)
    endif()

    add_library(openyamm_bgfx STATIC
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/bgfx.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/debug_renderdoc.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/glcontext_egl.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_agc.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_d3d11.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_d3d12.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_gl.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_gnm.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_noop.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_nvn.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_vk.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/renderer_webgpu.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/shader.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/shader_spirv.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/topology.cpp
        ${OPENYAMM_BGFX_SOURCE_DIR}/src/vertexlayout.cpp
        ${OPENYAMM_BX_SOURCE_DIR}/src/amalgamated.cpp
        ${OPENYAMM_BIMG_SOURCE_DIR}/src/image.cpp
        ${OPENYAMM_BIMG_SOURCE_DIR}/src/image_decode.cpp
        ${OPENYAMM_BIMG_SOURCE_DIR}/src/image_encode.cpp
        ${OPENYAMM_BIMG_SOURCE_DIR}/src/image_gnf.cpp
        ${OPENYAMM_ASTC_ENCODER_SOURCES}
    )

    target_include_directories(openyamm_bgfx
        PUBLIC
            ${OPENYAMM_BGFX_SOURCE_DIR}/include
            ${OPENYAMM_BX_SOURCE_DIR}/include
            ${OPENYAMM_BIMG_SOURCE_DIR}/include
        PRIVATE
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/khronos
            ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty
            ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/astc-encoder/include
            ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/iqa/include
            ${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/tinyexr/deps
            ${OPENYAMM_BX_SOURCE_DIR}/3rdparty
    )

    target_compile_features(openyamm_bgfx PUBLIC cxx_std_20)
    target_compile_definitions(openyamm_bgfx
        PUBLIC
            BX_CONFIG_DEBUG=$<IF:$<CONFIG:Debug>,1,0>
        PRIVATE
            BGFX_CONFIG_RENDERER_DIRECT3D11=0
            BGFX_CONFIG_RENDERER_DIRECT3D12=0
            BGFX_CONFIG_RENDERER_METAL=0
            BGFX_CONFIG_RENDERER_VULKAN=0
            BGFX_CONFIG_RENDERER_WEBGPU=0
            BGFX_CONFIG_RENDERER_OPENGL=33
            BGFX_CONFIG_RENDERER_OPENGLES=0
    )
    target_link_libraries(openyamm_bgfx PUBLIC Threads::Threads ${CMAKE_DL_LIBS} OpenGL::GL)

    if (UNIX AND NOT APPLE)
        target_link_libraries(openyamm_bgfx PUBLIC X11::X11 X11::Xext)
    endif()
endif()

add_custom_target(openyamm_runtime_shaders ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/vs_cubes.bin"
        "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_cubes.bin"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/fs_cubes.bin"
        "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_cubes.bin"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/vs_shadowmaps_texture.bin"
        "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_shadowmaps_texture.bin"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/fs_shadowmaps_texture.bin"
        "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_shadowmaps_texture.bin"
)

add_subdirectory(engine)
add_subdirectory(game)

if (OPENYAMM_BUILD_EDITOR)
    add_subdirectory(editor)
endif()

if (OPENYAMM_BUILD_TOOLS)
    add_subdirectory(tools)
endif()
