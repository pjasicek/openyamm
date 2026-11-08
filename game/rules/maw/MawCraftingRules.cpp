#include "game/rules/maw/MawCraftingRules.h"
#include "engine/Localization.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemRuntime.h"
#include "game/party/SkillData.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/PotionEffectTable.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr int FirstSkillEnchant = 17;
constexpr int LastSkillEnchant = 24;
constexpr int LastResistanceEnchant = 16;
constexpr int MaxQualityPercent = 20;
constexpr int ArtifactQualityStep = 2;
constexpr int ItemPowerCap = 120;
constexpr int EnchantItemMaxPower = 500;
constexpr int SecondEnchantMaxStrength = 65535;
// The strongest special pool, MAW's SPCITEMS level D.
constexpr int StrongestSpecialPool = 6;

bool isSkillEnchant(int type)
{
    return type >= FirstSkillEnchant && type <= LastSkillEnchant;
}

bool isWeapon(const ItemDefinition &definition)
{
    return definition.equipStat == "Weapon" || definition.equipStat == "Weapon2"
        || definition.equipStat == "Weapon1or2" || definition.equipStat == "Missile";
}

bool isRing(const ItemDefinition &definition)
{
    return definition.equipStat == "Ring";
}

// A weapon the element potions coat: any weapon but a blaster (MAW: weapon skill below 7).
bool takesWeaponPotion(const ItemDefinition &definition)
{
    static constexpr std::array<const char *, 7> Skills = {"Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace"};
    const std::string skill = canonicalSkillName(definition.skillGroup);
    return isWeapon(definition) && std::find(Skills.begin(), Skills.end(), skill) != Skills.end();
}

// Pandora's Cube refines a base stat: weapons and every armour slot. Rings and amulets have none (MAW took the cube
// for nothing).
bool takesQuality(const ItemDefinition &definition)
{
    static constexpr std::array<const char *, 7> Armour = {"Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets",
        "Boots"};
    return isWeapon(definition)
        || std::find(Armour.begin(), Armour.end(), definition.equipStat) != Armour.end();
}

int qualityStep(MawRarity rarity)
{
    switch (rarity)
    {
        case MawRarity::Rare:
            return 10;
        case MawRarity::Epic:
            return 7;
        case MawRarity::Ancient:
            return 5;
        case MawRarity::Primordial:
        case MawRarity::Legendary:
            return 4;
        case MawRarity::Celestial:
            return 1;
        default:
            return 20;
    }
}

bool hasSecondEnchant(const InventoryItem &item)
{
    return item.rulesetFields.secondStandardEnchantId != 0;
}

MawRarity rarityOf(const InventoryItem &item)
{
    return MawRarity(item.rulesetFields.lootRarity);
}

// The item's own craft seed: stored after its first craft, until then derived from what the item is, so a preview
// needs no write.
uint32_t itemCraftSeed(const InventoryItem &item)
{
    if (item.rulesetFields.craftSeed != 0)
    {
        return item.rulesetFields.craftSeed;
    }

    uint64_t hash = 1469598103934665603ull;
    const auto mix = [&hash](uint64_t value)
    {
        hash ^= value;
        hash *= 1099511628211ull;
    };
    const ItemRulesetFields &fields = item.rulesetFields;
    mix(item.objectDescriptionId);
    mix(item.standardEnchantId);
    mix(item.standardEnchantPower);
    mix(item.specialEnchantId);
    mix(fields.secondStandardEnchantId);
    mix(fields.secondStandardEnchantPower);
    mix(fields.lootRarity);
    mix(fields.legendaryAffixId);
    mix(fields.itemPower);
    mix(fields.dropLevel);
    mix(fields.qualityPercent);

    if (fields.dimensionMapId != 0)
    {
        mix(fields.dimensionMapId);
        mix(fields.dimensionPower);

        for (uint8_t affix : fields.dimensionAffixes)
        {
            mix(affix);
        }
    }

    return uint32_t(hash ^ (hash >> 32)) | 1u;
}

// The craft's random stream (RANDOMS.md §7.2, domain CraftApply): the item's seed and craft count and the material.
std::mt19937 craftStream(uint64_t rootSeed, uint32_t itemSeed, uint16_t craftCount, uint32_t materialId)
{
    const uint64_t key = randomStreamKey(rootSeed, RandomDomain::CraftApply, itemSeed, craftCount, materialId);
    std::seed_seq sequence{uint32_t(key), uint32_t(key >> 32)};
    return std::mt19937(sequence);
}

int uniform(std::mt19937 &rng, int low, int high)
{
    return std::uniform_int_distribution<int>(low, high)(rng);
}

// The strength of a weapon's dice and bonus (Emerald of Power): the dice average plus Mod2, or armour's Mod1 plus
// Mod2.
double basePower(const ItemDefinition &definition)
{
    int count = 0;
    int sides = 0;
    const size_t d = definition.mod1.find_first_of("dD");

    try
    {
        if (d != std::string::npos)
        {
            count = std::stoi(definition.mod1.substr(0, d));
            sides = std::stoi(definition.mod1.substr(d + 1));
        }
        else if (!definition.mod1.empty())
        {
            count = std::stoi(definition.mod1);
        }
    }
    catch (...)
    {
        count = 0;
        sides = 0;
    }

    int bonus = 0;

    try
    {
        bonus = definition.mod2.empty() ? 0 : std::stoi(definition.mod2);
    }
    catch (...)
    {
        bonus = 0;
    }

    return isWeapon(definition) ? count * (sides + 1) / 2.0 + bonus : double(count + bonus);
}

