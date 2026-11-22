#include "core/OutdoorLowering.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/OutdoorRim.h"
#include "core/Polygon.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstdio>
#include <memory>
#include <set>
#include <functional>
#include <limits>
#include <map>
#include <queue>

// How a sketch becomes land, in plain words.
//
// The land is a field of heights on the sketch's grid nodes: 128 x 128 of them, 512 units apart, node [x, y] at the
// north-west corner of cell [x, y]. Nothing here is random: the same sketch always gives the same bytes.
//
// 1. A base level for every node. With a grid in the sketch, the base is the grid read between its samples: each
//    sample is a spot height at the middle of its block, and the land runs through the samples as rounded ground
//    (a curve along each row of samples, then through the rows, never above or below the two samples it runs
//    between). Measured on Ravenshore and Harmondale, a grid of step 4 read so puts 91 and 83 of 100 nodes within
//    256 units of the original. Without a grid, a node takes the middle of the range of the height band whose
//    outline it stands in (the first that contains it; outside every outline, the nearest one).
//
// 1a. The rim. Beyond the square the party walks (nodes 19 to 109), the base is the rim's where `frame.rim`
//    describes it with a form (level ground, a shelf, a ridge of mounds), from the land at the square's edge out,
//    with valleys kept open where roads and rivers run out, and `frame.edge` holds the outermost row
//    (core/OutdoorRim, where the shipped maps' rims are measured). Inside the square nothing changes. Everything
//    below then works on the rim as on the rest.
//
// 2. Cliffs cut the grid. Two neighbouring nodes (also diagonal ones) whose joining line crosses a cliff line are
//    no longer neighbours. A node standing exactly on a cliff line belongs to the high side: the line is the
//    cliff's top edge, and the node takes its base level from that side (of a grid: from the samples the cliff
//    does not hide from it). The low side is the cliff's `down`;
//    where the sketch leaves it out, a first rough pass of the heights tells which side comes out lower.
//    A cliff's `drop` is measured from its top: where the land at a
//    cliff's foot would fall by less than three quarters of the drop (a pass cut through high ground between two
//    cliff lines), the nodes at the foot are set `drop` below the top, never below the lowest height the sketch
//    names. A break that still comes out at less than half its
//    drop is a warning. A height point drawn on a cliff line with the height of the land at the foot (lower than the
//    top there) is taken one node to the low side; one that raises the line's node stays on it.
//
// 3. Distances go round cliffs. The distance from a height point (or from water) to a node is the shortest way
//    over neighbouring nodes that are still joined, so a point at a cliff's foot does not pull the top, and its
//    pull fades smoothly round the end of a cliff line.
//
// 4. Height points. Over a grid a point corrects the grid where it stands: its difference from the grid's surface
//    there, fading to nothing one grid step away (where the fades of several points overlap to more than one
//    whole share, a node takes the mean of their corrections, not their sum); water and set cliff feet hold their
//    own nodes and pull nothing (the grid has the banks as they are: on the shipped maps the land stands 160 to
//    640 above the water one node from the shore). Without a grid the points pull the surface: a node's height is a weighted mean of its base
//    (weight 1), of every height point (weight (8 / distance)^2), of the nearest cliff foot set in step 2 and of
//    the nearest water (each with weight (3 / distance)^2; water at its level, so beaches run down to their
//    water). At a point's own node the height is the point's height.
//
// 5. Water lies on the corners of cells, as the tiles show it (core/OutdoorGround). A corner inside a water body's
//    outline or on it, or within half a river's width of its centre line (never less than one cell), is water.
//    What the tiles cannot show is cleared: water narrower than one cell, and cells with water on two opposite
//    corners only. A cell with all four corners in water is open water; a cell with some is shore. Every corner
//    of both lies at the water's level, so the corners round the water are a level beach, as on the shipped maps.
//    A cell with a cliff between its middle and one of its corners is the cliff's face: the water draws back from
//    it. Water without a `level` takes it from the land
//    the other layers give: a body lies at the lowest ground under it, a river follows the ground down its line
//    and never rises again. Under water the ground lies OutdoorWaterBedDepth below the surface.
//
// 6. Smoothing, without a grid only: six times, every node that is not
//    fixed (a height point, a water corner, a set cliff foot) takes the mean of itself and its four neighbours it
//    is still joined to. This rounds the steps between bands into slopes and never reaches across a cliff.
//
// 6r. Rough areas and ridges (`heights.rough`, `heights.ridges`), on the land the steps above made. In a rough area
//    every node not held by water, a height point, a cliff's foot or a rim form moves up or down by chance (most by
//    little, a few by more; node by node or in bumps of `scale` cells), fading over two cells at the outline: the
//    shipped maps' walkable ground stands 22 to 28 off the mean of its neighbours, a grid read smoothly about 21.
//    A ridge is a line of nodes set to its height (`width` nodes across), its sides running back into the land over
//    `slope` cells (0: upright): the narrow dykes, ledges and channels one node wide that a grid of spot heights
//    cannot hold (Harmondale's 640 ridges on its basin floor). A terrace (`heights.terraces`) then sets every node in
//    or on its outline to its height (with `steps`, nested rings `in` cells inside the outline at their own heights:
//    a stepped hill or pit), the land outside running back over `slope` cells. A cut (`heights.cuts`) then sets the
//    nodes inside its outline to its floor and leaves those on it at the land's height, so each wall is a one-node
//    cliff as high as the land there (Blackshire's trench, Free Haven's slots); an `open` edge goes to the floor
//    and the land beyond it runs down to it. Ramps (`ramps` of a terrace or a cut) are then laid as ridges without
//    sides across the steps, their ends at the land's height where no height is given. Last, peak fields
//    (`heights.peaks`: a count of peaks at places the seed picks, only ever raising the land) and spires
//    (`heights.spires`: one or two nodes set to a height, the neighbours untouched: Mount Nighon's needles), and
//    after everything blocks of nodes given one by one (`heights.nodes`). The last is for sheer land: Erathia's
//    mountains fall 1200 and more between two neighbouring nodes, node after node. Measured on it (2026-11-14), a grid
//    of step 4 read with every such break cut exactly still leaves those nodes 484 off on average (497 as built),
//    and one of step 2 389: the samples do not hold land that changes from node to node; and height points set there
//    are overwritten by the ridges, terraces and peaks laid after them (280 of 739) or moved off cliff lines (65).
//    A ridge with `closed` runs back to its first point (a crater's rim). Water keeps its level.
//    Roads and plots come after.
//
// 6a. Roads. A road is one cell wide and lies level across its width, as on the shipped maps (the median road
//    cell of Ravenshore and Harmondale rises 0 from corner to corner): each of its cells takes one height, the
//    land's along the road averaged over five cells or the sketch's `bed`, and a node takes the mean of the road
//    cells that meet at it. The banks beside the road are left as they are.
//
// 6b. Buildings. The ground under a building's plot is made level at the mean of the land there, and the building
//    stands on it (core/OutdoorBuildings).
//
// 6c. Ways in. The land under a cave mouth or a hatch is set to its shell: the floor under the mouth and the front,
//    the back row at the crest, the nodes under the shell below it (core/OutdoorWaysIn).
//
// 7. What an ODM stores. One byte per node in steps of 32 units from 0 (the plan's datum) to 8160. Heights are
//    rounded to the nearest step; a height outside the range is clamped and counted in a warning. An ODM has no
//    water surface: water is a tile on the terrain, so the corners of water and shore cells store the water's
//    level and the game sinks the bed under it itself. A cliff shows as the steepest thing the format has: the
//    whole break within one cell.
//
// 8. The ground: the tiles of the cells, from the sketch's ground zones, the water and the roads
//    (core/OutdoorGround).

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Nodes = OutdoorNodeCount;
constexpr size_t NodeTotal = static_cast<size_t>(Nodes) * Nodes;
constexpr size_t GroundNodeTotal = static_cast<size_t>(OutdoorGroundNodes) * OutdoorGroundNodes;
constexpr double PointPullCells = 8.0;
// Over a grid a height point reaches this share of the grid's step, in cells.
constexpr double GridPointReachShare = 1.0;
// A cliff's foot is set from its top where the break would be less than this share of the drop.
constexpr double CliffFootShare = 0.75;
constexpr double ShorePullCells = 3.0;
constexpr int SmoothingPasses = 6;
// A rough area's moves fade to nothing over this many cells inside its outline.
constexpr double RoughFadeCells = 2.0;
// Over bumps of more than a cell, a value from the smooth field of chance (mostly near its middle) is stretched by
// this much so that a node is moved about `amount` on average.
constexpr double RoughWaveScale = 2.5;
// A road's bed takes the land's height along the road averaged over this many cells to each side.
constexpr size_t RoadEaseCells = 2;
// A grid is read smoothly between its samples already: its land is not smoothed again.
constexpr int GridSmoothingPasses = 0;
// How far a cliff line is moved toward its low side, in cells, so that no node stands on it. Nodes and cell
// middles are at least 1 / 362 of a cell away from any line through whole-cell points that they are not on.
constexpr double CliffShift = 1.0e-3;
// How far a moved cliff line runs on past its two ends, in cells, so that no link slips between the ends of two
// cliffs that meet at a node.
constexpr double CliffEndReach = 1.0e-2;
constexpr double Unknown = std::numeric_limits<double>::quiet_NaN();
constexpr double Far = std::numeric_limits<double>::infinity();
// A sculpt patch on described land (heights.patches): at most this many cells across each way, and this many.
constexpr int SculptPatchCells = 32;
constexpr size_t SculptPatchCount = 16;
constexpr int DirectionX[8] = {1, 1, 0, -1, -1, -1, 0, 1};
constexpr int DirectionY[8] = {0, 1, 1, 1, 0, -1, -1, -1};
const char *SketchFile = "sketch.yml";

struct Segment
{
    Point2 first;
    Point2 second;
};

struct HeightPoint
{
    int node = 0;
    double height = 0.0;
};

struct Band
{
    std::vector<Point2> polygon;
    double level = 0.0;
};

struct Cliff
{
    std::vector<Point2> line;
    double drop = 0.0;
    // Which side is low, walking the line from its first point: -1 left, 1 right, 0 not known.
    int down = 0;
};

// A line of nodes the land is set to (heights.ridges): a dyke, a narrow ridge, a ledge or a channel.
struct Ridge
{
    std::vector<Point2> line;
    // The height at each point of the line, map units.
    std::vector<double> heights;
    double width = 1.0;
    double slope = 0.0;
};

// A level terrace (heights.terraces): the nodes in and on its outline at one height, the land outside running back
// over `slope` cells (Harmondale's town terraces at 640, 288 and 480).
struct Terrace
{
    std::vector<Point2> polygon;
    double height = 0.0;
    double slope = 0.0;
    // `steps`: nested level rings inside the outline, each [in, height]: the nodes at least `in` cells inside the
    // outline take that height (Castle Ironfist's pit: rings two nodes wide at 1856, 1248, 640 and a floor at 0).
    std::vector<std::array<double, 2>> steps;
};

// A hollow cut into the land (heights.cuts): the nodes inside its outline at `floor`, the nodes on it keeping the
// land's height so that each wall is a one-node cliff as high as the land there; an `open` edge's nodes go to the
// floor too and the land beyond it runs down to the floor over `slope` cells (the way in).
struct Cut
{
    std::vector<Point2> polygon;
    double floor = 0.0;
    std::vector<bool> open;
    double slope = 3.0;
};

// A one- or two-node needle (heights.spires): its nodes set to `height`, the neighbours untouched.
struct Spire
{
    Point2 at = {0.0, 0.0};
    double height = 0.0;
    int width = 1;
};

// A block of nodes given one by one (heights.nodes): sheer land whose falls lie between two neighbouring nodes, which
// no coarser word holds (Erathia's mountains beside drops of 1200 and more). A value left empty keeps the land the
// other words made.
struct NodeBlock
{
    int x = 0;
    int y = 0;
    std::vector<std::vector<double>> rows;
};

// An area filled with peaks (heights.peaks): `count` of them at places chosen by the seed, each with a top `width`
// nodes across at a height from the range (or that far over the land with `rise`), its sides running down to the land
// over its base radius as `profile` says.
struct PeakField
{
    std::vector<Point2> polygon;
    int count = 0;
    std::array<double, 2> height = {0.0, 0.0};
    bool rise = false;
    std::array<double, 2> radius = {0.0, 0.0};
    // needle (the top only, sheer), cone (straight sides) or round (rounded sides).
    std::string profile = "cone";
    int width = 1;
    double spacing = 2.0;
    uint32_t seed = 1;
};

// An area whose ground is made rougher (heights.rough).
struct RoughArea
{
    std::vector<Point2> polygon;
    double amount = 0.0;
    double scale = 1.0;
    uint32_t seed = 1;
};

struct WaterShape
{
    std::string id;
    bool river = false;
    // The outline of a body or the centre line of a river.
    std::vector<Point2> points;
    double width = 1.0;
    std::optional<double> level;
    // `tile_set`: a liquid laid in one of the map's ground sets instead of its water set.
    std::string tileSet;
};

// Which links between neighbouring nodes cliffs have cut: bit d of a node for its neighbour in direction d.
struct CutMap
{
    std::vector<uint8_t> bits = std::vector<uint8_t>(NodeTotal, 0);
};



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

bool pointOf(const YAML::Node &node, Point2 &point)
{
    return node.IsDefined() && node.IsSequence() && node.size() == 2 && numberOf(node[0], point[0])
        && numberOf(node[1], point[1]);
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

        if (!pointOf(item, point))
        {
            return false;
        }

        points.push_back(point);
    }

    return true;
}

int nodeIndex(int x, int y)
{
    return y * Nodes + x;
}

double orientation(const Point2 &origin, const Point2 &first, const Point2 &second)
{
    return (first[0] - origin[0]) * (second[1] - origin[1]) - (first[1] - origin[1]) * (second[0] - origin[0]);
}

// Whether the line from `from` to `to` crosses the segment: its two ends lie strictly on the two sides of the
// segment, and it passes between the segment's ends or exactly through one of them (so a link through the corner
// of a cliff line crosses the line). With `touching`, meeting the segment at any point counts.
bool crosses(const Point2 &from, const Point2 &to, const Segment &segment, bool touching)
{
    if (std::max(from[0], to[0]) < std::min(segment.first[0], segment.second[0])
        || std::min(from[0], to[0]) > std::max(segment.first[0], segment.second[0])
        || std::max(from[1], to[1]) < std::min(segment.first[1], segment.second[1])
        || std::min(from[1], to[1]) > std::max(segment.first[1], segment.second[1]))
    {
        return false;
    }

    const double d1 = orientation(segment.first, segment.second, from);
    const double d2 = orientation(segment.first, segment.second, to);
    const double d3 = orientation(from, to, segment.first);
    const double d4 = orientation(from, to, segment.second);

    if (((d1 > 0.0 && d2 < 0.0) || (d1 < 0.0 && d2 > 0.0)) && d3 * d4 <= 0.0)
    {
        return true;
    }

    // The boxes overlap (tested above), so lines that touch or lie on one another meet.
    return touching && d1 * d2 <= 0.0 && d3 * d4 <= 0.0;
}

bool crossesAny(const Point2 &from, const Point2 &to, const std::vector<Segment> &segments, bool touching)
{
    for (const Segment &segment : segments)
    {
        if (crosses(from, to, segment, touching))
        {
            return true;
        }
    }

    return false;
}

CutMap buildCutMap(const std::vector<Segment> &segments, bool touching)
{
    CutMap cut;

    if (segments.empty())
    {
        return cut;
    }

    for (int y = 0; y < Nodes; ++y)
    {
        for (int x = 0; x < Nodes; ++x)
        {
            for (int direction = 0; direction < 4; ++direction)
            {
                const int otherX = x + DirectionX[direction];
                const int otherY = y + DirectionY[direction];

                if (otherX < 0 || otherX >= Nodes || otherY >= Nodes)
                {
                    continue;
                }

                if (crossesAny({static_cast<double>(x), static_cast<double>(y)},
                        {static_cast<double>(otherX), static_cast<double>(otherY)}, segments, touching))
                {
                    cut.bits[nodeIndex(x, y)] |= static_cast<uint8_t>(1u << direction);
                    cut.bits[nodeIndex(otherX, otherY)] |= static_cast<uint8_t>(1u << (direction + 4));
                }
            }
        }
    }

    return cut;
}

// The shortest way from the nearest source to every node over joined neighbours, in cells; `pNearest` gets the
// source it starts from.
void walkDistances(
    const CutMap &cut,
    const std::vector<int> &sources,
    std::vector<double> &distance,
    std::vector<int> *pNearest)
{
    distance.assign(NodeTotal, Far);

    if (pNearest != nullptr)
    {
        pNearest->assign(NodeTotal, -1);
    }

    using Entry = std::pair<double, int>;
    std::priority_queue<Entry, std::vector<Entry>, std::greater<Entry>> queue;

    for (const int source : sources)
    {
        distance[source] = 0.0;

        if (pNearest != nullptr)
        {
            (*pNearest)[source] = source;
        }

        queue.push({0.0, source});
    }

    while (!queue.empty())
    {
        const Entry entry = queue.top();
        queue.pop();

        if (entry.first > distance[entry.second])
        {
            continue;
        }

        const int x = entry.second % Nodes;
        const int y = entry.second / Nodes;

        for (int direction = 0; direction < 8; ++direction)
        {
            const int otherX = x + DirectionX[direction];
            const int otherY = y + DirectionY[direction];

            if (otherX < 0 || otherX >= Nodes || otherY < 0 || otherY >= Nodes
                || (cut.bits[entry.second] & (1u << direction)) != 0)
            {
                continue;
            }

            const int other = nodeIndex(otherX, otherY);
            const double next = entry.first + ((direction % 2) == 0 ? 1.0 : std::sqrt(2.0));

            if (next < distance[other])
            {
                distance[other] = next;

                if (pNearest != nullptr)
                {
                    (*pNearest)[other] = (*pNearest)[entry.second];
                }

                queue.push({next, other});
            }
        }
    }
}

