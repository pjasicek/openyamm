#include "game/tables/SpriteTables.h"
#include "game/BinaryReader.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t SpriteFrameRecordSize = 60;

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

int mirroredSourceOctant(int octant)
{
    static constexpr std::array<int, 8> MirroredOctants = {0, 7, 6, 5, 4, 3, 2, 1};
    return MirroredOctants[static_cast<size_t>(octant)];
}

void appendUnique(std::vector<std::string> &names, const std::string &name)
{
    if (name.empty())
    {
        return;
    }

    if (std::find(names.begin(), names.end(), name) == names.end())
    {
        names.push_back(name);
    }
}

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

    if (trimmed.empty() || trimmed.front() == '-')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 0);

    if (pEnd == nullptr || *pEnd != '\0' || parsed > std::numeric_limits<uint16_t>::max())
    {
        return false;
    }

    value = static_cast<uint16_t>(parsed);
    return true;
}

bool parseUInt8Cell(const std::vector<std::string> &row, size_t index, uint8_t &value)
{
    uint16_t parsed = 0;

    if (!parseUInt16Cell(row, index, parsed) || parsed > std::numeric_limits<uint8_t>::max())
    {
        return false;
    }

    value = static_cast<uint8_t>(parsed);
    return true;
}

bool parseDecorationFlagsCell(const std::vector<std::string> &row, size_t index, uint16_t &flags)
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

    if (isNumericString(trimmed) || trimmed.starts_with("0x") || trimmed.starts_with("0X"))
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

        const std::string token = toLowerCopy(trimCopy(trimmed.substr(tokenBegin, tokenEnd - tokenBegin)));

        if (!token.empty())
        {
            if (token == "movethrough")
            {
                flags |= 0x0001;
            }
            else if (token == "dontdraw" || token == "invisible")
            {
                flags |= 0x0002;
            }
            else if (token == "flickerslow")
            {
                flags |= 0x0004;
            }
            else if (token == "flickeraverage")
            {
                flags |= 0x0008;
            }
            else if (token == "flickerfast")
            {
                flags |= 0x0010;
            }
            else if (token == "marker")
            {
                flags |= 0x0020;
            }
            else if (token == "slowloop")
            {
                flags |= 0x0040;
            }
            else if (token == "emitfire")
            {
                flags |= 0x0080;
            }
            else if (token == "soundondawn")
            {
                flags |= 0x0100;
            }
            else if (token == "soundondusk")
            {
                flags |= 0x0200;
            }
            else if (token == "emitsmoke" || token == "emitsmoke")
            {
                flags |= 0x0400;
            }
            else
            {
                return false;
            }
        }

        tokenBegin = tokenEnd + 1;
    }

    return true;
}

}

