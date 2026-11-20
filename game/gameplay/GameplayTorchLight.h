#pragma once

#include "game/party/Party.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
struct GameplayTorchLight
{
    float radius = 0.0f;
    float intensity = 1.0f;
    uint32_t colorAbgr = 0xffffffffu;
};

// The original's neutral grey (#606060), or a firelight orange of about the same brightness.
inline uint32_t gameplayTorchLightColorAbgr(bool warm)
{
    return warm ? 0xff1e5894u : 0xff606060u;
}

inline float gameplayTorchLightBaseRadius(bool outdoor)
{
    return outdoor ? 1024.0f : 800.0f;
}

// Outdoors the light fades in with darkness (0 by day, 1 at night) so it also works through dusk and dawn.
inline std::optional<GameplayTorchLight> resolveGameplayTorchLight(
    const Party &party,
    bool outdoor,
    float outdoorDarkness,
    bool warm)
{
    constexpr float MinimumOutdoorDarkness = 0.01f;

    if (outdoor && outdoorDarkness < MinimumOutdoorDarkness)
    {
        return std::nullopt;
    }

    const PartyBuffState *pTorchBuff = party.partyBuff(PartyBuffId::TorchLight);

    if (pTorchBuff == nullptr)
    {
        return std::nullopt;
    }

    GameplayTorchLight light = {};
    const int power = std::max(pTorchBuff->power, 1);
    light.radius = gameplayTorchLightBaseRadius(outdoor) * power;
    light.intensity = 1.0f;
    light.colorAbgr = gameplayTorchLightColorAbgr(warm);

    if (outdoor)
    {
        // Outdoor light emitters carry their strength in the alpha byte.
        const uint32_t alpha = static_cast<uint32_t>(std::lround(255.0f * std::min(outdoorDarkness, 1.0f)));
        light.colorAbgr = (light.colorAbgr & 0x00ffffffu) | (alpha << 24);
    }

    return light;
}
}
