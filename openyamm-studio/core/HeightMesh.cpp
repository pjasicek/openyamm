#include "core/HeightMesh.h"

#include "core/CoreMath.h"

#include <algorithm>
#include <cmath>
#include <set>
#include <utility>

namespace OpenYAMM::Studio
{
namespace
{
// Two places closer than this are one; a point this close to a line lies on it.
constexpr double Near = 1.0e-6;

double orient(const Point2 &a, const Point2 &b, const Point2 &c)
{
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
}

double distance(const Point2 &a, const Point2 &b)
{
    return oy::hypot(b[0] - a[0], b[1] - a[1]);
}

// How far `c` lies to the left of the line from `a` to `b`, `length` long (distance(a, b), measured once by callers
// that ask about many points: the same numbers, fewer square roots).
double offLine(const Point2 &a, const Point2 &b, double length, const Point2 &c)
{
    return length < Near ? distance(a, c) : orient(a, b, c) / length;
}

double offLine(const Point2 &a, const Point2 &b, const Point2 &c)
{
    return offLine(a, b, distance(a, b), c);
}

// Whether `c` lies on the line from `a` to `b` (`length` long) between its ends, on neither of them.
bool onOpenSegment(const Point2 &a, const Point2 &b, double length, const Point2 &c)
{
    if (length < Near || std::abs(orient(a, b, c)) / length > Near)
    {
        return false;
    }

    const double along = ((c[0] - a[0]) * (b[0] - a[0]) + (c[1] - a[1]) * (b[1] - a[1])) / length;
    return along > Near && along < length - Near;
}

// Whether the line from `a` to `b` (`length` long) and the one from `c` to `d` cross at one place inside both of
// them; `at` receives the place. The second line is measured only when the first test leaves the answer open.
bool crossInside(const Point2 &a, const Point2 &b, double length, const Point2 &c, const Point2 &d,
    Point2 *pAt = nullptr)
{
    const double c1 = offLine(a, b, length, c);
    const double d1 = offLine(a, b, length, d);

    if (!((c1 > Near && d1 < -Near) || (c1 < -Near && d1 > Near)))
    {
        return false;
    }

    const double otherLength = distance(c, d);
    const double a2 = offLine(c, d, otherLength, a);
    const double b2 = offLine(c, d, otherLength, b);

    if (!((a2 > Near && b2 < -Near) || (a2 < -Near && b2 > Near)))
    {
        return false;
    }

    if (pAt != nullptr)
    {
        const double share = a2 / (a2 - b2);
        *pAt = {a[0] + (b[0] - a[0]) * share, a[1] + (b[1] - a[1]) * share};
    }

    return true;
}

struct Edge
{
    size_t first = 0;
    size_t second = 0;

