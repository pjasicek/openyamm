#pragma once

#include "game/GameSession.h"
#include "game/scene/IMapSceneRuntime.h"

#include <optional>

namespace OpenYAMM::Game
{
class GameplayController
{
public:
    void bindSession(GameSession &session);
    void bindRuntime(IMapSceneRuntime *pRuntime);
    void clearRuntime();

    bool hasRuntime() const;
    Party *party();
    const Party *party() const;
    EventRuntimeState *eventRuntimeState();
    const EventRuntimeState *eventRuntimeState() const;

    void synchronizeSessionFromRuntime();
    bool advanceGameMinutes(float minutes);
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();

private:
    GameSession *m_pSession = nullptr;
    IMapSceneRuntime *m_pRuntime = nullptr;
};
}
