#include "game/rules/SoloTalents.h"

#include "engine/Localization.h"
#include "game/party/Party.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
const SoloTalentTable *g_pSoloTalentTable = nullptr;

// The skills behind each tree. Melee takes the best melee weapon skill or Armsmaster (not only the weapon in hand, so
// switching weapons does not take actives away); caster the best magic school.
constexpr std::array<const char *, 8> MeleeSkills = {
    "Sword", "Axe", "Mace", "Dagger", "Spear", "Staff", "Unarmed", "Armsmaster"};
constexpr std::array<const char *, 1> RangedSkills = {"Bow"};
constexpr std::array<const char *, 9> CasterSkills = {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic",
    "SpiritMagic", "MindMagic", "BodyMagic", "LightMagic", "DarkMagic"};

template <size_t N>
int bestMastery(const Character &character, const std::array<const char *, N> &skills)
{
    int best = 0;
    for (const char *pSkill : skills)
    {
        if (const CharacterSkill *pLearned = character.findSkill(pSkill); pLearned != nullptr && pLearned->level > 0)
        {
            best = std::max(best, int(pLearned->mastery));
        }
    }
    return best;
}

// The tree's best trained skill level (base level, not item bonuses).
template <size_t N>
int bestLevel(const Character &character, const std::array<const char *, N> &skills)
{
    int best = 0;
    for (const char *pSkill : skills)
    {
        if (const CharacterSkill *pLearned = character.findSkill(pSkill); pLearned != nullptr)
        {
            best = std::max(best, int(pLearned->level));
        }
    }
    return best;
}

std::optional<TalentTree> parseTree(const std::string &text)
{
    if (text == "arms")
    {
        return TalentTree::Arms;
    }
    if (text == "archery")
    {
        return TalentTree::Archery;
    }
    if (text == "arcana")
    {
        return TalentTree::Arcana;
    }
    if (text == "any")
    {
        return TalentTree::Any;
    }
    return std::nullopt;
}

std::string formatNumber(float value)
{
    std::ostringstream stream;
    const float rounded = std::round(value * 10.0f) / 10.0f;
    if (rounded == std::floor(rounded))
    {
        stream << int(rounded);
    }
    else
    {
        stream << rounded;
    }
    return stream.str();
}
}

