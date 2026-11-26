#include "core/OutdoorPlaces.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/OutdoorGrid.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <map>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// The map's cells along each side (core/OutdoorGrid).
int sideCells()
{
    return outdoorNodeCount();
}

const char *SketchFile = "sketch.yml";
// How many places are tried for each thing to place before the area is given up as full.
constexpr int TriesPerThing = 60;
// How much the ground under a scattered decoration that stands on walkable ground may vary (ScatterOptions).
constexpr double LevelSpread = 48.0;



bool numberOf(const YAML::Node &node, double &number)
{
    if (!node.IsDefined() || !node.IsScalar())
    {
        return false;
    }

    const std::string &text = node.Scalar();
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), number);
    return result.ec == std::errc() && result.ptr == text.data() + text.size() && std::isfinite(number);
}

// An area of the sketch: an outline, or a circle.
struct Area
{
    std::vector<Point2> polygon;
    Point2 center = {0.0, 0.0};
    double radius = 0.0;

    bool read(const YAML::Node &node)
    {
        const YAML::Node circle = childOf(node, "circle");
        const YAML::Node outline = childOf(node, "polygon");

        if (circle.IsDefined() && circle.IsMap())
        {
            const YAML::Node at = childOf(circle, "at");
            return at.IsDefined() && at.IsSequence() && at.size() == 2 && numberOf(at[0], center[0])
                && numberOf(at[1], center[1]) && numberOf(childOf(circle, "r"), radius) && radius > 0.0;
        }

        for (size_t index = 0; outline.IsDefined() && outline.IsSequence() && index < outline.size(); ++index)
        {
            Point2 point = {0.0, 0.0};

            if (!outline[index].IsSequence() || outline[index].size() != 2 || !numberOf(outline[index][0], point[0])
                || !numberOf(outline[index][1], point[1]))
            {
                return false;
            }

            polygon.push_back(point);
        }

        return polygon.size() >= 3;
    }

    bool holds(double x, double y) const
    {
        if (polygon.empty())
        {
            return oy::hypot(x - center[0], y - center[1]) <= radius;
        }

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

    // How far a place inside lies from the area's edge, in cells.
    double edgeDistance(double x, double y) const
    {
        if (polygon.empty())
        {
            return radius - oy::hypot(x - center[0], y - center[1]);
        }

        double nearest = 1e30;

        for (size_t index = 0; index < polygon.size(); ++index)
        {
            const Point2 &first = polygon[index];
            const Point2 &second = polygon[(index + 1) % polygon.size()];
            const double dx = second[0] - first[0];
            const double dy = second[1] - first[1];
            const double length = dx * dx + dy * dy;
            const double share = length > 0.0
                ? std::clamp(((x - first[0]) * dx + (y - first[1]) * dy) / length, 0.0, 1.0) : 0.0;
            nearest = std::min(nearest, oy::hypot(x - first[0] - dx * share, y - first[1] - dy * share));
        }

        return nearest;
    }

    // West, north, east, south.
    std::array<double, 4> box() const
    {
        if (polygon.empty())
        {
            return {center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius};
        }

        std::array<double, 4> bounds = {polygon[0][0], polygon[0][1], polygon[0][0], polygon[0][1]};

        for (const Point2 &point : polygon)
        {
            bounds = {std::min(bounds[0], point[0]), std::min(bounds[1], point[1]), std::max(bounds[2], point[0]),
                std::max(bounds[3], point[1])};
        }

        return bounds;
    }
};

// A number from 0 to 1 for a try, the same on every platform: integer mixing only.
double tryChance(uint32_t entry, uint32_t attempt, uint32_t axis)
{
    uint32_t value = entry * 0x9e3779b1u ^ (attempt * 0x85ebca77u + axis * 0xc2b2ae3du + 0x27d4eb2fu);
    value ^= value >> 15;
    value *= 0x2c1b3c6du;
    value ^= value >> 12;
    value *= 0x297a2d39u;
    value ^= value >> 15;
    return static_cast<double>(value & 0xffffffu) / 16777216.0;
}

// What a scatter entry asks of its placement beyond count and spacing (the words of the tree-spacing round:
// OUTDOOR_REBUILD_PROCEDURE.md, "Tree spacing (measured)").
struct ScatterOptions
{
    // Places already taken by the entries of its `spacing_group`, kept `spacing` from as its own.
    const std::vector<Point2> *pOthers = nullptr;
    // `close_share` of the count may stand down to `close_spacing` from the nearest (shipped forests: about one
    // tree in ten at 1.0 cell where the rest keep 1.4).
    double closeShare = 0.0;
    double closeSpacing = 0.0;
    // `edge_thin`: within `width` cells of the area's edge only `keep` of the tries are taken.
    double edgeWidth = 0.0;
    double edgeKeep = 1.0;
    // `on: water`: on open water instead of land (buoys, sea rocks).
    bool onWater = false;
    // A decoration on ground one can walk (not `steep`): the game's ground under its radius (cells) varies by no
    // more than `LevelSpread`, so it does not hang over a drop or float on one side (F6-R3, 2026-11-22: radius-52
    // bone piles on ground that dropped 49 to 57 under them). Trees, plants and natural rocks are not judged.
    double levelRadius = 0.0;
    // A scattered decoration's own radius (cells, its table's): it keeps (a placed decoration's radius + this) *
    // ClearShare from each placed one's middle; negative: not kept off them.
    double clearRadius = -1.0;
};

// How much of a placed decoration's radius and a scattered one's must lie between their middles (F73, X7 p7: a dead
// tree's trunk out of a boulder; tools/xeen/town_fit_check.py `decorations.through` judges by the same share).
constexpr double ClearShare = 0.6;
// The largest placed decoration (map units from its middle) kept clear of as a disc (the check's limit too).
constexpr double MaxClearReach = 384.0;

class Placer
{
public:
    // `clear`: the sketch's placed decorations, [x, y, radius] in cells.
    Placer(const LoweredOutdoorMap &lowered, const std::vector<std::array<double, 4>> &keepOff,
        const std::vector<std::array<double, 3>> &clear = {})
        : m_lowered(lowered)
        , m_keepOff(keepOff)
        , m_clear(clear)
        , m_blocked(static_cast<size_t>(sideCells()) * sideCells(), 0)
        , m_steep(static_cast<size_t>(sideCells()) * sideCells(), 0)
    {
        for (size_t cell = 0; cell < m_blocked.size(); ++cell)
        {
            m_blocked[cell] = lowered.waterCorners[cell] != 0 ? 1 : 0;
        }

        for (const OutdoorRoadRun &run : lowered.roads)
        {
            for (const int cell : run.cells)
            {
                m_blocked[cell] = 1;
            }
        }

        for (int y = 0; y + 1 < sideCells(); ++y)
        {
            for (int x = 0; x + 1 < sideCells(); ++x)
            {
                const int corners[4] = {lowered.samples[y * sideCells() + x], lowered.samples[y * sideCells() + x + 1],
                    lowered.samples[(y + 1) * sideCells() + x], lowered.samples[(y + 1) * sideCells() + x + 1]};
                m_steep[y * sideCells() + x] = (*std::max_element(corners, corners + 4)
                    - *std::min_element(corners, corners + 4)) * OutdoorHeightStep > OutdoorCellSize ? 1 : 0;
            }
        }
    }

