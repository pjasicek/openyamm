#pragma once

#include "game/events/EventRuntime.h"
#include "game/events/ISceneEventContext.h"
#include "game/maps/MapDeltaData.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"

#include <optional>

namespace OpenYAMM::Game
{
class IndoorWorldRuntime : public ISceneEventContext
{
public:
    IndoorWorldRuntime() = default;

    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const ObjectTable &objectTable,
        const ItemTable &itemTable,
        Party *pParty,
        std::optional<MapDeltaData> *pMapDeltaData,
        std::optional<EventRuntimeState> *pEventRuntimeState
    );

    float currentGameMinutes() const override;
    const MapDeltaData *mapDeltaData() const override;
    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ
    ) override;
    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    ) override;
    bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) override;
    bool checkMonstersKilled(
        uint32_t checkType,
        uint32_t id,
        uint32_t count,
        bool invisibleAsDead
    ) const override;

    void advanceGameMinutes(float minutes);
    void applyEventRuntimeState();
    float gameMinutes() const;

    MapDeltaData *mapDeltaData();
    EventRuntimeState *eventRuntimeState();
    const EventRuntimeState *eventRuntimeState() const;

private:
    const MapEncounterInfo *encounterInfo(uint32_t typeIndexInMapStats) const;
    const MonsterTable::MonsterStatsEntry *resolveEncounterStats(
        uint32_t typeIndexInMapStats,
        uint32_t level
    ) const;

    std::optional<MapStatsEntry> m_map;
    const MonsterTable *m_pMonsterTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    Party *m_pParty = nullptr;
    std::optional<MapDeltaData> *m_pMapDeltaData = nullptr;
    std::optional<EventRuntimeState> *m_pEventRuntimeState = nullptr;
    float m_gameMinutes = 9.0f * 60.0f;
};
}
