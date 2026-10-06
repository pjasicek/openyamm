if (POLICY CMP0207)
    cmake_policy(SET CMP0207 NEW)
endif()

if (NOT DEFINED OPENYAMM_RELEASE_STAGE_DIR OR OPENYAMM_RELEASE_STAGE_DIR STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_STAGE_DIR is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_ZIP_PATH OR OPENYAMM_RELEASE_ZIP_PATH STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_ZIP_PATH is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_EXECUTABLE OR OPENYAMM_RELEASE_EXECUTABLE STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_EXECUTABLE is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_SHADER_DIR OR OPENYAMM_RELEASE_SHADER_DIR STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_SHADER_DIR is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_ASSET_DEV_DIR OR OPENYAMM_RELEASE_ASSET_DEV_DIR STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_ASSET_DEV_DIR is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_SETTINGS_TEMPLATE OR OPENYAMM_RELEASE_SETTINGS_TEMPLATE STREQUAL "")
    get_filename_component(openyammReleaseSourceDir "${OPENYAMM_RELEASE_ASSET_DEV_DIR}" DIRECTORY)
    set(OPENYAMM_RELEASE_SETTINGS_TEMPLATE "${openyammReleaseSourceDir}/settings_release.ini")
endif()


file(REMOVE_RECURSE "${OPENYAMM_RELEASE_STAGE_DIR}")
file(REMOVE "${OPENYAMM_RELEASE_ZIP_PATH}")

file(MAKE_DIRECTORY "${OPENYAMM_RELEASE_STAGE_DIR}")
file(MAKE_DIRECTORY "${OPENYAMM_RELEASE_STAGE_DIR}/assets/worlds")
file(MAKE_DIRECTORY "${OPENYAMM_RELEASE_STAGE_DIR}/runtime")

file(COPY "${OPENYAMM_RELEASE_EXECUTABLE}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}")
file(COPY "${OPENYAMM_RELEASE_SHADER_DIR}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}/runtime"
    PATTERN "dxbc" EXCLUDE
)
file(COPY
    "${CMAKE_CURRENT_LIST_DIR}/../LICENSE"
    "${CMAKE_CURRENT_LIST_DIR}/../COPYRIGHT"
    DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}"
)

set(openyammReleaseRuntimeDependencyDirs "")
get_filename_component(openyammReleaseExecutableDir "${OPENYAMM_RELEASE_EXECUTABLE}" DIRECTORY)
list(APPEND openyammReleaseRuntimeDependencyDirs "${openyammReleaseExecutableDir}")

if (DEFINED OPENYAMM_RELEASE_RUNTIME_DLLS AND NOT OPENYAMM_RELEASE_RUNTIME_DLLS STREQUAL "")
    string(REPLACE "|" ";" runtimeDlls "${OPENYAMM_RELEASE_RUNTIME_DLLS}")

    foreach(runtimeDll IN LISTS runtimeDlls)
        if (EXISTS "${runtimeDll}")
            file(COPY "${runtimeDll}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}")
            get_filename_component(runtimeDllDir "${runtimeDll}" DIRECTORY)
            list(APPEND openyammReleaseRuntimeDependencyDirs "${runtimeDllDir}")
        endif()
    endforeach()
endif()

if (DEFINED OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS AND NOT OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS STREQUAL "")
    string(REPLACE "|" ";" systemRuntimeDlls "${OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS}")

    foreach(systemRuntimeDll IN LISTS systemRuntimeDlls)
        if (EXISTS "${systemRuntimeDll}")
            file(COPY "${systemRuntimeDll}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}")
        endif()
    endforeach()
endif()

if (DEFINED OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS AND NOT OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS STREQUAL "")
    string(REPLACE "|" ";" runtimeSearchDirs "${OPENYAMM_RELEASE_RUNTIME_SEARCH_DIRS}")
    list(APPEND openyammReleaseRuntimeDependencyDirs ${runtimeSearchDirs})
