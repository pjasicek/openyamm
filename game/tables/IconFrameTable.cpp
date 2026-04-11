#include "game/tables/IconFrameTable.h"

#include "game/StringUtils.h"

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

bool IconFrameTable::loadRows(const std::vector<std::vector<std::string>> &rows)
{
    m_frames.clear();
    m_animationIdByName.clear();
    m_frames.reserve(rows.size());

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 5 || !isNumericString(row[2]) || !isNumericString(row[3]))
        {
            continue;
        }

        IconFrameEntry entry = {};
        entry.animationName = row[0];
        entry.textureName = row[1];
        entry.frameLengthTicks = static_cast<int32_t>(std::stoi(row[2])) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(std::stoi(row[3])) * 8;
        entry.flags = static_cast<uint16_t>(std::stoul(row[4], nullptr, 0));

        if (!entry.animationName.empty() && hasFlag(entry.flags, IconFrameFlag::First))
        {
            m_animationIdByName[toLowerCopy(entry.animationName)] = m_frames.size();
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
