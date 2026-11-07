#include "PartySpellTestHarness.h"
#include "RegressionGameData.h"
#include "doctest/doctest.h"
#include "game/content/RulesetOptions.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawRules.h"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// MAW's challenge modes (devdocs/maw/PHASE9_SCOPE.md), by scope id.
namespace
{
MawItemData installedItemData()
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(text, error), error);
    return data;
}

RulesetOptions modeOptions(RulesetChallengeMode mode)
{
    RulesetOptions options;
    options.challengeMode = mode;
    options.difficulty = rulesetChallengeModeDifficulty(mode).value_or(options.difficulty);
    options.progression = rulesetChallengeModeProgression(mode).value_or(options.progression);
    return options;
}
}

TEST_CASE("The Doom modes play at Nightmare; Austerity keeps a changeable difficulty")
{
    for (const RulesetChallengeMode mode :
         {RulesetChallengeMode::Doom, RulesetChallengeMode::RoadToInsanity, RulesetChallengeMode::BeyondMadness})
    {
        CHECK(rulesetChallengeModeDifficulty(mode) == RulesetDifficulty::Nightmare);
        CHECK(modeOptions(mode).difficultyLocked());
    }

    CHECK_FALSE(rulesetChallengeModeDifficulty(RulesetChallengeMode::Austerity).has_value());
    RulesetOptions austerity = modeOptions(RulesetChallengeMode::Austerity);
    austerity.difficulty = RulesetDifficulty::Hard;
    CHECK_FALSE(austerity.difficultyLocked());
    austerity.difficulty = RulesetDifficulty::Nightmare;
    CHECK(austerity.difficultyLocked());

    // The --ruleset ids and scenarios take the mode's difficulty and progression over the ones given beside it.
    RulesetOptions parsed;
    REQUIRE(applyRulesetOptionIds("easy:free:beyond_madness", parsed));
    CHECK(parsed.difficulty == RulesetDifficulty::Nightmare);
    CHECK(parsed.progression == RulesetProgression::Horizontal);
    RulesetOptions austerityParsed;
    REQUIRE(applyRulesetOptionIds("hell:austerity", austerityParsed));
    CHECK(austerityParsed.difficulty == RulesetDifficulty::Hell);
}

TEST_CASE("A Doom party starts with 5000 gold, experience and item power (P9.D1)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const MawItemData items = installedItemData();
    REQUIRE(items.baseItem(84) != nullptr);

    for (const RulesetChallengeMode mode : {RulesetChallengeMode::Doom, RulesetChallengeMode::RoadToInsanity})
    {
        MawRules rules(modeOptions(mode), MawMapLevels{}, items);
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        Character &member = *party.member(0);
        const uint32_t level = member.level;
        const uint32_t experience = member.experience;
        member.inventory.push_back(InventoryItem{.objectDescriptionId = 84});
        member.inventory.push_back(InventoryItem{.objectDescriptionId = 2020});
        member.equipment.armor = 84;
        member.equipmentRuntime.armor = {};

        rules.gameRules().experience.prepareNewParty(party);
        const int power = mode == RulesetChallengeMode::Doom ? 2 : 4;
        CHECK_EQ(party.gold(), 5000);
        CHECK_EQ(member.level, level);
        CHECK_EQ(member.experience, experience + 10000 / uint32_t(party.members().size()));
        CHECK_EQ(int(member.inventory[member.inventory.size() - 2].rulesetFields.itemPower), power);
        CHECK_EQ(int(member.inventory.back().rulesetFields.itemPower), 0);
        CHECK_EQ(int(member.equipmentRuntime.armor.rulesetFields.itemPower), power);
    }
}

