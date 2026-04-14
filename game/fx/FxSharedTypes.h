#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
enum class FxParticleBlendMode
{
    Alpha,
    Additive,
};

enum class FxParticleAlignment
{
    CameraFacing,
    VelocityStretched,
    GroundAligned,
};

enum class FxParticleMaterial
{
    SoftBlob,
    Smoke,
    Mist,
    Ember,
    Spark,
};

enum class FxParticleTag
{
    Trail,
    Impact,
    DecorationEmitter,
    Buff,
    Misc,
};

enum class FxParticleMotion
{
    StaticFade,
    Ascend,
    Burst,
    VelocityTrail,
    BallisticTrail,
    Drift,
};

struct FxParticleState
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
    float size = 0.0f;
    float endSize = 0.0f;
    float drag = 0.0f;
    float rotationRadians = 0.0f;
    float angularVelocityRadians = 0.0f;
    float stretch = 1.0f;
    float ageSeconds = 0.0f;
    float fadeInSeconds = 0.0f;
    float lifetimeSeconds = 0.0f;
    uint32_t startColorAbgr = 0xffffffffu;
    uint32_t endColorAbgr = 0x00ffffffu;
    FxParticleMotion motion = FxParticleMotion::StaticFade;
    FxParticleBlendMode blendMode = FxParticleBlendMode::Alpha;
    FxParticleAlignment alignment = FxParticleAlignment::CameraFacing;
    FxParticleMaterial material = FxParticleMaterial::SoftBlob;
    FxParticleTag tag = FxParticleTag::Misc;
};
}
