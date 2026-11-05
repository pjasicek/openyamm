#include "game/scene/IndoorSceneRuntime.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/events/MechanismAudio.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovers.h"
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
        m_eventRuntimeState->mapWorldId = map.worldId;
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
        m_eventRuntimeState->mapWorldId = map.worldId;
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
        m_eventRuntimeState->mapWorldId = m_map.worldId;
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
        if (!activation->pTransition->askPlayer
            && applyTravelDaysSideEffects(
                m_partyRuntime.party(),
                &m_worldRuntime,
                activation->pTransition->travelDays,
                std::max(0, activation->pTransition->travelDays))
            && m_eventRuntimeState->pendingMapMove)
        {
            m_eventRuntimeState->pendingMapMove->travelTimeApplied = true;
        }
    }

    return advanceMechanisms(deltaMilliseconds) || stateChanged;
}

bool IndoorSceneRuntime::advanceMechanisms(float deltaMilliseconds)
{
    if (!m_eventRuntimeState || !m_mapDeltaData || deltaMilliseconds <= 0.0f)
    {
        return false;
    }

    if (!hasMovingMechanism(*m_eventRuntimeState) && !hasPendingMoverWork())
    {
        m_mechanismAccumulatorMilliseconds = 0.0f;
        return false;
    }

    const bool hasMovers = m_pIndoorMapData != nullptr && !m_pIndoorMapData->moverDefinitions.empty();

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

        if (hasMovers)
        {
            chooseMoverOpenAwayDirections();
        }

        const std::unordered_map<uint32_t, RuntimeMechanismState> previousMechanisms =
            m_eventRuntimeState->mechanisms;
        m_eventRuntime.advanceMechanisms(m_mapDeltaData, MechanismStepMilliseconds, *m_eventRuntimeState);

        if (hasMovers)
        {
            advanceMoverAutoClose(MechanismStepMilliseconds);
            applyMoverBodyRules(previousMechanisms);
            carryPartyOnRotatingMovers(previousMechanisms);
        }

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

    return mechanismSteps > 0;
}

namespace
{
const MapDeltaDoor *findSceneDoor(const MapDeltaData &mapDeltaData, uint32_t doorId)
{
    for (const MapDeltaDoor &door : mapDeltaData.doors)
    {
        if (door.doorId == doorId)
        {
            return &door;
        }
    }

    return nullptr;
}

IndoorMoverBody partyMoverBody(const IndoorPartyRuntime &partyRuntime)
{
    const IndoorMoveState &state = partyRuntime.movementState();
    const IndoorBodyDimensions dimensions = {};
    return IndoorMoverBody{state.x, state.y, state.footZ, dimensions.radius, dimensions.height};
}

// The door's face polygons in a pose (`vertices` holds the pose for the door's own vertices).
void moverFacePolygons(
    const IndoorMapData &indoorMapData,
    const MapDeltaDoor &door,
    const std::vector<IndoorVertex> &vertices,
    std::vector<std::vector<bx::Vec3>> &polygons)
{
    polygons.clear();

    for (uint16_t faceId : door.faceIds)
    {
        if (faceId >= indoorMapData.faces.size())
        {
            continue;
        }

        std::vector<bx::Vec3> polygon;

        for (uint16_t vertexId : indoorMapData.faces[faceId].vertexIndices)
        {
            if (vertexId < vertices.size())
            {
                polygon.push_back(indoorVertexToWorld(vertices[vertexId]));
            }
        }

        if (polygon.size() >= 3)
        {
            polygons.push_back(std::move(polygon));
        }
    }
}

bx::Vec3 polygonCentre(const std::vector<bx::Vec3> &polygon)
{
    bx::Vec3 centre = {0.0f, 0.0f, 0.0f};

    for (const bx::Vec3 &point : polygon)
    {
        centre = {centre.x + point.x, centre.y + point.y, centre.z + point.z};
    }

    const float count = static_cast<float>(polygon.size());
    return {centre.x / count, centre.y / count, centre.z / count};
}
}

bool IndoorSceneRuntime::hasPendingMoverWork() const
{
    if (m_pIndoorMapData == nullptr || m_pIndoorMapData->moverDefinitions.empty() || !m_eventRuntimeState)
    {
        return false;
    }

    for (const IndoorMoverDefinition &mover : m_pIndoorMapData->moverDefinitions)
    {
        if (mover.autoCloseSeconds <= 0.0f)
        {
            continue;
        }

        const auto iterator = m_eventRuntimeState->mechanisms.find(mover.doorId);

        if (iterator != m_eventRuntimeState->mechanisms.end()
            && iterator->second.state == static_cast<uint16_t>(EvtMechanismState::Open))
        {
            return true;
        }
    }

    return false;
}

