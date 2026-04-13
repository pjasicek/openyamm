#include "game/scene/IndoorSceneRuntime.h"

#include <iostream>

namespace OpenYAMM::Game
{
namespace
{
bool hasMovingMechanism(const EventRuntimeState &eventRuntimeState)
{
    for (const auto &entry : eventRuntimeState.mechanisms)
    {
        if (entry.second.isMoving)
        {
            return true;
        }
    }

    return false;
}
}

IndoorSceneRuntime::IndoorSceneRuntime(
    const std::string &mapFileName,
    Party &party,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
    : m_mapFileName(mapFileName)
    , m_pParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
{
}

SceneKind IndoorSceneRuntime::kind() const
{
    return SceneKind::Indoor;
}

const std::string &IndoorSceneRuntime::currentMapFileName() const
{
    return m_mapFileName;
}

Party &IndoorSceneRuntime::party()
{
    return *m_pParty;
}

const Party &IndoorSceneRuntime::party() const
{
    return *m_pParty;
}

EventRuntimeState *IndoorSceneRuntime::eventRuntimeState()
{
    return m_eventRuntimeState ? &*m_eventRuntimeState : nullptr;
}

const EventRuntimeState *IndoorSceneRuntime::eventRuntimeState() const
{
    return m_eventRuntimeState ? &*m_eventRuntimeState : nullptr;
}

std::optional<EventRuntimeState::PendingMapMove> IndoorSceneRuntime::consumePendingMapMove()
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingMapMove> pendingMapMove = std::move(m_eventRuntimeState->pendingMapMove);
    m_eventRuntimeState->pendingMapMove.reset();
    return pendingMapMove;
}

void IndoorSceneRuntime::advanceGameMinutes(float minutes)
{
    (void)minutes;
}

const std::optional<MapDeltaData> &IndoorSceneRuntime::mapDeltaData() const
{
    return m_mapDeltaData;
}

const std::optional<EventRuntimeState> &IndoorSceneRuntime::eventRuntimeStateStorage() const
{
    return m_eventRuntimeState;
}

const std::optional<ScriptedEventProgram> &IndoorSceneRuntime::localEventProgram() const
{
    return m_localEventProgram;
}

const std::optional<ScriptedEventProgram> &IndoorSceneRuntime::globalEventProgram() const
{
    return m_globalEventProgram;
}

IndoorSceneRuntime::Snapshot IndoorSceneRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.mapDeltaData = m_mapDeltaData;
    snapshot.eventRuntimeState = m_eventRuntimeState;
    snapshot.mechanismAccumulatorMilliseconds = m_mechanismAccumulatorMilliseconds;
    return snapshot;
}

void IndoorSceneRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_mapDeltaData = snapshot.mapDeltaData;
    m_eventRuntimeState = snapshot.eventRuntimeState;
    m_mechanismAccumulatorMilliseconds = snapshot.mechanismAccumulatorMilliseconds;
}

bool IndoorSceneRuntime::advanceSimulation(float deltaMilliseconds)
{
    if (!m_eventRuntimeState || !m_mapDeltaData || deltaMilliseconds <= 0.0f)
    {
        return false;
    }

    if (!hasMovingMechanism(*m_eventRuntimeState))
    {
        m_mechanismAccumulatorMilliseconds = 0.0f;
        return false;
    }

    int mechanismSteps = 0;
    constexpr float MechanismStepMilliseconds = 1000.0f / 120.0f;
    constexpr int MaximumMechanismStepsPerFrame = 8;
    m_mechanismAccumulatorMilliseconds += deltaMilliseconds;

    while (
        m_mechanismAccumulatorMilliseconds >= MechanismStepMilliseconds
        && mechanismSteps < MaximumMechanismStepsPerFrame
    )
    {
        m_eventRuntime.advanceMechanisms(m_mapDeltaData, MechanismStepMilliseconds, *m_eventRuntimeState);
        m_mechanismAccumulatorMilliseconds -= MechanismStepMilliseconds;
        ++mechanismSteps;
    }

    if (
        mechanismSteps == MaximumMechanismStepsPerFrame
        && m_mechanismAccumulatorMilliseconds > MechanismStepMilliseconds
    )
    {
        m_mechanismAccumulatorMilliseconds = MechanismStepMilliseconds;
    }

    return mechanismSteps > 0;
}

bool IndoorSceneRuntime::activateEvent(uint16_t eventId, const std::string &sourceKind, size_t sourceIndex)
{
    if (!m_eventRuntimeState)
    {
        return false;
    }

    if (eventId == 0)
    {
        m_eventRuntimeState->lastActivationResult = "no event on hovered target";
        return false;
    }

    std::cout << "Activating indoor event " << eventId
              << " from " << sourceKind
              << " index=" << sourceIndex << '\n';

    const bool executed = m_eventRuntime.executeEventById(
        m_localEventProgram,
        m_globalEventProgram,
        eventId,
        *m_eventRuntimeState,
        m_pParty,
        nullptr
    );

    if (!executed)
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}
}
