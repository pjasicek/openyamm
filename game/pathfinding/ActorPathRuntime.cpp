#include "game/pathfinding/ActorPathRuntime.h"

#include <cstdlib>

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MaxShortcutWaypointScan = 24;
constexpr size_t MaxGroundShortcutWaypointScan = 6;
constexpr float MaxGroundShortcutStepMultiplier = 6.0f;
constexpr double WaypointStallSeconds = 0.35;
constexpr double WaypointBlockedSeconds = 2.0;
constexpr float WaypointProgressEpsilon = 2.0f;
constexpr float RecoverySourceReachDistance = 4.0f;
constexpr float RecoveryBestReachDistance = 16.0f;

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

bool directCheckObjectMatchesRequest(const ActorPathState &state, const ActorPathResolveRequest &request)
{
    const PathObject &previousObject = state.directCheckObject;
    const PathObject &object = request.object;
    return state.directCheckValid
        && previousObject.canFly == object.canFly
        && previousObject.radius == object.radius
        && previousObject.height == object.height
        && previousObject.stepLength == object.stepLength
        && previousObject.stepHeight == object.stepHeight
        && previousObject.dropHeight == object.dropHeight
        && previousObject.riserHeight == object.riserHeight;
}

bool directCheckMatchesRequest(const ActorPathState &state, const ActorPathResolveRequest &request)
{
    const float movementLimit = std::max(1.0f, std::min(request.object.radius, request.object.stepLength));
    return directCheckObjectMatchesRequest(state, request)
        && distanceSquared3d(state.directCheckSource, request.source) <= movementLimit * movementLimit
        && distanceSquared3d(state.directCheckTarget, request.target) <= movementLimit * movementLimit;
}

void recordDirectCheck(ActorPathState &state, const ActorPathResolveRequest &request, bool reachable)
{
    state.directCheckValid = request.allowDirect;
    state.lastDirectReachable = reachable;
    state.directCheckSource = request.source;
    state.directCheckTarget = request.target;
    state.directCheckObject = request.object;
    state.lastDirectCheckSeconds = request.nowSeconds;
    state.mapRevision = static_cast<uint32_t>(request.mapRevision);
    state.nextDirectCheckSeconds = request.nowSeconds + std::max(0.01, request.directCheckIntervalSeconds);
}

bool pathWaypointReached(const PathPoint &source, const PathPoint &waypoint, float reachDistance)
{
    return distance2d(source, waypoint) <= std::max(1.0f, reachDistance);
}

bool planHasReachableBestPoint(const PathPlanResult &planResult, const ActorPathResolveRequest &request)
{
    if (planResult.debug.acceptedCandidates == 0)
    {
        return false;
    }

    const float reachDistance = std::max(request.waypointReachDistance, RecoveryBestReachDistance);
    return distanceSquared2d(planResult.debug.bestPoint, request.source) > reachDistance * reachDistance;
}

float relaxedWaypointReachDistance(const ActorPathResolveRequest &request)
{
    const float reachDistance = std::max(1.0f, request.waypointReachDistance);
    const float stepSlack = std::max(8.0f, request.object.stepLength * 0.75f);
    return std::max(reachDistance * 1.25f, reachDistance + stepSlack);
}

size_t firstUnreachedWaypointIndex(
    const std::vector<PathPoint> &waypoints,
    const PathPoint &source,
    float reachDistance
)
{
    size_t index = 0;

    while (index < waypoints.size()
        && pathWaypointReached(source, waypoints[index], reachDistance))
    {
        ++index;
    }

    return index;
}

size_t closestUnreachedWaypointIndex(
    const std::vector<PathPoint> &waypoints,
    const PathPoint &source,
    float reachDistance
)
{
    size_t bestIndex = waypoints.size();
    float bestDistance = std::numeric_limits<float>::max();

    for (size_t index = 0; index < waypoints.size(); ++index)
    {
        if (pathWaypointReached(source, waypoints[index], reachDistance))
        {
            bestIndex = index + 1;
            bestDistance = 0.0f;
            continue;
        }

        const float distance = distanceSquared3d(source, waypoints[index]);

        if (distance < bestDistance)
        {
            bestDistance = distance;
            bestIndex = index;
        }
    }

    return bestIndex;
}

}

ActorPathRuntime::~ActorPathRuntime()
{
    stopWorkers();
}

