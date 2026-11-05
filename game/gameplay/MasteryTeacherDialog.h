#pragma once

#include "game/tables/ClassSkillTable.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class NpcDialogTable;
class Party;
class MergedTeacherTopicTable;

struct MasteryTeacherEvaluation
{
    bool approved = false;
    std::string displayText;
    std::string skillName;
    SkillMastery targetMastery = SkillMastery::None;
    int cost = 0;
};

struct MasteryTeacherTopicDefinition
{
    uint32_t topicId = 0;
    uint32_t skillId = 0;
    uint32_t masteryRank = 0;
    uint32_t textId = 0;
    uint32_t requiredGold = 0;
    uint32_t requiredSkill = 0;
    std::string skillName;
    SkillMastery targetMastery = SkillMastery::None;
};

struct SkillMasteryTrainingRequest
{
    std::string skillName;
    SkillMastery targetMastery = SkillMastery::None;
    uint32_t requiredGold = 0;
    uint32_t requiredSkill = 0;
};

struct SkillMasteryGroupTrainingRequest
{
    std::string displayName;
    std::vector<std::string> skillNames;
    SkillMastery targetMastery = SkillMastery::None;
    uint32_t requiredGold = 0;
    uint32_t requiredSkill = 0;
};

std::optional<MasteryTeacherTopicDefinition> resolveMasteryTeacherTopic(
    uint32_t topicId,
    const MergedTeacherTopicTable *pTeacherTopicTable
);
// A teacher's price for a mastery when its topic names none (before the ruleset's SkillRules::masteryTeacherCost).
int masteryTeacherStandardCost(const std::string &skillName, SkillMastery targetMastery);
bool isMasteryTeacherTopic(
    uint32_t topicId,
    const MergedTeacherTopicTable *pTeacherTopicTable
);
std::optional<MasteryTeacherEvaluation> evaluateSkillMasteryTraining(
    const SkillMasteryTrainingRequest &request,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable
);
bool applySkillMasteryTraining(
    const SkillMasteryTrainingRequest &request,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    std::string &message
);
std::optional<MasteryTeacherEvaluation> evaluateSkillMasteryGroupTraining(
    const SkillMasteryGroupTrainingRequest &request,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable
);
bool applySkillMasteryGroupTraining(
    const SkillMasteryGroupTrainingRequest &request,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    std::string &message
);
std::optional<MasteryTeacherEvaluation> evaluateMasteryTeacherTopic(
    uint32_t topicId,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    const MergedTeacherTopicTable *pTeacherTopicTable = nullptr
);
bool applyMasteryTeacherTopic(
    uint32_t topicId,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    const MergedTeacherTopicTable *pTeacherTopicTable,
    std::string &message
);
}
