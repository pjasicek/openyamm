#include "game/tables/MergedBaseTables.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <limits>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string normalizedKey(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    std::string result;
    result.reserve(trimmed.size());

    bool previousWasSpace = true;

    for (char character : trimmed)
    {
        const unsigned char unsignedCharacter = static_cast<unsigned char>(character);

        if (std::isspace(unsignedCharacter) != 0)
        {
            if (!previousWasSpace)
            {
                result.push_back(' ');
                previousWasSpace = true;
            }

            continue;
        }

        result.push_back(static_cast<char>(std::tolower(unsignedCharacter)));
        previousWasSpace = false;
    }

    if (!result.empty() && result.back() == ' ')
    {
        result.pop_back();
    }

    return result;
}

bool isMarkerCell(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    return trimmed == "x" || trimmed == "X";
}

bool isDisabledCell(const std::string &value)
{
    return trimCopy(value) == "-";
}

bool parseUnsigned(const std::string &value, uint32_t &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 10);

    if (pEnd == trimmed.c_str() || *pEnd != '\0' || parsed > std::numeric_limits<uint32_t>::max())
    {
        return false;
    }

    result = static_cast<uint32_t>(parsed);
    return true;
}

bool parseSigned(const std::string &value, int32_t &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 10);

    if (pEnd == trimmed.c_str() || *pEnd != '\0'
        || parsed < std::numeric_limits<int32_t>::min()
        || parsed > std::numeric_limits<int32_t>::max())
    {
        return false;
    }

    result = static_cast<int32_t>(parsed);
    return true;
}

bool parseDouble(const std::string &value, double &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const double parsed = std::strtod(trimmed.c_str(), &pEnd);

    if (pEnd == trimmed.c_str() || *pEnd != '\0')
    {
        return false;
    }

    result = parsed;
    return true;
}

uint32_t raceSkillMasteryFromTokenPart(const std::string &value)
{
    const std::string normalized = normalizedKey(value);

    if (normalized.empty() || normalized == "0" || normalized == "none")
    {
        return 0;
    }

    if (normalized == "b" || normalized == "basic")
    {
        return 1;
    }

    if (normalized == "e" || normalized == "expert")
    {
        return 2;
    }

    if (normalized == "m" || normalized == "master")
    {
        return 3;
    }

    if (normalized == "g" || normalized == "grandmaster")
    {
        return 4;
    }

    uint32_t parsed = 0;

    if (parseUnsigned(value, parsed))
    {
        return parsed;
    }

    return 0;
}

int32_t raceSkillExceptionCodeFromTokenPart(const std::string &value)
{
    const std::string normalized = normalizedKey(value);

    if (normalized.empty() || normalized == "0" || normalized == "none")
    {
        return 0;
    }

    if (normalized == "i")
    {
        return -1;
    }

    if (normalized == "p")
    {
        return -2;
    }

    if (normalized == "ip")
    {
        return -3;
    }

    if (normalized == "s" || normalized == "spellcaster" || normalized == "spellcasters")
    {
        return -4;
    }

    if (normalized == "w" || normalized == "warrior" || normalized == "warriors")
    {
        return -5;
    }

    int32_t parsed = 0;

    if (parseSigned(value, parsed))
    {
        return parsed;
    }

    return 0;
}

std::string raceSkillMasteryName(uint32_t mastery)
{
    switch (mastery)
    {
    case 1:
        return "basic";
    case 2:
        return "expert";
    case 3:
        return "master";
    case 4:
        return "grandmaster";
    default:
        return "none";
    }
}

std::string raceSkillExceptionName(int32_t exceptionCode)
{
    switch (exceptionCode)
    {
    case -1:
        return "i";
    case -2:
        return "p";
    case -3:
        return "ip";
    case -4:
        return "spellcaster";
    case -5:
        return "warrior";
    case 0:
        return "none";
    default:
        return std::to_string(exceptionCode);
    }
}

std::vector<std::string> splitSlashSeparated(const std::string &value)
{
    std::vector<std::string> result;
    std::stringstream stream(value);
    std::string token;

    while (std::getline(stream, token, '/'))
    {
        result.push_back(trimCopy(token));
    }

    return result;
}

bool applyRaceSkillRawToken(MergedRaceSkillOverride &entry, const std::string &rawToken)
{
    const std::vector<std::string> parts = splitSlashSeparated(rawToken);

    if (parts.empty())
    {
        return false;
    }

    entry.rawToken = rawToken;
    entry.minMastery = raceSkillMasteryFromTokenPart(parts[0]);

    if (parts.size() > 1 && !parts[1].empty())
    {
        if (!parseSigned(parts[1], entry.add))
        {
            return false;
        }
    }

    if (parts.size() > 2)
    {
        entry.exceptionCode = raceSkillExceptionCodeFromTokenPart(parts[2]);
    }

    if (entry.exception.empty())
    {
        entry.exception = raceSkillExceptionName(entry.exceptionCode);
    }

    return true;
}

std::optional<uint32_t> parseOptionalYamlUnsigned(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return node.as<uint32_t>();
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::string yamlStringOrEmpty(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return {};
    }

    try
    {
        return node.as<std::string>();
    }
    catch (const YAML::Exception &)
    {
        return {};
    }
}

bool yamlUnsignedSequence(const YAML::Node &node, std::vector<uint32_t> &values)
{
    values.clear();

    if (!node || !node.IsSequence())
    {
        return false;
    }

    try
    {
        for (const YAML::Node &entryNode : node)
        {
            if (!entryNode.IsScalar())
            {
                return false;
            }

            values.push_back(entryNode.as<uint32_t>());
        }
    }
    catch (const YAML::Exception &)
    {
        return false;
    }

    return true;
}

bool yamlStringSequence(const YAML::Node &node, std::vector<std::string> &values)
{
    values.clear();

    if (!node || !node.IsSequence())
    {
        return false;
    }

    try
    {
        for (const YAML::Node &entryNode : node)
        {
            if (!entryNode.IsScalar())
            {
                return false;
            }

            values.push_back(entryNode.as<std::string>());
        }
    }
    catch (const YAML::Exception &)
    {
        return false;
    }

    return true;
}

uint32_t parseOptionalUnsigned(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return 0;
    }

    uint32_t result = 0;
    return parseUnsigned(row[index], result) ? result : 0;
}

std::optional<uint32_t> parseOptionalUnsignedValue(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return std::nullopt;
    }

    uint32_t result = 0;
    return parseUnsigned(row[index], result) ? std::optional<uint32_t>(result) : std::nullopt;
}

int32_t parseOptionalSigned(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return 0;
    }

    int32_t result = 0;
    return parseSigned(row[index], result) ? result : 0;
}

double parseOptionalDouble(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return 0.0;
    }

    double result = 0.0;
    return parseDouble(row[index], result) ? result : 0.0;
}

bool parsePrefixedUnsigned(const std::string &value, const char *pPrefix, uint32_t &result)
{
    const std::string trimmed = trimCopy(value);
    const std::string prefix = pPrefix;

    if (trimmed.rfind(prefix, 0) != 0)
    {
        return false;
    }

    return parseUnsigned(trimmed.substr(prefix.size()), result);
}

