#include "core/OutdoorGround.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/OutdoorLowering.h"
#include "core/SketchRead.h"

#include "game/maps/TerrainTileData.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <map>
#include <sstream>

// How the ground of a classic outdoor map is laid, as the shipped maps of Might and Magic 6 to 8 lay theirs
// (measured on Ravenshore and Harmondale: of their 16641 cell corners 76 and 64 do not follow these rules).
//
// Ground lies on the corners of the cells. Every corner holds dirt or one other kind of ground: grass, rock, snow,
// water. A map has dirt, two more kinds of land, water and roads: four tile sets of 36 tiles beside the dirt tiles.
// The tile of a cell follows from its four corners:
//   all four of one kind       the kind's plain tile, or one of its variants (3 frequent, 8 rare)
//   the kind and dirt          one of the kind's twelve tiles toward dirt: dirt along one side, on three corners
//                              or on one corner. Water's tiles toward dirt are the shore.
//   the kind on two opposite   no such tile: the corners are cleared to dirt before tiles are chosen
//   corners only
// Two kinds other than dirt never share a cell: there is always a line of dirt corners between grass and rock and
// between any land and water. Where the sketch draws them side by side, the ground that lies under the other (the
// earlier of the two in the sketch's `ground` list; any land beside water) gives up its corners.
//
// Water comes from the lowered map: the corners inside a water body's outline or along a river. The corners round
// them are dirt at the water's level, which is the beach the shipped maps have.
//
// A road is one cell wide. Its cell is dirt on all four corners (so grass leads over to it on both sides) and
// carries a road tile chosen by which of its four neighbours are road: straight, bend, T, crossing, end. A road
// that runs diagonally is a staircase of bends, each drawn with the diagonal piece instead of the round bend.
// A dirt path is the same without the road tile.

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Cells = OutdoorNodeCount;
constexpr int Nodes = OutdoorGroundNodes;
constexpr size_t CellTotal = static_cast<size_t>(Cells) * Cells;
constexpr size_t NodeTotal = static_cast<size_t>(Nodes) * Nodes;
const char *SketchFile = "sketch.yml";

struct WorldGroundKind
{
    const char *pKind;
    uint16_t row;
};

// The rows of a world's tile table where the tile sets of its ground kinds begin.
struct WorldGround
{
    const char *pWorld;
    uint8_t masterTile;
    uint16_t waterRow;
    uint16_t roadRow;
    // The second ground set of a map that uses one kind only, as most shipped maps of the world have it.
    uint16_t spareRow;
    const char *pTileTable;
    std::vector<WorldGroundKind> kinds;
};

const std::vector<WorldGround> &worldGrounds()
{
    static const std::vector<WorldGround> Worlds = {
        {"mm8", 0, 126, 414, 342, "terrain_tile_data.txt",
            {{"grass", 90}, {"rock", 342}, {"volcanic", 198}, {"swamp", 270}, {"redrock", 306}, {"desert", 162}}},
        {"mm7", 1, 126, 414, 342, "terrain_tile_data_2.txt",
            {{"grass", 90}, {"snow", 342}, {"sand", 162}, {"swamp", 270}, {"wasteland", 306}}},
        {"mm6", 2, 126, 774, 198, "terrain_tile_data_3.txt",
            {{"grass", 90}, {"snow", 342}, {"sand", 234}, {"swamp", 270}, {"volcanic", 198}, {"cracked", 162},
                {"tropical", 306}, {"cobble", 378}}},
    };
    return Worlds;
}

// The tile sets of each world's tile table (engine/data_tables/terrain_tile_data*.txt): the row where each set of 36
// begins, its first tile's name, and what it is: a liquid (water, lava, tar: the water bit), a road set (its first
// tile is laid over dirt), and for a road set whether its diagonal pieces (offsets 19 to 22) are its own art: MM6's
// table repeats MM7's diagonal tiles there, so an MM6 road jogs with two round bends, as its maps have it. Rows of
// leftover dirt tiles flagged as roads are left out. A sketch names a set by its name (the first set of that name
// and kind) or by its row.
struct TileSetEntry
{
    uint16_t row;
    const char *pName;
    bool liquid;
    bool road;
    bool diagonals;
};

const std::vector<TileSetEntry> &tileSetsOf(const std::string &world)
{
    static const std::vector<TileSetEntry> Mm8 = {{90, "grastyl", false, false, false},
        {126, "wtrtyl", true, false, false}, {162, "rdtyl", false, false, false}, {198, "voltyl", false, false, false},
        {234, "dirttyl", false, false, false}, {270, "swamptyl", false, false, false},
        {306, "rctyl", false, false, false}, {342, "rktyl", false, false, false}, {378, "lavtyl", true, false, false},
        {414, "drsrcros", false, true, true}, {450, "plntyl", false, false, false},
        {486, "plrctyl", false, false, false}, {522, "plrdcros", false, true, true},
        {558, "lavtyl", true, false, false}, {594, "plsatyl", false, false, false}, {630, "gdtyl", false, false, false},
        {666, "tartyl", true, false, false}, {702, "gstyl", false, false, false}, {738, "wtrtyl", true, false, false},
        {774, "gdrdcros", false, true, true}, {846, "tartyl", true, false, false}};
    static const std::vector<TileSetEntry> Mm7 = {{90, "7grastyl", false, false, false},
        {126, "7wtrtyl", true, false, false}, {162, "7sand", false, false, false}, {198, "7snow", false, false, false},
        {234, "7sand", false, false, false}, {270, "7swtyl", false, false, false},
        {306, "7wastetile", false, false, false}, {342, "7snow", false, false, false},
        {378, "wtrtyl", true, false, false}, {414, "7drsrcros", false, true, true}};
    static const std::vector<TileSetEntry> Mm6 = {{90, "6grastyl", false, false, false},
        {126, "6wtrtyl", true, false, false}, {162, "crktyl", false, false, false}, {198, "6voltyl", false, false, false},
        {234, "6sandtyl", false, false, false}, {270, "swmtyl", false, false, false},
        {306, "troptyl", false, false, false}, {342, "snotyl", false, false, false}, {378, "cstyl", false, false, false},
        {414, "grsrcros", false, true, false}, {450, "grrdcros", false, true, true},
        {486, "snsrcros", false, true, false}, {522, "sndrcros", false, true, false},
        {558, "vlsrcros", false, true, false}, {594, "vldrcros", false, true, false},
        {630, "trsrcros", false, true, false}, {666, "tropcros", false, true, true},
        {702, "csrcros", false, true, false}, {774, "6drsrcros", false, true, false},
        {810, "drrdcros", false, true, false}};
    static const std::vector<TileSetEntry> None;
    return world == "mm8" ? Mm8 : (world == "mm7" ? Mm7 : (world == "mm6" ? Mm6 : None));
}

