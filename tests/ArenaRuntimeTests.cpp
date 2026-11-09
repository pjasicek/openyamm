#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/ArenaRuntime.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/rules/maw/MawRules.h"
#include "tests/HouseDialogueTestHarness.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <set>
#include <sstream>
#include <vector>

namespace
{
using namespace OpenYAMM;

struct ArenaWorld
{
    const char *world;
    const char *map;
    uint32_t npc;
    int minimumMonster;
    int maximumMonster;
};

constexpr std::array<ArenaWorld, 3> Arenas = {{
    {"mm6", "zarena", 313, 475, 652},
    {"mm7", "7d05", 639, 199, 474},
    {"mm8", "d42", 313, 1, 198},
}};

std::string readSource(const std::string &path)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / path);
    REQUIRE(file.good());
    std::ostringstream stream;
    stream << file.rdbuf();
    return stream.str();
}

std::vector<std::vector<std::string>> tableRows(const char *name)
{
    const auto table = Engine::TextTable::parseTabSeparated(
        readSource(std::string("assets_dev/engine/data_tables/") + name));
    REQUIRE(table.has_value());
    std::vector<std::vector<std::string>> rows;
    for (size_t index = 0; index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }
    return rows;
}

Game::MonsterTable arenaMonsters()
{
    Game::MonsterTable monsters;
    REQUIRE(monsters.loadEntriesFromRows(tableRows("monster_descriptors.txt")));
    REQUIRE(monsters.loadStatsFromRows(tableRows("monster_data.txt")));
    Game::MergedBolsterMonsterTable kinds;
    REQUIRE(kinds.loadFromRows(tableRows("bolster_monsters.txt")));
    REQUIRE(monsters.applyKindFlagsFromBolsterMonsterTable(kinds));
    return monsters;
}

Game::MapStatsEntry arenaMap(const ArenaWorld &world)
{
    const std::string path = std::string("assets_dev/worlds/") + world.world + "/maps/" + world.map;
    const Game::IndoorSceneYmlLoader loader;
    std::string error;
    std::optional<Game::IndoorSceneData> scene = loader.loadFromText(readSource(path + ".scene.yml"), error);
    REQUIRE_MESSAGE(scene.has_value(), error);
    REQUIRE_MESSAGE(loader.applyOverlayFromText(*scene, readSource(path + "_1.scene.yml"), error), error);
    REQUIRE(scene->arena.has_value());
    CHECK(scene->runtimeRestrictions.isArena);
    CHECK_FALSE(scene->runtimeRestrictions.allowSaveGame);
    CHECK_EQ(scene->arena->minimumMonsterId, world.minimumMonster);
    CHECK_EQ(scene->arena->maximumMonsterId, world.maximumMonster);
    CHECK_EQ(scene->arena->monsterPositions.size(), 20);
    Game::MapStatsEntry map = {};
    map.fileName = std::string(world.map) + ".blv";
    map.worldId = world.world;
    map.runtimeRestrictions = scene->runtimeRestrictions;
    map.arena = scene->arena;
    return map;
}

size_t actionIndex(const Game::EventDialogContent &dialog, Game::EventDialogActionKind kind, uint32_t id)
{
    for (size_t index = 0; index < dialog.actions.size(); ++index)
    {
        if (dialog.actions[index].kind == kind && dialog.actions[index].id == id)
        {
            return index;
        }
    }
    FAIL("Arena dialogue action is missing");
    return 0;
}
}

