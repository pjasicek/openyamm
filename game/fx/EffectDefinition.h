#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct EffectVectorKey
{
    float time = 0.0f;
    std::array<float, 3> value = {};
};

struct EffectScalarKey
{
    float time = 0.0f;
    float value = 0.0f;
};

struct EffectColorKey
{
    float time = 0.0f;
    std::array<uint8_t, 3> rgb = {255, 255, 255};
    uint8_t transparency = 0;
};

enum class EffectEmissionShape
{
    Point,
    Plane,
    Sphere,
    PlaneIn,
    PlaneOut,
    Cone,
    Circle
};

enum class EffectBlendMode
{
    Alpha,
    Additive,
    Multiply
};

enum class EffectParticleSpace
{
    World,
    Local
};

enum class EffectSpriteAlignment
{
    CameraFacing,
    WorldPlane,
    // Camera-facing, with the sprite's width laid along the direction of travel (a particle's velocity, or the
    // effect's own movement for fixed sprites); stretch_u then lengthens it into a streak.
    Velocity
};

struct EffectComponentLink
{
    std::optional<uint32_t> componentId;
    std::string nodeName;
};

struct EffectSpriteEmitterDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    uint32_t repeatCount = 1;
    std::string spriteResource;
    uint32_t spritesPerEmission = 1;
    float emissionIntervalSeconds = 0.0f;
    // World units between emissions along the emitter's path (0: emit by time). Each emission lands at its own point
    // on the path, so a fast projectile's trail stays continuous; a stationary emitter sheds nothing after its first.
    float emissionDistance = 0.0f;
    float particleLifetimeSeconds = 1.0f;
    EffectEmissionShape emissionShape = EffectEmissionShape::Point;
    float radius = 0.0f;
    std::array<float, 3> planeDirection = {0.0f, 1.0f, 0.0f};
    float velocity = 0.0f;
    std::array<float, 3> windDirection = {};
    float windAmount = 0.0f;
    // World units per second squared pulling world-space particles down the world's -Z (chips, drops).
    float gravity = 0.0f;
    std::array<float, 3> offset = {};
    std::array<float, 3> rotationPerTick = {};
    float stretchU = 1.0f;
    float stretchV = 1.0f;
    // Each particle starts at a random roll about the view axis (camera-facing and world-plane sprites), so shed
    // puffs repeat less; spin_speed then turns it at 50-100% of that many radians per second, either way.
    bool randomRoll = false;
    float spinSpeed = 0.0f;
    EffectBlendMode blendMode = EffectBlendMode::Alpha;
    // False for MM9's additive sprites (LithTech ONE/ONE): the light is the texture's colour times the vertex colour,
    // weighted by neither the texture's alpha (its glow textures are already dark where transparent) nor the
    // opacity, drawn from texels without the transparent-edge colour bleed and not into the bloom glow.
    bool additiveTextureAlpha = true;
    EffectParticleSpace particleSpace = EffectParticleSpace::World;
    EffectSpriteAlignment alignment = EffectSpriteAlignment::CameraFacing;
    std::array<float, 3> planeRight = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> planeUp = {0.0f, 0.0f, 1.0f};
    EffectComponentLink link;
    std::vector<EffectColorKey> colorKeys;
    std::vector<EffectScalarKey> scaleKeys;
    std::vector<EffectVectorKey> motionKeys;
    // The body node MM9 puts this emitter on (`body_anchor`: left_hand, right_hand ...; empty: the effect's origin).
    // It emits at the effect's origin like the others; a spawn may keep only one anchor's emitters
    // (EffectSpawnParams::bodyAnchor).
    std::string bodyAnchor;
};

struct EffectModelDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    uint32_t repeatCount = 1;
    std::string modelResource;
    std::string animationClip;
    std::array<float, 3> offset = {};
    bool visible = false;
    EffectComponentLink link;
};

struct EffectNullDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    uint32_t repeatCount = 1;
    std::array<float, 3> offset = {};
    std::array<float, 3> rotationPerTick = {};
    EffectComponentLink link;
    std::vector<EffectScalarKey> scaleKeys;
    std::vector<EffectVectorKey> motionKeys;
};

