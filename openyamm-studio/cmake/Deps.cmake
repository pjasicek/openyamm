# Third-party sources of the studio: the same versions the game pins in cmake/Dependencies.cmake. When the game's
# build tree has already fetched them (build/_deps), they are reused from there and nothing is downloaded.
include(FetchContent)

# yaml-cpp 0.8.0 asks for a CMake older than current releases accept.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

set(OYMAP_YAML_CPP_VERSION "0.8.0")
set(OYMAP_BX_VERSION "0d38df86151b73b7b471a9a7db31deb5f4ce02ca")

function(oymap_reuse_fetched name)
    string(TOUPPER "${name}" upperName)
    set(localDir "${OPENYAMM_ROOT}/build/_deps/${name}-src")

    if (NOT DEFINED FETCHCONTENT_SOURCE_DIR_${upperName} AND EXISTS "${localDir}/")
        set(FETCHCONTENT_SOURCE_DIR_${upperName} "${localDir}" CACHE PATH "" FORCE)
    endif()
endfunction()

oymap_reuse_fetched(yaml-cpp)
oymap_reuse_fetched(bx)

# yaml-cpp
set(YAML_CPP_BUILD_CONTRIB OFF CACHE BOOL "" FORCE)
set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(YAML_CPP_INSTALL OFF CACHE BOOL "" FORCE)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
FetchContent_Declare(yaml-cpp
    GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
    GIT_TAG ${OYMAP_YAML_CPP_VERSION}
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(yaml-cpp)
target_compile_options(yaml-cpp PRIVATE -include cstdint)

if (NOT TARGET yaml-cpp::yaml-cpp)
    add_library(yaml-cpp::yaml-cpp ALIAS yaml-cpp)
endif()

# bx: the movement and geometry code uses bx/math.h. Only bx itself, never bgfx.
FetchContent_Declare(bx
    GIT_REPOSITORY https://github.com/bkaradzic/bx.git
    GIT_TAG ${OYMAP_BX_VERSION}
    SOURCE_SUBDIR oymap-no-cmake)
FetchContent_MakeAvailable(bx)
# Only the math: the rest of bx (threads, files, allocators) is not used and does not build everywhere.
add_library(oymap_bx STATIC ${bx_SOURCE_DIR}/src/math.cpp)
target_include_directories(oymap_bx
    PUBLIC ${bx_SOURCE_DIR}/include
    PRIVATE ${bx_SOURCE_DIR}/3rdparty)
target_compile_definitions(oymap_bx PUBLIC BX_CONFIG_DEBUG=0)

if (UNIX AND NOT EMSCRIPTEN)
    target_include_directories(oymap_bx PUBLIC ${bx_SOURCE_DIR}/include/compat/linux)
    target_link_libraries(oymap_bx PUBLIC ${CMAKE_DL_LIBS} pthread)
endif()

# cgltf (one header): the repository's copy in third_party/cgltf, the same file as bgfx's 3rdparty/ copy that the game
# compiles (S7_PLAN.md 1.2). The sources include <cgltf/cgltf.h>.
set(OYMAP_CGLTF_INCLUDE_DIR "${OPENYAMM_ROOT}/third_party/cgltf")

# doctest for the studio's tests (the game's tests carry a copy).
if (EXISTS "${OPENYAMM_ROOT}/third_party/doctest/doctest.h" OR EXISTS "${OPENYAMM_ROOT}/third_party/doctest/doctest/doctest.h")
    set(OYMAP_DOCTEST_INCLUDE_DIR "${OPENYAMM_ROOT}/third_party/doctest")
endif()

# Lua 5.4.8 (the game's version): map event scripts are read by the game's own ScriptedEventProgram.
oymap_reuse_fetched(lua)
FetchContent_Declare(lua
    URL "https://www.lua.org/ftp/lua-5.4.8.tar.gz" "https://www.tecgraf.puc-rio.br/lua/ftp/lua-5.4.8.tar.gz"
    URL_HASH SHA256=4f18ddae154e793e46eeab727c59ef1c0c0c2b744e7b94219710d76f530629ae
    SOURCE_SUBDIR oymap-no-cmake)
FetchContent_MakeAvailable(lua)
set(OYMAP_LUA_SOURCES)

foreach(luaFile lapi lauxlib lbaselib lcode lcorolib lctype ldblib ldebug ldo ldump lfunc lgc linit liolib llex
        lmathlib lmem loadlib lobject lopcodes loslib lparser lstate lstring lstrlib ltable ltablib ltm lundump
        lutf8lib lvm lzio)
    list(APPEND OYMAP_LUA_SOURCES ${lua_SOURCE_DIR}/src/${luaFile}.c)
endforeach()

add_library(oymap_lua STATIC ${OYMAP_LUA_SOURCES})
target_include_directories(oymap_lua PUBLIC ${lua_SOURCE_DIR}/src)

if (UNIX AND NOT EMSCRIPTEN)
    target_link_libraries(oymap_lua PUBLIC m)
endif()

# PhysicsFS 3.2.0: the engine's AssetFileSystem reads asset roots and packages through it.
oymap_reuse_fetched(physfs)
set(PHYSFS_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(PHYSFS_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(PHYSFS_BUILD_TEST OFF CACHE BOOL "" FORCE)
set(PHYSFS_INSTALL OFF CACHE BOOL "" FORCE)
# yaml-cpp already made an "uninstall" target.
set(PHYSFS_TARGETNAME_UNINSTALL "physfs_uninstall" CACHE STRING "" FORCE)
FetchContent_Declare(physfs
    GIT_REPOSITORY https://github.com/icculus/physfs.git
    GIT_TAG release-3.2.0
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(physfs)

# zstd 1.5.7 (the game's version, cmake/SpriteAtlasCodecs.cmake): the history keeps each file version once,
# compressed (S5_BROWSER_EDITOR.md 2.7). Its library sources are compiled directly, single-threaded and without its
# assembly, so the native and the WebAssembly core build it the same way.
oymap_reuse_fetched(openyamm_zstd)
FetchContent_Declare(openyamm_zstd
    URL https://codeload.github.com/facebook/zstd/tar.gz/refs/tags/v1.5.7
    URL_HASH SHA256=37d7284556b20954e56e1ca85b80226768902e2edabd3b649e9e72c0c9012ee3
    SOURCE_SUBDIR oymap-no-cmake)
FetchContent_MakeAvailable(openyamm_zstd)
file(GLOB OYMAP_ZSTD_SOURCES
    ${openyamm_zstd_SOURCE_DIR}/lib/common/*.c
    ${openyamm_zstd_SOURCE_DIR}/lib/compress/*.c
    ${openyamm_zstd_SOURCE_DIR}/lib/decompress/*.c)
add_library(oymap_zstd STATIC ${OYMAP_ZSTD_SOURCES})
target_include_directories(oymap_zstd PUBLIC ${openyamm_zstd_SOURCE_DIR}/lib)
target_compile_definitions(oymap_zstd PRIVATE ZSTD_DISABLE_ASM=1 ZSTD_MULTITHREAD=0 ZSTD_LEGACY_SUPPORT=0)
