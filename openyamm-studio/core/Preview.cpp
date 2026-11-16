#include "core/Preview.h"

#include "core/CoreMath.h"
#include "core/OutdoorBuildings.h"

#include "core/Json.h"
#include "core/Polygon.h"
#include "core/Sketch.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <map>
#include <optional>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
struct Color
{
    uint8_t red = 0;
    uint8_t green = 0;
    uint8_t blue = 0;
};

struct Point
{
    double x = 0.0;
    double y = 0.0;
};

// 5 by 7 glyphs for the labels: digits and the few letters labels use. One byte per row, bit 4 the left column.
const std::map<char, std::array<uint8_t, 7>> &glyphs()
{
    static const std::map<char, std::array<uint8_t, 7>> table = {
        {'0', {0x0e, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0e}}, {'1', {0x04, 0x0c, 0x04, 0x04, 0x04, 0x04, 0x0e}},
        {'2', {0x0e, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1f}}, {'3', {0x1f, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0e}},
        {'4', {0x02, 0x06, 0x0a, 0x12, 0x1f, 0x02, 0x02}}, {'5', {0x1f, 0x10, 0x1e, 0x01, 0x01, 0x11, 0x0e}},
        {'6', {0x06, 0x08, 0x10, 0x1e, 0x11, 0x11, 0x0e}}, {'7', {0x1f, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08}},
        {'8', {0x0e, 0x11, 0x11, 0x0e, 0x11, 0x11, 0x0e}}, {'9', {0x0e, 0x11, 0x11, 0x0f, 0x01, 0x02, 0x0c}},
        {'d', {0x01, 0x01, 0x0d, 0x13, 0x11, 0x13, 0x0d}}, {'s', {0x00, 0x00, 0x0e, 0x10, 0x0e, 0x01, 0x1e}},
        {'b', {0x10, 0x10, 0x16, 0x19, 0x11, 0x19, 0x16}}, {'S', {0x0f, 0x10, 0x10, 0x0e, 0x01, 0x01, 0x1e}},
        {'X', {0x11, 0x11, 0x0a, 0x04, 0x0a, 0x11, 0x11}}, {'e', {0x00, 0x00, 0x0e, 0x11, 0x1f, 0x10, 0x0e}},
    };
    return table;
}

class Canvas
{
public:
    Canvas(int width, int height, Color background)
    {
        m_image.width = width;
        m_image.height = height;
        m_image.pixels.resize(static_cast<size_t>(width) * height * 3);

        for (size_t index = 0; index < m_image.pixels.size(); index += 3)
        {
            m_image.pixels[index] = background.red;
            m_image.pixels[index + 1] = background.green;
            m_image.pixels[index + 2] = background.blue;
        }
    }

    void set(int x, int y, Color color)
    {
        if (x < 0 || y < 0 || x >= m_image.width || y >= m_image.height)
        {
            return;
        }

        const size_t offset = (static_cast<size_t>(y) * m_image.width + x) * 3;
        m_image.pixels[offset] = color.red;
        m_image.pixels[offset + 1] = color.green;
        m_image.pixels[offset + 2] = color.blue;
    }

    // Scanline fill of any simple polygon (even-odd).
    void fill(const std::vector<Point> &polygon, Color color)
    {
        if (polygon.size() < 3)
        {
            return;
        }

        double top = polygon[0].y;
        double bottom = polygon[0].y;

        for (const Point &point : polygon)
        {
            top = std::min(top, point.y);
            bottom = std::max(bottom, point.y);
        }

        const int firstRow = std::max(0, static_cast<int>(std::ceil(top - 0.5)));
        const int lastRow = std::min(m_image.height - 1, static_cast<int>(std::floor(bottom - 0.5)));
        std::vector<double> crossings;

        for (int row = firstRow; row <= lastRow; ++row)
        {
            const double y = row + 0.5;
            crossings.clear();

            for (size_t index = 0; index < polygon.size(); ++index)
            {
                const Point &first = polygon[index];
                const Point &second = polygon[(index + 1) % polygon.size()];

                if ((first.y <= y && second.y > y) || (second.y <= y && first.y > y))
                {
                    crossings.push_back(first.x + (y - first.y) / (second.y - first.y) * (second.x - first.x));
                }
            }

            std::sort(crossings.begin(), crossings.end());

            for (size_t index = 0; index + 1 < crossings.size(); index += 2)
            {
                const int from = std::max(0, static_cast<int>(std::ceil(crossings[index] - 0.5)));
                const int to = std::min(m_image.width - 1, static_cast<int>(std::floor(crossings[index + 1] - 0.5)));

                for (int column = from; column <= to; ++column)
                {
                    set(column, row, color);
                }
            }
        }
    }

    void line(Point from, Point to, Color color, int thickness = 1)
    {
        const double length = std::max(std::fabs(to.x - from.x), std::fabs(to.y - from.y));
        const int steps = std::max(1, static_cast<int>(std::ceil(length)));

        for (int step = 0; step <= steps; ++step)
        {
            const double share = static_cast<double>(step) / steps;
            const int x = static_cast<int>(std::lround(from.x + (to.x - from.x) * share));
            const int y = static_cast<int>(std::lround(from.y + (to.y - from.y) * share));

            for (int dy = 0; dy < thickness; ++dy)
            {
                for (int dx = 0; dx < thickness; ++dx)
                {
                    set(x + dx - thickness / 2, y + dy - thickness / 2, color);
                }
            }
        }
    }

    void dot(Point centre, int radius, Color color)
    {
        for (int dy = -radius; dy <= radius; ++dy)
        {
            for (int dx = -radius; dx <= radius; ++dx)
            {
                if (dx * dx + dy * dy <= radius * radius)
                {
                    set(static_cast<int>(std::lround(centre.x)) + dx, static_cast<int>(std::lround(centre.y)) + dy,
                        color);
                }
            }
        }
    }

    // A label centred on a point: dark text on a light plate, so it reads on any colour.
    void label(Point centre, const std::string &text, Color ink, int scale = 2)
    {
        const int width = static_cast<int>(text.size()) * 6 * scale;
        const int height = 7 * scale;
        const int left = static_cast<int>(std::lround(centre.x)) - width / 2;
        const int top = static_cast<int>(std::lround(centre.y)) - height / 2;

        for (int y = top - scale; y < top + height + scale; ++y)
        {
            for (int x = left - scale; x < left + width; ++x)
            {
                set(x, y, {250, 250, 245});
            }
        }

        for (size_t index = 0; index < text.size(); ++index)
        {
            const std::map<char, std::array<uint8_t, 7>>::const_iterator glyph = glyphs().find(text[index]);

            if (glyph == glyphs().end())
            {
                continue;
            }

            for (int row = 0; row < 7; ++row)
            {
                for (int column = 0; column < 5; ++column)
                {
                    if ((glyph->second[static_cast<size_t>(row)] >> (4 - column)) & 1)
                    {
                        for (int dy = 0; dy < scale; ++dy)
                        {
                            for (int dx = 0; dx < scale; ++dx)
                            {
                                set(left + static_cast<int>(index) * 6 * scale + column * scale + dx,
                                    top + row * scale + dy, ink);
                            }
                        }
                    }
                }
            }
        }
    }

    Image take()
    {
        return std::move(m_image);
    }

private:
    Image m_image;
};

// A colour per sector: spread round the colour wheel so neighbours differ, muted so labels read.
Color sectorColor(size_t sector, double shade)
{
    const double hue = std::fmod(static_cast<double>(sector) * 0.618033988749895, 1.0) * 6.0;
    const double chroma = 0.38;
    const double base = 0.52;
    const double second = chroma * (1.0 - std::fabs(std::fmod(hue, 2.0) - 1.0));
    double red = 0.0;
    double green = 0.0;
    double blue = 0.0;

    switch (static_cast<int>(hue))
    {
    case 0: red = chroma; green = second; break;
    case 1: red = second; green = chroma; break;
    case 2: green = chroma; blue = second; break;
    case 3: green = second; blue = chroma; break;
    case 4: red = second; blue = chroma; break;
    default: red = chroma; blue = second; break;
    }

    const auto channel = [shade, base](double value)
    {
        return static_cast<uint8_t>(std::clamp((value + base) * shade, 0.0, 1.0) * 255.0);
    };
    return {channel(red), channel(green), channel(blue)};
}

// Map coordinates to the canvas: plan (x east, y north, north up) or isometric (looking north-east and down).
struct Projection
{
    bool isometric = false;
    double scale = 1.0;
    double offsetX = 0.0;
    double offsetY = 0.0;