std::string specialName(const CraftingContext &context, uint16_t specialId)
{
    const SpecialItemEnchantEntry *pEntry =
        context.pSpecialEnchantTable != nullptr ? context.pSpecialEnchantTable->get(specialId) : nullptr;
    return pEntry != nullptr ? Engine::localize(pEntry->suffix, "special-enchant")
                             : Engine::tr("a special enchantment");
}

std::string itemName(const CraftingContext &context, uint32_t itemId)
{
    const ItemDefinition *pDefinition = context.pItemTable != nullptr ? context.pItemTable->get(itemId) : nullptr;
    return pDefinition != nullptr ? Engine::localize(pDefinition->name) : Engine::tr("the item");
}

CraftResult refuse(CraftResult result, std::string reason)
{
    result.possible = false;
    result.reason = std::move(reason);
    return result;
}
}

MawRarity mawCraftedRarity(const InventoryItem &item, MawRarity droppedRarity)
{
    if (droppedRarity == MawRarity::Celestial)
    {
        return MawRarity::Celestial;
    }

    if (item.rulesetFields.legendaryAffixId != 0)
    {
        return MawRarity::Legendary;
    }

    // The drop's ancient tier, apart from the affix and Celestial status (MawItemRarity, IT:691-715).
    if (item.rulesetFields.ancientTier != 0)
    {
        return item.rulesetFields.ancientTier == 2 ? MawRarity::Primordial : MawRarity::Ancient;
    }

    const int enchantments = (item.standardEnchantId != 0 ? 1 : 0) + (hasSecondEnchant(item) ? 1 : 0)
        + (item.specialEnchantId != 0 ? 1 : 0);
    return enchantments >= 3 ? MawRarity::Epic
        : enchantments == 2  ? MawRarity::Rare
        : enchantments == 1  ? MawRarity::Uncommon
                             : MawRarity::Common;
}

MawCraftingRules::MawCraftingRules(MawRules &rules)
    : m_rules(rules)
{
}

bool MawCraftingRules::hasCrafting() const
{
    return m_rules.craftingData().gemTiers() > 0;
}

bool MawCraftingRules::isMaterial(const InventoryItem &item) const
{
    const MawCraftingData &data = m_rules.craftingData();
    return data.gemTier(item.objectDescriptionId) > 0 || data.material(item.objectDescriptionId) != nullptr
        || data.potion(item.objectDescriptionId) != nullptr;
}

bool MawCraftingRules::isExtraTarget(const InventoryItem &item) const
{
    const uint32_t mapItemId = m_rules.dimensionData().mapItemId();
    return mapItemId != 0 && item.objectDescriptionId == mapItemId && item.rulesetFields.dimensionMapId != 0;
}

std::string MawCraftingRules::materialAction(uint32_t itemId) const
{
    const MawCraftingData &data = m_rules.craftingData();
    const MawCraftMaterial *pMaterial = data.material(itemId);
    const MawCraftMaterial *pPotion = data.potion(itemId);
    const MawCraftOperation operation = data.gemTier(itemId) > 0 ? MawCraftOperation::RaiseEnchant
        : pMaterial != nullptr                                    ? pMaterial->operation
        : pPotion != nullptr                                      ? pPotion->operation
                                                                  : MawCraftOperation::None;

    switch (operation)
    {
        case MawCraftOperation::RaiseEnchant:
            return Engine::tr("Gem: raise the weaker enchantment");
        case MawCraftOperation::AddSpecial:
            return Engine::tr("Add a special enchantment");
        case MawCraftOperation::AddSecondEnchant:
            return Engine::tr("Add a second enchantment");
        case MawCraftOperation::RefineQuality:
            return Engine::tr("Refine damage or armour");
        case MawCraftOperation::DuplicateItem:
            return Engine::tr("Copy the item");
        case MawCraftOperation::UpgradeBaseType:
            return Engine::tr("Upgrade to a stronger base item");
        case MawCraftOperation::RemoveEnchant:
            return Engine::tr("Remove an enchantment");
        case MawCraftOperation::TransferLegendaryAffix:
            return Engine::tr("Move a legendary power");
        case MawCraftOperation::TransferCelestial:
            return Engine::tr("Move Celestial status");
        case MawCraftOperation::AddPotionCharges:
            return Engine::tr("Add drinks to a potion");
        case MawCraftOperation::AddItemPower:
            return Engine::tr("Raise item power");
        case MawCraftOperation::AddFirstEnchant:
            return Engine::tr("Add a first enchantment");
        case MawCraftOperation::None:
            break;
    }

    return {};
}

int MawCraftingRules::gemTier(uint32_t itemId) const
{
    return m_rules.craftingData().gemTier(itemId);
}

int MawCraftingRules::gemCombineCount() const
{
    return m_rules.craftingData().gemCombineCount();
}

uint32_t MawCraftingRules::combinedGem(uint32_t itemId) const
{
    const MawCraftingData &data = m_rules.craftingData();
    const int tier = data.gemTier(itemId);
    return tier > 0 && tier < data.gemTiers() ? data.gemItemId(tier + 1) : 0;
}

