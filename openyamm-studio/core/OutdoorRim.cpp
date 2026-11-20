#include "core/OutdoorRim.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>

// The rim, in plain words.
//
// The party walks a square 23143 units from the map's middle: the nodes 19 to 109. The 8103 nodes outside it (half
// of the map) are land that is seen and never walked. Measured on four shipped maps (Harmondale 7out02, Ravenshore
// out02, New Sorpigal oute3, Dagger Wound out01; output/studio_s4e/orig/*.rim.txt):
//
//   What stands on it: no building model and no spawn point on any of the four; 61, 31, 66 and 0 decorations
//   (trees and rocks) against 507, 794, 413 and 800 inside.
//
//   What it is, by side: one of three things.
//     Sea or level ground: 92 to 100 % of the nodes at one height (all of Dagger Wound, three sides of New
//     Sorpigal, Ravenshore's south), with a few islets.
//     A shelf: high level ground that runs to the map's edge, uneven by a few hundred units (Ravenshore's east:
//     median 2432, a tenth of the nodes under 2144 and a tenth over 2848; its west the same with the headland on
//     it).
//     A ridge: a chain of round mounds that hides the map's edge (all four sides of Harmondale): tops at 2560 to
//     3360 (the highest 3584 to 4000) standing 11 to 13 cells out from the square (a tenth nearer than 8, a tenth
//     farther than 16), 17, 10 and 19 tops on three sides (one every 7 cells); between the square and the ridge
//     the land falls to a floor 4 to 6 cells out where the square's edge is low (the mean of the north side: 1466
//     at the edge, 913 four cells out, 2174 twelve out) and stays high where the edge is high (the west: 2428,
//     1950, 2329).
//   Or the land goes on as inside (Ravenshore's north, New Sorpigal's west): no rim to speak of, the heights say
//   it.
//
//   How it meets the walked land: without a break. The node two cells out follows the edge node (correlation 0.66
//   to 0.99 along a side), four cells out 0.4 to 0.9, eight cells out it has nothing to do with it.
//
//   How rugged: a node stands 83 to 121 units off the mean of the eight nodes round it on Harmondale's ridges
//   (half of them under 64, a tenth over 224 to 296: scarps one cell wide), 53 to 72 on Ravenshore's shelves, 0 on
//   sea.
//
//   The outer rows: the outermost row of nodes stands at one height on each side: 640 on all four sides of
//   Harmondale (rows 0 and 126; row and column 127, which close the last cells, are 0 there), 0 in Ravenshore's
//   north and west with the shelf at 2304 standing behind it, 2304 in its east, 0 where the rim is sea.
//
//   Valleys: where a road or a river leaves the square it runs on to the map's edge on a floor of its own, and
//   the ridge or the shelf stands back from it (Harmondale's three roads and its stream, Ravenshore's two passes
//   and its river).
//
// What a sketch says: `frame.rim` entries with a `form`, one for a side or for a stretch of it (`span`), and
// `frame.edge`. What the build does with them, for every node outside the square:
//
// 1. The land at the square's edge nearest the node (the mean of five nodes along the edge) is where every form
//    starts from, so the rim meets the walked land without a break.
// 2. `form: level`: the ground runs from the edge land to the form's own height over `meet` cells (4), then lies
//    there. With two heights it lies between them, rising and falling over about six cells (a shelf).
// 3. `form: ridge`: the ground falls from the edge land to the `floor` half-way to the crest (never rises to it:
//    where the edge is high the land stays high), a crest runs `crest` cells out at the lower of the two heights,
//    and mounds stand on it every six cells or so, their tops between the two heights, each 4 to 7 cells in radius;
//    behind the crest everything falls to the edge height (or the floor) at the map's last row. Where along the
//    crest a mound stands, how far it stands off the line (2.5 cells either way) and how high it is come from the
//    `seed`.
// 4. `roughness` moves each node up or down off the smooth form: the mean of what it adds, in map units, most
//    nodes by little and a few by much. None on the floor of a ridge or at the square's edge.
// 5. Where two entries meet (in the map's corners, at the ends of spans) they run into each other over four
//    cells; a node in a corner belongs to the side it stands farther out on. Past the end of every span the
//    heights of the sketch (grid, bands) speak as they do inside.
// 6. A road or a river that runs through the rim keeps its valley: within one cell of its own width the land lies
//    at the road's bed (the river's level; without either, at the land the heights give along the line), and the
//    form closes in over the next three cells.
// 7. `frame.edge`: the outermost row of nodes of a side stands at its height, whatever lies behind it.
// Height points, cliff lines, water and road beds are applied afterwards as everywhere (an islet in a sea rim is
// a height point).
//
// Nothing is random: a seed and a node give the same number on every machine (whole-number arithmetic).

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Nodes = 128;
constexpr int First = OutdoorPlayableFirstNode;
constexpr int Last = OutdoorPlayableLastNode;
const char *SketchFile = "sketch.yml";
// Cells over which two entries, or an entry and the heights beyond its span, run into each other.
constexpr double JoinCells = 4.0;
// A ridge (Harmondale's north, numbers in rows of nodes): a broad bank 8 to 10 nodes across whose top rises and
// falls along the side between saddles and tops, a top every 7 cells, the bank's line wandering 2 cells in and out.
// Cells from top to top along the crest; how far the crest's line wanders to each side; the bank's half-width
// across, least and most (it changes along the side too).
constexpr double MoundSpacing = 7.0;
constexpr double MoundOffLine = 3.0;
constexpr double CrestHalfWidthLeast = 4.5;
constexpr double CrestHalfWidthMost = 6.5;
// What the waves along a ridge are drawn from: separate rows of one field of chance, so they do not move together.
constexpr double TopRow = 1000.0;
constexpr double LineRow = 2000.0;
constexpr double WidthRow = 3000.0;
// A shelf rises and falls between its two heights over this many cells.
constexpr double ShelfWaveCells = 6.0;
// A valley: beyond the road's or river's own width its floor is this wide to each side, and the form closes in
// over this many cells more.
constexpr double ValleyFloorCells = 1.0;
constexpr double ValleyWallCells = 3.0;
// A valley's line is followed every this many cells.
constexpr double ValleyStepCells = 0.25;
// Roughness: a node's share is u * |u| for u between -1 and 1, whose mean size is a third; a node then stands
// 1.06 times that off the mean of its eight neighbours.
constexpr double RoughnessScale = 3.0 / 1.06;
constexpr double Pi = 3.14159265358979323846;



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

