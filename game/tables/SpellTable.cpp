#include "game/tables/SpellTable.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeName(std::string value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char &character : value)
    {
        if (std::isspace(static_cast<unsigned char>(character)) != 0)
        {
            if (!normalized.empty() && normalized.back() != ' ')
            {
                normalized.push_back(' ');
            }

            continue;
        }

        if (character == '-' && !normalized.empty() && normalized.back() == ' ')
        {
            normalized.pop_back();
        }

        normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    if (!normalized.empty() && normalized.back() == ' ')
    {
        normalized.pop_back();
    }

    return normalized;
}

std::string compactName(const std::string &value)
{
    std::string compacted;
    compacted.reserve(value.size());

    for (unsigned char character : value)
    {
        if (std::isalnum(character) != 0)
        {
            compacted.push_back(static_cast<char>(std::tolower(character)));
        }
    }

    return compacted;
}

std::string canonicalLegacySpellAlias(const std::string &normalizedName)
{
    if (normalizedName == "day-o-gods" || normalizedName == "day o gods")
    {
        return "day of the gods";
    }

    if (normalizedName == "psychic shockt")
    {
        return "psychic shock";
    }

    return normalizedName;
}

bool isNumericString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

int intCell(const std::vector<std::string> &row, size_t column, int fallback)
{
    return row.size() > column && !row[column].empty() ? std::stoi(row[column]) : fallback;
}

int scaledDamage(int value, int percent)
{
    return (value * percent + 50) / 100;
}
}

SpellMasteryNumbers spellNumbersAtMastery(const SpellEntry &entry, SkillMastery mastery)
{
    const size_t index = mastery == SkillMastery::Grandmaster ? 3
        : mastery == SkillMastery::Master                     ? 2
        : mastery == SkillMastery::Expert                     ? 1
                                                              : 0;
    const std::array<int, 4> manaCosts = {
        entry.normalManaCost, entry.expertManaCost, entry.masterManaCost, entry.grandmasterManaCost};
    const std::array<int, 4> recoveryTicks = {
        entry.normalRecoveryTicks, entry.expertRecoveryTicks, entry.masterRecoveryTicks,
        entry.grandmasterRecoveryTicks};
    const int percent = entry.damagePercents[index];
    const bool fixed = entry.damageDiceMin == entry.damageDiceSides;
    SpellMasteryNumbers numbers = {};
    numbers.manaCost = std::max(0, manaCosts[index]);
    numbers.recoveryTicks = recoveryTicks[index];
    numbers.damageBase = scaledDamage(entry.damageBase, percent);
    numbers.damageDiceMax = scaledDamage(std::max(entry.damageDiceMin, entry.damageDiceSides), percent);
    numbers.damageDiceMin = fixed ? numbers.damageDiceMax : entry.damageDiceMin;
    numbers.projectileCount = std::max<uint32_t>(1, entry.projectileCounts[index]);
    return numbers;
}

