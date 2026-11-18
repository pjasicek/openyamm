#include "PartySpellTestHarness.h"
#include "doctest/doctest.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/items/CraftingRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRulesetFields.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawExperienceRules.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// MAW's dimension maps (devdocs/maw/data/dimension_affixes.yml, rulesets/maw/data/dimension_maps.yml).
namespace
{
MawDimensionData installedDimensionData()
{
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/dimension_maps.yml");
    const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    MawDimensionData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(text, error), error);
    return data;
}

std::vector<std::string> monsterRow(int id, const std::string &picture, int level)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = picture;
    row[2] = picture;
    row[3] = std::to_string(level);
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}
}

TEST_CASE("the installed MAW dimension maps load with MAW's affix values")
{
    const MawDimensionData data = installedDimensionData();
    CHECK_EQ(data.mapItemId(), 290u);
    CHECK_EQ(data.affixCount(), 33);
    CHECK_EQ(data.dungeons().size(), 143u);
    CHECK_EQ(data.families(true).size(), 145u);
    CHECK_EQ(data.families(false).size(), 154u);

    // The examples of dimension_affixes.yml at power 10, 30 and 60.
    const auto values = [&data](MawMapAffix affix)
    {
        return std::vector<double>{*data.affixValue(int(affix), 10), *data.affixValue(int(affix), 30),
            *data.affixValue(int(affix), 60)};
    };
    CHECK_EQ(values(MawMapAffix::MonsterDamage), std::vector<double>{25, 35, 50});
    CHECK_EQ(values(MawMapAffix::Fireball), std::vector<double>{20, 40, 70});
    CHECK_EQ(values(MawMapAffix::ControlResistance), std::vector<double>{28.57, 37.5, 47.37});
    CHECK_EQ(values(MawMapAffix::PlayerRegeneration), std::vector<double>{23.08, 33.33, 44.44});
    CHECK(*data.affixValue(int(MawMapAffix::ReflectPhysical), 10) == doctest::Approx(8.5));
    // Chances stop at 100.
    CHECK_EQ(*data.affixValue(int(MawMapAffix::EnergyDamage), 100), 100);
    CHECK_FALSE(data.affixValue(34, 10));

    CHECK_EQ(data.affixLine(int(MawMapAffix::ControlResistance), 10),
             "Monsters have 28.57% extra chance to resist control effects");
    CHECK_EQ(data.affixLine(int(MawMapAffix::MonsterResistance), 10), "Monster resistances are increased by 50");
    CHECK_EQ(mawDimensionMapLevel(10, {14, 14, 17}), 135);

    // Quest tiers (MAW aef88884): 80, then +30, +29, ... down to +10; 22 tiers reach the unlock at 500.
    CHECK_EQ(data.quest().firstTier, 80);
    CHECK_EQ(data.nextQuestTier(80), 110);
    CHECK_EQ(data.nextQuestTier(110), 139);
    CHECK_EQ(data.nextQuestTier(139), 167);
    CHECK_EQ(data.nextQuestTier(490), 500);
    CHECK_EQ(data.nextQuestTier(500), 510);
    // A tier from the old ladder moves onto the new one.
    CHECK_EQ(data.nextQuestTier(100), 110);
    CHECK_EQ(data.nextQuestTier(155), 167);
    int tier = data.quest().firstTier;
    int tiers = 1;

    while (tier < data.quest().unlockTier)
    {
        tier = data.nextQuestTier(tier);
        ++tiers;
    }

    CHECK_EQ(tier, 500);
    CHECK_EQ(tiers, 22);
}

TEST_CASE("MAW dimension maps roll distinct affixes into their slots")
{
    const MawDimensionData data = installedDimensionData();

    for (uint64_t seed = 1; seed <= 50; ++seed)
    {
        RandomStream stream(randomStreamKey(seed, RandomDomain::Dimension));
        const std::array<uint8_t, 4> all = data.rollAffixes(stream, {true, true, true, true});
        CHECK_EQ(std::set<uint8_t>(all.begin(), all.end()).size(), 4u);
        CHECK(std::all_of(all.begin(), all.end(), [](uint8_t affix) { return affix >= 1 && affix <= 33; }));

        const std::array<uint8_t, 4> some = data.rollAffixes(stream, {false, true, false, true});
        CHECK_EQ(some[0], 0);
        CHECK_EQ(some[2], 0);
        CHECK(some[1] != 0);
        CHECK(some[3] != 0);
    }

    MawDimensionMap map;
    map.affixes = {3, 7, 9, 0};
    map.activeSlots = 2;
    CHECK_EQ(map.activeAffixes(), std::array<uint8_t, 4>{3, 7, 0, 0});
    CHECK_EQ(map.activeAffixCount(), 2);
    map.activeSlots = 0;
    CHECK_EQ(map.activeAffixCount(), 3);

    ItemRulesetFields fields;
    map.mapId = 152;
    map.power = 30;
    map.writeFields(fields);
    CHECK_FALSE(fields.empty());
    CHECK_EQ(MawDimensionMap::fromFields(fields).power, 30);
    CHECK_EQ(MawDimensionMap::fromFields(fields).mapId, 152);
}