std::vector<uint32_t> parseUnsignedList(const std::string &value)
{
    std::vector<uint32_t> result;
    std::stringstream stream(value);
    std::string token;

    while (std::getline(stream, token, ','))
    {
        uint32_t parsed = 0;

        if (parseUnsigned(token, parsed) && parsed != 0)
        {
            result.push_back(parsed);
        }
    }

    return result;
}

std::vector<std::string> splitCommaSeparated(const std::string &value)
{
    std::vector<std::string> result;
    std::stringstream stream(value);
    std::string token;

    while (std::getline(stream, token, ','))
    {
        const std::string trimmed = trimCopy(token);

        if (!trimmed.empty())
        {
            result.push_back(trimmed);
        }
    }

    return result;
}

bool parseFractionOrWhole(const std::string &value, uint32_t &numerator, uint32_t &denominator)
{
    const std::string trimmed = trimCopy(value);
    const size_t slash = trimmed.find('/');

    if (slash == std::string::npos)
    {
        if (!parseUnsigned(trimmed, numerator))
        {
            return false;
        }

        denominator = 1;
        return true;
    }

    return parseUnsigned(trimmed.substr(0, slash), numerator)
        && parseUnsigned(trimmed.substr(slash + 1), denominator)
        && denominator != 0;
}

bool parseBaseMaxPair(const std::string &value, uint32_t &baseValue, uint32_t &maxValue)
{
    return parseFractionOrWhole(value, baseValue, maxValue);
}

std::optional<uint32_t> parseTrailingParenthesizedId(const std::string &value)
{
    const size_t open = value.rfind('(');
    const size_t close = value.rfind(')');

    if (open == std::string::npos || close == std::string::npos || close <= open + 1)
    {
        return std::nullopt;
    }

    uint32_t id = 0;
    return parseUnsigned(value.substr(open + 1, close - open - 1), id) ? std::optional<uint32_t>(id) : std::nullopt;
}

std::string removeTrailingParenthesizedId(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    const size_t open = trimmed.rfind('(');
    const size_t close = trimmed.rfind(')');

    if (open == std::string::npos || close == std::string::npos || close < open)
    {
        return trimmed;
    }

    return trimCopy(trimmed.substr(0, open));
}

bool numericRow(const std::vector<std::string> &row)
{
    uint32_t ignored = 0;
    return !row.empty() && parseUnsigned(row[0], ignored);
}

bool rowContainsCell(const std::vector<std::string> &row, const char *pNeedle)
{
    for (const std::string &cell : row)
    {
        if (trimCopy(cell) == pNeedle)
        {
            return true;
        }
    }

    return false;
}

std::string firstNonEmptyCell(const std::vector<std::string> &row)
{
    for (const std::string &cell : row)
    {
        const std::string trimmed = trimCopy(cell);

        if (!trimmed.empty())
        {
            return trimmed;
        }
    }

    return "";
}

bool loadNewsRows(
    const std::vector<std::vector<std::string>> &rows,
    std::vector<MergedNewsTopicEntry> &entries)
{
    entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 3 || !numericRow(row))
        {
            continue;
        }

        MergedNewsTopicEntry entry = {};

        if (!parseUnsigned(row[0], entry.ownerId)
            || (!parseUnsigned(row[1], entry.topicTextId)
                && !parsePrefixedUnsigned(row[1], "NPCTopic ", entry.topicTextId))
            || (!parseUnsigned(row[2], entry.newsTextId)
                && !parsePrefixedUnsigned(row[2], "NPCText ", entry.newsTextId)))
        {
            return false;
        }

        entries.push_back(entry);
    }

    return !entries.empty();
}
}

bool MergedClassExtraTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 4 || !numericRow(row))
        {
            continue;
        }

        MergedClassExtraEntry entry = {};

        if (!parseUnsigned(row[0], entry.classId)
            || !parseUnsigned(row[1], entry.kind)
            || !parseUnsigned(row[2], entry.promotionStep))
        {
            return false;
        }

        entry.note = trimCopy(row[3]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool MergedCharacterSelectionTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_characterSelectionAllowedClassesByRaceId.clear();
    m_characterSelectionRaceNamesById.clear();
    m_characterSelectionContinents.clear();

    if (rows.empty())
    {
        return false;
    }

    const std::vector<std::string> classNames = rows.front();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        uint32_t raceId = 0;

        if (!parseUnsigned(row[0], raceId))
        {
            break;
        }

        std::vector<std::string> allowedClasses;

        for (size_t columnIndex = 1; columnIndex < row.size() && columnIndex < classNames.size(); ++columnIndex)
        {
            if (isMarkerCell(row[columnIndex]))
            {
                allowedClasses.push_back(trimCopy(classNames[columnIndex]));
            }
        }

        m_characterSelectionAllowedClassesByRaceId[raceId] = std::move(allowedClasses);
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (!rowContainsCell(row, "Continents:"))
        {
            continue;
        }

        size_t continentRow = rowIndex + 1;

        while (continentRow + 2 < rows.size())
        {
            const std::vector<std::string> &nameRow = rows[continentRow];
            const std::vector<std::string> &classRow = rows[continentRow + 1];
            const std::vector<std::string> &raceRow = rows[continentRow + 2];

            if (firstNonEmptyCell(classRow) != "Available classes:"
                || firstNonEmptyCell(raceRow) != "Available races:")
            {
                break;
            }

            MergedCharacterSelectionContinent continent = {};
            continent.name = trimCopy(nameRow[0]);

            if (continent.name.empty())
            {
                continent.name = firstNonEmptyCell(nameRow);
            }

            for (size_t index = 1; index < classRow.size(); ++index)
            {
                uint32_t value = 0;

                if (parseUnsigned(classRow[index], value))
                {
                    continent.availableClassIds.push_back(value);
                }
            }

            for (size_t index = 1; index < raceRow.size(); ++index)
            {
                uint32_t value = 0;

                if (parseUnsigned(raceRow[index], value))
                {
                    continent.availableRaceIds.push_back(value);
                }
            }

            if (!continent.name.empty())
            {
                m_characterSelectionContinents.push_back(std::move(continent));
            }

            continentRow += 3;
        }

        break;
    }

    return !m_characterSelectionAllowedClassesByRaceId.empty() && !m_characterSelectionContinents.empty();
}

