#include "game/gameplay/HouseServiceRuntime.h"

#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/party/Party.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"
#include <algorithm>
#include <array>
#include <optional>
#include <random>
#include <sstream>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MinutesPerDay = 24.0f * 60.0f;

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

bool isShopItemFamilyAllowed(const HouseEntry &houseEntry, const ItemDefinition &itemDefinition)
{
    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        return
            itemDefinition.equipStat == "Weapon"
            || itemDefinition.equipStat == "Weapon1or2"
            || itemDefinition.equipStat == "Weapon2"
            || itemDefinition.equipStat == "Missile";
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        return itemDefinition.equipStat == "Armor"
            || itemDefinition.equipStat == "Shield"
            || itemDefinition.equipStat == "Helm"
            || itemDefinition.equipStat == "Belt"
            || itemDefinition.equipStat == "Cloak"
            || itemDefinition.equipStat == "Gauntlets"
            || itemDefinition.equipStat == "Boots";
    }

    if (isHouseType(houseEntry, "Magic Shop"))
    {
        return itemDefinition.equipStat == "Ring"
            || itemDefinition.equipStat == "Amulet"
            || itemDefinition.equipStat == "WeaponW"
            || itemDefinition.equipStat == "Gem";
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return itemDefinition.equipStat == "Reagent" || itemDefinition.equipStat == "Bottle";
    }

    return false;
}

bool isArmorShopBottomRowItem(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat == "Shield")
    {
        return true;
    }

    if (itemDefinition.equipStat != "Armor")
    {
        return false;
    }

    return itemDefinition.skillGroup == "Leather"
        || itemDefinition.skillGroup == "Chain"
        || itemDefinition.skillGroup == "Plate";
}

bool isArmorShopTopRowItem(const ItemDefinition &itemDefinition)
{
    return (itemDefinition.equipStat == "Helm"
            || itemDefinition.equipStat == "Belt"
            || itemDefinition.equipStat == "Cloak"
            || itemDefinition.equipStat == "Gauntlets"
            || itemDefinition.equipStat == "Boots")
        && !isArmorShopBottomRowItem(itemDefinition);
}

std::optional<uint32_t> tryParseSpellId(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat != "Book" || itemDefinition.mod1.size() < 2 || itemDefinition.mod1[0] != 'S')
    {
        return std::nullopt;
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(itemDefinition.mod1.substr(1)));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

bool isSpellbookAllowedForGuild(const HouseEntry &houseEntry, const ItemDefinition &itemDefinition)
{
    const std::optional<uint32_t> spellId = tryParseSpellId(itemDefinition);

    if (!spellId)
    {
        return false;
    }

    if (isHouseType(houseEntry, "Elemental Guild"))
    {
        return *spellId >= 1 && *spellId <= 44;
    }

    if (isHouseType(houseEntry, "Self Guild"))
    {
        return *spellId >= 45 && *spellId <= 77;
    }

    if (isHouseType(houseEntry, "Light Guild"))
    {
        return *spellId >= 78 && *spellId <= 88;
    }

    if (isHouseType(houseEntry, "Dark Guild"))
    {
        return *spellId >= 89 && *spellId <= 99;
    }

    if (isHouseType(houseEntry, "Spell Shop"))
    {
        return *spellId >= 1 && *spellId <= 99;
    }

    return false;
}

int houseTreasureTier(const HouseEntry &houseEntry)
{
    return std::clamp(houseEntry.standardStockTier, 0, 6);
}

int houseSpecialTreasureTier(const HouseEntry &houseEntry)
{
    if (houseEntry.specialStockTier > 0)
    {
        return std::clamp(houseEntry.specialStockTier, 1, 6);
    }

    return std::clamp(houseTreasureTier(houseEntry), 1, 6);
}

int itemTreasureWeightUpToTier(const ItemDefinition &entry, int tier)
{
    const int clampedTier = std::clamp(tier, 0, static_cast<int>(entry.randomTreasureWeights.size()));
    int weight = 0;

    for (int tierIndex = 0; tierIndex < clampedTier; ++tierIndex)
    {
        weight += entry.randomTreasureWeights[tierIndex];
    }

    return weight;
}

