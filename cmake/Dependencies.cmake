include_guard(GLOBAL)

include(FetchContent)

if (POLICY CMP0169)
    cmake_policy(SET CMP0169 OLD)
endif()

set(OPENYAMM_SDL3_VERSION "3.4.2")
set(OPENYAMM_SDL3_URL
    "https://github.com/libsdl-org/SDL/releases/download/release-${OPENYAMM_SDL3_VERSION}/SDL3-${OPENYAMM_SDL3_VERSION}.tar.gz"
)
set(OPENYAMM_SDL3_URL_HASH
    "SHA256=ef39a2e3f9a8a78296c40da701967dd1b0d0d6e267e483863ce70f8a03b4050c"
)

set(OPENYAMM_BGFX_VERSION "a73c12db8f502022d292cc6fb8872482997b0664")
set(OPENYAMM_BX_VERSION "0d38df86151b73b7b471a9a7db31deb5f4ce02ca")
set(OPENYAMM_BIMG_VERSION "6c13a0c8a8908243df475dfcab276554458dcd13")
set(OPENYAMM_IMGUI_VERSION "v1.92.6-docking")
set(OPENYAMM_PHYSFS_VERSION "release-3.2.0")
set(OPENYAMM_FREETYPE_VERSION "VER-2-14-2")
set(OPENYAMM_SPDLOG_VERSION "v1.16.0")
set(OPENYAMM_FMT_VERSION "12.1.0")
set(OPENYAMM_FFMPEG_VERSION "n8.0.1")
set(OPENYAMM_YAML_CPP_VERSION "0.8.0")
set(OPENYAMM_LUA_VERSION "5.4.8")
set(OPENYAMM_LUA_URL "https://www.lua.org/ftp/lua-${OPENYAMM_LUA_VERSION}.tar.gz")
set(OPENYAMM_LUA_URL_HASH "SHA256=4f18ddae154e793e46eeab727c59ef1c0c0c2b744e7b94219710d76f530629ae")

function(openyamm_populate_dependency dependencyName outputSourceDirVariable)
    FetchContent_GetProperties(${dependencyName})

    if (NOT ${dependencyName}_POPULATED)
        FetchContent_Populate(${dependencyName})
    endif()

    FetchContent_GetProperties(${dependencyName})

    set(${outputSourceDirVariable} "${${dependencyName}_SOURCE_DIR}" PARENT_SCOPE)
endfunction()

function(openyamm_configure_sdl3)
    if (TARGET SDL3::SDL3)
        return()
    endif()

    if (OPENYAMM_USE_SYSTEM_SDL3)
        find_package(SDL3 CONFIG REQUIRED)
        return()
    endif()

    if (ANDROID)
        set(SDL_SHARED ON CACHE BOOL "" FORCE)
        set(SDL_STATIC OFF CACHE BOOL "" FORCE)
    else()
        set(SDL_SHARED OFF CACHE BOOL "" FORCE)
        set(SDL_STATIC ON CACHE BOOL "" FORCE)
    endif()

    set(SDL_TEST_LIBRARY OFF CACHE BOOL "" FORCE)
    set(SDL_TESTS OFF CACHE BOOL "" FORCE)
    set(SDL_X11_XTEST OFF CACHE BOOL "" FORCE)

    if (DEFINED OPENYAMM_SDL3_SOURCE_DIR AND IS_DIRECTORY "${OPENYAMM_SDL3_SOURCE_DIR}")
        add_subdirectory("${OPENYAMM_SDL3_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/sdl3")
        return()
    endif()

    FetchContent_Declare(
        sdl3
        URL ${OPENYAMM_SDL3_URL}
        URL_HASH ${OPENYAMM_SDL3_URL_HASH}
    )
    FetchContent_MakeAvailable(sdl3)
endfunction()

