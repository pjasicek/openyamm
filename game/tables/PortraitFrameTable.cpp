#include "game/tables/PortraitFrameTable.h"

#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
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

bool PortraitFrameTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_frames.clear();
    m_animationIdByPortraitId.clear();
    m_frames.reserve(rows.size());

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 5 || !isNumericString(row[0]))
        {
            continue;
        }

        const uint16_t portraitId = static_cast<uint16_t>(std::stoul(row[0]));
        PortraitFrameEntry entry = {};
        entry.portraitId = static_cast<PortraitId>(portraitId);
        entry.textureIndex = static_cast<uint16_t>(std::stoul(row[1]));
        entry.frameLengthTicks = static_cast<int32_t>(std::stoi(row[2])) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(std::stoi(row[3])) * 8;
        entry.flags = static_cast<uint16_t>(std::stoul(row[4], nullptr, 0));

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
