#include "game/indoor/IndoorFaceDrawGroups.h"

#include <algorithm>
#include <cmath>
#include <functional>

namespace OpenYAMM::Game
{
size_t IndoorFaceDrawGroupKeyHash::operator()(const IndoorFaceDrawGroupKey &key) const
{
    size_t hash = std::hash<std::string>{}(key.textureName);
    const auto combine = [&hash](size_t value)
    {
        hash ^= value + 0x9e3779b97f4a7c15ull + (hash << 6) + (hash >> 2);
    };
    combine(std::hash<int32_t>{}(key.lightmapPage));
    combine(std::hash<uint32_t>{}(key.waterColorAbgr));
    combine(std::hash<int32_t>{}(key.translucentFace));
    combine(std::hash<bool>{}(key.singleMaterialTerrain));
    return hash;
}

namespace
{
using Point = std::array<double, 3>;

double dot(const Point &a, const Point &b)
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

Point sub(const Point &a, const Point &b)
{
    return {a[0] - b[0], a[1] - b[1], a[2] - b[2]};
}

Point cross(const Point &a, const Point &b)
{
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}

// Keeps the part of the polygon where dot(normal, x) >= offset (Sutherland-Hodgman), into result.
void clipPolygon(const std::vector<Point> &polygon, const Point &normal, double offset, std::vector<Point> &result)
{
    result.clear();
    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point &current = polygon[index];
        const Point &next = polygon[(index + 1) % polygon.size()];
        const double currentSide = dot(normal, current) - offset;
        const double nextSide = dot(normal, next) - offset;
        if (currentSide >= 0.0)
        {
            result.push_back(current);
        }
        if ((currentSide >= 0.0) != (nextSide >= 0.0))
        {
            const double t = currentSide / (currentSide - nextSide);
            result.push_back({current[0] + (next[0] - current[0]) * t, current[1] + (next[1] - current[1]) * t,
                current[2] + (next[2] - current[2]) * t});
        }
    }
}
}

IndoorFaceShape makeIndoorFaceShape(std::span<const IndoorFacePoint> polygon)
{
    IndoorFaceShape shape;
    for (const IndoorFacePoint &point : polygon)
    {
        shape.points.push_back({point[0], point[1], point[2]});
    }
    const std::vector<Point> &points = shape.points;
    if (points.size() < 3)
    {
        return shape;
    }
    Point normal = {0.0, 0.0, 0.0};
    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point &current = points[index];
        const Point &next = points[(index + 1) % points.size()];
        normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
        normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
        normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
    }
    const double length = std::sqrt(dot(normal, normal));
    if (length < 1e-6)
    {
        return shape;
    }
    shape.normal = {normal[0] / length, normal[1] / length, normal[2] / length};
    shape.distance = dot(shape.normal, points[0]);
    for (const Point &point : points)
    {
        shape.flatness = std::max(shape.flatness, std::fabs(dot(shape.normal, point) - shape.distance));
    }
    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point edge = sub(points[(index + 1) % points.size()], points[index]);
        const Point nextEdge = sub(points[(index + 2) % points.size()], points[(index + 1) % points.size()]);
        if (dot(cross(edge, nextEdge), shape.normal) < -1e-6 * std::sqrt(dot(edge, edge) * dot(nextEdge, nextEdge)))
        {
            // Not convex: the edges' planes do not bound it.
            shape.edgePlanes.clear();
            return shape;
        }
        const double edgeLength = std::sqrt(dot(edge, edge));
        if (edgeLength < 1e-9)
        {
            continue;
        }
        const Point inward = cross(shape.normal, edge);
        const Point unit = {inward[0] / edgeLength, inward[1] / edgeLength, inward[2] / edgeLength};
        shape.edgePlanes.push_back({unit[0], unit[1], unit[2], dot(unit, points[index])});
    }
    shape.wholePlane = false;
    return shape;
}