function(openyamm_configure_lua)
    FetchContent_Declare(
        lua
        URL ${OPENYAMM_LUA_URL}
        URL_HASH ${OPENYAMM_LUA_URL_HASH}
    )

    openyamm_populate_dependency(lua luaSourceDir)

    if (NOT TARGET openyamm_lua)
        add_library(openyamm_lua STATIC
            ${luaSourceDir}/src/lapi.c
            ${luaSourceDir}/src/lauxlib.c
            ${luaSourceDir}/src/lbaselib.c
            ${luaSourceDir}/src/lcode.c
            ${luaSourceDir}/src/lcorolib.c
            ${luaSourceDir}/src/lctype.c
            ${luaSourceDir}/src/ldblib.c
            ${luaSourceDir}/src/ldebug.c
            ${luaSourceDir}/src/ldo.c
            ${luaSourceDir}/src/ldump.c
            ${luaSourceDir}/src/lfunc.c
            ${luaSourceDir}/src/lgc.c
            ${luaSourceDir}/src/linit.c
            ${luaSourceDir}/src/liolib.c
            ${luaSourceDir}/src/llex.c
            ${luaSourceDir}/src/lmathlib.c
            ${luaSourceDir}/src/lmem.c
            ${luaSourceDir}/src/loadlib.c
            ${luaSourceDir}/src/lobject.c
            ${luaSourceDir}/src/lopcodes.c
            ${luaSourceDir}/src/loslib.c
            ${luaSourceDir}/src/lparser.c
            ${luaSourceDir}/src/lstate.c
            ${luaSourceDir}/src/lstring.c
            ${luaSourceDir}/src/lstrlib.c
            ${luaSourceDir}/src/ltable.c
            ${luaSourceDir}/src/ltablib.c
            ${luaSourceDir}/src/ltm.c
            ${luaSourceDir}/src/lundump.c
            ${luaSourceDir}/src/lutf8lib.c
            ${luaSourceDir}/src/lvm.c
            ${luaSourceDir}/src/lzio.c
        )

        add_library(Lua::Lua ALIAS openyamm_lua)

        target_include_directories(openyamm_lua
            PUBLIC
                ${luaSourceDir}/src
        )

        target_compile_features(openyamm_lua PUBLIC c_std_99)

        if (UNIX)
            target_link_libraries(openyamm_lua PUBLIC m)
        endif()
    endif()

    set(OPENYAMM_LUA_TARGET openyamm_lua PARENT_SCOPE)
endfunction()

function(openyamm_configure_fmt)
    set(FMT_DOC OFF CACHE BOOL "" FORCE)
    set(FMT_TEST OFF CACHE BOOL "" FORCE)
    set(FMT_INSTALL OFF CACHE BOOL "" FORCE)

    FetchContent_Declare(
        fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG ${OPENYAMM_FMT_VERSION}
        GIT_SHALLOW TRUE
    )

    FetchContent_MakeAvailable(fmt)
endfunction()