enum class SetUse
{
    Ground,
    Water,
    Road,
};

// The set a sketch names for a use: by name (lower case) or by row. Null when the world has none that serves.
const TileSetEntry *findTileSet(const std::string &world, std::string text, SetUse use)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    const bool byRow = !text.empty() && std::all_of(text.begin(), text.end(), [](unsigned char character)
    {
        return std::isdigit(character) != 0;
    });

    for (const TileSetEntry &entry : tileSetsOf(world))
    {
        const bool serves = use == SetUse::Road ? entry.road : (use == SetUse::Water ? entry.liquid : !entry.road);

        if (serves && (byRow ? std::to_string(entry.row) == text : text == entry.pName))
        {
            return &entry;
        }
    }

    return nullptr;
}

const TileSetEntry *tileSetAt(const std::string &world, int row)
{
    for (const TileSetEntry &entry : tileSetsOf(world))
    {
        if (entry.row == row)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::string tileSetNames(const std::string &world, SetUse use)
{
    std::string names;

    for (const TileSetEntry &entry : tileSetsOf(world))
    {
        const bool serves = use == SetUse::Road ? entry.road : (use == SetUse::Water ? entry.liquid : !entry.road);

        if (serves)
        {
            names += (names.empty() ? "" : ", ") + std::string(entry.pName) + " (" + std::to_string(entry.row) + ")";
        }
    }

    return names;
}

// The plain ground under every other kind (the tiles below 90): the game shifts them by the master tile in MM8's
// table only (game/maps/TerrainTileData.cpp), so MM6 and MM7 maps keep their world's dirt.
struct DirtSet
{
    const char *pName;
    uint8_t masterTile;
};

const std::vector<DirtSet> &dirtSetsOf(const std::string &world)
{
    static const std::vector<DirtSet> Mm8 = {{"dirttyl", 0}, {"plntyl", 1}, {"gdtyl", 2}};
    static const std::vector<DirtSet> Mm7 = {{"7dirttyl", 1}};
    static const std::vector<DirtSet> Mm6 = {{"6dirttyl", 2}};
    static const std::vector<DirtSet> None;
    return world == "mm8" ? Mm8 : (world == "mm7" ? Mm7 : (world == "mm6" ? Mm6 : None));
}

const WorldGround *worldGroundOf(const std::string &world)
{
    for (const WorldGround &ground : worldGrounds())
    {
        if (world == ground.pWorld)
        {
            return &ground;
        }
    }

    return nullptr;
}

// The classic kind a material name stands for: the kind's own word, or a material of the terrain library that is
// drawn for it. Empty when the name stands for none.
std::string kindOfMaterial(std::string material)
{
    std::transform(material.begin(), material.end(), material.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    static const std::map<std::string, std::string> Library = {
        {"grass_meadow", "grass"}, {"grass_patchy", "grass"}, {"soil", "dirt"}, {"soil_stony", "dirt"},
        {"dirt_cracked", "dirt"}, {"rock_layered", "rock"}, {"rock_ground", "rock"}, {"rock_cliff", "rock"},
        {"rock_red", "redrock"}, {"gravel_volcanic", "volcanic"}, {"sand_ripples", "sand"}, {"sand_flat", "sand"},
        {"mud_cracked", "cracked"},
    };
    const std::map<std::string, std::string>::const_iterator found = Library.find(material);
    return found == Library.end() ? material : found->second;
}



bool numberOf(const YAML::Node &node, double &number)
{
    if (!node.IsDefined() || !node.IsScalar())
    {
        return false;
    }

    const std::string &text = node.Scalar();
    const char *pBegin = text.data() + ((!text.empty() && text[0] == '+') ? 1 : 0);
    const char *pEnd = text.data() + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, number);
    return result.ec == std::errc() && result.ptr == pEnd && std::isfinite(number);
}

bool pointsOf(const YAML::Node &node, std::vector<Point2> &points)
{
    points.clear();

    if (!node.IsDefined() || !node.IsSequence())
    {
        return false;
    }

    for (const YAML::Node &item : node)
    {
        Point2 point = {0.0, 0.0};

        if (!item.IsSequence() || item.size() != 2 || !numberOf(item[0], point[0]) || !numberOf(item[1], point[1]))
        {
            return false;
        }

        points.push_back(point);
    }

    return true;
}

// Even-odd test with half-open edges, as the lowering's.
bool insideOutline(const std::vector<Point2> &polygon, double x, double y)
{
    bool inside = false;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point2 &first = polygon[index];
        const Point2 &second = polygon[(index + 1) % polygon.size()];

        if ((first[1] > y) != (second[1] > y)
            && x < first[0] + (y - first[1]) * (second[0] - first[0]) / (second[1] - first[1]))
        {
            inside = !inside;
        }
    }

    return inside;
}

int nodeAt(int x, int y)
{
    return y * Nodes + x;
}

// A number from 0 to 1 for a cell, the same on every platform: integer mixing only.
double cellChance(int x, int y, uint32_t salt)
{
    uint32_t value = static_cast<uint32_t>(x) * 0x9e3779b1u ^ (static_cast<uint32_t>(y) * 0x85ebca77u + salt);
    value ^= value >> 15;
    value *= 0x2c1b3c6du;
    value ^= value >> 12;
    value *= 0x297a2d39u;
    value ^= value >> 15;
    return static_cast<double>(value & 0xffffffu) / 16777216.0;
}

// The plain tile or a variant, in the shares the shipped maps have: eight of ten cells the plain tile, the three
// frequent variants one in twenty each, the eight rare ones one in 160 each.
int variantOffset(int x, int y, uint32_t salt)
{
    const double chance = cellChance(x, y, salt);

    if (chance < 0.80)
    {
        return 0;
    }

    if (chance < 0.95)
    {
        return 1 + static_cast<int>((chance - 0.80) / 0.05);
    }

    return 4 + std::min(7, static_cast<int>((chance - 0.95) / 0.00625));
}

enum class RoadSurface
{
    Paved,
    Dirt,
    None,
};

RoadSurface surfaceOf(std::string surface)
{
    std::transform(surface.begin(), surface.end(), surface.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });

    if (surface.empty())
    {
        return RoadSurface::Paved;
    }

    for (const char *pWord : {"pebble", "stone", "cobble", "paved", "flag"})
    {
        if (surface.find(pWord) != std::string::npos && !surface.starts_with("none"))
        {
            return RoadSurface::Paved;
        }
    }

    for (const char *pWord : {"dirt", "soil", "earth"})
    {
        if (surface.find(pWord) != std::string::npos && !surface.starts_with("none"))
        {
            return RoadSurface::Dirt;
        }
    }

    return RoadSurface::None;
}

