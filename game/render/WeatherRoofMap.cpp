#include "game/render/WeatherRoofMap.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
void WeatherRoofMap::reset(float minX, float minY, float maxX, float maxY, float cellSize, uint32_t maxCells)
{
    m_heights.clear();
    m_width = 0;
    m_height = 0;

    if (!(maxX > minX) || !(maxY > minY) || cellSize <= 0.0f || maxCells == 0)
    {
        return;
    }

    const float largestSide = std::max(maxX - minX, maxY - minY);
    m_cellSize = std::max(cellSize, largestSide / static_cast<float>(maxCells));
    m_originX = minX;
    m_originY = minY;
    m_width = std::min(maxCells, static_cast<uint32_t>(std::ceil((maxX - minX) / m_cellSize)) + 1);
    m_height = std::min(maxCells, static_cast<uint32_t>(std::ceil((maxY - minY) / m_cellSize)) + 1);
    m_heights.assign(static_cast<size_t>(m_width) * m_height, NoSurface);
}

void WeatherRoofMap::addTriangle(
    const std::array<float, 3> &a, const std::array<float, 3> &b, const std::array<float, 3> &c)
{
    if (m_heights.empty())
    {
        return;
    }

    // Twice the signed area seen from above; walls have none.
    const float area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);

    if (std::abs(area) < 1.0f)
    {
        return;
    }

    const float inverseCell = 1.0f / m_cellSize;
    const auto firstCell = [&](float minimum, float origin)
    {
        return static_cast<int64_t>(std::ceil((minimum - origin) * inverseCell - 0.5f));
    };
    const auto lastCell = [&](float maximum, float origin)
    {
        return static_cast<int64_t>(std::floor((maximum - origin) * inverseCell - 0.5f));
    };
    const int64_t x0 = std::max<int64_t>(0, firstCell(std::min({a[0], b[0], c[0]}), m_originX));
    const int64_t x1 = std::min<int64_t>(m_width - 1, lastCell(std::max({a[0], b[0], c[0]}), m_originX));
    const int64_t y0 = std::max<int64_t>(0, firstCell(std::min({a[1], b[1], c[1]}), m_originY));
    const int64_t y1 = std::min<int64_t>(m_height - 1, lastCell(std::max({a[1], b[1], c[1]}), m_originY));
    const float inverseArea = 1.0f / area;
    // A cell centre on a shared edge belongs to both triangles: no gap along a roof's seams.
    constexpr float EdgeTolerance = -1.0e-4f;

    for (int64_t y = y0; y <= y1; ++y)
    {
        const float py = m_originY + (static_cast<float>(y) + 0.5f) * m_cellSize;

        for (int64_t x = x0; x <= x1; ++x)
        {
            const float px = m_originX + (static_cast<float>(x) + 0.5f) * m_cellSize;
            const float weightA = ((b[0] - px) * (c[1] - py) - (c[0] - px) * (b[1] - py)) * inverseArea;
            const float weightB = ((c[0] - px) * (a[1] - py) - (a[0] - px) * (c[1] - py)) * inverseArea;
            const float weightC = 1.0f - weightA - weightB;

            if (weightA < EdgeTolerance || weightB < EdgeTolerance || weightC < EdgeTolerance)
            {
                continue;
            }

            float &cell = m_heights[static_cast<size_t>(y) * m_width + static_cast<size_t>(x)];
            cell = std::max(cell, weightA * a[2] + weightB * b[2] + weightC * c[2]);
        }
    }
}

float WeatherRoofMap::heightAt(float x, float y) const
{
    if (m_heights.empty())
    {
        return NoSurface;
    }

    const float cellX = std::floor((x - m_originX) / m_cellSize);
    const float cellY = std::floor((y - m_originY) / m_cellSize);

    if (cellX < 0.0f || cellY < 0.0f || cellX >= static_cast<float>(m_width) || cellY >= static_cast<float>(m_height))
    {
        return NoSurface;
    }

    return m_heights[static_cast<size_t>(cellY) * m_width + static_cast<size_t>(cellX)];
}

bool WeatherRoofMap::covers(float x, float y, float z, float margin) const
{
    return z + margin < heightAt(x, y);
}
}
