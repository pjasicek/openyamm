#pragma once

#include "game/party/Party.h"

#include <algorithm>
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

inline uint32_t gameplayTorchLightColorAbgr()
{
    return 0xff606060u;
}

inline float gameplayTorchLightBaseRadius(bool outdoor)
{
    return outdoor ? 1024.0f : 800.0f;
}

inline std::optional<GameplayTorchLight> resolveGameplayTorchLight(
    const Party &party,
    bool outdoor,
    bool outdoorNight)
{
    if (outdoor && !outdoorNight)
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
    light.colorAbgr = gameplayTorchLightColorAbgr();
    return light;
}
}
