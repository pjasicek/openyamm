#include "core/OutdoorCompare.h"

#include "core/CoreMath.h"
#include "game/FaceEnums.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <numbers>
#include <numeric>

// How two outdoor maps are compared, in plain words.
//
// Both maps are read on the terrain's own grid: 128 x 128 height nodes 512 units apart, 128 x 128 cells of tiles.
// Regions are blocks of 16 x 16 cells, named by a letter for the column (A in the west) and a number for the row
// (1 in the north).
//
// Ground is read from the tiles the way the tile sets are drawn. A tile set has a plain tile with variants and
// twelve tiles that lead over to dirt: four with dirt along one side, four with dirt on three corners and four
// with dirt on one corner. So a cell's tile says what lies on each of its four corners: the set's own ground or
// dirt. Water is such a set (its tiles toward dirt are the shore), and a road tile is dirt with a road on it. The
// comparison counts corners, so a shore tile is half water and a road keeps its dirt.
//
// The parts, each from 0 to 1, and their share of the score:
//   heights      15 %  per node of the square the party walks (nodes 19 to 109), 1 - |difference| / 512, never
//                      below 0 (512 is the step a walker cannot take)
//   relief        6 %  per cell of the square, the relief is its highest corner minus its lowest; 1 - |difference|
//                      / the larger of the two reliefs (at least 128): flat ground where the original is rough loses
//   cliffs        6 %  cells of the square too steep to walk (relief over 512, the game's rule): how many of the
//                      original's have one of the rebuild's on them or beside them, and the other way round (their
//                      harmonic mean)
//   rim           8 %  the land beyond the square (half the map), which the party never walks and sees only as a
//                      skyline from inside it. Eyes stand 4 cells inside the square's edge, one every 2 cells along
//                      it, 192 over the original's land (the same eye in both maps; the nearest land beyond the edge
//                      lies 4 cells off, so a node beside the edge does not decide every line from one eye), and
//                      look out over a fan of 150 degrees, a sight
//                      line every 3 degrees; a line's horizon is the highest angle of the land beyond the square
//                      along it. The lines are grouped by the region their horizon lies in, in the original; in a
//                      group, 0.75 of: the two maps' horizons sorted and compared rank by rank (1 - the mean
//                      difference / 6 degrees, never below 0: the same skyline wherever its tops stand, so a rim
//                      described by its form and not traced can agree) and 0.25 of: how alike their ups and downs
//                      from one line to the next are (a smooth skyline where the original's is jagged loses). A
//                      group's weight is its number of lines.
// (Until 2026-11-13, `--without rim`: heights 20 %, relief 8 % and cliffs 7 % over every node and cell, the rim
// node by node with the rest; the rim's skyline is reported with no weight.)
//   water        10 %  quarter cells of water in both maps over those in either
//   ground       12 %  quarter cells of land with the same ground kind in both over all land quarters of either
//   roads         8 %  0.7 of: road cells of each map with a road cell of the other on them or beside them
//                      (harmonic mean); 0.3 of: road cells in both over road cells in either
//   buildings    15 %  footprints are the plan of every face of a building model on a grid of 64 units (a face
//                      that stands upright covers the pixels its foot runs through, so a ring wall without a
//                      roof has its ring, up to its top edge at each of them: a railing over an arch rises and
//                      falls with it); a building's top over a pixel is its highest face there, measured from
//                      the land under it. A model whose pixels others cover stands at the middle of its corners
//                      (not the centre the file stores: Harmondale's wagon pieces store garbage).
//                      0.3 of: area under buildings in both over area in either. 0.3 of: models found: the share
//                      of the original's models at least half of whose own area lies under buildings of the
//                      rebuild, and the same the other way round (their harmonic mean); how a building is cut
//                      into models does not count. 0.4 of: form: over the area under buildings in either map, how
//                      alike the tops are where both have one (1 - |difference| / 256, never below 0: a storey
//                      off is nothing) and 0 where only one has; a box where the original has a tower, a flat
//                      top where it has a roof, lose here. The report (differences.json `buildings`, `matched`)
//                      pairs models as buildings: a model joins one of the other map when at least half of the
//                      smaller one's area lies under it, and each group so joined is one building in both maps,
//                      however each cuts it into models (a ring of four pieces in one model against four walls);
//                      what is left pairs one to one by shared area, the largest first.
//   decorations   8 %  (party starts are markers, not decorations: left out.)
//                      decorations are paired nearest first within 8192 units (sixteen cells, a region's width), each
//                      once: half of the part is the pairs of the same kind (the name), half the pairs of any
//                      kind (density), each over the mean of the two maps' counts. Where the regions' borders
//                      run does not count: a clump across a border is the same clump. (Until 2026-11-13 the
//                      part counted by region and kind, and a clump that a border cut scored lower than one it
//                      missed.) A scatter's places inside its area are the build's own, so a kind spread
//                      evenly over a wide area pairs as well as the original's is even; clumps pair with clumps
//   spawns        4 %  spawn points paired nearest first within 2048 units: 1 a pair of the same monster slot,
//                      0.5 a pair of different slots, over the larger count
//   events        8 %  what can be clicked: every event on building faces (at the middle of its faces) and on
//                      decorations, named by what it leads to (a house, another map) when the scripts tell. An
//                      event number on models that stand apart (one name for fifteen houses, one title on two
//                      signposts) is a thing at each of them, not one thing at their common middle; models that
//                      touch (a ship cut into five) are one. Paired nearest first within 2048 units with the same
//                      name, over the larger count. An event whose handler has no title and does nothing (the
//                      flow lists it with empty paths) is no thing to click and is left out.
// differences.json names every decoration without a partner of its kind, in each map.
// A part of which neither map has anything scores 1. A region's score leaves out the parts neither map has
// anything of there.

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Cells = Game::OutdoorMapData::TerrainWidth;
constexpr size_t CellTotal = static_cast<size_t>(Cells) * Cells;
constexpr double CellSize = Game::OutdoorMapData::TerrainTileSize;
constexpr double HalfMap = CellSize * Cells / 2.0;
constexpr int RegionCells = 16;
constexpr int RegionsPerSide = Cells / RegionCells;
constexpr size_t RegionTotal = static_cast<size_t>(RegionsPerSide) * RegionsPerSide;
constexpr double SteepRelief = 512.0;
constexpr double HeightReach = 512.0;
constexpr double ReliefFloor = 128.0;
constexpr int FootprintSide = 1024;
constexpr double FootprintUnit = CellSize * Cells / FootprintSide;
constexpr double PairReach = 2048.0;
// How far apart two decorations may stand and still be the same decoration of the two maps: sixteen cells, the
// width of a region (the scale the part had when it counted by region). At eight cells the two rebuilds of
// 2026-11-13 measured 82.3 and 81.3 %, at sixteen 94.3 and 94.6 %: their scatter is written by blocks of that size, and a
// kind with three trees to a block finds its partner farther off than eight cells as often as not.
constexpr double DecorationReach = 8192.0;
// The difference of two buildings' tops at which their forms count as nothing alike: a storey.
constexpr double FormReach = 256.0;
constexpr int PartyStartDecoration = 13;
constexpr int FirstSetTile = 90;
constexpr int SetTiles = 36;
constexpr int LastSetTile = 234;

enum PartIndex : size_t
{
    PartHeights = 0,
    PartRelief,
    PartCliffs,
    PartWater,
    PartGround,
    PartRoads,
    PartBuildings,
    PartDecorations,
    PartSpawns,
    PartEvents,
    PartRim,
    PartCount,
};

struct PartDefinition
{
    const char *pId;
    const char *pTitle;
    double weight;
};

const PartDefinition PartDefinitions[PartCount] = {
    {"heights", "heights of the land", 0.15},
    {"relief", "roughness of the ground", 0.06},
    {"cliffs", "cells too steep to walk", 0.06},
    {"water", "water and shore", 0.10},
    {"ground", "ground kinds", 0.12},
    {"roads", "roads", 0.08},
    {"buildings", "buildings", 0.15},
    {"decorations", "decorations by kind and density", 0.08},
    {"spawns", "spawn points", 0.04},
    {"events", "entrances and other events", 0.08},
    {"rim", "the rim's skyline seen from the square's edge", 0.08},
};

// The weights before 2026-11-13 (`--without rim`): the land node by node over the whole map, no skyline.
constexpr std::array<double, PartCount> NodeByNodeWeights = {0.20, 0.08, 0.07, 0.10, 0.12, 0.08, 0.15, 0.08, 0.04,
    0.08, 0.0};

// The square the party walks (OutdoorRim.h: nodes 19 to 109) and how its rim is looked at.
constexpr int SquareFirst = 19;
constexpr int SquareLast = 109;
constexpr double SkylineEye = 192.0;
constexpr int SkylineEyeStep = 2;
constexpr int SkylineEyeInset = 4;
constexpr int SkylineFan = 75;
constexpr int SkylineRayStep = 3;
constexpr double SkylineSampleCells = 0.5;
constexpr double SkylineReach = 6.0;
constexpr double SkylineJagFloor = 0.5;

bool nodeInSquare(int x, int y)
{
    return x >= SquareFirst && x <= SquareLast && y >= SquareFirst && y <= SquareLast;
}

// A cell of the square: all four of its corners are.
bool cellInSquare(int x, int y)
{
    return nodeInSquare(x, y) && nodeInSquare(x + 1, y + 1);
}

// Which corners of a cell (north-west, north-east, south-west, south-east) hold dirt, for the twelve tiles of a
// set that lead over to dirt (offsets 12 to 23 in the set).
constexpr std::array<std::array<uint8_t, 4>, 12> DirtCorners = {{
    {1, 1, 0, 1}, {0, 1, 1, 1}, {1, 1, 1, 0}, {1, 0, 1, 1},
    {0, 1, 0, 1}, {1, 0, 1, 0}, {1, 1, 0, 0}, {0, 0, 1, 1},
    {0, 1, 0, 0}, {0, 0, 0, 1}, {1, 0, 0, 0}, {0, 0, 1, 0},
}};

struct Building
{
    std::string name;
    double centerX = 0.0;
    double centerY = 0.0;
    double base = 0.0;
    double height = 0.0;
    size_t pixels = 0;
    double pixelSumX = 0.0;
    double pixelSumY = 0.0;
    // How many of its pixels lie under a building of the other map.
    size_t covered = 0;
};

