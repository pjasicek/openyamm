#include "game/gameplay/HouseServiceRuntime.h"
#include "engine/Localization.h"

#include "game/gameplay/GameplayWorldItemPolicy.h"

#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/StealingRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/party/Party.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <random>
#include <sstream>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr int ShopTheftBanDays = 336;
constexpr int ShopTheftBanMinutesPerDay = 24 * 60;

std::string shopBanUntilVar(uint32_t houseId)
{
    return "MMerge.ShopBanUntil." + std::to_string(houseId);
}

constexpr float MinutesPerDay = 24.0f * 60.0f;
constexpr uint32_t ItemTypeAny = 0;
constexpr uint32_t ItemTypeWeapon = 1;
constexpr uint32_t ItemTypeWeapon2H = 2;
constexpr uint32_t ItemTypeMissile = 3;
constexpr uint32_t ItemTypeArmor = 4;
constexpr uint32_t ItemTypeShield = 5;
constexpr uint32_t ItemTypeHelm = 6;
constexpr uint32_t ItemTypeBelt = 7;
constexpr uint32_t ItemTypeCloak = 8;
constexpr uint32_t ItemTypeGauntlets = 9;
constexpr uint32_t ItemTypeBoots = 10;
constexpr uint32_t ItemTypeRing = 11;
constexpr uint32_t ItemTypeAmulet = 12;
constexpr uint32_t ItemTypeWand = 13;
constexpr uint32_t ItemTypeReagent = 14;
constexpr uint32_t ItemTypePotion = 15;
constexpr uint32_t ItemTypeScroll = 16;
constexpr uint32_t ItemTypeBook = 17;
constexpr uint32_t ItemTypeWeaponAny = 20;
constexpr uint32_t ItemTypeArmorAny = 21;
constexpr uint32_t ItemTypeMisc = 22;
constexpr uint32_t ItemTypeSword = 23;
constexpr uint32_t ItemTypeDagger = 24;
constexpr uint32_t ItemTypeAxe = 25;
constexpr uint32_t ItemTypeSpear = 26;
constexpr uint32_t ItemTypeBow = 27;
constexpr uint32_t ItemTypeMace = 28;
constexpr uint32_t ItemTypeClub = 29;
constexpr uint32_t ItemTypeStaff = 30;
constexpr uint32_t ItemTypeLeather = 31;
constexpr uint32_t ItemTypeChain = 32;
constexpr uint32_t ItemTypePlate = 33;
constexpr uint32_t ItemTypeShieldAny = 34;
constexpr uint32_t ItemTypeHelmAny = 35;
constexpr uint32_t ItemTypeBeltAny = 36;
constexpr uint32_t ItemTypeCloakAny = 37;
constexpr uint32_t ItemTypeGauntletsAny = 38;
constexpr uint32_t ItemTypeBootsAny = 39;
constexpr uint32_t ItemTypeRingAny = 40;
constexpr uint32_t ItemTypeAmuletAny = 41;
constexpr uint32_t ItemTypeWandAny = 42;
constexpr uint32_t ItemTypeScrollAny = 43;
constexpr uint32_t ItemTypePotionAny = 44;
constexpr uint32_t ItemTypeReagentAny = 45;
constexpr uint32_t ItemTypeGems = 46;
constexpr uint32_t ItemTypeGems2 = 47;

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

bool isShopItemFamilyAllowed(const HouseEntry &houseEntry, const ItemDefinition &itemDefinition)
{
    switch (houseEntry.vendorStockProfile)
    {
        case VendorStockProfile::Weapon:
            return itemDefinition.equipStat == "Weapon"
                || itemDefinition.equipStat == "Weapon1or2"
                || itemDefinition.equipStat == "Weapon2"
                || itemDefinition.equipStat == "Missile"
                || itemDefinition.equipStat == "Bow";

        case VendorStockProfile::Armor:
            return itemDefinition.equipStat == "Armor"
                || itemDefinition.equipStat == "Shield"
                || itemDefinition.equipStat == "Helm"
                || itemDefinition.equipStat == "Belt"
                || itemDefinition.equipStat == "Cloak"
                || itemDefinition.equipStat == "Gauntlets"
                || itemDefinition.equipStat == "Boots";

        case VendorStockProfile::Spellbook:
            return itemDefinition.equipStat == "Book";

        case VendorStockProfile::Mm9Apothecary:
            return itemDefinition.equipStat == "Ring"
                || itemDefinition.equipStat == "Amulet"
                || itemDefinition.equipStat == "Belt"
                || itemDefinition.equipStat == "Mscroll"
                || itemDefinition.equipStat == "Misc";

        case VendorStockProfile::Mm9GeneralStore:
            return itemDefinition.equipStat == "Weapon"
                || itemDefinition.equipStat == "Weapon1or2"
                || itemDefinition.equipStat == "Weapon2"
                || itemDefinition.equipStat == "Missile"
                || itemDefinition.equipStat == "Bow"
                || itemDefinition.equipStat == "Ring"
                || itemDefinition.equipStat == "Amulet"
                || itemDefinition.equipStat == "Belt"
                || itemDefinition.equipStat == "Gauntlets"
                || itemDefinition.equipStat == "Mscroll"
                || itemDefinition.equipStat == "Misc";

        case VendorStockProfile::Mm9Library:
            return itemDefinition.equipStat == "LearnSkill"
                && itemDefinition.hasContentFlag("SkillLearning");

        case VendorStockProfile::None:
            break;
    }

    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        return
            itemDefinition.equipStat == "Weapon"
            || itemDefinition.equipStat == "Weapon1or2"
            || itemDefinition.equipStat == "Weapon2"
            || itemDefinition.equipStat == "Missile"
            || itemDefinition.equipStat == "Bow";
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
        return (itemDefinition.skillGroup == "Misc" && itemDefinition.equipStat != "Mscroll")
            || itemDefinition.equipStat == "Book";
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return itemDefinition.equipStat == "Reagent"
            || itemDefinition.equipStat == "Herb"
            || itemDefinition.equipStat == "Bottle";
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

bool isWeaponItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Weapon"
        || itemDefinition.equipStat == "Weapon1or2"
        || itemDefinition.equipStat == "Weapon2"
        || itemDefinition.equipStat == "Missile"
        || itemDefinition.equipStat == "Bow";
}

