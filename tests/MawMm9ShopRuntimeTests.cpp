#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/RulesetDefinition.h"
#include "game/data/GameDataLoader.h"
#include "game/data/GameDataRepository.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawRulesFactory.h"

#include <algorithm>
#include <filesystem>
#include <memory>
#include <set>
#include <string>
#include <vector>

// MAW in MM9 (devdocs/maw/MM9_SUPPORT.md): MM9's shops under the MAW ruleset. Needs the MM9 world package.

TEST_CASE("MAW rolls MM9's fixed shop stock: the vendor's items at MAW's power and rarity")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm9"));
    std::vector<OpenYAMM::Game::RulesetDefinition> rulesets;
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::loadAvailableRulesets(assetFileSystem, rulesets, error), error);
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(),
        [](const OpenYAMM::Game::RulesetDefinition &ruleset) { return ruleset.id == "maw"; });
    REQUIRE(maw != rulesets.end());

    // MAW stops rolling some enchantments MM9's stock carries; it loads all the same (MM9_SUPPORT.md).
    OpenYAMM::Game::GameDataLoader dataLoader = {};
    dataLoader.setActiveRuleset(*maw);
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    OpenYAMM::Game::GameDataRepository data;
    data.bind(dataLoader);
    std::unique_ptr<OpenYAMM::Game::MawRules> pRules = OpenYAMM::Game::createMawRules(data, maw->defaultOptions());
    REQUIRE(pRules != nullptr);
    // MAW sizes shop stock by the levels banked (a share of them): a party with 40 on Chedian.
    pRules->state().continentLevels[3] = 40;

    const OpenYAMM::Game::HouseEntry *pSturmfordWeaponVendor =
        dataLoader.getHouseTable().resolvePackageSourceVendorId("mm9", 53);
    REQUIRE(pSturmfordWeaponVendor != nullptr);
    OpenYAMM::Game::Party party;
    party.setRules(&pRules->gameRules());
    const std::vector<OpenYAMM::Game::InventoryItem> stock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        party,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pSturmfordWeaponVendor,
        0.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_FALSE(stock.empty());

    size_t rolled = 0;
    for (size_t slotIndex = 0; slotIndex < stock.size(); ++slotIndex)
    {
        // The vendor keeps its items...
        CHECK_EQ(stock[slotIndex].objectDescriptionId,
            pSturmfordWeaponVendor->deterministicStandardStockPages[0].items[slotIndex].itemId);
        // ...and MAW gives them their power (MM9's gear has MAW bases: rulesets/maw/worlds/mm9/item_bases.yml).
        rolled += stock[slotIndex].rulesetFields.itemPower > 0 ? 1 : 0;
    }
    CHECK(rolled > stock.size() / 2);
}

TEST_CASE("MM9's shops buy the MM6-MM8 potions, scrolls, wands and gems a party brings in")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm9"));
    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    const OpenYAMM::Game::ItemTable &itemTable = dataLoader.getItemTable();
    const OpenYAMM::Game::HouseEntry *pApothecary = dataLoader.getHouseTable().get(30015);
    const OpenYAMM::Game::HouseEntry *pWeaponShop = dataLoader.getHouseTable().get(30010);
    REQUIRE(pApothecary != nullptr);
    REQUIRE(pWeaponShop != nullptr);

    // A potion bottle, a spell scroll, a wand and a gem of the merged MM6-MM8 table.
    for (const uint32_t itemId : {220u, 311u, 166u, 991u})
    {
        const OpenYAMM::Game::ItemDefinition *pDefinition = itemTable.get(itemId);
        REQUIRE(pDefinition != nullptr);
        OpenYAMM::Game::InventoryItem item = {};
        item.objectDescriptionId = itemId;
        CHECK_MESSAGE(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(itemTable, *pApothecary, item),
            pDefinition->name);
        CHECK_MESSAGE(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(itemTable, *pWeaponShop, item),
            pDefinition->name);
    }

    // MM9's own letters and quest notes stay unsellable.
    OpenYAMM::Game::InventoryItem letter = {};
    letter.objectDescriptionId = 10247;
    CHECK_FALSE(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(itemTable, *pApothecary, letter));
}