// The fields of one row of a tile table: tab separated, the first the row's number.
bool tableRow(const std::string &table, int index, std::string &texture, unsigned &flags)
{
    std::istringstream lines(table);
    std::string line;

    while (std::getline(lines, line))
    {
        std::vector<std::string> columns;
        size_t begin = 0;

        while (begin <= line.size())
        {
            const size_t tab = line.find('\t', begin);
            columns.push_back(line.substr(begin, tab == std::string::npos ? tab : tab - begin));

            if (tab == std::string::npos)
            {
                break;
            }

            begin = tab + 1;
        }

        int row = -1;

        if (columns.size() < 7
            || std::from_chars(columns[0].data(), columns[0].data() + columns[0].size(), row).ec != std::errc()
            || row != index)
        {
            continue;
        }

        std::string flagText = columns[6];

        while (!flagText.empty() && (flagText.back() == '\r' || flagText.back() == ' '))
        {
            flagText.pop_back();
        }

        const bool hex = flagText.starts_with("0x") || flagText.starts_with("0X");
        flags = 0;
        std::from_chars(flagText.data() + (hex ? 2 : 0), flagText.data() + flagText.size(), flags, hex ? 16 : 10);
        texture = columns[1];
        return true;
    }

    return false;
}
}

std::vector<OutdoorRoadRun> rasterizeOutdoorRoads(
    const Project &project,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings)
{
    std::vector<OutdoorRoadRun> runs;
    const YAML::Node roads = childOf(project.document(SketchFile), "roads");
    size_t bridges = 0;
    std::string unpaved;

    for (size_t index = 0; roads.IsDefined() && roads.IsSequence() && index < roads.size(); ++index)
    {
        const YAML::Node road = roads[index];
        const std::string path = "roads[" + std::to_string(index) + "]";
        std::vector<Point2> line;

        if (!pointsOf(childOf(road, "line"), line) || line.size() < 2)
        {
            issues.push_back({SketchFile, path + ".line", "a road's line is a list of at least two [x, y] points",
                "geometry"});
            continue;
        }

        const YAML::Node bridge = childOf(road, "bridge");

        if (bridge.IsDefined() && bridge.IsScalar() && bridge.Scalar() == "true")
        {
            ++bridges;
            continue;
        }

        const RoadSurface surface = surfaceOf(textOf(road, "surface"));

        if (surface == RoadSurface::None)
        {
            unpaved += (unpaved.empty() ? "" : ", ") + textOf(road, "link") + " (" + textOf(road, "surface") + ")";
            continue;
        }

        std::vector<double> bed;
        const YAML::Node bedNode = childOf(road, "bed");

        if (bedNode.IsDefined())
        {
            for (size_t point = 0; bedNode.IsSequence() && point < bedNode.size(); ++point)
            {
                double height = 0.0;

                if (numberOf(bedNode[point], height))
                {
                    bed.push_back(height);
                }
            }

            if (bed.size() != line.size())
            {
                issues.push_back({SketchFile, path + ".bed", "a road's `bed` gives one height for each of the "
                    + std::to_string(line.size()) + " points of its line; it has "
                    + std::to_string(bedNode.IsSequence() ? bedNode.size() : 0), "heights"});
                continue;
            }
        }

        OutdoorRoadRun run;
        run.link = textOf(road, "link");
        run.paved = surface == RoadSurface::Paved;
        const auto push = [&run, &bed](int x, int y, double height)
        {
            const int cell = std::clamp(y, 0, Cells - 1) * Cells + std::clamp(x, 0, Cells - 1);

            // A line that touches a cell again right after leaving it has not left it.
            if (run.cells.size() >= 2 && run.cells[run.cells.size() - 2] == cell)
            {
                run.cells.pop_back();

                if (!bed.empty())
                {
                    run.bed.pop_back();
                }

                return;
            }

            if (run.cells.empty() || run.cells.back() != cell)
            {
                run.cells.push_back(cell);

                if (!bed.empty())
                {
                    run.bed.push_back(height);
                }
            }
        };

        for (size_t segment = 0; segment + 1 < line.size(); ++segment)
        {
            const Point2 &from = line[segment];
            const Point2 &to = line[segment + 1];
            const int steps = std::max(1, static_cast<int>(std::ceil(oy::hypot(to[0] - from[0], to[1] - from[1])
                * 16.0)));

            for (int step = 0; step <= steps; ++step)
            {
                const double share = static_cast<double>(step) / steps;
                const double x = from[0] + (to[0] - from[0]) * share;
                const double y = from[1] + (to[1] - from[1]) * share;
                const double height = bed.empty() ? 0.0 : bed[segment] + (bed[segment + 1] - bed[segment]) * share;
                // A point on a cell's edge belongs to the cell south-east of it.
                const int cellX = std::clamp(static_cast<int>(std::floor(x + 1.0e-7)), 0, Cells - 1);
                const int cellY = std::clamp(static_cast<int>(std::floor(y + 1.0e-7)), 0, Cells - 1);

                if (!run.cells.empty())
                {
                    const int lastX = run.cells.back() % Cells;
                    const int lastY = run.cells.back() / Cells;

                    // Through a corner: the cell beside it whose middle the line passes nearer keeps the road in
                    // one piece.
                    if (lastX != cellX && lastY != cellY)
                    {
                        const double first = oy::hypot(cellX + 0.5 - x, lastY + 0.5 - y);
                        const double second = oy::hypot(lastX + 0.5 - x, cellY + 0.5 - y);
                        push(first <= second ? cellX : lastX, first <= second ? lastY : cellY, height);
                    }
                }

                push(cellX, cellY, height);
            }
        }

        runs.push_back(run);
    }

    if (bridges != 0)
    {
        warnings.push_back("not built yet: sketch.yml roads: " + std::to_string(bridges) + " bridges (no deck "
            "models; their lines lay no road tiles)");
    }

    if (!unpaved.empty())
    {
        warnings.push_back("roads: no tiles are laid for " + unpaved + ": a classic road is paved (pebbles, stone) "
            "or a dirt path (dirt)");
    }

    return runs;
}

