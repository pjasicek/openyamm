#include "game/pathfinding/PathPlanner.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <queue>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr float PlannerEpsilon = 0.0001f;
constexpr size_t InvalidNodeIndex = std::numeric_limits<size_t>::max();

struct NodeKey
{
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;

    bool operator==(const NodeKey &other) const
    {
        return x == other.x && y == other.y && z == other.z;
    }
};

struct NodeKeyHash
{
    size_t operator()(const NodeKey &key) const
    {
        const uint32_t x = static_cast<uint32_t>(key.x) * 73856093u;
        const uint32_t y = static_cast<uint32_t>(key.y) * 19349663u;
        const uint32_t z = static_cast<uint32_t>(key.z) * 83492791u;
        return static_cast<size_t>(x ^ y ^ z);
    }
};

struct SearchNode
{
    NodeKey key;
    PathPoint point;
    float cost = 0.0f;
    float estimate = 0.0f;
    size_t parentIndex = InvalidNodeIndex;
    size_t floorFacetIndex = static_cast<size_t>(-1);
    bool closed = false;
};

struct OpenNode
{
    float priority = 0.0f;
    size_t nodeIndex = 0;

    bool operator<(const OpenNode &other) const
    {
        return priority > other.priority;
    }
};

float distanceSquared2d(const PathPoint &from, const PathPoint &to)
{
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    return dx * dx + dy * dy;
}

float distanceSquared3d(const PathPoint &from, const PathPoint &to)
{
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    const float dz = to.z - from.z;
    return dx * dx + dy * dy + dz * dz;
}

float distance2d(const PathPoint &from, const PathPoint &to)
{
    return std::sqrt(distanceSquared2d(from, to));
}

float distance3d(const PathPoint &from, const PathPoint &to)
{
    return std::sqrt(distanceSquared3d(from, to));
}

bool walkStepDeltaAllowed(float fromZ, float toZ, const PathObject &object)
{
    const float deltaZ = toZ - fromZ;

    if (deltaZ > object.stepHeight + PlannerEpsilon)
    {
        return false;
    }

    if (-deltaZ > object.dropHeight + PlannerEpsilon)
    {
        return false;
    }

    return true;
}

void updateBestDebugPoint(PathPlanDebugInfo &debug, const SearchNode &node, const PathPoint &target)
{
    debug.bestPoint = node.point;
    debug.bestFloorFacet = node.floorFacetIndex;
    debug.bestDistance2d = distance2d(node.point, target);
    debug.bestDistance3d = distance3d(node.point, target);
}

NodeKey makeNodeKey(const PathPoint &point, float stepSize)
{
    return {
        static_cast<int32_t>(std::lround(point.x / stepSize)),
        static_cast<int32_t>(std::lround(point.y / stepSize)),
        static_cast<int32_t>(std::lround(point.z / stepSize))
    };
}

float heuristic(const PathPoint &from, const PathPoint &to, bool canFly)
{
    if (canFly)
    {
        return distanceSquared3d(from, to);
    }

    const float uphill = std::max(0.0f, to.z - from.z);
    return distanceSquared2d(from, to) + uphill * uphill * 4.0f;
}

float travelCost(const PathPoint &from, const PathPoint &to, bool canFly)
{
    if (canFly)
    {
        return distance3d(from, to);
    }

    const float uphill = std::max(0.0f, to.z - from.z);
    return distance2d(from, to) + uphill * 2.0f;
}

float partialProgressScore(
    const PathPoint &start,
    const PathPoint &point,
    const PathPoint &target,
    const PathObject &object
)
{
    if (object.canFly)
    {
        return heuristic(point, target, true);
    }

    const float targetRise = target.z - start.z;

    if (targetRise <= object.stepHeight)
    {
        return heuristic(point, target, false);
    }

    const float remainingRise = std::max(0.0f, target.z - point.z);
    const float droppedBelowStart = std::max(0.0f, start.z - point.z - object.stepHeight);
    return distanceSquared2d(point, target)
        + remainingRise * remainingRise * 16.0f
        + droppedBelowStart * droppedBelowStart * 64.0f;
}

