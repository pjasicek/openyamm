#include "doctest/doctest.h"

#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/mm9/Mm9HirelingServices.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

// MM9 hirelings' dialogue services, passives, wages and story companions (devdocs/mm9/MM9_HIRELINGS_PLAN.md phases
// 7-8), on the MM9 world's real hireling table.
namespace
{
using OpenYAMM::Game::Character;
using OpenYAMM::Game::CharacterCondition;
using OpenYAMM::Game::CharacterSkill;
using OpenYAMM::Game::Mm9HireOutcome;
using OpenYAMM::Game::Mm9Hireling;
using OpenYAMM::Game::Mm9HirelingServiceOutcome;
using OpenYAMM::Game::Mm9HirelingTable;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::SkillMastery;
using OpenYAMM::Game::SpeechId;

constexpr float MinutesPerDay = 24.0f * 60.0f;

const Mm9HirelingTable &worldTable()
{
    static const Mm9HirelingTable table = []
    {
        std::ifstream file(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/data_tables/hirelings.txt");
        std::vector<std::vector<std::string>> rows;
        std::string line;

        while (std::getline(file, line))
        {
            if (!line.empty() && line.back() == '\r')
            {
                line.pop_back();
            }

            std::vector<std::string> cells;
            std::stringstream stream(line);
            std::string cell;

            while (std::getline(stream, cell, '\t'))
            {
                cells.push_back(cell);
            }

            if (!line.empty() && line.back() == '\t')
            {
                cells.emplace_back();
            }

            rows.push_back(std::move(cells));
        }

        Mm9HirelingTable loaded;
        loaded.loadFromRows(rows);
        return loaded;
    }();
    REQUIRE_MESSAGE(table.entries().size() == 15u, "the MM9 world's hirelings.txt did not load");
    return table;
}

const Mm9Hireling &row(uint32_t rudeId)
{
    const Mm9Hireling *pRow = worldTable().find(rudeId);
    REQUIRE(pRow != nullptr);
    return *pRow;
}

Party makeParty(int gold)
{
    OpenYAMM::Game::PartySeed seed = {};

    for (size_t memberIndex = 0; memberIndex < 4; ++memberIndex)
    {
        Character member = {};
        member.name = "Member " + std::to_string(memberIndex + 1);
        member.maxHealth = 100;
        member.health = 100;
        member.might = 15;
        member.endurance = 15;
        member.speed = 15;
        member.luck = 15;
        seed.members.push_back(member);
    }

    seed.gold = gold;
    Party party = {};
    party.seed(seed);
    party.setMm9HirelingTable(&worldTable());
    return party;
}

bool spoke(const Party &party, SpeechId speechId)
{
    for (const Party::PendingAudioRequest &request : party.pendingAudioRequests())
    {
        if (request.kind == Party::PendingAudioRequest::Kind::Speech && request.speechId == speechId)
        {
            return true;
        }
    }

    return false;
}
}

TEST_CASE("MM9 hire charges the fee, sets the hire key and keeps MM9's limits")
{
    Party party = makeParty(5000);
    const Mm9Hireling &tesar = row(43);
    CHECK_EQ(tesar.hireQBit, 90451u);

    CHECK(OpenYAMM::Game::hireMm9Hireling(party, tesar) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.gold(), 4500);
    CHECK(party.hasQuestBit(90451));
    REQUIRE(party.findHireling(43) != nullptr);
    // Already along: refused, nothing charged.
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, tesar) == Mm9HireOutcome::Refused);
    CHECK_EQ(party.gold(), 4500);

    // Florie's fee is 2000 (her wage 1000): a second paid retainer.
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, row(308)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.gold(), 2500);
    // A third paid retainer is refused (two at most); the third slot is a story companion's, free.
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, row(42)) == Mm9HireOutcome::Refused);
    CHECK_FALSE(party.hasQuestBit(90450));
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, row(2)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.gold(), 2500);
    CHECK(party.hasQuestBit(90029));
    CHECK_EQ(party.hirelings().size(), 3u);
}

TEST_CASE("MM9 hire without the fee leaves the party as it was")
{
    Party party = makeParty(499);
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::NotEnoughGold);
    CHECK_EQ(party.gold(), 499);
    CHECK(party.hirelings().empty());
    CHECK_FALSE(party.hasQuestBit(90451));
}

TEST_CASE("MM9 dismissal always clears the hire key, so the retainer can be hired again")
{
    Party party = makeParty(2000);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    CHECK(OpenYAMM::Game::dismissMm9Hireling(party, row(43)));
    CHECK(party.hirelings().empty());
    CHECK_FALSE(party.hasQuestBit(90451));
    CHECK_FALSE(OpenYAMM::Game::dismissMm9Hireling(party, row(43)));
    // Rehiring charges the fee again.
    CHECK(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.gold(), 1000);
}

