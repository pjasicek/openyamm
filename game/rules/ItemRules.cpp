#include "game/rules/ItemRules.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/LootFilter.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
bool ItemRules::rollsRareItem(const ItemGenerationRequest &request, Party *, std::mt19937 &rng) const
{
    return request.allowRareItems
        && request.mode != ItemGenerationMode::Shop
        && std::clamp(request.treasureLevel, 1, 6) >= 6
        && std::uniform_int_distribution<int>(0, 99)(rng) < 5;
}

void ItemRules::rollPlainItem(InventoryItem &, const ItemDefinition &, const ItemGenerationRequest &) const
{
}

std::optional<std::string> ItemRules::sellRefusal(const Party &, const InventoryItem &) const
{
    return std::nullopt;
}

void ItemRules::itemSold(Party &, const InventoryItem &) const
{
}

bool ItemRules::levelSevenGivesRareItem() const
{
    return true;
}

void ItemRules::rollEnchantments(
    InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemRollTables &tables,
    const ItemGenerationRequest &request,
    Party *,
    std::mt19937 &rng) const
{
    const int clampedTreasureLevel = std::clamp(request.treasureLevel, 1, 6);
    const bool canHaveStandardEnchant = ItemEnchantRuntime::canHaveStandardEnchant(itemDefinition);
    const bool canHaveSpecialEnchant = ItemEnchantRuntime::canHaveSpecialEnchant(itemDefinition);
    const int standardChance =
        canHaveStandardEnchant ? ItemEnchantRuntime::standardEnchantChance(clampedTreasureLevel) : 0;
    const int specialChance =
        canHaveSpecialEnchant ? ItemEnchantRuntime::specialEnchantChance(itemDefinition, clampedTreasureLevel) : 0;

    if (!canHaveStandardEnchant)
    {
        if (specialChance > 0 && std::uniform_int_distribution<int>(0, 99)(rng) < specialChance)
        {
            const std::optional<uint16_t> specialEnchantId = ItemEnchantRuntime::chooseSpecialEnchantId(
                itemDefinition, tables.specialEnchants, clampedTreasureLevel, rng, request.worldId);

            if (specialEnchantId)
            {
                item.specialEnchantId = *specialEnchantId;
            }
        }

        return;
    }

    if (standardChance <= 0)
    {
        return;
    }

    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

    if (roll < standardChance)
    {
        const std::optional<uint16_t> standardEnchantId =
            ItemEnchantRuntime::chooseStandardEnchantId(itemDefinition, tables.standardEnchants, rng, request.worldId);

        if (standardEnchantId)
        {
            item.standardEnchantId = *standardEnchantId;

            if (const StandardItemEnchantEntry *pEntry = tables.standardEnchants.get(*standardEnchantId))
            {
                item.standardEnchantPower = static_cast<uint16_t>(
                    ItemEnchantRuntime::generateStandardEnchantPower(pEntry->kind, clampedTreasureLevel, rng));
            }
        }

        return;
    }

    if (roll < standardChance + specialChance)
    {
        const std::optional<uint16_t> specialEnchantId = ItemEnchantRuntime::chooseSpecialEnchantId(
            itemDefinition, tables.specialEnchants, clampedTreasureLevel, rng, request.worldId);

        if (specialEnchantId)
        {
            item.specialEnchantId = *specialEnchantId;
        }
    }
}

std::optional<ItemBaseStats> ItemRules::baseStats(const ItemDefinition &, const ItemRulesetFields &, int) const
{
    return std::nullopt;
}

void ItemRules::applyEquippedEnchantEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character &,
    Character &bonuses) const
{
    ItemEnchantRuntime::applyEquippedEnchantEffects(
        itemDefinition, runtimeState, pStandardTable, pSpecialTable, bonuses);
}

ItemWield ItemRules::wield(const Character &character, const ItemDefinition &itemDefinition) const
{
    const auto mastery = [&character](const char *pSkill)
    {
        const CharacterSkill *pSkillState = character.findSkill(pSkill);
        return pSkillState != nullptr ? pSkillState->mastery : SkillMastery::None;
    };
    const std::string skill = canonicalSkillName(itemDefinition.skillGroup);
    ItemWield wield;
    wield.twoHanded = itemDefinition.equipStat == "Weapon2";
    wield.offHand = (itemDefinition.equipStat == "Weapon" || itemDefinition.equipStat == "WeaponW")
        && ((skill == "Dagger" && mastery("Dagger") >= SkillMastery::Expert)
            || (skill == "Sword" && mastery("Sword") >= SkillMastery::Master));
    return wield;
}

