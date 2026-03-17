#include "game/OutdoorWorldRuntime.h"

#include "game/ItemTable.h"

#include <algorithm>
#include <chrono>
#include <cstring>
#include <iostream>
#include <random>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ChestItemRecordSize = 36;
constexpr int RandomChestItemMinLevel = 1;
constexpr int RandomChestItemMaxLevel = 7;
constexpr int SpawnableItemTreasureLevels = 6;
constexpr float GameMinutesPerRealSecond = 0.5f;

std::vector<int> parseCsvIntegers(const std::optional<std::string> &note)
{
    std::vector<int> values;

    if (!note || note->empty())
    {
        return values;
    }

    std::istringstream stream(*note);
    std::string token;

    while (std::getline(stream, token, ','))
    {
        if (token.empty())
        {
            values.push_back(0);
            continue;
        }

        try
        {
            values.push_back(std::stoi(token));
        }
        catch (...)
        {
            values.push_back(0);
        }
    }

    return values;
}

void appendTimersFromProgram(
    const std::optional<EventIrProgram> &program,
    std::vector<OutdoorWorldRuntime::TimerState> &timers
)
{
    if (!program)
    {
        return;
    }

    for (const EventIrEvent &event : program->getEvents())
    {
        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation != EventIrOperation::TriggerOnTimer)
            {
                continue;
            }

            const std::vector<int> values = parseCsvIntegers(instruction.note);
            OutdoorWorldRuntime::TimerState timer = {};
            timer.eventId = event.eventId;

            if (values.size() > 6 && values[6] > 0)
            {
                timer.repeating = true;
                timer.intervalGameMinutes = static_cast<float>(values[6]) * 0.5f;
                timer.remainingGameMinutes = timer.intervalGameMinutes;
                timers.push_back(timer);
                break;
            }

            if (values.size() > 3 && values[3] > 0)
            {
                timer.repeating = false;
                timer.targetHour = values[3];
                timer.intervalGameMinutes = static_cast<float>(values[3]) * 60.0f;
                timer.remainingGameMinutes = timer.intervalGameMinutes - 9.0f * 60.0f;

                if (timer.remainingGameMinutes < 0.0f)
                {
                    timer.remainingGameMinutes += 24.0f * 60.0f;
                }

                timers.push_back(timer);
                break;
            }
        }
    }
}
}

uint32_t OutdoorWorldRuntime::makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt)
{
    return sessionSeed
        ^ static_cast<uint32_t>(mapId) * 1315423911u
        ^ (chestId + 1u) * 2654435761u
        ^ (salt + 1u) * 2246822519u;
}

void OutdoorWorldRuntime::appendChestItem(std::vector<ChestItemState> &items, const ChestItemState &item)
{
    if (item.isGold)
    {
        for (ChestItemState &existing : items)
        {
            if (existing.isGold)
            {
                existing.goldAmount += item.goldAmount;
                existing.goldRollCount += item.goldRollCount;
                return;
            }
        }

        items.push_back(item);
        return;
    }

    for (ChestItemState &existing : items)
    {
        if (!existing.isGold && existing.itemId == item.itemId)
        {
            existing.quantity += item.quantity;
            return;
        }
    }

    items.push_back(item);
}

int OutdoorWorldRuntime::generateGoldAmount(int treasureLevel, std::mt19937 &rng)
{
    switch (treasureLevel)
    {
        case 1: return std::uniform_int_distribution<int>(50, 100)(rng);
        case 2: return std::uniform_int_distribution<int>(100, 200)(rng);
        case 3: return std::uniform_int_distribution<int>(200, 500)(rng);
        case 4: return std::uniform_int_distribution<int>(500, 1000)(rng);
        case 5: return std::uniform_int_distribution<int>(1000, 2000)(rng);
        case 6: return std::uniform_int_distribution<int>(2000, 5000)(rng);
        default: return 0;
    }
}

