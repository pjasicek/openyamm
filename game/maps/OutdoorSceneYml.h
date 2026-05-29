#pragma once

#include "game/maps/MapRuntimeRestrictions.h"
#include "game/maps/MapDeltaData.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWeatherProfile.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorSceneEnvironment
{
    struct Flags
    {
        bool foggy = false;
        bool raining = false;
        bool snowing = false;
        bool underwater = false;
        bool noTerrain = false;
        bool alwaysDark = false;
        bool alwaysLight = false;
        bool alwaysFoggy = false;
        bool redFog = false;
    };

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
    Flags flags = {};
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

struct OutdoorSceneTerrainFootstepSoundOverride
{
    uint8_t tileId = 0;
    uint32_t walkSoundId = 0;
    uint32_t runSoundId = 0;
};

struct OutdoorSceneInteractiveFace
{
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    std::string bmodelName;
    bool allFaces = false;
    bool hasLegacyAttributes = true;
    bool hasCogNumber = true;
    bool hasCogTriggeredNumber = true;
    bool hasCogTrigger = true;
    uint32_t legacyAttributes = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggeredNumber = 0;
    uint16_t cogTrigger = 0;
};

struct OutdoorSceneBModelFaceSource
{
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    std::string sourceKind;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    size_t sourcePolyIndex = 0;
    std::string textureAlias;
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

struct OutdoorSceneLight
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    int32_t radius = 0;
    std::array<uint8_t, 3> color = {255, 255, 255};
    std::array<uint8_t, 3> effectiveColor = {255, 255, 255};
    std::string type = "point";
    bool lightObjects = false;
    bool fastLightObjects = false;
    bool staticObjectLightEligible = false;
};

struct OutdoorSceneModelInstance
{
    std::string instanceId;
    std::string sourceRef;
    std::string sourceKind;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string sourceSkin;
    std::string modelAsset;
    std::string modelSkinBinding;
    int x = 0;
    int y = 0;
    int z = 0;
    std::array<float, 4> rotationQuat = {0.0f, 0.0f, 0.0f, 1.0f};
    std::array<float, 3> scale = {1.0f, 1.0f, 1.0f};
    std::string collisionMode = "none";
};

struct OutdoorSceneMechanism
{
    struct Binding
    {
        std::string targetKind;
        size_t bmodelIndex = static_cast<size_t>(-1);
        std::string bmodelName;
        std::string confidence;
    };

    struct Motion
    {
        bool hasLinear = false;
        int32_t dx = 0;
        int32_t dy = 0;
        int32_t dz = 0;
        bool hasRotation = false;
        float rotationPivotX = 0.0f;
        float rotationPivotY = 0.0f;
        float rotationPivotZ = 0.0f;
        float rotationDegreesX = 0.0f;
        float rotationDegreesY = 0.0f;
        float rotationDegreesZ = 0.0f;
        uint32_t moveTimeMs = 1000;
    };

    struct Activation
    {
        bool startOpen = false;
        bool locked = false;
    };

    uint32_t mechanismId = 0;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string kind;
    Binding binding = {};
    Motion motion = {};
    Activation activation = {};
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
    std::optional<std::string> sourceMetadataFile;
    MapRuntimeRestrictions runtimeRestrictions = {};
    OutdoorSceneEnvironment environment = {};
    std::vector<OutdoorSceneTerrainAttributeOverride> terrainAttributeOverrides;
    std::vector<OutdoorSceneTerrainFootstepSoundOverride> terrainFootstepSoundOverrides;
    std::vector<OutdoorSceneBModelFaceSource> bmodelFaceSources;
    std::vector<OutdoorSceneInteractiveFace> interactiveFaces;
    std::vector<OutdoorSceneEntity> entities;
    std::vector<OutdoorSceneSpawn> spawns;
    std::vector<OutdoorSceneLight> lights;
    std::vector<OutdoorSceneModelInstance> modelInstances;
    std::vector<OutdoorSceneMechanism> mechanisms;
    OutdoorSceneInitialState initialState = {};
};

class OutdoorSceneYmlLoader
{
public:
    std::optional<OutdoorSceneData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
    bool applyOverlayFromText(
        OutdoorSceneData &sceneData,
        const std::string &yamlText,
        std::string &errorMessage) const;
    bool applySourceMetadataFromText(
        OutdoorSceneData &sceneData,
        const std::string &yamlText,
        std::string &errorMessage) const;
};

bool buildOutdoorMapStateFromScene(
    const OutdoorSceneData &sceneData,
    OutdoorMapData &outdoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage);
}
