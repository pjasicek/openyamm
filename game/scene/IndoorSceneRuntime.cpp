#include "game/scene/IndoorSceneRuntime.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/gameplay/TravelRuntime.h"
#include "game/maps/MapAssetLoader.h"

#include <algorithm>
#include <cctype>
#include <cmath>

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

void initializeIndoorPartyStart(IndoorPartyRuntime &partyRuntime, const IndoorMapData &indoorMapData);

bool hasIndoorPressurePlateSupportFace(const IndoorMoveState &state)
{
    return state.grounded && state.supportFaceIndex != static_cast<size_t>(-1);
}

uint32_t effectiveIndoorSceneFaceAttributes(
    const IndoorFace &face,
    const std::optional<MapDeltaData> &mapDeltaData,
    size_t faceIndex)
{
    if (mapDeltaData && faceIndex < mapDeltaData->faceAttributes.size())
    {
        return mapDeltaData->faceAttributes[faceIndex];
    }

    return face.attributes;
}

std::optional<uint16_t> indoorPressurePlateEventId(
    const IndoorMapData &indoorMapData,
    const std::optional<MapDeltaData> &mapDeltaData,
    size_t faceIndex)
{
    if (faceIndex >= indoorMapData.faces.size())
    {
        return std::nullopt;
    }

    const IndoorFace &face = indoorMapData.faces[faceIndex];
    const uint32_t attributes = effectiveIndoorSceneFaceAttributes(face, mapDeltaData, faceIndex);

    if (face.cogTriggered == 0 || !hasFaceAttribute(attributes, FaceAttribute::PressurePlate))
    {
        return std::nullopt;
    }

    return face.cogTriggered;
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

bool mechanismDoorContainsFace(const MapDeltaDoor &door, size_t faceIndex)
{
    for (uint16_t doorFaceId : door.faceIds)
    {
        if (static_cast<size_t>(doorFaceId) == faceIndex)
        {
            return true;
        }
    }

    return false;
}

float mechanismDistanceFromBaseDoorState(const MapDeltaDoor &door)
{
    RuntimeMechanismState mechanism = {};
    mechanism.state = door.state;
    mechanism.timeSinceTriggeredMs = static_cast<float>(door.timeSinceTriggered);
    mechanism.currentDistance = EventRuntime::calculateMechanismDistance(door, mechanism);
    return mechanism.currentDistance;
}

void applyMovingMechanismSupportMovement(
    const MapDeltaData &mapDeltaData,
    const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms,
    EventRuntimeState &eventRuntimeState,
    IndoorPartyRuntime &partyRuntime)
{
    const IndoorMoveState &moveState = partyRuntime.movementState();

    if (!moveState.grounded || moveState.supportFaceIndex == static_cast<size_t>(-1))
    {
        return;
    }

    for (const MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (!indoorDoorCarriesPartySupport(door))
        {
            continue;
        }

        if (!mechanismDoorContainsFace(door, moveState.supportFaceIndex))
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator currentIterator =
            eventRuntimeState.mechanisms.find(door.doorId);

        if (currentIterator == eventRuntimeState.mechanisms.end())
        {
            continue;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator previousIterator =
            previousMechanisms.find(door.doorId);
        const float previousDistance =
            previousIterator != previousMechanisms.end()
                ? previousIterator->second.currentDistance
                : mechanismDistanceFromBaseDoorState(door);
        const float distanceDelta = currentIterator->second.currentDistance - previousDistance;

        if (std::abs(distanceDelta) <= 0.0001f)
        {
            continue;
        }

        partyRuntime.translatePartyPosition(
            fixedIndoorDoorDirectionComponentToFloat(door.directionX) * distanceDelta,
            fixedIndoorDoorDirectionComponentToFloat(door.directionY) * distanceDelta,
            fixedIndoorDoorDirectionComponentToFloat(door.directionZ) * distanceDelta);
    }
}

void initializeIndoorPartyStart(IndoorPartyRuntime &partyRuntime, const IndoorMapData &indoorMapData)
{
    if (indoorMapData.partyStartPoint.has_value())
    {
        const IndoorPartyStartPoint &startPoint = *indoorMapData.partyStartPoint;
        partyRuntime.initializePartyPosition(
            static_cast<float>(startPoint.x),
            static_cast<float>(startPoint.y),
            static_cast<float>(startPoint.z),
            false);
        return;
    }

    if (indoorMapData.vertices.empty())
    {
        return;
    }

    int minX = indoorMapData.vertices.front().x;
    int maxX = indoorMapData.vertices.front().x;
    int minY = indoorMapData.vertices.front().y;
    int minZ = indoorMapData.vertices.front().z;
    int maxZ = indoorMapData.vertices.front().z;

    for (const IndoorVertex &vertex : indoorMapData.vertices)
    {
        minX = std::min(minX, vertex.x);
        maxX = std::max(maxX, vertex.x);
        minY = std::min(minY, vertex.y);
        minZ = std::min(minZ, vertex.z);
        maxZ = std::max(maxZ, vertex.z);
    }

    partyRuntime.initializeEyePosition(
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
    const DecorationBillboardSet *pIndoorDecorationBillboardSet,
    const MergedBolsterMapTable *pMergedBolsterMapTable,
    const MergedBolsterMonsterTable *pMergedBolsterMonsterTable,
    bool bolsterMonstersEnabled,
    const NpcDialogTable *pNpcDialogTable,
    const MapItemSourceData *pItemSourceData,
    const Mm9MapTransitionTable *pMm9MapTransitionTable,
    const Mm9TeacherScheduleTable *pMm9TeacherScheduleTable)
    : m_map(map)
    , m_mapFileName(mapFileName)
    , m_pIndoorMapData(&indoorMapData)
    , m_pIndoorDecorationTable(pIndoorDecorationBillboardSet != nullptr ? &pIndoorDecorationBillboardSet->decorationTable : nullptr)
    , m_pSessionParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_eventRuntime(nullptr, pNpcDialogTable)
    , m_partyRuntime(
        IndoorMovementController(indoorMapData, &m_mapDeltaData, &m_eventRuntimeState),
        itemTable)
{
    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->mapFileName = mapFileName;
        setActiveHistoryContinent(*m_eventRuntimeState, map.mergedContinentId);
    }

    if (m_mapDeltaData)
    {
        normalizeIndoorDoorTextureDeltas(*m_mapDeltaData, indoorMapData);
    }

    m_partyRuntime.setParty(*m_pSessionParty);
    m_worldRuntime.setBolsterMonstersEnabled(bolsterMonstersEnabled);
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
        pIndoorDecorationBillboardSet,
        pMergedBolsterMapTable,
        pMergedBolsterMonsterTable,
        pItemSourceData
    );
    m_worldRuntime.bindEventExecution(&m_eventRuntime, &m_localEventProgram, &m_globalEventProgram);

    initializeIndoorPartyStart(m_partyRuntime, indoorMapData);
    if (pMm9MapTransitionTable != nullptr)
    {
        m_mm9PositionedTransitionRuntime.configure(
            pMm9MapTransitionTable->forSourceMapFile(mapFileName));
    }
    if (pMm9TeacherScheduleTable != nullptr)
    {
        m_mm9TeacherScheduleRuntime.configure(
            pMm9TeacherScheduleTable->forSourceMapFile(mapFileName));
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
    const DecorationBillboardSet *pIndoorDecorationBillboardSet,
    const MergedBolsterMapTable *pMergedBolsterMapTable,
    const MergedBolsterMonsterTable *pMergedBolsterMonsterTable,
    bool bolsterMonstersEnabled,
    const NpcDialogTable *pNpcDialogTable,
    const MapItemSourceData *pItemSourceData,
    const Mm9MapTransitionTable *pMm9MapTransitionTable,
    const Mm9TeacherScheduleTable *pMm9TeacherScheduleTable)
    : m_map(map)
    , m_mapFileName(mapFileName)
    , m_pIndoorMapData(&indoorMapData)
    , m_pIndoorDecorationTable(pIndoorDecorationBillboardSet != nullptr ? &pIndoorDecorationBillboardSet->decorationTable : nullptr)
    , m_pSessionParty(&party)
    , m_mapDeltaData(indoorMapDeltaData)
    , m_eventRuntimeState(eventRuntimeState)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_eventRuntime(nullptr, pNpcDialogTable)
    , m_partyRuntime(
        IndoorMovementController(indoorMapData, &m_mapDeltaData, &m_eventRuntimeState),
        itemTable)
{
    if (m_eventRuntimeState)
    {
        m_eventRuntimeState->mapFileName = mapFileName;
        setActiveHistoryContinent(*m_eventRuntimeState, map.mergedContinentId);
    }

    if (m_mapDeltaData)
    {
        normalizeIndoorDoorTextureDeltas(*m_mapDeltaData, indoorMapData);
    }

    m_partyRuntime.setParty(*m_pSessionParty);
    m_worldRuntime.setBolsterMonstersEnabled(bolsterMonstersEnabled);
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
        pIndoorDecorationBillboardSet,
        pMergedBolsterMapTable,
        pMergedBolsterMonsterTable,
        pItemSourceData
    );
    m_worldRuntime.bindEventExecution(&m_eventRuntime, &m_localEventProgram, &m_globalEventProgram);

    initializeIndoorPartyStart(m_partyRuntime, indoorMapData);
    if (pMm9MapTransitionTable != nullptr)
    {
        m_mm9PositionedTransitionRuntime.configure(
            pMm9MapTransitionTable->forSourceMapFile(mapFileName));
    }
    if (pMm9TeacherScheduleTable != nullptr)
    {
        m_mm9TeacherScheduleRuntime.configure(
            pMm9TeacherScheduleTable->forSourceMapFile(mapFileName));
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

ISceneEventContext *IndoorSceneRuntime::sceneEventContext()
{
    return &m_worldRuntime;
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
    if (minutes <= 0.0f)
    {
        return;
    }

    m_worldRuntime.advanceGameMinutes(minutes);
}

void IndoorSceneRuntime::advanceTurnBasedGameMinutes(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    m_worldRuntime.advanceGameMinutes(minutes);
    updateTimers(minutes);
    applyMm9TeacherScheduleActivations(
        m_mm9TeacherScheduleRuntime.update(m_worldRuntime.gameMinutes()),
        m_worldRuntime,
        m_worldRuntime);
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
    snapshot.lastPartyFloorFaceForPressurePlateTriggers = m_lastPartyFloorFaceForPressurePlateTriggers;
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
        m_eventRuntimeState->mapFileName = m_mapFileName;
        setActiveHistoryContinent(*m_eventRuntimeState, m_map.mergedContinentId);
        clearTransientEventRuntimeState(*m_eventRuntimeState);
    }
    m_worldRuntime.restoreSnapshot(snapshot.worldRuntime);
    m_partyRuntime.restoreSnapshot(snapshot.partyRuntime);
    m_partyRuntime.setParty(*m_pSessionParty);
    if (m_eventRuntimeState)
    {
        m_partyRuntime.party().applyGlobalNpcStateTo(*m_eventRuntimeState);
    }
    m_timers = snapshot.timers;
    m_timerDefinitionsInitialized = false;
    m_resetLegacyTimersOnInitialize = false;
    m_lastProcessedPartyMoveStateForFaceTriggers = snapshot.lastProcessedPartyMoveStateForFaceTriggers;
    m_lastPartyFloorFaceForPressurePlateTriggers = snapshot.lastPartyFloorFaceForPressurePlateTriggers;
    if (!m_lastPartyFloorFaceForPressurePlateTriggers
        && m_lastProcessedPartyMoveStateForFaceTriggers
        && hasIndoorPressurePlateSupportFace(*m_lastProcessedPartyMoveStateForFaceTriggers))
    {
        m_lastPartyFloorFaceForPressurePlateTriggers =
            m_lastProcessedPartyMoveStateForFaceTriggers->supportFaceIndex;
    }
    m_mechanismAudioStates.clear();
    m_mechanismAccumulatorMilliseconds = snapshot.mechanismAccumulatorMilliseconds;
    m_mm9PositionedTransitionRuntime.resetOverlapState();
    m_mm9TeacherScheduleRuntime.reset();
}

void IndoorSceneRuntime::stampLastVisitTime()
{
    if (m_mapDeltaData)
    {
        m_mapDeltaData->locationTime.lastVisitTime =
            legacyTimerTicksFromGameMinutes(static_cast<double>(m_worldRuntime.gameMinutes()));
    }
}

void IndoorSceneRuntime::applyMapReentryReset()
{
    m_worldRuntime.applyMapReentryReset();
    m_timerDefinitionsInitialized = false;
    m_resetLegacyTimersOnInitialize = true;
}

void IndoorSceneRuntime::prepareTimers()
{
    initializeTimers(static_cast<double>(m_worldRuntime.gameMinutes()));
}

bool IndoorSceneRuntime::advanceSimulation(float deltaMilliseconds)
{
    if (!m_eventRuntimeState || !m_mapDeltaData || deltaMilliseconds <= 0.0f)
    {
        return false;
    }

    const float deltaGameMinutes = deltaMilliseconds * SecondsPerMillisecond * GameMinutesPerRealSecond;

    if (deltaGameMinutes > 0.0f)
    {
        m_worldRuntime.advanceGameMinutes(deltaGameMinutes);
    }

    bool stateChanged = updateTimers(deltaGameMinutes);
    stateChanged = applyMm9TeacherScheduleActivations(
        m_mm9TeacherScheduleRuntime.update(m_worldRuntime.gameMinutes()),
        m_worldRuntime,
        m_worldRuntime) || stateChanged;
    stateChanged = updatePartyFaceTriggers() || stateChanged;
    const IndoorMoveState &moveState = m_partyRuntime.movementState();
    const std::optional<Mm9PositionedTransitionActivation> activation =
        m_mm9PositionedTransitionRuntime.update(
            moveState.x,
            moveState.y,
            moveState.footZ,
            *m_eventRuntimeState);
    if (activation)
    {
        stateChanged = true;
        if (!activation->pTransition->askPlayer)
        {
            applyTravelDaysSideEffects(
                m_partyRuntime.party(),
                &m_worldRuntime,
                activation->pTransition->travelDays,
                std::max(0, activation->pTransition->travelDays));
        }
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
    std::optional<std::unordered_map<uint32_t, RuntimeMechanismState>> previousMechanismsForGeometry;

    while (
        m_mechanismAccumulatorMilliseconds >= MechanismStepMilliseconds
        && mechanismSteps < MaximumMechanismStepsPerFrame
    )
    {
        if (!previousMechanismsForGeometry.has_value())
        {
            previousMechanismsForGeometry = m_eventRuntimeState->mechanisms;
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState> previousMechanisms =
            m_eventRuntimeState->mechanisms;
        m_eventRuntime.advanceMechanisms(m_mapDeltaData, MechanismStepMilliseconds, *m_eventRuntimeState);
        applyMovingMechanismSupportMovement(
            *m_mapDeltaData,
            previousMechanisms,
            *m_eventRuntimeState,
            m_partyRuntime);
        updateMechanismAudio(previousMechanisms, MechanismStepMilliseconds);
        m_mechanismAccumulatorMilliseconds -= MechanismStepMilliseconds;
        ++mechanismSteps;
    }

    if (mechanismSteps > 0)
    {
        const std::vector<uint32_t> changedDoorIds =
            m_worldRuntime.refreshMechanismRuntimeGeometryCache(*previousMechanismsForGeometry);
        m_partyRuntime.applyMechanismGeometryUpdate(changedDoorIds);
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

    m_lastProcessedPartyMoveStateForFaceTriggers = currentMoveState;

    if (!hasIndoorPressurePlateSupportFace(currentMoveState))
    {
        return false;
    }

    // Match OE floor-face semantics: short airborne/jitter frames do not re-enter the same pressure plate.
    if (!m_lastPartyFloorFaceForPressurePlateTriggers)
    {
        m_lastPartyFloorFaceForPressurePlateTriggers = currentMoveState.supportFaceIndex;
        return false;
    }

    const size_t previousFloorFaceIndex = *m_lastPartyFloorFaceForPressurePlateTriggers;
    m_lastPartyFloorFaceForPressurePlateTriggers = currentMoveState.supportFaceIndex;

    if (previousFloorFaceIndex == currentMoveState.supportFaceIndex)
    {
        return false;
    }

    if (m_pIndoorMapData == nullptr)
    {
        return false;
    }

    const std::optional<uint16_t> previousPressureEvent =
        indoorPressurePlateEventId(*m_pIndoorMapData, m_mapDeltaData, previousFloorFaceIndex);
    const std::optional<uint16_t> currentPressureEvent =
        indoorPressurePlateEventId(*m_pIndoorMapData, m_mapDeltaData, currentMoveState.supportFaceIndex);

    if (previousPressureEvent && currentPressureEvent && *previousPressureEvent == *currentPressureEvent)
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

    if (!m_timerDefinitionsInitialized)
    {
        initializeTimers(static_cast<double>(m_worldRuntime.gameMinutes()) - deltaGameMinutes);
    }

    if (m_timers.empty())
    {
        return false;
    }

    return updateScriptedEventTimers(
        m_timers,
        static_cast<double>(m_worldRuntime.gameMinutes()),
        [this](const ScriptedEventTimerDefinition &definition)
        {
            GAMEPLAY_DEBUG_TRACE(
                "timer_event_fired world=indoor event_id=" + std::to_string(definition.eventId)
                + " source_event_id=" + std::to_string(definition.sourceEventId)
                + " trigger_step=" + std::to_string(definition.triggerStep));

            const bool executed = m_eventRuntime.executeEventById(
                m_localEventProgram,
                m_globalEventProgram,
                definition.eventId,
                *m_eventRuntimeState,
                &m_partyRuntime.party(),
                &m_worldRuntime,
                std::nullopt,
                true,
                definition.scope,
                true);

            if (executed)
            {
                m_worldRuntime.applyEventRuntimeState();
                m_partyRuntime.party().applyEventRuntimeState(*m_eventRuntimeState, false);
            }

            return executed;
        });
}

void IndoorSceneRuntime::initializeTimers(double registrationGameMinutes)
{
    const std::vector<ScriptedEventTimerDefinition> definitions =
        scriptedEventTimerDefinitionsFromPrograms(m_localEventProgram, m_globalEventProgram);
    const int64_t lastVisitTime = m_mapDeltaData
        ? m_mapDeltaData->locationTime.lastVisitTime
        : 0;
    m_timers = reconcileScriptedEventTimers(
        m_timers,
        definitions,
        registrationGameMinutes,
        lastVisitTime,
        m_resetLegacyTimersOnInitialize);
    m_timerDefinitionsInitialized = true;
    m_resetLegacyTimersOnInitialize = false;
}

bool IndoorSceneRuntime::activateEvent(
    uint16_t eventId,
    const std::string &sourceKind,
    size_t sourceIndex,
    const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext)
{
    if (!m_eventRuntimeState)
    {
        return false;
    }

    if (eventId == 0)
    {
        if (sourceKind == "entity" && m_pIndoorMapData != nullptr && m_pIndoorDecorationTable != nullptr
            && toggleIndoorDecorationLight(*m_pIndoorMapData, *m_pIndoorDecorationTable, sourceIndex, *m_eventRuntimeState))
        {
            return true;
        }
        m_eventRuntimeState->lastActivationResult = "no event on hovered target";
        return false;
    }

    if (m_worldRuntime.useMm9BarrelEvent(eventId))
    {
        m_eventRuntimeState->lastActivationResult = "MM9 barrel event " + std::to_string(eventId) + " executed";
        return true;
    }

    m_eventRuntimeState->activeDecorationContext = activeDecorationContext;

    const bool allowGlobalFallback = activeDecorationContext.has_value();
    const std::optional<ScriptedEventProgram> emptyLocalProgram;
    const std::optional<ScriptedEventProgram> &effectiveLocalEventProgram =
        allowGlobalFallback ? emptyLocalProgram : m_localEventProgram;

    const bool executed = m_eventRuntime.executeEventById(
        effectiveLocalEventProgram,
        m_globalEventProgram,
        eventId,
        *m_eventRuntimeState,
        &m_partyRuntime.party(),
        &m_worldRuntime,
        std::nullopt,
        allowGlobalFallback
    );
    m_eventRuntimeState->activeDecorationContext.reset();

    if (!executed)
    {
        m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " unresolved";
        return false;
    }

    m_worldRuntime.applyEventRuntimeState();
    m_partyRuntime.party().applyEventRuntimeState(*m_eventRuntimeState, false);
    m_eventRuntimeState->lastActivationResult = "event " + std::to_string(eventId) + " executed";
    return true;
}
}