struct Place
{
    std::string what;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct Reading
{
    std::vector<double> heights;
    std::vector<std::array<uint8_t, 4>> ground;
    // 0: no road; else the road tile's offset in its set + 1.
    std::vector<uint8_t> roads;
    std::vector<double> relief;
    std::vector<Building> buildings;
    std::vector<uint16_t> footprints;
    // Per pixel of `footprints`: the height of the highest face there, map units; meaningless where no building.
    std::vector<float> tops;
    std::vector<Place> decorations;
    std::vector<Place> spawns;
    std::vector<Place> events;
};

std::string lowered(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

double rounded(double value, int digits)
{
    const double scale = oy::pow(10.0, digits);
    return std::round(value * scale) / scale;
}

std::string wholeText(double value)
{
    return formatNumber(std::round(value));
}

std::string percentText(double share)
{
    return formatNumber(rounded(share * 100.0, 1)) + " %";
}

int regionOfCell(int x, int y)
{
    return (std::clamp(y, 0, Cells - 1) / RegionCells) * RegionsPerSide + std::clamp(x, 0, Cells - 1) / RegionCells;
}

int regionOfWorld(double x, double y)
{
    return regionOfCell(static_cast<int>(std::floor((x + HalfMap) / CellSize)),
        static_cast<int>(std::floor((HalfMap - y) / CellSize)));
}

class KindTable
{
public:
    uint8_t idOf(const std::string &name)
    {
        for (size_t index = 0; index < m_names.size(); ++index)
        {
            if (m_names[index] == name)
            {
                return static_cast<uint8_t>(index);
            }
        }

        m_names.push_back(name);
        return static_cast<uint8_t>(m_names.size() - 1);
    }

    const std::vector<std::string> &names() const
    {
        return m_names;
    }

private:
    std::vector<std::string> m_names;
};

// Fills the pixels of the footprint grid whose middle lies inside the polygon (even-odd), given in grid pixels.
template <typename Visit>
void forEachPixel(const std::vector<std::array<double, 2>> &polygon, Visit visit)
{
    if (polygon.size() < 3)
    {
        return;
    }

    double top = polygon[0][1];
    double bottom = polygon[0][1];

    for (const std::array<double, 2> &point : polygon)
    {
        top = std::min(top, point[1]);
        bottom = std::max(bottom, point[1]);
    }

    const int firstRow = std::max(0, static_cast<int>(std::ceil(top - 0.5)));
    const int lastRow = std::min(FootprintSide - 1, static_cast<int>(std::floor(bottom - 0.5)));
    std::vector<double> crossings;

    for (int row = firstRow; row <= lastRow; ++row)
    {
        const double y = row + 0.5;
        crossings.clear();

        for (size_t index = 0; index < polygon.size(); ++index)
        {
            const std::array<double, 2> &first = polygon[index];
            const std::array<double, 2> &second = polygon[(index + 1) % polygon.size()];

            if ((first[1] <= y && second[1] > y) || (second[1] <= y && first[1] > y))
            {
                crossings.push_back(first[0] + (y - first[1]) / (second[1] - first[1]) * (second[0] - first[0]));
            }
        }

        std::sort(crossings.begin(), crossings.end());

        for (size_t index = 0; index + 1 < crossings.size(); index += 2)
        {
            const int from = std::max(0, static_cast<int>(std::ceil(crossings[index] - 0.5)));
            const int to = std::min(FootprintSide - 1, static_cast<int>(std::floor(crossings[index + 1] - 0.5)));

            for (int column = from; column <= to; ++column)
            {
                visit(static_cast<size_t>(row) * FootprintSide + column, row, column);
            }
        }
    }
}

bool readSide(const OutdoorCompareSide &side, KindTable &kinds, Reading &reading, std::string &errorMessage)
{
    if (side.pMap == nullptr || side.pMap->heightMap.size() != CellTotal || side.pMap->tileMap.size() != CellTotal)
    {
        errorMessage = side.name + " is not an outdoor map with a 128 x 128 terrain";
        return false;
    }

    const Game::OutdoorMapData &map = *side.pMap;
    reading.heights.resize(CellTotal);

    for (size_t node = 0; node < CellTotal; ++node)
    {
        reading.heights[node] = map.heightMap[node] * static_cast<double>(Game::OutdoorMapData::TerrainHeightScale);
    }

    // The relief of the 127 x 127 cells the game draws; the last row and column have no far nodes.
    reading.relief.assign(CellTotal, 0.0);

    for (int y = 0; y + 1 < Cells; ++y)
    {
        for (int x = 0; x + 1 < Cells; ++x)
        {
            const double corners[4] = {reading.heights[y * Cells + x], reading.heights[y * Cells + x + 1],
                reading.heights[(y + 1) * Cells + x], reading.heights[(y + 1) * Cells + x + 1]};
            reading.relief[y * Cells + x] = *std::max_element(corners, corners + 4)
                - *std::min_element(corners, corners + 4);
        }
    }

    const bool hasTiles = side.tiles.size() >= 256;
    // The map's plain ground, which every set's tiles lead over to: dirt (tile set 4), or what the map's master tile
    // makes of the tiles below 90 (Shadowspire's grey dust, Ironsand's hardpan).
    const auto plainKind = [&kinds](const Game::TerrainTileDescriptor &descriptor)
    {
        return descriptor.tileset == 4 || descriptor.textureName.empty() || descriptor.textureName == "pending"
            ? kinds.idOf("dirt") : kinds.idOf(lowered(descriptor.textureName));
    };
    const uint8_t dirt = hasTiles ? plainKind(side.tiles[1]) : kinds.idOf("dirt");
    reading.ground.assign(CellTotal, {dirt, dirt, dirt, dirt});
    reading.roads.assign(CellTotal, 0);

    for (size_t cell = 0; cell < CellTotal; ++cell)
    {
        const int tile = map.tileMap[cell];

        if (!hasTiles)
        {
            const uint8_t plain = kinds.idOf("ground");
            reading.ground[cell] = {plain, plain, plain, plain};
            continue;
        }

        const Game::TerrainTileDescriptor &descriptor = side.tiles[tile];

        if (tile < FirstSetTile || tile >= LastSetTile)
        {
            // The tiles outside the four sets: plain dirt (tile set 4) and whatever else a world keeps there.
            const uint8_t kind = descriptor.tileset == 4 || descriptor.textureName.empty()
                || descriptor.textureName == "pending" ? dirt : plainKind(descriptor);
            reading.ground[cell] = {kind, kind, kind, kind};
            continue;
        }

        const int base = FirstSetTile + ((tile - FirstSetTile) / SetTiles) * SetTiles;
        const int offset = tile - base;
        const Game::TerrainTileDescriptor &baseDescriptor = side.tiles[base];

        // A road set's first tile is itself a tile over dirt (a crossing).
        if ((baseDescriptor.flags & Game::TerrainTileFlagTransition) != 0)
        {
            reading.roads[cell] = static_cast<uint8_t>(offset + 1);
            continue;
        }

        // Water is water whatever its set; tar and lava are kinds of their own (drawn as liquids, never as water).
        const std::string setName = lowered(baseDescriptor.textureName);
        const bool liquid = (baseDescriptor.flags & Game::TerrainTileFlagWater) != 0;
        const uint8_t kind = liquid && setName.find("wtr") != std::string::npos ? kinds.idOf("water")
            : kinds.idOf(setName);
        reading.ground[cell] = {kind, kind, kind, kind};

        if (offset >= 12 && offset < 24)
        {
            for (size_t corner = 0; corner < 4; ++corner)
            {
                if (DirtCorners[offset - 12][corner] != 0)
                {
                    reading.ground[cell][corner] = dirt;
                }
            }
        }
    }

    reading.footprints.assign(static_cast<size_t>(FootprintSide) * FootprintSide, 0);
    reading.tops.assign(static_cast<size_t>(FootprintSide) * FootprintSide, -1.0e9f);
    // An event whose handler has no title and does nothing is no thing to click; nor, once the script is read, one
    // it gives neither a handler nor a name.
    const auto clickable = [&side](int event)
    {
        return !side.emptyEvents.contains(event)
            && (!side.eventsRead || side.handledEvents.contains(event) || side.namedEvents.contains(event));
    };
    // An event's faces, model by model: the sums of their middles, their number, and the model's bounds.
    struct EventOnModel
    {
        std::array<double, 4> sums = {0.0, 0.0, 0.0, 0.0};
        std::array<double, 4> bounds = {0.0, 0.0, 0.0, 0.0};
    };
    std::map<int, std::map<size_t, EventOnModel>> eventSums;

    for (size_t index = 0; index < map.bmodels.size() && index < 65534; ++index)
    {
        const Game::OutdoorBModel &bmodel = map.bmodels[index];
        Building building;
        building.name = bmodel.name;

        if (bmodel.vertices.empty())
        {
            reading.buildings.push_back(building);
            continue;
        }

        double lowest = bmodel.vertices[0].z;
        double highest = bmodel.vertices[0].z;
        // The model's bounds in plan, from its corners (west, south, east, north).
        std::array<double, 4> modelBounds = {static_cast<double>(bmodel.vertices[0].x),
            static_cast<double>(bmodel.vertices[0].y), static_cast<double>(bmodel.vertices[0].x),
            static_cast<double>(bmodel.vertices[0].y)};

        // What the player sees and stands on: an invisible face (a barrier, a ceiling over a bridge's span) is
        // neither a building's top nor its plan, nor its height. A model of invisible faces only is read whole.
        const auto invisible = [](const Game::OutdoorBModelFace &face)
        {
            return Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible);
        };
        std::vector<bool> seen(bmodel.vertices.size(), false);
        bool anySeen = false;

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (!invisible(face) && vertexIndex < seen.size())
                {
                    seen[vertexIndex] = true;
                    anySeen = true;
                }
            }
        }

        bool first = true;

        for (size_t vertexIndex = 0; vertexIndex < bmodel.vertices.size(); ++vertexIndex)
        {
            const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];

            if (anySeen && !seen[vertexIndex])
            {
                continue;
            }

            if (first)
            {
                lowest = highest = vertex.z;
                modelBounds = {static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                    static_cast<double>(vertex.x), static_cast<double>(vertex.y)};
                first = false;
            }

            lowest = std::min(lowest, static_cast<double>(vertex.z));
            highest = std::max(highest, static_cast<double>(vertex.z));
            modelBounds = {std::min(modelBounds[0], static_cast<double>(vertex.x)),
                std::min(modelBounds[1], static_cast<double>(vertex.y)),
                std::max(modelBounds[2], static_cast<double>(vertex.x)),
                std::max(modelBounds[3], static_cast<double>(vertex.y))};
        }

        building.base = lowest;
        building.height = highest - lowest;
        // Where a model that keeps no pixel of its own (its plan covered by others) stands: the middle of its
        // corners, not the centre the file stores (Harmondale's Wagon_W_5 stores [0, -5187]).
        building.centerX = (modelBounds[0] + modelBounds[2]) * 0.5;
        building.centerY = (modelBounds[1] + modelBounds[3]) * 0.5;
        std::vector<std::array<double, 2>> polygon;

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            polygon.clear();
            double sumX = 0.0;
            double sumY = 0.0;
            double sumZ = 0.0;

            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= bmodel.vertices.size())
                {
                    continue;
                }

                const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];
                polygon.push_back({(vertex.x + HalfMap) / FootprintUnit, (HalfMap - vertex.y) / FootprintUnit});
                sumX += vertex.x;
                sumY += vertex.y;
                sumZ += vertex.z;
            }

            if (anySeen && invisible(face))
            {
                // Still a place to click (an invisible event face), never a top.
                if (face.cogTriggeredNumber != 0 && !polygon.empty() && clickable(face.cogTriggeredNumber))
                {
                    EventOnModel &onModel = eventSums[face.cogTriggeredNumber][index];
                    onModel.sums[0] += sumX / polygon.size();
                    onModel.sums[1] += sumY / polygon.size();
                    onModel.sums[2] += sumZ / polygon.size();
                    onModel.sums[3] += 1.0;
                    onModel.bounds = modelBounds;
                }

                continue;
            }

            // The face's plane from its corners (Newell): its height over a pixel.
            double normal[3] = {0.0, 0.0, 0.0};
            const size_t corners = face.vertexIndices.size();

            for (size_t corner = 0; corner < corners; ++corner)
            {
                if (face.vertexIndices[corner] >= bmodel.vertices.size()
                    || face.vertexIndices[(corner + 1) % corners] >= bmodel.vertices.size())
                {
                    continue;
                }

                const Game::OutdoorBModelVertex &from = bmodel.vertices[face.vertexIndices[corner]];
                const Game::OutdoorBModelVertex &to = bmodel.vertices[face.vertexIndices[(corner + 1) % corners]];
                normal[0] += (static_cast<double>(from.y) - to.y) * (static_cast<double>(from.z) + to.z);
                normal[1] += (static_cast<double>(from.z) - to.z) * (static_cast<double>(from.x) + to.x);
                normal[2] += (static_cast<double>(from.x) - to.x) * (static_cast<double>(from.y) + to.y);
            }

            const double normalLength = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1]
                + normal[2] * normal[2]);
            const bool lies = normalLength > 0.0 && std::fabs(normal[2]) / normalLength > 0.05 && !polygon.empty();
            const double anchorX = polygon.empty() ? 0.0 : polygon[0][0] * FootprintUnit - HalfMap;
            const double anchorY = polygon.empty() ? 0.0 : HalfMap - polygon[0][1] * FootprintUnit;
            const uint16_t value = static_cast<uint16_t>(index + 1);
            forEachPixel(polygon, [&](size_t pixel, int row, int column)
            {
                reading.footprints[pixel] = value;

                if (lies)
                {
                    const double x = (column + 0.5) * FootprintUnit - HalfMap;
                    const double y = HalfMap - (row + 0.5) * FootprintUnit;
                    const double z = bmodel.vertices[face.vertexIndices[0]].z
                        - (normal[0] * (x - anchorX) + normal[1] * (y - anchorY)) / normal[2];
                    reading.tops[pixel] = std::max(reading.tops[pixel], static_cast<float>(z));
                }
            });

            if (!lies && polygon.size() >= 2)
            {
                // A face that stands upright has no plan area: it covers the pixels its foot runs through (a wall
                // without a roof over it, an open ring), up to its top edge there: a railing that rises over an
                // arch is as high as it is at each point, not everywhere as high as its highest.
                std::vector<std::array<double, 3>> corners3;

                for (const uint16_t vertexIndex : face.vertexIndices)
                {
                    if (vertexIndex < bmodel.vertices.size())
                    {
                        const Game::OutdoorBModelVertex &vertex = bmodel.vertices[vertexIndex];
                        corners3.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                            static_cast<double>(vertex.z)});
                    }
                }

                // The face's way across the plan: from its first corner to the corner farthest from it.
                std::array<double, 2> across = {0.0, 0.0};

                for (const std::array<double, 3> &corner : corners3)
                {
                    const std::array<double, 2> offset = {corner[0] - corners3[0][0], corner[1] - corners3[0][1]};

                    if (oy::hypot(offset[0], offset[1]) > oy::hypot(across[0], across[1]))
                    {
                        across = offset;
                    }
                }

                const double acrossLength = std::max(oy::hypot(across[0], across[1]), 1.0e-9);
                across = {across[0] / acrossLength, across[1] / acrossLength};
                const auto topAt = [&corners3, &across](double x, double y)
                {
                    const double along = (x - corners3[0][0]) * across[0] + (y - corners3[0][1]) * across[1];
                    double top = -1.0e9;
                    double nearestTop = -1.0e9;
                    double nearest = 1.0e18;

                    for (size_t corner = 0; corner < corners3.size(); ++corner)
                    {
                        const std::array<double, 3> &from = corners3[corner];
                        const std::array<double, 3> &to = corners3[(corner + 1) % corners3.size()];
                        const double fromAlong = (from[0] - corners3[0][0]) * across[0]
                            + (from[1] - corners3[0][1]) * across[1];
                        const double toAlong = (to[0] - corners3[0][0]) * across[0]
                            + (to[1] - corners3[0][1]) * across[1];

                        if (std::fabs(fromAlong - along) < nearest)
                        {
                            nearest = std::fabs(fromAlong - along);
                            nearestTop = from[2];
                        }

                        if (std::min(fromAlong, toAlong) <= along && along <= std::max(fromAlong, toAlong))
                        {
                            // An upright edge is as high as its higher end; another, where it passes.
                            top = std::max(top, std::fabs(toAlong - fromAlong) < 1.0e-9 ? std::max(from[2], to[2])
                                : from[2] + (to[2] - from[2]) * (along - fromAlong) / (toAlong - fromAlong));
                        }
                    }

                    // Off the face's span (a pixel's middle a little past its end): the nearest corner's height.
                    return top > -1.0e8 ? top : nearestTop;
                };

                for (size_t corner = 0; corner < polygon.size(); ++corner)
                {
                    const std::array<double, 2> &from = polygon[corner];
                    const std::array<double, 2> &to = polygon[(corner + 1) % polygon.size()];
                    const int steps = std::max(1, static_cast<int>(std::ceil(oy::hypot(to[0] - from[0],
                        to[1] - from[1]) * 4.0)));

                    for (int step = 0; step <= steps; ++step)
                    {
                        const int column = static_cast<int>(std::floor(from[0] + (to[0] - from[0]) * step / steps));
                        const int row = static_cast<int>(std::floor(from[1] + (to[1] - from[1]) * step / steps));

                        if (column < 0 || row < 0 || column >= FootprintSide || row >= FootprintSide)
                        {
                            continue;
                        }

                        const size_t pixel = static_cast<size_t>(row) * FootprintSide + column;

                        if (reading.footprints[pixel] == 0)
                        {
                            reading.footprints[pixel] = value;
                        }

                        if (reading.footprints[pixel] == value)
                        {
                            const double x = (from[0] + (to[0] - from[0]) * step / steps) * FootprintUnit - HalfMap;
                            const double y = HalfMap - (from[1] + (to[1] - from[1]) * step / steps) * FootprintUnit;
                            reading.tops[pixel] = std::max(reading.tops[pixel], static_cast<float>(topAt(x, y)));
                        }
                    }
                }
            }

            if (face.cogTriggeredNumber != 0 && !polygon.empty() && clickable(face.cogTriggeredNumber))
            {
                EventOnModel &onModel = eventSums[face.cogTriggeredNumber][index];
                onModel.sums[0] += sumX / polygon.size();
                onModel.sums[1] += sumY / polygon.size();
                onModel.sums[2] += sumZ / polygon.size();
                onModel.sums[3] += 1.0;
                onModel.bounds = modelBounds;
            }
        }

        reading.buildings.push_back(building);
    }

    for (int row = 0; row < FootprintSide; ++row)
    {
        for (int column = 0; column < FootprintSide; ++column)
        {
            const uint16_t value = reading.footprints[static_cast<size_t>(row) * FootprintSide + column];

            if (value != 0)
            {
                Building &building = reading.buildings[value - 1];
                ++building.pixels;
                building.pixelSumX += column + 0.5;
                building.pixelSumY += row + 0.5;
            }
        }
    }

    for (size_t index = 0; index < reading.buildings.size(); ++index)
    {
        Building &building = reading.buildings[index];

        if (building.pixels != 0)
        {
            building.centerX = building.pixelSumX / building.pixels * FootprintUnit - HalfMap;
            building.centerY = HalfMap - building.pixelSumY / building.pixels * FootprintUnit;
        }
    }

    const auto whatOf = [&side](int event)
    {
        const std::map<int, std::string>::const_iterator found = side.eventTargets.find(event);
        return found == side.eventTargets.end() ? std::string("event") : found->second;
    };

    // An event on several models is one thing where the models touch (their bounds within a cell of each other:
    // a ship cut into five models), and a thing of its own at each model or group that stands apart (the name
    // fifteen houses share, the title on two signposts).
    for (const std::pair<const int, std::map<size_t, EventOnModel>> &entry : eventSums)
    {
        std::vector<EventOnModel> groups;

        for (const std::pair<const size_t, EventOnModel> &model : entry.second)
        {
            groups.push_back(model.second);
        }

        for (bool merged = true; merged;)
        {
            merged = false;

            for (size_t first = 0; first < groups.size() && !merged; ++first)
            {
                for (size_t second = first + 1; second < groups.size() && !merged; ++second)
                {
                    const std::array<double, 4> &a = groups[first].bounds;
                    const std::array<double, 4> &b = groups[second].bounds;

                    if (a[0] - CellSize <= b[2] && b[0] - CellSize <= a[2] && a[1] - CellSize <= b[3]
                        && b[1] - CellSize <= a[3])
                    {
                        for (size_t axis = 0; axis < 4; ++axis)
                        {
                            groups[first].sums[axis] += groups[second].sums[axis];
                        }

                        groups[first].bounds = {std::min(a[0], b[0]), std::min(a[1], b[1]), std::max(a[2], b[2]),
                            std::max(a[3], b[3])};
                        groups.erase(groups.begin() + static_cast<std::ptrdiff_t>(second));
                        merged = true;
                    }
                }
            }
        }

        for (const EventOnModel &group : groups)
        {
            reading.events.push_back({whatOf(entry.first), group.sums[0] / group.sums[3],
                group.sums[1] / group.sums[3], group.sums[2] / group.sums[3]});
        }
    }

    for (const Game::OutdoorEntity &entity : map.entities)
    {
        std::string kind = lowered(entity.name);

        if (entity.decorationListId == PartyStartDecoration)
        {
            kind = "party start";
        }
        else if (kind.empty())
        {
            kind = "decoration " + std::to_string(entity.decorationListId);
        }

        // A party start (Ravenshore keeps 15, nameless) or a row of nothing is a marker, not a decoration one sees.
        if (entity.decorationListId != PartyStartDecoration && entity.decorationListId != 0)
        {
            reading.decorations.push_back({kind, static_cast<double>(entity.x), static_cast<double>(entity.y),
                static_cast<double>(entity.z)});
        }

        if (entity.scriptEventId() != 0 && clickable(entity.scriptEventId()))
        {
            reading.events.push_back({whatOf(entity.scriptEventId()), static_cast<double>(entity.x),
                static_cast<double>(entity.y), static_cast<double>(entity.z)});
        }
    }

    for (const Game::OutdoorSpawn &spawn : map.spawns)
    {
        reading.spawns.push_back({"spawn " + std::to_string(spawn.typeId) + "/" + std::to_string(spawn.index),
            static_cast<double>(spawn.x), static_cast<double>(spawn.y), static_cast<double>(spawn.z)});
    }

    return true;
}