std::vector<std::string> MawCraftingRules::craftOutlook(
    const InventoryItem &target,
    const CraftingContext &context) const
{
    std::vector<std::string> lines;
    const ItemDefinition *pDefinition =
        context.pItemTable != nullptr ? context.pItemTable->get(target.objectDescriptionId) : nullptr;

    if (pDefinition == nullptr || m_rules.itemData().baseItem(target.objectDescriptionId) == nullptr)
    {
        return lines;
    }

    lines.push_back(Engine::tr("Item Bonus Power: {power}/{cap}", {{"power", int64_t(target.rulesetFields.itemPower)},
        {"cap", int64_t(std::min(context.ownerLevel / 5, ItemPowerCap))}}));

    // The strongest gem's reach on each base enchantment.
    const int topTier = m_rules.craftingData().gemTiers();
    const double slot = slotMultiplier(*pDefinition);

    if (topTier > 0 && rarityOf(target) != MawRarity::Celestial)
    {
        const auto reach = [&](int type, int power, bool skill)
        {
            lines.push_back(Engine::tr("{stat} +{power}, gems raise it to {cap}",
                {{"stat", mawEnchantStatName(context.pStandardEnchantTable, type)}, {"power", power},
                    {"cap", gemCap(topTier, slot, skill)}}));
        };

        if (target.standardEnchantId != 0)
        {
            reach(target.standardEnchantId, target.standardEnchantPower, isSkillEnchant(target.standardEnchantId));
        }

        if (hasSecondEnchant(target))
        {
            reach(target.rulesetFields.secondStandardEnchantId, target.rulesetFields.secondStandardEnchantPower, false);
        }
    }

    // What the Hourglass and the Eye of Void would add, the same step their preview shows.
    for (const MawCraftOperation operation : {MawCraftOperation::AddSecondEnchant, MawCraftOperation::AddSpecial})
    {
        uint32_t materialId = 0;

        for (const auto &[itemId, material] : m_rules.craftingData().materials())
        {
            if (material.operation == operation && (materialId == 0 || itemId < materialId))
            {
                materialId = itemId;
            }
        }

        InventoryItem material = {};
        material.objectDescriptionId = materialId;
        const CraftResult result = materialId != 0 ? craft(target, material, context) : CraftResult{};

        if (result.possible && !result.hiddenOutcome)
        {
            lines.push_back(itemName(context, materialId) + ": " + result.summary);
        }
    }

    return lines;
}

int MawCraftingRules::primordialMaxStrength() const
{
    // Exact arithmetic: MAW's ceil(100 x 1.1) is 111 in floating point, which made Doom's cap 139 (DEVIATIONS.md).
    const double enchantPower = m_rules.lootConfig().enchantPower;
    return int(mawRound(std::ceil(100 * enchantPower - 1e-9) * 25 / 20));
}

int MawCraftingRules::gemCap(int tier, double slotMultiplier, bool skillEnchant) const
{
    const MawCraftingData &data = m_rules.craftingData();
    double cap = mawRound(double(tier) / std::max(1, data.gemTiers()) * primordialMaxStrength());

    if (skillEnchant)
    {
        cap = std::ceil(std::max(std::sqrt(cap), cap / 10));
    }

    return int(std::ceil(cap * slotMultiplier - 1e-9));
}

double MawCraftingRules::slotMultiplier(const ItemDefinition &definition) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(definition.itemId);
    return pBase != nullptr ? mawEnchantSlotMultiplier(definition, *pBase) : 1;
}

std::string MawCraftingRules::levelRefusal(
    const InventoryItem &item,
    const ItemDefinition &definition,
    const CraftingContext &context) const
{
    const int required = m_rules.itemRules().levelRequirement(definition, item.rulesetFields);
    return required > context.ownerLevel
        ? Engine::tr("Needs level {level}; its owner is level {owner}",
            {{"level", required}, {"owner", context.ownerLevel}})
        : std::string();
}