TEST_CASE("A Beyond Madness party restarts at level 1 with every skill at 1 (P9.M1)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(modeOptions(RulesetChallengeMode::BeyondMadness), MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &member = *party.member(0);
    member.level = 12;
    member.experience = 90000;
    member.skillPoints = 7;
    member.skills["Sword"] = {"Sword", 9, SkillMastery::Expert};
    member.skills["Cover"] = {"Cover", 6, SkillMastery::Expert};

    rules.gameRules().experience.prepareNewParty(party);
    CHECK_EQ(member.level, 1u);
    CHECK_EQ(member.skillPoints, 0u);
    CHECK_EQ(member.experience, 10000 / uint32_t(party.members().size()));
    CHECK_EQ(member.skills["Sword"].level, 1u);
    CHECK(member.skills["Sword"].mastery == SkillMastery::Normal);
    // MAW's own four skills are left as they are.
    CHECK_EQ(member.skills["Cover"].level, 6u);
    CHECK_EQ(party.gold(), 5000);
}

TEST_CASE("MAW's start reaches roster heroes: Learning refunded, Beyond Madness level 1, Doom item power (CHM-1)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    // Brimstone: level 30, Grandmaster Learning 10.
    const RosterEntry *pBrimstone = gameData.rosterTable.get(24);
    REQUIRE(pBrimstone != nullptr);
    const MawItemData items = installedItemData();
    const auto hired = [&gameData](const GameRules *pRules, const RosterEntry &entry)
    {
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(pRules);
        REQUIRE(party.replaceMemberWithRosterEntry(0, entry));
        return *party.member(0);
    };

    // Standard keeps the roster as it is.
    const Character standard = hired(nullptr, *pBrimstone);
    REQUIRE(standard.findSkill("Learning") != nullptr);
    REQUIRE_EQ(standard.findSkill("Learning")->level, 10u);
    REQUIRE_EQ(standard.level, 30u);

    // Any MAW game: Learning comes off and gives back 10 + 9 + ... + 2 points.
    MawRules plain(RulesetOptions{}, MawMapLevels{}, items);
    const Character maw = hired(&plain.gameRules(), *pBrimstone);
    CHECK(maw.findSkill("Learning") == nullptr);
    CHECK_EQ(maw.skillPoints, standard.skillPoints + 54);
    CHECK_EQ(maw.level, 30u);

    // Beyond Madness: level 1, no experience or points, every skill at 1.
    MawRules madness(modeOptions(RulesetChallengeMode::BeyondMadness), MawMapLevels{}, items);
    const Character reset = hired(&madness.gameRules(), *pBrimstone);
    CHECK_EQ(reset.level, 1u);
    CHECK_EQ(reset.experience, 0u);
    CHECK_EQ(reset.skillPoints, 0u);
    CHECK(reset.findSkill("Learning") == nullptr);

    for (const auto &[name, skill] : reset.skills)
    {
        if (!isRulesetSkill(name))
        {
            CHECK_EQ(skill.level, 1u);
            CHECK(skill.mastery == SkillMastery::Normal);
        }
    }

    // Doom: the roster hero's enchantable items get item power 2 (Infaustus; Brimstone carries none).
    const RosterEntry *pInfaustus = gameData.rosterTable.get(23);
    REQUIRE(pInfaustus != nullptr);
    MawRules doom(modeOptions(RulesetChallengeMode::Doom), MawMapLevels{}, items);
    const Character doomed = hired(&doom.gameRules(), *pInfaustus);
    bool anyPowered = false;

    const auto checkPower = [&items, &anyPowered](uint32_t itemId, const ItemRulesetFields &fields)
    {
        if (items.baseItem(itemId) != nullptr && itemId != 2020)
        {
            CHECK_EQ(int(fields.itemPower), 2);
            anyPowered = true;
        }
    };

    for (const InventoryItem &item : doomed.inventory)
    {
        checkPower(item.objectDescriptionId, item.rulesetFields);
    }

    // The roster's items are put on when the hero joins.
    checkPower(doomed.equipment.mainHand, doomed.equipmentRuntime.mainHand.rulesetFields);
    checkPower(doomed.equipment.offHand, doomed.equipmentRuntime.offHand.rulesetFields);
    checkPower(doomed.equipment.armor, doomed.equipmentRuntime.armor.rulesetFields);
    checkPower(doomed.equipment.helm, doomed.equipmentRuntime.helm.rulesetFields);
    checkPower(doomed.equipment.boots, doomed.equipmentRuntime.boots.rulesetFields);
    checkPower(doomed.equipment.cloak, doomed.equipmentRuntime.cloak.rulesetFields);
    CHECK(anyPowered);
}

