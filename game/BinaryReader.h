#pragma once

#include <cctype>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <type_traits>
#include <vector>

namespace OpenYAMM::Game
{
class ByteReader
{
public:
    explicit ByteReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    size_t size() const
    {
        return m_bytes.size();
    }

    bool canRead(size_t offset, size_t byteCount) const
    {
        if (offset > m_bytes.size())
        {
            return false;
        }

        return byteCount <= (m_bytes.size() - offset);
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

    bool readInt8(size_t offset, int8_t &value) const
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

    bool readUInt32(size_t offset, uint32_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    template <typename TInt>
    bool readInt32(size_t offset, TInt &value) const
        requires (std::is_signed_v<TInt> && sizeof(TInt) == sizeof(int32_t))
    {
        int32_t rawValue = 0;

        if (!canRead(offset, sizeof(rawValue)))
        {
            return false;
        }

        std::memcpy(&rawValue, m_bytes.data() + offset, sizeof(rawValue));

        value = rawValue;
        return true;
    }

    bool readInt64(size_t offset, int64_t &value) const
    {
        if (!canRead(offset, sizeof(value)))
        {
            return false;
        }

        std::memcpy(&value, m_bytes.data() + offset, sizeof(value));
        return true;
    }

    bool readBytes(size_t offset, size_t byteCount, std::vector<uint8_t> &target) const
    {
        if (!canRead(offset, byteCount))
        {
            return false;
        }

        target.assign(
            m_bytes.begin() + static_cast<ptrdiff_t>(offset),
            m_bytes.begin() + static_cast<ptrdiff_t>(offset + byteCount));
        return true;
    }

    bool matchesText(size_t offset, const char *pText) const
    {
        const size_t textLength = std::strlen(pText);

        if (!canRead(offset, textLength))
        {
            return false;
        }

        return std::memcmp(m_bytes.data() + offset, pText, textLength) == 0;
    }

    bool isZeroBlock(size_t offset, size_t byteCount) const
    {
        if (!canRead(offset, byteCount))
        {
            return false;
        }

        for (size_t index = 0; index < byteCount; ++index)
        {
            if (m_bytes[offset + index] != 0)
            {
                return false;
            }
        }

        return true;
    }

    std::string readFixedString(size_t offset, size_t maxLength, bool lowercase = false) const
    {
        if (!canRead(offset, maxLength))
        {
            return {};
        }

        std::string value;
        value.reserve(maxLength);

        for (size_t index = 0; index < maxLength; ++index)
        {
            char character = static_cast<char>(m_bytes[offset + index]);

            if (character == '\0')
            {
                break;
            }

            if (!std::isprint(static_cast<unsigned char>(character)))
            {
                break;
            }

            if (lowercase)
            {
                character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
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
