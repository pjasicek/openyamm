#include "core/Sketch.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/Polygon.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <map>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
const char *SketchFile = "sketch.yml";
constexpr double Epsilon = 1.0e-9;



bool numberOf(const YAML::Node &node, double &number)
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
    const std::from_chars_result result = std::from_chars(pBegin, text.data() + text.size(), number);
    return result.ec == std::errc() && std::isfinite(number);
}

bool numberOf(const YAML::Node &node, const std::string &key, double &number)
{
    return numberOf(childOf(node, key), number);
}

bool pointOf(const YAML::Node &node, Point2 &point)
{
    if (!node.IsDefined() || !node.IsSequence() || node.size() != 2)
    {
        return false;
    }

    return numberOf(node[0], point[0]) && numberOf(node[1], point[1]);
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

std::string cellText(const Point2 &point)
{
    return "[" + formatNumber(point[0]) + ", " + formatNumber(point[1]) + "]";
}

std::string itemPath(const std::string &list, size_t index)
{
    return list + "[" + std::to_string(index) + "]";
}

bool onStep(double value, double step)
{
    return std::fabs(value / step - std::round(value / step)) <= Epsilon;
}

double segmentDistance(const Point2 &first, const Point2 &second, const Point2 &point)
{
    const double dx = second[0] - first[0];
    const double dy = second[1] - first[1];
    const double lengthSquared = dx * dx + dy * dy;
    double share = 0.0;

    if (lengthSquared > 0.0)
    {
        share = std::clamp(((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / lengthSquared, 0.0, 1.0);
    }

    return oy::hypot(point[0] - first[0] - share * dx, point[1] - first[1] - share * dy);
}

double lineDistance(const std::vector<Point2> &line, const Point2 &point)
{
    if (line.size() == 1)
    {
        return oy::hypot(point[0] - line[0][0], point[1] - line[0][1]);
    }

    double best = 1.0e18;

    for (size_t index = 0; index + 1 < line.size(); ++index)
    {
        best = std::min(best, segmentDistance(line[index], line[index + 1], point));
    }

    return best;
}

double outlineDistance(const std::vector<Point2> &polygon, const Point2 &point)
{
    double best = 1.0e18;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        best = std::min(best, segmentDistance(polygon[index], polygon[(index + 1) % polygon.size()], point));
    }

    return best;
}

// Inside or on the outline.
bool insideOrOn(const std::vector<Point2> &polygon, const Point2 &point)
{
    return outlineDistance(polygon, point) <= 1.0e-6 || pointInPolygon(polygon, point, 0.0);
}

int turn(const Point2 &a, const Point2 &b, const Point2 &c)
{
    const double value = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    return value > Epsilon ? 1 : (value < -Epsilon ? -1 : 0);
}

bool withinBox(const Point2 &a, const Point2 &b, const Point2 &point)
{
    return point[0] >= std::min(a[0], b[0]) - Epsilon && point[0] <= std::max(a[0], b[0]) + Epsilon
        && point[1] >= std::min(a[1], b[1]) - Epsilon && point[1] <= std::max(a[1], b[1]) + Epsilon;
}

bool segmentsMeet(const Point2 &a, const Point2 &b, const Point2 &c, const Point2 &d)
{
    const int first = turn(a, b, c);
    const int second = turn(a, b, d);
    const int third = turn(c, d, a);
    const int fourth = turn(c, d, b);

    if (first != second && third != fourth)
    {
        return true;
    }

    return (first == 0 && withinBox(a, b, c)) || (second == 0 && withinBox(a, b, d))
        || (third == 0 && withinBox(c, d, a)) || (fourth == 0 && withinBox(c, d, b));
}

// Why an outline is not simple, in words: the repeated point or the two edges that meet.
std::string outlineFault(const std::vector<Point2> &polygon)
{
    const size_t count = polygon.size();

    for (size_t first = 0; first < count; ++first)
    {
        for (size_t second = first + 1; second < count; ++second)
        {
            if (oy::hypot(polygon[first][0] - polygon[second][0], polygon[first][1] - polygon[second][1]) <= Epsilon)
            {
                return "the point " + cellText(polygon[first]) + " is given twice (points " + std::to_string(first)
                    + " and " + std::to_string(second) + "); list each corner once and do not repeat the first "
                    "point at the end";
            }
        }
    }

    for (size_t first = 0; first < count; ++first)
    {
        for (size_t second = first + 2; second < count; ++second)
        {
            if (first == 0 && second == count - 1)
            {
                continue;
            }

            const Point2 &a = polygon[first];
            const Point2 &b = polygon[(first + 1) % count];
            const Point2 &c = polygon[second];
            const Point2 &d = polygon[(second + 1) % count];

            if (segmentsMeet(a, b, c, d))
            {
                return "the edge from " + cellText(a) + " to " + cellText(b) + " crosses or touches the edge from "
                    + cellText(c) + " to " + cellText(d) + "; reorder or move the points so the outline runs once "
                    "round the area";
            }
        }
    }

    return "two neighbouring edges fold back onto each other; remove the point between them";
}

const YAML::Node findBuilding(const YAML::Node &plan, const std::string &id)
{
    const YAML::Node spaces = childOf(plan, "spaces");

    if (!spaces.IsSequence())
    {
        return YAML::Node(YAML::NodeType::Undefined);
    }

    for (const YAML::Node &space : spaces)
    {
        const YAML::Node buildings = childOf(space, "buildings");

        if (!buildings.IsSequence())
        {
            continue;
        }

        for (const YAML::Node &building : buildings)
        {
            if (textOf(building, "id") == id)
            {
                return building;
            }
        }
    }

    return YAML::Node(YAML::NodeType::Undefined);
}

// The building's [front, depth] for one member of its group (0: the plot gives no index).
bool footprintOf(const YAML::Node &building, int index, Point2 &footprint)
{
    const YAML::Node cells = childOf(building, "footprint_cells");

    if (!cells.IsSequence() || cells.size() == 0)
    {
        return false;
    }

    if (cells[0].IsSequence())
    {
        const size_t member = index <= 0 ? 0 : static_cast<size_t>(index - 1);

        if ((index <= 0 && cells.size() != 1) || member >= cells.size())
        {
            return false;
        }

        return pointOf(cells[member], footprint) && footprint[0] > 0.0 && footprint[1] > 0.0;
    }

    return pointOf(cells, footprint) && footprint[0] > 0.0 && footprint[1] > 0.0;
}

int integerOf(const YAML::Node &node, const std::string &key, int fallback)
{
    double number = 0.0;
    return numberOf(node, key, number) ? static_cast<int>(std::lround(number)) : fallback;
}

struct PlacedPlot
{
    std::string path;
    std::string name;
    std::array<double, 4> rectangle = {0.0, 0.0, 0.0, 0.0};
};

struct HeightPoint
{
    size_t index = 0;
    Point2 at = {0.0, 0.0};
    double height = 0.0;
};

class SketchCheck
{
public:
    SketchCheck(const Project &project, std::vector<ProjectIssue> &issues)
        : m_issues(issues)
        , m_card(project.document("project.yml"))
        , m_plan(project.document("plan.yml"))
        , m_sketch(project.document(SketchFile))
    {
    }

    void run()
    {
        if (!m_sketch.IsDefined() || !m_sketch.IsMap())
        {
            return;
        }

        if (!m_plan.IsDefined() || !m_plan.IsMap())
        {
            add("", "reference", "a sketch places the things of a plan, and the project has no plan.yml; add the "
                "plan the sketch belongs to");
            return;
        }

        indexPlan();
        checkFrame();
        checkPoints();
        checkHeights();
        checkWater();
        checkRoads();
        checkDistricts();
        checkAreas();
        checkViews();
        checkGround();
        checkCoverage();
    }

private:
    void add(const std::string &path, const std::string &code, const std::string &message)
    {
        m_issues.push_back({SketchFile, path, message, code});
    }

    // A finding the lowering copes with (a point outside its band's range, a plan entry without a place): the build
    // takes the sketch as drawn, so it does not stop a build (S5_BROWSER_EDITOR.md 2.4.2).
    void warn(const std::string &path, const std::string &code, const std::string &message)
    {
        m_issues.push_back({SketchFile, path, message, code, IssueSeverity::Warning});
    }

    void indexList(const char *pKey, const char *pKind)
    {
        const YAML::Node list = childOf(m_plan, pKey);

        if (!list.IsSequence())
        {
            return;
        }

        for (const YAML::Node &entry : list)
        {
            const std::string id = textOf(entry, "id");

            if (id.empty())
            {
                continue;
            }

            m_kinds.emplace(id, pKind);
            m_entries.emplace(id, entry);
            const YAML::Node population = childOf(entry, "population");

            if (population.IsSequence())
            {
                for (const YAML::Node &group : population)
                {
                    if (!textOf(group, "id").empty())
                    {
                        m_kinds.emplace(textOf(group, "id"), "population");
                    }
                }
            }

            const YAML::Node buildings = childOf(entry, "buildings");

            if (buildings.IsSequence())
            {
                for (const YAML::Node &building : buildings)
                {
                    if (!textOf(building, "id").empty())
                    {
                        m_kinds.emplace(textOf(building, "id"), "building");
                        m_entries.emplace(textOf(building, "id"), building);
                        m_buildingSpace.emplace(textOf(building, "id"), id);
                    }
                }
            }
        }
    }

    void indexPlan()
    {
        indexList("spaces", "space");
        indexList("links", "link");
        indexList("entrances", "entrance");
        indexList("points_of_interest", "point of interest");
        indexList("landmarks", "landmark");
        indexList("sightlines", "sightline");
        indexList("height_bands", "height band");
        indexList("set_pieces", "set piece");
        indexList("containers", "container");
        indexList("goals", "goal");
        indexList("keys", "key");
        indexList("states", "state");
        indexList("regions", "region");
        const YAML::Node neighbours = childOf(m_card, "neighbours");

        if (neighbours.IsSequence())
        {
            for (const YAML::Node &neighbour : neighbours)
            {
                m_neighbours.emplace(textOf(neighbour, "id"), textOf(neighbour, "side"));
            }
        }
    }

    // Whether the plan has the id as one of the kinds. `role` is what the sketch uses it as ("the road's link").
    bool need(const std::string &id, const std::set<std::string> &kinds, const std::string &path,
        const std::string &role)
    {
        std::string wanted;

        for (const std::string &kind : kinds)
        {
            wanted += (wanted.empty() ? "" : ", ") + kind;
        }

        const std::map<std::string, std::string>::const_iterator found = m_kinds.find(id);

        if (found == m_kinds.end())
        {
            add(path, "reference", role + " names '" + id + "', which plan.yml does not have; use the id of a plan "
                "entry" + (kinds.empty() ? "" : " (" + wanted + ")") + " or add the entry to the plan");
            return false;
        }

        if (!kinds.empty() && !kinds.contains(found->second))
        {
            add(path, "reference", role + " names '" + id + "', which is a " + found->second + " in plan.yml; it "
                "must be one of: " + wanted);
            return false;
        }

        return true;
    }

    // Inside the map and on the grid: whole cells, or half cells where `half`.
    void checkCell(const Point2 &point, bool half, const std::string &path, const std::string &what)
    {
        if (point[0] < 0.0 || point[1] < 0.0 || point[0] > SketchMapCells || point[1] > SketchMapCells)
        {
            add(path, "geometry", what + " has the point " + cellText(point) + " outside the map; cells run from 0 "
                "to 128 on both axes");
            return;
        }

        const double step = half ? 0.5 : 1.0;

        if (!onStep(point[0], step) || !onStep(point[1], step))
        {
            add(path, "grid", what + " has the point " + cellText(point) + ", finer than "
                + (half ? "half cells; road lines and plot corners snap to half cells"
                        : "whole cells; only road lines and plot corners may use half cells") + ": round it");
        }
    }

    bool readLine(const YAML::Node &node, bool half, const std::string &path, const std::string &what,
        std::vector<Point2> &line)
    {
        if (!pointsOf(node, line) || line.size() < 2)
        {
            add(path, "geometry", what + " needs a line of at least two [x, y] points");
            line.clear();
            return false;
        }

        for (const Point2 &point : line)
        {
            checkCell(point, half, path, what);
        }

        return true;
    }

    bool readPolygon(const YAML::Node &node, const std::string &path, const std::string &what,
        std::vector<Point2> &polygon)
    {
        if (!pointsOf(node, polygon) || polygon.size() < 3)
        {
            add(path, "geometry", what + " needs an outline of at least three [x, y] points");
            polygon.clear();
            return false;
        }

        for (const Point2 &point : polygon)
        {
            checkCell(point, false, path, what);
        }

        if (!polygonIsSimple(polygon))
        {
            add(path, "geometry", "the outline of " + what + " is not a simple shape: " + outlineFault(polygon));
            polygon.clear();
            return false;
        }

        return true;
    }

    void checkFrame()
    {
        const YAML::Node frame = childOf(m_sketch, "frame");
        const YAML::Node playable = childOf(frame, "playable");
        double values[4] = {0.0, 0.0, 0.0, 0.0};

        if (playable.IsSequence() && playable.size() == 4 && numberOf(playable[0], values[0])
            && numberOf(playable[1], values[1]) && numberOf(playable[2], values[2]) && numberOf(playable[3], values[3]))
        {
            if (values[2] <= 0.0 || values[3] <= 0.0 || values[0] + values[2] > SketchMapCells
                || values[1] + values[3] > SketchMapCells)
            {
                add("frame.playable", "geometry", "the playable square reaches past the map: it is [x, y, width, "
                    "depth] from its north-west corner, so x + width and y + depth may be at most 128 (give the "
                    "size, not the far corner)");
            }

            for (const double value : values)
            {
                if (!onStep(value, 1.0))
                {
                    add("frame.playable", "grid", "the playable square is given in whole cells: round "
                        + formatNumber(value));
                }
            }
        }

        const YAML::Node edges = childOf(frame, "edges");

        for (size_t index = 0; edges.IsSequence() && index < edges.size(); ++index)
        {
            const YAML::Node edge = edges[index];
            const std::string path = itemPath("frame.edges", index);
            const std::string neighbour = textOf(edge, "neighbour");
            const std::map<std::string, std::string>::const_iterator found = m_neighbours.find(neighbour);

            if (found == m_neighbours.end())
            {
                add(path + ".neighbour", "reference", "the frame edge names '" + neighbour + "', which is not a "
                    "neighbour in project.yml; use the id of one of its `neighbours` or add the neighbour there");
            }
            else if (!found->second.empty() && found->second != textOf(edge, "side"))
            {
                add(path + ".side", "reference", "the frame edge to '" + neighbour + "' is on the "
                    + textOf(edge, "side") + " side, and project.yml puts that neighbour on the " + found->second
                    + " side; make the two agree");
            }

            Point2 span = {0.0, 0.0};

            if (pointOf(childOf(edge, "span"), span) && span[0] >= span[1])
            {
                add(path + ".span", "geometry", "the exit span runs [from, to] along its side with from below to; "
                    "swap the two numbers");
            }
        }

        const YAML::Node rim = childOf(frame, "rim");

        for (size_t index = 0; rim.IsSequence() && index < rim.size(); ++index)
        {
            // The plan space is a reader's link: checked when given. The forms are checked by the lowering
            // (core/OutdoorRim).
            if (childOf(rim[index], "space").IsDefined())
            {
                need(textOf(rim[index], "space"), {"space"}, itemPath("frame.rim", index) + ".space",
                    "the rim strip");
            }
        }
    }

    void checkPoints()
    {
        const YAML::Node points = childOf(m_sketch, "points");

        for (size_t index = 0; points.IsSequence() && index < points.size(); ++index)
        {
            const YAML::Node entry = points[index];
            const std::string path = itemPath("points", index);
            const std::string id = textOf(entry, "id");
            need(id, {}, path + ".id", "the point");
            Point2 at = {0.0, 0.0};

            if (pointOf(childOf(entry, "at"), at))
            {
                checkCell(at, false, path + ".at", "the point of " + id);
                m_points[id].push_back(at);
            }
        }
    }

    void checkHeights()
    {
        const YAML::Node heights = childOf(m_sketch, "heights");
        const YAML::Node points = childOf(heights, "points");

        for (size_t index = 0; points.IsSequence() && index < points.size(); ++index)
        {
            HeightPoint point;
            point.index = index;

            if (pointOf(childOf(points[index], "at"), point.at) && numberOf(points[index], "h", point.height))
            {
                checkCell(point.at, false, itemPath("heights.points", index) + ".at", "the height point");
                m_heights.push_back(point);
            }
        }

        // Per height point: the bands whose outline holds it, and whether one of them fits.
        std::vector<std::string> holding(m_heights.size());
        std::vector<bool> fits(m_heights.size(), false);
        const YAML::Node bands = childOf(heights, "bands");

        for (size_t index = 0; bands.IsSequence() && index < bands.size(); ++index)
        {
            const YAML::Node band = bands[index];
            const std::string path = itemPath("heights.bands", index);
            const std::string id = textOf(band, "band");
            const bool known = need(id, {"height band"}, path + ".band", "the height band outline");

            if (childOf(band, "space").IsDefined())
            {
                need(textOf(band, "space"), {"space"}, path + ".space", "the height band outline");
            }

            std::vector<Point2> polygon;

            if (!readPolygon(childOf(band, "polygon"), path + ".polygon", "band " + id, polygon) || !known)
            {
                continue;
            }

            const YAML::Node planBand = m_entries.find(id)->second;
            Point2 range = {0.0, 0.0};

            if (!pointOf(childOf(planBand, "range"), range))
            {
                if (!numberOf(planBand, "level", range[0]))
                {
                    continue;
                }

                range[1] = range[0];
            }

            for (size_t point = 0; point < m_heights.size(); ++point)
            {
                if (!pointInPolygon(polygon, m_heights[point].at, 0.01))
                {
                    continue;
                }

                const bool inside = m_heights[point].height >= range[0] && m_heights[point].height <= range[1];
                fits[point] = fits[point] || inside;
                holding[point] += (holding[point].empty() ? "" : ", ") + id + " (" + formatNumber(range[0]) + " to "
                    + formatNumber(range[1]) + ")";
            }
        }

        for (size_t point = 0; point < m_heights.size(); ++point)
        {
            if (!holding[point].empty() && !fits[point])
            {
                warn(itemPath("heights.points", m_heights[point].index) + ".h", "heights", "the height "
                    + formatNumber(m_heights[point].height) + " at " + cellText(m_heights[point].at)
                    + " is outside the range of the band it stands in: " + holding[point] + "; change the height, "
                    "redraw the band's outline round the point, or widen the band's range in plan.yml");
            }
        }

        const YAML::Node cliffs = childOf(heights, "cliffs");
        std::vector<std::vector<Point2>> cliffLines(cliffs.IsSequence() ? cliffs.size() : 0);

        for (size_t index = 0; cliffs.IsSequence() && index < cliffs.size(); ++index)
        {
            readLine(childOf(cliffs[index], "line"), false, itemPath("heights.cliffs", index) + ".line", "the cliff",
                cliffLines[index]);
        }

        // The roads' lines, for the passes they run through.
        std::vector<std::vector<Point2>> roadLines;
        const YAML::Node roads = childOf(m_sketch, "roads");

        for (size_t index = 0; roads.IsSequence() && index < roads.size(); ++index)
        {
            std::vector<Point2> line;

            if (pointsOf(childOf(roads[index], "line"), line) && line.size() >= 2)
            {
                roadLines.push_back(line);
            }
        }

        // A cliff line that ends a few cells short of another leaves a gap the land runs smoothly through: the
        // break closes there and the high ground spills down. Lines that are meant to meet must share a point.
        // A gap a road runs through is a pass: meant, however narrow.
        for (size_t index = 0; index < cliffLines.size(); ++index)
        {
            const std::vector<Point2> &line = cliffLines[index];

            for (const size_t end : {static_cast<size_t>(0), line.empty() ? 0 : line.size() - 1})
            {
                if (line.size() < 2)
                {
                    break;
                }

                const Point2 &point = line[end];

                // An end at the terrain's edge is closed by the edge.
                if (point[0] <= 1.0 || point[1] <= 1.0 || point[0] >= SketchMapCells - 1.0
                    || point[1] >= SketchMapCells - 1.0)
                {
                    continue;
                }

                // The two walls of a pass run side by side and end side by side: lines that run the same way at
                // the gap (within 30 degrees) are not meant to meet.
                const Point2 &inner = line[end == 0 ? 1 : line.size() - 2];
                const double ownLength = oy::hypot(point[0] - inner[0], point[1] - inner[1]);
                double nearest = SketchCliffGapCells + 1.0;
                size_t nearestLine = index;
                Point2 nearestPoint = point;
                bool joined = false;

                // An end that lies on another line shares a point with it, whichever way that line runs there
                // (two lines that go on from one point).
                for (size_t other = 0; other < cliffLines.size(); ++other)
                {
                    for (size_t segment = 0; other != index && segment + 1 < cliffLines[other].size(); ++segment)
                    {
                        joined = joined || segmentDistance(cliffLines[other][segment], cliffLines[other][segment + 1],
                            point) <= 1.0e-6;
                    }
                }

                if (joined)
                {
                    continue;
                }

                for (size_t other = 0; other < cliffLines.size(); ++other)
                {
                    for (size_t segment = 0; other != index && segment + 1 < cliffLines[other].size(); ++segment)
                    {
                        const Point2 &first = cliffLines[other][segment];
                        const Point2 &second = cliffLines[other][segment + 1];
                        const double distance = segmentDistance(first, second, point);
                        const double length = oy::hypot(second[0] - first[0], second[1] - first[1]);
                        const double turn = ownLength > 0.0 && length > 0.0
                            ? std::fabs((point[0] - inner[0]) * (second[1] - first[1])
                                - (point[1] - inner[1]) * (second[0] - first[0])) / (ownLength * length) : 1.0;

                        if (distance < nearest && turn >= 0.5)
                        {
                            nearest = distance;
                            nearestLine = other;
                            // The place on that stretch nearest to the end.
                            const double along = length > 0.0 ? std::clamp(((point[0] - first[0])
                                * (second[0] - first[0]) + (point[1] - first[1]) * (second[1] - first[1]))
                                / (length * length), 0.0, 1.0) : 0.0;
                            nearestPoint = {first[0] + (second[0] - first[0]) * along,
                                first[1] + (second[1] - first[1]) * along};
                        }
                    }
                }

                // A road that crosses the gap makes it a pass.
                bool pass = false;

                for (const std::vector<Point2> &road : roadLines)
                {
                    for (size_t segment = 0; segment + 1 < road.size(); ++segment)
                    {
                        const auto side = [](const Point2 &from, const Point2 &to, const Point2 &at)
                        {
                            return (to[0] - from[0]) * (at[1] - from[1]) - (to[1] - from[1]) * (at[0] - from[0]);
                        };
                        pass = pass || (side(point, nearestPoint, road[segment])
                            * side(point, nearestPoint, road[segment + 1]) <= 0.0
                            && side(road[segment], road[segment + 1], point)
                            * side(road[segment], road[segment + 1], nearestPoint) <= 0.0);
                    }
                }

                if (nearestLine != index && !pass && nearest > 1.0e-6 && nearest <= SketchCliffGapCells)
                {
                    warn(itemPath("heights.cliffs", index) + ".line", "heights", "the cliff ends at "
                        + cellText(point) + ", " + formatNumber(std::round(nearest * 10.0) / 10.0)
                        + " cells short of heights.cliffs[" + std::to_string(nearestLine) + "]: the land runs "
                        "smoothly through the gap and the break closes there. Let the two lines share a point, or "
                        "leave a gap wider than " + formatNumber(SketchCliffGapCells) + " cells where a slope is "
                        "meant; a gap a road's line runs through is a pass and may be as narrow as it is");
                }
            }
        }

        checkHeightGrid(childOf(heights, "grid"));
    }

    void checkHeightGrid(const YAML::Node &grid)
    {
        if (!grid.IsDefined() || !grid.IsMap())
        {
            return;
        }

        const int step = integerOf(grid, "step", 0);

        if (step < 4)
        {
            warn("heights.grid.step", "heights", "the height grid has a step of " + std::to_string(step)
                + " cells; a sketch's grid is 4 cells or coarser (a finer grid is a heightmap): use step 4 or 8 "
                "and give the detail as points, bands and cliffs");
            return;
        }

        const int mapCells = static_cast<int>(SketchMapCells);

        if (mapCells % step != 0)
        {
            warn("heights.grid.step", "heights", "the height grid's step must divide the map's 128 cells: use 4, 8, "
                "16 or 32");
            return;
        }

        const size_t expected = static_cast<size_t>(mapCells / step);
        const YAML::Node rows = childOf(grid, "rows");
        bool wrongShape = !rows.IsSequence() || rows.size() != expected;

        for (size_t row = 0; !wrongShape && row < rows.size(); ++row)
        {
            wrongShape = !rows[row].IsSequence() || rows[row].size() != expected;
        }

        if (wrongShape)
        {
            warn("heights.grid.rows", "heights", "a height grid of step " + std::to_string(step) + " has "
                + std::to_string(expected) + " rows of " + std::to_string(expected) + " values (128 / step), rows "
                "from north to south; add or remove values to fit");
        }
    }

    void checkWater()
    {
        const YAML::Node water = childOf(m_sketch, "water");
        const YAML::Node bodies = childOf(water, "bodies");

        for (size_t index = 0; bodies.IsSequence() && index < bodies.size(); ++index)
        {
            const YAML::Node body = bodies[index];
            const std::string path = itemPath("water.bodies", index);
            const std::string id = textOf(body, "id");
            need(id, {"space"}, path + ".id", "the water body");
            std::vector<Point2> polygon;
            double level = 0.0;

            if (!readPolygon(childOf(body, "polygon"), path + ".polygon", id, polygon)
                || !numberOf(body, "level", level))
            {
                continue;
            }

            for (const HeightPoint &point : m_heights)
            {
                if (point.height < level && !pointInPolygon(polygon, point.at, 0.0)
                    && outlineDistance(polygon, point.at) <= SketchShoreDistance)
                {
                    warn(path + ".level", "heights", "the water level " + formatNumber(level) + " of " + id
                        + " is above the ground on its shore: " + itemPath("heights.points", point.index)
                        + " gives " + formatNumber(point.height) + " at " + cellText(point.at) + "; lower the "
                        "level, raise that point, or move the outline away from it");
                }
            }
        }

        const YAML::Node rivers = childOf(water, "rivers");

        for (size_t index = 0; rivers.IsSequence() && index < rivers.size(); ++index)
        {
            const std::string path = itemPath("water.rivers", index);
            need(textOf(rivers[index], "id"), {"space", "link"}, path + ".id", "the river");
            std::vector<Point2> line;
            readLine(childOf(rivers[index], "line"), false, path + ".line", "the river", line);
        }

        const YAML::Node shores = childOf(water, "shores");

        for (size_t index = 0; shores.IsSequence() && index < shores.size(); ++index)
        {
            std::vector<Point2> line;
            readLine(childOf(shores[index], "line"), false, itemPath("water.shores", index) + ".line", "the shore",
                line);
        }
    }

    void checkRoads()
    {
        const YAML::Node roads = childOf(m_sketch, "roads");

        for (size_t index = 0; roads.IsSequence() && index < roads.size(); ++index)
        {
            const YAML::Node road = roads[index];
            const std::string path = itemPath("roads", index);
            const std::string id = textOf(road, "link");
            const bool known = need(id, {"link"}, path + ".link", "the road");
            std::vector<Point2> line;

            if (!readLine(childOf(road, "line"), true, path + ".line", "the line of " + id, line) || !known)
            {
                continue;
            }

            const YAML::Node link = m_entries.find(id)->second;

            for (const char *pEnd : {"from", "to"})
            {
                const std::string space = textOf(link, pEnd);
                const std::map<std::string, YAML::Node>::const_iterator entry = m_entries.find(space);

                if (entry == m_entries.end() || textOf(entry->second, "kind") != "junction")
                {
                    continue;
                }

                const std::map<std::string, std::vector<Point2>>::const_iterator placed = m_points.find(space);

                if (placed == m_points.end())
                {
                    warn(path + ".link", "coverage", "the link " + id + " runs " + pEnd + " the junction " + space
                        + ", which has no place in the sketch; add {id: " + space + ", at: [x, y]} to `points` "
                        "where the road meets it");
                    continue;
                }

                double best = 1.0e18;
                Point2 nearest = placed->second.front();

                for (const Point2 &point : placed->second)
                {
                    const double distance = lineDistance(line, point);

                    if (distance < best)
                    {
                        best = distance;
                        nearest = point;
                    }
                }

                if (best > SketchJunctionTolerance + Epsilon)
                {
                    add(path + ".line", "geometry", "the line of " + id + " misses the junction " + space + " (the "
                        "plan link's `" + pEnd + "`) at " + cellText(nearest) + " by "
                        + formatNumber(std::round(best * 10.0) / 10.0) + " cells; a road must pass within 1 cell "
                        "of each junction its link names: add the junction's point to the line, or move the point");
                }
            }
        }
    }

    void checkPlot(const YAML::Node &plot, const std::string &path, const std::string &space,
        const std::vector<Point2> &outline, std::vector<PlacedPlot> &placed)
    {
        const std::string id = textOf(plot, "building");
        const int index = integerOf(plot, "index", 0);
        const std::string name = id + (index > 0 ? " #" + std::to_string(index) : "");
        const bool known = need(id, {"building"}, path + ".building", "the plot");
        const std::string doorTo = textOf(plot, "door_to");

        if (!doorTo.empty())
        {
            need(doorTo, {"link", "space"}, path + ".door_to", "the plot's door_to");
        }

        Point2 at = {0.0, 0.0};
        const bool readable = pointOf(childOf(plot, "at"), at);

        if (readable)
        {
            checkCell(at, true, path + ".at", "the plot of " + name);
        }

        if (!known)
        {
            return;
        }

        const YAML::Node building = m_entries.find(id)->second;
        const int count = integerOf(building, "count", 1);

        if (m_buildingSpace[id] != space)
        {
            add(path + ".building", "reference", "the plot of " + name + " is drawn in " + space + ", and plan.yml "
                "lists that building under " + m_buildingSpace[id] + "; move the plot to that district");
        }

        if (count > 1 && (index < 1 || index > count))
        {
            add(path + (index > 0 ? ".index" : ""), "reference", id + " is a group of " + std::to_string(count)
                + " buildings; say which one this plot places with index: 1 to " + std::to_string(count));
            return;
        }

        if (count <= 1 && index > 1)
        {
            add(path + ".index", "reference", id + " is a single building in plan.yml; remove the index, or raise "
                "the building's count");
            return;
        }

        if (!m_plotted[id].insert(count > 1 ? index : 1).second)
        {
            add(path, "reference", name + " has two plots; remove one, or give the second its own index");
        }

        std::array<double, 4> rectangle = {0.0, 0.0, 0.0, 0.0};

        if (!readable || !sketchPlotRectangle(m_plan, plot, rectangle))
        {
            return;
        }

        if (!onStep(rectangle[2], 0.5) || !onStep(rectangle[3], 0.5))
        {
            add(path, "grid", "the footprint of " + name + " ends off the half-cell grid; give footprint_cells in "
                "half cells in plan.yml");
        }

        if (rectangle[2] > SketchMapCells || rectangle[3] > SketchMapCells)
        {
            add(path + ".at", "geometry", "the plot of " + name + " reaches past the map's edge; move it");
        }

        if (!outline.empty())
        {
            // Along the rectangle's rim every quarter cell, so an outline that bends into the plot is found too.
            bool outside = false;
            Point2 where = {0.0, 0.0};
            const double width = rectangle[2] - rectangle[0];
            const double depth = rectangle[3] - rectangle[1];
            const int stepsAcross = std::max(1, static_cast<int>(std::ceil(width * 4.0)));
            const int stepsDown = std::max(1, static_cast<int>(std::ceil(depth * 4.0)));

            for (int step = 0; step <= stepsAcross && !outside; ++step)
            {
                const double x = rectangle[0] + width * step / stepsAcross;

                for (const double y : {rectangle[1], rectangle[3]})
                {
                    if (!outside && !insideOrOn(outline, {x, y}))
                    {
                        outside = true;
                        where = {x, y};
                    }
                }
            }

            for (int step = 0; step <= stepsDown && !outside; ++step)
            {
                const double y = rectangle[1] + depth * step / stepsDown;

                for (const double x : {rectangle[0], rectangle[2]})
                {
                    if (!outside && !insideOrOn(outline, {x, y}))
                    {
                        outside = true;
                        where = {x, y};
                    }
                }
            }

            if (outside)
            {
                add(path + ".at", "geometry", "the plot of " + name + " covers x " + formatNumber(rectangle[0])
                    + " to " + formatNumber(rectangle[2]) + ", y " + formatNumber(rectangle[1]) + " to "
                    + formatNumber(rectangle[3]) + " and leaves the outline of " + space + " at " + cellText(where)
                    + "; move the plot, turn it, or widen the district's outline");
            }
        }

        for (const PlacedPlot &other : placed)
        {
            if (rectangle[0] < other.rectangle[2] - Epsilon && other.rectangle[0] < rectangle[2] - Epsilon
                && rectangle[1] < other.rectangle[3] - Epsilon && other.rectangle[1] < rectangle[3] - Epsilon)
            {
                add(path + ".at", "geometry", "the plots of " + name + " and " + other.name + " (" + other.path
                    + ") overlap: both cover x " + formatNumber(std::max(rectangle[0], other.rectangle[0])) + " to "
                    + formatNumber(std::min(rectangle[2], other.rectangle[2])) + ", y "
                    + formatNumber(std::max(rectangle[1], other.rectangle[1])) + " to "
                    + formatNumber(std::min(rectangle[3], other.rectangle[3])) + "; move one of them (`at` is the "
                    "north-west corner, the footprint is turned by `facing`)");
            }
        }

        placed.push_back({path, name, rectangle});
    }

    void checkDistricts()
    {
        const YAML::Node districts = childOf(m_sketch, "districts");
        std::vector<PlacedPlot> placed;
        std::set<std::string> drawn;

        for (size_t index = 0; districts.IsSequence() && index < districts.size(); ++index)
        {
            const YAML::Node district = districts[index];
            const std::string path = itemPath("districts", index);
            const std::string space = textOf(district, "space");
            need(space, {"space"}, path + ".space", "the district");

            if (!drawn.insert(space).second)
            {
                add(path + ".space", "reference", space + " has two outlines; a space has one district entry");
            }

            std::vector<Point2> outline;
            readPolygon(childOf(district, "polygon"), path + ".polygon", space, outline);
            const YAML::Node plots = childOf(district, "plots");

            if (plots.IsSequence() && plots.size() > 0)
            {
                m_plottedSpaces.emplace(space, path);
            }

            for (size_t plot = 0; plots.IsSequence() && plot < plots.size(); ++plot)
            {
                checkPlot(plots[plot], itemPath(path + ".plots", plot), space, outline, placed);
            }
        }
    }

    void checkAreas()
    {
        const YAML::Node areas = childOf(m_sketch, "areas");

        for (size_t index = 0; areas.IsSequence() && index < areas.size(); ++index)
        {
            const YAML::Node area = areas[index];
            const std::string path = itemPath("areas", index);
            const std::string id = textOf(area, "id");
            const std::string kind = textOf(area, "kind");

            if (kind.empty() || kind == "encounter")
            {
                need(id, {"population"}, path + ".id", "the encounter area");
            }
            else
            {
                need(id, {"population", "set piece", "space"}, path + ".id", "the " + kind + " area");
            }

            std::vector<Point2> polygon;
            const YAML::Node circle = childOf(area, "circle");

            if (childOf(area, "polygon").IsDefined())
            {
                readPolygon(childOf(area, "polygon"), path + ".polygon", "the area of " + id, polygon);
            }
            else if (circle.IsDefined())
            {
                Point2 at = {0.0, 0.0};

                if (pointOf(childOf(circle, "at"), at))
                {
                    checkCell(at, false, path + ".circle.at", "the area of " + id);
                }
            }
            else
            {
                add(path, "geometry", "the area of " + id + " has no shape; give it a polygon or a circle");
            }
        }
    }

    void checkViews()
    {
        const YAML::Node views = childOf(m_sketch, "views");

        for (size_t index = 0; views.IsSequence() && index < views.size(); ++index)
        {
            const YAML::Node view = views[index];
            const std::string path = itemPath("views", index);
            need(textOf(view, "id"), {"sightline", "landmark", "entrance", "point of interest"}, path + ".id",
                "the view");
            Point2 point = {0.0, 0.0};

            if (pointOf(childOf(view, "at"), point))
            {
                checkCell(point, false, path + ".at", "the view");
            }

            const bool hasLook = childOf(view, "look").IsDefined();

            if (hasLook && pointOf(childOf(view, "look"), point))
            {
                checkCell(point, false, path + ".look", "the view");
            }

            if (hasLook == childOf(view, "yaw").IsDefined())
            {
                add(path, "geometry", std::string("the view ") + (hasLook ? "has two directions" : "has no "
                    "direction") + "; give either look: [x, y] (the place it looks at) or yaw (compass degrees)");
            }
        }
    }

    void checkGround()
    {
        const YAML::Node ground = childOf(m_sketch, "ground");

        for (size_t index = 0; ground.IsSequence() && index < ground.size(); ++index)
        {
            // An area, or a strip along a line (core/OutdoorGround says when both or neither are given).
            if (childOf(ground[index], "line").IsDefined() && !childOf(ground[index], "polygon").IsDefined())
            {
                std::vector<Point2> line;
                readLine(childOf(ground[index], "line"), true, itemPath("ground", index) + ".line",
                    "the ground line " + textOf(ground[index], "material"), line);
                continue;
            }

            std::vector<Point2> polygon;
            readPolygon(childOf(ground[index], "polygon"), itemPath("ground", index) + ".polygon",
                "the ground zone " + textOf(ground[index], "material"), polygon);
        }
    }

    void checkCoverage()
    {
        const std::pair<const char *, const char *> located[] = {
            {"entrances", "entrance"}, {"points_of_interest", "point of interest"}, {"landmarks", "landmark"}};

        for (const std::pair<const char *, const char *> &list : located)
        {
            const YAML::Node entries = childOf(m_plan, list.first);

            for (size_t index = 0; entries.IsSequence() && index < entries.size(); ++index)
            {
                const std::string id = textOf(entries[index], "id");
                const std::map<std::string, std::vector<Point2>>::const_iterator placed = m_points.find(id);
                const size_t have = placed == m_points.end() ? 0 : placed->second.size();
                const size_t count = static_cast<size_t>(std::max(1, integerOf(entries[index], "count", 1)));

                if (have == 0)
                {
                    warn("points", "coverage", std::string("the plan's ") + list.second + " " + id + " has no place "
                        "in the sketch; add {id: " + id + ", at: [x, y]} to `points`");
                }
                else if (count > 1 && have != count)
                {
                    warn("points", "coverage", std::string("the plan's ") + list.second + " " + id + " has a count "
                        "of " + std::to_string(count) + " and " + std::to_string(have) + " points in the sketch; "
                        "give one point per member");
                }
            }
        }

        for (const std::pair<const std::string, std::string> &district : m_plottedSpaces)
        {
            const YAML::Node buildings = childOf(m_entries.contains(district.first)
                ? m_entries.find(district.first)->second : YAML::Node(YAML::NodeType::Undefined), "buildings");

            for (size_t index = 0; buildings.IsSequence() && index < buildings.size(); ++index)
            {
                const std::string id = textOf(buildings[index], "id");

                if (id.empty())
                {
                    continue;
                }

                const int count = integerOf(buildings[index], "count", 1);
                const std::set<int> &plotted = m_plotted[id];
                std::string missing;

                for (int member = 1; member <= count; ++member)
                {
                    if (!plotted.contains(member))
                    {
                        missing += (missing.empty() ? "" : ", ") + std::to_string(member);
                    }
                }

                if (missing.empty())
                {
                    continue;
                }

                warn(district.second + ".plots", "coverage", count > 1
                    ? "the group " + id + " has " + std::to_string(count) + " buildings in plan.yml and no plot "
                        "for index " + missing + "; add {building: " + id + ", index: n, at: [x, y], facing: s} "
                        "for each"
                    : "the building " + id + " of " + district.first + " has no plot; add {building: " + id
                        + ", at: [x, y], facing: s}");
            }
        }
    }

    std::vector<ProjectIssue> &m_issues;
    const YAML::Node m_card;
    const YAML::Node m_plan;
    const YAML::Node m_sketch;
    std::map<std::string, std::string> m_kinds;
    std::map<std::string, YAML::Node> m_entries;
    std::map<std::string, std::string> m_buildingSpace;
    // Neighbour id to its side in project.yml (empty when it has none).
    std::map<std::string, std::string> m_neighbours;
    std::map<std::string, std::vector<Point2>> m_points;
    std::vector<HeightPoint> m_heights;
    // Building id to the members that have a plot (1 for a single building).
    std::map<std::string, std::set<int>> m_plotted;
    // Spaces whose district has plots, with the district's path.
    std::map<std::string, std::string> m_plottedSpaces;
};
}

bool sketchPlotRectangle(const YAML::Node &plan, const YAML::Node &plot, std::array<double, 4> &rectangle)
{
    Point2 at = {0.0, 0.0};
    Point2 footprint = {0.0, 0.0};
    const std::string facing = textOf(plot, "facing");

    if (!pointOf(childOf(plot, "at"), at)
        || !footprintOf(findBuilding(plan, textOf(plot, "building")), integerOf(plot, "index", 0), footprint))
    {
        return false;
    }

    const bool frontAlongX = facing != "e" && facing != "w";
    rectangle = {at[0], at[1], at[0] + (frontAlongX ? footprint[0] : footprint[1]),
        at[1] + (frontAlongX ? footprint[1] : footprint[0])};
    return true;
}

void validateSketch(const Project &project, std::vector<ProjectIssue> &issues)
{
    if (!project.has(SketchFile))
    {
        return;
    }

    SketchCheck(project, issues).run();
}
}