    Point raw(double x, double y, double z) const
    {
        if (!isometric)
        {
            return {x, -y};
        }

        return {(x - y) * 0.7071, -(x + y) * 0.7071 * 0.5 - z * 0.8};
    }

    Point operator()(double x, double y, double z) const
    {
        const Point point = raw(x, y, z);
        return {point.x * scale + offsetX, point.y * scale + offsetY};
    }

    // Larger is nearer to the viewer.
    double depth(double x, double y, double z) const
    {
        return isometric ? -(x + y) + z * 0.5 : z;
    }
};

Projection fitProjection(
    bool isometric, const std::vector<std::array<double, 3>> &extent, int size, int &width, int &height)
{
    Projection projection;
    projection.isometric = isometric;
    double minX = 1.0e18;
    double minY = 1.0e18;
    double maxX = -1.0e18;
    double maxY = -1.0e18;

    for (const std::array<double, 3> &corner : extent)
    {
        const Point point = projection.raw(corner[0], corner[1], corner[2]);
        minX = std::min(minX, point.x);
        maxX = std::max(maxX, point.x);
        minY = std::min(minY, point.y);
        maxY = std::max(maxY, point.y);
    }

    const double margin = 24.0;
    const double spanX = std::max(1.0, maxX - minX);
    const double spanY = std::max(1.0, maxY - minY);
    projection.scale = (size - 2.0 * margin) / std::max(spanX, spanY);
    width = static_cast<int>(std::ceil(spanX * projection.scale + 2.0 * margin));
    height = static_cast<int>(std::ceil(spanY * projection.scale + 2.0 * margin));
    projection.offsetX = margin - minX * projection.scale;
    projection.offsetY = margin - minY * projection.scale;
    return projection;
}

Image renderIndoor(const LoadedMap &map, const PreviewOptions &options)
{
    const Game::IndoorMapData &indoor = *map.indoor;
    std::vector<std::array<double, 3>> extent;

    for (const Game::IndoorVertex &vertex : indoor.vertices)
    {
        extent.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y), static_cast<double>(vertex.z)});
    }

    if (extent.empty())
    {
        return Canvas(64, 64, {30, 30, 34}).take();
    }

    const bool isometric = options.view == PreviewView::Isometric;
    int width = 0;
    int height = 0;
    const Projection projection = fitProjection(isometric, extent, options.size, width, height);
    Canvas canvas(width, height, {28, 28, 32});
    std::set<uint16_t> doorFaces;
    std::map<uint16_t, uint32_t> doorOfFace;
    std::map<uint32_t, Point> doorLabels;

    if (map.state)
    {
        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            for (const uint16_t faceId : door.faceIds)
            {
                doorFaces.insert(faceId);
                doorOfFace[faceId] = door.doorId;
            }
        }
    }

    struct Drawn
    {
        size_t face = 0;
        double depth = 0.0;
        double normalX = 0.0;
        double normalY = 0.0;
        double normalZ = 0.0;
    };

    std::vector<Drawn> order;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

        Drawn drawn;
        drawn.face = faceIndex;
        double depth = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &current = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next =
                indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            drawn.normalX += (static_cast<double>(current.y) - next.y) * (static_cast<double>(current.z) + next.z);
            drawn.normalY += (static_cast<double>(current.z) - next.z) * (static_cast<double>(current.x) + next.x);
            drawn.normalZ += (static_cast<double>(current.x) - next.x) * (static_cast<double>(current.y) + next.y);
            depth += projection.depth(current.x, current.y, current.z);
        }

        const double length = std::sqrt(
            drawn.normalX * drawn.normalX + drawn.normalY * drawn.normalY + drawn.normalZ * drawn.normalZ);

        if (length <= 0.0)
        {
            continue;
        }

        drawn.normalX /= length;
        drawn.normalY /= length;
        drawn.normalZ /= length;
        drawn.depth = depth / static_cast<double>(face.vertexIndices.size());
        const bool isFloor = drawn.normalZ > 0.5;

        // Plan: floors only. Isometric: floors and the walls whose room side faces the viewer (who stands to the
        // south-west and looks down), so rooms are seen into over their near walls.
        if (isometric ? (drawn.normalZ < -0.2 || (!isFloor && drawn.normalX + drawn.normalY > -0.05)) : !isFloor)
        {
            continue;
        }

        order.push_back(drawn);
    }

    std::stable_sort(order.begin(), order.end(), [](const Drawn &left, const Drawn &right)
    {
        return left.depth < right.depth;
    });

    // Where each sector's number goes: the middle of its largest floor face.
    std::map<size_t, std::pair<double, Point>> labelBySector;

    for (const Drawn &drawn : order)
    {
        const Game::IndoorFace &face = indoor.faces[drawn.face];
        std::vector<Point> polygon;
        double sumX = 0.0;
        double sumY = 0.0;
        double sumZ = 0.0;
        double doubleArea = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next =
                indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            polygon.push_back(projection(vertex.x, vertex.y, vertex.z));
            sumX += vertex.x;
            sumY += vertex.y;
            sumZ += vertex.z;
            doubleArea += static_cast<double>(vertex.x) * next.y - static_cast<double>(next.x) * vertex.y;
        }

        const double count = static_cast<double>(face.vertexIndices.size());
        const bool isFloor = drawn.normalZ > 0.5;
        const bool isDoor = doorFaces.contains(static_cast<uint16_t>(drawn.face));

        if (face.isPortal)
        {
            if (!isometric || isFloor)
            {
                continue;
            }
        }

        // Light from the west and above.
        const double shade = isFloor ? 1.0 : 0.62 + 0.3 * std::max(0.0, drawn.normalX * 0.8 - drawn.normalY * 0.2);
        const Color color = isDoor ? Color{200, 60, 50} : face.isPortal ? Color{60, 150, 80}
            : sectorColor(face.roomNumber, shade);

        if (!face.isPortal)
        {
            canvas.fill(polygon, color);
        }

        if (isFloor && !face.isPortal && !isDoor)
        {
            const std::map<size_t, std::pair<double, Point>>::const_iterator known =
                labelBySector.find(face.roomNumber);

            if (known == labelBySector.end() || std::abs(doubleArea) > known->second.first)
            {
                labelBySector[face.roomNumber] = {
                    std::abs(doubleArea), projection(sumX / count, sumY / count, sumZ / count)};
            }
        }
    }

    // Lines over the fills: floor outlines, portals and doors.
    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];
        const bool isDoor = doorFaces.contains(static_cast<uint16_t>(faceIndex));

        if (face.vertexIndices.size() < 3 || (!face.isPortal && !isDoor))
        {
            continue;
        }

        const Color color = isDoor ? Color{235, 70, 55} : Color{70, 200, 100};
        double sumX = 0.0;
        double sumY = 0.0;
        double sumZ = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next =
                indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            canvas.line(projection(vertex.x, vertex.y, vertex.z), projection(next.x, next.y, next.z), color,
                isDoor ? 3 : 2);
            sumX += vertex.x;
            sumY += vertex.y;
            sumZ += vertex.z;
        }

        if (isDoor && options.labels)
        {
            const double count = static_cast<double>(face.vertexIndices.size());
            doorLabels[doorOfFace[static_cast<uint16_t>(faceIndex)]] =
                projection(sumX / count, sumY / count, sumZ / count);
        }
    }

    for (const Game::IndoorSpawn &spawn : indoor.spawns)
    {
        canvas.dot(projection(spawn.x, spawn.y, spawn.z), 3, {250, 220, 70});
    }

    std::optional<Game::IndoorPartyStartPoint> start = indoor.partyStartPoint;

    if (map.indoorScene && !map.indoorScene->partyStartPoints.empty())
    {
        start = map.indoorScene->partyStartPoints.front().startPoint;
    }

    if (options.labels)
    {
        for (const std::pair<const size_t, std::pair<double, Point>> &entry : labelBySector)
        {
            // A sector too small to hold its number stays unlabelled.
            if (entry.second.first * projection.scale * projection.scale > 1400.0)
            {
                canvas.label(entry.second.second, std::to_string(entry.first), {20, 20, 30});
            }
        }

        for (const std::pair<const uint32_t, Point> &entry : doorLabels)
        {
            canvas.label({entry.second.x, entry.second.y - 12.0}, "d" + std::to_string(entry.first), {170, 20, 10}, 1);
        }
    }

    if (start)
    {
        const Point point = projection(start->x, start->y, start->z);
        canvas.dot(point, 7, {255, 255, 255});
        canvas.label({point.x, point.y - 18.0}, "S", {0, 90, 200});
    }

    return canvas.take();
}

