#pragma once

#include "game/app/AppMode.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
class IScreen
{
public:
    virtual ~IScreen() = default;

    virtual AppMode mode() const = 0;
    virtual void renderFrame(int width, int height, float mouseWheelDelta, float deltaSeconds) = 0;

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