int itemTreasureWeightFromTier(const ItemDefinition &entry, int tier)
{
    const int startTier = std::clamp(tier, 1, static_cast<int>(entry.randomTreasureWeights.size())) - 1;
    int weight = 0;

    for (size_t tierIndex = static_cast<size_t>(startTier); tierIndex < entry.randomTreasureWeights.size(); ++tierIndex)
    {
        weight += entry.randomTreasureWeights[tierIndex];
    }

    return weight;
}

int itemTreasureWeightForSpecialStock(const ItemDefinition &entry, int tier)
{
    const int clampedTier = std::clamp(tier, 1, static_cast<int>(entry.randomTreasureWeights.size()));
    const int directWeight = entry.randomTreasureWeights[static_cast<size_t>(clampedTier - 1)];

    if (directWeight > 0)
    {
        return directWeight * 4;
    }

    if (clampedTier > 1)
    {
        return entry.randomTreasureWeights[static_cast<size_t>(clampedTier - 2)];
    }

    return 0;
}

int spellbookFallbackTreasureTier(const ItemDefinition &entry)
{
    if (entry.equipStat != "Book")
    {
        return 0;
    }

    if (entry.value > 3000)
    {
        return 4;
    }

    if (entry.value > 1000)
    {
        return 3;
    }

    if (entry.value > 400)
    {
        return 2;
    }

    return 1;
}

std::mt19937 createStockRng(const Party &party, const HouseEntry &houseEntry, const Party::HouseStockState &state)
{
    const uint32_t houseSeed = houseEntry.id != 0 ? houseEntry.id : 1;
    const uint32_t mixedSeed =
        houseSeed * 1103515245u
        + state.refreshSequence * 12345u
        + party.houseStockSeed() * 2654435761u
        + 0x4f1bbcdc;
    return std::mt19937(mixedSeed);
}

template <typename Predicate, typename WeightFunc>
std::vector<InventoryItem> generateStockItems(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    int treasureLevel,
    std::mt19937 &rng,
    size_t count,
    Predicate predicate,
    WeightFunc weightFunc,
    bool allowDuplicates = false)
{
    struct Candidate
    {
        uint32_t itemId = 0;
        int weight = 0;
    };

    std::vector<Candidate> candidates;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId == 0 || entry.name.empty() || !predicate(entry))
        {
            continue;
        }

        const int weight = weightFunc(entry);

        if (weight > 0)
        {
            candidates.push_back({entry.itemId, weight});
        }
    }

    std::vector<InventoryItem> results(count);

    if (candidates.empty())
    {
        return results;
    }

    std::unordered_set<uint32_t> usedItems;

    for (size_t slotIndex = 0; slotIndex < count; ++slotIndex)
    {
        std::vector<int> weights;
        weights.reserve(candidates.size());

        for (const Candidate &candidate : candidates)
        {
            const int slotWeight = (!allowDuplicates && usedItems.contains(candidate.itemId)) ? 0 : candidate.weight;
            weights.push_back(slotWeight);
        }

        std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
        const size_t candidateIndex = distribution(rng);

        if (candidateIndex >= candidates.size() || weights[candidateIndex] <= 0)
        {
            break;
        }

        const uint32_t itemId = candidates[candidateIndex].itemId;
        const std::optional<InventoryItem> generatedItem =
            ItemGenerator::generateRandomInventoryItem(
                itemTable,
                standardItemEnchantTable,
                specialItemEnchantTable,
                ItemGenerationRequest{treasureLevel, ItemGenerationMode::Shop, false},
                nullptr,
                rng,
                [itemId](const ItemDefinition &entry)
                {
                    return entry.itemId == itemId;
                });

        results[slotIndex] = generatedItem.value_or(ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Shop));

        if (!allowDuplicates)
        {
            usedItems.insert(itemId);
        }
    }

    return results;
}

