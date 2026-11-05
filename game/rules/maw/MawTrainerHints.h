#pragma once

#include "game/gameplay/TrainerDirectory.h"
#include "game/party/SkillData.h"
#include "game/rules/maw/MawSkillFormulas.h"

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ClassSkillTable;
class MapStats;
class MawRules;
class Party;
struct Character;

// MAW's trainer hints (TrainerHint.lua, devdocs/maw/UPSTREAM_SYNC_8fbb48d1.md §7): who teaches the next mastery of a
// skill and where, appended to the skill popup while the "Trainer hints" preference is on. The teachers and their
// ranking are the shared TrainerDirectory's; a hint names only teachers the party knows (trainerKnown: the teacher's
// note, or the continent's Ledger of Teachers). The texts here are pure.

enum class MawTrainerHintKind : uint8_t
{
    // The next mastery and its nearest teachers ("No trainer found." for none).
    Trainers,
    None,
    // Learned without a teacher at a skill level (a ladder, or a party of one's utility skills).
    Automatic,
    // The class reaches the mastery only after a promotion; trainers is empty for none, unset for a ladder skill.
    Promotion,
    // Neither the class nor its promotions reach the next mastery.
    ClassMaximum,
    Grandmaster,
};

struct MawTrainerHintInfo
{
    MawTrainerHintKind kind = MawTrainerHintKind::None;
    SkillMastery nextMastery = SkillMastery::None;
    uint32_t requiredLevel = 0;
    uint32_t level = 0;
    std::optional<uint32_t> currentContinent;
    std::optional<std::vector<PickedTrainer>> trainers;
    // The next mastery has teachers, but none the party knows yet.
    bool unknownTrainers = false;
};

// The hint's text with MAW's colour tags (mawFillText turns them into colour codes): the heading <value> (yellow), the
// required level <good> when the base level reaches it and <bad> when not, "(this map)" and "(outside)" <good>.
std::string mawComposeTrainerHint(const MawTrainerHintInfo &info);

// What the hint is about: a character's skill and where the party stands.
struct MawTrainerHintQuery
{
    std::string skill;
    uint32_t level = 0;
    SkillMastery mastery = SkillMastery::None;
    // The best mastery the class reaches now and after its promotions.
    SkillMastery classCap = SkillMastery::None;
    SkillMastery promotionCap = SkillMastery::None;
    // The base level a teacher wants for the next mastery.
    uint32_t requiredLevel = 0;
    // The levels at which the skill becomes Expert, Master and Grandmaster without a teacher (MAW's ladders).
    std::optional<std::array<uint32_t, 3>> ladder;
    // A party of one masters this skill by level alone.
    bool soloMastery = false;
    std::optional<uint32_t> currentMap;
    std::optional<uint32_t> currentContinent;
    // Indoors: the outdoor map the party came from.
    std::optional<uint32_t> referenceMap;
    TrainerNeighbours neighbours;
    // Whether the party knows a teacher (empty: every teacher is named).
    std::function<bool(const TrainerEntry &)> known;
};

// The hint for a skill (TrainerHint.explain), or nothing: an unlearned skill, a skill nobody teaches and no ladder
// grants.
std::optional<MawTrainerHintInfo> mawExplainTrainerHint(
    const TrainerDirectory &directory,
    const MawTrainerHintQuery &query);

// The session's tables the hints read, kept by MawRules; the teachers come from the party's TrainerDirectory.
struct MawTrainerHints
{
    const ClassSkillTable *pClassSkillTable = nullptr;
    const MapStats *pMapStats = nullptr;
};

// The hint block of a party member's skill popup with its colour codes, or empty: the preference off, no map yet
// (party creation), no trainer directory, or nothing to say. `mode` picks the ladders' row.
std::string mawTrainerHintText(
    const MawRules &rules,
    const Party &party,
    const Character &character,
    const std::string &canonicalSkill,
    MawSkillMode mode);
}
