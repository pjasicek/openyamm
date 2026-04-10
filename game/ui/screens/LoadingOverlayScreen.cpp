#include "game/ui/screens/LoadingOverlayScreen.h"

#include <algorithm>
#include <cmath>

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
}

LoadingOverlayScreen::LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem)
    : MenuScreenBase(assetFileSystem)
{
}

AppMode LoadingOverlayScreen::mode() const
{
    return AppMode::LoadMenu;
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