bool indoorFaceReachesInterior(const IndoorFaceShape &face, const IndoorFaceShape &other, float depthSlack,
    float edgeInset)
{
    if (other.points.empty())
    {
        return false;
    }
    if (dot(face.normal, face.normal) == 0.0)
    {
        return true;
    }
    // The part of `other` in the slab around the plane, then inside each shrunk edge.
    thread_local std::vector<Point> part;
    thread_local std::vector<Point> clipped;
    const double slab = double(depthSlack) + face.flatness;
    clipPolygon(other.points, face.normal, face.distance - slab, part);
    clipPolygon(part, {-face.normal[0], -face.normal[1], -face.normal[2]}, -(face.distance + slab), clipped);
    part.swap(clipped);
    if (part.empty() || face.wholePlane)
    {
        return !part.empty();
    }
    for (const std::array<double, 4> &plane : face.edgePlanes)
    {
        clipPolygon(part, {plane[0], plane[1], plane[2]}, plane[3] + double(edgeInset), clipped);
        part.swap(clipped);
        if (part.empty())
        {
            return false;
        }
    }
    return true;
}

bool indoorFacesMeetAtOneDepth(const IndoorFaceShape &first, const IndoorFaceShape &second, float depthSlack,
    float edgeInset)
{
    const bool degenerate = dot(first.normal, first.normal) == 0.0 || dot(second.normal, second.normal) == 0.0;
    const double minCosine = std::cos(double(IndoorFaceDrawMaxAngleDegrees) * 3.14159265358979323846 / 180.0);
    if (!degenerate && std::fabs(dot(first.normal, second.normal)) < minCosine)
    {
        return false;
    }
    return indoorFaceReachesInterior(first, second, depthSlack, edgeInset)
        || indoorFaceReachesInterior(second, first, depthSlack, edgeInset);
}

void IndoorFaceDrawPlan::clear()
{
    m_batchGroups.clear();
    m_groupIndices.clear();
    m_batchRanges.clear();
    m_laterConflicts.clear();
    m_conflictPairs.clear();
    m_planned = false;
    m_drawn.clear();
    m_draws.clear();
    m_mergedIndices.clear();
}

void IndoorFaceDrawPlan::addBatch(
    uint32_t group, uint32_t batch, std::span<const uint32_t> localIndices, uint32_t vertexOffset)
{
    if (group >= m_groupIndices.size())
    {
        m_groupIndices.resize(group + 1);
    }
    if (batch >= m_batchRanges.size())
    {
        m_batchRanges.resize(batch + 1);
        m_batchGroups.resize(batch + 1, 0);
        m_laterConflicts.resize(batch + 1);
    }
    std::vector<uint32_t> &indices = m_groupIndices[group];
    m_batchRanges[batch] = {uint32_t(indices.size()), uint32_t(localIndices.size())};
    m_batchGroups[batch] = group;
    for (uint32_t index : localIndices)
    {
        indices.push_back(vertexOffset + index);
    }
    m_planned = false;
}

bool IndoorFaceDrawPlan::addConflict(uint32_t batch, uint32_t otherBatch)
{
    if (batch == otherBatch || batch >= m_batchGroups.size() || otherBatch >= m_batchGroups.size())
    {
        return false;
    }
    const uint32_t earlier = std::min(batch, otherBatch);
    const uint32_t later = std::max(batch, otherBatch);
    if (!m_conflictPairs.insert((uint64_t(later) << 32) | earlier).second)
    {
        return false;
    }
    m_laterConflicts[earlier].push_back(later);
    m_planned = false;
    return true;
}

bool IndoorFaceDrawPlan::hasConflict(uint32_t batch, uint32_t otherBatch) const
{
    const uint32_t earlier = std::min(batch, otherBatch);
    const uint32_t later = std::max(batch, otherBatch);
    return m_conflictPairs.contains((uint64_t(later) << 32) | earlier);
}

IndoorFaceIndexRange IndoorFaceDrawPlan::batchRange(uint32_t batch) const
{
    return batch < m_batchRanges.size() ? m_batchRanges[batch] : IndoorFaceIndexRange{};
}

