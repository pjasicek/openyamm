#pragma once

#include "game/ui/MenuScreenBase.h"

#include <string>

namespace OpenYAMM::Game
{
class LoadingOverlayScreen : public MenuScreenBase
{
public:
    explicit LoadingOverlayScreen(const Engine::AssetFileSystem &assetFileSystem);

    AppMode mode() const override;

    void setBackgroundTextureName(const std::string &textureName);
    void setProgressPercent(int progressPercent);

private:
    void drawScreen(float deltaSeconds) override;

    std::string m_backgroundTextureName = "loading1";
    int m_progressPercent = 0;
};
}