TEST_CASE("MAW monster levels on a dimension map ignore the party's banks")
{
    std::vector<std::vector<std::string>> rows;
    const auto family = [&rows](int firstId, const std::string &picture, int a, int b, int c)
    {
        rows.push_back(monsterRow(firstId, picture + " A", a));
        rows.push_back(monsterRow(firstId + 1, picture + " B", b));
        rows.push_back(monsterRow(firstId + 2, picture + " C", c));
    };
    family(85, "Dire Wolf", 9, 14, 19);
    family(100, "Centaur", 11, 14, 18);
    family(193, "Human Mercenary", 10, 17, 24);
    MonsterTable monsters;
    REQUIRE(monsters.loadStatsFromRows(rows));
    MawMapLevels mapLevels;
    std::string error;
    REQUIRE_MESSAGE(
        mapLevels.loadFromYaml(
            "bands:\n  out02.odm: [14, 14, 17]\nhorizontal_starter_maps: []\n"
            "madness:\n  starting_maps: []\n  levels: {}\n",
            error),
        error);

    MawMonsterLevelInputs inputs;
    inputs.mapFileName = "out02.odm";
    inputs.encounterPictures = {"Human Mercenary", "Centaur", "Dire Wolf"};
    inputs.dimensionPower = 10;
    const std::vector<int> expected = {129, 134, 139, 131, 134, 138, 130, 137, 144};

    for (const double partyLevel : {0.0, 100.0})
    {
        inputs.partyLevel = partyLevel;
        inputs.horizontalProgression = partyLevel > 0;
        const std::unordered_map<int, int> levels = resolveMawMonsterLevels(monsters, mapLevels, inputs);
        std::vector<int> actual;

        for (int id : {85, 86, 87, 100, 101, 102, 193, 194, 195})
        {
            actual.push_back(levels.at(id));
        }

        CHECK_EQ(actual, expected);
    }
}

TEST_CASE("a MAW dimension run is a rift beside its map: placed once, and the map's refills never end it")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterHealth), int(MawMapAffix::BossDensity), 0, 0};
    run.power = 10;
    run.entering = true;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    rules.setCurrentMap("6D02.blv");

    CHECK(monsters.mapRefillForced("6D02.BLV"));
    CHECK(rules.mapAffix(MawMapAffix::MonsterHealth) == doctest::Approx(35));
    CHECK_FALSE(rules.mapAffix(MawMapAffix::Fireball));
    CHECK_FALSE(rules.mapAffix("6d01.blv", MawMapAffix::MonsterHealth));

    // Density: each group's upper count x (1 + 30 x 2 / 300).
    MapStatsEntry map = {};
    map.fileName = "6d02.blv";
    map.encounter1.maxCount = 5;
    map.encounter2.maxCount = 3;
    monsters.adjustMapEncounters(map);
    CHECK_EQ(map.encounter1.maxCount, 6);
    CHECK_EQ(map.encounter2.maxCount, 4);

    // The rift's first load places it, whatever state an older rift left there; the map's own records stay.
    rules.state().clearedSinceRefill.insert("6d02.blv");
    rules.state().mapsDropped["6d02.blv"] = 2;
    monsters.mapLoaded("6d02.blv", true);
    REQUIRE(rules.dimensionRun("6d02.blv") != nullptr);
    CHECK_FALSE(rules.dimensionRun("6d02.blv")->entering);
    CHECK_FALSE(monsters.mapRefillForced("6d02.blv"));
    CHECK(rules.state().clearedSinceRefill.contains("6d02.blv"));
    CHECK_EQ(rules.state().mapsDropped["6d02.blv"], 2);
    // In the rift the map counts as cleared only once the rift is.
    CHECK_FALSE(rules.clearedSinceRefill("6d02.blv"));
    CHECK_EQ(monsters.liveMapInstances().size(), 1u);

    // Outside the rift the map is itself: no run, no affix, its own records, and a refill of it leaves the rift.
    rules.setMapInstanceId({});
    CHECK(rules.dimensionRun("6d02.blv") == nullptr);
    CHECK_FALSE(rules.mapAffix(MawMapAffix::MonsterHealth));
    CHECK(rules.clearedSinceRefill("6d02.blv"));
    CHECK_FALSE(rules.inRift());
    monsters.mapLoaded("6d02.blv", true);
    CHECK_FALSE(rules.state().clearedSinceRefill.contains("6d02.blv"));
    REQUIRE(rules.rift() != nullptr);
    CHECK_EQ(rules.rift()->first, "6d02.blv");

    // The ways out of a dungeon's rift entered from New Sorpigal: outdoors leads back there, Town Portal where it
    // says, another dungeon nowhere; a move within the rift's own map stays. No road, ship or Lloyd's Beacon.
    rules.rift()->second.originMapFileName = "oute3.odm";
    rules.rift()->second.originX = 100;
    rules.rift()->second.originY = -200;
    rules.rift()->second.originZ = 30;
    CHECK_FALSE(monsters.mapTravelRefusal());
    CHECK_FALSE(monsters.lloydsBeaconRefusal());
    rules.setMapInstanceId(MawRiftInstanceId);
    CHECK(monsters.mapTravelRefusal());
    CHECK(monsters.lloydsBeaconRefusal());
    const MapInstanceExit door = monsters.mapInstanceExit("outd2.odm", false, "lua_event");
    CHECK(door.kind == MapInstanceExit::Kind::Redirect);
    CHECK_EQ(door.mapFileName, "oute3.odm");
    CHECK_EQ(door.x, 100);
    CHECK_EQ(door.y, -200);
    CHECK_EQ(door.z, 30);
    CHECK(monsters.mapInstanceExit("6d03.blv", false, "lua_event").kind == MapInstanceExit::Kind::Refuse);
    CHECK(monsters.mapInstanceExit("6d02.blv", true, "lua_event").kind == MapInstanceExit::Kind::Stay);
    CHECK(monsters.mapInstanceExit("6d02.blv", true, "town_portal").kind == MapInstanceExit::Kind::Leave);
    CHECK(monsters.mapInstanceExit("oute3.odm", false, "town_portal").kind == MapInstanceExit::Kind::Leave);
}