// Steps 3, 4 and 6 of the algorithm: the base pulled by the height points and the water, then smoothed.
// `waterNode` holds the water's level at the corners of water cells and Unknown elsewhere; `footNode` the height of
// the cliff feet that are set, Unknown elsewhere (or empty: none). `rimShaped`: the nodes frame.rim's forms shaped
// (or empty: none); the smoothing leaves them as they are and does not reach into the square the party walks from
// beyond it, so a rim leaves the square as it is.
std::vector<double> relief(
    const std::vector<double> &base,
    const std::vector<HeightPoint> &points,
    const std::vector<double> &waterNode,
    const std::vector<double> &footNode,
    const CutMap &cut,
    double pointPull,
    int smoothingPasses,
    bool local,
    const std::vector<uint8_t> &rimShaped)
{
    const bool squareApart = !rimShaped.empty();
    const auto inSquare = [](int x, int y)
    {
        return x >= OutdoorPlayableFirstNode && x <= OutdoorPlayableLastNode && y >= OutdoorPlayableFirstNode
            && y <= OutdoorPlayableLastNode;
    };

    std::vector<double> weighted = base;
    std::vector<double> weight(NodeTotal, 1.0);
    std::vector<double> distance;
    // Over a grid, the corrections of points whose reach overlaps do not add up (four points round a peak would
    // raise the land between them above it): where their shares sum to more than 1, a node takes their mean.
    std::vector<double> correction(NodeTotal, 0.0);
    std::vector<double> shares(NodeTotal, 0.0);

    for (const HeightPoint &point : points)
    {
        walkDistances(cut, {point.node}, distance, nullptr);

        // Over a grid a point corrects the grid where it stands: its difference from the grid's surface there,
        // fading to nothing at `pointPull` cells. The grid knows the land beyond.
        const double offset = point.height - base[point.node];

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            if (local)
            {
                if (distance[node] < pointPull)
                {
                    const double share = 1.0 - distance[node] / pointPull;
                    correction[node] += offset * share * share;
                    shares[node] += share * share;
                }
            }
            else if (distance[node] > 0.0 && distance[node] < Far)
            {
                const double pull = (pointPull / distance[node]) * (pointPull / distance[node]);
                weighted[node] += pull * point.height;
                weight[node] += pull;
            }
        }
    }

    for (size_t node = 0; local && node < NodeTotal; ++node)
    {
        weighted[node] += correction[node] / std::max(1.0, shares[node]);
    }

    // The nearest of a set of fixed nodes pulls, not all of them: a long shore is not heavier than a short one.
    const auto pullFromNearest = [&](const std::vector<double> &levels, double reach)
    {
        std::vector<int> sources;

        for (size_t node = 0; node < levels.size(); ++node)
        {
            if (!std::isnan(levels[node]))
            {
                sources.push_back(static_cast<int>(node));
            }
        }

        if (sources.empty())
        {
            return;
        }

        std::vector<int> nearest;
        walkDistances(cut, sources, distance, &nearest);

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            if (distance[node] > 0.0 && distance[node] < Far)
            {
                const double pull = (reach / distance[node]) * (reach / distance[node]);
                weighted[node] += pull * levels[nearest[node]];
                weight[node] += pull;
            }
        }
    };
    // A grid has the banks and the ground at a cliff's foot as they are: the water and the set feet hold their own
    // nodes and pull nothing.
    if (!local)
    {
        pullFromNearest(footNode, ShorePullCells);
        pullFromNearest(waterNode, ShorePullCells);
    }

    std::vector<double> heights(NodeTotal, 0.0);
    std::vector<uint8_t> fixed(NodeTotal, 0);

    for (size_t node = 0; node < NodeTotal; ++node)
    {
        heights[node] = weighted[node] / weight[node];
    }

    for (size_t node = 0; node < footNode.size(); ++node)
    {
        if (!std::isnan(footNode[node]))
        {
            heights[node] = footNode[node];
            fixed[node] = 1;
        }
    }

    for (const HeightPoint &point : points)
    {
        heights[point.node] = point.height;
        fixed[point.node] = 1;
    }

    for (size_t node = 0; node < NodeTotal; ++node)
    {
        if (!std::isnan(waterNode[node]))
        {
            heights[node] = waterNode[node];
            fixed[node] = 1;
        }
    }

    for (size_t node = 0; node < rimShaped.size(); ++node)
    {
        fixed[node] = rimShaped[node] != 0 ? 1 : fixed[node];
    }

    std::vector<double> smoothed = heights;

    for (int pass = 0; pass < smoothingPasses; ++pass)
    {
        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                const int node = nodeIndex(x, y);

                if (fixed[node] != 0)
                {
                    continue;
                }

                double sum = heights[node];
                double count = 1.0;

                for (int direction = 0; direction < 8; direction += 2)
                {
                    const int otherX = x + DirectionX[direction];
                    const int otherY = y + DirectionY[direction];

                    if (otherX >= 0 && otherX < Nodes && otherY >= 0 && otherY < Nodes
                        && (cut.bits[node] & (1u << direction)) == 0
                        && !(squareApart && inSquare(x, y) && !inSquare(otherX, otherY)))
                    {
                        sum += heights[nodeIndex(otherX, otherY)];
                        count += 1.0;
                    }
                }

                smoothed[node] = sum / count;
            }
        }

        heights = smoothed;
    }

    return heights;
}

// A field read between its nodes, weighed by distance; outside the nodes, the nearest edge.
double fieldAt(const std::vector<double> &field, double x, double y)
{
    const double clampedX = std::clamp(x, 0.0, static_cast<double>(Nodes - 1));
    const double clampedY = std::clamp(y, 0.0, static_cast<double>(Nodes - 1));
    const int x0 = std::min(static_cast<int>(std::floor(clampedX)), Nodes - 2);
    const int y0 = std::min(static_cast<int>(std::floor(clampedY)), Nodes - 2);
    const double shareX = clampedX - x0;
    const double shareY = clampedY - y0;
    const double north = field[nodeIndex(x0, y0)] * (1.0 - shareX) + field[nodeIndex(x0 + 1, y0)] * shareX;
    const double south = field[nodeIndex(x0, y0 + 1)] * (1.0 - shareX) + field[nodeIndex(x0 + 1, y0 + 1)] * shareX;
    return north * (1.0 - shareY) + south * shareY;
}

// Even-odd test with half-open edges, so a node on the border of two outlines that share it is in exactly one.
bool insideOutline(const std::vector<Point2> &polygon, const Point2 &point)
{
    bool inside = false;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point2 &first = polygon[index];
        const Point2 &second = polygon[(index + 1) % polygon.size()];

        if ((first[1] > point[1]) != (second[1] > point[1])
            && point[0] < first[0] + (point[1] - first[1]) * (second[0] - first[0]) / (second[1] - first[1]))
        {
            inside = !inside;
        }
    }

    return inside;
}

double segmentDistance(const Point2 &first, const Point2 &second, const Point2 &point, double *pShare = nullptr)
{
    const double dx = second[0] - first[0];
    const double dy = second[1] - first[1];
    const double lengthSquared = dx * dx + dy * dy;
    double share = 0.0;

    if (lengthSquared > 0.0)
    {
        share = std::clamp(((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / lengthSquared, 0.0, 1.0);
    }

    if (pShare != nullptr)
    {
        *pShare = share;
    }

    return oy::hypot(point[0] - first[0] - share * dx, point[1] - first[1] - share * dy);
}

double outlineDistance(const std::vector<Point2> &polygon, const Point2 &point)
{
    double best = Far;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        best = std::min(best, segmentDistance(polygon[index], polygon[(index + 1) % polygon.size()], point));
    }

    return best;
}

// The unit normal of a segment that points to the side `down` names (-1 left, 1 right, walking first to second).
// The sketch's y runs south, so left of east is north.
Point2 sideNormal(const Point2 &first, const Point2 &second, int down)
{
    const double dx = second[0] - first[0];
    const double dy = second[1] - first[1];
    const double length = oy::hypot(dx, dy);

    if (length <= 0.0)
    {
        return {0.0, 0.0};
    }

    const double sign = down < 0 ? 1.0 : -1.0;
    return {sign * dy / length, -sign * dx / length};
}

// A cliff's line moved CliffShift toward its low side, corners kept joined.
std::vector<Segment> shiftedCliff(const Cliff &cliff)
{
    const int down = cliff.down == 0 ? 1 : cliff.down;
    std::vector<Point2> moved;

    for (size_t index = 0; index < cliff.line.size(); ++index)
    {
        Point2 before = {0.0, 0.0};
        Point2 after = {0.0, 0.0};

        if (index > 0)
        {
            before = sideNormal(cliff.line[index - 1], cliff.line[index], down);
        }

        if (index + 1 < cliff.line.size())
        {
            after = sideNormal(cliff.line[index], cliff.line[index + 1], down);
        }

        Point2 shift = index == 0 ? after : (index + 1 == cliff.line.size() ? before : Point2{0.0, 0.0});

        if (index > 0 && index + 1 < cliff.line.size())
        {
            // The mitre of the two neighbouring segments; a hairpin keeps the first segment's side.
            const double dot = before[0] * after[0] + before[1] * after[1];
            const double scale = 1.0 + dot > 0.25 ? 1.0 / (1.0 + dot) : 0.0;
            shift = scale > 0.0 ? Point2{(before[0] + after[0]) * scale, (before[1] + after[1]) * scale} : before;
        }

        moved.push_back({cliff.line[index][0] + shift[0] * CliffShift, cliff.line[index][1] + shift[1] * CliffShift});
    }

    const auto runOn = [](Point2 &end, const Point2 &inner)
    {
        const double length = oy::hypot(end[0] - inner[0], end[1] - inner[1]);

        if (length > 0.0)
        {
            end = {end[0] + (end[0] - inner[0]) / length * CliffEndReach,
                end[1] + (end[1] - inner[1]) / length * CliffEndReach};
        }
    };
    const Point2 second = moved[1];
    const Point2 beforeLast = moved[moved.size() - 2];
    runOn(moved.front(), second);
    runOn(moved.back(), beforeLast);
    std::vector<Segment> segments;

    for (size_t index = 0; index + 1 < moved.size(); ++index)
    {
        segments.push_back({moved[index], moved[index + 1]});
    }

    return segments;
}

int facingUnits(const std::string &facing)
{
    static const std::map<std::string, int> Units = {{"e", 0}, {"ne", 256}, {"n", 512}, {"nw", 768}, {"w", 1024},
        {"sw", 1280}, {"s", 1536}, {"se", 1792}};
    const std::map<std::string, int>::const_iterator found = Units.find(facing);
    return found == Units.end() ? 0 : found->second;
}

std::string cellText(double x, double y)
{
    return "[" + formatNumber(x) + ", " + formatNumber(y) + "]";
}

// What the land words made, up to the peaks (S5_BROWSER_EDITOR.md 2.4.3, "Outdoors, the land is kept"): everything
// the lowering knows after raisePeaks that the structures, roads, node blocks and strokes do not change, so that a
// lowering of the same land words starts from it.
struct KeptLandState
{
    std::vector<Band> bands;
    std::vector<HeightPoint> points;
    std::vector<Cliff> cliffs;
    std::vector<Ridge> ridges;
    std::vector<Terrace> terraces;
    std::vector<Cut> cuts;
    std::vector<Ridge> ramps;
    std::vector<Spire> spires;
    std::vector<PeakField> peaks;
    std::vector<RoughArea> rough;
    std::vector<WaterShape> water;
    bool hasGrid = false;
    int gridStep = 0;
    int gridSide = 0;
    std::vector<double> gridValues;
    double pointPull = 0.0;
    int smoothingPasses = 0;
    OutdoorRim rim;
    std::vector<uint8_t> rimShaped;
    std::vector<double> base;
    std::vector<Segment> cliffSegments;
    std::map<int, Point2> cliffTopNodes;
    CutMap cut;
    std::vector<int> waterNodeShape;
    std::vector<int> cellShape;
    std::vector<uint8_t> cellCorners;
    std::vector<double> cellLevel;
    // The map as lowered so far (ground, water), the per-node water level and the cliffs' feet.
    LoweredOutdoorMap lowered;
    std::vector<double> waterNode;
    std::vector<double> feet;
    // The warnings the land words gave: while reading them (before the structures are read), and while lowering.
    std::vector<std::string> readWarnings;
    std::vector<std::string> landWarnings;
};

// A fast hash of a tree: its structure, keys, tags and scalars in document order.
void hashLandNode(const YAML::Node &node, uint64_t &hash)
{
    const auto mix = [&hash](const std::string &text)
    {
        for (const char character : text)
        {
            hash = (hash ^ static_cast<unsigned char>(character)) * 1099511628211ull;
        }

        hash = (hash ^ 0xffu) * 1099511628211ull;
    };

    if (!node.IsDefined())
    {
        mix("U");
    }
    else if (node.IsMap())
    {
        mix("M");

        for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
        {
            // A sub-object's key names it for the studio; the land never reads it (keys written into a file by the
            // core's first write would otherwise lower the land again).
            if (entry->first.Scalar() == "key")
            {
                continue;
            }

            mix(entry->first.Scalar());
            hashLandNode(entry->second, hash);
        }

        mix("m");
    }
    else if (node.IsSequence())
    {
        mix("S");

        for (const YAML::Node &item : node)
        {
            hashLandNode(item, hash);
        }

        mix("s");
    }
    else if (node.IsScalar())
    {
        mix("V" + node.Tag());
        mix(node.Scalar());
    }
    else
    {
        mix("N");
    }
}
}

// The land words of a project: what the lowering reads up to the peaks. The sketch's grid, frame (with the rim, which
// reads the roads that run out to the edge: the roads too when it has rim strips), water and heights without the
// words applied after the kept land (nodes, strokes, smooth, patches, hand_made) and without notes; and plan.yml's
// height bands. Checked by the read record in the unit suite.
struct OutdoorLandCache::Kept
{
    std::string key;
    KeptLandState state;
};

std::string outdoorLandKey(const Project &project)
{
    const YAML::Node sketch = project.document(SketchFile);
    const YAML::Node plan = project.document("plan.yml");
    uint64_t hash = 1469598103934665603ull;
    hashLandNode(childOf(plan, "height_bands"), hash);

    for (const char *pWord : {"grid", "map_cells", "frame", "water"})
    {
        hashLandNode(childOf(sketch, pWord), hash);
    }

    // The rim (strips, or the edge's heights) reads the roads that run out of the playable square: its valleys.
    const YAML::Node frame = childOf(sketch, "frame");
    const YAML::Node rim = childOf(frame, "rim");
    const YAML::Node roads = childOf(sketch, "roads");

    if (((rim.IsDefined() && rim.IsSequence() && rim.size() > 0) || childOf(frame, "edge").IsDefined())
        && roads.IsDefined() && roads.IsSequence())
    {
        for (const YAML::Node &road : roads)
        {
            std::vector<Point2> line;
            const bool runsOut = !pointsOf(childOf(road, "line"), line)
                || std::any_of(line.begin(), line.end(), [](const Point2 &point)
                {
                    return point[0] < OutdoorPlayableFirstNode || point[0] > OutdoorPlayableLastNode
                        || point[1] < OutdoorPlayableFirstNode || point[1] > OutdoorPlayableLastNode;
                });

            if (runsOut)
            {
                hashLandNode(road, hash);
            }
        }
    }

    const YAML::Node heights = childOf(sketch, "heights");

    if (heights.IsDefined() && heights.IsMap())
    {
        for (YAML::const_iterator entry = heights.begin(); entry != heights.end(); ++entry)
        {
            static const std::set<std::string> after = {"nodes", "strokes", "smooth", "patches", "hand_made", "notes"};

            if (!after.contains(entry->first.Scalar()))
            {
                hashLandNode(YAML::Node(entry->first), hash);
                hashLandNode(entry->second, hash);
            }
        }
    }
    else
    {
        hashLandNode(heights, hash);
    }

    char text[17];
    std::snprintf(text, sizeof(text), "%016llx", static_cast<unsigned long long>(hash));
    return text;
}

namespace
{
class Lowerer
{
public:
    Lowerer(const Project &project, LoweredOutdoorMap &lowered, std::vector<ProjectIssue> &issues,
        OutdoorLandCache *pLand, const std::string &styleWorld = std::string())
        : m_styleWorld(styleWorld)
        , m_project(project)
        , m_lowered(lowered)
        , m_issues(issues)
        , m_plan(project.document("plan.yml"))
        , m_sketch(project.document(SketchFile))
        , m_pLand(pLand)
    {
    }

    void useDoorPictures(const OutdoorDoorPictures *pDoorPictures)
    {
        m_pDoorPictures = pDoorPictures;
    }