int outdoorRoadTileOffset(bool north, bool east, bool south, bool west, bool staircase)
{
    const int count = (north ? 1 : 0) + (east ? 1 : 0) + (south ? 1 : 0) + (west ? 1 : 0);

    switch (count)
    {
    case 4:
        return 0;
    case 3:
        // The T pieces: north-south with a branch east or west, east-west with a branch north or south.
        return !west ? 7 : (!east ? 8 : (!south ? 9 : 10));
    case 2:
        if (north && south)
        {
            return 1;
        }

        if (east && west)
        {
            return 2;
        }

        if (north && east)
        {
            return staircase ? 20 : 3;
        }

        if (north && west)
        {
            return staircase ? 22 : 4;
        }

        if (south && east)
        {
            return staircase ? 21 : 5;
        }

        return staircase ? 19 : 6;
    case 1:
        // An end is named by the side it closes: a road that comes from the north ends in the south cap.
        return north ? 13 : (south ? 11 : (east ? 14 : 12));
    default:
        return 0;
    }
}

void settleOutdoorGroundMask(std::vector<uint8_t> &mask)
{
    if (mask.size() != NodeTotal)
    {
        return;
    }

    std::vector<uint8_t> kept(NodeTotal, 0);

    for (int pass = 0; pass < 64; ++pass)
    {
        std::fill(kept.begin(), kept.end(), 0);

        for (int y = 0; y + 1 < Nodes; ++y)
        {
            for (int x = 0; x + 1 < Nodes; ++x)
            {
                if (mask[nodeAt(x, y)] != 0 && mask[nodeAt(x + 1, y)] != 0 && mask[nodeAt(x, y + 1)] != 0
                    && mask[nodeAt(x + 1, y + 1)] != 0)
                {
                    kept[nodeAt(x, y)] = 1;
                    kept[nodeAt(x + 1, y)] = 1;
                    kept[nodeAt(x, y + 1)] = 1;
                    kept[nodeAt(x + 1, y + 1)] = 1;
                }
            }
        }

        bool changed = kept != mask;
        mask = kept;

        for (int y = 0; y + 1 < Nodes; ++y)
        {
            for (int x = 0; x + 1 < Nodes; ++x)
            {
                const bool northWest = mask[nodeAt(x, y)] != 0;
                const bool northEast = mask[nodeAt(x + 1, y)] != 0;
                const bool southWest = mask[nodeAt(x, y + 1)] != 0;
                const bool southEast = mask[nodeAt(x + 1, y + 1)] != 0;

                if (northWest && southEast && !northEast && !southWest)
                {
                    mask[nodeAt(x + 1, y + 1)] = 0;
                    changed = true;
                }
                else if (northEast && southWest && !northWest && !southEast)
                {
                    mask[nodeAt(x, y + 1)] = 0;
                    changed = true;
                }
            }
        }

        if (!changed)
        {
            return;
        }
    }
}

int outdoorGroundTileOffset(bool northWest, bool northEast, bool southWest, bool southEast)
{
    // By which corners hold dirt, bit 0 north-west, 1 north-east, 2 south-west, 3 south-east. The sets' tiles
    // toward dirt are named by where the dirt is: along a side (N, E, S, W), on three corners (NE, SE, NW, SW:
    // the kind keeps the opposite corner) or on one corner (XNE, XSE, XNW, XSW).
    static constexpr int Offsets[16] = {
        0,  // no dirt
        22, // north-west corner: XNW
        20, // north-east corner: XNE
        18, // north side: N
        23, // south-west corner: XSW
        17, // west side: W
        -1, // north-east and south-west
        14, // all but the south-east: NW
        21, // south-east corner: XSE
        -1, // north-west and south-east
        16, // east side: E
        12, // all but the south-west: NE
        19, // south side: S
        15, // all but the north-east: SW
        13, // all but the north-west: SE
        0,  // all dirt: not a tile of the set
    };
    return Offsets[(northWest ? 1 : 0) | (northEast ? 2 : 0) | (southWest ? 4 : 0) | (southEast ? 8 : 0)];
}

std::string outdoorGroundKindNames(const std::string &world)
{
    const WorldGround *pGround = worldGroundOf(world);
    std::string names = "dirt";

    for (size_t index = 0; pGround != nullptr && index < pGround->kinds.size(); ++index)
    {
        names += std::string(", ") + pGround->kinds[index].pKind;
    }

    return names;
}