bool itemSkillGroupIs(const ItemDefinition &itemDefinition, const char *pSkillGroup)
{
    return itemDefinition.skillGroup == pSkillGroup;
}

bool itemMatchesHouseRuleType(const ItemDefinition &itemDefinition, uint32_t itemType)
{
    switch (itemType)
    {
        case ItemTypeAny:
            return true;

        case ItemTypeWeapon:
        case ItemTypeWeaponAny:
            return isWeaponItem(itemDefinition);

        case ItemTypeWeapon2H:
            return itemDefinition.equipStat == "Weapon2" || itemDefinition.equipStat == "Weapon1or2";

        case ItemTypeMissile:
            return itemDefinition.equipStat == "Missile" || itemDefinition.equipStat == "Bow";

        case ItemTypeArmor:
        case ItemTypeArmorAny:
            return itemDefinition.equipStat == "Armor";

        case ItemTypeShield:
        case ItemTypeShieldAny:
            return itemDefinition.equipStat == "Shield";

        case ItemTypeHelm:
        case ItemTypeHelmAny:
            return itemDefinition.equipStat == "Helm";

        case ItemTypeBelt:
        case ItemTypeBeltAny:
            return itemDefinition.equipStat == "Belt";

        case ItemTypeCloak:
        case ItemTypeCloakAny:
            return itemDefinition.equipStat == "Cloak";

        case ItemTypeGauntlets:
        case ItemTypeGauntletsAny:
            return itemDefinition.equipStat == "Gauntlets";

        case ItemTypeBoots:
        case ItemTypeBootsAny:
            return itemDefinition.equipStat == "Boots";

        case ItemTypeRing:
        case ItemTypeRingAny:
            return itemDefinition.equipStat == "Ring";

        case ItemTypeAmulet:
        case ItemTypeAmuletAny:
            return itemDefinition.equipStat == "Amulet";

        case ItemTypeWand:
        case ItemTypeWandAny:
            return itemDefinition.equipStat == "WeaponW";

        case ItemTypeReagent:
        case ItemTypeReagentAny:
            return itemDefinition.equipStat == "Reagent" || itemDefinition.equipStat == "Herb";

        case ItemTypePotion:
        case ItemTypePotionAny:
            return itemDefinition.equipStat == "Bottle";

        case ItemTypeScroll:
        case ItemTypeScrollAny:
            return itemDefinition.equipStat == "Sscroll";

        case ItemTypeBook:
            return itemDefinition.equipStat == "Book";

        case ItemTypeMisc:
            return itemDefinition.skillGroup == "Misc";

        case ItemTypeSword:
            return itemSkillGroupIs(itemDefinition, "Sword");

        case ItemTypeDagger:
            return itemSkillGroupIs(itemDefinition, "Dagger");

        case ItemTypeAxe:
            return itemSkillGroupIs(itemDefinition, "Axe");

        case ItemTypeSpear:
            return itemSkillGroupIs(itemDefinition, "Spear");

        case ItemTypeBow:
            return itemSkillGroupIs(itemDefinition, "Bow") || itemDefinition.equipStat == "Missile";

        case ItemTypeMace:
            return itemSkillGroupIs(itemDefinition, "Mace");

        case ItemTypeClub:
            return itemSkillGroupIs(itemDefinition, "Club");

        case ItemTypeStaff:
            return itemSkillGroupIs(itemDefinition, "Staff");

        case ItemTypeLeather:
            return itemSkillGroupIs(itemDefinition, "Leather");

        case ItemTypeChain:
            return itemSkillGroupIs(itemDefinition, "Chain");

        case ItemTypePlate:
            return itemSkillGroupIs(itemDefinition, "Plate");

        case ItemTypeGems:
        case ItemTypeGems2:
            return itemDefinition.equipStat == "Gem";

        default:
            return false;
    }
}

bool itemMatchesHouseRuleTypes(const ItemDefinition &itemDefinition, const std::vector<uint32_t> &itemTypes)
{
    if (itemTypes.empty())
    {
        return false;
    }

    return std::any_of(
        itemTypes.begin(),
        itemTypes.end(),
        [&itemDefinition](uint32_t itemType)
        {
            return itemMatchesHouseRuleType(itemDefinition, itemType);
        });
}

constexpr uint32_t SpellsPerSchool = 11;
constexpr uint32_t MagicSchoolCount = 9;