bool SoloTalentTable::loadFromYaml(const std::string &text, std::string &error)
{
    m_talents.clear();
    try
    {
        const YAML::Node root = YAML::Load(text);
        m_levelsPerPoint = std::max(1u, root["levels_per_point"].as<uint32_t>(15));
        m_keystones.clear();
        m_keystoneLevels.clear();
        for (const YAML::Node &level : root["keystone_levels"])
        {
            m_keystoneLevels.push_back(level.as<uint32_t>());
        }
        std::sort(m_keystoneLevels.begin(), m_keystoneLevels.end());
        m_earlyMonsterCut.clear();
        for (const YAML::Node &point : root["early_monster_cut"])
        {
            if (!point.IsSequence() || point.size() != 2 || point[1].as<double>() < 1.0)
            {
                error = "early_monster_cut takes [level, divisor] pairs with a divisor of 1 or more";
                return false;
            }
            m_earlyMonsterCut.emplace_back(point[0].as<double>(), point[1].as<double>());
        }
        std::sort(m_earlyMonsterCut.begin(), m_earlyMonsterCut.end());
        m_experienceSurcharge.reset();
        if (root["experience_surcharge"])
        {
            m_experienceSurcharge = root["experience_surcharge"].as<double>();
            if (*m_experienceSurcharge < 0)
            {
                error = "experience_surcharge cannot be negative";
                return false;
            }
        }
        for (const YAML::Node &node : root["keystones"])
        {
            TalentDefinition keystone;
            keystone.id = node["id"].as<std::string>();
            keystone.name = node["name"].as<std::string>(keystone.id);
            keystone.text = node["text"].as<std::string>("");
            keystone.tree = TalentTree::Any;
            keystone.iconItem = node["icon_item"].as<std::string>("");
            keystone.iconSpell = node["icon_spell"].as<uint32_t>(0);
            keystone.cooldown = node["cooldown"].as<float>(0.0f);
            keystone.duration = node["duration"].as<float>(0.0f);
            if (findKeystone(keystone.id) != nullptr)
            {
                error = "keystone " + keystone.id + " is listed twice";
                return false;
            }
            m_keystones.push_back(std::move(keystone));
        }
        for (const YAML::Node &node : root["talents"])
        {
            TalentDefinition talent;
            talent.id = node["id"].as<std::string>();
            talent.name = node["name"].as<std::string>(talent.id);
            talent.text = node["text"].as<std::string>("");
            const std::optional<TalentTree> tree = parseTree(node["tree"].as<std::string>(""));
            if (!tree)
            {
                error = "talent " + talent.id + ": tree must be arms, archery, arcana or any";
                return false;
            }
            talent.tree = *tree;
            const std::string kind = node["kind"].as<std::string>("passive");
            if (kind != "passive" && kind != "active")
            {
                error = "talent " + talent.id + ": kind must be passive or active";
                return false;
            }
            talent.kind = kind == "active" ? TalentKind::Active : TalentKind::Passive;
            talent.unlimitedRanks = node["max_rank"].as<std::string>("") == "unlimited";
            talent.maxRank = talent.unlimitedRanks ? int(std::numeric_limits<uint16_t>::max())
                                                   : std::clamp(node["max_rank"].as<int>(1), 1, 50);
            talent.iconItem = node["icon_item"].as<std::string>("");
            talent.iconSpell = node["icon_spell"].as<uint32_t>(0);
            const std::string requirement = node["requires"].as<std::string>("none");
            talent.requirement = requirement == "master" ? TalentRequirement::Master
                : requirement == "expert"                ? TalentRequirement::Expert
                                                         : TalentRequirement::None;
            talent.needs = node["needs"].as<std::string>("");
            talent.perRank = node["per_rank"].as<float>(0.0f);
            if (node["first_rank"])
            {
                talent.firstRank = node["first_rank"].as<float>();
            }
            talent.perRankCalm = node["per_rank_calm"].as<float>(0.0f);
            talent.cooldown = node["cooldown"].as<float>(0.0f);
            talent.cooldownPerRank = node["cooldown_per_rank"].as<float>(0.0f);
            talent.cooldownPerAttack = node["cooldown_per_attack"].as<float>(0.0f);
            talent.cooldownPerHit = node["cooldown_per_hit"].as<float>(0.0f);
            talent.cooldownPerCritical = node["cooldown_per_crit"].as<float>(0.0f);
            talent.duration = node["duration"].as<float>(0.0f);
            talent.durationPerRank = node["duration_per_rank"].as<float>(0.0f);
            talent.targets = node["targets"].as<int>(0);
            talent.share = node["share"].as<float>(100.0f);
            talent.sharePerSkill = node["share_per_skill"].as<float>(0.0f);
            talent.shareCap = node["share_cap"].as<float>(0.0f);
            talent.shareByRank.clear();
            for (const YAML::Node &share : node["share_by_rank"])
            {
                talent.shareByRank.push_back(share.as<float>());
            }
            if (!talent.shareByRank.empty() && int(talent.shareByRank.size()) != talent.maxRank)
            {
                error = "talent " + talent.id + ": share_by_rank needs one share per rank";
                return false;
            }
            talent.distance = node["distance"].as<float>(0.0f);
            talent.arc = node["arc"].as<float>(0.0f);
            talent.recovery = node["recovery"].as<float>(100.0f);
            if (talent.recovery <= 0.0f)
            {
                error = "talent " + talent.id + ": recovery must be above 0";
                return false;
            }
            if (find(talent.id) != nullptr || findKeystone(talent.id) != nullptr)
            {
                error = "talent " + talent.id + " is listed twice";
                return false;
            }
            m_talents.push_back(std::move(talent));
        }
        for (const TalentDefinition &talent : m_talents)
        {
            if (!talent.needs.empty() && find(talent.needs) == nullptr)
            {
                error = "talent " + talent.id + " needs " + talent.needs + ", which is not in the table";
                return false;
            }
        }
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        return false;
    }
    return true;
}

const std::vector<TalentDefinition> &SoloTalentTable::talents() const
{
    return m_talents;
}

const TalentDefinition *SoloTalentTable::find(std::string_view id) const
{
    const auto found = std::find_if(m_talents.begin(), m_talents.end(),
        [id](const TalentDefinition &talent) { return talent.id == id; });
    return found != m_talents.end() ? &*found : nullptr;
}

