#pragma once

#include "game/EventIr.h"
#include "game/EventRuntime.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/scene/IMapSceneRuntime.h"

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
        OutdoorPartyRuntime &partyRuntime,
        OutdoorWorldRuntime &worldRuntime,
        const std::optional<EventIrProgram> &localEventIrProgram,
        const std::optional<EventIrProgram> &globalEventIrProgram
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
    const std::optional<EventIrProgram> &localEventIrProgram() const;
    const std::optional<EventIrProgram> &globalEventIrProgram() const;
    AdvanceFrameResult advanceFrame(const OutdoorMovementInput &movementInput, float deltaSeconds);
    bool executeEventById(
        const std::optional<EventIrProgram> &localEventIrProgram,
        uint16_t eventId,
        const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext,
        size_t &previousMessageCount
    );

private:
    std::string m_mapFileName;
    OutdoorPartyRuntime *m_pPartyRuntime = nullptr;
    OutdoorWorldRuntime *m_pWorldRuntime = nullptr;
    std::optional<EventIrProgram> m_localEventIrProgram;
    std::optional<EventIrProgram> m_globalEventIrProgram;
    EventRuntime m_eventRuntime;
};
}