const char *sideName(OutdoorRimSide side)
{
    switch (side)
    {
    case OutdoorRimSide::North:
        return "north";
    case OutdoorRimSide::East:
        return "east";
    case OutdoorRimSide::South:
        return "south";
    default:
        return "west";
    }
}

bool sideOf(const std::string &text, OutdoorRimSide &side)
{
    for (const OutdoorRimSide candidate : {OutdoorRimSide::North, OutdoorRimSide::East, OutdoorRimSide::South,
             OutdoorRimSide::West})
    {
        if (text == sideName(candidate))
        {
            side = candidate;
            return true;
        }
    }

    return false;
}

bool inSquare(double x, double y)
{
    return x >= First && x <= Last && y >= First && y <= Last;
}

// A number from 0 to 1 (never 1) for a seed and up to three whole numbers, the same on every machine.
double chance(uint32_t seed, int32_t first, int32_t second, int32_t third)
{
    uint32_t value = seed * 0x9E3779B1u;
    value ^= static_cast<uint32_t>(first) * 0x85EBCA6Bu;
    value = (value << 13) | (value >> 19);
    value ^= static_cast<uint32_t>(second) * 0xC2B2AE35u;
    value = (value << 17) | (value >> 15);
    value ^= static_cast<uint32_t>(third) * 0x27D4EB2Fu;
    value ^= value >> 16;
    value *= 0x7FEB352Du;
    value ^= value >> 15;
    value *= 0x846CA68Bu;
    value ^= value >> 16;
    return static_cast<double>(value >> 8) / 16777216.0;
}

