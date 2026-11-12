#include "doctest/doctest.h"
#include "game/gameplay/BountyHuntRuntime.h"
#include "game/party/Party.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/rules/ExperienceRules.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawRules.h"
#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <cmath>
#include <string>
#include <utility>
#include <vector>

// MAW audit 2026-10-24, stream 3: monsters, items and content (devdocs/maw/AUDIT_20261024_PLAN.md).

using namespace OpenYAMM::Game;

namespace
{
Party mawTestParty(MawRules &rules)
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    return party;
}

MapKillProgress clearedDungeon(const std::string &map)
{
    MapKillProgress progress;
    progress.mapFileName = map;
    progress.indoor = true;
    progress.countedMonsters = 20;
    progress.slainMonsters = 20;
    return progress;
}
}

TEST_CASE("MAW keeps a map cleared only until its monsters refill; the reward stays once per game (MON-3)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Nightmare;
    MawRules rules(options, MawMapLevels{});
    Party party = mawTestParty(rules);
    const MonsterRules &monsters = rules.gameRules().monsters;
    const ExperienceRules &experience = rules.gameRules().experience;

    // Before the clear: Nightmare saves cost food, no reset is offered.
    CHECK_EQ(monsters.saveFoodCost("d08.blv", true, false), 2);
    CHECK_FALSE(monsters.mapResetOffer("d08.blv").has_value());

    CHECK_FALSE(experience.rewardMapProgress(party, clearedDungeon("d08.blv")).empty());
    CHECK(rules.state().completedMaps.contains("d08.blv"));
    CHECK(rules.state().clearedSinceRefill.contains("d08.blv"));
    CHECK_EQ(monsters.saveFoodCost("d08.blv", true, false), 0);
    CHECK(monsters.mapResetOffer("d08.blv").has_value());

    // A reset (or a natural refill) brings the monsters back: not cleared, no second reset offer, saves cost again.
    monsters.resetMap("d08.blv");
    monsters.mapLoaded("d08.blv", true);
    CHECK(rules.state().completedMaps.contains("d08.blv"));
    CHECK_FALSE(rules.state().clearedSinceRefill.contains("d08.blv"));
    CHECK_FALSE(monsters.mapResetOffer("d08.blv").has_value());
    CHECK_EQ(monsters.saveFoodCost("d08.blv", true, false), 2);

    // A load without a refill keeps the clear; a re-clear marks it again without a second reward.
    const int gold = party.gold();
    CHECK(experience.rewardMapProgress(party, clearedDungeon("d08.blv")).empty());
    CHECK_EQ(party.gold(), gold);
    CHECK(rules.state().clearedSinceRefill.contains("d08.blv"));
    monsters.mapLoaded("d08.blv", false);
    CHECK(monsters.mapResetOffer("d08.blv").has_value());
}

TEST_CASE("MAW pays a map clear by the level of its monsters, else by the map's level (MAW 8967ae88)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto clearExperience = [](int levelledMonsters, double levelSum)
    {
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        Party party = mawTestParty(rules);
        MapKillProgress progress = clearedDungeon("d08.blv");
        progress.levelledMonsters = levelledMonsters;
        progress.monsterLevelSum = levelSum;
        const size_t members = party.members().size();
        const std::string message = rules.gameRules().experience.rewardMapProgress(party, progress);
        return std::pair(message, members);
    };
    // The bank's experience by level L for 20 monsters, and a member's share of five times it (mapClearLevel).
    const auto memberShare = [](double level, size_t members)
    {
        const double experience =
            std::ceil(std::pow(20.0, 0.7) * (level * 20 + std::pow(level, 1.8)) / 3 / 1000) * 1000;
        return std::to_string(int64_t(std::round(experience * 5 / double(members) / 1000) * 1000));
    };

    // Twenty monsters of average level 60.
    const auto [byMonsters, members] = clearExperience(20, 20 * 60.0);
    CHECK_NE(byMonsters.find("You gain " + memberShare(60, members) + " Exp"), std::string::npos);

    // No levels known: the map's own level (none in these tables, so 1) as before.
    const auto [byMap, sameMembers] = clearExperience(0, 0);
    CHECK_NE(byMap.find("You gain " + memberShare(1, sameMembers) + " Exp"), std::string::npos);
}

