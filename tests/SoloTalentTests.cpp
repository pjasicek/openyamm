#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"
#include "game/rules/CombatRules.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSoloTalents.h"
#include "game/tables/ItemTable.h"
#include "tests/PartySpellTestHarness.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
const char *TestTable = R"(
levels_per_point: 15
keystone_levels: [150, 300]
talents:
  - {id: cleave, name: Cleave, tree: arms, kind: active, max_rank: 3, requires: expert, cooldown: 12,
     cooldown_per_rank: -2, targets: 64, share: 150, arc: 60, duration: 1}
  - {id: sweeping_blows, name: Sweeping Blows, tree: arms, kind: passive, max_rank: 3, requires: expert, needs: cleave,
     per_rank: 1, share: 30, share_per_skill: 0.25, share_cap: 50, arc: 60}
  - {id: onslaught, name: Onslaught, tree: any, kind: passive, max_rank: 5, per_rank: 6, duration: 30}
  - {id: challenge, name: Challenge, tree: arms, kind: active, max_rank: 3, requires: expert, cooldown: 30,
     cooldown_per_rank: -4, duration: 4, duration_per_rank: 1, distance: 2048}
  - {id: quickfoot, name: Quickfoot, tree: archery, kind: passive, max_rank: 3, per_rank: 3, per_rank_calm: 15}
  - {id: steady_aim, name: Steady Aim, tree: archery, kind: passive, max_rank: 3, per_rank: 10}
  - {id: arcane_ward, name: Arcane Ward, tree: arcana, kind: passive, max_rank: 5, per_rank: 6}
  - {id: spell_surge, name: Spell Surge, tree: arcana, kind: active, max_rank: 3, requires: master, cooldown: 45,
     per_rank: 50}
  - {id: overload, name: Overload, tree: arcana, kind: passive, max_rank: 3, requires: expert, per_rank: 10, targets: 3}
  - {id: bloodthirst, name: Bloodthirst, tree: any, kind: passive, max_rank: 5, per_rank: 2}
  - {id: conditioning, name: Conditioning, tree: any, kind: passive, max_rank: unlimited, first_rank: 10,
     per_rank: 1, text: "+{value} %"}
  - {id: spell_suppression, name: Spell Suppression, tree: any, kind: passive, max_rank: 41, first_rank: 4,
     per_rank: 0.4}
  - {id: manathirst, name: Manathirst, tree: any, kind: passive, max_rank: 5, per_rank: 2}
keystones:
  - {id: cheat_death, name: Cheat Death, cooldown: 180, duration: 2}
  - {id: unbroken, name: Unbroken}
)";

// Binds a table for one test and unbinds it after.
struct BoundTable
{
    SoloTalentTable table;
    BoundTable()
    {
        std::string error;
        REQUIRE_MESSAGE(table.loadFromYaml(TestTable, error), error);
        bindSoloTalentTable(&table);
    }
    ~BoundTable()
    {
        bindSoloTalentTable(nullptr);
    }
};

Character fighter(uint32_t level)
{
    Character character;
    character.level = level;
    character.might = 100;
    character.endurance = 50;
    character.speed = 40;
    character.intellect = 30;
    character.personality = 20;
    return character;
}
}