double ease(double share)
{
    const double clamped = std::clamp(share, 0.0, 1.0);
    return clamped * clamped * (3.0 - 2.0 * clamped);
}

// 1 at the middle of a round mound, 0 at its foot and beyond.
double bell(double share)
{
    return share >= 1.0 ? 0.0 : 0.5 + 0.5 * oy::cos(Pi * std::max(0.0, share));
}

// A value from 0 to 1 that changes smoothly from place to place, level over about `cells` cells.
double wave(uint32_t seed, double x, double y, double cells)
{
    const double gridX = x / cells;
    const double gridY = y / cells;
    const int x0 = static_cast<int>(std::floor(gridX));
    const int y0 = static_cast<int>(std::floor(gridY));
    const double shareX = ease(gridX - x0);
    const double shareY = ease(gridY - y0);
    const double north = chance(seed, x0, y0, 77) * (1.0 - shareX) + chance(seed, x0 + 1, y0, 77) * shareX;
    const double south = chance(seed, x0, y0 + 1, 77) * (1.0 - shareX) + chance(seed, x0 + 1, y0 + 1, 77) * shareX;
    return north * (1.0 - shareY) + south * shareY;
}

double fieldAt(const std::vector<double> &field, double x, double y)
{
    const double clampedX = std::clamp(x, 0.0, Nodes - 1.0);
    const double clampedY = std::clamp(y, 0.0, Nodes - 1.0);
    const int x0 = std::min(Nodes - 2, static_cast<int>(clampedX));
    const int y0 = std::min(Nodes - 2, static_cast<int>(clampedY));
    const double shareX = clampedX - x0;
    const double shareY = clampedY - y0;
    const double north = field[static_cast<size_t>(y0) * Nodes + x0] * (1.0 - shareX)
        + field[static_cast<size_t>(y0) * Nodes + x0 + 1] * shareX;
    const double south = field[static_cast<size_t>(y0 + 1) * Nodes + x0] * (1.0 - shareX)
        + field[static_cast<size_t>(y0 + 1) * Nodes + x0 + 1] * shareX;
    return north * (1.0 - shareY) + south * shareY;
}

// How many rows of nodes a side's strip has: the outermost row stands this far out.
int stripDepth(OutdoorRimSide side)
{
    return side == OutdoorRimSide::North || side == OutdoorRimSide::West ? First : Nodes - 1 - Last;
}

struct ValleyPoint
{
    double x = 0.0;
    double y = 0.0;
    double floor = 0.0;
};

// A ridge at a place along its side: where its crest runs (cells out from the square), how high its top is there
// and how wide its bank is to each side of the crest.
struct RidgeAt
{
    double crest = 0.0;
    double top = 0.0;
    double halfWidth = 1.0;
};

RidgeAt ridgeAt(const OutdoorRimEntry &entry, double along)
{
    RidgeAt ridge;
    ridge.crest = entry.crest + (wave(entry.seed, along, LineRow, MoundSpacing * 2.0) * 2.0 - 1.0) * MoundOffLine;
    ridge.top = entry.low + (entry.high - entry.low) * wave(entry.seed, along, TopRow, MoundSpacing);
    ridge.halfWidth = CrestHalfWidthLeast + (CrestHalfWidthMost - CrestHalfWidthLeast)
        * wave(entry.seed, along, WidthRow, MoundSpacing);
    return ridge;
}
}

bool OutdoorRim::shapesAnything() const
{
    return !entries.empty() || edge[0] || edge[1] || edge[2] || edge[3];
}

double outdoorChance(uint32_t seed, int32_t first, int32_t second, int32_t third)
{
    return chance(seed, first, second, third);
}

double outdoorWave(uint32_t seed, double x, double y, double cells)
{
    return wave(seed, x, y, cells);
}

