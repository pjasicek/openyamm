#include "game/items/ItemGenerator.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/StringUtils.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
bool defaultIdentifiedState(const ItemDefinition &itemDefinition, ItemGenerationMode mode)
{
    if (mode == ItemGenerationMode::Shop)
    {
        return true;
    }

    // Loot identification is item-driven, not chest-driven:
    // items that do not require identification spawn identified,
    // while loot items that do require identification do not.
    if (!ItemRuntime::requiresIdentification(itemDefinition))
    {
        return true;
    }

    return false;
}

bool needsPotionPower(const InventoryItem &item, const ItemTable &itemTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);
    return pItemDefinition != nullptr && pItemDefinition->hasPotionPower && item.standardEnchantPower == 0;
}

// Weapons, armour and jewellery: the items a shop takes from its world's own pool (devdocs/LOOT_POOL.md).
// Potions, scrolls, books, reagents, gems and wands come from the merged base in every world.
bool isPooledEquipment(const ItemDefinition &entry)
{
    static const std::array<const char *, 13> PooledEquipStats = {
        "Weapon", "Weapon2", "Weapon1or2", "Missile", "Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets", "Boots",
        "Ring", "Amulet"};
    return std::any_of(PooledEquipStats.begin(), PooledEquipStats.end(),
        [&entry](const char *pEquipStat) { return entry.equipStat == pEquipStat; });
}

}

bool ItemGenerator::shopPoolAllows(const ItemDefinition &entry, const std::string &worldPool)
{
    if (worldPool.empty() || toLowerCopy(entry.packageId) == worldPool)
    {
        return true;
    }

    return !ItemRuntime::isRareItem(entry) && !isPooledEquipment(entry);
}

namespace
{
bool shouldTryGenerateRareItem(const ItemGenerationRequest &request)
{
    return request.allowRareItems
        && request.mode != ItemGenerationMode::Shop
        && std::clamp(request.treasureLevel, 1, 6) >= 6;
}

std::optional<uint32_t> chooseRandomRareItem(
    const ItemTable &itemTable,
    Party *pParty,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    std::vector<uint32_t> candidateIds;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId == 0 || entry.hasContentFlag("NoRandom")
            || !ItemRuntime::isUniquelyGeneratedRareItem(entry))
        {
            continue;
        }

        if (filter && !filter(entry))
        {
            continue;
        }

        if (pParty != nullptr && pParty->hasFoundArtifactItem(entry.itemId))
        {
            continue;
        }

        candidateIds.push_back(entry.itemId);
    }

    if (candidateIds.empty())
    {
        return std::nullopt;
    }

    const size_t index = std::uniform_int_distribution<size_t>(0, candidateIds.size() - 1)(rng);
    return candidateIds[index];
}

// The world's loot class for the treasure level, weighted as loot.yml gives it; rare items roll on their own.
std::optional<uint32_t> chooseWorldLootItem(
    const ItemTable &itemTable,
    const WorldLootTable &loot,
    int treasureLevel,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    const std::vector<WorldLootTable::Entry> *pEntries = loot.entriesForTreasureLevel(treasureLevel);

    if (pEntries == nullptr)
    {
        return std::nullopt;
    }

    std::vector<uint32_t> itemIds;
    std::vector<int> weights;

    for (const WorldLootTable::Entry &entry : *pEntries)
    {
        const ItemDefinition *pItem = itemTable.get(entry.itemId);

        if (pItem == nullptr || pItem->hasContentFlag("NoRandom") || ItemRuntime::isRareItem(*pItem)
            || (filter && !filter(*pItem)))
        {
            continue;
        }

        itemIds.push_back(entry.itemId);
        weights.push_back(entry.weight);
    }

    if (itemIds.empty())
    {
        return std::nullopt;
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    return itemIds[distribution(rng)];
}

int parsePositiveInteger(const std::string &value)
{
    int result = 0;
    bool hasDigit = false;

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            break;
        }

        hasDigit = true;
        result = result * 10 + character - '0';
    }

    return hasDigit ? std::max(0, result) : 0;
}

uint16_t baseWandCharges(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat != "WeaponW")
    {
        return 0;
    }

    return static_cast<uint16_t>(std::clamp(parsePositiveInteger(itemDefinition.mod2) + 1, 1, 0xFFFF));
}

void initializeWandCharges(InventoryItem &item, const ItemDefinition &itemDefinition, int randomBonus)
{
    const uint16_t baseCharges = baseWandCharges(itemDefinition);

    if (baseCharges == 0)
    {
        return;
    }

    const int maxCharges = std::clamp(static_cast<int>(baseCharges) + std::max(0, randomBonus), 1, 0xFFFF);
    item.currentCharges = static_cast<uint16_t>(maxCharges);
    item.maxCharges = static_cast<uint16_t>(maxCharges);
}
}