    bool operator<(const Edge &other) const
    {
        return first != other.first ? first < other.first : second < other.second;
    }
};

Edge edgeOf(size_t first, size_t second)
{
    return first < second ? Edge{first, second} : Edge{second, first};
}
}

bool triangulateRegion(
    const std::vector<Point2> &ring,
    const std::vector<Point2> &points,
    const std::vector<std::array<Point2, 2>> &lines,
    std::vector<Point2> &vertices,
    std::vector<std::array<size_t, 3>> &triangles,
    std::string &error)
{
    vertices.clear();
    triangles.clear();

    if (ring.size() < 3 || polygonDoubleArea(ring) <= Near)
    {
        error = "the region has no area";
        return false;
    }

    const auto vertexOf = [&vertices](const Point2 &point)
    {
        for (size_t index = 0; index < vertices.size(); ++index)
        {
            if (distance(vertices[index], point) < Near)
            {
                return index;
            }
        }

        vertices.push_back(point);
        return vertices.size() - 1;
    };

    std::set<Edge> forced;

    for (size_t index = 0; index < ring.size(); ++index)
    {
        const size_t first = vertexOf(ring[index]);
        const size_t second = vertexOf(ring[(index + 1) % ring.size()]);

        if (first != second)
        {
            forced.insert(edgeOf(first, second));
        }
    }

    for (const Point2 &point : points)
    {
        if (pointInOrOnPolygon(ring, point))
        {
            vertexOf(point);
        }
    }

    for (const std::array<Point2, 2> &line : lines)
    {
        // An end outside the region is no point of the result: the line is cut where it leaves the region, and a
        // point is made there.
        const size_t first = vertexOf(line[0]);
        const size_t second = vertexOf(line[1]);

        if (first != second)
        {
            forced.insert(edgeOf(first, second));
        }
    }

    // Forced edges end at every point lying on them and where they cross one another. Each pass finds the first
    // such place in set order and only then changes the set: erasing inside the search would leave its iterators
    // dangling (S5 spike 4: incrementing an erased iterator crashed a long-lived wasm core).
    for (bool changed = true; changed;)
    {
        changed = false;
        Edge split = {};
        size_t splitAt = 0;

        for (std::set<Edge>::const_iterator edge = forced.begin(); edge != forced.end() && !changed; ++edge)
        {
            const double length = distance(vertices[edge->first], vertices[edge->second]);

            for (size_t index = 0; index < vertices.size() && !changed; ++index)
            {
                if (index != edge->first && index != edge->second
                    && onOpenSegment(vertices[edge->first], vertices[edge->second], length, vertices[index]))
                {
                    split = *edge;
                    splitAt = index;
                    changed = true;
                }
            }
        }

        if (changed)
        {
            forced.erase(split);
            forced.insert(edgeOf(split.first, splitAt));
            forced.insert(edgeOf(splitAt, split.second));
            continue;
        }

        Edge first = {};
        Edge second = {};
        Point2 at = {};

        for (std::set<Edge>::const_iterator one = forced.begin(); one != forced.end() && !changed; ++one)
        {
            const double length = distance(vertices[one->first], vertices[one->second]);

            for (std::set<Edge>::const_iterator other = std::next(one); other != forced.end() && !changed; ++other)
            {
                if (one->first == other->first || one->first == other->second || one->second == other->first
                    || one->second == other->second)
                {
                    continue;
                }

                if (crossInside(vertices[one->first], vertices[one->second], length, vertices[other->first],
                        vertices[other->second], &at))
                {
                    first = *one;
                    second = *other;
                    changed = true;
                }
            }
        }

        if (changed)
        {
            const size_t middle = vertexOf(at);
            forced.erase(first);
            forced.erase(second);

            for (const size_t end : {first.first, first.second, second.first, second.second})
            {
                if (end != middle)
                {
                    forced.insert(edgeOf(end, middle));
                }
            }
        }
    }

    // What lies outside the region is no part of it: points, and the pieces of lines.
    std::vector<bool> alive(vertices.size(), false);

    for (size_t index = 0; index < vertices.size(); ++index)
    {
        alive[index] = pointInOrOnPolygon(ring, vertices[index]);
    }

    std::vector<Edge> chosen;

    for (const Edge &edge : forced)
    {
        const Point2 middle = {
            (vertices[edge.first][0] + vertices[edge.second][0]) / 2.0,
            (vertices[edge.first][1] + vertices[edge.second][1]) / 2.0};

        if (alive[edge.first] && alive[edge.second] && pointInOrOnPolygon(ring, middle))
        {
            chosen.push_back(edge);
        }
    }

    // Every other edge that could be drawn: between two points that see each other inside the region.
    struct Candidate
    {
        double length = 0.0;
        Edge edge;
    };

    std::vector<Candidate> candidates;
    const std::set<Edge> chosenSet(chosen.begin(), chosen.end());

    for (size_t first = 0; first < vertices.size(); ++first)
    {
        for (size_t second = first + 1; second < vertices.size(); ++second)
        {
            if (!alive[first] || !alive[second] || chosenSet.contains({first, second}))
            {
                continue;
            }

            const Point2 &a = vertices[first];
            const Point2 &b = vertices[second];
            const Point2 middle = {(a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0};

            if (!pointInPolygon(ring, middle, Near))
            {
                continue;
            }

            bool clear = true;
            const double length = distance(a, b);

            for (size_t index = 0; index < vertices.size() && clear; ++index)
            {
                clear = index == first || index == second || !alive[index]
                    || !onOpenSegment(a, b, length, vertices[index]);
            }

            if (clear)
            {
                // Lengths that differ by a rounding error are equal: such edges keep the order of their points.
                candidates.push_back({std::round(length * 1.0e6), {first, second}});
            }
        }
    }

    std::stable_sort(candidates.begin(), candidates.end(), [](const Candidate &left, const Candidate &right)
    {
        return left.length < right.length;
    });

    for (const Candidate &candidate : candidates)
    {
        const Point2 &a = vertices[candidate.edge.first];
        const Point2 &b = vertices[candidate.edge.second];
        const double length = distance(a, b);
        bool clear = true;

        for (size_t index = 0; index < chosen.size() && clear; ++index)
        {
            const Edge &edge = chosen[index];
            clear = edge.first == candidate.edge.first || edge.first == candidate.edge.second
                || edge.second == candidate.edge.first || edge.second == candidate.edge.second
                || !crossInside(a, b, length, vertices[edge.first], vertices[edge.second]);
        }

        if (clear)
        {
            chosen.push_back(candidate.edge);
        }
    }

    // The triangles: three points joined to one another with nothing inside, lying in the region.
    std::vector<std::vector<size_t>> neighbours(vertices.size());

    for (const Edge &edge : chosen)
    {
        neighbours[edge.first].push_back(edge.second);
        neighbours[edge.second].push_back(edge.first);
    }

    for (std::vector<size_t> &list : neighbours)
    {
        std::sort(list.begin(), list.end());
    }

    const std::set<Edge> edges(chosen.begin(), chosen.end());
    double area = 0.0;

    for (size_t first = 0; first < vertices.size(); ++first)
    {
        for (const size_t second : neighbours[first])
        {
            if (second < first)
            {
                continue;
            }

            for (const size_t third : neighbours[second])
            {
                if (third < second || !edges.contains({first, third}))
                {
                    continue;
                }

                const Point2 &a = vertices[first];
                const Point2 &b = vertices[second];
                const Point2 &c = vertices[third];
                const double doubled = orient(a, b, c);
                const double longest = std::max(distance(a, b), std::max(distance(b, c), distance(c, a)));

                if (std::abs(doubled) / longest < Near)
                {
                    continue;
                }

                const Point2 centre = {(a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0};

                if (!pointInPolygon(ring, centre, 0.0))
                {
                    continue;
                }

                bool empty = true;

                for (size_t index = 0; index < vertices.size() && empty; ++index)
                {
                    if (index == first || index == second || index == third || !alive[index])
                    {
                        continue;
                    }

                    const Point2 &point = vertices[index];
                    const double sign = doubled > 0.0 ? 1.0 : -1.0;
                    empty = !(offLine(a, b, point) * sign > -Near && offLine(b, c, point) * sign > -Near
                        && offLine(c, a, point) * sign > -Near);
                }

                if (!empty)
                {
                    continue;
                }

                triangles.push_back(doubled > 0.0
                    ? std::array<size_t, 3>{first, second, third} : std::array<size_t, 3>{first, third, second});
                area += std::abs(doubled);
            }
        }
    }

    const double whole = polygonDoubleArea(ring);

    if (std::abs(area - whole) > 1.0e-6 * whole + 1.0)
    {
        error = "the triangles do not cover the region (points too close together, or lines that run along one "
            "another)";
        return false;
    }

    return true;
}

double meshHeightAt(const HeightMesh &mesh, double x, double y)
{
    double best = 0.0;
    double bestInside = -1.0e30;

    for (const std::array<size_t, 3> &triangle : mesh.triangles)
    {
        const std::array<double, 3> &a = mesh.points[triangle[0]];
        const std::array<double, 3> &b = mesh.points[triangle[1]];
        const std::array<double, 3> &c = mesh.points[triangle[2]];
        const double area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);

        if (std::abs(area) < 1.0e-9)
        {
            continue;
        }

        std::array<double, 3> weights = {
            ((b[0] - x) * (c[1] - y) - (b[1] - y) * (c[0] - x)) / area,
            ((c[0] - x) * (a[1] - y) - (c[1] - y) * (a[0] - x)) / area,
            0.0};
        weights[2] = 1.0 - weights[0] - weights[1];
        const double inside = std::min(weights[0], std::min(weights[1], weights[2]));

        if (inside <= bestInside)
        {
            continue;
        }

        const double total = std::clamp(weights[0], 0.0, 1.0) + std::clamp(weights[1], 0.0, 1.0)
            + std::clamp(weights[2], 0.0, 1.0);
        best = (std::clamp(weights[0], 0.0, 1.0) * a[2] + std::clamp(weights[1], 0.0, 1.0) * b[2]
            + std::clamp(weights[2], 0.0, 1.0) * c[2]) / total;
        bestInside = inside;

        if (inside >= -1.0e-9)
        {
            break;
        }
    }

    return std::abs(best - std::round(best)) < 1.0e-7 ? std::round(best) : best;
}

double meshLowest(const HeightMesh &mesh)
{
    double lowest = 0.0;

    for (size_t index = 0; index < mesh.points.size(); ++index)
    {
        lowest = index == 0 ? mesh.points[index][2] : std::min(lowest, mesh.points[index][2]);
    }

    return lowest;
}

double meshHighest(const HeightMesh &mesh)
{
    double highest = 0.0;

    for (size_t index = 0; index < mesh.points.size(); ++index)
    {
        highest = index == 0 ? mesh.points[index][2] : std::max(highest, mesh.points[index][2]);
    }

    return highest;
}

double meshTriangleGradient(const HeightMesh &mesh, size_t triangle)
{
    const std::array<double, 3> &a = mesh.points[mesh.triangles[triangle][0]];
    const std::array<double, 3> &b = mesh.points[mesh.triangles[triangle][1]];
    const std::array<double, 3> &c = mesh.points[mesh.triangles[triangle][2]];
    const std::array<double, 3> u = {b[0] - a[0], b[1] - a[1], b[2] - a[2]};
    const std::array<double, 3> v = {c[0] - a[0], c[1] - a[1], c[2] - a[2]};
    const double nx = u[1] * v[2] - u[2] * v[1];
    const double ny = u[2] * v[0] - u[0] * v[2];
    const double nz = u[0] * v[1] - u[1] * v[0];
    return std::abs(nz) < 1.0e-9 ? 1.0e9 : oy::hypot(nx, ny) / std::abs(nz);
}

std::vector<double> meshBreaksAlong(const HeightMesh &mesh, const Point2 &from, const Point2 &to)
{
    std::vector<double> breaks;
    const double length = distance(from, to);

    if (length < Near)
    {
        return breaks;
    }

    for (const std::array<double, 3> &point : mesh.points)
    {
        const Point2 place = {point[0], point[1]};

        if (onOpenSegment(from, to, length, place))
        {
            breaks.push_back(distance(from, place));
        }
    }

    for (const std::array<size_t, 3> &triangle : mesh.triangles)
    {
        for (size_t corner = 0; corner < 3; ++corner)
        {
            const std::array<double, 3> &first = mesh.points[triangle[corner]];
            const std::array<double, 3> &second = mesh.points[triangle[(corner + 1) % 3]];
            Point2 at = {};

            if (crossInside(from, to, length, {first[0], first[1]}, {second[0], second[1]}, &at))
            {
                breaks.push_back(distance(from, at));
            }
        }
    }

    std::sort(breaks.begin(), breaks.end());
    breaks.erase(
        std::unique(breaks.begin(), breaks.end(), [](double left, double right)
        {
            return std::abs(left - right) < Near;
        }),
        breaks.end());
    return breaks;
}

std::vector<std::vector<size_t>> mergeFlatTriangles(
    const std::vector<std::array<int64_t, 3>> &corners,
    const std::vector<std::array<size_t, 3>> &triangles,
    size_t maximumCorners)
{
    const auto turn = [&corners](size_t a, size_t b, size_t c)
    {
        return (corners[b][0] - corners[a][0]) * (corners[c][1] - corners[a][1])
            - (corners[b][1] - corners[a][1]) * (corners[c][0] - corners[a][0]);
    };
    std::vector<std::vector<size_t>> faces;
    // Each face's plane: a normal and a point of it.
    std::vector<std::array<int64_t, 3>> normals;

    for (const std::array<size_t, 3> &triangle : triangles)
    {
        const std::array<int64_t, 3> &a = corners[triangle[0]];
        const std::array<int64_t, 3> &b = corners[triangle[1]];
        const std::array<int64_t, 3> &c = corners[triangle[2]];
        const std::array<int64_t, 3> u = {b[0] - a[0], b[1] - a[1], b[2] - a[2]};
        const std::array<int64_t, 3> v = {c[0] - a[0], c[1] - a[1], c[2] - a[2]};
        const std::array<int64_t, 3> normal = {
            u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]};

        // Seen from above it must still run counter-clockwise once its corners stand on whole units.
        if (normal[2] <= 0)
        {
            continue;
        }

        faces.push_back({triangle[0], triangle[1], triangle[2]});
        normals.push_back(normal);
    }

    const auto inPlane = [&corners, &normals, &faces](size_t face, size_t point)
    {
        const std::array<int64_t, 3> &normal = normals[face];
        const std::array<int64_t, 3> &origin = corners[faces[face][0]];
        // The products pass 64 bits for large faces far from the origin: compared as long doubles they are exact
        // to 64 bits of mantissa, which whole-unit maps stay within.
        const long double off = static_cast<long double>(normal[0]) * (corners[point][0] - origin[0])
            + static_cast<long double>(normal[1]) * (corners[point][1] - origin[1])
            + static_cast<long double>(normal[2]) * (corners[point][2] - origin[2]);
        return off == 0.0L;
    };

    for (bool merged = true; merged;)
    {
        merged = false;

        // `!merged` is tested first in every loop: a merge erases `faces[other]`, which `second` names.
        for (size_t one = 0; !merged && one < faces.size(); ++one)
        {
            for (size_t other = one + 1; !merged && other < faces.size(); ++other)
            {
                const std::vector<size_t> &first = faces[one];
                const std::vector<size_t> &second = faces[other];

                for (size_t i = 0; !merged && i < first.size(); ++i)
                {
                    for (size_t j = 0; !merged && j < second.size(); ++j)
                    {
                        // An edge of the first, run the other way by the second.
                        if (first[i] != second[(j + 1) % second.size()]
                            || first[(i + 1) % first.size()] != second[j])
                        {
                            continue;
                        }

                        bool flat = true;

                        for (const size_t point : second)
                        {
                            flat = flat && inPlane(one, point);
                        }

                        if (!flat)
                        {
                            continue;
                        }

                        // Round the first from the edge's end to its start, then round the second from the edge's
                        // start (its own end) to the edge's end.
                        std::vector<size_t> joined;

                        for (size_t step = 0; step < first.size(); ++step)
                        {
                            joined.push_back(first[(i + 1 + step) % first.size()]);
                        }

                        for (size_t step = 1; step + 1 < second.size(); ++step)
                        {
                            joined.push_back(second[(j + 1 + step) % second.size()]);
                        }

                        // Where the two share more than one edge in a row, the ring runs out to a point between
                        // them and straight back: that point lies inside the joined face and is left out.
                        for (bool cut = true; cut && joined.size() > 3;)
                        {
                            cut = false;

                            for (size_t corner = 0; corner < joined.size() && !cut; ++corner)
                            {
                                const size_t next = (corner + 1) % joined.size();
                                const size_t after = (corner + 2) % joined.size();

                                if (joined[corner] == joined[after])
                                {
                                    // Remove the point between and one of the two equal ones.
                                    joined.erase(joined.begin() + static_cast<std::ptrdiff_t>(std::max(next, after)));
                                    joined.erase(joined.begin() + static_cast<std::ptrdiff_t>(std::min(next, after)));
                                    cut = true;
                                }
                            }
                        }

                        bool convex = joined.size() >= 3 && joined.size() <= maximumCorners;

                        for (size_t corner = 0; corner < joined.size() && convex; ++corner)
                        {
                            convex = turn(
                                joined[corner], joined[(corner + 1) % joined.size()],
                                joined[(corner + 2) % joined.size()]) >= 0;
                        }

                        // No point twice: two faces that share more than one edge would fold onto themselves.
                        std::vector<size_t> sorted = joined;
                        std::sort(sorted.begin(), sorted.end());
                        convex = convex && std::adjacent_find(sorted.begin(), sorted.end()) == sorted.end();

                        if (!convex)
                        {
                            continue;
                        }

                        faces[one] = joined;
                        faces.erase(faces.begin() + static_cast<std::ptrdiff_t>(other));
                        normals.erase(normals.begin() + static_cast<std::ptrdiff_t>(other));
                        merged = true;
                    }
                }
            }
        }
    }

    return faces;
}
}
