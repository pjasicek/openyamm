#include "game/outdoor/OutdoorDistantSea.h"

#include "game/maps/OutdoorTerrainTiles.h"
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
    const OutdoorMapData &mapData, const std::vector<uint8_t> &landMask, const OutdoorTerrainTiles *pTerrainTiles)
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
    std::array<int, 4> sideVoid = {};
    std::array<int, 4> sideAll = {};
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

            const bool voidCell = !mapData.voidCells.empty()
                && mapData.voidCells[size_t(y) * OutdoorMapData::TerrainWidth + size_t(x)] != 0;

            for (size_t side = 0; side < onSide.size(); ++side)
            {
                sideAll[side] += onSide[side] ? 1 : 0;
                sideVoid[side] += onSide[side] && voidCell ? 1 : 0;
            }

            if (voidCell)
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

            if (pTerrainTiles != nullptr && sample < mapData.tileMap.size())
            {
                const uint32_t abgr = pTerrainTiles->tiles[mapData.tileMap[sample]].waterColorAbgr;

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

    const auto shareWeight = [](int count, int total)
    {
        const float share = float(count) / float(std::max(total, 1));
        const float ramp = std::clamp((share - NoSeaShare) / (FullSeaShare - NoSeaShare), 0.0f, 1.0f);
        return ramp * ramp * (3.0f - 2.0f * ramp);
    };

    for (size_t side = 0; side < sea.voidWeights.size(); ++side)
    {
        sea.voidWeights[side] = sideVoid[side] > 0 ? shareWeight(sideVoid[side], sideAll[side]) : 0.0f;
    }

    if (waterCells == 0)
    {
        return sea;
    }

    for (size_t side = 0; side < sea.sideWeights.size(); ++side)
    {
        // A side with void past it has no sea; its other cells measure the sea as before.
        sea.sideWeights[side] = sea.voidWeights[side] > 0.0f ? 0.0f : shareWeight(sideWater[side], sideCells[side]);
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
