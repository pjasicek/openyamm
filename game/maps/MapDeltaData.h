#pragma once

#include "game/indoor/IndoorMapData.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/party/InventoryItem.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/tables/Mm9MonsterAi.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct MapDeltaLocationInfo
{
    int32_t respawnCount = 0;
    int32_t lastRespawnDay = 0;
    int32_t reputation = 0;
    int32_t alertStatus = 0;
    uint32_t totalFacesCount = 0;
    uint32_t decorationCount = 0;
    uint32_t bmodelCount = 0;
};

struct MapDeltaPersistentVariables
{
    std::array<uint8_t, 75> mapVars = {};
    std::array<uint8_t, 125> decorVars = {};
};

struct MapDeltaLocationTime
{
    int64_t lastVisitTime = 0;
    std::string skyTextureName;
    int32_t weatherFlags = 0;
    int32_t fogWeakDistance = 0;
    int32_t fogStrongDistance = 0;
    std::array<uint8_t, 24> reserved = {};
};

// A rigid item an actor holds on one of its 3D model's nodes (scene held_items: MM9's AttachProp, a monk's broom, a
// miner's axe): the item's model, its origin on the node.
struct MapDeltaHeldItem
{
    std::string model;
    std::string node;

    bool operator==(const MapDeltaHeldItem &other) const = default;
};

// Puts the item on its node, replacing what the node held; detachHeldItem empties the node (empty: every node).
void attachHeldItem(std::vector<MapDeltaHeldItem> &items, const std::string &model, const std::string &node);
void detachHeldItem(std::vector<MapDeltaHeldItem> &items, const std::string &node);

struct MapDeltaActor
{
    std::string name;
    int16_t npcId = 0;
    int32_t mm9RudeId = 0;
    uint32_t mm9SourceObjectIndex = 0;
    bool mm9CanReceiveDamage = true;
    // MM9's ShouldRepopulate (scene respawns_on_refill; false: MM9's 0): a map refill keeps it as it was left (dead,
    // gone, moved) instead of placing it anew. Read from the scene at each refill, not saved.
    bool respawnsOnRefill = true;
    bool mm9Civilian = false;
    bool mm9Guard = false;
    // Its 3D model's scale against its binding's (scene `draw_scale`); 0: none, the model then follows its height over
    // its descriptor's. Lets a placement keep a collision body that is not its drawn size (MM9's).
    float drawScale = 0.0f;
    bool proceduralDeathLoot = true;
    uint16_t initialYawUnits = 0;
    bool immobile = false;
    // A placed actor that keeps its stored height (scene keeps_height: a Brood Sac on its cradle socket) instead of
    // standing on the floor under it; indoors only, outdoor placements keep theirs already.
    bool keepsHeight = false;
    // A posed prop (scene posed: MM9's RUDEProps, people sitting at a table or behind a bar who loop one pose): the
    // world never moves it, neither its initial placement nor collision pushes, nor gravity; it stays exactly where
    // placed, overlapping its seat. Indoors only. Its pose and facing come from its map script (evt.PlayActorClip).
    bool posed = false;
    // Items it holds (scene held_items), drawn on its 3D model beside its binding's own attachments; map scripts change
    // them (evt.AttachActorItem, evt.DetachActorItem). Saved with the map.
    std::vector<MapDeltaHeldItem> heldItems;
    // A leash for this placement (scene leash_radius): it fights at most this far from where it was placed and walks
    // back there with no target, whatever its monster's tactics say (0: none).
    uint16_t leashRadius = 0;
    // Resting (scene dormant): it stands, neither moving nor fighting, until it is hurt or an event wakes it
    // (evt.WakeActor, evt.WakeGroup). Indoors this is its live state; outdoors MapActorState::dormant is.
    bool dormant = false;
    // Waypoints it walks in turn, round and round, while it has nothing to fight (scene patrol: [[x, y, z], ...]).
    std::vector<std::array<int32_t, 3>> patrolPoints;
    // An MM9 placement's AI settings (scene mm9_ai, written by the MM9 map converters; devdocs/mm9_rework/monster_ai/
    // PROFILE.md). Data only for now: nothing changes how the actor behaves.
    std::optional<Mm9AiPlacementRecord> mm9Ai;
    uint32_t attributes = 0;
    int32_t hp = 0;
    uint8_t hostilityType = 0;
    int16_t monsterInfoId = 0;
    int16_t monsterId = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    uint16_t moveSpeed = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    std::array<uint16_t, 4> spriteIds = {};
    int16_t sectorId = 0;
    uint16_t currentActionAnimation = 0;
    uint32_t carriedItemId = 0;
    uint32_t group = 0;
    uint32_t ally = 0;
    int32_t uniqueNameIndex = 0;
    size_t diagnosticSourceActorIndex = static_cast<size_t>(-1);
    // Created after the map's first fill (summons, death summons, later event spawns): MAW's Nightmare revival raises
    // only the roster of the first fill.
    bool spawnedAfterFill = false;
    // The party member whose spell summoned it, -1 for none (MM8's Summoner field: a caster's summon limit counts it).
    int32_t summonerMemberIndex = -1;
    float bolsterRewardMultiplier = 1.0f;
    ActorRulesetFacts rulesetFacts;
};

