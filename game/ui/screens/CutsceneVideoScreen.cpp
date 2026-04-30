#include "game/ui/screens/CutsceneVideoScreen.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
CutsceneVideoScreen::CutsceneVideoScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    GameAudioSystem *pGameAudioSystem,
    const std::string &videoDirectory,
    const std::string &videoStem,
    AppMode mode)
    : MenuScreenBase(assetFileSystem)
    , m_pGameAudioSystem(pGameAudioSystem)
    , m_videoDirectory(videoDirectory)
    , m_videoStem(videoStem)
    , m_mode(mode)
{
}

AppMode CutsceneVideoScreen::mode() const
{
    return m_mode;
}

bool CutsceneVideoScreen::shouldClose() const
{
    return m_shouldClose;
}

void CutsceneVideoScreen::onEnter()
{
    if (m_pGameAudioSystem != nullptr)
    {
        m_pausedBackgroundMusic = !m_pGameAudioSystem->isBackgroundMusicPaused();

        if (m_pausedBackgroundMusic)
        {
            m_pGameAudioSystem->pauseBackgroundMusic();
        }
    }

    m_videoPlayer.initialize();
}

void CutsceneVideoScreen::onExit()
{
    m_videoPlayer.shutdown();

    if (m_pausedBackgroundMusic && m_pGameAudioSystem != nullptr)
    {
        m_pGameAudioSystem->resumeBackgroundMusic();
    }

    m_pausedBackgroundMusic = false;
}

void CutsceneVideoScreen::handleSdlEvent(const SDL_Event &event)
{
    if (event.type != SDL_EVENT_KEY_DOWN)
    {
        return;
    }

    if (event.key.key == SDLK_ESCAPE)
    {
        m_shouldClose = true;
    }
}

void CutsceneVideoScreen::drawScreen(float deltaSeconds)
{
    const Rect fullFrame = {0.0f, 0.0f, static_cast<float>(frameWidth()), static_cast<float>(frameHeight())};
    drawPixelsBgra("__cutscene_video_black__", 1, 1, m_blackPixel, fullFrame);

    if (!m_playAttempted)
    {
        m_playAttempted = true;
        m_startedPlayback = m_videoPlayer.play(assetFileSystem(), m_videoStem, m_videoDirectory, false);

        if (!m_startedPlayback)
        {
            m_shouldClose = true;
            return;
        }
    }

    if (!m_startedPlayback)
    {
        return;
    }

    m_videoPlayer.update(deltaSeconds);

    if (m_videoPlayer.hasFinishedPlayback())
    {
        m_shouldClose = true;
    }

    if (!m_videoPlayer.hasActiveFrame())
    {
        return;
    }

    const bgfx::TextureHandle textureHandle = m_videoPlayer.textureHandle();
    const int textureWidth = m_videoPlayer.videoTextureWidth();
    const int textureHeight = m_videoPlayer.videoTextureHeight();

    if (textureWidth <= 0 || textureHeight <= 0)
    {
        return;
    }

    const float sourceWidth = static_cast<float>(textureWidth);
    const float sourceHeight = static_cast<float>(textureHeight);
    const float scale = std::min(
        static_cast<float>(frameWidth()) / sourceWidth,
        static_cast<float>(frameHeight()) / sourceHeight);
    const float drawWidth = std::round(sourceWidth * scale);
    const float drawHeight = std::round(sourceHeight * scale);
    const float drawX = std::round((static_cast<float>(frameWidth()) - drawWidth) * 0.5f);
    const float drawY = std::round((static_cast<float>(frameHeight()) - drawHeight) * 0.5f);
    drawTextureHandle(textureHandle, Rect{drawX, drawY, drawWidth, drawHeight});
}
}