TEST_CASE("MAW dimension affixes strengthen the map's monsters")
{
    std::vector<std::vector<std::string>> rows = {monsterRow(193, "Human Mercenary A", 10),
        monsterRow(194, "Human Mercenary B", 17), monsterRow(195, "Human Mercenary C", 24)};
    MonsterTable monsters;
    REQUIRE(monsters.loadStatsFromRows(rows));
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    MapStatsEntry map = {};
    map.fileName = "6d02.blv";
    map.encounter1.pictureName = "Human Mercenary";
    GameplayBolsterRuntimeContext context = {};
    context.pMap = &map;
    context.pMonsterTable = &monsters;
    const MonsterTable::MonsterStatsEntry &stats = *monsters.findStatsById(194);
    const GameplayMonsterBolsterResult plain = rules.gameRules().monsters.resolveMonster(context, stats, nullptr);

    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterHealth), int(MawMapAffix::MonsterSpeed), int(MawMapAffix::Fireball),
        int(MawMapAffix::DragonBreath)};
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    const GameplayMonsterBolsterResult strong = rules.gameRules().monsters.resolveMonster(context, stats, nullptr);

    // Power 0: +20 % HP (live HP, unlike MAW), +30 % speed, and Dragon Breath (5 %, skill 5) over Fireball.
    CHECK_EQ(strong.rulesetFacts.level, plain.rulesetFacts.level + 20);
    CHECK_EQ(strong.moveSpeed, uint16_t(mawRound(plain.moveSpeed * 1.3)));
    CHECK_EQ(strong.generatedSpell1Id, 97u);
    CHECK_EQ(strong.generatedSpell1UseChance, 5);
    CHECK_EQ(strong.spell1SkillLevel, 5u);

    run.affixes = {int(MawMapAffix::MonsterHealth), 0, 0, 0};
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    const GameplayMonsterBolsterResult healthy = rules.gameRules().monsters.resolveMonster(context, stats, nullptr);
    const GameplayMonsterBolsterResult levelled = [&]()
    {
        // The same level without the affix: the run's level with its health affix taken away.
        run.affixes = {int(MawMapAffix::BossDensity), 0, 0, 0};
        rules.state().dimensionRuns["6d02.blv"] = run;
        rules.setMapInstanceId(MawRiftInstanceId);
        return rules.gameRules().monsters.resolveMonster(context, stats, nullptr);
    }();
    CHECK(double(healthy.maxHp) == doctest::Approx(levelled.maxHp * 1.2).epsilon(0.01));
}

TEST_CASE("Beyond Madness keeps dimension maps out of the world (P9.M6)")
{
    const MawDimensionData data = installedDimensionData();
    REQUIRE_NE(data.mapItemId(), 0u);
    RulesetOptions madness;
    madness.challengeMode = RulesetChallengeMode::BeyondMadness;
    madness.difficulty = RulesetDifficulty::Nightmare;
    madness.progression = RulesetProgression::Horizontal;
    MawRules mad(madness, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{}, MawTextData{}, data);
    MawRules plain(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, data);
    const ItemDefinition definition;
    const InventoryItem map{.objectDescriptionId = data.mapItemId()};
    const InventoryItem other{.objectDescriptionId = 1};
    CHECK_FALSE(mad.gameRules().items.canDropToWorld(map, definition));
    CHECK(mad.gameRules().items.canDropToWorld(other, definition));

    // Elsewhere a map is bound while the Dimensional Maps quest runs (its giver is the only source, and a lost map
    // would end the quest): not dropped, not sold. The dimensional portal is bound always.
    Party party;
    const InventoryItem portal{.objectDescriptionId = data.portalItemId()};
    REQUIRE_NE(data.portalItemId(), 0u);
    CHECK_FALSE(plain.gameRules().items.canDropToWorld(map, definition));
    CHECK(plain.gameRules().items.sellRefusal(party, map));
    CHECK(plain.gameRules().items.canDropToWorld(other, definition));
    plain.state().dimensionQuest.done = true;
    CHECK(plain.gameRules().items.canDropToWorld(map, definition));
    CHECK_FALSE(plain.gameRules().items.sellRefusal(party, map));
    CHECK_FALSE(plain.gameRules().items.canDropToWorld(portal, definition));
    CHECK(plain.gameRules().items.sellRefusal(party, portal));
}