    bool run()
    {
        const size_t issuesBefore = m_issues.size();
        const YAML::Node card = m_project.document("project.yml");
        m_lowered = {};
        m_lowered.mapStem = textOf(card, "id");
        m_lowered.world = textOf(card, "world");
        m_lowered.styleWorld = m_styleWorld.empty() ? m_lowered.world : m_styleWorld;
        std::transform(m_lowered.mapStem.begin(), m_lowered.mapStem.end(), m_lowered.mapStem.begin(),
            [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            });

        if (!m_sketch.IsDefined() || !m_sketch.IsMap())
        {
            issue("", "an outdoor map is built from its sketch: the project has no sketch.yml", "project");
            return false;
        }

        // The land up to the peaks, kept from an earlier lowering of the same land words (OutdoorLandCache).
        const std::string landKey = m_pLand != nullptr ? outdoorLandKey(m_project) : std::string();
        const std::shared_ptr<const OutdoorLandCache::Kept> kept =
            m_pLand != nullptr && m_pLand->kept && m_pLand->kept->key == landKey ? m_pLand->kept : nullptr;
        const size_t issuesBeforeLand = m_issues.size();

        if (kept)
        {
            restoreLand(kept->state);
            m_lowered.warnings = kept->state.readWarnings;
            readNodeBlocks(childOf(childOf(m_sketch, "heights"), "nodes"));
            ++m_pLand->hits;
        }
        else
        {
            readHeights();
            readWater();
            readNodeBlocks(childOf(childOf(m_sketch, "heights"), "nodes"));
            m_pLand != nullptr ? ++m_pLand->misses : 0;
        }

        readSculpt();
        const std::vector<std::string> readWarnings = m_lowered.warnings;
        const bool landReadClean = m_issues.size() == issuesBeforeLand;
        m_lowered.roads = rasterizeOutdoorRoads(m_project, m_issues, m_lowered.warnings);
        m_lowered.doorPictures = m_pDoorPictures != nullptr ? *m_pDoorPictures : OutdoorDoorPictures();
        m_lowered.buildings = readOutdoorBuildings(m_project, m_lowered.styleWorld, m_issues, m_lowered.warnings,
            &m_lowered.doorPictures);
        m_lowered.caves = readOutdoorCaves(m_project, m_lowered.styleWorld, m_issues);
        m_lowered.falls = readOutdoorFalls(m_project, m_lowered.styleWorld, m_issues);

        if (m_issues.size() != issuesBefore)
        {
            return false;
        }

        if (m_bands.empty() && !m_hasGrid && m_points.empty())
        {
            issue("heights", "the sketch says nothing of the land's height: give heights.bands, heights.points or "
                "heights.grid", "heights");
            return false;
        }

        if (m_bands.empty() && !m_hasGrid)
        {
            m_lowered.warnings.push_back("heights: no bands and no grid, so the land beyond the pull of the height "
                "points lies at the datum (0)");
        }

        std::vector<double> waterNode;
        std::vector<double> feet;

        if (kept)
        {
            m_lowered.ground = kept->state.lowered.ground;
            m_lowered.warnings.insert(m_lowered.warnings.end(), kept->state.landWarnings.begin(),
                kept->state.landWarnings.end());
            waterNode = kept->state.waterNode;
            feet = kept->state.feet;
        }
        else
        {
            const size_t warningsBeforeLand = m_lowered.warnings.size();
            const size_t issuesBeforeSteps = m_issues.size();
            lowerLand(waterNode, feet);

            if (m_pLand != nullptr && landReadClean && m_issues.size() == issuesBeforeSteps)
            {
                std::shared_ptr<OutdoorLandCache::Kept> made = std::make_shared<OutdoorLandCache::Kept>();
                made->key = landKey;
                saveLand(made->state);
                made->state.lowered = m_lowered;
                made->state.waterNode = waterNode;
                made->state.feet = feet;
                made->state.readWarnings = readWarnings;
                made->state.landWarnings.assign(m_lowered.warnings.begin()
                    + static_cast<std::ptrdiff_t>(warningsBeforeLand), m_lowered.warnings.end());
                m_pLand->kept = made;
            }
        }

        // The words applied over the kept land: a person's strokes (differences), smoothed areas, then the node
        // blocks (absolute, last).
        applyStrokes(waterNode);
        smoothAreas(waterNode);
        setNodeBlocks(waterNode);
        finishLand(waterNode, feet);
        return m_issues.size() == issuesBefore;
    }

    // The land words alone, up to the peaks (for the read record's check of outdoorLandKey).
    void runLandOnly()
    {
        readHeights();
        readWater();

        if (!m_issues.empty())
        {
            return;
        }

        std::vector<double> waterNode;
        std::vector<double> feet;
        lowerLand(waterNode, feet);
    }

private:
    // The land words up to the peaks: the base heights and cliffs, water, smoothing, rough areas, ridges,
    // terraces, cuts, ramps and peaks (kept by OutdoorLandCache).
    void lowerLand(std::vector<double> &waterNode, std::vector<double> &feet)
    {
        computeBase();
        markWaterCells();
        decideCliffSides();

        // The final cuts: every cliff moved off the nodes toward its low side.
        m_cliffSegments.clear();

        for (const Cliff &cliff : m_cliffs)
        {
            const std::vector<Segment> segments = shiftedCliff(cliff);
            m_cliffSegments.insert(m_cliffSegments.end(), segments.begin(), segments.end());
        }

        m_cut = buildCutMap(m_cliffSegments, false);

        if (!m_cliffSegments.empty())
        {
            // Again, now that every cliff has its sides: a node on a cliff line takes the base of the high side.
            findCliffTopNodes();
            computeBase();
        }

        settlePointsOnCliffs();
        dropCliffFaceCells();
        levelOpenWater();
        waterNode = waterNodes();
        m_lowered.ground = relief(m_base, m_points, waterNode, {}, m_cut, m_pointPull, m_smoothingPasses, m_hasGrid,
            m_rimShaped);
        feet = cliffFeet(m_lowered.ground, waterNode);

        if (!feet.empty())
        {
            m_lowered.ground = relief(m_base, m_points, waterNode, feet, m_cut, m_pointPull, m_smoothingPasses,
                m_hasGrid, m_rimShaped);
        }

        // Rough areas, then ridges over everything the heights made so far.
        roughen(waterNode, feet);
        raiseRidges(waterNode);
        levelTerraces(waterNode);
        cutHollows(waterNode);
        layRamps(waterNode);
        raisePeaks(waterNode);
    }

    // After the node blocks: the rim's edge, roads, plots, cave mouths, waterfalls, the stored samples, the start.
    void finishLand(std::vector<double> &waterNode, const std::vector<double> &feet)
    {
        // The map's outermost rows stand where frame.edge says, whatever the smoothing did.
        holdOutdoorRimEdge(m_rim, m_lowered.ground);
        gradeRoads(waterNode, feet);
        levelPlots(waterNode);
        // Step 6c: the land under cave mouths and hatches (core/OutdoorWaysIn).
        shapeOutdoorCaveLand(m_lowered.caves, m_lowered.ground, waterNode, m_lowered.warnings);
        // Step 6d: the land where waterfalls stand (core/OutdoorFalls).
        std::vector<size_t> dried;
        shapeOutdoorFallLand(m_lowered.falls, m_lowered.ground, waterNode, dried, m_lowered.warnings);

        if (!dried.empty())
        {
            // The stream's nodes a fall cut are land now: out of the water's tiles (and what the tiles then cannot
            // show with them), so no water tile slopes down the cut.
            std::vector<uint8_t> wet(GroundNodeTotal, 0);

            for (size_t node = 0; node < GroundNodeTotal; ++node)
            {
                wet[node] = m_waterNode[node] >= 0 ? 1 : 0;
            }

            for (const size_t node : dried)
            {
                wet[(node / Nodes) * OutdoorGroundNodes + node % Nodes] = 0;
            }

            settleWater(wet);
            const std::vector<double> settled = waterNodes();

            for (size_t node = 0; node < NodeTotal; ++node)
            {
                waterNode[node] = std::isnan(waterNode[node]) ? waterNode[node] : settled[node];
            }
        }
        store(waterNode);
        checkCliffs();
        placeStart();
    }

    void saveLand(KeptLandState &state) const
    {
        state.bands = m_bands;
        state.points = m_points;
        state.cliffs = m_cliffs;
        state.ridges = m_ridges;
        state.terraces = m_terraces;
        state.cuts = m_cuts;
        state.ramps = m_ramps;
        state.spires = m_spires;
        state.peaks = m_peaks;
        state.rough = m_rough;
        state.water = m_water;
        state.hasGrid = m_hasGrid;
        state.gridStep = m_gridStep;
        state.gridSide = m_gridSide;
        state.gridValues = m_gridValues;
        state.pointPull = m_pointPull;
        state.smoothingPasses = m_smoothingPasses;
        state.rim = m_rim;
        state.rimShaped = m_rimShaped;
        state.base = m_base;
        state.cliffSegments = m_cliffSegments;
        state.cliffTopNodes = m_cliffTopNodes;
        state.cut = m_cut;
        state.waterNodeShape = m_waterNode;
        state.cellShape = m_cellShape;
        state.cellCorners = m_cellCorners;
        state.cellLevel = m_cellLevel;
    }

    void restoreLand(const KeptLandState &state)
    {
        m_bands = state.bands;
        m_points = state.points;
        m_cliffs = state.cliffs;
        m_ridges = state.ridges;
        m_terraces = state.terraces;
        m_cuts = state.cuts;
        m_ramps = state.ramps;
        m_spires = state.spires;
        m_peaks = state.peaks;
        m_rough = state.rough;
        m_water = state.water;
        m_hasGrid = state.hasGrid;
        m_gridStep = state.gridStep;
        m_gridSide = state.gridSide;
        m_gridValues = state.gridValues;
        m_pointPull = state.pointPull;
        m_smoothingPasses = state.smoothingPasses;
        m_rim = state.rim;
        m_rimShaped = state.rimShaped;
        m_base = state.base;
        m_cliffSegments = state.cliffSegments;
        m_cliffTopNodes = state.cliffTopNodes;
        m_cut = state.cut;
        m_waterNode = state.waterNodeShape;
        m_cellShape = state.cellShape;
        m_cellCorners = state.cellCorners;
        m_cellLevel = state.cellLevel;
        // What the land made of the map so far (the structures' fields are read again).
        const std::string stem = m_lowered.mapStem;
        const std::string world = m_lowered.world;
        const std::string styleWorld = m_lowered.styleWorld;
        m_lowered = state.lowered;
        m_lowered.mapStem = stem;
        m_lowered.world = world;
        m_lowered.styleWorld = styleWorld;
        m_lowered.roads.clear();
        m_lowered.buildings.clear();
        m_lowered.caves.clear();
        m_lowered.falls.clear();
    }

    void issue(const std::string &path, const std::string &message, const std::string &code)
    {
        m_issues.push_back({SketchFile, path, message, code});
    }

    void readHeights()
    {
        std::map<std::string, double> bandLevels;
        const YAML::Node planBands = childOf(m_plan, "height_bands");

        for (size_t index = 0; planBands.IsDefined() && planBands.IsSequence() && index < planBands.size(); ++index)
        {
            const YAML::Node band = planBands[index];
            const YAML::Node range = childOf(band, "range");
            double low = 0.0;
            double high = 0.0;

            if (range.IsDefined() && range.IsSequence() && range.size() == 2 && numberOf(range[0], low)
                && numberOf(range[1], high))
            {
                bandLevels[textOf(band, "id")] = (low + high) * 0.5;
            }
        }

        const YAML::Node heights = childOf(m_sketch, "heights");
        const YAML::Node bands = childOf(heights, "bands");

        for (size_t index = 0; bands.IsDefined() && bands.IsSequence() && index < bands.size(); ++index)
        {
            const YAML::Node node = bands[index];
            const std::string path = "heights.bands[" + std::to_string(index) + "]";
            const std::map<std::string, double>::const_iterator level = bandLevels.find(textOf(node, "band"));
            Band band;

            if (level == bandLevels.end())
            {
                issue(path + ".band", "the band " + textOf(node, "band") + " has no range in plan.yml height_bands, "
                    "so its outline has no level", "reference");
                continue;
            }

            if (!pointsOf(childOf(node, "polygon"), band.polygon) || band.polygon.size() < 3)
            {
                issue(path + ".polygon", "the outline is not a list of at least three [x, y] points", "geometry");
                continue;
            }

            band.level = level->second;
            m_bands.push_back(band);
        }

        const YAML::Node points = childOf(heights, "points");
        size_t movedPoints = 0;

        for (size_t index = 0; points.IsDefined() && points.IsSequence() && index < points.size(); ++index)
        {
            const YAML::Node node = points[index];
            const std::string path = "heights.points[" + std::to_string(index) + "]";
            Point2 at = {0.0, 0.0};
            HeightPoint point;

            if (!pointOf(childOf(node, "at"), at) || !numberOf(childOf(node, "h"), point.height))
            {
                issue(path, "a height point needs `at: [x, y]` and a number `h`", "heights");
                continue;
            }

            const int x = static_cast<int>(std::lround(at[0]));
            const int y = static_cast<int>(std::lround(at[1]));
            movedPoints += (x > Nodes - 1 || y > Nodes - 1 || x < 0 || y < 0) ? 1 : 0;
            point.node = nodeIndex(std::clamp(x, 0, Nodes - 1), std::clamp(y, 0, Nodes - 1));
            m_points.push_back(point);
        }

        if (movedPoints != 0)
        {
            m_lowered.warnings.push_back("heights.points: " + std::to_string(movedPoints) + " stand on the map's far "
                "edge (x or y 128), which an ODM does not store; moved to the last stored node (127)");
        }

        const YAML::Node cliffs = childOf(heights, "cliffs");

        for (size_t index = 0; cliffs.IsDefined() && cliffs.IsSequence() && index < cliffs.size(); ++index)
        {
            const YAML::Node node = cliffs[index];
            Cliff cliff;

            if (!pointsOf(childOf(node, "line"), cliff.line) || cliff.line.size() < 2)
            {
                issue("heights.cliffs[" + std::to_string(index) + "].line",
                    "a cliff's line is a list of at least two [x, y] points", "geometry");
                continue;
            }

            numberOf(childOf(node, "drop"), cliff.drop);
            const std::string down = textOf(node, "down");
            cliff.down = down == "left" ? -1 : (down == "right" ? 1 : 0);
            m_cliffs.push_back(cliff);
        }

        readRidges(childOf(heights, "ridges"));
        readTerraces(childOf(heights, "terraces"));
        readCuts(childOf(heights, "cuts"));
        readSpires(childOf(heights, "spires"));
        // heights.nodes are read after the land words (run): applied after the kept land, outside its key.
        readPeaks(childOf(heights, "peaks"));
        readRough(childOf(heights, "rough"));
        const YAML::Node grid = childOf(heights, "grid");

        if (grid.IsDefined() && grid.IsMap())
        {
            double step = 0.0;
            double unit = 64.0;
            numberOf(childOf(grid, "step"), step);
            numberOf(childOf(grid, "unit"), unit);
            const YAML::Node rows = childOf(grid, "rows");
            const int gridStep = static_cast<int>(step);
            const size_t side = gridStep >= 1 && Nodes % gridStep == 0 ? static_cast<size_t>(Nodes / gridStep) : 0;
            bool readable = side != 0 && rows.IsDefined() && rows.IsSequence() && rows.size() == side;

            for (size_t row = 0; readable && row < side; ++row)
            {
                const YAML::Node rowNode = rows[row];
                readable = rowNode.IsSequence() && rowNode.size() == side;

                for (size_t column = 0; readable && column < side; ++column)
                {
                    double value = 0.0;
                    readable = numberOf(rowNode[column], value);
                    m_gridValues.push_back(value * unit);
                }
            }

            if (!readable)
            {
                issue("heights.grid", "the height grid needs a `step` that divides 128 and 128 / step rows of "
                    "128 / step numbers", "heights");
                return;
            }

            m_hasGrid = true;
            m_gridStep = gridStep;
            m_gridSide = static_cast<int>(side);
        }

        m_pointPull = m_hasGrid ? std::max(1.0, m_gridStep * GridPointReachShare) : PointPullCells;
        m_smoothingPasses = m_hasGrid ? GridSmoothingPasses : SmoothingPasses;
        readOutdoorRim(m_sketch, m_rim, m_issues, m_lowered.warnings);
    }

    void readRidges(const YAML::Node &ridges)
    {
        for (size_t index = 0; ridges.IsDefined() && ridges.IsSequence() && index < ridges.size(); ++index)
        {
            Ridge ridge;

            if (readLine(ridges[index], "heights.ridges[" + std::to_string(index) + "]", false, ridge))
            {
                m_ridges.push_back(ridge);
            }
        }
    }

    // `ramps` of a terrace or a cut: lines of nodes graded across its steps, read as ridges without sides.
    void readRamps(const YAML::Node &ramps, const std::string &path)
    {
        if (ramps.IsDefined() && !ramps.IsSequence())
        {
            issue(path, "`ramps` is a list of ramps, each `{line: [[x, y], ...]}` with `width` and `height` as "
                "a ridge's", "heights");
            return;
        }

        for (size_t index = 0; ramps.IsDefined() && index < ramps.size(); ++index)
        {
            Ridge ramp;

            if (readLine(ramps[index], path + "[" + std::to_string(index) + "]", true, ramp))
            {
                m_ramps.push_back(ramp);
            }
        }
    }

    // One ridge or ramp. A ridge's `closed` joins its last point to its first (a crater's rim); a ramp's `height`
    // may be left out (its ends take the land there, the points between are graded along the line).
    bool readLine(const YAML::Node &node, const std::string &path, bool ramp, Ridge &ridge)
    {
        const char *pWhat = ramp ? "a ramp" : "a ridge";
        bool usable = true;

        if (!pointsOf(childOf(node, "line"), ridge.line) || ridge.line.size() < 2)
        {
            issue(path + ".line", std::string(pWhat) + "'s line is a list of at least two [x, y] points",
                "geometry");
            return false;
        }

        const YAML::Node closed = childOf(node, "closed");
        bool isClosed = false;

        if (closed.IsDefined() && (ramp || !closed.IsScalar() || (closed.Scalar() != "true"
            && closed.Scalar() != "false")))
        {
            issue(path + ".closed", ramp ? "a ramp runs from one end to the other: `closed` is a ridge's word"
                : "`closed` is true (the line runs on from its last point back to its first: a ring) or false",
                "heights");
            return false;
        }

        isClosed = closed.IsDefined() && closed.Scalar() == "true";

        if (isClosed && ridge.line.size() < 3)
        {
            issue(path + ".line", "a closed ridge's line is a ring of at least three [x, y] points", "geometry");
            return false;
        }

        const YAML::Node height = childOf(node, "height");
        double one = 0.0;

        if (ramp && !height.IsDefined())
        {
            ridge.heights.assign(ridge.line.size(), Unknown);
        }
        else if (numberOf(height, one))
        {
            ridge.heights.assign(ridge.line.size(), one);
        }
        else if (height.IsDefined() && height.IsSequence() && height.size() == ridge.line.size())
        {
            for (size_t point = 0; point < height.size(); ++point)
            {
                usable = numberOf(height[point], one) && usable;
                ridge.heights.push_back(one);
            }
        }
        else
        {
            usable = false;
        }

        if (!usable)
        {
            issue(path + ".height", std::string(pWhat) + "'s `height` is one number (the whole line) or one number "
                "for each of its " + std::to_string(ridge.line.size()) + " points, map units"
                + (ramp ? " (left out: from the land at its ends)" : ""), "heights");
            return false;
        }

        for (const double value : ridge.heights)
        {
            if (value < 0.0 || value > OutdoorHighestSample * OutdoorHeightStep)
            {
                issue(path + ".height", "an outdoor map stores heights from 0 to 8160: " + formatNumber(value)
                    + " cannot be built", "heights");
                return false;
            }
        }

        const YAML::Node width = childOf(node, "width");
        const YAML::Node slope = childOf(node, "slope");

        if (width.IsDefined() && (!numberOf(width, ridge.width) || ridge.width < 1.0 || ridge.width > 8.0))
        {
            issue(path + ".width", std::string(pWhat) + "'s `width` is how many nodes across take its height: 1 to 8 "
                "(1 when left out); for a broad hill use the grid or height points", "heights");
            usable = false;
        }

        if (ramp && slope.IsDefined())
        {
            issue(path + ".slope", "a ramp has no sides: it lies across its steps, which stand as they are",
                "heights");
            usable = false;
        }
        else if (slope.IsDefined() && (!numberOf(slope, ridge.slope) || ridge.slope < 0.0 || ridge.slope > 16.0))
        {
            issue(path + ".slope", "a ridge's `slope` is how many cells its sides take to run back into the "
                "land: 0 (upright, as a dyke) to 16", "heights");
            usable = false;
        }

        if (usable && isClosed)
        {
            ridge.line.push_back(ridge.line.front());
            ridge.heights.push_back(ridge.heights.front());
        }

        return usable;
    }

