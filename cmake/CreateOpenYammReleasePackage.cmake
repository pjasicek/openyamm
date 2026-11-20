if (POLICY CMP0207)
    cmake_policy(SET CMP0207 NEW)
endif()

if (NOT DEFINED OPENYAMM_RELEASE_STAGE_DIR OR OPENYAMM_RELEASE_STAGE_DIR STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_STAGE_DIR is required")
endif()

if (NOT DEFINED OPENYAMM_RELEASE_ARCHIVE_PATH OR OPENYAMM_RELEASE_ARCHIVE_PATH STREQUAL "")
    message(FATAL_ERROR "OPENYAMM_RELEASE_ARCHIVE_PATH is required")
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

file(REMOVE_RECURSE "${OPENYAMM_RELEASE_STAGE_DIR}")
file(REMOVE "${OPENYAMM_RELEASE_ARCHIVE_PATH}")

# With a launcher, the package is a versioned installation (packaging/UPDATER_PLAN.md 9.1): OpenYAMM[.exe] starts
# app/<version>/openyamm[.exe], whose index.json mounts the shared packs in assets/packs. Extracting this package and
# updating to its version produce the same tree.
if (DEFINED OPENYAMM_RELEASE_LAUNCHER AND NOT OPENYAMM_RELEASE_LAUNCHER STREQUAL "")
    if (NOT OPENYAMM_RELEASE_VERSION MATCHES "^[A-Za-z0-9][A-Za-z0-9.-]*$")
        message(FATAL_ERROR "OPENYAMM_RELEASE_VERSION must name the version folder, not '${OPENYAMM_RELEASE_VERSION}'")
    endif()
    set(openyammReleaseAppDir "${OPENYAMM_RELEASE_STAGE_DIR}/app/${OPENYAMM_RELEASE_VERSION}")
    get_filename_component(openyammReleaseLauncherName "${OPENYAMM_RELEASE_LAUNCHER}" NAME)
    get_filename_component(openyammReleaseLauncherSuffix "${OPENYAMM_RELEASE_LAUNCHER}" LAST_EXT)
    file(MAKE_DIRECTORY "${openyammReleaseAppDir}")
    file(COPY "${OPENYAMM_RELEASE_LAUNCHER}" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}")
    # The game installs this copy as the launcher after its first successful start.
    file(COPY "${OPENYAMM_RELEASE_LAUNCHER}" DESTINATION "${openyammReleaseAppDir}")
    file(RENAME "${openyammReleaseAppDir}/${openyammReleaseLauncherName}"
        "${openyammReleaseAppDir}/OpenYAMM-launcher${openyammReleaseLauncherSuffix}")
    file(WRITE "${OPENYAMM_RELEASE_STAGE_DIR}/app/current" "${OPENYAMM_RELEASE_VERSION}\n")
else()
    set(openyammReleaseAppDir "${OPENYAMM_RELEASE_STAGE_DIR}")
endif()

file(MAKE_DIRECTORY "${OPENYAMM_RELEASE_STAGE_DIR}/assets")

if (DEFINED OPENYAMM_RELEASE_BUNDLE AND NOT OPENYAMM_RELEASE_BUNDLE STREQUAL "")
    # macOS: the game is OpenYAMM.app with its shaders inside. The ad-hoc signature seals the copied bundle (the
    # linker signs only the executable); macOS refuses to open a downloaded bundle whose seal is broken.
    file(COPY "${OPENYAMM_RELEASE_BUNDLE}" DESTINATION "${openyammReleaseAppDir}")
    get_filename_component(openyammReleaseBundleName "${OPENYAMM_RELEASE_BUNDLE}" NAME)
    execute_process(
        COMMAND "${OPENYAMM_RELEASE_CODESIGN}" --force --sign - "${openyammReleaseAppDir}/${openyammReleaseBundleName}"
        RESULT_VARIABLE codesignResult
    )
    if (NOT codesignResult EQUAL 0)
        message(FATAL_ERROR "Failed to sign ${openyammReleaseBundleName}")
    endif()
else()
    file(MAKE_DIRECTORY "${openyammReleaseAppDir}/runtime")
    file(COPY "${OPENYAMM_RELEASE_EXECUTABLE}" DESTINATION "${openyammReleaseAppDir}")
    file(COPY "${OPENYAMM_RELEASE_SHADER_DIR}" DESTINATION "${openyammReleaseAppDir}/runtime"
        PATTERN "dxbc" EXCLUDE
    )
endif()
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
            file(COPY "${runtimeDll}" DESTINATION "${openyammReleaseAppDir}")
            get_filename_component(runtimeDllDir "${runtimeDll}" DIRECTORY)
            list(APPEND openyammReleaseRuntimeDependencyDirs "${runtimeDllDir}")
        endif()
    endforeach()
endif()

if (DEFINED OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS AND NOT OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS STREQUAL "")
    string(REPLACE "|" ";" systemRuntimeDlls "${OPENYAMM_RELEASE_SYSTEM_RUNTIME_DLLS}")

    foreach(systemRuntimeDll IN LISTS systemRuntimeDlls)
        if (EXISTS "${systemRuntimeDll}")
            file(COPY "${systemRuntimeDll}" DESTINATION "${openyammReleaseAppDir}")
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
            file(COPY "${resolvedRuntimeDependency}" DESTINATION "${openyammReleaseAppDir}")
        endif()
    endforeach()

    if (unresolvedRuntimeDependencies)
        message(WARNING "Unresolved runtime dependencies: ${unresolvedRuntimeDependencies}")
    endif()
endif()

if (OPENYAMM_RELEASE_THIN)
    # The small download package (packaging/UPDATER_PLAN.md 9.1): the game downloads its packs on the first start. The index
    # comes from prebuilt content when given; release builds add it later (packaging/publish_release.py assemble).
    if (DEFINED OPENYAMM_RELEASE_CONTENT_DIR AND NOT OPENYAMM_RELEASE_CONTENT_DIR STREQUAL "")
        file(COPY "${OPENYAMM_RELEASE_CONTENT_DIR}/index.json" DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}/assets")
    endif()
elseif (DEFINED OPENYAMM_RELEASE_CONTENT_DIR AND NOT OPENYAMM_RELEASE_CONTENT_DIR STREQUAL "")
    # Content packed once (tools/package_runtime_assets.py), shared with the other packages.
    if (NOT EXISTS "${OPENYAMM_RELEASE_CONTENT_DIR}/index.json"
        OR NOT IS_DIRECTORY "${OPENYAMM_RELEASE_CONTENT_DIR}/packs")
        message(FATAL_ERROR "Prebuilt content lacks index.json or packs/: ${OPENYAMM_RELEASE_CONTENT_DIR}")
    endif()
    file(COPY "${OPENYAMM_RELEASE_CONTENT_DIR}/index.json" "${OPENYAMM_RELEASE_CONTENT_DIR}/packs"
        DESTINATION "${OPENYAMM_RELEASE_STAGE_DIR}/assets")
else()
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
endif()

if (NOT openyammReleaseAppDir STREQUAL OPENYAMM_RELEASE_STAGE_DIR
    AND EXISTS "${OPENYAMM_RELEASE_STAGE_DIR}/assets/index.json")
    # The index belongs to its version; the packs are shared by all versions.
    file(READ "${OPENYAMM_RELEASE_STAGE_DIR}/assets/index.json" openyammReleaseIndex)
    string(JSON openyammReleaseIndex SET "${openyammReleaseIndex}" store "\"../../assets/packs\"")
    file(WRITE "${openyammReleaseAppDir}/index.json" "${openyammReleaseIndex}\n")
    file(REMOVE "${OPENYAMM_RELEASE_STAGE_DIR}/assets/index.json")
endif()

get_filename_component(openyammReleaseParentDir "${OPENYAMM_RELEASE_STAGE_DIR}" DIRECTORY)
get_filename_component(openyammReleaseFolderName "${OPENYAMM_RELEASE_STAGE_DIR}" NAME)

if (DEFINED OPENYAMM_RELEASE_BUNDLE AND NOT OPENYAMM_RELEASE_BUNDLE STREQUAL "")
    # macOS players get a disk image: the signed OpenYAMM.app, unchanged (an added index would break its seal), with a
    # link to Applications to drag it to. On its first start the app installs its release into the per-user folder
    # (packaging/UPDATER_PLAN.md 9.4). packaging/publish_release.py publishes the image as it is.
    set(openyammReleaseImageDir "${openyammReleaseParentDir}/disk-image")
    file(REMOVE_RECURSE "${openyammReleaseImageDir}")
    file(MAKE_DIRECTORY "${openyammReleaseImageDir}")
    file(COPY "${openyammReleaseAppDir}/${openyammReleaseBundleName}"
        "${OPENYAMM_RELEASE_STAGE_DIR}/LICENSE" "${OPENYAMM_RELEASE_STAGE_DIR}/COPYRIGHT"
        DESTINATION "${openyammReleaseImageDir}")
    file(CREATE_LINK "/Applications" "${openyammReleaseImageDir}/Applications" SYMBOLIC)

    # hdiutil fails now and then with "Resource busy" on build machines; a second attempt succeeds.
    foreach(attempt RANGE 1 3)
        execute_process(
            COMMAND "${OPENYAMM_RELEASE_HDIUTIL}" create -volname OpenYAMM -srcfolder "${openyammReleaseImageDir}"
                -format UDZO -ov "${OPENYAMM_RELEASE_ARCHIVE_PATH}"
            RESULT_VARIABLE releaseArchiveResult
        )
        if (releaseArchiveResult EQUAL 0)
            break()
        endif()
        execute_process(COMMAND "${CMAKE_COMMAND}" -E sleep 5)
    endforeach()
    file(REMOVE_RECURSE "${openyammReleaseImageDir}")

    if (NOT releaseArchiveResult EQUAL 0)
        message(FATAL_ERROR "Failed to create the disk image: ${OPENYAMM_RELEASE_ARCHIVE_PATH}")
    endif()

    message(STATUS "Created OpenYAMM release package: ${OPENYAMM_RELEASE_ARCHIVE_PATH}")
    return()
endif()

# Windows players get a zip; Linux players a tar.gz, which keeps the executables' permissions.
if (OPENYAMM_RELEASE_ARCHIVE_PATH MATCHES "\\.tar\\.gz$")
    set(openyammReleaseTarArguments czf "${OPENYAMM_RELEASE_ARCHIVE_PATH}" --format=gnutar)
else()
    set(openyammReleaseTarArguments cf "${OPENYAMM_RELEASE_ARCHIVE_PATH}" --format=zip)
endif()

execute_process(
    COMMAND "${CMAKE_COMMAND}" -E tar ${openyammReleaseTarArguments} -- "${openyammReleaseFolderName}"
    WORKING_DIRECTORY "${openyammReleaseParentDir}"
    RESULT_VARIABLE releaseArchiveResult
)

if (NOT releaseArchiveResult EQUAL 0)
    message(FATAL_ERROR "Failed to create the release archive: ${OPENYAMM_RELEASE_ARCHIVE_PATH}")
endif()

message(STATUS "Created OpenYAMM release package: ${OPENYAMM_RELEASE_ARCHIVE_PATH}")
