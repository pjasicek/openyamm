include_guard(GLOBAL)

# Use the compiler sources and generated tables shipped with our pinned bgfx revision.
# Mixing system glslang/SPIRV-Tools versions with shaderc can change its reflection ABI.
function(openyamm_configure_spirv_compiler)
    set(compilerRoot "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty")
    set(spirvToolsRoot "${compilerRoot}/spirv-tools")
    file(GLOB spirvToolsSources CONFIGURE_DEPENDS
        "${spirvToolsRoot}/source/*.cpp"
        "${spirvToolsRoot}/source/opt/*.cpp"
        "${spirvToolsRoot}/source/val/*.cpp"
        "${spirvToolsRoot}/source/reduce/*.cpp"
        "${spirvToolsRoot}/source/util/*.cpp"
    )
    list(FILTER spirvToolsSources EXCLUDE REGEX "/(pch_source|mimalloc)\\.cpp$")
    add_library(openyamm_spirv_tools STATIC ${spirvToolsSources})
    target_include_directories(openyamm_spirv_tools
        PUBLIC "${spirvToolsRoot}/include"
        PRIVATE
            "${spirvToolsRoot}"
            "${spirvToolsRoot}/source"
            "${spirvToolsRoot}/include/generated"
            "${compilerRoot}/spirv-headers/include"
    )

    set(glslangRoot "${compilerRoot}/glslang")
    file(GLOB_RECURSE glslangSources CONFIGURE_DEPENDS
        "${glslangRoot}/glslang/*.cpp"
        "${glslangRoot}/SPIRV/*.cpp"
    )
    if (WIN32)
        list(FILTER glslangSources EXCLUDE REGEX "/OSDependent/Unix/")
    else()
        list(FILTER glslangSources EXCLUDE REGEX "/OSDependent/Windows/")
    endif()
    add_library(openyamm_glslang STATIC ${glslangSources})
    target_compile_definitions(openyamm_glslang PRIVATE ENABLE_OPT=1 ENABLE_HLSL=1)
    target_include_directories(openyamm_glslang
        PUBLIC "${glslangRoot}" "${glslangRoot}/glslang/Public" "${glslangRoot}/glslang/Include"
        PRIVATE "${compilerRoot}"
    )
    target_link_libraries(openyamm_glslang PUBLIC openyamm_spirv_tools)
    if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(openyamm_glslang PRIVATE -fno-strict-aliasing)
    endif()

    file(GLOB spirvCrossSources CONFIGURE_DEPENDS "${compilerRoot}/spirv-cross/spirv_*.cpp")
    add_library(openyamm_spirv_cross STATIC ${spirvCrossSources})
    target_compile_definitions(openyamm_spirv_cross PRIVATE SPIRV_CROSS_EXCEPTIONS_TO_ASSERTIONS)
    target_include_directories(openyamm_spirv_cross PUBLIC
        "${compilerRoot}/spirv-cross"
        "${compilerRoot}/spirv-cross/include"
    )

    target_sources(openyamm_shaderc PRIVATE "${OPENYAMM_BGFX_SOURCE_DIR}/tools/shaderc/shaderc_spirv.cpp")
    target_compile_definitions(openyamm_shaderc PRIVATE OPENYAMM_SHADERC_ENABLE_SPIRV=1 SHADERC_CONFIG_HAS_GLSLANG=1)
    target_link_libraries(openyamm_shaderc PRIVATE openyamm_glslang openyamm_spirv_cross)
endfunction()
