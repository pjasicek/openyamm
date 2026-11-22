#include "core/OutdoorWaysIn.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>

// How a way in is built, as the shipped maps build it.
//
// A cave mouth (Yaardrake's Cave, d49out_W and _W_1, measured 2026-11-14): a hollow shell of large triangles in the
// ground's own tile texture, no floor and no back, over a footprint 1024 square. Its front is a rim 72 thick round
// an arched mouth 828 wide and 720 high; a tunnel 292 deep narrows behind the mouth to one dark face (solid01) that
// carries the event into the dungeon, every other face the hint ("A Cave"). The shell's front corners and its sides
// up to half its depth lie at the floor; the sides then rise to the back edge, which lies at the crest (736 over the
// floor) all along. The land: the nodes under the mouth and the front at the floor, the back row at the crest, so
// the shell's edges lie on the land and the hill goes on behind it.
//
// So here: the mouth's outline (jambs and an arch head, `mouth.sides` segments) at `rim_depth` behind the front; the
// rim's outline round it at the front; the footprint's edge (front corners and sides at the floor up to the
// shoulder, then rising to the back edge at the crest; a free mound: at the floor all round). Between the rim's
// outline and the footprint's edge `rings` rings of points, matched point for point (both outlines cut at the same
// shares of their length), lifted into a mound and moved by `roughness` from a `seed`: the facets. Every face is a
// triangle, so moved points never bend one.
//
// A hatch's wedge (Ironsand's CoFent_S, 24 faces): the same with no rim and no rings: a lid in the ground tile from
// a low arched dark face at its front up to `height` (192) at its back, its sides sloping from the front corners.
// A hatch's pit (Ravage Roaming's d24entranceA, 13 faces): a square rim 64 high and 32 thick, its inner walls going
// down 16 to a dark face that carries the event.
//
// Arched heads (outc3 DunEntC3, oute2 archesN): the opening's face is the jambs and the head as one convex polygon;
// the corners of the panel above the head are faces of the wall round it.

namespace OpenYAMM::Studio
{
namespace
{
constexpr double Pi = 3.14159265358979323846;
constexpr int Nodes = 128;
constexpr double Cell = 512.0;
constexpr double Step = 32.0;
const char *SketchFile = "sketch.yml";

using Point3 = std::array<double, 3>;



bool numberOfNode(const YAML::Node &value, double &number)
{
    if (!value.IsDefined() || !value.IsScalar())
    {
        return false;
    }

    const std::string &text = value.Scalar();
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), number);
    return result.ec == std::errc() && result.ptr == text.data() + text.size() && std::isfinite(number);
}

double numberOr(const YAML::Node &node, const char *pKey, double fallback)
{
    double number = fallback;
    return numberOfNode(childOf(node, pKey), number) ? number : fallback;
}

// A cave point (across, back from the front, up from the floor) in world units.
Point3 toWorld(const OutdoorCavePlan &cave, const Point3 &local)
{
    const double angle = -cave.turn * Pi / 180.0;
    const double east = local[0];
    const double north = local[1] - cave.depth * 0.5;
    return {cave.x + east * oy::cos(angle) - north * oy::sin(angle),
        cave.y + east * oy::sin(angle) + north * oy::cos(angle), cave.floor + local[2]};
}

// A world place in the cave's own frame (across, back from the front).
std::array<double, 2> toLocal(const OutdoorCavePlan &cave, double x, double y)
{
    const double angle = -cave.turn * Pi / 180.0;
    const double dx = x - cave.x;
    const double dy = y - cave.y;
    return {dx * oy::cos(angle) + dy * oy::sin(angle), -dx * oy::sin(angle) + dy * oy::cos(angle)
        + cave.depth * 0.5};
}

struct CaveFace
{
    std::vector<Point3> points;
    // 0 the mound, 1 the rim, 2 the tunnel, 3 the door.
    int role = 0;
};

Point3 newell(const std::vector<Point3> &points)
{
    Point3 normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point3 &a = points[index];
        const Point3 &b = points[(index + 1) % points.size()];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    return normal;
}

// Adds a face wound to look along `toward` (counter-clockwise seen from that side).
void addFacing(std::vector<CaveFace> &faces, std::vector<Point3> points, const Point3 &toward, int role)
{
    const Point3 normal = newell(points);

    if (oy::hypot(normal[0], normal[1], normal[2]) < 1.0)
    {
        return;
    }

    if (normal[0] * toward[0] + normal[1] * toward[1] + normal[2] * toward[2] < 0.0)
    {
        std::reverse(points.begin(), points.end());
    }

    faces.push_back({points, role});
}

uint32_t nextRandom(uint32_t &state)
{
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state;
}

double randomShare(uint32_t &state)
{
    return (nextRandom(state) % 100000) / 50000.0 - 1.0;
}

std::vector<double> sharesOf(const std::vector<Point3> &line)
{
    std::vector<double> shares = {0.0};

    for (size_t index = 1; index < line.size(); ++index)
    {
        shares.push_back(shares.back() + oy::hypot(line[index][0] - line[index - 1][0],
            line[index][1] - line[index - 1][1], line[index][2] - line[index - 1][2]));
    }

    for (double &share : shares)
    {
        share /= std::max(shares.back(), 1.0e-9);
    }

    return shares;
}

Point3 alongLine(const std::vector<Point3> &line, const std::vector<double> &shares, double share)
{
    for (size_t index = 1; index < line.size(); ++index)
    {
        if (share <= shares[index] + 1.0e-12)
        {
            const double span = std::max(shares[index] - shares[index - 1], 1.0e-12);
            const double t = std::clamp((share - shares[index - 1]) / span, 0.0, 1.0);
            return {line[index - 1][0] + (line[index][0] - line[index - 1][0]) * t,
                line[index - 1][1] + (line[index][1] - line[index - 1][1]) * t,
                line[index - 1][2] + (line[index][2] - line[index - 1][2]) * t};
        }
    }

    return line.back();
}

