#include "game/fx/MistWisps.h"

#include "game/fx/ParticleSystem.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// Wisps appearing per second once the first set stands, and the most one frame may add.
constexpr float SpawnsPerSecond = 8.0f;
constexpr float MaxSpawnBudget = 3.0f;
// No wisp appears nearer than this: one fading in over the eye would tint the whole view.
constexpr float MinimumSpawnDistance = 130.0f;
// A wisp's opacity in the densest mist.
constexpr float WispOpacity = 0.7f;
constexpr float Pi = 3.14159265f;

uint32_t packAbgr(const std::array<float, 3> &color, float alpha)
{
    const auto channel = [](float value) { return uint32_t(std::clamp(value, 0.0f, 1.0f) * 255.0f + 0.5f); };
    return (channel(alpha) << 24) | (channel(color[2]) << 16) | (channel(color[1]) << 8) | channel(color[0]);
}
}

MistSample sampleMist(const MapMist &mist, const std::array<float, 3> &point)
{
    MistSample sample = {};
    std::array<float, 3> weighted = {};
    float daylightWeight = 0.0f;
    const auto add = [&](float density, const std::array<float, 3> &color, bool followsDaylight)
    {
        if (density <= 0.0f)
        {
            return;
        }
        sample.density += density;
        for (size_t channel = 0; channel < 3; ++channel)
        {
            weighted[channel] += color[channel] * density;
        }
        daylightWeight += followsDaylight ? density : 0.0f;
    };

    for (const MistLayer &layer : mist.layers)
    {
        add(mistLayerDensityAt(layer, point[2]), layer.color, layer.followsDaylight);
    }
    for (const MistVolume &volume : mist.volumes)
    {
        float radiusSquared = 0.0f;
        for (size_t axis = 0; axis < 3; ++axis)
        {
            const float offset = (point[axis] - volume.position[axis]) / std::max(volume.radius[axis], 1.0f);
            radiusSquared += offset * offset;
        }
        add(1.0f - radiusSquared, volume.color, volume.followsDaylight);
    }

    if (sample.density > 0.0f)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            sample.color[channel] = weighted[channel] / sample.density;
        }
        sample.followsDaylight = daylightWeight >= sample.density * 0.5f;
        sample.density = std::min(sample.density, 1.0f);
    }
    return sample;
}

float MistWisps::random()
{
    m_seed = m_seed * 1664525u + 1013904223u;
    return float(m_seed >> 8) / 16777216.0f;
}

