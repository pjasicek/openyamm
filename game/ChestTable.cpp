#include "game/ChestTable.h"

#include <algorithm>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t RecordSize = 36;
constexpr size_t NameSize = 32;

std::string trim(const std::string &value)
{
    const size_t first = value.find_first_not_of(" \t\r\n");

    if (first == std::string::npos)
    {
        return {};
    }

    const size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::vector<std::string> splitTabSeparatedRow(const std::string &line)
{
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream stream(line);

    while (std::getline(stream, token, '\t'))
    {
        tokens.push_back(trim(token));
    }

    return tokens;
}

std::string readFixedString(const uint8_t *pData, size_t size)
{
    std::string value;
    value.reserve(size);

    for (size_t index = 0; index < size; ++index)
    {
        const char character = static_cast<char>(pData[index]);

        if (character == '\0')
        {
            break;
        }

        value.push_back(character);
    }

    return value;
}

std::string buildTextureName(int16_t textureId)
{
    if (textureId <= 0)
    {
        return {};
    }

    std::ostringstream stream;
    stream << "chest";

    if (textureId < 10)
    {
        stream << '0';
    }

    stream << textureId;
    return stream.str();
}
}

bool ChestTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    m_entries.clear();

    if (bytes.size() < sizeof(uint32_t))
    {
        return false;
    }

    uint32_t entryCount = 0;
    std::memcpy(&entryCount, bytes.data(), sizeof(entryCount));

    const size_t requiredSize = sizeof(uint32_t) + static_cast<size_t>(entryCount) * RecordSize;

    if (bytes.size() < requiredSize)
    {
        return false;
    }

    m_entries.reserve(entryCount);

    for (uint32_t entryIndex = 0; entryIndex < entryCount; ++entryIndex)
    {
        const uint8_t *pRecord = bytes.data() + sizeof(uint32_t) + static_cast<size_t>(entryIndex) * RecordSize;
        ChestEntry entry = {};
        entry.name = readFixedString(pRecord, NameSize);
        entry.width = pRecord[32];
        entry.height = pRecord[33];
        std::memcpy(&entry.textureId, pRecord + 34, sizeof(entry.textureId));
        entry.textureName = buildTextureName(entry.textureId);
        m_entries.push_back(std::move(entry));
    }

    return true;
}

bool ChestTable::loadUiLayoutFromText(const std::string &text)
{
    std::istringstream stream(text);
    std::string line;
    bool headerSkipped = false;

    while (std::getline(stream, line))
    {
        const std::string trimmedLine = trim(line);

        if (trimmedLine.empty() || trimmedLine[0] == '#')
        {
            continue;
        }

        if (!headerSkipped)
        {
            headerSkipped = true;
            continue;
        }

        const std::vector<std::string> columns = splitTabSeparatedRow(trimmedLine);

        if (columns.size() < 3)
        {
            return false;
        }

        const int chestTypeId = std::stoi(columns[0]);

        if (chestTypeId < 0 || static_cast<size_t>(chestTypeId) >= m_entries.size())
        {
            return false;
        }

        ChestEntry &entry = m_entries[chestTypeId];
        entry.gridOffsetX = static_cast<int16_t>(std::stoi(columns[1]));
        entry.gridOffsetY = static_cast<int16_t>(std::stoi(columns[2]));

        if (columns.size() >= 5)
        {
            entry.gridWidth = static_cast<uint8_t>(std::max(0, std::stoi(columns[3])));
            entry.gridHeight = static_cast<uint8_t>(std::max(0, std::stoi(columns[4])));
        }
    }

    return true;
}

const ChestEntry *ChestTable::get(uint16_t chestTypeId) const
{
    if (chestTypeId >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[chestTypeId];
}

const std::vector<ChestEntry> &ChestTable::getEntries() const
{
    return m_entries;
}
}
