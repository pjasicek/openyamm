#include "engine/Utf8.h"

#include <algorithm>

namespace OpenYAMM::Engine
{
namespace
{
bool continuation(uint8_t value)
{
    return (value & 0xc0) == 0x80;
}
}

Utf8CodePoint nextUtf8CodePoint(std::string_view text, size_t &offset)
{
    if (offset >= text.size())
    {
        return {};
    }

    const size_t start = offset;
    const uint8_t first = static_cast<uint8_t>(text[offset]);
    uint32_t value = first;
    size_t length = 1;

    if (first >= 0xc2 && first <= 0xdf && offset + 1 < text.size()
        && continuation(static_cast<uint8_t>(text[offset + 1])))
    {
        value = ((first & 0x1f) << 6) | (static_cast<uint8_t>(text[offset + 1]) & 0x3f);
        length = 2;
    }
    else if (first >= 0xe0 && first <= 0xef && offset + 2 < text.size())
    {
        const uint8_t second = static_cast<uint8_t>(text[offset + 1]);
        const uint8_t third = static_cast<uint8_t>(text[offset + 2]);
        const bool validSecond = continuation(second) && (first != 0xe0 || second >= 0xa0)
            && (first != 0xed || second <= 0x9f);
        if (validSecond && continuation(third))
        {
            value = ((first & 0x0f) << 12) | ((second & 0x3f) << 6) | (third & 0x3f);
            length = 3;
        }
    }
    else if (first >= 0xf0 && first <= 0xf4 && offset + 3 < text.size())
    {
        const uint8_t second = static_cast<uint8_t>(text[offset + 1]);
        const uint8_t third = static_cast<uint8_t>(text[offset + 2]);
        const uint8_t fourth = static_cast<uint8_t>(text[offset + 3]);
        const bool validSecond = continuation(second) && (first != 0xf0 || second >= 0x90)
            && (first != 0xf4 || second <= 0x8f);
        if (validSecond && continuation(third) && continuation(fourth))
        {
            value = ((first & 0x07) << 18) | ((second & 0x3f) << 12)
                | ((third & 0x3f) << 6) | (fourth & 0x3f);
            length = 4;
        }
    }

    offset += length;
    return {value, start, length};
}

std::vector<Utf8CodePoint> decodeUtf8(std::string_view text)
{
    std::vector<Utf8CodePoint> result;
    result.reserve(text.size());

    size_t offset = 0;
    while (offset < text.size())
    {
        result.push_back(nextUtf8CodePoint(text, offset));
    }

    return result;
}

size_t utf8Length(std::string_view text)
{
    size_t length = 0;
    size_t offset = 0;
    while (offset < text.size())
    {
        nextUtf8CodePoint(text, offset);
        ++length;
    }
    return length;
}

void eraseLastUtf8CodePoint(std::string &text)
{
    if (text.empty())
    {
        return;
    }

    size_t offset = 0;
    size_t lastOffset = 0;
    while (offset < text.size())
    {
        lastOffset = offset;
        nextUtf8CodePoint(text, offset);
    }
    text.erase(lastOffset);
}

std::string truncateUtf8(std::string_view text, size_t maximumCodePoints)
{
    size_t offset = 0;
    for (size_t index = 0; index < maximumCodePoints && offset < text.size(); ++index)
    {
        nextUtf8CodePoint(text, offset);
    }
    return std::string(text.substr(0, offset));
}
}
