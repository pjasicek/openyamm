#include "game/scene/IndoorSceneRuntime.h"

#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/maps/MapAssetLoader.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;
constexpr float SecondsPerMillisecond = 0.001f;
constexpr uint32_t DoorNoSoundAttribute = 0x4;
constexpr uint32_t WoodDoor01SoundId = 167;
constexpr uint32_t StoneDoor01SoundId = 177;
constexpr uint32_t StoneDoor03SoundId = 181;
constexpr uint32_t StoneDoor04SoundId = 183;

uint64_t mechanismAudioKey(uint32_t doorId)
{
    constexpr uint64_t MechanismAudioKeyPrefix = uint64_t{0x4d454348} << 32; // "MECH"
    return MechanismAudioKeyPrefix | uint64_t{doorId};
}

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

void appendTimersFromProgram(
    const std::optional<ScriptedEventProgram> &program,
    std::vector<IndoorSceneRuntime::TimerState> &timers)
{
    if (!program)
    {
        return;
    }

    for (const ScriptedEventProgram::TimerTrigger &trigger : program->timerTriggers())
    {
        IndoorSceneRuntime::TimerState timer = {};
        timer.eventId = trigger.eventId;
        timer.repeating = trigger.repeating;
        timer.targetHour = trigger.targetHour;
        timer.intervalGameMinutes = trigger.intervalGameMinutes;
        timer.remainingGameMinutes = trigger.remainingGameMinutes;
        timers.push_back(std::move(timer));
    }
}

bool hasPersistedDecorationState(const std::optional<MapDeltaData> &mapDeltaData)
{
    if (!mapDeltaData)
    {
        return false;
    }

    for (uint8_t value : mapDeltaData->eventVariables.decorVars)
    {
        if (value != 0)
        {
            return true;
        }
    }

    return false;
}

void seedIndoorInteractiveDecorationRuntimeStateIfNeeded(
    const IndoorMapData &indoorMapData,
    const DecorationBillboardSet *pDecorationBillboardSet,
    const std::optional<MapDeltaData> &mapDeltaData,
    std::optional<EventRuntimeState> &eventRuntimeState)
{
    if (pDecorationBillboardSet == nullptr || !eventRuntimeState || hasPersistedDecorationState(mapDeltaData))
    {
        return;
    }

    for (uint8_t value : eventRuntimeState->decorVars)
    {
        if (value != 0)
        {
            return;
        }
    }

    uint8_t decorVarIndex = 0;
    constexpr uint8_t MaxDecorationVarCount = 125;

    for (size_t entityIndex = 0; entityIndex < indoorMapData.entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = indoorMapData.entities[entityIndex];

        if (entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0)
        {
            continue;
        }

        const DecorationEntry *pDecoration =
            pDecorationBillboardSet->decorationTable.get(entity.decorationListId);

        if ((pDecoration == nullptr || pDecoration->spriteId == 0) && !entity.name.empty())
        {
            pDecoration = pDecorationBillboardSet->decorationTable.findByInternalName(entity.name);
        }

        if (pDecoration == nullptr)
        {
            continue;
        }

        const std::optional<InteractiveDecorationBindingSpec> bindingSpec =
            resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name);

        if (!bindingSpec || decorVarIndex >= MaxDecorationVarCount)
        {
            continue;
        }

        uint8_t initialState = bindingSpec->initialState;
        const uint32_t seed =
            makeInteractiveDecorationSeed(
                entityIndex,
                entity.decorationListId,
                entity.x,
                entity.y,
                entity.z);

        if (bindingSpec->useSeededInitialState)
        {
            initialState = static_cast<uint8_t>(seed % bindingSpec->eventCount);
        }
        else if (bindingSpec->family != InteractiveDecorationFamily::None)
        {
            initialState = initialInteractiveDecorationState(bindingSpec->family, seed);
        }

        if (initialState != 0)
        {
            eventRuntimeState->decorVars[decorVarIndex] = initialState;
        }

        ++decorVarIndex;
    }
}

bool enteredIndoorPressurePlateFace(
    const IndoorMoveState &previousState,
    const IndoorMoveState &currentState)
{
    if (!currentState.grounded || currentState.supportFaceIndex == static_cast<size_t>(-1))
    {
        return false;
    }

    return !previousState.grounded
        || previousState.supportFaceIndex != currentState.supportFaceIndex;
}

std::string uppercaseCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return result;
}