int OutdoorWorldRuntime::remapTreasureLevel(int itemTreasureLevel, int mapTreasureLevel)
{
    static constexpr int mapping[7][7][2] = {
        {{1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}, {1, 1}},
        {{1, 1}, {1, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}, {2, 2}},
        {{1, 2}, {2, 2}, {2, 3}, {3, 3}, {3, 3}, {3, 3}, {3, 3}},
        {{2, 2}, {2, 2}, {3, 3}, {3, 4}, {4, 4}, {4, 4}, {4, 4}},
        {{2, 2}, {2, 2}, {3, 4}, {4, 4}, {4, 5}, {5, 5}, {5, 5}},
        {{2, 2}, {2, 2}, {4, 4}, {4, 5}, {5, 5}, {5, 6}, {6, 6}},
        {{2, 2}, {2, 2}, {7, 7}, {7, 7}, {7, 7}, {7, 7}, {7, 7}}
    };

    const int clampedItemLevel = std::clamp(itemTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int clampedMapLevel = std::clamp(mapTreasureLevel, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const int minLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][0];
    const int maxLevel = mapping[clampedItemLevel - 1][clampedMapLevel - 1][1];

    return (minLevel + maxLevel) / 2;
}

uint32_t OutdoorWorldRuntime::generateRandomItemId(int treasureLevel, std::mt19937 &rng) const
{
    if (m_pItemTable == nullptr)
    {
        return 0;
    }

    const int weightIndex = std::clamp(treasureLevel, 1, SpawnableItemTreasureLevels) - 1;
    int totalWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        totalWeight += entry.randomTreasureWeights[weightIndex];
    }

    if (totalWeight <= 0)
    {
        return 0;
    }

    const int pick = std::uniform_int_distribution<int>(1, totalWeight)(rng);
    int runningWeight = 0;

    for (const ItemDefinition &entry : m_pItemTable->entries())
    {
        if (entry.itemId == 0 || entry.randomTreasureWeights[weightIndex] <= 0)
        {
            continue;
        }

        runningWeight += entry.randomTreasureWeights[weightIndex];

        if (runningWeight >= pick)
        {
            return entry.itemId;
        }
    }

    return 0;
}

