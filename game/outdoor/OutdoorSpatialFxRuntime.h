#pragma once

#include "game/render/lighting/RenderLight.h"

#include <array>
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
    void addContactShadow(OutdoorGameView &view, float x, float y, float z, float radius, float heightScale);
    void addGlowBillboard(OutdoorGameView &view, float x, float y, float z, float radius, uint32_t colorAbgr);
    void addLightEmitter(
        OutdoorGameView &view,
        float x,
        float y,
        float z,
        float radius,
        uint32_t colorAbgr,
        RenderLightKind kind = RenderLightKind::GenericFx,
        uint32_t stableId = 0,
        bool important = false);

    std::unordered_map<uint64_t, float> m_emitterCooldownBySourceKey;
    std::unordered_map<uint64_t, uint32_t> m_emitterSequenceBySourceKey;
    float m_spatialRefreshAccumulatorSeconds = 0.0f;
    bool m_hasSpatialSnapshot = false;
    // The party's daytime shade for the torch (0 in sunlight, 1 in full shade), eased toward the last probe sample.
    float m_partyTorchShade = 0.0f;
    float m_partyTorchShadeTarget = 0.0f;
    std::array<float, 3> m_partyTorchShadePosition = {};
    bool m_partyTorchShadeSampled = false;
};
}
