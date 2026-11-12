#pragma once

#include "game/audio/WorldAmbientSounds.h"
#include "game/events/MechanismAudioProfile.h"
#include "game/indoor/IndoorFog.h"
#include "game/indoor/IndoorModelLighting.h"
#include "game/indoor/IndoorDaylight.h"
#include "game/indoor/IndoorOpenSky.h"
#include "game/indoor/IndoorWater.h"
#include "game/maps/MapPresentation.h"
#include "game/render/Mist.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorBakedLighting;

struct IndoorVertex
{
    int x = 0;
    int y = 0;
    int z = 0;
};

struct IndoorFace
{
    uint32_t attributes = 0;
    // Imported 16.16 plane orientation remains defined when a closed door collapses its portal.
    // Procedurally authored faces without this field derive it from their vertex winding.
    std::optional<std::array<int32_t, 3>> planeNormal;
    std::vector<uint16_t> vertexIndices;
    std::vector<int16_t> textureUs;
    std::vector<int16_t> textureVs;
    int16_t textureDeltaU = 0;
    int16_t textureDeltaV = 0;
    // Face +0x3A: the engine's texture index. Animated faces store their texture frame table sequence here, which
    // the original engines use instead of the texture name.
    int16_t textureFrameTableIndex = -1;
    uint16_t textureFrameTableCog = 0;
    uint16_t cogNumber = 0;
    uint16_t cogTriggered = 0;
    uint16_t cogTriggerType = 0;
    uint16_t lightLevel = 0;
    uint16_t roomNumber = 0;
    uint16_t roomBehindNumber = 0;
    uint8_t facetType = 0;
    std::string textureName;
    bool isPortal = false;
};

struct IndoorSector
{
    int32_t flags = 0;
    int32_t unknown0 = 0;
    uint16_t floorCount = 0;
    uint16_t wallCount = 0;
    uint16_t ceilingCount = 0;
    uint16_t fluidCount = 0;
    int16_t portalCount = 0;
    uint16_t faceCount = 0;
    uint16_t nonBspFaceCount = 0;
    uint16_t cylinderFaceCount = 0;
    uint16_t cogCount = 0;
    uint16_t decorationCount = 0;
    uint16_t markerCount = 0;
    uint16_t lightCount = 0;
    int16_t waterLevel = 0;
    int16_t mistLevel = 0;
    int16_t lightDistanceMultiplier = 0;
    int16_t minAmbientLightLevel = 0;
    int16_t firstBspNode = 0;
    int16_t exitTag = 0;
    int16_t minX = 0;
    int16_t maxX = 0;
    int16_t minY = 0;
    int16_t maxY = 0;
    int16_t minZ = 0;
    int16_t maxZ = 0;
    std::vector<uint16_t> floorFaceIds;
    std::vector<uint16_t> wallFaceIds;
    std::vector<uint16_t> ceilingFaceIds;
    std::vector<uint16_t> faceIds;
    std::vector<uint16_t> nonBspFaceIds;
    std::vector<uint16_t> cylinderFaceIds;
    std::vector<uint16_t> lightIds;
    std::vector<uint16_t> decorationIds;
    std::vector<uint16_t> portalFaceIds;
};

struct IndoorLight
{
    int16_t x = 0;
    int16_t y = 0;
    int16_t z = 0;
    int16_t radius = 0;
    uint8_t red = 0;
    uint8_t green = 0;
    uint8_t blue = 0;
    uint8_t type = 0;
    int16_t attributes = 0;
    int16_t brightness = 0;
    int32_t id = 0;
};

struct IndoorBspNode
{
    int16_t front = 0;
    int16_t back = 0;
    int16_t faceIdOffset = 0;
    int16_t faceCount = 0;
};

struct IndoorOutline
{
    uint16_t vertex1Id = 0;
    uint16_t vertex2Id = 0;
    uint16_t face1Id = 0;
    uint16_t face2Id = 0;
    int16_t z = 0;
    uint16_t flags = 0;
};

struct IndoorEntity
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

struct IndoorSpawn
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

