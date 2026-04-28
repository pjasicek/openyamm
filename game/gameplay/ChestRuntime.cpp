#include "game/gameplay/ChestRuntime.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cstring>
#include <iostream>
#include <limits>
#include <numeric>
#include <optional>
#include <random>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ChestItemRecordSize = 36;
constexpr int RandomChestItemMinLevel = 1;
constexpr int RandomChestItemMaxLevel = 7;
constexpr int SpawnableItemTreasureLevels = 6;

bool chestItemContainsCell(const GameplayChestItemState &item, uint8_t gridX, uint8_t gridY)
{
    return gridX >= item.gridX
        && gridX < item.gridX + item.width
        && gridY >= item.gridY
        && gridY < item.gridY + item.height;
}

bool chestItemFitsAt(
    const GameplayChestItemState &item,
    uint8_t gridX,
    uint8_t gridY,
    uint8_t gridWidth,
    uint8_t gridHeight)
{
    return item.width > 0
        && item.height > 0
        && gridX + item.width <= gridWidth
        && gridY + item.height <= gridHeight;
}

bool chestItemsOverlap(const GameplayChestItemState &left, const GameplayChestItemState &right)
{
    return left.gridX < right.gridX + right.width
        && left.gridX + left.width > right.gridX
        && left.gridY < right.gridY + right.height
        && left.gridY + left.height > right.gridY;
}

struct GoldHeapVisual
{
    uint8_t width = 1;
    uint8_t height = 1;
};

GoldHeapVisual classifyGoldHeapVisual(uint32_t goldAmount)
{
    if (goldAmount <= 200)
    {
        return {1, 1};
    }

    if (goldAmount <= 1000)
    {
        return {2, 1};
    }

    return {2, 1};
}

bool canPlaceChestItem(
    const GameplayChestItemState &item,
    const std::vector<GameplayChestItemState> &placedItems,
    uint8_t gridWidth,
    uint8_t gridHeight)
{
    if (!chestItemFitsAt(item, item.gridX, item.gridY, gridWidth, gridHeight))
    {
        return false;
    }

    for (const GameplayChestItemState &placedItem : placedItems)
    {
        if (chestItemsOverlap(placedItem, item))
        {
            return false;
        }
    }

    return true;
}

std::vector<uint8_t> buildRandomChestCellOrder(uint8_t gridWidth, uint8_t gridHeight, std::mt19937 &rng)
{
    const size_t chestArea = static_cast<size_t>(gridWidth) * gridHeight;
    std::vector<uint8_t> cellOrder(chestArea, 0);
    std::iota(cellOrder.begin(), cellOrder.end(), 0);
    std::shuffle(cellOrder.begin(), cellOrder.end(), rng);
    return cellOrder;
}

std::optional<std::pair<uint8_t, uint8_t>> findFirstFreeChestSlot(
    const std::vector<GameplayChestItemState> &items,
    uint8_t itemWidth,
    uint8_t itemHeight,
    uint8_t gridWidth,
    uint8_t gridHeight)
{
    if (itemWidth == 0 || itemHeight == 0 || itemWidth > gridWidth || itemHeight > gridHeight)
    {
        return std::nullopt;
    }

    std::vector<bool> occupied(static_cast<size_t>(gridWidth) * gridHeight, false);

    for (const GameplayChestItemState &item : items)
    {
        for (uint8_t offsetY = 0; offsetY < item.height; ++offsetY)
        {
            for (uint8_t offsetX = 0; offsetX < item.width; ++offsetX)
            {
                const uint8_t cellX = item.gridX + offsetX;
                const uint8_t cellY = item.gridY + offsetY;

                if (cellX >= gridWidth || cellY >= gridHeight)
                {
                    continue;
                }

                occupied[static_cast<size_t>(cellY) * gridWidth + cellX] = true;
            }
        }
    }

    for (int y = 0; y <= gridHeight - itemHeight; ++y)
    {
        for (int x = 0; x <= gridWidth - itemWidth; ++x)
        {
            bool canPlace = true;

            for (uint8_t offsetY = 0; offsetY < itemHeight && canPlace; ++offsetY)
            {
                for (uint8_t offsetX = 0; offsetX < itemWidth; ++offsetX)
                {
                    const size_t index =
                        static_cast<size_t>(y + offsetY) * gridWidth + static_cast<size_t>(x + offsetX);

                    if (occupied[index])
                    {
                        canPlace = false;
                        break;
                    }
                }
            }

            if (canPlace)
            {
                return std::pair<uint8_t, uint8_t>(uint8_t(x), uint8_t(y));
            }
        }
    }

    return std::nullopt;
}

