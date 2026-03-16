#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorDecorationCollision
{
    size_t entityIndex = 0;
    uint16_t decorationId = 0;
    uint16_t descriptionFlags = 0;
    uint16_t instanceFlags = 0;
    int16_t radius = 0;
    uint16_t height = 0;
    int worldX = 0;
    int worldY = 0;
    int worldZ = 0;
    std::string name;
};

struct OutdoorDecorationCollisionSet
{
    std::vector<OutdoorDecorationCollision> colliders;
};

enum class OutdoorActorCollisionSource
{
    Spawn,
    MapDelta,
};

struct OutdoorActorCollision
{
    size_t sourceIndex = 0;
    OutdoorActorCollisionSource source = OutdoorActorCollisionSource::Spawn;
    uint16_t radius = 0;
    uint16_t height = 0;
    int worldX = 0;
    int worldY = 0;
    int worldZ = 0;
    uint32_t attributes = 0;
    uint32_t group = 0;
    std::string name;
};

struct OutdoorActorCollisionSet
{
    std::vector<OutdoorActorCollision> colliders;
};

struct OutdoorSpriteObjectCollision
{
    size_t sourceIndex = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectAttributes = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    int worldX = 0;
    int worldY = 0;
    int worldZ = 0;
    int32_t spellId = 0;
    std::string name;
};

struct OutdoorSpriteObjectCollisionSet
{
    std::vector<OutdoorSpriteObjectCollision> colliders;
};
}
