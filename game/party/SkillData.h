#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class SkillMastery
{
    None = 0,
    Normal = 1,
    Expert = 2,
    Master = 3,
    Grandmaster = 4,
};

enum class StartingSkillAvailability
{
    None,
    CanLearn,
    HasByDefault,
};

struct CharacterSkill
{
    std::string name;
    uint32_t level = 0;
    SkillMastery mastery = SkillMastery::None;
};

std::string canonicalClassName(const std::string &name);
std::string canonicalSkillName(const std::string &name);
std::string displayClassName(const std::string &className);
std::string displaySkillName(const std::string &skillName);
std::string masteryDisplayName(SkillMastery mastery);
std::vector<std::string> allCanonicalSkillNames();
std::optional<std::string> nextPromotionClassName(const std::string &className);
std::vector<std::string> promotionClassNames(const std::string &className);
std::optional<uint32_t> mm8ClassIdForClassName(const std::string &className);
std::optional<std::string> classNameForMm8ClassId(uint32_t classId);
SkillMastery parseSkillMasteryToken(const std::string &token);
StartingSkillAvailability parseStartingSkillAvailabilityToken(const std::string &token);
}
