#pragma once

#include "game/tables/PortraitEnums.h"

#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct FaceAnimationEntry
{
    FaceAnimationId animationId = FaceAnimationId::Damaged;
    std::string animationName;
    std::vector<PortraitId> portraitIds;
};

class FaceAnimationTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const FaceAnimationEntry *find(FaceAnimationId animationId) const;

private:
    std::vector<FaceAnimationEntry> m_entries;
    std::unordered_map<uint16_t, size_t> m_entryIndexByAnimationId;
};
}