// Schools are numbered in spell id order: Fire, Air, Water, Earth, Spirit, Mind, Body, Light, Dark.
std::vector<uint32_t> guildMagicSchools(const HouseEntry &houseEntry)
{
    constexpr std::array<const char *, MagicSchoolCount> SingleSchoolGuildTypes = {
        "Fire Guild",
        "Air Guild",
        "Water Guild",
        "Earth Guild",
        "Spirit Guild",
        "Mind Guild",
        "Body Guild",
        "Light Guild",
        "Dark Guild",
    };

    for (uint32_t school = 0; school < MagicSchoolCount; ++school)
    {
        if (isHouseType(houseEntry, SingleSchoolGuildTypes[school]))
        {
            return {school};
        }
    }

    if (isHouseType(houseEntry, "Elemental Guild"))
    {
        return {0, 1, 2, 3};
    }

    if (isHouseType(houseEntry, "Self Guild"))
    {
        return {4, 5, 6};
    }

    if (isHouseType(houseEntry, "Spell Shop"))
    {
        return {0, 1, 2, 3, 4, 5, 6, 7, 8};
    }

    return {};
}

int stockRuleTreasureTier(const HouseEntry::StockRule &rule)
{
    return std::clamp(rule.quality, 0, 6);
}

int stockRuleSecondaryTreasureTier(const HouseEntry::StockRule &rule)
{
    if (rule.secondaryQuality > 0)
    {
        return std::clamp(rule.secondaryQuality, 1, 6);
    }

    return std::clamp(rule.quality, 0, 6);
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
    Party *pParty,
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
        if (entry.itemId == 0
            || entry.name.empty()
            || entry.hasContentFlag("NoShop")
            || !entry.availableInWorld(houseEntry.worldId)
            || !predicate(entry))
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
                ItemGenerationRequest{
                    .treasureLevel = treasureLevel,
                    .mode = ItemGenerationMode::Shop,
                    .allowRareItems = false,
                    .worldId = houseEntry.worldId,
                },
                pParty,
                rng,
                [itemId](const ItemDefinition &entry)
                {
                    return entry.itemId == itemId;
                });

        results[slotIndex] = generatedItem.value_or(ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Shop));
        ItemGenerator::assignTreasurePotionPower(results[slotIndex], itemTable, treasureLevel, rng);

        if (!allowDuplicates)
        {
            usedItems.insert(itemId);
        }
    }

    return results;
}

constexpr uint32_t PotionBottleItemId = 220;
constexpr size_t AlchemistTopRowSlots = 6;

bool isRecipeScrollItem(const ItemDefinition &entry)
{
    static const std::string RecipeSuffix = " Recipe";
    return entry.equipStat == "Mscroll"
        && entry.name.size() > RecipeSuffix.size()
        && entry.name.ends_with(RecipeSuffix);
}

// The merged table carries the MM8 and MM7 recipe sets under the same names; only the first of each name is sold so
// neither set doubles the odds.
std::unordered_set<uint32_t> uniqueRecipeScrollItemIds(const ItemTable &itemTable)
{
    std::unordered_set<uint32_t> itemIds;
    std::unordered_set<std::string> names;

    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (isRecipeScrollItem(entry) && names.insert(entry.name).second)
        {
            itemIds.insert(entry.itemId);
        }
    }

    return itemIds;
}

// The native alchemist rows (OpenEnroth GUIWindow_AlchemyShop::generateShopItems): the standard stock is six empty
// bottles over random reagents, the special stock six random recipe scrolls over random potions.
std::vector<InventoryItem> generateAlchemistStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    Party *pParty,
    std::mt19937 &rng,
    size_t count,
    int tier,
    bool special)
{
    const size_t topRowCount = std::min(AlchemistTopRowSlots, count);
    std::vector<InventoryItem> results(count);

    if (special)
    {
        const std::unordered_set<uint32_t> recipeItemIds = uniqueRecipeScrollItemIds(itemTable);
        const std::vector<InventoryItem> topRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            pParty,
            tier,
            rng,
            topRowCount,
            [&recipeItemIds](const ItemDefinition &entry)
            {
                return recipeItemIds.contains(entry.itemId);
            },
            [](const ItemDefinition &)
            {
                return 1;
            },
            true);
        std::copy(topRow.begin(), topRow.end(), results.begin());
    }
    else
    {
        for (size_t index = 0; index < topRowCount; ++index)
        {
            results[index] = ItemGenerator::makeInventoryItem(PotionBottleItemId, itemTable, ItemGenerationMode::Shop);
        }
    }

    const std::vector<InventoryItem> bottomRow = generateStockItems(
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        pParty,
        tier,
        rng,
        count - topRowCount,
        [special](const ItemDefinition &entry)
        {
            return special
                ? entry.equipStat == "Bottle" && entry.itemId != PotionBottleItemId
                : entry.equipStat == "Reagent" || entry.equipStat == "Herb";
        },
        [tier, special](const ItemDefinition &entry)
        {
            return special ? itemTreasureWeightForSpecialStock(entry, tier) : itemTreasureWeightUpToTier(entry, tier);
        },
        true);
    std::copy(bottomRow.begin(), bottomRow.end(), results.begin() + static_cast<std::ptrdiff_t>(topRowCount));
    return results;
}