TEST_CASE("empty arena maps load animation definitions for opponents from their scene overlay")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assetFileSystem));
    const Game::MonsterTable &monsters = data.getMonsterTable();
    const Game::MapAssetLoader loader;
    for (const ArenaWorld &world : Arenas)
    {
        CAPTURE(world.world);
        const Game::MapStatsEntry *pMap =
            data.getMapStats().findByFileName(std::string(world.map) + ".blv");
        REQUIRE(pMap != nullptr);
        REQUIRE_FALSE(pMap->arena.has_value());
        const std::optional<Game::MapAssetInfo> assets = loader.load(
            assetFileSystem, *pMap, monsters, data.getObjectTable(),
            Game::MapLoadPurpose::ActorPreviews);
        REQUIRE(assets.has_value());
        REQUIRE(assets->map.arena.has_value());
        REQUIRE(assets->indoorActorPreviewBillboardSet.has_value());
        CHECK(assets->indoorActorPreviewBillboardSet->billboards.empty());
        const Game::SpriteFrameTable &frames = assets->indoorActorPreviewBillboardSet->spriteFrameTable;
        for (int id = world.minimumMonster; id <= world.maximumMonster; ++id)
        {
            const Game::MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsById(int16_t(id));
            if (pStats == nullptr || pStats->hasKind(Game::MonsterKind::NoArena)
                || pStats->hasKind(Game::MonsterKind::Peasant) || pStats->level < 2 || pStats->level > 100)
            {
                continue;
            }
            CAPTURE(id);
            const Game::MonsterEntry *pMonster = monsters.findById(int16_t(id));
            REQUIRE(pMonster != nullptr);
            for (const std::string &name : pMonster->spriteNames)
            {
                if (!name.empty())
                {
                    CHECK_MESSAGE(frames.findFrameIndexBySpriteName(name).has_value(), name);
                }
            }
        }
    }
}

TEST_CASE("arena opponents stay in their own world at every difficulty and party level")
{
    const Game::MonsterTable monsters = arenaMonsters();
    Game::Party party;
    Game::PartySeed seed = {};
    seed.members.push_back(Game::Character{});
    party.seed(seed);
    struct LevelCase
    {
        uint32_t partyLevel;
        std::array<std::array<int, 2>, 4> monsterLevels;
    };
    constexpr std::array<LevelCase, 5> levelCases = {{
        {1, {{{2, 2}, {2, 2}, {2, 2}, {2, 2}}}},
        {20, {{{10, 20}, {10, 30}, {10, 40}, {20, 40}}}},
        {60, {{{30, 60}, {30, 90}, {30, 100}, {60, 100}}}},
        {100, {{{50, 100}, {50, 100}, {50, 100}, {100, 100}}}},
        {150, {{{75, 100}, {75, 100}, {75, 100}, {100, 100}}}},
    }};
    for (const ArenaWorld &world : Arenas)
    {
        CAPTURE(world.world);
        const Game::MapStatsEntry map = arenaMap(world);
        for (const LevelCase &levelCase : levelCases)
        {
            const uint32_t level = levelCase.partyLevel;
            party.member(0)->level = level;
            for (uint32_t difficulty = 1; difficulty <= 4; ++difficulty)
            {
                CAPTURE(level);
                CAPTURE(difficulty);
                for (uint32_t randomSeed = 0; randomSeed < 12; ++randomSeed)
                {
                    const auto challenge = Game::generateArenaChallenge(
                        monsters, map, party, Game::ArenaDifficulty(difficulty), randomSeed);
                    REQUIRE(challenge.has_value());
                    const std::array<size_t, 4> minimumCounts = {6, 6, 10, 20};
                    const std::array<size_t, 4> maximumCounts = {8, 12, 20, 20};
                    const std::array<uint32_t, 4> rewards = {50, 100, 200, 500};
                    CHECK_GE(challenge->monsterIds.size(), minimumCounts[difficulty - 1]);
                    CHECK_LE(challenge->monsterIds.size(), maximumCounts[difficulty - 1]);
                    CHECK_EQ(challenge->goldReward, level * rewards[difficulty - 1]);
                    std::set<int16_t> types;
                    for (int16_t id : challenge->monsterIds)
                    {
                        CHECK_GE(id, world.minimumMonster);
                        CHECK_LE(id, world.maximumMonster);
                        REQUIRE(monsters.findById(id) != nullptr);
                        const Game::MonsterTable::MonsterStatsEntry &stats = *monsters.findStatsById(id);
                        CHECK_GE(stats.level, levelCase.monsterLevels[difficulty - 1][0]);
                        CHECK_LE(stats.level, levelCase.monsterLevels[difficulty - 1][1]);
                        CHECK_FALSE(stats.hasKind(Game::MonsterKind::NoArena));
                        CHECK_FALSE(stats.hasKind(Game::MonsterKind::Peasant));
                        types.insert(id);
                    }
                    CHECK_LE(types.size(), 6);
                }
            }
        }
    }
}