TEST_CASE("MAW dimension affix 12 raises unnamed monsters' resistances, up to 200 + X and 999 (MON-6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterResistance), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    rules.setCurrentMap("6d02.blv");
    REQUIRE(rules.mapAffix(MawMapAffix::MonsterResistance));
    const int bonus = int(*rules.mapAffix(MawMapAffix::MonsterResistance));
    REQUIRE(bonus > 0);

    const MonsterRules &monsters = rules.gameRules().monsters;
    ActorRulesetFacts unnamed;
    unnamed.level = 50;
    ActorRulesetFacts boss = unnamed;
    boss.bossAffix = 1;
    ActorRulesetFacts unique = unnamed;
    unique.unique = true;
    ActorRulesetFacts risen = unnamed;
    risen.risen = true;

    // The inspect panel shows what the damage reads.
    CHECK_EQ(monsters.monsterResistanceText(40, unnamed), std::to_string(40 + bonus));
    CHECK_EQ(monsters.monsterResistanceText(250, unnamed), std::to_string(200 + bonus));
    CHECK_EQ(mawCappedMonsterResistance(950, 900), 999);

    for (const ActorRulesetFacts *pNamed : {&boss, &unique, &risen})
    {
        CHECK_EQ(monsters.monsterResistanceText(40, *pNamed), "40");
        CHECK_EQ(monsters.monsterResistanceText(250, *pNamed), "200");
    }

    std::mt19937 rng(5);
    const auto fireDamage = [&rules, &rng](const ActorRulesetFacts &facts)
    {
        MonsterDamageHit hit;
        hit.amount = 1000;
        hit.type = CombatDamageType::Fire;
        hit.resistance = 100;
        hit.targetFacts = facts;
        hit.pRng = &rng;
        return rules.gameRules().combat.damageToMonster(hit);
    };
    CHECK_EQ(fireDamage(unnamed), int(std::ceil(1000 / mawMonsterResistanceDivisor(100 + bonus))));
    CHECK_EQ(fireDamage(boss), int(std::ceil(1000 / mawMonsterResistanceDivisor(100))));

    // Outside the run nothing changes.
    rules.setCurrentMap("6d01.blv");
    CHECK_EQ(monsters.monsterResistanceText(40, unnamed), "40");
}

TEST_CASE("MAW kill experience leaves the dimension +HP affix out of the health ratio (MON-10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    Character member;
    member.level = 40;
    member.experience = 2000000;
    rules.setCurrentMap("6d02.blv");
    const MawMemberKillExperience plain = mawMemberKillExperience(rules, member, 4, 1000, 12000);

    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterHealth), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    const std::optional<double> affix = rules.mapAffix(MawMapAffix::MonsterHealth);
    REQUIRE(affix);
    // The same monster with the affix's extra health is worth the same.
    const int raisedHp = int(12000 * (1 + *affix / 100));
    const MawMemberKillExperience raised = mawMemberKillExperience(rules, member, 4, 1000, raisedHp);
    CHECK(raised.award == doctest::Approx(plain.award).epsilon(0.001));
}

TEST_CASE("MAW dimension rolls of different kinds never share a stream key (audit ROB-2-9)")
{
    // A run of power 19 completed with no maps dropped once keyed like the map's BecomeBoss roll.
    const uint64_t map = randomNameKey("d12.blv");
    const uint64_t completion = randomStreamKey(7, RandomDomain::DimensionCompletion, map, 0, 19);
    const uint64_t becomeBoss = randomStreamKey(7, RandomDomain::DimensionBecomeBoss, map, 0, 19);
    const uint64_t higherTier = randomStreamKey(7, RandomDomain::DimensionHigherTier, map, 0, 19);
    CHECK_NE(completion, becomeBoss);
    CHECK_NE(completion, higherTier);
    CHECK_NE(becomeBoss, higherTier);
}

namespace
{
// Records the monsters the rules spawn; the listed actor ids fight for the party.
class SummonTestWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override
    {
        spawns.push_back(request);
        return {};
    }

    bool actorRulesView(size_t actorIndex, GameplayActorRulesView &view) const override
    {
        if (!PartySpellTestWorldRuntime::actorRulesView(actorIndex, view))
        {
            return false;
        }

        view.partyAlly = allies.contains(view.actorId);
        return true;
    }

    std::vector<GameplayMonsterSpawnRequest> spawns;
    std::set<uint32_t> allies;
};

// How many of the given actors call a monster as they die, however they die.
size_t summonsOnDeath(MawRules &rules, size_t actors, bool risen, bool allied)
{
    const MonsterRules &monsters = rules.gameRules().monsters;
    SummonTestWorld world;

    for (uint32_t actorId = 1; actorId <= actors; ++actorId)
    {
        GameplayRuntimeActorState actor = {};
        actor.actorId = actorId;
        actor.monsterId = 194;
        actor.preciseX = float(actorId);
        actor.hostileToParty = true;
        actor.currentHp = 100;
        actor.maxHp = 100;
        actor.rulesetFacts.level = 30;
        actor.rulesetFacts.risen = risen;
        world.addActor(actor);

        if (allied)
        {
            world.allies.insert(actorId);
        }
    }

    monsters.updateMonsters(world, 0.016f);
    REQUIRE(world.spawns.empty());

    for (size_t index = 0; index < actors; ++index)
    {
        world.actor(index).isDead = true;
        world.actor(index).currentHp = 0;
    }

    monsters.updateMonsters(world, 0.016f);
    monsters.updateMonsters(world, 0.016f);

    for (const GameplayMonsterSpawnRequest &request : world.spawns)
    {
        CHECK_EQ(request.monsterId, 194);
        CHECK_EQ(request.tierWeights, std::array<int, 3>{55, 30, 15});
        CHECK_EQ(request.radius, 128.0f);
    }

    return world.spawns.size();
}
}

