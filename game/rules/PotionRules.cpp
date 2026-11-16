#include "game/rules/PotionRules.h"

#include "game/items/InventoryItemMixingRuntime.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
int PotionRules::reagentPower(const ItemDefinition &reagentDefinition, const InventoryItem &, SkillMastery, uint32_t) const
{
    return InventoryItemMixingRuntime::reagentPower(reagentDefinition);
}

double PotionRules::estimatedPool(PotionPool, int) const
{
    return 0;
}

uint32_t PotionRules::mixingAlchemyLevel(const Character &alchemist) const
{
    // The effective level, as the original brews: items and hired Herbalists or Apothecaries add to the trained level.
    const CharacterSkill *pSkill = alchemist.findSkill("Alchemy");
    return pSkill != nullptr ? uint32_t(std::max(0, int(pSkill->level) + alchemist.skillBonus("Alchemy"))) : 0;
}

int PotionRules::catalystMixPower(int targetPower, int heldPower, bool bothCatalysts, SkillMastery, uint32_t) const
{
    return bothCatalysts ? std::max(targetPower, heldPower) : heldPower;
}

std::optional<std::string> PotionRules::noBenefitText() const
{
    return std::nullopt;
}

bool PotionRules::potionAuraCounts(uint32_t, int) const
{
    return true;
}

const PotionRules &standardPotionRules()
{
    static const PotionRules Rules;
    return Rules;
}
}
