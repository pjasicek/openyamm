#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/ui/HouseShopLedger.h"

#include <algorithm>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace
{
using namespace OpenYAMM::Game;

std::vector<std::string> itemRow(uint32_t id, const std::string &name, const std::string &equipStat,
    const std::string &mod1 = "", const std::string &skillGroup = "")
{
    std::vector<std::string> row(26);
    row[5] = skillGroup;
    row[6] = mod1;
    row[0] = std::to_string(id);
    row[1] = "missing_test_icon";
    row[2] = name;
    row[3] = "100";
    row[4] = equipStat;
    row[17] = "test";
    row[18] = "test:item/" + std::to_string(id);
    row[19] = std::to_string(id);
    return row;
}

ItemTable makeItemTable()
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    ItemTable itemTable;
    REQUIRE(itemTable.load(assetFileSystem,
        {
            itemRow(10001, "Short Sword", "Weapon"),
            itemRow(10002, "Leather Armor", "Armor"),
            itemRow(10003, "Gloves", "Gauntlets"),
            itemRow(10004, "Spear Skill", "LearnSkill"),
            itemRow(10005, "Gold Ring", "Ring"),
            itemRow(10006, "Fire Bolt", "Book", "S2"),
            itemRow(10007, "Heal", "Book", "S68"),
            itemRow(10008, "Torch Light", "Book", "S1"),
            itemRow(10009, "Inferno", "Book", "S11"),
            itemRow(10010, "Halberd", "Weapon1or2", "", "Spear"),
            itemRow(10011, "Dwarven Hammer", "Weapon", "", "Mace"),
            itemRow(10012, "Cudgel", "Weapon", "", "Club"),
            itemRow(10013, "Long Bow", "Missile", "", "Bow"),
            itemRow(10014, "Chain Mail", "Armor", "", "Chain"),
            itemRow(10015, "Buckler", "Shield", "", "Shield"),
            itemRow(10016, "Helm", "Helm"),
        },
        {}));
    return itemTable;
}

InventoryItem stockItem(uint32_t id, uint16_t specialEnchantId = 0)
{
    InventoryItem item = {};
    item.objectDescriptionId = id;
    item.specialEnchantId = specialEnchantId;
    return item;
}

std::vector<std::string> vendorRow(const std::string &buyView)
{
    std::vector<std::string> row(35);
    row[0] = "30010";
    row[1] = "mm9";
    row[2] = "10";
    row[3] = "mm9:vendor/10";
    row[4] = "The Thjoradric Fist";
    row[5] = "Thjorgard";
    row[6] = "Weapon";
    row[8] = "Weapon";
    row[11] = "3";
    row[18] = "14";
    row[22] = "LiveGameplay";
    row[34] = buyView;
    return row;
}
}

TEST_CASE("house shop ledger sorts items into MM9's merchant tabs")
{
    ItemDefinition definition = {};
    const auto categoryOf = [&definition](const char *pEquipStat)
    {
        definition.equipStat = pEquipStat;
        return houseShopLedgerCategoryOf(definition);
    };

    CHECK(categoryOf("Weapon2") == HouseShopLedgerCategory::Weapons);
    CHECK(categoryOf("Missile") == HouseShopLedgerCategory::Weapons);
    CHECK(categoryOf("Shield") == HouseShopLedgerCategory::Armor);
    CHECK(categoryOf("Belt") == HouseShopLedgerCategory::Armor);
    CHECK(categoryOf("Boots") == HouseShopLedgerCategory::GlovesBoots);
    CHECK(categoryOf("Amulet") == HouseShopLedgerCategory::Jewelry);
    CHECK(categoryOf("Book") == HouseShopLedgerCategory::Books);
    CHECK(categoryOf("LearnSkill") == HouseShopLedgerCategory::Books);
    // Wands stay with potions and scrolls, as at MM9's apothecaries.
    CHECK(categoryOf("WeaponW") == HouseShopLedgerCategory::PotionsMisc);
    CHECK(categoryOf("Bottle") == HouseShopLedgerCategory::PotionsMisc);
}

