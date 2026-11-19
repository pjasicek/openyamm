#include "game/outdoor/OutdoorWaterDepthData.h"

#include "engine/ImageAssetLoader.h"
#include "game/maps/OutdoorTerrainTiles.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorTerrainMaterialConfig.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MapCells = OutdoorMapData::TerrainWidth;
constexpr int GridCells = MapCells - 1;
}

float OutdoorWaterDepthData::shoreDistance(float x, float y) const
{
    const float scale = float(shoreSize) / 65536.0f;
    const float u = std::clamp((x + 32768.0f) * scale - 0.5f, 0.0f, float(shoreSize - 1));
    const float v = std::clamp((32768.0f - y) * scale - 0.5f, 0.0f, float(shoreSize - 1));
    const int u0 = int(u);
    const int v0 = int(v);
    const auto at = [&](int column, int row)
    {
        return (float(shore[size_t(row) * shoreSize + column]) - 128.0f) / 127.0f * distanceRange;
    };
    const int u1 = std::min(u0 + 1, shoreSize - 1);
    const int v1 = std::min(v0 + 1, shoreSize - 1);
    return std::lerp(std::lerp(at(u0, v0), at(u1, v0), u - u0),
        std::lerp(at(u0, v1), at(u1, v1), u - u0), v - v0);
}

float OutdoorWaterDepthData::cellLevel(int cellX, int cellY, float u, float v) const
{
    std::array<float, 4> corners;
    float lowest = std::numeric_limits<float>::quiet_NaN();
    for (int corner = 0; corner < 4; ++corner)
    {
        const float level = levels[size_t((cellY + corner / 2) * MapCells + cellX + corner % 2)];
        corners[size_t(corner)] = level;
        if (std::isfinite(level) && (!std::isfinite(lowest) || level < lowest))
        {
            lowest = level;
        }
    }
    for (float &corner : corners)
    {
        corner = std::isfinite(corner) ? corner : lowest;
    }
    return std::lerp(std::lerp(corners[0], corners[1], u), std::lerp(corners[2], corners[3], u), v);
}

std::optional<float> OutdoorWaterDepthData::depth(float x, float y) const
{
    const float gridX = std::clamp((x + 32768.0f) / 512.0f, 0.0f, float(GridCells));
    const float gridY = std::clamp((32768.0f - y) / 512.0f, 0.0f, float(GridCells));
    const int cellX = std::min(int(gridX), GridCells - 1);
    const int cellY = std::min(int(gridY), GridCells - 1);
    if (otherLiquids[size_t(cellY * MapCells + cellX)] != 0)
    {
        return std::nullopt;
    }
    if (!std::isfinite(cellLevel(cellX, cellY, gridX - cellX, gridY - cellY)))
    {
        return std::nullopt;
    }
    // The renderer caps its hidden seabed below opaque water. That draw limit must not turn the sea into a ford.
    return std::max(0.0f, -shoreDistance(x, y) * seabedSlope);
}

std::optional<float> OutdoorWaterDepthData::movementHeight(float x, float y, bool waterWalk) const
{
    const std::optional<float> waterDepth = depth(x, y);
    if (!waterDepth || *waterDepth <= 0.0f)
    {
        return std::nullopt;
    }
    const float gridX = std::clamp((x + 32768.0f) / 512.0f, 0.0f, float(GridCells));
    const float gridY = std::clamp((32768.0f - y) / 512.0f, 0.0f, float(GridCells));
    const int cellX = std::min(int(gridX), GridCells - 1);
    const int cellY = std::min(int(gridY), GridCells - 1);
    const float level = cellLevel(cellX, cellY, gridX - cellX, gridY - cellY);
    return level - (waterWalk ? 0.0f : std::min(*waterDepth, WadingDepth));
}

