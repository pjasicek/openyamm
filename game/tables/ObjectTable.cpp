#include "game/tables/ObjectTable.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
struct FlagNameBit
{
    std::string_view name;
    uint16_t bit;
};

constexpr FlagNameBit FlagNameBits[] = {
    {"NoSprite", 0x0001},
    {"NoCollision", 0x0002},
    {"LifeTime", 0x0004},
    {"FTLifeTime", 0x0008},
    {"NoPickup", 0x0010},
    {"NoGravity", 0x0020},
    {"FlagOnIntercept", 0x0040},
    {"Bounce", 0x0080},
    {"TrailParticle", 0x0100},
    {"TrailFire", 0x0200},
    {"TrailLine", 0x0400}
};

std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return "";
    }

    return std::string(begin, end);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return result;
}

bool isCommentRow(const std::vector<std::string> &row)
{
    if (row.empty())
    {
        return true;
    }

    for (const std::string &cell : row)
    {
        if (!trimCopy(cell).empty())
        {
            return trimCopy(row.front()).starts_with("//");
        }
    }

    return true;
}

bool parseInt16Cell(const std::vector<std::string> &row, size_t index, int16_t &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    if (parsed < std::numeric_limits<int16_t>::min() || parsed > std::numeric_limits<int16_t>::max())
    {
        return false;
    }

    value = static_cast<int16_t>(parsed);
    return true;
}

bool parseUInt16Cell(const std::vector<std::string> &row, size_t index, uint16_t &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty())
    {
        return false;
    }

    if (trimmed.front() == '-')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    if (parsed > std::numeric_limits<uint16_t>::max())
    {
        return false;
    }

    value = static_cast<uint16_t>(parsed);
    return true;
}

bool parseUInt32Cell(const std::vector<std::string> &row, size_t index, uint32_t &value)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty())
    {
        return false;
    }

    if (trimmed.front() == '-')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    if (parsed > std::numeric_limits<uint32_t>::max())
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}

bool parseFlagsCell(const std::vector<std::string> &row, size_t index, uint16_t &flags)
{
    if (index >= row.size())
    {
        return false;
    }

    const std::string trimmed = trimCopy(row[index]);

    if (trimmed.empty() || trimmed == "0")
    {
        flags = 0;
        return true;
    }

    if (trimmed.starts_with("0x") || trimmed.starts_with("0X"))
    {
        return parseUInt16Cell(row, index, flags);
    }

    flags = 0;
    size_t tokenBegin = 0;

    while (tokenBegin < trimmed.size())
    {
        size_t tokenEnd = trimmed.find(',', tokenBegin);

        if (tokenEnd == std::string::npos)
        {
            tokenEnd = trimmed.size();
        }

        const std::string token = trimCopy(trimmed.substr(tokenBegin, tokenEnd - tokenBegin));

        if (!token.empty())
        {
            bool matched = false;
            const std::string normalizedToken = toLowerCopy(token);

            for (const FlagNameBit &flagNameBit : FlagNameBits)
            {
                if (toLowerCopy(std::string(flagNameBit.name)) == normalizedToken)
                {
                    flags |= flagNameBit.bit;
                    matched = true;
                    break;
                }
            }

            if (!matched)
            {
                char *pEnd = nullptr;
                const unsigned long parsed = std::strtoul(token.c_str(), &pEnd, 0);

                if (pEnd == nullptr || *pEnd != '\0' || parsed > std::numeric_limits<uint16_t>::max())
                {
                    return false;
                }

                flags |= static_cast<uint16_t>(parsed);
            }
        }

        tokenBegin = tokenEnd + 1;
    }

    return true;
}
}

bool ObjectTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    m_descriptionIdByObjectId.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (isCommentRow(row))
        {
            continue;
        }

        if (row.size() < 13)
        {
            return false;
        }

        ObjectEntry entry = {};
        entry.internalName = trimCopy(row[0]);
        const std::string spriteName = trimCopy(row[1]);

        if (!spriteName.empty() && toLowerCopy(spriteName) != "null")
        {
            entry.spriteName = spriteName;
        }

        uint16_t particleTrailRed = 0;
        uint16_t particleTrailGreen = 0;
        uint16_t particleTrailBlue = 0;

        if (!parseInt16Cell(row, 2, entry.objectId)
            || !parseInt16Cell(row, 3, entry.radius)
            || !parseInt16Cell(row, 4, entry.height)
            || !parseInt16Cell(row, 5, entry.lifetimeTicks)
            || !parseInt16Cell(row, 6, entry.speed)
            || !parseUInt16Cell(row, 7, entry.spriteId)
            || !parseUInt32Cell(row, 8, entry.particleTrailColor)
            || !parseUInt16Cell(row, 9, particleTrailRed)
            || !parseUInt16Cell(row, 10, particleTrailGreen)
            || !parseUInt16Cell(row, 11, particleTrailBlue))
        {
            return false;
        }

        if (particleTrailRed > std::numeric_limits<uint8_t>::max()
            || particleTrailGreen > std::numeric_limits<uint8_t>::max()
            || particleTrailBlue > std::numeric_limits<uint8_t>::max()
            )
        {
            return false;
        }

        entry.particleTrailRed = static_cast<uint8_t>(particleTrailRed);
        entry.particleTrailGreen = static_cast<uint8_t>(particleTrailGreen);
        entry.particleTrailBlue = static_cast<uint8_t>(particleTrailBlue);

        if (!parseFlagsCell(row, 12, entry.flags))
        {
            return false;
        }

        const uint16_t descriptionId = static_cast<uint16_t>(m_entries.size());
        m_entries.push_back(std::move(entry));
        m_descriptionIdByObjectId[m_entries.back().objectId] = descriptionId;
    }

    return !m_entries.empty();
}

const ObjectEntry *ObjectTable::get(uint16_t objectDescriptionId) const
{
    if (objectDescriptionId >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[objectDescriptionId];
}

const ObjectEntry *ObjectTable::findByObjectId(int16_t objectId) const
{
    const auto descriptionIt = m_descriptionIdByObjectId.find(objectId);

    if (descriptionIt == m_descriptionIdByObjectId.end())
    {
        return nullptr;
    }

    return get(descriptionIt->second);
}

std::optional<uint16_t> ObjectTable::findDescriptionIdByObjectId(int16_t objectId) const
{
    const auto descriptionIt = m_descriptionIdByObjectId.find(objectId);

    if (descriptionIt == m_descriptionIdByObjectId.end())
    {
        return std::nullopt;
    }

    return descriptionIt->second;
}
}
