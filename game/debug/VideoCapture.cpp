#include "game/debug/VideoCapture.h"

#include "engine/BgfxContext.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <filesystem>
#include <iostream>
#include <optional>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
// A frame not back after this long (real time) is given up, so a lost readback cannot stall the recording.
constexpr uint64_t FrameTimeoutMilliseconds = 3000;

#if defined(_WIN32)
FILE *openPipe(const std::string &command)
{
    return _popen(command.c_str(), "wb");
}

int closePipe(FILE *pPipe)
{
    return _pclose(pPipe);
}
#elif !defined(__ANDROID__)
FILE *openPipe(const std::string &command)
{
    return popen(command.c_str(), "w");
}

int closePipe(FILE *pPipe)
{
    return pclose(pPipe);
}
#endif
}

VideoCapture::~VideoCapture()
{
    if (m_pEncoder != nullptr)
    {
        finish();
    }
}

bool VideoCapture::start(const std::string &outputPath, uint32_t framesPerSecond, std::string &error)
{
#if defined(__ANDROID__)
    (void)outputPath;
    (void)framesPerSecond;
    error = "video capture is desktop only";
    return false;
#else
    if (m_active)
    {
        error = "a video is already being recorded: " + m_outputPath;
        return false;
    }

    if (outputPath.empty() || outputPath.find_first_of("\"'`$\\") != std::string::npos)
    {
        error = "the video path must be non-empty and free of quotes, $, ` and backslashes";
        return false;
    }

    if (framesPerSecond < 1 || framesPerSecond > 240)
    {
        error = "frames per second must be 1-240";
        return false;
    }

    const std::filesystem::path path(outputPath);

    if (path.has_parent_path())
    {
        std::error_code errorCode;
        std::filesystem::create_directories(path.parent_path(), errorCode);

        if (errorCode)
        {
            error = "cannot create " + path.parent_path().string() + ": " + errorCode.message();
            return false;
        }
    }

    m_outputPath = outputPath;
    m_framesPerSecond = framesPerSecond;
    ++m_session;
    m_active = true;
    m_stopping = false;
    m_width = 0;
    m_height = 0;
    m_requestedFrames = 0;
    m_writtenFrames = 0;
    m_droppedFrames = 0;
    m_waitStartTicks = 0;
    return true;
#endif
}

void VideoCapture::stop()
{
    m_stopping = true;
}

std::string VideoCapture::status() const
{
    if (!m_active)
    {
        return "Not recording.";
    }

    return std::string(m_stopping ? "Finishing " : "Recording ") + m_outputPath + " at "
        + std::to_string(m_framesPerSecond) + " fps: " + std::to_string(m_writtenFrames) + " frames written ("
        + std::to_string(double(m_writtenFrames) / m_framesPerSecond) + " s), "
        + std::to_string(m_droppedFrames) + " dropped";
}

std::string VideoCapture::frameToken(uint64_t frameIndex) const
{
    return "video-" + std::to_string(m_session) + "-" + std::to_string(frameIndex);
}

bool VideoCapture::openEncoder(uint32_t width, uint32_t height)
{
#if defined(__ANDROID__)
    (void)width;
    (void)height;
    return false;
#else
    // A high-quality master (x264 CRF 12, 4:2:0 for editors and players); the trailer edit re-encodes it.
    const std::string command = "ffmpeg -hide_banner -loglevel error -y -f rawvideo -pix_fmt bgra -s "
        + std::to_string(width) + "x" + std::to_string(height) + " -framerate " + std::to_string(m_framesPerSecond)
        + " -i - -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -movflags +faststart \"" + m_outputPath + "\"";
    m_pEncoder = openPipe(command);

    if (m_pEncoder == nullptr)
    {
        std::cerr << "VideoCapture: cannot start ffmpeg (is it on PATH?)\n";
        return false;
    }

    m_width = width;
    m_height = height;
    std::cout << "VideoCapture: recording " << width << "x" << height << " at " << m_framesPerSecond << " fps to "
              << m_outputPath << '\n';
    return true;
#endif
}

void VideoCapture::finish()
{
#if !defined(__ANDROID__)
    if (m_pEncoder != nullptr)
    {
        const int result = closePipe(m_pEncoder);
        m_pEncoder = nullptr;
        std::cout << "VideoCapture: " << (result == 0 ? "wrote " : "ffmpeg failed writing ") << m_outputPath << " ("
                  << m_writtenFrames << " frames, " << m_droppedFrames << " dropped)\n";
    }
#endif
    m_active = false;
    m_stopping = false;
}

void VideoCapture::update()
{
    if (!m_active)
    {
        return;
    }

    if (!m_stopping)
    {
        const std::string token = frameToken(m_requestedFrames);
        bgfx::requestScreenShot(BGFX_INVALID_HANDLE, token.c_str());
        ++m_requestedFrames;
    }

    // Write the frames that are back, in order.
    while (m_writtenFrames < m_requestedFrames)
    {
        std::optional<Engine::BgfxContext::ScreenshotCapture> frame =
            Engine::BgfxContext::consumeScreenshot(frameToken(m_writtenFrames));

        if (!frame)
        {
            const uint64_t now = SDL_GetTicks();

            if (m_waitStartTicks == 0)
            {
                m_waitStartTicks = now;
            }

            if (now - m_waitStartTicks < FrameTimeoutMilliseconds)
            {
                break;
            }

            std::cerr << "VideoCapture: frame " << m_writtenFrames << " never came back; skipped\n";
            ++m_writtenFrames;
            ++m_droppedFrames;
            m_waitStartTicks = 0;
            continue;
        }

        m_waitStartTicks = 0;

        if (m_pEncoder == nullptr && !openEncoder(frame->width, frame->height))
        {
            m_stopping = true;
            m_writtenFrames = m_requestedFrames;
            break;
        }

        if (frame->width != m_width || frame->height != m_height)
        {
            std::cerr << "VideoCapture: frame " << m_writtenFrames << " is " << frame->width << "x" << frame->height
                      << ", not " << m_width << "x" << m_height << "; skipped (keep the window size fixed)\n";
            ++m_droppedFrames;
        }
        else
        {
            std::fwrite(frame->bgraPixels.data(), 1, frame->bgraPixels.size(), m_pEncoder);
        }

        ++m_writtenFrames;
    }

    if (m_stopping && m_writtenFrames >= m_requestedFrames)
    {
        finish();
    }
}
}
