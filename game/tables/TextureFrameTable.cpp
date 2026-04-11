#include "game/tables/TextureFrameTable.h"

#include "game/StringUtils.h"

#include <algorithm>
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

bool TextureFrameTable::loadRows(const std::vector<std::vector<std::string>> &rows)
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

        TextureFrameEntry entry = {};
        entry.textureName = row[0];
        entry.textureId = static_cast<int16_t>(std::stoi(row[1]));
        entry.frameLengthTicks = static_cast<int32_t>(std::stoi(row[2])) * 8;
        entry.animationLengthTicks = static_cast<int32_t>(std::stoi(row[3])) * 8;
        entry.flags = static_cast<uint16_t>(std::stoul(row[4], nullptr, 0));

        if (!entry.textureName.empty() && hasFlag(entry.flags, TextureFrameFlag::First))
        {
            m_animationIdByName[toLowerCopy(entry.textureName)] = m_frames.size();
        }

        m_frames.push_back(std::move(entry));
    }

    return !m_frames.empty();
}

std::optional<size_t> TextureFrameTable::findAnimationIdByName(std::string_view textureName) const
{
    const std::unordered_map<std::string, size_t>::const_iterator animationIt =
        m_animationIdByName.find(toLowerCopy(std::string(textureName)));

    if (animationIt == m_animationIdByName.end())
    {
        return std::nullopt;
    }

    return animationIt->second;
}

std::optional<SurfaceAnimationSequence> TextureFrameTable::findAnimationSequenceByName(std::string_view textureName) const
{
    const std::optional<size_t> animationId = findAnimationIdByName(textureName);

    if (!animationId)
    {
        return std::nullopt;
    }

    return buildSequence(*animationId);
}

std::optional<SurfaceAnimationSequence> TextureFrameTable::findAnimationSequenceByIndex(size_t frameIndex) const
{
    const std::optional<size_t> firstFrameIndex = firstFrameIndexFor(frameIndex);

    if (!firstFrameIndex)
    {
        return std::nullopt;
    }

    return buildSequence(*firstFrameIndex);
}

bool TextureFrameTable::hasFlag(uint16_t flags, TextureFrameFlag flag)
{
    return (flags & static_cast<uint16_t>(flag)) != 0;
}

std::optional<size_t> TextureFrameTable::firstFrameIndexFor(size_t frameIndex) const
{
    if (frameIndex >= m_frames.size())
    {
        return std::nullopt;
    }

    size_t candidateIndex = frameIndex;

    while (candidateIndex > 0 && !hasFlag(m_frames[candidateIndex].flags, TextureFrameFlag::First))
    {
        --candidateIndex;
    }

    if (!hasFlag(m_frames[candidateIndex].flags, TextureFrameFlag::First))
    {
        return std::nullopt;
    }

    return candidateIndex;
}

SurfaceAnimationSequence TextureFrameTable::buildSequence(size_t firstFrameIndex) const
{
    SurfaceAnimationSequence sequence = {};

    if (firstFrameIndex >= m_frames.size())
    {
        return sequence;
    }

    sequence.animationLengthTicks = static_cast<uint32_t>(std::max(m_frames[firstFrameIndex].animationLengthTicks, 0));

    size_t frameIndex = firstFrameIndex;

    while (frameIndex < m_frames.size())
    {
        const TextureFrameEntry &frame = m_frames[frameIndex];
        SurfaceAnimationFrame animationFrame = {};
        animationFrame.textureName = frame.textureName;
        animationFrame.frameLengthTicks = static_cast<uint32_t>(std::max(frame.frameLengthTicks, 0));
        sequence.frames.push_back(std::move(animationFrame));

        if (!hasFlag(frame.flags, TextureFrameFlag::HasMore))
        {
            break;
        }

        ++frameIndex;
    }

    if (sequence.frames.size() == 1 && sequence.animationLengthTicks == 0)
    {
        sequence.animationLengthTicks = sequence.frames.front().frameLengthTicks;
    }

    return sequence;
}
} // namespace OpenYAMM::Game