bool layOutdoorGround(const Project &project, LoweredOutdoorMap &lowered, std::vector<ProjectIssue> &issues)
{
    const WorldGround *pWorld = worldGroundOf(lowered.world);

    if (pWorld == nullptr)
    {
        issues.push_back({"project.yml", "world", "oymap build knows the ground tiles of mm6, mm7 and mm8 only; no "
            "outdoor map can be built for the world " + lowered.world + " yet", "unsupported"});
        return false;
    }

    const size_t issuesBefore = issues.size();
    const YAML::Node zones = childOf(project.document(SketchFile), "ground");

    // The map's own sets (sketch `tile_sets`): its plain ground, its water and its roads; the world's usual ones
    // when left out.
    const YAML::Node tileSetsNode = childOf(project.document(SketchFile), "tile_sets");
    uint8_t masterTile = pWorld->masterTile;
    std::string dirtName;
    uint16_t waterRow = pWorld->waterRow;
    uint16_t roadRow = pWorld->roadRow;
    bool roadDiagonals = tileSetAt(lowered.world, pWorld->roadRow) == nullptr
        || tileSetAt(lowered.world, pWorld->roadRow)->diagonals;

    if (const std::string dirt = textOf(tileSetsNode, "dirt"); !dirt.empty())
    {
        std::string wanted = dirt;
        std::transform(wanted.begin(), wanted.end(), wanted.begin(), [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
        const std::vector<DirtSet> &dirts = dirtSetsOf(lowered.world);
        const std::vector<DirtSet>::const_iterator found = std::find_if(dirts.begin(), dirts.end(),
            [&wanted](const DirtSet &entry)
            {
                return wanted == entry.pName;
            });

        if (found == dirts.end())
        {
            std::string names;

            for (const DirtSet &entry : dirts)
            {
                names += (names.empty() ? "" : ", ") + std::string(entry.pName);
            }

            issues.push_back({SketchFile, "tile_sets.dirt", "the plain ground of a " + lowered.world + " map is one "
                "of " + names + " (the game shifts the tiles under every other kind by the map's master tile in "
                "MM8 only)", "ground"});
        }
        else
        {
            masterTile = found->masterTile;
            dirtName = found->pName;
        }
    }

    if (const std::string water = textOf(tileSetsNode, "water"); !water.empty())
    {
        const TileSetEntry *pSet = findTileSet(lowered.world, water, SetUse::Water);

        if (pSet == nullptr)
        {
            issues.push_back({SketchFile, "tile_sets.water", "the world " + lowered.world + " has no liquid set `"
                + water + "`; its liquid sets are " + tileSetNames(lowered.world, SetUse::Water), "ground"});
        }
        else
        {
            waterRow = pSet->row;
        }
    }

    if (const std::string road = textOf(tileSetsNode, "road"); !road.empty())
    {
        const TileSetEntry *pSet = findTileSet(lowered.world, road, SetUse::Road);

        if (pSet == nullptr)
        {
            issues.push_back({SketchFile, "tile_sets.road", "the world " + lowered.world + " has no road set `"
                + road + "`; its road sets are " + tileSetNames(lowered.world, SetUse::Road), "ground"});
        }
        else
        {
            roadRow = pSet->row;
            roadDiagonals = pSet->diagonals;
        }
    }

    // A ground zone's or a liquid body's set: a kind word of the world, a material of the terrain library, or a
    // ground or liquid set of the world's table by name or row. Returns the kind's name and row; "dirt" for the
    // map's plain ground; empty when the world has none.
    const auto groundSetOf = [&lowered, pWorld, &dirtName](const std::string &material, bool liquidOnly,
                                 uint16_t &row) -> std::string
    {
        const std::string kind = kindOfMaterial(material);

        if (!liquidOnly && (kind == "dirt" || (!dirtName.empty() && kind == dirtName)))
        {
            return "dirt";
        }

        for (const WorldGroundKind &entry : pWorld->kinds)
        {
            if (!liquidOnly && kind == entry.pKind)
            {
                row = entry.row;
                return kind;
            }
        }

        const TileSetEntry *pSet = findTileSet(lowered.world, kind, liquidOnly ? SetUse::Water : SetUse::Ground);

        if (pSet == nullptr && !liquidOnly)
        {
            pSet = findTileSet(lowered.world, kind, SetUse::Water);
        }

        if (pSet == nullptr)
        {
            return {};
        }

        row = pSet->row;
        return pSet->pName;
    };

    // The ground kind of every corner as the sketch draws it: 0 dirt, 1 and 2 the map's two other kinds of land,
    // in the order the sketch first names them.
    std::vector<std::string> kinds;
    std::vector<uint16_t> rows;
    std::vector<uint8_t> drawn(NodeTotal, 0);
    std::map<size_t, size_t> zoneCounts;
    // Per corner: the relief (highest corner minus lowest) of the steepest of the cells that meet at it.
    std::vector<double> steepest(NodeTotal, 0.0);

    for (int y = 0; y + 1 < Cells; ++y)
    {
        for (int x = 0; x + 1 < Cells; ++x)
        {
            const double corners[4] = {lowered.samples[y * Cells + x] * OutdoorHeightStep,
                lowered.samples[y * Cells + x + 1] * OutdoorHeightStep,
                lowered.samples[(y + 1) * Cells + x] * OutdoorHeightStep,
                lowered.samples[(y + 1) * Cells + x + 1] * OutdoorHeightStep};
            const double relief = *std::max_element(corners, corners + 4) - *std::min_element(corners, corners + 4);

            for (int corner = 0; corner < 4; ++corner)
            {
                double &value = steepest[nodeAt(x + corner % 2, y + corner / 2)];
                value = std::max(value, relief);
            }
        }
    }

    // A sketch without ground zones is all of the world's first kind: a map of bare dirt is not what is meant.
    const bool anyZone = zones.IsDefined() && zones.IsSequence() && zones.size() != 0;

    if (!anyZone)
    {
        kinds.push_back(pWorld->kinds[0].pKind);
        rows.push_back(pWorld->kinds[0].row);
        std::fill(drawn.begin(), drawn.end(), 1);
    }

    for (size_t index = 0; anyZone && index < zones.size(); ++index)
    {
        const YAML::Node zone = zones[index];
        const std::string path = "ground[" + std::to_string(index) + "]";
        const std::string material = textOf(zone, "material");
        std::vector<Point2> polygon;
        // A zone is an area (`polygon`) or a strip `width` nodes across along a `line` (grass along a ridge).
        std::vector<Point2> line;
        double width = 1.0;
        const YAML::Node lineNode = childOf(zone, "line");
        const bool byLine = lineNode.IsDefined();

        if (byLine == childOf(zone, "polygon").IsDefined())
        {
            issues.push_back({SketchFile, path, "a ground zone has a `polygon` (an area) or a `line` with a `width` "
                "(a strip along a ridge or a dyke), one of the two", "geometry"});
            continue;
        }

        if (byLine)
        {
            const YAML::Node widthNode = childOf(zone, "width");

            if (!pointsOf(lineNode, line) || line.size() < 2)
            {
                issues.push_back({SketchFile, path + ".line", "the line is not a list of at least two [x, y] points",
                    "geometry"});
                continue;
            }

            if (widthNode.IsDefined() && (!numberOf(widthNode, width) || width < 1.0 || width > 8.0
                || width != std::floor(width)))
            {
                issues.push_back({SketchFile, path + ".width", "a ground line's `width` is how many nodes across it "
                    "lays its ground, a whole number from 1 to 8 (1 when left out: the nodes nearest the line; 2: a "
                    "strip of whole cells)", "geometry"});
                continue;
            }
        }
        else if (!pointsOf(childOf(zone, "polygon"), polygon) || polygon.size() < 3)
        {
            issues.push_back({SketchFile, path + ".polygon", "the outline is not a list of at least three [x, y] "
                "points", "geometry"});
            continue;
        }

        uint8_t label = 0;
        uint16_t setRow = 0;
        const std::string kind = groundSetOf(material, false, setRow);

        if (kind.empty())
        {
            issues.push_back({SketchFile, path + ".material", "the world " + lowered.world + " has no ground "
                "of the kind `" + material + "`; its kinds are " + outdoorGroundKindNames(lowered.world)
                + " (or a material of the terrain library that is drawn for one of them: grass_meadow, "
                "soil, rock_layered, sand_ripples, gravel_volcanic), or one of its tile sets by name or row: "
                + tileSetNames(lowered.world, SetUse::Ground), "ground"});
            continue;
        }

        if (kind != "dirt")
        {
            const std::vector<uint16_t>::const_iterator known = std::find(rows.begin(), rows.end(), setRow);

            if (known != rows.end())
            {
                label = static_cast<uint8_t>(known - rows.begin() + 1);
            }
            else
            {
                kinds.push_back(kind);
                rows.push_back(setRow);
                label = static_cast<uint8_t>(kinds.size());
            }

            ++zoneCounts[label - 1];
        }

        // A zone may lie on steep ground only: where a cell at the corner rises more than `steeper_than`.
        double steeperThan = -1.0;
        const YAML::Node steeper = childOf(zone, "steeper_than");

        if (steeper.IsDefined() && (!numberOf(steeper, steeperThan) || steeperThan < 0.0))
        {
            issues.push_back({SketchFile, path + ".steeper_than", "`steeper_than` is how far a cell rises from its "
                "lowest corner to its highest, in map units (0 or more)", "ground"});
            continue;
        }

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                // The corners of the map's east column and south row lie on the outline of a zone drawn to the
                // map's edge, which the half-open test counts as outside: they are asked a hair inside.
                const double sampleX = x == Nodes - 1 ? x - 1.0e-6 : x;
                const double sampleY = y == Nodes - 1 ? y - 1.0e-6 : y;

                size_t segment = 0;
                double share = 0.0;
                double beyond = 0.0;
                const bool inZone = byLine ? outdoorNodeOnLine(line, width, x, y, segment, share, beyond)
                    : insideOutline(polygon, sampleX, sampleY);

                if (inZone && (steeperThan < 0.0 || steepest[nodeAt(x, y)] > steeperThan))
                {
                    drawn[nodeAt(x, y)] = label;
                }
            }
        }
    }

    // Liquid bodies laid in a ground set (`water.bodies[].tile_set`: tar pools, lava): each body's kind, by the
    // index of the lowered water shapes.
    std::vector<uint8_t> shapeLabel(lowered.waterSets.size(), 0);
    std::vector<bool> liquidKind;

    for (size_t shape = 0; shape < lowered.waterSets.size(); ++shape)
    {
        if (lowered.waterSets[shape].empty())
        {
            continue;
        }

        uint16_t setRow = 0;
        const std::string kind = groundSetOf(lowered.waterSets[shape], true, setRow);

        if (kind.empty())
        {
            issues.push_back({SketchFile, "water", "a water body's or river's `tile_set` is a liquid set of the "
                "world " + lowered.world + " other than its water: " + tileSetNames(lowered.world, SetUse::Water)
                + "; `" + lowered.waterSets[shape] + "` is none", "ground"});
            continue;
        }

        const std::vector<uint16_t>::const_iterator known = std::find(rows.begin(), rows.end(), setRow);

        if (known == rows.end())
        {
            kinds.push_back(kind);
            rows.push_back(setRow);
        }

        shapeLabel[shape] = static_cast<uint8_t>(std::find(rows.begin(), rows.end(), setRow) - rows.begin() + 1);
        zoneCounts[shapeLabel[shape] - 1] += 1;
    }

    for (const uint16_t row : rows)
    {
        const TileSetEntry *pSet = tileSetAt(lowered.world, row);
        liquidKind.push_back(pSet != nullptr && pSet->liquid);
    }

    if (kinds.size() > 2)
    {
        std::string drawn;

        for (size_t kind = 0; kind < kinds.size(); ++kind)
        {
            drawn += (kind == 0 ? "" : ", ") + kinds[kind] + " (" + std::to_string(zoneCounts[kind])
                + (zoneCounts[kind] == 1 ? " zone)" : " zones)");
        }

        issues.push_back({SketchFile, "ground", "a classic outdoor map holds dirt and two more kinds of land (its "
            "four tile sets are two grounds, water and roads); the sketch draws " + std::to_string(kinds.size())
            + ": " + drawn + ". Draw the zones of all but two of them as dirt (soil) or as one of the two", "ground"});
    }

    if (issues.size() != issuesBefore)
    {
        return false;
    }

    // Water corners, from the lowered cells; the corners of liquids laid in a ground set apart, by their kind.
    std::vector<uint8_t> water(NodeTotal, 0);
    std::vector<uint8_t> liquid(NodeTotal, 0);

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            const size_t cell = static_cast<size_t>(y) * Cells + x;
            const uint8_t corners = lowered.waterCorners[cell];
            const int shape = cell < lowered.waterShape.size() ? lowered.waterShape[cell] : -1;
            const uint8_t label = shape >= 0 && static_cast<size_t>(shape) < shapeLabel.size() ? shapeLabel[shape] : 0;

            for (int corner = 0; corner < 4; ++corner)
            {
                if ((corners & (1u << corner)) != 0)
                {
                    const int node = nodeAt(x + (corner % 2), y + (corner / 2));

                    if (label != 0 && water[node] == 0)
                    {
                        liquid[node] = label;
                    }
                    else
                    {
                        water[node] = 1;
                        liquid[node] = 0;
                    }
                }
            }
        }
    }

    // Road cells: dirt on all four corners. A cell with a corner in water is no road cell (a ford or a bridge the
    // sketch does not mark).
    std::vector<uint8_t> roadCells(CellTotal, 0);
    std::vector<uint8_t> roadNodes(NodeTotal, 0);
    size_t wetRoadCells = 0;
    std::string wetRoads;

    for (const OutdoorRoadRun &run : lowered.roads)
    {
        size_t wet = 0;

        for (const int cell : run.cells)
        {
            if (lowered.waterCorners[cell] != 0)
            {
                ++wet;
                continue;
            }

            roadCells[cell] = std::max<uint8_t>(roadCells[cell], run.paved ? 2 : 1);
        }

        if (wet != 0)
        {
            wetRoadCells += wet;
            wetRoads += (wetRoads.empty() ? "" : ", ") + run.link + " (" + std::to_string(wet) + ")";
        }
    }

    // Where several roads meet, their cells lie side by side and make a blob two cells wide, for which the road
    // tiles have no piece. A road is one cell wide: of every square of four road cells one is taken away, as long
    // as the cells round it stay joined without it (so no road is cut and no end is shortened), until none is left.
    const auto roadCellAt = [&roadCells](int x, int y)
    {
        return x >= 0 && y >= 0 && x < Cells && y < Cells && roadCells[y * Cells + x] != 0;
    };
    const auto removable = [&roadCellAt](int x, int y)
    {
        // The eight cells round it, in order: it can go when they hold exactly one unbroken run of road (cells
        // that touch only at a corner are not joined) and at least two road cells beside it.
        static const int Ring[8][2] = {{-1, -1}, {0, -1}, {1, -1}, {1, 0}, {1, 1}, {0, 1}, {-1, 1}, {-1, 0}};
        int runs = 0;
        int sides = 0;

        for (int index = 0; index < 8; ++index)
        {
            const bool here = roadCellAt(x + Ring[index][0], y + Ring[index][1]);
            const bool next = roadCellAt(x + Ring[(index + 1) % 8][0], y + Ring[(index + 1) % 8][1]);
            // A corner cell joins only through a side cell: a run begins where road follows no road, and a lone
            // corner between two empty sides is a run of its own.
            runs += !here && next ? 1 : 0;
            sides += index % 2 == 1 && here ? 1 : 0;
        }

        for (int corner = 0; corner < 8; corner += 2)
        {
            // A corner cell whose two side cells are both empty hangs on this cell alone.
            const int before = (corner + 7) % 8;
            const int after = (corner + 1) % 8;

            if (roadCellAt(x + Ring[corner][0], y + Ring[corner][1])
                && !roadCellAt(x + Ring[before][0], y + Ring[before][1])
                && !roadCellAt(x + Ring[after][0], y + Ring[after][1]))
            {
                return false;
            }
        }

        return runs == 1 && sides >= 2;
    };
    size_t thinned = 0;

    for (bool changed = true; changed;)
    {
        changed = false;

        for (int y = 0; y + 1 < Cells && !changed; ++y)
        {
            for (int x = 0; x + 1 < Cells && !changed; ++x)
            {
                if (!roadCellAt(x, y) || !roadCellAt(x + 1, y) || !roadCellAt(x, y + 1) || !roadCellAt(x + 1, y + 1))
                {
                    continue;
                }

                // The cell of the square with the fewest road cells beside it goes first: a corner of the blob,
                // not its middle.
                int best = -1;
                int fewest = 9;

                for (int corner = 0; corner < 4; ++corner)
                {
                    const int cx = x + corner % 2;
                    const int cy = y + corner / 2;
                    const int beside = (roadCellAt(cx - 1, cy) ? 1 : 0) + (roadCellAt(cx + 1, cy) ? 1 : 0)
                        + (roadCellAt(cx, cy - 1) ? 1 : 0) + (roadCellAt(cx, cy + 1) ? 1 : 0);

                    if (removable(cx, cy) && beside < fewest)
                    {
                        fewest = beside;
                        best = corner;
                    }
                }

                if (best >= 0)
                {
                    roadCells[(y + best / 2) * Cells + x + best % 2] = 0;
                    ++thinned;
                    changed = true;
                }
            }
        }
    }

    if (thinned != 0)
    {
        lowered.warnings.push_back("roads: " + std::to_string(thinned) + " road cells were taken out of squares of "
            "four where roads meet or run side by side: a road is one cell wide");
    }

    for (int cell = 0; cell < static_cast<int>(CellTotal); ++cell)
    {
        if (roadCells[cell] != 0)
        {
            const int x = cell % Cells;
            const int y = cell / Cells;
            roadNodes[nodeAt(x, y)] = 1;
            roadNodes[nodeAt(x + 1, y)] = 1;
            roadNodes[nodeAt(x, y + 1)] = 1;
            roadNodes[nodeAt(x + 1, y + 1)] = 1;
        }
    }

    if (wetRoadCells != 0)
    {
        lowered.warnings.push_back("roads: " + std::to_string(wetRoadCells) + " cells of road lie in water and "
            "carry no road: " + wetRoads + ". Draw the crossing as its own road with `bridge: true`, or move the "
            "line off the water");
    }

    // Each kind of land where it is drawn, less what must be dirt: the corners of roads, the corners at and beside
    // water, and the corners beside the kind that lies over it. Then what the tiles cannot show is cleared.
    std::vector<std::vector<uint8_t>> masks(kinds.size(), std::vector<uint8_t>(NodeTotal, 0));
    const auto near = [](const std::vector<uint8_t> &mask, int x, int y)
    {
        for (int dy = -1; dy <= 1; ++dy)
        {
            for (int dx = -1; dx <= 1; ++dx)
            {
                if (x + dx >= 0 && x + dx < Nodes && y + dy >= 0 && y + dy < Nodes
                    && mask[nodeAt(x + dx, y + dy)] != 0)
                {
                    return true;
                }
            }
        }

        return false;
    };

    for (size_t kind = kinds.size(); kind-- > 0;)
    {
        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                // A liquid lies where its bodies are; land keeps a line of dirt from water and from liquids.
                const bool pooled = liquid[nodeAt(x, y)] == kind + 1;
                masks[kind][nodeAt(x, y)] = pooled || (drawn[nodeAt(x, y)] == kind + 1 && !liquidKind[kind]
                    && roadNodes[nodeAt(x, y)] == 0 && !near(water, x, y) && !near(liquid, x, y)
                    && (kind + 1 >= kinds.size() || !near(masks[kind + 1], x, y))) ? 1 : 0;
            }
        }

        settleOutdoorGroundMask(masks[kind]);
    }

    lowered.masterTile = masterTile;
    lowered.tileSets = {rows.empty() ? pWorld->kinds[0].row : rows[0], waterRow,
        rows.size() > 1 ? rows[1] : pWorld->spareRow, roadRow};
    lowered.groundKinds = kinds;
    lowered.tileTable = pWorld->pTileTable;
    lowered.tiles.assign(CellTotal, OutdoorDirtTile);
    lowered.shoreCells = 0;
    lowered.roadCells = 0;
    const int setOf[3] = {OutdoorWaterSet, OutdoorFirstGroundSet, OutdoorSecondGroundSet};
    const auto roadAt = [&roadCells](int x, int y)
    {
        // A road that runs off the terrain runs on.
        return x < 0 || y < 0 || x >= Cells || y >= Cells || roadCells[static_cast<size_t>(y) * Cells + x] == 2;
    };
    // Which neighbours a road cell joins: bit 0 north, 1 east, 2 south, 3 west.
    const auto joins = [&roadAt](int x, int y)
    {
        return (roadAt(x, y - 1) ? 1 : 0) | (roadAt(x + 1, y) ? 2 : 0) | (roadAt(x, y + 1) ? 4 : 0)
            | (roadAt(x - 1, y) ? 8 : 0);
    };

    for (int y = 0; y < Cells; ++y)
    {
        for (int x = 0; x < Cells; ++x)
        {
            const size_t cell = static_cast<size_t>(y) * Cells + x;

            if (roadCells[cell] == 2)
            {
                const int own = joins(x, y);
                // A bend whose neighbour along the road is the opposite bend is a step of a diagonal road.
                const int opposite = ((own << 2) | (own >> 2)) & 15;
                const bool bend = own == 3 || own == 6 || own == 12 || own == 9;
                bool staircase = false;

                // A set without diagonal pieces of its own (MM6's) jogs with round bends.
                for (int side = 0; bend && roadDiagonals && side < 4; ++side)
                {
                    const int otherX = x + (side == 1 ? 1 : (side == 3 ? -1 : 0));
                    const int otherY = y + (side == 2 ? 1 : (side == 0 ? -1 : 0));

                    if ((own & (1 << side)) != 0 && otherX >= 0 && otherY >= 0 && otherX < Cells && otherY < Cells
                        && joins(otherX, otherY) == opposite)
                    {
                        staircase = true;
                    }
                }

                lowered.tiles[cell] = static_cast<uint8_t>(OutdoorFirstSetTile + OutdoorRoadSet * OutdoorSetTiles
                    + outdoorRoadTileOffset((own & 1) != 0, (own & 2) != 0, (own & 4) != 0, (own & 8) != 0,
                        staircase));
                ++lowered.roadCells;
                continue;
            }

            // The kind of the cell: the one kind other than dirt on its corners.
            int kind = -1;
            bool mixed = false;
            bool dirt[4] = {true, true, true, true};

            for (int corner = 0; corner < 4; ++corner)
            {
                const int node = nodeAt(x + (corner % 2), y + (corner / 2));
                int here = water[node] != 0 ? 0 : -1;

                for (size_t land = 0; here < 0 && land < masks.size(); ++land)
                {
                    here = masks[land][node] != 0 ? static_cast<int>(land) + 1 : -1;
                }

                if (here >= 0)
                {
                    mixed = mixed || (kind >= 0 && kind != here);
                    kind = here;
                    dirt[corner] = false;
                }
            }

            const int offset = kind < 0 || mixed ? -1 : outdoorGroundTileOffset(dirt[0], dirt[1], dirt[2], dirt[3]);

            if (offset < 0)
            {
                lowered.tiles[cell] = static_cast<uint8_t>(OutdoorDirtTile + variantOffset(x, y, 0x51ed270bu));
                continue;
            }

            lowered.tiles[cell] = static_cast<uint8_t>(OutdoorFirstSetTile + setOf[kind] * OutdoorSetTiles
                + (offset == 0 ? variantOffset(x, y, 0x1b873593u + static_cast<uint32_t>(kind)) : offset));
            lowered.shoreCells += kind == 0 && offset != 0 ? 1 : 0;
        }
    }

    return true;
}