bool SpellTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndexById.clear();
    m_entryIndexByNormalizedName.clear();
    m_shadowedEntryIndicesByName.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 6 || !isNumericString(row[0]))
        {
            continue;
        }

        SpellEntry entry = {};
        entry.id = std::stoi(row[0]);
        entry.name = row[2];
        entry.normalizedName = canonicalLegacySpellAlias(normalizeName(entry.name));
        entry.schoolName = row.size() > 3 ? row[3] : "";
        entry.shortName = row.size() > 4 ? row[4] : "";
        entry.description = row.size() > 5 ? row[5] : "";
        entry.normalText = row.size() > 6 ? row[6] : "";
        entry.expertText = row.size() > 7 ? row[7] : "";
        entry.masterText = row.size() > 8 ? row[8] : "";
        entry.grandmasterText = row.size() > 9 ? row[9] : "";
        entry.statsText = row.size() > 10 ? row[10] : "";
        entry.normalManaCost = row.size() > 11 && !row[11].empty() ? std::stoi(row[11]) : 0;
        entry.expertManaCost = row.size() > 12 && !row[12].empty() ? std::stoi(row[12]) : 0;
        entry.masterManaCost = row.size() > 13 && !row[13].empty() ? std::stoi(row[13]) : 0;
        entry.grandmasterManaCost = row.size() > 14 && !row[14].empty() ? std::stoi(row[14]) : 0;
        entry.normalRecoveryTicks = row.size() > 15 && !row[15].empty() ? std::stoi(row[15]) : 0;
        entry.expertRecoveryTicks = row.size() > 16 && !row[16].empty() ? std::stoi(row[16]) : 0;
        entry.masterRecoveryTicks = row.size() > 17 && !row[17].empty() ? std::stoi(row[17]) : 0;
        entry.grandmasterRecoveryTicks = row.size() > 18 && !row[18].empty() ? std::stoi(row[18]) : 0;
        entry.effectSoundId = row.size() > 19 && !row[19].empty() ? std::stoi(row[19]) : 0;
        entry.displayObjectId = row.size() > 20 && !row[20].empty() ? std::stoi(row[20]) : 0;
        entry.impactDisplayObjectId = row.size() > 21 && !row[21].empty() ? std::stoi(row[21]) : 0;
        entry.damageBase = row.size() > 22 && !row[22].empty() ? std::stoi(row[22]) : 0;
        entry.damageDiceSides = row.size() > 23 && !row[23].empty() ? std::stoi(row[23]) : 0;
        entry.requiredMastery = row.size() > 24 ? parseSkillMasteryToken(row[24]) : SkillMastery::None;
        entry.requiredMastery = entry.requiredMastery == SkillMastery::None ? SkillMastery::Normal
                                                                            : entry.requiredMastery;
        entry.damageDiceMin = intCell(row, 25, 1);

        for (size_t index = 0; index < 4; ++index)
        {
            entry.projectileCounts[index] = static_cast<uint32_t>(std::max(1, intCell(row, 26 + index, 1)));
            entry.damagePercents[index] = intCell(row, 30 + index, 100);
        }

        m_entryIndexById[entry.id] = m_entries.size();

        for (const std::string &key : {entry.normalizedName, compactName(entry.name)})
        {
            const auto [entryIt, inserted] = m_entryIndexByNormalizedName.try_emplace(key, m_entries.size());

            if (!inserted && entryIt->second != m_entries.size())
            {
                m_shadowedEntryIndicesByName[key].push_back(entryIt->second);
                entryIt->second = m_entries.size();
            }
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const SpellEntry *SpellTable::findById(int id) const
{
    const auto entryIt = m_entryIndexById.find(id);

    if (entryIt == m_entryIndexById.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}

const SpellEntry *SpellTable::findByName(const std::string &name) const
{
    const std::string normalizedName = canonicalLegacySpellAlias(normalizeName(name));
    auto entryIt = m_entryIndexByNormalizedName.find(normalizedName);

    if (entryIt == m_entryIndexByNormalizedName.end())
    {
        entryIt = m_entryIndexByNormalizedName.find(compactName(name));
    }

    if (entryIt == m_entryIndexByNormalizedName.end())
    {
        return nullptr;
    }

    return &m_entries[entryIt->second];
}

const SpellEntry *SpellTable::findByName(
    const std::string &name,
    const std::function<bool(const SpellEntry &)> &prefer) const
{
    const SpellEntry *pEntry = findByName(name);

    if (pEntry == nullptr || prefer(*pEntry))
    {
        return pEntry;
    }

    for (const std::string &key : {canonicalLegacySpellAlias(normalizeName(name)), compactName(name)})
    {
        const auto shadowedIt = m_shadowedEntryIndicesByName.find(key);

        if (shadowedIt == m_shadowedEntryIndicesByName.end())
        {
            continue;
        }

        for (const size_t index : shadowedIt->second)
        {
            if (prefer(m_entries[index]))
            {
                return &m_entries[index];
            }
        }
    }

    return pEntry;
}

const std::vector<SpellEntry> &SpellTable::entries() const
{
    return m_entries;
}
}
