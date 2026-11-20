# Map Studio (devdocs/map_studio/PLAN.md). A standalone project with its own build tree, so that building it never
# reconfigures or locks the game's build/. It links the shared core (../core: the game and engine sources it shares
# with the game, and the map builds in core/compile/), compiled once in this tree, and needs neither SDL nor bgfx.
# The same file builds the native tools and, under Emscripten, the WebAssembly core.
#
#   ./build.sh            native build into openyamm-studio/build
#   ./build.sh wasm       WebAssembly build into openyamm-studio/build-wasm (needs emsdk, see wasm/README.md)
cmake_minimum_required(VERSION 3.24)

project(OpenYammStudio VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release)
endif()

get_filename_component(OPENYAMM_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)

option(OYMAP_BUILD_TESTS "Build the studio's unit tests." ON)

if (EMSCRIPTEN)
    # yaml-cpp throws and the loaders catch; Lua (later) raises errors with longjmp. Before the dependencies, so
    # every object is built the same way.
    add_compile_options(-fwasm-exceptions)
    add_link_options(-fwasm-exceptions)
    # The allocator of the wasm builds (S8f). Emscripten's dlmalloc by default: mimalloc answers the edits' many
    # small allocations faster (an indoor commit about 15 % sooner) but grows the memory to 1.1 GB on Castle
    # Darkmoor's checks job (dlmalloc 193 MB), past the hosted page's 1 GB. The same bytes either way.
    set(OYMAP_WASM_MALLOC "dlmalloc" CACHE STRING "The WebAssembly core's allocator: dlmalloc or mimalloc.")
    set_property(CACHE OYMAP_WASM_MALLOC PROPERTY STRINGS dlmalloc mimalloc)
    if (NOT OYMAP_WASM_MALLOC STREQUAL "dlmalloc")
        add_link_options(-sMALLOC=${OYMAP_WASM_MALLOC})
    endif()
endif()

include(cmake/Deps.cmake)

# Output bytes must not depend on the build (native against wasm, PLAN.md section 3): no fast-math, and no
# contraction of a*b+c into fused multiply-adds, which differs between targets.
add_compile_options(-ffp-contract=off)

# --- The shared core ------------------------------------------------------------------------------------------------
# The game and engine sources the studio shares with the game (openyamm_core) and the indoor compiler and outdoor build
# (openyamm_core_compile, core/compile/): compiled once, with this tree's flags (above).
set(OPENYAMM_CORE_LUA_TARGET oymap_lua)
set(OPENYAMM_CORE_BX_TARGET oymap_bx)
add_subdirectory(${OPENYAMM_ROOT}/core ${CMAKE_BINARY_DIR}/openyamm_core)