TEST_CASE("house shop ledger groups copies and leaves out sold slots")
{
    const ItemTable itemTable = makeItemTable();
    const std::vector<InventoryItem> stock = {
        stockItem(10001),
        stockItem(10002),
        stockItem(10001),
        stockItem(0),
        stockItem(10001, 4),
        stockItem(10003),
        stockItem(10002),
        // Past the shop's slot count: not shown.
        stockItem(10005),
    };

    const HouseShopLedgerModel model = buildHouseShopLedgerModel(stock, 7, itemTable, HouseShopLedgerCategory::All);
    REQUIRE(model.rows.size() == 4);
    CHECK(model.rows[0].stockIndices == std::vector<size_t>{0, 2});
    CHECK(model.rows[1].stockIndices == std::vector<size_t>{1, 6});
    // An enchanted copy is a different item.
    CHECK(model.rows[2].stockIndices == std::vector<size_t>{4});
    CHECK(model.rows[3].stockIndices == std::vector<size_t>{5});
    CHECK(model.itemsForSale == 6);
    CHECK(model.copiesGrouped == 2);

    REQUIRE(model.chips.size() == 4);
    CHECK(model.chips[0].category == HouseShopLedgerCategory::All);
    CHECK(model.chips[0].rowCount == 4);
    CHECK(model.chips[1].category == HouseShopLedgerCategory::Weapons);
    CHECK(model.chips[1].rowCount == 2);
    CHECK(model.chips[2].category == HouseShopLedgerCategory::Armor);
    CHECK(model.chips[3].category == HouseShopLedgerCategory::GlovesBoots);

    const HouseShopLedgerModel weapons =
        buildHouseShopLedgerModel(stock, 7, itemTable, HouseShopLedgerCategory::Weapons);
    CHECK(weapons.filter == HouseShopLedgerCategory::Weapons);
    CHECK(weapons.rows.size() == 2);

    // A tab the stock no longer has falls back to All.
    const HouseShopLedgerModel books = buildHouseShopLedgerModel(stock, 7, itemTable, HouseShopLedgerCategory::Books);
    CHECK(books.filter == HouseShopLedgerCategory::All);
    CHECK(books.rows.size() == 4);
}

TEST_CASE("house shop ledger sorts a magic shop's spellbooks by spell and tabs them by school")
{
    const ItemTable itemTable = makeItemTable();
    const std::vector<InventoryItem> stock = {stockItem(10007), stockItem(10009), stockItem(10006), stockItem(10008)};
    const HouseShopLedgerModel model = buildHouseShopLedgerModel(stock, 4, itemTable, HouseShopLedgerCategory::All);
    REQUIRE(model.rows.size() == 4);
    // Torch Light (S1), Fire Bolt (S2), Inferno (S11), then Heal (S68, Body).
    CHECK(model.rows[0].stockIndices.front() == 3);
    CHECK(model.rows[1].stockIndices.front() == 2);
    CHECK(model.rows[2].stockIndices.front() == 1);
    CHECK(model.rows[3].stockIndices.front() == 0);
    REQUIRE(model.chips.size() == 3);
    CHECK(model.chips[1].category == HouseShopLedgerCategory::FireBooks);
    CHECK(model.chips[1].rowCount == 3);
    CHECK(model.chips[2].category == HouseShopLedgerCategory::BodyBooks);

    const HouseShopLedgerModel body =
        buildHouseShopLedgerModel(stock, 4, itemTable, HouseShopLedgerCategory::BodyBooks);
    REQUIRE(body.rows.size() == 1);
    CHECK(body.rows[0].stockIndices.front() == 0);

    CHECK(houseShopLedgerSpellbookLine(*itemTable.get(10008)) == "Fire Magic - Normal");
    CHECK(houseShopLedgerSpellbookLine(*itemTable.get(10009)) == "Fire Magic - Grandmaster");
    CHECK(houseShopLedgerSpellbookLine(*itemTable.get(10007)) == "Body Magic - Normal");
    CHECK(houseShopLedgerSpellbookLine(*itemTable.get(10001)).empty());
}

