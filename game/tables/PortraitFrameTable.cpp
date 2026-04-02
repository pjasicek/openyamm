#include "game/tables/PortraitFrameTable.h"

#include "game/BinaryReader.h"

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t PortraitFrameRecordSize = 10;
}

bool PortraitFrameTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t frameCount = 0;

    if (!reader.readUInt32(0, frameCount))
    {
        return false;
    }

    const size_t expectedSize = sizeof(uint32_t) + static_cast<size_t>(frameCount) * PortraitFrameRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_frames.clear();
    m_animationIdByPortraitId.clear();
    m_frames.reserve(frameCount);

    for (uint32_t index = 0; index < frameCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + static_cast<size_t>(index) * PortraitFrameRecordSize;
        PortraitFrameEntry entry = {};
        uint16_t portraitId = 0;
        int16_t frameLength = 0;
        int16_t animationLength = 0;

        if (!reader.readUInt16(offset + 0x00, portraitId)
            || !reader.readUInt16(offset + 0x02, entry.textureIndex)
            || !reader.readInt16(offset + 0x04, frameLength)
            || !reader.readInt16(offset + 0x06, animationLength)
            || !reader.readUInt16(offset + 0x08, entry.flags))
        {
            return false;
        }

        entry.portraitId = static_cast<PortraitId>(portraitId);
        entry.frameLengthTicks = static_cast<int32_t>(frameLength) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(animationLength) * 8;

        if (entry.portraitId != PortraitId::Invalid)
        {
            m_animationIdByPortraitId[portraitId] = m_frames.size();
        }

        m_frames.push_back(entry);
    }

    return !m_frames.empty();
}

std::optional<size_t> PortraitFrameTable::findAnimationId(PortraitId portraitId) const
{
    const auto animationIt = m_animationIdByPortraitId.find(static_cast<uint16_t>(portraitId));

    if (animationIt == m_animationIdByPortraitId.end())
    {
        return std::nullopt;
    }

    return animationIt->second;
}

const PortraitFrameEntry *PortraitFrameTable::getFrame(PortraitId portraitId, uint32_t elapsedTicks) const
{
    const std::optional<size_t> animationId = findAnimationId(portraitId);

    if (!animationId || *animationId >= m_frames.size())
    {
        return nullptr;
    }

    const PortraitFrameEntry *pFirstFrame = &m_frames[*animationId];

    if (!hasFlag(pFirstFrame->flags, PortraitFrameFlag::HasMore) || pFirstFrame->animationLengthTicks <= 0)
    {
        return pFirstFrame;
    }

    uint32_t localTicks = elapsedTicks % static_cast<uint32_t>(pFirstFrame->animationLengthTicks);
    size_t frameIndex = *animationId;

    while (frameIndex < m_frames.size())
    {
        const PortraitFrameEntry &frame = m_frames[frameIndex];

        if (frame.frameLengthTicks <= 0 || localTicks < static_cast<uint32_t>(frame.frameLengthTicks))
        {
            return &frame;
        }

        localTicks -= static_cast<uint32_t>(frame.frameLengthTicks);

        if (!hasFlag(frame.flags, PortraitFrameFlag::HasMore))
        {
            return &frame;
        }

        ++frameIndex;
    }

    return pFirstFrame;
}

int32_t PortraitFrameTable::animationLengthTicks(PortraitId portraitId) const
{
    const std::optional<size_t> animationId = findAnimationId(portraitId);

    if (!animationId || *animationId >= m_frames.size())
    {
        return 0;
    }

    return m_frames[*animationId].animationLengthTicks;
}

bool PortraitFrameTable::hasFlag(uint16_t flags, PortraitFrameFlag flag)
{
    return (flags & static_cast<uint16_t>(flag)) != 0;
}
}
