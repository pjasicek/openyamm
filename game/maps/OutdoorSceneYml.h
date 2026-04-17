#pragma once

#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWeatherProfile.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorSceneEnvironment
{
    struct WeatherConfig
    {
        OutdoorFogMode fogMode = OutdoorFogMode::Static;
        OutdoorPrecipitationKind precipitation = OutdoorPrecipitationKind::None;
        bool hasFogTint = false;
        std::array<uint8_t, 3> fogTintRgb = {255, 255, 255};
        int smallFogChance = 0;
        int averageFogChance = 0;
        int denseFogChance = 0;
        OutdoorFogDistances smallFog = {4096, 8192};
        OutdoorFogDistances averageFog = {0, 4096};
        OutdoorFogDistances denseFog = {0, 2048};
    };

    std::string skyTexture;
    std::string groundTilesetName;
    uint8_t masterTile = 0;
    std::array<uint16_t, 4> tileSetLookupIndices = {};
    int32_t dayBitsRaw = 0;
    uint32_t mapExtraBitsRaw = 0;
    int32_t fogWeakDistance = 0;
    int32_t fogStrongDistance = 0;
    int32_t ceiling = 0;
    WeatherConfig weather = {};
};

struct OutdoorSceneTerrainAttributeOverride
{
    int x = 0;
    int y = 0;
    uint8_t legacyAttributes = 0;
};

struct OutdoorSceneInteractiveFace
{
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    uint32_t legacyAttributes = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggeredNumber = 0;
    uint16_t cogTrigger = 0;
};

struct OutdoorSceneEntity
{
    size_t entityIndex = 0;
    OutdoorEntity entity = {};
    uint16_t initialDecorationFlag = 0;
};

struct OutdoorSceneSpawn
{
    size_t spawnIndex = 0;
    OutdoorSpawn spawn = {};
};

struct OutdoorSceneFaceAttributeOverride
{
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    uint32_t legacyAttributes = 0;
};

struct OutdoorSceneInitialState
{
    MapDeltaLocationInfo locationInfo = {};
    std::vector<OutdoorSceneFaceAttributeOverride> faceAttributeOverrides;
    std::vector<MapDeltaActor> actors;
    std::vector<MapDeltaSpriteObject> spriteObjects;
    std::vector<MapDeltaChest> chests;
    MapDeltaPersistentVariables eventVariables = {};
};

struct OutdoorSceneData
{
    int formatVersion = 0;
    std::string geometryFile;
    std::optional<std::string> legacyCompanionFile;
    OutdoorSceneEnvironment environment = {};
    std::vector<OutdoorSceneTerrainAttributeOverride> terrainAttributeOverrides;
    std::vector<OutdoorSceneInteractiveFace> interactiveFaces;
    std::vector<OutdoorSceneEntity> entities;
    std::vector<OutdoorSceneSpawn> spawns;
    OutdoorSceneInitialState initialState = {};
};

class OutdoorSceneYmlLoader
{
public:
    std::optional<OutdoorSceneData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
};

bool buildOutdoorMapStateFromScene(
    const OutdoorSceneData &sceneData,
    OutdoorMapData &outdoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage);
}