TEST_CASE("solo talents: the shipped table loads (tree v2 and the archetypes)")
{
    std::filesystem::path path = "assets_dev/engine/data_tables/talents.yml";
    for (int up = 0; up < 4 && !std::filesystem::exists(path); ++up)
    {
        path = std::filesystem::path("..") / path;
    }
    REQUIRE(std::filesystem::exists(path));
    std::ifstream file(path);
    std::stringstream text;
    text << file.rdbuf();
    SoloTalentTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadFromYaml(text.str(), error), error);
    // The archetypes of 2026-11-18: nine talents a path, the 19 old places kept (the action bar keeps talents by
    // place).
    CHECK(table.talents().size() == 32);
    for (const TalentTree path : {TalentTree::Arms, TalentTree::Archery, TalentTree::Arcana})
    {
        CHECK(std::count_if(table.talents().begin(), table.talents().end(),
                  [path](const TalentDefinition &talent) { return talent.tree == path; })
            == 9);
        CHECK(table.isPath(path));
    }
    CHECK_FALSE(table.isPath(TalentTree::Any));
    const std::vector<std::string> oldPlaces = {"cleave", "sweeping_blows", "onslaught", "charge", "challenge",
        "multishot", "piercing_arrows", "power_shot", "steady_aim", "quickfoot", "blink", "spell_surge", "arcane_ward",
        "overload", "binding_circle", "bloodthirst", "conditioning", "spell_suppression", "manathirst"};
    for (size_t place = 0; place < oldPlaces.size(); ++place)
    {
        CHECK(table.talents()[place].id == oldPlaces[place]);
    }
    CHECK(table.find("shield_wall") == nullptr);
    CHECK(table.find("resolve") == nullptr);
    // Onslaught: the Any tree, five ranks of 6 stacks.
    REQUIRE(table.find("onslaught") != nullptr);
    CHECK(table.find("onslaught")->tree == TalentTree::Any);
    CHECK(table.find("onslaught")->maxRank == 5);
    CHECK(talentValue(*table.find("onslaught"), 5) == doctest::Approx(30.0f));
    // Rage and its two abilities; the shared floor of the solo cuts.
    CHECK(table.rage().maximum == doctest::Approx(100.0f));
    CHECK(table.rage().limitPerSecond == doctest::Approx(20.0f));
    CHECK(table.damageFloor() == doctest::Approx(0.2));
    REQUIRE(table.find("heroic_strike") != nullptr);
    CHECK(table.find("heroic_strike")->rageCost == doctest::Approx(100.0f));
    CHECK(talentShareAtRank(*table.find("heroic_strike"), 1) == doctest::Approx(2.0f));
    CHECK(talentShareAtRank(*table.find("heroic_strike"), 3) == doctest::Approx(3.0f));
    REQUIRE(table.find("demoralizing_shout") != nullptr);
    CHECK(table.find("demoralizing_shout")->rageCost == doctest::Approx(100.0f));
    CHECK(talentDurationSeconds(*table.find("demoralizing_shout"), 3) == doctest::Approx(10.0f));
    CHECK(talentCooldownSeconds(*table.find("demoralizing_shout"), 3) == doctest::Approx(35.0f));
    REQUIRE(table.find("challenge") != nullptr);
    CHECK(talentDurationSeconds(*table.find("challenge"), 3) == doctest::Approx(6.0f));
    CHECK(talentCooldownSeconds(*table.find("challenge"), 3) == doctest::Approx(22.0f));
    // The user's numbers (2026-11-18).
    CHECK(talentValue(*table.find("vanguard"), 1) == doctest::Approx(20.0f));
    CHECK(talentValue(*table.find("vanguard"), 3) == doctest::Approx(60.0f));
    CHECK(table.find("vanguard")->distance == doctest::Approx(800.0f));
    // The pack talents count within 768, wider than MAW's 512 (user, 2026-11-18).
    CHECK(table.find("outnumbered")->distance == doctest::Approx(768.0f));
    CHECK(table.find("battle_frenzy")->distance == doctest::Approx(768.0f));
    CHECK(talentValue(*table.find("outnumbered"), 3) == doctest::Approx(4.0f));
    CHECK(talentValue(*table.find("battle_frenzy"), 2) == doctest::Approx(3.5f));
    CHECK(talentValue(*table.find("opening_volley"), 3) == doctest::Approx(45.0f));
    CHECK(talentValue(*table.find("breach"), 3) == doctest::Approx(15.0f));
    CHECK(talentValue(*table.find("phase"), 3) == doctest::Approx(50.0f));
    CHECK(talentValue(*table.find("arcane_ward"), 3) == doctest::Approx(30.0f));
    CHECK(table.find("long_shot")->distance == doctest::Approx(1536.0f));
    CHECK(table.find("long_shot")->fullDistance == doctest::Approx(5120.0f));
    CHECK(table.find("expose_weakness")->duration == doctest::Approx(5.0f));
    CHECK(table.find("hamstring")->duration == doctest::Approx(3.0f));
    CHECK(table.find("charge")->cooldownPerKill == doctest::Approx(3.0f));
    CHECK(talentCooldownSeconds(*table.find("spell_surge"), 3) == doctest::Approx(12.0f));
    CHECK(table.find("spell_surge")->cooldownPerCast == doctest::Approx(1.0f));
    CHECK(table.levelsPerPoint() == 5);
    CHECK(table.keystones().size() == 2);
    CHECK(table.keystoneLevels() == std::vector<uint32_t>{150, 300});
    REQUIRE(table.find("cleave") != nullptr);
    CHECK(table.find("cleave")->share == doctest::Approx(150));
    REQUIRE(table.find("multishot") != nullptr);
    CHECK(table.find("multishot")->cooldownPerHit == doctest::Approx(1.0f));
    CHECK(table.find("multishot")->cooldownPerAttack == doctest::Approx(0.0f));
    REQUIRE(table.find("sweeping_blows") != nullptr);
    CHECK(table.find("sweeping_blows")->needs == "cleave");
    CHECK(table.find("whirlwind") == nullptr);
    CHECK(table.find("purify") == nullptr);
    CHECK(table.findKeystone("cheat_death") != nullptr);
    CHECK(table.findKeystone("unbroken") != nullptr);
    // Power Shot replaced Pinning Shot (2026-11-16), in its place in the table: the action bar keeps talents by index.
    CHECK(table.find("pinning_shot") == nullptr);
    const TalentDefinition *pPowerShot = table.find("power_shot");
    REQUIRE(pPowerShot != nullptr);
    REQUIRE(table.find("piercing_arrows") != nullptr);
    CHECK(pPowerShot == table.find("piercing_arrows") + 1);
    CHECK(pPowerShot->kind == TalentKind::Active);
    CHECK(talentShareAtRank(*pPowerShot, 1) == doctest::Approx(1.35f));
    CHECK(talentShareAtRank(*pPowerShot, 2) == doctest::Approx(1.70f));
    CHECK(talentShareAtRank(*pPowerShot, 3) == doctest::Approx(2.00f));
    CHECK(talentCooldownSeconds(*pPowerShot, 1) == doctest::Approx(6.0f));
    CHECK(talentCooldownSeconds(*pPowerShot, 2) == doctest::Approx(5.0f));
    CHECK(talentCooldownSeconds(*pPowerShot, 3) == doctest::Approx(4.0f));
    CHECK(talentValue(*pPowerShot, 2) == doctest::Approx(170.0f));
    // A critical hit of an ordinary attack takes 0.5 s off Power Shot's cooldown (2026-11-16).
    CHECK(pPowerShot->cooldownPerCritical == doctest::Approx(0.5f));
    // Conditioning replaced Weapon Training, Marksman and Attunement (2026-11-16); Bloodthirst has five ranks of 2 %,
    // Steady Aim 10 % a rank.
    CHECK(table.find("weapon_training") == nullptr);
    CHECK(table.find("marksman") == nullptr);
    CHECK(table.find("attunement") == nullptr);
    const TalentDefinition *pConditioning = table.find("conditioning");
    REQUIRE(pConditioning != nullptr);
    CHECK(pConditioning->tree == TalentTree::Any);
    CHECK(pConditioning->unlimitedRanks);
    CHECK(talentValue(*pConditioning, 40) == doctest::Approx(49.0f));
    REQUIRE(table.find("bloodthirst") != nullptr);
    CHECK(table.find("bloodthirst")->maxRank == 5);
    CHECK(talentValue(*table.find("bloodthirst"), 5) == doctest::Approx(10.0f));
    REQUIRE(table.find("steady_aim") != nullptr);
    CHECK(talentValue(*table.find("steady_aim"), 3) == doctest::Approx(30.0f));
    // Spell Suppression: 4 % at rank 1, 0.4 % a rank after, 20 % at its last rank 41. Conditioning: 10 % at rank 1,
    // 1 % a rank after. Manathirst, the newest, is last in the table so the action bar's indexes keep.
    const TalentDefinition *pSuppression = table.find("spell_suppression");
    REQUIRE(pSuppression != nullptr);
    CHECK(pSuppression->tree == TalentTree::Any);
    CHECK(pSuppression->maxRank == 41);
    CHECK(talentValue(*pSuppression, 1) == doctest::Approx(4.0f));
    CHECK(talentValue(*pSuppression, 2) == doctest::Approx(4.4f));
    CHECK(talentValue(*pSuppression, 41) == doctest::Approx(20.0f));
    CHECK(talentValue(*pConditioning, 1) == doctest::Approx(10.0f));
    CHECK(table.talents()[18].id == "manathirst");
    CHECK(table.talents()[18].maxRank == 5);
    CHECK(talentValue(table.talents()[18], 5) == doctest::Approx(10.0f));
    CHECK(table.talents().back().id == "phase");
}

TEST_CASE("solo talents: an unlimited talent takes every point the character has")
{
    BoundTable bound;
    const TalentDefinition &conditioning = *bound.table.find("conditioning");
    CHECK(conditioning.unlimitedRanks);
    // Level 1500 at one point per 15 levels: 100 points, all of them into Conditioning.
    Character character = fighter(1500);
    for (int point = 0; point < 100; ++point)
    {
        REQUIRE(learnTalent(bound.table, character, "conditioning"));
    }
    CHECK(talentRank(character, "conditioning") == 100);
    CHECK_FALSE(learnTalent(bound.table, character, "conditioning"));
    // Past 255: ranks are two bytes.
    character.level = 15 * 400;
    for (int point = 0; point < 300; ++point)
    {
        REQUIRE(learnTalent(bound.table, character, "conditioning"));
    }
    CHECK(talentRank(character, "conditioning") == 400);
    // A bounded talent still stops at its last rank.
    SoloTalentTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadFromYaml("talents:\n  - {id: a, name: A, tree: any, max_rank: 60}\n", error), error);
    CHECK(table.find("a")->maxRank == 50);
    CHECK_FALSE(table.find("a")->unlimitedRanks);
}

TEST_CASE("solo talents: share_by_rank needs one share per rank")
{
    SoloTalentTable table;
    std::string error;
    CHECK_FALSE(table.loadFromYaml(R"(
talents:
  - {id: power_shot, name: Power Shot, tree: archery, kind: active, max_rank: 3, share_by_rank: [135, 170]}
)",
        error));
    CHECK(error.find("share_by_rank") != std::string::npos);
}

