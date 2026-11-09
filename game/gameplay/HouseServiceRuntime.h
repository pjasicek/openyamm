#pragma once

#include "game/tables/HouseTable.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/items/InventoryBags.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct InventoryItem;
struct ItemDefinition;
class ItemTable;
class IGameplayWorldRuntime;
class Party;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct EventRuntimeState;

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
        InventoryFull,
        Stolen,
        TheftCaught,
        Failed,
    };

    static bool supportsGeneratedStock(const HouseEntry &houseEntry);
    static bool supportsEquipmentSell(const HouseEntry &houseEntry);
    static bool supportsIdentify(const HouseEntry &houseEntry);
    static bool supportsRepair(const HouseEntry &houseEntry);
    // The slots on one shelf of the stock: a guild's spellbook stock holds one such shelf for each school of
    // spellbookShelfSchools, one after another.
    static size_t slotCountForStockMode(const HouseEntry &houseEntry, HouseStockMode mode);
    // The schools whose spellbooks a guild sells (0 Fire ... 8 Dark), one shelf each, in spell order: an Elemental
    // Guild has Fire, Air, Water and Earth shelves, as in MM8.
    static std::vector<uint32_t> spellbookShelfSchools(const HouseEntry &houseEntry);
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
        const InventoryItem &item,
        int effectiveReputation = 0);
    static int sellPrice(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item,
        int effectiveReputation = 0);
    static bool canSellItemToHouse(const ItemTable &itemTable, const HouseEntry &houseEntry, const InventoryItem &item);
    static std::string buildBuyHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item,
        int effectiveReputation = 0);
    static std::string buildSellHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item,
        int effectiveReputation = 0);
    static std::string buildIdentifyHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item,
        int effectiveReputation = 0);
    static std::string buildRepairHoverText(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item,
        int effectiveReputation = 0);
    static bool tryBuyStockItem(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        float gameMinutes,
        HouseStockMode mode,
        size_t slotIndex,
        std::string &statusText,
        ShopItemServiceResult *pResult = nullptr,
        int effectiveReputation = 0);
    // Rerolls a shop's whole stock for the rules' price (MAW); every new item comes identified. False when the shop
    // cannot be rerolled or the party cannot pay.
    static bool tryRerollStock(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        float gameMinutes,
        std::string &statusText);
    static bool tryStealStockItem(
        Party &party,
        IGameplayWorldRuntime &worldRuntime,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        float gameMinutes,
        HouseStockMode mode,
        size_t slotIndex,
        uint32_t successRoll,
        uint32_t caughtRoll,
        std::string &statusText,
        ShopItemServiceResult *pResult = nullptr,
        int effectiveReputation = 0);
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
        ShopItemServiceResult *pResult = nullptr,
        int effectiveReputation = 0);
    // Sell trash, on the sell screen of a ruleset with item rarities (MAW, ItemRules::lootFilterFacts): the rules pick
    // the trash (isSellTrash), the player adds and removes items, and the pick is sold at once.
    static bool offersSellTrash(const Party &party, const HouseEntry &houseEntry);
    // What the rules pick from every member's bags: identified items this shop buys and the rules let go.
    static std::vector<BagItemRef> findSellTrash(
        const Party &party,
        const ItemTable &itemTable,
        const HouseEntry &houseEntry);
    // Whether the player can add the item to the pick: the shop buys it and the rules let it go.
    static bool canSellTrashItem(
        const Party &party,
        const ItemTable &itemTable,
        const HouseEntry &houseEntry,
        const InventoryItem &item);
    // The item a pick refers to, while it still begins at that cell; none once it is gone.
    static const InventoryItem *sellTrashItem(const Party &party, const BagItemRef &ref);
    // The gold the pick brings.
    static int sellTrashPrice(
        const Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const std::vector<BagItemRef> &items,
        int effectiveReputation = 0);
    // Sells the pick ("Sold 12 items for 3400 gold."); returns how many were sold.
    static size_t trySellTrash(
        Party &party,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const HouseEntry &houseEntry,
        const std::vector<BagItemRef> &items,
        std::string &statusText,
        int effectiveReputation = 0);
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
        ShopItemServiceResult *pResult = nullptr,
        int effectiveReputation = 0,
        const EventRuntimeState *pEventRuntimeState = nullptr);
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
        ShopItemServiceResult *pResult = nullptr,
        int effectiveReputation = 0,
        const EventRuntimeState *pEventRuntimeState = nullptr);
};
}