    // Whether the game's ground within `radius` cells of a place varies by no more than `LevelSpread` (the middle
    // and eight points round it).
    bool level(double x, double y, double radius) const
    {
        if (radius <= 0.0)
        {
            return true;
        }

        double lowest = m_lowered.groundHeightAt(x, y);
        double highest = lowest;

        for (int point = 0; point < 8; ++point)
        {
            const double angle = point * 0.7853981633974483;
            const double height = m_lowered.groundHeightAt(x + radius * oy::cos(angle), y + radius * oy::sin(angle));
            lowest = std::min(lowest, height);
            highest = std::max(highest, height);
        }

        return highest - lowest <= LevelSpread;
    }

    // Whether a thing can stand at a place, in sketch cells: on the terrain, on land, off the roads, clear of the
    // buildings by a quarter cell, and with `walkable` not on a cell too steep to walk.
    bool free(double x, double y, bool walkable) const
    {
        if (x < 0.5 || y < 0.5 || x > sideCells() - 1.5 || y > sideCells() - 1.5)
        {
            return false;
        }

        const size_t cell = static_cast<size_t>(y) * sideCells() + static_cast<size_t>(x);

        if (m_blocked[cell] != 0 || (walkable && m_steep[cell] != 0))
        {
            return false;
        }

        // Nothing is scattered over the void (U-12, D-109): the world ends there.
        if (!m_lowered.voidCells.empty() && m_lowered.voidCells[cell] != 0)
        {
            return false;
        }

        for (const OutdoorBuildingPlan &building : m_lowered.buildings)
        {
            if (x > building.covered[0] - 0.25 && x < building.covered[2] + 0.25 && y > building.covered[1] - 0.25
                && y < building.covered[3] + 0.25)
            {
                return false;
            }
        }

        for (const std::array<double, 4> &covered : m_keepOff)
        {
            if (x > covered[0] - 0.25 && x < covered[2] + 0.25 && y > covered[1] - 0.25 && y < covered[3] + 0.25)
            {
                return false;
            }
        }

        return true;
    }

    // Whether a scattered decoration of radius `radius` (cells) at a place keeps clear of the placed decorations:
    // (their radius + its) * ClearShare from each one's middle. Negative: anything goes.
    bool clearOfPlaced(double x, double y, double radius) const
    {
        if (radius < 0.0)
        {
            return true;
        }

        return std::none_of(m_clear.begin(), m_clear.end(), [x, y, radius](const std::array<double, 3> &placed)
        {
            return oy::hypot(placed[0] - x, placed[1] - y) < (placed[2] + radius) * ClearShare;
        });
    }

    // Up to `count` places in the area in clumps: round each of `centres`, within `reach` cells of it, thinning
    // toward the rim; each at least `spacing` from the others of this call.
    std::vector<Point2> placeRound(const Area &area, const std::vector<Point2> &centres, double reach, size_t count,
        double spacing, bool walkable, uint32_t entry, double levelRadius = 0.0, double clearRadius = -1.0) const
    {
        std::vector<Point2> placed;

        for (uint32_t attempt = 0; !centres.empty() && placed.size() < count && attempt < count * TriesPerThing;
             ++attempt)
        {
            const Point2 &centre = centres[attempt % centres.size()];
            // Two chances multiplied: more near the middle than at the rim.
            const double distance = reach * tryChance(entry, attempt, 0) * (0.35 + 0.65 * tryChance(entry, attempt, 2));
            const double angle = 6.283185307179586 * tryChance(entry, attempt, 1);
            const double x = std::round((centre[0] + distance * oy::cos(angle)) * 16.0) / 16.0;
            const double y = std::round((centre[1] + distance * oy::sin(angle)) * 16.0) / 16.0;

            if (!area.holds(x, y) || !free(x, y, walkable) || (walkable && !level(x, y, levelRadius))
                || !clearOfPlaced(x, y, clearRadius))
            {
                continue;
            }

            const bool crowded = std::any_of(placed.begin(), placed.end(), [x, y, spacing](const Point2 &other)
            {
                return oy::hypot(other[0] - x, other[1] - y) < spacing;
            });

            if (!crowded)
            {
                placed.push_back({x, y});
            }
        }

        return placed;
    }