Image renderOutdoor(const LoadedMap &map, const PreviewOptions &options)
{
    const Game::OutdoorMapData &outdoor = *map.outdoor;
    const double cell = Game::OutdoorMapData::TerrainTileSize;
    const double half = cell * Game::OutdoorMapData::TerrainWidth / 2.0;
    const bool isometric = options.view == PreviewView::Isometric;
    int width = 0;
    int height = 0;
    const Projection projection = fitProjection(
        isometric,
        {{-half, -half, 0.0}, {half, -half, 0.0}, {half, half, 0.0}, {-half, half, 0.0}, {0.0, 0.0, 8192.0}},
        options.size, width, height);
    Canvas canvas(width, height, {28, 28, 32});
    const int cells = Game::OutdoorMapData::TerrainWidth;
    const auto heightAt = [&outdoor, cells](int column, int row) -> double
    {
        const size_t index = static_cast<size_t>(std::clamp(row, 0, cells - 1)) * cells
            + static_cast<size_t>(std::clamp(column, 0, cells - 1));
        return index < outdoor.heightMap.size()
            ? outdoor.heightMap[index] * static_cast<double>(Game::OutdoorMapData::TerrainHeightScale) : 0.0;
    };

    // Terrain cells from the far side to the near one; row 0 is the map's north edge.
    for (int step = 0; step < cells - 1; ++step)
    {
        const int row = step;

        for (int column = cells - 2; column >= 0; --column)
        {
            const double west = column * cell - half;
            const double north = half - row * cell;
            const double z = heightAt(column, row);
            const double slope = heightAt(column + 1, row) - heightAt(column, row + 1);
            const double level = std::clamp(z / 6000.0, 0.0, 1.0);
            const double shade = std::clamp(0.85 + slope / 1200.0, 0.55, 1.15);
            // Water is where the tiles are water, not where the land lies at 0: a beach or a town at sea level
            // is land.
            const size_t cellIndex = static_cast<size_t>(row) * cells + column;
            const uint8_t kind = cellIndex < options.cellKinds.size() ? options.cellKinds[cellIndex] : 0;
            const Color land = {
                static_cast<uint8_t>(std::clamp((70.0 + 120.0 * level) * shade, 0.0, 255.0)),
                static_cast<uint8_t>(std::clamp((120.0 + 60.0 * level) * shade, 0.0, 255.0)),
                static_cast<uint8_t>(std::clamp((60.0 + 90.0 * level) * shade, 0.0, 255.0))};
            const Color color = kind == 4 ? Color{36, 30, 34} : kind == 2 ? Color{50, 90, 150} : (kind == 1 ? Color{112, 132, 140}
                : (kind == 3 ? Color{static_cast<uint8_t>(land.red / 2 + 50), static_cast<uint8_t>(land.green / 2 + 35),
                    static_cast<uint8_t>(land.blue / 2 + 20)} : land));
            canvas.fill(
                {projection(west, north, heightAt(column, row)),
                    projection(west + cell, north, heightAt(column + 1, row)),
                    projection(west + cell, north - cell, heightAt(column + 1, row + 1)),
                    projection(west, north - cell, heightAt(column, row + 1))},
                color);
        }
    }

    std::vector<std::pair<Point, size_t>> buildingLabels;

    for (size_t index = 0; index < outdoor.bmodels.size(); ++index)
    {
        const Game::OutdoorBModel &bmodel = outdoor.bmodels[index];

        if (bmodel.vertices.empty())
        {
            continue;
        }

        double sumX = 0.0;
        double sumY = 0.0;
        double top = -1.0e9;

        for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
        {
            sumX += vertex.x;
            sumY += vertex.y;
            top = std::max(top, static_cast<double>(vertex.z));
        }

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            std::vector<Point> polygon;

            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex < bmodel.vertices.size())
                {
                    const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];
                    polygon.push_back(projection(vertex.x, vertex.y, vertex.z));
                }
            }

            const bool clickable = face.cogTriggeredNumber != 0;
            canvas.fill(polygon, clickable ? Color{215, 140, 60} : sectorColor(index, 0.9));
        }

        const double count = static_cast<double>(bmodel.vertices.size());
        buildingLabels.push_back({projection(sumX / count, sumY / count, top), index});
    }

    for (const Game::OutdoorSpawn &spawn : outdoor.spawns)
    {
        canvas.dot(projection(spawn.x, spawn.y, spawn.z), 3, {250, 220, 70});
    }

    if (options.labels)
    {
        for (const std::pair<Point, size_t> &entry : buildingLabels)
        {
            canvas.label(entry.first, "b" + std::to_string(entry.second), {20, 20, 30}, 1);
        }
    }

    return canvas.take();
}

uint32_t crc32Of(const uint8_t *pData, size_t length, uint32_t crc)
{
    static const std::array<uint32_t, 256> table = []()
    {
        std::array<uint32_t, 256> values = {};

        for (uint32_t index = 0; index < 256; ++index)
        {
            uint32_t value = index;

            for (int bit = 0; bit < 8; ++bit)
            {
                value = (value & 1) ? 0xedb88320u ^ (value >> 1) : value >> 1;
            }

            values[index] = value;
        }

        return values;
    }();

    for (size_t index = 0; index < length; ++index)
    {
        crc = table[(crc ^ pData[index]) & 0xff] ^ (crc >> 8);
    }

    return crc;
}

void appendBigEndian(std::vector<uint8_t> &bytes, uint32_t value)
{
    for (int shift = 24; shift >= 0; shift -= 8)
    {
        bytes.push_back(static_cast<uint8_t>((value >> shift) & 0xff));
    }
}

void appendChunk(std::vector<uint8_t> &file, const char *pType, const std::vector<uint8_t> &data)
{
    appendBigEndian(file, static_cast<uint32_t>(data.size()));
    std::vector<uint8_t> body(pType, pType + 4);
    body.insert(body.end(), data.begin(), data.end());
    file.insert(file.end(), body.begin(), body.end());
    appendBigEndian(file, crc32Of(body.data(), body.size(), 0xffffffffu) ^ 0xffffffffu);
}
}

std::vector<uint8_t> encodePng(const Image &image)
{
    std::vector<uint8_t> file = {0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a};
    std::vector<uint8_t> header;
    appendBigEndian(header, static_cast<uint32_t>(image.width));
    appendBigEndian(header, static_cast<uint32_t>(image.height));
    header.insert(header.end(), {8, 2, 0, 0, 0});
    appendChunk(file, "IHDR", header);

    // The rows, each with filter 0 in front, in stored deflate blocks.
    std::vector<uint8_t> raw;
    raw.reserve(static_cast<size_t>(image.height) * (static_cast<size_t>(image.width) * 3 + 1));

    for (int row = 0; row < image.height; ++row)
    {
        raw.push_back(0);
        const size_t offset = static_cast<size_t>(row) * image.width * 3;
        raw.insert(raw.end(), image.pixels.begin() + static_cast<std::ptrdiff_t>(offset),
            image.pixels.begin() + static_cast<std::ptrdiff_t>(offset + static_cast<size_t>(image.width) * 3));
    }

    std::vector<uint8_t> data = {0x78, 0x01};
    uint32_t adlerLow = 1;
    uint32_t adlerHigh = 0;
    size_t position = 0;

    do
    {
        const size_t length = std::min<size_t>(65535, raw.size() - position);
        data.push_back(position + length >= raw.size() ? 1 : 0);
        data.push_back(static_cast<uint8_t>(length & 0xff));
        data.push_back(static_cast<uint8_t>(length >> 8));
        data.push_back(static_cast<uint8_t>(~length & 0xff));
        data.push_back(static_cast<uint8_t>((~length >> 8) & 0xff));

        for (size_t index = 0; index < length; ++index)
        {
            const uint8_t value = raw[position + index];
            data.push_back(value);
            adlerLow = (adlerLow + value) % 65521;
            adlerHigh = (adlerHigh + adlerLow) % 65521;
        }

        position += length;
    } while (position < raw.size());

    appendBigEndian(data, (adlerHigh << 16) | adlerLow);
    appendChunk(file, "IDAT", data);
    appendChunk(file, "IEND", {});
    return file;
}

Image renderPreview(const LoadedMap &map, const PreviewOptions &options)
{
    if (map.indoor)
    {
        return renderIndoor(map, options);
    }

    if (map.outdoor)
    {
        return renderOutdoor(map, options);
    }

    return Canvas(64, 64, {28, 28, 32}).take();
}
}

// ---- The picture of an outdoor sketch (sketch.yml) ----

