#include "core/Polygon.h"

#include "core/CoreMath.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Studio
{
namespace
{
constexpr double Tiny = 1.0e-7;

double cross(const Point2 &origin, const Point2 &first, const Point2 &second)
{
    return (first[0] - origin[0]) * (second[1] - origin[1]) - (first[1] - origin[1]) * (second[0] - origin[0]);
}

bool onSegment(const Point2 &first, const Point2 &second, const Point2 &point)
{
    return std::abs(cross(first, second, point)) <= Tiny
        && point[0] >= std::min(first[0], second[0]) - Tiny && point[0] <= std::max(first[0], second[0]) + Tiny
        && point[1] >= std::min(first[1], second[1]) - Tiny && point[1] <= std::max(first[1], second[1]) + Tiny;
}

bool segmentsTouch(const Point2 &a, const Point2 &b, const Point2 &c, const Point2 &d)
{
    const double d1 = cross(a, b, c);
    const double d2 = cross(a, b, d);
    const double d3 = cross(c, d, a);
    const double d4 = cross(c, d, b);

    if (((d1 > Tiny && d2 < -Tiny) || (d1 < -Tiny && d2 > Tiny))
        && ((d3 > Tiny && d4 < -Tiny) || (d3 < -Tiny && d4 > Tiny)))
    {
        return true;
    }

    return onSegment(a, b, c) || onSegment(a, b, d) || onSegment(c, d, a) || onSegment(c, d, b);
}

double distanceToSegment(const Point2 &first, const Point2 &second, const Point2 &point)
{
    const double dx = second[0] - first[0];
    const double dy = second[1] - first[1];
    const double lengthSquared = dx * dx + dy * dy;
    double along =
        lengthSquared > 0.0 ? ((point[0] - first[0]) * dx + (point[1] - first[1]) * dy) / lengthSquared : 0.0;
    along = std::clamp(along, 0.0, 1.0);
    return oy::hypot(point[0] - (first[0] + dx * along), point[1] - (first[1] + dy * along));
}

// Whether `point` is inside or on the triangle.
bool inTriangle(const Point2 &a, const Point2 &b, const Point2 &c, const Point2 &point)
{
    return cross(a, b, point) >= -Tiny && cross(b, c, point) >= -Tiny && cross(c, a, point) >= -Tiny;
}

bool isConvexRing(const std::vector<Point2> &points, const std::vector<size_t> &ring)
{
    for (size_t index = 0; index < ring.size(); ++index)
    {
        if (cross(points[ring[index]], points[ring[(index + 1) % ring.size()]],
                points[ring[(index + 2) % ring.size()]]) < -Tiny)
        {
            return false;
        }
    }

    return true;
}

double ringDoubleArea(const std::vector<Point2> &points, const std::vector<size_t> &ring)
{
    double area = 0.0;

    for (size_t index = 0; index < ring.size(); ++index)
    {
        const Point2 &current = points[ring[index]];
        const Point2 &next = points[ring[(index + 1) % ring.size()]];
        area += current[0] * next[1] - next[0] * current[1];
    }

    return area;
}
}

double polygonDoubleArea(const std::vector<Point2> &points)
{
    double area = 0.0;

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point2 &current = points[index];
        const Point2 &next = points[(index + 1) % points.size()];
        area += current[0] * next[1] - next[0] * current[1];
    }

    return area;
}

bool polygonIsSimple(const std::vector<Point2> &points)
{
    const size_t count = points.size();

    if (count < 3)
    {
        return false;
    }

    for (size_t first = 0; first < count; ++first)
    {
        const Point2 &a = points[first];
        const Point2 &b = points[(first + 1) % count];

        if (oy::hypot(b[0] - a[0], b[1] - a[1]) <= Tiny)
        {
            return false;
        }

        for (size_t second = first + 1; second < count; ++second)
        {
            const bool neighbours = second == first + 1 || (first == 0 && second == count - 1);
            const Point2 &c = points[second];
            const Point2 &d = points[(second + 1) % count];

            if (neighbours)
            {
                // Neighbours share one corner; they may not fold back onto each other.
                const bool consecutive = second == first + 1;
                const Point2 &shared = consecutive ? b : a;
                const Point2 &start = consecutive ? a : c;
                const Point2 &end = consecutive ? d : b;

                if (std::abs(cross(start, shared, end)) <= Tiny
                    && (start[0] - shared[0]) * (end[0] - shared[0])
                        + (start[1] - shared[1]) * (end[1] - shared[1]) > 0.0)
                {
                    return false;
                }

                continue;
            }

            if (segmentsTouch(a, b, c, d))
            {
                return false;
            }
        }
    }

    return true;
}