PathPoint snapGroundPoint(
    const PathMap &map,
    const PathPoint &point,
    const PathObject &object,
    bool &valid,
    PathFloorSample *pFloorSample = nullptr,
    int32_t preferredSourceFacetSourceId = -1,
    bool *pPreferredSnapUsed = nullptr,
    float requestedNearbySnapDistance = 0.0f
)
{
    const PathFloorSample floor = map.floorAt({point.x, point.y, point.z + object.stepHeight});

    if (pFloorSample != nullptr)
    {
        *pFloorSample = floor;
    }

    if (!floor.hasFloor || floor.inVoid)
    {
        const float sourceSnapDistance = std::max(4.0f, object.radius + 4.0f);

        if (preferredSourceFacetSourceId >= 0)
        {
            PathFloorSample preferredFloor = {};
            bool preferredValid = false;
            const PathPoint snapped =
                map.snapToWalkableSourceFacet(
                    preferredSourceFacetSourceId,
                    {point.x, point.y, point.z + object.stepHeight},
                    sourceSnapDistance,
                    preferredValid,
                    &preferredFloor);

            if (preferredValid)
            {
                valid = true;

                if (pFloorSample != nullptr)
                {
                    *pFloorSample = preferredFloor;
                }

                if (pPreferredSnapUsed != nullptr)
                {
                    *pPreferredSnapUsed = true;
                }

                return snapped;
            }
        }

        PathFloorSample nearbyFloor = {};
        bool nearbyValid = false;
        const float nearbySnapDistance =
            std::max({sourceSnapDistance, object.radius + object.stepLength, requestedNearbySnapDistance});
        const PathPoint nearbySnapped =
            map.snapToNearestWalkableFloor(
                {point.x, point.y, point.z + object.stepHeight},
                nearbySnapDistance,
                nearbyValid,
                &nearbyFloor);

        if (nearbyValid)
        {
            valid = true;

            if (pFloorSample != nullptr)
            {
                *pFloorSample = nearbyFloor;
            }

            if (pPreferredSnapUsed != nullptr)
            {
                *pPreferredSnapUsed = true;
            }

            return nearbySnapped;
        }

        valid = false;
        return point;
    }

    valid = true;
    return {point.x, point.y, floor.z};
}

bool flyingPointIsValid(const PathMap &map, const PathPoint &point)
{
    const PathFloorSample floor = map.floorAt(point);
    return floor.hasFloor && !floor.inVoid;
}

std::vector<PathPoint> rebuildPathToNode(const std::vector<SearchNode> &nodes, size_t nodeIndex)
{
    std::vector<PathPoint> reversed;

    while (nodeIndex != InvalidNodeIndex)
    {
        reversed.push_back(nodes[nodeIndex].point);
        nodeIndex = nodes[nodeIndex].parentIndex;
    }

    std::vector<PathPoint> waypoints;

    for (size_t index = reversed.size(); index > 1; --index)
    {
        waypoints.push_back(reversed[index - 2]);
    }

    return waypoints;
}

std::vector<PathPoint> rebuildPath(const std::vector<SearchNode> &nodes, size_t nodeIndex, const PathPoint &target)
{
    std::vector<PathPoint> waypoints = rebuildPathToNode(nodes, nodeIndex);
    waypoints.push_back(target);
    return waypoints;
}
}

