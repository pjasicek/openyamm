#include "game/ObjectTable.h"
#include "game/BinaryReader.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ObjectRecordSize = 56;

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
}

bool ObjectTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    ByteReader reader(bytes);
    uint32_t entryCount = 0;

    if (!reader.readUInt32(0, entryCount))
    {
        return false;
    }

    const size_t expectedSize = sizeof(uint32_t) + size_t(entryCount) * ObjectRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_entries.clear();
    m_entries.reserve(entryCount);
    m_descriptionIdByObjectId.clear();

    for (uint32_t index = 0; index < entryCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + size_t(index) * ObjectRecordSize;
        ObjectEntry entry = {};

        if (!reader.readInt16(offset + 0x20, entry.objectId)
            || !reader.readInt16(offset + 0x22, entry.radius)
            || !reader.readInt16(offset + 0x24, entry.height)
            || !reader.readUInt16(offset + 0x26, entry.flags)
            || !reader.readUInt16(offset + 0x28, entry.spriteId)
            || !reader.readInt16(offset + 0x2a, entry.lifetimeTicks)
            || !reader.readUInt32(offset + 0x2c, entry.particleTrailColor)
            || !reader.readInt16(offset + 0x30, entry.speed)
            || !reader.readUInt8(offset + 0x32, entry.particleTrailRed)
            || !reader.readUInt8(offset + 0x33, entry.particleTrailGreen)
            || !reader.readUInt8(offset + 0x34, entry.particleTrailBlue))
        {
            return false;
        }

        entry.internalName = reader.readFixedString(offset, 32);
        m_entries.push_back(std::move(entry));
        m_descriptionIdByObjectId[m_entries.back().objectId] = static_cast<uint16_t>(index);
    }

    return !m_entries.empty();
}

bool ObjectTable::loadDisplayRows(const std::vector<std::vector<std::string>> &rows)
{
    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3 || !isNumericString(row[2]))
        {
            continue;
        }

        const int16_t objectId = static_cast<int16_t>(std::stoi(row[2]));
        const auto descriptionIt = m_descriptionIdByObjectId.find(objectId);
        const std::string &internalName = row[0];
        const std::string &spriteName = row[1];

        if (descriptionIt == m_descriptionIdByObjectId.end())
        {
            ObjectEntry entry = {};
            entry.internalName = internalName;
            entry.objectId = objectId;

            if (!spriteName.empty() && spriteName != "null")
            {
                entry.spriteName = spriteName;
            }

            if (row.size() > 3 && isNumericString(row[3]))
            {
                entry.radius = static_cast<int16_t>(std::stoi(row[3]));
            }

            if (row.size() > 4 && isNumericString(row[4]))
            {
                entry.height = static_cast<int16_t>(std::stoi(row[4]));
            }

            if (row.size() > 5 && isNumericString(row[5]))
            {
                entry.speed = static_cast<int16_t>(std::stoi(row[5]));
            }

            if (row.size() > 6 && isNumericString(row[6]))
            {
                entry.lifetimeTicks = static_cast<int16_t>(std::stoi(row[6]));
            }

            const uint16_t descriptionId = static_cast<uint16_t>(m_entries.size());
            m_entries.push_back(std::move(entry));
            m_descriptionIdByObjectId[objectId] = descriptionId;
            continue;
        }

        ObjectEntry &entry = m_entries[descriptionIt->second];

        if (!internalName.empty())
        {
            entry.internalName = internalName;
        }

        if (!spriteName.empty() && spriteName != "null")
        {
            entry.spriteName = spriteName;
        }
    }

    return true;
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