CraftResult MawCraftingRules::craft(
    const InventoryItem &target,
    const InventoryItem &material,
    const CraftingContext &context) const
{
    CraftResult result;
    result.target = target;
    const MawCraftingData &data = m_rules.craftingData();
    const ItemDefinition *pDefinition =
        context.pItemTable != nullptr ? context.pItemTable->get(target.objectDescriptionId) : nullptr;
    const int tier = data.gemTier(material.objectDescriptionId);
    const MawCraftMaterial *pMaterial = data.material(material.objectDescriptionId);
    const MawCraftMaterial *pPotion = data.potion(material.objectDescriptionId);
    const MawCraftOperation operation = tier > 0 ? MawCraftOperation::RaiseEnchant
        : pMaterial != nullptr                   ? pMaterial->operation
        : pPotion != nullptr                     ? pPotion->operation
                                                 : MawCraftOperation::None;

    if (pDefinition == nullptr || operation == MawCraftOperation::None)
    {
        return refuse(result, Engine::tr("Nothing to craft"));
    }

    // Dimension maps take the Eye, the Hourglass, the Emerald and the Crafting Cube; the Endless Potion works on
    // potions; everything else on equipment.
    if (isExtraTarget(target))
    {
        result = pMaterial != nullptr ? craftDimensionMap(result, material, operation)
                                      : refuse(result, Engine::tr("Does not work on maps"));
    }
    else if (operation == MawCraftOperation::AddPotionCharges)
    {
        result = addPotionCharges(result, material, context);
    }
    else
    {
        const bool base = m_rules.itemData().baseItem(target.objectDescriptionId) != nullptr;
        const bool artifact = ItemRuntime::isArtifact(*pDefinition);
        const bool takesArtifacts = operation == MawCraftOperation::RefineQuality;

        if (!base && !(takesArtifacts && artifact))
        {
            return refuse(result,
                artifact ? Engine::tr("{item} does not work on artifacts",
                               {{"item", itemName(context, material.objectDescriptionId)}})
                         : Engine::tr("Works on weapons, armour and jewellery only"));
        }

        if (!target.identified)
        {
            return refuse(result, Engine::tr("Identify the item first"));
        }

        const uint32_t streamSeed = itemCraftSeed(target);
        std::mt19937 rng = craftStream(
            m_rules.randomRootSeed(), streamSeed, target.rulesetFields.craftCount, material.objectDescriptionId);

        switch (operation)
        {
            case MawCraftOperation::RaiseEnchant:
                result = raiseEnchant(result, *pDefinition, tier, context);
                break;
            case MawCraftOperation::AddSpecial:
                result = addSpecial(result, *pDefinition, material, context, rng);
                break;
            case MawCraftOperation::AddSecondEnchant:
                result = addSecondEnchant(result, *pDefinition, context, rng);
                break;
            case MawCraftOperation::RefineQuality:
                result = refineQuality(result, *pDefinition, context);
                break;
            case MawCraftOperation::DuplicateItem:
                result = duplicateItem(result, *pDefinition, streamSeed);
                break;
            case MawCraftOperation::UpgradeBaseType:
                result = upgradeBaseType(result, *pDefinition, context);
                break;
            case MawCraftOperation::RemoveEnchant:
                result = removeEnchant(result, *pDefinition, context);
                break;
            case MawCraftOperation::TransferLegendaryAffix:
                result = transferLegendaryAffix(result, material);
                break;
            case MawCraftOperation::TransferCelestial:
                result = transferCelestial(result, material);
                break;
            case MawCraftOperation::AddItemPower:
                result = addItemPower(result, *pDefinition, context);
                break;
            case MawCraftOperation::AddFirstEnchant:
                result = addFirstEnchant(result, *pDefinition, material, context, rng);
                break;
            default:
                return refuse(result, Engine::tr("Nothing to craft"));
        }

        if (result.possible)
        {
            // The step moves the item's stream on; its rarity follows what it has now.
            result.target.rulesetFields.craftSeed = streamSeed;
            ++result.target.rulesetFields.craftCount;

            if (base)
            {
                const MawRarity dropped = rarityOf(result.target);
                result.target.rulesetFields.lootRarity = uint8_t(mawCraftedRarity(result.target, dropped));
            }
        }
    }

    return result;
}

CraftResult MawCraftingRules::craftDimensionMap(
    CraftResult result,
    const InventoryItem &material,
    MawCraftOperation operation) const
{
    InventoryItem &item = result.target;
    MawDimensionMap map = MawDimensionMap::fromFields(item.rulesetFields);
    const MawDimensionData &data = m_rules.dimensionData();

    switch (operation)
    {
        case MawCraftOperation::AddSpecial:
        case MawCraftOperation::AddSecondEnchant:
        {
            // The next stored affix becomes active (AL:1038-1074).
            if (map.activeSlots == 0 || map.activeSlots >= 4)
            {
                return refuse(result, Engine::tr("Every affix of this map is already active"));
            }

            const uint8_t affix = map.affixes[map.activeSlots];
            ++map.activeSlots;
            result.summary = affix != 0
                ? Engine::tr("Activates: {affix}", {{"affix", data.affixLine(affix, map.power)}})
                : Engine::tr("Opens an empty slot");
            break;
        }
        case MawCraftOperation::UpgradeBaseType:
        {
            if (map.power >= 255)
            {
                return refuse(result, Engine::tr("The map's power is at its limit"));
            }

            map.power = uint8_t(std::min(map.power + 5, 255));
            result.summary = Engine::tr("Power {power}: monsters 50 levels stronger", {{"power", int64_t(map.power)}});
            break;
        }
        case MawCraftOperation::AddItemPower:
        {
            // Another cleared place of the same kind, indoors or outdoors.
            const MapStats *pMapTable = m_rules.mapTable();
            const MapStatsEntry *pCurrent = pMapTable != nullptr ? pMapTable->findById(map.mapId) : nullptr;
            // Indoor is a .blv map; MAW's overworldMaps list agrees since it dropped the Plane of Earth (54f1ef13).
            const auto indoor = [](const MapStatsEntry &entry)
            {
                return entry.fileName.size() > 4
                    && std::tolower(static_cast<unsigned char>(entry.fileName[entry.fileName.size() - 3])) == 'b';
            };
            std::vector<uint16_t> others;

            for (uint16_t mapId : m_rules.dimensionMapPool())
            {
                const MapStatsEntry *pOther = pMapTable != nullptr ? pMapTable->findById(mapId) : nullptr;

                if (pCurrent != nullptr && pOther != nullptr && mapId != map.mapId
                    && indoor(*pOther) == indoor(*pCurrent))
                {
                    others.push_back(mapId);
                }
            }

            if (others.empty())
            {
                return refuse(result, Engine::tr("You have cleared no other place of this kind"));
            }

            std::mt19937 rng = craftStream(m_rules.randomRootSeed(), itemCraftSeed(item), item.rulesetFields.craftCount,
                material.objectDescriptionId);
            map.mapId = others[size_t(uniform(rng, 0, int(others.size()) - 1))];
            const MapStatsEntry *pNew = pMapTable->findById(map.mapId);
            result.hiddenOutcome = true;
            result.summary = Engine::tr("Moves the map to another cleared place");
            result.outcome = Engine::tr("The map now opens {place}",
                {{"place", pNew != nullptr ? Engine::localize(pNew->name) : Engine::tr("another place")}});
            break;
        }
        default:
            return refuse(result, Engine::tr("Does not work on maps"));
    }

    const uint32_t streamSeed = itemCraftSeed(item);
    map.writeFields(item.rulesetFields);
    item.rulesetFields.craftSeed = streamSeed;
    ++item.rulesetFields.craftCount;
    result.possible = true;
    result.materialConsumed = true;
    return result;
}

