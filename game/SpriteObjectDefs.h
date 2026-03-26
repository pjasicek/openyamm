#pragma once

#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
constexpr uint16_t ObjectDescNoSprite = 0x0001;
constexpr uint16_t ObjectDescNoCollision = 0x0002;
constexpr uint16_t ObjectDescTemporary = 0x0004;
constexpr uint16_t ObjectDescSftLifetime = 0x0008;
constexpr uint16_t ObjectDescUnpickable = 0x0010;
constexpr uint16_t ObjectDescNoGravity = 0x0020;
constexpr uint16_t ObjectDescInteractable = 0x0040;
constexpr uint16_t ObjectDescBounce = 0x0080;
constexpr uint16_t ObjectDescTrailParticle = 0x0100;
constexpr uint16_t ObjectDescTrailFire = 0x0200;
constexpr uint16_t ObjectDescTrailLine = 0x0400;

constexpr uint16_t SpriteAttrTemporary = 0x0002;
constexpr uint16_t SpriteAttrMissile = 0x0100;
constexpr uint16_t SpriteAttrRemoved = 0x0200;
constexpr uint16_t SpriteAttrDroppedByPlayer = 0x0400;

inline bool hasContainingItemPayload(const std::vector<uint8_t> &rawContainingItem)
{
    for (uint8_t value : rawContainingItem)
    {
        if (value != 0)
        {
            return true;
        }
    }

    return false;
}
}