bool DecorationTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();
    for (const std::vector<std::string> &row : rows)
    {
        if (row.empty() || !isNumericString(trimCopy(row[0])))
        {
            continue;
        }

        const int decorationNumber = std::stoi(trimCopy(row[0]));
        const int decorationId = decorationNumber - 1;

        if (decorationId < 0 || static_cast<size_t>(decorationId) != m_entries.size())
        {
            return false;
        }

        DecorationEntry entry = {};
        entry.internalName = row.size() > 1 ? toLowerCopy(trimCopy(row[1])) : std::string();
        entry.hint = row.size() > 2 ? trimCopy(row[2]) : std::string();

        if (!parseInt16Cell(row, 3, entry.type)
            || !parseInt16Cell(row, 4, entry.radius)
            || !parseUInt16Cell(row, 5, entry.height)
            || !parseInt16Cell(row, 6, entry.lightRadius)
            || !parseUInt8Cell(row, 7, entry.lightRed)
            || !parseUInt8Cell(row, 8, entry.lightGreen)
            || !parseUInt8Cell(row, 9, entry.lightBlue)
            || !parseInt16Cell(row, 10, entry.soundId)
            || !parseDecorationFlagsCell(row, 11, entry.flags)
            || !parseUInt16Cell(row, 12, entry.spriteId))
        {
            return false;
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

const DecorationEntry *DecorationTable::get(uint16_t decorationId) const
{
    if (decorationId >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[decorationId];
}

const DecorationEntry *DecorationTable::findByInternalName(const std::string &internalName) const
{
    std::string normalizedName;
    normalizedName.reserve(internalName.size());

    for (const char character : internalName)
    {
        normalizedName.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    while (!normalizedName.empty() && normalizedName.back() == ' ')
    {
        normalizedName.pop_back();
    }

    if (normalizedName.empty())
    {
        return nullptr;
    }

    for (const DecorationEntry &entry : m_entries)
    {
        if (entry.internalName == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool SpriteFrameTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t frameCount = 0;
    uint32_t eFrameCount = 0;

    if (!reader.readUInt32(0, frameCount) || !reader.readUInt32(4, eFrameCount))
    {
        return false;
    }

    const size_t expectedSize = 8
        + static_cast<size_t>(frameCount) * SpriteFrameRecordSize
        + static_cast<size_t>(eFrameCount) * sizeof(uint16_t);

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_frames.clear();
    m_frames.reserve(frameCount);

    for (uint32_t index = 0; index < frameCount; ++index)
    {
        const size_t offset = 8 + static_cast<size_t>(index) * SpriteFrameRecordSize;
        SpriteFrameEntry entry = {};
        int32_t scaleFixed = 0;
        int32_t flags = 0;
        int16_t frameLengthTicks = 0;
        int16_t animationLengthTicks = 0;

        entry.spriteName = reader.readFixedString(offset + 0x00, 12, true);
        entry.textureName = reader.readFixedString(offset + 0x0c, 12, true);

        if (!reader.readInt32(offset + 0x28, scaleFixed)
            || !reader.readInt32(offset + 0x2c, flags)
            || !reader.readInt16(offset + 0x30, entry.glowRadius)
            || !reader.readInt16(offset + 0x32, entry.paletteId)
            || !reader.readInt16(offset + 0x36, frameLengthTicks)
            || !reader.readInt16(offset + 0x38, animationLengthTicks))
        {
            return false;
        }

        entry.scale = static_cast<float>(scaleFixed) / 65536.0f;
        entry.flags = static_cast<uint32_t>(flags);
        entry.frameLengthTicks = static_cast<int32_t>(frameLengthTicks) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(animationLengthTicks) * 8;
        m_frames.push_back(std::move(entry));
    }

    m_eFrames.clear();
    m_eFrames.reserve(eFrameCount);

    for (uint32_t index = 0; index < eFrameCount; ++index)
    {
        uint16_t eFrame = 0;

        if (!reader.readUInt16(8 + static_cast<size_t>(frameCount) * SpriteFrameRecordSize + index * 2, eFrame))
        {
            return false;
        }

        m_eFrames.push_back(eFrame);
    }

    return !m_frames.empty();
}

const SpriteFrameEntry *SpriteFrameTable::getFrame(uint16_t spriteId, uint32_t timeTicks) const
{
    if (spriteId >= m_frames.size())
    {
        return nullptr;
    }

    const SpriteFrameEntry *pFrame = &m_frames[spriteId];

    if (!hasFlag(pFrame->flags, SpriteFrameFlag::HasMore) || pFrame->animationLengthTicks <= 0)
    {
        return pFrame;
    }

    uint32_t localTimeTicks = timeTicks % static_cast<uint32_t>(pFrame->animationLengthTicks);
    size_t frameIndex = spriteId;

    while (frameIndex < m_frames.size())
    {
        const SpriteFrameEntry &frame = m_frames[frameIndex];

        if (frame.frameLengthTicks <= 0 || localTimeTicks < static_cast<uint32_t>(frame.frameLengthTicks))
        {
            return &frame;
        }

        localTimeTicks -= static_cast<uint32_t>(frame.frameLengthTicks);

        if (!hasFlag(frame.flags, SpriteFrameFlag::HasMore))
        {
            return &frame;
        }

        ++frameIndex;
    }

    return pFrame;
}

std::vector<std::string> SpriteFrameTable::collectTextureNames(uint16_t spriteId) const
{
    std::vector<std::string> textureNames;

    if (spriteId >= m_frames.size())
    {
        return textureNames;
    }

    size_t frameIndex = spriteId;

    while (frameIndex < m_frames.size())
    {
        const SpriteFrameEntry &frame = m_frames[frameIndex];

        for (int octant = 0; octant < 8; ++octant)
        {
            const ResolvedSpriteTexture resolvedTexture = resolveTexture(frame, octant);
            appendUnique(textureNames, resolvedTexture.textureName);
        }

        if (!hasFlag(frame.flags, SpriteFrameFlag::HasMore))
        {
            break;
        }

        ++frameIndex;
    }

    return textureNames;
}

std::optional<uint16_t> SpriteFrameTable::findFrameIndexBySpriteName(const std::string &spriteName) const
{
    const std::string normalizedName = toLowerCopy(spriteName);

    for (size_t index = 0; index < m_frames.size(); ++index)
    {
        if (m_frames[index].spriteName == normalizedName)
        {
            return static_cast<uint16_t>(index);
        }
    }

    return std::nullopt;
}

ResolvedSpriteTexture SpriteFrameTable::resolveTexture(const SpriteFrameEntry &frame, int octant)
{
    const int clampedOctant = std::clamp(octant, 0, 7);
    ResolvedSpriteTexture resolvedTexture = {};
    const bool isMirrored = hasFlag(frame.flags, static_cast<SpriteFrameFlag>(mirrorFlagForOctant(clampedOctant)));
    resolvedTexture.mirrored = isMirrored;

    if (frame.textureName.empty())
    {
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Image1))
    {
        resolvedTexture.textureName = frame.textureName;
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Images3))
    {
        int sourceOctant = 0;

        if (clampedOctant == 3 || clampedOctant == 4 || clampedOctant == 5)
        {
            sourceOctant = 4;
        }
        else if (clampedOctant == 2 || clampedOctant == 6)
        {
            sourceOctant = 2;
        }

        resolvedTexture.textureName = buildTextureName(frame.textureName, sourceOctant);
        return resolvedTexture;
    }

    if (hasFlag(frame.flags, SpriteFrameFlag::Fidget))
    {
        if (clampedOctant == 0)
        {
            resolvedTexture.textureName = buildTextureName(frame.textureName, 0);
            return resolvedTexture;
        }

        if (clampedOctant == 4)
        {
            if (frame.textureName.size() >= 3)
            {
                resolvedTexture.textureName = frame.textureName.substr(0, frame.textureName.size() - 3) + "sta4";
            }

            return resolvedTexture;
        }

        if (clampedOctant == 3 || clampedOctant == 5)
        {
            if (frame.textureName.size() >= 3)
            {
                resolvedTexture.textureName = frame.textureName.substr(0, frame.textureName.size() - 3) + "sta3";
            }

            return resolvedTexture;
        }

        if (clampedOctant == 2 || clampedOctant == 6)
        {
            resolvedTexture.textureName = buildTextureName(frame.textureName, 2);
            return resolvedTexture;
        }

        resolvedTexture.textureName = buildTextureName(frame.textureName, 1);
        return resolvedTexture;
    }

    const int sourceOctant = isMirrored ? mirroredSourceOctant(clampedOctant) : clampedOctant;
    resolvedTexture.textureName = buildTextureName(frame.textureName, sourceOctant);
    return resolvedTexture;
}

bool SpriteFrameTable::hasFlag(uint32_t flags, SpriteFrameFlag flag)
{
    return (flags & static_cast<uint32_t>(flag)) != 0;
}

uint32_t SpriteFrameTable::mirrorFlagForOctant(int octant)
{
    return 0x100u << std::clamp(octant, 0, 7);
}

std::string SpriteFrameTable::buildTextureName(const std::string &baseName, int suffixIndex)
{
    if (baseName.size() >= 7)
    {
        return baseName;
    }

    return baseName + std::to_string(std::clamp(suffixIndex, 0, 7));
}
}
