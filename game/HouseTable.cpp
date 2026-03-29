#include "game/HouseTable.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <limits>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
bool isNumericOnly(const std::string &value)
{
    return !value.empty()
        && std::all_of(
            value.begin(),
            value.end(),
            [](unsigned char character)
            {
                return std::isdigit(character) != 0;
            });
}

std::string normalizeVideoStem(const std::string &value)
{
    return isNumericOnly(value) ? "" : value;
}

int parseTrainingMaxLevel(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    if (value == "No Max" || value == "no max")
    {
        return std::numeric_limits<int>::max();
    }

    return std::atoi(value.c_str());
}
}

bool HouseTable::loadFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const std::string &name = row[5];

        if (name.empty())
        {
            continue;
        }

        HouseEntry entry = {};
        entry.id = static_cast<uint32_t>(parsedId);
        entry.proprietorPictureId =
            (row.size() > 8 && !row[8].empty()) ? std::strtoul(row[8].c_str(), nullptr, 10) : 0;
        entry.type = row.size() > 2 ? row[2] : "";
        entry.name = name;
        entry.videoName = row.size() > 4 ? normalizeVideoStem(row[4]) : "";
        entry.proprietorName = row.size() > 6 ? row[6] : "";
        entry.proprietorTitle = row.size() > 7 ? row[7] : "";
        entry.priceMultiplier =
            (row.size() > 12 && !row[12].empty()) ? std::strtof(row[12].c_str(), nullptr) : 0.0f;
        entry.skillPriceMultiplier =
            (row.size() > 13 && !row[13].empty()) ? std::strtof(row[13].c_str(), nullptr) : 0.0f;
        entry.stockRefreshDays = (row.size() > 15 && !row[15].empty()) ? std::atoi(row[15].c_str()) : 0;
        entry.trainingMaxLevel = row.size() > 17 ? parseTrainingMaxLevel(row[17]) : 0;
        entry.openHour = (row.size() > 18 && !row[18].empty()) ? std::atoi(row[18].c_str()) : 0;
        entry.closeHour = (row.size() > 19 && !row[19].empty()) ? std::atoi(row[19].c_str()) : 0;
        entry.enterText = row.size() > 23 ? row[23] : "";

        if (row.size() > 24 && !row[24].empty())
        {
            std::istringstream stream(row[24]);
            std::string token;

            while (std::getline(stream, token, ','))
            {
                token.erase(
                    std::remove_if(
                        token.begin(),
                        token.end(),
                        [](unsigned char character)
                        {
                            return std::isspace(character) != 0;
                        }
                    ),
                    token.end()
                );

                if (!token.empty())
                {
                    entry.offeredSkills.push_back(token);
                }
            }
        }

        m_entries[entry.id] = entry;
    }

    return !m_entries.empty();
}

bool HouseTable::loadAnimationRows(const std::vector<std::vector<std::string>> &rows)
{
    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 3 || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }

        char *pEnd = nullptr;
        const unsigned long parsedId = std::strtoul(row[0].c_str(), &pEnd, 10);

        if (pEnd == row[0].c_str() || *pEnd != '\0')
        {
            continue;
        }

        const uint32_t houseId = static_cast<uint32_t>(parsedId);
        HouseEntry &entry = m_entries[houseId];
        entry.id = houseId;
        entry.buildingName = row[2];
        if (row.size() > 4)
        {
            const std::string normalizedVideoStem = normalizeVideoStem(row[4]);

            if (!normalizedVideoStem.empty())
            {
                entry.videoName = normalizedVideoStem;
            }
        }
        entry.roomSoundId = (row.size() > 6 && !row[6].empty()) ? std::strtoul(row[6].c_str(), nullptr, 10) : 0;
        entry.residentNpcIds.clear();

        size_t startPosition = 0;

        while (startPosition <= row[3].size())
        {
            const size_t commaPosition = row[3].find(',', startPosition);
            const size_t tokenLength = (commaPosition == std::string::npos)
                ? (row[3].size() - startPosition)
                : (commaPosition - startPosition);
            const std::string token = row[3].substr(startPosition, tokenLength);

            if (!token.empty())
            {
                char *pTokenEnd = nullptr;
                const unsigned long parsedNpcId = std::strtoul(token.c_str(), &pTokenEnd, 10);

                if (pTokenEnd != token.c_str() && *pTokenEnd == '\0')
                {
                    entry.residentNpcIds.push_back(static_cast<uint32_t>(parsedNpcId));
                }
            }

            if (commaPosition == std::string::npos)
            {
                break;
            }

            startPosition = commaPosition + 1;
        }
    }

    return true;
}

std::optional<std::string> HouseTable::getName(uint32_t houseId) const
{
    const auto entryIt = m_entries.find(houseId);

    if (entryIt == m_entries.end())
    {
        return std::nullopt;
    }

    return entryIt->second.name;
}

const HouseEntry *HouseTable::get(uint32_t houseId) const
{
    const std::unordered_map<uint32_t, HouseEntry>::const_iterator entryIt = m_entries.find(houseId);

    if (entryIt == m_entries.end())
    {
        return nullptr;
    }

    return &entryIt->second;
}
}
