#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"
#include "game/rules/CombatRules.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSoloTalents.h"
#include "game/tables/ItemTable.h"

#include <doctest/doctest.h>

#include <chrono>
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
  - {id: onslaught, name: Onslaught, tree: arms, kind: passive, max_rank: 3, per_rank: 10, duration: 30}
  - {id: shield_wall, name: Shield Wall, tree: arms, kind: active, max_rank: 3, requires: expert, cooldown: 60,
     duration: 6, per_rank: 50}
  - {id: quickfoot, name: Quickfoot, tree: archery, kind: passive, max_rank: 3, per_rank: 3, per_rank_calm: 15}
  - {id: steady_aim, name: Steady Aim, tree: archery, kind: passive, max_rank: 3, per_rank: 10}
  - {id: resolve, name: Resolve, tree: arcana, kind: passive, max_rank: 5, per_rank: 2}
  - {id: spell_surge, name: Spell Surge, tree: arcana, kind: active, max_rank: 3, requires: master, cooldown: 45,
     per_rank: 50}
  - {id: overload, name: Overload, tree: arcana, kind: passive, max_rank: 3, requires: expert, per_rank: 10, targets: 3}
  - {id: bloodthirst, name: Bloodthirst, tree: any, kind: passive, max_rank: 5, per_rank: 2}
  - {id: conditioning, name: Conditioning, tree: any, kind: passive, max_rank: unlimited, first_rank: 10,
     per_rank: 1, text: "+{value} %"}
  - {id: spell_suppression, name: Spell Suppression, tree: any, kind: passive, max_rank: 41, first_rank: 8,
     per_rank: 0.8}
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

TEST_CASE("solo talents: the shipped table loads (tree v2)")
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
    CHECK(table.talents().size() == 19);
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
    // Spell Suppression: 8 % at rank 1, 0.8 % a rank after, 40 % at its last rank 41. Conditioning: 10 % at rank 1,
    // 1 % a rank after. Manathirst, the newest, is last in the table so the action bar's indexes keep.
    const TalentDefinition *pSuppression = table.find("spell_suppression");
    REQUIRE(pSuppression != nullptr);
    CHECK(pSuppression->tree == TalentTree::Any);
    CHECK(pSuppression->maxRank == 41);
    CHECK(talentValue(*pSuppression, 1) == doctest::Approx(8.0f));
    CHECK(talentValue(*pSuppression, 2) == doctest::Approx(8.8f));
    CHECK(talentValue(*pSuppression, 41) == doctest::Approx(40.0f));
    CHECK(talentValue(*pConditioning, 1) == doctest::Approx(10.0f));
    CHECK(table.talents().back().id == "manathirst");
    CHECK(table.talents().back().maxRank == 5);
    CHECK(talentValue(table.talents().back(), 5) == doctest::Approx(10.0f));
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
    // The shipped experience surcharge, half of MAW's.
    REQUIRE(shipped.experienceSurcharge().has_value());
    CHECK(*shipped.experienceSurcharge() == doctest::Approx(0.0025));

    // No list, no cut; a divisor below 1 is refused; past a list that ends above 1 the cut is over all the same.
    SoloTalentTable none;
    REQUIRE(none.loadFromYaml("talents: []", error));
    CHECK(none.earlyMonsterCut(1) == doctest::Approx(1.0));
    CHECK_FALSE(none.experienceSurcharge().has_value());
    SoloTalentTable bad;
    CHECK_FALSE(bad.loadFromYaml("early_monster_cut: [[1, 0.5]]\ntalents: []", error));
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

