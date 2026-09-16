include_guard(GLOBAL)

function(openyamm_configure_ffmpeg)
    if (TARGET openyamm_ffmpeg_build)
        return()
    endif()

    find_program(OPENYAMM_FFMPEG_MAKE_PROGRAM make REQUIRED)

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

    set(openyammFfmpegConfigureArgs
        --prefix=${OPENYAMM_FFMPEG_INSTALL_DIR}
        --disable-programs
        --disable-doc
        --disable-network
        --disable-autodetect
        --disable-everything
        --disable-asm
        --disable-avdevice
        --disable-avfilter
        --disable-iconv
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
        --enable-demuxer=wav
        --enable-decoder=theora
        --enable-decoder=vorbis
        --enable-decoder=mp3
        --enable-decoder=mp3float
        --enable-decoder=adpcm_ima_wav
        --enable-parser=vorbis
        --enable-parser=mpegaudio
    )

    if (ANDROID)
        if (CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
            set(openyammFfmpegArch "aarch64")
            set(openyammFfmpegCompilerPrefix "aarch64-linux-android")
        elseif (CMAKE_ANDROID_ARCH_ABI STREQUAL "x86_64")
            set(openyammFfmpegArch "x86_64")
            set(openyammFfmpegCompilerPrefix "x86_64-linux-android")
        else()
            message(FATAL_ERROR "Unsupported Android ABI for FFmpeg: ${CMAKE_ANDROID_ARCH_ABI}")
        endif()

        set(openyammFfmpegAndroidApiLevel "${CMAKE_SYSTEM_VERSION}")
        if (DEFINED ANDROID_PLATFORM AND ANDROID_PLATFORM MATCHES "^android-([0-9]+)$")
            set(openyammFfmpegAndroidApiLevel "${CMAKE_MATCH_1}")
        endif()

        get_filename_component(openyammAndroidToolchainBinDir "${CMAKE_AR}" DIRECTORY)
        set(openyammFfmpegCc
            "${openyammAndroidToolchainBinDir}/${openyammFfmpegCompilerPrefix}${openyammFfmpegAndroidApiLevel}-clang")

        if (NOT EXISTS "${openyammFfmpegCc}")
            message(FATAL_ERROR "Android FFmpeg compiler not found: ${openyammFfmpegCc}")
        endif()

        list(APPEND openyammFfmpegConfigureArgs
            --enable-cross-compile
            --target-os=android
            --arch=${openyammFfmpegArch}
            --cc=${openyammFfmpegCc}
            --ar=${CMAKE_AR}
            --ranlib=${CMAKE_RANLIB}
            --strip=${CMAKE_STRIP}
            --nm=${CMAKE_NM}
        )

        if (NOT CMAKE_SYSROOT STREQUAL "")
            list(APPEND openyammFfmpegConfigureArgs --sysroot=${CMAKE_SYSROOT})
        endif()
    endif()

    file(MAKE_DIRECTORY "${OPENYAMM_FFMPEG_BUILD_DIR}")

    add_custom_command(
        OUTPUT
            "${OPENYAMM_FFMPEG_LIBAVFORMAT}"
            "${OPENYAMM_FFMPEG_LIBAVCODEC}"
            "${OPENYAMM_FFMPEG_LIBSWRESAMPLE}"
            "${OPENYAMM_FFMPEG_LIBSWSCALE}"
            "${OPENYAMM_FFMPEG_LIBAVUTIL}"
        COMMAND bash "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
            ${openyammFfmpegConfigureArgs}
        COMMAND ${OPENYAMM_FFMPEG_MAKE_PROGRAM} -j4
        COMMAND ${OPENYAMM_FFMPEG_MAKE_PROGRAM} install
        WORKING_DIRECTORY "${OPENYAMM_FFMPEG_BUILD_DIR}"
        DEPENDS
            "${OPENYAMM_FFMPEG_SOURCE_DIR}/configure"
            "${CMAKE_CURRENT_FUNCTION_LIST_FILE}"
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

    if (WIN32)
        target_link_libraries(${targetName} PRIVATE bcrypt)
    endif()

    add_dependencies(${targetName} openyamm_ffmpeg_build)
endfunction()