namespace OpenYAMM::Studio
{
namespace
{
// Capital letters and the marks ids use, 5 by 7 as the digits above.
const std::map<char, std::array<uint8_t, 7>> &sketchGlyphs()
{
    static const std::map<char, std::array<uint8_t, 7>> table = {
        {'A', {0x0e, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11}}, {'B', {0x1e, 0x11, 0x11, 0x1e, 0x11, 0x11, 0x1e}},
        {'C', {0x0e, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0e}}, {'D', {0x1e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1e}},
        {'E', {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x1f}}, {'F', {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x10}},
        {'G', {0x0e, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0f}}, {'H', {0x11, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11}},
        {'I', {0x0e, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0e}}, {'J', {0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0c}},
        {'K', {0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11}}, {'L', {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1f}},
        {'M', {0x11, 0x1b, 0x15, 0x15, 0x11, 0x11, 0x11}}, {'N', {0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11}},
        {'O', {0x0e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e}}, {'P', {0x1e, 0x11, 0x11, 0x1e, 0x10, 0x10, 0x10}},
        {'Q', {0x0e, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0d}}, {'R', {0x1e, 0x11, 0x11, 0x1e, 0x14, 0x12, 0x11}},
        {'S', {0x0f, 0x10, 0x10, 0x0e, 0x01, 0x01, 0x1e}}, {'T', {0x1f, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04}},
        {'U', {0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e}}, {'V', {0x11, 0x11, 0x11, 0x11, 0x11, 0x0a, 0x04}},
        {'W', {0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0a}}, {'X', {0x11, 0x11, 0x0a, 0x04, 0x0a, 0x11, 0x11}},
        {'Y', {0x11, 0x11, 0x11, 0x0a, 0x04, 0x04, 0x04}}, {'Z', {0x1f, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1f}},
        {'-', {0x00, 0x00, 0x00, 0x1f, 0x00, 0x00, 0x00}}, {':', {0x00, 0x0c, 0x0c, 0x00, 0x0c, 0x0c, 0x00}},
        {'.', {0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x0c}}, {'#', {0x0a, 0x0a, 0x1f, 0x0a, 0x1f, 0x0a, 0x0a}},
        {'=', {0x00, 0x00, 0x1f, 0x00, 0x1f, 0x00, 0x00}}, {'/', {0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10}},
    };
    return table;
}

// What a label shows of a text: capitals, digits and a few marks; anything else is a gap.
std::string sketchLabelText(const std::string &text, size_t maximumLength)
{
    std::string label;

    for (const char character : text)
    {
        if (label.size() >= maximumLength)
        {
            break;
        }

        const char upper = (character >= 'a' && character <= 'z') ? static_cast<char>(character - 'a' + 'A')
            : character;
        const bool known = (upper >= '0' && upper <= '9') || sketchGlyphs().contains(upper);
        label.push_back(known ? upper : ' ');
    }

    while (!label.empty() && label.back() == ' ')
    {
        label.pop_back();
    }

    return label;
}

int sketchTextWidth(const std::string &text, int scale)
{
    return text.empty() ? 0 : static_cast<int>(text.size()) * 6 * scale - scale;
}

// Text with its top-left corner at a pixel, on a light plate when asked.
void sketchDrawText(Canvas &canvas, int left, int top, const std::string &text, Color ink, int scale, bool plate)
{
    if (plate)
    {
        for (int y = top - 2; y < top + 7 * scale + 2; ++y)
        {
            for (int x = left - 2; x < left + sketchTextWidth(text, scale) + 2; ++x)
            {
                canvas.set(x, y, {252, 252, 246});
            }
        }
    }

    for (size_t index = 0; index < text.size(); ++index)
    {
        const std::array<uint8_t, 7> *pGlyph = nullptr;
        const std::map<char, std::array<uint8_t, 7>>::const_iterator own = sketchGlyphs().find(text[index]);

        if (own != sketchGlyphs().end())
        {
            pGlyph = &own->second;
        }
        else
        {
            const std::map<char, std::array<uint8_t, 7>>::const_iterator digit = glyphs().find(text[index]);

            if (digit != glyphs().end() && text[index] >= '0' && text[index] <= '9')
            {
                pGlyph = &digit->second;
            }
        }

        if (pGlyph == nullptr)
        {
            continue;
        }

        for (int row = 0; row < 7; ++row)
        {
            for (int column = 0; column < 5; ++column)
            {
                if ((((*pGlyph)[static_cast<size_t>(row)] >> (4 - column)) & 1) == 0)
                {
                    continue;
                }

                for (int dy = 0; dy < scale; ++dy)
                {
                    for (int dx = 0; dx < scale; ++dx)
                    {
                        canvas.set(left + static_cast<int>(index) * 6 * scale + column * scale + dx,
                            top + row * scale + dy, ink);
                    }
                }
            }
        }
    }
}

void sketchDashedLine(Canvas &canvas, Point from, Point to, Color color, int thickness, double dash, double gap)
{
    const double length = oy::hypot(to.x - from.x, to.y - from.y);

    if (length <= 0.0)
    {
        return;
    }

    for (double start = 0.0; start < length; start += dash + gap)
    {
        const double end = std::min(length, start + dash);
        canvas.line({from.x + (to.x - from.x) * start / length, from.y + (to.y - from.y) * start / length},
            {from.x + (to.x - from.x) * end / length, from.y + (to.y - from.y) * end / length}, color, thickness);
    }
}

void sketchPolyline(Canvas &canvas, const std::vector<Point> &points, bool closed, Color color, int thickness,
    double dash = 0.0)
{
    const size_t count = points.size();

    for (size_t index = 0; index + 1 < count || (closed && index < count); ++index)
    {
        const Point &from = points[index];
        const Point &to = points[(index + 1) % count];

        if (dash > 0.0)
        {
            sketchDashedLine(canvas, from, to, color, thickness, dash, dash * 0.7);
        }
        else
        {
            canvas.line(from, to, color, thickness);
        }
    }
}

YAML::Node sketchChild(const YAML::Node &node, const std::string &key)
{
    if (node.IsDefined() && node.IsMap())
    {
        const YAML::Node value = node[key];

        if (value.IsDefined())
        {
            return value;
        }
    }

    return YAML::Node(YAML::NodeType::Undefined);
}

std::string sketchString(const YAML::Node &node, const std::string &key)
{
    const YAML::Node value = sketchChild(node, key);
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();
}

bool sketchNumber(const YAML::Node &node, double &number)
{
    if (!node.IsDefined() || !node.IsScalar())
    {
        return false;
    }

    const ScalarKind kind = classifyScalar(node);

    if (kind != ScalarKind::Integer && kind != ScalarKind::Number)
    {
        return false;
    }

    const std::string &text = node.Scalar();
    const char *pBegin = text.data() + ((!text.empty() && text[0] == '+') ? 1 : 0);
    return std::from_chars(pBegin, text.data() + text.size(), number).ec == std::errc() && std::isfinite(number);
}

bool sketchCell(const YAML::Node &node, Point &cell)
{
    return node.IsDefined() && node.IsSequence() && node.size() == 2 && sketchNumber(node[0], cell.x)
        && sketchNumber(node[1], cell.y);
}

std::vector<Point> sketchCells(const YAML::Node &node)
{
    std::vector<Point> cells;

    if (node.IsDefined() && node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            Point cell;

            if (sketchCell(item, cell))
            {
                cells.push_back(cell);
            }
        }
    }

    return cells;
}

// The part of an id after its kind, as a label: "entrance:north_gate" gives "NORTH GATE".
std::string sketchIdLabel(const std::string &id, size_t maximumLength)
{
    const size_t colon = id.find(':');
    std::string name = colon == std::string::npos ? id : id.substr(colon + 1);
    std::replace(name.begin(), name.end(), '_', ' ');
    return sketchLabelText(name, maximumLength);
}

// Low ground green, middle ground sand, high ground brown.
Color sketchHeightColor(double share)
{
    const std::array<std::array<double, 3>, 3> stops = {{{204, 222, 178}, {230, 218, 172}, {178, 150, 120}}};
    const double position = std::clamp(share, 0.0, 1.0) * 2.0;
    const size_t first = position >= 1.0 ? 1 : 0;
    const double blend = position - static_cast<double>(first);
    const auto channel = [&stops, first, blend](size_t index)
    {
        return static_cast<uint8_t>(std::lround(stops[first][index] * (1.0 - blend) + stops[first + 1][index] * blend));
    };
    return {channel(0), channel(1), channel(2)};
}

struct SketchLabelRequest
{
    Point anchor;
    std::string text;
    Color ink;
    // Lower is placed first.
    int priority = 0;
    // Pixels kept free round the anchor (its dot).
    int clearance = 4;
    bool plate = true;
    // Dropped when no free place is found near the anchor.
    bool optional = false;
};

struct SketchBox
{
    int left = 0;
    int top = 0;
    int right = 0;
    int bottom = 0;