// The opening's outline at the front plane: left foot, up the left jamb, the head, down to the right foot, as
// [across, up]; `grow` widens it on each side and over its head.
std::vector<std::array<double, 2>> openingOutline(const OutdoorCavePlan &cave, double grow)
{
    const double width = cave.mouthWidth + grow * 2.0;
    const double height = cave.mouthHeight + grow;
    std::vector<std::array<double, 2>> outline = {{-width * 0.5, 0.0}};

    if (cave.mouthSides < 2)
    {
        outline.push_back({-width * 0.5, height});
        outline.push_back({width * 0.5, height});
    }
    else
    {
        for (const std::array<double, 2> &point : outdoorArchHead(width, height, "round", cave.mouthSides))
        {
            outline.push_back(point);
        }
    }

    outline.push_back({width * 0.5, 0.0});
    return outline;
}

// The footprint's edge the shell's foot lies on, from the front-left corner round the back to the front-right.
std::vector<Point3> footprintEdge(const OutdoorCavePlan &cave)
{
    const double half = cave.width * 0.5;

    if (cave.free)
    {
        return {{-half, 0.0, 0.0}, {-half, cave.depth, 0.0}, {half, cave.depth, 0.0}, {half, 0.0, 0.0}};
    }

    std::vector<Point3> edge = {{-half, 0.0, 0.0}};

    if (cave.shoulder > 0.5)
    {
        edge.push_back({-half, cave.shoulder, 0.0});
    }

    edge.push_back({-half, cave.depth, cave.crest});
    edge.push_back({half, cave.depth, cave.crest});

    if (cave.shoulder > 0.5)
    {
        edge.push_back({half, cave.shoulder, 0.0});
    }

    edge.push_back({half, 0.0, 0.0});
    return edge;
}

