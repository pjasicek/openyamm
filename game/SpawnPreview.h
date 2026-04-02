#pragma once

#include "game/tables/MonsterTable.h"
#include "game/tables/MapStats.h"

#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
struct SpawnPreview
{
    std::string typeName;
    std::string summary;
    std::string detail;
};

class SpawnPreviewResolver
{
public:
    static SpawnPreview describe(
        const MapStatsEntry &map,
        const MonsterTable *pMonsterTable,
        uint16_t typeId,
        uint16_t index,
        uint16_t attributes,
        uint32_t group
    );
};
}
