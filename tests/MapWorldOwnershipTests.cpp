#include "doctest/doctest.h"

#include "game/maps/MapIdentity.h"
#include "game/tables/MapStats.h"

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::vector<std::string> mapRow(const std::string &id, const std::string &fileName, const std::string &worldId = "")
{
    std::vector<std::string> row(35);
    row[0] = id;
    row[1] = fileName;
    row[2] = fileName;
    row[34] = worldId;
    return row;
}
}

TEST_CASE("map stats resolve each map's world from the world package that ships it")
{
    MapStats stats;
    REQUIRE(stats.loadFromRows({mapRow("1", "hive.blv"), mapRow("2", "6d02.blv"), mapRow("3", "d01.blv"),
        mapRow("4", "out01.odm"), mapRow("5", "pinned.blv", "mm7")}));
    CHECK(stats.findByFileName("hive.blv")->worldId == "mm8");

    REQUIRE(stats.applyWorldOwnership({{"mm6", "Hive.BLV"}, {"mm6", "6d02.blv"}, {"mm7", "d01.blv"},
        {"mm8", "out01.odm"}, {"mm6", "pinned.blv"}, {"mm6", "hive.scene.yml"}}));
    CHECK(stats.findByFileName("hive.blv")->worldId == "mm6");
    CHECK(stats.findByFileName("hive.blv")->canonicalId == "world.mm6.map.hive");
    CHECK(stats.findByFileName("d01.blv")->worldId == "mm7");
    CHECK(stats.findByFileName("out01.odm")->worldId == "mm8");
    CHECK(stats.findByFileName("pinned.blv")->worldId == "mm7");

    const std::vector<std::pair<std::string, std::string>> renames = stats.legacyCanonicalIdRenames();
    const std::vector<std::pair<std::string, std::string>> expected = {
        {"world.mm8.map.hive", "world.mm6.map.hive"}, {"world.mm8.map.d01", "world.mm7.map.d01"}};
    CHECK(renames == expected);
}

TEST_CASE("map stats reject a map file shipped by two worlds without an explicit world")
{
    MapStats stats;
    REQUIRE(stats.loadFromRows({mapRow("1", "shared.blv"), mapRow("2", "pinned.blv", "mm8")}));
    CHECK_FALSE(stats.applyWorldOwnership({{"mm6", "shared.blv"}, {"mm7", "shared.blv"}}));

    MapStats pinned;
    REQUIRE(pinned.loadFromRows({mapRow("2", "pinned.blv", "mm8")}));
    CHECK(pinned.applyWorldOwnership({{"mm6", "pinned.blv"}, {"mm7", "pinned.blv"}}));
    CHECK(pinned.findByFileName("pinned.blv")->worldId == "mm8");
}

TEST_CASE("saved map states move from a legacy canonical id without overwriting newer state")
{
    std::unordered_map<std::string, int> states = {{"world.mm8.map.hive", 1}, {"world.mm8.map.d01", 2},
        {"world.mm7.map.d01", 3}, {"hive.blv", 4}};
    migrateMapStateKey(states, "world.mm8.map.hive", "world.mm6.map.hive");
    migrateMapStateKey(states, "world.mm8.map.d01", "world.mm7.map.d01");
    migrateMapStateKey(states, "world.mm8.map.oracle", "world.mm6.map.oracle");

    CHECK_FALSE(states.contains("world.mm8.map.hive"));
    CHECK(states.at("world.mm6.map.hive") == 1);
    CHECK(states.at("world.mm7.map.d01") == 3);
    CHECK(states.at("hive.blv") == 4);
    CHECK_FALSE(states.contains("world.mm6.map.oracle"));
}