uint32_t resolveIndoorMechanismMovementSoundId(const MapStatsEntry &map)
{
    const std::string environmentName = uppercaseCopy(map.environmentName);

    if (environmentName == "MOUNTAIN")
    {
        return StoneDoor04SoundId;
    }

    if (environmentName == "CAVE")
    {
        return StoneDoor03SoundId;
    }

    if (environmentName == "STONEROOM")
    {
        return StoneDoor01SoundId;
    }

    return WoodDoor01SoundId;
}

bool mechanismReachedFinalState(const RuntimeMechanismState &mechanism)
{
    return mechanism.state == static_cast<uint16_t>(EvtMechanismState::Open)
        || mechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed);
}

EventRuntimeState::PendingSound buildMechanismSound(
    uint32_t soundId,
    const MapDeltaDoor &door)
{
    EventRuntimeState::PendingSound sound = {};
    sound.soundId = soundId;
    sound.positional = true;

    if (!door.xOffsets.empty())
    {
        sound.x = door.xOffsets.front();
    }

    if (!door.yOffsets.empty())
    {
        sound.y = door.yOffsets.front();
    }

    if (!door.zOffsets.empty())
    {
        sound.z = door.zOffsets.front();
        sound.hasExplicitZ = true;
    }

    return sound;
}

EventRuntimeState::PendingSound buildMechanismLoopSound(
    uint32_t soundId,
    const MapDeltaDoor &door)
{
    EventRuntimeState::PendingSound sound = buildMechanismSound(soundId, door);
    sound.kind = EventRuntimeState::PendingSound::Kind::PlayLoopingKeyed;
    sound.key = mechanismAudioKey(door.doorId);
    return sound;
}

EventRuntimeState::PendingSound buildStopMechanismSound(uint32_t doorId)
{
    EventRuntimeState::PendingSound sound = {};
    sound.kind = EventRuntimeState::PendingSound::Kind::StopKeyed;
    sound.key = mechanismAudioKey(doorId);
    return sound;
}
}

IndoorSceneRuntime::IndoorSceneRuntime(
    const std::string &mapFileName,
    const MapStatsEntry &map,
    const IndoorMapData &indoorMapData,
    const MonsterTable &monsterTable,
    const MonsterProjectileTable &monsterProjectileTable,
    const ObjectTable &objectTable,
    const SpellTable &spellTable,
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    Party &party,
    const std::optional<MapDeltaData> &indoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    GameplayActorService *pGameplayActorService,
    GameplayProjectileService *pGameplayProjectileService,
    GameplayCombatController *pGameplayCombatController,
    const SpriteFrameTable *pActorSpriteFrameTable,
    const SpriteFrameTable *pProjectileSpriteFrameTable,
    const DecorationBillboardSet *pIndoorDecorationBillboardSet)
    : m_map(map)
    , m_mapFileName(mapFileName)
    , m_pIndoorMapData(&indoorMapData)
    , m_pSessionParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_partyRuntime(
        IndoorMovementController(indoorMapData, &m_mapDeltaData, &m_eventRuntimeState),
        itemTable)
{
    if (m_mapDeltaData)
    {
        normalizeIndoorDoorTextureDeltas(*m_mapDeltaData, indoorMapData);
    }

    seedIndoorInteractiveDecorationRuntimeStateIfNeeded(
        indoorMapData,
        pIndoorDecorationBillboardSet,
        m_mapDeltaData,
        m_eventRuntimeState);

    m_partyRuntime.setParty(*m_pSessionParty);
    m_worldRuntime.initialize(
        map,
        monsterTable,
        monsterProjectileTable,
        objectTable,
        spellTable,
        itemTable,
        chestTable,
        &m_partyRuntime.party(),
        &m_partyRuntime,
        &m_mapDeltaData,
        &m_eventRuntimeState,
        pGameplayActorService,
        pGameplayProjectileService,
        pGameplayCombatController,
        pActorSpriteFrameTable,
        pProjectileSpriteFrameTable,
        &indoorMapData,
        pIndoorDecorationBillboardSet
    );
    m_worldRuntime.bindEventExecution(&m_eventRuntime, &m_localEventProgram, &m_globalEventProgram);

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
    const SpriteFrameTable *pActorSpriteFrameTable,
    const DecorationBillboardSet *pIndoorDecorationBillboardSet)
    : m_map(map)
    , m_mapFileName(mapFileName)
    , m_pIndoorMapData(&indoorMapData)
    , m_pSessionParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_partyRuntime(
        IndoorMovementController(indoorMapData, &m_mapDeltaData, &m_eventRuntimeState),
        itemTable)
{
    if (m_mapDeltaData)
    {
        normalizeIndoorDoorTextureDeltas(*m_mapDeltaData, indoorMapData);
    }

    seedIndoorInteractiveDecorationRuntimeStateIfNeeded(
        indoorMapData,
        pIndoorDecorationBillboardSet,
        m_mapDeltaData,
        m_eventRuntimeState);

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
        pActorSpriteFrameTable,
        &indoorMapData,
        pIndoorDecorationBillboardSet
    );
    m_worldRuntime.bindEventExecution(&m_eventRuntime, &m_localEventProgram, &m_globalEventProgram);

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
    if (snapshot.eventRuntimeState)
    {
        clearTransientEventRuntimeState(*snapshot.eventRuntimeState);
    }
    snapshot.worldRuntime = m_worldRuntime.snapshot();
    snapshot.partyRuntime = m_partyRuntime.snapshot();
    snapshot.timers = m_timers;
    snapshot.lastProcessedPartyMoveStateForFaceTriggers = m_lastProcessedPartyMoveStateForFaceTriggers;
    snapshot.mechanismAccumulatorMilliseconds = m_mechanismAccumulatorMilliseconds;
    return snapshot;
}

void IndoorSceneRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_mapDeltaData = snapshot.mapDeltaData;
    if (m_mapDeltaData && m_pIndoorMapData != nullptr)
    {
        normalizeIndoorDoorTextureDeltas(*m_mapDeltaData, *m_pIndoorMapData);
    }

    m_eventRuntimeState = snapshot.eventRuntimeState;
    if (m_eventRuntimeState)
    {
        clearTransientEventRuntimeState(*m_eventRuntimeState);
    }
    m_worldRuntime.restoreSnapshot(snapshot.worldRuntime);
    m_partyRuntime.restoreSnapshot(snapshot.partyRuntime);
    m_partyRuntime.setParty(*m_pSessionParty);
    m_timers = snapshot.timers;
    m_lastProcessedPartyMoveStateForFaceTriggers = snapshot.lastProcessedPartyMoveStateForFaceTriggers;
    m_mechanismAudioStates.clear();
    m_mechanismAccumulatorMilliseconds = snapshot.mechanismAccumulatorMilliseconds;
}

bool IndoorSceneRuntime::advanceSimulation(float deltaMilliseconds)
{
    if (!m_eventRuntimeState || !m_mapDeltaData || deltaMilliseconds <= 0.0f)
    {
        return false;
    }

    const float deltaGameMinutes = deltaMilliseconds * SecondsPerMillisecond * GameMinutesPerRealSecond;
    bool stateChanged = updateTimers(deltaGameMinutes);
    stateChanged = updatePartyFaceTriggers() || stateChanged;

    if (deltaGameMinutes > 0.0f)
    {
        m_worldRuntime.advanceGameMinutes(deltaGameMinutes);
    }

    if (!hasMovingMechanism(*m_eventRuntimeState))
    {
        m_mechanismAccumulatorMilliseconds = 0.0f;
        return stateChanged;
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
        const std::unordered_map<uint32_t, RuntimeMechanismState> previousMechanisms =
            m_eventRuntimeState->mechanisms;
        m_eventRuntime.advanceMechanisms(m_mapDeltaData, MechanismStepMilliseconds, *m_eventRuntimeState);
        updateMechanismAudio(previousMechanisms, MechanismStepMilliseconds);
        m_mechanismAccumulatorMilliseconds -= MechanismStepMilliseconds;
        ++mechanismSteps;
    }

    if (mechanismSteps > 0)
    {
        m_worldRuntime.refreshMechanismRuntimeGeometryCache();
    }

    if (
        mechanismSteps == MaximumMechanismStepsPerFrame
        && m_mechanismAccumulatorMilliseconds > MechanismStepMilliseconds
    )
    {
        m_mechanismAccumulatorMilliseconds = MechanismStepMilliseconds;
    }

    return stateChanged || mechanismSteps > 0;
}

