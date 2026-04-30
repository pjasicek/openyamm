#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/tables/MapStats.h"

#include <array>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace
{
std::vector<std::vector<std::string>> loadTextTableRows(const std::string &relativePath)
{
    const std::string path = std::string(OPENYAMM_SOURCE_DIR) + "/" + relativePath;
    std::ifstream file(path);
    REQUIRE(file.is_open());

    const std::string contents{
        std::istreambuf_iterator<char>(file),
        std::istreambuf_iterator<char>()};
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(contents);
    REQUIRE(table.has_value());

    std::vector<std::vector<std::string>> rows;
    rows.reserve(table->getRowCount());

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return rows;
}

OpenYAMM::Game::MapStats loadMapStats()
{
    OpenYAMM::Game::MapStats mapStats = {};
    REQUIRE(mapStats.loadFromRows(loadTextTableRows("assets_dev/Data/data_tables/map_stats.txt")));
    REQUIRE(mapStats.applyOutdoorNavigationRows(
        loadTextTableRows("assets_dev/Data/data_tables/map_navigation.txt")));
    return mapStats;
}

void checkTransition(
    const std::optional<OpenYAMM::Game::MapEdgeTransition> &transition,
    const char *pExpectedDestination)
{
    if (pExpectedDestination == nullptr)
    {
        CHECK_FALSE(transition.has_value());
        return;
    }

    REQUIRE(transition.has_value());
    CHECK_EQ(transition->destinationMapFileName, pExpectedDestination);
}
}

TEST_CASE("map navigation matches authoritative world map")
{
    struct ExpectedMapTransitions
    {
        const char *pFileName = nullptr;
        const char *pNorth = nullptr;
        const char *pSouth = nullptr;
        const char *pEast = nullptr;
        const char *pWest = nullptr;
    };

    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    static constexpr std::array<ExpectedMapTransitions, 9> ExpectedMaps = {{
        {"Out01.odm", nullptr, nullptr, nullptr, nullptr},
        {"Out02.odm", "Out03.odm", nullptr, "Out06.odm", "Out05.odm"},
        {"Out03.odm", nullptr, "Out02.odm", "Out07.odm", "Out04.odm"},
        {"Out04.odm", nullptr, "Out05.odm", "Out03.odm", nullptr},
        {"Out05.odm", "Out04.odm", "Out08.odm", "Out02.odm", nullptr},
        {"Out06.odm", "Out07.odm", nullptr, nullptr, "Out02.odm"},
        {"Out07.odm", nullptr, "Out06.odm", nullptr, "Out03.odm"},
        {"Out08.odm", "Out05.odm", nullptr, nullptr, nullptr},
        {"Out13.odm", nullptr, nullptr, nullptr, nullptr},
    }};

    for (const ExpectedMapTransitions &expected : ExpectedMaps)
    {
        const OpenYAMM::Game::MapStatsEntry *pEntry = mapStats.findByFileName(expected.pFileName);
        REQUIRE(pEntry != nullptr);
        checkTransition(pEntry->northTransition, expected.pNorth);
        checkTransition(pEntry->southTransition, expected.pSouth);
        checkTransition(pEntry->eastTransition, expected.pEast);
        checkTransition(pEntry->westTransition, expected.pWest);
    }
}

TEST_CASE("map stats parse perception difficulty")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pRavenshore = mapStats.findByFileName("Out02.odm");

    REQUIRE(pDaggerWound != nullptr);
    REQUIRE(pRavenshore != nullptr);
    CHECK_EQ(pDaggerWound->perceptionDifficulty, 0);
    CHECK_EQ(pRavenshore->perceptionDifficulty, 1);
}

TEST_CASE("map stats parse chest trap difficulty and damage dice")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pRavenshore = mapStats.findByFileName("Out02.odm");

    REQUIRE(pDaggerWound != nullptr);
    REQUIRE(pRavenshore != nullptr);
    CHECK_EQ(pDaggerWound->disarmDifficulty, 0);
    CHECK_EQ(pDaggerWound->trapDamageD20DiceCount, 0);
    CHECK_EQ(pRavenshore->disarmDifficulty, 1);
    CHECK_EQ(pRavenshore->trapDamageD20DiceCount, 1);
}

TEST_CASE("map navigation rows apply explicit arrival positions")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pRavenshore = mapStats.findByFileName("Out02.odm");
    REQUIRE(pRavenshore != nullptr);

    REQUIRE(pRavenshore->northTransition.has_value());
    CHECK_EQ(pRavenshore->northTransition->destinationMapFileName, "Out03.odm");
    CHECK_FALSE(pRavenshore->northTransition->useMapStartPosition);
    REQUIRE(pRavenshore->northTransition->arrivalX.has_value());
    REQUIRE(pRavenshore->northTransition->arrivalY.has_value());
    REQUIRE(pRavenshore->northTransition->arrivalZ.has_value());
    CHECK_EQ(*pRavenshore->northTransition->arrivalX, -15104);
    CHECK_EQ(*pRavenshore->northTransition->arrivalY, -22200);
    CHECK_EQ(*pRavenshore->northTransition->arrivalZ, 192);

    CHECK_FALSE(pRavenshore->southTransition.has_value());

    REQUIRE(pRavenshore->eastTransition.has_value());
    CHECK_EQ(pRavenshore->eastTransition->destinationMapFileName, "Out06.odm");
    CHECK_FALSE(pRavenshore->eastTransition->useMapStartPosition);
    REQUIRE(pRavenshore->eastTransition->arrivalX.has_value());
    REQUIRE(pRavenshore->eastTransition->arrivalY.has_value());
    REQUIRE(pRavenshore->eastTransition->arrivalZ.has_value());
    CHECK_EQ(*pRavenshore->eastTransition->arrivalX, -22080);
    CHECK_EQ(*pRavenshore->eastTransition->arrivalY, -5776);
    CHECK_EQ(*pRavenshore->eastTransition->arrivalZ, 480);

    REQUIRE(pRavenshore->westTransition.has_value());
    CHECK_EQ(pRavenshore->westTransition->destinationMapFileName, "Out05.odm");
    CHECK_FALSE(pRavenshore->westTransition->useMapStartPosition);
    REQUIRE(pRavenshore->westTransition->arrivalX.has_value());
    REQUIRE(pRavenshore->westTransition->arrivalY.has_value());
    REQUIRE(pRavenshore->westTransition->arrivalZ.has_value());
    CHECK_EQ(*pRavenshore->westTransition->arrivalX, 22096);
    CHECK_EQ(*pRavenshore->westTransition->arrivalY, 296);
    CHECK_EQ(*pRavenshore->westTransition->arrivalZ, 360);
}