TEST_CASE("MAW risen monsters give full experience in Nightmare and Doom, none in Road to Insanity (MON-1)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto granted = [](RulesetChallengeMode mode, bool risen)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        Party party = mawTestParty(rules);
        MonsterKillReward kill;
        kill.facts.level = 20;
        kill.facts.familyLevel = 20;
        kill.facts.experience = 5000;
        kill.facts.risen = risen;
        kill.maxHp = 500;
        return rules.gameRules().experience.grantKillExperience(party, kill);
    };

    CHECK_GT(granted(RulesetChallengeMode::Doom, true), 0u);
    CHECK_EQ(granted(RulesetChallengeMode::Doom, true), granted(RulesetChallengeMode::Doom, false));
    CHECK_EQ(granted(RulesetChallengeMode::RoadToInsanity, true), 0u);
    CHECK_EQ(granted(RulesetChallengeMode::BeyondMadness, true), 0u);
    CHECK_GT(granted(RulesetChallengeMode::RoadToInsanity, false), 0u);
}

TEST_CASE("MAW kills in the Endless Arena bank no levels; the members still gain experience (MON-5)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto kill = [](const char *pMap)
    {
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        rules.setCurrentMap(pMap);
        Party party = mawTestParty(rules);
        MonsterKillReward reward;
        reward.facts.level = 20;
        reward.facts.familyLevel = 20;
        reward.facts.experience = 5000;
        reward.maxHp = 500;
        const uint32_t granted = rules.gameRules().experience.grantKillExperience(party, reward);
        return std::pair(granted, rules.state().bankedExperience);
    };

    const auto [arenaGranted, arenaBank] = kill("d42.blv");
    const auto [fieldGranted, fieldBank] = kill("d08.blv");
    CHECK_GT(arenaGranted, 0u);
    CHECK_EQ(arenaBank, 0.0);
    CHECK_GT(fieldBank, 0.0);
    CHECK_EQ(arenaGranted, fieldGranted);
}

TEST_CASE("Beyond Madness rolls special bosses on a completed map once it refills (FMON-2-9)")
{
    RulesetOptions options;
    options.challengeMode = RulesetChallengeMode::BeyondMadness;
    MawRules rules(options, MawMapLevels{});
    rules.setCurrentMap("d08.blv");
    rules.state().completedMaps.insert("d08.blv");
    const MonsterRules &monsters = rules.gameRules().monsters;
    const auto specials = [&monsters]()
    {
        int count = 0;

        for (uint64_t seed = 1; seed <= 2000; ++seed)
        {
            ActorRulesetFacts facts;
            facts.level = 50;
            facts.familyLevel = 40;
            REQUIRE(monsters.makeBoss(facts, seed * 7919, 0));
            count += facts.bossAffix == uint8_t(MawBossAffix::Broodlord)
                || facts.bossAffix == uint8_t(MawBossAffix::Omnipotent) ? 1 : 0;
        }

        return count;
    };

    // Completed once, refilled since (a dimension run's map): the rolls and their bad-luck protection run.
    CHECK_GT(specials(), 0);
    // Cleared on this visit: none.
    rules.state().clearedSinceRefill.insert("d08.blv");
    CHECK_EQ(specials(), 0);
}

TEST_CASE("MAW kills by the party's allies give each conscious member a share; allies give none (FMON-2-2)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.setCurrentMap("d08.blv");
    Party party = mawTestParty(rules);
    REQUIRE_GE(party.members().size(), 2u);
    party.member(1)->conditions.set(size_t(CharacterCondition::Unconscious));
    const size_t conscious = party.members().size() - 1;
    std::vector<uint64_t> before;

    for (const Character &member : party.members())
    {
        before.push_back(member.experience);
    }

    MonsterKillReward kill;
    kill.facts.level = 20;
    kill.facts.familyLevel = 20;
    kill.facts.experience = 5000;
    kill.maxHp = 500;
    kill.byPartyAlly = true;
    const ExperienceRules &experience = rules.gameRules().experience;
    // The whole experience, split evenly, whatever the monster's toughness and with no bank.
    CHECK_EQ(experience.grantKillExperience(party, kill), uint32_t(5000 / conscious * conscious));
    CHECK_EQ(party.members()[0].experience - before[0], 5000 / conscious);
    CHECK_EQ(party.members()[1].experience, before[1]);
    CHECK_EQ(rules.state().bankedExperience, 0.0);

    // The party's own ally is worth nothing, however it dies.
    kill.partyAlly = true;
    CHECK_EQ(experience.grantKillExperience(party, kill), 0u);
    kill.byPartyAlly = false;
    CHECK_EQ(experience.grantKillExperience(party, kill), 0u);

    // Standard: an ally's kill gives nothing, and a slain ally its usual reward.
    const ExperienceRules standard;
    MonsterKillReward table;
    table.baseExperience = 400;
    table.baseHitPoints = 50;
    table.byPartyAlly = true;
    CHECK_EQ(standard.grantKillExperience(party, table), 0u);
    table.byPartyAlly = false;
    const uint32_t usual = standard.grantKillExperience(party, table);
    CHECK_GT(usual, 0u);
    table.partyAlly = true;
    CHECK_EQ(standard.grantKillExperience(party, table), usual);
}