bool MistWisps::spawn(const MapMist &mist, const std::array<float, 3> &eye, const std::array<float, 3> &light,
    float startAge, ParticleSystem &particles)
{
    // A volume in reach takes some of the wisps; the layer the rest.
    std::array<size_t, MaxMistVolumes> nearVolumes = {};
    size_t nearVolumeCount = 0;
    for (size_t index = 0; index < mist.volumes.size() && nearVolumeCount < nearVolumes.size(); ++index)
    {
        const MistVolume &volume = mist.volumes[index];
        const float dx = volume.position[0] - eye[0];
        const float dy = volume.position[1] - eye[1];
        const float dz = volume.position[2] - eye[2];
        const float reach = std::max({volume.radius[0], volume.radius[1], volume.radius[2]}) + SpawnRadius;
        if (dx * dx + dy * dy + dz * dz < reach * reach)
        {
            nearVolumes[nearVolumeCount++] = index;
        }
    }

    // The layer the eye stands in: the densest at waist height.
    const MistLayer *pLayer = nullptr;
    float bestDensity = -1.0f;
    for (const MistLayer &layer : mist.layers)
    {
        const float density = mistLayerDensityAt(layer, eye[2] - 75.0f);
        if (density > bestDensity)
        {
            bestDensity = density;
            pLayer = &layer;
        }
    }

    std::array<float, 3> point = {};
    const bool inVolume = nearVolumeCount > 0 && (pLayer == nullptr || random() < 0.4f);
    if (inVolume)
    {
        const size_t pick = size_t(random() * float(nearVolumeCount)) % nearVolumeCount;
        const MistVolume &volume = mist.volumes[nearVolumes[pick]];
        for (size_t axis = 0; axis < 3; ++axis)
        {
            point[axis] = volume.position[axis] + (random() * 2.0f - 1.0f) * volume.radius[axis] * 0.6f;
        }
    }
    else if (pLayer != nullptr)
    {
        const float angle = random() * 2.0f * Pi;
        const float distance = MinimumSpawnDistance + std::sqrt(random()) * (SpawnRadius - MinimumSpawnDistance);
        // About waist height while the eye stands in the mist, which keeps a wisp's lower edge off the floor it would
        // cut a line into (the party's eye is some 170 above it); at the mist's top when the eye looks down on it.
        const float falloff = pLayer->falloffHeight;
        const float centre = std::min(eye[2] - 75.0f, pLayer->baseHeight + falloff * 0.35f);
        point = {eye[0] + std::cos(angle) * distance, eye[1] + std::sin(angle) * distance,
            centre + (random() * 2.0f - 1.0f) * 30.0f};
    }
    else
    {
        return false;
    }

    const float dx = point[0] - eye[0];
    const float dy = point[1] - eye[1];
    const float dz = point[2] - eye[2];
    const float eyeDistanceSquared = dx * dx + dy * dy + dz * dz;
    const MistSample sample = sampleMist(mist, point);
    if (sample.density < 0.08f || eyeDistanceSquared < MinimumSpawnDistance * MinimumSpawnDistance
        || eyeDistanceSquared > (SpawnRadius * 1.5f) * (SpawnRadius * 1.5f))
    {
        return false;
    }

    // Lighter than the mist behind it: in the mist's own colour a wisp cannot be told from it.
    std::array<float, 3> color = {};
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const float lifted = sample.color[channel] + (1.0f - sample.color[channel]) * 0.55f;
        color[channel] = lifted * (sample.followsDaylight ? light[channel] : 1.0f);
    }

    FxParticleState particle = {};
    particle.x = point[0];
    particle.y = point[1];
    particle.z = point[2];
    const std::array<float, 2> drift = pLayer != nullptr ? pLayer->drift : MistLayer{}.drift;
    particle.velocityX = drift[0] * 1.5f + (random() * 2.0f - 1.0f) * 9.0f;
    particle.velocityY = drift[1] * 1.5f + (random() * 2.0f - 1.0f) * 9.0f;
    particle.velocityZ = (random() * 2.0f - 1.0f) * 2.0f;
    // Low and long, drawn out along its drift: a streak of mist rather than a puff.
    particle.size = 150.0f + random() * 90.0f;
    particle.endSize = particle.size * (1.15f + random() * 0.25f);
    particle.stretch = 3.0f + random() * 1.5f;
    particle.lifetimeSeconds = 8.0f + random() * 5.0f;
    particle.ageSeconds = startAge * particle.lifetimeSeconds;
    particle.fadeInSeconds = 2.5f;
    particle.fadeOutStartSeconds = particle.lifetimeSeconds * 0.5f;
    particle.startColorAbgr = packAbgr(color, WispOpacity * sample.density);
    particle.endColorAbgr = packAbgr(color, WispOpacity * sample.density);
    particle.motion = FxParticleMotion::VelocityTrail;
    particle.blendMode = FxParticleBlendMode::Alpha;
    particle.alignment = FxParticleAlignment::VelocityStretched;
    // The soft blob falls to nothing at the quad's edge; the mist texture keeps a tenth there, which shows as a line.
    particle.material = FxParticleMaterial::SoftBlob;
    particle.tag = FxParticleTag::MapMist;
    return particles.addParticle(particle);
}

void MistWisps::update(const MapMist &mist, const std::array<float, 3> &eye, float elapsedSeconds,
    const std::array<float, 3> &light, ParticleSystem &particles)
{
    const float deltaSeconds = m_lastElapsedSeconds >= 0.0f
        ? std::clamp(elapsedSeconds - m_lastElapsedSeconds, 0.0f, 0.1f) : 0.0f;
    m_lastElapsedSeconds = elapsedSeconds;
    if (!mist.enabled())
    {
        return;
    }

    // Wisps left far behind (a teleport, a fast flight) make room for new ones around the eye.
    constexpr float KeepRadius = SpawnRadius * 2.0f;
    size_t alive = 0;
    size_t stranded = 0;
    for (const FxParticleState &particle : particles.particles())
    {
        if (particle.tag != FxParticleTag::MapMist)
        {
            continue;
        }
        const float dx = particle.x - eye[0];
        const float dy = particle.y - eye[1];
        const float dz = particle.z - eye[2];
        const bool far = dx * dx + dy * dy + dz * dz > KeepRadius * KeepRadius;
        stranded += far ? 1 : 0;
        alive += far ? 0 : 1;
    }
    if (stranded > 0)
    {
        particles.removeParticlesIf([&eye](const FxParticleState &particle)
        {
            const float dx = particle.x - eye[0];
            const float dy = particle.y - eye[1];
            const float dz = particle.z - eye[2];
            return particle.tag == FxParticleTag::MapMist && dx * dx + dy * dy + dz * dz > KeepRadius * KeepRadius;
        });
    }

    if (alive == 0)
    {
        // The first set (a map just entered): part-way through their lives, so they neither appear nor leave together.
        for (size_t index = 0; index < TargetCount; ++index)
        {
            spawn(mist, eye, light, random() * 0.45f, particles);
        }
        m_spawnBudget = 0.0f;
        return;
    }

    m_spawnBudget = std::min(m_spawnBudget + deltaSeconds * SpawnsPerSecond, MaxSpawnBudget);
    while (m_spawnBudget >= 1.0f && alive < TargetCount)
    {
        m_spawnBudget -= 1.0f;
        alive += spawn(mist, eye, light, 0.0f, particles) ? 1 : 0;
    }
}
}