bool MergedCharacterSelectionTable::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    m_characterSelectionAllowedClassesByRaceId.clear();
    m_characterSelectionRaceNamesById.clear();
    m_characterSelectionContinents.clear();

    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    const YAML::Node raceClassAvailabilityNode = root["race_class_availability"];

    if (!raceClassAvailabilityNode || !raceClassAvailabilityNode.IsSequence())
    {
        errorMessage = "missing race_class_availability sequence";
        return false;
    }

    for (const YAML::Node &raceNode : raceClassAvailabilityNode)
    {
        const std::optional<uint32_t> raceId = parseOptionalYamlUnsigned(raceNode["race_id"]);

        if (!raceId.has_value())
        {
            errorMessage = "race_class_availability entry is missing race_id";
            return false;
        }

        std::vector<std::string> classNames;

        if (!yamlStringSequence(raceNode["classes"], classNames))
        {
            errorMessage = "race_class_availability entry has invalid classes sequence";
            return false;
        }

        m_characterSelectionAllowedClassesByRaceId[*raceId] = std::move(classNames);
        m_characterSelectionRaceNamesById[*raceId] = yamlStringOrEmpty(raceNode["race"]);
    }

    const YAML::Node continentsNode = root["new_game_continents"];

    if (!continentsNode || !continentsNode.IsSequence())
    {
        errorMessage = "missing new_game_continents sequence";
        return false;
    }

    for (const YAML::Node &continentNode : continentsNode)
    {
        MergedCharacterSelectionContinent continent = {};
        const std::optional<uint32_t> continentId = parseOptionalYamlUnsigned(continentNode["id"]);
        continent.id = continentId.value_or(0);
        continent.key = yamlStringOrEmpty(continentNode["key"]);
        continent.name = yamlStringOrEmpty(continentNode["name"]);

        if (continent.name.empty())
        {
            errorMessage = "new_game_continents entry is missing name";
            return false;
        }

        if (!yamlUnsignedSequence(continentNode["available_class_ids"], continent.availableClassIds))
        {
            errorMessage = "new_game_continents entry has invalid available_class_ids sequence";
            return false;
        }

        if (!yamlUnsignedSequence(continentNode["available_race_ids"], continent.availableRaceIds))
        {
            errorMessage = "new_game_continents entry has invalid available_race_ids sequence";
            return false;
        }

        if (const YAML::Node portraitExceptionsNode = continentNode["portrait_exceptions"])
        {
            if (!yamlStringSequence(portraitExceptionsNode, continent.portraitExceptions))
            {
                errorMessage = "new_game_continents entry has invalid portrait_exceptions sequence";
                return false;
            }
        }

        m_characterSelectionContinents.push_back(std::move(continent));
    }

    if (m_characterSelectionAllowedClassesByRaceId.empty() || m_characterSelectionContinents.empty())
    {
        errorMessage = "character selection table has no usable rows";
        return false;
    }

    return true;
}

bool MergedRaceSkillTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_overrides.clear();

    if (rows.empty())
    {
        return false;
    }

    const std::vector<std::string> &header = rows.front();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        const std::string skillName = trimCopy(row[0]);

        if (skillName.empty())
        {
            continue;
        }

        for (size_t columnIndex = 1; columnIndex < row.size() && columnIndex < header.size(); ++columnIndex)
        {
            const std::string token = trimCopy(row[columnIndex]);

            if (token.empty() || token == "-")
            {
                continue;
            }

            MergedRaceSkillOverride override = {};
            override.skillName = skillName;
            override.rawToken = token;

            const std::string target = trimCopy(header[columnIndex]);
            const size_t classSeparator = target.find(" - ");
            const std::string raceToken = classSeparator == std::string::npos
                ? target
                : target.substr(0, classSeparator);
            const size_t raceIdBegin = raceToken.find('(');
            const size_t raceIdEnd = raceToken.find(')', raceIdBegin == std::string::npos ? 0 : raceIdBegin);

            if (raceIdBegin != std::string::npos && raceIdEnd != std::string::npos && raceIdEnd > raceIdBegin)
            {
                uint32_t raceId = 0;

                if (parseUnsigned(raceToken.substr(raceIdBegin + 1, raceIdEnd - raceIdBegin - 1), raceId))
                {
                    override.raceId = raceId;
                }

                override.race = trimCopy(raceToken.substr(0, raceIdBegin));
            }
            else
            {
                override.race = raceToken;
            }

            if (classSeparator != std::string::npos)
            {
                override.classKind = trimCopy(target.substr(classSeparator + 3));
            }

            if (!override.race.empty() && applyRaceSkillRawToken(override, token))
            {
                m_overrides.push_back(std::move(override));
            }
        }
    }

    return !m_overrides.empty();
}

bool MergedRaceSkillTable::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    m_overrides.clear();

    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = std::string("could not parse race skills yaml: ") + exception.what();
        return false;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = "race skills yaml root must be a map";
        return false;
    }

    const YAML::Node rulesNode = root["rules"];

    if (!rulesNode || !rulesNode.IsSequence())
    {
        errorMessage = "race skills yaml rules must be a sequence";
        return false;
    }

    for (const YAML::Node &ruleNode : rulesNode)
    {
        if (!ruleNode || !ruleNode.IsMap())
        {
            errorMessage = "race skill rule must be a map";
            return false;
        }

        MergedRaceSkillOverride entry = {};
        entry.race = yamlStringOrEmpty(ruleNode["race"]);
        entry.raceId = parseOptionalYamlUnsigned(ruleNode["race_id"]);
        entry.classKind = yamlStringOrEmpty(ruleNode["class_kind"]);
        entry.skillName = yamlStringOrEmpty(ruleNode["skill"]);
        entry.rawToken = yamlStringOrEmpty(ruleNode["raw_token"]);

        if (entry.race.empty() || entry.skillName.empty())
        {
            errorMessage = "race skill rule is missing race or skill";
            return false;
        }

        if (!entry.rawToken.empty())
        {
            if (!applyRaceSkillRawToken(entry, entry.rawToken))
            {
                errorMessage = "race skill rule has invalid raw_token";
                return false;
            }
        }

        if (const YAML::Node masteryNode = ruleNode["min_mastery"]; masteryNode && masteryNode.IsScalar())
        {
            entry.minMastery = raceSkillMasteryFromTokenPart(masteryNode.as<std::string>());
        }

        if (const YAML::Node addNode = ruleNode["add"]; addNode && addNode.IsScalar())
        {
            try
            {
                entry.add = addNode.as<int32_t>();
            }
            catch (const YAML::Exception &)
            {
                errorMessage = "race skill rule has invalid add";
                return false;
            }
        }

        if (const YAML::Node exceptionNode = ruleNode["exception"]; exceptionNode && exceptionNode.IsScalar())
        {
            entry.exception = exceptionNode.as<std::string>();
            entry.exceptionCode = raceSkillExceptionCodeFromTokenPart(entry.exception);
        }
        else if (const YAML::Node exceptionCodeNode = ruleNode["exception_code"];
                 exceptionCodeNode && exceptionCodeNode.IsScalar())
        {
            try
            {
                entry.exceptionCode = exceptionCodeNode.as<int32_t>();
                entry.exception = raceSkillExceptionName(entry.exceptionCode);
            }
            catch (const YAML::Exception &)
            {
                errorMessage = "race skill rule has invalid exception_code";
                return false;
            }
        }
        else if (entry.exception.empty())
        {
            entry.exception = raceSkillExceptionName(entry.exceptionCode);
        }

        if (entry.rawToken.empty())
        {
            entry.rawToken = raceSkillMasteryName(entry.minMastery) + "/" + std::to_string(entry.add) + "/"
                + entry.exception;
        }

        m_overrides.push_back(std::move(entry));
    }

    return !m_overrides.empty();
}