TEST_CASE("MAW counts a bounty boss's kill only for the map it was posted for (MON-15)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawTestParty(rules);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    EventRuntimeState state = {};
    world.bindParty(&party);
    world.bindEventRuntimeState(&state);
    world.setMapName("map_b.odm");
    state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.MonsterId"] = 10;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.MonsterId"] = 10;
    ActorRulesetFacts boss;
    boss.bossAffix = 1;

    CHECK(markRuntimeBountyHuntMonsterKilled(world, 10, nullptr, boss));
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Done"], 1);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.Done"], 0);
}

TEST_CASE("MAW bounty texts name the spawned boss and its map note goes with it (GAPS H.11)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    std::vector<std::string> row(38);
    row[0] = "195";
    row[1] = "Human Mercenary C";
    row[2] = "Human Mercenary C";
    row[3] = "24";
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({row}));
    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(195);
    REQUIRE(pStats != nullptr);
    const int monsterId = pStats->id;
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = mawTestParty(rules);
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    EventRuntimeState state = {};
    world.bindParty(&party);
    world.bindEventRuntimeState(&state);
    world.bindMonsterTable(&monsterTable);
    world.setMapName("map_b.odm");
    state.mapFileName = "Map_B.odm";
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.MonsterId"] = monsterId;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.BossAffix"] = int(MawBossAffix::Omnipotent);
    JournalMapNote note;
    note.id = 9999;
    note.mapFileName = "map_b.odm";
    note.text = "Bounty";
    party.setJournalMapNote(note);

    const BountyHuntInteractionResult hunt = performBountyHuntInteraction(world, &party, true);
    REQUIRE_EQ(hunt.messages.size(), 1u);
    CHECK_NE(hunt.messages.front().find("Omnipotent " + pStats->name), std::string::npos);

    // Another boss of the kind leaves the note; the target's death takes it down.
    ActorRulesetFacts other;
    other.bossAffix = uint8_t(MawBossAffix::Swift);
    markRuntimeBountyHuntMonsterKilled(world, int16_t(monsterId), nullptr, other);
    CHECK(party.findJournalMapNote("map_b.odm", 9999) != nullptr);
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Done"] = 0;
    ActorRulesetFacts target;
    target.bossAffix = uint8_t(MawBossAffix::Omnipotent);
    markRuntimeBountyHuntMonsterKilled(world, int16_t(monsterId), nullptr, target);
    CHECK(party.findJournalMapNote("map_b.odm", 9999) == nullptr);

    const BountyHuntInteractionResult reward = performBountyHuntInteraction(world, &party, true);
    REQUIRE_EQ(reward.messages.size(), 1u);
    CHECK_NE(reward.messages.front().find("Omnipotent " + pStats->name), std::string::npos);

    // A plain target (Standard's) keeps the table name and stores no affix.
    state.namedGlobalVars.clear();
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.MonsterId"] = monsterId;
    const BountyHuntInteractionResult plain = performBountyHuntInteraction(world, &party, true);
    REQUIRE_EQ(plain.messages.size(), 1u);
    CHECK_EQ(plain.messages.front().find("Omnipotent"), std::string::npos);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.BossAffix"], 0);
}

