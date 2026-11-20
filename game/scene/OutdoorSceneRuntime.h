#pragma once

#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/mm9/Mm9PositionedTransitionRuntime.h"
#include "game/mm9/Mm9TeacherSchedule.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/tables/MapStats.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class HouseTable;
class NpcDialogTable;
class Mm9MapTransitionTable;
class Mm9TeacherScheduleTable;

// The map move for walking off an outdoor map edge from (x, y, footZ) while facing yawRadians.
EventRuntimeState::PendingMapMove buildBoundaryTravelMapMove(
    const MapEdgeTransition &transition,
    MapBoundaryEdge edge,
    float x,
    float y,
    float footZ,
    float yawRadians);

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
        const std::optional<ScriptedEventProgram> &globalEventProgram,
        const HouseTable *pHouseTable = nullptr,
        const NpcDialogTable *pNpcDialogTable = nullptr,
        const Mm9MapTransitionTable *pMm9MapTransitionTable = nullptr,
        const Mm9TeacherScheduleTable *pMm9TeacherScheduleTable = nullptr
    );

    SceneKind kind() const override;
    const std::string &currentMapFileName() const override;
    Party &party() override;
    const Party &party() const override;
    EventRuntimeState *eventRuntimeState() override;
    const EventRuntimeState *eventRuntimeState() const override;
    ISceneEventContext *sceneEventContext() override;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove() override;
    void advanceGameMinutes(float minutes) override;
    void advanceTurnBasedGameMinutes(float minutes) override;
    OutdoorPartyRuntime &partyRuntime();
    const OutdoorPartyRuntime &partyRuntime() const;
    OutdoorWorldRuntime &worldRuntime();
    const OutdoorWorldRuntime &worldRuntime() const;
    const std::optional<ScriptedEventProgram> &localEventProgram() const override;
    const std::optional<ScriptedEventProgram> &globalEventProgram() const override;
    AdvanceFrameResult advanceFrame(
        const OutdoorMovementInput &movementInput,
        float deltaSeconds,
        GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics = nullptr);
    bool executeEventById(
        const std::optional<ScriptedEventProgram> &localEventProgram,
        uint16_t eventId,
        const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext,
        size_t &previousMessageCount,
        bool allowGlobalFallback = false
    );
    bool executeNpcTopicEventById(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt);
    bool executeMapEventById(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt);
    bool executeEventHooks(EventRuntimeHookKind kind);
    bool processMonsterKilledEvents();

private:
    std::string m_mapFileName;
    MapStatsEntry m_mapEntry;
    OutdoorPartyRuntime *m_pPartyRuntime = nullptr;
    OutdoorWorldRuntime *m_pWorldRuntime = nullptr;
    std::optional<ScriptedEventProgram> m_localEventProgram;
    std::optional<ScriptedEventProgram> m_globalEventProgram;
    EventRuntime m_eventRuntime;
    Mm9PositionedTransitionRuntime m_mm9PositionedTransitionRuntime;
    Mm9TeacherScheduleRuntime m_mm9TeacherScheduleRuntime;
};
}