    // Up to `count` places in the area, each at least `spacing` cells from the others of this call and from
    // `options.others` (the entries of its spacing group placed before it); `options` also lets a share of them
    // stand closer, thins the rim and puts things on water instead of land.
    std::vector<Point2> place(const Area &area, size_t count, double spacing, bool walkable, uint32_t entry,
        const ScatterOptions &options = {}) const
    {
        std::vector<Point2> placed;
        const std::array<double, 4> box = area.box();
        size_t close = 0;
        const size_t closeAllowed = static_cast<size_t>(std::floor(options.closeShare * count + 1e-9));

        for (uint32_t attempt = 0; placed.size() < count && attempt < count * TriesPerThing; ++attempt)
        {
            // On a grid of sixteenths of a cell, so a place is a whole number of map units.
            const double x = std::round((box[0] + (box[2] - box[0]) * tryChance(entry, attempt, 0)) * 16.0) / 16.0;
            const double y = std::round((box[1] + (box[3] - box[1]) * tryChance(entry, attempt, 1)) * 16.0) / 16.0;

            if (!area.holds(x, y) || !(options.onWater ? onWater(x, y) : free(x, y, walkable))
                || (walkable && !options.onWater && !level(x, y, options.levelRadius))
                || !clearOfPlaced(x, y, options.clearRadius))
            {
                continue;
            }

            // The rim: only `edgeKeep` of the tries there are taken.
            if (options.edgeWidth > 0.0 && area.edgeDistance(x, y) < options.edgeWidth
                && tryChance(entry, attempt, 3) >= options.edgeKeep)
            {
                continue;
            }

            double nearest = 1e30;

            for (const Point2 &other : placed)
            {
                nearest = std::min(nearest, oy::hypot(other[0] - x, other[1] - y));
            }

            for (size_t index = 0; options.pOthers != nullptr && index < options.pOthers->size(); ++index)
            {
                const Point2 &other = (*options.pOthers)[index];
                nearest = std::min(nearest, oy::hypot(other[0] - x, other[1] - y));
            }

            if (nearest >= spacing)
            {
                placed.push_back({x, y});
            }
            else if (close < closeAllowed && nearest >= options.closeSpacing)
            {
                placed.push_back({x, y});
                ++close;
            }
        }

        return placed;
    }

    // Whether a thing can float at a place, in sketch cells: on open water (all four corners of the cell in it).
    bool onWater(double x, double y) const
    {
        if (x < 0.5 || y < 0.5 || x > sideCells() - 1.5 || y > sideCells() - 1.5)
        {
            return false;
        }

        return m_lowered.water[static_cast<size_t>(y) * sideCells() + static_cast<size_t>(x)] != 0;
    }

private:
    const LoweredOutdoorMap &m_lowered;
    const std::vector<std::array<double, 4>> m_keepOff;
    const std::vector<std::array<double, 3>> m_clear;
    std::vector<uint8_t> m_blocked;
    std::vector<uint8_t> m_steep;
};

// The decorations of decoration_data.txt by internal name (lower case): the number an ODM stores, the row's less 1;
// with `pRadii` also each one's radius for the level rule (the Radius column, map units; 0 for what grows or lies on
// slopes), with `pTableRadii` the Radius column as it is.
std::map<std::string, int> decorationIds(const std::string &table, std::map<std::string, double> *pRadii = nullptr,
    std::map<std::string, double> *pTableRadii = nullptr)
{
    std::map<std::string, int> ids;
    std::istringstream stream(table);
    std::string line;

    while (std::getline(stream, line))
    {
        const size_t firstTab = line.find('\t');
        const size_t secondTab = firstTab == std::string::npos ? firstTab : line.find('\t', firstTab + 1);
        int number = 0;

        if (firstTab == std::string::npos
            || std::from_chars(line.data(), line.data() + firstTab, number).ec != std::errc() || number < 1)
        {
            continue;
        }

        std::string name = line.substr(firstTab + 1,
            secondTab == std::string::npos ? secondTab : secondTab - firstTab - 1);
        std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });

        if (!name.empty() && !ids.contains(name))
        {
            ids[name] = number - 1;

            if (pRadii != nullptr || pTableRadii != nullptr)
            {
                // # InternalName Hint Type Radius. Trees, plants and natural rocks grow and lie on slopes (as
                // tools/xeen/check_props_support.py judges them): radius 0, so the level rule passes them.
                std::istringstream fields(line);
                std::string field;
                std::string hint;
                double radius = 0.0;

                for (int column = 0; column <= 4 && std::getline(fields, field, '\t'); ++column)
                {
                    if (column == 2)
                    {
                        hint = field;
                    }
                    else if (column == 4)
                    {
                        std::from_chars(field.data(), field.data() + field.size(), radius);
                    }
                }

                if (pTableRadii != nullptr)
                {
                    (*pTableRadii)[name] = radius;
                }

                std::string words = name + " " + hint;
                std::transform(words.begin(), words.end(), words.begin(), [](unsigned char character)
                {
                    return static_cast<char>(std::tolower(character));
                });

                for (const char *pWord : {"tree", "rock", "boulder", "basalt", "stalagmite", "crag", "plant", "bush",
                         "flower", "fern", "shrub", "grass", "reed", "mushroom", "weed", "cactus", "vine", "lily",
                         "stump", "log"})
                {
                    radius = words.find(pWord) != std::string::npos ? 0.0 : radius;
                }

                if (pRadii != nullptr)
                {
                    (*pRadii)[name] = radius;
                }
            }
        }
    }

    return ids;
}