TEST_CASE("MAW's summon-on-death affix rolls on every monster death (audit FCOR-2-40)")
{
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::SummonOnDeath), 0, 0, 0};
    run.power = 10;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    rules.setCurrentMap("6d02.blv");
    REQUIRE(rules.mapAffix(MawMapAffix::SummonOnDeath));
    const double chance = *rules.mapAffix(MawMapAffix::SummonOnDeath) / 100;
    constexpr size_t Actors = 2000;

    // No party kill involved: the actors simply die.
    const size_t summoned = summonsOnDeath(rules, Actors, false, false);
    CHECK(summoned > size_t(Actors * chance * 0.8));
    CHECK(summoned < size_t(Actors * chance * 1.2));

    // Not from the risen nor the party's allies.
    CHECK_EQ(summonsOnDeath(rules, 200, true, false), 0u);
    CHECK_EQ(summonsOnDeath(rules, 200, false, true), 0u);

    // Nor on a map without the affix.
    rules.setCurrentMap("6d01.blv");
    CHECK_EQ(summonsOnDeath(rules, 200, false, false), 0u);

    // Nor in Beyond Madness's arenas.
    RulesetOptions madness;
    madness.challengeMode = RulesetChallengeMode::BeyondMadness;
    MawRules arena(madness, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{}, MawTextData{},
        installedDimensionData());
    arena.state().dimensionRuns["zarena.blv"] = run;
    arena.setMapInstanceId(MawRiftInstanceId);
    arena.setCurrentMap("zarena.blv");
    REQUIRE(arena.mapAffix(MawMapAffix::SummonOnDeath));
    CHECK_EQ(summonsOnDeath(arena, 200, false, false), 0u);
}

TEST_CASE("MAW dimension affixes 25 and 33 slow the party near enemies and weaken buffs once (DEVIATIONS 60)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::PlayerMovement), int(MawMapAffix::BuffEffects), 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);
    rules.setCurrentMap("6d02.blv");
    REQUIRE(rules.mapAffix(MawMapAffix::PlayerMovement));
    REQUIRE(rules.mapAffix(MawMapAffix::BuffEffects));
    const double slow = *rules.mapAffix(MawMapAffix::PlayerMovement);
    const double scale = 1 - *rules.mapAffix(MawMapAffix::BuffEffects) / 100;

    // 33: base and per-skill scaling of every buff power alike, on this map only.
    CHECK(rules.buffScale() == doctest::Approx(scale));
    CHECK(mawAuraFlat(20, 2, 40, 30, rules.buffScale()) == doctest::Approx((20 * scale + 10) * (1 + 2 * scale * 0.3)));
    CHECK(mawBuffMultiplier(5, 30, rules.buffScale()) == doctest::Approx(scale * (0.1 + 0.06)));

    // 25: the party moves 1 - X / 100 as fast while a hostile that has seen it is near, at full speed otherwise.
    PartySeed seed;
    seed.members.resize(1);
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    rules.gameRules().monsters.updateMonsters(world, 0.016f);
    CHECK(party.rulesMovementMultiplier() == doctest::Approx(1.0f));

    GameplayRuntimeActorState actor = {};
    actor.actorId = 1;
    actor.monsterId = 194;
    actor.preciseX = 200;
    actor.hostileToParty = true;
    actor.hasDetectedParty = true;
    actor.currentHp = 100;
    actor.maxHp = 100;
    world.addActor(actor);
    rules.gameRules().monsters.updateMonsters(world, 0.016f);
    CHECK(party.rulesMovementMultiplier() == doctest::Approx(float(1 - slow / 100)));

    rules.setCurrentMap("6d01.blv");
    rules.gameRules().monsters.updateMonsters(world, 0.016f);
    CHECK(party.rulesMovementMultiplier() == doctest::Approx(1.0f));
    CHECK(rules.buffScale() == doctest::Approx(1.0));
}

TEST_CASE("a MAW dimension run makes its families the party's enemies, on its own map only")
{
    std::vector<std::vector<std::string>> rows;

    for (const auto &[firstId, picture] : {std::pair<int, const char *>{85, "Dire Wolf"}, {280, "Griffin"},
             {391, "Roc"}})
    {
        rows.push_back(monsterRow(firstId, std::string(picture) + " A", 10));
        rows.push_back(monsterRow(firstId + 1, std::string(picture) + " B", 15));
        rows.push_back(monsterRow(firstId + 2, std::string(picture) + " C", 20));
    }

    // No hostile.txt: every family is friendly to the party, as MMMerge's table leaves rocs and griffins.
    MonsterTable monsters;
    REQUIRE(monsters.loadStatsFromRows(rows));
    REQUIRE_FALSE(monsters.isHostileToParty(391));
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    const MonsterRules &monsterRules = rules.gameRules().monsters;
    MawDimensionRun run;
    run.families = {391, 280, 85};
    run.power = 10;
    rules.state().dimensionRuns["d14.blv"] = run;
    rules.setMapInstanceId(MawRiftInstanceId);

    // A map without a run keeps the table's relations.
    MapStatsEntry other = {};
    other.fileName = "d13.blv";
    monsterRules.enterMap(other, monsters);
    CHECK_FALSE(monsters.isHostileToParty(391));
    CHECK_FALSE(monsters.isHostileToParty(85));

    MapStatsEntry map = {};
    map.fileName = "d14.blv";
    monsterRules.enterMap(map, monsters);
    CHECK_EQ(map.encounter1.pictureName, "Roc");

    for (int16_t monsterId : {85, 86, 87, 280, 281, 282, 391, 392, 393})
    {
        CHECK(monsters.isHostileToParty(monsterId));
    }

    // Monsters outside the run's families are untouched, and the next map load starts from the table again.
    CHECK_FALSE(monsters.isHostileToParty(100));
    monsters.clearMapFactionRelations();
    CHECK_FALSE(monsters.isHostileToParty(391));
}