struct EffectSpriteDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    uint32_t repeatCount = 1;
    std::string spriteResource;
    std::array<float, 3> offset = {};
    float stretchU = 1.0f;
    float stretchV = 1.0f;
    EffectBlendMode blendMode = EffectBlendMode::Additive;
    // False for MM9's additive sprites (LithTech ONE/ONE): the light is the texture's colour times the vertex colour,
    // weighted by neither the texture's alpha (its glow textures are already dark where transparent) nor the
    // opacity, drawn from texels without the transparent-edge colour bleed and not into the bloom glow.
    bool additiveTextureAlpha = true;
    EffectSpriteAlignment alignment = EffectSpriteAlignment::CameraFacing;
    std::array<float, 3> planeRight = {1.0f, 0.0f, 0.0f};
    std::array<float, 3> planeUp = {0.0f, 0.0f, 1.0f};
    EffectComponentLink link;
    std::vector<EffectColorKey> colorKeys;
    std::vector<EffectScalarKey> scaleKeys;
    std::vector<EffectVectorKey> motionKeys;
};

// A camera-facing strip through the recent positions of the effect (a projectile's trail). Samples are taken every
// sample_distance world units and live lifetime_seconds, and the strip is at most max_length units long (0: no cap),
// so a fast projectile keeps the same trail length as a slow one. Phase runs from 0 at the head to 1 at whichever
// limit a sample reaches first.
// The texture's first frame repeats every texture_length units along the path and scrolls by scroll_speed repeats
// per second; its red channel is the trail's noise. Width, colour and transparency follow phase.
struct EffectRibbonDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    std::string spriteResource;
    EffectBlendMode blendMode = EffectBlendMode::Additive;
    std::array<float, 3> offset = {};
    float lifetimeSeconds = 0.3f;
    float maxLength = 0.0f;
    float sampleDistance = 16.0f;
    float width = 24.0f;
    float textureLength = 128.0f;
    float scrollSpeed = 0.0f;
    // Solid body added under the noise: about 0.3 gives a continuous flame, 0 leaves only the bright texture (arcs).
    float fill = 0.3f;
    // Noise erosion at the tail, 0 (none) to 1 (the tail dissolves completely).
    float erosion = 0.0f;
    // Brightness of a white-hot line along the centre, fading towards the tail.
    float core = 0.0f;
    // Sideways displacement of each sample in world units, re-randomised jitter_rate times per second (lightning).
    float jitter = 0.0f;
    float jitterRate = 0.0f;
    // A beam: instead of trailing, the strip runs straight from the effect's position to its beam target
    // (EffectSystem::setBeamTarget), sampled every sample_distance, while the component lasts. Its width keys run along
    // it, start (0) to target (1), so a beam aimed at the viewer can taper to nothing at the eye; its colour is the
    // keys' value at phase 0; jitter displaces every sample but the two ends.
    bool beam = false;
    std::vector<EffectScalarKey> widthKeys;
    std::vector<EffectColorKey> colorKeys;
};

struct EffectSoundDefinition
{
    uint32_t componentId = 0;
    float startSeconds = 0.0f;
    float endSeconds = 0.0f;
    std::string soundResource;
    bool spatial = true;
    bool loop = false;
    float volume = 1.0f;
    float pitch = 1.0f;
    float innerRadius = 100.0f;
    float outerRadius = 500.0f;
    bool followsEmitter = false;
};

enum class EffectTimingProfile
{
    Predictable,
    Mm9Native
};

struct EffectDefinition
{
    std::string id;
    float durationSeconds = 0.0f;
    EffectTimingProfile timingProfile = EffectTimingProfile::Predictable;
    std::vector<EffectModelDefinition> models;
    std::vector<EffectNullDefinition> nulls;
    std::vector<EffectSpriteDefinition> sprites;
    std::vector<EffectSpriteEmitterDefinition> spriteEmitters;
    std::vector<EffectRibbonDefinition> ribbons;
    std::vector<EffectSoundDefinition> sounds;
};
}
