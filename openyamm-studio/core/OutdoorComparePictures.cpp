#include "core/OutdoorCompare.h"

#include "core/CoreMath.h"

#include <algorithm>
#include <cmath>

// The pictures of an outdoor comparison. Each is the map three times side by side, north up, 4 pixels to a cell:
// the original, the rebuild, and where they differ. A line of words over each panel says what it is; the colours:
//
//   heights.png   original and rebuild: the land from dark (low) to light (high), water blue, cells too steep to
//                 walk with a black dot. Difference: red where the rebuild lies higher, blue where lower, white
//                 where the same (full colour at 1024 units), with the 16-cell region grid.
//   ground.png    original and rebuild: each corner of each cell in its ground kind's colour (dirt brown, grass
//                 green, water blue, rock grey, snow white, sand yellow), road cells with a black middle.
//                 Difference: pale where the corner's kind is the same, red where the land's kind differs, magenta
//                 where one map has water and the other land; a road cell only in the original has a blue middle,
//                 only in the rebuild an orange one, in both a black one.
//   objects.png   original and rebuild: building footprints black on the pale land, decorations green dots, spawn
//                 points red squares, events yellow squares. Difference: footprints grey where both maps have a
//                 building, blue where only the original has, orange where only the rebuild has; spawn points and
//                 events one map has and the other lacks as crosses in the same blue and orange.
//   regions.png   the 64 regions with their names and scores in per cent, from green (the same) over yellow
//                 (70 %) to red (40 % and under).

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Cells = Game::OutdoorMapData::TerrainWidth;
constexpr int CellPixels = 4;
constexpr int PanelSide = Cells * CellPixels;
constexpr int Margin = 8;
constexpr int TitleBand = 20;
constexpr int FootprintSide = 1024;
constexpr double HalfMap = 32768.0;

struct Color
{
    uint8_t red = 0;
    uint8_t green = 0;
    uint8_t blue = 0;
};

// 5 by 7 glyphs, one byte per row, bit 4 the left column.
const std::array<uint8_t, 7> *glyphOf(char character)
{
    static const std::array<std::array<uint8_t, 7>, 26> Letters = {{
        {0x0e, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11}, {0x1e, 0x11, 0x11, 0x1e, 0x11, 0x11, 0x1e},
        {0x0e, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0e}, {0x1e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1e},
        {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x1f}, {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x10},
        {0x0e, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0f}, {0x11, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11},
        {0x0e, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0e}, {0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0c},
        {0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11}, {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1f},
        {0x11, 0x1b, 0x15, 0x15, 0x11, 0x11, 0x11}, {0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11},
        {0x0e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e}, {0x1e, 0x11, 0x11, 0x1e, 0x10, 0x10, 0x10},
        {0x0e, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0d}, {0x1e, 0x11, 0x11, 0x1e, 0x14, 0x12, 0x11},
        {0x0f, 0x10, 0x10, 0x0e, 0x01, 0x01, 0x1e}, {0x1f, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04},
        {0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e}, {0x11, 0x11, 0x11, 0x11, 0x11, 0x0a, 0x04},
        {0x11, 0x11, 0x11, 0x15, 0x15, 0x1b, 0x11}, {0x11, 0x11, 0x0a, 0x04, 0x0a, 0x11, 0x11},
        {0x11, 0x11, 0x0a, 0x04, 0x04, 0x04, 0x04}, {0x1f, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1f},
    }};
    static const std::array<std::array<uint8_t, 7>, 10> Digits = {{
        {0x0e, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0e}, {0x04, 0x0c, 0x04, 0x04, 0x04, 0x04, 0x0e},
        {0x0e, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1f}, {0x1f, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0e},
        {0x02, 0x06, 0x0a, 0x12, 0x1f, 0x02, 0x02}, {0x1f, 0x10, 0x1e, 0x01, 0x01, 0x11, 0x0e},
        {0x06, 0x08, 0x10, 0x1e, 0x11, 0x11, 0x0e}, {0x1f, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},
        {0x0e, 0x11, 0x11, 0x0e, 0x11, 0x11, 0x0e}, {0x0e, 0x11, 0x11, 0x0f, 0x01, 0x02, 0x0c},
    }};
    static const std::array<uint8_t, 7> Dot = {0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x0c};
    static const std::array<uint8_t, 7> Percent = {0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03};
    static const std::array<uint8_t, 7> Dash = {0x00, 0x00, 0x00, 0x1f, 0x00, 0x00, 0x00};
    static const std::array<uint8_t, 7> Colon = {0x00, 0x0c, 0x0c, 0x00, 0x0c, 0x0c, 0x00};
    static const std::array<uint8_t, 7> Comma = {0x00, 0x00, 0x00, 0x00, 0x0c, 0x04, 0x08};

    if (character >= 'a' && character <= 'z')
    {
        return &Letters[character - 'a'];
    }

    if (character >= 'A' && character <= 'Z')
    {
        return &Letters[character - 'A'];
    }

    if (character >= '0' && character <= '9')
    {
        return &Digits[character - '0'];
    }

    switch (character)
    {
    case '.':
        return &Dot;
    case '%':
        return &Percent;
    case '-':
        return &Dash;
    case ':':
        return &Colon;
    case ',':
        return &Comma;
    default:
        return nullptr;
    }
}

