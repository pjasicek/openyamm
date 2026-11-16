#include "core/OutdoorRoofCover.h"

#include "core/CoreMath.h"

#include <algorithm>
#include <cmath>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// A half plane: the points p with dot(p, normal) <= offset.
struct HalfPlane
{
    Point2 normal;
    double offset;
};

constexpr double LeastArea = 2.0;

double crossOf(const Point2 &origin, const Point2 &first, const Point2 &second)
{
    return (first[0] - origin[0]) * (second[1] - origin[1]) - (first[1] - origin[1]) * (second[0] - origin[0]);
}

double lengthBetween(const Point2 &from, const Point2 &to)
{
    return oy::hypot(to[0] - from[0], to[1] - from[1]);
}

// The convex hull, counter-clockwise, without points in a line.
std::vector<Point2> hullOf(std::vector<Point2> points)
{
    std::sort(points.begin(), points.end());
    points.erase(std::unique(points.begin(), points.end(), [](const Point2 &first, const Point2 &second)
    {
        return std::fabs(first[0] - second[0]) < 1.0e-6 && std::fabs(first[1] - second[1]) < 1.0e-6;
    }), points.end());

    if (points.size() < 3)
    {
        return points;
    }

    std::vector<Point2> hull(points.size() * 2);
    size_t count = 0;

    for (size_t index = 0; index < points.size(); ++index)
    {
        while (count >= 2 && crossOf(hull[count - 2], hull[count - 1], points[index]) <= 1.0e-6)
        {
            --count;
        }

        hull[count++] = points[index];
    }

    for (size_t index = points.size() - 1, lower = count + 1; index-- > 0;)
    {
        while (count >= lower && crossOf(hull[count - 2], hull[count - 1], points[index]) <= 1.0e-6)
        {
            --count;
        }

        hull[count++] = points[index];
    }

    hull.resize(count - 1);
    return hull;
}

// The sides of a convex counter-clockwise polygon as half planes holding it (unit normals).
std::vector<HalfPlane> sidesOf(const std::vector<Point2> &polygon)
{
    std::vector<HalfPlane> sides;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point2 &from = polygon[index];
        const Point2 &to = polygon[(index + 1) % polygon.size()];
        const double length = lengthBetween(from, to);

        if (length < 1.0e-9)
        {
            continue;
        }

        const Point2 normal = {(to[1] - from[1]) / length, (from[0] - to[0]) / length};
        sides.push_back({normal, normal[0] * from[0] + normal[1] * from[1]});
    }

    return sides;
}

bool holds(const std::vector<Point2> &polygon, const Point2 &point, double margin)
{
    for (const HalfPlane &side : sidesOf(polygon))
    {
        if (side.normal[0] * point[0] + side.normal[1] * point[1] > side.offset + margin)
        {
            return false;
        }
    }

    return true;
}

double areaOf(const std::vector<Point2> &polygon)
{
    return polygon.size() < 3 ? 0.0 : polygonDoubleArea(polygon) * 0.5;
}

// The pieces of a convex polygon outside the convex region the half planes bound together.
std::vector<std::vector<Point2>> outsideOf(const std::vector<Point2> &polygon, const std::vector<HalfPlane> &region)
{
    std::vector<std::vector<Point2>> outside;
    std::vector<Point2> rest = polygon;

    for (const HalfPlane &side : region)
    {
        const std::vector<Point2> beyond = clipConvex(rest, {-side.normal[0], -side.normal[1]}, -side.offset);

        if (areaOf(beyond) > LeastArea * 0.5)
        {
            outside.push_back(beyond);
        }

        rest = clipConvex(rest, side.normal, side.offset);

        if (areaOf(rest) <= LeastArea * 0.5)
        {
            return outside;
        }
    }

    return outside;
}