TEST_CASE("solo run: the early monster cut is read from the table, fades between its points and follows earned levels")
{
    std::filesystem::path path = "assets_dev/engine/data_tables/talents.yml";
    for (int up = 0; up < 4 && !std::filesystem::exists(path); ++up)
    {
        path = std::filesystem::path("..") / path;
    }
    REQUIRE(std::filesystem::exists(path));
    std::ifstream file(path);
    std::stringstream text;
    text << file.rdbuf();
    SoloTalentTable shipped;
    std::string error;
    REQUIRE_MESSAGE(shipped.loadFromYaml(text.str(), error), error);
    // The shipped cut: 2.5 at the start, linear between the points, over from level 75.
    CHECK(shipped.earlyMonsterCut(1) == doctest::Approx(2.5));
    CHECK(shipped.earlyMonsterCut(5) == doctest::Approx(2.0));
    CHECK(shipped.earlyMonsterCut(10) == doctest::Approx(1.6));
    CHECK(shipped.earlyMonsterCut(30) == doctest::Approx(1.5));
    CHECK(shipped.earlyMonsterCut(50) == doctest::Approx(1.4));
    CHECK(shipped.earlyMonsterCut(60) == doctest::Approx(1.24));
    CHECK(shipped.earlyMonsterCut(75) == doctest::Approx(1.0));
    CHECK(shipped.earlyMonsterCut(500) == doctest::Approx(1.0));
    // The shipped early Regeneration: half until level 15, the whole from 75, an S-curve between.
    CHECK(shipped.earlyRegeneration(1) == doctest::Approx(0.5));
    CHECK(shipped.earlyRegeneration(15) == doctest::Approx(0.5));
    CHECK(shipped.earlyRegeneration(30) == doctest::Approx(0.585));
    CHECK(shipped.earlyRegeneration(45) == doctest::Approx(0.75));
    CHECK(shipped.earlyRegeneration(60) == doctest::Approx(0.915));
    CHECK(shipped.earlyRegeneration(75) == doctest::Approx(1.0));
    CHECK(shipped.earlyRegeneration(500) == doctest::Approx(1.0));
    // The shipped experience surcharge, half of MAW's.
    REQUIRE(shipped.experienceSurcharge().has_value());
    CHECK(*shipped.experienceSurcharge() == doctest::Approx(0.0025));

    // No list, no cut; a divisor below 1 is refused; past a list that ends above 1 the cut is over all the same.
    SoloTalentTable none;
    REQUIRE(none.loadFromYaml("talents: []", error));
    CHECK(none.earlyMonsterCut(1) == doctest::Approx(1.0));
    CHECK(none.earlyRegeneration(1) == doctest::Approx(1.0));
    CHECK_FALSE(none.experienceSurcharge().has_value());
    SoloTalentTable bad;
    CHECK_FALSE(bad.loadFromYaml("early_monster_cut: [[1, 0.5]]\ntalents: []", error));
    CHECK_FALSE(bad.loadFromYaml("early_regeneration: [[1, 1.5]]\ntalents: []", error));
    CHECK_FALSE(bad.loadFromYaml("early_regeneration: [[1, 0]]\ntalents: []", error));
    SoloTalentTable shortList;
    REQUIRE(shortList.loadFromYaml("early_monster_cut: [[1, 3], [20, 2]]\ntalents: []", error));
    CHECK(shortList.earlyMonsterCut(20) == doctest::Approx(2.0));
    CHECK(shortList.earlyMonsterCut(21) == doctest::Approx(1.0));

    // The character's cut goes by the level its experience has earned, trained or not.
    bindSoloTalentTable(&shipped);
    Character member = fighter(5);
    member.experience = 0;
    CHECK(MawSoloTalents::earlyMonsterCut(member) == doctest::Approx(2.0));
    // 190,000 experience is level 20 on MAW's curve (500 x 20 x 19).
    member.experience = 190000;
    CHECK(MawSoloTalents::earlyMonsterCut(member) == doctest::Approx(1.55));
    member.level = 100;
    CHECK(MawSoloTalents::earlyMonsterCut(member) == doctest::Approx(1.0));
    bindSoloTalentTable(nullptr);
}

TEST_CASE("solo run: the Regeneration skill of a class without it heals less at low character levels, the whole "
          "again later")
{
    SoloTalentTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadFromYaml("early_regeneration: [[15, 0.5], [75, 1.0]]\ntalents: []", error), error);
    bindSoloTalentTable(&table);
    // A Knight has Regeneration only by Lone Discipline; a Troll learns it in MAW.
    ClassSkillTable classes;
    REQUIRE(classes.loadCapsFromRows({{"", "Knight", "Troll"}, {"Regeneration", "-", "M"}}));
    // The hit points 30 seconds of Expert Regeneration give a wounded character of 50,000.
    const auto healed = [&classes](bool soloRun, uint32_t level, const char *pClassName = "Knight")
    {
        RulesetOptions options;
        options.soloRun = soloRun;
        MawRules rules(options, MawMapLevels{});
        PartySeed seed;
        seed.members.resize(1);
        seed.members[0].className = pClassName;
        seed.members[0].level = level;
        seed.members[0].skills["Regeneration"] = {"Regeneration", 10, SkillMastery::Expert};
        Party party;
        party.seed(seed);
        party.setClassSkillTable(&classes);
        party.setRules(&rules.gameRules());
        Character &member = *party.member(0);
        member.maxHealth = 50000;
        member.health = 100;
        OpenYAMM::Tests::PartySpellTestWorldRuntime world;

        for (int tick = 0; tick < 300; ++tick)
        {
            rules.gameRules().skills.updateRegeneration(party, world, 0.1f);
        }

        return member.health - 100;
    };
    const int whole = healed(false, 10);
    REQUIRE_GT(whole, 1000);
    // Half until level 15, three quarters half way to 75, the whole from there; a party's Regeneration is untouched.
    CHECK(healed(true, 10) == doctest::Approx(whole * 0.5).epsilon(0.01));
    CHECK(healed(true, 15) == doctest::Approx(whole * 0.5).epsilon(0.01));
    CHECK(healed(true, 45) == doctest::Approx(whole * 0.75).epsilon(0.01));
    CHECK(healed(true, 75) == doctest::Approx(whole).epsilon(0.01));
    CHECK(healed(false, 45) == doctest::Approx(whole).epsilon(0.01));
    // A class with Regeneration of its own keeps the whole at every level.
    CHECK(healed(true, 10, "Troll") == doctest::Approx(whole).epsilon(0.01));
    CHECK(healed(true, 45, "Troll") == doctest::Approx(whole).epsilon(0.01));
    bindSoloTalentTable(nullptr);
}

TEST_CASE("solo talents: one point every fifteen levels; keystones and removed talents cost nothing")
{
    BoundTable bound;
    Character character = fighter(14);
    CHECK(talentPointsTotal(bound.table, character) == 0);
    CHECK(nextTalentPointLevel(bound.table, character) == 15);
    character.level = 47;
    CHECK(talentPointsTotal(bound.table, character) == 3);
    CHECK(nextTalentPointLevel(bound.table, character) == 60);
    character.talentRanks["arcane_ward"] = 2;
    character.talentRanks["unbroken"] = 1;
    // A talent the table no longer has (an older save's Whirlwind) gives its points back.
    character.talentRanks["whirlwind"] = 3;
    CHECK(talentPointsSpent(bound.table, character) == 2);
    CHECK(talentPointsAvailable(bound.table, character) == 1);
}

TEST_CASE("solo talents: an ordinary attack takes cooldown_per_attack off, its hit cooldown_per_hit")
{
    SoloTalentTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadFromYaml(R"(
talents:
  - {id: charge, name: Charge, tree: arms, kind: active, max_rank: 3, cooldown: 25, cooldown_per_attack: 1}
  - {id: multishot, name: Multishot, tree: archery, kind: active, max_rank: 3, cooldown: 10, cooldown_per_hit: 1}
  - {id: cleave, name: Cleave, tree: arms, kind: active, max_rank: 3, cooldown: 12}
)", error), error);
    Character character = fighter(50);
    character.talentState.cooldownSeconds = {{"charge", 10.0f}, {"multishot", 0.5f}, {"cleave", 6.0f}};
    shortenTalentCooldowns(table, character, false);
    CHECK(character.talentState.cooldownSeconds["charge"] == doctest::Approx(9.0f));
    CHECK(character.talentState.cooldownSeconds["multishot"] == doctest::Approx(0.5f));
    shortenTalentCooldowns(table, character, true);
    CHECK(character.talentState.cooldownSeconds["charge"] == doctest::Approx(9.0f));
    CHECK(character.talentState.cooldownSeconds["multishot"] == doctest::Approx(0.0f));
    CHECK(character.talentState.cooldownSeconds["cleave"] == doctest::Approx(6.0f));
    // A cooldown not running is not started.
    Character fresh = fighter(50);
    shortenTalentCooldowns(table, fresh, true);
    CHECK(fresh.talentState.cooldownSeconds.empty());
}