    void readTerraces(const YAML::Node &terraces)
    {
        for (size_t index = 0; terraces.IsDefined() && terraces.IsSequence() && index < terraces.size(); ++index)
        {
            const YAML::Node node = terraces[index];
            const std::string path = "heights.terraces[" + std::to_string(index) + "]";
            Terrace terrace;

            if (!pointsOf(childOf(node, "polygon"), terrace.polygon) || terrace.polygon.size() < 3)
            {
                issue(path + ".polygon", "a terrace's `polygon` is its outline: at least three [x, y] points (nodes "
                    "in it and on it take its height)", "geometry");
                continue;
            }

            if (!numberOf(childOf(node, "height"), terrace.height) || terrace.height < 0.0
                || terrace.height > OutdoorHighestSample * OutdoorHeightStep)
            {
                issue(path + ".height", "a terrace's `height` is one number, map units, 0 to 8160", "heights");
                continue;
            }

            const YAML::Node slope = childOf(node, "slope");

            if (slope.IsDefined() && (!numberOf(slope, terrace.slope) || terrace.slope < 0.0 || terrace.slope > 16.0))
            {
                issue(path + ".slope", "a terrace's `slope` is how many cells the land outside takes to run back from "
                    "its edge: 0 (a step, the default) to 16", "heights");
                continue;
            }

            if (!readSteps(childOf(node, "steps"), path + ".steps", terrace.steps))
            {
                continue;
            }

            readRamps(childOf(node, "ramps"), path + ".ramps");
            m_terraces.push_back(terrace);
        }
    }

    // A terrace's `steps`: [[in, height], ...], `in` in cells from the outline, each further in than the last.
    bool readSteps(const YAML::Node &node, const std::string &path, std::vector<std::array<double, 2>> &steps)
    {
        if (!node.IsDefined())
        {
            return true;
        }

        bool usable = node.IsSequence() && node.size() >= 1;
        double last = 0.0;

        for (size_t index = 0; usable && index < node.size(); ++index)
        {
            std::array<double, 2> step = {0.0, 0.0};
            usable = node[index].IsSequence() && node[index].size() == 2 && numberOf(node[index][0], step[0])
                && numberOf(node[index][1], step[1]) && step[0] > last && step[1] >= 0.0
                && step[1] <= OutdoorHighestSample * OutdoorHeightStep;
            last = step[0];
            steps.push_back(step);
        }

        if (!usable)
        {
            issue(path, "a terrace's `steps` are nested rings: [[in, height], ...], `in` the cells from the outline "
                "where the ring begins (each further in than the one before, above 0), `height` 0 to 8160", "heights");
        }

        return usable;
    }

    void readCuts(const YAML::Node &cuts)
    {
        for (size_t index = 0; cuts.IsDefined() && cuts.IsSequence() && index < cuts.size(); ++index)
        {
            const YAML::Node node = cuts[index];
            const std::string path = "heights.cuts[" + std::to_string(index) + "]";
            Cut cut;

            if (!pointsOf(childOf(node, "polygon"), cut.polygon) || cut.polygon.size() < 3)
            {
                issue(path + ".polygon", "a cut's `polygon` is its outline: at least three [x, y] points (the nodes "
                    "inside go to its floor, those on it keep the land's height as its walls)", "geometry");
                continue;
            }

            if (!numberOf(childOf(node, "floor"), cut.floor) || cut.floor < 0.0
                || cut.floor > OutdoorHighestSample * OutdoorHeightStep)
            {
                issue(path + ".floor", "a cut's `floor` is one number, map units, 0 to 8160", "heights");
                continue;
            }

            cut.open.assign(cut.polygon.size(), false);
            const YAML::Node open = childOf(node, "open");
            bool usable = true;

            if (open.IsDefined())
            {
                usable = open.IsSequence();

                for (size_t edge = 0; usable && edge < open.size(); ++edge)
                {
                    double value = -1.0;
                    usable = numberOf(open[edge], value) && value >= 0.0 && value == std::floor(value)
                        && value < static_cast<double>(cut.polygon.size());
                    cut.open[usable ? static_cast<size_t>(value) : 0] = usable;
                }
            }

            if (!usable)
            {
                issue(path + ".open", "`open` lists the outline's edges left without a wall (the way in): edge i runs "
                    "from point i to the next, 0 to " + std::to_string(cut.polygon.size() - 1), "heights");
                continue;
            }

            const YAML::Node slope = childOf(node, "slope");

            if (slope.IsDefined() && (!numberOf(slope, cut.slope) || cut.slope < 0.0 || cut.slope > 16.0))
            {
                issue(path + ".slope", "a cut's `slope` is how many cells the land beyond an open edge takes to run "
                    "down to the floor: 0 to 16 (3 when left out)", "heights");
                continue;
            }

            readRamps(childOf(node, "ramps"), path + ".ramps");
            m_cuts.push_back(cut);
        }
    }

    void readSpires(const YAML::Node &spires)
    {
        for (size_t index = 0; spires.IsDefined() && spires.IsSequence() && index < spires.size(); ++index)
        {
            const YAML::Node node = spires[index];
            const std::string path = "heights.spires[" + std::to_string(index) + "]";
            Spire spire;
            double width = 1.0;

            if (!pointOf(childOf(node, "at"), spire.at) || spire.at[0] < 0.0 || spire.at[1] < 0.0
                || spire.at[0] > Nodes - 1 || spire.at[1] > Nodes - 1)
            {
                issue(path + ".at", "a spire's `at` is [x, y] in nodes, 0 to 127: its node (width 1) or the cell "
                    "whose four nodes it takes (width 2)", "geometry");
                continue;
            }

            if (!numberOf(childOf(node, "height"), spire.height) || spire.height < 0.0
                || spire.height > OutdoorHighestSample * OutdoorHeightStep)
            {
                issue(path + ".height", "a spire's `height` is its top, one number, map units, 0 to 8160", "heights");
                continue;
            }

            const YAML::Node widthNode = childOf(node, "width");

            if (widthNode.IsDefined() && (!numberOf(widthNode, width) || (width != 1.0 && width != 2.0)))
            {
                issue(path + ".width", "a spire's `width` is 1 (the node at `at`) or 2 (the four nodes of the cell "
                    "`at` is in); a broader column is a terrace or a ridge", "heights");
                continue;
            }

            spire.width = static_cast<int>(width);
            m_spires.push_back(spire);
        }
    }

    // heights.nodes (absolute heights) and heights.strokes (differences over the described land, a sculpt brush's
    // strokes: S5_BROWSER_EDITOR.md 3.18): one form, blocks of rows from a node.
    void readNodeBlocks(const YAML::Node &blocks, const char *pList = "nodes", std::vector<NodeBlock> *pTarget = nullptr)
    {
        const bool differences = std::string(pList) == "strokes";
        std::vector<NodeBlock> &target = pTarget != nullptr ? *pTarget : m_nodeBlocks;

        for (size_t index = 0; blocks.IsDefined() && blocks.IsSequence() && index < blocks.size(); ++index)
        {
            const YAML::Node node = blocks[index];
            const std::string path = std::string("heights.") + pList + "[" + std::to_string(index) + "]";
            Point2 at = {0.0, 0.0};
            double unit = 32.0;
            const YAML::Node unitNode = childOf(node, "unit");
            const YAML::Node rows = childOf(node, "rows");

            if (!pointOf(childOf(node, "at"), at) || at[0] < 0.0 || at[1] < 0.0 || at[0] > Nodes - 1
                || at[1] > Nodes - 1 || at[0] != std::floor(at[0]) || at[1] != std::floor(at[1]))
            {
                issue(path + ".at", "a node block's `at` is the node of its first row's first value, [x, y] in whole "
                    "nodes, 0 to 127", "geometry");
                continue;
            }

            if (unitNode.IsDefined() && (!numberOf(unitNode, unit) || unit <= 0.0))
            {
                issue(path + ".unit", "a node block's `unit` is the map units of one step of its values (32, the "
                    "ODM's own step, when left out)", "heights");
                continue;
            }

            if (!rows.IsDefined() || !rows.IsSequence() || rows.size() == 0)
            {
                issue(path + ".rows", "a node block's `rows` are lists of heights in `unit`s, the first row at `at` "
                    "running east, each next row one node south; `~` keeps a node as the other words made it",
                    "heights");
                continue;
            }

            NodeBlock block;
            block.x = static_cast<int>(at[0]);
            block.y = static_cast<int>(at[1]);
            bool good = true;

            for (size_t row = 0; good && row < rows.size(); ++row)
            {
                const YAML::Node values = rows[row];
                std::vector<double> line;

                if (!values.IsSequence() || block.y + static_cast<int>(row) > Nodes - 1
                    || block.x + static_cast<int>(values.size()) > Nodes)
                {
                    issue(path + ".rows[" + std::to_string(row) + "]", "a row of a node block is a list of heights "
                        "that ends inside the map (nodes 0 to 127 both ways)", "geometry");
                    good = false;
                    break;
                }

                for (size_t column = 0; column < values.size(); ++column)
                {
                    double value = 0.0;

                    if (values[column].IsNull())
                    {
                        line.push_back(Unknown);
                        continue;
                    }

                    const double lowest = differences ? -OutdoorHighestSample * OutdoorHeightStep : 0.0;

                    if (!numberOf(values[column], value) || value * unit < lowest
                        || value * unit > OutdoorHighestSample * OutdoorHeightStep)
                    {
                        issue(path + ".rows[" + std::to_string(row) + "][" + std::to_string(column) + "]",
                            differences ? "a stroke's value is how far it moves the land at that node, a number of "
                                "`unit`s from -8160 to 8160 map units, or `~`"
                                : "a node's height is a number of `unit`s from 0 to 8160 map units, or `~`",
                            "heights");
                        good = false;
                        break;
                    }

                    line.push_back(value * unit);
                }

                block.rows.push_back(line);
            }

            if (good)
            {
                target.push_back(block);
            }
        }
    }

    // The words of land made by hand (S5_BROWSER_EDITOR.md 3.18, D15 as extended): heights.strokes (a sculpt
    // brush's raise and lower, differences over the described land), heights.smooth (areas smoothed after them),
    // heights.patches (the bounded, marked places strokes and smoothing may lie in) and heights.hand_made (a person's
    // mark that the whole map's land is made by hand: then they may lie anywhere; never on a rebuild).
    void readSculpt()
    {
        const YAML::Node heights = childOf(m_sketch, "heights");
        readNodeBlocks(childOf(heights, "strokes"), "strokes", &m_strokeBlocks);
        const YAML::Node handMade = childOf(heights, "hand_made");
        m_handMade = handMade.IsDefined() && handMade.IsScalar() && handMade.Scalar() == "true";
        const YAML::Node stats = childOf(m_project.document("project.yml"), "map_stats");

        if (m_handMade && childOf(stats, "reference").IsDefined())
        {
            issue("heights.hand_made", "a rebuild's land is described, not made by hand (map_stats.reference names "
                "the map it rebuilds): sculpt only inside heights.patches, and leave hand_made out", "heights");
        }

        const YAML::Node patches = childOf(heights, "patches");

        for (size_t index = 0; patches.IsDefined() && patches.IsSequence() && index < patches.size(); ++index)
        {
            const std::string path = "heights.patches[" + std::to_string(index) + "]";
            std::vector<Point2> polygon;

            if (!pointsOf(childOf(patches[index], "polygon"), polygon) || polygon.size() < 3)
            {
                issue(path + ".polygon", "a sculpt patch's `polygon` is its outline: at least three [x, y] points",
                    "geometry");
                continue;
            }

            double low[2] = {Far, Far};
            double high[2] = {-Far, -Far};

            for (const Point2 &point : polygon)
            {
                for (int axis = 0; axis < 2; ++axis)
                {
                    low[axis] = std::min(low[axis], point[axis]);
                    high[axis] = std::max(high[axis], point[axis]);
                }
            }

            if (high[0] - low[0] > SculptPatchCells || high[1] - low[1] > SculptPatchCells)
            {
                issue(path + ".polygon", "a sculpt patch is bounded: at most " + std::to_string(SculptPatchCells)
                    + " cells across each way (a map agents edit stays described; a person who makes the whole land "
                    "by hand marks it with heights.hand_made)", "heights");
                continue;
            }

            m_patches.push_back(polygon);
        }

        if (patches.IsDefined() && patches.IsSequence() && patches.size() > SculptPatchCount && !m_handMade)
        {
            issue("heights.patches", "at most " + std::to_string(SculptPatchCount) + " sculpt patches on a map whose "
                "land is described", "heights");
        }

        const YAML::Node smooth = childOf(heights, "smooth");

        for (size_t index = 0; smooth.IsDefined() && smooth.IsSequence() && index < smooth.size(); ++index)
        {
            const YAML::Node node = smooth[index];
            const std::string path = "heights.smooth[" + std::to_string(index) + "]";
            SmoothArea area;
            double passes = 2.0;

            if (!pointsOf(childOf(node, "polygon"), area.polygon) || area.polygon.size() < 3)
            {
                issue(path + ".polygon", "a smoothed area's `polygon` is its outline: at least three [x, y] points",
                    "geometry");
                continue;
            }

            if ((childOf(node, "strength").IsDefined() && (!numberOf(childOf(node, "strength"), area.strength)
                    || area.strength <= 0.0 || area.strength > 1.0))
                || (childOf(node, "passes").IsDefined() && (!numberOf(childOf(node, "passes"), passes) || passes < 1.0
                    || passes > 8.0 || passes != std::floor(passes))))
            {
                issue(path, "a smoothed area has a `strength` above 0 up to 1 (1 when left out) and 1 to 8 `passes` "
                    "(2)", "heights");
                continue;
            }

            area.passes = static_cast<int>(passes);
            m_smooth.push_back(area);
        }

        if (m_handMade)
        {
            return;
        }

        // On described land, strokes and smoothing lie inside the patches.
        const auto inPatch = [this](const Point2 &point)
        {
            return std::any_of(m_patches.begin(), m_patches.end(), [&point](const std::vector<Point2> &patch)
            {
                return insideOutline(patch, point) || outlineDistance(patch, point) < 0.01;
            });
        };

        for (size_t index = 0; index < m_strokeBlocks.size(); ++index)
        {
            const NodeBlock &block = m_strokeBlocks[index];
            bool outside = false;

            for (size_t row = 0; !outside && row < block.rows.size(); ++row)
            {
                for (size_t column = 0; !outside && column < block.rows[row].size(); ++column)
                {
                    outside = !std::isnan(block.rows[row][column]) && !inPatch({static_cast<double>(block.x
                        + static_cast<int>(column)), static_cast<double>(block.y + static_cast<int>(row))});
                }
            }

            if (outside)
            {
                issue("heights.strokes[" + std::to_string(index) + "]", "a stroke lies outside every sculpt patch "
                    "(heights.patches): on land agents describe, a person sculpts inside a bounded, marked patch; "
                    "mark the land made by hand (heights.hand_made) to sculpt anywhere", "heights");
            }
        }

        for (size_t index = 0; index < m_smooth.size(); ++index)
        {
            if (!std::all_of(m_smooth[index].polygon.begin(), m_smooth[index].polygon.end(), inPatch))
            {
                issue("heights.smooth[" + std::to_string(index) + "]", "a smoothed area lies outside every sculpt "
                    "patch (heights.patches); mark the land made by hand (heights.hand_made) to smooth anywhere",
                    "heights");
            }
        }
    }

    // heights.strokes: each value moves the land at its node by that much. Water keeps its level.
    void applyStrokes(const std::vector<double> &waterNode)
    {
        for (const NodeBlock &block : m_strokeBlocks)
        {
            for (size_t row = 0; row < block.rows.size(); ++row)
            {
                for (size_t column = 0; column < block.rows[row].size(); ++column)
                {
                    const double value = block.rows[row][column];
                    const int node = nodeIndex(block.x + static_cast<int>(column), block.y + static_cast<int>(row));

                    if (!std::isnan(value) && std::isnan(waterNode[node]))
                    {
                        m_lowered.ground[node] += value;
                    }
                }
            }
        }
    }

    // heights.smooth: inside each outline, `passes` rounds that move each node toward the mean of the nine around
    // it by `strength`, from the land as the words and strokes made it (so the area follows the land beneath it).
    void smoothAreas(const std::vector<double> &waterNode)
    {
        for (const SmoothArea &area : m_smooth)
        {
            std::vector<int> nodes;

            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
                    const int node = nodeIndex(x, y);

                    if (std::isnan(waterNode[node])
                        && (insideOutline(area.polygon, at) || outlineDistance(area.polygon, at) < 0.01))
                    {
                        nodes.push_back(node);
                    }
                }
            }