// Whether two convex polygons share a stretch of side longer than 1.
bool shareSide(const std::vector<Point2> &first, const std::vector<Point2> &second)
{
    for (size_t index = 0; index < first.size(); ++index)
    {
        const Point2 &from = first[index];
        const Point2 &to = first[(index + 1) % first.size()];
        const double length = lengthBetween(from, to);

        if (length < 1.0e-9)
        {
            continue;
        }

        const Point2 along = {(to[0] - from[0]) / length, (to[1] - from[1]) / length};

        for (size_t other = 0; other < second.size(); ++other)
        {
            const Point2 &start = second[other];
            const Point2 &end = second[(other + 1) % second.size()];
            const auto off = [&](const Point2 &point)
            {
                return std::fabs((point[0] - from[0]) * along[1] - (point[1] - from[1]) * along[0]);
            };

            if (off(start) > 0.05 || off(end) > 0.05)
            {
                continue;
            }

            const double a = (start[0] - from[0]) * along[0] + (start[1] - from[1]) * along[1];
            const double b = (end[0] - from[0]) * along[0] + (end[1] - from[1]) * along[1];

            if (std::min(length, std::max(a, b)) - std::max(0.0, std::min(a, b)) > 1.0)
            {
                return true;
            }
        }
    }

    return false;
}

// Convex pieces that lie side by side joined while the join stays convex.
std::vector<std::vector<Point2>> joinedConvex(std::vector<std::vector<Point2>> pieces)
{
    for (bool joined = true; joined;)
    {
        joined = false;

        for (size_t first = 0; first < pieces.size() && !joined; ++first)
        {
            for (size_t second = first + 1; second < pieces.size() && !joined; ++second)
            {
                if (!shareSide(pieces[first], pieces[second]))
                {
                    continue;
                }

                std::vector<Point2> both = pieces[first];
                both.insert(both.end(), pieces[second].begin(), pieces[second].end());
                const std::vector<Point2> hull = hullOf(both);
                const double sum = areaOf(pieces[first]) + areaOf(pieces[second]);

                if (std::fabs(areaOf(hull) - sum) <= 0.5 + sum * 1.0e-7)
                {
                    pieces[first] = hull;
                    pieces.erase(pieces.begin() + static_cast<std::ptrdiff_t>(second));
                    joined = true;
                }
            }
        }
    }

    return pieces;
}
}

bool outlineBendsIn(const std::vector<Point2> &outline)
{
    for (size_t index = 0; index < outline.size(); ++index)
    {
        const Point2 &before = outline[(index + outline.size() - 1) % outline.size()];
        const Point2 &after = outline[(index + 1) % outline.size()];

        if (crossOf(before, outline[index], after) < -1.0e-3)
        {
            return true;
        }
    }

    return false;
}

std::vector<std::vector<Point2>> convexPartsOf(const std::vector<Point2> &outline)
{
    if (!outlineBendsIn(outline))
    {
        return {outline};
    }

    std::vector<std::vector<Point2>> parts;

    for (const std::vector<size_t> &piece : convexPieces(outline, 64))
    {
        std::vector<Point2> points;

        for (const size_t index : piece)
        {
            points.push_back(outline[index]);
        }

        parts.push_back(points);
    }

    return parts;
}