void IndoorSceneRuntime::chooseMoverOpenAwayDirections()
{
    const IndoorMoveState &partyState = m_partyRuntime.movementState();
    const bx::Vec3 party = {partyState.x, partyState.y, partyState.footZ + 80.0f};

    for (const IndoorMoverDefinition &mover : m_pIndoorMapData->moverDefinitions)
    {
        if (!mover.rotation || !mover.rotation->openAway)
        {
            continue;
        }

        const auto iterator = m_eventRuntimeState->mechanisms.find(mover.doorId);
        const MapDeltaDoor *pDoor = findSceneDoor(*m_mapDeltaData, mover.doorId);

        // A door starting to open from shut takes the side away from the party; it keeps it until shut again.
        if (iterator == m_eventRuntimeState->mechanisms.end()
            || pDoor == nullptr
            || iterator->second.state != static_cast<uint16_t>(EvtMechanismState::Opening)
            || iterator->second.currentDistance < static_cast<float>(pDoor->moveLength) - 0.5f)
        {
            continue;
        }

        iterator->second.rotationDirection = indoorMoverOpenAwayDirection(*pDoor, mover, party);
    }
}

void IndoorSceneRuntime::advanceMoverAutoClose(float stepMilliseconds)
{
    for (const IndoorMoverDefinition &mover : m_pIndoorMapData->moverDefinitions)
    {
        if (mover.autoCloseSeconds <= 0.0f)
        {
            continue;
        }

        const auto iterator = m_eventRuntimeState->mechanisms.find(mover.doorId);

        if (iterator == m_eventRuntimeState->mechanisms.end()
            || iterator->second.state != static_cast<uint16_t>(EvtMechanismState::Open)
            || iterator->second.isMoving)
        {
            continue;
        }

        // The open door's time is its existing (saved) time since it was triggered.
        RuntimeMechanismState &mechanism = iterator->second;
        mechanism.timeSinceTriggeredMs += stepMilliseconds;

        if (mechanism.timeSinceTriggeredMs >= mover.autoCloseSeconds * 1000.0f)
        {
            EventRuntime::applyMechanismAction(
                mechanism, findSceneDoor(*m_mapDeltaData, mover.doorId), MechanismAction::Close);
        }
    }
}