void IndoorSceneRuntime::updateMechanismAudio(
    const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms,
    float)
{
    if (!m_eventRuntimeState || !m_mapDeltaData)
    {
        return;
    }

    const uint32_t movementSoundId = resolveIndoorMechanismMovementSoundId(m_map);
    const uint32_t finalSoundId = movementSoundId + 1;

    for (const MapDeltaDoor &door : m_mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator currentIterator =
            m_eventRuntimeState->mechanisms.find(door.doorId);

        if (currentIterator == m_eventRuntimeState->mechanisms.end())
        {
            if (m_mechanismAudioStates.erase(door.doorId) > 0)
            {
                m_eventRuntimeState->pendingSounds.push_back(buildStopMechanismSound(door.doorId));
            }

            continue;
        }

        const RuntimeMechanismState &currentMechanism = currentIterator->second;
        const bool canPlaySound = (door.attributes & DoorNoSoundAttribute) == 0 && door.numVertices != 0;

        if (!canPlaySound)
        {
            if (m_mechanismAudioStates.erase(door.doorId) > 0)
            {
                m_eventRuntimeState->pendingSounds.push_back(buildStopMechanismSound(door.doorId));
            }

            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator previousIterator =
            previousMechanisms.find(door.doorId);
        const bool wasMoving =
            previousIterator != previousMechanisms.end() && previousIterator->second.isMoving;

        if (currentMechanism.isMoving)
        {
            MechanismAudioState &audioState = m_mechanismAudioStates[door.doorId];

            if (!audioState.loopStarted)
            {
                m_eventRuntimeState->pendingSounds.push_back(buildMechanismLoopSound(movementSoundId, door));
                audioState.loopStarted = true;
            }

            continue;
        }

        const bool hadLoopState = m_mechanismAudioStates.erase(door.doorId) > 0;

        if (wasMoving && mechanismReachedFinalState(currentMechanism))
        {
            if (hadLoopState)
            {
                m_eventRuntimeState->pendingSounds.push_back(buildStopMechanismSound(door.doorId));
            }

            m_eventRuntimeState->pendingSounds.push_back(buildMechanismSound(finalSoundId, door));
        }
    }
}

bool IndoorSceneRuntime::updatePartyFaceTriggers()
{
    const IndoorMoveState currentMoveState = m_partyRuntime.movementState();

    if (!m_lastProcessedPartyMoveStateForFaceTriggers)
    {
        m_lastProcessedPartyMoveStateForFaceTriggers = currentMoveState;
        return false;
    }

    const IndoorMoveState previousMoveState = *m_lastProcessedPartyMoveStateForFaceTriggers;
    m_lastProcessedPartyMoveStateForFaceTriggers = currentMoveState;

    if (!enteredIndoorPressurePlateFace(previousMoveState, currentMoveState))
    {
        return false;
    }

    return m_worldRuntime.executeFaceTriggeredEvent(
        currentMoveState.supportFaceIndex,
        FaceAttribute::PressurePlate,
        false);
}

bool IndoorSceneRuntime::updateTimers(float deltaGameMinutes)
{
    if (!m_eventRuntimeState || deltaGameMinutes <= 0.0f)
    {
        return false;
    }

    if (m_timers.empty())
    {
        appendTimersFromProgram(m_localEventProgram, m_timers);
        appendTimersFromProgram(m_globalEventProgram, m_timers);
    }

    if (m_timers.empty())
    {
        return false;
    }

    bool executedAny = false;

    for (TimerState &timer : m_timers)
    {
        if (timer.hasFired && !timer.repeating)
        {
            continue;
        }

        timer.remainingGameMinutes -= deltaGameMinutes;

        if (timer.remainingGameMinutes > 0.0f)
        {
            continue;
        }

        if (m_eventRuntime.executeEventById(
                m_localEventProgram,
                m_globalEventProgram,
                timer.eventId,
                *m_eventRuntimeState,
                &m_partyRuntime.party(),
                &m_worldRuntime))
        {
            executedAny = true;
            m_worldRuntime.applyEventRuntimeState();
            m_partyRuntime.party().applyEventRuntimeState(*m_eventRuntimeState, false);
        }

        if (timer.repeating)
        {
            timer.remainingGameMinutes += std::max(0.5f, timer.intervalGameMinutes);
        }
        else
        {
            timer.hasFired = true;
        }
    }

    return executedAny;
}

bool IndoorSceneRuntime::activateEvent(
    uint16_t eventId,
    const std::string &sourceKind,
    size_t sourceIndex,
    const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext)
{
    static_cast<void>(sourceKind);
    static_cast<void>(sourceIndex);

    if (!m_eventRuntimeState)
    {
        return false;
    }

    if (eventId == 0)
    {
        m_eventRuntimeState->lastActivationResult = "no event on hovered target";
        return false;
    }

    m_eventRuntimeState->activeDecorationContext = activeDecorationContext;

    const bool executed = m_eventRuntime.executeEventById(
        m_localEventProgram,
        m_globalEventProgram,
        eventId,
        *m_eventRuntimeState,
        &m_partyRuntime.party(),
        &m_worldRuntime
    );
    m_eventRuntimeState->activeDecorationContext.reset();

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