std::vector<std::vector<Point2>> roofCoverPieces(const std::vector<Point2> &outline)
{
    if (!outlineBendsIn(outline))
    {
        return {outline};
    }

    // Cells: the convex parts cut along both sides of every corner that bends in, carried on across the outline.
    std::vector<std::vector<Point2>> cells = convexPartsOf(outline);
    const size_t count = outline.size();

    for (size_t index = 0; index < count; ++index)
    {
        const Point2 &before = outline[(index + count - 1) % count];
        const Point2 &here = outline[index];
        const Point2 &after = outline[(index + 1) % count];

        if (crossOf(before, here, after) >= -1.0e-3)
        {
            continue;
        }

        for (const std::vector<Point2> &side : {std::vector<Point2>{before, here}, std::vector<Point2>{here, after}})
        {
            const HalfPlane line = sidesOf(side)[0];
            std::vector<std::vector<Point2>> cut;

            for (const std::vector<Point2> &cell : cells)
            {
                for (const double sign : {1.0, -1.0})
                {
                    std::vector<Point2> half = clipConvex(cell, {line.normal[0] * sign, line.normal[1] * sign},
                        line.offset * sign);

                    if (areaOf(half) > LeastArea)
                    {
                        cut.push_back(hullOf(half));
                    }
                }
            }

            cells = cut;
        }
    }

    // From every cell, the cells beside it taken in while the whole stays convex.
    const size_t cellCount = cells.size();
    std::vector<std::vector<bool>> beside(cellCount, std::vector<bool>(cellCount, false));

    for (size_t first = 0; first < cellCount; ++first)
    {
        for (size_t second = first + 1; second < cellCount; ++second)
        {
            beside[first][second] = beside[second][first] = shareSide(cells[first], cells[second]);
        }
    }

    std::vector<std::vector<Point2>> pieces;
    std::set<std::vector<bool>> seen;

    for (size_t seed = 0; seed < cellCount; ++seed)
    {
        std::vector<bool> member(cellCount, false);
        member[seed] = true;
        std::vector<Point2> hull = cells[seed];
        double area = areaOf(cells[seed]);

        for (bool grew = true; grew;)
        {
            grew = false;

            for (size_t cell = 0; cell < cellCount; ++cell)
            {
                bool touches = false;

                for (size_t other = 0; other < cellCount && !member[cell]; ++other)
                {
                    touches = touches || (member[other] && beside[cell][other]);
                }

                if (member[cell] || !touches)
                {
                    continue;
                }

                std::vector<Point2> both = hull;
                both.insert(both.end(), cells[cell].begin(), cells[cell].end());
                const std::vector<Point2> next = hullOf(both);
                const double sum = area + areaOf(cells[cell]);

                if (std::fabs(areaOf(next) - sum) <= 0.5 + sum * 1.0e-7)
                {
                    member[cell] = true;
                    hull = next;
                    area = sum;
                    grew = true;
                }
            }
        }

        if (seen.insert(member).second)
        {
            pieces.push_back(hull);
        }
    }

    // A piece inside another adds nothing.
    std::vector<std::vector<Point2>> kept;

    for (size_t index = 0; index < pieces.size(); ++index)
    {
        bool inside = false;

        for (size_t other = 0; other < pieces.size() && !inside; ++other)
        {
            if (other == index || (areaOf(pieces[other]) < areaOf(pieces[index]) - 0.5)
                || (std::fabs(areaOf(pieces[other]) - areaOf(pieces[index])) <= 0.5 && other > index))
            {
                continue;
            }

            inside = std::all_of(pieces[index].begin(), pieces[index].end(), [&](const Point2 &point)
            {
                return holds(pieces[other], point, 0.05);
            });
        }

        if (!inside)
        {
            kept.push_back(pieces[index]);
        }
    }

    return kept;
}

std::vector<std::vector<Point2>> areaBetween(const std::vector<Point2> &outer, const std::vector<Point2> &inner)
{
    std::vector<std::vector<Point2>> pieces = convexPartsOf(outer);

    for (const std::vector<Point2> &cut : convexPartsOf(inner))
    {
        std::vector<std::vector<Point2>> left;

        for (const std::vector<Point2> &piece : pieces)
        {
            for (std::vector<Point2> &outside : outsideOf(piece, sidesOf(cut)))
            {
                left.push_back(std::move(outside));
            }
        }

        pieces = left;
    }

    return joinedConvex(pieces);
}

