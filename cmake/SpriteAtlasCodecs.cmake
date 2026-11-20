include_guard(GLOBAL)
include(FetchContent)

# Portable Zstandard support is shared by the runtime container reader and host cooker.
set(ZSTD_BUILD_PROGRAMS OFF CACHE BOOL "" FORCE)
set(ZSTD_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(ZSTD_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(ZSTD_BUILD_STATIC ON CACHE BOOL "" FORCE)
set(ZSTD_LEGACY_SUPPORT OFF CACHE BOOL "" FORCE)
set(ZSTD_MULTITHREAD_SUPPORT OFF CACHE BOOL "" FORCE)
FetchContent_Declare(openyamm_zstd
    URL https://codeload.github.com/facebook/zstd/tar.gz/refs/tags/v1.5.7
    URL_HASH SHA256=37d7284556b20954e56e1ca85b80226768902e2edabd3b649e9e72c0c9012ee3
    SOURCE_SUBDIR build/cmake)
FetchContent_MakeAvailable(openyamm_zstd)
# Link the library into the game; do not build or install zstd's own programs and archives.
set_property(DIRECTORY "${openyamm_zstd_SOURCE_DIR}/build/cmake" PROPERTY EXCLUDE_FROM_ALL TRUE)

if (NOT CMAKE_CROSSCOMPILING)
    find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
    # Build just the portable encoders, without etcpak's application, Tracy or native CPU flags.
    FetchContent_Declare(openyamm_etcpak
        URL https://codeload.github.com/wolfpld/etcpak/tar.gz/3d716e1550023dc5ff8b602636af8b76584e0b66
        URL_HASH SHA256=f15d027ad7ca6e924cb017d97245c88e1313da952b3a193f9020bab6f849d7c1)
    openyamm_populate_dependency(openyamm_etcpak etcpakSourceDir)
    add_library(openyamm_atlas_encoders STATIC EXCLUDE_FROM_ALL
        ${etcpakSourceDir}/bc7enc.cpp
        ${etcpakSourceDir}/bcdec.c
        ${etcpakSourceDir}/Decode.cpp
        ${etcpakSourceDir}/Dither.cpp
        ${etcpakSourceDir}/ProcessDxtc.cpp
        ${etcpakSourceDir}/ProcessRGB.cpp
        ${etcpakSourceDir}/Tables.cpp)
    target_include_directories(openyamm_atlas_encoders PUBLIC ${etcpakSourceDir})
    target_compile_features(openyamm_atlas_encoders PRIVATE cxx_std_20)
    FetchContent_Declare(openyamm_etc2comp
        URL https://codeload.github.com/google/etc2comp/tar.gz/39422c1aa2f4889d636db5790af1d0be6ff3a226
        URL_HASH SHA256=e28adc618f29cbfbfba201049de0bdd9ed6cd205a6b7eaa91b3cf0a95b0172bc)
    openyamm_populate_dependency(openyamm_etc2comp etc2SourceDir)
    file(GLOB etc2Sources CONFIGURE_DEPENDS ${etc2SourceDir}/EtcLib/Etc/*.cpp ${etc2SourceDir}/EtcLib/EtcCodec/*.cpp)
    target_sources(openyamm_atlas_encoders PRIVATE ${etc2Sources})
    target_include_directories(openyamm_atlas_encoders PUBLIC ${etc2SourceDir}/EtcLib/Etc
        ${etc2SourceDir}/EtcLib/EtcCodec)
endif()