class Picture
{
public:
    Picture(int width, int height, Color background)
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

    void fill(int x, int y, int width, int height, Color color)
    {
        for (int row = y; row < y + height; ++row)
        {
            for (int column = x; column < x + width; ++column)
            {
                set(column, row, color);
            }
        }
    }

    void frame(int x, int y, int width, int height, Color color)
    {
        fill(x, y, width, 1, color);
        fill(x, y + height - 1, width, 1, color);
        fill(x, y, 1, height, color);
        fill(x + width - 1, y, 1, height, color);
    }

    void cross(int x, int y, int reach, Color color)
    {
        for (int step = -reach; step <= reach; ++step)
        {
            set(x + step, y + step, color);
            set(x + step, y - step, color);
            set(x + step + 1, y + step, color);
            set(x + step + 1, y - step, color);
        }
    }

    // Text in capitals, `scale` pixels to a glyph dot.
    void text(int x, int y, const std::string &words, Color color, int scale = 1)
    {
        int left = x;

        for (const char character : words)
        {
            const std::array<uint8_t, 7> *pGlyph = glyphOf(character);

            if (pGlyph != nullptr)
            {
                for (int row = 0; row < 7; ++row)
                {
                    for (int column = 0; column < 5; ++column)
                    {
                        if (((*pGlyph)[row] & (0x10 >> column)) != 0)
                        {
                            fill(left + column * scale, y + row * scale, scale, scale, color);
                        }
                    }
                }
            }

            left += 6 * scale;
        }
    }

    Image take()
    {
        return std::move(m_image);
    }

private:
    Image m_image;
};

int panelLeft(int panel)
{
    return Margin + panel * (PanelSide + Margin);
}

Picture threePanels(const std::string &third)
{
    Picture picture(3 * PanelSide + 4 * Margin, TitleBand + PanelSide + Margin, {24, 24, 28});
    const std::string titles[3] = {"ORIGINAL", "REBUILD", third};

    for (int panel = 0; panel < 3; ++panel)
    {
        picture.text(panelLeft(panel), 6, titles[panel], {235, 235, 235});
    }

    return picture;
}

void regionGrid(Picture &picture, int panel, Color color)
{
    for (int line = 16; line < Cells; line += 16)
    {
        for (int step = 0; step < PanelSide; step += 2)
        {
            picture.set(panelLeft(panel) + line * CellPixels, TitleBand + step, color);
            picture.set(panelLeft(panel) + step, TitleBand + line * CellPixels, color);
        }
    }
}

