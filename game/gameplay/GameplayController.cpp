#include "game/gameplay/GameplayController.h"

#include "game/rules/GameRules.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/OutdoorSceneRuntime.h"

namespace OpenYAMM::Game
{
void GameplayController::bindSession(GameSession &session)
{
    m_pSession = &session;
}

void GameplayController::bindRuntime(IMapSceneRuntime *pRuntime)
{
    m_pRuntime = pRuntime;

    if (m_pSession == nullptr)
    {
        return;
    }

    IGameplayWorldRuntime *pWorldRuntime = nullptr;

    if (pRuntime != nullptr)
    {
        if (pRuntime->kind() == SceneKind::Outdoor)
        {
            OutdoorSceneRuntime *pOutdoorRuntime = static_cast<OutdoorSceneRuntime *>(pRuntime);
            pWorldRuntime = &pOutdoorRuntime->worldRuntime();
        }
        else if (pRuntime->kind() == SceneKind::Indoor)
        {
            IndoorSceneRuntime *pIndoorRuntime = static_cast<IndoorSceneRuntime *>(pRuntime);
            pWorldRuntime = &pIndoorRuntime->worldRuntime();
        }
    }

    m_pSession->bindActiveWorldRuntime(pWorldRuntime);
    m_pSession->gameplayScreenRuntime().syncPartyConditionPortraits();
}

void GameplayController::clearRuntime()
{
    m_pRuntime = nullptr;

    if (m_pSession != nullptr)
    {
        m_pSession->bindActiveWorldRuntime(nullptr);
    }
}

bool GameplayController::hasRuntime() const
{
    return m_pRuntime != nullptr;
}

Party *GameplayController::party()
{
    return m_pRuntime != nullptr ? &m_pRuntime->party() : nullptr;
}

const Party *GameplayController::party() const
{
    return m_pRuntime != nullptr ? &m_pRuntime->party() : nullptr;
}

EventRuntimeState *GameplayController::eventRuntimeState()
{
    return m_pRuntime != nullptr ? m_pRuntime->eventRuntimeState() : nullptr;
}

const EventRuntimeState *GameplayController::eventRuntimeState() const
{
    return m_pRuntime != nullptr ? m_pRuntime->eventRuntimeState() : nullptr;
}

void GameplayController::synchronizeSessionFromRuntime()
{
    if (m_pSession == nullptr || m_pRuntime == nullptr)
    {
        return;
    }

    m_pSession->setCurrentMapFileName(m_pRuntime->currentMapFileName());
    m_pSession->setPartyState(m_pRuntime->party());
}

bool GameplayController::advanceGameMinutes(float minutes)
{
    if (m_pRuntime == nullptr)
    {
        return false;
    }

    m_pRuntime->advanceGameMinutes(minutes);
    m_pRuntime->party().advanceTimedStates(minutes * 60.0f);

    if (m_pSession != nullptr)
    {
        synchronizeSessionFromRuntime();
    }

    return true;
}

bool GameplayController::advanceTurnBasedGameMinutes(float minutes)
{
    if (m_pRuntime == nullptr || minutes <= 0.0f)
    {
        return false;
    }

    // A completed turn is all the time that passes in turn-based combat (OE NextTurn -> _494035_timed_effects): the
    // clock and buffs, the per-second regeneration and the monsters' spell effects advance by the turn's game time.
    constexpr float GameMinutesPerRealSecond = 0.5f;
    const float equivalentRealSeconds = minutes / GameMinutesPerRealSecond;
    Party &party = m_pRuntime->party();
    m_pRuntime->advanceTurnBasedGameMinutes(minutes);
    party.advanceTimedStates(minutes * 60.0f);
    party.updateRegeneration(equivalentRealSeconds);

    IGameplayWorldRuntime *pWorldRuntime = m_pSession != nullptr ? m_pSession->activeWorldRuntime() : nullptr;

    if (pWorldRuntime != nullptr)
    {
        party.rules().skills.updateRegeneration(party, *pWorldRuntime, equivalentRealSeconds);
        pWorldRuntime->advanceTurnBasedActorTimers(equivalentRealSeconds);
    }

    return true;
}

std::optional<EventRuntimeState::PendingMapMove> GameplayController::consumePendingMapMove()
{
    if (m_pSession != nullptr)
    {
        std::optional<EventRuntimeState::PendingMapMove> pendingMapMove = m_pSession->consumePendingMapMove();

        if (pendingMapMove)
        {
            return pendingMapMove;
        }
    }

    return m_pRuntime != nullptr ? m_pRuntime->consumePendingMapMove() : std::nullopt;
}

std::optional<EventRuntimeState::PendingArcomageGame> GameplayController::consumePendingArcomageGame()
{
    EventRuntimeState *pRuntimeState = eventRuntimeState();

    if (pRuntimeState == nullptr || !pRuntimeState->pendingArcomageGame.has_value())
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingArcomageGame> pendingArcomageGame = pRuntimeState->pendingArcomageGame;
    pRuntimeState->pendingArcomageGame.reset();
    return pendingArcomageGame;
}
}
