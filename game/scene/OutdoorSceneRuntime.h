#pragma once

#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/tables/MapStats.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class OutdoorSceneRuntime : public IMapSceneRuntime
{
public:
    struct AdvanceFrameResult
    {
        size_t previousMessageCount = 0;
        bool shouldOpenEventDialog = false;
    };

    OutdoorSceneRuntime(
        const std::string &mapFileName,
        const MapStatsEntry &mapEntry,
        OutdoorPartyRuntime &partyRuntime,
        OutdoorWorldRuntime &worldRuntime,
        const std::optional<ScriptedEventProgram> &localEventProgram,
        const std::optional<ScriptedEventProgram> &globalEventProgram
    );

    SceneKind kind() const override;
    const std::string &currentMapFileName() const override;
    Party &party() override;
    const Party &party() const override;
    EventRuntimeState *eventRuntimeState() override;
    const EventRuntimeState *eventRuntimeState() const override;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove() override;
    void advanceGameMinutes(float minutes) override;
    OutdoorPartyRuntime &partyRuntime();
    const OutdoorPartyRuntime &partyRuntime() const;
    OutdoorWorldRuntime &worldRuntime();
    const OutdoorWorldRuntime &worldRuntime() const;
    const std::optional<ScriptedEventProgram> &localEventProgram() const;
    const std::optional<ScriptedEventProgram> &globalEventProgram() const;
    AdvanceFrameResult advanceFrame(const OutdoorMovementInput &movementInput, float deltaSeconds);
    bool executeEventById(
        const std::optional<ScriptedEventProgram> &localEventProgram,
        uint16_t eventId,
        const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext,
        size_t &previousMessageCount
    );
    bool executeNpcTopicEventById(uint16_t eventId, size_t &previousMessageCount);

private:
    std::string m_mapFileName;
    MapStatsEntry m_mapEntry;
    OutdoorPartyRuntime *m_pPartyRuntime = nullptr;
    OutdoorWorldRuntime *m_pWorldRuntime = nullptr;
    std::optional<ScriptedEventProgram> m_localEventProgram;
    std::optional<ScriptedEventProgram> m_globalEventProgram;
    EventRuntime m_eventRuntime;
};
}
