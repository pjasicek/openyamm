#include "game/rules/maw/MawDimensionMaps.h"

#include "game/items/ItemRulesetFields.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawCombatFormulas.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <exception>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
MawAffixKind affixKindNamed(const std::string &name)
{
    if (name == "flat")
    {
        return MawAffixKind::Flat;
    }

    if (name == "proc")
    {
        return MawAffixKind::Proc;
    }

    if (name == "reduction")
    {
        return MawAffixKind::Reduction;
    }

    throw std::runtime_error("unknown affix kind '" + name + "'");
}

// A value as MAW prints it: up to two decimals, no trailing zeros.
std::string formatAffixValue(double value)
{
    char buffer[32];
    std::snprintf(buffer, sizeof(buffer), "%.2f", value);
    std::string text = buffer;

    while (!text.empty() && text.back() == '0')
    {
        text.pop_back();
    }

    if (!text.empty() && text.back() == '.')
    {
        text.pop_back();
    }

    return text;
}
}

MawDimensionMap MawDimensionMap::fromFields(const ItemRulesetFields &fields)
{
    MawDimensionMap map;
    map.mapId = fields.dimensionMapId;
    map.affixes = fields.dimensionAffixes;
    map.activeSlots = fields.dimensionActiveSlots;
    map.power = fields.dimensionPower;
    return map;
}

void MawDimensionMap::writeFields(ItemRulesetFields &fields) const
{
    fields.dimensionMapId = mapId;
    fields.dimensionAffixes = affixes;
    fields.dimensionActiveSlots = activeSlots;
    fields.dimensionPower = power;
}

std::array<uint8_t, 4> MawDimensionMap::activeAffixes() const
{
    const size_t slots = activeSlots == 0 ? 4 : std::min<size_t>(activeSlots, 4);
    std::array<uint8_t, 4> active = {};

    for (size_t slot = 0; slot < slots; ++slot)
    {
        active[slot] = affixes[slot];
    }

    return active;
}

int MawDimensionMap::activeAffixCount() const
{
    const std::array<uint8_t, 4> active = activeAffixes();
    return int(std::count_if(active.begin(), active.end(), [](uint8_t affix) { return affix != 0; }));
}

bool MawDimensionData::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        m_mapItemId = root["map_item"].as<uint32_t>();
        m_dungeons = root["dungeons"].as<std::vector<uint16_t>>();
        m_indoorFamilies = root["families_indoor"].as<std::vector<int16_t>>();
        m_outdoorFamilies = root["families_outdoor"].as<std::vector<int16_t>>();

        const YAML::Node drop = root["drop"];
        m_dropChance = drop["chance"].as<double>();
        m_dropLevelRequired = drop["level_required"].as<int>();
        m_bossDropMultiplier = drop["boss_multiplier"].as<double>();

        const YAML::Node quest = root["quest"];
        m_quest.firstTier = quest["first_tier"].as<int>();
        m_quest.unlockTier = quest["unlock_tier"].as<int>();

        m_quest.firstStep = quest["first_step"].as<int>();
        m_quest.lastStep = quest["last_step"].as<int>();

        m_quest.textTooLow = quest["text_too_low"].as<std::string>();
        m_quest.textGive = quest["text_give"].as<std::string>();
        m_quest.textNotCleared = quest["text_not_cleared"].as<std::string>();
        m_quest.textReward = quest["text_reward"].as<std::string>();

        const YAML::Node affixes = root["affixes"];
        m_affixes.assign(affixes.size(), {});

        for (const auto &entry : affixes)
        {
            const int affixId = entry.first.as<int>();

            if (affixId < 1 || affixId > int(m_affixes.size()))
            {
                throw std::runtime_error("affix ids must run from 1 without gaps");
            }

            MawDimensionAffix &affix = m_affixes[size_t(affixId - 1)];
            affix.text = entry.second["text"].as<std::string>();
            affix.base = entry.second["base"].as<double>();
            affix.scale = entry.second["scale"].as<double>();
            affix.kind = affixKindNamed(entry.second["kind"].as<std::string>());
        }

        if (m_dungeons.empty() || m_indoorFamilies.empty() || m_outdoorFamilies.empty() || m_affixes.size() < 4)
        {
            throw std::runtime_error("needs dungeons, both family lists and at least four affixes");
        }
    }
    catch (const std::exception &error)
    {
        errorMessage = error.what();
        return false;
    }

    return true;
}

