#include "game/ui/screens/WinGameScreen.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <sstream>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ReferenceWidth = 640.0f;
constexpr float ReferenceHeight = 480.0f;
constexpr const char *WinBackgroundTexture = "winBG";
constexpr const char *EndgameFontName = "ENDGAME";
constexpr uint32_t TextColor = 0xffffffffu;
}

WinGameScreen::WinGameScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    const WinGameCertificate &certificate,
    AppMode mode)
    : MenuScreenBase(assetFileSystem)
    , m_certificate(certificate)
    , m_mode(mode)
{
}

AppMode WinGameScreen::mode() const
{
    return m_mode;
}

bool WinGameScreen::shouldClose() const
{
    return m_shouldClose;
}

void WinGameScreen::handleSdlEvent(const SDL_Event &event)
{
    if (event.type == SDL_EVENT_KEY_DOWN
        && (event.key.key == SDLK_ESCAPE
            || event.key.key == SDLK_RETURN
            || event.key.key == SDLK_KP_ENTER
            || event.key.key == SDLK_SPACE))
    {
        m_shouldClose = true;
    }
    else if (event.type == SDL_EVENT_MOUSE_BUTTON_DOWN)
    {
        m_shouldClose = true;
    }
}

void WinGameScreen::drawCenteredText(
    const std::string &fontName,
    const std::string &text,
    float logicalY,
    float scale,
    float viewportX,
    float viewportY,
    float viewportWidth,
    uint32_t colorAbgr)
{
    const float textWidth = measureTextWidth(fontName, text, scale);
    const float x = std::round(viewportX + (viewportWidth - textWidth) * 0.5f);
    const float y = std::round(viewportY + logicalY * scale);
    drawText(fontName, text, x, y, colorAbgr, scale, false);
}

std::vector<std::string> WinGameScreen::wrapText(
    const std::string &fontName,
    const std::string &text,
    float maxWidth,
    float scale)
{
    std::vector<std::string> lines;
    std::istringstream input(text);
    std::string word;
    std::string currentLine;

    while (input >> word)
    {
        const std::string candidate = currentLine.empty() ? word : currentLine + " " + word;

        if (!currentLine.empty() && measureTextWidth(fontName, candidate, scale) > maxWidth)
        {
            lines.push_back(currentLine);
            currentLine = word;
        }
        else
        {
            currentLine = candidate;
        }
    }

    if (!currentLine.empty())
    {
        lines.push_back(currentLine);
    }

    return lines;
}

void WinGameScreen::drawScreen(float)
{
    const Rect fullFrame = {0.0f, 0.0f, static_cast<float>(frameWidth()), static_cast<float>(frameHeight())};
    drawPixelsBgra("__wingame_black__", 1, 1, m_blackPixel, fullFrame);

    const float scale = std::min(
        static_cast<float>(frameWidth()) / ReferenceWidth,
        static_cast<float>(frameHeight()) / ReferenceHeight);
    const float viewportWidth = std::round(ReferenceWidth * scale);
    const float viewportHeight = std::round(ReferenceHeight * scale);
    const float viewportX = std::round((static_cast<float>(frameWidth()) - viewportWidth) * 0.5f);
    const float viewportY = std::round((static_cast<float>(frameHeight()) - viewportHeight) * 0.5f);
    const Rect viewport = {viewportX, viewportY, viewportWidth, viewportHeight};

    drawTexture(WinBackgroundTexture, viewport);

    drawCenteredText(EndgameFontName, "Congratulations!", 155.0f, scale, viewportX, viewportY, viewportWidth, TextColor);
    drawCenteredText(
        EndgameFontName,
        m_certificate.characterLine,
        176.0f,
        scale,
        viewportX,
        viewportY,
        viewportWidth,
        TextColor);

    const std::vector<std::string> endingLines = wrapText(
        EndgameFontName,
        m_certificate.endingText,
        520.0f * scale,
        scale);
    const float lineHeight = static_cast<float>(fontHeight(EndgameFontName) + 3) * scale;
    float endingY = 230.0f;

    for (const std::string &line : endingLines)
    {
        drawCenteredText(EndgameFontName, line, endingY, scale, viewportX, viewportY, viewportWidth, TextColor);
        endingY += lineHeight / scale;
    }

    drawCenteredText(
        EndgameFontName,
        m_certificate.totalTimeLine,
        355.0f,
        scale,
        viewportX,
        viewportY,
        viewportWidth,
        TextColor);
    drawCenteredText(
        EndgameFontName,
        m_certificate.scoreLine,
        404.0f,
        scale,
        viewportX,
        viewportY,
        viewportWidth,
        TextColor);
}
}