namespace
{
Point2 centreOf(const std::vector<std::vector<Point2>> &polygons, double &area)
{
    Point2 centre = {0.0, 0.0};
    area = 0.0;

    for (const std::vector<Point2> &polygon : polygons)
    {
        for (size_t index = 1; index + 1 < polygon.size(); ++index)
        {
            const double twice = crossOf(polygon[0], polygon[index], polygon[index + 1]);
            centre[0] += twice * (polygon[0][0] + polygon[index][0] + polygon[index + 1][0]) / 3.0;
            centre[1] += twice * (polygon[0][1] + polygon[index][1] + polygon[index + 1][1]) / 3.0;
            area += twice;
        }
    }

    return area > 1.0e-9 ? Point2{centre[0] / area, centre[1] / area} : centre;
}

std::vector<Point2> clippedTo(std::vector<Point2> polygon, const std::vector<Point2> &region)
{
    for (const HalfPlane &side : sidesOf(region))
    {
        polygon = clipConvex(polygon, side.normal, side.offset);
    }

    return polygon;
}

// A piece's ridge: its way and the line across it (half width, middle).
struct Ridge
{
    Point2 along = {1.0, 0.0};
    double half = 0.0;
    double middle = 0.0;
};

Ridge ridgeOf(const std::vector<Point2> &hull, const Point2 &along)
{
    Ridge ridge;
    ridge.along = along;
    const Point2 across = {-along[1], along[0]};
    double least = 1.0e18;
    double most = -1.0e18;

    for (const Point2 &point : hull)
    {
        const double side = point[0] * across[0] + point[1] * across[1];
        least = std::min(least, side);
        most = std::max(most, side);
    }

    ridge.half = (most - least) * 0.5;
    ridge.middle = (most + least) * 0.5;
    return ridge;
}
}

