#pragma once

#include <cstdint>
#include <array>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MapStats;
class ItemTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
class MergedHouseExitTable;
class MergedHouseRuleTable;
class MergedTransportLocationTable;

enum class VendorStockProfile : uint8_t
{
    None = 0,
    Weapon,
    Armor,
    Spellbook,
    Mm9Apothecary,
    Mm9GeneralStore,
    Mm9Library,
};

enum class DialogueScenePolicy : uint8_t
{
    HouseVideo = 0,
    LiveGameplay,
};

// How a shop's Buy Standard and Buy Special show their stock: the MM6-MM8 shelf picture, or MM9's scrolling ledger
// (a vendors buy_view cell).
enum class ShopBuyView : uint8_t
{
    Shelf = 0,
    Ledger,
};

struct HouseEntry
{
    struct DeterministicStockItem
    {
        uint32_t itemId = 0;
        uint32_t quantity = 1;
        bool identified = true;
        uint16_t standardEnchantId = 0;
        uint16_t standardEnchantPower = 0;
        uint16_t specialEnchantId = 0;
        // Offered once the party has done this many of the world's major objectives (vendor_stock min_objectives).
        uint16_t minObjectives = 0;
    };

    struct DeterministicStockPage
    {
        uint32_t pageIndex = 0;
        std::vector<DeterministicStockItem> items;
    };

    struct StockRule
    {
        int quality = 0;
        int secondaryQuality = 0;
        std::vector<uint32_t> itemTypes;
        std::vector<uint32_t> secondaryItemTypes;
    };

    struct TransportRoute
    {
        uint32_t routeIndex = 0;
        std::string destinationName;
        std::string mapFileName;
        std::array<bool, 7> daysAvailable = {true, true, true, true, true, true, true};
        uint32_t travelDays = 0;
        int x = 0;
        int y = 0;
        int z = 0;
        int directionDegrees = 0;
        uint32_t requiredQBit = 0;
        bool useMapStartPosition = false;
    };

    struct ArcomageRule
    {
        int towerToWin = 0;
        int resourceToWin = 0;
        int towerAtStart = 0;
        int wallAtStart = 0;
        int quarry = 0;
        int magic = 0;
        int dungeon = 0;
        int bricks = 0;
        int gems = 0;
        int recruits = 0;
        int ai = 0;
        uint32_t rulesTextId = 0;
    };

    struct ExtraExit
    {
        uint32_t pictureId = 0;
        uint32_t destinationMapId = 0;
        uint32_t requiredQuestBit = 0;
        std::string destinationMapFileName;
        std::string destinationName;
        std::string label;
        bool useMapStartPosition = true;
        int x = 0;
        int y = 0;
        int z = 0;
    };

    uint32_t id = 0;
    uint32_t typeIndex = 0;
    uint32_t mapId = 0;
    uint32_t proprietorPictureId = 0;
    uint32_t roomSoundId = 0;
    uint32_t houseSoundBaseId = 0;
    std::string type;
    std::string name;
    std::string buildingName;
    std::string videoName;
    std::string proprietorName;
    std::string proprietorTitle;
    float priceMultiplier = 0.0f;
    float skillPriceMultiplier = 0.0f;
    float templeHealingTier = 0.0f;
    int templeBehavior = 0;
    StockRule standardStockRule;
    StockRule specialStockRule;
    StockRule spellbookStockRule;
    int standardStockTier = 0;
    int specialStockTier = 0;
    int stockRefreshDays = 0;
    int trainingMaxLevel = 0;
    // The most a vendor pays for an item, a per cent of its value (vendors resale_cap_percent); 100: uncapped.
    int resaleCapPercent = 100;
    int openHour = 0;
    int closeHour = 0;
    std::string enterText;
    std::vector<std::string> offeredSkills;
    // The skill cell said `none`: it teaches nothing, rather than its type's skills.
    bool teachesNothing = false;
    // A price switched by an objective (house_data cell 25, "qbit:multiplier"): once the party has the QBit, the
    // house's price multiplier is priceAfterQBit (HouseTable::get answers with the switched entry). 0: none.
    uint32_t priceQBit = 0;
    float priceAfterQBit = 0.0f;
    std::vector<uint32_t> residentNpcIds;
    std::vector<TransportRoute> transportRoutes;
    std::optional<ArcomageRule> arcomageRule;
    uint32_t rawExtraExitPictureIndex = 0;
    uint32_t rawExtraExitMapId = 0;
    int rawExtraExitRestriction = 0;
    std::optional<ExtraExit> extraExit;
    std::string packageId;
    std::string canonicalId;
    // World (mm6, mm7, mm8, ...) of the house's map; generated stock follows its item world gates.
    std::string worldId;
    uint32_t sourceVendorId = 0;
    uint32_t sourceServiceId = 0;
    VendorStockProfile vendorStockProfile = VendorStockProfile::None;
    DialogueScenePolicy dialogueScenePolicy = DialogueScenePolicy::HouseVideo;
    ShopBuyView shopBuyView = ShopBuyView::Shelf;
    bool vendorCanSell = true;
    bool vendorCanIdentify = true;
    bool vendorCanRepair = true;
    bool templeCanHeal = true;
    bool templeCanDonate = true;
    bool serviceCanLearnSkills = true;
    uint32_t deterministicStockGenerationVersion = 0;
    std::vector<DeterministicStockPage> deterministicStandardStockPages;
    std::vector<DeterministicStockPage> deterministicSpecialStockPages;
};

class HouseTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadAnimationRows(const std::vector<std::vector<std::string>> &rows);
    bool loadAnimationRows(
        const std::vector<std::vector<std::string>> &rows,
        const std::vector<std::vector<std::string>> &movieRows);
    bool appendVendorRows(
        const std::vector<std::vector<std::string>> &vendorRows,
        const std::vector<std::vector<std::string>> &aliasRows,
        const std::vector<std::vector<std::string>> &stockRows,
        std::string &errorMessage);
    bool appendServiceVenueRows(
        const std::vector<std::vector<std::string>> &venueRows,
        const std::vector<std::vector<std::string>> &aliasRows,
        std::string &errorMessage,
        const MapStats *pMapStats = nullptr);
    bool validateVendorStock(
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        std::string &errorMessage) const;
    // A ruleset that no longer rolls a special enchantment on a slot (MAW's Undead Slaying weapons) takes it off the
    // fixed stock of that slot: the item is sold plain. Returns how many stock items lost their enchantment.
    size_t removeSpecialEnchantsTheRulesetDoesNotRoll(
        const ItemTable &itemTable,
        const SpecialItemEnchantTable &specialItemEnchantTable);
    bool applyHouseRules(
        const MergedHouseRuleTable &houseRules,
        const MergedTransportLocationTable &transportLocations,
        const MapStats &mapStats
    );
    bool applyHouseExits(const MergedHouseExitTable &houseExits, const MapStats &mapStats);
    void applyMapWorlds(const MapStats &mapStats);
    std::optional<std::string> getName(uint32_t houseId) const;
    const HouseEntry *get(uint32_t houseId) const;
    // Answers whether the party has a QBit, for the houses whose price an objective switches (HouseEntry::priceQBit).
    // The session sets it; without one every house keeps its own price.
    void setQuestBitQuery(std::function<bool(uint32_t)> query) const;
    const HouseEntry *resolvePackageSourceVendorId(
        const std::string &packageId,
        uint32_t sourceVendorId) const;
    const HouseEntry *resolvePackageSourceServiceId(
        const std::string &packageId,
        uint32_t sourceServiceId) const;
    const std::unordered_map<uint32_t, HouseEntry> &entries() const;

private:
    mutable std::function<bool(uint32_t)> m_questBitQuery;
    mutable std::unordered_map<uint32_t, HouseEntry> m_priceSwitchedEntries;
    bool loadAnimationRows(
        const std::vector<std::vector<std::string>> &rows,
        const std::unordered_map<uint32_t, std::string> &movieStemsByAnimationId);

    std::unordered_map<uint32_t, HouseEntry> m_entries;
    std::unordered_map<std::string, uint32_t> m_vendorAliases;
    std::unordered_map<std::string, uint32_t> m_serviceAliases;
};
}
