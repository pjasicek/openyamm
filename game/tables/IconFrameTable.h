#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class IconFrameFlag : uint16_t
{
    HasMore = 0x1,
    First = 0x4,
};

struct IconFrameEntry
{
    std::string animationName;
    std::string textureName;
    uint16_t flags = 0;
    int32_t frameLengthTicks = 0;
    int32_t animationLengthTicks = 0;
};

class IconFrameTable
{
public:
    bool loadRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<size_t> findAnimationIdByName(const std::string &animationName) const;
    const IconFrameEntry *getFrame(size_t animationId, uint32_t elapsedTicks) const;
    int32_t animationLengthTicks(size_t animationId) const;

private:
    static bool hasFlag(uint16_t flags, IconFrameFlag flag);

private:
    std::vector<IconFrameEntry> m_frames;
    std::unordered_map<std::string, size_t> m_animationIdByName;
};
}