void ActorPathRuntime::setWorkerCount(size_t workerCount)
{
    // Headless runs simulate many seconds in a few wall-clock milliseconds, so a plan on a worker would land long
    // after the moment it was asked for (or never): they plan on the calling thread (main.cpp sets the variable).
    static const bool synchronousPlans = std::getenv("OPENYAMM_SYNCHRONOUS_PATH_PLANS") != nullptr;

    if (synchronousPlans)
    {
        workerCount = 0;
    }

    if (workerCount == m_workers.size())
    {
        return;
    }

    stopWorkers();

    if (workerCount == 0)
    {
        return;
    }

    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        m_stopWorkers = false;
    }

    m_workers.reserve(workerCount);

    for (size_t index = 0; index < workerCount; ++index)
    {
        m_workers.emplace_back(&ActorPathRuntime::workerLoop, this);
    }
}

void ActorPathRuntime::clear()
{
    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        ++m_generation;
        m_pendingPlanJobs.clear();
        m_completedPlanJobs.clear();
    }

    m_actorStates.clear();
    m_pendingReachabilityActors.clear();
    m_reachabilityQueued.clear();
    m_reachabilityGranted.clear();
    m_reachabilityBudgetEnabled = false;
}

void ActorPathRuntime::beginReachabilityFrame(size_t maxChecks)
{
    m_reachabilityBudgetEnabled = true;
    m_reachabilityChecksRemaining = maxChecks;
    std::fill(m_reachabilityGranted.begin(), m_reachabilityGranted.end(), false);
    // Reserve checks for actors deferred earlier, rather than favouring the first actor in every AI step.
    while (m_reachabilityChecksRemaining != 0 && !m_pendingReachabilityActors.empty())
    {
        const size_t actorIndex = m_pendingReachabilityActors.front();
        m_pendingReachabilityActors.pop_front();
        if (!m_reachabilityQueued[actorIndex])
        {
            continue;
        }
        m_reachabilityQueued[actorIndex] = false;
        m_reachabilityGranted[actorIndex] = true;
        --m_reachabilityChecksRemaining;
    }
}

bool ActorPathRuntime::consumeReachabilityCheck(size_t actorIndex)
{
    if (!m_reachabilityBudgetEnabled)
    {
        return true;
    }
    if (actorIndex >= m_reachabilityQueued.size())
    {
        m_reachabilityQueued.resize(actorIndex + 1, false);
        m_reachabilityGranted.resize(actorIndex + 1, false);
    }
    if (m_reachabilityGranted[actorIndex])
    {
        m_reachabilityGranted[actorIndex] = false;
        return true;
    }
    if (m_reachabilityChecksRemaining != 0)
    {
        --m_reachabilityChecksRemaining;
        return true;
    }
    if (!m_reachabilityQueued[actorIndex])
    {
        m_pendingReachabilityActors.push_back(actorIndex);
        m_reachabilityQueued[actorIndex] = true;
    }
    return false;
}

void ActorPathRuntime::resetActor(size_t actorIndex)
{
    if (actorIndex < m_actorStates.size())
    {
        m_actorStates[actorIndex] = {};
    }
    if (actorIndex < m_reachabilityQueued.size())
    {
        m_reachabilityQueued[actorIndex] = false;
        m_reachabilityGranted[actorIndex] = false;
    }
}

bool ActorPathRuntime::actorHasPendingPlan(size_t actorIndex) const
{
    return actorIndex < m_actorStates.size() && m_actorStates[actorIndex].inProgress;
}

bool ActorPathRuntime::actorHasActivePath(size_t actorIndex) const
{
    return actorIndex < m_actorStates.size() && pathCanStillBeFollowed(m_actorStates[actorIndex]);
}

ActorPathResolveResult ActorPathRuntime::resolveWaypoint(
    const PathMap &pathMap,
    const ActorPathResolveRequest &request
)
{
    return resolveWaypointInternal(pathMap, nullptr, request);
}

ActorPathResolveResult ActorPathRuntime::resolveWaypoint(
    std::shared_ptr<const PathMap> pathMap,
    const ActorPathResolveRequest &request
)
{
    if (pathMap == nullptr)
    {
        return {};
    }

    std::shared_ptr<const PathMap> pathMapSnapshot = std::move(pathMap);
    const PathMap &pathMapReference = *pathMapSnapshot;
    return resolveWaypointInternal(pathMapReference, pathMapSnapshot, request);
}