InventoryItem ItemGenerator::makeInventoryItem(
    uint32_t itemId,
    const ItemTable &itemTable,
    ItemGenerationMode mode)
{
    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    const ItemDefinition *pItemDefinition = itemTable.get(itemId);

    if (pItemDefinition != nullptr)
    {
        item.width = std::max<uint8_t>(1, pItemDefinition->inventoryWidth);
        item.height = std::max<uint8_t>(1, pItemDefinition->inventoryHeight);
        item.identified = defaultIdentifiedState(*pItemDefinition, mode);
        item.rarity = pItemDefinition->rarity;
        initializeWandCharges(item, *pItemDefinition, 0);

        if (ItemRuntime::isRareItem(*pItemDefinition))
        {
            item.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
        }

        assignSpecialItemEnchants(item, *pItemDefinition);
    }

    return item;
}

void ItemGenerator::assignSpecialItemEnchants(InventoryItem &item, const ItemDefinition &itemDefinition)
{
    if (itemDefinition.rarity != ItemRarity::Special || item.standardEnchantId != 0 || item.specialEnchantId != 0)
    {
        return;
    }

    item.standardEnchantId = itemDefinition.specialItemStandardEnchantId;
    item.standardEnchantPower =
        itemDefinition.specialItemStandardEnchantId != 0 ? itemDefinition.specialItemStandardEnchantPower : 0;
    item.specialEnchantId = itemDefinition.specialItemSpecialEnchantId;
}

std::optional<InventoryItem> ItemGenerator::generateRandomInventoryItem(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const ItemGenerationRequest &request,
    Party *pParty,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &callerFilter)
{
    // A boss's drop (rulesets that flag it, MAW) is always equipment that takes enchantments. A world with loot of
    // its own (loot.yml) rolls only the items it lists.
    const WorldLootTable *pWorldLoot = itemTable.worldLoot(request.worldId);
    // Random loot rolls from one pool of every mounted world's items; a shop keeps its world's own equipment, and so
    // does loot on the merged MM6-MM8 base's maps with the Gameplay setting "MM9 loot in MM6-MM8" off
    // (Party::mm9LootInOlderWorlds, the default).
    const std::string worldPool = itemTable.lootPoolForWorld(request.worldId);
    const bool ownWorldOnly = request.mode == ItemGenerationMode::Shop
        || (pParty != nullptr && !pParty->mm9LootInOlderWorlds() && worldPool == "engine");
    const std::string shopPool = ownWorldOnly ? worldPool : std::string();
    const std::function<bool(const ItemDefinition &)> filter =
        [&request, &callerFilter, pWorldLoot, &shopPool](const ItemDefinition &entry)
        {
            return entry.availableInWorld(request.worldId) && shopPoolAllows(entry, shopPool)
                && (!callerFilter || callerFilter(entry))
                && (!request.boss || ItemEnchantRuntime::isEnchantable(entry))
                && (pWorldLoot == nullptr || pWorldLoot->listedItemIds.contains(entry.itemId));
        };

    if (request.rareItemsOnly && !gameRulesFor(pParty).items.levelSevenGivesRareItem())
    {
        // A level-7 chest slot rolls as a boss's drop there (MAW re-rolls the engine's chest artifacts through the
        // boss path, zzMaw-Items.lua:4523-4533, audit OVR1-2-1); other level-7 requests are plain level 6.
        ItemGenerationRequest levelSix = request;
        levelSix.rareItemsOnly = false;
        levelSix.treasureLevel = 6;
        levelSix.boss = request.boss || request.mode == ItemGenerationMode::ChestLoot;
        return generateRandomInventoryItem(
            itemTable, standardItemEnchantTable, specialItemEnchantTable, levelSix, pParty, rng, callerFilter);
    }

    if (request.rareItemsOnly)
    {
        if (!shouldTryGenerateRareItem(request))
        {
            return std::nullopt;
        }

        const std::optional<uint32_t> rareItemId = chooseRandomRareItem(itemTable, pParty, rng, filter);

        if (!rareItemId)
        {
            return std::nullopt;
        }

        InventoryItem item = makeInventoryItem(*rareItemId, itemTable, request.mode);

        if (pParty != nullptr)
        {
            pParty->markArtifactItemFound(*rareItemId);
        }

        return item;
    }

    // A world whose artifacts come only from level-7 chest slots (world.yml chestArtifactsOnly) skips the level-6 roll.
    if (!itemTable.chestArtifactsOnly(request.worldId)
        && gameRulesFor(pParty).items.rollsRareItem(request, pParty, rng))
    {
        const std::optional<uint32_t> rareItemId = chooseRandomRareItem(itemTable, pParty, rng, filter);

        if (rareItemId)
        {
            InventoryItem item = makeInventoryItem(*rareItemId, itemTable, request.mode);

            if (pParty != nullptr)
            {
                pParty->markArtifactItemFound(*rareItemId);
            }

            return item;
        }
    }

    const std::optional<uint32_t> itemId = pWorldLoot != nullptr
        ? chooseWorldLootItem(itemTable, *pWorldLoot, request.treasureLevel, rng, filter)
        : chooseRandomBaseItem(itemTable, request.treasureLevel, rng, filter);

    if (!itemId)
    {
        return std::nullopt;
    }

    InventoryItem item = makeInventoryItem(*itemId, itemTable, request.mode);
    const ItemDefinition *pItemDefinition = itemTable.get(*itemId);

    if (pItemDefinition != nullptr && pItemDefinition->equipStat == "WeaponW")
    {
        initializeWandCharges(item, *pItemDefinition, std::uniform_int_distribution<int>(0, 5)(rng));
    }

    assignTreasurePotionPower(item, itemTable, request.treasureLevel, rng);

    if (pItemDefinition == nullptr || ItemRuntime::isRareItem(*pItemDefinition))
    {
        return item;
    }

    if (!ItemEnchantRuntime::isEnchantable(*pItemDefinition))
    {
        gameRulesFor(pParty).items.rollPlainItem(item, *pItemDefinition, request);
        return item;
    }

    // A world with a curated enchantment pool (loot.yml enchantments) re-rolls an enchantment outside it a few times,
    // then drops what is still outside.
    const auto standardAllowed = [&](const InventoryItem &rolled)
    {
        const StandardItemEnchantEntry *pEntry = rolled.standardEnchantId != 0
            ? standardItemEnchantTable.get(rolled.standardEnchantId) : nullptr;
        return pEntry == nullptr || pWorldLoot->standardEnchantments.contains(toLowerCopy(pEntry->suffix));
    };
    const auto specialAllowed = [&](const InventoryItem &rolled)
    {
        const SpecialItemEnchantEntry *pEntry = rolled.specialEnchantId != 0
            ? specialItemEnchantTable.get(rolled.specialEnchantId) : nullptr;
        const auto names = pWorldLoot->specialEnchantmentsByClass.find(
            pWorldLoot->classForTreasureLevel(request.treasureLevel));
        return pEntry == nullptr
            || (names != pWorldLoot->specialEnchantmentsByClass.end()
                && names->second.contains(toLowerCopy(pEntry->suffix)));
    };
    constexpr int CuratedEnchantmentRolls = 8;
    const InventoryItem plain = item;

    for (int roll = 0; roll < CuratedEnchantmentRolls; ++roll)
    {
        item = plain;
        gameRulesFor(pParty).items.rollEnchantments(
            item,
            *pItemDefinition,
            ItemRollTables{itemTable, standardItemEnchantTable, specialItemEnchantTable},
            request,
            pParty,
            rng);

        if (pWorldLoot == nullptr || !pWorldLoot->curatesEnchantments || (standardAllowed(item) && specialAllowed(item)))
        {
            return item;
        }
    }

    if (!standardAllowed(item))
    {
        item.standardEnchantId = 0;
        item.standardEnchantPower = 0;
    }

    if (!specialAllowed(item))
    {
        item.specialEnchantId = 0;
    }

    return item;
}