file(GLOB OYMAP_CORE_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/core/*.cpp)
# The game's reader of a terrain material file (core/GroundTerrain checks what it writes with it). Not in the shared
# core's list (the game compiles it in its own renderer library), so compiled here, once in this tree.
list(APPEND OYMAP_CORE_SOURCES ${OPENYAMM_ROOT}/game/render/TerrainMaterialConfig.cpp)

# The core's own math functions (core/CoreMath.h): musl's sources, the same bits natively and in wasm, whatever the
# C library (third_party/musl_math/README.md).
set(OYMAP_MUSL_MATH_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/musl_math)
set(OYMAP_MUSL_MATH_FILES)
foreach(name sin cos tan __sin __cos __tan __rem_pio2 __rem_pio2_large asin acos atan atan2 hypot cbrt pow pow_data
        exp_data scalbn __math_oflow __math_uflow __math_xflow __math_invalid __math_divzero)
    list(APPEND OYMAP_MUSL_MATH_FILES ${OYMAP_MUSL_MATH_DIR}/src/${name}.c)
endforeach()
add_library(oymap_musl_math STATIC ${OYMAP_MUSL_MATH_FILES})
set_target_properties(oymap_musl_math PROPERTIES C_STANDARD 99 C_EXTENSIONS ON)
target_include_directories(oymap_musl_math BEFORE PRIVATE ${OYMAP_MUSL_MATH_DIR}/include ${OYMAP_MUSL_MATH_DIR}/src)
target_compile_options(oymap_musl_math PRIVATE -fno-builtin -ffp-contract=off -U__FP_FAST_FMA -w
    "SHELL:-include ${OYMAP_MUSL_MATH_DIR}/include/oy_musl_names.h")

# The project format's schemas, compiled in (the command line, the host and the wasm core share one text).
file(GLOB OYMAP_SCHEMA_FILES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/schema/*.schema.json)
set(OYMAP_EMBEDDED_SCHEMAS ${CMAKE_CURRENT_BINARY_DIR}/EmbeddedSchemas.cpp)
add_custom_command(
    OUTPUT ${OYMAP_EMBEDDED_SCHEMAS}
    COMMAND ${CMAKE_COMMAND} -DDIR=${CMAKE_CURRENT_SOURCE_DIR}/schema -DOUT=${OYMAP_EMBEDDED_SCHEMAS}
        -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedSchemas.cmake
    DEPENDS ${OYMAP_SCHEMA_FILES} ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedSchemas.cmake
    VERBATIM)

# The request list (schema/rpc/*.rpc.json), compiled in beside the project schemas it refers to.
file(GLOB OYMAP_RPC_SCHEMA_FILES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/schema/rpc/*.rpc.json)
set(OYMAP_EMBEDDED_RPC_SCHEMAS ${CMAKE_CURRENT_BINARY_DIR}/EmbeddedRpcSchemas.cpp)
add_custom_command(
    OUTPUT ${OYMAP_EMBEDDED_RPC_SCHEMAS}
    COMMAND ${CMAKE_COMMAND} -DDIR=${CMAKE_CURRENT_SOURCE_DIR}/schema/rpc -DOUT=${OYMAP_EMBEDDED_RPC_SCHEMAS}
        -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedRpcSchemas.cmake
    DEPENDS ${OYMAP_RPC_SCHEMA_FILES} ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedRpcSchemas.cmake
    VERBATIM)

# The names of the game's event functions, read from the game's registration (the flow sandbox reports a call to
# anything else).
set(OYMAP_EVENT_RUNTIME_SOURCE ${OPENYAMM_ROOT}/game/events/EventRuntime.cpp)
set(OYMAP_EMBEDDED_EVENT_FUNCTIONS ${CMAKE_CURRENT_BINARY_DIR}/EmbeddedEventFunctions.cpp)
add_custom_command(
    OUTPUT ${OYMAP_EMBEDDED_EVENT_FUNCTIONS}
    COMMAND ${CMAKE_COMMAND} -DSOURCE=${OYMAP_EVENT_RUNTIME_SOURCE} -DOUT=${OYMAP_EMBEDDED_EVENT_FUNCTIONS}
        -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedEventFunctions.cmake
    DEPENDS ${OYMAP_EVENT_RUNTIME_SOURCE} ${CMAKE_CURRENT_SOURCE_DIR}/cmake/EmbedEventFunctions.cmake
    VERBATIM)

add_library(oymap_core STATIC ${OYMAP_CORE_SOURCES} ${OYMAP_EMBEDDED_SCHEMAS}
    ${OYMAP_EMBEDDED_EVENT_FUNCTIONS} ${OYMAP_EMBEDDED_RPC_SCHEMAS})
target_include_directories(oymap_core
    PUBLIC
        ${OPENYAMM_ROOT}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${OYMAP_CGLTF_INCLUDE_DIR}
)
target_link_libraries(oymap_core PUBLIC openyamm_core_compile openyamm_core yaml-cpp::yaml-cpp oymap_bx oymap_lua physfs-static oymap_musl_math
    oymap_zstd)
# The engine's development asset root (engine/AssetPaths); the studio is always told its root, this is the default.
target_compile_definitions(oymap_core PUBLIC OPENYAMM_DEV_ASSETS_DIR="${OPENYAMM_ROOT}/assets_dev")

file(GLOB OYMAP_CLI_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/cli/*.cpp)
add_executable(oymap ${OYMAP_CLI_SOURCES})
target_link_libraries(oymap PRIVATE oymap_core)

if (EMSCRIPTEN)
    # The smoke build: the command line itself run under Node with the host file system mounted, and the host's
    # HOME and OYMAP_* passed in (PhysicsFS needs a user directory to open an asset root).
    target_link_options(oymap PRIVATE
        -sNODERAWFS=1 -sALLOW_MEMORY_GROWTH=1 -sEXIT_RUNTIME=1 -sSTACK_SIZE=4MB
        --pre-js ${CMAKE_CURRENT_SOURCE_DIR}/wasm/node_env.pre.js)
    set_property(TARGET oymap APPEND PROPERTY LINK_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/wasm/node_env.pre.js)

    # The request list as a module: one C function, oymap_call(method, params JSON) -> answer JSON
    # (S5_BROWSER_EDITOR.md 2.3). For Node here (the contract suite); the browser worker build differs only in its
    # file system.
    set(OYMAP_RPC_MODULE_SOURCES ${OYMAP_CLI_SOURCES})
    list(FILTER OYMAP_RPC_MODULE_SOURCES EXCLUDE REGEX "/main\\.cpp$")
    add_executable(oymap_rpc ${OYMAP_RPC_MODULE_SOURCES}
        ${CMAKE_CURRENT_SOURCE_DIR}/wasm/RpcModule.cpp)
    target_link_libraries(oymap_rpc PRIVATE oymap_core)
    if (OYMAP_WASM_MALLOC STREQUAL "mimalloc")
        target_compile_definitions(oymap_rpc PRIVATE OYMAP_MIMALLOC)
    endif()
    target_link_options(oymap_rpc PRIVATE
        -sNODERAWFS=1 -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=4MB -sMODULARIZE=1 -sEXPORT_NAME=createOymapCore
        -sENVIRONMENT=node -sEXPORTED_FUNCTIONS=_oymap_call,_oymap_free,_malloc,_free
        -sEXPORTED_RUNTIME_METHODS=UTF8ToString,stringToNewUTF8 --profiling-funcs
        --pre-js ${CMAKE_CURRENT_SOURCE_DIR}/wasm/node_env.pre.js)

    # The browser's worker (S5_BROWSER_EDITOR.md 2.2, D7; S5c): the same request list as an ES module for a Web
    # Worker, with an in-memory file system the worker fills: in local mode with what it fetched from the host (walk
    # mode's map, movement state, terrain pack and decoration table), in hosted mode with the project folders the page
    # opened and the asset root mounted read-only over the player's packages (web/src/hosted/packfs.ts). The host
    # serves it at /core/, the hosted site beside its page. It also runs under Node (ENVIRONMENT node, NODEFS), so the
    # RPC contract suite drives this very build (schema/rpc/contract/run.mjs --worker).
    add_executable(oymap_worker ${OYMAP_RPC_MODULE_SOURCES}
        ${CMAKE_CURRENT_SOURCE_DIR}/wasm/RpcModule.cpp)
    target_link_libraries(oymap_worker PRIVATE oymap_core)
    if (OYMAP_WASM_MALLOC STREQUAL "mimalloc")
        target_compile_definitions(oymap_worker PRIVATE OYMAP_MIMALLOC)
    endif()
    set_target_properties(oymap_worker PROPERTIES SUFFIX ".mjs")
    target_link_options(oymap_worker PRIVATE
        -sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=4MB -sMODULARIZE=1 -sEXPORT_ES6=1 -sEXPORT_NAME=createOymapCore
        -sENVIRONMENT=worker,node -sFORCE_FILESYSTEM=1 -lnodefs.js
        -sEXPORTED_FUNCTIONS=_oymap_call,_oymap_free,_oymap_unzstd,_oymap_heap,_malloc,_free
        -sEXPORTED_RUNTIME_METHODS=UTF8ToString,stringToNewUTF8,FS,HEAPU8,HEAPF64,NODEFS)
endif()

if (OYMAP_BUILD_TESTS AND NOT EMSCRIPTEN)
    file(GLOB OYMAP_TEST_SOURCES CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp)

    if (OYMAP_TEST_SOURCES)
        # The command line's files but its main: the request list's handlers (cli/Rpc.cpp) are tested in process.
        set(OYMAP_TEST_CLI_SOURCES ${OYMAP_CLI_SOURCES})
        list(FILTER OYMAP_TEST_CLI_SOURCES EXCLUDE REGEX "/main\\.cpp$")
        add_executable(oymap_tests ${OYMAP_TEST_SOURCES} ${OYMAP_TEST_CLI_SOURCES})
        target_include_directories(oymap_tests PRIVATE ${OYMAP_DOCTEST_INCLUDE_DIR})
        target_link_libraries(oymap_tests PRIVATE oymap_core)
    endif()
endif()