TEST_CASE("arena master offers four difficulties and awards a completed fight exactly once in MM6 MM7 MM8")
{
    REQUIRE_MESSAGE(Tests::regressionGameDataLoaded(), Tests::regressionGameDataFailure());
    const Game::MonsterTable monsters = arenaMonsters();
    for (const ArenaWorld &world : Arenas)
    {
        CAPTURE(world.world);
        for (uint32_t difficulty = 1; difficulty <= 4; ++difficulty)
        {
            CAPTURE(difficulty);
            const Game::MapStatsEntry map = arenaMap(world);
            Tests::HouseDialogueTestHarness harness(Tests::regressionGameData());
            Game::MapDeltaData mapData;
            harness.setCurrentMap(map);
            harness.worldRuntime().bindMonsterTable(&monsters);
            harness.worldRuntime().bindMapDeltaData(&mapData);
            harness.worldRuntime().bindArenaMap(&map);
            for (size_t member = 0; member < harness.party().members().size(); ++member)
            {
                harness.party().member(member)->level = 20;
            }

            harness.openNpcDialogue(world.npc);
            harness.executeAndPresent(actionIndex(harness.activeDialog(), Game::EventDialogActionKind::NpcTopic, 704));
            REQUIRE_EQ(harness.activeDialog().actions.size(), 4);
            CHECK_EQ(harness.activeDialog().actions[0].label, "Page");
            CHECK_EQ(harness.activeDialog().actions[1].label, "Squire");
            CHECK_EQ(harness.activeDialog().actions[2].label, "Knight");
            CHECK_EQ(harness.activeDialog().actions[3].label, "Lord");
            harness.executeAndPresent(difficulty - 1);
            CHECK_FALSE(harness.activeDialog().isActive);
            REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
            CHECK_FALSE(harness.eventRuntimeState().pendingMapMove->mapName.has_value());
            CHECK_EQ(harness.eventRuntimeState().pendingMapMove->x, 3849);
            CHECK_EQ(harness.eventRuntimeState().pendingMapMove->y, 5770);
            REQUIRE_GE(mapData.actors.size(), 6);
            for (const Game::MapDeltaActor &actor : mapData.actors)
            {
                CHECK_FALSE(actor.proceduralDeathLoot);
                CHECK_EQ(actor.hostilityType, 4);
                CHECK_EQ(actor.group, 1u);
                CHECK_GE(actor.monsterId, world.minimumMonster);
                CHECK_LE(actor.monsterId, world.maximumMonster);
            }
            const size_t originalCount = mapData.actors.size();
            CHECK_FALSE(Game::startArenaChallenge(harness.worldRuntime(), Game::ArenaDifficulty::Lord, 1));
            CHECK_EQ(mapData.actors.size(), originalCount);

            // Snapshot cleanup must preserve the active challenge and the promised reward.
            Game::clearTransientEventRuntimeState(harness.eventRuntimeState());
            const int goldBefore = harness.party().gold();
            const uint16_t winVariable = uint16_t(Game::EvtVariable::ArenaWinsPage) + difficulty - 1;
            CHECK(Game::interactWithArena(harness.worldRuntime(), world.npc));
            CHECK_EQ(harness.party().gold(), goldBefore);
            for (Game::MapDeltaActor &actor : mapData.actors)
            {
                actor.hp = 0;
            }
            mapData.actors.back().hp = 1;
            CHECK(Game::interactWithArena(harness.worldRuntime(), world.npc));
            CHECK_EQ(harness.party().eventVariableValue(winVariable), 0);
            mapData.actors.back().hp = 0;
            Game::MapDeltaActor summon = {};
            summon.hp = 50;
            summon.ally = 999;
            mapData.actors.push_back(summon);
            CHECK_FALSE(Game::interactWithArena(harness.worldRuntime(), world.npc));
            CHECK_EQ(harness.party().eventVariableValue(winVariable), 1);
            const std::array<int, 4> rewards = {1000, 2000, 4000, 10000};
            CHECK_EQ(harness.party().gold(), goldBefore + rewards[difficulty - 1]);
            for (size_t member = 0; member < harness.party().members().size(); ++member)
            {
                CHECK(harness.party().hasAward(member, 45 + difficulty));
            }
            CHECK_FALSE(Game::interactWithArena(harness.worldRuntime(), world.npc));
            CHECK_EQ(harness.party().eventVariableValue(winVariable), 1);
            CHECK_EQ(harness.party().gold(), goldBefore + rewards[difficulty - 1]);
        }
    }
}

