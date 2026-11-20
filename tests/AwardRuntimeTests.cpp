#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/AwardRuntime.h"
#include "game/party/Party.h"
#include "game/tables/AwardTable.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace
{
constexpr uint32_t AutonoteVariableTag = 0x00E1u;

std::vector<std::vector<std::string>> parseRows(const std::string &text)
{
    const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text);
    REQUIRE(table.has_value());

    std::vector<std::vector<std::string>> rows;
    for (size_t index = 0; index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }
    return rows;
}

std::vector<std::vector<std::string>> loadEnglishTableRows(const char *pFileName)
{
    const std::filesystem::path path =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/data_tables/english" / pFileName;
    std::ifstream stream(path);
    REQUIRE(stream.is_open());

    std::ostringstream contents;
    contents << stream.rdbuf();
    return parseRows(contents.str());
}

bool hasVisibleAward(const std::vector<OpenYAMM::Game::VisibleAward> &awards, const std::string &key)
{
    return std::any_of(
        awards.begin(), awards.end(), [&key](const OpenYAMM::Game::VisibleAward &award) { return award.key == key; });
}
} // namespace

TEST_CASE("visible awards combine character awards with qbit and autonote aliases")
{
    OpenYAMM::Game::AwardTable table = {};
    REQUIRE(table.loadFromRows(
        {
            {"A Bit", "Awards", "Sort", "Notes"},
            {"18", "Stopped the Yellow Fever Epidemic", "3", ""},
            {"54", "Rescued Isthric", "3", ""},
        },
        {
            {"Key", "State", "State Id", "Text", "Sort", "Notes"},
            {"mm8.award.2", "party_autonote", "492", "Brought Power Stone", "3", ""},
            {"mm8.award.4", "party_autonote", "494", "Delivered Dadeross' Letter", "3", ""},
            {"mm8.award.51", "party_qbit", "1549", "Recovered Idol of the Snake", "3", ""},
            {"mm8.award.59", "party_qbit", "1552", "Brought the Anointed Herb Potion", "3", ""},
        }));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.addAward(0, 18);
    party.addAward(0, 54);
    party.setQuestBit(1549, true);
    party.setQuestBit(1552, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.variables[(492u << 16) | AutonoteVariableTag] = 1;
    runtimeState.variables[(494u << 16) | AutonoteVariableTag] = 1;

    const OpenYAMM::Game::Character *pCharacter = party.member(0);
    REQUIRE(pCharacter != nullptr);
    const std::vector<OpenYAMM::Game::VisibleAward> awards =
        OpenYAMM::Game::buildVisibleAwards(table, *pCharacter, party, [&runtimeState](uint32_t autonoteId) {
            const uint32_t variable = (autonoteId << 16) | AutonoteVariableTag;
            const auto iterator = runtimeState.variables.find(variable);
            return iterator != runtimeState.variables.end() && iterator->second != 0;
        });

    REQUIRE_EQ(awards.size(), 6u);
    CHECK(hasVisibleAward(awards, "award.18"));
    CHECK(hasVisibleAward(awards, "award.54"));
    CHECK(hasVisibleAward(awards, "mm8.award.2"));
    CHECK(hasVisibleAward(awards, "mm8.award.4"));
    CHECK(hasVisibleAward(awards, "mm8.award.51"));
    CHECK(hasVisibleAward(awards, "mm8.award.59"));
}

TEST_CASE("party award aliases are projected without changing character award bits")
{
    OpenYAMM::Game::AwardTable table = {};
    REQUIRE(table.loadFromRows({{"1", "Ordinary award", "2", ""}},
                               {{"mm8.award.51", "party_qbit", "1549", "Recovered Idol", "3", ""}}));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.setQuestBit(1549, true);

    const OpenYAMM::Game::Character *pCharacter = party.member(0);
    REQUIRE(pCharacter != nullptr);
    CHECK(pCharacter->awards.empty());
    CHECK_EQ(OpenYAMM::Game::visibleAwardCount(table, *pCharacter, party, {}), 1u);
    CHECK(pCharacter->awards.empty());
}

TEST_CASE("merged MM8 award aliases cover every displaced qbit and autonote award")
{
    OpenYAMM::Game::AwardTable table = {};
    REQUIRE(table.loadFromRows(loadEnglishTableRows("awards.txt"), loadEnglishTableRows("award_display_aliases.txt")));

    std::vector<uint32_t> qbitIds;
    std::vector<uint32_t> autonoteIds;

    for (const OpenYAMM::Game::AwardDisplayEntry &entry : table.entries())
    {
        if (entry.stateKind == OpenYAMM::Game::AwardStateKind::PartyQBit)
        {
            qbitIds.push_back(entry.stateId);
        }
        else if (entry.stateKind == OpenYAMM::Game::AwardStateKind::PartyAutonote)
        {
            autonoteIds.push_back(entry.stateId);
        }
    }

    REQUIRE_EQ(qbitIds.size(), 18u);
    REQUIRE_EQ(autonoteIds.size(), 13u);
    std::sort(qbitIds.begin(), qbitIds.end());
    std::sort(autonoteIds.begin(), autonoteIds.end());

    for (uint32_t qbitId = 1537; qbitId <= 1554; ++qbitId)
    {
        CHECK(std::binary_search(qbitIds.begin(), qbitIds.end(), qbitId));
    }

    for (uint32_t autonoteId = 492; autonoteId <= 504; ++autonoteId)
    {
        CHECK(std::binary_search(autonoteIds.begin(), autonoteIds.end(), autonoteId));
    }
}

TEST_CASE("MM7 tavern Arcomage wins show as awards and only one continent's taverns make a champion")
{
    OpenYAMM::Game::AwardTable table = {};
    REQUIRE(table.loadFromRows(loadEnglishTableRows("awards.txt"), loadEnglishTableRows("award_display_aliases.txt")));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    const OpenYAMM::Game::Character *pCharacter = party.member(0);
    REQUIRE(pCharacter != nullptr);

    party.recordArcomageWin(241, 0, 0);
    CHECK(hasVisibleAward(OpenYAMM::Game::buildVisibleAwards(table, *pCharacter, party, {}), "mm7.arcomage.241"));
    CHECK_FALSE(hasVisibleAward(OpenYAMM::Game::buildVisibleAwards(table, *pCharacter, party, {}), "mm7.arcomage.240"));

    // Eleven wins split between the continents are not a champion.
    for (uint32_t houseId = 228; houseId <= 232; ++houseId)
    {
        party.recordArcomageWin(houseId, 0, 0);
    }

    for (uint32_t houseId = 242; houseId <= 246; ++houseId)
    {
        party.recordArcomageWin(houseId, 0, 0);
    }

    CHECK_FALSE(pCharacter->awards.contains(41));

    for (uint32_t houseId = 233; houseId <= 238; ++houseId)
    {
        party.recordArcomageWin(houseId, 0, 0);
    }

    CHECK(pCharacter->awards.contains(41));
}