struct MapDeltaSpriteObject
{
    uint16_t spriteId = 0;
    uint16_t objectDescriptionId = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int16_t velocityX = 0;
    int16_t velocityY = 0;
    int16_t velocityZ = 0;
    uint16_t yawAngle = 0;
    uint16_t soundId = 0;
    uint16_t attributes = 0;
    int16_t sectorId = 0;
    uint16_t timeSinceCreated = 0;
    int16_t temporaryLifetime = 0;
    int16_t glowRadiusMultiplier = 0;
    int32_t spellId = 0;
    int32_t spellLevel = 0;
    int32_t spellSkill = 0;
    int32_t field54 = 0;
    int32_t spellCasterPid = 0;
    int32_t spellTargetPid = 0;
    int8_t lodDistance = 0;
    int8_t spellCasterAbility = 0;
    int initialX = 0;
    int initialY = 0;
    int initialZ = 0;
    // The object's identity while it exists (indoors: what an item's ground yaw and model are keyed by), unlike its index,
    // which shifts when an object before it is taken. 0 until assigned (appendSpriteObject, assignSpriteObjectKeys).
    uint32_t objectKey = 0;
    float lifetimeTickAccumulator = 0.0f;
    std::vector<uint8_t> rawContainingItem;
    // The item as the game made it (a drop, a monster's loot), with what the record's 0x24 bytes have no room for:
    // charges and the ruleset fields (audit ITM-1). Map-authored items have only the record.
    std::optional<InventoryItem> heldItem;
    std::string semanticSourceId;
    uint32_t semanticLootContainerId = 0;
    bool semanticPlacedPickup = false;
    bool semanticLootContainer = false;
    bool semanticPolicyHidden = false;
    // Runtime only (not saved): a placed world item shown but not yet takeable (MapWorldItemSource::pickupQBits),
    // set by the visibility sync; it draws no sparkle.
    bool semanticPickupLocked = false;
    // Runtime only: a placed world item's authored pose (yaw, pitch, roll radians; MapWorldItemSource::poseDegrees).
    std::optional<std::array<float, 3>> semanticPose;
};

struct MapDeltaChest
{
    uint16_t chestTypeId = 0;
    uint16_t flags = 0;
    std::vector<uint8_t> rawItems;
    std::vector<int16_t> inventoryMatrix;
};

