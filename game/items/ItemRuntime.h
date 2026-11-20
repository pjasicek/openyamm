#pragma once

#include "game/party/Party.h"

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
    static bool isArtifact(const ItemDefinition &itemDefinition);
    // Items hardened by the potion and all artifacts never break (GrayFace's HardenArtifacts), except on eradication.
    static bool isHardened(bool hardenedFlag, const ItemDefinition &itemDefinition);
    static std::optional<std::string> classRestriction(const ItemDefinition &itemDefinition);
    static std::optional<std::string> raceRestriction(const ItemDefinition &itemDefinition);
    // Who may wear a class- or race-gated item, as the popup and a refused equip say it ("Knights only").
    static std::optional<std::string> wearRequirementText(const ItemDefinition &itemDefinition);
    static bool characterMeetsClassRestriction(const Character &character, const ItemDefinition &itemDefinition);
    static bool characterMeetsRaceRestriction(const Character &character, const ItemDefinition &itemDefinition);
    static bool canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition);
    static bool canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition);
    static bool canDrop(const ItemDefinition &itemDefinition);
    static std::string displayName(const InventoryItem &item, const ItemDefinition &itemDefinition);
    // Generic item-class name used by "You found an item (...)" messages, never revealing an unidentified item.
    static std::string foundItemName(const ItemDefinition &itemDefinition);
    static std::string displayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardEnchantTable,
        const SpecialItemEnchantTable *pSpecialEnchantTable);
    // The name of an identified item without what the active rules add (Standard's own naming).
    static std::string identifiedDisplayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardEnchantTable,
        const SpecialItemEnchantTable *pSpecialEnchantTable);
};
}
