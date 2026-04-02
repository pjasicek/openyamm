#pragma once

#include "game/tables/PortraitEnums.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class PortraitFxEventKind : uint8_t
{
    None = 0,
    Disease,
    AwardGain,
    QuestComplete,
    StatIncrease,
    StatDecrease,
};

struct PortraitFxEventEntry
{
    PortraitFxEventKind kind = PortraitFxEventKind::None;
    std::string name;
    std::string animationName;
    std::optional<FaceAnimationId> faceAnimationId;
};

class PortraitFxEventTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const PortraitFxEventEntry *findByKind(PortraitFxEventKind kind) const;

private:
    std::vector<PortraitFxEventEntry> m_entries;
    std::unordered_map<PortraitFxEventKind, size_t> m_entryIndexByKind;
};
}