struct MapDeltaDoor
{
    uint32_t slotIndex = 0;
    uint32_t attributes = 0;
    uint32_t doorId = 0;
    uint32_t timeSinceTriggered = 0;
    int directionX = 0;
    int directionY = 0;
    int directionZ = 0;
    uint32_t moveLength = 0;
    uint32_t openSpeed = 0;
    uint32_t closeSpeed = 0;
    uint16_t numVertices = 0;
    uint16_t numFaces = 0;
    uint16_t numSectors = 0;
    uint16_t numOffsets = 0;
    uint16_t state = 0;
    std::vector<uint16_t> vertexIds;
    std::vector<uint16_t> faceIds;
    std::vector<uint16_t> sectorIds;
    std::vector<int16_t> deltaUs;
    std::vector<int16_t> deltaVs;
    std::vector<int16_t> xOffsets;
    std::vector<int16_t> yOffsets;
    std::vector<int16_t> zOffsets;
};

enum class Mm9BarrelType : uint8_t
{
    RedMight = 1,
    BlueMagic = 2,
    GreenEndurance = 3,
    PurpleSpeed = 4,
    WhiteLuck = 5,
    YellowAccuracy = 6,
    Swamp = 7,
    Water = 8,
};

struct MapDeltaMm9BarrelState
{
    uint32_t sourceObjectIndex = 0;
    Mm9BarrelType type = Mm9BarrelType::Water;
    bool used = false;
};

// One of a ruleset's extra pack members (MAW's density in MM9: a ruleset scene overlay's `pack_reserve`): a copy of a
// pack's member, placed beside it by tools/maw/mm9_pack_reserve.py with the converter's placement rules. It joins the
// map when the rules' density factor reaches `fromFactor` (MonsterRules::packDensityFactor).
struct MapDeltaPackReserveActor
{
    MapDeltaActor actor;
    float fromFactor = 0.0f;
};

struct MapDeltaData
{
    MapDeltaLocationInfo locationInfo = {};
    uint64_t surfaceRevision = 0;
    std::vector<uint8_t> fullyRevealedCells;
    std::vector<uint8_t> partiallyRevealedCells;
    std::vector<uint8_t> visibleOutlines;
    std::vector<uint32_t> faceAttributes;
    std::vector<uint16_t> decorationFlags;
    std::vector<MapDeltaActor> actors;
    // The map's pack reserve, by rising fromFactor, from its assets only (never saved): the first fill and each refill
    // append those the rules' density factor reaches right after the scene's actors (before encounter spawns), so the
    // k-th appended actor is always reserve entry k.
    std::vector<MapDeltaPackReserveActor> packReserve;
    std::vector<MapDeltaSpriteObject> spriteObjects;
    std::vector<MapDeltaChest> chests;
    uint32_t doorSlotCount = 0;
    std::vector<MapDeltaDoor> doors;
    std::vector<int16_t> doorsData;
    MapDeltaPersistentVariables eventVariables = {};
    MapDeltaLocationTime locationTime = {};
    std::vector<MapDeltaMm9BarrelState> mm9Barrels;
    // The source ids of the scene's placed world items the party took (MapWorldItemSource): never placed again,
    // through refills too.
    std::vector<std::string> takenWorldItems;
};

void normalizeIndoorDoorTextureDeltas(MapDeltaData &mapDeltaData, const IndoorMapData &indoorMapData);

// Appends an object under a key no present object has (MapDeltaSpriteObject::objectKey).
void appendSpriteObject(MapDeltaData &mapDeltaData, MapDeltaSpriteObject spriteObject);

// Gives each object without a key one, in order (a map's authored objects, a save from before keys).
void assignSpriteObjectKeys(MapDeltaData &mapDeltaData);

// A map refill places its scene actors anew (refilled, fresh from the scene); a scene actor with respawnsOnRefill false
// takes back its record from the saved map (the same index, name and monster) instead. Returns how many it kept.
size_t keepActorsThroughRefill(const MapDeltaData &saved, MapDeltaData &refilled);

class MapDeltaDataLoader
{
public:
    std::optional<MapDeltaData> loadOutdoorFromBytes(
        const std::vector<uint8_t> &bytes,
        const OutdoorMapData &outdoorMapData
    ) const;
    std::optional<MapDeltaData> loadIndoorFromBytes(
        const std::vector<uint8_t> &bytes,
        const IndoorMapData &indoorMapData
    ) const;
};
}
