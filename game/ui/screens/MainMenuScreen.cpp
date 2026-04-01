#include "game/ui/screens/MainMenuScreen.h"

#include <utility>

namespace OpenYAMM::Game
{
MainMenuScreen::MainMenuScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    Action newGameAction,
    Action loadGameAction,
    Action quitAction)
    : MenuScreenBase(assetFileSystem)
    , m_newGameAction(std::move(newGameAction))
    , m_loadGameAction(std::move(loadGameAction))
    , m_quitAction(std::move(quitAction))
{
}

AppMode MainMenuScreen::mode() const
{
    return AppMode::MainMenu;
}

void MainMenuScreen::drawScreen(float deltaSeconds)
{
    static_cast<void>(deltaSeconds);

    constexpr float RootWidth = 640.0f;
    constexpr float RootHeight = 480.0f;
    const float scale = std::min(
        static_cast<float>(frameWidth()) / RootWidth,
        static_cast<float>(frameHeight()) / RootHeight);
    const float scaledWidth = RootWidth * scale;
    const float scaledHeight = RootHeight * scale;
    const float rootX = (static_cast<float>(frameWidth()) - scaledWidth) * 0.5f;
    const float rootY = (static_cast<float>(frameHeight()) - scaledHeight) * 0.5f;

    drawTexture("title", Rect{rootX, rootY, scaledWidth, scaledHeight});

    const float actionColumnX = rootX + 402.0f * scale;
    const float actionColumnY = rootY + 182.0f * scale;
    const float buttonWidth = 135.0f * scale;
    const float buttonHeight = 41.0f * scale;
    const float buttonX = actionColumnX + 22.5f * scale;

    const ButtonState newGameButton = drawButton(
        ButtonVisualSet{"T_new_up", "T_new_ht", "T_new_dn"},
        Rect{buttonX, actionColumnY, buttonWidth, buttonHeight});
    const ButtonState loadGameButton = drawButton(
        ButtonVisualSet{"T_load_up", "T_load_ht", "T_load_dn"},
        Rect{buttonX, actionColumnY + 62.0f * scale, buttonWidth, buttonHeight});
    const ButtonState quitButton = drawButton(
        ButtonVisualSet{"T_quit_up", "T_quit_ht", "T_quit_dn"},
        Rect{buttonX, actionColumnY + 124.0f * scale, buttonWidth, buttonHeight});

    drawDebugText(static_cast<int>(rootX + 52.0f * scale), static_cast<int>(rootY + 40.0f * scale), 0x0f, "OpenYAMM");
    drawDebugText(static_cast<int>(buttonX + 28.0f * scale), static_cast<int>(actionColumnY + 14.0f * scale), 0x0f, "New Game");
    drawDebugText(
        static_cast<int>(buttonX + 30.0f * scale),
        static_cast<int>(actionColumnY + 76.0f * scale),
        0x0f,
        "Load Game");
    drawDebugText(static_cast<int>(buttonX + 44.0f * scale), static_cast<int>(actionColumnY + 138.0f * scale), 0x0f, "Quit");

    if (newGameButton.clicked && m_newGameAction)
    {
        m_newGameAction();
    }

    if (loadGameButton.clicked && m_loadGameAction)
    {
        m_loadGameAction();
    }

    if (quitButton.clicked && m_quitAction)
    {
        m_quitAction();
    }
}
}
