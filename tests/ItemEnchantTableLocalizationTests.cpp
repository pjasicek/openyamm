#include "doctest/doctest.h"

#include "game/items/ItemEnchantTables.h"

#include <string>
#include <vector>

TEST_CASE("localized standard enchant text keeps canonical gameplay kind")
{
    const std::vector<std::vector<std::string>> semanticRows = {
        {"Might", "of Might", "5", "0", "0", "0", "0", "0", "0", "0", "0"},
    };
    const std::vector<std::vector<std::string>> localizedRows = {
        {"Сила", "могущества", "5", "0", "0", "0", "0", "0", "0", "0", "0"},
    };
    OpenYAMM::Game::StandardItemEnchantTable table;

    REQUIRE(table.load(localizedRows, semanticRows));
    REQUIRE_EQ(table.entries().size(), 1);
    CHECK_EQ(table.entries()[0].kind, OpenYAMM::Game::StandardItemEnchantKind::Might);
    CHECK_EQ(table.entries()[0].statName, "Сила");
    CHECK_EQ(table.entries()[0].suffix, "могущества");
}

TEST_CASE("localized special enchant text keeps canonical behavior and placement")
{
    std::vector<std::string> semanticRow(17);
    semanticRow[0] = "Adds 3-4 points of Cold damage.";
    semanticRow[1] = "of Cold";
    semanticRow[2] = "20";
    semanticRow[14] = "500";
    semanticRow[15] = "A";
    semanticRow[16] = "(3-4) cold damage";
    std::vector<std::string> localizedRow = semanticRow;
    localizedRow[0] = "Добавляет 3–4 единицы урона от холода.";
    localizedRow[1] = "холода";
    localizedRow[16] = "3–4 урона от холода.";
    OpenYAMM::Game::SpecialItemEnchantTable table;

    REQUIRE(table.load({localizedRow}, {semanticRow}));
    REQUIRE_EQ(table.entries().size(), 1);
    CHECK_EQ(table.entries()[0].kind, OpenYAMM::Game::SpecialItemEnchantKind::Cold);
    CHECK_EQ(table.entries()[0].suffix, "холода");
    CHECK_FALSE(table.entries()[0].displayAsPrefix);
}
