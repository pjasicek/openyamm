#include "game/outdoor/OutdoorDistantSea.h"

#include "game/maps/MapAssetLoader.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
// Cells measured along each side of the terrain grid.
constexpr int BorderCells = 3;
// Water share of a side's border below which no sea is drawn past it, and at which it is drawn fully.
constexpr float NoSeaShare = 0.4f;
constexpr float FullSeaShare = 0.8f;
constexpr std::array<float, 3> FallbackWaterColor = {0.18f, 0.27f, 0.32f};
}

OutdoorDistantSea measureOutdoorDistantSea(
    const OutdoorMapData &mapData, const std::vector<uint8_t> &landMask, const OutdoorTerrainTextureAtlas *pAtlas)
{
    constexpr int CellsWide = OutdoorMapData::TerrainWidth - 1;
    constexpr int CellsHigh = OutdoorMapData::TerrainHeight - 1;
    OutdoorDistantSea sea = {};

    if (mapData.noTerrain || landMask.size() != size_t(CellsWide) * size_t(CellsHigh)
        || mapData.heightMap.size() < size_t(OutdoorMapData::TerrainWidth) * size_t(OutdoorMapData::TerrainHeight))
    {
        return sea;
    }

    // Grid x grows east (+X) and grid y grows south (-Y); corner cells count for both of their sides.
    std::array<int, 4> sideCells = {};
    std::array<int, 4> sideWater = {};
    int waterCells = 0;
    float heightSum = 0.0f;
    std::array<float, 3> colorSum = {};
    int coloredCells = 0;

    for (int y = 0; y < CellsHigh; ++y)
    {
        for (int x = 0; x < CellsWide; ++x)
        {
            const std::array<bool, 4> onSide = {
                x < BorderCells, x >= CellsWide - BorderCells, y >= CellsHigh - BorderCells, y < BorderCells};

            if (!onSide[0] && !onSide[1] && !onSide[2] && !onSide[3])
            {
                continue;
            }

            const bool water = landMask[size_t(y) * CellsWide + size_t(x)] == 0;

            for (size_t side = 0; side < onSide.size(); ++side)
            {
                sideCells[side] += onSide[side] ? 1 : 0;
                sideWater[side] += onSide[side] && water ? 1 : 0;
            }

            if (!water)
            {
                continue;
            }

            ++waterCells;
            const size_t sample = size_t(y) * OutdoorMapData::TerrainWidth + size_t(x);
            heightSum += float(mapData.heightMap[sample]) * float(OutdoorMapData::TerrainHeightScale);

            if (pAtlas != nullptr && sample < mapData.tileMap.size())
            {
                const uint32_t abgr = pAtlas->tileRegions[mapData.tileMap[sample]].waterColorAbgr;

                if (abgr != 0)
                {
                    colorSum[0] += float(abgr & 0xffu) / 255.0f;
                    colorSum[1] += float((abgr >> 8) & 0xffu) / 255.0f;
                    colorSum[2] += float((abgr >> 16) & 0xffu) / 255.0f;
                    ++coloredCells;
                }
            }
        }
    }

    if (waterCells == 0)
    {
        return sea;
    }

    for (size_t side = 0; side < sea.sideWeights.size(); ++side)
    {
        const float share = float(sideWater[side]) / float(std::max(sideCells[side], 1));
        const float ramp = std::clamp((share - NoSeaShare) / (FullSeaShare - NoSeaShare), 0.0f, 1.0f);
        sea.sideWeights[side] = ramp * ramp * (3.0f - 2.0f * ramp);
    }

    sea.seaLevel = heightSum / float(waterCells);
    sea.waterColorDisplay = FallbackWaterColor;

    if (coloredCells > 0)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            sea.waterColorDisplay[channel] = colorSum[channel] / float(coloredCells);
        }
    }

    return sea;
}
}
