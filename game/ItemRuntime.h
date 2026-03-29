#pragma once

#include "game/Party.h"

#include <string>

namespace OpenYAMM::Game
{
struct ItemDefinition;

class ItemRuntime
{
public:
    static bool requiresIdentification(const ItemDefinition &itemDefinition);
    static int identifyRepairDifficulty(const ItemDefinition &itemDefinition);
    static bool canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition);
    static bool canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition);
    static std::string displayName(const InventoryItem &item, const ItemDefinition &itemDefinition);
};
}
