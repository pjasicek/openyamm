#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
struct PathPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct PathBounds
{
    float minX = 0.0f;
    float maxX = 0.0f;
    float minY = 0.0f;
    float maxY = 0.0f;
    float minZ = 0.0f;
    float maxZ = 0.0f;
};

enum class PathFacetKind
{
    Generic,
    Floor,
    Wall,
    Ceiling,
    Portal
};

struct PathFacetAttributes
{
    bool portal = false;
    bool invisible = false;
    bool untouchable = false;
};

struct PathFacet
{
    std::vector<PathPoint> vertices;
    PathFacetKind kind = PathFacetKind::Generic;
    PathFacetAttributes attributes;
    bool blocking = true;
    bool walkableFloor = false;
    bool dynamic = false;
    int32_t sourceId = -1;
};

struct PathFloorSample
{
    bool hasFloor = false;
    bool inVoid = false;
    float z = 0.0f;
    float normalZ = 0.0f;
    size_t facetIndex = 0;
};

struct PathFloorQueryDebug
{
    PathPoint position;
    PathFloorSample result;
    size_t candidateCount = 0;
    size_t invalidFacetCount = 0;
    size_t nonWalkableCount = 0;
    size_t boundsRejectCount = 0;
    size_t polygonRejectCount = 0;
    size_t belowCount = 0;
    size_t aboveCount = 0;
    PathFloorSample bestBelow;
    PathFloorSample bestAbove;
};

struct PathObject
{
    bool canFly = false;
    float radius = 0.0f;
    // Walking height above the feet; zero uses only the lower radius probe.
    float height = 0.0f;
    float stepLength = 24.0f;
    float stepHeight = 40.0f;
    float dropHeight = 40.0f;
    // A face the walking body's low side probes touch whose top is at most this far above its floor is a stair it
    // climbs, not a wall (a stair whose treads are shorter than the radius); 0: none. Indoors only.
    float riserHeight = 0.0f;
};

enum class PathWalkRejectReason
{
    None,
    InvalidInput,
    StartNoFloor,
    StartVoid,
    SampleNoFloor,
    SampleVoid,
    StepHeight,
    Blocked
};

struct PathWalkSegmentDebug
{
    bool success = false;
    PathWalkRejectReason rejectReason = PathWalkRejectReason::None;
    PathPoint from;
    PathPoint to;
    PathPoint probe;
    PathPoint blockedPoint;
    PathFloorSample startFloor;
    PathFloorSample previousFloor;
    PathFloorSample failedFloor;
    size_t sampleIndex = 0;
    size_t sampleCount = 0;
    size_t blockedFacet = static_cast<size_t>(-1);
    float stepDeltaZ = 0.0f;
};

struct PathPlanRequest
{
    size_t actorIndex = 0;
    PathPoint source;
    PathPoint target;
    PathObject object;
    int32_t preferredSourceFacetSourceId = -1;
    size_t nodeLimit = 8000;
    uint32_t mapRevision = 0;
    float sourceSnapDistance = 0.0f;
    // A route may end at any point this close to the target (level), the arrival of a script's walk: a point that the
    // body cannot reach exactly (closer to a wall than its radius) still has a short route (0: the target itself).
    float goalDistance = 0.0f;
    bool allowPartialPath = false;
    bool allowDirect = true;
};

struct PathPlanDebugInfo
{
    bool sourceValid = false;
    bool targetValid = false;
    bool directReachable = false;
    bool preferredSourceSnapUsed = false;
    PathPoint requestSource;
    PathPoint requestTarget;
    PathPoint snappedSource;
    PathPoint snappedTarget;
    PathPoint bestPoint;
    PathPoint maxStepRejectFrom;
    PathPoint maxStepRejectTo;
    size_t sourceFloorFacet = static_cast<size_t>(-1);
    size_t targetFloorFacet = static_cast<size_t>(-1);
    size_t bestFloorFacet = static_cast<size_t>(-1);
    int32_t preferredSourceFacetSourceId = -1;
    float bestDistance2d = 0.0f;
    float bestDistance3d = 0.0f;
    float maxRejectedStepDeltaZ = 0.0f;
    size_t generatedCandidates = 0;
    size_t acceptedCandidates = 0;
    size_t rejectedNoFloor = 0;
    size_t rejectedStepHeight = 0;
    size_t rejectedWalkSegment = 0;
    size_t rejectedFlyingInvalid = 0;
    size_t rejectedDuplicate = 0;
    size_t reopenedCandidates = 0;
    size_t skippedClosedNodes = 0;
};

enum class PathPlanStatus
{
    NotRequested,
    Success,
    Partial,
    NoRoute,
    NodeLimitExceeded,
    StaleRevision
};

struct PathPlanResult
{
    PathPlanStatus status = PathPlanStatus::NotRequested;
    std::vector<PathPoint> waypoints;
    PathPlanDebugInfo debug;
    size_t analyzedNodeCount = 0;
    uint32_t mapRevision = 0;
};

struct ActorPathState
{
    PathPoint targetSnapshot;
    PathPoint sourceSnapshot;
    std::vector<PathPoint> waypoints;
    size_t waypointIndex = 0;
    uint64_t requestId = 0;
    bool inProgress = false;
    bool directCheckValid = false;
    bool lastDirectReachable = false;
    PathPoint directCheckSource;
    PathPoint directCheckTarget;
    PathObject directCheckObject;
    bool recoverySourceWaypointActive = false;
    bool recoveryBestWaypointActive = false;
    PathPlanStatus planStatus = PathPlanStatus::NotRequested;
    double failedUntilSeconds = 0.0;
    double nextDirectCheckSeconds = 0.0;
    double lastDirectCheckSeconds = 0.0;
    double nextPlanSeconds = 0.0;
    double nextShortcutCheckSeconds = 0.0;
    double lastWaypointProgressSeconds = 0.0;
    float bestWaypointDistance = 0.0f;
    bool waypointProgressObserved = false;
    float targetMovedThreshold = 1024.0f;
    // Its route was dropped where it stood held short of a waypoint (advanceStalledWaypoint): planned again at once.
    bool replanHeldRoute = false;
    size_t progressWaypointIndex = 0;
    PathPoint lastSourcePosition;
    uint32_t mapRevision = 0;
};
}