int ItemRules::levelRequirement(const ItemDefinition &, const ItemRulesetFields &) const
{
    return 0;
}

int ItemRules::itemValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    int minimumValue) const
{
    return ItemEnchantRuntime::standardItemValue(item, itemDefinition, pStandardTable, pSpecialTable, minimumValue);
}

int ItemRules::shopBuyValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    return itemValue(item, itemDefinition, pStandardTable, pSpecialTable, 1);
}

std::string ItemRules::displayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    return ItemRuntime::identifiedDisplayName(item, itemDefinition, pStandardTable, pSpecialTable);
}

std::string ItemRules::enchantDescription(
    const InventoryItem &item,
    const ItemDefinition &,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character *) const
{
    return ItemEnchantRuntime::buildEnchantDescription(item, pStandardTable, pSpecialTable);
}

std::optional<std::string> ItemRules::itemDescription(const InventoryItem &, const Character *) const
{
    return std::nullopt;
}

std::optional<uint32_t> ItemRules::nameColor(const InventoryItem &) const
{
    return std::nullopt;
}

bool ItemRules::glowsItemRarity() const
{
    return false;
}

bool ItemRules::inventorySearch() const
{
    return false;
}

std::vector<ItemInspectLine> ItemRules::inspectLines(
    const InventoryItem &,
    const ItemDefinition &,
    const StandardItemEnchantTable *,
    const SpecialItemEnchantTable *,
    const Character *) const
{
    return {};
}

std::optional<int> ItemRules::merchantValue(const Character &) const
{
    return std::nullopt;
}

std::optional<int> ItemRules::shopRerollCost(const Party &, const HouseEntry &) const
{
    return std::nullopt;
}

bool ItemRules::rollsFixedShopStock() const
{
    return false;
}

void ItemRules::adjustShopStock(
    std::vector<InventoryItem> &,
    const HouseEntry &,
    const Party &,
    const ItemTable &,
    std::mt19937 &) const
{
}

std::optional<std::string> ItemRules::useTravelItem(Party &, const InventoryItem &) const
{
    return std::nullopt;
}

const RulesetLootFilter *ItemRules::lootFilter() const
{
    return nullptr;
}

std::optional<LootFilterFacts> ItemRules::lootFilterFacts(const InventoryItem &, const ItemDefinition &) const
{
    return std::nullopt;
}

RecentLootDrops *ItemRules::recentLootDrops() const
{
    return nullptr;
}

int ItemRules::filteredLootGold(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    return itemValue(item, itemDefinition, pStandardTable, pSpecialTable, 0);
}

std::optional<uint32_t> ItemRules::chestGoldAmount(int, std::mt19937 &) const
{
    return std::nullopt;
}

uint32_t ItemRules::placedItemId(uint32_t itemId, std::mt19937 &) const
{
    return itemId;
}

std::vector<ItemInspectLine> ItemRules::comparisonLines(
    const Party &,
    size_t,
    const InventoryItem &,
    const ItemDefinition &) const
{
    return {};
}

void ItemRules::trimMercenaryItem(InventoryItem &, std::mt19937 &) const
{
}

int ItemRules::bagCount(const Party &) const
{
    return 1;
}

bool ItemRules::openSealedItem(InventoryItem &, const Character &) const
{
    return false;
}

bool ItemRules::canDropToWorld(const InventoryItem &, const ItemDefinition &definition) const
{
    return ItemRuntime::canDrop(definition);
}

std::optional<LootGathering> ItemRules::lootGathering() const
{
    return std::nullopt;
}

bool ItemRules::gathersItem(const InventoryItem &) const
{
    return false;
}

std::optional<BagTag> ItemRules::bagTag(const ItemDefinition &) const
{
    return std::nullopt;
}

std::optional<size_t> ItemRules::alchemist(const Party &) const
{
    return std::nullopt;
}

std::optional<std::string> ItemRules::pickAlchemist(Party &, size_t) const
{
    return std::nullopt;
}

std::optional<int> ItemRules::alchemySortRank(const InventoryItem &) const
{
    return std::nullopt;
}

std::optional<std::string> ItemRules::chestOpenRefusal(const Party &, int) const
{
    return std::nullopt;
}

std::optional<std::string> ItemRules::wearRefusal(const InventoryItem &) const
{
    return std::nullopt;
}

float ItemRules::shopServiceMultiplier(const ItemDefinition &, bool, float houseMultiplier) const
{
    return houseMultiplier;
}

const ItemRules &standardItemRules()
{
    static const ItemRules Rules;
    return Rules;
}
}
