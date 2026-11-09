#include "game/maps/MapLayoutIdentity.h"

#include "game/maps/MapIdentity.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// Bump when the fields below change: every saved map state then counts as another layout and is reset once.
constexpr uint64_t LayoutIdentityAlgorithm = 1;

// FNV-1a over each value's bytes, least significant first, so the identity is the same on every platform.
class LayoutHasher
{
public:
    explicit LayoutHasher(uint64_t kind)
    {
        add(kind);
        add(LayoutIdentityAlgorithm);
    }

    void add(int64_t value)
    {
        add(static_cast<uint64_t>(value));
    }

    void add(uint64_t value)
    {
        for (int byteIndex = 0; byteIndex < 8; ++byteIndex)
        {
            m_hash ^= (value >> (byteIndex * 8)) & 0xffu;
            m_hash *= 0x100000001b3ull;
        }
    }

    template <typename T>
    void addList(const std::vector<T> &values)
    {
        add(uint64_t(values.size()));

        for (const T &value : values)
        {
            add(int64_t(value));
        }
    }

    uint64_t identity() const
    {
        return m_hash != 0 ? m_hash : 1;
    }

private:
    uint64_t m_hash = 0xcbf29ce484222325ull;
};

void addInitialStateLayout(LayoutHasher &hasher, const std::optional<MapDeltaData> &initialState)
{
    if (!initialState)
    {
        hasher.add(uint64_t(0));
        return;
    }

    hasher.add(uint64_t(1));
    hasher.add(uint64_t(initialState->actors.size()));
    // A ruleset's pack reserve (MapDeltaData::packReserve): a regenerated one resets the map, a difficulty change not.
    // Maps without one keep the identity they had.
    if (!initialState->packReserve.empty())
    {
        hasher.add(uint64_t(initialState->packReserve.size()));
    }
    hasher.add(uint64_t(initialState->spriteObjects.size()));
    hasher.add(uint64_t(initialState->chests.size()));

    for (const MapDeltaChest &chest : initialState->chests)
    {
        hasher.add(uint64_t(chest.chestTypeId));
    }

    hasher.add(uint64_t(initialState->doorSlotCount));
    hasher.add(uint64_t(initialState->doors.size()));

    for (const MapDeltaDoor &door : initialState->doors)
    {
        hasher.add(uint64_t(door.slotIndex));
        hasher.add(uint64_t(door.doorId));
        hasher.add(int64_t(door.directionX));
        hasher.add(int64_t(door.directionY));
        hasher.add(int64_t(door.directionZ));
        hasher.add(uint64_t(door.moveLength));
        hasher.addList(door.vertexIds);
        hasher.addList(door.faceIds);
        hasher.addList(door.sectorIds);
    }
}
}

uint64_t computeIndoorMapLayoutIdentity(const IndoorMapData &map, const std::optional<MapDeltaData> &initialState)
{
    LayoutHasher hasher('B' | ('L' << 8) | ('V' << 16));
    hasher.add(uint64_t(map.vertices.size()));

    for (const IndoorVertex &vertex : map.vertices)
    {
        hasher.add(int64_t(vertex.x));
        hasher.add(int64_t(vertex.y));
        hasher.add(int64_t(vertex.z));
    }

    hasher.add(uint64_t(map.faces.size()));

    for (const IndoorFace &face : map.faces)
    {
        hasher.add(uint64_t(face.attributes));
        hasher.addList(face.vertexIndices);
        hasher.add(uint64_t(face.cogNumber));
        hasher.add(uint64_t(face.cogTriggered));
        hasher.add(uint64_t(face.cogTriggerType));
        hasher.add(uint64_t(face.roomNumber));
        hasher.add(uint64_t(face.roomBehindNumber));
        hasher.add(uint64_t(face.facetType));
        hasher.add(uint64_t(face.isPortal ? 1 : 0));
    }

    hasher.add(uint64_t(map.sectors.size()));
    hasher.add(uint64_t(map.outlines.size()));
    hasher.add(uint64_t(map.entities.size()));

    for (const IndoorEntity &entity : map.entities)
    {
        hasher.add(uint64_t(entity.decorationListId));
        hasher.add(int64_t(entity.x));
        hasher.add(int64_t(entity.y));
        hasher.add(int64_t(entity.z));
        hasher.add(uint64_t(entity.eventIdPrimary));
        hasher.add(uint64_t(entity.eventIdSecondary));
        hasher.add(uint64_t(entity.variablePrimary));
        hasher.add(uint64_t(entity.variableSecondary));
    }

    hasher.add(uint64_t(map.spawns.size()));

    for (const IndoorSpawn &spawn : map.spawns)
    {
        hasher.add(int64_t(spawn.x));
        hasher.add(int64_t(spawn.y));
        hasher.add(int64_t(spawn.z));
        hasher.add(uint64_t(spawn.typeId));
        hasher.add(uint64_t(spawn.index));
    }

    hasher.add(uint64_t(map.moverDefinitions.size()));

    for (const IndoorMoverDefinition &mover : map.moverDefinitions)
    {
        hasher.add(uint64_t(mover.doorId));
        hasher.add(uint64_t(mover.rotation ? 1 : 0));
        hasher.add(uint64_t(mover.spin ? 1 : 0));
    }

    hasher.add(uint64_t(map.destructibles.size()));

    for (const IndoorDestructible &destructible : map.destructibles)
    {
        hasher.add(uint64_t(destructible.id));
        hasher.add(uint64_t(destructible.cog));
    }

    addInitialStateLayout(hasher, initialState);
    return hasher.identity();
}

