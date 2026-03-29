#include "game/ItemRuntime.h"

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

    if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
    {
        return 0;
    }

    if (pSkill->mastery == SkillMastery::Grandmaster)
    {
        return std::numeric_limits<int>::max();
    }

    return static_cast<int>(pSkill->level) * masteryMultiplier(pSkill->mastery);
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
    if (!item.identified && hasMeaningfulUnidentifiedName(itemDefinition))
    {
        return itemDefinition.unidentifiedName;
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