    bool overlaps(const SketchBox &other) const
    {
        return left < other.right && other.left < right && top < other.bottom && other.top < bottom;
    }
};

// Puts each label beside its anchor where no other label or dot is, nearest places first.
class SketchLabels
{
public:
    // `box` is the part of the picture labels may be anchored in.
    SketchLabels(int size, const SketchBox &box)
        : m_size(size)
        , m_box(box)
    {
    }

    void keepFree(Point centre, int radius)
    {
        const int x = static_cast<int>(std::lround(centre.x));
        const int y = static_cast<int>(std::lround(centre.y));
        m_taken.push_back({x - radius, y - radius, x + radius + 1, y + radius + 1});
    }

    void add(const SketchLabelRequest &request)
    {
        const bool inside = request.anchor.x >= m_box.left && request.anchor.x <= m_box.right
            && request.anchor.y >= m_box.top && request.anchor.y <= m_box.bottom;

        if (!request.text.empty() && inside)
        {
            m_requests.push_back(request);
        }
    }

    void draw(Canvas &canvas)
    {
        std::stable_sort(m_requests.begin(), m_requests.end(),
            [](const SketchLabelRequest &left, const SketchLabelRequest &right)
            {
                return left.priority < right.priority;
            });
        std::vector<std::pair<std::string, Point>> placed;

        for (const SketchLabelRequest &request : m_requests)
        {
            const bool repeated = std::any_of(placed.begin(), placed.end(),
                [&request](const std::pair<std::string, Point> &entry)
                {
                    return entry.first == request.text
                        && oy::hypot(entry.second.x - request.anchor.x, entry.second.y - request.anchor.y) < 14.0;
                });

            if (repeated)
            {
                continue;
            }

            const int width = sketchTextWidth(request.text, 1);
            const int height = 7;
            const int x = static_cast<int>(std::lround(request.anchor.x));
            const int y = static_cast<int>(std::lround(request.anchor.y));
            bool found = false;
            SketchBox chosen;
            int chosenRing = 0;

            for (int ring = 0; ring < (request.optional ? 2 : 4) && !found; ++ring)
            {
                const int reach = request.clearance + 3 + ring * 11;
                // Right, left, above, below, then the four corners.
                const std::array<std::array<int, 2>, 8> corners = {{
                    {x + reach, y - height / 2}, {x - reach - width, y - height / 2},
                    {x - width / 2, y - reach - height}, {x - width / 2, y + reach},
                    {x + reach, y - reach - height}, {x + reach, y + reach},
                    {x - reach - width, y - reach - height}, {x - reach - width, y + reach}}};

                for (const std::array<int, 2> &corner : corners)
                {
                    const SketchBox box = {corner[0] - 3, corner[1] - 3, corner[0] + width + 3, corner[1] + height + 3};

                    if (box.left < 0 || box.top < 0 || box.right > m_size || box.bottom > m_size)
                    {
                        continue;
                    }

                    const bool taken = std::any_of(m_taken.begin(), m_taken.end(), [&box](const SketchBox &other)
                    {
                        return box.overlaps(other);
                    });

                    if (!taken)
                    {
                        chosen = box;
                        chosenRing = ring;
                        found = true;
                        break;
                    }
                }
            }

            if (!found)
            {
                if (request.optional)
                {
                    continue;
                }

                chosen = {x + request.clearance, y - 6, x + request.clearance + width + 6, y + 7};
            }

            if (chosenRing > 0)
            {
                // A leader from the anchor to the label's nearest corner.
                const Point corner = {
                    static_cast<double>(std::clamp(x, chosen.left + 2, chosen.right - 2)),
                    static_cast<double>(std::clamp(y, chosen.top + 2, chosen.bottom - 2))};
                canvas.line(request.anchor, corner, {90, 90, 90});
            }

            sketchDrawText(canvas, chosen.left + 3, chosen.top + 3, request.text, request.ink, 1, request.plate);
            m_taken.push_back(chosen);
            placed.push_back({request.text, request.anchor});
        }
    }

private:
    int m_size = 0;
    SketchBox m_box;
    std::vector<SketchBox> m_taken;
    std::vector<SketchLabelRequest> m_requests;
};
}