ActorPathResolveResult ActorPathRuntime::resolveWaypointInternal(
    const PathMap &pathMap,
    std::shared_ptr<const PathMap> pathMapSnapshot,
    const ActorPathResolveRequest &request
)
{
    ActorPathResolveResult result = {};
    ActorPathState &state = stateForActor(request.actorIndex);
    const float planningRangeSquared = request.planningRange * request.planningRange;

    if (!state.inProgress)
    {
        discardCompletedPlans(request.actorIndex);
    }

    if (distanceSquared3d(request.source, request.target) > planningRangeSquared)
    {
        state = {};
        result.outOfRange = true;
        return result;
    }

    if (state.mapRevision != 0 && state.mapRevision != static_cast<uint32_t>(request.mapRevision))
    {
        state = {};
    }

    result.reachedWaypointCount += advanceReachedWaypoints(pathMap, state, request);

    // A failed straight-line probe is only a shortcut opportunity when a valid route already exists.
    // Distant actors can follow that route while its endpoints move, without assuming a clear straight line.
    const bool reuseBlockedCheck = request.distantRouteReuseDistance > 0.0f
        && !state.lastDirectReachable
        && !pathIsStale(state, request)
        && directCheckObjectMatchesRequest(state, request)
        && distanceSquared3d(request.source, request.target)
            > request.distantRouteReuseDistance * request.distantRouteReuseDistance;

    if (!request.allowDirect || (!reuseBlockedCheck && !directCheckMatchesRequest(state, request)))
    {
        state.directCheckValid = false;
        state.lastDirectReachable = false;
    }

    const double directCheckDeadline = reuseBlockedCheck
        ? state.lastDirectCheckSeconds + std::max(0.01, request.distantRouteCheckIntervalSeconds)
        : state.nextDirectCheckSeconds;
    const bool directCheckDue =
        request.allowDirect
        && (!state.directCheckValid || request.nowSeconds >= directCheckDeadline);

    if (directCheckDue)
    {
        if (consumeReachabilityCheck(request.actorIndex))
        {
            const bool directReachable = pathMap.canReachDirectly(request.source, request.target, request.object);
            result.directChecked = true;
            if (directReachable)
            {
                state = {};
            }
            recordDirectCheck(state, request, directReachable);
        }
        else
        {
            result.deferred = true;
        }
    }

    if (request.allowDirect && state.directCheckValid && state.lastDirectReachable)
    {
        result.directReachable = true;
        return result;
    }

    consumeCompletedPlan(state, request, result);

    const bool stalePath = pathIsStale(state, request);
    const bool activePathBeforePlan = pathCanStillBeFollowed(state);

    // An unchecked route is not a failed route. Keep following a valid path while waiting for the check.
    if (directCheckDue && !result.directChecked && !activePathBeforePlan)
    {
        return result;
    }

    if (stalePath && !(directCheckDue && !result.directChecked))
    {
        const bool actorPlanReady = request.nowSeconds >= state.nextPlanSeconds;

        if (state.failedUntilSeconds > request.nowSeconds)
        {
            if (!activePathBeforePlan)
            {
                result.cooldown = true;
                return result;
            }
        }
        else if (state.inProgress)
        {
            result.deferred = true;
            return result;
        }
        else if (!request.allowPlan || !actorPlanReady)
        {
            if (!activePathBeforePlan)
            {
                result.deferred = true;
                return result;
            }
        }
        else
        {
            queuePlan(pathMap, pathMapSnapshot, state, request, result);

            if (result.failed && !pathCanStillBeFollowed(state))
            {
                return result;
            }

            if (result.queued)
            {
                result.deferred = true;
                return result;
            }
        }
    }

    result.reachedWaypointCount += advanceReachedWaypoints(pathMap, state, request);
    result.shortcutWaypointCount += advanceShortcutWaypoints(pathMap, state, request);

    if (!result.planned)
    {
        result.stalledWaypointCount += advanceStalledWaypoint(pathMap, state, request);

        if (state.replanHeldRoute)
        {
            state.replanHeldRoute = false;

            if (request.allowPlan && !state.inProgress && state.failedUntilSeconds <= request.nowSeconds)
            {
                queuePlan(pathMap, pathMapSnapshot, state, request, result);
            }
        }
    }

    if (state.waypointIndex < state.waypoints.size())
    {
        result.pathActive = true;
        result.waypointIndex = state.waypointIndex;
        result.waypoint = state.waypoints[state.waypointIndex];
    }

    return result;
}