CraftResult MawCraftingRules::raiseEnchant(
    CraftResult result,
    const ItemDefinition &definition,
    int tier,
    const CraftingContext &context) const
{
    InventoryItem &item = result.target;

    if (rarityOf(item) == MawRarity::Celestial)
    {
        return refuse(result, Engine::tr("Celestial items grow with their wearer; gems cannot raise them"));
    }

    if (const std::string refusal = levelRefusal(item, definition, context); !refusal.empty())
    {
        return refuse(result, refusal);
    }

    if (item.standardEnchantId == 0 && !hasSecondEnchant(item))
    {
        return refuse(result, Engine::tr("No enchantments to raise"));
    }

    // The enchantment furthest below its own cap rises: +3, +1 on a skill.
    const double slot = slotMultiplier(definition);
    const bool skill = isSkillEnchant(item.standardEnchantId);
    const int cap1 = gemCap(tier, slot, skill);
    const int cap2 = gemCap(tier, slot, false);
    uint16_t &strength2 = item.rulesetFields.secondStandardEnchantPower;
    const double fraction1 =
        item.standardEnchantId != 0 ? double(item.standardEnchantPower) / cap1 : std::numeric_limits<double>::max();
    const double fraction2 = hasSecondEnchant(item) ? double(strength2) / cap2 : std::numeric_limits<double>::max();

    if (fraction1 <= fraction2 && item.standardEnchantPower < cap1)
    {
        item.standardEnchantPower = uint16_t(std::min(item.standardEnchantPower + (skill ? 1 : 3), cap1));
        result.summary = Engine::tr("{stat} +{amount} (cap {cap})",
            {{"stat", mawEnchantStatName(context.pStandardEnchantTable, item.standardEnchantId)},
                {"amount", skill ? 1 : 3}, {"cap", cap1}});
    }
    else if (fraction2 <= fraction1 && strength2 < cap2 && strength2 < SecondEnchantMaxStrength)
    {
        strength2 = uint16_t(std::min({strength2 + 3, cap2, SecondEnchantMaxStrength}));
        result.summary = Engine::tr("{stat} +{amount} (cap {cap})",
            {{"stat", mawEnchantStatName(context.pStandardEnchantTable, item.rulesetFields.secondStandardEnchantId)},
                {"amount", 3}, {"cap", cap2}});
    }
    else
    {
        return refuse(result, Engine::tr("At this gem's cap; a higher tier raises it further"));
    }

    result.possible = true;
    result.materialConsumed = true;
    return result;
}

CraftResult MawCraftingRules::addSpecial(
    CraftResult result,
    const ItemDefinition &definition,
    const InventoryItem &material,
    const CraftingContext &context,
    std::mt19937 &rng) const
{
    InventoryItem &item = result.target;
    const MawCraftMaterial *pPotion = m_rules.craftingData().potion(material.objectDescriptionId);

    if (pPotion != nullptr)
    {
        const PotionDefinition *pDefinition =
            context.pPotionEffects != nullptr ? context.pPotionEffects->find(material.objectDescriptionId) : nullptr;

        if (pDefinition != nullptr && material.standardEnchantPower < pDefinition->minimumPower)
        {
            return refuse(result, Engine::tr("This potion has not enough power ({power} needed)",
                                      {{"power", pDefinition->minimumPower}}));
        }

        if (!takesWeaponPotion(definition))
        {
            return refuse(result, Engine::tr("Only weapons take this potion"));
        }
    }

    if (item.specialEnchantId != 0)
    {
        return refuse(result, Engine::tr("Already has a special enchantment"));
    }

    uint16_t specialId = 0;

    if (pPotion != nullptr && !pPotion->specialChoices.empty())
    {
        // Several choices are a gamble: the preview lists them, not the pick.
        specialId = pPotion->specialChoices[size_t(uniform(rng, 0, int(pPotion->specialChoices.size()) - 1))];
        result.hiddenOutcome = pPotion->specialChoices.size() > 1;

        std::string choices;

        for (uint16_t choice : pPotion->specialChoices)
        {
            choices += (choices.empty() ? "" : ", ") + specialName(context, choice);
        }

        result.summary += Engine::tr("Adds one at random: {choices}", {{"choices", choices}});
    }
    else if (context.pSpecialEnchantTable != nullptr)
    {
        specialId = ItemEnchantRuntime::chooseSpecialEnchantId(
            definition, *context.pSpecialEnchantTable, StrongestSpecialPool, rng)
                        .value_or(0);
    }

    if (specialId == 0)
    {
        return refuse(result, Engine::tr("This item cannot take a special enchantment"));
    }

    item.specialEnchantId = specialId;
    result.possible = true;
    result.materialConsumed = true;
    result.outcome = Engine::tr("Adds {what}", {{"what", specialName(context, specialId)}});

    if (!result.hiddenOutcome)
    {
        result.summary = result.outcome;
    }
    return result;
}