std::vector<InventoryItem> generateShopStandardStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    std::mt19937 &rng,
    size_t count)
{
    const int tier = houseTreasureTier(houseEntry);
    const bool allowDuplicates = isHouseType(houseEntry, "Magic Shop") || isHouseType(houseEntry, "Alchemist");

    if (tier <= 0)
    {
        return std::vector<InventoryItem>(count);
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        const size_t topRowCount = std::min<size_t>(4, count);
        const size_t bottomRowCount = count > topRowCount ? count - topRowCount : 0;
        std::vector<InventoryItem> results(count);
        const std::vector<InventoryItem> topRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            tier,
            rng,
            topRowCount,
            [](const ItemDefinition &entry)
            {
                return isArmorShopTopRowItem(entry);
            },
            [tier](const ItemDefinition &entry)
            {
                return itemTreasureWeightUpToTier(entry, tier);
            });
        const std::vector<InventoryItem> bottomRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            tier,
            rng,
            bottomRowCount,
            [](const ItemDefinition &entry)
            {
                return isArmorShopBottomRowItem(entry);
            },
            [tier](const ItemDefinition &entry)
            {
                return itemTreasureWeightUpToTier(entry, tier);
            });

        for (size_t index = 0; index < topRow.size() && index < results.size(); ++index)
        {
            results[index] = topRow[index];
        }

        for (size_t index = 0; index < bottomRow.size() && topRowCount + index < results.size(); ++index)
        {
            results[topRowCount + index] = bottomRow[index];
        }

        return results;
    }

    return generateStockItems(
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        tier,
        rng,
        count,
        [&houseEntry](const ItemDefinition &entry)
        {
            return isShopItemFamilyAllowed(houseEntry, entry);
        },
        [tier](const ItemDefinition &entry)
        {
            const int weight = itemTreasureWeightUpToTier(entry, tier);

            if (weight > 0)
            {
                return weight;
            }

            const int spellbookTier = spellbookFallbackTreasureTier(entry);
            return spellbookTier > 0 && spellbookTier <= tier ? 1 : 0;
        },
        allowDuplicates);
}

std::vector<InventoryItem> generateShopSpecialStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    std::mt19937 &rng,
    size_t count)
{
    const int tier = houseSpecialTreasureTier(houseEntry);
    const bool allowDuplicates = isHouseType(houseEntry, "Magic Shop") || isHouseType(houseEntry, "Alchemist");

    if (tier <= 0)
    {
        return std::vector<InventoryItem>(count);
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        const size_t topRowCount = std::min<size_t>(4, count);
        const size_t bottomRowCount = count > topRowCount ? count - topRowCount : 0;
        std::vector<InventoryItem> results(count);
        const std::vector<InventoryItem> topRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            tier,
            rng,
            topRowCount,
            [](const ItemDefinition &entry)
            {
                return isArmorShopTopRowItem(entry);
            },
            [tier](const ItemDefinition &entry)
            {
                return itemTreasureWeightForSpecialStock(entry, tier);
            });
        const std::vector<InventoryItem> bottomRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            tier,
            rng,
            bottomRowCount,
            [](const ItemDefinition &entry)
            {
                return isArmorShopBottomRowItem(entry);
            },
            [tier](const ItemDefinition &entry)
            {
                return itemTreasureWeightForSpecialStock(entry, tier);
            });

        for (size_t index = 0; index < topRow.size() && index < results.size(); ++index)
        {
            results[index] = topRow[index];
        }

        for (size_t index = 0; index < bottomRow.size() && topRowCount + index < results.size(); ++index)
        {
            results[topRowCount + index] = bottomRow[index];
        }

        return results;
    }

    return generateStockItems(
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        tier,
        rng,
        count,
        [&houseEntry](const ItemDefinition &entry)
        {
            return isShopItemFamilyAllowed(houseEntry, entry);
        },
        [tier](const ItemDefinition &entry)
        {
            return itemTreasureWeightForSpecialStock(entry, tier);
        },
        allowDuplicates);
}

std::vector<InventoryItem> generateGuildSpellbookStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    std::mt19937 &rng,
    size_t count)
{
    const int tier = houseTreasureTier(houseEntry);

    if (tier <= 0)
    {
        return std::vector<InventoryItem>(count);
    }

    return generateStockItems(
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        tier,
        rng,
        count,
        [&houseEntry](const ItemDefinition &entry)
        {
            return isSpellbookAllowedForGuild(houseEntry, entry);
        },
        [tier](const ItemDefinition &entry)
        {
            const int weight = itemTreasureWeightUpToTier(entry, tier);

            if (weight > 0)
            {
                return weight;
            }

            const int spellbookTier = spellbookFallbackTreasureTier(entry);
            return spellbookTier > 0 && spellbookTier <= tier ? 1 : 0;
        });
}

