#pragma once

#include "game/tables/HouseTable.h"
#include "game/gameplay/HouseInteraction.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct InventoryItem;
struct ItemDefinition;
class ItemTable;
class Party;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;

enum class HouseStockMode : uint8_t
{
    ShopStandard = 0,
    ShopSpecial,
    GuildSpellbooks
};

class HouseServiceRuntime
{
public:
    enum class ShopItemServiceResult
    {
        None,
        Success,
        NoItem,
        Unavailable,
        WrongShop,
        AlreadyIdentified,
        NothingToRepair,
        NotEnoughGold,
        Failed,
    };

    static bool supportsGeneratedStock(const HouseEntry &houseEntry);
    static bool supportsEquipmentSell(const HouseEntry &houseEntry);
    static bool supportsIdentify(const HouseEntry &houseEntry);
    static bool supportsRepair(const HouseEntry &houseEntry);
    static size_t slotCountForStockMode(const HouseEntry &houseEntry, HouseStockMode mode);
    static const std::vector<InventoryItem> &ensureStock(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        float gameMinutes,
        HouseStockMode mode);
    static int buyPrice(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static int sellPrice(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static bool canSellItemToHouse(const ItemTable &itemTable, const HouseEntry &houseEntry, const InventoryItem &item);
    static std::string buildBuyHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static std::string buildSellHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static std::string buildIdentifyHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static std::string buildRepairHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    static bool tryBuyStockItem(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        float gameMinutes,
        HouseStockMode mode,
        size_t slotIndex,
        std::string &statusText);
    static bool trySellInventoryItem(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText,
        ShopItemServiceResult *pResult = nullptr);
    static bool tryIdentifyInventoryItem(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText,
        ShopItemServiceResult *pResult = nullptr);
    static bool tryRepairInventoryItem(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText,
        ShopItemServiceResult *pResult = nullptr);
};
}