TEST_CASE("the Dimensional Maps NPC closes an unfinished quest rift for the same map once 80 % of it is slain")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    rules.setMapTable(&gameData.mapStats);
    const MonsterRules &monsters = rules.gameRules().monsters;
    const ItemRules &items = rules.gameRules().items;
    const uint32_t portalItemId = rules.dimensionData().portalItemId();
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].level = 120;
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.setCurrentMap("oute3.odm");
    MawGameState &state = rules.state();
    const auto mapItems = [&]() { return party.inventoryItemCount(290); };
    const auto portals = [&]() { return party.inventoryItemCount(portalItemId); };
    const auto questMap = [&]()
    {
        for (const InventoryItem &item : party.pouchItems(ItemPouch::Crafting))
        {
            if (item.objectDescriptionId == 290)
            {
                return item;
            }
        }

        return InventoryItem{};
    };

    // Nothing given: nothing to repeat.
    std::optional<RulesTopicReply> reply = monsters.rulesTopic("dimensional_maps_repeat", party, nullptr);
    REQUIRE(reply);
    CHECK(reply->confirmTopic.empty());

    // The quest's map, and the NPC's answer while its rift stands: the repeat is offered.
    state.completedMaps.insert("6d02.blv");
    reply = monsters.rulesTopic("dimensional_maps", party, nullptr);
    REQUIRE(reply);
    CHECK(reply->offeredTopic.empty());
    REQUIRE(state.dimensionQuest.mapGiven);
    REQUIRE_EQ(mapItems(), 1);
    reply = monsters.rulesTopic("dimensional_maps", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(reply->offeredTopic, "dimensional_maps_repeat");
    CHECK_EQ(mapItems(), 1);

    // The rift not opened yet: nothing to give up, and "yes" does nothing either.
    reply = monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(mapItems(), 1);

    // Using the map opens its rift from New Sorpigal and gives the portal; the map is spent by the caller.
    const InventoryItem map = questMap();
    REQUIRE_EQ(map.objectDescriptionId, 290u);

    // The plan, when the player uses the map: where it leads, and nothing changes (the autosave of the map being
    // left is made between the plan and the use, and holds the map unused).
    const std::optional<TravelItemUse> planned = items.planTravelItem(party, map, {100, -200, 30});
    REQUIRE(planned);
    CHECK(planned->refusal.empty());
    CHECK_EQ(planned->instanceId, MawRiftInstanceId);
    CHECK(rules.rift() == nullptr);
    CHECK_EQ(portals(), 0);

    const std::optional<TravelItemUse> opened = items.useTravelItem(party, map, {100, -200, 30});
    REQUIRE(opened);
    CHECK_EQ(opened->mapFileName, planned->mapFileName);
    CHECK(opened->refusal.empty());
    CHECK(opened->consumed);
    CHECK_EQ(opened->instanceId, MawRiftInstanceId);
    CHECK(opened->useMapStartPosition);
    REQUIRE(party.removeItem(290));
    CHECK_EQ(portals(), 1);
    REQUIRE(rules.rift() != nullptr);
    const std::string riftMap = rules.rift()->first;
    CHECK_EQ(rules.rift()->second.questTier, state.dimensionQuest.tierLevel);
    CHECK_EQ(rules.rift()->second.originMapFileName, "oute3.odm");
    CHECK_EQ(rules.rift()->second.originX, 100);

    // While the quest runs, a second map does not open over an unfinished rift.
    const std::optional<TravelItemUse> second = items.useTravelItem(party, map, {0, 0, 0});
    REQUIRE(second);
    CHECK_FALSE(second->refusal.empty());
    CHECK_EQ(rules.rift()->first, riftMap);

    // Never entered, the rift holds nothing to lose: the NPC offers to close it without a creature slain.
    CHECK(rules.rift()->second.entering);
    reply = monsters.rulesTopic("dimensional_maps_repeat", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(reply->confirmTopic, "dimensional_maps_repeat_confirmed");
    CHECK_NE(reply->text.find("never set foot"), std::string::npos);

    // The portal leads in from outside and remembers where from; inside it leads back there, and is kept.
    const InventoryItem portal{.objectDescriptionId = portalItemId};
    rules.setCurrentMap("outd2.odm");
    REQUIRE(items.planTravelItem(party, portal, {7, 8, 9}));
    CHECK_EQ(rules.rift()->second.originMapFileName, "oute3.odm");
    const std::optional<TravelItemUse> in = items.useTravelItem(party, portal, {7, 8, 9});
    REQUIRE(in);
    CHECK_FALSE(in->consumed);
    CHECK_EQ(in->instanceId, MawRiftInstanceId);
    CHECK_EQ(rules.rift()->second.originMapFileName, "outd2.odm");
    rules.setCurrentMap(riftMap);
    rules.setMapInstanceId(MawRiftInstanceId);
    monsters.mapLoaded(riftMap, false);
    CHECK_FALSE(rules.rift()->second.entering);
    const std::optional<TravelItemUse> out = items.useTravelItem(party, portal, {0, 0, 0});
    REQUIRE(out);
    CHECK_FALSE(out->consumed);
    CHECK(out->instanceId.empty());
    CHECK_EQ(out->mapFileName, "outd2.odm");
    CHECK_FALSE(out->useMapStartPosition);
    CHECK_EQ(out->x, 7);

    // Left at 79 of 100: not enough.
    rules.setCurrentMap("outd2.odm");
    rules.setMapInstanceId({});
    rules.rift()->second.slain = 79;
    rules.rift()->second.counted = 100;
    reply = monsters.rulesTopic("dimensional_maps_repeat", party, nullptr);
    REQUIRE(reply);
    CHECK(reply->confirmTopic.empty());
    CHECK_NE(reply->text.find("79 of the 100"), std::string::npos);
    reply = monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(mapItems(), 0);
    CHECK(rules.rift() != nullptr);

    // 80 of 100: the NPC asks, and nothing changes until the party confirms. Standing in the rift, she closes nothing.
    rules.rift()->second.slain = 80;
    reply = monsters.rulesTopic("dimensional_maps_repeat", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(reply->confirmTopic, "dimensional_maps_repeat_confirmed");
    CHECK_EQ(mapItems(), 0);
    rules.setMapInstanceId(MawRiftInstanceId);
    reply = monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(mapItems(), 0);
    CHECK(rules.rift() != nullptr);
    rules.setMapInstanceId({});

    // Confirmed: the same tier's map again, the rift and its portal gone, the quest still open, the map untouched.
    reply = monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(mapItems(), 1);
    CHECK_EQ(portals(), 0);
    CHECK(rules.rift() == nullptr);
    CHECK(monsters.liveMapInstances().empty());
    CHECK_FALSE(monsters.mapRefillForced(riftMap));
    CHECK(state.dimensionQuest.mapGiven);
    CHECK_FALSE(state.dimensionQuest.cleared);
    CHECK_EQ(state.dimensionQuest.tierLevel, 80);
    CHECK(questMap().rulesetFields == map.rulesetFields);

    // A second "yes" finds no rift to give up.
    reply = monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK_EQ(mapItems(), 1);

    // With the quest done, the next map gives an unfinished rift up, and a portal without a rift goes when used.
    REQUIRE(items.useTravelItem(party, map, {1, 2, 3}));
    state.dimensionQuest.done = true;
    rules.rift()->second.slain = 5;
    const std::optional<TravelItemUse> replaced = items.useTravelItem(party, map, {4, 5, 6});
    REQUIRE(replaced);
    CHECK(replaced->refusal.empty());
    CHECK_EQ(rules.rift()->second.slain, 0);
    CHECK_EQ(rules.rift()->second.originX, 4);
    CHECK_EQ(portals(), 1);
    state.dimensionRuns.clear();
    const std::optional<TravelItemUse> stale = items.useTravelItem(party, portal, {0, 0, 0});
    REQUIRE(stale);
    CHECK_FALSE(stale->refusal.empty());
    CHECK(stale->consumed);
}

TEST_CASE("the Dimensional Maps NPC closes a quest rift the party never entered and gives its map again")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    rules.setMapTable(&gameData.mapStats);
    const MonsterRules &monsters = rules.gameRules().monsters;
    const ItemRules &items = rules.gameRules().items;
    const uint32_t portalItemId = rules.dimensionData().portalItemId();
    PartySeed seed;
    seed.members.resize(1);
    seed.members[0].level = 120;
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.setCurrentMap("oute3.odm");
    rules.state().completedMaps = {"6d01.blv", "6d02.blv", "6d03.blv"};

    // The quest's map, used; the party never arrives (a save made between the two, loaded).
    REQUIRE(monsters.rulesTopic("dimensional_maps", party, nullptr));
    REQUIRE_EQ(party.pouchItems(ItemPouch::Crafting).size(), 1);
    const InventoryItem map = party.pouchItems(ItemPouch::Crafting).front();
    REQUIRE_EQ(map.objectDescriptionId, 290u);
    const std::optional<TravelItemUse> opened = items.useTravelItem(party, map, {0, 0, 0});
    REQUIRE(opened);
    REQUIRE(opened->refusal.empty());
    REQUIRE(party.removeItem(290));
    REQUIRE(rules.rift() != nullptr);
    CHECK(rules.rift()->second.entering);
    CHECK_EQ(party.inventoryItemCount(portalItemId), 1);

    // "yes": the rift and its portal are gone, and the same map is in the party's hands again.
    const std::optional<RulesTopicReply> reply =
        monsters.rulesTopic("dimensional_maps_repeat_confirmed", party, nullptr);
    REQUIRE(reply);
    CHECK(rules.rift() == nullptr);
    CHECK_EQ(party.inventoryItemCount(portalItemId), 0);
    REQUIRE_EQ(party.pouchItems(ItemPouch::Crafting).size(), 1);
    CHECK_EQ(party.pouchItems(ItemPouch::Crafting).front().rulesetFields.dimensionMapId,
        map.rulesetFields.dimensionMapId);
    CHECK(rules.state().dimensionQuest.mapGiven);
}

TEST_CASE("a save from before rifts keeps one dimension run as the rift and hands the other maps back")
{
    MawGameState state;
    CHECK(state.keepOneRift("oute3.odm").empty());

    // Three runs lay in their maps' own states: a cleared one, an unfinished one and the one the party stands in.
    MawDimensionRun cleared;
    cleared.completed = true;
    MawDimensionRun open;
    open.power = 4;
    MawDimensionRun here;
    here.power = 9;
    state.dimensionRuns = {{"6d01.blv", cleared}, {"6d02.blv", open}, {"6d03.blv", here}};
    state.mapVisits["6d03.blv"] = {12, 40, 3};
    state.mapsDropped["6d03.blv"] = 2;
    state.clearedSinceRefill = {"6d01.blv", "6d03.blv"};

    MawGameState standing = state;
    CHECK_EQ(standing.keepOneRift("6d03.blv"), "6d03.blv");
    REQUIRE_EQ(standing.dimensionRuns.size(), 1u);
    const MawDimensionRun &rift = standing.dimensionRuns.at("6d03.blv");
    CHECK_EQ(rift.power, 9);
    CHECK_EQ(rift.slain, 12);
    CHECK_EQ(rift.counted, 40);
    CHECK_EQ(rift.mapsDropped, 2);
    // Its map's records of the run are gone, and the other two maps refill as themselves.
    CHECK_FALSE(standing.mapVisits.contains("6d03.blv"));
    CHECK_FALSE(standing.mapsDropped.contains("6d03.blv"));
    CHECK_FALSE(standing.clearedSinceRefill.contains("6d03.blv"));
    CHECK(standing.clearedSinceRefill.contains("6d01.blv"));
    CHECK(standing.pendingRefills == std::unordered_set<std::string>{"6d01.blv", "6d02.blv"});

    // Standing elsewhere: the unfinished run is kept before a cleared one.
    MawGameState away = state;
    away.dimensionRuns.erase("6d03.blv");
    CHECK_EQ(away.keepOneRift("oute3.odm"), "6d02.blv");
    CHECK(away.pendingRefills == std::unordered_set<std::string>{"6d01.blv"});
}

TEST_CASE("MAW dimension maps lie in the crafting pouch, and a save's map in the quest pouch moves there")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    const uint32_t mapItemId = rules.dimensionData().mapItemId();
    const ItemDefinition *pMapRow = gameData.itemTable.get(mapItemId);
    REQUIRE(pMapRow != nullptr);
    CHECK(rules.gameRules().items.pouch(*pMapRow) == ItemPouch::Crafting);
    // As MAW's item table has it (patches/items.txt): worth nothing and no gear, a quest item by that alone.
    ItemDefinition mawRow = *pMapRow;
    mawRow.value = 0;
    mawRow.equipStat = "N / A";
    CHECK(rules.gameRules().items.pouch(mawRow) == ItemPouch::Crafting);

    PartySeed seed;
    seed.members.resize(1);
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    const auto holds = [&party](ItemPouch pouch, uint32_t itemId)
    {
        const std::vector<InventoryItem> &items = party.pouchItems(pouch);
        return std::count_if(items.begin(), items.end(),
            [itemId](const InventoryItem &item) { return item.objectDescriptionId == itemId; });
    };

    // As an older save holds them: the map among the quest items, where the Workbench does not look.
    InventoryItem map = ItemGenerator::makeInventoryItem(mapItemId, gameData.itemTable, ItemGenerationMode::Generic);
    map.rulesetFields.dimensionMapId = 152;
    REQUIRE(party.addToPouch(ItemPouch::Quest, map));
    REQUIRE(party.addToPouch(ItemPouch::Alchemy,
        ItemGenerator::makeInventoryItem(222, gameData.itemTable, ItemGenerationMode::Generic)));

    CHECK_EQ(party.movePouchItemsToTheirPouches(), 1);
    CHECK_EQ(holds(ItemPouch::Crafting, mapItemId), 1);
    CHECK_EQ(holds(ItemPouch::Quest, mapItemId), 0);
    CHECK_EQ(holds(ItemPouch::Alchemy, 222), 1);
    CHECK_EQ(party.pouchItems(ItemPouch::Crafting).front().rulesetFields.dimensionMapId, 152);
    CHECK_EQ(party.movePouchItemsToTheirPouches(), 0);

    // The Workbench lists it there among what it crafts on; the potion is no target.
    CraftingTables tables;
    tables.pItemTable = &gameData.itemTable;
    const std::vector<CraftTargetEntry> targets = CraftingRuntime::collectTargets(party, tables);
    CHECK_EQ(std::count_if(targets.begin(), targets.end(),
                 [mapItemId](const CraftTargetEntry &target) { return target.item.objectDescriptionId == mapItemId; }),
        1);
}