Party::HouseStockState &ensureHouseStockGenerated(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    float gameMinutes)
{
    Party::HouseStockState &state = party.ensureHouseStockState(houseEntry.id);
    const float refreshMinutes = static_cast<float>(std::max(1, houseEntry.stockRefreshDays)) * MinutesPerDay;
    const bool needsRefresh =
        state.standardStock.empty()
        && state.specialStock.empty()
        && state.spellbookStock.empty();

    if (!needsRefresh && gameMinutes < state.nextRefreshGameMinutes)
    {
        return state;
    }

    state.refreshSequence += 1;
    state.nextRefreshGameMinutes = gameMinutes + refreshMinutes;
    std::mt19937 rng = createStockRng(party, houseEntry, state);
    const size_t standardCount = HouseServiceRuntime::slotCountForStockMode(houseEntry, HouseStockMode::ShopStandard);
    const size_t specialCount = HouseServiceRuntime::slotCountForStockMode(houseEntry, HouseStockMode::ShopSpecial);
    const size_t spellbookCount = HouseServiceRuntime::slotCountForStockMode(
        houseEntry,
        HouseStockMode::GuildSpellbooks);
    state.standardStock =
        generateShopStandardStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            rng,
            standardCount);
    state.specialStock =
        generateShopSpecialStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            rng,
            specialCount);
    state.spellbookStock =
        generateGuildSpellbookStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            rng,
            spellbookCount);
    return state;
}

std::vector<InventoryItem> *selectStockVector(Party::HouseStockState &state, HouseStockMode mode)
{
    switch (mode)
    {
        case HouseStockMode::ShopStandard:
            return &state.standardStock;

        case HouseStockMode::ShopSpecial:
            return &state.specialStock;

        case HouseStockMode::GuildSpellbooks:
            return &state.spellbookStock;
    }

    return &state.standardStock;
}

const std::vector<InventoryItem> *selectStockVector(const Party::HouseStockState &state, HouseStockMode mode)
{
    switch (mode)
    {
        case HouseStockMode::ShopStandard:
            return &state.standardStock;

        case HouseStockMode::ShopSpecial:
            return &state.specialStock;

        case HouseStockMode::GuildSpellbooks:
            return &state.spellbookStock;
    }

    return &state.standardStock;
}

std::string itemDisplayName(const ItemDefinition &itemDefinition)
{
    if (!itemDefinition.name.empty())
    {
        return itemDefinition.name;
    }

    if (!itemDefinition.unidentifiedName.empty())
    {
        return itemDefinition.unidentifiedName;
    }

    return "Unknown item";
}

std::string itemDisplayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr)
{
    return ItemRuntime::displayName(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable);
}

int baseBuyPrice(int realValue, float priceMultiplier)
{
    return std::max(1, static_cast<int>(std::round(static_cast<float>(std::max(1, realValue)) * priceMultiplier)));
}

bool hasMerchantSkillForPhrase(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return false;
    }

    const CharacterSkill *pMerchant = pCharacter->findSkill("Merchant");
    return pMerchant != nullptr && pMerchant->mastery != SkillMastery::None && pMerchant->level > 0;
}

std::string merchantProfessionName(const HouseEntry &houseEntry)
{
    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        return "weaponsmith";
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        return "armorer";
    }

    if (isHouseType(houseEntry, "Magic Shop"))
    {
        return "scholar";
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return "alchemist";
    }

    return "merchant";
}