std::vector<InventoryItem> generateShopStandardStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    Party *pParty,
    std::mt19937 &rng,
    size_t count)
{
    const HouseEntry::StockRule &rule = houseEntry.standardStockRule;
    const int tier = stockRuleTreasureTier(rule);
    const bool allowDuplicates = isHouseType(houseEntry, "Magic Shop");

    if (tier <= 0)
    {
        return std::vector<InventoryItem>(count);
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return generateAlchemistStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            pParty,
            rng,
            count,
            tier,
            false);
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        const int bottomTier = stockRuleSecondaryTreasureTier(rule);
        const size_t topRowCount = std::min<size_t>(4, count);
        const size_t bottomRowCount = count > topRowCount ? count - topRowCount : 0;
        std::vector<InventoryItem> results(count);
        const std::vector<InventoryItem> topRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            pParty,
            tier,
            rng,
            topRowCount,
            [&rule](const ItemDefinition &entry)
            {
                return isArmorShopTopRowItem(entry) && itemMatchesHouseRuleTypes(entry, rule.itemTypes);
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
            pParty,
            tier,
            rng,
            bottomRowCount,
            [&rule](const ItemDefinition &entry)
            {
                return isArmorShopBottomRowItem(entry)
                    && itemMatchesHouseRuleTypes(entry, rule.secondaryItemTypes);
            },
            [bottomTier](const ItemDefinition &entry)
            {
                return itemTreasureWeightUpToTier(entry, bottomTier);
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
        pParty,
        tier,
        rng,
        count,
        [&houseEntry, &rule](const ItemDefinition &entry)
        {
            return !rule.itemTypes.empty()
                ? itemMatchesHouseRuleTypes(entry, rule.itemTypes)
                : isShopItemFamilyAllowed(houseEntry, entry);
        },
        [tier](const ItemDefinition &entry)
        {
            return itemTreasureWeightUpToTier(entry, tier);
        },
        allowDuplicates);
}

std::vector<InventoryItem> generateShopSpecialStock(
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    Party *pParty,
    std::mt19937 &rng,
    size_t count)
{
    const HouseEntry::StockRule &rule = houseEntry.specialStockRule;
    const int tier = stockRuleTreasureTier(rule);
    const bool allowDuplicates = isHouseType(houseEntry, "Magic Shop");

    if (tier <= 0)
    {
        return std::vector<InventoryItem>(count);
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return generateAlchemistStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            pParty,
            rng,
            count,
            tier,
            true);
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        const int bottomTier = stockRuleSecondaryTreasureTier(rule);
        const size_t topRowCount = std::min<size_t>(4, count);
        const size_t bottomRowCount = count > topRowCount ? count - topRowCount : 0;
        std::vector<InventoryItem> results(count);
        const std::vector<InventoryItem> topRow = generateStockItems(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            pParty,
            tier,
            rng,
            topRowCount,
            [&rule](const ItemDefinition &entry)
            {
                return isArmorShopTopRowItem(entry) && itemMatchesHouseRuleTypes(entry, rule.itemTypes);
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
            pParty,
            tier,
            rng,
            bottomRowCount,
            [&rule](const ItemDefinition &entry)
            {
                return isArmorShopBottomRowItem(entry)
                    && itemMatchesHouseRuleTypes(entry, rule.secondaryItemTypes);
            },
            [bottomTier](const ItemDefinition &entry)
            {
                return itemTreasureWeightForSpecialStock(entry, bottomTier);
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
        pParty,
        tier,
        rng,
        count,
        [&houseEntry, &rule](const ItemDefinition &entry)
        {
            return !rule.itemTypes.empty()
                ? itemMatchesHouseRuleTypes(entry, rule.itemTypes)
                : isShopItemFamilyAllowed(houseEntry, entry);
        },
        [tier](const ItemDefinition &entry)
        {
            return itemTreasureWeightForSpecialStock(entry, tier);
        },
        allowDuplicates);
}

std::vector<InventoryItem> generateGuildSpellbookStock(
    const ItemTable &itemTable,
    const HouseEntry &houseEntry,
    std::mt19937 &rng,
    size_t shelfSize)
{
    // Each school the guild teaches has a shelf of its own, the shelves one after another, as in MM8 (MM8-Rel.exe
    // 0x4b6e13: shelf (house - 139) x 12 + school). The guild rule is the highest spell number sold within each school.
    // Each spell is sold as the first book of the guild's world, so every continent keeps its own book design.
    const uint32_t maxSpellInSchool =
        static_cast<uint32_t>(std::clamp(houseEntry.spellbookStockRule.quality, 0, static_cast<int>(SpellsPerSchool)));
    const std::vector<uint32_t> schools = guildMagicSchools(houseEntry);
    std::vector<InventoryItem> results(shelfSize * std::max<size_t>(1, schools.size()));

    for (size_t shelf = 0; shelf < schools.size(); ++shelf)
    {
        std::vector<uint32_t> candidates;

        for (uint32_t spellInSchool = 0; spellInSchool < maxSpellInSchool; ++spellInSchool)
        {
            const std::optional<uint32_t> itemId = itemTable.spellbookItemIdForSpell(
                schools[shelf] * SpellsPerSchool + spellInSchool + 1,
                houseEntry.worldId);

            if (itemId)
            {
                candidates.push_back(*itemId);
            }
        }

        // When the shelf has room, every spell of the school is offered and spare slots repeat random spells.
        std::vector<uint32_t> selected;

        if (candidates.size() <= shelfSize)
        {
            selected = candidates;

            if (!candidates.empty())
            {
                std::uniform_int_distribution<size_t> distribution(0, candidates.size() - 1);

                while (selected.size() < shelfSize)
                {
                    selected.push_back(candidates[distribution(rng)]);
                }
            }
        }
        else
        {
            std::shuffle(candidates.begin(), candidates.end(), rng);
            selected.assign(candidates.begin(), candidates.begin() + shelfSize);
        }

        std::sort(selected.begin(), selected.end());

        for (size_t slotIndex = 0; slotIndex < selected.size(); ++slotIndex)
        {
            results[shelf * shelfSize + slotIndex] =
                ItemGenerator::makeInventoryItem(selected[slotIndex], itemTable, ItemGenerationMode::Shop);
        }
    }

    return results;
}

// A vendor's fixed stock for one restock: the page of the restock's turn. A tiered lane (a row gated by the world's
// objectives, min_objectives) shows instead every row the party has earned, in page and slot order, a page's worth at
// a time, each restock the next (wrapping; a short list repeats).
std::vector<InventoryItem> deterministicStockItems(
    const ItemTable &itemTable,
    const std::vector<HouseEntry::DeterministicStockPage> &pages,
    uint32_t refreshSequence,
    size_t objectivesDone)
{
    if (pages.empty())
    {
        return {};
    }

    const size_t pageOrdinal = refreshSequence > 0 ? static_cast<size_t>(refreshSequence - 1) : 0;
    size_t pageSize = 0;
    bool tiered = false;
    std::vector<const HouseEntry::DeterministicStockItem *> earned;

    for (const HouseEntry::DeterministicStockPage &page : pages)
    {
        pageSize = std::max(pageSize, page.items.size());

        for (const HouseEntry::DeterministicStockItem &stockItem : page.items)
        {
            tiered = tiered || stockItem.minObjectives > 0;

            if (stockItem.itemId != 0 && stockItem.minObjectives <= objectivesDone)
            {
                earned.push_back(&stockItem);
            }
        }
    }

    std::vector<const HouseEntry::DeterministicStockItem *> shown;

    if (tiered)
    {
        for (size_t slot = 0; slot < pageSize && !earned.empty(); ++slot)
        {
            shown.push_back(earned[(pageOrdinal * pageSize + slot) % earned.size()]);
        }
    }
    else
    {
        for (const HouseEntry::DeterministicStockItem &stockItem : pages[pageOrdinal % pages.size()].items)
        {
            shown.push_back(&stockItem);
        }
    }

    std::vector<InventoryItem> result;
    result.reserve(shown.size());
    for (const HouseEntry::DeterministicStockItem *pStockItem : shown)
    {
        InventoryItem item = ItemGenerator::makeInventoryItem(
            pStockItem->itemId,
            itemTable,
            ItemGenerationMode::Shop);
        item.quantity = pStockItem->quantity;
        item.identified = pStockItem->identified;
        item.standardEnchantId = pStockItem->standardEnchantId;
        item.standardEnchantPower = pStockItem->standardEnchantPower;
        item.specialEnchantId = pStockItem->specialEnchantId;
        result.push_back(item);
    }
    return result;
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
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        state.generationVersion = houseEntry.deterministicStockGenerationVersion;
        state.standardStock = deterministicStockItems(
            itemTable,
            houseEntry.deterministicStandardStockPages,
            state.refreshSequence,
            party.objectivesDone());
        state.specialStock = deterministicStockItems(
            itemTable,
            houseEntry.deterministicSpecialStockPages,
            state.refreshSequence,
            party.objectivesDone());
        state.spellbookStock.clear();
        return state;
    }

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
            &party,
            rng,
            standardCount);
    state.specialStock =
        generateShopSpecialStock(
            itemTable,
            standardItemEnchantTable,
            specialItemEnchantTable,
            houseEntry,
            &party,
            rng,
            specialCount);
    state.spellbookStock =
        generateGuildSpellbookStock(
            itemTable,
            houseEntry,
            rng,
            spellbookCount);
    const ItemRules &itemRules = gameRulesFor(&party).items;
    itemRules.adjustShopStock(state.standardStock, houseEntry, party, itemTable, rng);
    itemRules.adjustShopStock(state.specialStock, houseEntry, party, itemTable, rng);
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

    return Engine::tr("Unknown item");
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

const Character *partyMerchantMember(const Party &party)
{
    if (const Character *pRulesMerchant = PriceCalculator::rulesMerchantMember(party))
    {
        return pRulesMerchant;
    }

    const Character *pMerchant = party.bestPartyWideUtilitySkillMember("Merchant");
    return pMerchant != nullptr ? pMerchant : party.activeMember();
}

std::string merchantProfessionName(const HouseEntry &houseEntry)
{
    if (isHouseType(houseEntry, "Weapon Shop"))
    {
        return Engine::tr("weaponsmith");
    }

    if (isHouseType(houseEntry, "Armor Shop"))
    {
        return Engine::tr("armorer");
    }

    if (isHouseType(houseEntry, "Magic Shop"))
    {
        return Engine::tr("scholar");
    }

    if (isHouseType(houseEntry, "Alchemist"))
    {
        return Engine::tr("alchemist");
    }

    return Engine::tr("merchant");
}

std::string buildSellPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const ItemDefinition &itemDefinition,
    const InventoryItem &item,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int effectiveReputation)
{
    const std::string itemName = itemDisplayName(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable);

    if (itemDefinition.value <= 0)
    {
        return Engine::tr("Sorry, I'm not interested in that item.");
    }

    const int actualPrice = PriceCalculator::itemSellingPrice(
        pActiveMember,
        item,
        itemDefinition,
        houseEntry.priceMultiplier,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable,
        effectiveReputation,
        houseEntry.resaleCapPercent);
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
        return Engine::tr("Hmph. Looks like junk to me. <yawn> I suppose I could give you oh, say, "
                          "{price} gold pieces for it.",
                          {{"price", actualPrice}});
    }

    if (actualPrice == realValue * std::max(1u, item.quantity))
    {
        return Engine::tr("Normally, I do my best to buy a {item} for {listed} gold. "
                          "But I can see you know it's worth {price}. Agreed?",
                          {{"item", itemName}, {"listed", listedPrice}, {"price", actualPrice}});
    }

    return Engine::tr("Usually I try to buy something like this {item} for {listed} gold. "
                      "I'll give you {price} for it.",
                      {{"item", itemName}, {"listed", listedPrice}, {"price", actualPrice}});
}

