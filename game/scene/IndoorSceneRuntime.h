#pragma once

#include "game/EventRuntime.h"
#include "game/MapDeltaData.h"
#include "game/scene/IMapSceneRuntime.h"

#include <cstddef>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class IndoorSceneRuntime : public IMapSceneRuntime
{
public:
    struct Snapshot
    {
        std::optional<MapDeltaData> mapDeltaData;
        std::optional<EventRuntimeState> eventRuntimeState;
        float mechanismAccumulatorMilliseconds = 0.0f;
    };

    IndoorSceneRuntime(
        const std::string &mapFileName,
        Party &party,
        const std::optional<MapDeltaData> &indoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState,
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

    const std::optional<MapDeltaData> &mapDeltaData() const;
    const std::optional<EventRuntimeState> &eventRuntimeStateStorage() const;
    const std::optional<EventIrProgram> &localEventIrProgram() const;
    const std::optional<EventIrProgram> &globalEventIrProgram() const;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    bool advanceSimulation(float deltaMilliseconds);
    bool activateEvent(uint16_t eventId, const std::string &sourceKind, size_t sourceIndex);

private:
    std::string m_mapFileName;
    Party *m_pParty = nullptr;
    std::optional<MapDeltaData> m_mapDeltaData;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    std::optional<EventIrProgram> m_localEventIrProgram;
    std::optional<EventIrProgram> m_globalEventIrProgram;
    EventRuntime m_eventRuntime;
    float m_mechanismAccumulatorMilliseconds = 0.0f;
};
}