TEST_CASE("MAW calls a bounty off when anyone but the party slays its target; Standard does not")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto slain = [](bool maw, bool killedByParty)
    {
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        Party mawParty = mawTestParty(rules);
        Party standardParty = {};
        Party &party = maw ? mawParty : standardParty;
        OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
        EventRuntimeState state = {};
        world.bindParty(&party);
        world.bindEventRuntimeState(&state);
        world.setMapName("map_b.odm");
        state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Month"] = 0;
        state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.MonsterId"] = 195;
        state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.BossAffix"] = int(MawBossAffix::Swift);
        ActorRulesetFacts target;
        target.bossAffix = uint8_t(MawBossAffix::Swift);
        markRuntimeBountyHuntMonsterKilled(world, 195, nullptr, target, killedByParty);
        return state.namedGlobalVars;
    };

    // A party member's blow fulfils it.
    CHECK_EQ(slain(true, true).at("MMerge.BountyHunt.map_b.odm.Done"), 1);
    // An ally, another monster or a trap: MAW drops the bounty (BountyHunt.lua:247-250), so the town offers a new one.
    const std::unordered_map<std::string, int32_t> dropped = slain(true, false);
    CHECK_EQ(dropped.at("MMerge.BountyHunt.map_b.odm.MonsterId"), 0);
    CHECK_EQ(dropped.at("MMerge.BountyHunt.map_b.odm.Month"), 0);
    CHECK_EQ(dropped.at("MMerge.BountyHunt.map_b.odm.Done"), 0);
    // Standard: any death fulfils it.
    CHECK_EQ(slain(false, false).at("MMerge.BountyHunt.map_b.odm.Done"), 1);
}

TEST_CASE("MAW's map progress marks revival only where the dead can rise (MON-16)")
{
    // A dungeon half cleared.
    class ProgressWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
    {
    public:
        bool mapKillProgress(MapKillProgress &progress) const override
        {
            progress = clearedDungeon("d08.blv");
            progress.slainMonsters = 10;
            return true;
        }
    };

    // Below Nightmare a half-cleared dungeon shows its progress without the revival mark (MAW's red until cleared is
    // replaced by the mark, maw_map_progress_20261025).
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ProgressWorld world;
    std::optional<RulesetMapProgress> progress = rules.gameRules().monsters.mapProgress(world);
    REQUIRE(progress);
    CHECK(progress->percent == doctest::Approx(50.0));
    CHECK_FALSE(progress->revival);

    RulesetOptions nightmare;
    nightmare.difficulty = RulesetDifficulty::Nightmare;
    MawRules nightmareRules(nightmare, MawMapLevels{});
    progress = nightmareRules.gameRules().monsters.mapProgress(world);
    REQUIRE(progress);
    CHECK(progress->revival);
    CHECK_FALSE(progress->revivalPassed);
    CHECK_EQ(progress->revivalSlain, 13);
}

TEST_CASE("MAW map scripts read a bolster level with the reset and dimension terms (MON-17)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.state().continentLevels = {0, 60, 0, 0};
    rules.setCurrentMap("d12.blv");
    const MonsterRules &monsters = rules.gameRules().monsters;
    const int base = monsters.scriptInfo(1).bolsterLevel;
    CHECK_EQ(base, int(rules.state().levelOutside(1)) - 4);

    // Two resets: +40.
    rules.state().mapResetCounts["d12.blv"] = 2;
    CHECK_EQ(monsters.scriptInfo(1).bolsterLevel, base + 40);

    // A dimension run: its power x 10 + 20.
    MawDimensionRun run;
    run.power = 7;
    rules.state().dimensionRuns["d12.blv"] = run;
    CHECK_EQ(monsters.scriptInfo(1).bolsterLevel, 90);
}

TEST_CASE("MAW keeps the Hall under the Hill's unicorns at 1-3 on every difficulty (MON-18)")
{
    RulesetOptions options;
    options.difficulty = RulesetDifficulty::Nightmare;
    MawRules rules(options, MawMapLevels{});
    MapStatsEntry hall = {};
    hall.id = 96;
    hall.encounter3 = {.difficulty = 1, .minCount = 1, .maxCount = 3};
    MapStatsEntry other = hall;
    other.id = 95;
    rules.gameRules().monsters.adjustMapEncounters(hall);
    rules.gameRules().monsters.adjustMapEncounters(other);
    CHECK_EQ(hall.encounter3.minCount, 1);
    CHECK_EQ(hall.encounter3.maxCount, 3);
    CHECK(other.encounter3.maxCount > 3);
}

