#pragma once

#include "game/audio/HouseVideoPlayer.h"
#include "game/audio/GameAudioSystem.h"
#include "game/ui/MenuScreenBase.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class CutsceneVideoScreen : public MenuScreenBase
{
public:
    CutsceneVideoScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        const std::string &videoDirectory,
        const std::string &videoStem,
        AppMode mode);

    AppMode mode() const override;
    bool shouldClose() const;

    void onEnter() override;
    void onExit() override;
    void handleSdlEvent(const SDL_Event &event) override;

private:
    void drawScreen(float deltaSeconds) override;

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    HouseVideoPlayer m_videoPlayer;
    std::string m_videoDirectory;
    std::string m_videoStem;
    AppMode m_mode = AppMode::GameplayOutdoor;
    bool m_playAttempted = false;
    bool m_startedPlayback = false;
    bool m_shouldClose = false;
    bool m_pausedBackgroundMusic = false;
    std::vector<uint8_t> m_blackPixel = {0, 0, 0, 255};
};
}