bool ActorPathRuntime::consumeCompletedPlan(
    ActorPathState &state,
    const ActorPathResolveRequest &request,
    ActorPathResolveResult &result
)
{
    if (!state.inProgress || state.requestId == 0)
    {
        return false;
    }

    CompletedPlanJob completedJob = {};
    uint64_t currentGeneration = 0;
    bool found = false;

    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        currentGeneration = m_generation;

        for (auto it = m_completedPlanJobs.begin(); it != m_completedPlanJobs.end(); ++it)
        {
            if (it->request.actorIndex != request.actorIndex || it->jobId != state.requestId)
            {
                continue;
            }

            completedJob = std::move(*it);
            m_completedPlanJobs.erase(it);
            found = true;
            break;
        }
    }

    if (!found)
    {
        return false;
    }

    state.inProgress = false;

    result.planStatus = completedJob.result.status;
    result.planDebug = completedJob.result.debug;
    result.analyzedNodeCount = completedJob.result.analyzedNodeCount;
    result.waypointCount = completedJob.result.waypoints.size();

    if (completedJob.generation != currentGeneration
        || completedJob.request.mapRevision != request.mapRevision)
    {
        state = {};
        result.discarded = true;
        result.discardReason = ActorPathDiscardReason::StaleGeneration;
        return false;
    }

    const float targetMovedThreshold = std::max(1.0f, state.targetMovedThreshold);

    if (distanceSquared3d(completedJob.request.target, request.target)
        > targetMovedThreshold * targetMovedThreshold)
    {
        state.requestId = 0;
        result.discarded = true;
        result.discardReason = ActorPathDiscardReason::StaleTarget;
        return false;
    }

    return installPlanResult(state, request, completedJob.result, result);
}

bool ActorPathRuntime::installPlanResult(
    ActorPathState &state,
    const ActorPathResolveRequest &request,
    const PathPlanResult &planResult,
    ActorPathResolveResult &result
)
{
    result.planned = true;
    result.planStatus = planResult.status;
    result.planDebug = planResult.debug;
    result.analyzedNodeCount = planResult.analyzedNodeCount;
    result.waypointCount = planResult.waypoints.size();
    const bool hadActivePath = pathCanStillBeFollowed(state);

    const bool usablePlan =
        planResult.status == PathPlanStatus::Success
        || (request.allowPartialPath && planResult.status == PathPlanStatus::Partial);

    if (!usablePlan || planResult.waypoints.empty())
    {
        const bool useRecoveryBestWaypoint =
            !hadActivePath
            && planHasReachableBestPoint(planResult, request);

        if (!hadActivePath)
        {
            state = {};
        }

        state.inProgress = false;
        state.requestId = 0;
        state.failedUntilSeconds = request.nowSeconds + std::max(0.1, request.failedRetrySeconds);
        state.nextPlanSeconds = state.failedUntilSeconds;
        recordDirectCheck(state, request, false);
        result.failed = true;

        if (useRecoveryBestWaypoint)
        {
            state.targetSnapshot = request.target;
            state.sourceSnapshot = request.source;
            state.lastSourcePosition = request.source;
            state.mapRevision = static_cast<uint32_t>(request.mapRevision);
            state.waypoints = {planResult.debug.bestPoint};
            state.waypointIndex = 0;
            state.recoveryBestWaypointActive = true;
            state.planStatus = planResult.status;
            resetWaypointProgress(state, request);
            result.pathActive = true;
            result.waypointIndex = state.waypointIndex;
            result.waypoint = state.waypoints[state.waypointIndex];
        }

        return false;
    }

    std::vector<PathPoint> waypoints = planResult.waypoints;
    bool recoverySourceWaypointActive = false;

    if (planResult.debug.preferredSourceSnapUsed
        && distanceSquared2d(planResult.debug.snappedSource, request.source)
            > RecoverySourceReachDistance * RecoverySourceReachDistance)
    {
        waypoints.insert(waypoints.begin(), planResult.debug.snappedSource);
        recoverySourceWaypointActive = true;
    }

    size_t firstWaypointIndex =
        recoverySourceWaypointActive
            ? 0
            : firstUnreachedWaypointIndex(waypoints, request.source, request.waypointReachDistance);
    const float sourceMovedThreshold =
        std::max(request.waypointReachDistance * 2.0f, request.object.stepLength * 4.0f);

    if (!recoverySourceWaypointActive
        && distanceSquared2d(planResult.debug.requestSource, request.source)
        > sourceMovedThreshold * sourceMovedThreshold)
    {
        firstWaypointIndex =
            closestUnreachedWaypointIndex(waypoints, request.source, request.waypointReachDistance);
    }

    state.targetSnapshot = request.target;
    state.sourceSnapshot = request.source;
    state.lastSourcePosition = request.source;
    state.mapRevision = static_cast<uint32_t>(request.mapRevision);
    state.waypoints = std::move(waypoints);
    state.waypointIndex = firstWaypointIndex;
    state.recoverySourceWaypointActive = recoverySourceWaypointActive;
    state.inProgress = false;
    state.requestId = 0;
    state.failedUntilSeconds = 0.0;
    recordDirectCheck(state, request, false);
    state.planStatus = planResult.status;
    state.nextPlanSeconds = request.nowSeconds + std::max(0.0, request.minReplanIntervalSeconds);
    state.nextShortcutCheckSeconds = 0.0;
    resetWaypointProgress(state, request);

    return true;
}