// The faces of a cave mouth or a wedge, in the cave's own frame.
std::vector<CaveFace> caveFaces(const OutdoorCavePlan &cave)
{
    std::vector<CaveFace> faces;

    if (cave.kind == "hatch" && cave.form == "pit")
    {
        const double outer = 0.0;
        const double thick = cave.thickness;
        const double top = cave.crest;
        const double bottom = top - cave.mouthDepth;
        const double half = cave.width * 0.5;
        const std::vector<std::array<double, 2>> out = {{-half, outer}, {half, outer}, {half, cave.depth},
            {-half, cave.depth}};
        const std::vector<std::array<double, 2>> in = {{-half + thick, thick}, {half - thick, thick},
            {half - thick, cave.depth - thick}, {-half + thick, cave.depth - thick}};
        const double mid = cave.depth * 0.5;

        for (size_t side = 0; side < 4; ++side)
        {
            const size_t next = (side + 1) % 4;
            const Point3 outward = {out[side][0] + out[next][0], out[side][1] + out[next][1] - mid * 2.0, 0.0};
            addFacing(faces, {{out[side][0], out[side][1], -cave.skirt}, {out[next][0], out[next][1], -cave.skirt},
                {out[next][0], out[next][1], top}, {out[side][0], out[side][1], top}}, outward, 1);
            addFacing(faces, {{out[side][0], out[side][1], top}, {out[next][0], out[next][1], top},
                {in[next][0], in[next][1], top}, {in[side][0], in[side][1], top}}, {0.0, 0.0, 1.0}, 1);
            addFacing(faces, {{in[side][0], in[side][1], bottom}, {in[next][0], in[next][1], bottom},
                {in[next][0], in[next][1], top}, {in[side][0], in[side][1], top}},
                {-outward[0], -outward[1], 0.0}, 2);
        }

        addFacing(faces, {{in[0][0], in[0][1], bottom}, {in[1][0], in[1][1], bottom}, {in[2][0], in[2][1], bottom},
            {in[3][0], in[3][1], bottom}}, {0.0, 0.0, 1.0}, 3);
        return faces;
    }

    const std::vector<std::array<double, 2>> mouth = openingOutline(cave, 0.0);
    const std::vector<std::array<double, 2>> rim = openingOutline(cave, cave.rim);
    const size_t count = mouth.size();
    std::vector<Point3> front;
    std::vector<Point3> inner;
    std::vector<Point3> far;
    const double tunnelEnd = cave.rimDepth + cave.mouthDepth;

    const double back = cave.setback;
    const double up = cave.ledge;

    for (size_t index = 0; index < count; ++index)
    {
        front.push_back({rim[index][0], 0.0, (index == 0 || index + 1 == count ? 0.0 : up) + rim[index][1]});
        inner.push_back({mouth[index][0], back + cave.rimDepth, up + mouth[index][1]});
        far.push_back({mouth[index][0] * cave.narrow, back + tunnelEnd, up + mouth[index][1] * cave.narrow});
    }

    if (back > 0.5 && up > 0.5)
    {
        // The ledge: a ramp from the footprint's front up to the mouth's foot, closed at its sides.
        const double halfRim = rim.back()[0];
        addFacing(faces, {{-halfRim, 0.0, 0.0}, {halfRim, 0.0, 0.0}, {halfRim, back, up}, {-halfRim, back, up}},
            {0.0, -back, 1.0}, 4);

        for (const double end : {-1.0, 1.0})
        {
            addFacing(faces, {{end * halfRim, 0.0, 0.0}, {end * halfRim, back, 0.0}, {end * halfRim, back, up}},
                {end, 0.0, 0.0}, 4);
        }
    }

    // The rim: from its front outline back to the mouth.
    if (cave.rim > 0.5 || cave.rimDepth > 0.5)
    {
        for (size_t index = 0; index + 1 < count; ++index)
        {
            // Mirrored diagonals on the left half, as the mound's.
            if (front[index][0] + front[index + 1][0] < 0.0)
            {
                addFacing(faces, {front[index], front[index + 1], inner[index]}, {0.0, -1.0, 0.0}, 1);
                addFacing(faces, {front[index + 1], inner[index + 1], inner[index]}, {0.0, -1.0, 0.0}, 1);
            }
            else
            {
                addFacing(faces, {front[index], front[index + 1], inner[index + 1]}, {0.0, -1.0, 0.0}, 1);
                addFacing(faces, {front[index], inner[index + 1], inner[index]}, {0.0, -1.0, 0.0}, 1);
            }
        }
    }

    // The tunnel: its walls and roof look in.
    if (cave.mouthDepth > 0.5)
    {
        const double axis = cave.mouthHeight * 0.4;

        for (size_t index = 0; index + 1 < count; ++index)
        {
            const double middleZ = (inner[index][2] + inner[index + 1][2]) * 0.5;
            const double middleU = (inner[index][0] + inner[index + 1][0]) * 0.5;
            const Point3 in = {-middleU, 0.0, axis - middleZ};
            if (middleU < 0.0)
            {
                addFacing(faces, {inner[index], inner[index + 1], far[index]}, in, 2);
                addFacing(faces, {inner[index + 1], far[index + 1], far[index]}, in, 2);
            }
            else
            {
                addFacing(faces, {inner[index], inner[index + 1], far[index + 1]}, in, 2);
                addFacing(faces, {inner[index], far[index + 1], far[index]}, in, 2);
            }
        }
    }

    if (cave.form == "blocked")
    {
        // D-91: the mouth fallen in: a heap of rubble filling it at its face, from the mouth's outline to a crown
        // standing out before it at a third of its height, the heap's foot spilling out onto the floor.
        const std::vector<Point3> &face = cave.mouthDepth > 0.5 ? far : inner;
        const Point3 crown = {0.0, face[0][1] - std::min(96.0, cave.rimDepth + back + 32.0),
            up + cave.mouthHeight * 0.35};
        const Point3 spill = {0.0, std::max(0.0, face[0][1] - 128.0), 0.0};

        for (size_t index = 0; index + 1 < count; ++index)
        {
            addFacing(faces, {face[index], face[index + 1], crown}, {0.0, -1.0, 0.0}, 3);
        }

        addFacing(faces, {face.back(), spill, crown}, {1.0, -1.0, 0.0}, 3);
        addFacing(faces, {spill, face.front(), crown}, {-1.0, -1.0, 0.0}, 3);
    }
    else
    {
        // The dark face (or the door slab, a shelter's rock back) at the tunnel's end.
        addFacing(faces, cave.mouthDepth > 0.5 ? far : inner, {0.0, -1.0, 0.0}, 3);
    }

    // The mound: from the rim's front outline to the footprint's edge, cut at the same shares of their length.
    const std::vector<Point3> edge = footprintEdge(cave);
    const std::vector<double> frontShares = sharesOf(front);
    const std::vector<double> edgeShares = sharesOf(edge);
    std::vector<double> shares = frontShares;
    shares.insert(shares.end(), edgeShares.begin(), edgeShares.end());
    std::sort(shares.begin(), shares.end());
    shares.erase(std::unique(shares.begin(), shares.end(), [](double a, double b)
    {
        return std::fabs(a - b) < 1.0e-4;
    }), shares.end());
    const int rings = std::max(0, cave.rings);
    const double outerTop = cave.mouthHeight + cave.rim;
    const double lift = cave.free ? std::max(0.0, cave.crest - outerTop * 0.5) : 48.0;
    uint32_t state = cave.seed * 2654435761u + 0x9e3779b9u;

    for (const char character : cave.id)
    {
        state = state * 31u + static_cast<unsigned char>(character);
    }

    state = state == 0 ? 1u : state;
    std::vector<std::vector<Point3>> grid(static_cast<size_t>(rings) + 2);

    for (const double share : shares)
    {
        const Point3 from = alongLine(front, frontShares, share);
        const Point3 to = alongLine(edge, edgeShares, share);
        const double weight = std::clamp(std::max(std::fabs(to[1] - from[1]) / (cave.depth * 0.5), 0.3), 0.0, 1.0);

        for (int ring = 0; ring <= rings + 1; ++ring)
        {
            const double s = static_cast<double>(ring) / (rings + 1);
            Point3 point = {from[0] + (to[0] - from[0]) * s, from[1] + (to[1] - from[1]) * s,
                from[2] + (to[2] - from[2]) * s + lift * oy::sin(Pi * s) * (cave.free ? weight : 1.0 - weight)};

            if (!cave.free && ring > 0 && ring <= rings)
            {
                // Against a hill the inner rings lie on a rounded rock shell: across the footprint a flat-topped
                // curve (a superellipse of power 3) from the crest over the middle down to the floor at the sides,
                // so the shell reads as a hood of rock, not a slab from the rim to the back edge.
                // From the rim's top at the front it reaches the crest a quarter of the depth back, so no fin
                // stands over the arch.
                const double across = std::min(1.0, std::fabs(point[0]) / (cave.width * 0.5));
                const double rimTop = outerTop + cave.ledge;
                const double reach = std::clamp(point[1] / (cave.depth * 0.25), 0.0, 1.0);
                const double hood = std::min(cave.crest, rimTop + (cave.crest - rimTop) * reach);
                point[2] = std::max(point[2], hood * oy::cbrt(std::max(0.0, 1.0 - across * across * across)));
            }

            if (ring > 0 && ring <= rings && cave.roughness > 0.0)
            {
                point[0] += randomShare(state) * cave.roughness * 48.0;
                point[1] += randomShare(state) * cave.roughness * 48.0;
                point[2] += randomShare(state) * cave.roughness * 64.0;
                point[2] = std::max(point[2], 16.0);
            }

            // Inside the footprint, and (against a hill) never over the crest: the back edge is the top.
            point[0] = std::clamp(point[0], -cave.width * 0.5, cave.width * 0.5);
            point[1] = std::clamp(point[1], 0.0, cave.depth);

            if (!cave.free)
            {
                point[2] = std::min(point[2], cave.crest);
            }

            grid[static_cast<size_t>(ring)].push_back(point);
        }
    }

    for (size_t ring = 0; ring + 1 < grid.size(); ++ring)
    {
        for (size_t index = 0; index + 1 < shares.size(); ++index)
        {
            const Point3 &a = grid[ring][index];
            const Point3 &b = grid[ring][index + 1];
            const Point3 &c = grid[ring + 1][index + 1];
            const Point3 &d = grid[ring + 1][index];
            const auto outward = [&cave](const Point3 &p, const Point3 &q, const Point3 &r)
            {
                return Point3{(p[0] + q[0] + r[0]) / 3.0 * 0.5, (p[1] + q[1] + r[1]) / 3.0 - cave.depth * 0.5,
                    (p[2] + q[2] + r[2]) / 3.0 + cave.depth};
            };
            // The left half splits its quads on the mirrored diagonal, so both ends of the front close alike: one
            // diagonal everywhere gave the right end an upright cheek and laid a left-end triangle along the land's
            // front edge and through the hill at the jamb (X1's shaft-head hatch).
            if (grid[0][index][0] + grid[0][index + 1][0] < 0.0)
            {
                addFacing(faces, {a, b, d}, outward(a, b, d), 0);
                addFacing(faces, {b, c, d}, outward(b, c, d), 0);
            }
            else
            {
                addFacing(faces, {a, b, c}, outward(a, b, c), 0);
                addFacing(faces, {a, c, d}, outward(a, c, d), 0);
            }
        }
    }

    return faces;
}

