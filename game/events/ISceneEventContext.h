#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct MapDeltaData;
struct GameplayMonsterSpawnRequest;
struct InventoryItem;

// evt.FireMissile: a world missile (a monster_projectiles.yml token) from one point to another, over flightSeconds
// (0: at its object's speed). It passes the party, whose damage the event deals itself, and bursts at the target, or on
// whatever it strikes first, with damage of damageType to every actor within radius.
struct EventMissileRequest
{
    std::string missile;
    float fromX = 0.0f;
    float fromY = 0.0f;
    float fromZ = 0.0f;
    float toX = 0.0f;
    float toY = 0.0f;
    float toZ = 0.0f;
    int damage = 0;
    std::string damageType;
    float radius = 0.0f;
    float flightSeconds = 0.0f;
};

class ISceneEventContext
{
public:
    virtual ~ISceneEventContext() = default;

    virtual float currentGameMinutes() const = 0;
    virtual const MapDeltaData *mapDeltaData() const = 0;
    virtual MapDeltaData *mapDeltaData() = 0;
    // Every face of a cog number, or one indoor face by EventRuntime::indoorFaceReferenceKey; false when none matches.
    virtual bool setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn) = 0;
    virtual std::vector<uint32_t> resolveIndoorLightReferenceIds(int32_t rawReferenceId) const
    {
        (void)rawReferenceId;
        return {};
    }

    virtual bool registerOutdoorModelMechanism(
        uint32_t mechanismId,
        const std::string &modelName,
        int32_t dx,
        int32_t dy,
        int32_t dz,
        uint32_t moveTimeMs,
        bool closed,
        bool moveParty)
    {
        (void)mechanismId;
        (void)modelName;
        (void)dx;
        (void)dy;
        (void)dz;
        (void)moveTimeMs;
        (void)closed;
        (void)moveParty;
        return false;
    }

    virtual bool fireEventMissile(const EventMissileRequest &request)
    {
        (void)request;
        return false;
    }

    virtual bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ
    ) = 0;

    virtual bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    ) = 0;

    // Places a script's monsters (MAW's pseudoSpawnpoint) and returns their actor indices.
    virtual std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request)
    {
        (void)request;
        return {};
    }

    virtual bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) = 0;

    // evt.SummonRandomItem: one generated item (with its enchantments) on the ground, thrown like evt.SummonItem.
    virtual bool summonEventInventoryItem(
        const InventoryItem &item,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        bool randomRotate)
    {
        (void)item;
        (void)x;
        (void)y;
        (void)z;
        (void)speed;
        (void)randomRotate;
        return false;
    }

    // evt.SummonGold: a gold heap of the amount on the ground (the small heap up to 200, else the large one).
    virtual bool summonEventGold(uint32_t amount, int32_t x, int32_t y, int32_t z, int32_t speed)
    {
        (void)amount;
        (void)x;
        (void)y;
        (void)z;
        (void)speed;
        return false;
    }

    virtual bool summonEventObject(
        uint32_t objectId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) = 0;

    virtual bool checkMonstersKilled(
        uint32_t checkType,
        uint32_t id,
        uint32_t count,
        bool invisibleAsDead
    ) const = 0;

    virtual bool specialJump(uint32_t encodedHorizontalVelocity, uint32_t verticalVelocity)
    {
        (void)encodedHorizontalVelocity;
        (void)verticalVelocity;
        return false;
    }

    virtual bool setMapActorPosition(size_t actorIndex, float x, float y, float z)
    {
        (void)actorIndex;
        (void)x;
        (void)y;
        (void)z;
        return false;
    }

    // evt.TurnActor / evt.TurnGroup: the actor (or every living actor of the group) fights for the party, against
    // its own faction too, for the seconds (0: for good), as an enslaved monster does. False for none turned.
    virtual bool turnMapActors(std::optional<size_t> actorIndex, uint32_t group, float seconds)
    {
        (void)actorIndex;
        (void)group;
        (void)seconds;
        return false;
    }

    // evt.WakeActor / evt.WakeGroup: a resting (dormant) actor, or every one of the group, wakes. False for none woken.
    virtual bool wakeMapActors(std::optional<size_t> actorIndex, uint32_t group)
    {
        (void)actorIndex;
        (void)group;
        return false;
    }

    // evt.LineOfSight and evt.ActorSeesParty: nothing of the map's geometry between the two points.
    virtual bool hasLineOfSight(float fromX, float fromY, float fromZ, float toX, float toY, float toZ) const
    {
        (void)fromX;
        (void)fromY;
        (void)fromZ;
        (void)toX;
        (void)toY;
        (void)toZ;
        return false;
    }

    // Where a map actor stands (its feet); false for no such actor.
    virtual bool mapActorPosition(size_t actorIndex, float &x, float &y, float &z) const
    {
        (void)actorIndex;
        (void)x;
        (void)y;
        (void)z;
        return false;
    }

    virtual bool setMapActorBehavior(size_t actorIndex, const std::string &behaviorId)
    {
        (void)actorIndex;
        (void)behaviorId;
        return false;
    }

    // MM9's Trigger <object>, <message> to an actor's behaviour script (its onTrigger); false without a script.
    virtual bool triggerMapActor(size_t actorIndex, const std::string &message)
    {
        (void)actorIndex;
        (void)message;
        return false;
    }

    virtual bool isMapActorHostile(size_t actorIndex) const
    {
        (void)actorIndex;
        return false;
    }

    virtual bool isMapActorWithinPartyDistance(size_t actorIndex, float distance) const
    {
        (void)actorIndex;
        (void)distance;
        return false;
    }

    // evt.DamageDestructible, evt.DestroyDestructible and evt.SetDestructibleDamage: a scene destructible by its id
    // (devdocs/INDOOR_DESTRUCTIBLES.md; an outdoor map's by its source object index). False for no such
    // destructible or nothing changed.
    virtual bool damageDestructible(uint32_t id, int damage)
    {
        (void)id;
        (void)damage;
        return false;
    }

    virtual bool destroyDestructible(uint32_t id)
    {
        (void)id;
        return false;
    }

    virtual bool setDestructibleDamageEnabled(uint32_t id, bool enabled)
    {
        (void)id;
        (void)enabled;
        return false;
    }

    virtual bool searchLootProp(const std::string &sourceId)
    {
        (void)sourceId;
        return false;
    }

    virtual bool useMm9Barrel(const std::string &sourceId)
    {
        (void)sourceId;
        return false;
    }

    virtual bool useMm9BarrelEvent(uint16_t eventId)
    {
        (void)eventId;
        return false;
    }

    virtual bool spawnLootContainer(const std::string &sourceId)
    {
        (void)sourceId;
        return false;
    }

    virtual bool consumeWorldItem(const std::string &sourceId)
    {
        (void)sourceId;
        return false;
    }

    virtual bool setPersistentItemMechanismState(
        const std::string &sourceId,
        bool visible,
        bool solid)
    {
        (void)sourceId;
        (void)visible;
        (void)solid;
        return false;
    }

    virtual bool setPersistentItemMechanismVariant(
        const std::string &sourceId,
        uint32_t variantIndex)
    {
        (void)sourceId;
        (void)variantIndex;
        return false;
    }
};
}