void IndoorFaceDrawPlan::appendDraw(uint32_t group, const std::vector<uint32_t> &batches)
{
    // Ascending and back to back in the group's list: one run of it.
    bool run = true;
    uint32_t total = 0;
    for (size_t index = 0; index < batches.size(); ++index)
    {
        const IndoorFaceIndexRange &range = m_batchRanges[batches[index]];
        if (index > 0)
        {
            const IndoorFaceIndexRange &previous = m_batchRanges[batches[index - 1]];
            run = run && range.firstIndex == previous.firstIndex + previous.indexCount;
        }
        total += range.indexCount;
    }
    if (total == 0)
    {
        return;
    }
    if (run)
    {
        m_draws.push_back({group, false, m_batchRanges[batches.front()].firstIndex, total});
        return;
    }
    const std::vector<uint32_t> &indices = m_groupIndices[group];
    const uint32_t mergedFirst = uint32_t(m_mergedIndices.size());
    for (uint32_t batch : batches)
    {
        const IndoorFaceIndexRange &range = m_batchRanges[batch];
        m_mergedIndices.insert(m_mergedIndices.end(), indices.begin() + range.firstIndex,
            indices.begin() + range.firstIndex + range.indexCount);
    }
    m_draws.push_back({group, true, mergedFirst, total});
}

bool IndoorFaceDrawPlan::update(std::span<const uint8_t> drawn)
{
    if (m_planned && std::equal(drawn.begin(), drawn.end(), m_drawn.begin(), m_drawn.end()))
    {
        return false;
    }
    m_planned = true;
    m_drawn.assign(drawn.begin(), drawn.end());
    m_draws.clear();
    m_mergedIndices.clear();
    const auto drawsBatch = [&](uint32_t batch)
    {
        return batch < m_drawn.size() && m_drawn[batch] != 0 && batch < m_batchRanges.size()
            && m_batchRanges[batch].indexCount > 0;
    };

    // The drawn batches' earlier touching batches still to go, and each group's batches ready to go (ascending).
    std::vector<uint32_t> waiting(m_batchRanges.size(), 0);
    for (uint32_t batch = 0; batch < m_batchRanges.size(); ++batch)
    {
        if (drawsBatch(batch))
        {
            for (uint32_t later : m_laterConflicts[batch])
            {
                waiting[later] += drawsBatch(later) ? 1 : 0;
            }
        }
    }
    std::vector<std::vector<uint32_t>> ready(m_groupIndices.size());
    size_t remaining = 0;
    for (uint32_t batch = 0; batch < m_batchRanges.size(); ++batch)
    {
        if (drawsBatch(batch))
        {
            ++remaining;
            if (waiting[batch] == 0)
            {
                ready[m_batchGroups[batch]].push_back(batch);
            }
        }
    }

    std::vector<uint32_t> drawBatches;
    while (remaining > 0)
    {
        // The group with the most batches ready (the lowest batch first on a tie).
        uint32_t group = 0;
        size_t best = 0;
        uint32_t bestFirst = UINT32_MAX;
        for (uint32_t candidate = 0; candidate < ready.size(); ++candidate)
        {
            const std::vector<uint32_t> &batches = ready[candidate];
            if (!batches.empty() && (batches.size() > best || (batches.size() == best && batches.front() < bestFirst)))
            {
                group = candidate;
                best = batches.size();
                bestFirst = batches.front();
            }
        }
        if (best == 0)
        {
            // Not reachable: the pairs follow batch order, so they cannot form a cycle.
            break;
        }
        // Its ready batches, then the ones of the same group those free, in order.
        drawBatches.clear();
        while (!ready[group].empty())
        {
            std::vector<uint32_t> batches;
            batches.swap(ready[group]);
            std::sort(batches.begin(), batches.end());
            for (uint32_t batch : batches)
            {
                drawBatches.push_back(batch);
                --remaining;
                for (uint32_t later : m_laterConflicts[batch])
                {
                    if (drawsBatch(later) && --waiting[later] == 0)
                    {
                        ready[m_batchGroups[later]].push_back(later);
                    }
                }
            }
        }
        appendDraw(group, drawBatches);
    }
    return true;
}
}
