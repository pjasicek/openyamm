#pragma once

#include "game/ui/MenuDesignScreen.h"

#include <string>

namespace OpenYAMM::Game
{
class LoadingOverlayScreen : public MenuDesignScreen
{
public:
    enum class Presentation
    {
        Fullscreen,
        DungeonTransition
    };

    explicit LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem);
    ~LoadingOverlayScreen() override;

    AppMode mode() const override;

    void setPresentation(Presentation presentation);
    void setBackgroundTextureName(const std::string &textureName);
    void setProgressPercent(int progressPercent);
    bgfx::FrameBufferHandle createTransitionBackground(int width, int height);

private:
    void drawScreen(float deltaSeconds) override;
    void drawTransition();
    void drawHourglass(const Rect &rect);

    Presentation m_presentation = Presentation::Fullscreen;
    std::string m_backgroundTextureName = "loading1";
    int m_progressPercent = 0;
    uint64_t m_animationStartTicks = 0;
    bgfx::FrameBufferHandle m_transitionBackground = BGFX_INVALID_HANDLE;
};
}