TEST_CASE("solo talents: a critical hit takes cooldown_per_crit off, once for each")
{
    SoloTalentTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadFromYaml(R"(
talents:
  - {id: power_shot, name: Power Shot, tree: archery, kind: active, max_rank: 3, cooldown: 6, cooldown_per_crit: 0.5}
  - {id: multishot, name: Multishot, tree: archery, kind: active, max_rank: 3, cooldown: 10, cooldown_per_hit: 1}
)", error), error);
    Character character = fighter(50);
    character.talentState.cooldownSeconds = {{"power_shot", 4.0f}, {"multishot", 5.0f}};
    // Two critical arrows of one shot: a second each.
    shortenTalentCooldownsOnCritical(table, character);
    shortenTalentCooldownsOnCritical(table, character);
    CHECK(character.talentState.cooldownSeconds["power_shot"] == doctest::Approx(3.0f));
    CHECK(character.talentState.cooldownSeconds["multishot"] == doctest::Approx(5.0f));
    // A hit without a critical leaves Power Shot alone.
    shortenTalentCooldowns(table, character, true);
    CHECK(character.talentState.cooldownSeconds["power_shot"] == doctest::Approx(3.0f));
    character.talentState.cooldownSeconds["power_shot"] = 0.2f;
    shortenTalentCooldownsOnCritical(table, character);
    CHECK(character.talentState.cooldownSeconds["power_shot"] == doctest::Approx(0.0f));
    // Not running: not started.
    Character fresh = fighter(50);
    shortenTalentCooldownsOnCritical(table, fresh);
    CHECK(fresh.talentState.cooldownSeconds.empty());
}

TEST_CASE("solo talents: mastery locks and talents that need another first")
{
    BoundTable bound;
    Character character = fighter(200);
    const TalentDefinition &training = *bound.table.find("arcane_ward");
    const TalentDefinition &cleave = *bound.table.find("cleave");
    const TalentDefinition &sweeping = *bound.table.find("sweeping_blows");
    const TalentDefinition &bloodthirst = *bound.table.find("bloodthirst");
    CHECK(talentLearnRefusal(bound.table, character, training).empty());
    CHECK(talentLearnRefusal(bound.table, character, bloodthirst).empty());
    CHECK_FALSE(talentLearnRefusal(bound.table, character, cleave).empty());

    character.skills["Axe"] = {"Axe", 7, SkillMastery::Expert};
    CHECK(talentLearnRefusal(bound.table, character, cleave).empty());
    // Sweeping Blows needs Cleave first.
    CHECK_FALSE(talentLearnRefusal(bound.table, character, sweeping).empty());
    REQUIRE(learnTalent(bound.table, character, "cleave"));
    CHECK(talentLearnRefusal(bound.table, character, sweeping).empty());

    // No points left, and the last rank.
    Character spent = fighter(15);
    spent.talentRanks["arcane_ward"] = 1;
    CHECK_FALSE(talentLearnRefusal(bound.table, spent, training).empty());
    Character full = fighter(200);
    full.talentRanks["arcane_ward"] = 5;
    CHECK_FALSE(talentLearnRefusal(bound.table, full, training).empty());
}

TEST_CASE("solo talents: learning an active puts it on the bar; a reset forgets ranks and keystones")
{
    BoundTable bound;
    Character character = fighter(200);
    character.skills["Sword"] = {"Sword", 7, SkillMastery::Expert};
    character.actionBar[0] = {ActionBarSlotKind::Weapon, 0, {}};
    REQUIRE(learnTalent(bound.table, character, "cleave"));
    CHECK(talentRank(character, "cleave") == 1);
    const uint32_t cleaveIndex = uint32_t(bound.table.find("cleave") - bound.table.talents().data());
    CHECK(character.actionBar[1].kind == ActionBarSlotKind::Talent);
    CHECK(character.actionBar[1].id == cleaveIndex);
    REQUIRE(learnTalent(bound.table, character, "cleave"));
    CHECK(character.actionBar[2].kind == ActionBarSlotKind::Empty);
    REQUIRE(bindKeystone(bound.table, character, "unbroken"));

    character.talentState.cooldownSeconds["cleave"] = 5;
    resetTalents(character);
    CHECK(character.talentRanks.empty());
    CHECK_FALSE(hasKeystone(character, "unbroken"));
    CHECK(character.actionBar[1].kind == ActionBarSlotKind::Empty);
    CHECK(character.actionBar[0].kind == ActionBarSlotKind::Weapon);
    CHECK(character.talentState.cooldownSeconds.empty());
}

TEST_CASE("solo talents: a keystone slot opens every 150 levels")
{
    BoundTable bound;
    Character character = fighter(149);
    CHECK(keystoneSlots(bound.table, character) == 0);
    CHECK(nextKeystoneLevel(bound.table, character) == 150);
    CHECK_FALSE(bindKeystone(bound.table, character, "unbroken"));
    character.level = 150;
    CHECK(keystoneSlots(bound.table, character) == 1);
    REQUIRE(bindKeystone(bound.table, character, "unbroken"));
    CHECK(hasKeystone(character, "unbroken"));
    // The one slot is taken; a keystone is bound once.
    CHECK_FALSE(bindKeystone(bound.table, character, "cheat_death"));
    CHECK_FALSE(bindKeystone(bound.table, character, "unbroken"));
    character.level = 300;
    CHECK(nextKeystoneLevel(bound.table, character) == 0);
    REQUIRE(bindKeystone(bound.table, character, "cheat_death"));
    CHECK(keystonesBound(bound.table, character) == 2);
    // Keystones cost no points.
    CHECK(talentPointsSpent(bound.table, character) == 0);
}

TEST_CASE("solo talents: a save keeps the learned ranks and keystones")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.ruleset.id = "maw";
    save.ruleset.options.soloRun = true;
    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    party.member(0)->talentRanks["cleave"] = 2;
    party.member(0)->talentRanks["conditioning"] = 300;
    party.member(0)->talentRanks["cheat_death"] = 1;
    save.party = party.snapshot();

    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_solo_talents_" + std::to_string(ticks) + ".oysav");
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    REQUIRE_FALSE(loaded->party.members.empty());
    CHECK(loaded->party.members[0].talentRanks.at("cleave") == 2);
    CHECK(loaded->party.members[0].talentRanks.at("conditioning") == 300);
    CHECK(loaded->party.members[0].talentRanks.at("cheat_death") == 1);
}