bool pointInPolygon(const std::vector<Point2> &points, const Point2 &point, double margin)
{
    bool inside = false;
    const size_t count = points.size();

    for (size_t index = 0; index < count; ++index)
    {
        const Point2 &a = points[index];
        const Point2 &b = points[(index + 1) % count];

        if ((a[1] > point[1]) != (b[1] > point[1])
            && point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0])
        {
            inside = !inside;
        }
    }

    // A point within the margin of an edge is not inside: asked only of a point inside, the answer is the same and
    // an outside point costs no distances (S8f: the indoor lowering asks this of every candidate edge's middle).
    if (!inside)
    {
        return false;
    }

    for (size_t index = 0; index < count; ++index)
    {
        if (distanceToSegment(points[index], points[(index + 1) % count], point) <= margin)
        {
            return false;
        }
    }

    return true;
}

bool pointInOrOnPolygon(const std::vector<Point2> &points, const Point2 &point)
{
    for (size_t index = 0; index < points.size(); ++index)
    {
        if (distanceToSegment(points[index], points[(index + 1) % points.size()], point) <= 1.0e-6)
        {
            return true;
        }
    }

    return pointInPolygon(points, point, 0.0);
}

std::vector<std::vector<size_t>> convexPieces(const std::vector<Point2> &points, size_t maximumCorners)
{
    std::vector<std::vector<size_t>> pieces;

    if (points.size() < 3 || polygonDoubleArea(points) <= Tiny)
    {
        return pieces;
    }

    // Ear clipping. A corner is an ear when it turns left and no other remaining point lies in or on its triangle;
    // points in a line are never ears and are reached when their neighbours have been cut away.
    std::vector<size_t> ring(points.size());

    for (size_t index = 0; index < ring.size(); ++index)
    {
        ring[index] = index;
    }

    while (ring.size() > 3)
    {
        bool cut = false;

        for (size_t index = 0; index < ring.size(); ++index)
        {
            const size_t previous = ring[(index + ring.size() - 1) % ring.size()];
            const size_t current = ring[index];
            const size_t next = ring[(index + 1) % ring.size()];

            if (cross(points[previous], points[current], points[next]) <= Tiny)
            {
                continue;
            }

            bool blocked = false;

            // A ring with holes cut into it visits its bridge points twice: a point standing exactly on one of
            // the ear's own corners does not block it.
            const auto same = [&points](size_t first, size_t second)
            {
                return std::abs(points[first][0] - points[second][0]) <= Tiny
                    && std::abs(points[first][1] - points[second][1]) <= Tiny;
            };

            for (const size_t other : ring)
            {
                if (other != previous && other != current && other != next
                    && inTriangle(points[previous], points[current], points[next], points[other])
                    && !same(other, previous) && !same(other, current) && !same(other, next))
                {
                    blocked = true;
                    break;
                }
            }

            if (blocked)
            {
                continue;
            }

            pieces.push_back({previous, current, next});
            ring.erase(ring.begin() + static_cast<std::ptrdiff_t>(index));
            cut = true;
            break;
        }

        if (!cut)
        {
            return {};
        }
    }

    if (cross(points[ring[0]], points[ring[1]], points[ring[2]]) <= Tiny)
    {
        return {};
    }

    pieces.push_back(ring);

    // Join pieces across a shared edge while the result stays convex and small enough.
    bool joined = true;

    while (joined)
    {
        joined = false;

        for (size_t first = 0; first < pieces.size() && !joined; ++first)
        {
            for (size_t second = first + 1; second < pieces.size() && !joined; ++second)
            {
                const std::vector<size_t> &a = pieces[first];
                const std::vector<size_t> &b = pieces[second];

                if (a.size() + b.size() - 2 > maximumCorners)
                {
                    continue;
                }

                for (size_t i = 0; i < a.size() && !joined; ++i)
                {
                    for (size_t j = 0; j < b.size(); ++j)
                    {
                        if (a[i] != b[(j + 1) % b.size()] || a[(i + 1) % a.size()] != b[j])
                        {
                            continue;
                        }

                        // a: ... a[i] -> a[i+1] ...; b runs the same edge the other way.
                        std::vector<size_t> merged;

                        for (size_t step = 1; step <= a.size(); ++step)
                        {
                            merged.push_back(a[(i + step) % a.size()]);
                        }

                        for (size_t step = 2; step < b.size(); ++step)
                        {
                            merged.push_back(b[(j + step) % b.size()]);
                        }

                        if (isConvexRing(points, merged))
                        {
                            pieces[first] = merged;
                            pieces.erase(pieces.begin() + static_cast<std::ptrdiff_t>(second));
                            joined = true;
                        }

                        break;
                    }
                }
            }
        }
    }

    return pieces;
}

