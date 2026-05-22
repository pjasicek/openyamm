#pragma once

#include <bx/math.h>

#include <cstdint>

namespace OpenYAMM::Game
{
enum class RenderLightKind : uint8_t
{
    Static,
    Decoration,
    Torch,
    Projectile,
    Impact,
    ActorGlow,
    SpriteGlow,
    ClusteredFx,
    GenericFx,
};

struct RenderLight
{
    bx::Vec3 position = {0.0f, 0.0f, 0.0f};
    float radius = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
    float intensity = 1.0f;
    int16_t sectorId = -1;
    RenderLightKind kind = RenderLightKind::Static;
    uint32_t stableId = 0;
    bool dynamic = false;
    bool important = false;
};
}