TEST_CASE("MAW's paid new stock gives a weapon shop new shelves (Xeen and MM6-MM8)")
{
    // Feedback F52 (2026-11-24): Norman's New stock in Vertigo seemed to bring back the same items. Each paid stocking
    // is new, and since the player's report of predetermined loot (2026-11-24) a paid stocking adds a fresh random
    // value, so a reloaded save does not reroll the same new stock again.
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "xeen"));
    std::vector<OpenYAMM::Game::RulesetDefinition> rulesets;
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::loadAvailableRulesets(assetFileSystem, rulesets, error), error);
    const auto maw = std::find_if(rulesets.begin(), rulesets.end(),
        [](const OpenYAMM::Game::RulesetDefinition &ruleset) { return ruleset.id == "maw"; });
    REQUIRE(maw != rulesets.end());
    OpenYAMM::Game::GameDataLoader dataLoader = {};
    dataLoader.setActiveRuleset(*maw);
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    OpenYAMM::Game::GameDataRepository data;
    data.bind(dataLoader);
    std::unique_ptr<OpenYAMM::Game::MawRules> pRules = OpenYAMM::Game::createMawRules(data, maw->defaultOptions());
    REQUIRE(pRules != nullptr);

    // Norman's Ironworks (Xeen 4001), and the first MM7 weapon shop for comparison.
    std::vector<const OpenYAMM::Game::HouseEntry *> shops;
    shops.push_back(dataLoader.getHouseTable().get(4001));
    for (const auto &[houseId, house] : dataLoader.getHouseTable().entries())
    {
        if (house.worldId == "mm7" && house.type == "Weapon Shop")
        {
            shops.push_back(&house);
            break;
        }
    }

    for (const OpenYAMM::Game::HouseEntry *pShop : shops)
    {
        REQUIRE(pShop != nullptr);
        OpenYAMM::Game::Party party;
        party.setRules(&pRules->gameRules());
        party.setItemTable(&dataLoader.getItemTable());
        party.setItemEnchantTables(&dataLoader.getStandardItemEnchantTable(),
            &dataLoader.getSpecialItemEnchantTable());
        party.addGold(1000000, OpenYAMM::Game::GoldReason::Other);
        const auto shelves = [&]()
        {
            std::vector<uint32_t> ids;
            for (const OpenYAMM::Game::HouseStockMode mode :
                {OpenYAMM::Game::HouseStockMode::ShopStandard, OpenYAMM::Game::HouseStockMode::ShopSpecial})
            {
                for (const OpenYAMM::Game::InventoryItem &item : OpenYAMM::Game::HouseServiceRuntime::ensureStock(
                         party, dataLoader.getItemTable(), dataLoader.getStandardItemEnchantTable(),
                         dataLoader.getSpecialItemEnchantTable(), *pShop, 0.0f, mode))
                {
                    ids.push_back(item.objectDescriptionId);
                }
            }
            return ids;
        };

        const std::vector<uint32_t> first = shelves();
        std::string status;
        std::set<std::vector<uint32_t>> seen = {first};
        for (int reroll = 0; reroll < 4; ++reroll)
        {
            REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryRerollStock(party, dataLoader.getItemTable(),
                dataLoader.getStandardItemEnchantTable(), dataLoader.getSpecialItemEnchantTable(), *pShop, 0.0f,
                status));
            seen.insert(shelves());
        }

        std::string firstText;
        for (const uint32_t id : first)
        {
            firstText += std::to_string(id) + " ";
        }
        CHECK_MESSAGE(seen.size() >= 4, pShop->name << " (" << pShop->id << "): " << seen.size()
            << " different shelves in 5 stockings; first: " << firstText);

        // A reload: the shop's state as saved before a paid stocking, then the same stocking again.
        const OpenYAMM::Game::CampaignState::HouseStockState saved = *party.campaign().houseStockState(pShop->id);
        std::set<std::vector<uint32_t>> afterReload;
        for (int reload = 0; reload < 3; ++reload)
        {
            *party.campaign().houseStockState(pShop->id) = saved;
            REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryRerollStock(party, dataLoader.getItemTable(),
                dataLoader.getStandardItemEnchantTable(), dataLoader.getSpecialItemEnchantTable(), *pShop, 0.0f,
                status));
            afterReload.insert(shelves());
        }
        CHECK_MESSAGE(afterReload.size() >= 2, pShop->name << ": the same new stock after every reload");
    }
}