std::string buildIdentifyPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int effectiveReputation)
{
    if (!ItemRuntime::requiresIdentification(itemDefinition) || item.identified)
    {
        return ItemRuntime::displayName(item, itemDefinition);
    }

    if (!isShopItemFamilyAllowed(houseEntry, itemDefinition))
    {
        return Engine::tr("Sorry, I can't identify a {item} because I'm a {profession}. "
                          "I don't know anything about those.",
                          {{"item", itemDisplayName(item, itemDefinition)},
                           {"profession", merchantProfessionName(houseEntry)}});
    }

    const int actualPrice = PriceCalculator::itemIdentificationPrice(
        pActiveMember,
        item,
        itemDefinition,
        boundGameRules().items.shopServiceMultiplier(itemDefinition, true, houseEntry.priceMultiplier),
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable,
        effectiveReputation);
    return Engine::tr("I'll tell you what it is for {price} gold pieces.", {{"price", actualPrice}});
}

std::string buildRepairPhrase(
    const Character *pActiveMember,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable,
    int effectiveReputation)
{
    const std::string itemName =
        itemDisplayName(item, itemDefinition, pStandardItemEnchantTable, pSpecialItemEnchantTable);

    if (!isShopItemFamilyAllowed(houseEntry, itemDefinition))
    {
        return Engine::tr("Sorry, I have no idea how to fix a {item}.", {{"item", itemName}});
    }

    if (!item.broken)
    {
        return {};
    }

    const int actualPrice = PriceCalculator::itemRepairPrice(
        pActiveMember,
        item,
        itemDefinition,
        boundGameRules().items.shopServiceMultiplier(itemDefinition, false, houseEntry.priceMultiplier),
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable,
        effectiveReputation);
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
        return Engine::tr("This {item} is nearly beyond repair. It will take a superhuman effort to fix it! "
                          "I'll have to charge {price} gold.",
                          {{"item", itemName}, {"price", actualPrice}});
    }

    if (actualPrice == realValue)
    {
        return Engine::tr("Hmmm. Nothing a little glue and polish won't fix, I warrant. My policy is to ask for "
                          "{listed} gold, but I can go as low as {price}.",
                          {{"listed", listedPrice}, {"price", actualPrice}});
    }

    return Engine::tr("This {item} is in bad shape, but it can be fixed. I usually want "
                      "{listed} gold, but for you I will charge a mere {price}.",
                      {{"item", itemName}, {"listed", listedPrice}, {"price", actualPrice}});
}
}

