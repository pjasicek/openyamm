#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/PartySpellSystem.h"
#include "game/tables/PortraitFxEventTable.h"

#include <vector>

namespace OpenYAMM::Game
{
class GameSession;
class GameplayScreenRuntime;

class GameplayFxService
{
public:
    struct GameplayScreenOverlayState
    {
        float remainingSeconds = 0.0f;
        float durationSeconds = 0.0f;
        float peakAlpha = 0.0f;
        uint32_t colorAbgr = 0x00000000u;
    };

    explicit GameplayFxService(GameSession &session);

    void clear();
    void syncActiveWorldProjectilePresentation();
    void triggerPortraitEventFxWithoutSpeech(
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        PortraitFxEventKind kind) const;
    void triggerPortraitSpellFx(const PartySpellCastResult &result) const;
    void triggerGameplayScreenOverlay(const PartySpellCastResult::ScreenOverlayRequest &request);
    void advanceGameplayScreenOverlay(float deltaSeconds);
    void renderGameplayScreenOverlay(GameplayScreenRuntime &runtime, int width, int height) const;
    void consumePendingEventFxRequests(GameplayScreenRuntime &runtime) const;
    const std::vector<GameplayProjectilePresentationState> &activeProjectilePresentationStates() const;
    const std::vector<GameplayProjectileImpactPresentationState> &activeProjectileImpactPresentationStates() const;

private:
    void consumePendingPortraitEventFxRequest(
        GameplayScreenRuntime &runtime,
        const EventRuntimeState::PortraitFxRequest &request) const;
    void consumePendingSpellFxRequest(
        GameplayScreenRuntime &runtime,
        const EventRuntimeState::SpellFxRequest &request) const;

    GameSession &m_session;
    GameplayScreenOverlayState m_gameplayScreenOverlayState;
    std::vector<GameplayProjectilePresentationState> m_activeProjectilePresentationStates;
    std::vector<GameplayProjectileImpactPresentationState> m_activeProjectileImpactPresentationStates;
};
}