std::vector<Point2> cutHole(
    const std::vector<Point2> &outer,
    const std::vector<Point2> &hole,
    const std::vector<std::vector<Point2>> &keepClear)
{
    // The shortest bridge between a point of the outer ring and a point of the hole that crosses no edge of
    // either.
    const auto crossesAny = [&outer, &hole](const Point2 &from, const Point2 &to)
    {
        for (const std::vector<Point2> *pRing : {&outer, &hole})
        {
            for (size_t index = 0; index < pRing->size(); ++index)
            {
                const Point2 &a = (*pRing)[index];
                const Point2 &b = (*pRing)[(index + 1) % pRing->size()];
                const auto equal = [](const Point2 &left, const Point2 &right)
                {
                    return std::abs(left[0] - right[0]) <= Tiny && std::abs(left[1] - right[1]) <= Tiny;
                };

                if (equal(a, from) || equal(b, from) || equal(a, to) || equal(b, to))
                {
                    // An edge that starts or ends at the bridge's end may only touch it there.
                    const Point2 &other = equal(a, from) || equal(a, to) ? b : a;

                    if (onSegment(from, to, other))
                    {
                        return true;
                    }

                    continue;
                }

                if (segmentsTouch(from, to, a, b))
                {
                    return true;
                }
            }
        }

        return false;
    };
    // A ring that already has a hole visits the ends of that hole's bridge twice, once on each side of the bridge.
    // A new bridge must leave such a point on the side of the visit it is tied into: within the corner the ring
    // turns through there (from the edge that leaves the point counter-clockwise round to the edge that arrives).
    const auto leavesInside = [&outer](size_t index, const Point2 &to)
    {
        const Point2 &corner = outer[index];
        const Point2 &next = outer[(index + 1) % outer.size()];
        const Point2 &previous = outer[(index + outer.size() - 1) % outer.size()];
        const double afterNext = cross(corner, next, to);
        const double beforePrevious = cross(corner, to, previous);
        return cross(corner, next, previous) > Tiny
            ? afterNext > Tiny && beforePrevious > Tiny
            : afterNext > Tiny || beforePrevious > Tiny;
    };
    // Whether a bridge would run through a hole that is still to be cut (that hole could then not be cut any more).
    const auto crossesLater = [&keepClear](const Point2 &from, const Point2 &to)
    {
        for (const std::vector<Point2> &later : keepClear)
        {
            for (size_t index = 0; index < later.size(); ++index)
            {
                if (segmentsTouch(from, to, later[index], later[(index + 1) % later.size()]))
                {
                    return true;
                }
            }
        }

        return false;
    };
    double best = -1.0;
    size_t outerIndex = 0;
    size_t holeIndex = 0;

    // First a bridge clear of the later holes; when there is none, any bridge.
    for (const bool clearOfLater : {true, false})
    {
        if (best >= 0.0 || (!clearOfLater && keepClear.empty()))
        {
            break;
        }

        for (size_t i = 0; i < outer.size(); ++i)
        {
            for (size_t j = 0; j < hole.size(); ++j)
            {
                const double distance = oy::hypot(outer[i][0] - hole[j][0], outer[i][1] - hole[j][1]);

                if ((best < 0.0 || distance < best) && distance > Tiny && leavesInside(i, hole[j])
                    && !crossesAny(outer[i], hole[j]) && !(clearOfLater && crossesLater(outer[i], hole[j])))
                {
                    best = distance;
                    outerIndex = i;
                    holeIndex = j;
                }
            }
        }
    }

    if (best < 0.0)
    {
        return {};
    }

    std::vector<Point2> ring(outer.begin(), outer.begin() + static_cast<std::ptrdiff_t>(outerIndex) + 1);

    // Round the hole clockwise (the floor is on its outside), back to where the bridge landed.
    for (size_t step = 0; step <= hole.size(); ++step)
    {
        ring.push_back(hole[(holeIndex + hole.size() - step % hole.size()) % hole.size()]);
    }

    ring.insert(ring.end(), outer.begin() + static_cast<std::ptrdiff_t>(outerIndex), outer.end());
    return ring;
}