TEST_CASE("house shop ledger shows no tabs for a single kind of goods")
{
    const ItemTable itemTable = makeItemTable();
    const std::vector<InventoryItem> stock = {stockItem(10004), stockItem(10004), stockItem(10004)};
    const HouseShopLedgerModel model = buildHouseShopLedgerModel(stock, 12, itemTable, HouseShopLedgerCategory::All);
    CHECK(model.chips.empty());
    REQUIRE(model.rows.size() == 1);
    CHECK(model.rows[0].stockIndices.size() == 3);
}

TEST_CASE("house shop ledger tabs a weapon smith's or an armourer's goods by kind")
{
    const ItemTable itemTable = makeItemTable();
    const std::vector<InventoryItem> weapons = {
        stockItem(10010), stockItem(10011), stockItem(10001), stockItem(10012), stockItem(10013)};
    const HouseShopLedgerModel model = buildHouseShopLedgerModel(weapons, 5, itemTable, HouseShopLedgerCategory::All);
    // The Short Sword has no skill group here: listed under All only.
    REQUIRE(model.chips.size() == 4);
    CHECK(model.chips[0].category == HouseShopLedgerCategory::All);
    CHECK(model.chips[1].category == HouseShopLedgerCategory::Spears);
    CHECK(model.chips[2].category == HouseShopLedgerCategory::Maces);
    CHECK(model.chips[2].rowCount == 2);
    CHECK(model.chips[3].category == HouseShopLedgerCategory::Bows);
    CHECK(model.rows.size() == 5);

    const HouseShopLedgerModel maces = buildHouseShopLedgerModel(weapons, 5, itemTable, HouseShopLedgerCategory::Maces);
    REQUIRE(maces.rows.size() == 2);
    CHECK(maces.rows[0].stockIndices.front() == 1);
    CHECK(maces.rows[1].stockIndices.front() == 3);

    const std::vector<InventoryItem> armour = {stockItem(10014), stockItem(10015), stockItem(10016), stockItem(10002)};
    const HouseShopLedgerModel armourer = buildHouseShopLedgerModel(armour, 4, itemTable, HouseShopLedgerCategory::All);
    REQUIRE(armourer.chips.size() == 4);
    CHECK(armourer.chips[1].category == HouseShopLedgerCategory::BodyArmor);
    CHECK(armourer.chips[1].rowCount == 2);
    CHECK(armourer.chips[2].category == HouseShopLedgerCategory::Shields);
    CHECK(armourer.chips[3].category == HouseShopLedgerCategory::Helms);

    // Weapons beside other goods keep MM9's merchant tabs.
    const std::vector<InventoryItem> mixed = {stockItem(10010), stockItem(10011), stockItem(10014)};
    const HouseShopLedgerModel general = buildHouseShopLedgerModel(mixed, 3, itemTable, HouseShopLedgerCategory::All);
    REQUIRE(general.chips.size() == 3);
    CHECK(general.chips[1].category == HouseShopLedgerCategory::Weapons);
    CHECK(general.chips[2].category == HouseShopLedgerCategory::Armor);
}

