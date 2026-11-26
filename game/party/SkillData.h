#pragma once

#include <cstdint>
#include <map>
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

// The skill sheet's groups. Skills outside the listed groups are shown under Misc.
enum class SkillSheetGroup
{
    Weapons,
    Magic,
    Armor,
    Misc,
    Technology,
};

// Skill ids: the 40 classic MM skills keep their MMerge ids 0-39; the technology skills (Energy Guns, Energy
// Blades, Shield Tech, Hacking) follow from this id. Technology skills have no class caps and are raised with tech
// points instead of skill points.
constexpr uint32_t FirstTechnologySkillId = 40;
// MAW's skills (Cover, Mana Shield, Enlightenment, Retaliation) follow the technology skills. Only a ruleset's class
// table gives them caps, so Standard characters never learn them.
constexpr uint32_t FirstRulesetSkillId = 44;
// Implants (Hesper's implant sockets; once the technology skill Cybernetics, `cybernetics` is its alias) came after
// MAW's skills had their ids. An ordinary skill raised with skill points; every class can reach Grandmaster, but only a
// script teaches it (the Archive of the Eaten), so no class card or mercenary lists it (isTaughtOnlySkill).
constexpr uint32_t ImplantsSkillId = 48;

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
// The active ruleset's names for skills it shows differently (MAW: Learning is Ascension); empty for Standard.
void setSkillDisplayNameOverrides(const std::map<std::string, std::string> &displayNames);
std::string masteryDisplayName(SkillMastery mastery);
// Every skill in id order, the technology skills last.
std::vector<std::string> allCanonicalSkillNames();
std::optional<std::string> skillNameForSkillId(uint32_t skillId);
std::optional<uint32_t> skillIdForSkillName(const std::string &skillName);
bool isTechnologySkill(const std::string &skillName);
bool isRulesetSkill(const std::string &skillName);
// Skills no class lists among the skills it can learn (class cards, mercenaries, debug grants): the technology skills
// and Implants. A character who has one still shows it on the skill sheet.
bool isTaughtOnlySkill(const std::string &skillName);
// Hesper's Implants exist in the game only while a mounted world provides the `implants` table (ItemTable): the data
// load sets it once. Without it nothing shows, teaches or lists the skill, the sockets or the overlay (a save's sockets
// and skill are kept, unseen).
void setImplantsAvailable(bool available);
bool implantsAvailable();
// Every skill but Implants while implants are not available.
bool skillAvailable(const std::string &skillName);
const std::vector<std::string> &skillSheetGroupSkillNames(SkillSheetGroup group);
std::optional<std::string> nextPromotionClassName(const std::string &className);
std::vector<std::string> promotionClassNames(const std::string &className);
std::optional<uint32_t> mm8ClassIdForClassName(const std::string &className);
std::optional<std::string> classNameForMm8ClassId(uint32_t classId);
SkillMastery parseSkillMasteryToken(const std::string &token);
StartingSkillAvailability parseStartingSkillAvailabilityToken(const std::string &token);
}
