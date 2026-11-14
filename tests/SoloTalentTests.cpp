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
levels_per_point: 10
talents:
  - {id: weapon_training, name: Weapon Training, tree: melee, kind: passive, max_rank: 5, per_rank: 2, text: "+{value} %"}
  - {id: cleave, name: Cleave, tree: melee, kind: active, max_rank: 3, requires: expert, cooldown: 12,
     cooldown_per_rank: -2, targets: 5, share: 60, arc: 60}
  - {id: whirlwind, name: Whirlwind, tree: melee, kind: active, max_rank: 3, requires: master, cooldown: 20}
  - {id: frenzy, name: Frenzy, tree: melee, kind: active, max_rank: 3, requires: expert, cooldown: 30, duration: 6,
     duration_per_rank: 1, per_rank: 25}
  - {id: shield_wall, name: Shield Wall, tree: melee, kind: active, max_rank: 3, requires: expert, cooldown: 60,
     duration: 6, per_rank: 50}
  - {id: attunement, name: Attunement, tree: caster, kind: passive, max_rank: 5, per_rank: 2}
  - {id: resolve, name: Resolve, tree: caster, kind: passive, max_rank: 5, per_rank: 2}
  - {id: spell_surge, name: Spell Surge, tree: caster, kind: active, max_rank: 3, requires: master, cooldown: 45,
     per_rank: 50}
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

TEST_CASE("solo talents: the shipped table loads")
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
    CHECK(table.talents().size() == 17);
    CHECK(table.levelsPerPoint() == 10);
    REQUIRE(table.find("cleave") != nullptr);
    CHECK(table.find("cleave")->targets == 5);
    CHECK(table.find("cleave")->share == doctest::Approx(60));
}

TEST_CASE("solo talents: one point every ten levels")
{
    BoundTable bound;
    Character character = fighter(9);
    CHECK(talentPointsTotal(bound.table, character) == 0);
    CHECK(nextTalentPointLevel(bound.table, character) == 10);
    character.level = 47;
    CHECK(talentPointsTotal(bound.table, character) == 4);
    CHECK(nextTalentPointLevel(bound.table, character) == 50);
    character.talentRanks["weapon_training"] = 3;
    CHECK(talentPointsSpent(character) == 3);
    CHECK(talentPointsAvailable(bound.table, character) == 1);
}

TEST_CASE("solo talents: passives are open, actives need the tree's skill at Expert or Master")
{
    BoundTable bound;
    Character character = fighter(60);
    const TalentDefinition &training = *bound.table.find("weapon_training");
    const TalentDefinition &cleave = *bound.table.find("cleave");
    const TalentDefinition &whirlwind = *bound.table.find("whirlwind");
    CHECK(talentLearnRefusal(bound.table, character, training).empty());
    CHECK_FALSE(talentLearnRefusal(bound.table, character, cleave).empty());

    character.skills["Axe"] = {"Axe", 7, SkillMastery::Expert};
    CHECK(talentLearnRefusal(bound.table, character, cleave).empty());
    CHECK_FALSE(talentLearnRefusal(bound.table, character, whirlwind).empty());
    character.skills["Armsmaster"] = {"Armsmaster", 10, SkillMastery::Master};
    CHECK(talentLearnRefusal(bound.table, character, whirlwind).empty());

    // No points left, and the last rank.
    Character spent = fighter(10);
    spent.talentRanks["weapon_training"] = 1;
    CHECK_FALSE(talentLearnRefusal(bound.table, spent, training).empty());
    Character full = fighter(200);
    full.talentRanks["weapon_training"] = 5;
    CHECK_FALSE(talentLearnRefusal(bound.table, full, training).empty());
}