Color kindColor(const std::string &kind, size_t index)
{
    const auto has = [&kind](const char *pPart)
    {
        return kind.find(pPart) != std::string::npos;
    };

    if (kind == "dirt")
    {
        return {150, 112, 72};
    }

    if (kind == "water")
    {
        return {58, 108, 200};
    }

    if (has("gras"))
    {
        return {84, 150, 70};
    }

    if (has("sno"))
    {
        return {236, 236, 246};
    }

    if (has("gdtyl"))
    {
        return {170, 168, 158};
    }

    if (has("gstyl"))
    {
        return {82, 82, 90};
    }

    if (has("tar"))
    {
        return {30, 26, 30};
    }

    if (has("pln"))
    {
        return {196, 120, 60};
    }

    if (has("rk") || has("rock") || has("crk") || has("gs"))
    {
        return {128, 128, 132};
    }

    if (has("sand") || has("sd") || has("pls"))
    {
        return {222, 202, 140};
    }

    if (has("sw"))
    {
        return {92, 112, 70};
    }

    if (has("vol") || has("lav") || has("tar"))
    {
        return {86, 50, 44};
    }

    static const Color Others[4] = {{176, 96, 160}, {96, 170, 170}, {200, 140, 70}, {140, 140, 200}};
    return Others[index % 4];
}

Color heightColor(double height, double lowest, double highest)
{
    const double share = highest > lowest ? std::clamp((height - lowest) / (highest - lowest), 0.0, 1.0) : 0.0;
    const uint8_t grey = static_cast<uint8_t>(48.0 + 190.0 * share);
    return {grey, grey, static_cast<uint8_t>(grey * 0.92)};
}

double cellHeight(const std::vector<double> &heights, int x, int y)
{
    const int east = std::min(x + 1, Cells - 1);
    const int south = std::min(y + 1, Cells - 1);
    return (heights[y * Cells + x] + heights[y * Cells + east] + heights[south * Cells + x]
        + heights[south * Cells + east]) / 4.0;
}

double cellRelief(const std::vector<double> &heights, int x, int y)
{
    if (x + 1 >= Cells || y + 1 >= Cells)
    {
        return 0.0;
    }

    const double corners[4] = {heights[y * Cells + x], heights[y * Cells + x + 1], heights[(y + 1) * Cells + x],
        heights[(y + 1) * Cells + x + 1]};
    return *std::max_element(corners, corners + 4) - *std::min_element(corners, corners + 4);
}

Image heightsPicture(const OutdoorCompareResult &result)
{
    Picture picture = threePanels("DIFFERENCE: RED REBUILD HIGHER, BLUE LOWER");
    double lowest = result.originalHeights[0];
    double highest = result.originalHeights[0];

    for (size_t node = 0; node < result.originalHeights.size(); ++node)
    {
        lowest = std::min({lowest, result.originalHeights[node], result.rebuiltHeights[node]});
        highest = std::max({highest, result.originalHeights[node], result.rebuiltHeights[node]});
    }

    for (int panel = 0; panel < 2; ++panel)
    {
        const std::vector<double> &heights = panel == 0 ? result.originalHeights : result.rebuiltHeights;
        const std::vector<std::array<uint8_t, 4>> &ground = panel == 0 ? result.originalGround : result.rebuiltGround;

        for (int y = 0; y < Cells; ++y)
        {
            for (int x = 0; x < Cells; ++x)
            {
                const int left = panelLeft(panel) + x * CellPixels;
                const int top = TitleBand + y * CellPixels;
                picture.fill(left, top, CellPixels, CellPixels, heightColor(cellHeight(heights, x, y), lowest,
                    highest));

                for (int corner = 0; corner < 4; ++corner)
                {
                    if (ground[y * Cells + x][corner] == result.waterKind)
                    {
                        picture.fill(left + (corner % 2) * 2, top + (corner / 2) * 2, 2, 2, {58, 108, 200});
                    }
                }

                if (cellRelief(heights, x, y) > 512.0)
                {
                    picture.fill(left + 1, top + 1, 2, 2, {0, 0, 0});
                }
            }
        }
    }

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            const double delta = cellHeight(result.rebuiltHeights, x, y) - cellHeight(result.originalHeights, x, y);
            const double share = std::clamp(std::fabs(delta) / 1024.0, 0.0, 1.0);
            const uint8_t fade = static_cast<uint8_t>(255.0 - 215.0 * share);
            picture.fill(panelLeft(2) + x * CellPixels, TitleBand + y * CellPixels, CellPixels, CellPixels,
                delta > 0.0 ? Color{255, fade, fade} : Color{fade, fade, 255});
        }
    }

    regionGrid(picture, 2, {90, 90, 90});
    return picture.take();
}

