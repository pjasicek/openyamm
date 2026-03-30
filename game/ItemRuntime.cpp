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