bool ActorPathRuntime::queuePlan(
    const PathMap &pathMap,
    const std::shared_ptr<const PathMap> &pathMapSnapshot,
    ActorPathState &state,
    const ActorPathResolveRequest &request,
    ActorPathResolveResult &result
)
{
    PathPlanRequest planRequest = {};
    planRequest.actorIndex = request.actorIndex;
    planRequest.source = request.source;
    planRequest.target = request.target;
    planRequest.object = request.object;
    planRequest.preferredSourceFacetSourceId = request.preferredSourceFacetSourceId;
    planRequest.nodeLimit = request.nodeLimit;
    planRequest.mapRevision = static_cast<uint32_t>(request.mapRevision);
    planRequest.sourceSnapDistance = request.sourceSnapDistance;
    planRequest.goalDistance = request.goalDistance;
    planRequest.allowDirect = request.allowDirect;
    planRequest.allowPartialPath = request.allowPartialPath;
    result.requested = true;

    if (m_workers.empty())
    {
        const PathPlanResult planResult = m_planner.plan(pathMap, planRequest);
        return installPlanResult(state, request, planResult, result);
    }

    PendingPlanJob job = {};
    job.request = request;
    job.pathMap =
        pathMapSnapshot != nullptr
            ? pathMapSnapshot
            : std::make_shared<PathMap>(pathMap);

    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        job.jobId = m_nextJobId++;
        job.generation = m_generation;
        m_pendingPlanJobs.push_back(job);
    }

    state.requestId = job.jobId;
    state.inProgress = true;
    state.nextPlanSeconds = request.nowSeconds + std::max(0.0, request.minReplanIntervalSeconds);
    result.queued = true;

    m_jobCondition.notify_one();
    return true;
}

