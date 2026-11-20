get_filename_component(OPENYAMM_REPO_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../.." ABSOLUTE)

get_property(androidShaderNames GLOBAL PROPERTY OPENYAMM_RUNTIME_SHADER_NAMES)
if (NOT androidShaderNames)
    message(FATAL_ERROR "Android startup requires the configured runtime shader list.")
endif()
list(LENGTH androidShaderNames androidShaderCount)
set(androidShaderPaths "")
foreach(shaderName IN LISTS androidShaderNames)
    string(APPEND androidShaderPaths "    \"runtime/shaders/essl/${shaderName}\",\n")
endforeach()
configure_file(AndroidShaderPaths.h.in AndroidShaderPaths.h @ONLY)

# The APK packages exactly these shaders, from one folder per build type (android/app/build.gradle): the shader output
# folder keeps the outputs of removed shaders, and every native configuration has its own.
if (OPENYAMM_ANDROID_APK_SHADER_DIR)
    set(apkShaderDir "${OPENYAMM_ANDROID_APK_SHADER_DIR}/${ANDROID_ABI}/runtime/shaders/essl")
    set(apkShaderSources)
    foreach(shaderName IN LISTS androidShaderNames)
        list(APPEND apkShaderSources "${OPENYAMM_RUNTIME_SHADER_DIR}/essl/${shaderName}")
    endforeach()
    add_custom_command(
        OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/apk_shaders.stamp"
        COMMAND ${CMAKE_COMMAND} -E rm -rf "${apkShaderDir}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${apkShaderDir}"
        COMMAND ${CMAKE_COMMAND} -E copy ${apkShaderSources} "${apkShaderDir}"
        COMMAND ${CMAKE_COMMAND} -E touch "${CMAKE_CURRENT_BINARY_DIR}/apk_shaders.stamp"
        DEPENDS ${apkShaderSources}
        VERBATIM
    )
    add_custom_target(openyamm_apk_shaders DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/apk_shaders.stamp")
endif()

add_library(main SHARED
    openyamm_android_entry.cpp
)

target_include_directories(main
    PRIVATE
        "${OPENYAMM_REPO_ROOT}"
        "${CMAKE_CURRENT_BINARY_DIR}"
)

target_compile_features(main PRIVATE cxx_std_20)
target_link_libraries(main PRIVATE openyamm_game SDL3::SDL3 log android)
# Gradle builds only the libraries.
if (TARGET openyamm_apk_shaders)
    add_dependencies(main openyamm_apk_shaders)
endif()