// A translucent face (devdocs/INDOOR_TRANSLUCENT_FACES.md): drawn after the opaque scene, alpha-blended, its texture
// colour times `tint` at the texture's alpha times `opacity`. Opt-in per face through the map's scene file.
struct IndoorFaceTranslucency
{
    float opacity = 1.0f;
    std::array<float, 3> tint = {1.0f, 1.0f, 1.0f};
    // A single-sided face is drawn only from the side its plane normal faces.
    bool twoSided = false;

    bool operator==(const IndoorFaceTranslucency &other) const = default;
};

struct IndoorTranslucentFace
{
    uint16_t faceIndex = 0;
    IndoorFaceTranslucency translucency = {};
};

// A door's rotating and MM9 behaviours (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md), opt-in per door through the
// scene's door `mover` block; no MM6-MM8 door has one.
enum class IndoorMoverEasing : uint8_t
{
    Linear = 0,
    Sine,
};

// What the mover does when a moving face meets the party or a monster.
enum class IndoorMoverBodyRule : uint8_t
{
    Ignore = 0,
    Hold,
    Reverse,
    Push,
};

struct IndoorMoverRotation
{
    // A point on the hinge line and its unit axis (native units); positive angles turn right-handed about the axis.
    std::array<float, 3> pivot = {0.0f, 0.0f, 0.0f};
    std::array<float, 3> axis = {0.0f, 0.0f, 1.0f};
    // From the closed (stored) pose to the open pose.
    float openDegrees = 0.0f;
    // The sign is chosen when the door starts to open from closed, away from the party.
    bool openAway = false;
};

// A continuous spin (scene `mover.spin`, MM9's RotatingBrush: gears, saws, wheels): the door's faces turn about the axis
// through the pivot while it is switched on (evt.SpinMover), ramping up and down. The door's own motion, linear or
// rotating (the parent MM9 attaches the spinner to), carries the spun pose. devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md
// "Continuous spinners".
struct IndoorMoverSpin
{
    // A point on the spin axis in the stored pose (the BLV's vertices) and the unit axis; positive turns right-handed.
    std::array<float, 3> pivot = {0.0f, 0.0f, 0.0f};
    std::array<float, 3> axis = {0.0f, 0.0f, 1.0f};
    float degreesPerSecond = 360.0f;
    // From stopped to full speed and back (0: at once).
    float spinUpSeconds = 0.0f;
    float spinDownSeconds = 0.0f;
    // Its state until evt.SpinMover switches it.
    bool startOn = true;
};

struct IndoorMoverDefinition
{
    uint32_t doorId = 0;
    std::optional<IndoorMoverRotation> rotation;
    std::optional<IndoorMoverSpin> spin;
    IndoorMoverEasing easing = IndoorMoverEasing::Linear;
    IndoorMoverBodyRule bodies = IndoorMoverBodyRule::Ignore;
    // Grounded bodies standing on its faces move with it.
    bool carry = false;
    // An opened door closes itself after this long (0: never).
    float autoCloseSeconds = 0.0f;
};

// A climbable strip (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, "Ladders"), from the scene's `ladders`.
struct IndoorLadder
{
    std::string id;
    // The strip's centre line from the lower floor to where it ends.
    std::array<float, 3> bottom = {0.0f, 0.0f, 0.0f};
    std::array<float, 3> top = {0.0f, 0.0f, 0.0f};
    // The direction a climber faces (toward the ladder), degrees about +z from +x.
    float facingDegrees = 0.0f;
    float width = 64.0f;
    // How far in front of the strip a body may stand and grab it.
    float reach = 48.0f;
    // Where the party stands after climbing off at the top.
    std::array<float, 3> topExit = {0.0f, 0.0f, 0.0f};
    // A body in the air (jumping or falling) may grab it too, not only one standing (MM9's climbing poles).
    bool grabInAir = false;
    // A body standing at `top_exit` and walking toward the top takes hold there and climbs down (the way down from a
    // floor that has no other one, Drangheim City's TowerLadder1).
    bool grabAtTop = false;
};

// A scene `footstep_sounds` entry: the walking and running sounds on floors drawn with these textures (an MM9
// open-air map's grass, rock, wood; devdocs/INDOOR_OPEN_SKY.md "Footsteps").
// A door's own sounds (the scene door's `sounds` block).
struct IndoorDoorSounds
{
    uint32_t doorId = 0;
    MechanismAudioProfile profile = {};
};

