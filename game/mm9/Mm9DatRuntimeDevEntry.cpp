#include "game/mm9/Mm9DatRuntimeDevEntry.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string lowerCopy(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

Mm9DatDevStartPose poseFromStartPoint(
    const Mm9DatLevelRuntimeLoadResult &level,
    const Mm9DatRuntimeStartPoint &startPoint,
    Mm9DatDevStartPoseSource source)
{
    Mm9DatDevStartPose pose = {};
    pose.mapId = level.metadata.mapId;
    pose.position = startPoint.position;
    pose.yawRadians = startPoint.yawRadians;
    pose.source = source;
    pose.sourceName = startPoint.name;
    pose.sourceObjectIndex = startPoint.sourceObjectIndex;
    pose.hasSourceObject = true;
    return pose;
}

Mm9DatDevStartPose fallbackPoseFromWorldBounds(const Mm9DatLevelRuntimeLoadResult &level)
{
    Mm9DatDevStartPose pose = {};
    pose.mapId = level.metadata.mapId;
    pose.source = Mm9DatDevStartPoseSource::WorldBoundsCenter;

    const Mm9DatRenderBounds bounds = computeMm9DatRenderBounds(level.runtime.renderMesh);
    if (bounds.valid)
    {
        pose.position = bounds.center;
        pose.position.y = bounds.max.y + 128.0f;
    }

    return pose;
}

void snapDevPoseToFloor(
    const Mm9DatWorldRuntime &runtime,
    Mm9DatDevStartPose &pose,
    float partyHalfHeight,
    float floorSnapDistance,
    float floorBias)
{
    if (floorSnapDistance <= 0.0f)
    {
        return;
    }

    Mm9DatFloorSupportQuery query = {};
    query.position = pose.position;
    query.channelMask = Mm9DatPhysicsQueryChannelPhysics;
    query.maxDropDistance = floorSnapDistance;
    query.halfHeight = std::max(0.0f, partyHalfHeight);
    query.placementBias = floorBias;

    const std::optional<Mm9DatFloorSupportHit> support =
        runtime.collisionWorld.findFloorSupport(query);

    if (!support)
    {
        return;
    }

    pose.position = support->adjustedPosition;
    pose.snappedToFloor = true;
    pose.floorCandidateTriangleCount = support->candidateTriangleCount;
    pose.floorTestedTriangleCount = support->testedTriangleCount;
}
}

std::optional<Mm9DatDevStartPose> chooseMm9DatDevStartPose(
    const Mm9DatLevelRuntimeLoadResult &level,
    const std::string &preferredStartName,
    float partyHalfHeight,
    float floorSnapDistance,
    float floorBias)
{
    const std::string normalizedPreferredStartName = lowerCopy(preferredStartName);
    const Mm9DatRuntimeStartPoint *pFirstStartPoint = nullptr;

    for (const Mm9DatRuntimeStartPoint &startPoint : level.startPoints)
    {
        if (pFirstStartPoint == nullptr)
        {
            pFirstStartPoint = &startPoint;
        }

        if (!normalizedPreferredStartName.empty()
            && lowerCopy(startPoint.name) == normalizedPreferredStartName)
        {
            Mm9DatDevStartPose pose =
                poseFromStartPoint(level, startPoint, Mm9DatDevStartPoseSource::PreferredStartPoint);
            if (startPoint.movePlayerToFloor)
            {
                snapDevPoseToFloor(level.runtime, pose, partyHalfHeight, floorSnapDistance, floorBias);
            }
            return pose;
        }
    }

    if (pFirstStartPoint != nullptr)
    {
        Mm9DatDevStartPose pose =
            poseFromStartPoint(level, *pFirstStartPoint, Mm9DatDevStartPoseSource::FirstStartPoint);
        if (pFirstStartPoint->movePlayerToFloor)
        {
            snapDevPoseToFloor(level.runtime, pose, partyHalfHeight, floorSnapDistance, floorBias);
        }
        return pose;
    }

    Mm9DatDevStartPose pose = fallbackPoseFromWorldBounds(level);
    snapDevPoseToFloor(level.runtime, pose, partyHalfHeight, floorSnapDistance, floorBias);

    if (pose.source == Mm9DatDevStartPoseSource::None)
    {
        return std::nullopt;
    }

    return pose;
}

std::optional<Mm9DatRuntimeDevEntryResult> loadMm9DatRuntimeForDevEntry(
    const Mm9DatRuntimeDevEntryRequest &request,
    std::string &errorMessage)
{
    if (request.mapId.empty())
    {
        errorMessage = "MM9 DAT dev entry requires a map id";
        return std::nullopt;
    }

    std::optional<Mm9DatLevelRuntimeLoadResult> level =
        loadMm9DatLevelRuntimeForMap(request.sourceRoot, request.mapId, errorMessage);

    if (!level)
    {
        return std::nullopt;
    }

    std::optional<Mm9DatDevStartPose> startPose =
        chooseMm9DatDevStartPose(
            *level,
            request.preferredStartName,
            request.partyHalfHeight,
            request.floorSnapDistance,
            request.floorBias);

    if (!startPose)
    {
        errorMessage = "could not derive MM9 DAT dev start pose for map '" + request.mapId + "'";
        return std::nullopt;
    }

    Mm9DatRuntimeDevEntryResult result = {};
    result.level = std::move(*level);
    result.startPose = *startPose;
    result.diagnostics = result.level.diagnostics;

    if (!result.startPose.snappedToFloor)
    {
        result.diagnostics.push_back("MM9 DAT dev start pose was not snapped to floor");
    }

    return result;
}
}
