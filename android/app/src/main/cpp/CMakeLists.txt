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
