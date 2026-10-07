#pragma once

#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorWorldRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/mm9/Mm9PositionedTransitionRuntime.h"
#include "game/mm9/Mm9TeacherSchedule.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/tables/ChestTable.h"

#include <cstddef>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct DecorationBillboardSet;
class DecorationTable;
class GameplayActorService;
class GameplayCombatController;
class GameplayProjectileService;
class MergedBolsterMapTable;
class MergedBolsterMonsterTable;
class MonsterProjectileTable;
class NpcDialogTable;
class Mm9MapTransitionTable;
class Mm9TeacherScheduleTable;
class SpriteFrameTable;
class SpellTable;

class IndoorSceneRuntime : public IMapSceneRuntime
{
public:
    using TimerState = ScriptedEventTimerState;

    struct Snapshot
    {
        std::optional<MapDeltaData> mapDeltaData;
        std::optional<EventRuntimeState> eventRuntimeState;
        IndoorWorldRuntime::Snapshot worldRuntime;
        IndoorPartyRuntime::Snapshot partyRuntime;
        std::vector<TimerState> timers;
        std::optional<IndoorMoveState> lastProcessedPartyMoveStateForFaceTriggers;
        std::optional<size_t> lastPartyFloorFaceForPressurePlateTriggers;
        float mechanismAccumulatorMilliseconds = 0.0f;
    };

    IndoorSceneRuntime(
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
        GameplayCombatController *pGameplayCombatController = nullptr,
        const SpriteFrameTable *pActorSpriteFrameTable = nullptr,
        const SpriteFrameTable *pProjectileSpriteFrameTable = nullptr,
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr,
        const MergedBolsterMapTable *pMergedBolsterMapTable = nullptr,
        const MergedBolsterMonsterTable *pMergedBolsterMonsterTable = nullptr,
        bool bolsterMonstersEnabled = false,
        const NpcDialogTable *pNpcDialogTable = nullptr,
        const MapItemSourceData *pItemSourceData = nullptr,
        const Mm9MapTransitionTable *pMm9MapTransitionTable = nullptr,
        const Mm9TeacherScheduleTable *pMm9TeacherScheduleTable = nullptr
    );
    IndoorSceneRuntime(
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
        const SpriteFrameTable *pActorSpriteFrameTable = nullptr,
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr,
        const MergedBolsterMapTable *pMergedBolsterMapTable = nullptr,
        const MergedBolsterMonsterTable *pMergedBolsterMonsterTable = nullptr,
        bool bolsterMonstersEnabled = false,
        const NpcDialogTable *pNpcDialogTable = nullptr,
        const MapItemSourceData *pItemSourceData = nullptr,
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

    const std::optional<MapDeltaData> &mapDeltaData() const;
    const std::optional<EventRuntimeState> &eventRuntimeStateStorage() const;
    const std::optional<ScriptedEventProgram> &localEventProgram() const override;
    const std::optional<ScriptedEventProgram> &globalEventProgram() const override;
    IndoorPartyRuntime &partyRuntime();
    const IndoorPartyRuntime &partyRuntime() const;
    IndoorWorldRuntime &worldRuntime();
    const IndoorWorldRuntime &worldRuntime() const;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void stampLastVisitTime();
    void applyMapReentryReset();
    void prepareTimers();
    bool advanceSimulation(float deltaMilliseconds);
    bool activateEvent(
        uint16_t eventId,
        const std::string &sourceKind,
        size_t sourceIndex,
        const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext = std::nullopt);

private:
    struct MechanismAudioState
    {
        bool loopStarted = false;
    };

    bool updateTimers(float deltaGameMinutes);
    void initializeTimers(double registrationGameMinutes);
    bool updatePartyFaceTriggers();
    void updateMechanismAudio(
        const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms,
        float deltaMilliseconds);

    MapStatsEntry m_map;
    std::string m_mapFileName;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const DecorationTable *m_pIndoorDecorationTable = nullptr;
    Party *m_pSessionParty = nullptr;
    std::optional<MapDeltaData> m_mapDeltaData;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    std::optional<ScriptedEventProgram> m_localEventProgram;
    std::optional<ScriptedEventProgram> m_globalEventProgram;
    EventRuntime m_eventRuntime;
    IndoorPartyRuntime m_partyRuntime;
    IndoorWorldRuntime m_worldRuntime;
    std::vector<TimerState> m_timers;
    bool m_timerDefinitionsInitialized = false;
    bool m_resetLegacyTimersOnInitialize = false;
    std::optional<IndoorMoveState> m_lastProcessedPartyMoveStateForFaceTriggers;
    std::optional<size_t> m_lastPartyFloorFaceForPressurePlateTriggers;
    std::unordered_map<uint32_t, MechanismAudioState> m_mechanismAudioStates;
    float m_mechanismAccumulatorMilliseconds = 0.0f;
    Mm9PositionedTransitionRuntime m_mm9PositionedTransitionRuntime;
    Mm9TeacherScheduleRuntime m_mm9TeacherScheduleRuntime;
};
}
