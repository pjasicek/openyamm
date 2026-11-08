#include "doctest/doctest.h"

#include "game/mm9/Mm9SkillTrainer.h"

#include <string>
#include <vector>

namespace
{
std::string rudeRow()
{
    std::vector<std::string> columns(30, "0");
    columns[0] = "80";
    columns[1] = "80";
    columns[2] = "1";
    columns[3] = "Become Expert in Blade";
    columns[4] = "Ready?";
    columns[5] = "-4";
    columns[15] = "2006";
    std::string result;
    for (size_t index = 0; index < columns.size(); ++index)
    {
        if (index != 0)
        {
            result += ',';
        }
        result += columns[index];
    }
    return result + '\n';
}

std::vector<std::string> header()
{
    return {
        "CanonicalId", "RudeId", "RudeRowIndex", "SourceLine", "ChoiceSlot", "RawTrainerId",
        "Mm9Skill", "SharedSkills", "TargetMastery", "RequiredSkillRank", "RequiredGold",
        "RequiredRawKeys", "ForbiddenRawKeys", "ExpectedRegion", "SourceDisplayNames", "Npc998Hint",
        "ActorOwnership", "ActorSources", "SourceRude", "Provenance",
    };
}

std::vector<std::string> row()
{
    return {
        "mm9:trainer/80/1", "80", "0", "1", "1", "2006", "Blade", "Sword|Dagger|Axe", "Expert", "4", "0",
        "", "", "Sturmford", "Katrina Vianni", "Katrina Vianni of Sturmford teaches Blade.", "static",
        "assets_dev/worlds/mm9/maps/sturmfordcity.scene.yml", "NPC80.rude", "rude:-4+npc998_crosscheck",
    };
}
}

TEST_CASE("MM9 skill trainer table binds separate-skill services to authoritative RUDE rows")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC80.rude", rudeRow()));
    OpenYAMM::Game::Mm9SkillTrainerTable table;
    REQUIRE(table.loadFromRows({header(), row()}, rudeTable));
    CHECK(table.errors().empty());

    const OpenYAMM::Game::Mm9SkillTrainerService *pService = table.find(80, 0);
    REQUIRE(pService != nullptr);
    CHECK(pService->canonicalId == "mm9:trainer/80/1");
    CHECK(pService->mm9Skill == "Blade");
    CHECK(pService->topic.targetMastery == OpenYAMM::Game::SkillMastery::Expert);
    CHECK((pService->topic.skillNames == std::vector<std::string>{"Sword", "Dagger", "Axe"}));
    CHECK_EQ(pService->requiredSkillRank, 4);
}

TEST_CASE("MM9 skill trainer table rejects stale RUDE row ownership")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC80.rude", rudeRow()));
    std::vector<std::string> stale = row();
    stale[3] = "2";
    OpenYAMM::Game::Mm9SkillTrainerTable table;

    CHECK_FALSE(table.loadFromRows({header(), stale}, rudeTable));
    REQUIRE_EQ(table.errors().size(), 1);
    CHECK(table.errors().front().find("authoritative RUDE row") != std::string::npos);
}

TEST_CASE("MM9 skill trainer table rejects unknown and repeated skills")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText("NPC80.rude", rudeRow()));

    for (const std::string &skills : {std::string("Sword|Blade"), std::string("Sword|Dagger|Sword")})
    {
        std::vector<std::string> invalid = row();
        invalid[7] = skills;
        OpenYAMM::Game::Mm9SkillTrainerTable table;

        CHECK_FALSE(table.loadFromRows({header(), invalid}, rudeTable));
        REQUIRE_EQ(table.errors().size(), 1);
        CHECK(table.errors().front().find("distinct canonical OpenYAMM skills") != std::string::npos);
    }
}