// A door an MM9 monster opens by walking into it (the scene door's `ai_open`; MM9's AITriggerable doors): the doors it
// opens with it and its opening time (move_length / open_speed: MM9's DoorOpenTime).
struct IndoorAiDoor
{
    uint32_t doorId = 0;
    std::vector<uint32_t> opensDoorIds;
    float openSeconds = 0.0f;
};

// Scene `destructibles` (devdocs/INDOOR_DESTRUCTIBLES.md): a wall, window or prop that breaks. Its faces are the
// faces of its cog; its prop the decorations of its decoration cog (evt.SetSprite's key). Party weapons and missiles
// damage its faces; Lua damages or destroys it by its id (evt.DamageDestructible). Destroyed, its faces turn
// invisible and untouchable, its prop goes, its sound and debris effect play at its centre and its map event runs.
struct IndoorDestructible
{
    uint32_t id = 0;                    // the save state's key (EventRuntimeState::destructibles): MM9's object index
    std::string name;
    uint16_t cog = 0;
    uint16_t decorationCog = 0;
    int hp = 1;
    bool damageEnabled = true;
    bool triggerDestroyOnly = false;    // only evt.DestroyDestructible breaks it
    std::string sound;
    std::string effect;                 // an effect library id; empty: none
    float effectScale = 1.0f;
    std::array<float, 3> center = {};
    uint16_t destroyedEvent = 0;
    uint16_t damagedEvent = 0;          // runs on the first damage (MM9's DamageTrigger)
};

// Scene `pulsing_lights` (devdocs/INDOOR_PULSING_LIGHTS.md): MM9's GlowingLight, a dynamic point light
// whose intensity and radius each follow a sine between their min and max at their own frequency (cycles per second)
// and phase (cycles). evt.SetLight(lightKey, on) switches it (EventRuntimeState::indoorLightsEnabled); unset, it is on
// when startOn.
struct IndoorPulsingLight
{
    uint32_t lightKey = 0;
    std::array<float, 3> position = {};
    std::array<uint8_t, 3> color = {255, 255, 255};
    std::array<float, 4> intensity = {1.0f, 1.0f, 0.0f, 0.0f};     // min, max, frequency, phase
    std::array<float, 4> radius = {0.0f, 0.0f, 0.0f, 0.0f};        // min, max, frequency, phase
    bool startOn = true;
};

struct IndoorFootstepSound
{
    std::vector<std::string> textureNames;      // lower case
    uint32_t walkSoundId = 0;
    uint32_t runSoundId = 0;
};

// Scene `terrain` (devdocs/INDOOR_OPEN_SKY.md "Terrain"): an open-air map's ground faces drawn from blended library
// materials (TerrainMaterialSet) instead of their textures.
struct IndoorTerrain
{
    // The material file in worlds/<world>/terrain_materials/ (OutdoorTerrainMaterialConfig's format; its weights
    // cover the 65 536-unit map frame as on an outdoor map).
    std::string materials;
    std::vector<std::string> textureNames;      // lower case, sorted
    // `exclude_faces`: faces with a terrain texture drawn as ordinary faces (their texture and lightmap): a tunnel's
    // floor strips under the terrain (terrain_blend.py). Sorted.
    std::vector<uint32_t> excludedFaces;
    // `grass`: a terrain decoration file (worlds/<world>/terrain_decorations/<map>.yml format, by virtual path) whose
    // first grass rule and plant library grow the meadow over the terrain's grass layers (the materials with a meadow
    // strength): tall patches, flowers, verges, undergrowth and bushes; empty for none. devdocs/INDOOR_OPEN_SKY.md
    // "Terrain".
    std::string grass;
};

struct IndoorPartyStartPoint
{
    int x = 0;
    int y = 0;
    int z = 0;
    int facingDegrees = 0;
};