std::vector<Point2> clipConvex(const std::vector<Point2> &points, const Point2 &normal, double offset)
{
    std::vector<Point2> result;

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point2 &current = points[index];
        const Point2 &next = points[(index + 1) % points.size()];
        const double currentSide = current[0] * normal[0] + current[1] * normal[1] - offset;
        const double nextSide = next[0] * normal[0] + next[1] * normal[1] - offset;

        if (currentSide <= Tiny)
        {
            result.push_back(current);
        }

        if ((currentSide < -Tiny && nextSide > Tiny) || (currentSide > Tiny && nextSide < -Tiny))
        {
            const double along = currentSide / (currentSide - nextSide);
            result.push_back(
                {current[0] + (next[0] - current[0]) * along, current[1] + (next[1] - current[1]) * along});
        }
    }

    return result;
}

bool polygonsOverlap(const std::vector<Point2> &first, const std::vector<Point2> &second)
{
    if (first.empty() || second.empty())
    {
        return false;
    }

    // Outlines whose boxes share no area share none either (what is shared lies inside both boxes): the common case
    // of rooms apart, settled without cutting either into pieces.
    const auto box = [](const std::vector<Point2> &points)
    {
        std::array<double, 4> bounds = {points[0][0], points[0][1], points[0][0], points[0][1]};

        for (const Point2 &point : points)
        {
            bounds[0] = std::min(bounds[0], point[0]);
            bounds[1] = std::min(bounds[1], point[1]);
            bounds[2] = std::max(bounds[2], point[0]);
            bounds[3] = std::max(bounds[3], point[1]);
        }

        return bounds;
    };
    const std::array<double, 4> a = box(first);
    const std::array<double, 4> b = box(second);

    if (a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1])
    {
        return false;
    }

    const std::vector<std::vector<size_t>> firstPieces = convexPieces(first, 64);
    const std::vector<std::vector<size_t>> secondPieces = convexPieces(second, 64);

    for (const std::vector<size_t> &a : firstPieces)
    {
        for (const std::vector<size_t> &b : secondPieces)
        {
            std::vector<Point2> shared;

            for (const size_t index : a)
            {
                shared.push_back(first[index]);
            }

            for (size_t edge = 0; edge < b.size() && shared.size() >= 3; ++edge)
            {
                const Point2 &start = second[b[edge]];
                const Point2 &end = second[b[(edge + 1) % b.size()]];
                // Outward normal of a counter-clockwise edge.
                const Point2 normal = {end[1] - start[1], start[0] - end[0]};
                shared = clipConvex(shared, normal, start[0] * normal[0] + start[1] * normal[1]);
            }

            if (shared.size() >= 3 && polygonDoubleArea(shared) > 2.0)
            {
                return true;
            }
        }
    }

    return false;
}

