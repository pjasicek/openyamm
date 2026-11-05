#pragma once

#include "game/events/MechanismAudioProfile.h"
#include "game/maps/MapRuntimeRestrictions.h"
#include "game/maps/MapArenaDefinition.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MapItemSourceData.h"
#include "game/indoor/IndoorMapData.h"

#include <cstdint>
#include <optional>
#include <array>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorSceneEnvironment
{
    int64_t lastVisitTime = 0;
    std::string skyTexture;
    int32_t dayBitsRaw = 0;
    uint32_t mapExtraBitsRaw = 0;
    int32_t fogWeakDistance = 0;
    int32_t fogStrongDistance = 0;
    int32_t ceiling = 0;
    std::array<uint8_t, 24> mapExtraReserved = {};
};

struct IndoorSceneDecorationFlag
{
    size_t entityIndex = 0;
    uint16_t flag = 0;
};

struct IndoorSceneFaceAttributeOverride
{
    size_t faceIndex = 0;
    std::optional<uint32_t> legacyAttributes;
    std::optional<uint8_t> facetType;
    std::optional<std::string> textureName;
    std::optional<uint16_t> textureFrameTableCog;
    std::optional<int16_t> textureDeltaU;
    std::optional<int16_t> textureDeltaV;
    std::optional<std::vector<int16_t>> textureUs;
    std::optional<std::vector<int16_t>> textureVs;
    std::optional<uint16_t> cogNumber;
    std::optional<uint16_t> cogTriggered;
    std::optional<uint16_t> cogTriggerType;
};

struct IndoorSceneDoor
{
    size_t doorIndex = 0;
    MapDeltaDoor door = {};
    // The door's `mover` block (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md); none for every MM6-MM8 door.
    std::optional<IndoorMoverDefinition> mover;
    // The door's `sounds` block (MechanismAudioYml.h: an MM9 door's own sounds); none for every MM6-MM8 door, which
    // sounds as its map's environment.
    std::optional<MechanismAudioProfile> sounds;
    // The door's `ai_open` list: an MM9 monster walking into it opens these doors (its own and the leaves and
    // shells that open with it; MM9's AITriggerable doors, BaseDoor.inc). Empty for every other door.
    std::vector<uint32_t> aiOpenDoorIds;
};

struct IndoorSceneSpawn
{
    size_t spawnIndex = 0;
    IndoorSpawn spawn = {};
};

