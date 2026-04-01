#pragma once

#include "game/ui/MenuScreenBase.h"

#include <functional>

namespace OpenYAMM::Game
{
class MainMenuScreen : public MenuScreenBase
{
public:
    using Action = std::function<void()>;

    MainMenuScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        Action newGameAction,
        Action loadGameAction,
        Action quitAction);

    AppMode mode() const override;

private:
    void drawScreen(float deltaSeconds) override;

    Action m_newGameAction;
    Action m_loadGameAction;
    Action m_quitAction;
};
}