uint32_t SoloTalentTable::levelsPerPoint() const
{
    return m_levelsPerPoint;
}

const std::vector<TalentDefinition> &SoloTalentTable::keystones() const
{
    return m_keystones;
}

const TalentDefinition *SoloTalentTable::findKeystone(std::string_view id) const
{
    const auto found = std::find_if(m_keystones.begin(), m_keystones.end(),
        [id](const TalentDefinition &keystone) { return keystone.id == id; });
    return found != m_keystones.end() ? &*found : nullptr;
}

const std::vector<uint32_t> &SoloTalentTable::keystoneLevels() const
{
    return m_keystoneLevels;
}

std::optional<double> SoloTalentTable::experienceSurcharge() const
{
    return m_experienceSurcharge;
}

double SoloTalentTable::earlyMonsterCut(double level) const
{
    if (m_earlyMonsterCut.empty())
    {
        return 1.0;
    }

    if (level <= m_earlyMonsterCut.front().first)
    {
        return m_earlyMonsterCut.front().second;
    }

    for (size_t index = 1; index < m_earlyMonsterCut.size(); ++index)
    {
        const std::pair<double, double> &from = m_earlyMonsterCut[index - 1];
        const std::pair<double, double> &to = m_earlyMonsterCut[index];

        if (level <= to.first)
        {
            return from.second + (to.second - from.second) * (level - from.first) / (to.first - from.first);
        }
    }

    // Past the table the cut is over, whatever its last value.
    return 1.0;
}

const SoloTalentTable &soloTalentTable()
{
    static const SoloTalentTable Empty;
    return g_pSoloTalentTable != nullptr ? *g_pSoloTalentTable : Empty;
}

void bindSoloTalentTable(const SoloTalentTable *pTable)
{
    g_pSoloTalentTable = pTable;
}

bool soloTalentsActive(const RulesetSelection &ruleset)
{
    return ruleset.options.soloRun && ruleset.id == "maw";
}

int talentRank(const Character &character, std::string_view id)
{
    const auto found = character.talentRanks.find(std::string(id));
    return found != character.talentRanks.end() ? int(found->second) : 0;
}

int talentPointsTotal(const SoloTalentTable &table, const Character &character)
{
    return int(character.level / table.levelsPerPoint());
}

int talentPointsSpent(const SoloTalentTable &table, const Character &character)
{
    int spent = 0;
    for (const auto &[id, rank] : character.talentRanks)
    {
        if (table.find(id) != nullptr)
        {
            spent += rank;
        }
    }
    return spent;
}

int talentPointsAvailable(const SoloTalentTable &table, const Character &character)
{
    return std::max(0, talentPointsTotal(table, character) - talentPointsSpent(table, character));
}

uint32_t nextTalentPointLevel(const SoloTalentTable &table, const Character &character)
{
    const uint32_t step = table.levelsPerPoint();
    return (character.level / step + 1) * step;
}

int talentTreeMastery(const Character &character, TalentTree tree)
{
    switch (tree)
    {
        case TalentTree::Arms:
            return bestMastery(character, MeleeSkills);
        case TalentTree::Archery:
            return bestMastery(character, RangedSkills);
        case TalentTree::Arcana:
            return bestMastery(character, CasterSkills);
        case TalentTree::Any:
            return int(SkillMastery::Grandmaster);
    }
    return 0;
}

std::string talentLearnRefusal(const SoloTalentTable &table, const Character &character, const TalentDefinition &talent)
{
    if (talentRank(character, talent.id) >= talent.maxRank)
    {
        return Engine::tr("Fully learned");
    }
    const int needed = talent.requirement == TalentRequirement::Master ? int(SkillMastery::Master)
        : talent.requirement == TalentRequirement::Expert              ? int(SkillMastery::Expert)
                                                                       : 0;
    if (needed > 0 && talentTreeMastery(character, talent.tree) < needed)
    {
        const std::string mastery = needed == int(SkillMastery::Master) ? Engine::tr("Master") : Engine::tr("Expert");
        const std::string skill = talent.tree == TalentTree::Arms ? Engine::tr("a melee weapon or Armsmaster")
            : talent.tree == TalentTree::Archery                     ? Engine::tr("Bow")
                                                                     : Engine::tr("a magic school");
        return Engine::tr("Needs {skill} at {mastery}", {{"skill", skill}, {"mastery", mastery}});
    }
    if (!talent.needs.empty() && talentRank(character, talent.needs) <= 0)
    {
        const TalentDefinition *pNeeded = table.find(talent.needs);
        return Engine::tr("Needs {talent} first",
            {{"talent", pNeeded != nullptr ? Engine::tr(pNeeded->name) : talent.needs}});
    }
    if (talentPointsAvailable(table, character) <= 0)
    {
        return Engine::tr("No talent points: the next comes at level {level}",
            {{"level", int64_t(nextTalentPointLevel(table, character))}});
    }
    return {};
}

