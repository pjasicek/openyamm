#pragma once

#include "game/content/RulesetOptions.h"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
struct Character;
class Party;

// The special skills (talents) of an augmented solo run under MAW (devdocs/solo_action/TALENTS.md): the table read
// from engine data_tables/talents.yml, the point economy and the locks. The talents' effects live in the MAW rules
// (passives) and in game/gameplay/SoloTalentActions (actives); nothing here changes a rule by itself.
// What a tree trains (talent tree v2, devdocs/solo_action/TALENT_TREE_V2_BUILD.md): weapon fighting, the bow (never a
// dragon's breath), spells, and the few talents of any tree.
enum class TalentTree : uint8_t
{
    Arms,
    Archery,
    Arcana,
    Any,
};

enum class TalentKind : uint8_t
{
    Passive,
    Active,
};

enum class TalentRequirement : uint8_t
{
    None,
    Expert,
    Master,
};

struct TalentDefinition
{
    std::string id;
    std::string name;
    std::string text;
    TalentTree tree = TalentTree::Arms;
    TalentKind kind = TalentKind::Passive;
    int maxRank = 1;
    std::string iconItem;
    uint32_t iconSpell = 0;
    TalentRequirement requirement = TalentRequirement::None;
    // Another talent that must have a rank first (empty: none).
    std::string needs;
    float perRank = 0.0f;
    // A passive's value per rank out of combat (no yellow alert); 0 when it has none.
    float perRankCalm = 0.0f;
    float cooldown = 0.0f;
    float cooldownPerRank = 0.0f;
    float duration = 0.0f;
    float durationPerRank = 0.0f;
    int targets = 0;
    float share = 100.0f;
    // Percent added to `share` per point of the tree's weapon skill, and the share's ceiling (0: none).
    float sharePerSkill = 0.0f;
    float shareCap = 0.0f;
    float distance = 0.0f;
    float arc = 0.0f;
};

class SoloTalentTable
{
public:
    bool loadFromYaml(const std::string &text, std::string &error);
    const std::vector<TalentDefinition> &talents() const;
    const TalentDefinition *find(std::string_view id) const;
    uint32_t levelsPerPoint() const;
    // The keystones (no points, one per open slot) and the levels at which their slots open.
    const std::vector<TalentDefinition> &keystones() const;
    const TalentDefinition *findKeystone(std::string_view id) const;
    const std::vector<uint32_t> &keystoneLevels() const;

private:
    std::vector<TalentDefinition> m_talents;
    std::vector<TalentDefinition> m_keystones;
    std::vector<uint32_t> m_keystoneLevels;
    uint32_t m_levelsPerPoint = 15;
};

// The loaded table the rules and screens read; an empty table when none is bound (tools, tests without one).
const SoloTalentTable &soloTalentTable();
void bindSoloTalentTable(const SoloTalentTable *pTable);

// Talents exist only in an augmented solo run under MAW.
bool soloTalentsActive(const RulesetSelection &ruleset);

int talentRank(const Character &character, std::string_view id);
// One point per `levelsPerPoint` levels; the character's own level, not item or spell bonuses.
int talentPointsTotal(const SoloTalentTable &table, const Character &character);
// Ranks of the table's talents only: keystones cost nothing, and a talent no longer in the table gives its points back.
int talentPointsSpent(const SoloTalentTable &table, const Character &character);
int talentPointsAvailable(const SoloTalentTable &table, const Character &character);
// The level at which the next point comes.
uint32_t nextTalentPointLevel(const SoloTalentTable &table, const Character &character);

// Why a rank cannot be learned now (empty: it can): no points, the last rank, or the tree's skill below the mastery.
std::string talentLearnRefusal(const SoloTalentTable &table, const Character &character, const TalentDefinition &talent);
// Learns the next rank; false (and nothing changed) when refused. A newly learned active goes on the first free slot
// of the action bar's main row.
bool learnTalent(const SoloTalentTable &table, Character &character, std::string_view id);
// Forgets every rank and keystone (respec at a trainer); the bar's talent slots are cleared.
void resetTalents(Character &character);

// Keystones: a slot opens at each of the table's keystone levels; a bound keystone is kept as rank 1 under its id.
int keystoneSlots(const SoloTalentTable &table, const Character &character);
int keystonesBound(const SoloTalentTable &table, const Character &character);
bool hasKeystone(const Character &character, std::string_view id);
// Why the keystone cannot be bound now (empty: it can): already bound, or no open slot.
std::string keystoneBindRefusal(const SoloTalentTable &table, const Character &character, const TalentDefinition &keystone);
bool bindKeystone(const SoloTalentTable &table, Character &character, std::string_view id);
// The level at which the next keystone slot opens (0: none left).
uint32_t nextKeystoneLevel(const SoloTalentTable &table, const Character &character);

// A share that grows with the tree's weapon skill (Sweeping Blows, Piercing Arrows), as a fraction: share +
// share_per_skill x skill, at most share_cap.
float talentSkillShare(const TalentDefinition &talent, const Character &character);

// The tree's skill: the mastery that gates its actives (0: none, 1 Normal ... 4 Grandmaster).
int talentTreeMastery(const Character &character, TalentTree tree);

// A rank's numbers: the cooldown and the duration (seconds), and a passive's value.
float talentCooldownSeconds(const TalentDefinition &talent, int rank);
float talentDurationSeconds(const TalentDefinition &talent, int rank);
float talentValue(const TalentDefinition &talent, int rank);

// The effect line with the rank's number in it.
std::string talentEffectText(const TalentDefinition &talent, int rank);

// A monster a sweeping talent may strike: where it stands, its body radius, and whether it is a living hostile.
struct TalentTargetCandidate
{
    size_t index = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float radius = 0.0f;
    bool usable = false;
};

// Cleave, Sweeping Blows, Multishot and Piercing Arrows pick their targets: the usable monsters whose body is within `reach` of the party and
// whose centre lies within `arcDegrees` either side of the view (180: all around), nearest first, at most `maxCount`.
std::vector<size_t> pickTalentTargets(const std::vector<TalentTargetCandidate> &candidates, float partyX, float partyY,
    float partyZ, float yawRadians, float reach, float arcDegrees, size_t maxCount);
}