Image groundPicture(const OutdoorCompareResult &result)
{
    Picture picture = threePanels("DIFFERENCE: RED OTHER GROUND, MAGENTA WATER AGAINST LAND");

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            const size_t cell = static_cast<size_t>(y) * Cells + x;
            const int top = TitleBand + y * CellPixels;

            for (int corner = 0; corner < 4; ++corner)
            {
                const uint8_t first = result.originalGround[cell][corner];
                const uint8_t second = result.rebuiltGround[cell][corner];
                const int dx = x * CellPixels + (corner % 2) * 2;
                const int dy = top + (corner / 2) * 2;
                picture.fill(panelLeft(0) + dx, dy, 2, 2, kindColor(result.groundKinds[first], first));
                picture.fill(panelLeft(1) + dx, dy, 2, 2, kindColor(result.groundKinds[second], second));
                const bool water = first == result.waterKind || second == result.waterKind;
                picture.fill(panelLeft(2) + dx, dy, 2, 2, first == second ? (water ? Color{200, 212, 236}
                    : Color{232, 232, 226}) : (water ? Color{214, 60, 200} : Color{220, 62, 50}));
            }

            const bool firstRoad = result.originalRoads[cell] != 0;
            const bool secondRoad = result.rebuiltRoads[cell] != 0;

            if (firstRoad)
            {
                picture.fill(panelLeft(0) + x * CellPixels + 1, top + 1, 2, 2, {20, 20, 20});
            }

            if (secondRoad)
            {
                picture.fill(panelLeft(1) + x * CellPixels + 1, top + 1, 2, 2, {20, 20, 20});
            }

            if (firstRoad || secondRoad)
            {
                picture.fill(panelLeft(2) + x * CellPixels + 1, top + 1, 2, 2, firstRoad && secondRoad
                    ? Color{20, 20, 20} : (firstRoad ? Color{40, 90, 230} : Color{240, 140, 20}));
            }
        }
    }

    regionGrid(picture, 2, {120, 120, 120});
    return picture.take();
}

void drawPlaces(Picture &picture, int panel, const std::vector<OutdoorComparePlace> &places, Color color, int size,
    bool asCross)
{
    for (const OutdoorComparePlace &place : places)
    {
        const int x = panelLeft(panel) + static_cast<int>((place.x + HalfMap) / (2.0 * HalfMap) * PanelSide);
        const int y = TitleBand + static_cast<int>((HalfMap - place.y) / (2.0 * HalfMap) * PanelSide);

        if (x < panelLeft(panel) || x >= panelLeft(panel) + PanelSide || y < TitleBand || y >= TitleBand + PanelSide)
        {
            continue;
        }

        if (asCross)
        {
            picture.cross(x, y, size, color);
        }
        else
        {
            picture.fill(x - size / 2, y - size / 2, size, size, color);
        }
    }
}