uint32_t MawDimensionData::mapItemId() const
{
    return m_mapItemId;
}

const std::vector<uint16_t> &MawDimensionData::dungeons() const
{
    return m_dungeons;
}

const std::vector<int16_t> &MawDimensionData::families(bool indoor) const
{
    return indoor ? m_indoorFamilies : m_outdoorFamilies;
}

const MawDimensionAffix *MawDimensionData::affix(int affixId) const
{
    return affixId >= 1 && affixId <= int(m_affixes.size()) ? &m_affixes[size_t(affixId - 1)] : nullptr;
}

int MawDimensionData::affixCount() const
{
    return int(m_affixes.size());
}

std::optional<double> MawDimensionData::affixValue(int affixId, int power) const
{
    const MawDimensionAffix *pAffix = affix(affixId);

    if (pAffix == nullptr)
    {
        return std::nullopt;
    }

    const double value = pAffix->base + power * pAffix->scale;

    switch (pAffix->kind)
    {
        case MawAffixKind::Reduction:
            return mawRound((1 - 1 / (value / 100 + 1)) * 10000) / 100;
        case MawAffixKind::Proc:
            return std::min(value, 100.0);
        case MawAffixKind::Flat:
            break;
    }

    return value;
}

std::string MawDimensionData::affixLine(int affixId, int power) const
{
    const MawDimensionAffix *pAffix = affix(affixId);
    const std::optional<double> value = affixValue(affixId, power);

    if (pAffix == nullptr || !value)
    {
        return {};
    }

    std::string line = pAffix->text;
    const size_t placeholder = line.find("{X}");

    if (placeholder != std::string::npos)
    {
        line.replace(placeholder, 3, formatAffixValue(*value));
    }

    return line;
}

double MawDimensionData::dropChance() const
{
    return m_dropChance;
}

int MawDimensionData::dropLevelRequired() const
{
    return m_dropLevelRequired;
}

double MawDimensionData::bossDropMultiplier() const
{
    return m_bossDropMultiplier;
}

const MawDimensionQuestRules &MawDimensionData::quest() const
{
    return m_quest;
}

int MawDimensionData::nextQuestTier(int tier) const
{
    int next = m_quest.firstTier;
    int step = std::max(m_quest.firstStep, 1);

    while (next <= tier)
    {
        next += step;
        step = std::max(step - 1, std::max(m_quest.lastStep, 1));
    }

    return next;
}

std::array<uint8_t, 4> MawDimensionData::rollAffixes(RandomStream &stream, const std::array<bool, 4> &slots) const
{
    std::array<uint8_t, 4> affixes = {};
    std::vector<uint8_t> pool;

    for (int affixId = 1; affixId <= affixCount(); ++affixId)
    {
        pool.push_back(uint8_t(affixId));
    }

    // MAW draws affix 2, then 3, then 4, then 1, each unlike the ones before.
    for (const size_t slot : {size_t(1), size_t(2), size_t(3), size_t(0)})
    {
        if (!slots[slot] || pool.empty())
        {
            continue;
        }

        const size_t pick = stream.uniform(0, uint32_t(pool.size() - 1));
        affixes[slot] = pool[pick];
        pool.erase(pool.begin() + std::ptrdiff_t(pick));
    }

    return affixes;
}

double mawDimensionStrength(int power, int activeAffixes)
{
    return double(power + 20) * activeAffixes;
}

int mawDimensionMapLevel(int power, const std::array<double, 3> &band)
{
    return power * 10 + 20 + int(mawRound((band[0] + band[1] + band[2]) / 3));
}
}