TEST_CASE("solo talents: passives add their share of the whole stats")
{
    BoundTable bound;
    Character character = fighter(60);
    character.accuracy = 60;
    character.luck = 80;
    character.talentRanks["conditioning"] = 1;
    MawSoloTalents::applyStatPassives(character);
    // Conditioning's first rank: 10 % of each of the seven stats.
    CHECK(character.magicalBonuses.might == 10);
    CHECK(character.magicalBonuses.intellect == 3);
    CHECK(character.magicalBonuses.personality == 2);
    CHECK(character.magicalBonuses.endurance == 5);
    CHECK(character.magicalBonuses.accuracy == 6);
    CHECK(character.magicalBonuses.speed == 4);
    CHECK(character.magicalBonuses.luck == 8);
    // Rank 11: 10 % and ten ranks of 1 %, 20 %.
    Character eleven = fighter(60);
    eleven.talentRanks["conditioning"] = 11;
    MawSoloTalents::applyStatPassives(eleven);
    CHECK(eleven.magicalBonuses.might == 20);
    // The percent reads the whole stat: 100 base, 300 from potions, 500 from items and buffs; the 20 % is 180.
    Character geared = fighter(60);
    geared.talentRanks["conditioning"] = 11;
    geared.permanentBonuses.might = 300;
    geared.magicalBonuses.might = 500;
    geared.magicalBonuses.speed = -100;
    MawSoloTalents::applyStatPassives(geared);
    CHECK(geared.magicalBonuses.might == 680);
    // A stat below zero gives nothing.
    CHECK(geared.magicalBonuses.speed == -100);
    // Spells take no passive's share.
    CHECK(MawSoloTalents::spellDamageBonus(character, true, 4, false) == doctest::Approx(0.0));

    // Steady Aim while still adds its Luck to Conditioning's: 40 % of the same 280, not of each other's share.
    Character still = fighter(60);
    still.luck = 80;
    still.magicalBonuses.luck = 200;
    still.talentRanks["conditioning"] = 1;
    still.talentRanks["steady_aim"] = 3;
    still.talentState.steadyAimOn = true;
    MawSoloTalents::applyStatPassives(still);
    CHECK(still.magicalBonuses.luck == 312);
}

TEST_CASE("solo talents: MAW adds the stat passives before HP and SP, only in a solo run")
{
    BoundTable bound;
    RulesetOptions options;
    options.soloRun = true;
    MawRules solo(options, MawMapLevels{});
    Character member = fighter(60);
    member.talentRanks["conditioning"] = 11;
    solo.classRules().applyPrimaryStatBonuses(member);
    CHECK(member.magicalBonuses.endurance == 10);
    // The class bonuses that follow do not add the share again.
    solo.classRules().applyClassBonuses(member);
    CHECK(member.magicalBonuses.endurance == 10);

    Character other = fighter(60);
    other.talentRanks["conditioning"] = 11;
    MawRules party(RulesetOptions{}, MawMapLevels{});
    party.classRules().applyPrimaryStatBonuses(other);
    CHECK(other.magicalBonuses.endurance == 0);
}

TEST_CASE("solo talents: Onslaught stacks on kills, up to six per rank, and runs out")
{
    BoundTable bound;
    Character character = fighter(60);
    CHECK(MawSoloTalents::attackRecoveryScale(character) == doctest::Approx(1.0));
    MawSoloTalents::noteKill(character);
    CHECK(character.talentState.onslaughtStacks == 0);

    character.talentRanks["onslaught"] = 1;
    for (int kill = 0; kill < 14; ++kill)
    {
        MawSoloTalents::noteKill(character);
    }
    CHECK(character.talentState.onslaughtStacks == 6);
    CHECK(character.talentState.onslaughtSeconds == doctest::Approx(30));
    CHECK(MawSoloTalents::attackRecoveryScale(character) == doctest::Approx(1.0 / 1.06));
    character.talentRanks["onslaught"] = 5;
    for (int kill = 0; kill < 40; ++kill)
    {
        MawSoloTalents::noteKill(character);
    }
    CHECK(character.talentState.onslaughtStacks == 30);

    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    member.talentRanks["onslaught"] = 3;
    MawSoloTalents::noteKill(member);
    MawSoloTalents::update(party, 0, 0, true, 31);
    CHECK(member.talentState.onslaughtStacks == 0);
    CHECK(MawSoloTalents::attackRecoveryScale(member) == doctest::Approx(1.0));
}

TEST_CASE("solo talents: Unbroken and Cheat Death")
{
    BoundTable bound;
    Character character = fighter(300);
    character.talentRanks["conditioning"] = 1;
    CHECK(MawSoloTalents::absorbDamage(character, 100, 1000) == 100);

    // Unbroken: the part above 30 % of 1000 HP is halved.
    CHECK(MawSoloTalents::absorbDamage(character, 500, 1000) == 500);
    character.talentRanks["unbroken"] = 1;
    CHECK(MawSoloTalents::absorbDamage(character, 200, 1000) == 200);
    CHECK(MawSoloTalents::absorbDamage(character, 500, 1000) == 400);

    // Cheat Death: a fatal blow leaves 5 % HP, then 2 s of 95 % less damage, and a 3-minute cooldown.
    CHECK(MawSoloTalents::cheatDeath(character, 800, 600, 1000) == 800);
    character.talentRanks["cheat_death"] = 1;
    CHECK(MawSoloTalents::cheatDeath(character, 400, 600, 1000) == 400);
    CHECK(MawSoloTalents::cheatDeath(character, 800, 600, 1000) == 550);
    CHECK(character.talentState.cheatDeathSeconds == doctest::Approx(2));
    CHECK(character.talentState.cheatDeathCooldown == doctest::Approx(180));
    CHECK(MawSoloTalents::absorbDamage(character, 200, 1000) == 10);
    // On cooldown it does not save again.
    CHECK(MawSoloTalents::cheatDeath(character, 800, 50, 1000) == 800);
}

TEST_CASE("solo talents: Spell Suppression is the last cut of a hit that is not physical")
{
    BoundTable bound;
    RulesetOptions options;
    options.soloRun = true;
    MawRules rules(options, MawMapLevels{});
    Character member = fighter(300);
    member.maxHealth = 50000;
    member.health = 50000;
    const auto run = [&](CombatDamageType type, std::vector<DamageStageRecord> &records)
    {
        CharacterDamageHit hit;
        hit.amount = 20000;
        hit.type = type;
        hit.pCharacter = &member;
        hit.monsterAttack = true;
        hit.attackerLevel = 300;
        hit.attackerFacts.level = 300;
        hit.attackerFacts.familyLevel = 300;
        hit.attackerFacts.tier = 2;
        hit.attackerFacts.attack1Damage = 20000;
        std::mt19937 rng(9);
        hit.pRng = &rng;
        records.clear();
        return rules.gameRules().combat.damageToCharacterStages().run(hit, &records);
    };
    std::vector<DamageStageRecord> records;
    const int plainFire = run(CombatDamageType::Fire, records);
    const int plainPhysical = run(CombatDamageType::Physical, records);
    REQUIRE(plainFire > 100);
    REQUIRE(plainPhysical > 100);

    member.talentRanks["spell_suppression"] = 41;
    CHECK(MawSoloTalents::incomingDamageScale(member, {.physical = false}) == doctest::Approx(0.8));
    CHECK(MawSoloTalents::incomingDamageScale(member, {.physical = true}) == doctest::Approx(1.0));
    const int suppressed = run(CombatDamageType::Fire, records);
    // The last stage, after the mitigation and its floor: what the hit would have been, less 20 %.
    REQUIRE_FALSE(records.empty());
    CHECK(records.back().stage == "solo-talent-cuts");
    CHECK(records.back().before == plainFire);
    CHECK(suppressed == doctest::Approx(plainFire * 0.8).epsilon(0.001));
    // A physical hit keeps all of it.
    CHECK(run(CombatDamageType::Physical, records) == plainPhysical);

    // Outside a solo run the ranks do nothing.
    MawRules party(RulesetOptions{}, MawMapLevels{});
    std::vector<DamageStageRecord> partyRecords;
    CharacterDamageHit hit;
    hit.amount = 20000;
    hit.type = CombatDamageType::Fire;
    hit.pCharacter = &member;
    hit.monsterAttack = true;
    hit.attackerLevel = 300;
    hit.attackerFacts.level = 300;
    hit.attackerFacts.familyLevel = 300;
    hit.attackerFacts.tier = 2;
    hit.attackerFacts.attack1Damage = 20000;
    std::mt19937 rng(9);
    hit.pRng = &rng;
    const int partyTaken = party.gameRules().combat.damageToCharacterStages().run(hit, &partyRecords);
    CHECK(partyRecords.back().before == partyTaken);
}