Image objectsPicture(const OutdoorCompareResult &result)
{
    Picture picture = threePanels("DIFFERENCE: BLUE ONLY ORIGINAL, ORANGE ONLY REBUILD, GREY BOTH");
    const Color blue = {40, 90, 230};
    const Color orange = {240, 130, 20};
    const int footprintStep = FootprintSide / PanelSide;

    for (int row = 0; row < PanelSide; ++row)
    {
        for (int column = 0; column < PanelSide; ++column)
        {
            const size_t cell = static_cast<size_t>(row / CellPixels) * Cells + column / CellPixels;
            const int corner = ((row % CellPixels) / 2) * 2 + (column % CellPixels) / 2;
            const bool firstWater = result.originalGround[cell][corner] == result.waterKind;
            const bool secondWater = result.rebuiltGround[cell][corner] == result.waterKind;
            const size_t pixel = static_cast<size_t>(row * footprintStep) * FootprintSide + column * footprintStep;
            bool first = false;
            bool second = false;

            for (int dy = 0; dy < footprintStep; ++dy)
            {
                for (int dx = 0; dx < footprintStep; ++dx)
                {
                    first = first || result.originalFootprints[pixel + dy * FootprintSide + dx] != 0;
                    second = second || result.rebuiltFootprints[pixel + dy * FootprintSide + dx] != 0;
                }
            }

            const Color land = {226, 226, 214};
            const Color water = {190, 206, 236};
            picture.set(panelLeft(0) + column, TitleBand + row, first ? Color{30, 30, 30}
                : (firstWater ? water : land));
            picture.set(panelLeft(1) + column, TitleBand + row, second ? Color{30, 30, 30}
                : (secondWater ? water : land));
            picture.set(panelLeft(2) + column, TitleBand + row, first && second ? Color{110, 110, 110}
                : (first ? blue : (second ? orange : (firstWater ? water : land))));
        }
    }

    drawPlaces(picture, 0, result.originalDecorationPlaces, {40, 150, 50}, 2, false);
    drawPlaces(picture, 1, result.rebuiltDecorationPlaces, {40, 150, 50}, 2, false);
    drawPlaces(picture, 0, result.originalEventPlaces, {230, 200, 20}, 3, false);
    drawPlaces(picture, 1, result.rebuiltEventPlaces, {230, 200, 20}, 3, false);
    drawPlaces(picture, 0, result.originalSpawnPlaces, {220, 40, 40}, 4, false);
    drawPlaces(picture, 1, result.rebuiltSpawnPlaces, {220, 40, 40}, 4, false);
    drawPlaces(picture, 2, result.missingEvents, blue, 2, true);
    drawPlaces(picture, 2, result.extraEvents, orange, 2, true);
    drawPlaces(picture, 2, result.missingSpawns, blue, 4, true);
    drawPlaces(picture, 2, result.extraSpawns, orange, 4, true);
    regionGrid(picture, 2, {150, 150, 150});
    return picture.take();
}

Color scoreColor(double score)
{
    const double value = std::clamp((score - 0.4) / 0.6, 0.0, 1.0);
    return {static_cast<uint8_t>(value < 0.5 ? 226.0 : 226.0 * (1.0 - value) * 2.0),
        static_cast<uint8_t>(value < 0.5 ? 60.0 + 300.0 * value : 210.0 - 30.0 * (value - 0.5)), 60};
}

Image regionsPicture(const OutdoorCompareResult &result)
{
    const int side = 120;
    Picture picture(8 * side + 2 * Margin, TitleBand + 8 * side + Margin, {24, 24, 28});
    picture.text(Margin, 6, "REGIONS OF 16 X 16 CELLS: NAME AND SCORE IN PER CENT. WHOLE MAP "
        + formatNumber(std::round(result.score * 1000.0) / 10.0) + " %", {235, 235, 235});

    for (const OutdoorCompareRegion &region : result.regions)
    {
        const int left = Margin + region.column * side;
        const int top = TitleBand + region.row * side;
        picture.fill(left + 1, top + 1, side - 2, side - 2, scoreColor(region.score));
        picture.text(left + 8, top + 8, region.name, {0, 0, 0}, 2);
        picture.text(left + 8, top + 34, formatNumber(std::round(region.score * 1000.0) / 10.0), {0, 0, 0}, 3);
    }

    return picture.take();
}
}