bool MergedTeacherTopicTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndicesByTopicId.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 5 || !numericRow(row))
        {
            continue;
        }

        MergedTeacherTopicEntry entry = {};

        if (!parseUnsigned(row[0], entry.topicId)
            || !parseUnsigned(row[2], entry.skillId)
            || !parseUnsigned(row[3], entry.mastery)
            || !parseUnsigned(row[4], entry.textId))
        {
            return false;
        }

        entry.note = row.size() > 1 ? trimCopy(row[1]) : "";
        entry.requiredGold = parseOptionalUnsigned(row, 5);
        entry.requiredSkill = parseOptionalUnsigned(row, 6);
        m_entryIndicesByTopicId[entry.topicId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool MergedTeacherAutonoteTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_mappings.clear();
    m_autonoteIdsByTopicAndNpc.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty() || !numericRow(row))
        {
            continue;
        }

        uint32_t topicId = 0;

        if (!parseUnsigned(row[0], topicId))
        {
            return false;
        }

        for (size_t columnIndex = 2; columnIndex + 1 < row.size(); columnIndex += 2)
        {
            uint32_t npcId = 0;
            uint32_t autonoteId = 0;

            if (!parseUnsigned(row[columnIndex], npcId) || !parseUnsigned(row[columnIndex + 1], autonoteId))
            {
                continue;
            }

            MergedTeacherAutonoteMapping mapping = {};
            mapping.topicId = topicId;
            mapping.npcId = npcId;
            mapping.autonoteId = autonoteId;
            m_autonoteIdsByTopicAndNpc[key(topicId, npcId)] = autonoteId;
            m_mappings.push_back(mapping);
        }
    }

    return !m_mappings.empty();
}

bool MergedNpcProfessionTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 11 || !numericRow(row))
        {
            continue;
        }

        MergedNpcProfessionEntry entry = {};

        if (!parseUnsigned(row[0], entry.id)
            || !parseUnsigned(row[3], entry.rarity)
            || !parseUnsigned(row[4], entry.weeklyCost))
        {
            return false;
        }

        entry.profession = row.size() > 1 ? trimCopy(row[1]) : "";
        entry.globalTextId = parseOptionalUnsigned(row, 2);
        entry.personality = row.size() > 5 ? trimCopy(row[5]) : "";
        entry.actionTopicId = parseOptionalUnsigned(row, 6);
        entry.joins = row.size() > 7 && isMarkerCell(row[7]);
        entry.recruit = row.size() > 8 && isMarkerCell(row[8]);
        entry.joinTextId = parseOptionalUnsigned(row, 9);
        entry.descriptionTextId = parseOptionalUnsigned(row, 10);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const MergedNpcProfessionEntry *MergedNpcProfessionTable::get(uint32_t professionId) const
{
    for (const MergedNpcProfessionEntry &entry : m_entries)
    {
        if (entry.id == professionId)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool MergedNpcNameTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_npcMaleNames.clear();
    m_npcFemaleNames.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        if (!trimCopy(row[0]).empty())
        {
            m_npcMaleNames.push_back(trimCopy(row[0]));
        }

        if (row.size() > 1 && !trimCopy(row[1]).empty())
        {
            m_npcFemaleNames.push_back(trimCopy(row[1]));
        }
    }

    return !m_npcMaleNames.empty() && !m_npcFemaleNames.empty();
}

bool MergedNpcBtbTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 31 || trimCopy(row[0]).empty())
        {
            continue;
        }

        MergedNpcBtbEntry entry = {};
        entry.personality = trimCopy(row[0]);
        entry.acceptBeg = isMarkerCell(row[1]);
        entry.acceptBribe = isMarkerCell(row[2]);
        entry.acceptThreat = isMarkerCell(row[3]);
        entry.creed = trimCopy(row[4]);
        entry.requiredFame = parseOptionalUnsigned(row, 5);
        entry.requiredReputation = parseOptionalSigned(row, 6);
        entry.reputationOkFirstTextId = parseOptionalUnsigned(row, 7);
        entry.reputationOkSecondTextId = parseOptionalUnsigned(row, 8);
        entry.begReturnTextId = parseOptionalUnsigned(row, 9);
        entry.bribeReturnTextId = parseOptionalUnsigned(row, 10);
        entry.threatReturnTextId = parseOptionalUnsigned(row, 11);
        entry.fameTooLowTextId = parseOptionalUnsigned(row, 12);
        entry.reputationNotoriousGoodTextId = parseOptionalUnsigned(row, 13);
        entry.reputationNotoriousEvilTextId = parseOptionalUnsigned(row, 14);
        entry.reputationSaintlyGoodTextId = parseOptionalUnsigned(row, 15);
        entry.reputationSaintlyEvilTextId = parseOptionalUnsigned(row, 16);
        entry.reputationBelowZeroFirstGoodTextId = parseOptionalUnsigned(row, 17);
        entry.reputationAboveTenFirstEvilTextId = parseOptionalUnsigned(row, 18);
        entry.lowReputationFirstGoodTextId = parseOptionalUnsigned(row, 19);
        entry.lowReputationFirstEvilTextId = parseOptionalUnsigned(row, 20);
        entry.reputationBelowZeroSecondGoodTextId = parseOptionalUnsigned(row, 21);
        entry.reputationAboveTenSecondEvilTextId = parseOptionalUnsigned(row, 22);
        entry.lowReputationSecondGoodTextId = parseOptionalUnsigned(row, 23);
        entry.lowReputationSecondEvilTextId = parseOptionalUnsigned(row, 24);
        entry.begSuccessTextId = parseOptionalUnsigned(row, 25);
        entry.begFailTextId = parseOptionalUnsigned(row, 26);
        entry.bribeSuccessTextId = parseOptionalUnsigned(row, 27);
        entry.bribeFailTextId = parseOptionalUnsigned(row, 28);
        entry.threatSuccessTextId = parseOptionalUnsigned(row, 29);
        entry.threatFailTextId = parseOptionalUnsigned(row, 30);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool MergedNewsTopicTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    return loadNewsRows(rows, m_entries);
}

bool MergedNewsProfessionTopicTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_topics.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 16 || !numericRow(row))
        {
            continue;
        }

        uint32_t professionId = 0;

        if (!parseUnsigned(row[0], professionId))
        {
            return false;
        }

        for (size_t dayIndex = 0; dayIndex < 7; ++dayIndex)
        {
            const size_t topicColumn = 2 + dayIndex * 2;
            const size_t textColumn = topicColumn + 1;
            MergedNewsProfessionDayTopic topic = {};

            if (!parseUnsigned(row[topicColumn], topic.topicTextId)
                || !parseUnsigned(row[textColumn], topic.newsTextId))
            {
                return false;
            }

            topic.professionId = professionId;
            topic.dayIndex = static_cast<uint32_t>(dayIndex);
            m_topics.push_back(topic);
        }
    }

    return !m_topics.empty();
}

const MergedNewsProfessionDayTopic *MergedNewsProfessionTopicTable::get(
    uint32_t professionId,
    uint32_t dayIndex) const
{
    for (const MergedNewsProfessionDayTopic &topic : m_topics)
    {
        if (topic.professionId == professionId && topic.dayIndex == dayIndex)
        {
            return &topic;
        }
    }

    return nullptr;
}