endif()

list(REMOVE_DUPLICATES openyammReleaseRuntimeDependencyDirs)

if (DEFINED OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES AND OPENYAMM_RELEASE_COLLECT_RUNTIME_DEPENDENCIES)
    file(GET_RUNTIME_DEPENDENCIES
        EXECUTABLES "${OPENYAMM_RELEASE_EXECUTABLE}"
        DIRECTORIES ${openyammReleaseRuntimeDependencyDirs}
        PRE_EXCLUDE_REGEXES
            "api-ms-.*"
            "ext-ms-.*"
        POST_EXCLUDE_REGEXES
            "[/\\\\][Ww][Ii][Nn][Dd][Oo][Ww][Ss][/\\\\][Ss]ystem32[/\\\\].*"
            "[/\\\\][Ww][Ii][Nn][Dd][Oo][Ww][Ss][/\\\\][Ss]yswow64[/\\\\].*"
        RESOLVED_DEPENDENCIES_VAR resolvedRuntimeDependencies
        UNRESOLVED_DEPENDENCIES_VAR unresolvedRuntimeDependencies
    )

    foreach(resolvedRuntimeDependency IN LISTS resolvedRuntimeDependencies)
        if (EXISTS "${resolvedRuntimeDependency}")
            file(COPY "${resolvedRuntimeDependency}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}")
        endif()
    endforeach()

    if (unresolvedRuntimeDependencies)
        message(WARNING "Unresolved runtime dependencies: ${unresolvedRuntimeDependencies}")
    endif()
endif()

execute_process(
    COMMAND "${CMAKE_COMMAND}"
        "-DOPENYAMM_SETTINGS_TEMPLATE=${OPENYAMM_RELEASE_SETTINGS_TEMPLATE}"
        "-DOPENYAMM_SETTINGS_OUTPUT=${OPENYAMM_RELEASE_STAGE_DIR}/settings.ini"
        "-DOPENYAMM_SETTINGS_ASSET_ROOT=assets"
        -P "${CMAKE_CURRENT_LIST_DIR}/CreateOpenYammReleaseSettings.cmake"
    RESULT_VARIABLE openyammReleaseSettingsResult
)

if (NOT openyammReleaseSettingsResult EQUAL 0)
    message(FATAL_ERROR "Failed to create release settings.ini")
endif()

execute_process(
    COMMAND "${OPENYAMM_RELEASE_PYTHON}" "${CMAKE_CURRENT_LIST_DIR}/../tools/package_runtime_assets.py"
        --assets-root "${OPENYAMM_RELEASE_ASSET_DEV_DIR}"
        --output "${OPENYAMM_RELEASE_STAGE_DIR}/assets"
        --profile desktop --cooker "${OPENYAMM_RELEASE_COOKER}"
    RESULT_VARIABLE assetPackageResult
)
if (NOT assetPackageResult EQUAL 0)
    message(FATAL_ERROR "Runtime asset verification/packaging failed")
endif()

get_filename_component(openyammReleaseParentDir "${OPENYAMM_RELEASE_STAGE_DIR}" DIRECTORY)
get_filename_component(openyammReleaseFolderName "${OPENYAMM_RELEASE_STAGE_DIR}" NAME)

execute_process(
    COMMAND "${CMAKE_COMMAND}" -E tar cf "${OPENYAMM_RELEASE_ZIP_PATH}" --format=zip -- "${openyammReleaseFolderName}"
    WORKING_DIRECTORY "${openyammReleaseParentDir}"
    RESULT_VARIABLE releaseZipResult
)

if (NOT releaseZipResult EQUAL 0)
    message(FATAL_ERROR "Failed to create release zip: ${OPENYAMM_RELEASE_ZIP_PATH}")
endif()

message(STATUS "Created OpenYAMM release zip: ${OPENYAMM_RELEASE_ZIP_PATH}")