std::vector<std::pair<std::string, Image>> outdoorComparePictures(const OutdoorCompareResult &result)
{
    std::vector<std::pair<std::string, Image>> pictures;
    pictures.push_back({"heights.png", heightsPicture(result)});
    pictures.push_back({"ground.png", groundPicture(result)});
    pictures.push_back({"objects.png", objectsPicture(result)});
    pictures.push_back({"regions.png", regionsPicture(result)});
    return pictures;
}

std::string outdoorCompareShotsYaml(const OutdoorCompareResult &result)
{
    const auto whole = [](double value)
    {
        return formatNumber(std::round(value));
    };
    const auto ground = [&result](double x, double y)
    {
        const int cellX = std::clamp(static_cast<int>(std::floor((x + HalfMap) / 512.0)), 0, Cells - 1);
        const int cellY = std::clamp(static_cast<int>(std::floor((HalfMap - y) / 512.0)), 0, Cells - 1);
        return std::max(result.originalHeights[cellY * Cells + cellX], result.rebuiltHeights[cellY * Cells + cellX]);
    };
    // Written by hand: a flat list of scalars, the same on every platform.
    std::string text = "# Views for calibration/outdoor_ingame.py from `oymap compare " + result.originalName
        + " --with " + result.rebuiltName + "`: the twelve worst regions, each seen from its south side, 3000 "
          "above the higher of the two grounds (the game's fog hides the land from much farther); then the rim's six "
          "worst regions (rim-*) as the party sees them, from the square's edge at eye height.\n# at: x, y, z "
          "in map units; yaw in radians, 0 east, counter-clockwise; pitch in degrees, negative down.\nshots:\n";
    for (size_t index = 0; index < result.worstRegions.size() && index < 12; ++index)
    {
        const OutdoorCompareRegion &region = result.regions[result.worstRegions[index]];
        const double x = (region.column * 16 + 8 - 64) * 512.0;
        const double y = (64 - (region.row * 16 + 16)) * 512.0 - 2048.0;
        text += "  - {name: region-" + region.name + ", at: [" + whole(x) + ", " + whole(y) + ", "
            + whole(ground(x, y) + 3000.0) + "], yaw: 1.5708, pitch: -30, score: "
            + formatNumber(std::round(region.score * 1000.0) / 1000.0) + "}\n";
    }

    // The rim as the party sees it: the six worst regions the skyline is judged in, each seen from where the
    // measure's eyes stand, four cells in from the square's edge where it comes nearest, at the height of an eye
    // over the higher ground, looking out at the region's middle.
    std::vector<size_t> rim;

    for (const size_t index : result.worstRegions)
    {
        if (result.rimBySkyline && result.regions[index].skylineRays != 0 && rim.size() < 6)
        {
            rim.push_back(index);
        }
    }

    for (const size_t index : rim)
    {
        const OutdoorCompareRegion &region = result.regions[index];
        const double middleX = region.column * 16 + 8.0;
        const double middleY = region.row * 16 + 8.0;
        const double eyeX = std::clamp(middleX, 23.0, 105.0);
        const double eyeY = std::clamp(middleY, 23.0, 105.0);
        const double x = (eyeX - 64) * 512.0;
        const double y = (64 - eyeY) * 512.0;
        const double yaw = oy::atan2(-(middleY - eyeY), middleX - eyeX);
        text += "  - {name: rim-" + region.name + ", at: [" + whole(x) + ", " + whole(y) + ", "
            + whole(ground(x, y) + 192.0) + "], yaw: " + formatNumber(std::round(yaw * 10000.0) / 10000.0)
            + ", pitch: 4, score: " + formatNumber(std::round(region.score * 1000.0) / 1000.0) + "}\n";
    }

    return text;
}
}