void ItemGenerator::assignTreasurePotionPower(
    InventoryItem &item,
    const ItemTable &itemTable,
    int treasureLevel,
    std::mt19937 &rng)
{
    if (!needsPotionPower(item, itemTable))
    {
        return;
    }

    std::uniform_int_distribution<int> d4(1, 4);
    const int roll = d4(rng) + d4(rng);
    item.standardEnchantPower = static_cast<uint16_t>(roll * std::clamp(treasureLevel, 1, 6));
}

void ItemGenerator::assignPlacedPotionPower(InventoryItem &item, const ItemTable &itemTable, std::mt19937 &rng)
{
    if (needsPotionPower(item, itemTable))
    {
        item.standardEnchantPower = static_cast<uint16_t>(std::uniform_int_distribution<int>(5, 19)(rng));
    }
}

void ItemGenerator::assignMonsterPotionPower(InventoryItem &item, const ItemTable &itemTable, std::mt19937 &rng)
{
    if (needsPotionPower(item, itemTable))
    {
        item.standardEnchantPower = static_cast<uint16_t>(2 * std::uniform_int_distribution<int>(0, 3)(rng) + 2);
    }
}

std::optional<uint32_t> ItemGenerator::chooseRandomBaseItem(
    const ItemTable &itemTable,
    int treasureLevel,
    std::mt19937 &rng,
    const std::function<bool(const ItemDefinition &)> &filter)
{
    const int clampedTreasureLevel = std::clamp(treasureLevel, 1, 6);
    const size_t weightIndex = static_cast<size_t>(clampedTreasureLevel - 1);
    std::vector<uint32_t> itemIds;
    std::vector<int> weights;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId == 0 || entry.hasContentFlag("NoRandom")
            || weightIndex >= entry.randomTreasureWeights.size())
        {
            continue;
        }

        if (ItemRuntime::isRareItem(entry))
        {
            continue;
        }

        if (filter && !filter(entry))
        {
            continue;
        }

        const int weight = std::max(0, entry.randomTreasureWeights[weightIndex]);

        if (weight <= 0)
        {
            continue;
        }

        itemIds.push_back(entry.itemId);
        weights.push_back(weight);
    }

    if (itemIds.empty())
    {
        return std::nullopt;
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    const size_t index = distribution(rng);
    return index < itemIds.size() ? std::optional<uint32_t>(itemIds[index]) : std::nullopt;
}
}