TEST_CASE("solo talents: learning an active puts it on the bar; a reset forgets it all")
{
    BoundTable bound;
    Character character = fighter(40);
    character.skills["Sword"] = {"Sword", 7, SkillMastery::Expert};
    character.actionBar[0] = {ActionBarSlotKind::Weapon, 0, {}};
    REQUIRE(learnTalent(bound.table, character, "cleave"));
    CHECK(talentRank(character, "cleave") == 1);
    const uint32_t cleaveIndex = uint32_t(bound.table.find("cleave") - bound.table.talents().data());
    CHECK(character.actionBar[1].kind == ActionBarSlotKind::Talent);
    CHECK(character.actionBar[1].id == cleaveIndex);
    // A second rank does not place it twice.
    REQUIRE(learnTalent(bound.table, character, "cleave"));
    CHECK(character.actionBar[2].kind == ActionBarSlotKind::Empty);
    REQUIRE(learnTalent(bound.table, character, "weapon_training"));
    CHECK(character.actionBar[2].kind == ActionBarSlotKind::Empty);

    character.talentState.cooldownSeconds["cleave"] = 5;
    resetTalents(character);
    CHECK(character.talentRanks.empty());
    CHECK(character.actionBar[1].kind == ActionBarSlotKind::Empty);
    CHECK(character.actionBar[0].kind == ActionBarSlotKind::Weapon);
    CHECK(character.talentState.cooldownSeconds.empty());
}

TEST_CASE("solo talents: a save keeps the learned ranks")
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

TEST_CASE("solo talents: Frenzy, Shield Wall, Spell Surge and Purify while they last")
{
    BoundTable bound;
    Character character = fighter(60);
    CHECK(MawSoloTalents::attackRecoveryScale(character) == doctest::Approx(1.0));
    character.talentState.frenzySeconds = 3;
    CHECK(MawSoloTalents::attackRecoveryScale(character) == doctest::Approx(0.8));

    character.talentState.shieldWallSeconds = 3;
    CHECK(MawSoloTalents::absorbDamage(character, 100) == 100);
    character.equipment.offHand = 1;
    CHECK(MawSoloTalents::absorbDamage(character, 100) == 50);

    character.talentState.spellSurgeArmed = true;
    CHECK(MawSoloTalents::nextSpellFree(character));
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.5));
    MawSoloTalents::spendSurge(character);
    CHECK_FALSE(MawSoloTalents::nextSpellFree(character));
    CHECK(MawSoloTalents::spellDamageScale(character) == doctest::Approx(1.5));

    character.talentState.purifyCondition = size_t(CharacterCondition::Paralyzed);
    character.talentState.purifySeconds = 5;
    CHECK(MawSoloTalents::blocksCondition(character, CharacterCondition::Paralyzed));
    CHECK_FALSE(MawSoloTalents::blocksCondition(character, CharacterCondition::Asleep));
}

TEST_CASE("solo talents: cooldowns shorten with rank and run down in the update")
{
    BoundTable bound;
    const TalentDefinition &cleave = *bound.table.find("cleave");
    CHECK(talentCooldownSeconds(cleave, 1) == doctest::Approx(12));
    CHECK(talentCooldownSeconds(cleave, 3) == doctest::Approx(8));
    const TalentDefinition &frenzy = *bound.table.find("frenzy");
    CHECK(talentDurationSeconds(frenzy, 3) == doctest::Approx(8));

    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    member.talentRanks["cleave"] = 1;
    member.talentState.cooldownSeconds["cleave"] = 5;
    member.talentState.frenzySeconds = 1;
    MawSoloTalents::update(party, 0, 0, 2);
    CHECK(member.talentState.cooldownSeconds["cleave"] == doctest::Approx(3));
    CHECK(member.talentState.frenzySeconds == doctest::Approx(0));
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
    // All around: everything living in reach.
    const std::vector<size_t> whirlwind = pickTalentTargets(candidates, 0, 0, 0, 0.0f, 407.2f, 180.0f, 64);
    CHECK(whirlwind.size() == 4);
    // The count caps it.
    CHECK(pickTalentTargets(candidates, 0, 0, 0, 0.0f, 407.2f, 180.0f, 2).size() == 2);
}