Point2 polygonInteriorPoint(const std::vector<Point2> &points)
{
    const std::vector<std::vector<size_t>> pieces = convexPieces(points, 64);
    Point2 best = points.empty() ? Point2{0.0, 0.0} : points[0];
    double bestArea = 0.0;

    for (const std::vector<size_t> &piece : pieces)
    {
        const double area = ringDoubleArea(points, piece);

        if (area > bestArea)
        {
            // The area centroid of the piece.
            double x = 0.0;
            double y = 0.0;

            for (size_t index = 0; index < piece.size(); ++index)
            {
                const Point2 &current = points[piece[index]];
                const Point2 &next = points[piece[(index + 1) % piece.size()]];
                const double weight = current[0] * next[1] - next[0] * current[1];
                x += (current[0] + next[0]) * weight;
                y += (current[1] + next[1]) * weight;
            }

            bestArea = area;
            best = {x / (3.0 * area), y / (3.0 * area)};
        }
    }

    return best;
}

std::vector<Point2> pathOutline(const std::vector<Point2> &path, double width, std::string &error)
{
    if (path.size() < 2 || width <= 0.0)
    {
        error = "a path needs at least two points and a width";
        return {};
    }

    const double half = width / 2.0;
    std::vector<Point2> right;
    std::vector<Point2> left;

    for (size_t index = 0; index < path.size(); ++index)
    {
        // The directions of the segments before and after this point (the same at the ends).
        const Point2 &here = path[index];
        const Point2 &before = path[index == 0 ? 0 : index - 1];
        const Point2 &after = path[index + 1 == path.size() ? index : index + 1];
        Point2 in = {here[0] - before[0], here[1] - before[1]};
        Point2 out = {after[0] - here[0], after[1] - here[1]};

        if (index == 0)
        {
            in = out;
        }

        if (index + 1 == path.size())
        {
            out = in;
        }

        const double inLength = oy::hypot(in[0], in[1]);
        const double outLength = oy::hypot(out[0], out[1]);

        // Short segments are fine on a gentle curve; a bend too tight for the width shows as an outline that
        // crosses itself, which is checked at the end.
        if (inLength < 1.0 || outLength < 1.0)
        {
            error = "the path repeats a point";
            return {};
        }

        in = {in[0] / inLength, in[1] / inLength};
        out = {out[0] / outLength, out[1] / outLength};
        // The mitre: along the bisector of the two right-hand normals, long enough to keep the width.
        const Point2 inNormal = {in[1], -in[0]};
        const Point2 outNormal = {out[1], -out[0]};
        Point2 mitre = {inNormal[0] + outNormal[0], inNormal[1] + outNormal[1]};
        const double mitreLength = oy::hypot(mitre[0], mitre[1]);

        if (mitreLength < 0.5)
        {
            error = "the path turns back on itself (a bend sharper than about 150 degrees)";
            return {};
        }

        mitre = {mitre[0] / mitreLength, mitre[1] / mitreLength};
        const double reach = half / (mitre[0] * inNormal[0] + mitre[1] * inNormal[1]);
        right.push_back({std::round(here[0] + mitre[0] * reach), std::round(here[1] + mitre[1] * reach)});
        left.push_back({std::round(here[0] - mitre[0] * reach), std::round(here[1] - mitre[1] * reach)});
    }

    // Counter-clockwise: the room lies on the left of each edge, so forward along the right side and back along the
    // left.
    std::vector<Point2> outline = right;
    outline.insert(outline.end(), left.rbegin(), left.rend());

    if (!polygonIsSimple(outline) || polygonDoubleArea(outline) <= 0.0)
    {
        error = "the widened path crosses itself: its bends are too close together for its width";
        return {};
    }

    return outline;
}