void resolveChestItemSize(GameplayChestItemState &item, const ItemTable *pItemTable)
{
    if (item.isGold)
    {
        const GoldHeapVisual goldVisual = classifyGoldHeapVisual(item.goldAmount);
        item.width = goldVisual.width;
        item.height = goldVisual.height;
        return;
    }

    item.itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;
    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(item.itemId) : nullptr;
    item.width = pItemDefinition != nullptr ? std::max<uint8_t>(1, pItemDefinition->inventoryWidth) : 1;
    item.height = pItemDefinition != nullptr ? std::max<uint8_t>(1, pItemDefinition->inventoryHeight) : 1;
}

void tryPlaceHiddenChestItems(GameplayChestViewState &view)
{
    for (auto it = view.hiddenItems.begin(); it != view.hiddenItems.end();)
    {
        const std::optional<std::pair<uint8_t, uint8_t>> slot =
            findFirstFreeChestSlot(view.items, it->width, it->height, view.gridWidth, view.gridHeight);

        if (!slot.has_value())
        {
            ++it;
            continue;
        }

        GameplayChestItemState item = *it;
        item.gridX = slot->first;
        item.gridY = slot->second;
        view.items.push_back(item);
        it = view.hiddenItems.erase(it);
    }
}

uint32_t makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt)
{
    return sessionSeed
        ^ uint32_t(mapId) * 1315423911u
        ^ (chestId + 1u) * 2654435761u
        ^ (salt + 1u) * 2246822519u;
}

int chestItemValue(
    const GameplayChestItemState &item,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    if (item.isGold)
    {
        return static_cast<int>(std::min<uint32_t>(item.goldAmount, uint32_t(std::numeric_limits<int>::max())));
    }

    const uint32_t itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;
    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    return ItemEnchantRuntime::itemValue(
        item.item,
        *pItemDefinition,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable) * std::max(1u, item.quantity);
}

int generateGoldAmount(int treasureLevel, std::mt19937 &rng)
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

std::pair<int, int> remapTreasureLevelRange(int itemTreasureLevel, int mapTreasureLevel)
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
    return {minLevel, maxLevel};
}

int sampleRemappedTreasureLevel(int itemTreasureLevel, int mapTreasureLevel, std::mt19937 &rng)
{
    const auto [minimumLevel, maximumLevel] = remapTreasureLevelRange(itemTreasureLevel, mapTreasureLevel);
    return std::uniform_int_distribution<int>(minimumLevel, maximumLevel)(rng);
}

void writeChestItemDebug(
    std::ostream &stream,
    const GameplayChestItemState &item,
    const ItemTable *pItemTable)
{
    if (item.isGold)
    {
        stream << "gold=" << item.goldAmount;
        return;
    }

    const uint32_t itemId = item.item.objectDescriptionId != 0 ? item.item.objectDescriptionId : item.itemId;
    stream << "item=" << itemId;

    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItemDefinition != nullptr)
    {
        stream << ":\"" << pItemDefinition->name << "\"";
    }

    stream << "@(" << static_cast<unsigned>(item.gridX)
           << "," << static_cast<unsigned>(item.gridY)
           << ") " << static_cast<unsigned>(item.width)
           << "x" << static_cast<unsigned>(item.height);
}

void writeChestItemListDebug(
    std::ostream &stream,
    const std::vector<GameplayChestItemState> &items,
    const ItemTable *pItemTable)
{
    stream << '[';

    for (size_t itemIndex = 0; itemIndex < items.size(); ++itemIndex)
    {
        if (itemIndex > 0)
        {
            stream << ", ";
        }

        writeChestItemDebug(stream, items[itemIndex], pItemTable);
    }

    stream << ']';
}