RoofCover::RoofCover(const std::vector<Point2> &walls, bool gable, const std::optional<Point2> &ridge, double hipRun,
    bool sameSlope)
{
    std::vector<std::vector<Point2>> hulls;

    for (const std::vector<Point2> &piece : roofCoverPieces(walls))
    {
        std::vector<Point2> hull = hullOf(piece);

        if (hull.size() >= 3)
        {
            hulls.push_back(hull);
        }
    }

    // Each piece's ridge: as given; else away from where the piece meets the others (a wing's ridge runs out along
    // the wing, the hall's it joins runs across it: Harmondale's tavern); else along its longest side.
    std::vector<Point2> ways(hulls.size(), ridge.value_or(Point2{1.0, 0.0}));

    for (size_t piece = 0; piece < hulls.size() && !ridge; ++piece)
    {
        const std::vector<Point2> &hull = hulls[piece];
        double longest = 0.0;

        for (size_t index = 0; index < hull.size(); ++index)
        {
            const Point2 &from = hull[index];
            const Point2 &to = hull[(index + 1) % hull.size()];
            const double length = lengthBetween(from, to);

            if (length > longest + 1.0e-6)
            {
                longest = length;
                ways[piece] = {(to[0] - from[0]) / length, (to[1] - from[1]) / length};
            }
        }

        std::vector<std::vector<Point2>> shared;
        std::vector<std::vector<Point2>> own = {hull};

        for (size_t other = 0; other < hulls.size(); ++other)
        {
            if (other == piece)
            {
                continue;
            }

            const std::vector<Point2> both = clippedTo(hull, hulls[other]);

            if (areaOf(both) > LeastArea)
            {
                shared.push_back(both);
            }

            std::vector<std::vector<Point2>> left;

            for (const std::vector<Point2> &part : own)
            {
                for (std::vector<Point2> &outside : outsideOf(part, sidesOf(hulls[other])))
                {
                    left.push_back(std::move(outside));
                }
            }

            own = left;
        }

        double sharedArea = 0.0;
        double ownArea = 0.0;
        const Point2 sharedCentre = centreOf(shared, sharedArea);
        const Point2 ownCentre = centreOf(own, ownArea);
        const Point2 away = {ownCentre[0] - sharedCentre[0], ownCentre[1] - sharedCentre[1]};
        const double length = oy::hypot(away[0], away[1]);

        if (gable && sharedArea > LeastArea && ownArea > LeastArea && length > 1.0)
        {
            ways[piece] = {away[0] / length, away[1] / length};
        }
    }

    std::vector<Ridge> ridges;

    for (size_t piece = 0; piece < hulls.size(); ++piece)
    {
        ridges.push_back(ridgeOf(hulls[piece], ways[piece]));
    }

    // A gable narrower than one it runs into ends at that one's ridge (the tavern's hall in its wing), where the
    // part cut off lies under the wider piece.
    for (size_t piece = 0; gable && piece < hulls.size(); ++piece)
    {
        for (size_t other = 0; other < hulls.size(); ++other)
        {
            if (other == piece || ridges[piece].half >= ridges[other].half - 1.0
                || areaOf(clippedTo(hulls[piece], hulls[other])) <= LeastArea)
            {
                continue;
            }

            const Point2 across = {-ridges[other].along[1], ridges[other].along[0]};
            double ownArea = 0.0;
            const Point2 own = centreOf(outsideOf(hulls[piece], sidesOf(hulls[other])), ownArea);
            const double sign = own[0] * across[0] + own[1] * across[1] > ridges[other].middle ? -1.0 : 1.0;
            // Keep the side of the other's ridge where this piece's own part lies.
            const std::vector<Point2> kept = clipConvex(hulls[piece], {across[0] * sign, across[1] * sign},
                ridges[other].middle * sign);
            const std::vector<Point2> cut = clipConvex(hulls[piece], {-across[0] * sign, -across[1] * sign},
                -ridges[other].middle * sign);
            const bool under = std::all_of(cut.begin(), cut.end(), [&](const Point2 &point)
            {
                return holds(hulls[other], point, 1.0);
            });

            if (ownArea > LeastArea && under && areaOf(kept) > LeastArea)
            {
                hulls[piece] = hullOf(kept);
                ridges[piece] = ridgeOf(hulls[piece], ridges[piece].along);
            }
        }
    }

    std::vector<double> depths;

    for (size_t piece = 0; piece < hulls.size(); ++piece)
    {
        const std::vector<Point2> &hull = hulls[piece];
        const Point2 &along = ridges[piece].along;
        const double half = ridges[piece].half;
        const double middle = ridges[piece].middle;
        const Point2 across = {-along[1], along[0]};
        std::vector<RoofRun> runs;
        double deepest = 0.0;

        if (gable)
        {
            // half - (side - middle) and half + (side - middle).
            runs.push_back({-across[0], -across[1], half + middle});
            runs.push_back({across[0], across[1], half - middle});
            deepest = half;
        }
        else
        {
            for (const HalfPlane &side : sidesOf(hull))
            {
                // The distance in from the side; with a hip run, steeper over the sides that look along the ridge
                // (as an outline part's hip: the run between the half width and `hipRun` by the side's turn).
                double scale = 1.0;

                if (hipRun > 0.0 && half > 1.0e-9)
                {
                    const double turn = side.normal[0] * along[0] + side.normal[1] * along[1];
                    const double run = half + (std::min(hipRun, half) - half) * turn * turn;
                    scale = half / std::max(run, 1.0e-9);
                }

                runs.push_back({-side.normal[0] * scale, -side.normal[1] * scale, side.offset * scale});
            }

            for (size_t own = 0; own < runs.size(); ++own)
            {
                std::vector<Point2> region = hull;

                for (size_t other = 0; other < runs.size(); ++other)
                {
                    if (other != own)
                    {
                        region = clipConvex(region, {runs[own].a - runs[other].a, runs[own].b - runs[other].b},
                            runs[other].c - runs[own].c);
                    }
                }

                for (const Point2 &point : region)
                {
                    deepest = std::max(deepest, runs[own].a * point[0] + runs[own].b * point[1] + runs[own].c);
                }
            }
        }

        m_pieces.push_back(hull);
        m_runs.push_back(runs);
        depths.push_back(deepest);
        m_deepest = std::max(m_deepest, deepest);
    }

    // Unless one slope is asked for, every piece rises to the same height (the shipped cross gables meet ridge to
    // ridge): a narrower piece's slopes are steeper.
    for (size_t piece = 0; !sameSlope && piece < m_runs.size(); ++piece)
    {
        const double scale = depths[piece] > 1.0e-9 ? m_deepest / depths[piece] : 1.0;

        for (RoofRun &run : m_runs[piece])
        {
            run = {run.a * scale, run.b * scale, run.c * scale};
        }
    }
}

