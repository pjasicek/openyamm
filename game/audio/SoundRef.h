#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
enum class SoundScope
{
    Engine,
    World,
};

struct SoundRef
{
    SoundScope scope = SoundScope::Engine;
    uint32_t id = 0;
};

inline SoundRef engineSound(uint32_t soundId)
{
    return SoundRef{SoundScope::Engine, soundId};
}

inline SoundRef worldSound(uint32_t soundId)
{
    return SoundRef{SoundScope::World, soundId};
}
}
