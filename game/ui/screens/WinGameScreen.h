#pragma once

#include "game/app/AppMode.h"
#include "game/ui/MenuScreenBase.h"

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct WinGameCertificate
{
    std::string characterLine;
    std::string endingText;
    std::string totalTimeLine;
    std::string scoreLine;
};

class WinGameScreen : public MenuScreenBase
{
public:
    WinGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        const WinGameCertificate &certificate,
        AppMode mode);

    AppMode mode() const override;
    bool shouldClose() const;

    void handleSdlEvent(const SDL_Event &event) override;

private:
    void drawScreen(float deltaSeconds) override;

    void drawCenteredText(
        const std::string &fontName,
        const std::string &text,
        float logicalY,
        float scale,
        float viewportX,
        float viewportY,
        float viewportWidth,
        uint32_t colorAbgr);
    std::vector<std::string> wrapText(
        const std::string &fontName,
        const std::string &text,
        float maxWidth,
        float scale);

    WinGameCertificate m_certificate;
    AppMode m_mode = AppMode::GameplayOutdoor;
    bool m_shouldClose = false;
    std::vector<uint8_t> m_blackPixel = {0, 0, 0, 255};
};
}