PathPlanResult PathPlanner::plan(const PathMap &map, const PathPlanRequest &request)
{
    PathPlanResult result = {};
    result.mapRevision = request.mapRevision;
    result.debug.requestSource = request.source;
    result.debug.requestTarget = request.target;
    result.debug.preferredSourceFacetSourceId = request.preferredSourceFacetSourceId;

    const float stepSize = std::max(request.object.stepLength, 24.0f);
    PathPoint start = request.source;
    PathPoint target = request.target;
    bool startValid = true;
    bool targetValid = true;
    PathFloorSample startFloor = {};
    PathFloorSample targetFloor = {};

    if (!request.object.canFly)
    {
        bool preferredSourceSnapUsed = false;
        start =
            snapGroundPoint(
                map,
                request.source,
                request.object,
                startValid,
                &startFloor,
                request.preferredSourceFacetSourceId,
                &preferredSourceSnapUsed,
                request.sourceSnapDistance);
        result.debug.preferredSourceSnapUsed = preferredSourceSnapUsed;
        target = snapGroundPoint(map, request.target, request.object, targetValid, &targetFloor);
    }
    else
    {
        startFloor = map.floorAt(request.source);
        targetFloor = map.floorAt(request.target);
        startValid = startFloor.hasFloor && !startFloor.inVoid;
        targetValid = targetFloor.hasFloor && !targetFloor.inVoid;
    }

    result.debug.sourceValid = startValid;
    result.debug.targetValid = targetValid;
    result.debug.snappedSource = start;
    result.debug.snappedTarget = target;

    if (startFloor.hasFloor)
    {
        result.debug.sourceFloorFacet = startFloor.facetIndex;
    }

    if (targetFloor.hasFloor)
    {
        result.debug.targetFloorFacet = targetFloor.facetIndex;
    }

    if (!startValid || (!targetValid && !request.allowPartialPath))
    {
        result.debug.bestPoint = start;
        result.debug.bestDistance2d = distance2d(start, target);
        result.debug.bestDistance3d = distance3d(start, target);
        result.status = PathPlanStatus::NoRoute;
        return result;
    }

    if (request.allowDirect && targetValid && map.canReachDirectly(start, target, request.object))
    {
        result.status = PathPlanStatus::Success;
        result.debug.directReachable = true;
        result.debug.bestPoint = target;
        result.debug.bestFloorFacet = targetFloor.hasFloor ? targetFloor.facetIndex : static_cast<size_t>(-1);
        result.debug.bestDistance2d = 0.0f;
        result.debug.bestDistance3d = 0.0f;
        result.waypoints.push_back(target);
        return result;
    }

    std::vector<SearchNode> nodes;
    nodes.reserve(std::min<size_t>(request.nodeLimit, 8192));
    std::unordered_map<NodeKey, size_t, NodeKeyHash> nodeIndexByKey;
    std::priority_queue<OpenNode> openSet;

    SearchNode startNode = {};
    startNode.key = makeNodeKey(start, stepSize);
    startNode.point = start;
    startNode.estimate = heuristic(start, target, request.object.canFly);
    startNode.floorFacetIndex = startFloor.hasFloor ? startFloor.facetIndex : static_cast<size_t>(-1);
    nodes.push_back(startNode);
    nodeIndexByKey[startNode.key] = 0;
    openSet.push({startNode.estimate, 0});
    size_t bestPartialNodeIndex = 0;
    float bestPartialScore = partialProgressScore(start, start, target, request.object);
    updateBestDebugPoint(result.debug, startNode, target);

    const int directions2d[8][2] = {
        {-1, -1},
        {-1, 0},
        {-1, 1},
        {0, -1},
        {0, 1},
        {1, -1},
        {1, 0},
        {1, 1}
    };

    const int directions3d[3] = {-1, 0, 1};

    while (!openSet.empty())
    {
        const OpenNode openNode = openSet.top();
        openSet.pop();
        SearchNode &currentNode = nodes[openNode.nodeIndex];

        if (currentNode.closed)
        {
            ++result.debug.skippedClosedNodes;
            continue;
        }

        currentNode.closed = true;
        const PathPoint currentPoint = currentNode.point;
        const float currentCost = currentNode.cost;
        ++result.analyzedNodeCount;

        const float currentPartialScore = partialProgressScore(start, currentPoint, target, request.object);

        if (currentPartialScore < bestPartialScore)
        {
            bestPartialScore = currentPartialScore;
            bestPartialNodeIndex = openNode.nodeIndex;
            updateBestDebugPoint(result.debug, currentNode, target);
        }

        if (result.analyzedNodeCount > request.nodeLimit)
        {
            if (request.allowPartialPath && bestPartialNodeIndex != 0)
            {
                result.waypoints = rebuildPathToNode(nodes, bestPartialNodeIndex);

                if (!result.waypoints.empty())
                {
                    result.status = PathPlanStatus::Partial;
                    return result;
                }
            }

            result.status = PathPlanStatus::NodeLimitExceeded;
            return result;
        }

        const float closeEnoughDistance = stepSize * 4.0f;

        if (targetValid
            && (request.allowDirect || openNode.nodeIndex != 0)
            && distance3d(currentPoint, target) <= closeEnoughDistance
            && map.canReachDirectly(currentPoint, target, request.object))
        {
            result.status = PathPlanStatus::Success;
            result.waypoints = rebuildPath(nodes, openNode.nodeIndex, target);
            return result;
        }

        // Within the goal distance of the target (on its floor) the route ends here, short of it.
        if (request.goalDistance > 0.0f
            && openNode.nodeIndex != 0
            && distance2d(currentPoint, target) <= request.goalDistance
            && std::fabs(currentPoint.z - target.z) <= request.object.stepHeight)
        {
            result.status = PathPlanStatus::Success;
            result.waypoints = rebuildPathToNode(nodes, openNode.nodeIndex);
            return result;
        }

        auto visitCandidate =
            [&](PathPoint candidate) -> void
        {
            ++result.debug.generatedCandidates;
            PathFloorSample candidateFloor = {};

            if (request.object.canFly)
            {
                if (!flyingPointIsValid(map, candidate))
                {
                    ++result.debug.rejectedFlyingInvalid;
                    return;
                }
            }
            else
            {
                bool candidateValid = false;
                candidate = snapGroundPoint(map, candidate, request.object, candidateValid, &candidateFloor);

                if (!candidateValid)
                {
                    ++result.debug.rejectedNoFloor;
                    return;
                }

                const float stepDeltaZ = std::fabs(candidate.z - currentPoint.z);

                if (!walkStepDeltaAllowed(currentPoint.z, candidate.z, request.object))
                {
                    ++result.debug.rejectedStepHeight;

                    if (stepDeltaZ > result.debug.maxRejectedStepDeltaZ)
                    {
                        result.debug.maxRejectedStepDeltaZ = stepDeltaZ;
                        result.debug.maxStepRejectFrom = currentPoint;
                        result.debug.maxStepRejectTo = candidate;
                    }

                    return;
                }
            }

            NodeKey key = makeNodeKey(candidate, stepSize);
            float newCost =
                currentCost + travelCost(currentPoint, candidate, request.object.canFly);
            auto found = nodeIndexByKey.find(key);

            if (found != nodeIndexByKey.end())
            {
                SearchNode &knownNode = nodes[found->second];

                if (knownNode.closed || newCost >= knownNode.cost)
                {
                    ++result.debug.rejectedDuplicate;
                    return;
                }
            }

            if (request.object.canFly)
            {
                if (!map.canReachDirectly(currentPoint, candidate, request.object))
                {
                    ++result.debug.rejectedWalkSegment;
                    return;
                }
            }
            else
            {
                const PathPoint requestedCandidate = candidate;
                if (!map.resolveWalkStep(currentPoint, candidate, request.object))
                {
                    ++result.debug.rejectedWalkSegment;
                    return;
                }
                if (candidate.x != requestedCandidate.x || candidate.y != requestedCandidate.y)
                {
                    candidateFloor = map.floorAt({candidate.x, candidate.y, candidate.z + PlannerEpsilon});
                    key = makeNodeKey(candidate, stepSize);
                    newCost = currentCost + travelCost(currentPoint, candidate, false);
                    found = nodeIndexByKey.find(key);
                    if (found != nodeIndexByKey.end()
                        && (nodes[found->second].closed || newCost >= nodes[found->second].cost))
                    {
                        ++result.debug.rejectedDuplicate;
                        return;
                    }
                }
            }

            if (found != nodeIndexByKey.end())
            {
                SearchNode &knownNode = nodes[found->second];

                knownNode.point = candidate;
                knownNode.cost = newCost;
                knownNode.estimate = newCost + heuristic(candidate, target, request.object.canFly);
                knownNode.parentIndex = openNode.nodeIndex;
                knownNode.floorFacetIndex = request.object.canFly
                    ? static_cast<size_t>(-1)
                    : candidateFloor.facetIndex;
                openSet.push({knownNode.estimate, found->second});
                ++result.debug.acceptedCandidates;
                ++result.debug.reopenedCandidates;
                return;
            }

            SearchNode nextNode = {};
            nextNode.key = key;
            nextNode.point = candidate;
            nextNode.cost = newCost;
            nextNode.estimate = newCost + heuristic(candidate, target, request.object.canFly);
            nextNode.parentIndex = openNode.nodeIndex;
            nextNode.floorFacetIndex = request.object.canFly
                ? static_cast<size_t>(-1)
                : candidateFloor.facetIndex;
            const size_t nextIndex = nodes.size();
            nodes.push_back(nextNode);
            nodeIndexByKey[key] = nextIndex;
            openSet.push({nextNode.estimate, nextIndex});
            ++result.debug.acceptedCandidates;
        };

        if (request.object.canFly)
        {
            for (int dx : directions3d)
            {
                for (int dy : directions3d)
                {
                    for (int dz : directions3d)
                    {
                        if (dx == 0 && dy == 0 && dz == 0)
                        {
                            continue;
                        }

                        visitCandidate({
                            currentPoint.x + static_cast<float>(dx) * stepSize,
                            currentPoint.y + static_cast<float>(dy) * stepSize,
                            currentPoint.z + static_cast<float>(dz) * stepSize
                        });
                    }
                }
            }
        }
        else
        {
            for (const int *direction : directions2d)
            {
                visitCandidate({
                    currentPoint.x + static_cast<float>(direction[0]) * stepSize,
                    currentPoint.y + static_cast<float>(direction[1]) * stepSize,
                    currentPoint.z
                });
            }
        }
    }

    if (request.allowPartialPath && bestPartialNodeIndex != 0)
    {
        result.waypoints = rebuildPathToNode(nodes, bestPartialNodeIndex);

        if (!result.waypoints.empty())
        {
            result.status = PathPlanStatus::Partial;
            return result;
        }
    }

    result.status = PathPlanStatus::NoRoute;
    return result;
}
}