// On ground one can walk, unless a scatter entry says it also stands on steep ground (rocks on a scarp).
bool offSteepOf(const YAML::Node &node)
{
    return textOf(node, "steep") != "true";
}

// A scatter entry's row (`line`) or ring (`line` with `closed: true`): `count` places evenly along it, the first at
// its start and the last at its end (a ring: evenly round, the last a step before the first). A row is planted where
// it is drawn, as a single decoration of `structures` is (garden kerbs stand against the houses, buoys in the water):
// the build does not move or leave out its places. False with issues when it cannot be read or leaves the map.
bool placeAlong(const YAML::Node &node, const std::string &path, std::vector<ProjectIssue> &issues,
    std::vector<Point2> &found, double &count)
{
    found.clear();
    std::vector<Point2> line;
    const YAML::Node lineNode = childOf(node, "line");
    const bool closed = textOf(node, "closed") == "true";

    for (size_t index = 0; lineNode.IsDefined() && lineNode.IsSequence() && index < lineNode.size(); ++index)
    {
        Point2 point = {0.0, 0.0};

        if (!lineNode[index].IsSequence() || lineNode[index].size() != 2 || !numberOf(lineNode[index][0], point[0])
            || !numberOf(lineNode[index][1], point[1]))
        {
            line.clear();
            break;
        }

        line.push_back(point);
    }

    for (const Point2 &point : line)
    {
        if (point[0] < 0.5 || point[1] < 0.5 || point[0] > sideCells() - 1.5 || point[1] > sideCells() - 1.5)
        {
            issues.push_back({SketchFile, path + ".line", "a row's points stand on the map's terrain, half a cell "
                "and more from its edge (0.5 to 126.5): move [" + formatNumber(point[0]) + ", "
                + formatNumber(point[1]) + "]", "geometry"});
            return false;
        }
    }

    if (line.size() < (closed ? 3u : 2u))
    {
        issues.push_back({SketchFile, path + ".line", closed
            ? "a ring (`closed: true`) is a `line` of at least three [x, y] points, the last joined to the first"
            : "a row is a `line` of at least two [x, y] points (`closed` belongs to a line: a ring)", "geometry"});
        return false;
    }

    if (childOf(node, "polygon").IsDefined() || childOf(node, "circle").IsDefined()
        || childOf(node, "clusters").IsDefined() || childOf(node, "cluster_radius").IsDefined()
        || childOf(node, "spacing").IsDefined() || childOf(node, "steep").IsDefined())
    {
        issues.push_back({SketchFile, path, "a row or a ring stands evenly along its `line`, `count` of them: give "
            "it no `polygon`, `circle`, `spacing`, `clusters`, `cluster_radius` or `steep` (it stands where it is "
            "drawn; scatter over an area is another entry)", "geometry"});
        return false;
    }

    if (!numberOf(childOf(node, "count"), count) || count < 1.0 || count != std::floor(count)
        || (!closed && count < 2.0))
    {
        issues.push_back({SketchFile, path + ".count", std::string("`count` is how many decorations stand along "
            "the line, evenly: ") + (closed ? "1 or more round a ring" : "2 or more along a row (the first at its "
            "start, the last at its end)"), "geometry"});
        return false;
    }

    if (closed)
    {
        line.push_back(line.front());
    }

    std::vector<double> lengths = {0.0};

    for (size_t index = 0; index + 1 < line.size(); ++index)
    {
        lengths.push_back(lengths.back() + oy::hypot(line[index + 1][0] - line[index][0],
            line[index + 1][1] - line[index][1]));
    }

    const double total = lengths.back();
    const size_t wanted = static_cast<size_t>(count);
    const double step = closed ? total / wanted : total / (wanted - 1);

    if (total <= 0.0)
    {
        issues.push_back({SketchFile, path + ".line", "the line has no length: its points all stand at one place",
            "geometry"});
        return false;
    }

    size_t segment = 0;

    for (size_t index = 0; index < wanted; ++index)
    {
        const double at = std::min(total, step * index);

        while (segment + 2 < lengths.size() && lengths[segment + 1] < at)
        {
            ++segment;
        }

        const double piece = lengths[segment + 1] - lengths[segment];
        const double share = piece > 0.0 ? (at - lengths[segment]) / piece : 0.0;
        // On a grid of sixteenths of a cell, so a place is a whole number of map units.
        const double x = std::round((line[segment][0] + (line[segment + 1][0] - line[segment][0]) * share) * 16.0)
            / 16.0;
        const double y = std::round((line[segment][1] + (line[segment + 1][1] - line[segment][1]) * share) * 16.0)
            / 16.0;

        found.push_back({x, y});
    }

    return true;
}

// The words of a node as one text, maps in key order. Names, notes and the entry's optional ground support
// test leave the stream of candidate points intact.
void nodeText(const YAML::Node &node, std::string &text, bool entryRoot = false)
{
    if (node.IsScalar())
    {
        text += node.Scalar();
    }
    else if (node.IsSequence())
    {
        text += '[';

        for (const YAML::Node &item : node)
        {
            nodeText(item, text);
            text += ',';
        }

        text += ']';
    }
    else if (node.IsMap())
    {
        std::map<std::string, YAML::Node> sorted;

        for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
        {
            const std::string key = entry->first.Scalar();
            noteRead(entry->second);

            if (key != "id" && key != "notes" && !(entryRoot && key == "support_radius"))
            {
                sorted.emplace(key, entry->second);
            }
        }

        text += '{';

        for (const std::pair<const std::string, YAML::Node> &entry : sorted)
        {
            text += entry.first + ':';
            nodeText(entry.second, text);
            text += ',';
        }

        text += '}';
    }
}