// What a region counted; everything adds up over regions to the map's totals.
struct Tally
{
    double heightScore = 0.0;
    double heightDelta = 0.0;
    double heightAbs = 0.0;
    size_t nodes = 0;
    double reliefScore = 0.0;
    double originalRelief = 0.0;
    double rebuiltRelief = 0.0;
    size_t reliefCells = 0;
    size_t originalSteep = 0;
    size_t rebuiltSteep = 0;
    size_t originalSteepFound = 0;
    size_t rebuiltSteepFound = 0;
    size_t steepOnlyOriginal = 0;
    size_t steepOnlyRebuilt = 0;
    size_t walkOnlyOriginal = 0;
    size_t walkOnlyRebuilt = 0;
    size_t originalWater = 0;
    size_t rebuiltWater = 0;
    size_t sharedWater = 0;
    // By ground kind: quarters in the original, the rebuild and both.
    std::vector<std::array<size_t, 3>> ground;
    size_t originalRoads = 0;
    size_t rebuiltRoads = 0;
    size_t originalRoadsFound = 0;
    size_t rebuiltRoadsFound = 0;
    size_t sharedRoads = 0;
    size_t sameRoadTiles = 0;
    size_t originalPixels = 0;
    size_t rebuiltPixels = 0;
    size_t sharedPixels = 0;
    size_t originalBuildings = 0;
    size_t rebuiltBuildings = 0;
    size_t matchedBuildings = 0;
    double buildingHeightScore = 0.0;
    // Models with area of their own, and those at least half under buildings of the other map.
    size_t originalWithArea = 0;
    size_t rebuiltWithArea = 0;
    size_t originalFound = 0;
    size_t rebuiltFound = 0;
    // Over the pixels under buildings in both maps: how alike the tops are, summed.
    double formValue = 0.0;
    std::map<std::string, std::array<size_t, 2>> decorationKinds;
    size_t originalDecorations = 0;
    size_t rebuiltDecorations = 0;
    size_t originalSpawns = 0;
    size_t rebuiltSpawns = 0;
    double spawnValue = 0.0;
    size_t originalEvents = 0;
    size_t rebuiltEvents = 0;
    double eventValue = 0.0;
    std::vector<std::string> missing;
    // The rim: the sight lines whose horizon in the original lies here, their group's score times their number,
    // and the sums of their horizons' angles in each map.
    size_t skylineRays = 0;
    double skylineValue = 0.0;
    double originalSkyline = 0.0;
    double rebuiltSkyline = 0.0;
    double originalJag = 0.0;
    double rebuiltJag = 0.0;
    size_t jagSteps = 0;

    // The decorations of one region: the smaller and the larger count by kind, and of the totals.
    double decorationKindLow = 0.0;
    double decorationKindHigh = 0.0;
    double decorationLow = 0.0;
    double decorationHigh = 0.0;
};

// The land's height at a place in cells, between the nodes weighed by distance.
double landAt(const Reading &reading, double x, double y)
{
    const double clampedX = std::clamp(x, 0.0, Cells - 1.0);
    const double clampedY = std::clamp(y, 0.0, Cells - 1.0);
    const int x0 = std::min(Cells - 2, static_cast<int>(clampedX));
    const int y0 = std::min(Cells - 2, static_cast<int>(clampedY));
    const double shareX = clampedX - x0;
    const double shareY = clampedY - y0;
    const double north = reading.heights[y0 * Cells + x0] * (1.0 - shareX)
        + reading.heights[y0 * Cells + x0 + 1] * shareX;
    const double south = reading.heights[(y0 + 1) * Cells + x0] * (1.0 - shareX)
        + reading.heights[(y0 + 1) * Cells + x0 + 1] * shareX;
    return north * (1.0 - shareY) + south * shareY;
}

double harmonicMean(size_t firstFound, size_t firstAll, size_t secondFound, size_t secondAll)
{
    if (firstAll == 0 && secondAll == 0)
    {
        return 1.0;
    }

    if (firstAll == 0 || secondAll == 0)
    {
        return 0.0;
    }

    const double first = static_cast<double>(firstFound) / firstAll;
    const double second = static_cast<double>(secondFound) / secondAll;
    return first + second <= 0.0 ? 0.0 : 2.0 * first * second / (first + second);
}

double overlapShare(size_t shared, size_t first, size_t second)
{
    const size_t either = first + second - shared;
    return either == 0 ? 1.0 : static_cast<double>(shared) / either;
}

// A tally's parts: the score of each, or -1 where neither map has anything of it.
std::array<double, PartCount> partScores(const Tally &tally, uint8_t waterKind)
{
    std::array<double, PartCount> scores;
    scores.fill(-1.0);

    if (tally.nodes != 0)
    {
        scores[PartHeights] = tally.heightScore / tally.nodes;
    }

    if (tally.reliefCells != 0)
    {
        scores[PartRelief] = tally.reliefScore / tally.reliefCells;
    }

    if (tally.originalSteep + tally.rebuiltSteep != 0)
    {
        scores[PartCliffs] = harmonicMean(tally.originalSteepFound, tally.originalSteep, tally.rebuiltSteepFound,
            tally.rebuiltSteep);
    }

    if (tally.originalWater + tally.rebuiltWater != 0)
    {
        scores[PartWater] = overlapShare(tally.sharedWater, tally.originalWater, tally.rebuiltWater);
    }

    size_t landOriginal = 0;
    size_t landRebuilt = 0;
    size_t landShared = 0;

    for (size_t kind = 0; kind < tally.ground.size(); ++kind)
    {
        if (kind != waterKind)
        {
            landOriginal += tally.ground[kind][0];
            landRebuilt += tally.ground[kind][1];
            landShared += tally.ground[kind][2];
        }
    }

    if (landOriginal + landRebuilt != 0)
    {
        scores[PartGround] = overlapShare(landShared, landOriginal, landRebuilt);
    }

    if (tally.originalRoads + tally.rebuiltRoads != 0)
    {
        scores[PartRoads] = 0.7 * harmonicMean(tally.originalRoadsFound, tally.originalRoads,
            tally.rebuiltRoadsFound, tally.rebuiltRoads)
            + 0.3 * overlapShare(tally.sharedRoads, tally.originalRoads, tally.rebuiltRoads);
    }

    if (tally.originalBuildings + tally.rebuiltBuildings != 0 || tally.originalPixels + tally.rebuiltPixels != 0)
    {
        const double area = overlapShare(tally.sharedPixels, tally.originalPixels, tally.rebuiltPixels);
        const size_t either = tally.originalPixels + tally.rebuiltPixels - tally.sharedPixels;
        const double form = either == 0 ? 1.0 : tally.formValue / static_cast<double>(either);
        // A region a building only reaches into (its middle lies in another) has area and form to compare and
        // no model to count.
        scores[PartBuildings] = tally.originalWithArea + tally.rebuiltWithArea == 0
            ? (0.3 * area + 0.4 * form) / 0.7
            : 0.3 * area + 0.3 * harmonicMean(tally.originalFound, tally.originalWithArea, tally.rebuiltFound,
                tally.rebuiltWithArea) + 0.4 * form;
    }

    if (tally.originalDecorations + tally.rebuiltDecorations != 0)
    {
        scores[PartDecorations] = 0.5 * (tally.decorationKindHigh > 0.0
            ? tally.decorationKindLow / tally.decorationKindHigh : 1.0)
            + 0.5 * (tally.decorationHigh > 0.0 ? tally.decorationLow / tally.decorationHigh : 1.0);
    }

    if (tally.originalSpawns + tally.rebuiltSpawns != 0)
    {
        scores[PartSpawns] = tally.spawnValue / std::max(tally.originalSpawns, tally.rebuiltSpawns);
    }

    if (tally.originalEvents + tally.rebuiltEvents != 0)
    {
        scores[PartEvents] = tally.eventValue / std::max(tally.originalEvents, tally.rebuiltEvents);
    }

    if (tally.skylineRays != 0)
    {
        scores[PartRim] = tally.skylineValue / tally.skylineRays;
    }

    return scores;
}

