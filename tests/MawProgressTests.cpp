#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/events/EventRuntime.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/RulesetProgress.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MonsterTable.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

// The Journal's Progress tab (MAW, level_generation/ui/maw_loot_progress_20261025 B).
using namespace OpenYAMM::Game;

namespace
{
std::string readSource(const std::string &path)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / path);
    REQUIRE(file.good());
    std::ostringstream stream;
    stream << file.rdbuf();
    return stream.str();
}

std::vector<std::vector<std::string>> tableRows(const std::string &name)
{
    const auto table = OpenYAMM::Engine::TextTable::parseTabSeparated(
        readSource("assets_dev/engine/data_tables/" + name));
    REQUIRE(table.has_value());
    std::vector<std::vector<std::string>> rows;

    for (size_t index = 0; index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }

    return rows;
}

// The installed tables and MAW's map levels.
struct ProgressData
{
    MapStats maps;
    MonsterTable monsters;
    MawMapLevels mapLevels;

    ProgressData()
    {
        REQUIRE(maps.loadFromRows(tableRows("map_stats.txt")));
        // The continents come with the merged bolster maps.
        MergedBolsterMapTable bolsterMaps;
        REQUIRE(bolsterMaps.loadFromRows(tableRows("bolster_maps.txt")));
        REQUIRE(maps.applyMergedBolsterMaps(bolsterMaps));
        REQUIRE(monsters.loadStatsFromRows(tableRows("monster_data.txt")));
        std::string error;
        REQUIRE_MESSAGE(mapLevels.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/map_levels.yml"), error),
            error);
    }
};

const RulesetProgressMap *findMap(const RulesetProgressContinent &continent, const std::string &file)
{
    const auto found = std::find_if(continent.maps.begin(), continent.maps.end(),
        [&file](const RulesetProgressMap &map) { return map.fileName == file; });
    return found != continent.maps.end() ? &*found : nullptr;
}

// A map the party stands on, so far cleared.
class ProgressWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    bool mapKillProgress(MapKillProgress &progress) const override
    {
        progress = {};
        progress.mapFileName = "6D04.blv";
        progress.slainMonsters = 2;
        progress.countedMonsters = 5;
        progress.indoor = true;
        return true;
    }
};
}

TEST_CASE("MAW's Progress tab lists each continent's maps with their state, level and records")
{
    const ProgressData data;
    MawRules rules(RulesetOptions{}, data.mapLevels);
    rules.setMapTable(&data.maps);
    MawGameState &state = rules.state();
    state.continentLevels[*MawGameState::continentIndex(3)] = 12;
    state.completedMaps.insert("oute3.odm");
    state.clearedSinceRefill.insert("oute3.odm");
    state.mapResetCounts["6d01.blv"] = 2;
    state.mapVisits["6d02.blv"] = {3, 12, 1};
    state.dimensionRunsCleared = 4;
    state.bountiesClaimed = 2;
    const MonsterRules &monsters = rules.gameRules().monsters;
    CHECK(monsters.hasProgressTab());

    RulesetProgressQuery query;
    query.pMonsterTable = &data.monsters;
    query.gameMinutes = 5 * 24 * 60;
    MapKillProgress current;
    current.mapFileName = "6D03.blv";
    current.slainMonsters = 1;
    current.countedMonsters = 4;
    query.currentMap = current;
    // This month's bounty of the Abandoned Temple's map, and a dimension run open on 6d06.
    EventRuntimeState events;
    const std::string bountyPrefix = "MMerge.BountyHunt." + data.maps.findByFileName("6d02.blv")->name;
    events.namedGlobalVars[bountyPrefix + ".Month"] = 0;
    events.namedGlobalVars[bountyPrefix + ".MonsterId"] = 195;
    query.pEventState = &events;
    state.dimensionRuns["6d06.blv"].power = 3;
    const std::optional<RulesetProgressSummary> summary = monsters.progressSummary(query);
    REQUIRE(summary);
    CHECK_EQ(summary->difficulty, "MAW");
    CHECK_EQ(summary->dimensionQuest, "not started");
    CHECK_EQ(summary->dimensionRunsCleared, 4);
    CHECK_EQ(summary->bountiesClaimed, 2);
    CHECK_NE(summary->currentRun.find("power 3"), std::string::npos);
    CHECK_FALSE(summary->deaths);
    REQUIRE_EQ(summary->continents.size(), 3u);
    const RulesetProgressContinent &enroth = summary->continents[0];
    CHECK_EQ(enroth.name, "Enroth");
    CHECK_EQ(enroth.levelsBanked, 12.0);
    CHECK_EQ(enroth.mapsCleared, 1);
    CHECK(enroth.levelLow > 0);
    CHECK(enroth.levelHigh >= enroth.levelLow);

    // By level, and only maps with monsters of their own.
    for (size_t index = 0; index < enroth.maps.size(); ++index)
    {
        CHECK(enroth.maps[index].level > 0);

        if (index > 0)
        {
            CHECK(enroth.maps[index - 1].level <= enroth.maps[index].level);
        }
    }

    const RulesetProgressMap *pCleared = findMap(enroth, "oute3.odm");
    REQUIRE(pCleared != nullptr);
    CHECK_EQ(pCleared->state, RulesetMapProgressState::Cleared);
    CHECK(pCleared->completedOnce);
    CHECK_EQ(pCleared->slainShare, 1.0);

    // Left after slaying 3 of 12 on day 1: the refill counts from that day.
    const RulesetProgressMap *pVisited = findMap(enroth, "6d02.blv");
    REQUIRE(pVisited != nullptr);
    CHECK_EQ(pVisited->state, RulesetMapProgressState::InProgress);
    CHECK_EQ(pVisited->slainShare, 0.25);
    const int respawnDays = monsters.mapRespawnDays(*data.maps.findByFileName("6d02.blv"));

    if (respawnDays > 0)
    {
        REQUIRE(pVisited->refillInDays);
        CHECK_EQ(*pVisited->refillInDays, std::max(0, respawnDays - 5));
    }

    // The map the party is on reads live.
    const RulesetProgressMap *pCurrent = findMap(enroth, "6d03.blv");
    REQUIRE(pCurrent != nullptr);
    CHECK_EQ(pCurrent->state, RulesetMapProgressState::InProgress);
    CHECK_EQ(pCurrent->slainShare, 0.25);
    CHECK(pCurrent->current);
    CHECK_FALSE(pVisited->current);
    CHECK(pVisited->bountyTarget);
    CHECK_FALSE(pCurrent->bountyTarget);

    // Two resets: 40 levels' bolster more, shown as their share.
    const RulesetProgressMap *pReset = findMap(enroth, "6d01.blv");
    REQUIRE(pReset != nullptr);
    CHECK_EQ(pReset->resets, 2);
    CHECK_FALSE(pReset->dimensionRun);
    const RulesetProgressMap *pRun = findMap(enroth, "6d06.blv");
    REQUIRE(pRun != nullptr);
    CHECK(pRun->dimensionRun);
    CHECK(pReset->levelFromResets > 0);

    const RulesetProgressMap *pUnvisited = findMap(enroth, "6d05.blv");
    REQUIRE(pUnvisited != nullptr);
    CHECK_EQ(pUnvisited->state, RulesetMapProgressState::NotVisited);
    CHECK_FALSE(pUnvisited->refillInDays);

    // Standard has no Progress tab.
    const MonsterRules standard;
    CHECK_FALSE(standard.hasProgressTab());
    CHECK_FALSE(standard.progressSummary(query));
}

