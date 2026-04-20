#pragma once

#include "game/maps/MapDeltaData.h"
#include "game/indoor/IndoorMapData.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorSceneEnvironment
{
    std::string skyTexture;
    int32_t dayBitsRaw = 0;
    uint32_t mapExtraBitsRaw = 0;
    int32_t fogWeakDistance = 0;
    int32_t fogStrongDistance = 0;
    int32_t ceiling = 0;
};

struct IndoorSceneDecorationFlag
{
    size_t entityIndex = 0;
    uint16_t flag = 0;
};

struct IndoorSceneFaceAttributeOverride
{
    size_t faceIndex = 0;
    uint32_t legacyAttributes = 0;
};

struct IndoorSceneDoor
{
    size_t doorIndex = 0;
    MapDeltaDoor door = {};
};

struct IndoorSceneInitialState
{
    MapDeltaLocationInfo locationInfo = {};
    std::vector<uint8_t> visibleOutlines;
    std::vector<IndoorSceneFaceAttributeOverride> faceAttributeOverrides;
    std::vector<IndoorSceneDecorationFlag> decorationFlags;
    std::vector<MapDeltaActor> actors;
    std::vector<MapDeltaSpriteObject> spriteObjects;
    std::vector<MapDeltaChest> chests;
    std::vector<IndoorSceneDoor> doors;
    MapDeltaPersistentVariables eventVariables = {};
};

struct IndoorSceneData
{
    int formatVersion = 0;
    std::string geometryFile;
    std::optional<std::string> legacyCompanionFile;
    IndoorSceneEnvironment environment = {};
    IndoorSceneInitialState initialState = {};
};

class IndoorSceneYmlLoader
{
public:
    std::optional<IndoorSceneData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
};

bool buildIndoorMapStateFromScene(
    const IndoorSceneData &sceneData,
    const IndoorMapData &indoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage);
}