std::string buildSellPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const ItemDefinition &itemDefinition,
    const InventoryItem &item,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    const std::string itemName = itemDisplayName(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable);

    if (!isShopItemFamilyAllowed(houseEntry, itemDefinition))
    {
        return "Sorry, I am a " + merchantProfessionName(houseEntry) + ". I'm not interested in such things.";
    }

    const int actualPrice = PriceCalculator::itemSellingPrice(
        pActiveMember,
        item,
        itemDefinition,
        houseEntry.priceMultiplier,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);
    const int listedPrice = std::max(1, static_cast<int>(std::round(
        static_cast<float>(std::max(
            1,
            PriceCalculator::itemValue(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable)))
        / (houseEntry.priceMultiplier + 2.0f))));
    const int realValue = std::max(
        1,
        PriceCalculator::itemValue(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable));

    if (!hasMerchantSkillForPhrase(pActiveMember))
    {
        return "Hmph. Looks like junk to me. <yawn> I suppose I could give you oh, say, "
            + std::to_string(actualPrice) + " gold pieces for it.";
    }

    if (actualPrice == realValue * std::max(1u, item.quantity))
    {
        return "Normally, I do my best to buy a " + itemName + " for " + std::to_string(listedPrice)
            + " gold. But I can see you know it's worth " + std::to_string(actualPrice) + ". Agreed?";
    }

    return "Usually I try to buy something like this " + itemName + " for " + std::to_string(listedPrice)
        + " gold. I'll give you " + std::to_string(actualPrice) + " for it.";
}

std::string buildIdentifyPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    if (!ItemRuntime::requiresIdentification(itemDefinition) || item.identified)
    {
        return ItemRuntime::displayName(item, itemDefinition);
    }

    if (!isShopItemFamilyAllowed(houseEntry, itemDefinition))
    {
        return "Sorry, I can't identify a " + itemDisplayName(item, itemDefinition)
            + " because I'm a " + merchantProfessionName(houseEntry) + ". I don't know anything about those.";
    }

    const int actualPrice = PriceCalculator::itemIdentificationPrice(
        pActiveMember,
        item,
        itemDefinition,
        houseEntry.priceMultiplier,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);
    return "I'll tell you what it is for " + std::to_string(actualPrice) + " gold pieces.";
}

std::string buildRepairPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    const std::string itemName =
        itemDisplayName(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable);

    if (!isShopItemFamilyAllowed(houseEntry, itemDefinition))
    {
        return "Sorry, I have no idea how to fix a " + itemName + ".";
    }

    if (!item.broken)
    {
        return {};
    }

    const int actualPrice = PriceCalculator::itemRepairPrice(
        pActiveMember,
        item,
        itemDefinition,
        houseEntry.priceMultiplier,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);
    const int listedPrice = std::max(
        1,
        static_cast<int>(static_cast<float>(std::max(
            1,
            PriceCalculator::itemValue(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable)))
        / (6.0f - houseEntry.priceMultiplier)));
    const int realValue = std::max(
        1,
        PriceCalculator::itemValue(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable));

    if (!hasMerchantSkillForPhrase(pActiveMember))
    {
        return "This " + itemName + " is nearly beyond repair. It will take a superhuman effort to fix it! "
            "I'll have to charge " + std::to_string(actualPrice) + " gold.";
    }

    if (actualPrice == realValue)
    {
        return "Hmmm. Nothing a little glue and polish won't fix, I warrant. My policy is to ask for "
            + std::to_string(listedPrice) + " gold, but I can go as low as " + std::to_string(actualPrice) + ".";
    }

    return "This " + itemName + " is in bad shape, but it can be fixed. I usually want "
        + std::to_string(listedPrice) + " gold, but for you I will charge a mere "
        + std::to_string(actualPrice) + ".";
}
}

bool HouseServiceRuntime::supportsGeneratedStock(const HouseEntry &houseEntry)
{
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);
    return serviceType == HouseServiceType::Shop || serviceType == HouseServiceType::Guild;
}

bool HouseServiceRuntime::supportsEquipmentSell(const HouseEntry &houseEntry)
{
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop;
}

bool HouseServiceRuntime::supportsIdentify(const HouseEntry &houseEntry)
{
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop;
}

bool HouseServiceRuntime::supportsRepair(const HouseEntry &houseEntry)
{
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop && !isHouseType(houseEntry, "Alchemist");
}

size_t HouseServiceRuntime::slotCountForStockMode(const HouseEntry &houseEntry, HouseStockMode mode)
{
    switch (mode)
    {
        case HouseStockMode::GuildSpellbooks:
            return 12;

        case HouseStockMode::ShopStandard:
        case HouseStockMode::ShopSpecial:
            if (isHouseType(houseEntry, "Weapon Shop"))
            {
                return 6;
            }

            if (isHouseType(houseEntry, "Magic Shop") || isHouseType(houseEntry, "Alchemist"))
            {
                return 12;
            }

            return 8;
    }

    return 0;
}

