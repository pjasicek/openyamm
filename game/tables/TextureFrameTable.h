#pragma once

#include "game/tables/SurfaceAnimation.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class TextureFrameFlag : uint16_t
{
    HasMore = 0x0001,
    First = 0x0002,
};

struct TextureFrameEntry
{
    std::string textureName;
    int16_t textureId = 0;
    int32_t frameLengthTicks = 0;
    int32_t animationLengthTicks = 0;
    uint16_t flags = 0;
};

class TextureFrameTable
{
public:
    bool loadRows(const std::vector<std::vector<std::string>> &rows);

    std::optional<size_t> findAnimationIdByName(std::string_view textureName) const;
    std::optional<SurfaceAnimationSequence> findAnimationSequenceByName(std::string_view textureName) const;
    std::optional<SurfaceAnimationSequence> findAnimationSequenceByIndex(size_t frameIndex) const;

    static bool hasFlag(uint16_t flags, TextureFrameFlag flag);

private:
    std::optional<size_t> firstFrameIndexFor(size_t frameIndex) const;
    SurfaceAnimationSequence buildSequence(size_t firstFrameIndex) const;

    std::vector<TextureFrameEntry> m_frames;
    std::unordered_map<std::string, size_t> m_animationIdByName;
};
} // namespace OpenYAMM::Game