bool MergedMonsterPortraitTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_monsterPortraitsByGroupId.clear();
    m_monsterPortraitsByName.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 2 || !numericRow(row))
        {
            continue;
        }

        uint32_t groupId = 0;

        if (!parseUnsigned(row[0], groupId))
        {
            return false;
        }

        std::vector<uint32_t> portraits = parseUnsignedList(row[1]);
        m_monsterPortraitsByGroupId[groupId] = portraits;

        if (row.size() > 2)
        {
            const std::string nameKey = normalizedKey(row[2]);

            if (!nameKey.empty())
            {
                std::vector<uint32_t> &namedPortraits = m_monsterPortraitsByName[nameKey];

                for (uint32_t portraitId : portraits)
                {
                    if (portraitId != 0
                        && std::find(namedPortraits.begin(), namedPortraits.end(), portraitId)
                            == namedPortraits.end())
                    {
                        namedPortraits.push_back(portraitId);
                    }
                }
            }
        }
    }

    return !m_monsterPortraitsByGroupId.empty();
}

std::optional<uint32_t> MergedMonsterPortraitTable::firstPortraitForName(const std::string &name) const
{
    const std::string key = normalizedKey(name);

    if (key.empty())
    {
        return std::nullopt;
    }

    const auto it = m_monsterPortraitsByName.find(key);

    if (it == m_monsterPortraitsByName.end())
    {
        return std::nullopt;
    }

    for (uint32_t portraitId : it->second)
    {
        if (portraitId != 0)
        {
            return portraitId;
        }
    }

    return std::nullopt;
}

std::optional<uint32_t> MergedMonsterPortraitTable::portraitForMonsterId(uint32_t monsterId, uint64_t seed) const
{
    if (monsterId == 0)
    {
        return std::nullopt;
    }

    const uint32_t portraitGroupId = (monsterId + 2u) / 3u;
    const auto it = m_monsterPortraitsByGroupId.find(portraitGroupId);

    if (it == m_monsterPortraitsByGroupId.end() || it->second.empty())
    {
        return std::nullopt;
    }

    return it->second[static_cast<size_t>(seed % it->second.size())];
}

std::optional<uint32_t> MergedMonsterPortraitTable::portraitForName(const std::string &name, uint64_t seed) const
{
    const std::string key = normalizedKey(name);

    if (key.empty())
    {
        return std::nullopt;
    }

    const auto it = m_monsterPortraitsByName.find(key);

    if (it == m_monsterPortraitsByName.end() || it->second.empty())
    {
        return std::nullopt;
    }

    return it->second[seed % it->second.size()];
}

bool MergedPotionSettingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndicesByItemId.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 5 || !numericRow(row))
        {
            continue;
        }

        MergedPotionSettingEntry entry = {};

        if (!parseUnsigned(row[0], entry.potionId) || !parseUnsigned(row[1], entry.itemId))
        {
            return false;
        }

        uint32_t requiredMastery = 0;

        if (row.size() > 2 && parseUnsigned(row[2], requiredMastery))
        {
            entry.requiredMastery = requiredMastery;
        }

        entry.drinkable = row.size() > 3 && isMarkerCell(row[3]);
        entry.usable = row.size() > 4 && isMarkerCell(row[4]);
        entry.note = row.size() > 5 ? trimCopy(row[5]) : "";
        m_entryIndicesByItemId[entry.itemId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool MergedReagentSettingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_resultItemIdsByReagentItemId.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 3 || !numericRow(row))
        {
            continue;
        }

        MergedReagentSettingEntry entry = {};

        if (!parseUnsigned(row[0], entry.reagentId)
            || !parseUnsigned(row[1], entry.itemId)
            || !parseUnsigned(row[2], entry.resultItemId))
        {
            return false;
        }

        entry.note = row.size() > 3 ? trimCopy(row[3]) : "";
        m_resultItemIdsByReagentItemId[entry.itemId] = entry.resultItemId;
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedClassExtraEntry> &MergedClassExtraTable::entries() const
{
    return m_entries;
}

const std::vector<std::string> *MergedCharacterSelectionTable::allowedClassesForRaceId(uint32_t raceId) const
{
    const std::unordered_map<uint32_t, std::vector<std::string>>::const_iterator it =
        m_characterSelectionAllowedClassesByRaceId.find(raceId);
    return it != m_characterSelectionAllowedClassesByRaceId.end() ? &it->second : nullptr;
}

const std::vector<MergedCharacterSelectionContinent> &
MergedCharacterSelectionTable::continents() const
{
    return m_characterSelectionContinents;
}

std::optional<std::string> MergedCharacterSelectionTable::raceNameForId(uint32_t raceId) const
{
    const std::unordered_map<uint32_t, std::string>::const_iterator it =
        m_characterSelectionRaceNamesById.find(raceId);

    if (it == m_characterSelectionRaceNamesById.end() || it->second.empty())
    {
        return std::nullopt;
    }

    return it->second;
}

size_t MergedCharacterSelectionTable::raceCount() const
{
    return m_characterSelectionAllowedClassesByRaceId.size();
}

const std::vector<MergedRaceSkillOverride> &MergedRaceSkillTable::overrides() const
{
    return m_overrides;
}

size_t MergedRaceSkillTable::overrideCount() const
{
    return m_overrides.size();
}

const std::vector<MergedTeacherTopicEntry> &MergedTeacherTopicTable::entries() const
{
    return m_entries;
}

const MergedTeacherTopicEntry *MergedTeacherTopicTable::get(uint32_t topicId) const
{
    const auto found = m_entryIndicesByTopicId.find(topicId);
    return found != m_entryIndicesByTopicId.end() ? &m_entries[found->second] : nullptr;
}

std::optional<uint32_t> MergedTeacherAutonoteTable::autonoteIdForTopicAndNpc(
    uint32_t topicId,
    uint32_t npcId) const
{
    const auto found = m_autonoteIdsByTopicAndNpc.find(key(topicId, npcId));
    return found != m_autonoteIdsByTopicAndNpc.end()
        ? std::optional<uint32_t>(found->second)
        : std::nullopt;
}

size_t MergedTeacherAutonoteTable::mappingCount() const
{
    return m_mappings.size();
}

uint64_t MergedTeacherAutonoteTable::key(uint32_t topicId, uint32_t npcId)
{
    return (static_cast<uint64_t>(topicId) << 32) | static_cast<uint64_t>(npcId);
}

const std::vector<MergedNpcProfessionEntry> &MergedNpcProfessionTable::entries() const
{
    return m_entries;
}

size_t MergedNpcNameTable::maleNameCount() const
{
    return m_npcMaleNames.size();
}

size_t MergedNpcNameTable::femaleNameCount() const
{
    return m_npcFemaleNames.size();
}

const std::vector<std::string> &MergedNpcNameTable::maleNames() const
{
    return m_npcMaleNames;
}

const std::vector<std::string> &MergedNpcNameTable::femaleNames() const
{
    return m_npcFemaleNames;
}

const MergedNpcBtbEntry *MergedNpcBtbTable::get(const std::string &personality) const
{
    for (const MergedNpcBtbEntry &entry : m_entries)
    {
        if (entry.personality == personality)
        {
            return &entry;
        }
    }

    return nullptr;
}

const std::vector<MergedNpcBtbEntry> &MergedNpcBtbTable::entries() const
{
    return m_entries;
}