std::vector<uint32_t> HouseServiceRuntime::spellbookShelfSchools(const HouseEntry &houseEntry)
{
    return guildMagicSchools(houseEntry);
}

bool HouseServiceRuntime::supportsGeneratedStock(const HouseEntry &houseEntry)
{
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);
    return serviceType == HouseServiceType::Shop || serviceType == HouseServiceType::Guild;
}

bool HouseServiceRuntime::supportsEquipmentSell(const HouseEntry &houseEntry)
{
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        return houseEntry.vendorCanSell;
    }
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop;
}

bool HouseServiceRuntime::supportsIdentify(const HouseEntry &houseEntry)
{
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        return houseEntry.vendorCanIdentify;
    }
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop;
}

bool HouseServiceRuntime::supportsRepair(const HouseEntry &houseEntry)
{
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        return houseEntry.vendorCanRepair;
    }
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop && !isHouseType(houseEntry, "Alchemist");
}

size_t HouseServiceRuntime::slotCountForStockMode(const HouseEntry &houseEntry, HouseStockMode mode)
{
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        if (mode == HouseStockMode::GuildSpellbooks)
        {
            return 0;
        }
        // The vendor table sizes the pages: the shelf's fixed slot count, or a Ledger shop's restock rolls.
        const std::vector<HouseEntry::DeterministicStockPage> &pages = mode == HouseStockMode::ShopSpecial
            ? houseEntry.deterministicSpecialStockPages
            : houseEntry.deterministicStandardStockPages;
        size_t slotCount = 0;
        for (const HouseEntry::DeterministicStockPage &page : pages)
        {
            slotCount = std::max(slotCount, page.items.size());
        }
        return slotCount;
    }

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
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    const int actualValue = gameRulesFor(&party).items.shopBuyValue(
        item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);
    const int price = PriceCalculator::itemBuyingPrice(
        partyMerchantMember(party),
        actualValue,
        houseEntry.priceMultiplier,
        effectiveReputation);
    return std::max(actualValue, price);
}

int HouseServiceRuntime::sellPrice(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 0;
    }

    return PriceCalculator::itemSellingPrice(
        partyMerchantMember(party),
        item,
        *pItemDefinition,
        houseEntry.priceMultiplier,
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation,
        houseEntry.resaleCapPercent);
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

    return supportsEquipmentSell(houseEntry)
        && pItemDefinition->value > 0
        && (houseEntry.vendorStockProfile == VendorStockProfile::None
            || isShopItemFamilyAllowed(houseEntry, *pItemDefinition));
}

std::string HouseServiceRuntime::buildBuyHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return Engine::tr("Unavailable");
    }

    const Character *pActiveMember = partyMerchantMember(party);
    const int actualPrice = buyPrice(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        item,
        effectiveReputation);
    const int realValue = gameRulesFor(&party).items.shopBuyValue(
        item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);
    const int listedPrice = baseBuyPrice(realValue, houseEntry.priceMultiplier);
    const std::string itemName =
        ItemRuntime::displayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);

    if (!hasMerchantSkillForPhrase(pActiveMember))
    {
        return Engine::tr("An excellent choice! This {item} is of the finest quality. "
                          "I am willing to virtually give it away for {price} gold.",
                          {{"item", itemName}, {"price", actualPrice}});
    }

    if (actualPrice == realValue)
    {
        return Engine::tr("I try to sell things like this {item} for {listed} gold. "
                          "But we both know it's really worth {price}. So that's my price.",
                          {{"item", itemName}, {"listed", listedPrice}, {"price", actualPrice}});
    }

    return Engine::tr("Ordinarily I sell things like this {item} for {listed} gold. "
                      "But you drive a hard bargain-- I'll sell it to you for {price}.",
                      {{"item", itemName}, {"listed", listedPrice}, {"price", actualPrice}});
}