namespace
{
bool samePoint(const Point2 &first, const Point2 &second)
{
    return std::abs(first[0] - second[0]) < 1.0e-6 && std::abs(first[1] - second[1]) < 1.0e-6;
}

// The polygon with every corner of `other` that lies inside one of its edges added there.
std::vector<Point2> withCornersOf(const std::vector<Point2> &polygon, const std::vector<Point2> &other)
{
    std::vector<Point2> result;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point2 &from = polygon[index];
        const Point2 &to = polygon[(index + 1) % polygon.size()];
        const double dx = to[0] - from[0];
        const double dy = to[1] - from[1];
        const double length = dx * dx + dy * dy;
        std::vector<std::pair<double, Point2>> inside;
        result.push_back(from);

        for (const Point2 &point : other)
        {
            const double along = ((point[0] - from[0]) * dx + (point[1] - from[1]) * dy) / length;
            const double off = (point[0] - from[0]) * dy - (point[1] - from[1]) * dx;

            if (length > 0.0 && std::abs(off) < 1.0e-6 * std::sqrt(length) && along > 1.0e-9 && along < 1.0 - 1.0e-9)
            {
                inside.push_back({along, point});
            }
        }

        std::sort(inside.begin(), inside.end(), [](const auto &left, const auto &right)
        {
            return left.first < right.first;
        });

        for (const std::pair<double, Point2> &point : inside)
        {
            result.push_back(point.second);
        }
    }

    return result;
}
}

std::vector<Point2> unionTouching(const std::vector<Point2> &first, const std::vector<Point2> &second)
{
    if (first.size() < 3 || second.size() < 3)
    {
        return {};
    }

    std::vector<Point2> outline = withCornersOf(first, second);
    const std::vector<Point2> other = withCornersOf(second, first);
    bool joined = false;

    // A shared edge runs one way round the first and the other way round the second: splice the second in there.
    for (size_t index = 0; index < outline.size() && !joined; ++index)
    {
        const Point2 from = outline[index];
        const Point2 to = outline[(index + 1) % outline.size()];

        for (size_t otherIndex = 0; otherIndex < other.size() && !joined; ++otherIndex)
        {
            if (!samePoint(other[otherIndex], to) || !samePoint(other[(otherIndex + 1) % other.size()], from))
            {
                continue;
            }

            std::vector<Point2> spliced;

            for (size_t step = 0; step < outline.size(); ++step)
            {
                spliced.push_back(outline[(index + 1 + step) % outline.size()]);
            }

            for (size_t step = 2; step < other.size(); ++step)
            {
                spliced.push_back(other[(otherIndex + step) % other.size()]);
            }

            outline = spliced;
            joined = true;
        }
    }

    if (!joined)
    {
        return {};
    }

    // Further shared edges leave spikes (a corner whose neighbours are one point): fold them away, then drop corners
    // in a straight line.
    bool changed = true;

    while (changed && outline.size() >= 3)
    {
        changed = false;

        for (size_t index = 0; index < outline.size() && outline.size() >= 3; ++index)
        {
            const Point2 &previous = outline[(index + outline.size() - 1) % outline.size()];
            const Point2 &current = outline[index];
            const Point2 &next = outline[(index + 1) % outline.size()];
            const double cross = (current[0] - previous[0]) * (next[1] - current[1])
                - (current[1] - previous[1]) * (next[0] - current[0]);

            // Decided before the erase: `previous` and `next` refer into `outline`.
            const bool spike = samePoint(previous, next);

            if (spike || samePoint(previous, current) || std::abs(cross) < 1.0e-9)
            {
                outline.erase(outline.begin() + static_cast<std::ptrdiff_t>(index));

                if (spike && outline.size() >= 2)
                {
                    // The spike's foot is now doubled.
                    const size_t foot = index % outline.size();
                    outline.erase(outline.begin() + static_cast<std::ptrdiff_t>(foot));
                }

                changed = true;
                break;
            }
        }
    }

    const double expected = polygonDoubleArea(first) + polygonDoubleArea(second);

    if (outline.size() < 3 || !polygonIsSimple(outline) || std::abs(polygonDoubleArea(outline) - expected) > 1.0e-3)
    {
        return {};
    }

    return outline;
}
}