struct IndoorScenePartyStartPoint
{
    size_t startIndex = 0;
    std::string sourceName;
    IndoorPartyStartPoint startPoint = {};
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

// Scene `translucent_faces` entry (devdocs/INDOOR_TRANSLUCENT_FACES.md): faces drawn translucent, one setting each.
struct IndoorSceneTranslucentFaces
{
    std::vector<uint16_t> faceIds;
    IndoorFaceTranslucency translucency = {};
};

struct IndoorSceneData
{
    int formatVersion = 0;
    std::string geometryFile;
    std::optional<std::string> legacyCompanionFile;
    MapRuntimeRestrictions runtimeRestrictions = {};
    std::optional<MapArenaDefinition> arena;
    IndoorSceneEnvironment environment = {};
    bool hasSpawns = false;
    std::vector<IndoorSceneSpawn> spawns;
    std::vector<IndoorScenePartyStartPoint> partyStartPoints;
    IndoorSceneInitialState initialState = {};
    MapItemSourceData itemSources = {};
    std::vector<IndoorSceneTranslucentFaces> translucentFaces;
    // Scene `ladders` (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md).
    std::vector<IndoorLadder> ladders;
    // Scene `fog` (devdocs/INDOOR_FOG.md).
    IndoorFog fog;
    // Scene `model_lighting` (devdocs/INDOOR_MODEL_LIGHTING.md).
    IndoorModelLighting modelLighting;
    // Scene `sky` (devdocs/INDOOR_OPEN_SKY.md).
    IndoorOpenSky openSky;
    // Scene `daylight` (devdocs/INDOOR_OPEN_SKY.md "Daylight"); its sectors are computed when the map is built.
    IndoorDaylight daylight;
    // Scene `footstep_sounds` (devdocs/INDOOR_OPEN_SKY.md "Footsteps").
    std::vector<IndoorFootstepSound> footstepSounds;
    // Scene `terrain` (devdocs/INDOOR_OPEN_SKY.md "Terrain").
    std::optional<IndoorTerrain> terrain;
    // Scene `party_movement: {steep_slopes: block}`.
    bool partySteepSlopesBlock = false;
    // Scene `actor_barriers: {faces: [...]}`.
    std::vector<uint16_t> actorBarrierFaceIds;
    // Scene `actor_movement: {drops: follow}`.
    bool actorDropsFollow = false;
    // Scene `actor_detection: {wakes: none}` clears it.
    bool actorNeighbourWakes = true;
    // Scene `static_lights: {sides: front}`.
    bool staticLightsFrontOnly = false;
    // Scene `water_volumes` (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md).
    std::vector<IndoorWaterVolume> waterVolumes;
    // Scene `destructibles` (devdocs/INDOOR_DESTRUCTIBLES.md).
    std::vector<IndoorDestructible> destructibles;
    // Scene `pulsing_lights`.
    std::vector<IndoorPulsingLight> pulsingLights;
    // Scene `ambient_sounds`.
    std::vector<WorldAmbientSound> ambientSounds;
};

class IndoorSceneYmlLoader
{
public:
    std::optional<IndoorSceneData> loadFromText(const std::string &yamlText, std::string &errorMessage) const;
    bool applyOverlayFromText(
        IndoorSceneData &sceneData,
        const std::string &yamlText,
        std::string &errorMessage) const;
};

const IndoorSceneFaceAttributeOverride *findIndoorSceneFaceOverride(const IndoorSceneData &sceneData, size_t faceIndex);
IndoorSceneFaceAttributeOverride *findIndoorSceneFaceOverride(IndoorSceneData &sceneData, size_t faceIndex);
void applyIndoorSceneFaceOverride(const IndoorSceneFaceAttributeOverride &overrideEntry, IndoorFace &face);

// Parses a `translucent_faces` sequence (appended to `entries`).
bool parseIndoorSceneTranslucentFaces(
    const std::string &yamlText,
    std::vector<IndoorSceneTranslucentFaces> &entries,
    std::string &errorMessage);

// Parses a `fog` map: color_rgb (three numbers 0..255), near_distance, far_distance (0 <= near < far); false with the
// reason for anything else.
bool parseIndoorSceneFog(const std::string &yamlText, IndoorFog &fog, std::string &errorMessage);

// Parses a `sky` map: mode (only open) and optional sky_texture and preset (names); false with the reason for anything
// else.
bool parseIndoorSceneOpenSky(const std::string &yamlText, IndoorOpenSky &sky, std::string &errorMessage);

// Parses a `daylight` map: ambient_rgb and sun_rgb (three numbers 0..255 each) and optional day_scale_rgb and
// night_scale_rgb (0..255, 255 by default), sun_direction (three numbers, not zero; normalised) and sun_gain
// (0 < gain <= 100, 1 by default); false with the reason for anything else.
bool parseIndoorSceneDaylight(const std::string &yamlText, IndoorDaylight &daylight, std::string &errorMessage);

// Parses a `water_volumes` sequence of {id, liquid (water | lava), pieces [{polygon [[x, y], ...], bottom, top}], tint
// (0..1 each), fog (as the scene fog), current [x, y, z], mover_door_id}; false with the reason for anything else.
bool parseIndoorSceneWaterVolumes(
    const std::string &yamlText,
    std::vector<IndoorWaterVolume> &volumes,
    std::string &errorMessage);

// Parses a `footstep_sounds` sequence of {texture_names, walk_sound_id, run_sound_id}; false with the reason for
// anything else.
bool parseIndoorSceneAmbientSounds(
    const std::string &yamlText,
    std::vector<WorldAmbientSound> &sounds,
    std::string &errorMessage);

bool parseIndoorScenePulsingLights(
    const std::string &yamlText,
    std::vector<IndoorPulsingLight> &lights,
    std::string &errorMessage);

bool parseIndoorSceneDestructibles(
    const std::string &yamlText,
    std::vector<IndoorDestructible> &destructibles,
    std::string &errorMessage);

bool parseIndoorSceneFootstepSounds(
    const std::string &yamlText,
    std::vector<IndoorFootstepSound> &footstepSounds,
    std::string &errorMessage);

// Parses a `model_lighting` map: mode (only mm9), ambient and optional add (three numbers 0..255 each, add 30 30 30 by
// default) and optional light_scale (>= 0, 1 by default); false with the reason for anything else.
bool parseIndoorSceneModelLighting(
    const std::string &yamlText,
    IndoorModelLighting &lighting,
    std::string &errorMessage);

// The map's per-face translucency from the scene entries, sorted by face index; false for a face out of range, one
// listed twice, an opacity outside 0..1 or a negative tint.
bool buildIndoorTranslucentFaces(
    const std::vector<IndoorSceneTranslucentFaces> &entries,
    size_t faceCount,
    std::vector<IndoorTranslucentFace> &faces,
    std::string &errorMessage);

// The map's mover definitions from the scene doors' `mover` blocks, sorted by door id; false (with the reason) for a
// rotating mover that is not rigid (it moves part of a face or a portal, or shares a vertex with another door), whose
// travel does not match its angle (move_length = tenths of a degree), whose axis is not a unit vector or that has a
// linear direction, or for easing on a linear door.
bool buildIndoorMoverDefinitions(
    const std::vector<IndoorSceneDoor> &doors,
    const IndoorMapData &indoorMapData,
    std::vector<IndoorMoverDefinition> &movers,
    std::string &errorMessage);

bool buildIndoorMapStateFromScene(
    const IndoorSceneData &sceneData,
    IndoorMapData &indoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage);
}
