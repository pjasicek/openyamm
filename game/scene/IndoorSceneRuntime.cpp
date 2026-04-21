#include "game/scene/IndoorSceneRuntime.h"

#include "game/gameplay/GameplayActorService.h"

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
    const MapStatsEntry &map,
    const IndoorMapData &indoorMapData,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    Party &party,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    GameplayActorService *pGameplayActorService,
    const SpriteFrameTable *pActorSpriteFrameTable)
    : m_mapFileName(mapFileName)
    , m_pSessionParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_partyRuntime(
        IndoorMovementController(indoorMapData, &m_mapDeltaData, &m_eventRuntimeState),
        itemTable)
{
    m_partyRuntime.setParty(*m_pSessionParty);
    m_worldRuntime.initialize(
        map,
        monsterTable,
        objectTable,
        itemTable,
        chestTable,
        &m_partyRuntime.party(),
        &m_partyRuntime,
        &m_mapDeltaData,
        &m_eventRuntimeState,
        pGameplayActorService,
        pActorSpriteFrameTable
    );

    if (!indoorMapData.vertices.empty())
    {
        int minX = indoorMapData.vertices.front().x;
        int maxX = indoorMapData.vertices.front().x;
        int minY = indoorMapData.vertices.front().y;
        int maxY = indoorMapData.vertices.front().y;
        int minZ = indoorMapData.vertices.front().z;
        int maxZ = indoorMapData.vertices.front().z;

        for (const IndoorVertex &vertex : indoorMapData.vertices)
        {
            minX = std::min(minX, vertex.x);
            maxX = std::max(maxX, vertex.x);
            minY = std::min(minY, vertex.y);
            maxY = std::max(maxY, vertex.y);
            minZ = std::min(minZ, vertex.z);
            maxZ = std::max(maxZ, vertex.z);
        }

        m_partyRuntime.initializeEyePosition(
            static_cast<float>((minX + maxX) / 2),
            static_cast<float>(minY - 256),
            static_cast<float>((minZ + maxZ) / 2),
            false);
    }
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
    return m_partyRuntime.party();
}

const Party &IndoorSceneRuntime::party() const
{
    return m_partyRuntime.party();
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
    m_worldRuntime.advanceGameMinutes(minutes);
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

IndoorWorldRuntime &IndoorSceneRuntime::worldRuntime()
{
    return m_worldRuntime;
}

IndoorPartyRuntime &IndoorSceneRuntime::partyRuntime()
{
    return m_partyRuntime;
}

const IndoorPartyRuntime &IndoorSceneRuntime::partyRuntime() const
{
    return m_partyRuntime;
}

const IndoorWorldRuntime &IndoorSceneRuntime::worldRuntime() const
{
    return m_worldRuntime;
}

IndoorSceneRuntime::Snapshot IndoorSceneRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.mapDeltaData = m_mapDeltaData;
    snapshot.eventRuntimeState = m_eventRuntimeState;
    snapshot.worldRuntime = m_worldRuntime.snapshot();
    snapshot.partyRuntime = m_partyRuntime.snapshot();
    snapshot.mechanismAccumulatorMilliseconds = m_mechanismAccumulatorMilliseconds;
    return snapshot;
}

void IndoorSceneRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_mapDeltaData = snapshot.mapDeltaData;
    m_eventRuntimeState = snapshot.eventRuntimeState;
    m_worldRuntime.restoreSnapshot(snapshot.worldRuntime);
    m_partyRuntime.restoreSnapshot(snapshot.partyRuntime);
    m_partyRuntime.setParty(*m_pSessionParty);
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
        &m_partyRuntime.party(),
        &m_worldRuntime
    );

    if (!executed)
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    m_worldRuntime.applyEventRuntimeState();
    m_partyRuntime.party().applyEventRuntimeState(*m_eventRuntimeState);
    m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}
}