            for (int pass = 0; pass < area.passes; ++pass)
            {
                const std::vector<double> before = m_lowered.ground;

                for (const int node : nodes)
                {
                    const int x = node % Nodes;
                    const int y = node / Nodes;
                    double sum = 0.0;
                    int count = 0;

                    for (int dy = -1; dy <= 1; ++dy)
                    {
                        for (int dx = -1; dx <= 1; ++dx)
                        {
                            if (x + dx >= 0 && y + dy >= 0 && x + dx < Nodes && y + dy < Nodes)
                            {
                                sum += before[nodeIndex(x + dx, y + dy)];
                                ++count;
                            }
                        }
                    }

                    m_lowered.ground[node] = before[node] + (sum / count - before[node]) * area.strength;
                }
            }
        }
    }

    // heights.nodes, last of the land's words: every given node takes its height. Water keeps its level.
    void setNodeBlocks(const std::vector<double> &waterNode)
    {
        size_t wet = 0;

        for (const NodeBlock &block : m_nodeBlocks)
        {
            for (size_t row = 0; row < block.rows.size(); ++row)
            {
                for (size_t column = 0; column < block.rows[row].size(); ++column)
                {
                    const double value = block.rows[row][column];

                    if (std::isnan(value))
                    {
                        continue;
                    }

                    const int node = nodeIndex(block.x + static_cast<int>(column), block.y + static_cast<int>(row));

                    if (!std::isnan(waterNode[node]))
                    {
                        ++wet;
                        continue;
                    }

                    m_lowered.ground[node] = value;
                }
            }
        }

        if (wet != 0)
        {
            m_lowered.warnings.push_back("heights.nodes: " + std::to_string(wet) + " given nodes lie in water and "
                "keep the water's level");
        }
    }

    void readPeaks(const YAML::Node &peaks)
    {
        for (size_t index = 0; peaks.IsDefined() && peaks.IsSequence() && index < peaks.size(); ++index)
        {
            const YAML::Node node = peaks[index];
            const std::string path = "heights.peaks[" + std::to_string(index) + "]";
            PeakField field;
            field.seed = static_cast<uint32_t>(index + 1);
            const auto range = [this, &node, &path](const char *pKey, std::array<double, 2> &out, double low,
                double high, const std::string &what)
            {
                const YAML::Node value = childOf(node, pKey);
                double one = 0.0;
                bool good = false;

                if (numberOf(value, one))
                {
                    out = {one, one};
                    good = true;
                }
                else if (value.IsDefined() && value.IsSequence() && value.size() == 2)
                {
                    good = numberOf(value[0], out[0]) && numberOf(value[1], out[1]);
                }

                good = good && out[0] >= low && out[1] <= high && out[0] <= out[1];

                if (!good)
                {
                    issue(path + "." + pKey, what, "heights");
                }

                return good;
            };

            if (!pointsOf(childOf(node, "polygon"), field.polygon) || field.polygon.size() < 3)
            {
                issue(path + ".polygon", "a peak field's `polygon` is the area its peaks stand in: at least three "
                    "[x, y] points", "geometry");
                continue;
            }

            double count = 0.0;

            if (!numberOf(childOf(node, "count"), count) || count < 1.0 || count > 2000.0 || count != std::floor(count))
            {
                issue(path + ".count", "a peak field's `count` is how many peaks stand in it: 1 to 2000", "heights");
                continue;
            }

            field.count = static_cast<int>(count);
            const bool hasHeight = childOf(node, "height").IsDefined();
            field.rise = childOf(node, "rise").IsDefined();

            if (hasHeight == field.rise)
            {
                issue(path, "a peak field gives its tops by `height: [low, high]` (map units) or by `rise: [low, "
                    "high]` (over the land under each), one of the two", "heights");
                continue;
            }

            if (!range(field.rise ? "rise" : "height", field.height, 0.0, OutdoorHighestSample * OutdoorHeightStep,
                "the tops' range is [low, high] (or one number), map units, 0 to 8160"))
            {
                continue;
            }

            if (childOf(node, "radius").IsDefined() && !range("radius", field.radius, 0.0, 16.0,
                "`radius` is the range of the peaks' base radius in cells, [low, high], 0 to 16 (0: a needle)"))
            {
                continue;
            }

            field.profile = textOf(node, "profile").empty() ? (field.radius[1] > 0.0 ? "cone" : "needle")
                : textOf(node, "profile");

            if (field.profile != "needle" && field.profile != "cone" && field.profile != "round")
            {
                issue(path + ".profile", "a peak's `profile` is needle (the top only, sheer sides), cone (straight "
                    "sides) or round (rounded sides)", "heights");
                continue;
            }

            if (field.profile != "needle" && field.radius[0] <= 0.0)
            {
                issue(path + ".radius", "a cone or round peak needs a base `radius` above 0 cells", "heights");
                continue;
            }

            double width = 1.0;
            const YAML::Node widthNode = childOf(node, "width");

            if (widthNode.IsDefined() && (!numberOf(widthNode, width) || (width != 1.0 && width != 2.0)))
            {
                issue(path + ".width", "a peak's top is 1 or 2 nodes across", "heights");
                continue;
            }

            field.width = static_cast<int>(width);
            field.spacing = std::max(2.0, field.radius[0]);
            const YAML::Node spacing = childOf(node, "spacing");

            if (spacing.IsDefined() && (!numberOf(spacing, field.spacing) || field.spacing < 1.0
                || field.spacing > 32.0))
            {
                issue(path + ".spacing", "`spacing` is the least distance between two peaks' tops, cells, 1 to 32",
                    "heights");
                continue;
            }

            double seed = field.seed;
            const YAML::Node seedNode = childOf(node, "seed");

            if (seedNode.IsDefined() && (!numberOf(seedNode, seed) || seed < 0.0 || seed > 4294967295.0
                || seed != std::floor(seed)))
            {
                issue(path + ".seed", "the seed is a whole number from 0 up", "heights");
                continue;
            }

            field.seed = static_cast<uint32_t>(seed);
            m_peaks.push_back(field);
        }
    }

    // Terraces: the nodes in and on the outline take its height; with `slope` the nodes outside within that many
    // cells of the outline run back into the land. Water keeps its level. After ridges, before roads and plots.
    void levelTerraces(const std::vector<double> &waterNode)
    {
        size_t wet = 0;

        for (const Terrace &terrace : m_terraces)
        {
            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
                    const bool inside = pointInOrOnPolygon(terrace.polygon, at);
                    double outside = Far;

                    if (!inside && terrace.slope > 0.0)
                    {
                        for (size_t point = 0; point < terrace.polygon.size(); ++point)
                        {
                            outside = std::min(outside, segmentDistance(terrace.polygon[point],
                                terrace.polygon[(point + 1) % terrace.polygon.size()], at, nullptr));
                        }
                    }

                    if (!inside && outside >= terrace.slope)
                    {
                        continue;
                    }

                    const int node = nodeIndex(x, y);

                    if (!std::isnan(waterNode[node]))
                    {
                        wet += inside ? 1 : 0;
                        continue;
                    }

                    double level = terrace.height;

                    if (inside && !terrace.steps.empty())
                    {
                        // The rings: the deepest one the node is far enough in for.
                        const double in = outlineDistance(terrace.polygon, at);

                        for (const std::array<double, 2> &step : terrace.steps)
                        {
                            level = in >= step[0] - 1.0e-6 ? step[1] : level;
                        }
                    }

                    double &ground = m_lowered.ground[node];
                    ground = inside ? level
                        : ground + (terrace.height - ground) * (1.0 - outside / terrace.slope);
                }
            }
        }

        if (wet != 0)
        {
            m_lowered.warnings.push_back("heights.terraces: " + std::to_string(wet) + " nodes of terraces lie in "
                "water and keep the water's level");
        }
    }

    void readRough(const YAML::Node &areas)
    {
        for (size_t index = 0; areas.IsDefined() && areas.IsSequence() && index < areas.size(); ++index)
        {
            const YAML::Node node = areas[index];
            const std::string path = "heights.rough[" + std::to_string(index) + "]";
            RoughArea area;
            area.seed = static_cast<uint32_t>(index + 1);
            bool usable = true;

            if (!pointsOf(childOf(node, "polygon"), area.polygon) || area.polygon.size() < 3)
            {
                issue(path + ".polygon", "a rough area's outline is a list of at least three [x, y] points",
                    "geometry");
                continue;
            }

            if (!numberOf(childOf(node, "amount"), area.amount) || area.amount <= 0.0 || area.amount > 256.0)
            {
                issue(path + ".amount", "`amount` is how far the ground of the area is moved up or down at a node "
                    "on average, map units, above 0 and at most 256 (the shipped maps' walkable ground stands 22 to "
                    "28 off its neighbours; the step an ODM stores is 32)", "heights");
                usable = false;
            }

            const YAML::Node scale = childOf(node, "scale");

            if (scale.IsDefined() && (!numberOf(scale, area.scale) || area.scale < 1.0 || area.scale > 8.0))
            {
                issue(path + ".scale", "`scale` is the size of the bumps in cells: 1 (node by node, when left out) "
                    "to 8", "heights");
                usable = false;
            }

            double seed = area.seed;
            const YAML::Node seedNode = childOf(node, "seed");

            if (seedNode.IsDefined() && (!numberOf(seedNode, seed) || seed < 0.0 || seed > 4294967295.0
                || seed != std::floor(seed)))
            {
                issue(path + ".seed", "the seed is a whole number from 0 up", "heights");
                usable = false;
            }

            area.seed = static_cast<uint32_t>(seed);

            if (usable)
            {
                m_rough.push_back(area);
            }
        }
    }

    // Rough areas: each node of an area not held by something else (water, a height point, a cliff's foot, a
    // rim form) is moved up or down by chance, most by little and a few by more, fading over two cells at the
    // outline.
    void roughen(const std::vector<double> &waterNode, const std::vector<double> &feet)
    {
        if (m_rough.empty())
        {
            return;
        }

        std::vector<uint8_t> held(NodeTotal, 0);

        for (const HeightPoint &point : m_points)
        {
            held[point.node] = 1;
        }

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            held[node] |= !std::isnan(waterNode[node]) || (!feet.empty() && !std::isnan(feet[node]))
                || (!m_rimShaped.empty() && m_rimShaped[node] != 0) ? 1 : 0;
        }

        for (const RoughArea &area : m_rough)
        {
            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const int node = nodeIndex(x, y);
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};

                    if (held[node] != 0 || !insideOutline(area.polygon, at))
                    {
                        continue;
                    }

                    const double fade = std::min(1.0, outlineDistance(area.polygon, at) / RoughFadeCells);
                    double spread = 0.0;

                    if (area.scale <= 1.0)
                    {
                        // u * |u| for u from -1 to 1: its mean size is a third.
                        const double chance = outdoorChance(area.seed, x, y, 11) * 2.0 - 1.0;
                        spread = 3.0 * chance * std::fabs(chance);
                    }
                    else
                    {
                        spread = RoughWaveScale * (outdoorWave(area.seed, x, y, area.scale) * 2.0 - 1.0);
                    }

                    m_lowered.ground[node] += area.amount * spread * fade;
                }
            }
        }
    }

    // Cuts: the nodes inside each outline go to its floor; the nodes on it keep the land's height (the walls, one
    // node high cliffs); an open edge's nodes go to the floor and the land beyond it, where higher, runs down to the
    // floor over `slope` cells. Water keeps its level. After terraces, so that a cut may go into one; a cut inside
    // another steps down from its floor.
    void cutHollows(const std::vector<double> &waterNode)
    {
        size_t wet = 0;
        size_t low = 0;

        for (const Cut &cut : m_cuts)
        {
            std::vector<double> next = m_lowered.ground;

            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
                    bool onWall = false;
                    bool onOpen = false;
                    double nearOpen = Far;

                    for (size_t edge = 0; edge < cut.polygon.size(); ++edge)
                    {
                        double share = 0.0;
                        const double distance = segmentDistance(cut.polygon[edge],
                            cut.polygon[(edge + 1) % cut.polygon.size()], at, &share);
                        const bool on = distance < 1.0e-6;
                        onWall = onWall || (on && !cut.open[edge]);
                        onOpen = onOpen || (on && cut.open[edge]);
                        // Beyond an open edge: square in front of it, not round its ends (beside the walls).
                        const bool square = share > 1.0e-6 && share < 1.0 - 1.0e-6;
                        nearOpen = cut.open[edge] && square ? std::min(nearOpen, distance) : nearOpen;
                    }

                    const bool inside = !onWall && (onOpen || pointInOrOnPolygon(cut.polygon, at));
                    const bool beyond = !inside && !onWall && cut.slope > 0.0 && nearOpen < cut.slope;
                    const int node = nodeIndex(x, y);

                    if ((!inside && !beyond) || !std::isnan(waterNode[node]))
                    {
                        wet += inside && !std::isnan(waterNode[node]) ? 1 : 0;
                        continue;
                    }

                    const double ground = m_lowered.ground[node];

                    if (inside)
                    {
                        next[node] = cut.floor;
                    }
                    else if (ground > cut.floor)
                    {
                        next[node] = ground + (cut.floor - ground) * (1.0 - nearOpen / cut.slope);
                    }
                }
            }

            // A wall node that stands less than a step over the floor next to the hollow: no wall there.
            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
                    const int node = nodeIndex(x, y);

                    bool onWall = false;

                    for (size_t edge = 0; edge < cut.polygon.size(); ++edge)
                    {
                        onWall = onWall || (!cut.open[edge] && segmentDistance(cut.polygon[edge],
                            cut.polygon[(edge + 1) % cut.polygon.size()], at, nullptr) < 1.0e-6);
                    }

                    if (onWall && next[node] < cut.floor + OutdoorHeightStep * 2.0)
                    {
                        low += 1;
                    }
                }
            }

            m_lowered.ground = next;
        }

        if (wet != 0)
        {
            m_lowered.warnings.push_back("heights.cuts: " + std::to_string(wet) + " nodes inside cuts lie in water "
                "and keep the water's level");
        }

        if (low != 0)
        {
            m_lowered.warnings.push_back("heights.cuts: " + std::to_string(low) + " nodes of the cuts' walls stand "
                "less than 64 over the floor (the land there is no higher than the hollow): no wall where they are");
        }
    }

    // Ramps: a height left out at a ramp's end takes the land there (after the terraces and cuts), the points
    // between graded by their distance along the line; then laid as ridges without sides.
    void layRamps(const std::vector<double> &waterNode)
    {
        for (Ridge &ramp : m_ramps)
        {
            const auto landAt = [this](const Point2 &point)
            {
                const int x = std::clamp(static_cast<int>(std::lround(point[0])), 0, Nodes - 1);
                const int y = std::clamp(static_cast<int>(std::lround(point[1])), 0, Nodes - 1);
                return m_lowered.ground[nodeIndex(x, y)];
            };

            if (std::isnan(ramp.heights.front()))
            {
                ramp.heights.front() = landAt(ramp.line.front());
            }

            if (std::isnan(ramp.heights.back()))
            {
                ramp.heights.back() = landAt(ramp.line.back());
            }

            std::vector<double> along(ramp.line.size(), 0.0);

            for (size_t point = 1; point < ramp.line.size(); ++point)
            {
                along[point] = along[point - 1] + oy::hypot(ramp.line[point][0] - ramp.line[point - 1][0],
                    ramp.line[point][1] - ramp.line[point - 1][1]);
            }

            for (size_t point = 1; point + 1 < ramp.line.size(); ++point)
            {
                if (std::isnan(ramp.heights[point]))
                {
                    const double share = along.back() > 0.0 ? along[point] / along.back() : 0.0;
                    ramp.heights[point] = ramp.heights.front() + (ramp.heights.back() - ramp.heights.front()) * share;
                }
            }
        }

        raiseLines(m_ramps, waterNode, "heights.*.ramps");
    }

    // Peak fields, then spires: each sets its nodes where it stands higher than the land (a peak) or to its height
    // (a spire). Water keeps its level.
    void raisePeaks(const std::vector<double> &waterNode)
    {
        for (size_t fieldIndex = 0; fieldIndex < m_peaks.size(); ++fieldIndex)
        {
            const PeakField &field = m_peaks[fieldIndex];
            const std::vector<double> land = m_lowered.ground;
            std::vector<Point2> tops;
            int tries = 0;

            while (static_cast<int>(tops.size()) < field.count && tries < field.count * 200)
            {
                const int salt = tries++;
                double minX = Far;
                double minY = Far;
                double maxX = -Far;
                double maxY = -Far;

                for (const Point2 &point : field.polygon)
                {
                    minX = std::min(minX, point[0]);
                    maxX = std::max(maxX, point[0]);
                    minY = std::min(minY, point[1]);
                    maxY = std::max(maxY, point[1]);
                }

                const Point2 top = {std::round(minX + (maxX - minX) * outdoorChance(field.seed, salt, 1, 31)),
                    std::round(minY + (maxY - minY) * outdoorChance(field.seed, salt, 2, 31))};

                if (top[0] < 0.0 || top[1] < 0.0 || top[0] > Nodes - 1 || top[1] > Nodes - 1
                    || !pointInOrOnPolygon(field.polygon, top))
                {
                    continue;
                }

                bool clear = true;

                for (const Point2 &other : tops)
                {
                    clear = clear && oy::hypot(other[0] - top[0], other[1] - top[1]) >= field.spacing - 1.0e-9;
                }

                if (clear)
                {
                    tops.push_back(top);
                }
            }

            if (static_cast<int>(tops.size()) < field.count)
            {
                m_lowered.warnings.push_back("heights.peaks[" + std::to_string(fieldIndex) + "]: only "
                    + std::to_string(tops.size()) + " of " + std::to_string(field.count) + " peaks fit in the area "
                    + formatNumber(field.spacing) + " cells apart: lower `spacing` or `count`");
            }

            for (size_t index = 0; index < tops.size(); ++index)
            {
                const Point2 &top = tops[index];
                const int salt = static_cast<int>(index);
                const double share = outdoorChance(field.seed, salt, 3, 37);
                const double radius = field.radius[0] + (field.radius[1] - field.radius[0])
                    * outdoorChance(field.seed, salt, 4, 37);
                const double offset = field.width == 2 ? 0.5 : 0.0;
                const Point2 middle = {top[0] + offset, top[1] + offset};
                const double over = field.rise ? land[nodeIndex(static_cast<int>(top[0]), static_cast<int>(top[1]))]
                    : 0.0;
                const double height = std::min(over + field.height[0] + (field.height[1] - field.height[0]) * share,
                    OutdoorHighestSample * OutdoorHeightStep);
                const double flat = field.width == 2 ? 0.75 : 0.0;
                const int reach = static_cast<int>(std::ceil(radius + flat)) + 1;

                for (int y = static_cast<int>(top[1]) - reach; y <= static_cast<int>(top[1]) + reach; ++y)
                {
                    for (int x = static_cast<int>(top[0]) - reach; x <= static_cast<int>(top[0]) + reach; ++x)
                    {
                        if (x < 0 || y < 0 || x >= Nodes || y >= Nodes || !std::isnan(waterNode[nodeIndex(x, y)]))
                        {
                            continue;
                        }

                        const double distance = std::max(0.0, oy::hypot(x - middle[0], y - middle[1]) - flat);
                        double value = -Far;

                        if (distance < 1.0e-6)
                        {
                            value = height;
                        }
                        else if (field.profile != "needle" && distance < radius)
                        {
                            const double ground = land[nodeIndex(x, y)];
                            const double t = distance / radius;
                            const double fall = field.profile == "cone" ? 1.0 - t
                                : 0.5 * (1.0 + oy::cos(t * 3.14159265358979323846));
                            value = ground + (height - ground) * fall;
                        }

                        double &ground = m_lowered.ground[nodeIndex(x, y)];
                        ground = std::max(ground, value);
                    }
                }
            }
        }

        for (const Spire &spire : m_spires)
        {
            const int x0 = spire.width == 1 ? static_cast<int>(std::lround(spire.at[0]))
                : std::min(static_cast<int>(std::floor(spire.at[0])), Nodes - 2);
            const int y0 = spire.width == 1 ? static_cast<int>(std::lround(spire.at[1]))
                : std::min(static_cast<int>(std::floor(spire.at[1])), Nodes - 2);

            for (int y = y0; y < y0 + spire.width; ++y)
            {
                for (int x = x0; x < x0 + spire.width; ++x)
                {
                    if (std::isnan(waterNode[nodeIndex(x, y)]))
                    {
                        m_lowered.ground[nodeIndex(x, y)] = spire.height;
                    }
                }
            }
        }
    }

    void raiseRidges(const std::vector<double> &waterNode)
    {
        raiseLines(m_ridges, waterNode, "heights.ridges");
    }

    // Ridges: the nodes within half the width of the line take its height, those within `slope` more run back into
    // the land. Water keeps its level.
    void raiseLines(const std::vector<Ridge> &lines, const std::vector<double> &waterNode, const std::string &what)
    {
        size_t wet = 0;

        for (const Ridge &ridge : lines)
        {
            const double half = ridge.width * 0.5;

            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
                    double nearest = Far;
                    double height = 0.0;

                    for (size_t point = 0; point + 1 < ridge.line.size(); ++point)
                    {
                        double share = 0.0;
                        const double distance =
                            segmentDistance(ridge.line[point], ridge.line[point + 1], at, &share);

                        if (distance < nearest)
                        {
                            nearest = distance;
                            height = ridge.heights[point] + (ridge.heights[point + 1] - ridge.heights[point]) * share;
                        }
                    }

                    // The crest: `width` nodes across (outdoorNodeOnLine); its sides run back within `slope` more,
                    // measured from the crest's last node on their side (one node wide: from half a cell).
                    size_t crestSegment = 0;
                    double crestShare = 0.0;
                    double outside = nearest - half;
                    const bool crest = ridge.width < 1.5 ? nearest <= half + 1.0e-9
                        : outdoorNodeOnLine(ridge.line, ridge.width, x, y, crestSegment, crestShare, outside);

                    if (ridge.width >= 1.5 && outside < Far)
                    {
                        height = ridge.heights[crestSegment]
                            + (ridge.heights[crestSegment + 1] - ridge.heights[crestSegment]) * crestShare;
                    }

                    if (!crest && (outside > ridge.slope + 1.0e-9 || ridge.slope <= 0.0 || outside <= 0.0))
                    {
                        continue;
                    }

                    const int node = nodeIndex(x, y);

                    if (!std::isnan(waterNode[node]))
                    {
                        wet += crest ? 1 : 0;
                        continue;
                    }

                    double &ground = m_lowered.ground[node];
                    ground = crest ? height : ground + (height - ground) * (1.0 - outside / ridge.slope);
                }
            }
        }

        if (wet != 0)
        {
            m_lowered.warnings.push_back(what + ": " + std::to_string(wet) + " nodes of " + (what == "heights.ridges"
                ? "ridge lines" : "ramps") + " lie in water and keep the water's level");
        }
    }

    void readWater()
    {
        const YAML::Node water = childOf(m_sketch, "water");
        const YAML::Node bodies = childOf(water, "bodies");

        for (size_t index = 0; bodies.IsDefined() && bodies.IsSequence() && index < bodies.size(); ++index)
        {
            const YAML::Node node = bodies[index];
            WaterShape shape;
            shape.id = textOf(node, "id");
            double level = 0.0;

            if (!pointsOf(childOf(node, "polygon"), shape.points) || shape.points.size() < 3)
            {
                issue("water.bodies[" + std::to_string(index) + "].polygon",
                    "the outline is not a list of at least three [x, y] points", "geometry");
                continue;
            }

            if (numberOf(childOf(node, "level"), level))
            {
                shape.level = level;
            }

            shape.tileSet = textOf(node, "tile_set");
            m_water.push_back(shape);
        }

        const YAML::Node rivers = childOf(water, "rivers");

        for (size_t index = 0; rivers.IsDefined() && rivers.IsSequence() && index < rivers.size(); ++index)
        {
            const YAML::Node node = rivers[index];
            WaterShape shape;
            shape.id = textOf(node, "id");
            shape.river = true;
            double level = 0.0;

            if (!pointsOf(childOf(node, "line"), shape.points) || shape.points.size() < 2)
            {
                issue("water.rivers[" + std::to_string(index) + "].line",
                    "a river's line is a list of at least two [x, y] points", "geometry");
                continue;
            }

            numberOf(childOf(node, "width_cells"), shape.width);
            shape.tileSet = textOf(node, "tile_set");

            if (numberOf(childOf(node, "level"), level))
            {
                shape.level = level;
            }

            m_water.push_back(shape);
        }
    }

    // Step 1. A grid sample a cliff hides from the node does not speak for it.
    void computeBase()
    {
        m_base.assign(NodeTotal, 0.0);

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                Point2 node = {static_cast<double>(x), static_cast<double>(y)};

                if (m_hasGrid)
                {
                    m_base[nodeIndex(x, y)] = gridAt(node);
                    continue;
                }

                // A node on a cliff line is the cliff's top: it is in the band its high side lies in.
                const std::map<int, Point2>::const_iterator top = m_cliffTopNodes.find(nodeIndex(x, y));

                if (top != m_cliffTopNodes.end())
                {
                    node = {node[0] + top->second[0], node[1] + top->second[1]};
                }

                const Band *pNearest = nullptr;
                double nearest = Far;

                for (const Band &band : m_bands)
                {
                    if (insideOutline(band.polygon, node))
                    {
                        pNearest = &band;
                        break;
                    }

                    const double distance = outlineDistance(band.polygon, node);

                    if (distance < nearest)
                    {
                        nearest = distance;
                        pNearest = &band;
                    }
                }

                m_base[nodeIndex(x, y)] = pNearest != nullptr ? pNearest->level : 0.0;
            }
        }

        // Step 1a. Beyond the square the party walks, the rim's forms take the base's place.
        shapeOutdoorRim(m_rim, m_base, &m_rimShaped);
    }

    // The nodes that stand on a cliff line, each with a short step (a hundredth of a cell) toward the high side.
    void findCliffTopNodes()
    {
        m_cliffTopNodes.clear();

        for (const Cliff &cliff : m_cliffs)
        {
            const int down = cliff.down == 0 ? 1 : cliff.down;

            for (size_t index = 0; index + 1 < cliff.line.size(); ++index)
            {
                const Point2 &first = cliff.line[index];
                const Point2 &second = cliff.line[index + 1];
                const Point2 low = sideNormal(first, second, down);

                for (int y = std::max(0, static_cast<int>(std::floor(std::min(first[1], second[1]))));
                     y <= std::min(Nodes - 1, static_cast<int>(std::ceil(std::max(first[1], second[1])))); ++y)
                {
                    for (int x = std::max(0, static_cast<int>(std::floor(std::min(first[0], second[0]))));
                         x <= std::min(Nodes - 1, static_cast<int>(std::ceil(std::max(first[0], second[0])))); ++x)
                    {
                        if (segmentDistance(first, second, {static_cast<double>(x), static_cast<double>(y)}) < 1.0e-9)
                        {
                            Point2 &step = m_cliffTopNodes[nodeIndex(x, y)];
                            step = {step[0] - low[0], step[1] - low[1]};
                        }
                    }
                }
            }
        }

        for (std::pair<const int, Point2> &entry : m_cliffTopNodes)
        {
            const double length = oy::hypot(entry.second[0], entry.second[1]);
            entry.second = length > 0.0 ? Point2{entry.second[0] / length * 0.01, entry.second[1] / length * 0.01}
                : Point2{0.0, 0.0};
        }
    }

    double gridAt(const Point2 &node) const
    {
        const double half = m_gridStep * 0.5;
        const double column = std::clamp((node[0] - half) / m_gridStep, 0.0, static_cast<double>(m_gridSide - 1));
        const double row = std::clamp((node[1] - half) / m_gridStep, 0.0, static_cast<double>(m_gridSide - 1));
        const int column0 = std::min(static_cast<int>(std::floor(column)), std::max(0, m_gridSide - 2));
        const int row0 = std::min(static_cast<int>(std::floor(row)), std::max(0, m_gridSide - 2));
        double seenSum = 0.0;
        double seenWeight = 0.0;
        double allSum = 0.0;
        double allWeight = 0.0;
        bool hidden = false;

        for (int corner = 0; corner < 4; ++corner)
        {
            const int sampleColumn = std::min(column0 + (corner % 2), m_gridSide - 1);
            const int sampleRow = std::min(row0 + (corner / 2), m_gridSide - 1);
            const double shareX = (corner % 2) == 0 ? 1.0 - (column - column0) : column - column0;
            const double shareY = (corner / 2) == 0 ? 1.0 - (row - row0) : row - row0;
            const double weight = shareX * shareY;
            const double value = m_gridValues[static_cast<size_t>(sampleRow) * m_gridSide + sampleColumn];
            const Point2 sample = {sampleColumn * m_gridStep + half, sampleRow * m_gridStep + half};
            allSum += weight * value;
            allWeight += weight;

            if (!crossesAny(node, sample, m_cliffSegments, false))
            {
                seenSum += weight * value;
                seenWeight += weight;
            }
            else
            {
                hidden = true;
            }
        }

        if (hidden)
        {
            return seenWeight > 1.0e-6 ? seenSum / seenWeight : allSum / allWeight;
        }

        // Away from cliffs the grid is read as rounded land: a curve through the samples along each row, then
        // through the rows, never above or below the two samples it runs between (so no hill grows that the grid
        // does not have).
        const auto curve = [](double before, double from, double to, double after, double share)
        {
            const double value = 0.5 * (2.0 * from + (to - before) * share
                + (2.0 * before - 5.0 * from + 4.0 * to - after) * share * share
                + (3.0 * from - before - 3.0 * to + after) * share * share * share);
            return std::clamp(value, std::min(from, to), std::max(from, to));
        };
        const auto sampleAt = [this](int sampleColumn, int sampleRow)
        {
            return m_gridValues[static_cast<size_t>(std::clamp(sampleRow, 0, m_gridSide - 1)) * m_gridSide
                + std::clamp(sampleColumn, 0, m_gridSide - 1)];
        };
        double rows[4] = {};

        for (int offset = -1; offset <= 2; ++offset)
        {
            rows[offset + 1] = curve(sampleAt(column0 - 1, row0 + offset), sampleAt(column0, row0 + offset),
                sampleAt(column0 + 1, row0 + offset), sampleAt(column0 + 2, row0 + offset), column - column0);
        }

        return curve(rows[0], rows[1], rows[2], rows[3], row - row0);
    }

    // Step 5, first half: which cells each water shape covers. The first shape that covers a cell has it.
    void markWaterCells()
    {
        // Which water shape each corner of the cells lies in: inside a body's outline, or within half a river's
        // width of its line. The first shape that covers a corner has it.
        m_waterNode.assign(GroundNodeTotal, -1);
        std::vector<uint8_t> wet(GroundNodeTotal, 0);
        std::string thin;

        for (size_t index = 0; index < m_water.size(); ++index)
        {
            // The tiles show no water narrower than one open cell with a shore on each side.
            if (m_water[index].river && m_water[index].width < 2.0)
            {
                thin += (thin.empty() ? "" : ", ") + m_water[index].id;
            }
        }

        if (!thin.empty())
        {
            m_lowered.warnings.push_back("water: the rivers " + thin + " are narrower than 2 cells; the tiles show "
                "no water thinner than one open cell with a shore on each side, so they are laid 2 cells wide");
        }

        for (int y = 0; y < OutdoorGroundNodes; ++y)
        {
            for (int x = 0; x < OutdoorGroundNodes; ++x)
            {
                const Point2 corner = {static_cast<double>(x), static_cast<double>(y)};

                for (size_t index = 0; index < m_water.size(); ++index)
                {
                    const WaterShape &shape = m_water[index];
                    bool covered = false;

                    if (!shape.river)
                    {
                        // A corner on the outline is in the water: the outline is the edge of the open water, and
                        // the shore lies outside it.
                        covered = insideOutline(shape.points, corner)
                            || outlineDistance(shape.points, corner) < 1.0e-9;
                    }
                    else
                    {
                        const double reach = std::max(shape.width * 0.5, 1.0);

                        for (size_t point = 0; !covered && point + 1 < shape.points.size(); ++point)
                        {
                            covered = segmentDistance(shape.points[point], shape.points[point + 1], corner) <= reach;
                        }
                    }

                    if (covered)
                    {
                        m_waterNode[y * OutdoorGroundNodes + x] = static_cast<int>(index);
                        wet[y * OutdoorGroundNodes + x] = 1;
                        break;
                    }
                }
            }
        }

        settleWater(wet);
        m_cellLevel.assign(NodeTotal, Unknown);

        for (size_t cell = 0; cell < NodeTotal; ++cell)
        {
            if (m_cellShape[cell] >= 0 && m_water[m_cellShape[cell]].level)
            {
                m_cellLevel[cell] = *m_water[m_cellShape[cell]].level;
            }
        }
    }

    // Clears from the water's corners what the tiles cannot show, then says of every cell which of its corners
    // are water and which shape's: a cell with a corner in water lies at the water's level (open water or shore).
    void settleWater(std::vector<uint8_t> &wet)
    {
        settleOutdoorGroundMask(wet);
        m_cellShape.assign(NodeTotal, -1);
        m_cellCorners.assign(NodeTotal, 0);

        for (size_t node = 0; node < GroundNodeTotal; ++node)
        {
            if (wet[node] == 0)
            {
                m_waterNode[node] = -1;
            }
        }

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                for (int corner = 0; corner < 4; ++corner)
                {
                    const int shape = m_waterNode[(y + corner / 2) * OutdoorGroundNodes + x + corner % 2];

                    if (shape >= 0)
                    {
                        m_cellCorners[nodeIndex(x, y)] |= static_cast<uint8_t>(1u << corner);
                        m_cellShape[nodeIndex(x, y)] = m_cellShape[nodeIndex(x, y)] < 0 ? shape
                            : std::min(m_cellShape[nodeIndex(x, y)], shape);
                    }
                }
            }
        }
    }

    // The water's level at every corner of a water cell whose level is known: the lowest of the cells that meet
    // there. Unknown elsewhere.
    std::vector<double> waterNodes() const
    {
        std::vector<double> levels(NodeTotal, Unknown);

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                const double level = m_cellLevel[nodeIndex(x, y)];

                if (m_cellShape[nodeIndex(x, y)] < 0 || std::isnan(level))
                {
                    continue;
                }

                for (int corner = 0; corner < 4; ++corner)
                {
                    const int cornerX = x + (corner % 2);
                    const int cornerY = y + (corner / 2);

                    if (cornerX < Nodes && cornerY < Nodes)
                    {
                        double &stored = levels[nodeIndex(cornerX, cornerY)];
                        stored = std::isnan(stored) ? level : std::min(stored, level);
                    }
                }
            }
        }

        return levels;
    }

    // Step 2: the low side of the cliffs that do not name it, from a rough pass in which a cliff line cuts every
    // link that so much as touches it.
    void decideCliffSides()
    {
        const bool anyUnknown = std::any_of(m_cliffs.begin(), m_cliffs.end(), [](const Cliff &cliff)
        {
            return cliff.down == 0;
        });

        if (!anyUnknown)
        {
            return;
        }

        std::vector<Segment> segments;

        for (const Cliff &cliff : m_cliffs)
        {
            for (size_t index = 0; index + 1 < cliff.line.size(); ++index)
            {
                segments.push_back({cliff.line[index], cliff.line[index + 1]});
            }
        }

        const CutMap roughCut = buildCutMap(segments, true);
        const std::vector<double> rough =
            relief(m_base, m_points, waterNodes(), {}, roughCut, m_pointPull, m_smoothingPasses, m_hasGrid,
                m_rimShaped);
        size_t undecided = 0;

        for (Cliff &cliff : m_cliffs)
        {
            if (cliff.down != 0)
            {
                continue;
            }

            double leftMinusRight = 0.0;
            size_t samples = 0;

            for (size_t index = 0; index + 1 < cliff.line.size(); ++index)
            {
                const Point2 left = sideNormal(cliff.line[index], cliff.line[index + 1], -1);
                const Point2 middle = {(cliff.line[index][0] + cliff.line[index + 1][0]) * 0.5,
                    (cliff.line[index][1] + cliff.line[index + 1][1]) * 0.5};

                for (const double reach : {1.5, 3.0})
                {
                    leftMinusRight += fieldAt(rough, middle[0] + left[0] * reach, middle[1] + left[1] * reach)
                        - fieldAt(rough, middle[0] - left[0] * reach, middle[1] - left[1] * reach);
                    ++samples;
                }
            }

            if (samples != 0 && std::fabs(leftMinusRight) / samples >= OutdoorHeightStep)
            {
                cliff.down = leftMinusRight > 0.0 ? 1 : -1;
            }
            else
            {
                ++undecided;
            }
        }

        if (undecided != 0)
        {
            m_lowered.warnings.push_back("heights.cliffs: " + std::to_string(undecided) + " have no `down` and the "
                "land on their two sides comes out level, so their low side is not known; their lines still cut "
                "the smoothing");
        }
    }

    // A node on a cliff line is the cliff's top. A height point drawn on the line with the height of the foot (a
    // cave mouth at the cliff's base) is meant for the foot: it moves to the neighbouring node across the cliff
    // whose base level its height is nearest, when that is nearer than the base of its own node. Only a point lower
    // than its own node's base can be meant for a foot (a foot lies below its top), and only a lower neighbour is
    // one: a point that raises a node on the line (a shelf on the cliff's edge) stays where it is drawn (before
    // 2026-11-13 it could move to a neighbour whose base happened to be nearer, and set that node instead).
    void settlePointsOnCliffs()
    {
        size_t moved = 0;

        for (HeightPoint &point : m_points)
        {
            if (m_cut.bits[point.node] == 0)
            {
                continue;
            }

            const int x = point.node % Nodes;
            const int y = point.node / Nodes;
            if (!m_cliffTopNodes.contains(point.node) || point.height >= m_base[point.node])
            {
                continue;
            }

            int best = point.node;
            double bestGap = std::fabs(point.height - m_base[point.node]);

            for (int direction = 0; direction < 8; ++direction)
            {
                const int otherX = x + DirectionX[direction];
                const int otherY = y + DirectionY[direction];

                if ((m_cut.bits[point.node] & (1u << direction)) == 0 || otherX < 0 || otherX >= Nodes || otherY < 0
                    || otherY >= Nodes)
                {
                    continue;
                }

                const double gap = std::fabs(point.height - m_base[nodeIndex(otherX, otherY)]);

                if (gap < bestGap && m_base[nodeIndex(otherX, otherY)] < m_base[point.node])
                {
                    bestGap = gap;
                    best = nodeIndex(otherX, otherY);
                }
            }

            moved += best != point.node ? 1 : 0;
            point.node = best;
        }

        if (moved != 0)
        {
            m_lowered.warnings.push_back("heights.points: " + std::to_string(moved) + " stand on a cliff line with "
                "a height nearer the land at its foot than at its top; a node on the line is the cliff's top, so "
                "they were taken one node to the low side");
        }
    }

    // Step 5: a cell with a cliff between its middle and a corner is the cliff's face, not water.
    void dropCliffFaceCells()
    {
        if (m_cliffSegments.empty())
        {
            return;
        }

        std::vector<uint8_t> wet(GroundNodeTotal, 0);
        bool dropped = false;

        for (size_t node = 0; node < GroundNodeTotal; ++node)
        {
            wet[node] = m_waterNode[node] >= 0 ? 1 : 0;
        }

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                if (m_cellShape[nodeIndex(x, y)] < 0)
                {
                    continue;
                }

                const Point2 middle = {x + 0.5, y + 0.5};

                for (int corner = 0; corner < 4; ++corner)
                {
                    const Point2 cornerPoint = {static_cast<double>(x + (corner % 2)),
                        static_cast<double>(y + (corner / 2))};

                    if (crossesAny(middle, cornerPoint, m_cliffSegments, false))
                    {
                        // The water draws back from the cell: its corners are land.
                        for (int other = 0; other < 4; ++other)
                        {
                            wet[(y + other / 2) * OutdoorGroundNodes + x + other % 2] = 0;
                        }

                        dropped = true;
                        break;
                    }
                }
            }
        }

        if (!dropped)
        {
            return;
        }

        const std::vector<double> levels = m_cellLevel;
        const std::vector<int> shapes = m_cellShape;
        settleWater(wet);

        // A cell that kept water keeps its level; one that lost it has none.
        for (size_t cell = 0; cell < NodeTotal; ++cell)
        {
            m_cellLevel[cell] = m_cellShape[cell] >= 0 && shapes[cell] == m_cellShape[cell] ? levels[cell]
                : (m_cellShape[cell] >= 0 && m_water[m_cellShape[cell]].level ? *m_water[m_cellShape[cell]].level
                    : Unknown);
        }
    }

    // Step 5: water without a level takes it from the land the bands, the points and the other water give.
    void levelOpenWater()
    {
        std::vector<size_t> open;

        for (size_t index = 0; index < m_water.size(); ++index)
        {
            if (!m_water[index].level)
            {
                open.push_back(index);
            }
        }

        if (open.empty())
        {
            return;
        }

        const std::vector<double> land =
            relief(m_base, m_points, waterNodes(), {}, m_cut, m_pointPull, m_smoothingPasses, m_hasGrid,
                m_rimShaped);
        const auto floorToStep = [](double height)
        {
            return std::floor(height / OutdoorHeightStep) * OutdoorHeightStep;
        };

        for (const size_t index : open)
        {
            const WaterShape &shape = m_water[index];

            if (!shape.river)
            {
                double lowest = Far;
                size_t cells = 0;

                for (int y = 0; y < Nodes; ++y)
                {
                    for (int x = 0; x < Nodes; ++x)
                    {
                        if (m_cellShape[nodeIndex(x, y)] == static_cast<int>(index))
                        {
                            lowest = std::min(lowest, fieldAt(land, x + 0.5, y + 0.5));
                            ++cells;
                        }
                    }
                }

                if (cells == 0)
                {
                    continue;
                }

                for (size_t cell = 0; cell < NodeTotal; ++cell)
                {
                    if (m_cellShape[cell] == static_cast<int>(index))
                    {
                        m_cellLevel[cell] = floorToStep(lowest);
                    }
                }

                m_lowered.warnings.push_back("water: " + shape.id + " has no `level`; it lies at "
                    + formatNumber(floorToStep(lowest)) + ", the lowest land under it");
                continue;
            }

            // The ground along the line in half-cell steps, never rising downstream.
            std::vector<std::vector<double>> levels(shape.points.size() - 1);
            double lowestSoFar = Far;
            double source = 0.0;

            for (size_t segment = 0; segment + 1 < shape.points.size(); ++segment)
            {
                const Point2 &first = shape.points[segment];
                const Point2 &second = shape.points[segment + 1];
                const int steps = std::max(1, static_cast<int>(std::ceil(oy::hypot(second[0] - first[0],
                    second[1] - first[1]) * 2.0)));

                for (int step = 0; step <= steps; ++step)
                {
                    const double share = static_cast<double>(step) / steps;
                    lowestSoFar = std::min(lowestSoFar, fieldAt(land, first[0] + (second[0] - first[0]) * share,
                        first[1] + (second[1] - first[1]) * share));
                    levels[segment].push_back(floorToStep(lowestSoFar));

                    if (segment == 0 && step == 0)
                    {
                        source = floorToStep(lowestSoFar);
                    }
                }
            }

            for (int y = 0; y < Nodes; ++y)
            {
                for (int x = 0; x < Nodes; ++x)
                {
                    if (m_cellShape[nodeIndex(x, y)] != static_cast<int>(index))
                    {
                        continue;
                    }

                    const Point2 middle = {x + 0.5, y + 0.5};
                    double nearest = Far;

                    for (size_t segment = 0; segment + 1 < shape.points.size(); ++segment)
                    {
                        double share = 0.0;
                        const double distance =
                            segmentDistance(shape.points[segment], shape.points[segment + 1], middle, &share);

                        if (distance < nearest)
                        {
                            nearest = distance;
                            const size_t last = levels[segment].size() - 1;
                            m_cellLevel[nodeIndex(x, y)] =
                                levels[segment][static_cast<size_t>(std::lround(share * last))];
                        }
                    }
                }
            }

            m_lowered.warnings.push_back("water: the river " + shape.id + " has no `level`; it follows the land "
                "from " + formatNumber(source) + " down to " + formatNumber(floorToStep(lowestSoFar)));
        }
    }

    // Step 2, the drops: the feet of the cliffs whose break in `land` is too shallow, set from their tops. Empty
    // when no foot needs setting.
    std::vector<double> cliffFeet(const std::vector<double> &land, const std::vector<double> &waterNode) const
    {
        // No foot is dug below the lowest height the sketch names.
        double lowestNamed = Far;

        for (const HeightPoint &point : m_points)
        {
            lowestNamed = std::min(lowestNamed, point.height);
        }

        for (const WaterShape &shape : m_water)
        {
            lowestNamed = shape.level ? std::min(lowestNamed, *shape.level) : lowestNamed;
        }

        for (const double level : m_base)
        {
            lowestNamed = std::min(lowestNamed, level);
        }

        std::vector<uint8_t> isPoint(NodeTotal, 0);

        for (const HeightPoint &point : m_points)
        {
            isPoint[point.node] = 1;
        }

        std::vector<double> feet(NodeTotal, Unknown);
        bool any = false;

        for (const Cliff &cliff : m_cliffs)
        {
            if (cliff.drop <= 0.0 || cliff.down == 0)
            {
                continue;
            }

            const std::vector<Segment> own = shiftedCliff(cliff);
            int west = Nodes;
            int east = 0;
            int north = Nodes;
            int south = 0;

            for (const Point2 &point : cliff.line)
            {
                west = std::min(west, static_cast<int>(std::floor(point[0])) - 1);
                east = std::max(east, static_cast<int>(std::ceil(point[0])) + 1);
                north = std::min(north, static_cast<int>(std::floor(point[1])) - 1);
                south = std::max(south, static_cast<int>(std::ceil(point[1])) + 1);
            }

            for (int y = std::max(0, north); y <= std::min(Nodes - 1, south); ++y)
            {
                for (int x = std::max(0, west); x <= std::min(Nodes - 1, east); ++x)
                {
                    // East and south neighbours: every pair of 4-neighbours once.
                    for (int direction = 0; direction <= 2; direction += 2)
                    {
                        const int otherX = x + DirectionX[direction];
                        const int otherY = y + DirectionY[direction];

                        if (otherX >= Nodes || otherY >= Nodes)
                        {
                            continue;
                        }

                        const Point2 here = {static_cast<double>(x), static_cast<double>(y)};
                        const Point2 there = {static_cast<double>(otherX), static_cast<double>(otherY)};

                        for (const Segment &segment : own)
                        {
                            if (!crosses(here, there, segment, false))
                            {
                                continue;
                            }

                            // Left of the segment, walking it: the sketch's y runs south.
                            const bool hereIsLeft = orientation(segment.first, segment.second, here) < 0.0;
                            const bool hereIsLow = hereIsLeft == (cliff.down < 0);
                            const int low = hereIsLow ? nodeIndex(x, y) : nodeIndex(otherX, otherY);
                            const int high = hereIsLow ? nodeIndex(otherX, otherY) : nodeIndex(x, y);

                            // Whether the break is too shallow is judged from where the top should be: the
                            // heights there, or its band or grid when something has dragged its edge down (cliff
                            // lines that do not quite join). The foot is then set from the top as it came out.
                            const double top = std::max(land[high], m_base[high]);

                            if (top - land[low] < cliff.drop * CliffFootShare && isPoint[low] == 0
                                && std::isnan(waterNode[low]))
                            {
                                const double foot = std::max(land[high] - cliff.drop, lowestNamed);
                                feet[low] = std::isnan(feet[low]) ? foot : std::min(feet[low], foot);
                                any = true;
                            }

                            break;
                        }
                    }
                }
            }
        }

        return any ? feet : std::vector<double>();
    }

    // Step 6a: the beds of the roads. A road's cells lie level across the road: each cell takes one height, the
    // land's along the road eased over five cells (or the sketch's `bed`), and a node takes the mean of the road
    // cells that meet at it. Water, height points and set cliff feet keep their heights; a cell with a corner in
    // water (a ford, a bridge's place) is left as it is.
    void gradeRoads(const std::vector<double> &waterNode, const std::vector<double> &feet)
    {
        if (m_lowered.roads.empty())
        {
            return;
        }

        std::vector<double> sum(NodeTotal, 0.0);
        std::vector<double> count(NodeTotal, 0.0);
        const std::vector<double> &ground = m_lowered.ground;

        for (const OutdoorRoadRun &run : m_lowered.roads)
        {
            std::vector<double> land(run.cells.size(), 0.0);

            for (size_t index = 0; index < run.cells.size(); ++index)
            {
                const int x = run.cells[index] % Nodes;
                const int y = run.cells[index] / Nodes;
                const int east = std::min(x + 1, Nodes - 1);
                const int south = std::min(y + 1, Nodes - 1);
                land[index] = (ground[nodeIndex(x, y)] + ground[nodeIndex(east, y)] + ground[nodeIndex(x, south)]
                    + ground[nodeIndex(east, south)]) / 4.0;
            }

            for (size_t index = 0; index < run.cells.size(); ++index)
            {
                if (m_cellCorners[run.cells[index]] != 0)
                {
                    continue;
                }

                double bed = 0.0;

                if (!run.bed.empty())
                {
                    bed = run.bed[index];
                }
                else
                {
                    const size_t from = index >= RoadEaseCells ? index - RoadEaseCells : 0;
                    const size_t to = std::min(run.cells.size() - 1, index + RoadEaseCells);

                    for (size_t other = from; other <= to; ++other)
                    {
                        bed += land[other];
                    }

                    bed /= static_cast<double>(to - from + 1);
                }

                const int x = run.cells[index] % Nodes;
                const int y = run.cells[index] / Nodes;

                for (int corner = 0; corner < 4; ++corner)
                {
                    const int cornerX = x + corner % 2;
                    const int cornerY = y + corner / 2;

                    if (cornerX < Nodes && cornerY < Nodes)
                    {
                        sum[nodeIndex(cornerX, cornerY)] += bed;
                        count[nodeIndex(cornerX, cornerY)] += 1.0;
                    }
                }
            }
        }

        std::vector<uint8_t> fixed(NodeTotal, 0);

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            fixed[node] = !std::isnan(waterNode[node]) || (!feet.empty() && !std::isnan(feet[node])) ? 1 : 0;
        }

        for (const HeightPoint &point : m_points)
        {
            fixed[point.node] = 1;
        }

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            if (count[node] > 0.0 && fixed[node] == 0)
            {
                m_lowered.ground[node] = sum[node] / count[node];
            }
        }
    }

    // Step 6b: the plots of the buildings. A building's floor lies at the mean height of the nodes under its
    // plot (on a whole step of the stored heights), and those nodes are set to it: the building stands on level
    // ground. A plot that covers no node (under one cell) takes the land's height at its middle and levels
    // nothing; its foundation covers the slope. Water keeps its level: a plot with water under it stands at
    // least at the water's level, and is told, unless its `floor` is said lower.
    void levelPlots(const std::vector<double> &waterNode)
    {
        std::string wet;

        for (OutdoorBuildingPlan &building : m_lowered.buildings)
        {
            const int west = std::max(0, static_cast<int>(std::ceil(building.west - 1.0e-6)));
            const int east = std::min(Nodes - 1, static_cast<int>(std::floor(building.east + 1.0e-6)));
            const int north = std::max(0, static_cast<int>(std::ceil(building.north - 1.0e-6)));
            const int south = std::min(Nodes - 1, static_cast<int>(std::floor(building.south + 1.0e-6)));
            double sum = 0.0;
            double count = 0.0;
            double waterLevel = -Far;

            for (int y = north; y <= south; ++y)
            {
                for (int x = west; x <= east; ++x)
                {
                    const bool isWater = !std::isnan(waterNode[nodeIndex(x, y)]);
                    sum += isWater ? waterNode[nodeIndex(x, y)] : m_lowered.ground[nodeIndex(x, y)];
                    count += 1.0;
                    waterLevel = isWater ? std::max(waterLevel, waterNode[nodeIndex(x, y)]) : waterLevel;
                }
            }

            // Against a slope: the row of nodes along the front (the door's side, before the plot is turned).
            const auto front = [&building, west, east, north, south](int x, int y)
            {
                return building.facing == 'n' ? y == north : building.facing == 'e' ? x == east
                    : building.facing == 'w' ? x == west : y == south;
            };

            if (building.against)
            {
                sum = 0.0;
                count = 0.0;

                for (int y = north; y <= south; ++y)
                {
                    for (int x = west; x <= east; ++x)
                    {
                        if (front(x, y))
                        {
                            sum += m_lowered.ground[nodeIndex(x, y)];
                            count += 1.0;
                        }
                    }
                }
            }

            if (!building.onDeck.empty())
            {
                // On a deck (batch O-F): the floor is the deck's top, the walls reach through it, the land stays.
                const YAML::Node structures = childOf(m_sketch, "structures");
                YAML::Node deck;

                for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size();
                     ++index)
                {
                    if (textOf(structures[index], "id") == building.onDeck && textOf(structures[index], "kind") == "deck")
                    {
                        deck = structures[index];
                    }
                }

                double level = 0.0;
                double thickness = 32.0;

                if (!deck.IsDefined() || !numberOf(childOf(deck, "level"), level)
                    || (childOf(deck, "thickness").IsDefined() && !numberOf(childOf(deck, "thickness"), thickness)))
                {
                    issue(building.path + ".on", "`on` names a structure of `kind: deck` with its top at `level` (map "
                        "units): " + building.onDeck + " is none", "building");
                    continue;
                }

                building.base = level;
                building.foundation = thickness;
                continue;
            }

            const double land = count > 0.0 ? sum / count
                : fieldAt(m_lowered.ground, (building.west + building.east) * 0.5,
                    (building.north + building.south) * 0.5);
            // `plinth`: the floor stands that far over the land, which is made level at the floor's foot.
            const double plinth = std::round(building.plinth / OutdoorHeightStep) * OutdoorHeightStep;
            building.base = std::max(std::round(land / OutdoorHeightStep) * OutdoorHeightStep + plinth, waterLevel);

            if (building.floorGiven)
            {
                // The sketch says the floor: a building at a terrace's edge stands on the terrace, not at the
                // mean of the terrace and the slope below it. Said under the water of its plot, it stands there (a
                // fall's pool at the foot of a cliff whose stream reaches the plot): the water keeps its level.
                building.base = std::round(building.floor / OutdoorHeightStep) * OutdoorHeightStep;

                if (building.base < waterLevel - OutdoorHeightStep * 0.5)
                {
                    m_lowered.warnings.push_back("buildings: the floor of " + building.id + " is said at "
                        + formatNumber(building.floor) + ", under the water that reaches its plot (at "
                        + formatNumber(waterLevel) + "): it stands there and the water keeps its level");
                }
                else if (std::fabs(building.base - land) > 512.0)
                {
                    m_lowered.warnings.push_back("buildings: the floor of " + building.id + " is said at "
                        + formatNumber(building.floor) + ", " + formatNumber(std::round(std::fabs(building.base
                        - land))) + (building.base > land ? " above" : " below") + " the land under its plot ("
                        + formatNumber(std::round(land)) + " on average): the ground is made level at the floor, "
                        "and stands as a step in the land round it");
                }
            }

            // Only a plot that stands at the water's level is told: one that merely has a corner over the shore
            // and stands higher keeps its own floor.
            if (waterLevel > -Far && building.base <= waterLevel + OutdoorHeightStep * 0.5
                && building.base >= waterLevel - OutdoorHeightStep * 0.5)
            {
                wet += (wet.empty() ? "" : ", ") + building.id;
            }

            if (!building.skirt.empty())
            {
                // The skirt reaches below the lowest land round the plot (one node beyond it).
                double lowest = building.base;

                for (int y = std::max(0, north - 1); y <= std::min(Nodes - 1, south + 1); ++y)
                {
                    for (int x = std::max(0, west - 1); x <= std::min(Nodes - 1, east + 1); ++x)
                    {
                        lowest = std::min(lowest, m_lowered.ground[nodeIndex(x, y)]);
                    }
                }

                building.foundation = std::max(building.foundation, building.base - lowest + 64.0);
            }

            if (building.against)
            {
                // The land along the back, one node beyond the plot, against the walls' top.
                double top = building.base;

                for (const OutdoorPartPlan &part : building.parts)
                {
                    top = std::max(top, building.base + part.bottom + part.wallHeight);
                }

                size_t open = 0;
                size_t row = 0;
                const bool across = building.facing == 'n' || building.facing == 's';
                const int backLine = building.facing == 'n' ? south + 1 : building.facing == 's' ? north - 1
                    : building.facing == 'e' ? west - 1 : east + 1;

                for (int along = across ? west : north; along <= (across ? east : south); ++along)
                {
                    const int x = across ? along : backLine;
                    const int y = across ? backLine : along;

                    if (x >= 0 && y >= 0 && x < Nodes && y < Nodes)
                    {
                        row += 1;
                        open += m_lowered.ground[nodeIndex(x, y)] < top ? 1 : 0;
                    }
                }

                if (open != 0)
                {
                    m_lowered.warnings.push_back("buildings: " + building.id + " stands against a slope, but "
                        + std::to_string(open) + " of the " + std::to_string(row) + " nodes along its back stand lower "
                        "than its walls' top (" + formatNumber(top) + "): its inside shows there");
                }
            }

            for (int y = north; y <= south; ++y)
            {
                for (int x = west; x <= east; ++x)
                {
                    // Against a slope only the front row is set (the door's ground); with a skirt nothing.
                    const bool keep = !building.skirt.empty() || (building.against && !front(x, y));

                    if (std::isnan(waterNode[nodeIndex(x, y)]) && !keep)
                    {
                        m_lowered.ground[nodeIndex(x, y)] = building.base - plinth;
                    }
                }
            }
        }

        if (!wet.empty())
        {
            m_lowered.warnings.push_back("buildings: the plots of " + wet + " reach onto water or its shore; they "
                "stand at the water's level there (a pier or a ship needs its own model: `form: none`)");
        }
    }

    // Step 7.
    void store(const std::vector<double> &waterNode)
    {
        m_lowered.samples.assign(NodeTotal, 0);
        m_lowered.water.assign(NodeTotal, 0);
        m_lowered.waterCorners.assign(NodeTotal, 0);
        m_lowered.waterLevel.assign(NodeTotal, 0.0);
        m_lowered.waterShape = m_cellShape;
        m_lowered.waterSets.clear();

        for (const WaterShape &shape : m_water)
        {
            m_lowered.waterSets.push_back(shape.tileSet);
        }
        size_t below = 0;
        size_t above = 0;
        double lowest = 0.0;
        double highest = 0.0;

        for (size_t node = 0; node < NodeTotal; ++node)
        {
            const bool wet = !std::isnan(waterNode[node]);
            const double surface = wet ? waterNode[node] : m_lowered.ground[node];
            const double steps = std::round(surface / OutdoorHeightStep);

            if (steps < 0.0)
            {
                ++below;
                lowest = std::min(lowest, surface);
            }
            else if (steps > OutdoorHighestSample)
            {
                ++above;
                highest = std::max(highest, surface);
            }

            m_lowered.samples[node] =
                static_cast<uint8_t>(std::clamp(steps, 0.0, static_cast<double>(OutdoorHighestSample)));

            if (wet)
            {
                m_lowered.ground[node] = waterNode[node] - OutdoorWaterBedDepth;
            }

            m_lowered.waterCorners[node] = m_cellCorners[node];

            if (m_cellShape[node] >= 0)
            {
                m_lowered.waterLevel[node] = m_cellLevel[node];
            }

            if (m_cellCorners[node] == 15)
            {
                m_lowered.water[node] = 1;
                ++m_lowered.waterCells;
            }
        }

        if (below != 0)
        {
            m_lowered.warnings.push_back("heights: " + std::to_string(below) + " nodes lie below the datum (lowest "
                + formatNumber(std::round(lowest)) + "); an ODM stores no height below 0, they are stored as 0");
        }

        if (above != 0)
        {
            m_lowered.warnings.push_back("heights: " + std::to_string(above) + " nodes lie above "
                + formatNumber(OutdoorHighestSample * OutdoorHeightStep) + " (highest "
                + formatNumber(std::round(highest)) + "), the most an ODM stores; they are stored as that");
        }
    }

    // A cliff's drop against the break that came out: the mean step over pairs of nodes one cell to each side.
    void checkCliffs()
    {
        size_t shallow = 0;
        std::string worst;
        double worstShare = 1.0;

        for (size_t index = 0; index < m_cliffs.size(); ++index)
        {
            const Cliff &cliff = m_cliffs[index];

            if (cliff.drop <= 0.0)
            {
                continue;
            }

            const std::vector<Segment> own = shiftedCliff(cliff);
            double sum = 0.0;
            size_t pairs = 0;

            for (size_t segment = 0; segment + 1 < cliff.line.size(); ++segment)
            {
                const Point2 low = sideNormal(cliff.line[segment], cliff.line[segment + 1], cliff.down == 0 ? 1
                    : cliff.down);

                for (const double share : {0.25, 0.5, 0.75})
                {
                    const double x = cliff.line[segment][0] + (cliff.line[segment + 1][0] - cliff.line[segment][0])
                        * share;
                    const double y = cliff.line[segment][1] + (cliff.line[segment + 1][1] - cliff.line[segment][1])
                        * share;
                    const int lowX = static_cast<int>(std::lround(x + low[0]));
                    const int lowY = static_cast<int>(std::lround(y + low[1]));
                    const int highX = static_cast<int>(std::lround(x - low[0]));
                    const int highY = static_cast<int>(std::lround(y - low[1]));

                    if (lowX < 0 || lowX >= Nodes || lowY < 0 || lowY >= Nodes || highX < 0 || highX >= Nodes
                        || highY < 0 || highY >= Nodes
                        || !crossesAny({static_cast<double>(lowX), static_cast<double>(lowY)},
                            {static_cast<double>(highX), static_cast<double>(highY)}, own, false))
                    {
                        continue;
                    }

                    sum += std::fabs(m_lowered.samples[nodeIndex(highX, highY)]
                        - m_lowered.samples[nodeIndex(lowX, lowY)]) * OutdoorHeightStep;
                    ++pairs;
                }
            }

            if (pairs != 0 && sum / pairs < cliff.drop * 0.5)
            {
                ++shallow;

                if (sum / pairs / cliff.drop < worstShare)
                {
                    worstShare = sum / pairs / cliff.drop;
                    worst = "cliffs[" + std::to_string(index) + "] from " + cellText(cliff.line[0][0],
                        cliff.line[0][1]) + ": a break of " + formatNumber(std::round(sum / pairs)) + " for a drop "
                        "of " + formatNumber(cliff.drop);
                }
            }
        }

        if (shallow != 0)
        {
            m_lowered.warnings.push_back("heights.cliffs: " + std::to_string(shallow) + " of "
                + std::to_string(m_cliffs.size()) + " break by less than half their `drop` (height points or water "
                "at their foot hold the ground up); the shallowest is " + worst);
        }
    }

    // The party arrives at the plan's first entrance of kind `arrival` that the sketch places; without one, at the
    // first that is not an exit.
    void placeStart()
    {
        const YAML::Node entrances = childOf(m_plan, "entrances");
        const YAML::Node points = childOf(m_sketch, "points");

        for (const char *pKind : {"arrival", ""})
        {
            for (size_t index = 0; entrances.IsDefined() && entrances.IsSequence() && index < entrances.size();
                 ++index)
            {
                const YAML::Node entrance = entrances[index];
                const std::string kind = textOf(entrance, "kind");
                const std::string id = textOf(entrance, "id");

                if (kind == "exit" || (std::string(pKind) == "arrival" && kind != "arrival"))
                {
                    continue;
                }

                for (size_t point = 0; points.IsDefined() && points.IsSequence() && point < points.size(); ++point)
                {
                    const YAML::Node pointNode = points[point];
                    Point2 at = {0.0, 0.0};

                    if (textOf(pointNode, "id") != id || !pointOf(childOf(pointNode, "at"), at))
                    {
                        continue;
                    }

                    LoweredOutdoorStart start;
                    start.entrance = id;
                    start.x = (at[0] - Nodes / 2) * OutdoorCellSize;
                    start.y = (Nodes / 2 - at[1]) * OutdoorCellSize;
                    start.z = m_lowered.storedHeightAt(at[0], at[1]);
                    const std::string facing = textOf(pointNode, "facing");
                    start.facing = facingUnits(facing.empty() ? textOf(entrance, "facing") : facing);
                    m_lowered.start = start;
                    const int cellX = std::clamp(static_cast<int>(std::floor(at[0])), 0, Nodes - 1);
                    const int cellY = std::clamp(static_cast<int>(std::floor(at[1])), 0, Nodes - 1);

                    if (m_lowered.water[nodeIndex(cellX, cellY)] != 0)
                    {
                        m_lowered.warnings.push_back("points: the arrival " + id + " at " + cellText(at[0], at[1])
                            + " stands in water");
                    }

                    return;
                }
            }
        }

        m_issues.push_back({"plan.yml", "entrances", "the map needs a party start: an entrance in plan.yml (kind "
            "arrival or both) with a point of the same id in sketch.yml `points`", "project"});
    }

    const std::string m_styleWorld;
    const Project &m_project;
    LoweredOutdoorMap &m_lowered;
    std::vector<ProjectIssue> &m_issues;
    const YAML::Node m_plan;
    const YAML::Node m_sketch;
    std::vector<Band> m_bands;
    std::vector<HeightPoint> m_points;
    std::vector<Cliff> m_cliffs;
    std::vector<Ridge> m_ridges;
    std::vector<Terrace> m_terraces;
    std::vector<Cut> m_cuts;
    // Ramps of terraces and cuts, laid after both: a height of NaN at a point of the line is taken from the land
    // there (its ends) or graded between them (the points between).
    std::vector<Ridge> m_ramps;
    std::vector<Spire> m_spires;
    std::vector<NodeBlock> m_nodeBlocks;
    // A person's sculpt strokes (heights.strokes: differences over the described land), the smoothed areas
    // (heights.smooth), the patches strokes may lie in (heights.patches) and the mark of land made by hand.
    std::vector<NodeBlock> m_strokeBlocks;
    struct SmoothArea
    {
        std::vector<Point2> polygon;
        double strength = 1.0;
        int passes = 2;
    };
    std::vector<SmoothArea> m_smooth;
    std::vector<std::vector<Point2>> m_patches;
    bool m_handMade = false;
    OutdoorLandCache *m_pLand = nullptr;
    // The asset root's door pictures (lowerOutdoorProject); none: no wing door is paired.
    const OutdoorDoorPictures *m_pDoorPictures = nullptr;
    std::vector<PeakField> m_peaks;
    std::vector<RoughArea> m_rough;
    std::vector<WaterShape> m_water;
    bool m_hasGrid = false;
    int m_gridStep = 0;
    int m_gridSide = 0;
    std::vector<double> m_gridValues;
    double m_pointPull = PointPullCells;
    int m_smoothingPasses = SmoothingPasses;
    // The land beyond the square the party walks, as `frame.rim` and `frame.edge` describe it (core/OutdoorRim).
    OutdoorRim m_rim;
    // Per node: 1 where a rim form shaped it (empty when the sketch has no rim forms).
    std::vector<uint8_t> m_rimShaped;
    std::vector<double> m_base;
    std::vector<Segment> m_cliffSegments;
    std::map<int, Point2> m_cliffTopNodes;
    CutMap m_cut;
    // Per corner of the cells (129 x 129): the water shape it lies in, or -1.
    std::vector<int> m_waterNode;
    // Per cell: the water shape that has a corner of it (the cell lies at that water's level), or -1; which of its
    // corners are water; and the water's level there (Unknown until it is decided).
    std::vector<int> m_cellShape;
    std::vector<uint8_t> m_cellCorners;
    std::vector<double> m_cellLevel;
};
}

