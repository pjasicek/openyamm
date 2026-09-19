#pragma once

#include "bx/math.h"

#include "game/maps/MapPresentation.h"

#include "game/maps/OutdoorSceneProfile.h"
#include "game/outdoor/OutdoorNavigationData.h"
#include "game/outdoor/OutdoorRenderData.h"
#include "game/outdoor/OutdoorLightingData.h"
#include "game/outdoor/OutdoorMechanismAudio.h"
#include "game/render/SurfaceMaterialRuntime.h"

#include <cstddef>
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorBModelVertex
{
    int x = 0;
    int y = 0;
    int z = 0;
};

struct OutdoorBspNode
{
    int16_t front = 0;
    int16_t back = 0;
    int16_t faceIdOffset = 0;
    int16_t faceCount = 0;
};

struct OutdoorBModelFace
{
    int32_t planeNormalX = 0;
    int32_t planeNormalY = 0;
    int32_t planeNormalZ = 0;
    int32_t planeDistance = 0;
    uint32_t attributes = 0;
    std::vector<uint16_t> vertexIndices;
    std::vector<int16_t> textureUs;
    std::vector<int16_t> textureVs;
    int16_t bitmapIndex = 0;
    int16_t textureDeltaU = 0;
    int16_t textureDeltaV = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggeredNumber = 0;
    uint16_t cogTrigger = 0;
    uint16_t reserved = 0;
    uint8_t polygonType = 0;
    uint8_t shade = 0;
    uint8_t visibility = 0;
    int perceptionDifficulty = -1;
    std::string textureName;
};

struct OutdoorBModel
{
    std::string name;
    std::string secondaryName;
    int positionX = 0;
    int positionY = 0;
    int positionZ = 0;
    int minX = 0;
    int minY = 0;
    int minZ = 0;
    int maxX = 0;
    int maxY = 0;
    int maxZ = 0;
    int boundingCenterX = 0;
    int boundingCenterY = 0;
    int boundingCenterZ = 0;
    int boundingRadius = 0;
    std::vector<OutdoorBModelVertex> vertices;
    std::vector<OutdoorBModelFace> faces;
    std::vector<OutdoorBspNode> bspNodes;
};

struct OutdoorEntity
{
    uint16_t decorationListId = 0;
    uint16_t aiAttributes = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int facing = 0;
    uint16_t eventIdPrimary = 0;
    uint16_t eventIdSecondary = 0;
    uint16_t variablePrimary = 0;
    uint16_t variableSecondary = 0;
    uint16_t specialTrigger = 0;
    std::string name;

    uint16_t scriptEventId() const
    {
        return eventIdSecondary;
    }

    uint32_t spriteOverrideKey(size_t entityIndex) const
    {
        return eventIdPrimary != 0 ? eventIdPrimary : static_cast<uint32_t>(entityIndex);
    }
};

struct OutdoorSpawn
{
    int x = 0;
    int y = 0;
    int z = 0;
    uint16_t radius = 0;
    uint16_t typeId = 0;
    uint16_t index = 0;
    uint16_t attributes = 0;
    uint32_t group = 0;
};

struct OutdoorTerrainFootstepSoundOverride
{
    uint8_t tileId = 0;
    uint32_t walkSoundId = 0;
    uint32_t runSoundId = 0;
};

enum class OutdoorBModelMechanismKind
{
    LinearDoor,
    WeightedLift,
    RotatingDoor,
    RotatingBrush,
    CollisionVolume,
    Unsupported
};

enum class OutdoorBModelMechanismMotionKind
{
    None,
    Linear,
    Rotation
};

struct OutdoorBModelMechanism
{
    bool hasRuntimeEndpointMotion() const
    {
        return motionKind == OutdoorBModelMechanismMotionKind::Linear
            || motionKind == OutdoorBModelMechanismMotionKind::Rotation;
    }

    uint32_t mechanismId = 0;
    uint16_t interactionEventId = 0;
    uint32_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceKind;
    OutdoorBModelMechanismKind kind = OutdoorBModelMechanismKind::Unsupported;
    OutdoorBModelMechanismMotionKind motionKind = OutdoorBModelMechanismMotionKind::None;
    bool hasBModelBinding = false;
    size_t bmodelIndex = static_cast<size_t>(-1);
    std::string bmodelName;
    std::string bindingConfidence;
    int32_t deltaX = 0;
    int32_t deltaY = 0;
    int32_t deltaZ = 0;
    int32_t pivotX = 0;
    int32_t pivotY = 0;
    int32_t pivotZ = 0;
    float rotationDegreesX = 0.0f;
    float rotationDegreesY = 0.0f;
    float rotationDegreesZ = 0.0f;
    uint32_t moveTimeMs = 0;
    bool startOpen = false;
    bool startOn = false;
    bool pushOpen = false;
    bool touchToOpen = false;
    bool locked = false;
    bool openAway = false;
    bool moveParty = false;
    OutdoorMechanismAudioProfile audio = {};
};

struct OutdoorDestructible
{
    uint32_t sourceObjectIndex = 0;
    uint32_t runtimeObjectId = 0;
    std::string sourceName;
    size_t bmodelIndex = static_cast<size_t>(-1);
    std::string bmodelName;
    std::vector<size_t> auxiliaryBmodelIndices;
    int initialHp = 1;
    bool initiallyDamageEnabled = false;
    bool triggerDestroyOnly = false;
    bool shouldMiniSave = true;
    std::string destructionSound;
    uint32_t deathTargetSourceObjectIndex = 0;
    std::string deathMessage;
};