void IndoorSceneRuntime::applyMoverBodyRules(
    const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms)
{
    std::vector<std::vector<bx::Vec3>> polygons;
    std::vector<std::vector<bx::Vec3>> previousPolygons;
    std::vector<std::pair<size_t, IndoorMoverBody>> actorBodies;

    for (const IndoorMoverDefinition &mover : m_pIndoorMapData->moverDefinitions)
    {
        if (mover.bodies == IndoorMoverBodyRule::Ignore)
        {
            continue;
        }

        const auto currentIterator = m_eventRuntimeState->mechanisms.find(mover.doorId);
        const auto previousIterator = previousMechanisms.find(mover.doorId);
        const MapDeltaDoor *pDoor = findSceneDoor(*m_mapDeltaData, mover.doorId);

        if (currentIterator == m_eventRuntimeState->mechanisms.end()
            || previousIterator == previousMechanisms.end()
            || pDoor == nullptr
            || std::abs(currentIterator->second.currentDistance - previousIterator->second.currentDistance) <= 0.0001f)
        {
            continue;
        }

        if (m_moverPoseVertices.size() != m_pIndoorMapData->vertices.size())
        {
            m_moverPoseVertices = m_pIndoorMapData->vertices;
        }

        const MapDeltaDoor &door = *pDoor;
        RuntimeMechanismState &mechanism = currentIterator->second;
        const RuntimeMechanismState &previous = previousIterator->second;
        applyIndoorMechanismDoorToVertices(
            door, &mover, previous.currentDistance, previous.rotationDirection, m_moverPoseVertices);
        moverFacePolygons(*m_pIndoorMapData, door, m_moverPoseVertices, previousPolygons);
        applyIndoorMechanismDoorToVertices(
            door, &mover, mechanism.currentDistance, mechanism.rotationDirection, m_moverPoseVertices);
        moverFacePolygons(*m_pIndoorMapData, door, m_moverPoseVertices, polygons);

        bx::Vec3 minimum = {1.0e9f, 1.0e9f, 1.0e9f};
        bx::Vec3 maximum = {-1.0e9f, -1.0e9f, -1.0e9f};

        for (const std::vector<bx::Vec3> &polygon : polygons)
        {
            for (const bx::Vec3 &point : polygon)
            {
                minimum = {std::min(minimum.x, point.x), std::min(minimum.y, point.y), std::min(minimum.z, point.z)};
                maximum = {std::max(maximum.x, point.x), std::max(maximum.y, point.y), std::max(maximum.z, point.z)};
            }
        }

        m_worldRuntime.collectMoverActorBodies(minimum, maximum, actorBodies);
        const IndoorMoverBody party = partyMoverBody(m_partyRuntime);
        // A face counts only while it moves toward the body: one swinging away from a body leaning on it (or a floor
        // tipping away from under it) does not stop or push anything.
        const auto approaches = [&polygons, &previousPolygons](const IndoorMoverBody &body, size_t index)
        {
            const float distance = indoorBodyAxisPolygonDistance(body, polygons[index]);
            return distance < body.radius
                && distance < indoorBodyAxisPolygonDistance(body, previousPolygons[index]) - 0.001f;
        };
        const auto touches = [&polygons, &approaches](const IndoorMoverBody &body)
        {
            for (size_t index = 0; index < polygons.size(); ++index)
            {
                if (approaches(body, index))
                {
                    return true;
                }
            }

            return false;
        };

        if (mover.bodies == IndoorMoverBodyRule::Push)
        {
            // Each face moving into a body moves the body clear of it, on the side the body was.
            const auto clearance = [&](const IndoorMoverBody &body) -> bx::Vec3
            {
                bx::Vec3 total = {0.0f, 0.0f, 0.0f};
                IndoorMoverBody moved = body;

                for (size_t index = 0; index < polygons.size(); ++index)
                {
                    if (!approaches(moved, index))
                    {
                        continue;
                    }

                    const bx::Vec3 centre = {moved.x, moved.y, moved.footZ + moved.height * 0.5f};
                    const bx::Vec3 before = polygonCentre(previousPolygons[index]);
                    const bx::Vec3 step = indoorBodyPolygonClearance(
                        moved, polygons[index], {centre.x - before.x, centre.y - before.y, centre.z - before.z});
                    moved.x += step.x;
                    moved.y += step.y;
                    moved.footZ += step.z;
                    total = {total.x + step.x, total.y + step.y, total.z + step.z};
                }

                return total;
            };
            const bx::Vec3 partyPush = clearance(party);

            if (partyPush.x != 0.0f || partyPush.y != 0.0f || partyPush.z != 0.0f)
            {
                m_partyRuntime.pushPartyPosition(partyPush.x, partyPush.y, partyPush.z);
            }

            for (const std::pair<size_t, IndoorMoverBody> &actor : actorBodies)
            {
                const bx::Vec3 actorPush = clearance(actor.second);

                if (actorPush.x != 0.0f || actorPush.y != 0.0f || actorPush.z != 0.0f)
                {
                    m_worldRuntime.displaceActorByMover(actor.first, actorPush.x, actorPush.y, actorPush.z);
                }
            }

            continue;
        }

        bool blocked = touches(party);

        for (size_t index = 0; !blocked && index < actorBodies.size(); ++index)
        {
            blocked = touches(actorBodies[index].second);
        }

        if (!blocked)
        {
            continue;
        }

        // Hold the step; a closing door with the reverse rule opens again (MM9 ReopenOnContact).
        const bool wasClosing = previous.state == static_cast<uint16_t>(EvtMechanismState::Closing);
        mechanism = previous;

        if (wasClosing && mover.bodies == IndoorMoverBodyRule::Reverse)
        {
            EventRuntime::applyMechanismAction(mechanism, pDoor, MechanismAction::Open);
        }
    }
}