CraftResult MawCraftingRules::addSecondEnchant(
    CraftResult result,
    const ItemDefinition &definition,
    const CraftingContext &context,
    std::mt19937 &rng) const
{
    InventoryItem &item = result.target;

    if (item.standardEnchantId == 0 || item.standardEnchantPower == 0)
    {
        return refuse(result, Engine::tr("Needs a first enchantment to copy"));
    }

    if (hasSecondEnchant(item))
    {
        return refuse(result, Engine::tr("Already has a second enchantment"));
    }

    // A stat (rings: also a resistance) other than the first, near its strength: x (1 to 1.25), capped at 100 x the
    // difficulty's multiplier x the slot multiplier.
    int type = item.standardEnchantId;

    while (type == item.standardEnchantId)
    {
        type = uniform(rng, 1, isRing(definition) ? LastResistanceEnchant : 10);
    }

    static constexpr std::array<double, 10> DifficultyMultipliers = {1, 1, 1, 1, 1.05, 1.1, 1.2, 1.5, 1.5, 1.5};
    const int difficulty = std::clamp(m_rules.lootConfig().difficulty, 0, 9);
    const double cap = std::min(100 * DifficultyMultipliers[size_t(difficulty)] * slotMultiplier(definition),
        double(SecondEnchantMaxStrength));
    const double roll = std::uniform_real_distribution<double>(0.0, 1.0)(rng);
    const int strength = int(std::min(mawRound(item.standardEnchantPower * (1 + 0.25 * roll)), cap));
    item.rulesetFields.secondStandardEnchantId = uint16_t(type);
    item.rulesetFields.secondStandardEnchantPower = uint16_t(strength);
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Adds {stat} +{amount}",
        {{"stat", mawEnchantStatName(context.pStandardEnchantTable, type)}, {"amount", int64_t(strength)}});
    return result;
}

CraftResult MawCraftingRules::refineQuality(
    CraftResult result,
    const ItemDefinition &definition,
    const CraftingContext &context) const
{
    InventoryItem &item = result.target;

    if (!takesQuality(definition))
    {
        return refuse(result, Engine::tr("Only weapons and armour can be refined"));
    }

    if (const std::string refusal = levelRefusal(item, definition, context); !refusal.empty())
    {
        return refuse(result, refusal);
    }

    uint8_t &quality = item.rulesetFields.qualityPercent;

    if (quality >= MaxQualityPercent)
    {
        return refuse(result, Engine::tr("Item quality reached its limit"));
    }

    const int step = ItemRuntime::isArtifact(definition) ? ArtifactQualityStep : qualityStep(rarityOf(item));
    quality = uint8_t(std::min(quality + step, MaxQualityPercent));
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Quality {percent} %", {{"percent", int64_t(quality)}});
    return result;
}

CraftResult MawCraftingRules::duplicateItem(CraftResult result, const ItemDefinition &, uint32_t streamSeed) const
{
    // The mirror becomes a copy: identified as the original, never broken, hardened or stolen, with its own craft
    // stream (MAW's copies crafted alike and came out unidentified).
    InventoryItem copy = result.target;
    copy.broken = false;
    copy.hardened = false;
    copy.stolen = false;
    copy.rulesetFields.craftSeed = uint32_t(streamSeed * 2654435761u + 0x9e3779b9u) | 1u;
    copy.rulesetFields.craftCount = 0;
    result.materialAfter = copy;
    result.possible = true;
    result.summary = Engine::tr("Becomes a copy");
    return result;
}

