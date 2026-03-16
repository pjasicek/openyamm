#include "game/MonsterTable.h"

#include <algorithm>
#include <cctype>
#include <cstring>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MonsterRecordSize = 184;

class ByteReader
{
public:
    explicit ByteReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    bool canRead(size_t offset, size_t byteCount) const
    {
        if (offset > m_bytes.size())
        {
            return false;
        }

        return byteCount <= (m_bytes.size() - offset);
    }

    bool readUInt32(size_t offset, uint32_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readUInt16(size_t offset, uint16_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readInt16(size_t offset, int16_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    std::string readFixedString(size_t offset, size_t maxLength) const
    {
        if (!canRead(offset, maxLength))
        {
            return {};
        }

        std::string value;
        value.reserve(maxLength);

        for (size_t index = 0; index < maxLength; ++index)
        {
            const char character = static_cast<char>(m_bytes[offset + index]);

            if (character == '\0')
            {
                break;
            }

            if (!std::isprint(static_cast<unsigned char>(character)))
            {
                break;
            }

            value.push_back(character);
        }

        while (!value.empty() && value.back() == ' ')
        {
            value.pop_back();
        }

        return value;
    }

private:
    const std::vector<uint8_t> &m_bytes;
};

std::string toLowerCopy(const std::string &value)
{
    std::string lowered = value;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}
}

bool MonsterTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t entryCount = 0;

    if (!reader.readUInt32(0, entryCount))
    {
        return false;
    }

    const size_t expectedSize = sizeof(uint32_t) + static_cast<size_t>(entryCount) * MonsterRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_entries.clear();
    m_entries.reserve(entryCount);

    for (uint32_t index = 0; index < entryCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + static_cast<size_t>(index) * MonsterRecordSize;
        MonsterEntry entry = {};

        if (!reader.readUInt16(offset + 0x00, entry.height)
            || !reader.readUInt16(offset + 0x02, entry.radius)
            || !reader.readUInt16(offset + 0x04, entry.movementSpeed)
            || !reader.readInt16(offset + 0x06, entry.toHitRadius)
            || !reader.readUInt32(offset + 0x08, entry.tintColor)
            || !reader.readUInt16(offset + 0x0c, entry.soundSampleIds[0])
            || !reader.readUInt16(offset + 0x0e, entry.soundSampleIds[1])
            || !reader.readUInt16(offset + 0x10, entry.soundSampleIds[2])
            || !reader.readUInt16(offset + 0x12, entry.soundSampleIds[3]))
        {
            return false;
        }

        entry.internalName = reader.readFixedString(offset + 0x14, 32);

        for (size_t spriteIndex = 0; spriteIndex < entry.spriteNames.size(); ++spriteIndex)
        {
            entry.spriteNames[spriteIndex] = reader.readFixedString(offset + 0x54 + spriteIndex * 10, 10);
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool MonsterTable::loadDisplayNamesFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_displayNames.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3 || row[0].empty())
        {
            continue;
        }

        bool isNumericId = true;

        for (const char character : row[0])
        {
            if (!std::isdigit(static_cast<unsigned char>(character)))
            {
                isNumericId = false;
                break;
            }
        }

        if (!isNumericId || row[1].empty() || row[2].empty())
        {
            continue;
        }

        MonsterDisplayNameEntry entry = {};
        entry.id = std::stoi(row[0]);
        entry.displayName = row[1];
        entry.pictureName = toLowerCopy(row[2]);
        m_displayNames.push_back(std::move(entry));
    }

    return !m_displayNames.empty();
}

bool MonsterTable::loadUniqueNamesFromRows(const std::vector<std::vector<std::string>> &rows)
{
    size_t maxIndex = 0;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty())
        {
            continue;
        }

        bool isNumericId = true;

        for (const char character : row[0])
        {
            if (!std::isdigit(static_cast<unsigned char>(character)))
            {
                isNumericId = false;
                break;
            }
        }

        if (!isNumericId)
        {
            continue;
        }

        const size_t index = static_cast<size_t>(std::stoul(row[0]));
        maxIndex = std::max(maxIndex, index);
    }

    m_uniqueNames.clear();
    m_uniqueNames.resize(maxIndex + 1);

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty())
        {
            continue;
        }

        bool isNumericId = true;

        for (const char character : row[0])
        {
            if (!std::isdigit(static_cast<unsigned char>(character)))
            {
                isNumericId = false;
                break;
            }
        }

        if (!isNumericId)
        {
            continue;
        }

        const size_t index = static_cast<size_t>(std::stoul(row[0]));

        if (index < m_uniqueNames.size())
        {
            m_uniqueNames[index] = row[1];
        }
    }

    return !m_uniqueNames.empty();
}

const MonsterEntry *MonsterTable::findByInternalName(const std::string &internalName) const
{
    const std::string normalizedName = toLowerCopy(internalName);

    for (const MonsterEntry &entry : m_entries)
    {
        if (toLowerCopy(entry.internalName) == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}

const MonsterEntry *MonsterTable::findById(int16_t monsterId) const
{
    if (monsterId < 0)
    {
        return nullptr;
    }

    const size_t index = static_cast<size_t>(monsterId);

    if (index >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[index];
}

const MonsterTable::MonsterDisplayNameEntry *MonsterTable::findDisplayEntryById(int id) const
{
    for (const MonsterDisplayNameEntry &entry : m_displayNames)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::optional<std::string> MonsterTable::findDisplayNameByInternalName(const std::string &internalName) const
{
    const std::string normalizedName = toLowerCopy(internalName);

    for (const MonsterDisplayNameEntry &entry : m_displayNames)
    {
        if (entry.pictureName == normalizedName)
        {
            return entry.displayName;
        }
    }

    return std::nullopt;
}

std::optional<std::string> MonsterTable::getUniqueName(int32_t uniqueNameIndex) const
{
    if (uniqueNameIndex <= 0)
    {
        return std::nullopt;
    }

    const size_t index = static_cast<size_t>(uniqueNameIndex);

    if (index >= m_uniqueNames.size() || m_uniqueNames[index].empty())
    {
        return std::nullopt;
    }

    return m_uniqueNames[index];
}

const std::vector<MonsterEntry> &MonsterTable::getEntries() const
{
    return m_entries;
}
}
