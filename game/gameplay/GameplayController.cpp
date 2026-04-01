#include "game/gameplay/GameplayController.h"

namespace OpenYAMM::Game
{
void GameplayController::bindSession(GameSession &session)
{
    m_pSession = &session;
}

void GameplayController::bindRuntime(IMapSceneRuntime *pRuntime)
{
    m_pRuntime = pRuntime;
}

void GameplayController::clearRuntime()
{
    m_pRuntime = nullptr;
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
}
