# Cross-compiles the Windows x64 release from Linux with Ubuntu's MinGW-w64 GCC (POSIX thread model).
# Used by the release workflow (.github/workflows/packages.yml); needs a host shaderc build, and a host sprite atlas
# cooker for packages that pack assets_dev:
#   -DOPENYAMM_HOST_SHADERC=<host build>/openyamm_shaderc
#   -DOPENYAMM_HOST_SPRITE_ATLAS_COOK=<host build>/game/openyamm_sprite_atlas_cook
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

set(openyammMingwPrefix x86_64-w64-mingw32)

set(CMAKE_C_COMPILER ${openyammMingwPrefix}-gcc-posix)
set(CMAKE_CXX_COMPILER ${openyammMingwPrefix}-g++-posix)
set(CMAKE_RC_COMPILER ${openyammMingwPrefix}-windres)
set(CMAKE_AR ${openyammMingwPrefix}-ar CACHE FILEPATH "")
set(CMAKE_RANLIB ${openyammMingwPrefix}-ranlib CACHE FILEPATH "")
set(CMAKE_NM ${openyammMingwPrefix}-nm CACHE FILEPATH "")
set(CMAKE_STRIP ${openyammMingwPrefix}-strip CACHE FILEPATH "")
set(CMAKE_OBJDUMP ${openyammMingwPrefix}-objdump CACHE FILEPATH "")

set(CMAKE_FIND_ROOT_PATH /usr/${openyammMingwPrefix})
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Link libgcc, libstdc++ and winpthread statically: the package then needs only Windows system DLLs.
set(CMAKE_EXE_LINKER_FLAGS_INIT "-static")