std::vector<uint8_t> outdoorCellKinds(
    const Game::OutdoorMapData &map,
    const std::vector<Game::TerrainTileDescriptor> &tiles)
{
    std::vector<uint8_t> kinds(map.tileMap.size(), 0);

    for (size_t cell = 0; cell < map.tileMap.size() && tiles.size() >= 256; ++cell)
    {
        const int tile = map.tileMap[cell];
        const Game::TerrainTileDescriptor &descriptor = tiles[tile];

        if ((descriptor.flags & Game::TerrainTileFlagWater) != 0)
        {
            // Tar and lava are no water (their tiles' names say so: water tiles are wtrtyl in every world).
            kinds[cell] = descriptor.textureName.find("wtr") != std::string::npos ? 2 : 4;
        }
        else if ((descriptor.flags & Game::TerrainTileFlagShore) != 0)
        {
            kinds[cell] = 1;
        }
        else if (tile >= OutdoorFirstSetTile && tile < OutdoorFirstSetTile + 4 * OutdoorSetTiles)
        {
            // A road set begins with a tile that is itself laid over dirt (the crossing).
            const int base = OutdoorFirstSetTile + ((tile - OutdoorFirstSetTile) / OutdoorSetTiles) * OutdoorSetTiles;
            kinds[cell] = (tiles[base].flags & Game::TerrainTileFlagTransition) != 0 ? 3 : 0;
        }
    }

    return kinds;
}