double weightedScore(const std::array<double, PartCount> &scores, const std::array<double, PartCount> &weights,
    bool absentCountsAsSame)
{
    double sum = 0.0;
    double weight = 0.0;

    for (size_t part = 0; part < PartCount; ++part)
    {
        if (scores[part] >= 0.0)
        {
            sum += scores[part] * weights[part];
            weight += weights[part];
        }
        else if (absentCountsAsSame)
        {
            sum += weights[part];
            weight += weights[part];
        }
    }

    return weight > 0.0 ? sum / weight : 1.0;
}

void addTally(Tally &total, const Tally &part)
{
    total.heightScore += part.heightScore;
    total.heightDelta += part.heightDelta;
    total.heightAbs += part.heightAbs;
    total.nodes += part.nodes;
    total.reliefScore += part.reliefScore;
    total.originalRelief += part.originalRelief;
    total.rebuiltRelief += part.rebuiltRelief;
    total.reliefCells += part.reliefCells;
    total.originalSteep += part.originalSteep;
    total.rebuiltSteep += part.rebuiltSteep;
    total.originalSteepFound += part.originalSteepFound;
    total.rebuiltSteepFound += part.rebuiltSteepFound;
    total.steepOnlyOriginal += part.steepOnlyOriginal;
    total.steepOnlyRebuilt += part.steepOnlyRebuilt;
    total.walkOnlyOriginal += part.walkOnlyOriginal;
    total.walkOnlyRebuilt += part.walkOnlyRebuilt;
    total.originalWater += part.originalWater;
    total.rebuiltWater += part.rebuiltWater;
    total.sharedWater += part.sharedWater;
    total.ground.resize(std::max(total.ground.size(), part.ground.size()), {0, 0, 0});

    for (size_t kind = 0; kind < part.ground.size(); ++kind)
    {
        for (size_t column = 0; column < 3; ++column)
        {
            total.ground[kind][column] += part.ground[kind][column];
        }
    }

    total.originalRoads += part.originalRoads;
    total.rebuiltRoads += part.rebuiltRoads;
    total.originalRoadsFound += part.originalRoadsFound;
    total.rebuiltRoadsFound += part.rebuiltRoadsFound;
    total.sharedRoads += part.sharedRoads;
    total.sameRoadTiles += part.sameRoadTiles;
    total.originalPixels += part.originalPixels;
    total.rebuiltPixels += part.rebuiltPixels;
    total.sharedPixels += part.sharedPixels;
    total.originalBuildings += part.originalBuildings;
    total.rebuiltBuildings += part.rebuiltBuildings;
    total.matchedBuildings += part.matchedBuildings;
    total.buildingHeightScore += part.buildingHeightScore;
    total.originalWithArea += part.originalWithArea;
    total.rebuiltWithArea += part.rebuiltWithArea;
    total.originalFound += part.originalFound;
    total.rebuiltFound += part.rebuiltFound;
    total.formValue += part.formValue;

    for (const std::pair<const std::string, std::array<size_t, 2>> &kind : part.decorationKinds)
    {
        total.decorationKinds[kind.first][0] += kind.second[0];
        total.decorationKinds[kind.first][1] += kind.second[1];
    }

    total.originalDecorations += part.originalDecorations;
    total.rebuiltDecorations += part.rebuiltDecorations;
    total.decorationKindLow += part.decorationKindLow;
    total.decorationKindHigh += part.decorationKindHigh;
    total.decorationLow += part.decorationLow;
    total.decorationHigh += part.decorationHigh;
    total.originalSpawns += part.originalSpawns;
    total.rebuiltSpawns += part.rebuiltSpawns;
    total.spawnValue += part.spawnValue;
    total.originalEvents += part.originalEvents;
    total.rebuiltEvents += part.rebuiltEvents;
    total.eventValue += part.eventValue;
    total.skylineRays += part.skylineRays;
    total.skylineValue += part.skylineValue;
    total.originalSkyline += part.originalSkyline;
    total.rebuiltSkyline += part.rebuiltSkyline;
    total.originalJag += part.originalJag;
    total.rebuiltJag += part.rebuiltJag;
    total.jagSteps += part.jagSteps;
}

// Whether any of the cell and its eight neighbours is set.
bool setNear(const std::vector<uint8_t> &cells, int x, int y)
{
    for (int dy = -1; dy <= 1; ++dy)
    {
        for (int dx = -1; dx <= 1; ++dx)
        {
            const int otherX = x + dx;
            const int otherY = y + dy;

            if (otherX >= 0 && otherX < Cells && otherY >= 0 && otherY < Cells
                && cells[static_cast<size_t>(otherY) * Cells + otherX] != 0)
            {
                return true;
            }
        }
    }

    return false;
}

// Pairs the places of two maps nearest first within PairReach: a pair needs the same name when `sameName`, and is
// worth 1 with the same name and 0.5 without. What stays alone is listed.
void pairPlaces(
    const std::vector<Place> &original,
    const std::vector<Place> &rebuilt,
    bool sameName,
    std::vector<Tally> &tallies,
    size_t Tally::*pOriginalCount,
    size_t Tally::*pRebuiltCount,
    double Tally::*pValue,
    std::vector<OutdoorComparePlace> &missing,
    std::vector<OutdoorComparePlace> &extra)
{
    struct Pair
    {
        double distance = 0.0;
        size_t original = 0;
        size_t rebuilt = 0;
    };

    std::vector<Pair> pairs;

    for (size_t first = 0; first < original.size(); ++first)
    {
        for (size_t second = 0; second < rebuilt.size(); ++second)
        {
            const double distance = oy::hypot(original[first].x - rebuilt[second].x,
                original[first].y - rebuilt[second].y);

            if (distance <= PairReach && (!sameName || original[first].what == rebuilt[second].what))
            {
                pairs.push_back({distance, first, second});
            }
        }
    }

    // Pairs of the same name before pairs of different names at the same distance; then by index, so the result
    // does not depend on the sort.
    std::sort(pairs.begin(), pairs.end(), [&original, &rebuilt](const Pair &left, const Pair &right)
    {
        const bool leftSame = original[left.original].what == rebuilt[left.rebuilt].what;
        const bool rightSame = original[right.original].what == rebuilt[right.rebuilt].what;

        if (left.distance != right.distance)
        {
            return left.distance < right.distance;
        }

        if (leftSame != rightSame)
        {
            return leftSame;
        }

        return left.original != right.original ? left.original < right.original : left.rebuilt < right.rebuilt;
    });
    std::vector<uint8_t> originalTaken(original.size(), 0);
    std::vector<uint8_t> rebuiltTaken(rebuilt.size(), 0);

    for (const Pair &pair : pairs)
    {
        if (originalTaken[pair.original] != 0 || rebuiltTaken[pair.rebuilt] != 0)
        {
            continue;
        }

        originalTaken[pair.original] = 1;
        rebuiltTaken[pair.rebuilt] = 1;
        const Place &place = original[pair.original];
        tallies[regionOfWorld(place.x, place.y)].*pValue += place.what == rebuilt[pair.rebuilt].what ? 1.0 : 0.5;
    }

    for (size_t index = 0; index < original.size(); ++index)
    {
        Tally &tally = tallies[regionOfWorld(original[index].x, original[index].y)];
        ++(tally.*pOriginalCount);

        if (originalTaken[index] == 0)
        {
            missing.push_back({original[index].what, original[index].x, original[index].y, original[index].z});
            tally.missing.push_back(original[index].what);
        }
    }

    for (size_t index = 0; index < rebuilt.size(); ++index)
    {
        ++(tallies[regionOfWorld(rebuilt[index].x, rebuilt[index].y)].*pRebuiltCount);

        if (rebuiltTaken[index] == 0)
        {
            extra.push_back({rebuilt[index].what, rebuilt[index].x, rebuilt[index].y, rebuilt[index].z});
        }
    }
}

std::vector<OutdoorComparePlace> placesOf(const std::vector<Place> &places)
{
    std::vector<OutdoorComparePlace> result;

    for (const Place &place : places)
    {
        result.push_back({place.what, place.x, place.y, place.z});
    }

    return result;
}

std::string cellsText(size_t quarters)
{
    return formatNumber(rounded(quarters / 4.0, 1));
}

// What differs in a region, each with the score it costs, largest first.
std::vector<std::string> regionDifferences(
    const Tally &tally,
    const std::array<double, PartCount> &scores,
    const std::array<double, PartCount> &weights,
    const std::vector<std::string> &kinds,
    uint8_t waterKind)
{
    std::vector<std::pair<double, std::string>> found;
    const auto add = [&found, &scores, &weights](PartIndex part, const std::string &text)
    {
        if (scores[part] >= 0.0 && scores[part] < 0.995 && weights[part] > 0.0)
        {
            found.push_back({(1.0 - scores[part]) * weights[part], text});
        }
    };

    if (tally.nodes != 0)
    {
        const double mean = tally.heightDelta / tally.nodes;
        const double meanAbs = tally.heightAbs / tally.nodes;
        add(PartHeights, "the land differs by " + wholeText(meanAbs) + " on average"
            + (std::fabs(mean) >= 32.0 ? " (the rebuild lies " + wholeText(std::fabs(mean))
                + (mean > 0.0 ? " higher)" : " lower)") : std::string()));
    }

    if (tally.reliefCells != 0)
    {
        const double first = tally.originalRelief / tally.reliefCells;
        const double second = tally.rebuiltRelief / tally.reliefCells;
        add(PartRelief, std::string(first > second ? "the original's ground is rougher" : first < second
            ? "the rebuild's ground is rougher" : "the ground is rough in other places") + ": a cell rises "
            + wholeText(first) + " in the original, " + wholeText(second) + " in the rebuild");
    }

    add(PartCliffs, std::to_string(tally.originalSteep) + " cells too steep to walk in the original, "
        + std::to_string(tally.rebuiltSteep) + " in the rebuild (" + std::to_string(tally.steepOnlyOriginal)
        + " only in the original, " + std::to_string(tally.steepOnlyRebuilt) + " only in the rebuild)");
    add(PartWater, cellsText(tally.originalWater) + " cells of water in the original, "
        + cellsText(tally.rebuiltWater) + " in the rebuild, " + cellsText(tally.sharedWater) + " in the same place");
    std::string ground;

    for (size_t kind = 0; kind < tally.ground.size(); ++kind)
    {
        if (kind != waterKind && tally.ground[kind][0] != tally.ground[kind][1])
        {
            ground += (ground.empty() ? "" : "; ") + kinds[kind] + " " + cellsText(tally.ground[kind][0])
                + " cells in the original, " + cellsText(tally.ground[kind][1]) + " in the rebuild";
        }
    }

    add(PartGround, ground.empty() ? "the same ground kinds lie in other places" : "ground: " + ground);
    add(PartRoads, std::to_string(tally.originalRoads) + " road cells in the original, "
        + std::to_string(tally.rebuiltRoads) + " in the rebuild, " + std::to_string(tally.sharedRoads)
        + " in the same place");
    const size_t eitherPixels = tally.originalPixels + tally.rebuiltPixels - tally.sharedPixels;
    add(PartBuildings, std::to_string(tally.originalBuildings) + " buildings in the original, "
        + std::to_string(tally.rebuiltBuildings) + " in the rebuild, " + std::to_string(tally.matchedBuildings)
        + " matched; their footprints share " + percentText(overlapShare(tally.sharedPixels, tally.originalPixels,
            tally.rebuiltPixels)) + " of their area and their forms are "
        + percentText(eitherPixels == 0 ? 1.0 : tally.formValue / eitherPixels) + " alike");
    std::string decorations;
    std::vector<std::pair<size_t, std::string>> gaps;

    for (const std::pair<const std::string, std::array<size_t, 2>> &kind : tally.decorationKinds)
    {
        if (kind.second[0] != kind.second[1])
        {
            gaps.push_back({std::max(kind.second[0], kind.second[1]) - std::min(kind.second[0], kind.second[1]),
                kind.first + " " + std::to_string(kind.second[0]) + "/" + std::to_string(kind.second[1])});
        }
    }

    std::sort(gaps.begin(), gaps.end(), [](const std::pair<size_t, std::string> &left,
        const std::pair<size_t, std::string> &right)
    {
        return left.first != right.first ? left.first > right.first : left.second < right.second;
    });

    for (size_t index = 0; index < gaps.size() && index < 4; ++index)
    {
        decorations += (index == 0 ? "" : ", ") + gaps[index].second;
    }

    add(PartDecorations, std::to_string(tally.originalDecorations) + " decorations in the original, "
        + std::to_string(tally.rebuiltDecorations) + " in the rebuild"
        + (decorations.empty() ? std::string() : " (original/rebuild: " + decorations + ")"));
    add(PartSpawns, std::to_string(tally.originalSpawns) + " spawn points in the original, "
        + std::to_string(tally.rebuiltSpawns) + " in the rebuild");
    std::string missing;

    for (size_t index = 0; index < tally.missing.size() && index < 5; ++index)
    {
        if (!tally.missing[index].starts_with("spawn"))
        {
            missing += (missing.empty() ? "" : ", ") + tally.missing[index];
        }
    }

    add(PartEvents, std::to_string(tally.originalEvents) + " events in the original, "
        + std::to_string(tally.rebuiltEvents) + " in the rebuild"
        + (missing.empty() ? std::string() : " (missing: " + missing + ")"));

    if (tally.skylineRays != 0)
    {
        const double first = tally.originalSkyline / tally.skylineRays;
        const double second = tally.rebuiltSkyline / tally.skylineRays;
        const double tenths = std::round((second - first) * 10.0) / 10.0;
        add(PartRim, "the skyline seen from the square's edge stands " + formatNumber(rounded(first, 1))
            + " degrees over the eye in the original and " + formatNumber(rounded(second, 1)) + " in the rebuild"
            + (tenths == 0.0 ? std::string() : std::string(" (") + (tenths > 0.0 ? "higher" : "lower") + ")")
            + (tally.jagSteps == 0 ? std::string() : ", rising and falling " + formatNumber(rounded(
                tally.originalJag / tally.jagSteps, 2)) + " and " + formatNumber(rounded(tally.rebuiltJag
                / tally.jagSteps, 2)) + " degrees from one sight line to the next")
            + ", over " + std::to_string(tally.skylineRays) + " sight lines");
    }
    std::stable_sort(found.begin(), found.end(), [](const std::pair<double, std::string> &left,
        const std::pair<double, std::string> &right)
    {
        return left.first > right.first;
    });
    std::vector<std::string> texts;

    for (const std::pair<double, std::string> &entry : found)
    {
        texts.push_back(entry.second);
    }

    return texts;
}