int outdoorRimDistance(OutdoorRimSide side, int x, int y)
{
    switch (side)
    {
    case OutdoorRimSide::North:
        return First - y;
    case OutdoorRimSide::South:
        return y - Last;
    case OutdoorRimSide::West:
        return First - x;
    default:
        return x - Last;
    }
}

void readOutdoorRim(const YAML::Node &sketch, OutdoorRim &rim, std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings)
{
    rim = {};
    const YAML::Node frame = childOf(sketch, "frame");
    const YAML::Node edge = childOf(frame, "edge");
    const auto add = [&issues](const std::string &path, const std::string &message)
    {
        issues.push_back({SketchFile, path, message, "heights"});
    };
    const auto storable = [](double height)
    {
        return height >= 0.0 && height <= 8160.0;
    };

    if (edge.IsDefined() && edge.IsMap())
    {
        double all = 0.0;
        const bool hasAll = numberOf(childOf(edge, "height"), all);

        for (const OutdoorRimSide side : {OutdoorRimSide::North, OutdoorRimSide::East, OutdoorRimSide::South,
                 OutdoorRimSide::West})
        {
            double own = 0.0;

            if (numberOf(childOf(edge, sideName(side)), own))
            {
                rim.edge[static_cast<size_t>(side)] = own;
            }
            else if (hasAll)
            {
                rim.edge[static_cast<size_t>(side)] = all;
            }

            const std::optional<double> &height = rim.edge[static_cast<size_t>(side)];

            if (height && !storable(*height))
            {
                add("frame.edge", "the map's edge stands at " + formatNumber(*height) + " on the "
                    + sideName(side) + " side; an outdoor map stores heights from 0 to 8160: give a height in "
                    "that range");
            }
        }

        if (!rim.shapesAnything())
        {
            add("frame.edge", "the edge says no height: give `height` (all four sides) or one of `north`, `east`, "
                "`south`, `west`, or remove `edge`");
        }
    }

    const YAML::Node entries = childOf(frame, "rim");

    for (size_t index = 0; entries.IsDefined() && entries.IsSequence() && index < entries.size(); ++index)
    {
        const YAML::Node node = entries[index];
        const std::string path = "frame.rim[" + std::to_string(index) + "]";
        const std::string form = textOf(node, "form");
        const bool hasWords = childOf(node, "height").IsDefined() || childOf(node, "floor").IsDefined()
            || childOf(node, "crest").IsDefined() || childOf(node, "roughness").IsDefined()
            || childOf(node, "seed").IsDefined() || childOf(node, "meet").IsDefined();

        if (childOf(node, "depth").IsDefined())
        {
            warnings.push_back("sketch.yml " + path + ".depth is retired and not read: a rim strip reaches from the "
                "playable square's edge to the map's edge; remove `depth`");
        }

        if (form.empty())
        {
            // A strip that only names its plan space: a note for a reader, not land.
            if (hasWords)
            {
                add(path, "the rim entry gives heights and no `form`: add `form: level` (flat ground, a sea, a "
                    "shelf) or `form: ridge` (a chain of mounds)");
            }
            else
            {
                warnings.push_back("sketch.yml " + path + " has no `form`, so it shapes nothing and the heights "
                    "(grid, bands, points) say the land there: give it `form: level` or `form: ridge` with a "
                    "`height`");
            }

            continue;
        }

        OutdoorRimEntry entry;
        entry.space = textOf(node, "space");
        bool usable = true;

        if (!sideOf(textOf(node, "side"), entry.side))
        {
            add(path + ".side", "a rim entry's side is north, east, south or west");
            continue;
        }

        // Each side's mounds and waves differ unless the sketch gives its own seed: 1 north, 2 east, 3 south, 4
        // west.
        entry.seed = static_cast<uint32_t>(entry.side) + 1;

        if (form != "level" && form != "ridge")
        {
            add(path + ".form", "a rim entry's form is `level` (flat ground, a sea, a shelf) or `ridge` (a chain "
                "of mounds that hides the map's edge), not '" + form + "'");
            continue;
        }

        entry.form = form == "ridge" ? OutdoorRimForm::Ridge : OutdoorRimForm::Level;
        const YAML::Node span = childOf(node, "span");

        if (span.IsDefined())
        {
            if (!span.IsSequence() || span.size() != 2 || !numberOf(span[0], entry.spanFrom)
                || !numberOf(span[1], entry.spanTo) || entry.spanFrom >= entry.spanTo || entry.spanFrom < 0.0
                || entry.spanTo > Nodes)
            {
                add(path + ".span", "a rim entry's span is [from, to] along its side in cells, from below to, "
                    "both from 0 to 128 (x for north and south, y for east and west)");
                usable = false;
            }
        }

        const YAML::Node height = childOf(node, "height");

        if (height.IsDefined() && height.IsSequence() && height.size() == 2 && numberOf(height[0], entry.low)
            && numberOf(height[1], entry.high))
        {
            if (entry.low > entry.high)
            {
                add(path + ".height", "the two heights are [low, high]: swap " + formatNumber(entry.low) + " and "
                    + formatNumber(entry.high));
                usable = false;
            }
        }
        else if (height.IsDefined() && numberOf(height, entry.low))
        {
            entry.high = entry.low;

            if (entry.form == OutdoorRimForm::Ridge)
            {
                add(path + ".height", "a ridge needs two heights, [low, high]: the height of its crest between "
                    "the mounds and the height of its highest tops (Harmondale's north ridge: [2200, 3900])");
                usable = false;
            }
        }
        else
        {
            add(path + ".height", entry.form == OutdoorRimForm::Ridge
                ? "a ridge needs `height: [low, high]`: the height of its crest between the mounds and the height "
                  "of its highest tops"
                : "level ground needs `height`: one number (a sea: the water's level) or [low, high] for a shelf "
                  "that lies between the two");
            usable = false;
        }

        if (usable && (!storable(entry.low) || !storable(entry.high)))
        {
            add(path + ".height", "an outdoor map stores heights from 0 to 8160: the rim's heights must lie in "
                "that range");
            usable = false;
        }

        const std::optional<double> &edgeHeight = rim.edge[static_cast<size_t>(entry.side)];
        entry.floor = edgeHeight ? *edgeHeight : 0.0;
        const YAML::Node floor = childOf(node, "floor");
        const YAML::Node crest = childOf(node, "crest");
        const YAML::Node meet = childOf(node, "meet");

        if (entry.form == OutdoorRimForm::Level)
        {
            if (floor.IsDefined() || crest.IsDefined())
            {
                add(path, "`floor` and `crest` are a ridge's words: remove them, or make this `form: ridge`");
                usable = false;
            }

            if (meet.IsDefined() && (!numberOf(meet, entry.meet) || entry.meet < 1.0 || entry.meet > 12.0))
            {
                add(path + ".meet", "`meet` is how many cells the land takes from the square's edge to the form's "
                    "height: 1 to 12 (4 when left out)");
                usable = false;
            }
        }
        else
        {
            if (meet.IsDefined())
            {
                add(path + ".meet", "`meet` is level ground's word; a ridge's land falls to its `floor` half-way "
                    "to its `crest`: remove `meet`");
                usable = false;
            }

            if (floor.IsDefined() && (!numberOf(floor, entry.floor) || !storable(entry.floor)))
            {
                add(path + ".floor", "a ridge's `floor` is the height of the ground between the square and the "
                    "crest, 0 to 8160");
                usable = false;
            }

            if (crest.IsDefined() && (!numberOf(crest, entry.crest) || entry.crest < 4.0 || entry.crest > 15.0))
            {
                add(path + ".crest", "a ridge's crest stands 4 to 15 cells out from the square (12 when left out): "
                    "the rim is 18 to 19 cells wide and a mound up to 7 in radius");
                usable = false;
            }

            if (usable && entry.low <= entry.floor)
            {
                add(path + ".height", "the ridge's crest (" + formatNumber(entry.low) + ") does not stand above "
                    "its floor (" + formatNumber(entry.floor) + ", from `floor` or from frame.edge): raise the "
                    "first height or lower the floor; for ground without a crest use `form: level`");
                usable = false;
            }
        }

        const YAML::Node roughness = childOf(node, "roughness");

        if (roughness.IsDefined() && (!numberOf(roughness, entry.roughness) || entry.roughness < 0.0
            || entry.roughness > 512.0))
        {
            add(path + ".roughness", "roughness is how far a node stands off the smooth form on average, in map "
                "units: 0 to 512 (Harmondale's ridges 80 to 120, Ravenshore's shelves 50 to 70)");
            usable = false;
        }

        double seed = entry.seed;
        const YAML::Node seedNode = childOf(node, "seed");

        if (seedNode.IsDefined() && (!numberOf(seedNode, seed) || seed < 0.0 || seed > 4294967295.0
            || seed != std::floor(seed)))
        {
            add(path + ".seed", "the seed is a whole number from 0 up");
            usable = false;
        }

        entry.seed = static_cast<uint32_t>(seed);

        for (const OutdoorRimEntry &other : rim.entries)
        {
            if (usable && other.side == entry.side && entry.spanFrom < other.spanTo && other.spanFrom < entry.spanTo)
            {
                add(path + ".span", std::string("two entries shape the ") + sideName(entry.side) + " rim from "
                    + formatNumber(std::max(entry.spanFrom, other.spanFrom)) + " to "
                    + formatNumber(std::min(entry.spanTo, other.spanTo)) + ": give each a `span` of its own so "
                    "that they do not overlap");
                usable = false;
            }
        }

        if (usable)
        {
            rim.entries.push_back(entry);
        }
    }

    if (!rim.shapesAnything())
    {
        return;
    }

    // The valleys: roads (not bridges, not boat routes) and rivers with a point outside the square.
    const auto runsOut = [](const std::vector<Point2> &line)
    {
        return std::any_of(line.begin(), line.end(), [](const Point2 &point)
        {
            return !inSquare(point[0], point[1]);
        });
    };
    const YAML::Node roads = childOf(sketch, "roads");

    for (size_t index = 0; roads.IsDefined() && roads.IsSequence() && index < roads.size(); ++index)
    {
        const YAML::Node road = roads[index];
        OutdoorRimValley valley;

        if (textOf(road, "surface") == "water" || textOf(road, "bridge") == "true"
            || !pointsOf(childOf(road, "line"), valley.line) || valley.line.size() < 2 || !runsOut(valley.line))
        {
            continue;
        }

        const YAML::Node bed = childOf(road, "bed");

        for (size_t point = 0; bed.IsDefined() && bed.IsSequence() && point < bed.size(); ++point)
        {
            double height = 0.0;

            if (numberOf(bed[point], height))
            {
                valley.floor.push_back(height);
            }
        }

        if (valley.floor.size() != valley.line.size())
        {
            valley.floor.clear();
        }

        const std::string width = textOf(road, "width");
        valley.halfWidth = width == "high_road" ? 1.0 : (width == "lane" ? 0.25 : 0.5);
        rim.valleys.push_back(valley);
    }

    const YAML::Node rivers = childOf(childOf(sketch, "water"), "rivers");

    for (size_t index = 0; rivers.IsDefined() && rivers.IsSequence() && index < rivers.size(); ++index)
    {
        const YAML::Node river = rivers[index];
        OutdoorRimValley valley;
        double width = 1.0;
        double level = 0.0;

        if (!pointsOf(childOf(river, "line"), valley.line) || valley.line.size() < 2 || !runsOut(valley.line))
        {
            continue;
        }

        numberOf(childOf(river, "width_cells"), width);
        valley.halfWidth = std::max(0.5, width * 0.5);

        if (numberOf(childOf(river, "level"), level))
        {
            valley.floor.assign(valley.line.size(), level);
        }

        rim.valleys.push_back(valley);
    }
}

