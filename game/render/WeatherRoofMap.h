#pragma once

#include <array>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
// Seen from the sky, the height of the highest surface over each cell of a map: rain and snow fall only above it (a
// roof, a bridge, the terrain over a tunnel), and a camera below it is under cover. Built once per map from its
// surfaces (devdocs/INDOOR_OPEN_SKY.md "Weather"); the weather shader hides drops below it.
class WeatherRoofMap
{
public:
    // A cell no surface covers (off the map's surfaces, or only walls).
    static constexpr float NoSurface = -1.0e9f;

    // An empty grid over the rectangle, at most maxCells cells a side (the cells grow to fit).
    void reset(float minX, float minY, float maxX, float maxY, float cellSize, uint32_t maxCells);
    // A surface triangle: it raises every cell whose centre lies inside it (seen from above) to its height there.
    // Walls (no area seen from above) change nothing.
    void addTriangle(const std::array<float, 3> &a, const std::array<float, 3> &b, const std::array<float, 3> &c);
    // The highest surface over the point, NoSurface where there is none.
    float heightAt(float x, float y) const;
    // Whether the point is under a surface (more than margin below it).
    bool covers(float x, float y, float z, float margin) const;

    bool empty() const
    {
        return m_heights.empty();
    }
    uint32_t width() const
    {
        return m_width;
    }
    uint32_t height() const
    {
        return m_height;
    }
    float originX() const
    {
        return m_originX;
    }
    float originY() const
    {
        return m_originY;
    }
    float cellSize() const
    {
        return m_cellSize;
    }
    // Row-major, y rows of width cells from the origin.
    const std::vector<float> &heights() const
    {
        return m_heights;
    }

private:
    float m_originX = 0.0f;
    float m_originY = 0.0f;
    float m_cellSize = 1.0f;
    uint32_t m_width = 0;
    uint32_t m_height = 0;
    std::vector<float> m_heights;
};
}
