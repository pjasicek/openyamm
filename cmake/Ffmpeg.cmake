include_guard(GLOBAL)

function(openyamm_configure_ffmpeg)
    if (TARGET openyamm_ffmpeg_build)
        return()
    endif()

    if (NOT DEFINED OPENYAMM_FFMPEG_SOURCE_DIR OR OPENYAMM_FFMPEG_SOURCE_DIR STREQUAL "")
        set(OPENYAMM_FFMPEG_SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-src")
    endif()

    set(OPENYAMM_FFMPEG_BUILD_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-build")
    set(OPENYAMM_FFMPEG_INSTALL_DIR "${CMAKE_BINARY_DIR}/_deps/ffmpeg-install")
    set(OPENYAMM_FFMPEG_INCLUDE_DIR "${OPENYAMM_FFMPEG_INSTALL_DIR}/include")
    set(OPENYAMM_FFMPEG_LIBAVFORMAT "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavformat.a")
    set(OPENYAMM_FFMPEG_LIBAVCODEC "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavcodec.a")
    set(OPENYAMM_FFMPEG_LIBSWRESAMPLE "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libswresample.a")
    set(OPENYAMM_FFMPEG_LIBSWSCALE "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libswscale.a")
    set(OPENYAMM_FFMPEG_LIBAVUTIL "${OPENYAMM_FFMPEG_INSTALL_DIR}/lib/libavutil.a")

    add_custom_command(
        OUTPUT
            "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
            "${OPENYAMM_FFMPEG_LIBAVCODEC}"
            "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
            "${OPENYAMM_FFMPEG_LIBSWSCALE}"
            "${OPENYAMM_FFMPEG_LIBAVUTIL}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${OPENYAMM_FFMPEG_BUILD_DIR}"
        COMMAND bash "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
            --prefix=${OPENYAMM_FFMPEG_INSTALL_DIR}
            --disable-programs
            --disable-doc
            --disable-network
            --disable-autodetect
            --disable-everything
            --disable-asm
            --disable-avdevice
            --disable-avfilter
            --enable-static
            --disable-shared
            --enable-avcodec
            --enable-avformat
            --enable-avutil
            --enable-swresample
            --enable-swscale
            --enable-protocol=file
            --enable-demuxer=ogg
            --enable-demuxer=mp3
            --enable-decoder=theora
            --enable-decoder=vorbis
            --enable-decoder=mp3
            --enable-decoder=mp3float
            --enable-parser=vorbis
            --enable-parser=mpegaudio
        COMMAND ${CMAKE_MAKE_PROGRAM} -j4
        COMMAND ${CMAKE_MAKE_PROGRAM} install
        WORKING_DIRECTORY "${OPENYAMM_FFMPEG_BUILD_DIR}"
        DEPENDS "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
        COMMENT "Building bundled FFmpeg static libraries for house video playback"
        VERBATIM
    )

    add_custom_target(openyamm_ffmpeg_build
        DEPENDS
            "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
            "${OPENYAMM_FFMPEG_LIBAVCODEC}"
            "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
            "${OPENYAMM_FFMPEG_LIBSWSCALE}"
            "${OPENYAMM_FFMPEG_LIBAVUTIL}"
    )

    set(OPENYAMM_FFMPEG_INCLUDE_DIR "${OPENYAMM_FFMPEG_INCLUDE_DIR}" PARENT_SCOPE)
    set(OPENYAMM_FFMPEG_LIBAVFORMAT "${OPENYAMM_FFMPEG_LIBAVFORMAT}" PARENT_SCOPE)
    set(OPENYAMM_FFMPEG_LIBAVCODEC "${OPENYAMM_FFMPEG_LIBAVCODEC}" PARENT_SCOPE)
    set(OPENYAMM_FFMPEG_LIBSWRESAMPLE "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}" PARENT_SCOPE)
    set(OPENYAMM_FFMPEG_LIBSWSCALE "${OPENYAMM_FFMPEG_LIBSWSCALE}" PARENT_SCOPE)
    set(OPENYAMM_FFMPEG_LIBAVUTIL "${OPENYAMM_FFMPEG_LIBAVUTIL}" PARENT_SCOPE)
endfunction()

function(openyamm_target_link_ffmpeg targetName)
    target_include_directories(${targetName}
        PRIVATE
            "${OPENYAMM_FFMPEG_INCLUDE_DIR}"
    )

    target_link_libraries(${targetName}
        PRIVATE
            "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
            "${OPENYAMM_FFMPEG_LIBAVCODEC}"
            "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
            "${OPENYAMM_FFMPEG_LIBSWSCALE}"
            "${OPENYAMM_FFMPEG_LIBAVUTIL}"
    )

    add_dependencies(${targetName} openyamm_ffmpeg_build)
endfunction()
