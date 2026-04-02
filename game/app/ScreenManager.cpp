#include "game/app/ScreenManager.h"

namespace OpenYAMM::Game
{
void ScreenManager::setCurrentMode(AppMode mode)
{
    m_currentMode = mode;
}

AppMode ScreenManager::currentMode() const
{
    return m_currentMode;
}

void ScreenManager::setActiveScreen(std::unique_ptr<IScreen> pScreen)
{
    if (m_pActiveScreen)
    {
        m_pActiveScreen->onExit();
    }

    m_pActiveScreen = std::move(pScreen);

    if (m_pActiveScreen)
    {
        m_currentMode = m_pActiveScreen->mode();
        m_pActiveScreen->onEnter();
    }
}

IScreen *ScreenManager::activeScreen()
{
    return m_pActiveScreen.get();
}

const IScreen *ScreenManager::activeScreen() const
{
    return m_pActiveScreen.get();
}
}