Image renderSketch(const Project &project, const SketchPreviewOptions &options)
{
    const YAML::Node sketch = project.document("sketch.yml");
    const YAML::Node plan = project.document("plan.yml");
    const int size = std::clamp(options.size, 256, 4096);
    const double margin = std::max(30.0, size * 0.03);
    std::array<double, 4> region = options.region;
    region[0] = std::clamp(region[0], 0.0, SketchMapCells - 1.0);
    region[1] = std::clamp(region[1], 0.0, SketchMapCells - 1.0);
    region[2] = std::clamp(region[2], 1.0, SketchMapCells - region[0]);
    region[3] = std::clamp(region[3], 1.0, SketchMapCells - region[1]);
    const double scale = (size - 2.0 * margin) / std::max(region[2], region[3]);
    const auto pixel = [margin, scale, &region](double x, double y)
    {
        return Point{margin + (x - region[0]) * scale, margin + (y - region[1]) * scale};
    };
    // A close view gets a finer grid.
    const int gridCells = std::max(region[2], region[3]) > 48.0 ? 8 : 2;
    const auto pixels = [&pixel](const std::vector<Point> &cells)
    {
        std::vector<Point> result;

        for (const Point &cell : cells)
        {
            result.push_back(pixel(cell.x, cell.y));
        }

        return result;
    };
    const auto each = [](const YAML::Node &list)
    {
        std::vector<YAML::Node> items;

        if (list.IsDefined() && list.IsSequence())
        {
            for (const YAML::Node &item : list)
            {
                items.push_back(item);
            }
        }

        return items;
    };
    const int thin = std::max(1, static_cast<int>(std::lround(scale * 0.12)));
    const Color paper = {250, 250, 244};
    const Color land = {222, 226, 196};
    const Color ink = {30, 30, 30};
    const Color waterFill = {142, 186, 232};
    const Color waterLine = {70, 130, 205};
    const Color cliffInk = {62, 46, 36};
    Canvas canvas(size, size, paper);
    const Point boxFrom = pixel(region[0], region[1]);
    const Point boxTo = pixel(region[0] + region[2], region[1] + region[3]);
    SketchLabels labels(size, {static_cast<int>(boxFrom.x), static_cast<int>(boxFrom.y), static_cast<int>(boxTo.x),
        static_cast<int>(boxTo.y)});
    canvas.fill({pixel(0, 0), pixel(128, 0), pixel(128, 128), pixel(0, 128)}, land);

    // ---- the land by height: the coarse grid as shading, else the bands as tints
    const YAML::Node heights = sketchChild(sketch, "heights");
    const YAML::Node grid = sketchChild(heights, "grid");
    std::map<std::string, std::array<double, 2>> bandRanges;
    double lowest = 1.0e18;
    double highest = -1.0e18;

    for (const YAML::Node &band : each(sketchChild(plan, "height_bands")))
    {
        Point range;

        if (!sketchCell(sketchChild(band, "range"), range))
        {
            if (!sketchNumber(sketchChild(band, "level"), range.x))
            {
                continue;
            }

            range.y = range.x;
        }

        bandRanges[sketchString(band, "id")] = {range.x, range.y};
        lowest = std::min(lowest, (range.x + range.y) * 0.5);
        highest = std::max(highest, (range.x + range.y) * 0.5);
    }

    double gridStep = 0.0;
    const std::vector<YAML::Node> gridRows = each(sketchChild(grid, "rows"));
    const bool hasGrid = sketchNumber(sketchChild(grid, "step"), gridStep) && gridStep >= 1.0 && !gridRows.empty();

    if (hasGrid)
    {
        double low = 1.0e18;
        double high = -1.0e18;

        for (const YAML::Node &row : gridRows)
        {
            for (const YAML::Node &value : each(row))
            {
                double number = 0.0;

                if (sketchNumber(value, number))
                {
                    low = std::min(low, number);
                    high = std::max(high, number);
                }
            }
        }

        for (size_t row = 0; row < gridRows.size(); ++row)
        {
            const std::vector<YAML::Node> values = each(gridRows[row]);

            for (size_t column = 0; column < values.size(); ++column)
            {
                double number = 0.0;

                if (!sketchNumber(values[column], number))
                {
                    continue;
                }

                const double x = static_cast<double>(column) * gridStep;
                const double y = static_cast<double>(row) * gridStep;
                canvas.fill({pixel(x, y), pixel(x + gridStep, y), pixel(x + gridStep, y + gridStep),
                    pixel(x, y + gridStep)}, sketchHeightColor(high > low ? (number - low) / (high - low) : 0.0));
            }
        }
    }

    for (const YAML::Node &band : each(sketchChild(heights, "bands")))
    {
        const std::vector<Point> outline = pixels(sketchCells(sketchChild(band, "polygon")));
        const std::map<std::string, std::array<double, 2>>::const_iterator range =
            bandRanges.find(sketchString(band, "band"));

        if (hasGrid)
        {
            sketchPolyline(canvas, outline, true, {150, 118, 84}, 1, 3.0);
        }
        else if (range != bandRanges.end())
        {
            const double middle = (range->second[0] + range->second[1]) * 0.5;
            canvas.fill(outline, sketchHeightColor(highest > lowest ? (middle - lowest) / (highest - lowest) : 0.0));
        }
    }

    // ---- water
    const YAML::Node water = sketchChild(sketch, "water");

    for (const YAML::Node &body : each(sketchChild(water, "bodies")))
    {
        const std::vector<Point> outline = pixels(sketchCells(sketchChild(body, "polygon")));
        canvas.fill(outline, waterFill);
        sketchPolyline(canvas, outline, true, waterLine, 1);
    }

    for (const YAML::Node &river : each(sketchChild(water, "rivers")))
    {
        double width = 1.0;
        sketchNumber(sketchChild(river, "width_cells"), width);
        const std::vector<Point> line = pixels(sketchCells(sketchChild(river, "line")));
        const int thickness = std::max(2, static_cast<int>(std::lround(width * scale)));
        sketchPolyline(canvas, line, false, waterFill, thickness);

        for (const Point &point : line)
        {
            canvas.dot(point, thickness / 2, waterFill);
        }
    }

    // ---- the cell grid, dotted: every 8 cells, every 2 in a close view
    for (int cell = 0; cell <= 128; cell += gridCells)
    {
        for (int step = 0; step <= static_cast<int>(128.0 * scale); step += 4)
        {
            const double along = step / scale;
            const Point across = pixel(along, cell);
            const Point down = pixel(cell, along);
            const Color dots = {150, 150, 138};
            canvas.set(static_cast<int>(std::lround(across.x)), static_cast<int>(std::lround(across.y)), dots);
            canvas.set(static_cast<int>(std::lround(down.x)), static_cast<int>(std::lround(down.y)), dots);
        }
    }

    // ---- shores and cliffs
    for (const YAML::Node &shore : each(sketchChild(water, "shores")))
    {
        const std::string kind = sketchString(shore, "kind");
        const Color color = kind == "cliff" ? cliffInk : (kind == "marsh" ? Color{84, 140, 90} : Color{226, 196, 104});
        sketchPolyline(canvas, pixels(sketchCells(sketchChild(shore, "line"))), false, color,
            kind == "cliff" ? thin + 1 : thin + 2);
    }

    for (const YAML::Node &cliff : each(sketchChild(heights, "cliffs")))
    {
        const std::vector<Point> line = pixels(sketchCells(sketchChild(cliff, "line")));
        sketchPolyline(canvas, line, false, cliffInk, thin + 2);
        const std::string down = sketchString(cliff, "down");

        if (down.empty())
        {
            continue;
        }

        // Ticks on the low side: left of the walking direction is (dy, -dx) on a picture whose y runs down.
        const double side = down == "left" ? 1.0 : -1.0;

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            const double dx = line[index + 1].x - line[index].x;
            const double dy = line[index + 1].y - line[index].y;
            const double length = oy::hypot(dx, dy);

            for (double along = scale * 0.75; along < length; along += scale * 1.5)
            {
                const Point base = {line[index].x + dx * along / length, line[index].y + dy * along / length};
                const double reach = side * scale * 0.6 / length;
                canvas.line(base, {base.x + dy * reach, base.y - dx * reach}, cliffInk, thin);
            }
        }
    }

    // ---- districts: outlines, then their plots
    const Color districtInk = {124, 62, 150};

    for (const YAML::Node &district : each(sketchChild(sketch, "districts")))
    {
        const std::vector<Point> cells = sketchCells(sketchChild(district, "polygon"));

        if (sketchString(district, "rest") == "true" || cells.size() < 3)
        {
            continue;
        }

        sketchPolyline(canvas, pixels(cells), true, districtInk, 1);

        if (options.labels)
        {
            std::vector<Point2> outline;

            for (const Point &cell : cells)
            {
                outline.push_back({cell.x, cell.y});
            }

            if (polygonDoubleArea(outline) < 0.0)
            {
                std::reverse(outline.begin(), outline.end());
            }

            if (polygonIsSimple(outline))
            {
                const Point2 middle = polygonInteriorPoint(outline);
                labels.add({pixel(middle[0], middle[1]), sketchIdLabel(sketchString(district, "space"), 16),
                    districtInk, 6, 0, false, true});
            }
        }
    }

    // ---- roads
    for (const YAML::Node &road : each(sketchChild(sketch, "roads")))
    {
        const std::string width = sketchString(road, "width");
        const double share = width == "high_road" ? 0.5 : (width == "lane" ? 0.18 : 0.32);
        const int thickness = std::max(1, static_cast<int>(std::lround(scale * share)));
        const std::vector<Point> line = pixels(sketchCells(sketchChild(road, "line")));

        if (sketchString(road, "surface") == "water")
        {
            sketchPolyline(canvas, line, false, {24, 66, 160}, std::max(1, thin), 7.0);
            continue;
        }

        if (sketchString(road, "bridge") == "true")
        {
            sketchPolyline(canvas, line, false, ink, thickness + 4);
        }

        sketchPolyline(canvas, line, false, {134, 92, 50}, thickness);
    }

    // ---- plots: the footprint, the door side in red; a small open square where the plan gives no footprint
    for (const YAML::Node &district : each(sketchChild(sketch, "districts")))
    {
        for (const YAML::Node &plot : each(sketchChild(district, "plots")))
        {
            std::array<double, 4> rectangle = {0.0, 0.0, 0.0, 0.0};
            Point at;

            if (!sketchCell(sketchChild(plot, "at"), at))
            {
                continue;
            }

            const bool sized = sketchPlotRectangle(plan, plot, rectangle);

            if (!sized)
            {
                rectangle = {at.x, at.y, at.x + 1.0, at.y + 1.0};
            }

            const std::vector<Point> corners = {pixel(rectangle[0], rectangle[1]), pixel(rectangle[2], rectangle[1]),
                pixel(rectangle[2], rectangle[3]), pixel(rectangle[0], rectangle[3])};

            if (sized)
            {
                canvas.fill(corners, {208, 198, 186});
            }

            sketchPolyline(canvas, corners, true, {70, 58, 50}, 1, sized ? 0.0 : 2.0);
            const std::string facing = sketchString(plot, "facing");
            const size_t side = facing == "n" ? 0 : (facing == "e" ? 1 : (facing == "s" ? 2 : 3));
            canvas.line(corners[side], corners[(side + 1) % 4], {208, 30, 30}, thin + 1);

            if (options.labels && sized && sketchChild(plot, "index").IsDefined() == false)
            {
                labels.add({pixel((rectangle[0] + rectangle[2]) * 0.5, (rectangle[1] + rectangle[3]) * 0.5),
                    sketchIdLabel(sketchString(plot, "building"), 14), {70, 58, 50}, 5,
                    static_cast<int>((rectangle[2] - rectangle[0]) * scale * 0.5), true, true});
            }
        }
    }

    // ---- the parts of the buildings (plots and building structures) as the build reads them: every part's
    // outline, turned as the plot is, over the plot's footprint; a door as a red tick on its wall
    {
        std::vector<ProjectIssue> unusedIssues;
        std::vector<std::string> unusedWarnings;
        const YAML::Node worldNode = sketchChild(project.document("project.yml"), "world");
        const std::vector<OutdoorBuildingPlan> buildings = readOutdoorBuildings(project,
            worldNode.IsDefined() && worldNode.IsScalar() ? worldNode.Scalar() : std::string("mm8"), unusedIssues,
            unusedWarnings);
        const auto worldPixel = [&pixel](const std::array<double, 2> &world)
        {
            return pixel(world[0] / 512.0 + 64.0, 64.0 - world[1] / 512.0);
        };

        for (const OutdoorBuildingPlan &building : buildings)
        {
            for (const OutdoorPartPlan &part : building.parts)
            {
                std::vector<Point> outline;

                for (const std::array<double, 2> &corner : part.outline)
                {
                    outline.push_back(worldPixel(corner));
                }

                // Parts that hang (an upper storey, a turret) are drawn lighter and dashed.
                canvas.fill(outline, part.bottom > 0.0 ? Color{226, 214, 196} : Color{190, 172, 150});
                sketchPolyline(canvas, outline, true, {70, 58, 50}, 1, part.bottom > 0.0 ? 2.0 : 0.0);
            }

            for (const OutdoorDoorPlan &door : building.doors)
            {
                const OutdoorPartPlan &part = building.parts[door.part];
                const std::array<double, 2> &from = part.outline[door.wall];
                const std::array<double, 2> &to = part.outline[(door.wall + 1) % part.outline.size()];
                const std::vector<double> edges = outdoorBayEdges(part, door.wall, door.storey > 0);
                const double low = edges[std::min(door.bay, edges.size() - 2)];
                const double high = edges[std::min(door.bay + 1, edges.size() - 1)];
                canvas.line(worldPixel({from[0] + (to[0] - from[0]) * low, from[1] + (to[1] - from[1]) * low}),
                    worldPixel({from[0] + (to[0] - from[0]) * high, from[1] + (to[1] - from[1]) * high}),
                    {208, 30, 30}, thin + 2);
            }
        }
    }

    // ---- structures that are no building: a line for a wall, a bridge or stairs, a mark for the rest
    for (const YAML::Node &structure : each(sketchChild(sketch, "structures")))
    {
        const std::string kind = sketchString(structure, "kind");

        if (kind == "building")
        {
            continue;
        }

        const Color colour = kind == "wall" ? Color{90, 90, 96} : (kind == "bridge" || kind == "stairs"
            ? Color{128, 96, 52} : (kind == "decoration" ? Color{40, 120, 60} : Color{150, 40, 150}));
        std::vector<Point> line;

        for (const YAML::Node &corner : each(sketchChild(structure, "line")))
        {
            Point at;

            if (sketchCell(corner, at))
            {
                line.push_back(pixel(at.x, at.y));
            }
        }

        if (line.size() >= 2)
        {
            if (sketchString(structure, "closed") == "true")
            {
                line.push_back(line.front());
            }

            for (size_t index = 0; index + 1 < line.size(); ++index)
            {
                canvas.line(line[index], line[index + 1], colour, thin + (kind == "wall" ? 2 : 1));
            }

            continue;
        }

        Point at;

        if (!sketchCell(sketchChild(structure, "at"), at))
        {
            continue;
        }

        // A square a fifth of a cell each way, at least a few pixels: a well, a chest, a sign, a decoration.
        const double half = std::max(0.2, 2.5 / scale);
        const std::vector<Point> mark = {pixel(at.x - half, at.y - half), pixel(at.x + half, at.y - half),
            pixel(at.x + half, at.y + half), pixel(at.x - half, at.y + half)};
        canvas.fill(mark, colour);

        if (options.labels && scale >= 24.0)
        {
            labels.add({pixel(at.x, at.y + half * 2.0), sketchIdLabel(sketchString(structure, "id"), 14), colour, 4,
                static_cast<int>(scale), true, true});
        }
    }

    // ---- areas: dashed rings
    for (const YAML::Node &area : each(sketchChild(sketch, "areas")))
    {
        const std::string kind = sketchString(area, "kind");
        const Color color = kind == "keep_clear" ? Color{226, 132, 0}
            : (kind == "open" ? Color{40, 140, 70} : Color{204, 36, 36});
        const YAML::Node circle = sketchChild(area, "circle");
        std::vector<Point> ring = pixels(sketchCells(sketchChild(area, "polygon")));
        Point centre;
        double radius = 0.0;

        if (ring.empty() && sketchCell(sketchChild(circle, "at"), centre)
            && sketchNumber(sketchChild(circle, "r"), radius))
        {
            const Point middle = pixel(centre.x, centre.y);
            const double reach = std::max(5.0, radius * scale);

            for (int step = 0; step < 24; ++step)
            {
                const double angle = step * 6.283185307179586 / 24.0;
                ring.push_back({middle.x + oy::cos(angle) * reach, middle.y + oy::sin(angle) * reach});
            }

            sketchPolyline(canvas, ring, true, color, thin + 1);
            continue;
        }

        sketchPolyline(canvas, ring, true, color, thin + 1, 6.0);

        if (options.labels && !ring.empty())
        {
            // At the outline's first corner, so it does not sit on what the area holds.
            labels.add({ring[0], sketchIdLabel(sketchString(area, "id"), 16), color, 6, 2, true, true});
        }
    }

    // ---- the frame: the playable square and its exits
    const YAML::Node frame = sketchChild(sketch, "frame");
    std::array<double, 4> playable = {0.0, 0.0, 128.0, 128.0};
    const YAML::Node playableNode = sketchChild(frame, "playable");
    double square[4] = {0.0, 0.0, 0.0, 0.0};

    if (playableNode.IsDefined() && playableNode.IsSequence() && playableNode.size() == 4
        && sketchNumber(playableNode[0], square[0]) && sketchNumber(playableNode[1], square[1])
        && sketchNumber(playableNode[2], square[2]) && sketchNumber(playableNode[3], square[3]))
    {
        playable = {square[0], square[1], std::min(128.0, square[0] + square[2]),
            std::min(128.0, square[1] + square[3])};
        sketchPolyline(canvas, {pixel(playable[0], playable[1]), pixel(playable[2], playable[1]),
            pixel(playable[2], playable[3]), pixel(playable[0], playable[3])}, true, {70, 70, 70}, 1, 8.0);
    }

    for (const YAML::Node &edge : each(sketchChild(frame, "edges")))
    {
        Point span;
        const std::string side = sketchString(edge, "side");

        if (!sketchCell(sketchChild(edge, "span"), span) || side.empty())
        {
            continue;
        }

        const char letter = side[0];
        const bool alongX = letter == 'n' || letter == 's';
        const double fixed = letter == 'n' ? playable[1] : (letter == 's' ? playable[3]
            : (letter == 'w' ? playable[0] : playable[2]));
        const Point from = alongX ? pixel(span.x, fixed) : pixel(fixed, span.x);
        const Point to = alongX ? pixel(span.y, fixed) : pixel(fixed, span.y);
        canvas.line(from, to, {16, 150, 70}, thin + 3);

        if (options.labels)
        {
            labels.add({{(from.x + to.x) * 0.5, (from.y + to.y) * 0.5},
                "TO " + sketchIdLabel(sketchString(edge, "neighbour"), 18), {10, 110, 50}, 1, thin + 3, true, false});
        }
    }

    canvas.line(pixel(0, 0), pixel(128, 0), ink);
    canvas.line(pixel(128, 0), pixel(128, 128), ink);
    canvas.line(pixel(128, 128), pixel(0, 128), ink);
    canvas.line(pixel(0, 128), pixel(0, 0), ink);

    // ---- views: an arrow from the camera toward what it looks at
    for (const YAML::Node &view : each(sketchChild(sketch, "views")))
    {
        Point at;
        Point look;
        double yaw = 0.0;

        if (!sketchCell(sketchChild(view, "at"), at))
        {
            continue;
        }

        if (!sketchCell(sketchChild(view, "look"), look))
        {
            if (!sketchNumber(sketchChild(view, "yaw"), yaw))
            {
                continue;
            }

            look = {at.x + oy::sin(yaw * 0.017453292519943295), at.y - oy::cos(yaw * 0.017453292519943295)};
        }

        const double distance = oy::hypot(look.x - at.x, look.y - at.y);

        if (distance <= 0.0)
        {
            continue;
        }

        const double dx = (look.x - at.x) / distance;
        const double dy = (look.y - at.y) / distance;
        const double reach = std::min(distance, 3.5);
        const Point from = pixel(at.x, at.y);
        const Point tip = pixel(at.x + dx * reach, at.y + dy * reach);
        const Color color = {36, 56, 204};
        const double head = scale * 0.8;
        canvas.line(from, tip, color, thin + 1);
        canvas.line(tip, {tip.x - (dx * 0.8 + dy * 0.5) * head, tip.y - (dy * 0.8 - dx * 0.5) * head}, color, thin + 1);
        canvas.line(tip, {tip.x - (dx * 0.8 - dy * 0.5) * head, tip.y - (dy * 0.8 + dx * 0.5) * head}, color, thin + 1);
    }

    // ---- key heights: a small cross and the number
    for (const YAML::Node &point : each(sketchChild(heights, "points")))
    {
        Point at;
        double height = 0.0;

        if (!sketchCell(sketchChild(point, "at"), at) || !sketchNumber(sketchChild(point, "h"), height))
        {
            continue;
        }

        const Point centre = pixel(at.x, at.y);
        const Color color = {120, 78, 30};
        canvas.line({centre.x - 3, centre.y}, {centre.x + 3, centre.y}, color);
        canvas.line({centre.x, centre.y - 3}, {centre.x, centre.y + 3}, color);

        if (options.labels)
        {
            labels.add({centre, sketchLabelText(formatNumber(height), 8), color, 7, 3, false, true});
        }
    }

    // ---- points
    for (const YAML::Node &point : each(sketchChild(sketch, "points")))
    {
        Point at;

        if (!sketchCell(sketchChild(point, "at"), at))
        {
            continue;
        }

        const std::string id = sketchString(point, "id");
        const std::string kind = id.substr(0, id.find(':'));
        const bool minor = kind != "entrance" && kind != "poi" && kind != "landmark";
        const Color color = kind == "entrance" ? Color{0, 120, 50} : (kind == "poi" ? Color{160, 0, 130}
            : (kind == "landmark" ? Color{200, 96, 0} : Color{70, 70, 70}));
        const Point centre = pixel(at.x, at.y);
        const int radius = minor ? 2 : 3;
        canvas.dot(centre, radius + 1, {255, 255, 255});
        canvas.dot(centre, radius, color);
        labels.keepFree(centre, radius + 1);

        if (options.labels)
        {
            labels.add({centre, sketchIdLabel(id, 18), color, kind == "entrance" ? 0 : (kind == "poi" ? 1
                : (kind == "landmark" ? 2 : 4)), radius + 1, true, minor});
        }
    }

    // ---- the margins: whatever was drawn past the region is wiped, then the cell numbers go there
    const double edge = static_cast<double>(size);
    canvas.fill({{0.0, 0.0}, {edge, 0.0}, {edge, boxFrom.y}, {0.0, boxFrom.y}}, paper);
    canvas.fill({{0.0, boxTo.y + 1.0}, {edge, boxTo.y + 1.0}, {edge, edge}, {0.0, edge}}, paper);
    canvas.fill({{0.0, 0.0}, {boxFrom.x, 0.0}, {boxFrom.x, edge}, {0.0, edge}}, paper);
    canvas.fill({{boxTo.x + 1.0, 0.0}, {edge, 0.0}, {edge, edge}, {boxTo.x + 1.0, edge}}, paper);
    sketchPolyline(canvas, {boxFrom, {boxTo.x, boxFrom.y}, boxTo, {boxFrom.x, boxTo.y}}, true, ink, 1);

    for (int cell = 0; cell <= 128 && options.labels; cell += gridCells * 2)
    {
        const std::string number = std::to_string(cell);
        const Color grey = {110, 110, 110};

        if (cell >= region[0] && cell <= region[0] + region[2])
        {
            sketchDrawText(canvas, static_cast<int>(pixel(cell, 0).x) - sketchTextWidth(number, 1) / 2,
                static_cast<int>(boxFrom.y) - 11, number, grey, 1, false);
        }

        if (cell >= region[1] && cell <= region[1] + region[3])
        {
            sketchDrawText(canvas, static_cast<int>(boxFrom.x) - sketchTextWidth(number, 1) - 4,
                static_cast<int>(pixel(0, cell).y) - 3, number, grey, 1, false);
        }
    }

    if (options.labels)
    {
        labels.draw(canvas);
        // The title above the map and the key below it, each word in the colour it explains.
        const std::string title = sketchLabelText(sketchString(project.document("project.yml"), "id"), 24)
            + " SKETCH   NORTH UP   GRID " + std::to_string(gridCells) + " CELLS   1 CELL = 512 UNITS";
        sketchDrawText(canvas, static_cast<int>(margin), 4, title, ink, 1, false);
        const std::pair<const char *, Color> key[] = {
            {"ENTRANCE", {0, 120, 50}}, {"POI", {160, 0, 130}}, {"LANDMARK", {200, 96, 0}},
            {"JUNCTION", {70, 70, 70}}, {"ROAD", {134, 92, 50}}, {"CLIFF", cliffInk}, {"DISTRICT", districtInk},
            {"DOOR SIDE", {208, 30, 30}}, {"ENCOUNTER", {204, 36, 36}}, {"KEEP CLEAR", {226, 132, 0}},
            {"OPEN", {40, 140, 70}}, {"VIEW", {36, 56, 204}}, {"EXIT", {16, 150, 70}}, {"HEIGHT", {120, 78, 30}}};
        int left = static_cast<int>(margin);

        for (const std::pair<const char *, Color> &entry : key)
        {
            sketchDrawText(canvas, left, size - 13, entry.first, entry.second, 1, false);
            left += sketchTextWidth(entry.first, 1) + 18;
        }
    }

    return canvas.take();
}
}

