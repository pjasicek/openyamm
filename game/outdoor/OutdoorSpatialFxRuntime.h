#pragma once

#include <cstdint>
#include <unordered_map>

namespace OpenYAMM::Game
{
class OutdoorGameView;

class OutdoorSpatialFxRuntime
{
public:
    void reset();
    bool beginFrame(OutdoorGameView &view, float deltaSeconds);
    void syncSpatialFx(OutdoorGameView &view, bool refreshSpatialFx);

private:
    void syncOutdoorProjectileContactShadows(OutdoorGameView &view, bool refreshSpatialFx);
    void syncPartyTorchLight(OutdoorGameView &view);
    void syncActorSpatialFx(OutdoorGameView &view);
    void syncDecorationEmitters(OutdoorGameView &view);
    void syncSpriteObjectSpatialFx(OutdoorGameView &view);
    void syncWeatherParticles(OutdoorGameView &view, float deltaSeconds);
    void addContactShadow(OutdoorGameView &view, float x, float y, float z, float radius, float heightScale);
    void addGlowBillboard(OutdoorGameView &view, float x, float y, float z, float radius, uint32_t colorAbgr);
    void addLightEmitter(
        OutdoorGameView &view,
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr);

    std::unordered_map<uint64_t, float> m_emitterCooldownBySourceKey;
    std::unordered_map<uint64_t, uint32_t> m_emitterSequenceBySourceKey;
    float m_spatialRefreshAccumulatorSeconds = 0.0f;
    float m_snowEmissionAccumulator = 0.0f;
    float m_rainEmissionAccumulator = 0.0f;
    uint32_t m_weatherEmissionSequence = 0;
    bool m_hasSpatialSnapshot = false;
};
}
