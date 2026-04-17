#pragma once

#include "game/fx/FxSharedTypes.h"
#include "game/party/PartySpellSystem.h"

#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorGameView;
class ParticleSystem;

class OutdoorFxRuntime
{
public:
    using ParticleMotion = FxParticleMotion;
    using ParticleState = FxParticleState;

    struct GlowBillboardState
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
        bool renderVisibleBillboard = true;
    };

    struct LightEmitterState
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
    };

    struct ContactShadowState
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        uint32_t colorAbgr = 0x50000000u;
    };

    void reset();
    void update(OutdoorGameView &view, float deltaSeconds);
    void triggerPartySpellFx(OutdoorGameView &view, const PartySpellCastResult &result);

    const std::vector<GlowBillboardState> &glowBillboards() const;
    const std::vector<LightEmitterState> &lightEmitters() const;
    const std::vector<ContactShadowState> &contactShadows() const;

private:
    void syncRuntimeProjectiles(OutdoorGameView &view, bool refreshSpatialFx);
    void syncRuntimeActors(OutdoorGameView &view);
    void syncRuntimeDecorations(OutdoorGameView &view);
    void syncRuntimeSpriteObjects(OutdoorGameView &view);
    void syncWeatherParticles(OutdoorGameView &view, float deltaSeconds);
    void cleanupSeenIds(const OutdoorGameView &view);
    void addContactShadow(OutdoorGameView &view, float x, float y, float z, float radius, float heightScale);
    void addGlowBillboard(
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr,
        bool renderVisibleBillboard = true);
    void addLightEmitter(
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr);

    std::vector<GlowBillboardState> m_glowBillboards;
    std::vector<LightEmitterState> m_lightEmitters;
    std::vector<ContactShadowState> m_contactShadows;
    std::unordered_map<uint64_t, float> m_emitterCooldownBySourceKey;
    std::unordered_map<uint64_t, uint32_t> m_emitterSequenceBySourceKey;
    std::unordered_map<uint32_t, float> m_trailCooldownByProjectileId;
    std::unordered_set<uint32_t> m_seenImpactIds;
    float m_spatialRefreshAccumulatorSeconds = 0.0f;
    float m_snowEmissionAccumulator = 0.0f;
    float m_rainEmissionAccumulator = 0.0f;
    uint32_t m_weatherEmissionSequence = 0;
    bool m_hasSpatialSnapshot = false;
};
}
