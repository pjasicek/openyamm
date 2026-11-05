#pragma once

#include "game/app/AppMode.h"
#include "game/content/CompletionCertificates.h"
#include "game/debug/ScreenshotCaptureService.h"
#include "game/ui/MenuScreenBase.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The completion certificate (CompletionCertificates.h): its art at 1536 x 1024 art pixels, fitted to the frame, with
// the OpenYAMM seal and the game's text over it.
class WinGameScreen : public MenuScreenBase
{
public:
    WinGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        const CompletionCertificate &certificate,
        AppMode mode);

    AppMode mode() const override;
    bool shouldClose() const;
    const CompletionCertificate &certificate() const;
    // Once, after the certificate has been drawn: the part of the frame it covers, to be saved as an image.
    std::optional<ScreenshotCaptureService::Region> takeCaptureRegion();

    void handleSdlEvent(const SDL_Event &event) override;

private:
    struct TextLine
    {
        std::string text;
        std::string fontName;
        // Height in art pixels.
        float size = 0.0f;
        uint32_t colorAbgr = 0;
        // Space above the line, in art pixels.
        float gapAbove = 0.0f;
        // The wordmark, title and headline, which stay at the top of the zone.
        bool header = false;
    };

    void drawScreen(float deltaSeconds) override;
    // "OpenYAMM", with the rules the game was played by when they are not the Standard ones.
    std::string wordmark() const;
    std::vector<TextLine> layoutLines(float zoneWidth);

    CompletionCertificate m_certificate;
    AppMode m_mode = AppMode::GameplayOutdoor;
    bool m_shouldClose = false;
    float m_shownSeconds = 0.0f;
    uint32_t m_drawnFrames = 0;
    bool m_captureTaken = false;
    ScreenshotCaptureService::Region m_certificateRegion;
    std::vector<uint8_t> m_blackPixel = {0, 0, 0, 255};
};
}