CraftResult MawCraftingRules::upgradeBaseType(
    CraftResult result,
    const ItemDefinition &definition,
    const CraftingContext &context) const
{
    InventoryItem &item = result.target;
    const MawItemData &itemData = m_rules.itemData();
    const ItemDefinition *pNext = context.pItemTable->get(definition.itemId + 1);
    uint32_t upgradeId = 0;

    // The next rung of the item's family, else the weakest base item of its kind stronger than it.
    if (pNext != nullptr && itemData.baseItem(pNext->itemId) != nullptr
        && pNext->unidentifiedName == definition.unidentifiedName)
    {
        upgradeId = pNext->itemId;
    }
    else
    {
        const std::string skill = canonicalSkillName(definition.skillGroup);
        const double power = basePower(definition);
        double best = std::numeric_limits<double>::max();

        for (const ItemDefinition &candidate : context.pItemTable->entries())
        {
            if (itemData.baseItem(candidate.itemId) == nullptr || candidate.equipStat != definition.equipStat
                || canonicalSkillName(candidate.skillGroup) != skill)
            {
                continue;
            }

            const double candidatePower = basePower(candidate);

            if (candidatePower > power && candidatePower < best)
            {
                best = candidatePower;
                upgradeId = candidate.itemId;
            }
        }
    }

    if (upgradeId == 0)
    {
        return refuse(result, Engine::tr("Already the strongest of its kind"));
    }

    const ItemDefinition *pUpgrade = context.pItemTable->get(upgradeId);
    item.objectDescriptionId = upgradeId;
    item.width = pUpgrade->inventoryWidth;
    item.height = pUpgrade->inventoryHeight;
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Becomes {item}", {{"item", Engine::localize(pUpgrade->name)}});

    if (m_rules.itemRules().levelRequirement(*pUpgrade, item.rulesetFields) > context.ownerLevel)
    {
        result.confirmation = Engine::tr(
            "Its owner will be too low in level to use the {item}", {{"item", Engine::localize(pUpgrade->name)}});
    }

    return result;
}

CraftResult MawCraftingRules::removeEnchant(
    CraftResult result,
    const ItemDefinition &definition,
    const CraftingContext &context) const
{
    InventoryItem &item = result.target;
    // The enchantments present, by slot (1 and 2 the base ones, 3 the special), named as the inspect popup reads them.
    std::vector<std::pair<int, std::string>> present;

    if (item.standardEnchantId != 0)
    {
        present.push_back({1, m_rules.itemRules().enchantLine(item.standardEnchantId, item.standardEnchantPower, true,
            definition, context.pStandardEnchantTable, nullptr)});
    }

    if (hasSecondEnchant(item))
    {
        const ItemRulesetFields &fields = item.rulesetFields;
        present.push_back({2, m_rules.itemRules().enchantLine(fields.secondStandardEnchantId,
            fields.secondStandardEnchantPower, false, definition, context.pStandardEnchantTable, nullptr)});
    }

    if (item.specialEnchantId != 0)
    {
        present.push_back({3, specialName(context, item.specialEnchantId)});
    }

    if (present.empty())
    {
        return refuse(result, Engine::tr("No enchantments to remove"));
    }

    // The player picks which one goes (MAW picks at random, DEVIATIONS.md); losing the first moves the second up.
    if (present.size() > 1)
    {
        result.choicePrompt = Engine::tr("Remove which enchantment?");

        for (const auto &[slot, name] : present)
        {
            result.choices.push_back(name);
        }
    }

    result.choice = std::min(context.choice, present.size() - 1);
    const auto &[slot, removed] = present[result.choice];
    ItemRulesetFields &fields = item.rulesetFields;

    if (slot == 1)
    {
        item.standardEnchantId = fields.secondStandardEnchantId;
        item.standardEnchantPower = fields.secondStandardEnchantPower;
        fields.secondStandardEnchantId = 0;
        fields.secondStandardEnchantPower = 0;
    }
    else if (slot == 2)
    {
        fields.secondStandardEnchantId = 0;
        fields.secondStandardEnchantPower = 0;
    }
    else
    {
        item.specialEnchantId = 0;
    }

    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Removes {what}", {{"what", removed}});
    result.outcome = Engine::tr("Removed {what}", {{"what", removed}});
    result.confirmation = Engine::tr("Remove {what}?", {{"what", removed}});
    return result;
}

CraftResult MawCraftingRules::transferLegendaryAffix(CraftResult result, const InventoryItem &material) const
{
    InventoryItem &item = result.target;
    const uint16_t stored = material.rulesetFields.craftState;
    const uint16_t affix = item.rulesetFields.legendaryAffixId;

    if (stored == 0)
    {
        if (affix == 0)
        {
            return refuse(result, Engine::tr("The orb is empty: choose a legendary item to draw its power from"));
        }

        // The empty orb draws the affix out and is kept.
        InventoryItem charged = material;
        charged.rulesetFields.craftState = affix;
        item.rulesetFields.legendaryAffixId = 0;
        result.materialAfter = charged;
        result.possible = true;
        result.summary = Engine::tr("The orb takes the legendary power");
        result.confirmation = Engine::tr("Move the legendary power into the orb?");
        return result;
    }

    item.rulesetFields.legendaryAffixId = stored;
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Gains the orb's legendary power");

    if (affix != 0)
    {
        result.confirmation = Engine::tr("Replace the item's legendary power?");
    }

    return result;
}

CraftResult MawCraftingRules::transferCelestial(CraftResult result, const InventoryItem &material) const
{
    InventoryItem &item = result.target;
    const bool charged = material.rulesetFields.craftState != 0;
    const bool celestial = rarityOf(item) == MawRarity::Celestial;

    if (charged && !celestial)
    {
        item.rulesetFields.lootRarity = uint8_t(MawRarity::Celestial);
        result.possible = true;
        result.materialConsumed = true;
        result.summary = Engine::tr("Becomes Celestial");
        return result;
    }

    if (!charged && celestial)
    {
        // Losing Celestial status leaves what the item is without it: its affix, its tier or its enchantments.
        item.rulesetFields.lootRarity = uint8_t(mawCraftedRarity(item, MawRarity::Common));
        InventoryItem filled = material;
        filled.rulesetFields.craftState = 1;
        result.materialAfter = filled;
        result.possible = true;
        result.summary = Engine::tr("The orb takes the Celestial status");
        result.confirmation = Engine::tr("Move the Celestial status into the orb?");
        return result;
    }

    return refuse(result, Engine::tr(charged ? "Already Celestial" : "The orb is empty: choose a Celestial item"));
}

