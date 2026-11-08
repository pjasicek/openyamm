#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/maps/MapIdentity.h"
#include "game/maps/MapRegistry.h"
#include "game/StringUtils.h"
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

struct ExpectedEdge
{
    const char *pDestination = nullptr;
    int travelDays = 0;
    OpenYAMM::Game::MapBoundaryEdge arrivalSide = OpenYAMM::Game::MapBoundaryEdge::North;
};

void checkEdge(const std::optional<OpenYAMM::Game::MapEdgeTransition> &transition, const ExpectedEdge &expected)
{
    if (expected.pDestination == nullptr)
    {
        CHECK_FALSE(transition.has_value());
        return;
    }

    REQUIRE(transition.has_value());
    CHECK_EQ(transition->destinationMapFileName, expected.pDestination);
    CHECK_EQ(transition->travelDays, expected.travelDays);
    CHECK(transition->useMapStartPosition);
    CHECK_FALSE(transition->straightTravel);
    REQUIRE(transition->arrivalSide.has_value());
    CHECK_EQ(*transition->arrivalSide, expected.arrivalSide);
}
}

TEST_CASE("mm8 foot travel matches the original executable table")
{
    using OpenYAMM::Game::MapBoundaryEdge;

    struct ExpectedMapTransitions
    {
        const char *pFileName = nullptr;
        ExpectedEdge north;
        ExpectedEdge south;
        ExpectedEdge east;
        ExpectedEdge west;
    };

    // Destination, base days and arrival start point of each edge, from the foot travel tables of MM8-Rel.exe
    // (destinations at 0x4fe95b, days and arrival sides 0x34 and 0x68 bytes later).
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    static constexpr ExpectedEdge None = {};
    static constexpr std::array<ExpectedMapTransitions, 9> ExpectedMaps = {{
        {"out01.odm", None, None, None, None},
        {"out02.odm",
            {"out03.odm", 5, MapBoundaryEdge::South},
            {"out06.odm", 10, MapBoundaryEdge::West},
            {"out06.odm", 5, MapBoundaryEdge::West},
            {"out05.odm", 5, MapBoundaryEdge::East}},
        {"out03.odm",
            {"out04.odm", 10, MapBoundaryEdge::West},
            {"out02.odm", 5, MapBoundaryEdge::North},
            {"out04.odm", 5, MapBoundaryEdge::West},
            {"out07.odm", 5, MapBoundaryEdge::East}},
        {"out04.odm",
            {"out03.odm", 10, MapBoundaryEdge::North},
            {"out06.odm", 5, MapBoundaryEdge::North},
            {"out06.odm", 10, MapBoundaryEdge::East},
            {"out03.odm", 5, MapBoundaryEdge::East}},
        {"out05.odm",
            {"out07.odm", 5, MapBoundaryEdge::South},
            {"out08.odm", 5, MapBoundaryEdge::North},
            {"out02.odm", 5, MapBoundaryEdge::West},
            {"out08.odm", 10, MapBoundaryEdge::North}},
        {"out06.odm",
            {"out04.odm", 5, MapBoundaryEdge::South},
            {"out02.odm", 10, MapBoundaryEdge::East},
            {"out04.odm", 10, MapBoundaryEdge::South},
            {"out02.odm", 5, MapBoundaryEdge::East}},
        {"out07.odm",
            {"out03.odm", 10, MapBoundaryEdge::North},
            {"out05.odm", 5, MapBoundaryEdge::North},
            {"out03.odm", 5, MapBoundaryEdge::West},
            {"out05.odm", 10, MapBoundaryEdge::West}},
        {"out08.odm",
            {"out05.odm", 5, MapBoundaryEdge::South},
            {"out05.odm", 15, MapBoundaryEdge::South},
            {"out05.odm", 10, MapBoundaryEdge::South},
            {"out05.odm", 10, MapBoundaryEdge::South}},
        {"out13.odm", None, None, None, None},
    }};

    for (const ExpectedMapTransitions &expected : ExpectedMaps)
    {
        INFO("map=" << expected.pFileName);
        const OpenYAMM::Game::MapStatsEntry *pEntry = mapStats.findByFileName(expected.pFileName);
        REQUIRE(pEntry != nullptr);
        checkEdge(pEntry->northTransition, expected.north);
        checkEdge(pEntry->southTransition, expected.south);
        checkEdge(pEntry->eastTransition, expected.east);
        checkEdge(pEntry->westTransition, expected.west);
    }
}