void ActorPathRuntime::discardCompletedPlans(size_t actorIndex)
{
    std::lock_guard<std::mutex> lock(m_jobMutex);

    for (auto it = m_completedPlanJobs.begin(); it != m_completedPlanJobs.end();)
    {
        if (it->request.actorIndex == actorIndex)
        {
            it = m_completedPlanJobs.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

ActorPathState &ActorPathRuntime::stateForActor(size_t actorIndex)
{
    if (actorIndex >= m_actorStates.size())
    {
        m_actorStates.resize(actorIndex + 1);
    }

    return m_actorStates[actorIndex];
}

bool ActorPathRuntime::pathIsStale(
    const ActorPathState &state,
    const ActorPathResolveRequest &request
) const
{
    if (state.waypoints.empty() || state.waypointIndex >= state.waypoints.size())
    {
        return true;
    }

    if (state.mapRevision != static_cast<uint32_t>(request.mapRevision))
    {
        return true;
    }

    const float targetMovedThreshold = std::max(1.0f, state.targetMovedThreshold);
    return distanceSquared3d(state.targetSnapshot, request.target) > targetMovedThreshold * targetMovedThreshold;
}

bool ActorPathRuntime::pathCanStillBeFollowed(const ActorPathState &state) const
{
    return !state.waypoints.empty() && state.waypointIndex < state.waypoints.size();
}

void ActorPathRuntime::resetWaypointProgress(
    ActorPathState &state,
    const ActorPathResolveRequest &request
) const
{
    state.progressWaypointIndex = state.waypointIndex;
    state.lastWaypointProgressSeconds = request.nowSeconds;
    state.waypointProgressObserved = false;

    if (state.waypointIndex < state.waypoints.size())
    {
        state.bestWaypointDistance = distance2d(request.source, state.waypoints[state.waypointIndex]);
    }
    else
    {
        state.bestWaypointDistance = 0.0f;
    }
}

size_t ActorPathRuntime::advanceReachedWaypoints(
    const PathMap &pathMap,
    ActorPathState &state,
    const ActorPathResolveRequest &request
)
{
    const size_t originalIndex = state.waypointIndex;

    while (state.waypointIndex < state.waypoints.size()
        && pathWaypointReached(
            request.source,
            state.waypoints[state.waypointIndex],
            state.recoverySourceWaypointActive && state.waypointIndex == 0
                ? RecoverySourceReachDistance
                : (state.recoveryBestWaypointActive && state.waypointIndex == 0
                    ? RecoveryBestReachDistance
                    : request.waypointReachDistance)))
    {
        // The step to the next waypoint is a short trace outside the frame's reachability budget: waiting for the
        // budget held an actor jittering on a reached waypoint, so crowded indoor monsters crawled along their routes.
        if (state.waypointIndex + 1 < state.waypoints.size()
            && !pathMap.canReachDirectly(
                request.source,
                state.waypoints[state.waypointIndex + 1],
                request.object))
        {
            break;
        }

        ++state.waypointIndex;

        if (state.recoverySourceWaypointActive && state.waypointIndex > 0)
        {
            state.recoverySourceWaypointActive = false;
        }

        if (state.recoveryBestWaypointActive && state.waypointIndex > 0)
        {
            state.recoveryBestWaypointActive = false;
        }
    }

    if (state.waypointIndex != originalIndex)
    {
        resetWaypointProgress(state, request);
    }

    return state.waypointIndex - originalIndex;
}

size_t ActorPathRuntime::advanceShortcutWaypoints(
    const PathMap &pathMap,
    ActorPathState &state,
    const ActorPathResolveRequest &request
)
{
    if (!pathCanStillBeFollowed(state)
        || !request.allowDirect
        || request.nowSeconds < state.nextShortcutCheckSeconds)
    {
        return 0;
    }

    if (state.recoverySourceWaypointActive || state.recoveryBestWaypointActive)
    {
        return 0;
    }

    const double intervalSeconds = std::max(0.01, request.shortcutCheckIntervalSeconds);

    const size_t originalIndex = state.waypointIndex;
    const size_t maxShortcutWaypointScan =
        request.object.canFly ? MaxShortcutWaypointScan : MaxGroundShortcutWaypointScan;
    const size_t lastCandidateIndex =
        std::min(state.waypoints.size() - 1, originalIndex + maxShortcutWaypointScan);
    const float maxGroundShortcutDistance =
        std::max(request.object.stepLength, 1.0f) * MaxGroundShortcutStepMultiplier;
    const float maxGroundShortcutDistanceSquared =
        maxGroundShortcutDistance * maxGroundShortcutDistance;

    for (size_t index = lastCandidateIndex; index > originalIndex; --index)
    {
        if (!request.object.canFly
            && distanceSquared2d(request.source, state.waypoints[index]) > maxGroundShortcutDistanceSquared)
        {
            continue;
        }

        if (!consumeReachabilityCheck(request.actorIndex))
        {
            return 0;
        }
        state.nextShortcutCheckSeconds = request.nowSeconds + intervalSeconds;
        if (!pathMap.canReachDirectly(request.source, state.waypoints[index], request.object))
        {
            continue;
        }

        state.waypointIndex = index;
        resetWaypointProgress(state, request);
        return state.waypointIndex - originalIndex;
    }

    return 0;
}

size_t ActorPathRuntime::advanceStalledWaypoint(
    const PathMap &pathMap,
    ActorPathState &state,
    const ActorPathResolveRequest &request
)
{
    if (!pathCanStillBeFollowed(state))
    {
        return 0;
    }

    const float waypointDistance = distance2d(request.source, state.waypoints[state.waypointIndex]);

    if (state.progressWaypointIndex != state.waypointIndex)
    {
        resetWaypointProgress(state, request);
        return 0;
    }

    if (waypointDistance + WaypointProgressEpsilon < state.bestWaypointDistance)
    {
        state.bestWaypointDistance = waypointDistance;
        state.lastWaypointProgressSeconds = request.nowSeconds;
        state.waypointProgressObserved = true;
        return 0;
    }

    if (!state.waypointProgressObserved)
    {
        state.lastWaypointProgressSeconds = request.nowSeconds;
        state.waypointProgressObserved = true;
        return 0;
    }

    const bool nearWaypoint = waypointDistance <= relaxedWaypointReachDistance(request);
    const bool stalled = request.nowSeconds - state.lastWaypointProgressSeconds >= WaypointStallSeconds;

    if (!stalled)
    {
        return 0;
    }

    if (state.waypointIndex + 1 < state.waypoints.size()
        && !consumeReachabilityCheck(request.actorIndex))
    {
        return 0;
    }

    if (state.waypointIndex + 1 < state.waypoints.size()
        && !pathMap.canReachDirectly(
            request.source,
            state.waypoints[state.waypointIndex + 1],
            request.object))
    {
        // Near its waypoint it may still slide round the corner; one held there this long is stuck, and its route
        // is dropped to be planned again from where it stands. Kept for ever, it held Hjarrand (Thjorad Mine) at a
        // ramp's foot for good, his script's walk never ending.
        if (nearWaypoint && request.nowSeconds - state.lastWaypointProgressSeconds < WaypointBlockedSeconds)
        {
            return 0;
        }

        state.replanHeldRoute = nearWaypoint;
        state.waypointIndex = state.waypoints.size();
    }
    else
    {
        ++state.waypointIndex;
    }

    if (state.recoveryBestWaypointActive && state.waypointIndex >= state.waypoints.size())
    {
        state.recoveryBestWaypointActive = false;
    }

    resetWaypointProgress(state, request);
    return 1;
}

void ActorPathRuntime::stopWorkers()
{
    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        m_stopWorkers = true;
        m_pendingPlanJobs.clear();
    }

    m_jobCondition.notify_all();

    for (std::thread &worker : m_workers)
    {
        if (worker.joinable())
        {
            worker.join();
        }
    }

    {
        std::lock_guard<std::mutex> lock(m_jobMutex);
        m_workers.clear();
        m_completedPlanJobs.clear();
        m_stopWorkers = false;
    }
}

void ActorPathRuntime::workerLoop()
{
    PathPlanner planner;

    while (true)
    {
        PendingPlanJob job = {};

        {
            std::unique_lock<std::mutex> lock(m_jobMutex);
            m_jobCondition.wait(lock, [this]()
            {
                return m_stopWorkers || !m_pendingPlanJobs.empty();
            });

            if (m_stopWorkers)
            {
                return;
            }

            job = std::move(m_pendingPlanJobs.front());
            m_pendingPlanJobs.pop_front();
        }

        PathPlanRequest planRequest = {};
        planRequest.actorIndex = job.request.actorIndex;
        planRequest.source = job.request.source;
        planRequest.target = job.request.target;
        planRequest.object = job.request.object;
        planRequest.preferredSourceFacetSourceId = job.request.preferredSourceFacetSourceId;
        planRequest.nodeLimit = job.request.nodeLimit;
        planRequest.mapRevision = static_cast<uint32_t>(job.request.mapRevision);
        planRequest.sourceSnapDistance = job.request.sourceSnapDistance;
        planRequest.allowDirect = job.request.allowDirect;
        planRequest.allowPartialPath = job.request.allowPartialPath;

        CompletedPlanJob completedJob = {};
        completedJob.jobId = job.jobId;
        completedJob.generation = job.generation;
        completedJob.request = job.request;
        completedJob.result = planner.plan(*job.pathMap, planRequest);

        {
            std::lock_guard<std::mutex> lock(m_jobMutex);

            if (!m_stopWorkers && completedJob.generation == m_generation)
            {
                m_completedPlanJobs.push_back(std::move(completedJob));
            }
        }
    }
}
}