void logChestMaterializationDebug(
    const GameplayChestViewState &view,
    const std::vector<int32_t> &rawItemIds,
    int mapTreasureLevel,
    int mapId,
    const ItemTable *pItemTable)
{
    std::cout << "Chest populate chest=" << view.chestId
              << " map=" << mapId
              << " type=" << view.chestTypeId
              << " treasure=" << mapTreasureLevel
              << " grid=" << static_cast<unsigned>(view.gridWidth)
              << "x" << static_cast<unsigned>(view.gridHeight)
              << " fixed=[";

    bool wroteFixed = false;

    for (int32_t rawItemId : rawItemIds)
    {
        if (rawItemId <= 0)
        {
            continue;
        }

        if (wroteFixed)
        {
            std::cout << ", ";
        }

        std::cout << rawItemId;
        const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(static_cast<uint32_t>(rawItemId)) : nullptr;

        if (pItemDefinition != nullptr)
        {
            std::cout << ":\"" << pItemDefinition->name << "\"";
        }

        wroteFixed = true;
    }

    std::cout << "] visible=";
    writeChestItemListDebug(std::cout, view.items, pItemTable);
    std::cout << " hidden=";
    writeChestItemListDebug(std::cout, view.hiddenItems, pItemTable);
    std::cout << '\n';
}
}

