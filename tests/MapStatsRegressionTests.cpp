#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/MapRegistry.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

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
    REQUIRE(mapStats.loadFromRows(loadTextTableRows("assets_dev/engine/data_tables/map_stats.txt")));
    REQUIRE(mapStats.applyOutdoorNavigationRows(
        loadTextTableRows("assets_dev/engine/data_tables/map_navigation.txt")));

    OpenYAMM::Game::MergedBolsterMapTable bolsterMaps = {};
    REQUIRE(bolsterMaps.loadFromRows(loadTextTableRows("assets_dev/engine/data_tables/bolster_maps.txt")));
    REQUIRE(mapStats.applyMergedBolsterMaps(bolsterMaps));

    OpenYAMM::Game::MergedOutdoorTravelTable outdoorTravels = {};
    REQUIRE(outdoorTravels.loadFromRows(loadTextTableRows("assets_dev/engine/data_tables/outdoor_travels.txt")));
    REQUIRE(mapStats.applyMergedOutdoorTravels(outdoorTravels));
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

TEST_CASE("map stats parse refill days")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pIronsand = mapStats.findByFileName("out04.odm");
    const OpenYAMM::Game::MapStatsEntry *pCastleHarmondale = mapStats.findByFileName("7d29.blv");

    REQUIRE(pDaggerWound != nullptr);
    REQUIRE(pIronsand != nullptr);
    REQUIRE(pCastleHarmondale != nullptr);
    CHECK_EQ(pDaggerWound->respawnIntervalDays, 672);
    CHECK_EQ(pIronsand->respawnIntervalDays, 336);
    CHECK_EQ(pCastleHarmondale->respawnIntervalDays, -1);
}

TEST_CASE("map stats normalize non-audio redbook track")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pEscatonsPalace = mapStats.findByFileName("d35.blv");

    REQUIRE(pEscatonsPalace != nullptr);
    CHECK_EQ(pEscatonsPalace->redbookTrack, 0);
}

TEST_CASE("map stats parse base stealing fine")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pRavenshore = mapStats.findByFileName("Out02.odm");

    REQUIRE(pDaggerWound != nullptr);
    REQUIRE(pRavenshore != nullptr);
    CHECK_EQ(pDaggerWound->baseStealingFine, 1);
    CHECK_EQ(pRavenshore->baseStealingFine, 2);
}

TEST_CASE("merged bolster map metadata marks Antagarich outdoor maps")
{
    OpenYAMM::Game::MergedBolsterMapTable bolsterMaps = {};
    REQUIRE(bolsterMaps.loadFromRows(loadTextTableRows("assets_dev/engine/data_tables/bolster_maps.txt")));

    const OpenYAMM::Game::MergedBolsterMapEntry *pTulareanForest = bolsterMaps.findById(65u);
    REQUIRE(pTulareanForest != nullptr);
    CHECK_EQ(pTulareanForest->note, "The Tularean Forest");
    CHECK_EQ(pTulareanForest->continent, 2u);
    CHECK_EQ(pTulareanForest->bolsterKind, "LowerToEqual");
    CHECK(pTulareanForest->spells);
    CHECK(pTulareanForest->summons);
    CHECK(pTulareanForest->weather);
    REQUIRE(pTulareanForest->professionMaxRarity.has_value());
    CHECK_EQ(*pTulareanForest->professionMaxRarity, 30u);

    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pEmeraldIsland = mapStats.findByFileName("7out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pHarmondale = mapStats.findByFileName("7out02.odm");
    const OpenYAMM::Game::MapStatsEntry *pTulareanMap = mapStats.findByFileName("7out04.odm");

    REQUIRE(pEmeraldIsland != nullptr);
    REQUIRE(pHarmondale != nullptr);
    REQUIRE(pTulareanMap != nullptr);
    CHECK_EQ(pEmeraldIsland->mergedContinentId, 2u);
    CHECK_EQ(pHarmondale->mergedContinentId, 2u);
    CHECK_EQ(pTulareanMap->mergedContinentId, 2u);
}

TEST_CASE("merged outdoor travels add mm6 map boundary transitions")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pNewSorpigal = mapStats.findByFileName("oute3.odm");

    REQUIRE(pNewSorpigal != nullptr);
    CHECK(pNewSorpigal->outdoorBounds.enabled);
    CHECK_EQ(pNewSorpigal->outdoorBounds.minX, -23143);
    CHECK_EQ(pNewSorpigal->outdoorBounds.maxX, 23143);
    CHECK_EQ(pNewSorpigal->outdoorBounds.minY, -23143);
    CHECK_EQ(pNewSorpigal->outdoorBounds.maxY, 23143);
    CHECK_FALSE(pNewSorpigal->northTransition.has_value());
    CHECK_FALSE(pNewSorpigal->southTransition.has_value());
    CHECK_FALSE(pNewSorpigal->eastTransition.has_value());
    REQUIRE(pNewSorpigal->westTransition.has_value());
    CHECK_EQ(pNewSorpigal->westTransition->destinationMapFileName, "outd3.odm");
    CHECK_EQ(pNewSorpigal->westTransition->travelDays, 5);
    CHECK_FALSE(pNewSorpigal->westTransition->useMapStartPosition);
    CHECK(pNewSorpigal->westTransition->straightTravel);
    REQUIRE(pNewSorpigal->westTransition->straightTravelSide.has_value());
    CHECK_EQ(*pNewSorpigal->westTransition->straightTravelSide, OpenYAMM::Game::MapBoundaryEdge::West);
    REQUIRE(pNewSorpigal->westTransition->directionDegrees.has_value());
    CHECK_EQ(*pNewSorpigal->westTransition->directionDegrees, 180);
}

