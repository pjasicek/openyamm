#pragma once

#include "game/maps/MapRuntimeRestrictions.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapItemSourceData.h"
#include "game/maps/OutdoorSceneProfile.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/tables/SurfaceAnimation.h"

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
        OutdoorAuthoredFogState authoredDayFog = {};
        OutdoorAuthoredFogState authoredNightFog = {};
    };

    std::string skyTexture;
    OutdoorLocationType locationType = OutdoorLocationType::Exterior;
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

struct OutdoorSceneLighting
{
    float lightmapBrightnessScale = 1.0f;
};

// Authored world-space puddle mask for native terrain. The mask path is an explicit mounted
// path; origin and origin+extent identify the first and last texel centers in world space,
// with signed extent selecting the row/column direction.
struct OutdoorScenePuddles
{
    std::string mask;
    std::array<float, 2> origin = {0.0f, 0.0f};
    std::array<float, 2> extent = {0.0f, 0.0f};
};

struct OutdoorSceneRendering
{
    std::optional<float> viewDistanceScale;
    std::optional<OutdoorScenePuddles> puddles;
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

struct OutdoorScenePerceptionFace
{
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    int difficulty = 0;
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

struct OutdoorSceneSurfaceAnimation
{
    std::string textureName;
    SurfaceAnimationSequence animation;
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

struct OutdoorSceneBaseContentCounts
{
    size_t entities = 0;
    size_t spawns = 0;
    size_t actors = 0;
    size_t spriteObjects = 0;
    size_t chests = 0;
};

struct OutdoorSceneData
{
    int formatVersion = 0;
    std::string geometryFile;
    std::optional<std::string> legacyCompanionFile;
    OutdoorSceneProfile sceneProfile = OutdoorSceneProfile::ClassicOdm;
    MapRuntimeRestrictions runtimeRestrictions = {};
    OutdoorSceneEnvironment environment = {};
    OutdoorSceneLighting lighting = {};
    OutdoorSceneRendering rendering = {};
    std::vector<OutdoorSceneTerrainAttributeOverride> terrainAttributeOverrides;
    std::vector<OutdoorSceneTerrainFootstepSoundOverride> terrainFootstepSoundOverrides;
    std::vector<OutdoorSceneSurfaceAnimation> surfaceAnimations;
    std::vector<OutdoorSceneInteractiveFace> interactiveFaces;
    std::vector<OutdoorScenePerceptionFace> perceptionFaces;
    std::vector<OutdoorBModelMechanism> mechanisms;
    std::vector<OutdoorDestructible> destructibles;
    std::vector<OutdoorDestructibleReceiver> destructibleReceivers;
    std::vector<OutdoorTriggerVolume> triggerVolumes;
    std::vector<OutdoorMm9NpcGreeting> mm9NpcGreetings;
    std::vector<OutdoorSceneEntity> entities;
    std::vector<OutdoorSceneSpawn> spawns;
    OutdoorSceneInitialState initialState = {};
    MapItemSourceData itemSources = {};
    OutdoorSceneBaseContentCounts baseContentCounts = {};
};

class OutdoorSceneYmlLoader
{
public:
    std::optional<OutdoorSceneData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
    bool applyOverlayFromText(
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