TEST_CASE("solo talents: Spell Surge, Overload and Bloodthirst")
{
    BoundTable bound;
    Character character = fighter(60);
    character.talentState.spellSurgeArmed = true;
    CHECK(MawSoloTalents::nextSpellFree(character));
    CHECK(MawSoloTalents::spellDamageBonus(character, false, 0, false) == doctest::Approx(0.5));
    MawSoloTalents::spendSurge(character);
    CHECK_FALSE(MawSoloTalents::nextSpellFree(character));
    // The surging spell's damage is rolled where it lands, within the window the cast opened.
    CHECK(MawSoloTalents::spellDamageBonus(character, false, 0, false) == doctest::Approx(0.5));
    character.talentState.surgeDamageSeconds = 0;

    // Overload: an area spell's blast, for the monsters it struck beyond the first, at most three more.
    CHECK(MawSoloTalents::spellDamageBonus(character, true, 4, false) == doctest::Approx(0.0));
    character.talentRanks["overload"] = 2;
    CHECK(MawSoloTalents::spellDamageBonus(character, true, 1, false) == doctest::Approx(0.0));
    CHECK(MawSoloTalents::spellDamageBonus(character, true, 3, false) == doctest::Approx(0.4));
    CHECK(MawSoloTalents::spellDamageBonus(character, true, 9, false) == doctest::Approx(0.6));
    CHECK(MawSoloTalents::spellDamageBonus(character, false, 9, false) == doctest::Approx(0.0));

    CHECK(MawSoloTalents::leechBonus(character) == doctest::Approx(0.0));
    CHECK(MawSoloTalents::leechFloorDivisor(character) == doctest::Approx(5.0));
    character.talentRanks["bloodthirst"] = 2;
    CHECK(MawSoloTalents::leechBonus(character) == doctest::Approx(0.04));
    CHECK(MawSoloTalents::leechFloorDivisor(character) == doctest::Approx(4.0));
    character.talentRanks["bloodthirst"] = 5;
    CHECK(MawSoloTalents::leechBonus(character) == doctest::Approx(0.10));
    CHECK(MawSoloTalents::leechFloorDivisor(character) == doctest::Approx(2.5));

    // Manathirst: the same shape for the SP bar.
    CHECK(MawSoloTalents::manaLeechShare(character) == doctest::Approx(0.0));
    CHECK(MawSoloTalents::manaLeechFloorDivisor(character) == doctest::Approx(5.0));
    character.talentRanks["manathirst"] = 1;
    CHECK(MawSoloTalents::manaLeechShare(character) == doctest::Approx(0.02));
    CHECK(MawSoloTalents::manaLeechFloorDivisor(character) == doctest::Approx(4.5));
    character.talentRanks["manathirst"] = 5;
    CHECK(MawSoloTalents::manaLeechShare(character) == doctest::Approx(0.10));
    CHECK(MawSoloTalents::manaLeechFloorDivisor(character) == doctest::Approx(2.5));
}

TEST_CASE("solo talents: Sweeping Blows' share grows with the weapon skill up to its cap")
{
    BoundTable bound;
    const TalentDefinition &sweeping = *bound.table.find("sweeping_blows");
    Character character = fighter(200);
    character.skills["Axe"] = {"Axe", 40, SkillMastery::Master};
    CHECK(talentSkillShare(sweeping, character) == doctest::Approx(0.40));
    character.skills["Axe"].level = 120;
    CHECK(talentSkillShare(sweeping, character) == doctest::Approx(0.50));
}

TEST_CASE("solo talents: cooldowns run down in the update; Quickfoot speeds the party, more out of combat")
{
    BoundTable bound;
    const TalentDefinition &cleave = *bound.table.find("cleave");
    CHECK(talentCooldownSeconds(cleave, 1) == doctest::Approx(12));
    CHECK(talentCooldownSeconds(cleave, 3) == doctest::Approx(8));

    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    member.talentRanks["cleave"] = 1;
    member.talentState.cooldownSeconds["cleave"] = 5;
    MawSoloTalents::update(party, 0, 0, false, 2);
    CHECK(member.talentState.cooldownSeconds["cleave"] == doctest::Approx(3));
    CHECK(party.movementMultiplier() == doctest::Approx(1.0));

    member.talentRanks["quickfoot"] = 2;
    MawSoloTalents::update(party, 0, 0, false, 0.25f);
    CHECK(party.movementMultiplier() == doctest::Approx(1.06));
    MawSoloTalents::update(party, 0, 0, true, 0.25f);
    CHECK(party.movementMultiplier() == doctest::Approx(1.30));
}

TEST_CASE("solo talents: sweeps pick living hostiles in reach and in the arc, nearest first")
{
    std::vector<TalentTargetCandidate> candidates = {
        {1, 300, 0, 0, 40, true},   // ahead, in reach
        {2, 200, 100, 0, 40, true}, // ahead-left, nearer
        {3, -300, 0, 0, 40, true},  // behind
        {4, 0, 900, 0, 40, true},   // out of reach
        {5, 250, -50, 0, 40, false}, // dead or friendly
        {6, 0, 300, 0, 40, true},   // to the side (90 degrees)
    };
    // Facing +x, a 60-degree arc either side.
    const std::vector<size_t> cleave = pickTalentTargets(candidates, 0, 0, 0, 0.0f, 407.2f, 60.0f, 5);
    REQUIRE(cleave.size() == 2);
    CHECK(cleave[0] == 2);
    CHECK(cleave[1] == 1);
    // All around (Binding Circle): everything living in reach.
    const std::vector<size_t> around = pickTalentTargets(candidates, 0, 0, 0, 0.0f, 407.2f, 180.0f, 64);
    CHECK(around.size() == 4);
    // The count caps it.
    CHECK(pickTalentTargets(candidates, 0, 0, 0, 0.0f, 407.2f, 180.0f, 2).size() == 2);
}

namespace
{
// The shipped table, bound for one test.
struct ShippedTable
{
    SoloTalentTable table;
    ShippedTable()
    {
        std::filesystem::path path = "assets_dev/engine/data_tables/talents.yml";
        for (int up = 0; up < 4 && !std::filesystem::exists(path); ++up)
        {
            path = std::filesystem::path("..") / path;
        }
        std::ifstream file(path);
        std::stringstream text;
        text << file.rdbuf();
        std::string error;
        REQUIRE_MESSAGE(table.loadFromYaml(text.str(), error), error);
        bindSoloTalentTable(&table);
    }
    ~ShippedTable()
    {
        bindSoloTalentTable(nullptr);
    }
};
}

TEST_CASE("solo archetypes: the first rank in a path closes the other two until a reset")
{
    ShippedTable shipped;
    const SoloTalentTable &table = shipped.table;
    Character character = fighter(500);
    character.skills["Axe"] = {"Axe", 10, SkillMastery::Master};
    character.skills["Bow"] = {"Bow", 10, SkillMastery::Master};
    character.skills["FireMagic"] = {"FireMagic", 10, SkillMastery::Master};
    CHECK_FALSE(talentPath(table, character));
    CHECK(talentLearnRefusal(table, character, *table.find("multishot")).empty());
    CHECK(talentLearnRefusal(table, character, *table.find("blink")).empty());

    // The Any tree never chooses a path.
    REQUIRE(learnTalent(table, character, "onslaught"));
    REQUIRE(learnTalent(table, character, "conditioning"));
    CHECK_FALSE(talentPath(table, character));
    CHECK_FALSE(hasRageBar(table, character));

    REQUIRE(learnTalent(table, character, "cleave"));
    CHECK(talentPath(table, character) == TalentTree::Arms);
    CHECK(hasRageBar(table, character));
    CHECK_FALSE(talentLearnRefusal(table, character, *table.find("multishot")).empty());
    CHECK_FALSE(talentLearnRefusal(table, character, *table.find("blink")).empty());
    CHECK_FALSE(learnTalent(table, character, "nimble"));
    CHECK(talentLearnRefusal(table, character, *table.find("vanguard")).empty());
    CHECK(talentLearnRefusal(table, character, *table.find("bloodthirst")).empty());

    // A reset is free and frees the choice.
    resetTalents(character);
    CHECK_FALSE(talentPath(table, character));
    REQUIRE(learnTalent(table, character, "multishot"));
    CHECK(talentPath(table, character) == TalentTree::Archery);
    CHECK_FALSE(hasRageBar(table, character));
    CHECK_FALSE(learnTalent(table, character, "cleave"));
}