// The highest angle over the eye, degrees, of the land beyond the square along a sight line from a node of the
// square's edge, and where along it that horizon lies (cells).
double horizonAlong(const Reading &reading, double fromX, double fromY, double angle, double eye, double &atX,
    double &atY)
{
    const double stepX = oy::cos(angle);
    const double stepY = oy::sin(angle);
    double best = -90.0;
    atX = fromX;
    atY = fromY;

    for (double reach = SkylineSampleCells;; reach += SkylineSampleCells)
    {
        const double x = fromX + stepX * reach;
        const double y = fromY + stepY * reach;

        if (x < 0.0 || y < 0.0 || x > Cells - 1.0 || y > Cells - 1.0)
        {
            break;
        }

        if (x >= SquareFirst && x <= SquareLast && y >= SquareFirst && y <= SquareLast)
        {
            continue;
        }

        const double degrees = oy::atan2(landAt(reading, x, y) - eye, reach * CellSize) * 180.0 / std::numbers::pi;

        if (degrees > best)
        {
            best = degrees;
            atX = x;
            atY = y;
        }
    }

    return best;
}

// The rim part: sight lines from the square's edge, grouped by the region of the original's horizon (the method
// is told at the top of this file).
void tallySkyline(const Reading &first, const Reading &second, std::vector<Tally> &tallies)
{
    struct Group
    {
        std::vector<double> original;
        std::vector<double> rebuilt;
        double originalJag = 0.0;
        double rebuiltJag = 0.0;
        size_t steps = 0;
    };

    std::vector<Group> groups(RegionTotal);
    // Outward along each side: north, east, south, west, in degrees with x east and y south.
    const int normals[4] = {-90, 0, 90, 180};

    for (size_t side = 0; side < 4; ++side)
    {
        for (int along = SquareFirst + 1; along < SquareLast; along += SkylineEyeStep)
        {
            // On the square's edge, then SkylineEyeInset cells in from it: the party sees the rim from inside the
            // square, and the nearest land beyond the edge stands that far off.
            const int eyeX = side == 0 || side == 2 ? along
                : (side == 1 ? SquareLast - SkylineEyeInset : SquareFirst + SkylineEyeInset);
            const int eyeY = side == 1 || side == 3 ? along
                : (side == 0 ? SquareFirst + SkylineEyeInset : SquareLast - SkylineEyeInset);
            const double eye = first.heights[static_cast<size_t>(eyeY) * Cells + eyeX] + SkylineEye;
            bool hasPrevious = false;
            double previousFirst = 0.0;
            double previousSecond = 0.0;

            for (int offset = -SkylineFan; offset <= SkylineFan; offset += SkylineRayStep)
            {
                const double angle = (normals[side] + offset) * std::numbers::pi / 180.0;
                double atX = 0.0;
                double atY = 0.0;
                double unusedX = 0.0;
                double unusedY = 0.0;
                const double firstHorizon = horizonAlong(first, eyeX, eyeY, angle, eye, atX, atY);
                const double secondHorizon = horizonAlong(second, eyeX, eyeY, angle, eye, unusedX, unusedY);
                Group &group = groups[regionOfCell(static_cast<int>(atX), static_cast<int>(atY))];
                group.original.push_back(firstHorizon);
                group.rebuilt.push_back(secondHorizon);

                if (hasPrevious)
                {
                    group.originalJag += std::fabs(firstHorizon - previousFirst);
                    group.rebuiltJag += std::fabs(secondHorizon - previousSecond);
                    ++group.steps;
                }

                hasPrevious = true;
                previousFirst = firstHorizon;
                previousSecond = secondHorizon;
            }
        }
    }

    for (size_t region = 0; region < RegionTotal; ++region)
    {
        Group &group = groups[region];

        if (group.original.empty())
        {
            continue;
        }

        Tally &tally = tallies[region];
        double sumFirst = 0.0;
        double sumSecond = 0.0;

        for (size_t index = 0; index < group.original.size(); ++index)
        {
            sumFirst += group.original[index];
            sumSecond += group.rebuilt[index];
        }

        std::sort(group.original.begin(), group.original.end());
        std::sort(group.rebuilt.begin(), group.rebuilt.end());
        double rankDifference = 0.0;

        for (size_t index = 0; index < group.original.size(); ++index)
        {
            rankDifference += std::fabs(group.original[index] - group.rebuilt[index]);
        }

        rankDifference /= group.original.size();
        const double heights = std::max(0.0, 1.0 - rankDifference / SkylineReach);
        double jag = 1.0;

        if (group.steps != 0)
        {
            const double firstJag = group.originalJag / group.steps;
            const double secondJag = group.rebuiltJag / group.steps;
            jag = 1.0 - std::fabs(firstJag - secondJag) / std::max({firstJag, secondJag, SkylineJagFloor});
        }

        const double score = 0.75 * heights + 0.25 * jag;
        tally.skylineRays += group.original.size();
        tally.skylineValue += score * group.original.size();
        tally.originalSkyline += sumFirst;
        tally.rebuiltSkyline += sumSecond;
        tally.originalJag += group.originalJag;
        tally.rebuiltJag += group.rebuiltJag;
        tally.jagSteps += group.steps;
    }
}
}