// The lowest shell over a place of the cave's frame; infinity where none lies over it.
double shellOver(const std::vector<CaveFace> &faces, double u, double v)
{
    double lowest = std::numeric_limits<double>::infinity();

    for (const CaveFace &face : faces)
    {
        if (face.role > 1 || face.points.size() != 3)
        {
            continue;
        }

        const Point3 &a = face.points[0];
        const Point3 &b = face.points[1];
        const Point3 &c = face.points[2];
        const double area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);

        if (std::fabs(area) < 1.0)
        {
            continue;
        }

        const double wb = ((u - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (v - a[1])) / area;
        const double wc = ((b[0] - a[0]) * (v - a[1]) - (u - a[0]) * (b[1] - a[1])) / area;
        const double wa = 1.0 - wb - wc;

        if (wa >= -1.0e-6 && wb >= -1.0e-6 && wc >= -1.0e-6)
        {
            lowest = std::min(lowest, wa * a[2] + wb * b[2] + wc * c[2]);
        }
    }

    return lowest;
}

// The shell's highest point over a place of the footprint (its top seen from above); -infinity where none.
double shellTop(const std::vector<CaveFace> &faces, double u, double v)
{
    double highest = -std::numeric_limits<double>::infinity();

    for (const CaveFace &face : faces)
    {
        if (face.role > 1 || face.points.size() != 3)
        {
            continue;
        }

        const Point3 &a = face.points[0];
        const Point3 &b = face.points[1];
        const Point3 &c = face.points[2];
        const double area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);

        if (std::fabs(area) < 1.0)
        {
            continue;
        }

        const double wb = ((u - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (v - a[1])) / area;
        const double wc = ((b[0] - a[0]) * (v - a[1]) - (u - a[0]) * (b[1] - a[1])) / area;
        const double wa = 1.0 - wb - wc;

        if (wa >= -1.0e-6 && wb >= -1.0e-6 && wc >= -1.0e-6)
        {
            highest = std::max(highest, wa * a[2] + wb * b[2] + wc * c[2]);
        }
    }

    return highest;
}
}

std::vector<std::array<double, 2>> outdoorArchHead(double width, double height, const std::string &form, int sides,
    double rise)
{
    const int segments = std::clamp(sides, 2, 16);
    const double half = width * 0.5;
    std::vector<std::array<double, 2>> head;

    if (form == "segment")
    {
        // An arc of a circle through both springs and the crown, flatter than a half circle: `rise` over the
        // springs (a quarter of the width when not given: an arc of about 106 degrees), never more than half the
        // width (a half circle) or the opening's height.
        const double up = std::min({rise > 0.0 ? rise : width * 0.25, half, height});
        const double radius = (half * half + up * up) / (2.0 * up);
        const double centre = height - radius;
        const double reach = oy::asin(std::clamp(half / radius, -1.0, 1.0));

        for (int index = 0; index <= segments; ++index)
        {
            const double angle = -reach + 2.0 * reach * index / segments;
            head.push_back({radius * oy::sin(angle), centre + radius * oy::cos(angle)});
        }

        head.front() = {-half, height - up};
        head.back() = {half, height - up};
        return head;
    }

    if (form == "pointed")
    {
        const double full = width * std::sqrt(3.0) * 0.5;
        const double up = std::min(full, height);
        const double squash = up / full;
        const int perSide = std::max(1, segments / 2);

        for (int index = 0; index <= perSide; ++index)
        {
            const double angle = Pi - (Pi / 3.0) * index / perSide;
            head.push_back({half + width * oy::cos(angle), height - up + width * oy::sin(angle) * squash});
        }

        for (int index = perSide - 1; index >= 0; --index)
        {
            head.push_back({-head[static_cast<size_t>(index)][0], head[static_cast<size_t>(index)][1]});
        }

        return head;
    }

    const double up = std::min(half, height);

    for (int index = 0; index <= segments; ++index)
    {
        const double angle = Pi - Pi * index / segments;
        head.push_back({half * oy::cos(angle), height - up + up * oy::sin(angle)});
    }

    return head;
}

