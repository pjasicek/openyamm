#include "game/rules/maw/MawTexts.h"
#include "engine/Localization.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <type_traits>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<const char *, 4> MasteryKeys = {"normal", "expert", "master", "grandmaster"};

// Descriptions and mastery lines are read in the interface language, before the rules fill their {placeholders};
// names stay English: the rules compare them with the spell table's (devdocs/LOCALIZATION.md).
MawSpellTextEntry parseEntry(const YAML::Node &node)
{
    MawSpellTextEntry entry;

    if (node["name"])
    {
        entry.name = node["name"].as<std::string>();
    }

    if (node["description"])
    {
        entry.description = Engine::localize(node["description"].as<std::string>());
    }

    for (size_t mastery = 0; mastery < MasteryKeys.size(); ++mastery)
    {
        if (node[MasteryKeys[mastery]])
        {
            entry.masteryLines[mastery] = Engine::localize(node[MasteryKeys[mastery]].as<std::string>());
        }
    }

    return entry;
}

MawSkillTextEntry parseSkillEntry(const YAML::Node &node)
{
    MawSkillTextEntry entry;

    if (node["description"])
    {
        entry.description = Engine::localize(node["description"].as<std::string>());
    }

    if (node["append"])
    {
        entry.append = Engine::localize(node["append"].as<std::string>());
    }

    for (size_t mastery = 0; mastery < MasteryKeys.size(); ++mastery)
    {
        if (node[MasteryKeys[mastery]])
        {
            entry.masteryLines[mastery] = Engine::localize(node[MasteryKeys[mastery]].as<std::string>());
        }
    }

    return entry;
}

std::unordered_map<std::string, MawSkillTextEntry> parseSkills(const YAML::Node &node)
{
    std::unordered_map<std::string, MawSkillTextEntry> skills;

    for (const auto &item : node)
    {
        skills[item.first.as<std::string>()] = parseSkillEntry(item.second);
    }

    return skills;
}

std::unordered_map<uint32_t, MawSpellTextEntry> parseSpells(const YAML::Node &node)
{
    std::unordered_map<uint32_t, MawSpellTextEntry> spells;

    for (const auto &item : node)
    {
        spells[item.first.as<uint32_t>()] = parseEntry(item.second);
    }

    return spells;
}

template <typename T>
void overlay(std::optional<T> &target, const std::optional<T> &source)
{
    if (source)
    {
        target = source;
    }
}

// The colour tags texts may use, as Might and Magic's inline colour codes (R5G6B5, "\f00000" the line's own colour).
constexpr std::array<std::pair<const char *, const char *>, 5> ColorTags = {{
    {"<good>", "\f02016"},
    {"<bad>", "\f63488"},
    {"<value>", "\f65516"},
    {"<mana>", "\f23679"},
    {"</>", "\f00000"},
}};

std::string formatNumber(double value, int decimals)
{
    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "%.*f", decimals, value);
    std::string text = buffer;

    // "12.0" reads as "12", "2.10" as "2.1".
    if (decimals > 0)
    {
        while (text.ends_with("0"))
        {
            text.pop_back();
        }

        if (text.ends_with("."))
        {
            text.pop_back();
        }
    }

    return text;
}
}

bool MawTextData::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        m_spells = parseSpells(root["spells"]);
        m_classSpells.clear();

        for (const auto &line : root["classes"])
        {
            m_classSpells[line.first.as<std::string>()] = parseSpells(line.second);
        }

        m_skills = parseSkills(root["skills"]);
        m_stats = parseSkills(root["stats"]);
        m_items.clear();
        m_itemKinds.clear();

        for (const auto &item : root["items"])
        {
            const std::string key = item.first.as<std::string>();

            if (!key.empty() && std::all_of(key.begin(), key.end(), [](char c) { return c >= '0' && c <= '9'; }))
            {
                m_items[uint32_t(std::stoul(key))] = Engine::localize(item.second.as<std::string>());
            }
            else
            {
                m_itemKinds[key] = Engine::localize(item.second.as<std::string>());
            }
        }

        m_classSkills.clear();

        for (const auto &line : root["class_skills"])
        {
            m_classSkills[line.first.as<std::string>()] = parseSkills(line.second);
        }
    }
    catch (const std::exception &error)
    {
        errorMessage = error.what();
        return false;
    }

    return true;
}

std::optional<MawSpellTextEntry> MawTextData::find(const std::string &classLine, uint32_t spellId) const
{
    const auto general = m_spells.find(spellId);
    const auto line = m_classSpells.find(classLine);
    const MawSpellTextEntry *pOwn = nullptr;

    if (line != m_classSpells.end())
    {
        const auto own = line->second.find(spellId);
        pOwn = own != line->second.end() ? &own->second : nullptr;
    }

    if (general == m_spells.end() && pOwn == nullptr)
    {
        return std::nullopt;
    }

    MawSpellTextEntry entry = general != m_spells.end() ? general->second : MawSpellTextEntry {};

    if (pOwn != nullptr)
    {
        overlay(entry.name, pOwn->name);
        overlay(entry.description, pOwn->description);

        for (size_t mastery = 0; mastery < entry.masteryLines.size(); ++mastery)
        {
            overlay(entry.masteryLines[mastery], pOwn->masteryLines[mastery]);
        }
    }

    return entry;
}