bool compareOutdoorMaps(
    const OutdoorCompareSide &original,
    const OutdoorCompareSide &rebuilt,
    OutdoorCompareResult &result,
    std::string &errorMessage,
    const OutdoorCompareOptions &options)
{
    result = {};
    result.originalName = original.name;
    result.rebuiltName = rebuilt.name;
    result.rimBySkyline = options.rimBySkyline;
    std::array<double, PartCount> weights = NodeByNodeWeights;

    if (options.rimBySkyline)
    {
        for (size_t part = 0; part < PartCount; ++part)
        {
            weights[part] = PartDefinitions[part].weight;
        }
    }

    // Under the skyline judging the land is compared node by node only inside the square the party walks.
    const auto judgedNode = [&options](int x, int y)
    {
        return !options.rimBySkyline || nodeInSquare(x, y);
    };
    KindTable kinds;
    kinds.idOf("dirt");
    const uint8_t waterKind = kinds.idOf("water");
    Reading first;
    Reading second;

    if (!readSide(original, kinds, first, errorMessage) || !readSide(rebuilt, kinds, second, errorMessage))
    {
        return false;
    }

    const size_t kindCount = kinds.names().size();
    std::vector<Tally> tallies(RegionTotal);

    for (Tally &tally : tallies)
    {
        tally.ground.assign(kindCount, {0, 0, 0});
    }

    // Heights, node by node.
    double sumFirst = 0.0;
    double sumSecond = 0.0;
    double sumSquares = 0.0;
    std::array<size_t, 4> within = {};
    size_t judgedNodes = 0;

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            if (!judgedNode(x, y))
            {
                continue;
            }

            ++judgedNodes;
            const size_t node = static_cast<size_t>(y) * Cells + x;
            const double delta = second.heights[node] - first.heights[node];
            Tally &tally = tallies[regionOfCell(x, y)];
            tally.heightScore += std::max(0.0, 1.0 - std::fabs(delta) / HeightReach);
            tally.heightDelta += delta;
            tally.heightAbs += std::fabs(delta);
            ++tally.nodes;
            sumFirst += first.heights[node];
            sumSecond += second.heights[node];
            sumSquares += delta * delta;
            const double limits[4] = {64.0, 128.0, 256.0, 512.0};

            for (size_t limit = 0; limit < 4; ++limit)
            {
                within[limit] += std::fabs(delta) <= limits[limit] ? 1 : 0;
            }
        }
    }

    const double meanFirst = sumFirst / judgedNodes;
    const double meanSecond = sumSecond / judgedNodes;
    double covariance = 0.0;
    double varianceFirst = 0.0;
    double varianceSecond = 0.0;

    for (size_t node = 0; node < CellTotal; ++node)
    {
        if (!judgedNode(static_cast<int>(node % Cells), static_cast<int>(node / Cells)))
        {
            continue;
        }

        covariance += (first.heights[node] - meanFirst) * (second.heights[node] - meanSecond);
        varianceFirst += (first.heights[node] - meanFirst) * (first.heights[node] - meanFirst);
        varianceSecond += (second.heights[node] - meanSecond) * (second.heights[node] - meanSecond);
    }

    // Two level maps are as alike as can be; a level map against a hilly one shares nothing of its shape.
    result.heightCorrelation = varianceFirst > 0.0 && varianceSecond > 0.0
        ? covariance / std::sqrt(varianceFirst * varianceSecond) : (varianceFirst == varianceSecond ? 1.0 : 0.0);
    result.rmsHeightDelta = std::sqrt(sumSquares / judgedNodes);

    for (size_t limit = 0; limit < 4; ++limit)
    {
        result.heightWithin[limit] = static_cast<double>(within[limit]) / judgedNodes;
    }

    // Relief, steep cells, water, ground and roads, cell by cell.
    std::vector<uint8_t> firstSteep(CellTotal, 0);
    std::vector<uint8_t> secondSteep(CellTotal, 0);

    for (size_t cell = 0; cell < CellTotal; ++cell)
    {
        firstSteep[cell] = first.relief[cell] > SteepRelief ? 1 : 0;
        secondSteep[cell] = second.relief[cell] > SteepRelief ? 1 : 0;
    }

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            const size_t cell = static_cast<size_t>(y) * Cells + x;
            Tally &tally = tallies[regionOfCell(x, y)];
            size_t firstWater = 0;
            size_t secondWater = 0;

            for (size_t corner = 0; corner < 4; ++corner)
            {
                const uint8_t firstKind = first.ground[cell][corner];
                const uint8_t secondKind = second.ground[cell][corner];
                ++tally.ground[firstKind][0];
                ++tally.ground[secondKind][1];
                tally.ground[firstKind][2] += firstKind == secondKind ? 1 : 0;
                firstWater += firstKind == waterKind ? 1 : 0;
                secondWater += secondKind == waterKind ? 1 : 0;
                tally.sharedWater += firstKind == waterKind && secondKind == waterKind ? 1 : 0;
            }

            tally.originalWater += firstWater;
            tally.rebuiltWater += secondWater;

            if (first.roads[cell] != 0)
            {
                ++tally.originalRoads;
                tally.originalRoadsFound += setNear(second.roads, x, y) ? 1 : 0;
            }

            if (second.roads[cell] != 0)
            {
                ++tally.rebuiltRoads;
                tally.rebuiltRoadsFound += setNear(first.roads, x, y) ? 1 : 0;
            }

            if (first.roads[cell] != 0 && second.roads[cell] != 0)
            {
                ++tally.sharedRoads;
                tally.sameRoadTiles += first.roads[cell] == second.roads[cell] ? 1 : 0;
            }

            if (x + 1 >= Cells || y + 1 >= Cells || (options.rimBySkyline && !cellInSquare(x, y)))
            {
                continue;
            }

            const double larger = std::max({first.relief[cell], second.relief[cell], ReliefFloor});
            tally.reliefScore += 1.0 - std::min(1.0, std::fabs(first.relief[cell] - second.relief[cell]) / larger);
            tally.originalRelief += first.relief[cell];
            tally.rebuiltRelief += second.relief[cell];
            ++tally.reliefCells;

            if (firstSteep[cell] != 0)
            {
                ++tally.originalSteep;
                tally.originalSteepFound += setNear(secondSteep, x, y) ? 1 : 0;
                tally.steepOnlyOriginal += secondSteep[cell] == 0 ? 1 : 0;
            }

            if (secondSteep[cell] != 0)
            {
                ++tally.rebuiltSteep;
                tally.rebuiltSteepFound += setNear(firstSteep, x, y) ? 1 : 0;
                tally.steepOnlyRebuilt += firstSteep[cell] == 0 ? 1 : 0;
            }

            // A walker stands on a cell that is neither too steep nor all water.
            const bool firstWalk = firstSteep[cell] == 0 && firstWater < 4;
            const bool secondWalk = secondSteep[cell] == 0 && secondWater < 4;
            tally.walkOnlyOriginal += firstWalk && !secondWalk ? 1 : 0;
            tally.walkOnlyRebuilt += secondWalk && !firstWalk ? 1 : 0;
        }
    }

    // Buildings: area by region, then each building with the one of the other map it shares most area with.
    std::map<std::pair<uint16_t, uint16_t>, size_t> sharedByPair;
    std::vector<size_t> coveredOfFirst(first.buildings.size(), 0);
    std::vector<size_t> coveredOfSecond(second.buildings.size(), 0);

    for (int row = 0; row < FootprintSide; ++row)
    {
        for (int column = 0; column < FootprintSide; ++column)
        {
            const size_t pixel = static_cast<size_t>(row) * FootprintSide + column;
            const uint16_t firstValue = first.footprints[pixel];
            const uint16_t secondValue = second.footprints[pixel];

            if (firstValue == 0 && secondValue == 0)
            {
                continue;
            }

            Tally &tally = tallies[regionOfCell(column * Cells / FootprintSide, row * Cells / FootprintSide)];
            tally.originalPixels += firstValue != 0 ? 1 : 0;
            tally.rebuiltPixels += secondValue != 0 ? 1 : 0;

            if (firstValue != 0 && secondValue != 0)
            {
                ++tally.sharedPixels;
                ++sharedByPair[{firstValue, secondValue}];
                ++coveredOfFirst[firstValue - 1];
                ++coveredOfSecond[secondValue - 1];
                // The tops over the land of each map: its own land, so a building that stands right on land
                // that lies wrong loses in the heights part, not here.
                const double cellX = (column + 0.5) * Cells / FootprintSide;
                const double cellY = (row + 0.5) * Cells / FootprintSide;
                const double firstTop = first.tops[pixel] - landAt(first, cellX, cellY);
                const double secondTop = second.tops[pixel] - landAt(second, cellX, cellY);
                tally.formValue += std::max(0.0, 1.0 - std::fabs(firstTop - secondTop) / FormReach);
            }
        }
    }

    std::vector<int> partnerOfFirst(first.buildings.size(), -1);
    std::vector<int> partnerOfSecond(second.buildings.size(), -1);
    const double pixelArea = (FootprintUnit / CellSize) * (FootprintUnit / CellSize);

    const auto addMatched = [&](const OutdoorCompareBuilding &building)
    {
        result.buildings.push_back(building);

        for (const int firstIndex : building.originalModels)
        {
            const Building &firstBuilding = first.buildings[static_cast<size_t>(firstIndex)];
            Tally &tally = tallies[regionOfWorld(firstBuilding.centerX, firstBuilding.centerY)];
            ++tally.matchedBuildings;
            const double taller = std::max({firstBuilding.height, building.heightDelta + firstBuilding.height, 1.0});
            tally.buildingHeightScore += 1.0 - std::min(1.0, std::fabs(building.heightDelta) / taller);
        }
    };

    // Models that share footprint are one building however each map cuts it into models: a model joins one of the
    // other map when at least half of the smaller one's area lies under it (Harmondale's fort ring, one model of
    // four pieces, against four walls; its castle of sixteen models against one plot; a ship of ten models). Each
    // group of joined models is a building found in both maps.
    const size_t firstCount = first.buildings.size();
    std::vector<size_t> parent(firstCount + second.buildings.size());
    std::iota(parent.begin(), parent.end(), 0);
    const auto rootOf = [&parent](size_t node)
    {
        while (parent[node] != node)
        {
            parent[node] = parent[parent[node]];
            node = parent[node];
        }

        return node;
    };

    for (const std::pair<const std::pair<uint16_t, uint16_t>, size_t> &entry : sharedByPair)
    {
        const size_t firstIndex = entry.first.first - 1u;
        const size_t secondIndex = entry.first.second - 1u;
        const size_t smaller = std::min(first.buildings[firstIndex].pixels, second.buildings[secondIndex].pixels);

        if (smaller != 0 && 2 * entry.second >= smaller)
        {
            const size_t firstRoot = rootOf(firstIndex);
            const size_t secondRoot = rootOf(firstCount + secondIndex);
            parent[std::max(firstRoot, secondRoot)] = std::min(firstRoot, secondRoot);
        }
    }

    struct Group
    {
        std::vector<size_t> originals;
        std::vector<size_t> rebuilts;
        size_t shared = 0;
    };

    std::map<size_t, Group> groups;

    for (size_t node = 0; node < parent.size(); ++node)
    {
        Group &group = groups[rootOf(node)];
        (node < firstCount ? group.originals : group.rebuilts).push_back(node < firstCount ? node : node - firstCount);
    }

    for (const std::pair<const std::pair<uint16_t, uint16_t>, size_t> &entry : sharedByPair)
    {
        const size_t root = rootOf(entry.first.first - 1u);

        if (root == rootOf(firstCount + entry.first.second - 1u))
        {
            groups[root].shared += entry.second;
        }
    }

    std::vector<const Group *> joined;

    for (const std::pair<const size_t, Group> &entry : groups)
    {
        if (!entry.second.originals.empty() && !entry.second.rebuilts.empty())
        {
            joined.push_back(&entry.second);
        }
    }

    std::sort(joined.begin(), joined.end(), [](const Group *pLeft, const Group *pRight)
    {
        return pLeft->shared != pRight->shared ? pLeft->shared > pRight->shared
            : pLeft->originals.front() < pRight->originals.front();
    });

    for (const Group *pGroup : joined)
    {
        // The group's extent in each map: its pixels, its middle, its lowest base and its highest top.
        const auto extentOf = [](const std::vector<Building> &buildings, const std::vector<size_t> &members,
            size_t &pixels, double &centerX, double &centerY, double &base, double &top, size_t &largest)
        {
            pixels = 0;
            centerX = 0.0;
            centerY = 0.0;
            base = 1.0e18;
            top = -1.0e18;
            largest = members.front();

            for (const size_t member : members)
            {
                const Building &building = buildings[member];
                pixels += building.pixels;
                centerX += building.centerX * building.pixels;
                centerY += building.centerY * building.pixels;
                base = std::min(base, building.base);
                top = std::max(top, building.base + building.height);
                largest = building.pixels > buildings[largest].pixels ? member : largest;
            }

            centerX = pixels != 0 ? centerX / pixels : buildings[largest].centerX;
            centerY = pixels != 0 ? centerY / pixels : buildings[largest].centerY;
        };
        size_t firstPixels = 0;
        size_t secondPixels = 0;
        size_t firstLargest = 0;
        size_t secondLargest = 0;
        double firstX = 0.0;
        double firstY = 0.0;
        double secondX = 0.0;
        double secondY = 0.0;
        double firstBase = 0.0;
        double firstTop = 0.0;
        double secondBase = 0.0;
        double secondTop = 0.0;
        extentOf(first.buildings, pGroup->originals, firstPixels, firstX, firstY, firstBase, firstTop, firstLargest);
        extentOf(second.buildings, pGroup->rebuilts, secondPixels, secondX, secondY, secondBase, secondTop,
            secondLargest);
        OutdoorCompareBuilding building;
        building.original = static_cast<int>(firstLargest);
        building.rebuilt = static_cast<int>(secondLargest);
        building.name = first.buildings[firstLargest].name;
        building.x = firstX;
        building.y = firstY;
        building.area = firstPixels * pixelArea;
        building.overlap = overlapShare(pGroup->shared, firstPixels, secondPixels);
        building.heightDelta = (secondTop - secondBase) - (firstTop - firstBase);
        building.baseDelta = secondBase - firstBase;

        for (const size_t member : pGroup->originals)
        {
            partnerOfFirst[member] = static_cast<int>(secondLargest);
            building.originalModels.push_back(static_cast<int>(member));
            building.originalNames.push_back(first.buildings[member].name);
        }

        for (const size_t member : pGroup->rebuilts)
        {
            partnerOfSecond[member] = static_cast<int>(firstLargest);
            building.rebuiltModels.push_back(static_cast<int>(member));
            building.rebuiltNames.push_back(second.buildings[member].name);
        }

        addMatched(building);
    }

    // Models that share less than that with any: paired one to one, the largest shares first.
    std::vector<std::pair<size_t, std::pair<uint16_t, uint16_t>>> looser;

    for (const std::pair<const std::pair<uint16_t, uint16_t>, size_t> &entry : sharedByPair)
    {
        looser.push_back({entry.second, entry.first});
    }

    std::sort(looser.begin(), looser.end(), [](const auto &left, const auto &right)
    {
        return left.first != right.first ? left.first > right.first : left.second < right.second;
    });

    for (const std::pair<size_t, std::pair<uint16_t, uint16_t>> &entry : looser)
    {
        const size_t firstIndex = entry.second.first - 1u;
        const size_t secondIndex = entry.second.second - 1u;

        if (partnerOfFirst[firstIndex] >= 0 || partnerOfSecond[secondIndex] >= 0)
        {
            continue;
        }

        partnerOfFirst[firstIndex] = static_cast<int>(secondIndex);
        partnerOfSecond[secondIndex] = static_cast<int>(firstIndex);
        const Building &firstBuilding = first.buildings[firstIndex];
        const Building &secondBuilding = second.buildings[secondIndex];
        OutdoorCompareBuilding building;
        building.original = static_cast<int>(firstIndex);
        building.rebuilt = static_cast<int>(secondIndex);
        building.name = firstBuilding.name;
        building.x = firstBuilding.centerX;
        building.y = firstBuilding.centerY;
        building.area = firstBuilding.pixels * pixelArea;
        building.overlap = overlapShare(entry.first, firstBuilding.pixels, secondBuilding.pixels);
        building.heightDelta = secondBuilding.height - firstBuilding.height;
        building.baseDelta = secondBuilding.base - firstBuilding.base;
        building.originalModels = {building.original};
        building.rebuiltModels = {building.rebuilt};
        building.originalNames = {firstBuilding.name};
        building.rebuiltNames = {secondBuilding.name};
        addMatched(building);
    }

    // A model with no area of its own on the grid (a post, a model wholly under another): with the nearest such
    // model of the other map, no further than two cells.
    struct NearPair
    {
        double distance = 0.0;
        size_t original = 0;
        size_t rebuilt = 0;
    };

    std::vector<NearPair> nearPairs;

    for (size_t firstIndex = 0; firstIndex < first.buildings.size(); ++firstIndex)
    {
        for (size_t secondIndex = 0; secondIndex < second.buildings.size(); ++secondIndex)
        {
            const double distance = oy::hypot(first.buildings[firstIndex].centerX
                - second.buildings[secondIndex].centerX, first.buildings[firstIndex].centerY
                - second.buildings[secondIndex].centerY);

            if (partnerOfFirst[firstIndex] < 0 && partnerOfSecond[secondIndex] < 0
                && first.buildings[firstIndex].pixels == 0 && second.buildings[secondIndex].pixels == 0
                && distance <= 2.0 * CellSize)
            {
                nearPairs.push_back({distance, firstIndex, secondIndex});
            }
        }
    }

    std::sort(nearPairs.begin(), nearPairs.end(), [](const NearPair &left, const NearPair &right)
    {
        if (left.distance != right.distance)
        {
            return left.distance < right.distance;
        }

        return left.original != right.original ? left.original < right.original : left.rebuilt < right.rebuilt;
    });

    for (const NearPair &pair : nearPairs)
    {
        if (partnerOfFirst[pair.original] < 0 && partnerOfSecond[pair.rebuilt] < 0)
        {
            partnerOfFirst[pair.original] = static_cast<int>(pair.rebuilt);
            partnerOfSecond[pair.rebuilt] = static_cast<int>(pair.original);
            const Building &firstBuilding = first.buildings[pair.original];
            const Building &secondBuilding = second.buildings[pair.rebuilt];
            OutdoorCompareBuilding building;
            building.original = static_cast<int>(pair.original);
            building.rebuilt = static_cast<int>(pair.rebuilt);
            building.name = firstBuilding.name;
            building.x = firstBuilding.centerX;
            building.y = firstBuilding.centerY;
            building.heightDelta = secondBuilding.height - firstBuilding.height;
            building.baseDelta = secondBuilding.base - firstBuilding.base;
            building.originalModels = {building.original};
            building.rebuiltModels = {building.rebuilt};
            building.originalNames = {firstBuilding.name};
            building.rebuiltNames = {secondBuilding.name};
            addMatched(building);
        }
    }

    // The original's models that found their building in the rebuild.
    result.matchedBuildings = static_cast<size_t>(std::count_if(partnerOfFirst.begin(), partnerOfFirst.end(),
        [](int partner)
        {
            return partner >= 0;
        }));

    for (size_t index = 0; index < first.buildings.size(); ++index)
    {
        const Building &building = first.buildings[index];
        Tally &tally = tallies[regionOfWorld(building.centerX, building.centerY)];
        ++tally.originalBuildings;
        tally.originalWithArea += building.pixels != 0 ? 1 : 0;
        tally.originalFound += building.pixels != 0 && 2 * coveredOfFirst[index] >= building.pixels ? 1 : 0;

        if (partnerOfFirst[index] < 0)
        {
            OutdoorCompareBuilding alone;
            alone.original = static_cast<int>(index);
            alone.name = building.name;
            alone.x = building.centerX;
            alone.y = building.centerY;
            alone.area = building.pixels * pixelArea;
            result.buildings.push_back(alone);
        }
    }

    for (size_t index = 0; index < second.buildings.size(); ++index)
    {
        const Building &building = second.buildings[index];
        Tally &ownTally = tallies[regionOfWorld(building.centerX, building.centerY)];
        ++ownTally.rebuiltBuildings;
        ownTally.rebuiltWithArea += building.pixels != 0 ? 1 : 0;
        ownTally.rebuiltFound += building.pixels != 0 && 2 * coveredOfSecond[index] >= building.pixels ? 1 : 0;

        if (partnerOfSecond[index] < 0)
        {
            OutdoorCompareBuilding alone;
            alone.rebuilt = static_cast<int>(index);
            alone.name = building.name;
            alone.x = building.centerX;
            alone.y = building.centerY;
            alone.area = building.pixels * pixelArea;
            result.buildings.push_back(alone);
        }
    }

    // Decorations: counted by region and kind for the regions' texts, and paired nearest first within
    // DecorationReach for the score: once by kind, once whatever the kind. A pair counts half in the region of
    // each of its two, and a region's measure is its pairs over the mean of the two maps' counts there, so the
    // whole map's is pairs over the mean of the two counts, wherever the borders run.
    for (const Place &place : first.decorations)
    {
        Tally &tally = tallies[regionOfWorld(place.x, place.y)];
        ++tally.decorationKinds[place.what][0];
        ++tally.originalDecorations;
    }

    for (const Place &place : second.decorations)
    {
        Tally &tally = tallies[regionOfWorld(place.x, place.y)];
        ++tally.decorationKinds[place.what][1];
        ++tally.rebuiltDecorations;
    }

    const auto pairDecorations = [&](bool sameKind, double Tally::*pLow,
        std::vector<OutdoorComparePlace> *pUnpairedOriginal, std::vector<OutdoorComparePlace> *pUnpairedRebuilt)
    {
        struct Candidate
        {
            double distance = 0.0;
            size_t original = 0;
            size_t rebuilt = 0;
        };
        std::vector<Candidate> candidates;

        for (size_t original = 0; original < first.decorations.size(); ++original)
        {
            for (size_t other = 0; other < second.decorations.size(); ++other)
            {
                const Place &a = first.decorations[original];
                const Place &b = second.decorations[other];
                const double distance = oy::hypot(a.x - b.x, a.y - b.y);

                if (distance <= DecorationReach && (!sameKind || a.what == b.what))
                {
                    candidates.push_back({distance, original, other});
                }
            }
        }

        std::sort(candidates.begin(), candidates.end(), [](const Candidate &left, const Candidate &right)
        {
            return left.distance != right.distance ? left.distance < right.distance
                : (left.original != right.original ? left.original < right.original : left.rebuilt < right.rebuilt);
        });
        std::vector<uint8_t> originalTaken(first.decorations.size(), 0);
        std::vector<uint8_t> rebuiltTaken(second.decorations.size(), 0);

        for (const Candidate &candidate : candidates)
        {
            if (originalTaken[candidate.original] != 0 || rebuiltTaken[candidate.rebuilt] != 0)
            {
                continue;
            }

            originalTaken[candidate.original] = 1;
            rebuiltTaken[candidate.rebuilt] = 1;
            const Place &a = first.decorations[candidate.original];
            const Place &b = second.decorations[candidate.rebuilt];
            tallies[regionOfWorld(a.x, a.y)].*pLow += 0.5;
            tallies[regionOfWorld(b.x, b.y)].*pLow += 0.5;
        }

        for (size_t index = 0; pUnpairedOriginal != nullptr && index < first.decorations.size(); ++index)
        {
            const Place &place = first.decorations[index];

            if (originalTaken[index] == 0)
            {
                pUnpairedOriginal->push_back({place.what, place.x, place.y, place.z});
            }
        }

        for (size_t index = 0; pUnpairedRebuilt != nullptr && index < second.decorations.size(); ++index)
        {
            const Place &place = second.decorations[index];

            if (rebuiltTaken[index] == 0)
            {
                pUnpairedRebuilt->push_back({place.what, place.x, place.y, place.z});
            }
        }
    };
    pairDecorations(true, &Tally::decorationKindLow, &result.unpairedOriginalDecorations,
        &result.unpairedRebuiltDecorations);
    pairDecorations(false, &Tally::decorationLow, nullptr, nullptr);

    for (Tally &tally : tallies)
    {
        tally.decorationKindHigh = (tally.originalDecorations + tally.rebuiltDecorations) * 0.5;
        tally.decorationHigh = tally.decorationKindHigh;
    }

    pairPlaces(first.spawns, second.spawns, false, tallies, &Tally::originalSpawns, &Tally::rebuiltSpawns,
        &Tally::spawnValue, result.missingSpawns, result.extraSpawns);
    pairPlaces(first.events, second.events, true, tallies, &Tally::originalEvents, &Tally::rebuiltEvents,
        &Tally::eventValue, result.missingEvents, result.extraEvents);
    tallySkyline(first, second, tallies);

    // The regions and the whole map.
    Tally total;
    total.ground.assign(kindCount, {0, 0, 0});

    for (size_t index = 0; index < RegionTotal; ++index)
    {
        const Tally &tally = tallies[index];
        addTally(total, tally);
        OutdoorCompareRegion region;
        region.column = static_cast<int>(index % RegionsPerSide);
        region.row = static_cast<int>(index / RegionsPerSide);
        region.name = std::string(1, static_cast<char>('A' + region.column)) + std::to_string(region.row + 1);
        const std::array<double, PartCount> scores = partScores(tally, waterKind);
        region.partScores.assign(scores.begin(), scores.end());
        region.score = weightedScore(scores, weights, false);
        region.differences = regionDifferences(tally, scores, weights, kinds.names(), waterKind);
        region.meanHeightDelta = tally.nodes != 0 ? tally.heightDelta / tally.nodes : 0.0;
        region.meanAbsHeightDelta = tally.nodes != 0 ? tally.heightAbs / tally.nodes : 0.0;
        region.skylineRays = tally.skylineRays;
        region.originalSkyline = tally.skylineRays != 0 ? tally.originalSkyline / tally.skylineRays : 0.0;
        region.rebuiltSkyline = tally.skylineRays != 0 ? tally.rebuiltSkyline / tally.skylineRays : 0.0;

        for (size_t difference = 0; difference < region.differences.size() && difference < 3; ++difference)
        {
            region.sentence += (difference == 0 ? "" : "; ") + region.differences[difference];
        }

        result.regions.push_back(region);
    }

    result.worstRegions.resize(RegionTotal);
    std::iota(result.worstRegions.begin(), result.worstRegions.end(), 0);
    std::stable_sort(result.worstRegions.begin(), result.worstRegions.end(), [&result](size_t left, size_t right)
    {
        return result.regions[left].score < result.regions[right].score;
    });

    const std::array<double, PartCount> scores = partScores(total, waterKind);
    result.score = weightedScore(scores, weights, true);
    result.meanHeightDelta = total.heightDelta / judgedNodes;
    result.meanAbsHeightDelta = total.heightAbs / judgedNodes;
    result.skylineRays = total.skylineRays;
    result.originalSkyline = total.skylineRays != 0 ? total.originalSkyline / total.skylineRays : 0.0;
    result.rebuiltSkyline = total.skylineRays != 0 ? total.rebuiltSkyline / total.skylineRays : 0.0;
    result.originalRelief = total.reliefCells != 0 ? total.originalRelief / total.reliefCells : 0.0;
    result.rebuiltRelief = total.reliefCells != 0 ? total.rebuiltRelief / total.reliefCells : 0.0;
    result.originalSteepCells = total.originalSteep;
    result.rebuiltSteepCells = total.rebuiltSteep;
    result.walkableOnlyInOriginal = total.walkOnlyOriginal;
    result.walkableOnlyInRebuilt = total.walkOnlyRebuilt;
    result.originalWaterQuarters = total.originalWater;
    result.rebuiltWaterQuarters = total.rebuiltWater;
    result.sharedWaterQuarters = total.sharedWater;
    result.groundKinds = kinds.names();
    result.groundQuarters = total.ground;
    result.originalRoadCells = total.originalRoads;
    result.rebuiltRoadCells = total.rebuiltRoads;
    result.sharedRoadCells = total.sharedRoads;
    result.sameRoadTileCells = total.sameRoadTiles;
    result.originalBuildings = first.buildings.size();
    result.rebuiltBuildings = second.buildings.size();
    result.footprintOverlap = overlapShare(total.sharedPixels, total.originalPixels, total.rebuiltPixels);
    const size_t eitherPixels = total.originalPixels + total.rebuiltPixels - total.sharedPixels;
    result.buildingForm = eitherPixels == 0 ? 1.0 : total.formValue / eitherPixels;
    result.originalModelsWithArea = total.originalWithArea;
    result.rebuiltModelsWithArea = total.rebuiltWithArea;
    result.originalModelsFound = total.originalFound;
    result.rebuiltModelsFound = total.rebuiltFound;
    result.originalDecorations = first.decorations.size();
    result.rebuiltDecorations = second.decorations.size();

    for (const std::pair<const std::string, std::array<size_t, 2>> &kind : total.decorationKinds)
    {
        result.decorationKinds.push_back({kind.first, kind.second});
    }

    result.originalSpawns = first.spawns.size();
    result.rebuiltSpawns = second.spawns.size();
    result.originalEvents = first.events.size();
    result.rebuiltEvents = second.events.size();
    size_t landOriginal = 0;
    size_t landShared = 0;

    for (size_t kind = 0; kind < kindCount; ++kind)
    {
        if (kind != waterKind)
        {
            landOriginal += total.ground[kind][0];
            landShared += total.ground[kind][2];
        }
    }

    const std::string where = options.rimBySkyline ? " in the square the party walks" : "";
    const std::string details[PartCount] = {
        "the land differs by " + wholeText(result.meanAbsHeightDelta) + " units on average" + where
            + " (rebuild minus original " + wholeText(result.meanHeightDelta) + "), "
            + percentText(result.heightWithin[2]) + " of the nodes within 256 and "
            + percentText(result.heightWithin[3]) + " within 512; correlation "
            + formatNumber(rounded(result.heightCorrelation, 3)),
        "a cell rises " + wholeText(result.originalRelief) + " units in the original and "
            + wholeText(result.rebuiltRelief) + " in the rebuild, on average" + where,
        std::to_string(total.originalSteep) + " cells too steep to walk in the original, "
            + std::to_string(total.rebuiltSteep) + " in the rebuild; " + std::to_string(total.originalSteepFound)
            + " of the original's have one of the rebuild's on or beside them; "
            + std::to_string(total.walkOnlyOriginal) + " cells can be walked only in the original, "
            + std::to_string(total.walkOnlyRebuilt)
            + " only in the rebuild",
        cellsText(total.originalWater) + " cells of water in the original, " + cellsText(total.rebuiltWater)
            + " in the rebuild, " + cellsText(total.sharedWater) + " in the same place",
        cellsText(landShared) + " of the original's " + cellsText(landOriginal)
            + " cells of land have the same ground kind in the rebuild",
        std::to_string(total.originalRoads) + " road cells in the original, " + std::to_string(total.rebuiltRoads)
            + " in the rebuild, " + std::to_string(total.sharedRoads) + " in the same place ("
            + std::to_string(total.sameRoadTiles) + " with the same road tile), "
            + std::to_string(total.originalRoadsFound) + " of the original's with one of the rebuild's on or beside "
              "them",
        std::to_string(result.originalBuildings) + " building models in the original, "
            + std::to_string(result.rebuiltBuildings) + " in the rebuild, " + std::to_string(result.matchedBuildings)
            + " matched; their footprints share " + percentText(result.footprintOverlap) + " of their area, "
            + std::to_string(result.originalModelsFound) + " of the original's "
            + std::to_string(result.originalModelsWithArea) + " models with area of their own lie at least half "
              "under the rebuild's and " + std::to_string(result.rebuiltModelsFound) + " of the rebuild's "
            + std::to_string(result.rebuiltModelsWithArea) + " under the original's; over the area under buildings "
              "in either map their tops are " + percentText(result.buildingForm) + " alike",
        std::to_string(result.originalDecorations) + " decorations in the original, "
            + std::to_string(result.rebuiltDecorations) + " in the rebuild",
        std::to_string(result.originalSpawns) + " spawn points in the original, "
            + std::to_string(result.rebuiltSpawns) + " in the rebuild, "
            + std::to_string(result.originalSpawns - result.missingSpawns.size()) + " paired",
        std::to_string(result.originalEvents) + " events on faces and decorations in the original, "
            + std::to_string(result.rebuiltEvents) + " in the rebuild, "
            + std::to_string(result.originalEvents - result.missingEvents.size()) + " paired",
        "seen from the square's edge over " + std::to_string(result.skylineRays) + " sight lines, the land beyond "
            "it stands " + formatNumber(rounded(result.originalSkyline, 1)) + " degrees over the eye in the original "
            "and " + formatNumber(rounded(result.rebuiltSkyline, 1)) + " in the rebuild, on average; compared by "
            "the region the original's horizon lies in, rank by rank and by its ups and downs"
            + (options.rimBySkyline ? std::string() : " (not in the score: the rim is judged node by node)"),
    };

    for (size_t part = 0; part < PartCount; ++part)
    {
        OutdoorComparePart entry;
        entry.id = PartDefinitions[part].pId;
        entry.title = PartDefinitions[part].pTitle;
        entry.weight = weights[part];
        entry.score = scores[part] < 0.0 ? 1.0 : scores[part];
        entry.detail = details[part];
        result.parts.push_back(entry);
    }

    result.originalHeights = std::move(first.heights);
    result.rebuiltHeights = std::move(second.heights);
    result.originalGround = std::move(first.ground);
    result.rebuiltGround = std::move(second.ground);
    result.originalRoads = std::move(first.roads);
    result.rebuiltRoads = std::move(second.roads);
    result.originalFootprints = std::move(first.footprints);
    result.rebuiltFootprints = std::move(second.footprints);
    result.originalDecorationPlaces = placesOf(first.decorations);
    result.rebuiltDecorationPlaces = placesOf(second.decorations);
    result.originalSpawnPlaces = placesOf(first.spawns);
    result.rebuiltSpawnPlaces = placesOf(second.spawns);
    result.originalEventPlaces = placesOf(first.events);
    result.rebuiltEventPlaces = placesOf(second.events);
    result.waterKind = waterKind;
    return true;
}

