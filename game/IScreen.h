#pragma once

#include "game/AppMode.h"

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
};
}