TEST_CASE("MM9 healer service heals every member and hireling once per 24 game hours")
{
    Party party = makeParty(5000);
    party.setGameMinutes(10.0f * MinutesPerDay);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(238)) == Mm9HireOutcome::Hired);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    party.combatant(0)->health = 10;
    party.combatant(1)->health = -5;
    party.combatant(1)->conditions.set(size_t(CharacterCondition::Unconscious));
    party.combatant(2)->conditions.set(size_t(CharacterCondition::PoisonWeak));
    party.combatant(3)->conditions.set(size_t(CharacterCondition::Dead));
    party.combatant(3)->health = 0;
    // Tesar knocked out at 0 HP.
    party.applyDamageToMember(5, 1000, "");
    REQUIRE(party.combatant(5)->conditions.test(size_t(CharacterCondition::Unconscious)));

    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(238)) == Mm9HirelingServiceOutcome::Healed);
    CHECK_EQ(party.combatant(0)->health, party.reachableMaximumHealth(0));
    CHECK_EQ(party.combatant(1)->health, party.reachableMaximumHealth(1));
    CHECK_FALSE(party.combatant(1)->conditions.test(size_t(CharacterCondition::Unconscious)));
    CHECK_EQ(party.combatant(5)->health, 110);
    CHECK_FALSE(party.combatant(5)->conditions.test(size_t(CharacterCondition::Unconscious)));
    // Sowelu cures nothing (cshell@0x1002b03d), and the dead stay dead.
    CHECK(party.combatant(2)->conditions.test(size_t(CharacterCondition::PoisonWeak)));
    CHECK(party.combatant(3)->conditions.test(size_t(CharacterCondition::Dead)));
    CHECK_EQ(party.combatant(3)->health, 0);

    party.combatant(0)->health = 10;
    party.setGameMinutes(10.0f * MinutesPerDay + 23.0f * 60.0f);
    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(238)) == Mm9HirelingServiceOutcome::CoolingDown);
    CHECK_EQ(party.combatant(0)->health, 10);
    CHECK_EQ(OpenYAMM::Game::mm9HirelingServiceCooldownText("Sowelu Axeldotir"),
        "Sowelu Axeldotir can cast this but once per day!");

    // The cooldown is saved with the hireling.
    Party restored = {};
    restored.restoreSnapshot(party.snapshot());
    restored.setMm9HirelingTable(&worldTable());
    restored.setGameMinutes(10.0f * MinutesPerDay + 23.0f * 60.0f);
    CHECK(OpenYAMM::Game::useMm9HirelingService(restored, row(238)) == Mm9HirelingServiceOutcome::CoolingDown);
    restored.setGameMinutes(11.0f * MinutesPerDay);
    CHECK(OpenYAMM::Game::useMm9HirelingService(restored, row(238)) == Mm9HirelingServiceOutcome::Healed);
}

TEST_CASE("MM9 Florie heals and cures her conditions; services need the hireling along")
{
    Party party = makeParty(5000);
    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(308)) == Mm9HirelingServiceOutcome::Unavailable);
    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(43)) == Mm9HirelingServiceOutcome::Unavailable);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(308)) == Mm9HireOutcome::Hired);
    party.combatant(0)->conditions.set(size_t(CharacterCondition::PoisonSevere));
    party.combatant(1)->conditions.set(size_t(CharacterCondition::Cursed));
    party.combatant(2)->conditions.set(size_t(CharacterCondition::Insane));
    party.combatant(3)->conditions.set(size_t(CharacterCondition::Weak));
    party.combatant(4)->conditions.set(size_t(CharacterCondition::DiseaseMedium));

    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(308)) == Mm9HirelingServiceOutcome::Healed);
    CHECK_FALSE(party.combatant(0)->conditions.test(size_t(CharacterCondition::PoisonSevere)));
    CHECK_FALSE(party.combatant(1)->conditions.test(size_t(CharacterCondition::Cursed)));
    CHECK_FALSE(party.combatant(2)->conditions.test(size_t(CharacterCondition::Insane)));
    CHECK_FALSE(party.combatant(4)->conditions.test(size_t(CharacterCondition::DiseaseMedium)));
    // Weak is not one of hers (cshell@0x1002b17c: Cursed, Diseased, Insane, Poisoned).
    CHECK(party.combatant(3)->conditions.test(size_t(CharacterCondition::Weak)));
}