namespace
{
void writePlace(const OutdoorComparePlace &place, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("what", place.what);
    writer.key("at");
    writer.beginArray();
    writer.value(rounded(place.x, 0));
    writer.value(rounded(place.y, 0));
    writer.value(rounded(place.z, 0));
    writer.endArray();
    writer.field("region", std::string(1, static_cast<char>('A' + regionOfWorld(place.x, place.y) % RegionsPerSide))
        + std::to_string(regionOfWorld(place.x, place.y) / RegionsPerSide + 1));
    writer.endObject();
}

void writePlaces(const char *pKey, const std::vector<OutdoorComparePlace> &places, JsonWriter &writer)
{
    writer.key(pKey);
    writer.beginArray();

    for (const OutdoorComparePlace &place : places)
    {
        writePlace(place, writer);
    }

    writer.endArray();
}

void writeRegion(const OutdoorCompareResult &result, const OutdoorCompareRegion &region, bool whole,
    JsonWriter &writer)
{
    writer.beginObject();
    writer.field("region", region.name);
    writer.key("cells");
    writer.beginArray();
    writer.value(region.column * RegionCells);
    writer.value(region.row * RegionCells);
    writer.value(RegionCells);
    writer.value(RegionCells);
    writer.endArray();
    writer.field("score", rounded(region.score, 3));
    writer.field("mean_height_difference", rounded(region.meanHeightDelta, 0));

    if (region.skylineRays != 0)
    {
        writer.key("skyline");
        writer.beginObject();
        writer.field("sight_lines", static_cast<uint64_t>(region.skylineRays));
        writer.field("original_mean_degrees", rounded(region.originalSkyline, 2));
        writer.field("rebuilt_mean_degrees", rounded(region.rebuiltSkyline, 2));
        writer.endObject();
    }

    writer.key("parts");
    writer.beginObject();

    for (size_t part = 0; part < region.partScores.size(); ++part)
    {
        if (region.partScores[part] >= 0.0)
        {
            writer.field(result.parts[part].id, rounded(region.partScores[part], 3));
        }
    }

    writer.endObject();

    if (whole)
    {
        writer.key("differences");
        writer.beginArray();

        for (const std::string &difference : region.differences)
        {
            writer.value(difference);
        }

        writer.endArray();
    }
    else
    {
        writer.field("what", region.sentence);
    }

    writer.endObject();
}
}

