#pragma once

namespace OpenYAMM::Game
{
// A point or direction in world units. In its own header so that the format files which carry points (the
// cinematics library) need nothing of the gameplay runtime.
struct GameplayWorldPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};
}
