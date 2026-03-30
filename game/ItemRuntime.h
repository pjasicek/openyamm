#pragma once

#include "game/Party.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
struct ItemDefinition;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;

class ItemRuntime
{
public:
    static bool requiresIdentification(const ItemDefinition &itemDefinition);
    static int identifyRepairDifficulty(const ItemDefinition &itemDefinition);
    static bool isRareItem(const ItemDefinition &itemDefinition);
    static bool isUniquelyGeneratedRareItem(const ItemDefinition &itemDefinition);
    static std::optional<std::string> classRestriction(const ItemDefinition &itemDefinition);
    static std::optional<std::string> raceRestriction(const ItemDefinition &itemDefinition);
    static bool characterMeetsClassRestriction(const Character &character, const ItemDefinition &itemDefinition);
    static bool characterMeetsRaceRestriction(const Character &character, const ItemDefinition &itemDefinition);
    static bool canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition);
    static bool canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition);
    static std::string displayName(const InventoryItem &item, const ItemDefinition &itemDefinition);
    static std::string displayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardEnchantTable,
        const SpecialItemEnchantTable *pSpecialEnchantTable);
};
}
