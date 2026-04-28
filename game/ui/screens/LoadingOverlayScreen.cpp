#include "game/ui/screens/LoadingOverlayScreen.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>

namespace OpenYAMM::Game
{
namespace
{
constexpr float ReferenceWidth = 640.0f;
constexpr float ReferenceHeight = 480.0f;
constexpr float ProgressBarX = 173.0f;
constexpr float ProgressBarY = 459.0f;
constexpr float ProgressBarWidth = 299.0f;
constexpr float ProgressBarHeight = 14.0f;
constexpr int ProgressStepPercent = 5;
constexpr int ProgressStepCount = 20;
constexpr float DungeonProgressBarX = 94.0f;
constexpr float DungeonProgressBarY = 42.0f;
constexpr float DungeonProgressBarWidth = 113.0f;
constexpr float DungeonProgressBarHeight = 16.0f;
constexpr float DungeonTurnHourX = 20.0f;
constexpr float DungeonTurnHourY = 24.0f;
constexpr int TurnHourFrameCount = 10;
constexpr uint64_t TurnHourFrameMilliseconds = 50;
constexpr uint16_t FullscreenLoadingViewId = 0;
constexpr uint16_t DungeonTransitionLoadingViewId = 3;

std::string turnHourFrameName()
{
    const int frameIndex = static_cast<int>(
        (SDL_GetTicks() / TurnHourFrameMilliseconds) % TurnHourFrameCount) + 1;
    char frameName[16] = {};
    std::snprintf(frameName, sizeof(frameName), "ia02-%03d", frameIndex);
    return frameName;
}
}

LoadingOverlayScreen::LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem)
    : MenuScreenBase(assetFileSystem)
{
}

AppMode LoadingOverlayScreen::mode() const
{
    return AppMode::LoadMenu;
}

void LoadingOverlayScreen::setPresentation(Presentation presentation)
{
    m_presentation = presentation;
    setRenderViewId(
        presentation == Presentation::DungeonTransition
            ? DungeonTransitionLoadingViewId
            : FullscreenLoadingViewId);
    setClearBackground(presentation == Presentation::Fullscreen);
}

void LoadingOverlayScreen::setBackgroundTextureName(const std::string &textureName)
{
    m_backgroundTextureName = textureName;
}

void LoadingOverlayScreen::setProgressPercent(int progressPercent)
{
    m_progressPercent = std::clamp(progressPercent, 0, 100);
}

void LoadingOverlayScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    const float baseScale = std::min(
        static_cast<float>(frameWidth()) / ReferenceWidth,
        static_cast<float>(frameHeight()) / ReferenceHeight);
    const float viewportWidth = ReferenceWidth * baseScale;
    const float viewportHeight = ReferenceHeight * baseScale;
    const float viewportX = (static_cast<float>(frameWidth()) - viewportWidth) * 0.5f;
    const float viewportY = (static_cast<float>(frameHeight()) - viewportHeight) * 0.5f;

    if (m_presentation == Presentation::DungeonTransition)
    {
        const std::array<std::string, 2> bardataCandidates = {
            m_backgroundTextureName,
            "bardata"
        };
        std::string bardataTextureName;
        std::optional<TextureSize> bardataSize;

        for (const std::string &candidate : bardataCandidates)
        {
            bardataSize = textureSize(candidate);

            if (bardataSize)
            {
                bardataTextureName = candidate;
                break;
            }
        }

        if (!bardataSize)
        {
            return;
        }

        const float imageWidth = bardataSize->width * baseScale;
        const float imageHeight = bardataSize->height * baseScale;
        const float imageX = std::round((static_cast<float>(frameWidth()) - imageWidth) * 0.5f);
        const float imageY = std::round((static_cast<float>(frameHeight()) - imageHeight) * 0.5f);

        drawTexture(
            bardataTextureName,
            Rect{
                imageX,
                imageY,
                std::round(imageWidth),
                std::round(imageHeight)
            });

        const std::string turnHourTextureName = turnHourFrameName();
        const std::optional<TextureSize> turnHourSize = textureSize(turnHourTextureName);

        if (turnHourSize)
        {
            drawTexture(
                turnHourTextureName,
                Rect{
                    std::round(imageX + DungeonTurnHourX * baseScale),
                    std::round(imageY + DungeonTurnHourY * baseScale),
                    std::round(turnHourSize->width * baseScale),
                    std::round(turnHourSize->height * baseScale)
                });
        }

        const float fillFraction = static_cast<float>(std::clamp(m_progressPercent, 0, 100)) / 100.0f;
        const int fillWidth = static_cast<int>(std::round(DungeonProgressBarWidth * fillFraction));

        if (fillWidth <= 0)
        {
            return;
        }

        const std::vector<uint8_t> redPixelBgra = {0, 0, 220, 255};
        drawPixelsBgra(
            "__dungeon_transition_loading_red_pixel__",
            1,
            1,
            redPixelBgra,
            Rect{
                std::round(imageX + DungeonProgressBarX * baseScale),
                std::round(imageY + DungeonProgressBarY * baseScale),
                std::round(static_cast<float>(fillWidth) * baseScale),
                std::round(DungeonProgressBarHeight * baseScale)
            });
        return;
    }

    drawTexture(
        m_backgroundTextureName,
        Rect{
            std::round(viewportX),
            std::round(viewportY),
            std::round(viewportWidth),
            std::round(viewportHeight)
        });

    const int filledSteps = m_progressPercent >= 100
        ? ProgressStepCount
        : std::clamp(m_progressPercent / ProgressStepPercent, 0, ProgressStepCount - 1);

    if (filledSteps <= 0)
    {
        return;
    }

    const float fillFraction = static_cast<float>(filledSteps) / static_cast<float>(ProgressStepCount);
    const float filledWidth = ProgressBarWidth * fillFraction;
    const Rect destinationRect = {
        std::round(viewportX + ProgressBarX * baseScale),
        std::round(viewportY + ProgressBarY * baseScale),
        std::round(filledWidth * baseScale),
        std::round(ProgressBarHeight * baseScale)
    };
    const SourceRect sourceRect = {
        0.0f,
        0.0f,
        filledWidth,
        ProgressBarHeight
    };

    drawTextureRegion("loadprog", sourceRect, destinationRect);
}
}