TEST_CASE("an MM9 Jarl posts his region's bounty and its target appears when the party enters the region")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    std::vector<std::string> row(38);
    row[0] = "195";
    row[1] = "Human Mercenary C";
    row[2] = "Human Mercenary C";
    row[3] = "10";   // within an empty party's reach (Standard: level 20)
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({row}));
    const BountyHuntRemoteMap region = {"Sturmford", "sturmford.blv"};

    // MAW: the region, not the city, must be cleared first.
    {
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        Party party = mawTestParty(rules);
        OpenYAMM::Tests::PartySpellTestWorldRuntime city = {};
        EventRuntimeState state = {};
        city.bindParty(&party);
        city.bindEventRuntimeState(&state);
        city.bindMonsterTable(&monsterTable);
        city.setMapName("Sturmford City");
        const BountyHuntInteractionResult refused = performBountyHuntInteraction(city, &party, true, nullptr, &region);
        REQUIRE_EQ(refused.messages.size(), 1u);
        CHECK_NE(refused.messages.front().find("Sturmford"), std::string::npos);
        CHECK_FALSE(state.namedGlobalVars.contains("MMerge.BountyHunt.Sturmford.MonsterId"));
        rules.state().clearedSinceRefill.insert("sturmford.blv");
        performBountyHuntInteraction(city, &party, true, nullptr, &region);
        CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.Sturmford.Pending"], 1);
    }

    // Posted in the city: the hunt is the region's, waiting; nothing appears in the city.
    Party party = {};
    OpenYAMM::Tests::PartySpellTestWorldRuntime city = {};
    EventRuntimeState state = {};
    city.bindParty(&party);
    city.bindEventRuntimeState(&state);
    city.bindMonsterTable(&monsterTable);
    city.setMapName("Sturmford City");
    const BountyHuntInteractionResult posted = performBountyHuntInteraction(city, &party, true, nullptr, &region);
    REQUIRE_EQ(posted.messages.size(), 1u);
    CHECK(posted.succeeded);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.Sturmford.MonsterId"], 195);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.Sturmford.Pending"], 1);
    CHECK(city.hostileSummonRequests().empty());
    spawnPendingBountyHunt(city, &party);
    CHECK(city.hostileSummonRequests().empty());

    // Entering the region places the target once.
    std::unordered_map<std::string, int32_t> sessionGlobals = state.namedGlobalVars;
    OpenYAMM::Tests::PartySpellTestWorldRuntime regionWorld = {};
    regionWorld.bindParty(&party);
    regionWorld.bindEventRuntimeState(&state);
    regionWorld.bindMonsterTable(&monsterTable);
    regionWorld.setMapName("Sturmford");
    spawnPendingBountyHunt(regionWorld, &party);
    REQUIRE_EQ(regionWorld.hostileSummonRequests().size(), 1u);
    CHECK_EQ(regionWorld.hostileSummonRequests().front().monsterId, 195);
    // Cleared as 0, not erased: the session merges a map's global vars back, so an erased key returned with the next
    // map load and the target appeared again on every entry that month.
    CHECK_EQ(state.namedGlobalVars.at("MMerge.BountyHunt.Sturmford.Pending"), 0);
    spawnPendingBountyHunt(regionWorld, &party);
    CHECK_EQ(regionWorld.hostileSummonRequests().size(), 1u);

    // Leaving and entering again the same month: the session merges the map's globals back
    // (GameSession::mergeNamedGlobalVarsFromRuntime) and gives them to the next load; the target stays placed once.
    for (const auto &[name, value] : state.namedGlobalVars)
    {
        sessionGlobals[name] = value;
    }

    EventRuntimeState reentered = {};
    reentered.namedGlobalVars = sessionGlobals;
    OpenYAMM::Tests::PartySpellTestWorldRuntime regionAgain = {};
    regionAgain.bindParty(&party);
    regionAgain.bindEventRuntimeState(&reentered);
    regionAgain.bindMonsterTable(&monsterTable);
    regionAgain.setMapName("Sturmford");
    spawnPendingBountyHunt(regionAgain, &party);
    CHECK(regionAgain.hostileSummonRequests().empty());

    // Slain in the region, the Jarl pays it.
    markRuntimeBountyHuntMonsterKilled(regionWorld, 195, &monsterTable);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.Sturmford.Done"], 1);
    const int goldBefore = party.gold();
    performBountyHuntInteraction(city, &party, true, nullptr, &region);
    CHECK_GT(party.gold(), goldBefore);
}