std::string HouseServiceRuntime::buildSellHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return Engine::tr("Unavailable");
    }

    return buildSellPhrase(
        partyMerchantMember(party),
        houseEntry,
        *pItemDefinition,
        item,
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation);
}

std::string HouseServiceRuntime::buildIdentifyHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return Engine::tr("Unavailable");
    }

    if (!supportsIdentify(houseEntry))
    {
        return Engine::tr("Sorry, I can't identify a {item} because I'm a {profession}.",
                          {{"item", itemDisplayName(
                                        item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)},
                           {"profession", merchantProfessionName(houseEntry)}});
    }

    return buildIdentifyPhrase(
        partyMerchantMember(party),
        houseEntry,
        item,
        *pItemDefinition,
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation);
}

std::string HouseServiceRuntime::buildRepairHoverText(
    const Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    const InventoryItem &item,
    int effectiveReputation)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return Engine::tr("Unavailable");
    }

    if (!supportsRepair(houseEntry))
    {
        return Engine::tr("Sorry, I have no idea how to fix a {item}.",
                          {{"item", itemDisplayName(
                                        item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)}});
    }

    return buildRepairPhrase(
        partyMerchantMember(party),
        houseEntry,
        item,
        *pItemDefinition,
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation);
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
    std::string &statusText,
    ShopItemServiceResult *pResult,
    int effectiveReputation)
{
    statusText.clear();

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::None;
    }

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
        statusText = Engine::tr("Nothing is for sale in that slot.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const InventoryItem item = (*pStock)[slotIndex];
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("That item is unavailable.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    const int price = buyPrice(
        party,
        itemTable,
        standardItemEnchantTable,
        specialItemEnchantTable,
        houseEntry,
        item,
        effectiveReputation);

    if (party.gold() < price)
    {
        statusText = Engine::tr("Not enough gold.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NotEnoughGold;
        }

        return false;
    }

    // A purchase goes where a pickup would: a tagged bag first (alchemy reagents and bottles, MAW's crafting), OY-257.
    if (!storePickedUpItem(party, item, &itemTable))
    {
        statusText = Engine::tr("Inventory full.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::InventoryFull;
        }

        return false;
    }

    party.addGold(-price, GoldReason::Shop);
    (*pStock)[slotIndex] = {};
    statusText = Engine::tr(
        "Bought {item} for {price} gold.",
        {{"item",
          ItemRuntime::displayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)},
         {"price", price}});

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Success;
    }

    return true;
}

bool HouseServiceRuntime::tryRerollStock(
    Party &party,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    float gameMinutes,
    std::string &statusText)
{
    const std::optional<int> cost = gameRulesFor(&party).items.shopRerollCost(party, houseEntry);

    if (!cost)
    {
        return false;
    }

    if (party.gold() < *cost)
    {
        statusText = Engine::tr("Not enough gold.");
        return false;
    }

    party.addGold(-*cost, GoldReason::Guild);
    Party::HouseStockState &state = party.ensureHouseStockState(houseEntry.id);
    state.standardStock.clear();
    state.specialStock.clear();
    state.spellbookStock.clear();
    ensureHouseStockGenerated(
        party, itemTable, standardItemEnchantTable, specialItemEnchantTable, houseEntry, gameMinutes);

    for (std::vector<InventoryItem> *pStock : {&state.standardStock, &state.specialStock})
    {
        for (InventoryItem &item : *pStock)
        {
            item.identified = true;
        }
    }

    statusText = Engine::tr("New stock for {gold} gold.", {{"gold", int64_t(*cost)}});
    return true;
}

