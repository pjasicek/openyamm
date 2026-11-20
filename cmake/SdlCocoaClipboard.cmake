include_guard(GLOBAL)

# SDL 3.4.2's Cocoa GetMimeTypes reads the pasteboard item types twice: once to size a buffer, once to fill it. A
# clipboard change in between (another app copying) writes past the buffer or leaves pointers unset. Instead of
# patching the SDL checkout, which may be shared between builds, compile a generated copy of SDL_cocoaclipboard.m whose
# GetMimeTypes takes one snapshot (patches/SdlCocoaClipboardSnapshot.m.in). The source hash pins it to SDL 3.4.2.
function(openyamm_patch_sdl3_cocoa_clipboard)
    if (NOT APPLE OR IOS)
        return()
    endif()

    foreach(sdlTarget IN ITEMS SDL3-static SDL3-shared)
        if (NOT TARGET ${sdlTarget})
            continue()
        endif()

        get_target_property(sdlSources ${sdlTarget} SOURCES)
        foreach(sdlSource IN LISTS sdlSources)
            if (NOT sdlSource MATCHES "/src/video/cocoa/SDL_cocoaclipboard\\.m$")
                continue()
            endif()

            file(SHA256 "${sdlSource}" clipboardHash)
            if (NOT clipboardHash STREQUAL "2f54eccdcfba2516e621f20914b2d065f59e6a9501baaede23bae2db594c7450")
                message(FATAL_ERROR "SDL Cocoa clipboard source changed. "
                    "Review or remove the SDL 3.4.2 snapshot patch before upgrading SDL.")
            endif()

            file(READ "${sdlSource}" clipboardSource)
            file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/patches/SdlCocoaClipboardSnapshot.m.in" snapshotFunction)
            string(FIND "${clipboardSource}" "static char **GetMimeTypes(int *pnformats)" functionStart)
            string(FIND "${clipboardSource}" "void Cocoa_CheckClipboardUpdate(" functionEnd)
            if (functionStart LESS 0 OR functionEnd LESS functionStart)
                message(FATAL_ERROR "Could not locate the pinned SDL Cocoa clipboard function")
            endif()

            string(SUBSTRING "${clipboardSource}" 0 ${functionStart} sourcePrefix)
            string(SUBSTRING "${clipboardSource}" ${functionEnd} -1 sourceSuffix)
            set(patchedSource "${sourcePrefix}${snapshotFunction}\n\n${sourceSuffix}")
            get_filename_component(cocoaDirectory "${sdlSource}" DIRECTORY)
            string(REPLACE "#include \"SDL_cocoavideo.h\""
                "#include \"${cocoaDirectory}/SDL_cocoavideo.h\"" patchedSource "${patchedSource}")
            string(REPLACE "#include \"../../events/"
                "#include \"${cocoaDirectory}/../../events/" patchedSource "${patchedSource}")

            set(patchedPath "${CMAKE_BINARY_DIR}/openyamm-sdl-cocoa/SDL_cocoaclipboard.m")
            file(CONFIGURE OUTPUT "${patchedPath}" CONTENT "${patchedSource}" @ONLY)
            foreach(sourceProperty IN ITEMS COMPILE_FLAGS SKIP_PRECOMPILE_HEADERS)
                get_source_file_property(sourcePropertyValue "${sdlSource}"
                    TARGET_DIRECTORY ${sdlTarget} ${sourceProperty})
                if (NOT sourcePropertyValue STREQUAL "NOTFOUND")
                    set_source_files_properties("${patchedPath}" TARGET_DIRECTORY ${sdlTarget}
                        PROPERTIES ${sourceProperty} "${sourcePropertyValue}")
                endif()
            endforeach()
            list(REMOVE_ITEM sdlSources "${sdlSource}")
            list(APPEND sdlSources "${patchedPath}")
            set_property(TARGET ${sdlTarget} PROPERTY SOURCES "${sdlSources}")
            set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                "${sdlSource}"
                "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/patches/SdlCocoaClipboardSnapshot.m.in")
            message(STATUS "SDL Cocoa clipboard: using a single encoded format snapshot")
            break()
        endforeach()
    endforeach()
endfunction()
