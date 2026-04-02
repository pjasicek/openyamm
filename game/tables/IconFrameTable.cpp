#include "game/tables/IconFrameTable.h"

#include "game/BinaryReader.h"
#include "game/StringUtils.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t IconFrameRecordSize = 32;
}

bool IconFrameTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t frameCount = 0;

    if (!reader.readUInt32(0, frameCount))
    {
        return false;
    }

    const size_t expectedSize = sizeof(uint32_t) + static_cast<size_t>(frameCount) * IconFrameRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_frames.clear();
    m_animationIdByName.clear();
    m_frames.reserve(frameCount);

    for (uint32_t index = 0; index < frameCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + static_cast<size_t>(index) * IconFrameRecordSize;
        IconFrameEntry entry = {};
        int16_t frameLength = 0;
        int16_t animationLength = 0;

        entry.animationName = reader.readFixedString(offset + 0x00, 12, true);
        entry.textureName = reader.readFixedString(offset + 0x0c, 12, true);

        if (!reader.readInt16(offset + 0x18, frameLength)
            || !reader.readInt16(offset + 0x1a, animationLength)
            || !reader.readUInt16(offset + 0x1c, entry.flags))
        {
            return false;
        }

        entry.frameLengthTicks = static_cast<int32_t>(frameLength) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(animationLength) * 8;

        if (!entry.animationName.empty() && hasFlag(entry.flags, IconFrameFlag::First))
        {
            m_animationIdByName[entry.animationName] = m_frames.size();
        }

        m_frames.push_back(std::move(entry));
    }

    return !m_frames.empty();
}

std::optional<size_t> IconFrameTable::findAnimationIdByName(const std::string &animationName) const
{
    const auto animationIt = m_animationIdByName.find(toLowerCopy(animationName));

    if (animationIt == m_animationIdByName.end())
    {
        return std::nullopt;
    }

    return animationIt->second;
}

const IconFrameEntry *IconFrameTable::getFrame(size_t animationId, uint32_t elapsedTicks) const
{
    if (animationId >= m_frames.size())
    {
        return nullptr;
    }

    const IconFrameEntry *pFirstFrame = &m_frames[animationId];

    if (!hasFlag(pFirstFrame->flags, IconFrameFlag::HasMore) || pFirstFrame->animationLengthTicks <= 0)
    {
        return pFirstFrame;
    }

    uint32_t localTicks = elapsedTicks % static_cast<uint32_t>(pFirstFrame->animationLengthTicks);
    size_t frameIndex = animationId;

    while (frameIndex < m_frames.size())
    {
        const IconFrameEntry &frame = m_frames[frameIndex];

        if (frame.frameLengthTicks <= 0 || localTicks < static_cast<uint32_t>(frame.frameLengthTicks))
        {
            return &frame;
        }

        localTicks -= static_cast<uint32_t>(frame.frameLengthTicks);

        if (!hasFlag(frame.flags, IconFrameFlag::HasMore))
        {
            return &frame;
        }

        ++frameIndex;
    }

    return pFirstFrame;
}

int32_t IconFrameTable::animationLengthTicks(size_t animationId) const
{
    if (animationId >= m_frames.size())
    {
        return 0;
    }

    return m_frames[animationId].animationLengthTicks;
}

bool IconFrameTable::hasFlag(uint16_t flags, IconFrameFlag flag)
{
    return (flags & static_cast<uint16_t>(flag)) != 0;
}
}