TEST_CASE("house shop ledger scrolls by whole rows inside the shop frame")
{
    // The shop frame at 2x: 460 by 338 logical units below the top bar.
    const GameplayResolvedHudLayoutElement frame = {100.0f, 56.0f, 920.0f, 676.0f, 2.0f};
    const HouseShopLedgerLayout layout = buildHouseShopLedgerLayout(frame);
    CHECK(layout.visibleRows == 7);
    CHECK(layout.list.height == doctest::Approx(7 * 36 * 2.0f));
    CHECK(layout.list.y + layout.list.height <= layout.footer.y);
    CHECK(houseShopLedgerMaximumFirstRow(layout, 5) == 0);
    CHECK(houseShopLedgerMaximumFirstRow(layout, 12) == 5);

    const std::vector<HouseShopLedgerRowRect> rows = houseShopLedgerVisibleRows(layout, 12, 3);
    REQUIRE(rows.size() == 7);
    CHECK(rows.front().rowIndex == 3);
    CHECK(rows.back().rowIndex == 9);
    // Rows leave the scrollbar's strip free when the list scrolls.
    CHECK(rows.front().rect.width == doctest::Approx(layout.list.width - 8 * 2.0f));
    CHECK(houseShopLedgerVisibleRows(layout, 12, 40).front().rowIndex == 5);

    const float rowY = rows[2].rect.y + 4.0f;
    CHECK(houseShopLedgerRowAt(layout, 12, 3, layout.list.x + 20.0f, rowY) == 5);
    CHECK_FALSE(houseShopLedgerRowAt(layout, 12, 3, layout.list.x + layout.list.width - 4.0f, rowY).has_value());
    CHECK(houseShopLedgerOnScrollbar(layout, layout.list.x + layout.list.width - 4.0f, rowY));

    // Seven tabs narrow to share the bar; ten (All and nine schools) still fit, the ones past the bar are left out.
    const std::vector<GameplayResolvedHudLayoutElement> chips = houseShopLedgerChipRects(layout, 7);
    CHECK(chips.size() == 7);
    CHECK(chips[0].width < HouseShopLedgerMetrics::ChipWidth * 2.0f);
    CHECK(houseShopLedgerChipAt(layout, 7, chips[1].x + 2.0f, chips[1].y + 2.0f) == 1);
    CHECK(houseShopLedgerChipRects(layout, 10).size() == 10);
    CHECK(houseShopLedgerChipRects(layout, 2).front().width == doctest::Approx(HouseShopLedgerMetrics::ChipWidth * 2));
    CHECK(houseShopLedgerChipRects(layout, 20).size() < 20);
}