TEST_CASE("MAW arena bouts past level 100 draw from the twelve types nearest the range (audit OVR2-2-2)")
{
    const Game::MonsterTable monsters = arenaMonsters();
    Game::MawRules rules(Game::RulesetOptions{}, Game::MawMapLevels{});
    Game::Party party;
    Game::PartySeed seed = {};
    seed.members.push_back(Game::Character{});
    party.seed(seed);
    party.member(0)->level = 200;

    for (const ArenaWorld &world : Arenas)
    {
        CAPTURE(world.world);
        const Game::MapStatsEntry map = arenaMap(world);
        const auto typesDrawn = [&](const Game::Party &drawer)
        {
            std::set<int16_t> types;

            for (uint32_t randomSeed = 0; randomSeed < 40; ++randomSeed)
            {
                const auto challenge = Game::generateArenaChallenge(
                    monsters, map, drawer, Game::ArenaDifficulty::Lord, randomSeed);
                REQUIRE(challenge.has_value());
                types.insert(challenge->monsterIds.begin(), challenge->monsterIds.end());
            }

            return types.size();
        };
        const size_t standard = typesDrawn(party);
        party.setRules(&rules.gameRules());
        CHECK(typesDrawn(party) >= std::min<size_t>(6, standard + 2));
        party.setRules(nullptr);
    }
}

TEST_CASE("MAW arena bouts in d42 draw by the six-fold arena levels, not the table's")
{
    // A level 28 party's Squire bout brought Cyclops Hunters with 27,000 hit points: table level in the Squire range,
    // six times that in the Arena.
    const Game::MonsterTable monsters = arenaMonsters();
    Game::MawRules rules(Game::RulesetOptions{}, Game::MawMapLevels{});
    Game::Party party;
    Game::PartySeed seed = {};
    seed.members.push_back(Game::Character{});
    party.seed(seed);
    party.member(0)->level = 28;
    party.setRules(&rules.gameRules());
    const Game::MapStatsEntry map = arenaMap(Arenas[2]);
    // Squire at 28: 14..42. d42 levels (zzMaw-Monsters.lua:577-582); the bout takes the twelve nearest types.
    const auto distance = [&](int id)
    {
        const double base = monsters.findStatsById(int16_t(id))->level;
        const double familyLevel = monsters.findStatsById(int16_t(Game::mawMonsterFamily(&monsters, id).row(2)))->level;
        const int level = int(std::lround(std::max(base * 6 - (base - familyLevel) * 6 * 0.8, 5.0)));
        return std::max({14 - level, level - 42, 0});
    };
    std::vector<int> distances;

    for (int id = map.arena->minimumMonsterId; id <= map.arena->maximumMonsterId; ++id)
    {
        const Game::MonsterTable::MonsterStatsEntry *pStats = monsters.findStatsById(int16_t(id));

        if (pStats != nullptr && pStats->hitPoints > 0 && !pStats->hasKind(Game::MonsterKind::NoArena)
            && !pStats->hasKind(Game::MonsterKind::Peasant) && monsters.findById(int16_t(id)) != nullptr)
        {
            distances.push_back(distance(id));
        }
    }
    std::sort(distances.begin(), distances.end());
    REQUIRE_GE(distances.size(), 12);
    const int farthest = distances[11];
    CHECK_LE(farthest, 10);

    for (uint32_t randomSeed = 0; randomSeed < 40; ++randomSeed)
    {
        CAPTURE(randomSeed);
        const auto challenge = Game::generateArenaChallenge(
            monsters, map, party, Game::ArenaDifficulty::Squire, randomSeed);
        REQUIRE(challenge.has_value());

        for (int16_t id : challenge->monsterIds)
        {
            CAPTURE(id);
            CHECK_LE(distance(id), farthest);
        }
    }
}