CraftResult MawCraftingRules::addPotionCharges(
    CraftResult result,
    const InventoryItem &material,
    const CraftingContext &context) const
{
    InventoryItem &potion = result.target;
    const MawCraftMaterial *pMaterial = m_rules.craftingData().material(material.objectDescriptionId);
    const PotionDefinition *pPotion =
        context.pPotionEffects != nullptr ? context.pPotionEffects->find(potion.objectDescriptionId) : nullptr;

    if (pMaterial == nullptr || pPotion == nullptr
        || std::find(pMaterial->targets.begin(), pMaterial->targets.end(), potion.objectDescriptionId)
            == pMaterial->targets.end())
    {
        return refuse(result, Engine::tr("Refills Protection, Meditation, Regeneration, Magic Protection, Champion's, "
                                         "Paladin's, Divine Blessing and Divine Resistance potions"));
    }

    // A full bottle (no charges) holds its potion's drinks.
    const int drinks = potion.currentCharges > 0 ? int(potion.currentCharges) : pPotion->charges;
    const int added = std::max(1, int(material.rulesetFields.craftState));
    potion.currentCharges = uint16_t(std::min(drinks + added, int(std::numeric_limits<uint16_t>::max())));
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("+{count} drinks", {{"count", added}});
    return result;
}

CraftResult MawCraftingRules::addItemPower(
    CraftResult result,
    const ItemDefinition &definition,
    const CraftingContext &context) const
{
    InventoryItem &item = result.target;

    if (rarityOf(item) == MawRarity::Celestial)
    {
        return refuse(result, Engine::tr("Celestial items grow with their wearer"));
    }

    const int cap = std::min(context.ownerLevel / 5, ItemPowerCap);

    if (item.rulesetFields.itemPower >= cap)
    {
        return refuse(
            result, Engine::tr("Item power reached the limit for its owner's level ({cap})", {{"cap", cap}}));
    }

    const int step = isWeapon(definition) || definition.equipStat == "Armor" ? 2 : 4;
    item.rulesetFields.itemPower = uint16_t(std::min(item.rulesetFields.itemPower + step, cap));
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Item power {power} (cap {cap})", {{"power", int64_t(item.rulesetFields.itemPower)},
        {"cap", int64_t(cap)}});
    return result;
}

CraftResult MawCraftingRules::addFirstEnchant(
    CraftResult result,
    const ItemDefinition &definition,
    const InventoryItem &material,
    const CraftingContext &context,
    std::mt19937 &rng) const
{
    InventoryItem &item = result.target;

    if (item.standardEnchantId != 0 || hasSecondEnchant(item) || item.specialEnchantId != 0)
    {
        return refuse(result, Engine::tr("Enchant Item works on items without enchantments"));
    }

    // A tenth are skill enchantments; rings also roll resistances. Strength: a fifth of the power (up to 500) times
    // the slot multiplier; skills much less.
    int type = 0;

    if (uniform(rng, 1, 10) == 1)
    {
        type = uniform(rng, FirstSkillEnchant, LastSkillEnchant);
    }
    else
    {
        type = uniform(rng, 1, isRing(definition) ? LastResistanceEnchant : 10);
    }

    // MAW stores the fifth in the item's whole-number strength before the slot multiplier (zzMAWPotions.lua:73-86).
    double strength = std::ceil(std::min(int(material.standardEnchantPower), EnchantItemMaxPower) / 5
        * slotMultiplier(definition) - 1e-9);

    if (isSkillEnchant(type))
    {
        strength = std::max(std::sqrt(strength), std::ceil(strength / 10));
    }

    item.standardEnchantId = uint16_t(type);
    item.standardEnchantPower = uint16_t(std::max(1, int(strength)));
    result.possible = true;
    result.materialConsumed = true;
    result.summary = Engine::tr("Adds {stat} +{amount}",
        {{"stat", mawEnchantStatName(context.pStandardEnchantTable, type)},
            {"amount", int64_t(item.standardEnchantPower)}});
    return result;
}

std::optional<std::string> MawCraftingRules::materialDescription(const InventoryItem &item) const
{
    const int tier = gemTier(item.objectDescriptionId);
    const std::string *pText = m_rules.textData().findItemKindText("gem");

    if (tier <= 0 || pText == nullptr)
    {
        return std::nullopt;
    }

    // The slot multipliers of mawEnchantSlotMultiplier.
    const MawCraftingData &data = m_rules.craftingData();
    return mawFillText(*pText, {
        {"tier", tier},
        {"max_power", gemCap(tier, 1, false)},
        {"skill_max", gemCap(tier, 1, true)},
        {"two_handed", gemCap(tier, 2, false)},
        {"body", gemCap(tier, 1.5, false)},
        {"helm", gemCap(tier, 1.25, false)},
        {"ring", gemCap(tier, 0.75, false)},
        {"drop_max_tier", data.gemDropMaxTier()},
        {"tiers", data.gemTiers()},
        {"combine", gemCombineCount()},
    });
}
}
