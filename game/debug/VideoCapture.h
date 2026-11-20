#pragma once

#include <cstdint>
#include <cstdio>
#include <string>

namespace OpenYAMM::Game
{
// Records the rendered frames (HUD included) into a video file through an ffmpeg process (desktop only): every frame
// is read back with a bgfx screenshot and written to ffmpeg's input in order. While recording, the owner runs the game
// on a fixed frame step of 1/fps (EngineApplication::setFixedFrameSeconds), so the video plays smoothly at fps however
// slowly the frames render. No sound is recorded. Console: `video start <path> [fps]`, `video stop`.
// update() must run once per frame after world/UI rendering and before bgfx::frame().
class VideoCapture
{
public:
    VideoCapture() = default;
    VideoCapture(const VideoCapture &) = delete;
    VideoCapture &operator=(const VideoCapture &) = delete;
    ~VideoCapture();

    bool start(const std::string &outputPath, uint32_t framesPerSecond, std::string &error);
    // Requests no more frames; the ones in flight are still written, then the file is closed.
    void stop();
    void update();

    // Recording or still writing the frames in flight.
    bool active() const
    {
        return m_active;
    }
    // Requesting a frame each update (started, not stopped).
    bool recording() const
    {
        return m_active && !m_stopping;
    }
    uint32_t framesPerSecond() const
    {
        return m_framesPerSecond;
    }
    std::string status() const;

private:
    std::string frameToken(uint64_t frameIndex) const;
    bool openEncoder(uint32_t width, uint32_t height);
    void finish();

    std::string m_outputPath;
    uint32_t m_framesPerSecond = 60;
    uint32_t m_session = 0;
    bool m_active = false;
    bool m_stopping = false;
    FILE *m_pEncoder = nullptr;
    uint32_t m_width = 0;
    uint32_t m_height = 0;
    uint64_t m_requestedFrames = 0;
    uint64_t m_writtenFrames = 0;
    uint64_t m_droppedFrames = 0;
    uint64_t m_waitStartTicks = 0;
};
}
