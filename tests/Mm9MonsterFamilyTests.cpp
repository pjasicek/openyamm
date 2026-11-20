#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <string>

namespace
{
void checkFamilyTiers(
    const OpenYAMM::Game::MonsterTable &monsterTable,
    const std::string &pictureBase,
    const std::array<int16_t, 3> &expectedIds,
    size_t tierCount)
{
    const std::array<char, 3> letters = {'A', 'B', 'C'};

    for (size_t tier = 0; tier < letters.size(); ++tier)
    {
        const std::string picture = pictureBase + " " + std::string(1, letters[tier]);
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsByPictureName(picture);

        if (tier >= tierCount)
        {
            CHECK_MESSAGE(pStats == nullptr, picture);
            continue;
        }

        REQUIRE_MESSAGE(pStats != nullptr, picture);
        CHECK_EQ(pStats->id, expectedIds[tier]);

        const OpenYAMM::Game::MonsterEntry *pDescriptor = monsterTable.findByInternalName(picture);
        REQUIRE_MESSAGE(pDescriptor != nullptr, picture);
        CHECK_EQ(pDescriptor, monsterTable.findById(expectedIds[tier]));
    }
}
}

TEST_CASE("MM9 monster families resolve encounter tier pictures")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    const OpenYAMM::Game::MonsterTable &monsterTable = dataLoader.getMonsterTable();

    checkFamilyTiers(monsterTable, "MM9 Dragonfly", {9075, 9076, 9077}, 3);
    checkFamilyTiers(monsterTable, "MM9 Skeleton", {9183, 9184, 9135}, 3);
    checkFamilyTiers(monsterTable, "MM9 Skeleton Warrior", {9136, 9137, 0}, 2);

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pDragonflyMite = monsterTable.findStatsById(9075);
    REQUIRE(pDragonflyMite != nullptr);
    CHECK_EQ(pDragonflyMite->name, "Dragonfly Mite");

    // Rows outside a family keep their unique source picture.
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pSkullThrower =
        monsterTable.findStatsByPictureName("MM9 185 Skull Thrower");
    REQUIRE(pSkullThrower != nullptr);
    CHECK_EQ(pSkullThrower->id, 9185);

    const OpenYAMM::Game::MapStatsEntry *pIsleOfAshes = dataLoader.getMapStats().findById(9021);
    REQUIRE(pIsleOfAshes != nullptr);
    CHECK_EQ(pIsleOfAshes->encounter1.pictureName, "MM9 Skeleton");
    CHECK_EQ(pIsleOfAshes->encounter2.pictureName, "MM9 Dragonfly");
    CHECK(pIsleOfAshes->encounter3.pictureName.empty());
}