TEST_CASE("arena invalid difficulty or unavailable opponent pool cannot begin a challenge")
{
    const Game::MonsterTable monsters = arenaMonsters();
    Game::Party party;
    Game::PartySeed seed = {};
    seed.members.push_back(Game::Character{});
    party.seed(seed);
    const Game::MapStatsEntry map = arenaMap(Arenas[2]);
    CHECK_FALSE(Game::generateArenaChallenge(monsters, map, party, Game::ArenaDifficulty(0), 0));
    CHECK_FALSE(Game::generateArenaChallenge(monsters, map, party, Game::ArenaDifficulty(5), 0));
    Game::MapStatsEntry onlyPeasants = map;
    onlyPeasants.arena->minimumMonsterId = 1;
    onlyPeasants.arena->maximumMonsterId = 3;
    party.member(0)->level = 6;
    CHECK_FALSE(Game::generateArenaChallenge(monsters, onlyPeasants, party, Game::ArenaDifficulty::Page, 0));
}

TEST_CASE("arena opponents from hostile factions share a group and never target each other")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assetFileSystem));
    const Game::MonsterTable &monsters = data.getMonsterTable();

    int16_t firstMonsterId = 0;
    int16_t secondMonsterId = 0;
    for (int16_t first = 1; first <= 198 && firstMonsterId == 0; ++first)
    {
        for (int16_t second = 1; second <= 198; ++second)
        {
            if (monsters.findStatsById(first) != nullptr && monsters.findStatsById(second) != nullptr
                && monsters.getRelationBetweenMonsters(first, second) > 0)
            {
                firstMonsterId = first;
                secondMonsterId = second;
                break;
            }
        }
    }
    REQUIRE_NE(firstMonsterId, 0);

    Game::GameplayActorService service = {};
    service.bindTables(&monsters, &data.getSpellTable());

    Game::GameplayActorTargetPolicyState attacker = {};
    attacker.monsterId = firstMonsterId;
    attacker.hostileToParty = true;
    attacker.height = 128;

    Game::GameplayActorTargetPolicyState opponent = attacker;
    opponent.monsterId = secondMonsterId;

    CHECK(service.resolveActorTargetPolicy(attacker, opponent).canTarget);

    attacker.group = 1;
    opponent.group = 1;
    CHECK_FALSE(service.resolveActorTargetPolicy(attacker, opponent).canTarget);

    Game::GameplayActorTargetPolicyState summon = {};
    summon.monsterId = secondMonsterId;
    summon.group = 1;
    summon.height = 128;
    summon.controlMode = Game::GameplayActorControlMode::Enslaved;
    CHECK(service.resolveActorTargetPolicy(attacker, summon).canTarget);
}