std::optional<MawSkillTextEntry> MawTextData::findSkill(
    const std::string &classLine,
    const std::string &canonicalSkill) const
{
    const auto general = m_skills.find(canonicalSkill);
    const auto line = m_classSkills.find(classLine);
    const MawSkillTextEntry *pOwn = nullptr;

    if (line != m_classSkills.end())
    {
        const auto own = line->second.find(canonicalSkill);
        pOwn = own != line->second.end() ? &own->second : nullptr;
    }

    if (general == m_skills.end() && pOwn == nullptr)
    {
        return std::nullopt;
    }

    MawSkillTextEntry entry = general != m_skills.end() ? general->second : MawSkillTextEntry {};

    if (pOwn != nullptr)
    {
        // A class's own description or paragraph replaces the ruleset's, whichever it gives.
        if (pOwn->description || pOwn->append)
        {
            entry.description = pOwn->description;
            entry.append = pOwn->append;
        }

        for (size_t mastery = 0; mastery < entry.masteryLines.size(); ++mastery)
        {
            overlay(entry.masteryLines[mastery], pOwn->masteryLines[mastery]);
        }
    }

    return entry;
}

const MawSkillTextEntry *MawTextData::findStat(const std::string &statName) const
{
    const auto found = m_stats.find(statName);
    return found != m_stats.end() ? &found->second : nullptr;
}

const std::string *MawTextData::findItemText(uint32_t itemId) const
{
    const auto item = m_items.find(itemId);
    return item != m_items.end() ? &item->second : nullptr;
}

const std::string *MawTextData::findItemKindText(const std::string &kind) const
{
    const auto item = m_itemKinds.find(kind);
    return item != m_itemKinds.end() ? &item->second : nullptr;
}

std::vector<uint32_t> MawTextData::spellIds() const
{
    std::vector<uint32_t> ids;

    for (const auto &[spellId, entry] : m_spells)
    {
        ids.push_back(spellId);
    }

    std::sort(ids.begin(), ids.end());
    return ids;
}

std::vector<uint32_t> MawTextData::classSpellIds(const std::string &classLine) const
{
    std::vector<uint32_t> ids;
    const auto line = m_classSpells.find(classLine);

    if (line != m_classSpells.end())
    {
        for (const auto &[spellId, entry] : line->second)
        {
            ids.push_back(spellId);
        }
    }

    std::sort(ids.begin(), ids.end());
    return ids;
}

std::string mawFillText(
    const std::string &text,
    const std::unordered_map<std::string, double> &values,
    const std::unordered_map<std::string, std::string> &words)
{
    std::string result;
    size_t position = 0;

    while (position < text.size())
    {
        const size_t open = text.find('{', position);
        const size_t close = open != std::string::npos ? text.find('}', open) : std::string::npos;

        if (close == std::string::npos)
        {
            result += text.substr(position);
            break;
        }

        result += text.substr(position, open - position);
        std::string token = text.substr(open + 1, close - open - 1);
        int decimals = 0;
        double factor = 1;
        // A malformed ":N" or "*F" leaves the placeholder as written instead of failing the frame (ROB-2-10).
        bool wellFormed = true;
        const auto parsed = [&wellFormed](const std::string &number, auto &result)
        {
            const char *pEnd = number.data() + number.size();
            bool read = false;

            // Android's libc++ has no floating-point std::from_chars.
            if constexpr (std::is_floating_point_v<std::remove_reference_t<decltype(result)>>)
            {
                char *pParsedEnd = nullptr;
                result = std::strtod(number.c_str(), &pParsedEnd);
                read = pParsedEnd == pEnd;
            }
            else
            {
                const std::from_chars_result parsedNumber = std::from_chars(number.data(), pEnd, result);
                read = parsedNumber.ec == std::errc() && parsedNumber.ptr == pEnd;
            }

            wellFormed = wellFormed && !number.empty() && read;
        };

        if (const size_t colon = token.find(':'); colon != std::string::npos)
        {
            parsed(token.substr(colon + 1), decimals);
            token.resize(colon);
        }

        if (const size_t star = token.find('*'); star != std::string::npos)
        {
            parsed(token.substr(star + 1), factor);
            token.resize(star);
        }

        const auto value = values.find(token);
        const auto word = words.find(token);

        if (!wellFormed)
        {
            result += text.substr(open, close - open + 1);
        }
        else if (word != words.end())
        {
            result += word->second;
        }
        else if (value != values.end())
        {
            const double scaled = value->second * factor;
            result += formatNumber(decimals > 0 ? scaled : std::round(scaled), decimals);
        }
        else
        {
            result += text.substr(open, close - open + 1);
        }

        position = close + 1;
    }

    for (const auto &[pTag, pCode] : ColorTags)
    {
        const std::string tag = pTag;

        for (size_t found = result.find(tag); found != std::string::npos; found = result.find(tag, found))
        {
            result.replace(found, tag.size(), pCode);
        }
    }

    return result;
}
}
