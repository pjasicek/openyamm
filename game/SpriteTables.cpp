#include "game/SpriteTables.h"
#include "game/BinaryReader.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t DecorationRecordSize = 84;
constexpr size_t SpriteFrameRecordSize = 60;

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

}

bool DecorationTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t entryCount = 0;

    if (!reader.readUInt32(0, entryCount))
    {
        return false;
    }

    const size_t expectedSize =
        sizeof(uint32_t) + static_cast<size_t>(entryCount) * DecorationRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_entries.clear();
    m_entries.reserve(entryCount);

    for (uint32_t index = 0; index < entryCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + static_cast<size_t>(index) * DecorationRecordSize;
        DecorationEntry entry = {};

        entry.internalName = reader.readFixedString(offset + 0x00, 32, true);
        entry.hint = reader.readFixedString(offset + 0x20, 32, true);

        if (!reader.readInt16(offset + 0x40, entry.type)
            || !reader.readUInt16(offset + 0x42, entry.height)
            || !reader.readInt16(offset + 0x44, entry.radius)
            || !reader.readInt16(offset + 0x46, entry.lightRadius)
            || !reader.readUInt16(offset + 0x48, entry.spriteId)
            || !reader.readUInt16(offset + 0x4a, entry.flags)
            || !reader.readInt16(offset + 0x4c, entry.soundId))
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
