#pragma once

#include "game/mm9/Mm9DatLevelRuntimeLoader.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class Mm9DatDevStartPoseSource
{
    None,
    PreferredStartPoint,
    FirstStartPoint,
    WorldBoundsCenter,
};

struct Mm9DatDevStartPose
{
    std::string mapId;
    Mm9DatVec3 position;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    Mm9DatDevStartPoseSource source = Mm9DatDevStartPoseSource::None;
    std::string sourceName;
    size_t sourceObjectIndex = 0;
    bool hasSourceObject = false;
    bool snappedToFloor = false;
    size_t floorCandidateTriangleCount = 0;
    size_t floorTestedTriangleCount = 0;
};

struct Mm9DatRuntimeDevEntryRequest
{
    std::filesystem::path sourceRoot;
    std::string mapId;
    std::string preferredStartName;
    float partyHalfHeight = 64.0f;
    float floorSnapDistance = 10000.0f;
    float floorBias = 0.1f;
};

struct Mm9DatRuntimeDevEntryResult
{
    Mm9DatLevelRuntimeLoadResult level;
    Mm9DatDevStartPose startPose;
    std::vector<std::string> diagnostics;
};

std::optional<Mm9DatDevStartPose> chooseMm9DatDevStartPose(
    const Mm9DatLevelRuntimeLoadResult &level,
    const std::string &preferredStartName = {},
    float partyHalfHeight = 64.0f,
    float floorSnapDistance = 10000.0f,
    float floorBias = 0.1f);

std::optional<Mm9DatRuntimeDevEntryResult> loadMm9DatRuntimeForDevEntry(
    const Mm9DatRuntimeDevEntryRequest &request,
    std::string &errorMessage);
}
