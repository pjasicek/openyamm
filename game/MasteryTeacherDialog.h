#pragma once

#include "game/ClassSkillTable.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class NpcDialogTable;
class Party;

struct MasteryTeacherEvaluation
{
    bool approved = false;
    std::string displayText;
    std::string skillName;
    SkillMastery targetMastery = SkillMastery::None;
    int cost = 0;
};

bool tryDecodeMasteryTeacherTopicLabel(
    const std::string &topicLabel,
    std::string &skillName,
    SkillMastery &targetMastery
);
std::optional<MasteryTeacherEvaluation> evaluateMasteryTeacherTopic(
    uint32_t topicId,
    const Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable
);
bool applyMasteryTeacherTopic(
    uint32_t topicId,
    Party &party,
    const ClassSkillTable &classSkillTable,
    const NpcDialogTable &npcDialogTable,
    std::string &message
);
}
