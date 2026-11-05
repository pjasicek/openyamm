#include "PartySpellTestHarness.h"
#include "doctest/doctest.h"
#include "game/gameplay/GameplayMonsterSpawn.h"
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
    inputs.mapName = "Ravenshore";
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

TEST_CASE("a MAW dimension run refills its map once and lasts until the map refills again")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterHealth), int(MawMapAffix::BossDensity), 0, 0};
    run.power = 10;
    run.entering = true;
    rules.state().dimensionRuns["6d02.blv"] = run;
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

    // The run's own load refills the map and keeps it; the next refill ends it.
    monsters.mapLoaded("6d02.blv", true);
    REQUIRE(rules.dimensionRun("6d02.blv") != nullptr);
    CHECK_FALSE(rules.dimensionRun("6d02.blv")->entering);
    CHECK_FALSE(monsters.mapRefillForced("6d02.blv"));
    monsters.mapLoaded("6d02.blv", false);
    CHECK(rules.dimensionRun("6d02.blv") != nullptr);
    monsters.mapLoaded("6d02.blv", true);
    CHECK(rules.dimensionRun("6d02.blv") == nullptr);
    CHECK_FALSE(rules.mapAffix(MawMapAffix::MonsterHealth));
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
    const GameplayMonsterBolsterResult strong = rules.gameRules().monsters.resolveMonster(context, stats, nullptr);

    // Power 0: +20 % HP (live HP, unlike MAW), +30 % speed, and Dragon Breath (5 %, skill 5) over Fireball.
    CHECK_EQ(strong.rulesetFacts.level, plain.rulesetFacts.level + 20);
    CHECK_EQ(strong.moveSpeed, uint16_t(mawRound(plain.moveSpeed * 1.3)));
    CHECK_EQ(strong.generatedSpell1Id, 97u);
    CHECK_EQ(strong.generatedSpell1UseChance, 5);
    CHECK_EQ(strong.spell1SkillLevel, 5u);

    run.affixes = {int(MawMapAffix::MonsterHealth), 0, 0, 0};
    rules.state().dimensionRuns["6d02.blv"] = run;
    const GameplayMonsterBolsterResult healthy = rules.gameRules().monsters.resolveMonster(context, stats, nullptr);
    const GameplayMonsterBolsterResult levelled = [&]()
    {
        // The same level without the affix: the run's level with its health affix taken away.
        run.affixes = {int(MawMapAffix::BossDensity), 0, 0, 0};
        rules.state().dimensionRuns["6d02.blv"] = run;
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
    CHECK(plain.gameRules().items.canDropToWorld(map, definition));
}

TEST_CASE("MAW dimension affix 12 raises unnamed monsters' resistances, up to 200 + X and 999 (MON-6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, installedDimensionData());
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterResistance), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
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