std::vector<OutdoorCavePlan> readOutdoorCaves(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues)
{
    std::vector<OutdoorCavePlan> caves;
    const YAML::Node structures = childOf(project.document(SketchFile), "structures");
    const std::string ground = world == "mm6" ? "6dirttyl" : world == "mm7" ? "7dirttyl" : "dirttyl";
    const std::string dark = world == "mm6" ? "solid10" : world == "mm7" ? "7solid01" : "solid01";
    const std::string carved = world == "mm6" ? "tewd" : world == "mm7" ? "hhm1d" : "t14c03";

    for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size(); ++index)
    {
        const YAML::Node node = structures[index];
        const std::string kind = textOf(node, "kind");

        if (kind != "cave_mouth" && kind != "hatch")
        {
            continue;
        }

        OutdoorCavePlan cave;
        cave.id = textOf(node, "id");
        cave.path = "structures[" + std::to_string(index) + "]";
        cave.kind = kind;
        const auto add = [&](const std::string &where, const std::string &message)
        {
            issues.push_back({SketchFile, cave.path + where, message, "structure"});
        };
        const YAML::Node at = childOf(node, "at");
        double cellX = 0.0;
        double cellY = 0.0;

        if (!at.IsDefined() || !at.IsSequence() || at.size() != 2 || !numberOfNode(at[0], cellX)
            || !numberOfNode(at[1], cellY) || cellX < 0.0 || cellY < 0.0 || cellX > Nodes - 1 || cellY > Nodes - 1)
        {
            add(".at", "`at` is the middle of the footprint [x, y] in cells (fractions allowed), inside the map");
            continue;
        }

        cave.x = (cellX - Nodes / 2) * Cell;
        cave.y = (Nodes / 2 - cellY) * Cell;
        cave.turn = numberOr(node, "turn", 0.0);
        const YAML::Node mouth = childOf(node, "mouth");
        const YAML::Node size = childOf(node, "size");
        const bool pit = kind == "hatch" && textOf(node, "form", "wedge") == "pit";
        cave.form = kind == "hatch" ? textOf(node, "form", "wedge") : "";

        if (kind == "hatch" && cave.form != "wedge" && cave.form != "pit")
        {
            add(".form", "a hatch's form is wedge (a sloping lid with a dark mouth at its low front) or pit (a "
                "rim round a dark shaft)");
            continue;
        }

        const double defaultSize = kind == "cave_mouth" ? 1024.0 : pit ? 320.0 : 512.0;
        cave.width = defaultSize;
        cave.depth = defaultSize;

        if (size.IsDefined() && (!size.IsSequence() || size.size() != 2 || !numberOfNode(size[0], cave.width)
            || !numberOfNode(size[1], cave.depth)))
        {
            add(".size", "`size` is the footprint [across the mouth, front to back] in map units");
            continue;
        }

        cave.floorGiven = childOf(node, "floor").IsDefined();
        cave.floor = numberOr(node, "floor", 0.0);
        cave.shellTexture = textOf(childOf(node, "textures"), "shell", ground);
        cave.seed = static_cast<uint32_t>(std::max(0.0, numberOr(node, "seed", 0.0)));
        cave.free = textOf(node, "free") == "true";

        if (kind == "hatch")
        {
            cave.roughness = numberOr(node, "roughness", 0.0);
            cave.rings = 0;
            cave.rim = 0.0;
            cave.rimDepth = 0.0;
            cave.narrow = 1.0;
            cave.shoulder = 0.0;
            cave.crest = numberOr(node, "height", pit ? 64.0 : 192.0);
            cave.mouthWidth = numberOr(mouth, "width", cave.width - 64.0);
            cave.mouthHeight = numberOr(mouth, "height", cave.crest * 0.75);
            cave.mouthDepth = numberOr(mouth, "depth", pit ? 16.0 : 24.0);
            cave.mouthSides = static_cast<int>(numberOr(mouth, "sides", 4.0));
            cave.thickness = numberOr(node, "thickness", 32.0);
            cave.doorTexture = textOf(childOf(node, "textures"), "door", dark);

            if (cave.free)
            {
                add(".free", "`free` is a cave mouth's word (a barrow on level land); a hatch's pit stands free "
                    "already");
                continue;
            }

            if (cave.width < 128.0 || cave.width > 4096.0 || cave.depth < 128.0 || cave.depth > 4096.0
                || cave.crest < 16.0 || cave.crest > 1024.0)
            {
                add("", "a hatch's `size` is 128 to 4096 each way and its `height` 16 to 1024 (a wedge's back over "
                    "its front: 192; a pit's rim: 64)");
                continue;
            }

            if (pit && (cave.thickness < 8.0 || cave.thickness * 2.0 > std::min(cave.width, cave.depth) - 64.0
                || cave.mouthDepth < 4.0 || cave.mouthDepth > cave.crest + 512.0))
            {
                add("", "a pit's rim is 8 thick or more and leaves a shaft at least 64 across; its dark face lies "
                    "`mouth.depth` (16) below the rim's top");
                continue;
            }

            if (!pit && (cave.mouthWidth < 64.0 || cave.mouthWidth > cave.width || cave.mouthHeight < 32.0
                || cave.mouthHeight > cave.crest || cave.mouthDepth < 0.0 || cave.mouthDepth > cave.depth * 0.5))
            {
                add(".mouth", "a wedge's mouth is 64 wide up to the lid's width, 32 high up to its `height`, and "
                    "its dark face lies 0 to half the lid's depth back");
                continue;
            }

            caves.push_back(cave);
            continue;
        }

        cave.mouthForm = textOf(mouth, "form", "arch");
        cave.form = textOf(node, "form");
        cave.leadsIn = childOf(node, "into").IsDefined();

        if (cave.mouthForm != "arch" && cave.mouthForm != "door")
        {
            add(".mouth.form", "a cave mouth is an open dark `arch` (the default) or a flat front with a `door` slab");
            continue;
        }

        // D-91: a mouth that leads nowhere is a shelter (a shallow open overhang, its back and floor in sight) or
        // blocked (rubble fills it at its face).
        if ((!cave.form.empty() && cave.form != "shelter" && cave.form != "blocked")
            || (!cave.form.empty() && (cave.leadsIn || cave.mouthForm == "door")))
        {
            add(".form", "a cave mouth's `form` is shelter (a shallow open overhang, its rock back lit) or blocked "
                "(rubble fills the mouth at its face), for a mouth that leads nowhere: not with `into` or a door "
                "slab (`mouth.form: door`)");
            continue;
        }

        const bool door = cave.mouthForm == "door";
        const bool shelter = cave.form == "shelter";
        const bool blocked = cave.form == "blocked";
        cave.mouthWidth = numberOr(mouth, "width", door ? 192.0 : 512.0);
        cave.mouthHeight = numberOr(mouth, "height", door ? 320.0 : 384.0);
        cave.mouthDepth = numberOr(mouth, "depth", door ? 16.0 : shelter ? 160.0 : blocked ? 0.0 : 256.0);
        cave.mouthSides = static_cast<int>(numberOr(mouth, "sides", door ? 0.0 : 6.0));
        cave.rim = numberOr(mouth, "rim", door ? 128.0 : 72.0);
        cave.rimDepth = door ? 0.0 : std::min(72.0, cave.rim);
        cave.narrow = door ? 1.0 : shelter ? 0.95 : 0.85;
        cave.setback = numberOr(mouth, "setback", 0.0);
        cave.ledge = numberOr(mouth, "ledge", 0.0);
        cave.ledgeTexture = textOf(childOf(node, "textures"), "ledge", ground);
        cave.crest = numberOr(node, "crest", cave.mouthHeight + cave.rim + cave.ledge + 64.0);
        cave.roughness = numberOr(node, "roughness", 0.5);
        // A shelter's back and a blocked mouth's rubble are the shell's rock unless `textures.door` says.
        cave.doorTexture = textOf(childOf(node, "textures"), "door", door ? carved : shelter || blocked
            ? cave.shellTexture : dark);

        if (cave.width < 256.0 || cave.width > 8192.0 || cave.depth < 256.0 || cave.depth > 8192.0)
        {
            add(".size", "a cave mouth's footprint is 256 to 8192 each way ([1024, 1024] when left out)");
            continue;
        }

        if (cave.mouthWidth < 64.0 || cave.mouthHeight < 64.0 || cave.mouthWidth + cave.rim * 2.0 > cave.width
            || cave.rim < 0.0 || cave.rim > 512.0 || cave.mouthSides < 0 || cave.mouthSides > 16)
        {
            add(".mouth", "the mouth is at least 64 wide and high, its rim 0 to 512, and the mouth with its rim "
                "fits the footprint's width (" + formatNumber(cave.width) + "); `sides` 0 (a flat head) to 16");
            continue;
        }

        if (cave.crest < cave.mouthHeight + cave.rim || cave.crest > 4096.0)
        {
            add(".crest", "the crest stands over the mouth and its rim (at least " + formatNumber(cave.mouthHeight
                + cave.rim) + " over the floor) and at most 4096");
            continue;
        }

        if (cave.mouthDepth < 0.0 || cave.setback + cave.rimDepth + cave.mouthDepth > cave.depth * 0.75)
        {
            add(".mouth.depth", "the tunnel (with the mouth's `setback`) reaches at most three quarters of the "
                "footprint's depth back");
            continue;
        }

        if (cave.setback < 0.0 || cave.setback > cave.depth * 0.5 || cave.ledge < 0.0
            || cave.ledge > cave.mouthHeight * 0.5 || (cave.ledge > 0.0 && cave.setback < 32.0)
            || cave.crest < cave.mouthHeight + cave.rim + cave.ledge)
        {
            add(".mouth.setback", "the mouth stands `setback` 0 to half the footprint's depth behind its front, its "
                "foot `ledge` 0 to half the mouth's height over the floor (a ledge needs a setback of 32 or more for "
                "its ramp), and the crest over the ledge, the mouth and its rim");
            continue;
        }

        if (cave.roughness < 0.0 || cave.roughness > 1.0)
        {
            add(".roughness", "roughness is 0 (smooth) to 1 (the most facets)");
            continue;
        }

        // The sides lie at the floor up to the first node line at or past half the depth and the tunnel's end.
        const double reach = std::max(cave.depth * 0.5, cave.setback + cave.rimDepth + cave.mouthDepth);
        cave.shoulder = std::ceil(reach / Cell - 1.0e-6) * Cell;

        if (cave.shoulder >= cave.depth - 1.0)
        {
            cave.shoulder = reach;
        }

        caves.push_back(cave);
    }

    return caves;
}