double LoweredOutdoorMap::storedHeightAt(double x, double y) const
{
    if (samples.size() != NodeTotal)
    {
        return 0.0;
    }

    const double clampedX = std::clamp(x, 0.0, static_cast<double>(Nodes - 1));
    const double clampedY = std::clamp(y, 0.0, static_cast<double>(Nodes - 1));
    const int x0 = std::min(static_cast<int>(std::floor(clampedX)), Nodes - 2);
    const int y0 = std::min(static_cast<int>(std::floor(clampedY)), Nodes - 2);
    const double shareX = clampedX - x0;
    const double shareY = clampedY - y0;
    const auto at = [this](int nodeX, int nodeY)
    {
        return samples[nodeIndex(nodeX, nodeY)] * OutdoorHeightStep;
    };
    const double north = at(x0, y0) * (1.0 - shareX) + at(x0 + 1, y0) * shareX;
    const double south = at(x0, y0 + 1) * (1.0 - shareX) + at(x0 + 1, y0 + 1) * shareX;
    return north * (1.0 - shareY) + south * shareY;
}

double LoweredOutdoorMap::groundHeightAt(double x, double y) const
{
    if (samples.size() != NodeTotal)
    {
        return 0.0;
    }

    const double clampedX = std::clamp(x, 0.0, static_cast<double>(Nodes - 1));
    const double clampedY = std::clamp(y, 0.0, static_cast<double>(Nodes - 1));
    const int x0 = std::min(static_cast<int>(std::floor(clampedX)), Nodes - 2);
    const int y0 = std::min(static_cast<int>(std::floor(clampedY)), Nodes - 2);
    const double shareX = clampedX - x0;
    const double shareY = clampedY - y0;
    const auto at = [this](int nodeX, int nodeY)
    {
        return samples[nodeIndex(nodeX, nodeY)] * OutdoorHeightStep;
    };
    const double northWest = at(x0, y0);
    const double northEast = at(x0 + 1, y0);
    const double southWest = at(x0, y0 + 1);
    const double southEast = at(x0 + 1, y0 + 1);
    return shareX >= shareY ? northWest + shareX * (northEast - northWest) + shareY * (southEast - northEast)
                            : northWest + shareY * (southWest - northWest) + shareX * (southEast - southWest);
}