std::string checkOutdoorTileTable(const LoweredOutdoorMap &lowered, const std::string &table)
{
    const char *pNames[4] = {"first ground", "water", "second ground", "road"};

    for (int set = 0; set < 4; ++set)
    {
        std::string texture;
        unsigned flags = 0;
        const int row = lowered.tileSets[set];

        if (!tableRow(table, row, texture, flags) || texture.empty())
        {
            return std::string("the tile table has no tile at row ") + std::to_string(row) + ", where the map's "
                + pNames[set] + " set begins";
        }

        const bool water = (flags & Game::TerrainTileFlagWater) != 0;
        const bool road = (flags & Game::TerrainTileFlagTransition) != 0;

        // A ground set may hold a liquid (tar, lava: sketch `water.bodies[].tile_set`); the water set must.
        if ((set == OutdoorWaterSet && !water) || (set == OutdoorRoadSet) != road)
        {
            return std::string("the tile at row ") + std::to_string(row) + " of the tile table (" + texture
                + ") is not what the map's " + pNames[set] + " set needs there";
        }

        // The twelve tiles toward dirt of the ground and water sets.
        for (int offset = 12; set != OutdoorRoadSet && offset < 24; ++offset)
        {
            if (!tableRow(table, row + offset, texture, flags) || texture.empty()
                || (flags & Game::TerrainTileFlagTransition) == 0)
            {
                return std::string("the tile table's set at row ") + std::to_string(row) + " (the map's "
                    + pNames[set] + " set) has no tile toward dirt at row " + std::to_string(row + offset);
            }
        }
    }

    return {};
}
}
