include_guard(GLOBAL)

function(openyamm_bgfx_shader_platform outputVariable)
    if (WIN32)
        set(shaderPlatform "windows")
    elseif (APPLE)
        set(shaderPlatform "osx")
    else()
        set(shaderPlatform "linux")
    endif()

    set(${outputVariable} "${shaderPlatform}" PARENT_SCOPE)
endfunction()

function(openyamm_copy_runtime_shader sourcePath outputName)
    add_custom_command(
        OUTPUT "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/${outputName}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${sourcePath}"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/${outputName}"
        DEPENDS "${sourcePath}"
        VERBATIM
    )
endfunction()

function(openyamm_compile_bgfx_shader sourcePath shaderType outputName)
    openyamm_bgfx_shader_platform(shaderPlatform)

    add_custom_command(
        OUTPUT "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/${outputName}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl"
        COMMAND "$<TARGET_FILE:openyamm_shaderc>"
            --platform "${shaderPlatform}"
            -p 120
            --type "${shaderType}"
            --varyingdef "${CMAKE_SOURCE_DIR}/game/shaders/varying.def.sc"
            -i "${CMAKE_SOURCE_DIR}/game/shaders"
            -i "${OPENYAMM_BGFX_SOURCE_DIR}/src"
            -i "${OPENYAMM_BGFX_SOURCE_DIR}/examples/common"
            -f "${sourcePath}"
            -o "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/${outputName}"
        DEPENDS
            "${sourcePath}"
            "${CMAKE_SOURCE_DIR}/game/shaders/varying.def.sc"
            "${OPENYAMM_BGFX_SOURCE_DIR}/examples/common/common.sh"
            openyamm_shaderc
        VERBATIM
    )
endfunction()

function(openyamm_configure_bgfx_runtime)
    file(GLOB openyammAstcEncoderSources "${OPENYAMM_BIMG_SOURCE_DIR}/3rdparty/astc-encoder/source/*.cpp")

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
            ${openyammAstcEncoderSources}
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

    if (NOT TARGET openyamm_fcpp)
        add_library(openyamm_fcpp STATIC
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp1.c
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp2.c
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp3.c
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp4.c
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp5.c
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp/cpp6.c
        )

        target_include_directories(openyamm_fcpp PUBLIC ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp)
        target_compile_definitions(openyamm_fcpp PRIVATE
            NINCLUDE=64
            NWORK=65536
            NBUFF=65536
            OLD_PREPROCESSOR=0
        )

        if (UNIX AND NOT APPLE)
            target_compile_options(openyamm_fcpp PRIVATE
                -Wno-implicit-fallthrough
                -Wno-incompatible-pointer-types
                -Wno-parentheses-equality
            )
        endif()
    endif()

    if (NOT TARGET openyamm_glsl_optimizer)
        file(GLOB_RECURSE openyammGlslOptimizerSources
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/*.c"
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/*.cpp"
        )
        list(FILTER openyammGlslOptimizerSources EXCLUDE REGEX "/src/node/")
        list(REMOVE_ITEM openyammGlslOptimizerSources
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl/glcpp/glcpp.c"
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl/main.cpp"
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl/builtin_stubs.cpp"
            "${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl/ir_set_program_inouts.cpp"
        )

        add_library(openyamm_glsl_optimizer STATIC ${openyammGlslOptimizerSources})
        target_include_directories(openyamm_glsl_optimizer
            PUBLIC
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/include
            PRIVATE
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/mesa
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/mesa/main
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/mesa/program
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/mapi
                ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/util
        )

        if (UNIX AND NOT APPLE)
            target_compile_options(openyamm_glsl_optimizer PRIVATE
                -fno-strict-aliasing
                -Wno-implicit-fallthrough
                -Wno-parentheses
                -Wno-sign-compare
                -Wno-unused-function
                -Wno-unused-parameter
                -Wno-misleading-indentation
            )
        endif()
    endif()

    if (NOT TARGET openyamm_shaderc)
        add_executable(openyamm_shaderc
            ${OPENYAMM_BGFX_SOURCE_DIR}/tools/shaderc/shaderc.cpp
            ${OPENYAMM_BGFX_SOURCE_DIR}/tools/shaderc/shaderc_glsl.cpp
            ${CMAKE_SOURCE_DIR}/tools/openyamm_shaderc_stubs.cpp
        )
        target_include_directories(openyamm_shaderc PRIVATE
            ${OPENYAMM_BIMG_SOURCE_DIR}/include
            ${OPENYAMM_BGFX_SOURCE_DIR}/include
            ${OPENYAMM_BGFX_SOURCE_DIR}/tools/shaderc
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/directx-headers/include/directx
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/fcpp
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/include
            ${OPENYAMM_BGFX_SOURCE_DIR}/3rdparty/glsl-optimizer/src/glsl
        )
        target_link_libraries(openyamm_shaderc PRIVATE openyamm_bgfx openyamm_fcpp openyamm_glsl_optimizer)
    endif()
endfunction()

function(openyamm_configure_runtime_shaders)
    if (TARGET openyamm_runtime_shaders)
        return()
    endif()

    openyamm_copy_runtime_shader(
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/vs_cubes.bin"
        "vs_cubes.bin")
    openyamm_copy_runtime_shader(
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/fs_cubes.bin"
        "fs_cubes.bin")
    openyamm_copy_runtime_shader(
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/vs_shadowmaps_texture.bin"
        "vs_shadowmaps_texture.bin")
    openyamm_copy_runtime_shader(
        "${OPENYAMM_BGFX_SOURCE_DIR}/examples/runtime/shaders/glsl/fs_shadowmaps_texture.bin"
        "fs_shadowmaps_texture.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/vs_outdoor_textured_fog.sc"
        "vertex"
        "vs_outdoor_textured_fog.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/vs_outdoor_billboard_lit.sc"
        "vertex"
        "vs_outdoor_billboard_lit.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/fs_outdoor_textured_fog.sc"
        "fragment"
        "fs_outdoor_textured_fog.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/fs_outdoor_billboard_lit.sc"
        "fragment"
        "fs_outdoor_billboard_lit.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/vs_outdoor_force_perspective.sc"
        "vertex"
        "vs_outdoor_force_perspective.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/fs_outdoor_force_perspective.sc"
        "fragment"
        "fs_outdoor_force_perspective.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/vs_particle.sc"
        "vertex"
        "vs_particle.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/fs_particle.sc"
        "fragment"
        "fs_particle.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/vs_editor_preview_material.sc"
        "vertex"
        "vs_editor_preview_material.bin")
    openyamm_compile_bgfx_shader(
        "${CMAKE_SOURCE_DIR}/game/shaders/fs_editor_preview_material.sc"
        "fragment"
        "fs_editor_preview_material.bin")

    add_custom_target(openyamm_runtime_shaders ALL
        DEPENDS
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_cubes.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_cubes.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_shadowmaps_texture.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_shadowmaps_texture.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_outdoor_textured_fog.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_outdoor_billboard_lit.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_outdoor_textured_fog.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_outdoor_billboard_lit.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_outdoor_force_perspective.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_outdoor_force_perspective.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_particle.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_particle.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/vs_editor_preview_material.bin"
            "${OPENYAMM_RUNTIME_SHADER_DIR}/glsl/fs_editor_preview_material.bin"
    )
endfunction()