void IndoorSceneRuntime::carryPartyOnRotatingMovers(
    const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms)
{
    const IndoorMoveState &state = m_partyRuntime.movementState();

    if (!state.grounded || state.supportFaceIndex == static_cast<size_t>(-1))
    {
        return;
    }

    for (const IndoorMoverDefinition &mover : m_pIndoorMapData->moverDefinitions)
    {
        if (!mover.carry || !mover.rotation)
        {
            continue;
        }

        const MapDeltaDoor *pDoor = findSceneDoor(*m_mapDeltaData, mover.doorId);
        const auto currentIterator = m_eventRuntimeState->mechanisms.find(mover.doorId);
        const auto previousIterator = previousMechanisms.find(mover.doorId);

        if (pDoor == nullptr
            || !mechanismDoorContainsFace(*pDoor, state.supportFaceIndex)
            || currentIterator == m_eventRuntimeState->mechanisms.end()
            || previousIterator == previousMechanisms.end())
        {
            continue;
        }

        const std::optional<IndoorRigidMotion> before = indoorRotatingMoverMotion(
            *pDoor, &mover, previousIterator->second.currentDistance, previousIterator->second.rotationDirection);
        const std::optional<IndoorRigidMotion> after = indoorRotatingMoverMotion(
            *pDoor, &mover, currentIterator->second.currentDistance, currentIterator->second.rotationDirection);
        const IndoorRigidMotion step = composeIndoorRigidMotions(*after, before->inverse());
        const bx::Vec3 foot = {state.x, state.y, state.footZ};
        const bx::Vec3 moved = step.apply(foot);
        m_partyRuntime.translatePartyPosition(moved.x - foot.x, moved.y - foot.y, moved.z - foot.z);
        return;
    }
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

        // A door with its own sounds (an MM9 door's start, creak and shut) plays them, not the environment's.
        if (const MechanismAudioProfile *pSounds =
                canPlaySound && m_pIndoorMapData != nullptr ? findIndoorDoorSounds(*m_pIndoorMapData, door.doorId)
                                                             : nullptr)
        {
            MechanismAudioProfile profile = *pSounds;

            if (!profile.positional)
            {
                const EventRuntimeState::PendingSound at = buildMechanismSound(0, door);
                profile.x = at.x;
                profile.y = at.y;
                profile.z = at.z;
                profile.positional = at.positional;
            }

            const std::unordered_map<uint32_t, RuntimeMechanismState>::const_iterator previousIterator =
                previousMechanisms.find(door.doorId);
            const bool wasMoving =
                previousIterator != previousMechanisms.end() && previousIterator->second.isMoving;
            const uint16_t previousState =
                previousIterator != previousMechanisms.end() ? previousIterator->second.state : currentMechanism.state;
            queueMechanismMovementAudio(
                *m_eventRuntimeState, mechanismAudioKey(door.doorId), profile, previousState, wasMoving,
                currentMechanism);

            if (wasMoving && !currentMechanism.isMoving && mechanismReachedFinalState(currentMechanism))
            {
                queueMechanismCompletionAudio(
                    *m_eventRuntimeState, mechanismAudioKey(door.doorId), profile, currentMechanism);
            }

            continue;
        }

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

    // Every floor face crossed by this frame's movement steps, then the current one (teleports, carried party).
    m_partyRuntime.takeSteppedFloorFaces(m_partyFloorFacesForPressurePlateTriggers);

    if (hasIndoorPressurePlateSupportFace(currentMoveState)
        && (m_partyFloorFacesForPressurePlateTriggers.empty()
            || m_partyFloorFacesForPressurePlateTriggers.back() != currentMoveState.supportFaceIndex))
    {
        m_partyFloorFacesForPressurePlateTriggers.push_back(currentMoveState.supportFaceIndex);
    }

    bool executed = false;

    for (size_t floorFaceIndex : m_partyFloorFacesForPressurePlateTriggers)
    {
        executed = enterPartyFloorFace(floorFaceIndex) || executed;
    }

    return executed;
}

bool IndoorSceneRuntime::enterPartyFloorFace(size_t floorFaceIndex)
{
    // Match OE floor-face semantics: short airborne/jitter frames do not re-enter the same pressure plate.
    if (!m_lastPartyFloorFaceForPressurePlateTriggers)
    {
        m_lastPartyFloorFaceForPressurePlateTriggers = floorFaceIndex;
        return false;
    }

    const size_t previousFloorFaceIndex = *m_lastPartyFloorFaceForPressurePlateTriggers;
    m_lastPartyFloorFaceForPressurePlateTriggers = floorFaceIndex;

    if (previousFloorFaceIndex == floorFaceIndex || m_pIndoorMapData == nullptr)
    {
        return false;
    }

    const std::optional<uint16_t> previousPressureEvent =
        indoorPressurePlateEventId(*m_pIndoorMapData, m_mapDeltaData, previousFloorFaceIndex);
    const std::optional<uint16_t> currentPressureEvent =
        indoorPressurePlateEventId(*m_pIndoorMapData, m_mapDeltaData, floorFaceIndex);

    if (previousPressureEvent && currentPressureEvent && *previousPressureEvent == *currentPressureEvent)
    {
        return false;
    }

    return m_worldRuntime.executeFaceTriggeredEvent(floorFaceIndex, FaceAttribute::PressurePlate, false);
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
        m_eventRuntimeState->timerControls.clear();
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
        },
        &m_eventRuntimeState->timerControls);
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
    const std::vector<int64_t> statsBefore =
        activeDecorationContext ? partyBaseStatSnapshot(m_partyRuntime.party()) : std::vector<int64_t>{};

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

    if (executed && activeDecorationContext)
    {
        reportDecorationStatGain(
            m_partyRuntime.party(), *m_eventRuntimeState, activeDecorationContext->decorVarIndex, statsBefore);
    }

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
