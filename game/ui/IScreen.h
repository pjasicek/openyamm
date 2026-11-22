#pragma once

#include "game/app/AppMode.h"
#include "game/gameplay/GameplayInputFrame.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
class IScreen
{
public:
    virtual ~IScreen() = default;

    virtual AppMode mode() const = 0;
    virtual bool rendersOverGameplay() const
    {
        return false;
    }
    // A screen every player of a co-op session watches together (a movie, a story's end): the session's world waits
    // while it shows. Any other screen is this game's own, and the session's world goes on behind it
    // (GameSession::coopSession).
    virtual bool holdsCoopWorld() const
    {
        return false;
    }
    virtual bool textInputActive() const
    {
        return false;
    }
    virtual void renderFrame(
        int width,
        int height,
        const GameplayInputFrame &inputFrame,
        float deltaSeconds) = 0;

    virtual void onEnter()
    {
    }

    virtual void onExit()
    {
    }

    virtual void handleSdlEvent(const SDL_Event &event)
    {
        static_cast<void>(event);
    }
};
}