// The plan with marks: additions for `oymap compare`.

namespace OpenYAMM::Studio
{
Image renderMarkedPlan(const LoadedMap &map, const std::vector<PlanMark> &marks, int size)
{
    if (!map.indoor || map.indoor->vertices.empty())
    {
        return Canvas(64, 64, {30, 30, 34}).take();
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    std::vector<std::array<double, 3>> extent;
    double lowest = indoor.vertices.front().z;
    double highest = lowest;

    for (const Game::IndoorVertex &vertex : indoor.vertices)
    {
        extent.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y), static_cast<double>(vertex.z)});
        lowest = std::min(lowest, static_cast<double>(vertex.z));
        highest = std::max(highest, static_cast<double>(vertex.z));
    }

    int width = 0;
    int height = 0;
    const Projection projection = fitProjection(false, extent, size, width, height);
    Canvas canvas(width, height, {22, 22, 26});
    std::set<uint16_t> doorFaces;

    if (map.state)
    {
        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            doorFaces.insert(door.faceIds.begin(), door.faceIds.end());
        }
    }

    struct Floor
    {
        size_t face = 0;
        double height = 0.0;
    };

    std::vector<Floor> floors;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (face.vertexIndices.size() < 3 || face.isPortal)
        {
            continue;
        }

        double normalZ = 0.0;
        double normalX = 0.0;
        double normalY = 0.0;
        double sumZ = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &current = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next =
                indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            normalX += (static_cast<double>(current.y) - next.y) * (static_cast<double>(current.z) + next.z);
            normalY += (static_cast<double>(current.z) - next.z) * (static_cast<double>(current.x) + next.x);
            normalZ += (static_cast<double>(current.x) - next.x) * (static_cast<double>(current.y) + next.y);
            sumZ += current.z;
        }

        const double length = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);

        if (length > 0.0 && normalZ / length > 0.5)
        {
            floors.push_back({faceIndex, sumZ / static_cast<double>(face.vertexIndices.size())});
        }
    }

    // Low floors first, so a gallery lies over the hall under it.
    std::stable_sort(floors.begin(), floors.end(), [](const Floor &left, const Floor &right)
    {
        return left.height < right.height;
    });

    for (const Floor &floor : floors)
    {
        const Game::IndoorFace &face = indoor.faces[floor.face];
        std::vector<Point> polygon;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
            polygon.push_back(projection(vertex.x, vertex.y, vertex.z));
        }

        const double share = highest > lowest ? (floor.height - lowest) / (highest - lowest) : 0.5;
        const uint8_t grey = static_cast<uint8_t>(58.0 + 62.0 * share);
        const bool isDoor = doorFaces.contains(static_cast<uint16_t>(floor.face));
        canvas.fill(polygon, isDoor ? Color{120, 60, 55} : Color{grey, grey, static_cast<uint8_t>(grey + 6)});

        for (size_t index = 0; index < polygon.size(); ++index)
        {
            canvas.line(polygon[index], polygon[(index + 1) % polygon.size()],
                {static_cast<uint8_t>(grey - 14), static_cast<uint8_t>(grey - 14), static_cast<uint8_t>(grey - 8)});
        }
    }

    for (const PlanMark &mark : marks)
    {
        canvas.dot(projection(mark.x, mark.y, mark.z), mark.radius, {mark.color[0], mark.color[1], mark.color[2]});
    }

    for (const PlanMark &mark : marks)
    {
        if (!mark.label.empty())
        {
            const Point point = projection(mark.x, mark.y, mark.z);
            canvas.label({point.x, point.y - mark.radius - 9.0}, mark.label, {20, 20, 30}, 1);
        }
    }

    return canvas.take();
}
}