TEST_CASE("solo archetypes: rage fills from blows and hits taken, to its limit, and drains out of combat")
{
    ShippedTable shipped;
    const SoloTalentTable &table = shipped.table;
    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    member.level = 300;
    member.skills["Axe"] = {"Axe", 10, SkillMastery::Master};

    // No bar off the Arms path.
    MawSoloTalents::gainRageFromBlow(member, 0.2, 0.5f, false);
    CHECK(member.talentState.rage == doctest::Approx(0.0f));

    REQUIRE(learnTalent(table, member, "cleave"));
    // A half-second swing that took a fifth of the monster's bar: 6 x 0.5 + 30 x 0.2.
    MawSoloTalents::gainRageFromBlow(member, 0.2, 0.5f, false);
    CHECK(member.talentState.rage == doctest::Approx(9.0f));
    // An extra blow gives a third.
    MawSoloTalents::gainRageFromBlow(member, 0.2, 0.5f, true);
    CHECK(member.talentState.rage == doctest::Approx(12.0f).epsilon(0.01));
    // A hit that took a tenth of the member's own bar: 60 x 0.1; the second's limit of 20 holds the rest back.
    MawSoloTalents::gainRageFromHit(member, 0.1);
    CHECK(member.talentState.rage == doctest::Approx(18.0f).epsilon(0.01));
    MawSoloTalents::gainRageFromHit(member, 0.5);
    CHECK(member.talentState.rage == doctest::Approx(20.0f).epsilon(0.01));
    MawSoloTalents::gainRageFromBlow(member, 1.0, 0.5f, false);
    CHECK(member.talentState.rage == doctest::Approx(20.0f).epsilon(0.01));

    // The next second gives room again, in combat (not calm) without a drain.
    MawSoloTalents::update(party, 0, 0, false, 1.0f);
    CHECK(member.talentState.rage == doctest::Approx(20.0f).epsilon(0.01));
    MawSoloTalents::gainRageFromBlow(member, 1.0, 0.5f, false);
    CHECK(member.talentState.rage == doctest::Approx(40.0f).epsilon(0.01));

    // The bar never passes its maximum.
    for (int second = 0; second < 6; ++second)
    {
        MawSoloTalents::update(party, 0, 0, false, 1.0f);
        MawSoloTalents::gainRageFromBlow(member, 1.0, 0.5f, false);
    }
    CHECK(member.talentState.rage == doctest::Approx(100.0f));

    // Out of combat it drains 5 a second.
    MawSoloTalents::update(party, 0, 0, true, 2.0f);
    CHECK(member.talentState.rage == doctest::Approx(90.0f));
}

TEST_CASE("solo archetypes: Vanguard, Outnumbered, Nimble and Phase cut a hit, down to the shared floor")
{
    ShippedTable shipped;
    Character member = fighter(300);
    const auto scale = [&member](MawSoloTalents::IncomingHit hit)
    {
        return MawSoloTalents::incomingDamageScale(member, hit);
    };
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true, .firedFromDistance = 3000})
        == doctest::Approx(1.0));

    // Vanguard: a missile loosed from beyond 800, with the melee weapon in the arms.
    member.talentRanks["vanguard"] = 3;
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true, .firedFromDistance = 801})
        == doctest::Approx(0.4));
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true, .firedFromDistance = 800})
        == doctest::Approx(1.0));
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = false, .firedFromDistance = 3000})
        == doctest::Approx(1.0));
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true}) == doctest::Approx(1.0));
    member.talentRanks["vanguard"] = 1;
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true, .firedFromDistance = 3000})
        == doctest::Approx(0.8));
    member.talentState.meleeDrawn = false;
    CHECK(scale({.physical = true, .monsterAttack = true, .missile = true, .firedFromDistance = 3000})
        == doctest::Approx(1.0));
    member.talentState.meleeDrawn = true;
    member.talentRanks.erase("vanguard");

    // Outnumbered: 4 % a nearby monster at rank 3, at most ten of them; a trap is not a monster's hit. The world
    // counts the monsters within the talent's own reach (MawCombatRules::updateCombat).
    CHECK(MawSoloTalents::packReach("outnumbered") == doctest::Approx(768.0f));
    CHECK(MawSoloTalents::packReach("battle_frenzy") == doctest::Approx(768.0f));
    member.talentRanks["outnumbered"] = 3;
    CHECK(scale({.physical = true, .monsterAttack = true, .nearbyMonsters = 1}) == doctest::Approx(0.96));
    CHECK(scale({.physical = true, .monsterAttack = true, .nearbyMonsters = 4}) == doctest::Approx(0.84));
    CHECK(scale({.physical = true, .monsterAttack = true, .nearbyMonsters = 25}) == doctest::Approx(0.6));
    CHECK(scale({.physical = true, .monsterAttack = false, .nearbyMonsters = 4}) == doctest::Approx(1.0));
    // More monsters never hurt less in all: n x (1 - 0.04 n) rises to the tenth.
    for (int count = 1; count < 10; ++count)
    {
        CHECK((count + 1) * scale({.physical = true, .monsterAttack = true, .nearbyMonsters = count + 1})
            > count * scale({.physical = true, .monsterAttack = true, .nearbyMonsters = count}));
    }
    member.talentRanks.erase("outnumbered");

    // Nimble: while moving. Phase: after a Blink.
    member.talentRanks["nimble"] = 3;
    member.talentState.hasLastPosition = true;
    member.talentState.stillSeconds = 0.0f;
    CHECK(scale({.physical = true, .monsterAttack = true}) == doctest::Approx(0.85));
    member.talentState.stillSeconds = 1.0f;
    CHECK(scale({.physical = true, .monsterAttack = true}) == doctest::Approx(1.0));
    member.talentRanks.erase("nimble");
    member.talentRanks["phase"] = 3;
    CHECK(scale({.physical = true, .monsterAttack = true}) == doctest::Approx(1.0));
    member.talentState.phaseSeconds = 2.0f;
    CHECK(scale({.physical = true, .monsterAttack = true}) == doctest::Approx(0.5));
    member.talentState.phaseSeconds = 0.0f;

    // Together they multiply: Vanguard's 60 % with Spell Suppression's 20 %.
    member.talentRanks["vanguard"] = 3;
    member.talentRanks["spell_suppression"] = 41;
    CHECK(scale({.physical = false, .monsterAttack = true, .missile = true, .firedFromDistance = 3000})
        == doctest::Approx(0.32));
    member.talentRanks["vanguard"] = 1;
    CHECK(scale({.physical = false, .monsterAttack = true, .missile = true, .firedFromDistance = 3000})
        == doctest::Approx(0.64));
    // And they never leave less than a fifth: with Outnumbered's ten monsters (0.4 x 0.8 x 0.6 would be 0.192).
    member.talentRanks["vanguard"] = 3;
    member.talentRanks["outnumbered"] = 3;
    CHECK(scale({.physical = false, .monsterAttack = true, .missile = true, .firedFromDistance = 3000,
              .nearbyMonsters = 10})
        == doctest::Approx(0.2));
}