void shapeOutdoorCaveLand(
    std::vector<OutdoorCavePlan> &caves,
    std::vector<double> &ground,
    const std::vector<double> &waterNode,
    std::vector<std::string> &warnings)
{
    for (OutdoorCavePlan &cave : caves)
    {
        const bool pit = cave.kind == "hatch" && cave.form == "pit";

        // The land at a place of the cave's frame, between the nodes.
        const auto landAt = [&ground, &cave](double u, double v)
        {
            const Point3 place = toWorld(cave, {u, v, 0.0});
            const double fx = std::clamp(place[0] / Cell + Nodes / 2, 0.0, Nodes - 1.0);
            const double fy = std::clamp(Nodes / 2 - place[1] / Cell, 0.0, Nodes - 1.0);
            const int x0 = std::min(Nodes - 2, static_cast<int>(fx));
            const int y0 = std::min(Nodes - 2, static_cast<int>(fy));
            const double tx = fx - x0;
            const double ty = fy - y0;
            const auto at = [&ground](int x, int y)
            {
                return ground[static_cast<size_t>(y) * Nodes + x];
            };
            return (at(x0, y0) * (1 - tx) + at(x0 + 1, y0) * tx) * (1 - ty)
                + (at(x0, y0 + 1) * (1 - tx) + at(x0 + 1, y0 + 1) * tx) * ty;
        };

        if (!cave.floorGiven)
        {
            // The land at the middle of the front (of the footprint, for a pit).
            cave.floor = landAt(0.0, pit ? cave.depth * 0.5 : 0.0);
        }

        cave.floor = std::round(cave.floor / Step) * Step;
        cave.crest = std::round(cave.crest / Step) * Step;
        const double half = cave.width * 0.5;

        if (pit)
        {
            for (const double u : {-half, half})
            {
                for (const double v : {0.0, cave.depth})
                {
                    cave.skirt = std::max(cave.skirt, std::ceil((cave.floor - landAt(u, v)) / Step) * Step);
                }
            }
        }

        const std::vector<CaveFace> faces = caveFaces(cave);
        // F8: a cave mouth into a hill is covered by the land round its sides and back.
        const bool buried = cave.kind == "cave_mouth" && !cave.free;
        const double tunnelEnd = cave.setback + cave.rimDepth + cave.mouthDepth;

        // The highest a node may stand over the floor so that the land in the mouth (and its tunnel) stays within
        // a step of the floor: the ground of a cell is two triangles of its corners, so a corner weighs at most
        // 1 - min(across, along) / Cell at a place of the cell.
        const auto capAt = [&cave, tunnelEnd](double u, double v)
        {
            double cap = std::numeric_limits<double>::infinity();

            for (double pu = -cave.mouthWidth * 0.5; pu <= cave.mouthWidth * 0.5 + 0.5; pu += Step)
            {
                for (double pv = 0.0; pv <= tunnelEnd + 0.5; pv += Step)
                {
                    const double across = std::fabs(pu - u) / Cell;
                    const double along = std::fabs(pv - v) / Cell;
                    const double weight = across < 1.0 && along < 1.0 ? 1.0 - std::min(across, along) : 0.0;

                    if (weight > 1.0e-3)
                    {
                        cap = std::min(cap, Step / weight);
                    }
                }
            }

            return cap;
        };
        // The shell's highest point over the cells round a node.
        const auto coverAt = [&cave, &faces, half](double u, double v)
        {
            double cover = 0.0;

            for (double su = std::max(-half, u - Cell); su <= std::min(half, u + Cell) + 0.5; su += 64.0)
            {
                for (double sv = std::max(0.0, v - Cell); sv <= std::min(cave.depth, v + Cell) + 0.5; sv += 64.0)
                {
                    const double top = shellTop(faces, std::clamp(su, -half, half), std::min(sv, cave.depth));
                    cover = std::isfinite(top) ? std::max(cover, top) : cover;
                }
            }

            return std::min(cover, cave.crest);
        };
        size_t lowBehind = 0;
        double lowest = std::numeric_limits<double>::infinity();
        size_t wet = 0;
        bool offNodes = false;

        for (const std::array<double, 2> &corner : std::vector<std::array<double, 2>>{{-half, 0.0}, {half, 0.0},
                 {-half, cave.depth}, {half, cave.depth}})
        {
            const Point3 place = toWorld(cave, {corner[0], corner[1], 0.0});
            offNodes = offNodes || std::fabs(place[0] / Cell - std::round(place[0] / Cell)) > 0.01
                || std::fabs(place[1] / Cell - std::round(place[1] / Cell)) > 0.01;
        }

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                const size_t node = static_cast<size_t>(y) * Nodes + x;
                const std::array<double, 2> local = toLocal(cave, (x - Nodes / 2) * Cell, (Nodes / 2 - y) * Cell);
                const double u = local[0];
                const double v = local[1];
                constexpr double Near = 1.0;

                if (!pit && !buried && !cave.free && std::fabs(u) <= half + Near && v > cave.depth + Cell - Near
                    && v < cave.depth + Cell + Near && ground[node] < cave.floor + cave.crest - 64.0)
                {
                    ++lowBehind;
                    lowest = std::min(lowest, ground[node]);
                }

                if (std::fabs(u) > half + Near || v < -Near || v > cave.depth + Near)
                {
                    // F8: one cell beyond the sides and the back the land rises to the shell near it.
                    if (buried && std::isnan(waterNode[node]) && v > Near && std::fabs(u) < half + Cell + Near
                        && v < cave.depth + Cell + Near)
                    {
                        const double cover = std::min(coverAt(u, v), capAt(u, v));
                        ground[node] = std::max(ground[node], cave.floor + std::floor(cover / Step) * Step);
                    }

                    continue;
                }

                if (!std::isnan(waterNode[node]))
                {
                    ++wet;
                    continue;
                }

                if (pit || cave.free)
                {
                    ground[node] = cave.floor;
                    continue;
                }

                // The sides' profile: the floor up to the shoulder, then rising to the crest at the back.
                const double rise = v <= cave.shoulder ? 0.0
                    : cave.crest * std::min(1.0, (v - cave.shoulder) / std::max(cave.depth - cave.shoulder, 1.0));
                const bool edge = std::fabs(u) > half - Near || v < Near || v > cave.depth - Near;
                double height = v > cave.depth - Near ? cave.crest : rise;

                if (!edge)
                {
                    // Under the shell: below it, up to the profile where the land is lower; a hillside between
                    // stays as it is, and where the hill already stands over the shell it stays and the shell lies
                    // buried in it (Emerald Island's Dragon Cave on its slope).
                    const double shell = shellOver(faces, u, v);
                    const double land = ground[node] - cave.floor;

                    if (land >= shell + 32.0)
                    {
                        continue;
                    }

                    height = std::max(0.0, std::min(std::max(rise, land), shell - 32.0));
                }
                else if (buried && v > Near)
                {
                    // F8: the side and back edges: a hill over the profile stays, and the land rises to the shell
                    // near it, as far as the mouth's floor allows.
                    const double cap = capAt(u, v);
                    height = std::max(height, std::min(ground[node] - cave.floor, cap));
                    height = std::max(height, std::floor(std::min(coverAt(u, v), cap) / Step) * Step);

                    if (ground[node] >= cave.floor + height - 0.5 && ground[node] <= cave.floor + cap + 0.5)
                    {
                        continue;
                    }
                }
                else if (height > 0.5 && ground[node] > cave.floor + height)
                {
                    // The rising side and back edges: a hill higher than the profile stays.
                    continue;
                }

                ground[node] = cave.floor + std::round(height / Step) * Step;
            }
        }

        // F8: how far the shell stands over the land beside it (its wings beside the rim) and behind it (its dome),
        // and D-91: a dark mouth that leads nowhere.
        if (buried)
        {
            const double rimHalf = cave.mouthWidth * 0.5 + cave.rim;
            double wings = 0.0;
            double dome = 0.0;

            for (double u = -half; u <= half + 0.5; u += 64.0)
            {
                for (double v = 0.0; v <= cave.depth + 0.5; v += 64.0)
                {
                    const double top = shellTop(faces, std::min(u, half), std::min(v, cave.depth));

                    if (!std::isfinite(top))
                    {
                        continue;
                    }

                    if (std::fabs(u) > rimHalf + 16.0 && v <= std::min(cave.shoulder, cave.depth))
                    {
                        wings = std::max(wings, top - (landAt(u < 0.0 ? -half - 64.0 : half + 64.0, v) - cave.floor));
                    }

                    if (v > tunnelEnd + 32.0)
                    {
                        dome = std::max(dome, top - (landAt(u, cave.depth + 64.0) - cave.floor));
                    }
                }
            }

            if (wings > 64.0)
            {
                warnings.push_back(cave.path + ": caves.wings: the shell of " + cave.id + " stands "
                    + formatNumber(std::round(wings)) + " over the land beside it, rock wings beside its rim: make "
                    "the footprint as wide as the mouth and its rim (`size` " + formatNumber(rimHalf * 2.0)
                    + " across) or raise the land beside it");
            }

            if (dome > 64.0)
            {
                warnings.push_back(cave.path + ": caves.dome: the shell of " + cave.id + " stands "
                    + formatNumber(std::round(dome)) + " over the land behind it: raise the land behind it, lower "
                    "`crest`, or say `free: true` for a mound on level land");
            }
        }

        if (cave.kind == "cave_mouth" && !cave.leadsIn && cave.form.empty())
        {
            warnings.push_back(cave.path + ": caves.blind_mouth: " + cave.id + " shows a dark way in that leads "
                "nowhere: give it `into`, or `form: shelter` (an open overhang with its back lit) or `form: blocked` "
                "(rubble fills it) and a click line (D-91)");
        }

        if (lowBehind != 0)
        {
            warnings.push_back(cave.path + ": the land behind the " + (cave.kind == "hatch" ? "hatch" : "cave mouth")
                + " " + cave.id + " lies lower than its crest (" + formatNumber(cave.floor + cave.crest)
                + ") at " + std::to_string(lowBehind) + " nodes (lowest " + formatNumber(std::round(lowest))
                + "): its back edge stands as a step; raise the land behind it, lower `crest`, or say `free: true`");
        }

        if (wet != 0)
        {
            warnings.push_back(cave.path + ": " + std::to_string(wet) + " nodes under " + cave.id + " lie in water "
                "and keep the water's level");
        }

        if (offNodes)
        {
            warnings.push_back(cave.path + ": the corners of " + cave.id + " lie between the land's nodes, so its "
                "edges may stand off the land: put `at` on whole or half cells, `size` in 512s and `turn` on a "
                "right angle");
        }
    }
}