TEST_CASE("MM9 Ehwaz's Town Portal starts his cooldown")
{
    Party party = makeParty(5000);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(179)) == Mm9HireOutcome::Hired);
    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(179)) == Mm9HirelingServiceOutcome::TownPortal);
    CHECK(party.findHireling(179)->serviceReadyGameMinutes == doctest::Approx(party.gameMinutes() + MinutesPerDay));
    CHECK(OpenYAMM::Game::useMm9HirelingService(party, row(179)) == Mm9HirelingServiceOutcome::CoolingDown);
}

TEST_CASE("MM9 Edina adds 20 percent to found gold and Cleirach 10 percent to experience")
{
    Party party = makeParty(5000);
    CHECK_EQ(OpenYAMM::Game::resolveFoundGold(1000, nullptr, &party).partyAmount, 1000u);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(126)) == Mm9HireOutcome::Hired);
    const OpenYAMM::Game::FoundGold found = OpenYAMM::Game::resolveFoundGold(1000, nullptr, &party);
    CHECK_EQ(found.amount, 1200u);
    // MM9's gold share is never deducted (section 5).
    CHECK_EQ(found.partyAmount, 1200u);

    const uint64_t before = party.member(0)->experience;
    CHECK_EQ(party.grantSharedExperience(4000), 4000u);
    CHECK_EQ(party.member(0)->experience - before, 1000u);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(281)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.grantSharedExperience(4000), 4400u);
    CHECK_EQ(party.member(0)->experience - before, 2100u);
}

TEST_CASE("MM9 Cleirach identifies and Alvar repairs without the skill")
{
    Party party = makeParty(5000);
    OpenYAMM::Game::ItemDefinition item = {};
    item.equipStat = "Weapon";
    CHECK_FALSE(party.canIdentifyItem(item));
    CHECK_FALSE(party.canRepairItem(item));

    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(281)) == Mm9HireOutcome::Hired);
    CHECK(party.canIdentifyItem(item));
    CHECK_FALSE(party.canRepairItem(item));
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(178)) == Mm9HireOutcome::Hired);
    CHECK(party.canRepairItem(item));
    REQUIRE(OpenYAMM::Game::dismissMm9Hireling(party, row(281)));
    CHECK_FALSE(party.canIdentifyItem(item));
}

TEST_CASE("MM9 Alberik and Beagan raise skills the members already have")
{
    Party party = makeParty(5000);
    party.member(0)->skills["Merchant"] = CharacterSkill{"Merchant", 3, SkillMastery::Normal};
    party.member(1)->skills["Perception"] = CharacterSkill{"Perception", 2, SkillMastery::Normal};

    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(177)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.member(0)->skillBonus("Merchant"), 6);
    CHECK_EQ(party.member(1)->skillBonus("Merchant"), 0);

    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(125)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.member(1)->skillBonus("Perception"), 4);
    CHECK_EQ(party.member(1)->skillBonus("DisarmTraps"), 0);
    CHECK_EQ(party.member(0)->skillBonus("Perception"), 0);

    REQUIRE(OpenYAMM::Game::dismissMm9Hireling(party, row(177)));
    CHECK_EQ(party.member(0)->skillBonus("Merchant"), 0);
    CHECK_EQ(party.member(1)->skillBonus("Perception"), 4);
}

TEST_CASE("MM9 wages come due every 28 days from the hire")
{
    Party party = makeParty(5000);
    party.setGameMinutes(MinutesPerDay);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    REQUIRE_EQ(party.gold(), 4500);

    party.setGameMinutes(28.0f * MinutesPerDay);
    CHECK(OpenYAMM::Game::payMm9HirelingWages(party, worldTable()).empty());
    CHECK_EQ(party.gold(), 4500);

    party.setGameMinutes(29.0f * MinutesPerDay);
    CHECK(OpenYAMM::Game::payMm9HirelingWages(party, worldTable()).empty());
    CHECK_EQ(party.gold(), 4000);
    CHECK(party.findHireling(43)->nextWageGameMinutes == doctest::Approx(57.0f * MinutesPerDay));

    // Two periods passed at once (a long voyage): both wages.
    party.setGameMinutes(86.0f * MinutesPerDay);
    CHECK(OpenYAMM::Game::payMm9HirelingWages(party, worldTable()).empty());
    CHECK_EQ(party.gold(), 3000);
    CHECK_FALSE(spoke(party, SpeechId::NotEnoughGold));
}

