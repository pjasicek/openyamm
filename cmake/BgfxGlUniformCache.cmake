include_guard(GLOBAL)

# Apply to populated trees too: FetchContent PATCH_COMMAND alone misses existing builds.
function(openyamm_patch_bgfx_gl_uniform_cache sourceDirectory)
    find_package(Git REQUIRED)
    set(patchFile "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/patches/bgfx-gl-uniform-cache.patch")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${patchFile}")
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" apply --check "${patchFile}"
        WORKING_DIRECTORY "${sourceDirectory}"
        RESULT_VARIABLE patchCheck OUTPUT_QUIET ERROR_QUIET
    )
    if (patchCheck EQUAL 0)
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" apply "${patchFile}"
            WORKING_DIRECTORY "${sourceDirectory}"
            RESULT_VARIABLE patchResult ERROR_VARIABLE patchError
        )
        if (NOT patchResult EQUAL 0)
            message(FATAL_ERROR "Cannot apply bgfx GL uniform cache patch: ${patchError}")
        endif()
    else()
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" apply --reverse --check "${patchFile}"
            WORKING_DIRECTORY "${sourceDirectory}"
            RESULT_VARIABLE reverseCheck OUTPUT_QUIET ERROR_QUIET
        )
        if (NOT reverseCheck EQUAL 0)
            message(FATAL_ERROR "bgfx source does not match the pinned GL uniform cache patch: ${sourceDirectory}")
        endif()
    endif()
endfunction()