const std::vector<InventoryItem> &HouseServiceRuntime::ensureStock(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    float gameMinutes,
    HouseStockMode mode)
{
    Party::HouseStockState &state = ensureHouseStockGenerated(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        gameMinutes);
    return *selectStockVector(state, mode);
}

int HouseServiceRuntime::buyPrice(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    const int actualValue =
        PriceCalculator::itemValue(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);
    const int price = PriceCalculator::itemBuyingPrice(party.activeMember(), actualValue, houseEntry.priceMultiplier);
    return std::max(actualValue, price);
}

int HouseServiceRuntime::sellPrice(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    return PriceCalculator::itemSellingPrice(
        party.activeMember(),
        item,
        *pItemDefinition,
        houseEntry.priceMultiplier,
        &standardItemEnchantTable,
        &specialItemEnchantTable);
}

bool HouseServiceRuntime::canSellItemToHouse(
    const ItemTable &itemTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return false;
    }

    return isShopItemFamilyAllowed(houseEntry, *pItemDefinition);
}

std::string HouseServiceRuntime::buildBuyHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return "Unavailable";
    }

    const Character *pActiveMember = party.activeMember();
    const int actualPrice = buyPrice(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        item);
    const int realValue =
        PriceCalculator::itemValue(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);
    const int listedPrice = baseBuyPrice(realValue, houseEntry.priceMultiplier);
    const std::string itemName =
        ItemRuntime::displayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);

    if (!hasMerchantSkillForPhrase(pActiveMember))
    {
        return "An excellent choice! This " + itemName
            + " is of the finest quality. I am willing to virtually give it away for "
            + std::to_string(actualPrice) + " gold.";
    }

    if (actualPrice == realValue)
    {
        return "I try to sell things like this " + itemName + " for " + std::to_string(listedPrice)
            + " gold. But we both know it's really worth " + std::to_string(actualPrice) + ". So that's my price.";
    }

    return "Ordinarily I sell things like this " + itemName + " for " + std::to_string(listedPrice)
        + " gold. But you drive a hard bargain-- I'll sell it to you for " + std::to_string(actualPrice) + ".";
}

std::string HouseServiceRuntime::buildSellHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return "Unavailable";
    }

    return buildSellPhrase(
        party.activeMember(),
        houseEntry,
        *pItemDefinition,
        item,
        &standardItemEnchantTable,
        &specialItemEnchantTable);
}

std::string HouseServiceRuntime::buildIdentifyHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return "Unavailable";
    }

    if (!supportsIdentify(houseEntry))
    {
        return "Sorry, I can't identify a "
            + itemDisplayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)
            + " because I'm a " + merchantProfessionName(houseEntry) + ".";
    }

    return buildIdentifyPhrase(
        party.activeMember(),
        houseEntry,
        item,
        *pItemDefinition,
        &standardItemEnchantTable,
        &specialItemEnchantTable);
}

std::string HouseServiceRuntime::buildRepairHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return "Unavailable";
    }

    if (!supportsRepair(houseEntry))
    {
        return "Sorry, I have no idea how to fix a "
            + itemDisplayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable) + ".";
    }

    return buildRepairPhrase(
        party.activeMember(),
        houseEntry,
        item,
        *pItemDefinition,
        &standardItemEnchantTable,
        &specialItemEnchantTable);
}

bool HouseServiceRuntime::tryBuyStockItem(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    float gameMinutes,
    HouseStockMode mode,
    size_t slotIndex,
    std::string &statusText)
{
    statusText.clear();
    Party::HouseStockState &state = ensureHouseStockGenerated(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        gameMinutes);
    std::vector<InventoryItem> *pStock = selectStockVector(state, mode);

    if (pStock == nullptr || slotIndex >= pStock->size() || (*pStock)[slotIndex].objectDescriptionId == 0)
    {
        statusText = "Nothing is for sale in that slot.";
        return false;
    }

    const InventoryItem item = (*pStock)[slotIndex];
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "That item is unavailable.";
        return false;
    }

    const int price = buyPrice(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        item);

    if (party.gold() < price)
    {
        statusText = "Not enough gold.";
        return false;
    }

    if (!party.tryAutoPlaceItemInMemberInventory(party.activeMemberIndex(), item))
    {
        statusText = "Inventory full.";
        return false;
    }

    party.addGold(-price);
    (*pStock)[slotIndex] = {};
    statusText =
        "Bought "
        + ItemRuntime::displayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)
        + " for " + std::to_string(price) + " gold.";
    return true;
}