OutdoorWorldRuntime::ChestViewState OutdoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    ChestViewState view = {};
    view.chestId = chestId;

    if (chestId >= m_chests.size())
    {
        return view;
    }

    const MapDeltaChest &chest = m_chests[chestId];
    view.chestTypeId = chest.chestTypeId;
    view.flags = chest.flags;

    std::cout << "Chest populate: chest=" << chestId
              << " type=" << chest.chestTypeId
              << " flags=0x" << std::hex << chest.flags << std::dec
              << " raw_records=" << (chest.rawItems.size() / ChestItemRecordSize)
              << '\n';

    if (chest.rawItems.empty() || chest.inventoryMatrix.empty())
    {
        std::cout << "  empty source buffers\n";
        return view;
    }

    std::vector<int32_t> rawItemIds(chest.rawItems.size() / ChestItemRecordSize, 0);

    for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
    {
        std::memcpy(
            &rawItemIds[itemIndex],
            chest.rawItems.data() + itemIndex * ChestItemRecordSize,
            sizeof(int32_t)
        );
    }

    {
        std::ostringstream rawItemSample;
        size_t nonZeroRawItems = 0;
        size_t sampledRawItems = 0;

        for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
        {
            if (rawItemIds[itemIndex] == 0)
            {
                continue;
            }

            ++nonZeroRawItems;

            if (sampledRawItems < 12)
            {
                if (sampledRawItems > 0)
                {
                    rawItemSample << ' ';
                }

                rawItemSample << itemIndex << ':' << rawItemIds[itemIndex];
                ++sampledRawItems;
            }
        }

        std::cout << "  raw nonzero=" << nonZeroRawItems
                  << " sample=[" << rawItemSample.str() << "]"
                  << '\n';
    }

    std::mt19937 rng(makeChestSeed(m_sessionChestSeed, m_mapId, chestId, 0));
    const int mapTreasureLevel = std::clamp(m_mapTreasureLevel + 1, 1, 7);
    size_t positiveCells = 0;
    size_t negativeCells = 0;
    std::ostringstream matrixSample;
    size_t sampledCells = 0;

    for (size_t cellIndex = 0; cellIndex < chest.inventoryMatrix.size(); ++cellIndex)
    {
        const int16_t cellValue = chest.inventoryMatrix[cellIndex];

        if (cellValue > 0)
        {
            ++positiveCells;
        }
        else if (cellValue < 0)
        {
            ++negativeCells;
        }

        if (cellValue != 0 && sampledCells < 12)
        {
            if (sampledCells > 0)
            {
                matrixSample << ' ';
            }

            matrixSample << cellIndex << ':' << cellValue;
            ++sampledCells;
        }
    }

    std::cout << "  matrix positive=" << positiveCells
              << " negative=" << negativeCells
              << " sample=[" << matrixSample.str() << "]"
              << '\n';

    size_t materializedRecords = 0;

    for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
    {
        const int32_t itemId = rawItemIds[itemIndex];

        if (itemId == 0)
        {
            continue;
        }

        const bool hasGridReference = std::find(
            chest.inventoryMatrix.begin(),
            chest.inventoryMatrix.end(),
            static_cast<int16_t>(itemIndex + 1)
        ) != chest.inventoryMatrix.end();
        materializedRecords += 1;
        std::cout << "  record=" << itemIndex
                  << " raw_item_id=" << itemId
                  << " grid_ref=" << (hasGridReference ? "yes" : "no")
                  << '\n';

        if (itemId > 0)
        {
            ChestItemState item = {};
            item.itemId = static_cast<uint32_t>(itemId);
            item.quantity = 1;
            appendChestItem(view.items, item);
            std::cout << "    serialized item=" << item.itemId;

            if (m_pItemTable != nullptr && m_pItemTable->get(item.itemId) == nullptr)
            {
                std::cout << " unknown";
            }

            std::cout << '\n';
            continue;
        }

        if (itemId > -8 && itemId < 0)
        {
            const int resolvedTreasureLevel = remapTreasureLevel(-itemId, mapTreasureLevel);
            const int generatedCount = std::uniform_int_distribution<int>(1, 5)(rng);
            std::cout << "    random placeholder level=" << (-itemId)
                      << " map_treasure=" << mapTreasureLevel
                      << " resolved=" << resolvedTreasureLevel
                      << " rolls=" << generatedCount
                      << '\n';

            for (int count = 0; count < generatedCount; ++count)
            {
                const int roll = std::uniform_int_distribution<int>(0, 99)(rng);
                std::cout << "      roll=" << roll;

                if (roll < 20)
                {
                    std::cout << " -> empty\n";
                    continue;
                }

                if (roll < 60)
                {
                    ChestItemState gold = {};
                    gold.goldAmount = static_cast<uint32_t>(generateGoldAmount(
                        std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels),
                        rng
                    ));
                    gold.goldRollCount = 1;
                    gold.isGold = gold.goldAmount > 0;

                    if (gold.isGold)
                    {
                        appendChestItem(view.items, gold);
                        std::cout << " -> gold " << gold.goldAmount << '\n';
                    }
                    else
                    {
                        std::cout << " -> gold 0 skipped\n";
                    }

                    continue;
                }

                const int generationLevel = std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels);
                const uint32_t generatedItemId = generateRandomItemId(generationLevel, rng);

                if (generatedItemId == 0)
                {
                    std::cout << " -> item generation failed\n";
                    continue;
                }

                ChestItemState item = {};
                item.itemId = generatedItemId;
                item.quantity = 1;
                appendChestItem(view.items, item);
                std::cout << " -> item " << generatedItemId << '\n';
            }

            continue;
        }

        std::cout << "    unsupported negative item marker skipped\n";
    }

    std::cout << "  materialized_records=" << materializedRecords
              << " final_entries=" << view.items.size()
              << '\n';

    return view;
}

void OutdoorWorldRuntime::activateChestView(uint32_t chestId)
{
    if (chestId >= m_chests.size())
    {
        return;
    }

    if (chestId >= m_materializedChestViews.size())
    {
        return;
    }

    if (!m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
}

void OutdoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const ItemTable &itemTable,
    const std::optional<MapDeltaData> &outdoorMapDeltaData,
    const std::optional<EventRuntimeState> &eventRuntimeState
)
{
    m_mapId = map.id;
    m_mapName = map.name;
    m_mapTreasureLevel = map.treasureLevel;
    m_gameMinutes = 9.0f * 60.0f;
    m_timers.clear();
    m_chests = outdoorMapDeltaData ? outdoorMapDeltaData->chests : std::vector<MapDeltaChest>();
    m_openedChests.assign(outdoorMapDeltaData ? outdoorMapDeltaData->chests.size() : 0, false);
    m_materializedChestViews.assign(m_chests.size(), std::nullopt);
    m_activeChestView.reset();
    m_eventRuntimeState = eventRuntimeState;
    m_pItemTable = &itemTable;
    std::random_device randomDevice;
    const uint64_t timeSeed = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ static_cast<uint32_t>(timeSeed) ^ static_cast<uint32_t>(timeSeed >> 32);
}

