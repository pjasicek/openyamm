#pragma once

#include <cstdint>
#include <filesystem>
#include <functional>
#include <optional>
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
    using PixelsCallback = std::function<void(uint32_t, uint32_t, const std::vector<uint8_t> &)>;

    // A part of the frame, in fractions of its width and height.
    struct Region
    {
        float x = 0.0f;
        float y = 0.0f;
        float width = 1.0f;
        float height = 1.0f;
    };

    // Saves the next frame, or only region of it, as a PNG.
    void requestCapture(
        const std::filesystem::path &outputPath,
        CompletionCallback completionCallback,
        const std::optional<Region> &region = std::nullopt);
    void requestPixels(PixelsCallback callback);
    bool hasPendingCaptures() const;
    void update();

private:
    struct PendingCapture
    {
        std::filesystem::path outputPath;
        CompletionCallback completionCallback;
        PixelsCallback pixelsCallback;
        std::optional<Region> region;
        std::string token;
        uint64_t requestedTicks = 0;
        bool screenshotRequested = false;
    };

    std::vector<PendingCapture> m_pendingCaptures;
    uint32_t m_nextCaptureToken = 0;
};
}