TEST_CASE("MM9 unpaid wage empties the purse and that retainer leaves, in MM9's order")
{
    Party party = makeParty(5000);
    // Edina (row 285) hired before Tesar (280); both wages fall due at once, MM9 pays Tesar first.
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(126)) == Mm9HireOutcome::Hired);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    party.addGold(600 - party.gold());
    party.clearPendingAudioRequests();

    party.setGameMinutes(Party::Mm9HirelingWagePeriodGameMinutes + 1.0f);
    const std::vector<uint32_t> departed = OpenYAMM::Game::payMm9HirelingWages(party, worldTable());
    REQUIRE_EQ(departed.size(), 1u);
    CHECK_EQ(departed[0], 126u);
    CHECK_EQ(party.gold(), 0);
    CHECK(party.findHireling(126) == nullptr);
    CHECK(party.findHireling(43) != nullptr);
    // Unlike MM9, the key goes, so Edina can be hired again.
    CHECK_FALSE(party.hasQuestBit(90456));
    CHECK(party.hasQuestBit(90451));
    CHECK(spoke(party, SpeechId::NotEnoughGold));
}

TEST_CASE("MM9 story companions join free, take no wage, and come and go by script")
{
    Party party = makeParty(100);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(2)) == Mm9HireOutcome::Hired);
    CHECK_EQ(party.gold(), 100);
    party.setGameMinutes(200.0f * MinutesPerDay);
    CHECK(OpenYAMM::Game::payMm9HirelingWages(party, worldTable()).empty());
    CHECK_EQ(party.gold(), 100);
    CHECK(party.findHireling(2) != nullptr);

    // Forad leaves at the council by script (RemoveNPC 2): key 29 stays, as in MM9.
    CHECK(party.removeHireling(2));
    CHECK(party.hasQuestBit(90029));
    // Tamur joins by script (AddNPC 309) even beside two paid retainers.
    party.addGold(5000);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(43)) == Mm9HireOutcome::Hired);
    REQUIRE(OpenYAMM::Game::hireMm9Hireling(party, row(126)) == Mm9HireOutcome::Hired);
    CHECK(party.addHirelingByRudeId(309));
    CHECK_EQ(party.hirelings().size(), 3u);
    CHECK_FALSE(party.addHirelingByRudeId(253));
}

TEST_CASE("MAW scales MM9's hirelings to the party's level and keeps paid ones away from Doom up")
{
    using OpenYAMM::Game::MawClassRules;
    using OpenYAMM::Game::MawMapLevels;
    using OpenYAMM::Game::MawRules;
    using OpenYAMM::Game::RulesetChallengeMode;
    using OpenYAMM::Game::RulesetOptions;

    const Mm9Hireling *pHrolf = worldTable().find(42);
    REQUIRE(pHrolf != nullptr);
    Party party = makeParty(5000);
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    party.setRules(&rules.gameRules());
    REQUIRE_EQ(OpenYAMM::Game::hireMm9Hireling(party, *pHrolf), Mm9HireOutcome::Hired);
    const auto &classes = dynamic_cast<const MawClassRules &>(rules.gameRules().classes);

    // A party below the row's level leaves the hireling as the row has it.
    for (size_t index = 0; index < party.members().size(); ++index)
    {
        party.member(index)->level = 5;
    }
    classes.scaleHirelings(party);
    const OpenYAMM::Game::Mm9PartyHireling *pHireling = party.findHireling(42);
    REQUIRE(pHireling != nullptr);
    CHECK_EQ(pHireling->character.level, pHrolf->level);
    CHECK_EQ(pHireling->character.maxHealth, pHrolf->hitPoints);
    CHECK(pHireling->rulesDamageScale == doctest::Approx(1.0f));

    // At the party's level it keeps its share of MAW's expected character: more damage, health and armour, the
    // health it had kept as a share.
    party.findHireling(42)->character.health = pHrolf->hitPoints / 2;
    for (size_t index = 0; index < party.members().size(); ++index)
    {
        party.member(index)->level = uint32_t(pHrolf->level + 30);
    }
    classes.scaleHirelings(party);
    CHECK_EQ(pHireling->character.level, pHrolf->level + 30);
    CHECK(pHireling->character.maxHealth > pHrolf->hitPoints);
    CHECK(pHireling->character.health * 2 == doctest::Approx(pHireling->character.maxHealth).epsilon(0.02));
    CHECK(pHireling->character.armorClassModifier > pHrolf->armorClass);
    CHECK(pHireling->rulesDamageScale > 1.2f);

    // Doom and up: paid retainers refuse, story companions join.
    RulesetOptions doom;
    doom.challengeMode = RulesetChallengeMode::Doom;
    MawRules doomRules(doom, MawMapLevels{});
    Party doomParty = makeParty(5000);
    doomParty.setRules(&doomRules.gameRules());
    CHECK_EQ(OpenYAMM::Game::hireMm9Hireling(doomParty, *pHrolf), Mm9HireOutcome::Declines);
    const Mm9Hireling *pForad = worldTable().find(2);
    REQUIRE(pForad != nullptr);
    CHECK_EQ(OpenYAMM::Game::hireMm9Hireling(doomParty, *pForad), Mm9HireOutcome::Hired);
}
