#include "game/outdoor/OutdoorMeadow.h"

#include "game/outdoor/OutdoorGeometryUtils.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr int Side = OutdoorMapData::TerrainWidth;

// Separable Gaussian blur of the corner grid (sigma in cells), clamped at the edges.
std::vector<float> blurred(const std::vector<float> &values, float sigma)
{
    const int radius = int(std::ceil(sigma * 3.0f));
    std::vector<float> kernel(size_t(radius) * 2 + 1);
    float total = 0.0f;
    for (int offset = -radius; offset <= radius; ++offset)
    {
        const float weight = std::exp(-0.5f * float(offset * offset) / (sigma * sigma));
        kernel[size_t(offset + radius)] = weight;
        total += weight;
    }
    for (float &weight : kernel)
    {
        weight /= total;
    }
    std::vector<float> result = values;
    std::vector<float> pass(values.size());
    for (int axis = 0; axis < 2; ++axis)
    {
        for (int row = 0; row < Side; ++row)
        {
            for (int column = 0; column < Side; ++column)
            {
                float sum = 0.0f;
                for (int offset = -radius; offset <= radius; ++offset)
                {
                    const int x = axis == 0 ? std::clamp(column + offset, 0, Side - 1) : column;
                    const int y = axis == 1 ? std::clamp(row + offset, 0, Side - 1) : row;
                    sum += result[size_t(y) * Side + x] * kernel[size_t(offset + radius)];
                }
                pass[size_t(row) * Side + column] = sum;
            }
        }
        result.swap(pass);
    }
    return result;
}

// Distance in cells from every corner to the nearest corner touching a water cell (two-pass 3-4 chamfer).
std::vector<float> waterDistance(const std::vector<uint8_t> &waterCells)
{
    constexpr float Far = 1.0e6f;
    std::vector<float> distance(size_t(Side) * Side, Far);
    for (int y = 0; y + 1 < Side; ++y)
    {
        for (int x = 0; x + 1 < Side; ++x)
        {
            if (waterCells[size_t(y) * Side + x] != 0)
            {
                for (int corner = 0; corner < 4; ++corner)
                {
                    distance[size_t(y + corner / 2) * Side + x + corner % 2] = 0.0f;
                }
            }
        }
    }
    const auto relax = [&](int x, int y, int dx, int dy, float cost)
    {
        const int nx = x + dx;
        const int ny = y + dy;
        if (nx >= 0 && ny >= 0 && nx < Side && ny < Side)
        {
            float &value = distance[size_t(y) * Side + x];
            value = std::min(value, distance[size_t(ny) * Side + nx] + cost);
        }
    };
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            relax(x, y, -1, 0, 3.0f);
            relax(x, y, 0, -1, 3.0f);
            relax(x, y, -1, -1, 4.0f);
            relax(x, y, 1, -1, 4.0f);
        }
    }
    for (int y = Side - 1; y >= 0; --y)
    {
        for (int x = Side - 1; x >= 0; --x)
        {
            relax(x, y, 1, 0, 3.0f);
            relax(x, y, 0, 1, 3.0f);
            relax(x, y, 1, 1, 4.0f);
            relax(x, y, -1, 1, 4.0f);
        }
    }
    for (float &value : distance)
    {
        value /= 3.0f;
    }
    return distance;
}

float smoothUnit(float value)
{
    value = std::clamp(value, 0.0f, 1.0f);
    return value * value * (3.0f - 2.0f * value);
}
}

float OutdoorMeadowField::sample(float x, float y) const
{
    if (values.size() != size_t(Side) * Side)
    {
        return 0.0f;
    }
    const float gridX = std::clamp(outdoorWorldToGridXFloat(x), 0.0f, float(Side - 1));
    const float gridY = std::clamp(outdoorWorldToGridYFloat(y), 0.0f, float(Side - 1));
    const int x0 = std::min(int(gridX), Side - 2);
    const int y0 = std::min(int(gridY), Side - 2);
    const float fx = gridX - float(x0);
    const float fy = gridY - float(y0);
    const auto at = [this](int column, int row)
    {
        return values[size_t(row) * Side + column];
    };
    return std::lerp(std::lerp(at(x0, y0), at(x0 + 1, y0), fx), std::lerp(at(x0, y0 + 1), at(x0 + 1, y0 + 1), fx),
        fy);
}

OutdoorMeadowField buildOutdoorMeadowField(const OutdoorMapData &map)
{
    if (map.noTerrain || map.heightMap.size() != size_t(Side) * Side)
    {
        return {};
    }
    std::vector<float> heights(size_t(Side) * Side);
    std::vector<uint8_t> waterCells(size_t(Side) * Side, 0);
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            heights[size_t(y) * Side + x] = outdoorNativeTerrainHeight(map, float(x), float(y));
            if (x + 1 < Side && y + 1 < Side)
            {
                const float centerX = outdoorGridCornerWorldX(x) + 0.5f * OutdoorMapData::TerrainTileSize;
                const float centerY = outdoorGridCornerWorldY(y) - 0.5f * OutdoorMapData::TerrainTileSize;
                waterCells[size_t(y) * Side + x] = isOutdoorTerrainWater(map, centerX, centerY) ? 1 : 0;
            }
        }
    }
    return buildMeadowField(heights, waterCells);
}

OutdoorMeadowField buildMeadowField(const std::vector<float> &heights, const std::vector<uint8_t> &waterCells)
{
    OutdoorMeadowField field;
    if (heights.size() != size_t(Side) * Side || waterCells.size() != heights.size())
    {
        return field;
    }
    // Relief against the surroundings at two scales: a knoll (about 1.5 cells) and a whole hill (about 5).
    const std::vector<float> near = blurred(heights, 3.0f);
    const std::vector<float> wide = blurred(heights, 10.0f);
    const std::vector<float> smooth = blurred(heights, 1.0f);
    const std::vector<float> water = waterDistance(waterCells);
    std::vector<float> values(heights.size());
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            const size_t index = size_t(y) * Side + x;
            const auto height = [&](int column, int row)
            {
                return smooth[size_t(std::clamp(row, 0, Side - 1)) * Side + std::clamp(column, 0, Side - 1)];
            };
            const float slope = std::hypot(height(x + 1, y) - height(x - 1, y), height(x, y + 1) - height(x, y - 1))
                / (2.0f * OutdoorMapData::TerrainTileSize);
            const float crest = std::clamp((heights[index] - near[index]) / 320.0f, -1.5f, 1.5f);
            const float hill = std::clamp((heights[index] - wide[index]) / 1000.0f, -1.5f, 1.5f);
            const float exposed = smoothUnit((slope - 0.15f) / 0.35f);
            const float shore = std::exp(-water[index] / 2.5f);
            const float dryness = 0.55f * crest + 0.35f * hill + 0.5f * exposed - shore;
            // Soft saturation: strong relief and open water both approach the ends of the range.
            values[index] = std::clamp(1.5f * dryness / (1.0f + std::abs(dryness)), -1.0f, 1.0f);
        }
    }
    field.values = blurred(values, 1.0f);
    return field;
}

std::array<float, 3> outdoorMeadowTint(float meadow, const std::array<float, 3> &dry, const std::array<float, 3> &lush,
    float strength)
{
    const std::array<float, 3> &target = meadow > 0.0f ? dry : lush;
    const float amount = std::min(std::abs(meadow) * strength, 1.0f);
    return {std::lerp(1.0f, target[0], amount), std::lerp(1.0f, target[1], amount),
        std::lerp(1.0f, target[2], amount)};
}
} // namespace OpenYAMM::Game