GameplayChestViewState buildMaterializedChestView(
    uint32_t chestId,
    const MapDeltaChest &chest,
    int mapTreasureLevel,
    int mapId,
    uint32_t sessionChestSeed,
    const ChestTable *pChestTable,
    const ItemTable *pItemTable,
    Party *pParty)
{
    GameplayChestViewState view = {};
    view.chestId = chestId;
    view.chestTypeId = chest.chestTypeId;
    view.flags = chest.flags;

    const ChestEntry *pChestEntry = pChestTable != nullptr ? pChestTable->get(chest.chestTypeId) : nullptr;
    view.gridWidth = pChestEntry != nullptr && pChestEntry->gridWidth > 0 ? pChestEntry->gridWidth : 9;
    view.gridHeight = pChestEntry != nullptr && pChestEntry->gridHeight > 0 ? pChestEntry->gridHeight : 9;

    if (chest.rawItems.empty() || chest.inventoryMatrix.empty() || view.gridWidth == 0 || view.gridHeight == 0)
    {
        return view;
    }

    std::vector<int32_t> rawItemIds(chest.rawItems.size() / ChestItemRecordSize, 0);

    for (size_t itemIndex = 0; itemIndex < rawItemIds.size(); ++itemIndex)
    {
        std::memcpy(
            &rawItemIds[itemIndex],
            chest.rawItems.data() + itemIndex * ChestItemRecordSize,
            sizeof(int32_t));
    }

    const int normalizedMapTreasureLevel =
        std::clamp(mapTreasureLevel + 1, RandomChestItemMinLevel, RandomChestItemMaxLevel);
    const StandardItemEnchantTable *pStandardItemEnchantTable =
        pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr;

    const auto materializeChestRecord =
        [&](int32_t rawItemId, size_t recordIndex)
        {
            std::vector<GameplayChestItemState> generatedItems;

            if (rawItemId == 0)
            {
                return generatedItems;
            }

            if (rawItemId > 0)
            {
                if (pItemTable == nullptr)
                {
                    return generatedItems;
                }

                GameplayChestItemState item = {};
                item.item = ItemGenerator::makeInventoryItem(
                    uint32_t(rawItemId),
                    *pItemTable,
                    ItemGenerationMode::ChestLoot);
                item.itemId = item.item.objectDescriptionId;
                item.quantity = item.item.quantity;
                resolveChestItemSize(item, pItemTable);
                generatedItems.push_back(item);
                return generatedItems;
            }

            if (rawItemId <= -8)
            {
                return generatedItems;
            }

            std::mt19937 rng(makeChestSeed(sessionChestSeed, mapId, chestId, uint32_t(recordIndex)));
            const int resolvedTreasureLevel = sampleRemappedTreasureLevel(-rawItemId, normalizedMapTreasureLevel, rng);

            if (resolvedTreasureLevel == RandomChestItemMaxLevel)
            {
                if (pItemTable == nullptr
                    || pStandardItemEnchantTable == nullptr
                    || pSpecialItemEnchantTable == nullptr)
                {
                    return generatedItems;
                }

                const std::optional<InventoryItem> generatedItem =
                    ItemGenerator::generateRandomInventoryItem(
                        *pItemTable,
                        *pStandardItemEnchantTable,
                        *pSpecialItemEnchantTable,
                        ItemGenerationRequest{
                            SpawnableItemTreasureLevels,
                            ItemGenerationMode::ChestLoot,
                            true,
                            true},
                        pParty,
                        rng);

                if (generatedItem.has_value())
                {
                    GameplayChestItemState item = {};
                    item.item = *generatedItem;
                    item.itemId = item.item.objectDescriptionId;
                    item.quantity = item.item.quantity;
                    resolveChestItemSize(item, pItemTable);
                    generatedItems.push_back(item);
                }

                return generatedItems;
            }

            const int generatedCount = std::uniform_int_distribution<int>(1, 5)(rng);

            for (int generatedIndex = 0; generatedIndex < generatedCount; ++generatedIndex)
            {
                const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

                if (roll < 20)
                {
                    continue;
                }

                GameplayChestItemState item = {};

                if (roll < 60)
                {
                    item.goldAmount = uint32_t(generateGoldAmount(
                        std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels),
                        rng));
                    item.goldRollCount = item.goldAmount > 0 ? 1u : 0u;
                    item.isGold = item.goldAmount > 0;

                    if (!item.isGold)
                    {
                        continue;
                    }
                }
                else
                {
                    if (pItemTable == nullptr
                        || pStandardItemEnchantTable == nullptr
                        || pSpecialItemEnchantTable == nullptr)
                    {
                        continue;
                    }

                    const std::optional<InventoryItem> generatedItem =
                        ItemGenerator::generateRandomInventoryItem(
                            *pItemTable,
                            *pStandardItemEnchantTable,
                            *pSpecialItemEnchantTable,
                            ItemGenerationRequest{
                                std::min(resolvedTreasureLevel, SpawnableItemTreasureLevels),
                                ItemGenerationMode::ChestLoot},
                            pParty,
                            rng);

                    if (!generatedItem)
                    {
                        continue;
                    }

                    item.item = *generatedItem;
                    item.itemId = item.item.objectDescriptionId;
                    item.quantity = item.item.quantity;
                }

                resolveChestItemSize(item, pItemTable);
                generatedItems.push_back(item);
            }

            return generatedItems;
        };

    std::vector<std::vector<GameplayChestItemState>> materializedRecordItems(rawItemIds.size());
    std::vector<bool> placedRecords(rawItemIds.size(), false);
    std::vector<GameplayChestItemState> guaranteedDeferredItems;
    std::vector<GameplayChestItemState> randomDeferredItems;

    const auto deferChestItem =
        [&](const GameplayChestItemState &item, int32_t rawItemId)
        {
            if (rawItemId > 0 || rawItemId == -RandomChestItemMaxLevel)
            {
                guaranteedDeferredItems.push_back(item);
                return;
            }

            randomDeferredItems.push_back(item);
        };

    for (size_t recordIndex = 0; recordIndex < rawItemIds.size(); ++recordIndex)
    {
        materializedRecordItems[recordIndex] = materializeChestRecord(rawItemIds[recordIndex], recordIndex);
    }

    for (uint8_t gridY = 0; gridY < view.gridHeight; ++gridY)
    {
        for (uint8_t gridX = 0; gridX < view.gridWidth; ++gridX)
        {
            const size_t cellIndex = size_t(gridY) * view.gridWidth + gridX;

            if (cellIndex >= chest.inventoryMatrix.size())
            {
                continue;
            }

            const int16_t cellValue = chest.inventoryMatrix[cellIndex];

            if (cellValue <= 0)
            {
                continue;
            }

            const size_t recordIndex = size_t(cellValue - 1);

            if (recordIndex >= rawItemIds.size() || placedRecords[recordIndex])
            {
                continue;
            }

            placedRecords[recordIndex] = true;
            const std::vector<GameplayChestItemState> &recordItems = materializedRecordItems[recordIndex];

            if (recordItems.empty())
            {
                continue;
            }

            GameplayChestItemState anchoredItem = recordItems.front();
            anchoredItem.gridX = gridX;
            anchoredItem.gridY = gridY;

            if (rawItemIds[recordIndex] < 0 && rawItemIds[recordIndex] != -RandomChestItemMaxLevel)
            {
                randomDeferredItems.push_back(anchoredItem);
            }
            else if (canPlaceChestItem(anchoredItem, view.items, view.gridWidth, view.gridHeight))
            {
                view.items.push_back(anchoredItem);
            }
            else
            {
                deferChestItem(anchoredItem, rawItemIds[recordIndex]);
            }

            for (size_t itemIndex = 1; itemIndex < recordItems.size(); ++itemIndex)
            {
                deferChestItem(recordItems[itemIndex], rawItemIds[recordIndex]);
            }
        }
    }

    for (size_t recordIndex = 0; recordIndex < materializedRecordItems.size(); ++recordIndex)
    {
        if (placedRecords[recordIndex])
        {
            continue;
        }

        for (const GameplayChestItemState &item : materializedRecordItems[recordIndex])
        {
            deferChestItem(item, rawItemIds[recordIndex]);
        }
    }

    std::mt19937 placementRng(makeChestSeed(sessionChestSeed, mapId, chestId, 0xfaceu));
    const std::vector<uint8_t> placementCellOrder =
        buildRandomChestCellOrder(view.gridWidth, view.gridHeight, placementRng);

    const auto placeDeferredItems =
        [&](const std::vector<GameplayChestItemState> &deferredItems, bool keepOverflowHidden)
        {
            for (const GameplayChestItemState &deferredItem : deferredItems)
            {
                bool placed = false;

                for (uint8_t cellIndex : placementCellOrder)
                {
                    GameplayChestItemState candidate = deferredItem;
                    candidate.gridX = uint8_t(cellIndex % view.gridWidth);
                    candidate.gridY = uint8_t(cellIndex / view.gridWidth);

                    if (!canPlaceChestItem(candidate, view.items, view.gridWidth, view.gridHeight))
                    {
                        continue;
                    }

                    view.items.push_back(candidate);
                    placed = true;
                    break;
                }

                if (!placed)
                {
                    if (keepOverflowHidden)
                    {
                        view.hiddenItems.push_back(deferredItem);
                    }
                }
            }
        };

    std::stable_sort(
        randomDeferredItems.begin(),
        randomDeferredItems.end(),
        [&](const GameplayChestItemState &left, const GameplayChestItemState &right)
        {
            return chestItemValue(
                left,
                pItemTable,
                pStandardItemEnchantTable,
                pSpecialItemEnchantTable)
                > chestItemValue(
                    right,
                    pItemTable,
                    pStandardItemEnchantTable,
                    pSpecialItemEnchantTable);
        });

    placeDeferredItems(guaranteedDeferredItems, true);
    placeDeferredItems(randomDeferredItems, false);

    logChestMaterializationDebug(view, rawItemIds, mapTreasureLevel, mapId, pItemTable);

    return view;
}