TEST_CASE("solo archetypes: Battle Frenzy, Long Shot, the spell talents, Breach and Arcane Ward")
{
    ShippedTable shipped;
    Character member = fighter(300);
    CHECK(MawSoloTalents::battleFrenzyScale(member, 10) == doctest::Approx(1.0));
    member.talentRanks["battle_frenzy"] = 3;
    CHECK(MawSoloTalents::battleFrenzyScale(member, 0) == doctest::Approx(1.0));
    CHECK(MawSoloTalents::battleFrenzyScale(member, 4) == doctest::Approx(1.2));
    CHECK(MawSoloTalents::battleFrenzyScale(member, 30) == doctest::Approx(1.5));
    member.talentRanks["battle_frenzy"] = 2;
    CHECK(MawSoloTalents::battleFrenzyScale(member, 10) == doctest::Approx(1.35));

    // Long Shot: nothing within 1536, rising evenly to 9 % at 5120 (user, 2026-11-18; 15 % until 2026-11-19).
    CHECK(MawSoloTalents::longShotScale(member, 5120) == doctest::Approx(1.0));
    member.talentRanks["long_shot"] = 3;
    CHECK(MawSoloTalents::longShotScale(member, 1000) == doctest::Approx(1.0));
    CHECK(MawSoloTalents::longShotScale(member, 1536) == doctest::Approx(1.0));
    CHECK(MawSoloTalents::longShotScale(member, 3328) == doctest::Approx(1.045));
    CHECK(MawSoloTalents::longShotScale(member, 5120) == doctest::Approx(1.09));
    CHECK(MawSoloTalents::longShotScale(member, 9000) == doctest::Approx(1.09));

    // Spell Surge, Overload and Opening Volley add: 50 + 90 + 45.
    member.talentRanks["overload"] = 3;
    member.talentRanks["opening_volley"] = 3;
    CHECK(MawSoloTalents::spellDamageBonus(member, true, 1, true) == doctest::Approx(0.45));
    CHECK(MawSoloTalents::spellDamageBonus(member, true, 6, false) == doctest::Approx(0.9));
    member.talentState.surgeDamageSeconds = 1.0f;
    CHECK(MawSoloTalents::spellDamageBonus(member, true, 6, true) == doctest::Approx(1.85));

    CHECK(MawSoloTalents::breachShare(member) == doctest::Approx(0.0));
    member.talentRanks["breach"] = 3;
    CHECK(MawSoloTalents::breachShare(member) == doctest::Approx(0.15));
    CHECK(MawSoloTalents::manaShieldCostScale(member) == doctest::Approx(1.0));
    member.talentRanks["arcane_ward"] = 3;
    CHECK(MawSoloTalents::manaShieldCostScale(member) == doctest::Approx(0.7));
    CHECK(MawSoloTalents::exposeWeaknessPercent(member) == doctest::Approx(0.0f));
    member.talentRanks["expose_weakness"] = 2;
    member.talentRanks["hamstring"] = 3;
    CHECK(MawSoloTalents::exposeWeaknessPercent(member) == doctest::Approx(6.0f));
    CHECK(MawSoloTalents::exposeWeaknessSeconds() == doctest::Approx(5.0f));
    CHECK(MawSoloTalents::hamstringPercent(member) == doctest::Approx(15.0f));
    CHECK(MawSoloTalents::hamstringSeconds() == doctest::Approx(3.0f));
}

TEST_CASE("solo archetypes: a kill takes 3 s off Charge, a spell cast that hits 1 s off Spell Surge, once a cast")
{
    ShippedTable shipped;
    Party party;
    party.seed(Party::createDefaultSeed());
    Character &member = *party.member(0);
    member.talentRanks["charge"] = 1;
    member.talentState.cooldownSeconds["charge"] = 20.0f;
    MawSoloTalents::noteKill(member);
    CHECK(member.talentState.cooldownSeconds["charge"] == doctest::Approx(17.0f));

    member.talentState.cooldownSeconds["spell_surge"] = 12.0f;
    MawSoloTalents::noteSpellHit(member);
    // An area spell's other monsters and a bolt's leaps are the same cast.
    MawSoloTalents::noteSpellHit(member);
    MawSoloTalents::noteSpellHit(member);
    CHECK(member.talentState.cooldownSeconds["spell_surge"] == doctest::Approx(11.0f));
    MawSoloTalents::update(party, 0, 0, false, 1.0f);
    MawSoloTalents::noteSpellHit(member);
    CHECK(member.talentState.cooldownSeconds["spell_surge"] == doctest::Approx(9.0f));
}

TEST_CASE("solo archetypes: the damage stages apply the talents, only in a solo run")
{
    ShippedTable shipped;
    RulesetOptions options;
    options.soloRun = true;
    MawRules solo(options, MawMapLevels{});
    MawRules plain(RulesetOptions{}, MawMapLevels{});
    Character member = fighter(300);
    member.talentRanks["long_shot"] = 3;
    member.talentRanks["opening_volley"] = 3;
    member.talentRanks["breach"] = 3;

    const auto stage = [](const MawRules &rules, MonsterDamageHit hit, const std::string &name)
    {
        std::mt19937 rng(5);
        hit.pRng = &rng;
        std::vector<DamageStageRecord> records;
        rules.gameRules().combat.damageToMonsterStages().run(hit, &records);
        for (const DamageStageRecord &record : records)
        {
            if (record.stage == name)
            {
                return std::pair<int, int>(record.before, record.after);
            }
        }
        return std::pair<int, int>(0, 0);
    };

    // An arrow that flew the bow's full range: Long Shot's 9 %.
    MonsterDamageHit arrow;
    arrow.amount = 10000;
    arrow.pMissileAttacker = &member;
    arrow.missileFlightDistance = 5120;
    arrow.targetFacts.level = 100;
    arrow.targetFacts.maxHp = 50000;
    arrow.targetCurrentHp = 20000;
    std::pair<int, int> result = stage(solo, arrow, "solo-talents");
    REQUIRE(result.first > 0);
    CHECK(result.second == doctest::Approx(result.first * 1.09).epsilon(0.001));
    // Expose Weakness on the monster adds its share to every hit.
    arrow.targetFacts.exposedPercent = 9;
    arrow.targetFacts.exposedUntilGameMinutes = 100;
    result = stage(solo, arrow, "solo-talents");
    CHECK(result.second == doctest::Approx(result.first * 1.09 * 1.09).epsilon(0.001));
    // Not in a party game.
    result = stage(plain, arrow, "solo-talents");
    CHECK(result.second == result.first);

    // A spell on a monster at full health: Opening Volley's 45 %; on a hurt one nothing.
    MonsterDamageHit spell;
    spell.amount = 10000;
    spell.type = CombatDamageType::Fire;
    spell.pMissileAttacker = &member;
    spell.missileSpellId = 2;
    spell.targetFacts.level = 100;
    spell.targetFacts.maxHp = 50000;
    spell.targetCurrentHp = 50000;
    result = stage(solo, spell, "solo-talents");
    CHECK(result.second == doctest::Approx(result.first * 1.45).epsilon(0.001));
    spell.targetCurrentHp = 49999;
    result = stage(solo, spell, "solo-talents");
    CHECK(result.second == result.first);

    // Breach: a resistance of 200 counts as 170, so the spell does 2^0.3 as much after the resistance stage.
    spell.resistance = 200;
    const std::pair<int, int> breached = stage(solo, spell, "resistance");
    const std::pair<int, int> whole = stage(plain, spell, "resistance");
    REQUIRE(whole.second > 0);
    CHECK(double(breached.second) / whole.second == doctest::Approx(std::pow(2.0, 0.3)).epsilon(0.01));
}