TEST_CASE("solo talents: one point every fifteen levels; keystones and removed talents cost nothing")
{
    BoundTable bound;
    Character character = fighter(14);
    CHECK(talentPointsTotal(bound.table, character) == 0);
    CHECK(nextTalentPointLevel(bound.table, character) == 15);
    character.level = 47;
    CHECK(talentPointsTotal(bound.table, character) == 3);
    CHECK(nextTalentPointLevel(bound.table, character) == 60);
    character.talentRanks["resolve"] = 2;
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
    const TalentDefinition &training = *bound.table.find("resolve");
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
    spent.talentRanks["resolve"] = 1;
    CHECK_FALSE(talentLearnRefusal(bound.table, spent, training).empty());
    Character full = fighter(200);
    full.talentRanks["resolve"] = 5;
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

TEST_CASE("solo talents: passives add their share of the base stats")
{
    BoundTable bound;
    Character character = fighter(60);
    character.accuracy = 60;
    character.luck = 80;
    character.talentRanks["conditioning"] = 1;
    character.talentRanks["resolve"] = 5;
    character.baseResistances.fire = 40;
    character.permanentBonuses.resistances.fire = 30;
    character.magicalBonuses.resistances.fire = 10;
    MawSoloTalents::applyPassives(character);
    // Conditioning's first rank: 10 % of each of the seven base stats.
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
    MawSoloTalents::applyPassives(eleven);
    CHECK(eleven.magicalBonuses.might == 20);
    // Resolve: 10 % of the 80 base, permanent and magical fire resistance.
    CHECK(character.magicalBonuses.resistances.fire == 18);
    // Spells no longer take a passive's share.
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.0));

    // Steady Aim while still adds its Luck to Conditioning's.
    Character still = fighter(60);
    still.luck = 80;
    still.talentRanks["conditioning"] = 1;
    still.talentRanks["steady_aim"] = 3;
    still.talentState.steadyAimOn = true;
    MawSoloTalents::applyPassives(still);
    CHECK(still.magicalBonuses.luck == 32);
}

TEST_CASE("solo talents: Onslaught stacks on kills, up to ten per rank, and runs out")
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
    CHECK(character.talentState.onslaughtStacks == 10);
    CHECK(character.talentState.onslaughtSeconds == doctest::Approx(30));
    CHECK(MawSoloTalents::attackRecoveryScale(character) == doctest::Approx(1.0 / 1.1));

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

TEST_CASE("solo talents: Shield Wall, Unbroken and Cheat Death")
{
    BoundTable bound;
    Character character = fighter(300);
    character.talentRanks["conditioning"] = 1;
    // Shield Wall needs a shield in hand.
    character.talentState.shieldWallSeconds = 3;
    CHECK(MawSoloTalents::absorbDamage(character, 100, 1000) == 100);
    character.equipment.offHand = 1;
    CHECK(MawSoloTalents::absorbDamage(character, 100, 1000) == 50);
    character.talentState.shieldWallSeconds = 0;

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

TEST_CASE("solo talents: Resolve raises MAW's sheet resistances (armour skills, staves, Luck) in a solo run")
{
    BoundTable bound;
    RulesetOptions options;
    options.soloRun = true;
    MawRules rules(options, MawMapLevels{});
    ItemTable items;
    Character member = fighter(300);
    member.talentRanks["resolve"] = 5;
    // Luck 1000: 200 to every resistance row, and 10 % more at five ranks.
    const CharacterCombatRows solo = mawCombatRows(rules, member, items, {100, 100, 1000});
    CHECK(solo.resistances.fire == 220);
    CHECK(solo.resistances.mind == 220);

    member.talentRanks.erase("resolve");
    CHECK(mawCombatRows(rules, member, items, {100, 100, 1000}).resistances.fire == 200);

    // Outside a solo run the talent does nothing.
    member.talentRanks["resolve"] = 5;
    MawRules party(RulesetOptions{}, MawMapLevels{});
    CHECK(mawCombatRows(party, member, items, {100, 100, 1000}).resistances.fire == 200);
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
    CHECK(MawSoloTalents::nonPhysicalDamageScale(member) == doctest::Approx(0.6));
    const int suppressed = run(CombatDamageType::Fire, records);
    // The last stage, after the mitigation and its floor: what the hit would have been, less 40 %.
    REQUIRE_FALSE(records.empty());
    CHECK(records.back().stage == "solo-spell-suppression");
    CHECK(records.back().before == plainFire);
    CHECK(suppressed == doctest::Approx(plainFire * 0.6).epsilon(0.001));
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
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.5));
    MawSoloTalents::spendSurge(character);
    CHECK_FALSE(MawSoloTalents::nextSpellFree(character));
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.5));

    CHECK(MawSoloTalents::overloadScale(character, 4) == doctest::Approx(1.0));
    character.talentRanks["overload"] = 2;
    CHECK(MawSoloTalents::overloadScale(character, 1) == doctest::Approx(1.0));
    CHECK(MawSoloTalents::overloadScale(character, 3) == doctest::Approx(1.4));
    // At most three more monsters count.
    CHECK(MawSoloTalents::overloadScale(character, 9) == doctest::Approx(1.6));

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
