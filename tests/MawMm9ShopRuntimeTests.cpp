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
