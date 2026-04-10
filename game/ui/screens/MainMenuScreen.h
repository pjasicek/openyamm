#pragma once

#include "game/audio/SoundIds.h"
#include "game/ui/MenuScreenBase.h"
#include "game/ui/UiLayoutManager.h"

#include <functional>
#include <optional>

namespace OpenYAMM::Game
{
class GameAudioSystem;

class MainMenuScreen : public MenuScreenBase
{
public:
    using Action = std::function<void()>;

    MainMenuScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        Action newGameAction,
        Action loadGameAction,
        Action quitAction);

    AppMode mode() const override;

private:
    void drawScreen(float deltaSeconds) override;
    bool ensureLayoutLoaded();
    std::optional<Rect> resolveLayoutRect(
        const std::string &layoutId,
        float fallbackWidth = 0.0f,
        float fallbackHeight = 0.0f) const;
    ButtonVisualSet resolveButtonVisuals(
        const std::string &layoutId,
        const ButtonVisualSet &fallbackVisuals) const;
    std::string resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const;
    void playUiClickSound(SoundId soundId) const;

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    Action m_newGameAction;
    Action m_loadGameAction;
    Action m_quitAction;
    UiLayoutManager m_layoutManager;
    bool m_layoutLoaded = false;
};
}
