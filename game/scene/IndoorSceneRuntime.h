#pragma once

#include "game/indoor/IndoorPartyRuntime.h"
#include "game/indoor/IndoorWorldRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/events/EventRuntime.h"
#include "game/maps/MapDeltaData.h"
#include "game/scene/IMapSceneRuntime.h"
#include "game/tables/ChestTable.h"

#include <cstddef>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct DecorationBillboardSet;
class GameplayActorService;
class GameplayCombatController;
class GameplayProjectileService;
class MonsterProjectileTable;
class SpriteFrameTable;
class SpellTable;

class IndoorSceneRuntime : public IMapSceneRuntime
{
public:
    struct TimerState
    {
        uint16_t eventId = 0;
        bool repeating = false;
        int targetHour = 0;
        float intervalGameMinutes = 0.0f;
        float remainingGameMinutes = 0.0f;
        bool hasFired = false;
    };

    struct Snapshot
    {
        std::optional<MapDeltaData> mapDeltaData;
        std::optional<EventRuntimeState> eventRuntimeState;
        IndoorWorldRuntime::Snapshot worldRuntime;
        IndoorPartyRuntime::Snapshot partyRuntime;
        std::vector<TimerState> timers;
        std::optional<IndoorMoveState> lastProcessedPartyMoveStateForFaceTriggers;
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
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr
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
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr
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
    const std::optional<ScriptedEventProgram> &localEventProgram() const;
    const std::optional<ScriptedEventProgram> &globalEventProgram() const;
    IndoorPartyRuntime &partyRuntime();
    const IndoorPartyRuntime &partyRuntime() const;
    IndoorWorldRuntime &worldRuntime();
    const IndoorWorldRuntime &worldRuntime() const;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    bool advanceSimulation(float deltaMilliseconds);
    bool activateEvent(uint16_t eventId, const std::string &sourceKind, size_t sourceIndex);

private:
    struct MechanismAudioState
    {
        float movementSoundElapsedMilliseconds = 1000.0f;
    };

    bool updateTimers(float deltaGameMinutes);
    bool updatePartyFaceTriggers();
    void updateMechanismAudio(
        const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms,
        float deltaMilliseconds);

    MapStatsEntry m_map;
    std::string m_mapFileName;
    Party *m_pSessionParty = nullptr;
    std::optional<MapDeltaData> m_mapDeltaData;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    std::optional<ScriptedEventProgram> m_localEventProgram;
    std::optional<ScriptedEventProgram> m_globalEventProgram;
    EventRuntime m_eventRuntime;
    IndoorPartyRuntime m_partyRuntime;
    IndoorWorldRuntime m_worldRuntime;
    std::vector<TimerState> m_timers;
    std::optional<IndoorMoveState> m_lastProcessedPartyMoveStateForFaceTriggers;
    std::unordered_map<uint32_t, MechanismAudioState> m_mechanismAudioStates;
    float m_mechanismAccumulatorMilliseconds = 0.0f;
};
}