bool learnTalent(const SoloTalentTable &table, Character &character, std::string_view id)
{
    const TalentDefinition *pTalent = table.find(id);
    if (pTalent == nullptr || !talentLearnRefusal(table, character, *pTalent).empty())
    {
        return false;
    }
    uint16_t &rank = character.talentRanks[pTalent->id];
    ++rank;
    if (rank == 1 && pTalent->kind == TalentKind::Active)
    {
        // A new active goes on the first free key of the main row (1-0), unless it is already on the bar.
        const uint32_t talentIndex = uint32_t(pTalent - table.talents().data());
        const bool placed = std::any_of(character.actionBar.begin(), character.actionBar.end(),
            [talentIndex](const ActionBarSlot &slot)
            { return slot.kind == ActionBarSlotKind::Talent && slot.id == talentIndex; });
        for (size_t slot = 0; !placed && slot < ActionBarSlotCount / 2; ++slot)
        {
            if (character.actionBar[slot].kind == ActionBarSlotKind::Empty)
            {
                character.actionBar[slot] = {ActionBarSlotKind::Talent, talentIndex, {}};
                break;
            }
        }
    }
    return true;
}

void resetTalents(Character &character)
{
    character.talentRanks.clear();
    character.talentState = {};
    for (ActionBarSlot &slot : character.actionBar)
    {
        if (slot.kind == ActionBarSlotKind::Talent)
        {
            slot = {};
        }
    }
}

int keystoneSlots(const SoloTalentTable &table, const Character &character)
{
    return int(std::count_if(table.keystoneLevels().begin(), table.keystoneLevels().end(),
        [&character](uint32_t level) { return character.level >= level; }));
}

int keystonesBound(const SoloTalentTable &table, const Character &character)
{
    return int(std::count_if(table.keystones().begin(), table.keystones().end(),
        [&character](const TalentDefinition &keystone) { return hasKeystone(character, keystone.id); }));
}

void endMapTalentEffects(Character &character)
{
    character.talentState.onslaughtStacks = 0;
    character.talentState.onslaughtSeconds = 0.0f;
}

bool hasKeystone(const Character &character, std::string_view id)
{
    return talentRank(character, id) > 0;
}

std::string keystoneBindRefusal(const SoloTalentTable &table, const Character &character, const TalentDefinition &keystone)
{
    if (hasKeystone(character, keystone.id))
    {
        return Engine::tr("Bound");
    }
    if (keystonesBound(table, character) >= keystoneSlots(table, character))
    {
        const uint32_t next = nextKeystoneLevel(table, character);
        return next > 0 ? Engine::tr("No open keystone slot: the next opens at level {level}", {{"level", int64_t(next)}})
                        : Engine::tr("No open keystone slot");
    }
    return {};
}

bool bindKeystone(const SoloTalentTable &table, Character &character, std::string_view id)
{
    const TalentDefinition *pKeystone = table.findKeystone(id);
    if (pKeystone == nullptr || !keystoneBindRefusal(table, character, *pKeystone).empty())
    {
        return false;
    }
    character.talentRanks[pKeystone->id] = 1;
    return true;
}

uint32_t nextKeystoneLevel(const SoloTalentTable &table, const Character &character)
{
    for (const uint32_t level : table.keystoneLevels())
    {
        if (character.level < level)
        {
            return level;
        }
    }
    return 0;
}

float talentSkillShare(const TalentDefinition &talent, const Character &character)
{
    const int skill = talent.tree == TalentTree::Archery ? bestLevel(character, RangedSkills)
        : talent.tree == TalentTree::Arcana              ? bestLevel(character, CasterSkills)
                                                         : bestLevel(character, MeleeSkills);
    float percent = talent.share + talent.sharePerSkill * float(skill);
    if (talent.shareCap > 0.0f)
    {
        percent = std::min(percent, talent.shareCap);
    }
    return std::max(0.0f, percent) / 100.0f;
}

