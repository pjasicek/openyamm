#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"
#include "game/rules/maw/MawSoloTalents.h"

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
  - {id: weapon_training, name: Weapon Training, tree: arms, kind: passive, max_rank: 5, per_rank: 2, text: "+{value} %"}
  - {id: cleave, name: Cleave, tree: arms, kind: active, max_rank: 3, requires: expert, cooldown: 12,
     cooldown_per_rank: -2, targets: 64, share: 150, arc: 60, duration: 1}
  - {id: sweeping_blows, name: Sweeping Blows, tree: arms, kind: passive, max_rank: 3, requires: expert, needs: cleave,
     per_rank: 1, share: 30, share_per_skill: 0.25, share_cap: 50, arc: 60}
  - {id: onslaught, name: Onslaught, tree: arms, kind: passive, max_rank: 3, per_rank: 10, duration: 30}
  - {id: shield_wall, name: Shield Wall, tree: arms, kind: active, max_rank: 3, requires: expert, cooldown: 60,
     duration: 6, per_rank: 50}
  - {id: quickfoot, name: Quickfoot, tree: archery, kind: passive, max_rank: 3, per_rank: 3, per_rank_calm: 15}
  - {id: attunement, name: Attunement, tree: arcana, kind: passive, max_rank: 5, per_rank: 2}
  - {id: resolve, name: Resolve, tree: arcana, kind: passive, max_rank: 5, per_rank: 2}
  - {id: spell_surge, name: Spell Surge, tree: arcana, kind: active, max_rank: 3, requires: master, cooldown: 45,
     per_rank: 50}
  - {id: overload, name: Overload, tree: arcana, kind: passive, max_rank: 3, requires: expert, per_rank: 10, targets: 3}
  - {id: bloodthirst, name: Bloodthirst, tree: any, kind: passive, max_rank: 3, per_rank: 2}
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
    CHECK(table.levelsPerPoint() == 10);
    CHECK(table.keystones().size() == 2);
    CHECK(table.keystoneLevels() == std::vector<uint32_t>{150, 300});
    REQUIRE(table.find("cleave") != nullptr);
    CHECK(table.find("cleave")->share == doctest::Approx(150));
    REQUIRE(table.find("sweeping_blows") != nullptr);
    CHECK(table.find("sweeping_blows")->needs == "cleave");
    CHECK(table.find("whirlwind") == nullptr);
    CHECK(table.find("purify") == nullptr);
    CHECK(table.findKeystone("cheat_death") != nullptr);
    CHECK(table.findKeystone("unbroken") != nullptr);
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
    character.talentRanks["weapon_training"] = 2;
    character.talentRanks["unbroken"] = 1;
    // A talent the table no longer has (an older save's Whirlwind) gives its points back.
    character.talentRanks["whirlwind"] = 3;
    CHECK(talentPointsSpent(bound.table, character) == 2);
    CHECK(talentPointsAvailable(bound.table, character) == 1);
}

TEST_CASE("solo talents: mastery locks and talents that need another first")
{
    BoundTable bound;
    Character character = fighter(200);
    const TalentDefinition &training = *bound.table.find("weapon_training");
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
    spent.talentRanks["weapon_training"] = 1;
    CHECK_FALSE(talentLearnRefusal(bound.table, spent, training).empty());
    Character full = fighter(200);
    full.talentRanks["weapon_training"] = 5;
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
    party.member(0)->talentRanks["attunement"] = 4;
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
    CHECK(loaded->party.members[0].talentRanks.at("attunement") == 4);
    CHECK(loaded->party.members[0].talentRanks.at("cheat_death") == 1);
}

TEST_CASE("solo talents: passives add their share of the base stats")
{
    BoundTable bound;
    Character character = fighter(60);
    character.talentRanks["weapon_training"] = 3;
    character.talentRanks["attunement"] = 2;
    character.talentRanks["resolve"] = 5;
    character.baseResistances.fire = 40;
    character.magicalBonuses.resistances.fire = 10;
    MawSoloTalents::applyPassives(character);
    CHECK(character.magicalBonuses.might == 6);
    // Endurance takes Weapon Training's 6 % and Attunement's 4 %.
    CHECK(character.magicalBonuses.endurance == 5);
    CHECK(character.magicalBonuses.speed == 2);
    CHECK(character.magicalBonuses.intellect == 1);
    // Resolve: 10 % of the 50 fire resistance.
    CHECK(character.magicalBonuses.resistances.fire == 15);
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.04));
    CHECK(MawSoloTalents::healScale(character) == doctest::Approx(1.04));
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
    character.talentRanks["weapon_training"] = 1;
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
    character.talentRanks["bloodthirst"] = 3;
    CHECK(MawSoloTalents::leechBonus(character) == doctest::Approx(0.06));
    CHECK(MawSoloTalents::leechFloorDivisor(character) == doctest::Approx(2.5));
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