TEST_CASE("merged outdoor travels add Avlee Shoals special transition")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pAvlee = mapStats.findByFileName("out14.odm");

    REQUIRE(pAvlee != nullptr);
    REQUIRE(pAvlee->westTransition.has_value());
    CHECK_EQ(pAvlee->westTransition->destinationMapFileName, "7out15.odm");
    CHECK_EQ(pAvlee->westTransition->travelDays, 0);
    CHECK_EQ(
        pAvlee->westTransition->requiredOriginSurface,
        OpenYAMM::Game::MapTransitionSurfaceRequirement::Water);
    REQUIRE_EQ(pAvlee->westTransition->requiredQuestBitsAny.size(), 3u);
    CHECK_EQ(pAvlee->westTransition->requiredQuestBitsAny[0], 642u);
    CHECK_EQ(pAvlee->westTransition->requiredQuestBitsAny[1], 643u);
    CHECK_EQ(pAvlee->westTransition->requiredQuestBitsAny[2], 783u);
}

TEST_CASE("merged outdoor travels preserve original mm8 boundary transitions")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pRavenshore = mapStats.findByFileName("out02.odm");
    const OpenYAMM::Game::MapStatsEntry *pAlvar = mapStats.findByFileName("out03.odm");
    const OpenYAMM::Game::MapStatsEntry *pShadowspire = mapStats.findByFileName("out06.odm");

    REQUIRE(pRavenshore != nullptr);
    REQUIRE(pAlvar != nullptr);
    REQUIRE(pShadowspire != nullptr);

    REQUIRE(pRavenshore->northTransition.has_value());
    CHECK_EQ(pRavenshore->northTransition->destinationMapFileName, "Out03.odm");
    CHECK_EQ(pRavenshore->northTransition->travelDays, 1);
    REQUIRE(pRavenshore->northTransition->arrivalX.has_value());
    CHECK_EQ(*pRavenshore->northTransition->arrivalX, -15104);
    REQUIRE(pRavenshore->eastTransition.has_value());
    CHECK_EQ(pRavenshore->eastTransition->destinationMapFileName, "Out06.odm");
    CHECK_EQ(pRavenshore->eastTransition->travelDays, 1);
    REQUIRE(pRavenshore->westTransition.has_value());
    CHECK_EQ(pRavenshore->westTransition->destinationMapFileName, "Out05.odm");
    CHECK_EQ(pRavenshore->westTransition->travelDays, 1);

    REQUIRE(pAlvar->westTransition.has_value());
    CHECK_EQ(pAlvar->westTransition->destinationMapFileName, "Out04.odm");
    CHECK_EQ(pAlvar->westTransition->travelDays, 1);
    REQUIRE(pShadowspire->westTransition.has_value());
    CHECK_EQ(pShadowspire->westTransition->destinationMapFileName, "Out02.odm");
    CHECK_EQ(pShadowspire->westTransition->travelDays, 1);
}