struct IndoorMapData
{
    int version = 0;
    int32_t faceDataSizeBytes = 0;
    int32_t sectorDataSizeBytes = 0;
    int32_t sectorLightDataSizeBytes = 0;
    int32_t doorsDataSizeBytes = 0;
    uint32_t rawFaceCount = 0;
    std::vector<IndoorVertex> vertices;
    std::vector<IndoorFace> faces;
    std::vector<IndoorSector> sectors;
    std::vector<uint16_t> sectorData;
    std::vector<uint16_t> sectorLightData;
    std::vector<IndoorEntity> entities;
    std::vector<IndoorLight> lights;
    std::vector<IndoorBspNode> bspNodes;
    std::vector<IndoorSpawn> spawns;
    std::vector<IndoorOutline> outlines;
    std::optional<IndoorPartyStartPoint> partyStartPoint;
    std::optional<MapPresentation> mapPresentation;
    // The map's baked lighting sidecar (IndoorBakedLighting.h) when it has a valid one; null renders unbaked.
    std::shared_ptr<const IndoorBakedLighting> bakedLighting;
    // The scene's translucent faces, sorted by face index (empty for every map without them).
    std::vector<IndoorTranslucentFace> translucentFaces;
    // The scene's `opaque_faces`, sorted: faces drawn opaque whatever their texture's alpha (MM9's window glass without
    // its Translucent flag, devdocs/INDOOR_TRANSLUCENT_FACES.md "Opaque faces"); empty for every map without them.
    std::vector<uint16_t> opaqueFaces;
    // The scene's door `mover` blocks, sorted by door id, and its ladders (both empty for every MM6-MM8 map).
    std::vector<IndoorMoverDefinition> moverDefinitions;
    std::vector<IndoorLadder> ladders;
    // The scene's fog (disabled for every map without it).
    IndoorFog fog;
    // The scene's mist (none for every map without it).
    MapMist mist;
    // The scene's model lighting (disabled for every map without it).
    IndoorModelLighting modelLighting;
    // The scene's open sky (disabled for every map without it).
    IndoorOpenSky openSky;
    // The scene's daylight on the sectors open to the sky (disabled for every map without it).
    IndoorDaylight daylight;
    // The scene's footstep sounds by floor texture (empty for every map without them: the stone hall sound).
    std::vector<IndoorFootstepSound> footstepSounds;
    // The scene's terrain faces (none for every map without them).
    std::optional<IndoorTerrain> terrain;
    // The scene doors' own sounds, sorted by door id (empty for every MM6-MM8 map: their doors sound as the map's
    // environment).
    std::vector<IndoorDoorSounds> doorSounds;
    // The doors MM9 monsters open (scene `ai_open`), sorted by door id, and their faces (face index, door id), sorted
    // (empty for every MM6-MM8 map).
    std::vector<IndoorAiDoor> aiDoors;
    std::vector<std::pair<uint16_t, uint32_t>> aiDoorFaces;
    // Scene `party_movement: {steep_slopes: block}`: the party climbs no floor steeper than a monster can (an MM9
    // open-air map's cliffs); false keeps MM6-MM8's party, which climbs any slope.
    bool partySteepSlopesBlock = false;
    // Scene `actor_barriers: {faces: [...]}`: invisible, untouchable faces that block monsters' movement only (MM9's
    // AIBarrier brushes along bridges and ledges). Nothing else collides with them.
    std::vector<uint16_t> actorBarrierFaceIds;
    // Scene `actor_movement: {drops: follow}`: monsters walk off ledges of any height after their target and plan
    // paths down them (MM9's monsters, devdocs/mm9_rework/MM9_MONSTER_JUMP_RE.md); without it they keep MM6-MM8's
    // limit of IndoorActorMaxDropHeight.
    bool actorDropsFollow = false;
    // Scene `portal_visibility: {near_reach}`: a portal of the camera's sector within this distance that the view would
    // drop opens the whole view (IndoorPortalVisibilityInput::nearPortalReach); 0 for every MM6-MM8 map.
    float portalNearReach = 0.0f;
    // Scene `actor_detection: {wakes: none}` clears it: a monster that notices the party, or is hit by it, then wakes
    // none of its neighbours (wakeIndoorActorNeighbours). Off for MM9's converted outdoor regions, whose open
    // country is no room of a dungeon; every MM6-MM8 map keeps it.
    bool actorNeighbourWakes = true;
    // Scene `actor_detection: {provoke_radius: N}`: how far a provoking party hit provokes an MM9 loop monster's
    // friends on this map, instead of the monster's own alert radius (MM9_MONSTER_AI_PLAN.md "Awareness of the party").
    std::optional<float> actorProvokeRadius;
    // Scene `static_lights: {sides: front}`: a static light adds nothing to a face it stands behind (more than
    // IndoorStaticLightBehindTolerance behind the face's plane), so a room's lights no longer show on the outside of
    // its walls where their reach crosses a doorway (MM9's lights, baked with shadows in MM9;
    // devdocs/INDOOR_OPEN_SKY.md "Static lights"). Without it (`both`) MM6-MM8's angle-free static light is unchanged.
    bool staticLightsFrontOnly = false;
    // Scene `water_volumes`: MM9's deep water, swum and dived in (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md).
    // Empty for every map without them: no water state, breath or swimming.
    std::vector<IndoorWaterVolume> waterVolumes;
    // Scene `destructibles`, sorted by id (empty for every MM6-MM8 map).
    std::vector<IndoorDestructible> destructibles;
    // Per face: 1 for a face of a destructible (its cog), which party missiles and blows hit even while it is
    // invisible (MM9's RayHit boxes round Sturmford's drawbridge chains); empty without destructibles.
    std::vector<uint8_t> destructibleFaceMask;
    // Scene `pulsing_lights` (empty for every MM6-MM8 map).
    std::vector<IndoorPulsingLight> pulsingLights;
    // Scene `ambient_sounds` (devdocs/AMBIENT_SOUNDS.md; empty for every MM6-MM8 map).
    std::vector<WorldAmbientSound> ambientSounds;
    uint32_t doorCount = 0;
    size_t sectorCount = 0;
    size_t spriteCount = 0;
    size_t lightCount = 0;
    size_t spawnCount = 0;
};