float talentCooldownSeconds(const TalentDefinition &talent, int rank)
{
    return std::max(1.0f, talent.cooldown + talent.cooldownPerRank * float(std::max(rank, 1) - 1));
}

float talentCooldownRemaining(const Character &character, std::string_view id)
{
    const auto found = character.talentState.cooldownSeconds.find(std::string(id));
    return found != character.talentState.cooldownSeconds.end() ? std::max(0.0f, found->second) : 0.0f;
}

void shortenTalentCooldowns(const SoloTalentTable &table, Character &character, bool hit)
{
    for (const TalentDefinition &talent : table.talents())
    {
        const float seconds = hit ? talent.cooldownPerHit : talent.cooldownPerAttack;
        const auto found = character.talentState.cooldownSeconds.find(talent.id);

        if (seconds > 0.0f && found != character.talentState.cooldownSeconds.end())
        {
            found->second = std::max(0.0f, found->second - seconds);
        }
    }
}

void shortenTalentCooldownsOnCritical(const SoloTalentTable &table, Character &character)
{
    for (const TalentDefinition &talent : table.talents())
    {
        const auto found = character.talentState.cooldownSeconds.find(talent.id);

        if (talent.cooldownPerCritical > 0.0f && found != character.talentState.cooldownSeconds.end())
        {
            found->second = std::max(0.0f, found->second - talent.cooldownPerCritical);
        }
    }
}

float talentDurationSeconds(const TalentDefinition &talent, int rank)
{
    return std::max(0.0f, talent.duration + talent.durationPerRank * float(std::max(rank, 1) - 1));
}

float talentValue(const TalentDefinition &talent, int rank)
{
    if (talent.kind == TalentKind::Active)
    {
        return !talent.shareByRank.empty()      ? talentShareAtRank(talent, rank) * 100.0f
            : talent.durationPerRank != 0.0f ? talentDurationSeconds(talent, rank)
                                             : talent.perRank;
    }
    if (talent.firstRank && rank > 0)
    {
        return *talent.firstRank + talent.perRank * float(rank - 1);
    }
    return talent.perRank * float(rank);
}

float talentShareAtRank(const TalentDefinition &talent, int rank)
{
    const float percent = talent.shareByRank.empty()
        ? talent.share
        : talent.shareByRank[size_t(std::clamp(rank, 1, int(talent.shareByRank.size())) - 1)];
    return std::max(0.0f, percent) / 100.0f;
}

std::string talentEffectText(const TalentDefinition &talent, int rank)
{
    return Engine::tr(talent.text, {{"value", formatNumber(talentValue(talent, std::max(rank, 1)))}});
}

std::vector<size_t> pickTalentTargets(const std::vector<TalentTargetCandidate> &candidates, float partyX, float partyY,
    float partyZ, float yawRadians, float reach, float arcDegrees, size_t maxCount)
{
    constexpr float Pi = 3.14159265358979f;
    std::vector<std::pair<float, size_t>> inReach;
    for (const TalentTargetCandidate &candidate : candidates)
    {
        if (!candidate.usable)
        {
            continue;
        }
        const float dx = candidate.x - partyX;
        const float dy = candidate.y - partyY;
        const float dz = candidate.z - partyZ;
        const float distance = std::max(0.0f, std::sqrt(dx * dx + dy * dy + dz * dz) - candidate.radius);
        if (distance > reach)
        {
            continue;
        }
        if (arcDegrees < 180.0f && (dx != 0.0f || dy != 0.0f))
        {
            float difference = std::atan2(dy, dx) - yawRadians;
            while (difference > Pi)
            {
                difference -= 2 * Pi;
            }
            while (difference < -Pi)
            {
                difference += 2 * Pi;
            }
            if (std::abs(difference) > arcDegrees * Pi / 180.0f)
            {
                continue;
            }
        }
        inReach.emplace_back(distance, candidate.index);
    }
    std::sort(inReach.begin(), inReach.end());
    std::vector<size_t> picked;
    for (const auto &[distance, index] : inReach)
    {
        if (picked.size() >= maxCount)
        {
            break;
        }
        picked.push_back(index);
    }
    return picked;
}
}