TEST_CASE("Austerity and no mode leave the new party alone")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();

    for (const RulesetChallengeMode mode : {RulesetChallengeMode::None, RulesetChallengeMode::Austerity})
    {
        MawRules rules(modeOptions(mode), MawMapLevels{}, installedItemData());
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        const int gold = party.gold();
        const uint32_t experience = party.member(0)->experience;
        rules.gameRules().experience.prepareNewParty(party);
        CHECK_EQ(party.gold(), gold);
        CHECK_EQ(party.member(0)->experience, experience);
    }
}

TEST_CASE("Event scripts see the challenge mode in evt.RulesetInfo (Q8)")
{
    MawRules doom(modeOptions(RulesetChallengeMode::Doom), MawMapLevels{}, installedItemData());
    CHECK_EQ(doom.gameRules().monsters.scriptInfo(0).challengeMode, "doom");
    MawRules plain(RulesetOptions{}, MawMapLevels{}, installedItemData());
    CHECK_EQ(plain.gameRules().monsters.scriptInfo(0).challengeMode, "none");
    CHECK_EQ(standardGameRules().monsters.scriptInfo(0).challengeMode, "none");
}

TEST_CASE("experience is 64 bits: MAW characters train past level 1063, Standard keeps the 4 billion cap")
{
    // Audit ROB-2-1: MAW's level 1064 needs 4,011,174,940 experience, more than 32 bits hold.
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    constexpr uint64_t Level1064 = 4011174940ull;

    CHECK_EQ(party.setMemberExperience(0, Level1064 + 5), 4000000000ull);
    CHECK_EQ(party.addExperienceToMember(0, 1000000000), 4000000000ull);

    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    party.setRules(&rules.gameRules());
    CHECK_EQ(party.setMemberExperience(0, Level1064 + 5), Level1064 + 5);
    CHECK_EQ(party.addExperienceToMember(0, 6000000000), Level1064 + 6000000005ull);
    CHECK_EQ(party.member(0)->experience, Level1064 + 6000000005ull);
    CHECK_EQ(party.addExperienceToMember(0, -int64_t(Level1064) * 10), 0u);
}

TEST_CASE("Beyond Madness: an event's experience is the same for every member, the bank paid once after it")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::ifstream supportFile(std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev/engine/scripts/common/event_support.lua");
    std::ostringstream supportLua;
    supportLua << supportFile.rdbuf();
    std::string error;
    const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
        supportLua.str() + R"lua(
RegisterEvent(1, "Quest reward", function()
    evt.ForPlayer(Players.All)
    evt.Add(eventSupport.varTag.Experience, 1000)
end)
)lua",
        "@tests/maw_event_experience.lua", ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    MawRules rules(modeOptions(RulesetChallengeMode::BeyondMadness), MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    const size_t partySize = party.members().size();
    REQUIRE(partySize > 1);
    std::vector<uint64_t> before;

    for (const Character &member : party.members())
    {
        before.push_back(member.experience);
    }

    // MAW banks every member's share on the next tick (zzzMaw_Experience.lua:93-126), so the level the reward is
    // scaled by is the one before it: 1000 x 5 / party size each at level 0, and 1000 banked once all are paid.
    EventRuntimeState runtimeState = {};
    EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, runtimeState, &party));

    for (size_t index = 0; index < partySize; ++index)
    {
        CHECK_EQ(party.members()[index].experience - before[index], uint64_t(1000 * 5 / partySize));
    }

    CHECK_EQ(rules.state().bankedExperience, doctest::Approx(1000));
}