bool HouseServiceRuntime::trySellInventoryItem(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText,
    ShopItemServiceResult *pResult)
{
    statusText.clear();

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::None;
    }

    if (memberIndex >= party.members().size())
    {
        return false;
    }

    const Character &member = party.members()[memberIndex];
    const InventoryItem *pItem = member.inventoryItemAt(gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    if (!canSellItemToHouse(itemTable, houseEntry, *pItem))
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::WrongShop;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "That item is unavailable.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    const int price = sellPrice(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        *pItem);
    InventoryItem removedItem = {};

    if (!party.takeItemFromMemberInventoryCell(memberIndex, pItem->gridX, pItem->gridY, removedItem))
    {
        statusText = "Could not take the item.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(price);
    statusText = "Sold "
        + itemDisplayName(*pItem, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)
        + " for " + std::to_string(price) + " gold.";

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Success;
    }

    return true;
}

bool HouseServiceRuntime::tryIdentifyInventoryItem(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText,
    ShopItemServiceResult *pResult)
{
    statusText.clear();

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::None;
    }

    if (memberIndex >= party.members().size())
    {
        return false;
    }

    const Character &member = party.members()[memberIndex];
    const InventoryItem *pItem = member.inventoryItemAt(gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "That item is unavailable.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    if (!ItemRuntime::requiresIdentification(*pItemDefinition) || pItem->identified)
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::AlreadyIdentified;
        }

        return false;
    }

    if (!supportsIdentify(houseEntry) || !isShopItemFamilyAllowed(houseEntry, *pItemDefinition))
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::WrongShop;
        }

        return false;
    }

    const int price = PriceCalculator::itemIdentificationPrice(
        party.activeMember(),
        *pItem,
        *pItemDefinition,
        houseEntry.priceMultiplier,
        &standardItemEnchantTable,
        &specialItemEnchantTable);

    if (party.gold() < price)
    {
        statusText = "You don't have enough gold";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NotEnoughGold;
        }

        return false;
    }

    std::string identifyStatus;

    if (!party.identifyMemberInventoryItem(memberIndex, gridX, gridY, identifyStatus))
    {
        statusText = identifyStatus.empty() ? "Identification failed." : identifyStatus;

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(-price);
    statusText = "Done!";

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Success;
    }

    return true;
}

bool HouseServiceRuntime::tryRepairInventoryItem(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText,
    ShopItemServiceResult *pResult)
{
    statusText.clear();

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::None;
    }

    if (memberIndex >= party.members().size())
    {
        return false;
    }

    const Character &member = party.members()[memberIndex];
    const InventoryItem *pItem = member.inventoryItemAt(gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = "No item there.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "That item is unavailable.";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    if (!pItem->broken)
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NothingToRepair;
        }

        return false;
    }

    if (!supportsRepair(houseEntry) || !isShopItemFamilyAllowed(houseEntry, *pItemDefinition))
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::WrongShop;
        }

        return false;
    }

    const int price = PriceCalculator::itemRepairPrice(
        party.activeMember(),
        *pItem,
        *pItemDefinition,
        houseEntry.priceMultiplier,
        &standardItemEnchantTable,
        &specialItemEnchantTable);

    if (party.gold() < price)
    {
        statusText = "You don't have enough gold";

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NotEnoughGold;
        }

        return false;
    }

    std::string repairStatus;

    if (!party.repairMemberInventoryItem(memberIndex, gridX, gridY, repairStatus))
    {
        statusText = repairStatus.empty() ? "Repair failed." : repairStatus;

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(-price);
    statusText = "Good as New!";

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Success;
    }

    return true;
}
}
