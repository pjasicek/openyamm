#pragma once

#include "game/app/AppMode.h"
#include "game/ui/IScreen.h"

#include <memory>

namespace OpenYAMM::Game
{
class ScreenManager
{
public:
    void setCurrentMode(AppMode mode);
    AppMode currentMode() const;

    void setActiveScreen(std::unique_ptr<IScreen> pScreen);
    IScreen *activeScreen();
    const IScreen *activeScreen() const;

private:
    AppMode m_currentMode = AppMode::MainMenu;
    std::unique_ptr<IScreen> m_pActiveScreen;
};
}