double RoofCover::runAt(const Point2 &point) const
{
    double best = 0.0;

    for (size_t piece = 0; piece < m_pieces.size(); ++piece)
    {
        if (!holds(m_pieces[piece], point, 0.05))
        {
            continue;
        }

        double least = 1.0e18;

        for (const RoofRun &run : m_runs[piece])
        {
            least = std::min(least, run.a * point[0] + run.b * point[1] + run.c);
        }

        best = std::max(best, least);
    }

    return best;
}

double RoofCover::runOf(const RoofCoverFace &face, const Point2 &point) const
{
    const RoofRun &run = m_runs[face.piece][face.plane];
    return run.a * point[0] + run.b * point[1] + run.c;
}

std::vector<RoofCoverFace> RoofCover::faces(const std::vector<Point2> &region) const
{
    constexpr double Tie = 0.01;
    const std::vector<std::vector<Point2>> regionParts = region.empty() ? std::vector<std::vector<Point2>>()
        : convexPartsOf(region);
    std::vector<RoofCoverFace> faces;

    for (size_t piece = 0; piece < m_pieces.size(); ++piece)
    {
        const std::vector<RoofRun> &runs = m_runs[piece];

        for (size_t plane = 0; plane < runs.size(); ++plane)
        {
            const RoofRun &own = runs[plane];
            // Where this plane is the piece's roof: lower than its other planes.
            std::vector<Point2> start = m_pieces[piece];

            for (size_t other = 0; other < runs.size() && areaOf(start) > LeastArea; ++other)
            {
                if (other != plane)
                {
                    start = clipConvex(start, {own.a - runs[other].a, own.b - runs[other].b}, runs[other].c - own.c);
                }
            }

            if (areaOf(start) <= LeastArea)
            {
                continue;
            }

            // Less where another piece's roof stands higher (on a tie the earlier piece keeps it).
            std::vector<std::vector<Point2>> fragments = {start};

            for (size_t other = 0; other < m_pieces.size(); ++other)
            {
                if (other == piece)
                {
                    continue;
                }

                std::vector<HalfPlane> higher = sidesOf(m_pieces[other]);
                const double tie = other < piece ? -Tie : Tie;
                bool empty = false;

                for (const RoofRun &run : m_runs[other])
                {
                    const Point2 normal = {own.a - run.a, own.b - run.b};
                    const double offset = run.c - own.c - tie;

                    if (oy::hypot(normal[0], normal[1]) < 1.0e-9)
                    {
                        empty = empty || offset < 0.0;
                        continue;
                    }

                    higher.push_back({normal, offset});
                }

                if (empty)
                {
                    continue;
                }

                std::vector<std::vector<Point2>> left;

                for (const std::vector<Point2> &fragment : fragments)
                {
                    for (std::vector<Point2> &outside : outsideOf(fragment, higher))
                    {
                        left.push_back(std::move(outside));
                    }
                }

                fragments = left;
            }

            if (!regionParts.empty())
            {
                std::vector<std::vector<Point2>> inside;

                for (const std::vector<Point2> &fragment : fragments)
                {
                    for (const std::vector<Point2> &part : regionParts)
                    {
                        std::vector<Point2> both = fragment;

                        for (const HalfPlane &side : sidesOf(part))
                        {
                            both = clipConvex(both, side.normal, side.offset);
                        }

                        if (areaOf(both) > LeastArea)
                        {
                            inside.push_back(both);
                        }
                    }
                }

                fragments = inside;
            }

            for (const std::vector<Point2> &fragment : joinedConvex(fragments))
            {
                const std::vector<Point2> hull = hullOf(fragment);

                if (areaOf(hull) > LeastArea)
                {
                    faces.push_back({hull, piece, plane});
                }
            }
        }
    }

    return faces;
}