TEST_CASE("all legacy outdoor maps declare movement bounds independently of transitions")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    size_t mm6OutdoorCount = 0;
    size_t mm7OutdoorCount = 0;
    size_t mm8OutdoorCount = 0;

    for (const OpenYAMM::Game::MapStatsEntry &entry : mapStats.getEntries())
    {
        if (!OpenYAMM::Game::toLowerCopy(entry.fileName).ends_with(".odm"))
        {
            continue;
        }

        size_t *pWorldOutdoorCount = nullptr;

        if (entry.worldId == "mm6")
        {
            pWorldOutdoorCount = &mm6OutdoorCount;
        }
        else if (entry.worldId == "mm7")
        {
            pWorldOutdoorCount = &mm7OutdoorCount;
        }
        else if (entry.worldId == "mm8")
        {
            pWorldOutdoorCount = &mm8OutdoorCount;
        }

        if (pWorldOutdoorCount == nullptr)
        {
            continue;
        }

        ++*pWorldOutdoorCount;
        INFO("map=" << entry.fileName << " world=" << entry.worldId);
        CHECK(entry.outdoorBounds.enabled);
        CHECK_LT(entry.outdoorBounds.minX, entry.outdoorBounds.maxX);
        CHECK_LT(entry.outdoorBounds.minY, entry.outdoorBounds.maxY);
    }

    CHECK_EQ(mm6OutdoorCount, 15u);
    CHECK_EQ(mm7OutdoorCount, 13u);
    CHECK_EQ(mm8OutdoorCount, 14u);

    const OpenYAMM::Game::MapStatsEntry *pEmeraldIsland = mapStats.findByFileName("7out01.odm");
    REQUIRE(pEmeraldIsland != nullptr);
    CHECK(pEmeraldIsland->outdoorBounds.enabled);
    CHECK_FALSE(pEmeraldIsland->northTransition.has_value());
    CHECK_FALSE(pEmeraldIsland->southTransition.has_value());
    CHECK_FALSE(pEmeraldIsland->eastTransition.has_value());
    CHECK_FALSE(pEmeraldIsland->westTransition.has_value());
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

TEST_CASE("MM9 map music uses globally unique world track ids")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pRavensford = mapStats.findByFileName("bootcamp.blv");

    REQUIRE(pRavensford != nullptr);
    CHECK_EQ(pRavensford->worldId, "mm9");
    // MAPSTATS Music Track N plays MM9-Song(N-1), track 90000 + N - 1 (MM9_AMBIENT_AUDIO_RE.md section 2): Ravensford's
    // 7 is Song06.
    CHECK_EQ(pRavensford->redbookTrack, 90006);

    // Thousand Terrors' 18 is Song17; Temple of Honk (blank: MM9 keeps the song it was entered with) has Guberland's.
    const OpenYAMM::Game::MapStatsEntry *pThousandTerrors = mapStats.findByFileName("1000terrors.blv");
    const OpenYAMM::Game::MapStatsEntry *pTempleOfHonk = mapStats.findByFileName("templeofhonk.blv");
    REQUIRE(pThousandTerrors != nullptr);
    REQUIRE(pTempleOfHonk != nullptr);
    CHECK_EQ(pThousandTerrors->redbookTrack, 90017);
    CHECK_EQ(pTempleOfHonk->redbookTrack, 90006);
}

