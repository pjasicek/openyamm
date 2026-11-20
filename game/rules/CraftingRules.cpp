#include "game/rules/CraftingRules.h"

namespace OpenYAMM::Game
{
bool CraftingRules::hasCrafting() const
{
    return false;
}

bool CraftingRules::isMaterial(const InventoryItem &) const
{
    return false;
}

bool CraftingRules::isExtraTarget(const InventoryItem &) const
{
    return false;
}

CraftResult CraftingRules::craft(const InventoryItem &target, const InventoryItem &, const CraftingContext &) const
{
    CraftResult result;
    result.target = target;
    return result;
}

std::string CraftingRules::materialAction(uint32_t) const
{
    return {};
}

std::optional<std::string> CraftingRules::materialDescription(const InventoryItem &) const
{
    return std::nullopt;
}

int CraftingRules::gemTier(uint32_t) const
{
    return 0;
}

int CraftingRules::gemCombineCount() const
{
    return 0;
}

uint32_t CraftingRules::combinedGem(uint32_t) const
{
    return 0;
}

std::vector<std::string> CraftingRules::craftOutlook(const InventoryItem &, const CraftingContext &) const
{
    return {};
}

const CraftingRules &standardCraftingRules()
{
    static const CraftingRules Rules;
    return Rules;
}
}
