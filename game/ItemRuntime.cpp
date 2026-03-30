#include "game/ItemRuntime.h"

#include "game/ItemEnchantRuntime.h"
#include "game/ItemEnchantTables.h"
#include "game/ItemTable.h"
#include "game/SkillData.h"

#include <algorithm>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
int masteryMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;

        case SkillMastery::Expert:
            return 2;

        case SkillMastery::Master:
            return 3;

        case SkillMastery::Grandmaster:
            return 5;

        case SkillMastery::None:
        default:
            return 0;
    }
}

int identifyRepairSkillScore(const Character &character, const char *pSkillName)
{
    const CharacterSkill *pSkill = character.findSkill(pSkillName);
    const auto bonusIt = character.itemSkillBonuses.find(std::string(pSkillName));
    const int bonusLevel = bonusIt != character.itemSkillBonuses.end() ? bonusIt->second : 0;

    if ((pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0) && bonusLevel == 0)
    {
        return 0;
    }

    if (pSkill != nullptr && pSkill->mastery == SkillMastery::Grandmaster)
    {
        return std::numeric_limits<int>::max();
    }

    const int baseLevel = pSkill != nullptr ? static_cast<int>(pSkill->level) : 0;
    const SkillMastery mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    return (baseLevel + bonusLevel) * masteryMultiplier(mastery);
}

bool hasMeaningfulUnidentifiedName(const ItemDefinition &itemDefinition)
{
    return !itemDefinition.unidentifiedName.empty()
        && itemDefinition.unidentifiedName != "0"
        && itemDefinition.unidentifiedName != "N / A";
}

bool matchesClassOrPromotion(const std::string &characterClassName, const std::string &requiredClassName)
{
    const std::string canonicalCharacterClass = canonicalClassName(characterClassName);
    const std::string canonicalRequiredClass = canonicalClassName(requiredClassName);

    if (canonicalCharacterClass.empty() || canonicalRequiredClass.empty())
    {
        return false;
    }

    if (canonicalCharacterClass == canonicalRequiredClass)
    {
        return true;
    }

    std::vector<std::string> pendingClasses = promotionClassNames(canonicalRequiredClass);

    while (!pendingClasses.empty())
    {
        const std::string className = canonicalClassName(pendingClasses.back());
        pendingClasses.pop_back();

        if (className == canonicalCharacterClass)
        {
            return true;
        }

        const std::vector<std::string> nextPromotions = promotionClassNames(className);
        pendingClasses.insert(pendingClasses.end(), nextPromotions.begin(), nextPromotions.end());
    }

    return false;
}
}

bool ItemRuntime::requiresIdentification(const ItemDefinition &itemDefinition)
{
    return identifyRepairDifficulty(itemDefinition) > 0
        && hasMeaningfulUnidentifiedName(itemDefinition)
        && itemDefinition.unidentifiedName != itemDefinition.name;
}

int ItemRuntime::identifyRepairDifficulty(const ItemDefinition &itemDefinition)
{
    return std::max(0, itemDefinition.identifyRepairDifficulty);
}

bool ItemRuntime::isRareItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.rarity != ItemRarity::Common;
}

bool ItemRuntime::isUniquelyGeneratedRareItem(const ItemDefinition &itemDefinition)
{
    return (itemDefinition.rarity == ItemRarity::Artifact || itemDefinition.rarity == ItemRarity::Relic)
        && itemDefinition.value > 0;
}

std::optional<std::string> ItemRuntime::classRestriction(const ItemDefinition &itemDefinition)
{
    switch (itemDefinition.itemId)
    {
        case 515:
            return "Knight";

        case 516:
            return "Cleric";

        case 521:
            return "Lich";

        case 529:
            return "Necromancer";

        default:
            return std::nullopt;
    }
}

std::optional<std::string> ItemRuntime::raceRestriction(const ItemDefinition &itemDefinition)
{
    switch (itemDefinition.itemId)
    {
        case 504:
            return "Minotaur";

        case 508:
            return "Vampire";

        case 514:
        case 532:
            return "DarkElf";

        default:
            return std::nullopt;
    }
}

bool ItemRuntime::characterMeetsClassRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    const std::optional<std::string> restriction = classRestriction(itemDefinition);
    return !restriction || matchesClassOrPromotion(character.className, *restriction);
}

bool ItemRuntime::characterMeetsRaceRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    const std::optional<std::string> restriction = raceRestriction(itemDefinition);
    return !restriction || matchesClassOrPromotion(character.className, *restriction);
}

bool ItemRuntime::canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition)
{
    if (!requiresIdentification(itemDefinition))
    {
        return true;
    }

    return identifyRepairSkillScore(character, "IdentifyItem") >= identifyRepairDifficulty(itemDefinition);
}

bool ItemRuntime::canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition)
{
    return identifyRepairSkillScore(character, "RepairItem") >= identifyRepairDifficulty(itemDefinition);
}

std::string ItemRuntime::displayName(const InventoryItem &item, const ItemDefinition &itemDefinition)
{
    return displayName(item, itemDefinition, nullptr, nullptr);
}

std::string ItemRuntime::displayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    if (!item.identified && hasMeaningfulUnidentifiedName(itemDefinition))
    {
        return itemDefinition.unidentifiedName;
    }

    if (item.standardEnchantId != 0 || item.specialEnchantId != 0)
    {
        return ItemEnchantRuntime::displayName(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);
    }

    if (!itemDefinition.name.empty())
    {
        return itemDefinition.name;
    }

    if (hasMeaningfulUnidentifiedName(itemDefinition))
    {
        return itemDefinition.unidentifiedName;
    }

    return "Unknown item";
}
}