bool takeChestItem(GameplayChestViewState &view, size_t itemIndex, GameplayChestItemState &item)
{
    if (itemIndex >= view.items.size())
    {
        return false;
    }

    item = view.items[itemIndex];
    view.items.erase(view.items.begin() + ptrdiff_t(itemIndex));
    tryPlaceHiddenChestItems(view);
    return true;
}

bool takeChestItemAt(GameplayChestViewState &view, uint8_t gridX, uint8_t gridY, GameplayChestItemState &item)
{
    for (size_t itemIndex = 0; itemIndex < view.items.size(); ++itemIndex)
    {
        if (!chestItemContainsCell(view.items[itemIndex], gridX, gridY))
        {
            continue;
        }

        item = view.items[itemIndex];
        view.items.erase(view.items.begin() + ptrdiff_t(itemIndex));
        tryPlaceHiddenChestItems(view);
        return true;
    }

    return false;
}

bool tryPlaceChestItemAt(
    GameplayChestViewState &view,
    const GameplayChestItemState &item,
    uint8_t gridX,
    uint8_t gridY)
{
    GameplayChestItemState placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    const auto canPlace =
        [&view](const GameplayChestItemState &candidate)
        {
            if (!chestItemFitsAt(candidate, candidate.gridX, candidate.gridY, view.gridWidth, view.gridHeight))
            {
                return false;
            }

            for (const GameplayChestItemState &existingItem : view.items)
            {
                if (chestItemsOverlap(existingItem, candidate))
                {
                    return false;
                }
            }

            return true;
        };

    if (!canPlace(placedItem))
    {
        const std::optional<std::pair<uint8_t, uint8_t>> fallbackPlacement =
            findFirstFreeChestSlot(view.items, placedItem.width, placedItem.height, view.gridWidth, view.gridHeight);

        if (!fallbackPlacement)
        {
            return false;
        }

        placedItem.gridX = fallbackPlacement->first;
        placedItem.gridY = fallbackPlacement->second;
    }

    view.items.push_back(placedItem);
    return true;
}
}