TEST_CASE("map stats assign default canonical MM8 map identity")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pMountNighon = mapStats.findByFileName("out10.odm");
    const OpenYAMM::Game::MapStatsEntry *pLandOfTheGiants = mapStats.findByFileName("out12.odm");
    const OpenYAMM::Game::MapStatsEntry *pErathianSewers = mapStats.findByFileName("d01.blv");
    const OpenYAMM::Game::MapStatsEntry *pBarrowXiv = mapStats.findByFileName("mdk04.blv");
    const OpenYAMM::Game::MapStatsEntry *pTempleOfTheDark = mapStats.findByFileName("t02.blv");
    const OpenYAMM::Game::MapStatsEntry *pBreach = mapStats.findByFileName("Breach.odm");
    const OpenYAMM::Game::MapStatsEntry *pBrAlvar = mapStats.findByFileName("BrAlvar.odm");
    const OpenYAMM::Game::MapStatsEntry *pBrBase = mapStats.findByFileName("BrBase.blv");

    REQUIRE(pDaggerWound != nullptr);
    CHECK_EQ(pDaggerWound->worldId, OpenYAMM::Game::DefaultWorldId);
    CHECK_EQ(pDaggerWound->canonicalId, "world.mm8.map.out01");

    REQUIRE(pMountNighon != nullptr);
    REQUIRE(pLandOfTheGiants != nullptr);
    CHECK_EQ(pMountNighon->worldId, "mm7");
    CHECK_EQ(pMountNighon->canonicalId, "world.mm7.map.out10");
    CHECK_EQ(pLandOfTheGiants->worldId, "mm7");
    CHECK_EQ(pLandOfTheGiants->canonicalId, "world.mm7.map.out12");

    REQUIRE(pErathianSewers != nullptr);
    REQUIRE(pBarrowXiv != nullptr);
    REQUIRE(pTempleOfTheDark != nullptr);
    CHECK_EQ(pErathianSewers->worldId, "mm7");
    CHECK_EQ(pErathianSewers->canonicalId, "world.mm7.map.d01");
    CHECK_EQ(pBarrowXiv->worldId, "mm7");
    CHECK_EQ(pBarrowXiv->canonicalId, "world.mm7.map.mdk04");
    CHECK_EQ(pTempleOfTheDark->worldId, "mm7");
    CHECK_EQ(pTempleOfTheDark->canonicalId, "world.mm7.map.t02");

    REQUIRE(pBreach != nullptr);
    REQUIRE(pBrAlvar != nullptr);
    REQUIRE(pBrBase != nullptr);
    CHECK_EQ(pBreach->worldId, "mmmerge");
    CHECK_EQ(pBreach->canonicalId, "world.mmmerge.map.breach");
    CHECK_EQ(pBrAlvar->worldId, "mmmerge");
    CHECK_EQ(pBrBase->worldId, "mmmerge");
}

TEST_CASE("map registry supports canonical id and world/file compatibility lookups")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    OpenYAMM::Game::MapRegistry registry = {};
    registry.initialize(mapStats.getEntries());

    const std::optional<OpenYAMM::Game::MapStatsEntry> canonicalEntry =
        registry.findByCanonicalId("WORLD.MM8.MAP.OUT01");
    REQUIRE(canonicalEntry.has_value());
    CHECK_EQ(canonicalEntry->fileName, "out01.odm");

    const std::optional<OpenYAMM::Game::MapStatsEntry> worldFileEntry =
        registry.findByWorldAndFileName("mm8", "out01.ODM");
    REQUIRE(worldFileEntry.has_value());
    CHECK_EQ(worldFileEntry->canonicalId, "world.mm8.map.out01");

    CHECK_FALSE(registry.findByWorldAndFileName("mm6", "out01.odm").has_value());

    const std::optional<OpenYAMM::Game::MapStatsEntry> mm6Entry =
        registry.findByWorldAndFileName("mm6", "oute3.odm");
    REQUIRE(mm6Entry.has_value());
    CHECK_EQ(mm6Entry->canonicalId, "world.mm6.map.oute3");

    const std::optional<OpenYAMM::Game::MapStatsEntry> mm7Entry =
        registry.findByWorldAndFileName("mm7", "7out01.odm");
    REQUIRE(mm7Entry.has_value());
    CHECK_EQ(mm7Entry->canonicalId, "world.mm7.map.7out01");
    CHECK_EQ(mm7Entry->mergedContinentId, 2u);
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