size_t MergedNpcBtbTable::personalityCount() const
{
    return m_entries.size();
}

const std::vector<MergedNewsTopicEntry> &MergedNewsTopicTable::entries() const
{
    return m_entries;
}

size_t MergedNewsProfessionTopicTable::topicCount() const
{
    return m_topics.size();
}

size_t MergedMonsterPortraitTable::groupCount() const
{
    return m_monsterPortraitsByGroupId.size();
}

const std::vector<MergedPotionSettingEntry> &MergedPotionSettingTable::entries() const
{
    return m_entries;
}

const MergedPotionSettingEntry *MergedPotionSettingTable::getByItemId(uint32_t itemId) const
{
    const auto found = m_entryIndicesByItemId.find(itemId);
    return found != m_entryIndicesByItemId.end() ? &m_entries[found->second] : nullptr;
}

uint32_t MergedPotionSettingTable::emptyBottleItemId() const
{
    for (const MergedPotionSettingEntry &entry : m_entries)
    {
        if (entry.potionId == 0)
        {
            return entry.itemId;
        }
    }

    return 0;
}

uint32_t MergedPotionSettingTable::catalystPotionItemId() const
{
    for (const MergedPotionSettingEntry &entry : m_entries)
    {
        if (entry.potionId == 1)
        {
            return entry.itemId;
        }
    }

    return 0;
}

const std::vector<MergedReagentSettingEntry> &MergedReagentSettingTable::entries() const
{
    return m_entries;
}

std::optional<uint32_t> MergedReagentSettingTable::resultItemIdForReagent(uint32_t itemId) const
{
    const auto found = m_resultItemIdsByReagentItemId.find(itemId);
    return found != m_resultItemIdsByReagentItemId.end()
        ? std::optional<uint32_t>(found->second)
        : std::nullopt;
}

bool MergedAdditionalUiTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 10 || !numericRow(row))
        {
            continue;
        }

        MergedAdditionalUiEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.lodName = trimCopy(row[1]);
        entry.dLodName = trimCopy(row[2]);
        entry.showBlankHostileIndicator = isMarkerCell(row[3]);
        entry.hostileIndicatorY = parseOptionalSigned(row, 4);
        entry.hostileIndicatorXOffset = parseOptionalSigned(row, 5);
        entry.selectionRingOnTop = isMarkerCell(row[6]);
        entry.selectionRingY = parseOptionalSigned(row, 7);
        entry.selectionRingXOffset = parseOptionalSigned(row, 8);
        entry.notes = trimCopy(row[9]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedAdditionalUiEntry> &MergedAdditionalUiTable::entries() const
{
    return m_entries;
}

bool MergedBolsterFormulaTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 3 || trimCopy(row[0]).empty())
        {
            continue;
        }

        MergedBolsterFormulaEntry entry = {};
        entry.target = trimCopy(row[0]);
        entry.monsterKindId = parseOptionalUnsignedValue(row, 0);
        entry.stat = trimCopy(row[1]);
        entry.formula = trimCopy(row[2]);
        entry.notes = row.size() > 3 ? trimCopy(row[3]) : "";

        if (!entry.stat.empty() && !entry.formula.empty())
        {
            m_entries.push_back(std::move(entry));
        }
    }

    return !m_entries.empty();
}

const std::vector<MergedBolsterFormulaEntry> &MergedBolsterFormulaTable::entries() const
{
    return m_entries;
}

bool MergedBolsterMapTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 9 || !numericRow(row))
        {
            continue;
        }

        MergedBolsterMapEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.note = trimCopy(row[1]);
        entry.continent = parseOptionalUnsigned(row, 2);
        entry.bolsterKind = trimCopy(row[3]);
        entry.spells = isMarkerCell(row[4]);
        entry.summons = isMarkerCell(row[5]);
        entry.weather = isMarkerCell(row[6]);
        entry.bolsterExtra = parseOptionalUnsigned(row, 7);
        entry.professionMaxRarity = parseOptionalUnsignedValue(row, 8);
        entry.customSky = row.size() > 9 ? trimCopy(row[9]) : "";
        entry.rain = row.size() > 10 ? !isDisabledCell(row[10]) : true;
        entry.snow = row.size() > 11 ? isMarkerCell(row[11]) : false;
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedBolsterMapEntry> &MergedBolsterMapTable::entries() const
{
    return m_entries;
}

const MergedBolsterMapEntry *MergedBolsterMapTable::findById(uint32_t id) const
{
    for (const MergedBolsterMapEntry &entry : m_entries)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool MergedBolsterMonsterTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 17 || !numericRow(row))
        {
            continue;
        }

        MergedBolsterMonsterEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.note = trimCopy(row[1]);
        entry.type = trimCopy(row[2]);
        entry.extraTypes = splitCommaSeparated(row[3]);
        entry.creed = trimCopy(row[4]);
        entry.gender = trimCopy(row[5]);
        entry.style = trimCopy(row[6]);
        entry.preferredMagic = trimCopy(row[7]);
        entry.noBountyHunt = isMarkerCell(row[8]);
        entry.newRangedAttacks = isMarkerCell(row[9]);
        entry.newSpells = isMarkerCell(row[10]);
        entry.sizeAffectsHp = isMarkerCell(row[11]);
        entry.replicate = isMarkerCell(row[12]);
        entry.newSummons = isMarkerCell(row[13]);
        entry.summonId = parseOptionalUnsignedValue(row, 14);
        entry.extraPoints = parseOptionalUnsignedValue(row, 15);
        entry.maxHpBoostPercent = parseOptionalUnsignedValue(row, 16);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedBolsterMonsterEntry> &MergedBolsterMonsterTable::entries() const
{
    return m_entries;
}