bool outdoorNodeOnLine(const std::vector<std::array<double, 2>> &line, double width, int x, int y, size_t &segment,
    double &share, double &beyond)
{
    const Point2 at = {static_cast<double>(x), static_cast<double>(y)};
    beyond = Far;

    if (width < 1.5)
    {
        // The nodes nearest the line.
        double nearest = Far;

        for (size_t point = 0; point + 1 < line.size(); ++point)
        {
            double along = 0.0;
            const double distance = segmentDistance(line[point], line[point + 1], at, &along);

            if (distance < nearest)
            {
                nearest = distance;
                segment = point;
                share = along;
            }
        }

        return nearest <= 0.5 + 1.0e-9;
    }

    // That many nodes across, along the axis the segment crosses most: from `low` to `high` nodes to its left.
    const int count = static_cast<int>(std::lround(width));
    const double low = -std::floor((count - 1) * 0.5) - 0.5;
    const double high = std::ceil((count - 1) * 0.5) + 0.5;

    for (size_t point = 0; point + 1 < line.size(); ++point)
    {
        const Point2 &from = line[point];
        const Point2 &to = line[point + 1];
        const double dx = to[0] - from[0];
        const double dy = to[1] - from[1];
        const bool alongX = std::fabs(dx) >= std::fabs(dy);
        const double run = alongX ? dx : dy;

        if (std::fabs(run) < 1.0e-9)
        {
            continue;
        }

        // Where along the segment the node stands, on the axis it runs along most.
        const double t = ((alongX ? at[0] : at[1]) - (alongX ? from[0] : from[1])) / run;

        if (t < -1.0e-9 || t > 1.0 + 1.0e-9)
        {
            continue;
        }

        // Across: positive to the left as drawn (north up, y south: walking east, left is north).
        const double crossing = alongX ? from[1] + dy * t : from[0] + dx * t;
        const double offset = alongX ? (at[1] - crossing) * (dx > 0.0 ? -1.0 : 1.0)
            : (at[0] - crossing) * (dy > 0.0 ? 1.0 : -1.0);

        if (offset >= low - 1.0e-9 && offset < high - 1.0e-9)
        {
            segment = point;
            share = std::clamp(t, 0.0, 1.0);
            beyond = 0.0;
            return true;
        }

        // Off the nodes taken: how far past the last of them on its side, square to the segment.
        const double past = offset < low ? (low + 0.5) - offset : offset - (high - 0.5);
        const double square = std::fabs(run) / oy::hypot(dx, dy);

        if (past * square < beyond)
        {
            beyond = past * square;
            segment = point;
            share = std::clamp(t, 0.0, 1.0);
        }
    }

    return false;
}

bool lowerOutdoorLandOnly(const Project &project)
{
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    Lowerer lowerer(project, lowered, issues, nullptr);
    lowerer.runLandOnly();
    return issues.empty();
}

bool lowerOutdoorProject(const Project &project, LoweredOutdoorMap &lowered, std::vector<ProjectIssue> &issues,
    OutdoorLandCache *pLand, const std::string &styleWorld, const OutdoorDoorPictures *pDoorPictures)
{
    Lowerer lowerer(project, lowered, issues, pLand, styleWorld);
    lowerer.useDoorPictures(pDoorPictures);
    return lowerer.run() && layOutdoorGround(project, lowered, issues);
}
}
