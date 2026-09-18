#pragma once

#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Captures rendered frames through the bgfx screenshot callback and writes them as PNG files.
// update() must run once per frame after world/UI rendering and before bgfx::frame().
// Only one capture is submitted to bgfx at a time; queued captures run in order.
class ScreenshotCaptureService
{
public:
    using CompletionCallback = std::function<void(bool success, const std::string &message)>;

    void requestCapture(const std::filesystem::path &outputPath, CompletionCallback completionCallback);
    bool hasPendingCaptures() const;
    void update();

private:
    struct PendingCapture
    {
        std::filesystem::path outputPath;
        CompletionCallback completionCallback;
        std::string token;
        uint32_t requestedTicks = 0;
        bool screenshotRequested = false;
    };

    std::vector<PendingCapture> m_pendingCaptures;
    uint32_t m_nextCaptureToken = 0;
};
}