bool HouseServiceRuntime::tryStealStockItem(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    const ItemTable &itemTable,
    const StandardItemEnchantTable &standardItemEnchantTable,
    const SpecialItemEnchantTable &specialItemEnchantTable,
    const HouseEntry &houseEntry,
    float gameMinutes,
    HouseStockMode mode,
    size_t slotIndex,
    uint32_t successRoll,
    uint32_t caughtRoll,
    std::string &statusText,
    ShopItemServiceResult *pResult,
    int effectiveReputation)
{
    statusText.clear();

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::None;
    }

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
        statusText = Engine::tr("Nothing is for sale in that slot.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const InventoryItem item = (*pStock)[slotIndex];
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);
    const Character *pMember = party.activeMember();

    if (pItemDefinition == nullptr || pMember == nullptr)
    {
        statusText = Engine::tr("That item is unavailable.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    const int itemValue =
        PriceCalculator::itemValue(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable);
    StealingAttemptInput input = {};
    input.targetKind = StealingTargetKind::Shop;
    input.itemValue = itemValue;
    input.inventoryHasRoom = party.canGrantInventoryItem(item);
    input.successRoll = successRoll;
    input.caughtRoll = caughtRoll;

    const StealingAttemptResult stealResult = resolveStealingAttempt(*pMember, input);

    if (!stealResult.handled)
    {
        statusText = Engine::tr("You need Stealing skill to steal that.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    applyStealingAttemptResult(worldRuntime, &party, stealResult);

    if (stealResult.outcome == StealingOutcomeKind::NoInventoryRoom)
    {
        statusText = Engine::tr("Inventory full.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::InventoryFull;
        }

        return false;
    }

    if (stealResult.outcome == StealingOutcomeKind::Success)
    {
        if (!storePickedUpItem(party, item, &itemTable))
        {
            statusText = Engine::tr("Inventory full.");

            if (pResult != nullptr)
            {
                *pResult = ShopItemServiceResult::InventoryFull;
            }

            return false;
        }

        (*pStock)[slotIndex] = {};
        statusText = Engine::tr("Stole {item}.", {{"item",
            ItemRuntime::displayName(item, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)}});

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Stolen;
        }

        return true;
    }

    if (stealResult.caught)
    {
        statusText = Engine::tr("Caught stealing.");

        if (EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState())
        {
            pEventRuntimeState->namedGlobalVars[shopBanUntilVar(houseEntry.id)] =
                static_cast<int32_t>(
                    std::floor(worldRuntime.gameMinutes())
                    + ShopTheftBanDays * ShopTheftBanMinutesPerDay);
        }

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::TheftCaught;
        }

        (void)effectiveReputation;
        return false;
    }

    statusText = Engine::tr("You failed to steal it.");

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Failed;
    }

    return false;
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
    ShopItemServiceResult *pResult,
    int effectiveReputation)
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
        statusText = Engine::tr("No item there.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    if (!canSellItemToHouse(itemTable, houseEntry, *pItem))
    {
        statusText = Engine::tr("That item cannot be sold.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("That item is unavailable.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Unavailable;
        }

        return false;
    }

    if (const std::optional<std::string> refusal = party.rules().items.sellRefusal(party, *pItem))
    {
        statusText = *refusal;

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
        *pItem,
        effectiveReputation);
    InventoryItem removedItem = {};

    if (!party.takeItemFromMemberInventoryCell(memberIndex, pItem->gridX, pItem->gridY, removedItem))
    {
        statusText = Engine::tr("Could not take the item.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(price, GoldReason::Sold);
    party.rules().items.itemSold(party, removedItem);
    statusText = Engine::tr(
        "Sold {item} for {price} gold.",
        {{"item", itemDisplayName(removedItem, *pItemDefinition, &standardItemEnchantTable, &specialItemEnchantTable)},
         {"price", price}});

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
    ShopItemServiceResult *pResult,
    int effectiveReputation,
    const EventRuntimeState *pEventRuntimeState)
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
        statusText = Engine::tr("No item there.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("That item is unavailable.");

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

    const bool houseCanIdentify = supportsIdentify(houseEntry) && isShopItemFamilyAllowed(houseEntry, *pItemDefinition);
    const bool followerCanIdentify = pEventRuntimeState != nullptr
        && hiredNpcHasProfession(pEventRuntimeState->hiredNpcFollowers, 4);

    if (!houseCanIdentify && !followerCanIdentify)
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::WrongShop;
        }

        return false;
    }

    const int price = followerCanIdentify ? 0 : PriceCalculator::itemIdentificationPrice(
        partyMerchantMember(party),
        *pItem,
        *pItemDefinition,
        gameRulesFor(&party).items.shopServiceMultiplier(*pItemDefinition, true, houseEntry.priceMultiplier),
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation);

    if (party.gold() < price)
    {
        statusText = Engine::tr("Not enough gold.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NotEnoughGold;
        }

        return false;
    }

    std::string identifyStatus;

    if (!party.identifyMemberInventoryItem(memberIndex, gridX, gridY, identifyStatus))
    {
        statusText = identifyStatus.empty() ? Engine::tr("Identify Failed") : identifyStatus;

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(-price, GoldReason::Shop);
    statusText = Engine::tr("Done!");

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
    ShopItemServiceResult *pResult,
    int effectiveReputation,
    const EventRuntimeState *pEventRuntimeState)
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
        statusText = Engine::tr("No item there.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NoItem;
        }

        return false;
    }

    const ItemDefinition *pItemDefinition = itemTable.get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("That item is unavailable.");

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

    const bool houseCanRepair = supportsRepair(houseEntry) && isShopItemFamilyAllowed(houseEntry, *pItemDefinition);
    const bool followerCanRepair = pEventRuntimeState != nullptr
        && hiredNpcCanRepairItemKind(pEventRuntimeState->hiredNpcFollowers, pItemDefinition->equipStat);

    if (!houseCanRepair && !followerCanRepair)
    {
        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::WrongShop;
        }

        return false;
    }

    const int price = followerCanRepair ? 0 : PriceCalculator::itemRepairPrice(
        partyMerchantMember(party),
        *pItem,
        *pItemDefinition,
        gameRulesFor(&party).items.shopServiceMultiplier(*pItemDefinition, false, houseEntry.priceMultiplier),
        &standardItemEnchantTable,
        &specialItemEnchantTable,
        effectiveReputation);

    if (party.gold() < price)
    {
        statusText = Engine::tr("Not enough gold.");

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::NotEnoughGold;
        }

        return false;
    }

    std::string repairStatus;

    if (!party.repairMemberInventoryItem(memberIndex, gridX, gridY, repairStatus))
    {
        statusText = repairStatus.empty() ? Engine::tr("Repair Failed") : repairStatus;

        if (pResult != nullptr)
        {
            *pResult = ShopItemServiceResult::Failed;
        }

        return false;
    }

    party.addGold(-price, GoldReason::Shop);
    statusText = Engine::tr("Good as New!");

    if (pResult != nullptr)
    {
        *pResult = ShopItemServiceResult::Success;
    }

    return true;
}
}
