#pragma once

#include "game/pathfinding/PathPlanner.h"
#include "game/pathfinding/PathfindingTypes.h"

#include <condition_variable>
#include <cstddef>
#include <optional>
#include <deque>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

namespace OpenYAMM::Game
{
enum class ActorPathDiscardReason
{
    None,
    StaleGeneration,
    StaleTarget,
    StaleSource
};

struct ActorPathResolveRequest
{
    size_t actorIndex = 0;
    PathPoint source;
    PathPoint target;
    PathObject object;
    int32_t preferredSourceFacetSourceId = -1;
    size_t nodeLimit = 8000;
    size_t mapRevision = 0;
    float sourceSnapDistance = 0.0f;
    float planningRange = 12000.0f;
    float waypointReachDistance = 0.0f;
    double nowSeconds = 0.0;
    double failedRetrySeconds = 3.0;
    double directCheckIntervalSeconds = 0.25;
    float distantRouteReuseDistance = 0.0f;
    double distantRouteCheckIntervalSeconds = 1.0;
    double minReplanIntervalSeconds = 1.0;
    double shortcutCheckIntervalSeconds = 0.5;
    bool allowPlan = true;
    bool allowDirect = true;
    bool allowPartialPath = false;
};

struct ActorPathResolveResult
{
    bool directChecked = false;
    bool directReachable = false;
    bool pathActive = false;
    bool planned = false;
    // This call started a new plan: queued it for a worker, or planned it in place without workers. Taking up a
    // finished plan sets `planned` only.
    bool requested = false;
    bool failed = false;
    bool cooldown = false;
    bool deferred = false;
    bool outOfRange = false;
    bool queued = false;
    bool discarded = false;
    ActorPathDiscardReason discardReason = ActorPathDiscardReason::None;
    PathPlanStatus planStatus = PathPlanStatus::NotRequested;
    PathPlanDebugInfo planDebug;
    size_t analyzedNodeCount = 0;
    size_t waypointCount = 0;
    size_t waypointIndex = 0;
    size_t reachedWaypointCount = 0;
    size_t shortcutWaypointCount = 0;
    size_t stalledWaypointCount = 0;
    PathPoint waypoint;
};

class ActorPathRuntime
{
public:
    ActorPathRuntime() = default;
    ActorPathRuntime(const ActorPathRuntime &other) = delete;
    ActorPathRuntime &operator=(const ActorPathRuntime &other) = delete;
    ~ActorPathRuntime();

    void setWorkerCount(size_t workerCount);
    void clear();
    void beginReachabilityFrame(size_t maxChecks);
    void resetActor(size_t actorIndex);
    bool actorHasPendingPlan(size_t actorIndex) const;
    bool actorHasActivePath(size_t actorIndex) const;
    ActorPathResolveResult resolveWaypoint(const PathMap &pathMap, const ActorPathResolveRequest &request);
    ActorPathResolveResult resolveWaypoint(
        std::shared_ptr<const PathMap> pathMap,
        const ActorPathResolveRequest &request);

private:
    struct PendingPlanJob
    {
        uint64_t jobId = 0;
        uint64_t generation = 0;
        ActorPathResolveRequest request;
        std::shared_ptr<const PathMap> pathMap;
    };

    struct CompletedPlanJob
    {
        uint64_t jobId = 0;
        uint64_t generation = 0;
        ActorPathResolveRequest request;
        PathPlanResult result;
    };

    ActorPathResolveResult resolveWaypointInternal(
        const PathMap &pathMap,
        std::shared_ptr<const PathMap> pathMapSnapshot,
        const ActorPathResolveRequest &request
    );
    ActorPathState &stateForActor(size_t actorIndex);
    bool pathIsStale(const ActorPathState &state, const ActorPathResolveRequest &request) const;
    bool pathCanStillBeFollowed(const ActorPathState &state) const;
    bool consumeReachabilityCheck(size_t actorIndex);
    void resetWaypointProgress(ActorPathState &state, const ActorPathResolveRequest &request) const;
    size_t advanceReachedWaypoints(
        const PathMap &pathMap,
        ActorPathState &state,
        const ActorPathResolveRequest &request
    );
    size_t advanceShortcutWaypoints(
        const PathMap &pathMap,
        ActorPathState &state,
        const ActorPathResolveRequest &request
    );
    size_t advanceStalledWaypoint(
        const PathMap &pathMap,
        ActorPathState &state,
        const ActorPathResolveRequest &request
    );
    bool consumeCompletedPlan(
        ActorPathState &state,
        const ActorPathResolveRequest &request,
        ActorPathResolveResult &result
    );
    bool installPlanResult(
        ActorPathState &state,
        const ActorPathResolveRequest &request,
        const PathPlanResult &planResult,
        ActorPathResolveResult &result
    );
    bool queuePlan(
        const PathMap &pathMap,
        const std::shared_ptr<const PathMap> &pathMapSnapshot,
        ActorPathState &state,
        const ActorPathResolveRequest &request,
        ActorPathResolveResult &result
    );
    void discardCompletedPlans(size_t actorIndex);
    void stopWorkers();
    void workerLoop();

    PathPlanner m_planner;
    std::vector<ActorPathState> m_actorStates;
    std::deque<size_t> m_pendingReachabilityActors;
    std::vector<bool> m_reachabilityQueued;
    std::vector<bool> m_reachabilityGranted;
    size_t m_reachabilityChecksRemaining = 0;
    bool m_reachabilityBudgetEnabled = false;
    std::mutex m_jobMutex;
    std::condition_variable m_jobCondition;
    std::deque<PendingPlanJob> m_pendingPlanJobs;
    std::deque<CompletedPlanJob> m_completedPlanJobs;
    std::vector<std::thread> m_workers;
    uint64_t m_nextJobId = 1;
    uint64_t m_generation = 1;
    bool m_stopWorkers = false;
};
}