bool OutdoorWorldRuntime::isInitialized() const
{
    return m_mapId != 0 || !m_mapName.empty() || m_eventRuntimeState.has_value();
}

int OutdoorWorldRuntime::mapId() const
{
    return m_mapId;
}

const std::string &OutdoorWorldRuntime::mapName() const
{
    return m_mapName;
}

float OutdoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

int OutdoorWorldRuntime::currentHour() const
{
    int currentHour = static_cast<int>(m_gameMinutes / 60.0f) % 24;

    if (currentHour < 0)
    {
        currentHour += 24;
    }

    return currentHour;
}

void OutdoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes <= 0.0f)
    {
        return;
    }

    m_gameMinutes += minutes;
}

void OutdoorWorldRuntime::applyEventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return;
    }

    for (uint32_t chestId : m_eventRuntimeState->openedChestIds)
    {
        if (chestId < m_openedChests.size())
        {
            m_openedChests[chestId] = true;
            activateChestView(chestId);
        }
    }
}

bool OutdoorWorldRuntime::updateTimers(
    float deltaSeconds,
    const EventRuntime &eventRuntime,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram
)
{
    if (!m_eventRuntimeState || deltaSeconds <= 0.0f)
    {
        return false;
    }

    if (m_timers.empty())
    {
        appendTimersFromProgram(localEventIrProgram, m_timers);
        appendTimersFromProgram(globalEventIrProgram, m_timers);
    }

    if (m_timers.empty())
    {
        return false;
    }

    const float deltaGameMinutes = deltaSeconds * GameMinutesPerRealSecond;
    m_gameMinutes += deltaGameMinutes;

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

        if (eventRuntime.executeEventById(
                localEventIrProgram,
                globalEventIrProgram,
                timer.eventId,
                *m_eventRuntimeState))
        {
            executedAny = true;
            applyEventRuntimeState();
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

bool OutdoorWorldRuntime::isChestOpened(uint32_t chestId) const
{
    return chestId < m_openedChests.size() ? m_openedChests[chestId] : false;
}

size_t OutdoorWorldRuntime::chestCount() const
{
    return m_openedChests.size();
}

size_t OutdoorWorldRuntime::openedChestCount() const
{
    size_t count = 0;

    for (bool isOpened : m_openedChests)
    {
        if (isOpened)
        {
            ++count;
        }
    }

    return count;
}

const OutdoorWorldRuntime::ChestViewState *OutdoorWorldRuntime::activeChestView() const
{
    if (!m_activeChestView)
    {
        return nullptr;
    }

    return &*m_activeChestView;
}

bool OutdoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeChestView || itemIndex >= m_activeChestView->items.size())
    {
        return false;
    }

    item = m_activeChestView->items[itemIndex];
    m_activeChestView->items.erase(m_activeChestView->items.begin() + static_cast<ptrdiff_t>(itemIndex));

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

void OutdoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

const EventRuntimeState::PendingMapMove *OutdoorWorldRuntime::pendingMapMove() const
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState->pendingMapMove;
}

std::optional<EventRuntimeState::PendingMapMove> OutdoorWorldRuntime::consumePendingMapMove()
{
    if (!m_eventRuntimeState || !m_eventRuntimeState->pendingMapMove)
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingMapMove> result = std::move(m_eventRuntimeState->pendingMapMove);
    m_eventRuntimeState->pendingMapMove.reset();
    return result;
}

EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState()
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}

const EventRuntimeState *OutdoorWorldRuntime::eventRuntimeState() const
{
    if (!m_eventRuntimeState)
    {
        return nullptr;
    }

    return &*m_eventRuntimeState;
}
}