void shapeOutdoorRim(const OutdoorRim &rim, std::vector<double> &base, std::vector<uint8_t> *pShaped)
{
    if (pShaped != nullptr)
    {
        pShaped->clear();
    }

    if (!rim.shapesAnything() || base.size() != static_cast<size_t>(Nodes) * Nodes)
    {
        return;
    }

    if (pShaped != nullptr)
    {
        pShaped->assign(base.size(), 0);
    }

    const std::vector<double> before = base;

    // The land at the square's edge nearest a node, evened over five nodes along the edge.
    const auto edgeLand = [&before](int x, int y)
    {
        const int nearX = std::clamp(x, First, Last);
        const int nearY = std::clamp(y, First, Last);
        const bool alongX = (nearY == First || nearY == Last) && nearX > First && nearX < Last;
        const bool alongY = (nearX == First || nearX == Last) && nearY > First && nearY < Last;
        double sum = 0.0;

        for (int offset = -2; offset <= 2; ++offset)
        {
            const int sampleX = alongX ? std::clamp(nearX + offset, First, Last) : nearX;
            const int sampleY = alongY ? std::clamp(nearY + offset, First, Last) : nearY;
            sum += before[static_cast<size_t>(sampleY) * Nodes + sampleX];
        }

        return sum / 5.0;
    };

    // Each valley's way through the rim, every quarter cell, with the floor's height there: the road's bed or the
    // river's level, else the land where the line leaves the square, carried out level.
    std::vector<std::vector<ValleyPoint>> valleyPoints;

    for (const OutdoorRimValley &valley : rim.valleys)
    {
        std::vector<ValleyPoint> points;
        std::optional<double> leaving;

        for (size_t point = 0; point + 1 < valley.line.size(); ++point)
        {
            const Point2 &from = valley.line[point];
            const Point2 &to = valley.line[point + 1];
            const double length = oy::hypot(to[0] - from[0], to[1] - from[1]);
            const int steps = std::max(1, static_cast<int>(std::ceil(length / ValleyStepCells)));

            for (int step = 0; step <= steps; ++step)
            {
                const double share = static_cast<double>(step) / steps;
                const double atX = from[0] + (to[0] - from[0]) * share;
                const double atY = from[1] + (to[1] - from[1]) * share;

                if (inSquare(atX, atY))
                {
                    leaving = fieldAt(before, atX, atY);
                    continue;
                }

                double floor = 0.0;

                if (!valley.floor.empty())
                {
                    floor = valley.floor[point] + (valley.floor[point + 1] - valley.floor[point]) * share;
                }
                else
                {
                    if (!leaving)
                    {
                        leaving = fieldAt(before, std::clamp(atX, static_cast<double>(First),
                            static_cast<double>(Last)), std::clamp(atY, static_cast<double>(First),
                            static_cast<double>(Last)));
                    }

                    floor = *leaving;
                }

                points.push_back({atX, atY, floor});
            }
        }

        valleyPoints.push_back(points);
    }

    for (int y = 0; y < Nodes; ++y)
    {
        for (int x = 0; x < Nodes; ++x)
        {
            if (inSquare(x, y))
            {
                continue;
            }

            const size_t node = static_cast<size_t>(y) * Nodes + x;
            int out = 0;

            for (const OutdoorRimSide side : {OutdoorRimSide::North, OutdoorRimSide::East, OutdoorRimSide::South,
                     OutdoorRimSide::West})
            {
                out = std::max(out, outdoorRimDistance(side, x, y));
            }

            const double land = edgeLand(x, y);
            double weightSum = 0.0;
            double heightSum = 0.0;

            for (size_t index = 0; index < rim.entries.size(); ++index)
            {
                const OutdoorRimEntry &entry = rim.entries[index];
                const int own = outdoorRimDistance(entry.side, x, y);

                if (own <= 0)
                {
                    continue;
                }

                const bool alongX = entry.side == OutdoorRimSide::North || entry.side == OutdoorRimSide::South;
                const double along = alongX ? x : y;
                const double past = std::max({entry.spanFrom - along, along - entry.spanTo, 0.0});
                const double weight = ease(1.0 - (out - own) / JoinCells) * ease(1.0 - past / JoinCells);

                if (weight <= 0.0)
                {
                    continue;
                }

                // Roughness: most nodes by little, a few by much.
                const double spread = chance(entry.seed, x, y, 5) * 2.0 - 1.0;
                const double rough = entry.roughness * RoughnessScale * spread * std::fabs(spread);
                double height = 0.0;

                if (entry.form == OutdoorRimForm::Level)
                {
                    const double target = entry.low + (entry.high - entry.low)
                        * wave(entry.seed, x, y, ShelfWaveCells);
                    const double share = ease(own / entry.meet);
                    height = land + (target - land) * share + rough * share;
                }
                else
                {
                    const double trough = entry.crest * 0.5;
                    const double depth = stripDepth(entry.side);
                    // The land falls to the floor on the way to the crest, and never rises to it; the ridge's bank
                    // stands on that ground, its top rising and falling along the side.
                    const double ground = land > entry.floor
                        ? land + (entry.floor - land) * ease(own / trough) : land;
                    const RidgeAt ridge = ridgeAt(entry, along);
                    height = ground + std::max(0.0, ridge.top - ground)
                        * bell(std::fabs(own - ridge.crest) / ridge.halfWidth);
                    height += rough * std::clamp((height - ground) / 512.0, 0.0, 1.0);
                    // Behind the crest everything falls to the map's edge.
                    const std::optional<double> &edge = rim.edge[static_cast<size_t>(entry.side)];
                    const double last = edge ? *edge : entry.floor;
                    const double fallFrom = ridge.crest + 1.0;
                    height += (last - height) * ease((own - fallFrom) / std::max(1.0, depth - fallFrom));
                }

                weightSum += weight;
                heightSum += weight * height;
            }

            double height = before[node];

            if (weightSum > 0.0)
            {
                double form = heightSum / weightSum;

                // Valleys: the floor along a road or a river, the form closing in beside it. Only the line's way
                // through the rim counts: a road along the inside of the square's edge opens no valley.
                for (size_t valleyIndex = 0; valleyIndex < rim.valleys.size(); ++valleyIndex)
                {
                    const OutdoorRimValley &valley = rim.valleys[valleyIndex];
                    double nearest = std::numeric_limits<double>::infinity();
                    double floor = 0.0;

                    for (const ValleyPoint &point : valleyPoints[valleyIndex])
                    {
                        const double distance = oy::hypot(x - point.x, y - point.y);

                        if (distance < nearest)
                        {
                            nearest = distance;
                            floor = point.floor;
                        }
                    }

                    const double open = ease((nearest - valley.halfWidth - ValleyFloorCells) / ValleyWallCells);

                    if (open < 1.0)
                    {
                        form = floor + (form - floor) * open;
                    }
                }

                const double cover = std::min(1.0, weightSum);
                height = before[node] + (form - before[node]) * cover;

                if (pShaped != nullptr)
                {
                    (*pShaped)[node] = 1;
                }
            }

            base[node] = height;
        }
    }

    holdOutdoorRimEdge(rim, base);
}

void holdOutdoorRimEdge(const OutdoorRim &rim, std::vector<double> &field)
{
    if (field.size() != static_cast<size_t>(Nodes) * Nodes)
    {
        return;
    }

    for (int y = 0; y < Nodes; ++y)
    {
        for (int x = 0; x < Nodes; ++x)
        {
            double edgeSum = 0.0;
            int edgeCount = 0;

            for (const OutdoorRimSide side : {OutdoorRimSide::North, OutdoorRimSide::East, OutdoorRimSide::South,
                     OutdoorRimSide::West})
            {
                const std::optional<double> &edge = rim.edge[static_cast<size_t>(side)];

                if (edge && outdoorRimDistance(side, x, y) == stripDepth(side))
                {
                    edgeSum += *edge;
                    ++edgeCount;
                }
            }

            if (edgeCount != 0)
            {
                field[static_cast<size_t>(y) * Nodes + x] = edgeSum / edgeCount;
            }
        }
    }
}
}