uint64_t computeOutdoorMapLayoutIdentity(const OutdoorMapData &map, const std::optional<MapDeltaData> &initialState)
{
    LayoutHasher hasher('O' | ('D' << 8) | ('M' << 16));
    hasher.add(uint64_t(map.bmodels.size()));

    for (const OutdoorBModel &bmodel : map.bmodels)
    {
        hasher.add(uint64_t(bmodel.vertices.size()));

        for (const OutdoorBModelVertex &vertex : bmodel.vertices)
        {
            hasher.add(int64_t(vertex.x));
            hasher.add(int64_t(vertex.y));
            hasher.add(int64_t(vertex.z));
        }

        hasher.add(uint64_t(bmodel.faces.size()));

        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            hasher.add(uint64_t(face.attributes));
            hasher.addList(face.vertexIndices);
            hasher.add(uint64_t(face.cogNumber));
            hasher.add(uint64_t(face.cogTriggeredNumber));
            hasher.add(uint64_t(face.cogTrigger));
            hasher.add(uint64_t(face.polygonType));
        }
    }

    hasher.add(uint64_t(map.entities.size()));

    for (const OutdoorEntity &entity : map.entities)
    {
        hasher.add(uint64_t(entity.decorationListId));
        hasher.add(int64_t(entity.x));
        hasher.add(int64_t(entity.y));
        hasher.add(int64_t(entity.z));
        hasher.add(uint64_t(entity.eventIdPrimary));
        hasher.add(uint64_t(entity.eventIdSecondary));
    }

    hasher.add(uint64_t(map.spawns.size()));

    for (const OutdoorSpawn &spawn : map.spawns)
    {
        hasher.add(int64_t(spawn.x));
        hasher.add(int64_t(spawn.y));
        hasher.add(int64_t(spawn.z));
        hasher.add(uint64_t(spawn.typeId));
        hasher.add(uint64_t(spawn.index));
    }

    hasher.add(uint64_t(map.mechanisms.size()));

    for (const OutdoorBModelMechanism &mechanism : map.mechanisms)
    {
        hasher.add(uint64_t(mechanism.mechanismId));
        hasher.add(uint64_t(mechanism.bmodelIndex));
    }

    hasher.add(uint64_t(map.destructibles.size()));

    for (const OutdoorDestructible &destructible : map.destructibles)
    {
        hasher.add(uint64_t(destructible.sourceObjectIndex));
        hasher.add(uint64_t(destructible.bmodelIndex));
    }

    addInitialStateLayout(hasher, initialState);
    return hasher.identity();
}

SavedMapStateVerdict judgeSavedMapState(uint64_t savedIdentity, uint64_t currentIdentity, const std::string &worldId)
{
    if (savedIdentity == 0)
    {
        const std::string world = normalizeWorldId(worldId);
        const bool nativeWorld = world == "mm6" || world == "mm7" || world == "mm8";
        return nativeWorld ? SavedMapStateVerdict::Keep : SavedMapStateVerdict::ResetUnknown;
    }

    return savedIdentity == currentIdentity ? SavedMapStateVerdict::Keep : SavedMapStateVerdict::ResetChanged;
}
}
