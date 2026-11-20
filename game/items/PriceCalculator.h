#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
struct Character;
class Party;
struct HouseEntry;
struct InventoryItem;
struct ItemDefinition;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;

class PriceCalculator
{
public:
    static int playerMerchant(const Character *pCharacter, int effectiveReputation = 0);
    // The member whose merchant value prices the party's deals when the rules compute it themselves (MAW: the best);
    // null under Standard, whose callers choose by the Merchant skill.
    static const Character *rulesMerchantMember(const Party &party);
    static int applyMerchantDiscount(const Character *pCharacter, int goldAmount, int effectiveReputation = 0);
    static int itemBuyingPrice(
        const Character *pCharacter,
        int realValue,
        float priceMultiplier,
        int effectiveReputation = 0);
    static int itemValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr);
    // What a vendor pays, at most resaleCapPercent of the value whatever the Merchant skill (a world's vendors may cap
    // it: HouseEntry::resaleCapPercent).
    static int itemSellingPrice(
        const Character *pCharacter,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        float priceMultiplier,
        const StandardItemEnchantTable *pStandardEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr,
        int effectiveReputation = 0,
        int resaleCapPercent = 100);
    static int itemIdentificationPrice(
        const Character *pCharacter,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        float priceMultiplier,
        const StandardItemEnchantTable *pStandardEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr,
        int effectiveReputation = 0);
    static int itemRepairPrice(
        const Character *pCharacter,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        float priceMultiplier,
        const StandardItemEnchantTable *pStandardEnchantTable = nullptr,
        const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr,
        int effectiveReputation = 0);
    static int skillLearningPrice(
        const Character *pCharacter,
        const HouseEntry &houseEntry,
        bool isGuild,
        int effectiveReputation = 0);
    static int transportPrice(
        const Character *pCharacter,
        const HouseEntry &houseEntry,
        bool isBoat,
        int effectiveReputation = 0);
    static int transportPrice(
        const Character *pCharacter,
        int basePrice,
        float priceMultiplier,
        int effectiveReputation = 0);
    static int tavernRoomPrice(
        const Character *pCharacter,
        const HouseEntry &houseEntry,
        int effectiveReputation = 0);
    static int tavernFoodPrice(
        const Character *pCharacter,
        const HouseEntry &houseEntry,
        int effectiveReputation = 0);
    static int templeHealPrice(const Character *pCharacter, const HouseEntry &houseEntry);
    static int trainingPrice(
        const Character *pCharacter,
        const HouseEntry &houseEntry,
        int effectiveReputation = 0);
    static int trainingPrice(
        const Character *pCharacter,
        const Character *pMerchantCharacter,
        const HouseEntry &houseEntry,
        int effectiveReputation = 0);
};
}
