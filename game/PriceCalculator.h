#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
struct Character;
struct HouseEntry;
struct InventoryItem;
struct ItemDefinition;

class PriceCalculator
{
public:
    static int playerMerchant(const Character *pCharacter);
    static int applyMerchantDiscount(const Character *pCharacter, int goldAmount);
    static int itemBuyingPrice(const Character *pCharacter, const ItemDefinition &itemDefinition, float priceMultiplier);
    static int itemSellingPrice(
        const Character *pCharacter,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        float priceMultiplier);
    static int itemIdentificationPrice(const Character *pCharacter, float priceMultiplier);
    static int itemRepairPrice(const Character *pCharacter, const ItemDefinition &itemDefinition, float priceMultiplier);
    static int skillLearningPrice(const Character *pCharacter, const HouseEntry &houseEntry, bool isGuild);
    static int transportPrice(const Character *pCharacter, const HouseEntry &houseEntry, bool isBoat);
    static int tavernRoomPrice(const Character *pCharacter, const HouseEntry &houseEntry);
    static int tavernFoodPrice(const Character *pCharacter, const HouseEntry &houseEntry);
    static int templeHealPrice(const Character *pCharacter, const HouseEntry &houseEntry);
    static int trainingPrice(const Character *pCharacter, const HouseEntry &houseEntry);
};
}
