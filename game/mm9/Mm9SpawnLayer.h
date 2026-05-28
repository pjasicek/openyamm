#pragma once

#include "game/mm9/Mm9DatWorld.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9SpawnSourceObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 rotationLt;
    bool hasRotation = false;
    std::optional<int> spawnLevel;
    std::optional<std::string> spawnObject;
    Mm9DatVec3 spawnObjectVelocityLt;
    bool hasSpawnObjectVelocity = false;
    std::optional<int> npcProps;
    std::optional<int> npcNumber;
};

struct Mm9SpawnObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 rotationLt;
    bool hasRotation = false;
    std::optional<int> spawnLevel;
    std::optional<std::string> spawnObject;
    Mm9DatVec3 spawnObjectVelocityLt;
    bool hasSpawnObjectVelocity = false;
    std::optional<int> npcProps;
    std::optional<int> npcNumber;
};

struct Mm9SpawnLayer
{
    std::vector<Mm9SpawnObject> objects;
    size_t spawnLevelCount = 0;
    size_t spawnObjectCount = 0;
    size_t spawnObjectVelocityCount = 0;
    size_t npcPropertyCount = 0;
    size_t npcNumberCount = 0;
};

Mm9SpawnLayer buildMm9SpawnLayer(const std::vector<Mm9SpawnSourceObject> &sourceObjects);
}