TEST_CASE("MAW records the map the party leaves and counts dimension runs and bounties")
{
    const ProgressData data;
    MawRules rules(RulesetOptions{}, data.mapLevels);
    rules.setMapTable(&data.maps);
    rules.setCurrentMap("6d04.blv");
    const MonsterRules &monsters = rules.gameRules().monsters;
    ProgressWorld world;
    world.advanceGameMinutes(3 * 24 * 60 + 30);
    monsters.updateMonsters(world, 0.016f);
    monsters.leaveMap(world);
    REQUIRE(rules.state().mapVisits.contains("6d04.blv"));
    CHECK_EQ(rules.state().mapVisits.at("6d04.blv"), MawMapVisit{2, 5, 4});

    monsters.bountyClaimed();
    CHECK_EQ(rules.state().bountiesClaimed, 1);
    const MonsterRules standard;
    standard.bountyClaimed();
}

TEST_CASE("MAW's map table gives every listed map's level under each progression (ruleset maplevels)")
{
    const ProgressData data;
    MawRules rules(RulesetOptions{}, data.mapLevels);
    rules.setMapTable(&data.maps);
    // The table ignores this game's banks and options.
    rules.state().continentLevels[0] = 30;

    const std::vector<MawRules::MapLevelRow> rows = rules.mapLevelTable(data.monsters, 50);
    const auto find = [&rows](const std::string &file)
    {
        const auto found = std::find_if(rows.begin(), rows.end(),
            [&file](const MawRules::MapLevelRow &row) { return row.fileName == file; });
        REQUIRE(found != rows.end());
        return *found;
    };

    // Ravenshore: Jadame, band [14, 14, 17]; its natives climb with the banks and sit far higher in horizontal.
    const MawRules::MapLevelRow ravenshore = find("out02.odm");
    CHECK_EQ(ravenshore.continentId, 1u);
    CHECK(ravenshore.band == std::array<double, 3>{14, 14, 17});
    CHECK(ravenshore.freeLevel > 0);
    CHECK(ravenshore.freeBankedLevel > ravenshore.freeLevel + 40);
    CHECK(ravenshore.horizontalLevel > ravenshore.freeLevel + 10);
    CHECK(ravenshore.madnessMapLevel > 0);

    // Dagger Wound Island starts horizontal progression: no x2.5 there.
    const MawRules::MapLevelRow daggerWound = find("out01.odm");
    CHECK(daggerWound.horizontalStarter);
    CHECK(daggerWound.horizontalLevel < 2 * std::max(daggerWound.freeLevel, 4));

    // Every listed map, each of the three MM6-MM8 continents.
    CHECK(rows.size() > 150);
    for (uint32_t continent : {1u, 2u, 3u})
    {
        CHECK(std::any_of(rows.begin(), rows.end(),
            [continent](const MawRules::MapLevelRow &row) { return row.continentId == continent; }));
    }
}
