#pragma once

#include "game/ui/MenuScreenBase.h"

#include <string>

namespace OpenYAMM::Game
{
class LoadingOverlayScreen : public MenuScreenBase
{
public:
    enum class Presentation
    {
        Fullscreen,
        DungeonTransition
    };

    explicit LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem);

    AppMode mode() const override;

    void setPresentation(Presentation presentation);
    void setBackgroundTextureName(const std::string &textureName);
    void setProgressPercent(int progressPercent);

private:
    void drawScreen(float deltaSeconds) override;

    Presentation m_presentation = Presentation::Fullscreen;
    std::string m_backgroundTextureName = "loading1";
    int m_progressPercent = 0;
};
}
