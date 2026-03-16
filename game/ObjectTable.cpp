#include "game/ObjectTable.h"

#include <cctype>
#include <cstring>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t ObjectRecordSize = 56;

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

    bool readUInt8(size_t offset, uint8_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        value = m_bytes[offset];
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
            const char character = char(m_bytes[offset + index]);

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
}