std::vector<RoofProfileFace> RoofCover::profiles(const std::vector<Point2> &region) const
{
    constexpr double Least = 0.05;
    std::vector<RoofProfileFace> faces;
    std::vector<RoofRun> allRuns = {{0.0, 0.0, 0.0}};

    for (const std::vector<RoofRun> &runs : m_runs)
    {
        allRuns.insert(allRuns.end(), runs.begin(), runs.end());
    }

    for (size_t index = 0; index < region.size(); ++index)
    {
        const Point2 &from = region[index];
        const Point2 &to = region[(index + 1) % region.size()];
        const double length = lengthBetween(from, to);

        if (length < 1.0)
        {
            continue;
        }

        const Point2 step = {to[0] - from[0], to[1] - from[1]};
        const auto pointAt = [&](double share)
        {
            return Point2{from[0] + step[0] * share, from[1] + step[1] * share};
        };
        std::vector<double> shares = {0.0, 1.0};

        // Where the run along the side can bend: where it enters or leaves a piece, where two planes cross.
        for (const std::vector<Point2> &piece : m_pieces)
        {
            for (const HalfPlane &side : sidesOf(piece))
            {
                const double rate = side.normal[0] * step[0] + side.normal[1] * step[1];

                if (std::fabs(rate) > 1.0e-12)
                {
                    shares.push_back((side.offset - side.normal[0] * from[0] - side.normal[1] * from[1]) / rate);
                }
            }
        }

        for (size_t first = 0; first < allRuns.size(); ++first)
        {
            for (size_t second = first + 1; second < allRuns.size(); ++second)
            {
                const double a = allRuns[first].a - allRuns[second].a;
                const double b = allRuns[first].b - allRuns[second].b;
                const double c = allRuns[first].c - allRuns[second].c;
                const double rate = a * step[0] + b * step[1];

                if (std::fabs(rate) > 1.0e-12)
                {
                    shares.push_back(-(a * from[0] + b * from[1] + c) / rate);
                }
            }
        }

        std::sort(shares.begin(), shares.end());
        std::vector<std::array<double, 2>> chain;

        for (const double share : shares)
        {
            if (share < 0.0 || share > 1.0 || (!chain.empty() && (share - chain.back()[0]) * length < 0.01))
            {
                continue;
            }

            chain.push_back({share, runAt(pointAt(share))});
        }

        // Faces between the side and the roof over it: a new face where the roof touches its foot or bends up.
        std::vector<std::array<double, 2>> current;
        const auto close = [&]()
        {
            if (current.size() >= 2)
            {
                RoofProfileFace face;
                const Point2 left = pointAt(current.front()[0]);
                const Point2 right = pointAt(current.back()[0]);
                face.push_back({left[0], left[1], 0.0});
                face.push_back({right[0], right[1], 0.0});

                for (size_t point = current.size(); point-- > 0;)
                {
                    if (current[point][1] > Least)
                    {
                        const Point2 place = pointAt(current[point][0]);
                        face.push_back({place[0], place[1], current[point][1]});
                    }
                }

                if (face.size() >= 3)
                {
                    faces.push_back(face);
                }
            }

            current.clear();
        };
        const auto slopeOf = [&](const std::array<double, 2> &a, const std::array<double, 2> &b)
        {
            return (b[1] - a[1]) / std::max((b[0] - a[0]) * length, 1.0e-9);
        };

        for (size_t point = 0; point < chain.size(); ++point)
        {
            const std::array<double, 2> &here = chain[point];

            if (current.empty())
            {
                current.push_back(here);
                continue;
            }

            const bool bends = current.size() >= 2
                && slopeOf(current.back(), here) > slopeOf(current[current.size() - 2], current.back()) + 1.0e-6;

            if (bends)
            {
                const std::array<double, 2> corner = current.back();
                close();
                current.push_back(corner);
            }
            else if (current.size() >= 2
                && std::fabs(slopeOf(current.back(), here) - slopeOf(current[current.size() - 2], current.back()))
                <= 1.0e-6)
            {
                // In a line: the middle point is no corner.
                current.pop_back();
            }

            current.push_back(here);

            if (here[1] <= Least)
            {
                const bool raised = std::any_of(current.begin(), current.end(), [](const std::array<double, 2> &p)
                {
                    return p[1] > Least;
                });

                if (raised)
                {
                    close();
                }

                current.clear();
                current.push_back(here);
            }
        }

        close();
    }

    return faces;
}
}