TEST_CASE("house shop ledger headings cycle the list through type and price order")
{
    using Key = HouseShopLedgerSortKey;
    HouseShopLedgerSort sort = {};
    sort = nextHouseShopLedgerSort(sort, Key::Price);
    CHECK((sort.key == Key::Price && !sort.descending));
    sort = nextHouseShopLedgerSort(sort, Key::Price);
    CHECK((sort.key == Key::Price && sort.descending));
    // The other heading starts ascending; a third click on one heading restores the stock's order.
    CHECK((nextHouseShopLedgerSort(sort, Key::Type).key == Key::Type && !nextHouseShopLedgerSort(sort, Key::Type)
        .descending));
    sort = nextHouseShopLedgerSort(sort, Key::Price);
    CHECK(sort.key == Key::Stock);

    const auto makeRow = [](size_t stockIndex, HouseShopLedgerCategory category, const std::string &type, int price)
    {
        HouseShopLedgerRow row = {};
        row.stockIndices = {stockIndex};
        row.category = category;
        row.typeText = type;
        row.price = price;
        return row;
    };
    const std::vector<HouseShopLedgerRow> stockOrder = {
        makeRow(0, HouseShopLedgerCategory::Armor, "Helm", 300),
        makeRow(1, HouseShopLedgerCategory::Weapons, "Sword", 120),
        makeRow(2, HouseShopLedgerCategory::Weapons, "Axe", 300),
        makeRow(3, HouseShopLedgerCategory::Weapons, "Sword", 80),
    };
    const auto order = [&stockOrder](HouseShopLedgerSort by)
    {
        std::vector<HouseShopLedgerRow> rows = stockOrder;
        sortHouseShopLedgerRows(rows, by);
        std::vector<size_t> indices;
        for (const HouseShopLedgerRow &row : rows)
        {
            indices.push_back(row.stockIndices.front());
        }
        return indices;
    };

    CHECK(order({Key::Stock, false}) == std::vector<size_t>{0, 1, 2, 3});
    // Equal prices keep the stock's order either way round.
    CHECK(order({Key::Price, false}) == std::vector<size_t>{3, 1, 0, 2});
    CHECK(order({Key::Price, true}) == std::vector<size_t>{0, 2, 1, 3});
    // Type: MM9's tab order (weapons before armour), then the type line; two swords keep the stock's order.
    CHECK(order({Key::Type, false}) == std::vector<size_t>{2, 1, 3, 0});
    CHECK(order({Key::Type, true}) == std::vector<size_t>{0, 1, 3, 2});

    // Spellbooks by type: school by school in spell order, whatever their type lines say.
    std::vector<HouseShopLedgerRow> books = {
        makeRow(0, HouseShopLedgerCategory::Books, "Fire Magic - Normal", 100),
        makeRow(1, HouseShopLedgerCategory::Books, "Air Magic - Normal", 100),
        makeRow(2, HouseShopLedgerCategory::Books, "Fire Magic - Expert", 500),
    };
    books[0].school = HouseShopLedgerCategory::FireBooks;
    books[0].spellNumber = 1;
    books[1].school = HouseShopLedgerCategory::AirBooks;
    books[1].spellNumber = 12;
    books[2].school = HouseShopLedgerCategory::FireBooks;
    books[2].spellNumber = 5;
    sortHouseShopLedgerRows(books, {Key::Type, false});
    CHECK(books[0].stockIndices.front() == 0);
    CHECK(books[1].stockIndices.front() == 2);
    CHECK(books[2].stockIndices.front() == 1);

    const GameplayResolvedHudLayoutElement frame = {100.0f, 56.0f, 920.0f, 676.0f, 2.0f};
    const HouseShopLedgerLayout layout = buildHouseShopLedgerLayout(frame);
    const HouseShopLedgerColumnRects columns = houseShopLedgerColumnRects(layout);
    const float headingY = layout.columns.y + 2.0f;
    CHECK(houseShopLedgerColumnAt(layout, columns.wares.x + 4.0f, headingY) == Key::Type);
    CHECK(houseShopLedgerColumnAt(layout, columns.price.x + columns.price.width - 4.0f, headingY) == Key::Price);
    CHECK_FALSE(houseShopLedgerColumnAt(layout, columns.stat.x + 4.0f, headingY).has_value());
    CHECK_FALSE(houseShopLedgerColumnAt(layout, columns.wares.x + 4.0f, layout.list.y + 4.0f).has_value());
    CHECK(columns.price.x + columns.price.width <= layout.list.x + layout.list.width);
    CHECK(columns.wares.x + columns.wares.width <= columns.stat.x);
}

TEST_CASE("vendor rows choose the ledger or the shelf buy view")
{
    const auto load = [](const std::string &buyView, std::string &error)
    {
        // A weapon shop's pages hold six slots.
        std::vector<std::vector<std::string>> stockRows;
        for (const char *pLane : {"standard", "special"})
        {
            for (int slot = 0; slot < 6; ++slot)
            {
                stockRows.push_back({"30010", pLane, "0", std::to_string(slot), "10001", "1", "1", "0", "0", "0",
                    "1"});
            }
        }
        HouseTable table;
        const bool loaded =
            table.appendVendorRows({vendorRow(buyView)}, {{"30010", "mm9", "10", "2"}}, stockRows, error);
        return loaded && table.get(30010) != nullptr ? std::optional<ShopBuyView>(table.get(30010)->shopBuyView)
                                                      : std::nullopt;
    };
    std::string error;
    CHECK(load("Ledger", error) == ShopBuyView::Ledger);
    CHECK(load("Shelf", error) == ShopBuyView::Shelf);
    CHECK(load("", error) == ShopBuyView::Shelf);
    CHECK_FALSE(load("Grid", error).has_value());
    CHECK(error.find("buy_view") != std::string::npos);
}

