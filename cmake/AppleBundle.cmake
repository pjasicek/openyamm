include_guard(GLOBAL)

set(OPENYAMM_APPLE_BUNDLE_IDENTIFIER "io.github.openyamm.OpenYAMM" CACHE STRING
    "Bundle identifier of OpenYAMM.app. Device builds need one that the signing team's provisioning profile allows.")

# Builds the game as OpenYAMM.app. The runtime shaders and the icon are bundle resources (Contents/Resources on macOS,
# the bundle root on iOS), the directory SDL_GetBasePath() returns inside a bundle. The bundle carries no settings.ini:
# the defaults are built in, and the game keeps the player's choices in its per-user folder.
function(openyamm_configure_apple_bundle target)
    set_target_properties(${target} PROPERTIES
        MACOSX_BUNDLE TRUE
        OUTPUT_NAME "OpenYAMM"
        MACOSX_BUNDLE_BUNDLE_NAME "OpenYAMM"
        MACOSX_BUNDLE_GUI_IDENTIFIER "${OPENYAMM_APPLE_BUNDLE_IDENTIFIER}"
        MACOSX_BUNDLE_SHORT_VERSION_STRING "${PROJECT_VERSION}"
        MACOSX_BUNDLE_BUNDLE_VERSION "${PROJECT_VERSION}"
    )

    set(resourceLocation "Resources")
    if (IOS)
        # iOS bundles are flat: resources sit next to the executable.
        set(resourceLocation ".")
        # Info-iOS.plist.in is configured in the scope that creates the target.
        if (CMAKE_OSX_SYSROOT MATCHES "[Ss]imulator")
            set(OPENYAMM_IOS_BUNDLE_PLATFORM "iPhoneSimulator" PARENT_SCOPE)
        else()
            set(OPENYAMM_IOS_BUNDLE_PLATFORM "iPhoneOS" PARENT_SCOPE)
        endif()
        set_target_properties(${target} PROPERTIES
            MACOSX_BUNDLE_INFO_PLIST "${CMAKE_SOURCE_DIR}/packaging/apple/Info-iOS.plist.in"
        )
    endif()

    # Shaders are bundle resources rather than a post-build copy, so a shader-only change updates the app too.
    get_property(shaderOutputs GLOBAL PROPERTY OPENYAMM_RUNTIME_SHADER_OUTPUTS)
    foreach(shaderOutput IN LISTS shaderOutputs)
        get_filename_component(shaderDirectory "${shaderOutput}" DIRECTORY)
        get_filename_component(shaderBackend "${shaderDirectory}" NAME)
        set_source_files_properties("${shaderOutput}" PROPERTIES
            GENERATED TRUE
            MACOSX_PACKAGE_LOCATION "${resourceLocation}/runtime/shaders/${shaderBackend}"
        )
    endforeach()
    target_sources(${target} PRIVATE ${shaderOutputs})
    add_dependencies(${target} openyamm_runtime_shaders)

    # The icon is assembled from the exported Linux icon sizes (tools/generate_app_icons.py).
    set(iconSourceDir "${CMAKE_SOURCE_DIR}/packaging/icons/hicolor")
    set(iconName "io.github.openyamm.OpenYAMM.png")
    if (IOS)
        find_program(openyammSips sips REQUIRED)
        set(iconInput "${iconSourceDir}/256x256/apps/${iconName}")
        set(iconFiles)
        foreach(iconEntry IN ITEMS "AppIcon60x60@2x.png:120" "AppIcon60x60@3x.png:180"
            "AppIcon76x76@2x~ipad.png:152" "AppIcon83.5x83.5@2x~ipad.png:167")
            string(REPLACE ":" ";" iconEntry "${iconEntry}")
            list(GET iconEntry 0 iconFileName)
            list(GET iconEntry 1 iconSize)
            set(iconFile "${CMAKE_CURRENT_BINARY_DIR}/apple-bundle/${iconFileName}")
            add_custom_command(
                OUTPUT "${iconFile}"
                COMMAND "${openyammSips}" --resampleHeightWidth ${iconSize} ${iconSize} "${iconInput}"
                    --out "${iconFile}"
                DEPENDS "${iconInput}"
                VERBATIM
            )
            list(APPEND iconFiles "${iconFile}")
        endforeach()
        set_source_files_properties(${iconFiles} PROPERTIES
            GENERATED TRUE
            MACOSX_PACKAGE_LOCATION "${resourceLocation}"
        )
        target_sources(${target} PRIVATE ${iconFiles})
        return()
    endif()

    find_program(openyammIconutil iconutil REQUIRED)
    set(iconsetDir "${CMAKE_CURRENT_BINARY_DIR}/apple-bundle/OpenYAMM.iconset")
    set(iconFile "${CMAKE_CURRENT_BINARY_DIR}/apple-bundle/OpenYAMM.icns")
    set(iconsetCommands)
    set(iconsetInputs)
    foreach(iconEntry IN ITEMS
        "16x16:16x16" "16x16@2x:32x32" "32x32:32x32" "32x32@2x:64x64" "128x128:128x128" "128x128@2x:256x256"
        "256x256:256x256" "256x256@2x:512x512" "512x512:512x512")
        string(REPLACE ":" ";" iconEntry "${iconEntry}")
        list(GET iconEntry 0 iconSlot)
        list(GET iconEntry 1 iconSize)
        set(iconInput "${iconSourceDir}/${iconSize}/apps/${iconName}")
        list(APPEND iconsetInputs "${iconInput}")
        list(APPEND iconsetCommands
            COMMAND "${CMAKE_COMMAND}" -E copy "${iconInput}" "${iconsetDir}/icon_${iconSlot}.png")
    endforeach()
    add_custom_command(
        OUTPUT "${iconFile}"
        COMMAND "${CMAKE_COMMAND}" -E rm -rf "${iconsetDir}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${iconsetDir}"
        ${iconsetCommands}
        COMMAND "${openyammIconutil}" --convert icns --output "${iconFile}" "${iconsetDir}"
        DEPENDS ${iconsetInputs}
        COMMENT "Creating the macOS application icon"
        VERBATIM
    )
    set_source_files_properties("${iconFile}" PROPERTIES GENERATED TRUE MACOSX_PACKAGE_LOCATION "${resourceLocation}")
    target_sources(${target} PRIVATE "${iconFile}")
    set_target_properties(${target} PROPERTIES MACOSX_BUNDLE_ICON_FILE "OpenYAMM.icns")
endfunction()
