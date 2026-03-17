#pragma once

#include "game/EventRuntime.h"
#include "game/EventIr.h"
#include "game/MapDeltaData.h"
#include "game/MapStats.h"

#include <random>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;

class OutdoorWorldRuntime
{
public:
    struct ChestItemState
    {
        uint32_t itemId = 0;
        uint32_t quantity = 0;
        uint32_t goldAmount = 0;
        uint32_t goldRollCount = 0;
        bool isGold = false;
    };

    struct ChestViewState
    {
        uint32_t chestId = 0;
        uint16_t chestTypeId = 0;
        uint16_t flags = 0;
        std::vector<ChestItemState> items;
    };

    struct TimerState
    {
        uint16_t eventId = 0;
        bool repeating = false;
        float intervalGameMinutes = 0.0f;
        float remainingGameMinutes = 0.0f;
        std::optional<int> targetHour;
        bool hasFired = false;
    };

    void initialize(
        const MapStatsEntry &map,
        const ItemTable &itemTable,
        const std::optional<MapDeltaData> &outdoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState
    );

    bool isInitialized() const;
    int mapId() const;
    const std::string &mapName() const;
    float gameMinutes() const;
    int currentHour() const;
    void advanceGameMinutes(float minutes);

    void applyEventRuntimeState();
    bool updateTimers(
        float deltaSeconds,
        const EventRuntime &eventRuntime,
        const std::optional<EventIrProgram> &localEventIrProgram,
        const std::optional<EventIrProgram> &globalEventIrProgram
    );
    bool isChestOpened(uint32_t chestId) const;
    size_t chestCount() const;
    size_t openedChestCount() const;
    const ChestViewState *activeChestView() const;
    bool takeActiveChestItem(size_t itemIndex, ChestItemState &item);
    void closeActiveChestView();

    const EventRuntimeState::PendingMapMove *pendingMapMove() const;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();

    EventRuntimeState *eventRuntimeState();
    const EventRuntimeState *eventRuntimeState() const;

private:
    static uint32_t makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt);
    static void appendChestItem(std::vector<ChestItemState> &items, const ChestItemState &item);
    static int generateGoldAmount(int treasureLevel, std::mt19937 &rng);
    static int remapTreasureLevel(int itemTreasureLevel, int mapTreasureLevel);

    uint32_t generateRandomItemId(int treasureLevel, std::mt19937 &rng) const;
    ChestViewState buildChestView(uint32_t chestId) const;
    void activateChestView(uint32_t chestId);

    int m_mapId = 0;
    int m_mapTreasureLevel = 0;
    std::string m_mapName;
    float m_gameMinutes = 9.0f * 60.0f;
    std::vector<TimerState> m_timers;
    std::vector<MapDeltaChest> m_chests;
    std::vector<bool> m_openedChests;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    const ItemTable *m_pItemTable = nullptr;
    uint32_t m_sessionChestSeed = 0;
};
}