TEST_CASE("MM9 venues teach the skills of their learn_skills column")
{
    std::string error;
    std::vector<std::string> row = vendorRow("Ledger");
    row.push_back("Sword|Axe|Staff");
    std::vector<std::vector<std::string>> stockRows;
    for (const char *pLane : {"standard", "special"})
    {
        for (int slot = 0; slot < 6; ++slot)
        {
            stockRows.push_back({"30010", pLane, "0", std::to_string(slot), "10001", "1", "1", "0", "0", "0", "1"});
        }
    }
    HouseTable table;
    REQUIRE_MESSAGE(table.appendVendorRows({row}, {{"30010", "mm9", "10", "2"}}, stockRows, error), error);
    REQUIRE(table.get(30010) != nullptr);
    CHECK(table.get(30010)->offeredSkills == std::vector<std::string> {"Sword", "Axe", "Staff"});
    const std::vector<HouseActionOption> options =
        buildHouseActionOptions(*table.get(30010), nullptr, nullptr, nullptr, 0.0f, DialogueMenuId::None);
    CHECK(std::any_of(options.begin(), options.end(), [](const HouseActionOption &option)
        {
            return option.id == HouseActionId::OpenLearnSkillsMenu;
        }));

    // MM9's composite names, unknown and repeated skills are refused
    for (const char *pBad : {"Blade", "Sword|Sword", "Sword|Nothing"})
    {
        row.back() = pBad;
        HouseTable badTable;
        CHECK_FALSE(badTable.appendVendorRows({row}, {{"30010", "mm9", "10", "2"}}, stockRows, error));
        CHECK(error.find("learn_skills") != std::string::npos);
    }

    std::vector<std::string> venue = {"30016", "mm9", "16", "mm9:service/16", "The Tree of Life", "Thjorgard",
        "Temple", "3", "0", "0", "1", "1", "1", "LiveGameplay", "RudeQuestKey", "8", "Regeneration|Meditation"};
    HouseTable venueTable;
    REQUIRE_MESSAGE(venueTable.appendServiceVenueRows({venue}, {{"30016", "mm9", "16", "8"}}, error), error);
    CHECK(venueTable.get(30016)->serviceCanLearnSkills);
    CHECK(venueTable.get(30016)->offeredSkills == std::vector<std::string> {"Regeneration", "Meditation"});
    venue[12] = "0";
    HouseTable mismatchTable;
    CHECK_FALSE(mismatchTable.appendServiceVenueRows({venue}, {{"30016", "mm9", "16", "8"}}, error));
}

TEST_CASE("ledger vendors may sell from one list of any length")
{
    const auto load = [](const std::string &buyView, int slotCount, bool withSpecial, std::string &error)
    {
        std::vector<std::vector<std::string>> stockRows;
        for (const char *pLane : {"standard", "special"})
        {
            if (std::string(pLane) == "special" && !withSpecial)
            {
                continue;
            }
            for (int slot = 0; slot < slotCount; ++slot)
            {
                stockRows.push_back({"30010", pLane, "0", std::to_string(slot), "10001", "1", "1", "0", "0", "0",
                    "2"});
            }
        }
        HouseTable table;
        return table.appendVendorRows({vendorRow(buyView)}, {{"30010", "mm9", "10", "2"}}, stockRows, error)
            ? std::optional<size_t>(table.get(30010)->deterministicStandardStockPages.front().items.size())
            : std::nullopt;
    };
    std::string error;
    // MM9's restock: 30 rolls in one list, no Special pages.
    CHECK(load("Ledger", 30, false, error) == 30);
    // A shelf keeps its fixed slots and both lists.
    CHECK_FALSE(load("Shelf", 30, true, error).has_value());
    CHECK_FALSE(load("Shelf", 6, false, error).has_value());
    CHECK(load("Shelf", 6, true, error) == 6);
    CHECK_FALSE(load("Ledger", 65, false, error).has_value());
}
