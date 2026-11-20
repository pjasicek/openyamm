#pragma once

#include "game/render/LiquidKind.h"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// Per raw tile id of an outdoor map: how its native terrain tile takes part (land, a liquid, or an edge over a
// liquid). The ground is drawn from the map's materials (OutdoorTerrainMaterials); no tile art is loaded.
struct OutdoorTerrainTile
{
    std::string textureName;
    // Used by the map's cells and named in the tile table.
    bool valid = false;
    bool water = false;
    // Drawn by the liquid shader (water, tar or lava).
    bool waterSurface = false;
    // An edge tile over a liquid: its coverage mask is where the liquid shows.
    bool transitionOverlay = false;
    LiquidKind liquid = LiquidKind::None;
    // The liquid's colour (ABGR); see LiquidDefinition::colorAbgr.
    uint32_t waterColorAbgr = 0;
    // See LiquidDefinition::reflects.
    bool liquidReflects = true;
};

struct OutdoorTerrainTiles
{
    std::array<OutdoorTerrainTile, 256> tiles = {};
    // Per liquid edge tile: WaterCoverageSize x WaterCoverageSize liquid coverage (255 all liquid), cooked by
    // tools/terrain_materials.py from the native tile's alpha. Empty for every other tile.
    std::array<std::vector<uint8_t>, 256> liquidCoverageMasks;
};
}