std::vector<uint32_t> resolveIndoorLightReferenceIds(const IndoorMapData &indoorMapData, int32_t rawReferenceId);

// A standing destructible's face (not yet untouchable): hit by missiles and blows even when invisible.
inline bool indoorDestructibleHitFace(const IndoorMapData &indoorMapData, size_t faceIndex, uint32_t attributes)
{
    return faceIndex < indoorMapData.destructibleFaceMask.size() && indoorMapData.destructibleFaceMask[faceIndex] != 0
        && !hasFaceAttribute(attributes, FaceAttribute::Untouchable);
}

// The face's translucency, or null when it is opaque (always null on a map without translucent faces).
const IndoorFaceTranslucency *findIndoorFaceTranslucency(const IndoorMapData &indoorMapData, size_t faceIndex);

// A see-through face the party walks through and that runs no event (the scene's translucent faces: MM9's perception
// outline over a secret door, a sink's water): a click or the use key passes through it to what lies behind (Drangheim
// Prison's Door2 sits between the two faces of its outline).
inline bool indoorFacePassesPicks(
    const IndoorMapData &indoorMapData, size_t faceIndex, uint16_t cogTriggered, uint32_t attributes)
{
    return cogTriggered == 0 && hasFaceAttribute(attributes, FaceAttribute::Untouchable)
        && findIndoorFaceTranslucency(indoorMapData, faceIndex) != nullptr;
}
// Whether the scene lists the face in `opaque_faces` (its texture's alpha is not a cut-out there).
bool isIndoorFaceOpaque(const IndoorMapData &indoorMapData, size_t faceIndex);

// The footstep sounds of the face's texture, or null (always null on a map without footstep sounds).
const IndoorFootstepSound *findIndoorFootstepSound(const IndoorMapData &indoorMapData, size_t faceIndex);
// The door's own sounds, or null when it sounds as the map's environment.
const MechanismAudioProfile *findIndoorDoorSounds(const IndoorMapData &indoorMapData, uint32_t doorId);
// The door an MM9 monster opens by walking into this face (null for every other face).
const IndoorAiDoor *findIndoorAiDoorByFace(const IndoorMapData &indoorMapData, size_t faceIndex);
const IndoorAiDoor *findIndoorAiDoor(const IndoorMapData &indoorMapData, uint32_t doorId);

// The door's mover definition, or null for an ordinary linear door (always null on a map without them).
const IndoorMoverDefinition *findIndoorMoverDefinition(const IndoorMapData &indoorMapData, uint32_t doorId);

class IndoorMapDataLoader
{
public:
    std::optional<IndoorMapData> loadFromBytes(const std::vector<uint8_t> &bytes) const;
};

class IndoorMapDataWriter
{
public:
    std::optional<std::vector<uint8_t>> buildBytes(const IndoorMapData &indoorMapData) const;
};
}