struct OutdoorDestructibleReceiver
{
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    uint32_t requiredDestructionCount = 0;
    int32_t rewardRawQuestKey = 0;
    uint32_t rewardExperience = 0;
};

enum class OutdoorTriggerAction
{
    DamageOn,
    DamageOff,
    Damage,
    Destroy,
    Remove,
};

struct OutdoorTriggerOutput
{
    uint32_t targetSourceObjectIndex = 0;
    OutdoorTriggerAction action = OutdoorTriggerAction::Destroy;
    int damage = 1;
};

struct OutdoorTriggerVolume
{
    uint32_t sourceObjectIndex = 0;
    std::string sourceName;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    int32_t halfExtentX = 0;
    int32_t halfExtentY = 0;
    int32_t halfExtentZ = 0;
    bool startOn = true;
    std::vector<OutdoorTriggerOutput> outputs;
};

struct OutdoorMm9NpcGreeting
{
    uint32_t sourceObjectIndex = 0;
    std::string soundName;
};

struct OutdoorMapData
{
    static constexpr int TerrainWidth = 128;
    static constexpr int TerrainHeight = 128;
    static constexpr int TerrainTileSize = 512;
    static constexpr int TerrainHeightScale = 32;

    int version = 0;
    std::string worldId;
    std::string name;
    std::string fileName;
    std::string description;
    OutdoorSceneProfile sceneProfile = OutdoorSceneProfile::ClassicOdm;
    OutdoorLocationType locationType = OutdoorLocationType::Exterior;
    float lightmapBrightnessScale = 1.0f;
    float viewDistanceScale = 1.0f;
    bool noTerrain = false;
    std::string skyTexture;
    std::string groundTilesetName;
    uint8_t masterTile = 0;
    std::array<uint16_t, 4> tileSetLookupIndices = {};
    std::vector<uint8_t> heightMap;
    std::vector<uint8_t> tileMap;
    std::vector<uint8_t> attributeMap;
    std::vector<uint32_t> someOtherMap;
    std::vector<uint16_t> normalMap;
    std::vector<float> normals;
    std::vector<OutdoorBModel> bmodels;
    std::vector<OutdoorEntity> entities;
    std::vector<uint16_t> decorationPidList;
    std::vector<uint32_t> decorationMap;
    std::vector<OutdoorSpawn> spawns;
    std::vector<OutdoorTerrainFootstepSoundOverride> terrainFootstepSoundOverrides;
    std::vector<OutdoorBModelMechanism> mechanisms;
    std::vector<OutdoorDestructible> destructibles;
    std::vector<OutdoorDestructibleReceiver> destructibleReceivers;
    std::vector<OutdoorTriggerVolume> triggerVolumes;
    std::vector<OutdoorMm9NpcGreeting> mm9NpcGreetings;
    std::optional<OutdoorNavigationData> navigationData;
    std::optional<OutdoorRenderData> renderData;
    std::optional<OutdoorLightingData> lightingData;
    std::optional<MapPresentation> mapPresentation;
    SurfaceMaterialRuntimeSet surfaceMaterials;
    // Fixed sun direction of the paired bake recipe (runtime-only, never serialized).
    bx::Vec3 bakeSunDirection = {0.0f, 0.0f, 0.0f};
    bool hasBakeSunDirection = false;
    // Authored terrain puddle mask (runtime-only). Origin and origin+extent are the first
    // and last texel centers; the first decoded image row is the row at origin.y.
    struct PuddleMask
    {
        std::string maskPath;
        float originX = 0.0f;
        float originY = 0.0f;
        float extentX = 0.0f;
        float extentY = 0.0f;
        int width = 0;
        int height = 0;
        std::vector<uint8_t> pixelsBgra;
    };
    std::optional<PuddleMask> puddleMask;
    // Decoded packed facade masks for the materials this map's BModel faces actually
    // reference (runtime-only, keyed by resolved material id). Channels: R shine selector,
    // G wetness response multiplier, B emissive multiplier, A reserved.
    struct MaterialMaskImage
    {
        std::string sourceId;
        std::string maskPath;
        int width = 0;
        int height = 0;
        std::vector<uint8_t> pixelsBgra;
    };
    std::unordered_map<uint16_t, MaterialMaskImage> materialMasks;
    size_t terrainNormalCount = 0;
    size_t bmodelCount = 0;
    size_t entityCount = 0;
    size_t idListCount = 0;
    size_t spawnCount = 0;
    int minHeightSample = 0;
    int maxHeightSample = 0;
    size_t uniqueTileCount = 0;
};

class OutdoorMapDataLoader
{
public:
    std::optional<OutdoorMapData> loadFromBytes(const std::vector<uint8_t> &bytes) const;
};

class OutdoorMapDataWriter
{
public:
    std::optional<std::vector<uint8_t>> buildBytes(const OutdoorMapData &outdoorMapData) const;
    std::optional<std::vector<uint8_t>> patchBytes(
        const OutdoorMapData &outdoorMapData,
        const std::vector<uint8_t> &baseBytes) const;
};
}
