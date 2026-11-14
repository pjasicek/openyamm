#include "game/rules/SoloTalents.h"

#include "engine/Localization.h"
#include "game/party/Party.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
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

std::optional<TalentTree> parseTree(const std::string &text)
{
    if (text == "melee")
    {
        return TalentTree::Melee;
    }
    if (text == "ranged")
    {
        return TalentTree::Ranged;
    }
    if (text == "caster")
    {
        return TalentTree::Caster;
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
        m_levelsPerPoint = std::max(1u, root["levels_per_point"].as<uint32_t>(10));
        for (const YAML::Node &node : root["talents"])
        {
            TalentDefinition talent;
            talent.id = node["id"].as<std::string>();
            talent.name = node["name"].as<std::string>(talent.id);
            talent.text = node["text"].as<std::string>("");
            const std::optional<TalentTree> tree = parseTree(node["tree"].as<std::string>(""));
            if (!tree)
            {
                error = "talent " + talent.id + ": tree must be melee, ranged or caster";
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
            talent.maxRank = std::clamp(node["max_rank"].as<int>(1), 1, 9);
            talent.iconItem = node["icon_item"].as<std::string>("");
            talent.iconSpell = node["icon_spell"].as<uint32_t>(0);
            const std::string requirement = node["requires"].as<std::string>("none");
            talent.requirement = requirement == "master" ? TalentRequirement::Master
                : requirement == "expert"                ? TalentRequirement::Expert
                                                         : TalentRequirement::None;
            talent.perRank = node["per_rank"].as<float>(0.0f);
            talent.cooldown = node["cooldown"].as<float>(0.0f);
            talent.cooldownPerRank = node["cooldown_per_rank"].as<float>(0.0f);
            talent.duration = node["duration"].as<float>(0.0f);
            talent.durationPerRank = node["duration_per_rank"].as<float>(0.0f);
            talent.targets = node["targets"].as<int>(0);
            talent.share = node["share"].as<float>(100.0f);
            talent.distance = node["distance"].as<float>(0.0f);
            talent.arc = node["arc"].as<float>(0.0f);
            if (find(talent.id) != nullptr)
            {
                error = "talent " + talent.id + " is listed twice";
                return false;
            }
            m_talents.push_back(std::move(talent));
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

int talentPointsSpent(const Character &character)
{
    int spent = 0;
    for (const auto &[id, rank] : character.talentRanks)
    {
        spent += rank;
    }
    return spent;
}

int talentPointsAvailable(const SoloTalentTable &table, const Character &character)
{
    return std::max(0, talentPointsTotal(table, character) - talentPointsSpent(character));
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
        case TalentTree::Melee:
            return bestMastery(character, MeleeSkills);
        case TalentTree::Ranged:
            return bestMastery(character, RangedSkills);
        case TalentTree::Caster:
            return bestMastery(character, CasterSkills);
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
        const std::string skill = talent.tree == TalentTree::Melee ? Engine::tr("a melee weapon or Armsmaster")
            : talent.tree == TalentTree::Ranged                     ? Engine::tr("Bow")
                                                                    : Engine::tr("a magic school");
        return Engine::tr("Needs {skill} at {mastery}", {{"skill", skill}, {"mastery", mastery}});
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
    uint8_t &rank = character.talentRanks[pTalent->id];
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

float talentCooldownSeconds(const TalentDefinition &talent, int rank)
{
    return std::max(1.0f, talent.cooldown + talent.cooldownPerRank * float(std::max(rank, 1) - 1));
}

float talentDurationSeconds(const TalentDefinition &talent, int rank)
{
    return std::max(0.0f, talent.duration + talent.durationPerRank * float(std::max(rank, 1) - 1));
}

float talentValue(const TalentDefinition &talent, int rank)
{
    if (talent.kind == TalentKind::Active)
    {
        return talent.durationPerRank != 0.0f ? talentDurationSeconds(talent, rank) : talent.perRank;
    }
    return talent.perRank * float(rank);
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