void raiseOutdoorCave(
    const OutdoorCavePlan &cave,
    OutdoorModelBuilder &builder,
    uint16_t event,
    std::vector<int> &doorFaces)
{
    const std::vector<CaveFace> faces = caveFaces(cave);
    const bool slab = cave.mouthForm == "door";

    for (const CaveFace &face : faces)
    {
        std::vector<OutdoorModelPoint> points;

        for (const Point3 &point : face.points)
        {
            points.push_back(toWorld(cave, point));
        }

        if (face.role == 3 && slab)
        {
            // The door slab: its picture fills the opening.
            std::vector<std::array<double, 2>> texels;

            for (const Point3 &point : face.points)
            {
                texels.push_back({(point[0] + cave.mouthWidth * 0.5) * 128.0 / cave.mouthWidth,
                    (cave.mouthHeight - point[2]) * 256.0 / cave.mouthHeight});
            }

            const int number = builder.addFace(points, cave.doorTexture, texels, event);
            doorFaces.push_back(number);
            continue;
        }

        const int number = builder.addSurface(points, face.role == 3 ? cave.doorTexture : face.role == 4
            ? cave.ledgeTexture : cave.shellTexture, event);

        if (face.role == 3 && number >= 0)
        {
            doorFaces.push_back(number);
        }
    }
}
}