void writeOutdoorCompareJson(const OutdoorCompareResult &result, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("kind", "outdoor");
    writer.field("original", result.originalName);
    writer.field("rebuilt", result.rebuiltName);
    writer.field("score", rounded(result.score, 4));
    writer.key("parts");
    writer.beginArray();

    for (const OutdoorComparePart &part : result.parts)
    {
        writer.beginObject();
        writer.field("id", part.id);
        writer.field("title", part.title);
        writer.field("weight", part.weight);
        writer.field("score", rounded(part.score, 4));
        writer.field("what", part.detail);
        writer.endObject();
    }

    writer.endArray();
    writer.key("heights");
    writer.beginObject();
    writer.field("correlation", rounded(result.heightCorrelation, 4));
    writer.field("mean_difference", rounded(result.meanHeightDelta, 1));
    writer.field("mean_absolute_difference", rounded(result.meanAbsHeightDelta, 1));
    writer.field("rms_difference", rounded(result.rmsHeightDelta, 1));
    writer.field("within_64", rounded(result.heightWithin[0], 4));
    writer.field("within_128", rounded(result.heightWithin[1], 4));
    writer.field("within_256", rounded(result.heightWithin[2], 4));
    writer.field("within_512", rounded(result.heightWithin[3], 4));
    writer.field("original_mean_relief", rounded(result.originalRelief, 1));
    writer.field("rebuilt_mean_relief", rounded(result.rebuiltRelief, 1));
    writer.field("original_steep_cells", static_cast<uint64_t>(result.originalSteepCells));
    writer.field("rebuilt_steep_cells", static_cast<uint64_t>(result.rebuiltSteepCells));
    writer.field("walkable_only_in_original", static_cast<uint64_t>(result.walkableOnlyInOriginal));
    writer.field("walkable_only_in_rebuilt", static_cast<uint64_t>(result.walkableOnlyInRebuilt));
    writer.field("over", result.rimBySkyline ? "the square the party walks (nodes 19 to 109)" : "the whole map");
    writer.endObject();
    writer.key("rim");
    writer.beginObject();
    writer.field("judged_by", result.rimBySkyline ? "skyline" : "nodes");
    writer.field("sight_lines", static_cast<uint64_t>(result.skylineRays));
    writer.field("original_mean_degrees", rounded(result.originalSkyline, 2));
    writer.field("rebuilt_mean_degrees", rounded(result.rebuiltSkyline, 2));
    writer.endObject();
    writer.key("water_cells");
    writer.beginObject();
    writer.field("original", result.originalWaterQuarters / 4.0);
    writer.field("rebuilt", result.rebuiltWaterQuarters / 4.0);
    writer.field("same_place", result.sharedWaterQuarters / 4.0);
    writer.endObject();
    writer.key("ground_cells");
    writer.beginArray();

    for (size_t kind = 0; kind < result.groundKinds.size(); ++kind)
    {
        if (result.groundQuarters[kind][0] + result.groundQuarters[kind][1] == 0)
        {
            continue;
        }

        writer.beginObject();
        writer.field("kind", result.groundKinds[kind]);
        writer.field("original", result.groundQuarters[kind][0] / 4.0);
        writer.field("rebuilt", result.groundQuarters[kind][1] / 4.0);
        writer.field("same_place", result.groundQuarters[kind][2] / 4.0);
        writer.endObject();
    }

    writer.endArray();
    writer.key("road_cells");
    writer.beginObject();
    writer.field("original", static_cast<uint64_t>(result.originalRoadCells));
    writer.field("rebuilt", static_cast<uint64_t>(result.rebuiltRoadCells));
    writer.field("same_place", static_cast<uint64_t>(result.sharedRoadCells));
    writer.field("same_tile", static_cast<uint64_t>(result.sameRoadTileCells));
    writer.endObject();
    writer.key("buildings");
    writer.beginObject();
    writer.field("original", static_cast<uint64_t>(result.originalBuildings));
    writer.field("rebuilt", static_cast<uint64_t>(result.rebuiltBuildings));
    writer.field("matched", static_cast<uint64_t>(result.matchedBuildings));
    writer.field("footprint_overlap", rounded(result.footprintOverlap, 4));
    writer.field("form_alike", rounded(result.buildingForm, 4));
    writer.field("original_models_with_area", static_cast<uint64_t>(result.originalModelsWithArea));
    writer.field("original_models_found", static_cast<uint64_t>(result.originalModelsFound));
    writer.field("rebuilt_models_with_area", static_cast<uint64_t>(result.rebuiltModelsWithArea));
    writer.field("rebuilt_models_found", static_cast<uint64_t>(result.rebuiltModelsFound));
    writer.endObject();
    writer.key("decorations");
    writer.beginObject();
    writer.field("original", static_cast<uint64_t>(result.originalDecorations));
    writer.field("rebuilt", static_cast<uint64_t>(result.rebuiltDecorations));
    writer.field("kinds", static_cast<uint64_t>(result.decorationKinds.size()));
    writer.endObject();
    writer.key("spawns");
    writer.beginObject();
    writer.field("original", static_cast<uint64_t>(result.originalSpawns));
    writer.field("rebuilt", static_cast<uint64_t>(result.rebuiltSpawns));
    writer.field("missing", static_cast<uint64_t>(result.missingSpawns.size()));
    writer.field("extra", static_cast<uint64_t>(result.extraSpawns.size()));
    writer.endObject();
    writer.key("events");
    writer.beginObject();
    writer.field("original", static_cast<uint64_t>(result.originalEvents));
    writer.field("rebuilt", static_cast<uint64_t>(result.rebuiltEvents));
    writer.field("missing", static_cast<uint64_t>(result.missingEvents.size()));
    writer.field("extra", static_cast<uint64_t>(result.extraEvents.size()));
    writer.endObject();
    writer.key("worst_regions");
    writer.beginArray();

    for (size_t index = 0; index < result.worstRegions.size() && index < 12; ++index)
    {
        writeRegion(result, result.regions[result.worstRegions[index]], false, writer);
    }

    writer.endArray();
    writer.key("regions");
    writer.beginArray();

    // Row by row from the north, each row from the west: the map as a table of scores.
    for (int row = 0; row < RegionsPerSide; ++row)
    {
        writer.beginArray();

        for (int column = 0; column < RegionsPerSide; ++column)
        {
            writer.value(rounded(result.regions[static_cast<size_t>(row) * RegionsPerSide + column].score, 3));
        }

        writer.endArray();
    }

    writer.endArray();
    writer.endObject();
}

void writeOutdoorDifferencesJson(const OutdoorCompareResult &result, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("original", result.originalName);
    writer.field("rebuilt", result.rebuiltName);
    writer.key("regions");
    writer.beginArray();

    for (const size_t index : result.worstRegions)
    {
        writeRegion(result, result.regions[index], true, writer);
    }

    writer.endArray();
    writer.key("buildings");
    writer.beginArray();

    for (const OutdoorCompareBuilding &building : result.buildings)
    {
        writer.beginObject();
        writer.field("state", building.original >= 0 && building.rebuilt >= 0 ? "matched"
            : (building.original >= 0 ? "only in the original" : "only in the rebuild"));
        writer.field("name", building.name);

        if (building.original >= 0)
        {
            writer.field("original_index", building.original);
        }

        if (building.rebuilt >= 0)
        {
            writer.field("rebuilt_index", building.rebuilt);
        }

        writer.key("at");
        writer.beginArray();
        writer.value(rounded(building.x, 0));
        writer.value(rounded(building.y, 0));
        writer.endArray();
        writer.field("area_cells", rounded(building.area, 2));

        if (building.original >= 0 && building.rebuilt >= 0)
        {
            writer.field("footprint_overlap", rounded(building.overlap, 3));
            writer.field("height_difference", rounded(building.heightDelta, 0));
            writer.field("base_difference", rounded(building.baseDelta, 0));
        }

        // A building cut into several models in either map: all of them.
        if (building.originalNames.size() > 1 || building.rebuiltNames.size() > 1)
        {
            for (const bool original : {true, false})
            {
                writer.key(original ? "models_original" : "models_rebuilt");
                writer.beginArray();

                for (const std::string &name : original ? building.originalNames : building.rebuiltNames)
                {
                    writer.value(name);
                }

                writer.endArray();
            }
        }

        writer.endObject();
    }

    writer.endArray();
    writePlaces("spawns_only_in_original", result.missingSpawns, writer);
    writePlaces("spawns_only_in_rebuilt", result.extraSpawns, writer);
    writePlaces("events_only_in_original", result.missingEvents, writer);
    writePlaces("events_only_in_rebuilt", result.extraEvents, writer);
    // The decorations without a partner of their kind within reach (the part's half by kind).
    writePlaces("decorations_only_in_original", result.unpairedOriginalDecorations, writer);
    writePlaces("decorations_only_in_rebuilt", result.unpairedRebuiltDecorations, writer);
    writer.key("decoration_kinds");
    writer.beginArray();

    for (const std::pair<std::string, std::array<size_t, 2>> &kind : result.decorationKinds)
    {
        writer.beginObject();
        writer.field("kind", kind.first);
        writer.field("original", static_cast<uint64_t>(kind.second[0]));
        writer.field("rebuilt", static_cast<uint64_t>(kind.second[1]));
        writer.endObject();
    }

    writer.endArray();
    writer.endObject();
}

std::set<int> outdoorFlowEvents(const std::string &eventFlowJson)
{
    std::set<int> events;
    const std::string eventKey = "{\"event\":";

    for (size_t at = eventFlowJson.find(eventKey); at != std::string::npos;
         at = eventFlowJson.find(eventKey, at + eventKey.size()))
    {
        events.insert(std::atoi(eventFlowJson.c_str() + at + eventKey.size()));
    }

    return events;
}

std::set<int> outdoorEmptyEvents(const std::string &eventFlowJson)
{
    std::set<int> empty;
    const std::string eventKey = "{\"event\":";
    size_t at = eventFlowJson.find(eventKey);

    while (at != std::string::npos)
    {
        const size_t next = eventFlowJson.find(eventKey, at + eventKey.size());
        const std::string_view body = std::string_view(eventFlowJson).substr(at,
            next == std::string::npos ? std::string::npos : next - at);
        const int event = std::atoi(eventFlowJson.c_str() + at + eventKey.size());
        // No title, and every path does nothing.
        const bool untitled = body.find("\"title\":\"\"") != std::string_view::npos;
        bool effects = false;

        for (size_t found = body.find("\"effects\":["); found != std::string_view::npos;
             found = body.find("\"effects\":[", found + 1))
        {
            effects = effects || (found + 11 < body.size() && body[found + 11] != ']');
        }

        if (untitled && !effects)
        {
            empty.insert(event);
        }

        at = next;
    }

    return empty;
}

std::map<int, std::string> outdoorEventTargets(const std::string &eventFlowJson)
{
    std::map<int, std::string> targets;
    const std::string eventKey = "{\"event\":";
    size_t at = eventFlowJson.find(eventKey);

    while (at != std::string::npos)
    {
        const size_t next = eventFlowJson.find(eventKey, at + eventKey.size());
        const std::string_view body = std::string_view(eventFlowJson).substr(at,
            next == std::string::npos ? std::string::npos : next - at);
        const int event = std::atoi(eventFlowJson.c_str() + at + eventKey.size());
        const size_t house = body.find("EnterHouse(");
        const size_t leave = body.find("\"leave to ");

        if (house != std::string_view::npos)
        {
            targets[event] = "house " + std::to_string(std::atoi(std::string(body.substr(house + 11, 12)).c_str()));
        }
        else if (leave != std::string_view::npos)
        {
            const size_t begin = leave + 10;
            const size_t end = body.find(' ', begin);
            targets[event] = "map " + lowered(std::string(body.substr(begin, end == std::string_view::npos
                ? std::string_view::npos : end - begin)));
        }

        at = next;
    }

    return targets;
}
}