OutdoorWaterDepthData buildOutdoorWaterDepthData(const OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, const OutdoorTerrainMaterialShore &shore,
    std::vector<uint8_t> encoded, int size)
{
    OutdoorWaterDepthData result;
    result.shore = std::move(encoded);
    result.shoreSize = size;
    result.distanceRange = shore.range;
    result.seabedSlope = shore.seabedSlope;
    result.renderedSeabedDepth = shore.seabedDepth;
    const auto cellTile = [&](int cellX, int cellY) -> const OutdoorTerrainTile &
    {
        return tiles[map.tileMap[size_t(cellY * MapCells + cellX)]];
    };
    result.otherLiquids.assign(size_t(MapCells) * MapCells, 0);
    for (int cellY = 0; cellY < GridCells; ++cellY)
    {
        for (int cellX = 0; cellX < GridCells; ++cellX)
        {
            const LiquidKind liquid = cellTile(cellX, cellY).liquid;
            result.otherLiquids[size_t(cellY * MapCells + cellX)] =
                liquid != LiquidKind::None && liquid != LiquidKind::Water;
        }
    }
    // Water level at every native vertex: the native height where an open-water cell touches it, carried over the
    // land side of shore cells and spread two cells further for shores away from open water and for the beaches.
    // Sloping rivers keep their slope.
    const float noLevel = std::numeric_limits<float>::quiet_NaN();
    std::vector<float> &levels = result.levels;
    levels.assign(size_t(MapCells) * MapCells, noLevel);
    const auto nativeVertex = [&](int x, int y)
    {
        return float(map.heightMap[size_t(y * MapCells + x)] * OutdoorMapData::TerrainHeightScale);
    };
    const auto cornerIndex = [](int cellX, int cellY, int corner)
    {
        return size_t((cellY + corner / 2) * MapCells + cellX + corner % 2);
    };
    for (int cellY = 0; cellY < GridCells; ++cellY)
    {
        for (int cellX = 0; cellX < GridCells; ++cellX)
        {
            const OutdoorTerrainTile &tile = cellTile(cellX, cellY);
            if (tile.valid && tile.liquid == LiquidKind::Water && !tile.transitionOverlay)
            {
                for (int corner = 0; corner < 4; ++corner)
                {
                    levels[cornerIndex(cellX, cellY, corner)] =
                        nativeVertex(cellX + corner % 2, cellY + corner / 2);
                }
            }
        }
    }
    for (int cellY = 0; cellY < GridCells; ++cellY)
    {
        for (int cellX = 0; cellX < GridCells; ++cellX)
        {
            const OutdoorTerrainTile &tile = cellTile(cellX, cellY);
            if (!tile.valid || tile.liquid != LiquidKind::Water || !tile.transitionOverlay)
            {
                continue;
            }
            float lowest = noLevel;
            for (int corner = 0; corner < 4; ++corner)
            {
                const float level = levels[cornerIndex(cellX, cellY, corner)];
                lowest = std::isnan(lowest) || level < lowest ? level : lowest;
            }
            // Shore cells away from open water take the nearby water's level from the spreading below.
            if (std::isnan(lowest))
            {
                continue;
            }
            for (int corner = 0; corner < 4; ++corner)
            {
                float &level = levels[cornerIndex(cellX, cellY, corner)];
                level = std::isnan(level) ? lowest : level;
            }
        }
    }
    for (int pass = 0; pass < 2; ++pass)
    {
        const std::vector<float> previous = levels;
        for (int y = 0; y < MapCells; ++y)
        {
            for (int x = 0; x < MapCells; ++x)
            {
                float &level = levels[size_t(y * MapCells + x)];
                for (int dy = -1; dy <= 1 && std::isnan(level); ++dy)
                {
                    for (int dx = -1; dx <= 1; ++dx)
                    {
                        const float neighbour = previous[size_t(std::clamp(y + dy, 0, MapCells - 1) * MapCells
                            + std::clamp(x + dx, 0, MapCells - 1))];
                        if (!std::isnan(neighbour) && (std::isnan(level) || neighbour < level))
                        {
                            level = neighbour;
                        }
                    }
                }
            }
        }
    }
    return result;
}

bool loadOutdoorWaterDepthData(const Engine::AssetFileSystem &assets, OutdoorMapData &map,
    const std::array<OutdoorTerrainTile, 256> &tiles, std::string &error)
{
    map.waterDepth.reset();
    const std::optional<OutdoorTerrainMaterialConfig> config = loadOutdoorTerrainMaterialConfig(assets, map, error);
    if (!config)
    {
        return false;
    }
    if (!config->shore)
    {
        return true;
    }
    const std::string path = config->directory + config->shore->file;
    Engine::BinaryAssetCache cache;
    const std::optional<Engine::ImagePixelsBgra> image = Engine::loadImageAssetPixelsBgra(assets, path, cache);
    const int size = MapCells * config->texelsPerCell;
    if (!image || image->width != size || image->height != size)
    {
        error = "terrain shore distance must be " + std::to_string(size) + " pixels square: " + path;
        return false;
    }
    std::vector<uint8_t> encoded(size_t(size) * size);
    for (size_t index = 0; index < encoded.size(); ++index)
    {
        encoded[index] = image->pixels[index * 4 + 2];
    }
    map.waterDepth = buildOutdoorWaterDepthData(map, tiles, *config->shore, std::move(encoded), size);
    return true;
}
}