function(openyamm_configure_spdlog)
    set(SPDLOG_BUILD_EXAMPLE OFF CACHE BOOL "" FORCE)
    set(SPDLOG_BUILD_EXAMPLE_HO OFF CACHE BOOL "" FORCE)
    set(SPDLOG_BUILD_SHARED OFF CACHE BOOL "" FORCE)
    set(SPDLOG_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(SPDLOG_BUILD_TESTS_HO OFF CACHE BOOL "" FORCE)
    set(SPDLOG_BUILD_WARNINGS OFF CACHE BOOL "" FORCE)
    set(SPDLOG_FMT_EXTERNAL ON CACHE BOOL "" FORCE)
    set(SPDLOG_INSTALL OFF CACHE BOOL "" FORCE)

    FetchContent_Declare(
        spdlog
        GIT_REPOSITORY https://github.com/gabime/spdlog.git
        GIT_TAG ${OPENYAMM_SPDLOG_VERSION}
        GIT_SHALLOW TRUE
    )

    FetchContent_MakeAvailable(spdlog)
endfunction()

function(openyamm_configure_freetype)
    set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
    set(FT_DISABLE_BROTLI ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_BZIP2 ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_HARFBUZZ ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_PNG ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_ZLIB ON CACHE BOOL "" FORCE)
    set(SKIP_INSTALL_ALL ON CACHE BOOL "" FORCE)

    FetchContent_Declare(
        freetype
        GIT_REPOSITORY https://github.com/freetype/freetype.git
        GIT_TAG ${OPENYAMM_FREETYPE_VERSION}
        GIT_SHALLOW TRUE
    )

    FetchContent_MakeAvailable(freetype)
endfunction()

function(openyamm_configure_physfs)
    set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
    set(PHYSFS_BUILD_DOCS OFF CACHE BOOL "" FORCE)
    set(PHYSFS_BUILD_SHARED OFF CACHE BOOL "" FORCE)
    set(PHYSFS_BUILD_TEST OFF CACHE BOOL "" FORCE)
    set(PHYSFS_INSTALL OFF CACHE BOOL "" FORCE)

    FetchContent_Declare(
        physfs
        GIT_REPOSITORY https://github.com/icculus/physfs.git
        GIT_TAG ${OPENYAMM_PHYSFS_VERSION}
        GIT_SHALLOW TRUE
    )

    FetchContent_MakeAvailable(physfs)
endfunction()

function(openyamm_configure_yaml_cpp)
    set(YAML_CPP_BUILD_CONTRIB OFF CACHE BOOL "" FORCE)
    set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
    set(YAML_CPP_INSTALL OFF CACHE BOOL "" FORCE)

    FetchContent_Declare(
        yaml-cpp
        GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
        GIT_TAG ${OPENYAMM_YAML_CPP_VERSION}
        GIT_SHALLOW TRUE
    )

    FetchContent_MakeAvailable(yaml-cpp)

    if (TARGET yaml-cpp AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(yaml-cpp PRIVATE -include cstdint)
    endif()

    if (TARGET yaml-cpp AND NOT TARGET yaml-cpp::yaml-cpp)
        add_library(yaml-cpp::yaml-cpp ALIAS yaml-cpp)
    endif()
endfunction()

function(openyamm_configure_imgui)
    FetchContent_Declare(
        imgui
        GIT_REPOSITORY https://github.com/ocornut/imgui.git
        GIT_TAG ${OPENYAMM_IMGUI_VERSION}
        GIT_SHALLOW TRUE
    )

    openyamm_populate_dependency(imgui imguiSourceDir)

    if (NOT TARGET imgui)
        add_library(imgui STATIC
            ${imguiSourceDir}/imgui.cpp
            ${imguiSourceDir}/imgui_demo.cpp
            ${imguiSourceDir}/imgui_draw.cpp
            ${imguiSourceDir}/imgui_tables.cpp
            ${imguiSourceDir}/imgui_widgets.cpp
        )

        add_library(imgui::imgui ALIAS imgui)

        target_include_directories(imgui
            PUBLIC
                ${imguiSourceDir}
        )

        target_compile_features(imgui PUBLIC cxx_std_20)
    endif()
endfunction()

function(openyamm_fetch_bgfx_stack)
    FetchContent_Declare(
        bx
        GIT_REPOSITORY https://github.com/bkaradzic/bx.git
        GIT_TAG ${OPENYAMM_BX_VERSION}
        GIT_SHALLOW FALSE
    )

    FetchContent_Declare(
        bimg
        GIT_REPOSITORY https://github.com/bkaradzic/bimg.git
        GIT_TAG ${OPENYAMM_BIMG_VERSION}
        GIT_SHALLOW FALSE
    )

    FetchContent_Declare(
        bgfx
        GIT_REPOSITORY https://github.com/bkaradzic/bgfx.git
        GIT_TAG ${OPENYAMM_BGFX_VERSION}
        GIT_SHALLOW FALSE
    )

    openyamm_populate_dependency(bx bxSourceDir)
    openyamm_populate_dependency(bimg bimgSourceDir)
    openyamm_populate_dependency(bgfx bgfxSourceDir)

    include("${CMAKE_CURRENT_FUNCTION_LIST_DIR}/BgfxGlUniformCache.cmake")
    openyamm_patch_bgfx_gl_uniform_cache("${bgfxSourceDir}")

    if (NOT TARGET openyamm_bgfx_headers)
        add_library(openyamm_bgfx_headers INTERFACE)

        target_include_directories(openyamm_bgfx_headers
            INTERFACE
                ${bxSourceDir}/include
                ${bimgSourceDir}/include
                ${bgfxSourceDir}/include
        )
    endif()

    set(OPENYAMM_BX_SOURCE_DIR "${bxSourceDir}" PARENT_SCOPE)
    set(OPENYAMM_BIMG_SOURCE_DIR "${bimgSourceDir}" PARENT_SCOPE)
    set(OPENYAMM_BGFX_SOURCE_DIR "${bgfxSourceDir}" PARENT_SCOPE)
endfunction()

function(openyamm_fetch_ffmpeg)
    FetchContent_Declare(
        ffmpeg
        GIT_REPOSITORY https://github.com/FFmpeg/FFmpeg.git
        GIT_TAG ${OPENYAMM_FFMPEG_VERSION}
        GIT_SHALLOW TRUE
    )

    openyamm_populate_dependency(ffmpeg ffmpegSourceDir)
    set(OPENYAMM_FFMPEG_SOURCE_DIR "${ffmpegSourceDir}" PARENT_SCOPE)
endfunction()

function(openyamm_configure_dependencies)
    openyamm_configure_sdl3()
    openyamm_configure_fmt()
    openyamm_configure_spdlog()
    openyamm_configure_freetype()
    openyamm_configure_physfs()
    openyamm_configure_yaml_cpp()
    openyamm_configure_imgui()
    openyamm_fetch_bgfx_stack()
    openyamm_fetch_ffmpeg()
endfunction()

openyamm_configure_dependencies()