const MergedBolsterMonsterEntry *MergedBolsterMonsterTable::findById(uint32_t id) const
{
    for (const MergedBolsterMonsterEntry &entry : m_entries)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool MergedCharacterVoiceTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    if (rows.empty())
    {
        return false;
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty() || trimCopy(row[0]).empty())
        {
            continue;
        }

        MergedCharacterVoiceEntry entry = {};
        entry.soundType = trimCopy(row[0]);

        for (size_t columnIndex = 1; columnIndex < row.size(); ++columnIndex)
        {
            entry.soundIdsByVoiceSetId.push_back(parseOptionalUnsigned(row, columnIndex));
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedCharacterVoiceEntry> &MergedCharacterVoiceTable::entries() const
{
    return m_entries;
}

std::vector<uint32_t> MergedCharacterVoiceTable::soundIdsForTypes(
    uint32_t voiceSetId,
    const std::vector<std::string> &soundTypes) const
{
    std::vector<uint32_t> soundIds;

    for (const std::string &soundType : soundTypes)
    {
        const std::string requestedType = normalizedKey(soundType);

        for (const MergedCharacterVoiceEntry &entry : m_entries)
        {
            if (normalizedKey(entry.soundType) != requestedType)
            {
                continue;
            }

            if (voiceSetId >= entry.soundIdsByVoiceSetId.size())
            {
                continue;
            }

            const uint32_t soundId = entry.soundIdsByVoiceSetId[voiceSetId];

            if (soundId != 0)
            {
                soundIds.push_back(soundId);
            }
        }
    }

    return soundIds;
}

bool MergedClassStartingStatTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    if (rows.size() < 3)
    {
        return false;
    }

    const std::vector<std::string> &header = rows[0];

    for (size_t rowIndex = 1; rowIndex + 1 < rows.size(); rowIndex += 2)
    {
        const std::vector<std::string> &statRow = rows[rowIndex];
        const std::vector<std::string> &addRow = rows[rowIndex + 1];

        if (statRow.empty() || trimCopy(statRow[0]).empty() || firstNonEmptyCell(addRow) != "+ add")
        {
            continue;
        }

        const std::string statName = trimCopy(statRow[0]);

        for (size_t columnIndex = 1; columnIndex < header.size() && columnIndex < statRow.size(); ++columnIndex)
        {
            uint32_t baseValue = 0;
            uint32_t maxValue = 0;
            uint32_t addNumerator = 0;
            uint32_t addDenominator = 1;

            if (!parseBaseMaxPair(statRow[columnIndex], baseValue, maxValue))
            {
                return false;
            }

            if (columnIndex >= addRow.size()
                || !parseFractionOrWhole(addRow[columnIndex], addNumerator, addDenominator))
            {
                return false;
            }

            MergedClassStartingStatEntry entry = {};
            entry.statName = statName;
            entry.raceName = removeTrailingParenthesizedId(header[columnIndex]);
            entry.raceId = parseTrailingParenthesizedId(header[columnIndex]);
            entry.baseValue = baseValue;
            entry.maxValue = maxValue;
            entry.addNumerator = addNumerator;
            entry.addDenominator = addDenominator;
            m_entries.push_back(std::move(entry));
        }
    }

    return !m_entries.empty();
}

const std::vector<MergedClassStartingStatEntry> &MergedClassStartingStatTable::entries() const
{
    return m_entries;
}

bool MergedComplexItemPictureOffsetTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 4 || !numericRow(row))
        {
            continue;
        }

        MergedComplexItemPictureOffsetEntry entry = {};

        if (!parseUnsigned(row[0], entry.portraitId) || !parseUnsigned(row[1], entry.itemId))
        {
            return false;
        }

        entry.x = parseOptionalSigned(row, 2);
        entry.y = parseOptionalSigned(row, 3);
        m_entries.push_back(entry);
    }

    return !m_entries.empty();
}

const std::vector<MergedComplexItemPictureOffsetEntry> &MergedComplexItemPictureOffsetTable::entries() const
{
    return m_entries;
}

bool MergedComplexItemPictureTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_entryIndicesByItemId.clear();

    for (size_t rowIndex = 2; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 4 || !numericRow(row))
        {
            continue;
        }

        MergedComplexItemPictureEntry entry = {};

        if (!parseUnsigned(row[0], entry.id) || !parseUnsigned(row[1], entry.itemId))
        {
            return false;
        }

        entry.notes = trimCopy(row[2]);

        constexpr size_t firstPointColumn = 4;
        constexpr size_t pointCount = 6;

        for (size_t pointIndex = 0; pointIndex < pointCount; ++pointIndex)
        {
            const size_t columnIndex = firstPointColumn + pointIndex * 2;
            int32_t x = 0;
            int32_t y = 0;

            if (columnIndex + 1 < row.size())
            {
                parseSigned(row[columnIndex], x);
                parseSigned(row[columnIndex + 1], y);
            }

            entry.points.push_back({x, y, 0});
        }

        m_entryIndicesByItemId[entry.itemId] = m_entries.size();
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const MergedComplexItemPictureEntry *MergedComplexItemPictureTable::get(uint32_t itemId) const
{
    const std::unordered_map<uint32_t, size_t>::const_iterator found = m_entryIndicesByItemId.find(itemId);
    return found != m_entryIndicesByItemId.end() ? &m_entries[found->second] : nullptr;
}

const std::vector<MergedComplexItemPictureEntry> &MergedComplexItemPictureTable::entries() const
{
    return m_entries;
}

bool MergedContinentSettingTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 23 || !numericRow(row))
        {
            continue;
        }

        MergedContinentSettingEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.note = trimCopy(row[1]);
        entry.reputationAffectsGuards = isMarkerCell(row[2]);
        entry.reputationAffectsShops = isMarkerCell(row[3]);
        entry.reputationAffectsNpc = isMarkerCell(row[4]);
        entry.tellProfessionNews = isMarkerCell(row[5]);
        entry.npcFollowers = isMarkerCell(row[6]);
        entry.saturation = parseOptionalDouble(row, 7);
        entry.softness = parseOptionalDouble(row, 8);
        entry.deathMovie = trimCopy(row[9]);
        entry.specificWater = trimCopy(row[10]);
        entry.deathMap1 = trimCopy(row[11]);
        entry.deathMap1X = parseOptionalSigned(row, 12);
        entry.deathMap1Y = parseOptionalSigned(row, 13);
        entry.deathMap1Z = parseOptionalSigned(row, 14);
        entry.deathMap1Direction = parseOptionalSigned(row, 15);
        entry.deathMap2 = trimCopy(row[16]);
        entry.deathMap2X = parseOptionalSigned(row, 17);
        entry.deathMap2Y = parseOptionalSigned(row, 18);
        entry.deathMap2Z = parseOptionalSigned(row, 19);
        entry.deathMap2Direction = parseOptionalSigned(row, 20);
        entry.skies = splitCommaSeparated(row[21]);
        entry.loadingPictures = splitCommaSeparated(row[22]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedContinentSettingEntry> &MergedContinentSettingTable::entries() const
{
    return m_entries;
}

const MergedContinentSettingEntry *MergedContinentSettingTable::findById(uint32_t id) const
{
    for (const MergedContinentSettingEntry &entry : m_entries)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool MergedHardwareWaterTextureTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 2 || trimCopy(row[0]).empty())
        {
            continue;
        }

        MergedHardwareWaterTextureEntry entry = {};
        entry.softwareTexture = trimCopy(row[0]);
        entry.hardwareTexturePrefix = trimCopy(row[1]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedHardwareWaterTextureEntry> &MergedHardwareWaterTextureTable::entries() const
{
    return m_entries;
}

bool MergedHouseExitTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_data = {};

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty())
        {
            continue;
        }

        const std::string firstCell = trimCopy(row[0]);

        if (firstCell == "NPC pics:")
        {
            for (size_t columnIndex = 1; columnIndex < row.size(); ++columnIndex)
            {
                uint32_t value = 0;

                if (parseUnsigned(row[columnIndex], value))
                {
                    m_data.npcPictureIds.push_back(value);
                }
            }

            continue;
        }

        if (firstCell == "Free NPC:")
        {
            m_data.freeNpcId = parseOptionalUnsignedValue(row, 1);
            continue;
        }

        if (firstCell == "Free topic:")
        {
            m_data.freeTopicId = parseOptionalUnsignedValue(row, 1);
            continue;
        }

        if (firstCell == "Map name")
        {
            continue;
        }

        if (firstCell.empty())
        {
            continue;
        }

        MergedHouseExitEntry entry = {};
        entry.mapName = firstCell;

        for (size_t columnIndex = 1; columnIndex + 2 < row.size(); columnIndex += 3)
        {
            int32_t x = 0;
            int32_t y = 0;
            int32_t z = 0;

            if (parseSigned(row[columnIndex], x)
                && parseSigned(row[columnIndex + 1], y)
                && parseSigned(row[columnIndex + 2], z))
            {
                entry.positions.push_back({x, y, z});
            }
        }

        if (!entry.positions.empty())
        {
            m_data.exits.push_back(std::move(entry));
        }
    }

    return !m_data.npcPictureIds.empty() && !m_data.exits.empty();
}

