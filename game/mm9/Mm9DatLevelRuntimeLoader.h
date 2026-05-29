#pragma once

#include "game/maps/Mm9EventsYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/mm9/Mm9DatWorldRuntime.h"

#include <cstddef>
#include <array>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9DatLevelRuntimeSource
{
    std::string dat;
    std::string manifest;
    std::string originalDat;
    std::string sourceGame;
    int datVersion = 0;
    std::string contentHash;
};

struct Mm9DatLevelRuntimeSidecars
{
    std::string datWorld;
    std::string rawObjects;
    std::string materials;
    std::string events;
    std::optional<std::string> sourceAssetAliases;
    std::optional<std::string> sceneCompat;
    std::optional<std::string> sourceMetadataCompat;
    std::optional<std::string> bspCompat;
    std::optional<std::string> geometryCompat;
    std::optional<std::string> modelAssetsCompat;
    std::optional<std::string> odmCompat;
    std::optional<std::string> blvCompat;
};

struct Mm9DatLevelRuntimeMetadata
{
    int formatVersion = 0;
    std::string kind;
    std::string mapId;
    std::string displayName;
    Mm9DatLevelRuntimeSource source;
    std::string worldBackend;
    std::string collision;
    std::string render;
    std::string visibility;
    bool sky = false;
    Mm9DatLevelRuntimeSidecars sidecars;
};

struct Mm9DatWorldSidecarRuntimeData
{
    std::string mapId;
    std::string sourceDat;
    int datVersion = 0;
    size_t worldModelCount = 0;
    std::vector<Mm9DatModelRenderRole> modelRoles;
};

struct Mm9DatRuntimeStartPoint
{
    std::string name;
    size_t sourceObjectIndex = 0;
    Mm9DatVec3 positionLt;
    Mm9DatVec3 position;
    std::array<float, 4> rotationLt = {};
    float yawRadians = 0.0f;
    bool movePlayerToFloor = true;
};

struct Mm9DatRuntimeExitTrigger
{
    std::string name;
    size_t sourceObjectIndex = 0;
    Mm9DatVec3 positionLt;
    Mm9DatVec3 position;
    Mm9DatVec3 dimsLt;
    Mm9DatVec3 dims;
    std::string destinationWorld;
    std::string destinationMapId;
    std::string startPointName;
    std::string loadScreen;
    float travelDays = 0.0f;
    bool askPlayer = false;
    bool startOn = true;
};

struct Mm9DatLevelRuntimeLoadResult
{
    Mm9DatLevelRuntimeMetadata metadata;
    std::filesystem::path levelPath;
    std::filesystem::path sourceDatPath;
    std::filesystem::path datWorldSidecarPath;
    std::filesystem::path rawObjectsSidecarPath;
    std::filesystem::path sceneCompatPath;
    std::filesystem::path eventsSidecarPath;
    Mm9DatWorld world;
    Mm9DatWorldSidecarRuntimeData datWorldSidecar;
    std::vector<Mm9DatModelRenderRole> modelRoles;
    Mm9EventsData events;
    OutdoorSceneData sceneData;
    std::vector<Mm9ScriptedObject> scriptedObjects;
    std::vector<Mm9DatRuntimeStartPoint> startPoints;
    std::vector<Mm9DatRuntimeExitTrigger> exitTriggers;
    Mm9DatWorldRuntime runtime;
    std::vector<std::string> diagnostics;
};

std::filesystem::path resolveMm9DatLevelRuntimeRelativePath(
    const std::filesystem::path &levelPath,
    const std::string &relativePath);

std::optional<Mm9DatLevelRuntimeMetadata> parseMm9DatLevelRuntimeMetadata(
    const std::string &text,
    std::string &errorMessage);

std::optional<Mm9DatWorldSidecarRuntimeData> parseMm9DatWorldSidecarRuntimeData(
    const std::string &text,
    std::string &errorMessage);

std::optional<Mm9DatLevelRuntimeLoadResult> loadMm9DatLevelRuntime(
    const std::filesystem::path &levelPath,
    std::string &errorMessage);

std::optional<Mm9DatLevelRuntimeLoadResult> loadMm9DatLevelRuntimeForMap(
    const std::filesystem::path &sourceRoot,
    const std::string &mapId,
    std::string &errorMessage);
}
