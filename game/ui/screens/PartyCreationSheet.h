#pragma once

#include "game/party/SkillData.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ClassSkillTable;
struct CharacterDollEntry;
struct MergedRaceSkillOverride;

// Rules behind the party creation sheet (approach C2 of level_generation/ui/party_creation_study_20261101): what the
// skill list, race card and party board show. No drawing here.

// A skill for one adventurer: a fixed starting skill, one of the two choices (chosen or not), one a teacher can teach
// later (now or after a promotion), or one the class line never learns.
enum class CreationSkillState
{
    Fixed,
    Chosen,
    Option,
    Later,
    Never,
};

struct CreationSkillGroup
{
    std::string title;
    std::vector<std::string> skills;
};

// The sheet's skill groups in display order: weapons, armour (with a ruleset's Cover, Retaliation and Mana Shield),
// magic, the racial abilities and the rest.
const std::vector<CreationSkillGroup> &creationSkillGroups();

// The mastery a skill reaches now and the best it reaches through the class line's promotions.
struct CreationSkillReach
{
    SkillMastery now = SkillMastery::None;
    SkillMastery best = SkillMastery::None;
};

CreationSkillReach creationSkillReach(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill);

CreationSkillState creationSkillState(
    const std::vector<std::string> &fixedSkills,
    const std::vector<std::string> &optionalSkills,
    const std::vector<std::string> &chosenSkills,
    const CreationSkillReach &reach,
    const std::string &skill);

// Whether the race changes what the class line can reach in the skill (the skill's race tag).
bool creationRaceChangesSkill(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill);

// For a mastery level: 0 the class has it now, 1 a promotion brings it, 2 never.
int creationMasteryAvailability(
    const ClassSkillTable &table, const std::string &className, uint32_t raceId, const std::string &skill,
    SkillMastery mastery);

// The class line from a starting class: the class, then its first promotions, then the second ones (by class id).
std::vector<std::vector<std::string>> creationClassLine(const ClassSkillTable &table, const std::string &className);

// One line of the race card.
struct RaceCardLine
{
    enum class Kind
    {
        Even,
        Strong,
        Weak,
        Skill,
        Note,
    };

    Kind kind = Kind::Even;
    std::string text;
};

// A race's starting attributes: start value, maximum, the gain per bonus point and the bonus points per +1.
struct RaceStatLine
{
    int base = 11;
    int maximum = 25;
    int gainPerPoint = 1;
    int pointsPerGain = 1;
};

constexpr size_t CreationStatCount = 7;

// Might, Intellect, Personality, Endurance, Accuracy, Speed, Luck.
const std::array<const char *, CreationStatCount> &creationStatNames();

// The race card: attributes that differ from the even 1-for-1 rule (attributes alike share a line), the race's skill
// rules grouped by effect, then the ruleset's notes.
std::vector<RaceCardLine> raceCardLines(
    const std::array<RaceStatLine, CreationStatCount> &stats,
    const std::array<const char *, CreationStatCount> &statNames,
    const std::vector<MergedRaceSkillOverride> &raceSkillRules,
    uint32_t raceId,
    const ClassSkillTable &table,
    const std::vector<std::string> &notes);

// The marker shown for an attribute on the sheet: +1 when a bonus point buys more than 1, -1 when +1 costs more than
// a point, 0 otherwise; and its explanation.
int raceStatTrend(const RaceStatLine &stat);
std::string raceStatTrendText(const RaceStatLine &stat);

// One adventurer as the party board sees it.
struct CreationPartyMember
{
    std::string className;
    uint32_t raceId = 0;
    std::vector<std::string> fixedSkills;
    std::vector<std::string> optionalSkills;
    std::vector<std::string> chosenSkills;
};

// "Party covers N of M reachable skills · K to Grandmaster": skills some member reaches, those a member starts with,
// and of those the ones a member starting with them takes to Grandmaster.
struct CreationPartyCoverage
{
    size_t reachable = 0;
    size_t covered = 0;
    size_t grandmaster = 0;
};

CreationPartyCoverage creationPartyCoverage(const ClassSkillTable &table,
                                            const std::vector<CreationPartyMember> &members);

std::string portraitTextureNameForEntry(const CharacterDollEntry &entry);
// The class's menu icon; a class without an icon of its own shows the icon of the line it comes from.
std::string classIconTextureName(const std::string &className);
} // namespace OpenYAMM::Game
