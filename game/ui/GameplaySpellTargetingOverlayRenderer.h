#pragma once

#include "game/gameplay/GameplayScreenState.h"

#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class GameplaySpellService;

class GameplaySpellTargetingOverlayRenderer
{
public:
    struct AreaMarkerVisualPolicy
    {
        uint32_t spellId = 0;
        float radius = 0.0f;
        uint32_t ringColorAbgr = 0;
        uint32_t baseColorAbgr = 0;
        uint32_t accentColorAbgr = 0;
        float shaderSpeed = 0.0f;
        float shaderFrequency = 0.0f;
        float shaderPrimaryBandWidth = 0.0f;
        float shaderSecondaryBandWidth = 0.0f;
    };

    static void renderPendingSpellTargetingOverlay(
        GameplayScreenRuntime &context,
        const GameplaySpellService &spellService,
        const GameplayScreenState::PendingSpellTargetState &pendingSpellCast,
        int width,
        int height,
        float cursorX,
        float cursorY);

    static std::optional<AreaMarkerVisualPolicy> resolveAreaMarkerVisualPolicy(
        const GameplayScreenState::PendingSpellTargetState &pendingSpellCast);
};
} // namespace OpenYAMM::Game
