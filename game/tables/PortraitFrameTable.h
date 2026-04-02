#pragma once

#include "game/tables/PortraitEnums.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class PortraitFrameFlag : uint16_t
{
    HasMore = 0x1,
};

struct PortraitFrameEntry
{
    PortraitId portraitId = PortraitId::Invalid;
    uint16_t textureIndex = 0;
    uint16_t flags = 0;
    int32_t frameLengthTicks = 0;
    int32_t animationLengthTicks = 0;
};

class PortraitFrameTable
{
public:
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    std::optional<size_t> findAnimationId(PortraitId portraitId) const;
    const PortraitFrameEntry *getFrame(PortraitId portraitId, uint32_t elapsedTicks) const;
    int32_t animationLengthTicks(PortraitId portraitId) const;

private:
    static bool hasFlag(uint16_t flags, PortraitFrameFlag flag);

private:
    std::vector<PortraitFrameEntry> m_frames;
    std::unordered_map<uint16_t, size_t> m_animationIdByPortraitId;
};
}