// Where a scatter entry's tries fall: from the entry's own words (FNV-1a of them), so an entry places the same
// whatever entries come before it (splitting one entry in two moved decorations all over the map when the seed was
// the entry's place in the list). An entry written twice alike takes the next seed for each repeat.
uint32_t scatterSeed(const YAML::Node &node, std::map<std::string, uint32_t> &repeats)
{
    std::string text;
    nodeText(node, text, true);
    uint32_t hash = 2166136261u;

    for (const char character : text)
    {
        hash = (hash ^ static_cast<unsigned char>(character)) * 16777619u;
    }

    return hash + 0x9e3779b9u * repeats[text]++;
}

int worldX(double x)
{
    return static_cast<int>(std::lround((x - sideCells() / 2) * OutdoorCellSize));
}

int worldY(double y)
{
    return static_cast<int>(std::lround((sideCells() / 2 - y) * OutdoorCellSize));
}
}

bool placeOutdoorThings(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::string &decorationTable,
    OutdoorPlaces &places,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const std::vector<std::array<double, 4>> &keepOff,
    const std::vector<OutdoorPlacedDecoration> &placed,
    const std::map<std::string, double> &drawnReach)
{
    const OutdoorGridScope gridScope(project);
    places = {};
    const size_t issuesBefore = issues.size();
    const YAML::Node sketch = project.document(SketchFile);
    const YAML::Node plan = project.document("plan.yml");
    const YAML::Node card = project.document("project.yml");
    std::map<std::string, double> tableRadii;

    if (!decorationTable.empty())
    {
        decorationIds(decorationTable, nullptr, &tableRadii);
    }

    // The sketch's placed decorations the scatter keeps clear of, in cells: each by its model's drawn reach (Xeen's
    // basalt boulders: 170 in the table, drawn 269), else its table radius. Only round pieces, up to MaxClearReach:
    // a hull piece, a Sphinx or a great tree's crown is long or open, not a disc to keep out of.
    std::vector<std::array<double, 3>> clear;

    for (const OutdoorPlacedDecoration &decoration : placed)
    {
        const std::map<std::string, double>::const_iterator table = tableRadii.find(decoration.name);
        const std::map<std::string, double>::const_iterator drawn = drawnReach.find(decoration.name);
        const double radius = drawn != drawnReach.end() ? drawn->second
            : table == tableRadii.end() ? 0.0 : table->second;

        if (radius > 0.0 && radius <= MaxClearReach)
        {
            clear.push_back({decoration.x / OutdoorCellSize + sideCells() / 2,
                sideCells() / 2 - decoration.y / OutdoorCellSize, radius / OutdoorCellSize});
        }
    }

    const Placer placer(lowered, keepOff, clear);

    // Spawn points: each encounter area holds `count` markers of one of the map's three monster slots.
    std::map<std::string, std::string> actorOfPopulation;
    std::map<std::string, double> slotOfPopulation;
    const YAML::Node spaces = childOf(plan, "spaces");

    for (size_t space = 0; spaces.IsDefined() && spaces.IsSequence() && space < spaces.size(); ++space)
    {
        const YAML::Node spaceNode = spaces[space];
        const YAML::Node population = childOf(spaceNode, "population");

        for (size_t index = 0; population.IsDefined() && population.IsSequence() && index < population.size();
             ++index)
        {
            const YAML::Node entry = population[index];
            actorOfPopulation[textOf(entry, "id")] = textOf(entry, "actor");
            double planSlot = 0.0;

            if (numberOf(childOf(entry, "slot"), planSlot))
            {
                slotOfPopulation[textOf(entry, "id")] = planSlot;
            }
        }
    }

    std::vector<std::string> slotMonsters;
    const YAML::Node slots = childOf(childOf(card, "map_stats"), "slots");

    for (size_t index = 0; slots.IsDefined() && slots.IsSequence() && index < slots.size(); ++index)
    {
        const YAML::Node slot = slots[index];
        slotMonsters.push_back(textOf(slot, "monster"));
    }

    const YAML::Node areas = childOf(sketch, "areas");
    // Seeded by each area's own words, as scatter entries are: an area places its markers the same whatever areas
    // come before it (the place in the list moved every later area's markers when one was added or split).
    std::map<std::string, uint32_t> areaRepeats;
    size_t shortSpawns = 0;
    std::string unslotted;

    for (size_t index = 0; areas.IsDefined() && areas.IsSequence() && index < areas.size(); ++index)
    {
        const YAML::Node node = areas[index];
        const std::string path = "areas[" + std::to_string(index) + "]";
        const std::string kind = textOf(node, "kind");

        if (!kind.empty() && kind != "encounter" && kind != "items")
        {
            continue;
        }

        Area area;

        if (!area.read(node))
        {
            issues.push_back({SketchFile, path, "an area needs a `polygon` of at least three points or a `circle` "
                "with `at` and `r`", "geometry"});
            continue;
        }

        const std::string id = textOf(node, "id");
        double slot = 0.0;

        if (kind == "items")
        {
            // Item spawn points, as the shipped maps have them (Harmondale: six, of treasure levels 2 and 3): a
            // marker of type 2 whose number is the treasure level of the thing the game lays there.
            double level = 0.0;
            double markers = 1.0;
            numberOf(childOf(node, "count"), markers);

            if (!numberOf(childOf(node, "level"), level) || level < 1.0 || level > 7.0 || level != std::floor(level))
            {
                issues.push_back({SketchFile, path + ".level", "an items area has a `level`: the treasure level of "
                    "what lies there, 1 to 7", "reference"});
                continue;
            }

            const std::vector<Point2> lying = placer.place(area, static_cast<size_t>(markers), 0.25, true,
                scatterSeed(node, areaRepeats) ^ 0x7000u);
            shortSpawns += static_cast<size_t>(markers) - lying.size();

            for (const Point2 &point : lying)
            {
                OutdoorPlacedSpawn spawn = {id, static_cast<int>(level), worldX(point[0]), worldY(point[1]),
                    static_cast<int>(std::lround(lowered.groundHeightAt(point[0], point[1])))};
                spawn.type = 2;
                places.spawns.push_back(spawn);
            }

            continue;
        }

        if (childOf(node, "level").IsDefined())
        {
            issues.push_back({SketchFile, path + ".level", "`level` is the treasure level of an items area (`kind: "
                "items`); an encounter area spawns monsters of a `slot`", "reference"});
            continue;
        }

        if (!numberOf(childOf(node, "slot"), slot))
        {
            const std::map<std::string, std::string>::const_iterator actor = actorOfPopulation.find(id);
            const std::map<std::string, double>::const_iterator planned = slotOfPopulation.find(id);
            slot = planned != slotOfPopulation.end() ? planned->second : 0.0;

            for (size_t monster = 0; actor != actorOfPopulation.end() && monster < slotMonsters.size(); ++monster)
            {
                slot = !actor->second.empty() && slotMonsters[monster] == actor->second && slot == 0.0
                    ? static_cast<double>(monster + 1) : slot;
            }

            // A population that is none of the map's monsters (townsfolk, guards, a scripted force) is made of
            // placed actors, not of spawn points: a marker of some other slot would put wolves in the market.
            if (slot == 0.0)
            {
                unslotted += (unslotted.find(id) == std::string::npos ? (unslotted.empty() ? "" : ", ") + id : "");
                continue;
            }
        }

        if (slot < 1.0 || slot > 3.0)
        {
            issues.push_back({SketchFile, path + ".slot", "a map has three monster slots: `slot` is 1, 2 or 3",
                "reference"});
            continue;
        }

        double count = 1.0;
        numberOf(childOf(node, "count"), count);
        // Half a cell apart: on the shipped maps the markers of one pack stand 180 to 600 units from each other
        // (Ravenshore's median is 364).
        const std::vector<Point2> found = placer.place(area, static_cast<size_t>(count), 0.5, true,
            scatterSeed(node, areaRepeats) ^ 0x5000u);
        shortSpawns += static_cast<size_t>(count) - found.size();

        for (const Point2 &point : found)
        {
            places.spawns.push_back({id, static_cast<int>(slot), worldX(point[0]), worldY(point[1]),
                static_cast<int>(std::lround(lowered.groundHeightAt(point[0], point[1])))});
        }
    }

    if (!unslotted.empty())
    {
        warnings.push_back("not built yet: areas of " + unslotted + ": their populations are none of the "
            "map's monster slots (placed actors: townsfolk, guards, scripted forces), so they get no spawn "
            "points. For monsters of a slot, give the area or its plan population a `slot`, or name the slot's "
            "monster in project.yml map_stats.slots as the population names its actor");
    }

    if (shortSpawns != 0)
    {
        warnings.push_back("areas: " + std::to_string(shortSpawns) + " spawn points found no place: their areas "
            "are water, road, buildings or too steep to walk, or too small for their count at half a cell apart");
    }

    // Decorations.
    const YAML::Node scatter = childOf(sketch, "scatter");
    const size_t entries = scatter.IsDefined() && scatter.IsSequence() ? scatter.size() : 0;

    if (entries != 0 && decorationTable.empty())
    {
        warnings.push_back("scatter: " + std::to_string(entries) + " entries are left out: decorations are named "
            "by engine/data_tables/decoration_data.txt, so the build needs an asset root (--assets)");
        return issues.size() == issuesBefore;
    }

    std::map<std::string, double> radii;
    const std::map<std::string, int> ids = decorationIds(decorationTable, &radii);
    size_t shortDecorations = 0;
    size_t wanted = 0;
    std::map<std::string, uint32_t> repeats;
    // The places taken by each spacing group so far.
    std::map<std::string, std::vector<Point2>> spacingGroups;
    // The entries that found no place for all their count: "scatter[3] (pines) 12 of 40".
    std::vector<std::string> shortEntries;

    for (size_t index = 0; index < entries; ++index)
    {
        const YAML::Node node = scatter[index];
        const std::string path = "scatter[" + std::to_string(index) + "]";
        // `decoration`, or `kinds`: several decorations mixed one by one, each by its weight.
        std::vector<std::pair<std::string, double>> kinds;
        const YAML::Node kindsNode = childOf(node, "kinds");
        double totalWeight = 0.0;
        bool readable = true;

        if (kindsNode.IsDefined())
        {
            if (!kindsNode.IsMap() || kindsNode.size() == 0 || childOf(node, "decoration").IsDefined())
            {
                readable = false;
            }

            for (YAML::const_iterator kind = kindsNode.begin(); readable && kind != kindsNode.end(); ++kind)
            {
                noteRead(kind->second);
                double weight = 0.0;

                if (!numberOf(kind->second, weight) || weight <= 0.0)
                {
                    readable = false;
                    break;
                }

                kinds.push_back({kind->first.Scalar(), weight});
                totalWeight += weight;
            }

            if (!readable)
            {
                issues.push_back({SketchFile, path + ".kinds", "`kinds` mixes decorations one by one: {tree41: 2, "
                    "tree42: 1} (a weight above 0 for each), instead of `decoration`", "geometry"});
                continue;
            }

            // In name order, so the choice does not hang on how the map was written.
            std::sort(kinds.begin(), kinds.end());
        }
        else
        {
            kinds.push_back({textOf(node, "decoration"), 1.0});
            totalWeight = 1.0;
        }

        std::vector<int> kindIds;

        for (std::pair<std::string, double> &kind : kinds)
        {
            std::transform(kind.first.begin(), kind.first.end(), kind.first.begin(), [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            });
            const std::map<std::string, int>::const_iterator id = ids.find(kind.first);

            if (id == ids.end())
            {
                issues.push_back({SketchFile, path + (kindsNode.IsDefined() ? ".kinds" : ".decoration"),
                    "there is no decoration named " + kind.first + " in decoration_data.txt (oymap assets <text> "
                    "--kind decoration lists them)", "reference"});
                readable = false;
                break;
            }

            kindIds.push_back(id->second);
        }

        if (!readable)
        {
            continue;
        }

        // What events change the entry's decorations by (`set_sprite`, `hide`): its `id`, else its `group`.
        const std::string target = !textOf(node, "id").empty() ? textOf(node, "id")
            : childOf(node, "group").IsDefined() ? "group:" + textOf(node, "group") : std::string();
        Area area;
        double count = 0.0;
        double spacing = 0.5;
        // `height: [low, high]`: floating that far over the land (the Plane of Air's clouds), by a fixed rule.
        double lowest = 0.0;
        double highest = 0.0;
        const YAML::Node heightNode = childOf(node, "height");

        if (heightNode.IsDefined() && (!heightNode.IsSequence() || heightNode.size() != 2
                || !numberOf(heightNode[0], lowest) || !numberOf(heightNode[1], highest) || lowest > highest
                || lowest < -512.0 || highest > 16384.0))
        {
            issues.push_back({SketchFile, path + ".height", "`height` is [low, high]: how far over the land (or the "
                "water) the decorations float, map units, -512 to 16384", "geometry"});
            continue;
        }

        const std::string on = textOf(node, "on");

        if (!on.empty() && on != "land" && on != "water")
        {
            issues.push_back({SketchFile, path + ".on", "`on` is land (the default) or water (buoys, sea rocks: "
                "open water only)", "geometry"});
            continue;
        }

        const auto chooseKind = [&](uint32_t seed, size_t placeIndex)
        {
            if (kinds.size() == 1)
            {
                return size_t(0);
            }

            double pick = tryChance(seed, static_cast<uint32_t>(placeIndex), 5) * totalWeight;

            for (size_t kind = 0; kind < kinds.size(); ++kind)
            {
                pick -= kinds[kind].second;

                if (pick < 0.0)
                {
                    return kind;
                }
            }

            return kinds.size() - 1;
        };
        const auto addPlaced = [&](const std::vector<Point2> &found, uint32_t seed)
        {
            for (size_t placeIndex = 0; placeIndex < found.size(); ++placeIndex)
            {
                const Point2 &point = found[placeIndex];
                const size_t kind = chooseKind(seed, placeIndex);
                const double lift = heightNode.IsDefined()
                    ? std::round(lowest + (highest - lowest) * tryChance(seed, static_cast<uint32_t>(placeIndex), 6))
                    : 0.0;
                OutdoorPlacedDecoration decoration = {kinds[kind].first, kindIds[kind], worldX(point[0]),
                    worldY(point[1]), static_cast<int>(std::lround(
                        lowered.decorationGroundAt(kinds[kind].first, point[0], point[1], 0) + lift)),
                    target};
                decoration.entry = static_cast<int>(index);
                places.decorations.push_back(decoration);
            }
        };

        if (childOf(node, "line").IsDefined() || childOf(node, "closed").IsDefined())
        {
            // A row or a ring: `count` decorations evenly along the line.
            std::vector<Point2> found;

            if (placeAlong(node, path, issues, found, count))
            {
                wanted += static_cast<size_t>(count);
                shortDecorations += static_cast<size_t>(count) - found.size();
                addPlaced(found, scatterSeed(node, repeats));
            }

            continue;
        }

        if (!area.read(node) || !numberOf(childOf(node, "count"), count) || count < 0.0)
        {
            issues.push_back({SketchFile, path, "a scatter entry needs a `count` and a `polygon` of at least three "
                "points or a `circle` with `at` and `r`", "geometry"});
            continue;
        }

        double clusters = 0.0;
        double reach = 1.5;
        numberOf(childOf(node, "clusters"), clusters);
        numberOf(childOf(node, "cluster_radius"), reach);

        // Clumps keep a cell between their things unless `spacing` says otherwise: packed at half a cell they
        // read as one blot (Vertigo's dead forest, pass two); an even throw keeps half a cell.
        if (!numberOf(childOf(node, "spacing"), spacing))
        {
            spacing = clusters >= 1.0 ? 1.0 : 0.5;
        }

        // On ground one can walk, unless the entry says it also stands on steep ground (rocks on a scarp).
        const bool offSteep = offSteepOf(node);

        if (clusters < 0.0 || clusters > 64.0 || clusters != std::floor(clusters) || reach <= 0.0 || reach > 32.0)
        {
            issues.push_back({SketchFile, path, "`clusters` is how many clumps the count stands in (0 to 64; 0 or "
                "left out: spread evenly) and `cluster_radius` how far a clump reaches, in cells (up to 32)",
                "geometry"});
            continue;
        }

        ScatterOptions options;
        options.onWater = on == "water";

        options.clearRadius = 0.0;

        for (const std::pair<std::string, double> &kind : kinds)
        {
            const std::map<std::string, double>::const_iterator radius = radii.find(kind.first);
            options.levelRadius = std::max(options.levelRadius,
                radius == radii.end() ? 0.0 : radius->second / OutdoorCellSize);
            const std::map<std::string, double>::const_iterator table = tableRadii.find(kind.first);
            options.clearRadius = std::max(options.clearRadius,
                table == tableRadii.end() ? 0.0 : table->second / OutdoorCellSize);
        }
        if (const YAML::Node support = childOf(node, "support_radius"); support.IsDefined())
        {
            double radius = 0.0;
            if (!numberOf(support, radius) || radius < 0.0)
            {
                issues.push_back({SketchFile, path + ".support_radius", "a ground support radius is a nonnegative "
                    "number of map units", "geometry"});
                continue;
            }
            options.levelRadius = radius / OutdoorCellSize;
        }

        const std::string spacingGroup = textOf(node, "spacing_group");
        const YAML::Node closeShare = childOf(node, "close_share");
        const YAML::Node closeSpacing = childOf(node, "close_spacing");

        if (closeShare.IsDefined() != closeSpacing.IsDefined()
            || (closeShare.IsDefined() && (!numberOf(closeShare, options.closeShare) || options.closeShare < 0.0
                || options.closeShare > 1.0 || !numberOf(closeSpacing, options.closeSpacing)
                || options.closeSpacing < 0.0 || options.closeSpacing >= spacing)))
        {
            issues.push_back({SketchFile, path + ".close_share", "`close_share` (0 to 1) of the count may stand "
                "down to `close_spacing` (cells, under `spacing`) from the nearest: give both (shipped forests: 0.1 "
                "at 1.0 where the rest keep 1.4)", "geometry"});
            continue;
        }

        if (const YAML::Node edge = childOf(node, "edge_thin"); edge.IsDefined())
        {
            if (!edge.IsMap() || !numberOf(childOf(edge, "width"), options.edgeWidth) || options.edgeWidth <= 0.0
                || options.edgeWidth > 32.0 || !numberOf(childOf(edge, "keep"), options.edgeKeep)
                || options.edgeKeep < 0.0 || options.edgeKeep > 1.0)
            {
                issues.push_back({SketchFile, path + ".edge_thin", "`edge_thin` is {width: <cells from the area's "
                    "edge, up to 32>, keep: <the share kept there, 0 to 1>} (shipped stands: width 3, keep 0.33)",
                    "geometry"});
                continue;
            }
        }

        if (options.onWater && (clusters >= 1.0 || textOf(node, "steep") == "true"))
        {
            issues.push_back({SketchFile, path + ".on", "things on water are spread evenly: no `clusters` or "
                "`steep`", "geometry"});
            continue;
        }

        if (!spacingGroup.empty())
        {
            options.pOthers = &spacingGroups[spacingGroup];
        }

        std::vector<Point2> found;
        const uint32_t seed = scatterSeed(node, repeats);

        if (clusters >= 1.0)
        {
            // The clumps' middles keep two reaches apart where the area has room, one where not.
            std::vector<Point2> centres = placer.place(area, static_cast<size_t>(clusters), reach * 2.0, offSteep,
                seed ^ 0xc000u);

            if (centres.size() < static_cast<size_t>(clusters))
            {
                centres = placer.place(area, static_cast<size_t>(clusters), reach, offSteep, seed ^ 0xc000u);
            }

            found = placer.placeRound(area, centres, reach, static_cast<size_t>(count), std::max(spacing, 0.0),
                offSteep, seed, options.levelRadius, options.clearRadius);
        }
        else
        {
            found = placer.place(area, static_cast<size_t>(count), std::max(spacing, 0.0), offSteep, seed, options);
        }

        if (!spacingGroup.empty())
        {
            spacingGroups[spacingGroup].insert(spacingGroups[spacingGroup].end(), found.begin(), found.end());
        }

        wanted += static_cast<size_t>(count);
        shortDecorations += static_cast<size_t>(count) - found.size();

        if (found.size() < static_cast<size_t>(count))
        {
            shortEntries.push_back(path + (textOf(node, "id").empty() ? "" : " (" + textOf(node, "id") + ")") + " "
                + std::to_string(found.size()) + " of " + std::to_string(static_cast<size_t>(count)));
        }

        addPlaced(found, seed);
    }

    if (shortDecorations != 0)
    {
        std::string named;

        for (size_t index = 0; index < shortEntries.size() && index < 12; ++index)
        {
            named += (index == 0 ? "" : ", ") + shortEntries[index];
        }

        if (shortEntries.size() > 12)
        {
            named += " and " + std::to_string(shortEntries.size() - 12) + " more";
        }

        warnings.push_back("scatter: " + std::to_string(shortDecorations) + " of " + std::to_string(wanted)
            + " decorations found no place: their areas are water, road, buildings or ground too steep to walk "
            "(say `steep: true` for what stands on a scarp), or too small for their count at their spacing"
            + (named.empty() ? std::string() : " (" + named + ")"));
    }

    return issues.size() == issuesBefore;
}
}