TEST_CASE("MM6 named locations use their fixed soundtrack assignments")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    struct ExpectedTrack
    {
        const char *pMapFileName;
        int track;
    };

    constexpr std::array<ExpectedTrack, 13> ExpectedTracks = {{
        {"outa1.odm", 40}, // Sweet Water
        {"outb3.odm", 41}, // Dragonsand
        {"outc1.odm", 47}, // Frozen Highlands
        {"outc2.odm", 51}, // Free Haven
        {"outc3.odm", 48}, // Mire of the Damned
        {"outd1.odm", 39}, // Silver Cove
        {"outd3.odm", 38}, // Castle Ironfist
        {"oute3.odm", 37}, // New Sorpigal
        {"6d15.blv", 43}, // Icewind Keep
        {"6d17.blv", 42}, // Lair of the Wolf
        {"6t6.blv", 50}, // Supreme Temple of Baa
        {"cd3.blv", 49}, // Castle Kriegspire
        {"pyramid.blv", 46}, // Tomb of VARN
    }};

    for (const ExpectedTrack &expected : ExpectedTracks)
    {
        const OpenYAMM::Game::MapStatsEntry *pMap = mapStats.findByFileName(expected.pMapFileName);
        REQUIRE(pMap != nullptr);
        CHECK_EQ(pMap->redbookTrack, expected.track);
    }
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
    REQUIRE(pNewSorpigal->westTransition->arrivalSide.has_value());
    CHECK_EQ(*pNewSorpigal->westTransition->arrivalSide, OpenYAMM::Game::MapBoundaryEdge::East);
    CHECK_FALSE(pNewSorpigal->westTransition->directionDegrees.has_value());
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

TEST_CASE("map stats assign default canonical MM8 map identity")
{
    const OpenYAMM::Game::MapStats mapStats = loadMapStats();
    const OpenYAMM::Game::MapStatsEntry *pDaggerWound = mapStats.findByFileName("Out01.odm");
    const OpenYAMM::Game::MapStatsEntry *pMountNighon = mapStats.findByFileName("out10.odm");
    const OpenYAMM::Game::MapStatsEntry *pLandOfTheGiants = mapStats.findByFileName("out12.odm");
    const OpenYAMM::Game::MapStatsEntry *pErathianSewers = mapStats.findByFileName("d01.blv");
    const OpenYAMM::Game::MapStatsEntry *pBarrowXiv = mapStats.findByFileName("mdk04.blv");
    const OpenYAMM::Game::MapStatsEntry *pTempleOfTheDark = mapStats.findByFileName("t02.blv");

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

    CHECK(mapStats.findByFileName("Breach.odm") == nullptr);
    CHECK(mapStats.findByFileName("BrBase.blv") == nullptr);
    CHECK(mapStats.findByFileName("BrAlvar.odm") == nullptr);
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
    OpenYAMM::Game::MapStats mapStats = {};
    REQUIRE(mapStats.loadFromRows(loadTextTableRows("assets_dev/engine/data_tables/map_stats.txt")));

    // North edge with an explicit arrival position, east edge without one, south and west edges unused.
    const std::vector<std::vector<std::string>> navigationRows = {{
        "Out02.odm", "-23143", "23143", "-23143", "23143",
        "Out03.odm", "1", "0",
        "0", "0", "0",
        "Out06.odm", "1", "0",
        "0", "0", "0",
        "-15104", "-22200", "192",
    }};
    REQUIRE(mapStats.applyOutdoorNavigationRows(navigationRows));

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
    CHECK_FALSE(pRavenshore->westTransition.has_value());

    REQUIRE(pRavenshore->eastTransition.has_value());
    CHECK_EQ(pRavenshore->eastTransition->destinationMapFileName, "Out06.odm");
    CHECK(pRavenshore->eastTransition->useMapStartPosition);
    CHECK_FALSE(pRavenshore->eastTransition->arrivalX.has_value());
}