const MergedHouseExitTableData &MergedHouseExitTable::data() const
{
    return m_data;
}

bool MergedHouseRuleTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_sections.clear();
    MergedHouseRuleSection *pCurrentSection = nullptr;

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];
        const std::string firstCell = row.empty() ? "" : trimCopy(row[0]);

        if (firstCell.empty())
        {
            continue;
        }

        int32_t ignored = 0;

        if (!parseSigned(firstCell, ignored))
        {
            MergedHouseRuleSection section = {};
            section.name = firstCell;
            m_sections.push_back(std::move(section));
            pCurrentSection = &m_sections.back();
            continue;
        }

        if (pCurrentSection == nullptr)
        {
            MergedHouseRuleSection section = {};
            section.name = "default";
            m_sections.push_back(std::move(section));
            pCurrentSection = &m_sections.back();
        }

        std::vector<int32_t> values;

        for (const std::string &cell : row)
        {
            int32_t value = 0;

            if (parseSigned(cell, value))
            {
                values.push_back(value);
            }
        }

        if (!values.empty())
        {
            pCurrentSection->numericRows.push_back(std::move(values));
        }
    }

    return !m_sections.empty();
}

const std::vector<MergedHouseRuleSection> &MergedHouseRuleTable::sections() const
{
    return m_sections;
}

bool MergedHistoryTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 4 || !numericRow(row))
        {
            continue;
        }

        MergedHistoryEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.text = row[1];
        entry.time = trimCopy(row[2]);
        entry.pageTitle = trimCopy(row[3]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedHistoryEntry> &MergedHistoryTable::entries() const
{
    return m_entries;
}

bool MergedOutdoorTravelTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    const auto parseDirection =
        [](
            const std::vector<std::string> &row,
            size_t baseIndex,
            size_t requirementIndex) -> MergedOutdoorTravelDirection
        {
            MergedOutdoorTravelDirection direction = {};
            direction.mapName = baseIndex < row.size() ? trimCopy(row[baseIndex]) : "";
            direction.side = baseIndex + 1 < row.size() ? trimCopy(row[baseIndex + 1]) : "";
            direction.days = parseOptionalUnsignedValue(row, baseIndex + 2);
            direction.requirements = requirementIndex < row.size() ? trimCopy(row[requirementIndex]) : "";
            return direction;
        };

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 15 || trimCopy(row[0]).empty())
        {
            continue;
        }

        MergedOutdoorTravelEntry entry = {};
        entry.keyMap = trimCopy(row[0]);
        entry.up = parseDirection(row, 1, 15);
        entry.down = parseDirection(row, 4, 16);
        entry.left = parseDirection(row, 7, 17);
        entry.right = parseDirection(row, 10, 18);
        entry.straightTravel = isMarkerCell(row[13]);
        entry.notes = trimCopy(row[14]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedOutdoorTravelEntry> &MergedOutdoorTravelTable::entries() const
{
    return m_entries;
}

bool MergedOverlayTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 3 || !numericRow(row))
        {
            continue;
        }

        MergedOverlayEntry entry = {};

        if (!parseUnsigned(row[0], entry.id) || !parseUnsigned(row[1], entry.type))
        {
            return false;
        }

        entry.sftGroup = trimCopy(row[2]);
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedOverlayEntry> &MergedOverlayTable::entries() const
{
    return m_entries;
}

bool MergedTownPortalSwitchTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_groups.clear();
    MergedTownPortalSwitchGroup *pCurrentGroup = nullptr;

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.empty())
        {
            continue;
        }

        const std::string firstCell = trimCopy(row[0]);

        if (firstCell.empty())
        {
            continue;
        }

        if (firstCell == "@")
        {
            if (row.size() < 3)
            {
                return false;
            }

            MergedTownPortalSwitchGroup group = {};
            group.name = trimCopy(row[1]);

            if (!parseUnsigned(row[2], group.topicId))
            {
                return false;
            }

            m_groups.push_back(std::move(group));
            pCurrentGroup = &m_groups.back();
            continue;
        }

        if (pCurrentGroup == nullptr || row.size() < 13)
        {
            continue;
        }

        MergedTownPortalDestination destination = {};

        if (!parseUnsigned(row[0], destination.id)
            || !parseUnsigned(row[1], destination.mapId)
            || !parseSigned(row[2], destination.x)
            || !parseSigned(row[3], destination.y)
            || !parseSigned(row[4], destination.z)
            || !parseSigned(row[5], destination.direction)
            || !parseSigned(row[6], destination.lookAngle))
        {
            return false;
        }

        destination.iconName = trimCopy(row[7]);
        destination.iconX = parseOptionalSigned(row, 8);
        destination.iconY = parseOptionalSigned(row, 9);
        destination.iconWidth = parseOptionalUnsignedValue(row, 10);
        destination.iconHeight = parseOptionalUnsignedValue(row, 11);

        if (!parseUnsigned(row[12], destination.qbitIndex))
        {
            return false;
        }

        destination.description = row.size() > 13 ? trimCopy(row[13]) : "";
        pCurrentGroup->destinations.push_back(std::move(destination));
    }

    return !m_groups.empty();
}

const std::vector<MergedTownPortalSwitchGroup> &MergedTownPortalSwitchTable::groups() const
{
    return m_groups;
}

bool MergedTransportIndexTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 2 || !numericRow(row))
        {
            continue;
        }

        MergedTransportIndexEntry entry = {};

        if (!parseUnsigned(row[0], entry.houseEventId))
        {
            return false;
        }

        for (size_t columnIndex = 1; columnIndex < row.size(); ++columnIndex)
        {
            int32_t index = 0;

            if (!parseSigned(row[columnIndex], index))
            {
                return false;
            }

            entry.locationIndicesByPeriod.push_back(index);
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedTransportIndexEntry> &MergedTransportIndexTable::entries() const
{
    return m_entries;
}

bool MergedTransportLocationTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 15 || !numericRow(row))
        {
            continue;
        }

        MergedTransportLocationEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            return false;
        }

        entry.mapName = trimCopy(row[1]);

        for (size_t dayIndex = 0; dayIndex < entry.weekdays.size(); ++dayIndex)
        {
            entry.weekdays[dayIndex] = isMarkerCell(row[2 + dayIndex]);
        }

        if (!parseUnsigned(row[9], entry.daysCount)
            || !parseSigned(row[10], entry.x)
            || !parseSigned(row[11], entry.y)
            || !parseSigned(row[12], entry.z)
            || !parseSigned(row[13], entry.direction)
            || !parseUnsigned(row[14], entry.qbit))
        {
            return false;
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const std::vector<MergedTransportLocationEntry> &MergedTransportLocationTable::entries() const
{
    return m_entries;
}
}
